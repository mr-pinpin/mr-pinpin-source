// Only the active sandbox gets mutation capabilities. Conversation and runtime controls never cross this bridge.
const ID='[A-Za-z0-9_.-]+';
const reads=[/^\/api\/state$/, /^\/api\/plan$/, /^\/api\/media$/, /^\/api\/insights$/, /^\/api\/assets$/, /^\/api\/jobs$/, /^\/api\/history$/, /^\/api\/history\/\d+$/];
const writes=[/^\/api\/plan\/approve$/, /^\/api\/jobs$/, /^\/api\/storyboards$/, /^\/api\/media\/import$/,new RegExp('^/api/jobs/'+ID+'/review$'),new RegExp('^/api/storyboards/'+ID+'/review$')];
export function validateRequest(path,options={},canMutate=false,readOnly=false){
 if(typeof path!=='string'||path.length>600||!path.startsWith('/api/')||path.includes('%')||path.includes('\\')||path.includes('#'))throw Error('This workspace request is not allowed.');
 const url=new URL(path,location.origin);if(url.origin!==location.origin)throw Error('External requests are not allowed.');
 const method=String(options.method||'GET').toUpperCase(),query=[...url.searchParams.keys()];
 if(method==='GET'){if(!reads.some(re=>re.test(url.pathname)))throw Error('This workspace API is not available.');const permitted=url.pathname==='/api/plan'?['chapterId']:url.pathname==='/api/state'?['revision']:[];if(query.some(key=>!permitted.includes(key)))throw Error('Unknown request parameters.');return{path:url.pathname+url.search,options:{}}}
 if(!canMutate||readOnly)throw Error(readOnly?'This review is read-only. Return to Live preview to edit.':'The preview is still opening.');
 if(query.length||!((method==='PUT'&&url.pathname==='/api/state')||(method==='POST'&&writes.some(re=>re.test(url.pathname)))))throw Error('This workspace action is not allowed.');
 if(typeof options.body!=='string'||options.body.length>8*1024*1024)throw Error('Use a JSON request body.');let body;try{body=JSON.parse(options.body)}catch{throw Error('Invalid JSON request.')}if(!body||Array.isArray(body)||typeof body!=='object')throw Error('Use a JSON object.');
 return{path:url.pathname,options:{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}};
}
