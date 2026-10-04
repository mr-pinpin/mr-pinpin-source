# Compact location discovery and reference hydration

This workflow supports ordinary authorized Studio requests for locations, rooms,
viewpoints, furnishing/eye-height variants, and illustrated connections. It
indexes existing evidence; it does not create artwork, publish stories, or
change Studio's media allowlist.

Use the persistent index outside the source checkout. Run `index` in a worker
when source metadata changes; never run a cold restore from UI paint or a
metadata query. `query` is offline and read-only. Its JSON records exact source
identities, reference roles, review evidence, cameras, fixed-node connections,
selected panorama stacks, generation/projection recipe paths and missing media.
Default metadata queries do not stat/open media (`availability: not-probed`).
Use `--probe-media` in a worker for availability/missing checks. Availability is
not proof of content identity: hydration verifies SHA-256 and
byte count before use.

```sh
python3 -B tools/studio-locations/cli.py --root SOURCE --index DATA/cache/location-index.json index --studio-data DATA
python3 -B tools/studio-locations/cli.py --root SOURCE --index DATA/cache/location-index.json list
python3 -B tools/studio-locations/cli.py --root SOURCE --index DATA/cache/location-index.json query bathroom
python3 -B tools/studio-locations/cli.py --root SOURCE --index DATA/cache/location-index.json query tour/bath/child --scope all
python3 -B tools/studio-locations/cli.py --root SOURCE --index DATA/cache/location-index.json query world/elder
python3 -B tools/studio-locations/cli.py --root SOURCE --index DATA/cache/location-index.json query tractor/orbit --stop stop-14 --scope all
```

Choose an exact ID from `list`. Unknown IDs, nonexistent viewpoints and invalid
stop numbers return exit 2 with a structured `location_request_rejected` error.
Do not invent a room or silently choose a nearby one. `approved` selects actual
approved/published book references plus explicitly labelled workflow context;
`all` exposes selected study/candidate assets with their distinct status.
An asset hash, archive backup or source filename never proves visual approval.
Visual-direction approval is not a publication grant.

For a generation request, hydrate a few relevant book images and **one** good
projection/style reference. Supply them separately with their exact roles:
book images establish the requested location/object design; the panorama
teaches spherical format and finish. Prevent its kitchen/doors/furniture/floor
layout from migrating into a new forest, lake or Elder scene. A successful
projection is not a room-layout donor.

```sh
python3 -B tools/studio-locations/cli.py --root SOURCE --index DATA/cache/location-index.json hydrate world/elder --output DATA/requests/elder-001 --max-bytes 33554432
```

The default verifies/copies local bytes and writes a request manifest, hydration
receipt and **only the missing requested objects** in `restore-manifest.json`.
For an ordinary authorized generation request, the agent may automatically use
`--restore --cache DATA/cache/location-media` to retrieve those bounded needed
references. This flag is an internal workflow choice, not a new human permission
step. Keep it off the interactive paint path. Do not download a whole archive.
The existing verified `tools/assets/hf_store.py` adapter owns legacy transfers.
Existing Studio shared replica hash IDs/registered logical IDs are reused when
available; this workflow never creates another store, forges native-imagegen
provenance, or enqueues deterministic sheets as generated originals.

`--media references` is the small generation context bundle. `--media selected`
adds the chosen live stack. `--media all` includes the returned query inventory;
use `--scope all` consciously for review candidates. Every bundle is capped by
an explicit byte budget and file count; exceeding it returns a rejection before
copy or network. Outputs/caches must be external, traversal-free and nonsymlinked.
Conflicting source/catalog identities are refused, not repaired silently.

The canonical house has three measured rooms. Its hall view is a camera within
the common room, not a fourth room. Image-led common↔bathroom and
common↔bedroom connections are fixed viewing-node transitions, not measured
continuous travel; there is no invented direct bathroom↔bedroom route. Low-eye
variants are artistic reconstructions, not metric camera translations.

The 24 tractor stops are video-derived visual samples at recorded frame/time
positions, not uniform measured 15-degree orbit geometry. Their fit/source
camera differs from authored guide camera; both are retained. `reviewed` and
experimental source-lock status remain separate. Catalog discovery does not
mean every stop is already wired into Studio's fixed media allowlist.

Run focused tests with `python3 -B -m unittest discover -s tools/studio-locations/tests -v`.
The sprint report records actual timings, metadata sizes, source hashes and
sample manifests; targets are not promises.

## Cold index across remote storage

Run a cold index explicitly in a background worker using `index_job.py` rather
than putting a rebuild on any query path:

```sh
python3 -B tools/studio-locations/index_job.py --root SOURCE --catalog EXPORTED/workflows/locations/catalog.json --index DATA/cache/location-index.json --diagnostics HOME/tmp/location-index-diagnostics --timeout-seconds 180
```

The worker reads only catalog-declared metadata/recipe dependencies and follows
selected tractor records. Binary filenames are filtered before file stats; each
changed metadata document is read once and hashed from those bytes. Warm scans
reuse document fingerprints. No recursive artwork directory survey is needed.

Diagnostics belong on responsive native storage: the latest phase, path,
counts and elapsed time are saved once a second; faulthandler stack traces are
saved every ten seconds during a stall. The supervisor stages a complete
candidate beside the live cache and publishes it by one atomic rename. On a
structured `index_timeout` (exit 3) or failed/incomplete scan, the prior cache
remains unchanged and queryable. Candidate paths are reported for inspection;
no artwork or original cache is evicted. Retry the explicit job after correcting
the diagnosed filesystem path. Do not automatically rebuild on `query`.
