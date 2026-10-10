import {mkdir, writeFile} from 'node:fs/promises';
import {join, isAbsolute} from 'node:path';
import {execFile} from 'node:child_process';
import {openHelperTunnel} from './tunnel.mjs';
import {open, seal} from './protocol.mjs';

export function executeAction(actions, payload, remainingMs) {
  if (!payload || typeof payload !== 'object' || typeof payload.action !== 'string' || Object.keys(payload).some(k => k !== 'action')) throw Error('Invalid action');
  if (payload.action === 'ping') return Promise.resolve({ok:true, time:Date.now()});
  const action = Object.hasOwn(actions, payload.action) ? actions[payload.action] : null;
  if (!action || !isAbsolute(action.command) || !Array.isArray(action.args) || !action.args.every(x => typeof x === 'string')) throw Error('Action is not configured');
  // No remote shell strings, arguments, environment overrides or working directories.
  return new Promise(resolve => execFile(action.command, action.args, {
    timeout:Math.min(remainingMs, 10000), maxBuffer:8192, encoding:'utf8',
    env:{PATH:'/usr/bin:/bin:/usr/sbin:/sbin', HOME:process.env.HOME},
  }, error => resolve({ok:!error, action:payload.action})));
}

export async function serve(channel, config, stateDir, actions = {}) {
  if (!isAbsolute(stateDir)) throw Error('Replay state directory must be absolute');
  await mkdir(stateDir, {recursive:true, mode:0o700});
  let busy = false;
  const active = new Map();
  const unsubscribe = channel.listen('requests', async (id, envelope) => {
    let payload;
    try {
      if (id !== envelope?.id) return;
      payload = open(config.key, `${config.pair}/requests`, envelope);
    } catch {return;}
    // Reject rather than queue work beyond its deadline. Replayed work is never run.
    if (busy) return;
    busy = true;
    try {
      try {await writeFile(join(stateDir, id), '', {flag:'wx', mode:0o600});}
      catch (error) {if (error.code === 'EEXIST') return; throw error;}
      const remaining = envelope.expiresAt - Date.now();
      if (remaining <= 0) return;
      let result;
      try {result = payload?.action === 'ssh'
        ? await openHelperTunnel(channel, config, payload, active)
        : await executeAction(actions, payload, remaining);}
      catch {result = {ok:false, error:'Action rejected'};}
      if (Date.now() >= envelope.expiresAt) return;
      const response = seal(config.key, `${config.pair}/responses`, result, Date.now(),
        envelope.expiresAt - Date.now(), id);
      await channel.send('responses', response);
    } catch {console.error('Recovery request failed; outcome may be unknown');}
    finally {busy = false;}
  }, () => console.error('Recovery subscription denied; check database access'));
  return () => {unsubscribe(); for (const socket of active.values()) socket.destroy();};
}
