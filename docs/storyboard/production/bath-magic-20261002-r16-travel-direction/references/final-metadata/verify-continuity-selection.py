#!/usr/bin/env python3
from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;old=p.parent/'pinpin-bath-magic-20261002-r15-beaver-aqueduct'
plan=json.loads((p/'story-plan.json').read_text());before=json.loads((old/'story-plan.json').read_text())
assert len(plan['scenes'])==138
assert [s['id']for s in plan['scenes']]==[s['id']for s in before['scenes']]
for a,b in zip(plan['scenes'],before['scenes']):
 for key in ['paragraphs','number','day','title','cast']:assert a[key]==b[key],(a['id'],key)
a=json.loads((p/'media.json').read_text())['images'];b=json.loads((old/'media.json').read_text())['images']
assert len(a)==139 and set(a)==set(b)
assert {sid for sid in a if a[sid]['sha256']!=b[sid]['sha256']}=={'scene-32b'}
for sid,entry in a.items():
 f=p.parent/('pinpin-'+entry['sourceProduction'])/entry['path']
 assert hashlib.sha256(f.read_bytes()).hexdigest()==entry['sha256'],sid
order=[s['id']for s in plan['scenes']];assert order[order.index('scene-32b')+1]=='scene-32c'
result={'passed':True,'scenes':138,'images':139,'onlyChangedImage':'scene-32b','all138OtherImagesByteIdentical':True,'allCaptionsTitlesCastsDaysOrderUnchanged':True,'nextScene32cPreserved':True}
(p/'reader/selection-qa.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
