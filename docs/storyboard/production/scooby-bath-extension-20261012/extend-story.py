"""Insert new reviewed pages; retain every published v1 scene verbatim."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[4]
p=root/'docs/storyboard/stories/scooby-bath.json';s=json.loads(p.read_text())
if s['editionVersion']!=1:raise SystemExit('Extension requires the original edition')
texts=[
('Morning began with Mama’s familiar preparations: bread, berries, and water. PinPin carried the jug, and Mama filled Scooby’s own breakfast bowl.',
 'Утро началось с привычных Маминых забот: хлеб, ягоды и вода. ПинПин принёс кувшин, а Мама наполнила отдельную миску Скуби.',
 'La mañana empezó con los preparativos de siempre de Mamá: pan, bayas y agua. PinPin llevó la jarra, y Mamá llenó el cuenco de desayuno de Scooby.'),
('They ate breakfast together in the garden. Scooby finished his own food and looked up. His paws were clean, his coat was fluffy, and the whole day was waiting.',
 'Они вместе позавтракали в саду. Скуби доел свой корм и поднял голову. Лапы были чистые, шерсть пушистая, а впереди ждал целый день.',
 'Desayunaron juntos en el jardín. Scooby terminó su comida y levantó la cabeza. Tenía las patas limpias, el pelo esponjoso y todo un día por delante.'),
('“Clean paws before food, a little care before bed,” Mama reminded PinPin, as she did every day. She wiped one sticky paw. “And now you’re ready to play!”',
 '— Чистые лапки перед едой, немного заботы перед сном, — напомнила Мама ПинПину, как каждый день. Она вытерла липкую лапку. — А теперь можно играть!',
 '—Patitas limpias antes de comer y un poquito de cuidado antes de dormir —le recordó Mamá a PinPin, como cada día. Le limpió una pata pegajosa—. ¡Y ahora, a jugar!'),
('After breakfast, Papa and PinPin went out to play with Scooby. A leaf danced on the breeze. Scooby chased it, and PinPin chased Scooby’s wagging tail.',
 'После завтрака Папа и ПинПин пошли играть со Скуби. На ветру танцевал листок. Скуби побежал за ним, а ПинПин — за виляющим хвостом Скуби.',
 'Después del desayuno, Papá y PinPin salieron a jugar con Scooby. Una hoja bailaba en la brisa. Scooby la persiguió, y PinPin corrió detrás de su cola alegre.'),
('Then—splash! Scooby found a puddle left by the rain. Brown drops flew, and his clean paws disappeared into the mud. PinPin laughed from the dry grass.',
 'И тут — плюх! Скуби нашёл лужу после дождя. Бурые капли разлетелись, а чистые лапы погрузились в грязь. ПинПин смеялся, стоя на сухой траве.',
 'Y entonces… ¡plas! Scooby encontró un charco que había dejado la lluvia. Volaron gotas marrones, y sus patas limpias se hundieron en el barro. PinPin se rio desde la hierba seca.'),
('A roll in the damp leaves seemed like an excellent idea too. Scooby wriggled happily. Now his paws were muddy, his coat was muddy, and a leaf had come along for the ride.',
 'Поваляться в сырых листьях тоже показалось отличной идеей. Скуби радостно перевернулся. Теперь грязными были и лапы, и шерсть, а один листок отправился с ним дальше.',
 'Revolcarse entre las hojas húmedas también le pareció una idea estupenda. Scooby se retorció feliz. Ahora tenía barro en las patas y en el pelo, y una hoja se había apuntado al paseo.'),
('By afternoon, Mama and Papa had the bath ready. Mama checked the warm water, Papa brought towels, and PinPin found the brush. Scooby watched the preparations very carefully.',
 'Во второй половине дня Мама и Папа приготовили ванну. Мама проверила тёплую воду, Папа принёс полотенца, а ПинПин нашёл щётку. Скуби очень внимательно наблюдал за приготовлениями.',
 'Por la tarde, Mamá y Papá prepararon el baño. Mamá comprobó el agua tibia, Papá trajo las toallas y PinPin encontró el cepillo. Scooby observó los preparativos con mucha atención.'),
('Mama gave Scooby a quiet stroke. “Clean paws, a little care, and a goodnight cuddle,” she said. It was the same gentle routine she kept for her family every evening.',
 'Мама ласково погладила Скуби. — Чистые лапки, немного заботы и объятия на ночь, — сказала она. Так каждый вечер она нежно заботилась о своей семье.',
 'Mamá acarició a Scooby con suavidad. —Patitas limpias, un poquito de cuidado y un abrazo de buenas noches —dijo. Era la misma rutina cariñosa de su familia cada noche.'),
('Scooby yawned, and PinPin yawned too. Going to sleep meant letting tired paws rest and the day grow quiet. Tomorrow there would be time to play again.',
 'Скуби зевнул, и ПинПин тоже. Лечь спать — значит дать уставшим лапкам отдохнуть и тихо закончить день. Завтра снова будет время для игр.',
 'Scooby bostezó, y PinPin también. Irse a dormir significaba dejar descansar las patas cansadas y terminar el día en calma. Mañana habría tiempo para volver a jugar.')]
new=[]
for i,values in enumerate(texts,1):
 t=dict(zip(['en','ru','es'],values));id=f'ext-{i:02}'
 new.append({'id':id,'image':f'images/published/scooby-bath/extension-v2/{id}.webp','width':1536,'height':1024,'alt':t,'paragraphs':{k:[v] for k,v in t.items()}})
s['editionVersion']=2;s['scenes']=[s['scenes'][0],*new[:7],*s['scenes'][1:16],*new[7:],s['scenes'][16]]
s['spreads']=[{'scenes':[i],'style':'cover' if i==0 else 'elder','paper':'portrait' if i==0 else 'landscape'} for i in range(len(s['scenes']))]
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
