"""Versioned Studio business API loaded as one immutable package per revision."""
from .routes import route
from .context import selected_context
from .jobs import claim_job, complete_job, fail_job, reply, inbox
from .conversation_plan import plan_hash
from .insights import elapsed

API_VERSION = 1


def self_test():
    """Pure candidate contract checks: no live Store, network or filesystem writes."""
    assert callable(route) and callable(selected_context)
    assert elapsed("2026-01-01T00:00:00Z", "2026-01-01T00:00:03Z") == 3
    project = {"entities": [], "book": {}}
    chapter = {"id": "test", "script": "", "scenes": []}
    assert len(plan_hash(project, chapter)) == 64
    assert route(None, "GET", "/not-a-business-route", {}, None) is None
    return True
