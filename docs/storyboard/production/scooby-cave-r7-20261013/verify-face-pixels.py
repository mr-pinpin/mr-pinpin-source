"""Independent screenshot/source comparison detects swapped/mirrored cube directions."""
import json, math, sys
from pathlib import Path
from PIL import Image

out,source=map(Path,sys.argv[1:])
records=json.loads((out/'view-records.json').read_text());evidence=[]
bases={'front':((0,1,0),(1,0,0),(0,0,1)), 'right':((1,0,0),(0,-1,0),(0,0,1)), 'back':((0,-1,0),(-1,0,0),(0,0,1)), 'left':((-1,0,0),(0,1,0),(0,0,1)), 'up':((0,0,1),(1,0,0),(0,-1,0)), 'down':((0,0,-1),(1,0,0),(0,1,0))}
faces={name:Image.open(source/(name+'.png')).convert('RGB') for name in bases}
def dot(a,b):return sum(x*y for x,y in zip(a,b))
assert len([r for r in records if r['id'].startswith('edge-')])==12
for r in records:
    shot=Image.open(out/(r['id']+'.png')).convert('RGB')
    tan=math.tan(math.radians(r['fov'])/2);errors=[]
    for nx,ny in [(-.45,-.4),(-.45,.4),(.45,-.4),(.45,.4),(0,0),(0,-.4),(0,.4)]:
        sx=round((nx+1)*shot.width/2);sy=round((1-ny)*shot.height/2)
        x,y,z=nx*tan*r['width']/r['height'],ny*tan,1
        cosine_yaw,sine_yaw=math.cos(r['yaw']),math.sin(r['yaw']);cp,sp=math.cos(r['pitch']),math.sin(r['pitch'])
        up=y*cp+z*sp;forward=z*cp-y*sp;world=(x*cosine_yaw+forward*sine_yaw,forward*cosine_yaw-x*sine_yaw,up)
        name=max(bases,key=lambda name:dot(world,bases[name][0]));f,right,vertical=bases[name];distance=dot(world,f);face=faces[name]
        u=.5+.5*dot(world,right)/distance;v=.5-.5*dot(world,vertical)/distance
        fx=round(u*(face.width-1));fy=round(v*(face.height-1))
        a=shot.getpixel((sx,sy));b=face.getpixel((fx,fy));errors.append(max(abs(x-y) for x,y in zip(a,b)))
    assert max(errors)<=24,(r['id'],errors)
    evidence.append(dict(face=r['id'],sampleCount=len(errors),maxRgbError=max(errors)))
(out/'face-pixel-proof.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('PASS actual renderer/source direction matching:',evidence)
