# Editable Studio business package

This is trusted product logic loaded inside the existing Studio server process.
Edit here for context/reference selection, plans, job handoffs/review, storyboards,
metrics and the media catalog. This is separate from the editable normal UI in
web/workspace-dev. Do not edit the stable HTTP/transport/Store/runtime kernel.

Modules use relative imports within this package so each immutable revision stays
consistent while requests are in flight. __init__.py exports API_VERSION=1,
route(store, method, path, query, body), selected_context(store, body), and a pure
self_test(). Query values are lists. route returns None for an unhandled path or
(status, JSON-serializable payload). Raise model.StudioError for expected validation
errors. Unexpected failures invalidate the build; failed mutations are never replayed.

The server watches this directory and activates a validated immutable package without
restarting the process. Keep edits narrow and run isolated checks; never mutate live
records from imports or self_test. Use Store's existing validation, optimistic revision
and append-only artifact operations. Changing product behavior does not authorize
weakening origin checks, filesystem allowlists or durable storage validation.

context.py owns selected context and native image attachment rules. conversation_plan.py
owns plan fingerprints/approval; jobs.py owns handoffs/review; boards.py owns contact
sheets; insights.py owns actual ledger statistics; media_library.py owns catalog and
reviewed image import. The fixed hash-pinned file registry and binary range delivery
remain kernel capabilities. No arbitrary filesystem endpoint may be added here.

Agent CLI commands from a frozen release pass both --business-source (this exact root)
and --runtime-dir (the configured immutable artifacts root). The CLI reads the active
verified bundle without writes/builds to runtime storage. Only the running server may
activate revisions. Do not create a separate daemon, restart the server, or edit runtime
snapshots.
