// month_runtime.js: the in-page half of tests/month_sim.py (installed once; the page is never reloaded).
// Injection through the app's own paths, the screens each role works from, the actors' policies, the sheet
// driver and the ledger's checks. Every name, address and amount it handles comes from tests/month_book.json
// (invented data). The actors never read the book: they read the DOM of their own screens.
() => {
if (window.__MS) return true;
const M = window.__MS = { toasts: [], tried: new Set(), memo: {}, seenLog: {}, holds: {}, picks: {}, firstSeen: {}, lineGap: {}, used: new Set() };
const sleep = ms => new Promise(r => setTimeout(r, ms));
// the brain's 30-minute timer would fire at a wall-clock moment; the day's hooks (appSetDay) run it instead
try { clearInterval(bnTimer); bnTimer = 1; } catch (e) {}
try { clearInterval(gsTimerId); } catch (e) {}
try { tdCatchAll = true; } catch (e) {}
const norm = s => String(s == null ? '' : s).replace(/\s+/g, ' ').trim();
const vis = el => !!el && el.isConnected && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
const RX = s => new RegExp(s, 'i');
const projOf = id => DB.projects.find(p => p.id === id);

// ---- toasts: every mutation toasts; the action log keeps what each one said
(() => { const t = document.getElementById('toast'); if (!t) return;
  new MutationObserver(() => { const x = norm(t.innerText); if (x && M.toasts[M.toasts.length - 1] !== x) M.toasts.push(x.slice(0, 200)); })
    .observe(t, { childList: true, subtree: true, characterData: true }); })();
const STAFF = { 'alan@smartdesign.nyc': 'u_owner', 'alan.pm@smartdesign.nyc': 'u_alan', 'chen@smartdesign.nyc': 'u_chen',
  'angel@smartdesign.nyc': 'u_angel', 'sarah@smartdesign.nyc': 'u_sarah', 'billing@smartdesign.nyc': 'u_billing',
  'controller@smartdesign.nyc': 'u_controller', 'alberto@smartdesign.nyc': 'u_alberto', 'alex@smartdesign.nyc': 'u_alex' };
const addrUid = a => { const m = String(a || '').match(/<([^>]+)>/); return STAFF[(m ? m[1] : a).toLowerCase().trim()] || ''; };
const closeAll = () => { try { mbCloseModal(); } catch (e) {} try { if (document.querySelector('#drawer.on') && typeof closeEditor === 'function') closeEditor(); } catch (e) {}
  try { document.querySelectorAll('.viewer.on, #viewer.on').forEach(v => v.classList.remove('on')); } catch (e) {} };
M.as = uid => { closeAll(); if ((currentUser() || {}).id !== uid) signIn(uid); };   // signIn renders the person's landing view
M.go = v => { closeAll(); view = v; render(); };
M.root = () => document.querySelector('section.view.on') || document.body;
M.text = () => norm(M.root().innerText);

// ============================================================================ injection
M.wsMail = ev => {   // into every staff mailbox the message is addressed to; each mailbox holds its own copy
  const p = ev.payload, at = new Date(`${ev.day}T${ev.time}:00`).getTime(), out = [];
  const from = addrUid(p.from), rcpt = [...p.to, ...(p.cc || [])].map(addrUid).filter(Boolean);
  [...new Set([from, ...rcpt].filter(Boolean))].forEach(uid => {
    if (!(DB.conn[uid] && (DB.conn[uid].google || {}).demo)) return;
    const W = demoWsFor(uid), id = `ms_${ev.id}_${uid}`;
    if (W.messages.some(m => m.id === id)) return;
    const mine = uid === from;
    W.messages.push({ id, threadId: `msth_${p.thread || ev.id}_${uid}`, labelIds: mine ? (p.labels || ['SENT']) : ['INBOX', 'UNREAD'],
      internalDate: at, historyId: ++W.historyId,
      headers: { From: p.from, To: p.to.join(', '), Cc: (p.cc || []).join(', '), Subject: p.subject, Date: new Date(at).toUTCString() },
      body: p.text, attachments: (p.att || []).map((a, i) => ({ id: `msa_${ev.id}_${uid}_${i}`, filename: a.filename, mime: 'application/pdf', size: 40000 + 100 * (a.text || '').length, text: a.text || '' })) });
    out.push(uid);
  });
  return out.join(',') || 'no mailbox';
};
M.wsEvent = ev => { const p = ev.payload, W = demoWsFor(p.uid), s = new Date(p.start + ':00').getTime();
  W.events.push({ id: `mse_${ev.id}`, status: 'confirmed', summary: p.title, description: '', location: p.where || '', htmlLink: '',
    updated: new Date(appNowMs()).toISOString(), organizer: { email: W.email }, attendees: [{ email: W.email, responseStatus: 'accepted' }],
    transparency: 'opaque', start: { dateTime: new Date(s).toISOString() }, end: { dateTime: new Date(s + 60000 * (p.mins || 60)).toISOString() } });
  return p.uid; };
M.wsFile = ev => { const p = ev.payload, W = demoWsFor(p.uid);
  W.files.push({ id: `msf_${ev.id}`, name: p.name, mimeType: /\.txt$/.test(p.name) ? 'text/plain' : 'application/pdf', modifiedTime: new Date(appNowMs()).toISOString(),
    size: String(60000 + 300 * (p.text || '').length), owners: [{ displayName: W.name, emailAddress: W.email }], webViewLink: '', parents: ['dwroot_' + p.uid], text: p.text || '', trashed: false });
  return p.uid; };
M.connect = async uid => { M.as(uid); const d = await gcDemoConnect(); try { clearInterval(gsTimerId); } catch (e) {}
  return d ? { mail: d.mail.length, events: d.events.length, files: d.files.length, errors: d.errors } : null; };
M.sync = async uid => {   // the watcher's pull for the signed-in persona: route, read, nudge, chase
  if (!(DB.conn[uid] && (DB.conn[uid].google || {}).demo)) return null;
  const W = demoWsFor(uid); W.now = appNowMs();
  const d = await gsRun({ quiet: true });
  return d ? { mail: d.mail.length, events: d.events.length, files: d.files.length, errors: d.errors } : null;
};
M.importCsv = async (acct, name, text) => {   // Banking > Import Statement, with the file handed to its file input
  view = 'bank'; render(); bfImportDialog(acct);
  const inp = document.querySelector('#bfi-file'); if (!inp) return { err: 'no file input' };
  const dt = new DataTransfer(); dt.items.add(new File([text], name, { type: 'text/csv' })); inp.files = dt.files;
  inp.dispatchEvent(new Event('change'));
  let ok = null; for (let i = 0; i < 100; i++) { await sleep(15); ok = document.querySelector('#mbm-ok'); if (ok && !ok.disabled && /Import \d/.test(ok.textContent)) break; }
  if (!ok || ok.disabled) { const t = norm((document.querySelector('#mbm') || {}).innerText).slice(0, 160); closeAll(); return { err: 'not ready: ' + t }; }
  const label = norm(ok.textContent); ok.click(); await sleep(30); closeAll();
  return { label, imp: (DB.bankImports || []).filter(i => i.fileName === name).map(i => ({ added: i.added, dup: i.dup })) };
};
// the signed-in actor's own events: field reports, portal actions, facts a "due" event puts in place
M.own = async ev => {
  const p = ev.payload || {};
  if (ev.kind === 'field') { const pr = projOf(p.project); setCurrent(pr.id);
    if (p.do === 'raise') { const r = fSend({ type: p.type, title: p.title, note: p.note, taskId: p.taskId || '' }); return r ? 'raised ' + r.id : 'not raised'; }
    if (p.do === 'request') { const r = addRequest({ what: p.what, qty: p.qty, unit: p.unit, neededBy: p.neededBy, taskId: p.taskId || '', note: '' }, (currentUser() || {}).name); save(); return r ? 'requested ' + r.id : 'not requested'; }
    if (p.do === 'pct') { const t = pr.tasks.find(x => x.id === p.taskId); if (!t) return 'no task';
      prgSet(pr, t, { pct: p.pct, by: (currentUser() || {}).name || 'Angel', role: 'foreman', src: 'field', note: p.note }); save(); return 'measured ' + t.pct; }
  }
  if (ev.kind === 'client') {
    if (p.do === 'hold') { M.holds[p.decision] = p.until; return 'will choose ' + p.decision + ' on ' + p.until; }
    if (p.do === 'choose') { M.picks[p.decision] = { option: p.option || 0, match: p.match || '', on: p.on || ev.day }; return 'will choose ' + p.decision + (p.on ? ' on ' + p.on : ''); }
    if (p.do === 'chat') return await M.chat(p.text);
    if (p.do === 'coAsk') { M.go('client'); const b = [...M.root().querySelectorAll('[data-pask]')].find(x => { const r = x.closest('.pa-row'); return r && r.innerText.includes('CO-2026-002') || /co:/.test(x.dataset.pask); });
      if (!b) return 'no Ask'; b.click(); await sleep(30); const m = document.querySelector('#mbm'); if (!m) return 'no sheet';
      const f = m.querySelector('textarea, input[type=text]'); if (f) { f.value = p.text; f.dispatchEvent(new Event('input', { bubbles: true })); }
      const ok = m.querySelector('#mbm-ok'); ok && ok.click(); await sleep(30); closeAll(); return 'asked on the CO'; }
  }
  if (ev.kind === 'due') {
    if (p.create) { const pr = projOf(p.create.project); pr.actions = pr.actions || [];
      pr.actions.push({ id: uid('a'), title: p.create.title, assignee: p.create.assignee || '', due: p.create.due, status: 'todo', createdAt: today(), src: 'manual' }); save(); return 'task left unowned'; }
    if (p.typed) { const t = p.typed; setCurrent(t.project || 'p121'); view = 'bank'; render(); txnDialog();
      const set = (s, v) => { const e = document.querySelector(s); if (e) { e.value = v; e.dispatchEvent(new Event('change', { bubbles: true })); } };
      set('#e-date', t.date); set('#e-acct', t.acct); set('#e-desc', t.desc); set('#e-amt', String(t.amt)); set('#e-cat', t.cat); set('#e-proj', t.project); set('#e-code', t.code);
      const sv = document.querySelector('#d-save'); sv && sv.click(); await sleep(20); closeAll(); return 'typed by hand'; }
    if (p.journal) { return await M.journal(p.journal); }
  }
  return '';
};
M.chat = async text => {   // Chat: the composer every role has (#chat-text, Send)
  M.go('chat'); const ta = document.querySelector('#chat-text'), send = document.querySelector('#chat-send');
  if (!ta || !send) return 'no chat box';
  ta.value = text; ta.dispatchEvent(new Event('input', { bubbles: true })); send.click(); await sleep(30); return 'sent in Chat';
};
M.journal = async j => {   // Ledger > New entry, drafted by the controller, submitted for the Owner
  view = 'gl'; render(); const tab = [...M.root().querySelectorAll('button')].find(x => /^New entry$/i.test(norm(x.innerText))); if (!tab) return 'no New entry';
  tab.click(); await sleep(30);
  const set = (el, v) => { if (el) { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); } };
  set(document.querySelector('#gle-date'), j.date); set(document.querySelector('#gle-memo'), j.memo);
  const sels = [...M.root().querySelectorAll('select')].filter(x => vis(x) && [...x.options].some(o => /^1590/.test(o.text)));
  const nums = [...M.root().querySelectorAll('input[type=number]')].filter(vis);
  if (sels.length < 2 || nums.length < 4) return 'journal form not as expected';
  const exp = [...sels[0].options].find(o => /depreciation/i.test(o.text) && !/^1590/.test(o.text)) || [...sels[0].options].find(o => /^6|^7/.test(o.text));
  set(sels[0], exp ? exp.value : ''); set(nums[0], String(j.amount));
  set(sels[1], ([...sels[1].options].find(o => /^1590/.test(o.text)) || {}).value); set(nums[3], String(j.amount));
  const sub = [...M.root().querySelectorAll('button')].find(b => /^Submit for approval$/i.test(norm(b.innerText))); if (!sub) return 'no Submit';
  const t0 = M.toasts.length; sub.click(); await sleep(30); const st = await M.drive(SAY.controller);
  return ('submitted: ' + (M.toasts.slice(t0).join(' | ') || st.join('; '))).slice(0, 120);
};

