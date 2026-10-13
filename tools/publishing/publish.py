#!/usr/bin/env python3
"""Package, upload, and stage verified releases. Never creates/deploys a remote repo."""
import argparse
import importlib.util
import json
from pathlib import Path

from release_format import (BUCKET, canonical, clean_path, identity, load_release,
                            require, write_new)
from package_release import package
from pages_template import select, stage, template
from materialize import download


def upload(directory, cache, receipt, adapter=None):
    directory = clean_path(directory)
    receipt = clean_path(receipt)
    require(not receipt.exists() and receipt.parent.is_dir(), "Receipt needs a new path in an existing directory")
    manifest, release = load_release(directory / "release-manifest.json")
    archive = manifest["archive"]
    require(identity(directory / "release.tar.gz") == (archive["bytes"], archive["sha256"]), "Package archive changed")
    public_readback = adapter is None
    if adapter is None:
        source = Path(__file__).resolve().parents[1] / "assets" / "hf_store.py"
        spec = importlib.util.spec_from_file_location("pinpin_hf_store", source)
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
    # Construct the entry from the authenticated manifest, not a second mutable file.
    entry = {"path": "release.tar.gz", "role": "archive", "bytes": archive["bytes"],
             "sha256": archive["sha256"], "object": archive["object"]}
    result = adapter.upload_entries([entry], directory, BUCKET, cache, workers=1,
                                    **({"public_http_readback": True} if public_readback else {}))
    require(result.get("verified") is True and result.get("dry_run") is False
            and len(result.get("entries", [])) == 1
            and result["entries"][0].get("remote_verified") is True, "Upload did not return verified readback")
    download(manifest)  # Real anonymous streamed GET; no second archive copy.
    result.update(release=release, anonymous_verified=True)
    write_new(receipt, canonical(result))
    return {"release": release, "receipt": str(receipt), "anonymous_verified": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("package", help="Package existing verified build artifact into a new directory")
    pack.add_argument("--artifact", required=True)
    pack.add_argument("--source-commit", required=True)
    pack.add_argument("--out", required=True)
    push = commands.add_parser("upload", help="Explicit HF upload plus SDK and anonymous readback")
    push.add_argument("--package", required=True)
    push.add_argument("--cache", required=True)
    push.add_argument("--receipt", required=True)
    create = commands.add_parser("template", help="Generate a new deployment-only repo directory")
    create.add_argument("--package", required=True)
    create.add_argument("--out", required=True)
    add = commands.add_parser("stage", help="Add an immutable manifest to an existing Pages repo; no Git writes")
    add.add_argument("--package", required=True)
    add.add_argument("--pages-repo", required=True)
    choose = commands.add_parser("select", help="Explicit publication/rollback selection; no Git writes")
    choose.add_argument("--pages-repo", required=True)
    choose.add_argument("--release", required=True)
    choose.add_argument("--expected-current", required=True)
    args = parser.parse_args()
    if args.command == "package":
        result = package(args.artifact, args.source_commit, args.out)
    elif args.command == "upload":
        result = upload(args.package, args.cache, args.receipt)
    elif args.command == "template":
        result = {"release": template(args.package, args.out), "template": args.out}
    elif args.command == "stage":
        result = {"release": stage(args.package, args.pages_repo)}
    else:
        result = {"release": select(args.pages_repo, args.release, args.expected_current)}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
