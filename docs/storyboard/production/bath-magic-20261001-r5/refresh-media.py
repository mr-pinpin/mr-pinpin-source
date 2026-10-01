#!/usr/bin/env python3
"""Index existing review images; does not generate, alter or delete artwork."""
import argparse
import hashlib
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--pack', type=Path, default=Path(__file__).resolve().parent)
args = parser.parse_args()
root = args.pack.resolve()
web = root / 'web'
derivatives_path = root / 'derivatives.json'
derivatives = json.loads(derivatives_path.read_text()).get('assets', {}) if derivatives_path.is_file() else {}
manifest = {'version': 1, 'status': 'draft-for-review', 'images': {}, 'storyboards': [], 'concept': None, 'references': [], 'documents': []}
for path in sorted(web.glob('*')):
    if path.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp'}:
        continue
    entry = {'path': path.relative_to(root).as_posix(), 'bytes': path.stat().st_size,
             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    derivative = derivatives.get(path.stem, {})
    if derivative.get('width') and derivative.get('height'):
        entry.update(width=derivative['width'], height=derivative['height'])
    if path.stem == 'title':
        manifest['images']['cover'] = entry
    elif path.stem.startswith('scene-') and path.stem[6:].isdigit():
        manifest['images'][path.stem] = entry
    elif path.stem == 'channel-guide':
        entry['title']='Temporary channel staging guide · Preproduction reference'
        manifest['references'].append(entry)
    elif path.stem == 'storyboard-concept':
        manifest['concept'] = entry
    elif path.stem.startswith('storyboard-'):
        entry['kind'] = 'overview' if path.stem == 'storyboard-00' else 'sheet'
        entry['number'] = int(path.stem.split('-')[-1])
        manifest['storyboards'].append(entry)
for path in sorted([*(root / 'references').glob('*'), *(root / 'preproduction').glob('*')]):
    if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}:
        manifest['references'].append({'path': path.relative_to(root).as_posix(), 'title': path.stem.replace('-', ' '),
                                       'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for name in ['STORY.md', 'continuity.json', 'REVIEW.md', 'derivatives.json', 'contact-sheets.json', 'input-preservation.json', 'reuse.json']:
    if (root / name).is_file():
        manifest['documents'].append({'path': name, 'title': name})
for path in sorted((root / 'prompts').glob('*')):
    if path.is_file() and path.suffix in {'.txt', '.json', '.md'}:
        manifest['documents'].append({'path': path.relative_to(root).as_posix(), 'title': path.name})
destination = root / 'media.json'
temporary=destination.with_name(f'.media-{os.getpid()}.json')
temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
temporary.replace(destination)
print(json.dumps({'manifest': str(destination), 'images': len(manifest['images']), 'storyboards': len(manifest['storyboards']), 'references': len(manifest['references'])}))
