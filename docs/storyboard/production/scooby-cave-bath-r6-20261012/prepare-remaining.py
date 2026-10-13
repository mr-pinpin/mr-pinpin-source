"""Prepare missing scene handoffs only; built-in tool invocation remains separate."""
import json,subprocess,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent;root=p.parents[3]
script=json.loads((p/'script/story-script.json').read_text());selected=json.loads((p/'working-selection.json').read_text())['selected'];anchors={x['location']:p/x['native'] for x in json.loads((p/'environment/anchors.json').read_text())['anchors']}
jobs=[]
for s in script['scenes']:
 n=s['number'];id=f'r6-{n:03}-v1';dest=p/'prompts'/f'{id}.txt'
 if f'{n:03}' in selected or n in [13,15,16,17,18,19,51,70,74,88,93,95,128,138]:continue
 if s.get('reusedApprovedImage') or s.get('reusedEnvironmentNative'):continue
 refs=[];loc=s['location'];cast=s['visibleCast']
 def add(role,path):refs.append((role,str(path)))
 if loc in anchors:add('Environment geometry, landmark directions and lighting ONLY; add exactly the assigned actors/actions',anchors[loc])
 if loc in ['H1','H2']:
  add('Family identities and selected room continuity; change expressions/action to this shot',p/'native'/('r6-053-v1.png' if loc=='H2' else 'r6-001-v1.png'))
 else:
  if any(c in cast for c in ['Papa','Scooby','PinPin']):add('Papa, PinPin and giant Scooby identities/scale ONLY; cave background only when assigned, NO blossom/boats unless current shot requires',p/'native/r6-041-v2.png')
  if any(c in cast for c in ['Mama','PomPom']):add('Mama, supported PomPom and PinPin identity ONLY; indoor furniture only when assigned',p/'native/r6-014-v1.png')
 if 'Rabbit' in cast:add('Rabbit identity, folded green leaf boat shape ONLY; do NOT copy grinning acting or extra boats',root/'docs/storyboard/images/published/bath-magic/r17/scene-03l.webp')
 if loc=='S0' or any(c in cast for c in ['BlueTit','Robin']):add('Known stone spring and exactly one blue tit/one robin identities, no wooden bucket',root/'docs/storyboard/images/published/bath-magic/r17/scene-05b.webp')
 if 'Elder' in cast:add('Elder gray quills and round gold spectacles ONLY; no tractor, garden furniture, cane or reference cast',root/'docs/storyboard/images/published/bath-magic/r24/scene-328.webp')
 if 'Beaver' in cast:add('Adult Beaver in BLUE work vest ONLY; no wife, children or reference picnic props',root/'docs/storyboard/images/published/bath-magic/r24/scene-321.webp')
 if loc=='H0':add('Cottage facade, green door and pink terracotta flower east of step; clean dog identity only when assigned',p/'native/r6-009-v1.png')
 if not refs:add('PinPin book style and identities ONLY, use authored environment/action',p/'native/r6-041-v2.png')
 if not dest.exists():
  args=['python3',str(p/'prepare-image.py'),str(n)]
  for role,path in refs:args+=['--reference',role+'='+path]
  subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
  with dest.open('a') as f:f.write('\nADDITIONAL FIXED CONTINUITY: No invented signboards or cave direction symbols: the cave is discovered by smell and draft. No staircase or ladder. Use ONLY the cast assigned to this still. One baby held securely whenever present. No infant walking. Do not import background props or animals from identity references. Elder carries no walking stick in this chapter; his spectacles identify him. Do not draw captions.\n')
  hand=p/'prompts'/f'{id}-handoff.json';h=json.loads(hand.read_text());h['promptSha256']=hashlib.sha256(dest.read_bytes()).hexdigest();hand.write_text(json.dumps(h,indent=2)+'\n')
 h=json.loads((p/'prompts'/f'{id}-handoff.json').read_text());jobs.append({'id':id,'prompt':str(dest),'references':[x['path'] for x in h['references']]})
print(json.dumps(jobs,indent=2))
