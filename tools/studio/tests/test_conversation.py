import copy
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_backend as fixtures
from conversation import Conversation
from conversation_context import selected_context
from conversation_plan import approve_plan, plan_status
from model import StudioError
from store import atomic_json


class FakeTransport:
    """Protocol fixture only: no production fallback ever uses this."""
    def __init__(self, notify, cwd):
        self.notify = notify
        self.process = self
        self.closed = False
        self.requests = []
    def poll(self):
        return 0 if self.closed else None
    def request(self, method, params):
        self.requests.append((method, params))
        if method in ("thread/start", "thread/resume"):
            return {"thread": {"id": "fixture-thread"}, "model": "fixture"}
        if method == "turn/start":
            return {"turn": {"id": "fixture-turn"}}
        if method == "turn/interrupt":
            self.notify("turn/completed", {"turn": {"id": "fixture-turn", "status": "interrupted"}})
        return {}
    def close(self):
        self.closed = True


class ConversationTests(unittest.TestCase):
    setUp = fixtures.BackendTests.setUp
    tearDown = fixtures.BackendTests.tearDown

    def wait_running(self, conversation):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if conversation.snapshot()["conversation"]["status"] != "connecting":
                return
            time.sleep(.01)
        self.fail("Fixture did not start")

    def test_context_registered_images_scope_and_no_full_manuscript(self):
        text, scope, inputs = selected_context(self.store, {
            "text": "Review framing", "chapterId": "bath", "sceneIds": ["one"]})
        self.assertEqual(scope["projectRevision"], self.store.read()["revision"])
        self.assertEqual(scope["assetIds"][0], self.first["id"])
        self.assertEqual(inputs[1]["type"], "localImage")
        self.assertNotIn("The original manuscript", inputs[0]["text"])
        self.assertNotIn('"scenes": [{"id": "one"', inputs[0]["text"].split('"chapter": ')[1].split('"scenes":')[0])
        for bad in ({"sceneIds": ["missing"], "chapterId": "bath"},
                    {"assetIds": ["../../secret"]}, {"assetIds": ["missing"]},
                    {"sceneIds": "one"}, {"text": ""}):
            with self.assertRaises(StudioError):
                selected_context(self.store, {"text": "test", **bad})

    def test_full_plan_approval_invalidated_by_geometry_not_output(self):
        state = self.store.read()
        approved = approve_plan(self.store, {"chapterId": "bath", "expectedRevision": state["revision"]})
        project = approved["project"]
        chapter = project["chapters"][0]
        self.assertTrue(plan_status(project, chapter)["approved"])
        chapter["scenes"][0]["imageAssetId"] = self.second["id"]
        chapter["scenes"][0]["status"] = "candidate"
        self.assertTrue(plan_status(project, chapter)["approved"])
        chapter["scenes"][0]["camera"] = {"yaw": 45}
        self.assertFalse(plan_status(project, chapter)["approved"])
        chapter["scenes"][0].pop("camera")
        self.assertTrue(plan_status(project, chapter)["approved"])
        project["entities"][0]["scale"] = "twice as tall"
        self.assertFalse(plan_status(project, chapter)["approved"])
        with self.assertRaises(StudioError):
            approve_plan(self.store, {"chapterId": "bath", "expectedRevision": state["revision"]})

    def test_stream_cursor_usage_interrupt_and_restart_persistence(self):
        c = Conversation(self.store, FakeTransport)
        c.send({"text": "hello", "chapterId": "bath"})
        self.wait_running(c)
        with self.assertRaises(StudioError) as busy:
            c.send({"text": "second"})
        self.assertEqual(busy.exception.code, "conversation_busy")
        c.notify("item/agentMessage/delta", {"threadId": "fixture-thread", "turnId": "fixture-turn",
                                           "itemId": "reply", "delta": "Hello"})
        cursor = c.snapshot()["cursor"]
        c.notify("item/agentMessage/delta", {"itemId": "reply", "delta": " world", "turnId": "fixture-turn"})
        c.notify("thread/tokenUsage/updated", {"tokenUsage": {"total": {"totalTokens": 123}}})
        c.notify("item/completed", {"item": {"id": "cmd", "type": "commandExecution",
                                          "aggregatedOutput": "SECRET", "command": "TOKEN=SECRET"}})
        snapshot = c.snapshot(cursor)
        self.assertEqual(snapshot["conversation"]["messages"][-1]["text"], "Hello world")
        self.assertTrue(all(e["seq"] > cursor for e in snapshot["events"]))
        self.assertNotIn("SECRET", json.dumps(snapshot))
        c.interrupt()
        self.assertEqual(c.snapshot()["conversation"]["status"], "interrupted")
        c.close()
        restarted = Conversation(self.store, FakeTransport)
        self.assertEqual(restarted.snapshot()["conversation"]["messages"][-1]["text"], "Hello world")
        restarted.send({"text": "continue"})
        self.wait_running(restarted)
        self.assertEqual(restarted.transport.requests[0][0], "thread/resume")
        restarted.close()

    def test_restarted_active_turn_and_honest_unavailable(self):
        c = Conversation(self.store, FakeTransport)
        c.state["status"] = "running"
        c._save()
        restarted = Conversation(self.store, FakeTransport)
        self.assertEqual(restarted.snapshot()["conversation"]["status"], "interrupted")
        def unavailable(*args):
            raise RuntimeError("PRIVATE SECRET")
        failed = Conversation(self.store, unavailable)
        failed.send({"text": "hello"})
        self.wait_running(failed)
        snapshot = failed.snapshot()
        self.assertEqual(snapshot["conversation"]["status"], "error")
        self.assertEqual(len(snapshot["conversation"]["messages"]), 1)
        self.assertNotIn("PRIVATE", json.dumps(snapshot))
        failed.close()


    def test_http_poll_origin_plan_and_range(self):
        from server import StudioServer
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        server = StudioServer(("127.0.0.1", 0), self.store)
        server.conversation.transport_factory = FakeTransport
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        def request(path, body=None, headers=None):
            return urlopen(Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                   headers={"Content-Type": "application/json", **(headers or {})}))
        try:
            with request("/api/conversation") as response:
                self.assertEqual(json.load(response)["conversation"]["status"], "idle")
            with self.assertRaises(HTTPError) as forbidden:
                request("/api/conversation/messages", {"text": "hello"}, {"Origin": "https://evil.example"})
            self.assertEqual(forbidden.exception.code, 403)
            forbidden.exception.close()
            with request("/api/conversation/messages", {"text": "hello"}) as response:
                self.assertEqual(response.status, 202)
            self.wait_running(server.conversation)
            with request("/api/conversation/interrupt", {}) as response:
                self.assertEqual(json.load(response)["conversation"]["status"], "interrupted")
            with request("/api/plan/approve", {"chapterId": "bath",
                         "expectedRevision": self.store.read()["revision"]}) as response:
                self.assertIn("studioPlanApproval", json.load(response)["project"]["chapters"][0])
            with request("/api/plan?chapterId=bath") as response:
                self.assertTrue(json.load(response)["approved"])
            with patch("media_library.media_file", return_value=(self.native, "image/png", "hash")):
                with request("/api/media/files/test", headers={"Range": "bytes=2-8"}) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.read(), self.native.read_bytes()[2:9])
                with self.assertRaises(HTTPError) as invalid:
                    request("/api/media/files/test", headers={"Range": "bytes=999999-"})
                self.assertEqual(invalid.exception.code, 416)
                invalid.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
