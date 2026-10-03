import {studio,request,refresh,notify,esc} from './conversation-state.js';
import {readRoute,cleanRoute,applyRoute,writeRoute} from './shell-route.js';
import {createWorkspaceHost} from './shell-frame-host.js';
import {createConversationKernel} from './kernel-conversation.js';
import {createFallback} from './kernel-fallback.js';
let host,kernel,fallback,manualRecovery=false,available=false;
function showRecovery(open){document.querySelector('#kernel-fallback').hidden=!open;document.querySelector('#communication-toggle').textContent=open?'Back to app':'Conversation';document.querySelector('#fallback-close').disabled=!available}
function render(snapshot){fallback?.render(snapshot);host?.conversationUpdated(snapshot)}
async function start(){try{
 studio.route=readRoute();await refresh();applyRoute(studio,cleanRoute(studio.route,studio.state));writeRoute(studio.route,true);
 document.querySelector('#studio').innerHTML='<main class="kernel-shell"><header class="kernel-bar"><div id="workspace-controls"></div><button id="communication-toggle" type="button">Conversation</button></header><div id="workspace-host" class="workspace-unavailable"><p class="workspace-opening">Opening Studio…</p></div><section id="kernel-fallback" aria-label="Recovery conversation"></section></main>';
 kernel=createConversationKernel({onChange:render,onContext:()=>host?.contextUpdated(),onProject:()=>host?.stateUpdated()});
 fallback=createFallback(document.querySelector('#kernel-fallback'),kernel);fallback.render(kernel.snapshot());
 document.querySelector('#communication-toggle').onclick=()=>{manualRecovery=!document.querySelector('#kernel-fallback').hidden;manualRecovery=!manualRecovery;showRecovery(manualRecovery)};
 document.querySelector('#fallback-close').onclick=()=>{manualRecovery=false;showRecovery(false)};
 host=createWorkspaceHost({studio,getConversation:kernel.snapshot,onConversationCommand:async(type,d)=>{if(type==='get-conversation')return kernel.snapshot();if(type==='send')return kernel.send(d.text);if(type==='interrupt')return kernel.interrupt();if(type==='upload')return kernel.upload(d)},onDraft:d=>kernel.setDraft(d.text,d.seq,d.scroll,d),onFullContext:d=>kernel.setContext(d),onRoute:()=>kernel.emit(),onContext:value=>kernel.selectContext(value),onCompose:text=>{const old=kernel.snapshot().draft;kernel.setDraft(old.trim()&&old.trim()!==text.trim()?old+'\n\n'+text:text)},onFocus:()=>{manualRecovery=true;showRecovery(true);fallback.input.focus()},onAvailability:ready=>{available=ready;showRecovery(manualRecovery||!available)}});
 showRecovery(true);setInterval(async()=>{try{const next=await request('/api/state'+(studio.route.rev!==undefined?'?revision='+studio.route.rev:''));if(next.revision!==studio.state.revision||studio.state.readOnly){studio.state=next;host.stateUpdated();kernel.emit()}}catch{}},6000);
}catch(error){document.querySelector('#studio').innerHTML='<main class="kernel-error"><h1>Studio could not open</h1><p>'+esc(error.message)+'</p><button onclick="location.reload()">Try again</button></main>'}}
start();
