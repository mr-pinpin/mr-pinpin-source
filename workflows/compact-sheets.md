# Bind an existing rough comic sheet

Keep rough page artwork separate from individual scene illustrations. Register the approved existing image through the ordinary Studio image registration workflow first; do not regenerate it merely to bind it.

Use the selected chapter's prepared `chapterDraftWorkflow.compactSheet` command. If its active runtime placeholder is unresolved, supply the coordinator-configured runtime directory. The authored helper must be installed in DATA/tools.

```sh
tools/studio-python tools/chapter_sheet_ops.py --data-dir <DATA> --runtime-dir <ACTIVE_RUNTIME> bind --receipt <existing-generation-receipt.json> --asset-id <registered-sheet-id> --columns 2 --rows 5 --expected-revision <selected-project-revision>
```

The existing receipt must include `proposedBinding.chapterId`, `version`, `sha256` (saved narrative digest), ordered `panelIds`; top-level `sha256` (artwork digest) and `promptSHA256`. The helper computes receiptSHA256 from exact bytes. It never emits the private prompt or paths in that receipt. Grid slots must equal panel count. Unknown source/version/order, stale project revision, missing/corrupt registered art or repeated identical binding fails; inspect current context before deliberately retrying. Do not silently rewrite hashes.

Binding saves chapter.studioDraftPreviews, leaving narrative versions, references, generation and production approval unchanged. Prompt/receipt digests are caller-declared provenance assertions; preserve the actual generation receipt for tool/input verification. The Studio displays one prominent complete sheet with source version/hash and ordered panels. Subsequent narrative revisions mark it stale while keeping old artwork reviewable. A sheet is never repeated as ten separate scene images or converted into fabricated crops/lineart.

No full production, provider calls or publication are implicit. Historical review exposes no mutation command. For host UI, registered typed operations are `draft.sheet.bind.v1` and `draft.sheet.get.v1`; request contains IDs/digests, never arbitrary filesystem paths or URLs.

Use the coordinator/w5-owned `tools/studio-python` wrapper; generic explicit Python startup has stalled in production despite isolated -S tests. Do not install or change dependencies. Root canonical convention is `workflows/` (alongside chapter-drafts.md); helper at `tools/chapter_sheet_ops.py`, portable tests at `tools/studio/tests/`.
