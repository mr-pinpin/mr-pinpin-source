"""Trusted host environment only; no child/project configuration is consumed."""
import importlib.util,os,pathlib,sys,types,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Error(Exception):
 def __init__(self,*args):self.args=args
class HostConfiguration(unittest.TestCase):
 def setUp(self):
  self.pkg='qa_registry';pkg=types.ModuleType(self.pkg);pkg.__path__=[]
  self.modules={self.pkg:pkg,'model':types.SimpleNamespace(StudioError=Error)}
  for name in ['capability_adapters','book_capabilities','location_capabilities','compact_sheet','location_media']:
   self.modules[self.pkg+'.'+name]=types.SimpleNamespace(business_capabilities=lambda:[],business_dispatch=lambda *args:'ok')
  self.modules[self.pkg+'.locations']=types.SimpleNamespace(LocationAdapter=lambda *args,**kwargs:(args,kwargs))
  self.modules[self.pkg+'.location_capabilities'].BoundedLocationService=lambda *args:args
  self.mock=patch.dict(sys.modules,self.modules);self.mock.start()
  spec=importlib.util.spec_from_file_location(self.pkg+'.registry',ROOT/'business/capability_registry.py');self.registry=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.registry)
 def tearDown(self):self.mock.stop()
 def invoke(self,store,body=None):return self.registry.business_dispatch(store,'location.query.v1',body or {},{'businessHash':'abc'})
 def test_environment_configures_service(self):
  env={'STUDIO_LOCATION_SOURCE_ROOT':'/source','STUDIO_LOCATION_INDEX_PATH':'/index','STUDIO_LOCATION_PYTHON_PATH':'/python','STUDIO_LOCATION_OUTPUT_ROOT':'/output','STUDIO_LOCATION_CACHE_ROOT':'/cache'}
  with patch.dict(os.environ,env,clear=True):
   store=types.SimpleNamespace();self.assertEqual(self.invoke(store),'ok');self.assertEqual(store.location_capability_service[1:],('/output','/cache'))
 def test_incomplete_environment_refused(self):
  with patch.dict(os.environ,{'STUDIO_LOCATION_SOURCE_ROOT':'/source'},clear=True):
   with self.assertRaises(Error):self.invoke(types.SimpleNamespace())
 def test_relative_environment_refused(self):
  with patch.dict(os.environ,{'STUDIO_LOCATION_SOURCE_ROOT':'relative'},clear=True):
   with self.assertRaises(Error):self.invoke(types.SimpleNamespace())
 def test_no_configuration_is_not_invented(self):
  with patch.dict(os.environ,{},clear=True):
   store=types.SimpleNamespace();self.invoke(store,{'sourceRoot':'/child'});self.assertFalse(hasattr(store,'location_capability_service'))
 def test_attribute_overrides_environment(self):
  store=types.SimpleNamespace(location_capability_configuration={'sourceRoot':'/trusted','indexPath':'/index','pythonPath':'/python','outputRoot':'/out'})
  with patch.dict(os.environ,{'STUDIO_LOCATION_SOURCE_ROOT':'relative'},clear=True):self.invoke(store)
  self.assertEqual(store.location_capability_service[0][0][0],'/trusted')
 def test_relative_cache_refused(self):
  store=types.SimpleNamespace(location_capability_configuration={'sourceRoot':'/s','indexPath':'/i','pythonPath':'/p','outputRoot':'/o','cacheRoot':'relative'})
  with self.assertRaises(Error):self.invoke(store)
if __name__=='__main__':unittest.main()
