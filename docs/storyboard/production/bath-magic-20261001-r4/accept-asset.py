#!/usr/bin/env python3
"""Preserve a supplied master, derive native-size WebP, record identities and refresh review.

Run on mini with .venv/bin/python accept-asset.py --master masters/scene-01-v1.png
--slug scene-01 --prompt prompts/scene-01-v1.txt. No image synthesis or retouching.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from PIL import Image, __version__ as pillow_version

parser = argparse.ArgumentParser()
parser.add_argument('--pack', type=Path, default=Path(__file__).resolve().parent)
parser.add_argument('--master', type=Path, required=True)
parser.add_argument('--slug', required=True)
parser.add_argument('--prompt', default=None)
parser.add_argument('--generation-record', default=None)
args = parser.parse_args()
root = args.pack.resolve()
if not re.fullmatch(r'(title|scene-\d{2}|storyboard-\d{2}|storyboard-concept|duck-study|duck-character-study)', args.slug):
    parser.error('slug must be title, scene-NN, storyboard-NN or storyboard-concept')
source = args.master if args.master.is_absolute() else root / args.master
source = source.resolve(strict=True)
if root / 'masters' not in source.parents:
    destination = root / 'masters' / source.name
    destination.parent.mkdir(exist_ok=True, parents=True)
    if destination.exists() and destination.read_bytes() != source.read_bytes():
        raise ValueError('Master filename already exists with different bytes; use a versioned name')
    if not destination.exists():
        shutil.copy2(source, destination)
    source = destination
web = root / 'web' / f'{args.slug}.webp'
web.parent.mkdir(exist_ok=True, parents=True)
temporary = web.with_name(f'.{args.slug}-{os.getpid()}.webp')
with Image.open(source) as image:
    dimensions = image.size
    image.save(temporary, 'WEBP', quality=94, method=6)
def identity(path):
    return {'path':path.relative_to(root).as_posix(), 'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
with (root / '.accept.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    temporary.replace(web)
    record = {'slug':args.slug,'master':identity(source),'web':identity(web),'width':dimensions[0],
              'height':dimensions[1],'recipe':{'tool':'Pillow','version':pillow_version,'format':'WEBP',
              'quality':94,'method':6,'resized':False,'artEdited':False},'prompt':args.prompt,
              'generationRecord':args.generation_record,'approval':'draft-for-review'}
    index = root / 'derivatives.json'
    records = json.loads(index.read_text()) if index.exists() else {'version':1,'assets':{}}
    records['assets'][args.slug] = record
    pending = index.with_suffix('.pending')
    pending.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    pending.replace(index)
    subprocess.run([sys.executable,str(root/'refresh-media.py'),'--pack',str(root)],check=True)
    print(json.dumps(record))
