## Current inline card: implemented behavior

The current renderer accepts a JSON object inside a `ui` fenced block. This example uses an asset from the [PomPom run](/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/workflows/examples/mr-pompom.md); substitute the actual registered candidate ID when reusing it.

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

Action buttons prepare a normal composer message; the user sends it. They do not independently submit generation, record approval, mutate workflow state or select references. Use `actions: []` for a completed result without further choices: the renderer omits the option-selection hint and empty action bar. The card is a presentation layer, not a new action API. See the actual [renderer](/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/web/workspace-dev/workflow-card.js).

Each registered card image has an **Open full-size** button. The modal [image viewer](/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/web/workspace-dev/image-viewer.js) starts at original pixel size with scrolling. **Fit to window** switches to an overview; **Original size (100%)** switches back. **Close** or Escape returns to the conversation and restores focus to the image button. The viewer reads the registered original through the existing media bridge; it does not alter the artwork. Closing or suspending the frame releases its Blob URL. Inspect multi-view sheets at full size before judging small details.

The viewer is implemented in the ready workspace build `e13edd4de644de7a2744d58f41472ca0062797589b9647d217f01d67f0df44db`. Source matching, syntax checks and focused renderer assertions passed; independent headful Chrome verification passed all 12 checks at 2026-10-03 09:22:47.605 UTC: original 1024 × 1536 display, scrolling, Fit/100% switching, Close/Escape and focus return, actionless-card footer removal, intact split layout and zero JavaScript errors.

Earlier sketches such as `CharacterReview { ... }`, typed workflow objects or declarative actions like `confirmDesign` are future proposals, not the implemented protocol. Keep such proposals out of working examples unless they are explicitly marked as unimplemented.

