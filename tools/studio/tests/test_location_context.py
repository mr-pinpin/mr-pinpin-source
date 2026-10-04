"""Bounded projection/schema checks, no image generation/storage resolution."""
import sys,json,unittest,types,importlib.util,copy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]/'business'
pkg=types.ModuleType('location_context_fixture');pkg.__path__=[str(ROOT)];sys.modules[pkg.__name__]=pkg
spec=importlib.util.spec_from_file_location(pkg.__name__+'.location_context',ROOT/'location_context.py');c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
worker=types.ModuleType(pkg.__name__+'.location_workflow');sys.modules[worker.__name__]=worker
class Tests(unittest.TestCase):
 def setUp(self):
  self.state={'revision':7,'assets':[{'id':'format','sha256':'a'*64},{'id':'target','sha256':'b'*64},{'id':'unrelated','sha256':'c'*64}]};self.store=types.SimpleNamespace(read=lambda:self.state)
  self.catalog={'location':{'id':'house'},'media':[{'path':'target.png','sha256':'b'*64,'bytes':4,'roles':['location-identity'],'approval':'existing-evidence'}],'indexProvenance':{'indexSHA256':'d'*64}}
  self.calls=[]
  def catalog(store,location):self.calls.append(location);return self.catalog
  worker.catalog=catalog
 def context(self,**kw):return c.location_context(self.store,'house',**kw)
 def test_complete_minimal_schema(self):
  s=self.context()['prepareSchema'];self.assertEqual(set(s['required']),{'location','expectedRevision','request','prompt','references','camera','formatReview'});self.assertEqual(s['properties']['references']['items']['properties']['role']['enum'],c.ROLES);self.assertFalse(s['additionalProperties'])
 def test_template_guard_and_actual_roles(self):
  r=self.context(selected_references={'seamless-panorama':'format','location-identity':'target','book-style':'target'});t=r['prepareEnvelopeTemplate'];self.assertEqual(t['expectedRevision'],7);self.assertEqual(t['references'][0]['sha256'],'a'*64);self.assertNotEqual(t['references'][0]['assetId'],t['references'][1]['assetId']);self.assertEqual(t['references'][1]['assetId'],t['references'][2]['assetId']);self.assertIn('ACTUAL_VIEWER',t['formatReview']['evidence'])
 def test_catalog_never_claims_health_or_bytes(self):
  r=self.context();self.assertEqual(r['selection']['references'][0]['availability'],'metadata-only');self.assertEqual(r['selection']['references'][0]['registeredAssetId'],'target');self.assertIn('SELECT_',r['prepareEnvelopeTemplate']['references'][0]['assetId']);self.assertFalse(r['generationDispatched'])
 def test_large_metadata_bound(self):
  self.catalog['media']=[dict(self.catalog['media'][0],path='x'*50000,roles=['y'*50000]*30,approval={'huge':'z'*50000}) for _ in range(4096)];self.catalog['indexProvenance']={'huge':'z'*100000};r=self.context();self.assertLessEqual(len(json.dumps(r,ensure_ascii=False).encode()),24576);self.assertTrue(r['selection']['truncated']);self.assertEqual(len(r['selection']['references']),12)
 def test_no_all_location_asset_dump_or_mutation(self):
  before=copy.deepcopy(self.state);r=self.context();self.assertEqual(self.calls,['house']);self.assertNotIn('unrelated',json.dumps(r));self.assertEqual(self.state,before)
 def test_proposal_status_and_optional_geometry(self):
  r=self.context();self.assertEqual(r['provenanceExample']['status'],'proposed-variant-unreviewed');self.assertEqual(len(r['prepareEnvelopeTemplate']['references']),3);self.assertIn('Optional',r['referenceRoles']['geometry-underlay'])
 def test_no_selection_query_if_unspecified(self):r=c.location_context(self.store);self.assertEqual(self.calls,[]);self.assertNotIn('selection',r)
if __name__=='__main__':unittest.main()
