import {panoramaRenderer} from './location-viewer-support/home-panorama-gl.js';
import {panoramaControls} from './location-viewer-support/home-panorama-controls.js';
import {tractorPanoramaAnchor} from './location-viewer-support/tractor-panorama-anchor.js';
import {tourGestures} from './location-viewer-support/tractor-viewer-gestures.js';
import {RAD,clamp,wrap} from './location-viewer-support/home-panorama-math.js';
const ID=/^[A-Za-z0-9_.-]{1,160}$/,SHA=/^[a-f0-9]{64}$/;
export const loop=p=>((p%1)+1)%1;
export function nearestAvailable(stops,progress,duration){
 if(!Number.isFinite(duration)||duration<=0)return null;
 return stops.filter(s=>s.available&&Number.isFinite(s.actualTimestampSeconds)&&s.actualTimestampSeconds>=0&&s.actualTimestampSeconds<duration).reduce((best,s)=>{const distance=Math.abs(loop(s.actualTimestampSeconds/duration-progress+.5)-.5);return !best||distance<best.distance?{stop:s,distance}:best;},null)?.stop||null;
}
function identity(row,kind){if(!row||!ID.test(row.id)||!SHA.test(row.sha256)||!Number.isSafeInteger(row.bytes)||row.bytes<=0||row.bytes>268435456||!(kind==='video'?['video/mp4','video/webm']:['image/png','image/jpeg','image/webp']).includes(row.mime))throw Error('Invalid registered media identity/type');return {...row};}
function camera(c){if(!c||![c.yaw,c.pitch,c.fov].every(Number.isFinite)||Math.abs(c.pitch)>89*RAD||c.fov<20||c.fov>120)throw Error('Explicit valid camera yaw/pitch radians and FOV degrees required');return {...c};}
export function buildLocationDescriptor(manifest,registry){
 if(!manifest||manifest.schemaVersion!==1||!ID.test(manifest.id)||!SHA.test(manifest.sha256)||!Array.isArray(manifest.stops||[])||(manifest.stops||[]).length>24)throw Error('Invalid bounded location manifest');
 const resolve=(ref,kind)=>{if(!ref||!ID.test(ref.id)||!SHA.test(ref.sha256))throw Error('Hash-pinned registered reference required');const row=registry[ref.id];if(!row||row.sha256!==ref.sha256)throw Error('Registry/manifest media identity differs');return identity({...row,id:ref.id},kind);};
 if((manifest.repairs||[]).length>4)throw Error('At most four registered repairs');
 const stops=(manifest.stops||[]).map(s=>{if(!ID.test(s.id)||!Number.isFinite(s.actualTimestampSeconds)||s.actualTimestampSeconds<0)throw Error('Exact stop id and actual seconds required');const available=!!s.panorama&&s.status==='reviewed';return {...s,available,camera:camera(s.camera),panorama:s.panorama?resolve(s.panorama,'image'):null,sourceFrame:s.sourceFrame?resolve(s.sourceFrame,'image'):null};});
 if(new Set(stops.map(s=>s.id)).size!==stops.length)throw Error('Duplicate stops');
 return {id:manifest.id,sha256:manifest.sha256,reviewStatus:manifest.reviewStatus||'unreviewed',projection:manifest.projection,panorama:manifest.panorama?resolve(manifest.panorama,'image'):null,camera:camera(manifest.camera||{yaw:0,pitch:0,fov:72}),orbit:manifest.orbit?resolve(manifest.orbit,'video'):null,stops,repairs:(manifest.repairs||[]).map(r=>{if(!['front','rear','up','down'].includes(r.face))throw Error('Unknown repair face');return {...r,media:resolve(r.media,'image')};}),repairCalibration:manifest.repairCalibration,readOnly:!!manifest.readOnly};
}
export function mountLocationViewer(container,descriptor,{resolveAsset,compose,onError=()=>{},readOnly=false}={}){
 if(typeof resolveAsset!=='function')throw Error('Trusted registered-media resolver required');
 if(descriptor.projection!=='equirectangular')throw Error('Only explicit equirectangular panoramas supported');
 const doc=container.ownerDocument,offs=[],images=new Set(),waiters=new Set();let dead=false,epoch=0,renderer=null,controls=null,gestures=null,active=null,mode='idle',drawFrame=0,seekFrame=0,desired=null,ready=false,pendingDrag={x:0,y:0},pendingZoom=0;
 const cam={...camera(descriptor.camera),width:1,height:1};
 const create=(tag,label)=>{const el=doc.createElement(tag);if(label)el.textContent=label;return el;};
 const section=create('section'),title=create('h3','Existing location media'),status=create('p','Select media to load. No archive restoration or generation.'),stage=create('div'),canvas=create('canvas'),video=create('video'),load=create('button','Load selected panorama'),orbitButton=create('button','Load / return to orbit'),play=create('button','Play / pause orbit'),use=create('button','Use this view in brief'),slider=create('input');
 section.dataset.locationViewer=descriptor.id;section.dataset.selectionSha=descriptor.sha256;stage.tabIndex=0;stage.style.cssText='position:relative;min-height:240px;aspect-ratio:16/9;touch-action:none;overflow:hidden';canvas.style.cssText='width:100%;height:100%;display:block';video.style.cssText='width:100%;height:100%;display:none';video.preload='none';video.playsInline=true;video.loop=true;video.muted=true;slider.type='range';slider.min='0';slider.max='100';slider.step='.1';slider.disabled=true;play.disabled=true;use.disabled=readOnly||descriptor.readOnly;orbitButton.disabled=!descriptor.orbit;load.disabled=!descriptor.panorama&&!descriptor.stops.some(s=>s.available);
 stage.append(canvas,video);section.append(title,status,stage,load,orbitButton,play,slider,use);container.append(section);
 const listen=(el,name,fn,opts)=>{el.addEventListener(name,fn,opts);offs.push(()=>el.removeEventListener(name,fn,opts));};
 function report(error){if(dead)return;status.textContent=error.message||String(error);onError(error);}
 function draw(){drawFrame=0;if(dead||!renderer||mode!=='look')return;const r=stage.getBoundingClientRect();cam.width=Math.max(1,r.width);cam.height=Math.max(1,r.height);renderer.draw(cam);}
 function requestDraw(){if(!drawFrame)drawFrame=requestAnimationFrame(draw);}
 function clearRenderer(){controls?.destroy();controls=null;renderer?.destroy();renderer=null;}
 function progress(){return ready&&video.duration>0?video.currentTime/video.duration:0;}
 async function image(row,own){identity(row,'image');const src=await resolveAsset(row);if(dead||own!==epoch)throw Error('Stale media selection');return new Promise((yes,no)=>{const img=new Image();images.add(img);const cancel=()=>{waiters.delete(cancel);img.onload=null;img.onerror=null;img.src='';no(Error('Stale media selection'));};waiters.add(cancel);img.onload=()=>{waiters.delete(cancel);if(dead||own!==epoch){img.src='';no(Error('Stale media selection'));return;}if(!img.naturalWidth||!img.naturalHeight){no(Error('Image decode failed'));return;}yes(img);};img.onerror=()=>{waiters.delete(cancel);no(Error('Registered image unavailable'));};img.src=src;});}
 function waitSeek(own){return new Promise((yes,no)=>{let timer=null;const finish=()=>{waiters.delete(cancel);if(timer)clearTimeout(timer);video.removeEventListener('seeked',check);};const cancel=()=>{finish();no(Error('Stale media selection'));};const check=()=>{if(dead||own!==epoch)return cancel();if(desired===null&&!video.seeking){finish();yes();}};waiters.add(cancel);video.addEventListener('seeked',check);timer=setTimeout(()=>{finish();no(Error('Selected source frame seek timed out'));},5000);requestAnimationFrame(check);});}
 function seek(p){if(!ready)return;video.pause();desired=Math.min(loop(p)*video.duration,Math.max(0,video.duration-.001));slider.value=String(loop(p)*100);if(!seekFrame)seekFrame=requestAnimationFrame(pump);}
 function pump(){seekFrame=0;if(dead||!ready||desired===null||video.seeking)return;const next=desired;desired=null;video.currentTime=next;}
 function orbit(p=progress()){epoch++;pendingDrag={x:0,y:0};pendingZoom=0;mode='orbit';clearRenderer();canvas.style.display='none';video.style.display='block';seek(p);status.textContent='Recorded orbit; visible loop join and possible detail drift. Two-finger move/scroll orbits; one finger looks.';}
 function applyLook(){if(mode!=='look')return;cam.yaw=wrap(cam.yaw-pendingDrag.x/stage.clientWidth*cam.fov*RAD);cam.pitch=clamp(cam.pitch+pendingDrag.y/stage.clientHeight*cam.fov*RAD,-89*RAD,89*RAD);cam.fov=clamp(cam.fov*Math.exp(pendingZoom*.0015),20,100);pendingDrag={x:0,y:0};pendingZoom=0;requestDraw();}
 async function look(forced=null){
  if(dead||mode==='loading-look'||mode==='look'&&!forced)return;
  const stop=forced||nearestAvailable(descriptor.stops,progress(),video.duration);const row=stop?.panorama||descriptor.panorama;if(!row)return;
  const own=++epoch;mode='loading-look';video.pause();status.textContent='Loading selected existing panorama…';
  try{
   if(stop&&ready){seek(stop.actualTimestampSeconds/video.duration);await waitSeek(own);}
   const base=await image(row,own);if(base.naturalWidth!==2*base.naturalHeight)throw Error('Selected media is not a 2:1 spherical panorama');
   let source=null;
   if(stop?.sourceFrame)source=ready&&Math.abs(video.currentTime-stop.actualTimestampSeconds)<.05?video:await image(stop.sourceFrame,own);
   if(dead||own!==epoch)return;
   clearRenderer();Object.assign(cam,stop?.camera||descriptor.camera);active=stop||null;
   if(stop&&source){renderer=tractorPanoramaAnchor(canvas,base,source,{...stop.camera,aspect:source===video?video.videoWidth/video.videoHeight:source.naturalWidth/source.naturalHeight,featherStart:.94},{key:stop.id,maxPanoramas:1,maxBytes:96*1024*1024});}
   else{const repairs={};for(const r of descriptor.repairs||[])repairs[r.face]=await image(r.media,own);if(dead||own!==epoch)return;renderer=panoramaRenderer(canvas,base,repairs,descriptor.repairCalibration?{repairs:descriptor.repairCalibration}:undefined);}
   mode='look';canvas.style.display='block';video.style.display='none';status.textContent=`${stop?.id||descriptor.id} · ${row.reviewStatus||descriptor.reviewStatus} · fixed illustrated viewpoint${source?' · source-frame anchored ('+(stop?.sourceLockStatus||'unreviewed')+')':' · unanchored'}`;
   if(!descriptor.orbit){controls=panoramaControls(stage,{...cam,minFov:20,maxFov:100,maxPitch:89,hotspots:[]},state=>{Object.assign(cam,state);requestDraw();});}
   images.forEach(img=>{img.onload=null;img.onerror=null;img.src='';});images.clear();
   applyLook();requestDraw();
  }catch(error){if(own===epoch&&!dead){mode=ready?'orbit':'idle';report(error);}}
 }
 async function loadOrbit(){if(!descriptor.orbit)return;try{if(!video.getAttribute('src')){const own=++epoch;const src=await resolveAsset(identity(descriptor.orbit,'video'));if(dead||own!==epoch)return;video.src=src;video.load();}orbit();}catch(error){report(error);}}
 listen(video,'loadedmetadata',()=>{ready=Number.isFinite(video.duration)&&video.duration>0;slider.disabled=!ready;play.disabled=!ready;});listen(video,'seeked',()=>{if(desired!==null&&!seekFrame)seekFrame=requestAnimationFrame(pump);});listen(video,'timeupdate',()=>{if(desired===null)slider.value=String(progress()*100);});listen(video,'error',()=>{ready=false;slider.disabled=play.disabled=true;report(Error('Registered orbit unavailable'));});
 listen(load,'click',()=>look());listen(orbitButton,'click',loadOrbit);listen(play,'click',async()=>{if(!ready)return;const wasPaused=video.paused;if(mode!=='orbit')orbit();try{if(wasPaused)await video.play();else video.pause();}catch(e){report(e);}});listen(slider,'input',()=>orbit(Number(slider.value)/100));
 for(const stop of descriptor.stops.filter(s=>s.available)){const button=create('button',stop.id);button.dataset.locationStop=stop.id;section.append(button);listen(button,'click',()=>{if(ready){seek(stop.actualTimestampSeconds/video.duration);}look(stop);});}
 listen(use,'click',()=>{if(use.disabled)return;const media=mode==='orbit'?descriptor.orbit:active?.panorama||descriptor.panorama;if(!media)return;compose?.(`Use existing location ${descriptor.id} [selection ${descriptor.sha256}], ${mode==='orbit'?'recorded orbit at '+video.currentTime+' seconds':active?.id||'selected panorama'}; yaw ${cam.yaw} rad, pitch ${cam.pitch} rad, FOV ${cam.fov} degrees. Media ${media.id}, SHA ${media.sha256}. Preserve its existing role and review status; illustrated scenery is not measured geometry.`);});
 if(descriptor.orbit){gestures=tourGestures(stage,{progress,startLook:()=>{void look();},drag:(x,y)=>{pendingDrag.x+=x;pendingDrag.y+=y;applyLook();},zoom:value=>{pendingZoom+=value;applyLook();},orbit:p=>orbit(p),wheelInput:(x,y,pinch)=>{if(pinch){void look();pendingZoom+=y;applyLook();}else if(ready)orbit(progress()+(Math.abs(x)>Math.abs(y)?x:y)/stage.clientWidth);},cancelInput:()=>{pendingDrag={x:0,y:0};pendingZoom=0;},isLooking:()=>mode==='look'});}
 listen(stage,'keydown',e=>{if(e.target!==stage||!descriptor.orbit)return;if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','+','-'].includes(e.key)){e.preventDefault();if(mode==='orbit'&&['ArrowLeft','ArrowRight'].includes(e.key)){seek(progress()+(e.key==='ArrowRight'?.01:-.01));return;}void look();if(e.key==='Home')Object.assign(cam,active?.camera||descriptor.camera);else if(e.key==='+'||e.key==='-')pendingZoom+=e.key==='+'?-80:80;else{pendingDrag.x+=e.key==='ArrowLeft'?20:e.key==='ArrowRight'?-20:0;pendingDrag.y+=e.key==='ArrowUp'?20:e.key==='ArrowDown'?-20:0;}applyLook();}});
 const resize=new ResizeObserver(requestDraw);resize.observe(stage);
 return {get snapshot(){return {mode,ready,stop:active?.id||null,selectionSHA256:descriptor.sha256,camera:{...cam},progress:progress(),duration:video.duration,availableStops:descriptor.stops.filter(s=>s.available).map(s=>s.id),gesture:gestures?.state||null};},destroy(){if(dead)return;dead=true;epoch++;waiters.forEach(cancel=>cancel());images.forEach(img=>{img.onload=null;img.onerror=null;img.src='';});images.clear();gestures?.destroy();clearRenderer();resize.disconnect();offs.splice(0).forEach(off=>off());if(drawFrame)cancelAnimationFrame(drawFrame);if(seekFrame)cancelAnimationFrame(seekFrame);video.pause();video.removeAttribute('src');video.load();section.remove();}};
}
