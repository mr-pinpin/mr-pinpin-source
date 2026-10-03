# Studio workflows

Reusable working methods for carrying a creative request through to a visible result.

- [Character creation](character-creation.md): first prototype, inline review, coordinated views, a composite reference sheet and a required separate cast-interaction page.
- [Mr. PomPom example](examples/mr-pompom.md): an actual Studio run, its registered outputs, reference lineage and review attribution.

- [Character timing observations](examples/character-latency-20261003.md): measured PomPom, Mama and Papa runs with scope and comparison limits.

These are operating guides, not extra approval gates. The original request authorizes ordinary reversible draft work. Ask only about a decision that genuinely blocks progress; honor review checkpoints the user explicitly requested. A recorded plan review, design confirmation, artifact selection and publication authorization are different decisions.

The [Studio documentation](../tools/studio/README.md) describes the implementation. Normal UI and business workflow policy are editable; the transport, persistence and authority kernel remains separate. The current creative policy is [creative_policy.py](../tools/studio/business/creative_policy.py).

Generated media stays in external Studio storage. Example manifests contain registered asset IDs, full SHA-256 identities, relative data paths and provenance, not image binaries. Local asset endpoints work only in the matching Studio installation. They are not public download links; another installation must restore the corresponding bytes and registry before using them.

Code and creative content retain their respective terms in [LICENSE](../LICENSE), [CONTENT-LICENSE.md](../CONTENT-LICENSE.md) and [THIRD-PARTY-NOTICES.md](../THIRD-PARTY-NOTICES.md). A workflow example does not grant new rights or turn a candidate into approved artwork.

## Durable cast production

- [Cast run contract](cast-run.md): resume the first missing verified stage without another authorization request.
- [Character folders](characters/): canonical names/aliases, age and life-stage evidence, source bibliography, design/contact constraints and package decisions. Each folder has a README.md and evidence.json.
- [Cast manifest](cast-run.json): durable queue and required solo/interactions stages.

The application loads its canonical Markdown and manifest from persistent external Studio data on fresh turns. Source copies are mechanical checkpoints. Registered images and exact prompts/native hashes/stage receipts stay in that data root under reports/character-packages/<entity>.json, and survive closing a session. A status flag alone cannot complete a package: distinct stage receipts must match registered assets and actual image bytes. Solo-only packages resume interactions without duplicating successful solo art. Read selected IDs/hashes programmatically from receipts; never retype opaque identities from memory. Historical review does not import mutable live cast state.

Produced drafts, delegated working-reference acceptance, personal review, artifact selection and publication remain distinct. Notetaker is unavailable; durable Markdown notes are the labeled fallback. Source checkpoints contain metadata and documentation, never generated image binaries or invented approval.

## Complete-cast draft inventory

The final checkpoint exports a [readable final-stage inventory](/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-conversation-data/reports/cast-complete-inventory.md) and [full receipt/source inventory](/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-conversation-data/reports/cast-complete-inventory.json). Registered native artwork stays outside Git. Source/proposal distinctions, age evidence and unknown historical measurements remain explicit. These inventories document drafts and agent QA, not personal Miguel approval, reference selection or publication.

Native image inputs are capped at five using saved toolchain policy: current verified solo/identity first, needed counterpart identities, then layout/style/context. Omitted bibliography remains recorded. Fresh context supplies the policy and persistent stage/reference bindings; it never relies on prior chat memory. Notetaker remains unavailable; Markdown is the truthful fallback.

## Compact selected-task context

[Character context index](character-context-index.md) directs retrieval of the full guide, selected dossier/evidence and canonical stage receipts. Queue and guide indexes replace long repeated prose; unrelated character bindings are omitted from the turn while preserved in revision-local book data and character folders. Exact prompts remain registered metadata, retrievable by asset ID. Fresh-process selected/resume and historical-isolation tests and UTF-8 byte measurements are recorded in reports/cast-context-compact-proof.json. This is a business-layer text reduction, not a native-thread reset or compaction fix.

## Verified character-job storage — 2026-10-03

[Industrial storage and preparation](industrial-storage.md) documents ID resolution, bounded cache/disk preflight and actual job outcomes. Persist storage-policy.json, toolchain.json, character folders and reports/character-jobs plus reports/storage with the data layout. Fresh context hydrates the commands; no credentials or image binaries enter source exports. Standalone data-relative tests belong in the dated workflow example with their data layout, not unittest discovery. Remote quota is unknown.

## Current shared storage and measured timing

The standalone `packages/replica_store` library and filesystem outbox are implemented. The native agent remains network-restricted; filesystem handoff to the host worker works. Badger, Otter and Beaver final pairs have matching verified remote receipts. New production uses `cast_ops.py closeout <entity>`; already produced characters use `cast_ops.py archive-existing <entity>` without historical metrics rewrites. See [replica-storage.md](replica-storage.md).

Actual deployment runs through authorized Mini tmux with a TB4 mount/UUID guard and bounded caches/logs. Direct launchd external-volume access blocks reboot autostart; automatic reboot recovery is not established. No Studio daemon/kernel change is implied.

Frozen ordinary character benchmarks remain Badger 658.651596s total / 87.371827s image / 571.279769s outside image; Otter 312.267804s total / 93.365586s image / 218.902218s outside image. These predate the combined shared-storage workflow; no new combined creation-plus-storage or full-chapter benchmark has been measured. Keep preparation, generation, visual QA, registration, metadata closeout and asynchronous transfer time distinct.
