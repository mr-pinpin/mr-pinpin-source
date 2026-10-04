"""Reuse an existing registered sheet + generation receipt; no network/artwork calls.
Loads the active immutable business bundle read-only, just like chapter_draft_ops;
only the optimistic Store binding writes. Never activates/builds/replays bundles.
"""
import argparse,hashlib,json,os,re,sys,time
from pathlib import Path

def binding_from_receipt(raw,asset_id,columns,rows,revision):
 if len(raw)>1024*1024:raise ValueError('Generation receipt exceeds1MiB')
 receipt=json.loads(raw);source=receipt['proposedBinding']
 body={'chapterId':source['chapterId'],'sourceVersion':source['version'],'sourceVersionSHA256':source['sha256'],'panelIds':source['panelIds'],'assetId':asset_id,'assetSHA256':receipt['sha256'],'columns':columns,'rows':rows,'promptSHA256':receipt['promptSHA256'],'receiptSHA256':hashlib.sha256(raw).hexdigest(),'expectedRevision':revision}
 if len(json.dumps(body).encode())>131072:raise ValueError('Binding exceeds128KiB')
 return body

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--data-dir',default=os.environ.get('PINPIN_STUDIO_DATA'))
 parser.add_argument('--runtime-dir',default=os.environ.get('PINPIN_STUDIO_RUNTIME'))
 sub=parser.add_subparsers(dest='command',required=True)
 bind=sub.add_parser('bind',help='Bind existing artwork only, never generate or authorize')
 bind.add_argument('--receipt',required=True);bind.add_argument('--asset-id',required=True);bind.add_argument('--columns',type=int,required=True);bind.add_argument('--rows',type=int,required=True);bind.add_argument('--expected-revision',type=int,required=True)
 args=parser.parse_args(argv)
 if not args.data_dir or not args.runtime_dir:parser.error('Explicit --data-dir/--runtime-dir or PINPIN_STUDIO_DATA/PINPIN_STUDIO_RUNTIME required')
 data=Path(args.data_dir).expanduser().resolve();directory=Path(args.runtime_dir).expanduser().resolve()
 if data==directory or data.is_relative_to(directory) or directory.is_relative_to(data):parser.error('Data and runtime roots must be separate')
 deployment=json.loads((directory/'current-deployment.json').read_text());sha=deployment['stableRelease']
 if not isinstance(sha,str) or not re.fullmatch('[a-f0-9]{64}',sha):raise ValueError('Invalid immutable stable release digest')
 stable=directory/'stable-releases'/sha
 sys.path.insert(0,str(stable));sys.dont_write_bytecode=True
 from store import Store
 from business_runtime import BusinessRuntime
 from model import StudioError
 started=time.monotonic()
 with Path(args.receipt).open('rb') as stream:raw=stream.read(1024*1024+1)
 body=binding_from_receipt(raw,args.asset_id,args.columns,args.rows,args.expected_revision)
 runtime=BusinessRuntime(None,directory,watch=False,read_only=True)
 try:
  _,result=runtime.invoke('route',Store(data),'POST','/api/business/draft.sheet.bind.v1',{},body)
  result['cliPreparationToSaveSeconds']=time.monotonic()-started
  print(json.dumps(result,ensure_ascii=False));return 0
 except StudioError as exc:
  print(json.dumps({'error':{'code':getattr(exc,'code','sheet_binding_error'),'message':str(exc)},'automaticRetry':False}),file=sys.stderr);return 1
 finally:runtime.close()
if __name__=='__main__':
 try:raise SystemExit(main())
 except (OSError,ValueError,KeyError):
  print(json.dumps({'error':{'code':'sheet_input_unavailable','message':'Receipt or explicit runtime configuration is unavailable or invalid; inspect local inputs.'},'automaticRetry':False}),file=sys.stderr);raise SystemExit(2)
