# Unpublished Studio chapter delivery

Version-bound deterministic reader and PDF exporter for a saved chapter, using provided registered images and captions. It performs no AI generation, paid API calls, approval, publication or app mutation. It reuses the layout/verification method in `scripts/export-chapter-pdfs.cjs` and its recorded PDF workflow without that exporter's hardcoded nine-chapter catalog. Native image bytes are retained unchanged (no resize/recompression/crop); output hashes describe newly composed artifacts, never replacements for originals.

## Input contract

`prepare.py` takes a pinned actual Store snapshot (`project.chapters`) or saved chapter object (`id`, `studioDraft.versions`), selecting the requested historical version. It also accepts a detached version record only when chapterId (or spec.chapterId) explicitly binds its chapter. Maximum raw input8MiB; extract the bounded saved chapter/record if the complete Store is larger. Spec contains title, ordered panels (up to512), optional coverAssetId. A panel has id, optional imageAssetId, and caption or multilingual captions. A required externally known SHA256 pins the entire saved-record file before use; requested chapter/version must match. Actual saved records with referenceBindings/referenceHash verify the app's precise availability-independent reference hash and version fingerprint over spec+referenceHash. Detached generic fixtures without these fields retain declared identity without claiming native binding verification. Raw record hash independently pins the supplied file. Manifest sourceVersionSHA256 is the saved version fingerprint, not merely a spec-only hash. Registry is an asset array or existing Store snapshot with assets; each selected image supplies id, storagePath, mime, bytes, sha256 and provenance. Asset root is explicit, paths stay contained after symlink resolution, image hash/size verified. Supported art: PNG/JPEG/WebP, up to40MiB each, aggregate embedded budget256MiB default. All selected bytes count toward budget; no silent omission.

For multilingual captions/title use `{en: ..., ru: ...}`. Missing caption language is explicit, never silently substituted. Plain strings are used verbatim in the operator-selected language; the exporter does not translate. `--cover-asset` explicitly selects a registered title reference; no first-reference fallback. Up to three `--coloring-asset` IDs select existing registered line art with provenance.kind line-art, coloring-page or provided-line-art. No conversion of story art into invented coloring pages. Exactly three coloring slots always appear; absent bytes/art stay explicitly missing. This is a draft reader even if every selected image exists; it does not imply a real completed illustrated chapter or production approval.

## Run

Use TB4 draft scratch outside source for actual outputs. `--out` must be empty/new and cannot be inside this tool's source directory. Do not commit HTML media/PDF binaries. Example paths are placeholders:

```sh
python3 tools/studio-delivery/prepare.py \
  --record /TB4/data/reports/chapter-drafts/CHAPTER/vN.json \
  --record-sha256 KNOWN_RECORD_SHA --chapter CHAPTER --version N \
  --registry /TB4/scratch/assets-snapshot.json --asset-root /TB4/data \
  --language ru --out /TB4/scratch/delivery-CHAPTER-vN-ru

PLAYWRIGHT_MODULE=/existing/node_modules/playwright \
node tools/studio-delivery/render.cjs --dir /TB4/scratch/delivery-CHAPTER-vN-ru
```

Render uses existing Chrome/Playwright, not a new downloaded dependency. It checks font readiness, every image's natural dimensions/load, expected DOM page count, overflow and captions, then PDF page count and selectable Unicode text. Default verification uses existing pdfinfo/pdftotext; provide explicit paths if needed. On macOS with those tools absent, existing system PDFKit can verify without a compiler/package:

```sh
node tools/studio-delivery/render.cjs --dir /TB4/scratch/delivery-CHAPTER-vN-ru \
  --playwright-module /existing/node_modules/playwright \
  --pdfkit-verifier tools/studio-delivery/verify-pdf.jxa.js
```

Outputs: self-contained preview.html; chapter.pdf after rendering; delivery-manifest.json with pinned source version/hash, language, ordered selected image identities/sanitized provenance, missing-art list, three coloring slots, HTML/PDF exact byte sizes/hashes and verification fields. PDF byte identity can vary with browser/font/time; composition/input selection is deterministic. No exact PDF reproducibility claim beyond each actual receipt. A failed PDF verification is not a successful delivery even if partial PDF bytes exist; use a fresh output directory after resolving failure.

## Tests and current integration boundary

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/studio-delivery/test_delivery.py
node --check tools/studio-delivery/render.cjs
```

Fixtures are synthetic tiny PNG data; no real art/story is generated. `browser-fixture-proof.json` records actual EN/RU5-page PDFs, images loaded, layout and selectable text, with exact byte hashes; final preparer emits identical HTML to those tested inputs. Nineteen isolated tests cover missing/corrupt/wrong art, source pinning, version, path/symlink escape, no overwrite, coloring semantics, escaping, language and byte budget. These do not prove a real illustrated chapter or a Studio download.

Existing `/api/assets` registration is image-only: Store.prepare_asset allows PNG/JPEG/WebP. `/api/assets/<id>` serves registered image mime/path/SHA. Business routes return JSON. A PDF cannot be smuggled into image registration. Existing media-file allowlist must be independently checked before claiming that route supports these exports. No arbitrary file endpoint, allowlist change, server restart or serving integration is included. The coordinator/app must own any later documented artifact registration integration and truthful clickable Studio download. Actual saved chapter schema and fingerprint/binding algorithms were read and independently fixture-verified; schema-adapter-proof.json contains provenance. Final boundaries are verified in INTEGRATION.md: fixed bridge excludes these capabilities. New helper modules are ready, but actual Studio downloads require reviewed versioned bridge extension/canary and app integration; no live support claimed.

## Bounded draft download helpers

See [INTEGRATION.md](INTEGRATION.md) for exact new module mappings and proposed named capability. Portable transport tests after source copy:

```sh
python3 tools/studio-delivery/test_pdf_delivery.py
node tools/studio-delivery/test_pdf_download.mjs
```

The UI module intentionally uses `/api/business/draft.pdf.chunk.v1`, not a disguised legacy route. Current stable bridge rejects it. Actual draft-download acceptance is pending app integration/canary; fixture proof remains labeled.
