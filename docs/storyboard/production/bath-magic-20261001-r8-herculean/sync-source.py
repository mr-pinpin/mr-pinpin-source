#!/usr/bin/env python3
"""Copy authoritative small R8 files into the mini source checkout."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parent
repo=Path("/Volumes/TB4/mac-mini-storage/shared/pinpin-workspace/mr-pinpin-source")
dest=repo/"docs/storyboard/production/bath-magic-20261001-r8-herculean"
allowed={".py",".cjs",".md",".json",".txt"}
folders={"root","story","geometry","reused","preproduction","references","browser-check"}
excluded={"archive-manifest.json","archive-receipt.json"}
copied=[]
for path in sorted(root.rglob("*")):
    rel=path.relative_to(root)
    if not path.is_file() or path.suffix not in allowed:continue
    if len(rel.parts)>1 and rel.parts[0] not in folders:continue
    if path.name in excluded:continue
    target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    assert hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256(path.read_bytes()).digest()
    copied.append(rel.as_posix())
for src,name in [("archive-manifest.json","bath-magic-20261001-r8-herculean.json"),("archive-receipt.json","bath-magic-20261001-r8-herculean-receipt.json")]:
    if (root/src).exists():shutil.copy2(root/src,repo/"assets"/name)
print(json.dumps({"sourceTextFiles":len(copied),"allByteIdentical":True,"files":copied}))
