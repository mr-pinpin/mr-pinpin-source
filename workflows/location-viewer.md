# Existing location media in Studio Spaces

Use the existing Spaces surface to inspect registered panoramas and recorded orbit video. Selecting a configured orbit/stop entry requests spaces.location.get.v1; the actual viewer mounts inside existing media-workspace.js. No new stable URL enum or provider generation. Preserve all original records and hash-pinned media.

The viewer loads only media explicitly selected for inspection. One finger/pointer looks around; two-finger translation/scroll orbits the existing clip, pinch zooms. Re-grab and wrap continue across multiple turns. Enter the nearest AVAILABLE panorama stop using actualTimestampSeconds, never24uniform inferred angles. Stop07 source timestamp5.625s, FOV63.108676232412364degrees and camera yaw/pitch radians come from its actual selected/sourceAnchor records. Source-lock remains experimental; inferred scenery is not metric geometry. Exact decoded video source texture is retained when available; source-display fallback is labelled experimental. Review/byte verification does not establish seamless scenery or production approval.

Use this view in brief populates the durable composer only and preserves existing text/focus; never sends or authorizes. Historical current-selection metadata is unavailable; existing pinned-media inspection remains and reference/import/conversation actions disabled. Viewer cleanup releases gesture listeners/pointer captures, pending work, GL resources/video/images and Spaces-owned Blob URLs.

## Trusted local-cache contract

Host configuration PINPIN_MEDIA_CACHE_ROOT selects an existing private media cache. Fixed media-registry.json: schemaVersion1/files map, max128KiB/128entries, contained relative image/video paths, required MIME/bytes/SHA256. No arbitrary UI URL/path/cache selector. MIME extension and magic, SHA and size checked by media_file(); no symlinks. Legacy IDs preserve immutable hashes. Keep video as video; image attachment import rejects it. GET /api/media/files/:id and existing Range handler remain unchanged; opaque app uses existing read-asset bridge/local Blob URLs (40MiB bridge bound). No large archive fetch on catalog/query.

Trusted offline tools/studio/build_location_media.py --root <delivered-receipt-media-root> --out <external-small-config-dir> verifies delivered media/record identities and emits registry plus location-manifest.json. Sample schema/record binding under workflows/examples/location-viewer; samples reference external media, contain no copied binaries. Root installs generated config only during reviewed cutover, retaining original records/archives. Catalog metadata alone is not actual-byte verification.

Registry owner integration: append location_media.business_capabilities(), dispatch spaces.location.* to location_media.business_dispatch(). This is reloadable business; frozen source is rebuilt into a new immutable release only for media_library.py portability change. Never edit frozen artifacts or launch live as part of these tests.

## Repository-layout verification

python3 -B tools/studio/tests/test_location_media_library.py
python3 -B tools/studio/tests/test_location_metadata.py
node tools/studio/web/tests/location-viewer.test.mjs

Actual provider-disabled Studio browser fixture (existing Pillow/Playwright/Chrome, no installations):
python3 -B tools/studio/tests/run_spaces_browser_fixture.py --kernel-dir <new-verified-immutable-kernel> --media-root <delivered-media-with-receipt> --out-root <external-private-proof-dir> --node <existing-node>

Optional --prepare-only verifies real Store/business/workspace activation without opening HTTP/browser. Full test uses actual opaque shell host, Spaces source and named metadata operation; explicit Range206/video MIME, actual decode at desktop1440/mobile390, exact timestamp/FOV/experimental labels, composer preservation/restoration, no jobs/provider/approval/publication. Source captures must be coherent; registry must already include capability (fixture never silently patches disconnected production wiring). Reports/screenshots/caches stay in caller's external directory, never in source. Existing dependency roots may be supplied in PYTHONPATH; PLAYWRIGHT_MODULE and CHROME_EXECUTABLE are optional existing tool paths.
