"""Real agent handoffs, immutable outputs and explicit user review."""
import copy
import json
from pathlib import Path
from model import StudioError, JOB_KINDS, now, new_id, find
from store import atomic_bytes, digest

HEADER = """Mr. PinPin production handoff v1
Use the active Codex agent's built-in image tool; this queue does not call an external paid API.
Inspect all role-assigned references before generation. Preserve approved identities, relative scale,
room/door/window geography, gaze and physical contact. Use warm dimensional book rendering.
Show real actions and varied cameras; no forced manic smiles or fatigue. Respect causal setup,
attempt, consequence, family reaction and earned payoff. Preserve approved originals; edit a pristine
input rather than repeatedly degrading a derivative. Keep native output, exact ACTUAL submitted
prompt, actual reference hashes, and candidate review separately from this planned handoff.
Never automatically publish or silently replace selected artwork.
"""
PANORAMA = """Panorama: use TWO distinct inputs with separate roles: a successful seamless panorama
as the method/projection example, and the requested location as identity/decoration reference.
Generate one continuous 2:1 spherical image, not six independent faces. Preserve the source view;
inspect poles and wrap in the actual viewer. Record repair views/masks and use tools/panoramas for
deterministic projection conversion. Measured Blender geometry and artistic camera changes are
different workflows; do not claim measured consistency from an illustration alone.
"""



ORBIT = """Orbit video handoff: prepare a conventional source still with explicit subject and place
references. Reuse the documented tractor-orbit workflow. Request one coherent camera path around
a stationary subject; do not treat a rectangular video as a spherical panorama or measured 3D.
Record exact prompt, input hashes, model, settings, actual duration and output hash. Inspect the
full circuit, silhouette/detail stability and endpoint join. Keep the original output and a
separate seek-friendly derivative. This queue does not execute a paid video call or auto-retry.
Return a text artifact with the immutable output manifest and review evidence; video ingestion
requires a reviewed media registration before the browser can serve it.
"""


def _entity_role(kind):
    return {"character": "character-identity", "location": "location-identity",
            "prop": "prop-geometry", "style": "book-style",
            "panorama": "seamless-panorama"}[kind]


