#!/usr/bin/env python3
"""Synchronize selected image metadata with frozen derivative provenance; never rewrite captions."""
from pathlib import Path
import json,datetime
p=Path(__file__).resolve().parent
f=p/'story-plan.json';plan=json.loads(f.read_text());assets=json.loads((p/'derivatives.json').read_text())['assets']
casts={'scene-04':['Mama','PinPin'],'scene-04a':['PinPin','Mama'],'scene-04b':['PinPin','Rabbit'],'scene-04c':['PinPin','Rabbit'],'scene-04d':['PinPin','Rabbit','Robin','Bluebird'],'scene-05':['PinPin','Rabbit','Robin','Bluebird'],'scene-05a':['PinPin','Rabbit','Robin'],'scene-05b':['PinPin','Rabbit','Robin','Bluebird'],'scene-05c':['PinPin','Rabbit','Robin','Bluebird'],'scene-05d':['PinPin','Mama']}
for s in [plan['cover'],*plan['scenes']]:
 sid='title'if s['id']=='cover'else s['id'];a=assets[sid]
 s.update({'selectedImageProduction':a['sourceProduction'],'selectedMaster':a['master']['path'],'selectedMasterSha256':a['master']['sha256'],'selectedWeb':a['web']['path'],'selectedWebSha256':a['web']['sha256'],'selectedImagePath':a['web']['path'],'image':a['web']['path'],'imageStatus':'available','selectionKind':a['kind']})
 if sid in casts:
  s['cast']=casts[sid];s['reviewStatus']='Selected illustration inspected by production agent and coordinator; awaiting user feedback; unpublished.'
  s['status']='selected illustrated draft for user review';s['candidateMaster']=a['master']['path'];s['generationRecord']=a['generationRecord'];s['artStrategy']='R14 image-led illustration using preserved references; selected native and display bytes recorded in derivatives.json.'
  for key in ['reuseRecord','upstreamSelected','upstreamSceneId']:s.pop(key,None)
plan['status']='Complete illustrated outdoor water-trip draft; awaiting user feedback; unpublished'
plan['metadataFrozenAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
f.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'metadataSynchronized':len(assets),'castsReviewed':len(casts),'captionsUnchanged':True}))
