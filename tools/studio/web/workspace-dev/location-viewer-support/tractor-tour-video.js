// The source-lock trial displays orbit and panorama through the same WebGL RGB path.
// No tone curve, filter or change to the underlying video is applied.
export function orbitVideoRenderer(canvas){
 const gl=canvas.getContext('webgl',{alpha:false,antialias:false,preserveDrawingBuffer:true});if(!gl)throw Error('WebGL unavailable');
 const program=gl.createProgram(),shaders=[];
 for(const[type,code]of[[gl.VERTEX_SHADER,'attribute vec2 p;varying vec2 uv;void main(){uv=vec2(.5+.5*p.x,.5-.5*p.y);gl_Position=vec4(p,0.,1.);}'],[gl.FRAGMENT_SHADER,'precision highp float;varying vec2 uv;uniform sampler2D frame;void main(){gl_FragColor=vec4(texture2D(frame,uv).rgb,1.);}']]){const s=gl.createShader(type);gl.shaderSource(s,code);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));gl.attachShader(program,s);shaders.push(s);}
 gl.linkProgram(program);gl.useProgram(program);const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);const p=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);const texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);for(const n of[gl.TEXTURE_MIN_FILTER,gl.TEXTURE_MAG_FILTER])gl.texParameteri(gl.TEXTURE_2D,n,gl.LINEAR);for(const n of[gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T])gl.texParameteri(gl.TEXTURE_2D,n,gl.CLAMP_TO_EDGE);
 let lastFrame=null,textureWidth=0,textureHeight=0,uploads=0,draws=0;
 return{get stats(){return{uploads,draws};},draw(video,width,height,frame=video.currentTime){
  if(video.readyState<2)return;
  const ratio=Math.min(devicePixelRatio||1,1.5),w=Math.round(width*ratio),h=Math.round(height*ratio),resized=canvas.width!==w||canvas.height!==h;
  if(resized){canvas.width=w;canvas.height=h;}
  if(frame===lastFrame&&!resized)return;
  gl.viewport(0,0,w,h);
  if(frame!==lastFrame){
   if(textureWidth===video.videoWidth&&textureHeight===video.videoHeight)gl.texSubImage2D(gl.TEXTURE_2D,0,0,0,gl.RGBA,gl.UNSIGNED_BYTE,video);
   else{gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,video);textureWidth=video.videoWidth;textureHeight=video.videoHeight;}
   lastFrame=frame;uploads++;
  }
  gl.drawArrays(gl.TRIANGLE_STRIP,0,4);draws++;
 },destroy(){gl.deleteTexture(texture);gl.deleteBuffer(buffer);gl.deleteProgram(program);shaders.forEach(s=>gl.deleteShader(s));}};
}
