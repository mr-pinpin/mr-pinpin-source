# Final pilot reader/PDF delivery, unpublished

Use the saved completed chapter and its exact version/hash. Do not explore implementation or invoke generation. The existing verified runtime CLI and local renderer compose provided assets only. Output is a reader/PDF derivative, never publication or approval.

From configured Studio working directory:
```sh
tools/studio-python tools/studio-delivery/cli.py \
 --chapter CHAPTER --version N --sha256 EXACT_SAVED_VERSION_SHA \
 --cover COVER_ASSET_ID --miniature MINIATURE_ASSET_ID \
 --coloring LINE_ART_ID1 --coloring LINE_ART_ID2 --coloring LINE_ART_ID3 \
 --out EXTERNAL_NEW_DIRECTORY --render \
 --node EXISTING_NODE_PATH --playwright-module EXISTING_PLAYWRIGHT_MODULE \
 --pdfkit-verifier tools/studio-delivery/verify-pdf.jxa.js
```

PINPIN_STUDIO_DATA and PINPIN_STUDIO_RUNTIME must identify the existing deployment; optional explicit global --data-dir/--runtime-dir are supported. tools/studio-python uses the approved runpy launcher (owner w5 handoff). CLI opens verified active business read-only, selects one exact immutable chapter version, exports only selected registry metadata and verifies original image bytes. It never saves state, registers an artifact, activates business, approves, restores remotely or publishes. Use existing Node/Playwright/Chrome; do not install/download another browser. --render absent builds readers only and reports pdfBuilt:false. The PDFKit verifier is existing macOS system tooling; otherwise renderer uses existing pdfinfo/pdftotext.

Required: actual title and captions in both languages, every panel's saved imageAssetId, registered cover/title art, a registered miniature/contact-sheet asset, three DISTINCT provided line-art assets with provenance.kind line-art/coloring-page/provided-line-art. Catalog/provenance labels cannot prove visual suitability; inspect the actual three coloring pages and miniature. No automatic conversion, cropping, translated story invention or reference fallback. English-only native drafts require an explicit supplied translation file. Pass --translations FILE --translations-sha256 EXACT_FILE_SHA; JSON is {sourceVersionSHA256:EXACT, title:{en:SOURCE_TITLE,ru:SUPPLIED_RUSSIAN}, captions:{PANEL_ID:{en:EXACT_SOURCE_CAPTION,ru:SUPPLIED_RUSSIAN},...}}. Every exact panel is required and English words must match. The derivative records localizationSHA256 while preserving original version identity. No model translation call is made.

Default completed delivery rejects missing title/translation/image/miniature/coloring pages. --allow-incomplete is explicitly a draft: missingArtwork remains visible, complete:false. Never describe reserved boxes as actual coloring pages. Source native reference fingerprint is verified before composition. Missing panel image IDs remain missing: the CLI does not infer artwork from unrelated reference IDs, current mutable scenes, or a job from another version. If approved production outputs are not bound into the saved draft, report that integration gap to the chapter owner; never silently map them.

Outputs en/preview.html, ru/preview.html (self-contained embedded exact native art), chapter.pdf per language after renderer verification, delivery-manifest.json per language with exact source version, raw record hash, localization identity, ordered artwork SHA/size/provenance, missing list, originalAssetsModified:false, generationCalls:0 and unpublished:true. Browser checks image decode, font readiness, layout/overflow/page count; PDFKit or pdfinfo/pdftotext checks actual PDF page count/selectable Unicode text. Original source art stays unchanged. Requested output need not be reproducible byte-for-byte across browser/font/time; each actual PDF receipt binds its exact bytes.

No directory overwrite. Failed/partial outputs remain diagnosis evidence and are never called completed; rerun to a fresh directory after correcting inputs. Source/private state and media must not be copied to public Git. No delivery catalog/serving route mutation is performed. Existing draft.pdf.chunk capability consumes registered deliveries/catalog.json entries and verifies actual PDF bytes; its integration/registration owner must separately attach actual artifacts if app download is required. Do not claim a clickable Studio download from a local external artifact alone.
