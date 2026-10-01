const {chromium}=require('/Users/miguel_lemos/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=__dirname,out=path.join(root,'browser-check'),url='http://127.0.0.1:18796/storyboard/review/bath-magic-r7-bath.html';
const data=JSON.parse(fs.readFileSync(path.join(root,'review.json')));
fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const result={time:new Date().toISOString(),checks:[],errors:[],sourceHashes:{}};
for(const f of ['review.json','story-discussion.json','twelve-mishaps-proposal.json','check-report.cjs'])result.sourceHashes[f]=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,f))).digest('hex');
const src='/Volumes/TB4/mac-mini-storage/shared/pinpin-workspace/mr-pinpin-source/docs/storyboard/review/';
for(const ext of ['html','css','js']){const f='bath-magic-r7-bath.'+ext;result.sourceHashes['review/'+f]=crypto.createHash('sha256').update(fs.readFileSync(src+f)).digest('hex');}
try{
for(const width of [1440,390,320]){const page=await browser.newPage({viewport:{width,height:width===1440?1000:844}});page.on('pageerror',e=>result.errors.push(e.message));await page.goto(url+'?lang=en');await page.waitForSelector('#mishaps li');assert.equal(await page.locator('#mishaps li').count(),12);assert.equal(await page.locator('#comparison img').count(),2);assert.equal(await page.locator('.pending').count(),0);
await page.locator('#comparison img').evaluateAll(images=>Promise.all(images.map(i=>i.decode())));assert.equal(await page.locator('#studies').getAttribute('open'),null);
await page.screenshot({path:path.join(out,'report-'+width+'.png')});
await page.locator('#bath').screenshot({path:path.join(out,'bath-'+width+'.png')});
for(const lang of ['ru','es','en']){await page.locator('[data-lang='+lang+']').click();assert.equal(await page.locator('html').getAttribute('lang'),lang);assert.equal(await page.locator('#mishaps li').count(),12);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
await page.locator('#story-link').click();assert.ok((await page.locator('#story').boundingBox()).y<844);await page.screenshot({path:path.join(out,'story-'+width+'.png')});
await page.locator('#studies-title').click();await page.locator('#study-pair img').evaluateAll(images=>Promise.all(images.map(i=>i.decode())));assert.equal(await page.locator('#study-pair img').count(),2);
assert.equal(await page.locator('#production-content a').count(),data.documents.length);for(const href of await page.locator('#production-content a').evaluateAll(a=>a.map(x=>x.href))){assert.ok((await page.request.get(href)).ok(),href);}
result.checks.push({width,comparisonImages:2,secondaryImages:2,numberedMishaps:12,languages:['en','ru','es'],provenanceLinks:data.documents.length,noOverflow:true});await page.close();}
assert.deepEqual(result.errors,[]);result.passed=true;
}catch(e){result.passed=false;result.failure=e.stack;process.exitCode=1;}
finally{await browser.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));}
})();
