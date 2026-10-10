import test from 'node:test';
import assert from 'node:assert/strict';
import net from 'node:net';
import {randomBytes} from 'node:crypto';
import {mkdtemp, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {serve} from './helper.mjs';
import {createForwarder} from './forward.mjs';

export function memoryChannel() {
  const watchers = new Map(), retained = new Map();
  return {
    listen(path,callback) {
      if (!watchers.has(path)) watchers.set(path,new Set());
      watchers.get(path).add(callback);
      for (const [id,value] of retained.get(path) || []) queueMicrotask(() => callback(id,value));
      return () => watchers.get(path)?.delete(callback);
    },
    async send(path,value) {
      if (!retained.has(path)) retained.set(path,new Map());
      retained.get(path).set(value.id,value);
      for (const callback of watchers.get(path) || []) queueMicrotask(() => callback(value.id,value));
    },
    async remove(path,id) {retained.get(path)?.delete(id);}
  };
}
const listen = server => new Promise(resolve => server.listen(0,'127.0.0.1',() => resolve(server.address().port)));
async function exchange(port,body) {
  const socket = net.connect(port,'127.0.0.1');
  const received = [];
  try {
    return await new Promise((resolve,reject) => {
      const timer = setTimeout(() => {socket.destroy(); reject(Error('Exchange timeout'));},5000);
      socket.on('error',error => {clearTimeout(timer); reject(error);});
      socket.on('data',data => {
        received.push(data);
        if (received.reduce((n,b) => n+b.length,0) === body.length) {clearTimeout(timer); resolve(Buffer.concat(received));}
      });
      socket.on('connect',() => socket.write(body));
    });
  } finally {socket.destroy();}
}

test('unavailable primary falls back and carries binary SSH-sized traffic bidirectionally', async () => {
  const peers = new Set();
  const echo = net.createServer(socket => {peers.add(socket);socket.on('error',() => {});socket.on('close',() => peers.delete(socket));socket.pipe(socket);});
  const sshPort = await listen(echo);
  const dir = await mkdtemp(join(tmpdir(),'pinpin-tunnel-'));
  const channel = memoryChannel();
  const config = {pair:'test',key:'cd'.repeat(32),sshPort,primaryHost:'127.0.0.1',primaryPort:1};
  const stop = await serve(channel,config,dir);
  const routes = [], forward = createForwarder(config,async () => channel,message => routes.push(message));
  const port = await listen(forward.server);
  try {
    const body = randomBytes(256000);
    assert.deepEqual(await exchange(port,body),body);
    assert.ok(routes.includes('Connected through Firebase'));
  } finally {
    forward.close(); stop(); for (const socket of peers) socket.destroy(); echo.close();
    await rm(dir,{recursive:true,force:true});
  }
});
test('working primary route remains usable when Firebase is completely unavailable', async () => {
  const echo = net.createServer(socket => {socket.on('error',() => {});socket.pipe(socket);});
  const port = await listen(echo);
  let called = false;
  const forward = createForwarder({primaryHost:'127.0.0.1',primaryPort:port},async () => {called = true; throw Error('Firebase offline');});
  try {
    assert.deepEqual(await exchange(await listen(forward.server),Buffer.from('SSH-2.0-test\r\n')),Buffer.from('SSH-2.0-test\r\n'));
    assert.equal(called,false);
  } finally {forward.close();echo.close();}
});
