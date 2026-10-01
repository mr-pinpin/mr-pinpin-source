#!/usr/bin/env python3
"""Copy selected R2 artwork unchanged into R3, preserving upstream provenance."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--pack',type=Path,default=Path(__file__).resolve().parent)
parser.add_argument('--source-pack',type=Path,default=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r2'))
args=parser.parse_args();root=args.pack.resolve();origin=args.source_pack.resolve()
plan=json.loads((root/'story-plan.json').read_text())
selected={x['id']:x for x in json.loads((origin/'selected-scenes.json').read_text())['scenes']}
ledger={x['record']:x for x in json.loads((origin/'input-preservation.json').read_text())['generations']}
upstream={x['id']:x for x in json.loads((origin/'reuse.json').read_text())['items']}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def identity(path):return {'path':path.relative_to(root).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)}
def copy(source,target,expected):
    assert sha(source)==expected,str(source)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert sha(target)==expected,f'Existing reuse identity conflict: {target}'
    else:shutil.copy2(source,target)
    assert sha(target)==expected,str(target)
with (root/'.accept.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    derivatives_path=root/'derivatives.json'
    derivatives=json.loads(derivatives_path.read_text()) if derivatives_path.exists() else {'version':1,'assets':{}}
    reuse=[]
    for scene in [plan['cover'],*plan['scenes']]:
        source_id=scene.get('reusedFrom')
        if not source_id:continue
        old=selected[source_id];slug='title' if scene['id']=='cover' else scene['id']
        master=root/'masters'/'reused'/slug/Path(old['master']['path']).name
        web=root/'web'/f'{slug}.webp'
        copy(origin/old['master']['path'],master,old['master']['sha256'])
        copy(origin/old['web']['path'],web,old['web']['sha256'])
        prior=upstream.get(source_id) if old.get('reuseRecord') else None
        if prior:
            source_record=origin/prior['originRecord']['path']
            prompt_source=origin/prior['originPrompt']['path']
            prompt_hash=prior['originPrompt']['sha256']
            input_items=prior['inputs']
        else:
            source_record=origin/old['generationRecord']
            record_key=source_record.relative_to(origin).as_posix()
            inputs=ledger[record_key]
            prompt_source=origin/inputs['prompt']
            prompt_hash=inputs['promptFileSha256']
            input_items=inputs['inputs']
        record_copy=root/'reuse-records'/slug/'origin-record.json'
        copy(source_record,record_copy,sha(source_record))
        prompt_copy=root/'reuse-records'/slug/'origin-prompt.txt'
        copy(prompt_source,prompt_copy,prompt_hash)
        preserved_inputs=[]
        for item in input_items:
            original=origin/item['preservedPaths'][0]
            target=root/'references'/'reused'/item['sha256'][:12]/original.name
            copy(original,target,item['sha256'])
            preserved_inputs.append({'originalPath':item['originalPath'],'sha256':item['sha256'],'preservedPaths':[target.relative_to(root).as_posix()]})
        entry={'id':scene['id'],'operation':'reuse unchanged; not newly generated','sourceProduction':'bath-magic-20261001-r2',
               'sourceId':source_id,'originMaster':old['master'],'originWeb':old['web'],
               'master':identity(master),'web':identity(web),'originRecord':identity(record_copy),'originPrompt':identity(prompt_copy),
               'inputs':preserved_inputs,'width':old['width'],'height':old['height']}
        if prior:
            entry['upstreamOrigin']={'sourceProduction':prior['sourceProduction'],'sourceId':prior['sourceId'],
                'originMaster':prior['originMaster'],'originWeb':prior['originWeb'],
                'reuseRecord':old['reuseRecord']}
        reuse.append(entry)
        derivatives['assets'][slug]={'slug':slug,'master':entry['master'],'web':entry['web'],'width':old['width'],'height':old['height'],
            'recipe':{'operation':'byte-for-byte copy','resized':False,'reencoded':False,'artEdited':False},
            'reuseRecord':f'reuse.json#{scene["id"]}','generationRecord':None,'approval':'draft-for-review'}
    derivatives_path.write_text(json.dumps(derivatives,ensure_ascii=False,indent=2)+'\n')
    (root/'reuse.json').write_text(json.dumps({'version':1,'sourceProduction':'bath-magic-20261001-r2','items':reuse},ensure_ascii=False,indent=2)+'\n')
    subprocess.run([sys.executable,str(root/'refresh-media.py')],check=True)
print(json.dumps({'reused':len(reuse),'artReencoded':False,'r2Changed':False}))
