const protocol='pinpin-workspace-v1';
const nonce=new URLSearchParams(location.hash.slice(1)).get('nonce');
let parentOrigin=null,serial=0;const pending=new Map();
export function send(type,payload={}){parent.postMessage({protocol,nonce,type,...payload},parentOrigin||'*');}
export function accept(event){const value=event.data;if(event.source!==parent||!value||value.protocol!==protocol||value.nonce!==nonce)return false;if(parentOrigin&&event.origin!==parentOrigin)return false;if(value.type==='init'&&!parentOrigin)parentOrigin=event.origin;return true;}
export function receiveResponse(value){if(value.type!=='response')return false;const call=pending.get(value.id);if(!call)return true;clearTimeout(call.timer);pending.delete(value.id);if(value.error){const error=new Error(typeof value.error==='string'?value.error:value.error.message||'Request failed');error.status=value.error.status;call.reject(error);}else call.resolve(value.result);return true;}
export function rpc(path,options={},type='request'){const id='workspace-'+(++serial);return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(id);reject(Error('The workspace request timed out. Your draft is preserved.'));},30000);pending.set(id,{resolve,reject,timer});send(type,{id,path,options});});}
export function close(){for(const value of pending.values()){clearTimeout(value.timer);value.reject(Error('Workspace closed'));}pending.clear();}
