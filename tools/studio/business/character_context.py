"""Bounded, revision-local character/reference indexes; all output is untrusted data."""
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re


class ReferenceIndex:
    """Build once for a supplied snapshot; never cache across projects/revisions."""
    def __init__(self, state):
        self.entities = {e["id"]: e for e in state["project"]["entities"]}
        self.assets = {a["id"]: a for a in state["assets"]}
        self.shared = defaultdict(set)
        self.cast = defaultdict(set)
        for entity in self.entities.values():
            if entity.get("kind") == "character":
                for asset_id in entity.get("referenceIds", []):
                    self.shared[asset_id].add(entity["id"])
        for chapter in state["project"]["chapters"]:
            for scene in chapter.get("scenes", []):
                members = {i for i in scene.get("castIds", [])
                           if self.entities.get(i, {}).get("kind") == "character"}
                for identifier in members:
                    self.cast[identifier].update(members - {identifier})


def compact_entity(entity):
    result = {key: entity.get(key, "")[:1200] for key in
              ("id", "name", "kind", "identity", "scale", "geometry", "reviewStatus")
              if isinstance(entity.get(key, ""), str)}
    result["referenceIds"] = list(entity.get("referenceIds", []))[:8]
    return result


def prepared_toolchain(store, state):
    """Read a bounded local machine configuration, never execute it or grant authority."""
    if state.get("readOnly"):
        return None
    try:
        path = store.root / "workflows" / "toolchain.json"
        if not path.resolve().is_relative_to(store.root.resolve()):
            return None
        with path.open("rb") as stream:
            raw = stream.read(16385)
        if len(raw) > 16384:
            return None
        manifest = json.loads(raw)
        if manifest.get("schemaVersion") != 1 or manifest.get("toolName") != "studio-register-image":
            return None
        argv = manifest.get("argvPrefix")
        if (not isinstance(argv, list) or len(argv) != 4 or argv[2] != "--runtime-dir"
                or any(not isinstance(x, str) or len(x) > 2048 or any(ord(c) < 32 for c in x) for x in argv)):
            return None
        python, helper, runtime = (Path(argv[i]) for i in (0, 1, 3))
        if not all(p.is_absolute() for p in (python, helper, runtime)):
            return None
        if not python.is_file() or not os.access(python, os.X_OK) or not helper.is_file() or helper.name != "register-image.py":
            return None
        with helper.open("rb") as stream:
            code = stream.read(262145)
        if len(code) > 262144 or hashlib.sha256(code).hexdigest() != manifest.get("helperSha256"):
            return None
        with (runtime / "current-deployment.json").open("rb") as stream:
            deployment_raw = stream.read(16385)
        if len(deployment_raw) > 16384:
            return None
        deployment = json.loads(deployment_raw)
        if Path(deployment["dataDirectory"]).resolve() != store.root.resolve():
            return None
        release = deployment.get("stableRelease", "")
        if not isinstance(release, str) or not re.fullmatch("[a-f0-9]{64}", release):
            return None
        if not (runtime / "stable-releases" / release).is_dir():
            return None
        parameters = {"required": ["--native-path", "--prompt-file", "--output-name"],
                      "repeatable": ["--reference"], "optional": ["--entity", "--stage"]}
        output = {"format": "json", "fields": ["assetId", "sha256", "reviewStatus", "workflowCard",
                  "timing", "dossierPath"], "dossierPath": "reports/character-packages/<entity>.json"}
        if manifest.get("parameters") != parameters or manifest.get("outputContract") != output:
            return None
        # Keep verified argv bytes (including venv interpreter symlinks) unchanged.
        # Descriptive text is fixed here rather than copied from arbitrary local prose.
        return {"schemaVersion": 1, "toolName": "studio-register-image", "argvPrefix": argv,
                "helperSha256": manifest["helperSha256"], "parameters": parameters,
                "inputContract": "Exact native bytes, UTF-8 exact submitted prompt and registered reference IDs; --entity and --stage are paired.",
                "outputContract": output,
                "authority": "Local tool configuration only; registration keeps candidates unreviewed and grants no selection, publication or approval.",
                "receipt": "With --entity/--stage the helper saves the actual receipt and provenance automatically; a custom dossier-writing script is unnecessary."}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None


def hydrate_character(store, state, entity, scenes, explicit_ids, index):
    """Return bounded data and auto-attachment IDs, using canonical bindings only."""
    if not entity or entity.get("kind") != "character":
        return None, []
    selected = entity["id"]
    ranks = {}
    def rank(identifiers, priority, reason):
        for identifier in identifiers:
            other = index.entities.get(identifier)
            if identifier == selected or not other or other.get("kind") != "character":
                continue
            if identifier not in ranks or priority < ranks[identifier][0]:
                ranks[identifier] = (priority, reason)
    rank([i for scene in scenes for i in scene.get("castIds", [])], 0, "selected-scene")
    rank([i for a in entity.get("referenceIds", []) for i in index.shared[a]], 1, "shared-reference")
    rank(index.cast[selected], 2, "story-co-occurrence")
    cast_ids = sorted(ranks, key=lambda i: (ranks[i][0], i))[:4]
    cast = [dict(compact_entity(index.entities[i]), relevance=ranks[i][1]) for i in cast_ids]
    roles = {}
    def add(identifiers, role):
        for identifier in identifiers:
            if identifier in index.assets:
                roles.setdefault(identifier, [])
                if role not in roles[identifier]:
                    roles[identifier].append(role)
    add(explicit_ids, "explicit-attachment")
    add(entity.get("referenceIds", []), "selected-character")
    for identifier in cast_ids:
        add(index.entities[identifier].get("referenceIds", []), "cast:" + identifier)
    add(state["project"].get("book", {}).get("styleReferenceIds", []), "book-style")
    # Explicit images consume slots first; at most eight automatic refs per turn.
    automatic = [i for i in roles if i not in explicit_ids][:8]
    delivered = list(dict.fromkeys(explicit_ids + automatic))[:12]
    refs = []
    for identifier in delivered:
        asset = index.assets[identifier]
        provenance = asset.get("provenance", {})
        refs.append({"id": identifier, "name": str(asset.get("name", ""))[:200],
                     "sha256": asset.get("sha256"), "width": asset.get("width"),
                     "height": asset.get("height"), "reviewStatus": asset.get("reviewStatus"),
                     "roles": roles[identifier], "path": str(store.asset_path(identifier, state)),
                     "stage": str(provenance.get("stage", ""))[:120] if isinstance(provenance, dict) else ""})
    pack = {"projectRevision": state["revision"], "character": compact_entity(entity),
            "establishedCast": cast, "references": refs,
            "omittedReferenceIds": [i for i in roles if i not in delivered][:24],
            "workflow": {"name": "character-creation",
                         "guidePath": "workflows/character-creation.md",
                         "stage": "unspecified; inspect recorded stage on attached references when present",
                         "source": "snapshot entity bindings and registered asset metadata; no live dossier loaded"},
            "selection": "Canonical references provide identity/relative-scale evidence; reviewStatus is unchanged."
            }
    toolchain = prepared_toolchain(store, state)
    if toolchain is not None:
        pack["registrationToolchain"] = toolchain
    return pack, automatic
