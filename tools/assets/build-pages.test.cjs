const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const {buildPages, BUDGET} = require('./build-pages.cjs');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(),'pinpin-pages-test-'));
  t.after(() => fs.rmSync(root,{recursive:true,force:true}));
  const manifest = {version:1,bucket:'miguelemosreverte/mr-pinpin-archive',assets:[]};
  function write(name, data = 'data') {
    fs.mkdirSync(path.dirname(path.join(root,name)),{recursive:true});
    fs.writeFileSync(path.join(root,name),data);
  }
  function asset(name, role = 'production', data = 'image') {
    write(name,data);
    manifest.assets.push({path:name,role,bytes:Buffer.byteLength(data),sha256:crypto.createHash('sha256').update(data).digest('hex'),object:'sha256/'+crypto.createHash('sha256').update(data).digest('hex')});
  }
  function build(options = {}) {
    write('assets/manifest.json',JSON.stringify(manifest));
    return buildPages({root,...options});
  }
  write('docs/index.html','<img src="images/live.png?rev=v1">');
  asset('docs/images/live.png');
  return {root,manifest,write,asset,build};
}

test('production-only stage preserves code, runtime JSON/fonts and assets without HF or local archives', t => {
  const f = fixture(t);
  f.write('docs/app.js','fetch("registry.json");');
  f.write('docs/registry.json','{"src":"images/live.png"}');
  f.asset('docs/fonts/book.woff2');
  f.write('docs/.nojekyll','');
  for (const tree of ['comparison','storyboard/review','storyboard/models','storyboard/production']) f.write(`docs/${tree}/secret.json`);
  f.asset('docs/images/rejected.png','archive');
  fs.unlinkSync(path.join(f.root,'docs/images/rejected.png'));
  const result = f.build();
  assert.equal(result.managedProduction,2);
  for (const name of ['index.html','app.js','registry.json','fonts/book.woff2','images/live.png','.nojekyll'])
    assert(fs.existsSync(path.join(result.dest,name)),name);
  assert(!fs.existsSync(path.join(result.dest,'comparison')));
  assert(!fs.existsSync(path.join(result.dest,'storyboard')));
  assert(!fs.existsSync(path.join(result.dest,'images/rejected.png')));
});

test('generation metadata sidecars stay local while runtime focus data ships', t => {
  const f = fixture(t);
  f.write('docs/storyboard/images/covers/chapter-01/production.html','<img src="gone.png">');
  f.write('docs/storyboard/videos/old.json','{"output":"/local/old.mp4"}');
  f.write('docs/storyboard/images/atlas/shire-focus-field-v1.json','{"data":"field.bin"}');
  f.asset('docs/storyboard/images/atlas/field.bin');
  const {dest} = f.build();
  assert(!fs.existsSync(path.join(dest,'storyboard/images/covers')));
  assert(!fs.existsSync(path.join(dest,'storyboard/videos')));
  assert(fs.existsSync(path.join(dest,'storyboard/images/atlas/shire-focus-field-v1.json')));
  assert(fs.existsSync(path.join(f.root,'docs/storyboard/images/covers/chapter-01/production.html')));
});

test('production walk manifest ships and validates sheet references without admitting other sidecars',t=>{
  const f=fixture(t),base='docs/storyboard/images/atlas/walk/';
  f.write(base+'manifest.json',JSON.stringify({clips:{loop000:{sheet:'./sheets/loop000.webp'}}}));
  f.write(base+'authoring.json','{"source":"/private/draft.png"}');
  assert.throws(()=>f.build({check:true}),/dangling local reference.*loop000/);
  f.asset(base+'sheets/loop000.webp');
  const {dest}=f.build();
  assert(fs.existsSync(path.join(dest,base.slice(5)+'manifest.json')));
  assert(!fs.existsSync(path.join(dest,base.slice(5)+'authoring.json')));
});

test('checks every managed production file including unreferenced files', t => {
  const f = fixture(t); f.asset('docs/images/other.png');
  f.write('docs/images/other.png','wrong');
  assert.throws(() => f.build(),/hash\/size mismatch.*other.png/);
  assert(!fs.existsSync(path.join(f.root,'.pages-site')));
});

test('missing production fails but unavailable archives do not', t => {
  const f = fixture(t); fs.unlinkSync(path.join(f.root,'docs/images/live.png'));
  assert.throws(() => f.build(),/Missing production file/);
});

test('unmanaged binary fails closed', t => {
  const f = fixture(t); f.write('docs/images/unknown.mp4');
  assert.throws(() => f.build(),/Unmanaged production file/);
});

test('rejects selected symlinks but does not follow excluded archive links', t => {
  const f = fixture(t);
  fs.symlinkSync('/does-not-exist',path.join(f.root,'docs/broken.js'));
  assert.throws(() => f.build(),/Selected symlink/);
  fs.unlinkSync(path.join(f.root,'docs/broken.js'));
  fs.mkdirSync(path.join(f.root,'docs/storyboard'),{recursive:true});
  fs.symlinkSync('/does-not-exist',path.join(f.root,'docs/storyboard/models'));
  assert(f.build({check:true}).check);
});

