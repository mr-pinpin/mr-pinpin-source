#!/usr/bin/env python3
"""Snapshot this chapter's media to regular files and make its scoped HF manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--pack', type=Path, default=Path(__file__).resolve().parent)
args = parser.parse_args()
root = args.pack.resolve()
stage = root / 'archive-stage'
prefix = Path('docs/storyboard/production/bath-magic-20261002-r15-beaver-aqueduct')
assets = []
for folder in ['root', 'story', 'geometry', 'preproduction', 'boards', 'references', 'browser-check', 'restored']:
    for source in sorted((root / folder).rglob('*')):
        if not source.is_file() or source.suffix.lower() not in {'.png', '.webp', '.jpg', '.jpeg', '.pdf', '.blend', '.exr', '.obj', '.mtl', '.json', '.txt', '.md', '.py'}:
            continue
        if source.is_symlink():
            raise ValueError(f'Use regular source media: {source}')
        relative = prefix / source.relative_to(root)
        destination = stage / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        assets.append({'path':relative.as_posix(), 'role':'archive', 'bytes':destination.stat().st_size,
                       'sha256':digest, 'object':f'sha256/{digest[:2]}/{digest}/{destination.name}'})
manifest = {'version':1, 'bucket':'miguelemosreverte/mr-pinpin-archive', 'assets':assets}
destination = root / 'archive-manifest.json'
destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'manifest':str(destination),'root':str(stage),'assets':len(assets),'bytes':sum(x['bytes'] for x in assets)}))
