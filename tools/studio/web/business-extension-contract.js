// New narrow versioned stable artifact; trusted parent installs server-pinned metadata.
export const PROTOCOL='pinpin-business-json-v1';
const installedRegistries=new WeakSet();
const HASH=/^[a-f0-9]{64}$/,OP=/^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$/;
const reserved=new Set(['conversation','runtime','transport','authority','kernel','agent','fleet','account','credentials','filesystem']);
const forbidden=new Set(['path','filepath','storagepath','url','endpoint','route','transport','credentials']);
const bytes=value=>new TextEncoder().encode(typeof value==='string'?value:JSON.stringify(value)).byteLength;
const plain=value=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&[Object.prototype,null].includes(Object.getPrototypeOf(value));
const integer=(n,min,max)=>Number.isSafeInteger(n)&&n>=min&&n<=max;
const deepFreeze=value=>{if(value&&typeof value==='object'){for(const item of Object.values(value))deepFreeze(item);Object.freeze(value);}return value;};
function schema(node,depth=0,budget={nodes:0}){
 if(!plain(node)||depth>8||++budget.nodes>256)throw Error('Invalid bounded capability schema.');
 const allowed={id:['type','maxLength'],hash:['type'],enum:['type','values'],text:['type','maxLength'],integer:['type','minimum','maximum'],number:['type','minimum','maximum'],boolean:['type'],array:['type','maxItems','items'],object:['type','fields','required']}[node.type];
 if(!allowed||Object.keys(node).some(k=>!allowed.includes(k)))throw Error('Unknown capability schema field.');
 if(['id','text'].includes(node.type)&&!integer(node.maxLength,1,node.type==='id'?160:16000))throw Error('Unbounded string schema.');
 if(node.type==='enum'&&(!Array.isArray(node.values)||!node.values.length||node.values.length>32||node.values.some(v=>typeof v!=='string'||v.length>160)))throw Error('Invalid enum schema.');
 if(['integer','number'].includes(node.type)&&(!Number.isFinite(node.minimum)||!Number.isFinite(node.maximum)||node.minimum>node.maximum||(node.type==='integer'&&(!Number.isSafeInteger(node.minimum)||!Number.isSafeInteger(node.maximum)))))throw Error('Invalid numeric schema.');
 if(node.type==='array'){if(!integer(node.maxItems,1,512))throw Error('Unbounded array schema.');schema(node.items,depth+1,budget);}
 if(node.type==='object'){
  if(!plain(node.fields)||Object.keys(node.fields).length>64||!Array.isArray(node.required)||node.required.length>64||new Set(node.required).size!==node.required.length||node.required.some(k=>typeof k!=='string'||!Object.hasOwn(node.fields,k)))throw Error('Invalid object schema.');
  for(const [key,value] of Object.entries(node.fields)){if(!/^[A-Za-z][A-Za-z0-9]{0,63}$/.test(key)||forbidden.has(key.toLowerCase())||['__proto__','constructor','prototype'].includes(key))throw Error('Forbidden request selector.');schema(value,depth+1,budget);}
 }
 return node;
}
function valueValid(node,value){
 switch(node.type){
  case 'id':return typeof value==='string'&&value.length<=node.maxLength&&/^[A-Za-z0-9_.-]+$/.test(value);
  case 'hash':return typeof value==='string'&&HASH.test(value);
  case 'enum':return node.values.includes(value);
  case 'text':return typeof value==='string'&&value.length<=node.maxLength;
  case 'integer':return Number.isSafeInteger(value)&&value>=node.minimum&&value<=node.maximum;
  case 'number':return typeof value==='number'&&Number.isFinite(value)&&value>=node.minimum&&value<=node.maximum;
  case 'boolean':return typeof value==='boolean';
  case 'array':return Array.isArray(value)&&value.length<=node.maxItems&&value.every(v=>valueValid(node.items,v));
  case 'object':return plain(value)&&Object.keys(value).every(k=>Object.hasOwn(node.fields,k))&&node.required.every(k=>Object.hasOwn(value,k))&&Object.entries(value).every(([k,v])=>valueValid(node.fields[k],v));
 }
 return false;
}
export function installCapabilities(metadata,activeBusinessHash){
 if(!plain(metadata)||metadata.protocol!==PROTOCOL||metadata.schemaVersion!==1||!HASH.test(activeBusinessHash||'')||metadata.businessHash!==activeBusinessHash||bytes(metadata)>65536||Object.keys(metadata).some(k=>!['protocol','schemaVersion','businessHash','operations'].includes(k))||!Array.isArray(metadata.operations)||metadata.operations.length>64)throw Error('Untrusted or invalid business capability metadata.');
 const operations=Object.create(null);
 for(const item of metadata.operations){
  if(!plain(item)||Object.keys(item).some(k=>!['id','effect','method','request','maxRequestBytes','maxResponseBytes','timeoutMs'].includes(k))||typeof item.id!=='string'||item.id.length>80||!OP.test(item.id)||reserved.has(item.id.split(/[.-]/)[0])||Object.hasOwn(operations,item.id)||!['read','mutation'].includes(item.effect)||item.method!=='POST'||!integer(item.maxRequestBytes,1,1024*1024)||!integer(item.maxResponseBytes,1,1024*1024)||!integer(item.timeoutMs,1,10000)||item.request?.type!=='object')throw Error('Invalid registered business operation.');
  schema(item.request);operations[item.id]=JSON.parse(JSON.stringify(item));
 }
 const registry=deepFreeze({protocol:PROTOCOL,businessHash:activeBusinessHash,operations});installedRegistries.add(registry);return registry;
}
export function businessRequest(path,options,canMutate,readOnly,registry){
 if(!registry||registry.protocol!==PROTOCOL||!installedRegistries.has(registry))throw Error('Business capability is unavailable.');
 const match=/^\/api\/business\/([a-z][a-z0-9]*(?:[.-][a-z0-9]+)*)$/.exec(path),operation=match&&registry.operations[match[1]];
 if(!operation||String(options.method||'GET').toUpperCase()!=='POST')throw Error('Unknown business capability/method.');
 if(operation.effect==='mutation'&&(canMutate!==true||readOnly!==false))throw Error(readOnly?'This review is read-only. Return to Live preview to edit.':'The preview is still opening.');
 if(Object.keys(options).some(k=>!['method','body'].includes(k))||typeof options.body!=='string'||bytes(options.body)>operation.maxRequestBytes)throw Error('Invalid bounded JSON capability body.');
 let body;try{body=JSON.parse(options.body);}catch{throw Error('Invalid JSON capability body.');}
 if(!valueValid(operation.request,body))throw Error('Capability body does not match its registered schema.');
 return {path,options:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}};
}
export function validateBusinessResponse(path,result,registry){
 if(!registry||!installedRegistries.has(registry))throw Error('Business capability is unavailable.');
 const match=/^\/api\/business\/([a-z][a-z0-9]*(?:[.-][a-z0-9]+)*)$/.exec(path);const operation=match&&registry.operations[match[1]];if(!operation)throw Error('Unknown business capability response.');
 const finite=(v,depth=0)=>depth<=16&&(v===null||typeof v==='string'||typeof v==='boolean'||(typeof v==='number'&&Number.isFinite(v))||(Array.isArray(v)&&v.every(x=>finite(x,depth+1)))||(plain(v)&&Object.values(v).every(x=>finite(x,depth+1))));
 if(!finite(result)||bytes(result)>operation.maxResponseBytes)throw Error('Invalid or oversized business response.');return result;
}

