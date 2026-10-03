# Stable transport kernel / editable Studio app protocol

The normal Studio interface lives entirely in `workspace-dev/`: conversation,
composer, keyboard policy, context chips, chat scroll, all workspace modes,
styles and layout. An agent can improve the chat interface in the same hot UI
build as the rest of the app. There is no normal chat presentation in the kernel.

The immutable parent keeps transport, server polling, message-send exclusion,
the authoritative draft/context, session persistence, URL validation, frame
activation, binary upload validation, and minimal recovery conversation controls.
Server-side conversation history remains authoritative. The recovery chat is
always available through Conversation and opens if no app can load.

## Envelope and lifecycle

The app loads at `/workspace-builds/<64-character-sha256>/index.html#nonce=...`.
Sandbox: `allow-scripts allow-downloads allow-popups`; never add
`allow-same-origin` or `allow-forms`. Native form submission is blocked:
editable composer controls call typed commands directly. Ordinary Enter still
inserts a newline; Cmd/Ctrl+Enter sends. That policy is editable app code.

Every message is an object with `protocol: "pinpin-workspace-v1"`, the frame's
`nonce`, and `type`. The parent validates origin `null`, source exactly matching
the active or pending frame, and its nonce. The child validates parent source,
nonce and the origin learned through init. Wildcard targeting is used only
where the opaque origin requires it, including initial boot.

Parent sends `init` after load or boot:
`{state,ui,session,apiOrigin,readOnly,...conversationSnapshot}`.
Child renders, then sends `ready` with
`capabilities: ["conversation-ui"]`. Parent retains the old app until ready,
then sends the latest route, conversation snapshot and `activate`. Activation
restores caret/focus only once; normal polling must not steal focus.
The hidden prior app receives `suspend` to stop video/GL and release image blobs.
Failure retains the last good app, or exposes recovery chat if none remains.

Old right-workspace-only builds remain compatible. Their absent capability
does not prevent loading; Conversation opens the parent's minimal chat.

## Conversation transport

Snapshot fields:
`conversation, draft, draftSeq, chatContext, pending, uploading, chatScroll,
chatFocus, chatSelection, connectionError, readOnly`.
`chatContext` is `{chapterId,sceneIds,entityId,assetIds}`.
The nullable connectionError is explicitly reset on reconnection.
The parent sends a `conversation` snapshot after transport and draft changes.

Typed RPC uses top-level fields `{type,id,...payload}`.
Replies are `response {id,result}` or `response {id,error:{message,status}}`.

- `get-conversation`: current snapshot; active or candidate may read.
- `send {text}`: active only. Parent supplies validated context and the URL's
  pinned projectRevision itself. Child cannot override the review revision.
  Parent rejects empty/oversized input, pending/active turns and ongoing uploads.
  Editing a new draft during the send preserves it when the response arrives.
- `interrupt`: active only; uses the existing conversation API.
- `upload {buffer:ArrayBuffer,mime,name}`: active only, PNG/JPEG/WebP,
  nonempty and at most40MiB, bounded filename. Server verifies image bytes.
  Pinned reviews cannot upload. Returns registered asset and current snapshot.
- `draft {text,seq,scroll?,focus?,selectionStart?,selectionEnd?}`: active only;
  parent persists text, monotonic sequence and scroll/caret state. Candidate
  input cannot replace a newer active draft.
- `context {chapterId,sceneIds,entityId,assetIds}`: active only; parent verifies
  existing chapter/panels/entity and at most12 registered assets.

Only the active app may send, interrupt, upload or otherwise mutate. A candidate
may render private conversation snapshots but cannot perform conversation actions.
No credentials, auth tokens or direct conversation API access are exposed.
The typed transport is intentionally available to the editable normal composer.

## Workspace requests and media

Existing messages remain:
`get-state {id}`, `request {id,path,options}`,
`select-context {context}`, `compose {text}`,
`ui-state {ui,session,replace}`, `notify {message}`, `error {message}`.

The general JSON request allowlist excludes conversation endpoints, runtime
controls, arbitrary URLs and headers. Only active frames may mutate project
APIs. Review snapshots are read-only regardless of child controls; GET state
uses the parent's locked snapshot and GET plan is forced to its pinned revision.

`read-asset {id,path}` returns transferable
`{buffer:ArrayBuffer,mime}` only for registered images or the fixed archive video
allowlist, maximum40MiB. Child image/video/WebGL uses blob URLs: opaque Chrome
iframes cannot fetch loopback media directly. API CORS was not widened.

Canonical URL fields are chapter/view/scene/entity/lang/media/yaw/pitch/fov/t,
ui=live|hash, and optional rev. Copy link pins UI hash plus saved project
revision. No prompt, script or draft content belongs in URLs. Unsaved plan and
workspace scroll stay in parent session state.

## Verification note

On the Mini's Chrome headless mode, isolated iframe screen size can remain
800×600 despite a larger emulated viewport, clipping pointer hit tests near the
bottom. Full-app acceptance therefore runs headed Chrome with site isolation
and the production sandbox intact. Real Send and Stop pointer actions are
required; direct handler invocation is not a substitute.