// ============================================================================ screens and their items
// Each collector reads the current DOM of one surface: [{key, sec, kind, text, verbs:[{label, el}]}].
const its = (els, f) => els.filter(vis).map(f).filter(Boolean);
const btns = (el, sel) => [...el.querySelectorAll(sel || 'button')].filter(vis).map(b => ({ label: norm(b.innerText || b.getAttribute('aria-label')), el: b })).filter(v => v.label);
const COLLECT = {
  home: R => {
    if (R.querySelector('.td-home')) return its([...R.querySelectorAll('.td-do .td-card')], el => ({ sec: 'Do Now', kind: el.dataset.kind, text: norm(el.querySelector('.td-txt').innerText), verbs: btns(el, '[data-tdverb]') }))
      .concat(its([...R.querySelectorAll('.td-catch .td-card')], el => ({ sec: 'Caught for You', kind: el.dataset.src, text: norm(el.querySelector('.td-txt').innerText), verbs: btns(el, '[data-tdcatch]') })))
      .concat(its([...R.querySelectorAll('section, .td-sec')].filter(s => /needs your hand/i.test(norm((s.querySelector('h2,h3') || {}).innerText))).flatMap(s => [...s.querySelectorAll('.td-card, .card, li')]),
        el => ({ sec: 'Needs Your Hand', kind: 'hand', text: norm(el.innerText).slice(0, 240), verbs: btns(el) })));
    return its([...R.querySelectorAll('.h4c')].flatMap(card => [...card.querySelectorAll('.h4r[data-ea]')].map(el => [card, el])).map(x => x[1]), el => {
      const card = el.closest('.h4c'); return { sec: norm((card.querySelector('.h4c-hd b') || {}).innerText), kind: 'ea', text: norm(el.innerText).slice(0, 240), verbs: [{ label: norm((el.querySelector('em, .h4-act') || {}).innerText || 'Open'), el }] }; });
  },
  mapprove: R => { const out = its([...R.querySelectorAll('.m-appr')], el => ({ sec: 'Approvals', kind: el.dataset.mk, id: el.dataset.mid, text: norm(el.querySelector('.m-appr-t') ? el.querySelector('.m-appr-t').innerText : el.innerText).slice(0, 240), verbs: btns(el, '.m-appr-a button') }));
    const all = R.querySelector('#mappr-allhours'); if (all && vis(all) && !all.disabled) out.unshift({ sec: 'Approvals', kind: 'hours', text: norm(all.innerText), verbs: [{ label: norm(all.innerText), el: all }] });
    return out; },
  billing: R => its([...R.querySelectorAll('tr')].filter(tr => tr.querySelector('[data-blact]')), el => ({ sec: 'Billing Queue', kind: 'bl', text: norm(el.innerText).slice(0, 240), verbs: btns(el, '[data-blact]') })),
  bank: R => its([...R.querySelectorAll('[data-mconfirm]')], b => { let row = b.parentElement; for (let i = 0; i < 4 && row && norm(row.innerText).length < 60; i++) row = row.parentElement;
      return { sec: 'Matches Waiting for Your Confirmation', kind: 'proposal', text: norm(row.innerText).slice(0, 240), verbs: [{ label: 'Confirm', el: b }] }; })
    .concat(its([...R.querySelectorAll('button')].filter(b => /^Accept$/.test(norm(b.innerText))), b => { let row = b.parentElement; for (let i = 0; i < 4 && row && norm(row.innerText).length < 40; i++) row = row.parentElement;
      return { sec: 'Needs Category', kind: 'suggest', text: norm(row.innerText).slice(0, 240), verbs: [{ label: 'Accept', el: b }] }; })
    .concat(its([...R.querySelectorAll('tr')].filter(tr => tr.querySelector('[data-trmatch]')), el => ({ sec: 'Not Matched', kind: 'unmatched', text: norm(el.innerText).slice(0, 240), verbs: btns(el, '[data-trmatch]') })))),
  ftoday: R => its([...R.querySelectorAll('.f-row')].filter(r => r.querySelector('[data-fack], [data-fneed]')), el => ({ sec: 'Today', kind: 'f', text: norm(el.innerText).slice(0, 240), verbs: btns(el, '[data-fack], [data-fneed]') })),
  sday: R => its([...R.querySelectorAll('.f-row')].filter(r => r.querySelector('[data-fans], [data-nyh]')), el => ({ sec: el.querySelector('[data-nyh]') ? 'Needs Your Hand' : 'From the Field', kind: el.querySelector('[data-nyh]') ? 'hand' : 'raise', text: norm(el.innerText).slice(0, 240), verbs: btns(el, '[data-fans], [data-nyh]') })),
  // a submittal the client approves (the tile sample) carries its Approve as [data-smcl], not [data-papprove]: the
  // client sees and presses it, so the collector reads it too (flow: the month scored the sample missed because the
  // actor never saw the button the client sees)
  client: R => its([...R.querySelectorAll('.cl-waiting .pa-row')], el => ({ sec: 'Waiting on You', kind: (el.querySelector('[data-pdecide]') ? 'dec' : 'doc'), id: ((el.querySelector('[data-pdecide]') || {}).dataset || {}).pdecide || ((el.querySelector('[data-papprove]') || {}).dataset || {}).papprove || ((el.querySelector('[data-smcl]') || {}).dataset || {}).smcl || '',
    text: norm(el.innerText).slice(0, 240), verbs: btns(el, '[data-pdecide], [data-papprove], [data-smcl]') })),
};
const VIEWOF = { home: 'home', mapprove: 'mapprove', billing: 'billing', bank: 'bank', ftoday: 'ftoday', sday: 'sday', client: 'client', comms: 'comms', tkall: 'tkall', time: 'time', route: 'route', close: 'gl', pa: 'pa' };
M.texts = {};
M.open = (s, force) => { const v = VIEWOF[s] || s;
  if (s === 'home') { try { tdCatchAll = true; } catch (e) {} }
  if (s === 'mapprove') window.mApprKind = 'all';
  if (force || view !== v || document.querySelector('#mbm') || document.querySelector('#drawer.on') || s === 'close') M.go(v);
  if (s === 'close') { const t = [...M.root().querySelectorAll('button, [role=tab]')].find(b => norm(b.innerText) === 'Close'); t && t.click(); }
  if (s === 'comms') { const f = M.root().querySelector('[data-cmf="all"]'); f && !f.classList.contains('on') && f.click(); }
  return M.text(); };
M.items = s => (COLLECT[s] ? COLLECT[s](M.root()) : []);
M.SURF = { owner: ['home', 'mapprove'], pm: ['home', 'mapprove', 'tkall'], coord: ['home', 'mapprove', 'comms'], billing: ['billing', 'home', 'comms', 'bank'],
  controller: ['home', 'close', 'bank', 'comms'], designer: ['sday', 'tkall'], foreman: ['ftoday'], crew: ['time'], driver: ['route'], client: ['client'] };
M.matchSeen = (uid, s, text, needles, day) => {
  const T = String(text || '').toLowerCase(), hits = {};
  Object.entries(needles || {}).forEach(([id, N]) => { if (N.some(n => n && T.includes(String(n).toLowerCase()))) {
    hits[id] = s; M.seenLog[id] = M.seenLog[id] || {}; M.seenLog[id][uid] = M.seenLog[id][uid] || [day, s]; } });
  return hits; };

