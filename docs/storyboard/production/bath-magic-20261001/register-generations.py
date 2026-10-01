#!/usr/bin/env python3
"""Complete source provenance, preserve originals on mounted TB4, and register review derivatives.

Run on the Air: python3 register-generations.py --ids scene-13-v2 scene-15-v1
Use --preserve-only for rejected candidates. Explicitly rejected records are never selected.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--ids', nargs='+', required=True)
parser.add_argument('--source-pack', type=Path, default=Path(__file__).resolve().parent)
parser.add_argument('--mini-pack', type=Path, default=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001'))
parser.add_argument('--preserve-only', action='store_true')
args = parser.parse_args()
source_pack = args.source_pack.resolve()
mini_pack = args.mini_pack
probe = subprocess.run(['test','-d',str(mini_pack)], timeout=3)
if probe.returncode:
    raise SystemExit('TB4 mount unavailable; restore the existing mount before registering images.')
def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()
def copy(source, relative, immutable=False):
    destination = mini_pack / relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        if sha(destination) == sha(source):
            return
        if immutable:
            raise ValueError(f'Master identity conflict: {relative}; supply a new version ID')
    shutil.copy2(source,destination)
for id in args.ids:
    if not re.fullmatch(r'(scene-\d{2}|title|storyboard-concept)-v\d+',id):
        raise ValueError(f'Unexpected generation id: {id}')
    record_path = source_pack / 'records' / f'{id}.json'
    record = json.loads(record_path.read_text())
    prompt_relative = Path(record['promptPath'])
    if prompt_relative.is_absolute() or '..' in prompt_relative.parts:
        raise ValueError('promptPath must be relative to the production pack')
    prompt = source_pack / prompt_relative
    master = Path(record['sourceOutput'])
    reference_paths = [Path(item if isinstance(item,str) else item['path']) for item in record['references']]
    record['referenceIdentities'] = [{'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)} for path in reference_paths]
    record['promptSha256'] = sha(prompt)
    master_relative = Path('masters') / f'{id}{master.suffix}'
    record['master'] = {'path':master_relative.as_posix(),'bytes':master.stat().st_size,'sha256':sha(master)}
    record['approval'] = 'draft-for-review'
    record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    copy(master,master_relative,immutable=True)
    copy(prompt,prompt_relative)
    copy(record_path,Path('records')/record_path.name)
    rejected = 'reject' in str(record.get('visualReview','')).lower()
    if args.preserve_only or rejected:
        print(json.dumps({'id':id,'preserved':True,'selected':False,'reason':'preserve-only or rejected visual review'}))
        continue
    slug = re.sub(r'-v\d+$','',id)
    command = [str(mini_pack/'.venv/bin/python'),str(mini_pack/'accept-asset.py'),
               '--master',master_relative.as_posix(),'--slug',slug,
               '--prompt',prompt_relative.as_posix(),'--generation-record',f'records/{id}.json']
    subprocess.run(['ssh','mini',shlex.join(command)],check=True,timeout=120)
    print(json.dumps({'id':id,'preserved':True,'selected':True,'master':record['master']}))
