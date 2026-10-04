// One-finger/pointer motion looks; two-finger translation or scrolling orbits.
export function tourGestures(stage,api,{captureButton=null,captureHint=null}={}){
  const points=new Map();let gesture=null,hover=null,twoFrame=0,mouseClick=null,lockPending=false;
  const interactive=e=>Boolean(e.target?.closest?.('button,a,input,select,textarea,[role="button"],[contenteditable="true"]'));
  const finePointer=matchMedia('(pointer:fine)').matches;
  const canCapture=finePointer&&typeof stage.requestPointerLock==='function';
  const locked=()=>document.pointerLockElement===stage;
  function clearInput(){
    if(twoFrame)cancelAnimationFrame(twoFrame);twoFrame=0;
    for(const id of points.keys())if(stage.hasPointerCapture(id))stage.releasePointerCapture(id);
    points.clear();gesture=null;hover=null;mouseClick=null;api.cancelInput?.();
  }
  function captureUI(message=null){
    stage.dataset.mouseCaptured=String(locked());
    if(captureButton){captureButton.hidden=!canCapture;captureButton.textContent=locked()?'Release mouse':'Capture mouse';captureButton.setAttribute('aria-pressed',String(locked()));}
    if(captureHint){captureHint.hidden=!finePointer;captureHint.textContent=message||(locked()?'Mouse captured: look freely in any direction. Two-finger scroll orbits. Press Escape to release.':canCapture?'Click the scene or Capture mouse for continuous 360° looking. Press Escape to release.':'Mouse capture is unavailable here. Use repeated drags to keep looking around.');}
  }
  function captureError(){lockPending=false;captureUI('Mouse capture was unavailable or denied. Keep using normal pointer movement or repeated drags; you can try Capture mouse again.');}
  function requestCapture(e){
    if(!e.isTrusted||!canCapture||locked()||lockPending)return;
    lockPending=true;
    try{const request=stage.requestPointerLock();if(request?.catch)request.catch(captureError);}catch{captureError();}
  }
  function releaseMouse(){if(locked())document.exitPointerLock();}
  document.addEventListener('pointerlockchange',()=>{lockPending=false;clearInput();captureUI();if(locked())stage.focus({preventScroll:true});});
  document.addEventListener('pointerlockerror',captureError);
  document.addEventListener('mousemove',e=>{if(!locked())return;const dx=Number.isFinite(e.movementX)?e.movementX:0,dy=Number.isFinite(e.movementY)?e.movementY:0;if(dx||dy)lookMove(dx,dy);});
  stage.addEventListener('click',e=>{const click=mouseClick;mouseClick=null;if(!interactive(e)&&e.pointerType!=='touch'&&click?.eligible)requestCapture(e);});
  stage.addEventListener('keydown',e=>{if(e.key==='Enter'&&!interactive(e)&&canCapture){e.preventDefault();requestCapture(e);}});
  captureButton?.addEventListener('click',e=>{if(locked())releaseMouse();else requestCapture(e);});
  captureUI();
  const center=()=>{const p=[...points.values()].slice(0,2);return{x:(p[0].x+p[1].x)/2,y:(p[0].y+p[1].y)/2,d:Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y)};};
  function lookMove(dx,dy){api.startLook();api.drag(dx,dy);}
  function mouseMotion(e){
    if(locked())return;
    if(e.pointerType!=='mouse'||e.buttons||points.size||interactive(e)){hover=null;return;}
    const now=performance.now();
    if(!hover){hover={x:e.clientX,y:e.clientY,time:now,dx:0,dy:0,active:false};return;}
    const dx=e.clientX-hover.x,dy=e.clientY-hover.y,elapsed=now-hover.time;
    hover.x=e.clientX;hover.y=e.clientY;hover.time=now;
    // Re-entry, cursor warps, and small jitter are not look intent.
    if(elapsed>240||Math.hypot(dx,dy)>Math.min(120,stage.clientWidth*.3)){hover.dx=hover.dy=0;hover.active=false;return;}
    if(!hover.active){hover.dx+=dx;hover.dy+=dy;if(Math.hypot(hover.dx,hover.dy)<5)return;hover.active=true;lookMove(hover.dx,hover.dy);}
    else if(dx||dy)lookMove(dx,dy);
  }
  function flushTwo(){
    if(twoFrame)cancelAnimationFrame(twoFrame);twoFrame=0;
    if(gesture?.kind!=='two'||points.size<2)return;
    const c=center(),dx=c.x-gesture.start.x,dy=c.y-gesture.start.y,travel=Math.hypot(dx,dy),spread=Math.abs(c.d-gesture.start.d);
    if(!gesture.action){
      // Decide from a complete two-pointer sample, not the transient centroid
      // halfway through delivery of the two pointermove events.
      if(spread>=3&&spread>travel*1.3)gesture.action='pinch';
      else if(travel>=4){gesture.action='orbit';gesture.axis=Math.abs(dx)>=Math.abs(dy)?'x':'y';}
      else return;
    }
    if(gesture.action==='pinch'){if(c.d>0&&gesture.last.d>0){api.startLook();api.zoom(Math.log(gesture.last.d/c.d)*400);}}
    else api.orbit(gesture.origin+(gesture.axis==='x'?dx:dy)/stage.clientWidth);
    gesture.last=c;
  }
  stage.addEventListener('pointerenter',e=>{hover=null;mouseMotion(e);});
  stage.addEventListener('pointerleave',()=>{hover=null;});
  stage.addEventListener('contextmenu',e=>{if(!interactive(e))e.preventDefault();});
  function wheel(e){if(!locked()&&interactive(e))return;hover=null;e.preventDefault();const unit=e.deltaMode===1?16:e.deltaMode===2?stage.clientHeight:1;api.wheelInput(e.deltaX*unit,e.deltaY*unit,e.ctrlKey);}
  stage.addEventListener('wheel',e=>{if(!locked())wheel(e);},{passive:false});
  document.addEventListener('wheel',e=>{if(locked())wheel(e);},{passive:false});
  stage.addEventListener('pointerdown',e=>{
    hover=null;if(locked()||interactive(e)||(e.pointerType==='mouse'&&e.button!==0&&e.button!==2))return;
    mouseClick=e.pointerType==='mouse'&&e.button===0?{x:e.clientX,y:e.clientY,eligible:true}:null;
    points.set(e.pointerId,{x:e.clientX,y:e.clientY});stage.setPointerCapture(e.pointerId);
    if(e.pointerType==='touch'&&points.size===2){const c=center();gesture={kind:'two',start:c,last:c,origin:api.progress(),action:null,axis:null};return;}
    if(points.size>1)return;
    gesture={kind:'single',active:false,x:e.clientX,y:e.clientY,lastX:e.clientX,lastY:e.clientY,touch:e.pointerType==='touch'};
  });
  stage.addEventListener('pointermove',e=>{
    if(locked())return;
    if(mouseClick&&Math.hypot(e.clientX-mouseClick.x,e.clientY-mouseClick.y)>4)mouseClick.eligible=false;
    if(!points.has(e.pointerId)||!gesture){mouseMotion(e);return;}
    points.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if(gesture.kind==='two'){if(!twoFrame)twoFrame=requestAnimationFrame(flushTwo);return;}
    const dx=e.clientX-gesture.lastX,dy=e.clientY-gesture.lastY;
    if(!gesture.active){const totalX=e.clientX-gesture.x,totalY=e.clientY-gesture.y;if(Math.hypot(totalX,totalY)<(gesture.touch?8:3))return;gesture.active=true;lookMove(totalX,totalY);}
    else if(dx||dy)lookMove(dx,dy);
    gesture.lastX=e.clientX;gesture.lastY=e.clientY;
  });
  function release(e,cancelled=false){
    if(!points.has(e.pointerId))return;
    if(cancelled){if(twoFrame)cancelAnimationFrame(twoFrame);twoFrame=0;api.cancelInput?.();}
    else flushTwo();
    points.delete(e.pointerId);if(stage.hasPointerCapture(e.pointerId))stage.releasePointerCapture(e.pointerId);
    if(!points.size)gesture=null;
    else if(gesture?.kind==='two'){const p=points.values().next().value;gesture={kind:'single',active:false,x:p.x,y:p.y,lastX:p.x,lastY:p.y,touch:true};}
  }
  stage.addEventListener('pointerup',e=>release(e));stage.addEventListener('pointercancel',e=>release(e,true));
  return {releaseMouse,get state(){return{locked:locked(),canCapture,kind:gesture?.kind||(hover?.active?'hover-look':'idle'),action:gesture?.action??null,pointers:points.size,accepted:api.isLooking()};}};
}
