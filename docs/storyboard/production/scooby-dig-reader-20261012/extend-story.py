"""Add a six-step digging cause without modifying prior published scenes."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[4];p=root/'docs/storyboard/stories/scooby-bath.json';s=json.loads(p.read_text());assert s['editionVersion']==2
texts=[
('After chasing leaves, Scooby took Papa back to his old digging spot. He scratched the soft ground again. “Mind the little plant,” Papa said. Something round was peeping out!',
 'Побегав за листьями, Скуби привёл Папу туда, где уже копал раньше. Он снова поскрёб мягкую землю. — Осторожно, тут маленькое растение, — сказал Папа. Из земли показалось что-то круглое!',
 'Después de perseguir hojas, Scooby llevó a Papá al lugar donde ya había cavado. Volvió a rascar la tierra blanda. —Cuidado con la plantita —dijo Papá. ¡Algo redondo asomaba!'),
('PinPin picked up a smooth little stone. Scooby dug a little farther and uncovered an acorn. One treasure, then another! Perhaps there was something else beneath them.',
 'ПинПин поднял гладкий камешек. Скуби копнул чуть дальше и нашёл жёлудь. Сначала одно сокровище, потом другое! А вдруг под ними спряталось ещё что-нибудь?',
 'PinPin recogió una piedrecita lisa. Scooby cavó un poco más y descubrió una bellota. ¡Un tesoro y después otro! Quizá hubiera algo más debajo.'),
('Scratch, scratch, scratch! The hole grew wider and deeper. Soil flew over Scooby’s paws, legs, and tummy. Papa looked at the heap of earth. “You’ve been very busy!”',
 'Шкряб, шкряб, шкряб! Ямка становилась шире и глубже. Земля летела на лапы, ноги и живот Скуби. Папа посмотрел на выросшую кучку. — Вот это ты потрудился!',
 '¡Rasca, rasca, rasca! El hoyo se hizo más ancho y profundo. La tierra cayó sobre las patas y la barriga de Scooby. Papá miró el montón de tierra. —¡Cuánto has trabajado!'),
('At last, Scooby tried to climb out. His paws slid on the earthy bank. He looked at Papa, then back at the bottom. Couldn’t he dig just one little bit more?',
 'Наконец Скуби попробовал выбраться. Лапы скользили по земляному склону. Он посмотрел на Папу, потом снова на дно. А может, копнуть ещё совсем чуть-чуть?',
 'Por fin, Scooby intentó salir. Las patas resbalaban por la cuesta de tierra. Miró a Papá y después al fondo otra vez. ¿No podría cavar un poquito más?'),
('Papa shaped three broad steps in the sloping bank. PinPin edged the little staircase with smooth stones. Scooby watched from below. What a splendid way out!',
 'Папа сделал в склоне три широкие ступеньки. ПинПин выложил края маленькой лестницы гладкими камнями. Скуби наблюдал снизу. Вот это замечательный выход!',
 'Papá hizo tres escalones anchos en la cuesta. PinPin adornó los bordes con piedras lisas. Scooby miraba desde abajo. ¡Qué salida tan estupenda!'),
('Up came Scooby, one muddy paw at a time. At the top he turned back, still dreaming of more digging. “The treasures can wait until tomorrow,” Papa said. PinPin kept the stone and acorn.',
 'Скуби поднялся наверх, переставляя грязные лапы. На последней ступеньке он обернулся: так хотелось ещё покопать! — Сокровища подождут до завтра, — сказал Папа. ПинПин сохранил камешек и жёлудь.',
 'Scooby subió, una pata embarrada tras otra. Arriba se volvió, todavía soñando con seguir cavando. —Los tesoros pueden esperar hasta mañana —dijo Papá. PinPin guardó la piedra y la bellota.')]
new=[]
for i,values in enumerate(texts,1):
 id=f'dig-{i:02}';t=dict(zip(['en','ru','es'],values));new.append({'id':id,'image':f'images/published/scooby-bath/dig-v3/{id}.webp','width':1536,'height':1024,'alt':t,'paragraphs':{k:[v] for k,v in t.items()}})
index=next(i for i,x in enumerate(s['scenes']) if x['id']=='ext-05');s['scenes'][index:index]=new;s['editionVersion']=3;s['spreads']=[{'scenes':[i],'style':'cover' if i==0 else 'elder','paper':'portrait' if i==0 else 'landscape'} for i in range(len(s['scenes']))];p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
