# Expanded talking-duck draft preservation

Verified on 2026-10-01. This preserves the complete local R2 review draft, not an
official chapter release or user approval of every illustration.

- Manifest: `assets/bath-magic-20261001-r2.json`.
- Matching receipt: `assets/bath-magic-20261001-r2-receipt.json`.
- Existing approved public bucket: `miguelemosreverte/mr-pinpin-archive`.
- **261 media files, 450,295,404 bytes.**
- Receipt: version 1, action `push`, `verified: true`, `dry_run: false`.
- Every entry matches path, archive role, size, SHA-256 and content object key;
  every entry has both `verified: true` and `remote_verified: true`.
- Independent `verify-preservation.py --current` passed for every current file
  and full coverage of the scoped pack. No originals were deleted or untracked.

The selected chapter has 56 scenes and a cover: 25 newly generated scenes, 31
unchanged reused scene illustrations, and the unchanged reused cover. All 37
new image-tool outputs (including studies and superseded candidates) are retained
and were compared with their original tool files on TB4. Their 34 distinct input
hashes are mapped in `input-preservation.json`. Exact prompts, generation records,
camera guides and review notes are preserved with the source. New artwork used
the built-in image-generation tool.

`reuse.json` and `reuse-records/` explicitly distinguish old work from new
generations. All 32 reused master/WebP pairs match v1 byte-for-byte, and their
original prompts, generation records and exact input images are preserved in R2.
The final selected versions are in `selected-scenes.json`. The overview and ten
six-panel sheets use final selections; their v2 input hashes and layout recipe
are in `contact-sheets.json`. The exploratory concept is labelled as such and
does not replace the chronological storyboard.

The final reader check passed at 1440px, 390px and 320px with all 56 illustrations
and cover decoding, English/Russian/Spanish controls, storyboard navigation,
and no missing-image placeholders, browser errors or horizontal overflow.
`browser-check/results.json` contains the tested source/plan/media hashes.

All **167 v1 source files and 155 v1 media files remain unchanged**, checked
independently. V1 was not replaced. All heavy processing, browser screenshots,
staging, media and caches are on the mini SSD; only source text and metadata are
kept in the Air checkout. Global asset catalogs/policies and official publication
registries were not changed.

## Restore

From the source checkout, restore into a regular TB4 directory:

```sh
python3 tools/assets/hf_store.py pull \
  --manifest assets/bath-magic-20261001-r2.json \
  --root /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-r2-restored \
  --cache /Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache \
  --profile archive
```

Media restore beneath `docs/storyboard/production/bath-magic-20261001-r2/`.
Copy the corresponding source pack text and
`docs/storyboard/review/bath-magic-r2.{html,css,js}` to matching paths, then serve
the restored `docs` directory. To use the previous-draft link, also restore v1
with its separate unchanged manifest and reader. This does not publish either
draft. Restoration verifies content identities and refuses conflicting files.

Current local reader:
`http://127.0.0.1:18795/storyboard/review/bath-magic-r2.html?lang=en`.
The mini server listens on 18796 and is forwarded to Air port 18795.
See the production pack's `REVIEW.md` for workflow details and review limits.

Creative material remains subject to the repository content notices.
Preservation and reuse do not grant additional rights or assert copyright in
purely AI-generated output.
