"""Content-addressed immutable file bundles; never executes source code."""
import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path

MANIFEST = ".studio-manifest.json"
IGNORED = {".git", "__pycache__", "node_modules", ".DS_Store"}
MAX_FILES = 2000
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 96 * 1024 * 1024


class BundleError(ValueError):
    pass


def capture(source, extensions=None, exclude=()):
    source = Path(source).resolve()
    if not source.is_dir():
        raise BundleError("Workspace source directory is unavailable")
    files = {}
    total = 0
    def excluded(path):
        relative = path.relative_to(source).as_posix()
        return any(relative == item or relative.startswith(item + "/") for item in exclude)

    for directory, dirs, names in os.walk(source, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED and not d.startswith(".")
                         and not excluded(Path(directory) / d))
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise BundleError("Symlinks are not allowed in source bundles")
        for name in sorted(names):
            if name in IGNORED or name.startswith(".") or name.endswith((".pyc", ".pyo")) or excluded(Path(directory) / name):
                continue
            path = Path(directory) / name
            relative = path.relative_to(source).as_posix()
            if path.is_symlink() or not path.resolve().is_relative_to(source):
                raise BundleError("Symlinks are not allowed in source bundles")
            if extensions is not None and path.suffix.lower() not in extensions:
                raise BundleError("Unsupported workspace file: " + relative)
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
                    raise BundleError("Source file is not a bounded regular file: " + relative)
                raw = stream.read(MAX_FILE_BYTES + 1)
            if len(raw) > MAX_FILE_BYTES:
                raise BundleError("Source file is too large: " + relative)
            total += len(raw)
            if total > MAX_TOTAL_BYTES or len(files) >= MAX_FILES:
                raise BundleError("Source bundle exceeds its size/file limit")
            files[relative] = raw
    return files


def file_manifest(files):
    return {name: {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            for name, raw in sorted(files.items())}


def bundle_hash(files):
    manifest = json.dumps(file_manifest(files), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(manifest).hexdigest()


def verify_bundle(directory, expected=None):
    directory = Path(directory)
    try:
        manifest = json.loads((directory / MANIFEST).read_text())
        files = capture(directory)
        sha = bundle_hash(files)
        if sha != manifest["hash"] or (expected is not None and sha != expected):
            raise BundleError("Immutable bundle checksum mismatch")
        if file_manifest(files) != manifest["files"]:
            raise BundleError("Immutable bundle file manifest mismatch")
        return manifest
    except (OSError, ValueError, KeyError) as exc:
        raise BundleError("Immutable bundle could not be verified") from exc


def publish_bundle(files, destination, created_at, kind):
    """Atomically publish by digest. Existing versions are verified, never overwritten."""
    parent = Path(destination)
    parent.mkdir(parents=True, exist_ok=True)
    sha = bundle_hash(files)
    final = parent / sha
    if final.exists():
        return verify_bundle(final, sha)
    manifest = {"hash": sha, "createdAt": created_at, "kind": kind,
                "fileCount": len(files), "bytes": sum(map(len, files.values())),
                "files": file_manifest(files)}
    staging = Path(tempfile.mkdtemp(prefix=".building-", dir=parent))
    try:
        for relative, raw in files.items():
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        with (staging / MANIFEST).open("w") as stream:
            stream.write(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        for root, dirs, names in os.walk(staging):
            for name in names:
                (Path(root) / name).chmod(0o444)
        for root, dirs, names in os.walk(staging, topdown=False):
            descriptor = os.open(root, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            if Path(root) != staging:
                Path(root).chmod(0o555)
        try:
            os.rename(staging, final)
            final.chmod(0o555)
        except OSError:
            if not final.exists():
                raise
            verify_bundle(final, sha)
        descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if staging.exists():
            for root, dirs, names in os.walk(staging):
                Path(root).chmod(0o755)
            shutil.rmtree(staging)
    return manifest
