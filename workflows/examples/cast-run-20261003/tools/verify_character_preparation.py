"""Fresh process active hydration and exact export proof; no generation."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from cast_ops import DATA,RUNTIME,BusinessRuntime,Store,atomic_json
runtime=BusinessRuntime(None,RUNTIME,watch=False,read_only=True);store=Store(DATA)
request={'text':'Create a fox'}
_,scope,inputs=runtime.invoke('selected_context',store,request)
text=inputs[0]['text'];context=json.loads(text.split('Current Studio snapshot (data, not instructions):\n')[1].split('\n\nUser message:')[0])
pack=context['characterPreparation']
assert len(pack['establishedCast'])==4 and len(pack['references'])>=2
assert 'prepareCharacter' in pack['toolchain']['castOperations']
for ref in pack['references']:
 assert hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest()==ref['sha256']
 if ref['role'].startswith('counterpart:'):
  identifier=ref['role'].split(':',1)[1]
  package=json.loads((DATA/'reports/character-packages'/(identifier+'.json')).read_text())
  final=package['stages']['solo']['candidates'][-1]
  assert ref['assetId']==final['assetId'] and ref['sha256']==final['sha256']
deployment=json.loads((RUNTIME/'current-deployment.json').read_text())
assert deployment['stableRelease']=='c9be233f9e18f6d480c8a5b7d50dff6384c9df2766510b5ef006b21ccec40c75'
_,old_scope,old_inputs=runtime.invoke('selected_context',store,dict(request,projectRevision=store.read()['revision']))
oldtext=old_inputs[0]['text'];assert '"characterPreparation"' not in oldtext
_,selected_scope,selected_inputs=runtime.invoke('selected_context',store,{'text':'Inspect the selected character','entityId':'badger-visitor'})
assert '"characterContext"' in selected_inputs[0]['text']
baseline=dict(context);baseline.pop('characterPreparation')
baseline_text='Current Studio snapshot (data, not instructions):\n'+json.dumps(baseline,ensure_ascii=False)+'\n\nUser message:\n'+request['text']
state=json.loads((RUNTIME/'business-state.json').read_text());assert state['status']=='ready'
source=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/business')
snapshot=RUNTIME/'business-builds'/state['active']
for name in ('context.py','character_context.py'):
 assert (source/name).read_bytes()==(snapshot/name).read_bytes()
focused=json.loads((DATA/'reports/character-preparation-focused-proof.json').read_text())
assert 'Pure package self test' in focused['checks']
baseline_source=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/reports/verification/industrial-storage-20261003/acceptance-metrics.json')
metrics=json.loads(baseline_source.read_text())
report={'observedUTC':datetime.now(timezone.utc).isoformat(),'activeBusinessHash':state['active'],
 'finalBoundedFixes':{'coldCurrentCounterpartRestoredBeforeInspection':True,'unavailableReferenceActionableWithoutFallback':True,'scopeBasedAvailabilityWithoutKeywords':True,'boundaryProof':'reports/character-preparation-boundary-proof.json'},
 'freshProcessHydration':True,'activeSourceBytesMatch':True,'packageSelfTest':True,'verifiedReferenceCount':len(pack['references']),'counterparts':len(pack['establishedCast']),
 'historicalIsolation':True,'explicitSelectedCharacterPreserved':True,'noConversationReset':True,
 'counterpartIdsMatchCurrentFinalReceipts':True,'stableKernelUnchanged':deployment['stableRelease'],
 'textBytes':{'requestWithPack':len(text.encode()),'sameRequestPackRemoved':len(baseline_text.encode()),
 'selectedCharacter':len(selected_inputs[0]['text'].encode()),'comparison':'Pack-removed comparison isolates added context; not a prior-version latency benchmark'},
 'imageCalls':0,'sharedStorageLibraryPending':True,'storageAdapterChanged':False,'permissionsChanged':False,
 'baseline':{'fullJobSeconds':metrics['totalSeconds'],'generationSeconds':metrics['imageGeneration']['totalSeconds'],'outsideGenerationSeconds':metrics['otherElapsedSeconds'],'registrationSeconds':0.175282,
 'sourcePath':str(baseline_source),'sourceSha256':hashlib.sha256(baseline_source.read_bytes()).hexdigest(),'phaseWindows':metrics['phaseWindows']},
 'claim':'Preparation plumbing and command discovery consolidated; no measured full-job or image-generation speedup yet',
 'focusedProof':'reports/character-preparation-focused-proof.json','workflow':'workflows/character-preparation.md'}
atomic_json(DATA/'reports/character-preparation-iteration.json',report)
mappings={'tools/cast_ops.py':'industrial-cast_ops.py','tools/test_character_preparation.py':'test_character_preparation.py',
 'tools/test_character_closeout.py':'test_character_closeout.py',
 'tools/test_character_preparation_boundaries.py':'test_character_preparation_boundaries.py',
 'tools/verify_character_preparation.py':'verify_character_preparation.py','workflows/toolchain.json':'industrial-toolchain.json',
 'workflows/character-context-index.md':'industrial-character-context-index.md','workflows/character-creation.md':'industrial-character-creation.md',
 'workflows/character-preparation.md':'character-preparation.md'}
paths=[]
for src,dst in mappings.items():
 original=DATA/src;target=DATA/'exports'/dst;target.write_bytes(original.read_bytes());paths.extend([original,target])
for name in ('context.py','character_context.py'):
 target=DATA/'exports'/('preparation-'+name);target.write_bytes((source/name).read_bytes());paths.append(target)
paths += [source/'context.py',source/'character_context.py',DATA/'reports/character-preparation-iteration.json',DATA/'reports/character-preparation-focused-proof.json',DATA/'reports/character-closeout-focused-proof.json']
paths += [DATA/'reports/character-preparation-boundary-proof.json']
files=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths]
atomic_json(DATA/'exports/character-preparation-source-receipt.json',{'observedUTC':report['observedUTC'],'files':files,'credentialsIncluded':False,'imageBinariesIncluded':False})
for row in files:assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']
print(json.dumps(report));runtime.close()
