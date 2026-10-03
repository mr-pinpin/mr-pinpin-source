"""Version-bound human approval of the complete preproduction plan."""
import hashlib
import json
from model import find, valid_id, now
from store import Store

SCENE_FIELDS = ("id", "title", "captions", "action", "dependsOn", "castIds", "locationId",
                "propIds", "camera", "stateBefore", "stateAfter", "tempo")
ENTITY_FIELDS = ("id", "name", "kind", "description", "identity", "scale", "geometry", "referenceIds")


def plan_hash(project, chapter):
    scenes = [{key: scene.get(key) for key in SCENE_FIELDS} for scene in chapter.get("scenes", [])]
    entity_ids = set(project.get("book", {}).get("styleEntityIds", []))
    for scene in scenes:
        entity_ids.update(scene.get("castIds") or [])
        entity_ids.update(scene.get("propIds") or [])
        if scene.get("locationId"):
            entity_ids.add(scene["locationId"])
    entities = [{key: entity.get(key) for key in ENTITY_FIELDS}
                for entity in project.get("entities", []) if entity["id"] in entity_ids]
    entities.sort(key=lambda entity: entity["id"])
    plan = {"chapterId": chapter["id"], "script": chapter.get("script", ""),
            "synopsis": chapter.get("synopsis", ""), "scenes": scenes, "entities": entities,
            "styleReferenceIds": project.get("book", {}).get("styleReferenceIds", [])}
    return hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def plan_status(project, chapter):
    sha = plan_hash(project, chapter)
    approval = chapter.get("studioPlanApproval")
    return {"chapterId": chapter["id"], "sha256": sha, "approval": approval,
            "approved": bool(approval and approval.get("scope") == "preproduction" and
                             approval.get("sha256") == sha)}


def approve_plan(store, body):
    state = store.read()
    project = state["project"]
    chapter = find(project["chapters"], valid_id(body.get("chapterId")), "chapter")
    chapter["studioPlanApproval"] = {"sha256": plan_hash(project, chapter), "approvedAt": now(),
                                    "baseRevision": state["revision"], "scope": "preproduction"}
    return store.save_project(project, body.get("expectedRevision"))
