import sys,tempfile,unittest,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from contracts import camera,door_states,validate_manifest,write,artifact,FACES
from png_atlas import encode,decode,assemble
class WorkflowTests(unittest.TestCase):
 def test_invalid_cameras_fail(self):
  for c in [{'position':[0,0,float('nan')],'target':[0,1,0]},{'position':[0,0,1],'target':[0,0,1]},{'position':[0,0,1],'quaternionWXYZ':[0,0,0,0]},{'position':[0,0,1],'target':[0,1,1],'eulerDegrees':[0,0,0]},{'position':[0,0,1],'target':[0,1,1],'horizontalFovDegrees':180}]:
   with self.assertRaises(ValueError):camera(c)
  camera({'position':[0,0,1],'quaternionWXYZ':[1,0,0,0],'horizontalFovDegrees':90})
 def test_bad_door_angles_fail(self):
  for value in [-1,121,float('inf'),True]:
   with self.assertRaises(ValueError):door_states({'door-bath':value})
 def test_empty_escape_and_tamper_fail(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder);write(p/'manifest.json',{})
   with self.assertRaises(ValueError):validate_manifest(p/'manifest.json')
   (p/'still.png').write_bytes(b'known');m={'schemaVersion':1,'stage':'render','locationId':'test','inputs':{'plan.json':'a'*64},'artifacts':[artifact(p/'still.png',p)]};write(p/'manifest.json',m);self.assertTrue(validate_manifest(p/'manifest.json')['pass']);(p/'still.png').write_bytes(b'changed')
   with self.assertRaises(ValueError):validate_manifest(p/'manifest.json')
   m['artifacts'][0]['path']='../still.png';write(p/'manifest.json',m)
   with self.assertRaises(ValueError):validate_manifest(p/'manifest.json')
 def test_atlas_tiles_keep_pixels_and_order(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder);files=[]
   for i in range(6):
    file=p/(str(i)+'.png');encode(file,3,3,3,[bytes([i*30,y*50,200])*3 for y in range(3)]);files.append(file)
   self.assertTrue(assemble(files,p/'atlas.png')['decodedPixelExact']);w,h,c,rows=decode(p/'atlas.png');self.assertEqual((w,h,c),(9,6,3));self.assertEqual(rows[0][9:12],bytes([30,0,200]));self.assertEqual(rows[3][:3],bytes([90,0,200]))
 def test_all_twelve_cube_edges_pair(self):
  edges={}
  def ray(f,r,u,x,y):
   v=[f[i]+r[i]*x+u[i]*y for i in range(3)];length=math.sqrt(sum(a*a for a in v));return tuple(round(a/length,8) for a in v)
  for name,f,r,u in FACES:
   for a,b in [((-1,-1),(-1,1)),((1,-1),(1,1)),((-1,-1),(1,-1)),((-1,1),(1,1))]:
    key=tuple(sorted([ray(f,r,u,*a),ray(f,r,u,*b)]));edges.setdefault(key,[]).append(name)
  self.assertEqual(len(edges),12);self.assertTrue(all(len(v)==2 for v in edges.values()))
if __name__=='__main__':unittest.main()
