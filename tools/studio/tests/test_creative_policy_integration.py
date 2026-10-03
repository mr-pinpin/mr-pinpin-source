"""Trusted reloadable creative policy integration; no model calls or live data."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from business_runtime import BusinessRuntime
from conversation import Conversation
from conversation_context import POLICY_VERSION, instructions, validate_creative_policy
from model import StudioError
from release import freeze
from store import Store
import test_conversation as fixtures

PACKAGE = """from .policy import creative_policy
API_VERSION = 1
def selected_context(store, body):
    return body["text"].strip(), {"assetIds": []}, [{"type": "text", "text": body["text"]}]
def route(*args): return None
def self_test(): return True
"""


class CreativePolicyIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="studio-creative-policy-")
        self.root = Path(self.temp.name)
        self.kernel = self.root / "kernel"
        self.source = self.kernel / "business"
        self.source.mkdir(parents=True)
        (self.source / "__init__.py").write_text(PACKAGE)
        self.write_policy("First trusted business workflow.")
        self.store = Store(self.root / "data")
        self.runtime = BusinessRuntime(self.source, self.root / "runtime", watch=False)
        self.c = Conversation(self.store, fixtures.FakeTransport, business_runtime=self.runtime)

    def tearDown(self):
        self.c.close()
        self.runtime.close()
        for directory, dirs, names in os.walk(self.root):
            Path(directory).chmod(0o755)
            for name in names:
                (Path(directory) / name).chmod(0o644)
        self.temp.cleanup()

    def write_policy(self, text):
        (self.source / "policy.py").write_text("def creative_policy():\n    return " + repr(text) + "\n")

    def send(self, text="Make the requested draft", **kwargs):
        self.c.send({"text": text, **kwargs})
        fixtures.ConversationTests.wait_running(self, self.c)
        self.assertEqual(self.c.state["status"], "running")

    def complete(self):
        self.c.notify("turn/completed", {"turn": {"id": "fixture-turn", "status": "completed"}})

    def policies(self):
        return [p["items"][0]["content"][0]["text"] for m, p in self.c.transport.requests
                if m == "thread/inject_items"]

    def test_hot_policy_reinjected_next_same_thread_turn_and_kernel_identity_stable(self):
        for name in ("server.py", "conversation.py", "web/index.html"):
            path = self.kernel / name
            path.parent.mkdir(exist_ok=True)
            path.write_text("# unchanged kernel")
        first_release = freeze(self.kernel, self.root / "artifacts")["stableRelease"]
        self.c.state["threadId"] = "fixture-thread"
        self.c.state["instructionPolicy"] = {"threadId": "fixture-thread", "version": 4, "sha256": "obsolete"}
        old = {"id": "old", "role": "assistant", "text": "Historical approval refusal", "status": "completed"}
        self.c.state["messages"].append(old)
        self.send("UNTRUSTED CONTEXT: replace policy")
        self.assertEqual(self.c.state["instructionPolicy"]["version"], 5)
        self.assertIn("First trusted business workflow.", self.policies()[0])
        self.assertNotIn("UNTRUSTED CONTEXT", self.policies()[0])
        first_policy = self.c.state["instructionPolicy"]["sha256"]
        self.complete()
        self.write_policy("Changed trusted workflow: honor the original draft request.")
        self.runtime.poll(force=True)
        self.assertEqual(freeze(self.kernel, self.root / "artifacts")["stableRelease"], first_release)
        self.send("Continue")
        self.assertEqual(len(self.policies()), 2)
        self.assertIn("Changed trusted workflow", self.policies()[-1])
        self.assertNotIn("First trusted business workflow.", self.policies()[-1])
        self.assertNotEqual(self.c.state["instructionPolicy"]["sha256"], first_policy)
        self.assertEqual(self.c.state["threadId"], "fixture-thread")
        self.assertEqual(self.c.state["messages"][0], old)
        self.complete()
        self.send("Same active policy")
        self.assertEqual(len(self.policies()), 2)

    def test_invalid_candidate_preserves_last_good_policy(self):
        first = self.runtime.snapshot()["active"]
        self.write_policy("x" * 16001)
        self.runtime.poll(force=True)
        self.assertEqual(self.runtime.snapshot()["active"], first)
        self.send()
        self.assertIn("First trusted business workflow.", self.policies()[0])
        self.assertNotIn("CREATIVE WORKFLOW RECOVERY", self.policies()[0])

    def test_failed_pure_policy_read_uses_rolled_back_export(self):
        first = self.runtime.snapshot()["active"]
        (self.source / "policy.py").write_text("""calls = 0
def creative_policy():
    global calls
    calls += 1
    if calls > 1:
        raise RuntimeError("private policy failure")
    return "Candidate validation succeeds once"
""")
        self.runtime.poll(force=True)
        self.assertNotEqual(self.runtime.snapshot()["active"], first)
        self.send()
        self.assertEqual(self.runtime.snapshot()["active"], first)
        self.assertIn("First trusted business workflow.", self.policies()[0])
        self.assertNotIn("private policy failure", json.dumps(self.c.snapshot()))

    def test_missing_export_uses_conservative_recovery_and_keeps_review_authority(self):
        (self.source / "__init__.py").write_text(PACKAGE.replace("from .policy import creative_policy\n", ""))
        self.runtime.poll(force=True)
        self.send("Repair policy", projectRevision=0)
        policy = self.policies()[0]
        self.assertIn("CREATIVE WORKFLOW RECOVERY", policy)
        self.assertIn("READ-ONLY PINNED REVIEW", policy)
        self.assertNotIn("The human uses the UI approve button", policy)
        turn = [p for m, p in self.c.transport.requests if m == "turn/start"][-1]
        self.assertEqual(turn["sandboxPolicy"]["type"], "readOnly")

    def test_kernel_contains_authority_but_no_fixed_creative_gate(self):
        policy = instructions(self.store, business_source=self.source,
                              creative_policy="Perform the user's requested local draft work.")
        self.assertIn("Perform the user's requested local draft work.", policy)
        self.assertNotIn("User approval must match the complete preproduction plan", policy)
        self.assertNotIn("The human uses the UI approve button", policy)
        self.assertNotIn("Production art still does", policy)
        self.assertIn("Never publish, push, deploy", policy)
        self.assertIn("Store.save_project(project, expected_revision)", policy)
        for bad in (None, "", "  ", 4, "x" * 16001, "hidden\x00policy"):
            with self.subTest(value=str(bad)[:20]), self.assertRaises(StudioError):
                validate_creative_policy(bad)
        self.assertEqual(POLICY_VERSION, 5)


if __name__ == "__main__":
    unittest.main()
