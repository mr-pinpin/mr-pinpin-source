"""Full-dimension WebP derivatives of selected masters; originals stay intact."""
from pathlib import Path
from PIL import Image
import hashlib,json
pack=Path(__file__).resolve().parent;root=pack.parents[3]
out=root/'docs/storyboard/images/published/scooby-bath/dig-v3';out.mkdir(parents=True,exist_ok=True)
records=[]
for i in range(1,7):
 name=f'dig-{i:02}';source=pack/'native'/(name+'.png');target=out/(name+'.webp')
 with Image.open(source) as image:
  assert image.size==(1536,1024),(name,image.size)
  image.save(target,'WEBP',quality=86,method=6)
 records.append({'id':name,'native':{'path':str(source.relative_to(root)),'bytes':source.stat().st_size,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()},'reader':{'path':str(target.relative_to(root)),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},'width':1536,'height':1024,'review':'Selected by Codex visual review under user publication instruction; no individual user image approval claimed'})
(pack/'media.json').write_text(json.dumps({'schemaVersion':1,'recipe':{'format':'WEBP','quality':86,'method':6,'resize':False,'crop':False},'images':records},indent=2)+'\n')
print(sum(r['reader']['bytes'] for r in records))
