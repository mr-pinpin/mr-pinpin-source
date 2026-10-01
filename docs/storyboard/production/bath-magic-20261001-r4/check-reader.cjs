const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'/Users/miguel_lemos/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const base=process.env.REVIEW_URL||'http://127.0.0.1:18796/storyboard/review/bath-magic-r4.html';
const plan=JSON.parse(fs.readFileSync(path.join(__dirname,'story-plan.json'),'utf8'));
const output=path.join(__dirname,'browser-check');fs.mkdirSync(output,{recursive:true});
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  const result={time:new Date().toISOString(),url:base,stage:'preproduction',sourceHashes:{},checks:[],errors:[]};
  for(const name of ['story-plan.json','media.json','check-reader.cjs','preview/docs/storyboard/review/bath-magic-r4.html','preview/docs/storyboard/review/bath-magic-r4.css','preview/docs/storyboard/review/bath-magic-r4.js'])result.sourceHashes[name]=crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,name))).digest('hex');
  try{
    for(const viewport of [{width:1440,height:1000},{width:390,height:844},{width:320,height:740}]){
      const page=await browser.newPage({viewport});page.on('pageerror',error=>result.errors.push(error.message));await page.goto(base+'?lang=en');await page.waitForSelector('.scene');
      assert.equal(await page.locator('.scene').count(),plan.scenes.length);assert.equal(await page.locator('.day').count(),4);assert.equal(await page.locator('.scene > img').count(),0);assert.equal(await page.locator('.pending').count(),0);
      assert.match(await page.locator('#draft-label').innerText(),/Preproduction/i);const studyCount=await page.locator('#duck-study img').count();if(!process.argv.includes('--text-only'))assert.equal(studyCount,1);if(studyCount)await page.locator('#duck-study img').evaluate(image=>image.decode());
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(output,`reader-${viewport.width}.png`)});
      for(const language of ['ru','es']){await page.locator(`[data-lang="${language}"]`).click();assert.equal(await page.locator('html').getAttribute('lang'),language);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.ok((await page.locator('#scene-80 .scene-text').innerText()).length>5);}
      await page.locator('#day-links a').last().click();await page.waitForTimeout(150);assert.ok(await page.locator('#day-4').evaluate(e=>e.getBoundingClientRect().top<innerHeight));
      if(await page.locator('.old-art').count()){const reference=page.locator('.old-art').first();await reference.locator('summary').click();await reference.locator('img').first().evaluate(image=>image.decode());assert.match(await reference.locator('figcaption').first().innerText(),/R3/);}
      result.checks.push({viewport,scenes:plan.scenes.length,days:4,studyDecoded:studyCount===1,finishedSceneImages:0});await page.close();
    }
    assert.equal(result.errors.length,0);result.passed=true;
  }catch(error){result.passed=false;result.failure=String(error);process.exitCode=1;}
  finally{await browser.close();fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));}
})();
