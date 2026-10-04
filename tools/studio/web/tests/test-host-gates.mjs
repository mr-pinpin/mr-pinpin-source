import fs from 'node:fs';
import assert from 'node:assert/strict';
import {validateRequest} from '../shell-bridge.js';
import {installCapabilities,PROTOCOL} from '../business-extension-contract.js';
globalThis.location={origin:'http://127.0.0.1:18826'};
const source=fs.readFileSync(new URL('../shell-frame-host.js',import.meta.url),'utf8');
const code=source.slice(source.indexOf(' async function receive(event)'),source.indexOf(" window.addEventListener('message',receive);"));
const hash='a'.repeat(64),metadata={schemaVersion:1,protocol:PROTOCOL,businessHash:hash,operations:[{id:'draft.get.v1',effect:'read',method:'POST',request:{type:'object',fields:{},required:[]},maxRequestBytes:100,maxResponseBytes:100,timeoutMs:100},{id:'draft.patch.v1',effect:'mutation',method:'POST',request:{type:'object',fields:{},required:[]},maxRequestBytes:100,maxResponseBytes:100,timeoutMs:100}]};
let passes=0;
async function test(name,fn){await fn();passes++;console.log('PASS '+name);}
function harness(readOnly=false){const calls=[],sent=[],frame={nonce:'nonce',element:{contentWindow:{}}},candidate={nonce:'candidate',element:{contentWindow:{}}};const studio={state:{readOnly,revision:1,assets:[]},route:{}};
 const receive=new Function('active','pending','studio','protocol','validateRequest','fetchCapabilities','executeBusinessRequest','tell','reloadState','request',code+'; return receive;')(frame,candidate,studio,'pinpin-workspace-v1',validateRequest,async()=>{calls.push('metadata');return installCapabilities(metadata,hash);},async()=>{calls.push('execute');return{};},(frame,type,value)=>sent.push(value),async()=>calls.push('reload'),async()=>{calls.push('legacy');return{};});
 const event=(patch={})=>({origin:'null',source:frame.element.contentWindow,data:{protocol:'pinpin-workspace-v1',nonce:'nonce',type:'request',id:'id',path:'/api/business/draft.get.v1',options:{method:'POST',body:'{}'}},...patch});return{calls,sent,frame,candidate,event,receive};}
await test('non-null origin blocked before any HTTP',async()=>{const h=harness();await h.receive(h.event({origin:location.origin}));assert.deepEqual(h.calls,[]);});
await test('wrong source blocked before any HTTP',async()=>{const h=harness();await h.receive(h.event({source:{}}));assert.deepEqual(h.calls,[]);});
await test('wrong nonce blocked before any HTTP',async()=>{const h=harness(),e=h.event();e.data.nonce='wrong';await h.receive(e);assert.deepEqual(h.calls,[]);});
await test('wrong protocol blocked before any HTTP',async()=>{const h=harness(),e=h.event();e.data.protocol='other';await h.receive(e);assert.deepEqual(h.calls,[]);});
await test('registered read does not reload project state',async()=>{const h=harness(true);await h.receive(h.event());assert.deepEqual(h.calls,['metadata','execute']);});
await test('historical mutation denied by real host receive branch',async()=>{const h=harness(true),e=h.event();e.data.path='/api/business/draft.patch.v1';await h.receive(e);assert.deepEqual(h.calls,['metadata']);assert.ok(h.sent[0].error);});
await test('pending frame mutation denied',async()=>{const h=harness(),e=h.event({source:h.candidate.element.contentWindow});e.data.nonce='candidate';e.data.path='/api/business/draft.patch.v1';await h.receive(e);assert.deepEqual(h.calls,['metadata']);assert.ok(h.sent[0].error);});
await test('active mutation executes and refreshes state',async()=>{const h=harness(),e=h.event();e.data.path='/api/business/draft.patch.v1';await h.receive(e);assert.deepEqual(h.calls,['metadata','execute','reload']);});
await test('child-provided capability metadata ignored',async()=>{const h=harness(),e=h.event();e.data.capabilities={operations:[{id:'runtime.restart'}]};e.data.path='/api/business/runtime.restart';await h.receive(e);assert.deepEqual(h.calls,['metadata']);assert.ok(h.sent[0].error);});
console.log(`${passes} host gate tests passed`);
