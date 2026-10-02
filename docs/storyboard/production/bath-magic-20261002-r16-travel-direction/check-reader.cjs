const {chromium}=require('/Users/miguel_lemos/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const pack='/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261002-r16-travel-direction';
const media=JSON.parse(fs.readFileSync(path.join(pack,'media.json')));
(async()=>{const b=await chromium.launch({channel:'chrome',headless:true});const out={passed:false,checks:[],errors:[]};
try{for(const width of [1440,390]){const p=await b.newPage({viewport:{width,height:950}});p.on('pageerror',e=>out.errors.push(e.message));
await p.goto('http://127.0.0.1:18796/storyboard/review/bath-magic-r16-travel-direction.html?lang=ru#scene-32b');await p.waitForSelector('#scene-32b img');
assert.equal(await p.locator('.scene').count(),138);
for(const sid of ['scene-32b','scene-32c']){const i=p.locator('#'+sid+' img');await i.evaluate(i=>i.decode());assert((await i.getAttribute('src')).includes(media.images[sid].sha256.slice(0,12)));}
await p.locator('#scene-32b').scrollIntoViewIfNeeded();await p.screenshot({path:path.join(pack,'browser-check','travel-'+width+'.png')});
await p.locator('#changes-tab').click();assert.equal(await p.locator('.art-change').count(),1);assert.equal(await p.locator('.art-insertion').count(),0);assert.equal(await p.locator('.text-change').count(),0);
await p.locator('.art-change img').evaluateAll(a=>Promise.all(a.map(i=>i.decode())));await p.screenshot({path:path.join(pack,'browser-check','changes-'+width+'.png')});
assert(!(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
await p.locator('#overview-tab').click();assert.equal(await p.locator('.comic-sheet').count(),5);const sheet=p.locator('.comic-sheet').filter({has:p.locator('a[href="#scene-32b"]')});assert.equal(await sheet.count(),1);await sheet.locator('img').evaluate(i=>i.decode());
for(const lang of ['en','es']){await p.locator('[data-lang="'+lang+'"]').click();assert.equal(await p.locator('html').getAttribute('lang'),lang);assert.equal(await p.locator('.scene').count(),138);}
out.checks.push({width,scenes:138,travelAndNextImageDecoded:true,oneBeforeAfter:true,noTextOrInsertionChanges:true,affectedBoardDecoded:true,threeLanguages:true,noOverflow:true});await p.close();}
assert.equal(out.errors.length,0);out.passed=true;
}catch(e){out.failure=e.stack;process.exitCode=1}finally{await b.close();fs.writeFileSync(path.join(pack,'browser-check/results.json'),JSON.stringify(out,null,2));console.log(JSON.stringify(out))}})();
