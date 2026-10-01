#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--origins',action='store_true');args=p.parse_args()
root=Path(__file__).resolve().parent
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
items=json.loads((root/'reuse.json').read_text())['items']
for row in items:
 for key in ['master','web','originRecord','originPrompt']:
  entry=row[key];file=root/entry['path'];assert sha(file)==entry['sha256'] and file.stat().st_size==entry['bytes'],(row['id'],key)
 assert row['master']['sha256']==row['originMaster']['sha256'] and row['web']['sha256']==row['originWeb']['sha256']
 for item in row['inputs']:assert all(sha(root/file)==item['sha256'] for file in item['preservedPaths'])
 if args.origins:
  origin=Path(row['sourceRoot'])
  for key in ['originMaster','originWeb']:assert sha(origin/row[key]['path'])==row[key]['sha256'],(row['id'],key)
print(json.dumps({'reusedAssets':len(items),'allCopiesBitIdentical':True,'allOriginInputsPreserved':True,'originFilesChecked':args.origins}))
