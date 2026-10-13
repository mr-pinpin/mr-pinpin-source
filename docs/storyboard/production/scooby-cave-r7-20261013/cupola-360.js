import {cubemapRenderer} from '../../../home-cubemap-gl.js';
import {panoramaControls} from '../../../home-panorama-controls.js';
const stage=document.getElementById('stage'),canvas=document.getElementById('canvas');
const status=document.getElementById('status'),record=document.getElementById('view-record');
const initial={yaw:Math.atan2(7,8.33),pitch:20*Math.PI/180,fov:70};
const config={...initial,minFov:35,maxFov:100,maxPitch:89.5,hotspots:[]};
let controls,renderer;
function draw(s){renderer?.draw(s);record.textContent=`Fixed origin [-7, -6.33, 1.15]m · yaw ${(s.yaw*180/Math.PI).toFixed(1)}° · pitch ${(s.pitch*180/Math.PI).toFixed(1)}° · vertical FOV ${s.fov.toFixed(1)}°`;}
controls=panoramaControls(stage,config,draw);
const base='geometry/results/rotunda-cube-v2/';
// Use the existing room renderer's explicit face bases; exact90° geometry faces
// need full boundary coverage rather than the legacy overscan feather.
const faces=['front','right','back','left','up','down'];
Promise.all(faces.map(async id=>{const image=new Image();image.src=base+id+'.png';await image.decode();return[id,image]})).then(entries=>{renderer=cubemapRenderer(canvas,Object.fromEntries(entries),{faceFov:90,exactCube:true});stage.dataset.ready='true';status.textContent='Fixed-camera geometry ready. Turn to compare openings, bank, lake and the one oculus.';draw(controls.snapshot);}).catch(error=>{status.textContent='Review media unavailable: restore the recorded R7 asset scope.';console.error(error);});
const views={reveal:initial,front:{yaw:0,pitch:0},right:{yaw:Math.PI/2,pitch:0},back:{yaw:Math.PI,pitch:0},left:{yaw:-Math.PI/2,pitch:0},up:{yaw:0,pitch:Math.PI/2},down:{yaw:0,pitch:-Math.PI/2}};
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>controls.setCamera({...views[button.dataset.view],fov:70})));
window.cupolaReview={setView:value=>controls.setCamera(value),get view(){return controls.snapshot}};
