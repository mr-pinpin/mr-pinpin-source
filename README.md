# Mr. PinPin Source and Authoring

[Visit Mr. PinPin’s house](https://mr-pinpin.github.io/) ·
[Read the original book](https://mr-pinpin.github.io/original/).

[Read the storyboard edition](https://mr-pinpin.github.io/storyboard/?chapter=1&lang=ru).
The storyboard edition and standalone family stories are developed alongside the
original book. Chapter and language are preserved in the URL; the library shows
the available editions.

[Chapter library](https://mr-pinpin.github.io/storyboard/library.html)
and [interactive atlas](https://mr-pinpin.github.io/storyboard/atlas-webgpu.html).

This repository is the source workspace, not the canonical reader website.

Start with the [storyboard guide](docs/storyboard/README.md) for content and runtime,
[workspace guide](WORKSPACE.md) for checkouts and retained drafts, and
[publishing guide](PUBLISHING.md) for releases.

[Read One Day in the Forest — five chapters](https://mr-pinpin.github.io/storyboard/?story=one-day-in-the-forest&lang=ru).

| Role | Location | Contents |
| --- | --- | --- |
| Authoring | [mr-pinpin-source](https://github.com/mr-pinpin/mr-pinpin-source) | Story text, translations, code, provenance, manifests, original history |
| Reader releases | [mr-pinpin.github.io](https://github.com/mr-pinpin/mr-pinpin.github.io) | Small deployment scripts and immutable release records |
| Public storage | [mr-pinpin-archive](https://huggingface.co/buckets/miguelemosreverte/mr-pinpin-archive) | Verified originals, experiments, preservation copies, release bundles |
| Production sessions | [Private session and prompt archive](https://github.com/mr-pinpin/session-archive) | Sanitized conversation snapshots, exact image prompts, and provenance (authorized collaborators only) |

The official workflow verifies a selected public HF bundle before deploying;
readers receive the resulting files from Pages. See [PUBLISHING.md](PUBLISHING.md)
for release, restoration, and rollback instructions.

Former GitHub repo URLs, including `mr-pinpin-original`, `mr-pinpin-pages`, and
`mr-pinpin-official`, redirect to the repositories in the `mr-pinpin` organization.
Old **Pages website URLs do not automatically redirect**. Use
`https://mr-pinpin.github.io/` for readers. Source pushes run verification only;
official deployment happens in the separate release repository.

## Permissions

Only project-owned software is [MIT-licensed](LICENSE-MIT), within the
[scope in LICENSE](LICENSE). Stories and other creative content, including
content embedded in code, are excluded. [Content permissions](CONTENT-LICENSE.md)
allow personal/noncommercial family reading, downloading, and printing only for
rights the project controls. [Third-party terms](THIRD-PARTY-NOTICES.md), legal
exceptions, public-domain status, and valid prior grants remain unaffected.

## Quickstart

Work in `/Users/miguel_lemos/anastasia-pinpin-repos/mr-pinpin-source`. The sibling
`mr-pinpin-official` is the deployment checkout for `mr-pinpin/mr-pinpin.github.io`;
local directory names have not changed with the organization move. Old local names are
compatibility symlinks; use canonical paths for tools that reject symlink parents.

```sh
npm ci
npm run verify
python3 scripts/serve-chapter-workshop.py --port 8782
```

Open http://127.0.0.1:8782/storyboard/library.html for local reading, or the workshop
URL printed by the server when the relevant review pack is present. Retained Elder
production packs live in the draft worktree described in [WORKSPACE.md](WORKSPACE.md).
If production media is absent,
first install the pinned HF SDK in your Python environment and run
`npm run assets:restore-production` with an external `PINPIN_ASSET_CACHE`.
See [restoration instructions](tools/assets/backup-publication.md).

| Task | Command |
| --- | --- |
| Check production without creating an artifact | `npm run verify` |
| Run unit tests | `npm test` |
| Refresh asset classification after authoring | `npm run assets:plan` |
| Restore missing production / archive media | `npm run assets:restore-production` / `npm run assets:pull` |
| Inspect archive backup/migration | `npm run assets:sync -- --dry-run` |
| Build on mini/SSD into a new output directory | `npm run build:pages -- --dest NEW_ARTIFACT_DIRECTORY` |
| Publisher commands | `npm run release -- --help` |
| Publisher checks | `npm run test:publishing` |

## Layout

| Path | Purpose |
| --- | --- |
| `docs/index.html`, `docs/home.css`, `docs/home.js` | Illustrated house menu |
| `docs/original.html`, `docs/images/` | Preserved original book and artwork; `/original/` is its reader alias |
| `docs/storyboard/` | Reader, atlas, library, stories and local review tools |
| `assets/` | Runtime/archive inventory and policy; storage documentation |
| `tools/assets/` | Verified backup, restoration and preservation manifests |
| `tools/publishing/` | Package, upload, manifest selection and rollback tools |
| `scripts/` | Authoring helpers and focused verification |

Publishing requires an explicit release selection in `mr-pinpin/mr-pinpin.github.io`.
Rollback selects a prior manifest with `publish.py select --pages-repo OFFICIAL_CLONE
--release PREVIOUS_SHA --expected-current CURRENT_SHA`, followed by an ordinary
commit/push there. Keep old manifests and HF objects; never force-push for rollback.

## Preserved Book

The new edition lives in `docs/storyboard/`. Run `python3 tools/build_book.py`
(requires `lxml`) and `python3 tools/prepare_scenes.py` to rebuild source data.
Both scripts verify that the original narrative is preserved in order.

This repository preserves the original HTML book and all 100 original PNG
illustrations, without compression, resizing, abridgment, or changes to the story.
Mr. PinPin and Mr. PomPom are brothers; this book focuses on Mr. PinPin's origin.

The supplied `MrPinPin.html` is stored as `docs/original.html`, accessible through
`/original/` on GitHub Pages. Its bytes and the image bytes are unchanged from the
original export. The original document layout and font references are preserved.

The source GitHub Actions workflow verifies assets, build references and publishing
tools on main pushes and pull requests. It does not deploy. The official repository
verifies and deploys an explicitly selected release bundle; experiments are excluded
from that bundle. Readers do not need a Pages branch or ZIP download.

To read the original locally, open `docs/original.html` in a browser.
`docs/index.html` is the illustrated house menu.

## Development and Asset Storage

```sh
npm ci
npm test
npm run build:pages
```

Production assets remain in the preserved Git history; they are not copied to
the lightweight official repository. Missing production media can be restored
from its preservation manifest. Non-production assets use the Hugging Face bucket
recorded in `assets/manifest.json`, with content hashes and verified restoration.
Source code, generation recipes, provenance, and the manifest remain versioned.
The production build does not require Hugging Face credentials or make readers
download anything from the archive.

Use `npm run assets:sync -- --dry-run` to inspect changes, `npm run assets:sync`
to back up and migrate verified archive assets, and `npm run assets:pull` to
restore missing review/authoring assets. The sync command does not commit, push,
delete working files, or rewrite history. [Storage workflow](assets/README.md).
