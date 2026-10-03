# Stable Studio kernel and reloadable product code

The HTTP service, conversation transport, persistence, recovery, iframe host and
code loaders run from an immutable kernel release. Normal chat and workspace
presentation run in one editable opaque iframe. Product routes and context
assembly run as independently versioned Python packages inside the same server
process. Ordinary product changes need no second server, restart or kernel release.

## Freeze and launch

Run the existing release command on the Mini:
    python tools/studio/release.py --runtime-dir /RUNTIME freeze

Launch the returned immutable server path with external roots:
    PYTHONDONTWRITEBYTECODE=1 python /RUNTIME/stable-releases/HASH/server.py \
      --data-dir /DATA \
      --business-source /SOURCE/tools/studio/business \
      --workspace-source /SOURCE/tools/studio/web/workspace-dev \
      --runtime-dir /RUNTIME \
      --media-root /MEDIA \
      --port 18826

Use a persistent tmux session. Do not restart an existing service merely to edit
normal UI or product Python. Kernel/transport/store/schema changes require a
deliberate release and cutover. Verify a release using:
    python tools/studio/release.py --runtime-dir /RUNTIME verify HASH

Freeze excludes business/**, workspace-dev/**, web/workspace-dev/**, tests/** and
web/tests/** before traversal, plus hidden/cache artifacts. Editing normal UI,
business code or tests leaves the kernel hash unchanged. Thin compatibility
shims and existing legacy static editor assets remain in the kernel; /legacy.html
remains usable. The shims contain no product implementation. Frozen server/CLI
operation requires external business configuration. Files are content-addressed,
mode 0444 with directories 0555; existing releases are verified, never overwritten.
Running mutable server.py reports stableRelease:"development".

## Python business builds

BusinessRuntime(source, directory, watch=True) uses the existing process and
stores immutable packages in directory/business-builds/<sha256>. Its watcher
debounces source changes, compiles Python, verifies required exports, imports
under a unique package namespace, and runs pure self_test() before activation.
Relative imports remain bound to that version. Imports and tests must not mutate
live data, spawn background work or access the network. An unchanged captured
source is activated atomically after validation.

Required exports: API_VERSION = 1, selected_context(store, body),
route(store, method, path, query, body), self_test().
A route returns None when unhandled, or (status, JSON-serializable payload).
Optional local CLI operations: claim_job, complete_job, fail_job, reply, inbox.

invoke(name, *args, validate=None) captures an immutable module lease; a supplied
output validator executes before release. Requests in flight retain their
version while later requests see the new active handle. Old namespaces are
removed only after neither active/previous handles nor requests need them.
Immutable disk versions remain retained.

GET /api/runtime includes business: {active, previous, status, error}.
business-state.json exposes the same bounded status for agents whose sandbox
disallows network access. The runtime directory is readable, never added to
writable agent roots. Status is idle/building/ready/error; error contains a
code, diagnostic and failed hash.

Syntax/import/export/self-test failure preserves the active handle. Unexpected
call errors, invalid route payloads or context-validator failures roll back only
if the failing handle is still active. Expected StudioError validation responses
do not roll back. Accidental SystemExit during import/call becomes a failure.
Failed requests are NEVER replayed: a mutation may already have persisted, so
the caller receives an error and must inspect state. The failed hash is not
automatically reactivated; edit source to produce a new candidate.
Restart restores verified persisted active/previous packages even when current
source is broken.

The CLI opens BusinessRuntime(None, directory, watch=False, read_only=True)
against the server's activated manifest. It does not build, watch or write
runtime status. Run immutable imports with PYTHONDONTWRITEBYTECODE=1; the CLI
sets the equivalent Python flag. Frozen startup requires --business-source.

This is trusted in-process Python, NOT a security sandbox. Imports and self-tests
execute trusted code. Code that blocks forever, starts threads, invokes native
crashes or intentionally bypasses the contract can affect the process. This
loader does not claim malicious-code isolation or transactional mutation undo.

## UI builds and transport

The workspace watcher scans every 500 ms, debounces 400 ms, checks JavaScript
syntax using Node and validates JSON. It never runs npm or package scripts.
A source capture is validated and rechecked before atomic hash publication.
Invalid candidates retain the working URL. Previous builds remain available.

GET /api/runtime also returns stableRelease, workspace
{latest, previous, status, error, url} and pollIntervalMs.
GET /api/runtime/releases/list lists retained UI versions.

The parent prepares a candidate iframe and swaps only after ready. Syntax-valid
runtime failures retain the last good frame or expose minimal recovery chat.
Only app-owned global errors are fatal; unrelated extension rejections are ignored.
Recovery conversation remains manually accessible.

The iframe sandbox is allow-scripts allow-downloads allow-popups, without
allow-same-origin or allow-forms. Parent RPC validates source window, opaque
origin and per-frame nonce. Normal conversation/composer layout and keyboard
policy live in editable UI; transport, persistence and authority stay in kernel.
Read [FRAME-PROTOCOL.md](web/FRAME-PROTOCOL.md) for typed RPC details.
Private APIs/assets have no wildcard CORS; only immutable UI static files do.
Child images/video/WebGL use parent-authorized binary blobs.

## Agent scope and saved reviews

The agent may edit exactly the configured data/UI/business writable roots.
Immutable kernel and runtime artifacts stay outside those roots. User-requested
UI/product-code work needs no creative production-plan approval. Publishing and
creative approval gates remain unchanged.

Current policy is reapplied on each resumed turn using thread/inject_items
before turn/start, superseding obsolete same-thread bans. Policy version 4
removes the blanket business-backend prohibition while preserving kernel
authority. Permission follows actual source boundaries. Injection failure
starts no turn; saved thread/transcript/context are preserved.

GET /api/state?revision=N returns the closest saved project snapshot at or before
N with readOnly/review metadata. Assets/jobs/storyboards/events remain live
registries. Pinned conversation context uses that same projectRevision and a
read-only sandbox. Parent bridge blocks mutations and image uploads while pinned.
Kernel independently validates context envelopes and derives review authority.
Return to Live before editing.

Copy link pins UI hash, saved project revision and selected view/context/media
state. Drafts stay in parent session persistence, never in URLs. A UI hash and
project revision do not claim to reproduce a historical server/job ledger.

## Restore, compatibility and verification

Back up source, complete kernel/UI/business bundles and manifests,
business-state.json, and project data including history/conversation/assets.
Credentials and Codex login remain machine-local. Verify frozen releases before
restoring; never overwrite immutable directories. Restore compatible source roots
and launch the pinned kernel with external data/runtime paths.

Breaking kernel/bridge/API changes require a matched UI/business/kernel cutover
with backups and rollback. Keep compatible source channels during that migration.
Ordinary UI/business edits keep using the one running process. Schema migrations
remain explicit kernel operations with versioned backups and compatibility checks.

Run:
    python -m unittest discover -s tools/studio/tests -v

Focused loader tests cover immutable hashes, relative imports, concurrent leases,
namespace cleanup, debounce, syntax/import/self-test/contract failures, rollback,
expected validation, invalid output, no mutation replay, SystemExit recovery,
bad-source restart, read-only CLI access and independent kernel identity.
Actual model probes must use isolated data/source roots and preserve live work.
