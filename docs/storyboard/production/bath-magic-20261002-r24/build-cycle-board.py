#!/usr/bin/env python3
"""Build real comedy-cycle boards. Shared cuts are contextual repeats, not extra story scenes."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,math
p=Path(__file__).resolve().parent
plan=json.loads((p/'story-plan.json').read_text());media=json.loads((p/'media.json').read_text());before=json.loads((p/'baseline/story-plan.json').read_text());bm=json.loads((p/'baseline/media.json').read_text())
a=json.loads((p/'preproduction/willow-gag/plan.json').read_text());tempo=json.loads((p/'plan/tempo-comparison.json').read_text())
rows={x['id']:x for x in plan['scenes']};oldRows={x['id']:x for x in before['scenes']};ids=a['gagOrder'];ready=[s for s in ids if s not in media.get('pendingIds',[])and s in media['images']]
out=p/'cycle-board';out.mkdir(exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',25);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
def render(name,which,lang,cols,kind,baseline=False,group=None):
 rmap=oldRows if baseline else rows;mm=bm if baseline else media
 cw,ch,gap=500,620,20
 im=Image.new('RGB',(cols*cw+(cols+1)*gap,math.ceil(len(which)/cols)*ch+40),'#fff9ed');draw=ImageDraw.Draw(im);proof=[]
 for i,sid in enumerate(which):
  row=rmap[sid];e=mm['images'][sid];src=p.parent/('pinpin-'+e['sourceProduction'])/e['path'];assert hashlib.sha256(src.read_bytes()).hexdigest()==e['sha256']
  x=gap+(i%cols)*(cw+gap);y=20+(i//cols)*ch;label=f"{'R23' if baseline else 'R24'} {row['number']} · {sid}"
  draw.text((x,y),label,font=small,fill='#5b4932');pic=Image.open(src).convert('RGB');pic.thumbnail((cw,334));im.paste(pic,(x,y+34))
  lines=[];line=''
  for word in ' '.join(row['paragraphs'][lang]).split():
   test=(line+' '+word).strip()
   if line and draw.textlength(test,font=font)>cw:lines.append(line);line=word
   else:line=test
  if line:lines.append(line)
  draw.multiline_text((x,y+383),'\n'.join(lines),font=font,fill='#28221a',spacing=6)
  proof.append({'id':sid,'number':row['number'],'sha256':e['sha256'],'sourceProduction':e['sourceProduction'],'path':e['path']})
 dst=out/(name+'-'+lang+'.webp');im.save(dst,'WEBP',quality=89)
 return {'kind':kind,'group':group,'baseline':baseline,'lang':lang,'path':dst.name,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'width':im.width,'height':im.height,'panels':proof}
sheets=[]
for lang in ['ru','en','es']:
 for i,group in enumerate(a['cycleGroups']):
  if all(s in ready for s in group):
   sheets.append(render(f'cycle-{i+1}',group,lang,min(len(group),6),'cycle'if i<3 else'anticipation',group=i+1))
   if i<3:sheets.append(render(f'previous-cycle-{i+1}',tempo['baseline']['cycles'][i],lang,3,'previous-cycle',True,i+1))
 if 'scene-354'in ready:sheets.append(render('seat',['scene-354'],lang,1,'setup'))
 climax=['scene-'+str(n)for n in range(348,354)]
 if all(s in ready for s in climax):sheets.append(render('climax',climax,lang,6,'climax'))
 if len(ready)==25:
  sheets.append(render('gag-overview',ids,lang,5,'full-gag'))
  sheets.append(render('gag-transitions',['scene-329','scene-330']+ids+['scene-332','scene-333'],lang,6,'transitions'))
manifest={'schemaVersion':1,'status':'complete proposed sequence'if len(ready)==25 else'work in progress; only finished groups shown','selectedFrames':len(ready),'totalFrames':25,'fullChapterScenes':len(plan['scenes']),'sharedCutContextIds':['scene-341','scene-343','scene-345'],'sheets':sheets,'tempo':tempo}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'readyGag':len(ready),'sheets':len(sheets),'chapter':len(plan['scenes'])}))
