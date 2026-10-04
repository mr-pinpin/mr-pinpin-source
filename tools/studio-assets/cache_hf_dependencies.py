"""Copy exact installed HF SDK dependency closure; no install/download/credentials."""
from pathlib import Path
import importlib.metadata as metadata
from packaging.requirements import Requirement
from packaging.markers import default_environment
import argparse,hashlib,json,shutil,time
parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=Path,required=True);args=parser.parse_args();base=args.candidate;target=base/'dependencies-hf';plan=base/'runtime';queue=['huggingface-hub'];seen=set();files={};versions={};environment=default_environment();environment['extra']=''
while queue:
 name=queue.pop().lower().replace('_','-')
 if name in seen:continue
 seen.add(name);d=metadata.distribution(name);versions[d.metadata['Name']]=d.version
 for spec in d.requires or []:
  r=Requirement(spec)
  if r.marker is None or r.marker.evaluate(environment):queue.append(r.name)
 for rel in d.files or []:
  parts=Path(rel).parts
  if not parts or '..' in parts or Path(rel).is_absolute() or '__pycache__' in parts or str(rel).endswith('.pyc'):continue
  src=Path(d.locate_file(rel));assert not src.is_symlink();assert src.is_file(),str(src);files[str(rel)]=src
size=sum(p.stat().st_size for p in files.values());assert size<=33554432 and len(files)<=2500,(size,len(files));rows=[]
for rel,src in files.items():
 dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True);b=src.read_bytes();digest=hashlib.sha256(b).hexdigest()
 if dst.exists():assert hashlib.sha256(dst.read_bytes()).hexdigest()==digest
 else:dst.write_bytes(b)
 rows.append({'path':str(dst),'sourcePath':str(src),'bytes':len(b),'sha256':digest})
proof={'epoch':time.time(),'root':str(target),'bytes':size,'fileCount':len(rows),'versions':versions,'files':rows,'scope':'exact installed required SDK dependency packages/metadata; no credentials, site startup, package installation or network'};(plan/'hf-dependency-cache-receipt.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='files'}))
