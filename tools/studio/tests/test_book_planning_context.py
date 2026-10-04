import importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('book_context',Path(__file__).resolve().parents[1]/'business/book_context.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_large_history(self):
  moments=[{'id':'moment-'+str(i),'chapterId':'chapter-1','intent':'x'*120,'category':'setup','estimatedSeconds':2,'castIds':['c'+str(j) for j in range(32)],'dependsOn':[],'shotIds':['shot-'+str(i)]} for i in range(4096)]
  version={'version':100,'sha256':'a'*64,'spec':{'brief':'b'*16000,'arc':'a'*16000,'moments':moments,'chapterIntents':[{'chapterId':'chapter-1','intent':'i'*4000}],'links':[]},'referenceBindings':[]}
  history=[dict(version,version=i) for i in range(1,101)]
  project={'book':{'title':'preserved','studioBookPlan':{'currentVersion':100,'versions':history}}}
  single_version_bytes=len(json.dumps(version,separators=(',',':')).encode());out=m.planning_context(project,'chapter-1',['shot-215'],42);encoded=len(json.dumps(out,separators=(',',':')).encode())
  self.assertLess(encoded,16384);self.assertEqual(out['selectedMoments'][0]['id'],'moment-215');self.assertNotIn('versions',out);self.assertEqual(out['version'],100);self.assertEqual(out['projectRevision'],42);self.assertEqual(project['book']['title'],'preserved')
  print(json.dumps({'singleVersionBytes':single_version_bytes,'logicalRepeatedVersionBytesEstimate':single_version_bytes*100,'projectedBookPlanBytes':encoded,'moments':4096,'historicalVersions':100,'selectedScene':'shot-215','test':'projection; full context integration not live-tested'}))
 def test_empty(self):self.assertIsNone(m.planning_context({'book':{}}))
if __name__=='__main__':unittest.main()
