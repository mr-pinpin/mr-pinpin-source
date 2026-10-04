// Perspective rays sample a spherical base plus calibrated perspective repair faces.
export function panoramaRenderer(canvas,image,repairs={},config={repairs:{fov:110,frontMask:[.102,-.028,.075,.075]}}){
 const gl=canvas.getContext('webgl',{alpha:false,antialias:false,powerPreference:'low-power'});if(!gl)throw Error('WebGL unavailable');
 const shaders=[];function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('Panorama shader unavailable');shaders.push(s);return s;}
 const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,'attribute vec2 aPosition;varying vec2 p;void main(){p=aPosition;gl_Position=vec4(aPosition,0.,1.);}'));
 gl.attachShader(program,shader(gl.FRAGMENT_SHADER,`precision highp float;varying vec2 p;
 uniform sampler2D uImage,uFront,uRear,uUp,uDown;uniform vec4 uCamera,uEnabled,uFrontMask;uniform float uPatchTan;
 vec4 repair(sampler2D image,vec3 local,float enabled,float front){
  if(enabled<.5||local.z<=0.)return vec4(0.);
  vec2 q=local.xy/(local.z*uPatchTan);float edge=max(abs(q.x),abs(q.y));
  if(edge>=.96)return vec4(0.);
  float weight=1.-smoothstep(.70,.96,edge);
  if(front>.5){vec2 mask=abs((q-uFrontMask.xy)/uFrontMask.zw);weight*=1.-smoothstep(.60,1.,max(mask.x,mask.y));}
  return vec4(texture2D(image,vec2(.5+.5*q.x,.5-.5*q.y)).rgb,weight);
 }
 void main(){
  vec3 r=normalize(vec3(p.x*uCamera.w*uCamera.z,p.y*uCamera.z,1.));
  float cy=cos(uCamera.x),sy=sin(uCamera.x),cp=cos(uCamera.y),sp=sin(uCamera.y);
  float y=r.y*cp+r.z*sp,z=r.z*cp-r.y*sp;vec3 w=vec3(r.x*cy+z*sy,y,z*cy-r.x*sy);
  vec2 uv=vec2(fract(.5+atan(w.x,w.z)/6.28318530718),.5-asin(clamp(w.y,-1.,1.))/3.14159265359);
  vec4 f=repair(uFront,w,uEnabled.x,1.),b=repair(uRear,vec3(-w.x,w.y,-w.z),uEnabled.y,0.);
  vec4 t=repair(uUp,vec3(w.x,-w.z,w.y),uEnabled.z,0.),d=repair(uDown,vec3(w.x,w.z,-w.y),uEnabled.w,0.);
  float base=1.-max(max(f.a,b.a),max(t.a,d.a));
  vec3 color=(texture2D(uImage,uv).rgb*base+f.rgb*f.a+b.rgb*b.a+t.rgb*t.a+d.rgb*d.a)/(base+f.a+b.a+t.a+d.a);
  gl_FragColor=vec4(color,1.);
 }`));
 gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Panorama renderer unavailable');gl.useProgram(program);
 const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);const position=gl.getAttribLocation(program,'aPosition');gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);
 const names=['front','rear','up','down'],sources=[image,...names.map(id=>repairs[id])];
 const textures=sources.map((source,i)=>{const texture=gl.createTexture();gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,texture);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);if(source)gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,source);else gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([0,0,0,255]));return texture;});
 ['uImage','uFront','uRear','uUp','uDown'].forEach((name,i)=>gl.uniform1i(gl.getUniformLocation(program,name),i));
 gl.uniform4f(gl.getUniformLocation(program,'uEnabled'),...names.map(id=>repairs[id]?1:0));
 gl.uniform1f(gl.getUniformLocation(program,'uPatchTan'),Math.tan(config.repairs.fov*Math.PI/360));
 gl.uniform4f(gl.getUniformLocation(program,'uFrontMask'),...config.repairs.frontMask);
 const camera=gl.getUniformLocation(program,'uCamera');
 return {draw(s){const ratio=Math.min(devicePixelRatio||1,1.5,Math.sqrt(2000000/(s.width*s.height))),w=Math.round(s.width*ratio),h=Math.round(s.height*ratio);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}gl.viewport(0,0,w,h);gl.uniform4f(camera,s.yaw,s.pitch,Math.tan(s.fov*Math.PI/360),s.width/s.height);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);},destroy(){textures.forEach(t=>gl.deleteTexture(t));gl.deleteBuffer(buffer);shaders.forEach(s=>gl.deleteShader(s));gl.deleteProgram(program);}};
}
