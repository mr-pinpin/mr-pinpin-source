import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {seal, open} from './protocol.mjs';
import {serve, executeAction} from './helper.mjs';
import {request} from './channel.mjs';
const key = 'ab'.repeat(32), config = {key, pair:'test-pair'};
test('encryption binds direction, identity and lifetime; tampering and stale requests fail', () => {
  const envelope = seal(key, 'pair/requests', {action:'ping'}, 1000, 1000);
  assert.deepEqual(open(key, 'pair/requests', envelope, 1500), {action:'ping'});
  for (const [context,value,now] of [
    ['pair/responses',envelope,1500], ['pair/requests',{...envelope, expiresAt:2500},1500],
    ['pair/requests',envelope,2000], ['pair/requests',{...envelope,id:'other'},1500],
  ]) assert.throws(() => open(key, context, value, now));
  assert.throws(() => seal(key, 'x', {data:'x'.repeat(40000)}));
});
function mockChannel() {
  const callbacks = new Map(), writes = [];
  return {writes,
    listen(direction, callback) {callbacks.set(direction,callback); return () => callbacks.delete(direction);},
    async send(direction, value) {writes.push([direction,value]); await callbacks.get(direction)?.(value.id,value);},
    async remove() {},
    deliver(direction, value) {return callbacks.get(direction)?.(value.id,value);}
  };
}
test('round trip subscribes before send and duplicate delivery never executes twice, including restart', async () => {
  const stateDir = await mkdtemp(join(tmpdir(),'pinpin-recovery-'));
  try {
    const channel = mockChannel();
    let stop = await serve(channel, config, stateDir);
    assert.equal((await request(channel, config, {action:'ping'})).ok, true);
    const envelope = channel.writes.find(([d]) => d === 'requests')[1];
    await channel.deliver('requests', envelope);
    assert.equal(channel.writes.filter(([d]) => d === 'responses').length, 1);
    stop(); stop = await serve(channel, config, stateDir);
    await channel.deliver('requests', envelope);
    assert.equal(channel.writes.filter(([d]) => d === 'responses').length, 1);
    stop();
  } finally {await rm(stateDir,{recursive:true,force:true});}
});
test('stale queued writes and ciphertext substitution cannot invoke actions', async () => {
  const dir = await mkdtemp(join(tmpdir(),'pinpin-recovery-'));
  try {
    const channel = mockChannel(); await serve(channel,config,dir);
    await channel.deliver('requests',seal(key,`${config.pair}/requests`,{action:'ping'},Date.now()-2000,1000));
    await channel.deliver('requests',seal(key,`${config.pair}/responses`,{action:'ping'}));
    assert.equal(channel.writes.length,0);
  } finally {await rm(dir,{recursive:true,force:true});}
});
test('remote arguments and unknown actions are rejected; timeout reports uncertain execution', async () => {
  assert.throws(() => executeAction({}, {action:'shell'},1000));
  assert.throws(() => executeAction({}, {action:'ping',args:['bad']},1000));
  await assert.rejects(request(mockChannel(),config,{action:'ping'},10), /outcome may be unknown/);
});
