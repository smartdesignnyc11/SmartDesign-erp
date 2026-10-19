// What in a watch run is worth a notification. Plain rules, no AI: mail from a vendor or client on file, mail that
// names a job, mail from a city agency, and calendar entries in the next 48 hours that are new or changed.
// Promotions, social, forums, newsletters and the person's own sent mail never notify.
const hdr = (m, n) => (((m.payload || {}).headers || []).find(h => (h.name || '').toLowerCase() === n) || {}).value || '';
const addr = s => ((String(s).match(/<([^>]+)>/) || [])[1] || String(s)).trim().toLowerCase();
const nameOf = s => String(s).replace(/<[^>]*>/, '').replace(/"/g, '').trim() || addr(s);
const SKIP = ['CATEGORY_PROMOTIONS', 'CATEGORY_SOCIAL', 'CATEGORY_FORUMS', 'SPAM', 'TRASH', 'SENT', 'DRAFT'];
const AGENCY = /(@|\.)(nyc\.gov|ny\.gov|buildings\.nyc\.gov|lpc\.nyc\.gov|dot\.nyc\.gov|fdny\.nyc\.gov)$/;

// The firm's people and jobs, from its records: e-mail addresses (and their domains, except public mail) and job words.
export function contextFrom(cols) {
  const emails = new Set(), domains = new Set(), jobs = [];
  const PUBLIC = /^(gmail|yahoo|hotmail|outlook|icloud|aol|me|live|msn)\./;
  const add = e => { e = String(e || '').trim().toLowerCase(); if (!/@/.test(e)) return; emails.add(e); const d = e.split('@')[1]; if (d && !PUBLIC.test(d)) domains.add(d); };
  const walk = (v, depth = 0) => { if (depth > 4 || !v) return; if (typeof v === 'string') { (v.match(/[\w.+-]+@[\w-]+\.[\w.-]+/g) || []).forEach(add); return; }
    if (Array.isArray(v)) return v.forEach(x => walk(x, depth + 1)); if (typeof v === 'object') Object.values(v).forEach(x => walk(x, depth + 1)); };
  walk(cols.vendors); walk(cols.clients);
  for (const p of cols.projects || []) {
    const pr = p.project || p;
    for (const t of [pr.name, pr.address, pr.addr]) { const w = String(t || '').replace(/ —.*$/, '').trim(); if (w.length >= 6) jobs.push(w.toLowerCase().split(',')[0]); }
  }
  return {emails, domains, jobs: [...new Set(jobs)]};
}

export function score(found, ctx, me = '') {
  const items = [];
  for (const m of found.gmail || []) {
    const labels = m.labelIds || [];
    if (labels.some(l => SKIP.includes(l))) continue;
    const from = hdr(m, 'from'), a = addr(from), subj = hdr(m, 'subject') || '(no subject)';
    if (!a || a === me) continue;
    const text = (subj + ' ' + (m.snippet || '')).toLowerCase();
    const known = ctx.emails.has(a) || ctx.domains.has(a.split('@')[1] || '');
    const job = ctx.jobs.find(j => text.includes(j));
    const agency = AGENCY.test(a);
    if (hdr(m, 'list-unsubscribe') && !known && !agency) continue;     // newsletters, unless someone we work with
    if (!(known || job || agency)) continue;
    items.push({kind: 'mail', line: `${nameOf(from)}: ${subj}`.slice(0, 120), why: agency ? 'agency' : known ? 'known' : 'job'});
  }
  const soon = Date.now() + 48 * 3600e3;
  for (const ev of found.cal || []) {
    const st = Date.parse((ev.start || {}).dateTime || (ev.start || {}).date || '');
    if (!st || st < Date.now() - 3600e3 || st > soon) continue;
    const when = new Date(st).toLocaleString('en-US', {timeZone: 'America/New_York', weekday: 'short', hour: 'numeric', minute: '2-digit'});
    items.push({kind: 'event', line: (ev.status === 'cancelled' ? 'Cancelled: ' : '') + `${ev.summary || 'Calendar entry'}, ${when}`.slice(0, 120), why: 'soon'});
  }
  return items;
}

// One notification per run per person: what changed, in plain words, the first three lines.
export function message(items) {
  if (!items.length) return null;
  const mail = items.filter(i => i.kind === 'mail').length, ev = items.length - mail;
  const title = [mail ? `${mail} new from people and jobs you work with` : '', ev ? `${ev} calendar change${ev > 1 ? 's' : ''} in the next two days` : ''].filter(Boolean).join(' · ');
  return {title, body: items.slice(0, 3).map(i => i.line).join('\n') + (items.length > 3 ? `\nand ${items.length - 3} more` : ''), url: '/'};
}
