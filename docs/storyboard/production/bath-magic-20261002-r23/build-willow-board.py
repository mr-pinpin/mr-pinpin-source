#!/usr/bin/env python3
"""Willow gag: three five-frame strips and final15/19-frame continuity boards."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,math
p=Path(__file__).resolve().parent
plan=json.loads((p/'story-plan.json').read_text());media=json.loads((p/'media.json').read_text())
rows={r['id']:r for r in plan['scenes']};ids=['scene-331']+[f'scene-{n}'for n in range(340,354)]
ready=[sid for sid in ids if sid not in media.get('pendingIds',[])and sid in media['images']]
out=p/'willow-board';out.mkdir(exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',25)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
def path(entry):
 return p.parent/('pinpin-'+entry['sourceProduction'])/entry['path']
def render(name,which,lang,cols,kind):
 cw,ch,gap,margin=500,620,20,20;image=Image.new('RGB',(cols*cw+(cols+1)*gap,math.ceil(len(which)/cols)*ch+2*margin),'#fff9ed');draw=ImageDraw.Draw(image);proof=[]
 for i,sid in enumerate(which):
  row=rows[sid];entry=media['images'][sid];source=path(entry);raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['sha256']
  x=gap+(i%cols)*(cw+gap);y=margin+(i//cols)*ch
  status='SETUP'if sid=='scene-331'else'NEW'if sid in ids else'CONTEXT';label=f"{row['number']} · {sid} · {status}"
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
 for i in range(3):
  chunk=ids[i*5:(i+1)*5]
  if all(s in ready for s in chunk):sheets.append(render(f'willow-group-{i+1:02}',chunk,lang,5,'five-frame'))
 if len(ready)==15:
  sheets.append(render('willow-overview',ids,lang,5,'fifteen-frame'))
  sheets.append(render('willow-transitions',['scene-329','scene-330']+ids+['scene-332','scene-333'],lang,5,'transitions'))
manifest={'schemaVersion':1,'status':'complete proposed sequence'if len(ready)==15 else'work in progress; unrendered frames are not presented as finished','selectedFrames':len(ready),'totalFrames':15,'fullChapterScenes':205,'sheets':sheets}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'selected':len(ready),'sheets':len(sheets),'fullChapterScenes':205}))
