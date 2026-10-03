"""Isolated real Store fixture: source/layout and partial solo hydration."""
import importlib.util,io,json,sys,tempfile
from pathlib import Path
DATA=Path(__file__).resolve().parents[1]
BUSINESS=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/business')
KERNEL=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime/stable-releases/c9be233f9e18f6d480c8a5b7d50dff6384c9df2766510b5ef006b21ccec40c75')
sys.path.insert(0,str(KERNEL))
spec=importlib.util.spec_from_file_location('reference_fixture_business',BUSINESS/'__init__.py',submodule_search_locations=[str(BUSINESS)])
business=importlib.util.module_from_spec(spec);sys.modules[spec.name]=business;spec.loader.exec_module(business)
from store import Store,atomic_json
from PIL import Image
root=Path(tempfile.mkdtemp(prefix='cast-input-fixture-',dir=DATA/'reports'));store=Store(root)
(root/'workflows/characters/new').mkdir(parents=True);(root/'reports/character-packages').mkdir(parents=True)
(root/'workflows/character-creation.md').write_text('Fixture guide');(root/'workflows/cast-run.md').write_text('Fixture contract')
(root/'workflows/characters/new/README.md').write_text('Exact age not stated; new squirrel')
assets=[]
for color in ('red','green','blue','yellow','purple'):
    out=io.BytesIO();Image.new('RGB',(4,4),color).save(out,format='PNG');assets.append(store.upload_asset(out.getvalue(),color,{'source':'deterministic fixture, not generated art'})[0])
source,layout,style,solo,partner=assets
state=store.read();p=state['project'];p['entities']=[{'id':'new','name':'New squirrel','kind':'character','identity':'Squirrel; portrait proposed','referenceIds':[]},{'id':'peer','name':'Peer rabbit','kind':'character','identity':'Rabbit','referenceIds':[partner['id']]}]
p['book']['styleReferenceIds']=[style['id']]
p['book']['characterReferenceDefaults']={'layoutReference':{'assetId':layout['id'],'sha256':layout['sha256']},'characters':{'new':{'sourceReferences':[{'assetId':source['id'],'sha256':source['sha256'],'role':'original-context'}],'counterpartIds':['peer'],'designBasis':'Portrait proposed; source text establishes squirrel','speciesAndRole':'Squirrel friend'}}}
store.save_project(p,state['revision'])
atomic_json(root/'workflows/cast-run.json',{'schemaVersion':1,'characters':[{'id':'new','status':'pending','outputs':[]}]})
def snapshot():
    _,scope,inputs=business.selected_context(store,{'text':'continue the cast'});return json.loads(inputs[0]['text'].split('\n',1)[1].split('\n\nUser message:')[0]),scope,inputs
checks=[]
def check(label,value):assert value,label;checks.append({'test':label,'passed':True})
s,scope,inputs=snapshot();refs={r['id']:r for r in s['characterContext']['references']}
check('new subject source is native input, not only family style',source['id'] in scope['assetIds'] and len(inputs)>2)
check('layout role distinct and counterpart hydrated', 'layout-direction-only:no-species-transfer' in refs[layout['id']]['roles'] and partner['id'] in refs)
check('proposal disclosed rather than style called identity','proposed' in s['characterContext']['referenceInstructions']['designBasis'])
atomic_json(root/'reports/character-packages/new.json',{'entityId':'new','stages':{'solo':{'candidates':[{'entityId':'new','stage':'solo','assetId':solo['id'],'sha256':solo['sha256']}]}}})
s,scope,inputs=snapshot();refs=s['characterContext']['references']
check('partial resumes interactions without new solo','interactions'==s['castWorkflow']['selected']['nextStage'])
check('real verified target solo is first primary native identity',scope['assetIds'][0]==solo['id'] and 'primary-working-identity:verified-solo' in refs[0]['roles'])
check('source and counterpart remain alongside solo',source['id'] in scope['assetIds'] and partner['id'] in scope['assetIds'])
check('package self_test',business.self_test())
atomic_json(DATA/'reports/cast-reference-input-proof.json',{'checks':checks,'fixture':str(root),'scope':'Isolated fixture; no model thread or generation claimed'})
print(json.dumps({'passed':len(checks),'report':'reports/cast-reference-input-proof.json'}))
