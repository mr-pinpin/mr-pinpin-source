# R6 correction review preservation

Seven proposed corrections, awaiting user feedback; R5 remains unchanged.

Manifest: assets/bath-magic-20261001-r6-corrections.json
Receipt: assets/bath-magic-20261001-r6-corrections-receipt.json
Existing bucket: miguelemosreverte/mr-pinpin-archive

71 artifacts, 49,450,467 bytes: native originals/proposals, exact input snapshots,
prompts and generation records, comparison metadata and browser evidence.
Seven native tool outputs and eleven unique exact input hashes were verified.
All 459 earlier R5 source files and 345 archived files remain unchanged.
The complete reader passed 1440/390/320 widths, fourteen images and EN/RU/ES.

The version 1 push receipt requires verified: true, dry_run: false and every entry
verified: true, remote_verified: true. The independent current-file verifier also
checks path, role, size, SHA-256, object key and complete snapshot coverage.

## Restore on the mini

```sh
python3 tools/assets/hf_store.py pull \
  --manifest assets/bath-magic-20261001-r6-corrections.json \
  --root /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-r6-restored \
  --cache /Volumes/TB4/mac-mini-storage/shared/pinpin-asset-cache \
  --profile archive
```

Files restore beneath docs/storyboard/production/bath-magic-20261001-r6-corrections/.
Copy the corresponding production source text and
docs/storyboard/review/bath-magic-r6-corrections.{html,css,js} to matching paths,
then serve docs/. Restore the separate R5 source/media for the previous-chapter
link. Restoration verifies content identities and does not publish the report.

Reader: http://127.0.0.1:18795/storyboard/review/bath-magic-r6-corrections.html?lang=ru
Use lang=en or lang=es. All processing, screenshots and archives stay on mini.
The twelve-mishaps proposal is unrendered discussion, separate from corrections.

Creative material remains under existing repository notices; preservation adds
no rights or copyright claims in AI-only output.
