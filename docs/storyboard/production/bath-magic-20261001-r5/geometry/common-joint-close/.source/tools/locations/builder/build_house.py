"""Blender --background --python build_house.py -- plan.json --out output-dir.

Only a supplied semantic plan determines footprint, walls, rooms and openings.
The reference image is a packed, non-rendering editor underlay, never projected art.
"""
import argparse,sys,json,hashlib,math
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from plan_geometry import floor_polygon,wall_ribbon,point_on_path,profile_prism,opening_profile,cut_opening,signed_area,furniture_blockout,hinged_leaf


def parse():
    parser=argparse.ArgumentParser();parser.add_argument('plan');parser.add_argument('--out',required=True);parser.add_argument('--no-render',action='store_true')
    return parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])


def validate(plan):
    if plan.get('schemaVersion')!=1:raise ValueError('Unknown plan schema')
    if plan.get('units')!='meters':raise ValueError('Explicit meter units required')
    if len(plan['footprint'])<3 or abs(signed_area(plan['footprint']))<.1:raise ValueError('Nonempty footprint required')
    room_ids=[r['id'] for r in plan['rooms']];wall_ids=[w['id'] for w in plan['walls']]
    if len(set(room_ids))!=len(room_ids) or len(set(wall_ids))!=len(wall_ids):raise ValueError('Duplicate semantic IDs')
    for room in plan['rooms']:
        if len(room['polygon'])<3 or abs(signed_area(room['polygon']))<.05:raise ValueError('Invalid room polygon: '+room['id'])
    for wall in plan['walls']:
        if len(wall['path'])<2 or wall['height']<=0 or wall['thickness']<=0:raise ValueError('Invalid wall: '+wall['id'])
        if wall.get('closed') and len(wall['path'])<3:raise ValueError('Closed wall needs at least3points')
    for opening in plan.get('openings',[]):
        if opening['wall'] not in wall_ids:raise ValueError('Unknown opening wall')
        if any(r not in room_ids+['outside'] for r in opening['connects']):raise ValueError('Unknown room connection')
        if opening['width']<=0 or opening['height']<=0:raise ValueError('Nonpositive opening size')
        wall=next(w for w in plan['walls'] if w['id']==opening['wall'])
        if opening['sillZ']<wall.get('baseZ',0)-.01 or opening['sillZ']+opening['height']>wall.get('baseZ',0)+wall['height']+.01:raise ValueError('Opening extends beyond wall height')
    for item in plan.get('furniture',[]):
        if item['room'] not in room_ids or min(item['sizeXY'])<=0 or item['height']<=0:raise ValueError('Invalid furniture anchor: '+item['id'])
    # Every named room must be reachable through a real door/passage, not a window.
    reachable={'outside'}
    links=[set(o['connects']) for o in plan.get('openings',[]) if o['kind'] in {'door','passage'}]
    for _ in range(len(room_ids)+1):
        for link in links:
            if reachable & link:reachable |= link
    if not set(room_ids)<=reachable:raise ValueError('Rooms lack a door route from outside: '+str(sorted(set(room_ids)-reachable)))


def collection(name):
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);return c


