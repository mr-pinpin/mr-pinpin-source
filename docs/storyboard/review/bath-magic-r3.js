'use strict';
(() => {
  const pack = new URL('../production/bath-magic-20261001-r3/', location.href);
  const params = new URLSearchParams(location.search);
  let lang = ['en', 'ru', 'es'].includes(params.get('lang')) ? params.get('lang') : 'en';
  let mode = params.get('view') === 'storyboard' ? 'storyboard' : 'read';
  let plan, media;
  const $ = id => document.getElementById(id);
  const words = {
    en: {read:'Read', board:'Storyboard', draft:'Chapter draft · For review', made:'How this chapter was made', pending:'Illustration in progress', ready:(n,t)=>`${n} of ${t} illustrations ready`, complete:n=>`${n} illustrated scenes · Complete draft`, plan:'Story and camera plan', prompts:'Illustration prompts', refs:'Character and location references', report:'Review notes', sheet:'Storyboard sheet'},
    ru: {read:'Читать', board:'Раскадровка', draft:'Черновик главы · Для просмотра', made:'Как создавалась эта глава', pending:'Иллюстрация в работе', ready:(n,t)=>`Готово иллюстраций: ${n} из ${t}`, complete:n=>`${n} иллюстрированных сцен · Полный черновик`, plan:'История и план кадров', prompts:'Задания для иллюстраций', refs:'Образы героев и дома', report:'Заметки к просмотру', sheet:'Лист раскадровки'},
    es: {read:'Leer', board:'Storyboard', draft:'Borrador del capítulo · Para revisar', made:'Cómo se creó este capítulo', pending:'Ilustración en preparación', ready:(n,t)=>`${n} de ${t} ilustraciones listas`, complete:n=>`${n} escenas ilustradas · Borrador completo`, plan:'Historia y plan de cámara', prompts:'Instrucciones de ilustración', refs:'Referencias de personajes y lugares', report:'Notas de revisión', sheet:'Hoja del storyboard'}
  };
  const localized = value => typeof value === 'string' ? value : value?.[lang] ?? value?.en ?? '';
  const el = (name, className, text) => { const node = document.createElement(name); if(className) node.className=className; if(text !== undefined) node.textContent=text; return node; };
  const mediaURL = entry => {const url=new URL(typeof entry==='string'?entry:entry.path,pack);if(entry.sha256)url.searchParams.set('v',entry.sha256.slice(0,12));return url.href;};
  const asset = item => {
    const entry = media?.images?.[item.id];
    if(!entry) return null;
    return mediaURL(entry);
  };
  function illustration(item, eager=false) {
    const url = asset(item);
    if(!url) return el('p','pending',words[lang].pending);
    const img = el('img'); img.src=url; img.alt=localized(item.alt)||localized(item.title); img.loading=eager?'eager':'lazy'; img.decoding='async';
    const dimensions=media.images[item.id];if(dimensions.width && dimensions.height){img.width=dimensions.width;img.height=dimensions.height;}
    if(eager) img.fetchPriority='high';
    img.addEventListener('error',()=>{img.replaceWith(el('p','error',words[lang].pending));});
    return img;
  }
  function setMode(next, update=true) {
    mode=next;
    $('chapter').hidden=mode!=='read'; $('overview').hidden=mode!=='storyboard'; $('cover').hidden=mode!=='read';
    $('read-tab').setAttribute('aria-pressed',String(mode==='read')); $('overview-tab').setAttribute('aria-pressed',String(mode==='storyboard'));
    if(update) updateURL();
  }
  function updateURL() { const url=new URL(location.href); url.searchParams.set('lang',lang); if(mode==='storyboard') url.searchParams.set('view',mode); else url.searchParams.delete('view'); history.replaceState(null,'',url); }
  function render() {
    document.documentElement.lang=lang;
    const previous=document.querySelector('.previous-draft');previous.href=`bath-magic-r2.html?lang=${lang}`;previous.title=localized({en:'Previous draft',ru:'Предыдущий вариант',es:'Borrador anterior'});previous.setAttribute('aria-label',previous.title);
    const w=words[lang];
    $('chapter-title').textContent=localized(plan.title); document.title=`${localized(plan.title)} · ${w.draft}`;
    $('draft-label').textContent=w.draft; $('read-tab').textContent=w.read; $('overview-tab').textContent=w.board; $('production-title').textContent=w.made;
    document.querySelectorAll('[data-lang]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lang===lang)));
    const ready=plan.scenes.filter(s=>asset(s)).length;
    $('progress').textContent=ready===plan.scenes.length && asset(plan.cover) ? w.complete(ready) : w.ready(ready,plan.scenes.length);
    $('cover').replaceChildren(illustration(plan.cover,true));
    $('chapter').replaceChildren(); $('overview').replaceChildren();
    for(const scene of plan.scenes) {
      const article=el('article','scene'); article.id=scene.id;
      article.append(illustration(scene,scene.number===1));
      const text=el('div','scene-text'); text.append(el('span','scene-number',String(scene.number).padStart(2,'0')));
      const paragraphs=localized(scene.paragraphs); for(const p of Array.isArray(paragraphs)?paragraphs:[paragraphs]) text.append(el('p','',p));
      article.append(text); $('chapter').append(article);
    }
    for(const [i,sheet] of (media.storyboards||[]).entries()) {
      const figure=el('figure','board-sheet'); const img=el('img'); img.src=mediaURL(sheet); img.alt=sheet.kind==='overview'?localized({en:'Full chapter overview',ru:'Вся глава на одном листе',es:'Vista general del capítulo'}):`${w.sheet} ${sheet.number??i+1}`; img.loading='lazy';
      figure.append(img,el('figcaption','',img.alt)); $('overview').append(figure);
    }
    const grid=el('div','board-grid');
    for(const scene of plan.scenes) {
      const figure=el('figure','board-card'), button=el('button'); button.type='button'; button.append(illustration(scene));
      const caption=el('figcaption');caption.append(el('span','scene-number',String(scene.number).padStart(2,'0')),el('span','',localized(scene.title)));
      button.append(caption); button.addEventListener('click',()=>{setMode('read'); requestAnimationFrame(()=>$(scene.id).scrollIntoView({behavior:'smooth'}));}); figure.append(button); grid.append(figure);
    }
    $('overview').append(grid);
    const production=$('production-content'); production.replaceChildren();
    for(const [path,label] of [['story-plan.json',w.plan],...(media.documents||[]).map(x=>[x.path,x.title])]) {const a=el('a','',label); a.href=new URL(path,pack).href; a.target='_blank'; a.rel='noopener'; production.append(a);}
    if(media.concept) {
      const figure=el('figure','board-sheet'),img=el('img');img.src=mediaURL(media.concept);img.alt=localized({en:'Exploratory concept — not a chronological storyboard',ru:'Поисковый эскиз — не последовательная раскадровка',es:'Concepto exploratorio — no es un storyboard cronológico'});img.loading='lazy';figure.append(img,el('figcaption','',img.alt));production.append(figure);
    }
    for(const ref of media.references||[]) {const figure=el('figure','board-sheet'),img=el('img');img.src=mediaURL(ref);img.alt=localized(ref.title)||w.refs;img.loading='lazy';figure.append(img,el('figcaption','',localized(ref.title)||w.refs));production.append(figure);}
    const details=el('details'),summary=el('summary','',w.plan);details.append(summary,el('pre','',JSON.stringify(plan,null,2)));production.append(details);
    setMode(mode,false);
  }
  $('read-tab').addEventListener('click',()=>setMode('read'));
  $('overview-tab').addEventListener('click',()=>setMode('storyboard'));
  document.querySelectorAll('[data-lang]').forEach(b=>b.addEventListener('click',()=>{lang=b.dataset.lang;updateURL();render();}));
  Promise.all(['story-plan.json','media.json'].map(async name=>{const response=await fetch(new URL(name,pack),{cache:'no-store'});if(!response.ok)throw Error(`${name}: ${response.status}`);return response.json();})).then(([p,m])=>{plan=p;media=m;render();if(location.hash)requestAnimationFrame(()=>document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView());}).catch(error=>{$('progress').textContent=error.message;$('progress').classList.add('error');});
})();
