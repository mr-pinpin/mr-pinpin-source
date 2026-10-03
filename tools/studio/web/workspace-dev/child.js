import {shouldReportFailure} from './error-policy.js';
import {closeImageViewer} from './image-viewer.js';
import {disposeImages,suspendImages,resumeImages} from './image-assets.js';
import {accept,receiveResponse,send,close} from './bridge.js';
import {studio,adopt,applyRoute,emitUI,snapshot} from './child-state.js';
import {renderWorkspace,renderWorkspaceHeader} from './workspace.js';
import {mountChat,renderChat,showMobile} from './chat.js';
import {receiveChat} from './chat-state.js';
import {restoreComposerFocus} from './chat-composer.js';
let initialized=false,rendering=false,scrollFrame=0;
function failure(error,boundary='app',filename=''){if(shouldReportFailure(error,{boundary,filename,appURL:import.meta.url}))send('error',{message:error?.message||String(error)});}
async function render(){resumeImages();rendering=true;try{document.querySelector('#revision-notice').hidden=!studio.readOnly;renderWorkspaceHeader();await renderWorkspace();document.querySelector('#workspace-content').scrollTop=studio.scroll;renderChat();}finally{rendering=false;}}
function bindWorkspace(){document.querySelector('#workspace-content').addEventListener('scroll',()=>{if(rendering||scrollFrame)return;scrollFrame=requestAnimationFrame(()=>{scrollFrame=0;studio.scroll=document.querySelector('#workspace-content').scrollTop;emitUI(true);});});document.querySelector('#return-live').onclick=()=>{studio.routeExtra.rev=null;emitUI(false);send('live');};}
window.addEventListener('message',async event=>{if(!accept(event))return;const value=event.data;if(receiveResponse(value))return;try{
 if(value.type==='init'){if(initialized)return;initialized=true;studio.apiOrigin=value.apiOrigin||event.origin;studio.readOnly=Boolean(value.readOnly||value.state?.readOnly);adopt(value.state);applyRoute(value.ui,value.session);receiveChat(value,true);mountChat();bindWorkspace();await render();send('ready',{...snapshot(),capabilities:['conversation-ui']});}
 else if(value.type==='suspend'&&initialized){closeImageViewer();studio.mediaCleanup?.();studio.mediaCleanup=null;suspendImages();}
 else if(value.type==='route'&&initialized){studio.readOnly=Boolean(value.readOnly||value.state?.readOnly);if(value.state)adopt(value.state);applyRoute(value.ui,value.session);receiveChat(value);await render();showMobile(studio.mobile);}
 else if(value.type==='activate'&&initialized){receiveChat(value);renderChat();restoreComposerFocus();}
 else if(value.type==='conversation'&&initialized){const changed=receiveChat(value);renderChat();if(changed&&['board','references'].includes(studio.mode)&&!studio.planOpen)await renderWorkspace({preserveScroll:true});}
 else if(value.type==='state'&&initialized){studio.readOnly=Boolean(value.readOnly||value.state?.readOnly);const old=JSON.stringify(studio.state?.project);studio.scroll=document.querySelector('#workspace-content').scrollTop;adopt(value.state);if(value.ui?.assetIds)studio.assetIds=value.ui.assetIds;receiveChat(value);if(old!==JSON.stringify(studio.state.project)&&!studio.planOpen)await render();else renderChat();}
}catch(error){failure(error);}});
window.addEventListener('error',event=>failure(event.error||event.message,'global',event.filename));window.addEventListener('unhandledrejection',event=>failure(event.reason,'global'));window.addEventListener('pagehide',()=>{studio.mediaCleanup?.();disposeImages();close();});
send('boot');
