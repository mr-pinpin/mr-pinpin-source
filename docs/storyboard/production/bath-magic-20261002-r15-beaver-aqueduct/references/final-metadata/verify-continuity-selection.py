#!/usr/bin/env python3
from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;old=p.parent/'pinpin-bath-magic-20261002-r14-water-trip';r8=p.parent/'pinpin-bath-magic-20261001-r8-herculean'
plan=json.loads((p/'story-plan.json').read_text());before=json.loads((old/'story-plan.json').read_text())
insert={'scene-05d':['scene-05e','scene-05f','scene-05g'],'scene-30':['scene-30a','scene-30b','scene-30c','scene-30d'],'scene-32':['scene-32'+c for c in 'abcdefghij'],'scene-73':['scene-73d']}
expected=[]
for s in before['scenes']:expected.extend([s['id'],*insert.get(s['id'],[])])
inserted={sid for group in insert.values()for sid in group};edits={'scene-04a','scene-05a','scene-05d','scene-47'}
assert plan['storyIllustrationCount']==138 and plan['totalIllustrations']==139
assert [s['id']for s in plan['scenes']]==expected
assert [s['number']for s in plan['scenes']]==list(range(1,139))
original={s['id']:s for s in before['scenes']}
for s in plan['scenes']:
 for lang in ['ru','en','es']:
  assert s['paragraphs'].get(lang),s['id']
  assert not any(x in text for text in s['paragraphs'][lang]for x in ['[Draft text pending]','[Текст в работе]','[Texto en preparación]']),s['id']
 if s['id']in original:
  assert s['r14Number']==original[s['id']]['number'],s['id']
  if s['id']!='scene-05a':assert s['paragraphs']==original[s['id']]['paragraphs'],('Unexpected existing-caption change',s['id'])
a=json.loads((p/'media.json').read_text())['images'];b=json.loads((old/'media.json').read_text())['images'];d=json.loads((p/'derivatives.json').read_text())['assets']
assert len(a)==139 and set(a)-set(b)==inserted
changed={sid for sid in a if sid in b and a[sid]['sha256']!=b[sid]['sha256']};assert changed==edits,changed
selected_ids={'title',*[s['id']for s in plan['scenes']]}
assert sum(d[sid]['kind']=='generated'for sid in selected_ids)==21
r=json.loads((r8/'derivatives.json').read_text())['assets']['scene-73']
assert d['scene-73d']['kind']=='restored unchanged archive'
assert d['scene-73d']['sourceProduction']=='bath-magic-20261001-r8-herculean'
for field in ['master','web']:
 for key in ['path','sha256','bytes']:assert d['scene-73d'][field][key]==r[field][key],(field,key)
for sid in a:
 f=p.parent/('pinpin-'+a[sid]['sourceProduction'])/a[sid]['path'];assert hashlib.sha256(f.read_bytes()).hexdigest()==a[sid]['sha256'],sid
for sid in ['scene-75','scene-123','scene-45','scene-55','scene-55a','scene-55c']:
 assert a[sid]['sha256']==b[sid]['sha256'],sid
result={'passed':True,'scenes':138,'allPointersChecked':139,'replacedStableIds':sorted(changed),'insertedStableIds':sorted(inserted),'generatedIllustrations':21,'restoredUnchangedR8Scene73As73d':True,'allOther117R14SlotsByteIdentical':True,'approvedPapaAndCanalUnchanged':True,'noScenesRemoved':True,'remainingRelativeOrderUnchanged':True,'existingCaptionOnly05aChanged':True,'allTranslationsFilled':True,'r14FeedbackNumbersPreserved':True}
(p/'reader/selection-qa.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
