# Stable conversation / workspace frame protocol

The parent owns chat DOM, private conversation, input draft, uploads, context,
API authority, canonical URL, and serialized workspace draft state.
A workspace build lives below /workspace-builds/<64-character-sha256>/index.html.
Its iframe has sandbox="allow-scripts allow-downloads allow-popups"; never add
allow-same-origin. Its opaque origin must not read parent DOM, storage, or API.

Every message is a plain object with protocol: "pinpin-workspace-v1",
nonce (from the frame URL fragment #nonce=...), and type. Parent verifies origin
"null", source equals an active/pending iframe window, and that frame's nonce.
Parent-to-child messages use a wildcard target because the child is opaque.
The child's initial boot also uses a wildcard; subsequent messages target the
validated origin received with init.

Parent sends init after load (and may answer boot):
{state,ui,session,apiOrigin,readOnly}. Child renders before sending ready.
ui uses chapter/view/scene/entity/lang/media/yaw/pitch/fov/t plus ui/rev.
Child must use apiOrigin for direct registered image/video display URLs.
Parent later sends state {state,ui,readOnly} and route {state,ui,session,readOnly}.

Child messages:
- ready: first successful rendered view; allows atomic frame swap
- get-state {id}: parent replies response {id,result: state}
- request {id,path,options}: response {id,result} or {id,error:{message,status}}
- read-asset {id,path}: registered image or fixed archive video, maximum40MiB;
  response result {buffer:ArrayBuffer,mime} transfers bytes. Use child blob URLs
  for images/video/WebGL because opaque iframe origins cannot fetch loopback media.
- select-context {context:{type:scene|entity|asset,id}}
- compose {text}: sets a draft only, never sends; parent preserves existing draft
- ui-state {ui,session,replace}: canonical navigation + serialized planDrafts/scroll
- notify {message}; error {message}

Only active frames may mutate project APIs or request context/composer changes.
Pending frames may read approved workspace APIs. Conversation endpoints,
runtime controls, arbitrary URLs and headers are excluded. Review snapshots
are read-only regardless of the child UI. Parent does not trust child readOnly.
The parent sends no conversation transcript, input draft, credentials, or tokens.

The shell polls runtime metadata and swaps only after ready. A failed candidate
leaves the last good frame alive. Hot updates never reload the parent document.
Only allowed URL fields are serialized; Copy link pins both build hash and
saved project revision. Unsaved plan/scroll state stays in parent sessionStorage.
