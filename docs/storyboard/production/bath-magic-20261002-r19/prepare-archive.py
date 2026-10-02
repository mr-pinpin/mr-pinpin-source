#!/usr/bin/env python3
"""Freeze a portable R19 archive, dereferencing intentional media links."""
import hashlib,json,shutil,os
from pathlib import Path
root=Path(__file__).resolve().parent
prefix=Path('docs/storyboard/production/bath-magic-20261002-r19')
stage=root/'archive-stage'
suffixes={'.png','.webp','.jpg','.jpeg','.json','.txt','.md','.py','.cjs','.js','.html','.css','.mmd','.svg'}
folders=['art','web','retained','baseline','boards','new-storyboards','walk-board','plan','audit','integration','reader','archive-tools']
sources=[]
for folder in folders:
 for base,dirs,names in os.walk(root/folder,followlinks=True):
  dirs[:]=[d for d in dirs if d not in ['__pycache__','archive-stage','archive-readback','.git']]
  for name in names:
   f=Path(base)/name
   if f.is_file() and f.suffix.lower() in suffixes:sources.append(f)
for f in root.iterdir():
 if f.is_file() and f.suffix.lower() in suffixes and not f.name.startswith('archive-'):
  sources.append(f)
entries=[]
for f in sorted(set(sources)):
 rel=prefix/f.relative_to(root);dst=stage/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(f,dst)
 sha=hashlib.sha256(dst.read_bytes()).hexdigest()
 entries.append({'path':str(rel),'role':'archive','bytes':dst.stat().st_size,'sha256':sha,'object':f'sha256/{sha[:2]}/{sha}/{dst.name}'})
manifest={'version':1,'bucket':'miguelemosreverte/mr-pinpin-archive','assets':entries}
(root/'archive-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':len(entries),'bytes':sum(e['bytes'] for e in entries)}))
