import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
const helper=fs.existsSync(new URL('./draft-pdf-download.js',import.meta.url))?new URL('./draft-pdf-download.js',import.meta.url):new URL('../studio/web/workspace-dev/draft-pdf-download.js',import.meta.url);
const {pdfBlob}=await import(helper);
const hash=b=>createHash('sha256').update(b).digest('hex');
const data=Buffer.concat([Buffer.from('%PDF-transport-fixture\n'),Buffer.alloc(100000,97)]);
const selection={chapterId:'fixture',version:2,language:'ru',sourceVersionSHA256:'a'.repeat(64),artifactSHA256:hash(data)};
function rpc(change=x=>x,bytes=data){return async (path,options)=>{assert.equal(path,'/api/business/draft.pdf.chunk.v1');assert.equal(options.method,'POST');const offset=JSON.parse(options.body).offset,part=bytes.subarray(offset,offset+65536);return change({...selection,offset,totalBytes:bytes.length,bytes:part.length,base64:part.toString('base64'),chunkSHA256:hash(part),mime:'application/pdf',filename:'fixture-v2-ru.pdf',done:offset+part.length===bytes.length,unpublished:true});};}
let result=await pdfBlob(rpc(),selection);assert.equal(hash(Buffer.from(await result.blob.arrayBuffer())),hash(data));assert.equal(result.bytes,data.length);
await assert.rejects(pdfBlob(rpc(x=>({...x,chunkSHA256:'0'.repeat(64)})),selection),/integrity/);
await assert.rejects(pdfBlob(rpc(x=>({...x,totalBytes:65*1024*1024})),selection),/binding/);
await assert.rejects(pdfBlob(rpc(x=>({...x,sourceVersionSHA256:'b'.repeat(64)})),selection),/binding/);
await assert.rejects(pdfBlob(rpc(x=>({...x,done:true})),selection),/completion/);
await assert.rejects(pdfBlob(rpc(x=>({...x,filename:x.offset?'changed.pdf':x.filename})),selection),/Filename/);
const changed=Buffer.from(data);changed[50]^=1;await assert.rejects(pdfBlob(rpc(x=>x,changed),selection),/Whole PDF integrity/);
await assert.rejects(pdfBlob(rpc(x=>({...x,offset:1})),selection),/binding/);
console.log(JSON.stringify({passed:8,actualAppRequests:0,transportFixturesOnly:true}));
