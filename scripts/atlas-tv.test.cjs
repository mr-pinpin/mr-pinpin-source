const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname,'../docs/storyboard/atlas-tv.js'),'utf8');
const modulePromise = import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
function target(extra={}) { const listeners={};return Object.assign({addEventListener(n,f){listeners[n]=f;},removeEventListener(n){delete listeners[n];},emit(n,e){listeners[n]?.(e);}},extra); }
test('TV five-way keys aim before Enter; mouse hover never activates',async()=>{
 const {createTVControls}=await modulePromise;
 const cursor={style:{},setAttribute(){},remove(){}};
 const view=target({PointerEvent:function(){}}),doc=target({defaultView:view,createElement:()=>cursor});
 let focused=0,blocked=false;const calls=[];
 const canvas=target({ownerDocument:doc,getBoundingClientRect:()=>({left:10,top:20,width:1000,height:600}),focus(){focused++;}});
 const control=createTVControls({canvas,viewport:{append(){}},camera:{screenToWorld:p=>p.map(v=>v/2)},activate:p=>calls.push(p),blocked:()=>blocked});
 const event=key=>({key,preventDefault(){},stopImmediatePropagation(){}});
 assert.deepEqual(control.point,[500,300]);
 doc.emit('keydown',event('ArrowRight'));assert.deepEqual(control.point,[536,300]);assert.equal(calls.length,0);
 doc.emit('keydown',{...event('Unidentified'),keyCode:13});assert.deepEqual(calls,[[268,150]]);
 canvas.emit('mousemove',{clientX:110,clientY:220});assert.deepEqual(control.point,[100,200]);assert.equal(calls.length,1);
 blocked=true;doc.emit('keydown',event('Enter'));assert.equal(calls.length,1);
 blocked=false;doc.emit('keydown',{...event('Enter'),target:{closest:()=>true}});assert.equal(calls.length,1);
 assert(focused>=2);control.destroy();
});

const path = require('node:path');
const vm = require('node:vm');
function presentationTarget() {
  const handlers = new Map();
  return {
    handlers,
    addEventListener(name, fn) { if (!handlers.has(name)) handlers.set(name, new Set()); handlers.get(name).add(fn); },
    removeEventListener(name, fn) { handlers.get(name)?.delete(fn); },
    emit(name, fields = {}) {
      const event = {preventDefault() {}, stopImmediatePropagation() {}, ...fields};
      for (const fn of handlers.get(name) || []) fn(event);
    }
  };
}

async function harness(showPointer, modernPointer = false) {
  const {createTVControls} = await modulePromise;
  const view = Object.assign(presentationTarget(), {PointerEvent: modernPointer ? function PointerEvent() {} : null});
  const children = [], created = [], activations = [];
  const doc = Object.assign(presentationTarget(), {defaultView: view, createElement() {
    const element = {style: {}, setAttribute() {}, remove() { children.splice(children.indexOf(element), 1); }};
    created.push(element); return element;
  }});
  const canvas = Object.assign(presentationTarget(), {ownerDocument: doc, focus() {},
    getBoundingClientRect: () => ({left: 10, top: 20, width: 400, height: 200})});
  let blocked = false, wheels = 0;
  canvas.addEventListener('wheel', () => wheels++);
  const options = {canvas, viewport: {append(element) { children.push(element); }},
    camera: {screenToWorld: point => point.map(value => value * 2)},
    activate: point => activations.push(point), blocked: () => blocked};
  if (showPointer !== undefined) options.showPointer = showPointer;
  const controls = createTVControls(options);
  return {canvas, doc, view, children, created, activations, controls,
    key(key, extra = {}) { doc.emit('keydown', {key, ...extra}); },
    block(value) { blocked = value; controls.refresh(); },
    get wheels() { return wheels; }};
}

test('standalone pages retain their pointer; only an exact explicit stream opt-out uses the native pointer', async () => {
  const {usesNativeCursor} = await modulePromise;
  for (const query of ['', '?tv=1', '?tv=1&nativeCursor=1', '?tv=1&renderSession=1',
    '?tv=1&renderSession=1&nativeCursor=0', '?renderSession=1&nativeCursor=true',
    '?renderSession=0&nativeCursor=1', '?renderSession=1&nativeCursor=01']) {
    assert.equal(usesNativeCursor('https://example.test/atlas' + query), false, query);
  }
  assert.equal(usesNativeCursor('https://example.test/atlas?tv=1&renderSession=1&nativeCursor=1'), true);
  const h = await harness();
  assert.equal(h.children.length, 1);
  assert.equal(h.children[0].className, 'atlas-tv-cursor');
  h.controls.destroy(); assert.equal(h.children.length, 0);
});

test('the actual Atlas initializer passes the explicit native cursor choice to its existing controls', async () => {
  const {usesNativeCursor} = await modulePromise;
  const atlas = fs.readFileSync(path.join(__dirname, '../docs/storyboard/atlas-webgpu.js'), 'utf8');
  const start = atlas.indexOf('const tvControls = tvMode ? createTVControls(');
  const end = atlas.indexOf(' : null;', start) + ' : null;'.length;
  assert(start >= 0 && end > start);
  for (const [query, expected] of [['?tv=1', true], ['?tv=1&nativeCursor=1', true],
    ['?tv=1&renderSession=1&nativeCursor=1', false]]) {
    let received;
    vm.runInNewContext(atlas.slice(start, end), {tvMode: true, usesNativeCursor,
      createTVControls(options) { received = options; }, location: {href: 'https://example.test/' + query},
      canvas: {}, viewport: {}, camera: {}, tap() {}});
    assert.equal(received.showPointer, expected, query);
  }
});

for (const showPointer of [true, false]) {
  test(`pointer presentation ${showPointer} preserves keyboard, mouse activation, wheel and teardown`, async () => {
    const h = await harness(showPointer);
    assert.equal(h.children.length, showPointer ? 1 : 0);
    assert.deepEqual(h.controls.point, [200, 100]);
    h.key('ArrowRight'); h.key('ArrowDown', {repeat: true});
    assert.deepEqual(h.controls.point, [236, 124]);
    h.key('Enter'); assert.deepEqual(h.activations, [[472, 248]]);
    h.canvas.emit('mousemove', {clientX: 60, clientY: 80});
    assert.deepEqual(h.controls.point, [50, 60]);
    h.canvas.emit('click', {clientX: 80, clientY: 90});
    assert.deepEqual(h.activations[1], [140, 140]);
    h.canvas.emit('wheel', {deltaY: 2}); assert.equal(h.wheels, 1);
    h.block(true); h.key('Enter');
    assert.equal(h.activations.length, 2);
    if (showPointer) assert.equal(h.children[0].hidden, true);
    h.controls.destroy();
    h.key('Enter'); h.canvas.emit('click', {clientX: 80, clientY: 90});
    assert.equal(h.activations.length, 2);
    assert.equal(h.children.length, 0);
    h.canvas.emit('wheel'); assert.equal(h.wheels, 2);
  });
}

test('hiding the circle does not add duplicate activation on modern pointer browsers', async () => {
  const h = await harness(false, true);
  h.canvas.emit('click', {clientX: 70, clientY: 90});
  assert.equal(h.activations.length, 0);
  h.key('Enter'); assert.equal(h.activations.length, 1);
  h.controls.destroy();
});
