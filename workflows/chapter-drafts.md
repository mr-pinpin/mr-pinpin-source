# Declarative chapter drafts and fast revisions

Describe intent, review actions/cause/effect/camera and reading rhythm, then revise selected panels. Planning and requested rough visual preproduction remain proactive. Full production requires a separate specific user instruction for the reviewed current version. Draft saves never generate art, approve artifacts or publish.

## Persistent commands and bounded context

Use `python -B tools/chapter_draft_ops.py context <chapterId> --page 0` for current version/hash and a compact page. Ordinary revisions use `python -B tools/chapter_draft_ops.py patch <chapterId> --panel <panelId> --fields '<JSON>' --request '<original request>'`. The helper reads current Store state and performs one business mutation; no copied full spec or bespoke Python script is needed. Pass --version, --sha256 and --expected-revision from selected conversational context when preserving the exact reviewed base. A concurrent revision must fail rather than overwrite.

The helper accepts --data-dir and --runtime-dir, or PINPIN_STUDIO_DATA/PINPIN_STUDIO_RUNTIME. Defaults match the standard installed data/tools layout. Other deployments should pass explicit roots. It imports the configured active verified business bundle, with no cast_ops dependency.

`save <spec.json>` remains creation/import: chapterId, expectedRevision, baseVersion, request, reason, spec {title, synopsis, referenceIds, location {baseEntityId, proposed:boolean, description}, panels}. Synopsis defaults empty. Panels require id, action, cause, effect, caption, camera, beat (setup/repeat/turn/payoff), integer seconds (1–120), registered character castIds, earlier dependsOn IDs and honest previewKind. The location base must be a registered location entity. Missing/malformed required fields and role confusion raise StudioError.

Support 1–512 panels, including 215-panel chapters; bounds are 1 MiB per spec, 32 references and 100 versions. UI pages contain twelve panels. Context includes selected panels or one page and ten recent version summaries, not full history. Reading seconds remain semantic timing, distinct from ordinal scene tempo. Patches are at most 32 KiB and twelve selected panels. Exact before/after changedFields persist with each version; older versions remain unchanged. Pinned review reads historical state and disables mutation controls.

## Honest visual previews and reference bindings

Schematic placeholders cannot claim imageAssetId or approval/status. Reused-reference previews require registered images and are labeled reuse, not newly illustrated scenes. Generated previews require actual registered images with prompt provenance. The UI displays those images through the existing bounded media bridge. A registered compact comic sheet can be used as a preview image; this iteration does not implement per-panel cropping or invent sheet assets.

New versions snapshot reference IDs, full SHA256, catalog byte counts and roles. Semantic SHA binds spec plus reference identity/roles; the original request is retained and separately hashed. Local bytes may be explicitly unresolved during planning. Generation dispatch must verify exact registered local bytes; restore through the usual storage workflow beforehand. Never silently omit or substitute an archived reference. Legacy pilot versions remain unchanged and have no fabricated bindings; their next ordinary revision creates a current reference snapshot.

Reuse family studies, location panoramas and tractor orbit/24-view exploration in their actual roles. Inspect relevant pixels before real generation. The location owner supplies tools/studio-locations query/hydrate and workflows/locations/catalog.json. Preserve its projection/role/hash/byte metadata and unresolved status; chosen media must be normally registered before a draft references it. The porch-side nook remains a proposed layout variant, not generated location artwork.

## Production dispatch boundary

GET /api/chapter-drafts hydrates a compact page, optionally at an historical revision. POST /api/chapter-drafts/patch persists a selected-field revision. POST /api/chapter-drafts/authorize-production records an actual specific user instruction with expectedRevision, version, sha256, referenceHash, explicitFullProductionGo:true and userInstruction. Do not call it from ordinary draft authorization or fabricate review. Legacy versions without referenceHash hydrate current catalog reference bindings for review/authorization without rewriting frozen versions; inspect those bindings and record the actual specific go. If registered identities/roles have changed on a version that already binds references, create and review a new revision.

