"""Isolated actual Store / existing archive adapter tests. No live art or network."""
import hashlib, importlib.util, io, json, sys, tempfile
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
DATA = Path(__file__).resolve().parents[1]
BUSINESS = Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/business')
RUNTIME = Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime')
deployment = json.loads((RUNTIME/'current-deployment.json').read_text())
sys.path.insert(0, str(RUNTIME/'stable-releases'/deployment['stableRelease']))
from store import Store, atomic_json
from model import StudioError
from PIL import Image
spec = importlib.util.spec_from_file_location('industrial_fixture', BUSINESS/'__init__.py', submodule_search_locations=[str(BUSINESS)])
b = importlib.util.module_from_spec(spec); sys.modules[spec.name] = b; spec.loader.exec_module(b)
s = sys.modules['industrial_fixture.asset_storage']
adapter_spec = importlib.util.spec_from_file_location('existing_hf', Path(json.loads((DATA/'workflows/storage-policy.json').read_text())['adapterPath']))
archive_python=json.loads((DATA/'workflows/storage-policy.json').read_text())['pythonPath']
sdk_dir=subprocess.check_output([archive_python,'-B','-c','import huggingface_hub,pathlib; print(pathlib.Path(huggingface_hub.__file__).parent.parent)'],text=True).strip()
sys.path.append(sdk_dir)
hf = importlib.util.module_from_spec(adapter_spec); adapter_spec.loader.exec_module(hf)
if len(sys.argv) > 1 and sys.argv[1] == 'probe':
 probe_store=Store(Path(sys.argv[2]))
 _,scope,inputs=b.selected_context(probe_store,{'text':'Inspect fixture character','entityId':'subject'})
 with patch.object(s,'resolve',side_effect=AssertionError('Historical reads must not restore')):
  _,old_scope,old_inputs=b.selected_context(probe_store,{'text':'Inspect historical fixture','entityId':'subject','projectRevision':probe_store.read()['revision']})
 print(json.dumps({'resolvedBytes':Path(inputs[1]['path']).read_bytes().hex(),'nativePath':inputs[1]['path'],
                   'historicalReadOnly':old_scope['reviewSnapshot'],'selfTest':b.self_test()}));sys.exit(0)
root = Path(tempfile.mkdtemp(prefix='industrial-fixture-', dir=DATA/'reports'))
store = Store(root); (root/'workflows').mkdir()
atomic_json(root/'workflows/storage-policy.json', json.loads((DATA/'workflows/storage-policy.json').read_text()))
atomic_json(root/'workflows/toolchain.json', {'imageGeneration': {'tool': 'image_gen.imagegen'}})
raw=io.BytesIO(); Image.new('RGB',(4,4),'red').save(raw,format='PNG')
asset,_=store.upload_asset(raw.getvalue(),'fixture.png',{'source':'native-imagegen','prompt':'Fixture exact prompt','referenceIds':[]})
state=store.read(); project=state['project']; project['entities']=[{'id':'subject','kind':'character','name':'Fixture subject','identity':'Proposed squirrel','referenceIds':[asset['id']]}]; store.save_project(project,state['revision'])
folder=root/'workflows/characters/subject'; folder.mkdir(parents=True)
(folder/'README.md').write_text('Exact age not stated. Proposed squirrel; no canonical portrait. Deterministic fixture only.')
atomic_json(folder/'evidence.json',{'bibliography':[]})
class FakeAPI:
 def __init__(self): self.objects={}; self.downloads=[]; self.corrupt=False
 def get_bucket_paths_info(self,bucket,paths):
  return [SimpleNamespace(type='file',path=p,size=len(self.objects[p]),xet_hash=hashlib.sha512(self.objects[p]).hexdigest()) for p in paths if p in self.objects]
 def batch_bucket_files(self,bucket,*,add):
  for source,key in add:self.objects[key]=Path(source).read_bytes()
 def download_bucket_files(self,bucket,files,*,raise_on_missing_files):
  for key,target in files:
   self.downloads.append(key); data=self.objects[key]; Path(target).write_bytes(b'x'+data[1:] if self.corrupt else data)
api=FakeAPI()
def transfer(store,cfg,entry,action,root,cache):
 fn=hf.upload_entries if action=='push' else hf.materialize_entries
 proof=fn([entry],root,cfg['bucket'],cache,api=api,workers=1)
 return {'adapterReceipt':proof,'transferSeconds':None,'observedUTC':s.stamp(),'fixture':True}
checks=[]
def check(name,ok):assert ok,name;checks.append({'test':name,'passed':True})
def refuses(name,fn):
 try:fn()
 except (StudioError,hf.StorageError,OSError):check(name,True)
 else:raise AssertionError(name)
