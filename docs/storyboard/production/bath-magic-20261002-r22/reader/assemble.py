#!/usr/bin/env python3
"""Integrate twenty dam frames into the full chapter, retaining R21 media by reference."""
from pathlib import Path
from PIL import Image
import json,hashlib
p=Path(__file__).resolve().parents[1];u=p.parent/'pinpin-bath-magic-20261002-r21'
load=lambda f:json.loads(f.read_text())
write=lambda f,d:f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
plan=load(p/'plan/story-plan.json');old=load(u/'story-plan.json');before=load(u/'media.json');change=load(p/'plan/replacement-map.json')
newIds=change['newIds'];selected={}
excluded=load(p/'plan/excluded-candidates.json')['candidates']
for mf in sorted((p/'art').glob('*/selection.json'))+sorted((p/'art').glob('*/selected-assets.json')):
 data=load(mf);rows=data.get('assets',data.get('selected',data)) if isinstance(data,dict)else data
 if isinstance(rows,dict):rows=[{'id':k,**v}for k,v in rows.items()]
 for row in rows:
  sid=row.get('id',row.get('sceneId'))
  if sid in newIds and row.get('selected',True) and row.get('rootReview')in ['pass','pass-for-preview']:selected[sid]={**row,'selectionManifest':str(mf.relative_to(p))}
ids={x['id']for x in plan['scenes']}
media={'version':1,'status':'R22 production preview; officialR18 unchanged','images':{k:v for k,v in before['images'].items()if k in ids or k=='cover'},'covers':before['covers'],'pendingIds':[],'documents':[{'path':'preproduction/beaver-dam/plan.json','title':'20-scene dam plan'},{'path':'dam-board/index.html','title':'20 new scenes in one storyboard'},{'path':'reader/REPORT.txt','title':'Review and preservation status'},{'path':'selected-assets.json','title':'Artwork and exact prompt provenance'}]}
for sid,row in selected.items():
 value=row.get('web',row.get('webPath'))
 if isinstance(value,dict):value=value.get('path')
 if not value:continue
 web=Path(value)
 if not web.is_absolute():web=(p/row['selectionManifest']).parent/web
 if not web.is_file():continue
 assert not any(x['id']==sid and f"{sid}-{x['version']}"in web.name for x in excluded),f'Explicitly rejected candidate selected: {web.name}'
 assert hashlib.sha256(web.read_bytes()).hexdigest()==row['webSha256'],f'Selected WebP hash changed: {sid}'
 with Image.open(web)as im:w,h=im.size
 media['images'][sid]={'path':str(web.relative_to(p)),'sourceProduction':p.name.removeprefix('pinpin-'),'sha256':hashlib.sha256(web.read_bytes()).hexdigest(),'bytes':web.stat().st_size,'width':w,'height':h}
ready=[sid for sid in newIds if sid in media['images']]
media['pendingIds']=[sid for sid in newIds if sid not in ready]
for x in plan['scenes']:
 x['artChanged']=False;x['retainArt']=x['id']not in newIds;x['feedbackLabel']='New'if not x['retainArt']else'Retained R21'
 x['production']['reviewStatus']='agent-reviewed proposal; user review pending'if x['id']in ready else'illustration pending'if x['id']in newIds else'retained R21 preview'
(p/'baseline').mkdir(exist_ok=True)
write(p/'baseline/story-plan.json',old);write(p/'baseline/media.json',before)
write(p/'story-plan.json',plan);write(p/'media.json',media);write(p/'selected-assets.json',selected)
removed=[{'id':x['id'],'previousNumber':x['number'],'replacedBy':newIds,'reason':{'en':'This short walkway-tour scene is replaced by the twenty-scene beaver pond and dam sequence. The picnic and all aqueduct work remain afterward.','ru':'Этот короткий эпизод заменён последовательностью из двадцати кадров о бобровом пруде и плотине. Пикник и работа над водостоком сохранены дальше.','es':'Esta breve visita se sustituye por veinte escenas del estanque y la presa. El picnic y todo el trabajo del canal se conservan después.'}}for x in change['oldScenes']]
write(p/'feedback-map.json',{'changedArtIds':[],'newIds':newIds,'removed':removed,'changes':[]})
write(p/'reader/selection-qa.json',{'storyScenes':len(plan['scenes']),'selected':ready,'pending':media['pendingIds'],'retainedMediaDependency':'immutable R21/R20/R19'})
print(json.dumps({'scenes':len(plan['scenes']),'selected':len(ready),'pending':media['pendingIds']}))
