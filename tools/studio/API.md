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

`POST /api/jobs` body `{kind,chapterId?,sceneIds:[],entityId?,instruction,retryOf?,referenceIds:[],referenceBindings:[{assetId,role,entityId?}]}` returns `{job,revision}`. Kinds: illustration,edit,cubemap,story-plan,character-study,location-study,title-cover,miniature,coloring,orbit-video. Jobs are **queued, waiting for a Codex agent**; the server never calls a paid image API or invents progress.
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

## Live conversation

The local Studio owns a persistent, separate Codex app-server thread using the Mac mini's existing Codex login. It does not inherit another ChatGPT conversation. No API key or account token is sent to the browser. If login is stale, Studio reports a real error; it never substitutes a canned assistant response.

- `GET /api/conversation?after=0`: `{conversation,events,cursor}`. Conversation includes `id,threadId,status,messages,activeTurnId,error,model,usage,plan`. Status is idle/connecting/running/interrupting/interrupted/completed/error.
- `POST /api/conversation/messages`: `{text,chapterId?,sceneIds?:[],entityId?,assetIds?:[]}`, returns202 with the same envelope. One active turn; a second returns409 `conversation_busy`.
- `POST /api/conversation/interrupt`: `{}`, requests actual upstream turn interruption and returns the same envelope. It also cancels a turn while connecting.

Poll about once per second. Every response contains the full accumulated transcript; replace message snapshots rather than appending them. Message fields: `id,role,text,status,createdAt,turnId?,context?,phase?`. Assistant text is actual model output. `after` filters incremental events only; `cursor` is monotonic. Events include message/delta/status/usage/plan/activity. The last1000 events are retained; full transcript remains durable. Raw reasoning, commands, command output, credentials and upstream error payloads are not exposed. `usage` is null until supplied by Codex, then its actual `{total,last,modelContextWindow}`; costs are not inferred.

References must be registered assets. Explicit refs and selected scene images take priority, followed by relevant entity/style refs (at most12 native local images). Context includes exact project revision, scoped scene/entity details, compact chapter scene index, and plan approval status. Long manuscripts remain available to the agent via Store. Transcript/thread IDs persist in external data `conversation.json`; restart marks unfinished turns interrupted, and next message resumes that thread.

The agent writes only inside the external Studio workspace, with network access disabled for local shell tools. It can use Studio Store/CLI to make user-requested draft changes and register real outputs. Published source content is outside its writable workspace. It must not publish, modify human approvals, or pretend queued image jobs have rendered. Production execution requires a matching human-approved preproduction plan. Available tools and login determine whether actual image generation can run.

## Preproduction approval

`GET /api/plan?chapterId=ID` returns `{chapterId,sha256,approved,approval}`.
`POST /api/plan/approve` accepts `{chapterId,expectedRevision}` and returns the full updated Store state. Approval is stored as `chapter.studioPlanApproval={sha256,approvedAt,baseRevision,scope:"preproduction"}`.

The server hashes canonical UTF8 JSON containing chapter script/synopsis, ordered scene planning fields (captions/action/dependencies/cast/location/props/camera/state/tempo), referenced entity identity/scale/geometry/reference IDs, and book style references. Changing any of those invalidates approval. Output image selection/status and job progress are excluded. This is human approval of preproduction only; image review and publication remain separate.

