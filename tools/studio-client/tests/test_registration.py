import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "studio"))
try:
    from PIL import Image
    from store import Store
    from release import freeze
except ImportError:
    Image = None


@unittest.skipIf(Image is None, "Run with Studio Python environment (Pillow required)")
class RegistrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory()
        cls.root = Path(cls.workspace.name)
        cls.kernel = freeze(ROOT / "studio", cls.root / "runtime")["path"]

    @classmethod
    def tearDownClass(cls):
        # Immutable release files deliberately persist for the tempdir lifetime.
        import os
        for directory, dirs, files in os.walk(cls.root):
            os.chmod(directory, 0o755)
            for name in files:
                os.chmod(Path(directory)/name, 0o644)
        cls.workspace.cleanup()

    def setUp(self):
        self.case = tempfile.TemporaryDirectory(dir=self.root)
        self.folder = Path(self.case.name)
        self.store = Store(self.folder / "data")
        self.original = self.folder / "native.png"
        Image.new("RGB", (11,13), "red").save(self.original)
        self.prompt = self.folder / "prompt.txt"
        self.prompt.write_text("Exact generation prompt.\n",encoding="utf-8")
        raw = io.BytesIO()
        Image.new("RGB",(8,9),"blue").save(raw,format="PNG")
        self.reference = self.store.upload_asset(raw.getvalue(), "ref.png")[0]["id"]

    def tearDown(self):
        self.case.cleanup()

    def call(self, reference=None, extra=()):
        result = subprocess.run([sys.executable, str(ROOT / "studio-client/register-image.py"),
                                 "--kernel-root", self.kernel, "--data-dir", str(self.store.root),
                                 "--native-path", str(self.original), "--prompt-file", str(self.prompt),
                                 "--reference", reference or self.reference, "--output-name", "study.png", *extra],
                                capture_output=True,text=True,timeout=20)
        return result.returncode,json.loads(result.stdout)

    def test_exact_bytes_provenance_card_and_no_project_change(self):
        project=self.store.read()["project"]
        code,result=self.call()
        self.assertEqual(code,0,result)
        self.assertEqual(result["reviewStatus"],"unreviewed")
        self.assertEqual(Path(result["generatedPath"]).read_bytes(),self.original.read_bytes())
        saved=next(a for a in self.store.read()["assets"] if a["id"]==result["assetId"])
        self.assertEqual(saved["provenance"]["prompt"],self.prompt.read_text())
        self.assertEqual(saved["provenance"]["referenceIds"],[self.reference])
        self.assertEqual(saved["provenance"]["tool"],"image_gen.imagegen")
        self.assertEqual(result["workflowCard"]["actions"],[])
        self.assertEqual(self.store.asset_path(result["assetId"]).read_bytes(),self.original.read_bytes())
        self.assertEqual(self.store.read()["project"],project)
        self.assertEqual(result["workflowCard"]["assetIds"],[result["assetId"]])
        self.assertGreaterEqual(result["timing"]["registrationSeconds"],0)
        count=len(self.store.read()["assets"])
        code,repeated=self.call()
        self.assertEqual(code,0,repeated)
        self.assertTrue(repeated["reused"])
        self.assertEqual(count,len(self.store.read()["assets"]))

    def test_unknown_reference_fails_before_copy(self):
        code,result=self.call("missing")
        self.assertEqual(code,1)
        self.assertIn("Unknown reference",result["error"]["message"])
        self.assertFalse((self.store.root/"generated").exists())

    def test_malformed_image_fails_before_copy(self):
        self.original.write_bytes(b"not an image")
        code,_=self.call()
        self.assertEqual(code,1)
        self.assertFalse((self.store.root/"generated").exists())

    def test_output_collision_preserves_existing_bytes(self):
        import hashlib
        sha=hashlib.sha256(self.original.read_bytes()).hexdigest()
        generated=self.store.root/"generated"
        generated.mkdir()
        destination=generated/(sha[:16]+"-study.png")
        destination.write_bytes(b"existing other bytes")
        before=len(self.store.read()["assets"])
        code,result=self.call()
        self.assertEqual(code,1)
        self.assertIn("different bytes",result["error"]["message"])
        self.assertEqual(destination.read_bytes(),b"existing other bytes")
        self.assertEqual(len(self.store.read()["assets"]),before)

    def test_dossier_preserves_prior_stages_candidates_and_project(self):
        self.store.mutate(lambda state:state["project"]["entities"].append({"id":"papa","name":"Papa"}))
        path=self.store.root/"reports/character-packages/papa.json"
        path.parent.mkdir(parents=True)
        prior={"schemaVersion":1,"entityId":"papa","note":"keep me","stages":{"earlier":{"candidates":[{"assetId":"prior","note":"retain"}]}}}
        path.write_text(json.dumps(prior))
        before=self.store.read()["project"]
        code,result=self.call(extra=("--entity","papa","--stage","solo"))
        self.assertEqual(code,0,result)
        value=json.loads(path.read_text())
        self.assertEqual(value["stages"]["earlier"],prior["stages"]["earlier"])
        self.assertEqual(value["note"],"keep me")
        receipt=value["stages"]["solo"]["candidates"][0]
        self.assertEqual(receipt["assetId"],result["assetId"])
        self.assertEqual(receipt["provenance"]["referenceIds"],[self.reference])
        self.assertGreaterEqual(receipt["timing"]["registrationSeconds"],0)
        self.assertEqual(result["dossierPath"],str(path))
        self.assertEqual(self.store.read()["project"],before)
        code,_=self.call(extra=("--entity","papa","--stage","solo"))
        self.assertEqual(code,0)
        self.assertEqual(len(json.loads(path.read_text())["stages"]["solo"]["candidates"]),1)

    def test_setup_manifest_exact_argv_and_helper_hash(self):
        import hashlib
        runtime=self.root/"runtime"
        (runtime/"current-deployment.json").write_text(json.dumps({"stableRelease":Path(self.kernel).name,"dataDirectory":str(self.store.root)}))
        helper=ROOT/"studio-client/register-image.py"
        before=self.store.read()
        result=subprocess.run([sys.executable,str(helper),"--runtime-dir",str(runtime),"--setup-toolchain"],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        manifest=json.loads((self.store.root/"workflows/toolchain.json").read_text())
        self.assertEqual(manifest["argvPrefix"],[str(Path(sys.executable).absolute()),str(helper.resolve()),"--runtime-dir",str(runtime.resolve())])
        self.assertEqual(manifest["helperSha256"],hashlib.sha256(helper.read_bytes()).hexdigest())
        self.assertEqual(manifest["parameters"]["optional"],["--entity","--stage"])
        self.assertEqual(self.store.read(),before)

    def test_invalid_dossier_or_entity_fails_before_copy(self):
        code,result=self.call(extra=("--entity","../escape","--stage","solo"))
        self.assertEqual(code,1)
        self.assertFalse((self.store.root/"generated").exists())
        self.store.mutate(lambda state:state["project"]["entities"].append({"id":"papa"}))
        path=self.store.root/"reports/character-packages/papa.json"
        path.parent.mkdir(parents=True)
        path.write_text('{"keep":"unsupported dossier"}')
        code,_=self.call(extra=("--entity","papa","--stage","solo"))
        self.assertEqual(code,1)
        self.assertEqual(path.read_text(),'{"keep":"unsupported dossier"}')
        self.assertFalse((self.store.root/"generated").exists())
