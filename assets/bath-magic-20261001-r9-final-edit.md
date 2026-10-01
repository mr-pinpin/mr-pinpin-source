# R9 final editorial draft — new comic-sheet preservation

Manifest: assets/bath-magic-20261001-r9-final-edit.json
Receipt: assets/bath-magic-20261001-r9-final-edit-receipt.json
Bucket: miguelemosreverte/mr-pinpin-archive

23 new artifacts,181,915,005 bytes:10 WebP comic sheets,10 native PNG sheet
masters, board manifest, board QA and workflow notes. Layout only; no artwork
regeneration. Five sheets per language, Russian and English.

The full126-scene reader plus cover reuses the verified R8 archive by reference.
No R8 native image is copied or rearchived. Restore both scoped manifests:

```sh
python3 tools/assets/hf_store.py pull --manifest assets/bath-magic-20261001-r8-herculean.json --root /Volumes/TB4/mac-mini-storage/shared/pinpin-r9-restored --cache /Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache --profile archive
python3 tools/assets/hf_store.py pull --manifest assets/bath-magic-20261001-r9-final-edit.json --root /Volumes/TB4/mac-mini-storage/shared/pinpin-r9-restored --cache /Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache --profile archive
```

Copy corresponding committed source text and review/bath-magic-r9-final-edit
HTML/CSS/JS into the restored docs/storyboard hierarchy; serve docs/.
The earlier-reader and tempo links require their matching source routes.
upstream-assets.json records unchanged R8 metadata/image identities.
verify-preservation.py checks every derivative receipt entry and current bytes.

Complete local editorial draft, unpublished. Existing content notices apply;
preservation does not grant new rights.
