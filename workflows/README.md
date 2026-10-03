# Studio workflows

Reusable working methods for carrying a creative request through to a visible result.

- [Character creation](character-creation.md): first prototype, inline review, coordinated views and a composite reference sheet.
- [Mr. PomPom example](examples/mr-pompom.md): an actual Studio run, its registered outputs, reference lineage and review attribution.

These are operating guides, not extra approval gates. The original request authorizes ordinary reversible draft work. Ask only about a decision that genuinely blocks progress; honor review checkpoints the user explicitly requested. A recorded plan review, design confirmation, artifact selection and publication authorization are different decisions.

The [Studio documentation](../tools/studio/README.md) describes the implementation. Normal UI and business workflow policy are editable; the transport, persistence and authority kernel remains separate. The current creative policy is [creative_policy.py](../tools/studio/business/creative_policy.py).

Generated media stays in external Studio storage. Example manifests contain registered asset IDs, full SHA-256 identities, relative data paths and provenance, not image binaries. Local asset endpoints work only in the matching Studio installation. They are not public download links; another installation must restore the corresponding bytes and registry before using them.

Code and creative content retain their respective terms in [LICENSE](../LICENSE), [CONTENT-LICENSE.md](../CONTENT-LICENSE.md) and [THIRD-PARTY-NOTICES.md](../THIRD-PARTY-NOTICES.md). A workflow example does not grant new rights or turn a candidate into approved artwork.
