# R7 bath review preservation

Manifest: assets/bath-magic-20261001-r7-bath.json
Receipt: assets/bath-magic-20261001-r7-bath-receipt.json
Bucket: miguelemosreverte/mr-pinpin-archive

39 artifacts, 19,973,992 bytes. Three exact native tool outputs and three
distinct input hashes preserved with prompts, records, previous attempts and
browser evidence. The final push receipt requires verified:true, dry_run:false
and every entry verified:true/remote_verified:true. Independent
verify-preservation.py --current checks identity and complete coverage.

Restore from the mini source checkout:

```sh
python3 tools/assets/hf_store.py pull \
  --manifest assets/bath-magic-20261001-r7-bath.json \
  --root /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-r7-restored \
  --cache /Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache \
  --profile archive
```

Files restore under docs/storyboard/production/bath-magic-20261001-r7-bath/.
Copy the corresponding source text and review/bath-magic-r7-bath.{html,css,js}
into the matching docs/storyboard/ locations and serve docs/. Restore the
separate R6 source/media for the previous-review link. No publication occurs.

Reader: http://127.0.0.1:18795/storyboard/review/bath-magic-r7-bath.html?lang=ru
EN/RU/ES, original/new comparison, secondary rejected/study references and
expanded twelve-item discussion passed desktop/mobile checks. The story
discussion is not illustrated here; R8 production is separate.
Existing repository content notices apply; preservation grants no new rights.