def create_job(store, request):
    if request.get("kind") not in JOB_KINDS:
        raise StudioError("Unknown job kind")
    instruction = request.get("instruction", "")
    if not isinstance(instruction, str) or not instruction.strip():
        raise StudioError("Describe the requested work")
    if len(instruction) > 100_000:
        raise StudioError("Instruction is too long")
    for field in ("sceneIds", "referenceIds", "referenceBindings"):
        if not isinstance(request.get(field, []), list):
            raise StudioError(field + " must be an array")
    for field in ("sceneIds", "referenceIds"):
        if any(not isinstance(value, str) for value in request.get(field, [])):
            raise StudioError(field + " must contain string IDs")
    if any(not isinstance(value, dict) for value in request.get("referenceBindings", [])):
        raise StudioError("referenceBindings must contain objects")

    def create(state):
        project = state["project"]
        retry_of = request.get("retryOf")
        if retry_of is not None:
            find(state["jobs"], retry_of, "retry parent job")
        scenes, entities = [], []
        chapter_id = request.get("chapterId")
        scene_ids = list(dict.fromkeys(request.get("sceneIds", [])))
        chapter = find(project["chapters"], chapter_id, "chapter") if chapter_id else None
        if scene_ids and chapter is None:
            raise StudioError("Scene jobs require chapterId")
        if chapter:
            scenes = [copy.deepcopy(find(chapter["scenes"], sid, "scene")) for sid in scene_ids]
        used_entities = set()
        if request.get("entityId"):
            used_entities.add(request["entityId"])
        for scene in scenes:
            used_entities.update(scene.get("castIds", []))
            used_entities.update(scene.get("propIds", []))
            if scene.get("locationId"):
                used_entities.add(scene["locationId"])
        for entity_id in sorted(used_entities):
            entities.append(copy.deepcopy(find(project["entities"], entity_id, "entity")))
        bindings = {}

        def bind(asset_id, role, entity_id=None):
            asset = find(state["assets"], asset_id, "reference asset")
            if not isinstance(role, str) or not role.strip():
                raise StudioError("Every reference needs a role")
            if asset_id not in bindings:
                bindings[asset_id] = {"assetId": asset_id, "role": role, "roles": [],
                                      "entityIds": [], "sha256": asset["sha256"],
                                      "name": asset["name"], "url": asset["url"],
                                      "path": str(store.asset_path(asset_id, state)),
                                      "reviewStatus": asset.get("reviewStatus", "unreviewed")}
            binding = bindings[asset_id]
            if role not in binding["roles"]:
                binding["roles"].append(role)
            if entity_id and entity_id not in binding["entityIds"]:
                binding["entityIds"].append(entity_id)

        for entity in entities:
            for asset_id in entity.get("referenceIds", []):
                bind(asset_id, _entity_role(entity["kind"]), entity["id"])
        for asset_id in project.get("book", {}).get("styleReferenceIds", []):
            bind(asset_id, "book-style")
        for scene in scenes:
            if scene.get("imageAssetId"):
                bind(scene["imageAssetId"], "current-scene")
        for asset_id in request.get("referenceIds", []):
            bind(asset_id, "reference")
        for value in request.get("referenceBindings", []):
            bind(value.get("assetId"), value.get("role"), value.get("entityId"))
        if request["kind"] == "cubemap":
            methods = {b["assetId"] for b in bindings.values() if "seamless-panorama" in b["roles"]}
            locations = {b["assetId"] for b in bindings.values() if "location-identity" in b["roles"]}
            if not any(a != b for a in methods for b in locations):
                raise StudioError("Cubemap needs distinct seamless-panorama and location-identity images",
                                  "cubemap_references")
        identifier = new_id("job")
        snapshot = {"chapterId": chapter_id, "scenes": scenes, "entities": entities,
                    "bookContinuity": project.get("book", {}).get("continuity", ""),
                    "references": list(bindings.values())}
        if request["kind"] == "story-plan":
            snapshot["book"] = copy.deepcopy(project.get("book", {}))
            snapshot["chapter"] = copy.deepcopy(chapter)
        elif chapter:
            context_ids = set()
            for index, scene in enumerate(chapter["scenes"]):
                if scene["id"] in scene_ids:
                    context_ids.update(scene.get("dependsOn", []))
                    for neighbor in (index - 1, index + 1):
                        if 0 <= neighbor < len(chapter["scenes"]):
                            context_ids.add(chapter["scenes"][neighbor]["id"])
            snapshot["causalContext"] = [
                {key: scene.get(key) for key in ("id", "title", "captions", "action", "stateBefore", "stateAfter")}
                for scene in chapter["scenes"] if scene["id"] in context_ids - set(scene_ids)]
        prompt = HEADER + (PANORAMA if request["kind"] == "cubemap" else ORBIT if request["kind"] == "orbit-video" else "")
        prompt += "\nRequested work:\n" + instruction + "\n\nBound snapshot:\n"
        prompt += json.dumps(snapshot, ensure_ascii=False, indent=2)
        prompt_path = store.root / "jobs" / identifier / "handoff-prompt.txt"
        atomic_bytes(prompt_path, prompt.encode())
        job = {"id": identifier, "kind": request["kind"], "status": "queued",
               "chapterId": chapter_id, "sceneIds": scene_ids, "entityId": request.get("entityId"),
               "instruction": instruction, "prompt": prompt, "promptSha256": digest(prompt.encode()),
               "promptPath": str(prompt_path), "referenceBindings": list(bindings.values()),
               "snapshot": snapshot, "projectRevision": state["revision"], "artifacts": [],
               "feedback": [], "createdAt": now(), "updatedAt": now()}
        if retry_of is not None:
            job["retryOf"] = retry_of
        state["jobs"].append(job)
        store.event(state, "job.queued", jobId=identifier)
        return job
    return store.mutate(create)


def claim_job(store, identifier, agent):
    if not agent or not agent.strip():
        raise StudioError("Agent name is required")
    def claim(state):
        job = find(state["jobs"], identifier, "job")
        if job["status"] == "claimed" and job.get("claimedBy") == agent:
            return job
        if job["status"] != "queued":
            raise StudioError("Job is not queued", "job_state_conflict", 409)
        job.update(status="claimed", claimedBy=agent, claimedAt=now(), updatedAt=now())
        store.event(state, "job.claimed", jobId=identifier, agent=agent)
        return job
    return store.mutate(claim)


def _owned(job, agent):
    if job["status"] != "claimed" or job.get("claimedBy") != agent:
        raise StudioError("Job must be claimed by this agent", "job_state_conflict", 409)


