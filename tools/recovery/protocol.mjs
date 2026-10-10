import {randomUUID, randomBytes, createCipheriv, createDecipheriv} from 'node:crypto';
export const MAX_BYTES = 32768;
export const MAX_TTL = 60000;
export const validId = value => typeof value === 'string' && /^[a-zA-Z0-9_-]{1,80}$/.test(value);
function keyBytes(key) {
  if (typeof key !== 'string' || !/^[a-fA-F0-9]{64}$/.test(key)) throw Error('A 32-byte hexadecimal pairing key is required');
  return Buffer.from(key, 'hex');
}
export function seal(key, context, payload, now = Date.now(), ttl = 15000, id = randomUUID()) {
  if (!validId(id) || !Number.isInteger(ttl) || ttl < 1 || ttl > MAX_TTL) throw Error('Invalid message lifetime or ID');
  const body = Buffer.from(JSON.stringify(payload));
  if (body.length > MAX_BYTES) throw Error('Payload too large');
  const meta = {version:1, id, createdAt:now, expiresAt:now + ttl};
  const iv = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', keyBytes(key), iv);
  cipher.setAAD(Buffer.from(JSON.stringify([context, meta])));
  const ciphertext = Buffer.concat([cipher.update(body), cipher.final()]);
  return {...meta, iv:iv.toString('base64'), ciphertext:ciphertext.toString('base64'), tag:cipher.getAuthTag().toString('base64')};
}
export function open(key, context, envelope, now = Date.now()) {
  if (!envelope || Buffer.byteLength(JSON.stringify(envelope)) > MAX_BYTES * 2) throw Error('Invalid envelope');
  const {version, id, createdAt, expiresAt, iv, ciphertext, tag} = envelope;
  if (version !== 1 || !validId(id) || !Number.isSafeInteger(createdAt) || !Number.isSafeInteger(expiresAt) ||
      createdAt > now + 5000 || expiresAt <= now || expiresAt <= createdAt || expiresAt - createdAt > MAX_TTL ||
      ![iv,ciphertext,tag].every(x => typeof x === 'string')) throw Error('Invalid or expired envelope');
  const nonce = Buffer.from(iv, 'base64'), authTag = Buffer.from(tag, 'base64');
  if (nonce.length !== 12 || authTag.length !== 16) throw Error('Invalid encryption metadata');
  const decipher = createDecipheriv('aes-256-gcm', keyBytes(key), nonce);
  decipher.setAAD(Buffer.from(JSON.stringify([context, {version,id,createdAt,expiresAt}])));
  decipher.setAuthTag(authTag);
  const body = Buffer.concat([decipher.update(Buffer.from(ciphertext, 'base64')), decipher.final()]);
  if (body.length > MAX_BYTES) throw Error('Payload too large');
  return JSON.parse(body.toString('utf8'));
}
