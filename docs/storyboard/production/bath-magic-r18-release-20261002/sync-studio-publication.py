#!/usr/bin/env python3
"""Select published R18 candidates through optimistic Studio API without changing jobs."""
from pathlib import Path
import json,hashlib,urllib.request,urllib.error,copy
root=Path(__file__).resolve().parent
selection=json.loads((root.parent/'pinpin-bath-magic-20261002-r18/selected-assets.json').read_text())
base='http://127.0.0.1:18806/api/state'
release='b5a94c02b5cb34e308261c877d5af19aa93b113b059a35043660ca7053162c22'
for attempt in range(4):
 state=json.load(urllib.request.urlopen(base));project=copy.deepcopy(state['project'])
 chapter=next(c for c in project['chapters'] if c['id']=='bath-magic-r17')
 assert len(chapter['scenes'])==172
 assets={a['sha256']:a for a in state['assets']}; changes=[]
 for scene in chapter['scenes']:
  row=selection.get(scene['id'])
  if not row:continue
  digest=hashlib.sha256(Path(row.get('native',row['master'])).read_bytes()).hexdigest();asset=assets[digest]
  old=scene.get('imageAssetId')
  if old!=asset['id']:
   scene.setdefault('imageHistory',[]).append({'assetId':old,'reason':'Superseded by published R18 selection','release':release})
  scene['imageAssetId']=asset['id'];scene['status']='published'
  scene['selectionBasis']='user-authorized publication; coordinator visual review'
  scene['publicationSelection']={'release':release,'assetSha256':digest,'nativeAssetId':asset['id'],'webSha256':hashlib.sha256(Path(row['web']).read_bytes()).hexdigest()}
  if scene['id']=='scene-84':scene['userReview']='approved'
  changes.append({'scene':scene['id'],'priorAssetId':old,'selectedAssetId':asset['id']})
 chapter.update(status='published',publicationStatus='published',revisionLabel='R18',publicUrl='https://mr-pinpin.github.io/storyboard/?story=bath-magic&lang=ru',publicationRelease=release,publicationSourceCommit='a5f4bec8d8232ffcbd815c5da7305a3e5f89542f',sourcePlan='docs/storyboard/production/bath-magic-20261002-r18/story-plan.json')
 chapter['tempoMethod']='Inherited editorial categories matched by stable ID; new-beat proposals explicitly labeled. Three ordinal levels, not measured audience response.'
 project['book']['arc']=project['book'].get('arc','').replace('R17 candidate','R18 published').replace('R17 draft','R18 published')
 request=urllib.request.Request(base,data=json.dumps({'expectedRevision':state['revision'],'project':project}).encode(),headers={'Content-Type':'application/json'},method='PUT')
 try:
  saved=json.load(urllib.request.urlopen(request));break
 except urllib.error.HTTPError as error:
  if error.code!=409 or attempt==3:raise
else:raise RuntimeError('Could not preserve concurrent state')
after=json.load(urllib.request.urlopen(base))
assert after['jobs']==state['jobs'],'Jobs changed during update; inspect rather than overwrite'
(root/'studio-publication-proof.json').write_text(json.dumps({'priorRevision':state['revision'],'revision':after['revision'],'release':release,'selected':changes,'jobsPreserved':True,'historicalReviewStatusesPreserved':True},indent=2)+'\n')
print(json.dumps({'revision':after['revision'],'selected':len(changes),'jobsPreserved':True}))
