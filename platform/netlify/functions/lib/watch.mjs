// One watch run for one person: fresh access from the sealed key, then new mail, calendar changes and Drive
// files into their private inbox row (own:<person>:inbox). The app files the inbox through its own sync code
// when it opens, so routing, proposals and filing are the same as a sync run in the browser.
import {rest} from './auth.mjs';
import {open} from './seal.mjs';
import {access, newMail, calChanges, driveChanges} from './google.mjs';

export async function watchOne(row, deadline = Date.now() + 20000) {
  const cur = row.cursors || {}, next = {...cur}, found = {gmail: [], cal: [], drive: []};
  let error = '';
  try {
    const tok = (await access(open(row.sealed))).access_token;
    const started = Math.floor(Date.now() / 1000) - 120;          // a little overlap; the app skips what it holds
    const m = await newMail(tok, cur.gmailAfter, 40, deadline);
    found.gmail = m.messages; if (m.done) next.gmailAfter = started;
    if (Date.now() < deadline) {
      try { const c = await calChanges(tok, cur.calTok); found.cal = c.items; if (c.syncToken) next.calTok = c.syncToken; }
      catch (e) { if (e.gone) next.calTok = ''; else throw e; }
    }
    if (Date.now() < deadline) {
      const at = new Date().toISOString();
      found.drive = await driveChanges(tok, cur.driveAt); next.driveAt = at;
    }
  } catch (e) { error = String(e.message || e).slice(0, 300); }
  const items = Object.fromEntries(Object.entries(found).filter(([, v]) => v.length));
  if (Object.keys(items).length) await rest('rpc/watch_put_inbox', {method: 'POST', body: JSON.stringify({p_ws: row.workspace_id, p_key: row.person_key, p_items: items})});
  const now = new Date().toISOString();
  await rest('google_watch?person_key=eq.' + encodeURIComponent(row.person_key), {method: 'PATCH', headers: {prefer: 'return=minimal'},
    body: JSON.stringify({cursors: next, last_run: now, last_error: error, ...(error ? {} : {last_ok: now})})});
  return {mail: found.gmail.length, events: found.cal.length, files: found.drive.length, error};
}
