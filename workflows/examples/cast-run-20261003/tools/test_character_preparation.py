"""Focused isolated spec/preparation checks; no image calls or live mutations."""
import importlib.util,sys,json,tempfile,io,hashlib
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import cast_ops
from store import Store,atomic_json
SOURCE=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/business')
loader=importlib.util.spec_from_file_location('preparation_fixture',SOURCE/'__init__.py',submodule_search_locations=[str(SOURCE)])
b=importlib.util.module_from_spec(loader);sys.modules[loader.name]=b;loader.loader.exec_module(b)
s=sys.modules['preparation_fixture.asset_storage'];cc=sys.modules['preparation_fixture.character_context']
checks=[]
def check(name,ok): assert ok,name;checks.append(name)
with tempfile.TemporaryDirectory(dir=cast_ops.DATA/'reports') as tmp:
 root=Path(tmp);store=Store(root);(root/'workflows').mkdir()
 config=json.loads((cast_ops.DATA/'workflows/toolchain.json').read_text())
 config['characterPreparation']['counterpartIds']=[]
 atomic_json(root/'workflows/toolchain.json',config)
 atomic_json(root/'workflows/storage-policy.json',json.loads((cast_ops.DATA/'workflows/storage-policy.json').read_text()))
 atomic_json(root/'workflows/cast-run.json',{'characters':[]})
 raw=io.BytesIO();Image.new('RGB',(4,4),'red').save(raw,format='PNG')
 asset,_=store.upload_asset(raw.getvalue(),'style.png',{'source':'native-imagegen'})
 state=store.read();project=state['project'];project['book']['styleReferenceIds']=[asset['id']];store.save_project(project,state['revision'])
 class Runtime:
  def invoke(self,method,*args):
   if method=='selected_context':
    st=args[0].read();entity=next(e for e in st['project']['entities'] if e['id']==args[1]['entityId'])
    from preparation_fixture.cast_workflow import reconcile_character
    verified=reconcile_character(store,st,{'id':entity['id']})
    pack,_=cc.hydrate_character(store,st,entity,[],[],cc.ReferenceIndex(st),{'selected':dict(verified,id=entity['id'])})
    return '',{},[{'text':'Current Studio snapshot (data, not instructions):\n'+json.dumps({'characterContext':pack})+'\n\nUser message: prepare'}]
   with s.operation(store): return 200,s.prepare(store,args[-1])
 spec={'entityId':'fixture-visitor','name':'Unnamed visitor','request':'Create a proposed young visitor',
  'identity':'Young stocky badger','scale':'About child height; unmeasured','geometry':'Two arms and legs',
  'lifeStage':'young, request evidence','proposed':True,'stage':'solo','prompt':'Exact fixture prompt'}
 with patch.object(cast_ops,'DATA',root):
  result=cast_ops.prepare_character(Runtime(),store,spec)
  prepared=json.loads(Path(result['preparedSpec']).read_text())
  check('One spec initializes and prepares actual fixture',prepared['status']=='prepared')
  check('Exact prompt persisted unchanged',Path(prepared['promptFile']).read_text()==spec['prompt'])
  check('Native references verified/capped',len(prepared['references'])==1 and prepared['references'][0]['sha256']==asset['sha256'])
  evidence=json.loads((root/'workflows/characters/fixture-visitor/evidence.json').read_text())
  check('Request/proposal/unknown age retained',evidence['proposed'] and evidence['exactAge']=='not stated' and evidence['bibliography'][0]['excerpt']==spec['request'])
  before=(root/'workflows/characters/fixture-visitor/README.md').read_bytes()
  again=cast_ops.prepare_character(Runtime(),store,spec)
  check('Resume preserves curated dossier',before==(root/'workflows/characters/fixture-visitor/README.md').read_bytes())
  check('Attempts distinct and retained',again['attemptId']!=result['attemptId'] and Path(result['preparedSpec']).exists())
  pixels=io.BytesIO();Image.new('RGB',(4,4),'blue').save(pixels,format='PNG')
  solo,_=store.upload_asset(pixels.getvalue(),'solo.png',{'source':'native-imagegen'})
  atomic_json(root/'reports/character-packages/fixture-visitor.json',{'entityId':'fixture-visitor',
    'stages':{'solo':{'candidates':[{'entityId':'fixture-visitor','stage':'solo','assetId':solo['id'],'sha256':solo['sha256']}]}}})
  interaction=cast_ops.prepare_character(Runtime(),store,{'entityId':'fixture-visitor','stage':'interactions','prompt':'Exact family contact prompt'})
  prepared_interaction=json.loads(Path(interaction['preparedSpec']).read_text())
  check('Interaction starts with verified real target solo',prepared_interaction['references'][0]['assetId']==solo['id'] and 'primary' in prepared_interaction['references'][0]['role'])
  check('Both page and anatomy requirements retained',prepared_interaction['outputRequirements']['stages']==['solo','interactions'] and 'contact' in prepared_interaction['outputRequirements']['visualQA'])
  refused=dict(spec,entityId='second-visitor',proposed=False)
  try:cast_ops.prepare_character(Runtime(),store,refused)
  except ValueError:checks.append('New canonical fact invention refused')
  else:raise AssertionError('Undisclosed proposal accepted')
  st=store.read();st['readOnly']=True
  check('Historical starter pack isolated',cc.starter_pack(store,st,{},config) is None)
 check('Pure package self test',b.self_test() is True)
atomic_json(cast_ops.DATA/'reports/character-preparation-focused-proof.json',{'passed':len(checks),'checks':checks,'imageCalls':0,'storageAdapterChanged':False})
print(json.dumps({'passed':len(checks)}))
