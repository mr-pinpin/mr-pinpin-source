"""Real isolated Store: sheet binding does not alter narrative/reference/approval."""
import copy,hashlib,io,pathlib,sys,tempfile,time,unittest
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from store import Store
from business_runtime import BusinessRuntime
from model import StudioError
class CompactSheet(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.store=Store(self.root/'data')
  image=Image.new('RGB',(4,4),'white');raw=io.BytesIO();image.save(raw,format='PNG');self.asset,state=self.store.upload_asset(raw.getvalue(),'safe-fixture.png')
  p=state['project'];p['entities']=[{'id':'pinpin','kind':'character','name':'Fixture','referenceIds':[self.asset['id']]},{'id':'place','kind':'location','name':'Fixture','referenceIds':[]}];state=self.store.save_project(p,state['revision'])
  self.runtime=BusinessRuntime(ROOT/'business',self.root/'runtime',watch=False);self.assertIsNotNone(self.runtime.active)
  self.core=sys.modules[self.runtime.active.name+'.chapter_drafts'];self.sheets=sys.modules[self.runtime.active.name+'.compact_sheet']
  panel={'action':'Watch','cause':'Leaf falls','effect':'Rests','caption':'Hmm…','camera':'Close-up','beat':'setup','seconds':5,'castIds':['pinpin'],'previewKind':'schematic-placeholder'}
  spec={'title':'Fixture','synopsis':'','referenceIds':[self.asset['id']],'location':{'baseEntityId':'place','description':'Field','proposed':False},'panels':[dict(panel,id='p1'),dict(panel,id='p2')]}
  v=self.core.save_draft(self.store,{'chapterId':'chapter','baseVersion':0,'expectedRevision':state['revision'],'spec':spec})
  self.body={'chapterId':'chapter','sourceVersion':1,'sourceVersionSHA256':v['sha256'],'assetId':self.asset['id'],'assetSHA256':self.asset['sha256'],'panelIds':['p1','p2'],'columns':2,'rows':1,'promptSHA256':'a'*64,'receiptSHA256':'b'*64,'expectedRevision':v['revision']}
 def tearDown(self):self.runtime.close();self.tmp.cleanup()
 def call(self,body=None,readonly=False):
  return self.sheets.business_dispatch(self.store,'draft.sheet.bind.v1',body or self.body,{'revision':self.store.read()['revision'],'readOnly':readonly})
 def test_binds_one_page_without_core_or_approval_mutation(self):
  before=self.store.read()['project']['chapters'][0]['studioDraft'];result=self.call();after=self.store.read()['project']['chapters'][0]
  self.assertEqual(after['studioDraft'],before);self.assertEqual(len(after['studioDraftPreviews']),1);self.assertFalse(result['artworkCreated']);self.assertFalse(result['productionAuthorized'])
 def test_order_refused(self):
  with self.assertRaises(StudioError):self.call(dict(self.body,panelIds=['p2','p1']))
 def test_duplicate_panels_refused(self):
  with self.assertRaises(StudioError):self.call(dict(self.body,panelIds=['p1','p1']))
 def test_unknown_panels_refused(self):
  with self.assertRaises(StudioError):self.call(dict(self.body,panelIds=['p1','missing']))
 def test_grid_mismatch_refused(self):
  with self.assertRaises(StudioError):self.call(dict(self.body,rows=2))
 def test_wrong_source_hash_refused(self):
  with self.assertRaises(StudioError):self.call(dict(self.body,sourceVersionSHA256='c'*64))
 def test_wrong_asset_hash_refused(self):
  with self.assertRaises(StudioError):self.call(dict(self.body,assetSHA256='c'*64))
 def test_corrupt_bytes_refused(self):
  self.store.asset_path(self.asset['id']).write_bytes(b'corrupt')
  with self.assertRaises(StudioError):self.call()
 def test_readonly_refused(self):
  with self.assertRaises(StudioError):self.call(readonly=True)
 def test_stale_revision_refused(self):
  with self.assertRaises(StudioError):self.call(dict(self.body,expectedRevision=0))
 def test_revision_retains_and_marks_old_sheet_stale(self):
  self.call();state=self.store.read();before=state['project']['chapters'][0]['studioDraft'];v=before['versions'][-1]
  self.core.patch_draft(self.store,{'chapterId':'chapter','baseVersion':1,'baseSHA256':v['sha256'],'expectedRevision':state['revision'],'patches':[{'panelId':'p1','fields':{'caption':'Changed'}}]})
  state=self.store.read();chapter=state['project']['chapters'][0];view=self.sheets.sheet_views(chapter,state['assets']);self.assertEqual(len(view),1);self.assertTrue(view[0]['stale']);self.assertEqual(chapter['studioDraft']['currentVersion'],2)
 def test_duplicate_binding_refused(self):
  self.call();self.body['expectedRevision']=self.store.read()['revision']
  with self.assertRaises(StudioError):self.call()
 def test_cumulative_metadata_bound_refused(self):
  state=self.store.read();state['project']['chapters'][0]['studioDraftPreviews']=[{'note':'x'*(512*1024)}];state=self.store.save_project(state['project'],state['revision']);self.body['expectedRevision']=state['revision']
  with self.assertRaises(StudioError):self.call()
 def test_prompt_provenance_not_claimed_verified(self):
  self.assertEqual(self.call()['sheet']['provenanceStatus'],'caller-declared-prompt-and-receipt-digests')
if __name__=='__main__':unittest.main()
