"""Versioned trusted Python business plugins inside the existing Studio process.

This is an activation/rollback boundary, not a Python security sandbox.
"""
import copy
import importlib.util
import inspect
import json
import re
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from immutable_bundle import BundleError, bundle_hash, capture, publish_bundle, verify_bundle
from model import StudioError, now
from store import atomic_json

HASH = re.compile(r"^[a-f0-9]{64}$")
EXTENSIONS = {".py", ".json", ".md", ".txt"}
EXPORTS = ("selected_context", "route", "self_test")


@dataclass(eq=False)
class _Handle:
    sha: str
    name: str
    module: object
    leases: int = 0


class BusinessRuntime:
    def __init__(self, source, directory, watch=True, read_only=False):
        self.source = Path(source).expanduser().resolve() if source else None
        self.root = Path(directory).expanduser().resolve()
        if self.source and (self.root.is_relative_to(self.source) or self.source.is_relative_to(self.root)):
            raise ValueError("Business source and runtime artifacts must be separate")
        self.builds = self.root / "business-builds"
        self.read_only = read_only
        if not read_only:
            self.builds.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "business-state.json"
        self.lock = threading.RLock()
        self.build_lock = threading.Lock()
        self.stop = threading.Event()
        self.worker = None
        self.active = self.previous = None
        self.handles = []
        self.candidate = self.attempted = None
        self.candidate_since = 0
        self.state = {"active": None, "previous": None, "status": "idle", "error": None}
        self._restore()
        if self.source and not self.read_only:
            self.poll(force=True)
            if watch:
                self.worker = threading.Thread(target=self._watch, name="studio-business-builder", daemon=True)
                self.worker.start()

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.state)

    def _save(self, status, error=None):
        self.state = {"active": self.active.sha if self.active else None,
                      "previous": self.previous.sha if self.previous else None,
                      "status": status, "error": error}
        if not self.read_only:
            atomic_json(self.state_path, self.state)

    def _restore(self):
        try:
            stored = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}
            for key in ("active", "previous"):
                sha = stored.get(key)
                if not isinstance(sha, str) or not HASH.fullmatch(sha):
                    continue
                try:
                    handle = self._load(sha)
                except (Exception, SystemExit):
                    continue
                if self.active is None:
                    self.active = handle
                elif handle.sha != self.active.sha:
                    self.previous = handle
            failed = stored.get("error") or {}
            self.attempted = failed.get("hash") or (self.active.sha if self.active else None)
            if self.active:
                self._save("error" if failed else "ready", failed or None)
        except (OSError, ValueError):
            # The source can still supply a fresh validated initial build.
            pass

    @staticmethod
    def _validate(files):
        if "__init__.py" not in files:
            raise BundleError("Business source needs __init__.py")
        for name, raw in files.items():
            if name.endswith(".py"):
                try:
                    compile(raw, name, "exec")
                except (SyntaxError, ValueError) as exc:
                    raise BundleError("Python syntax check failed: " + name) from exc

    def _load(self, sha):
        directory = self.builds / sha
        verify_bundle(directory, sha)
        name = "_pinpin_business_" + sha + "_" + uuid4().hex
        spec = importlib.util.spec_from_file_location(name, directory / "__init__.py",
                                                     submodule_search_locations=[str(directory)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
            if type(getattr(module, "API_VERSION", None)) is not int or module.API_VERSION != 1 or any(
                    not callable(getattr(module, export, None)) for export in EXPORTS):
                raise BundleError("Business package must export API_VERSION=1, selected_context, route and self_test")
            for export, count in (("selected_context", 2), ("route", 5), ("self_test", 0)):
                inspect.signature(getattr(module, export)).bind(*([None] * count))
            # Optional for compatibility with retained packages predating creative policy.
            if hasattr(module, "creative_policy"):
                if not callable(module.creative_policy):
                    raise BundleError("Business creative_policy must be callable")
                inspect.signature(module.creative_policy).bind()
                self._validate_creative_policy(module.creative_policy())
            if module.self_test() is False:
                raise BundleError("Business self_test failed")
        except BaseException:
            self._unload(name)
            raise
        handle = _Handle(sha, name, module)
        with self.lock:
            self.handles.append(handle)
        return handle

    @staticmethod
    def _unload(name):
        for key in list(sys.modules):
            if key == name or key.startswith(name + "."):
                sys.modules.pop(key, None)

    def _prune(self):
        for handle in self.handles[:]:
            if handle not in (self.active, self.previous) and not handle.leases:
                self._unload(handle.name)
                self.handles.remove(handle)

    def _watch(self):
        while not self.stop.wait(.5):
            self.poll()

    def poll(self, force=False):
        if self.read_only or not self.source or self.stop.is_set() or not self.build_lock.acquire(blocking=False):
            return
        sha = None
        try:
            files = capture(self.source, EXTENSIONS)
            sha = bundle_hash(files)
            if sha != self.candidate:
                self.candidate, self.candidate_since = sha, time.monotonic()
            if sha == self.attempted or (not force and time.monotonic() - self.candidate_since < .4):
                return
            self.attempted = sha
            with self.lock:
                self._save("building")
            self._validate(files)
            publish_bundle(files, self.builds, now(), "business")
            handle = self._load(sha)
            # Imports/self_test may take time; do not activate an obsolete capture.
            if bundle_hash(capture(self.source, EXTENSIONS)) != sha:
                self.attempted = None
                with self.lock:
                    self._prune()
                return
            with self.lock:
                if self.stop.is_set():
                    self._prune()
                    return
                self.previous, self.active = self.active, handle
                self._save("ready")
                self._prune()
        except (Exception, SystemExit) as exc:
            message = str(exc) if isinstance(exc, BundleError) else "Business candidate import or self-test failed"
            with self.lock:
                self._save("error", {"code": "business_build", "message": message, "hash": sha})
                self._prune()
        finally:
            self.build_lock.release()

    @staticmethod
    def _validate_creative_policy(value):
        if not isinstance(value, str) or not value.strip() or len(value) > 16000:
            raise BundleError("Business creative policy must contain 1–16000 characters")

    def invoke(self, name, *args, validate=None):
        if name not in ("selected_context", "route", "claim_job", "complete_job", "fail_job", "reply", "inbox", "creative_policy"):
            raise StudioError("Unknown business operation", "invalid_request", 400)
        with self.lock:
            handle = self.active
            if handle is None:
                raise StudioError("Business logic is unavailable; conversation recovery remains available",
                                  "business_unavailable", 503)
            if not callable(getattr(handle.module, name, None)):
                raise StudioError("Business operation is unavailable", "business_unavailable", 503)
            handle.leases += 1
        try:
            value = getattr(handle.module, name)(*args)
            if name == "creative_policy":
                self._validate_creative_policy(value)
            if name == "route" and value is not None and (
                    not isinstance(value, tuple) or len(value) != 2 or
                    type(value[0]) is not int or not 100 <= value[0] <= 599):
                raise ValueError("Invalid business route response")
            if name == "route" and value is not None:
                json.dumps(value[1], ensure_ascii=False, allow_nan=False)
            if validate is not None:
                try:
                    validate(value)
                except (Exception, SystemExit) as exc:
                    raise ValueError("Business output validation failed") from exc
            return value
        except StudioError:
            # Input validation, optimistic revision conflicts and expected API errors
            # do not indicate a broken build.
            raise
        except (Exception, SystemExit) as exc:
            with self.lock:
                if self.active is handle:
                    self.active, self.previous = self.previous, None
                    self._save("error", {"code": "business_call", "message":
                        "Business operation failed; previous version restored" if self.active else
                        "Business operation failed; recovery remains available", "hash": handle.sha})
            # The failed operation may already have persisted a mutation. Never replay it.
            raise StudioError("Business operation failed; request was not replayed",
                              "business_call", 503) from exc
        finally:
            with self.lock:
                handle.leases -= 1
                self._prune()

    def close(self):
        self.stop.set()
        if self.worker:
            self.worker.join(timeout=12)
        with self.lock:
            self.active = self.previous = None
            self._prune()
