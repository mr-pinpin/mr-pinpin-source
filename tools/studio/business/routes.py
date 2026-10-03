"""Product JSON routes; HTTP framing, uploads and binary delivery stay in kernel."""
from model import StudioError, find, valid_id
from review_state import state_at_revision
from .conversation_plan import plan_status, approve_plan
from .jobs import create_job, review_job, inbox
from .boards import create_storyboard, review_storyboard
from .insights import insights
from .media_library import media_library, import_media


def route(store, method, path, query, body):
    if method == "GET":
        if path == "/api/plan":
            chapter_id = query.get("chapterId", [None])[0]
            revision = query.get("revision", [None])[0]
            if revision is not None and not revision.isdigit():
                raise StudioError("revision must be a nonnegative integer")
            state = state_at_revision(store, int(revision) if revision is not None else None)
            project = state["project"]
            chapter = find(project["chapters"], valid_id(chapter_id), "chapter")
            result = plan_status(project, chapter)
            if state.get("readOnly"):
                result.update(readOnly=True, review=state["review"])
            return 200, result
        if path == "/api/jobs":
            state = store.read()
            return 200, {"jobs": state["jobs"], "revision": state["revision"]}
        if path == "/api/inbox":
            return 200, inbox(store)
        if path == "/api/insights":
            return 200, insights(store)
        if path == "/api/media":
            return 200, media_library(store)
    elif method == "POST":
        if path == "/api/plan/approve":
            return 200, approve_plan(store, body)
        if path == "/api/media/import":
            asset, state = import_media(store, valid_id(body.get("id"), "media id"))
            return 201, {"asset": asset, "revision": state["revision"]}
        if path == "/api/jobs":
            job, state = create_job(store, body)
            return 201, {"job": job, "revision": state["revision"]}
        if path == "/api/storyboards":
            board, state = create_storyboard(store, body)
            return 201, {"storyboard": board, "revision": state["revision"]}
        parts = path.strip("/").split("/")
        if len(parts) == 4 and parts[0] == "api" and parts[3] == "review":
            identifier = valid_id(parts[2])
            if parts[1] == "jobs":
                result, state = review_job(store, identifier, body)
                return 200, {"job": result, "revision": state["revision"]}
            if parts[1] == "storyboards":
                result, state = review_storyboard(store, identifier, body)
                return 200, {"storyboard": result, "revision": state["revision"]}
    return None
