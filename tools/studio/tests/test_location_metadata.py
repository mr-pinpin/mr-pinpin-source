import sys,types,importlib.util,tempfile,os,json,unittest,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1];EXAMPLES=REPO/'workflows/examples/location-viewer'
sys.path.insert(0,str(ROOT))
from model import StudioError as Error
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('qa_location_archive',ROOT/'media_library.py');archive=importlib.util.module_from_spec(spec);spec.loader.exec_module(archive)
pkg=types.ModuleType('_qa_location_metadata');pkg.__path__=[str(ROOT/'business')]
caps=types.ModuleType('_qa_location_metadata.capability_adapters');caps.ident=lambda:{'type':'id','maxLength':160};caps.descriptor=lambda *a,**k:(a,k)
spec=importlib.util.spec_from_file_location('_qa_location_metadata.location_media',ROOT/'business/location_media.py');loc=importlib.util.module_from_spec(spec)
with patch.dict(sys.modules,{'media_library':archive,pkg.__name__:pkg,caps.__name__:caps}):spec.loader.exec_module(loc)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.old=os.environ.get('PINPIN_MEDIA_CACHE_ROOT');os.environ['PINPIN_MEDIA_CACHE_ROOT']=str(self.root);self.addCleanup(self.restore)
  for f in ['media-registry.json','location-manifest.json']:shutil.copy(EXAMPLES/f,self.root/f)
 def restore(self):
  if self.old is None:os.environ.pop('PINPIN_MEDIA_CACHE_ROOT',None)
  else:os.environ['PINPIN_MEDIA_CACHE_ROOT']=self.old
 def test_safe_metadata_no_media_reads(self):
  old=archive.media_file;archive.media_file=lambda *a:(_ for _ in ()).throw(AssertionError('Media read forbidden in metadata'))
  try:value=loc.selection_metadata('tractor-orbit-scrub-v1')
  finally:archive.media_file=old
  self.assertEqual(value['manifest']['stops'][0]['actualTimestampSeconds'],5.625);self.assertFalse(value['mediaBytesVerified']);self.assertEqual(len(value['registry']),3);self.assertFalse(any('path' in row for row in value['registry'].values()))
 def test_unknown(self):self.assertRaises(Error,loc.selection_metadata,'unregistered')
 def test_manifest_hash(self):
  f=self.root/'location-manifest.json';v=json.loads(f.read_text());v['stops'][0]['camera']['fov']=10;f.write_text(json.dumps(v));self.assertRaises(Error,loc.selection_metadata)
 def test_oversize(self): (self.root/'location-manifest.json').write_text(' '*32769);self.assertRaises(Error,loc.selection_metadata)
 def test_manifest_symlink(self):
  f=self.root/'location-manifest.json';f.unlink();f.symlink_to(EXAMPLES/'location-manifest.json');self.assertRaises(Error,loc.selection_metadata)
 def test_historical_denied(self):self.assertRaises(Error,loc.business_dispatch,None,'spaces.location.get.v1',{'mediaId':'tractor-orbit-scrub-v1'},{'readOnly':True,'deadlineMonotonic':time.monotonic()+5})
 def test_deadline(self):self.assertRaises(Error,loc.business_dispatch,None,'spaces.location.get.v1',{'mediaId':'tractor-orbit-scrub-v1'},{'readOnly':False,'deadlineMonotonic':0})
if __name__=='__main__':unittest.main(verbosity=2)
