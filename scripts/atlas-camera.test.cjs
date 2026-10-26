const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../docs/storyboard/gpu/camera.js'), 'utf8');
const modulePromise = import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const near = (a, b) => assert(Math.abs(a - b) < 1e-8, `${a} != ${b}`);
const samePoint = (a, b) => a.forEach((value, i) => near(value, b[i]));

function target() {
  const events = new Map();
  return {
    events,
    addEventListener(type, fn) { if (!events.has(type)) events.set(type, new Set()); events.get(type).add(fn); },
    removeEventListener(type, fn) { events.get(type)?.delete(fn); },
    emit(type, event = {}) { for (const fn of events.get(type) || []) fn({type, ...event}); }
  };
}
async function harness(width = 1200, height = 800, reducedMotion = false) {
  const {createCamera} = await modulePromise;
  const raf = new Map(), timers = new Map(), captured = new Set();
  let clock = 0, serial = 0;
  const media = Object.assign(target(), {matches: reducedMotion});
  const view = Object.assign(target(), {
    matchMedia: () => media, performance: {now: () => clock},
    requestAnimationFrame(fn) { raf.set(++serial, fn); return serial; },
    cancelAnimationFrame(id) { raf.delete(id); },
    setTimeout(fn, delay) { timers.set(++serial, {fn, at: clock + delay}); return serial; },
    clearTimeout(id) { timers.delete(id); }
  });
  const rect = {left: 37, top: 29, width, height};
  const canvas = Object.assign(target(), {style: {touchAction: 'auto'}, ownerDocument: {defaultView: view},
    getBoundingClientRect: () => rect,
    setPointerCapture: id => captured.add(id), hasPointerCapture: id => captured.has(id),
    releasePointerCapture(id) { captured.delete(id); canvas.emit('lostpointercapture', {pointerId: id}); }
  });
  const changes = [], lifecycle = [], taps = [], points = [];
  const camera = createCamera(canvas, {worldWidth: 1536, worldHeight: 1024,
    onChange: value => changes.push(value), onMoveStart: () => lifecycle.push('start'),
    onMoveEnd: () => lifecycle.push('end'), onTap: p => taps.push(p), onPoint: p => points.push(p)});
  return {camera, rect, canvas, media, view, changes, lifecycle, taps, points, raf, timers, captured,
    event(type, x = 600, y = 400, extra = {}) {
      let prevented = false;
      canvas.emit(type, {pointerId: 1, pointerType: 'mouse', button: 0, clientX: x + rect.left,
        clientY: y + rect.top, preventDefault() { prevented = true; }, ...extra});
      return prevented;
    },
    advance(ms) {
      clock += ms;
      const callbacks = [...raf.values()]; raf.clear(); callbacks.forEach(fn => fn(clock));
      for (const [id, timer] of timers) if (timer.at <= clock) { timers.delete(id); timer.fn(); }
    }
  };
}

test('exact 2x cover and home/lake centers on desktop, phone and narrow phone', async () => {
  for (const [width, height] of [[1440, 900], [390, 844], [320, 700]]) {
    const {camera} = await harness(width, height), s = camera.snapshot;
    near(s.scale, 2 * Math.max(width / 1536, height / 1024));
    near(s.x, 1536 * (width < 600 ? .30 : .36)); near(s.y, 512);
    assert(s.x > width / (2 * s.scale) && s.x < 1536 - width / (2 * s.scale));
    assert(s.y > height / (2 * s.scale) && s.y < 1024 - height / (2 * s.scale));
    samePoint(camera.worldToScreen([s.x, s.y]), [width / 2, height / 2]);
  }
});

test('transforms invert, snapshot is isolated, and nonzero canvas offsets map correctly', async () => {
  const h = await harness(), {camera} = h;
  for (const p of [[0, 0], [460.8, 512], [1536, 1024], [-10, 1700]])
    samePoint(camera.screenToWorld(camera.worldToScreen(p)), p);
  const snapshot = camera.snapshot; snapshot.x = -999; assert.notEqual(camera.snapshot.x, snapshot.x);
  h.event('pointermove', 500, 340); samePoint(h.points[0], camera.screenToWorld([500, 340]));
});

test('wheel is prevented and stays anchored with reference sensitivity and debounce', async () => {
  const h = await harness(), anchor = h.camera.screenToWorld([800, 500]), initial = h.camera.snapshot.scale;
  assert(h.event('wheel', 800, 500, {deltaY: -100, deltaMode: 0}));
  near(h.camera.snapshot.scale, initial * 2 ** .22);
  samePoint(h.camera.screenToWorld([800, 500]), anchor);
  assert.deepEqual(h.lifecycle, ['start']); h.advance(119); assert.deepEqual(h.lifecycle, ['start']);
  h.advance(1); assert.deepEqual(h.lifecycle, ['start', 'end']);
  h.event('wheel', 800, 500, {deltaY: -1, deltaMode: 1, ctrlKey: true});
  near(h.camera.snapshot.scale, initial * 2 ** (.22 + .16));
});

