#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
p=Path(__file__).resolve().parent
data=json.loads((p/'art/return-walk/selection.json').read_text())['selected']
rows=json.loads((p/'plan/return-home-inserts.json').read_text())['rows']
out=p/'walk-board';out.mkdir(exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',27)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24)
manifest=[]
for lang in ['ru','en','es']:
 im=Image.new('RGB',(2640,670),'#fffaf0');draw=ImageDraw.Draw(im)
 for i,row in enumerate(rows):
  x=20+i*524
  entry=data[row['id']];img=Image.open(entry.get('web',entry.get('master'))).convert('RGB');img.thumbnail((500,334))
  im.paste(img,(x,58));draw.text((x,17),str(i+1)+' · '+row['id'],font=small,fill='#4b392a')
  text=' '.join(row['captions'][lang]);lines=[];line=''
  for word in text.split():
   test=(line+' '+word).strip()
   if draw.textlength(test,font=font)>498 and line:lines.append(line);line=word
   else:line=test
  if line:lines.append(line)
  draw.multiline_text((x,411),'\n'.join(lines),font=font,fill='#29231c',spacing=8)
 dest=out/('return-home-'+lang+'.webp');im.save(dest,'WEBP',quality=90)
 manifest.append({'lang':lang,'path':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'panels':[r['id']for r in rows]})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'boards':len(manifest),'panels':5,'dimensions':[2640,670]}))
