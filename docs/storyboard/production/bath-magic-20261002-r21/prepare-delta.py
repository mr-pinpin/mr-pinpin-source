#!/usr/bin/env python3
"""Archive only R21 delta files; immutable R20 media is a restore dependency."""
from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;prefix=Path('docs/storyboard/production/bath-magic-20261002-r21')
files=[]
for folder in ['art','plan','reader','integration','baseline','archive-tools']:
 files.extend(f for f in (p/folder).rglob('*')if f.is_file() and '__pycache__'not in f.parts)
for name in ['story-plan.json','media.json','selected-assets.json','feedback-map.json','RESTORE.txt','prepare-delta.py','upload-archive.py','verify-archive-batched.py']:
 files.append(p/name)
entries=[]
for f in sorted(set(files)):
 rel=prefix/f.relative_to(p);dst=p/'archive-stage'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst);sha=hashlib.sha256(dst.read_bytes()).hexdigest()
 entries.append({'path':str(rel),'role':'archive','sha256':sha,'bytes':dst.stat().st_size,'object':f'sha256/{sha[:2]}/{sha}/{dst.name}'})
manifest={'version':1,'bucket':'miguelemosreverte/mr-pinpin-archive','assets':entries}
(p/'archive-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
dependency=json.loads((p.parent/'pinpin-bath-magic-20261002-r20/restore-manifest.json').read_text())
combined={e['path']:e for e in dependency['assets']}
for e in entries:
 assert e['path']not in combined;combined[e['path']]=e
(p/'restore-manifest.json').write_text(json.dumps({**manifest,'assets':list(combined.values())},indent=2)+'\n')
print(json.dumps({'deltaFiles':len(entries),'deltaBytes':sum(e['bytes']for e in entries),'retainedDependencyFiles':len(dependency['assets']),'oldArtworkCopied':False}))
