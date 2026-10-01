#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
m=json.loads((p/'archive-manifest.json').read_text());r=json.loads((p/'archive-receipt.json').read_text())
assert m['version']==r['version']==1 and r['verified'] is True and r['dry_run'] is False
assert r['action'] in ['push','verify'] and r['bucket']==m['bucket']
entries={e['path']:e for e in r['entries']};assert len(entries)==len(m['assets'])
prefix='docs/storyboard/production/bath-magic-20261001-r9-final-edit/'
for a in m['assets']:
 e=entries[a['path']]
 assert all(e[k]==a[k] for k in ['path','bytes','sha256','object','role'])
 assert e['verified'] is True and e['remote_verified'] is True
 assert a['path'].startswith(prefix)
 f=p/a['path'][len(prefix):]
 assert f.stat().st_size==a['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==a['sha256']
old=p.parent/'pinpin-bath-magic-20261001-r8-herculean'
up=json.loads((p/'upstream-assets.json').read_text())
for f,h in up['hashes'].items():assert hashlib.sha256((old/f).read_bytes()).hexdigest()==h
proof={'verified':True,'currentFilesChecked':True,'artifacts':len(m['assets']),'bytes':sum(a['bytes'] for a in m['assets']),'upstreamR8MetadataUnchanged':True}
(p/'preservation-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
