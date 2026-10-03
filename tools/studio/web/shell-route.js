// Canonical, shareable UI state. Never put conversation text or draft content in URLs.
export const HASH=/^[a-f0-9]{64}$/;
const identifier=/^[A-Za-z0-9_.-]{1,160}$/;
const views=new Set(['board','read','references','spaces','insights','plan']);
export function cleanRoute(input={},state=null){
 const out={view:views.has(input.view)?input.view:'board',lang:['ru','en','es'].includes(input.lang)?input.lang:'ru',ui:input.ui==='live'||HASH.test(input.ui||'')?input.ui:'live'};
 for(const key of ['chapter','scene','entity','media'])if(identifier.test(input[key]||''))out[key]=input[key];
 for(const [key,min,max]of [['yaw',-360,360],['pitch',-90,90],['fov',20,120],['t',0,86400]])if(input[key]!==undefined&&input[key]!==null&&input[key]!==''&&Number.isFinite(Number(input[key])))out[key]=Math.min(max,Math.max(min,Number(input[key])));
 const rev=Number(input.rev);if(input.rev!==undefined&&input.rev!==null&&input.rev!==''&&Number.isSafeInteger(rev)&&rev>=0)out.rev=rev;
 if(state){const p=state.project;let c=p.chapters.find(c=>c.id===out.chapter);if(!c){out.chapter=p.activeChapterId||p.chapters.find(c=>c.scenes?.length)?.id||p.chapters[0]?.id;c=p.chapters.find(c=>c.id===out.chapter)}if(!c?.scenes?.some(s=>s.id===out.scene))delete out.scene;if(!p.entities.some(e=>e.id===out.entity))delete out.entity}
 return out;
}
export const readRoute=state=>cleanRoute(Object.fromEntries(new URL(location.href).searchParams),state);
export function routeURL(ui){const url=new URL(location.href);url.search='';url.hash='';for(const key of ['chapter','view','scene','entity','lang','media','yaw','pitch','fov','t','ui','rev'])if(ui[key]!==undefined&&ui[key]!==null&&ui[key]!=='')url.searchParams.set(key,String(ui[key]));return url}
export function writeRoute(ui,replace=false){const url=routeURL(ui);if(url.href!==location.href)history[replace?'replaceState':'pushState'](null,'',url)}
export function applyRoute(studio,ui){studio.chapterId=ui.chapter;studio.mode=ui.view==='plan'?'board':ui.view;studio.planOpen=ui.view==='plan';studio.lang=ui.lang;studio.sceneIds=ui.scene?[ui.scene]:[];studio.entityId=ui.entity||null;studio.route=ui}
