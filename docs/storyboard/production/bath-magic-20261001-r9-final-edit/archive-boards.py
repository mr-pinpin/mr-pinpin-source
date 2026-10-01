#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent
prefix=Path('docs/storyboard/production/bath-magic-20261001-r9-final-edit')
manifest=json.loads((p/'boards/manifest.json').read_text())
files=set()
for board in manifest['boards']:
    files.add(p/board['path'])
for folder in ['boards']:
    for f in (p/folder).rglob('*'):
        if f.is_file() and f.suffix.lower() in {'.webp','.png'} and 'layout-check' not in f.parts:files.add(f)
files.add(p/'boards/manifest.json')
files.add(p/'boards/qa.json')
files.add(p/'STORYBOARD-WORKFLOW.txt')
assets=[]
for f in sorted(files):
    rel=prefix/f.relative_to(p);dest=p/'archive-stage'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    assets.append({'path':str(rel),'role':'archive','bytes':dest.stat().st_size,'sha256':digest,'object':f'sha256/{digest[:2]}/{digest}/{dest.name}'})
out={'version':1,'bucket':'miguelemosreverte/mr-pinpin-archive','assets':assets}
(p/'archive-manifest.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'artifacts':len(assets),'bytes':sum(a['bytes'] for a in assets)}))
