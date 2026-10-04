# Bounded Studio artwork storage

Studio authority is LOCAL DATA, with code in SOURCE and immutable releases/builds in RUNTIME. Original TB4 metadata/art remains preserved. Do not restore old writers or overwrite live metadata from a prequiescent checkpoint. Conversation, project and all history remain private local metadata plus versioned authorized Air SMB snapshots; never upload them to the public artwork bucket.

## Selected-ID contract

Run `tools/studio-python "$PINPIN_STUDIO_SOURCE/tools/studio-assets/cli.py" ASSET_ID...` for metadata only. It reads at most16MiB registry input, selects1–4 exact registered IDs, reports existing review statuses/roles, and never downloads on paint/query. Unknown IDs, unsafe registered paths, over-budget requests and corrupt bytes fail explicitly. Registry identity/approval is never rewritten.

Ordinary authorized generation or reference preparation may choose `--restore` automatically as an INTERNAL workflow step, not an extra human permission. Default missing-byte budget32MiB, explicit max64MiB; total default timeout45seconds, max60. Restore off interactive paint. The existing `business.asset_storage.hydrate_selected(store, ids, restore=True, byte_budget=..., timeout_seconds=...)` is the app library handoff. Existing configured replica_store.resolve/get supplies immutable content-hash bytes first; legacy archive fallback requires its verified receipt. Missing/offline/timeout returns pending, never guessed inventory or remote proof. Root owns adding an asynchronous UI consumer; naked immutable asset GET still requires local bytes. Do not run cold transfer in the GET/paint path.

Preserve distinct book/location identity, geometry underlay, projection exemplar and image-led stop roles. Projection style does not donate a new room layout. Tractor24 selected stops are video-derived visual stops, not measured uniform15-degree cameras. Current selected viewer cache has stop07 source-display/panorama and orbit MP4; this is a sparse set, not a full gallery/archive recovery.

## One uploader and durable receipts

The existing replica_store CLI owns verification/upload: enqueue copies exact owned image bytes; worker downloads and SHA/size verifies before publishing immutable remote manifest and proof. Pending never means backed up. Old uploader/poller ownership must be quiescent before migrating queue metadata and starting one local host. Preserve every original job/receipt byte-for-byte; copy only still-pending owned objects after measuring them. Producer outbox has pollReplica:false. Do not repoint an independent namespace-wide poller at the producer queue; optional poller needs its own bounded root/checkpoint and approval.

`tools/studio-python "$PINPIN_STUDIO_SOURCE/tools/studio-assets/replica_host.py" --candidate LOCAL_LAYOUT status|start|stop` wraps existing pinned library CLI; start requires `--receipt` with quiescent, verifiedApplied, root and oldActorPids. It rechecks exact library hashes, uses one owned process group, worker--once passes every15s with60s timeout, and three256KiB status-only logs. No credential/error body logging. Standard HF SDK auth stays private. Wrapper SDK dependencies must be explicit package cache; automatic Python site startup is disabled. `cache_hf_dependencies.py --candidate LOCAL_LAYOUT` copies only installed required package/metadata closure within32MiB, with hashes, no install/download/credentials.

After actual native image registration, use existing `tools/studio-python tools/cast_ops.py enqueue ASSET_ID` to enqueue exact registered native-imagegen bytes. Do not forge provenance for deterministic sheets or reviewed source refs. Root-authorized source-art transfer can use the standalone library CLI independently; it does not change Studio provenance. Surface remote backup as pending until status binds exact assetId/hash/bytes to a verified receipt.

Mini offline does not prevent another configured network-capable host from resolving HF content-addressed objects into its own bounded cache; no Mini/LAN endpoint is required. An offline local verified hit works; missing uncached bytes remain pending. No claim that all445 assets or private history have a remote replica.

## Recorded acceptance

Three selected pilot references23,467,445B uploaded by sole local uploader; fresh remote object+manifest download/hash receipts preserved. Cold452,790B HF get6.611s; canonical app library materialization25.052ms; offline local hit exercised without any subprocess. Separate cold app library get through no-site wrapper and explicitly cached HF SDK completed7.405s. A get-only cache with no logical-ID outbox job conservatively reports unverified backup status despite a fresh hash-verified object receipt; do not relabel it. Fifteen fixture/admission/registration-validation tests passed. Exact host reports contain receipts/timestamps/hashes; these are actual remote tests, not inference from fixtures.