test('budget is strictly below the cap and cannot be raised', t => {
  const f = fixture(t), {bytes} = f.build({check:true});
  assert.throws(() => f.build({budget:bytes}),/must be below/);
  assert.throws(() => f.build({budget:BUDGET+1}),/must be below/);
  assert(f.build({check:true,budget:bytes+1}).check);
});

test('rejects malformed, duplicate, unsafe and excluded production manifest entries', t => {
  const f = fixture(t), original = structuredClone(f.manifest.assets[0]);
  for (const mutation of [{path:'docs/../outside.png'},{path:'docs/storyboard/review/live.png'}, {bytes:-1},{sha256:'no'}, {object:'../secret'}, {role:'maybe'}]) {
    f.manifest.assets = [{...original,...mutation}];
    assert.throws(() => f.build());
  }
  f.manifest.assets = [original, original];
  assert.throws(() => f.build(),/Duplicate/);
});

test('HTML, CSS, module, runtime JSON and srcset dangling references fail with file/line', t => {
  const f = fixture(t);
  for (const [name, content] of [
    ['docs/index.html','<a href="storyboard/review/study.html">Review</a>'],
    ['docs/index.html','<img srcset="images/live.png 1x, images/gone.webp 2x">'],
    ['docs/main.css','a { background: url("images/gone.webp"); }'],
    ['docs/main.css','@import "gone.css";'],
    ['docs/main.js','import "./gone.js";'],
    ['docs/main.js','fetch("gone.json");'],
    ['docs/main.json','{"src":"images/gone.webp"}']
  ]) {
    f.write(name,content);
    assert.throws(() => f.build({check:true}),new RegExp(name.replaceAll('.','\\.')+':1: dangling'));
    fs.unlinkSync(path.join(f.root,name));
  }
});

test('JSON provenance can point to an archive; live paths and query strings still checked', t => {
  const f = fixture(t);
  f.write('docs/registry.json',JSON.stringify({variants:[{src:'images/live.png?rev=08'}],registration:{source:'videos/archive.mp4'},generationLog:'storyboard/production/log.json'}));
  f.write('docs/index.html','<a href="https://example.test/remote"><img src="images/live.png#v1"></a>');
  assert(f.build({check:true}).check);
  f.asset('docs/images/rejected.png','archive');
  f.write('docs/registry.json','{"src":"images/rejected.png"}');
  assert.throws(() => f.build(),/dangling local reference/);
});

test('story image URLs resolve against the document and focus data against its JSON', t => {
  const f = fixture(t);
  f.asset('docs/storyboard/images/live.png');
  f.asset('docs/storyboard/images/atlas/field.bin');
  f.write('docs/storyboard/stories/book.json','{"image":"images/live.png"}');
  f.write('docs/storyboard/images/atlas/shire-focus-field-v1.json','{"data":"field.bin"}');
  assert(f.build({check:true}).check);
});

test('direct runtime and fallback references cannot silently use default-archived assets', t => {
  const f = fixture(t);
  f.asset('docs/images/draft.webp', 'archive');
  f.write('docs/main.js', 'const image = preferred || "images/draft.webp";');
  assert.throws(() => f.build({check:true}), /dangling local reference images\/draft.webp/);
  f.manifest.assets.find(e => e.path === 'docs/images/draft.webp').role = 'production';
  assert(f.build({check:true}).check);
});

test('never replaces existing destinations or writes into source trees', t => {
  const f = fixture(t);
  f.write('existing/precious.txt','keep');
  for (const dest of ['.', '..', 'docs', 'docs/output', 'existing']) assert.throws(() => f.build({dest}));
  assert.equal(fs.readFileSync(path.join(f.root,'existing/precious.txt'),'utf8'),'keep');
  fs.symlinkSync(path.join(f.root,'existing'),path.join(f.root,'link'));
  assert.throws(() => f.build({dest:'link/output'}),/symlink/);
  assert(f.build({dest:'other/output'}).dest.endsWith('/other/output'));
});

test('audited local experiment entrypoints stay out while public runtime and unknown references remain checked', t => {
  const f=fixture(t);
  f.write('docs/house-image-tour.html','<img src="storyboard/production/archived.png">');
  f.write('docs/house-image-tour-config.js','const source="missing-review-only.png";');
  f.write('docs/storyboard/locations/pinpin-house/location.json','{"source":"missing-guide.png"}');
  f.write('docs/room-compare.html','<img src="images/live.png">');
  f.write('docs/storyboard/atlas.html','<img src="../images/live.png">');
  f.write('docs/storyboard/stories/example.json','{"image":"../../images/live.png"}');
  const {dest}=f.build();
  for(const name of ['room-compare.html','storyboard/atlas.html','storyboard/stories/example.json'])
    assert(fs.existsSync(path.join(dest,name)),name);
  for(const name of ['house-image-tour.html','house-image-tour-config.js','storyboard/locations'])
    assert(!fs.existsSync(path.join(dest,name)),name);
  assert(fs.existsSync(path.join(f.root,'docs/house-image-tour.html')));
  f.write('docs/house-new-public.html','<img src="unknown.png">');
  assert.throws(()=>f.build({check:true}),/dangling local reference.*unknown/);
});
