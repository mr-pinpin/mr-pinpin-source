# Bath-Time Flood — review reader

Status: complete illustrated draft for review, not user-approved or published.
All 36 scenes and the cover are selected, with English, Russian and Spanish text.
`selected-scenes.json` records the exact versions and hashes; older candidates
remain preserved. The full overview and six readable contact sheets use the final
selected images (contact-sheet masters v2).

The isolated reader is `docs/storyboard/review/bath-magic.html`. It reads
`story-plan.json` and `media.json` from this pack, and supports English, Russian,
and Spanish through the same circular flag treatment as the existing reader.
The reading view follows all 36 scenes; the storyboard view separates the early
six-panel concept from the final numbered contact sheets and clickable scene
grid. Technical plans, reference images, prompts and provenance stay collapsed.

Preview on the Air:

`http://127.0.0.1:18795/storyboard/review/bath-magic.html?lang=en`

Russian: replace `lang=en` with `lang=ru`. Add `&view=storyboard` for the visual
overview. No official story registry, home screen, atlas or publication was changed.

## Storage and generation handoff

Heavy files are on the mini at
`/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001`.

- `masters/`: unchanged image-model outputs and explicitly labelled contact-sheet composites.
- `web/`: native-size WebP review derivatives, quality 94, method 6.
- `references/`: existing book artwork and geometry underlay; distinct from generated art.
- `geometry/`: camera/room study material supplied by the geometry lane.
- `browser-check/`: actual browser screenshots and machine-readable results.
- `derivatives.json`: master and derivative SHA-256, byte size, dimensions and conversion recipe.
- `media.json`: only assets that exist, with hashes and review status.

The source checkout keeps recipes, prompts, story text, provenance, reports and
scoped preservation metadata. Large media stay on TB4. The preview's production
path is a review-only symlink into the pack, never a Pages release artifact.

Accept a generated image on the mini:

```sh
PACK=/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001
"$PACK/.venv/bin/python" "$PACK/accept-asset.py" \
  --master masters/scene-01-v1.png --slug scene-01 \
  --prompt prompts/scene-01-v1.txt
```

The command preserves the original, converts only file encoding at unchanged
dimensions, and updates the media/provenance indexes under a file lock. It does
not synthesize, repaint, crop or retouch artwork. The isolated Python environment
uses Pillow 12.3.0. `contact-sheets.py` arranges the existing images into a single
36-frame overview and six sheets of six frames; the numbers refer to the story
plan. These are layout derivatives, not separately generated illustrations.

## Preview and verification

The mini serves `preview/docs` on localhost port 18796 using `serve-preview.py`.
The Air uses an SSH forward from port 18795. To restart a stopped server:

```sh
PACK=/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001
nohup /opt/homebrew/bin/python3 "$PACK/serve-preview.py" \
  --directory "$PACK/preview/docs" --port 18796 \
  > "$PACK/preview/server.log" 2>&1 < /dev/null &
```

On the Air, if the tunnel is absent:

```sh
ssh -fN -o ExitOnForwardFailure=yes -L 18795:127.0.0.1:18796 mini
```

`check-reader.cjs` runs installed Chrome through Playwright on the mini at 1440px,
390px and 320px widths. It checks all 36 text scenes, language switching, overview-to-
scene navigation, lack of horizontal overflow, browser errors, and successful
decoding of every available illustration. Pass `--complete` to require all 36
illustrations plus cover, with no unfinished-image placeholders. The final complete-image run passed at all three widths with no browser errors
or broken/unfinished images. Cover and first scene are eagerly loaded, and
screenshots wait for their actual decoding; all remaining scenes stay lazy.
`browser-check/results.json` records the tested source/manifest hashes. The final
390px screenshot was also inspected visually and shows the cover and first
illustration fully painted. Scene, storyboard and reference URLs use content
hashes to avoid stale artwork after revision.

## Preservation

`prepare-archive.py` snapshots regular media from masters, web, references,
geometry and browser-check into a scoped regular-file stage and makes a version-1
content-addressed manifest. The standard repository `tools/assets/hf_store.py`
push/verify workflow supplies the independent remote-verification receipt.
No media is deleted or untracked by these helpers, and global asset manifests or
policies are not modified. The final scoped manifest/receipt are recorded under
`assets/bath-magic-20261001*`. `verify-preservation.py --current` checks every
manifest identity, remote proof and present media file. Exact counts and receipt
results are recorded in `assets/bath-magic-20261001.md`.

Creative material remains under the repository's content terms; generating,
converting, or preserving an image does not establish third-party rights or
relicense it under the software MIT grant.

## Provenance and review limits

`input-preservation.json` maps 55 generated originals and their 37 distinct input
image hashes to preserved bytes. Input references may point to prior book art,
geometry guides, or another generated master; matching SHA-256 establishes which
exact bytes were used, without relying on transient absolute paths. Prompt files,
inline prompts and generation records are retained separately from artwork.
The nine geometry guides passed their location-CLI validations.

The illustrations were reviewed for cast, actions, flooding progression and major
room/object continuity; they remain artistic approximations of the geometry guides,
not measured reconstructions. This is a complete proposal for Miguel to review,
not a claim of perfect spatial consistency or official publication. No chapter
PDF, coloring pages or production release is implied by this draft.

Selected revisions beyond v1: scenes 02 v2, 03 v3, 05–08 v2, 13 v2, 25–26 v2,
29–30 v2, 32 v2, 34 v3, and 35–36 v2. All other scenes and the cover use v1.
After browser verification, production-status/selection fields were populated
consistently for all 36 scenes and cover; captions, order, and image URLs were
unchanged. The browser result records this metadata-only hash update.
