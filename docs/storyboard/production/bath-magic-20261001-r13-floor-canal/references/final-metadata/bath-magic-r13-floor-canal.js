'use strict';
(() => {
  const pack = new URL('../production/bath-magic-20261001-r13-floor-canal/', location.href);
  const upstream = new URL('../production/bath-magic-20261001-r12-house-layout/', location.href);
  const params = new URLSearchParams(location.search);
  let lang = ['en', 'ru', 'es'].includes(params.get('lang')) ? params.get('lang') : 'ru';
  let mode = ['storyboard','changes'].includes(params.get('view')) ? params.get('view') : 'read';
  let plan, media, causal, boards, before, edits, beforeMedia;
  const $ = id => document.getElementById(id);
  const words = {
    en: {read:'Read', board:'Storyboard', draft:'Chapter draft · For review', made:'How this chapter was made', pending:'Illustration in progress', ready:(n,t)=>`${n} of ${t} illustrations ready`, complete:n=>`${n} illustrated scenes · Continuity review`, plan:'Story and camera plan', prompts:'Illustration prompts', refs:'Character and location references', report:'Review notes', sheet:'Storyboard sheet'},
    ru: {read:'Читать', board:'Раскадровка', draft:'Черновик главы · Для просмотра', made:'Как создавалась эта глава', pending:'Иллюстрация в работе', ready:(n,t)=>`Готово иллюстраций: ${n} из ${t}`, complete:n=>`${n} иллюстрированных сцен · Проверка согласованности`, plan:'История и план кадров', prompts:'Задания для иллюстраций', refs:'Образы героев и дома', report:'Заметки к просмотру', sheet:'Лист раскадровки'},
    es: {read:'Leer', board:'Storyboard', draft:'Borrador del capítulo · Para revisar', made:'Cómo se creó este capítulo', pending:'Ilustración en preparación', ready:(n,t)=>`${n} de ${t} ilustraciones listas`, complete:n=>`${n} escenas ilustradas · Revisión de continuidad`, plan:'Historia y plan de cámara', prompts:'Instrucciones de ilustración', refs:'Referencias de personajes y lugares', report:'Notas de revisión', sheet:'Hoja del storyboard'}
  };
  const localized = value => typeof value === 'string' ? value : value?.[lang] ?? value?.en ?? '';
  const el = (name, className, text) => { const node = document.createElement(name); if(className) node.className=className; if(text !== undefined) node.textContent=text; return node; };
  const mediaURL = entry => {const url=new URL(typeof entry==='string'?entry:entry.path,new URL('../production/'+(entry.sourceProduction||'bath-magic-20261001-r13-floor-canal')+'/',location.href));if(entry.sha256)url.searchParams.set('v',entry.sha256.slice(0,12));return url.href;};
  const asset = item => {
    const entry = media?.images?.[item.id==='title'?'cover':item.id];
    if(!entry) return null;
    return mediaURL(entry);
  };
  function illustration(item, eager=false) {
    const url = asset(item);
    if(!url) return el('p','pending',words[lang].pending);
    const img = el('img'); img.src=url; img.alt=localized(item.alt)||localized(item.title); img.loading=eager?'eager':'lazy'; img.decoding='async';
    const dimensions=media.images[item.id==='title'?'cover':item.id];if(dimensions.width && dimensions.height){img.width=dimensions.width;img.height=dimensions.height;}
    if(eager) img.fetchPriority='high';
    img.addEventListener('error',()=>{img.replaceWith(el('p','error',words[lang].pending));});
    return img;
  }
  function setMode(next, update=true) {
    mode=next;
    $('changes').hidden=mode!=='changes'; $('chapter').hidden=mode!=='read'; $('overview').hidden=mode!=='storyboard'; $('cover').hidden=mode!=='read'; $('day-links').hidden=mode!=='read';
    $('read-tab').setAttribute('aria-pressed',String(mode==='read')); $('overview-tab').setAttribute('aria-pressed',String(mode==='storyboard'));
    if(update) updateURL();
  }
  function updateURL() { const url=new URL(location.href); url.searchParams.set('lang',lang); if(mode!=='read') url.searchParams.set('view',mode); else url.searchParams.delete('view'); history.replaceState(null,'',url); }
  function causalOverview(){
    if(!causal?.nodes?.length)return;
    const labels={
      en:{title:'Why one spell leads to the next',rhythm:'Cause → spell → pause → surprise → family response',from:'Follows',cause:'Problem',attempt:'Attempt',hold:'Visual pause',misfire:'Magical mistake',payoff:'Family response',remains:'What remains',scene:'Scene',ending:'The rhythm changes at the end',refrain:'The familiar incantation'},
      ru:{title:'Почему одно заклинание ведёт к следующему',rhythm:'Причина → заклинание → пауза → сюрприз → реакция семьи',from:'После',cause:'Проблема',attempt:'Попытка',hold:'Пауза в изображениях',misfire:'Магическая ошибка',payoff:'Реакция семьи',remains:'Что остаётся',scene:'Кадр',ending:'В конце ритм меняется',refrain:'Знакомое заклинание'},
      es:{title:'Por qué un hechizo lleva al siguiente',rhythm:'Causa → hechizo → pausa → sorpresa → respuesta familiar',from:'Después de',cause:'Problema',attempt:'Intento',hold:'Pausa visual',misfire:'Error mágico',payoff:'Respuesta familiar',remains:'Lo que queda',scene:'Escena',ending:'El ritmo cambia al final',refrain:'La fórmula conocida'}
    }[lang];
    const section=el('section','causal-overview');section.id='causal-flow';section.append(el('h2','',labels.title),el('p','causal-pattern',labels.rhythm),el('p','causal-refrain',labels.refrain+': “'+localized(causal.refrain)+'”'));
    function sceneLink(n){const button=el('button','scene-link',labels.scene+' '+n);button.type='button';button.addEventListener('click',()=>{setMode('read');requestAnimationFrame(()=>document.getElementById('scene-'+String(n).padStart(2,'0'))?.scrollIntoView({behavior:'smooth'}));});return button;}
    const grid=el('div','causal-grid');
    for(const node of causal.nodes){const card=el('article','causal-node');card.id='causal-'+node.id;const scene=plan.scenes.find(s=>s.number===node.misfireScene);card.append(el('h3','',node.id+'. '+localized(scene?.title||node.misfire)));
      if(node.parentIds?.length){const parents=el('p','causal-parents',labels.from+' ');for(const parent of node.parentIds){const a=el('a','',String(parent));a.href='#causal-'+parent;parents.append(a);}card.append(parents);}
      const dl=el('dl');
      for(const [key,label] of [['cause',labels.cause],['attempt',labels.attempt],['misfire',labels.misfire],['payoff',labels.payoff],['persistentConsequence',labels.remains]]){dl.append(el('dt','',label),el('dd','',localized(node[key])));}
      card.append(dl);const timing=el('div','causal-timing');timing.append(sceneLink(node.attemptScene),el('span','', ' → '),sceneLink(node.misfireScene));card.append(timing);
      const hold=el('div','causal-hold');hold.append(el('span','',labels.hold+': '));for(const n of node.pauseFrames||[])hold.append(sceneLink(n));card.append(hold);grid.append(card);
    }section.append(grid);
    if(causal.resolution){const ending=el('div','causal-resolution');ending.append(el('h3','',labels.ending),el('p','',localized(causal.resolution.rhythmBreak)));for(const n of [causal.resolution.seedScene,causal.resolution.recollectionScene,causal.resolution.observationScene,...causal.resolution.successfulInverseScenes||[]])if(n)ending.append(sceneLink(n));section.append(ending);}
    $('overview').append(section);
  }
  function render() {
    document.documentElement.lang=lang;
    const previous=document.querySelector('.previous-draft');previous.href=`bath-magic-r12-house-layout.html?lang=${lang}`;previous.title=localized({en:'Previous draft',ru:'Предыдущий вариант',es:'Borrador anterior'});previous.setAttribute('aria-label',previous.title);
    const w=words[lang];
    $('chapter-title').textContent=localized(plan.title); document.title=`${localized(plan.title)} · ${w.draft}`;
    $('draft-label').textContent=w.draft; $('read-tab').textContent=w.read; $('overview-tab').textContent=w.board; $('production-title').textContent=w.made;
    document.querySelectorAll('[data-lang]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lang===lang)));
    const ready=plan.scenes.filter(s=>asset(s)).length;
    $('progress').textContent=ready===plan.scenes.length && asset(plan.cover) ? w.complete(ready) : w.ready(ready,plan.scenes.length);
    $('cover').replaceChildren(illustration(plan.cover,true));
    $('chapter').replaceChildren(); $('overview').replaceChildren(); $('day-links').replaceChildren();
    $('causal-tab').textContent=localized({en:'Cause & rhythm',ru:'Причины и ритм',es:'Causas y ritmo'});
    const dayLabel=localized({en:'Day',ru:'День',es:'Día'});
    let previousDay=null;
    for(const scene of plan.scenes) {
      const day=Number(scene.day||1);
      if(day!==previousDay){
        const heading=el('header','day-heading');heading.id=`day-${day}`;heading.append(el('h2','',`${dayLabel} ${day}`));$('chapter').append(heading);
        const link=el('a','',`${dayLabel} ${day}`);link.href=`#day-${day}`;$('day-links').append(link);previousDay=day;
      }
      const article=el('article','scene'); article.id=scene.id;
      article.append(illustration(scene,scene.number===1));
      const text=el('div','scene-text'); text.append(el('span','scene-number',String(scene.number).padStart(2,'0')+' · '+scene.id+' · '+(scene.feedbackLabel||'')));
      const paragraphs=localized(scene.paragraphs); for(const p of Array.isArray(paragraphs)?paragraphs:[paragraphs]) text.append(el('p','',p));
      article.append(text); $('chapter').append(article);
    }

    const boardLang=lang==='es'?'en':lang;
    const selectedBoards=(boards?.boards||[]).filter(b=>b.language===boardLang).sort((a,b)=>a.number-b.number);
    $('overview').append(el('h2','',localized({ru:'Вся история на пяти листах',en:'The whole story on five sheets',es:'Toda la historia en cinco hojas'})));
    if(boards?.preproduction || selectedBoards.some(b=>b.pendingPanels))$('overview').append(el('p','preproduction-notice',localized({ru:'Предварительная раскадровка: пустые панели обозначают будущие иллюстрации. Новые предложения появляются в полном просмотре главы по мере готовности.',en:'Preproduction storyboard: blank panels mark upcoming illustrations. The full reader shows new proposals as they become ready.',es:'Storyboard preliminar: los paneles vacíos indican ilustraciones pendientes. El lector completo muestra las nuevas propuestas disponibles.'})));
    if(lang==='es')$('overview').append(el('p','', 'Las cinco hojas usan texto en inglés; el capítulo completo está en español.'));
    if(selectedBoards.length!==5)$('overview').append(el('p','pending',localized({ru:'Собираем пять листов…',en:'Assembling five sheets…',es:'Preparando cinco hojas…'})));
    for(const board of selectedBoards){
      const figure=el('figure','comic-sheet');const caption=el('figcaption','',`${board.number} / 5 · ${board.sceneStart}–${board.sceneEnd}`);figure.append(caption);
      const stage=el('div','comic-stage'),img=el('img');const url=new URL(board.path,pack);url.searchParams.set('v',board.sha256.slice(0,12));img.src=url.href;img.alt=localized({ru:'Лист',en:'Sheet',es:'Hoja'})+' '+board.number;img.width=board.width;img.height=board.height;img.loading=board.number===1?'eager':'lazy';stage.append(img);
      for(const panel of board.panels||[]){const a=el('a','panel-link');a.href='#'+panel.sceneId;a.setAttribute('aria-label',localized({ru:'Читать кадр ',en:'Read scene ',es:'Leer escena '})+panel.sceneId.replace('scene-',''));Object.assign(a.style,{left:(panel.x/board.width*100)+'%',top:(panel.y/board.height*100)+'%',width:(panel.width/board.width*100)+'%',height:(panel.height/board.height*100)+'%'});a.addEventListener('click',e=>{e.preventDefault();setMode('read');requestAnimationFrame(()=>$(panel.sceneId)?.scrollIntoView({behavior:'smooth'}));});stage.append(a);}
      figure.append(stage);const full=el('a','sheet-download',localized({ru:'Открыть крупнее / сохранить',en:'Open full size / save',es:'Abrir grande / guardar'}));full.href=url.href;full.target='_blank';full.rel='noopener';figure.append(full);$('overview').append(figure);
    }
    $('changes').replaceChildren(el('h2','',localized({ru:'Предложения по исправлениям',en:'Proposed corrections',es:'Correcciones propuestas'})),el('p','',localized({ru:'Три исправления канала: слева — R12, справа — новый вариант. Номера кадров, текст и порядок истории не изменились.',en:'Three canal corrections: R12 at left, revised art at right. Scene numbers, text and story order are unchanged.',es:'Tres correcciones del canal: R12 a la izquierda, nueva versión a la derecha. Los números, el texto y el orden no cambian.'})));
    for(const scene of plan.scenes.filter(s=>(!s.retainArt || media.images[s.id]?.sourceProduction==='bath-magic-20261001-r13-floor-canal') && beforeMedia.images[s.id])){
      const article=el('article','art-change');article.append(el('h3','', 'R12 '+String(scene.r12Number)+' · '+scene.id+' · '+localized({ru:'Теперь ',en:'Now ',es:'Ahora '})+String(scene.number)));
      const row=el('div','comparison-row');const oldFigure=el('figure'),oldImg=el('img'),entry=beforeMedia.images[scene.id];oldImg.src=mediaURL(entry);oldImg.alt=localized({ru:'Прежняя иллюстрация',en:'Previous illustration',es:'Ilustración anterior'});oldImg.loading='lazy';oldImg.width=entry.width;oldImg.height=entry.height;oldFigure.append(el('figcaption','',localized({ru:'Раньше',en:'Before',es:'Antes'})),oldImg);
      const newFigure=el('figure');newFigure.append(el('figcaption','',localized({ru:'Предложение',en:'Proposal',es:'Propuesta'})),illustration(scene));row.append(oldFigure,newFigure);article.append(row);$('changes').append(article);
    }
    for(const removed of edits?.removed||[]){
      const article=el('article','removed-scene');article.append(el('h3','',localized({ru:'Удалён кадр R11 ',en:'Removed R11 image ',es:'Imagen R11 eliminada '})+removed.r11Number+' · '+removed.id));
      const entry=beforeMedia.images[removed.id];if(entry){const img=el('img');img.src=mediaURL(entry);img.alt=localized({ru:'Удалённая иллюстрация',en:'Removed illustration',es:'Ilustración eliminada'});img.loading='lazy';img.width=entry.width;img.height=entry.height;article.append(img);}
      article.append(el('p','',localized({ru:'Этот кадр удалён по вашей просьбе. Остальной порядок истории сохранён.',en:'Removed at your request. The rest of the story keeps its order.',es:'Eliminada como pediste. El resto de la historia mantiene su orden.'})));$('changes').append(article);
    }
    const textDetails=el('details','caption-changes');textDetails.append(el('summary','',localized({ru:'Изменения повествования',en:'Narrative changes',es:'Cambios del relato'})));$('changes').append(textDetails);
    for(const scene of plan.scenes){const old=before.scenes.find(s=>s.id===scene.id);if(JSON.stringify(old?.paragraphs?.[lang])===JSON.stringify(scene.paragraphs?.[lang]))continue;const article=el('article','text-change');article.append(el('h3','',String(scene.number)));const pair=el('div','change-pair');for(const [label,content]of[[localized({ru:'Раньше',en:'Before',es:'Antes'}),old?.paragraphs?.[lang]],[localized({ru:'Теперь',en:'Now',es:'Ahora'}),scene.paragraphs?.[lang]]]){const column=el('div');column.append(el('strong','',label));for(const p of content||[])column.append(el('p','',p));pair.append(column);}article.append(pair);const change=edits?.changes?.find(c=>c.id===scene.id);if(change)article.append(el('p','change-reason',localized(change.reason)));const link=el('button','scene-link',localized({ru:'Читать кадр',en:'Read scene',es:'Leer escena'}));link.onclick=()=>{setMode('read');requestAnimationFrame(()=>$(scene.id)?.scrollIntoView({behavior:'smooth'}));};article.append(link);textDetails.append(article);}
    $('changes-tab').textContent=localized({ru:'До и после',en:'Before / after',es:'Antes / después'});document.querySelector('.revision-links a').textContent=localized({ru:'Анализ версии R8 ↗',en:'R8 tempo analysis ↗',es:'Análisis de R8 ↗'});
    const production=$('production-content'); production.replaceChildren();
    for(const [path,label] of [['story-plan.json',w.plan],...(media.documents||[]).map(x=>[x.path,x.title])]) {const a=el('a','',label); a.href=new URL(path,pack).href; a.target='_blank'; a.rel='noopener'; production.append(a);}
    if(media.concept) {
      const figure=el('figure','board-sheet'),img=el('img');img.src=mediaURL(media.concept);img.alt=localized({en:'Exploratory concept — not a chronological storyboard',ru:'Поисковый эскиз — не последовательная раскадровка',es:'Concepto exploratorio — no es un storyboard cronológico'});img.loading='lazy';figure.append(img,el('figcaption','',img.alt));production.append(figure);
    }
    for(const ref of media.references||[]) {const figure=el('figure','board-sheet'),img=el('img');img.src=mediaURL(ref);img.alt=localized(ref.title)||w.refs;img.loading='lazy';figure.append(img,el('figcaption','',localized(ref.title)||w.refs));production.append(figure);}
    const details=el('details'),summary=el('summary','',w.plan);details.append(summary,el('pre','',JSON.stringify(plan,null,2)));production.append(details);
    setMode(mode,false);
  }
  $('changes-tab').addEventListener('click',()=>{setMode('changes');window.scrollTo({top:0,behavior:'instant'});});
  $('causal-tab').addEventListener('click',()=>{setMode('storyboard');$('causal-details').open=true;requestAnimationFrame(()=>$('causal-flow')?.scrollIntoView({behavior:'smooth'}));});
  $('read-tab').addEventListener('click',()=>setMode('read'));
  $('overview-tab').addEventListener('click',()=>{setMode('storyboard');window.scrollTo({top:0,behavior:'instant'});});
  document.querySelectorAll('[data-lang]').forEach(b=>b.addEventListener('click',()=>{lang=b.dataset.lang;updateURL();render();}));
  const get=async(base,name)=>{const r=await fetch(new URL(name,base),{cache:'no-store'});if(!r.ok)throw Error(`${name}: ${r.status}`);return r.json();};
  Promise.all([get(pack,'story-plan.json'),get(pack,'media.json'),get(pack,'causal-rhythm.json').catch(()=>({})),get(pack,'boards/manifest.json').catch(()=>({boards:[]})),get(new URL('../production/bath-magic-20261001-r12-house-layout/',location.href),'story-plan.json'),get(pack,'feedback-map.json').catch(()=>({})),get(upstream,'media.json')]).then(([p,m,c,b,o,e,om])=>{plan=p;media=m;causal=c;boards=b;before=o;edits=e;beforeMedia=om;render();if(location.hash)requestAnimationFrame(()=>document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView());}).catch(error=>{$('progress').textContent=error.message;$('progress').classList.add('error');});
})();
