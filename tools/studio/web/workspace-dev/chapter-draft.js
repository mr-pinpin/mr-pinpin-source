import {esc,studio,asset,request,post,notify,emitUI} from './child-state.js';
import {compose} from './child-actions.js';
const selections=new Map();
export function renderChapterDraft(c){
 const d=c.studioDraft;if(!d)return '';const versions=d.versions||[];
 const choice=selections.get(c.id)||{version:d.currentVersion,page:0};
 const v=versions.find(v=>v.version===choice.version)||versions.at(-1);if(!v)return '';
 const count=Math.ceil(v.spec.panels.length/12);choice.page=Math.min(choice.page,count-1);selections.set(c.id,choice);
 const entityName=id=>{const e=studio.state?.project.entities.find(e=>e.id===id);return typeof e?.name==='string'?e.name:e?.name?.en||id;};
 const page=v.spec.panels.slice(choice.page*12,(choice.page+1)*12);
 return `<section class="chapter-prototype"><h2>${esc(v.spec.title)} · v${v.version}</h2><p>Unpublished draft · preview type is labeled on each panel · full production requires your specific approval of the current version.</p><p data-production-status>Full-production authorization is checked against the saved current bindings.</p><button data-production-go data-version="${v.version}" data-sha="${esc(v.sha256)}" disabled>Authorize full production for this version</button><nav>${versions.map(x=>`<button data-draft-version="${x.version}">v${x.version} · ${esc(x.reason)}</button>`).join('')}</nav><p>${esc(v.spec.location.description)} · ${v.spec.location.proposed?'proposed variant':'existing location'}</p><p>${v.spec.panels.reduce((n,p)=>n+p.seconds,0)}s proposed reading rhythm · ${v.spec.panels.length} panels</p><nav><button data-draft-page="${choice.page-1}" ${choice.page===0?'disabled':''}>Previous page</button> Page ${choice.page+1} / ${count} <button data-draft-page="${choice.page+1}" ${choice.page===count-1?'disabled':''}>Next page</button></nav><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">${page.map((p,i)=>{const image=p.imageAssetId&&asset(p.imageAssetId);return `<article style="border:1px solid #bbb;padding:12px;border-radius:12px"><strong>${choice.page*12+i+1}. ${esc(p.beat)} · ${p.seconds}s</strong><div style="background:#f2eee5;padding:16px;margin:8px 0">${image?`<img data-asset-src="${esc(image.url)}" alt="${esc(p.action)}" style="max-width:100%"><small>${p.previewKind==='generated'?'Registered generated preview':'Reused reference, not a new scene illustration'}</small>`:`${esc(p.castIds.map(entityName).join(' + '))}<br>↪ ${esc(p.action)}<br><small>Schematic placeholder</small>`}<p>${esc(p.camera)}</p></div><p>${esc(p.caption)}</p><small>Because: ${esc(p.cause)}<br>Result: ${esc(p.effect)}</small><p><button data-draft-panel="${esc(p.id)}" data-version="${v.version}" data-sha="${esc(v.sha256)}">Revise this panel in conversation</button></p></article>`;}).join('')}</div><p>${v.spec.referenceIds.length} existing references retained. Reuse and placeholders do not imply newly generated artwork.</p></section>`;
}
export function bindChapterDraft(c,rerender){
 document.querySelectorAll('[data-production-go]').forEach(b=>{
  b.disabled=true;
  if(studio.readOnly||Number(b.dataset.version)!==c.studioDraft.currentVersion)return;
  request('/api/chapter-drafts?chapterId='+encodeURIComponent(c.id)).then(result=>{
   const d=result.draft;
   if(result.readOnly||!d||d.currentVersion!==Number(b.dataset.version)||d.sha256!==b.dataset.sha)return;
   b.disabled=false;
   const status=document.querySelector('[data-production-status]');
   if(status)status.textContent=d.productionAuthorized?'Full production authorized for this version; no job started.':'Awaiting explicit full-production go. Reference binding '+d.referenceHash.slice(0,12)+'.';
   b.onclick=async()=>{
    b.disabled=true;
    try{
     await post('/api/chapter-drafts/authorize-production',{chapterId:c.id,version:d.currentVersion,sha256:d.sha256,referenceHash:d.referenceHash,expectedRevision:result.revision,explicitFullProductionGo:true,userInstruction:'UI explicit go: authorize full production for '+c.id+' v'+d.currentVersion+' spec '+d.sha256+' references '+d.referenceHash});
     studio.state=await request('/api/state');emitUI(true);rerender();notify('Full-production authorization saved for this version. No production job started.');
    }catch(e){notify(e.message);}
   };
  }).catch(e=>notify(e.message));
 });

 document.querySelectorAll('[data-draft-version]').forEach(b=>b.onclick=()=>{selections.set(c.id,{version:Number(b.dataset.draftVersion),page:0});rerender();});
 document.querySelectorAll('[data-draft-page]').forEach(b=>b.onclick=()=>{const choice=selections.get(c.id);choice.page=Number(b.dataset.draftPage);rerender();});
 document.querySelectorAll('[data-draft-panel]').forEach(b=>{b.disabled=studio.readOnly||Number(b.dataset.version)!==c.studioDraft.currentVersion;b.onclick=()=>compose(`Revise ${c.id} draft v${b.dataset.version}, panel ${b.dataset.draftPanel}: … Keep other panels unchanged. Use the persistent patch command with current hash ${b.dataset.sha}. Script/storyboard only; no full production.`);});
}
