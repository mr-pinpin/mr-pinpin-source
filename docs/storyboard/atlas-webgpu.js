import './icons.js';
import './atlas-geometry.js';
import './atlas-directions.js';
import './atlas-sprite-cache.js';
import './atlas-expression-motion.js';
import './atlas-face-layer.js';
import './atlas-family.js';
import './atlas-motion.js';
import './atlas-focus.js';
import './atlas-preview.js?v=bath-magic-20261002';
import {createCoverLayer} from './atlas-cover-layer.js';
import {createCoverSelection} from './atlas-cover-selection.js';
import {createCamera} from './gpu/camera.js';
import {createRenderer} from './gpu/renderer.js';
import {createAtlasDebug} from './atlas-debug.js';
import {loadScenery} from './atlas-scenery.js';
import {loadSurfaceSampler} from './gpu/surface.js';
import {resolveAtlasRuntime} from './atlas-production.js';

const $=id => document.getElementById(id);
const storageKey='pinpin.atlas.v1', languages=['en','es','ru'];
const cameraStorageKey='pinpin.atlas.camera.v1';
const spriteTrial=new URLSearchParams(location.search).get('spriteTrial')==='1';
const runtime=resolveAtlasRuntime(location.search,location.hostname);
if(runtime.videoEnabled)await import('./atlas-video-sprite.js');
if(runtime.groundEnabled)await import('./atlas-field.js');
// Sprite trial: walk-speed turns from the movement lab (stepping gate + catch-up); ?turnWalk=0 restores pivot-in-place.
if(runtime.turnWalk) {
  const gaitName=runtime.gaitModule;
  const [{integrateWalkTurn,turnRate},{turnGait}]=await Promise.all([import('./sprite-turn-profile.mjs'),import('./'+gaitName)]);
  window.AtlasTurnWalk={integrateWalkTurn,gait:turnGait,turnRate};
}
const familyPreview=new URLSearchParams(location.search).get('familyPreview')==='1' && new URLSearchParams(location.search).get('family')==='1';
const returnStorageKey='pinpin.atlas.return.v1', places=['home','lake','elder','bridge'];
const words={
  en:{title:'The Shire',author:'Mr. PinPin',lake:'Crystal Lake',elder:"Elder's Oak",home:'Home, Sweet Home',bridge:'The Timber Bridge',available:'Open story',opened:'Opened',locked:'Locked: open Crystal Lake first',soon:'Coming soon',library:'Library',language:'Language',stories:'Stories',view:'Map view',in:'Zoom in',out:'Zoom out',fit:'Fit map',pause:'Pause animation',play:'Play animation',close:'Close',unavailable:'Preview unavailable',bokeh:'Depth of field'},
  es:{title:'La Comarca',author:'Se\u00f1or PinPin',lake:'Lago Cristal',elder:'Roble del anciano',home:'Hogar, dulce hogar',bridge:'El puente de madera',available:'Abrir historia',opened:'Abierta',locked:'Bloqueada: abre primero el Lago Cristal',soon:'Pr\u00f3ximamente',library:'Biblioteca',language:'Idioma',stories:'Historias',view:'Vista del mapa',in:'Acercar',out:'Alejar',fit:'Ver todo el mapa',pause:'Pausar animaci\u00f3n',play:'Reproducir animaci\u00f3n',close:'Cerrar',unavailable:'Vista previa no disponible',bokeh:'Profundidad de campo'},
  ru:{title:'\u0428\u0438\u0440',author:'\u041c\u0438\u0441\u0442\u0435\u0440 \u041f\u0438\u043d-\u041f\u0438\u043d',lake:'\u041a\u0440\u0438\u0441\u0442\u0430\u043b\u044c\u043d\u043e\u0435 \u043e\u0437\u0435\u0440\u043e',elder:'\u0414\u0443\u0431 \u0421\u0442\u0430\u0440\u0435\u0439\u0448\u0438\u043d\u044b',home:'\u041c\u0438\u043b\u044b\u0439 \u0434\u043e\u043c',bridge:'\u0414\u0435\u0440\u0435\u0432\u044f\u043d\u043d\u044b\u0439 \u043c\u043e\u0441\u0442',available:'\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0438\u0441\u0442\u043e\u0440\u0438\u044e',opened:'\u041e\u0442\u043a\u0440\u044b\u0442\u0430',locked:'\u0417\u0430\u043a\u0440\u044b\u0442\u043e: \u0441\u043d\u0430\u0447\u0430\u043b\u0430 \u043e\u0442\u043a\u0440\u043e\u0439\u0442\u0435 \u041a\u0440\u0438\u0441\u0442\u0430\u043b\u044c\u043d\u043e\u0435 \u043e\u0437\u0435\u0440\u043e',soon:'\u0421\u043a\u043e\u0440\u043e',library:'\u0411\u0438\u0431\u043b\u0438\u043e\u0442\u0435\u043a\u0430',language:'\u042f\u0437\u044b\u043a',stories:'\u0418\u0441\u0442\u043e\u0440\u0438\u0438',view:'\u0412\u0438\u0434 \u043a\u0430\u0440\u0442\u044b',in:'\u041f\u0440\u0438\u0431\u043b\u0438\u0437\u0438\u0442\u044c',out:'\u041e\u0442\u0434\u0430\u043b\u0438\u0442\u044c',fit:'\u0412\u0441\u044f \u043a\u0430\u0440\u0442\u0430',pause:'\u041f\u0440\u0438\u043e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u0430\u043d\u0438\u043c\u0430\u0446\u0438\u044e',play:'\u0412\u043e\u0441\u043f\u0440\u043e\u0438\u0437\u0432\u0435\u0441\u0442\u0438 \u0430\u043d\u0438\u043c\u0430\u0446\u0438\u044e',close:'\u0417\u0430\u043a\u0440\u044b\u0442\u044c',unavailable:'\u041f\u0440\u0435\u0434\u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d',bokeh:'\u0413\u043b\u0443\u0431\u0438\u043d\u0430 \u0440\u0435\u0437\u043a\u043e\u0441\u0442\u0438'}
};
const routes={lake:'chapter=1',elder:'chapter=2',bridge:'story=timber-tractor',home:'story=home-sweet-home'};
let availableStories=new Set(['lake','elder','bridge']);
const geometry=window.atlasGeometry, {width,height,regions}=geometry;
const viewport=$('map-viewport'), canvas=$('world-canvas'), overlay=$('book-overlay');
const motionCanvas=document.createElement('canvas');
motionCanvas.id='map-motion'; motionCanvas.width=width; motionCanvas.height=height;
const world=point => [point[0]*width,point[1]*height];
const normalized=point => [point[0]/width,point[1]/height];
let state={version:1,lang:'en',opened:[]}, lang='en';
let camera, renderer, motion, detector, reviewRecorder=null, frame=0, settleTimer=0;
let moving=false, focusAllowed=false, targetPending=false, selection=null, arrival=null;
let focused=null, anchor=null, keyboardRequest=null, dof=true, renderCount=0;
let bookRequest=0, previewPending=false, bookPress=null;
let rendererError=null, suspended=false;
let sceneryState={enabled:false,reason:'loading'};
let sceneryStarted=false;
let cameraReady=false;
let coverPoint=null;
const preview=window.AtlasPreview.create({canOpen,onOpen:recordOpen,onClose() {
  keyboardRequest=focused; chooseBook();
}});
const languageMenu=window.AtlasPreview.createLanguage();
let bokehStrength=4;
let lensOptions={focusOffset:0,highlights:1};
try {
  const saved=sessionStorage.getItem('pinpin.atlas.debug.bokeh.v1');
  if (saved!==null && matchMedia('(min-width: 768px) and (hover: hover) and (pointer: fine)').matches) {
    const value=Number(saved);
    if (Number.isFinite(value) && value>=0 && value<=4) bokehStrength=value;
  }
} catch { /* Debug adjustments still work when storage is blocked. */ }
const debugPanel=createAtlasDebug({getStrength:() => bokehStrength,getLens:() => lensOptions,
spriteTrial,getSpriteSet:()=>motion?.spriteSet || 'original',onSpriteSetChange:value=>motion?.setSpriteSet(value),
getWalkMode:()=>new URLSearchParams(location.search).get('sandbox')==='1' ? motion?.walkMode || new URLSearchParams(location.search).get('walk') || 'steer' : null,
onWalkModeChange:value=>motion?.setWalkMode(value),
onLensChange(value) { lensOptions={...lensOptions,...value}; renderer?.setLensOptions(lensOptions); },onStrengthChange(value) {
  bokehStrength=value;
  renderer?.setBokehStrength(value);
  try { sessionStorage.setItem('pinpin.atlas.debug.bokeh.v1',String(value)); } catch { /* Optional debug persistence. */ }
}});
const covers=createCoverLayer({regions,viewport,root:overlay,status,
  onInvalidate() { invalidate(); },
  project:point => camera.worldToScreen(world(point)),
  view() { const s=snapshot(); return {...s,openingScale:2*Math.max(s.width/width,s.height/height)}; },
  activate:openBook,
  bind(button,id) {
    button.addEventListener('wheel',event => {
      event.preventDefault();
      const {clientX,clientY,deltaY,deltaMode,ctrlKey}=event;
      canvas.dispatchEvent(new WheelEvent('wheel',{clientX,clientY,deltaY,deltaMode,ctrlKey,cancelable:true}));
    },{passive:false});
    button.addEventListener('pointerdown',event => {
      if (event.pointerType==='mouse' && event.button!==0) return;
      event.preventDefault();
      bookPress={id,pointerId:event.pointerId};
      const {pointerId,pointerType,clientX,clientY,button,buttons,isPrimary}=event;
      canvas.dispatchEvent(new PointerEvent('pointerdown',{pointerId,pointerType,clientX,clientY,button,buttons,isPrimary,cancelable:true}));
    });
  }
});
const coverSelection=createCoverSelection({onChange(id) { covers.select(id); showBook(id); }});

