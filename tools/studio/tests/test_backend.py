import copy
import io
import json
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import StudioError, empty_project
from store import Store, digest
from jobs import create_job, claim_job, complete_job, fail_job, review_job, inbox, reply
from boards import create_storyboard, review_storyboard
from server import StudioServer


def png(color):
    data = io.BytesIO()
    Image.new("RGB", (96, 64), color).save(data, "PNG")
    return data.getvalue()


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pinpin-studio-test-")
        self.root = Path(self.tmp.name)
        self.media = self.root / "allowed"
        self.media.mkdir()
        self.store = Store(self.root / "data", [self.media])
        self.first = self.store.upload_asset(png("red"), "first.png")[0]
        self.second = self.store.upload_asset(png("blue"), "second.png")[0]
        self.native = self.media / "native.png"
        self.native.write_bytes(png("green"))
        project = empty_project()
        project["book"].update(manuscript="The original manuscript", arc="An earned solution")
        project["entities"] = [
            {"id": "papa", "kind": "character", "name": "Papa", "referenceIds": [self.first["id"]]},
            {"id": "house", "kind": "location", "name": "House", "referenceIds": [self.second["id"]]},
            {"id": "sphere", "kind": "panorama", "name": "Seamless example", "referenceIds": [self.first["id"]]}]
        project["chapters"] = [{"id": "bath", "title": {"en": "A Bath", "ru": "Купание", "es": "El baño"},
            "script": "A chapter script", "synopsis": "An overflowing bath", "scenes": [
                {"id": "one", "title": "One", "captions": {"ru": "Папа несёт ведро.", "en": "Papa carries water."},
                 "castIds": ["papa"], "locationId": "house", "dependsOn": [], "imageAssetId": self.first["id"],
                 "action": "Carry the bucket", "status": "user-approved", "tempo": {"activity": 2}},
                {"id": "two", "title": "Two", "captions": {"en": "The water rises."},
                 "castIds": [], "dependsOn": ["one"], "imageAssetId": None}]}]
        project["activeChapterId"] = "bath"
        self.store.save_project(project, self.store.read()["revision"])

    def tearDown(self):
        self.tmp.cleanup()

    def job(self, **changes):
        request = {"kind": "illustration", "chapterId": "bath", "sceneIds": ["one"],
                   "instruction": "Improve this physical action"}
        request.update(changes)
        return create_job(self.store, request)[0]

    def test_revision_conflict_restart_and_project_history(self):
        state = self.store.read()
        old = copy.deepcopy(state["project"])
        changed = copy.deepcopy(old)
        changed["book"]["arc"] = "New arc"
        self.store.save_project(changed, state["revision"])
        with self.assertRaises(StudioError) as error:
            self.store.save_project(old, state["revision"])
        self.assertEqual(error.exception.status, 409)
        restarted = Store(self.root / "data")
        self.assertEqual(restarted.read()["project"]["book"]["arc"], "New arc")
        self.assertEqual(restarted.project_revision(state["revision"])["project"], old)
        self.assertEqual(len(restarted.read()["assets"]), 2)

    def test_causal_cycle_and_malformed_fields_rejected(self):
        state = self.store.read()
        project = copy.deepcopy(state["project"])
        project["chapters"][0]["scenes"][0]["dependsOn"] = ["two"]
        with self.assertRaises(StudioError) as error:
            self.store.save_project(project, state["revision"])
        self.assertEqual(error.exception.code, "causal_cycle")
        for field, value in (("book", None), ("entities", "wrong")):
            bad = copy.deepcopy(state["project"])
            bad[field] = value
            with self.assertRaises(StudioError):
                self.store.save_project(bad, state["revision"])
        bad = copy.deepcopy(state["project"])
        bad["chapters"][0]["scenes"][0]["castIds"] = "papa"
        with self.assertRaises(StudioError):
            self.store.save_project(bad, state["revision"])

    def test_registered_media_and_symlink_containment(self):
        outside = self.root / "outside.png"
        outside.write_bytes(png("orange"))
        (self.media / "escape.png").symlink_to(outside)
        with self.assertRaises(StudioError) as error:
            self.store.import_asset(self.media / "escape.png")
        self.assertEqual(error.exception.status, 403)
        imported = self.store.import_asset(self.native)
        self.assertEqual(self.store.asset_path(imported["id"]).read_bytes(), self.native.read_bytes())
        with self.assertRaises(StudioError):
            self.store.asset_path("../../outside.png")
        with self.assertRaises(StudioError):
            self.store.upload_asset(b"not an image", "fake.png")

    def test_reference_deduplication_and_type_specific_context(self):
        state = self.store.read()
        project = state["project"]
        project["book"]["styleReferenceIds"] = [self.first["id"]]
        self.store.save_project(project, state["revision"])
        job = self.job()
        binding = next(b for b in job["referenceBindings"] if b["assetId"] == self.first["id"])
        self.assertEqual(set(binding["roles"]), {"character-identity", "book-style", "current-scene"})
        self.assertEqual(len(job["referenceBindings"]), 2)
        self.assertNotIn("The original manuscript", job["prompt"])
        self.assertEqual(job["snapshot"]["causalContext"][0]["id"], "two")
        plan = self.job(kind="story-plan")
        self.assertIn("The original manuscript", plan["prompt"])
        self.assertIn("A chapter script", plan["prompt"])

    def test_cubemap_requires_distinct_role_bound_inputs(self):
        with self.assertRaises(StudioError):
            self.job(kind="cubemap", chapterId=None, sceneIds=[], referenceBindings=[
                {"assetId": self.first["id"], "role": "seamless-panorama"},
                {"assetId": self.first["id"], "role": "location-identity"}])
        job = self.job(kind="cubemap", entityId="sphere")
        self.assertEqual(job["status"], "queued")
        self.assertIn("one continuous 2:1", job["prompt"])

    def test_claim_race_and_owner(self):
        job = self.job()
        def attempt(agent):
            try:
                claim_job(self.store, job["id"], agent)
                return agent
            except StudioError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            winners = [x for x in pool.map(attempt, ("alpha", "beta")) if x]
        self.assertEqual(len(winners), 1)
        with self.assertRaises(StudioError):
            complete_job(self.store, job["id"], "outsider", image=self.native)

    def test_native_candidate_actual_prompt_approve_and_reject_rollback(self):
        job = self.job()
        claim_job(self.store, job["id"], "codex")
        done = complete_job(self.store, job["id"], "codex", image=self.native,
            actual_prompt="The exact submitted image edit", used_job_references=True,
            tool_name="image_gen__imagegen", visual_pass=True)[0]
        artifact = done["artifacts"][0]
        self.assertEqual(artifact["reviewStatus"], "candidate")
        self.assertNotEqual(artifact["actualPromptSha256"], artifact["handoffPromptSha256"])
        self.assertEqual(artifact["sha256"], digest(self.native.read_bytes()))
        self.assertEqual(self.store.read()["project"]["chapters"][0]["scenes"][0]["imageAssetId"], self.first["id"])
        review_job(self.store, job["id"], {"decision": "approve", "artifactId": artifact["id"]})
        scene = self.store.read()["project"]["chapters"][0]["scenes"][0]
        self.assertEqual(scene["imageAssetId"], artifact["assetId"])
        self.assertEqual(scene["imageHistory"][0]["previousAssetId"], self.first["id"])
        review_job(self.store, job["id"], {"decision": "reject", "artifactId": artifact["id"]})
        self.assertEqual(self.store.read()["project"]["chapters"][0]["scenes"][0]["imageAssetId"], self.first["id"])

    def test_entity_rejection_removes_newly_approved_reference(self):
        job = self.job(chapterId=None, sceneIds=[], entityId="papa", kind="character-study")
        claim_job(self.store, job["id"], "codex")
        artifact = complete_job(self.store, job["id"], "codex", image=self.native)[0]["artifacts"][0]
        self.assertEqual(artifact["actualPromptStatus"], "unknown")
        review_job(self.store, job["id"], {"decision": "approve", "artifactId": artifact["id"]})
        review_job(self.store, job["id"], {"decision": "reject", "artifactId": artifact["id"]})
        self.assertEqual(self.store.read()["project"]["entities"][0]["referenceIds"], [self.first["id"]])

    def test_text_artifact_fail_and_feedback_inbox(self):
        job = self.job(kind="story-plan")
        claim_job(self.store, job["id"], "codex")
        done = complete_job(self.store, job["id"], "codex", text="A revised scene plan")[0]
        self.assertEqual(done["artifacts"][0]["type"], "text")
        reviewed = review_job(self.store, job["id"], {"decision": "feedback", "feedback": "More action"})[0]
        feedback = reviewed["feedback"][0]
        self.assertEqual(inbox(self.store)["unresolvedFeedback"][0]["id"], feedback["id"])
        reply(self.store, job["id"], "codex", "I expanded the action", feedback["id"])
        self.assertEqual(inbox(self.store)["unresolvedFeedback"], [])
        failed = self.job()
        claim_job(self.store, failed["id"], "codex")
        self.assertEqual(fail_job(self.store, failed["id"], "codex", "Tool unavailable")[0]["status"], "failed")

    def test_storyboard_snapshot_placeholder_and_panel_feedback(self):
        board = create_storyboard(self.store, {"chapterId": "bath", "language": "ru", "panelsPerPage": 6})[0]
        page = board["pages"][0]
        self.assertEqual(page["panels"][0]["caption"], "Папа несёт ведро.")
        self.assertIsNone(page["panels"][1]["imageAssetId"])
        original = self.store.asset_path(page["assetId"]).read_bytes()
        Image.open(io.BytesIO(original)).verify()
        state = self.store.read()
        state["project"]["chapters"][0]["scenes"][0]["captions"]["ru"] = "Другой текст"
        self.store.save_project(state["project"], state["revision"])
        self.assertEqual(original, self.store.asset_path(page["assetId"]).read_bytes())
        reviewed = review_storyboard(self.store, board["id"], {"pageId": page["id"],
            "sceneId": "two", "decision": "feedback", "feedback": "Add a reaction"})[0]
        feedback = reviewed["pages"][0]["feedback"][0]
        self.assertEqual(inbox(self.store)["unresolvedFeedback"][0]["targetType"], "storyboard")
        reply(self.store, board["id"], "codex", "Reaction added", feedback["id"])
        self.assertFalse(inbox(self.store)["unresolvedFeedback"])

    def test_http_conflict_upload_origin_and_traversal(self):
        server = StudioServer(("127.0.0.1", 0), self.store)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        def request(path, method="GET", body=None, headers=None):
            headers = headers or {}
            if isinstance(body, dict):
                body = json.dumps(body).encode()
                headers["Content-Type"] = "application/json"
            try:
                with urlopen(Request(base + path, data=body, method=method, headers=headers)) as response:
                    return response.status, response.read()
            except HTTPError as error:
                return error.code, error.read()
        try:
            state = json.loads(request("/api/state")[1])
            code, _ = request("/api/state", "PUT", {"expectedRevision": state["revision"] - 1, "project": state["project"]})
            self.assertEqual(code, 409)
            self.assertEqual(request("/api/assets", "POST", png("yellow"),
                                     {"Origin": "https://untrusted.example", "Content-Type": "image/png"})[0], 403)
            code, raw = request("/api/assets", "POST", png("yellow"), {"Content-Type": "image/png", "X-File-Name": "yellow.png"})
            self.assertEqual(code, 201)
            self.assertEqual(request(json.loads(raw)["asset"]["url"])[0], 200)
            self.assertEqual(request("/api/assets/%2e%2e%2fstate.json")[0], 403)
            self.assertEqual(request("/api/assets/not-registered")[0], 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
