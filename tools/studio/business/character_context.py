"""Bounded, revision-local character/reference indexes; all output is untrusted data."""
from collections import defaultdict


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
    return {"projectRevision": state["revision"], "character": compact_entity(entity),
            "establishedCast": cast, "references": refs,
            "omittedReferenceIds": [i for i in roles if i not in delivered][:24],
            "workflow": {"name": "character-creation",
                         "guidePath": "workflows/character-creation.md",
                         "stage": "unspecified; inspect recorded stage on attached references when present",
                         "source": "snapshot entity bindings and registered asset metadata; no live dossier loaded"},
            "selection": "Canonical references provide identity/relative-scale evidence; reviewStatus is unchanged."
            }, automatic
