# Runtime variant selection — 2026-10-12

The live release cc9fb27f8fb5e3e33b3b625e58852f3c24ae12b6b4e5de7ac3224e5c08e8e021
contains 948,137,769 bytes: 264 PNGs (594,944,406 bytes), 566 WebPs
(334,288,150 bytes), plus video/code/data. Forty-one same-basename PNG/WebP
pairs include 76,290,222 native PNG bytes. Not every PNG can be omitted: original
book imagery, legacy chapter images and real fallback/metadata dependencies remain.

The family atlas consumer in atlas-family.js explicitly chooses runtimeSrc before
src. Both source and runtime files were promoted by a blanket registry scan and
explicit policy entries, even where no deployed consumer needed the source PNG.
The audited family-production and family-production-blinks seeds now opt into
preferRuntimeSrc. Only src entries with a nonempty runtimeSrc are skipped; other
fields and ordinary chapter manifests retain their original behavior. The Pages
reference checker applies this same verified contract only to those two registries.
Missing runtime variants still fail; a descriptor without runtimeSrc still needs
its src. Native provenance remains intact in the registries.

Existing WebP bytes are unchanged. Source PNGs are retained in working files and
Git history, and verified against their immutable HF backups before any untracking.
No original book or previously published story image was regenerated, resized,
compressed or shortened. The new Scooby chapter uses full native-size WebP reader
derivatives. The build including it passes at 923,201,365 bytes before final PDF
catalog/provenance additions, under the unchanged 950,000,000-byte cap.

Regression fixtures cover opt-in variant preference, ordinary manifest behavior,
missing runtime files, src-only fallback, preservation of provenance, exclusion of
unused native bytes, and byte-identical runtime copies. Existing asset tests pass.
A browser trace is retained in the Scooby production pack to check actual atlas
variant requests; publication evidence is recorded in the release report.
