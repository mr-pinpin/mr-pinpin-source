"""Blender-side geometry, cameras and one-scene cubemap renderer."""
import sys,json,math,importlib.util
from pathlib import Path
import bpy,bmesh
from mathutils import Vector,Quaternion,Matrix,Euler
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from contracts import read,write,sha,artifact,FACES
from png_atlas import assemble
req=read(sys.argv[sys.argv.index('--')+1]);root=Path(req['root']);out=Path(req['out']);out.mkdir(parents=True,exist_ok=True);loc=req['location'];action=req['action']
def collection():
 c=bpy.data.collections.new('05 Inferred panorama supplement');bpy.context.scene.collection.children.link(c);c['status']='Inferred reversible rendering additions, not canonical book architecture';return c
def mat(name,value):
 m=bpy.data.materials.new(name);m.diffuse_color=(value,value,value,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(value,value,value,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9;return m
def move_collection(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
def supplements(plan):
 a=loc.get('additions',{});c=collection();gray=mat('Inferred gray ceiling and world',.50)
 if a.get('ceiling',{}).get('enabled'):
  from plan_geometry import floor_polygon
  s=a['ceiling'];floor_polygon('Inferred continuous ceiling',plan['footprint'],s.get('z',2.65)+s.get('thickness',.12),s.get('thickness',.12),gray,c)
 e=a.get('exterior',{})
 if e.get('enabled'):
  bpy.ops.mesh.primitive_plane_add(size=e.get('size',40),location=(0,0,e.get('groundZ',-.2)));o=bpy.context.object;o.name='Inferred exterior ground';move_collection(o,c);o.data.materials.append(gray)
  for anchor in e.get('anchors',[]):
   x,y,z=anchor['position'];h=anchor.get('height',4);rad=anchor.get('radius',.35);bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=rad,depth=h,location=(x,y,z+h/2));o=bpy.context.object;o.name='Fixed exterior anchor '+anchor['id'];move_collection(o,c);o.data.materials.append(gray)
   bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=rad*3,location=(x,y,z+h));o=bpy.context.object;o.name='Fixed exterior canopy '+anchor['id'];move_collection(o,c);o.data.materials.append(gray)
 for light in a.get('interiorLights',[]):
  data=bpy.data.lights.new('Inferred fill '+light['id'],'AREA');data.energy=light.get('energy',100);data.size=light.get('size',1.5);o=bpy.data.objects.new(data.name,data);c.objects.link(o);o.location=light['position']
 return {'collection':c.name,'inference':c['status'],'configuration':a,'objects':[o.name for o in c.objects]}
def doors(states):
 records=[]
 for key,angle in states.items():
  hinge=bpy.data.objects.get('Hinge '+key)
  if hinge is None:raise ValueError('Unknown hinged door '+key)
  if 'authored_closed_yaw' not in hinge:
   default=math.radians(hinge['swing_degrees']);hinge['authored_closed_yaw']=hinge.rotation_euler.z-default;hinge['authored_swing_sign']=1 if default>=0 else -1
  closed=hinge['authored_closed_yaw'];sign=hinge['authored_swing_sign'];hinge.rotation_euler.z=closed+math.radians(angle)*sign;hinge['current_open_degrees']=angle;bpy.context.view_layer.update();records.append({'id':key,'angleDegrees':angle,'signedAngleDegrees':angle*sign,'hingeWorld':list(hinge.location),'matrixWorld':[list(v) for v in hinge.matrix_world]})
 return records
def orientation(camera):
 if 'target' in camera:return (Vector(camera['target'])-Vector(camera['position'])).to_track_quat('-Z','Y')
 if 'eulerDegrees' in camera:return Euler([math.radians(v) for v in camera['eulerDegrees']],'XYZ').to_quaternion()
 if 'quaternionWXYZ' in camera:return Quaternion(camera['quaternionWXYZ'])
 return Vector((0,1,0)).to_track_quat('-Z','Y')
def inside(point,poly):
 x,y=point;state=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:state=not state
 return state
def camera_clear(camera,plan):
 p=Vector(camera['position']);allow=camera.get('allowOutside',False)
 if not allow and not any(inside(p[:2],r['polygon']) for r in plan['rooms']):raise ValueError('Interior camera is outside named room floors; use explicit allowOutside for exterior stations')
 if not allow and not .06<p.z<loc.get('additions',{}).get('ceiling',{}).get('z',2.65)-.06:raise ValueError('Interior camera outside floor/ceiling height range')
 deps=bpy.context.evaluated_depsgraph_get();checked=0
 for o in bpy.data.objects:
  if o.type!='MESH' or not(o.name=='House structural walls' or o.name.startswith('Leaf ') or (o.parent and o.parent.name.startswith('Furniture '))):continue
  ev=o.evaluated_get(deps);m=ev.to_mesh();vs=[ev.matrix_world@v.co for v in m.vertices];tree=BVHTree.FromPolygons(vs,[list(f.vertices) for f in m.polygons]);hit=tree.find_nearest(p);ev.to_mesh_clear();checked+=1
  if hit[0] is not None and (hit[3]<.035 or hit[1].dot(p-hit[0])<-.001):raise ValueError('Camera intersects or approaches geometry: '+o.name)
 return {'pass':True,'minimumSurfaceMarginM':.035,'objectsChecked':checked,'allowOutside':allow}
def setup_camera(camera):
 data=bpy.data.cameras.new('Location job camera');o=bpy.data.objects.new(data.name,data);bpy.context.scene.collection.objects.link(o);o.location=camera['position'];o.rotation_mode='QUATERNION';o.rotation_quaternion=orientation(camera);data.type='PERSP';data.sensor_fit='HORIZONTAL';data.sensor_width=36;data.lens=camera.get('lensMm',24)
 if 'horizontalFovDegrees' in camera:data.lens=36/(2*math.tan(math.radians(camera['horizontalFovDegrees'])/2))
 data.clip_start=.025;data.clip_end=100;bpy.context.scene.camera=o;return o
def render(camera,path,width,height):
 s=bpy.context.scene;s.render.resolution_x=width;s.render.resolution_y=height;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.filepath=str(path);s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=req.get('job',{}).get('samples',24);s.cycles.seed=7;s.cycles.use_denoising=True;bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
 return {'position':list(camera.location),'quaternionWXYZ':list(camera.rotation_quaternion),'matrixWorld':[list(v) for v in camera.matrix_world],'lensMm':camera.data.lens,'horizontalFovDegrees':math.degrees(camera.data.angle_x),'width':width,'height':height}
if action=='build':
 path=root/loc['builder']['path'];sys.path.insert(0,str(path.parent));spec=importlib.util.spec_from_file_location('location_builder',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);sys.argv=['blender','--',str(root/loc['plan']['path']),'--out',str(out),'--no-render'];module.main();plan=read(root/loc['plan']['path']);extra=supplements(plan);state=doors(loc.get('doorStates',{}));bpy.ops.wm.save_as_mainfile(filepath=str(out/'base.blend'))
 bm=bmesh.new();bm.from_mesh(bpy.data.objects['House structural walls'].data);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free()
 if bad or volume<=0:raise ValueError('Build is not a closed positive structural solid')
 write(out/'worker-result.json',{'supplement':extra,'doorStates':state,'structuralCheck':{'pass':True,'nonmanifoldEdges':bad,'volumeM3':volume},'blenderVersion':bpy.app.version_string})
else:
 bpy.ops.wm.open_mainfile(filepath=req['base']);plan=read(root/loc['plan']['path']);j=req['job'];states={**loc.get('doorStates',{}),**j.get('doorStates',{})};state=doors(states);check=camera_clear(j['camera'],plan);cam=setup_camera(j['camera']);records=[]
 if action=='render':
  record=render(cam,out/'still.png',j['camera'].get('width',1400),j['camera'].get('height',1000));records.append(record);artifacts=[artifact(out/'still.png',out)]
 else:
  size=j.get('faceSize',512);reference=Vector((0,1,0)).to_track_quat('-Z','Y');delta=orientation(j['camera'])@reference.inverted();
  for index,(name,forward,right,up) in enumerate(FACES):
   f=delta@Vector(forward);r=delta@Vector(right);u=delta@Vector(up);cam.rotation_quaternion=Matrix((r,u,-f)).transposed().to_quaternion();cam.data.lens=18;record=render(cam,out/(name+'.png'),size,size);record.update({'id':name,'tile':[index%3,index//3],'forward':list(f),'right':list(r),'up':list(u)});records.append(record)
  assemble([out/(name+'.png') for name,*_ in FACES],out/'cube-atlas.png')
  artifacts=[artifact(out/(name+'.png'),out) for name,*_ in FACES]+[artifact(out/'cube-atlas.png',out)]
 write(out/'worker-result.json',{'cameraCheck':check,'doorStates':state,'cameras':records,'artifacts':artifacts,'sceneSourceSha256':sha(req['base']),'cubeLayout':'top:front/right/back;bottom:left/up/down' if action=='cubemap' else None,'singleScene':True,'blenderVersion':bpy.app.version_string})
