# Separate chapter deployments

Recommendation, 2026-10-13: keep canonical authoring in `mr-pinpin-source`,
and introduce a lightweight deployment ledger per new chapter. The central
`mr-pinpin.github.io` site remains the library and preserves existing URLs.
The first deployment ledger is `mr-pinpin/chapter-scooby-bath`; earlier chapters remain on the central site.

GitHub permits project Pages sites for repositories. Its published-site limit
is 1 GB per site. Separate chapter sites give independent release/rollback and
size accounting; they do not establish unlimited bandwidth or availability.
References:
https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits

First ledger: `mr-pinpin/chapter-scooby-bath`, reader base
`https://mr-pinpin.github.io/chapter-scooby-bath/`. It should hold only the
publisher's verified release manifests, selector and deployment workflow.
Do not duplicate authoring Git history, original images or PDFs there.

## Build and navigation contract

A chapter artifact must include its reader runtime, localized title/text,
selected reading derivatives, relevant notices and verified assets only.
All media/reader URLs must work under the repository path prefix. The shared
library link is absolute; opening another chapter goes through its recorded
canonical URL. Preserve `lang`, chapter identifier and scene links during
migration. HTML reading remains on Pages; explicit PDFs retain existing verified
HF download handling. Native illustration backups and historical object keys
stay unchanged in the existing public HF bucket.

`npm run build:chapter -- --story scooby-bath --dest NEW_EXTERNAL_DIRECTORY`
builds a scoped artifact using the existing reader interface and production
catalog. It filters the cover/PDF registries, validates the story completeness
gate and media hashes, refuses symlinks/existing outputs, and preserves selected
media bytes. The chapter root preserves query/hash state and sets its default
story; map/PDF-library links go to the central site. Other requested stories are
forwarded to the central reader. Do not deploy the whole library to each ledger.

R6 contains 216 pages in EN/RU/ES and approximately 61MB of scoped reader files.
Four scope, tamper, symlink and output-preservation tests pass; desktop/mobile
browser checks pass in all three languages, including lazy loading and deep links.
Dynamic reader dependencies require browser checks at the final repository
prefix before promotion; the scoped builder is not a general arbitrary-site
dependency bundler.

## First cutover

1. Complete and review the Scooby chapter before promoting its selected artwork.
2. Build the scoped reader and test EN/RU/ES, deep links, lazy loading, unsupported
   image format fallback, library return and PDF downloads under a non-root base.
3. Package/upload/anonymous readback using the existing immutable release tools.
4. Create the small ledger from the publisher template, configure Pages and
   deploy; verify its live reader against the selected hashes.
5. Only after live verification, update the shared library's chapter URL and
   preserve the older `?story=scooby-bath` entry as a compatible forwarding route
   carrying language/scene state. Keep the old release selectable for rollback.
6. Migrate earlier chapters individually only after equivalent verification;
   preserve original approved media bytes and historical release records.

Source repository splitting would duplicate shared characters, location packs,
reader fixes and preservation policies. Chapter-scoped authoring folders plus
independent deployment ledgers provide the requested hosting separation while
retaining one coherent production workspace.

## Published Scooby edition

The chapter release `7c9b5542ee82650d31dcf48d5261c8ee5234712e72ee19cdbb65ea91187b9983`
is live and verified at
https://mr-pinpin.github.io/chapter-scooby-bath/storyboard/?story=scooby-bath&lang=en&v=20261013-r6.
It contains 216 pages, with all three language readers checked publicly.
The central cutover release is
`c24f3af781c1f7960633f9347ac3d04f4cf42d2580eeff2981fd4e14257009c4`.
Earlier central production assets and archived releases remain unchanged.

When a Git login lacks workflow-write permission, a new ledger can be generated
from the existing deployment repository template without changing its workflow.
The first cutover used this method; the central repository template flag was
restored afterward. The unused empty preparation repository remains separate.
