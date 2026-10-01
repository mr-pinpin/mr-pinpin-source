#!/usr/bin/env python3
"""Record the final selected art with explicit reused/new provenance."""
import json
from pathlib import Path
root=Path(__file__).resolve().parent
plan=json.loads((root/'story-plan.json').read_text())
derivatives=json.loads((root/'derivatives.json').read_text())['assets']
rows=[]
for scene in [plan['cover'],*plan['scenes']]:
    slug='title' if scene['id']=='cover' else scene['id'];asset=derivatives[slug]
    assert scene['selectedMaster']==asset['master']['path'],scene['id']
    assert scene['selectedMasterSha256']==asset['master']['sha256'],scene['id']
    row={'id':scene['id'],'master':asset['master'],'web':asset['web'],'width':asset['width'],'height':asset['height']}
    if scene.get('reuseRecord'):row.update(kind='reused unchanged',reuseRecord=scene['reuseRecord'],reusedFrom=scene.get('reusedFrom','cover'))
    else:row.update(kind='newly generated',generationRecord=scene['generationRecord'])
    rows.append(row)
(root/'selected-scenes.json').write_text(json.dumps({'version':1,'status':'complete illustrated draft; not published or user-approved','scenes':rows},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'selected':len(rows),'reused':sum(x['kind']=='reused unchanged' for x in rows),'new':sum(x['kind']=='newly generated' for x in rows)}))
