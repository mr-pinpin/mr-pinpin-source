#!/usr/bin/env python3
from pathlib import Path
import json,math
p=Path(__file__).resolve().parent
plan=json.loads((p/'story-plan.json').read_text());cfg=json.loads((p/'storyboard-layout.json').read_text());cfg['groups']=[]
size=math.ceil(len(plan['scenes'])/5)
for start in range(0,len(plan['scenes']),size):
 scenes=plan['scenes'][start:start+size];end=start+len(scenes)
 cfg['groups'].append({'title':{'ru':f'Кадры {start+1}–{end}','en':f'Scenes {start+1}–{end}'},'panels':[{'scene':s['id']}for s in scenes]})
assert len(cfg['groups'])==5
(p/'storyboard-layout.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'scenes':len(plan['scenes']),'sheets':5,'order':'story-plan array, not stable-ID sorting'}))
