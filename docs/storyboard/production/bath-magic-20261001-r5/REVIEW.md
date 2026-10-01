# R5 illustrated chapter — four days

Status: complete illustrated review draft, unpublished and awaiting user feedback.
The chapter has 84 scenes plus a cover, with English, Russian and Spanish text.
Day counts are 42 / 14 / 15 / 13. Every scene has selected artwork; there are no
unfinished image placeholders.

Reader: http://127.0.0.1:18795/storyboard/review/bath-magic-r5.html?lang=en
Use lang=ru or lang=es; add &view=storyboard for the overview. Four day links
navigate the chapter. The previous-draft arrow opens R4 preproduction.
Official chapter lists, the atlas, library and publication registry were not changed.

## Artwork and provenance

Thirteen inspected R3 scenes are reused byte-for-byte: 01–06, 08, 10, 14, 15,
25, 29 and 30. Seventy-one story illustrations and the cover are new selections.
selected-scenes.json records all 85 master and WebP identities. reuse.json and
reuse-records preserve actual origin generation, exact input bytes and earlier
lineage; reused artwork is never described as newly generated.

All 91 native image-tool outputs are retained, including production guides and
superseded candidates. All 61 distinct model input hashes map to preserved bytes
in input-preservation.json. Exact prompts, generation records, reference hashes,
visual reviews and ten validated geometry guides remain with the source.
New illustration and revisions used the built-in image-generation tool.
Native WebP conversion is recorded separately; contact sheets only arrange
existing illustrations and do not edit their artwork.

Final selected corrections include scene 43 v2, scene 44 v3, scene 47 v2,
scene 80 v2 and scene 83 v2. selected-scenes.json is authoritative for every
version. The final contact-sheet recipe is version 2: one overview and fourteen
six-panel sheets, with exact selected panel hashes. Earlier sheet originals
remain preserved.

## Verification and preservation

Complete reader checks passed at 1440px, 390px and 320px: all 84 scene images
and the cover decode, language controls and day navigation work, storyboard
links open the matching scene, and no placeholders, horizontal overflow or
JavaScript errors remain. Fresh mobile and desktop screenshots were inspected.
The storyboard tab now opens at the overview. browser-check/results.json
records the seven exact tested source/plan/media hashes, verified against the
canonical checkout.

All 212 prior R3/R4 source files and all 256 archived R3/R4 media files remain
unchanged. Thirteen reused assets, their origin bytes and all required origin
inputs passed independent identity checks.

Final scoped archival snapshot: 345 media files, 678,821,126 bytes. All 345 remote objects verified successfully.
assets/bath-magic-20261001-r5.json and its matching receipt record the proof;
independent verify-preservation.py --current passed. The independent verify-preservation.py --current check requires
complete coverage, current SHA-256 identities and remotely verified objects.
No original files are discarded.

## Mini workspace and reproducible commands

The canonical source checkout now lives on the mini SSD:
 /Volumes/TB4/mac-mini-storage/shared/pinpin-workspace/mr-pinpin-source
The former Air path is a compatibility symlink. Source edits, Python/image
processing, browser checks, caches, staging and archival work run on the mini.
The heavy pack remains:
 /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r5

workspace-migration.json records the separate workspace move. The existing
mini preview server on port 18796 is forwarded to Air port 18795.

Run registration on the mini via SSH, with direct local conversion:

```sh
ssh mini '/opt/homebrew/bin/python3 /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r5/register-generations.py --local --ids scene-59-v1'
```

Records contain the actual tool output, exact prompt and reference paths.
Registration snapshots each input before mutable WebP derivatives can change.
Immutable masters can serve as inputs directly. --preserve-only retains an
unselected candidate. The default SSH behavior remains for legacy compatibility;
--local avoids nested SSH when already running on the mini.

After new selections: preserve exact inputs, normalize selection metadata,
rebuild contact sheets, refresh media, run check-reader.cjs --complete, then
stage/archive and verify. Recover source text from the authoritative pack;
never overwrite a complete mini record with an empty or stale source file.
See the scoped assets Markdown file for media restore commands.

Creative material remains under the repository content notices. Preservation
grants no new rights or copyright claims in AI-only output. Camera guides are
artistic staging aids, not a claim of exact measured reconstruction. This is
a review draft, not an official publication or PDF edition.
