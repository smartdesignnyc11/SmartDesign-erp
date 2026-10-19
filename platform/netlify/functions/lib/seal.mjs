// Seal and open a secret with AES-256-GCM. WATCH_KEY (32 bytes, base64) lives only in Netlify; a sealed value in
// the database is useless without it. Format: v1.<iv>.<tag>.<ciphertext>, all base64url.
import crypto from 'node:crypto';
const key = () => {
  const k = Buffer.from(process.env.WATCH_KEY || '', 'base64');
  if (k.length !== 32) throw new Error('WATCH_KEY is not set on the server');
  return k;
};
export function seal(text) {
  const iv = crypto.randomBytes(12), c = crypto.createCipheriv('aes-256-gcm', key(), iv);
  const enc = Buffer.concat([c.update(String(text), 'utf8'), c.final()]);
  return ['v1', iv, c.getAuthTag(), enc].map((x, i) => i ? x.toString('base64url') : x).join('.');
}
export function open(sealed) {
  const [v, iv, tag, enc] = String(sealed).split('.');
  if (v !== 'v1') throw new Error('unknown seal');
  const d = crypto.createDecipheriv('aes-256-gcm', key(), Buffer.from(iv, 'base64url'));
  d.setAuthTag(Buffer.from(tag, 'base64url'));
  return Buffer.concat([d.update(Buffer.from(enc, 'base64url')), d.final()]).toString('utf8');
}
