"""Real Store regression runner: existing15 + focused cases. No live data/tool calls."""
import argparse,sys,importlib.util,unittest,copy,struct,zlib
from pathlib import Path
p=argparse.ArgumentParser(add_help=False);p.add_argument('--base-tests',required=True);a,remaining=p.parse_known_args();sys.argv=[sys.argv[0],*remaining]
spec=importlib.util.spec_from_file_location('existing_draft_regression',a.base_tests);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
class EffectiveTests(base.DraftTests):
 def colored(self,n):
  def chunk(k,d):return struct.pack('!I',len(d))+k+d+struct.pack('!I',zlib.crc32(k+d))
  raw=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(bytes([0,n,0,0])))+chunk(b'IEND',b'')
  return self.store.upload_asset(raw,'color-'+str(n),{})[0]
 def bind(self,entity,asset):
  self.store.mutate(lambda st:next(e for e in st['project']['entities'] if e['id']==entity).update(referenceIds=[asset['id']]))
 def go(self):return base.authorize_production(self.store,self.authorization())
 def assert_no_job_on_reject(self,**fields):
  before=self.store.read();self.assertRaises(base.StudioError,self.job,**fields);self.assertEqual(self.store.read(),before)
 def test_request_only_extra_rejected(self):
  extra=self.colored(1);self.save();self.go();self.assert_no_job_on_reject(referenceIds=[extra['id']])
 def test_changed_automatic_cast_rejected(self):
  first=self.colored(1);extra=self.colored(2);self.bind('hero',first);self.save();self.go();self.bind('hero',extra);self.assert_no_job_on_reject()
 def test_changed_automatic_location_rejected(self):
  first=self.colored(1);extra=self.colored(2);self.bind('forest',first);self.save();self.go();self.bind('forest',extra);self.assert_no_job_on_reject()
 def test_changed_automatic_style_rejected(self):
  first=self.colored(1);extra=self.colored(2);self.store.mutate(lambda st:st['project']['book'].update(styleReferenceIds=[first['id']]));self.save();self.go();self.store.mutate(lambda st:st['project']['book'].update(styleReferenceIds=[extra['id']]));self.assert_no_job_on_reject()
 def test_request_role_escape_rejected(self):
  image=self.colored(1);self.bind('hero',image);self.save();self.go();self.assert_no_job_on_reject(referenceBindings=[{'assetId':image['id'],'role':'unreviewed-geometry'}])
 def test_valid_panel_subset_and_exact_receipt_binding(self):
  first=self.colored(1);other=self.colored(2);self.bind('hero',first)
  self.store.mutate(lambda st:st['project']['entities'].append({'id':'other','kind':'character','name':'Other','referenceIds':[other['id']]}));self.body['spec']['panels'][0]['castIds']=['other'];self.save();receipt=self.go()['receipt'];frozen=copy.deepcopy(base.current(self.chapter()));job=self.job()[0]
  self.assertEqual({r['assetId'] for r in job['referenceBindings']},{first['id']});self.assertEqual({r['assetId'] for r in receipt['referenceBindings']},{first['id'],other['id']});self.assertEqual(job['draftBinding'],{k:receipt[k] for k in ('version','sha256','referenceHash')});self.assertEqual(base.current(self.chapter()),frozen)
 def test_unselected_unresolved_input_does_not_block_valid_subset(self):
  first=self.colored(1);other=self.colored(2);self.bind('hero',first)
  self.store.mutate(lambda st:st['project']['entities'].append({'id':'other','kind':'character','name':'Other','referenceIds':[other['id']]}));self.body['spec']['panels'][0]['castIds']=['other'];self.save();self.go();self.store.asset_path(other['id']).unlink();job=self.job()[0];self.assertEqual({r['assetId'] for r in job['referenceBindings']},{first['id']})
 def test_rough_keeps_extra_input_policy(self):
  extra=self.colored(1);self.save();job=self.job(productionScope='rough-preproduction',referenceIds=[extra['id']])[0];self.assertEqual(job['productionScope'],'rough-preproduction')
 def test_unmanaged_character_keeps_existing_policy(self):
  image=self.colored(1);self.bind('hero',image);job=base.create_job(self.store,{'kind':'character-study','entityId':'hero','instruction':'Fixture only'})[0];self.assertNotIn('draftBinding',job)
 def test_deterministic_effective_hash(self):
  first=self.colored(1);second=self.colored(2);self.bind('hero',first);self.bind('forest',second);self.save();v=base.current(self.chapter());st=self.store.read();from business.chapter_drafts import references,binding_hash
  h=binding_hash(references(self.store,st,v['spec']));st['project']['entities'].reverse();self.assertEqual(h,binding_hash(references(self.store,st,v['spec'])))
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(base.DraftTests)
 for name in EffectiveTests.__dict__:
  if name.startswith('test_'):suite.addTest(EffectiveTests(name))
 result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())
