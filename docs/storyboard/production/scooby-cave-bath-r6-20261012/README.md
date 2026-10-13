# Scooby cave-and-bath revision: 216-page edition

Completed 215 narrative scenes plus localized title, in English, Russian and Spanish.
Release target: https://mr-pinpin.github.io/chapter-scooby-bath/storyboard/?story=scooby-bath&lang=en
Publication is complete only after the selected deployment is verified.

- [Overview](OVERVIEW.md): four-day story, subplots, cast roles and magic rules.
- [Ordered beats](BEATS.md): 215 narrative scenes plus localized title, matching Bath Magic's 216 reader pages.
- [Continuity](CONTINUITY.md): item counts/holders, infant handovers, dirt and explicit water start/stop states.
- [Acting and review](ACTING-AND-REVIEW.md): facial registers, audit findings and production gates.
- [Object inventory](OBJECTS.json), [cast coverage](CAST-COVERAGE.json), [machine-readable beats](BEAT-PLAN.json).
- [Causal flow](causal-flow.mmd).

The original `create-preproduction.py` scaffold predates the final editorial adjustments; do not overwrite the final beat plan. It produces planning
material, never selects assets or changes the reader. All215 EN/RU/ES captions and individual camera/acting/object directions are
authored in [the script](script/english-reading.md) and [director data](script/story-script.json).
[Subplots](SUBPLOTS.md), [cast](CAST-BIBLE.md), and [editorial decisions](EDITORIAL-DECISIONS.md) guide the new version.
Symbolic continuity checks and full visual selection are complete.
207 new narrative masters, six deliberate environment views and two unchanged approved book images form the narrative. Superseded R4 smiling/boat studies and R5 short outline are not selected.

## Reading-size feasibility study

The existing full release is approximately 928.4MB; its current Scooby media is
12.27MB. The fixed 950MB cap leaves roughly 33.8MB for replacement chapter media
and additional text. Existing book artwork must remain byte-for-byte preserved.

A preliminary AVIF test on three unpublished R4 masters at their native1536×1024
size produced 125036,144745,155218 bytes at quality55 (Pillow12.3.0). Quality60:
149316,173351,185953 bytes. These are measurements, not a quality approval or a
chosen format. Adding768×512 JPEG quality82 fallbacks would cost another
102661,119893,127842 bytes per tested picture, exceeding the planned budget.

Codec study and outputs are local external cache at
`/root/.local/share/pinpin-production/scooby-cave-bath-r6-20261012/codec-study/`.
No R6 art was generated in this feasibility study. Before art batches, visually
review representative new cave/forest/house masters and determine suitable
reading variants and fallback costs within the cap. Do not raise the cap or
recompress the older book to conceal an unresolved budget.

## Restore the working review

After restoring production references with `npm run assets:restore-production`,
restore this pack's scoped archived natives with standard HF tools:

```sh
python3 tools/assets/hf_store.py pull --manifest docs/storyboard/production/scooby-cave-bath-r6-20261012/environment/asset-scope.json --root . --profile all --cache /path/outside/checkout/pinpin-cache
```

Serve `docs` locally and open `storyboard/production/scooby-cave-bath-r6-20261012/environment/review.html`.
This working review is excluded from official Pages artifacts. Exact submitted
prompts are in `prompts/`; all native outputs are retained, including rejected
studies. `generation-records.json` records hashes/statuses/tool originals; built-in
imagegen was used, no paid CLI/API fallback.

## Final production

Built-in image generation produced the selected native masters in `native/`;
individual prompts, geometry/style references and hashes are recorded in
`prompts/` and `generation-records.json`. Native files are retained locally and
preserved by the verified V7 archive receipt. `reader/selected-masters.json`
records the exact selections; `reader/production-manifest.json` records the
WebP reading derivatives. No prior approved book image was changed.

The scoped chapter artifact contains 216 pages, 1440×960 reading illustrations,
localized titles and a responsive miniature. Desktop/mobile browser checks pass
in all three languages with two or three initial image requests, lazy loading,
late-scene navigation and no Hugging Face requests for ordinary reading.
PDF exports preserve native image dimensions and selectable localized text;
new immutable PDF objects do not replace older edition objects.

House pictures follow published illustration references; they are not certified
measured geometry renders. The earlier R4/R5 studies remain preserved separately.
