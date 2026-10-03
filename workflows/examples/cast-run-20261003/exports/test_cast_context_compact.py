"""Fresh-process byte measurements and selected/resume/historical isolation checks."""
import importlib.util,io,json,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
D=Path(__file__).resolve().parents[1]
R=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime')
deployment=json.loads((R/'current-deployment.json').read_text())
sys.path.insert(0,str(R/'stable-releases'/deployment['stableRelease']))
from store import Store,atomic_json
from PIL import Image
def load_business(path):
 spec=importlib.util.spec_from_file_location('compact_business',path/'__init__.py',submodule_search_locations=[str(path)])
 module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module
def probe(root,source,live=False):
 b=load_business(source);store=Store(root)
 if not live:assert not (root/'conversation.json').exists()
 results={}
 subject='migrating-bird-family' if live else 'subject'
 for label,body in {'selected':{'text':'Inspect this character','entityId':subject},'resume':{'text':'continue the cast'}}.items():
  _,scope,inputs=b.selected_context(store,body)
  snap=json.loads(inputs[0]['text'].split('\n',1)[1].split('\n\nUser message:')[0])
  results[label]={'textBytes':len(inputs[0]['text'].encode()),'castBytes':len(json.dumps(snap['castWorkflow'],ensure_ascii=False).encode()),'scope':scope,'snapshot':snap}
 from compact_business import context
 with patch.object(context,'workflow_context',side_effect=AssertionError('historical live import')):
  _,scope,inputs=b.selected_context(store,{'text':'continue the cast','entityId':subject,'projectRevision':store.read()['revision']})
  results['historical']={'readOnly':scope['reviewSnapshot'],'noMutableCast':'castWorkflow' not in inputs[0]['text'],'noToolchain':'registrationToolchain' not in inputs[0]['text']}
 results['selfTest']=bool(b.self_test());return results
if len(sys.argv)>1 and sys.argv[1] in ('probe','liveprobe'):
 print(json.dumps(probe(Path(sys.argv[2]),Path(sys.argv[3]),live=sys.argv[1]=='liveprobe')));sys.exit(0)
if len(sys.argv)>1 and sys.argv[1]=='prepare':
 root=Path(tempfile.mkdtemp(prefix='cast-compact-',dir=D/'reports'));store=Store(root)
 (root/'workflows').mkdir();(root/'reports/character-packages').mkdir(parents=True)
 for filename in ('character-creation.md','cast-run.md'):(root/'workflows'/filename).write_bytes((D/'workflows'/filename).read_bytes())
 assets=[]
 for color in ('red','green','blue'):
  raw=io.BytesIO();Image.new('RGB',(4,4),color).save(raw,format='PNG');assets.append(store.upload_asset(raw.getvalue(),color,{'source':'deterministic test fixture','prompt':'fixture prompt '*200})[0])
 rows=[];state=store.read();p=state['project'];p['entities']=[]
 bindings={}
 for i in range(21):
  identifier='subject' if i==0 else 'other-'+str(i)
  folder=root/'workflows/characters'/identifier;folder.mkdir(parents=True)
  marker='SELECTED_DOSSIER' if i==0 else 'UNRELATED_DOSSIER_'+str(i)
  (folder/'README.md').write_text(marker+'; exact age not stated; young squirrel fixture.\n'+'Curated source/proposal evidence. '*50)
  atomic_json(folder/'evidence.json',{'bibliography':[{'chapterId':'fixture','excerpt':'Species squirrel; exact age not stated'}]})
  p['entities'].append({'id':identifier,'name':identifier,'kind':'character','identity':'Squirrel fixture; proposed portrait','referenceIds':[assets[0]['id']]})
  bindings[identifier]={'speciesAndRole':'Squirrel fixture','designBasis':'Source text fixture, proposed portrait. '*20,'sourceReferences':[{'assetId':assets[0]['id'],'sha256':assets[0]['sha256'],'role':'identity'}],'counterpartIds':[]}
  rows.append({'id':identifier,'canonicalName':identifier,'exactAge':'not stated','evidencedLifeStage':'young squirrel fixture','aliases':[],'status':'produced','dossierPath':'workflows/characters/'+identifier+'/README.md','evidencePath':'workflows/characters/'+identifier+'/evidence.json','outputs':[]})
  stages={'solo':{'candidates':[{'entityId':identifier,'stage':'solo','assetId':assets[1]['id'],'sha256':assets[1]['sha256']}]}}
  if i:stages['interactions']={'candidates':[{'entityId':identifier,'stage':'interactions','assetId':assets[2]['id'],'sha256':assets[2]['sha256']}]}
  atomic_json(root/'reports/character-packages'/(identifier+'.json'),{'entityId':identifier,'stages':stages})
 p['book']['styleReferenceIds']=[assets[2]['id']];p['book']['characterReferenceDefaults']={'schemaVersion':1,'layoutReference':{'assetId':assets[1]['id'],'sha256':assets[1]['sha256']},'characters':bindings}
 store.save_project(p,state['revision']);atomic_json(root/'workflows/cast-run.json',{'schemaVersion':1,'characters':rows})
 source=R/'business-builds'/json.loads((R/'business-state.json').read_text())['active']
 before=json.loads(subprocess.check_output([sys.executable,'-B',__file__,'probe',str(root),str(source)],text=True))
 atomic_json(D/'reports/cast-context-before.json',{'fixture':str(root),'businessPath':str(source),'requests':before})
 print(json.dumps({'fixture':str(root),'before':{k:{x:v[x] for x in ('textBytes','castBytes')} for k,v in before.items() if k in ('selected','resume')}}));sys.exit(0)
