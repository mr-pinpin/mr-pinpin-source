"""Spaces registry integration only; actual media/browser acceptance belongs to w3/root."""
import pathlib,sys,tempfile,time,types,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from business_runtime import BusinessRuntime
from model import StudioError
class RegistrySpaces(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.runtime=BusinessRuntime(ROOT/'business',self.tmp.name,watch=False);self.assertIsNotNone(self.runtime.active)
 def tearDown(self):self.runtime.close();self.tmp.cleanup()
 def test_thirteen_registered_operations_preserve_draft_sheet_and_spaces(self):
  operations=self.runtime.capabilities()['operations'];self.assertEqual(len(operations),13);ids={x['id'] for x in operations}
  self.assertTrue({'draft.sheet.bind.v1','draft.sheet.get.v1','draft.patch.v1','spaces.location.get.v1'}<=ids)
  op=next(x for x in operations if x['id']=='spaces.location.get.v1');self.assertEqual(op['effect'],'read');self.assertEqual(op['maxResponseBytes'],65536);self.assertEqual(op['timeoutMs'],10000)
 def test_registry_delegates_exact_body_context_to_author_module(self):
  module=sys.modules[self.runtime.active.name+'.location_media'];module.archive=types.SimpleNamespace(media_entries=lambda:None);seen=[];module.business_dispatch=lambda *args:seen.append(args) or {'delegated':True}
  body={'mediaId':'selected'};context={'revision':1,'readOnly':False,'businessHash':self.runtime.active.sha,'deadlineMonotonic':time.monotonic()+1}
  result=self.runtime.active.module.business_dispatch(None,'spaces.location.get.v1',body,context)
  self.assertTrue(result['delegated']);self.assertIs(seen[0][2],body);self.assertIs(seen[0][3],context)
 def test_old_media_artifact_fails_closed_without_business_rollback(self):
  module=sys.modules[self.runtime.active.name+'.location_media'];module.archive=types.SimpleNamespace()
  with self.assertRaises(StudioError) as exc:self.runtime.active.module.business_dispatch(None,'spaces.location.get.v1',{'mediaId':'selected'},{'readOnly':False,'deadlineMonotonic':time.monotonic()+1})
  self.assertEqual(exc.exception.status,503);self.assertIsNotNone(self.runtime.active)
 def test_historical_spaces_refusal_kept(self):
  sys.modules[self.runtime.active.name+'.location_media'].archive=types.SimpleNamespace(media_entries=lambda:None)
  with self.assertRaises(StudioError):self.runtime.active.module.business_dispatch(None,'spaces.location.get.v1',{'mediaId':'selected'},{'readOnly':True,'deadlineMonotonic':time.monotonic()+1})
if __name__=='__main__':unittest.main()
