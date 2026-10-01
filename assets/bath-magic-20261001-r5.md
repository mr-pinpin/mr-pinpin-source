# Bath chapter R5 preservation

Complete local review draft, awaiting user feedback; not an official release.

- Manifest: assets/bath-magic-20261001-r5.json.
- Receipt: assets/bath-magic-20261001-r5-receipt.json.
- Existing archive bucket: miguelemosreverte/mr-pinpin-archive.
- 345 media files, 678,821,126 bytes.
- Receipt version 1: push, verified true, dry_run false. Every entry is
  verified and remote_verified; paths, roles, sizes, hashes and object keys
  match the manifest. Independent verify-preservation.py --current passed.

There are 84 scenes over four days and a cover, with EN/RU/ES text: thirteen
unchanged R3 illustrations, seventy-one new scene selections and a new cover.
All 91 native tool outputs and 61 distinct exact model inputs remain preserved,
including guides and superseded candidates. Exact prompts and generation/reuse
records live in the source. Only selected reused masters and required provenance
inputs were copied; reuse is not presented as new generation.

selected-scenes.json identifies all 85 final selections. Version 2 contact
sheets consist of the overview plus fourteen six-panel sheets. Complete reader
checks passed at 1440, 390 and 320 pixels, with every chapter image decoded,
three languages, four day links and storyboard navigation. Fresh screenshots
and exact tested identities are in browser-check/results.json.
All 212 earlier R3/R4 source files and 256 archived media remain unchanged.

The source checkout and all heavy work now live on the mini SSD. The previous
Air checkout path is a compatibility symlink. Global asset catalogs, policies
and official publication registries are unchanged.

## Restore

Run from the canonical source checkout on the mini:

```sh
python3 tools/assets/hf_store.py pull \
  --manifest assets/bath-magic-20261001-r5.json \
  --root /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-r5-restored \
  --cache /Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache \
  --profile archive
```

Media restore beneath docs/storyboard/production/bath-magic-20261001-r5/.
Copy corresponding source pack text and
docs/storyboard/review/bath-magic-r5.{html,css,js} to matching locations, then
serve the restored docs directory. Restore separate R4 source/media to use
the previous-draft link. Restore verifies identities and refuses conflicting
files; it does not publish the chapter.

Reader: http://127.0.0.1:18795/storyboard/review/bath-magic-r5.html?lang=en
Use lang=ru or lang=es, or &view=storyboard. Mini serves on18796, forwarded to
Air18795. The production REVIEW.md documents commands, provenance and limits.

Creative material remains under repository content notices. Preservation and
reuse grant no additional rights or copyright claims in AI-only output.
