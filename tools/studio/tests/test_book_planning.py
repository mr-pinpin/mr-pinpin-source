"""Actual local Store planning fixtures, no content/model/image/video calls."""
import sys,importlib.util,copy,tempfile,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from store import Store
from model import StudioError
package=type(sys)('planning_fixture');package.__path__=[str(ROOT/'business')];sys.modules['planning_fixture']=package
from planning_fixture import book_plans as b,tempo
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=Store(self.tmp.name);st=self.s.read();p=st['project'];p['entities']=[{'id':'hero','kind':'character','name':'Fixture','referenceIds':[]}];p['chapters']=[{'id':'c1','title':{'en':'Fixture chapter'},'script':'','synopsis':'','scenes':[]}];self.s.save_project(p,st['revision'])
  self.body={'baseVersion':0,'expectedRevision':self.s.read()['revision'],'request':'Literal user fixture intent','spec':{'brief':'Herculean comic intent remains editable','arc':'User-declared arc fixture','chapterIntents':[{'chapterId':'c1','intent':'Existing chapter intent'}],'moments':[{'id':'m'+str(i),'chapterId':'c1','sequenceId':'s1','intent':'Moment '+str(i),'category':'setup' if i==0 else 'payoff' if i==9 else 'repetition','estimatedSeconds':i+1,'castIds':['hero'],'dependsOn':['m'+str(i-1)] if i else []} for i in range(10)],'links':[{'id':'l1','from':'m0','to':'m9','kind':'setup-payoff','resolved':True,'explanation':'User-planned mapping'}]}}
 def save(self):return b.save_plan(self.s,self.body)
 def project(self):return self.s.read()['project']
 def test_persistence_no_calls(self):
  self.save();v=b.current(Store(self.tmp.name).read()['project']);self.assertEqual(v['spec']['brief'],self.body['spec']['brief']);self.assertEqual(v['request'],self.body['request']);self.assertEqual(v['generationCalls'],0);self.assertFalse(v['productionStarted']);self.assertEqual(self.s.read()['jobs'],[])
 def test_stale_revision(self):
  self.body['expectedRevision']=0;self.assertRaises(StudioError,self.save)
 def test_stale_version_hash(self):
  self.save();self.body.update(expectedRevision=self.s.read()['revision']);self.assertRaises(StudioError,self.save)
 def test_immutable_history_patch(self):
  self.save();old=copy.deepcopy(b.current(self.project()));v=old;r=b.patch_plan(self.s,{'baseVersion':1,'baseSHA256':v['sha256'],'expectedRevision':self.s.read()['revision'],'patches':[{'momentId':'m3','fields':{'estimatedSeconds':7,'intent':'User revised fixture'}}],'request':'Actual edited fields'});versions=self.project()['book']['studioBookPlan']['versions'];self.assertEqual(versions[0],old);self.assertEqual(r['version'],2)
 def test_historical_cannot_save(self):
  self.body['reviewSnapshot']=True;self.assertRaises(StudioError,self.save)
 def test_unknown_chapter(self):
  self.body['spec']['moments'][0]['chapterId']='missing';self.assertRaises(StudioError,self.save)
 def test_duplicate_moment(self):
  self.body['spec']['moments'][1]['id']='m0';self.assertRaises(StudioError,self.save)
 def test_dependency_cycle(self):
  self.body['spec']['moments'][0]['dependsOn']=['m9'];self.assertRaises(StudioError,self.save)
 def test_causal_link_cycle(self):
  self.body['spec']['links'].append({'id':'l2','from':'m9','to':'m0','kind':'cause-effect','resolved':True,'explanation':'Cycle'});self.assertRaises(StudioError,self.save)
 def test_unresolved_link_visible(self):
  self.body['spec']['links'].append({'id':'missing','from':'m2','to':'future','kind':'cause-effect','resolved':False,'explanation':'Unresolved user intention'});self.save();t=tempo.tempo_summary(self.project());self.assertEqual(t['unresolvedLinkCount'],1)
 def test_setup_payoff_categories(self):
  self.body['spec']['links'][0]['from']='m2';self.assertRaises(StudioError,self.save)
 def test_long_chapter_coarse_overview(self):
  self.body['spec']['moments']=[dict(self.body['spec']['moments'][1],id='m'+str(i),dependsOn=[]) for i in range(215)];self.body['spec']['links']=[];self.save();v=b.view_plan(self.project(),page=17);self.assertEqual(len(v['moments']),11);self.assertEqual(len(v['overview']),10);self.assertEqual(v['overview'][0]['id'],'m0');self.assertEqual(v['overview'][-1]['id'],'m214');self.assertEqual(v['totalMoments'],215)
 def test_4096_bounded_chart(self):
  self.body['spec']['moments']=[dict(self.body['spec']['moments'][1],id='m'+str(i),dependsOn=[]) for i in range(4096)];self.body['spec']['links']=[];self.save();self.assertLessEqual(len(tempo.tempo_summary(self.project())['bins']),120)
 def test_unknown_seconds_not_measured(self):
  self.body['spec']['moments'][0]['estimatedSeconds']=None;self.save();t=tempo.tempo_summary(self.project());self.assertIsNone(t['estimatedTotalSeconds']);self.assertEqual(t['knownEstimatedSeconds'],54);self.assertEqual(t['unknownMoments'],1)
 def test_heuristic_target_label(self):
  self.body['spec']['intendedTargetSeconds']=120;self.save();self.assertIn('heuristic',tempo.tempo_summary(self.project())['intendedTarget']['label'])
 def test_bad_seconds(self):
  for val in (True,float('nan'),-1):self.body['spec']['moments'][0]['estimatedSeconds']=val;self.assertRaises(StudioError,self.save)
 def test_cast_not_interaction_proof(self):
  self.save();t=tempo.tempo_summary(self.project());self.assertEqual(t['castParticipation'][0]['plannedMomentCount'],10);self.assertIn('does not prove interaction',t['castCaveat'])
 def test_requests_only(self):
  self.save()
  for kind in ('expand-sequence','compact-comic-page'):
   req=b.planning_request(self.project(),kind,['m1']);self.assertEqual(req['status'],'request-only');self.assertFalse(req['productionStarted'])
  self.assertEqual(self.s.read()['jobs'],[])
 def test_forbidden_patch(self):
  self.save();v=b.current(self.project());self.assertRaises(StudioError,b.patch_plan,self.s,{'baseVersion':1,'baseSHA256':v['sha256'],'expectedRevision':self.s.read()['revision'],'patches':[{'momentId':'m1','fields':{'approved':True}}]})
 def test_shot_references_actual(self):
  self.body['spec']['moments'][0]['shotIds']=['not-imported'];self.assertRaises(StudioError,self.save)
 def test_historical_view(self):
  self.save();old=b.current(self.project());self.body.update(baseVersion=1,baseSHA256=old['sha256'],expectedRevision=self.s.read()['revision']);self.body['spec']['arc']='User revised arc';self.save();self.assertTrue(b.view_plan(self.project(),version=1)['historical'])
 def test_historical_tempo_matches_view(self):
  self.save();old=b.current(self.project());self.body.update(baseVersion=1,baseSHA256=old['sha256'],expectedRevision=self.s.read()['revision']);self.body['spec']['moments'][0]['estimatedSeconds']=100;self.save();v=b.planning_view(self.s.read(),version=1);self.assertEqual(v['tempo']['estimatedTotalSeconds'],55);self.assertEqual(v['tempo']['bookPlanSHA256'],v['plan']['sha256'])
 def test_zoom_last_long_moment(self):
  self.body['spec']['moments']=[dict(self.body['spec']['moments'][1],id='m'+str(i),dependsOn=[]) for i in range(215)];self.body['spec']['links']=[];self.save();v=b.view_plan(self.project(),moment_id='m214');self.assertEqual(v['page'],17);self.assertIn('m214',[m['id'] for m in v['moments']])
 def test_unknown_shot_span_refused(self):
  self.body['spec']['moments'][0]['shotSpan']={'firstSceneId':'missing','lastSceneId':'missing'};self.assertRaises(StudioError,self.save)
 def test_unknown_catalog_reference_rejected(self):
  self.body['spec']['referenceIds']=['missing'];self.assertRaises(StudioError,self.save)
 def test_catalog_binding_snapshot_is_honest(self):
  self.s.mutate(lambda st:st['assets'].append({'id':'reference-fixture','sha256':'a'*64,'bytes':3,'provenance':{'role':'style'}}));self.body['spec']['referenceIds']=['reference-fixture'];self.body['expectedRevision']=self.s.read()['revision'];self.save();binding=b.current(self.project())['referenceBindings'][0];self.assertEqual(binding['sha256'],'a'*64);self.assertEqual(binding['role'],'style');self.assertEqual(binding['availability'],'catalog-only-not-byte-verified')
 def test_budget_rejection_preserves_revision_and_identity(self):
  self.save();prior=self.s.read();v=b.current(prior['project']);self.body.update(baseVersion=1,baseSHA256=v['sha256'],expectedRevision=prior['revision']);self.body['spec']['arc']='Valid revised intent'
  old=b.MAX_PLAN_HISTORY_BYTES;b.MAX_PLAN_HISTORY_BYTES=1
  try:self.assertRaises(StudioError,self.save)
  finally:b.MAX_PLAN_HISTORY_BYTES=old
  self.assertEqual(self.s.read(),prior)
 def test_unchanged_does_not_duplicate_text(self):
  self.save();prior=self.s.read();v=b.current(prior['project']);self.body.update(baseVersion=1,baseSHA256=v['sha256'],expectedRevision=prior['revision']);self.assertRaises(StudioError,self.save);self.assertEqual(self.s.read(),prior)
 def test_canonical_budget_utf8(self):
  value={'text':'é'*10};expected=len(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
  self.assertEqual(b.canonical_size(value,expected),expected);self.assertRaises(StudioError,b.canonical_size,value,expected-1)
if __name__=='__main__':unittest.main(verbosity=2)
