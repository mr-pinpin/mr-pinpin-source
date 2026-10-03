import json,hashlib,sys
from pathlib import Path
from PIL import Image
b=Path(__file__).parent
ident,version,source=sys.argv[1:4]
r=json.loads((b/'records'/f'{ident}-{version}-request.json').read_text())
p=b/'masters'/f'{ident}-{version}.png'
w=b/'web'/f'{ident}-{version}.webp'
Image.open(p).save(w,'WEBP',quality=94)
r.update(schemaVersion=1,id=ident,version=version,tool='image_gen__imagegen',native=str(p),master=str(p),web=str(w),record=str(b/'records'/f'{ident}-{version}.json'),sourceOutputPath=source,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),webSha256=hashlib.sha256(w.read_bytes()).hexdigest(),artistReview='pending',rootReview='pending',userReview='pending',selected=False)
r['width'],r['height']=Image.open(p).size
r['inputs']=[{'path':v,'sha256':hashlib.sha256(Path(v).read_bytes()).hexdigest(),'role':role} for v,role in zip(r['toolArguments']['referenced_image_paths'],r['inputRoles'])]
Path(r['record']).write_text(json.dumps(r,ensure_ascii=False,indent=2))
print(json.dumps({'native':str(p),'sha256':r['sha256']}))
