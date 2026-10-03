# Conversation Studio preproduction contract, version 1

This is a versioned declarative preproduction workspace. The project remains the
source of manuscript, chapter, scene, continuity, character, place and reference
intent. Conversation requests bind that intent to immutable job snapshots;
artifacts and user review remain separate from publishing.

## Spaces and motion

`GET /api/media` lists registered panorama references and a small fixed archive
allowlist. The allowlist pins exact file IDs, filenames and SHA-256 identities;
`/api/media/files/{id}` never accepts a filesystem path. Missing or modified
archive files are omitted with an explanatory note. `POST /api/media/import`
registers only a fixed allowlisted image after hash verification. Spaces review
then attaches its actual immutable image asset, including for fresh installations.
Video selection carries explicit metadata and asks for extracted-frame inspection;
it is not presented as a native video attachment. The backend serves video
with byte ranges. A range does not bypass hash verification.

`web/media-workspace.js` exports synchronous `renderSpaces(container, options)`
and `renderInsights(container, options)`; each returns a cleanup function.
Options include `state`, `lang`, `request(url, options)`,
`selectContext({type,id,label})` and `compose(text)`. Requests run asynchronously
and discard their results after cleanup. Mount the corresponding stylesheet.

The existing native panorama viewer now accepts an optional mount container and
returns cleanup. Equirectangular 2:1 assets use spherical UV coordinates; only
the explicitly declared `cube-atlas-3x2` archive format uses face projection.
That atlas is `[front, right, back; left, up, down]`, using the face bases recorded
in the archive export manifests. Unknown image projections remain flat previews.
The fixed viewpoint can rotate; this does not establish measured geometry.

The retained tractor orbit is the reviewed 12.041667-second, 1280×720,
24-fps all-intra derivative. Drag and slider navigate the actual video.
Progress is along one camera path, not measured azimuth or free movement.
Documented uneven pacing, detail drift and the visible endpoint join are exposed.
No image, video or paid model call is made by browsing or preparing a request.

`kind: cubemap` still requires TWO distinct registered images with roles
`seamless-panorama` and `location-identity`. `kind: orbit-video` creates a real
queued agent handoff with exact bound references and instructions for preserving
the original video, recording provenance and reviewing the whole circuit. The
current completion API accepts text/image artifacts; an orbit worker returns a
text manifest and a reviewer must explicitly register any new video before it
is served. The UI does not claim an automatic video generator is connected.

## Evidence and retries

`GET /api/insights` counts the current Store ledger only. It reports status
counts, failure/rejection hotspots, and claim-to-terminal observed durations.
Explicit `historicalRegistration: true` jobs and the existing `Register already-generated `
registration declaration are excluded from timing, with the exclusion count shown.
These durations include agent work and must not be called provider generation
times. Missing timestamps remain unknown. Imported assets are not generation
calls, and no historic billing or attempts are inferred from archive filenames.

Creating a job can carry `retryOf` naming an existing job (an illustration-to-edit revision may change kind). Only these
explicit links count as retries. Older unrelated jobs sharing a scene are never
relabeled as retries. A multi-scene job can contribute to several target
hotspots; this is documented alongside the table. Rejections use current
artifact decisions, while the ledger retains the review events.

## Execution exception and verification

The coordinator used native subordinate agents after Mission Control lane
creation reported `agent_pane_busy`; this fallback is recorded here rather than
presented as the normal fleet interface. Work is isolated to the copied Studio
source and external conversation data directory, not the running original data.

`tests/test_insights_media.py` covers explicit lineage, missing timing, archive
checksums, traversal and symlink rejection, projection classification and orbit
handoff behavior. HTTP range and conversation tests are owned by the backend
lane. Browser checks must exercise actual panorama/cube pixels, video seeking,
mobile layout and cleanup; a syntactic check alone is insufficient.

Verified on Mini sidecar http://127.0.0.1:18826 (Air tunnel http://127.0.0.1:18825): eight focused tests, actual Chrome panorama/cube rotation, video seeking with206 byte ranges, correct image attachment and390px mobile layout. Six-direction cube-to-sphere screenshot differences averaged0.587–1.178 RGB levels out of255, confirming declared projection mapping. This checks the renderer, not new visual approval of archived art. Evidence is retained in the external pinpin-studio-conversation-20261002 report directory.

## Editable business logic and durable conversation

The configured business package owns normal context/attachment selection and exported application
rules. The immutable conversation kernel calls `BusinessRuntime.invoke("selected_context", store,
body)` for each send, holding that invocation's version while it assembles context. Valid source
changes activate within the same server process; syntax, API or self-test failures keep the previous
working package. An invocation failure rolls back without replaying side effects.

Agent policy v4 explicitly supersedes historic blanket backend bans for the configured business
source. Its exact directory joins the data and UI writable roots. Transport/thread protocol, durable
transcript machinery, Store persistence, origin/authority checks and immutable builds remain
protected. Historical project review stays read-only across every root. Trusted policy injection
migrates the existing thread; it never fabricates a user message or resets the transcript.

This is capability plumbing only. Normal attachment selection and keyboard behavior are preserved;
the agent implements later user-requested rules through the editable source and reports the actual
active hash. Comic preproduction approval does not gate business development.

If no valid business package remains, minimal kernel context keeps chat usable for repair. It
contains the validated raw request, selection identifiers, authoritative revision/review state and
explicit registered attachments only, with a clear recovery diagnostic. Automatic business context
is omitted. Failed business calls are never replayed, and normal invalid-request errors are retained.
