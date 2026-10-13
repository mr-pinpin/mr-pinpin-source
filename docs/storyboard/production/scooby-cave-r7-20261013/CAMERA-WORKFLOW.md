# Apply the working 360° lesson to a walk through caves

Reviewed workflows:
- `docs/storyboard/panorama-workflow/README.md`
- `docs/storyboard/panorama-workflow/source-frame-lock.md`
- `docs/storyboard/production/tractor-explore-20260924/README.md`
- `docs/storyboard/production/house-image-tour-20260924/README.md`
- `docs/storyboard/locations/AGENTS.md`
- `docs/storyboard/locations/pinpin-house/README.md`
- `tools/panoramas/README.md` and `tools/locations/README.md`

The tractor distinguished orbit translation from turning in one fixed panorama.
Its later source-frame lock preserved the visible machine using a registered
source texture; an image-model instruction alone did not prevent deformation.
Room work checked real viewer directions and joins, with repairs extracted from
the current assembled stack. The measured house workflow recorded origins,
targets, FOV and door states in an actual scene.

## R7 application

1. Freeze a top-down layout plus a longitudinal elevation section, bank widths,
   ceiling heights, occluding limestone screen, water levels and light positions.
   R7's new coordinates are authored blocking units, not recovered book dimensions.
2. Give every viewpoint a fixed origin/target/FOV and a landmark checklist.
   `cave-layout.json` records pilots, route and expected visible/hidden features.
3. Build simple cave blocking geometry for translated cameras before narrative
   batches. If precise sightlines are claimed, render this geometry; a schematic
   or generated spherical illustration alone cannot establish that claim.
4. At each important fixed viewpoint generate one empty continuous panorama.
   Inspect front/right/back/left/up/down, wrap and oblique joins in the real viewer.
   Keep landmarks and lights fixed, then freeze the selected stack.
5. Use `tools/panoramas/project.py extract --config ... --yaw ... --pitch ...`
   for a still from that origin. A turn uses that sphere. A move to another shore
   uses a new recorded origin/guide, not a yaw adjustment or false reprojection.
6. Add acting/characters to the selected perspective with approved identity inputs.
   Preserve an environment source core where appropriate, as in the tractor lock.
   An illustration of a moved dog requires a new pose; pixel locking an old pose
   is not an animation or anatomy solution.
7. Inspect adjacent views with the top-down camera overlay: screen direction,
   entrance/exit sides, water flow, shaft/berries and the occluding wall. Hide the
   lake before the reveal; afterwards retain its shoreline in all reverse views.
8. Record input/output hashes, prompts, origin/target, extracted view and actual
   reviewed angles. Projection math validates sampling, not visual correctness.

Current state: recorded plan and camera pilots only. No new cave Blender scene,
panorama, measured sightline proof or finished narrative images are claimed.
Existing measured house geometry and approved room/tractor panoramas are unchanged.
