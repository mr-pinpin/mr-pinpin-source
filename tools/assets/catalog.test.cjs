'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const {buildCatalog, archiveIgnore, receiptPlan, validateManifest, main} = require('./catalog.cjs');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pinpin-catalog-'));
  t.after(() => fs.rmSync(root, {recursive: true, force: true}));
  const put = (name, text = name) => {
    fs.mkdirSync(path.dirname(path.join(root, name)), {recursive: true});
    fs.writeFileSync(path.join(root, name), text);
  };
  put('docs/image.png', 'production');
  put('docs/review.mp4', 'archive');
  put('docs/index.html', '<img src="image.png">');
  const policy = {version: 1, bucket: 'test/archive', roots: ['docs'],
    extensions: ['.png', '.mp4', '.glb'], managedSymlinks: [],
    manifestSeeds: [], manifestDirectories: [], resolutionBases: ['docs'],
    production: ['docs/image.png'], archive: ['docs/review.mp4']};
  return {root, put, policy};
}

test('catalog hashes binary assets, totals Pages files, and produces content-addressed keys', async t => {
  const {root, policy} = fixture(t);
  const {manifest, summary} = await buildCatalog(root, policy);
  assert.equal(manifest.assets.length, 2);
  const first = manifest.assets[0];
  assert.equal(first.sha256, crypto.createHash('sha256').update('production').digest('hex'));
  assert.equal(first.object, `sha256/${first.sha256.slice(0, 2)}/${first.sha256}/image.png`);
  assert.equal(summary.projectedPagesBytes, 10 + Buffer.byteLength('<img src="image.png">'));
  assert.equal(summary.archive.bytes, 7);
  assert.deepEqual(manifest, (await buildCatalog(root, policy, manifest)).manifest);
});

test('unclassified additions fail; explicit archive assignment refreshes the catalog', async t => {
  const {root, put, policy} = fixture(t);
  put('docs/new.png');
  await assert.rejects(buildCatalog(root, policy), /Unclassified assets.*\n.*new.png/s);
  policy.archive.push('docs/new.png');
  assert.equal((await buildCatalog(root, policy)).manifest.assets.length, 3);
});

test('structured manifests discover new production, preserve every cover status, and ignore source-video metadata', async t => {
  const {root, put, policy} = fixture(t);
  put('docs/new-cover.png');
  put('docs/book.json', JSON.stringify({covers: {one: {status: 'proposed', src: 'new-cover.png'}}}));
  put('docs/video.json', JSON.stringify({source: 'missing-source.mp4', variants: [{src: 'review.mp4'}]}));
  policy.manifestSeeds = [{path: 'docs/book.json'}, {path: 'docs/video.json', select: ['variants']}];
  const {manifest} = await buildCatalog(root, policy);
  assert.equal(manifest.assets.find(e => e.path === 'docs/new-cover.png').role, 'production');
  assert.equal(manifest.assets.find(e => e.path === 'docs/review.mp4').role, 'production');
});

test('opt-in unreferenced archives need no path entry and promote when registered', async t => {
  const {root, put, policy} = fixture(t);
  policy.unreferencedRole = 'archive';
  for (const name of ['docs/review/draft.png', 'docs/models/draft.glb', 'docs/chapter/new.png']) put(name);
  const initial = (await buildCatalog(root, policy)).manifest;
  for (const name of ['docs/review/draft.png', 'docs/models/draft.glb', 'docs/chapter/new.png'])
    assert.equal(initial.assets.find(e => e.path === name).role, 'archive');
  fs.unlinkSync(path.join(root, 'docs/review/draft.png'));
  put('docs/book.json', '{"image":"chapter/new.png"}');
  policy.manifestSeeds = [{path: 'docs/book.json'}];
  const next = (await buildCatalog(root, policy, initial)).manifest;
  assert.equal(next.assets.find(e => e.path === 'docs/chapter/new.png').role, 'production');
  assert.deepEqual(next.assets.find(e => e.path === 'docs/review/draft.png'), initial.assets.find(e => e.path === 'docs/review/draft.png'));
  assert.equal(next.assets.find(e => e.path === 'docs/image.png').role, 'production');
  fs.unlinkSync(path.join(root, 'docs/chapter/new.png'));
  await assert.rejects(buildCatalog(root, policy, next), /Missing production asset/);
  policy.unreferencedRole = 'production';
  await assert.rejects(buildCatalog(root, policy, next), /Invalid unreferencedRole/);
});

