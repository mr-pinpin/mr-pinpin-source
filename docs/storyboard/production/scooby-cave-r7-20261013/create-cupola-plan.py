"""Version the cupola plan without overwriting the preserved first proposal."""
import copy, json, math
from pathlib import Path

P=Path(__file__).resolve().parent
plan=copy.deepcopy(json.loads((P/'cave-layout.json').read_text()))
metric=json.loads((P/'geometry/rotunda-plan.json').read_text())
plan.update(id='scooby-cave-r7-cupola-proposal-v2',status='authored-cupola-blocking-and-proposed-network-not-published',units='Plan XY units; lake chamber uses3plan units per authored meter. Metric Z/cameras are in the rotunda plan/jobs; network grades remain provisional.',metricChamberPlan='geometry/rotunda-plan.json',cupola=metric['rotunda'])
plan['lights']=[dict(id='central-oculus',position=[76,55,13.3],kind='one open circular crown aperture'),dict(id='west-vines',position=[49,61,4],kind='fixed growing light'),dict(id='east-vines',position=[103,61,4.6],kind='fixed growing light')]
for c in plan['cameras']:
    if c['id']=='C':c.update(position=[41.8,31,1.15],target=[49.9,35.8,1.5],horizontalFovDegrees=90,metricJob='geometry/before-screen.json')
    if c['id']=='D':c.update(position=[55,36,1.15],target=[76,61,5.5],horizontalFovDegrees=110,metricJob='geometry/lake-reveal.json')
    if c['id']=='E':c.update(position=[52,64,1.15],target=[58,34,3],metricJob='geometry/shore-reverse.json')
for route in plan['walkingRoutes']:
    if route['id']=='first-approach':route['points']=[[4,5],[17,12],[31,21],[44,31],[49,30],[57,31],[58,34],[55,36],[57,38]]
plan['cameras'].append(dict(id='H',name='Reflection insert, planned',position=[60.4,39.7,1.15],target=[61.6,41.5,-.35],horizontalFovDegrees=65,metricJob='geometry/lake-reflection.json',status='planned-not-rendered'))
plan['occluders']=[dict(id='limestone-screen',segment=[[47.46,43.26],[55.94,33.14]],purpose='Actual rotunda screen; tested before/after lake-point rays')]
(P/'cave-layout-v2.json').write_text(json.dumps(plan,indent=2)+'\n')
def xy(p):return (100+p[0]*7.5,760-p[1]*7.5)
def points(ps):return ' '.join(f'{x:.2f},{y:.2f}' for x,y in map(xy,ps))
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 1000" role="img" aria-label="Cupola cave plan and section">','<rect width="1400" height="1000" fill="#12231f"/>','<text x="40" y="43" fill="#fff1d0" font-size="29">R7 v2 — underground lake beneath one great cupola</text>','<text x="40" y="74" fill="#c4d7c2" font-size="16">North ↑ · original-book planting/vault references · recorded 3D chamber; wider network remains proposed</text>']
for r in plan['walkingRoutes']:s.append(f'<polyline points="{points(r["points"])}" fill="none" stroke="{r["colour"]}" stroke-width="22" stroke-linecap="round" opacity=".6"/>')
cx,cy=xy([76,55]);radius=metric['rotunda']['innerRadius']*3*7.5
s.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="#5e6143" fill-opacity=".28" stroke="#bfc0a0" stroke-width="3" stroke-dasharray="9 6"/>')
for n in plan['nodes']:
    x,y=xy(n['centre']);rx,ry=n['radius'];lake=n['id']=='L5'
    s.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx*7.5}" ry="{ry*7.5}" fill="{"#225366" if lake else "#786449"}" stroke="{"#9bd7df" if lake else "#cabb92"}" stroke-width="2"/>')
    label=n['name']
    if n['id']=='R3':y-=22;label='Root fork'
    if n['id']=='R4':x+=20;y-=25;label='Reveal bank'
    s.append(f'<text x="{x}" y="{y-7}" fill="#fff3d6" text-anchor="middle" font-size="19">{n["id"]}</text><text x="{x}" y="{y+14}" fill="#fff3d6" text-anchor="middle" font-size="13">{label}</text>')
