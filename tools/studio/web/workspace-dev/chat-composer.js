import {command} from './bridge.js';
import {studio,notify,refresh} from './child-state.js';
import {chat,active,persistDraft,persistContext,receiveChat} from './chat-state.js';

export function bindComposer({render,renderContext}){
 const input=document.querySelector('#message-input'),form=document.querySelector('#composer');input.value=chat.draft;
 input.addEventListener('input',()=>{persistDraft(input.value);updateControls();});for(const type of ['focus','blur','select','keyup','click'])input.addEventListener(type,()=>persistDraft(input.value));
 // Keyboard policy belongs to this editable UI module. Call sendMessage directly:
 // the opaque iframe blocks native submit/requestSubmit because allow-forms is absent.
 input.addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.metaKey||e.ctrlKey)){e.preventDefault();sendMessage();}});
 const sendMessage=async()=>{const text=input.value.trim();if(!text||chat.pending||chat.sending||chat.uploading||chat.localUploading||active())return;persistDraft(input.value);persistContext();chat.sending=true;chat.pending=true;updateControls();try{const result=await command('send',{text});receiveChat(result);render();const messages=document.querySelector('#messages');messages.scrollTop=messages.scrollHeight;}catch(error){notify(error.message);}finally{chat.sending=false;chat.pending=false;updateControls();}};form.addEventListener('submit',event=>event.preventDefault());document.querySelector('#send').onclick=sendMessage;
 document.querySelector('#interrupt').onclick=async()=>{try{receiveChat(await command('interrupt'));render();}catch(error){notify(error.message);}};
 document.querySelector('#attachment').onchange=async event=>{const file=event.target.files[0];if(!file)return;if(studio.assetIds.length>=12){notify('A conversation can include up to 12 attached images.');event.target.value='';return;}if(file.size>40*1024*1024){notify('Choose an image smaller than 40 MiB.');event.target.value='';return;}chat.localUploading=true;chat.uploading=true;updateControls();try{const buffer=await file.arrayBuffer();const result=await command('upload',{buffer,mime:file.type,name:file.name},[buffer]);receiveChat(result);await refresh();if(result?.asset?.id&&!studio.assetIds.includes(result.asset.id)){studio.assetIds.push(result.asset.id);persistContext();}renderContext();notify('Image attached to your next message.');}catch(error){notify(error.message);}finally{event.target.value='';chat.localUploading=false;chat.uploading=false;render();}};
}

export function updateControls(){const input=document.querySelector('#message-input'),button=document.querySelector('#send');if(!button)return;button.disabled=chat.pending||chat.sending||chat.uploading||chat.localUploading||active()||!input.value.trim();button.textContent=chat.pending?'Sending…':chat.uploading?'Uploading…':'Send ↗';const stop=document.querySelector('#interrupt');stop.classList.toggle('hidden',!active());stop.disabled=chat.conversation?.status==='interrupting';document.querySelector('#attachment').disabled=chat.uploading||chat.pending||studio.readOnly;}
export function synchronizeDraft(){const input=document.querySelector('#message-input');if(input&&input.value!==chat.draft){const start=input.selectionStart,end=input.selectionEnd,focused=document.activeElement===input;input.value=chat.draft;if(focused)input.setSelectionRange(Math.min(start,input.value.length),Math.min(end,input.value.length));}updateControls();}

export function restoreComposerFocus(){const input=document.querySelector("#message-input");if(input&&chat.focus){input.setSelectionRange(Math.min(chat.selection?.start??input.value.length,input.value.length),Math.min(chat.selection?.end??input.value.length,input.value.length));input.focus({preventScroll:true});}}
