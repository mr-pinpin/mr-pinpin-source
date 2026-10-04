"""Portable real Store/active BusinessRuntime CLI-contract tests; no providers."""
import sys,json,tempfile,unittest,importlib.util,shutil,contextlib,io
from pathlib import Path
STUDIO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(STUDIO))
from store import Store
from model import StudioError
from business_runtime import BusinessRuntime
from release import freeze
spec=importlib.util.spec_from_file_location('book_cli',STUDIO.parent/'book_plan_ops.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(Path(self.tmp.name)/'data');state=self.store.read();project=state['project'];project['chapters']=[{'id':'c1','title':{'en':'Existing chapter'},'script':'','synopsis':'','scenes':[]}];state=self.store.save_project(project,state['revision']);self.runtime=BusinessRuntime(STUDIO/'business',Path(self.tmp.name)/'runtime',watch=False)
  self.addCleanup(self.runtime.close);self.assertIsNotNone(self.runtime.active)
  self.body={'baseVersion':0,'expectedRevision':state['revision'],'request':'  Literal user words: Herculean comic; no new story.  ','spec':{'brief':'  Exact editable user book intent  ','arc':'User-declared arc','chapterIntents':[{'chapterId':'c1','intent':'Exact chapter intent'}],'moments':[{'id':'m1','chapterId':'c1','intent':'User setup','category':'setup','estimatedSeconds':2,'castIds':[],'dependsOn':[]},{'id':'m2','chapterId':'c1','intent':'User payoff','category':'payoff','estimatedSeconds':None,'castIds':[],'dependsOn':['m1']}],'links':[{'id':'l1','from':'m1','to':'m2','kind':'setup-payoff','resolved':True,'explanation':'Exact user cause/effect'}]}}
 def save(self):return cli.execute(self.store,self.runtime,'save',payload=self.body)
 def context(self,**selectors):return cli.execute(self.store,self.runtime,'context',selectors=selectors)
 def patch(self):
  view=self.context()['plan'];return {'baseVersion':view['version'],'baseSHA256':view['sha256'],'expectedRevision':self.store.read()['revision'],'request':'Exact selected revision','patches':[{'momentId':'m2','fields':{'intent':'User changed payoff','estimatedSeconds':4}}]}
 def test_first_context(self):
  result=self.context();self.assertFalse(result['plan']['ready']);self.assertEqual(result['workflow']['actualChapterIds'],['c1']);self.assertEqual(result['workflow']['guards']['baseVersion'],0);self.assertIn('tools/studio-python',result['workflow']['helper']);self.assertEqual(self.store.read()['jobs'],[])
 def test_literal_request_and_intent(self):
  self.save();version=self.store.read()['project']['book']['studioBookPlan']['versions'][0];self.assertEqual(version['request'],self.body['request']);self.assertEqual(version['spec']['brief'],self.body['spec']['brief']);self.assertFalse(version['productionStarted'])
 def test_context_saved_tempo_dag(self):
  self.save();result=self.context(chapterId='c1');self.assertEqual(result['plan']['links'][0]['explanation'],'Exact user cause/effect');self.assertEqual(result['tempo']['knownEstimatedSeconds'],2);self.assertIsNone(result['tempo']['estimatedTotalSeconds']);self.assertEqual(result['plan']['sha256'],result['tempo']['bookPlanSHA256'])
 def test_guarded_patch(self):
  self.save();before=self.store.read()['project']['book']['studioBookPlan']['versions'][0];result=cli.execute(self.store,self.runtime,'patch',payload=self.patch());self.assertEqual(result['version'],2);self.assertEqual(self.store.read()['project']['book']['studioBookPlan']['versions'][0],before);self.assertEqual(self.context()['tempo']['estimatedTotalSeconds'],6)
 def test_missing_guards(self):self.assertRaises(StudioError,cli.execute,self.store,self.runtime,'save',payload={'spec':self.body['spec'],'request':'x'})
 def test_stale_revision(self):
  self.save();payload=self.patch();payload['expectedRevision']-=1;before=self.store.read();self.assertRaises(StudioError,cli.execute,self.store,self.runtime,'patch',payload=payload);self.assertEqual(self.store.read(),before)
 def test_stale_version_hash(self):
  self.save();payload=self.patch();payload['baseSHA256']='a'*64;before=self.store.read();self.assertRaises(StudioError,cli.execute,self.store,self.runtime,'patch',payload=payload);self.assertEqual(self.store.read(),before)
 def test_unknown_moment(self):
  self.save();payload=self.patch();payload['patches'][0]['momentId']='not-saved';self.assertRaises(StudioError,cli.execute,self.store,self.runtime,'patch',payload=payload)
 def test_no_production_fields(self):
  self.save();payload=self.patch();payload['patches'][0]['fields']={'productionStarted':True};self.assertRaises(StudioError,cli.execute,self.store,self.runtime,'patch',payload=payload);self.assertEqual(self.store.read()['jobs'],[])
 def test_historical_context(self):
  self.save();cli.execute(self.store,self.runtime,'patch',payload=self.patch());result=self.context(version=1);self.assertTrue(result['readOnly']);self.assertEqual(result['plan']['version'],1)
 def test_operation_allowlist(self):self.assertRaises(StudioError,cli.execute,self.store,self.runtime,'authorize',payload={})
 def test_workflow_hint_without_plan(self):
  module=sys.modules[self.runtime.active.name+'.book_context'];hint=module.planning_context(self.store.read()['project'],'c1',revision=self.store.read()['revision']);self.assertFalse(hint['ready']);self.assertEqual(hint['workflow']['guards']['baseVersion'],0);self.assertEqual(hint['workflow']['actualChapterIds'],['c1']);self.assertIn('save <book-plan-envelope.json>',hint['workflow']['save'])
 def test_main_verified_deployment_context_save_patch(self):
  # Freeze the unchanged real kernel into external fixture runtime; never serving.
  runtime_dir=Path(self.tmp.name)/'runtime';receipt=freeze(STUDIO,runtime_dir)
  (runtime_dir/'current-deployment.json').write_text(json.dumps({'stableRelease':receipt['stableRelease']}))
  envelope=Path(self.tmp.name)/'request.json';envelope.write_text(json.dumps(self.body,ensure_ascii=False))
  prefix=['--data-dir',str(self.store.root),'--runtime-dir',str(runtime_dir)]
  out=io.StringIO()
  with contextlib.redirect_stdout(out):self.assertEqual(cli.main(prefix+['save',str(envelope)]),0)
  saved=json.loads(out.getvalue());out=io.StringIO()
  with contextlib.redirect_stdout(out):self.assertEqual(cli.main(prefix+['context','--chapter','c1']),0)
  current=json.loads(out.getvalue());self.assertEqual(current['plan']['version'],saved['version']);self.assertEqual(current['plan']['brief'],self.body['spec']['brief'])
  out=io.StringIO()
  with contextlib.redirect_stdout(out):self.assertEqual(cli.main(prefix+['patch','--moment','m2','--fields','{"estimatedSeconds":4}','--version',str(current['plan']['version']),'--sha256',current['plan']['sha256'],'--expected-revision',str(current['revision']),'--request','Exact user request']),0)
  self.assertEqual(json.loads(out.getvalue())['version'],2);self.assertEqual(self.store.read()['jobs'],[])
if __name__=='__main__':unittest.main(verbosity=2)
