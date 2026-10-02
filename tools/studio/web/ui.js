export const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const text = (v, lang='en') => Array.isArray(v) ? v.join('\n\n') : typeof v==='object' && v ? text(v[lang] ?? v.en ?? Object.values(v)[0] ?? '',lang) : String(v ?? '');
export const uid = prefix => `${prefix}-${crypto.randomUUID().slice(0,8)}`;
export const arr = v => Array.isArray(v) ? v : [];
export const date = v => v ? new Date(v).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '';
export function at(obj,path){return path.split('.').reduce((o,k)=>o?.[k],obj)}
export function put(obj,path,value){const p=path.split('.');const last=p.pop();let o=obj;for(const k of p){o[k]??={};o=o[k]}o[last]=value}
export function field(label,path,value,opts={}){
 const attrs=`aria-label="${esc(label)}" data-path="${esc(path)}" ${opts.list?'data-list="true"':''} ${opts.numeric?'data-number="true"':''}`;
 return `<label class="field ${opts.wide?'wide':''}"><span>${esc(label)}</span>${opts.area?`<textarea ${attrs} rows="${opts.rows||4}" placeholder="${esc(opts.placeholder||'')}">${esc(text(value))}</textarea>`:`<input ${attrs} type="${opts.numeric?'number':'text'}" value="${esc(text(value))}" placeholder="${esc(opts.placeholder||'')}" ${opts.readonly?'readonly':''}>`}${opts.help?`<small>${esc(opts.help)}</small>`:''}</label>`;
}
export function select(label,path,value,options,{multiple=false,empty=false}={}){
 return `<label class="field"><span>${esc(label)}</span><select aria-label="${esc(label)}" data-path="${esc(path)}" ${multiple?'multiple':''}>${empty?'<option value="">None</option>':''}${options.map(o=>`<option value="${esc(o.id)}" ${(multiple?arr(value).includes(o.id):value===o.id)?'selected':''}>${esc(o.name)}</option>`).join('')}</select>${multiple?'<small>Choose one or more. Hold ⌘ / Ctrl for several.</small>':''}</label>`;
}
export function chips(label,path,value,options,state){return `<fieldset class="chip-field"><legend>${esc(label)}</legend><div class="choice-chips">${options.map(o=>`<label><input type="checkbox" data-array-path="${esc(path)}" value="${esc(o.id)}" ${arr(value).includes(o.id)?'checked':''}>${o.referenceIds?.[0]?picture(state,o.referenceIds[0],o.name):''}<span>${esc(o.name)}</span></label>`).join('')||'<small>Add references to choose from.</small>'}</div></fieldset>`}
export const button=(label,action,id='',cls='')=>`<button type="button" class="${cls}" data-action="${esc(action)}" data-id="${esc(id)}">${esc(label)}</button>`;
export const empty=(title,detail)=>`<div class="empty"><span class="empty-mark">✧</span><h3>${esc(title)}</h3><p>${esc(detail)}</p></div>`;
export function asset(state,id){return arr(state.assets).find(x=>x.id===id)}
export function picture(state,id,alt='',cls=''){const a=asset(state,id);return a?`<img class="${cls}" src="${esc(a.url)}" alt="${esc(alt||a.name)}" loading="lazy">`:`<div class="image-placeholder ${cls}"><span>✧</span><small>Room for an illustration</small></div>`}
export function instruction(stage,chapterId=''){
 return `<section class="instruction panel"><div><span class="eyebrow">WORK WITH YOUR AGENT</span><h3>What should happen next?</h3><p>Write naturally. Your instruction and current references become a saved handoff.</p></div><form data-form="instruction"><input type="hidden" name="stage" value="${stage}"><input type="hidden" name="chapterId" value="${esc(chapterId)}"><label class="field"><span>Instruction</span><textarea name="instruction" rows="3" required placeholder="Describe the change, question, or next version you want…"></textarea></label><button class="primary">Queue instruction</button><small>Requests wait here until Codex picks them up. Publishing is a separate step.</small></form></section>`;
}
