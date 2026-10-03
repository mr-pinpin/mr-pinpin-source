"""Read-only project revision views with explicitly live asset/job collections."""
from model import StudioError


def state_at_revision(store, revision=None):
    state = store.read()
    if revision is None:
        return state
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise StudioError("project revision must be a nonnegative integer")
    if revision > state["revision"]:
        raise StudioError("Requested project revision does not exist", "not_found", 404)
    revisions = [event["revision"] for event in state["events"]
                 if event["type"] == "project.snapshot" and event["revision"] <= revision]
    if not revisions:
        raise StudioError("Requested project snapshot does not exist", "not_found", 404)
    snapshot_revision = max(revisions)
    snapshot = store.project_revision(snapshot_revision)
    live_revision = state["revision"]
    state.update(project=snapshot["project"], revision=snapshot_revision, readOnly=True,
                 review={"requestedRevision": revision, "snapshotRevision": snapshot_revision,
                         "liveRevision": live_revision,
                         "liveCollections": ["assets", "jobs", "storyboards", "events"]})
    return state
