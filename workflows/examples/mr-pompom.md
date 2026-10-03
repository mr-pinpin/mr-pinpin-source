# Mr. PomPom: completed character reference package

This run applies the [character-creation workflow](../character-creation.md) to the infant hedgehog in PinPin's family. The Studio agent generated the artwork and corrected the views; codex-wap1 reviewed it as Miguel's explicitly authorized representative. The final 24-study package was accepted for reuse under that delegation on 2026-10-03.

The original request authorized the first prototype. The requested Edit / Confirm / Exit checkpoint came after that visible candidate. Prototype confirmation authorized the remaining requested package; there was no additional chapter-approval or “go ahead” prerequisite.

## Character and coverage

PomPom is a tiny infant, distinct from older PinPin: round head, short rounded muzzle, dark brown eyes, small dark nose, round ears, warm brown quills, cream face and tummy, and short limbs. The warm dimensional rendering follows the existing family image. Poses remain supported sitting or reclining; the run does not establish independent standing or walking. The family reference establishes relative scale; isolated sheets do not establish absolute height.

The final composite contains 24 studies:

| Group | Coverage |
| --- | --- |
| Face perspectives | Six views, including opposing three-quarter directions and profiles |
| Expressions | Calm, delighted, curious, surprised, sleepy, mildly upset |
| Body perspectives | Six supported views |
| Gestures | Reach, wave, clap, hug a ball, look up, recline |

Initial source sheets repeated a three-quarter direction. Targeted native edits corrected the face's second cell and the body's fourth cell; the originals remain retained. Composite labels explicitly use screen-facing left/right. The body source's original labels describe the visible character side, while face source labels describe screen direction. This is a generated reference study, not a measured 3D turnaround.

## Registered outputs

The [machine-readable manifest](mr-pompom-assets.json) contains full SHA-256 hashes, byte counts, dimensions, exact prompts, input references, correction provenance and storage paths for every row.

| Role | Registered asset ID | Dimensions |
| --- | --- | --- |
| Existing family reference | `asset-88d74c56a468e3f250b12dbc` | 1536 × 1024 |
| Working prototype | `asset-463aeb445b75c551fad7414b` | 1254 × 1254 |
| Initial face sheet, retained | `asset-dc2b8c16da4e6a0117680fa8` | 1536 × 1024 |
| Initial body sheet, retained | `asset-7dcf707dc1478230a7a5cc94` | 1536 × 1024 |
| Corrected face sheet | `asset-dd88542003c752494cb277f0` | 1536 × 1024 |
| Corrected body sheet | `asset-4b5cccd08ae5bf379e3864a8` | 1536 × 1024 |
| Final unified composite | `asset-483201f4d30299518e37b401` | 1024 × 1536 |

Final composite SHA-256: `483201f4d30299518e37b401259cdd365de5efcdfddf3624156c4c1f176b4f2a`.

All generated outputs came from actual `image_gen.imagegen` calls and were copied without conversion. Registered files match their recorded bytes and hashes. No job records were created in this run; revision provenance uses actual source asset IDs, not invented job or `retryOf` history.

## Review and acceptance

- Prototype working-identity confirmation: `message-72bf29e48ff44b42a452`, codex-wap1 acting under Miguel's delegation.
- Independent visual QA found consistent infant identity, opposing view coverage, natural expression variety, supported gestures and no obvious limb duplication at delivered resolution. Native-byte and browser-loading checks passed.
- Final package acceptance for reuse: `message-a418666a456249b48eb5`, 2026-10-03 09:12:46 UTC, codex-wap1 acting under the same delegation.

These are attributed delegated decisions, not a personal review or click by Miguel. The family reference retains its existing `user-approved` status. All six newly generated assets retain their actual `unreviewed` registration status. The workflow acceptance does not silently select canonical entity references or fabricate approval metadata. No publication occurred as part of this run.

## Open the actual artifacts

In the matching Studio instance, select or attach the registered IDs above. Each registry URL follows `/api/assets/<asset-id>`; it is local to that Studio registry, not a public download. The canonical external data root for this run is:

```text
/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-conversation-data
```

Useful paths relative to that root:

| Artifact | Data-relative location |
| --- | --- |
| Final composite | `generated/pompom-unified-reference.png` |
| Corrected source sheets | `generated/pompom-faceFixed.png` and `generated/pompom-bodyFixed.png` |
| Working prototype | `generated/pompom-prototype-v1-01a0ff85.png` |
| Live workflow and dossier | `workflows/character-creation.md` and `workflows/mr-pompom.md` |
| Source prompts and registrations | `reports/pompom-source-package.json` |
| Composite prompt and registration | `reports/pompom-composite-prompt.txt` and `reports/pompom-composite-registration.json` |
| Completion record | `reports/pompom-workflow-completion.json` |

Generated binaries stay outside this repository. A clone has this portable documentation and manifest; displaying these specific IDs requires the matching registry and files. Do not replace missing files with invented examples.

The implemented inline card can present the final package as:

```ui
{
  "type": "WorkflowCard",
  "title": "PomPom — accepted reference package",
  "text": "24 studies accepted for reuse by codex-wap1 under Miguel's delegation. Registry candidates remain unreviewed.",
  "assetIds": [
    "asset-483201f4d30299518e37b401",
    "asset-dd88542003c752494cb277f0",
    "asset-4b5cccd08ae5bf379e3864a8"
  ],
  "actions": []
}
```

This completion card uses the real schema and no follow-up actions, so it has no option-selection hint. Click a registered image’s **Open full-size** control to inspect the original at 100% with scrolling, use **Fit to window** for an overview, and **Close** or Escape to return. The viewer does not change the image or review status. Source and ready-build matching plus syntax/renderer assertions passed for workspace build `e13edd4de644de7a2744d58f41472ca0062797589b9647d217f01d67f0df44db`; independent headful Chrome verification passed all 12 checks at 2026-10-03 09:22:47.605 UTC, including native 1024 × 1536 display, scrolling, Fit/100%, Close/Escape and focus return, no actionless footer, intact split layout and zero JavaScript errors.

## Reuse lessons

Generate a first reviewable candidate promptly, retain its identity as the reference, and expand into a few coordinated multi-view sheets. Inspect direction coverage before composing the final sheet. Make targeted corrections, preserve successful material and exact prompts, and finish the requested package without redundant permission loops.

The sequence and timestamps are provenance, not a measured latency benchmark: registration times do not establish generation start/end or total turnaround. Avoid claiming generation speed from those intervals.
