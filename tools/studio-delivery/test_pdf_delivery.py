import base64,hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
class Error(Exception):
 def __init__(self,message,*a):super().__init__(message)
module=types.ModuleType('model');module.StudioError=Error
with patch.dict(sys.modules,{'model':module}):
 helper=Path(__file__).with_name('draft_pdf_delivery.py')
 if not helper.exists():helper=Path(__file__).resolve().parents[1]/'studio/business/draft_pdf_delivery.py'
 spec=importlib.util.spec_from_file_location('pdf_delivery',helper);delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
class PDFDeliveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'deliveries').mkdir();self.bytes=b'%PDF-fixture-only\n'+b'x'*100000;self.pdf=self.root/'deliveries/fixture.pdf';self.pdf.write_bytes(self.bytes);self.sha=hashlib.sha256(self.bytes).hexdigest();self.version='a'*64;self.entry={'chapterId':'fixture','version':2,'sourceVersionSHA256':self.version,'language':'ru','artifactSHA256':self.sha,'storagePath':'fixture.pdf','bytes':len(self.bytes)};self.catalog=self.root/'deliveries/catalog.json';self.save();self.store=types.SimpleNamespace(root=self.root,read=lambda:{'project':{'chapters':[{'id':'fixture','studioDraft':{'versions':[{'version':2,'sha256':self.version}]}}]}});self.request={k:self.entry[k] for k in ('chapterId','version','sourceVersionSHA256','language','artifactSHA256')};self.request['offset']=0
 def save(self):self.catalog.write_text(json.dumps({'deliveries':[self.entry]}))
 def test_chunks_bound_and_integrity(self):
  parts=[]
  for offset in (0,65536):
   r=delivery.chunk(self.store,dict(self.request,offset=offset));parts.append(base64.b64decode(r['base64']));self.assertLessEqual(len(json.dumps(r).encode()),96*1024)
  self.assertEqual(b''.join(parts),self.bytes);self.assertTrue(r['done'])
 def test_wrong_version_sha_refused(self):
  with self.assertRaises(Error):delivery.chunk(self.store,dict(self.request,sourceVersionSHA256='b'*64))
 def test_client_path_refused(self):
  with self.assertRaises(Error):delivery.chunk(self.store,dict(self.request,path='/private'))
 def test_registered_escape_refused(self):
  self.entry['storagePath']='../private.pdf';self.save()
  with self.assertRaises(Error):delivery.chunk(self.store,self.request)
 def test_corruption_refused(self):
  self.pdf.write_bytes(b'%PDF-'+b'y'*(len(self.bytes)-5))
  with self.assertRaises(Error):delivery.chunk(self.store,self.request)
 def test_no_implicit_generation_or_registration(self):
  before=self.catalog.read_bytes();delivery.chunk(self.store,self.request);self.assertEqual(self.catalog.read_bytes(),before);self.assertEqual(self.pdf.read_bytes(),self.bytes)
 def test_bad_offset_refused(self):
  for offset in (-1,1,True,len(self.bytes)):
   with self.assertRaises(Error):delivery.chunk(self.store,dict(self.request,offset=offset))
 def test_corrupt_catalog_is_expected_error(self):
  self.catalog.write_text('bad json')
  with self.assertRaises(Error):delivery.chunk(self.store,self.request)
if __name__=='__main__':unittest.main()
