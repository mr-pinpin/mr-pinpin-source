# Shared storage workflow

For storage of an already produced character use `python -B tools/cast_ops.py archive-existing <entity>`. It reads the durable selected solo/interaction IDs from `cast-run.json`, checks their registration receipts and exact native bytes, enqueues/checks shared storage, and saves `<entity>-shared-storage.json`. It does not rerun creative finish or rewrite generation/dossier/benchmark records. New production continues to use `closeout`. Historical Beaver calls use `before`/`after`/`seconds`, whereas modern finish metrics expect `generationBeforeUTC`/`generationAfterUTC`; archive-existing bypasses those unrelated metrics entirely.

Cold retrieval: host `python -B -m replica_store --config <config> get <fullSHA256> <bytes>` verifies the immutable manifest and object before materialization. Studio resolve uses shared owned bytes first and configured host-Python cold get when missing, with existing legacy archive fallback. No sandbox remote success is inferred. A corrupt polling entry records failure and advances; later wraps retry it. `put` targets its requested immutable logical ID rather than unrelated backlog work.

Normal `python -B tools/cast_ops.py closeout <entity>` verifies both final registered pages and automatically enqueues exact owned bytes. `python -B tools/cast_ops.py enqueue <assetId>` idempotently refreshes receipt status. These operations require no agent network access. Pending backup retains the usable local draft; only a matching fresh-download hash receipt counts as remote verified. Old archive proofs remain intact.

Host command, using the exported standalone package and existing HF SDK/private authentication:

```sh
PYTHONPATH=/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-conversation-data/exports/packages/replica_store/src /opt/homebrew/bin/python3 -B -m replica_store --config /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-conversation-data/workflows/replica-store.json worker --once
```

Use `worker --watch` for explicitly requested polling. The worker owns transfers; Studio never submits source paths in jobs. Configuration is `workflows/replica-store.json`. An optional independent replica uses its own absolute root and the same bucket/namespace with `pollReplica:true`; it polls HF and requires no Mini endpoint. Limits and reserves refuse new admission without deleting originals. No remote quota is asserted.

The standalone API and installation instructions are in `exports/packages/replica_store/README.md`. Source outside writable roots is exported for mechanical copying; no kernel or daemon change is required. Native prompts, decisions, timing and visual QA stay in existing local character records, outside remote manifests.
