# Book and chapter planning in conversation

Start with the user's actual declarative brief: book arc, chapter intent, comic ambition, causes, consequences and the desired reaction/pause/payoff. Preserve the brief verbatim in plan provenance, including a Herculean comic intention if that is what the user asked for. Treat it as editable intent, not a cheerful/tired style default. Do not generate a new story, images or video merely to initialize this workflow.

## First useful overview

Save a versioned book plan referencing actual registered chapter IDs. Show the arc, chapter intents, estimated reading rhythm and **eight to twelve representative moments** spanning the chosen chapter/sequence or book. This coarse overview is the first feedback surface; do not require eighteen comic sheets before asking for feedback. Fewer than eight existing moments are shown honestly rather than padded with invented content.

Every moment has id, actual chapterId, user intent, rhythm category, estimatedSeconds (positive editorial estimate or null if unknown), optional registered castIds and sequenceId. Categories are setup/repetition/reaction/pause/turn/payoff. Planned cast participation is a count of intended appearances, not proof of interaction. interactionIntent records an explicit user's staging intention; it is not evidence an illustration or child reader exhibited it.

shotIds may reference existing actual chapter scene IDs; shotSpan can instead bind ordered firstSceneId/lastSceneId endpoints. A coarse moment can span many existing shots without copying or rendering them all. Unknown future shots remain sequence-expansion requests, not fabricated saved scene IDs.

## Cause/effect and setup/payoff

Moment dependsOn refers to known saved moments. The combined dependency graph and resolved cause-effect/setup-payoff links must be acyclic. A resolved setup-payoff mapping binds a setup category to a payoff category and retains the user's explanation. An explicitly unresolved link may name a future endpoint and explain the missing connection; display it as unresolved and exclude it from resolved dependency proof. Never silently label a missing endpoint resolved.

## Zoom and revise

Select a representative moment to zoom into its sequence/page; the selected moment is actually included in that page. A page contains at most twelve moments; up to4096 moment intentions fit a bounded2MiB plan, while a small coarse plan can reference much longer existing chapters through shot spans. Context uses one page, at most24 related links and ten recent version summaries, not whole history.

Use the persistent bookPlanVersion/bookPlanSHA256 plus project expectedRevision for every edit. Save only the intended changed fields; conflicts fail rather than overwrite. Saved versions retain the original request/hash, exact catalog reference identities/roles and provenance. Old versions remain unchanged and historical views disable edits and rough-page request controls. Direct moment editing is a reversible planning save; it does not send a chat message or grant production approval.

The UI sits within the existing Plan surface. Chapter, sequence and history pagination live in component state/capability parameters; no new stable URL view enum is needed. Chat and composer stay normal. Sequence-expansion and compact-comic-page buttons **populate conversation only**, never send or execute. The actual conversational request can then use the existing chapter planning workflow. A rough comic request requires a registered visual artifact before visual preproduction can be called complete; schematic boxes and reused thumbnails alone are not a completed scene-specific comic sheet.

## Tempo is an editorial estimate

Derive categories and seconds from the actual saved plan version. Unknown seconds remain unknown; show partial known estimates separately, not a false complete duration. Ordered chart bins aggregate to at most120 groups for long plans. An optional intendedTargetSeconds is always labelled **user editorial heuristic**, for the whole book even while viewing a chapter; it is neither Disney/Pixar ground truth nor measured child reading. This workflow has no industry calibration or child-reading study.

Historical overview and tempo use the same frozen book plan version/hash. Changes to reading seconds, intent or category produce a new plan version. Seconds are not the older ordinal activity/comedy/discovery values. Book and chapter pacing should stay editable in conversation; no claimed ideal curve overrides the user's intention.

## References, phase boundaries and provenance

referenceIds must be actual catalog assets with full SHA256/size. Planning bindings are catalog-only, not a claim bytes were inspected. Resolve/verify exact needed references through existing character/location/storage workflows before a real visual operation. Preserve their projection, identity/style/geometry roles; do not turn layout donors into character identity or geometry-underlay into panorama methods.

This book plan records planned intent and zero generationCalls/productionStarted. It does not approve imagery, authorize full production, create jobs, publish, call a model or control a video/API budget. Optional shot expansion and comic requests remain rough-preproduction. Full production uses the existing managed chapter's **separate actual explicit go**, bound to reviewed current chapter version/spec/effective references; book arc, planning edits or rough art do not substitute for that go. This module does not rewrite chapter authorization state or claim cross-chapter production automation exists.

## Timing contracts and targets

businessPreparationSeconds is measured only from business function entry through validation/snapshot preparation, before Store commit. requestAcceptanceToCompletionSeconds remains null without server measurement. Test-suite runtimes are fixture runtimes, not conversational or browser latency.

Proposed targets (not measured): warm215-moment state validate/save/view <=1s; conversational coarse overview <=30s p95; one-moment revision <=15s p95. Measure actual request acceptance, first visible feedback, durable-save receipt and browser paint separately; report cache state/model/tool counts. No live improvement or fixture-only “finished” claim.

## Integration contract

The module exports save_plan, patch_plan, planning_view and planning_request. A trusted capability registry supplies Store/current or pinned snapshot and guards mutation context. planning_view provides overview and tempo from the same version plus projectRevision/readOnly. save/patch receive optimistic guards; planning_request returns request metadata only, not a job.

The host wires renderBookPlan/bindBookPlan under existing Plan. Inject onView, savePatch, compose, onSaved/onError callbacks through supported registry/bridge; modules do not fetch directly, use storage, access parent DOM, or manage serving/kernel authority. See HANDOFF.md and capabilities.json for exact function parameters. No existing routes/context/chapter core are changed by this export. Live integration, hot reload, persistence through the running host and actual browser rendering remain separate acceptance.

## Persistent storage and ordinary revision bounds

Each standalone saved spec is bounded2MiB; all canonical studioBookPlan versions/metadata together are bounded8MiB, with at most100 versions. Unchanged effective spec/reference identity is rejected409 rather than duplicating text/history; budget exhaustion is rejected413 before Store save. Existing immutable version identities are retained. No automatic deletion/archive or whole-history rewrite occurs. Separate Store project-history storage is not globally bounded by this planning contribution cap. The named book.save.v1 bridge has a narrower1MiB request limit with up to48 bounded JSON chunks; ordinary book.patch.v1 uses changed fields only.

Ordinary context omits studioBookPlan/history from raw book metadata. Bounded current planningContext supplies exact current version/hash/project revision, selected chapter intent, up to8 selected moments and8 overview moments, up to12 local links and8 reference bindings. Use book.get.v1 for bounded authoritative page/version retrieval, then one book.patch.v1 call; do not re-explore the whole thread or rewrite helper scripts for a simple change. Model/provider acceptance-to-completion timing is distinct from business preparation.

## Portable checks

From repository root, using Python with existing Studio requirements:
python3 -B tools/studio/tests/test_book_planning.py
python3 -B tools/studio/tests/test_book_planning_context.py
node tools/studio/web/tests/book-planning.test.mjs

These fixtures perform no model/image/video/provider calls or production authorization. Small projection test serializes one bounded version and estimates repeated history arithmetically, never serializes a1.7GiB fixture. Browser/user acceptance requires actual visual artifact availability; unit fixture checks alone do not prove live integration.
