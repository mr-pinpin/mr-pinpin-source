# R5 camera and practical-channel production
Status: 19 assigned illustrations selected for review (31–47, 53–54); nine originally assigned late images (48–52, 55–58) transferred to parent before generation. No publication or user approval implied.

## House remains canonical
The house-plan SHA-256 remains cab510b31c13e85beaa689edb54005223412a988f640724e56b9d95dba20c28c. All ten jobs reuse the verified original bath-wide Blender build. No wall, opening, room, permanent drain or canonical furnishing was changed. Front door 105°, bath door75°, bedroom door0° are job states.
Ten stills were rendered on the mini, inspected, then CLI prepare completed for all ten. Preparation bundles were completed after the art calls; actual art used inspected raw stills and exact references enumerated in generation records, NOT the auto-prepared template. Do not misrepresent the later preparation as the generation prompt.
Raw outputs: geometry/<job>/still.png and render-manifest.json. Preparation: geometry/<job>-prepared/{geometry-reference.png,prompt.txt,imagegen-job.json,prepared-manifest.json}. Each render manifest records input hashes and camera checks.

## Camera pool
- bath-channel-reverse: bath foreground toward open bathroom-to-common doorway. Supplies collector staging; no bathroom window on reverse wall.
- common-channel-north: across table toward bath/closed bedroom side. Front entrance is behind camera; do not introduce exterior door on back wall.
- common-channel-south: table left, original front door centered between two round windows.
- common-table-open: wider north/table option; not a claim that every art image used this guide.
- front-outlet: outside original front door looking in. Do not invent a second exterior door at back of room.
- bath-source: original magic camera position [-2.4,2.15,1.35], target [-3.1,2.65,.42],45mm. Matched original scene09 via direct image edit for53; root used53 for74–79.
- bath-rim-close: rim/water close viewpoint.
- bath-wide-channel: doorway-wide broad bath option.
- bedroom-protected: bedroom bed viewpoint. Final42/43 use exact earlier bedroom-art composition instead of forcing new camera.
- common-joint-close: low table-leg/joint detail spatial guide.

## Temporary channel
Broad removable external catch tray BELOW a chosen bath rim spill feeds shallow wooden U-channel. Portable pieces overlap upstream over downstream, with cream cloth joint seals and loose descending support blocks. It passes through existing bath doorway, west of common table, through propped front door, into garden. Small pails/cloth catch residual drips; not all overflow is magically diverted at once. Bedroom is closed with splash towel, not a certified watertight dam.
Broad LOW wood bath and large rust/cream oval rug UNDER it stay fixed. Distinct blue/cream common mat may move. Exact construction, gradients and dimensions in finished illustrations are stylized, not measured or hydraulically simulated. Geometry render does NOT contain the added channel prop; channel was inferred/staged by imagegen.

## Channel candidates and correction
channel-guide-v1: rejected because trough pours into bathtub, invented reverse-wall window.
v2: fixed wall and outward bath spill but long trough still pours toward collector. Entire candidate unselected; RIGHT panel only used explicitly as downstream common-room material reference.
v3: rejected; reversing falls text did not reverse hydraulic direction.
v4: new single-view, simplified continuous smooth gutter, no staircase falls. Tub visibly spills OUT into external curved collector, connected to channel through existing bathroom door. Internally selected production reference. Camera interpretation shifted from gray guide; not a one-to-one projection match.
Later common-room37-v1 inherited small inward falls;37-v2 removed steps for continuous shallow water. This is why selected37-v2 is preferred for later common shots.

## Art review and retained versions
31-v1;32-v2;33-v1;34-v1;35-v1;36-v2;37-v2;38-v1;39-v1;40-v1;41-v1;42-v1;43-v2;44-v3;45-v1;46-v1;47-v2;53-v1;54-v2.
Repairs:32 white modern tub→wood bath and common mat→bluecream;36 invented overalls removed, common mat bluecream;37 backward falls removed;43 invented open doorway/background family removed by returning to direct bedroom reference;54 child wrongly inside bath moved back outside using53.
53/54 preserve exact original over-right-shoulder composition. Partial reverse direction itself cannot be proven by a static circle; story and progressive erasure in final sequence supply that meaning.
Individual quiet, focused, inconvenienced and tired faces replace repeated grinning: supper40, cloth41, morning43, repair45, effort46 and hangingcloth47. Babies remain held or in highchairs. No duck appears in this lane, avoiding premature animation/wood-toy drift.

## Provenance and limits
Exact prompts are prompts/scene-NN-vN.txt, actual generation and inspected references in records/scene-NN-vN.json. Originals and rejected candidates preserved; immutable hashes/reference snapshots saved by register-generations.py. sourceOutput paths point at the existing generated-image symlink on TB4.
Finished art maintains recognizable setting and repeated staging but is not a metrically exact digital-twin reconstruction. Background detailing, mat extent and furniture scale can vary. Source guides constrain viewpoints; book art controls materials. No claim of pixel-perfect cross-image architecture.
Air disk exhaustion interrupted a prompt write (then saved onTB4); parent recovered space. During requested workspace migration final43-v2/47-v1 records and this report were written ONLY toTB4pack and must be incorporated into migrated source, not copied back to the old Air checkout.

Validation: CLI validate passed for all ten prepared manifests, three artifacts checked per manifest.

Final narrow QA:44-v2 still planted paw on channel, rejected;44-v3 clearly plants hindpaw on dry floor and lifts other foot over channel.47-v2 restores cream splash towel at closed bedroomdoor. All19 lane scenes frozen. Post-migration small source files copied via SSH into /Volumes/TB4/mac-mini-storage/shared/pinpin-workspace/mr-pinpin-source; no old Air checkout writes.
