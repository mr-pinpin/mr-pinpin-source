#!/usr/bin/env python3
"""Assemble R18 from immutable R17 and selected narrow corrections."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image
P=Path(__file__).resolve().parents[1];U=P.parent/'pinpin-bath-magic-20261002-r17'
load=lambda p:json.loads(p.read_text())
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
changed=['scene-03g','scene-05f','scene-05g1','scene-05g2','scene-63','scene-83','scene-84']
added=['scene-05f1','scene-05f2'];selected={}
for f in sorted((P/'art').glob('*/selection.json'))+sorted((P/'art').glob('*/selected-assets.json')):
 d=load(f);rows=d.get('assets',d.get('selected',d)) if isinstance(d,dict) else d
 if isinstance(rows,dict):rows=[{'id':k,**v} for k,v in rows.items()]
 for row in rows:
  sid=row.get('id',row.get('sceneId'))
  if sid in changed+added:selected[sid]={**row,'selectionManifest':str(f.relative_to(P))}
plan=load(P/'plan/story-plan.json');old=load(U/'story-plan.json');before=load(U/'media.json')
for directory in ['web','retained','baseline/web']: (P/directory).mkdir(parents=True,exist_ok=True)
def link(dst,src):
 if dst.is_symlink() or dst.exists():dst.unlink()
 dst.symlink_to(src.resolve())
media={'version':1,'status':'R18 review','images':{},'covers':{},'pendingIds':[],'documents':[{'path':'plan/story-plan.json','title':'R18 story and camera plan'},{'path':'reader/REPORT.txt','title':'Review and publication status'}]}
baseline={'version':1,'images':{},'covers':{}}
for sid,row in before['images'].items():
 src=U/row['path'];dst=P/'baseline/web'/(sid+'.webp');link(dst,src)
 baseline['images'][sid]={**row,'sourceProduction':P.name.removeprefix('pinpin-'),'path':str(dst.relative_to(P))}
 if sid=='cover':continue
 dst=P/'retained'/(sid+'.webp');link(dst,src)
 media['images'][sid]={**row,'sourceProduction':P.name.removeprefix('pinpin-'),'path':str(dst.relative_to(P)),'retainedR17':True}
for lang in ['en','ru','es']:
 src=U/'web'/('title-'+lang+'-v2.webp');dst=P/'web'/src.name;link(dst,src)
 media['covers'][lang]={'path':str(dst.relative_to(P)),'sourceProduction':P.name.removeprefix('pinpin-'),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'width':1024,'height':1536}
media['images']['cover']=media['covers']['ru']
for sid,row in selected.items():
 value=row.get('web',row.get('webPath'))
 if isinstance(value,dict):value=value.get('path')
 if not value:continue
 src=Path(value)
 if not src.is_absolute():
  possibilities=[P/src,(P/row['selectionManifest']).parent/src]
  src=next((x for x in possibilities if x.is_file()),possibilities[0])
 if not src.is_file():continue
 sha=hashlib.sha256(src.read_bytes()).hexdigest();dst=P/'web'/(sid+'-'+sha[:12]+'.webp');link(dst,src)
 with Image.open(src) as im:w,h=im.size
 media['images'][sid]={'path':str(dst.relative_to(P)),'sourceProduction':P.name.removeprefix('pinpin-'),'sha256':sha,'bytes':src.stat().st_size,'width':w,'height':h,'selectionManifest':row['selectionManifest']}
ready=set(sid for sid in changed+added if sid in media['images'] and not media['images'][sid].get('retainedR17'))
media['pendingIds']=[sid for sid in changed+added if sid not in ready]
for x in plan['scenes']:
 x['artChanged']=x['id'] in changed;x['retainArt']=x['id'] not in changed+added
 x['feedbackLabel']='New' if x['id'] in added else 'Corrected' if x['id'] in changed else 'Retained R17'
 x['production']={**x.get('production',{}),'reviewStatus':'selected candidate; awaiting final review' if x['id'] in ready else 'illustration pending' if x['id'] in media['pendingIds'] else 'retained R17'}
media['images'].pop('scene-62b',None)
write(P/'story-plan.json',plan);write(P/'media.json',media);write(P/'baseline/story-plan.json',old);write(P/'baseline/media.json',baseline)
write(P/'feedback-map.json',{'newIds':added,'changedArtIds':changed,'removed':[{'id':'scene-62b','previousNumber':126,'mergedInto':'scene-63'}]})
write(P/'selected-assets.json',selected)
write(P/'reader/selection-qa.json',{'storyScenes':len(plan['scenes']),'new':len(added),'changed':len(changed),'selected':sorted(ready),'pending':media['pendingIds']})
print(json.dumps({'scenes':len(plan['scenes']),'selected':len(ready),'pending':media['pendingIds']}))
