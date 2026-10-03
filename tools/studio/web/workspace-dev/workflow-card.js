import {esc,asset} from './child-state.js';

// Declarative data only: buttons prepare a message for the user's review.
export function renderWorkflowText(text){
 const pattern=/```ui\s*\n([\s\S]*?)```/g;
 let html='',position=0;
 for(const match of text.matchAll(pattern)){
  html+=esc(text.slice(position,match.index));position=match.index+match[0].length;
  let card;try{card=JSON.parse(match[1]);}catch{html+=esc(match[0]);continue;}
  if(card?.type!=='WorkflowCard'||typeof card.title!=='string'||!Array.isArray(card.actions)||card.actions.length>6){html+=esc(match[0]);continue;}
  const actions=card.actions.filter(a=>typeof a?.label==='string'&&typeof a.message==='string'&&a.message.length<=4000);
  const images=(Array.isArray(card.assetIds)?card.assetIds:[]).slice(0,4).map(id=>asset(id)).filter(Boolean);
  html+=`<section class="workflow-card"><strong>${esc(card.title)}</strong><p>${esc(typeof card.text==='string'?card.text:'')}</p>${images.map(a=>`<button type="button" class="workflow-image-open" data-open-asset="${esc(a.id)}" aria-label="Open full-size: ${esc(a.name)}"><img data-asset-src="${esc(a.url)}" alt="${esc(a.name)}"><span>Open full-size</span></button>`).join('')}${actions.length?`<div class="workflow-actions">${actions.map(a=>`<button type="button" data-prompt="${esc(a.message)}">${esc(a.label)}</button>`).join('')}</div><small>Choose an option, then send the prepared message.</small>`:''}</section>`;
 }
 return html+esc(text.slice(position));
}
