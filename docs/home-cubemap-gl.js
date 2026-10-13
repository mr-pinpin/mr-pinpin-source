// Blender-guided overlapping directional faces; every view ray has full coverage.
export function cubemapRenderer(canvas,images,config){
 if(config.exactCube===true&&config.faceFov!==90)throw Error('Exact cube requires90degree faces');
 const gl=canvas.getContext('webgl',{alpha:false,antialias:false,powerPreference:'low-power'});if(!gl)throw Error('WebGL unavailable');
 const shaders=[];function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('Cubemap shader unavailable');shaders.push(s);return s;}
 const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,'attribute vec2 aPosition;varying vec2 p;void main(){p=aPosition;gl_Position=vec4(aPosition,0.,1.);}'));
 gl.attachShader(program,shader(gl.FRAGMENT_SHADER,`precision highp float;varying vec2 p;uniform vec4 uCamera;uniform float uFaceTan;uniform bool uExactCube;uniform sampler2D uFront,uBack,uRight,uLeft,uUp,uDown;
 // Stable directional ownership avoids averaging independently painted objects.
 // Side walls own their overscan, then roof/floor own theirs. Only the narrow
 // support boundary feathers; at least one face is fully covered for every ray.
 vec4 face(sampler2D image,vec3 local){if(local.z<=0.)return vec4(0.);vec2 q=local.xy/(local.z*uFaceTan);float edge=max(abs(q.x),abs(q.y));if(uExactCube){if(edge>1.000001)return vec4(0.);return vec4(texture2D(image,clamp(vec2(.5+.5*q.x,.5-.5*q.y),0.,1.)).rgb,1.);}if(edge>=.99)return vec4(0.);float weight=1.-smoothstep(.95,.99,edge);return vec4(texture2D(image,vec2(.5+.5*q.x,.5-.5*q.y)).rgb*weight,weight);}
 vec4 over(vec4 below,vec4 above){return above+below*(1.-above.a);}
 void main(){vec3 r=normalize(vec3(p.x*uCamera.w*uCamera.z,p.y*uCamera.z,1.));float cy=cos(uCamera.x),sy=sin(uCamera.x),cp=cos(uCamera.y),sp=sin(uCamera.y);float y=r.y*cp+r.z*sp,z=r.z*cp-r.y*sp;vec3 w=vec3(r.x*cy+z*sy,y,z*cy-r.x*sy);
 vec4 walls=face(uFront,w)+face(uBack,vec3(-w.x,w.y,-w.z));vec4 sides=face(uRight,vec3(-w.z,w.y,w.x))+face(uLeft,vec3(w.z,w.y,-w.x));vec4 poles=face(uUp,vec3(w.x,-w.z,w.y))+face(uDown,vec3(w.x,w.z,-w.y));vec4 color=over(over(walls,sides),poles);gl_FragColor=vec4(color.rgb/max(color.a,.0001),1.);}`));
 gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Cubemap renderer unavailable');gl.useProgram(program);
 const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);const position=gl.getAttribLocation(program,'aPosition');gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);
 const ids=['front','back','right','left','up','down'],uniforms=['uFront','uBack','uRight','uLeft','uUp','uDown'];
 const textures=ids.map((id,i)=>{const texture=gl.createTexture();gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,texture);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,images[id]);gl.uniform1i(gl.getUniformLocation(program,uniforms[i]),i);return texture;});
 gl.uniform1f(gl.getUniformLocation(program,'uFaceTan'),Math.tan(config.faceFov*Math.PI/360));gl.uniform1i(gl.getUniformLocation(program,'uExactCube'),config.exactCube===true?1:0);const camera=gl.getUniformLocation(program,'uCamera');
 return{draw(s){const ratio=Math.min(devicePixelRatio||1,1.5,Math.sqrt(2000000/(s.width*s.height))),w=Math.round(s.width*ratio),h=Math.round(s.height*ratio);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}gl.viewport(0,0,w,h);gl.uniform4f(camera,s.yaw,s.pitch,Math.tan(s.fov*Math.PI/360),s.width/s.height);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);},destroy(){textures.forEach(t=>gl.deleteTexture(t));gl.deleteBuffer(buffer);shaders.forEach(s=>gl.deleteShader(s));gl.deleteProgram(program);}};
}
