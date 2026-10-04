import hashlib,importlib.util,json,tempfile,unittest,zlib,struct
from pathlib import Path
spec=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('prepare.py'));delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
def png():
 def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',24,24,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\x80\xaa\x99'*24)*24))+chunk(b'IEND',b'')
class DeliveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'assets').mkdir();self.art=self.root/'assets/fixture.png';self.art.write_bytes(png());self.asset={'id':'fixture-art','storagePath':'assets/fixture.png','sha256':delivery.digest(png()),'bytes':len(png()),'mime':'image/png','reviewStatus':'synthetic-fixture','provenance':{'kind':'fixture','prompt':'private omitted'}};self.record={'version':2,'chapterId':'fixture','sha256':'fixture-spec-identity','spec':{'chapterId':'fixture','title':{'en':'The leaf','ru':'Листочек'},'coverAssetId':'fixture-art','panels':[{'id':'p7','imageAssetId':'fixture-art','captions':{'en':'Hmm…','ru':'Хм…'}}]}};self.save()
 def save(self):
  self.file=self.root/'record.json';self.file.write_text(json.dumps(self.record,ensure_ascii=False));self.sha=delivery.digest(self.file.read_bytes())
 def export(self,**changes):
  kw={'record_path':self.file,'record_sha':self.sha,'chapter':'fixture','version':2,'registry':[self.asset],'asset_root':self.root,'out':self.root/'out','lang':'en'};kw.update(changes);return delivery.prepare(**kw)
 def test_unicode_order_original_identity_and_no_production(self):
  original=self.art.read_bytes();m=self.export(lang='ru');self.assertEqual(m['panelOrder'],['p7']);self.assertIn('Хм…',(self.root/'out/preview.html').read_text());self.assertEqual(self.art.read_bytes(),original);self.assertEqual(m['pageCount'],5);self.assertFalse(m['productionApprovalInferred']);self.assertEqual(m['generationCalls'],0);self.assertNotIn('private omitted',json.dumps(m))
 def test_record_hash_mismatch(self):
  with self.assertRaisesRegex(ValueError,'SHA'):self.export(record_sha='0'*64)
 def test_version_mismatch(self):
  with self.assertRaisesRegex(ValueError,'version'):self.export(version=3)
 def test_missing_art_explicit_no_reference_replacement(self):
  self.record['spec']['panels'][0]['imageAssetId']='missing';self.record['spec']['referenceIds']=['fixture-art'];self.save();m=self.export();self.assertTrue(any(a['assetId']=='missing' for a in m['missingArtwork']));self.assertEqual(len(m['selectedArtwork']),1)
 def test_corrupt_art_refused(self):
  self.art.write_bytes(b'corrupt')
  with self.assertRaisesRegex(ValueError,'SHA'):self.export()
 def test_path_escape_refused(self):
  self.asset['storagePath']='../private.png'
  with self.assertRaisesRegex(ValueError,'forbidden'):self.export()
 def test_symlink_escape_refused(self):
  with tempfile.TemporaryDirectory() as outside:
   p=Path(outside)/'outside.png';p.write_bytes(png());self.art.unlink();self.art.symlink_to(p)
   with self.assertRaisesRegex(ValueError,'forbidden'):self.export()
 def test_coloring_slots_never_fabricate(self):
  m=self.export();self.assertEqual(m['coloringSlotCount'],3);self.assertEqual(sum(x['slot'].startswith('coloring-') for x in m['missingArtwork']),3);self.assertIn('not a generated coloring page',(self.root/'out/preview.html').read_text())
 def test_coloring_cannot_relabel_story_art(self):
  with self.assertRaisesRegex(ValueError,'line art'):self.export(coloring=['fixture-art'])
 def test_no_cover_fallback(self):
  del self.record['spec']['coverAssetId'];self.save();m=self.export();self.assertTrue(any(x['slot']=='cover' for x in m['missingArtwork']))
 def test_html_escape_and_missing_language(self):
  self.record['spec']['panels'][0]['captions']={'en':'<script>oops</script>'};self.save();self.export();self.assertNotIn('<script>',(self.root/'out/preview.html').read_text())
 def test_no_overwrite(self):
  self.export()
  with self.assertRaisesRegex(ValueError,'overwrite'):self.export()
 def test_pdf_asset_not_accepted_as_image(self):
  self.asset['mime']='application/pdf'
  with self.assertRaisesRegex(ValueError,'type'):self.export()
 def test_embedded_budget_refuses_instead_of_dropping_images(self):
  with self.assertRaisesRegex(ValueError,'budget'):self.export(max_embedded_bytes=1)
 def test_missing_caption_language_is_explicit(self):
  self.record['spec']['panels'][0]['captions']={'en':'Hello'};self.save();m=self.export(lang='ru');self.assertTrue(any(x.get('reason')=='caption-language-missing' for x in m['missingArtwork']))
 def test_explicit_cover_selection_and_supplied_line_art(self):
  self.asset['provenance']['kind']='provided-line-art';del self.record['spec']['coverAssetId'];self.save();m=self.export(cover_asset='fixture-art',coloring=['fixture-art']);self.assertEqual(m['selection']['coverAssetId'],'fixture-art');self.assertEqual(sum(x['slot'].startswith('coloring-') for x in m['missingArtwork']),2);self.assertEqual(m['generationCalls'],0)
 def bound_snapshot(self):
  bindings=[{'assetId':self.asset['id'],'sha256':self.asset['sha256'],'bytes':self.asset['bytes'],'roles':['fixture:art'],'availability':'verified-local'}]
  reference_hash=delivery.fingerprint([{k:x[k] for k in ('assetId','sha256','bytes','roles')} for x in bindings]);version={'version':2,'spec':self.record['spec'],'referenceBindings':bindings,'referenceHash':reference_hash};version['sha256']=delivery.fingerprint({'spec':version['spec'],'referenceHash':reference_hash});return {'project':{'chapters':[{'id':'fixture','studioDraft':{'currentVersion':3,'versions':[version,dict(version,version=3)]}}]}}
 def test_actual_saved_snapshot_arbitrary_historical_version(self):
  self.record=self.bound_snapshot();self.save();m=self.export();self.assertEqual(m['version'],2);self.assertTrue(m['savedReferenceBindingVerified'])
 def test_tampered_saved_binding_refused(self):
  self.record=self.bound_snapshot();self.record['project']['chapters'][0]['studioDraft']['versions'][0]['referenceBindings'][0]['sha256']='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'SHA'):self.export()
 def test_reference_cache_availability_is_not_semantic_hash(self):
  self.record=self.bound_snapshot();self.record['project']['chapters'][0]['studioDraft']['versions'][0]['referenceBindings'][0]['availability']='unresolved-local';self.save();self.assertTrue(self.export()['savedReferenceBindingVerified'])
if __name__=='__main__':unittest.main()
