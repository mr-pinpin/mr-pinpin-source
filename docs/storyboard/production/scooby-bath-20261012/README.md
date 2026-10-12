# Scooby Gets a Bath

A new original standalone adventure requested for publication on 2026-10-12.
Sixteen illustrated story scenes plus localized title covers; EN/RU/ES. Papa and
PinPin help the reluctant Scooby settle into warm water, brush his coat with dog
shampoo, clean his paws, rinse him, survive his enormous shake, brush out loose
hair, and welcome him to a soft sleeping place inside the house.

The user authorized creating and publishing the chapter. Artwork selection is
Codex visual review under that instruction; no individual user image approvals
are claimed. Existing story text, artwork, original book and PDFs are unchanged.
Creative content is outside the software MIT grant; see root notices. No rights
are claimed in unprotectable AI output or public-domain material.

## Art and geography

The built-in `image_gen__imagegen` tool produced 22 successful outputs: 20 selected
native assets and two rejected first indoor illustrations. The selected sources
are 1536×1024 story images, 1024×1536 covers and a separately composed text-free
miniature. `media.json` records native/reader hashes and the WebP quality-86 recipe;
no selected reader image is resized or cropped. Native PNGs remain preserved in
`native/` with verified archive restoration keys in the asset catalog.

Individual `*-prompt.txt` files contain the exact selected prompts. Saved jobs in
`jobs/` pin the reusable house model. Outdoor close-ups contain no house geometry;
the portable garden dog bath is a temporary story prop. The final indoor scenes
use the current measured house and new Blender 4.5.14 renders. The first indoor
outputs copied historic style-reference furniture/openings and were rejected.
Targeted built-in edits corrected the backgrounds before selection. Doorway shot
15 is a clean-paw close-up, not a claim of validated full-dog passage through the
opening. Scene 16 preserves the current floor/table/stool/partial-door camera.

The mini/Mac was unreachable during this run, so rendering and release work use
external storage on the Linux VPS. Heavy masters and browser tools are outside Git.
Native artwork copied into the production pack is archived through the catalog and
verified synchronization workflow, with working files retained.

`media-web-v2.json` records an unselected smaller-image experiment. The final
chapter uses the full-size variants. The actual size issue was duplicate native
atlas packaging, not a reason to lower the new chapter's image dimensions.

## Reader and print

Runtime model: `docs/storyboard/stories/scooby-bath.json`.
Reader route: `/storyboard/?story=scooby-bath&lang=en` (also RU/ES).
`reader-proof.json` records all 17 pages, image decoding, language and horizontal
layout checks at 390px and 1440px. `scripts/scooby-bath.test.cjs` prevents partial,
reordered or untranslated models from being selected as complete.

`export-pdfs.cjs` creates three new 17-page PDFs from the untouched full-size
masters using external JPEG print derivatives (quality 92, no resizing/cropping).
The PDFs have selectable narration and are preserved at content-addressed public
HF keys. `pdf/` contains input/export and verified upload records; the library
catalog links those immutable files. Existing PDF entries and bytes are retained.

Publication completes only after the verified release tools select a new official
release and its Pages deployment/public chapter checks pass. The publication
record is added separately after deployment.