function save() { try { localStorage.setItem(storageKey,JSON.stringify(state)); } catch { /* Progress remains in memory. */ } }
function restore() {
  try {
    const parsed=JSON.parse(localStorage.getItem(storageKey));
    state={version:1,lang:parsed?.version===1 && languages.includes(parsed.lang) ? parsed.lang : 'en',
      opened:parsed?.version===1 && Array.isArray(parsed.opened) ? [...new Set(parsed.opened.filter(id => Object.hasOwn(routes,id)))] : []};
    if (!state.opened.includes('lake')) state.opened=state.opened.filter(id => id!=='elder');
  } catch { /* Keep the current state when storage is blocked. */ }
}
function status(id) { return !availableStories.has(id) ? 'soon' : id==='elder' && !state.opened.includes('lake') ? 'locked' : state.opened.includes(id) ? 'opened' : 'available'; }
function canOpen(id) { return Object.hasOwn(routes,id) && !['locked','soon'].includes(status(id)); }
function storyHref(id) {
  const url=new URL(window.AtlasStories?.href(id,lang) || './?'+routes[id]+'&lang='+lang,location.href);
  url.searchParams.set('returnTo','atlas-webgpu.html'); url.searchParams.set('returnPlace',id);
  return url.href;
}
async function refreshStories() {
  if (!window.AtlasStories) return;
  try { availableStories=await window.AtlasStories.available(); }
  catch { availableStories=new Set(); }
  render();
}
function recordOpen(id) {
  saveCamera();
  restore(); if (!canOpen(id)) return;
  try { sessionStorage.setItem(returnStorageKey,JSON.stringify({place:id,pending:true})); } catch { /* The reader URL also carries the location. */ }
  if (!state.opened.includes(id)) state.opened.push(id);
  state.lang=lang; save(); motion?.update(state.opened);
}
function icon(name) {
  const node=document.createElement('i'); node.dataset.lucide=name; node.setAttribute('aria-hidden','true'); return node;
}
function label(id,text) { $(id).title=text; $(id).setAttribute('aria-label',text); }
function renderMotion() {
  const paused=motion?.paused ?? true;
  label('motion-toggle',words[lang][paused ? 'play' : 'pause']);
  $('motion-toggle').setAttribute('aria-pressed',String(!paused));
  $('motion-toggle').replaceChildren(icon(paused ? 'play' : 'pause'));
  window.lucide.createIcons(); ensureScenery(); invalidate();
}
function ensureScenery() {
  if (!renderer || sceneryStarted || suspended) return;
  if (motion?.paused) { sceneryState={enabled:false,reason:'paused'}; return; }
  sceneryStarted=true;
  loadScenery(renderer,{animate:!motion.paused}).then(value => {
    sceneryState=value;
    if (['paused','pagehide'].includes(value.reason)) {
      sceneryStarted=false;
      if (value.reason==='pagehide') ensureScenery();
    }
    invalidate();
  }).catch(error => {
    sceneryState={enabled:false,reason:String(error?.message || error)}; invalidate();
  });
}
function renderBokeh() {
  const available=renderer?.backend==='webgpu' && Boolean(renderer.stats?.dof);
  debugPanel.setAvailable(available);
  $('bokeh-toggle').disabled=!available;
  $('bokeh-toggle').setAttribute('aria-pressed',String(available && dof));
  $('bokeh-toggle').replaceChildren(icon(available && dof ? 'eye' : 'eye-off'));
  label('bokeh-toggle',words[lang].bokeh); window.lucide.createIcons();
}
function snapshot() { return camera.snapshot; }
function readCamera() {
  try {
    const saved=JSON.parse(sessionStorage.getItem(cameraStorageKey));
    if (saved && [saved.x,saved.y,saved.zoom].every(Number.isFinite) &&
        saved.x>=-.25*width && saved.x<=1.25*width && saved.y>=-.25*height && saved.y<=1.25*height && saved.zoom>0 && saved.zoom<=16) return saved;
  } catch { /* A blocked or invalid session keeps the opening camera. */ }
  return null;
}
function saveCamera() {
  if(familyPreview)return;
  if (!cameraReady) return;
  const s=snapshot(), zoom=s.scale/Math.max(s.width/width,s.height/height);
  if (![s.x,s.y,zoom].every(Number.isFinite) || zoom<=0 || zoom>16) return;
  try { sessionStorage.setItem(cameraStorageKey,JSON.stringify({x:s.x,y:s.y,zoom})); }
  catch { /* Camera interaction still works without storage. */ }
}
function restoreCamera() {
  const saved=readCamera();
  if (saved) {
    const s=snapshot();
    // Below-cover zoom is the camera's explicit overview mode.
    if (saved.zoom<1) camera.fit();
    else camera.focus([saved.x,saved.y],saved.zoom*Math.max(s.width/width,s.height/height));
    focusAllowed=true;
  }
  cameraReady=true;
  saveCamera();
}
function restoreReturnPlace() {
  const url=new URL(location.href), requested=url.searchParams.get('returnPlace');
  if (url.searchParams.has('returnPlace') && !places.includes(requested)) return;
  let saved;
  try { saved=JSON.parse(sessionStorage.getItem(returnStorageKey)); } catch { /* Ignore blocked or corrupt storage. */ }
  const stored=places.includes(saved?.place) ? saved.place : null;
  const id=saved?.pending===true && stored ? stored : requested || stored;
  if (!id || !motion?.placeAtLocation(id)) return;
  clearTimeout(settleTimer); targetPending=false; selection=null; arrival=null;
  url.searchParams.set('returnPlace',id); history.replaceState(history.state,'',url);
  try { sessionStorage.setItem(returnStorageKey,JSON.stringify({place:id,pending:false})); } catch { /* Keep the URL fallback. */ }
}
// Keep camera coordinates in the same shape as the legacy map controller.
const facade={
  getSize() { const s=snapshot(); return {x:s.width,y:s.height}; },
  containerPointToLatLng(point) { const [x,y]=camera.screenToWorld(point); return {x,y}; },
  getCenter() { const s=snapshot(); return this.containerPointToLatLng([s.width/2,s.height/2]); },
  getZoom() { return Math.log2(snapshot().scale); }
};
function positionBook() {
  const obscured=previewPending || preview.open;
  renderer?.suspend(suspended || obscured);
  motion?.suspend(obscured);
  if (camera) covers.hide(obscured);
}
function showBook(id) {
  focused=id; viewport.dataset.focus=id || ''; motion?.focus(id);
  anchor=regions.find(region => region.id===id)?.center || null;
  $('map-status').textContent=id ? words[lang][id]+': '+words[lang][status(id)] : '';
  positionBook();
  if (keyboardRequest===id) { covers.focus(id); keyboardRequest=null; }
}
async function openBook(id) {
  if (moving || previewPending || preview.open || !canOpen(id)) return;
  clearTimeout(settleTimer); targetPending=false; arrival=null;
  focused=id; viewport.dataset.focus=id;
  const opening=++bookRequest; previewPending=true; positionBook();
  await preview.show(id,lang,words[lang],storyHref(id));
  if (opening===bookRequest) { previewPending=false; positionBook(); }
}
function chooseBook() {
  syncCharacterCover();
  positionBook();
}
function syncCharacterCover() {
  if (!detector || !camera) return;
  const x=Number(motionCanvas.dataset.x), y=Number(motionCanvas.dataset.y);
  if (!Number.isFinite(x) || !Number.isFinite(y) || (coverPoint?.[0]===x && coverPoint?.[1]===y)) return;
  coverPoint=[x,y];
  const sample=detector.sampleRegion([x/width,y/height]);
  const confidence=String(sample.confidence);
  if (viewport.dataset.coverConfidence!==confidence) viewport.dataset.coverConfidence=confidence;
  coverSelection.update(sample);
}
function arrive(point) {
  if (new URLSearchParams(location.search).get('spriteTrial')==='1' && new URLSearchParams(location.search).get('sandbox')==='1') return; // Sandbox never enters places.
  const doorway=geometry.routes.find(route => route.id==='home-to-lake')?.points[0];
  // Only the completed walk into the doorway enters the house, not the wider home region.
  const entry=motion?.reviewDiagnostics?.planner?.endpoint;
  const requested=motion?.reviewDiagnostics?.planner?.goal;
  const projectedDoor=entry && requested && doorway &&
    Math.hypot(requested[0]-doorway[0]*width,requested[1]-doorway[1]*height)<=2 &&
    point && Math.hypot(point[0]*width-entry[0],point[1]*height-entry[1])<=4;
  if (doorway && point && (projectedDoor || Math.hypot((point[0]-doorway[0])*geometry.width,(point[1]-doorway[1])*geometry.height)<=2)) {
    saveCamera(); state.lang=lang; save();
    try { sessionStorage.setItem(returnStorageKey,JSON.stringify({place:'home',pending:false})); } catch { /* The menu URL preserves the language. */ }
    const menu=new URL('../',location.href); menu.searchParams.set('lang',lang);
    location.assign(menu.href);
    return;
  }
  chooseBook();
}
function interact() { focusAllowed=true; targetPending=true; selection=null; arrival=null; }
function startMove() {
  if (!cameraReady) return;
  clearTimeout(settleTimer); moving=true;
  bookRequest++; previewPending=false;
  preview.dismiss(); positionBook(); invalidate();
}
function settle() {
  if (!cameraReady) return;
  clearTimeout(settleTimer);
  settleTimer=setTimeout(() => {
    moving=false;
    if (targetPending && camera && !preview.open) {
      const center=facade.getCenter(); motion?.setTarget([center.x/width,center.y/height]);
    }
    targetPending=false; chooseBook(); invalidate();
  },160);
}
function tap(point) {
  if (!detector || preview.open) return;
  const p=normalized(point), id=detector.regionAt(p,{nearby:true});
  clearTimeout(settleTimer); moving=false; targetPending=false; focusAllowed=true; arrival=null;
  selection=id ? {id,point:p} : null; motion?.setTarget(p); chooseBook(); invalidate();
}
function focusDestination(id) {
  const region=regions.find(r => r.id===id); if (!region || !camera) return;
  interact(); keyboardRequest=id; selection={id,point:region.center};
  const s=snapshot(), [,,w,h]=region.bounds;
  const scale=Math.max(Math.max(s.width/width,s.height/height)*2,
    Math.min(s.width/(w*width*1.6),s.height/(h*height*1.6)));
  camera.focus(world(region.center),scale); settle();
}
function invalidate() {
  if (!frame && renderer && camera && !document.hidden && !suspended) frame=requestAnimationFrame(draw);
}
function draw(now) {
  frame=0;
  if (!renderer || !camera || document.hidden || suspended || previewPending || preview.open) return;
  if (viewport.dataset.backend!==renderer.backend) {
    viewport.dataset.backend=renderer.backend; renderBokeh();
    covers.setGpuRendering(renderer.backend==='webgpu');
  }
  const s=snapshot(), x=Number(motionCanvas.dataset.x), y=Number(motionCanvas.dataset.y);
  const focus=Number.isFinite(x) && Number.isFinite(y) ? [x,y] : camera.screenToWorld([s.width/2,s.height/2]);
  renderer.render(s,{focus,dof:dof && renderer.backend==='webgpu',overlayVersion:motion.version,animate:!motion.paused,now});
  renderCount++;
}
function render() {
  const requested=new URL(location.href).searchParams.get('lang');
  lang=languages.includes(requested) ? requested : state.lang; state.lang=lang;
  const ui=words[lang]; document.documentElement.lang=lang; document.title=ui.title+' - '+ui.author;
  $('atlas-title').textContent=ui.title; $('atlas-author').textContent=ui.author;
  viewport.setAttribute('aria-label',ui.title); canvas.setAttribute('aria-label',ui.title);
  document.querySelector('.language-selector').setAttribute('aria-label',ui.language);
  document.querySelector('.atlas-actions').setAttribute('aria-label',ui.language);
  languageMenu.update(lang,ui.language);
  document.querySelector('.map-controls').setAttribute('aria-label',ui.view);
  $('map-regions').setAttribute('aria-label',ui.stories);
  for (const [id,text] of [['atlas-library',ui.library],['zoom-in',ui.in],['zoom-out',ui.out],['zoom-fit',ui.fit]]) label(id,text);
  $('atlas-library').href='library.html?lang='+lang;
  document.querySelectorAll('[data-lang]').forEach(button => button.setAttribute('aria-pressed',String(button.dataset.lang===lang)));
  $('map-regions').replaceChildren(...regions.map(region => {
    const link=document.createElement('a'); link.className='map-region'; link.dataset.place=region.id;
    link.dataset.state=status(region.id); link.href='#world-canvas'; link.textContent=ui[region.id]+': '+ui[status(region.id)];
    link.addEventListener('focus',() => focusDestination(region.id));
    link.addEventListener('click',event => { event.preventDefault(); focusDestination(region.id); });
    return link;
  }));
  covers.update(lang,ui).then(() => { if (keyboardRequest) covers.focus(keyboardRequest); });
  motion?.update(state.opened); renderMotion(); renderBokeh(); chooseBook();
}
function refresh() { restore(); render(); }
function resize() { camera?.resize(); positionBook(); invalidate(); settle(); }

