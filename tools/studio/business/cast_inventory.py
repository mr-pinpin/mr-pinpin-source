"""Explicit evidence index for a resumable cast run; never approves artwork."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CAST = [
 ("pinpin", "Mr. PinPin", ["Пин-Пин", "ПинПин", "PinPin", "ШипШип", "ФырФыркин", "ЁжЁжик", "Колючий Шарик", "Пиковый Мистер", "ЁжЁженька"], "child in published family; original exact age not stated"),
 ("pompom", "Mr. PomPom", ["PomPom", "ПомПом"], "infant in published family"),
 ("mama", "Mama", ["Mama", "мама", "Мама", "мать"], "adult parent"),
 ("papa", "Papa", ["Papa", "папа", "Папа", "отец"], "adult parent"),
 ("rabbit", "Rabbit / Lulu", ["Rabbit", "rabbit", "Лулу", "ЛуЛу", "Lulu"], "peer companion; exact age not stated"),
 ("elder", "The Elder", ["Старейшина", "Шипостав", "Шипокол", "Шипастойпалки", "Спайкстейв", "Тарин", "Elder"], "old hedgehog mentor; source name variants provisionally grouped by narrative role"),
 ("scooby", "Scooby", ["Scooby", "Скуби"], "large dog; age not stated"),
 ("beaver", "Beaver", ["Beaver", "Бобр", "бобр"], "adult builder in adaptation"),
 ("mama-beaver", "Mama Beaver", ["Mama Beaver", "Мама Бобриха", "бобриха"], "adult parent in adaptation"),
 ("beaver-kits", "Two little beavers", ["little beavers", "kits", "бобрята"], "young sibling pair; separate reusable group package"),
 ("bear", "Mr. Bear", ["Mr. Bear", "Bear", "Медведь", "медвед"], "adult supporting builder; adaptation design"),
 ("talking-duck", "Talking bath Duck", ["duck", "Duck", "утк", "Утк"], "magically sentient duck, separate from ordinary toy prop"),
 ("tutu", "Tutu", ["Туту", "ТуТу", "Tutu"], "squirrel friend (chapter 9); exact age not stated"),
 ("pipilini", "Mr. Pipilini", ["Пипилини", "Пипилино", "Pipilini", "Pipilino"], "older migrating bird with weak wings; spelling variants in continuous story"),
 ("oreshek", "Elder Oreshek", ["Орешек", "Oreshek"], "squirrel elder; distinct from hedgehog Elder"),
 ("lilia", "Lilia", ["Лилия", "Лили", "Lilia"], "magical squirrel; exact age not stated"),
 ("hedgehog-cousins", "Young hedgehog cousins", ["кузен", "cousin"], "younger hedgehog relatives in chapter 38; unnamed recurring group"),
 ("spring-birds", "Two spring birds", ["birds", "птич", "птиц"], "small birds in bath adaptation; incidental pair retained as supporting group"),
 ("squirrel-community", "Forest squirrel community", ["белк", "Белк", "squirrels"], "recurring mixed squirrel community; unnamed cast group, not named invented individuals"),
 ("migrating-bird-family", "Pipilini's migrating family", ["семейств", "Пипилини", "Пипилино"], "recurring bird family from chapter 8; broad family matches require contextual review"),
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def bootstrap(store, source):
    """Run explicitly once or reconcile new evidence without resetting existing progress."""
    source = Path(source)
    root = store.root
    state = store.read()
    book_path = source / "docs/storyboard/book.json"
    book = json.loads(book_path.read_text())
    manifest_path = root / "workflows/cast-run.json"
    prior = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    previous = {c["id"]: c for c in prior.get("characters", [])}
    completed = {
      "pompom": ["asset-483201f4d30299518e37b401", "asset-56362912ae9b6173ac8464de"],
      "mama": ["asset-0409122a3c93ef73014f6338", "asset-4a23599bb5c8411f29297d55"],
      "papa": ["asset-6d619138c33f8111b5b1ff68", "asset-1733f4d737f28fd9a90a2a05"]}
    assets = {a["id"]: a for a in state["assets"]}
    entities = {e["id"]: e for e in state["project"]["entities"]}
    records = []
    for identifier, name, aliases, life_stage in CAST:
        evidence = []
        for chapter in book["chapters"]:
            for i, block in enumerate(chapter["blocks"]):
                text = "\n".join(p.get("text", "") for p in block if p.get("type") == "text")
                if any(alias.casefold() in text.casefold() for alias in aliases):
                    images = []
                    for piece in block:
                        if piece.get("type") == "image":
                            path = (book_path.parent / piece["src"]).resolve()
                            images.append({"source": piece["src"], "path": str(path), "sha256": digest(path)})
                    evidence.append({"kind": "original", "sourcePath": str(book_path), "sourceSha256": digest(book_path),
                      "chapterId": chapter["id"], "chapterTitle": chapter["title"], "blockIndexZeroBased": i,
                      "excerpt": text, "images": images})
        for story_path in sorted((source / "docs/storyboard/stories").glob("*.json")):
            story = json.loads(story_path.read_text())
            for scene in story.get("scenes", []):
                text = json.dumps({k: scene.get(k) for k in ("paragraphs", "alt", "caption", "captions")}, ensure_ascii=False)
                if any(alias.casefold() in text.casefold() for alias in aliases):
                    image = scene.get("image")
                    path = source / "docs" / image if isinstance(image, str) else None
                    evidence.append({"kind": "published", "sourcePath": str(story_path), "sourceSha256": digest(story_path),
                      "chapterId": story.get("id"), "sceneId": scene.get("id"), "excerpt": text,
                      "imagePath": str(path) if path else None, "imageSha256": digest(path) if path else None})
        entity = entities.get(identifier, {})
        refs = [assets[a] for a in entity.get("referenceIds", []) if a in assets]
        outputs = [assets[a] for a in completed.get(identifier, []) if a in assets]
        old = previous.get(identifier, {})
        record = {"id": identifier, "canonicalName": name, "aliases": aliases, "exactAge": "not stated",
          "evidencedLifeStage": life_stage, "status": old.get("status", "produced" if len(outputs) == 2 else "pending"),
          "dossierPath": "workflows/characters/" + identifier + "/README.md", "evidencePath": "workflows/characters/" + identifier + "/evidence.json",
          "evidenceCount": len(evidence), "registeredReferenceIds": entity.get("referenceIds", []),
          "outputs": old.get("outputs", [{"assetId": a["id"], "sha256": a.get("sha256")} for a in outputs]),
          "constraints": {k: entity.get(k, "not yet designed; use indexed original evidence and approved book style") for k in ("identity", "scale", "geometry")}}
        folder = root / "workflows/characters" / identifier
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "evidence.json").write_text(json.dumps({"character": record, "bibliography": evidence, "registeredReferences": refs, "existingOutputs": outputs}, ensure_ascii=False, indent=2))
        if not (folder / "README.md").exists():
            (folder / "README.md").write_text("# " + name + "\n\nExact age: **not stated**. Life stage: " + life_stage + ".\n\n"
              "Aliases/source variants: " + ", ".join(aliases) + ". Alias grouping for the hedgehog mentor and Rabbit/Lulu is a narrative inference, not an invented canonical fact.\n\n"
              "Canonical evidence and bibliography: [evidence.json](evidence.json), with original chapter/block indices, published scenes, paths and full hashes. Broad lexical matches are discovery evidence; inspect the cited block before treating it as a fact.\n\n"
              "Identity/scale constraints: " + json.dumps(record["constraints"], ensure_ascii=False) + ".\n\n"
              "Status: " + record["status"] + ". Existing output IDs: " + ", ".join(a["id"] for a in outputs) + ".\n\n"
              "Exact prompts, native files, hashes, reference bindings and timings: existing asset provenance in evidence.json and automatic registration receipts at ../../../reports/character-packages/" + identifier + ".json. Earlier family records remain in workflows/ and reports/. Unknown historical timings remain unknown. New source interpretations or unsourced designs must be labeled proposals. No personal Miguel review or publication is inferred.\n")
        records.append(record)
    manifest = {"schemaVersion": 1, "updatedAt": datetime.now(timezone.utc).isoformat(), "characters": records,
      "nextEntityId": next((c["id"] for c in records if c["status"] not in ("produced", "accepted", "completed")), None),
      "notetaker": {"available": False, "evidence": "Coordinator reports bounded connected-tool/plugin/repo discovery found no configured Notetaker integration.", "fallback": "Durable Markdown notes, explicitly not Notetaker."},
      "audit": {"originalChaptersIndexed": len(book["chapters"]), "originalSource": str(book_path), "sourceSha256": digest(book_path),
         "scope": "Named individuals and recurring adaptation groups; lexical bibliography requires contextual reading.",
         "dispositions": "Unnamed butterfly/rabbit crowds, raccoon honey anecdote and general forest populations remain incidental groups, not invented named characters. Ordinary bath toy remains prop; sentient Duck has a separate package. Mentor name variants are provisional aliases; Oreshek is a distinct squirrel elder.",
         "agePolicy": "No exact numeric age found in indexed cast evidence; descriptive old/young/infant are life stages, not dates."}}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return {"count": len(records), "next": manifest["nextEntityId"], "retained": list(completed)}

def ensure_registry(store):
    """Add only missing draft cast entries; preserve original entities and bindings."""
    state = store.read()
    project = state["project"]
    existing = {e["id"] for e in project["entities"]}
    added = []
    for identifier, name, aliases, life_stage in CAST:
        if identifier in existing:
            continue
        project["entities"].append({"id": identifier, "name": name, "kind": "character", "identity": life_stage,
          "scale": "Not measured; use original/published indexed visual evidence", "geometry": "",
          "referenceIds": [], "reviewStatus": "unreviewed", "sourceEvidencePath": "workflows/characters/" + identifier + "/evidence.json",
          "notes": "Draft inventory entry. Alias interpretation and new visual details are proposals; no personal review recorded."})
        added.append(identifier)
    if added:
        store.save_project(project, state["revision"])
    return added

def record_package(store, identifier, asset_ids, qa_note, timing_path=None):
    """Persist produced status without changing approval, selection or original references."""
    from store import atomic_json
    state = store.read()
    assets = {a["id"]: a for a in state["assets"]}
    if len(asset_ids) != 2 or len(set(asset_ids)) != 2 or any(a not in assets for a in asset_ids):
        raise ValueError("A registered solo and interaction page are required")
    from .cast_workflow import reconcile_character
    resolved = reconcile_character(store, state, {"id": identifier})
    if not resolved["complete"] or [resolved["stages"][role]["assetId"] for role in ("solo", "interactions")] != asset_ids:
        raise ValueError("Required stages must have matching valid registration receipts")
    with store.lock():
        path = store.root / "workflows/cast-run.json"
        run = json.loads(path.read_text())
        character = next(c for c in run["characters"] if c["id"] == identifier)
        character.update(status="produced", outputs=[{"assetId": a, "sha256": assets[a]["sha256"]} for a in asset_ids],
                         qaNote=qa_note, timingPath=timing_path, completedAt=datetime.now(timezone.utc).isoformat())
        run["nextEntityId"] = next((c["id"] for c in run["characters"] if c["status"] not in ("produced", "accepted", "completed")), None)
        run["updatedAt"] = datetime.now(timezone.utc).isoformat()
        atomic_json(path, run)
        folder = store.root / "workflows/characters" / identifier
        evidence_path = folder / "evidence.json"
        evidence = json.loads(evidence_path.read_text())
        evidence["character"] = character
        evidence["existingOutputs"] = [assets[a] for a in asset_ids]
        atomic_json(evidence_path, evidence)
        doc = folder / "README.md"
        text = doc.read_text().split("\n## Current package result\n")[0]
        text += "\n## Current package result\n\nStatus: **produced**, registered unreviewed drafts.\n\n"
        for stage, asset_id in zip(("Solo studies", "Interactions"), asset_ids):
            asset = assets[asset_id]
            text += "- " + stage + ": `" + asset_id + "`, SHA-256 `" + asset["sha256"] + "`.\n"
        text += "\nQA: " + qa_note + "\n\nExact prompts, native paths/hashes and registration receipts: ../../../reports/character-packages/" + identifier + ".json. Generation timings: " + str(timing_path) + ". No personal Miguel acceptance or publication inferred.\n"
        doc.write_text(text)
    from .cast_workflow import save_progress
    run = save_progress(store)
    return {"next": run["nextEntityId"], "remaining": [c["id"] for c in run["characters"] if not c.get("complete")]}
