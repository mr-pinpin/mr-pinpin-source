"""Verified, non-destructive content-addressed Hugging Face bucket storage."""
from __future__ import annotations

import hashlib
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys
import tempfile


class StorageError(ValueError):
    """Invalid manifest, unsafe destination, corrupt content, or storage failure."""


def relative_path(value: str) -> PurePosixPath:
    if (not isinstance(value, str) or not value or "\\" in value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise StorageError("Expected a nonempty POSIX relative path")
    path = PurePosixPath(value)
    if (path.is_absolute() or PureWindowsPath(value).drive
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise StorageError("Absolute paths and traversal components are forbidden")
    return path


def content_key(sha256: str, basename: str) -> str:
    if (not isinstance(sha256, str) or len(sha256) != 64
            or any(c not in "0123456789abcdef" for c in sha256)):
        raise StorageError("Expected a lowercase SHA-256 digest")
    name = relative_path(basename)
    if len(name.parts) != 1:
        raise StorageError("Content key requires a basename")
    return f"sha256/{sha256[:2]}/{sha256}/{name}"


def safe_path(root: Path | str, relative: str, *, create: bool = False) -> Path:
    parts = relative_path(relative).parts
    base = Path(root).expanduser()
    if base.is_symlink():
        raise StorageError("Root must not be a symlink")
    if create:
        base.mkdir(parents=True, exist_ok=True)
    base = base.resolve()
    current = base
    for index, part in enumerate(parts):
        current /= part
        if current.is_symlink():
            raise StorageError(f"Symlink path component: {relative}")
        if index < len(parts) - 1:
            if create:
                current.mkdir(exist_ok=True)
            if current.exists() and not current.is_dir():
                raise StorageError(f"Non-directory path component: {relative}")
    return current


def file_identity(path: Path | str) -> tuple[int, str]:
    """Hash a regular file without following a final symlink."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    digest, size = hashlib.sha256(), 0
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise StorageError("Asset must be a regular file")
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return size, digest.hexdigest()


def check_file(path: Path, size: int, sha256: str) -> None:
    try:
        identity = file_identity(path)
    except OSError as exc:
        raise StorageError(f"Cannot read regular asset: {path.name}") from exc
    if identity != (size, sha256):
        raise StorageError(f"Size or SHA-256 mismatch: {path.name}")


def atomic_place(temporary: Path, destination: Path, size: int, sha256: str) -> None:
    """Publish without replacing a concurrent or existing destination."""
    check_file(temporary, size, sha256)
    try:
        os.link(temporary, destination, follow_symlinks=False)
    except FileExistsError:
        check_file(destination, size, sha256)


def temporary_path(parent: Path) -> Path:
    fd, name = tempfile.mkstemp(prefix=".hf-store-", suffix=".part", dir=parent)
    os.close(fd)
    return Path(name)


def validate_entries(entries: list[dict]) -> list[dict]:
    if not isinstance(entries, list):
        raise StorageError("Manifest assets must be a list")
    result, seen = [], set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise StorageError("Each asset must be an object")
        path = relative_path(entry.get("path"))
        size, digest = entry.get("bytes"), entry.get("sha256")
        if type(size) is not int or size < 0:
            raise StorageError("Asset bytes must be a nonnegative integer")
        if entry.get("role") not in ("production", "archive"):
            raise StorageError("Asset role must be production or archive")
        key = content_key(digest, path.name)
        if entry.get("object") != key:
            raise StorageError("Asset object must match its SHA-256 and basename")
        if str(path) in seen:
            raise StorageError("Duplicate asset path")
        seen.add(str(path))
        result.append({"path": str(path), "role": entry["role"], "bytes": size,
                       "sha256": digest, "object": key})
    for name in seen:
        if any(str(parent) in seen for parent in PurePosixPath(name).parents):
            raise StorageError("Manifest paths overlap a file and its children")
    return result


def validate_bucket(bucket: str) -> str:
    if not isinstance(bucket, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", bucket):
        raise StorageError("Bucket must be namespace/name")
    return bucket


def load_manifest(path: Path | str, profile: str = "archive") -> tuple[str, list[dict]]:
    with open(path, encoding="utf-8") as stream:
        manifest = json.load(stream)
    if not isinstance(manifest, dict) or type(manifest.get("version")) is not int or manifest["version"] != 1:
        raise StorageError("Expected manifest version 1")
    bucket = validate_bucket(manifest.get("bucket"))
    entries = validate_entries(manifest.get("assets"))
    if profile not in {"archive", "production", "all"}:
        raise StorageError("Unknown profile")
    return bucket, [e for e in entries if profile == "all" or e["role"] == profile]


def cache_root(root: Path | str, cache: Path | str | None) -> Path:
    default = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "mr-pinpin" / "assets"
    location = Path(cache or os.environ.get("PINPIN_ASSET_CACHE") or default).expanduser()
    if location.is_symlink():
        raise StorageError("Cache root must not be a symlink")
    resolved = location.resolve()
    if resolved.is_relative_to(Path(root).expanduser().resolve()):
        raise StorageError("Asset cache must be outside the repository root")
    return resolved


def source_path(root, relative, *, allow_symlinks=False) -> Path:
    if not allow_symlinks:
        return safe_path(root, relative)
    # Explicit opt-in is read-only and still requires the manifest's byte identity.
    path = Path(root).expanduser().resolve().joinpath(*relative_path(relative).parts)
    return path.resolve(strict=True)


def _client(api):
    if api is not None:
        return api
    try:
        from huggingface_hub import HfApi
    except ImportError:
        raise StorageError("Install tools/assets/requirements.txt to enable HF transfers") from None
    return HfApi()  # HF_TOKEN and the standard cached token are handled by the SDK.


def _remote_error(operation: str, exc: Exception) -> StorageError:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    suffix = f" (HTTP {status})" if type(status) is int else ""
    # Classify provider errors without copying response bodies, URLs, or tokens.
    detail = str(exc).lower()
    if "private" in detail and ("quota" in detail or ("storage" in detail and ("limit" in detail or "exceed" in detail))):
        return StorageError(f"Hugging Face private bucket storage quota exceeded{suffix}")
    return StorageError(f"Remote {operation} failed{suffix}")


def _remote_metadata(api, bucket: str, entry: dict):
    from huggingface_hub.errors import EntryNotFoundError
    try:
        # HEAD Content-Length can describe a redirect body. Bucket path-info
        # carries the stored object's size and Xet identity used by SDK downloads.
        records = list(api.get_bucket_paths_info(bucket, [entry["object"]]))
    except EntryNotFoundError:
        return None
    except Exception as exc:
        raise _remote_error("metadata lookup", exc) from None
    if not records:
        return None
    if len(records) != 1 or getattr(records[0], "path", None) != entry["object"]:
        raise StorageError("Remote metadata does not identify the requested object")
    metadata = records[0]
    if getattr(metadata, "type", None) != "file" or not _fingerprint(metadata):
        raise StorageError("Remote metadata lacks a file content identity")
    if type(metadata.size) is not int or metadata.size != entry["bytes"]:
        raise StorageError("Existing remote object has a conflicting size; refusing overwrite")
    return metadata


def _fingerprint(metadata):
    value = getattr(metadata, "xet_hash", None)
    return value if isinstance(value, str) and value else None


def _resume_matches(receipt, bucket, entry, metadata) -> bool:
    fingerprint = _fingerprint(metadata)
    if (not isinstance(receipt, dict) or type(receipt.get("version")) is not int or receipt["version"] != 1
            or receipt.get("action") not in ("push", "verify") or receipt.get("dry_run") is not False
            or receipt.get("bucket") != bucket
            or receipt.get("verified") is not True or not fingerprint):
        return False
    records = receipt.get("entries")
    if not isinstance(records, list):
        return False
    for previous in records:
        if not isinstance(previous, dict):
            continue
        if (all(previous.get(k) == entry[k] for k in ("path", "sha256", "bytes", "object", "role"))
                and previous.get("verified") is True and previous.get("remote_verified") is True
                and previous.get("remote_xet_hash") == fingerprint):
            return True
    return False


def _workers(value):
    if type(value) is not int or not 1 <= value <= 16:
        raise StorageError("workers must be between 1 and 16")
    return value


def _copy_verified(source: Path, destination: Path, entry: dict) -> None:
    if destination.exists() or destination.is_symlink():
        check_file(destination, entry["bytes"], entry["sha256"])
        return
    temporary = temporary_path(destination.parent)
    try:
        fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as incoming, temporary.open("wb") as outgoing:
            if not stat.S_ISREG(os.fstat(incoming.fileno()).st_mode):
                raise StorageError("Source must be a regular file")
            for block in iter(lambda: incoming.read(1024 * 1024), b""):
                outgoing.write(block)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        atomic_place(temporary, destination, entry["bytes"], entry["sha256"])
    finally:
        temporary.unlink(missing_ok=True)


def _download_verified(api, bucket: str, entry: dict, cache: Path, *, keep: bool) -> Path:
    destination = safe_path(cache, entry["object"], create=True)
    if keep and destination.exists():
        check_file(destination, entry["bytes"], entry["sha256"])
        return destination
    temporary = temporary_path(destination.parent)
    try:
        try:
            api.download_bucket_files(bucket, [(entry["object"], temporary)], raise_on_missing_files=True)
        except Exception as exc:
            raise _remote_error("download", exc) from None
        check_file(temporary, entry["bytes"], entry["sha256"])
        if keep:
            safe_path(cache, entry["object"])
            atomic_place(temporary, destination, entry["bytes"], entry["sha256"])
        return destination
    finally:
        temporary.unlink(missing_ok=True)


def _result(entry: dict, status: str, *, remote: bool = False, verified: bool = True) -> dict:
    return {**entry, "status": status, "verified": verified, "remote_verified": remote}


def _receipt(action: str, bucket: str, results: list[dict], dry_run: bool = False) -> dict:
    return {"version": 1, "action": action, "bucket": bucket, "dry_run": dry_run,
            "verified": not dry_run and all(e["verified"] for e in results), "entries": results}


def _verify_remote(api, bucket, entry, cache, *, status="remote-verified", metadata=None) -> dict:
    before = metadata if metadata is not None else _remote_metadata(api, bucket, entry)
    if before is None:
        raise StorageError("Remote object is missing")
    _download_verified(api, bucket, entry, cache, keep=False)
    after = _remote_metadata(api, bucket, entry)
    if after is None or _fingerprint(before) != _fingerprint(after):
        raise StorageError("Remote object changed during verification")
    result = _result(entry, status, remote=True)
    if _fingerprint(after):
        result["remote_xet_hash"] = _fingerprint(after)
    return result


def upload_entries(entries, root, bucket, cache=None, *, api=None, dry_run=False,
                   allow_source_symlinks=False, workers=4, resume_receipt=None, progress=None) -> dict:
    """Upload archive entries; verify production locally. Never overwrite conflicts."""
    entries, bucket = validate_entries(entries), validate_bucket(bucket)
    cache = cache_root(root, cache)
    workers = _workers(workers)
    # Validate the complete source set before any remote write can begin.
    for entry in entries:
        source = source_path(root, entry["path"], allow_symlinks=allow_source_symlinks)
        check_file(source, entry["bytes"], entry["sha256"])
    if progress:
        progress(f"Validated {len(entries)} local assets")
    if dry_run:
        return _receipt("push", bucket, [_result(e, "would-upload" if e["role"] == "archive"
                        else "production-local", verified=e["role"] == "production") for e in entries], True)
    archives, cached_files = [], {}
    for entry in entries:
        if entry["role"] == "production":
            continue
        source = source_path(root, entry["path"], allow_symlinks=allow_source_symlinks)
        cached = safe_path(cache, entry["object"], create=True)
        _copy_verified(source, cached, entry)
        archives.append(entry)
        cached_files[entry["object"]] = cached
    if not archives:
        return _receipt("push", bucket, [_result(e, "production-local") for e in entries])
    api = _client(api)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        metadata = list(pool.map(lambda entry: _remote_metadata(api, bucket, entry), archives))
        missing = {e["object"]: e for e, meta in zip(archives, metadata) if meta is None}
        pending = list(missing.values())
        for start in range(0, len(pending), 64):
            batch = pending[start:start + 64]
            for entry in batch:
                check_file(cached_files[entry["object"]], entry["bytes"], entry["sha256"])
            try:
                api.batch_bucket_files(bucket, add=[(cached_files[e["object"]], e["object"]) for e in batch])
            except Exception as exc:
                raise _remote_error("upload", exc) from None
            if progress:
                progress(f"Uploaded {min(start + 64, len(pending))}/{len(pending)} new objects")

        def verify_one(pair):
            entry, meta = pair
            if meta is not None and _resume_matches(resume_receipt, bucket, entry, meta):
                return {**_result(entry, "receipt-resumed", remote=True), "remote_xet_hash": _fingerprint(meta)}
            return _verify_remote(api, bucket, entry, cache, metadata=meta,
                                  status="uploaded" if meta is None else "remote-existing")

        results = []
        for result in pool.map(verify_one, zip(archives, metadata)):
            results.append(result)
            if progress and (len(results) % 25 == 0 or len(results) == len(archives)):
                progress(f"Verified {len(results)}/{len(archives)} archive assets")
    by_path = {r["path"]: r for r in results}
    return _receipt("push", bucket, [by_path[e["path"]] if e["role"] == "archive"
                                    else _result(e, "production-local") for e in entries])


def materialize_entries(entries, root, bucket, cache=None, *, api=None, workers=4, progress=None) -> dict:
    """Restore missing archive paths; an identical local file needs no transfer."""
    entries, bucket = validate_entries(entries), validate_bucket(bucket)
    cache = cache_root(root, cache)
    workers = _workers(workers)
    # Refuse all known local conflicts before downloading or placing any asset.
    for entry in entries:
        destination = safe_path(root, entry["path"])
        if destination.exists() or entry["role"] == "production":
            check_file(destination, entry["bytes"], entry["sha256"])
    # Construct at most one shared SDK client, and only for a cache miss.
    if any(e["role"] == "archive" and not safe_path(root, e["path"]).exists()
           and not safe_path(cache, e["object"]).exists() for e in entries):
        api = _client(api)

    def restore_one(entry):
        destination = safe_path(root, entry["path"], create=True)
        if destination.exists():
            check_file(destination, entry["bytes"], entry["sha256"])
            return _result(entry, "production-local" if entry["role"] == "production" else "local-existing")
        cached = safe_path(cache, entry["object"], create=True)
        cache_hit = cached.exists()
        if cache_hit:
            check_file(cached, entry["bytes"], entry["sha256"])
        else:
            cached = _download_verified(api, bucket, entry, cache, keep=True)
        safe_path(root, entry["path"])
        _copy_verified(cached, destination, entry)
        check_file(destination, entry["bytes"], entry["sha256"])
        return _result(entry, "cache-restored" if cache_hit else "downloaded", remote=not cache_hit)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = []
        for result in pool.map(restore_one, entries):
            results.append(result)
            if progress and (len(results) % 25 == 0 or len(results) == len(entries)):
                progress(f"Materialized {len(results)}/{len(entries)} assets")
    return _receipt("pull", bucket, results)


def verify_entries(entries, root, bucket, cache=None, *, api=None, workers=4, progress=None) -> dict:
    """Fresh-download archive objects for migration proof; production stays local."""
    entries, bucket = validate_entries(entries), validate_bucket(bucket)
    cache = cache_root(root, cache)
    workers = _workers(workers)
    for entry in entries:
        if entry["role"] == "production":
            check_file(safe_path(root, entry["path"]), entry["bytes"], entry["sha256"])
    if any(e["role"] == "archive" for e in entries):
        api = _client(api)
    def verify_one(entry):
        if entry["role"] == "production":
            return _result(entry, "production-local")
        return _verify_remote(api, bucket, entry, cache)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = []
        for result in pool.map(verify_one, entries):
            results.append(result)
            if progress and (len(results) % 25 == 0 or len(results) == len(entries)):
                progress(f"Verified {len(results)}/{len(entries)} assets")
    return _receipt("verify", bucket, results)


def write_receipt(filename: Path | str, receipt: dict) -> None:
    """Only explicitly selected receipts are replaceable; asset files never are."""
    destination = Path(filename).expanduser().absolute()
    # The caller selects the receipt directory; the final file cannot be a link.
    destination = safe_path(destination.parent.resolve(), destination.name, create=True)
    temporary = temporary_path(destination.parent)
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(receipt, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if destination.is_symlink():
            raise StorageError("Receipt destination must not be a symlink")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("push", "pull", "verify"))
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--cache")
    parser.add_argument("--receipt", help="Atomic JSON receipt written only after successful verification")
    parser.add_argument("--resume-receipt", help="Reuse push proofs when remote content identity is unchanged")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--allow-source-symlinks", action="store_true", help="Allow verified push source reads through symlinks")
    parser.add_argument("--profile", choices=("archive", "production", "all"), default="archive")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.dry_run and args.action != "push":
        parser.error("--dry-run is supported for push only")
    if (args.allow_source_symlinks or args.resume_receipt) and args.action != "push":
        parser.error("Source symlink and resume options are supported for push only")
    try:
        bucket, entries = load_manifest(args.manifest, args.profile)
        function = {"push": upload_entries, "pull": materialize_entries, "verify": verify_entries}[args.action]
        kwargs = {"workers": args.workers, "progress": lambda message: print(f"hf-store: {message}", file=sys.stderr)}
        if args.action == "push":
            resume = None
            prior = args.resume_receipt or args.receipt
            if prior and Path(prior).exists():
                with open(prior, encoding="utf-8") as stream:
                    resume = json.load(stream)
            kwargs.update(dry_run=args.dry_run, allow_source_symlinks=args.allow_source_symlinks, resume_receipt=resume)
        receipt = function(entries, args.root, bucket, args.cache, **kwargs)
        if args.receipt and not args.dry_run:
            write_receipt(args.receipt, receipt)
    except (StorageError, OSError, json.JSONDecodeError) as exc:
        message = str(exc) if isinstance(exc, StorageError) else type(exc).__name__
        print(json.dumps({"version": 1, "action": args.action, "verified": False, "error": message}), file=sys.stderr)
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
