"""Versioned Studio business API loaded as one immutable package per revision."""
from .routes import route as _legacy_route
from .capability_registry import business_capabilities, business_dispatch
from .context import selected_context as _selected_context
from .sheet_workflow import add_sheet_workflow, cli_sheet_route
from .book_context import cli_book_route
from .creative_policy import creative_policy
from .jobs import claim_job, complete_job, fail_job, reply, inbox
from .conversation_plan import plan_hash
from .insights import elapsed
from .cast_workflow import save_progress as reconcile_cast
from .cast_inventory import record_package as finish_cast_package

API_VERSION = 1

def route(store,method,path,query,body):
    book_result=cli_book_route(store,method,path,query,body)
    if book_result is not None:
        return book_result
    if method=='POST' and path=='/api/business/draft.sheet.bind.v1':
        return 200,cli_sheet_route(store,body)
    return _legacy_route(store,method,path,query,body)

def selected_context(store,body):
    return add_sheet_workflow(_selected_context(store,body),store)


def self_test():
    """Pure candidate contract checks: no live Store, network or filesystem writes."""
    assert callable(route) and callable(selected_context)
    from .cast_workflow import self_test as cast_self_test
    assert cast_self_test()
    policy = creative_policy()
    assert isinstance(policy, str) and 0 < len(policy.strip()) <= 16000
    assert elapsed("2026-01-01T00:00:00Z", "2026-01-01T00:00:03Z") == 3
    project = {"entities": [], "book": {}}
    chapter = {"id": "test", "script": "", "scenes": []}
    assert len(plan_hash(project, chapter)) == 64
    assert route(None, "GET", "/not-a-business-route", {}, None) is None
    return True
