'use strict';
// Browser evidence for cover navigation, deferred image requests, and complete print preparation.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.PINPIN_READER_BASE||'http://127.0.0.1:18812/';
const out=path.resolve(process.argv[2]||'');
const root=path.resolve(__dirname,'..');
if(!process.argv[2]||out===root||out.startsWith(root+path.sep))throw Error('Pass an external evidence directory');
fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({headless:true});const evidence=[];
try{for(const width of [390,1440])for(const lang of ['en','ru','es']){
 const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage();let pdfRequests=0;const errors=[];
 context.on('request',r=>{if(r.url().includes('huggingface.co'))pdfRequests++});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(new URL('storyboard/library.html?lang='+lang,base).href);await page.waitForSelector('[data-read="scooby-bath"]');
 await page.locator('#chapter-search').fill('Scooby');if(lang==='ru')await page.locator('#chapter-search').fill('Скуби');
 const cover=page.locator('[data-read="scooby-bath"]');assert.equal(await cover.getAttribute('target'),'_blank');assert.equal(await cover.getAttribute('rel'),'noopener');assert.equal(await page.locator('[data-download="scooby-bath"]').count(),1);
 const pending=context.waitForEvent('page');await cover.click();const reader=await pending;reader.on('pageerror',e=>errors.push(e.message));const requested=[];reader.on('request',r=>{if(/\/images\//.test(r.url()))requested.push(r.url())});
 await reader.waitForSelector('#reader article');await reader.locator('.scene-art img').first().evaluate(i=>i.decode());await reader.waitForTimeout(250);
 assert.equal(new URL(reader.url()).searchParams.get('story'),'scooby-bath');assert.equal(new URL(reader.url()).searchParams.get('lang'),lang);assert.equal(pdfRequests,0,'Reading never requests PDF storage');
 const initial=await reader.evaluate(()=>({pages:document.querySelectorAll('.scene').length,started:[...document.querySelectorAll('.scene-art img')].filter(i=>i.hasAttribute('src')).length,deferred:document.querySelectorAll('.scene-art img[data-src]').length,overflow:document.documentElement.scrollWidth>innerWidth}));
 assert(initial.pages>=26);assert(initial.started<=6,JSON.stringify(initial));assert(initial.deferred>initial.pages/2);assert(!initial.overflow);
 const last=reader.locator('.scene').last();await last.scrollIntoViewIfNeeded();await reader.waitForFunction(()=>{const i=[...document.querySelectorAll('.scene-art img')].at(-1);return i?.hasAttribute('src')});
 await last.locator('img').evaluate(i=>i.decode());assert.equal(await last.locator('img').evaluate(i=>i.naturalWidth),1536);
 const afterJump=await reader.locator('.scene-art img[data-src]').count();assert(afterJump>initial.pages/2,'Jumping to end does not fetch intervening pages');
 await reader.evaluate(()=>window.prepareChapterPrint());const full=await reader.evaluate(()=>({pending:document.querySelectorAll('.scene-art img[data-src]').length,broken:[...document.querySelectorAll('.scene-art img')].filter(i=>!i.complete||!i.naturalWidth).length}));assert.deepEqual(full,{pending:0,broken:0});assert.deepEqual(errors,[]);
 const readingPDFRequests=pdfRequests; let downloadVerified=false;
 if(width===390&&lang==='en'){await page.screenshot({path:path.join(out,'library-mobile.png')});const expected=await page.evaluate(async()=>{const c=await (await fetch('library-pdfs.json')).json();return c.chapters.find(x=>x.id==='scooby-bath').pdf.en});const pendingDownload=page.waitForEvent('download',{timeout:120000});await page.locator('[data-download="scooby-bath"]').click();const download=await pendingDownload;assert.equal(await download.failure(),null);const bytes=fs.readFileSync(await download.path());assert.equal(bytes.length,expected.bytes);assert.equal(require('node:crypto').createHash('sha256').update(bytes).digest('hex'),expected.sha256);downloadVerified=true;}
 evidence.push({width,lang,...initial,deferredAfterJump:afterJump,print:full,readingPDFRequests,downloadVerified});await context.close();
}
const fallback=await browser.newPage({viewport:{width:390,height:900}});await fallback.addInitScript(()=>delete window.IntersectionObserver);await fallback.goto(new URL('storyboard/?story=scooby-bath&lang=en',base).href);await fallback.waitForSelector('#reader article');await fallback.waitForFunction(()=>document.querySelectorAll('.scene-art img[data-src]').length===0);await fallback.locator('.scene-art img').first().evaluate(i=>i.decode());await fallback.close();
fs.writeFileSync(path.join(out,'reading-proof.json'),JSON.stringify({base,evidence,nativeLazyFallback:true},null,2)+'\n');console.log(JSON.stringify(evidence));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
