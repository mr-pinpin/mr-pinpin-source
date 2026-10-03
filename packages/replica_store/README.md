# replica-store

Standalone configurable Python library: content-addressed verified bytes, a durable filesystem outbox, Hugging Face bucket publication, and optional local replica polling. No PinPin imports, Mini endpoint, mutable shared remote index, server restart, credential files, or original eviction. Dependencies are declared in pyproject.toml; install this package in a network-capable host's Python environment.

## Contract and configuration

Repository(config).enqueue(asset_id, source, sha256, size) verifies and copies exact bytes into its owned objects directory before publishing a local job. The worker only reads owned objects addressed by validated hashes. Source paths never enter jobs or remote manifests. Producers can leave/offline/disconnect after enqueue. Logical IDs stay local. One configured root serves a serialized outbox and/or an optional replica; independent clients use separate roots and the same bucket/namespace. Remote put never requires a Mini/LAN endpoint.

Configure root (absolute), bucket (namespace/name), namespace (relative), maxObjectBytes, maxLocalBytes, minFreeBytes, batchSize <=64, maxRemoteScan, pollReplica and pollIntervalSeconds. Default Studio deployment uses the already approved public artwork bucket and dedicated replica-store-v1/book-art namespace. Configuration and receipts are local. Standard HF SDK authentication uses its environment/cached credentials privately. Never upload sessions, prompts or private documents to a public artwork namespace.

```sh
python -m replica_store --config /path/config.json enqueue stable-id /path/image.png FULL_SHA256 SIZE
python -m replica_store --config /path/config.json worker --once
python -m replica_store --config /path/config.json worker --watch
python -m replica_store --config /path/config.json status stable-id FULL_SHA256
python -m replica_store --config /path/config.json put stable-id /path/image.png FULL_SHA256 SIZE
```

Put is direct remote publication from any configured network-capable client; enqueue is offline safe. Pending is never verified. A worker uploads objects/SHA, freshly downloads/verifies full SHA/size, THEN publishes an immutable manifests/first-hex/SHA.json containing only schemaVersion, sha256 and bytes. HF batches are nontransactional: a crash after object upload is harmless and recoverable, a failed verification never publishes a manifest. Identical concurrent clients publish identical immutable records; differing objects have different records. No lost-update shared index exists. Existing conflicting bytes/manifests are refused.

Optional Mini replica: configure a separate root and pollReplica:true, then run worker --watch. It polls HF immutable manifests in 16 rotating digest partitions, persists bounded scan offset, verifies manifests and bytes before non-overwriting atomic materialization. Subsequent sweeps find late records; remote/LAN/Mini availability does not block other clients. A partition exceeding maxRemoteScan reports pending/actionable rather than scanning without bounds. Existing original/owned bytes are never deleted or evicted. Budgets can therefore fill: increase the explicit budget or provision space; do not assume unlimited quota.

Outbox attempts retain bounded exponential backoff (10s to 3600s), failure class only and recovery state. Workers serialize per root with flock; independent roots need no global lock. Atomic records are fsynced, object publication uses non-overwriting hard links and verifies concurrent existing bytes. Traversal/symlinks, corrupt conflicts, oversized files/manifests and low free space are refused. Host jobs have a strict allowlist without source paths. HTTP metadata bounds SDK downloads; providers must honor their declared stored sizes, and post-download size/hash is independently checked. Full host process/network timeout policy remains deployment-owned.

Tests use isolated fake remote storage, real files and real library operations; no live credentials or production deletion. Run `PYTHONPATH=src python -m unittest discover -s tests`. A real host worker round trip is a separate acceptance step, never inferred from offline tests.
# Correction contracts

An identity-matching historical receipt remains byte-for-byte unchanged on a valid local cache hit, including `verifiedUTC`. It describes verification at that historical time, not current remote availability. Without that proof, polling freshly downloads and SHA/size-verifies the remote object before issuing a receipt, even when owned bytes already exist. Missing or corrupt remote bytes produce a pending entry failure and do not create or refresh proof.

Logical asset IDs are immutable: enqueueing a changed digest under an existing ID is refused without replacing its job or bytes. `status(asset_id, sha256)` binds both request fields and the job size to its receipt; another object's receipt cannot prove this identity.

`put` processes only the requested logical ID, respecting durable retry backoff, rather than draining an unrelated backlog batch. Network failures remain pending. `get <sha256> <size>` (or `Repository.get(remote, sha256, size)`) verifies the exact immutable manifest and downloaded object before atomic local materialization. Existing corrupt local objects are refused and preserved. CLI `resolve` remains local-only; CLI `get` permits explicit host-side remote fallback.

Polling records a bounded per-partition failure summary, advances past failed entries and retries them on later partition wraps. A pass with failed entries reports pending and never counts those entries as verified. Studio canonical restoration checks shared owned bytes first, can invoke configured host Python cold-get, and retains its legacy archive fallback. Agent sandbox network restrictions still apply; pending does not establish a remote backup.
