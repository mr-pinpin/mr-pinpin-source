import pathlib,json,hashlib,sys,urllib.request,subprocess
from PIL import Image
base=pathlib.Path(__file__).parent
sid,version=sys.argv[1:3]
j=json.loads((base/'records'/f'{sid}-request-{version}.json').read_text())
master=base/'masters'/f'{sid}-{version}.png'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
refs=[dict(path=p,sha256=sha(p),bytes=pathlib.Path(p).stat().st_size) for p in j['refs']]
prompt=base/'prompts'/f'{sid}-{version}.txt'
web=base/'web'/f'{sid}-{version}.webp'
with Image.open(master) as im: dims=im.size;im.save(web,quality=94,method=6)
r=dict(schemaVersion=1,id=sid,version=version,jobId=j['job'],tool='image_gen__imagegen',master=str(master),masterSha256=sha(master),dimensions=dims,web=str(web),webSha256=sha(web),exactPrompt=j['prompt'],prompt=dict(path=str(prompt),sha256=sha(prompt)),references=refs,toolArguments=dict(prompt=j['prompt'],referenced_image_paths=j['refs'],transparent_background=False),originalToolOutput=j.get('originalToolOutput'),artistReview=j.get('artistReview','pass'),rootReview=j.get('rootReview','pending'),selected=False)
(base/'records'/f'{sid}-{version}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
if '--complete' in sys.argv:
 s=json.load(urllib.request.urlopen('http://127.0.0.1:18806/api/state'));bindings=[]
 for i,ref in enumerate(refs):
  asset=next((a for a in s['assets'] if a['sha256']==ref['sha256']),None)
  if asset is None:
   cmd=[sys.executable,'/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/cli.py','--data-dir','/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-data','--media-root','/Volumes/TB4/mac-mini-storage/shared','import-asset',ref['path']]
   asset=json.loads(subprocess.check_output(cmd))['asset']
  bindings.append(dict(assetId=asset['id'],role=j.get('roles',['edit-target']+['identity-reference']*8)[i]))
 f=base/'records'/f'{sid}-{version}-studio-references.json';f.write_text(json.dumps(bindings,indent=2))
 cmd=[sys.executable,'/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/cli.py','--data-dir','/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-data','--media-root','/Volumes/TB4/mac-mini-storage/shared','complete',j['job'],'--agent','r18-opening','--image',str(master),'--scene-id',sid,'--visual-pass','--tool','image_gen__imagegen','--prompt-file',str(prompt),'--references-file',str(f)]
 out=json.loads(subprocess.check_output(cmd));(base/'records'/f'{sid}-{version}-studio-result.json').write_text(json.dumps(out,indent=2));print(sid,version,out['job']['status'])
else: print(sid,version,'recorded')
