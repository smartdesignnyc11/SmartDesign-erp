// sim/page_tools.js: the world server's in-page half (BACKLOG §1.17). Installed by sim/server.py into every
// person's page after each boot. ONLY the server calls these; the agents' toolkit (sim/act) never evaluates
// JavaScript. It reads what a person can see (the open sheet, the view, the toast, the menu) into compact
// text with numbered controls, resolves a number back to its element, and runs the Demo Workspace mailbox
// the way Gmail on the person's phone would. Nothing here writes app records except the mailbox
// (DB.demoWs, the same store the app's own demo Gmail writes) and the "read" flag on a message.
() => {
if (window.__SIM) return 'ok';
const S = window.__SIM = { ctl: [], sig: [], toasts: [], errs: [], lastScreen: '' };
const norm = s => String(s == null ? '' : s).replace(/\s+/g, ' ').trim();
const vis = el => { if (!el || !el.isConnected || !el.getClientRects().length) return false;
  const cs = getComputedStyle(el); return cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity !== 0; };
// the app's own timers would run a watcher or the brain at a wall-clock moment; the world runs them instead
try { clearInterval(bnTimer); bnTimer = 1; } catch (e) {}
try { clearInterval(gsTimerId); } catch (e) {}
// only the person whose turn it is may write the shared database (an idle page's stale timer must not)
try { if (!window.__simGate) { const base = idbSet; window.__simGate = true;
  idbSet = async function (k, v) { if (window.__simActive === false) { window.__simDropped = (window.__simDropped || 0) + 1; return false; } return base(k, v); }; } } catch (e) {}
(() => { const t = document.getElementById('toast'); if (!t) return;
  new MutationObserver(() => { const x = norm(t.innerText); if (x && S.toasts[S.toasts.length - 1] !== x) S.toasts.push(x.slice(0, 240)); })
    .observe(t, { childList: true, subtree: true, characterData: true }); })();
window.addEventListener('error', e => S.errs.push(String(e.message || e).slice(0, 200)));

// ------------------------------------------------------------------ what is on the screen
S.overlays = () => {
  const c = [...document.querySelectorAll('#mbm, .mbm, #drawer.on, #viewer.on, [role=dialog], [aria-modal=true], .sheet.on, .msheet.on, .cmdk.on, #cmdk.on')].filter(vis);
  return c.filter(el => !c.some(o => o !== el && o.contains(el)));
};
S.viewRoot = () => document.querySelector('section.view.on') || document.querySelector('main') || document.body;
const BLOCKS = /^(block|flex|grid|table|table-row|list-item|table-caption)$/;
const CTL_TAGS = { BUTTON: 1, A: 1, INPUT: 1, SELECT: 1, TEXTAREA: 1, SUMMARY: 1 };
const isCtl = el => {
  const tg = el.tagName;
  if (tg === 'SECTION' || tg === 'BODY' || tg === 'NAV' || tg === 'FORM' || tg === 'TABLE' || tg === 'TBODY') return false;
  if (CTL_TAGS[tg]) {
    if (tg === 'A' && !el.getAttribute('href') && !el.onclick && !Object.keys(el.dataset).length) return false;
    if (tg === 'INPUT' && el.type === 'hidden') return false;
    return true;
  }
  const r = el.getAttribute('role');
  if (r && /^(button|tab|link|checkbox|radio|switch|menuitem|option)$/.test(r)) return true;
  if (el.onclick) return true;
  if (el.isContentEditable && el.getAttribute('contenteditable') !== null) return true;
  // the app delegates most clicks from a data-* attribute (e.target.closest('[data-myreq]')), often with no pointer cursor
  const ds = Object.keys(el.dataset || {}).filter(k => !NOT_ACTION.test(k));
  if (!ds.length) return getComputedStyle(el).cursor === 'pointer' && !!el.parentElement && getComputedStyle(el.parentElement).cursor !== 'pointer' && /^(DIV|LI|TR|SPAN|TD|IMG|LABEL)$/.test(tg) && !!norm(el.innerText);
  return true;
};
const NOT_ACTION = /^(simn|simfile|booted|role|scope|trWatch|tip|tt|title|theme|testid|count|n|w|h|pct|tone|sev|state|lvl|level|col|i18n|nocase|label|hint|day|date|amt|v2|ok)$/;
const fieldLabel = el => {
  let l = '';
  try { if (el.labels && el.labels.length) l = norm(el.labels[0].innerText); } catch (e) {}
  if (!l) l = norm(el.getAttribute('aria-label') || '');
  if (!l) { const f = el.closest('.f, .field, label, .fld, td, .row'); const lb = f && f.querySelector('label, .lbl, .k');
    if (lb && lb !== el && !lb.contains(el)) l = norm(lb.innerText); else if (f && f.tagName === 'LABEL') l = norm(f.innerText); }
  if (!l) l = norm(el.getAttribute('placeholder') || el.getAttribute('title') || '');
  if (!l) { const td = el.closest('td'), tb = td && td.closest('table'); const th = tb && tb.querySelectorAll('thead th, tr:first-child th')[td.cellIndex]; if (th) l = norm(th.innerText); }
  if (!l) { const row = el.parentElement; const sib = row && [...row.querySelectorAll('input, select, textarea')]; if (sib && sib.length > 1) l = '#' + (sib.indexOf(el) + 1) + ' in its row'; }
  if (!l) l = norm(el.name || el.id || '');
  return l.slice(0, 60);
};
const ctlLabel = el => {
  let l = norm(el.innerText || el.value || '');
  if (!l) l = norm(el.getAttribute('aria-label') || el.getAttribute('title') || '');
  if (!l) { const ds = Object.entries(el.dataset || {}).filter(([k]) => k !== 'simn')[0]; l = ds ? `(${ds[0]}${ds[1] ? ' ' + String(ds[1]).slice(0, 24) : ''})` : '(icon)'; }
  return l;
};
const kindOf = el => { const tg = el.tagName, ty = (el.type || '').toLowerCase(), r = el.getAttribute('role') || '';
  if (tg === 'SELECT') return 'select';
  if (tg === 'TEXTAREA' || el.isContentEditable) return 'text';
  if (tg === 'INPUT') { if (ty === 'checkbox' || ty === 'radio') return 'check'; if (ty === 'file') return 'file';
    if (/^(button|submit|reset|image)$/.test(ty)) return 'button'; return ty === 'date' ? 'date' : 'input'; }
  if (r === 'checkbox' || r === 'switch') return 'check';
  if (r === 'tab') return 'tab';
  if (tg === 'A') return 'link';
  return 'button'; };
const fieldMarker = (n, el, k) => {
  const lab = fieldLabel(el);
  if (k === 'select') { const opts = [...el.options].map(o => norm(o.text)).filter(Boolean); const cur = el.selectedIndex >= 0 ? norm(el.options[el.selectedIndex].text) : '';
    return `[${n} select "${lab}" ="${cur}" {${opts.slice(0, 14).join('|')}${opts.length > 14 ? `|+${opts.length - 14} more` : ''}}]`; }
  if (k === 'check') { const on = el.tagName === 'INPUT' ? el.checked : el.getAttribute('aria-checked') === 'true';
    let l = lab; if (!l) { const p = el.closest('label') || el.parentElement; l = norm(p && p.innerText).slice(0, 60); }
    return `[${n} check "${l}" ${on ? 'on' : 'off'}]`; }
  if (k === 'file') return `[${n} file "${lab}"]`;
  const v = el.isContentEditable ? norm(el.innerText) : String(el.value || '');
  return `[${n} ${k} "${lab}"${v ? ` ="${v.slice(0, 80)}${v.length > 80 ? '…' : ''}"` : ''}]`;
};
let reg;
const walk = (node, out) => {
  if (node.nodeType === 3) { const t = node.nodeValue.replace(/\s+/g, ' '); if (t.trim()) out.push(t); return; }
  if (node.nodeType !== 1) return;
  const el = node, tg = el.tagName;
  if (tg === 'SCRIPT' || tg === 'STYLE' || tg === 'NOSCRIPT' || tg === 'TEMPLATE' || tg === 'svg' || tg === 'SVG') return;
  const cs = getComputedStyle(el);
  if (cs.display === 'none') return;
  if (cs.display !== 'contents' && !el.getClientRects().length && tg !== 'OPTION') return;
  const hidden = cs.visibility === 'hidden' || +cs.opacity === 0;
  const block = BLOCKS.test(cs.display) || tg === 'BR' || tg === 'TR';
  if (block) out.push('\n');
  if (!hidden && isCtl(el)) {
    const k = kindOf(el), n = reg(el, k);
    if (k !== 'button' && k !== 'link' && k !== 'tab') out.push(' ' + fieldMarker(n, el, k) + ' ');
    else { const lab = ctlLabel(el);
      const inner = el.querySelector('button, a[href], input, select, textarea, [role=button], [role=tab]');
      if (inner || lab.length > 70) { out.push(` [${n}${k === 'tab' ? ' tab' : ''}] `); for (const c of el.childNodes) walk(c, out); }
      else out.push(` [${n}${k === 'tab' ? ' tab' : k === 'link' ? ' link' : ''} ${lab}] `);
      if (tg === 'TD' || tg === 'TH') out.push(' | ');
      if (block) out.push('\n');
      return; }
  } else for (const c of el.childNodes) walk(c, out);
  if (tg === 'TD' || tg === 'TH') out.push(' | ');
  if (block) out.push('\n'); else if (cs.display !== 'inline') out.push(' ');
};
const tidy = parts => {
  const lines = parts.join('').split('\n').map(l => l.replace(/[ \t]+/g, ' ').replace(/( \| )+$/, '').trim()).filter(l => l && l !== '|');
  const out = []; for (const l of lines) {
    const prev = out[out.length - 1];
    if (prev === l) continue;
    if (prev && /^\[\d+( tab)?\]$/.test(prev)) { out[out.length - 1] = prev + ' ' + l; continue; }
    out.push(l); }
  return out;
};
const MENU_SEL = '#nav-groups button, #nav-groups a, #nav button[data-v], #tabbar button';
S.menu = () => {
  const items = [...document.querySelectorAll(MENU_SEL)]
    .filter(el => vis(el) && !el.closest('section.view')).map(el => norm(el.innerText || el.getAttribute('aria-label') || el.title || '')).filter(Boolean);
  return [...new Set(items)];
};
S.title = () => { const r = S.viewRoot(); const h = r.querySelector('h1, h2, .ph h2, .f-hero b'); return norm(h ? h.innerText : (r.id || '')).slice(0, 80); };
S.screen = () => {
  S.ctl = []; S.sig = [];
  document.querySelectorAll('[data-simn]').forEach(e => e.removeAttribute('data-simn'));
  reg = (el, k) => { const n = S.ctl.length + 1; S.ctl.push(el); el.setAttribute('data-simn', String(n));
    const lab = k === 'button' || k === 'link' || k === 'tab' ? ctlLabel(el) : fieldLabel(el);
    const filled = k === 'select' ? el.selectedIndex > 0 || (el.selectedIndex === 0 && !/^(—|-|choose|select|pick)/i.test(norm((el.options[0] || {}).text))) :
      k === 'check' ? !!el.checked : (k === 'input' || k === 'text' || k === 'date') ? !!String(el.value || (el.isContentEditable ? el.innerText : '')).trim() : null;
    S.sig.push({ k, label: lab.slice(0, 80), tag: el.tagName, filled }); return n; };
  const ov = S.overlays(), out = [];
  const t = document.getElementById('toast');
  const toastOn = t && t.classList.contains('on') && vis(t);
  // a file field is usually hidden behind a "Choose File" area: a person can still tap it, so it gets a number
  const files = root => [...root.querySelectorAll('input[type=file]')].filter(f => !f.hasAttribute('data-simn') && !f.disabled)
    .map(f => { const n = reg(f, 'file'); const lab = fieldLabel(f) || norm((f.closest('label, .f, .drop, div') || {}).innerText || '').slice(0, 50) || (f.accept || 'a file');
      return `[${n} file "${lab}"${f.accept ? ' (' + f.accept + ')' : ''}${f.multiple ? ' multiple' : ''}]`; });
  if (ov.length) {
    ov.forEach(o => { const p = ['\n']; walk(o, p); out.push('== Open on top ==', ...tidy(p), ...files(o)); });
    out.push(`== Behind it: ${S.title()} (close the sheet to use it) ==`);
  } else { const p = [];
    ['#subnav', '#mtabs'].map(q => document.querySelector(q)).filter(e => e && vis(e) && !e.closest('section.view')).forEach(e => { walk(e, p); p.push('\n'); });
    walk(S.viewRoot(), p); out.push(...tidy(p), ...files(S.viewRoot())); }
  if (toastOn) { const p = []; walk(t, p); out.push('== Toast ==', ...tidy(p)); }
  S.lastScreen = out.join('\n');
  return { title: S.title(), menu: S.menu(), lines: out, n: S.ctl.length, sig: S.sig, overlay: ov.length > 0, view: typeof view !== 'undefined' ? view : '' };
};
S.visibleText = () => { const parts = [S.viewRoot(), ...S.overlays(), document.getElementById('toast')].filter(Boolean).map(e => norm(e.innerText)); return parts.join(' \n '); };
// a number from the last screen back to its element; if the screen re-rendered, find the same control again
S.resolve = n => {
  const i = n - 1, el = S.ctl[i], sg = S.sig[i];
  if (!sg) return { ok: false, why: `there is no control ${n} on your last screen` };
  if (el && el.isConnected && (vis(el) || sg.k === 'file')) { el.setAttribute('data-simn', String(n)); return { ok: true, sig: sg }; }
  const same = sg.k === 'file' ? [...(S.overlays()[0] || S.viewRoot()).querySelectorAll('input[type=file]')]
    : [...document.querySelectorAll(sg.tag)].filter(x => vis(x) && ((sg.k === 'button' || sg.k === 'link' || sg.k === 'tab') ? ctlLabel(x) : fieldLabel(x)).slice(0, 80) === sg.label);
  if (same.length === 1) { S.ctl[i] = same[0]; same[0].setAttribute('data-simn', String(n)); return { ok: true, sig: sg, relocated: true }; }
  return { ok: false, why: `control ${n} ("${sg.label}") is no longer on the screen; run screen again`, sig: sg };
};
// the form on screen when a person saves: how many fields, how many with a value (typed or defaulted)
S.formStats = () => { const F = S.sig.filter(x => x.filled !== null && x.filled !== undefined); return { fields: F.length, filled: F.filter(x => x.filled).length }; };
S.fieldInfo = n => { const el = S.ctl[n - 1]; if (!el) return null; return { kind: kindOf(el), tag: el.tagName, label: S.sig[n - 1].label,
  options: el.tagName === 'SELECT' ? [...el.options].map(o => ({ v: o.value, t: norm(o.text) })) : null }; };
S.pick = (n, opt) => { const el = S.ctl[n - 1]; if (!el || el.tagName !== 'SELECT') return { ok: false, why: 'not a select' };
  const want = norm(opt).toLowerCase(), O = [...el.options];
  const o = O.find(x => norm(x.text).toLowerCase() === want) || O.find(x => norm(x.text).toLowerCase().startsWith(want)) || O.find(x => norm(x.text).toLowerCase().includes(want)) || O.find(x => String(x.value).toLowerCase() === want);
  if (!o) return { ok: false, why: `no option "${opt}"; the options are: ${O.map(x => norm(x.text)).filter(Boolean).slice(0, 30).join(' | ')}` };
  return { ok: true, value: o.value, text: norm(o.text) }; };
S.fileInputNear = n => { const el = S.ctl[n - 1]; if (!el) return false;
  if (el.tagName === 'INPUT' && el.type === 'file') { el.setAttribute('data-simfile', '1'); return true; }
  document.querySelectorAll('[data-simfile]').forEach(x => x.removeAttribute('data-simfile'));
  const scope = el.closest('#mbm, .mbm, #drawer, section.view, form, .card') || document.body;
  const f = el.querySelector('input[type=file]') || (el.htmlFor && document.getElementById(el.htmlFor)) || scope.querySelector('input[type=file]');
  if (!f) return false; f.setAttribute('data-simfile', '1'); return true; };
// navigation by the label a person sees in their menu (the rail on a desktop, the tab bar and More on a phone)
S.navCandidates = () => [...document.querySelectorAll(MENU_SEL + ', #subnav button, #mtabs button, .m-sheet-list button, .m-sheet-list a, .more-sheet button')]
  .filter(el => !el.closest('section.view'));
S.go = label => {
  const want = norm(label).toLowerCase().replace(/\s+\d+$/, '');
  const C = S.navCandidates().map(el => ({ el, t: norm(el.innerText || el.getAttribute('aria-label') || el.title || '').toLowerCase().replace(/\s+\d+$/, ''), v: vis(el) }));
  const hit = C.find(c => c.v && c.t === want) || C.find(c => c.t === want) || C.find(c => c.v && c.t.startsWith(want)) || C.find(c => c.t.startsWith(want)) || C.find(c => c.v && c.t.includes(want));
  if (!hit) return { ok: false, why: `no "${label}" in your menu; it has: ${S.menu().join(' · ')}` };
  hit.el.click(); return { ok: true, label: hit.t };
};
S.closeTop = () => { const ov = S.overlays(); if (!ov.length) return false; const o = ov[ov.length - 1];
  const b = [...o.querySelectorAll('button, a')].filter(vis).find(x => /^(cancel|close|done|back|not now|×|x)$/i.test(norm(x.innerText || x.getAttribute('aria-label') || '')));
  if (b) { b.click(); return 'closed with ' + norm(b.innerText || b.getAttribute('aria-label')); }
  try { if (o.id === 'mbm' || o.classList.contains('mbm')) { mbCloseModal(); return 'closed'; } } catch (e) {}
  try { if (o.id === 'drawer') { closeEditor(); return 'closed'; } } catch (e) {}
  o.classList.remove('on'); return 'closed'; };
// what the person has open, so a reload brings them back to it
S.where = () => ({ view: typeof view !== 'undefined' ? view : '', project: (typeof S_ !== 'undefined' ? '' : ''), cur: (DB && DB.currentId) || '', y: Math.round(scrollY) });

// ------------------------------------------------------------------ records, for the find-it-again check
const NOISE = /(^|\.)(audit|log|logs$|activity|history|touch|seen|notif|toasts|ticks|bnTicks|events|paLog|undo|snap|cache|memo|views|reads|tracks|checks|sweeps|runs|stamps|briefCache|chases|digest)/i;
S.keys = () => { const out = {}; const add = (k, arr) => { if (!Array.isArray(arr) || NOISE.test(k)) return;
    arr.forEach((r, i) => { if (r && typeof r === 'object' && (r.id || r.number)) out[k + ':' + (r.id || r.number)] = 1; }); };
  for (const [k, v] of Object.entries(DB)) {
    if (Array.isArray(v)) add(k, v);
    else if (v && typeof v === 'object' && k !== 'demoWs' && k !== 'company') for (const [k2, v2] of Object.entries(v)) if (Array.isArray(v2)) add(k + '.' + k2, v2);
    if (k === 'projects') v.forEach(p => { for (const [pk, pv] of Object.entries(p)) if (Array.isArray(pv)) add('p.' + pk, pv); });
    if (k === 'clients') v.forEach(c => { for (const ck of ['estimates', 'invoices', 'changeOrders', 'payments', 'creditMemos']) add('c.' + ck, c[ck]); });
  }
  return out; };
S.recordName = key => { const [coll, id] = [key.slice(0, key.lastIndexOf(':')), key.slice(key.lastIndexOf(':') + 1)];
  const find = arr => (arr || []).find(r => r && (r.id === id || r.number === id));
  let r = null; const parts = coll.split('.');
  if (parts[0] === 'p') for (const p of DB.projects) { r = find(p[parts[1]]); if (r) break; }
  else if (parts[0] === 'c') for (const c of DB.clients) { r = find(c[parts[1]]); if (r) break; }
  else if (parts.length === 2) r = find((DB[parts[0]] || {})[parts[1]]);
  else r = find(DB[coll]);
  if (!r) return { coll, id, name: '' };
  const name = r.number || r.title || r.name || r.what || r.subject || r.fileName || r.filename || r.desc || r.item || r.label || r.text || r.memo || '';
  return { coll, id, name: norm(name).slice(0, 80) };
};
S.onScreen = name => { const n = norm(name).toLowerCase(); if (!n) return { on: false, toast: false };
  const view = norm([S.viewRoot(), ...S.overlays()].map(e => e.innerText).join(' ')).toLowerCase();
  const t = document.getElementById('toast'); const toast = !!(t && t.classList.contains('on') && norm(t.innerText).toLowerCase().includes(n.slice(0, 40)));
  return { on: view.includes(n.slice(0, 40)), toast }; };

// ------------------------------------------------------------------ the mailbox (Gmail on the person's phone)
const hdr = (m, k) => (m.headers || {})[k] || '';
const labelsOf = (uid, m) => { const A = (DB.demoWs || {})[uid] || {}; return ((A.labels || {})[m.id] || m.labelIds || []); };
S.hasMailbox = uid => { try { return !!(typeof DW_STAFF !== 'undefined' && DW_STAFF[uid] && DB.conn[uid] && (DB.conn[uid].google || {}).demo); } catch (e) { return false; } };
S.mbAddr = uid => { try { return dwAddr(uid); } catch (e) { return ''; } };
S.mbList = (uid, box) => { const W = demoWsFor(uid);
  return W.messages.filter(m => { const L = labelsOf(uid, m); if (box === 'drafts') return L.includes('DRAFT'); if (L.includes('DRAFT')) return false; return box === 'sent' ? L.includes('SENT') : !L.includes('SENT'); })
    .sort((a, b) => b.internalDate - a.internalDate)
    .map(m => ({ id: m.id, from: hdr(m, 'From'), to: hdr(m, 'To'), subject: hdr(m, 'Subject'), at: m.internalDate, unread: labelsOf(uid, m).includes('UNREAD'),
      snippet: norm(m.body).slice(0, 90), att: (m.attachments || []).map(a => a.filename), thread: m.threadId })); };
S.mbRead = (uid, id) => { const W = demoWsFor(uid), m = W.messages.find(x => x.id === id); if (!m) return null;
  const L = labelsOf(uid, m).filter(x => x !== 'UNREAD'); m.labelIds = L; dwAdded(uid).labels[m.id] = L; save();
  return { id: m.id, from: hdr(m, 'From'), to: hdr(m, 'To'), cc: hdr(m, 'Cc'), subject: hdr(m, 'Subject'), at: m.internalDate, body: m.body, thread: m.threadId,
    att: (m.attachments || []).map(a => ({ filename: a.filename, mime: a.mime, text: a.text || '' })) }; };
// send a draft the way Gmail's Send does (the app's own Save to Mailbox Drafts puts it there)
S.mbSendDraft = (uid, id) => { const W = demoWsFor(uid), A = dwAdded(uid), m = W.messages.find(x => x.id === id); if (!m) return null;
  m.labelIds = ['SENT']; m.internalDate = appNowMs(); A.labels[m.id] = m.labelIds;
  W.drafts = (W.drafts || []).filter(d => d.message.id !== id); A.drafts = (A.drafts || []).filter(d => d.message.id !== id); save();
  return { id: m.id, to: hdr(m, 'To'), subject: hdr(m, 'Subject') }; };
// put a message in a staff mailbox (the world's mail, a colleague's mail); kept in DB.demoWs so it outlives a reload
S.mbPut = (uid, msg) => { const A = dwAdded(uid); if (A.messages.some(m => m.id === msg.id)) return false;
  const W = DEMO_WS[uid] || DW_ATTACHED[uid]; msg.historyId = W ? ++W.historyId : 900 + A.messages.length;
  A.messages.push(msg); if (W && !W.messages.some(m => m.id === msg.id)) W.messages.push(msg); save(); return true; };
S.mbEvent = (uid, ev) => { const A = dwAdded(uid); if (A.events.some(e => e.id === ev.id)) return false;
  const W = DEMO_WS[uid]; A.events.push(ev); if (W && !W.events.some(e => e.id === ev.id)) W.events.push(ev); save(); return true; };
// every message any staff mailbox has sent (by a person through the toolkit, or by the app's own Send)
S.mbSentAll = () => { const out = [];
  Object.entries(DB.demoWs || {}).forEach(([uid, A]) => (A.messages || []).forEach(m => { const L = (A.labels || {})[m.id] || m.labelIds || [];
    if (L.includes('SENT')) out.push({ uid, id: m.id, from: hdr(m, 'From'), to: hdr(m, 'To'), cc: hdr(m, 'Cc'), subject: hdr(m, 'Subject'), body: m.body, at: m.internalDate, thread: m.threadId,
      att: (m.attachments || []).map(a => ({ filename: a.filename, text: a.text || '' })) }); }));
  (DB.outbox || []).forEach(o => { if (/sent|delivered/.test(String(o.status || '')) && o.id) out.push({ uid: o.byUid || o.by || '', id: 'outbox_' + o.id, from: o.from || '', to: [].concat(o.to || []).join(', '),
    cc: '', subject: o.subject || '', body: o.body || o.text || '', at: Date.parse(o.at || '') || 0, thread: o.threadId || '', outbox: true, att: [] }); });
  return out; };
// Drive: the world holds each person's drive; after a reload its files are put back where the app reads them
S.driveSync = files => { let n = 0; (files || []).forEach(f => { try { if (!S.hasMailbox(f.uid)) return; const W = demoWsFor(f.uid);
  if (!W.files.some(x => x.id === f.file.id)) { W.files.push(f.file); n++; } } catch (e) {} }); return n; };
return 'ok';
}
