#!/usr/bin/python3
"""Publish a credential-free client snapshot for authenticated SSH upgrades."""
import base64
import hashlib
import json
import os
import sys
from pathlib import Path
from client_upgrade import FILES

root = Path(__file__).resolve().parent.parent
files = {}
for name in sorted(FILES):
    source = root/'commands'/name if name.endswith('.py') else root/name
    files[name] = base64.b64encode(source.read_bytes()).decode()
version = hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
path = Path(sys.argv[1])
path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
temporary = path.with_name(path.name+'.next')
temporary.write_text(json.dumps({'version':version,'files':files})+'\n')
temporary.chmod(0o600)
os.replace(temporary,path)
print('Published custom client '+version[:12])
