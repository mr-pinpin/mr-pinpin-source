// New reloadable UI helper. Caller supplies existing request RPC; no direct fetch.
const MAX=64*1024*1024,CHUNK=64*1024;
const hex=bytes=>[...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,'0')).join('');
async function sha(bytes){return hex(await crypto.subtle.digest('SHA-256',bytes));}
export async function pdfBlob(rpc,selection){
 if(!selection||!Number.isSafeInteger(selection.version)||selection.version<1||!['en','ru'].includes(selection.language)||![selection.sourceVersionSHA256,selection.artifactSHA256].every(h=>/^[a-f0-9]{64}$/.test(h)))throw Error('Require exact saved version and artifact identity');
 const chunks=[];let offset=0,total=null,filename=null;
 while(true){
  // New named capability; intentionally unavailable until reviewed bridge canary.
  const part=await rpc('/api/business/draft.pdf.chunk.v1',{method:'POST',body:JSON.stringify({...selection,offset})});
  if(part.unpublished!==true||part.mime!=='application/pdf'||part.offset!==offset||!Number.isSafeInteger(part.totalBytes)||part.totalBytes<1||part.totalBytes>MAX||part.chapterId!==selection.chapterId||part.version!==selection.version||part.language!==selection.language||part.sourceVersionSHA256!==selection.sourceVersionSHA256||part.artifactSHA256!==selection.artifactSHA256)throw Error('Delivery binding mismatch');
  if(total!==null&&part.totalBytes!==total)throw Error('PDF changed between chunks');total=part.totalBytes;
  if(typeof part.base64!=='string'||part.base64.length>4*Math.ceil(CHUNK/3)||typeof part.chunkSHA256!=='string'||!/^[a-f0-9]{64}$/.test(part.chunkSHA256))throw Error('Invalid bounded PDF chunk');
  const decoded=atob(part.base64),bytes=Uint8Array.from(decoded,c=>c.charCodeAt(0));if(!bytes.length||bytes.length>CHUNK||bytes.length!==part.bytes||offset+bytes.length>total||await sha(bytes)!==part.chunkSHA256)throw Error('PDF chunk integrity failure');
  const done=offset+bytes.length===total;if(part.done!==done||(!done&&bytes.length!==CHUNK))throw Error('Invalid PDF completion');
  if(typeof part.filename!=='string'||!/^[A-Za-z0-9_.-]{1,100}\.pdf$/.test(part.filename))throw Error('Invalid download filename');if(filename&&filename!==part.filename)throw Error('Filename changed between chunks');filename=part.filename;
  chunks.push(bytes);offset+=bytes.length;if(done)break;
 }
 const blob=new Blob(chunks,{type:'application/pdf'}),full=await blob.arrayBuffer();if(blob.size!==total||await sha(full)!==selection.artifactSHA256||new TextDecoder().decode(full.slice(0,5))!=='%PDF-')throw Error('Whole PDF integrity failure');return{blob,filename,sha256:selection.artifactSHA256,bytes:total,unpublished:true};
}
export async function downloadPDF(rpc,selection){const result=await pdfBlob(rpc,selection),url=URL.createObjectURL(result.blob),a=document.createElement('a');a.href=url;a.download=result.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);return{filename:result.filename,sha256:result.sha256,bytes:result.bytes,unpublished:true};}
