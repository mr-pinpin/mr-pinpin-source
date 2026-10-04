"""Real Store, immutable active runtime and runpy delivery CLI with fixture inputs."""
import sys,runpy,tempfile,unittest,json,hashlib,io,types,copy
from pathlib import Path
TOOLS=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TOOLS/'studio'))
from store import Store
from business_runtime import BusinessRuntime
from PIL import Image
cli=runpy.run_path(str(Path(__file__).with_name('cli.py')))
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.s=Store(self.root/'data')
  assets=[]
  for color in ('red','blue','green','white','black'):
   b=io.BytesIO();Image.new('RGB',(24,24),color).save(b,format='PNG');assets.append(self.s.upload_asset(b.getvalue(),color+'.png',{'kind':'provided-line-art' if color in ('green','white','black') else 'fixture'},'unreviewed')[0])
  spec={'title':{'en':'The leaf','ru':'Листочек'},'panels':[{'id':'p1','imageAssetId':assets[1]['id'],'captions':{'en':'Hmm…','ru':'Хм…'}}]};refs=[]
  fp=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
  refhash=fp(refs);sha=fp({'spec':spec,'referenceHash':refhash});v={'version':1,'spec':spec,'referenceBindings':refs,'referenceHash':refhash,'sha256':sha}
  st=self.s.read();p=st['project'];p['chapters']=[{'id':'c1','title':{'en':'The leaf'},'script':'','scenes':[],'studioDraft':{'currentVersion':1,'versions':[v]}}];self.s.save_project(p,st['revision'])
  self.runtime=BusinessRuntime(TOOLS/'studio/business',self.root/'runtime',watch=False);self.addCleanup(self.runtime.close);self.assertIsNotNone(self.runtime.active)
  self.args=types.SimpleNamespace(chapter='c1',version=1,sha256=sha,cover=assets[0]['id'],miniature=assets[1]['id'],coloring=[a['id'] for a in assets[2:]],out=str(self.root/'output'),allow_incomplete=False,render=False,translations=None)
 def test_two_language_real_runtime_build(self):
  before=self.s.read();r=cli['build'](self.s,self.runtime,self.args);self.assertEqual(self.s.read(),before);self.assertEqual(len(r['languages']),2);self.assertTrue(all(m['complete'] for m in r['languages']));self.assertTrue(all(m['savedReferenceBindingVerified'] for m in r['languages']));self.assertFalse(r['pdfBuilt'])
 def test_wrong_saved_hash(self):self.args.sha256='0'*64;self.assertRaises(Exception,cli['build'],self.s,self.runtime,self.args)
 def test_missing_selected_asset(self):self.args.miniature='absent';self.assertRaisesRegex(ValueError,'missing',cli['build'],self.s,self.runtime,self.args)
if __name__=='__main__':unittest.main()
