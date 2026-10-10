# Working in Mr. PinPin Source

- For explicitly image-led 360° illustrations, panorama variations and derived
  cubemaps, use `docs/storyboard/panorama-workflow/README.md` and
  `tools/panoramas/README.md`. Keep these artistic studies separate from the
  measured location packs; the user’s chosen workflow takes precedence.

- For house scenes, camera changes, and room panoramas, start with
  `docs/storyboard/locations/AGENTS.md` and the selected location's `README.md`.
  Use the reusable renderer in `tools/locations/` and its recorded jobs. Keep
  geometry references distinct from illustration/style references, and record
  generated derivatives with their input hashes and review status.

- Read `LICENSE`, `CONTENT-LICENSE.md`, and `THIRD-PARTY-NOTICES.md`. MIT covers
  owned software only, never creative content merely because it is in JS/JSON/HTML.
  Preserve upstream terms and prior grants; do not claim rights in unprotectable
  AI output or public-domain material. Keep `docs/permissions/` notice copies in
  sync with root notices. New notices require a new release, not archive mutation.

- Canonical source: `https://github.com/mr-pinpin/mr-pinpin-source`, local
  `/Users/miguel_lemos/anastasia-pinpin-repos/mr-pinpin-source`. Use this checkout
  for authoring; old local names are compatibility symlinks only.
- Canonical reader site: `https://mr-pinpin.github.io/`.
  Public storage stays `miguelemosreverte/mr-pinpin-archive`; do not rename its
  objects or rewrite historical reports/manifests to match repository renames.
- Read `WORKSPACE.md` to distinguish canonical checkouts from retained worktrees
  and migration snapshots. Preserve branch-only work and uncommitted edits.
- Read `PUBLISHING.md` before releasing. The separate `mr-pinpin/mr-pinpin.github.io` repository
  is a lightweight deployment ledger, not an authoring checkout. Never copy this
  repository's Git history or binary assets into it. Use the verified,
  content-addressed release tools in `tools/publishing/`. Its local checkout remains
  `/Users/miguel_lemos/anastasia-pinpin-repos/mr-pinpin-official`.
- Preserve the original book and approved story/image content. Storage migration
  must not regenerate, resize, compress, or shorten the published book.
- Keep source, recipes, provenance, and asset manifests in Git. Restore absent
  production media through `npm run assets:restore-production`; backing up media
  does not authorize deleting working files or rewriting its Git history.
  Non-production media belongs in the configured Hugging Face archive.
- Read `assets/README.md` before generating, moving, restoring, or publishing assets.
  Use the catalog and `npm run assets:sync`, not manual deletion or blanket staging
  of experimental binaries. A verified matching backup is required before untracking.
- Never commit tokens, credential files, signed download URLs, or local cache data.
  Use standard Hugging Face authentication. Never change archive visibility silently.
- Prefer the mini and TB4 for large transfers, caches, and site build outputs.
  Set `PINPIN_ASSET_CACHE` outside the checkout; pass an external build output path
  when the Air is low on disk space.
- Commit completed task changes and push them to the source remote. Preserve
  unrelated work; a source push does not select an official reader release.
- Run focused asset tests and a production build before pushing. The Pages artifact
  must contain only production assets, with valid checksums and no local symlinks.
- Keep local review tools usable through verified asset restoration. Do not describe
  archived or proposed studies as approved production content.
- Do not rewrite Git history to remove old assets without explicit approval.
- Renamed GitHub repository URLs redirect; old Pages URLs do not automatically
  redirect. The source workflow performs verification only; an old source-site
  snapshot may still be served, but link readers to `https://mr-pinpin.github.io/`.
  A source push does not select an official release. Rollback explicitly selects an
  existing release SHA in the official checkout, with ordinary commits/pushes and
  retained archive objects.
