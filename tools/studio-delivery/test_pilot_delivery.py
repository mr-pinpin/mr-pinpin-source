import json,unittest,sys,types,importlib.util,copy
from pathlib import Path
from unittest.mock import patch
import test_delivery as old
D=old.delivery
class Tests(unittest.TestCase):
 def setUp(self):
  self.save=types.MethodType(old.DeliveryTests.save,self)
  old.DeliveryTests.setUp(self)
  self.record['sha256']='a'*64;self.save=types.MethodType(old.DeliveryTests.save,self);self.save()
  self.registry=[self.asset]+[dict(self.asset,id='line'+str(i),provenance={'kind':'provided-line-art'}) for i in range(3)]
 def export(self,**kw):
  body=dict(record_path=self.file,record_sha=self.sha,chapter='fixture',version=2,registry=self.registry,asset_root=self.root,out=self.root/'out',lang='en',coloring=['line0','line1','line2'],cover_asset='fixture-art',miniature_asset='fixture-art',require_complete=True,source_version_sha='a'*64);body.update(kw);return D.prepare(**body)
 def test_complete_three_line_pages_and_miniature(self):
  m=self.export();self.assertTrue(m['complete']);self.assertEqual(m['pageCount'],6);self.assertEqual(len([a for a in m['selectedArtwork'] if a['slot'].startswith('coloring-')]),3);self.assertEqual(m['selection']['miniatureAssetId'],'fixture-art')
 def test_missing_miniature(self):self.assertRaisesRegex(ValueError,'missing',self.export,miniature_asset='absent')
 def test_three_distinct_pages(self):self.assertRaisesRegex(ValueError,'distinct',self.export,coloring=['line0']*3)
 def test_missing_title_translation(self):self.record['spec']['title']={'en':'Title'};self.save();self.assertRaisesRegex(ValueError,'missing',self.export,lang='ru')
 def test_exact_version_hash(self):self.assertRaisesRegex(ValueError,'version SHA',self.export,source_version_sha='b'*64)
 def test_no_fake_ru_from_plain_text(self):self.record['spec']['title']='The leaf';self.save();self.assertRaisesRegex(ValueError,'russian',self.export,lang='ru')
 def translation(self):return {'sourceVersionSHA256':'a'*64,'title':{'en':'The leaf','ru':'Листочек'},'captions':{'p7':{'en':'Hmm…','ru':'Хм…'}}}
 def test_pinned_translation(self):m=self.export(lang='ru',translations=self.translation());self.assertTrue(m['complete']);self.assertIsNotNone(m['localizationSHA256']);self.assertIn('Раскраска',(self.root/'out/preview.html').read_text())
 def test_translation_wrong_version(self):t=self.translation();t['sourceVersionSHA256']='b'*64;self.assertRaises(ValueError,self.export,translations=t)
 def test_translation_changes_user_words(self):t=self.translation();t['captions']['p7']['en']='New story';self.assertRaisesRegex(ValueError,'English',self.export,translations=t)
 def test_unknown_panel_translation(self):t=self.translation();t['captions']['other']=t['captions']['p7'];self.assertRaisesRegex(ValueError,'panel',self.export,translations=t)
 def test_context_narrow_registry_no_state_mutation(self):
  class Error(Exception):pass
  mod=types.ModuleType('model');mod.StudioError=Error
  with patch.dict(sys.modules,{'model':mod}):
   spec=importlib.util.spec_from_file_location('pilot_pdf',Path(__file__).parents[1]/'studio/business/draft_pdf_delivery.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  state={'revision':2,'project':{'chapters':[{'id':'fixture','studioDraft':{'versions':[self.record]}}]},'assets':self.registry+[dict(self.asset,id='unused')]};before=copy.deepcopy(state)
  store=types.SimpleNamespace(read=lambda:state)
  r=helper.delivery_context(store,{'chapterId':'fixture','version':2,'sourceVersionSHA256':'a'*64,'additionalAssetIds':['line0','line1','line2','fixture-art']});self.assertNotIn('unused',[a['id'] for a in r['assets']]);self.assertEqual(state,before);self.assertRaises(Error,helper.delivery_context,store,{'chapterId':'fixture','version':2,'sourceVersionSHA256':'b'*64})
if __name__=='__main__':unittest.main()