for w in plan['waterRoutes']:s.append(f'<polyline points="{points(w["points"])}" fill="none" stroke="#67d0e8" stroke-width="5"/>')
for light in plan['lights']:
    x,y=xy(light['position']);r=metric['rotunda']['oculusRadius']*3*7.5 if light['id']=='central-oculus' else 9
    s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#f5d37c" fill-opacity=".38" stroke="#f5d37c" stroke-width="2"/><text x="{x+r+10}" y="{y-15}" fill="#ffe3a1" font-size="14">{light["id"]}</text>')
s.append(f'<polyline points="{points(plan["occluders"][0]["segment"])}" stroke="#e39e80" stroke-width="8"/>')
for c in plan['cameras']:
    x,y=xy(c['position']);tx,ty=xy(c['target']);a=math.atan2(ty-y,tx-x);h=math.radians(c['horizontalFovDegrees']/2)
    if c['id']=='D':s.append(f'<path d="M{x},{y} L{x+math.cos(a-h)*130},{y+math.sin(a-h)*130} L{x+math.cos(a+h)*130},{y+math.sin(a+h)*130}Z" fill="#e6a8d0" fill-opacity=".18" stroke="#e6a8d0"/>')
    s.append(f'<circle cx="{x}" cy="{y}" r="12" fill="#88446c" stroke="#f9cde8"/><text x="{x}" y="{y+5}" text-anchor="middle" fill="white" font-size="14">{c["id"]}</text>')
s+=['<text x="1040" y="130" fill="#fff1d0" font-size="22">LAKE CHAMBER SECTION</text>','<text x="1040" y="157" fill="#c4d7c2" font-size="14">Authored dimensions, not book measurements</text>','<path d="M1045,405 L1045,350 Q1045,212 1158,200 M1190,200 Q1305,212 1305,350 L1305,405" fill="none" stroke="#cabb92" stroke-width="13"/>','<line x1="1074" y1="405" x2="1276" y2="405" stroke="#6bccde" stroke-width="8"/>','<line x1="1045" y1="398" x2="1074" y2="398" stroke="#bca47b" stroke-width="11"/><line x1="1276" y1="398" x2="1305" y2="398" stroke="#bca47b" stroke-width="11"/>','<path d="M1161,204 L1114,399 L1233,399 L1187,204" fill="#f4d578" fill-opacity=".12"/>','<text x="1065" y="450" fill="#fff1d0" font-size="15">21.6m chamber · 16×12m lake</text>','<text x="1065" y="478" fill="#fff1d0" font-size="15">13.3m crown · 4.4m open oculus</text>','<text x="1065" y="506" fill="#fff1d0" font-size="15">Broad dry shore; water 0.35m below</text>','<text x="1065" y="546" fill="#e4b3a0" font-size="14">C: tested lake ray blocked</text>','<text x="1065" y="571" fill="#e4b3a0" font-size="14">D: tested lake and oculus rays clear</text>','<text x="40" y="914" fill="#fff1d0" font-size="17">Dashed circle: cupola footprint · Central gold circle: ONE crown opening · Blue: lake/water · Pink: saved cameras</text>','<text x="40" y="945" fill="#c4d7c2" font-size="15">Keep the preserved v1 plan separate. The old north-rim shaft is superseded by the central oculus.</text>','</svg>']
svg=''.join(s);(P/'cave-plan-v2.svg').write_text(svg+'\n')
(P/'cave-plan-v2.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cupola lake plan v2</title><style>body{margin:0;background:#12231f;color:#fff1d0;font:17px system-ui}main{max-width:1400px;margin:auto;padding:18px}svg{width:100%;height:auto}a{color:#b9e4ea}</style><main><p>New author-confirmed cupola direction; preproduction, not a published replacement.</p>'+svg+'<p><a href="geometry/rotunda-plan.json">Metric chamber source</a> · <a href="cave-layout-v2.json">Network/camera links</a> · <a href="CANON-AND-CUPOLA.md">Original book connections</a></p></main></html>\n')
print('Saved cupola v2 map, section and network/camera links; preserved v1 untouched')
