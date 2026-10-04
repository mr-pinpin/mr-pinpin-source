# Business JSON v1 — implemented export, isolated canary handoff

No live artifact changed or process restarted. Source exports extend the stable c9be233f9e18f6d480c8a5b7d50dff6384c9df2766510b5ef006b21ccec40c75 closure. Coordinator owns mechanical copying, immutable build, canary and cutover. Source export receipt lists every byte/hash/base; copied cache originals remain immutable. Paid cost $0.

## Implemented closure

- `server.py`: same existing loopback/origin guard, GET `/api/business/capabilities` trusted metadata; only canonical POST `/api/business/<registered operation>` extension paths. Parent supplies exact business hash, view revision and explicit read-only flag in headers. Unknown/stale operation fails before body read. Content-Length must fit its pinned descriptor cap before buffering (maximum 1 MiB). Body read deadline 10 seconds. Existing conversation, fixed APIs and registered image serving unchanged.
- `business_contract.py`: pure bounded descriptor/schema validation, strict types/unknown-field refusal and incremental capped UTF-8 JSON response encoding. No filesystem, transport or secret selector fields. Metadata 64 KiB/64 operations; request up to declared 1 MiB; response up to declared 1 MiB; nested schema depth 8/256 nodes; operation timeout <=10 seconds. Descriptors cannot alter stable control namespaces.
- `BusinessRuntime`: optional exports `business_capabilities()` and `business_dispatch(store, operation, body, context)`, preserving packages without these exports. Validates descriptors before activation. Leases descriptor and immutable handler atomically by supplied business hash; an intervening activation refuses stale requests rather than calling a different revision. Historical/read-only and mismatched current revision mutations are refused server-side. Handler output byte cap enforced before HTTP response serialization.
- `shell-frame-host.js`: retains nonce, source, null-origin and active-frame checks. Parent obtains descriptors from trusted same-origin server; none are accepted from child. Validates new operation, injects parent-selected view/hash headers, uses streamed bounded fetch/abort, and validates the finite JSON response. Reads do not trigger unnecessary state reload; mutations do. Fetches current metadata per extension request, so a registry is never silently reused after activation.
- `shell-bridge.js` plus `business-extension-contract.js`: previous four-argument fixed routes remain compatible. New registry identity is private, descriptors deeply frozen, canonical names registered, unknown schema fields rejected. Mutation approvals require exact booleans. No generic URL/path/transport forwarding; redirect:error. Existing frame conversation controls never become business operations.

## Timeout semantics — explicit limitation

Host fetch aborts at the declared deadline without retry. Runtime returns HTTP 504 at the deadline without waiting indefinitely. Python trusted in-process code cannot safely be killed: a timed-out handler can finish later. Its lease remains live until completion, and subsequent extension mutations and legacy business-route POST/PUT calls are refused while a capability mutation remains pending. No automatic replay. At most 16 concurrent leased extension calls are admitted; stuck trusted handlers retain their leases and eventually cause refusal rather than unbounded thread creation. The response says outcome may be uncertain; hydrate/review before another attempt. Cooperative handlers receive `deadlineMonotonic` and must check it before work/mutation. This does not claim hard cancellation or a Python security sandbox. Direct stable Store/conversation APIs retain existing behavior.

## Reloadable example integration

NEW `business/capability_adapters.py` registers actual `draft.get.v1`, `draft.patch.v1`, `draft.authorize.v1`, `draft.pdf.chunk.v1`. It delegates to app-owned chapter_drafts functions and the new read-only PDF helper, never changes chapter_drafts/jobs. Draft get honors historical project snapshot and returns new named patch/authorize route hints. Patch uses existing hydrated current version/hash and expectedRevision. Authorization still requires specific explicit full-production instruction/version/spec/reference binding and only records an authorization receipt; tests never generate. No schema/template automatically authorizes production or publication.

App-owner applies separate `business-registration.diff` to business/__init__.py. No legacy business routes need changes: server dispatch intercepts the dedicated namespace before them. The coordinator/app owner must review adapter bindings against the latest w3 core before activation; the manifest records the supplied core snapshot hash used for isolated checks.

PDF helper requires Store.root/deliveries/catalog.json with `deliveries` list. Each entry pins chapterId, version, sourceVersionSHA256, language, artifactSHA256, bytes, storagePath **relative to deliveries/**, e.g. `chapter-v2-en.pdf`. No user-requested filepath is accepted. PDF remains beneath that root, full SHA/size/PDF magic verified, 64 KiB chunks, <=96 KiB descriptor response, <=64 MiB full artifact. App owner registers an actual immutable export receipt; it must never forge a missing artifact. UI delivery module already supplied in separate delivery export uses `/api/business/draft.pdf.chunk.v1` and receives only legitimate JSON RPC. No image MIME forgery or media/import disguise.

## Reproduce isolated tests

From this local export closure:

```
node web/tests/test-extensions.mjs
node web/tests/test-transport.mjs
node web/tests/test-host-gates.mjs
PYTHONPATH=/Users/miguel_lemos/tmp/studio-canary-cache-20261004/dependencies \
STUDIO_QA_STABLE=/Users/miguel_lemos/tmp/studio-canary-cache-20261004/stable/c9be233f9e18f6d480c8a5b7d50dff6384c9df2766510b5ef006b21ccec40c75 \
STUDIO_QA_BUSINESS=/Users/miguel_lemos/tmp/studio-canary-cache-20261004/source/business \
/opt/homebrew/bin/python3 -B test_business_extensions.py
```

After mapping to source, Node tests reside web/tests and Python test tools/studio/tests; use source dependency environment and omit snapshot overrides. Tests use fresh home/tmp fixtures only. Real HTTP tests exercise original chapter_drafts get/patch/explicit authorization, registered fixture PDF SHA chunks, stale hashes, snapshot reads, server historical mutation refusal, immutable package activation, leased old handler across activation, bounded request before reading body, >64 KiB declared request, response refusal and timed-out mutation no replay. Node bridge is additionally connected to that real Python HTTP handler for get/patch. Host gate tests evaluate the actual exported receive function with isolated stubs; full DOM/browser acceptance is coordinator/w5 canary ownership.

## Remaining canary acceptance / rollback

Build a NEW immutable artifact from the exported stable closure; do not edit existing hash directories. Wire reviewed app registration and the separate delivery UI module in isolated canary. Verify actual opaque-sandbox UI reads/patches/authorization refusal in review, old fixed routes/conversation nonce controls, hotreload metadata, streamed size/timeout behavior and stale hashes. Register an actual saved arbitrary chapter-version PDF and download in the real browser; check saved bytes/SHA/page count/selectable RU/EN text/images and missing-art list. Earlier synthetic PDF render proof is valid fixture evidence; prior native download.saveAs stalled, so actual saved draft download is not yet claimed.

No live generation, production approval or publication performed in this lane. Root explicit reviewed cutover retains prior immutable artifact pointer for rollback; business data is not rewritten during rollback.
