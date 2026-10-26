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
