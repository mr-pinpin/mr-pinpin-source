import {pathToFileURL} from 'node:url';
import {join} from 'node:path';
import {readFile, realpath} from 'node:fs/promises';
import {connect, request} from './channel.mjs';
import {serve} from './helper.mjs';
import {createForwarder} from './forward.mjs';

const [mode, configPath, action = 'ping'] = process.argv.slice(2);
if (!['helper','request','forward'].includes(mode) || !configPath) {
  console.error('Usage: node cli.mjs helper|request|forward /absolute/private/config.json [action]');
  process.exitCode = 1;
} else {
  let channel, pendingChannel, forwarder, stopHelper;
  const forwarders = [], channels = [];
  try {
    const config = JSON.parse(await readFile(configPath, 'utf8'));
    const getChannel = async () => {
      if (!pendingChannel) pendingChannel = (async () => {
        const token = config.tokenFile ? await readFile(config.tokenFile,'utf8') : undefined;
        channel = await connect(config,token);
        channels.push(channel);
        return channel;
      })().catch(error => {pendingChannel = null; throw error;});
      return pendingChannel;
    };
    if (mode === 'request') {
      console.log(JSON.stringify(await request(await getChannel(),config,{action})));
      await channel.close();
    } else {
      if (mode === 'forward') {
        const port = config.listenPort ?? 18822;
        if (!Number.isInteger(port) || port < 1 || port > 65535) throw Error('Invalid forward port');
        forwarder = createForwarder(config,getChannel,message => console.error(message));
        await new Promise((resolve,reject) => {
          forwarder.server.once('error',reject);
          forwarder.server.listen(port,'127.0.0.1',resolve);
        });
        forwarders.push(forwarder);
        let reloading = false;
        process.on('SIGHUP', async () => {
          if (reloading || !process.env.PINPIN_CLIENT_CURRENT) return;
          reloading = true;
          let replacement;
          try {
            const root = await realpath(process.env.PINPIN_CLIENT_CURRENT);
            const freshForward = await import(pathToFileURL(join(root,'forward.mjs')).href);
            const freshChannel = await import(pathToFileURL(join(root,'channel.mjs')).href);
            let freshPending;
            const getFreshChannel = () => {
              if (!freshPending) freshPending = (async () => {
                const token = config.tokenFile ? await readFile(config.tokenFile,'utf8') : undefined;
                const connection = await freshChannel.connect(config,token);
                channels.push(connection); return connection;
              })().catch(error => {freshPending = null; throw error;});
              return freshPending;
            };
            replacement = freshForward.createForwarder(config,getFreshChannel,message => console.error(message));
            // Retire the listener, keeping its established SSH sockets alive.
            forwarder.retire();
            await new Promise(resolve => setTimeout(resolve,50));
            await new Promise((resolve,reject) => {
              replacement.server.once('error',reject);
              replacement.server.listen(port,'127.0.0.1',resolve);
            });
            forwarder = replacement; forwarders.push(forwarder);
            console.error('Custom transport reloaded; existing SSH sessions retained');
          } catch {
            replacement?.close();
            console.error('Custom transport reload failed; restarting listener');
            try {forwarder.server.listen(port,'127.0.0.1');} catch {}
          } finally {reloading = false;}
        });
        console.error(`SSH fallback listening on 127.0.0.1:${port}`);
      } else {
        stopHelper = await serve(await getChannel(),config,config.stateDir,config.actions || {});
        channel.status(connected => console.error(connected ? 'Recovery connected' : 'Recovery disconnected; reconnecting'));
      }
      for (const signal of ['SIGINT','SIGTERM']) process.once(signal,async () => {
        for (const active of forwarders) active.close(); stopHelper?.(); for (const connection of channels) await connection.close(); process.exit(0);
      });
    }
  } catch {
    console.error('Recovery startup or request failed; check private configuration and connectivity');
    forwarder?.close(); stopHelper?.(); if (channel) await channel.close(); process.exitCode = 1;
  }
}