def material(name,value):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(value,value,value,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(value,value,value,1);p.inputs['Roughness'].default_value=.9;return m


def main():
    args=parse();source=Path(args.plan).resolve();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True);plan=json.loads(source.read_text());validate(plan)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    structure=collection('01 Structure');rooms=collection('02 Named rooms');reference=collection('00 Plan underlay — editor only');gray=material('Neutral gray walls',.62);floorgray=material('Neutral gray floors',.44)
    floor_polygon('Footprint foundation',plan['footprint'],-.015,.16,floorgray,structure)
    for room in plan['rooms']:
        obj=floor_polygon('Room '+room['id'],room['polygon'],room.get('floorZ',0),.02,floorgray,rooms);obj['room_id']=room['id'];obj['room_label']=room['label'];obj['purpose']=room.get('purpose','')
        label=bpy.data.objects.new(room['label'],None);rooms.objects.link(label);label.location=(sum(p[0] for p in room['polygon'])/len(room['polygon']),sum(p[1] for p in room['polygon'])/len(room['polygon']),.08);label.show_name=True;label.empty_display_size=.1
    walls={}
    for wall in plan['walls']:
        obj=wall_ribbon('Wall '+wall['id'],wall['path'],wall.get('closed',False),wall['thickness'],wall.get('baseZ',0),wall['height'],gray,structure);obj['wall_id']=wall['id'];obj['kind']=wall['kind'];walls[wall['id']]=obj
    # A single watertight structural solid avoids coplanar top faces at wall joins.
    structural=next(iter(walls.values()))
    for other in list(walls.values())[1:]:
        bpy.context.view_layer.objects.active=structural;union=structural.modifiers.new('Union '+other.name,'BOOLEAN');union.operation='UNION';union.solver='MANIFOLD';union.object=other;bpy.ops.object.modifier_apply(modifier=union.name);bpy.data.objects.remove(other,do_unlink=True)
    structural.name='House structural walls';structural['semantic_wall_ids']=list(walls);walls={key:structural for key in walls}
    openings=[];leaves=[];leaf_collection=collection('04 Hinged door leaves')
    for opening in plan.get('openings',[]):
        spec=next(w for w in plan['walls'] if w['id']==opening['wall']);center,tangent=point_on_path(spec['path'],spec.get('closed',False),opening['station']);profile=opening_profile(opening['shape'],opening['width'],opening['height'],opening['sillZ']);cutter=profile_prism(opening['id'],center,tangent,profile,spec['thickness']+1,None,structure);cut_opening(walls[opening['wall']],cutter)
        openings.append({**opening,'worldCenterXY':list(center),'worldTangentXY':list(tangent),'worldNormalXY':[-tangent.y,tangent.x]})
        if opening.get('leaf'):leaves.append(hinged_leaf(opening,center,tangent,{r['id']:r['polygon'] for r in plan['rooms']},gray,leaf_collection))
    for wall in set(walls.values()):
        bevel=wall.modifiers.new('Small architectural edge bevel','BEVEL');bevel.width=.012;bevel.segments=2
    furnishings=collection('03 Measured furniture');furniture_records=[]
    for item in plan.get('furniture',[]):
        room=next(r for r in plan['rooms'] if r['id']==item['room']);base=item.get('baseZ',room.get('floorZ',0));anchor=furniture_blockout(item,base,gray,furnishings);bpy.context.view_layer.update();furniture_records.append({**item,'baseZ':base,'matrixWorldRows':[list(r) for r in anchor.matrix_world]})
    underlay=plan.get('underlay');underlay_record=None
    if underlay:
        path=(source.parent/underlay['image']).resolve();image=bpy.data.images.load(str(path));image.pack();obj=bpy.data.objects.new('Calibrated plan image — not a render surface',None);reference.objects.link(obj);obj.empty_display_type='IMAGE';obj.data=image;obj.location=(*underlay['centerXY'],-.22);obj.empty_display_size=max(underlay['widthMeters'],underlay['heightMeters']);obj.rotation_euler.z=math.radians(underlay.get('rotationDegrees',0));obj.empty_image_depth='BACK';obj.hide_render=True
        if abs(underlay['widthMeters']/underlay['heightMeters']-image.size[0]/image.size[1])>.01:raise ValueError('Underlay world aspect must match image aspect')
        underlay_record={**underlay,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pixelDimensions':list(image.size),'note':'Packed editor underlay only; not assigned to architecture materials'}
    xs=[p[0] for p in plan['footprint']];ys=[p[1] for p in plan['footprint']];cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2;span=max(max(xs)-min(xs),max(ys)-min(ys));height=max(w['height'] for w in plan['walls'])
    world=bpy.data.worlds.new('Gray review environment');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[1].default_value=.6
    light=bpy.data.lights.new('Broad review light','AREA');light.energy=1800;light.size=span;obj=bpy.data.objects.new('Broad review light',light);scene.collection.objects.link(obj);obj.location=(cx,cy,height+span*.7)
    fill=bpy.data.lights.new('Soft front inspection fill','AREA');fill.energy=500;fill.size=span*.7;fill_obj=bpy.data.objects.new('Soft front inspection fill',fill);scene.collection.objects.link(fill_obj);fill_obj.location=(cx,cy-span*1.2,height*.8);fill_obj.rotation_euler=(Vector((cx,cy,height*.45))-fill_obj.location).to_track_quat('-Z','Y').to_euler()
    camera=bpy.data.cameras.new('Measured review camera');obj=bpy.data.objects.new('Measured review camera',camera);scene.collection.objects.link(obj);scene.camera=obj;camera.clip_end=500
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    views=plan.get('cameras',[{'id':'topdown','position':[cx,cy,height+span*1.5],'target':[cx,cy,0],'projection':'ORTHO','orthoScale':span*1.15},{'id':'overview','position':[cx+span*.8,cy-span*.9,height+span*.8],'target':[cx,cy,height*.3],'projection':'PERSP','lensMm':35}])
    manifest={'plan':str(source),'planSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'units':'meters','layoutSource':'Supplied semantic plan; no reused previous house footprint','underlay':underlay_record,'rooms':plan['rooms'],'walls':plan['walls'],'openings':openings,'furniture':furniture_records,'doorLeaves':leaves,'renders':[],'geometryOnly':True}
    for view in views:
        obj.location=view['position'];obj.rotation_euler=(Vector(view['target'])-obj.location).to_track_quat('-Z','Y').to_euler();camera.type=view['projection'];camera.ortho_scale=view.get('orthoScale',span*1.15);camera.lens=view.get('lensMm',35);scene.render.resolution_x=view.get('width',1400);scene.render.resolution_y=view.get('height',1100);scene.render.filepath=str(out/(view['id']+'.png'))
        if not args.no_render:bpy.ops.render.render(write_still=True)
        manifest['renders'].append({**view,'rotationEulerXYZ':list(obj.rotation_euler),'matrixWorldRows':[list(r) for r in obj.matrix_world]})
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'house-plan-gray.blend'));(out/'geometry-manifest.json').write_text(json.dumps(manifest,indent=2));(out/'plan-used.json').write_text(json.dumps(plan,indent=2));print('PLAN_GEOMETRY_COMPLETE')

if __name__=='__main__':main()
