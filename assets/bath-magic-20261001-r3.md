# Bath chapter R3 preservation

Verified on 2026-10-01. This is a complete local review draft, not an official
chapter release or user approval of every illustration.

- Manifest: `assets/bath-magic-20261001-r3.json`.
- Receipt: `assets/bath-magic-20261001-r3-receipt.json`.
- Existing public bucket: `miguelemosreverte/mr-pinpin-archive`.
- **252 media files, 480,541,332 bytes.**
- Receipt: version 1, action `push`, `verified: true`, `dry_run: false`.
- Every path, archive role, size, SHA-256 and content object key matches; every
  entry is `verified: true` and `remote_verified: true`.
- Independent `verify-preservation.py --current` passed exact file identities
  and complete coverage. No originals were deleted or untracked.

The chapter has 62 scenes plus a new cover: 38 unchanged R2 scene illustrations,
24 newly generated scenes, and the newly generated cover. `reuse.json` records
unchanged master/WebP identities, source scene mapping and upstream lineage.
Only selected reused masters and their required provenance inputs were copied.
Their original prompts, generation records and input bytes are preserved;
reused artwork is not described as a new generation.

All 29 R3 image-tool outputs remain preserved, including four superseded
candidates. Every output matches its original tool file on TB4. The 28 distinct
input hashes are mapped in `input-preservation.json`. Exact prompts, camera
references and generation/review records stay with the source; new artwork used
the built-in image-generation tool. `selected-scenes.json` identifies all 63
final selections. The final overview and eleven sheets use those selections;
version 2 recipes and per-panel input hashes are in `contact-sheets.json`.

Complete-image reader checks passed at 1440px, 390px and 320px, including all
62 scenes and cover decoding, EN/RU/ES controls, storyboard navigation and no
missing-image placeholders, errors or overflow. Fresh screenshots and exact
tested code/plan/media hashes are recorded in `browser-check/results.json`.
All 189 R2 source files and all 261 R2 media files remain unchanged.

Heavy processing, screenshots, staging, media and caches stay on the mini SSD.
The Air checkout contains text/code/provenance only. Global asset catalogs,
policies, official chapter lists and publication registries were not changed.

## Restore

Restore media to a regular directory on TB4:

```sh
python3 tools/assets/hf_store.py pull \
  --manifest assets/bath-magic-20261001-r3.json \
  --root /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-r3-restored \
  --cache /Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache \
  --profile archive
```

Media restore beneath `docs/storyboard/production/bath-magic-20261001-r3/`.
Copy the corresponding source pack text and
`docs/storyboard/review/bath-magic-r3.{html,css,js}` to matching locations and
serve the restored `docs` directory. Restore the separate R2 manifest/source
reader to use the previous-draft link. Restoration validates content identities
and refuses conflicting files; it does not publish the draft.

Current local reader:
`http://127.0.0.1:18795/storyboard/review/bath-magic-r3.html?lang=en`.
Use `lang=ru` or `lang=es`, and `&view=storyboard` for the visual overview.
Mini serves on 18796, forwarded to Air port 18795. See the production pack's
`REVIEW.md` for workflow details and review limits.

Creative material remains under the repository content notices. Preservation
and reuse grant no additional rights or copyright claims in AI-only output.