test('direct pan moves both axes, then inertia ends exactly after 260 ms', async () => {
  const h = await harness(), initial = h.camera.snapshot;
  h.event('pointerdown', 600, 400); h.advance(16); h.event('pointermove', 630, 420);
  near(h.camera.snapshot.x, initial.x - 30 / initial.scale);
  near(h.camera.snapshot.y, initial.y - 20 / initial.scale);
  h.event('pointerup', 630, 420); const released = h.camera.snapshot;
  assert.equal(h.taps.length, 0); assert.deepEqual(h.lifecycle, ['start']); assert.equal(h.raf.size, 1);
  h.advance(130); assert(h.camera.snapshot.x < released.x && h.camera.snapshot.y < released.y);
  assert.deepEqual(h.lifecycle, ['start']); h.advance(129); assert.deepEqual(h.lifecycle, ['start']);
  h.advance(1); assert.deepEqual(h.lifecycle, ['start', 'end']); assert.equal(h.raf.size, 0);
  near(h.camera.snapshot.x, released.x - (30 / 16 * .3) * 130 / initial.scale);
});

test('stale velocity and reduced motion suppress release inertia', async () => {
  for (const reduced of [true, false]) {
    const h = await harness(1200, 800, reduced);
    h.event('pointerdown'); h.advance(16); h.event('pointermove', 620, 420);
    if (!reduced) h.advance(81);
    h.event('pointerup', 620, 420); assert.equal(h.raf.size, 0);
    assert.deepEqual(h.lifecycle, ['start', 'end']);
  }
  const h = await harness(); h.event('pointerdown'); h.advance(16);
  h.event('pointermove', 620, 420); h.event('pointerup', 620, 420);
  h.media.matches = true; h.media.emit('change'); assert.equal(h.raf.size, 0);
  assert.deepEqual(h.lifecycle, ['start', 'end']);
});

test('pinch keeps the original world anchor under its moving midpoint', async () => {
  const h = await harness(), anchor = h.camera.screenToWorld([600, 400]), initial = h.camera.snapshot.scale;
  h.event('pointerdown', 500, 400, {pointerType: 'touch'});
  h.event('pointerdown', 700, 400, {pointerId: 2, pointerType: 'touch'});
  const singlePoints = h.points.length;
  h.event('pointermove', 450, 420, {pointerType: 'touch'});
  samePoint(h.camera.screenToWorld([575, 410]), anchor);
  h.event('pointermove', 750, 440, {pointerId: 2, pointerType: 'touch'});
  samePoint(h.camera.screenToWorld([600, 430]), anchor);
  near(h.camera.snapshot.scale, initial * Math.hypot(300, 20) / 200);
  assert.equal(h.points.length, singlePoints);
  h.event('pointerup', 750, 440, {pointerId: 2, pointerType: 'touch'});
  const before = h.camera.snapshot; h.advance(16); h.event('pointermove', 460, 430, {pointerType: 'touch'});
  near(h.camera.snapshot.x, before.x - 10 / before.scale);
  h.event('pointerup', 460, 430, {pointerType: 'touch'}); h.advance(260);
  assert.equal(h.taps.length, 0); assert.deepEqual(h.lifecycle, ['start', 'end']);
});

test('third-pointer removal rebases pinch without jumping or creating a tap', async () => {
  const h = await harness();
  for (const [id, x] of [[1, 500], [2, 700], [3, 900]]) h.event('pointerdown', x, 400, {pointerId: id, pointerType: 'touch'});
  h.event('pointerup', 500, 400, {pointerType: 'touch'}); const before = h.camera.snapshot;
  h.event('pointermove', 700, 400, {pointerId: 2, pointerType: 'touch'});
  assert.deepEqual(h.camera.snapshot, before);
  h.event('pointerup', 700, 400, {pointerId: 2}); h.event('pointerup', 900, 400, {pointerId: 3});
  assert.equal(h.taps.length, 0);
});

