"""Bounded Markdown hydration and artifact-based resumable character stages."""
import hashlib
import json
import re
from model import StudioError

SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")
REQUIRED = ("solo", "interactions")

def read_document(root, relative, maximum=24000):
    try:
        path = root / relative
        if not path.resolve().is_relative_to(root.resolve()):
            return {"path": relative, "error": "path outside data"}
        with path.open("rb") as stream:
            raw = stream.read(maximum + 1)
        if len(raw) > maximum:
            return {"path": relative, "error": "oversized document", "maximumBytes": maximum, "bytesRead": len(raw), "truncated": True}
        return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "text": raw.decode("utf-8")}
    except (OSError, UnicodeError, TypeError):
        return None

def read_json(root, relative, maximum):
    doc = read_document(root, relative, maximum)
    try:
        return json.loads(doc["text"]) if doc and "text" in doc else None
    except (ValueError, TypeError):
        return None

def load_run(store):
    value = read_json(store.root, "workflows/cast-run.json", 160000)
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        return None
    rows = value.get("characters")
    if not isinstance(rows, list) or len(rows) > 100:
        return None
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not SAFE_ID.fullmatch(row["id"]) or row["id"] in ids:
            return None
        ids.add(row["id"])
        if not isinstance(row.get("outputs", []), list) or not isinstance(row.get("stageReceipts", {}), dict):
            return None
        for role, receipt in row.get("stageReceipts", {}).items():
            if role not in REQUIRED or not isinstance(receipt, dict):
                return None
    return value

def verified_asset(store, state, receipt):
    if not isinstance(receipt, dict):
        return False
    asset = next((a for a in state.get("assets", []) if a["id"] == receipt.get("assetId")), None)
    if not asset or asset.get("sha256") != receipt.get("sha256") or not asset.get("provenance"):
        return False
    try:
        path = store.asset_path(asset["id"], state)
        if not path.is_file() or path.stat().st_size > 40 * 1024 * 1024:
            return False
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest() == receipt["sha256"]
    except (OSError, ValueError, KeyError, StudioError):
        return False

def reconcile_character(store, state, row):
    package = read_json(store.root, "reports/character-packages/" + row["id"] + ".json", 512000)
    package = package if isinstance(package, dict) and package.get("entityId") == row["id"] else {}
    stages = package.get("stages", {})
    stages = stages if isinstance(stages, dict) else {}
    valid = {}
    for role in REQUIRED:
        value = stages.get(role, {})
        candidates = value.get("candidates", []) if isinstance(value, dict) else []
        candidates = candidates if isinstance(candidates, list) else []
        legacy = row.get("stageReceipts", {}).get(role)
        if legacy and legacy.get("receiptKind") == "legacy-catalog-provenance":
            candidates = candidates + [legacy]
        for candidate in reversed(candidates[-40:]):
            if not isinstance(candidate, dict):
                continue
            if candidate.get("qaDisposition") == "needs-repair":
                continue
            if candidate.get("receiptKind") != "legacy-catalog-provenance" and (candidate.get("entityId") != row["id"] or candidate.get("stage") != role):
                continue
            if verified_asset(store, state, candidate):
                valid[role] = {k: candidate.get(k) for k in ("assetId", "sha256", "nativePath", "generatedPath", "receiptKind")}
                break
    if len(valid) == 2 and valid["solo"]["assetId"] == valid["interactions"]["assetId"]:
        valid.pop("interactions")
    missing = [role for role in REQUIRED if role not in valid]
    return {"stages": valid, "missingStages": missing, "nextStage": missing[0] if missing else None,
            "complete": not missing, "claimedStatus": row.get("status"),
            "status": row.get("status") if not missing and row.get("status") in ("accepted", "completed") else "produced" if not missing else "partial" if valid else "pending"}

def workflow_context(store, entity_id=None, details=True):
    run = load_run(store)
    if not run:
        return {"manifestPath": "workflows/cast-run.json", "error": "Cast manifest absent, malformed or oversized; art preserved.",
                "nextEntityId": None, "remaining": [], "characters": []}
    state = store.read()
    rows = []
    for original in run["characters"]:
        row = dict(original)
        row.update(reconcile_character(store, state, row))
        rows.append(row)
    next_id = next((c["id"] for c in rows if not c["complete"]), None)
    selected = entity_id or next_id
    entry = next((c for c in rows if c["id"] == selected), None)
    result = {"manifestPath": "workflows/cast-run.json", "nextEntityId": next_id,
              "remaining": [c["id"] for c in rows if not c["complete"]], "selected": entry,
              "characters": [{k: c.get(k) for k in ("id", "canonicalName", "status", "dossierPath", "evidencePath", "outputs", "nextStage", "missingStages")} for c in rows],
              "notetaker": run.get("notetaker"), "authority": "Persistent product data; no approval/publication authority."}
    if not details:
        result["selected"] = None
        return result
    result.update(guide=read_document(store.root, "workflows/character-creation.md", 22000),
                  runContract=read_document(store.root, "workflows/cast-run.md", 10000),
                  dossier=read_document(store.root, "workflows/characters/" + selected + "/README.md", 8000) if selected else None,
                  packageReceipts=entry.get("stages") if entry else None)
    if entry:
        evidence = read_json(store.root, entry.get("evidencePath", ""), 2000000)
        if isinstance(evidence, dict):
            result["evidence"] = {"path": entry.get("evidencePath"), "bibliography": evidence.get("bibliography", [])[:4],
                                  "inspectedVisualEvidence": evidence.get("inspectedVisualEvidence", [])[:8],
                                  "registeredReferences": evidence.get("registeredReferences", [])[:8]}
    if len(json.dumps(result, ensure_ascii=False).encode()) > 48000:
        result.pop("evidence", None)
        result["budgetNote"] = "Evidence preview omitted at aggregate 48KB cap; read persistent index."
    if len(json.dumps(result, ensure_ascii=False).encode()) > 48000:
        result.pop("runContract", None)
        result["budgetNote"] = "Run contract omitted at aggregate 48KB cap; read persistent path."
    if len(json.dumps(result, ensure_ascii=False).encode()) > 48000:
        result["characters"] = [{k: c.get(k) for k in ("id", "status", "nextStage")} for c in rows]
        result["selected"] = {k: entry.get(k) for k in ("id", "status", "nextStage", "missingStages", "stages", "dossierPath", "evidencePath")} if entry else None
        result["budgetNote"] = "Large optional manifest fields omitted at aggregate budget; persistent manifest remains authoritative."
    return result

def self_test():
    assert REQUIRED == ("solo", "interactions")
    assert SAFE_ID.fullmatch("rabbit") and not SAFE_ID.fullmatch("../rabbit")
    return True

def save_progress(store, verified=None):
    """Reconcile and durably save stage evidence, without touching review authority."""
    from store import atomic_json
    run = load_run(store)
    if not run:
        raise ValueError("Cannot save malformed cast manifest")
    state = store.read()
    # Internal finish callers may reuse evidence checked during this invocation.
    # Routes never accept this map from a request body.
    verified = verified or {}
    updates = {c["id"]: verified[c["id"]] if c["id"] in verified else reconcile_character(store, state, c)
               for c in run["characters"]}
    with store.lock():
        current = load_run(store)
        if not current:
            raise ValueError("Cast manifest changed incompatibly")
        for row in current["characters"]:
            if row["id"] in updates:
                row.update(updates[row["id"]])
        current["nextEntityId"] = next((c["id"] for c in current["characters"] if not c.get("complete")), None)
        atomic_json(store.root / "workflows/cast-run.json", current)
    return current
