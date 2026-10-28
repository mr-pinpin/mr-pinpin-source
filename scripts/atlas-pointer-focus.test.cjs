const test=require('node:test'),assert=require('node:assert/strict');
test('mouse lens tracks the world under a stationary screen pointer across zoom and pan',async()=>{
  const {createPointerFocus}=await import('../docs/storyboard/atlas-pointer-focus.mjs');
  const lens=createPointerFocus(),canvas={getBoundingClientRect:()=>({left:10,top:20,width:100,height:100})};
  let scale=1,pan=0;const camera={screenToWorld:([x,y])=>[pan+x/scale,y/scale]};
  assert.equal(lens.update({pointerType:'mouse',clientX:30,clientY:40}),true);
  assert.deepEqual(lens.world(camera,canvas),[20,20]);scale=2;pan=50;
  assert.deepEqual(lens.world(camera,canvas),[60,10]);
  lens.clear();assert.equal(lens.world(camera,canvas),null);
});
test('touch does not opt into the mouse lens and out-of-canvas mouse positions do not focus',async()=>{
  const {createPointerFocus}=await import('../docs/storyboard/atlas-pointer-focus.mjs');
  const lens=createPointerFocus(),canvas={getBoundingClientRect:()=>({left:0,top:0,width:100,height:100})},camera={screenToWorld:p=>p};
  assert.equal(lens.update({pointerType:'touch',clientX:30,clientY:40}),false);
  assert.equal(lens.world(camera,canvas),null);
  lens.update({pointerType:'mouse',clientX:101,clientY:40});assert.equal(lens.world(camera,canvas),null);
});
