import {model} from './store.js';
import {esc,text,picture,button} from './ui.js';

export function publishedURL(chapter){
 try{const url=new URL(chapter.publicURL);if(!['https:','http:'].includes(url.protocol))return '';url.searchParams.set('lang',model.lang);return url.href}catch{return ''}
}
export function publishedLink(chapter,label='Open published chapter',cls=''){
 const url=publishedURL(chapter);
 return url?`<a class="link-button ${cls}" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)} ↗</a>`:'';
}
export function renderPublished(chapter){
 return `<section class="panel published-reference" data-published-reference="${esc(chapter.id)}"><div class="published-cover">${picture(model.server,chapter.coverAssetId,text(chapter.title,model.lang))}</div><div class="stack"><span class="eyebrow">PUBLISHED REFERENCE</span><h2>${esc(text(chapter.title,model.lang))}</h2><p>The full text and artwork are available in the published reader. This catalog entry has not been imported as an editable draft.</p><div class="row">${publishedLink(chapter)}${button('Start a new chapter','new-chapter')}</div><p class="muted">Choose your working draft above to continue editing it.</p></div></section>`;
}