test('3px drag, return-to-origin drag, cancellation and multitouch cannot become taps', async () => {
  for (const gesture of ['threshold', 'return', 'cancel', 'lost', 'multi', 'release-distance']) {
    const h = await harness(); h.event('pointerdown');
    if (gesture === 'threshold') h.event('pointermove', 603, 400);
    if (gesture === 'return') { h.event('pointermove', 620, 420); h.event('pointermove'); }
    if (gesture === 'cancel') h.event('pointercancel');
    if (gesture === 'lost') h.event('lostpointercapture');
    if (gesture === 'multi') { h.event('pointerdown', 650, 400, {pointerId: 2}); h.event('pointerup', 650, 400, {pointerId: 2}); }
    h.event('pointerup', gesture === 'release-distance' ? 620 : 600, 400);
    assert.equal(h.taps.length, 0, gesture);
  }
  const h = await harness(); h.event('pointerdown', 520, 350); h.event('pointerup', 521, 351);
  assert.equal(h.taps.length, 1); samePoint(h.taps[0], h.camera.screenToWorld([521, 351]));
  h.event('pointerdown', 600, 400, {button: 2}); h.event('pointerup', 600, 400, {button: 2});
  assert.equal(h.taps.length, 1); assert.equal(h.captured.size, 0);
});

test('navigation bounds add 25 percent on each side without changing map coordinates', async () => {
  const {navigationBounds} = await modulePromise;
  assert.deepEqual(navigationBounds(), {minX: -384, minY: -256, maxX: 1920, maxY: 1280, width: 2304, height: 1536});
  assert.deepEqual(navigationBounds(400, 200), {minX: -100, minY: -50, maxX: 500, maxY: 250, width: 600, height: 300});
});

test('both drag directions clamp every viewport edge to the expanded rectangle', async () => {
  for (const [width, height] of [[1440, 900], [390, 844]]) for (const sign of [-1, 1]) {
    const h = await harness(width, height, true); h.event('pointerdown', width / 2, height / 2);
    h.event('pointermove', sign * 10000, sign * 10000); h.event('pointerup', sign * 10000, sign * 10000);
    const s = h.camera.snapshot, a = h.camera.worldToScreen([-384, -256]), b = h.camera.worldToScreen([1920, 1280]);
    assert(a[0] <= 1e-8 && a[1] <= 1e-8 && b[0] >= width - 1e-8 && b[1] >= height - 1e-8);
    near(s.x, sign === 1 ? -384 + width / (2 * s.scale) : 1920 - width / (2 * s.scale));
    near(s.y, sign === 1 ? -256 + height / (2 * s.scale) : 1280 - height / (2 * s.scale));
  }
});

test('negative and beyond-map centers survive focus and zoom; inertia stays bounded', async () => {
  const h = await harness(), {camera} = h;
  for (const p of [[-200, -100], [1700, 1150]]) {
    camera.focus(p, 8); samePoint([camera.snapshot.x, camera.snapshot.y], p);
    camera.zoomBy(1.2); samePoint([camera.snapshot.x, camera.snapshot.y], p);
  }
  camera.focus([-200, -100], 8);
  h.event('pointerdown'); h.advance(16); h.event('pointermove', 10600, 10400);
  h.event('pointerup', 10600, 10400); h.advance(260);
  near(camera.snapshot.x, -384 + camera.snapshot.width / (2 * camera.snapshot.scale));
  near(camera.snapshot.y, -256 + camera.snapshot.height / (2 * camera.snapshot.scale));
  assert.equal(h.raf.size, 0);
});

test('fit contains artwork; focus restores cover bounds; resize preserves zoom relative to cover', async () => {
  const h = await harness(390, 844), {camera} = h;
  camera.zoomBy(1e-9); near(camera.snapshot.scale, 844 / 1024);
  camera.fit(); near(camera.snapshot.scale, 390 / 1536); samePoint([camera.snapshot.x, camera.snapshot.y], [768, 512]);
  h.rect.width = 800; h.rect.height = 600; camera.resize(); near(camera.snapshot.scale, 800 / 1536);
  camera.focus([500, 500], 2); near(camera.snapshot.scale, 2); samePoint([camera.snapshot.x, camera.snapshot.y], [500, 500]);
  camera.zoomBy(2); near(camera.snapshot.scale, 4);
  h.rect.width = 1200; h.rect.height = 900; camera.resize(); near(camera.snapshot.scale, 6);
  camera.focus([-9999, 9999], 1e-9); near(camera.snapshot.scale, 900 / 1024);
});