// ============================================================================ the sheet driver
// A diligent person reads the sheet, fills the blanks with a plain sentence (a name where it asks for a name),
// picks the first option where one must be picked, ticks the "I approve" box and presses the blue button: the
// house rule is that the primary is the safe next step. `prefer` names a button to press instead.
M.drive = async (P, prefer) => {
  const steps = [];
  for (let i = 0; i < 5; i++) {
    await sleep(15);
    const m = document.querySelector('#mbm'); if (!m) break;
    const title = norm((m.querySelector('h3') || {}).innerText).slice(0, 70);
    const radios = [...m.querySelectorAll('.sel-opts input[type=radio]')].filter(r => r.value !== '__other');
    if (radios.length && !radios.some(r => r.checked)) { const byMatch = P.match ? radios.find(r => RX(P.match).test(r.value + ' ' + norm((r.closest('label') || r.parentElement || {}).innerText))) : null;
      const r = byMatch || radios[Math.min(P.option || 0, radios.length - 1)]; r.click(); r.dispatchEvent(new Event('change')); }
    m.querySelectorAll('textarea, input[type=text], input:not([type])').forEach(f => {
      if (!vis(f) || f.readOnly || f.disabled || String(f.value || '').trim()) return;
      if (radios.length && (f.id === 'pd-choice' || f.dataset.f === 'ans')) return;
      const lab = norm(((f.closest('.f') || {}).querySelector ? (f.closest('.f').querySelector('label') || {}).innerText : '') + ' ' + (f.placeholder || '') + ' ' + (f.dataset.f || ''));
      const lab0 = norm(((f.closest('.f') || {}).querySelector ? (f.closest('.f').querySelector('label') || {}).innerText : '') || '');
      if (f.type === 'email' || /^(to|e-?mail|email address)\b/i.test(lab0) || f.dataset.f === 'to') return;
      f.value = /\bname\b|sign|signature/i.test(lab) ? P.name : P.say;
      f.dispatchEvent(new Event('input', { bubbles: true })); f.dispatchEvent(new Event('change', { bubbles: true }));
    });
    m.querySelectorAll('input[type=checkbox]').forEach(c => { const l = norm((c.closest('label') || c.parentElement || {}).innerText);
      if (!c.checked && /approve|confirm|true record|checked|agree|understand/i.test(l)) c.click(); });
    let btn = prefer ? [...m.querySelectorAll('button, [data-trpick]')].find(b => vis(b) && !b.disabled && RX(prefer).test(norm(b.innerText))) : null;
    btn = btn || [...m.querySelectorAll('.btn.primary, button.primary')].find(b => vis(b) && !b.disabled);
    if (!btn) { steps.push(`[${title}] no blue button`); break; }
    if (P.never && RX(P.never).test(norm(btn.innerText))) { steps.push(`[${title}] left: ${norm(btn.innerText).slice(0, 30)}`); break; }
    steps.push(`[${title}] ${norm(btn.innerText).slice(0, 40)}`);
    btn.click(); await sleep(40);
    if (document.querySelector('#mbm') === m && m.isConnected) { steps.push('sheet stayed open'); break; }
  }
  closeAll();
  return steps;
};

// ============================================================================ the actors
const SAY = {
  owner: { say: 'Approved at the PO amount; the difference is disputed until the vendor credits it.', name: 'Alan Mishali' },
  pm: { say: 'Go ahead as drawn; checked against the drawings and the schedule. Photograph before and after.', name: 'Alan' },
  coord: { say: 'Acknowledged. Ordered and on the driver\'s route; I will confirm the delivery window.', name: 'Chen Biron' },
  billing: { say: 'Recorded per the bank deposit and the invoice.', name: 'Billing' },
  controller: { say: 'Coded per the receipt and the job.', name: 'Controller', prefer: '^Match$|^Confirm the Match$', never: '^Sign an Exception$' },
  designer: { say: 'Go with the drawing: A-301 rev 2 governs; 42 inches at the open side, per code.', name: 'Sarah Davis' },
  foreman: { say: 'Got it.', name: 'Angel' }, crew: { say: 'Done.', name: 'Alberto' }, driver: { say: 'Bought and dropped.', name: 'Alex' },
  client: { say: 'Thank you, that works for us.', name: 'Sarah Klein' } };
// Policies: per surface, an ordered list of rules {verb, kind?, text?, not?, sec?, follow?, chase?, prefer?}.
// The one-tap verbs the app gained for the month's cracks (flow lane): Order on a late line, Record Choice on a choice
// made by mail, Write the Change Order / Send to Client on an extra, Make It a Task on a dated ask, Book It on a
// meeting time, Draft the Renewal on an obligation, Draft the Reply on a lead's questions, Chase on billing's past-due
// row; a line with no supplier yet is tried again after three working days, like a chase. Each is the button the person
// sees on their own screen; the actor presses it like the others and the sheet driver does the rest.
const POL = {
  owner: { home: [{ verb: /^Approve$/ }, { verb: /^Dispute Difference$/ }, { verb: /^Chase COI$/, chase: 1, max: 2 }, { verb: /^Chase$/, chase: 1, max: 2 }, { verb: /^(Make It a Task|Book It|Draft the Renewal|Draft the Reply)$/, max: 2 }],
    mapprove: [{ verb: /^Approve$/, kind: /^bill$/ }, { verb: /^(Approve|Post|Approve & Post)/, kind: /^(journal|payroll|learn)$/ }, { verb: /^(Make It a Task|Book It|Draft the Renewal|Draft the Reply)$/, kind: /^hand$/, max: 2 }] },
  pm: { home: [{ verb: /^Answer$/ }, { verb: /^(Approve|Recommend)$/ }, { verb: /^(Record Choice|Write the Change Order|Send to Client)$/ }, { verb: /^Make It a Task$/, max: 2 }, { verb: /^Chase$/, chase: 1, max: 1 }],
    mapprove: [{ verb: /^Approve All Hours/ }, { verb: /^Answer$/ }, { verb: /^(Approve|Recommend)$/, kind: /^(bill|time)$/ }, { verb: /^(Record Choice|Write the Change Order|Send to Client|Make It a Task)$/, kind: /^hand$/, max: 2 }, { verb: /^Open$/, kind: /^meeting$/, follow: /^Approve All/ }] },
  coord: { home: [{ verb: /^Acknowledge$/ }, { verb: /^(Apply|Make It a Task)$/, max: 4 }, { verb: /^Order$/, max: 3, chase: 1 }, { verb: /^Chase$/, chase: 1, max: 2 }],
    mapprove: [{ verb: /^Acknowledge$/, follow: /^Acknowledge$/ }, { verb: /^Answer$/, follow: /^Answer$/ }, { verb: /^Open$/, kind: /^meeting$/, follow: /^Approve All/ }] },
  billing: { billing: [{ verb: /^Draft$/, follow: /^Send to Client$/ }, { verb: /^Send$/ }], home: [{ verb: /^(Record Payment|Resolve)$/ }, { verb: /^(Draft|Draft It)$/, follow: /^Send to Client$/ }, { verb: /^Confirm$/ }, { verb: /^Apply$/, max: 3 }, { verb: /^Chase$/, chase: 1, max: 2 }] },
  controller: { home: [{ verb: /^Confirm$/, follow: /^Confirm$/ }, { verb: /^Apply$/, max: 4 }], bank: [{ verb: /^Confirm$/, kind: /^proposal$/ }, { verb: /^Accept$/ }, { verb: /^Match to a Line/, kind: /^unmatched$/ }] },
  designer: { sday: [{ verb: /^Answer$/ }, { verb: /^Make It a Task$/ }] },
  foreman: { ftoday: [{ verb: /^Got It$/ }, { verb: /^Still Need This$/, chase: 1, max: 2 }] },
  client: { client: [{ verb: /^(Choose|Approve)$/ }] },
};
const workBetween = (a, b) => { try { return workdays(a, b) - 1; } catch (e) { return 0; } };
M.turn = async (uid, roleName, o) => {
  const day = today(), out = { injected: [], imported: [], sync: null, seen: {}, texts: {}, acts: [], errs: [], t: {} }; let t0 = performance.now();
  M.as(uid); out.t.signIn = Math.round(performance.now() - t0); t0 = performance.now();
  for (const ev of (o.own || [])) { try { out.injected.push([ev.id, String(await M.own(ev)).slice(0, 80)]); } catch (e) { out.injected.push([ev.id, 'ERR ' + e.message]); } }
  for (const [acct, name, text] of (o.bank || [])) { try { out.imported.push([acct, await M.importCsv(acct, name, text)]); } catch (e) { out.imported.push([acct, 'ERR ' + e.message]); } }
  out.t.inject = Math.round(performance.now() - t0); t0 = performance.now();
  try { out.sync = await M.sync(uid); } catch (e) { out.errs.push('sync ' + e.message); }
  out.t.sync = Math.round(performance.now() - t0); t0 = performance.now();
  if (/crew|foreman/.test(roleName)) { try { await M.clockIn(uid); } catch (e) {} }
  M.as(uid);
  return out;
};
// What the person saw on each surface, then what they did. Returns the action log.
M.work = async (uid, roleName, o) => {
  const out = { seen: {}, acts: [], errs: [], t: {} }, P = SAY[roleName] || SAY.pm, cap = o.cap || 12, day = today(); let t0w = performance.now();
  let n = 0;
  const did = (sec, item, verb, res) => { n++; out.acts.push({ sec, item: norm(item).slice(0, 110), verb, steps: res.steps || [], toast: (res.toast || '').slice(0, 160), via: res.via || 'button' }); };
  const press = async (el, rule, item) => {
    const t0 = M.toasts.length, v0 = view; el.click(); await sleep(30);
    let steps = await M.drive(Object.assign({}, P, rule.option != null ? { option: rule.option } : {}, rule.match ? { match: rule.match } : {}), rule.prefer || P.prefer);
    if (rule.follow && !steps.length) {   // the verb navigated: find the same item on the new screen and press the follow verb
      const key = norm(item.text).slice(0, 28).toLowerCase();
      const cand = [...M.root().querySelectorAll('button, [data-fans]')].filter(b => vis(b) && rule.follow.test(norm(b.innerText)));
      const b = cand.find(b => { let r = b; for (let i = 0; i < 6 && r; i++, r = r.parentElement) if (norm(r.innerText).toLowerCase().includes(key)) return true; return false; }) || (cand.length === 1 || /Approve All/.test(String(rule.follow)) ? cand[0] : null);
      if (b) { steps.push(`(${v0} > ${view}) ${norm(b.innerText).slice(0, 30)}`); b.click(); await sleep(30); steps = steps.concat(await M.drive(P, rule.prefer || P.prefer)); }
      else steps.push(`(${v0} > ${view}) no "${rule.follow.source}" for it here`);
    } else if (rule.follow) {   // a sheet made a document: its own next step (Send to Client) is on the page now
      const b = [...M.root().querySelectorAll('button')].find(b => vis(b) && rule.follow.test(norm(b.innerText)));
      if (b) { b.click(); await sleep(30); steps = steps.concat(['> ' + norm(b.innerText)], await M.drive(P, '^Send$|^Send to Client$')); }
    }
    return { steps, toast: M.toasts.slice(t0).join(' | ') };
  };
  for (const s of (M.SURF[roleName] || []).filter(s => s !== 'close' || day >= '2026-09-28')) {
    t0w = performance.now();
    let text = ''; const used = new Map(); const first = s === M.SURF[roleName][0];
    if (first && o.opened) text = M.texts[s];   // opened by M.look, and photographed, a moment ago
    else try { text = M.open(s, !(first && view === (VIEWOF[s] || s))); M.texts[s] = text; } catch (e) { out.errs.push(s + ': ' + e.message); continue; }
    out.t[s + ':open'] = Math.round(performance.now() - t0w); t0w = performance.now();
    Object.assign(out.seen, M.matchSeen(uid, s, text, o.needles, day));
    out.t[s + ':seen'] = Math.round(performance.now() - t0w); t0w = performance.now();
    const rules = (POL[roleName] || {})[s];
    if (!rules) continue;
    for (let k = 0; k < 40 && n < cap; k++) {
      try { M.open(s); } catch (e) { break; }
      let pickIt = null, pickV = null, pickR = null;
      for (const it of M.items(s)) {
        for (const r of rules) {
          const v = it.verbs.find(v => r.verb.test(v.label)); if (!v) continue;
          if (r.kind && !r.kind.test(it.kind || '')) continue; if (r.text && !r.text.test(it.text)) continue;
          const key = `${uid}|${s}|${it.text.slice(0, 70)}|${v.label}`;
          if (M.tried.has(day + '|' + key)) continue;
          if (r.chase && M.memo[key] && workBetween(M.memo[key], day) < 3) continue;
          if (r.max && (used.get(r) || 0) >= r.max) continue;
          if (roleName === 'client' && !(await M.clientReady(uid, it))) { M.tried.add(day + '|' + key); continue; }
          pickIt = it; pickV = v; pickR = r; M.tried.add(day + '|' + key); M.memo[key] = day; used.set(r, (used.get(r) || 0) + 1); break;
        }
        if (pickIt) break;
      }
      if (!pickIt) break;
      const rule = Object.assign({}, pickR);
      if (roleName === 'client' && pickIt.kind === 'dec') { const d = String(pickIt.id || '').split(':')[1]; if (M.picks[d]) { rule.option = M.picks[d].option; rule.match = M.picks[d].match; } }
      try { const res = await press(pickV.el, rule, pickIt); did(pickIt.sec || s, pickIt.text, pickV.label, res); }
      catch (e) { out.errs.push(`${s} ${pickV.label}: ${String(e.message || e).slice(0, 120)}`); }
    }
    out.t[s + ':loop'] = Math.round(performance.now() - t0w);
  }
  t0w = performance.now();
  const X = M.extras[roleName];
  if (X && n < cap) { try { await X(uid, cap - n, did, o); } catch (e) { out.errs.push('extras: ' + String(e.stack || e).slice(0, 200)); } }
  out.t.extras = Math.round(performance.now() - t0w);
  closeAll();
  return out;
};
// The first screen of the day, opened before the person acts (the screenshot is taken of it)
M.look = (uid, roleName, o) => { const s = M.SURF[roleName][0]; M.texts = {};
  const text = M.open(s, view !== (VIEWOF[s] || s)); M.texts[s] = text; return M.matchSeen(uid, s, text, o.needles, today()); };
