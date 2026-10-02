#!/usr/bin/env python3
"""Verify the entire scoped archive with batched metadata and fresh downloads."""
from pathlib import Path
import hashlib,json,time
from huggingface_hub import HfApi
root=Path(__file__).resolve().parent
manifest=json.loads((root/'archive-manifest.json').read_text())
bucket=manifest['bucket'];entries=manifest['assets'];api=HfApi()
unique={e['object']:e for e in entries}
def metadata():
    result={}
    paths=list(unique)
    for start in range(0,len(paths),100):
        for item in api.get_bucket_paths_info(bucket,paths[start:start+100]):
            assert item.path not in result
            result[item.path]=item
    assert set(result)==set(unique),'Missing remote objects'
    for path,item in result.items():
        assert item.type=='file' and item.xet_hash
        assert item.size==unique[path]['bytes']
    return result
print('Batched metadata before readback',flush=True)
before=metadata()
dest=root/'archive-readback'/str(time.time_ns());dest.mkdir(parents=True)
pairs=[]
for path,item in before.items():
    target=dest/path;target.parent.mkdir(parents=True,exist_ok=True)
    pairs.append((item,target))
print(f'Fresh remote readback: {len(pairs)} unique objects',flush=True)
api.download_bucket_files(bucket,pairs,raise_on_missing_files=True)
for i,(path,entry) in enumerate(unique.items(),1):
    target=dest/path
    assert target.stat().st_size==entry['bytes'],path
    assert hashlib.sha256(target.read_bytes()).hexdigest()==entry['sha256'],path
    if i%100==0:print(f'Byte-verified {i}/{len(unique)} unique objects',flush=True)
print('Batched metadata after readback',flush=True)
after=metadata()
for path in unique:
    assert before[path].xet_hash==after[path].xet_hash,'Remote object changed during verification'
rows=[{**e,'status':'remote-byte-verified-batched','verified':True,'remote_verified':True,
       'remote_xet_hash':after[e['object']].xet_hash} for e in entries]
receipt={'version':1,'action':'verify','bucket':bucket,'dry_run':False,'verified':True,'entries':rows}
temp=root/'.archive-receipt.json.tmp';temp.write_text(json.dumps(receipt,indent=2)+'\n');temp.replace(root/'archive-receipt.json')
print(json.dumps({'verified':len(rows),'uniqueRemoteObjects':len(unique),'bytes':sum(x['bytes'] for x in entries),'freshReadback':str(dest)}),flush=True)
