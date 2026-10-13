"""Authored rotunda blocking; invoked by the reusable location renderer."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy, bmesh
from mathutils import Vector

def material(name, colour, roughness=.8, emission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*colour,1)
    bs.inputs['Roughness'].default_value=roughness
    if emission:
        bs.inputs['Emission Color'].default_value=(*colour,1);bs.inputs['Emission Strength'].default_value=emission
    return m

def revolve(name, profile, mat, count=96):
    verts=[(r*math.cos(2*math.pi*j/count),r*math.sin(2*math.pi*j/count),z) for r,z in profile for j in range(count)]
    faces=[]
    for k in range(len(profile)):
        nxt=(k+1)%len(profile)
        for j in range(count):faces.append((k*count+j,k*count+(j+1)%count,nxt*count+(j+1)%count,nxt*count+j))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o);o.data.materials.append(mat)
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume()<0:bmesh.ops.flip_faces(bm,faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free();return o

def cut(subject,cutter):
    bpy.context.view_layer.objects.active=subject
    mod=subject.modifiers.new('Authored natural opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)

def cube(name,position,size,mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=position);o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(mat)
    return o

def main():
    p=argparse.ArgumentParser();p.add_argument('plan');p.add_argument('--out',required=True);p.add_argument('--no-render',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    source=Path(a.plan);plan=json.loads(source.read_text());out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    rock=material('Authored warm stone blocking',(.39,.34,.25));bank=material('Dry shore blocking',(.46,.39,.25));water=material('Lake surface blocking',(.09,.33,.40),.18);moss=material('Cultivated plant zone blocking',(.16,.35,.19));amber=material('Fixed luminous vine anchors',(.95,.55,.12),.5,3)
    r=plan['rotunda']['innerRadius'];th=plan['rotunda']['shellThickness'];base=plan['rotunda']['springHeight'];hole=plan['rotunda']['oculusRadius'];rings=32
    imin=math.asin(hole/r);omin=math.asin(hole/(r+th))
    profile=[(r,-.2),(r,base)]
    for i in range(1,rings+1):
        t=math.pi/2-(math.pi/2-imin)*i/rings;profile.append((r*math.sin(t),base+r*math.cos(t)))
    for i in range(rings,-1,-1):
        t=math.pi/2-(math.pi/2-omin)*i/rings;profile.append(((r+th)*math.sin(t),base+(r+th)*math.cos(t)))
    profile.append((r+th,-.2));shell=revolve('Cave structural shell',profile,rock)
    for opening in plan['openings']:
        ang=math.radians(opening['angleDegrees']);cx=r*math.cos(ang);cy=r*math.sin(ang)
        lower=cube('Portal lower cut', [cx,cy,.9],[opening['width'],2.2,2.2]);lower.rotation_euler.z=ang-math.pi/2;cut(shell,lower)
        bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=opening['width']/2,depth=2.2,location=(cx,cy,1.65));arch=bpy.context.object;arch.rotation_euler=(Vector((math.cos(ang),math.sin(ang),0))).to_track_quat('Z','Y').to_euler();cut(shell,arch)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=r,depth=.25,location=(0,0,-.125));floor=bpy.context.object;floor.name='Dry annular shore';floor.data.materials.append(bank)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1,depth=4,location=(0,0,-1));basin=bpy.context.object;basin.scale=(plan['lake']['radii'][0],plan['lake']['radii'][1],1);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);cut(floor,basin)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1,depth=.12,location=(0,0,plan['lake']['waterLevel']-.06));lake=bpy.context.object;lake.name='Single underground lake';lake.scale=(*plan['lake']['radii'],1);lake.data.materials.append(water)
    screen=plan['screen'];o=cube('Reveal occluding stone',screen['position'],screen['size'],rock);o.rotation_euler.z=math.radians(screen['rotationDegrees'])
    for zone in plan['plantZones']:
        o=cube('Cultivated bank '+zone['id'],zone['position'],zone['size'],moss)
    for light in plan['vineLights']:
        for n in range(7):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.12,location=(light['position'][0],light['position'][1],light['position'][2]-n*.28));bpy.context.object.name='Vine '+light['id']+' berry '+str(n);bpy.context.object.data.materials.append(amber)
        d=bpy.data.lights.new('Fixed vine light '+light['id'],'POINT');d.energy=100;d.color=(1,.66,.28);o=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(o);o.location=light['position']
    world=bpy.data.worlds.new('Soft sky through oculus');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.6,.75,.95,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6
    d=bpy.data.lights.new('Oculus daylight','AREA');d.energy=1800;d.size=hole*2;o=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(o);o.location=(0,0,base+r+3)
    cube('Outside threshold floor',[-11,-8,-.18],[7,7,.2],bank)
    # Geometry-only visibility probes test actual meshes, not a drawn frustum.
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();probes=[]
    for item in plan['visibilityProbes']:
        start=Vector(item['origin']);end=Vector(item['target']);delta=end-start
        hit=bpy.context.scene.ray_cast(deps,start,delta.normalized(),distance=delta.length-.01)
        visible=not hit[0];assert visible==item['expectedVisible'],(item['id'],hit[4].name if hit[0] else 'clear')
        probes.append(dict(id=item['id'],visible=visible,hit=hit[4].name if hit[0] else None))
    record=dict(schemaVersion=1,status='authored-metric-blocking-not-original-book-measurements',planSha256=hashlib.sha256(source.read_bytes()).hexdigest(),units='meters',rotunda=plan['rotunda'],visibilityProbes=probes,objects=[o.name for o in bpy.data.objects],geometryOnly=True)
    (out/'geometry-manifest.json').write_text(json.dumps(record,indent=2)+'\n');(out/'plan-used.json').write_bytes(source.read_bytes())
    print('AUTHORED_ROTUNDA_COMPLETE')

if __name__=='__main__':main()