M.clientReady = async (uid, it) => {   // the client takes up to two days, waits where they said they would, and picks what they said
  const day = today(), d = String(it.id || '').split(':')[1] || '';
  if (d && M.holds[d] && day < M.holds[d]) return false;
  if (d && M.picks[d]) return day >= M.picks[d].on;
  const key = uid + '|' + it.text.slice(0, 60); M.firstSeen[key] = M.firstSeen[key] || day;
  const due = (it.text.match(/needed by \w+, (\w+ \d+)/) || [])[1];
  return workBetween(M.firstSeen[key], day) >= 1 || /as soon as you can/i.test(it.text);
};
// ---- the Inbox: open each message that has something to decide, Apply what is this role's to apply
// visit: a vendor's delivery date or a sub's day read from mail (flow lane), the coordinator's to apply like a delivery
const KINDS = { owner: /^(lead|call)$/, coord: /^(bill|quote|delivery|visit|coi|receipt|unrouted|statement|request|noshow)$/, billing: /^(deposit|statement|bill)$/, controller: /^(bill|statement)$/, pm: /^(permit|lpc|noshow|question|decision)$/ };
M.inbox = async (uid, roleName, cap, did) => {
  let done = 0; const tried = new Set();
  for (let k = 0; k < 40 && done < cap; k++) {
    M.open('comms');
    const it = [...M.root().querySelectorAll('.ib-item[data-ibopen]')].filter(vis).find(x => !tried.has(x.dataset.ibopen) && /to decide/.test(x.innerText));
    if (!it) break; tried.add(it.dataset.ibopen);
    const c = DB.comms.find(x => x.id === it.dataset.ibopen); if (!c) continue;
    const toChen = /chen@/.test(JSON.stringify([c.to, c.cc]));
    const mineKinds = (c.proposals || []).filter(pr => pr.status !== 'applied' && KINDS[roleName].test(pr.kind) && !(roleName !== 'coord' && pr.kind === 'bill' && toChen) && !(pr.kind === 'unrouted' && pr.as !== 'vendor'));
    if (!mineKinds.length) continue;
    it.click(); await sleep(20);
    for (const pr of mineKinds) { if (done >= cap) break;
      const b = [...document.querySelectorAll('[data-cmapply]')].find(x => vis(x) && x.dataset.cmapply === c.id + '|' + pr.id); if (!b) continue;
      const t0 = M.toasts.length; b.click(); await sleep(25); const steps = await M.drive(SAY[roleName]); done++;
      did('Inbox', `${c.subject} · ${pr.kind}: ${pr.summary || ''}`, 'Apply', { steps, toast: M.toasts.slice(t0).join(' | ') }); }
    const back = [...document.querySelectorAll('[data-ibback]')].find(vis); back && back.click();
  }
  return done;
};
// ---- one screen further in: the steps a role takes from what its screens show (the function each button calls)
M.extras = {};
M.extras.pm = async (uid, cap, did, o) => {
  let n = 0; const p = projOf('p121'); const seen = ((M.texts.home || '') + ' ' + (M.texts.tkall || '') + ' ' + (M.texts.mapprove || '')).slice(0, 80000);
  // an extra answered "Proceed as an extra" leaves "Write change order: X" on his list: raise it, price it from the item, send it
  for (const pr of DB.projects) for (const a of (pr.actions || []).filter(a => /^Write change order: /.test(a.title) && a.status !== 'done')) {
    if (n >= cap) break; if (!seen.includes('Write change order')) continue;
    const r = (DB.field.raises || []).find(x => x.id === a.raiseId); if (!r || r.coId) continue;
    const amt = +((String(r.note || '') + ' ' + r.title).match(/\$([\d,]+)/) || [, '0'])[1].replace(/,/g, '');
    setCurrent(pr.id); const co = opsRaiseCO({ kind: 'raise', id: r.id }); if (!co) continue; r.coId = co.id;
    const res = await M.sendCO(co, amt); if (res.sent) a.status = 'done'; n++;
    did('Tasks', a.title, 'fn:Write Change Order + price + Send to Client', res);
  }
  // a client's choice over the allowance leaves "Raise the $X change order": raise it from the decision
  for (const pr of DB.projects) for (const a of (pr.actions || []).filter(a => /^Raise the \$[\d,]+ change order/.test(a.title) && a.status !== 'done')) {
    if (n >= cap) break; if (!seen.includes('change order')) continue;
    const d = (pr.decisions || []).find(x => a.source && x.id === a.source.id) || (pr.decisions || []).find(x => x.status !== 'open' && !x.coId && x.chosen && +(x.chosen.delta || 0) > 0);
    if (!d || d.coId) continue; setCurrent(pr.id); const co = opsRaiseCO({ kind: 'dec', id: d.id }); if (!co) continue;
    const res = await M.sendCO(co, +(a.title.match(/\$([\d,]+)/) || [, '0'])[1].replace(/,/g, '')); if (res.sent) a.status = 'done'; n++;
    did('Tasks', a.title, 'fn:Raise Change Order + Send to Client', res);
  }
  // an inspection window he can read on his screens (DOB NOW notice in the Inbox, a field item) is booked on the inspection record
  const inbox = M.open('comms', true);
  const wins = [...(seen + ' ' + inbox).matchAll(/(rough plumbing|rough electrical)[^.]{0,90}?(?:window|scheduled)[^0-9]{0,14}(\d{2})\/(\d{2})\/(\d{4})/gi)];
  for (const w of wins) { if (n >= cap) break; const id = /plumb/i.test(w[1]) ? 'i3' : 'i4', date = `${w[4]}-${w[2]}-${w[3]}`;
    const ins = (p.inspections || []).find(x => x.id === id); if (!ins || ins.date === date || date < today()) continue;
    setCurrent(p.id); ins.status = 'scheduled'; ins.date = date; ins.notes = [ins.notes, `Booked from the DOB NOW window ${date}`].filter(Boolean).join(' · '); save();
    n++; did('Permits', `${ins.name} ${date}`, 'fn:inspection record (Permits > row > status + date > Save)', { steps: ['scheduled', date] }); }
  n < cap && (n += await M.inbox(uid, 'pm', cap - n, did));
  // a client's question on his Inbox gets an answer in the job's Chat (the Messages composer)
  const inboxNow = M.open('comms');
  for (const c of (DB.comms || []).filter(c => (c.route || {}).clientId && (c.route || {}).projectId && c.direction !== 'out' && String(c.date || '').slice(0, 10) >= iso(addDays(today(), -5)))) {
    if (n >= cap) break; const key = 'reply|' + c.id; if (M.memo[key]) continue;
    const from = String((c.from || {}).email || (c.from || {}).name || ''); if (/smartdesign/.test(from)) continue;
    if (!/\?/.test(c.text || '') || !inboxNow.includes(String(c.subject || '').slice(0, 30))) continue;
    M.memo[key] = today(); setCurrent(c.route.projectId);
    const r = await M.chat('Hi — to your question: yes, that is included; I will confirm the details on site this week. Alan'); n++;
    did('Inbox', c.subject, 'fn:reply in the job Chat', { steps: [r] });
  }
  n < cap && (n += await M.doneMine(uid, cap - n, did));
  return n;
};
M.sendCO = async (co, amt) => {
  const c = DB.clients.find(x => (x.changeOrders || []).some(d => d.id === co.id)), steps = [];
  const l = (co.lines || [])[0]; if (l && amt > 0 && !(+l.rate > 0)) { l.rate = amt; steps.push('price ' + amt); }
  save();
  if (!(co.lines || []).some(x => +x.rate > 0)) { steps.push('no price on his screens: left as a draft'); return { steps, sent: false }; }
  const t0 = M.toasts.length;
  try { await docAction(c, co, 'send'); steps.push(...await M.drive({ say: 'Please review and sign.', name: 'Alan' }, '^Send$')); } catch (e) { steps.push('send failed: ' + e.message); }
  return { steps, sent: ['sent', 'approved'].includes(co.status), toast: M.toasts.slice(t0).join(' | ') };
};
M.extras.coord = async (uid, cap, did) => {
  let n = await M.inbox(uid, 'coord', cap, did); const p = projOf('p121'); setCurrent(p.id);
  // receive what is due today (it is on the foreman's Arriving list): Received, then Bill It
  for (const po of (DB.pos || []).filter(x => x.projectId === p.id && ['issued', 'partial'].includes(x.status) && x.expected && x.expected <= today())) {
    if (n >= cap) break; const t0 = M.toasts.length; try { setCurrent(p.id); poAction(po, 'receive'); save(); render(); } catch (e) {}
    n++; did('Deliveries', `${po.number} ${po.vendor}`, 'fn:Received', { steps: ['received ' + po.status], toast: M.toasts.slice(t0).join(' | ') });
    if (n < cap && typeof lkBillPO === 'function') { try { const t1 = M.toasts.length; lkBillPO(po); const st = await M.drive(Object.assign({}, SAY.coord, { say: po.number + '-R' })); n++; did('Deliveries', po.number, 'fn:Bill It', { steps: st, toast: M.toasts.slice(t1).join(' | ') }); } catch (e) {} }
  }
  n < cap && (n += await M.doneMine(uid, cap - n, did));
  // order what is late to order and priced (a vendor and a price on the line): New PO > vendor > from materials > Create, then Issue PO
  const board = M.open('home');
  for (const m of p.materials.filter(m => ['not-ordered', 'quoted'].includes(m.status) && m.vendor && m.vendor !== 'TBD' && +String(m.cost || '').replace(/[^\d.]/g, '') > 0)) {
    if (n >= cap) break;
    if ((DB.pos || []).some(po => po.status !== 'cancelled' && (po.lines || []).some(l => l.materialId === m.id))) continue;
    const res = await M.newPO(p, m); n++; did('Buy Board', `${m.name} · ${m.vendor} · ${m.cost}`, 'fn:New PO + Issue PO', res);
  }
  return n;
};
M.newPO = async (p, m) => {
  setCurrent(p.id); const steps = [], t0 = M.toasts.length;
  try { newPODialog(); await sleep(15);
    const set = (s, v) => { const e = document.querySelector(s); if (e) { e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); } };
    set('#e-vendor', m.vendor); set('#e-src', 'mats'); set('#e-expected', iso(addWork(today(), Math.max(3, +m.lead || 5))));
    const n0 = DB.pos.length; document.querySelector('#d-save').click(); await sleep(40);
    if (DB.pos.length === n0) { closeAll(); return { steps: ['Create draft made nothing'] }; }
    const po = DB.pos[DB.pos.length - 1]; po.lines = po.lines.filter(l => l.materialId === m.id); save();
    steps.push(`draft ${po.number} ${po.vendor} $${typeof poTotal === 'function' ? poTotal(po).total : '?'}`);
    poAction(po, 'issue'); save(); render(); steps.push('issue: ' + po.status);
    steps.push(...await M.drive(SAY.coord));
  } catch (e) { steps.push('failed ' + e.message); closeAll(); }
  return { steps, toast: M.toasts.slice(t0).join(' | ') };
};
M.extras.billing = async (uid, cap, did) => {
  let n = await M.inbox(uid, 'billing', cap, did);
  n < cap && (n += await M.doneMine(uid, cap - n, did));
  // money in: a deposit on Banking with a client's name, and an open invoice of theirs: Record Payment on that invoice
  const bankText = M.open('bank');
  for (const c of DB.clients) { if (n >= cap) break;
    const word = String(c.name).replace(/family|LLC|&|The/g, ' ').split(/\s+/).filter(w => w.length > 3).pop(); if (!word) continue;
    const t = (DB.txns || []).find(t => +t.amt > 0 && t.acct === 'ac1' && RX(word).test(t.desc) && !M.used.has(t.id) && t.date >= '2026-09-03' && bankText.toUpperCase().includes(String(t.desc).slice(0, 14).toUpperCase()));
    if (!t) continue;
    const inv = (c.invoices || []).filter(i => ['sent', 'partial', 'overdue'].includes(i.status)).sort((a, b) => String(a.date).localeCompare(b.date))[0];
    M.used.add(t.id);
    if (!inv) { n++; did('Banking', `${t.desc} ${t.amt}`, 'nothing to apply it to', { steps: ['no open invoice for ' + c.name] }); continue; }
    const t0 = M.toasts.length, steps = [];
    try { clientOpen = c.id; await docAction(c, inv, 'pay'); await sleep(40);   // Record Payment: amount received, date, method, reference, Apply Oldest First, Record
      const set = (s_, v) => { const e = document.querySelector(s_); if (e) { e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); } };
      set('#py-amt', String(+t.amt)); set('#py-date', t.date); set('#py-method', /WIRE/.test(t.desc) ? 'Wire' : /ZELLE|ACH/.test(t.desc) ? 'ACH' : 'Check'); set('#py-ref', t.desc);
      const oldest = [...document.querySelectorAll('#mbm button')].find(b => /Apply Oldest First/.test(b.innerText)); oldest && oldest.click(); await sleep(15);
      steps.push('received ' + t.amt);
      steps.push(...await M.drive(Object.assign({}, SAY.billing, { say: t.desc }), '^Record$'));
    } catch (e) { steps.push('failed: ' + e.message); }
    n++; did('Invoices', `${inv.number} · ${t.desc} ${t.amt}`, 'fn:Record Payment', { steps, toast: M.toasts.slice(t0).join(' | ') });
  }
  return n;
};
const CTL_KNOW = [  // what a controller knows about a line from its description, and nothing else
  [/RESTORATION HARDWARE|WATERWORKS|DIAMOND APPL|FERGUSON|GOWANUS STONE/i, 'materials'], [/SCAFFOLD/i, 'equipment'], [/DUMPSTER/i, 'disposal'],
  [/HOME DEPOT|LOWES|LUMBER|GRK|SQ \*BROOKLYN/i, 'materials'], [/SHELL|EZPASS/i, 'vehicle'], [/GEICO/i, 'insurance'], [/CON ED|VERIZON|ADOBE|AMAZON/i, 'office'],
  [/CHIPOTLE/i, 'meals'], [/RENT|400 ATLANTIC/i, 'office'], [/DEPT OF BUILDINGS/i, 'permits'], [/SERVICE FEE/i, 'office'], [/ZELLE TO|CHECK \d+ /i, 'subs'],
  [/AMEX EPAYMENT/i, 'cc-payment'], [/WIRE IN|MOBILE DEPOSIT|ZELLE FROM|INTEREST/i, 'income'] ];
