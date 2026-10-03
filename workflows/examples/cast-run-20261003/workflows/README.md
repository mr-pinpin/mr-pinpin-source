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