def complete_job(store, identifier, agent, image=None, text=None, scene_id=None,
                 actual_prompt=None, actual_references=None, used_job_prompt=False,
                 used_job_references=False, tool_name=None, visual_pass=False):
    if (image is None) == (text is None):
        raise StudioError("Supply exactly one image or text artifact")
    if actual_prompt is not None and used_job_prompt:
        raise StudioError("Choose actual prompt or explicit used-job-prompt")
    if actual_references is not None and used_job_references:
        raise StudioError("Choose actual references or explicit used-job-references")

    def complete(state):
        job = find(state["jobs"], identifier, "job")
        _owned(job, agent)
        target = scene_id or (job["sceneIds"][0] if len(job["sceneIds"]) == 1 else None)
        if target and target not in job["sceneIds"]:
            raise StudioError("Artifact scene is not a job target")
        if image and len(job["sceneIds"]) > 1 and not target:
            raise StudioError("Multi-scene image job completion requires sceneId")
        artifact_id = new_id("artifact")
        actual = job["prompt"] if used_job_prompt else actual_prompt
        references = copy.deepcopy(job["referenceBindings"]) if used_job_references else None
        if actual_references is not None:
            references = []
            for binding in actual_references:
                asset = find(state["assets"], binding.get("assetId"), "actual reference asset")
                roles = binding.get("roles") or [binding.get("role", "reference")]
                references.append({"assetId": asset["id"], "roles": roles,
                                   "sha256": asset["sha256"], "path": str(store.asset_path(asset["id"], state))})
        artifact = {"id": artifact_id, "sceneId": target, "agent": agent,
                    "createdAt": now(), "reviewStatus": "candidate",
                    "agentVisualPass": bool(visual_pass), "toolName": tool_name,
                    "handoffPromptSha256": job["promptSha256"],
                    "actualPromptStatus": "recorded" if actual is not None else "unknown",
                    "actualPromptSha256": digest(actual.encode()) if actual is not None else None,
                    "actualReferencesStatus": "recorded" if references is not None else "unknown",
                    "actualReferenceBindings": references}
        if actual is not None:
            path = store.root / "jobs" / identifier / (artifact_id + "-actual-prompt.txt")
            atomic_bytes(path, actual.encode())
            artifact["actualPromptPath"] = str(path)
        if image is not None:
            source = store.allowed_source(image)
            asset = store.prepare_asset(source.read_bytes(), source.name,
                                        {"sourcePath": str(source), "jobId": identifier,
                                         "artifactId": artifact_id}, "candidate")
            asset = store.register_asset(state, asset)
            artifact.update(type="image", assetId=asset["id"], sha256=asset["sha256"], url=asset["url"])
        else:
            if not isinstance(text, str) or not text.strip() or len(text.encode()) > 5 * 1024 * 1024:
                raise StudioError("Text artifact must contain 1 byte to 5 MiB of text")
            path = store.root / "jobs" / identifier / (artifact_id + ".txt")
            atomic_bytes(path, text.encode())
            artifact.update(type="text", text=text, sha256=digest(text.encode()), path=str(path))
        job["artifacts"].append(artifact)
        completed_scenes = {a.get("sceneId") for a in job["artifacts"] if a["type"] == "image"}
        finished = text is not None or not job["sceneIds"] or set(job["sceneIds"]) <= completed_scenes
        job.update(status="completed" if finished else "claimed", updatedAt=now())
        if finished:
            job["completedAt"] = now()
        store.event(state, "job.artifact", jobId=identifier, artifactId=artifact_id, agent=agent)
        return job
    return store.mutate(complete)


def fail_job(store, identifier, agent, reason):
    def fail(state):
        job = find(state["jobs"], identifier, "job")
        _owned(job, agent)
        job.update(status="failed", error=str(reason), updatedAt=now())
        store.event(state, "job.failed", jobId=identifier, agent=agent, reason=str(reason))
        return job
    return store.mutate(fail)


