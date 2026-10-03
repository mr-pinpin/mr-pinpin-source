"""Reproducible isolated Store tests: synthetic registered images, no transcript/thread."""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

DATA = Path(__file__).resolve().parents[1]
BUSINESS = Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/business')
KERNEL = Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime/stable-releases/c9be233f9e18f6d480c8a5b7d50dff6384c9df2766510b5ef006b21ccec40c75')
sys.path.insert(0, str(KERNEL))
spec = importlib.util.spec_from_file_location('isolated_business', BUSINESS / '__init__.py', submodule_search_locations=[str(BUSINESS)])
business = importlib.util.module_from_spec(spec); sys.modules[spec.name] = business; spec.loader.exec_module(business)
from isolated_business import context
from isolated_business.cast_workflow import workflow_context, read_document, save_progress
from isolated_business.cast_inventory import record_package
from store import Store, atomic_json
from PIL import Image

def probe(root):
    store = Store(root)
    assert not (store.root / 'conversation.json').exists()
    _, scope, inputs = business.selected_context(store, {'text':'continue the cast'})
    snapshot = json.loads(inputs[0]['text'].split('\n',1)[1].split('\n\nUser message:')[0])
    return {'entity': scope['entityId'], 'workflow': snapshot['castWorkflow'], 'contextBytes':len(inputs[0]['text'].encode()),
            'guideOccurrences':inputs[0]['text'].count('FIXTURE_GUIDE_V'), 'dossierOccurrences': inputs[0]['text'].count('FIXTURE_DOSSIER')}

if len(sys.argv)>1 and sys.argv[1]=='probe':
    print(json.dumps(probe(Path(sys.argv[2])))); sys.exit(0)

root = Path(tempfile.mkdtemp(prefix='cast-isolated-', dir=DATA / 'reports'))
store = Store(root)
(root/'workflows/characters/partial').mkdir(parents=True)
(root/'reports/character-packages').mkdir(parents=True)
(root/'workflows/character-creation.md').write_text('FIXTURE_GUIDE_V1: complete solo and interactions')
(root/'workflows/cast-run.md').write_text('Resume durable stage receipts')
(root/'workflows/characters/partial/README.md').write_text('FIXTURE_DOSSIER: source-established fixture, no generation')
assets=[]
for color in ('red','green','blue'):
    output=io.BytesIO(); Image.new('RGB',(4,4),color).save(output,format='PNG')
    assets.append(store.upload_asset(output.getvalue(),color+'.png',{'tool':'deterministic fixture image; NOT imagegen','prompt':color,'references':[]})[0])
state=store.read(); project=state['project']; project['entities']=[{'id':name,'kind':'character','name':name,'referenceIds':[]} for name in ('partial','complete')]; store.save_project(project,state['revision'])
history_revision=store.read()['revision']
def candidate(asset, entity='partial', role='solo'): return {'assetId':asset['id'],'sha256':asset['sha256'],'entityId':entity,'stage':role}
manifest={'schemaVersion':1,'characters':[{'id':name,'canonicalName':name,'status':'completed','outputs':[],'exactAge':'not stated','evidencedLifeStage':'fixture','aliases':[], 'dossierPath':'workflows/characters/'+name+'/README.md','evidencePath':'workflows/characters/'+name+'/evidence.json'} for name in ('partial','complete')]}
def write_run(value): atomic_json(root/'workflows/cast-run.json',value)
write_run(manifest)
atomic_json(root/'reports/character-packages/partial.json',{'entityId':'partial','stages':{'solo':{'candidates':[candidate(assets[0])]}}})
atomic_json(root/'reports/character-packages/complete.json',{'entityId':'complete','stages':{'solo':{'candidates':[candidate(assets[1], 'complete')]},'interactions':{'candidates':[candidate(assets[2], 'complete', 'interactions')]}}})
results=[]
def check(name, condition):
    assert condition, name
    results.append({'test':name,'passed':True})
