(()=>{'use strict';
const pack=new URL('../production/bath-magic-20261001-r6-corrections/',location.href),$=id=>document.getElementById(id);
const words={
en:{title:'A closer look',status:'Correction proposals · For review',intro:'Original and proposed images, one scene at a time. The R5 chapter remains unchanged.',before:'Original · R5',after:'Proposed correction',pending:'Proposal in progress',image:'Image',back:'Chapter',production:'References and exact prompts',ready:'proposals ready',open:'Open full image'},
ru:{title:'Рассмотрим поближе',status:'Предложения исправлений · На рассмотрении',intro:'Исходное изображение и предложение для каждой сцены. Глава R5 остаётся без изменений.',before:'Исходное · R5',after:'Предлагаемое исправление',pending:'Предложение в работе',image:'Иллюстрация',back:'Глава',production:'Образцы и точные запросы',ready:'предложений готово',open:'Открыть изображение'},
es:{title:'Una mirada más cercana',status:'Correcciones propuestas · Para revisar',intro:'La imagen original y la propuesta para cada escena. El capítulo R5 sigue sin cambios.',before:'Original · R5',after:'Corrección propuesta',pending:'Propuesta en preparación',image:'Imagen',back:'Capítulo',production:'Referencias e instrucciones exactas',ready:'propuestas listas',open:'Abrir imagen completa'}};
let lang=new URLSearchParams(location.search).get('lang')||'en',data;if(!words[lang])lang='en';
function localized(value){return typeof value==='string'?value:(value?.[lang]||value?.en||'');}
function href(asset){const u=new URL(asset.path,pack);if(asset.sha256)u.searchParams.set('v',asset.sha256.slice(0,16));return u.href;}
function figure(asset,label,alt){const f=document.createElement('figure'),c=document.createElement('figcaption');c.textContent=label;f.append(c);
if(asset){const a=document.createElement('a');a.href=href(asset);a.target='_blank';a.rel='noopener';a.title=words[lang].open;const img=new Image();img.src=href(asset);img.alt=alt;img.width=asset.width;img.height=asset.height;img.loading='lazy';a.append(img);f.append(a);}else{const p=document.createElement('p');p.className='pending';p.textContent=words[lang].pending;f.append(p);}return f;}
function render(){if(!data)return;const w=words[lang];document.documentElement.lang=lang;document.title='PinPin · '+w.title;
for(const [id,text] of Object.entries({'title':w.title,'status-label':w.status,'intro':w.intro,'back-label':w.back,'production-title':w.production}))$(id).textContent=text;
$('previous').href='bath-magic-r5.html?lang='+lang;$('progress').textContent=data.rows.filter(r=>r.proposal).length+' / '+(data.expectedRows||data.rows.length)+' '+w.ready;
document.querySelectorAll('[data-lang]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.lang===lang)));
$('comparisons').replaceChildren();$('scene-links').replaceChildren();
for(const row of data.rows){const section=document.createElement('article');section.className='comparison';section.id=row.id;
const h=document.createElement('h2');h.textContent=w.image+' '+String(row.number).padStart(2,'0')+' · '+localized(row.title);const p=document.createElement('p');p.className='reason';p.textContent=localized(row.reason);
const pair=document.createElement('div');pair.className='pair';pair.append(figure(row.original,w.before,w.image+' '+row.number+' — '+w.before),figure(row.proposal,w.after,w.image+' '+row.number+' — '+w.after));if(row.laneEntry?.captionChanged){[row.laneEntry.existingParagraphs,row.laneEntry.proposedParagraphs].forEach((captions,index)=>{const box=document.createElement('div');box.className='caption-proposal';const lines=localized(captions);for(const line of Array.isArray(lines)?lines:[lines]){const paragraph=document.createElement('p');paragraph.textContent=line;box.append(paragraph);}pair.children[index].append(box);});}section.append(h,p,pair);const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent=w.production;details.append(summary);for(const doc of row.documents||[]){const a=document.createElement('a');a.href=new URL(doc.path,pack);a.textContent=localized(doc.title);a.target='_blank';a.rel='noopener';details.append(a);}section.append(details);$('comparisons').append(section);
const a=document.createElement('a');a.href='#'+row.id;a.textContent=String(row.number).padStart(2,'0');$('scene-links').append(a);}
document.querySelectorAll('#comparisons img').forEach((img,i)=>{if(i<2)img.loading='eager';});
$('production-content').replaceChildren();
for(const doc of data.documents||[]){const a=document.createElement('a');a.href=new URL(doc.path,pack);a.textContent=localized(doc.title);a.target='_blank';a.rel='noopener';$('production-content').append(a);}
const url=new URL(location.href);url.searchParams.set('lang',lang);history.replaceState(null,'',url);}
document.querySelectorAll('[data-lang]').forEach(button=>button.addEventListener('click',()=>{lang=button.dataset.lang;render();}));
fetch(new URL('corrections.json',pack),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error(r.status);return r.json();}).then(value=>{data=value;render();}).catch(e=>{$('progress').textContent=String(e);$('progress').className='error';});
})();