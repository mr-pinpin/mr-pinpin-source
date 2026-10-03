#!/usr/bin/env python3
"""Freeze or verify complete Studio runtimes as immutable content-addressed releases."""
import argparse
import json
from pathlib import Path
from immutable_bundle import BundleError, MANIFEST, capture, publish_bundle, verify_bundle
from model import now


def freeze(source, runtime_dir):
    source = Path(source).expanduser().resolve()
    runtime_dir = Path(runtime_dir).expanduser().resolve()
    if runtime_dir.is_relative_to(source) or source.is_relative_to(runtime_dir):
        raise BundleError("Runtime artifacts must be separate from Studio source")
    files = capture(source)
    for required in ("server.py", "conversation.py", "web/index.html"):
        if required not in files:
            raise BundleError("Incomplete stable source: " + required)
    manifest = publish_bundle(files, runtime_dir / "stable-releases", now(), "stable-runtime")
    path = runtime_dir / "stable-releases" / manifest["hash"]
    return {"stableRelease": manifest["hash"], "path": str(path), "server": str(path / "server.py"),
            "files": manifest["fileCount"], "bytes": manifest["bytes"],
            "note": "Launch server.py from this immutable path, passing --workspace-source, --runtime-dir and --data-dir."}


def stable_release(source):
    source = Path(source).resolve()
    if not (source / MANIFEST).exists():
        return "development"
    manifest = verify_bundle(source)
    if manifest.get("kind") != "stable-runtime":
        raise BundleError("Server source is not a stable runtime release")
    return manifest["hash"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("freeze")
    command.add_argument("--source", default=str(Path(__file__).resolve().parent))
    command = sub.add_parser("verify")
    command.add_argument("hash")
    args = parser.parse_args()
    try:
        if args.command == "freeze":
            result = freeze(args.source, args.runtime_dir)
        else:
            from workspace_runtime import HASH
            if not HASH.fullmatch(args.hash):
                raise BundleError("Invalid stable release hash")
            manifest = verify_bundle(Path(args.runtime_dir) / "stable-releases" / args.hash, args.hash)
            result = {"stableRelease": manifest["hash"], "verified": True, "files": manifest["fileCount"]}
        print(json.dumps(result, ensure_ascii=False))
    except (BundleError, OSError, ValueError) as exc:
        parser.exit(1, "Release failed: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
