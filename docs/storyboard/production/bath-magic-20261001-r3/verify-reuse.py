#!/usr/bin/env python3
"""Verify unchanged reused artwork and its self-contained origin/input records."""
import argparse
import hashlib
import json
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--pack',type=Path,default=Path(__file__).resolve().parent)
parser.add_argument('--origin',type=Path,default=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r2'))
args=parser.parse_args();root=args.pack.resolve();origin=args.origin.resolve()
reuse=json.loads((root/'reuse.json').read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for entry in reuse['items']:
    for kind in ['master','web','originRecord','originPrompt']:
        expected=entry[kind];path=root/expected['path']
        assert path.stat().st_size==expected['bytes'],str(path)
        assert sha(path)==expected['sha256'],str(path)
    for kind,original in [('master','originMaster'),('web','originWeb')]:
        assert entry[kind]['sha256']==entry[original]['sha256'],entry['id']
        assert sha(origin/entry[original]['path'])==entry[kind]['sha256'],entry['id']
    for reference in entry['inputs']:
        assert reference['preservedPaths']
        for path in reference['preservedPaths']:assert sha(root/path)==reference['sha256'],path
print(json.dumps({'reusedAssets':len(reuse['items']),'allCopiesBitIdentical':True,'originBytesUnchanged':True,'allOriginInputsPreserved':True}))
