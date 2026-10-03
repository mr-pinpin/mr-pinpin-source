import {openPanorama} from './panorama.js';
const el=(tag,text,className)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(className)n.className=className;return n;};
function button(text,action){const n=el('button',text);n.type='button';n.onclick=action;return n;}
async function get(options,url){return options.request(url);}
function heading(container,title,description){container.append(el('h2',title),el('p',description,'media-description'));}

export function renderSpaces(container,options={}){
 let alive=true,dispose=()=>{},selection=0;container.classList.add('media-workspace');
 heading(container,'Spaces & motion','Look around a place, inspect its cube faces, or travel along a recorded orbit.');
 const toolbar=el('div',null,'media-actions'),layout=el('div',null,'media-layout'),list=el('div',null,'media-library'),stage=el('div',null,'media-stage');
 toolbar.append(button('Request panorama',()=>options.compose?.('Create a panorama for this place using a successful seamless panorama reference and a distinct location identity reference.')),
 button('Request orbit video',()=>options.compose?.('Prepare an orbit-video generation handoff for this subject. Bind the subject and location references, and review one complete camera circuit.')));
 if(options.readOnly)for(const b of toolbar.querySelectorAll('button')){b.disabled=true;b.title='Switch to Live to request production.';}
 layout.append(list,stage);container.append(toolbar,layout);stage.append(el('p','Loading registered spaces…'));
 get(options,'/api/media').then(data=>{if(!alive)return;
  async function select(item,restoring=false){const token=++selection;dispose();stage.replaceChildren();for(const n of list.children)n.classList.toggle('selected',n.dataset.id===item.id);
   const title=typeof item.name==='object'?item.name[options.lang]||item.name.en||Object.values(item.name)[0]:item.name;
   stage.append(el('h3',title),el('p',item.note||`${item.projection} · ${item.reviewStatus}`,'media-description'));
   const view=el('div',null,'media-view');stage.append(view);const restored=restoring?{...options.viewState}:{};options.onViewChange?.({media:item.id,...(restoring?{}:{yaw:null,pitch:null,fov:null,t:null})});
   if((item.kind==='panorama'&&item.projection==='equirectangular')||item.projection==='cube-atlas-3x2'){
    try{const textureURL=await options.readAsset(item.url);if(!alive||selection!==token){URL.revokeObjectURL(textureURL);return;}const close=openPanorama({...item,url:textureURL},view,{yaw:restored.yaw,pitch:restored.pitch,fov:restored.fov,onChange:patch=>options.onViewChange?.(patch)});dispose=()=>{close?.();URL.revokeObjectURL(textureURL);};}catch(error){if(alive&&selection===token)view.append(el('p',error.message,'media-error'));}
   }else if(item.kind==='orbit-video'){try{const blob=await options.readAsset(item.url);if(!alive||selection!==token){URL.revokeObjectURL(blob);return;}const close=orbit(view,{...item,url:blob},{t:restored.t,onChange:patch=>options.onViewChange?.(patch)});dispose=()=>{close();URL.revokeObjectURL(blob);};}catch(error){if(alive&&selection===token)view.append(el('p',error.message,'media-error'));}}
   else{const img=el('img');img.dataset.assetSrc=item.url;img.alt=title;img.className='media-atlas';view.append(img);dispose=()=>{};}
   const actions=el('div',null,'media-actions');
   async function attach(){if(!item.assetId){const response=await options.request('/api/media/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:item.id})});item.assetId=response.asset.id;await options.refresh?.();}options.selectContext?.({type:'asset',id:item.assetId,label:title});}
   if(item.kind!=='orbit-video')actions.append(button('Use as reference',async()=>{try{await attach();options.notify?.('Reference added to the conversation.');}catch(e){options.notify?.(e.message);}}));
   actions.append(button('Review in conversation',async()=>{try{if(item.kind!=='orbit-video')await attach();options.compose?.(`Review ${title} from the Spaces library (media ID: ${item.id}). ${item.kind==='orbit-video'?'Video selected: inspect extracted frames from the allowlisted archive; this is not a native video attachment. ':''}Inspect continuity, visible seams and remaining defects; preserve its source version.`);}catch(e){options.notify?.(e.message);}}));
   stage.append(actions);if(item.reviewNotes){const detail=el('details');detail.append(el('summary','Source & review notes'),el('p',item.reviewNotes,'media-description'));stage.append(detail);}
  }
  for(const item of data.items){const label=typeof item.name==='object'?item.name[options.lang]||item.name.en||Object.values(item.name)[0]:item.name;const b=button('',()=>select(item));b.dataset.id=item.id;b.append(el('strong',label),el('small',item.kind.replaceAll('-',' ')));list.append(b);}
  if(data.items.length)select(data.items.find(i=>i.id===options.viewState?.media)||data.items[0],true);else stage.replaceChildren(el('p','No registered spaces yet. Bind a location and an approved panorama reference to prepare a request.'));
  if(data.notes?.length){const details=el('details');details.append(el('summary','Unavailable archive entries'),el('p',data.notes.join(' · ')));container.append(details);}
 }).catch(error=>{if(alive)stage.replaceChildren(el('p',error.message,'media-error'));});
 return()=>{alive=false;dispose();container.classList.remove('media-workspace');};
}

function orbit(container,item,options={}){
 const video=el('video');video.src=item.url;video.preload='metadata';video.playsInline=true;video.muted=true;video.className='media-orbit';video.tabIndex=0;video.setAttribute('aria-label','Drag horizontally to inspect the orbit');
 const slider=el('input');slider.type='range';slider.min='0';slider.max='1000';slider.value='0';slider.disabled=true;slider.setAttribute('aria-label','Orbit progress');
 const time=el('output','Loading orbit…'),play=button('Play',async()=>{try{video.paused?await video.play():video.pause();}catch{time.textContent='Playback unavailable. Try dragging the clip.';}});play.disabled=true;
 const controls=el('div',null,'media-orbit-controls');controls.append(play,slider,time);container.append(video,controls,el('p','Drag to orbit · use the slider to choose a view.','media-description'));
 let pointer=null,desired=null;
 const seek=p=>{if(!Number.isFinite(video.duration)||!video.duration)return;video.pause();desired=Math.max(0,Math.min(video.duration-.001,p*video.duration));pump();};
 function pump(){if(desired!==null&&!video.seeking){const value=desired;desired=null;video.currentTime=value;}}
 function display(){slider.value=String(Math.round(video.currentTime/video.duration*1000)||0);time.textContent=`${Math.round(video.currentTime/video.duration*100)||0}%`;time.title=`${video.currentTime.toFixed(1)} / ${video.duration.toFixed(1)} seconds`;if(Number.isFinite(video.duration))options.onChange?.({t:Math.round(video.currentTime*1000)/1000}); }
 video.onloadedmetadata=()=>{slider.disabled=play.disabled=false;if(Number.isFinite(options.t)&&options.t>0)seek(options.t/video.duration);else display();};video.onseeked=()=>{pump();display();};video.ontimeupdate=display;
 video.onplay=()=>play.textContent='Pause';video.onpause=()=>play.textContent='Play';video.onerror=()=>{time.textContent='The archived video could not be loaded.';slider.disabled=play.disabled=true;};
 slider.oninput=()=>seek(Number(slider.value)/1000);
 video.onpointerdown=e=>{if(e.button>0||slider.disabled)return;pointer={id:e.pointerId,x:e.clientX,start:video.currentTime/video.duration};video.pause();video.setPointerCapture(e.pointerId);};
 video.onpointermove=e=>{if(pointer?.id===e.pointerId)seek(((pointer.start+(e.clientX-pointer.x)/video.clientWidth)%1+1)%1);};
 video.onpointerup=video.onpointercancel=()=>pointer=null;
 video.onkeydown=e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();seek(video.currentTime/video.duration+(e.key==='ArrowLeft'?-.01:.01));}};
 return()=>{video.pause();video.removeAttribute('src');video.load();};
}

export function renderInsights(container,options={}){
 let alive=true;container.classList.add('media-workspace');heading(container,'Production insights','Observed job history, review decisions and explicit retries.');const body=el('div');container.append(body);body.append(el('p','Reading job ledger…'));
 get(options,'/api/insights').then(data=>{if(!alive)return;body.replaceChildren();const cards=el('div',null,'insight-cards');
  const timing=data.observedDurations;for(const [label,value]of [['Recorded jobs',data.totalJobs],['Failed jobs',data.statuses.failed||0],['Explicit retries',data.explicitRetries],['Median ledger interval',timing.medianSeconds==null?'Unknown':`${timing.medianSeconds<1?timing.medianSeconds.toFixed(3):Math.round(timing.medianSeconds)} s`]]){const card=el('div',null,'insight-card');card.append(el('strong',String(value)),el('span',label));cards.append(card);}body.append(cards,el('p',`${timing.sampleCount} timed jobs; ${timing.excludedHistoricalRegistrations||0} historical registrations excluded. ${timing.meaning}`,'media-description'),el('p',data.retryCoverage,'media-description'),el('h3','Failure & review hotspots'));
  if(!data.hotspots.length)body.append(el('p','No recorded failures, rejected artifacts or explicitly linked retries. This is not evidence of zero historical attempts.'));
  else{const table=el('table',null,'insight-table'),head=el('tr');for(const x of ['Target / kind','Jobs','Failed','Rejected','Retries'])head.append(el('th',x));const thead=el('thead');thead.append(head);table.append(thead);const tbody=el('tbody');for(const r of data.hotspots){const tr=el('tr');for(const v of [`${r.targetId} / ${r.kind}`,r.jobs,r.failures,r.rejections,r.retries])tr.append(el('td',String(v)));tbody.append(tr);}table.append(tbody);body.append(table);}
  for(const note of data.notes)body.append(el('p',note,'media-description'));
 }).catch(error=>{if(alive)body.replaceChildren(el('p',error.message,'media-error'));});
 return()=>{alive=false;container.classList.remove('media-workspace');};
}
