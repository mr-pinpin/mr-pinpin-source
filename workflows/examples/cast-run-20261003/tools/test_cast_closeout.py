"""Focused isolated closeout checks; no native generation or live mutations."""
import importlib.util,sys,tempfile,json,io
from pathlib import Path
from PIL import Image
D=Path(__file__).resolve().parents[1]
B=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/business')
K=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime/stable-releases/c9be233f9e18f6d480c8a5b7d50dff6384c9df2766510b5ef006b21ccec40c75')
sys.path.insert(0,str(K))
spec=importlib.util.spec_from_file_location('closeout_business',B/'__init__.py',submodule_search_locations=[str(B)])
business=importlib.util.module_from_spec(spec);sys.modules[spec.name]=business;spec.loader.exec_module(business)
from closeout_business.cast_inventory import record_package
from closeout_business.cast_workflow import reconcile_character
from store import Store,atomic_json
root=Path(tempfile.mkdtemp(prefix='cast-closeout-',dir=D/'reports'));store=Store(root)
folder=root/'workflows/characters/subject';folder.mkdir(parents=True);(root/'reports/character-packages').mkdir(parents=True)
(folder/'README.md').write_text('# Subject\nCurated source before.\n\n## Current package result\nOld generated result.\n\n## Curated interpretation\nRetain this source/proposal distinction.\n')
atomic_json(folder/'evidence.json',{'bibliography':[{'excerpt':'CURATED SOURCE'}],'inspectedVisualEvidence':[{'inspection':'ACTUAL PIXEL QA'}]})
assets=[]
for color in ('red','green'):
 out=io.BytesIO();Image.new('RGB',(4,4),color).save(out,format='PNG');assets.append(store.upload_asset(out.getvalue(),color,{'source':'deterministic test, not imagegen'})[0])
atomic_json(root/'workflows/cast-run.json',{'schemaVersion':1,'characters':[{'id':'subject','status':'pending','outputs':[]},{'id':'next','status':'pending','outputs':[]}]})
atomic_json(root/'reports/character-packages/subject.json',{'entityId':'subject','stages':{role:{'candidates':[{'entityId':'subject','stage':role,'assetId':asset['id'],'sha256':asset['sha256']}]} for role,asset in zip(('solo','interactions'),assets)}})
result=record_package(store,'subject',[a['id'] for a in assets],'Fixture visual QA','reports/character-packages/subject-generation.json')
checks=[]
def check(name,value):assert value,name;checks.append({'test':name,'passed':True})
text=(folder/'README.md').read_text(); evidence=json.loads((folder/'evidence.json').read_text())
check('curated dossier before and after generated result retained','Curated source before.' in text and 'Retain this source/proposal distinction.' in text)
check('curated bibliography and visual QA preserved',evidence['bibliography'][0]['excerpt']=='CURATED SOURCE' and evidence['inspectedVisualEvidence'][0]['inspection']=='ACTUAL PIXEL QA')
check('completion returns real receipt-derived stages and card',result['workflowCard']['assetIds']==[a['id'] for a in assets] and result['stages']['solo']['sha256']==assets[0]['sha256'])
check('next missing stage persisted',result['next']=='next' and result['remaining']==['next'])
receipt_path=root/'reports/character-packages/subject.json';candidate_receipts=json.loads(receipt_path.read_text());candidate_receipts['stages']['interactions']['candidates'][-1]['qaDisposition']='needs-repair';atomic_json(receipt_path,candidate_receipts)
check('agent-rejected render resumes missing interaction rather than completing',reconcile_character(store,store.read(),{'id':'subject'})['nextStage']=='interactions')
candidate_receipts['stages']['interactions']['candidates'][-1].pop('qaDisposition');atomic_json(receipt_path,candidate_receipts)
again=record_package(store,'subject',[a['id'] for a in assets],'Fixture visual QA','reports/character-packages/subject-generation.json')
check('repeat finish preserves curated section once',(folder/'README.md').read_text().count('Retain this source/proposal distinction.')==1)
image_path=store.asset_path(assets[1]['id']);retained_bytes=image_path.read_bytes();image_path.unlink()
try:record_package(store,'subject',[a['id'] for a in assets],'fixture')
except ValueError:check('missing real image still rejects completion',True)
else:raise AssertionError('missing image accepted')
image_path.write_bytes(retained_bytes)
ops_spec=importlib.util.spec_from_file_location('fixture_cast_ops',D/'tools/cast_ops.py')
ops=importlib.util.module_from_spec(ops_spec);ops_spec.loader.exec_module(ops);ops.DATA=root
(root/'tools').mkdir();(root/'tools/cast_ops.py').write_bytes((D/'tools/cast_ops.py').read_bytes());ops.__file__=str(root/'tools/cast_ops.py')
record={'entityId':'subject','calls':[{'generationBeforeUTC':'2026-10-03 10:00:00 UTC','generationAfterUTC':'2026-10-03 10:00:10 UTC','repair':False,'receipt':{'timing':{'registrationSeconds':0.25}}}], 'monetaryCost':None}
atomic_json(root/'reports/character-packages/subject-generation.json',record)
closed=ops.finish_records('subject',result)
check('finish coherently saves stage evidence and actual metrics',closed['metrics']['summedImageCallWindowSeconds']==10 and json.loads((folder/'generation.json').read_text())['finalStages']==result['stages'] and json.loads((folder/'evidence.json').read_text())['bibliography']==evidence['bibliography'])
(folder/'README.md').write_text('# Subject\nCurated source before.\n\n## Current package result\nOld final generated section.\n')
for retry in range(2):
 full=record_package(store,'subject',[a['id'] for a in assets],'Fixture visual QA','reports/character-packages/subject-generation.json')
 ops.finish_records('subject',full)
 text=(folder/'README.md').read_text()
 check('full finish retry '+str(retry+1)+' is idempotent without later curated heading',text.count('## Measured generation and decisions')==1 and text.count('<!-- cast-ops metrics begin -->')==1 and text.count('<!-- cast-ops metrics end -->')==1 and 'Curated source before.' in text)
(root/'exports').mkdir();(root/'workflows/character-creation.md').write_text('Fixture guide');(root/'workflows/toolchain.json').write_text('{}');(root/'workflows/cast-run.md').write_text('# Fixture contract\nCurated previous checkpoint.\n')
class Runtime:
 def invoke(self,*args):return business.route(*args[1:])
receipt=ops.checkpoint(Runtime(),store,'fixture',['subject'])
check('single checkpoint queue summary export and archived narrative',receipt['remaining']==['next'] and (root/'exports/cast-fixture-checkpoint-receipt.json').is_file() and 'Curated previous checkpoint.' in (root/'reports/cast-before-fixture-checkpoint.md').read_text())
check('package self_test',business.self_test())
atomic_json(D/'reports/cast-closeout-proof.json',{'checks':checks,'fixtureRoot':str(root),'scope':'Isolated registered deterministic pixels, no model thread or art calls'})
print(json.dumps({'passed':len(checks),'report':'reports/cast-closeout-proof.json'}))
