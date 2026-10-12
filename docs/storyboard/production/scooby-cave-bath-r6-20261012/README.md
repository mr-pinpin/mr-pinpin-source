# Scooby cave-and-bath revision: preproduction

This is the new authoring direction, not a published replacement.
The existing short chapter is still the live release.

- [Overview](OVERVIEW.md): four-day story, subplots, cast roles and magic rules.
- [Ordered beats](BEATS.md): 215 narrative scenes plus localized title, matching Bath Magic's 216 reader pages.
- [Continuity](CONTINUITY.md): item counts/holders, infant handovers, dirt and explicit water start/stop states.
- [Acting and review](ACTING-AND-REVIEW.md): facial registers, audit findings and production gates.
- [Object inventory](OBJECTS.json), [cast coverage](CAST-COVERAGE.json), [machine-readable beats](BEAT-PLAN.json).
- [Causal flow](causal-flow.mmd).

Regenerate beat plan with `python3 create-preproduction.py`. This produces planning
material, never selects assets or changes the reader. All215 EN/RU/ES captions and individual camera/acting/object directions are
authored in [the script](script/english-reading.md) and [director data](script/story-script.json).
[Subplots](SUBPLOTS.md), [cast](CAST-BIBLE.md), and [editorial decisions](EDITORIAL-DECISIONS.md) guide the new version.
Symbolic continuity checks pass; visual production and editorial proofing continue.
The revised chapter has not been published. Superseded R4 smiling/boat studies and R5 short outline are not selected.

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
