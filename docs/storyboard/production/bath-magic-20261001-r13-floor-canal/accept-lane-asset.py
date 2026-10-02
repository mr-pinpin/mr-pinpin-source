#!/usr/bin/env python3
"""Preserve one native generation and exact inputs, then update only its lane."""
import argparse,fcntl,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--lane',required=True,choices=['root','story','geometry']);p.add_argument('--id',required=True);p.add_argument('--record',required=True);p.add_argument('--master');p.add_argument('--preserve-only',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parent;lane=root/a.lane
assert re.fullmatch(r'(scene-\d{2,3}|title|[a-z][a-z0-9-]+)',a.id)
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def physical(value):
 f=Path(value)
 if '/.codex/generated_images/' in str(f):return root.parent/'air-space-recovery/codex-generated-images-elder-r6'/str(f).split('/.codex/generated_images/',1)[1]
 return f if f.is_absolute() else lane/f
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():
  assert sha(dst)==sha(src),'Immutable identity conflict: '+str(dst)
 else:shutil.copy2(src,dst)
record_path=lane/a.record;record=json.loads(record_path.read_text())
output=physical(record.get('sourceOutputPhysical',record['sourceOutput']))
master=lane/(a.master or ('masters/'+record_path.stem.replace('-record','')+output.suffix))
copy(output,master)
prompt=physical(record.get('promptPath',record.get('prompt')))
record['promptSha256']=sha(prompt);record['master']={'path':master.relative_to(lane).as_posix(),'sha256':sha(master),'bytes':master.stat().st_size}
record['referenceIdentities']=[];record['preservedReferences']=[]
for item in record.get('references',[]):
 value=item if isinstance(item,str) else item.get('path',item.get('sourcePath',item.get('snapshot')))
 f=physical(value);digest=sha(f)
 if isinstance(item,dict) and item.get('sha256'):assert digest==item['sha256']
 snapshot=lane/'references/inputs'/digest[:12]/f.name;copy(f,snapshot)
 record['referenceIdentities'].append({'path':value,'sha256':digest,'bytes':f.stat().st_size})
 record['preservedReferences'].append({'path':snapshot.relative_to(lane).as_posix(),'sha256':digest})
record['reviewStatus']='illustration candidate; awaiting user feedback'
if a.preserve_only:
 record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'id':a.id,'preserved':True,'selected':False}));raise SystemExit
web=lane/'web'/f'{a.id}.webp';web.parent.mkdir(parents=True,exist_ok=True)
with Image.open(master) as image:
 image=image.convert('RGB');width,height=image.size
 temp=web.with_name(f'.{web.stem}-{os.getpid()}.webp');image.save(temp,'WEBP',quality=94,method=6);temp.replace(web)
record['web']={'path':web.relative_to(lane).as_posix(),'sha256':sha(web),'bytes':web.stat().st_size}
record['dimensions']=[width,height];record['conversion']={'format':'WebP','quality':94,'method':6,'resized':False,'artEdited':False}
record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
entry={'id':a.id,'master':master.relative_to(lane).as_posix(),'web':web.relative_to(lane).as_posix(),'record':a.record,'kind':'generated','status':'candidate','width':width,'height':height}
with (lane/'.manifest.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);file=lane/'manifest.json';data=json.loads(file.read_text()) if file.exists() else {'version':1,'assets':[]}
 entries=data.get('assets',data.get('entries',[]));entries=list(entries.values()) if isinstance(entries,dict) else entries
 entries=[e for e in entries if e['id']!=a.id]+[entry];data['assets']=sorted(entries,key=lambda e:e['id']);data.pop('entries',None)
 tmp=file.with_name(f'.manifest-{os.getpid()}.json');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');tmp.replace(file)
subprocess.run([str(root/'.venv/bin/python'),str(root/'refresh-media.py')],check=True)
print(json.dumps({'id':a.id,'lane':a.lane,'selected':True,'nativeMaster':str(master)}))
