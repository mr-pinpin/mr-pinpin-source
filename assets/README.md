# Mr. PinPin Source Assets

For the separate lightweight Pages repository and immutable release bundles,
read [PUBLISHING.md](../PUBLISHING.md). The Git tracking statements below describe
the `mr-pinpin-source` authoring repository, not `mr-pinpin.github.io`: the deployment repository holds
only code and release manifests. Preserving media in HF does not automatically
remove its historical Git copies.

`policy.json` assigns explicit production and archive roles. `manifest.json` records
each asset's relative path, role, byte count, SHA-256, and immutable object path.
Source code, source/provenance notes, generation records, and policy stay in Git.
Production assets are available from Git or the verified production preservation
manifest when absent. Ordinary HTML reading makes no Hugging Face requests; explicit PDF downloads from the library or `download=pdf` routes fetch verified public PDFs from Hugging Face.
Publishing and restoration can download from HF. Experimental, historical, model, and review assets
are archived in the public HF bucket `miguelemosreverte/mr-pinpin-archive` after
verification. Public visibility was explicitly approved and enabled by the main
operator on 2026-09-22, resolving the earlier private-storage quota blocker.

Canonical reader site: https://mr-pinpin.github.io/.
Authoring source: https://github.com/mr-pinpin/mr-pinpin-source.
Public store: https://huggingface.co/buckets/miguelemosreverte/mr-pinpin-archive.
The store name and existing hash keys are unchanged by repository renames.
GitHub repo redirects do not automatically redirect old Pages URLs.

## Historical migration checkpoint

Remote archive preservation succeeded: all 181 manifest assets, totaling
745,024,807 bytes, passed fresh download and SHA-256 verification on the mini.
The successful `action: verify` receipt is
`/Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache/mini-upload-receipt.json`.
Migration succeeded: the main operator applied the receipt and untracked 111
verified archive paths while retaining all working files. The production build
contains 411 files (669,321,739 bytes); navigation checks passed at 320, 390, and
1440 pixels. Authoring Blender sources are preserved independently under
`authoring/blender-v3`; see
`tools/assets/verification-authoring.md` for their separate verification status.

## Plan and sync

```sh
npm run assets:plan
npm run assets:sync -- --dry-run
npm run assets:sync
```

Refresh the catalog after adding media or changing story registries. Supported
binary files under `docs` default to archive unless explicitly selected by policy
or referenced by a configured production registry. Original-book assets and
registered stories, covers, sprites, and video variants remain production.
Direct HTML/CSS/JS references need a policy entry; computed paths require review.
New file extensions or registry types need explicit policy support. The Pages
builder checks the catalog but does not refresh it automatically.

Normal sync runs `node tools/assets/catalog.cjs --root ROOT`, then invokes
`tools/assets/hf_store.py push --manifest assets/manifest.json --root ROOT
--cache CACHE --profile archive --receipt RECEIPT`. It uses `PINPIN_PYTHON`
(default `python3`). Install the adapter dependencies from
`tools/assets/requirements.txt` into your Python environment before uploading.
Dry run builds the catalog in memory and reports proposed changes without uploads,
generated-file writes, index changes, or `.gitignore` changes.

Only a version 1 `push` or `verify` receipt with `verified: true`,
`dry_run: false`, and the exact bucket permits migration. Every archive entry
must match its path, role, byte count, SHA-256, and content object key, with both
`verified: true` and `remote_verified: true`. Omitted proof fields are refused.
Sync rehashes present local archive files after remote verification, updates its
managed `.gitignore` block with anchored, escaped exact paths, and runs
`git rm --cached` for verified indexed archive paths. Working files remain on disk,
including staged modifications that match the uploaded manifest. Indexed file
bytes must also match the receipt; a different staged version stops sync. Managed
symlinks must match their staged link targets. Missing local
archive files are allowed when the receipt proves their manifest identities.
Changes since upload stop the operation before Git changes. Content outside the
managed ignore block is preserved. Sync never commits, pushes Git, deletes local
assets, or rewrites Git history; old Git blobs remain in historical commits.

Policy-listed source symlinks may be read and hash-checked for upload and local
verification. A directory symlink such as
`docs/storyboard/models/pinpin-v3/renders` is ignored and removed from the index
only when every manifest child is archive and every file currently beneath it is
accounted for as archive. Unknown files or production children keep that parent
symlink tracked. Arbitrary symlinks are refused. Restore does not write through
symlink destinations.

