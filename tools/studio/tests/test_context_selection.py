"""Selection-based compact context without changing Store or native attachments."""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from business.context import selected_context
import test_backend as fixtures


def envelope(inputs):
    return json.loads(inputs[0]["text"].split("\n", 1)[1].split("\n\nUser message:", 1)[0])


class ContextSelectionTests(unittest.TestCase):
    setUp = fixtures.BackendTests.setUp
    tearDown = fixtures.BackendTests.tearDown

    def large_chapter(self):
        state = self.store.read()
        chapter = state["project"]["chapters"][0]
        template = chapter["scenes"][0]
        chapter["script"] = "FULL SCRIPT MUST REMAIN IN STORE " * 450
        chapter["synopsis"] = "Summary " * 300
        chapter["continuity"] = "Continuity " * 300
        chapter["scenes"] = [dict(copy.deepcopy(template), id=f"scene-{i:03}",
                                 action=f"Action {i:03} " * 25)
                             for i in range(215)]
        self.store.save_project(state["project"], state["revision"])
        return self.store.read()["project"]["chapters"][0]

    def test_short_message_large_chapter_is_compact_and_store_unchanged(self):
        chapter = self.large_chapter()
        before = self.store.read()
        _, scope, inputs = selected_context(self.store, {
            "text": "Continue", "chapterId": chapter["id"], "sceneIds": [], "assetIds": []})
        context = envelope(inputs)
        summary = context["chapter"]
        self.assertEqual(summary["sceneCount"], 215)
        self.assertEqual(len(summary["sceneIndexPreview"]), 5)
        self.assertLessEqual(len(summary["synopsis"]), 1200)
        self.assertLessEqual(len(summary["continuity"]), 1200)
        self.assertNotIn("script", summary)
        self.assertNotIn("sceneIndex", summary)
        self.assertNotIn("FULL SCRIPT MUST REMAIN IN STORE", inputs[0]["text"])
        self.assertNotIn("scene-214", inputs[0]["text"])
        self.assertIn("state_at_revision(store, projectRevision)", summary["details"])
        self.assertLess(len(inputs[0]["text"].encode()), 8000)
        self.assertEqual(scope["assetIds"], [])
        self.assertEqual(len(inputs), 1)
        self.assertEqual(self.store.read(), before)
        # No task classification: only explicit selection controls the same context.
        other = selected_context(self.store, {"text": "Generate an illustration", "chapterId": chapter["id"]})[2]
        self.assertEqual(envelope(other), context)

    def test_selected_scene_and_explicit_native_attachment_remain_exact(self):
        chapter = self.large_chapter()
        state = self.store.read()
        selected = state["project"]["chapters"][0]["scenes"][100]
        selected["action"] = "Do not truncate selected staging. " * 500
        self.store.save_project(state["project"], state["revision"])
        before = self.store.read()
        expected = before["project"]["chapters"][0]["scenes"][100]
        _, scope, inputs = selected_context(self.store, {
            "text": "Review selected scene", "chapterId": chapter["id"], "sceneIds": [selected["id"]],
            "assetIds": [self.second["id"], self.second["id"]]})
        context = envelope(inputs)
        self.assertEqual(context["scenes"], [expected])
        self.assertEqual(context["chapter"]["sceneCount"], 215)
        self.assertEqual(len(context["chapter"]["adjacentScenes"]), 2)
        self.assertEqual(scope["assetIds"], [self.second["id"]])
        self.assertEqual(inputs[1:], [{"type": "localImage",
                                     "path": str(self.store.asset_path(self.second["id"]))}])
        self.assertIn(self.first["id"], [a["id"] for a in context["references"]])
        self.assertEqual(self.store.read(), before)


if __name__ == "__main__":
    unittest.main()
