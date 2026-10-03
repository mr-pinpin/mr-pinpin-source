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

    def test_guidance_allows_normal_composer_but_protects_actual_kernel(self):
        policy = instructions(self.store, self.source)
        self.assertEqual(POLICY_VERSION, 4)
        self.assertIn("chat-composer.js and its keyboard handlers are ordinary editable UI source", policy)
        self.assertIn("Permission follows the actual source path", policy)
        self.assertIn("Older Studio statements that the normal chat composer", policy)
        self.assertIn("authenticated transport, typed API", policy)
        self.assertIn("persistent storage/recovery, iframe hosting and isolation", policy)
        self.assertNotIn("stable parent composer, conversation controls or backend", policy)
        self.assertIn("does not override system instructions, sandbox enforcement", policy)

    def test_business_runtime_dispatch_and_exact_scope_migrate_old_backend_ban(self):
        from conversation_context import selected_context
        source = self.root / "business"
        source.mkdir()
        calls = []
        class Runtime:
            def invoke(runtime, name, *args, validate=None):
                calls.append(name)
                return validate(selected_context(*args))
        runtime = Runtime()
        runtime.source = source
        self.c.business_runtime = runtime
        self.c.state["threadId"] = "fixture-thread"
        old = {"id": "v3", "role": "assistant", "text": "All backend files are protected.",
               "status": "completed", "createdAt": "old", "turnId": "old-turn"}
        self.c.state["messages"].append(old)
        self.c.state["instructionPolicy"] = {"threadId": "fixture-thread", "sha256": "v3", "version": 3}
        self.send("Change a backend business rule")
        self.assertEqual(calls, ["selected_context"])
        self.assertEqual(self.c.state["messages"][0], old)
        policy = self.injections()[0]["items"][0]["content"][0]["text"]
        self.assertIn("supersedes earlier Studio bans on all backend edits", policy)
        self.assertIn("SAME running server", policy)
        self.assertIn(str(source), policy)
        self.assertIn("durable transcript machinery", policy)
        params = [p for m, p in self.c.transport.requests if m == "turn/start"][-1]
        self.assertEqual(params["sandboxPolicy"]["writableRoots"],
                         [str(self.store.root), str(self.source), str(source)])
        self.complete()
        self.send("Review only", projectRevision=0)
        params = [p for m, p in self.c.transport.requests if m == "turn/start"][-1]
        self.assertEqual(params["sandboxPolicy"], {"type": "readOnly", "networkAccess": False})

    def test_business_cannot_grant_write_authority_to_review(self):
        from conversation_context import selected_context
        class Runtime:
            source = self.root / "business"
            def invoke(runtime, name, store, body, validate=None):
                text, scope, inputs = selected_context(store, body)
                scope.update(reviewSnapshot=False, projectRevision=999)
                result = text, scope, inputs
                validate(result)
                return result
        self.c.business_runtime = Runtime()
        self.send("Review only", projectRevision=0)
        self.assertTrue(self.c.state["messages"][-1]["context"]["reviewSnapshot"])
        self.assertEqual(self.c.state["messages"][-1]["context"]["projectRevision"], 0)
        params = [p for m, p in self.c.transport.requests if m == "turn/start"][-1]
        self.assertEqual(params["sandboxPolicy"]["type"], "readOnly")

    def test_native_context_envelope_rejects_paths_and_unbounded_or_nontext_inputs(self):
        from conversation_context import selected_context, validate_context
        from model import StudioError
        body = {"text": "hello"}
        state = self.store.read()
        result = selected_context(self.store, body)
        self.assertEqual(validate_context(self.store, body, result, state)[0], "hello")
        cases = [
            ("different user text", {}, [{"type": "text", "text": "hello"}]),
            ("hello", {}, [{"type": "text", "text": "x" * 524289}]),
            ("hello", {}, [{"type": "tool", "text": "hello"}]),
            ("hello", {"assetIds": ["missing"]}, [{"type": "text", "text": "hello"},
                                                  {"type": "localImage", "path": "/etc/passwd"}]),
            ("hello", {"assetIds": [{}]}, [{"type": "text", "text": "hello"}, {}]),
            ("hello", {}, [None]),
        ]
        for case in cases:
            with self.subTest(case=str(case)[:80]), self.assertRaises(StudioError):
                validate_context(self.store, body, case, state)

    def test_missing_business_preserves_review_chat_recovery(self):
        from business_runtime import BusinessRuntime
        from model import StudioError
        source = self.root / "broken-business"
        source.mkdir()
        (source / "__init__.py").write_text("invalid Python !")
        runtime = BusinessRuntime(source, self.root / "runtime", watch=False)
        self.c.business_runtime = runtime
        try:
            with self.assertRaises(StudioError):
                self.c.send({"text": "", "projectRevision": 0})
            with self.assertRaises(StudioError):
                self.c.send({"text": "hello", "assetIds": ["missing"]})
            self.assertEqual(self.c.state["messages"], [])
            self.send("Explain what failed", projectRevision=0)
            context = self.c.state["messages"][-1]["context"]
            self.assertEqual(context["contextDiagnostic"]["code"], "business_unavailable")
            params = [p for m, p in self.c.transport.requests if m == "turn/start"][-1]
            self.assertEqual(params["sandboxPolicy"]["type"], "readOnly")
            self.assertIn("minimal conversation recovery", params["input"][0]["text"])
            self.c.notify("item/agentMessage/delta", {"itemId": "recovery-reply", "delta": "I can explain the failure."})
            self.complete()
            self.assertEqual(self.c.snapshot()["conversation"]["messages"][-1]["text"], "I can explain the failure.")
        finally:
            runtime.close()

    def test_failed_business_call_recovery_does_not_replay_side_effect(self):
        from business_runtime import BusinessRuntime
        source = self.root / "failing-business"
        source.mkdir()
        (source / "__init__.py").write_text("""API_VERSION = 1
 def selected_context(store, body):
     path = store.root / 'invocations.txt'
     path.write_text((path.read_text() if path.exists() else '') + 'x')
     raise RuntimeError('private failure')
 def route(*args): return None
 def self_test(): return True
""".replace("\n ", "\n"))
        runtime = BusinessRuntime(source, self.root / "runtime", watch=False)
        self.c.business_runtime = runtime
        try:
            self.assertIsNotNone(runtime.snapshot()["active"])
            self.send("Repair the business module")
            self.assertEqual((self.store.root / "invocations.txt").read_text(), "x")
            self.assertIsNone(runtime.snapshot()["active"])
            context = self.c.state["messages"][-1]["context"]
            self.assertEqual(context["contextDiagnostic"]["code"], "business_call")
            self.assertNotIn("private failure", json.dumps(self.c.snapshot()))
            self.assertEqual(len([m for m, p in self.c.transport.requests if m == "turn/start"]), 1)
        finally:
            runtime.close()

    def test_business_failure_is_not_replayed_or_started_as_a_turn(self):
        calls = []
        class Runtime:
            source = self.root / "business"
            def invoke(runtime, *args, **kwargs):
                calls.append(args[0])
                raise RuntimeError("business validation failed")
        self.c.business_runtime = Runtime()
        with self.assertRaisesRegex(RuntimeError, "business validation failed"):
            self.c.send({"text": "hello"})
        self.assertEqual(calls, ["selected_context"])
        self.assertEqual(self.c.state["messages"], [])
        self.assertIsNone(self.c.transport)

    def test_version_two_composer_restriction_is_replaced_in_same_thread(self):
        self.c.state["threadId"] = "fixture-thread"
        self.c.state["instructionPolicy"] = {
            "threadId": "fixture-thread", "sha256": "old-version-two", "version": 2, "scope": "live"}
        old = {"id": "legacy", "role": "assistant", "text": "The composer is protected stable core.",
               "status": "completed", "createdAt": "old", "turnId": "old-turn"}
        self.c.state["messages"].append(old)
        self.send("Change the keyboard shortcut in the normal composer")
        self.assertEqual(len(self.injections()), 1)
        self.assertEqual(self.c.state["instructionPolicy"]["version"], 4)
        self.assertEqual(self.c.state["messages"][0], old)
        params = [params for method, params in self.c.transport.requests if method == "turn/start"][-1]
        self.assertEqual(params["sandboxPolicy"]["writableRoots"],
                         [str(self.store.root), str(self.source)])


if __name__ == "__main__":
    unittest.main()
