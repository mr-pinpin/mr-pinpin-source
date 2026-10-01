#!/usr/bin/env python3
"""Scoped content-addressed upload with batched metadata; proof requires fresh readback."""
from pathlib import Path
import importlib.util,json,subprocess,sys
from huggingface_hub import HfApi
from huggingface_hub.errors import EntryNotFoundError
p=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('hf_store',p/'archive-tools/hf_store.py');store=importlib.util.module_from_spec(spec);spec.loader.exec_module(store)
manifest=json.loads((p/'archive-manifest.json').read_text())
entries=store.validate_entries(manifest['assets']);bucket=store.validate_bucket(manifest['bucket'])
stage=p/'archive-stage';cache=p.parent/'pinpin-asset-cache'
unique={e['object']:e for e in entries};cached={}
for entry in entries:
 source=store.source_path(stage,entry['path'],allow_symlinks=False);store.check_file(source,entry['bytes'],entry['sha256'])
 dest=store.safe_path(cache,entry['object'],create=True);store._copy_verified(source,dest,entry);cached[entry['object']]=dest
print(f'Validated {len(entries)} source artifacts',flush=True)
api=HfApi();remote={};paths=list(unique)
for start in range(0,len(paths),100):
 try:rows=list(api.get_bucket_paths_info(bucket,paths[start:start+100]))
 except EntryNotFoundError:rows=[]
 for item in rows:
  assert item.path in unique and item.path not in remote
  assert item.type=='file' and item.xet_hash and item.size==unique[item.path]['bytes']
  remote[item.path]=item
missing=[obj for obj in paths if obj not in remote]
for start in range(0,len(missing),64):
 batch=missing[start:start+64]
 api.batch_bucket_files(bucket,add=[(cached[obj],obj)for obj in batch])
 print(f'Uploaded {min(start+64,len(missing))}/{len(missing)} new objects',flush=True)
(p/'archive-upload.json').write_text(json.dumps({'status':'upload only; not verification proof','artifacts':len(entries),'newObjects':len(missing),'existingObjects':len(remote),'bucket':bucket},indent=2)+'\n')
subprocess.run([sys.executable,str(p/'verify-archive-batched.py')],check=True)