test('interruption, blur and destroy settle callbacks and remove captures/listeners/timers', async () => {
  const h = await harness(); h.event('pointerdown'); h.advance(16); h.event('pointermove', 620, 420);
  h.event('pointerup', 620, 420); h.event('pointerdown'); assert.equal(h.raf.size, 0);
  h.view.emit('blur'); assert.equal(h.captured.size, 0); h.event('pointerup'); assert.equal(h.taps.length, 0);
  h.event('wheel', 600, 400, {deltaY: -20}); h.camera.destroy();
  assert.equal(h.timers.size, 0); assert.equal(h.raf.size, 0); assert.equal(h.canvas.style.touchAction, 'auto');
  for (const t of [h.canvas, h.view, h.media]) for (const set of t.events.values()) assert.equal(set.size, 0);
  const before = h.camera.snapshot; h.camera.zoomBy(2); h.camera.resize(); h.camera.fit(); h.camera.destroy();
  assert.deepEqual(h.camera.snapshot, before);
  assert.deepEqual(h.lifecycle, ['start', 'end', 'start', 'end']);
});

test('Chrome native pointer capture pans a fixed canvas and wheel preserves its world anchor',
  {skip: !process.env.ATLAS_CAMERA_BROWSER}, async () => {
    const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
    const browser = await chromium.launch({channel: 'chrome', headless: true});
    try {
      for (const width of [1440, 390]) {
        const page = await browser.newPage({viewport: {width, height: 900}});
        await page.setContent('<style>html,body{margin:0;overflow:hidden}canvas{position:fixed;inset:0;width:100%;height:100%}</style><canvas></canvas>');
        await page.evaluate(async moduleSource => {
          const {createCamera} = await import('data:text/javascript;base64,' + btoa(moduleSource));
          const canvas = document.querySelector('canvas');
          window.camera = createCamera(canvas, {
            onMoveStart() { window.ends = 0; }, onMoveEnd() { window.ends++; },
            onTap() { window.taps++; },
            onChange(s) {
              canvas.width = s.width; canvas.height = s.height;
              const ctx = canvas.getContext('2d');
              ctx.fillStyle = '#78a855'; ctx.fillRect(0, 0, s.width, s.height);
              ctx.fillStyle = '#126ed0';
              ctx.fillRect((460 - s.x) * s.scale + s.width / 2, (400 - s.y) * s.scale + s.height / 2,
                140 * s.scale, 200 * s.scale);
            }
          });
          window.taps = 0; window.ends = 0;
        }, source);
        const read = () => page.evaluate(() => ({snapshot: window.camera.snapshot, ends: window.ends, taps: window.taps,
          rect: document.querySelector('canvas').getBoundingClientRect().toJSON(),
          pixels: document.querySelector('canvas').toDataURL()}));
        const before = await read();
        await page.mouse.move(width / 2, 450); await page.mouse.down();
        await page.mouse.move(width / 2 + 50, 500, {steps: 5}); await page.mouse.up();
        await page.waitForTimeout(300); const after = await read();
        assert(after.snapshot.x < before.snapshot.x && after.snapshot.y < before.snapshot.y);
        assert.equal(after.taps, 0); assert.equal(after.ends, 1);
        assert.deepEqual(after.rect, before.rect); assert.notEqual(after.pixels, before.pixels);
        await page.mouse.move(width / 2, 450);
        const anchor = await page.evaluate(() => window.camera.screenToWorld([innerWidth / 2, 450]));
        await page.mouse.wheel(0, -100); await page.waitForTimeout(160);
        samePoint(await page.evaluate(() => window.camera.screenToWorld([innerWidth / 2, 450])), anchor);
        await page.close();
      }
    } finally { await browser.close(); }
  });

test('character tracking centers without starting or ending a user gesture', async () => {
  const h = await harness();
  h.camera.track([600, 500]);
  samePoint(h.camera.worldToScreen([600, 500]), [600, 400]);
  assert.deepEqual(h.lifecycle, []);
  const changes = h.changes.length;
  h.camera.track([600, 500]); assert.equal(h.changes.length, changes);
  h.camera.track([NaN, 5]); assert.equal(h.changes.length, changes);
});

test('tracking eases toward character and converges without gesture callbacks', async()=>{
 const h=await harness(), before=h.camera.snapshot;
 assert.equal(h.camera.track([800,600],.25),true);
 near(h.camera.snapshot.x,before.x+(800-before.x)*.25);
 for(let n=0;n<100;n++)h.camera.track([800,600],.25);
 samePoint([h.camera.snapshot.x,h.camera.snapshot.y],[800,600]);
 assert.equal(h.camera.track([800,600],.25),false);assert.deepEqual(h.lifecycle,[]);
});

test('tracking unreachable edge converges and stops publishing unchanged frames',async()=>{
 const h=await harness();h.camera.fit();
 for(let n=0;n<100;n++)h.camera.track([-10000,-10000],.25);
 const count=h.changes.length;
 assert.equal(h.camera.track([-10000,-10000],.25),false);
 assert.equal(h.changes.length,count);
});
