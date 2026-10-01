#!/usr/bin/env python3
"""Map every recorded generation input to preserved exact bytes, copying missing inputs only."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--source-pack',type=Path,default=Path(__file__).resolve().parent)
parser.add_argument('--mini-pack',type=Path,default=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r3'))
parser.add_argument('--on-mini',action='store_true')
parser.add_argument('--generated-root',type=Path)
args=parser.parse_args()
source=args.source_pack.resolve()
pack=args.mini_pack
code="""import hashlib,json;from pathlib import Path
root=Path(%r);files={}
for folder in ['masters','references','preproduction','geometry','web']:
 for p in (root/folder).rglob('*'):
  if p.is_file() and p.suffix.lower() in {'.png','.webp','.jpg','.jpeg','.blend'}:
   files.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(),[]).append(p.relative_to(root).as_posix())
print(json.dumps(files))
""" % str(pack)
if args.on_mini:
    index={}
    for folder in ['masters','references','preproduction','geometry','web']:
        for path in (pack/folder).rglob('*'):
            if path.is_file() and path.suffix.lower() in {'.png','.webp','.jpg','.jpeg','.blend'}:
                index.setdefault(hashlib.sha256(path.read_bytes()).hexdigest(),[]).append(path.relative_to(pack).as_posix())
else:
    index=json.loads(subprocess.check_output(['ssh','mini',shlex.join(['/opt/homebrew/bin/python3','-c',code])],text=True))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def physical(path):
    marker='/.codex/generated_images/'
    return args.generated_root/str(path).split(marker,1)[1] if args.generated_root and marker in str(path) else Path(path)
def preserve(path,sha):
    if sha in index:return index[sha]
    path=physical(path)
    assert path.is_file(),f'Missing unpreserved input: {path}'
    assert digest(path)==sha,f'Input identity changed: {path}'
    target=pack/'references'/f'{sha[:12]}-{path.name}'
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target)
    assert digest(target)==sha
    index[sha]=[target.relative_to(pack).as_posix()]
    return index[sha]
records=[]
for directory in ['records','generation-records']:
    for path in sorted((source/directory).glob('*.json')):
        if path.stem.endswith('-request'):continue
        record=json.loads(path.read_text())
        references={}
        for item in record.get('referenceIdentities',[]):references[item['path']]=item['sha256']
        references.update(record.get('inputHashes',{}))
        for item in record.get('references',[]):
            if isinstance(item,dict) and item.get('sha256'):references[item['path']]=item['sha256']
            elif isinstance(item,str) and item not in references:references[item]=digest(physical(item))
        assert references,f'No input identities: {path}'
        inputs=[{'originalPath':p,'sha256':sha,'preservedPaths':preserve(Path(p),sha)} for p,sha in references.items()]
        prompt_relative=record.get('promptPath',f'prompts/{path.stem}.txt')
        if Path(prompt_relative).is_absolute():prompt_relative='prompts/'+Path(prompt_relative).name
        prompt=source/prompt_relative
        assert prompt.is_file(),f'Missing prompt file: {prompt}'
        prompt_sha=digest(prompt)
        inline_sha=hashlib.sha256(record['prompt'].encode()).hexdigest() if record.get('prompt') else None
        if record.get('promptSha256'):assert record['promptSha256'] in {prompt_sha,inline_sha},f'Prompt identity mismatch: {path}'
        master=Path(record['savedOriginalPath']) if record.get('savedOriginalPath') else pack/'masters'/f'{path.stem}.png'
        assert pack in master.parents,f'Output outside R3 pack: {master}'
        assert master.is_file(),f'Missing generation original: {master}'
        master_sha=digest(master)
        original=record.get('sourceOutput') or record.get('sourceOutputPath') or record.get('generatedFile')
        original_checked=bool(original and physical(original).is_file())
        if original_checked:assert digest(physical(original))==master_sha,f'Original/master mismatch: {path}'
        expected=record.get('imageSha256') or record.get('master',{}).get('sha256')
        if expected:assert expected==master_sha,f'Output identity mismatch: {path}'
        relative_record=path.relative_to(source)
        (pack/relative_record).parent.mkdir(parents=True,exist_ok=True)
        if path.resolve()!=(pack/relative_record).resolve():shutil.copy2(path,pack/relative_record)
        (pack/prompt_relative).parent.mkdir(parents=True,exist_ok=True)
        if prompt.resolve()!=(pack/prompt_relative).resolve():shutil.copy2(prompt,pack/prompt_relative)
        records.append({'record':relative_record.as_posix(),'recordSha256':digest(path),
                        'prompt':prompt_relative,'promptFileSha256':prompt_sha,'inlinePromptSha256':inline_sha,
                        'inputs':inputs,'output':{'path':master.relative_to(pack).as_posix(),'sha256':master_sha,'originalCompared':original_checked}})
result={'version':1,'status':'input and output bytes preserved locally; consult archive receipt for remote proof',
        'generations':records,'uniqueInputHashes':len({i['sha256'] for r in records for i in r['inputs']})}
(source/'input-preservation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if source.resolve()!=pack.resolve():shutil.copy2(source/'input-preservation.json',pack/'input-preservation.json')
print(json.dumps({'generations':len(records),'uniqueInputs':result['uniqueInputHashes'],'allMappedToPreservedBytes':True}))
