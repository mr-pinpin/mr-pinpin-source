#!/usr/bin/env python3
"""Reusable Blender location workflow. No image-generation API calls."""
import argparse,os,re,shlex,shutil,subprocess,sys
from pathlib import Path
from contracts import *
HERE=Path(__file__).resolve().parent;DEFAULT_ROOT=HERE.parents[1]
def parser():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['build','render','cubemap','prepare','import','validate']);p.add_argument('--root',default=str(DEFAULT_ROOT));p.add_argument('--location');p.add_argument('--job');p.add_argument('--out');p.add_argument('--host',choices=['mini']);p.add_argument('--blender',default=os.environ.get('PINPIN_BLENDER','/Volumes/TB4/mac-mini-storage/tools/blender-4.5.14/Blender.app/Contents/MacOS/Blender'));p.add_argument('--build',help='Optional checksum-verified build directory');p.add_argument('--from-manifest');p.add_argument('--prepared');p.add_argument('--image');p.add_argument('--record');p.add_argument('--manifest');return p

def run_worker(action,root,loc,out,blender,**extra):
 out.mkdir(parents=True,exist_ok=True);(out/'worker-result.json').unlink(missing_ok=True);request={'action':action,'root':str(root),'location':loc,'out':str(out),**extra};write(out/'worker-request.json',request)
 with (out/'blender.log').open('w') as log:result=subprocess.run([blender,'-b','--python',str(root/'tools/locations/blender_worker.py'),'--',str(out/'worker-request.json')],stdout=log,stderr=subprocess.STDOUT)
 if result.returncode or not (out/'worker-result.json').is_file():raise RuntimeError('Blender failed; inspect '+str(out/'blender.log'))
 return read(out/'worker-result.json')
def inputs_for(root,locpath,jobpath=None):
 loc,inputs=location(root,locpath)
 for p in HERE.rglob('*.py'):
  if '__pycache__' not in p.parts:inputs[str(p.relative_to(DEFAULT_ROOT))]=sha(p)
 if jobpath:inputs[jobpath]=sha(resolve(root,jobpath))
 return loc,inputs
def build(root,locpath,out,blender):
 loc,inputs=inputs_for(root,locpath);result=run_worker('build',root,loc,out,blender);m={'schemaVersion':1,'stage':'build','locationId':loc['id'],'locationVersion':loc['version'],'inputs':inputs,'artifacts':[artifact(out/'base.blend',out),artifact(out/'geometry-manifest.json',out),artifact(out/'plan-used.json',out)],**result};write(out/'build-manifest.json',m);return m

def remote(args,root,out):
 if args.command not in ['build','render','cubemap']:raise ValueError('--host mini is only for Blender work; prepare/import/validate run locally')
 if not str(out).startswith('/Volumes/TB4/'):raise ValueError('Remote output must be on shared /Volumes/TB4')
 locpath=args.location if args.command=='build' else read(resolve(root,args.job))['location'];loc=read(resolve(root,locpath));stage=out/'.source';paths=[locpath,loc['plan']['path'],loc['underlay']['path'],loc['builder']['path']]+[x['path'] for x in loc['builder'].get('dependencies',[])];paths += [args.job] if args.job else []
 for p in (root/'tools/locations').rglob('*.py'):
  if '__pycache__' not in p.parts:paths.append(str(p.relative_to(root)))
 for rel in sorted(set(paths)):
  target=stage/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(resolve(root,rel),target)
 command=['/opt/homebrew/bin/python3',str(stage/'tools/locations/cli.py'),args.command,'--root',str(stage),'--out',str(out),'--blender',args.blender]
 for key in ['location','job','build']:
  value=getattr(args,key)
  if value:command += ['--'+key,value]
 subprocess.run(['ssh','mini',shlex.join(command)],check=True)

