"""Preserve built-in native output and exact prompt/reference provenance."""
import argparse,hashlib,json,shutil
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('id');p.add_argument('source');p.add_argument('prompt');p.add_argument('--reference',action='append',default=[]);p.add_argument('--review',required=True);p.add_argument('--status',default='candidate');a=p.parse_args()
pack=Path(__file__).resolve().parent;root=pack.parents[3];native=pack/'native'/f'{a.id}.png';native.parent.mkdir(exist_ok=True)
assert not native.exists(),f'No overwriting {native}'
shutil.copyfile(a.source,native)
def digest(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
record={'id':a.id,'tool':'built-in image_gen.imagegen','nativePath':str(native.relative_to(root)),'nativeSha256':digest(native),'toolOriginal':a.source,'promptPath':str(Path(a.prompt).resolve().relative_to(root)),'promptSha256':digest(a.prompt),'references':[{'path':s,'sha256':digest(s)} for s in a.reference],'recordedAt':datetime.now(timezone.utc).isoformat(),'status':a.status,'selectedForPublication':False,'review':a.review}
f=pack/'generation-records.json';records=json.loads(f.read_text()) if f.exists() else [];records.append(record);f.write_text(json.dumps(records,indent=2)+'\n');print(a.id,record['nativeSha256'],a.status)
