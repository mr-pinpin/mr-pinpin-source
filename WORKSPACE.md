# Local workspace guide

The authoring checkout moved to the Mac mini's SSD on 2026-10-01 at Miguel's
request. Its physical path is
`/Volumes/TB4/mac-mini-storage/shared/pinpin-workspace/mr-pinpin-source`.
Use `ssh mini` for authoring commands, tests, builds and Git operations there.
The former `/Users/miguel_lemos/anastasia-pinpin-repos/mr-pinpin-source` path on
both machines is a compatibility symlink, not another copy. Use the physical path
for tools that reject symlink checkout paths. Do not recreate the checkout on the Air.

The complete checkout, Git history, ignored files and uncommitted work were copied
and checksum-verified before the Air copy was removed. All 1,926 modified/untracked
status entries matched at cutover. Linked worktree registrations were preserved;
the Elder release worktree still resides on the Air and must not be pruned from the mini.

The R5 bath production pack and preview server also live on the mini. Its server
uses port 18796; the existing Air tunnel exposes port 18795. This checkout move
does not publish or change the official reader. Heavy output belongs on TB4.

The names below remain relative to `/Users/miguel_lemos/anastasia-pinpin-repos/`
on the Air for compatibility. The official deployment checkout has not moved.
GitHub roles and release commands are in [PUBLISHING.md](PUBLISHING.md); content
and runtime files are described in the [storyboard guide](docs/storyboard/README.md).

| Directory | Role | Use for new work |
| --- | --- | --- |
| `mr-pinpin-source/` | [Authoring repository](https://github.com/mr-pinpin/mr-pinpin-source) | Stories, application code, provenance, manifests and tools |
| `mr-pinpin-official/` | [Official deployment repository](https://github.com/mr-pinpin/mr-pinpin.github.io) | Select or roll back verified releases; no artwork or authoring history |

Public reader: https://mr-pinpin.github.io/. Source pushes run checks; they do not
select an official release. Prefer the mini/TB4 for large builds and caches.

## Compatibility aliases

`mr-pinpin-original` points to `mr-pinpin-source`; `mr-pinpin-pages` points to
`mr-pinpin-official`. These are symlinks, not duplicate repositories. Keep them for
older tooling and historical references. Use canonical paths for the publishing
CLI, which rejects symlink path components. Do not rewrite historical manifests
or reports merely to update names.

## Retained authoring worktrees

These share the source repository’s Git history but have independent working
files. Neither is the default place for new authoring.

| Directory | Branch | Why it is retained |
| --- | --- | --- |
| `mr-pinpin-cover-standard/` (compatibility symlink) | `draft/book-workshop-backup-20260921` | Full Elder production history, including branch-only commits; physical worktree is `/Volumes/TB4/mac-mini-storage/shared/pinpin-retained-worktrees/mr-pinpin-cover-standard`, retained and locked for external storage |
| `mr-pinpin-elder-release/` | `publish/elder-five-chapters-20260922` | Earlier release integration and verification work; inspection on 2026-09-22 found an uncommitted `scripts/verify-title-covers.cjs` edit |

The published Elder story JSON and selected WebP files on main are reader assets,
not substitutes for the original production pack. The draft worktree contains
`docs/storyboard/production/chapters-02-04/revision-06/`; that pack is not currently
part of main. To inspect or resume it, read the worktree’s instructions and reports,
then restore any missing media through its documented provenance/backup paths.
Do not blindly change main to the draft branch or copy the whole draft over main.

Before retiring any worktree, inspect `git worktree list`, its current status and
branch-only commits. Clean working files alone do not mean its work is merged.
The observations above are a dated inventory, not a permanent status guarantee.

The cover-standard worktree was copied and hash-verified as a complete directory
before relocation on 2026-09-24. Its old path remains a compatibility symlink;
the TB4 mount must be available to use it. Git history and worktree metadata now
live with the canonical source checkout on the mini SSD. Git's worktree registration was
repaired for the physical path and locked to protect it while the share is absent.

## Migration snapshots

`mr-pinpin-pages-template-20260922/` and
`mr-pinpin-pages-template-final-20260922/` are non-Git snapshots from the deployment
migration. Their pre-organization names and URLs are historical. Do not start a
release from them; use current `tools/publishing/` and the official checkout.

## Separate projects

`MrPinPin/`, `mr-pinpin/`, and `learning-with-anastasia/` are independent repositories
with their own histories, not aliases of the canonical source. The first contains
an older owl-glasses story, the second a small static site, and the third an
educational magazine. Similar names do not authorize merging, moving or deleting
them as part of this book’s cleanup.

## Before starting a task

1. Start in `mr-pinpin-source/` and read `AGENTS.md`.
2. Check Git status; other agents may be editing the same checkout.
3. Find content in the storyboard guide, asset handling in `assets/README.md`, and
   release steps in `PUBLISHING.md`.
4. Keep changes scoped. Preserve existing branch-only work and unrelated edits.
5. Run the relevant checks and commit only the files belonging to the task.
