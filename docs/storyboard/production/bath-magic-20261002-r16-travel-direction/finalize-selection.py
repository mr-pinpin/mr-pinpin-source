#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
plan=json.loads((p/'story-plan.json').read_text());assets=json.loads((p/'derivatives.json').read_text())['assets'];rows=[]
for s in [plan['cover'],*plan['scenes']]:
 sid='title' if s['id']=='cover' else s['id'];a=assets[sid];origin=p.parent/('pinpin-'+a['sourceProduction'])
 for field in ['master','web']:
  f=origin/a[field]['path'];assert f.stat().st_size==a[field]['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==a[field]['sha256'],sid
 rows.append({'id':sid,'number':s.get('number'),'feedbackLabel':s.get('feedbackLabel'),'kind':a['kind'],'sourceProduction':a['sourceProduction'],'sourceSceneId':a.get('sourceSceneId'), 'reusedFromProduction':a.get('reusedFromProduction'),'reusedFromSceneId':a.get('reusedFromSceneId'),'master':a['master'],'web':a['web'],'restorationRecord':a.get('restorationRecord'),'generationRecord':a.get('generationRecord'),'upstreamGenerationRecord':a.get('upstreamGenerationRecord'),'upstreamReuseRecord':a.get('upstreamReuseRecord')})
result={'version':1,'status':'complete illustrated draft awaiting user feedback; unpublished','selected':rows}
(p/'selected-scenes.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'selected':len(rows),'new':sum(r['kind']=='generated'for r in rows),'restoredArchive':sum(r['kind']=='restored unchanged archive'for r in rows),'unchangedUpstream':sum(r['kind']=='upstream unchanged'for r in rows)}))
