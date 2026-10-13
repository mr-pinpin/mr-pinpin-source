# Publishing Mr. PinPin

Canonical reader site: https://mr-pinpin.github.io/

Books: https://mr-pinpin.github.io/storyboard/library.html

Atlas: https://mr-pinpin.github.io/storyboard/atlas-webgpu.html

Preserved original book: https://mr-pinpin.github.io/original/

## Repository responsibilities

- [mr-pinpin-source](https://github.com/mr-pinpin/mr-pinpin-source): authoring source, story text,
  translations, artwork provenance, asset policies, and preserved Git history.
- [mr-pinpin.github.io](https://github.com/mr-pinpin/mr-pinpin.github.io): deployment code and small, versioned
  release records only. Do not commit artwork, videos, release archives, or
  authoring history to this repository.
- Public Hugging Face bucket `miguelemosreverte/mr-pinpin-archive`: verified
  originals, production-media preservation copies, experiments, and immutable
  release bundles. Never put credentials or private files here.

The public bucket name is unchanged. Repository renames do not change release
hashes, asset object keys, or preserved Git history. Keep historical reports and
immutable release manifests exactly as recorded.

Former GitHub repository URLs, including `mr-pinpin-original`, `mr-pinpin-pages`,
and `mr-pinpin-official`, redirect to the repositories in the `mr-pinpin` organization.
Their old Pages URLs do **not** automatically redirect. Link readers to
`https://mr-pinpin.github.io/`. The source repository now runs verification only
through `.github/workflows/verify-source.yml`. Its former Pages workflow is retired.
An old source-site snapshot may remain available, but it is not updated by source
pushes and must not be used as the reader address.

Canonical local checkouts are
`/Users/miguel_lemos/anastasia-pinpin-repos/mr-pinpin-source` and
`/Users/miguel_lemos/anastasia-pinpin-repos/mr-pinpin-official`. Old local names are
symlink aliases only. Use canonical directories with the publishing CLI, which
rejects symlink path components. The organization move does not rename these local
directories; `mr-pinpin-official` now checks out `mr-pinpin/mr-pinpin.github.io`.

For local checkout roles and retained history, see [WORKSPACE.md](WORKSPACE.md).

## Commands and layout

Run authoring commands from the source checkout. Install Node dependencies with
`npm ci`; install `tools/assets/requirements.txt` in the Python environment used
for HF transfers. Use an external `PINPIN_ASSET_CACHE` and mini/SSD build outputs.

| Step | Command or path |
| --- | --- |
| Restore missing production | `npm run assets:restore-production` |
| Verify source assets/references | `npm run verify` |
| Create a fresh production artifact | `npm run build:pages -- --dest NEW_ARTIFACT_DIRECTORY` |
| Package existing verified bytes | `npm run release -- package --artifact ARTIFACT --source-commit FULL_SHA --out NEW_PACKAGE_DIRECTORY` |
| Upload plus anonymous readback | `npm run release -- upload --package PACKAGE --cache EXTERNAL_CACHE --receipt NEW_RECEIPT.json` |
| Add an immutable record to official repo | `npm run release -- stage --package PACKAGE --pages-repo OFFICIAL_CLONE` |
| Select new release or rollback | `npm run release -- select --pages-repo OFFICIAL_CLONE --release SELECTED_SHA --expected-current CURRENT_SHA` |
| Materialize/verify before deployment | `python3 OFFICIAL_CLONE/scripts/materialize.py --repo OFFICIAL_CLONE --out NEW_VERIFY_DIRECTORY` |

In source, `docs/` contains book/runtime files, `assets/` holds runtime policy and
inventory, `tools/assets/` provides preservation/restoration, and
`tools/publishing/` provides the release CLI. In official, `releases/<sha>.json`
are immutable records, `release.json` selects one, `scripts/` verifies it, and
`.github/workflows/pages.yml` deploys it. HF holds the bytes addressed by those
manifests. Full flags and safeguards: [publisher guide](tools/publishing/README.md).

## Release contract

Build with the production allowlist, using the existing Pages builder. Prepare
the release using `tools/publishing/` and follow its command documentation.
Each release records the source commit, every output file's size and SHA-256,
and the archive identity. Upload and verify the public bundle before selecting
it in the Pages repository.

The Pages workflow downloads the selected release anonymously, checks archive
and per-file identities, rejects unsafe paths and links, enforces the deployment
size budget, and only then deploys. Readers receive files from GitHub Pages,
not from Hugging Face. A storage outage can block a new deployment without
breaking a release that Pages is already serving.

Keep previous release records and objects. Rollback runs the same explicit
`select` command with the previous manifest SHA and the actual current selector,
then commits/pushes that selector change in the official repo. It does not
force-push or rewrite
history. Content-addressed storage is application-enforced immutability, not a
provider guarantee against account-owner deletion. Verification detects changed
content; it cannot prevent a bucket administrator deleting an object.

## Artwork safety

The approved Elder WebP derivatives retain their original pixel dimensions.
The original PNGs remain distinct assets. Never treat a compressed derivative
as a backup of its source. Verify the original against its provenance hash and
verify its uploaded bytes before considering removal from Git tracking.

Backing up an asset does not itself delete or untrack it. Preserve working
files and original history. Any later untracking must use matching verification
receipts and leave a documented restoration path. Do not bulk-delete media to
make a repository look smaller.

## Future agents

1. Read `AGENTS.md`, `assets/README.md`, and the publishing tool documentation.
2. Make changes in the authoring repository, not the Pages repository.
3. Preserve or restore original assets through the verified manifests.
4. Build and test on the mini/SSD when the work is disk-heavy.
5. Create and verify a new release, then update the Pages release selector.
6. Wait for successful deployment and check chapters, languages, image loading,
   and atlas navigation on the public URL before reporting success.

Do not assume that pushing to the authoring repository automatically selects a
release in the separate Pages repository. That release selection is an explicit
publishing step.

## Chapter-specific hosting

The optional scoped reader builder uses the same authoring checkout and
verified production catalog:

```sh
npm run build:chapter -- --story scooby-bath --dest NEW_EXTERNAL_DIRECTORY
```

Its artifact can pass through the same immutable package/upload/template
workflow into a separate lightweight chapter deployment repository. Creating
that repository does not move authoring history or archive objects. Preserve
central library and old reader URLs until the new live reader is verified.
Current migration design and implementation limits: [chapter hosting](tools/publishing/CHAPTER-HOSTING.md).
