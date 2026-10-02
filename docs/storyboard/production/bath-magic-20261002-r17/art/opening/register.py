import argparse,json,hashlib,datetime
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--id',required=True);p.add_argument('--version',default='v1');p.add_argument('--original',default='');p.add_argument('--refs',nargs='*',default=[]);p.add_argument('--note',required=True);a=p.parse_args()
root=Path(__file__).resolve().parent;stem=a.id+'-'+a.version;master=root/'masters'/(stem+'.png');assert master.exists();prompt=root/'prompts'/(stem+'.txt');assert prompt.exists()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
(root/'web').mkdir(exist_ok=True);web=root/'web'/(stem+'.webp')
im=Image.open(master);im.convert('RGB').save(web,'WEBP',quality=93,method=6)
refs=[]
for path in a.refs:
 f=Path(path);assert f.exists();refs.append({'path':str(f),'sha256':sha(f)})
record={'id':a.id,'version':a.version,'tool':'image_gen__imagegen','master':str(master),'masterSha256':sha(master),'masterBytes':master.stat().st_size,'dimensions':list(im.size),'originalToolOutput':a.original,'prompt':str(prompt),'promptSha256':sha(prompt),'references':refs,'web':str(web),'webSha256':sha(web),'reviewStatus':'agent visual pass; root review pending','visualReview':a.note,'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(root/'records'/(stem+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2))
mf=root/'selection.json';d=json.loads(mf.read_text()) if mf.exists() else {'schemaVersion':1,'selected':{}};d['selected'][a.id]=record;mf.write_text(json.dumps(d,ensure_ascii=False,indent=2))
print(a.id,im.size,sha(master))
