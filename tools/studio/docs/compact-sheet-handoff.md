# Compact sheet and pointer hotload

Stable 0ec577... and chapter_drafts.py unchanged. Root applies additive export with base-hash checks; no restart needed for reloadable business/workspace. Initial26 exports remain separate and frozen.

`business/compact_sheet.py` registers two operations through registry:

- POST `/api/business/draft.sheet.bind.v1` (mutation): chapterId, sourceVersion, sourceVersionSHA256, registered assetId, assetSHA256, ordered panelIds, columns, rows, promptSHA256, receiptSHA256, expectedRevision. No filenames, URLs, raw prompts, transport selectors, production authorization or generation. Source version/hash/panel order and registered local image SHA/size verified. Grid slots equal panel count. Prompt/receipt digests are explicitly caller-declared provenance assertions, not verified remote/tool evidence. Existing generation receipt remains authoritative separate evidence.
- POST `/api/business/draft.sheet.get.v1` (read): chapterId only. Historical reads use historical project; historical mutations denied. Returns bindings and stale/registered metadata status, no filesystem paths.

Independent chapter.studioDraftPreviews survives core save_draft; max32 records and512KiB cumulative JSON. Bind request/response128KiB; get request4KiB, response1MiB, timeout10s. Identical repeats refused. Asset <=40MiB, SHA/size verified before binding. Cold/missing/corrupt local bytes refused rather than silently registering substitute. Existing reference/production guards untouched.

App owner registers existing actual sheet through normal image registration and invokes bind with actual generation receipt/prompt digest, source v3/hash and ten ordered IDs, columns2/rows5. QA has not registered or bound the real comic. NEW compact-sheet-view renders one prominent whole page above detail cards and suppresses its whole-sheet asset in all individual panel cards. Narrative revision keeps saved sheet visibly stale; no crops/lineart/scene illustrations fabricated.

Pointer editor fix retains open, dirty text and focus/caret by chapter/version/panel (max256 entries); one-line workspace.js uses existing updateContent cache to prevent unchanged Plan DOM replacement. Real pointer summary/fill/Save/prior-version clicks pass in actual opaque normal Studio UI with unchanged composer and visible next version. Actual production/recovery-metadata browser confirmation remains coordinator/w5 acceptance.

Location host environment fallback (only if trusted Store attribute absent): mandatory STUDIO_LOCATION_SOURCE_ROOT, STUDIO_LOCATION_INDEX_PATH, STUDIO_LOCATION_PYTHON_PATH, STUDIO_LOCATION_OUTPUT_ROOT; optional STUDIO_LOCATION_CACHE_ROOT. All supplied paths absolute. Source root contains tools/studio-locations/cli.py; index points at actual trusted catalog; output/cache outside source, configured by host. Missing configuration honestly503; request/project cannot configure it. w5 received names through Mission Control CLI. Actual host values supplied by coordinator, no guessed paths.

Portable checks from mapped tools/studio:
`PYTHONPATH=<existing Pillow dependencies> python3 -B tests/test_compact_sheet.py` (14 real Store checks)
`python3 -B tests/test_location_host_configuration.py` (6)
`node web/tests/test-compact-sheet.mjs` (7)
`PYTHONPATH=<existing dependencies> python3 -B tests/test_business_extensions.py` (23 HTTP/runtime regression checks)
Existing unchanged stable JS checks52 remain valid. No paid/provider calls, full production or publication; $0.

## Native agent command and selected context

NEW `tools/chapter_sheet_ops.py` uses the existing active-bundle native CLI route interface (same read-only bundle loading pattern as chapter_draft_ops). No network calls, stable enum additions, runtime activation or artifact writes. It accepts a pre-existing receipt, hashes exact receipt bytes, uses receipt.proposedBinding chapterId/version/sha256/panelIds plus receipt.sha256/promptSHA256, and binds the separately registered image ID with explicit grid and optimistic revision. It does not print receipt prompt/private paths. Seven additional native CLI/selected-context tests pass, including real active-bundle binding with unchanged business-state bytes and real selected_context through runtime.

`tools/studio-python tools/chapter_sheet_ops.py --data-dir <DATA> --runtime-dir <ACTIVE_RUNTIME> bind --receipt <existing-generation-receipt.json> --asset-id <registered-sheet-id> --columns 2 --rows 5 --expected-revision <revision>`

Root must copy authored helper to DATA/tools/chapter_sheet_ops.py and workflow to DATA/workflows/compact-sheets.md in addition to canonical Git source mapping. Explicit PINPIN_STUDIO_RUNTIME host environment enables fully prepared selected command; otherwise it honestly shows <active-runtime-dir>. Small registration wrapper adds compactSheet workflow metadata to selected chapter context, preserves original user text/local-image inputs, and omits mutation command for historical review. context.py remains untouched.

Use the coordinator/w5-owned `tools/studio-python` wrapper; generic explicit Python startup has stalled in production despite isolated -S tests. Do not install or change dependencies. Root canonical convention is `workflows/` (alongside chapter-drafts.md); helper at `tools/chapter_sheet_ops.py`, portable tests at `tools/studio/tests/`.
