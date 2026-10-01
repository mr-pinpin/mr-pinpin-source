# R4 preproduction study preservation

Verified on 2026-10-01. This preserves the new duck character study and its exact
input, not an illustrated 80-scene chapter or an official publication.

- Manifest: `assets/bath-magic-20261001-r4.json`.
- Receipt: `assets/bath-magic-20261001-r4-receipt.json`.
- Existing bucket: `miguelemosreverte/mr-pinpin-archive`.
- **4 media files, 3,844,835 bytes.**
- Both native image-tool outputs are retained; version 2 is selected and version
  1 is an unselected candidate. The selected WebP and exact R3 scene-28 style
  input complete the scope. No old chapter media pack was cloned.
- Every receipt entry matches its path, archive role, size, SHA-256 and content
  object key; all entries are verified and remotely verified. The receipt is
  version 1, action `push`, `verified: true`, `dry_run: false`.
- Independent `verify-preservation.py --current` passed exact current-file
  identities and complete coverage of the study/input scope.

`input-preservation.json` maps two generation records and two unique input
hashes. Both native outputs were compared with their actual tool files on TB4.
Exact prompts, references and review notes remain with the source. The new art
used the built-in image-generation tool. Native-size WebP conversion is recorded
separately; it does not replace the originals.

The reader contains 80 proposed trilingual scenes across four days. Prior R3
images are clearly labelled reference candidates, not newly generated or approved
R4 illustrations. R3 remains unchanged: 187 source files and 252 media files.
The geometry-only `CONTINUITY.md` report is distinct from the new duck study.

Focused checks passed at 1440px, 390px and 320px: all scenes, day navigation,
EN/RU/ES controls, old-reference accordions, selected-study decoding and no
horizontal overflow or browser errors. Tested hashes are recorded in
`browser-check/results.json`. Reproducible screenshots remain on TB4 and are
not part of this deliberately small study/input archive.

## Restore

```sh
python3 tools/assets/hf_store.py pull \
  --manifest assets/bath-magic-20261001-r4.json \
  --root /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-r4-restored \
  --cache /Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache \
  --profile archive
```

Media restore below `docs/storyboard/production/bath-magic-20261001-r4/`.
Copy the matching source pack text and `docs/storyboard/review/bath-magic-r4.*`
to matching paths, then serve the restored `docs` directory. Restore R3 separately
using its existing manifest to view the optional older-art references and use
the previous-draft link. The R4 text and study remain readable without those
optional images. Restoration verifies identities and refuses conflicting files.

Local reader:
`http://127.0.0.1:18795/storyboard/review/bath-magic-r4.html?lang=en`.
Use `lang=ru` or `lang=es`; four day links navigate the story proposal.

No official reader registry, atlas, library, canonical geometry or publication
was changed. Creative material remains under the repository content notices;
preservation grants no new rights or copyright claims in AI-only output.
