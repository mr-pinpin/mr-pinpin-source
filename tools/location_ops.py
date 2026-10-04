"""Portable active-bundle location CLI: bounded context/prepare, no providers."""
import argparse,json,os,sys,time,re
from pathlib import Path

def read_json(path,limit):
    path=Path(path)
    if not path.is_file() or path.stat().st_size>limit:raise ValueError('Input unavailable or exceeds bound')
    raw=path.read_bytes()
    if len(raw)>limit:raise ValueError('Input exceeds bound')
    return json.loads(raw,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Nonfinite input')))

def execute(store,runtime,command,payload=None,selectors=None):
    from model import StudioError
    if command not in ('context','prepare'):raise StudioError('Unsupported location operation')
    query={k:[v] for k,v in (selectors or {}).items()} if command=='context' else {}
    response=runtime.invoke('route',store,'GET' if command=='context' else 'POST','/api/location-workflow/'+command,query,None if command=='context' else payload)
    if response is None:raise StudioError('Location workflow route not integrated','business_unavailable',503)
    status,result=response
    if len(json.dumps(result,allow_nan=False).encode())>262144:raise StudioError('Location response exceeds bound')
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',default=os.environ.get('PINPIN_STUDIO_DATA'));parser.add_argument('--runtime-dir',default=os.environ.get('PINPIN_STUDIO_RUNTIME'))
    sub=parser.add_subparsers(dest='command',required=True)
    context=sub.add_parser('context');context.add_argument('--location')
    prepare=sub.add_parser('prepare');prepare.add_argument('envelope',help='Explicit guarded prompt/roles/review JSON')
    args=parser.parse_args(argv)
    if not args.data_dir or not args.runtime_dir:parser.error('Configure PINPIN_STUDIO_DATA/PINPIN_STUDIO_RUNTIME or explicit --data-dir/--runtime-dir; no guessed deployment')
    data=Path(args.data_dir).expanduser().resolve();runtime_dir=Path(args.runtime_dir).expanduser().resolve()
    if not (data/'state.json').is_file():parser.error('Existing Studio DATA state.json required; this CLI never initializes a project')
    deployment=read_json(runtime_dir/'current-deployment.json',65536);stable=deployment.get('stableRelease')
    if not isinstance(stable,str) or not re.fullmatch('[a-f0-9]{64}',stable):parser.error('Verified current deployment stableRelease required')
    kernel=runtime_dir/'stable-releases'/stable;sys.path.insert(0,str(kernel))
    from immutable_bundle import verify_bundle
    verify_bundle(kernel,stable)
    from store import Store
    from business_runtime import BusinessRuntime
    from model import StudioError
    runtime=None
    try:
        runtime=BusinessRuntime(None,runtime_dir,watch=False,read_only=True)
        if not runtime.active:raise StudioError('Active business bundle unavailable','business_unavailable',503)
        store=Store(data)
        if args.command=='context':result=execute(store,runtime,'context',selectors={'location':args.location} if args.location else {})
        else:result=execute(store,runtime,'prepare',payload=read_json(args.envelope,131072))
        print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    except (StudioError,ValueError,OSError,RecursionError) as exc:
        print(json.dumps(exc.payload() if isinstance(exc,StudioError) else {'error':{'message':str(exc),'code':'location_cli'}},ensure_ascii=False),file=sys.stderr);return 1
    finally:
        if runtime:runtime.close()
    return 0
if __name__=='__main__':raise SystemExit(main())
