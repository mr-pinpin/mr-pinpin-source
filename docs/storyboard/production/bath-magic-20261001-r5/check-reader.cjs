const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/Users/miguel_lemos/.npm/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const base = process.env.REVIEW_URL || 'http://127.0.0.1:18796/storyboard/review/bath-magic-r5.html';
const plan = JSON.parse(fs.readFileSync(path.join(__dirname,'story-plan.json'),'utf8'));
const expectedCount = plan.scenes.length;
const lastId = plan.scenes.at(-1).id;
const out = process.env.REVIEW_OUTPUT || path.join(__dirname, 'browser-check');
fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const result = { time: new Date().toISOString(), url: base, browser: browser.version(), sourceHashes: {}, checks: [], errors: [] };
  for(const file of ['story-plan.json','media.json','derivatives.json','check-reader.cjs','preview/docs/storyboard/review/bath-magic-r5.html','preview/docs/storyboard/review/bath-magic-r5.css','preview/docs/storyboard/review/bath-magic-r5.js']) {
    const target=path.join(__dirname,file);if(fs.existsSync(target))result.sourceHashes[file]=crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex');
  }
  try {
    for (const viewport of [{width:1440,height:1000}, {width:390,height:844}, {width:320,height:740}]) {
      const page = await browser.newPage({viewport});
      page.on('pageerror', e => result.errors.push(e.message));
      await page.goto(base + '?lang=en');
      await page.waitForSelector('.scene');
      const scenes = await page.locator('.scene').count();
      assert.equal(scenes, expectedCount);
      assert.equal(await page.locator('.day-heading').count(),4);
      assert.equal(await page.locator('#day-links a').count(),4);
      assert.equal(await page.locator('html').getAttribute('lang'), 'en');
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      assert.equal(overflow, false, 'No horizontal overflow');
      await page.locator('#cover img, #scene-01 img').evaluateAll(nodes=>Promise.all(nodes.map(image=>image.decode())));
      await page.screenshot({path:path.join(out, `reader-${viewport.width}.png`)});
      await page.locator('[data-lang="ru"]').click();
      assert.equal(await page.locator('html').getAttribute('lang'), 'ru');
      assert.match(await page.locator('#chapter-title').innerText(), /[А-Яа-я]/);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false,'Russian controls fit');
      await page.locator('[data-lang="es"]').click();
      assert.equal(await page.locator('html').getAttribute('lang'), 'es');
      await page.locator('#day-links a').last().click();
      assert.ok(await page.locator('#day-4').evaluate(e=>e.getBoundingClientRect().top<innerHeight));
      await page.locator('#overview-tab').click();
      assert.equal(await page.locator('#overview').isVisible(), true);
      assert.equal(await page.locator('.board-card').count(), expectedCount);
      if(await page.locator('#overview .board-sheet img').count()) await page.locator('#overview .board-sheet img').first().evaluate(image=>image.decode());
      await page.locator('#overview img').evaluateAll(nodes=>Promise.all(nodes.filter(image=>{const r=image.getBoundingClientRect();return r.top<innerHeight && r.bottom>0;}).map(image=>image.decode())));
      await page.screenshot({path:path.join(out, `storyboard-${viewport.width}.png`)});
      await page.locator('.board-card button').last().click();
      assert.equal(await page.locator('#chapter').isVisible(), true);
      await page.waitForTimeout(500);
      assert.ok(await page.locator('#'+lastId).evaluate(e => {const r=e.getBoundingClientRect();return r.top<innerHeight && r.bottom>80;}));
      const images = await page.locator('#chapter img').evaluateAll(async nodes => Promise.all(nodes.map(async image => {
        image.loading='eager';
        try { await image.decode(); return {src:image.src,width:image.naturalWidth,height:image.naturalHeight}; }
        catch { return {src:image.src,error:true}; }
      })));
      assert.ok(images.every(i=>!i.error), 'Every available illustration decodes');
      if(process.argv.includes('--complete')) {
        assert.equal(images.length,expectedCount);
        assert.equal(await page.locator('.pending').count(),0);
        assert.equal(await page.locator('#cover img').count(),1);
      }
      result.checks.push({viewport,scenes,readyImages:images.length,noHorizontalOverflow:!overflow,languages:['en','ru','es'],storyboardNavigation:true,decodedImages:images});
      await page.close();
    }
    assert.deepEqual(result.errors,[]);
    result.passed=true;
  } catch(error) {result.passed=false;result.failure=error.stack;process.exitCode=1;}
  finally { await browser.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:result.passed,checks:result.checks.map(x=>({viewport:x.viewport,scenes:x.scenes,readyImages:x.readyImages})),failure:result.failure})); }
})();
