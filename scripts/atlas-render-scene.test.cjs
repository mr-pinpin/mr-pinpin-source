const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../docs/storyboard/atlas-render-scene.js'), 'utf8');
const load = () => import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));

test('streamed pointer uses existing camera world transform; malformed input cannot set a destination', async () => {
  const {registerAtlasScene} = await load();
  const host = {}, destinations = [], screen = [], zoom = [];
  const camera = {
    snapshot: {x: 100, y: 50, width: 1920, height: 1080, scale: 2},
    screenToWorld(point) { screen.push(point); return [point[0] / 2 + 100, point[1] / 2 + 50]; },
    zoomBy(value) { zoom.push(value); }, focus() {}
  };
  const scene = await registerAtlasScene({host, canvas:{}, camera, target:p => destinations.push(p), refresh() {}}).create();
  scene.applyInput({activate:true, pointer:[.25, .75], zoom:999});
  assert.deepEqual(screen, [[480,810]]);
  assert.deepEqual(destinations, [[340,455]]);
  assert.equal(zoom[0], Math.pow(1.12,3));
  scene.applyInput({activate:true,pointer:[NaN,.5]});
  scene.applyInput({activate:true,pointer:[.5]});
  assert.equal(destinations.length,1);
  scene.applyInput({activate:true,pointer:[-10,10]});
  assert.deepEqual(screen[1],[0,1080]);
});

test('stopping the scene releases captured tracks and ignores later remote input', async () => {
  const {registerAtlasScene} = await load();
  let stopped = 0, activated = 0, requested;
  const stream = {getTracks:() => [{stop() { stopped++; }}]};
  const scene = await registerAtlasScene({host:{}, canvas:{captureStream(fps) {requested=fps;return stream;}},
    camera:{snapshot:{}}, target() {activated++;}, refresh() {}}).create();
  assert.equal(scene.capture({fps:999}),stream);
  assert.equal(requested,60);
  scene.stop();scene.stop();
  assert.equal(stopped,1);
  scene.applyInput({activate:true,pointer:[.5,.5]});
  assert.equal(activated,0);
  assert.throws(() => scene.capture(),/stopped/);
});
