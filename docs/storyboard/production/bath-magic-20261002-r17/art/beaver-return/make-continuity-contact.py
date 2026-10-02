from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
import json,hashlib
shared=Path('/Volumes/TB4/mac-mini-storage/shared');r17=shared/'pinpin-bath-magic-20261002-r17';lane=r17/'art/beaver-return'
selection=json.loads((lane/'selection.json').read_text())['selected']
ids=['32a','32b','32b1','32b2','32c','32c1','32c2','32c3','32d','32e','32f','32g','32h','32h1','32h2','32h3','32i','32i1','32i2','32i3','32i4','32i5','32i6','32i7','32j']
thumbw,thumbh,label=400,267,30;canvas=Image.new('RGB',(2000,5*(thumbh+label)),(247,240,226));draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20)
rows=[]
for n,id in enumerate(ids):
 key='scene-'+id
 if key in selection:src=Path(selection[key]['master']);status=selection[key]['reviewStatus']
 elif id=='32b':src=shared/'pinpin-bath-magic-20261002-r16-travel-direction/geometry/masters/scene-32b-v1.png';status='retained approved'
 elif id in ['32i5','32i6','32i7']:
  selected={a["id"]:a for a in json.loads((r17/"art/homeward-finish/selected-assets.json").read_text())["assets"]};src=Path(selected[key]["master"]);status="root visual PASS"
 else:src=shared/'pinpin-bath-magic-20261002-r15-beaver-aqueduct/geometry/masters'/(key+'-v1.png');status='retained approved'
 x=(n%5)*thumbw;y=(n//5)*(thumbh+label)
 if src and src.exists():
  im=Image.open(src).convert('RGB');canvas.paste(ImageOps.contain(im,(thumbw,thumbh)),(x,y));sha=hashlib.sha256(src.read_bytes()).hexdigest()
 else:sha=None
 draw.text((x+8,y+thumbh+3),id+'  '+('retained' if status.startswith('retained') else 'R17'),font=font,fill=(40,35,30))
 rows.append({'id':key,'source':str(src),'sha256':sha,'reviewStatus':status})
canvas.save(lane/'continuity-32a-through-32j.jpg',quality=93)
(lane/'continuity-sources.json').write_text(json.dumps(rows,indent=2))
print('contact',len(rows),'missing',sum(x['sha256'] is None for x in rows))