with patch.object(s,'transfer',side_effect=transfer):
 check('known ID hashes actual canonical bytes',s.resolve(store,asset['id'])['sha256']==asset['sha256'])
 refuses('unknown ID refused',lambda:s.resolve(store,'asset-unknown'))
 refuses('no backup is never counted remotely verified',lambda:s.resolve(store,asset['id'],True))
 backed=s.backup(store,asset['id']);check('backup requires fresh downloaded hash proof',backed['remoteBackupStatus']=='verified-download' and len(api.downloads)==1)
 restored=s.resolve(store,asset['id'],True);check('cold replica cache downloads exact bytes',restored['source']=='downloaded' and len(api.downloads)==2 and Path(restored['nativePath']).read_bytes()==raw.getvalue())
 check('browser URL and canonical artwork unchanged',restored['assetURL']==asset['url'] and store.asset_path(asset['id']).read_bytes()==raw.getvalue())
 # Removing only deterministic fixture bytes proves missing-canonical restoration.
 store.asset_path(asset['id']).unlink(); restored=s.resolve(store,asset['id']);check('missing canonical restored through stable ID',Path(restored['nativePath']).read_bytes()==raw.getvalue())
 bad=root/'storage/cache/materialized'/Path(restored['nativePath']).name;bad.write_bytes(b'x')
 refuses('conflicting replica is refused, never overwritten',lambda:s.resolve(store,asset['id'],True))
 cfg=s.policy(store)
 with patch.object(s.shutil,'disk_usage',return_value=SimpleNamespace(free=cfg['minFreeBytes'])):
  refuses('low disk fails before dispatch',lambda:s.preflight(store,cfg,cfg['generationReserveBytes']))
 native_home=Path(s.os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
 def volume_space(path):
  path=Path(path)
  return SimpleNamespace(free=cfg['minFreeBytes'] if path.is_relative_to(native_home) else 10**12)
 with patch.object(s.shutil,'disk_usage',side_effect=volume_space):
  refuses('internal native low with TB4 healthy refuses dispatch',lambda:s.preflight(store,cfg,cfg['generationReserveBytes']))
 volume_budget=s.preflight(store,cfg,1)
 check('volume checks deduplicate devices and include native history/output/temp',len(volume_budget['uniqueVolumes'])==len({v['device'] for v in volume_budget['uniqueVolumes']}) and any(any('generated_images' in p for p in v['paths']) for v in volume_budget['uniqueVolumes']))
 small=dict(cfg,maxCacheBytes=1)
 refuses('cache admission is bounded',lambda:s.preflight(store,small,1,1))
 spec={'entityId':'subject','stage':'solo','prompt':'Fixture exact prompt','outputName':'fixture.png','references':[{'assetId':asset['id'],'sha256':asset['sha256'],'role':'identity'}]}
 prepared=s.prepare(store,spec);check('real character preparation uses resolver native path/hash',prepared['references'][0]['nativePath']==str(store.asset_path(asset['id'])) and prepared['references'][0]['sha256']==asset['sha256'])
 check('preparation retains dossier/evidence hashes and output requirements',len(prepared['dossierSha256'])==64 and prepared['outputRequirements']['registeredCandidate'])
 refuses('six native references rejected before dispatch',lambda:s.prepare(store,dict(spec,references=spec['references']*6)))
 refuses('wrong supplied hash refused',lambda:s.prepare(store,dict(spec,references=[dict(spec['references'][0],sha256='0'*64)])))
 refuses('interaction missing target solo refused',lambda:s.prepare(store,dict(spec,stage='interactions')))
 cancelled=s.outcome(store,{'attemptId':prepared['attemptId'],'status':'cancelled','reason':'Preflight-only fixture; no generation invoked'})
 check('outcome releases durable reservation',cancelled['status']=='cancelled')
 check('outcome is idempotent',s.outcome(store,cancelled['outcome'])==cancelled)
 # Corrupt remote is refused before remote verification proof can be created.
 second_raw=io.BytesIO();Image.new('RGB',(4,4),'blue').save(second_raw,format='PNG')
 second,_=store.upload_asset(second_raw.getvalue(),'second.png',{'source':'native-imagegen'})
 api.corrupt=True
 refuses('corrupt downloaded remote cannot count replicated',lambda:s.backup(store,second['id']))
 check('failed backup has no verified receipt',not s.receipt_path(store,second['id'],'backup').exists())
 check('transfer projection contains only byte identity, never prompts',set(backed['adapterReceipt']['entries'][0]) >= {'path','sha256','bytes','object'} and 'prompt' not in json.dumps(backed['adapterReceipt']))
 refuses('arbitrary path escape refused',lambda:s.inside(store,'../outside'))
 check('package self_test',b.self_test())
 # A separate process enters selected-character context with canonical bytes missing.
 store.asset_path(asset['id']).unlink()
 fresh=json.loads(subprocess.check_output([sys.executable,'-B',__file__,'probe',str(root)],text=True))
 check('fresh-process incoming context restores missing bound reference',bytes.fromhex(fresh['resolvedBytes'])==raw.getvalue() and store.asset_path(asset['id']).is_file())
 check('historical/pinned context never invokes mutable storage',fresh['historicalReadOnly'])
atomic_json(DATA/'reports/industrial-storage-focused-proof.json',{'checks':checks,'fixture':str(root),'network':'Fake remote, real existing adapter byte verification; not live HF proof','kernelChanged':False})
print(json.dumps({'passed':len(checks),'report':'reports/industrial-storage-focused-proof.json'}))
