import assert from 'node:assert/strict';
import {boundedJSONFetch,installCapabilities,executeBusinessRequest,PROTOCOL} from '../business-extension-contract.js';
const encoder=new TextEncoder();
let passed=0;
async function test(name,fn){await fn();passed++;console.log('PASS '+name);}
function response(chunks,headers={},status=200){return new Response(new ReadableStream({start(controller){for(const item of chunks)controller.enqueue(encoder.encode(item));controller.close();}}),{status,headers:{'Content-Type':'application/json',...headers}});}
await test('streamed bounded JSON result',async()=>assert.deepEqual(await boundedJSONFetch('/x',{},100,100,async()=>response(['{"ok":','true}'])),{ok:true}));
await test('oversized Content-Length refused before buffering',async()=>assert.rejects(()=>boundedJSONFetch('/x',{},10,100,async()=>response(['{}'],{'Content-Length':'100'}))));
await test('stream without Content-Length bounded incrementally',async()=>assert.rejects(()=>boundedJSONFetch('/x',{},10,100,async()=>response(['{"x":"','0123456789012','"}']))));
await test('non JSON MIME refused',async()=>assert.rejects(()=>boundedJSONFetch('/x',{},100,100,async()=>response(['{}'],{'Content-Type':'text/html'}))));
await test('malformed JSON refused',async()=>assert.rejects(()=>boundedJSONFetch('/x',{},100,100,async()=>response(['{']))));
await test('timeout aborts network and never retries',async()=>{let calls=0;await assert.rejects(()=>boundedJSONFetch('/x',{},100,10,async(path,opts)=>{calls++;return await new Promise((resolve,reject)=>opts.signal.addEventListener('abort',()=>reject(Error('aborted'))));}));assert.equal(calls,1);});
await test('redirects forbidden and cache disabled',async()=>{await boundedJSONFetch('/x',{},100,100,async(path,opts)=>{assert.equal(opts.redirect,'error');assert.equal(opts.cache,'no-store');return response(['{}']);});});
await test('server error status survives bounded parsing',async()=>{await assert.rejects(()=>boundedJSONFetch('/x',{},100,100,async()=>response(['{"error":{"message":"stale"}}'],{},409)),e=>e.status===409);});
await test('parent injects revision/hash/view headers itself',async()=>{const hash='a'.repeat(64),registry=installCapabilities({schemaVersion:1,protocol:PROTOCOL,businessHash:hash,operations:[{id:'draft.get.v1',effect:'read',method:'POST',maxRequestBytes:1048576,maxResponseBytes:100,timeoutMs:100,request:{type:'object',fields:{},required:[]}}]},hash);await executeBusinessRequest({path:'/api/business/draft.get.v1',options:{method:'POST',body:'{}'}},registry,{revision:3,readOnly:true},async(path,opts)=>{assert.equal(opts.headers['X-Studio-Business-Hash'],hash);assert.equal(opts.headers['X-Studio-Revision'],'3');assert.equal(opts.headers['X-Studio-Read-Only'],'true');return response(['{}']);});});
console.log(`${passed} transport tests passed`);
