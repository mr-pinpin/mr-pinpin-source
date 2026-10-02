#!/usr/bin/env python3
"""Check the scoped manifest/receipt identities without trusting a success label alone."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--pack',type=Path,default=Path(__file__).resolve().parent)
parser.add_argument('--current',action='store_true',help='Also require every present source media file to match the snapshot')
args=parser.parse_args()
root=args.pack.resolve()
manifest=json.loads((root/'archive-manifest.json').read_text())
receipt=json.loads((root/'archive-receipt.json').read_text())
assert manifest['version']==receipt['version']==1
assert receipt['action'] in {'push','verify'}
assert receipt['verified'] is True and receipt['dry_run'] is False
assert manifest['bucket']==receipt['bucket']=='miguelemosreverte/mr-pinpin-archive'
entries={x['path']:x for x in receipt['entries']}
assert len(entries)==len(receipt['entries'])==len(manifest['assets'])
prefix='docs/storyboard/production/bath-magic-20261001-r11-continuity/'
for asset in manifest['assets']:
    entry=entries[asset['path']]
    assert entry['verified'] is True and entry['remote_verified'] is True,asset['path']
    for field in ['path','role','bytes','sha256','object']:
        assert asset[field]==entry[field],(asset['path'],field)
    if args.current:
        assert asset['path'].startswith(prefix)
        path=root/asset['path'][len(prefix):]
        assert path.stat().st_size==asset['bytes'],str(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==asset['sha256'],str(path)
if args.current:
    present={prefix+path.relative_to(root).as_posix()
             for folder in ['root','story','geometry','preproduction','boards','references','browser-check']
             for path in (root/folder).rglob('*')
             if path.is_file() and path.suffix.lower() in {'.png','.webp','.jpg','.jpeg','.pdf','.blend','.exr','.obj','.mtl','.json','.txt','.md','.py'}}
    assert present==set(entries),{'unpreserved':sorted(present-set(entries)),'absent':sorted(set(entries)-present)}
print(json.dumps({'verified':True,'assets':len(entries),'bytes':sum(x['bytes'] for x in manifest['assets']),'currentFilesChecked':args.current}))
