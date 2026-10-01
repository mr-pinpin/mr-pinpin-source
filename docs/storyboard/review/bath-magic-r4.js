'use strict';
(() => {
  const pack=new URL('../production/bath-magic-20261001-r4/',location.href);
  const previousPack=new URL('../production/bath-magic-20261001-r3/',location.href);
  const params=new URLSearchParams(location.search);
  let lang=['en','ru','es'].includes(params.get('lang'))?params.get('lang'):'en';
  let plan,media,previous;
  const $=id=>document.getElementById(id);
  const words={
    en:{toolbar:'Story proposal',stage:'Preproduction · For discussion',note:'A proposed story across four days. The new duck design is a character study; the scene illustrations have not been made for this version. Older pictures, where offered, are references only.',count:n=>`${n} proposed scenes · Four days`,day:'Day',study:'The new yellow bath duck',studyNote:'Character study for review: a soft yellow plastic bath toy. This is a design reference, not a finished chapter scene.',studyPending:'The new duck design is being prepared.',time:'Time',emotion:'Emotional beat',camera:'Camera',older:'Previous artwork · Reference only',olderNote:'From the previous illustrated draft. This image is not a finished R4 illustration or a promise to reuse it unchanged.',production:'Production references and exact prompts',previous:'Previous illustrated draft'},
    ru:{toolbar:'План истории',stage:'Подготовка · Для обсуждения',note:'Предлагаемая история охватывает четыре дня. Новый образ уточки — эскиз персонажа; иллюстрации сцен для этой версии ещё не созданы. Старые рисунки показаны только как ориентиры.',count:n=>`${n} сцен в плане · Четыре дня`,day:'День',study:'Новая жёлтая уточка для ванны',studyNote:'Эскиз для обсуждения: мягкая жёлтая пластиковая игрушка для ванны. Это образ персонажа, а не готовая иллюстрация главы.',studyPending:'Новый образ уточки готовится.',time:'Время',emotion:'Настроение',camera:'Камера',older:'Старый рисунок · Только ориентир',olderNote:'Из предыдущего иллюстрированного варианта. Это не готовая иллюстрация R4 и не обещание использовать её без изменений.',production:'Материалы и точные задания для иллюстраций',previous:'Предыдущий иллюстрированный вариант'},
    es:{toolbar:'Propuesta de historia',stage:'Preproducción · Para conversar',note:'Una propuesta que transcurre a lo largo de cuatro días. El nuevo pato es un estudio de personaje; las ilustraciones de las escenas de esta versión aún no se han creado. Las imágenes anteriores son solo referencias.',count:n=>`${n} escenas propuestas · Cuatro días`,day:'Día',study:'El nuevo patito amarillo de baño',studyNote:'Estudio de personaje para revisar: un juguete de baño de plástico amarillo y blando. Es una referencia de diseño, no una escena terminada del capítulo.',studyPending:'Se está preparando el nuevo diseño del pato.',time:'Momento',emotion:'Emoción',camera:'Cámara',older:'Ilustración anterior · Solo referencia',olderNote:'Del borrador ilustrado anterior. No es una ilustración terminada de R4 ni una promesa de reutilizarla sin cambios.',production:'Referencias de producción e instrucciones exactas',previous:'Borrador ilustrado anterior'}
  };
  const localized=value=>typeof value==='string'||typeof value==='number'?String(value):value?.[lang]??value?.en??'';
  const node=(tag,className,text)=>{const n=document.createElement(tag);if(className)n.className=className;if(text!==undefined)n.textContent=text;return n;};
  const url=(item,base=pack)=>{const u=new URL(item.path,base);if(item.sha256)u.searchParams.set('v',item.sha256.slice(0,12));return u.href;};
  const describe=value=>{const text=localized(value);if(text)return text;if(Array.isArray(value))return value.map(describe).filter(Boolean).join(' · ');if(value&&typeof value==='object')return Object.entries(value).map(([k,v])=>`${k}: ${describe(v)}`).join(' · ');return '';};
  function image(item,base=pack){const img=node('img');img.src=url(item,base);img.alt=words[lang].study;img.loading='lazy';img.decoding='async';if(item.width){img.width=item.width;img.height=item.height;}return img;}
  function render(){
    const w=words[lang];document.documentElement.lang=lang;document.title=`${localized(plan.title)} · ${w.toolbar}`;
    $('toolbar-title').textContent=w.toolbar;$('draft-label').textContent=w.stage;$('chapter-title').textContent=localized(plan.title);$('progress').textContent=w.count(plan.scenes.length);$('stage-note').textContent=w.note;
    const back=document.querySelector('.previous-draft');back.href=`bath-magic-r3.html?lang=${lang}`;back.title=w.previous;back.setAttribute('aria-label',w.previous);
    document.querySelectorAll('[data-lang]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lang===lang)));
    const study=$('duck-study');study.replaceChildren(node('h2','',w.study));
    if(media.studies?.length){for(const entry of media.studies){const figure=node('figure');const img=image(entry);img.loading='eager';img.fetchPriority='high';figure.append(img,node('figcaption','',w.studyNote));study.append(figure);}}
    else study.append(node('p','study-pending',w.studyPending));
    $('day-links').replaceChildren();$('chapter').replaceChildren();
    const days=[...new Set(plan.scenes.map(s=>Number(s.day)))].sort((a,b)=>a-b);
    for(const day of days){
      const section=node('section','day');section.id=`day-${day}`;const header=node('header','day-heading');header.append(node('h2','',`${w.day} ${day}`));
      const group=plan.scenes.filter(s=>Number(s.day)===day);header.append(node('p','',`${String(group[0].number).padStart(2,'0')}–${String(group.at(-1).number).padStart(2,'0')}`));section.append(header);
      const link=node('a','',`${w.day} ${day}`);link.href=`#day-${day}`;$('day-links').append(link);
      for(const scene of group){
        const article=node('article','scene');article.id=scene.id;article.append(node('span','scene-number',String(scene.number).padStart(2,'0')),node('h3','',localized(scene.title)));
        const text=node('div','scene-text');const paragraphs=localized(scene.paragraphs);for(const p of Array.isArray(paragraphs)?paragraphs:[paragraphs])text.append(node('p','',p));article.append(text);
        const notes=node('div','scene-notes');for(const [label,value] of [[w.time,scene.timeOfDay],[w.emotion,scene.emotionalBeat],[w.camera,scene.camera]]){const content=describe(value);if(content)notes.append(node('p','',`${label}: ${content}`));}article.append(notes);
        const candidates=Array.isArray(scene.r3Candidate)?scene.r3Candidate:scene.r3Candidate?[scene.r3Candidate]:[];
        const valid=candidates.map(id=>({id,entry:previous.images?.[id]})).filter(x=>x.entry);
        if(valid.length){const details=node('details','old-art');details.append(node('summary','',w.older),node('p','',w.olderNote));for(const {id,entry} of valid){const figure=node('figure');const img=image(entry,previousPack);img.alt=`${w.older}: ${id}`;figure.append(img,node('figcaption','',`R3 · ${id} · ${w.older}`));details.append(figure);}article.append(details);}
        section.append(article);
      }
      $('chapter').append(section);
    }
    $('production-title').textContent=w.production;const content=$('production-content');content.replaceChildren();for(const entry of media.documents||[]){const a=node('a','',entry.title);a.href=new URL(entry.path,pack).href;a.target='_blank';a.rel='noopener';content.append(a);}
  }
  document.querySelectorAll('[data-lang]').forEach(b=>b.addEventListener('click',()=>{lang=b.dataset.lang;const u=new URL(location.href);u.searchParams.set('lang',lang);history.replaceState(null,'',u);render();}));
  const readJSON=async resource=>{const response=await fetch(resource,{cache:'no-store'});if(!response.ok)throw Error(`Cannot open ${response.url}`);return response.json();};
  Promise.all([readJSON(new URL('story-plan.json',pack)),readJSON(new URL('media.json',pack)),readJSON(new URL('media.json',previousPack)).catch(()=>({images:{}}))]).then(([p,m,old])=>{plan=p;media=m;previous=old;render();}).catch(error=>{$('progress').textContent=error.message;$('progress').className='error';});
})();
