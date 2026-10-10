import net from 'node:net';
import {randomUUID} from 'node:crypto';
import {open, seal, validId} from './protocol.mjs';
import {request} from './channel.mjs';

const CHUNK = 12000, WINDOW = 8;
const TIMEOUT = 20000;
export function attachStream(channel, config, session, role, socket) {
  if (!validId(session) || !['client','helper'].includes(role)) throw Error('Invalid tunnel session');
  const root = `sessions/${session}`;
  const outgoing = `${root}/${role === 'client' ? 'c2h' : 'h2c'}`;
  const incoming = `${root}/${role === 'client' ? 'h2c' : 'c2h'}`;
  const outgoingAck = `${outgoing}-acks`, incomingAck = `${incoming}-acks`;
  let sendSeq = 0, recvSeq = 0, closed = false, ended = false;
  const pending = new Map(), reorder = new Map(), unsubscribers = [];
  const context = direction => `${config.pair}/${direction}`;
  const updateFlow = () => pending.size >= WINDOW ? socket.pause() : socket.resume();
  function cleanup(error) {
    if (closed) return;
    closed = true;
    for (const stop of unsubscribers) stop();
    for (const {timer,id} of pending.values()) {
      clearTimeout(timer); channel.remove(outgoing,id).catch(() => {});
    }
    pending.clear();
    socket.destroy(error);
  }
  function send(payload) {
    if (closed) return;
    const seq = sendSeq++, id = String(seq).padStart(12,'0');
    const packet = seal(config.key, context(outgoing), {seq,...payload}, Date.now(),TIMEOUT,id);
    const timer = setTimeout(() => cleanup(Error('Firebase tunnel acknowledgement timed out')), TIMEOUT);
    pending.set(seq,{timer,id}); updateFlow();
    channel.send(outgoing,packet).catch(() => cleanup(Error('Firebase tunnel write failed')));
  }
  unsubscribers.push(channel.listen(outgoingAck,(id,value) => {
    try {
      if (id !== value?.id) throw Error('Invalid acknowledgement ID');
      const ack = open(config.key,context(outgoingAck),value);
      const entry = pending.get(ack.seq);
      if (!entry || id !== entry.id) return;
      clearTimeout(entry.timer); pending.delete(ack.seq);
      channel.remove(outgoing,entry.id).catch(() => {});
      channel.remove(outgoingAck,id).catch(() => {});
      updateFlow();
    } catch {cleanup(Error('Invalid Firebase tunnel acknowledgement'));}
  }, () => cleanup(Error('Firebase tunnel acknowledgement subscription failed'))));
  unsubscribers.push(channel.listen(incoming,(id,value) => {
    try {
      if (id !== value?.id) throw Error('Invalid packet ID');
      const packet = open(config.key,context(incoming),value);
      if (!Number.isSafeInteger(packet.seq) || packet.seq < 0 || id !== String(packet.seq).padStart(12,'0') ||
          !['data','end'].includes(packet.type) || packet.seq >= recvSeq + WINDOW * 4) throw Error('Invalid packet sequence');
      if (packet.seq < recvSeq) return;
      if (packet.type === 'data' && (typeof packet.data !== 'string' || packet.data.length > CHUNK * 4/3)) throw Error('Invalid packet size');
      reorder.set(packet.seq,{packet,id});
      while (reorder.has(recvSeq)) {
        const {packet:next,id:nextId} = reorder.get(recvSeq); reorder.delete(recvSeq);
        if (ended) throw Error('Data after end');
        const acknowledge = () => {
          if (closed) return;
          channel.send(incomingAck,seal(config.key,context(incomingAck),{seq:next.seq},Date.now(),TIMEOUT,nextId))
            .catch(() => cleanup(Error('Firebase tunnel acknowledgement failed')));
        };
        recvSeq++;
        if (next.type === 'end') {ended = true; socket.end(acknowledge);}
        else socket.write(Buffer.from(next.data,'base64'),acknowledge);
      }
    } catch {cleanup(Error('Invalid Firebase tunnel packet'));}
  }, () => cleanup(Error('Firebase tunnel subscription failed'))));
  socket.on('data',data => {
    // Node stream chunks can exceed the window; cap source highWaterMark at CHUNK.
    for (let offset = 0; offset < data.length; offset += CHUNK) send({type:'data',data:data.subarray(offset,offset+CHUNK).toString('base64')});
  });
  socket.on('end',() => send({type:'end'}));
  socket.on('error',() => cleanup());
  socket.on('close',() => cleanup());
  updateFlow();
  return () => cleanup();
}

export function connectTCP(host, port, timeout = 3000) {
  return new Promise((resolve,reject) => {
    const socket = net.createConnection({host,port,allowHalfOpen:true,highWaterMark:CHUNK});
    socket.pause();
    const timer = setTimeout(() => socket.destroy(Error('TCP connect timeout')),timeout);
    socket.once('error',error => {clearTimeout(timer); reject(error);});
    socket.once('connect',() => {clearTimeout(timer); resolve(socket);});
  });
}

// Called only after encrypted and replay-checked control request validation.
export async function openHelperTunnel(channel, config, payload, active) {
  if (!validId(payload.session) || Object.keys(payload).some(k => !['action','session'].includes(k))) throw Error('Invalid tunnel request');
  if (active.size >= 4 || active.has(payload.session)) throw Error('Tunnel capacity reached');
  const port = config.sshPort ?? 22;
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw Error('Invalid local SSH port');
  const socket = await connectTCP('127.0.0.1',port);
  active.set(payload.session,socket);
  socket.once('close',() => active.delete(payload.session));
  const idle = setTimeout(() => socket.destroy(), 15000);
  socket.once('data',() => clearTimeout(idle));
  socket.once('close',() => clearTimeout(idle));
  attachStream(channel,config,payload.session,'helper',socket);
  return {ok:true,session:payload.session};
}

export async function firebaseTunnel(channel, config, socket) {
  const session = randomUUID();
  socket.pause();
  const stop = attachStream(channel,config,session,'client',socket);
  socket.pause();
  try {
    const response = await request(channel,config,{action:'ssh',session});
    if (!response.ok || response.session !== session) throw Error('Remote SSH tunnel unavailable');
    socket.resume();
    return stop;
  } catch (error) {stop(); throw error;}
}
