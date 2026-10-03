# Current character/task context

Use the selected character's dossier, indexed evidence, reconciled stages and role-labelled native references. The compact queue identifies the next missing stage; other character folders remain addressable under workflows/characters/<id>/README.md and evidence.json. Full final IDs, prompts, lineage and timings are in reports/character-packages/<id>.json and the generation report linked by the dossier. A produced label alone cannot complete a package.

Read workflows/character-creation.md for the full current workflow and workflows/cast-run.md for the current checkpoint. Their hashes and section indexes are hydrated; the full prose is kept on disk. Preserve existing art, source/proposal distinctions and unknown ages. Solo and separate interaction pages are required. Inspect every subject in every direction cell, not only the larger representative in a group.

Before generation cap native inputs at five using workflows/toolchain.json and tools.cast_ops.rank_reference_pack: current target solo/identity first, necessary counterparts, then layout/style/context. Omitted bibliography remains recorded. Interactions use the verified target solo as primary identity with named species/roles per panel. Use saved tools/cast_ops.py finish/checkpoint; do not retype asset IDs/hashes.

Agent QA, delegated review, personal approval and publication remain separate. Notetaker is unavailable; durable Markdown is the truthful fallback. This context reduction does not reset native conversation history or fix native-thread compaction.

Before every new character generation, use [industrial-storage.md](industrial-storage.md) and the hydrated storageWorkflow commands. Address images by registered ID. `cast_ops.py prepare <spec.json>` verifies source bytes, roles, five-input cap, dossier/evidence, exact prompt, output requirements and disk reservations BEFORE dispatch; generate from its prepared spec and use register_cast_spec.py to retain the real outcome. Backup is explicitly unverified until fresh remote download/hash proof exists. Resume prepared attempts from reports/character-jobs; record failures/cancellations and actual retry lineage instead of asking for procedural supervision.

For a new proposed subject, `python -B tools/cast_ops.py prepare-character <spec.json>` initializes source/age dossier and queue, derives capped verified references, saves the exact prompt and returns a prepared spec. Fields: entityId, name, request, identity, scale, geometry, lifeStage, proposed:true, stage, prompt; optional counterpartIds. Reuse entityId + stage + exact prompt for interactions; verified solo is first. Inspect native inputs/pages; register using hydrated castOperations.register. Closeout via cast_ops.py closeout validates new final pages and enqueues shared owned bytes; host-worker receipts establish remote backups; pending remote work preserves local drafts. See character-preparation.md.

Existing-character archive tasks use `cast_ops.py archive-existing <entity>` directly, avoiding historical finish/timing conversions. Shared library/outbox details and deployment limits are in [replica-storage.md](replica-storage.md).

## Current shared storage and measured timing

The standalone `packages/replica_store` library and filesystem outbox are implemented. The native agent remains network-restricted; filesystem handoff to the host worker works. Badger, Otter and Beaver final pairs have matching verified remote receipts. New production uses `cast_ops.py closeout <entity>`; already produced characters use `cast_ops.py archive-existing <entity>` without historical metrics rewrites. See [replica-storage.md](replica-storage.md).

Actual deployment runs through authorized Mini tmux with a TB4 mount/UUID guard and bounded caches/logs. Direct launchd external-volume access blocks reboot autostart; automatic reboot recovery is not established. No Studio daemon/kernel change is implied.

Frozen ordinary character benchmarks remain Badger 658.651596s total / 87.371827s image / 571.279769s outside image; Otter 312.267804s total / 93.365586s image / 218.902218s outside image. These predate the combined shared-storage workflow; no new combined creation-plus-storage or full-chapter benchmark has been measured. Keep preparation, generation, visual QA, registration, metadata closeout and asynchronous transfer time distinct.
