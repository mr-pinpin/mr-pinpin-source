const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'../docs/storyboard'),story=JSON.parse(fs.readFileSync(path.join(root,'stories/bath-magic.json')));
function api(){const c=vm.createContext({window:{},fetch:async()=>({ok:true,json:async()=>structuredClone(story)})});vm.runInContext(fs.readFileSync(path.join(root,'standalone-stories.js'),'utf8'),c);return c.window.standaloneStories;}
test('approved bath is one continuous localized 139-image edition',async()=>{const a=api();assert(a.complete(story));assert.equal((await a.load('bath-magic')).scenes.length,139);for(const l of ['en','ru','es']){const e=a.edition(story,l);assert.equal(e.images[0].src,story.cover[l]);assert.equal(e.scenes.length,139);}assert.deepEqual(story.sectionNav.map(s=>s.startScene),[1,68,81,103]);});
test('bath rejects incomplete captions, duplicate scenes and misplaced spreads',()=>{for(const mutate of [s=>s.scenes.pop(),s=>s.scenes[2].id=s.scenes[1].id,s=>s.scenes[4].paragraphs.ru=[],s=>s.spreads[50].scenes=[0]]){const s=structuredClone(story);mutate(s);assert.equal(api().complete(s),false);}});

test('home atlas keeps bedtime primary and exposes bath in the selected language',async()=>{
 const c=vm.createContext({window:{standaloneStories:{load:async id=>id==='bath-magic'?story:null}},location:{search:''},URLSearchParams,Image:function(){}});
 vm.runInContext(fs.readFileSync(path.join(root,'atlas-stories.js'),'utf8'),c);
 const a=c.window.AtlasStories;assert.equal(Object.keys(a.entries).length,4);
 for(const lang of ['en','ru','es']){assert.equal(a.href('home',lang),'index.html?story=home-sweet-home&lang='+lang);const items=await a.related('home',lang);assert.equal(items.length,1);assert.equal(items[0].href,'index.html?story=bath-magic&lang='+lang);assert.equal(items[0].title,story.title[lang]);}
 assert.equal((await a.related('lake','ru')).length,0);
});
