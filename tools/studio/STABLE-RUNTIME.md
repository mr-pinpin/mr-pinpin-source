# Stable Studio runtime and evolving workspace

The conversation shell and Python service run from an immutable release. The right workspace runs in a separate opaque-origin iframe, built from a dedicated editable source directory. Updating that source does not restart the server, reload the parent document, or replace the conversation.

## Freeze and launch

Use the existing Python environment on the Mac mini. Runtime artifacts and project data must be separate directories outside Git.

```sh
python tools/studio/release.py --runtime-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime freeze
```

The command returns `stableRelease`, `path` and `server`. Launch the returned `server` path:

```sh
PYTHONDONTWRITEBYTECODE=1 python /RUNTIME/stable-releases/HASH/server.py \
  --data-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-shell-preview-data \
  --workspace-source /Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/web/workspace-dev \
  --runtime-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime \
  --media-root /Volumes/TB4/mac-mini-storage/shared \
  --port 18836
```

Use a persistent tmux session for operation. Do not restart an existing service merely to make UI changes. A stable shell/backend change requires an explicit new release and deliberate cutover. Verify an existing release with `release.py --runtime-dir /RUNTIME verify HASH`.

Freeze copies the complete Studio tree, excluding hidden/development artifacts such as `.git`, `__pycache__` and `node_modules`. Every file is hashed; canonical manifest SHA256 names the release. Published files are mode0444 and directories0555. Existing hashes are verified and never overwritten. Server startup verifies the stable release's complete manifest. Running directly from mutable source is development mode and reports `stableRelease:"development"`; it is not an immutable deployment.

## Workspace builds

The background watcher scans the configured workspace source every500ms and waits400ms for stable content. It requires `index.html`, checks JavaScript with `node --input-type=module --check`, and validates JSON. It never runs `npm`, package scripts, imported JS, or arbitrary source build commands.

A source change is captured into memory, hashed, validated and captured again to detect edits during validation. The builder publishes a new immutable directory atomically, then updates the latest manifest. Build failures retain the previous valid URL and expose a bounded diagnostic. All previous builds remain available.

`GET /api/runtime` returns:

```json
{"stableRelease":"sha256","workspace":{"latest":"sha256","previous":null,"status":"ready","error":null,"url":"/workspace-builds/sha256/index.html"},"pollIntervalMs":1000}
```

Status is idle/building/ready/error. Errors are `{code:"workspace_build",message}`. `GET /api/runtime/releases/list` returns retained workspace hashes, URLs, creation times, file counts and byte counts. The parent polls this small manifest, prepares a candidate iframe and swaps only after the child reports ready. Syntax-valid runtime failures are caught by that readiness boundary; backend syntax checking does not claim semantic correctness.

Workspace files are served by exact hash and manifest path with immutable caching and byte-checksum verification. Traversal, symlinks, hidden files and documentation files cannot be served. Only immutable workspace static responses receive wildcard CORS, required by opaque-origin ES module imports. JSON APIs and private assets do not receive wildcard CORS. WebGL textures use the parent binary-asset RPC.

## Boundaries and agent UI work

The iframe must retain `sandbox="allow-scripts allow-downloads allow-popups"` without `allow-same-origin`. The parent owns conversation DOM, API authority, URL state and drafts. It verifies source-window, opaque origin and per-frame nonce before accepting bridge messages. Read [web/FRAME-PROTOCOL.md](web/FRAME-PROTOCOL.md) and the workspace source's `AGENTS.md` for the exact RPC contract.

The local Codex agent receives writable roots for exactly the project data directory and the configured evolving UI source directory. The stable release and runtime artifacts must lie outside both. Every turn starts/resumes with current developer instructions and explicit sandbox roots, so an older thread cannot retain obsolete permissions. User-requested UI improvements do not require comic production-plan approval. Art production still requires the approved current plan.

The agent can edit the evolving UI, run syntax checks, and write reports to project data. It cannot edit the frozen shell/backend, overwrite release artifacts, publish the book, or approve creative outputs. It must preserve existing work and use the established bridge rather than bypassing the iframe boundary.

## Reproducible review

`GET /api/state?revision=N` returns the closest saved project snapshot at or before N, with `readOnly:true` and `review:{requestedRevision,snapshotRevision,liveRevision,liveCollections}`. The project is immutable; assets/jobs/storyboards/events remain explicitly live registries. Requests for future or absent revisions fail. Normal `GET /api/state` is unchanged.

A pinned conversation sends `projectRevision:N`. Its model context uses the same historical project, and the turn receives a read-only sandbox plus explicit review-only instructions. It does not reinterpret old scene IDs against today's live project. The parent blocks workspace mutations while pinned. Return to Live before editing.

A copy link pins both a workspace build hash and project revision, plus selected chapter/view/scene/entity/language/media/camera/time state. Unsaved drafts are retained by the parent session; they are not falsely represented as saved revision content.

## Verification

Run `python -m unittest discover -s tools/studio/tests -v`. Runtime tests cover immutable release preservation, build debounce, syntax failure retention, no package-script execution, symlink/traversal/tamper rejection, scoped CORS, historical review, and per-turn agent sandbox scope. Actual model integration probes use isolated data/UI roots and leave the live project untouched.

## Restore and stable-core migrations

Back up source, complete stable release directories, complete workspace build directories and their manifests. Back up project data separately, including state.json, settings.json, history/, conversation.json and registered assets/jobs/storyboards. The runtime artifact contains code only; it does not contain the project, credentials or Codex login. Reinstall the documented Python dependencies and Node/Codex tools on the target machine, verify each release with release.py, restore data to an external directory, then launch the pinned server path. Codex authentication remains machine-local.

To restore a UI view, open a known workspace build hash in the shell URL. To restore the stable shell/backend, stop only the intended service and launch a previously verified stable release against compatible data. Do not overwrite old release directories or copy modified files into them. Preserve the source commit, manifest hash, launch arguments and data backup used at cutover.

Future backend/store/schema changes require a new stable release. Write migrations as explicit versioned operations with pre-migration backups and compatibility checks. Verify them on a separate copy of project data, then perform a deliberate serving cutover. A new workspace build must remain compatible with the running parent's documented bridge; protocol-breaking changes require a coordinated new stable release. A workspace hash and project revision preserve that UI and saved project snapshot, not an entire historical runtime environment or historical job ledger.
