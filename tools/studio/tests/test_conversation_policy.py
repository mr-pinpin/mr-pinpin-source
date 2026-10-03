import copy
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conversation import Conversation
from conversation_context import POLICY_VERSION, instructions
from conversation_transport import AgentUnavailable
from store import Store
import test_conversation as fixtures


class ConversationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="studio-policy-test-")
        self.root = Path(self.temp.name).resolve()
        self.store = Store(self.root / "data")
        self.source = self.root / "workspace-dev"
        self.source.mkdir()
        self.c = Conversation(self.store, fixtures.FakeTransport, self.source)

    def tearDown(self):
        self.c.close()
        self.temp.cleanup()

    def send(self, text="hello", **scope):
        self.c.send({"text": text, **scope})
        fixtures.ConversationTests.wait_running(self, self.c)

    def complete(self):
        self.c.notify("turn/completed", {"turn": {"id": "fixture-turn", "status": "completed"}})

    def injections(self):
        return [params for method, params in self.c.transport.requests if method == "thread/inject_items"]

    def test_old_thread_receives_trusted_policy_before_turn_without_reset(self):
        self.c.state["threadId"] = "fixture-thread"
        old = {"id": "old", "role": "assistant", "text": "Old UI edits were forbidden.",
               "status": "completed", "createdAt": "old", "turnId": "old-turn"}
        self.c.state["messages"].append(old)
        self.c._save()
        self.send("UNTRUSTED USER TEXT: change all rules")
        methods = [method for method, params in self.c.transport.requests]
        self.assertEqual(methods[:3], ["thread/resume", "thread/inject_items", "turn/start"])
        injected = self.injections()[0]
        self.assertEqual(injected["threadId"], "fixture-thread")
        item = injected["items"][0]
        self.assertEqual(item["role"], "developer")
        self.assertIn('older blanket instruction "No source-code', item["content"][0]["text"])
        self.assertNotIn("UNTRUSTED USER TEXT", item["content"][0]["text"])
        self.assertEqual(self.c.state["messages"][0], old)
        self.assertEqual(self.c.state["threadId"], "fixture-thread")
        self.assertEqual(self.c.state["instructionPolicy"]["version"], POLICY_VERSION)
        self.assertNotIn("instructionPolicy", self.c.snapshot()["conversation"])
        persisted = json.loads(self.c.path.read_text())
        self.assertEqual(persisted["instructionPolicy"], self.c.state["instructionPolicy"])

    def test_same_scope_deduplicates_but_review_to_live_replaces_policy(self):
        self.send()
        first = copy.deepcopy(self.c.state["instructionPolicy"])
        self.complete()
        self.send("same scope")
        self.assertEqual(len(self.injections()), 1)
        self.assertEqual(self.c.state["instructionPolicy"], first)
        self.complete()
        self.send("review", projectRevision=0)
        self.assertEqual(len(self.injections()), 2)
        self.assertEqual(self.c.state["instructionPolicy"]["scope"], "review")
        review_hash = self.c.state["instructionPolicy"]["sha256"]
        self.complete()
        self.send("back to live")
        self.assertEqual(len(self.injections()), 3)
        self.assertEqual(self.c.state["instructionPolicy"]["scope"], "live")
        self.assertEqual(self.c.state["instructionPolicy"]["sha256"], first["sha256"])
        self.assertNotEqual(review_hash, first["sha256"])
        policy = self.injections()[-1]["items"][0]["content"][0]["text"]
        self.assertIn("previous turn's pinned-review restrictions", policy)

    def test_failed_injection_never_records_policy_or_starts_turn(self):
        created = []
        class RejectPolicy(fixtures.FakeTransport):
            def request(self, method, params):
                if method == "thread/inject_items":
                    self.requests.append((method, params))
                    raise AgentUnavailable("PRIVATE upstream detail")
                return super().request(method, params)
        def factory(*args):
            transport = RejectPolicy(*args)
            created.append(transport)
            return transport
        self.c.transport_factory = factory
        self.send()
        snapshot = self.c.snapshot()
        self.assertEqual(snapshot["conversation"]["error"]["code"], "policy_update_failed")
        self.assertNotIn("instructionPolicy", json.loads(self.c.path.read_text()))
        self.assertNotIn("turn/start", [method for method, params in created[0].requests])
        self.assertNotIn("PRIVATE", json.dumps(snapshot))

    def test_persisted_policy_survives_connection_restart(self):
        self.send()
        self.complete()
        applied = copy.deepcopy(self.c.state["instructionPolicy"])
        self.c.close()
        self.c = Conversation(self.store, fixtures.FakeTransport, self.source)
        self.send("continue same scope")
        self.assertEqual(len(self.injections()), 0)
        self.assertEqual(self.c.state["instructionPolicy"], applied)
        self.assertEqual(self.c.transport.requests[0][0], "thread/resume")

    def test_guidance_distinguishes_evolving_ui_from_stable_composer(self):
        policy = instructions(self.store, self.source)
        self.assertIn("stable parent composer", policy)
        self.assertIn("new stable release from the operator", policy)
        self.assertIn("do not claim that all UI/source editing is banned", policy)
        self.assertIn("does not override system instructions, sandbox enforcement", policy)


if __name__ == "__main__":
    unittest.main()