M.extras.controller = async (uid, cap, did) => {
  let n = await M.inbox(uid, 'controller', Math.min(4, cap), did); const td = today();
  // payroll: the payroll service's deadline is in his Inbox; build the run from approved time and approve it
  const inboxText = M.open('comms');
  if (/payroll for \d+\/\d+/i.test(inboxText) && n < cap && !M.memo['payroll|' + inboxText.match(/payroll for (\d+\/\d+)/i)[1]]) {
    M.memo['payroll|' + inboxText.match(/payroll for (\d+\/\d+)/i)[1]] = td;
    const before = DB.payroll.length, t0 = M.toasts.length;
    try { view = 'ap'; render(); payrollFromTime(); await sleep(20); await M.drive(SAY.controller); } catch (e) {}
    const made = DB.payroll.slice(before); n++;
    did('Bills & Payroll', 'payroll from approved time', 'fn:Build Payroll from Approved Time', { steps: [made.length + ' run(s) built: ' + made.map(r => r.period + ' $' + r.total).join(', ')], toast: M.toasts.slice(t0).join(' | ') });
    for (const r of made) { try { const t1 = M.toasts.length; payrollAction(r, 'approve'); await M.drive(SAY.controller);
      did('Bills & Payroll', 'approve run ' + r.period, 'fn:Approve Payroll', { steps: [r.status], toast: M.toasts.slice(t1).join(' | ') }); n++; } catch (e) {} }
  }
  // code what the suggestions did not reach, from the description on the line (the transaction drawer)
  const bank = M.open('bank');
  const JOBCAT = /materials|subs|equipment|permits|disposal/;
  for (const t of (DB.txns || []).filter(t => (t.status === 'new' || t.cat === 'uncat' || !t.cat || (JOBCAT.test(t.cat) && !t.projectId && +t.amt < 0)) && t.date >= '2026-09-03' && bank.toUpperCase().includes(String(t.desc).slice(0, 12).toUpperCase()))) {
    if (n >= cap) break; const k = CTL_KNOW.find(([re]) => re.test(t.desc)); if (!k) continue;
    const t0 = M.toasts.length;
    try { txnDialog(t.id); await sleep(15); const sel = document.querySelector('#e-cat'); const opt = sel && [...sel.options].find(o => RX(k[1]).test(o.value + ' ' + o.text));
      if (opt) { sel.value = opt.value; sel.dispatchEvent(new Event('change', { bubbles: true })); }
      if (JOBCAT.test(k[1])) { const pj = document.querySelector('#e-proj'); if (pj && !pj.value) { pj.value = /LOWES/.test(t.desc) ? 'p206' : 'p121'; pj.dispatchEvent(new Event('change', { bubbles: true })); } }
      const sv = document.querySelector('#d-save'); sv && sv.click(); await sleep(20); closeAll();
    } catch (e) {}
    n++; did('Banking', `${t.desc} ${t.amt}`, 'fn:code in the transaction drawer', { steps: [t.cat + ' ' + (t.projectId || '')], toast: M.toasts.slice(t0).join(' | ') });
  }
  n < cap && (n += await M.doneMine(uid, cap - n, did));
  // what the Not Matched count on Banking holds: a charge twice is voided with a reason; a line with a proposed match is matched
  let U = []; try { U = bankUnmatched().rows.filter(t => t.date >= '2026-08-01' && !t.exception); } catch (e) {}
  for (const t of U) { if (n >= cap) break; const key = 'match|' + t.id; if (M.memo[key] && workBetween(M.memo[key], td) < 3) continue; M.memo[key] = td;
    const twin = (DB.txns || []).find(x => x.id !== t.id && x.acct === t.acct && x.desc === t.desc && Math.abs(+x.amt - +t.amt) < 0.01 && x.date < t.date && Math.abs(dayDiff(x.date, t.date)) <= 3);
    const t0 = M.toasts.length; let steps = [];
    try { txnDialog(t.id); await sleep(15);
      if (twin) { const v = document.querySelector('#d-delete'); if (v && vis(v)) { v.click(); await sleep(20); steps = await M.drive(Object.assign({}, SAY.controller, { say: 'Charged twice; the second charge is disputed with the card issuer.', never: null })); } else steps.push('no Void on the line'); }
      else { const mb = [...document.querySelectorAll('#drawer [data-trmatch], [data-trmatch]')].find(vis); if (mb) { mb.click(); await sleep(20);
          const m = document.querySelector('#mbm'), pickB = m && [...m.querySelectorAll('[data-trpick]')].find(b => /proposed/.test(norm((b.closest('tr') || {}).innerText)));
          if (pickB) { pickB.click(); await sleep(20); steps.push('matched: ' + norm((pickB.closest('tr') || {}).innerText).slice(0, 60)); } else steps.push('no proposed line to match'); } }
    } catch (e) { steps.push('failed ' + e.message); }
    closeAll(); n++; did('Banking', `${t.desc} ${t.amt}`, twin ? 'fn:Void… (a duplicate charge)' : 'fn:Match to a Line…', { steps, toast: M.toasts.slice(t0).join(' | ') }); }
  // the September close on 10/1
  if (td >= '2026-10-01' && typeof ctCloseStatus === 'function' && !ctCloseStatus('2026-09').closed && n < cap) {
    const t0 = M.toasts.length; let res;
    try { res = await fin2RunClose('2026-09', 'September close: every line matched or excepted, the WIP tied.'); } catch (e) { res = 'refused: ' + (e.message || e); }
    const st = await M.drive(SAY.controller); n++;
    did('Close', 'Run the September 2026 close', 'fn:Run the Close', { steps: [String(typeof res === 'object' ? JSON.stringify(res) : res).slice(0, 160)].concat(st), toast: M.toasts.slice(t0).join(' | ') });
  }
  return n;
};
M.extras.designer = async (uid, cap, did) => { let n = 0; const seen = (M.texts.sday || '') + ' ' + (M.texts.tkall || '');
  for (const p of DB.projects) for (const a of (p.actions || []).filter(a => /Sarah/.test(a.assignee || '') && a.status !== 'done' && a.due && a.due <= today())) {
    if (n >= cap) break; if (!seen.includes(a.title.slice(0, 22))) continue;
    a.status = 'done'; a.completedAt = today(); save(); n++; did('My Day', a.title, 'fn:mark the task done', { steps: ['done'] }); }
  return n; };
