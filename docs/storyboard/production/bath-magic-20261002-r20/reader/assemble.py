#!/usr/bin/env python3
"""R20 small overlay; all retained artwork resolves directly to immutable R19."""
from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parents[1];u=p.parent/'pinpin-bath-magic-20261002-r19'
load=lambda f:json.loads(f.read_text())
write=lambda f,d:f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
plan=load(p/'plan/story-plan.json');before=load(u/'media.json');old=load(u/'story-plan.json')
selected={}
for manifest in (p/'art').glob('*/selected-assets.json'):
 for row in load(manifest).get('assets',[]):
  if row['id']=='scene-05g':selected[row['id']]={**row,'selectionManifest':str(manifest.relative_to(p))}
ids={x['id']for x in plan['scenes']}
media={'version':1,'status':'R20 preview; officialR18 unchanged','images':{k:v for k,v in before['images'].items()if k in ids or k=='cover'},'covers':before['covers'],'pendingIds':[],'documents':[{'path':'plan/supersession.json','title':'Why05d was replaced'},{'path':'reader/REPORT.txt','title':'Review status'},{'path':'art/papa-arm/review.html','title':'Papa arm before/after'},{'path':'selected-assets.json','title':'Exact artwork and prompt provenance'}]}
if 'scene-05g' in selected:
 row=selected['scene-05g'];web=Path(row['web'])
 media['images']['scene-05g']={'path':str(web.relative_to(p)),'sourceProduction':p.name.removeprefix('pinpin-'),'sha256':hashlib.sha256(web.read_bytes()).hexdigest(),'bytes':web.stat().st_size,'width':1536,'height':1024}
else:media['pendingIds']=['scene-05g']
for x in plan['scenes']:
 x['artChanged']=x['id']=='scene-05g';x['retainArt']=not x['artChanged']
 x['feedbackLabel']='Corrected' if x['artChanged'] else 'Retained R19 preview'
 x['production']['reviewStatus']='agent-reviewed proposal; user review pending' if x['artChanged'] and not media['pendingIds'] else 'retained R19 preview'
(p/'baseline').mkdir(exist_ok=True)
write(p/'baseline/story-plan.json',old);write(p/'baseline/media.json',before)
write(p/'story-plan.json',plan);write(p/'media.json',media);write(p/'selected-assets.json',selected)
sup=load(p/'plan/supersession.json')
write(p/'feedback-map.json',{'changedArtIds':['scene-05g'],'newIds':[],'removed':sup['removed'],'changes':[{'id':'scene-05c5','reason':{'en':'The shared arrival replaces05d and keeps Mama’s thanks for the water.','ru':'Общий приход домой заменяет05d и сохраняет благодарность Мамы за воду.','es':'La llegada juntos sustituye05d y conserva el agradecimiento de Mamá por el agua.'}}]})
write(p/'reader/selection-qa.json',{'storyScenes':len(plan['scenes']),'selected':list(selected),'pending':media['pendingIds'],'retainedMediaDependency':'immutable R19'})
print(json.dumps({'scenes':len(plan['scenes']),'selected':list(selected),'pending':media['pendingIds']}))
