# Character creation

Deliver a coherent character reference package through the conversation: one prototype, a useful review loop, coordinated studies, and a unified sheet. Keep the result visible in chat rather than requiring an unrelated chapter or administrative screen.

## Start from the request

Read the character dossier, current entity and registered references. Inspect the actual reference images. Separate established identity and scale from proposed details: age, face, silhouette, proportions, colors, asymmetry, clothing and movement abilities.

Discuss only the missing choices needed for a useful first draft. An ordinary request to make a character authorizes its first exploratory prototype; it does not need a second “go ahead,” a complete chapter plan, or an approval button. Make routine framing and presentation choices within the request. Keep original art intact.

For PinPin, retain the warm dimensional book style and readable staging for a four-year-old. An infant needs plausible support, distinct limbs and age-appropriate actions; do not invent independent standing or walking from a seated reference.

## Make and show the prototype

Use an actual image-generation or editing tool. Start with a clear single view that shows the face and whole body; use a restrained background. Reuse the registered identity and scale references rather than repeatedly rediscovering them. Keep a concise record of the exact submitted prompt and reference IDs/hashes.

Copy the native output into external Studio storage without conversion, register it as a candidate, and show that registered image in chat. A family reference is an input, not a substitute for the requested new character image. A queued job, proposed control or tool helper display is not a delivered candidate.

Where the user requests an iterative workflow, offer:

- **Edit:** make the specified change, preserving identity and other successful details. Record a prior job as `retryOf` only when it is actually being revised.
- **Confirm design:** use this candidate as the working identity for the next requested stage. Record who confirmed and what that confirmation covers.
- **Exit:** stop further generation; retain the dossier, candidates and decisions.

The review checkpoint follows the first visible candidate. Do not insert another permission step before it. If the user explicitly delegates review to a representative, that representative can make decisions within the delegation; record them as delegated decisions, not as personal review or button clicks by the user.

## Expand the working identity

After a requested prototype-review checkpoint is satisfied, execute the remaining authorized package. Do not ask again whether to do work the user already requested.

Use a small number of coordinated multi-view sheets when that reduces turnaround time without making the views unreadable. A useful arrangement is one face sheet for perspectives and expressions, and one body sheet for perspectives and gestures. The exact coverage follows the request and the character's abilities.

| Group | Typical coverage |
| --- | --- |
| Face views | Front, distinct left/right three-quarter, profiles, rear head |
| Expressions | Neutral, curious, happy, surprised, sleepy, mild upset |
| Body views | Front, distinct three-quarter directions, side, back |
| Gestures | Age-appropriate reaching, clapping, waving, holding or resting |

Keep identity, eye/muzzle/ear shapes, quill or hair treatment, relative scale, lighting and style consistent. Vary expression naturally; a forced smile or raised eyebrows in every cell is not an expression range. Do not silently mirror asymmetric details or mislabel duplicate orientations as different views.

Inspect the source sheets before composing the final reference. Check anatomy, separate limbs, support, full-body framing, readable actions and identity drift. Correct meaningful defects with targeted edits. Retain rejected or superseded versions and record why a replacement was selected; do not repeatedly regenerate successful material merely to make progress appear visible.

## Deliver the composite and records

Assemble a real readable image with labeled face, expression, body and gesture sections. Keep consistent scale within each group and enough space to distinguish views. Preserve the source sheets. Register the composite separately and show it prominently in chat alongside the source sheets.

The package is concrete when the requested studies and composite exist, are registered and viewable, and their provenance and review decisions are recorded. Do not require a further administrative click to call the requested draft package delivered. If the user requested a final review, honor it at that point.

Keep distinct:

- Permission to make a reversible draft.
- Working-design confirmation, including a specifically delegated review.
- Technical or visual QA of an output.
- Studio artifact review status and explicit selection as an entity/story reference.
- Permission to publish.

Never fabricate approval metadata or silently replace existing approved references. Follow an explicitly reviewed plan when supplied; its version/hash documents that review rather than imposing a universal prerequisite on exploratory work.

## Current inline card: implemented behavior

The current renderer accepts a JSON object inside a `ui` fenced block. This example uses an asset from the [PomPom run](examples/mr-pompom.md); substitute the actual registered candidate ID when reusing it.

```ui
{
  "type": "WorkflowCard",
  "title": "Character — prototype",
  "text": "Review identity, proportions and the supported pose.",
  "assetIds": ["asset-463aeb445b75c551fad7414b"],
  "actions": [
    {"label": "Edit", "message": "Edit this prototype: "},
    {"label": "Confirm design", "message": "I confirm this prototype as the working design. Continue the requested reference package."},
    {"label": "Exit", "message": "Exit this character workflow for now."}
  ]
}
```

The supported fields are `type: "WorkflowCard"`, string `title`, optional string `text`, optional `assetIds`, and an `actions` array. At most four registered images are displayed and at most six actions are accepted. An action has string `label` and `message`; messages longer than 4,000 characters are excluded. Missing assets are not fabricated. Invalid JSON or unsupported card structure stays visible as ordinary text.

Action buttons prepare a normal composer message; the user sends it. They do not independently submit generation, record approval, mutate workflow state or select references. Use `actions: []` for a completed result without further choices: the renderer omits the option-selection hint and empty action bar. The card is a presentation layer, not a new action API. See the actual [renderer](../tools/studio/web/workspace-dev/workflow-card.js).

Each registered card image has an **Open full-size** button. The modal [image viewer](../tools/studio/web/workspace-dev/image-viewer.js) starts at original pixel size with scrolling. **Fit to window** switches to an overview; **Original size (100%)** switches back. **Close** or Escape returns to the conversation and restores focus to the image button. The viewer reads the registered original through the existing media bridge; it does not alter the artwork. Closing or suspending the frame releases its Blob URL. Inspect multi-view sheets at full size before judging small details.

The viewer is implemented in the ready workspace build `e13edd4de644de7a2744d58f41472ca0062797589b9647d217f01d67f0df44db`. Source matching, syntax checks and focused renderer assertions passed; independent headful Chrome verification passed all 12 checks at 2026-10-03 09:22:47.605 UTC: original 1024 × 1536 display, scrolling, Fit/100% switching, Close/Escape and focus return, actionless-card footer removal, intact split layout and zero JavaScript errors.

Earlier sketches such as `CharacterReview { ... }`, typed workflow objects or declarative actions like `confirmDesign` are future proposals, not the implemented protocol. Keep such proposals out of working examples unless they are explicitly marked as unimplemented.

## Evidence and latency

Keep the dossier, exact prompts, registered input/output IDs, full hashes, native file locations, actual tool names, targeted revision lineage and attributed review notes together. Use local registered metadata and existing references; avoid repeated context scans, oversized duplicated attachments and unnecessary generation calls. Parallelize independent face/body studies only when the available tool path supports it, then review the combined result for consistency.

Report actual stage and results briefly. If generation is unavailable, identify the missing capability honestly and complete independent authorized work; do not disguise tool unavailability as an approval requirement.
