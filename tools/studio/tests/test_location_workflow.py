"""Real Store scoped location preparation; providers/network never invoked."""
import sys,tempfile,unittest,json,io,copy,importlib.util
from pathlib import Path
from unittest.mock import patch
STUDIO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(STUDIO))
from store import Store
from model import StudioError
from PIL import Image
from business import location_workflow as w,location_context as c
class Service:
 def __init__(self,digest):self.digest=digest;self.calls=[]
 def query(self,**kwargs):
  self.calls.append(kwargs);return {'location':{'id':'house'},'media':[{'sha256':self.digest,'path':'existing.png','roles':['location-identity']}],'indexProvenance':{'fixture':'metadata'}}
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(self.tmp.name)
  def upload(color):
   buf=io.BytesIO();Image.new('RGB',(4,2),color).save(buf,format='PNG');return self.store.upload_asset(buf.getvalue(),color+'.png',{},'unreviewed')[0]
  self.a=upload('red');self.b=upload('blue');self.store.location_capability_service=Service(self.b['sha256'])
  self.body={'location':'house','expectedRevision':self.store.read()['revision'],'request':'  User requested new location study  ','prompt':'  Exact submitted spherical prompt  ','references':[{'assetId':a['id'],'sha256':a['sha256'],'role':role} for a,role in [(self.a,'seamless-panorama'),(self.b,'location-identity'),(self.b,'book-style')]],'camera':{'intention':'User chosen eye height','yawDegrees':0,'pitchDegrees':0,'fovDegrees':90},'formatReview':{'assetId':self.a['id'],'sha256':self.a['sha256'],'projection':'pass','seam':'pass','poles':'pass','evidence':'Fixture explicit visual observation'}}
  self.cfg={'maxAssetBytes':33554432}
  self.policy=patch.object(w.asset_storage,'policy',return_value=self.cfg);self.policy.start();self.addCleanup(self.policy.stop)
  self.remote=patch.object(w.asset_storage,'resolve',side_effect=AssertionError('No remote-capable resolve'));self.remote.start();self.addCleanup(self.remote.stop)
 def run_prepare(self):return w.prepare(self.store,self.body)
 def test_exact_prompt_no_project_mutation(self):
  old=self.store.read();r=self.run_prepare();self.assertEqual(r['status'],'prepared');self.assertEqual((self.store.root/r['promptFile']).read_bytes(),self.body['prompt'].encode());self.assertEqual(self.store.read(),old);self.assertFalse(r['generationDispatched']);self.assertEqual(len(r['toolRequest']['referenced_image_paths']),2)
 def test_idempotent(self):self.assertEqual(self.run_prepare(),self.run_prepare())
 def test_stale_revision(self):self.body['expectedRevision']-=1;self.assertRaises(StudioError,self.run_prepare)
 def test_missing_bytes_pending_no_files(self):
  (self.store.root/self.b['storagePath']).unlink();r=self.run_prepare();self.assertEqual(r['status'],'pending-restore');self.assertFalse((self.store.root/'reports/location-workflow').exists())
 def test_corrupt_bytes(self):(self.store.root/self.b['storagePath']).write_bytes(b'bad');self.assertRaises(StudioError,self.run_prepare)
 def test_changed_hash(self):self.body['references'][1]['sha256']='0'*64;self.assertRaises(StudioError,self.run_prepare)
 def test_missing_style(self):self.body['references'].pop();self.assertRaises(StudioError,self.run_prepare)
 def test_optional_geometry_not_required(self):self.assertNotIn('geometry-underlay',[r['role'] for r in self.run_prepare()['references']])
 def test_format_must_differ(self):self.body['references'][1]=dict(self.body['references'][0],role='location-identity');self.assertRaises(StudioError,self.run_prepare)
 def test_review_exact_hash(self):self.body['formatReview']['sha256']='0'*64;self.assertRaises(StudioError,self.run_prepare)
 def test_failed_visual_review(self):self.body['formatReview']['seam']='fail';self.assertRaises(StudioError,self.run_prepare)
 def test_target_catalog_binding(self):self.store.location_capability_service.digest='0'*64;self.assertRaises(StudioError,self.run_prepare)
 def test_camera_nonfinite(self):self.body['camera']['fovDegrees']=float('nan');self.assertRaises((StudioError,ValueError),self.run_prepare)
 def test_arbitrary_field(self):self.body['outputPath']='/tmp/arbitrary';self.assertRaises(StudioError,self.run_prepare)
 def test_metadata_context_no_policy(self):
  self.policy.stop();r=c.location_context(self.store,'house');self.assertEqual(r['selection']['references'][0]['availability'],'metadata-only');self.assertFalse(self.store.location_capability_service.calls[-1]['network'])
 def test_active_runtime_cli_context(self):
  from business_runtime import BusinessRuntime
  runtime=BusinessRuntime(STUDIO/'business',Path(self.tmp.name)/'runtime',watch=False);self.addCleanup(runtime.close);self.assertIsNotNone(runtime.active)
  spec=importlib.util.spec_from_file_location('location_cli',STUDIO.parent/'location_ops.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
  result=cli.execute(self.store,runtime,'context',selectors={'location':'house'});self.assertEqual(result['projectRevision'],self.store.read()['revision']);self.assertFalse(result['generationDispatched'])
  self.assertRaises(StudioError,cli.execute,self.store,runtime,'generate')
 def test_route_fixed(self):
  self.assertIsNone(w.cli_location_route(self.store,'POST','/api/other',{},{}));self.assertRaises(StudioError,w.cli_location_route,self.store,'POST','/api/location-workflow/context',{},{});self.assertEqual(w.cli_location_route(self.store,'GET','/api/location-workflow/context',{},None)[0],200)
if __name__=='__main__':unittest.main()