def prepare(args,root,out):
 if not args.from_manifest:raise ValueError('prepare requires --from-manifest from a completed render/cubemap')
 j=job(root,args.job,cube=read(resolve(root,args.job)).get('prompt',{}).get('template')=='cubemap');loc,inputs=inputs_for(root,j['location'],args.job);source=Path(args.from_manifest).resolve();validate_manifest(source,root);m=read(source)
 if m['stage'] not in ['render','cubemap'] or m.get('jobSha256')!=sha(resolve(root,args.job)):raise ValueError('Geometry manifest does not belong to this exact job')
 geometry=source.parent/('still.png' if m['stage']=='render' else 'cube-atlas.png');out.mkdir(parents=True,exist_ok=True);shutil.copy2(geometry,out/'geometry-reference.png')
 refs=read(resolve(root,loc['referencesPath']))['references'];prompt=j.get('prompt',{});ids=prompt.get('referenceIds')
 if ids is None:
  name=j['id'].lower();ids=['bathroom-book' if 'bath' in name else 'bedroom-book' if 'bed' in name else 'exterior-book' if 'exterior' in name else 'common-book']
 selected=[]
 for identity in ids:
  ref=next((r for r in refs if r['id']==identity),None)
  if ref is None or any('legacy' in role for role in ref['roles']):raise ValueError('Unknown or legacy reference cannot be selected by default: '+identity)
  path=resolve(root,ref['path'])
  if sha(path)!=ref['sha256']:raise ValueError('Reference hash mismatch: '+ref['path'])
  selected.append({**ref,'absolutePath':str(path)});inputs[ref['path']]=ref['sha256']
 templatepath=loc['promptTemplates'][prompt.get('template','still')];template=resolve(root,templatepath).read_text();inputs[templatepath]=sha(resolve(root,templatepath));inputs[loc['referencesPath']]=sha(resolve(root,loc['referencesPath']))
 values={'location_id':loc['id'],'location_version':loc['version'],'camera_record':json.dumps(m['cameras'],indent=2),'door_states':json.dumps(m['doorStates'],indent=2),'characters':prompt.get('characters','No characters.'),'action':prompt.get('action','Preserve architecture.'),'lighting':prompt.get('lighting','Preserve rendered lighting.'),'intent':prompt.get('intent','Illustrate the supplied geometry faithfully.'),'geometry_reference':str(out/'geometry-reference.png'),'style_reference_roles':json.dumps(selected,indent=2)}
 for key,value in values.items():template=template.replace('${'+key+'}',str(value))
 if re.search(r'\$\{[^}]+\}',template):raise ValueError('Unresolved prompt placeholders')
 (out/'prompt.txt').write_text(template);record={'schemaVersion':1,'status':'awaiting-built-in-imagegen','tool':'image_gen__imagegen','prompt':template,'promptSha256':sha(out/'prompt.txt'),'referenced_image_paths':[str(out/'geometry-reference.png')]+[r['absolutePath'] for r in selected],'sourceGeometrySha256':sha(geometry),'sourceManifestSha256':sha(source),'sourceJobSha256':sha(resolve(root,args.job)),'instruction':'Invoke the available built-in imagegen tool; this CLI never invokes image generation. Inspect references first. Import resulting file with an explicit generation record.'};write(out/'imagegen-job.json',record)
 manifest={'schemaVersion':1,'stage':'prepared','locationId':loc['id'],'inputs':inputs,'jobSha256':record['sourceJobSha256'],'promptSha256':record['promptSha256'],'status':record['status'],'artifacts':[artifact(out/f,out) for f in ['geometry-reference.png','prompt.txt','imagegen-job.json']]};write(out/'prepared-manifest.json',manifest)

def import_result(args,root,out):
 if not all([args.prepared,args.image,args.record]):raise ValueError('import requires --prepared, --image and --record')
 source=Path(args.prepared).resolve();validate_manifest(source,root);m=read(source)
 if m['stage']!='prepared':raise ValueError('Expected a prepared manifest')
 record=read(args.record)
 if record.get('tool')!='image_gen__imagegen' or record.get('promptSha256')!=m['promptSha256'] or not record.get('generatedAt'):raise ValueError('Generation record needs built-in tool name, exact promptSha256 and generatedAt')
 image=Path(args.image).resolve()
 if not image.is_file() or image.suffix.lower() not in ['.png','.webp','.jpg','.jpeg']:raise ValueError('Existing raster output required')
 out.mkdir(parents=True,exist_ok=True);target=out/('generated-original'+image.suffix.lower());shutil.copy2(image,target);provenance={**record,'sourceOriginalPath':str(image),'imageSha256':sha(target),'preparedManifestSha256':sha(source),'status':'proposal-needs-visual-review','approved':False};write(out/'provenance.json',provenance);write(out/'generated-manifest.json',{'schemaVersion':1,'stage':'generated','locationId':m['locationId'],'inputs':m['inputs'],'promptSha256':m['promptSha256'],'status':provenance['status'],'artifacts':[artifact(target,out),artifact(out/'provenance.json',out)]})
def main():
 args=parser().parse_args();root=Path(args.root).resolve();out=Path(args.out).resolve() if args.out else None
 if args.command=='validate':
  if not args.manifest:raise ValueError('validate requires --manifest')
  print(json.dumps(validate_manifest(args.manifest,root)));return
 if out is None:raise ValueError('--out required')
 if args.host:remote(args,root,out);return
 if args.command=='build':
  if not args.location:raise ValueError('build requires --location')
  build(root,args.location,out,args.blender)
 elif args.command in ['render','cubemap']:
  j=job(root,args.job,args.command=='cubemap');loc,inputs=inputs_for(root,j['location'],args.job);base=Path(args.build).resolve() if args.build else out/'build'
  if (base/'build-manifest.json').is_file():
   validate_manifest(base/'build-manifest.json',root);bm=read(base/'build-manifest.json')
   if bm['locationId']!=loc['id']:raise ValueError('Cached build is for another location')
  else:build(root,j['location'],base,args.blender)
  result=run_worker(args.command,root,loc,out,args.blender,job=j,base=str(base/'base.blend'));manifest={'schemaVersion':1,'stage':args.command,'locationId':loc['id'],'locationVersion':loc['version'],'jobId':j['id'],'jobSha256':sha(resolve(root,args.job)),'inputs':inputs,**result};write(out/(args.command+'-manifest.json'),manifest)
 elif args.command=='prepare':prepare(args,root,out)
 else:import_result(args,root,out)
 print(json.dumps({'status':'complete','command':args.command,'out':str(out)}))
if __name__=='__main__':
 try:main()
 except (ValueError,RuntimeError,OSError,KeyError,subprocess.CalledProcessError) as error:print('location workflow: '+str(error),file=sys.stderr);sys.exit(1)
