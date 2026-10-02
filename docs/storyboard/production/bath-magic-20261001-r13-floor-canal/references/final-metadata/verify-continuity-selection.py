#!/usr/bin/env python3
from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;old=p.parent/'pinpin-bath-magic-20261001-r12-house-layout'
plan=json.loads((p/'story-plan.json').read_text());before=json.loads((old/'story-plan.json').read_text())
assert plan['storyIllustrationCount']==112 and plan['totalIllustrations']==113
assert [(s['id'],s['number'])for s in plan['scenes']]==[(s['id'],s['number'])for s in before['scenes']]
for s,o in zip(plan['scenes'],before['scenes']):
 assert s['paragraphs']==o['paragraphs'],s['id']
 assert s['r12Number']==o['number']
a=json.loads((p/'media.json').read_text())['images'];b=json.loads((old/'media.json').read_text())['images']
assert set(a)==set(b) and len(a)==113
changed={sid for sid in a if a[sid]['sha256']!=b[sid]['sha256']}
assert changed=={'scene-55','scene-55a','scene-55c'},changed
for sid in a:
 f=p.parent/('pinpin-'+a[sid]['sourceProduction'])/a[sid]['path']
 assert hashlib.sha256(f.read_bytes()).hexdigest()==a[sid]['sha256'],sid
for sid in ['scene-75','scene-123','scene-63','scene-45','scene-55b']:
 assert a[sid]['sha256']==b[sid]['sha256'],sid
result={'passed':True,'scenes':112,'allPointersChecked':113,'changedStableIds':sorted(changed),'allOther110SlotsByteIdentical':True,'approvedPapa75And123Unchanged':True,'noScenesRemovedOrAdded':True,'allNumbersOrderAndCaptionsUnchanged':True}
(p/'reader/selection-qa.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
