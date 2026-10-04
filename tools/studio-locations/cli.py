#!/usr/bin/env python3
"""Location discovery CLI: stdout JSON, structured errors, no implicit network."""
import argparse
import json
from pathlib import Path
import sys
import time
from paths import LocationError, external_path
from indexer import build, read_index
from query import query
from hydration import hydrate


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--catalog',type=Path,help='Optional exported catalog for source-backed verification')
    parser.add_argument('--index',type=Path,required=True,help='Persistent external metadata index')
    commands = parser.add_subparsers(dest='command',required=True)
    index_command = commands.add_parser('index',help='Incrementally scan metadata; never download or read media')
    index_command.add_argument('--studio-data',type=Path,help='Optional existing Studio data root for shared replica IDs')
    commands.add_parser('list',help='List exact IDs and aliases')
    for name in ('query','hydrate'):
        sub = commands.add_parser(name)
        sub.add_argument('location',help='Exact catalog ID or alias; quote multiword aliases')
        sub.add_argument('--scope',choices=('approved','all'),default='approved')
        sub.add_argument('--stop')
        sub.add_argument('--viewpoint')
        sub.add_argument('--probe-media',action='store_true',help='Optional worker-only stat check; leave off interactive queries')
        if name=='hydrate':
            sub.add_argument('--output',required=True,type=Path)
            sub.add_argument('--max-bytes',type=int,default=32*1024*1024)
            sub.add_argument('--media',choices=('references','selected','all'),default='references')
            sub.add_argument('--restore',action='store_true',help='Explicit cold archive restore through existing adapter')
            sub.add_argument('--cache',type=Path)
    args = parser.parse_args(argv)
    started = time.perf_counter()
    try:
        root = args.root.resolve()
        index_path = external_path(root,args.index)
        if args.command=='index':
            result = build(root,index_path,args.studio_data,args.catalog)
        else:
            index = read_index(root,index_path)
            if args.command=='list':
                result = {'schemaVersion':1,'locations':[{k:e[k] for k in ('id','aliases','kind','approval')} for e in index['config']['entries']]}
            else:
                result = query(index,root,args.location,args.scope,args.stop,args.viewpoint,args.probe_media)
                if args.command=='hydrate':
                    if index.get('studioBridge'):
                        result['_hydrationBridge'] = index['studioBridge']
                    result = hydrate(root,result,args.output,args.max_bytes,args.media,args.restore,args.cache)
        result.setdefault('timing',{})['commandSeconds'] = time.perf_counter()-started
        encoded = json.dumps(result,ensure_ascii=False,separators=(',',':'))
        if len(encoded.encode())>256*1024:
            raise LocationError('Metadata response exceeds 256 KiB bound; narrow request')
        print(encoded)
        return 0
    except (LocationError,OSError,ValueError,KeyError) as exc:
        print(json.dumps({'error':{'code':'location_request_rejected','message':str(exc)[:300]},'networkImplicit':False}))
        return 2


if __name__=='__main__':
    sys.exit(main())
