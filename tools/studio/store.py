"""Atomic external-data store. No production media lives in the Git checkout."""
import copy
import fcntl
import hashlib
import io
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from model import StudioError, empty_state, now, new_id, find, validate_project

MAX_UPLOAD = 40 * 1024 * 1024
FORMATS = {"PNG": ("image/png", ".png"), "JPEG": ("image/jpeg", ".jpg"),
           "WEBP": ("image/webp", ".webp")}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".studio-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


class Store:
    def __init__(self, data_dir, media_roots=None):
        self.root = Path(data_dir).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "state.json"
        for name in ("assets", "jobs", "storyboards", "history"):
            (self.root / name).mkdir(exist_ok=True)
        with self.lock():
            settings_path = self.root / "settings.json"
            settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
            roots = settings.get("mediaRoots", [])
            for root in media_roots or []:
                resolved = str(Path(root).expanduser().resolve())
                if resolved not in roots:
                    roots.append(resolved)
            self.media_roots = [Path(p) for p in roots]
            atomic_json(settings_path, {"mediaRoots": roots})
            if not self.path.exists():
                initial = empty_state()
                self._snapshot(initial, 0)
                atomic_json(self.path, initial)
            else:
                initial = json.loads(self.path.read_text())
                if not any(e["type"] == "project.snapshot" for e in initial["events"]):
                    self._snapshot(initial, initial["revision"])
                    atomic_json(self.path, initial)

    @contextmanager
    def lock(self, exclusive=True):
        with (self.root / ".lock").open("a+") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def read(self):
        with self.lock(False):
            return json.loads(self.path.read_text())

    def mutate(self, callback, expected_revision=None):
        with self.lock():
            state = json.loads(self.path.read_text())
            if expected_revision is not None and expected_revision != state["revision"]:
                raise StudioError("Project changed; reload before saving", "revision_conflict", 409,
                                  {"currentRevision": state["revision"]})
            old_project = copy.deepcopy(state["project"])
            previous_events = len(state["events"])
            result = callback(state)
            state["revision"] += 1
            if state["project"] != old_project or any(
                    e["type"] == "project.saved" for e in state["events"][previous_events:]):
                self._snapshot(state, state["revision"])
            atomic_json(self.path, state)
            return copy.deepcopy(result), copy.deepcopy(state)

    def _snapshot(self, state, revision):
        project_hash = digest(json.dumps(state["project"], ensure_ascii=False, sort_keys=True).encode())
        relative = "history/" + str(revision).zfill(8) + "-" + project_hash + ".json"
        snapshot = {"revision": revision, "createdAt": now(), "sha256": project_hash,
                    "project": copy.deepcopy(state["project"])}
        if not (self.root / relative).exists():
            atomic_json(self.root / relative, snapshot)
        self.event(state, "project.snapshot", revision=revision, sha256=project_hash, path=relative)

    def project_history(self):
        return [{k: event[k] for k in ("revision", "createdAt", "sha256", "path")}
                for event in self.read()["events"] if event["type"] == "project.snapshot"]

    def project_revision(self, revision):
        entries = [r for r in self.project_history() if r["revision"] == revision]
        if not entries:
            raise StudioError("Project revision not found", "not_found", 404)
        entry = entries[-1]
        path = (self.root / entry["path"]).resolve()
        if not path.is_relative_to((self.root / "history").resolve()):
            raise StudioError("Invalid history path", "path_forbidden", 403)
        snapshot = json.loads(path.read_text())
        if digest(json.dumps(snapshot["project"], ensure_ascii=False, sort_keys=True).encode()) != entry["sha256"]:
            raise StudioError("Project snapshot checksum mismatch", "storage_corruption", 500)
        return snapshot

    @staticmethod
    def event(state, kind, **data):
        event = {"id": new_id("event"), "type": kind, "createdAt": now(), **data}
        state["events"].append(event)
        return event

    def save_project(self, project, expected_revision):
        if not isinstance(expected_revision, int) or isinstance(expected_revision, bool):
            raise StudioError("expectedRevision is required")
        def update(state):
            validate_project(project, state["assets"])
            state["project"] = copy.deepcopy(project)
            self.event(state, "project.saved")
        return self.mutate(update, expected_revision)[1]

    def allowed_source(self, path):
        source = Path(path).expanduser().resolve()
        if not any(source.is_relative_to(root) for root in self.media_roots + [self.root]):
            raise StudioError("Import is outside configured media roots", "path_forbidden", 403)
        if not source.is_file():
            raise StudioError("Import file not found", "not_found", 404)
        return source

    def asset_path(self, asset_id, state=None):
        state = state if state is not None else self.read()
        asset = find(state["assets"], asset_id, "asset")
        path = (self.root / asset["storagePath"]).resolve()
        if not path.is_relative_to((self.root / "assets").resolve()) or not path.is_file():
            raise StudioError("Asset storage path is invalid", "path_forbidden", 403)
        return path

    def prepare_asset(self, raw, name="image", provenance=None, review_status="unreviewed"):
        if not raw or len(raw) > MAX_UPLOAD:
            raise StudioError("Image must be between 1 byte and 40 MiB", "upload_size", 413)
        try:
            im = Image.open(io.BytesIO(raw))
            if im.format not in FORMATS or im.width * im.height > 80_000_000:
                raise StudioError("Unsupported image format or dimensions")
            mime, extension = FORMATS[im.format]
            dimensions = im.size
            im.verify()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
            raise StudioError("Invalid image data", "invalid_image") from exc
        sha = digest(raw)
        identifier = "asset-" + sha[:24]
        relative = "assets/" + sha + extension
        target = self.root / relative
        if target.exists():
            if digest(target.read_bytes()) != sha:
                raise StudioError("Asset checksum mismatch", "storage_corruption", 500)
        else:
            atomic_bytes(target, raw)
        return {"id": identifier, "name": Path(name).name[:200], "mime": mime,
                "sha256": sha, "bytes": len(raw), "width": dimensions[0],
                "height": dimensions[1], "url": "/api/assets/" + identifier,
                "storagePath": relative, "createdAt": now(), "reviewStatus": review_status,
                "provenance": provenance or {}}

    def register_asset(self, state, asset):
        existing = next((a for a in state["assets"] if a["id"] == asset["id"]), None)
        if existing:
            return existing
        state["assets"].append(asset)
        return asset

    def upload_asset(self, raw, name="image", provenance=None, review_status="unreviewed"):
        asset = self.prepare_asset(raw, name, provenance, review_status)
        def add(state):
            result = self.register_asset(state, asset)
            self.event(state, "asset.imported", assetId=result["id"])
            return result
        return self.mutate(add)

    def import_asset(self, path, name=None, provenance=None, review_status="unreviewed"):
        source = self.allowed_source(path)
        if source.stat().st_size > MAX_UPLOAD:
            raise StudioError("Image exceeds 40 MiB", "upload_size", 413)
        provenance = {"sourcePath": str(source), **(provenance or {})}
        return self.upload_asset(source.read_bytes(), name or source.name, provenance, review_status)[0]
