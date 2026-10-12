"""Check authored continuity states, not illustration pixels or literary quality."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent;pack=p.parent
s=json.loads((p/'story-script.json').read_text());l=json.loads((p/'continuity-ledger.json').read_text());layout=json.loads((pack/'environment/cave-layout.json').read_text())
assert len(s['scenes'])==len(l['scenes'])==215
assert [x['number'] for x in s['scenes']]==list(range(1,216))
assert all('shot' in x and set(x['narration'])=={'en','ru','es'} and all(x['narration'][lang][0].strip() for lang in ['en','ru','es']) for x in s['scenes'])
assert [sum(x['day']==d for x in s['scenes']) for d in [1,2,3,4]]==[52,54,53,56]
assert all(x['location'] in {n['id'] for n in layout['nodes']}|{'H1','H2'} for x in s['scenes'])
for before,after in zip(l['scenes'],l['scenes'][1:]):assert before['after']==after['before'],(before['id'],after['id'])
for x in l['scenes']:
 st=x['after'];assert len(st['leafBoats'])==2;assert len(st['markers'])==3;assert len(st['towels'])==2
 if x['id'] in ['r6-052','r6-106','r6-159','r6-215']:assert 'FLOWING' not in st['magic']
for n in range(178,194):assert l['scenes'][n-1]['after']['dogSoil'].startswith('HEAVY'),n
for n in range(199,216):assert l['scenes'][n-1]['after']['dogSoil'].startswith('CLEAN'),n
for n in [144,188]:assert 'NO FLOW' in l['scenes'][n-1]['after']['magic']
for n in [150,201,215]:assert l['scenes'][n-1]['after']['magic'].startswith('OFF')
for n in range(165,216):assert all('Rabbit home' in x for x in l['scenes'][n-1]['after']['leafBoats']),n
assert all('Papa bag' in v for v in l['scenes'][-1]['after']['markers'])
assert s['scenes'][-2]['location']=='H2' and s['scenes'][-1]['location']=='H1'
assert s['scenes'][-1]['visibleCast']==['Scooby']
result={'status':'pass','narrativeScenes':215,'readerTarget':216,'authoredEnglishCaptions':215,'authoredRussianCaptions':215,'authoredSpanishCaptions':215,'authoredIndividualShots':215,'checks':['continuous symbolic before/after states','two leaf boats/three markers/two towels throughout','heavy mud persists until wash','clean dog stays clean after full rinse','incomplete magic rings have no flow','both water sessions explicitly stop before night','leaf boats remain home on towel-help day','three route strips collected at ending','family and dog settle in their correct separate rooms','all scene locations exist in authored layout'],'limits':'Does not approve literary quality, multilingual meaning, image anatomy, faces, actual visible props or measured geometry.'}
(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
