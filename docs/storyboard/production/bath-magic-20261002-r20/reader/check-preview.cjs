const {chromium}=require('/Users/miguel_lemos/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs=require('fs'),assert=require('assert/strict'),crypto=require('crypto');
const root='/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261002-r20',base='http://127.0.0.1:18796';
(async()=>{let b;const proof={passed:false,errors:[],checks:[]};try{
const plan=JSON.parse(fs.readFileSync(root+'/story-plan.json')),media=JSON.parse(fs.readFileSync(root+'/media.json')),old=JSON.parse(fs.readFileSync(root+'/baseline/story-plan.json')),before=JSON.parse(fs.readFileSync(root+'/baseline/media.json'));
assert.equal(plan.scenes.length,176);assert.deepEqual(media.pendingIds,[]);assert(!plan.scenes.some(x=>x.id==='scene-05d'));
assert.deepEqual(plan.scenes.map(x=>x.id),old.scenes.filter(x=>x.id!=='scene-05d').map(x=>x.id));
const at=plan.scenes.findIndex(x=>x.id==='scene-05c5');assert.equal(plan.scenes[at+1].id,'scene-05e');
for(const x of plan.scenes){assert.equal(x.number,plan.scenes.indexOf(x)+1);if(x.id!=='scene-05g')assert.equal(media.images[x.id].sha256,before.images[x.id].sha256);if(x.id!=='scene-05c5')assert.deepEqual(x.paragraphs,old.scenes.find(y=>y.id===x.id).paragraphs)}
proof.checks.push('176ordered scenes; only05d removed;175retained image hashes unchanged; only05c5 caption reconciled');
const entry=media.images['scene-05g'],url=base+'/storyboard/production/'+entry.sourceProduction+'/'+entry.path,r=await fetch(url);assert(r.ok);const bytes=Buffer.from(await r.arrayBuffer());assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),entry.sha256);proof.newImage={url,sha256:entry.sha256};
b=await chromium.launch({channel:'chrome',headless:true});const p=await b.newPage();p.on('pageerror',e=>proof.errors.push(e.message));
for(const width of [1440,390]){await p.setViewportSize({width,height:900});for(const lang of ['ru','en','es']){
await p.goto(base+'/storyboard/review/bath-magic-r20.html?lang='+lang);await p.locator('#chapter .scene').last().waitFor();
const rows=await p.locator('#chapter .scene').evaluateAll(es=>es.map(e=>({id:e.id,paragraphs:[...e.querySelectorAll('.scene-text p')].map(p=>p.textContent)})));assert.deepEqual(rows,plan.scenes.map(x=>({id:x.id,paragraphs:x.paragraphs[lang]})));assert.equal(await p.locator('#day-links a').count(),4);assert.equal(await p.locator('.pending:visible').count(),0);
for(const selector of ['#cover img','#scene-05g img','#scene-05c5 img'])await p.locator(selector).evaluate(i=>{i.loading='eager';return i.decode()});
assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
await p.locator('#changes-tab').click();assert.equal(await p.locator('.art-change').count(),1);assert.equal(await p.locator('.removed-scene').count(),1);assert.equal(await p.locator('.art-insertion').count(),0);
assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);if(lang==='ru')await p.screenshot({path:root+'/reader/changes-'+width+'.png'});
}}
proof.checks.push('RUENES desktop/mobile exactcaption/order, arrival and arm image decode, one correction/one removedscene before-after, zerooverflow');assert.deepEqual(proof.errors,[]);proof.passed=true;
}catch(e){proof.error=e.stack;process.exitCode=1}finally{if(b)await b.close();fs.writeFileSync(root+'/reader/preview-proof.json',JSON.stringify(proof,null,2));console.log(JSON.stringify(proof,null,2))}})();