M.doneMine = async (uid, cap, did) => { let n = 0; const me = (currentUser() || {}).name || '';
  const seen = Object.values(M.texts).join(' ');
  const skip = /^(Write change order|Raise the \$)|change order|inspection|Inspection|COI|PO\b/;
  for (const p of DB.projects) for (const a of (p.actions || []).filter(a => a.status !== 'done' && a.due && a.due <= today() && a.assignee && (me.split(' ')[0] && RX('^' + me.split(' ')[0]).test(a.assignee)))) {
    if (n >= cap) break; if (skip.test(a.title) || !seen.includes(a.title.slice(0, 20))) continue;
    a.status = 'done'; a.completedAt = today(); save(); n++; did('Tasks', a.title, 'fn:Done (Tasks > row > Done)', { steps: ['done'] }); }
  return n; };
M.extras.foreman = async () => 0;
M.extras.owner = async (uid, cap, did) => { let n = await M.inbox(uid, 'owner', Math.min(3, cap), did); return n + await M.doneMine(uid, cap - n, did); };
M.extras.driver = async (uid, cap, did) => { let n = 0; const route = M.open('route').toLowerCase();
  for (const p of DB.projects) for (const r of (p.requests || []).filter(r => r.status === 'ack' && route.includes(String(r.what).slice(0, 14).toLowerCase()))) {
    if (n >= cap) break; setCurrent(p.id); try { requestAction(p.id, r.id, 'delivered'); } catch (e) {}
    save(); n++; did('Route', `${r.qty} ${r.unit} ${r.what}`, 'fn:Bought and Dropped', { steps: [r.status] }); }
  return n; };
M.clockIn = async uid => { const p = projOf('p121'); setCurrent(p.id); const emp = myEmp(); if (!emp) return 'no employee';
  if ((DB.time || []).some(t => t.empId === emp.id && !t.out)) return 'already in'; await clockEvent('in'); return 'in'; };
M.evening = async (uid, roleName, own) => {   // the actor's afternoon events, the crew clocks out, the foreman signs the day's log
  M.as(uid); const out = [];
  for (const ev of (own || [])) { try { out.push([ev.id, String(await M.own(ev)).slice(0, 80)]); } catch (e) { out.push([ev.id, 'ERR ' + e.message]); } }
  if (/crew|foreman/.test(roleName)) { const p = projOf('p121'); setCurrent(p.id); const emp = myEmp();
    const e = emp && (DB.time || []).find(t => t.empId === emp.id && !t.out);
    if (e) { await clockEvent('out'); const e2 = DB.time.find(t => t.id === e.id);
      if (e2 && e2.status === 'open') { const h = Math.round((hoursOf(e2) || 8) * 4) / 4; e2.work = [{ projectId: p.id, code: '', hours: h, note: 'per the day' }]; e2.status = 'submitted'; save(); }
      out.push(['clock out', e2 && e2.status]); } }
  if (roleName === 'foreman') { const p = projOf('p121');
    if (typeof dlSubmit === 'function' && !(DB.field.logs || []).some(l => l.projectId === p.id && l.date === today())) {
      try { setCurrent(p.id); const dr = dlDraft(p, today()); dlSubmit(dr, p); out.push(['daily log', 'signed']); } catch (e) { out.push(['daily log', 'failed ' + e.message]); } } }
  return out;
};

// ============================================================================ checks (the ledger)
const allTasks = () => DB.projects.flatMap(p => (p.actions || []).map(a => Object.assign({ projectId: p.id }, a))).concat((DB.tasks || []).map(t => Object.assign({ projectId: '' }, t)));
const billsOf = n => (DB.bills || []).filter(b => String(b.number || '').toUpperCase() === String(n).toUpperCase());
const billOf = n => billsOf(n)[0];
const poNum = id => ((DB.pos || []).find(p => p.id === id) || {}).number || '';
const txnsLike = (d, amt) => (DB.txns || []).filter(t => String(t.desc || '').toUpperCase().includes(String(d).toUpperCase()) && (amt == null || Math.abs(+t.amt - amt) < 0.01));
const matchOf = t => { try { const m = truthMatchOf(t) || {}; return Object.values(m).some(Boolean) ? m : null; } catch (e) { return null; } };
const tot = d => { try { return +(docTotal(d).total || 0); } catch (e) { return 0; } };
const sentAfter = (re, after, fromRe) => {   // anything that went out to that party on or after a day: a mail sent or drafted, an outbox record
  const R = RX(re), out = [];
  (DB.outbox || []).forEach(o => { if (String(o.at || '') >= after && R.test(JSON.stringify(o.to || '') + ' ' + (o.subject || ''))) out.push('outbox ' + (o.status || '')); });
  Object.entries(DB.demoWs || {}).forEach(([u, A]) => (A.messages || []).forEach(m => { const day = appIso(new Date(m.internalDate)).slice(0, 10);
    if (day >= after && R.test(String(m.headers.To) + ' ' + m.headers.Subject) && (!fromRe || RX(fromRe).test(u))) out.push((m.labelIds || []).join('/').toLowerCase() + ' by ' + u); }));
  return out; };
