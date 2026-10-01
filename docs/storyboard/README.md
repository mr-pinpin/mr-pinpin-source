# Mr. PinPin Storyboard

[Chapter library](https://mr-pinpin.github.io/storyboard/library.html) ·
[Interactive atlas](https://mr-pinpin.github.io/storyboard/atlas-webgpu.html) ·
[Original book](https://mr-pinpin.github.io/original/)

This directory contains the illustrated reader and its authoring records. Work in
`mr-pinpin-source`; the official website selects a verified release through the
separate `mr-pinpin.github.io` repository. A source push does not publish that release.
See [publishing and rollback](../../PUBLISHING.md).

## Read an edition

Reader URLs use `lang=ru|en|es` and either `chapter` or `story`:

| Edition | Public reader |
| --- | --- |
| The lake / original chapter 1 adaptation | [Read chapter 1](https://mr-pinpin.github.io/storyboard/?chapter=1&lang=ru) |
| Earlier Elder / original chapter 2 adaptation | [Read chapter 2](https://mr-pinpin.github.io/storyboard/?chapter=2&lang=ru) |
| Timber Tractor, including the return home | [Read the continuous story](https://mr-pinpin.github.io/storyboard/?story=timber-tractor&lang=ru) |
| Home, Sweet Home | [Read the bedtime story](https://mr-pinpin.github.io/storyboard/?story=home-sweet-home&lang=ru) |
| One Day in the Forest | [Read all five expanded Elder chapters](https://mr-pinpin.github.io/storyboard/?story=one-day-in-the-forest&lang=ru) |

The expanded Elder collection has 161 illustrated story scenes plus five title
pages. Its individual routes are `story=elder-papa-home`,
`elder-family-morning`, `elder-forest-path`, `elder-elder-house`, and
`elder-beneath-roots`. The collection links to each part.

The original book has 38 chapters. That is the source catalog, not a claim that
38 illustrated adaptations are ready: numbered reader editions are selected by
`chapter-editions.js`, and the library labels the remaining adaptations as upcoming.

## Find the right file

All paths below are relative to this directory unless stated otherwise.

| Path | Responsibility |
| --- | --- |
| [`../original.html`](../original.html), `../images/` | Preserved original book and illustrations; do not edit them to revise an adaptation |
| [`book.json`](book.json) | Ordered source-book extraction used by the library and source comparisons |
| [`illustrations.json`](illustrations.json), [`translations.json`](translations.json) | Selected artwork, adapted scene text, and translations for numbered editions |
| [`chapter-editions.js`](chapter-editions.js) | Numbered edition availability and print-spread layouts |
| [`stories/`](stories/), [`standalone-stories.js`](standalone-stories.js) | Trilingual story manifests, scene order, cover pages, spreads, loading and validation; the two tractor manifests compose one continuous story |
| [`covers.json`](covers.json), [`title-covers.js`](title-covers.js) | Selected localized title covers, separate text-free miniatures, approval states and rendering |
| [`index.html`](index.html), [`reader.js`](reader.js), reader/edition/print CSS | Reading, language switching and print presentation |
| [`library.html`](library.html), [`library.js`](library.js) | Available editions and the source chapter catalog |
| [`atlas-webgpu.html`](atlas-webgpu.html), `atlas-*.js`, atlas registries | Interactive forest navigation and its selected scenery, characters and media |
| [`production/`](production/), [`review/`](review/) | Generation records, prompts, continuity plans, proposals and review pages; these include historical work |
| [`../../assets/`](../../assets/) | Production/archive classification and asset hashes used by the build and restoration tools |

For the Elder collection, selected runtime images are under
`images/published/elder-cycle/`; its story manifests include each part's localized
title page. Earlier editions use the paths selected in their artwork and cover
registries. Follow the explicit selected path rather than choosing the highest
version number or moving files to make their names uniform.

Title illustrations and miniatures are different assets: a title contains localized
lettering; a miniature is a separately composed text-free image for small displays.
[`production/TITLE-COVERS.md`](production/TITLE-COVERS.md) documents the initial
four-edition cover workflow and sidecars. Consult the current registries for the
additional Elder editions and their selected WebP assets.

## Compact storyboard review

Start with the text outline, then assemble two to five numbered comic sheets
from existing illustrations and explicit blank panels for missing shots. Discuss
the sequence before generating targeted artwork and assembling the full reader.
Keep the selected scene order, captions and planned reading pauses visible.

The [reusable contact-sheet workflow](production/bath-magic-20261001-r9-final-edit/STORYBOARD-WORKFLOW.txt)
documents the configurable layout, blank panels, Russian/English exports and
hash-checked upstream images. The
[builder](production/bath-magic-20261001-r9-final-edit/build-storyboard.py)
composes existing images without cropping or retouching them.
The [five-sheet bath example](review/bath-magic-r9-final-edit.html?view=storyboard&lang=ru)
links each panel to its full scene. These are local review tools, not published
editions; restore the referenced assets before serving them.

## Source, approval and history

Source text, adaptation decisions, generated proposals and selected reader assets
have different roles. A file in `production/` is a production *record*, not proof
that its image is approved or shipped. A review page or a successful check does
not grant approval. Keep exact prompts, provenance, rejected versions and historical
reports; current selections and approval records determine the intended edition,
and the official release manifest determines what is deployed.

The camera-first [production workflow](production/WORKFLOW.md) contains useful
staging and review practices alongside dated chapter findings. Those historical
counts and pending-review notes do not describe the whole current book. The former
six-scene chapter-one candidate is likewise historical; its records remain in
[`production/chapter-01-v2.json`](production/chapter-01-v2.json).

Read the [asset guide](../../assets/README.md) before generating, moving or restoring
media. Missing production media uses `npm run assets:restore-production`; missing
archived review media uses `npm run assets:pull`. Keep caches and large build outputs
outside the checkout, preferably on the mini/SSD. Restoration verifies recorded
bytes; do not regenerate missing originals or treat a derivative as their backup.

## Local preview and checks

Run from the repository root:

```sh
npm ci
npm run verify
python3 scripts/serve-chapter-workshop.py --port 8782
```

Open `http://127.0.0.1:8782/storyboard/library.html` and use the same reader query
parameters as the public site. Local review pages may also require restored archive
media; their presence does not make them part of the published reader.

For the chapter-one browser regression suite, with Playwright and Google Chrome
already installed:

```sh
PLAYWRIGHT_MODULE=/absolute/path/to/playwright READER_URL=http://127.0.0.1:8782/storyboard/ node docs/storyboard/verify.cjs
```

That suite covers chapter-one text preservation, scene/spread structure, languages,
image dimensions and responsive rendering. Other editions have their own focused
checks, including [`verify-chapter-two.cjs`](verify-chapter-two.cjs) and
[`../../scripts/verify-elder-edition.cjs`](../../scripts/verify-elder-edition.cjs).
Visual anatomy, gaze and narrative continuity still require image-by-image review.
Complete the [release checks](../../PUBLISHING.md) before publishing and confirm the
selected release on the canonical public site.
