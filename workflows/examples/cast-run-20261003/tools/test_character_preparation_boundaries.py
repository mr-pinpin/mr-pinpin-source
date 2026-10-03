"""Isolated cold-reference and scope tests; no production cold simulation/network."""
import importlib.util,sys,json,tempfile,io,hashlib
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from cast_ops import DATA,Store,atomic_json
from model import StudioError
source=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/business')
spec=importlib.util.spec_from_file_location('boundary_fixture',source/'__init__.py',submodule_search_locations=[str(source)])
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)
cc=sys.modules['boundary_fixture.character_context'];context=sys.modules['boundary_fixture.context'];storage=cc.asset_storage
checks=[]
def check(name,ok):assert ok,name;checks.append(name)
def snapshot(inputs):return json.loads(inputs[0]['text'].split('Current Studio snapshot (data, not instructions):\n')[1].split('\n\nUser message:')[0])
with tempfile.TemporaryDirectory(dir=DATA/'reports') as tmp:
 root=Path(tmp);store=Store(root);(root/'workflows').mkdir()
 cfg={'characterPreparation':{'counterpartIds':['parent']},'storageWorkflow':{'resolve':'existing resolve command'}}
 atomic_json(root/'workflows/toolchain.json',cfg);atomic_json(root/'workflows/storage-policy.json',{})
 images=[]
 for color in ('red','blue'):
  raw=io.BytesIO();Image.new('RGB',(4,4),color).save(raw,format='PNG')
  asset,_=store.upload_asset(raw.getvalue(),color+'.png',{'source':'native-imagegen'});images.append((asset,raw.getvalue()))
 old,current=[i[0] for i in images];expected_bytes=images[1][1]
 state=store.read();project=state['project'];project['entities']=[{'id':'parent','name':'Parent','kind':'character','identity':'Adult squirrel','referenceIds':[]}]
 store.save_project(project,state['revision'])
 row={'id':'parent','canonicalName':'Parent','exactAge':'not stated','evidencedLifeStage':'adult',
  'stages':{'solo':{'assetId':current['id'],'sha256':current['sha256']}}}
 atomic_json(root/'workflows/cast-run.json',{'schemaVersion':1,'characters':[row]})
 candidates=[dict(entityId='parent',stage='solo',assetId=a['id'],sha256=a['sha256']) for a in (old,current)]
 atomic_json(root/'reports/character-packages/parent.json',{'entityId':'parent','stages':{'solo':{'candidates':candidates}}})
 cold=store.asset_path(current['id']);cold.unlink() # isolated fixture bytes only
 resolved=[]
 def restore(store_arg,identifier,*args,**kwargs):
  assert identifier==current['id'];resolved.append(identifier)
  cold.write_bytes(expected_bytes)
  return {'assetId':identifier,'sha256':current['sha256'],'nativePath':str(cold)}
 with patch.object(storage,'resolve',side_effect=restore):
  pack=cc.starter_pack(store,store.read(),{},cfg)
 check('Cold exact current ID restored before byte inspection',resolved==[current['id']] and pack['references'][0]['assetId']==current['id'])
 check('Restored bytes and hash exact',hashlib.sha256(cold.read_bytes()).hexdigest()==current['sha256'] and pack['availability']=='ready')
 cold.unlink()
 with patch.object(storage,'resolve',side_effect=StudioError('Verified replica unavailable')):
  pack=cc.starter_pack(store,store.read(),{},cfg)
 check('Unavailable current ID remains actionable',pack['availability']=='blocked' and pack['missingReferences'][0]['assetId']==current['id'] and pack['references'][0]['path'] is None)
 check('Available older candidate never substituted',all(r['assetId']!=old['id'] for r in pack['references']) and not cold.exists())
 with patch.object(storage,'resolve',side_effect=restore),patch.object(context,'prepared_toolchain',return_value=cfg):
  _,_,inputs=b.selected_context(store,{'text':'Create a fox'})
  check('Ordinary wording gets preparation availability',snapshot(inputs)['characterPreparation']['availability']=='ready')
  _,_,inputs=b.selected_context(store,{'text':'A different ordinary request'})
  check('Availability independent of species/keyword guessing','characterPreparation' in snapshot(inputs))
  _,_,inputs=b.selected_context(store,{'text':'Create a fox','characterPreparation':False})
  check('Explicit opt-out respected','characterPreparation' not in snapshot(inputs))
  _,_,inputs=b.selected_context(store,{'text':'Create a fox','entityId':'parent'})
  check('Explicit selected scope retains original workflow','characterPreparation' not in snapshot(inputs) and 'characterContext' in snapshot(inputs))
  _,_,inputs=b.selected_context(store,{'text':'Create a fox','entityId':'parent','characterPreparation':True})
  check('Explicit preparation request works in selected scope','characterPreparation' in snapshot(inputs))
 st=store.read();st['readOnly']=True
 with patch.object(storage,'resolve',side_effect=AssertionError('Historical write')):
  check('Historical starter never resolves or writes',cc.starter_pack(store,st,{},cfg) is None)
  _,_,inputs=b.selected_context(store,{'text':'Create a fox','projectRevision':store.read()['revision']})
  check('Pinned context excludes mutable preparation pack','characterPreparation' not in snapshot(inputs))
 check('Pack remains bounded',len(json.dumps(pack).encode())<10000 and len(pack['references'])<=6)
 check('Pure business self test',b.self_test() is True)
atomic_json(DATA/'reports/character-preparation-boundary-proof.json',{'passed':len(checks),'checks':checks,'productionBytesRemoved':False,'networkCalls':0,'imageCalls':0})
print(json.dumps({'passed':len(checks)}))
