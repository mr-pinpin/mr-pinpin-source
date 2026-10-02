import {put} from './ui.js';
export const model={server:null,draft:null,revision:0,dirty:false,stage:'book',lang:localStorage.getItem('pinpin-studio-language')||'ru',chapterId:null,sceneId:null,entityId:null,referenceKind:'all',query:'',busy:false,conflict:false,notice:'',draftEpoch:0};
let notify=()=>{};
export function onChange(fn){notify=fn}
export async function api(url,body,method='POST'){
 const res=await fetch(url,{method:body===undefined?'GET':method,headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
 const data=await res.json();if(!res.ok){const err=new Error(data.error?.message||`Request failed (${res.status})`);err.status=res.status;err.details=data.error?.details;throw err}return data;
}
export function adopt(s){model.server=s;model.draft=structuredClone(s.project);model.revision=s.revision;model.dirty=false;model.conflict=false;model.notice='';model.chapterId=model.chapterId||s.project.activeChapterId||s.project.chapters?.[0]?.id;notify()}
export async function load(){adopt(await api('/api/state'))}
export function edit(path,value){put(model.draft,path,value);model.dirty=true;model.draftEpoch++;notify('status')}
export function changed(){model.dirty=true;model.draftEpoch++;notify()}
export async function save(){if(model.conflict)throw new Error('Resolve the newer server version first. Your draft is preserved; download it before reloading if needed.');if(!model.dirty)return;const epoch=model.draftEpoch,snapshot=structuredClone(model.draft);try{const s=await api('/api/state',{expectedRevision:model.revision,project:snapshot},'PUT');if(model.draftEpoch===epoch)adopt(s);else{model.server=s;model.revision=s.revision;model.dirty=true;notify('status')}}catch(e){if(e.status===409){model.conflict=true;model.notice='The server has a newer revision. Your unsaved changes are still here.';notify()}throw e}}
export async function mutate(url,body){await save();const result=await api(url,body);adopt(await api('/api/state'));return result}
export async function upload(file){
 if(!file)throw new Error('Choose an image first.');
 await save();
 const res=await fetch('/api/assets',{method:'POST',headers:{'Content-Type':file.type,'X-File-Name':encodeURIComponent(file.name)},body:file});
 const data=await res.json();if(!res.ok)throw new Error(data.error?.message||'Upload failed');
 adopt(await api('/api/state'));return data.asset;
}
export async function poll(){
 if(model.busy)return;try{const s=await api('/api/state');if(s.revision===model.server?.revision)return;
 const unchanged=JSON.stringify(s.project)===JSON.stringify(model.server.project);
 model.server={...s};
 if(unchanged&&!model.conflict){model.revision=s.revision;notify('metadata')}else{model.notice='New project changes are available on the server. Refresh when ready.';model.conflict=true;notify('status')}
 }catch{/* Visible connection state is handled by explicit operations, not disruptive polling dialogs. */}
}
export function chapter(){return model.draft?.chapters?.find(c=>c.id===model.chapterId)||model.draft?.chapters?.[0]}
export function chapterIndex(){return model.draft.chapters.findIndex(c=>c.id===chapter()?.id)}
export function scene(){return chapter()?.scenes?.find(s=>s.id===model.sceneId)||chapter()?.scenes?.[0]}
export function entity(){return model.draft?.entities?.find(e=>e.id===model.entityId)}
