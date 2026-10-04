export const RAD=Math.PI/180,TAU=Math.PI*2;
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export const wrap=x=>((x+Math.PI)%TAU+TAU)%TAU-Math.PI;
export function direction([u,v]){const lon=(u-.5)*TAU,lat=(.5-v)*Math.PI,c=Math.cos(lat);return[Math.sin(lon)*c,Math.sin(lat),Math.cos(lon)*c];}
export function cameraRay(p,s){const t=Math.tan(s.fov*RAD/2),x=(p.x/s.width*2-1)*t*s.width/s.height,y=(1-p.y/s.height*2)*t,n=Math.hypot(x,y,1);return[x/n,y/n,1/n];}
export function worldRay(p,s){const [x,y,z]=cameraRay(p,s),cy=Math.cos(s.yaw),sy=Math.sin(s.yaw),cp=Math.cos(s.pitch),sp=Math.sin(s.pitch),py=y*cp+z*sp,pz=z*cp-y*sp;return[x*cy+pz*sy,py,pz*cy-x*sy];}
export function anchored(target,point,s){const [x,y,z]=cameraRay(point,s);s.pitch=Math.asin(clamp(target[1]/Math.hypot(y,z),-1,1))-Math.atan2(y,z);const rz=z*Math.cos(s.pitch)-y*Math.sin(s.pitch);s.yaw=Math.atan2(target[0],target[2])-Math.atan2(x,rz);}
export function cameraPoint(uv,s){const [x,y,z]=direction(uv),cy=Math.cos(s.yaw),sy=Math.sin(s.yaw),cp=Math.cos(s.pitch),sp=Math.sin(s.pitch),px=x*cy-z*sy,pz=x*sy+z*cy;return[px,y*cp-pz*sp,y*sp+pz*cp];}
export function project(uv,s){const [x,y,z]=cameraPoint(uv,s),t=Math.tan(s.fov*RAD/2);return{x:s.width/2+x/z/t*s.height/2,y:s.height/2-y/z/t*s.height/2,visible:z>0&&Math.abs(x/z/t)<s.width/s.height&&Math.abs(y/z/t)<1};}
export function polygonPath(uvs,s){
 const points=[];
 for(let i=0;i<uvs.length;i++){const a=uvs[i],b=uvs[(i+1)%uvs.length],du=((b[0]-a[0]+1.5)%1)-.5,dv=b[1]-a[1],n=Math.max(1,Math.ceil(Math.hypot(du,dv)/.004));for(let j=0;j<n;j++)points.push(cameraPoint([a[0]+du*j/n,a[1]+dv*j/n],s));}
 const clipped=[];for(let i=0;i<points.length;i++){const a=points[i],b=points[(i+1)%points.length],inside=a[2]>.025,next=b[2]>.025;if(inside)clipped.push(a);if(inside!==next){const f=(.025-a[2])/(b[2]-a[2]);clipped.push(a.map((v,k)=>v+(b[k]-v)*f));}}
 const t=Math.tan(s.fov*RAD/2);return clipped.length?clipped.map(([x,y,z],i)=>`${i?'L':'M'}${(s.width/2+x/z/t*s.height/2).toFixed(2)} ${(s.height/2-y/z/t*s.height/2).toFixed(2)}`).join(' ')+' Z':'';
}
