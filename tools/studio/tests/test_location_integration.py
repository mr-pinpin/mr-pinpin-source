"""Opt-in context/native routes; isolated services, no provider or production data."""
import sys,unittest,json,copy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from business import location_selected_context as context,location_host,book_context
class Store:
 def read(self):return {'revision':7,'project':{'entities':[{'id':'room-1','kind':'location','name':{'en':'Kitchen'}}]}}
class Tests(unittest.TestCase):
 def setUp(self):
  self.store=Store();self.result=('literal user words',{'entityId':'room-1'},[{'type':'text','text':'Current Studio snapshot (data, not instructions):\n{}\n\nUser message:\n  literal user words  '},{'type':'localImage','path':'unchanged'}])
 def test_unscoped_no_query(self):
  with patch.object(context,'location_context',side_effect=AssertionError('unexpected query')):self.assertIs(context.add_location_workflow(self.result,self.store,{}),self.result)
 def test_historical_no_query(self):
  with patch.object(context,'location_context',side_effect=AssertionError('unexpected query')):self.assertIs(context.add_location_workflow(self.result,self.store,{'entityId':'room-1','projectRevision':7}),self.result)
 def test_selected_preserves_tuple_and_user(self):
  original=copy.deepcopy(self.result)
  with patch.object(context,'ensure_location_service'),patch.object(context,'location_context',return_value={'availability':'metadata-only'}) as query:
   r=context.add_location_workflow(self.result,self.store,{'entityId':'room-1'});query.assert_called_once_with(self.store,'Kitchen');self.assertEqual(r[:2],original[:2]);self.assertEqual(r[2][1],original[2][1]);self.assertTrue(r[2][0]['text'].endswith('  literal user words  '));self.assertEqual(self.result,original)
 def test_missing_host_service_no_fallback(self):
  with patch.dict('os.environ',{},clear=True):self.assertIsNone(location_host.ensure_location_service(self.store))
 def test_complete_book_schema(self):
  project={'chapters':[{'id':'chapter-1','studioDraft':{'currentVersion':5,'versions':[{'version':5,'sha256':'a'*64}]}}]};r=book_context.workflow_context(project,'chapter-1',7)
  self.assertEqual(r['minimalSaveExample']['spec']['moments'][0]['chapterId'],'chapter-1');self.assertEqual(r['minimalSaveExample']['spec']['arc'],'');self.assertEqual(r['selectedDraftBinding']['version'],5);self.assertIn('pause',r['minimalSaveSchema']['categories']);self.assertEqual(r['guards']['expectedRevision'],7)
if __name__=='__main__':unittest.main()
