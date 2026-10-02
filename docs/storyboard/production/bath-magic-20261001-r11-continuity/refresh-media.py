#!/usr/bin/env python3
"""Consolidate generated selections and explicit R10 baseline pointers; no image copy."""
import fcntl,hashlib,json,os
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parent
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
with (root/'.media.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 prev=json.loads((root/'derivatives.json').read_text()).get('assets',{}) if (root/'derivatives.json').exists() else {}
 deriv={};media={'version':1,'status':'draft-for-review','images':{},'references':[],'documents':[]}
 for lane in ['root','story','geometry']:
  manifest=root/lane/'manifest.json'
  if not manifest.exists():continue
  data=json.loads(manifest.read_text());entries=data.get('assets',[])
  for e in entries:
   sid=e['id'];assert sid not in deriv,('Duplicate selection',sid)
   asset={'slug':sid,'lane':lane,'kind':'generated','status':e.get('status','candidate'),'sourceProduction':root.name.removeprefix('pinpin-')}
   for field in ['master','web']:
    v=e[field];f=root/lane/(v['path'] if isinstance(v,dict) else v);st=f.stat();rel=f.relative_to(root).as_posix();cached=prev.get(sid,{}).get(field,{})
    digest=cached.get('sha256') if cached.get('path')==rel and cached.get('mtimeNs')==st.st_mtime_ns and cached.get('bytes')==st.st_size else sha(f)
    asset[field]={'path':rel,'sha256':digest,'bytes':st.st_size,'mtimeNs':st.st_mtime_ns}
   with Image.open(root/asset['web']['path']) as im:asset['width'],asset['height']=im.size
   asset['generationRecord']=(Path(lane)/e['record']).as_posix();deriv[sid]=asset
 if (root/'reuse-enabled.json').exists() and (root/'story-plan.json').exists():
  plan=json.loads((root/'story-plan.json').read_text());upstreams={}
  for scene in [plan['cover'],*plan['scenes']]:
   sid=scene['id'];sid='title' if sid=='cover' else sid
   if sid in deriv or not scene.get('retainArt'):continue
   production=scene.get('reuseSourceProduction',scene['sourceProduction']);assert production=='bath-magic-20261001-r10-story-repair',production
   if production not in upstreams:upstreams[production]=json.loads((root.parent/('pinpin-'+production)/'derivatives.json').read_text())['assets']
   origin=scene.get('reuseSourceSceneId',scene.get('sourceSceneId',sid));origin='title' if origin=='cover' else origin
   source=upstreams[production][origin]
   asset={**source,'slug':sid,'kind':'upstream unchanged','sourceProduction':source['sourceProduction'],'sourceSceneId':source.get('sourceSceneId',origin),'reusedFromProduction':production,'reusedFromSceneId':origin,'upstreamGenerationRecord':source.get('generationRecord',source.get('upstreamGenerationRecord')),'upstreamReuseRecord':source.get('reuseRecord',source.get('upstreamReuseRecord'))}
   asset.pop('generationRecord',None);asset.pop('reuseRecord',None);deriv[sid]=asset
 for sid,asset in deriv.items():
  display={**asset['web'],'width':asset['width'],'height':asset['height'],'sourceProduction':asset['sourceProduction']}
  if sid=='title':media['images']['cover']=display
  elif sid.startswith('scene-'):media['images'][sid]=display
  else:media['references'].append({**display,'title':sid.replace('-',' ')})
 for name in ['story-plan.json','causal-rhythm.json','REPORT.txt','revision-map.json','derivatives.json','input-preservation.json']:
  if (root/name).exists():media['documents'].append({'path':name,'title':name})
 for filename,data in [('derivatives.json',{'version':1,'assets':deriv}),('media.json',media)]:
  f=root/filename;temp=f.with_name(f'.{f.stem}-{os.getpid()}.json');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(f)
 print(json.dumps({'images':len(media['images']),'new':sum(a['kind']=='generated' for a in deriv.values()),'upstreamPointers':sum(a['kind']=='upstream unchanged' for a in deriv.values())}))
