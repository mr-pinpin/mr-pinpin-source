# Cave revision R7 — feedback and preproduction

Status: proposed revision for review, not the published chapter. The R6 release,
its original art, caption/PDF editions and preservation records remain intact.

The author requested correct Scooby identity in the home scenes, understandable
cave navigation, circumstance-specific acting, and discovery with a causal payoff.
They proposed a luminous underground lake and evidence that Veles shaped the caves.

- [Author-confirmed cupola and original-book connections](CANON-AND-CUPOLA.md)
- [Cupola top-down and section v2](cave-plan-v2.html)
- [Fixed-camera geometry 360° and illustration candidate](cupola-360.html)
- [Twelve-shot lake reveal pilot](LAKE-REVEAL-PILOT.md)
- [Editable rotunda and recorded renderer jobs](geometry/README.md)
- [Existing-edition audit](AUDIT.md)
- [Discovery and pacing](STORY-PLAN.md)
- [Acting and reference rules](ACTING.md)
- [Earlier interactive proposal, superseded north-rim shaft](cave-plan.html)
- [Home-scene before/after candidates](review.html)
- [Layout and camera records](cave-layout.json)
- [Camera workflow](CAMERA-WORKFLOW.md)

The existing R6 top-down map is in
`../scooby-cave-bath-r6-20261012/environment/top-down-map.html`. Its C3 echo pool
is a shallow pool; L0 is an outdoor lake. It never specified the proposed large
underground lake. R7 uses new node IDs rather than pretending those are the same plan.

The identity trials use built-in imagegen with the current page as an edit target
and two approved Bath Magic dog images as anatomy references. Exact prompts,
reference hashes and unmodified native outputs are recorded here. They are
candidates; neither changed room geometry nor approval of a complete revision is
claimed. Native files remain locally retained and require verified archive receipts
before any managed ignoring/untracking. Review diagrams are authored SVG/HTML,
not generated architectural evidence. Creative content follows root content notices.

Open author decision: Veles separate from the Elder, connected to him, or his
identity? Until answered, the established Elder is not rewritten as a thief or god.

## Inspiration sources

Mojang describes lush caves with moss, azalea roots, clay pools, suspended vines
and luminous berries. R7 borrows the spatial/ecological idea, with original
PinPin illustrations, not Minecraft assets or literal block geometry:
https://www.minecraft.net/pt-pt/article/around-block--lush-caves
https://feedback.minecraft.net/hc/en-us/articles/360057761252-Minecraft-Java-Edition-Snapshot-21w10a

The supplied Perun/Veles conversation is author brainstorming, not verified
historical evidence. Its proposed motives, secret vault, eagle dialogue and
identity reversals are not automatically book canon. This revision does not
retcon the first pond restoration into theft or introduce telepathy.

## Preservation and verification

All four native correction trials and the standalone map SVG passed public
SHA-256 readback in `archive-preservation-receipt.json`; working originals remain
retained. Restore missing review media using `tools/assets/hf_store.py pull` with
`review/asset-scope.json`, source root and an external cache. The HTML/SVG map
can also be recreated with `python3 create-plan.py`; this does not alter artwork.
Seven interactive camera selections and mobile layout checks pass.
62 focused asset tests pass, one existing skip; the unchanged central production
build passes at996files /928,448,794bytes. This source update does not select a
new reader release.

## Cupola checkpoint

The author confirmed a Roman-temple-like cupola with a circular crown opening.
Original-book chapters21 and25–30 and their actual image inputs were checked.
The new rotunda is an authored metric scene using the reusable location renderer,
with a real six-face fixed-camera geometry view. `geometry/REVIEW.json` records
build/ray checks, six directions,12edge views and126browser/source ray comparisons
(maximum observed RGB error4), plus preserved legacy overscan compilation.
The shared renderer has opt-in exact90degree face coverage; previous overscan
settings keep their existing path. Two illustration trials failed geometry review
and remain rejected. The strict paint-over is a composition candidate only.

Cupola media passed readback in `archive-preservation-receipt-cupola.json`;
restore with `review/asset-scope-cupola.json`. The twelve-shot reveal pilot is
not a finished216page revision. Reflection camera H and the broader cave network
remain to be rendered. This authoring checkpoint does not replace the live R6
reader, original book, earlier PDF objects or approved images.
