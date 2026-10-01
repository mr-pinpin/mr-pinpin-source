# R8 Herculean chapter preservation

Manifest: assets/bath-magic-20261001-r8-herculean.json
Receipt: assets/bath-magic-20261001-r8-herculean-receipt.json
Bucket: miguelemosreverte/mr-pinpin-archive

923 artifacts, 1,024,438,942 bytes. Retains 100 exact native outputs with prompts and 75 distinct input identities, 48 selected unchanged reuse origins, one retired reuse candidate, final WebPs, preproduction, sheets and browser evidence. The 127 selected illustrations are 48 unchanged reuses plus79 newly generated selections including cover.

Run on mini from the canonical source checkout:

```sh
python3 tools/assets/hf_store.py pull \
  --manifest assets/bath-magic-20261001-r8-herculean.json \
  --root /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-r8-restored \
  --cache /Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache \
  --profile archive
```

Restore path: docs/storyboard/production/bath-magic-20261001-r8-herculean/. Copy corresponding committed source text and review/bath-magic-r8-herculean.{html,css,js} into matching docs/storyboard/ locations and serve docs/. The previous-draft link requires the separate R5 reader/assets; all R8 reading assets and exact image inputs are included here.

The final receipt requires verified:true, dry_run:false and every entry verified:true/remote_verified:true. verify-preservation.py --current independently checks byte identities and coverage. verify-reuse.py works on restored copies; --origins additionally checks original packs when present.

Reader: http://127.0.0.1:18795/storyboard/review/bath-magic-r8-herculean.html?lang=en

Complete local draft; unpublished. Existing content notices apply; preservation grants no new rights.

Remote proof uses verify-archive-batched.py: batched metadata, fresh downloads, SHA-256/size checks, then unchanged remote Xet identities. The standard verification receipt is written only after all checks pass. The earlier upload succeeded; its per-file verification was stopped because provider metadata calls were rate-limited.