For managed chapters, /api/jobs defaults to full-production and checks current stored authorization against version/spec/reference hash before handoff creation. Revision clears the authorization. Stale request fields or approved:true do not grant permission. Selected managed scenes must match the saved plan, and generation references must have verified local bytes within the byte budget. Jobs persist draftBinding and productionScope. Requested productionScope:rough-preproduction remains allowed without full-production approval, with byte preflight. Story-plan jobs remain planning; ordinary character exploration without a managed chapter remains unchanged.

## Replies, receipts and actual measurements

Use app-relative links, such as [Open draft](/?chapter=pilot-returning-leaf&view=plan). The renderer resolves them against the authenticated parent origin, including Air18825. Do not expose local paths or hard-code the Mini port in user-facing deliverables. Version/page controls retain review context; replies preserve line breaks and simple emphasis.

Exact request/result receipts remain reports/chapter-drafts/<chapter>/vN.json. Business preparation seconds and CLI preparation-to-save seconds are partial timers. Request-acceptance-to-completion remains unknown unless actual server evidence exists. The server measured 94.29 seconds for v3, but that request lacked --chapter selection: retain it as an unselected-chapter baseline, not a matched UI benchmark. The earlier 13.85 seconds measured preparation-to-save only. No new runtime improvement, warm selected-chapter latency or combined generation/storage benchmark is claimed.

Portable isolated tests use --studio-dir <source/tools/studio>, --kernel-dir <stable release> and --scratch-dir <writable fixtures>. They do not depend on private pilot state, cast_ops, network or artwork tools. Preserve the recorded ten passing tests. Fresh warm revision and real browser/tunnel acceptance are separate next checks.

The sprint allowance is US$25 cumulative additional video/API spending, not per task. Additional paid spending remains zero. No new art, full production, publication, server restart, kernel change or permission/TCC change is part of this recovery.


## Explicit full-production go for managed chapter drafts

Script edits and rough visual storyboard studies remain ordinary preproduction. They never imply full-production permission. The managed Plan view has a separate “Authorize full production for this version” control; the older ordinary plan approval does not grant this permission. Authorization saves a receipt and does not create or execute jobs.

For an explicit conversational request to begin full production, hydrate the selected current chapter with the persistent context command. Record the user's exact instruction, then invoke the authorize command with the reviewed version, spec SHA256 and reference hash. If the request is ambiguous or refers to an older view, clarify the specific production scope/version; never infer go from “show me”, a text edit, or rough-sheet generation. Do not invoke authorization while merely implementing or testing the workflow.

    python -B tools/chapter_draft_ops.py context <chapterId>
    python -B tools/chapter_draft_ops.py authorize <chapterId> --version <N> --sha256 <specSHA256> --reference-hash <referenceHash> --expected-revision <revision> --instruction '<exact explicit full-production request>'

The UI hydrates these same bindings and records the user's deliberate authorization click. Pinned historical views and noncurrent versions cannot authorize. Legacy drafts hydrate a current catalog reference binding without rewriting their frozen versions. Known archived bytes may be unresolved at review; every actual input must be restored and verified before generation. Reference identity/role changes require a new reviewed draft.

Receipts persist in studioDraft.authorizationReceipts; the active receipt is productionAuthorization. A draft revision preserves receipt history but removes the active authorization. Dispatch checks the current spec/version/reference binding and local bytes again; stale receipts fail. No authorization in a test fixture is a live user approval.

Timing fields name their measured interval. Null requestAcceptanceToCompletionSeconds means no server end-to-end measurement is available. The recorded 94.29-second unselected request is not a matched selected-chapter UI benchmark. No new latency improvement is claimed.


## Deployment acceptance is separate

The instructions above describe the reviewed source contract. New UI routes remain unavailable until the approved extensible bridge integration is verified. Backend TB4 access is currently OS-denied in the reported live process; filesystem canary and serving checks belong to infrastructure owners. Source/fixture tests are not live readiness. Do not grant real authorization or start production while testing recovery; use isolated fixtures.
