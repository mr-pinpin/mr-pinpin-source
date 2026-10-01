#!/usr/bin/env python3
"""Index R4 preproduction studies, never claim finished scene illustrations."""
import hashlib
import json
import os
from pathlib import Path
root=Path(__file__).resolve().parent
derivatives=json.loads((root/'derivatives.json').read_text()).get('assets',{}) if (root/'derivatives.json').exists() else {}
def identity(path):
    result={'path':path.relative_to(root).as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    asset=derivatives.get(path.stem,{})
    if asset.get('width'):result.update(width=asset['width'],height=asset['height'])
    return result
studies=[identity(p) for p in sorted((root/'web').glob('duck*.webp'))]
documents=[]
for name in ['STORY.md','REVIEW.md','story-plan.json','continuity.json','CONTINUITY.md','PREPRODUCTION.md','derivatives.json','input-preservation.json']:
    if (root/name).is_file():documents.append({'path':name,'title':name})
for p in sorted((root/'prompts').glob('*.txt')):documents.append({'path':p.relative_to(root).as_posix(),'title':p.name})
data={'version':1,'status':'preproduction; scene artwork not commissioned or completed','studies':studies,'documents':documents}
temp=root/f'.media-{os.getpid()}.json';temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(root/'media.json')
print(json.dumps({'studies':len(studies),'finishedSceneImages':0}))