Protocol reference: [official Codex app-server documentation](https://learn.chatgpt.com/docs/app-server). The installed CLI-generated schema determines exact wire enums.

## Media and observed insights

`GET /api/media` lists registered panoramas and fixed hash-pinned archive entries, with exact IDs, names, kinds, projection, source URL and review notes. `GET`/`HEAD /api/media/files/<id>` serves only those allowlisted files; video supports single byte ranges (206, or 416 when unsatisfiable). No client filesystem path is accepted. Missing archive entries appear as notes, not dead links.

`GET /api/insights` reports recorded job counts/statuses, explicit retry links, observed claim-to-terminal ledger intervals and target failure/rejection hotspots. Durations exclude explicitly declared already-generated registrations; missing timing and older retry lineage remain unknown. These are not provider generation-time or billing estimates. Imported images are not inferred calls.

New revision jobs can supply `retryOf: previousJob.id`. The parent must exist; an explicit revision can change kind, such as illustration to edit. The legacy request-revision action records this link. Sharing a scene or similar instructions never establishes retry lineage.

`orbit-video` creates a queued handoff for the documented source-still/video workflow, with immutable references and prompt. It does not invoke a paid video service. The worker completes with a text manifest retaining native video identity and review evidence; a reviewer must register new media before it is served. `cubemap` retains its separate successful panorama and location-identity reference requirement.

`POST /api/media/import` accepts `{id}` for a fixed allowlisted archive image. It verifies the pinned hash and registers immutable image bytes, returning `{asset,revision}`. Repeated imports reuse the same asset and revision. Video IDs and filesystem paths are rejected. Spaces uses this action before attaching an archived image to conversation; videos are selected as metadata for explicit frame-based inspection.

## Stable runtime, evolving workspace, and pinned review

See [STABLE-RUNTIME.md](STABLE-RUNTIME.md) for release creation, immutable build semantics, sandbox boundaries and operational commands.

`GET /api/runtime` returns `{stableRelease,workspace:{latest,previous,status,error,url},pollIntervalMs:1000}`. Build hashes are exactly64 lowercase SHA256 hex characters. `latest` and `url` retain the last valid build if new source fails validation. Status is idle/building/ready/error; error is null or `{code,message}`.
`GET /api/runtime/releases/list` returns `{releases:[{hash,url,createdAt,fileCount,bytes}]}`.
`GET /workspace-builds/<hash>/<file>` serves only manifest-registered static files with immutable caching and wildcard CORS for sandbox module imports. API/private-asset responses do not gain wildcard CORS.

`GET /api/state?revision=N` returns the closest project snapshot at or before N, replacing `project` and `revision` and adding `readOnly:true,review:{requestedRevision,snapshotRevision,liveRevision,liveCollections:["assets","jobs","storyboards","events"]}`. Those listed collections remain live. Out-of-range revisions fail. Clients must disable mutations when pinned; normal live state remains unchanged.

Conversation messages additionally accept optional numeric `projectRevision`. Context comes from the same historical snapshot selection and records `context.reviewSnapshot/context.review`. Such turns use a read-only sandbox and cannot change project/UI/business files. Live turns allow user-requested UI work inside `--workspace-source` and business Python changes inside `--business-source`, alongside the existing external data root. Instructions and sandbox scope are refreshed every turn; comic approval gates do not apply to UI improvements.

Pinned approval review: `GET /api/plan?chapterId=ID&revision=N` computes approval against the same historical project snapshot and adds readOnly/review markers. Without revision it reads the live project.

Conversation scope migration: Studio appends its trusted developer policy through thread/inject_items before turn/start when the policy hash or thread changes. It preserves the saved thread/transcript. Internal instructionPolicy metadata is not exposed in GET /api/conversation; a failed injection returns an asynchronous conversation error with code policy_update_failed and starts no model turn.

Policy version4 / reloadable business source: the configured UI source contains normal chat presentation, composer keyboard behavior and visual workspace modules. The separate configured business source contains normal Python context, attachment, plan, media and job rules. Only these explicit source roots are writable, alongside external data. Transport/thread protocol, durable transcript machinery, Store persistence primitives, origin/authority checks and immutable kernel artifacts remain protected. The trusted policy supersedes older saved-thread blanket backend prohibitions without resetting history. This policy update implements no requested attachment or keyboard behavior itself.

Conversation context assembly calls `BusinessRuntime.invoke("selected_context", store, body)` for each send. The invocation keeps its module version until it finishes; no mutable global business module is retained by Conversation. The active module may change on subsequent requests without restarting the server or Codex thread. Failed invocations are not replayed. Kernel releases exclude editable business source and must configure the runtime explicitly; direct development imports remain compatible with the source package.

The kernel derives historical-review authority from validated `projectRevision`, never from a
business-returned flag. It validates conversation input shape and bounds, permits only text plus
at most12 registered native images, and verifies each image path against Store. Invalid business
output rolls back inside the module lease; its native inputs never reach Codex. The kernel then
uses minimal recovery context to keep the conversation available, without replaying the business call.
Business policy cannot grant a historical review writable sandbox access.

When invoked from a frozen kernel, the agent CLI receives both `--business-source SOURCE` and
`--runtime-dir RUNTIME`. It reads the active verified business build without writing runtime
artifacts or relying on excluded top-level business imports.

If context assembly reports `business_unavailable`, `business_call` or `invalid_business_context`,
the kernel sends minimal recovery context containing the validated user message, selected IDs,
requested review revision and only explicitly registered attachments. It omits automatic product
context and records a bounded `message.context.contextDiagnostic` so the agent can repair business
source. Expected input errors still return400/404; no business mutation is retried. Transport,
thread history, interrupt and read-only review remain available even with no working business build.
