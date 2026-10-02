#!/usr/bin/env python3
"""Copy source-only R14 provenance into the canonical checkout; never stage media."""
from pathlib import Path
import json,shutil
pack=Path(__file__).resolve().parent
repo=pack.parent/'pinpin-workspace/mr-pinpin-source'
dest=repo/'docs/storyboard/production'/pack.name.removeprefix('pinpin-')
extensions={'.json','.txt','.py','.cjs','.js','.html','.css','.md'}
skip={'.venv','archive-stage','archive-readback','__pycache__'}
copied=[]
for f in pack.rglob('*'):
 rel=f.relative_to(pack)
 if any(part in skip or part.startswith('.') for part in rel.parts):continue
 if not f.is_file() or f.suffix not in extensions:continue
 if f.name in {'source-files.json'}:continue
 target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
 copied.append(target.relative_to(repo).as_posix())
for name,source in [('bath-magic-20261002-r14-water-trip.json','archive-manifest.json'),('bath-magic-20261002-r14-water-trip-receipt.json','archive-receipt.json')]:
 if (pack/source).exists():
  target=repo/'assets'/name;shutil.copy2(pack/source,target);copied.append(target.relative_to(repo).as_posix())
for ext in ['html','css','js']:copied.append('docs/storyboard/review/bath-magic-r14-water-trip.'+ext)
(pack/'source-files.json').write_text(json.dumps(sorted(copied),indent=2)+'\n')
print(json.dumps({'sourceFiles':len(copied),'binaryFiles':0}))
