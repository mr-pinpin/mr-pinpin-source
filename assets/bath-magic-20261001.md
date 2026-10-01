# Bath-Time Flood draft preservation

Verified on 2026-10-01. This is preservation of an unpublished review draft,
not a production release or user approval of the illustrations.

- Manifest: `assets/bath-magic-20261001.json`.
- Matching receipt: `assets/bath-magic-20261001-receipt.json`.
- Bucket: `miguelemosreverte/mr-pinpin-archive` (existing approved public store).
- **155 media files, 272,831,464 bytes.**
- Receipt action `push`, version 1, `verified: true`, `dry_run: false`.
- Every path, role, size, SHA-256 and content object key matches; every entry has
  both `verified: true` and `remote_verified: true`.
- Independent `verify-preservation.py --current` passed: every current media file
  under the scoped pack is included and its bytes still match the snapshot.

Scope includes the 55 unchanged image-model originals (selected images and
rejected/superseded candidates), cover/concept art, native-size review WebPs,
initial and final contact-sheet masters, exact reference inputs, nine geometry
guide packs and final browser screenshots. Textual story/plans, prompts,
generation records, camera metadata, recipes and browser results stay in Git.
No files were deleted or untracked, and no global asset manifest or policy was
changed. The regular-file stage and working originals remain on the mini SSD.

`docs/storyboard/production/bath-magic-20261001/input-preservation.json` maps all
55 generation records and 37 distinct input-image hashes to preserved bytes.
All 55 output masters were compared with their original image-tool output files.
`selected-scenes.json` records the cover and 36 selected scene versions.
`contact-sheets.json` records the input hashes and layout recipe for the final
overview and six sheets. The complete-image reader check passed at 1440px, 390px
and 320px in installed Chrome; its results and source hashes are in the pack.

## Restore a review copy

Use a regular directory on TB4, with the asset cache outside the source checkout:

```sh
python3 tools/assets/hf_store.py pull \
  --manifest assets/bath-magic-20261001.json \
  --root /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-restored \
  --cache /Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache \
  --profile archive
```

This restores the preserved media to their manifest paths under
`docs/storyboard/production/bath-magic-20261001/`. Copy the source pack's text
files and `docs/storyboard/review/bath-magic.{html,css,js}` into the corresponding
paths, then serve that restored `docs` directory. Restoration verifies hashes
and refuses conflicting existing file contents. It does not publish the chapter.

The current isolated preview is served by the mini on port 18796, forwarded to
Air port 18795. See the pack's `REVIEW.md` for restart commands and the browser
URL. Creative material remains under the repository content notices; preservation
is not a rights grant or an assertion of copyright in purely AI-generated output.
