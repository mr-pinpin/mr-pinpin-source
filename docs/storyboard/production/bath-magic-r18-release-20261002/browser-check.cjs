const {chromium}=require('/Users/miguel_lemos/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const base=process.argv[2],out=process.argv[3],withPdf=process.argv.includes('--pdf');
fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true,downloadsPath:path.join(out,'downloads')});const result={readers:[],errors:[]};
try{
for(const lang of ['ru','en','es']){
 const page=await browser.newPage({viewport:{width:390,height:844}});page.on('pageerror',e=>result.errors.push(e.message));
 await page.goto(new URL('storyboard/?story=bath-magic&lang='+lang,base).href);await page.waitForSelector('article[data-story="bath-magic"] .scene');
 assert.equal(await page.locator('article[data-story="bath-magic"] .scene').count(),173);
 const cover=page.locator('article[data-story="bath-magic"] .scene-art img').first();
 await page.locator('.scene-art img').evaluateAll(async imgs=>{await Promise.all(imgs.map(i=>{i.loading='eager';return i.decode()}))}); await cover.evaluate(i=>i.decode());const data=await cover.evaluate(i=>({src:i.getAttribute('src'),width:i.naturalWidth,height:i.naturalHeight}));
 assert(data.src.endsWith('title-'+lang+'-v2.webp'));assert.equal(data.width,1024);assert.equal(data.height,1536);
 assert.equal(await page.locator('.story-section-nav a').count(),4);
 await page.screenshot({path:path.join(out,'reader-'+lang+'.png')});
 await page.goto(new URL('storyboard/library.html?lang='+lang,base).href);await page.waitForSelector('[data-download="bath-magic"]');
 const tile=page.locator('[data-story="bath-magic"] img');await tile.evaluate(i=>{i.loading='eager';return i.decode()});assert((await tile.getAttribute('src')).endsWith('bath-magic/miniature.webp'));
 result.readers.push({lang,cover:data,scenes:173,libraryMiniatureUnchanged:true});await page.close();
}
if(withPdf){
 const page=await browser.newPage();const url=new URL('storyboard/?story=bath-magic&lang=ru&download=pdf',base).href;
 const waiting=page.waitForEvent('download',{timeout:180000});await page.goto(url);const download=await waiting;const save=path.join(out,'bath-magic-ru.pdf');await download.saveAs(save);
 const catalog=await (await page.request.get(new URL('storyboard/library-pdfs.json',base).href)).json();const expected=catalog.chapters.find(e=>e.id==='bath-magic').pdf.ru;
 const bytes=fs.readFileSync(save);const sha=crypto.createHash('sha256').update(bytes).digest('hex');assert.equal(sha,expected.sha256);assert.equal(bytes.length,expected.bytes);
 assert.equal(await page.locator('article[data-story="bath-magic"]').count(),0);
 result.pdf={lang:'ru',filename:download.suggestedFilename(),bytes:bytes.length,sha256:sha,readerSuppressed:true};await page.close();
}
assert.equal(result.errors.length,0);result.pass=true;
}catch(e){result.error=e.stack;process.exitCode=1}finally{await browser.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));}})();
