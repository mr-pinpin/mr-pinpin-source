export const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const words=value=>Array.isArray(value)?value.join('\n'):typeof value==='object'&&value?value.en||value.ru||Object.values(value)[0]||'':String(value??'');
export const title=(value,lang='en')=>typeof value==='object'&&!Array.isArray(value)&&value?words(value[lang]||value.en||value.ru):words(value);
export async function request(path,options={}){const res=await fetch(path,options),data=await res.json();if(!res.ok){const error=new Error(data.error?.message||'Request failed ('+res.status+')');error.status=res.status;throw error}return data}
export const post=(path,body,method='POST')=>request(path,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
export const studio={state:null,chapterId:localStorage.getItem('pinpin-conversation-chapter'),lang:localStorage.getItem('pinpin-studio-language')||'ru',mode:'board',sceneIds:[],entityId:null,assetIds:[],conversation:null,pending:false,uploading:false,planOpen:false,planDrafts:new Map(),mediaCleanup:null};
export const chapter=()=>studio.state?.project.chapters.find(c=>c.id===studio.chapterId);
export const asset=id=>studio.state?.assets.find(a=>a.id===id);
export const caption=scene=>title(scene.captions,studio.lang)||scene.action||scene.title||'A moment waiting for words.';
export const active=()=>['connecting','running','interrupting'].includes(studio.conversation?.status);
export function notify(message){const n=document.querySelector('#notification');n.textContent=message;n.classList.add('visible');clearTimeout(notify.timer);notify.timer=setTimeout(()=>n.classList.remove('visible'),6500)}
export async function refresh(){studio.state=await request('/api/state'+(studio.route?.rev!==undefined?'?revision='+studio.route.rev:''));if(!chapter())studio.chapterId=studio.state.project.activeChapterId||studio.state.project.chapters.find(c=>c.scenes?.length)?.id||studio.state.project.chapters[0]?.id;return studio.state}
