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

    def call(self, reference=None):
        result = subprocess.run([sys.executable, str(ROOT / "studio-client/register-image.py"),
                                 "--kernel-root", self.kernel, "--data-dir", str(self.store.root),
                                 "--native-path", str(self.original), "--prompt-file", str(self.prompt),
                                 "--reference", reference or self.reference, "--output-name", "study.png"],
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
