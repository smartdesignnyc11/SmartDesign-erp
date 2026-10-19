// Every fifteen minutes through the working day (New York 7am to 7pm, weekdays): each connected person's new mail,
// calendar changes and Drive files go into their private inbox row, oldest-checked first, inside Netlify's time limit.
import {rest} from './lib/auth.mjs';
import {watchOne} from './lib/watch.mjs';
export default async () => {
  const stop = Date.now() + 22000;
  const rows = await rest('google_watch?select=*&order=last_run.asc.nullsfirst');
  const done = [];
  for (const row of rows || []) {
    if (Date.now() > stop - 4000) break;
    const r = await watchOne(row, stop);
    done.push({mail: r.mail, events: r.events, files: r.files, ok: !r.error});
  }
  console.log('watch', JSON.stringify(done));
  return new Response('ok');
};
export const config = {schedule: '*/15 11-23 * * 1-5'};
