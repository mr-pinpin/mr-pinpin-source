"""Fresh-process live context/toolchain check; no generation or project mutation."""
import ast, hashlib, json, sys
from pathlib import Path
DATA=Path(__file__).resolve().parents[1]
RUNTIME=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime')
deployment=json.loads((RUNTIME/'current-deployment.json').read_text())
sys.path.insert(0,str(RUNTIME/'stable-releases'/deployment['stableRelease']))
from store import Store,atomic_json
from business_runtime import BusinessRuntime
store=Store(DATA);runtime=BusinessRuntime(None,RUNTIME,watch=False,read_only=True)
_,scope,inputs=runtime.invoke('selected_context',store,{'text':'Inspect this character','entityId':'pinpin'})
snap=json.loads(inputs[0]['text'].split('\n',1)[1].split('\n\nUser message:')[0])
assert snap['storageWorkflow']['prepare'].endswith('prepare <spec.json>')
assert not snap['castWorkflow']['guide'].get('error')
_,historical,oldinputs=runtime.invoke('selected_context',store,{'text':'Inspect historical character','entityId':'pinpin','projectRevision':store.read()['revision']})
assert historical['reviewSnapshot'] and 'storageWorkflow' not in oldinputs[0]['text']
runtime.close()
source=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/business')
status=json.loads((RUNTIME/'business-state.json').read_text());assert status['status']=='ready' and status['error'] is None
active=RUNTIME/'business-builds'/status['active']
changed=['asset_storage.py','routes.py','context.py','character_context.py']
for name in changed:
 ast.parse((source/name).read_text());assert (source/name).read_bytes()==(active/name).read_bytes(),name
atomic_json(DATA/'reports/industrial-storage-fresh-context.json',{'freshProcess':True,'storageWorkflow':snap['storageWorkflow'],
 'guide':snap['castWorkflow']['guide'],'nativeAssetIds':scope['assetIds'],'historicalStorageExcluded':True,
 'activeBusinessHash':status['active'],'activeSourceMatch':changed,'kernelReleaseUnchanged':deployment['stableRelease'],
 'nativeGenerationInvoked':False})
print(json.dumps({'freshContext':True,'historicalIsolation':True,'businessReady':True,'activeBusinessHash':status['active']}))
