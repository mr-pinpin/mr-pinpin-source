# Conversational location creation

Select an existing exact location through the existing catalog and business.locations adapter. Do not rebuild a cold index on an ordinary app turn. Query is metadata-only, never network. Use `tools/studio-python tools/location_ops.py context --location EXACT_ID` with configured PINPIN_STUDIO_DATA/PINPIN_STUDIO_RUNTIME (or explicit global flags).

Read docs/storyboard/panorama-workflow/README.md and tools/panoramas/README.md. Inspect actual local references before a native image request. Separate roles: seamless-panorama demonstrates healthy projection/finish only; location-identity establishes the target place and landmarks; book-style supplies style only. Target/style may share bytes with explicit separate bindings. A Blender geometry-underlay is optional and distinct, never implicitly required. The exemplar must differ from target identity. Record actual seam/pole/projection review evidence with its exact asset ID/hash; never manufacture that evidence from metadata/checksums.

If catalog files are not registered, use existing business.locations LocationAdapter.prepare with scoped verified hydration and supported role bindings. Absence returns pending restoration; use existing host storage/hydration job, then retry. No implicit long network operation in this helper. Do not claim bytes ready from catalog approval. Existing registered assets resolve through asset_storage; no new storage engine.

Prepare JSON contains location, expectedRevision, literal request, exact prompt, references [{assetId,sha256,role}], camera {intention, optional eyeHeightIntent/yawDegrees/pitchDegrees/fovDegrees}, and formatReview {assetId,sha256,projection:"pass",seam:"pass",poles:"pass",evidence:"ACTUAL OBSERVATION"}. Run `tools/studio-python tools/location_ops.py prepare envelope.json`. It saves immutable prompt.txt and prepared.json under DATA/reports/location-workflow/CONTENT_HASH. It produces one toolRequest but dispatches nothing. It preserves the current project, original artwork and review status. Native generation occurs only when actually requested in conversation, following imagegen skill and inspecting every supplied local image.

Request one continuous 2:1 equirectangular scene, rear left/right wrap and coherent poles, level horizon where intended. Prevent format/style references importing their unrelated doors/furniture. Preserve source landmarks/openings and requested camera intention; unseen continuation is artistic inference, not measured geography. An eye-height change must alter occlusion, not just tilt/crop. Save native master bytes unchanged and register via existing registration/asset storage workflow with actual prompt/reference hashes and prepared attempt provenance. Registration is owned by that existing workflow, not this helper.

Review actual dimensions/projection, rear wrap, poles, doors/openings, camera/occlusion and oblique angles in Spaces. Keep failed yaw/pitch/FOV/screenshots. Hash/math checks do not establish visual approval. Use tools/panoramas/project.py extract for demonstrated repair views; retain immutable repairs and hash-pinned selected stack. Only after review derive cubemap with existing `tools/panoramas/project.py export --input REGISTERED_MASTER --output EXTERNAL_DIR --width 3072 --face-size 1024` (or --config selected stack). Six faces sample one final scene; never generate independent faces. Retain exports-v1.json, input/output hashes, orientations and actual validation. No publication, paid video, provider fallback or story invention implied.

## Execute without source exploration

Context includes prepareSchema, crossFieldRules, prepareEnvelopeTemplate and current projectRevision. Select only the requested location. The template is a proposal requiring actual choices and actual observations: never submit SELECT_/REPLACE_ strings or report visual review merely because template fields say pass. Read supplied local images. W4 may pass an explicit trusted selected_references role-to-asset-ID map into location_context; those IDs/hashes fill the template, but availability stays metadata-only until preparation verifies bytes. No search across all locations or automatic panorama health inference occurs.

Minimal envelope (all placeholders must be replaced):
```json
{
  "location":"EXACT_EXISTING_LOCATION_ID",
  "expectedRevision":123,
  "request":"LITERAL_USER_REQUEST",
  "prompt":"EXACT_SUBMITTED_PROMPT",
  "references":[
    {"assetId":"HEALTHY_EXISTING_PANORAMA","sha256":"ACTUAL_64_HEX_SHA","role":"seamless-panorama"},
    {"assetId":"TARGET_LOCATION_ILLUSTRATION","sha256":"ACTUAL_64_HEX_SHA","role":"location-identity"},
    {"assetId":"TARGET_OR_DISTINCT_STYLE_IMAGE","sha256":"ACTUAL_64_HEX_SHA","role":"book-style"}
  ],
  "camera":{"intention":"ACTUAL_USER_INTENTION","yawDegrees":0,"pitchDegrees":0,"fovDegrees":90},
  "formatReview":{"assetId":"HEALTHY_EXISTING_PANORAMA","sha256":"ACTUAL_64_HEX_SHA","projection":"pass","seam":"pass","poles":"pass","evidence":"ACTUAL_VIEWER_ANGLES_AND_OBSERVATIONS"}
}
```

Envelope fields above are required; camera eyeHeightIntent/yawDegrees/pitchDegrees/fovDegrees are optional. No extra top-level/reference/camera/review fields. Reference role enum: seamless-panorama, location-identity, book-style, optional geometry-underlay. Three to five role bindings, each assetId/role pair unique. Format asset differs from target; style can share target with a separate role. Target SHA must occur in selected catalog. Format review binds exact format ID/hash, with projection/seam/poles pass established by actual inspection. Request/prompt nonblank <=32000UTF8 bytes each; total envelope <=131072bytes. Finite degree ranges yaw[-360,360], pitch[-90,90], FOV[1,179]. expectedRevision must match current Store. The emitted schema is authoring guidance, with maxUTF8Bytes as a descriptive extension; actual location_workflow.prepare remains the validator. It does not authorize generation.

Selection/provenance example: existing healthy house panorama is FORMAT ONLY, existing target outdoor illustration is LOCATION IDENTITY, selected book-style artwork is STYLE ONLY. Never import the house's doors/furniture into the outdoor variant. These are role examples, not assertions that a particular catalog image is healthy/ready. A proposed variant uses status proposed-variant-unreviewed, retains originalLocationUnchanged:true and exact source roles/hashes. Saved prepared.json retains literal request, exact prompt SHA, exact registered inputs/native paths, camera intention, format visual evidence and selected catalog indexProvenance. prompt.txt stores exact submitted bytes. Existing originals/review status remain unchanged; missing media returns pending-restore without a prepared generation record. Native output later has actual dimensions/hash, candidate status and registration provenance from the existing owner workflow.

Ordinary sequence: context --location EXACT -> explicitly select existing references -> existing scoped prepare/hydration if registered bytes absent -> inspect -> fill current guarded envelope -> prepare ENVELOPE.json. Reload current context after any revision conflict; never silently replace a stale guard. User words/camera/spec and format/style roles stay explicit. Root/native app generation and subsequent review/cubemap export are separate operations.
