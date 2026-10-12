"""User-requested reference-led revision; retain the superseded edition verbatim."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent;root=p.parents[3];previous=json.loads((p/'superseded-edition-v3.json').read_text());s=json.loads(json.dumps(previous));new=[]
for r in json.loads((p/'narration.json').read_text()):
 new.append({'id':r['id'],'image':f"images/published/scooby-bath/revision-v4/{r['id']}.webp",'width':1536,'height':1024,'alt':r['text'],'paragraphs':{k:[v] for k,v in r['text'].items()}})
old={r['id']:r for r in previous['scenes']};welcome=json.loads(json.dumps(old['scene-15']));welcome['image']='images/published/scooby-bath/revision-v4/scene-15.webp'
s['editionVersion']=4;s['scenes']=[old['scooby-bath-title'],*new,*[old[f'scene-{i:02}'] for i in range(1,15)],welcome,old['ext-08'],old['ext-09'],old['scene-16']];s['spreads']=[{'scenes':[i],'style':'cover' if i==0 else 'elder','paper':'portrait' if i==0 else 'landscape'} for i in range(len(s['scenes']))];assert len(s['scenes'])==33
(root/'docs/storyboard/stories/scooby-bath.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
