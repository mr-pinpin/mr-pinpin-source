"""Version-bound EN/RU delivery through verified active runtime, no state mutation."""
import argparse,hashlib,json,os,re,runpy,subprocess,sys,tempfile
from pathlib import Path

def build(store,runtime,args):
 query={'chapterId':[args.chapter],'version':[str(args.version)],'sourceVersionSHA256':[args.sha256],'additionalAssetIds':[json.dumps([args.cover,args.miniature,*args.coloring])]}
 response=runtime.invoke('route',store,'GET','/api/draft-delivery/context',query,None)
 if response is None:raise ValueError('Delivery context route not integrated in active business')
 _,context=response
 out=Path(args.out).resolve()
 source=os.environ.get('PINPIN_STUDIO_SOURCE')
 if source and out.is_relative_to(Path(source).resolve()):raise ValueError('Delivery output must remain outside source')
 if out.exists():raise ValueError('Delivery output must be a NEW directory')
 if out==store.root.resolve() or out.is_relative_to(store.root.resolve()):raise ValueError('Use external output; never write Studio DATA')
 translations=None
 if args.translations:
  raw=Path(args.translations).read_bytes()
  if len(raw)>1024*1024 or hashlib.sha256(raw).hexdigest()!=args.translations_sha256:raise ValueError('Pinned translations SHA/size differs')
  translations=json.loads(raw)
 prepare=runpy.run_path(str(Path(__file__).with_name('prepare.py')))['prepare']
 # All input files temporary outside DATA. No record/registry/state mutation.
 with tempfile.TemporaryDirectory() as tmp:
  record=Path(tmp)/'record.json';raw=json.dumps(context['record'],ensure_ascii=False).encode();record.write_bytes(raw)
  manifests=[]
  try:
   for language in ('en','ru'):
    manifests.append(prepare(record,hashlib.sha256(raw).hexdigest(),args.chapter,args.version,context['assets'],store.root,out/language,language,args.coloring,args.cover,miniature_asset=args.miniature,require_complete=not args.allow_incomplete,source_version_sha=args.sha256,translations=translations))
  except Exception:
   # Partial output retained for diagnosis, never called completed.
   raise
 if args.render:
  if not args.node or not args.playwright_module:raise ValueError('Explicit existing Node and Playwright paths required; no installation')
  for language in ('en','ru'):
   argv=[args.node,str(Path(__file__).with_name('render.cjs')),'--dir',str(out/language),'--playwright-module',args.playwright_module]
   if args.pdfkit_verifier:argv+=['--pdfkit-verifier',args.pdfkit_verifier]
   subprocess.run(argv,check=True,timeout=120)
  manifests=[json.loads((out/lang/'delivery-manifest.json').read_text()) for lang in ('en','ru')]
 return {'chapterId':args.chapter,'version':args.version,'sourceVersionSHA256':args.sha256,'unpublished':True,'languages':manifests,'pdfBuilt':bool(args.render),'stateModified':False}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-dir',default=os.environ.get('PINPIN_STUDIO_DATA'));p.add_argument('--runtime-dir',default=os.environ.get('PINPIN_STUDIO_RUNTIME'))
 p.add_argument('--chapter',required=True);p.add_argument('--version',required=True,type=int);p.add_argument('--sha256',required=True);p.add_argument('--cover',required=True);p.add_argument('--miniature',required=True);p.add_argument('--coloring',action='append',required=True);p.add_argument('--out',required=True);p.add_argument('--allow-incomplete',action='store_true');p.add_argument('--translations');p.add_argument('--translations-sha256');p.add_argument('--render',action='store_true');p.add_argument('--node',default=os.environ.get('PINPIN_STUDIO_NODE'));p.add_argument('--playwright-module',default=os.environ.get('PLAYWRIGHT_MODULE'));p.add_argument('--pdfkit-verifier');a=p.parse_args(argv)
 if not a.data_dir or not a.runtime_dir:p.error('Configured DATA/RUNTIME required')
 if len(a.coloring)!=3:p.error('Exactly three registered coloring IDs required')
 if not re.fullmatch('[a-f0-9]{64}',a.sha256):p.error('Full exact saved version hash required')
 runtime=None
 try:
  runtime_dir=Path(a.runtime_dir);deployment=runtime_dir/'current-deployment.json'
  if deployment.stat().st_size>65536:raise ValueError('Deployment receipt too large')
  stable=json.loads(deployment.read_text())['stableRelease']
  if not re.fullmatch('[a-f0-9]{64}',stable):raise ValueError('Invalid stable release')
  kernel=runtime_dir/'stable-releases'/stable;sys.path.insert(0,str(kernel))
  from immutable_bundle import verify_bundle
  verify_bundle(kernel,stable)
  from store import Store
  from business_runtime import BusinessRuntime
  if not (Path(a.data_dir)/'state.json').is_file():raise ValueError('Existing state required')
  runtime=BusinessRuntime(None,runtime_dir,watch=False,read_only=True)
  if not runtime.active:raise ValueError('Active business unavailable')
  print(json.dumps(build(Store(a.data_dir),runtime,a),ensure_ascii=False));return 0
 except Exception as exc:
  print(json.dumps({'error':str(exc),'completed':False}),file=sys.stderr);return 1
 finally:
  if runtime:runtime.close()
if __name__=='__main__':raise SystemExit(main())
