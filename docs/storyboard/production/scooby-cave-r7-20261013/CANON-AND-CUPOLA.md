# Underground lake beneath a cupola — author direction, 2026-10-13

The author confirmed a large underground lake beneath a cupola with an opening
at its crown, referring to Roman temples and the original PinPin book. This
supersedes the proposal's small north-rim daylight shaft. Use **one central open
oculus**, not an outdoor lake with a roof framing the sky, a glass greenhouse
cap, or multiple improvised skylights.

## Original book connections actually checked

Source: `docs/storyboard/book.json`, preserved full original manuscript, source
SHA256 `07bf4433d51b7236ff2db5f15b717d15129b9d7c7f1e61aaa4eca7e55d7f0114`.
The original chapter numbering differs from the expanded reader's chapter menu.

| Original chapter | Existing story fact | Use in this revision |
| --- | --- | --- |
| 1 | Lulu reports Crystal Lake dry; PinPin's golden-quill circle brings water up from the ground. | PinPin has a real remembered water skill. Do not retcon his help into stealing a god's cloud. |
| 21 | A council proposes a large circular opening for daylight. PinPin proposes an underground cathedral and seeking the old hedgehog's magic; Papa protects their magical secret. | Overhead light and cathedral-like subterranean space are already in the book's imagination. |
| 25 | Squirrels secretly provide glazed light and plants; PinPin wonders whether squirrels have their own magical elder. | A plausible initial explanation: squirrel builders or another forest neighbour. This is a hypothesis, not proof of Veles. |
| 26 | The chamber appears to grow overnight; Father and child notice changed distances and ceilings. | PinPin knows an ordinary-looking underground place can conceal extraordinary scale. |
| 28 | PinPin explores left, returns toward central overhead light, then explores right. | Use a central light landmark to make navigation legible; show the return before changing direction. |
| 29–30 | He investigates the unexplained nocturnal light and meets the squirrel elder amid fireflies. She describes the result as their cooperation. | Discovery follows observation and investigation, with a physical character encounter. Preserve the squirrel contribution and Elder's established identity. |

The relevant original image inputs are inspected and hash-recorded in
`geometry/references.json`:
- `docs/images/image83.png`: crafted underground cathedral vaults and overhead
  light, original chapter21. Scale/rhythm reference, not a requirement to copy
  its multiple floors, columns or cast.
- `docs/images/image12.png`: deep round planted chamber, hanging growth and light
  above, original chapter25. Material/planting reference, not the new layout.
- `docs/images/image67.png`: central opening viewed upward, great depth and
  suspended planted edges, original chapter26. Dome/light/scale inspiration,
  without copying its wooden walkways or vegetable crates.

Do not imply these chapters say Veles made the caves. The Veles connection is
new author-directed fiction requiring new evidence. The squirrel-elder scene
prevents casually attributing every existing underground wonder to the hedgehog
Elder or rewriting cooperation into deception.

## Cupola and light contract

The Pantheon analogy supplies an oculus admitting a moving patch of daylight:
https://cultura.gov.it/evento/magia-di-luce-il-pantheon-e-la-fondazione-di-roma-natale-di-roma-al-pantheon

The current geometry pilot has an authored 21.6m internal diameter, a 13.3m
maximum internal height, and a 4.4m diameter crown opening. These are working
fictional dimensions, not measurements recovered from a book illustration or
copies of the Pantheon. The lake is an ellipse16×12m; its water lies0.35m below
the broad dry annular shore. The hillside encloses the cupola. Surface ground
over the crown is higher than the side entrances: the approach remains a gentle
horizontal hillside route, with no invented stairs or deep-pit dog rescue.

Daylight enters through the central aperture and reflects in the lake. West/east
vine lights stay in fixed positions, so shaded banks remain readable. Rain can
fall through the opening; no endless waterfall or magical water source is
inferred from the hole. A reflection/patch shifts with time, while the aperture,
bank, openings, occluding screen and vine groups never move between shots.

## The reveal earns its space

1. A damp blossom/draft brings Scooby back to the old digging place.
2. A gallery shows recognisable trained plants; PinPin recalls the older garden.
3. From before the stone screen, the lake is hidden but a higher echo and returned
   light suggest more space. An insert follows the light on a wet root.
4. The camera and children explicitly pass the same screen onto the dry bank.
5. First show the water and far bank, then follow a reflection upward to the dome
   and central opening. Let scale register before an explanatory conversation.
6. Only after orientation, inspect the worked outlet and caretaker traces. The
   characters' initial squirrel explanation can fail on concrete evidence.

Room-wide joy, absorbed looking, a child's upward eyeline and the dog's busy
nose are different performances. Concern is reserved for a real obstacle, such
as an overlarge gate adjustment or unsafe footing.

## What is built versus still proposed

`geometry/rotunda-plan.json` and its builder create one real editable blocking
scene. The reusable `tools/locations/` renderer executes saved before-screen,
reveal and reverse jobs and one six-view cubemap job. Actual mesh ray probes
check that a selected lake point is hidden before the screen, visible after it,
and that a ray can pass through the central oculus. Those probes establish the
tested rays, not every pixel of the story image or structural engineering.

An illustration or 360° candidate must retain these claims under visual review.
The full branching cave network remains a plan; this first scene models the
lake chamber and its three exits. It is not a declaration that all R7 cameras
or translated narrative scenes have already been validated.
