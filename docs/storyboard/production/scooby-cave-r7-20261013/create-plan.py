"""Author an inspectable spatial/camera proposal; no generated image editing."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
nodes = [
    dict(id='R0', name='Root entrance', centre=[4,5,0], radius=[6,5], light='West daylight', clue='Cool draft and damp blossom'),
    dict(id='R1', name='Fern porch / family base', centre=[17,12,-.1], radius=[10,8], light='Entrance spill', clue='Broad dry station; supported infant'),
    dict(id='R2', name='Trained vine gallery', centre=[31,21,-.2], radius=[10,7], light='Three persistent amber vine clusters', clue='Repeated plant training beyond daylight'),
    dict(id='R3', name='Braided-root fork', centre=[44,31,-.35], radius=[8,7], light='Dim berries; lake reflection hidden by screen', clue='Worked root, leaf return, hollow echo'),
    dict(id='R4', name='Screen and reveal threshold', centre=[53,36,-.45], radius=[6,5], light='Lake light only AFTER limestone screen', clue='First view of a space larger than predicted'),
    dict(id='L5', name='Underground lake', centre=[76,55,-.8], radius=[24,18], light='North skylight + east/west luminous vines', clue='Stored living water; not proof of theft'),
    dict(id='K6', name='Keeper alcove / nursery', centre=[61,77,-.5], radius=[12,7], light='West vine light; no new sun shaft', clue='Caretaker trace and shore plant nursery'),
    dict(id='G7', name='Living root spillway', centre=[95,30,-1], radius=[8,6], light='Lake reflection + east daylight', clue='Old water marks; controlled-release problem'),
    dict(id='E8', name='East outlet', centre=[116,20,-1.15], radius=[7,6], light='East daylight', clue='Beaver verifies surface response'),
]
routes = [
    dict(id='first-approach', name='Approach → hidden lake → reveal', points=[[4,5],[17,12],[31,21],[44,31],[48,32],[51,35],[55,36],[57,38]], colour='#f1c979'),
    dict(id='west-bank', name='Dry west bank → keeper alcove', points=[[55,36],[51,46],[51,64],[61,77]], colour='#bf97eb'),
    dict(id='south-bank', name='Dry south bank → spillway → east outlet', points=[[55,36],[65,32],[79,31],[95,30],[116,20]], colour='#f1c979'),
    dict(id='outside-return', name='Shown exterior return around hill', points=[[116,20],[112,0],[84,-8],[49,-11],[16,-5],[4,5]], colour='#86bc83'),
]
water = [
    dict(id='feed', points=[[80,83],[81,76],[80,69]], direction='Natural seep feeds lake; source authorship unresolved'),
    dict(id='controlled-outlet', points=[[91,44],[95,36],[95,30],[106,25],[116,20],[125,12],[135,7]], direction='Lake → gate → existing surface water system'),
    dict(id='nursery', points=[[61,68],[62,72],[67,74]], direction='Lake shallows sustain nursery; do not drain them'),
]
cameras = [
    dict(id='A', name='Entrance orientation', position=[1,3,.7], target=[18,13,.4], horizontalFovDegrees=70, visible=['west entrance rim','fern base'], hidden=['lake','spillway'], scene='Follow Scooby into a broad visible threshold'),
    dict(id='B', name='Vine evidence', position=[26,17,.55], target=[34,24,.7], horizontalFovDegrees=62, visible=['same trained vines','braided-root approach'], hidden=['lake surface','keeper alcove'], scene='Detail and over-shoulder hypothesis, not a full-cast portrait'),
    dict(id='C', name='Before the screen', position=[44,29,.45], target=[50,34,.5], horizontalFovDegrees=58, visible=['limestone screen','returned leaf'], hidden=['lake expanse','east outlet'], scene='Hear and predict the concealed space'),
    dict(id='D', name='Lake reveal', position=[55,36,.45], target=[78,56,.8], horizontalFovDegrees=78, visible=['west bank','lake','north skylight','far east vines'], hidden=['surface pond','caretaker behind west bend'], scene='Cross the screen explicitly; first full lake view'),
    dict(id='E', name='Shore reverse', position=[51,61,.5], target=[57,37,.4], horizontalFovDegrees=65, visible=['west shore','reveal arch behind','same near vine cluster'], hidden=['east surface path'], scene='Reverse retains landmark and water side; establish axis first'),
    dict(id='F', name='Gate trial', position=[87,28,.35], target=[96,33,.2], horizontalFovDegrees=64, visible=['root gate','water marks','south lake edge','east daylight hint'], hidden=['keeper alcove','west entrance'], scene='Parent stops overlarge change; hands/flow insert'),
    dict(id='G', name='Outlet consequence', position=[113,16,-.4], target=[125,12,-.5], horizontalFovDegrees=68, visible=['outlet bank','Beaver station','surface stream'], hidden=['lake through rock'], scene='Observable surface payoff rather than magical explanation'),
]
plan = dict(schemaVersion=1, id='scooby-cave-r7-lake-proposal-v1', status='author-review-proposal-not-published-or-measured', units='authored relative blocking units, not recovered book measurements', axes='X east, Y north, Z up; plan north is screen up', nodes=nodes, walkingRoutes=routes, waterRoutes=water, cameras=cameras, occluders=[dict(id='limestone-screen', segment=[[49,31],[53,36]], height=3, purpose='Hide lake before the reveal; geometry render must verify exact sightlines')], waterLevel=-.8, lakeBedLevel=-2.5, minDryBankWidth=3, lights=[dict(id='north-shaft',position=[80,78,7],kind='filtered daylight, fixed north rim'),dict(id='west-vines',position=[52,55,3],kind='amber growing light'),dict(id='east-vines',position=[101,61,4],kind='amber growing light')], identityDecision='Veles/Elder relation awaits author; existing Elder unchanged', prohibitions=['stairs or spontaneous rescue structure','teleport between camera origins','lake visible through the limestone screen','water flowing uphill','open all gates without consequence','immediate god/theft inference from water','offscreen unsupervised infant'])
(ROOT/'cave-layout.json').write_text(json.dumps(plan,indent=2)+'\n')

def pos(point):
    return round(110+point[0]*8.5,2), round(760-point[1]*6.7,2)

def poly(points):
    return ' '.join(f'{x},{y}' for x,y in map(pos,points))

svg=['<svg id="plan" viewBox="0 0 1400 900" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Proposed cave plan with hidden underground lake, walking routes, water and recorded camera positions">', '<defs><marker id="water-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#64cee8"/></marker></defs>', '<rect width="1400" height="900" fill="#11221e"/>', '<text x="45" y="47" fill="#fff2d2" font-size="28">R7 PROPOSAL — a hidden underground lake</text>', '<text x="45" y="77" fill="#c2d3c0" font-size="16">North ↑ · authored blocking, not measured geometry · camera origins are distinct from turns</text>', '<path d="M85 735Q75 410 315 335Q500 70 880 125Q1180 175 1190 455L1170 710Q990 825 490 812Z" fill="#293b2c" stroke="#577252" stroke-width="3"/>']
for route in routes:
    svg.append(f'<polyline points="{poly(route["points"])}" fill="none" stroke="{route["colour"]}" stroke-width="{14 if route["id"]=="outside-return" else 32}" opacity=".48" stroke-linejoin="round" stroke-linecap="round"/>')
for n in nodes:
    x,y=pos(n['centre']);rx,ry=n['radius'];lake=n['id']=='L5'
    svg.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx*8.5}" ry="{ry*6.7}" fill="{"#245267" if lake else "#71634a"}" stroke="{"#91d6e2" if lake else "#c4b487"}" stroke-width="3"/>')
    lx,ly=x,y
    if n['id']=='R3': ly-=23
    if n['id']=='R4': lx+=20; ly-=26
    label=n['name'] if n['id']!='R4' else 'Reveal threshold'
    svg.append(f'<text x="{lx}" y="{ly-7}" fill="#fff6dc" text-anchor="middle" font-size="21" font-weight="bold">{n["id"]}</text><text x="{lx}" y="{ly+15}" fill="#fff6dc" text-anchor="middle" font-size="13">{label}</text>')
for w in water:
    svg.append(f'<polyline points="{poly(w["points"])}" fill="none" stroke="#64cee8" stroke-width="6" marker-end="url(#water-arrow)"/>')
svg.append(f'<polyline points="{poly(plan["occluders"][0]["segment"])}" stroke="#e3997c" stroke-width="13" stroke-linecap="round"/><text x="400" y="600" fill="#f5b098" font-size="14">Limestone screen: reveal ONLY after crossing</text>')
for light in plan['lights']:
    x,y=pos(light['position']);svg.append(f'<circle cx="{x}" cy="{y}" r="13" fill="#f8d975"/><text x="{x+18}" y="{y-10}" fill="#f8d975" font-size="13">{light["id"]}</text>')
for c in cameras:
    x,y=pos(c['position']);tx,ty=pos(c['target']);svg.append(f'<g class="camera" data-camera="{c["id"]}"><line x1="{x}" y1="{y}" x2="{x+(tx-x)*.3}" y2="{y+(ty-y)*.3}" stroke="#ffddf1" stroke-width="3"/><circle cx="{x}" cy="{y}" r="14" fill="#7b3868" stroke="#ffddf1" stroke-width="2"/><text x="{x}" y="{y+5}" text-anchor="middle" font-size="15" fill="white">{c["id"]}</text></g>')
svg += ['<g id="camera-frustum"></g>','<text x="45" y="845" fill="#e0d6b9" font-size="16">Gold: dry cave route · Purple: keeper branch · Green: surface return · Blue: water · Pink A–G: cameras</text>','<text x="45" y="875" fill="#b7cebe" font-size="15">Lake and nursery stay alive. Controlled outlet changes the surface stream; finding water alone proves no theft.</text>','</svg>']
map_svg=''.join(svg)
(ROOT/'cave-plan.svg').write_text(map_svg+'\n')
options=''.join(f'<option value="{c["id"]}">{c["id"]}: {c["name"]}</option>' for c in cameras)
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>R7 proposed cave plan</title><style>body{margin:0;background:#11221e;color:#fff1d0;font:17px/1.5 system-ui}main{max-width:1400px;margin:auto;padding:18px}h1{font-size:24px}svg{width:100%;height:auto}select{font:inherit;padding:8px;background:#fff1d0;color:#11221e}#details{padding:18px;background:#263a30;border-radius:12px}code{color:#bde4e7}.camera{cursor:pointer}.camera.selected circle{fill:#bb548e}a{color:#bde4e7}.section{margin-top:22px;padding:18px;background:#263a30}.section p{margin:8px 0}small{color:#c2d3c0}</style><main><h1>Spatial and discovery proposal — not a published replacement</h1><p>The original map had a shallow pool and an outdoor lake. This proposal adds a large concealed underground lake, dry banks, a nursery, a worked outlet and repeatable camera origins.</p>'''+map_svg+'''<p><label for="camera">Inspect a camera: </label><select id="camera">'''+options+'''</select></p><div id="details" aria-live="polite"></div><div class="section"><h2>Elevation and reveal contract</h2><p>Entrance floor <code>0</code> → gallery <code>−0.2</code> → reveal bank <code>−0.45</code> → lake water <code>−0.8</code>; lake bed <code>−2.5</code>. Gate <code>−1</code> → east outlet <code>−1.15</code>. These are authored relative levels; the walk uses broad gentle banks, not stairs.</p><p>The north skylight and two vine-light groups stay fixed. Camera C remains before the limestone screen; D explicitly crosses it. E is a new shore position, not a turn of D's panorama. Exact occlusion must be tested with blocking geometry before finished cave art.</p><p>Clues accumulate: draft → tended growing lights → worked root → returning leaf/echo → lake → controlled gate → caretaker trace. Veles's relation to the Elder remains an author decision.</p></div><p><a href="cave-layout.json">Layout/camera JSON</a> · <a href="cave-plan.svg">Standalone vector map</a></p><small>Creative planning illustration. No measured-conformance or completed-story approval claim.</small></main><script>const plan='''+json.dumps(plan)+''';const svg=document.getElementById('plan'),select=document.getElementById('camera');function xy(p){return[110+p[0]*8.5,760-p[1]*6.7]}function show(id){const c=plan.cameras.find(x=>x.id===id);select.value=id;document.querySelectorAll('.camera').forEach(e=>e.classList.toggle('selected',e.dataset.camera===id));const p=xy(c.position),q=xy(c.target),a=Math.atan2(q[1]-p[1],q[0]-p[0]),h=c.horizontalFovDegrees*Math.PI/360,r=140,one=[p[0]+Math.cos(a-h)*r,p[1]+Math.sin(a-h)*r],two=[p[0]+Math.cos(a+h)*r,p[1]+Math.sin(a+h)*r];document.getElementById('camera-frustum').innerHTML=`<polygon points="${p} ${one} ${two}" fill="#eab2d1" fill-opacity=".16" stroke="#ffc9e9" stroke-width="2"/>`;const d=document.getElementById('details');d.replaceChildren();for(const text of[`${c.id}: ${c.name}`,`Position [${c.position}], target [${c.target}], horizontal FOV ${c.horizontalFovDegrees}°`,c.scene,`Visible: ${c.visible.join('; ')}`,`Hidden: ${c.hidden.join('; ')}`]){const e=document.createElement('p');e.textContent=text;d.append(e)}}select.addEventListener('change',()=>show(select.value));document.querySelectorAll('.camera').forEach(e=>e.addEventListener('click',()=>show(e.dataset.camera)));show('D');</script></html>'''
(ROOT/'cave-plan.html').write_text(html+'\n')
assert len({n['id'] for n in nodes})==len(nodes)
assert len({c['id'] for c in cameras})==len(cameras)
assert all(1 < c['horizontalFovDegrees'] < 120 for c in cameras)
assert all(c['position'] != c['target'] for c in cameras)
assert plan['lakeBedLevel'] < plan['waterLevel']
print('Created proposed layout, seven camera records, vector map and interactive HTML')
