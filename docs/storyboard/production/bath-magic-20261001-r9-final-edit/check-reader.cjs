
const {chromium}=require('/Users/miguel_lemos/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const pack='/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r9-final-edit';
const root='/Volumes/TB4/mac-mini-storage/shared/pinpin-workspace/mr-pinpin-source';
const plan=JSON.parse(fs.readFileSync(path.join(pack,'story-plan.json')));
const old=JSON.parse(fs.readFileSync('/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261001-r8-herculean/story-plan.json'));
const out={passed:false,checks:[],errors:[],sourceHashes:{}};
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});
try{
for(const f of ['story-plan.json','causal-rhythm.json','editorial-changes.json','boards/manifest.json'])out.sourceHashes[f]=crypto.createHash('sha256').update(fs.readFileSync(path.join(pack,f))).digest('hex');
for(const ext of ['html','css','js']){const f='docs/storyboard/review/bath-magic-r9-final-edit.'+ext;out.sourceHashes[f]=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,f))).digest('hex')}
for(const width of [1440,390]){
 const p=await browser.newPage({viewport:{width,height:950}});p.on('pageerror',e=>out.errors.push(e.message));
 await p.goto('http://127.0.0.1:18796/storyboard/review/bath-magic-r9-final-edit.html');
 await p.waitForSelector('.scene');assert.equal(await p.locator('html').getAttribute('lang'),'ru');assert.equal(await p.locator('.scene').count(),126);
 await p.locator('#cover img,#scene-01 img').evaluateAll(a=>Promise.all(a.map(i=>i.decode())));
 assert(!(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
 await p.screenshot({path:path.join(pack,'browser-check','reader-'+width+'.png')});
 await p.locator('#overview-tab').click();assert.equal(await p.locator('.comic-sheet').count(),5);assert.equal(await p.locator('.panel-link').count(),126);
 await p.locator('.comic-sheet img').evaluateAll(a=>Promise.all(a.map(i=>{i.loading='eager';return i.decode()})));
 await p.screenshot({path:path.join(pack,'browser-check','boards-ru-'+width+'.png')});
 await p.locator('.panel-link').last().click();await p.waitForTimeout(500);assert(await p.locator('#chapter').isVisible());assert(await p.locator('#scene-126').evaluate(e=>e.getBoundingClientRect().top<innerHeight));
 await p.locator('#changes-tab').click();let expected=plan.scenes.filter((s,i)=>JSON.stringify(s.paragraphs.ru)!==JSON.stringify(old.scenes[i].paragraphs.ru)).length;assert.equal(await p.locator('.text-change').count(),expected);
 await p.locator('[data-lang="en"]').click();await p.locator('#overview-tab').click();assert.equal(await p.locator('.comic-sheet').count(),5);assert((await p.locator('.comic-sheet img').first().getAttribute('src')).includes('-en.webp'));
 await p.locator('.comic-sheet img').evaluateAll(a=>Promise.all(a.map(i=>{i.loading='eager';return i.decode()})));
 await p.locator('#read-tab').click();const images=await p.locator('#chapter img').evaluateAll(a=>Promise.all(a.map(async i=>{i.loading='eager';await i.decode();return i.naturalWidth})));assert.equal(images.length,126);assert(images.every(Boolean));assert.equal(await p.locator('.pending,.error').count(),0);
 await p.locator('[data-lang="es"]').click();assert.equal(await p.locator('html').getAttribute('lang'),'es');assert.equal(await p.locator('.scene').count(),126);
 assert(!(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
 out.checks.push({width,defaultRussian:true,fullReaderScenes:126,decodedSceneImages:126,boardImagesDecoded:10,panelLinks:126,textComparison:true,languages:['ru','en','es'],noOverflow:true});await p.close();
}
assert.equal(out.errors.length,0);out.passed=true;
}catch(e){out.failure=e.stack;process.exitCode=1}finally{await browser.close();fs.writeFileSync(path.join(pack,'browser-check/results.json'),JSON.stringify(out,null,2));console.log(JSON.stringify(out))}})();
