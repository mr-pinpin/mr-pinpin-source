# Chapter production: persistent commands, exact inputs, resumable artifacts

Use `tools/studio-python tools/chapter_production_ops.py`; trusted host environment supplies PINPIN_STUDIO_DATA/RUNTIME/SOURCE and explicit Pillow/HF dependency caches. The helper verifies the immutable kernel and imports the existing active verified business bundle. It performs no generation, approval or publication. `schema` needs no Store/provider. `context` and `resume` are read-only and avoid constructing a settings writer.

Before dispatch, hydrate the reviewed current chapter using `context <chapterId>` and the existing chapter-draft context helper. Full production requires the existing explicit current-version/spec/reference-bound go. This CLI never grants it. Registered local reference bytes and scene alignment remain checked by the unchanged business dispatch. Rough-preproduction remains a distinct scope.

    tools/studio-python tools/chapter_production_ops.py schema
    tools/studio-python tools/chapter_production_ops.py context <chapterId>
    tools/studio-python tools/chapter_production_ops.py dispatch <request.json>
    tools/studio-python tools/chapter_production_ops.py claim <jobId> --agent codex

Minimal dispatch JSON:

```json
{"kind":"illustration","chapterId":"<chapterId>","sceneIds":["<sceneId>"],"instruction":"<actual requested work>","productionScope":"full-production","referenceIds":["<registeredAssetId>"]}
```

Optional referenceBindings assign actual roles: `[{"assetId":"...","role":"character-identity"}]`. Do not merge geometry, projection and location identity roles. Existing job creation writes a bound handoff prompt; it is planned input, not proof of the actual submitted generation prompt.

For each target scene, write the exact UTF-8 planned prompt and actual reference bindings to files BEFORE generation. Do not rely on functions store/load across a pending image call. `prepare` validates registered local reference hashes within256MiB and preserves prompt/reference files under that job without changing project state. A changed repair prompt produces a distinct hash/file. Inspect the relevant pixels before generation.

    tools/studio-python tools/chapter_production_ops.py prepare <jobId> --agent codex --scene <sceneId> --prompt-file <exact-prompt.txt> --references-file <actual-references.json>

Actual-reference JSON: `[{"assetId":"<registeredAssetId>","roles":["<actualRole>"]}]`. The result returns immutable promptFile/referencesFile paths and promptSHA256. Read these files when forming the generation payload. Record exact actual submitted tool/arguments/output path/hash and timing. A preparation file is not evidence that a tool executed or that its output was approved.

Complete one scene with the actual native output and exact submitted files:

    tools/studio-python tools/chapter_production_ops.py complete <jobId> --agent codex --scene <sceneId> --image <native-output.png> --prompt-file <submitted-prompt.txt> --references-file <submitted-references.json> --tool image_gen.imagegen

Existing complete_job validates claimed ownership, allowed source, target scene and actual registered references; one artifact is saved in a single Store mutation. It records actual prompt/reference provenance and preserves existing artwork. `--visual-pass` means actual agent QA only. Candidate completion does not select, approve or publish. Text artifacts use `--text-file` instead of `--image`; existing semantics complete a text job immediately, so do not use text completion to mark an image scene done.

    tools/studio-python tools/chapter_production_ops.py resume <jobId>
    tools/studio-python tools/chapter_production_ops.py fail <jobId> --agent codex --reason '<actual failure>'

Resume returns status, ownership, existing artifact hashes and remaining scene IDs without mutation or generation. Claim is idempotent only for the same already-claimed agent as provided by existing business logic. Completion is not an exactly-once RPC: after an uncertain result inspect existing artifacts/hashes before retrying, and never blindly repeat completion. Continue remaining scenes on the same claimed job. A failed job needs an explicit new dispatch with `retryOf`; current go/reference guards run again. Never auto-retry generation or infer authorization from an old job. Fail records actual failure; it does not remove artifacts or approvals.

Read-only runtime evidence and cost/storage boundaries are described in [studio-runtime-status.md](studio-runtime-status.md). Provider subscription use and additional paid API/video spend remain distinct. No deterministic one-shot guarantee is made. Private receipt paths and hashes are evidence. Keep credentials and raw conversations out of public artwork/source. Authorized exact prompt provenance and user-requested prompt/session archives may be retained in the intended private or explicitly approved repository, with destination and scope recorded.