motion=window.AtlasMotion.create(motionCanvas,geometry,event => {
  if (event?.type==='arrival') arrive(event.point); else renderMotion();
  invalidate();
},() => { syncCharacterCover(); invalidate(); },runtime);
if(runtime.production)motion.ready.then(restoreReturnPlace);
else restoreReturnPlace();
camera=createCamera(canvas,{worldWidth:width,worldHeight:height,
  onChange() { saveCamera(); positionBook(); invalidate(); },onMoveStart:startMove,onMoveKindChange:startMove,onMoveEnd:settle,
  onTap(point,event) { if (bookPress?.pointerId===event.pointerId) openBook(bookPress.id); else tap(point); },
  onPoint(point) { if (!moving && !preview.open) { motion.setTarget(normalized(point)); invalidate(); } }
});
restoreCamera();
for (const name of ['pointerup','pointercancel']) addEventListener(name,event => {
  if (bookPress?.pointerId===event.pointerId) bookPress=null;
});
canvas.addEventListener('pointerdown',interact,{passive:true});
canvas.addEventListener('wheel',interact,{passive:true});
canvas.addEventListener('keydown',event => {
  const keys=['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','+','-','=','Home'];
  if (!keys.includes(event.key)) return;
  event.preventDefault(); interact();
  if (event.key==='Home') camera.fit();
  else if (event.key==='+' || event.key==='=') camera.zoomBy(1.32);
  else if (event.key==='-') camera.zoomBy(1/1.32);
  else {
    const s=snapshot(), step=80/s.scale;
    camera.focus([s.x+(event.key==='ArrowLeft' ? -step : event.key==='ArrowRight' ? step : 0),
      s.y+(event.key==='ArrowUp' ? -step : event.key==='ArrowDown' ? step : 0)]);
  }
});
$('zoom-in').onclick=() => { interact(); camera.zoomBy(1.32); };
$('zoom-out').onclick=() => { interact(); camera.zoomBy(1/1.32); };
$('zoom-fit').onclick=() => { interact(); camera.fit(); };
$('motion-toggle').onclick=() => motion.toggle();
$('bokeh-toggle').onclick=() => { dof=!dof; renderBokeh(); invalidate(); };
document.querySelectorAll('[data-lang]').forEach(button => button.addEventListener('click',() => {
  bookRequest++; previewPending=false;
  preview.dismiss(true);
  if (history.state?.atlasPreview) history.replaceState(null,'');
  const url=new URL(location.href); url.searchParams.set('lang',button.dataset.lang);
  history.pushState(null,'',url); render(); save();
}));
addEventListener('popstate',refresh);
addEventListener('storage',event => {
  if (event.key===storageKey || event.key===null) { preview.dismiss(); refresh(); }
});
addEventListener('resize',resize);
addEventListener('pagehide',() => { saveCamera(); suspended=true; renderer?.suspend(true); cancelAnimationFrame(frame); frame=0; clearTimeout(settleTimer); });
addEventListener('pageshow',event => { suspended=false; if (event.persisted) restoreReturnPlace(); refresh(); resize(); });
document.addEventListener('visibilitychange',() => {
  if (document.hidden) { cancelAnimationFrame(frame); frame=0; } else invalidate();
});
window.atlasGpuDebug=Object.freeze({camera,motion,motionCanvas,preview,facade,world,normalized,focusDestination,covers,coverSelection,debugPanel,
  get recorder() { return reviewRecorder; },
  get renderer() { return renderer; },get detector() { return detector; },
  get focus() { return {id:focused,semantic:detector?.diagnostic}; },get moving() { return moving; },
  get selection() { return selection; },get dof() { return dof; },get renderCount() { return renderCount; },
  get rendererError() { return rendererError; },get scenery() { return sceneryState; }
});
refresh();
refreshStories();
window.AtlasFocus.create(geometry).then(value => {
  detector=value; viewport.dataset.mask='ready';
  // Restoring a parked character is not a new arrival into the house.
  chooseBook();
}).catch(() => { viewport.dataset.mask='unavailable'; $('map-status').textContent=words[lang].unavailable; });
try {
  renderer=await createRenderer({canvas,artSrc:'images/atlas/shire-v1.webp',depthSrc:'images/atlas/shire-depth-v1.webp',overlayCanvas:motionCanvas,
    onError(error) {
      rendererError=String(error?.message || error); viewport.dataset.rendererError=rendererError; invalidate();
    }
  });
  renderer.setBokehStrength(bokehStrength);
  renderer.setLensOptions?.(lensOptions);
  renderer.setBannerLayer?.(covers.gpuLayer);
  covers.setGpuRendering(renderer.backend==='webgpu');
  if (renderer.backend==='webgpu') loadSurfaceSampler().then(surface => {
    covers.setSurfaceSampler({depth:(x,y) => renderer.sampleDepth(x,y),
      normal:(x,y) => surface.normalAt(x/width,y/height)});
    invalidate();
  }).catch(() => { /* Authored orientation remains usable if estimated normals fail to load. */ });
  positionBook();
  ensureScenery();
  viewport.dataset.backend=renderer.backend; renderBokeh(); invalidate();
  if(runtime.reviewCapture) {
    // Optional local tool, deliberately outside the production dependency closure.
    const recorderSrc='./atlas-review-recorder'+'.js';
    import(recorderSrc).then(({createReviewRecorder}) =>
      createReviewRecorder({camera,motion,renderer,canvas,viewport})).then(value => {reviewRecorder=value;})
      .catch(error => {console.warn('Review recorder unavailable:',error.message);});
  }
  if(familyPreview) {
    motion.startFamilyPreview();
    camera.focus([1030,570],Math.min(innerWidth/410,2.6));
  }
} catch (error) {
  rendererError=String(error?.message || error); viewport.dataset.backend='unavailable';
  viewport.dataset.rendererError=rendererError; $('map-status').textContent=words[lang].unavailable;
  renderBokeh();
}
