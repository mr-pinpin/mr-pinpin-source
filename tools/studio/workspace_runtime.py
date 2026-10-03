"""Debounced, syntax-checked immutable workspace builds for the stable shell."""
import copy
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from immutable_bundle import BundleError, MANIFEST, capture, bundle_hash, publish_bundle, verify_bundle
from model import StudioError, now
from store import atomic_json

HASH = re.compile(r"^[a-f0-9]{64}$")
WEB_EXTENSIONS = {".html", ".js", ".mjs", ".css", ".json", ".svg", ".png", ".jpg", ".jpeg",
                  ".webp", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".avif", ".map"}
SOURCE_EXTENSIONS = WEB_EXTENSIONS | {".md", ".txt"}


class WorkspaceRuntime:
    def __init__(self, source, directory, stable_release="development", watch=True):
        self.source = Path(source).expanduser().resolve() if source else None
        self.root = Path(directory).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.builds = self.root / "workspace-builds"
        self.builds.mkdir(exist_ok=True)
        self.state_path = self.root / "workspace-state.json"
        self.stable_release = stable_release
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.worker = None
        self.candidate = None
        self.candidate_since = 0
        self.attempted = None
        self.verified_files = {}
        self.state = {"latest": None, "previous": None, "status": "idle", "error": None, "url": None}
        if self.state_path.exists():
            stored = json.loads(self.state_path.read_text())
            for key in ("latest", "previous"):
                sha = stored.get(key)
                if sha and HASH.fullmatch(sha):
                    verify_bundle(self.builds / sha, sha)
                    self.state[key] = sha
            if self.state["latest"]:
                self.state.update(status="ready", url=self.url(self.state["latest"]))
        if self.source:
            self.poll(force=True)
            if watch:
                self.worker = threading.Thread(target=self._watch, name="studio-workspace-builder", daemon=True)
                self.worker.start()

    @staticmethod
    def url(sha):
        return "/workspace-builds/" + sha + "/index.html"

    def snapshot(self):
        with self.lock:
            return {"stableRelease": self.stable_release, "workspace": copy.deepcopy(self.state),
                    "pollIntervalMs": 1000}

    def _update(self, **fields):
        with self.lock:
            self.state.update(fields)
            atomic_json(self.state_path, self.state)

    def _watch(self):
        while not self.stop.wait(.5):
            self.poll()

    def _validate(self, files):
        if "index.html" not in files:
            raise BundleError("Workspace needs index.html")
        scripts = [(name, raw) for name, raw in files.items() if Path(name).suffix in (".js", ".mjs")]
        if scripts:
            path = "/opt/homebrew/bin:" + os.environ.get("PATH", "")
            node = shutil.which("node", path=path)
            if not node:
                raise BundleError("Node is unavailable for workspace syntax validation")
            for name, raw in scripts:
                try:
                    result = subprocess.run([node, "--input-type=module", "--check"], input=raw,
                                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=10)
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise BundleError("Syntax validation unavailable: " + name) from exc
                if result.returncode:
                    raise BundleError("JavaScript syntax check failed: " + name)
        for name, raw in files.items():
            if name.endswith(".json"):
                try:
                    json.loads(raw)
                except (ValueError, UnicodeDecodeError) as exc:
                    raise BundleError("Invalid JSON: " + name) from exc

    def poll(self, force=False):
        if not self.source:
            return
        try:
            files = capture(self.source, SOURCE_EXTENSIONS)
            sha = bundle_hash(files)
            if sha != self.candidate:
                self.candidate, self.candidate_since = sha, time.monotonic()
            if not force and (sha == self.attempted or time.monotonic() - self.candidate_since < .4):
                return
            self.attempted = sha
            self._update(status="building", error=None)
            self._validate(files)
            # Do not publish a mixture of files that changed while checks ran.
            if bundle_hash(capture(self.source, SOURCE_EXTENSIONS)) != sha:
                self.attempted = None
                return
            manifest = publish_bundle(files, self.builds, now(), "workspace")
            with self.lock:
                previous = self.state["latest"] if sha != self.state["latest"] else self.state["previous"]
            self._update(latest=manifest["hash"], previous=previous, status="ready",
                         error=None, url=self.url(sha))
        except (BundleError, OSError, ValueError) as exc:
            # BundleError messages contain only source-relative filenames and fixed diagnostics.
            message = str(exc) if isinstance(exc, BundleError) else "Workspace source could not be read"
            error = {"code": "workspace_build", "message": message}
            with self.lock:
                unchanged = self.state["status"] == "error" and self.state["error"] == error
            if not unchanged:
                self._update(status="error", error=error)

    def releases(self):
        releases = []
        for path in self.builds.iterdir():
            if path.is_dir() and HASH.fullmatch(path.name):
                try:
                    manifest = json.loads((path / MANIFEST).read_text())
                    releases.append({key: manifest[key] for key in
                                     ("hash", "createdAt", "fileCount", "bytes")})
                    releases[-1]["url"] = self.url(path.name)
                except (OSError, ValueError, KeyError):
                    continue
        return {"releases": sorted(releases, key=lambda release: release["createdAt"], reverse=True)}

    def file(self, sha, relative):
        if not isinstance(sha, str) or not HASH.fullmatch(sha) or not relative or any(part.startswith(".") for part in relative.split("/")):
            raise StudioError("Workspace file not found", "not_found", 404)
        if Path(relative).suffix.lower() not in WEB_EXTENSIONS:
            raise StudioError("Workspace file not found", "not_found", 404)
        root = self.builds / sha
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise StudioError("Workspace file not found", "not_found", 404)
        try:
            manifest = json.loads((root / MANIFEST).read_text())
            entry = manifest["files"][relative]
            info = path.stat()
            signature = (info.st_ino, info.st_size, info.st_mtime_ns)
            key = (sha, relative)
            if self.verified_files.get(key) != signature:
                if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                    raise StudioError("Workspace checksum mismatch", "storage_corruption", 500)
                self.verified_files[key] = signature
            return path, mimetypes.guess_type(path)[0] or "application/octet-stream", entry["sha256"]
        except (OSError, ValueError, KeyError) as exc:
            raise StudioError("Workspace file not found", "not_found", 404) from exc

    def close(self):
        self.stop.set()
        if self.worker:
            self.worker.join(timeout=12)
