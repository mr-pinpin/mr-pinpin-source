"""Small geometry primitives for a measured floor plan; no assumed house layout."""
import math
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon


def signed_area(points):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))/2


def mesh_object(name,vertices,faces,material,collection):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj)
    if material:mesh.materials.append(material)
    return obj


def floor_polygon(name,points,z,thickness,material,collection):
    points=list(points)
    if signed_area(points)<0:points.reverse()
    n=len(points);vertices=[(x,y,h) for h in [z-thickness,z] for x,y in points]
    flat=[Vector((x,y,0)) for x,y in points];lookup={(p.x,p.y):i for i,p in enumerate(flat)}
    triangles=[[v if isinstance(v,int) else lookup[(v.x,v.y)] for v in tri] for tri in tessellate_polygon([flat])]
    faces=[tuple(reversed(t)) for t in triangles]+[tuple(i+n for i in t) for t in triangles]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh_object(name,vertices,faces,material,collection)


def wall_ribbon(name,path,closed,thickness,base,height,material,collection):
    """Continuous mitered centerline ribbon, including concave/organic polylines."""
    points=[Vector(p) for p in path];n=len(points);offsets=[]
    for i,p in enumerate(points):
        before=(p-points[(i-1)%n]).normalized() if closed or i else (points[1]-p).normalized()
        after=(points[(i+1)%n]-p).normalized() if closed or i<n-1 else before
        normal_before=Vector((-before.y,before.x));normal_after=Vector((-after.y,after.x))
        bisector=normal_before+normal_after
        if bisector.length<1e-6:raise ValueError('Wall reverses direction: '+name)
        bisector.normalize();denominator=bisector.dot(normal_after)
        distance=thickness/2/denominator
        if abs(distance)>thickness*3:raise ValueError('Wall corner too sharp: '+name)
        offsets.append(bisector*distance)
    vertices=[]
    for p,o in zip(points,offsets):
        vertices.extend([(p.x-o.x,p.y-o.y,base),(p.x+o.x,p.y+o.y,base),(p.x-o.x,p.y-o.y,base+height),(p.x+o.x,p.y+o.y,base+height)])
    faces=[]
    for i in range(n if closed else n-1):
        a=i*4;b=((i+1)%n)*4
        faces.extend([(a,b,b+2,a+2),(a+1,a+3,b+3,b+1),(a,a+1,b+1,b),(a+2,b+2,b+3,a+3)])
    if not closed:faces.extend([(0,2,3,1),((n-1)*4,(n-1)*4+1,(n-1)*4+3,(n-1)*4+2)])
    return mesh_object(name,vertices,faces,material,collection)


def point_on_path(path,closed,distance):
    pairs=list(zip(path,path[1:]+([path[0]] if closed else [])))
    for a,b in pairs:
        a,b=Vector(a),Vector(b);length=(b-a).length
        if distance<=length+1e-7:return a+(b-a)*max(0,min(1,distance/length)),(b-a).normalized()
        distance-=length
    raise ValueError('Opening station extends beyond wall path')


