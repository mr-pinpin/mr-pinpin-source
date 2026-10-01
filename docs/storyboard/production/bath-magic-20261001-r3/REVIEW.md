# Bath-Time Flood — R3 review

Status: complete illustrated draft, unpublished, awaiting user feedback. The
chapter contains 62 scenes and a new cover. Thirty-eight scene illustrations
are reused unchanged from the selected R2 draft; 24 scenes and the cover have
new artwork. See `STORY.md` and `story-plan.json` for the actual story.

Reader: `http://127.0.0.1:18795/storyboard/review/bath-magic-r3.html?lang=en`.
Use `lang=ru` or `lang=es`; add `&view=storyboard` for the visual overview.
The back arrow opens R2 in the selected language. No official chapter index,
atlas, library or publication registry is changed.

## Artwork and provenance

`revision-map.json` defines the mapping. `reuse.json` records all 38 unchanged
master/WebP pairs, exact original prompts and generation records, preserved
reference identities, and upstream R1 lineage where the R2 source was itself
reused. Reuse is a byte copy without resizing, recompression or image editing.
Only selected reused masters and their required provenance inputs are copied;
old unused candidates are not imported as R3 masters. A reused image is never
recorded as a new generation.

All 29 R3 image-tool originals are retained, including four superseded candidates.
Every original was compared against its actual tool output on TB4. Their 28
unique input hashes map to preserved exact bytes in `input-preservation.json`.
The built-in image-generation tool produced the new artwork. Exact prompts,
reference identities, selected versions and visual review notes are retained.
Final corrected selections include scenes 21-v2, 27-v2, 34-v2 and 38-v2.

`register-generations.py --ids scene-XX-v1` uses the same record schema as R2.
`--preserve-only` retains rejected candidates without selecting them. Original
masters are immutable; revisions use new version IDs. `accept-asset.py` creates
native-size WebP review copies on mini, recording dimensions, hashes and recipe.

The final storyboard uses actual selected images: a 62-frame overview and eleven
readable sheets, saved as version 2. `contact-sheets.json` records each panel's
input hash and the deterministic layout recipe. This step arranges existing art;
it does not generate or retouch it. Production details remain collapsed in the
reader, while reading and storyboard modes are directly accessible.

## Storage and verification

Heavy media, conversion, contact sheets, browser screenshots, staging and
archival operations run on the mini at
`/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r3`.
Only text, code and provenance metadata belong in the Air checkout. The existing
preview server serves this separate pack and new reader files.

All 189 R2 source identities and all 261 R2 media identities remain unchanged,
verified independently. `r2-preservation-check.json` records the source baseline
and final result. An Air disk-full interruption affected small source provenance
copies only; their complete authoritative mini copies were retained and restored.
No generated original was lost or deleted.

The final complete-image reader check passed at 1440px, 390px and 320px: all
62 scenes and the cover decode, EN/RU/ES controls and storyboard navigation
work, and there are no missing-image placeholders, browser errors or horizontal
overflow. Fresh desktop/mobile screenshots were visually checked.
`browser-check/results.json` records the exact final code/plan/media hashes,
which also match the source checkout.

The final scoped archive contains **252 media files, 480,541,332 bytes**. Every
receipt entry is remotely verified and matches its manifest identity. Independent
`verify-preservation.py --current` passed exact current-file checks and full
coverage. Manifest, receipt and restore notes are
`assets/bath-magic-20261001-r3.json`,
`assets/bath-magic-20261001-r3-receipt.json` and
`assets/bath-magic-20261001-r3.md`. No originals were deleted or untracked.

Creative content
remains subject to the repository content notices. Preservation does not grant
new rights or claim copyright in purely AI-generated output. Illustrations are
reviewed artistic interpretations, not exact measured spatial reconstructions.
This draft is not an official publication, PDF edition or approval of every image.
