import {studio} from './child-state.js';
import {send} from './bridge.js';
export const chat={conversation:null,draft:'',draftSeq:0,pending:false,uploading:false,sending:false,localUploading:false,connectionError:null,scroll:null,focus:false,selection:{start:0,end:0},mobile:'story',key:'',contextKey:''};
export const active=()=>['connecting','running','interrupting'].includes(chat.conversation?.status);
export function context(){return {chapterId:studio.chapterId,sceneIds:[...studio.sceneIds],entityId:studio.entityId,assetIds:[...studio.assetIds]};}
export function persistContext(){send('context',context());}
export function persistDraft(text,{scroll}={}){if(text!==chat.draft){chat.draft=text;chat.draftSeq++;}if(Number.isFinite(scroll))chat.scroll=scroll;const input=document.querySelector('#message-input');if(input){chat.focus=document.activeElement===input;chat.selection={start:input.selectionStart,end:input.selectionEnd};}send('draft',{text:chat.draft,seq:chat.draftSeq,focus:chat.focus,selectionStart:chat.selection.start,selectionEnd:chat.selection.end,...(Number.isFinite(chat.scroll)?{scroll:chat.scroll}:{})});}
export function receiveChat(value,initial=false){
 if(!value||typeof value!=='object')return false;
 if(value.conversation){chat.conversation=value.conversation;if(!Object.hasOwn(value,'connectionError'))chat.connectionError=null;}
 for(const key of ['pending','uploading','connectionError'])if(Object.hasOwn(value,key))chat[key]=value[key];
 if(typeof value.draft==='string'&&(initial||(Number(value.draftSeq)||0)>=chat.draftSeq)){chat.draft=value.draft;chat.draftSeq=Number(value.draftSeq)||0;if(typeof value.chatFocus==='boolean')chat.focus=value.chatFocus;if(value.chatSelection)chat.selection=value.chatSelection;}
 if(initial&&Number.isFinite(value.chatScroll??value.scroll))chat.scroll=value.chatScroll??value.scroll;
 const before=JSON.stringify(context());const next=value.chatContext;
 if(next){if(next.chapterId)studio.chapterId=next.chapterId;if(Array.isArray(next.sceneIds))studio.sceneIds=[...next.sceneIds];if(Object.hasOwn(next,'entityId'))studio.entityId=next.entityId;if(Array.isArray(next.assetIds))studio.assetIds=[...next.assetIds];}
 return before!==JSON.stringify(context());
}
