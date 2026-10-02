#!/usr/bin/env python3
"""Rolling five-frame contact sheets and final20/24-frame continuity boards."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,math
p=Path(__file__).resolve().parent
plan=json.loads((p/'story-plan.json').read_text());media=json.loads((p/'media.json').read_text())
rows={r['id']:r for r in plan['scenes']};ids=[f'scene-{n}'for n in range(320,340)]
ready=[sid for sid in ids if sid not in media.get('pendingIds',[])and sid in media['images']]
out=p/'dam-board';out.mkdir(exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',25)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
def path(entry):
 return p.parent/('pinpin-'+entry['sourceProduction'])/entry['path']
def render(name,which,lang,cols,kind):
 cw,ch,gap,margin=500,620,20,20;image=Image.new('RGB',(cols*cw+(cols+1)*gap,math.ceil(len(which)/cols)*ch+2*margin),'#fff9ed');draw=ImageDraw.Draw(image);proof=[]
 for i,sid in enumerate(which):
  row=rows[sid];entry=media['images'][sid];source=path(entry);raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['sha256']
  x=gap+(i%cols)*(cw+gap);y=margin+(i//cols)*ch
  status='NEW'if sid in ids else'RETAINED';label=f"{row['number']} · {sid} · {status}"
  draw.text((x,y),label,font=small,fill='#5b4932')
  picture=Image.open(source).convert('RGB');picture.thumbnail((cw,334));image.paste(picture,(x,y+34))
  line='';lines=[]
  for word in ' '.join(row['paragraphs'][lang]).split():
   test=(line+' '+word).strip()
   if line and draw.textlength(test,font=font)>cw:lines.append(line);line=word
   else:line=test
  if line:lines.append(line)
  draw.multiline_text((x,y+383),'\n'.join(lines),font=font,fill='#28221a',spacing=6)
  proof.append({'id':sid,'number':row['number'],'sha256':entry['sha256'],'sourceProduction':entry['sourceProduction'],'path':entry['path']})
 dest=out/(name+'-'+lang+'.webp');image.save(dest,'WEBP',quality=89)
 return {'kind':kind,'lang':lang,'path':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'width':image.width,'height':image.height,'panels':proof}
sheets=[]
for lang in ['ru','en','es']:
 for i in range(4):
  chunk=ids[i*5:(i+1)*5]
  if all(s in ready for s in chunk):sheets.append(render(f'dam-group-{i+1:02}',chunk,lang,5,'five-frame'))
 if len(ready)==20:
  sheets.append(render('dam-overview',ids,lang,5,'twenty-frame'))
  sheets.append(render('dam-transitions',['scene-32b','scene-32b1']+ids+['scene-32d','scene-32e'],lang,6,'transitions'))
manifest={'schemaVersion':1,'status':'complete proposed sequence'if len(ready)==20 else'work in progress; unrendered frames are not presented as finished','selectedFrames':len(ready),'totalFrames':20,'fullChapterScenes':191,'sheets':sheets}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'selected':len(ready),'sheets':len(sheets),'fullChapterScenes':191}))
