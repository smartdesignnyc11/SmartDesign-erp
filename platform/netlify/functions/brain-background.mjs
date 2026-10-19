// The Brain's run, as a background function (up to 15 minutes; the caller gets 202 at once). Started by the nightly
// schedule (brain-nightly.mjs) or by the owner from /api/brain, with a key only the server knows.
import {runBrain} from './lib/brain.mjs';
import crypto from 'node:crypto';
export const brainKey = () => crypto.createHmac('sha256', process.env.WATCH_KEY || '').update('brain-run').digest('hex');
export default async (req) => {
  if (req.headers.get('x-brain-key') !== brainKey()) return new Response('no', {status: 403});
  let b = {}; try { b = await req.json(); } catch {}
  const r = await runBrain(b.ws || 'smartdesign', {today: b.today});
  console.log('brain', JSON.stringify(r));
};
