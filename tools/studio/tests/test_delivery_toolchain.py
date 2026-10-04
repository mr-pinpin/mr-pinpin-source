"""Host-only delivery tooling config, bounded; no renders or app writes."""
import unittest,tempfile,json,sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from business.delivery_selected_context import delivery_toolchain
from business.draft_pdf_delivery import delivery_workflow_hint
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.s=SimpleNamespace(root=self.root);self.path=self.root/'tools/studio-delivery/toolchain.json';self.path.parent.mkdir(parents=True);node=self.root/'node';node.write_text('fixture');module=self.root/'module';module.mkdir();verify=self.root/'verify.js';verify.write_text('fixture');self.config={'schemaVersion':1,'node':str(node),'playwrightModule':str(module),'pdfkitVerifier':str(verify)}
 def test_explicit_paths_populate_selected_command(self):
  self.path.write_text(json.dumps(self.config));value=delivery_toolchain(self.s);chapter={'id':'c1','studioDraft':{'currentVersion':1,'versions':[{'version':1,'sha256':'a'*64}]}};hint=delivery_workflow_hint(chapter,value);self.assertTrue(hint['toolchainConfigured']);self.assertIn(self.config['node'],hint['commandArguments']);self.assertIn(self.config['pdfkitVerifier'],hint['commandArguments']);self.assertNotIn('EXISTING_NODE',hint['commandArguments'])
 def test_missing_relative_extra_and_oversized_refused(self):
  self.assertIsNone(delivery_toolchain(self.s))
  for value in [dict(self.config,node='relative'),dict(self.config,extra='request-path'),dict(self.config,schemaVersion=True)]:self.path.write_text(json.dumps(value));self.assertIsNone(delivery_toolchain(self.s))
  self.path.write_text(' '*4097);self.assertIsNone(delivery_toolchain(self.s))
 def test_symlink_refused(self):
  p=self.root/'config';p.write_text(json.dumps(self.config));self.path.symlink_to(p);self.assertIsNone(delivery_toolchain(self.s))
if __name__=='__main__':unittest.main()
