"""Dependency-free location/camera contracts and checksums."""
import hashlib,json,math
from pathlib import Path
FACES=[('front',(0,1,0),(1,0,0),(0,0,1)),('right',(1,0,0),(0,-1,0),(0,0,1)),('back',(0,-1,0),(-1,0,0),(0,0,1)),('left',(-1,0,0),(0,1,0),(0,0,1)),('up',(0,0,1),(1,0,0),(0,-1,0)),('down',(0,0,-1),(1,0,0),(0,1,0))]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def resolve(root,path):
 p=Path(path)
 if p.is_absolute() or '..' in p.parts:raise ValueError('Expected a repository-relative path: '+str(path))
 result=(Path(root)/p).resolve()
 if not result.is_relative_to(Path(root).resolve()):raise ValueError('Path escapes repository')
 return result
def vector(value,n,label):
 if not isinstance(value,list) or len(value)!=n or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in value):raise ValueError(label+' must contain '+str(n)+' finite numbers')
 return value
def camera(value,cube=False):
 vector(value.get('position'),3,'camera.position');choices=[k for k in ['target','eulerDegrees','quaternionWXYZ'] if k in value]
 if len(choices)>1 or (not cube and len(choices)!=1):raise ValueError('Specify exactly one target, eulerDegrees or quaternionWXYZ for a still')
 if 'target' in value:
  vector(value['target'],3,'camera.target')
  if sum((a-b)**2 for a,b in zip(value['position'],value['target']))<1e-12:raise ValueError('Camera target equals position')
 if 'eulerDegrees' in value:vector(value['eulerDegrees'],3,'camera.eulerDegrees')
 if 'quaternionWXYZ' in value:
  q=vector(value['quaternionWXYZ'],4,'camera.quaternionWXYZ')
  if abs(sum(v*v for v in q)-1)>1e-4:raise ValueError('Camera quaternion must have unit length')
 if 'lensMm' in value and 'horizontalFovDegrees' in value:raise ValueError('Specify lens or FOV, not both')
 for k,low,high in [('lensMm',5,300),('horizontalFovDegrees',5,140)]:
  if k in value and (not isinstance(value[k],(int,float)) or not math.isfinite(value[k]) or not low<=value[k]<=high):raise ValueError('Invalid camera '+k)
 for k in ['width','height']:
  if k in value and (type(value[k]) is not int or not 64<=value[k]<=8192):raise ValueError('Invalid camera '+k)
 return value
def door_states(states):
 for key,value in states.items():
  if not isinstance(key,str) or isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=120:raise ValueError('Door angles must be finite0..120 degrees')
def location(root,path):
 p=resolve(root,path);v=read(p)
 if v.get('schemaVersion')!=1 or v.get('units')!='meters':raise ValueError('Location schemaVersion1 and meter units required')
 inputs={path:sha(p)}
 for item in [v['plan'],v['underlay'],v['builder']]+v['builder'].get('dependencies',[]):
  target=resolve(root,item['path'])
  if sha(target)!=item['sha256']:raise ValueError('Pinned input checksum mismatch: '+item['path'])
  inputs[item['path']]=item['sha256']
 door_states(v.get('doorStates',{}));return v,inputs
def job(root,path,cube=False):
 j=read(resolve(root,path))
 if j.get('schemaVersion')!=1 or not j.get('id'):raise ValueError('Job schemaVersion1 and id required')
 camera(j.get('camera',{}),cube);door_states(j.get('doorStates',{}))
 if cube and (type(j.get('faceSize',512)) is not int or not 64<=j.get('faceSize',512)<=2048):raise ValueError('faceSize must be64..2048')
 return j
def artifact(path,out):return {'path':str(Path(path).relative_to(out)),'sha256':sha(path),'bytes':Path(path).stat().st_size}
def validate_manifest(path,root=None):
 path=Path(path).resolve();m=read(path)
 if m.get('schemaVersion')!=1 or m.get('stage') not in ['build','render','cubemap','prepared','generated']:raise ValueError('Unknown or missing manifest schema/stage')
 if not isinstance(m.get('inputs'),dict) or not m['inputs'] or not m.get('locationId'):raise ValueError('Manifest requires pinned input identities and locationId')
 if not isinstance(m.get('artifacts'),list) or not m['artifacts']:raise ValueError('Manifest requires nonempty artifacts')
 required={'build':'base.blend','render':'still.png','cubemap':'cube-atlas.png','prepared':'prompt.txt','generated':'provenance.json'}[m['stage']]
 if required not in [a.get('path') for a in m['artifacts']]:raise ValueError('Required stage artifact missing: '+required)
 for item in m.get('artifacts',[]):
  p=resolve(path.parent,item['path'])
  if not p.is_file() or p.stat().st_size!=item['bytes'] or sha(p)!=item['sha256']:raise ValueError('Artifact checksum mismatch: '+str(p))
 if root:
  for p,digest in m.get('inputs',{}).items():
   if sha(resolve(root,p))!=digest:raise ValueError('Source input changed: '+p)
 return {'pass':True,'artifactCount':len(m.get('artifacts',[]))}
