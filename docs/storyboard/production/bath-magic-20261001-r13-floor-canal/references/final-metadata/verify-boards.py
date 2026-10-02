#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
from PIL import Image,ImageOps,ImageChops
p=Path(__file__).resolve().parent
plan=json.loads((p/'story-plan.json').read_text());manifest=json.loads((p/'boards/manifest.json').read_text())
scenes={s['id']:s for s in plan['scenes']};expected=list(scenes);panels=0
media=json.loads((p/'media.json').read_text())['images']
assert manifest['sourcePack']==str(p)
assert not manifest['preproduction'] and manifest['pendingPanels']==0
for lang in ['ru','en']:
 boards=sorted([b for b in manifest['boards']if b['language']==lang],key=lambda b:b['number'])
 assert len(boards)==5
 assert [panel['sceneId']for b in boards for panel in b['panels']]==expected
 for board in boards:
  for field,key in [('path','sha256'),('master','masterSha256')]:
   assert hashlib.sha256((p/board[field]).read_bytes()).hexdigest()==board[key]
  with Image.open(p/board['master'])as im:
   master=im.convert('RGB')
   for panel in board['panels']:
    assert panel['caption']=='\n'.join(scenes[panel['sceneId']]['paragraphs'][lang])
    assert panel['input'] is not None
    assert panel['input']['sha256']==media[panel['sceneId']]['sha256'],('Stale storyboard panel',panel['sceneId'])
    x,y,w,h=[panel[k]for k in ['x','y','width','height']]
    assert 0<=x and 0<=y and x+w<=board['width']and y+h<=board['height']
    source=Path(panel['input']['path']);assert hashlib.sha256(source.read_bytes()).hexdigest()==panel['input']['sha256']
    with Image.open(source)as original:tile=ImageOps.contain(original.convert('RGB'),(w,round(w*2/3)),Image.Resampling.LANCZOS)
    left=x+(w-tile.width)//2;top=y+(round(w*2/3)-tile.height)//2
    assert ImageChops.difference(tile,master.crop((left,top,left+tile.width,top+tile.height))).getbbox() is None
    panels+=1
proof={'passed':True,'boards':len(manifest['boards']),'panels':panels,'exactCaptions':True,'boundsValid':True,'selectedInputHashesValid':True,'containedSourcePixelsUnchanged':True,'operation':'layout only, no artwork retouching'}
(p/'boards/qa.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
