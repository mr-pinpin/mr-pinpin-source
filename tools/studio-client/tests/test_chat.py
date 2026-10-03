import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CLI = Path(__file__).resolve().parents[1] / "chat.py"


class Fixture(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self, code, value):
        body = json.dumps(value).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.server.gets += 1
        index = min(self.server.gets - 1, len(self.server.snapshots) - 1)
        self.respond(200, self.server.snapshots[index])

    def do_POST(self):
        self.server.posts.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        if self.server.busy:
            return self.respond(409, {"error": {"code": "conversation_busy", "message": "An agent turn is active."}})
        if self.server.drop:
            self.close_connection = True
            return
        value = snapshot("connecting")
        value["conversation"]["messages"] = [{"id": "user-1", "role": "user", "text": self.server.posts[-1]["text"].strip(), "turnId": None}]
        self.respond(202, value)


def snapshot(status="completed", phase="final_answer", later=False):
    running = status in ("running", "connecting")
    messages = [{"id": "user-1", "role": "user", "text": "saved", "turnId": None if status == "connecting" else "turn-1"}]
    if status != "connecting":
        messages.append({"id": "answer-1", "role": "assistant", "text": "reply", "turnId": "turn-1", "phase": phase, "status": "completed"})
    if later:
        messages.append({"id": "user-2", "role": "user", "text": "next", "turnId": "turn-2"})
    return {"conversation": {"id": "studio", "threadId": "same-thread", "status": status, "activeTurnId": "turn-2" if later else ("turn-1" if running else None), "messages": messages}, "cursor": 5, "events": []}


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
        self.server.posts, self.server.gets = [], 0
        self.server.busy = self.server.drop = False
        self.server.snapshots = [snapshot()]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:" + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def call(self, *args):
        result = subprocess.run([sys.executable, str(CLI), *args, "--url", self.url, "--json"], text=True, capture_output=True, timeout=5)
        return result.returncode, json.loads(result.stdout)

    def test_status_read_same_thread(self):
        code, status = self.call("status")
        self.assertEqual((code, status["threadId"], status["messageCount"]), (0, "same-thread", 2))
        code, read = self.call("read", "--limit", "1", "--after", "4")
        self.assertEqual(len(read["messages"]), 1)
        self.assertEqual(read["messages"][0]["role"], "assistant")
        self.assertEqual(self.server.posts, [])
        self.server.snapshots[0]["events"] = [{"delta": "x" * 100000}]
        _, bounded = self.call("read", "--limit", "1")
        self.assertNotIn("events", bounded)
        self.assertLess(len(json.dumps(bounded)), 1000)
        _, events = self.call("read", "--limit", "1", "--after", "4")
        self.assertEqual(len(events["events"]), 1)

    def test_file_send_visible_attribution_and_context(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "message.txt"
            path.write_text("Keep this exact.\nСпасибо.\n", encoding="utf-8")
            code, receipt = self.call("send", "--actor", "codex-wap1", "--on-behalf-of", "Miguel", "--message-file", str(path), "--chapter", "bath", "--scene", "scene-1", "--entity", "pompom", "--asset", "asset-1", "--revision", "3")
        self.assertEqual(code, 0)
        self.assertEqual(receipt["messageId"], "user-1")
        self.assertTrue(receipt["accepted"])
        self.assertGreaterEqual(receipt["httpAcceptSeconds"], 0)
        self.assertIn("T", receipt["requestStartedAt"])
        body = self.server.posts[0]
        self.assertEqual(body["text"], "[fleet-msg from codex-wap1]\n[Actor: codex-wap1; on behalf of: Miguel]\n\nKeep this exact.\nСпасибо.")
        self.assertEqual(body["projectRevision"], 3)
        self.assertEqual(body["sceneIds"], ["scene-1"])
        self.assertEqual(len(self.server.posts), 1)

    def test_busy_is_distinct_and_never_retries(self):
        self.server.busy = True
        code, result = self.call("send", "--actor", "claude", "--text", "hello")
        self.assertEqual(code, 3)
        self.assertEqual(result["error"]["code"], "conversation_busy")
        self.assertEqual(len(self.server.posts), 1)

    def test_lost_send_response_not_replayed(self):
        self.server.drop = True
        code, result = self.call("send", "--actor", "human", "--text", "hello")
        self.assertEqual(code, 1)
        self.assertTrue(result["outcomeUnknown"])
        self.assertEqual(len(self.server.posts), 1)

    def test_wait_passes_completed_commentary_until_turn_finishes(self):
        self.server.snapshots = [snapshot("connecting"), snapshot("running", "commentary"), snapshot()]
        code, result = self.call("wait", "--message-id", "user-1", "--timeout", "2", "--poll", ".25")
        self.assertEqual(code, 0)
        self.assertEqual(result["outcome"], "completed")
        self.assertEqual(self.server.gets, 3)

    def test_wait_timeout_bounded_without_send(self):
        self.server.snapshots = [snapshot("running")]
        started = time.monotonic()
        code, result = self.call("wait", "--message-id", "user-1", "--timeout", ".3", "--poll", ".25")
        self.assertEqual(code, 4)
        self.assertEqual(result["receipt"]["messageId"], "user-1")
        self.assertLess(time.monotonic() - started, 1.5)
        self.assertEqual(self.server.posts, [])

    def test_wait_failure_not_success(self):
        self.server.snapshots = [snapshot("error")]
        code, result = self.call("wait", "--message-id", "user-1")
        self.assertEqual(code, 1)
        self.assertEqual(result["error"]["code"], "turn_error")

    def test_old_turn_completion_while_new_turn_runs(self):
        self.server.snapshots = [snapshot("running", later=True)]
        code, result = self.call("wait", "--message-id", "user-1")
        self.assertEqual(code, 0)
        self.assertEqual(result["outcome"], "completed")

    def test_measure_command_capture_and_resume_are_read_only(self):
        value = snapshot()
        value["conversation"]["messages"][0]["createdAt"] = "2026-10-03T09:30:00+00:00"
        value["conversation"]["messages"][1]["createdAt"] = "2026-10-03T09:30:02+00:00"
        value["events"] = [{"seq":1,"type":"message","messageId":"user-1","createdAt":"2026-10-03T09:30:00+00:00"},
                           {"seq":2,"type":"message","messageId":"answer-1","createdAt":"2026-10-03T09:30:03+00:00"},
                           {"seq":3,"type":"status","status":"completed","createdAt":"2026-10-03T09:30:04+00:00"}]
        self.server.snapshots = [value]
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder)/"capture.json")
            code,result = self.call("measure","--message-id","user-1","--capture-file",path)
            self.assertEqual(code,0,result)
            self.assertEqual(result["totalSeconds"],4)
            self.assertEqual(result["finalMessageIds"],["answer-1"])
            code,resumed = self.call("measure","--message-id","user-1","--capture-file",path,"--once")
            self.assertEqual(code,0,resumed)
            self.assertEqual(resumed["totalSeconds"],4)
            self.assertNotIn('"text"',Path(path).read_text())
        self.assertEqual(self.server.posts, [])

    def test_send_wait_timeout_keeps_send_receipt(self):
        self.server.snapshots = [snapshot("running")]
        code, result = self.call("send", "--actor", "codex", "--text", "hello", "--wait", "--timeout", ".3", "--poll", ".25")
        self.assertEqual(code, 4)
        self.assertTrue(result["sendReceipt"]["accepted"])
        self.assertEqual(len(self.server.posts), 1)


if __name__ == "__main__":
    unittest.main()
