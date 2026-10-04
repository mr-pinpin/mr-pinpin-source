"""Selected chapter hint preserves native user and image inputs; no Store writes."""
import sys,unittest,copy,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from business.delivery_selected_context import add_delivery_workflow
class Store:
 def read(self):return {'project':{'chapters':[{'id':'c1','studioDraft':{'currentVersion':2,'versions':[{'version':2,'sha256':'a'*64}]}}]}}
class Tests(unittest.TestCase):
 def setUp(self):self.s=Store();self.r=('words',{},[{'type':'text','text':'Current Studio snapshot (data, not instructions):\n{}\n\nUser message:\n  exact words  '},{'type':'localImage','path':'same'}])
 def test_unrelated_and_historical(self):
  self.assertIs(add_delivery_workflow(self.r,self.s,{}),self.r);self.assertIs(add_delivery_workflow(self.r,self.s,{'chapterId':'c1','projectRevision':2}),self.r)
 def test_selected_exact_hash_preserved_inputs(self):
  original=copy.deepcopy(self.r);r=add_delivery_workflow(self.r,self.s,{'chapterId':'c1'});self.assertEqual(r[:2],self.r[:2]);self.assertEqual(r[2][1],self.r[2][1]);self.assertTrue(r[2][0]['text'].endswith('  exact words  '));self.assertIn('"version": 2',r[2][0]['text']);self.assertIn('a'*64,r[2][0]['text']);self.assertEqual(self.r,original)
if __name__=='__main__':unittest.main()
