#!/usr/bin/env python3
"""Assemble R24 from immutable R23 and explicitly selected new/repair artwork."""
from pathlib import Path
from PIL import Image
import json,hashlib
p=Path(__file__).resolve().parents[1];b=p.parent/'pinpin-bath-magic-20261002-r23'
load=lambda f:json.loads(f.read_text())
write=lambda f,d:f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
plan=load(p/'plan/story-plan.json');old=load(b/'story-plan.json');before=load(b/'media.json');change=load(p/'plan/change-map.json')
approved=load(p/'preproduction/willow-gag/plan.json')
author={s['id']:s for s in approved['scenes']+approved['captionEdits']}
for scene in plan['scenes']:
 if scene['id']in author:scene['paragraphs']=author[scene['id']]['paragraphs']
allowed=change['newIds']+change['patchIds'];selected={}
for mf in sorted((p/'art').glob('*/selection.json'))+sorted((p/'art').glob('*/selected-assets.json')):
 data=load(mf);rows=data.get('assets',data.get('selected',data))if isinstance(data,dict)else data
 if isinstance(rows,dict):rows=[{'id':k,**v}for k,v in rows.items()]
 for row in rows:
  sid=row.get('id',row.get('sceneId'))
  if sid in allowed and row.get('selected',True)and row.get('rootReview')in ['pass','pass-for-preview']:selected[sid]={**row,'selectionManifest':str(mf.relative_to(p))}
media={'version':1,'status':'R24 production preview; official R18 unchanged','images':before['images'].copy(),'covers':before['covers'],'pendingIds':[],'pendingPatchIds':[],'documents':[{'path':'preproduction/willow-gag/plan.json','title':'25-scene willow gag plan'},{'path':'cycle-board/index.html','title':'Comedy cycles, tempo comparison and full gag'},{'path':'plan/tempo-comparison.json','title':'Actual R23/R24 frame and beat allocation'},{'path':'integration/REPORT.txt','title':'Review and preservation status'},{'path':'selected-assets.json','title':'Selected artwork and exact prompt provenance'}]}
ready=[]
for sid,row in selected.items():
 value=row.get('web',row.get('webPath'))
 if isinstance(value,dict):value=value.get('path')
 if not value:continue
 web=Path(value)
 if not web.is_absolute():web=(p/row['selectionManifest']).parent/web
 if not web.is_file():continue
 sha=hashlib.sha256(web.read_bytes()).hexdigest();assert sha==row['webSha256'],sid
 with Image.open(web)as im:w,h=im.size
 media['images'][sid]={'path':str(web.relative_to(p)),'sourceProduction':p.name.removeprefix('pinpin-'),'sha256':sha,'bytes':web.stat().st_size,'width':w,'height':h};ready.append(sid)
media['pendingNewIds']=[s for s in change['newIds']if s not in ready]
media['pendingIds']=[s for s in allowed if s not in ready]
media['pendingPatchIds']=[s for s in change['patchIds']if s not in ready]
for s in plan['scenes']:
 sid=s['id'];s['artChanged']=sid in change['patchIds']and sid in ready;s['retainArt']=sid not in allowed
 s['feedbackLabel']='New'if sid in change['newIds']else'Revised illustration'if s['artChanged']else'Retained R23'
 s['production']['reviewStatus']='agent-reviewed proposal; user review pending'if sid in ready else'illustration pending'if sid in change['newIds']else'retained R23 preview'
write(p/'baseline/story-plan.json',old);write(p/'baseline/media.json',before)
write(p/'story-plan.json',plan);write(p/'media.json',media);write(p/'selected-assets.json',selected)
write(p/'feedback-map.json',{'changedArtIds':[s for s in change['patchIds']if s in ready],'newIds':change['newIds'],'removed':[],'changes':[]})
write(p/'reader/selection-qa.json',{'storyScenes':len(plan['scenes']),'selected':ready,'pendingNew':media['pendingNewIds'],'pendingRepairs':media['pendingPatchIds'],'retainedMediaDependency':'immutable R23 and predecessors'})
print(json.dumps({'scenes':len(plan['scenes']),'selected':len(ready),'pendingNew':media['pendingNewIds'],'pendingRepairs':media['pendingPatchIds']}))
