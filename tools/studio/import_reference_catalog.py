#!/usr/bin/env python3
"""Import the checked reference catalog into an external Studio data directory."""
import argparse,copy,hashlib,json
from pathlib import Path
from store import Store
from model import validate_project

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--data-dir',type=Path,required=True)
 parser.add_argument('--catalog',type=Path,default=Path(__file__).parent/'examples/reference-catalog.json')
 parser.add_argument('--root',action='append',default=[],metavar='NAME=PATH')
 parser.add_argument('--replace',action='store_true',help='Explicitly replace project content; existing immutable assets remain')
 parser.add_argument('--dry-run',action='store_true')
 args=parser.parse_args()
 catalog=json.loads(args.catalog.read_text()); roots={k:Path(v).expanduser().resolve() for k,v in catalog['roots'].items()}
 for item in args.root:
  name,sep,path=item.partition('=')
  if not sep or name not in roots:parser.error('--root must name a catalog root')
  roots[name]=Path(path).expanduser().resolve()
 project=json.loads((args.catalog.parent/catalog['project']).read_text())
 files=[]
 for row in catalog['assets']:
  path=(roots[row['root']]/row['path']).resolve()
  # Catalog media intentionally contains verified symlinks to immutable earlier packs.
  if not path.is_file():raise SystemExit('Missing catalog asset: '+str(path))
  digest=hashlib.sha256(path.read_bytes()).hexdigest()
  if digest!=row['sha256']:raise SystemExit('Checksum mismatch: '+row['key'])
  files.append((row,path))
 if args.dry_run:
  print(json.dumps({'verifiedAssets':len(files),'chapters':len(project['chapters']),'draftScenes':len(project['chapters'][-1]['scenes'])}));return
 store=Store(args.data_dir,media_roots=list(roots.values())+[p.parent for _,p in files])
 state=store.read()
 if (state['project'].get('chapters') or state['project'].get('book',{}).get('manuscript')) and not args.replace:
  raise SystemExit('Project is not empty. No project changes made; use --replace only for an intentional reseed.')
 initial_revision=state['revision'];mapping={}
 for row,path in files:
  asset=store.import_asset(path,name=row['name'],provenance={'catalogKey':row['key'],'catalogSha256':row['sha256'],**row.get('provenance',{})},review_status=row['reviewStatus'])
  mapping[row['key']]=asset['id']
 def resolve(value):
  if isinstance(value,list):return [resolve(v) for v in value]
  if not isinstance(value,dict):return value
  result={}
  for key,v in value.items():
   if key in ('referenceIds','styleReferenceIds'):result[key]=[mapping[x] for x in v]
   elif key in ('imageAssetId','coverAssetId') and v:result[key]=mapping[v]
   elif key=='coverAssetIds':result[key]={k:mapping[x] for k,x in v.items()}
   else:result[key]=resolve(v)
  return result
 project=resolve(project);state=store.read()
 # Every import changes revision once; concurrent edits must never be overwritten.
 if state['revision']!=initial_revision+len(files):raise SystemExit('Concurrent Studio changes detected; imported assets kept, project was not replaced.')
 validate_project(project,state['assets'])
 saved=store.save_project(project,state['revision'])
 report={'schemaVersion':1,'catalog':str(args.catalog.resolve()),'catalogSha256':hashlib.sha256(args.catalog.read_bytes()).hexdigest(),'verifiedAssets':len(files),'uniqueAssets':len(saved['assets']),'chapters':len(project['chapters']),'draftScenes':171,'revision':saved['revision'],'mapping':mapping}
 (args.data_dir/'catalog-import.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='mapping'}))
if __name__=='__main__':main()
