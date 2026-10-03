"""Portable Studio project validation and public defaults."""
import re
from datetime import datetime, timezone
from uuid import uuid4

LANGUAGES = ("en", "ru", "es")
JOB_KINDS = ("illustration", "edit", "cubemap", "story-plan", "character-study",
             "location-study", "title-cover", "miniature", "coloring", "orbit-video")
ENTITY_KINDS = ("character", "location", "prop", "style", "panorama")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class StudioError(Exception):
    def __init__(self, message, code="invalid_request", status=400, details=None):
        super().__init__(message)
        self.message, self.code, self.status, self.details = message, code, status, details

    def payload(self):
        error = {"code": self.code, "message": self.message}
        if self.details is not None:
            error["details"] = self.details
        return {"error": error}


def now():
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix):
    return prefix + "-" + uuid4().hex[:20]


def valid_id(value, name="id"):
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise StudioError("Invalid " + name)
    return value


def empty_project():
    return {"id": "pinpin", "name": "Mr. PinPin", "book": {
        "title": {lang: "" for lang in LANGUAGES}, "manuscript": "", "arc": "",
        "continuity": "", "styleReferenceIds": []}, "entities": [], "chapters": [],
        "activeChapterId": None}


def empty_state():
    return {"schemaVersion": 1, "revision": 0, "project": empty_project(),
            "assets": [], "jobs": [], "storyboards": [], "events": [],
            "config": {"languages": list(LANGUAGES), "jobKinds": list(JOB_KINDS),
                       "panelsPerPage": [6, 12, 24], "maxUploadBytes": 40 * 1024 * 1024,
                       "generationMode": "queued-for-agent", "autoPublish": False}}


def find(items, identifier, kind="record"):
    for item in items:
        if item.get("id") == identifier:
            return item
    raise StudioError(kind + " not found", "not_found", 404)


def _unique(items, kind):
    if not isinstance(items, list):
        raise StudioError(kind + " must be an array")
    result = set()
    for item in items:
        if not isinstance(item, dict):
            raise StudioError(kind + " entries must be objects")
        identifier = valid_id(item.get("id"), kind + " id")
        if identifier in result:
            raise StudioError("Duplicate " + kind + " id: " + identifier)
        result.add(identifier)
    return result


def validate_project(project, assets):
    if not isinstance(project, dict):
        raise StudioError("project must be an object")
    valid_id(project.get("id", "pinpin"), "project id")
    if not isinstance(project.get("book", {}), dict):
        raise StudioError("book must be an object")
    entities = project.get("entities", [])
    chapters = project.get("chapters", [])
    entity_ids = _unique(entities, "entity")
    chapter_ids = _unique(chapters, "chapter")
    asset_ids = {a["id"] for a in assets}

    def references(values):
        if not isinstance(values, list):
            raise StudioError("referenceIds must be an array")
        if any(not isinstance(value, str) or value not in asset_ids for value in values):
            raise StudioError("Reference names an unregistered asset")

    references(project.get("book", {}).get("styleReferenceIds", []))
    for entity in entities:
        if entity.get("kind") not in ENTITY_KINDS:
            raise StudioError("Unknown entity kind")
        references(entity.get("referenceIds", []))
    active = project.get("activeChapterId")
    if active:
        valid_id(active, "active chapter id")
    if active and active not in chapter_ids:
        raise StudioError("Active chapter does not exist")
    for chapter in chapters:
        if chapter.get("coverAssetId"):
            references([chapter["coverAssetId"]])
        scenes = chapter.get("scenes", [])
        scene_ids = _unique(scenes, "scene")
        graph = {}
        for scene in scenes:
            deps = scene.get("dependsOn", [])
            if not isinstance(deps, list) or any(not isinstance(d, str) or d not in scene_ids for d in deps):
                raise StudioError("Scene dependency names an unknown scene")
            graph[scene["id"]] = deps
            for field in ("castIds", "propIds"):
                if not isinstance(scene.get(field, []), list) or any(
                        not isinstance(x, str) for x in scene.get(field, [])):
                    raise StudioError(field + " must be an array of IDs")
            used = scene.get("castIds", []) + scene.get("propIds", [])
            if scene.get("locationId"):
                valid_id(scene["locationId"], "location id")
                used += [scene["locationId"]]
            if any(e not in entity_ids for e in used):
                raise StudioError("Scene names an unknown entity")
            if scene.get("imageAssetId"):
                references([scene["imageAssetId"]])
            if not isinstance(scene.get("tempo", {}), dict):
                raise StudioError("tempo must be an object")
            if not isinstance(scene.get("camera", {}), dict):
                raise StudioError("camera must be an object")
            if not isinstance(scene.get("captions", {}), dict):
                raise StudioError("captions must be an object")
            for value in scene.get("captions", {}).values():
                if not isinstance(value, str) and not (
                        isinstance(value, list) and all(isinstance(x, str) for x in value)):
                    raise StudioError("Caption values must be text or arrays of text")
            for value in scene.get("tempo", {}).values():
                if isinstance(value, bool) or value not in (None, 1, 2, 3):
                    raise StudioError("Tempo values must be 1, 2, or 3")
        visiting, visited = set(), set()

        def walk(identifier):
            if identifier in visiting:
                raise StudioError("Scene dependencies contain a cycle", "causal_cycle")
            if identifier in visited:
                return
            visiting.add(identifier)
            for dependency in graph[identifier]:
                walk(dependency)
            visiting.remove(identifier)
            visited.add(identifier)
        for identifier in graph:
            walk(identifier)
    return project


def caption(scene, language):
    value = scene.get("captions", {}).get(language, "")
    return "\n".join(value) if isinstance(value, list) else str(value or "")
