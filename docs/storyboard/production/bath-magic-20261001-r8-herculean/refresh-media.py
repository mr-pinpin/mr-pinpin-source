#!/usr/bin/env python3
"""Consolidate immutable lane selections without moving their native media."""
import fcntl,hashlib,json,os,re
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parent
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
with (root/'.media.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 prev=json.loads((root/'derivatives.json').read_text()).get('assets',{}) if (root/'derivatives.json').exists() else {}
 deriv={};media={'version':1,'status':'draft-for-review','images':{},'storyboards':[],'concept':None,'references':[],'documents':[]}
 for lane in ['root','story','geometry','reused']:
  manifest=root/lane/'manifest.json'
  if not manifest.exists():continue
  data=json.loads(manifest.read_text());entries=data if isinstance(data,list) else data.get('assets',data.get('entries',[]))
  if isinstance(entries,dict):entries=[dict(v,id=v.get('id',k)) for k,v in entries.items()]
  for e in entries:
   sid=e['id'];assert sid not in deriv,('Duplicate selection',sid,lane)
   asset={'slug':sid,'lane':lane,'kind':e.get('kind','generated'),'status':e.get('status','candidate')}
   for field in ['master','web']:
    v=e[field];file=root/lane/(v['path'] if isinstance(v,dict) else v);stat=file.stat();relative=file.relative_to(root).as_posix();cached=prev.get(sid,{}).get(field,{})
    digest=cached.get('sha256') if cached.get('path')==relative and cached.get('mtimeNs')==stat.st_mtime_ns and cached.get('bytes')==stat.st_size else sha(file)
    asset[field]={'path':relative,'sha256':digest,'bytes':stat.st_size,'mtimeNs':stat.st_mtime_ns}
   with Image.open(root/asset['web']['path']) as image:asset['width'],asset['height']=image.size
   if e.get('record'):asset['generationRecord']=(Path(lane)/e['record']).as_posix()
   if e.get('reuseRecord'):asset['reuseRecord']=(Path(lane)/e['reuseRecord']).as_posix()
   deriv[sid]=asset
   display={**asset['web'],'width':asset['width'],'height':asset['height']}
   if sid=='title':media['images']['cover']=display
   elif re.fullmatch(r'scene-\d{2,3}',sid):media['images'][sid]=display
   else:media['references'].append({**display,'title':sid.replace('-',' ')})
 for f in sorted((root/'web').glob('storyboard-*.webp')):
  with Image.open(f) as image:width,height=image.size
  n=int(f.stem.split('-')[-1]);media['storyboards'].append({'path':f.relative_to(root).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size,'width':width,'height':height,'number':n,'kind':'overview' if n==0 else 'sheet'})
 for folder in ['preproduction']:
  for f in sorted((root/folder).glob('*.webp')):media['references'].append({'path':f.relative_to(root).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size,'title':f.stem.replace('-',' ')})
 for name in ['STORY.md','causal-rhythm.json','continuity.json','REVIEW.md','revision-map.json','derivatives.json','reuse.json','contact-sheets.json','input-preservation.json']:
  if (root/name).exists():media['documents'].append({'path':name,'title':name})
 for lane in ['root','story','geometry']:
  for f in sorted((root/lane/'prompts').glob('*.txt')):media['documents'].append({'path':f.relative_to(root).as_posix(),'title':lane+'/'+f.name})
 for filename,data in [('derivatives.json',{'version':1,'assets':deriv}),('media.json',media)]:
  f=root/filename;temp=f.with_name(f'.{f.stem}-{os.getpid()}.json');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(f)
 print(json.dumps({'images':len(media['images']),'references':len(media['references']),'storyboards':len(media['storyboards'])}))
