# Character preparation from a structured spec

An ordinary new-character request receives a bounded characterPreparation pack with the verified existing family solos, family style/relative scale, layout-only template, source pointers and actual helper toolchain. These images do not define the proposed subject. Inspect the relevant actual images before generation. No conversation restart or storage-library substitution is involved.

Preparation availability follows workspace scope, not words or species guesses: unscoped live requests receive the optional bounded pack. Explicit entity/chapter/scene/asset selections retain their existing workflow unless characterPreparation:true is requested; characterPreparation:false opts out. Pinned historical contexts never read or restore mutable preparation inputs. A current counterpart is selected from saved final metadata before resolving its exact logical ID through existing storage. availability:blocked and missingReferences identify unavailable identities and recovery actions; never replace them with an older available candidate or proceed with an incomplete family pack.

Write one concise JSON spec, choosing routine design details within the request:

```json
{
  "entityId": "proposed-visitor",
  "name": "Unnamed proposed visitor",
  "request": "The user's actual character request",
  "identity": "Species, appearance and personality; mark proposed details",
  "scale": "Relative size, distinguishing sourced evidence from proposals",
  "geometry": "Anatomy, contact/support and movement constraints",
  "lifeStage": "Requested/evidenced life stage; no invented precise age",
  "proposed": true,
  "stage": "solo",
  "prompt": "Exact complete image prompt; spell both face and body screen directions"
}
```

Run `python -B tools/cast_ops.py prepare-character <spec.json>`. The existing helper initializes a new proposed entity, request bibliography, Markdown dossier and durable queue entry without hand-coded Store plumbing. It preserves existing dossiers on resume, ranks/caps actual references at five, saves exact prompt bytes and invokes the existing disk/reference/output preflight. It returns preparedSpec, actual references/native paths, omission lineage and commands. New established/canonical characters require separately indexed source evidence; this initializer refuses to invent it. Exact age remains not stated for this proposal initializer.

Use the native image tool with the returned exact prompt and actual references. Record real nativePath and generationBeforeUTC/generationAfterUTC in call.json, then run `python -B tools/register_cast_spec.py <preparedSpec> <call.json>`. Inspect the actual full page and record visual QA; repair meaningful defects with retryOfAttempt plus retryReason. Recorded attempts, failed preparation receipts and actual outcome receipts remain durable.

For the separate family page, submit entityId, stage: interactions and the exact prompt through the same prepare-character command. It reuses the current verified target solo FIRST, family identity/relative-scale image and needed counterpart solos; it omits the solo layout template. Name species/roles per panel, preserve age and relative scale, verify every participant/contact/support. Omitted sources remain bibliography and prepared receipt data, not claimed tool inputs. Register and inspect this page separately.

After both pages pass recorded agent QA, run `python -B tools/cast_ops.py closeout <entity>`, then the existing batch checkpoint when an inventory checkpoint is needed. Local draft completion, verified archive status and human approval stay distinct. The frozen badger benchmark is preserved. No image speed or full-job speed improvement is claimed until a comparable ordinary request is measured.

Storage uses the implemented standalone packages/replica_store library: normal closeout enqueues owned verified native image bytes through the filesystem outbox, and the host worker uploads/download-verifies them. Existing-character storage uses archive-existing instead of rerunning creative finish metrics. See replica-storage.md. No quota assumption or permission change is implied. Notetaker remains unavailable; durable Markdown is the explicit fallback.

Engineering exports are separate: `python -B tools/cast_ops.py closeout-dev-checkpoint <entity>` reads an existing closeout receipt and verifies authored/exported bytes. Ordinary `closeout` never calls this operation and does not require engineering source files, test proofs or export directories.

## Current shared storage and measured timing

The standalone `packages/replica_store` library and filesystem outbox are implemented. The native agent remains network-restricted; filesystem handoff to the host worker works. Badger, Otter and Beaver final pairs have matching verified remote receipts. New production uses `cast_ops.py closeout <entity>`; already produced characters use `cast_ops.py archive-existing <entity>` without historical metrics rewrites. See [replica-storage.md](replica-storage.md).

Actual deployment runs through authorized Mini tmux with a TB4 mount/UUID guard and bounded caches/logs. Direct launchd external-volume access blocks reboot autostart; automatic reboot recovery is not established. No Studio daemon/kernel change is implied.

Frozen ordinary character benchmarks remain Badger 658.651596s total / 87.371827s image / 571.279769s outside image; Otter 312.267804s total / 93.365586s image / 218.902218s outside image. These predate the combined shared-storage workflow; no new combined creation-plus-storage or full-chapter benchmark has been measured. Keep preparation, generation, visual QA, registration, metadata closeout and asynchronous transfer time distinct.
