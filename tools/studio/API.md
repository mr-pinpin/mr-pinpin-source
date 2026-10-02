# Studio API v1

Local server: `python tools/studio/server.py --data-dir /Volumes/TB4/mac-mini-storage/shared/pinpin-studio-data --port 18806 --media-root /Volumes/TB4/mac-mini-storage/shared`.
All JSON responses use UTF-8. Errors: `{error:{code,message,details?}}` with appropriate HTTP status. Jobs/events/assets are server-owned; project saves never overwrite them. Additional project/entity/scene fields are preserved.

## State and project

`GET /api/state` returns `{schemaVersion:1,revision,project,assets:[],jobs:[],storyboards:[],events:[],config}`.
`PUT /api/state` body `{expectedRevision:number,project:object}` returns the full new state. A stale revision returns409 with `error.code="revision_conflict"` and `error.details.currentRevision`. Any successful mutation increments revision. Fetch fresh state after mutations. Saving a project validates unique IDs, scene dependency references/cycles, existing asset IDs, and referenced entity IDs. Scene order is the order of its array.

Project shape:
```json
{"id":"pinpin","name":"Mr. PinPin","book":{"title":{"en":"","ru":"","es":""},"manuscript":"","arc":"","continuity":"","styleReferenceIds":[]},"entities":[],"chapters":[],"activeChapterId":null}
```
Entity: `{id,name,kind:"character"|"location"|"prop"|"style"|"panorama",description:"",identity:"",scale:"",geometry:"",referenceIds:[assetId],reviewStatus:"draft"}`.
Chapter: `{id,title:{en,ru,es},synopsis:"",script:"",scenes:[],coverAssetId:null}`.
Scene: `{id,title:"",captions:{en:"",ru:"",es:""},action:"",dependsOn:[],castIds:[],locationId:null,propIds:[],camera:{position:"",height:"",yaw:null,pitch:null,fov:null,gaze:""},stateBefore:"",stateAfter:"",tempo:{activity:1,comedy:1,discovery:1},imageAssetId:null,status:"draft"}`. Tempo values1/2/3 are editorial low/medium/high, not measured audience responses. Captions also accept arrays of strings for imported editions.

## Assets

`POST /api/assets` uploads image bytes directly, using `Content-Type:image/png` (also jpeg/webp) and `X-File-Name:encodeURIComponent(file.name)`. Returns `{asset,revision}`. Max40MiB; decoded-image format verified. Binary uploads are immutable, content-addressed and copied to external data storage.
Asset: `{id,name,mime,sha256,bytes,width,height,url:"/api/assets/<id>",createdAt,reviewStatus,provenance}`. Native originals are retained. `GET /api/assets/<id>` serves only registered bytes; no filesystem path request is accepted. Uploaded assets default to `reviewStatus:"unreviewed"`.
Trusted local CLI/catalog importer uses `Store.import_asset(path,name=None,provenance=None,review_status="unreviewed")`; path must be below configured media roots. `Store(data_dir,media_roots=[...])`; `Store.read()` gets state, `Store.save_project(project,expected_revision)` saves. Both return JSON-compatible values. CLI `import-asset PATH` provides the same operation.

## Generation handoff jobs

`POST /api/jobs` body `{kind,chapterId?,sceneIds:[],entityId?,instruction,referenceIds:[],referenceBindings:[{assetId,role,entityId?}]}` returns `{job,revision}`. Kinds: illustration,edit,cubemap,story-plan,character-study,location-study,title-cover,miniature,coloring. Jobs are **queued, waiting for a Codex agent**; the server never calls a paid image API or invents progress.
Scene/entity character, location, prop and book/style references auto-attach with explicit roles and content hashes. Explicit references supplement these. Cubemap jobs REQUIRE two distinct assets: role `seamless-panorama` and role `location-identity`; entity kind panorama/location can infer these roles. Supplying the same asset twice cannot satisfy the requirement. The immutable handoff contains the stable workflow header, exact user instruction, scene/entity snapshots, role-assigned reference hashes and absolute registered local paths for the agent. Prompt text/path/hash are retained on the job.
`GET /api/jobs` returns `{jobs:[]}`. Job fields: `{id,kind,status:"queued"|"claimed"|"completed"|"failed",chapterId,sceneIds,entityId,instruction,prompt,promptSha256,referenceBindings:[],artifacts:[],feedback:[],createdAt,updatedAt,claimedBy?,error?}`.

CLI (same data-dir and media-root flags before subcommand):
```
python tools/studio/cli.py --data-dir DATA --media-root ROOT jobs
python tools/studio/cli.py --data-dir DATA claim JOB_ID --agent codex
python tools/studio/cli.py --data-dir DATA --media-root ROOT complete JOB_ID --agent codex --image /absolute/native.png --scene-id scene-01 --visual-pass
python tools/studio/cli.py --data-dir DATA complete JOB_ID --agent codex --text-file /absolute/plan.txt
python tools/studio/cli.py --data-dir DATA fail JOB_ID --agent codex --reason "..."
python tools/studio/cli.py --data-dir DATA reply JOB_ID --agent codex --text "..."
```
Completion requires a matching claim and preserves immutable image/text artifacts. Text files are explicit trusted CLI inputs. Image artifacts `{id,type:"image",assetId,sceneId?,sha256,agentVisualPass,reviewStatus:"candidate",createdAt}`; text artifacts have `type:"text",text,sha256`. An agent's visual pass is separate from user approval.

`POST /api/jobs/<id>/review` body `{decision:"feedback"|"approve"|"reject",feedback:"",artifactId?}` returns `{job,revision}`. Approval requires a named artifact. For an image with a scene target, approval selects its imageAssetId on that scene and retains the prior selection in `imageHistory`. Entity jobs add the approved image to entity.referenceIds. Text approval records approval but does not silently rewrite the manuscript. Before/after IDs remain in the history. No review action publishes to the official site.

## Storyboard sheets and feedback

`POST /api/storyboards` body `{chapterId,panelsPerPage:6|12|24,language:"en"|"ru"|"es"}` returns `{storyboard,revision}`. Storyboard: `{id,chapterId,language,panelsPerPage,createdAt,pages:[{id,assetId,url,index,panels:[{sceneId,index,caption,imageAssetId,box:[x,y,w,h]}],reviewStatus:"unreviewed",feedback:[]}],snapshotSha256}`. It renders real immutable PNG sheets with labels/captions and placeholders for missing images; an empty chapter is rejected. Caption snapshots and selected image hashes are saved alongside the PNGs.
`POST /api/storyboards/<id>/review` body `{pageId,sceneId?,decision:"feedback"|"approve"|"reject",feedback:""}` returns `{storyboard,revision}`. With sceneId it records panel feedback, otherwise page feedback. Reviewing a contact page does not automatically approve unseen final image candidates.

## Safety and persistence

Loopback only. Mutation requests reject nonlocal/mismatched Origin headers. Native files are served by registered IDs only; path traversal rejected. JSON persistence uses cross-process locks, atomic replace, fsync and optimistic revisions. All external media imports must resolve within allowlisted roots, including symlink resolution. Config reports only supported languages/kinds/panel counts and queue semantics. Data, uploaded/generated images and contact sheets live outside Git.
