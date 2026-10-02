# PinPin Studio

Studio is a local workspace for discussing a chapter, choosing references, inspecting small storyboards and handing precise generation jobs to an agent. It does not publish a chapter or pretend that queued jobs have generated images.

Start with the [CLI documentation](../../../tools/studio/README.md) and [API contract](../../../tools/studio/API.md). The [seed catalog](../../../tools/studio/examples/README.md) contains the real book and references, not demonstration placeholders.

## Seeded material

- Original Russian manuscript: all 38 source chapters, faithfully flattened from `docs/storyboard/book.json`; the exact structured original is also retained.
- Ten published library entries, including the explicitly labeled earlier Elder edition. These are catalog links, not ten newly imported editable stories.
- R17 bath draft: 171 scenes plus the approved localized cover, separate from the published 138-scene chapter.
- Eighteen character, place, prop, style and panorama records. New Bear/blue utility tractor designs remain agent-reviewed and user-pending.
- 138 prior editorial tempo annotations matched by stable ID, plus 33 explicitly proposed new ratings. Physical activity, comic pressure and discovery use low/medium/high ordinal categories. These are not measured audience attention or elapsed time. R17 day allocation is 100, 13, 22 and 36 scenes.

The source catalog names 192 checked imports, deduplicating to 190 immutable asset files. Media are copied into the external data directory; the running UI does not depend on Air storage or mounted symlinks.

## A short working cycle

1. Discuss what happens and why. Write concrete setup, attempted solution, consequence and family response.
2. Choose identity, scale, location and style references by role. A useful image for dog scale may be wrong for the house architecture.
3. Define camera position, height, direction, field of view and gaze. Record object states before and after the scene.
4. Inspect a compact board with existing art or clearly blank panels. Agree on the missing actions and transitions before expensive work.
5. Queue one bounded generation or repair instruction. An active agent uses the image tool and preserves native output, exact prompt and reference hashes.
6. Review the result against neighboring scenes. Agent review and user approval are distinct states. Keep alternatives and provenance.
7. Export or publish only the selected approved version using the established release process.

Thirty minutes is an iteration target to measure, not a guarantee for a long illustrated chapter. Record planning, generation, review and export time separately. Do not optimize by silently skipping the reference or review stages.

## Continuity that must survive edits

The [lessons](../../../tools/studio/examples/lessons.json) and [prompt templates](../../../tools/studio/examples/prompt-templates.json) explain the concrete lessons behind this workflow.

PinPin fetches one bucket through scene19; Papa introduces another at scene20. The open U-shaped canal is installed from scene34 through scene122, then dismantled in scene123 (R17 page167). A close-up can hide the canal; it must not be arbitrarily added into every crop. Two round windows and the solid green front door belong to the front facade; interior doors in a reverse kitchen view do not become garden exits.

Papa is clearly adult and broad, with a rounded short muzzle. Scooby retains the mounted silhouette and occupies most of the kitchen floor when indoors. Infant PomPom is a whole separate supported body. Humor comes from plans meeting surprising consequences, energetic family responses and earned pauses; neither fatigue nor a fixed cheerful expression substitutes for action.

There are six current magical complications. The old twelve-challenge outline is historical. Twelve ducks is a cast count.

## Panorama example

The [two-reference example](../../../tools/studio/examples/panorama-example.json) uses the successful assembled kitchen panorama as a projection and continuity guide, and a separate Elder/forest reference for place identity. Generate one continuous 2:1 equirectangular image, inspect it in the viewer, repair registered perspective views if needed, then export the cubemap deterministically.

This does not mean generating six independent faces. It also does not guarantee a flawless one-shot result or metric camera translation. The [documented panorama workflow](../panorama-workflow/README.md) records the actual successful method and its limits.

## Storage and recovery

Use the Mini SSD for Studio state, native assets, jobs and rendered boards. Git tracks text, prompts, catalog hashes and restore recipes; heavy media stay in content-addressed archives.

The R17 [restore contract](bath-magic-20261002-r17/RESTORE.txt) and scoped archive manifest restore the full reader and its before/after baseline to regular portable files. Historical records retain original machine paths as provenance. Two recovered opening candidates (03l/03m) explicitly disclose an inferred native-to-tool-output association; this uncertainty must not be relabeled as exact tool trace.

For a new machine, restore the catalog source packs, pass `--root NAME=PATH` overrides to the importer and run `--dry-run` first. Every asset SHA is checked before import. A nonempty Studio project is protected unless `--replace` is explicitly requested; the normal UI preserves ongoing work.

Localized cover lettering belongs on the full-bleed artwork. The miniature is a separate text-free image. Published PDFs include three coloring pages. R17 remains a review draft, so its PDFs and official publication were not regenerated.
