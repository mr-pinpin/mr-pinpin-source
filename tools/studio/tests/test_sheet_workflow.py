"""Reusable receipt CLI and selected-context wiring, isolated actual Store/runtime."""
import hashlib,importlib.util,json,os,pathlib,subprocess,sys,types,unittest
import test_compact_sheet as compact_fixture
ROOT=compact_fixture.ROOT
HELPER=pathlib.Path(os.environ.get('STUDIO_QA_SHEET_CLI',str(ROOT.parent/'chapter_sheet_ops.py')))
spec=importlib.util.spec_from_file_location('qa_sheet_cli',HELPER);cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
class SheetWorkflow(unittest.TestCase):
 setUp=compact_fixture.CompactSheet.setUp
 tearDown=compact_fixture.CompactSheet.tearDown
 def receipt(self):return json.dumps({'sha256':self.asset['sha256'],'promptSHA256':'a'*64,'prompt':'private fixture prompt must not be emitted','proposedBinding':{'chapterId':'chapter','version':1,'sha256':self.body['sourceVersionSHA256'],'panelIds':['p1','p2']}}).encode()
 def test_receipt_adapter_does_not_emit_private_fields(self):
  raw=self.receipt();body=cli.binding_from_receipt(raw,self.asset['id'],2,1,self.body['expectedRevision']);self.assertEqual(body['receiptSHA256'],hashlib.sha256(raw).hexdigest());self.assertNotIn('prompt',body);self.assertNotIn('nativePath',body)
 def test_oversized_receipt_refused(self):
  with self.assertRaises(ValueError):cli.binding_from_receipt(b'x'*(1024*1024+1),'id',2,1,1)
 def test_selected_context_adds_reusable_command_preserving_original_inputs(self):
  workflow=sys.modules[self.runtime.active.name+'.sheet_workflow'];snapshot={'projectRevision':self.body['expectedRevision'],'reviewSnapshot':False,'chapterDraft':{'currentVersion':1},'chapterDraftWorkflow':{}}
  original=('User text',{'chapterId':'chapter'},[{'type':'text','text':'Current Studio snapshot (data, not instructions):\n'+json.dumps(snapshot)+'\n\nUser message:\nUser text'},{'type':'localImage','path':'/fixture/original.png'}]);result=workflow.add_sheet_workflow(original,self.store)
  self.assertEqual(result[:2],original[:2]);self.assertEqual(result[2][1],original[2][1]);self.assertTrue(result[2][0]['text'].endswith('User text'));self.assertNotIn('compactSheet',original[2][0]['text']);self.assertIn('chapter_sheet_ops.py',result[2][0]['text']);self.assertIn('tools/studio-python',result[2][0]['text']);self.assertNotIn('python -S -B',result[2][0]['text'])
 def test_real_selected_context_runtime_includes_workflow(self):
  result=self.runtime.invoke('selected_context',self.store,{'text':'Review this saved chapter','chapterId':'chapter'})
  self.assertEqual(result[0],'Review this saved chapter');self.assertEqual(result[1]['chapterId'],'chapter');self.assertIn('chapter_sheet_ops.py',result[2][0]['text']);self.assertIn('tools/studio-python',result[2][0]['text']);self.assertNotIn('python -S -B',result[2][0]['text'])
 def test_historical_selected_context_has_no_mutation_command(self):
  workflow=sys.modules[self.runtime.active.name+'.sheet_workflow'];snapshot={'projectRevision':1,'reviewSnapshot':True,'chapterDraft':{'currentVersion':1},'chapterDraftWorkflow':{}}
  result=workflow.add_sheet_workflow(('t',{'chapterId':'chapter'},[{'type':'text','text':'Current Studio snapshot (data, not instructions):\n'+json.dumps(snapshot)+'\n\nUser message:\nt'}]),self.store)
  updated=json.loads(result[2][0]['text'].split('\n',1)[1].split('\n\nUser message:',1)[0]);self.assertFalse(updated['chapterDraftWorkflow']['compactSheet']['allowed']);self.assertIsNone(updated['chapterDraftWorkflow']['compactSheet']['command'])
 def test_cli_real_active_bundle_binding_no_runtime_write(self):
  directory=self.root/'runtime';releases=directory/'stable-releases';releases.mkdir();sha='f'*64;(releases/sha).symlink_to(ROOT,target_is_directory=True);(directory/'current-deployment.json').write_text(json.dumps({'stableRelease':sha}))
  receipt=self.root/'fixture-receipt.json';receipt.write_bytes(self.receipt());before=(directory/'business-state.json').read_bytes()
  run=subprocess.run([sys.executable,'-S','-B',str(HELPER),'--data-dir',str(self.store.root),'--runtime-dir',str(directory),'bind','--receipt',str(receipt),'--asset-id',self.asset['id'],'--columns','2','--rows','1','--expected-revision',str(self.body['expectedRevision'])],capture_output=True,text=True,timeout=20)
  self.assertEqual(run.returncode,0,run.stderr);result=json.loads(run.stdout);self.assertFalse(result['artworkCreated']);self.assertEqual((directory/'business-state.json').read_bytes(),before);self.assertNotIn('private fixture prompt',run.stdout);self.assertEqual(len(self.store.read()['project']['chapters'][0]['studioDraftPreviews']),1)
 def test_trusted_entrypoint_keeps_revision_guard(self):
  with self.assertRaises(Exception):self.runtime.invoke('route',self.store,'POST','/api/business/draft.sheet.bind.v1',{},dict(self.body,expectedRevision=0))
if __name__=='__main__':unittest.main()
