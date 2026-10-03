import argparse,json,time
from .core import Repository,read_json
from .hf import HFRemote
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True)
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ('enqueue','put'):
        p=commands.add_parser(name);p.add_argument('asset_id');p.add_argument('source');p.add_argument('sha256');p.add_argument('size',type=int)
    p=commands.add_parser('status');p.add_argument('asset_id');p.add_argument('sha256')
    p=commands.add_parser('resolve');p.add_argument('sha256');p.add_argument('size',type=int)
    p=commands.add_parser('get');p.add_argument('sha256');p.add_argument('size',type=int)
    p=commands.add_parser('worker');mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--once',action='store_true');mode.add_argument('--watch',action='store_true')
    args=parser.parse_args();repository=Repository(read_json(args.config))
    if args.command in ('enqueue','put'):
        result=repository.enqueue(args.asset_id,args.source,args.sha256,args.size)
        if args.command=='put':repository.once(HFRemote(repository.config['bucket']),poll=False,asset_id=args.asset_id);result=repository.status(args.asset_id,args.sha256)
    elif args.command=='status':result=repository.status(args.asset_id,args.sha256)
    elif args.command=='resolve':result={'localPath':str(repository.resolve(args.sha256,args.size))}
    elif args.command=='get':
        try:result={'status':'verified-local','localPath':str(repository.get(HFRemote(repository.config['bucket']),args.sha256,args.size))}
        except Exception as exc:result={'status':'pending','errorType':type(exc).__name__}
    else:
        remote=HFRemote(repository.config['bucket']);interval=repository.config.get('pollIntervalSeconds',15)
        if type(interval)!=int or not 1<=interval<=3600:raise ValueError('Invalid watch interval')
        while True:
            try:result={'results':repository.once(remote)}
            except Exception as exc:result={'status':'pending','errorType':type(exc).__name__}
            if args.once:break
            print(json.dumps(result),flush=True);time.sleep(interval)
    print(json.dumps(result))
