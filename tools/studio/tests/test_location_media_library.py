import unittest,tempfile,sys,types,json,hashlib,os,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from model import StudioError as Error
spec=importlib.util.spec_from_file_location('qa_media_library',ROOT/'media_library.py');media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.previous=os.environ.get('PINPIN_MEDIA_CACHE_ROOT');os.environ['PINPIN_MEDIA_CACHE_ROOT']=str(self.root);self.addCleanup(self.restore);self.raw=b'\x89PNG\r\n\x1a\nfixture';(self.root/'image.png').write_bytes(self.raw);self.row={'path':'image.png','mime':'image/png','sha256':hashlib.sha256(self.raw).hexdigest(),'bytes':len(self.raw)};self.write()
 def restore(self):
  if self.previous is None:os.environ.pop('PINPIN_MEDIA_CACHE_ROOT',None)
  else:os.environ['PINPIN_MEDIA_CACHE_ROOT']=self.previous
 def write(self): (self.root/'media-registry.json').write_text(json.dumps({'schemaVersion':1,'files':{'stop-07':self.row}}))
 def test_local_registry(self):self.assertEqual(media.media_file('stop-07')[1],'image/png');self.assertIn('tractor-orbit-scrub-v1',media.media_entries()[1])
 def test_unknown_id(self):self.assertRaises(Error,media.media_file,'/etc/passwd')
 def test_traversal(self):self.row['path']='../image.png';self.write();self.assertRaises(Error,media.media_file,'stop-07')
 def test_absolute(self):self.row['path']='/tmp/image.png';self.write();self.assertRaises(Error,media.media_file,'stop-07')
 def test_url(self):self.row['path']='https://example/image.png';self.write();self.assertRaises(Error,media.media_file,'stop-07')
 def test_symlink(self): (self.root/'link.png').symlink_to(self.root/'image.png');self.row['path']='link.png';self.write();self.assertRaises(Error,media.media_file,'stop-07')
 def test_hash_corruption(self):media.media_file('stop-07');(self.root/'image.png').write_bytes(self.raw[:-1]+b'X');self.assertRaises(Error,media.media_file,'stop-07')
 def test_size(self):self.row['bytes']+=1;self.write();self.assertRaises(Error,media.media_file,'stop-07')
 def test_mime_forgery(self):self.row['mime']='video/mp4';self.write();self.assertRaises(Error,media.media_file,'stop-07')
 def test_magic(self):raw=b'fake png';(self.root/'image.png').write_bytes(raw);self.row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());self.write();self.assertRaises(Error,media.media_file,'stop-07')
 def test_video_import_rejected(self):
  raw=b'\x00\x00\x00\x18ftypisomfixture';(self.root/'video.mp4').write_bytes(raw);self.row.update(path='video.mp4',mime='video/mp4',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());self.write()
  spec=importlib.util.spec_from_file_location('business_media',ROOT/'business/media_library.py');module=importlib.util.module_from_spec(spec);from unittest.mock import patch
  with patch.dict(sys.modules,{'media_library':media}):spec.loader.exec_module(module)
  self.assertEqual(media.media_file('stop-07')[1],'video/mp4');self.assertRaises(Error,module.import_media,object(),'stop-07')
 def test_legacy_identity_change(self):self.row['sha256']='a'*64;(self.root/'media-registry.json').write_text(json.dumps({'schemaVersion':1,'files':{'tractor-orbit-scrub-v1':self.row}}));self.assertRaises(Error,media.media_entries)
if __name__=='__main__':unittest.main(verbosity=2)
