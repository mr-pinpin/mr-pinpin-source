# Character jobs and verified image storage

Use this contract for ordinary character requests. The request authorizes reversible drafts; do not ask for a second go-ahead. Preserve any design-review checkpoint actually requested. Human acceptance, selection and publication remain separate. Notetaker is unavailable; these Markdown dossiers and receipts are the durable fallback.

## Prepare once, before generation

Read the requested character's dossier/evidence and current registered sources. For a new proposed character, save a new character entity through `Store.save_project(project, expected_revision)` using fresh state, preserving every unrelated field. Create `workflows/characters/<id>/README.md` and `evidence.json`: sourced age/life stage, identity, source versus proposal, bibliography (empty only when no source portrait exists and that absence is disclosed). Add the requested solo/interactions requirement to the existing cast manifest; never reset its completed entries. Obtain established counterpart IDs from actual receipts. Do not invent ages, approval or measurements.

Write one spec under data containing `entityId`, `stage` (`solo` or `interactions`), exact `prompt`, `promptFile`, plain image `outputName`, `references` (`assetId`, `role`, optional expected `sha256`) and `omittedReferences`. The prompt file must contain the identical UTF-8 prompt. Reference IDs are the model-facing storage interface: do not reconstruct machine/provider paths. Rank/cap the pack using `tools.cast_ops.rank_reference_pack`; maximum FIVE input images. Layout is direction-only; never transfer species or clothing. Spell all six face AND body directions. Record named species/roles per interaction panel. Interactions must put the current verified target solo FIRST with a PRIMARY role, followed by relevant counterpart identities. Retain omitted bibliography honestly.

Run the configured Studio Python:

```
python -B tools/cast_ops.py prepare reports/<spec>.json
```

Use the returned `<spec>.prepared.json`. Preparation resolves the real IDs, verifies registered SHA-256/size against actual bytes, checks input count/roles, dossier/evidence, exact prompt, output filename, target solo and configured native tool. It reserves 160 MiB per prepared job for native/copy/registration overhead, plus a 2 GiB free-space floor and outstanding prepared reservations. A failure stops before dispatch. Policy is `workflows/storage-policy.json`; storage budgets are measured local bytes, not an HF quota claim. The prepared receipt is `reports/character-jobs/<attemptId>.json` and remains discoverable after interruption. Use its resolved paths only at the image-tool boundary.

## Run, inspect, register, finish

Invoke the actual native image tool with the exact prepared prompt and at most five resolved paths. Capture actual UTC before/after boundaries and returned native path in the existing call JSON. Inspect every subject/cell, opposed directions, species, scale, anatomy and contact. Preserve good versions. A repair is a new prepared attempt with `retryOfAttempt` pointing to the actual earlier attempt, plus the real reason. Do not invent a returned image after a failed call.

```
python -B tools/register_cast_spec.py reports/<spec>.prepared.json reports/<call>.json
```

The existing registration helper retains exact native bytes, prompt, references and candidates. The wrapper records a registered outcome only when the real asset's prompt and inputs match the preparation. It returns the registered WorkflowCard; show it immediately with real IDs and `actions: []` for a completed draft page. For a failed native call or an abandoned preflight, save an outcome JSON with `attemptId`, `status: failed|cancelled`, concise reason and actual known timing bounds, then `python -B tools/cast_ops.py outcome <outcome.json>`. Missing timings remain unknown. Never put tokens or provider response bodies in reasons. Failed/cancelled/registered outcomes release the logical reservation and are idempotent. Resume a prepared attempt from its durable receipt; do not repeat successful generation.

After real QA of both final pages, reuse `cast_ops.py finish <entity>` and the saved checkpoint command. They read canonical IDs/hashes from actual receipts and preserve curated evidence. Keep user-requested review separate from technical completion.

## Stable IDs, cache, backup and restoration

```
python -B tools/cast_ops.py resolve <assetId>
python -B tools/cast_ops.py backup <assetId>
python -B tools/cast_ops.py restore-replica <assetId>
```

Equivalent business POST routes are `/api/storage/resolve` (`assetId`, optional `restoreReplica: true`), `/api/storage/backup`, `/api/characters/prepare` (spec), `/api/characters/outcome` (outcome). The saved CLI invokes these through the active verified business bundle. The immutable browser RPC allowlist does not include these new routes; no bypass or kernel change is attempted. Existing browser media URLs remain unchanged. There is no arbitrary filesystem endpoint. The current asset registry remains the only catalog. Per-ID receipts in `reports/storage/` are verification proofs, not a parallel registry. Transfers project only image filename, object key, byte size and SHA-256 into the existing HF adapter; prompts, conversation, entire state and credentials are never uploaded. Standard SDK authentication stays private. The already approved public book bucket remains unchanged.

Resolution verifies local canonical bytes first. A missing canonical file is restored from a matching verified remote-backup receipt, using the existing adapter's non-overwriting materialization. Conflicting local/cache/remote bytes are refused. `/api/assets/<id>` and normal registration stay compatible: restoration places identical verified bytes at the existing canonical registry path. The immutable serving kernel itself is unchanged; resolve/preparation are the product boundary used before native tools.

Backup is explicit and limited to registered generated book image bytes. It uses the existing hash-addressed archive adapter and counts remote replication ONLY after fresh download/size/hash verification. `remoteBackupStatus: unverified` means no verified backup; a saved path or attempted upload is not proof. Receipts retain local/hash/size and verified HF object identity with observed time. No public visibility changes or historical migration are required.

The managed cache is under external TB4 Studio data, bounded to 1 GiB. Admission is serialized across app processes. Full-cache and low-disk conditions fail before transfers; this first version has no automatic eviction and never deletes/untracks canonical or generated art. `restore-replica` uses a separate initially cold subcache and materialized replica WITHIN that same budget, allowing a cache-miss demonstration while keeping canonical art untouched. Future missing-canonical resolution can restore the browser's original path. Existing approved art and all previous versions remain intact.

Preflight also derives native output/history/runtime-temp directories from CODEX_HOME or the current home, and system temp from runtime configuration. Optional nativeRuntime path overrides and reserves live in storage-policy.json. It checks each unique filesystem device once with store/native reservations and safe free-space floors; it never moves native history or changes the kernel.

The app-agent shell sandbox cannot resolve `huggingface.co`. Independent QA DID complete a real verified backup and cold download using the exact saved application CLI outside this sandbox; proofs are reports/storage/storage-live-cli-backup.json and storage-live-cli-restore.json. This does not grant this sandbox DNS or establish HF quota. Local preparation and fresh-process hydration work; isolated tests separately exercise corrupt bytes and low internal-disk/TB4-healthy refusal. No native-thread compaction or kernel change is claimed.

Normal character closeout: after recorded visual QA and registration, run `python -B tools/cast_ops.py closeout <entity>`. It reuses finish validation and exact stage receipts, preserves completed generation/benchmark records, and requests each missing verified backup through the existing loopback Studio HTTP business route. HF credentials stay in the server adapter. Failed or pending backups retain the usable local draft and are explicit in reports/character-packages/<entity>-closeout.json; no automatic POST retry. This command replaces finish-only closeout; batch checkpoint remains a separate inventory operation. The existing HTTP client/server uses loopback host/origin guards, not a token authentication scheme.
