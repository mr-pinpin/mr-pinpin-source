"""Read-only active-bundle verification; no transport or live workflow mutation."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio')
RUNTIME=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime')
deploy=json.loads((RUNTIME/'current-deployment.json').read_text())
sys.path.insert(0,str(RUNTIME/'stable-releases'/deploy['stableRelease']))
from business_runtime import BusinessRuntime
from store import Store
runtime=BusinessRuntime(None,RUNTIME,watch=False,read_only=True)
business=json.loads((RUNTIME/'business-state.json').read_text()); ui=json.loads((RUNTIME/'workspace-state.json').read_text())
assert business['status']==ui['status']=='ready'
checks={}
for file in ('cast_workflow.py','context.py','routes.py','cast_inventory.py','__init__.py','character_context.py'):
    checks[file]=(SOURCE/'business'/file).read_bytes()==(RUNTIME/'business-builds'/business['active']/file).read_bytes()
checks['media-workspace.js']=(SOURCE/'web/workspace-dev/media-workspace.js').read_bytes()==(RUNTIME/'workspace-builds'/ui['latest']/'media-workspace.js').read_bytes()
assert all(checks.values())
_,scope,inputs=runtime.invoke('selected_context',Store(ROOT),{'text':'continue the cast'})
snap=json.loads(inputs[0]['text'].split('\n',1)[1].split('\n\nUser message:')[0])
run=snap['castWorkflow']; guide=run['guide']; assert guide['sha256']==hashlib.sha256((ROOT/'workflows/character-creation.md').read_bytes()).hexdigest()
manifest=json.loads((ROOT/'workflows/cast-run.json').read_text())
assert scope['entityId']==run['nextEntityId']==manifest['nextEntityId']
assert 'guide' not in snap.get('characterContext',{}).get('persistentWorkflow',{})
assert sum(1 for _ in run['characters'] if _['status'] in ('produced','accepted','completed'))==len(run['characters'])-len(run['remaining'])
report={'business':business,'workspace':ui,'sourceMatches':checks,'liveFreshContextEntity':scope['entityId'],
        'workflowSha256':guide['sha256'],'remaining':run['remaining'],'guideLoaded':bool(guide.get('text') or guide.get('sections')),
        'note':'Fresh local application-context invocation without prior message state; not a claim of a new model thread. New browser verification not performed.'}
_,explicit_scope,explicit_inputs=runtime.invoke('selected_context',Store(ROOT),{'text':'inspect current character references','entityId':'tarin'})
explicit=json.loads(explicit_inputs[0]['text'].split('\n',1)[1].split('\n\nUser message:')[0])
native=explicit['characterContext']; policy=native['registrationToolchain']['imageGeneration']
assert policy['maxInputReferences']==5
receipt=json.loads((ROOT/'reports/character-packages/tarin.json').read_text())
solo=[c for c in receipt['stages']['solo']['candidates'] if c.get('qaDisposition')!='needs-repair'][-1]
assert native['references'][0]['id']==solo['assetId'] and 'primary-working-identity:verified-solo' in native['references'][0]['roles']
report['explicitFreshTarinInputs']={'primarySoloId':native['references'][0]['id'],'maxInputReferences':policy['maxInputReferences'],'roles':[r['roles'] for r in native['references']]}
(ROOT/'reports/cast-active-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
runtime.close()