test('new story manifests and sprite frame keys extend production automatically', async t => {
  const {root, put, policy} = fixture(t);
  put('docs/stories/one.json', JSON.stringify({'../review.mp4#front#1': {}}));
  policy.manifestDirectories = ['docs/stories'];
  const {manifest} = await buildCatalog(root, policy);
  assert.equal(manifest.assets.find(e => e.path === 'docs/review.mp4').role, 'production');
});

test('missing archives retain their exact previous identities, missing production fails', async t => {
  const {root, policy} = fixture(t);
  const initial = (await buildCatalog(root, policy)).manifest;
  fs.unlinkSync(path.join(root, 'docs/review.mp4'));
  const next = await buildCatalog(root, policy, initial);
  assert.deepEqual(next.manifest, initial);
  assert.deepEqual(next.retained, ['docs/review.mp4']);
  await assert.rejects(buildCatalog(root, policy), /Missing archive without prior identity/);
  fs.unlinkSync(path.join(root, 'docs/image.png'));
  await assert.rejects(buildCatalog(root, policy, initial), /Missing production asset/);
});

test('missing production manifest references fail even if prior archives exist', async t => {
  const {root, put, policy} = fixture(t);
  const prior = (await buildCatalog(root, policy)).manifest;
  fs.unlinkSync(path.join(root, 'docs/review.mp4'));
  put('docs/story.json', '{"image":"./review.mp4"}');
  policy.manifestSeeds = [{path: 'docs/story.json'}];
  await assert.rejects(buildCatalog(root, policy, prior), /Missing production asset/);
  put('docs/story.json', '{"image":"./absent.png"}');
  await assert.rejects(buildCatalog(root, policy, prior), /Missing manifest asset/);
});

test('managed symlink directories retain logical paths and absent targets can use archived identities', async t => {
  const {root, put, policy} = fixture(t);
  put('outside/render.png', 'pixels');
  fs.symlinkSync(path.join(root, 'outside'), path.join(root, 'docs/renders'));
  policy.managedSymlinks = ['docs/renders'];
  policy.archive.push('docs/renders/render.png');
  const initial = (await buildCatalog(root, policy)).manifest;
  assert.ok(initial.assets.some(e => e.path === 'docs/renders/render.png'));
  fs.rmSync(path.join(root, 'outside'), {recursive: true});
  assert.deepEqual((await buildCatalog(root, policy, initial)).manifest, initial);
});

test('unmanaged links, cycles, and broken first-time managed targets fail', async t => {
  const {root, policy} = fixture(t);
  fs.symlinkSync(path.join(root, 'docs'), path.join(root, 'docs/loop'));
  await assert.rejects(buildCatalog(root, policy), /Unmanaged symlink/);
  policy.managedSymlinks.push('docs/loop');
  await assert.rejects(buildCatalog(root, policy), /Symlink cycle/);
  fs.unlinkSync(path.join(root, 'docs/loop'));
  fs.symlinkSync(path.join(root, 'absent'), path.join(root, 'docs/loop'));
  await assert.rejects(buildCatalog(root, policy), /Broken managed symlink/);
});

test('skip bytecode and backups but keep provenance outside the binary catalog', async t => {
  const {root, put, policy} = fixture(t);
  put('docs/__pycache__/asset.png');
  put('docs/backups/asset.png');
  put('docs/cache.pyc');
  put('docs/work.blend1');
  put('docs/frame.png.bak');
  put('docs/notes.md', 'provenance');
  const {manifest, summary} = await buildCatalog(root, policy);
  assert.equal(manifest.assets.length, 2);
  assert.equal(summary.nonAssetFiles, 2);
});

