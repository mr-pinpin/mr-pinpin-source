#!/usr/bin/env python3
"""Build review-only WebP comparisons from immutable lane manifests."""
import argparse,hashlib,json,shutil
from pathlib import Path
from PIL import Image
parser=argparse.ArgumentParser()
parser.add_argument('--complete',action='store_true')
args=parser.parse_args()
root=Path(__file__).resolve().parent
old=root.parent/'pinpin-bath-magic-20261001-r5'
selected=json.loads((old/'derivatives.json').read_text())['assets']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source(lane,value):
 p=(root/lane/value).resolve()
 if root not in p.parents:raise ValueError('Source outside correction pack: '+str(p))
 return p
def derivative(path,slug):
 target=root/'web'/f'{slug}.webp'
 with Image.open(path) as image:
  rgb=image.convert('RGB')
  if path.suffix.lower()=='.webp':shutil.copy2(path,target)
  else:rgb.save(target,'WEBP',quality=94,method=6)
  width,height=rgb.size
 return {'path':target.relative_to(root).as_posix(),'sha256':sha(target),'bytes':target.stat().st_size,'width':width,'height':height,'source':path.relative_to(root).as_posix(),'sourceSha256':sha(path),'operation':'unchanged WebP byte copy' if path.suffix.lower()=='.webp' else 'native-size WebP encoding, quality94 method6; no artwork edits'}
labels={
'beds':{'title':{'en':'The shared family bed','ru':'Общая семейная кровать','es':'La cama compartida de la familia'},'reason':{'en':'Show the family sharing the same broad bed, with each character clearly separate.','ru':'Показать семью в одной широкой кровати так, чтобы каждый персонаж был отчётливо виден.','es':'Mostrar a la familia compartiendo la misma cama ancha, con cada personaje claramente separado.'}},
'geometry':{'title':{'en':'Inside the bath','ru':'В ванне','es':'Dentro de la bañera'},'reason':{'en':'Correct the bath geometry and the family’s placement.','ru':'Сплошная деревянная стенка окружает семью; под водой видно деревянное дно. Сохранён вид над водой и под ней.','es':'Una pared continua de madera rodea a la familia y se ve el fondo de madera bajo el agua. Se conserva la vista dividida por la superficie.'}},
'tables':{'title':{'en':'Around the table','ru':'За столом','es':'Alrededor de la mesa'},'reason':{'en':'Keep the table and the family’s seating consistent.','ru':'Вернуть обычный круглый деревянный стол, а таз с уткой поставить рядом на отдельную низкую табуретку.','es':'Recuperar la mesa redonda de madera y colocar el recipiente del pato sobre un taburete bajo aparte.'}}}
rows=[];documents=[];manifests=[]
for lane in ['beds','geometry','tables']:
 m=root/lane/'manifest.json'
 if not m.exists():
  if args.complete:raise ValueError('Missing lane manifest: '+lane)
  continue
 entries=json.loads(m.read_text())['corrections'];manifests.append({'path':m.relative_to(root).as_posix(),'sha256':sha(m)})
 for entry in entries:
  number=int(str(entry['sceneId']).split('-')[-1]);sid=f'scene-{number:02}'
  before=source(lane,entry['original']);after=source(lane,entry['proposal'])
  assert before.is_file() and after.is_file(),sid
  original=selected[sid]
  digest=sha(before)
  assert digest in {original['master']['sha256'],original['web']['sha256']},'R5 original identity mismatch: '+sid
  row={'id':sid,'number':number,'lane':lane,'title':entry.get('title',labels[lane]['title']),'reason':entry.get('reason',labels[lane]['reason']),'status':'candidate awaiting user review','original':derivative(before,sid+'-before'),'proposal':derivative(after,sid+'-after'),'originR5':{'master':original['master'],'web':original['web']},'laneEntry':entry}
  record=source(lane,entry['record']);record_data=json.loads(record.read_text())
  row['documents']=[{'path':record.relative_to(root).as_posix(),'title':'Generation record'}]
  prompt=source(lane,record_data['promptPath'])
  assert prompt.is_file(),prompt
  row['documents'].append({'path':prompt.relative_to(root).as_posix(),'title':'Exact image prompt'})
  if isinstance(row['reason'],str):row['reason']={**labels[lane]['reason'],'en':row['reason']}
  rows.append(row)
 for path in sorted((root/lane).rglob('*')):
  if path.is_file() and path.suffix in {'.md','.json','.txt'}:
   documents.append({'path':path.relative_to(root).as_posix(),'title':path.relative_to(root).as_posix()})
if (root/'twelve-mishaps-proposal.json').exists():
 documents.insert(0,{'path':'twelve-mishaps-proposal.json','title':{'en':'Story proposal — not rendered','ru':'Предложение сюжета — без новых иллюстраций','es':'Propuesta de historia — sin ilustrar'}})
rows.sort(key=lambda r:r['number']);assert len({r['id'] for r in rows})==len(rows)
data={'status':'correction candidates awaiting user review; R5 unchanged','rows':rows,'expectedRows':max(7,len(rows)),'documents':documents,'laneManifests':manifests}
(root/'corrections.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'rows':len(rows),'scenes':[r['id'] for r in rows],'documents':len(documents)}))