def profile_prism(name,center,tangent,profile,depth,material,collection):
    normal=Vector((-tangent.y,tangent.x));n=len(profile);vertices=[]
    for side in [-depth/2,depth/2]:
        for x,z in profile:
            p=center+tangent*x+normal*side;vertices.append((p.x,p.y,z))
    # Profiles are simple, convex rectangular/arched/round openings.
    # The profile lies in tangent/Z; its positive winding points -normal.
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces += [(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    return mesh_object(name,vertices,faces,material,collection)


def opening_profile(kind,width,height,sill):
    if kind=='round':
        return [(width/2*math.cos(i*math.tau/64),sill+height/2+height/2*math.sin(i*math.tau/64)) for i in range(64)]
    if kind=='arch':
        spring=sill+height-width/2
        if spring<sill:raise ValueError('Arch height must be at least half its width')
        return [(-width/2,sill),(width/2,sill)]+[(width/2*math.cos(i*math.pi/32),spring+width/2*math.sin(i*math.pi/32)) for i in range(33)]
    return [(-width/2,sill),(width/2,sill),(width/2,sill+height),(-width/2,sill+height)]


def cut_opening(wall,cutter):
    bpy.context.view_layer.objects.active=wall
    modifier=wall.modifiers.new('Measured opening '+cutter.name,'BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter,do_unlink=True)


def furniture_blockout(spec,base_z,material,collection):
    """Gray semantic proxies contained within the measured footprint/height."""
    root=bpy.data.objects.new('Furniture '+spec['id'],None);collection.objects.link(root)
    root.location=(*spec['centerXY'],base_z);root.rotation_euler.z=math.radians(spec.get('rotationDegrees',0))
    root['kind']=spec['kind'];root['room_id']=spec['room'];root['source_note']=spec.get('sourceNote','')
    w,d=spec['sizeXY'];h=spec['height'];kind=spec['kind'].lower()
    def part(label,loc,scale):
        x,y,z=loc;a,b,c=[v/2 for v in scale]
        if spec.get('shape')=='ellipse' and label in {'top','basin','temporary basin cutter','measured proxy'}:
            count=64;vertices=[(x+a*math.cos(i*math.tau/count),y+b*math.sin(i*math.tau/count),z+side*c) for side in [-1,1] for i in range(count)];faces=[tuple(range(count-1,-1,-1)),tuple(range(count,count*2))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
        else:
            vertices=[(x+sx*a,y+sy*b,z+sz*c) for sz in [-1,1] for sy in [-1,1] for sx in [-1,1]];faces=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
        obj=mesh_object(spec['id']+' '+label,vertices,faces,material,collection);obj.parent=root
        bevel=obj.modifiers.new('Proxy rounded edges','BEVEL');bevel.width=min(.025,min(scale)*.12);bevel.segments=2
        return obj
    if kind in {'table','dining_table','desk','stool'}:
        t=min(.09,h*.12);part('top',(0,0,h-t/2),(w,d,t));leg=min(w,d)*.08;lx=w*.30 if spec.get('shape')=='ellipse' else w/2-leg/2;ly=d*.30 if spec.get('shape')=='ellipse' else d/2-leg/2
        for x in [-lx,lx]:
            for y in [-ly,ly]:part('leg',(x,y,(h-t)/2),(leg,leg,h-t))
    elif kind in {'bed','double_bed','single_bed'}:
        part('base',(0,0,h*.2),(w,d,h*.4));part('mattress',(0,0,h*.5),(w*.96,d*.96,h*.2));part('headboard',(0,d*.46,h*.5),(w,d*.08,h))
    elif kind in {'bookcase','shelf','bookshelf'}:
        t=min(w,d)*.09
        part('back',(0,d/2-t/2,h/2),(w,t,h))
        for x in [-w/2+t/2,w/2-t/2]:part('side',(x,0,h/2),(t,d,h))
        for i in range(5):part('shelf',(0,0,t/2+(h-t)*i/4),(w,d,t))
    elif kind in {'chair','bench','sofa'}:
        part('seat',(0,0,h*.45),(w,d,h*.12));part('back',(0,d*.44,h*.7),(w,d*.12,h*.6));leg=min(w,d)*.09
        for x in [-w/2+leg/2,w/2-leg/2]:
            for y in [-d/2+leg/2,d/2-leg/2]:part('leg',(x,y,h*.2),(leg,leg,h*.4))
    elif kind in {'bathtub','bath','tub','sink','washstand'}:
        outer=part('basin',(0,0,h/2),(w,d,h));cavity=part('temporary basin cutter',(0,0,h*.72),(w*.78,d*.75,h*.9))
        bpy.context.view_layer.update();cut_opening(outer,cavity)
    else:
        part('measured proxy',(0,0,h/2),(w,d,h))
    return root


def hinged_leaf(opening,center,tangent,room_polygons,material,collection):
    spec=opening['leaf'];width=opening['width'];direction=1 if spec['hingeAt']=='start' else -1
    hinge=center-tangent*(width/2)*direction
    def centroid(points):return Vector((sum(p[0] for p in points)/len(points),sum(p[1] for p in points)/len(points)))
    if spec['toward']=='outside':
        inside=next(r for r in opening['connects'] if r!='outside');target=center+(center-centroid(room_polygons[inside])).normalized()*3
    else:target=centroid(room_polygons[spec['toward']])
    angle=math.radians(spec['angleDegrees']);closed=math.atan2(tangent.y,tangent.x)
    def midpoint(a):
        v=Vector((math.cos(closed+a),math.sin(closed+a)))*direction*width/2
        return hinge+v
    signed=min([angle,-angle],key=lambda a:(midpoint(a)-target).length)
    pivot=bpy.data.objects.new('Hinge '+opening['id'],None);collection.objects.link(pivot);pivot.location=(*hinge,0);pivot.rotation_euler.z=closed+signed
    profile=opening_profile(opening['shape'],width-.024,opening['height']-.02,opening['sillZ']+.01)
    leaf=profile_prism('Leaf '+opening['id'],Vector((direction*width/2,0)),Vector((1,0)),profile,spec.get('thickness',.035),material,collection);leaf.parent=pivot
    bevel=leaf.modifiers.new('Soft leaf edge','BEVEL');bevel.width=.008;bevel.segments=2
    pivot['opening_id']=opening['id'];pivot['swing_target']=spec['toward'];pivot['swing_degrees']=math.degrees(signed)
    return {'opening':opening['id'],'hingeXY':list(hinge),'closedYawDegrees':math.degrees(closed),'signedSwingDegrees':math.degrees(signed),'toward':spec['toward'],'leafThickness':spec.get('thickness',.035),'width':width}