test('previous manifest validation rejects unsafe paths, duplicate paths, identities, and bucket mismatch', async t => {
  const {root, policy} = fixture(t);
  const manifest = (await buildCatalog(root, policy)).manifest;
  const altered = change => ({...manifest, assets: [{...manifest.assets[0], ...change}]});
  assert.throws(() => validateManifest(altered({path: 'docs/../secret.png'}), policy.bucket), /Unsafe/);
  assert.throws(() => validateManifest(altered({sha256: 'bad'}), policy.bucket), /Invalid/);
  assert.throws(() => validateManifest(altered({object: 'unverified'}), policy.bucket), /Invalid/);
  assert.throws(() => validateManifest({...manifest, assets: [...manifest.assets, manifest.assets[0]]}, policy.bucket), /Invalid/);
  assert.throws(() => validateManifest(manifest, 'another/bucket'), /mismatch/);
});

test('generated ignore is root-anchored and verification plan is not a success receipt', async t => {
  const {root, policy} = fixture(t);
  const {manifest} = await buildCatalog(root, policy);
  assert.match(archiveIgnore(manifest), /\n\/docs\/review.mp4\n/);
  assert.doesNotMatch(archiveIgnore(manifest), /\/docs\/image.png/);
  assert.equal(receiptPlan(manifest).verificationRequired, true);
  assert.equal(receiptPlan(manifest).assets.length, 1);
});

test('CLI refresh and check are deterministic; stale output and unknown additions do not write', async t => {
  const {root, put, policy} = fixture(t);
  put('assets/policy.json', JSON.stringify(policy));
  await main(['--root', root, '--receipt-plan', 'assets/plan.json']);
  await main(['--root', root, '--check', '--receipt-plan', 'assets/plan.json']);
  const previous = fs.readFileSync(path.join(root, 'assets/manifest.json'), 'utf8');
  put('docs/image.png', 'changed');
  await assert.rejects(main(['--root', root, '--check']), /stale/);
  assert.equal(fs.readFileSync(path.join(root, 'assets/manifest.json'), 'utf8'), previous);
  put('docs/unknown.png');
  await assert.rejects(main(['--root', root]), /Unclassified/);
  assert.equal(fs.readFileSync(path.join(root, 'assets/manifest.json'), 'utf8'), previous);
});

test('opted-in runtime variants archive native sources without changing ordinary chapter assets', async t => {
  const {root, put, policy}=fixture(t);
  policy.extensions.push('.webp');policy.unreferencedRole='archive';
  put('docs/master.png','native original');put('docs/runtime.webp','selected runtime');
  put('docs/sprites.json',JSON.stringify({direction:{src:'master.png',runtimeSrc:'runtime.webp'}}));
  policy.manifestSeeds=[{path:'docs/sprites.json',preferRuntimeSrc:true}];
  let result=await buildCatalog(root,policy);
  assert.equal(result.manifest.assets.find(e=>e.path==='docs/master.png').role,'archive');
  assert.equal(result.manifest.assets.find(e=>e.path==='docs/runtime.webp').role,'production');
  assert.equal(result.manifest.assets.find(e=>e.path==='docs/image.png').role,'production');
  policy.manifestSeeds[0].preferRuntimeSrc=false;
  result=await buildCatalog(root,policy);
  assert.equal(result.manifest.assets.find(e=>e.path==='docs/master.png').role,'production');
  policy.manifestSeeds[0].preferRuntimeSrc=true;
  put('docs/sprites.json',JSON.stringify({direction:{src:'master.png',runtimeSrc:''}}));
  result=await buildCatalog(root,policy);
  assert.equal(result.manifest.assets.find(e=>e.path==='docs/master.png').role,'production');
  put('docs/sprites.json',JSON.stringify({direction:{src:'master.png',runtimeSrc:'absent.webp'}}));
  await assert.rejects(buildCatalog(root,policy),/Missing manifest asset/);
});
