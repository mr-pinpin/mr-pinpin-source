# Workflows

Each workflow is a Markdown file with a clear purpose, inputs, discussion steps, review loop, deliverables, and completion criteria. Character dossiers link to the reusable procedure.

| Document | Purpose | Status |
| --- | --- | --- |
| [Character creation](character-creation.md) | Reusable character design and reference-sheet procedure | Reusable; exercised with PomPom |
| [Papa](papa.md) | Solo and interaction reference package | Produced; unreviewed candidates |
| [Mama](mama.md) | Solo and interaction reference package | Produced; unreviewed candidates |
| [Mr. PomPom](mr-pompom.md) | Accepted reference package and character dossier | Completed under codex-wap1 delegated review |

To discover a workflow, read this index or search `workflows/*.md`. Keep this index and the project README updated when adding a workflow.

Code fences may describe typed data and declarative UI. They are specifications, not automatically executable code. The first chat renderer supports JSON WorkflowCard blocks described in character-creation.md; other schemas remain proposals. Never execute arbitrary Markdown code blocks.
# Resumable cast run

The application loads [character-creation.md](character-creation.md), [cast-run.md](cast-run.md), and [cast-run.json](cast-run.json) from this persistent directory. Per-character records and bibliographies live under `characters/<id>/`. Production insights displays the current next item and workflow notes. Use “continue the cast” to resume the first unfinished package; existing completed family outputs are retained.

## Current shared storage and measured timing

The standalone `packages/replica_store` library and filesystem outbox are implemented. The native agent remains network-restricted; filesystem handoff to the host worker works. Badger, Otter and Beaver final pairs have matching verified remote receipts. New production uses `cast_ops.py closeout <entity>`; already produced characters use `cast_ops.py archive-existing <entity>` without historical metrics rewrites. See [replica-storage.md](replica-storage.md).

Actual deployment runs through authorized Mini tmux with a TB4 mount/UUID guard and bounded caches/logs. Direct launchd external-volume access blocks reboot autostart; automatic reboot recovery is not established. No Studio daemon/kernel change is implied.

Frozen ordinary character benchmarks remain Badger 658.651596s total / 87.371827s image / 571.279769s outside image; Otter 312.267804s total / 93.365586s image / 218.902218s outside image. These predate the combined shared-storage workflow; no new combined creation-plus-storage or full-chapter benchmark has been measured. Keep preparation, generation, visual QA, registration, metadata closeout and asynchronous transfer time distinct.
