import {esc,studio,asset,request,notify,emitUI} from './child-state.js';
import {rpc} from './bridge.js';
import {compose} from './child-actions.js';
import {renderCompactSheets,toggleSheetZoom} from './compact-sheet-view.js';
import {downloadPDF} from './draft-pdf-download.js';
const selections=new Map(),editors=new Map();
const editorKey=(chapter,version,panel)=>JSON.stringify([chapter,version,panel]);
function editor(chapter,version,panel,caption){const key=editorKey(chapter,version,panel);if(!editors.has(key)){if(editors.size>=256)editors.delete(editors.keys().next().value);editors.set(key,{caption,open:false,focused:false,start:0,end:0});}return editors.get(key);}
export function rememberDraftEditors(){
 const section=document.querySelector('.chapter-prototype');if(!section)return;
 const chapter=section.dataset.draftChapter,version=Number(section.dataset.draftVersionView);
 for(const details of section.querySelectorAll('[data-draft-editor]')){const input=details.querySelector('[data-draft-caption]');if(!input)continue;const value=editor(chapter,version,details.dataset.draftEditor,input.value);value.caption=input.value;value.open=details.open;value.focused=document.activeElement===input;if(value.focused){value.start=input.selectionStart;value.end=input.selectionEnd;}}
}

// Named reads use RPC directly: the generic child-state POST gate treats every POST
// as a mutation. Stable parent/server independently enforce registered read effects.
const capability=(operation,body)=>rpc('/api/business/'+operation,{method:'POST',body:JSON.stringify(body)});
export const readDraft=(chapterId,page=0)=>capability('draft.get.v1',{chapterId,page});
export function patchDraft(body){if(studio.readOnly)throw Error('Pinned revision; switch to Live to revise.');return capability('draft.patch.v1',body);}
export function authorizeDraft(body){if(studio.readOnly)throw Error('Pinned revision; switch to Live to authorize.');return capability('draft.authorize.v1',body);}
export function renderChapterDraft(c){
 const d=c.studioDraft;if(!d)return '';const versions=d.versions||[];
 const choice=selections.get(c.id)||{version:d.currentVersion,page:0,followCurrent:true};
 if(choice.followCurrent)choice.version=d.currentVersion;
 const v=versions.find(v=>v.version===choice.version)||versions.at(-1);if(!v)return '';
 const count=Math.ceil(v.spec.panels.length/12);choice.page=Math.max(0,Math.min(choice.page,count-1));selections.set(c.id,choice);
 const entityName=id=>{const e=studio.state?.project.entities.find(e=>e.id===id);return typeof e?.name==='string'?e.name:e?.name?.en||id;};
 const sheets=renderCompactSheets(c,v,{assets:studio.state.assets,escape:esc});
 const page=v.spec.panels.slice(choice.page*12,(choice.page+1)*12);
 return `<section class="chapter-prototype" data-draft-chapter="${esc(c.id)}" data-draft-version-view="${v.version}"><h2>${esc(v.spec.title)} · v${v.version}</h2>${sheets.html}<details><summary>Version review, approval and downloads</summary><p>Unpublished draft · full production requires your specific approval of the current version.</p><p data-production-status>Checking the saved current bindings…</p><button data-production-go data-version="${v.version}" data-sha="${esc(v.sha256)}" disabled>Authorize full production for this version</button><div data-draft-deliveries>Checking registered PDF exports…</div></details><nav>${versions.map(x=>`<button data-draft-version="${x.version}">v${x.version} · ${esc(x.reason)}</button>`).join('')}</nav><p>${esc(entityName(v.spec.location.description))} · ${v.spec.location.proposed?'proposed variant':'existing location'}</p><p>${v.spec.panels.reduce((n,p)=>n+p.seconds,0)}s proposed reading rhythm · ${v.spec.panels.length} panels</p><nav><button data-draft-page="${choice.page-1}" ${choice.page===0?'disabled':''}>Previous page</button> Page ${choice.page+1} / ${count} <button data-draft-page="${choice.page+1}" ${choice.page===count-1?'disabled':''}>Next page</button></nav><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">${page.map((p,i)=>{const image=p.imageAssetId&&!sheets.sheetAssetIds.has(p.imageAssetId)&&asset(p.imageAssetId),edit=editor(c.id,v.version,p.id,p.caption);return `<article style="border:1px solid #bbb;padding:12px;border-radius:12px"><strong>${choice.page*12+i+1}. ${esc(p.beat)} · ${p.seconds}s</strong><div style="background:#f2eee5;padding:16px;margin:8px 0">${image?`<img data-asset-src="${esc(image.url)}" alt="${esc(p.action)}" style="max-width:100%"><small>${p.previewKind==='generated'?'Registered generated preview':'Reused reference, not a new scene illustration'}</small>`:`${esc(p.castIds.map(entityName).join(' + '))}<br>↪ ${esc(p.action)}<br><small>Schematic placeholder</small>`}<p>${esc(p.camera)}</p></div><p>${esc(p.caption)}</p><small>Because: ${esc(p.cause)}<br>Result: ${esc(p.effect)}</small><details data-draft-editor="${esc(p.id)}" ${edit.open?'open':''}><summary>Edit caption</summary><textarea data-draft-caption="${esc(p.id)}" maxlength="1500">${esc(edit.caption)}</textarea><button type="button" data-draft-save="${esc(p.id)}" data-version="${v.version}" data-sha="${esc(v.sha256)}" disabled>Save caption</button></details><p><button data-draft-panel="${esc(p.id)}" data-version="${v.version}" data-sha="${esc(v.sha256)}">Revise this panel in conversation</button></p></article>`;}).join('')}</div><p>${v.spec.referenceIds.length} existing references retained. Reuse and placeholders do not imply newly generated artwork.</p></section>`;
}
export function bindChapterDraft(c,rerender){
 const section=document.querySelector('.chapter-prototype');if(!section)return;
 section.querySelectorAll('[data-sheet-zoom]').forEach(b=>b.onclick=()=>{const img=b.closest('figure').querySelector('img');if(!img)return;const zoom=toggleSheetZoom(b.closest('figure').dataset.compactSheet);b.setAttribute('aria-pressed',String(zoom));b.textContent=zoom?'Fit whole page':'Zoom page';img.style.height=zoom?'auto':'calc(100dvh - 450px)';img.style.maxHeight=zoom?'none':'760px';rerender();});
 const choice=selections.get(c.id),selected=c.studioDraft.versions.find(v=>v.version===choice.version);
 const current=()=>section.isConnected&&studio.chapterId===c.id;
 const canEdit=d=>current()&&!studio.readOnly&&selected?.version===d.currentVersion&&selected?.sha256===d.sha256;
 readDraft(c.id,choice.page).then(result=>{
  if(!current())return;const d=result.draft;if(!d)return;
  const status=section.querySelector('[data-production-status]');
  if(status)status.textContent=d.referenceBindingStatus==='unresolved'?'Reference bindings unresolved. Saved draft remains viewable; production authorization unavailable. '+(d.bindingError||'Restore and verify the registered references.') :d.bindingChanged?'Reference bindings changed; revise and review before full production.':result.readOnly?'Pinned revision · switch to Live to edit or authorize.':d.productionAuthorized?'Full production authorized for this version; no job started.':'Awaiting explicit full-production go. Reference binding '+d.referenceHash.slice(0,12)+'.';
  const pdfs=section.querySelector('[data-draft-deliveries]');
  const receipts=(d.deliveries||[]).filter(x=>x.version===selected.version&&x.sourceVersionSHA256===selected.sha256);
  if(pdfs){pdfs.textContent='';if(!receipts.length)pdfs.textContent='No PDF export registered for this saved version.';for(const receipt of receipts){const b=document.createElement('button');b.textContent='Download '+receipt.language.toUpperCase()+' PDF · v'+receipt.version;b.dataset.draftPdf=receipt.language;b.onclick=async()=>{b.disabled=true;try{await downloadPDF(rpc,{chapterId:c.id,version:receipt.version,language:receipt.language,sourceVersionSHA256:receipt.sourceVersionSHA256,artifactSHA256:receipt.artifactSHA256});notify('Unpublished PDF download ready.');}catch(e){notify(e.message);}finally{b.disabled=false;}};pdfs.append(b);}}
  section.querySelectorAll('[data-production-go]').forEach(b=>{
   if(result.readOnly||!canEdit(d)||d.bindingsVerified!==true||d.bindingChanged)return;b.disabled=false;
   b.onclick=async()=>{b.disabled=true;try{await authorizeDraft({chapterId:c.id,version:d.currentVersion,sha256:d.sha256,referenceHash:d.referenceHash,expectedRevision:result.revision,explicitFullProductionGo:true,userInstruction:'UI explicit go: authorize full production for '+c.id+' v'+d.currentVersion+' spec '+d.sha256+' references '+d.referenceHash});studio.state=await request('/api/state');emitUI(true);rerender();notify('Full-production authorization saved for this version. No production job started.');}catch(e){notify(e.message);if(current())b.disabled=false;}};
  });
  section.querySelectorAll('[data-draft-save]').forEach(b=>{
   if(result.readOnly||!canEdit(d))return;b.disabled=false;
   b.onclick=async()=>{b.disabled=true;try{const fresh=await readDraft(c.id);if(!canEdit(fresh.draft))throw Error('Saved version changed; reopen before revising.');const input=[...section.querySelectorAll('[data-draft-caption]')].find(x=>x.dataset.draftCaption===b.dataset.draftSave);const saved=await patchDraft({chapterId:c.id,baseVersion:fresh.draft.currentVersion,baseSHA256:fresh.draft.sha256,expectedRevision:fresh.revision,patches:[{panelId:b.dataset.draftSave,fields:{caption:input.value}}],reason:'Caption revision in Studio'});editors.delete(editorKey(c.id,selected.version,b.dataset.draftSave));selections.set(c.id,{version:saved.version,page:choice.page,followCurrent:true});studio.state=await request('/api/state');emitUI(true);rerender();notify('Caption revision saved.');}catch(e){notify(e.message);if(current())b.disabled=false;}};
  });
 }).catch(e=>{if(current()){section.querySelector('[data-production-status]').textContent=e.message;section.querySelector('[data-draft-deliveries]').textContent='PDF exports unavailable: '+e.message;}notify(e.message);});
 section.querySelectorAll('[data-draft-editor]').forEach(details=>{
  const input=details.querySelector('[data-draft-caption]'),value=editor(c.id,selected.version,details.dataset.draftEditor,input.value);
  details.querySelector('summary').addEventListener('click',()=>{value.open=!details.open;});
  details.ontoggle=()=>{if(details.isConnected)value.open=details.open;};
  const capture=()=>{value.caption=input.value;value.focused=document.activeElement===input;value.start=input.selectionStart;value.end=input.selectionEnd;};
  for(const type of ['input','focus','select','keyup'])input.addEventListener(type,capture);
  input.addEventListener('blur',()=>{if(input.isConnected)value.focused=false;});
  if(value.focused)queueMicrotask(()=>{if(input.isConnected&&document.activeElement===document.body){input.focus({preventScroll:true});input.setSelectionRange(value.start,value.end);}});
 });
 section.querySelectorAll('[data-draft-version]').forEach(b=>b.onclick=()=>{selections.set(c.id,{version:Number(b.dataset.draftVersion),page:0,followCurrent:false});rerender();});
 section.querySelectorAll('[data-draft-page]').forEach(b=>b.onclick=()=>{choice.page=Number(b.dataset.draftPage);rerender();});
 section.querySelectorAll('[data-draft-panel]').forEach(b=>{b.disabled=studio.readOnly||Number(b.dataset.version)!==c.studioDraft.currentVersion;b.onclick=()=>compose(`Revise ${c.id} draft v${b.dataset.version}, panel ${b.dataset.draftPanel}: … Keep other panels unchanged. Use the persistent patch command with current hash ${b.dataset.sha}. Script/storyboard only; no full production.`);});
 section.querySelectorAll('[data-draft-caption]').forEach(input=>input.readOnly=studio.readOnly||selected.version!==c.studioDraft.currentVersion);
}