before=json.loads((D/'reports/cast-context-before.json').read_text());root=Path(before['fixture'])
source=R/'business-builds'/json.loads((R/'business-state.json').read_text())['active']
after=json.loads(subprocess.check_output([sys.executable,'-B',__file__,'probe',str(root),str(source)],text=True))
checks=[]
def check(name,ok):assert ok,name;checks.append({'test':name,'passed':True})
measurements={}
for label in ('selected','resume'):
 old=before['requests'][label];new=after[label];snap=new['snapshot'];run=snap['castWorkflow']
 check(label+' exact same selection and native refs',old['scope']==new['scope'])
 check(label+' source age identity and partial stage retained',snap['characterContext']['character']['exactAge']=='not stated' and run['selected']['nextStage']=='interactions' and 'SELECTED_DOSSIER' in run['dossier']['text'])
 check(label+' unrelated dossiers and bindings omitted','UNRELATED_DOSSIER' not in json.dumps(snap) and set(snap['book']['characterReferenceDefaults']['characters'])=={'subject'})
 check(label+' guide hash/pointer and exact reference roles retained',run['guide']['sha256']==old['snapshot']['castWorkflow']['guide']['sha256'] and 'sections' in run['guide'] and snap['characterContext']['references']==old['snapshot']['characterContext']['references'])
 check(label+' concise queue still resumes exact missing stage',run['remaining']==['subject'] and len(run['characters'])==21)
 check(label+' text bytes decreased',new['textBytes']<old['textBytes'])
 measurements[label]={'beforeTextBytes':old['textBytes'],'afterTextBytes':new['textBytes'],'beforeCastBytes':old['castBytes'],'afterCastBytes':new['castBytes'],'savedBytes':old['textBytes']-new['textBytes']}
check('historical explicit selection never imports mutable cast/toolchain',all(after['historical'].values()))
check('package self_test',after['selfTest'])
live={}
for phase,path in [('before',before['businessPath']),('after',str(source))]:
 live[phase]=json.loads(subprocess.check_output([sys.executable,'-B',__file__,'liveprobe',str(D),path],text=True))
live_measurements={}
for label in ('selected','resume'):
 old=live['before'][label];new=live['after'][label]
 check('live '+label+' scope and role-labelled references unchanged',old['scope']==new['scope'] and old['snapshot'].get('characterContext',{}).get('references')==new['snapshot'].get('characterContext',{}).get('references'))
 live_measurements[label]={'beforeTextBytes':old['textBytes'],'afterTextBytes':new['textBytes'],'savedBytes':old['textBytes']-new['textBytes'],'selectedEntity':new['scope']['entityId']}
check('live repaired bird solo is current primary',live['after']['selected']['snapshot']['characterContext']['references'][0]['id']==json.loads((D/'reports/character-packages/migrating-bird-family.json').read_text())['stages']['solo']['candidates'][-1]['assetId'])
check('live complete queue remains empty',live['after']['resume']['snapshot']['castWorkflow']['remaining']==[])
atomic_json(D/'reports/cast-context-compact-proof.json',{'checks':checks,'measurements':measurements,'liveEquivalentRequests':live_measurements,'fixture':str(root),'beforeBusiness':before['businessPath'],'afterBusiness':str(source),'freshProcesses':True,'modelThreadReset':False,'limit':'UTF-8 text bytes, not token counts, compute savings or a native compaction fix'})
print(json.dumps({'passed':len(checks),'measurements':measurements,'liveEquivalentRequests':live_measurements}))