def review_job(store, identifier, request):
    decision = request.get("decision")
    if decision not in ("feedback", "approve", "reject"):
        raise StudioError("Unknown review decision")
    def review(state):
        job = find(state["jobs"], identifier, "job")
        artifact = find(job["artifacts"], request["artifactId"], "artifact") if request.get("artifactId") else None
        if decision in ("approve", "reject") and artifact is None:
            raise StudioError("Approve/reject requires artifactId")
        feedback = {"id": new_id("feedback"), "decision": decision,
                    "text": str(request.get("feedback", "")), "artifactId": request.get("artifactId"),
                    "createdAt": now(), "author": "user", "resolved": decision != "feedback",
                    "targetProjectRevision": state["revision"], "handoffProjectRevision": job["projectRevision"]}
        job["feedback"].append(feedback)
        if artifact is not None and decision != "feedback":
            artifact["reviewStatus"] = "user-approved" if decision == "approve" else "user-rejected"
            if decision == "approve" and artifact["type"] == "image":
                if artifact.get("sceneId"):
                    chapter = find(state["project"]["chapters"], job["chapterId"], "chapter")
                    scene = find(chapter["scenes"], artifact["sceneId"], "scene")
                    if scene.get("imageAssetId") != artifact["assetId"]:
                        scene.setdefault("imageHistory", []).append({"previousAssetId": scene.get("imageAssetId"),
                            "previousStatus": scene.get("status", "draft"),
                            "selectedAssetId": artifact["assetId"], "artifactId": artifact["id"], "selectedAt": now()})
                    scene.update(imageAssetId=artifact["assetId"], status="user-approved")
                elif job.get("entityId"):
                    entity = find(state["project"]["entities"], job["entityId"], "entity")
                    if artifact["assetId"] not in entity.setdefault("referenceIds", []):
                        entity["referenceIds"].append(artifact["assetId"])
                        artifact["referenceAdded"] = True
                find(state["assets"], artifact["assetId"], "asset")["reviewStatus"] = "user-approved"
            elif decision == "reject" and artifact["type"] == "image":
                if artifact.get("sceneId"):
                    chapter = find(state["project"]["chapters"], job["chapterId"], "chapter")
                    scene = find(chapter["scenes"], artifact["sceneId"], "scene")
                    if scene.get("imageAssetId") == artifact["assetId"]:
                        prior = next((h for h in reversed(scene.get("imageHistory", []))
                                      if h.get("artifactId") == artifact["id"] and not h.get("reverted")), None)
                        if not prior:
                            raise StudioError("Change the existing selected image before rejecting this duplicate asset",
                                              "selected_asset_conflict", 409)
                        scene["imageAssetId"] = prior.get("previousAssetId")
                        scene["status"] = prior.get("previousStatus", "draft")
                        prior["reverted"] = True
                        prior["revertedAt"] = now()
                elif job.get("entityId") and artifact.get("referenceAdded"):
                    entity = find(state["project"]["entities"], job["entityId"], "entity")
                    entity["referenceIds"] = [a for a in entity.get("referenceIds", []) if a != artifact["assetId"]]
                still_used = any(s.get("imageAssetId") == artifact["assetId"]
                                 for c in state["project"]["chapters"] for s in c["scenes"])
                still_used = still_used or any(artifact["assetId"] in e.get("referenceIds", [])
                                              for e in state["project"]["entities"])
                if not still_used:
                    find(state["assets"], artifact["assetId"], "asset")["reviewStatus"] = "user-rejected"
        job["updatedAt"] = now()
        store.event(state, "job.reviewed", jobId=identifier, feedbackId=feedback["id"], decision=decision)
        return job
    return store.mutate(review)


def inbox(store):
    state = store.read()
    pending = []
    for job in state["jobs"]:
        for feedback in job["feedback"]:
            if feedback.get("author") == "user" and not feedback.get("resolved", True):
                pending.append({"targetType": "job", "targetId": job["id"], **feedback})
    for board in state["storyboards"]:
        for page in board["pages"]:
            for feedback in page["feedback"]:
                if feedback.get("author") == "user" and not feedback.get("resolved", True):
                    pending.append({"targetType": "storyboard", "targetId": board["id"],
                                    "pageId": page["id"], **feedback})
    return {"jobs": [j for j in state["jobs"] if j["status"] in ("queued", "claimed")],
            "unresolvedFeedback": pending, "revision": state["revision"]}


def reply(store, identifier, agent, text, feedback_id=None):
    if not text or not text.strip():
        raise StudioError("Reply text is required")
    def respond(state):
        target = next((j for j in state["jobs"] if j["id"] == identifier), None)
        if target is not None:
            groups = [target["feedback"]]
        else:
            target = find(state["storyboards"], identifier, "job or storyboard")
            groups = [p["feedback"] for p in target["pages"]]
        matching = None
        if feedback_id:
            matching = next((f for group in groups for f in group if f["id"] == feedback_id), None)
            if not matching:
                raise StudioError("Feedback not found", "not_found", 404)
            matching.update(resolved=True, resolvedAt=now(), resolvedBy=agent)
        message = {"id": new_id("feedback"), "author": "agent", "agent": agent,
                   "decision": "reply", "text": text, "createdAt": now(),
                   "inReplyTo": feedback_id, "resolved": True}
        group = next((g for g in groups if matching in g), groups[0]) if groups else []
        group.append(message)
        store.event(state, "agent.replied", targetId=identifier, feedbackId=message["id"], agent=agent)
        return target
    return store.mutate(respond)