one=workflow_context(store); check('status alone cannot complete; solo-only resumes interactions',one['nextEntityId']=='partial' and one['selected']['nextStage']=='interactions')
check('genuine distinct two-stage package skipped',one['remaining']==['partial'])
fresh=json.loads(subprocess.check_output([sys.executable,'-B',str(Path(__file__).resolve()),'probe',str(root)],text=True))
check('independent fresh process without conversation/thread sees exact missing stage',fresh['entity']=='partial' and fresh['workflow']['selected']['nextStage']=='interactions')
(root/'workflows/character-creation.md').write_text('FIXTURE_GUIDE_V2: changed Markdown, no Python policy edits')
fresh2=json.loads(subprocess.check_output([sys.executable,'-B',str(Path(__file__).resolve()),'probe',str(root)],text=True))
check('changed Markdown loaded in second independent process',fresh2['workflow']['guide']['sha256']!=fresh['workflow']['guide']['sha256'] and 'V2' in fresh2['workflow']['guide']['text'])
check('guide/dossier serialized once',fresh2['guideOccurrences']==fresh2['dossierOccurrences']==1)
check('aggregate bounded context',fresh2['contextBytes']<60000)
atomic_json(root/'reports/character-packages/partial.json',{'entityId':'partial','stages':{'solo':{'candidates':[candidate(assets[0], 'complete')]}}})
check('receipt for a different entity cannot complete a stage',workflow_context(store)['selected']['nextStage']=='solo')
atomic_json(root/'reports/character-packages/partial.json',{'entityId':'partial','stages':{'solo':{'candidates':[candidate(assets[0], 'partial', 'interactions')]}}})
check('receipt role must match required stage',workflow_context(store)['selected']['nextStage']=='solo')
asset_file=store.asset_path(assets[0]['id']); retained_bytes=asset_file.read_bytes(); asset_file.unlink()
atomic_json(root/'reports/character-packages/partial.json',{'entityId':'partial','stages':{'solo':{'candidates':[candidate(assets[0])]}}})
check('registered metadata without actual image bytes cannot complete',workflow_context(store)['selected']['nextStage']=='solo')
asset_file.write_bytes(retained_bytes)
atomic_json(root/'reports/character-packages/partial.json',{'entityId':'partial','stages':{'solo':{'candidates':[candidate(assets[0])]},'interactions':{'candidates':[candidate(assets[0], 'partial', 'interactions')]}}})
check('same asset cannot serve both required pages',workflow_context(store)['selected']['nextStage']=='interactions')
for bad in [{'assetId':'asset-unknown','sha256':'0'*64},{'assetId':assets[0]['id'],'sha256':'0'*64}]:
    atomic_json(root/'reports/character-packages/partial.json',{'entityId':'partial','stages':{'solo':{'candidates':[bad]}}})
    check('unknown or mismatched-hash stage incomplete',workflow_context(store)['selected']['nextStage']=='solo')
try: record_package(store,'partial',[assets[0]['id'],assets[0]['id']],'fixture')
except ValueError: check('duplicate package write rejected',True)
else: raise AssertionError('duplicate write accepted')
for malformed in [{'schemaVersion':1,'characters':[None]}, {'schemaVersion':1,'characters':[{'id':'same'},{'id':'same'}]}, {'schemaVersion':1,'characters':[{'id':'../escape'}]}, {'schemaVersion':1,'characters':[{'id':'a','stageReceipts':{'solo':[]}}]}]:
    write_run(malformed); check('malformed manifest graceful',bool(workflow_context(store).get('error')))
write_run(manifest)
(root/'huge.md').write_bytes(b'x'*100000)
reads=[]; original=Path.open
class Guard:
    def __init__(self,stream): self.stream=stream
    def __enter__(self): return self
    def __exit__(self,*args): self.stream.close()
    def read(self,size=-1): reads.append(size); assert 0<size<=33; return self.stream.read(size)
with patch.object(Path,'open',lambda path,*args,**kw:Guard(original(path,*args,**kw))):
    oversized=read_document(root,'huge.md',32)
check('bounded read before allocation; no false full-file hash',reads==[33] and oversized['truncated'] and 'sha256' not in oversized and 'text' not in oversized)
with patch.object(context,'workflow_context',side_effect=AssertionError('historical imported live run')):
    _,scope,inputs=business.selected_context(store,{'text':'continue the cast','projectRevision':history_revision})
    check('historical context never reads live mutable workflow or advances',scope['entityId'] is None and 'castWorkflow' not in inputs[0]['text'])
check('no conversation copied; fixture does not share live Store',not (root/'conversation.json').exists() and root!=DATA)
assert business.self_test()
report={'fixtureRoot':str(root),'tests':results,'freshProcessOne':fresh,'freshProcessTwo':fresh2,'actualModelThreadStarted':False,
        'proofScope':'Isolated real Store and registered deterministic image fixtures, two independent processes with no conversation/thread. No actual new Codex agent thread capability used; this is reproducible application persistence proof, not a claim of a new model session.'}
(DATA/'reports/cast-isolated-persistence-proof.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':len(results),'fixtureRoot':str(root),'freshNextStage':fresh2['workflow']['selected']['nextStage']}))
