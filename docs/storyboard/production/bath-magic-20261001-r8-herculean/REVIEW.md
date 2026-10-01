# R8 complete illustrated draft — PinPin and the Twelve Surprises

126 illustrated scenes plus a cover, in English, Russian and Spanish, across six days. This is an unpublished draft awaiting Miguel's feedback. Earlier R5/R6/R7 readers and artwork remain separate.

Reader: http://127.0.0.1:18795/storyboard/review/bath-magic-r8-herculean.html?lang=en
Storyboard: http://127.0.0.1:18795/storyboard/review/bath-magic-r8-herculean.html?lang=en&view=storyboard

## Story and review

Twelve accidents form a causal chain, with a familiar incantation, short visual pauses and varied family responses. Cause & rhythm presents twelve translated cards, predecessor links and direct links to attempts, pauses, consequences and the final inverse gesture. PinPin's abundant physical energy is distinct from his limited magical control. The ordinary round table and shared family bed stay consistent.

All 127 selections have exact native-master/WebP identities in selected-scenes.json and story-plan.json: 48 unchanged selections with origin lineage and 79 newly generated selections (78 story images plus cover). The former scene124 reuse is retained as an unselected candidate; its replacement removes the flowing gutter after the water stops. Scene90 selects v1 after independent review counted twelve ducks; v2 is preserved as a rejected thirteen-duck candidate. Scene122 selects v3. These are production choices, not claims of user approval.

The story author and independent visual reviewers checked the finished sequence. See FINAL-STORY-REVIEW.md, geometry/OPENING-QA.md, geometry/ROOT-QA.md and root/ for reports. Camera-dependent decorative differences remain; the artwork is not a survey-accurate reconstruction.

## Browser proof

check-reader.cjs --complete passed at 1440x1000, 390x844 and 320x740: 126 scene images plus cover decode, no missing illustrations, no horizontal overflow or JavaScript errors, EN/RU/ES controls work, six day links navigate, and twelve causal cards and branched predecessor links are present. Fresh screenshots and exact tested hashes are in browser-check/. The 390px reader and translated causal overview screenshots were visually inspected. Image URLs use SHA cache busting.

Contact sheets are deterministic layouts with no artwork edits: one 126-frame overview and 21 six-panel sheets. Final native sheets are v2; v1 remains preserved. contact-sheets.json records the exact selected image hashes.

## Preservation

preserve-inputs.py verified 100 native image-generation outputs against actual tool output bytes, exact prompts and 75 distinct input identities, including superseded candidates and preproduction. verify-reuse.py --origins verified all 48 selected copied masters/WebPs and input lineage against source assets. The retired scene124 origin remains preserved.

The scoped archive contains 923 artifacts, 1,024,438,942 bytes: masters, WebPs, prompts/records/inputs, reuse origins, preproduction, both sheet generations, final production metadata and browser evidence. The assets manifest and receipt provide restoration. A completed receipt requires verified:true, dry_run:false and every entry verified:true/remote_verified:true; verify-preservation.py --current independently checks identities and current coverage.

## Reproduction on the mini

Canonical source: /Volumes/TB4/mac-mini-storage/shared/pinpin-workspace/mr-pinpin-source
Heavy pack: /Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r8-herculean

All processing, hashing, QA and archival run on the mini SSD. Existing Air18795 to mini18796 serves this isolated reader. Run from the pack on mini:

```sh
.venv/bin/python accept-lane-asset.py --lane story --id scene-40 --record records/scene-40-v1.json
.venv/bin/python refresh-media.py
.venv/bin/python contact-sheets.py --version 3
python3 preserve-inputs.py
python3 verify-reuse.py --origins
python3 finalize-selection.py
/opt/homebrew/bin/node check-reader.cjs --complete
python3 prepare-archive.py
python3 verify-preservation.py --current
python3 sync-source.py
```

Independent lane manifests live in root/, story/ and geometry/. The registrar preserves native outputs and exact inputs/prompts, then derives native-size WebP quality94/method6. --preserve-only retains rejected output without selecting it. reuse-assets.py imports only explicit inspected mappings. A changed frozen artifact requires an updated archive manifest and receipt before current-file verification can pass.

Source text belongs in Git; heavy artwork restores from the scoped asset manifest. See assets/bath-magic-20261001-r8-herculean.md. This lane performs no official publication or source push.

## Batched remote verification

All 677 missing content-addressed objects uploaded successfully. The original per-file verifier then hit provider metadata rate limits, so its process was stopped after upload. Scoped verify-archive-batched.py checks metadata in batches, downloads every unique object afresh, checks exact byte size and SHA-256, then checks the remote Xet identity again. Only after every check passes does it write the standard action:verify receipt. No global asset tool is changed. verify-preservation.py --current independently checks that receipt against all 923 current artifacts.

The top-level REVIEW.md and Python/JavaScript verification helpers are source-only Git artifacts, as is assets/bath-magic-20261001-r8-herculean.md. They are intentionally outside the media archive. Archived lane reports, prompts, records, browser evidence and production metadata snapshots are frozen and covered by the current-file audit.

Final preservation result: all 923 artifacts passed fresh remote byte readback and unchanged before/after Xet identity checks. The standard action:verify receipt is complete. Independent verify-preservation.py --current passed all 923 current files, totaling 1,024,438,942 bytes.
