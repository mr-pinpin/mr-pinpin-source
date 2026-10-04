"""Portable active-bundle book intent CLI: bounded context/save/patch, no providers."""
import argparse,json,os,sys,time,re
from pathlib import Path

def read_json(path,limit):
    path=Path(path)
    if not path.is_file() or path.stat().st_size>limit:raise ValueError('Input unavailable or exceeds bound')
    raw=path.read_bytes()
    if len(raw)>limit:raise ValueError('Input exceeds bound')
    return json.loads(raw,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Nonfinite input')))

def execute(store,runtime,command,payload=None,selectors=None,project_revision=None):
    """Same active immutable business API as app; no script-supplied function dispatch."""
    from model import StudioError
    from business_contract import value_valid,bounded_json
    state=store.read();context={'revision':state['revision'] if project_revision is None else project_revision,'readOnly':project_revision is not None,'deadlineMonotonic':time.monotonic()+10,'businessHash':runtime.active.sha}
    operation={'context':'book.get.v1','save':'book.save.v1','patch':'book.patch.v1'}.get(command)
    if not operation:raise StudioError('Unsupported book operation','invalid_request',400)
    if command=='context':body=dict(selectors or {})
    elif command=='save':
        if not isinstance(payload,dict) or set(payload)-{'spec','baseVersion','baseSHA256','expectedRevision','request'}:raise StudioError('Explicit save envelope required','invalid_request',400)
        body={k:v for k,v in payload.items() if k!='spec'};serialized=json.dumps(payload.get('spec'),ensure_ascii=False,allow_nan=False,separators=(',',':'));body['specChunks']=[serialized[i:i+16000] for i in range(0,len(serialized),16000)]
    else:
        if not isinstance(payload,dict) or set(payload)-{'patches','baseVersion','baseSHA256','expectedRevision','request'}:raise StudioError('Explicit patch envelope required','invalid_request',400)
        body={k:v for k,v in payload.items() if k!='patches'};body['patchesJson']=json.dumps(payload.get('patches'),ensure_ascii=False,allow_nan=False,separators=(',',':'))
    descriptor=next((d for d in runtime.capabilities()['operations'] if d['id']==operation),None)
    if descriptor is None:raise StudioError('Book capabilities are not integrated in active business','business_unavailable',503)
    if not value_valid(descriptor['request'],body):raise StudioError('Explicit version/hash/revision guards and bounded fields required','business_contract',400)
    bounded_json(body,descriptor['maxRequestBytes'])
    if command!='context' and (project_revision is not None or body.get('expectedRevision')!=state['revision']):raise StudioError('Workspace changed or historical; retrieve current context','revision_conflict',409)
    started=time.monotonic()
    route='/api/book-plans/'+command
    query={k:[str(v)] for k,v in body.items()} if command=='context' else {}
    if project_revision is not None:query['revision']=[str(project_revision)]
    response=runtime.invoke('route',store,'GET' if command=='context' else 'POST',route,query,None if command=='context' else body)
    if response is None:raise StudioError('Book CLI routes are not integrated; registry owner must add cli_book_route','business_unavailable',503)
    _,result=response
    bounded_json(result,descriptor['maxResponseBytes'])
    if command=='context':
        result['readOnly']=bool(result.get('readOnly') or result.get('plan',{}).get('historical'))
        result.setdefault('workflow',{}).update({'guidePath':'workflows/book-planning.md','helper':'tools/studio-python tools/book_plan_ops.py','mutations':'Only save/patch, explicit current baseVersion/baseSHA256/expectedRevision; no production authority','ready':bool(result.get('plan',{}).get('ready'))})
    else:result['cliOperationSeconds']=time.monotonic()-started # local helper interval, not model response latency
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',default=os.environ.get('PINPIN_STUDIO_DATA'));parser.add_argument('--runtime-dir',default=os.environ.get('PINPIN_STUDIO_RUNTIME'))
    sub=parser.add_subparsers(dest='command',required=True)
    context=sub.add_parser('context');context.add_argument('--chapter');context.add_argument('--sequence');context.add_argument('--moment');context.add_argument('--page',type=int,default=0);context.add_argument('--version',type=int);context.add_argument('--project-revision',type=int)
    save=sub.add_parser('save');save.add_argument('envelope',help='JSON {spec,request,expectedRevision,baseVersion,baseSHA256 if existing}')
    patch=sub.add_parser('patch');patch.add_argument('--moment',required=True);patch.add_argument('--fields',required=True);patch.add_argument('--version',required=True,type=int);patch.add_argument('--sha256',required=True);patch.add_argument('--expected-revision',required=True,type=int);patch.add_argument('--request',default='')
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
        if args.command=='context':
            mapping={'chapter':'chapterId','sequence':'sequenceId','moment':'momentId','page':'page','version':'version'};selectors={v:getattr(args,k) for k,v in mapping.items() if getattr(args,k) is not None};result=execute(store,runtime,'context',selectors=selectors,project_revision=args.project_revision)
        elif args.command=='save':result=execute(store,runtime,'save',payload=read_json(args.envelope,2*1024*1024))
        else:
            if len(args.fields.encode())>16000:raise StudioError('Patch fields exceed bound','business_contract',413)
            fields=json.loads(args.fields,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('Nonfinite input')))
            result=execute(store,runtime,'patch',payload={'baseVersion':args.version,'baseSHA256':args.sha256,'expectedRevision':args.expected_revision,'request':args.request,'patches':[{'momentId':args.moment,'fields':fields}]})
        print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    except (StudioError,ValueError,OSError,RecursionError) as exc:
        print(json.dumps(exc.payload() if isinstance(exc,StudioError) else {'error':{'message':str(exc),'code':'book_cli'}},ensure_ascii=False),file=sys.stderr);return 1
    finally:
        if runtime:runtime.close()
    return 0
if __name__=='__main__':raise SystemExit(main())
