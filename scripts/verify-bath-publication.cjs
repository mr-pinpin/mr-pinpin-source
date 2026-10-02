const {chromium}=require('/Users/miguel_lemos/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const base=new URL(process.argv[2]),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-webgpu']});const result={passed:false,readers:[],errors:[]};
try{
for(const width of [1440,390]){const page=await browser.newPage({viewport:{width,height:950}});page.on('pageerror',e=>result.errors.push(e.message));
for(const lang of ['ru','en','es']){
await page.goto(new URL('storyboard/?story=bath-magic&lang='+lang,base).href);await page.waitForSelector('article[data-story="bath-magic"] .scene');
assert.equal(await page.locator('article[data-story="bath-magic"] .scene').count(),139);assert.equal(await page.locator('.story-section-nav a').count(),4);
const imgs=await page.locator('article[data-story="bath-magic"] .scene-art img').evaluateAll(a=>Promise.all(a.map(async i=>{i.loading='eager';await i.decode();return i.naturalWidth;})));assert.equal(imgs.length,139);assert(imgs.every(Boolean));
assert.equal(await page.locator('html').getAttribute('lang'),lang);assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
for(const n of [1,2,3,4]){const a=page.locator('.story-section-nav a').nth(n-1);const href=await a.getAttribute('href');await a.click();await page.waitForFunction(selector=>{const top=document.querySelector(selector).getBoundingClientRect().top;return top>=-1&&top<innerHeight;},href,{timeout:5000});}
if(lang==='ru'){await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,'reader-'+width+'.png')});}
result.readers.push({width,lang,images:139,dayLinks:4,noOverflow:true});
}
await page.goto(new URL('storyboard/?story=home-sweet-home&lang=ru',base).href);await page.waitForSelector('article[data-story="home-sweet-home"]');assert.equal(await page.locator('.story-section-nav').count(),0);
await page.goto(new URL('storyboard/library.html?lang=ru',base).href);await page.waitForSelector('[data-download="bath-magic"]');assert(!(await page.locator('[data-download="bath-magic"]').isDisabled()));await page.locator('[data-story="bath-magic"] img').evaluate(i=>{i.loading='eager';return i.decode()});await page.screenshot({path:path.join(out,'library-'+width+'.png')});
await page.close();
}
const page=await browser.newPage({viewport:{width:1200,height:950}});page.on('pageerror',e=>result.errors.push(e.message));
await page.goto(new URL('storyboard/atlas-webgpu.html?lang=ru',base).href);await page.waitForFunction(()=>window.atlasGpuDebug&&window.AtlasStories,{timeout:60000});
await page.waitForFunction(async()=> (await window.AtlasStories.available()).has('home'));
await page.evaluate(()=>window.atlasGpuDebug.preview.show('home','ru',{available:'Открыть историю',unavailable:'Ошибка'},'index.html?story=home-sweet-home&lang=ru&returnTo=atlas-webgpu.html&returnPlace=home'));
await page.waitForSelector('#story-preview[open] .preview-related-story');assert((await page.locator('#preview-open').getAttribute('href')).includes('story=home-sweet-home'));const related=page.locator('.preview-related-story');assert((await related.getAttribute('href')).includes('story=bath-magic'));assert((await related.getAttribute('href')).includes('lang=ru'));await related.locator('img').evaluate(i=>i.decode());await page.screenshot({path:path.join(out,'home-stories.png')});await related.click();await page.waitForSelector('article[data-story="bath-magic"]');assert.equal(new URL(page.url()).searchParams.get('lang'),'ru');result.atlasHomeRelatedLink=true;await page.close();
assert.equal(result.errors.length,0);result.passed=true;
}catch(e){result.failure=e.stack;process.exitCode=1}finally{await browser.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));}})();
