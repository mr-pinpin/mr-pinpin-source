const {chromium}=require('/Users/miguel_lemos/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=__dirname,output=path.join(root,'browser-check'),url='http://127.0.0.1:18796/storyboard/review/bath-magic-r6-corrections.html';
const data=JSON.parse(fs.readFileSync(path.join(root,'corrections.json')));
fs.mkdirSync(output,{recursive:true});
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});
const result={time:new Date().toISOString(),url,checks:[],errors:[],sourceHashes:{}};
for(const f of ['corrections.json','check-report.cjs'])result.sourceHashes[f]=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,f))).digest('hex');
const review='/Volumes/TB4/mac-mini-storage/shared/pinpin-workspace/mr-pinpin-source/docs/storyboard/review/';
for(const ext of ['html','css','js']){const f='bath-magic-r6-corrections.'+ext;result.sourceHashes['review/'+f]=crypto.createHash('sha256').update(fs.readFileSync(review+f)).digest('hex');}
try{
 assert.ok(data.rows.length>=6);assert.ok(data.rows.every(r=>r.original&&r.proposal));
 for(const width of [1440,390,320]){
 const page=await browser.newPage({viewport:{width,height:width===1440?1000:844}});
 page.on('pageerror',e=>result.errors.push(e.message));
 await page.goto(url+'?lang=en');await page.waitForSelector('.comparison');
 assert.equal(await page.locator('.comparison').count(),data.rows.length);
 await page.locator('.comparison img').evaluateAll(images=>Promise.all(images.map(async image=>{image.loading='eager';await image.decode();})));
 assert.equal(await page.locator('.comparison img').count(),data.rows.length*2);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.screenshot({path:path.join(output,'report-'+width+'.png')});
 await page.locator('.comparison').first().screenshot({path:path.join(output,'first-row-'+width+'.png')});
 for(const lang of ['ru','es','en']){await page.locator('[data-lang='+lang+']').click();assert.equal(await page.locator('html').getAttribute('lang'),lang);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
 await page.locator('#scene-links a').last().click();const bounds=await page.locator('.comparison').last().boundingBox();assert.ok(bounds.y<844);
 assert.ok((await page.locator('#previous').getAttribute('href')).includes('bath-magic-r5.html'));
 assert.equal(await page.locator('#production-content a').count(),data.documents.length);
 for(const href of await page.locator('#production-content a, .comparison details a').evaluateAll(a=>a.map(x=>x.href))){const response=await page.request.get(href);assert.ok(response.ok(),'Provenance link '+href);}
 result.checks.push({width,rows:data.rows.length,decodedImages:data.rows.length*2,languages:['en','ru','es'],noOverflow:true,provenanceLinks:data.documents.length});await page.close();
 }
 assert.deepEqual(result.errors,[]);result.passed=true;
}catch(e){result.passed=false;result.failure=e.stack;process.exitCode=1;}
finally{await browser.close();fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));}
})();
