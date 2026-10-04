import {RAD,TAU,clamp,wrap,worldRay,anchored} from './home-panorama-math.js?v=panorama-20260922';
export function panoramaControls(stage,config,onChange){
 const s={yaw:config.yaw,pitch:config.pitch,fov:config.fov,width:1,height:1,totalYaw:0};
 const pointers=new Map(),listeners=[];let base,pinch,blocked=false,keyboard=false;
 function listen(node,type,fn,options){node.addEventListener(type,fn,options);listeners.push(()=>node.removeEventListener(type,fn,options));}
 function change(){s.fov=clamp(s.fov,config.minFov,config.maxFov);s.pitch=clamp(s.pitch,-config.maxPitch*RAD,config.maxPitch*RAD);s.yaw=wrap(s.yaw);onChange({...s});}
 const local=e=>{const r=stage.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top};};
 const pair=()=>{const[a,b]=[...pointers.values()];return{mid:{x:(a.x+b.x)/2,y:(a.y+b.y)/2},distance:Math.max(1,Math.hypot(a.x-b.x,a.y-b.y))};};
 function baseline(){if(pointers.size>1){const p=pair();pinch={...p,tangent:Math.tan(s.fov*RAD/2),target:worldRay(p.mid,s)};}else{pinch=null;const p=pointers.values().next().value;base=p?{...p,yaw:s.yaw,pitch:s.pitch}:null;}}
 listen(stage,'pointerdown',e=>{if(e.pointerType==='mouse'&&e.button!==0)return;if(!pointers.size)blocked=false;keyboard=false;pointers.set(e.pointerId,local(e));e.target.setPointerCapture?.(e.pointerId);if(pointers.size>1)blocked=true;baseline();});
 listen(window,'pointermove',e=>{if(!pointers.has(e.pointerId))return;e.preventDefault();const p=local(e);pointers.set(e.pointerId,p);const old=s.yaw;if(pinch){const next=pair();s.fov=clamp(2*Math.atan(pinch.tangent*pinch.distance/next.distance)/RAD,config.minFov,config.maxFov);anchored(pinch.target,next.mid,s);blocked=true;}else if(base){const dx=p.x-base.x,dy=p.y-base.y;if(Math.hypot(dx,dy)>5)blocked=true;if(blocked){const speed=s.fov*RAD/s.height;s.yaw=base.yaw-dx*speed;s.pitch=base.pitch+dy*speed;}}if(blocked){s.totalYaw+=wrap(s.yaw-old);change();}stage.classList.toggle('is-dragging',blocked);},{passive:false});
 function release(e){if(!pointers.has(e.pointerId))return;if(e.type!=='pointerup')blocked=true;pointers.delete(e.pointerId);baseline();if(!pointers.size)stage.classList.remove('is-dragging');}
 for(const event of ['pointerup','pointercancel','lostpointercapture'])listen(window,event,release);
 listen(stage,'click',e=>{if(blocked&&e.detail!==0){e.preventDefault();e.stopImmediatePropagation();}},true);
 listen(stage,'dragstart',e=>e.preventDefault());
 listen(stage,'wheel',e=>{e.preventDefault();if(pointers.size)return;const p=local(e),target=worldRay(p,s),delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?s.height:1),old=s.yaw;s.fov=clamp(2*Math.atan(Math.tan(s.fov*RAD/2)*Math.exp(delta*.0015))/RAD,config.minFov,config.maxFov);anchored(target,p,s);s.totalYaw+=wrap(s.yaw-old);change();},{passive:false});
 listen(document,'keydown',()=>{keyboard=true;},true);listen(document,'pointerdown',()=>{keyboard=false;},true);
 listen(stage,'keydown',e=>{let handled=true;switch(e.key){case'ArrowLeft':s.yaw-=8*RAD;s.totalYaw-=8*RAD;break;case'ArrowRight':s.yaw+=8*RAD;s.totalYaw+=8*RAD;break;case'ArrowUp':s.pitch+=8*RAD;break;case'ArrowDown':s.pitch-=8*RAD;break;case'+':case'=':s.fov-=5;break;case'-':s.fov+=5;break;case'Home':s.yaw=config.yaw;s.pitch=config.pitch;s.fov=config.fov;break;default:handled=false;}if(handled){e.preventDefault();change();}});
 listen(stage,'focusin',e=>{const id=e.target.dataset.panoramaHotspot;if(!id||(!keyboard&&!e.target.matches(':focus-visible')))return;const h=config.hotspots.find(h=>h.id===id);s.yaw=(h.anchor[0]-.5)*TAU;s.pitch=(.5-h.anchor[1])*Math.PI;s.fov=config.fov;change();});
 const resize=()=>{const r=stage.getBoundingClientRect();s.width=Math.max(1,r.width);s.height=Math.max(1,r.height);pointers.clear();pinch=base=null;change();};const observer=new ResizeObserver(resize);observer.observe(stage);resize();
 listen(window,'blur',()=>{pointers.clear();pinch=base=null;blocked=true;});
 return {get snapshot(){return{...s};},setCamera(camera){if(!camera||![camera.yaw,camera.pitch,camera.fov].every(Number.isFinite))return;s.yaw=camera.yaw;s.pitch=camera.pitch;s.fov=camera.fov;change();},destroy(){observer.disconnect();listeners.forEach(off=>off());pointers.clear();}};
}