The adapter's explicit `push --allow-source-symlinks` flag permits source reads
through links without interpreting policy; sync checks the policy allowlist before
using it. The flag is rejected for pull and verify, so it cannot enable writes
through restore destinations.

## Cache and mini upload

Set `PINPIN_ASSET_CACHE` outside the checkout. The default is
`${XDG_CACHE_HOME:-$HOME/.cache}/mr-pinpin/assets`; `--cache CACHE` overrides it.
Use the mini's SSD for large transfers:

```sh
export PINPIN_ASSET_CACHE=/Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache
```

The primary operator can upload a regular-file staging root on the mini using the
same manifest, then apply its receipt to the local checkout:

```sh
"${PINPIN_PYTHON:-python3}" tools/assets/hf_store.py push \
  --manifest assets/manifest.json --root /path/to/regular-file-stage \
  --cache "$PINPIN_ASSET_CACHE" --profile archive \
  --receipt "$PINPIN_ASSET_CACHE/mini-upload-receipt.json"
npm run assets:sync -- --apply-receipt /path/to/mini-upload-receipt.json --dry-run
npm run assets:sync -- --apply-receipt /path/to/mini-upload-receipt.json
```

Receipt application skips catalog generation and upload. Keep the matching
manifest available locally. Receipts contain hashes and verification records,
not credentials; they are trusted operator artifacts, not signed attestations.
An incomplete, mismatched, duplicate, dry-run, or unverified receipt is refused.
Sync-generated receipts live in the external cache.

For interrupted direct uploads, reuse `--receipt FILE` or supply
`--resume-receipt FILE`. Matching prior remote proofs may skip repeat downloads
only when bucket, path, role, bytes, SHA-256, object key, and remote Xet identity
still match. `--workers N` sets transfer verification concurrency from 1 to 16
(default 4). New or changed remote objects require a fresh download and hash check.

## Restore and verification

```sh
npm run assets:restore-production
npm run assets:pull
npm run assets:verify -- --receipt /path/outside/repo/archive-verified.json
```

`assets:restore-production` uses `tools/assets/production-preservation.json` for
missing runtime media. `assets:pull` restores archive/review media from
`assets/manifest.json`. Both operate in the source checkout; neither populates
the official repo with artwork. See [preservation instructions](../tools/assets/backup-publication.md).

Pull restores missing archive files using the local cache or HF and verifies
their byte counts and SHA-256. Existing conflicting files are not overwritten.
To restore into a separate regular directory, invoke the adapter directly:

```sh
"${PINPIN_PYTHON:-python3}" tools/assets/hf_store.py pull \
  --manifest assets/manifest.json --root /path/to/restore \
  --cache "$PINPIN_ASSET_CACHE" --profile archive
```

Objects use `sha256/<first-two-hex>/<sha256>/<basename>`. New content gets a new
object path. Upload receipts require remote content verification; matching size
alone is insufficient. Configure authentication using the standard HF credential
store or `HF_TOKEN` in the operator environment. Never put credentials in the
repository, browser code, receipts, or logs. Production builds require no HF token.

## Chapter PDF downloads

`assets/chapter-pdfs.json` preserves the separately generated chapter PDFs in the same public bucket. They are downloadable editions, kept outside the Pages bundle; the HTML reader continues to serve its illustrations from Pages. `docs/storyboard/library-pdfs.json` records each completed chapter, language, filename, public content-addressed URL, exact size and SHA-256. The library fetches a PDF only after selection; explicit reader URLs with `download=pdf` request the PDF directly.

Generate with `scripts/export-chapter-pdfs.cjs` and follow `docs/storyboard/production/house-menu-library-20260922/PDF-EXPORT.md`. Keep heavy output and cache on TB4. PDF originals can be restored into a separate directory using `tools/assets/hf_store.py pull --manifest assets/chapter-pdfs.json --root EXTERNAL_DIRECTORY --cache EXTERNAL_CACHE --profile archive`. Never put PDF binaries or credentials into the Pages ledger.

## Public archive readback

For the approved public bucket, `hf_store.py push --public-http-readback`
uses anonymous streamed HTTPS readback instead of the SDK download transport.
Uploads still use standard Hugging Face authentication; byte counts, SHA-256
and remote metadata checks remain required. The option refuses other buckets.
Release uploads use this verified public readback plus the release materializer
verification. No visibility or historical object keys change.
