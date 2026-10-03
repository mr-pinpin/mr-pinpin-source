# Studio workflows

Reusable working methods for carrying a creative request through to a visible result.

- [Character creation](character-creation.md): first prototype, inline review, coordinated views, a composite reference sheet and a required separate cast-interaction page.
- [Mr. PomPom example](examples/mr-pompom.md): an actual Studio run, its registered outputs, reference lineage and review attribution.

- [Character timing observations](examples/character-latency-20261003.md): measured PomPom, Mama and Papa runs with scope and comparison limits.

These are operating guides, not extra approval gates. The original request authorizes ordinary reversible draft work. Ask only about a decision that genuinely blocks progress; honor review checkpoints the user explicitly requested. A recorded plan review, design confirmation, artifact selection and publication authorization are different decisions.

The [Studio documentation](../tools/studio/README.md) describes the implementation. Normal UI and business workflow policy are editable; the transport, persistence and authority kernel remains separate. The current creative policy is [creative_policy.py](../tools/studio/business/creative_policy.py).

Generated media stays in external Studio storage. Example manifests contain registered asset IDs, full SHA-256 identities, relative data paths and provenance, not image binaries. Local asset endpoints work only in the matching Studio installation. They are not public download links; another installation must restore the corresponding bytes and registry before using them.

Code and creative content retain their respective terms in [LICENSE](../LICENSE), [CONTENT-LICENSE.md](../CONTENT-LICENSE.md) and [THIRD-PARTY-NOTICES.md](../THIRD-PARTY-NOTICES.md). A workflow example does not grant new rights or turn a candidate into approved artwork.

## Durable cast production

- [Cast run contract](cast-run.md): resume the first missing verified stage without another authorization request.
- [Character folders](characters/): canonical names/aliases, age and life-stage evidence, source bibliography, design/contact constraints and package decisions. Each folder has a README.md and evidence.json.
- [Cast manifest](cast-run.json): durable queue and required solo/interactions stages.

The application loads its canonical Markdown and manifest from persistent external Studio data on fresh turns. Source copies are mechanical checkpoints. Registered images and exact prompts/native hashes/stage receipts stay in that data root under reports/character-packages/<entity>.json, and survive closing a session. A status flag alone cannot complete a package: distinct stage receipts must match registered assets and actual image bytes. Solo-only packages resume interactions without duplicating successful solo art. Read selected IDs/hashes programmatically from receipts; never retype opaque identities from memory. Historical review does not import mutable live cast state.

Produced drafts, delegated working-reference acceptance, personal review, artifact selection and publication remain distinct. Notetaker is unavailable; durable Markdown notes are the labeled fallback. Source checkpoints contain metadata and documentation, never generated image binaries or invented approval.
