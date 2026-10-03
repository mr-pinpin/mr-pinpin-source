import copy
import json
import os
import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from immutable_bundle import BundleError, MANIFEST, bundle_hash, capture, verify_bundle
from workspace_runtime import WorkspaceRuntime
from release import freeze
from review_state import state_at_revision
from conversation import Conversation
from conversation_context import selected_context, instructions
from model import StudioError, empty_project
from server import StudioServer
from store import Store
import test_conversation as conversation_fixtures


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pinpin-runtime-test-")
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "workspace-dev"
        self.source.mkdir()
        (self.source / "index.html").write_text('<html><script type="module" src="./main.js"></script></html>')
        (self.source / "main.js").write_text('export const greeting = "first";')
        self.artifacts = self.root / "runtime"
        self.store = Store(self.root / "data")
        project = empty_project()
        project["chapters"] = [{"id": "test", "title": {"en": "Test"}, "script": "original",
                                "synopsis": "", "scenes": [{"id": "scene", "action": "original action"}]}]
        self.store.save_project(project, 0)

    def tearDown(self):
        for directory, dirs, names in os.walk(self.root):
            Path(directory).chmod(0o755)
            for name in names:
                if not (Path(directory) / name).is_symlink():
                    (Path(directory) / name).chmod(0o644)
        self.temp.cleanup()

    def runtime(self):
        return WorkspaceRuntime(self.source, self.artifacts, "stable-test", watch=False)

    def test_hash_immutable_last_good_and_no_build_scripts_executed(self):
        marker = self.root / "must-not-exist"
        (self.source / "package.json").write_text(json.dumps({"scripts": {"build": "touch " + str(marker)}}))
        (self.source / "main.js").write_text('throw new Error("must not execute"); export const value=1;')
        runtime = self.runtime()
        first = runtime.snapshot()["workspace"]["latest"]
        first_bytes = runtime.file(first, "main.js")[0].read_bytes()
        self.assertFalse(marker.exists())
        self.assertEqual(runtime.snapshot()["workspace"]["status"], "ready")
        (self.source / "main.js").write_text('export const value=2;')
        runtime.poll(force=True)
        second = runtime.snapshot()["workspace"]["latest"]
        self.assertNotEqual(first, second)
        self.assertEqual(runtime.snapshot()["workspace"]["previous"], first)
        self.assertEqual(runtime.file(first, "main.js")[0].read_bytes(), first_bytes)
        self.assertEqual(runtime.file(first, "main.js")[0].stat().st_mode & 0o222, 0)
        (self.source / "main.js").write_text('export const = syntax error;')
        runtime.poll(force=True)
        self.assertEqual(runtime.snapshot()["workspace"]["latest"], second)
        self.assertEqual(runtime.snapshot()["workspace"]["status"], "error")
        self.assertIn("main.js", runtime.snapshot()["workspace"]["error"]["message"])
        self.assertEqual(len(runtime.releases()["releases"]), 2)
        resumed = self.runtime()
        self.assertEqual(resumed.snapshot()["workspace"]["latest"], second)

    def test_debounce_and_source_symlinks_rejected(self):
        runtime = self.runtime()
        first = runtime.snapshot()["workspace"]["latest"]
        (self.source / "main.js").write_text('export const version=2;')
        runtime.poll()
        self.assertEqual(runtime.snapshot()["workspace"]["latest"], first)
        runtime.candidate_since -= 1
        runtime.poll()
        second = runtime.snapshot()["workspace"]["latest"]
        self.assertNotEqual(first, second)
        outside = self.root / "secret.js"
        outside.write_text("private")
        (self.source / "escape.js").symlink_to(outside)
        runtime.poll(force=True)
        self.assertEqual(runtime.snapshot()["workspace"]["latest"], second)
        self.assertEqual(runtime.snapshot()["workspace"]["status"], "error")
        with self.assertRaises(BundleError):
            capture(self.source)

    def test_workspace_traversal_and_tamper_rejected(self):
        runtime = self.runtime()
        sha = runtime.snapshot()["workspace"]["latest"]
        for relative in ("../../secret", "/etc/passwd", MANIFEST, "AGENTS.md"):
            with self.assertRaises(StudioError):
                runtime.file(sha, relative)
        path = runtime.file(sha, "main.js")[0]
        path.chmod(0o644)
        path.write_text("changed")
        with self.assertRaises(StudioError) as error:
            runtime.file(sha, "main.js")
        self.assertEqual(error.exception.code, "storage_corruption")

    def test_stable_release_snapshot_untouched_by_source_changes(self):
        stable = self.root / "stable-source"
        (stable / "web").mkdir(parents=True)
        (stable / "server.py").write_text("# stable server")
        (stable / "conversation.py").write_text("# stable conversation")
        (stable / "web/index.html").write_text("<h1>stable shell</h1>")
        release = freeze(stable, self.artifacts)
        frozen = Path(release["path"])
        (stable / "server.py").write_text("# edited mutable source")
        self.assertEqual((frozen / "server.py").read_text(), "# stable server")
        self.assertEqual(verify_bundle(frozen)["hash"], release["stableRelease"])
        self.assertEqual(frozen.stat().st_mode & 0o222, 0)
        again = freeze(stable, self.artifacts)
        self.assertNotEqual(again["stableRelease"], release["stableRelease"])
        self.assertEqual((frozen / "server.py").read_text(), "# stable server")

    def test_revision_view_and_conversation_use_same_historical_project(self):
        initial = self.store.read()
        original = copy.deepcopy(initial["project"])
        self.store.mutate(lambda state: Store.event(state, "test.nonproject"))
        requested = self.store.read()["revision"]
        latest = self.store.read()
        latest["project"]["chapters"][0]["scenes"][0]["action"] = "later action"
        self.store.save_project(latest["project"], latest["revision"])
        historical = state_at_revision(self.store, requested)
        self.assertEqual(historical["project"], original)
        self.assertEqual(historical["revision"], initial["revision"])
        self.assertEqual(historical["review"]["requestedRevision"], requested)
        self.assertTrue(historical["readOnly"])
        text, scope, inputs = selected_context(self.store, {"text": "review",
            "projectRevision": requested, "chapterId": "test", "sceneIds": ["scene"]})
        self.assertTrue(scope["reviewSnapshot"])
        self.assertIn("original action", inputs[0]["text"])
        self.assertNotIn("later action", inputs[0]["text"])
        for invalid in (-1, True, "1", 999):
            with self.assertRaises(StudioError):
                state_at_revision(self.store, invalid)

    def test_agent_ui_scope_and_pinned_readonly_resume_each_turn(self):
        c = Conversation(self.store, conversation_fixtures.FakeTransport, self.source)
        try:
            c.send({"text": "Improve the workspace UI"})
            conversation_fixtures.ConversationTests.wait_running(self, c)
            params = [params for method, params in c.transport.requests if method == "turn/start"][-1]
            self.assertEqual(params["sandboxPolicy"]["writableRoots"], [str(self.store.root), str(self.source)])
            guidance = c.transport.requests[0][1]["developerInstructions"]
            self.assertIn(str(self.source), guidance)
            self.assertIn("UI edits do NOT require", guidance)
            self.assertNotIn(str(self.artifacts), params["sandboxPolicy"]["writableRoots"])
            c.notify("turn/completed", {"turn": {"status": "completed", "id": "fixture-turn"}})
            c.send({"text": "Review original", "projectRevision": 1})
            conversation_fixtures.ConversationTests.wait_running(self, c)
            requests = c.transport.requests
            self.assertEqual([method for method, params in requests].count("thread/resume"), 1)
            params = [params for method, params in requests if method == "turn/start"][-1]
            self.assertEqual(params["sandboxPolicy"]["type"], "readOnly")
            guidance = [params for method, params in requests if method == "thread/resume"][-1]["developerInstructions"]
            self.assertIn("READ-ONLY PINNED REVIEW", guidance)
        finally:
            c.close()

    def test_http_runtime_cors_only_builds_and_review_snapshot(self):
        from conversation_plan import approve_plan
        approved = approve_plan(self.store, {"chapterId": "test", "expectedRevision": 1})
        approved["project"]["chapters"][0]["script"] = "changed later"
        self.store.save_project(approved["project"], approved["revision"])
        server = StudioServer(("127.0.0.1", 0), self.store, workspace_source=self.source,
                              runtime_dir=self.artifacts)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        try:
            with urlopen(base + "/api/runtime") as response:
                self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
                runtime = json.load(response)
            url = runtime["workspace"]["url"]
            with urlopen(Request(base + url, headers={"Origin": "null"})) as response:
                self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
                self.assertIn("immutable", response.headers["Cache-Control"])
            with urlopen(base + "/api/runtime/releases/list") as response:
                self.assertEqual(len(json.load(response)["releases"]), 1)
            with urlopen(base + "/api/state?revision=1") as response:
                self.assertTrue(json.load(response)["readOnly"])
                self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
            with urlopen(base + "/api/plan?chapterId=test&revision=2") as response:
                plan = json.load(response)
                self.assertTrue(plan["approved"])
                self.assertTrue(plan["readOnly"])
            with urlopen(base + "/api/plan?chapterId=test") as response:
                self.assertFalse(json.load(response)["approved"])
            bad = url.rsplit("/", 1)[0] + "/%2e%2e/server.py"
            with self.assertRaises(HTTPError) as error:
                urlopen(base + bad)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_artifacts_cannot_live_under_agent_writable_roots(self):
        with self.assertRaises(ValueError):
            StudioServer(("127.0.0.1", 0), self.store, workspace_source=self.source,
                         runtime_dir=self.store.root / "runtime")
        with self.assertRaises(ValueError):
            StudioServer(("127.0.0.1", 0), self.store, workspace_source=self.source,
                         runtime_dir=self.source / "runtime")


if __name__ == "__main__":
    unittest.main()
