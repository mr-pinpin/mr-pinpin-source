import {initializeApp, deleteApp} from 'firebase/app';
import {getAuth, signInWithCustomToken} from 'firebase/auth';
import {getDatabase, forceWebSockets, ref, set, remove, onChildAdded, onValue, goOffline} from 'firebase/database';
import {validId, seal, open} from './protocol.mjs';

export const DATABASE_URL = 'https://signaling-dcfad-default-rtdb.europe-west1.firebasedatabase.app';
export async function connect(config, token) {
  if (!validId(config.pair)) throw Error('A valid pairing ID is required');
  seal(config.key, `${config.pair}/validation`, {action:'ping'});
  forceWebSockets();
  const app = initializeApp({apiKey:config.apiKey, databaseURL:DATABASE_URL}, `recovery-${crypto.randomUUID()}`);
  try {
    if (token) {
      const auth = getAuth(app);
      await signInWithCustomToken(auth, token.trim());
    }
    const db = getDatabase(app);
    const path = direction => `pinpinRecovery/v1/${config.pair}/${direction}`;
    const unsubscribers = new Set();
    let closed = false;
    return {
      async send(direction, envelope) { if (closed) throw Error('Channel closed'); return set(ref(db, `${path(direction)}/${envelope.id}`), envelope); },
      async remove(direction, id) { if (closed) return; return remove(ref(db, `${path(direction)}/${id}`)); },
      listen(direction, callback, onError) {
        const unsubscribe = onChildAdded(ref(db, path(direction)), snapshot => callback(snapshot.key, snapshot.val()), onError);
        unsubscribers.add(unsubscribe);
        return () => {unsubscribers.delete(unsubscribe); unsubscribe();};
      },
      status(callback) {const stop = onValue(ref(db, '.info/connected'), s => callback(s.val() === true)); unsubscribers.add(stop); return stop;},
      async close() {if (closed) return; closed = true; for (const stop of unsubscribers) stop(); goOffline(db); await deleteApp(app);}
    };
  } catch (error) {await deleteApp(app); throw error;}
}

// Listener precedes write so a fast helper cannot race the response subscription.
export function request(channel, config, payload, timeoutMs = 15000) {
  const context = `${config.pair}/requests`;
  const envelope = seal(config.key, context, payload, Date.now(), timeoutMs);
  return new Promise((resolve, reject) => {
    let done = false, stop = () => {}, timer;
    const finish = (error, value) => {
      if (done) return;
      done = true; clearTimeout(timer); stop();
      // SDK may queue cleanup until reconnection. The envelope still expires.
      channel.remove('requests', envelope.id).catch(() => {});
      channel.remove('responses', envelope.id).catch(() => {});
      error ? reject(error) : resolve(value);
    };
    stop = channel.listen('responses', (id, value) => {
      if (id !== envelope.id) return;
      try {
        if (value.id !== id) throw Error('Response ID mismatch');
        const result = open(config.key, `${config.pair}/responses`, value);
        finish(null, result);
      } catch {finish(Error('Invalid recovery response'));}
    }, () => finish(Error('Recovery subscription denied')));
    timer = setTimeout(() => finish(Error('Recovery request timed out; execution outcome may be unknown')), timeoutMs);
    channel.send('requests', envelope).catch(() => finish(Error('Recovery request write failed')));
  });
}
