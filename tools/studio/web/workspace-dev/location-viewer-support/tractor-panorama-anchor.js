// Isolated rectangular source-frustum overlay. No generated pixels are rewritten.
export function tractorPanoramaAnchor(canvas, panorama, source, anchor={yaw:0,pitch:0,fov:65,aspect:16/9,featherStart:.94}, options={}) {
 const gl=canvas.getContext('webgl',{alpha:false,antialias:false,preserveDrawingBuffer:true});
 if(!gl)throw Error('WebGL unavailable');
 const shaders=[];
 function compile(type,text){const s=gl.createShader(type);gl.shaderSource(s,text);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));shaders.push(s);return s;}
 const program=gl.createProgram();
 gl.attachShader(program,compile(gl.VERTEX_SHADER,'attribute vec2 aPosition;varying vec2 p;void main(){p=aPosition;gl_Position=vec4(p,0.,1.);}'));
 gl.attachShader(program,compile(gl.FRAGMENT_SHADER,`precision highp float;
 varying vec2 p;uniform sampler2D uPanorama,uSource;uniform vec4 uCamera,uAnchor;uniform float uAspect,uFeather,uEnabled;
 void main(){
  vec3 r=normalize(vec3(p.x*uCamera.w*uCamera.z,p.y*uCamera.z,1.));
  float cy=cos(uCamera.x),sy=sin(uCamera.x),cp=cos(uCamera.y),sp=sin(uCamera.y);
  float y=r.y*cp+r.z*sp,z=r.z*cp-r.y*sp;
  vec3 world=vec3(r.x*cy+z*sy,y,z*cy-r.x*sy);
  vec2 uv=vec2(fract(.5+atan(world.x,world.z)/6.28318530718),.5-asin(clamp(world.y,-1.,1.))/3.14159265359);
  vec3 color=texture2D(uPanorama,uv).rgb;
  float ac=cos(uAnchor.x),as=sin(uAnchor.x),pc=cos(uAnchor.y),ps=sin(uAnchor.y);
  float ax=world.x*ac-world.z*as,az=world.x*as+world.z*ac;
  vec3 local=vec3(ax,world.y*pc-az*ps,world.y*ps+az*pc);
  if(uEnabled>.5&&local.z>0.){
   vec2 q=vec2(local.x/(local.z*uAnchor.z*uAspect),local.y/(local.z*uAnchor.z));
   float edge=max(abs(q.x),abs(q.y));
   if(edge<1.){
    float weight=1.-smoothstep(uFeather,1.,edge);
    color=mix(color,texture2D(uSource,vec2(.5+.5*q.x,.5-.5*q.y)).rgb,weight);
   }
  }
  gl_FragColor=vec4(color,1.);
 }`));
 gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);
 const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
 const pos=gl.getAttribLocation(program,'aPosition');gl.enableVertexAttribArray(pos);gl.vertexAttribPointer(pos,2,gl.FLOAT,false,0,0);
 // Full-resolution GPU LRU: keep the visible texture pinned, release decoded
 // images after upload, and never regenerate or resize panorama pixels.
 const panoramas=new Map(),maxPanoramas=options.maxPanoramas??3,maxBytes=options.maxBytes??96*1024*1024;
 let currentKey=null,bytes=0,peakBytes=0,panoramaUploads=0,sourceUploads=0;
 const recentVisits=[],visitLimit=Math.max(1,maxPanoramas-2);let warmKeys=new Set();
 function texture(unit){const t=gl.createTexture();gl.activeTexture(gl.TEXTURE0+unit);gl.bindTexture(gl.TEXTURE_2D,t);for(const n of[gl.TEXTURE_MIN_FILTER,gl.TEXTURE_MAG_FILTER])gl.texParameteri(gl.TEXTURE_2D,n,gl.LINEAR);for(const n of[gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T])gl.texParameteri(gl.TEXTURE_2D,n,gl.CLAMP_TO_EDGE);return t;}
 function trim(protectedKey){for(const[key,item]of panoramas){if(panoramas.size<=maxPanoramas&&bytes<=maxBytes)return;if(key===currentKey||key===protectedKey)continue;gl.deleteTexture(item.texture);bytes-=item.bytes;panoramas.delete(key);}}
 function cachePanorama(key,image,speculative=false){
  if(panoramas.has(key))return;
  const size=(image.naturalWidth||image.width)*(image.naturalHeight||image.height)*4;
  // Evict before allocation so a speculative upload cannot transiently exceed
  // the advertised retained-texture budget. Keep the visible texture pinned.
  if(size>maxBytes)throw Error('Panorama exceeds texture cache budget');
  const priority=key=>recentVisits.includes(key)?2:warmKeys.has(key)?1:0;
  const victims=[...panoramas].sort(([a],[b])=>priority(a)-priority(b));
  for(const[old,item]of victims){if(panoramas.size<maxPanoramas&&bytes+size<=maxBytes)break;if(old===currentKey||(speculative&&(recentVisits.includes(old)||warmKeys.has(old))))continue;gl.deleteTexture(item.texture);bytes-=item.bytes;panoramas.delete(old);}
  if(panoramas.size>=maxPanoramas||bytes+size>maxBytes)throw Error('No idle panorama cache capacity');
  const t=texture(0);
  gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);panoramaUploads++;
  panoramas.set(key,{texture:t,bytes:size});bytes+=size;peakBytes=Math.max(peakBytes,bytes);trim(key);
  // An idle upload must not replace the panorama currently being viewed.
  if(currentKey!==null)gl.bindTexture(gl.TEXTURE_2D,panoramas.get(currentKey).texture);
 }
 const anchorLocation=gl.getUniformLocation(program,'uAnchor'),aspectLocation=gl.getUniformLocation(program,'uAspect'),featherLocation=gl.getUniformLocation(program,'uFeather');
 function setPanorama(key,image,nextAnchor){
  if(!panoramas.has(key))cachePanorama(key,image);
  const item=panoramas.get(key);panoramas.delete(key);panoramas.set(key,item);currentKey=key;trim(key);
  const visit=recentVisits.indexOf(key);if(visit!==-1)recentVisits.splice(visit,1);recentVisits.push(key);while(recentVisits.length>visitLimit)recentVisits.shift();
  gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,item.texture);
  gl.uniform4f(anchorLocation,nextAnchor.yaw,nextAnchor.pitch,Math.tan(nextAnchor.fov*Math.PI/360),1);
  gl.uniform1f(aspectLocation,nextAnchor.aspect);gl.uniform1f(featherLocation,nextAnchor.featherStart);
 }
 const sourceTexture=texture(1);let sourceWidth=0,sourceHeight=0;
 function setSource(image){
  const w=image.videoWidth||image.naturalWidth||image.width,h=image.videoHeight||image.naturalHeight||image.height;
  gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,sourceTexture);
  if(w===sourceWidth&&h===sourceHeight)gl.texSubImage2D(gl.TEXTURE_2D,0,0,0,gl.RGBA,gl.UNSIGNED_BYTE,image);
  else{gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);sourceWidth=w;sourceHeight=h;}
  sourceUploads++;
 }
 if(source)setSource(source);else gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([0,0,0,255]));
 gl.uniform1i(gl.getUniformLocation(program,'uPanorama'),0);gl.uniform1i(gl.getUniformLocation(program,'uSource'),1);
 setPanorama(options.key??'initial',panorama,anchor);
 const camera=gl.getUniformLocation(program,'uCamera'),enabled=gl.getUniformLocation(program,'uEnabled');let active=true;
 return {
  hasPanorama:key=>panoramas.has(key),setWarmPanoramas(keys){warmKeys=new Set(keys);},cachePanorama,setPanorama,setSource,
  get stats(){return{cachedPanoramas:panoramas.size,bytes,peakBytes,panoramaUploads,sourceUploads,maxPanoramas,maxBytes,recentVisits:[...recentVisits]};},
  setEnabled(value){active=Boolean(value);},
  draw(s){const ratio=s.pixelRatio??Math.min(devicePixelRatio||1,1.5),w=Math.round(s.width*ratio),h=Math.round(s.height*ratio);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}gl.viewport(0,0,w,h);gl.uniform4f(camera,s.yaw,s.pitch,Math.tan(s.fov*Math.PI/360),s.width/s.height);gl.uniform1f(enabled,active?1:0);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);},
  readPixels(){const pixels=new Uint8Array(canvas.width*canvas.height*4);gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);return pixels;},
  destroy(){panoramas.forEach(item=>gl.deleteTexture(item.texture));panoramas.clear();bytes=0;gl.deleteTexture(sourceTexture);shaders.forEach(s=>gl.deleteShader(s));gl.deleteBuffer(buffer);gl.deleteProgram(program);}
 };
}
