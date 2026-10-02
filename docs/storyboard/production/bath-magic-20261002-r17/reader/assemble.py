#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,copy,math,shutil
from PIL import Image
B=Path(__file__).resolve().parent.parent
P=B.parent; OLD=P/'pinpin-bath-magic-20261002-r16-travel-direction'
PREVIEW=P/'pinpin-bath-magic-20261001/preview/docs/storyboard'
NAME=B.name.removeprefix('pinpin-')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
draft=read(B/'plan/r17-story-plan.json')
s=next(s for s in draft['scenes'] if s['id']=='scene-20')
s['paragraphs']={'en':['Papa looked at the stream, then at PinPin. He put another bucket under the spill.'],'ru':['Папа посмотрел на струйку, потом на Пин-Пина. Он подставил ещё одно ведёрко.'],'es':['Papá miró el chorro y después a PinPin. Puso otro cubo bajo el agua.']}
s['alt']=copy.deepcopy(s['paragraphs']);s['alt']={k:' '.join(v) for k,v in s['alt'].items()}
write(B/'plan/r17-story-plan.json',draft)
plan=read(OLD/'story-plan.json')
plan.update({'id':NAME,'productionId':NAME,'status':'R17 expanded chapter draft; not published','scenes':draft['scenes'],'days':draft['days'],'storyIllustrationCount':171,'totalIllustrations':172,'source':{'previousPublishedSourceCommit':'d56d45c1c3796def448686b8be2c82b6791f5354','narrativeBaseline':'R16 approved138 scenes','plan':draft['source'],'immutableUpstream':True}})
media=read(OLD/'media.json')
media.update({'status':'R17 draft','references':[],'documents':[{'path':'plan/r17-story-plan.json','title':'Story, camera and continuity plan'},{'path':'plan/preproduction.txt','title':'References and continuity standards'},{'path':'reader/REPORT.txt','title':'Draft report'},{'path':'selected-assets.json','title':'Selected assets and provenance'}]})
selected={}
for lane in ['opening','beaver-return']:
 f=B/'art'/lane/'selection.json'
 if f.exists():
  for k,a in read(f)['selected'].items():selected[k]={'native':a['master'],'nativeSha256':a['masterSha256'],'web':a['web'],'record':str(f.parent/'records'/(k+'-'+a['version']+'.json')),'reviewStatus':a['reviewStatus'],'userReview':'pending','lane':lane}
for lane in ['opening-edits','aqueduct','homeward-finish']:
 f=B/'art'/lane/'selected-assets.json'
 for a in read(f)['assets']:
  if a.get('operation','').startswith('reuse') or not a.get('native'):continue
  n=a['native'];path=Path(n) if isinstance(n,str) else f.parent/n['path']
  selected[a['id']]={'native':str(path),'nativeSha256':a.get('sha256') or n['sha256'],'record':str(f.parent/a['record']) if not Path(a['record']).is_absolute() else a['record'],'reviewStatus':'root visual PASS; user review pending','userReview':'pending','lane':lane,'web':a.get('web')}
(B/'web').mkdir(exist_ok=True)
for k,a in selected.items():
 n=Path(a['native']);assert sha(n)==a['nativeSha256'],k
 web=Path(a['web']) if a.get('web') else B/'web'/(k+'-'+a['nativeSha256'][:12]+'.webp')
 if not web.exists():Image.open(n).convert('RGB').save(web,'WEBP',quality=93,method=6)
 w,h=Image.open(web).size
 media['images'][k]={'path':str(web.relative_to(B)),'sourceProduction':NAME,'sha256':sha(web),'bytes':web.stat().st_size,'width':w,'height':h}
 a['web']=str(web);a['webSha256']=sha(web)
(B/'retained').mkdir(exist_ok=True)
for k,e in media['images'].items():
 if k=='cover' or k in selected:continue
 src=P/('pinpin-'+e['sourceProduction'])/e['path']
 dst=B/'retained'/(k+'.webp')
 assert sha(src)==e['sha256'],k
 if not dst.exists():dst.symlink_to(src)
 e['path']=str(dst.relative_to(B));e['sourceProduction']=NAME;e['retainedApprovedR16']=True
coverbase=P/'pinpin-bath-cover-fix-20261002/publication/site/storyboard/images/published/bath-magic'
media['covers']={}
for lang in ['en','ru','es']:
 src=coverbase/('title-'+lang+'-v2.webp');dest=B/'web'/src.name
 if not dest.exists():dest.symlink_to(src)
 w,h=Image.open(src).size
 media['covers'][lang]={'path':str(dest.relative_to(B)),'sourceProduction':NAME,'sha256':sha(src),'width':w,'height':h}
media['images']['cover']=media['covers']['ru']
oldids={s['id'] for s in read(OLD/'story-plan.json')['scenes']}
for s in plan['scenes']:
 s['artChanged']=s['id'] in selected and s['id'] in oldids
 s['retainArt']=s['id'] not in selected and s['id'] in oldids
 s['feedbackLabel']=('R16 '+str(s['priorR16Number'])) if s.get('priorR16Number') else 'New'
 s['production']['reviewStatus']=selected[s['id']]['reviewStatus'] if s['id'] in selected else ('approved R16 retained' if s['id'] in oldids else 'illustration pending')
assert len(plan['scenes'])==171 and len({s['id'] for s in plan['scenes']})==171
assert oldids <= {s['id'] for s in plan['scenes']}
write(B/'story-plan.json',plan);write(B/'media.json',media);write(B/'selected-assets.json',{'schemaVersion':1,'selected':selected})
write(B/'feedback-map.json',{'schemaVersion':1,'baseline':'Published R16 narrative, d56d45c covers','newIds':[s['id'] for s in plan['scenes'] if s['id'] not in oldids],'changedArtIds':[s['id'] for s in plan['scenes'] if s['artChanged']]})
cfg=read(OLD/'storyboard-layout.json');cfg['sourcePack']=str(B);cfg['groups']=[]
for start in range(0,171,35):
 seq=plan['scenes'][start:start+35];cfg['groups'].append({'title':{'en':f"Scenes {start+1}–{start+len(seq)}",'ru':f"Кадры {start+1}–{start+len(seq)}"},'panels':[{'scene':s['id']} for s in seq]})
write(B/'storyboard-layout.json',cfg)
prod=PREVIEW/'production'/NAME
if not prod.exists():prod.symlink_to(B,target_is_directory=True)
(B/'reader').mkdir(exist_ok=True)
for ext in ['html','css','js']:
 target=PREVIEW/'review'/('bath-magic-r17.'+ext)
 source=B/'reader'/('bath-magic-r17.'+ext)
 if source.exists():
  if target.is_symlink():target.unlink()
  elif target.exists():raise ValueError('Do not overwrite unrelated preview file')
  target.symlink_to(source)
ready=sum(s['id'] in media['images'] for s in plan['scenes'])
write(B/'reader/selection-qa.json',{'narrativeCount':171,'preservedBaselineIds':138,'newIds':33,'ready':ready,'changedArt':len([s for s in plan['scenes'] if s['artChanged']]),'missing':[s['id'] for s in plan['scenes'] if s['id'] not in media['images']]})
print('Ready',ready,'of171, selected',len(selected))
