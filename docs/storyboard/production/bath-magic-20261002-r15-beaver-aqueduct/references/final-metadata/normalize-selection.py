#!/usr/bin/env python3
from pathlib import Path
import json,datetime
p=Path(__file__).resolve().parent;f=p/'story-plan.json';plan=json.loads(f.read_text());assets=json.loads((p/'derivatives.json').read_text())['assets']
for s in [plan['cover'],*plan['scenes']]:
 sid='title'if s['id']=='cover'else s['id'];a=assets[sid]
 s.update({'selectedImageProduction':a['sourceProduction'],'selectedMaster':a['master']['path'],'selectedMasterSha256':a['master']['sha256'],'selectedWeb':a['web']['path'],'selectedWebSha256':a['web']['sha256'],'selectedImagePath':a['web']['path'],'image':a['web']['path'],'imageStatus':'available','selectionKind':a['kind']})
 if a['kind']=='generated':
  s['reviewStatus']='Selected illustration inspected by production agent and coordinator; awaiting user feedback; unpublished.'
  s['status']='selected illustrated draft for user review';s['candidateMaster']=a['master']['path'];s['generationRecord']=a['generationRecord']
  for key in ['reuseRecord','upstreamSelected','upstreamSceneId']:s.pop(key,None)
 if a['kind']=='restored unchanged archive':
  s['reviewStatus']='Exact archived R8 image selected by coordinator to restore the requested gag; no generation or new user approval implied.'
  s['restorationRecord']=a['restorationRecord']
plan['status']='Complete illustrated Beaver/aqueduct expansion draft; awaiting user feedback; unpublished';plan['metadataFrozenAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
f.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'selectedMetadataUpdated':len(plan['scenes'])+1,'captionsUnchanged':True}))
