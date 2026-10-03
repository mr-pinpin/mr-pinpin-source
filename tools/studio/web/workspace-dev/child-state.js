import {rpc,send} from './bridge.js';
export const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const words=value=>Array.isArray(value)?value.join('\n'):typeof value==='object'&&value?value.en||value.ru||Object.values(value)[0]||'':String(value??'');
export const title=(value,lang='en')=>typeof value==='object'&&!Array.isArray(value)&&value?words(value[lang]||value.en||value.ru):words(value);
export const studio={state:null,chapterId:null,lang:'ru',mode:'board',sceneIds:[],entityId:null,assetIds:[],planOpen:false,planDrafts:new Map(),mediaCleanup:null,referenceFilter:'all',media:null,yaw:null,pitch:null,fov:null,t:null,apiOrigin:null,readOnly:false,routeExtra:{},scroll:0};
export function absolute(url){if(!url)return url;try{return new URL(url,studio.apiOrigin).href;}catch{return url;}}
function mediaURLs(data){if(!data||typeof data!=='object')return data;const copy=structuredClone(data);for(const a of copy.assets||[])a.url=absolute(a.url);for(const b of copy.storyboards||[])for(const p of b.pages||[])if(p.url)p.url=absolute(p.url);for(const item of copy.items||[])if(item.url)item.url=absolute(item.url);if(copy.asset?.url)copy.asset.url=absolute(copy.asset.url);return copy;}
export async function request(path,options={}){if(studio.readOnly&&!['GET','HEAD'].includes((options.method||'GET').toUpperCase()))throw Error('This is a pinned revision. Switch to Live to make changes.');return mediaURLs(await rpc(path,options));}
export const post=(path,body,method='POST')=>request(path,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
export const chapter=()=>studio.state?.project.chapters.find(c=>c.id===studio.chapterId);
export const asset=id=>studio.state?.assets.find(a=>a.id===id);
export const caption=scene=>title(scene.captions,studio.lang)||scene.action||scene.title||'A moment waiting for words.';
export function notify(message){send('notify',{message});}
export function adopt(state){studio.state=mediaURLs(state);if(!chapter())studio.chapterId=state.project.activeChapterId||state.project.chapters.find(c=>c.scenes?.length)?.id||state.project.chapters[0]?.id;}
export async function refresh(){if(studio.readOnly)return studio.state;adopt(await request('/api/state'));return studio.state;}
export function applyRoute(ui={},session){studio.routeExtra={...ui};studio.chapterId=ui.chapter||studio.chapterId;studio.mode=ui.view==='plan'?'board':ui.view||'board';studio.planOpen=ui.view==='plan';studio.sceneIds=Array.isArray(ui.scene)?ui.scene:ui.scene?[ui.scene]:[];studio.entityId=ui.entity||null;studio.lang=ui.lang||'ru';studio.referenceFilter=ui.referenceFilter||ui.filter||'all';for(const name of ['media','yaw','pitch','fov','t'])studio[name]=ui[name]??null;if(session){studio.planDrafts=new Map(Object.entries(session.planDrafts||{}));studio.scroll=Number(session.scroll)||0;}if(ui.assetIds)studio.assetIds=ui.assetIds;}
export function snapshot(){const ui={...studio.routeExtra,chapter:studio.chapterId,view:studio.planOpen?'plan':studio.mode,scene:studio.sceneIds[0]||null,entity:studio.entityId,lang:studio.lang,referenceFilter:studio.referenceFilter,media:studio.media,yaw:studio.yaw,pitch:studio.pitch,fov:studio.fov,t:studio.t};return {ui,session:{planDrafts:Object.fromEntries(studio.planDrafts),scroll:document.querySelector('#workspace-content')?.scrollTop??studio.scroll}};}
export function emitUI(replace=false){send('ui-state',{...snapshot(),replace});}

export async function readAsset(url){const path=new URL(url,studio.apiOrigin).pathname;const result=await rpc(path,{},'read-asset');return URL.createObjectURL(new Blob([result.buffer],{type:result.mime}));}
