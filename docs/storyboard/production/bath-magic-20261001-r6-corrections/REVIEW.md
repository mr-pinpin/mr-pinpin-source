# R6 correction candidates

Seven before/after proposals are ready for user review. The R5 chapter remains
unchanged. This report does not publish or select these proposals into the chapter.

Reader: http://127.0.0.1:18795/storyboard/review/bath-magic-r6-corrections.html?lang=ru
English and Spanish use lang=en and lang=es. Desktop uses one side-by-side
comparison per row; phones stack original and proposal within each numbered row.

## Proposed changes

- 01, 42, 43 and 71: the whole family shares the broad bed, with distinct bodies
  and appropriate morning/bedtime lighting. Only scene 01 has a proposed caption
  revision, shown beneath the corresponding original/proposed image.
- 30: restore the continuous wooden enclosure and visible submerged floor.
  The split-level composition and family remain. Scene 29 already shows an
  enclosed underwater interior and is retained.
- 69 and 83: restore the ordinary round wooden table. The duck basin sits on a
  separate low stool. Adjacent close-ups 70 and 84 were inspected and retained.

Each row links to the exact image prompt and generation record. Further lane
notes and references are collapsed below the comparisons. The separate
twelve-mishaps-proposal.json is a story discussion only, labelled “not rendered”;
no narrative expansion or corresponding illustration generation was performed.

## Evidence and preservation

The seven native image-generation outputs match their original tool files.
Eleven distinct reference hashes map to exact preserved input bytes. Lane
records and prompts remain unchanged; references/provenance-audit.json adds an
independent record/prompt/output/input identity check without rewriting them.
Before-image inputs match the actual R5 selected master or WebP. Existing WebPs
are copied unchanged; new native PNGs are converted to WebP at quality 94/method 6,
without resizing or artwork edits. build-comparisons.py records that operation.

Focused browser checks passed at 1440, 390 and 320 pixels: seven complete pairs,
fourteen decoded images, EN/RU/ES controls, numbered navigation, all 37 row/general
provenance links and no horizontal overflow or JavaScript errors. Fresh desktop
and mobile screenshots were visually inspected. browser-check/results.json
records exact tested identities.

All 459 R5 source files and all 345 archived R5 files remain unchanged.
r5-preservation-check.json records that proof. R5 selection, story text, reader,
official atlas/library and publication registries were not edited.

The scoped archive contains 71 files (49,450,467 bytes), including native outputs,
originals, input snapshots, exact prompt/record text, review selection metadata
and browser evidence. The matching assets manifest/receipt records remote proof;
All 71 remote objects verified successfully; verify-preservation.py --current
passed exact current identities and complete coverage.

## Location and reproduction

Everything was built through SSH on the mini SSD. Canonical source:
 /Volumes/TB4/mac-mini-storage/shared/pinpin-workspace/mr-pinpin-source
Heavy correction pack:
 /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r6-corrections

The mini preview server 18796 is forwarded to Air 18795. Its new production
symlink serves this isolated pack; previous readers remain available.
Run build-comparisons.py --complete with the pack's Pillow environment,
verify-provenance.py, then check-report.cjs. Only rebuild after explicitly
changing the frozen lane manifests. The scoped assets Markdown file explains
restoration. No commit, source push or official publication was performed by
this reader/archive lane.

Creative material retains the repository content notices. Internal visual
review is not user approval. Geometry corrections are artistic edits, not a
claim of exact measured optical simulation.
