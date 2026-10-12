"""Join authored captions and shot directions; never manufacture final art approvals."""
import json,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent;pack=p.parent
plan=json.loads((pack/'BEAT-PLAN.json').read_text())
texts={int(n):t for n,t in [line.split('|',1) for line in (p/'english.txt').read_text().splitlines() if line]}
assert sorted(texts)==list(range(1,216))
shots={}
for f in sorted(p.glob('shots-day*.txt')):
 for line in f.read_text().splitlines():
  n,camera,acting,objects=line.split('|');n=int(n);assert n not in shots
  shots[n]={'camera':camera,'acting':acting,'objects':objects,'status':'authored direction, not pixel-reviewed'}
translations={}
for f in sorted(p.glob('translations-day*.txt')):
 for line in f.read_text().splitlines():
  n,ru,es=line.split('|');n=int(n);assert n not in translations;translations[n]={'ru':[ru],'es':[es]}
records=json.loads((pack/'generation-records.json').read_text()) if (pack/'generation-records.json').exists() else []
for s in plan['scenes']:
 s.pop('acting',None)
 candidates=[r['id'] for r in records if r['id'].startswith(s['id']+'-')]
 if candidates:s['artStatus']='Candidates available; no reader selection';s['artCandidates']=candidates
 s['narration']={'en':[texts[s['number']]]};s['narration'].update(translations.get(s['number'],{}))
 s['captionStatus']='authored localized draft' if s['number'] in translations else 'English authored; translation pending'
 if s['number'] in shots:s['shot']=shots[s['number']]
 env_reuse={70: 'cave-lobby-anchor-v1', 74: 'cave-gallery-anchor-v2', 88: 'cave-echo-anchor-v1', 93: 'cave-fork-anchor-v2', 95: 'cave-blossom-anchor-v2', 128: 'cave-outlet-anchor-v1'}
 if s['number'] in env_reuse:s['visibleCast']=[];s['reusedEnvironmentNative']='native/'+env_reuse[s['number']]+'.png';s['shot']['camera']='Scout/family POV establishing environment; original reviewed anchor view';s['shot']['acting']='Cast offscreen in this deliberate environment POV; next scene returns to interaction.'
 if s['number']==51:s['reusedApprovedImage']='images/published/bath-magic/scene-70.webp'
 if s['number']==138:s['visibleCast']=['DuckAdult1','DuckAdult2',*[f'Duckling{i:02}' for i in range(1,11)]];s['reusedApprovedImage']='images/published/bath-magic/scene-126.webp'
 if s['number']==29:s['visibleCast']+=['BlueTit','Robin']
 if s['number']==78:s['continuityTargets']['infantHolder']='Papa supports infant while Mama unfolds picnic cloth'
 if s['number']==109:s['continuityTargets']['infantHolder']='Papa while Mama checks/refills supplies; return to Mama for walk'
 if s['number'] in [145,150,189,201]:s['continuityTargets']['childSupport']='Papa lowers child onto dry ground after tracing; no unsupported floating child'
 if s['number'] in [143,144,148,188,200]:s['continuityTargets']['childSupport']='Papa steadies/lifts child with two arms, both child paws free for trace; no simultaneous extra hands washing dog'
 if s['number'] in [173,177,182,209]:s['continuityTargets']['markers']={173:'M2 collected; M1 at C0, M3 at C6',177:'M3 collected beside M2; M1 at C0',182:'M1 collected; all three bagged',209:'count three already collected strips; no repeat pickup'}[s['number']]
plan['status']='215 EN/RU/ES captions and individual shot directions authored; editorial/visible art review in progress; no reader cutover'
plan['scriptSources']={'englishSha256':hashlib.sha256((p/'english.txt').read_bytes()).hexdigest(),'authoredShotCount':len(shots),'translatedSceneCount':len(translations)}
(p/'story-script.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
(p/'english-reading.md').write_text('# Scooby Gets a Bath — cave adventure English script draft\n\nAuthoring draft; not the published reader.\n\n'+'\n'.join(f"## Day {d}\n\n"+'\n\n'.join(f"**{s['number']:03} · {s['title']}**\n\n{s['narration']['en'][0]}" for s in plan['scenes'] if s['day']==d) for d in range(1,5))+'\n')
print('Compiled215 English captions and',len(shots),'authored shots')
