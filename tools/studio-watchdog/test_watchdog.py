import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('wd',Path(__file__).with_name('watchdog.py'));wd=importlib.util.module_from_spec(spec);spec.loader.exec_module(wd)
class Checks(unittest.TestCase):
 def run_case(self,mode,fail=False,response=None):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
   root=Path(tmp);action={'id':'one','text':'fixture only','coordinatorApproved':True,'threadId':'t','expectedCursor':7,'reserveUSD':2};(root/'queued-action.json').write_text(json.dumps(action));calls=[]
   def cli(args):
    calls.append(args)
    if 'send' in args:
     self.assertEqual(json.loads((root/'checkpoint.json').read_text())['reservedUSD'],2)
     if fail:raise RuntimeError('uncertain')
     return response if response is not None else {'id':'studio','accepted':True,'messageId':'fixture-message','turnId':'fixture-turn','acceptedAt':'fixture-time'}
    return {'status':'completed','threadId':'t','cursor':7}
   c={'deadlineEpoch':100,'approvedThread':'t','mode':mode,'python':'fixture','client':'fixture','url':'fixture'}
   with patch.object(wd,'invoke',side_effect=cli),patch.object(wd.time,'time',return_value=1):wd.tick(c,root);wd.tick(c,root)
   return calls,json.loads((root/'checkpoint.json').read_text())
 def test_duplicate_not_sent_twice(self):
  calls,s=self.run_case('coordinator-queue');self.assertEqual(sum('send' in x for x in calls),1);self.assertEqual(s['reservedUSD'],2)
 def test_uncertain_never_retries(self):
  calls,s=self.run_case('coordinator-queue',True);self.assertEqual(sum('send' in x for x in calls),1);self.assertEqual(s['claims']['one']['status'],'uncertain-no-retry')
 def test_read_only_never_dispatches(self):
  calls,s=self.run_case('read-only');self.assertFalse(any('send' in x for x in calls));self.assertEqual(s['reservedUSD'],0)
 def test_receipt_identity_and_positive_acceptance(self):
  _,s=self.run_case('coordinator-queue');claim=s['claims']['one'];self.assertEqual(claim['messageId'],'fixture-message');self.assertEqual(claim['turnId'],'fixture-turn');self.assertEqual(claim['acceptedAt'],'fixture-time')
  for accepted in (False,None,1,'true'):
   _,s=self.run_case('coordinator-queue',response={'id':'studio','accepted':accepted});self.assertEqual(s['claims']['one']['status'],'uncertain-no-retry')
 def test_config_thread_and_exact_boolean_approvals(self):
  c={'deadlineEpoch':100,'approvedThread':'t'};state={'claims':{},'spentUSD':0,'reservedUSD':0};status={'status':'completed','threadId':'t','cursor':7};action={'id':'a','text':'fixture','coordinatorApproved':True,'threadId':'t','expectedCursor':7,'reserveUSD':0}
  self.assertEqual(wd.decision(status,1,dict(c,approvedThread='other'),action,state),'config-thread-refused')
  for value in (1,'true',[],None,False):
   self.assertEqual(wd.decision(status,1,c,dict(action,coordinatorApproved=value),state),'unapproved-or-wrong-thread')
   self.assertEqual(wd.decision(status,1,c,dict(action,fullProduction=True,explicitProductionApproval=value),state),'scope-approval-required')
 def test_nonfinite_negative_and_boolean_money(self):
  c={'deadlineEpoch':100,'approvedThread':'t'};state={'claims':{},'spentUSD':0,'reservedUSD':0};status={'status':'completed','threadId':'t','cursor':7};action={'id':'a','text':'fixture','coordinatorApproved':True,'threadId':'t','expectedCursor':7,'reserveUSD':0}
  for key in ('reserveUSD','reservedUSD','spentUSD'):
   for value in (True,False,float('nan'),float('inf'),float('-inf'),-1,None,'0'):
    a=dict(action);s=dict(state)
    if key=='reserveUSD':a[key]=value
    else:s[key]=value
    self.assertEqual(wd.decision(status,1,c,a,s),'budget-refused')
 def test_observation_error_durable_and_sanitized(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
   root=Path(tmp);wd.observation_error(root,{'mode':'read-only'},RuntimeError('private error body'));d=json.loads((root/'checkpoint.json').read_text());self.assertEqual(d['latest']['decision'],'observation-error');self.assertNotIn('private error body',(root/'ticks.jsonl').read_text())
if __name__=='__main__':unittest.main()
