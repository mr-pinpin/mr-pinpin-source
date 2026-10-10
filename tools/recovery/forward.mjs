import net from 'node:net';
import {writeFile,realpath} from 'node:fs/promises';
import {join,dirname,basename} from 'node:path';
import {connectTCP, firebaseTunnel} from './tunnel.mjs';

export function createForwarder(config, getChannel, report = () => {}) {
  const sockets = new Set();
  const server = net.createServer({allowHalfOpen:true,highWaterMark:12000}, async socket => {
    sockets.add(socket); socket.pause();
    socket.on('error',() => {});
    socket.once('close',() => sockets.delete(socket));
    try {
      let direct;
      if (config.primaryHost) {
        try {direct = await connectTCP(config.primaryHost, config.primaryPort ?? 22, config.connectTimeoutMs ?? 2000);}
        catch {report('Primary unavailable; using Firebase');}
      }
      if (socket.destroyed) {direct?.destroy(); return;}
      if (direct) {
        sockets.add(direct); direct.once('close',() => sockets.delete(direct));
        direct.on('error',() => socket.destroy()); socket.on('error',() => direct.destroy());
        socket.once('close',() => direct.destroy()); direct.once('close',() => socket.destroy());
        socket.pipe(direct); direct.pipe(socket); socket.resume(); direct.resume();
        report('Connected through primary route');
      } else {
        await firebaseTunnel(await getChannel(),config,socket);
        report('Connected through Firebase');
      }
    } catch {report('Fallback connection failed'); socket.destroy();}
  });
  server.on('listening', async () => {
    if (!process.env.PINPIN_CLIENT_CURRENT) return;
    try {
      const root = await realpath(process.env.PINPIN_CLIENT_CURRENT);
      await writeFile(join(dirname(process.env.PINPIN_CLIENT_CURRENT),'loaded-version'),basename(root));
    } catch {report('Client version marker unavailable');}
  });
  return {server, retire() {server.close();}, close() {for (const socket of sockets) socket.destroy(); server.close();}};
}
