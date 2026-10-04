import sys,json,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[3];sys.path.insert(0,str(BASE/'tools/studio'))
from business import asset_storage as mod
from model import StudioError
class View:
 def __init__(self,root):self.root=root
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.store=View(self.root);self.calls=[]
 def tearDown(self):self.tmp.cleanup()
 def entry(self,store,key,cfg):return {'id':key,'url':'/api/assets/'+key},self.root/(key+'.png'),{'sha256':'a'*64,'bytes':100}
 def test_metadata_never_resolves(self):
  with patch.object(mod,'policy',return_value={}),patch.object(mod,'asset_entry',side_effect=self.entry),patch.object(mod,'resolve',side_effect=AssertionError('No restore on paint')):
   r=mod.hydrate_selected(self.store,['asset-good']);self.assertFalse(r['networkAllowed']);self.assertEqual(r['missingBytes'],100)
 def test_over_budget_prevents_transfer(self):
  with patch.object(mod,'policy',return_value={}),patch.object(mod,'asset_entry',side_effect=self.entry),patch.object(mod,'resolve',side_effect=AssertionError()):
   with self.assertRaises(StudioError):mod.hydrate_selected(self.store,['asset-good'],restore=True,byte_budget=99)
 def test_missing_remote_is_pending(self):
  with patch.object(mod,'policy',return_value={}),patch.object(mod,'asset_entry',side_effect=self.entry),patch.object(mod,'resolve',side_effect=StudioError('offline')):
   r=mod.hydrate_selected(self.store,['asset-good'],restore=True);self.assertEqual(r['results'][0]['status'],'pending');self.assertEqual(r['remoteBackupStatus'],'unverified')
 def test_timeout_remains_bounded(self):
  def resolve(store,key,**kw):self.calls.append(kw['timeout_seconds']);return {'assetId':key}
  with patch.object(mod,'policy',return_value={}),patch.object(mod,'asset_entry',side_effect=self.entry),patch.object(mod,'resolve',side_effect=resolve):
   r=mod.hydrate_selected(self.store,['asset-good'],restore=True,timeout_seconds=1);self.assertGreater(self.calls[0],0);self.assertLessEqual(self.calls[0],1)
 def test_request_count(self):
  with self.assertRaises(StudioError):mod.hydrate_selected(self.store,['a']*5)
 def test_duplicate(self):
  with self.assertRaises(StudioError):mod.hydrate_selected(self.store,['a','a'])
 def test_oversized_budget(self):
  with self.assertRaises(StudioError):mod.hydrate_selected(self.store,['a'],byte_budget=67108865)
if __name__=='__main__':unittest.main()
