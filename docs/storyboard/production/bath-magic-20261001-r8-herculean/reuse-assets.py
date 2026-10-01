#!/usr/bin/env python3
"""Import only explicit inspected reuse selections, retaining exact origin lineage."""
import hashlib,json,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent;lane=root/'reused'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):return {'path':p.relative_to(root).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def copy(p,dest):
 dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert sha(dest)==sha(p),'Immutable reused bytes changed: '+str(dest)
 else:shutil.copy2(p,dest)
 return identity(dest)
def relative(origin,value):return Path(value) if Path(value).is_absolute() else origin/value
plan=json.loads((root/'story-plan.json').read_text())
old=json.loads((lane/'manifest.json').read_text()) if (lane/'manifest.json').exists() else {'version':1,'assets':[]}
assets={a['id']:a for a in old['assets']};items={x['id']:x for x in json.loads((root/'reuse.json').read_text())['items']} if (root/'reuse.json').exists() else {}
for scene in [plan['cover'],*plan['scenes']]:
 if not scene.get('reusedFrom'):continue
 sid=scene['id'];source_id=scene['reusedFrom'];production=scene['reuseSourceProduction'];origin=root.parent/('pinpin-'+production)
 if sid in items:
  assert items[sid]['sourceProduction']==production and items[sid]['sourceId']==source_id,('Reuse mapping changed',sid)
  continue
 upstream=None;input_sources=[]
 if scene.get('reuseMaster'):
  master=origin/scene['reuseMaster'];web=origin/scene['reuseWeb'];record=origin/scene['reuseGenerationRecord']
  record_data=json.loads(record.read_text());prompt=relative(origin,record_data.get('promptPath',record_data.get('prompt')))
 else:
  selected=json.loads((origin/'derivatives.json').read_text())['assets'][source_id]
  master=origin/selected['master']['path'];web=origin/selected['web']['path']
  assert sha(master)==selected['master']['sha256'] and sha(web)==selected['web']['sha256']
  if selected.get('reuseRecord'):
   prior=next(x for x in json.loads((origin/'reuse.json').read_text())['items'] if x['id']==source_id)
   record=origin/prior['originRecord']['path'];prompt=origin/prior['originPrompt']['path'];upstream=prior
   for ref in prior['inputs']:input_sources.append((origin/ref['preservedPaths'][0],ref['sha256'],ref.get('originalPath','')))
   record_data=json.loads(record.read_text())
  else:
   record=origin/selected['generationRecord'];record_data=json.loads(record.read_text());prompt=relative(origin,record_data.get('promptPath',record_data.get('prompt')))
 if not input_sources and record_data.get('references'):
  proof_path=origin/'input-preservation.json'
  proof=None
  if proof_path.exists():proof=next((x for x in json.loads(proof_path.read_text())['generations'] if x['record']==record.relative_to(origin).as_posix()),None)
  if proof:
   for ref in proof['inputs']:input_sources.append((origin/ref['preservedPaths'][0],ref['sha256'],ref.get('originalPath','')))
  elif record_data.get('preservedReferences'):
   for ref in record_data['preservedReferences']:input_sources.append((relative(origin,ref['path']),ref['sha256'],ref['path']))
  else:
   supplied={v['path']:v for v in record_data.get('inputs',[])}
   for ref in record_data['references']:
    if isinstance(ref,str):ref=supplied.get(ref,{'path':ref})
    value=ref.get('snapshot',ref.get('path',ref.get('sourcePath')))
    actual=relative(origin,value);input_sources.append((actual,ref.get('sha256',sha(actual)),ref.get('sourcePath',ref.get('path',value))))
 info={'id':sid,'operation':'reuse unchanged; not newly generated','sourceProduction':production,'sourceId':source_id,'sourceRoot':str(origin),'originMaster':{'path':master.relative_to(origin).as_posix(),'sha256':sha(master),'bytes':master.stat().st_size},'originWeb':{'path':web.relative_to(origin).as_posix(),'sha256':sha(web),'bytes':web.stat().st_size}}
 info['master']=copy(master,lane/'masters'/sid/master.name);info['web']=copy(web,lane/'web'/f'{sid}.webp')
 info['originRecord']=copy(record,lane/'records'/sid/'origin-record.json');info['originPrompt']=copy(prompt,lane/'records'/sid/'origin-prompt.txt')
 if record_data.get('promptSha256'):assert sha(prompt)==record_data['promptSha256'],sid
 info['inputs']=[]
 for source,digest,label in input_sources:
  assert sha(source)==digest,(sid,str(source));saved=copy(source,lane/'references'/digest[:12]/source.name)
  info['inputs'].append({'originalPath':label,'sha256':digest,'preservedPaths':[saved['path']]})
 if upstream:info['upstreamOrigin']=upstream
 dest=lane/'records'/sid/'reuse.json';dest.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
 assets[sid]={'id':sid,'master':Path(info['master']['path']).relative_to('reused').as_posix(),'web':Path(info['web']['path']).relative_to('reused').as_posix(),'reuseRecord':dest.relative_to(lane).as_posix(),'kind':'reused unchanged','status':'selected draft'}
 items[sid]=info
(lane/'manifest.json').write_text(json.dumps({'version':1,'assets':list(assets.values())},ensure_ascii=False,indent=2)+'\n')
(root/'reuse.json').write_text(json.dumps({'version':1,'items':list(items.values())},ensure_ascii=False,indent=2)+'\n')
subprocess.run([str(root/'.venv/bin/python'),str(root/'refresh-media.py')],check=True)
print(json.dumps({'reusedSelections':len(items),'exactMasterAndWebCopies':True}))
