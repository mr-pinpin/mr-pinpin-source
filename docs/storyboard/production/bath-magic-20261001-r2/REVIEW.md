# Bath-Time Flood — expanded talking-duck draft

Status: complete illustrated R2 draft, unpublished, awaiting user feedback.
The plan contains 56 scenes plus a cover. Thirty-one scene illustrations and the
cover are reused unchanged from the previous draft; 25 scenes have newly generated artwork.
The expanded chapter includes the family joining the bath and the wooden duck
coming to life. See `STORY.md` and `story-plan.json` for the actual story.

Reader:
`http://127.0.0.1:18795/storyboard/review/bath-magic-r2.html?lang=en`

Use `lang=ru` or `lang=es` for the other language versions; add
`&view=storyboard` for the overview. The previous draft remains at
`bath-magic.html`, accessible through the back arrow. No official reader, atlas,
library or publication registry was changed.

## What is reused and what is new

`reuse.json` records the 32 unchanged assets (31 scenes and cover), their original
scene IDs, exact master/WebP identities, original generation records and prompts,
and preserved input images. Reuse is a byte-for-byte copy, not a new generation
or a recompression. Original basenames remain in nested reuse directories so
the content-addressed archive can reuse the existing object identities.
`reuse-records/` keeps the relevant original records and prompts locally in R2.

New image-tool outputs stay under `masters/`; `accept-asset.py` makes native-size
WebP review copies and records the master/derivative hashes. The wooden duck
character study is preproduction material and appears only in the collapsed
production/reference area. Scene numbers in R2 are independent of the old draft.

`v1-preservation-check.json` records a baseline of all 167 previous draft source
file identities. Final verification passed for all 167 source files and all 155 previously
preserved media files; both the old text/code and media remain unchanged. R2 only adds its own reader files and production pack.

## Storage and review tools

Heavy files stay on the mini at
`/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r2`.
The existing local preview server serves the R2 pack through a review-only
symlink; the old reader and its assets remain in place. The Python environment
reuses the existing Pillow 12.3.0 runtime without changing it.

Source recipes:

- `reuse-assets.py`: copy exact selected old artwork and document its origins.
- `register-generations.py`: complete provenance and transfer a new generated
  original, prompt and record to TB4, then invoke `accept-asset.py`.
- `refresh-media.py`: index existing assets and their hashes for the reader.
- `contact-sheets.py`: arrange all current selected pictures into an overview
  and readable six-panel sheets; no synthesis or retouching.
- `preserve-inputs.py`: map new generation inputs to preserved exact bytes.
- `prepare-archive.py` and `verify-preservation.py`: scoped regular-file snapshot
  and independent verification of matching remote proofs/current media.
- `check-reader.cjs`: installed-Chrome desktop/mobile reader checks using the
  scene count from the plan, including full-image decoding with `--complete`.

The final complete-image reader check passed at 1440px, 390px and 320px: all
56 scenes plus the cover decode, language switching and storyboard navigation
work, and there are no missing-image placeholders, browser errors or horizontal
overflow. Cover and first scene load eagerly; later scenes remain lazy.
`browser-check/results.json` records the exact tested code/plan/media hashes.

The final storyboard uses the actual selected artwork: one 56-frame overview
and ten readable sheets, saved as contact-sheet master version 2. The earlier
exploratory concept remains explicitly labelled inside production references;
it is not presented as a chronological storyboard.

`selected-scenes.json` identifies all 57 selected assets: 25 newly generated
scenes and 32 unchanged reuses (including cover). `input-preservation.json`
maps all 37 R2 generation outputs, including studies and superseded candidates,
and their 34 distinct input hashes. Every output was compared with its original
image-tool file on TB4. All new artwork used the built-in image-generation tool;
exact prompts, reference identities and review notes are retained.

The final archive snapshot contains 261 media files, 450,295,404 bytes. The
matching scoped manifest, remote-verification receipt and restoration notes are
`assets/bath-magic-20261001-r2.json`, `assets/bath-magic-20261001-r2-receipt.json`
and `assets/bath-magic-20261001-r2.md`. All heavy conversion, contact-sheet work,
browser verification, staging and storage run on the mini SSD. Only source
text, recipes and provenance metadata are kept in the Air checkout.

The scene images are reviewed artistic interpretations, not a claim of exact
measured spatial reconstruction. This is a local review draft, not an official
chapter release, PDF edition or user approval of every illustration.

Creative material stays under the repository content notices. Preserving or
reusing an image is not a rights grant or a claim of copyright in AI-only output.
