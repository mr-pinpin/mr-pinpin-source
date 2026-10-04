#!/usr/bin/env python3
"""Register exact native image bytes as an unreviewed Studio candidate."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True
_TRACE = '--trace-phases' in sys.argv or '--trace' in sys.argv
_TRACE_STARTED = time.monotonic()
def phase(name):
    if _TRACE:
        print(json.dumps({'registrationPhase': name, 'elapsedMs': round((time.monotonic()-_TRACE_STARTED)*1000,3)}), file=sys.stderr, flush=True)
phase('module-imports-complete')


def now():
    return datetime.now(timezone.utc).isoformat()


def load_store(args):
    phase("deployment-read-before")
    if args.runtime_dir:
        runtime = Path(args.runtime_dir).expanduser().resolve()
        deployment = json.loads((runtime / "current-deployment.json").read_text())
        release = deployment["stableRelease"]
        if not re.fullmatch("[a-f0-9]{64}", release):
            raise ValueError("Invalid active stable release")
        kernel = runtime / "stable-releases" / release
        data = Path(args.data_dir or deployment["dataDirectory"]).expanduser().resolve()
    else:
        kernel = Path(args.kernel_root).expanduser().resolve()
        if not args.data_dir:
            raise ValueError("--data-dir is required with --kernel-root")
        data = Path(args.data_dir).expanduser().resolve()
    phase("deployment-read-complete")
    # Execute only an explicitly selected, intact immutable Store implementation.
    sys.path.insert(0, str(kernel))
    phase("kernel-import-before")
    from immutable_bundle import verify_bundle
    phase("verify-bundle-before")
    manifest = verify_bundle(kernel)
    phase("verify-bundle-complete")
    if manifest.get("kind") != "stable-runtime":
        raise ValueError("Selected kernel is not a frozen stable-runtime release")
    phase("store-import-before")
    from store import Store
    phase("store-import-complete")
    if not (data / "state.json").is_file():
        raise ValueError("Existing Studio data directory required")
    if getattr(args, 'validate_only', False):
        # Diagnostic/read-only validation never constructs a settings writer.
        store = Store.__new__(Store)
        store.root, store.path = data, data / 'state.json'
        store.media_roots = [Path(p) for p in json.loads((data/'settings.json').read_text()).get('mediaRoots', [])]
        store.read = lambda: json.loads(store.path.read_text())
        phase('readonly-registry-view-ready')
        return store, manifest, data
    phase('store-constructor-before')
    store = Store(data)
    phase('store-constructor-complete')
    return store, manifest, data


def safe_report(data, relative):
    path = data / relative
    if not path.resolve().is_relative_to(data) or path.is_symlink():
        raise ValueError("Report path escapes data or is a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def dossier(path, entity):
    value = json.loads(path.read_text()) if path.exists() else {"schemaVersion": 1, "entityId": entity, "stages": {}}
    if value.get("schemaVersion") != 1 or value.get("entityId") != entity or not isinstance(value.get("stages"), dict):
        raise ValueError("Existing dossier has an incompatible schema; preserved unchanged")
    for stage in value["stages"].values():
        if not isinstance(stage, dict) or not isinstance(stage.get("candidates"), list):
            raise ValueError("Existing dossier candidates are invalid; preserved unchanged")
    return value


def setup_toolchain(args):
    if not args.runtime_dir or args.data_dir:
        raise ValueError("Setup requires --runtime-dir without a data override")
    store, _, data = load_store(args)
    from store import atomic_json
    helper = Path(__file__).resolve()
    launcher = data / "tools" / "studio-python"
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise ValueError("Prepared executable DATA/tools/studio-python is required for registration hydration")
    value = {"schemaVersion": 1, "toolName": "studio-register-image",
             "argvPrefix": [str(launcher), str(helper), "--runtime-dir", str(Path(args.runtime_dir).expanduser().resolve())],
             "helperSha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
             "parameters": {"required": ["--native-path", "--prompt-file", "--output-name"], "repeatable": ["--reference"], "optional": ["--entity", "--stage"]},
             "inputContract": "Exact native image bytes, UTF-8 exact prompt, registered reference IDs; entity/stage must be paired.",
             "outputContract": {"format": "json", "fields": ["assetId", "sha256", "reviewStatus", "workflowCard", "timing", "dossierPath"], "dossierPath": "reports/character-packages/<entity>.json"},
             "help": "Register unreviewed candidate and optional dossier in one call; no selection or approval."}
    path = safe_report(data, "workflows/toolchain.json")
    with store.lock():
        atomic_json(path, value)
    return {"toolchainPath": str(path), **value}


def register(args):
    started, started_at = time.monotonic(), now()
    store, manifest, data = load_store(args)
    from store import MAX_UPLOAD, atomic_json
    from PIL import Image
    phase("registry-read-before")
    state = store.read()
    phase("registry-read-complete")
    dossier_path = None
    if bool(args.entity) != bool(args.stage):
        raise ValueError("--entity and --stage must be supplied together")
    if args.entity:
        if not all(re.fullmatch("[A-Za-z0-9][A-Za-z0-9_-]{0,79}", item) for item in (args.entity, args.stage)):
            raise ValueError("Entity and stage require safe identifiers")
        if not any(entity["id"] == args.entity for entity in state["project"]["entities"]):
            raise ValueError("Unknown entity: " + args.entity)
        dossier_path = safe_report(data, "reports/character-packages/" + args.entity + ".json")
        dossier(dossier_path, args.entity)
    if len(args.reference) > 12 or len(set(args.reference)) != len(args.reference):
        raise ValueError("Use at most12 unique registered references")
    phase("native-path-before")
    source = Path(args.native_path).expanduser().resolve(strict=True)
    if not source.is_file() or not 0 < source.stat().st_size <= MAX_UPLOAD:
        raise ValueError("Native image must be a file between1 byte and40MiB")
    prompt_path = Path(args.prompt_file).expanduser().resolve(strict=True)
    if prompt_path.stat().st_size > 100000:
        raise ValueError("Prompt file exceeds100000 bytes")
    prompt_bytes = prompt_path.read_bytes()
    prompt = prompt_bytes.decode("utf-8")
    if not prompt.strip():
        raise ValueError("Exact generation prompt is required")
    name = args.output_name
    if not name or len(name) > 160 or name in (".", "..") or Path(name).name != name or "\\" in name or any(ord(c) < 32 for c in name):
        raise ValueError("Output name must be a plain filename, maximum160 characters")
    phase("prompt-read-complete")
    refs = []
    for identifier in args.reference:
        item = next((a for a in state["assets"] if a["id"] == identifier), None)
        if item is None:
            raise ValueError("Unknown reference: " + identifier)
        store.asset_path(identifier, state)
        refs.append({"assetId": identifier, "sha256": item["sha256"]})
    phase("reference-paths-complete")
    raw = source.read_bytes()
    phase("image-read-complete")
    if not raw or len(raw) > MAX_UPLOAD:
        raise ValueError("Native image changed size while reading")
    phase("image-open-before")
    with Image.open(io.BytesIO(raw)) as image:
        if image.format not in ("PNG", "JPEG", "WEBP") or image.width * image.height > 80000000:
            raise ValueError("Unsupported native image format or dimensions")
        image.verify()
    phase("image-verify-complete")
    sha = hashlib.sha256(raw).hexdigest()
    existing = next((a for a in state["assets"] if a["sha256"] == sha), None)
    if existing and (existing.get("reviewStatus") != "unreviewed" or existing.get("provenance", {}).get("prompt") != prompt
                     or existing.get("provenance", {}).get("referenceIds") != args.reference):
        raise ValueError("These bytes already have different provenance or review status; existing record preserved")
    phase('validation-complete')
    if getattr(args, 'validate_only', False):
        return {'validationOnly': True, 'sha256': sha, 'bytes': len(raw), 'referenceIds': args.reference,
                'alreadyRegistered': bool(existing), 'mutated': False}
    validated_at = now()
    phase("generated-copy-before")
    generated = data / "generated"
    generated.mkdir(exist_ok=True)
    if not generated.resolve().is_relative_to(data):
        raise ValueError("Generated output directory escapes Studio data")
    destination = generated / (sha[:16] + "-" + name)
    if destination.exists():
        if not destination.is_file() or destination.read_bytes() != raw:
            raise ValueError("Output filename already contains different bytes")
    else:
        with destination.open("xb") as stream:
            stream.write(raw)
    if destination.read_bytes() != raw:
        raise ValueError("Native copy verification failed")
    copied_at = now()
    provenance = {"source": "native-imagegen", "tool": args.tool, "nativeOutputPath": str(source), "nativeSha256": sha,
                  "prompt": prompt, "promptSha256": hashlib.sha256(prompt_bytes).hexdigest(),
                  "promptFile": str(prompt_path), "referenceIds": args.reference, "inputAssets": refs,
                  "registeredBy": "studio-client/register-image.py"}
    phase("asset-register-before")
    asset = existing or store.import_asset(destination, name=name, provenance=provenance, review_status="unreviewed")
    phase("asset-register-complete")
    completed_at = now()
    card = {"type": "WorkflowCard", "title": name, "text": "Unreviewed candidate. Original image available at full size.",
            "assetIds": [asset["id"]], "actions": []}
    result = {"assetId": asset["id"], "sha256": asset["sha256"], "bytes": asset["bytes"],
            "reviewStatus": asset["reviewStatus"], "nativePath": str(source), "generatedPath": str(destination),
            "reused": bool(existing), "kernelRelease": manifest["hash"], "workflowCard": card,
            "timing": {"startedAt": started_at, "validatedAt": validated_at, "copiedAt": copied_at,
                       "registeredAt": completed_at, "registrationSeconds": round(time.monotonic() - started, 6)}}
    if dossier_path:
        result["dossierPath"] = str(dossier_path)
        result["entityId"], result["stage"] = args.entity, args.stage
        phase("dossier-lock-before")
        with store.lock():
            phase("dossier-lock-acquired")
            value = dossier(dossier_path, args.entity)
            stage = value["stages"].setdefault(args.stage, {"candidates": []})
            receipt = {**result, "provenance": asset.get("provenance", {})}
            previous = next((candidate for candidate in stage["candidates"] if candidate.get("assetId") == asset["id"]), None)
            if previous is None:
                stage["candidates"].append(receipt)
            value["updatedAt"] = now()
            atomic_json(dossier_path, value)
        result["timing"]["dossierWrittenAt"] = now()
        result["timing"]["helperTotalSeconds"] = round(time.monotonic() - started, 6)
    phase("receipt-ready")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    runtime = parser.add_mutually_exclusive_group(required=True)
    runtime.add_argument("--runtime-dir")
    runtime.add_argument("--kernel-root", help="Explicit verified frozen stable release directory")
    parser.add_argument("--data-dir", help="Existing data directory; defaults to runtime deployment manifest")
    parser.add_argument("--setup-toolchain", action="store_true")
    parser.add_argument("--trace-phases", "--trace", dest="trace_phases", action="store_true", help="Bounded phase/timing labels on stderr; no prompts, pixels or credentials")
    parser.add_argument("--validate-only", action="store_true", help="Verify original/reference bytes without copying/registering or writing Store settings")
    parser.add_argument("--entity")
    parser.add_argument("--stage")
    parser.add_argument("--native-path")
    parser.add_argument("--prompt-file")
    parser.add_argument("--reference", action="append", default=[])
    parser.add_argument("--output-name")
    parser.add_argument("--tool", default="image_gen.imagegen", choices=["image_gen.imagegen"], help="Actual source tool asserted by caller; not inferred from image pixels")
    args = parser.parse_args()
    if args.trace_phases:
        import faulthandler
        faulthandler.enable(file=sys.stderr)
        faulthandler.dump_traceback_later(8, repeat=False, file=sys.stderr)
    try:
        if args.validate_only and args.setup_toolchain:raise ValueError('Validation cannot setup toolchain')
        if not args.setup_toolchain and not all((args.native_path, args.prompt_file, args.output_name)):
            raise ValueError("--native-path, --prompt-file and --output-name are required")
        result = setup_toolchain(args) if args.setup_toolchain else register(args)
    except Exception as exc:
        print(json.dumps({"error": {"code": "registration_failed", "message": str(exc)},
                          "advice": "Inspect existing assets before retrying; no approval or selection was performed."}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
