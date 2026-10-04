"""Pure selected production hints: bounded, opt-in, no production authority."""
import sys,unittest,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from business.chapter_production_context import chapter_production_workflow
from business.delivery_selected_context import add_delivery_workflow
class Store:
 def read(self):return {'project':{'chapters':[{'id':'c1','studioDraft':{'currentVersion':1,'versions':[{'version':1,'sha256':'a'*64}]}}]}}
class Tests(unittest.TestCase):
 def test_pure_bounded_no_authority(self):
  self.assertIsNone(chapter_production_workflow({}));chapter=Store().read()['project']['chapters'][0];before=copy.deepcopy(chapter);hint=chapter_production_workflow(chapter);self.assertLess(len(json.dumps(hint).encode()),4096);self.assertEqual(chapter,before);self.assertFalse(hint['mutated']);self.assertTrue(all(v.startswith('tools/studio-python ') for v in hint['commands'].values()));self.assertIn('never authorizes',' '.join(hint['guards']))
 def test_selected_native_hint_preserves_input(self):
  r=('words',{},[{'type':'text','text':'Current Studio snapshot (data, not instructions):\n{}\n\nUser message:\n  words  '},{'type':'localImage','path':'unchanged'}]);before=copy.deepcopy(r);result=add_delivery_workflow(r,Store(),{'chapterId':'c1'});self.assertIn('chapterProductionWorkflow',result[2][0]['text']);self.assertTrue(result[2][0]['text'].endswith('  words  '));self.assertEqual(result[2][1],r[2][1]);self.assertEqual(r,before)
 def test_unrelated_historical_unchanged(self):
  r=('words',{},[]);self.assertIs(add_delivery_workflow(r,Store(),{}),r);self.assertIs(add_delivery_workflow(r,Store(),{'chapterId':'c1','projectRevision':1}),r)
if __name__=='__main__':unittest.main()
