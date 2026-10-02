from pathlib import Path
import hashlib,json,time,shutil
from huggingface_hub import HfApi
p=Path("/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-pdf-release-20261002");source=Path("/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-release-20261002-source")
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
recipe=p/'recipe';recipe.mkdir(exist_ok=True)
shutil.copy2(source/'scripts/export-story-pdf.py',recipe/'export-story-pdf.py')
shutil.copy2(source/'docs/storyboard/stories/bath-magic.json',recipe/'bath-magic.json')
(recipe/'requirements.txt').write_text('pillow==12.3.0\nreportlab==5.0.1\npymupdf==1.28.2\nhuggingface_hub==2.1.1\n')
selected=[]
for folder in ['masters','prompts','records','references','web','recipe']:
 selected.extend(f for f in (p/folder).rglob('*') if f.is_file())
selected.extend((p/'exports').glob('*.pdf'));selected.append(p/'exports/export-manifest.json');selected.append(p/'screenshots/ru-proof-contact.jpg')
entries=[]
for f in selected:
 digest=sha(f);obj=f'sha256/{digest[:2]}/{digest}/{f.name}'
 entries.append({'path':'docs/storyboard/production/bath-magic-pdf-release-20261002/'+f.relative_to(p).as_posix(),'local':str(f),'role':'archive','bytes':f.stat().st_size,'sha256':digest,'object':obj})
bucket='miguelemosreverte/mr-pinpin-archive';api=HfApi()
unique={e['object']:e for e in entries}
(p/'archive-manifest.json').write_text(json.dumps({'version':1,'bucket':bucket,'assets':entries},indent=2)+'\n')
api.batch_bucket_files(bucket,add=[(Path(e['local']),obj) for obj,e in unique.items()])
print('Uploaded',len(unique),'objects',flush=True)
rows=list(api.get_bucket_paths_info(bucket,list(unique)))
assert len(rows)==len(unique)
dest=p/'archive-readback'/str(time.time_ns());dest.mkdir(parents=True)
pairs=[]
for row in rows:
 e=unique[row.path];assert row.size==e['bytes'] and row.xet_hash
 f=dest/row.path;f.parent.mkdir(parents=True,exist_ok=True);pairs.append((row,f))
api.download_bucket_files(bucket,pairs,raise_on_missing_files=True)
verified=[]
for row,f in pairs:
 e=unique[row.path];assert f.stat().st_size==e['bytes'] and sha(f)==e['sha256']
 verified.append({**e,'verified':True,'remote_verified':True,'remote_xet_hash':row.xet_hash})
(p/'archive-receipt.json').write_text(json.dumps({'version':1,'bucket':bucket,'verified':True,'freshReadback':str(dest),'entries':verified},indent=2)+'\n')
print('FRESH SHA256 VERIFIED',len(verified),sum(e['bytes']for e in verified),flush=True)
