// The executive assistant's runs, as a background function (up to 15 minutes; the caller gets 202 at once). Started by
// the weekday schedule (assistant-run.mjs) or by a person for their own assistant (/api/assistant), with a key only
// the server knows.
import {runAssistants} from './lib/assistant.mjs';
import crypto from 'node:crypto';
export const assistantKey = () => crypto.createHmac('sha256', process.env.WATCH_KEY || '').update('assistant-run').digest('hex');
export default async (req) => {
  if (req.headers.get('x-assistant-key') !== assistantKey()) return new Response('no', {status: 403});
  // Off until the app files the runs (lane executive assistant): set ASSISTANT_RUNS=on in Netlify to start them.
  if (process.env.ASSISTANT_RUNS !== 'on') { console.log('assistant runs are off (ASSISTANT_RUNS)'); return; }
  let b = {}; try { b = await req.json(); } catch {}
  const r = await runAssistants(b.ws || 'smartdesign', {today: b.today, only: b.only, push: !!b.push});
  console.log('assistant', JSON.stringify(r));
};
