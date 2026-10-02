from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
b=Path(__file__).parent
rows=['03g','05f','05g1','05g2'];canvas=Image.new('RGB',(1300,4*465),(244,239,226));d=ImageDraw.Draw(canvas)
for i,s in enumerate(rows):
 req=json.loads((b/'records'/f'scene-{s}-request-v1.json').read_text());before=Path(req['refs'][0]);v={'05g1':'v2','05g2':'v3'}.get(s,'v1');after=b/'masters'/f'scene-{s}-{v}.png'
 for col,p in enumerate([before,after]):
  im=Image.open(p).convert('RGB');im.thumbnail((630,420));x=10+650*col;y=i*465+35;canvas.paste(im,(x,y));d.text((x,i*465+10),f'scene-{s}: '+('BEFORE R17' if col==0 else 'AFTER R18 '+v),fill=(40,40,30))
canvas.save(b/'before-after-opening.jpg',quality=90)
canvas=Image.new('RGB',(1300,485),(244,239,226));d=ImageDraw.Draw(canvas)
for i,s in enumerate(['05f1','05f2']):
 im=Image.open(b/'masters'/f'scene-{s}-v1.png');im.thumbnail((630,420));canvas.paste(im,(10+i*650,40));d.text((10+i*650,12),'NEW scene-'+s,fill=(40,40,30))
canvas.save(b/'rabbit-closure.jpg',quality=92)
print('before-after-opening.jpg and rabbit-closure.jpg')
