#!/usr/bin/env python3
from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;old=p.parent/'pinpin-bath-magic-20261001-r11-continuity'
plan=json.loads((p/'story-plan.json').read_text());before=json.loads((old/'story-plan.json').read_text())
expected_order=[s['id']for s in before['scenes']if s['id']!='scene-82']
assert len(plan['scenes'])==112
assert [s['id']for s in plan['scenes']]==expected_order
assert [s['number']for s in plan['scenes']]==list(range(1,113))
old_scenes={s['id']:s for s in before['scenes']}
for s in plan['scenes']:
 assert s['r11Number']==old_scenes[s['id']]['number']
 assert s['feedbackLabel']=='R11 image '+str(s['r11Number'])
 assert s['paragraphs']==old_scenes[s['id']]['paragraphs'],s['id']
a=json.loads((p/'media.json').read_text())['images'];b=json.loads((old/'media.json').read_text())['images']
expected={'scene-75','scene-123','scene-55','scene-55a','scene-55c'}
changed={sid for sid in a if a[sid]['sha256']!=b[sid]['sha256']}
assert changed==expected,(changed,expected)
assert len(a)==113 and 'scene-82'not in a
for sid in a:
 f=p.parent/('pinpin-'+a[sid]['sourceProduction'])/a[sid]['path']
 assert hashlib.sha256(f.read_bytes()).hexdigest()==a[sid]['sha256'],sid
for sid in ['scene-63','scene-45','scene-55b']:
 assert a[sid]['sha256']==b[sid]['sha256'],sid
result={'passed':True,'scenes':112,'allPointersChecked':113,'changedStableIds':sorted(changed),'allOther108SlotsByteIdentical':True,'onlyRemovedScene':'scene-82','removedR11Number':94,'remainingOrderUnchanged':True,'allR11FeedbackNumbersPreserved':True,'allCaptionsUnchangedFromR11':True,'scene63DuckRetained':True,'scene45Unchanged':True}
(p/'reader/selection-qa.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
