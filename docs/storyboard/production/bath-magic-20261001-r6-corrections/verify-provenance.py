#!/usr/bin/env python3
"""Verify exact model outputs, prompts and archived reference inputs without rewriting lane records."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
generated=root.parent/'air-space-recovery/codex-generated-images-elder-r6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def locate(lane,value):
 p=Path(value)
 return p if p.is_absolute() else root/lane/p
def physical(value):
 p=Path(value)
 if '/.codex/generated_images/' in str(p):return generated/str(p).split('/.codex/generated_images/',1)[1]
 return p
index={}
for lane in ['tables','beds','geometry','references']:
 for path in (root/lane).rglob('*'):
  if path.is_file() and path.suffix.lower() in {'.png','.webp','.jpg','.jpeg'}:
   index.setdefault(sha(path),[]).append(path.relative_to(root).as_posix())
rows=[];inputs=set()
for lane in ['tables','beds','geometry']:
 for path in sorted((root/lane).rglob('*.json')):
  record=json.loads(path.read_text())
  if not isinstance(record,dict) or 'tool' not in record or 'sourceOutput' not in record or 'master' not in record:continue
  master=record['master'];master_path=locate(lane,master['path'] if isinstance(master,dict) else master)
  digest=sha(master_path)
  expected=master.get('sha256') if isinstance(master,dict) else record.get('sha256')
  if expected:assert digest==expected,path
  output=physical(record.get('sourceOutputPhysical',record['sourceOutput']))
  assert output.is_file(),output
  assert sha(output)==digest,('original tool output mismatch',path)
  prompt=locate(lane,record['promptPath']);prompt_hash=sha(prompt)
  if record.get('promptSha256'):assert prompt_hash==record['promptSha256'],path
  preserved=[]
  supplied={x['path']:x for x in record.get('inputs',[])}
  for ref in record.get('references',[]):
   value=ref if isinstance(ref,str) else ref['path']
   info=supplied.get(value,{}) if isinstance(ref,str) else ref
   reference_hash=info.get('sha256')
   if not reference_hash:reference_hash=sha(locate(lane,value))
   assert reference_hash in index,('Unpreserved exact reference',path,value)
   inputs.add(reference_hash);preserved.append({'originalPath':value,'sha256':reference_hash,'preservedPaths':index[reference_hash]})
  rows.append({'record':path.relative_to(root).as_posix(),'recordSha256':sha(path),'tool':record['tool'],'master':master_path.relative_to(root).as_posix(),'masterSha256':digest,'nativeToolOutputMatched':True,'prompt':prompt.relative_to(root).as_posix(),'promptSha256':prompt_hash,'inputs':preserved})
assert rows,'No generation records found'
data={'status':'Exact originals, prompts and input bytes verified locally; remote proof in scoped archive receipt','generations':rows,'uniqueInputHashes':sorted(inputs)}
(root/'references/provenance-audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'generations':len(rows),'uniqueInputs':len(inputs),'allOutputsAndInputsVerified':True}))