M.check = (c, ev) => {
  const after = c.after || ev.day;
  try { switch (c.t) {
    case 'bill': { const B = billsOf(c.number); if (!B.length) return [false, 'no bill ' + c.number];
      const b = B[0]; const dup = B.length > 1 ? ` (${B.length} copies)` : '';
      if (c.poNumber && poNum(b.poId) !== c.poNumber) return [false, `entered on ${poNum(b.poId) || 'no PO'}, ${b.projectId || 'no job'}${dup}`];
      if (c.projectId && b.projectId !== c.projectId) return [false, `entered on ${b.projectId || 'no job'}${dup}`];
      if (c.status && !B.some(x => c.status.includes(x.status))) return [false, `${b.status}${dup}`];
      return [true, `${b.number} ${b.status} ${poNum(b.poId)}${dup}`]; }
    case 'billOnce': { const B = billsOf(c.number); return [B.length === 1, `${B.length} bills numbered ${c.number}`]; }
    case 'billShort': { const b = billOf(c.number); return [!!(b && b.short && Math.abs(+b.short.approved - c.approved) < 1), b ? `${b.status}${b.short ? ' short ' + b.short.approved : ''}` : 'no bill']; }
    case 'billShortAny': { const b = billOf(c.number); return [!!(b && (b.short || b.status === 'disputed')), b ? `${b.status}${b.short ? ' approved ' + b.short.approved : ''}` : 'no bill']; }
    case 'mat': { const p = projOf(c.project), m = p.materials.find(x => x.id === c.id); if (!m) return [false, 'no line'];
      const cost = +String(m.cost || '').replace(/[^\d.]/g, '');
      if (c.cost && Math.abs(cost - c.cost) > 1) return [false, `line at ${m.cost || 'no price'} · ${m.status}`];
      if (c.priced && !(cost > 0)) return [false, 'no price on the line'];
      if (c.status && !c.status.includes(m.status)) return [false, m.status];
      if (c.eta && m.eta !== c.eta) return [false, 'expected ' + (m.eta || 'no date')];
      return [true, `${m.status} ${m.cost || ''} ${m.vendor || ''}`]; }
    case 'po': { const P = (DB.pos || []).filter(po => po.projectId === c.project && !['cancelled', 'draft'].includes(po.status) &&
        (po.lines || []).some(l => (c.mat && l.materialId === c.mat) || (c.item && RX(c.item).test((l.item || '') + ' ' + (l.desc || '')))) && (!c.vendor || RX(c.vendor).test(po.vendor || '')));
      const good = P.filter(po => po.vendor && (typeof poTotal === 'function' ? poTotal(po).total : 1) > 0);
      return [good.length > 0, P.length ? P.map(po => `${po.number} ${po.vendor || 'NO VENDOR'} $${typeof poTotal === 'function' ? poTotal(po).total : '?'} ${po.status}`).join('; ') : 'no PO issued']; }
    case 'poEta': case 'poEtaAny': { const po = (DB.pos || []).find(p => c.number ? p.number === c.number : RX(c.vendor).test(p.vendor || ''));
      return [!!(po && po.expected === c.eta), po ? `${po.number} expected ${po.expected || 'no date'}` : 'no PO']; }
    case 'poStatus': { const po = (DB.pos || []).find(p => p.number === c.number); return [!!(po && c.status.includes(po.status)), po ? po.status : 'no PO']; }
    case 'coi': { const v = (DB.vendors || []).find(v => RX(c.vendor).test(v.name)); return [!!(v && v.insuranceExp && v.insuranceExp >= c.expAfter), v ? `insurance to ${v.insuranceExp || 'none on file'}` : 'vendor not on file']; }
    case 'outreach': { const s = sentAfter(c.to + (c.rx ? '|' + c.rx : ''), after, c.from); return [s.length > 0, s.length ? s.slice(0, 3).join(', ') : 'nothing went to them']; }
    case 'txn': { const T = txnsLike(c.desc, c.amt).filter(t => !c.after || t.date >= c.after);
      if (!T.length) return [false, (DB.voided || []).some(t => RX(c.desc).test(t.desc || '')) ? 'voided' : 'not in Banking'];
      const t = T[T.length - 1];
      if (c.resolved) return [!!(matchOf(t) || t.exception), `${t.status} ${t.cat}${t.exception ? ' excepted' : ''}`];
      if (c.matched && !matchOf(t) && !t.billId && !t.payrollId && !t.retId && !t.creditOf) return [false, `${t.status} · ${t.cat || 'uncat'} · ${t.projectId || 'no job'} · matched to no line${t.exception ? ' (exception signed)' : ''}`];
      if (c.coded && (!t.cat || t.cat === 'uncat' || t.status === 'new')) return [false, `${t.status} · ${t.cat || 'uncat'}`];
      if (c.project && t.projectId !== c.project) return [false, `${t.cat} on ${t.projectId || 'no job'}`];
      if (c.notIncome && /income|revenue|sales/.test(t.cat || '')) return [false, 'coded as income'];
      return [true, `${t.status} · ${t.cat} · ${t.projectId || ''}`]; }
    case 'dup': { const T = txnsLike(c.desc, c.amt).filter(t => !c.after || t.date >= c.after);
      const V = (DB.voided || []).filter(t => RX(c.desc).test(t.desc || ''));
      const ok = V.length > 0 || T.some(t => /dispute|duplicate|void/i.test(JSON.stringify([t.status, t.memo, t.ownerNote, t.cat, t.exception || '', t.dispute || ''])));
      return [ok, `${T.length} on file, ${V.length} voided${T.some(t => t.exception) ? ', an exception signed' : ''}`]; }
    case 'payment': { const cl = DB.clients.find(x => x.id === c.client);
      const P = (cl && cl.payments || []).filter(py => py.date >= ev.day && Math.abs(+py.amount - c.amount) < 1);
      return [P.length > 0, P.length ? `recorded ${P[0].date}` : 'no payment recorded']; }
    case 'invoice': { const cl = DB.clients.find(x => x.id === c.client);
      const I = (cl && cl.invoices || []).filter(i => (i.date || '') >= (c.after || '2026-09-03') && ['sent', 'paid', 'partial', 'overdue'].includes(i.status) && tot(i) >= c.amount - 1);
      const D = (cl && cl.invoices || []).filter(i => (i.date || '') >= (c.after || '2026-09-03') && i.status === 'draft');
      return [I.length > 0, I.length ? I.map(i => i.number + ' ' + i.status).join(', ') : D.length ? D.map(i => i.number + ' still a draft').join(', ') : 'nothing invoiced']; }
    case 'rebilled': { const T = txnsLike(c.desc, c.amt); const t = T[T.length - 1]; if (!t) return [false, 'no line'];
      const w = String(t.desc).split(' ').slice(0, 2).join(' ');
      const onInv = !!(t.invoiceLineId || t.billed || t.rebilled || (matchOf(t) || {}).invoiceLineId) || DB.clients.some(cl => (cl.invoices || []).some(i => (i.date || '') >= t.date && ['sent', 'paid', 'partial'].includes(i.status) &&
        (i.lines || []).some(l => RX(w).test((l.desc || '') + ' ' + (l.item || '')) || Math.abs((+l.rate || 0) * (+l.qty || 1) - Math.abs(t.amt)) < 1)));
      return [onInv, onInv ? 'on an invoice' : `${t.cat || 'uncat'} on ${t.projectId || 'no job'}, on no invoice`]; }
    case 'rtbGone': { const sp = typeof spUnbilled === 'function' ? spUnbilled() : []; const left = sp.filter(r => RX(c.rx).test(JSON.stringify([r.label, r.line && (r.line.item || r.line.desc)])));
      const amt = left.reduce((a, r) => a + (+r.gap || 0), 0); return [amt < 1, amt ? `$${Math.round(amt).toLocaleString()} still not billed` : 'billed']; }
    case 'raise': { const r = (DB.field.raises || []).filter(r => RX(c.title).test(r.title)).pop(); if (!r) return [false, 'no field item'];
      return [['answered', 'closed', 'done', 'resolved'].includes(r.status), `${r.status}${r.escalated ? ' (escalated)' : ''}`]; }
    case 'request': { const W = String(c.what).toLowerCase(), hit = r => /[|]/.test(c.what) ? RX(c.what).test(r.what + ' ' + (r.note || '')) : (r.what + ' ' + (r.note || '')).toLowerCase().includes(W);
      const R = DB.projects.filter(p => c.project === 'any' || p.id === c.project).flatMap(p => p.requests || []).filter(hit);
      const r = R[R.length - 1]; if (!r) return [false, 'not on the board']; return [c.status.includes(r.status), r.status]; }
    case 'task': { const T = allTasks().filter(a => RX(c.title).test(a.title || ''));
      const T2 = T.filter(a => (!c.assignee || RX(c.assignee).test(a.assignee || '')) && (!c.due || a.due === c.due) && (!c.dueOn || a.due === c.dueOn) && (!c.assigned || (a.assignee || '').trim()));
      if (!T2.length) return [false, T.length ? `no such task for ${c.assignee || 'its owner'} (nearest: ${T[0].title.slice(0, 30)} · ${T[0].assignee || 'nobody'} · due ${T[0].due || '-'})` : 'no task'];
      if (c.done) return [T2.some(a => a.status === 'done'), T2.map(a => a.status).join(',')];
      return [true, `${T2[0].assignee || ''} due ${T2[0].due || ''}`]; }
    case 'taskDone': { const t = (projOf(c.project).tasks || []).find(x => x.id === c.id); return [!!(t && (t.status === 'done' || t.pct >= 100)), t ? `${t.status} ${t.pct || 0}%` : 'no task']; }
    case 'insp': { const i = (projOf(c.project).inspections || []).find(x => x.id === c.id); if (!i) return [false, 'no inspection'];
      if (c.date && i.date !== c.date) return [false, `${i.status} ${i.date || 'no date'}`];
      if (c.status && !c.status.includes(i.status)) return [false, i.status];
      return [true, `${i.status} ${i.date}`]; }
    case 'co': { const cl = DB.clients.find(x => x.id === (projOf(c.project) || {}).clientId); const C = (cl && cl.changeOrders || []).filter(d => (d.date || '') >= ev.day &&
        (!c.rx || RX(c.rx).test(d.title + ' ' + (d.memo || '') + JSON.stringify(d.lines || []))) && (!c.amount || Math.abs(tot(d) - c.amount) < 2));
      return [C.some(d => c.status.includes(d.status)), C.length ? C.map(d => `${d.number} ${d.status} $${tot(d)}`).join(', ') : 'no change order']; }
    case 'coStatus': { const d = DB.clients.flatMap(x => x.changeOrders || []).find(d => d.number === c.number); return [!!(d && c.status.includes(d.status)), d ? d.status : 'none']; }
    case 'coResolved': { const cl = DB.clients.find(x => x.id === (projOf(c.project) || {}).clientId); const C = (cl && cl.changeOrders || []).filter(d => RX(c.rx).test(d.title + JSON.stringify(d.lines || [])));
      return [C.some(d => /-R\d/.test(d.number) || ['void', 'withdrawn', 'rejected'].includes(d.status) || (d.status === 'approved' && String(d.approvedOn || d.date || '') >= ev.day)), C.map(d => d.number + ' ' + d.status).join(', ') || 'no CO']; }
    case 'coBilled': { let gap = 0; try { const R = readyToBill(); gap = (R.rows || []).concat(R.held || []).filter(r => (r.p || {}).id === 'p121' && /CO-/.test(JSON.stringify([r.label, r.what, r.name, r.why]))).reduce((a, r) => a + (+r.amount || 0), 0); } catch (e) {}
      const cl = DB.clients.find(x => x.id === c.client); const ap = (cl.changeOrders || []).filter(d => d.status === 'approved' && (d.date || '') >= '2026-09-01');
      const billed = (cl.invoices || []).filter(i => (i.date || '') >= '2026-09-03' && i.status !== 'draft').some(i => (i.lines || []).some(l => /CO-/.test((l.desc || '') + (l.item || '') + (l.source || ''))));
      return [billed || !ap.length, billed ? 'CO lines on an invoice' : `${ap.map(d => d.number).join(', ')} approved, on no invoice`]; }
    case 'decision': { const d = (projOf(c.project).decisions || []).find(x => x.id === c.id); if (!d) return [false, 'none'];
      const by = String(d.decidedBy || ''), ch = String(d.choice || d.decision || '');
      if (c.choice && !RX(c.choice).test(ch)) return [false, `${d.status}: ${ch.slice(0, 40)}${by ? ' (by ' + by + ')' : ''}`];
      if (c.notBy && RX(c.notBy).test(by)) return [false, `the client had to choose again on the portal: ${ch.slice(0, 30)}`];
      return [d.status !== 'open', `${d.status}${ch ? ': ' + ch.slice(0, 30) : ''}${by ? ' (by ' + by + ')' : ''}`]; }
    case 'subm': { const s = (typeof smOf === 'function' ? smOf(projOf(c.project)) : []).find(x => x.id === c.id); return [!!(s && c.status.includes(s.status)), s ? s.status : 'none']; }
    case 'meeting': { const m = (DB.meetings || []).filter(m => RX(c.rx).test(m.title || '')).pop(); if (!m) return [false, 'not ingested'];
      const open = (m.proposals || []).filter(x => x.status === 'proposed').length; return [open === 0, `${open} proposals still waiting`]; }
    case 'meetingFrom': { const m = (DB.meetings || []).find(m => RX(c.rx).test((m.title || '') + ' ' + (m.source || ''))); return [!!m, m ? 'ingested as a meeting' : 'only a file']; }
    case 'lesson': { const L = (DB.lessons || []).filter(l => RX(c.rx).test((l.title || '') + ' ' + (l.trigger || '') + ' ' + (l.why || '')) && String(l.at || '') >= c.after);
      const fired = (DB.lessons || []).filter(l => RX(c.rx).test((l.title || '') + ' ' + (l.trigger || '')) && (l.fired || []).some(f => String(f.at || f.on || f || '') >= c.after));
      let sug = []; try { sug = (bnSuggestLessons() || []).filter(s => RX(c.rx).test(JSON.stringify(s))); } catch (e) {}
      return [L.length + fired.length > 0, L.length ? 'lesson: ' + L[0].title.slice(0, 40) : fired.length ? 'a lesson fired' : sug.length ? 'suggested only on The Brain page' : 'no lesson']; }
    case 'payroll': { const r = DB.payroll.find(x => x.id === c.id); return [!!(r && c.status.includes(r.status)), r ? r.status : 'none']; }
    case 'payrollRun': { const R = DB.payroll.filter(x => x.id !== 'pr1' && ((x.from && x.from <= c.to && (x.to || '') >= c.from) || (x.payDate && x.payDate >= c.from && x.payDate <= iso(addDays(c.to, 6)))));
      const r = R[R.length - 1];
      if (!r) return [false, 'no run built'];
      if (c.approved && !['approved', 'paid'].includes(r.status)) return [false, `${r.period} ${r.status}`]; return [true, `${r.period} ${r.status} $${r.total}`]; }
    case 'hours': { const T = (DB.time || []).filter(t => t.date >= c.from && t.date <= c.to && t.out); if (!T.length) return [false, 'no hours'];
      const open = T.filter(t => t.status !== 'approved'); return [open.length === 0, `${open.length} of ${T.length} entries not approved`]; }
    case 'logs': { const L = (DB.field.logs || []).filter(l => l.projectId === c.project); const miss = c.days.filter(d => !L.some(l => l.date === d));
      return [miss.length === 0, miss.length ? 'missing ' + miss.map(d => d.slice(5)).join(', ') : 'all filed']; }
    case 'recon': { const R = (DB.bankRecons || []).filter(r => r.acctId === c.acct && String(r.end || '').slice(0, 7) === c.month); return [R.length > 0, R.length ? 'reconciled' : 'not reconciled']; }
    case 'close': { const s = ctCloseStatus(c.ym); return [!!s.closed, s.closed ? 'closed' : String((s.blockers || []).slice(0, 2).join(' / ') || s.headline || 'open').slice(0, 160)]; }
    case 'unmatched': { let n = 0, ex = 0; try { const by = PRED.unmatchedTxns.byMonth(); n = (by[c.month] || {}).n || 0; ex = (by[c.month] || {}).excepted || 0; } catch (e) {}
      return [n - ex <= c.max, `${n} lines not matched (${ex} excepted)`]; }
    case 'journal': { const J = [].concat(DB.gl && DB.gl.journals || [], DB.journals || [], DB.gl && DB.gl.drafts || []).filter(j => RX(c.rx).test(JSON.stringify(j).slice(0, 3000)));
      return [J.some(j => j.status === 'posted' || j.approvedBy), J.length ? J.map(j => j.status).join(',') : 'never drafted']; }
    case 'seenBy': { const s = M.seenLog[ev.id] && M.seenLog[ev.id][c.uid]; return [!!s, s ? `seen ${s[0]} on ${s[1]}` : 'not on their screens']; }
    case 'ignored': { const C = (DB.comms || []).filter(x => x.subject === c.subject); if (!C.length) return [false, 'not read'];
      return [C.every(x => x.status === 'ignored' || !(x.proposals || []).length), C.map(x => x.status + ' ' + (x.proposals || []).map(p => p.kind).join('/')).join(', ')]; }
    case 'lead': { const L = (DB.leads || []).filter(l => RX(c.name).test(l.name)); const H = DB.hub ? (DB.hub.contacts || []).filter(x => RX(c.name).test(`${x.first} ${x.last}`)) : [];
      return [L.length + H.length > 0, L.length ? 'lead at ' + L[0].stage : H.length ? 'a contact' : 'not on file']; }
    case 'oblig': { const o = (DB.obligations || []).find(o => RX(c.rx).test(o.name)); return [!!(o && (o.expires > '2026-09-28' || /renewed|done|filed/.test(o.status))), o ? `${o.status}, expires ${o.expires}` : 'none']; }
    case 'riveraFixed': { const cl = DB.clients.find(x => x.id === 'cl45'); const P = (cl.payments || []).filter(p => [5000, 16350].includes(+p.amount));
      const bad = P.filter(p => !(DB.txns || []).some(t => Math.abs(+t.amt - +p.amount) < 1 && t.acct === 'ac1')); return [bad.length === 0, bad.length + ' recorded payments still not in the bank']; }
    case 'clientCredit': { const cl = DB.clients.find(x => x.id === c.client); const ok = (cl.invoices || []).concat(cl.creditMemos || []).some(i => (i.date || '') >= ev.day && (i.lines || []).some(l => +l.rate < 0 || /credit/i.test((l.desc || '') + ' ' + (l.item || ''))));
      return [ok, ok ? 'credited to the client' : 'no credit to the client']; }
    case 'clientAnswered': { const p = projOf(c.project), CH = p.chat || [];
      const q = CH.findIndex(m => RX(c.rx).test(m.text || ''));
      const after_ = CH.filter(m => String(m.ts || m.at || '').slice(0, 10) >= ev.day || CH.indexOf(m) > q);
      const ans = (q >= 0 ? CH.slice(q + 1) : after_).some(m => m.by && !/Klein|Cambri|Jessop|client/i.test(m.by + ' ' + (m.role || '')));
      const comm = (DB.comms || []).filter(x => RX(c.rx).test((x.subject || '') + ' ' + (x.text || '')));
      return [!!ans, ans ? 'answered in the chat' : q >= 0 ? 'asked in the chat, no answer' : comm.length ? 'in the Inbox: ' + comm.map(x => x.status).join(',') : 'the question never landed']; }
    case 'confirmSub': { const p = projOf('p121'), t = p.tasks.find(x => x.id === 'rest'); const hist = JSON.stringify([t.history || [], t.log || [], t.moves || []]);
      const ok = allTasks().some(a => RX(c.rx).test(a.title) && /confirm|rebook|book/i.test(a.title)) || /no-?show|did not show/i.test(hist);
      return [ok, ok ? 'rebooked or slipped' : 'no rebook, no slip, no confirm-the-day-before']; }
    case 'fileRouted': { const f = (DB.gdrive || []).find(f => RX(c.rx).test(f.name)); return [!!(f && f.route && f.route.projectId === c.project), f ? 'routed to ' + ((f.route || {}).projectId || 'no job') : 'not pulled']; }
    case 'calendar': { const E = (DB.calendar.external || []).filter(e => e.owner === c.uid && RX(c.rx).test(e.title || '') && String(e.start || '').slice(0, 10) === c.day);
      return [E.length > 0, E.length ? 'on the calendar' : 'not on the calendar']; }
    case 'noDupBill': { const B = (DB.bills || []).filter(b => RX(c.rx).test(JSON.stringify([b.number, b.notes, b.lines])) || (Math.abs(billTotal(b) - c.amount) < 0.5 && /Brooklyn Lumber/i.test(b.vendor)));
      const unpaid = B.filter(b => !['paid', 'void', 'rejected'].includes(b.status)); return [unpaid.length === 0, unpaid.length ? `a second bill: ${unpaid.map(b => b.number + ' ' + b.status).join(', ')}` : 'no second bill']; }
    case 'noBillFrom': { const B = (DB.bills || []).filter(b => RX(c.rx).test(b.vendor + ' ' + (b.notes || ''))); return [B.length === 0, B.length ? 'a bill made from money coming in' : 'no bill']; }
    case 'disputeResolved': { const b = billOf(c.number); const ok = !!(b && b.short && (b.short.resolved || b.short.credited || b.short.closed || /resolved|credited|closed/.test(b.short.status || '')));
      return [ok, b ? (b.short ? 'dispute open: ' + JSON.stringify(b.short).slice(0, 70) : 'never disputed') : 'no bill']; }
    case 'lineBilled': { const p = projOf(c.project); let rows = []; try { rows = pgRows(p.id); } catch (e) {}
      const t = p.tasks.find(x => x.id === c.taskId), name = t ? t.name : c.taskId;
      let code = ''; try { code = codeForTrade(t.trade, t.name); } catch (e) {}
      let line = null; try { line = (tpJobPctDetail(p).lines || []).find(L => L.x && L.x.code === code); } catch (e) {}
      const r = line ? rows.find(x => x.sv.id === line.x.sv.id) : null;
      if (!r) return [false, 'no pay-application line for ' + name + (code ? ' (code ' + code + ')' : '')];
      const billed = +((r.ev || {}).billedPct || 0), meas = +(line.pct != null ? line.pct : ((r.pr || {}).pct || 0)), gap = Math.max(0, Math.min(meas, c.pct) - billed);
      M.lineGap[ev.id] = Math.round((+line.x.value || +r.sv.scheduled || 0) * gap / 100);
      return [billed >= Math.min(meas, c.pct) - 1, `${String(r.sv.desc).slice(0, 30)}: measured ${Math.round(meas)}%, billed ${billed}%`]; }
    default: return [false, 'unknown check ' + c.t];
  } } catch (e) { return [false, 'check error: ' + String(e.message || e).slice(0, 100)]; }
};
M.checkAll = (list) => list.map(([c, ev]) => M.check(c, ev));
return true;
}
