from pathlib import Path
import json,sys,shutil,hashlib,datetime
from PIL import Image
lane=Path(__file__).resolve().parent;b=lane.parents[2];shared=Path('/Volumes/TB4/mac-mini-storage/shared')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):
 f=Path(p)
 if f.exists():return f
 n=f.name
 fixed={'scene-32b-v1.png':shared/'pinpin-bath-magic-20261002-r16-travel-direction/geometry/masters'/n,'scene-123-v1.png':shared/'pinpin-bath-magic-20261001-r12-house-layout/root/masters'/n}
 if n in fixed:return fixed[n]
 for r in [lane/'masters'/n,lane/'studies'/n,shared/'pinpin-bath-magic-20261002-r15-beaver-aqueduct/geometry/masters'/n]:
  if r.exists():return r
 raise RuntimeError('Missing reference '+p)
for j in json.load(open(sys.argv[1])):
 stem=j['id']+'-'+j['version'];source=Path(j['original'].replace('/Users/miguel_lemos/.codex/generated_images','/Volumes/TB4/mac-mini-storage/shared/air-space-recovery/codex-generated-images-elder-r6'));assert source.exists()
 master=lane/'masters'/(stem+'.png');shutil.copy2(source,master);assert sha(source)==sha(master)
 prompt=lane/'prompts'/(stem+'.txt');prompt.write_text(j['prompt']+'\n')
 im=Image.open(master);web=lane/'web'/(stem+'.webp');im.convert('RGB').save(web,'WEBP',quality=93,method=6)
 record={'id':j['id'],'version':j['version'],'tool':'image_gen__imagegen','master':str(master),'masterSha256':sha(master),'masterBytes':master.stat().st_size,'dimensions':list(im.size),'originalToolOutput':j['original'],'durableToolOutput':str(source),'prompt':str(prompt),'promptSha256':sha(prompt),'toolArguments':{'prompt':j['prompt'],'referenced_image_paths':j['refs'],'transparent_background':False},'references':[{'path':str(ref(p)),'sha256':sha(ref(p))} for p in j['refs']],'web':str(web),'webSha256':sha(web),'reviewStatus':j.get('reviewStatus','agent visual pass; root review pending'),'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 (lane/'records'/(stem+'.json')).write_text(json.dumps(record,indent=2))
 if j.get('selected',True):
  mf=lane/'selection.json';data=json.loads(mf.read_text());data['selected'][j['id']]=record;mf.write_text(json.dumps(data,indent=2))
 print(stem,sha(master),flush=True)
