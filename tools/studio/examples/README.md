# Real PinPin example catalog

Run from the repository root after restoring the external media packs:

```sh
python tools/studio/import_reference_catalog.py --data-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-data --dry-run
python tools/studio/import_reference_catalog.py --data-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-data
```

The importer refuses to replace a nonempty project unless `--replace` is explicitly supplied. The default media roots are the current Mini SSD packs. Remap them with `--root r17=/restored/r17`, `--root published=/restored/storyboard` and `--root worlds=/restored/story-worlds`.

- [Reference catalog](reference-catalog.json): logical keys, source roles, exact SHA256, approval status and remappable root paths.
- [Project seed](project-seed.json): original manuscript, character/place/prop records, published chapter links and editable 171-scene draft.
- [Exact original book](original-book.json) and [Russian manuscript](original-manuscript-ru.txt).
- [Published library catalog](published-chapters.json): ten entries, preserving edition labels and PDF links.
- [Editorial baseline](published-tempo-138.json): previous 138-scene annotation; current seed maps stable IDs and labels new proposals.
- [Production lessons](lessons.json), [prompt templates](prompt-templates.json), [panorama example](panorama-example.json).

The 33 new and 25 repaired R17 images are agent-reviewed candidates. User approval is pending. Retained approved images and published cover references keep their existing status. No asset is promoted to approved because it was merely imported.

See [Studio workflow](../../../docs/storyboard/production/STUDIO.md) for the short conversational cycle and recovery policy.

## Portable media restore

The [scoped media manifest](media-restore.json) reuses preserved content-addressed objects for every catalog input. Use tools/assets/hf_store.py pull with this manifest, an external --root destination and --profile archive. Then remap r17, published and worlds to the matching subfolders of that destination using importer --root options. Run --dry-run first; seed only an empty data directory. No binary artwork belongs in Git.
