#!/usr/bin/env python3
import hashlib,json,shutil
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'art/manifest.json').read_text())
def build(key):
 value=manifest[key];value=value['path'] if isinstance(value,dict) else value
 source=root/'art'/value
 target=root/'web'/f'{key}.webp'
 with Image.open(source) as image:
  rgb=image.convert('RGB')
  if source.suffix.lower()=='.webp':shutil.copy2(source,target)
  else:rgb.save(target,'WEBP',quality=94,method=6)
  width,height=rgb.size
 return {'path':target.relative_to(root).as_posix(),'sha256':sha(target),'width':width,'height':height,'source':source.relative_to(root).as_posix(),'sourceSha256':sha(source),'operation':'unchanged WebP byte copy' if source.suffix.lower()=='.webp' else 'native-size WebP quality94/method6; no resizing or artwork edit'}
data={'status':'bath candidate awaiting user review','artManifestSha256':sha(root/'art/manifest.json'),**{key:build(key) for key in ['original','proposal','rejected','study']}}
old=root.parent/'pinpin-bath-magic-20261001-r5'
selection=json.loads((old/'derivatives.json').read_text())['assets']['scene-30']
assert data['original']['sourceSha256'] in {selection['master']['sha256'],selection['web']['sha256']}
data['documents']=[{'path':f.relative_to(root).as_posix(),'title':f.name} for f in sorted((root/'art').rglob('*')) if f.is_file() and f.suffix in {'.md','.txt','.json'}]
data['documents']+=[{'path':'twelve-mishaps-proposal.json','title':'Original story proposal (not rendered here)'},{'path':'story-discussion.json','title':'Readable discussion and energy principle'}]
(root/'review.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'images':4,'documents':len(data['documents']),'originalR5Matched':True}))
