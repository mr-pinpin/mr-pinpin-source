#!/usr/bin/env python3
from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;old=p.parent/'pinpin-bath-magic-20261001-r13-floor-canal'
plan=json.loads((p/'story-plan.json').read_text());before=json.loads((old/'story-plan.json').read_text())
insert={'scene-04':['scene-04a','scene-04b','scene-04c','scene-04d'],'scene-05':['scene-05a','scene-05b','scene-05c','scene-05d']}
expected=[]
for s in before['scenes']:expected.extend([s['id'],*insert.get(s['id'],[])])
new_ids={sid for ids in insert.values()for sid in ids}
replaced={'scene-04','scene-05'}
assert plan['storyIllustrationCount']==120 and plan['totalIllustrations']==121
assert [s['id']for s in plan['scenes']]==expected
assert [s['number']for s in plan['scenes']]==list(range(1,121))
original={s['id']:s for s in before['scenes']}
for s in plan['scenes']:
 for lang in ['ru','en','es']:
  assert s['paragraphs'].get(lang),s['id']
  assert not any(x in text for text in s['paragraphs'][lang]for x in ['[Draft text pending]','[Текст в работе]','[Texto en preparación]']),s['id']
 if s['id'] in original:
  assert s['r13Number']==original[s['id']]['number'],s['id']
  if s['id'] not in replaced:assert s['paragraphs']==original[s['id']]['paragraphs'],('Unexpected caption edit',s['id'])
a=json.loads((p/'media.json').read_text())['images'];b=json.loads((old/'media.json').read_text())['images']
assert len(a)==121 and set(a)-set(b)==new_ids
changed={sid for sid in a if sid in b and a[sid]['sha256']!=b[sid]['sha256']}
assert changed==replaced,changed
for sid in a:
 f=p.parent/('pinpin-'+a[sid]['sourceProduction'])/a[sid]['path']
 assert hashlib.sha256(f.read_bytes()).hexdigest()==a[sid]['sha256'],sid
for sid in ['scene-06','scene-75','scene-123','scene-63','scene-45','scene-55','scene-55a','scene-55c']:
 assert a[sid]['sha256']==b[sid]['sha256'],sid
result={'passed':True,'scenes':120,'allPointersChecked':121,'replacedStableIds':sorted(changed),'insertedStableIds':sorted(new_ids),'allOther111SlotsByteIdentical':True,'approvedPapaAndCanalUnchanged':True,'noScenesRemoved':True,'remainingRelativeOrderUnchanged':True,'allTranslationsFilled':True,'r13FeedbackNumbersPreserved':True}
(p/'reader/selection-qa.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