export async function boundedJSONFetch(path, options, maximum, timeoutMs, fetchImpl=fetch){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeoutMs);
 try{
  const response=await fetchImpl(path,{...options,signal:controller.signal,cache:'no-store',redirect:'error'});
  if(!(response.headers.get('Content-Type')||'').toLowerCase().startsWith('application/json'))throw Error('Expected a JSON business response.');
  const declared=response.headers.get('Content-Length');if(declared!==null&&(!/^\d+$/.test(declared)||Number(declared)>maximum))throw Error('Business response exceeds its limit.');
  if(!response.body?.getReader)throw Error('Streaming JSON response is required.');
  const reader=response.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let total=0,text='';
  try{while(true){const {done,value}=await reader.read();if(done)break;total+=value.byteLength;if(total>maximum)throw Error('Business response exceeds its limit.');text+=decoder.decode(value,{stream:true});}text+=decoder.decode();}
  catch(error){await reader.cancel().catch(()=>{});throw error;}
  const result=JSON.parse(text);if(!response.ok){const error=Error(String(result?.error?.message||'Business request failed.').slice(0,500));error.status=response.status;throw error;}return result;
 }finally{clearTimeout(timer);}
}
export async function fetchCapabilities(fetchImpl=fetch){
 const metadata=await boundedJSONFetch('/api/business/capabilities',{},65536,5000,fetchImpl);
 return installCapabilities(metadata,metadata.businessHash);
}
export async function executeBusinessRequest(action,registry,context,fetchImpl=fetch){
 if(!installedRegistries.has(registry))throw Error('Business capability is unavailable.');
 const operation=registry.operations[action.path.split('/').at(-1)];if(!operation)throw Error('Business capability is unavailable.');
 if(typeof context.readOnly!=='boolean'||!Number.isSafeInteger(context.revision)||context.revision<0)throw Error('Invalid workspace view context.');
 const checked=businessRequest(action.path,{method:action.options.method,body:action.options.body},context.canMutate===true,context.readOnly,registry);
 const result=await boundedJSONFetch(checked.path,{...checked.options,headers:{'Content-Type':'application/json','X-Studio-Business-Hash':registry.businessHash,'X-Studio-Revision':String(context.revision),'X-Studio-Read-Only':String(context.readOnly)}},operation.maxResponseBytes,operation.timeoutMs,fetchImpl);
 return validateBusinessResponse(action.path,result,registry);
}
