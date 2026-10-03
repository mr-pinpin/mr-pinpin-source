"""Focused trusted product-policy contract and loader regression tests."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from business import creative_policy, self_test
from business_runtime import BusinessRuntime
from model import StudioError


class CreativePolicyTests(unittest.TestCase):
    def test_export_is_pure_bounded_and_package_contract_passes(self):
        with patch("builtins.open", side_effect=AssertionError("Policy must not read files")):
            value = creative_policy()
            self.assertEqual(value, creative_policy())
        self.assertIsInstance(value, str)
        self.assertTrue(0 < len(value.strip()) <= 16000)
        self.assertTrue(self_test())

    def test_first_request_is_sufficient_but_design_and_production_boundaries_remain(self):
        value = creative_policy()
        for clause in ("initial action request itself authorizes",
                       "do not require a complete\nchapter plan",
                       "produce and show the first candidate",
                       "before expanding the unconfirmed design",
                       "fabricate or write human approval metadata",
                       "also authorizes ordinary reversible local chapter draft production",
                       "not a universal workflow block",
                       "Never invent progress",
                       "Publication requires its own explicit authorization"):
            self.assertIn(clause, value)

    def test_views_and_existing_registration_helper_are_explicit(self):
        value = creative_policy()
        for clause in ("SCREEN LEFT versus SCREEN RIGHT", "both face and body sheets",
                       "Inspect actual", "direction coverage before delivery",
                       "register-image.py helper and its README",
                       "exact submitted prompt file and actual registered reference IDs",
                       "Do not invent a helper path"):
            self.assertIn(clause, value)

    def test_generation_waits_are_bounded_without_busy_polling(self):
        value = creative_policy()
        for clause in ("initial exec yield of 30–60 seconds",
                       "subsequent waits of 30–60 seconds",
                       "Avoid one-second busy polling",
                       "tool-specific instructions and supported ranges take",
                       "updates about every 60 seconds",
                       "do not\nassume image generation executes concurrently"):
            self.assertIn(clause, value)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="studio-creative-policy-")
        self.root = Path(self.temp.name)
        self.source = self.root / "business"
        self.source.mkdir()
        self.runtime = None

    def tearDown(self):
        if self.runtime:
            self.runtime.close()
        self.temp.cleanup()

    def package(self, extra=""):
        (self.source / "__init__.py").write_text(
            "API_VERSION=1\n"
            "def selected_context(store,body): return None\n"
            "def route(store,method,path,query,body): return None\n"
            "def self_test(): return True\n" + extra)

    def start(self):
        self.runtime = BusinessRuntime(self.source, self.root / "runtime", watch=False)
        self.assertIsNotNone(self.runtime.snapshot()["active"])

    def test_retained_package_without_export_remains_valid_but_cannot_supply_policy(self):
        self.package()
        self.start()
        before = self.runtime.snapshot()
        with self.assertRaises(StudioError) as error:
            self.runtime.invoke("creative_policy")
        self.assertEqual(error.exception.code, "business_unavailable")
        self.assertEqual(before, self.runtime.snapshot())

    def test_invalid_candidate_policy_preserves_last_good(self):
        self.package("def creative_policy(): return 'valid policy'\n")
        self.start()
        before = self.runtime.snapshot()["active"]
        for extra in ("creative_policy='not callable'\n",
                      "def creative_policy(required): return 'wrong arity'\n",
                      "def creative_policy(): return {}\n",
                      "def creative_policy(): return '   '\n",
                      "def creative_policy(): return 'x'*16001\n"):
            with self.subTest(extra=extra):
                self.package(extra)
                self.runtime.poll(force=True)
                self.assertEqual(self.runtime.snapshot()["active"], before)
                self.assertEqual(self.runtime.snapshot()["status"], "error")
                self.assertEqual(self.runtime.invoke("creative_policy"), "valid policy")

    def test_late_policy_failure_rolls_back_without_replaying(self):
        self.package("def creative_policy(): return 'previous policy'\n")
        self.start()
        previous = self.runtime.snapshot()["active"]
        self.package("calls=0\n"
                     "def creative_policy():\n"
                     " global calls\n"
                     " calls+=1\n"
                     " return 'initially valid' if calls==1 else None\n")
        self.runtime.poll(force=True)
        self.assertNotEqual(self.runtime.snapshot()["active"], previous)
        with self.assertRaises(StudioError) as error:
            self.runtime.invoke("creative_policy")
        self.assertEqual(error.exception.code, "business_call")
        self.assertEqual(self.runtime.snapshot()["active"], previous)
        self.assertEqual(self.runtime.invoke("creative_policy"), "previous policy")


if __name__ == "__main__":
    unittest.main()
