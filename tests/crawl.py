"""The click crawler: does every click perform the correct act and take you to the correct page?

For each user (harness.USERS plus u_cambri, the second client) x each view in ROLE_VIEWS[role] x desktop
1440x900 and phone 390x844, it lists every visible, enabled clickable on the screen (buttons, links, tabs,
the rail and tab bars, tiles, chips, row actions, cards, anything a person can see is clickable: a pointer
cursor or a data-* action attribute), dedupes them by a stable key (view + accessible label + action
attributes), samples repeated rows (at most --per-family alike controls per view) and caps each view
(--max-per-view, 60), reporting what it skipped.

Each control is pressed from a FRESH known state. A view's state is snapshotted once: the DB as JSON, the
current job, the view, the scroll, the overlays the shell holds, the app's own UI state (every top-level
let/const and window property that can be cloned, named by the debugger's Runtime.globalLexicalScopeNames:
filters, tabs, open rows, a tile's focus) and localStorage / sessionStorage. Before each press the page is
put back in place, in memory: DB is replaced the way the app's own Import does it (DB = parsed copy,
setCurrent, render()). When the previous press changed nothing in DB and left the page itself alone, only
the overlays it opened are closed (render costs about 0.3 s, so it runs only when needed). The visible
state is then compared with the snapshot; if it drifted the page is reloaded and the view replayed. Saving
is switched off for the crawl, so nothing reaches IndexedDB and no press leaks into the next. Transitions
and animations are off, Math.random is seeded (the seed's ids are the same every boot), window.open,
print and links that would leave the page are recorded instead of followed.

Every flag is then pressed again from a freshly booted page (the view opened straight after sign-in, the
control pressed once). A flag that does not come back was made by the crawl's own sequence, not by a press
from a fresh state: it is listed under Info as "not reproduced from a fresh boot" and does not count.

After each press (settled when the DOM is quiet for 150 ms, at most 1.5 s; native dialogs are recorded and
dismissed) it records: page and console errors; the destination (view, heading, the drawer / modal / sheet
that opened and its title, the scroll); the DB diff (collections and ids added, changed, removed); toasts,
their Open links and where the first link goes (it is pressed); and whether anything visible changed.

Rules (each flag: RULE | viewport | user | view | control label | detail):
  ERROR        a page or console error
  NOOP         nothing visible changed: no navigation, overlay, dialog, DB change, toast, scroll or download
  DEADEND      landed on a view the role may not open, a blank page, or fell through to Ask; or a toast's
               Open link that goes nowhere
  MISMATCH     the label promises a destination and the destination disagrees: "Open X" / "View X" / a record
               number opens another record or only the list; a rail entry, sub-tab or tab lands on a page whose
               heading is not its label (lint's heading-vs-nav rule); a tile lands on a page that does not name
               it; a verb (Approve, Send, Record Payment, Order, Chase, Draft ...) opens nothing related
  SILENT       DB changed but no toast, or the toast has no Open link (a settings save with no record: INFO)
  LEAK         a client sees another client's job, people or money; a foreman, crew or driver sees money
  DESTRUCTIVE  a Delete / Void / Reject / Remove reached the mutation with no confirmation step

Output: review/crawl/flags.json, review/crawl/report.md (per role: controls pressed, flags by rule, the
worst 30 with screenshots in review/crawl/shots/) and the last line
`CRAWL N flags (clicked X controls over Y screens)`. Exit 1 if N > 0.

  python3 crawl.py [--user u_owner,u_alan] [--view home,inv] [--phone|--desktop] [--rule NOOP,SILENT]
                   [--max-per-view 60] [--per-family 3] [--json path] [--quiet] [--no-confirm]

A full run takes three to five hours on this build (about 11,000 presses over 646 screens), so it is an optional suite in tests/run_all.sh
(tests/run_all.sh crawl), like month_sim; filter by --user / --view / --phone / --desktop while fixing.
"""
import asyncio, json, os, re, sys, time, argparse
from collections import Counter, defaultdict
from harness import *

OUT = os.path.join(ROOT, 'review', 'crawl')
SHOTS = os.path.join(OUT, 'shots')
CRAWL_USERS = USERS + ['u_cambri']
FIELD_ROLES = {'foreman', 'crew', 'driver'}
SEVERITY = ['ERROR', 'LEAK', 'DESTRUCTIVE', 'DEADEND', 'SILENT', 'MISMATCH', 'NOOP']

# ---------------------------------------------------------------------------------------------- allowlist
# Demonstrable false positives only, each with the reason. (rule, label regex, view regex or None, why)
ALLOW = [
]

# DB keys a press may write without being a mutation of a record: the current job, the person's own UI
# state and the read log. A change confined to these is not a mutation (no toast owed).
UI_KEYS = {'currentId', 'workspace'}
# Paths inside DB that hold a person's view preferences, not records: the dashboard preset each user last
# chose (dashboards.u:<uid>:<preset>).
UI_PATHS = [
    r'^dashboards\.u:',
    # the person's own conversation with the assistant (an Ask chip's question and answer are the visible result)
    r'^asst\.[^.\[]+\.(thread|ctx|last|seen|asked)',
    # a document's unsaved-changes snapshot, written when its editor opens (DOC_EDIT_KEYS / docSnap)
    r'\._base$',
    # the sales pipeline the Numbers page is showing
    r'^hub\.pipeline(Id)?\b',
    # a daily log draft as the foreman fills it in, step by step (Submit is the mutation, and it toasts), and
    # a request's text prefilled into the composer by Need Something (Send is the mutation)
    r'^field\.(dlDraft|draft)\b',
]

# ---------------------------------------------------------------------------------------------- page side
# Installed before the app's own scripts: a seeded Math.random (the seed's ids are the same every boot, so
# keys are stable), and window.open / print stand-ins that record instead of leaving the page.
INIT_JS = r"""
(() => {
  let s = 0x2f6b9a1d;
  Math.random = () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  window.__crRec = {opens: [], prints: 0, ext: [], stacks: []};
  // where a logged error came from: the first frames of any Error handed to console.error
  const ce = console.error.bind(console);
  console.error = (...a) => { try { a.forEach(x => x && x.stack && window.__crRec.stacks.push(String(x.stack).split('\n').slice(1, 4).map(l => l.trim().replace(/\(file:[^)]*:(\d+):\d+\)/, 'line $1')).join(' < '))); } catch (e) {} return ce(...a); };
  window.addEventListener('error', e => { try { e.error && e.error.stack && window.__crRec.stacks.push(String(e.error.stack).split('\n').slice(1, 4).map(l => l.trim().replace(/\(file:[^)]*:(\d+):\d+\)/, 'line $1')).join(' < ')); } catch (x) {} });
  const stub = new Proxy(function () {}, { get: (t, k) => k === Symbol.toPrimitive ? (() => '') : (k === 'then' ? undefined : stub), apply: () => stub, set: () => true });
  window.open = (u) => { window.__crRec.opens.push(String(u || '').slice(0, 120)); return stub; };
  window.print = () => { window.__crRec.prints++; };
  // a link that would leave the page (mailto:, tel:, http, a download) is recorded and kept on the page
  window.addEventListener('click', (e) => {
    const a = e.target && e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    const h = a.getAttribute('href') || '';
    if (!h || h[0] === '#' || /^javascript:/i.test(h)) return;
    window.__crRec.ext.push((a.hasAttribute('download') ? 'download ' : '') + h.slice(0, 120));
    e.preventDefault();
  }, true);
})();
"""

PAGE_JS = r"""
() => {
  if (window.__cr) return 'again';
  const C = window.__cr = {toasts: [], links: [], lastMut: Date.now()};
  // no transitions or animations: a control is pressed where it is, not where a sliding rail will put it
  const st = document.createElement('style'); st.id = 'cr-still';
  st.textContent = '*, *::before, *::after { transition: none !important; animation: none !important; scroll-behavior: auto !important; }';
  document.head.appendChild(st);
  const R = window.__crRec;
  // Saving is off for the crawl: the in-memory DB is the only state, restored before every press. The
  // save-sequence bookkeeping is kept in step so "Saved" toasts are not held back waiting for a write.
  persist = function () { try { trSavedSeq = trSaveSeq; } catch (e) {} try { saveState.ok = true; } catch (e) {} return Promise.resolve(true); };
  const norm = s => String(s || '').replace(/\s+/g, ' ').trim();
  C.norm = norm;
  const toastEl = document.getElementById('toast');
  new MutationObserver(() => {
    const t = toastEl; if (!t || !t.classList.contains('on')) return;
    const as = [...t.querySelectorAll('a, button')];
    const txt = norm(t.innerText || t.textContent); if (!txt) return;
    const links = as.map(a => norm(a.innerText || a.textContent)).filter(Boolean);
    as.forEach(a => { if (!C.links.includes(a)) C.links.push(a); });
    const last = C.toasts[C.toasts.length - 1];
    if (last && last.text === txt) { last.links = [...new Set(last.links.concat(links))]; return; }
    C.toasts.push({text: txt.slice(0, 200), links});
  }).observe(toastEl, {childList: true, subtree: true, characterData: true, attributes: true});
  new MutationObserver(muts => {
    for (const m of muts) { const t = m.target; if (t && t.closest && t.closest('#toast')) continue; if (t && t.parentElement && t.parentElement.closest && t.parentElement.closest('#toast')) continue; C.lastMut = Date.now(); return; }
  }).observe(document.body, {childList: true, subtree: true, characterData: true, attributes: true});
  document.addEventListener('scroll', () => { C.scrollAt = Date.now(); }, true);
  C.quiet = (q, max) => new Promise(res => { const t0 = Date.now(); const tick = () => { const now = Date.now(); if (now - C.lastMut >= q || now - t0 >= max) return res(now - t0); setTimeout(tick, 25); }; setTimeout(tick, 40); });

  const cs = e => getComputedStyle(e);
  const vis = el => {
    if (!el || !el.getBoundingClientRect) return false;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const s = cs(el);
    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0) return false;
    if (el.closest('[aria-hidden="true"]')) return false;
    const det = el.closest('details:not([open])'); if (det && !el.closest('summary')) return false;
    // parked off screen (a closed drawer)
    for (let x = el; x && x !== document.body; x = x.parentElement) { const p = cs(x).position; if (p === 'fixed') { const q = x.getBoundingClientRect(); if (q.left >= innerWidth - 1 || q.right <= 1 || q.top >= innerHeight - 1) return false; break; } }
    return true;
  };
  C.vis = vis;
  const V = () => document.querySelector('.view.on');
  const OV_SEL = '#mbm, .mbm, .drawer, .viewer, .pal, .sheet, [class*="sheet"], .modal, [role="dialog"], .overlay, .popover, .menu, [class*="-pop"], [class*="menu"]';
  const BAR = '#toast, .toast, nav, .rail, .topbar, .tabbar, #tabbar, #mtabs, #fab, .scrim, .railscrim, #scrim, #railscrim, .shell';
  // An overlay: a fixed or absolute layer that is not part of the shell's bars, covering a real share of the
  // screen, or a known modal/drawer/sheet class.
  const overlays = () => {
    const out = [];
    // layers live outside the shell (body children and what they hold), plus the shell's own drawers
    const pool = [...document.querySelectorAll('.shell #mbm, .shell .mbm, .shell .drawer, .shell .viewer, .shell .pal')];
    for (const k of document.body.children) {
      if (k.matches('.shell, script, style, #toast')) continue;
      pool.push(k); if (cs(k).position !== 'fixed') pool.push(...k.querySelectorAll('*'));
    }
    for (const e of pool) {
      if (e.closest(BAR) && !e.matches('#mbm, .mbm, .drawer, .viewer, .pal')) continue;
      const s = cs(e); if (s.position !== 'fixed' && !(s.position === 'absolute' && +s.zIndex >= 20)) continue;
      if (!vis(e)) continue;
      const r = e.getBoundingClientRect();
      const big = r.width * r.height >= innerWidth * innerHeight * 0.12;
      if (!big && !e.matches(OV_SEL)) continue;
      if (out.some(o => o.contains(e))) continue;
      if (!norm(e.innerText)) continue;
      out.push(e);
    }
    return out;
  };
  const titleOf = o => {
    const d = o.matches('[role=dialog][aria-label]') ? o : o.querySelector('[role=dialog][aria-label]');
    const h = [...o.querySelectorAll('h1, h2, h3, .title, .hd b, .vhd b, .dr-title, .sh-title, b')].find(vis);
    return norm((h && h.innerText) || (d && d.getAttribute('aria-label')) || '').slice(0, 100);
  };
  C.overlays = overlays;

  // the visible-state signature: view, scroll, overlays and a hash of every element's tag, class, style,
  // open/hidden and text (digits dropped for the "stable" one, which judges drift between presses)
  const hash = (h, s) => { for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0; return h; };
  C.sig = () => {
    let a = 0, b = 0;
    // only what can be seen: the view that is on, the shell, open layers (a closed drawer keeps its last
    // contents and an inactive view its last render; neither is on screen)
    const walk = (el) => {
      for (const c of el.children) {
        if (c.tagName === 'SCRIPT' || c.tagName === 'STYLE' || c.id === 'toast') continue;
        if (c.classList.contains('view') && !c.classList.contains('on')) continue;
        if (el === document.body && !vis(c)) continue;
        if (c.hidden || /display:\s*none/.test(c.getAttribute('style') || '')) continue;
        // style read back as the browser serialises it ("margin:0" and "margin: 0px;" are one style)
        const k = c.tagName + (c.getAttribute('class') || '') + (c.style ? c.style.cssText : '') + (c.hidden ? 'H' : '') + (c.open ? 'O' : '') +
          (/^(INPUT|TEXTAREA|SELECT)$/.test(c.tagName) ? '=' + c.value + (c.checked ? 'C' : '') + (c.disabled ? 'D' : '') : '');
        a = hash(a, k); b = hash(b, k);
        for (const n of c.childNodes) if (n.nodeType === 3 && n.data.trim()) { a = hash(a, n.data); b = hash(b, n.data.replace(/\d+/g, '#')); }
        walk(c);
      }
    };
    a = hash(a, document.body.className + '|' + document.documentElement.className); b = hash(b, document.body.className + '|' + document.documentElement.className);
    const vOn = V();
    let va = 0;
    if (vOn) { const save = a; a = 0; walk(vOn); va = a; a = save; }
    walk(document.body);
    const m = document.querySelector('.main');
    const sy = Math.round(Math.max(scrollY, document.documentElement.scrollTop, document.body.scrollTop, m ? m.scrollTop : 0));
    return {full: a + ':' + sy, stable: b, sy, view: va};
  };

  // ---- the clickables
  const SEL = 'button, a, [role=button], [role=tab], [role=link], [role=menuitem], [role=option], [onclick], [data-v], [data-mv], [data-sub], [data-grp], .gl, .chip, summary';
  const kindOf = e => {
    if (e.closest('#ws')) return 'ws';
    if (e.closest('#nav-groups, #nav, .rail')) return 'rail';
    if (e.closest('#mtabs, #tabbar')) return 'mtab';
    if (e.closest('#subnav')) return 'subtab';
    if (e.matches('[role=tab]') || (e.parentElement && e.parentElement.matches('.ctabs, .seg, .tabs, .sub-tabs, [role=tablist], .hb-tabs, .hb-subtabs, .rep-groups, .rep-sub'))) return 'tab';
    if (e.matches('.gl, .kpi, .dx-tile, .tile, .ov-tiles > *, .dtiles > *, .fd-tiles > *')) return 'tile';
    if (e.matches('.chip, [class*="chip"]') || (e.parentElement && e.parentElement.matches('[class*="chips"]'))) return 'chip';
    if (e.closest('.topbar, #crumbs, .td-hdr, [class*="hdr"]') && !V()?.contains(e)) return 'top';
    if (e.tagName === 'A') return 'link';
    if (e.tagName === 'SUMMARY') return 'summary';
    if (e.matches('button, [role=button], .btn')) return 'button';
    return 'card';
  };
  const labelOf = e => {
    const own = norm(e.innerText || e.textContent);
    const t = own || norm(e.getAttribute('aria-label')) || norm(e.getAttribute('title')) || norm(e.getAttribute('alt')) || norm(e.value);
    return t.slice(0, 80);
  };
  const actOf = e => {
    const out = [];
    for (const at of e.attributes) {
      const n = at.name;
      if (n.startsWith('data-cr') || n.startsWith('data-dw') || n === 'data-tip') continue;
      if (n.startsWith('data-') || n === 'onclick' || n === 'href') out.push(n + '=' + String(at.value).slice(0, 40));
    }
    return out.sort().join(' ');
  };
  const disabledLooking = e => e.disabled || e.getAttribute('aria-disabled') === 'true' || e.matches('.disabled, .dis, [disabled]') || cs(e).pointerEvents === 'none' || +cs(e).opacity < 0.45;
  const rowOf = e => e.closest('tr, li, .row, [class*="row"], .card, [class*="card"], .item, [class*="item"]');
  C.list = () => {
    const v = V();
    const ovs = overlays();
    const roots = [document.body];
    const cand = new Set();
    for (const e of document.querySelectorAll(SEL)) cand.add(e);
    // anything a person reads as clickable: a pointer cursor that is not inherited from a clickable parent
    const scanRoots = [v, ...ovs, ...document.querySelectorAll('#nav-groups, #subnav, .topbar, #mtabs, #tabbar, #ws')].filter(Boolean);
    for (const e of scanRoots.flatMap(rt => [...rt.querySelectorAll('div, span, li, tr, td, article, section, b, strong, img, svg, label, p, h3, h4, i, em')])) {
      if (e.closest('svg') && e.tagName !== 'svg') continue;
      const s = cs(e); if (s.cursor !== 'pointer') continue;
      const p = e.parentElement; if (p && cs(p).cursor === 'pointer') continue;
      cand.add(e);
    }
    const out = [], seen = Object.create(null), disabled = [];
    C.byKey = new Map();
    let i = 0;
    for (const e of cand) {
      if (e.closest('#toast, script, style, select, option, #signin:not(.on)')) continue;
      if (e.matches('input, select, textarea, option, label') && !e.matches('[role=button], [role=tab]')) continue;
      if (e.tagName === 'LABEL' || e.querySelector(':scope > input[type=checkbox], :scope > input[type=radio]')) continue;
      // a panel that carries data-v to name itself (the property screen's sections) is not a control
      if (e.matches('section, article, form') && cs(e).cursor !== 'pointer') continue;
      if (e.tagName === 'svg' && e.closest('button, a, [role=button]')) continue;
      if (!vis(e)) continue;
      // a figure drawn as a tile with no pointer (.gl.static) is a reading, not a control
      if (e.matches('.gl, .kpi') && cs(e).cursor !== 'pointer') continue;
      const label = labelOf(e);
      if (!label) continue;
      const inOv = ovs.find(o => o.contains(e));
      const chrome = !inOv && !(v && v.contains(e));
      const scope = inOv ? 'overlay' : chrome ? 'chrome' : 'view';
      const kind = kindOf(e);
      // a tile's caption is what it promises; its value and sub-line are data
      const cap = kind === 'tile' ? e.querySelector('.gl-k, :scope > span, .k, .lbl') : null;
      const promise = cap ? norm(cap.innerText || cap.textContent) : '';
      if (disabledLooking(e)) { disabled.push(label.slice(0, 40)); continue; }
      const act = actOf(e);
      const key = scope + '|' + label + '|' + act;
      const n = seen[key] = (seen[key] || 0) + 1;
      const cls = (typeof e.className === 'string' ? e.className : '').trim().split(/\s+/).filter(Boolean).slice(0, 2).join('.');
      const family = scope + '|' + e.tagName + '.' + cls + '|' + label.replace(/\d[\d,.\-\/:]*/g, '#').slice(0, 30) + '|' + [...e.attributes].map(a => a.name).filter(n => n.startsWith('data-')).sort().join(',');
      const row = rowOf(e);
      const rowText = row && row !== e && !row.contains(v) ? norm(row.innerText).slice(0, 240) : '';
      e.setAttribute('data-cr-i', String(i));
      C.byKey.set(key + '#' + n, e);
      const active = e.matches('.on, .active, .sel, .cur, .current, .is-on, .is-active, [aria-selected=true], [aria-current]:not([aria-current=false]), [aria-pressed=true]');
      out.push({i: i++, key, n, family, label, kind, scope, act, tag: e.tagName.toLowerCase(), rowText, active, promise});
    }
    return {cands: out, disabled};
  };
  // nested clickables inside a candidate (a card holding buttons): click the card where none of them sit
  C.point = (key, n) => {
    // the element listed last time, when the page was not drawn again since; else list again
    let e = C.byKey && C.byKey.get(key + '#' + n), c = {key, n};
    if (!(e && e.isConnected && vis(e) && key.endsWith('|' + labelOf(e) + '|' + actOf(e)))) {
      const {cands} = C.list();
      c = cands.find(x => x.key === key && x.n === n);
      if (!c) return {missing: true};
      e = document.querySelector(`[data-cr-i="${c.i}"]`);
    }
    e.scrollIntoView({block: 'center', inline: 'center', behavior: 'instant'});
    const r = e.getBoundingClientRect();
    const inner = [...e.querySelectorAll(SEL)].filter(x => x !== e && vis(x));
    const pts = [[0.5, 0.5], [0.25, 0.5], [0.75, 0.5], [0.5, 0.25], [0.5, 0.75], [0.1, 0.5], [0.9, 0.5], [0.15, 0.2], [0.85, 0.8], [0.15, 0.8], [0.85, 0.2]];
    let blocker = '';
    for (const [fx, fy] of pts) {
      const x = r.left + r.width * fx, y = r.top + r.height * fy;
      if (x < 1 || y < 1 || x > innerWidth - 1 || y > innerHeight - 1) continue;
      const top = document.elementFromPoint(x, y);
      if (!top) continue;
      if (!(e === top || e.contains(top))) { blocker = blocker || (top.tagName.toLowerCase() + (top.id ? '#' + top.id : '') + '.' + String(top.className || '').split(' ')[0] + ' "' + norm(top.innerText).slice(0, 30) + '"'); continue; }
      if (inner.some(x => x === top || x.contains(top))) continue;
      return {x, y, c};
    }
    return {covered: blocker || 'every point of it is another control', c};
  };

  // ---- before / after a press
  C.before = () => {
    C.toasts = []; C.links = []; R.opens = []; R.prints = 0; R.ext = []; R.stacks = [];
    C.pre = {}; for (const k of Object.keys(DB)) C.pre[k] = JSON.stringify(DB[k]);
    C.preView = view; C.preCur = DB.currentId;
    C.preOv = new Set(overlays());
    C.preSig = C.sig();
    C.pressAt = Date.now(); C.scrollAt = 0;
    document.querySelectorAll('.view.on').forEach(x => x.setAttribute('data-cr-was', '1'));
    return true;
  };
  const idOf = x => x && typeof x === 'object' ? (x.id || x.number || x.key || x.uid || null) : null;
  const diff = (a, b, path, out, depth) => {
    if (out.length > 14) return;
    if (Array.isArray(a) && Array.isArray(b)) {
      const ida = a.map(idOf), idb = b.map(idOf);
      if (ida.every(Boolean) && idb.every(Boolean) && (a.length || b.length)) {
        const A = new Map(a.map(x => [idOf(x), x])), B = new Map(b.map(x => [idOf(x), x]));
        for (const [k, x] of B) if (!A.has(k)) out.push({op: 'add', path, id: String(k), label: String(x.number || x.title || x.name || x.what || x.text || '').slice(0, 50)});
        for (const k of A.keys()) if (!B.has(k)) out.push({op: 'del', path, id: String(k)});
        for (const [k, x] of B) if (A.has(k)) { const y = A.get(k); if (JSON.stringify(x) !== JSON.stringify(y)) { if (depth < 3 && x && y && typeof x === 'object') { const before = out.length; diff(y, x, path + '[' + k + ']', out, depth + 1); if (out.length === before) out.push({op: 'chg', path: path + '[' + k + ']'}); } else out.push({op: 'chg', path: path + '[' + k + ']'}); } }
      } else if (JSON.stringify(a) !== JSON.stringify(b)) out.push({op: b.length > a.length ? 'add' : b.length < a.length ? 'del' : 'chg', path, id: b.length + ' items (was ' + a.length + ')'});
      return;
    }
    if (a && b && typeof a === 'object' && typeof b === 'object' && depth < 4) {
      for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
        const x = a[k], y = b[k];
        if (x === y) continue;
        if (typeof x !== 'object' || typeof y !== 'object' || x === null || y === null) { if (JSON.stringify(x) !== JSON.stringify(y)) out.push({op: x === undefined ? 'add' : y === undefined ? 'del' : 'set', path: path + '.' + k, val: String(JSON.stringify(y)).slice(0, 40)}); continue; }
        if (JSON.stringify(x) !== JSON.stringify(y)) diff(x, y, path + '.' + k, out, depth + 1);
      }
      return;
    }
    if (JSON.stringify(a) !== JSON.stringify(b)) out.push({op: 'set', path, val: String(JSON.stringify(b)).slice(0, 40)});
  };
  C.after = (opts) => {
    const v = V();
    const keys = [];
    for (const k of new Set([...Object.keys(C.pre), ...Object.keys(DB)])) { const s = JSON.stringify(DB[k]); if (s !== C.pre[k]) keys.push(k); }
    const changes = [];
    const rawKeys = keys.slice();
    for (const k of keys) { let a; try { a = C.pre[k] === undefined ? undefined : JSON.parse(C.pre[k]); } catch (e) { a = null; } diff(a, DB[k], k, changes, 0); if (!changes.some(c => c.path.split(/[.\[]/)[0] === k)) changes.push({op: 'chg', path: k}); }
    // Not a mutation: a lazy default filled in by a render (an empty list or object) and the sync stamps a
    // render writes (gl.lastSync).
    // A first visit that seeds a screen's demo data flips a __...Seeded flag: all of that is the seed's doing.
    const seeding = keys.some(k => /^__\w*seed/i.test(k));
    const noise = ch => seeding || (ch.op === 'add' && /^("?"?|\[\]|\{\}|null|false|0)$/.test(ch.val || '')) || /\.lastSync$/.test(ch.path);
    const ui = ch => (C.uiPaths || []).some(re => new RegExp(re).test(ch.path));
    const real = changes.filter(ch => !noise(ch) && !ui(ch));
    keys.length = 0; for (const ch of real) { const k = ch.path.split(/[.\[]/)[0]; if (!keys.includes(k)) keys.push(k); }
    const ovs = overlays();
    const fresh = ovs.filter(o => !C.preOv.has(o));
    const ovInfo = fresh.map(o => ({title: titleOf(o), text: norm(o.innerText).slice(0, 3000), cls: String(o.className || o.id || o.tagName).slice(0, 40)}));
    const stillOv = ovs.filter(o => C.preOv.has(o)).map(o => ({title: titleOf(o), text: norm(o.innerText).slice(0, 3000)}));
    // the heading and the active nav entry, as lint reads them
    const tabOn = document.querySelector('#subnav .sub-tabs button.on, #subnav .sub-tabs .on');
    const grpOn = document.querySelector('#nav-groups button.on') || [...document.querySelectorAll('#nav-mb button.on')].find(vis);
    const grpEls = [grpOn, ...document.querySelectorAll('#mtabs .on, #tabbar .on, .mtabs .on')].filter(Boolean);
    const tabL = tabOn && vis(tabOn) ? norm(tabOn.innerText) : '';
    const g = grpEls.find(vis);
    const grpL = (g ? norm(g.innerText) : '') || (grpOn ? norm(grpOn.textContent) : '');
    let hEl = v && ([...v.querySelectorAll('h1')].find(vis) || [...v.querySelectorAll('h2')].find(vis));
    const hdrT = document.querySelector('#crumbs b');
    if (v && v.querySelector('.ph h2.td-in-hdr') && hdrT && vis(hdrT)) hEl = hdrT;
    const heading = hEl ? norm(hEl.innerText) : '';
    const sig = C.sig();
    // what the person looks at now: the newest overlay, else the view
    const viewText = v ? norm(v.innerText).slice(0, 20000) : '';
    const top = viewText.slice(0, 600);
    // a highlighted row after a jump (flash, highlight, :target, selected)
    const hl = v ? [...v.querySelectorAll('.rec-hl, .flash, .hl, .highlight, .pulse, .is-target, .sel, .selected, :target, [class*="flash"], [class*="hilite"]')].filter(vis).map(e => norm(e.innerText).slice(0, 200)) : [];
    // the section the page scrolled to: the first heading at the top of the screen
    const anchor = v ? ([...v.querySelectorAll('h2, h3, h4, .sec-h, .card-h, legend')].filter(vis).find(h => { const q = h.getBoundingClientRect(); return q.top >= -4 && q.top < innerHeight * 0.6; }) || null) : null;
    const activeTabs = [...document.querySelectorAll('.tl-focus b, [class*="focus"] b, .gl.on .gl-k, .ctabs .on, .seg .on, .tabs .on, [role=tab][aria-selected=true], .sub-tabs .on, [class*="chips"] .on, .chip.on, [aria-pressed=true]')].filter(vis).map(e => norm(e.innerText).slice(0, 60));
    const out = {
      view, cur: DB.currentId, viewChanged: view !== C.preView, curChanged: DB.currentId !== C.preCur,
      anchor: anchor ? norm(anchor.innerText).slice(0, 80) : '',
      keys, rawKeys, changes: real.slice(0, 16), noise: changes.length - real.length, overlays: ovInfo, stillOv, heading, tabL, grpL, top, hl, activeTabs,
      sigChanged: sig.full !== C.preSig.full, viewSigChanged: sig.view !== C.preSig.view, scrolled: Math.abs(sig.sy - C.preSig.sy) > 4 || C.scrollAt > C.pressAt, sy: sig.sy,
      toasts: C.toasts.slice(0, 6), opens: R.opens.slice(), prints: R.prints, ext: R.ext.slice(), stacks: R.stacks.slice(0, 3),
      // blank: next to no text and nothing to press (a hub whose one tile is the way on is not blank)
      blank: !ovs.length && (!v || (norm(v.innerText).length < 25 && ![...v.querySelectorAll('button, a[href], input, select, textarea, [role=button]')].some(e => e.getClientRects().length))),
      viewLen: viewText.length,
    };
    if (opts && opts.text) out.viewText = viewText;
    return out;
  };
  // press the first Open link a toast carried, then read where it went
  C.followToast = () => {
    const a = C.links.find(x => x && x.onclick);
    if (!a) return false;
    C.before();
    try { a.onclick({preventDefault() {}, stopPropagation() {}, target: a}); } catch (e) { console.warn('crawl toast link', e); }
    return norm(a.innerText || a.textContent);
  };

  // ---- the app's own UI state: top-level let/const values (filters, open rows, the open client, a tile's
  // focus). Their names come from the debugger (Runtime.globalLexicalScopeNames). A value is kept when it
  // can be cloned and is not DB itself, a function or a DOM node; on restore only what changed is put back.
  const NOT_STATE = new Set(['DB', 'S', 'view', 'trDataDB', 'saveTimer', 'trSaveSeq', 'trSavedSeq', 'lastSaved', 'askEl', 'askOn', 'saveState', 'holidaySet', 'holidaySets', 'TZ_FMT']);
  const ser = v => { try { return JSON.stringify(v, (k, x) => x instanceof Set ? {__set: [...x]} : x instanceof Map ? {__map: [...x]} : x); } catch (e) { return null; } };
  C.initState = (names) => {
    C.state = [];
    for (const n of names) {
      if (NOT_STATE.has(n) || n.startsWith('__cr')) continue;
      let get; try { get = new Function('return ' + n); get(); } catch (e) { continue; }
      const v = get();
      if (typeof v === 'function' || v === DB || (v && (v instanceof Node || v === window))) continue;
      let isConst = false; try { new Function('v', n + ' = v')(v); } catch (e) { isConst = true; }
      if (isConst && (v === null || typeof v !== 'object')) continue;
      try { structuredClone(v); } catch (e) { continue; }
      C.state.push({n, get, set: isConst ? null : new Function('v', n + ' = v'), isConst});
    }
    const fr = document.createElement('iframe'); document.body.appendChild(fr);
    C.std = new Set(Object.getOwnPropertyNames(fr.contentWindow)); fr.remove();
    C.scanWindow();
    return C.state.length;
  };
  // properties set on window (window.mApprKind = ...), beyond what a blank window holds; scanned again at
  // each snapshot, since a screen sets its own the first time it draws
  C.scanWindow = () => {
    const std = C.std, lex = new Set(C.state.map(x => x.n));
    for (const n of Object.getOwnPropertyNames(window)) {
      if (std.has(n) || lex.has(n) || NOT_STATE.has(n) || n.startsWith('__cr') || /^on/.test(n)) continue;
      let v; try { v = window[n]; } catch (e) { continue; }
      if (typeof v === 'function' || v === DB || (v && (v instanceof Node || v === window))) continue;
      const d = Object.getOwnPropertyDescriptor(window, n); if (!d || (!d.writable && !d.set)) continue;
      try { structuredClone(v); } catch (e) { continue; }
      C.state.push({n, get: () => window[n], set: x => { window[n] = x; }, isConst: false});
    }
  };
  C.snapState = () => { C.scanWindow(); for (const st of C.state || []) { const v = st.get(); st.s = ser(v); try { st.v = structuredClone(v); } catch (e) { st.v = undefined; st.s = null; } } };
  // a value that now holds DOM nodes is the app's bookkeeping of the live page (the one-strip toolbar's list
  // of what it moved, osMoved): rewinding it while the page stays as it is strands those nodes
  const holdsNode = (v, d = 0) => {
    if (!v || typeof v !== 'object' || d > 3) return false;
    if (v instanceof Node) return true;
    for (const k in v) { try { if (holdsNode(v[k], d + 1)) return true; } catch (e) {} }
    return false;
  };
  C.restoreState = () => {
    let n = 0;
    for (const st of C.state || []) {
      if (st.s == null) continue;
      const cur = st.get();
      if (ser(cur) === st.s) continue;
      if (holdsNode(cur)) continue;
      const v = structuredClone(st.v); n++;
      if (!st.isConst) { try { st.set(v); } catch (e) {} continue; }
      try {
        if (cur instanceof Set) { cur.clear(); v.forEach(x => cur.add(x)); }
        else if (cur instanceof Map) { cur.clear(); v.forEach((x, k) => cur.set(k, x)); }
        else if (Array.isArray(cur)) { cur.length = 0; cur.push(...v); }
        else if (cur && typeof cur === 'object') { for (const k of Object.keys(cur)) delete cur[k]; Object.assign(cur, v); }
      } catch (e) {}
    }
    return n;
  };

  // ---- snapshot / restore of one view's state
  C.snap = () => {
    C.snapDb = JSON.stringify(DB);
    C.snapView = view; C.snapCur = DB.currentId;
    C.snapKids = new Set(document.body.children);
    C.snapCls = [...document.body.children].map(e => [e, e.className, e.getAttribute('style')]);
    C.snapBody = document.body.className; C.snapHtml = document.documentElement.className;
    C.snapState();
    // the browser's own storage holds UI choices too (dashAll, dashView, tableSort, the tasks mode)
    const st = o => { const out = {}; try { for (let i = 0; i < o.length; i++) { const k = o.key(i); out[k] = o.getItem(k); } } catch (e) {} return out; };
    C.snapLS = st(localStorage); C.snapSS = st(sessionStorage);
    C.snapSig = C.sig();
    if (window.__crDebug) C.snapDump = C.dump();
    return C.snapSig.stable;
  };
  const closeLayers = () => {
    try { typeof mbCloseModal === 'function' && mbCloseModal(); } catch (e) {}
    document.querySelectorAll('#mbm, #mbm-held').forEach(x => x.remove());
    for (const c of [...document.body.children]) if (!C.snapKids.has(c)) { if (window.__crDebug) (C.removed = C.removed || []).push(c.tagName + '#' + c.id + '.' + c.className); c.remove(); }
    for (const [e, cls, st] of C.snapCls) { if (e.className !== cls) e.className = cls; if (e.getAttribute('style') !== st) { st == null ? e.removeAttribute('style') : e.setAttribute('style', st); } }
    document.body.className = C.snapBody; document.documentElement.className = C.snapHtml;
    const t = document.getElementById('toast'); t.classList.remove('on', 'act', 'toast-up');
  };
  const scrollBack = () => { window.scrollTo(0, C.snapSig.sy); document.documentElement.scrollTop = C.snapSig.sy; document.body.scrollTop = C.snapSig.sy; const m = document.querySelector('.main'); if (m) m.scrollTop = 0; };
  const putStore = (o, snap) => { try { const want = JSON.stringify(snap); const have = {}; for (let i = 0; i < o.length; i++) { const k = o.key(i); have[k] = o.getItem(k); } if (JSON.stringify(have) === want) return; o.clear(); for (const [k, v] of Object.entries(snap || {})) o.setItem(k, v); } catch (e) {} };
  C.restore = (full) => {
    closeLayers();
    if (full) {
      putStore(localStorage, C.snapLS); putStore(sessionStorage, C.snapSS);
      C.restoreState();
      DB = JSON.parse(C.snapDb); setCurrent(C.snapCur); view = C.snapView;
      render();
      closeLayers();
    }
    scrollBack();
    C.toasts = []; C.links = [];
    return C.sig().stable === C.snapSig.stable;
  };
  // a structural dump, to say what drifted (CRAWL_DEBUG=1)
  C.dump = () => { const out = []; const walk = (el, d) => { for (const c of el.children) { if (c.tagName === 'SCRIPT' || c.id === 'toast') continue; if (c.classList.contains('view') && !c.classList.contains('on')) continue; if (el === document.body && !vis(c)) continue; if (c.hidden || /display:\s*none/.test(c.getAttribute('style') || '')) continue; const own = [...c.childNodes].filter(n => n.nodeType === 3 && n.data.trim()).map(n => n.data.trim().replace(/\d+/g, '#')).join(' '); out.push(' '.repeat(d) + c.tagName + '#' + c.id + '.' + (typeof c.className === 'string' ? c.className : '') + ' ' + (c.style ? c.style.cssText : '') + (c.hidden ? ' H' : '') + (c.open ? ' O' : '') + ' ' + own.slice(0, 60)); walk(c, d + 1); } }; out.push('BODY.' + document.body.className + ' HTML.' + document.documentElement.className); walk(document.body, 0); return out; };
  // what rendering view v alone writes into DB (lazy defaults, derived caches): not the press's doing
  C.renderWrites = (v, cur) => {
    DB = JSON.parse(C.snapDb); setCurrent(C.snapCur);
    C.before();
    if (cur && cur !== DB.currentId) setCurrent(cur);
    view = v; render();
    const r = C.after({});
    return r.keys;
  };
  C.dbSame = () => JSON.stringify(DB) === C.snapDb;
  return 'ok';
}
"""

# What a client must never see: another client's name, another job, another client's document numbers, the
# firm's bills and POs (askgen_privacy_test's rule, read off the screen instead of an answer).
LEAK_WORDS_JS = r"""
() => {
  const u = currentUser(), cid = u && u.clientId;
  if (!cid) return [];
  const others = DB.clients.filter(c => c.id !== cid);
  const short = p => String(p.project.name).replace(/ —.*$/, '');
  const mine = new Set(DB.projects.filter(p => p.clientId === cid).map(short));
  const me = DB.clients.find(c => c.id === cid);
  const meWords = new Set(String(me && me.name || '').split(/[^A-Za-z]+/));
  const w = others.map(c => String(c.name).split(/[^A-Za-z]+/).filter(t => t.length >= 4 && !/^(family|the|llc|lenox|street|state)$/i.test(t) && !meWords.has(t)).pop()).filter(Boolean)
    .concat(DB.projects.filter(p => p.clientId !== cid).map(short).filter(n => !mine.has(n) && n.length >= 6))
    .concat(others.flatMap(c => [...(c.invoices || []), ...(c.estimates || []), ...(c.changeOrders || [])].map(d => d.number)).filter(Boolean))
    .concat((DB.bills || []).map(b => b.number).filter(n => n && n.length >= 5)).concat((DB.pos || []).map(p => p.number).filter(Boolean));
  return [...new Set(w)];
}
"""

# ---------------------------------------------------------------------------------------------- judging
NAV_KINDS = {'rail', 'mtab', 'subtab'}
DOC_RE = re.compile(r'\b[A-Z]{2,5}-\d{2,4}(?:-\d{2,5})?(?:-R\d+)?\b')
STOP = {'the', 'a', 'an', 'of', 'to', 'for', 'and', 'on', 'in', 'my', 'all', 'open', 'view', 'new', 'by', 'with',
        'this', 'that', 'at', 'from', 'is', 'are', 'what', 'who', 'see', 'show'}
# A verb on a button promises an act. Its result must name it: a DB change, a toast, or an overlay / page
# whose words match.
VERBS = [
    (r'^approve\b', r'approv'),
    (r'^(send|resend)\b', r'\b(send|sent|email|mail|draft|to:|message|share)'),
    (r'^record (a )?payment\b', r'payment|paid|deposit|receiv'),
    (r'^(order|reorder)\b', r'order|purchase|\bpo\b|vendor'),
    (r'^chase\b', r'chase|remind|draft|follow|nudge|email'),
    (r'^draft\b', r'draft|write|email|message'),
    (r'^(pay|pay now)\b', r'pay'),
    (r'^bill\b', r'bill|invoice'),
    (r'^(reject|decline)\b', r'reject|declin|reason'),
    (r'^(sign|countersign)\b', r'sign'),
    (r'^(publish)\b', r'publish'),
    (r'^(book)\b', r'book|inspection|calendar|hold'),
]
OPEN_RE = re.compile(r'^(open|view|go to)\b\s*(.*)$', re.I)
DESTRUCT_RE = re.compile(r'^(delete|void|reject|remove|discard)\b', re.I)
ASKISH = re.compile(r'\bask\b|assistant|\?$|^(what|who|when|how|which|why|show me|list)\b', re.I)


def norm(s):
    return re.sub(r'\s+', ' ', (s or '')).strip()


def nkey(s):
    s = re.sub(r'\s*\d+\+?\s*$', '', norm(s))
    return s.replace('&', 'and').lower()


def words(s):
    return {w for w in re.findall(r'[a-z]{3,}', (s or '').lower()) if w not in STOP}


def stem(w):
    return re.sub(r'(ies|es|s|ing|ed)$', '', w)


def share(a, b):
    """Two phrases name the same thing: a word in common, stemmed, or a common 5-letter start (renewal / renew)."""
    A = {stem(w) for w in words(a)}; B = {stem(w) for w in words(b)}
    if A & B: return True
    pa = {w[:5] for w in A if len(w) >= 5}; pb = {w[:5] for w in B if len(w) >= 5}
    return bool(pa & pb)


def dest_title(r):
    if r['overlays']: return r['overlays'][-1]['title']
    return r['heading']


def heading_ok(r, label):
    """lint's heading-vs-nav rule, plus: the entry pressed is the active one."""
    h, tabL, grpL = nkey(r['heading']), nkey(r['tabL']), nkey(r['grpL'])
    ok = lambda l: l and (l == h or h.startswith(l + ' — ') or h.startswith(l + ' · '))
    return bool(h) and (ok(tabL) or ok(grpL))


def judge(c, r, ctx):
    """Returns [(rule, detail)] for one press. c: the control; r: what happened; ctx: user, role, views."""
    out = []
    L = c['label']
    lab = L.lower()
    if r.get('errors'):
        st = (r.get('stacks') or [''])[0]
        out.append(('ERROR', r['errors'][0].splitlines()[0][:200] + (f' [{st[:160]}]' if st else '')))
    mutated = [k for k in r['keys'] if k not in UI_KEYS]
    toasts = r['toasts']
    linked = [t for t in toasts if t['links']]
    moved = r['viewChanged'] or r['overlays'] or r['scrolled'] or r['curChanged']
    side = r['dialogs'] or r['opens'] or r['prints'] or r['ext'] or r['downloads'] or r['choosers'] or r.get('reloaded')
    acted = bool(mutated or toasts or moved or side or r['sigChanged'])
    if not acted:
        if c.get('active'):
            return out   # pressing the entry you are on
        if c['kind'] == 'ws':
            return [('INFO', 'the workspace you are in')]
        out.append(('NOOP', 'nothing changed: no navigation, overlay, toast, dialog or DB change'))
        return out
    # dead ends
    if r['viewChanged'] and r['view'] not in ctx['views'] and r['view'] != ctx['view']:
        out.append(('DEADEND', f"lands on view '{r['view']}', which {ctx['role']} may not open"))
    elif r['blank'] and not side:
        out.append(('DEADEND', f"lands on a blank page (view '{r['view']}')"))
    elif r['viewChanged'] and r['view'] == 'pa' and ctx['view'] != 'pa' and not ASKISH.search(L) and 'ask' not in c['act'].lower() and c['kind'] not in NAV_KINDS:
        out.append(('DEADEND', 'falls through to Ask'))
    # nav entries: the heading names the entry pressed
    # (a nav entry that stays on the page and opens a menu, as the phone's More does, is judged by its menu)
    if c['kind'] in NAV_KINDS and not r['overlays'] and not side and (r['viewChanged'] or not r['sigChanged']):
        if not heading_ok(r, L):
            out.append(('MISMATCH', f"{c['kind']} \"{L}\" lands on heading \"{r['heading'][:50]}\" (active nav: \"{r['tabL'] or r['grpL']}\")"))
        elif nkey(L) not in (nkey(r['tabL']), nkey(r['grpL'])) and not share(L, r['tabL'] + ' ' + r['grpL'] + ' ' + r['heading']):
            out.append(('MISMATCH', f"{c['kind']} \"{L}\" lands on \"{r['heading'][:50]}\""))
    elif c['kind'] == 'tile' and (r['viewChanged'] or r['overlays']):
        t = dest_title(r)
        if t and not share(c.get('promise') or L, t + ' ' + ' '.join(r['activeTabs']) + ' ' + r.get('anchor', '') + ' ' + ' '.join(r['hl'])):
            out.append(('MISMATCH', f"tile \"{(c.get('promise') or L)[:40]}\" opens \"{t[:60]}\""))
    elif c['kind'] == 'tab' and not r['viewChanged'] and not r['overlays']:
        if r['activeTabs'] and not any(nkey(L) == nkey(a) or nkey(a).startswith(nkey(L)) for a in r['activeTabs']) and not r['sigChanged']:
            out.append(('MISMATCH', f"tab \"{L}\" did not become the active tab"))
    # "Open X" / "View X" / a record number: the record opened is that record
    m = OPEN_RE.match(L)
    target = None
    if m:
        target = m.group(2).strip()
        if not target or target.lower() in ('record', 'details', 'it', 'all', 'full', 'more', 'job', 'thread', 'the record'):
            dm = DOC_RE.search(c['rowText'] or '')
            target = dm.group(0) if dm else None
    elif DOC_RE.fullmatch(L.strip()):
        target = L.strip()
    # only a record named by number, or by a proper name, is checked against the destination ("Open the Kit",
    # "Open them" promise no particular record)
    if target and not DOC_RE.search(target) and not re.search(r'[A-Z][a-z]+ [A-Z0-9]|\d', target): target = None
    if target and not side:
        dest = ' '.join([o['title'] + ' ' + o['text'][:1500] for o in r['overlays']]) if r['overlays'] else ''
        here = r['heading'] + ' ' + r['top'] + ' ' + ' '.join(r['hl'])
        T = target.lower()
        found = T in dest.lower() or T in here.lower() or (len(T) > 3 and T in ' '.join(r['hl']).lower())
        if not found and not r['overlays'] and not r['viewChanged'] and not mutated:
            out.append(('MISMATCH', f"\"{L[:40]}\" opens nothing for {target[:40]} (stays on the list)"))
        elif not found and (r['overlays'] or r['viewChanged']):
            if DOC_RE.fullmatch(target) or words(target):
                if not (words(target) and share(target, dest_title(r)) and not DOC_RE.fullmatch(target)):
                    out.append(('MISMATCH', f"\"{L[:40]}\" opens \"{dest_title(r)[:60]}\" (view '{r['view']}'), not {target[:40]}"))
    # verbs promise an act
    verbish = c['kind'] in ('button', 'link', 'chip', 'top') and len(L.split()) <= 5 and not re.search(r'[\d$]', L)
    for vre, want in (VERBS if verbish else []):
        if re.search(vre, lab):
            if mutated or toasts or side: break
            txt = ' '.join(o['title'] + ' ' + o['text'] for o in r['overlays']) + ' ' + (r['heading'] + ' ' + r['top'] if r['viewChanged'] else '')
            if not re.search(want, txt, re.I) and not (r['overlays'] and share(re.sub(vre, '', lab), dest_title(r))):
                out.append(('MISMATCH', f"\"{L[:40]}\" did not act: no change, no toast; it shows \"{dest_title(r)[:60]}\""))
            break
    # a mutation tells the person what happened, with Open
    if mutated:
        what = ', '.join(sorted(set(mutated)))[:80]
        settings = ctx['view'] in ('setup', 'settings', 'conn', 'admin', 'company', 'users', 'prefs') or set(mutated) <= {'company', 'prefs', 'ui', 'settings'}
        if not toasts:
            if r['overlays'] and not DESTRUCT_RE.match(L):
                pass   # an editor or sheet opened: the save inside it owes the toast
            else:
                out.append(('INFO' if settings else 'SILENT', f'DB changed ({what}) with no toast'))
        elif not linked:
            out.append(('INFO' if settings else 'SILENT', f"toast \"{toasts[-1]['text'][:70]}\" has no Open link (DB: {what})"))
    if DESTRUCT_RE.match(L) and mutated and not r['dialogs'] and not r['overlays']:
        out.append(('DESTRUCTIVE', f"\"{L[:40]}\" changed {', '.join(mutated)[:60]} with no confirmation"))
    if r.get('toastLink'):
        tl = r['toastLink']
        if tl.get('errors'):
            out.append(('ERROR', 'toast link: ' + tl['errors'][0][:180]))
        elif not tl['acted']:
            out.append(('DEADEND', f"toast \"{toasts[-1]['text'][:50] if toasts else ''}\" link \"{tl['label']}\" goes nowhere"))
        elif tl.get('deadview'):
            out.append(('DEADEND', f"toast link \"{tl['label']}\" lands on view '{tl['view']}', which {ctx['role']} may not open"))
    return out


def leak_check(r, ctx):
    out = []
    text = ' '.join(o['title'] + ' ' + o['text'] for o in r['overlays']) + ' ' + (r.get('viewText') or '')
    if ctx['role'] == 'client':
        for w in ctx['leakWords']:
            if re.search(r'(?<![A-Za-z0-9])' + re.escape(w) + r'(?![A-Za-z0-9])', text):
                i = text.find(w)
                out.append(('LEAK', w, f"shows \"{w}\" (another client's): \"…{text[max(0, i - 40):i + 50]}…\""))
    elif ctx['role'] in FIELD_ROLES:
        m = re.search(r'\$\s?\d[\d,.]*', text)
        if m:
            i = m.start()
            out.append(('LEAK', m.group(0), f"shows money to {ctx['role']}: \"…{text[max(0, i - 50):i + 30]}…\""))
    return out


def allowed(rule, c, view):
    for ar, lre, vre, _ in ALLOW:
        if ar == rule and re.search(lre, c['label'], re.I) and (vre is None or re.search(vre, view)):
            return True
    return False


# ---------------------------------------------------------------------------------------------- the crawl
class Crawler:
    def __init__(self, a):
        self.a = a
        self.tm = Counter()
        self.flags, self.infos = [], []
        self.pressed = Counter(); self.screens = 0; self.skipped = Counter(); self.skipped_ex = defaultdict(list)
        self.covered = Counter(); self.disabled = Counter(); self.drift = 0; self.reloads = 0
        self.shots_by = Counter(); self.leak_seen = set()
        self.errs, self.dialogs, self.downloads, self.choosers, self.popups = [], [], [], [], []
        self.navigated = False

    async def boot(self, p, phone):
        self.b = await p.chromium.launch()
        self.ctx = await self.b.new_context(viewport=PHONE if phone else DESKTOP, is_mobile=phone, has_touch=phone)
        await self.ctx.add_init_script(INIT_JS)
        self.pg = pg = await self.ctx.new_page()
        self.ctx.on('page', lambda np: np != pg and (self.popups.append(np.url) or asyncio.ensure_future(np.close())))
        pg.on('pageerror', lambda e: self.errs.append(str(e)))
        # a resource the network refused (a font, a public records API through the proxy) is the network's, not
        # the page's: noted by the browser with no script behind it
        pg.on('console', lambda m: m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text and 'Failed to load resource' not in m.text and self.errs.append('console: ' + m.text))
        pg.on('dialog', lambda d: self.dialogs.append(f'{d.type}: {d.message[:100]}') or asyncio.ensure_future(d.dismiss()))
        pg.on('download', lambda d: self.downloads.append(d.suggested_filename) or asyncio.ensure_future(d.cancel()))
        pg.on('filechooser', lambda fc: self.choosers.append(1))
        # a reload or a real navigation drops window.__cr; hash changes (the app's routes) do not
        pg.on('load', lambda *_: setattr(self, 'navigated', True))
        await self.load()
        want = (PHONE if phone else DESKTOP)['width']
        if await pg.evaluate('innerWidth') != want: raise SystemExit('layout width is not the viewport: is the viewport meta missing?')
        self.boot_db = await pg.evaluate('() => JSON.stringify(DB)')
        # every later load (a reload after drift, the confirm pass) starts from this boot's browser storage,
        # so a UI choice one press stored (dashAll, tableSort) never reaches a later press
        store = await pg.evaluate("() => { const st = o => { const out = {}; for (let i = 0; i < o.length; i++) { const k = o.key(i); out[k] = o.getItem(k); } return out; }; return [st(localStorage), st(sessionStorage)]; }")
        await self.ctx.add_init_script("((ls, ss) => { try { localStorage.clear(); sessionStorage.clear(); for (const [k, v] of Object.entries(ls)) localStorage.setItem(k, v); for (const [k, v] of Object.entries(ss)) sessionStorage.setItem(k, v); } catch (e) {} })(" + json.dumps(store[0]) + ", " + json.dumps(store[1]) + ")")

    async def load(self):
        await self.pg.goto(URL)
        await self.pg.wait_for_function("document.body.dataset.booted==='1'", timeout=90000)
        if os.environ.get('CRAWL_DEBUG'): await self.pg.evaluate('() => { window.__crDebug = 1; }')
        await self.pg.evaluate(PAGE_JS)
        cdp = await self.ctx.new_cdp_session(self.pg)
        names = (await cdp.send('Runtime.globalLexicalScopeNames'))['names']
        await cdp.detach()
        self.nstate = await self.pg.evaluate('n => window.__cr.initState(n)', names)
        await self.pg.evaluate('p => { window.__cr.uiPaths = p; }', UI_PATHS)
        self.navigated = False

    async def settle(self, q=150, mx=1500):
        try: return await self.pg.evaluate('([q, m]) => window.__cr ? window.__cr.quiet(q, m) : 0', [q, mx])
        except Exception: return 0

    async def start_user(self, u):
        await self.pg.evaluate("([db, u]) => { DB = JSON.parse(db); signIn(u); render(); }", [self.boot_db, u])
        await self.settle()
        # the views a press may land on: the role's, plus the Mercer & Bond workspace's when the person has it
        return await self.pg.evaluate("""() => ({role: role(), views: (ROLE_VIEWS[role()] || []).slice(), user: currentUser() && currentUser().id,
          may: (ROLE_VIEWS[role()] || []).concat(typeof mbAccess === 'function' && mbAccess() && typeof MB_VIEWS !== 'undefined' ? MB_VIEWS : [])})""")

    async def open_view(self, v):
        # a Mercer & Bond view is opened in its own workspace (the switch a person presses first)
        await self.pg.evaluate("""v => { document.querySelectorAll('#mbm').forEach(x => x.remove());
          const mb = typeof MB_VIEWS !== 'undefined' && MB_VIEWS.includes(v);
          if (mb && typeof mbAccess === 'function' && mbAccess()) DB.workspace = 'mb'; else if (!mb && DB.workspace === 'mb') DB.workspace = 'sd';
          view = v; render(); window.scrollTo(0, 0); }""", v)
        await self.settle(200, 2500)
        # the snapshot is taken after a second render: some pages finish drawing on the render after the one
        # that opened them (a tile host added late), and every restore draws the page again
        await self.pg.evaluate("() => { render(); window.scrollTo(0, 0); }")
        await self.settle(150, 2000)
        await self.pg.evaluate("() => { const t = document.getElementById('toast'); t && t.classList.remove('on', 'act', 'toast-up'); window.scrollTo(0, 0); }")
        await self.pg.evaluate('() => window.__cr.snap()')
        self.view_db = await self.pg.evaluate('() => window.__cr.snapDb')
        self.view_v = v

    async def reboot_view(self, u):
        """The page left (a reload or a navigation) or drifted: boot again and put the view back."""
        self.reloads += 1
        await self.load()
        await self.pg.evaluate("([db, u, v]) => { DB = JSON.parse(db); signIn(u); DB = JSON.parse(db); setCurrent(DB.currentId); view = v; render(); window.scrollTo(0, 0); }", [self.view_db, u, self.view_v])
        await self.settle(200, 2500)
        await self.pg.evaluate("() => { const t = document.getElementById('toast'); t && t.classList.remove('on', 'act', 'toast-up'); window.scrollTo(0, 0); }")
        await self.pg.evaluate('() => window.__cr.snap()')

    async def fresh(self, dirty, u):
        """Put the view back to its snapshot before the next press."""
        if self.navigated or not await self.pg.evaluate('() => !!window.__cr'):
            await self.reboot_view(u); return
        if not dirty: return
        full = dirty == 'full'
        same = '() => window.__cr.sig().stable === window.__cr.snapSig.stable'
        try:
            ok = await self.pg.evaluate('f => window.__cr.restore(f)', full)
            if not ok and not full:
                full = True
                ok = await self.pg.evaluate('f => window.__cr.restore(f)', True)
            if full:
                # a render finishes after it returns (the active sub-tab is scrolled into view on a timer):
                # press only once the page is still
                await self.settle(100, 1200)
            if not ok:
                # a render finishes its asynchronous parts after it returns
                await self.settle(120, 1500)
                await self.pg.evaluate('() => window.__cr.restore(false)')
                ok = await self.pg.evaluate(same)
            if not ok:
                self.drift += 1
                if os.environ.get('CRAWL_DEBUG'):
                    import difflib
                    a, b = await self.pg.evaluate('() => [window.__cr.snapDump || [], window.__cr.dump()]')
                    print('DRIFT', self.view_v, '\n'.join(list(difflib.unified_diff(a, b, lineterm='', n=0))[:14]))
                await self.reboot_view(u)
        except Exception:
            await self.reboot_view(u)
        del self.errs[:]

    async def press(self, c, phone):
        pg = self.pg
        pt = await pg.evaluate('([k, n]) => window.__cr.point(k, n)', [c['key'], c['n']])
        if pt.get('missing'): return {'missing': True}
        if pt.get('covered'): return {'covered': pt['covered']}
        await pg.evaluate('() => window.__cr.before()')
        del self.errs[:]; del self.dialogs[:]; del self.downloads[:]; del self.choosers[:]; del self.popups[:]
        self.navigated = False
        try:
            if phone: await pg.touchscreen.tap(pt['x'], pt['y'])
            else: await pg.mouse.click(pt['x'], pt['y'])
        except Exception as e:
            self.errs.append('crawl: click failed ' + str(e).splitlines()[0][:100])
        t1 = time.time(); await self.settle(); self.tm['settle'] += time.time() - t1
        r = None
        if not self.navigated:
            try: r = await pg.evaluate('o => window.__cr && window.__cr.after(o)', {'text': self.leaky})
            except Exception: r = None
        if not r:
            # the page reloaded or navigated away
            await self.pg.wait_for_timeout(300)
            r = {'view': '?', 'cur': '', 'viewChanged': True, 'curChanged': False, 'keys': [], 'changes': [], 'overlays': [], 'stillOv': [],
                 'heading': '', 'tabL': '', 'grpL': '', 'top': '', 'hl': [], 'activeTabs': [], 'sigChanged': True, 'scrolled': False,
                 'toasts': [], 'opens': [], 'prints': 0, 'ext': [], 'blank': False, 'reloaded': True, 'viewLen': 0}
        r.update(errors=[e for e in self.errs if not e.startswith('crawl:')], dialogs=self.dialogs[:], downloads=self.downloads[:],
                 choosers=len(self.choosers), opens=r.get('opens', []) + self.popups[:])
        return r

    async def follow_toast(self, r, ctx):
        del self.errs[:]
        lab = await self.pg.evaluate('() => window.__cr.followToast()')
        if not lab: return None
        await self.settle()
        t = await self.pg.evaluate('() => window.__cr.after({})')
        acted = t['viewChanged'] or t['overlays'] or t['scrolled'] or t['sigChanged'] or t['curChanged']
        if not acted:
            # already on the record the toast names: its number is on the screen's head or open sheet
            toks = [m.group(0) for tt in r['toasts'] for m in DOC_RE.finditer(tt['text'])]
            here = ' '.join([t['heading'], t['top']] + [o['title'] + ' ' + o['text'][:400] for o in t['stillOv']])
            acted = bool(toks) and any(k in here for k in toks)
        return {'label': lab, 'acted': bool(acted), 'view': t['view'], 'title': dest_title(t), 'errors': self.errs[:],
                'deadview': t['viewChanged'] and t['view'] not in ctx['views']}

    async def shot(self, rule, vp, n):
        if self.shots_by[(rule, vp)] >= 12: return None
        self.shots_by[(rule, vp)] += 1
        os.makedirs(SHOTS, exist_ok=True)
        path = os.path.join(SHOTS, f'{rule.lower()}_{vp}_{self.cur_user}_{n}.png')
        try: await self.pg.screenshot(path=path); return os.path.relpath(path, ROOT)
        except Exception: return None

    def plan(self, cands, chrome_done):
        a = self.a
        fam = Counter(); out = []; skipped = []
        for c in cands:
            if c['scope'] == 'overlay':
                skipped.append(('overlay', c)); continue
            if c['scope'] == 'chrome':
                ck = (c['key'], c['n'])
                if ck in chrome_done: continue
            fam[c['family']] += 1
            if fam[c['family']] > a.per_family:
                skipped.append(('family', c)); continue
            out.append(c)
        # the view's own controls first, then the chrome not yet pressed for this user
        out = [c for c in out if c['scope'] == 'view'] + [c for c in out if c['scope'] == 'chrome']
        if len(out) > a.max_per_view:
            skipped += [('cap', c) for c in out[a.max_per_view:]]
            out = out[:a.max_per_view]
        for c in out:
            if c['scope'] == 'chrome': chrome_done.add((c['key'], c['n']))
        return out, skipped

    def add_flag(self, rule, vp, u, v, c, detail, shot=None, r=None):
        f = {'rule': rule, 'viewport': vp, 'user': u, 'view': v, 'label': c['label'][:80], 'kind': c['kind'], 'key': c['key'], 'n': c['n'],
             'detail': detail, 'shot': shot}
        if r is not None:
            f['dest'] = {'view': r.get('view'), 'title': dest_title(r)[:80] if 'heading' in r else '', 'db': [f"{x['op']} {x['path']}{(' ' + x['id']) if x.get('id') else ''}" for x in r.get('changes', [])[:6]],
                         'toasts': [t['text'][:80] + (' [' + ', '.join(t['links']) + ']' if t['links'] else '') for t in r.get('toasts', [])[:3]]}
        if rule == 'INFO': self.infos.append(f)
        else: self.flags.append(f)
        if not self.a.quiet and rule != 'INFO' and (not self.a.rules or rule in self.a.rules):
            print(f"{rule} | {vp} | {u} | {v} | {c['label'][:50]} | {detail}", flush=True)

    async def assess(self, c, r, ctx, rw_cache, leaks=True):
        """The flags one press earns: (rule, detail) pairs, the allowlist applied."""
        if r['keys'] and not r['toasts'] and r['view'] != '?':
            # what drawing the destination writes by itself (lazy defaults, caches) is not the press's doing
            # a new page's own writes are cached per page and job; a press that stayed on the page (a tab, a
            # filter) is measured each time, since what the page draws depends on the state the press set
            ck = (r['view'], r.get('cur'))
            rk = rw_cache.get(ck) if r['viewChanged'] else None
            if rk is None:
                rk = set(await self.pg.evaluate('([v, c]) => window.__cr.renderWrites(v, c)', [r['view'], r.get('cur')]))
                if r['viewChanged']: rw_cache[ck] = rk
            r['renderKeys'] = sorted(rk & set(r['keys']))
            r['keys'] = [k for k in r['keys'] if k not in rk]
        found = judge(c, r, ctx)
        if self.leaky and leaks:
            for rule, tok, det in leak_check(r, ctx):
                k = (ctx['vp'], ctx['user'], tok, r['view'], dest_title(r))
                if k in self.leak_seen: continue
                self.leak_seen.add(k); found.append((rule, det))
        return [(rule, det) for rule, det in found if not allowed(rule, c, ctx['view'])]

    async def confirm(self, phone):
        """Each flag again, from a freshly booted page: the view opened straight after sign-in, the control
        pressed once. A flag that does not come back was made by the crawl's own sequence, not by the app."""
        vp = 'phone' if phone else 'desktop'
        groups = defaultdict(list)
        for f in self.flags:
            if f['viewport'] == vp and f['rule'] != 'LEAK' and not f.get('confirmed'): groups[(f['user'], f['view'])].append(f)
        # one boot per flag: two flags confirmed in one page would make the second ride on the first's
        # leftovers, the very thing this pass is here to rule out
        for (u, v), fl in groups.items():
            for f in fl:
                await self.load()
                info = await self.start_user(u)
                role, views = info['role'], info['may']
                self.leaky = False
                await self.open_view(v)
                ctx = {'user': u, 'role': role, 'views': views, 'view': v, 'leakWords': [], 'vp': vp}
                rw_cache = {}
                lst = await self.pg.evaluate('() => window.__cr.list()')
                c = next((x for x in lst['cands'] if x['key'] == f['key'] and x['n'] == f['n']), None)
                if not c:
                    f['confirmed'] = 'gone'; continue
                r = await self.press(c, phone)
                if r.get('missing') or r.get('covered'):
                    f['confirmed'] = 'gone'; continue
                again = await self.assess(c, r, ctx, rw_cache, leaks=False)
                if 'toast' in f['detail'] and 'link' in f['detail'] and any(t['links'] for t in r['toasts']):
                    tl = await self.follow_toast(r, ctx)
                    if tl: again += [x for x in judge(c, dict(r, toastLink=tl, errors=[]), ctx) if 'link' in x[1]]
                f['confirmed'] = any(rule == f['rule'] for rule, _ in again)
                if not f['confirmed'] and not self.a.quiet:
                    print(f"not reproduced from a fresh boot: {f['rule']} | {vp} | {u} | {v} | {f['label'][:50]}", flush=True)
        # what did not come back is the crawl's doing: noted, not flagged
        keep = []
        for f in self.flags:
            if f['viewport'] == vp and f.get('confirmed') is False:
                f['detail'] = 'not reproduced from a fresh boot: ' + f['rule'] + ' ' + f['detail']
                self.infos.append(f)
            else: keep.append(f)
        self.flags = keep

    async def run(self):
        a = self.a
        async with async_playwright() as p:
            for phone in a.vps:
                vp = 'phone' if phone else 'desktop'
                await self.boot(p, phone)
                for u in a.users:
                    info = await self.start_user(u)
                    if info['user'] != u:
                        print(f'skip {u}: no such user'); continue
                    role, views, may = info['role'], info['views'], info['may']
                    self.cur_user = u
                    self.leaky = role == 'client' or role in FIELD_ROLES
                    leak_words = await self.pg.evaluate(LEAK_WORDS_JS) if role == 'client' else []
                    chrome_done = set(); rw_cache = {}
                    t_user = time.time(); n_user = 0
                    for v in views:
                        if a.views and v not in a.views: continue
                        try:
                            await self.open_view(v)
                        except Exception as e:
                            # an earlier press left the page unable to draw this view: start clean and try once more
                            self.reloads += 1
                            await self.load(); await self.start_user(u)
                            try: await self.open_view(v)
                            except Exception as e2:
                                c0 = {'label': '(opening the view)', 'kind': 'view', 'key': 'view|' + v, 'n': 1}
                                self.add_flag('ERROR', vp, u, v, c0, 'opening the view throws: ' + str(e2).splitlines()[0][:160])
                                continue
                        landed = await self.pg.evaluate('() => view')
                        if landed != v:
                            # not a screen of its own for this person: opening it lands elsewhere (counted there)
                            self.infos.append({'rule': 'INFO', 'viewport': vp, 'user': u, 'view': v, 'label': '', 'kind': '', 'key': '', 'detail': f'opening {v} lands on {landed}'})
                            continue
                        self.screens += 1
                        lst = await self.pg.evaluate('() => window.__cr.list()')
                        for d in lst['disabled']: self.disabled[(vp, u, v)] += 1
                        plan, skipped = self.plan(lst['cands'], chrome_done)
                        for why, c in skipped:
                            self.skipped[why] += 1
                            if len(self.skipped_ex[(vp, u, v)]) < 12: self.skipped_ex[(vp, u, v)].append(f"{why}: {c['label'][:40]}")
                        ctx = {'user': u, 'role': role, 'views': may, 'view': v, 'leakWords': leak_words, 'vp': vp}
                        dirty = None
                        for c in plan:
                            t1 = time.time(); await self.fresh(dirty, u); self.tm['fresh ' + str(dirty)] += time.time() - t1; self.tm['n fresh ' + str(dirty)] += 1
                            t1 = time.time(); r = await self.press(c, phone); self.tm['press'] += time.time() - t1
                            if r.get('missing'):
                                self.skipped['gone after restore'] += 1; dirty = 'full'; continue
                            if r.get('covered'):
                                # a container whose face is all other controls (a strip, a card of buttons): its
                                # controls are pressed on their own; something else on top of it is noted
                                self.covered[(vp, u, v)] += 1
                                if 'another control' in r['covered']: self.skipped['all inner controls'] += 1
                                else: self.add_flag('INFO', vp, u, v, c, 'covered by ' + r['covered'])
                                dirty = None; continue
                            self.pressed[(vp, u)] += 1; n_user += 1
                            if os.environ.get('CRAWL_DEBUG'):
                                pr = await self.pg.evaluate(os.environ['CRAWL_PROBE']) if os.environ.get('CRAWL_PROBE') else ''
                                print('PRESS', v, '|', c['label'][:60], '->', r.get('view'), 'dirty', dirty, 'err', bool(r.get('errors')), pr, flush=True)
                            t1 = time.time(); found = await self.assess(c, r, ctx, rw_cache); self.tm['assess'] += time.time() - t1
                            for rule, det in found:
                                shot = None
                                if rule != 'INFO' and (not a.rules or rule in a.rules):
                                    shot = await self.shot(rule, vp, len(self.flags) + 1)
                                self.add_flag(rule, vp, u, v, c, det, shot, r)
                            # where the toast's Open goes
                            if any(t['links'] for t in r['toasts']) and not r.get('reloaded'):
                                tl = await self.follow_toast(r, ctx)
                                if os.environ.get('CRAWL_PROBE'): print('  FOLLOW', tl and tl.get('view'), await self.pg.evaluate(os.environ['CRAWL_PROBE']), flush=True)
                                if tl:
                                    r2 = dict(r, toastLink=tl, errors=[])
                                    for rule, det in judge(c, r2, ctx):
                                        if 'toast' in det and 'link' in det and not allowed(rule, c, v):
                                            self.add_flag(rule, vp, u, v, c, det, None, r)
                            mut = [k for k in r['keys'] if k not in UI_KEYS]
                            if r.get('reloaded') or self.navigated: dirty = 'full'
                            elif mut or r['viewChanged'] or r['curChanged'] or r['keys']: dirty = 'full'
                            elif r.get('viewSigChanged'): dirty = 'full'   # the page itself changed: draw it again
                            elif r['overlays'] or r['sigChanged'] or r['toasts'] or r['scrolled']: dirty = 'light'
                            else: dirty = None
                        # leave the view as found for the next one
                        await self.fresh(dirty if dirty else None, u)
                    if not a.quiet: print(f'-- {vp} {u}: {n_user} presses in {time.time() - t_user:.0f}s', flush=True)
                if not a.no_confirm:
                    t_c = time.time()
                    await self.confirm(phone)
                    if not a.quiet: print(f'-- {vp}: flags confirmed from a fresh boot in {time.time() - t_c:.0f}s', flush=True)
                await self.b.close()

    # ------------------------------------------------------------------------------------------ report
    def write(self, t0):
        a = self.a
        flags = [f for f in self.flags if not a.rules or f['rule'] in a.rules]
        os.makedirs(OUT, exist_ok=True)
        clicked = sum(self.pressed.values())
        data = {'flags': flags, 'info': self.infos, 'pressed': {f'{k[0]} {k[1]}': n for k, n in self.pressed.items()},
                'screens': self.screens, 'skipped': dict(self.skipped), 'skippedExamples': {' '.join(k): v for k, v in self.skipped_ex.items()},
                'disabled': {' '.join(k): n for k, n in self.disabled.items()}, 'drift': self.drift, 'reloads': self.reloads,
                'seconds': round(time.time() - t0)}
        jpath = a.json or os.path.join(OUT, 'flags.json')
        with open(jpath, 'w') as fh: json.dump(data, fh, indent=1)
        by_rule = Counter(f['rule'] for f in flags)
        L = ['# Click crawl', '',
             f'{clicked} controls pressed over {self.screens} screens in {(time.time() - t0) / 60:.1f} min; '
             f'{len(flags)} flags. Skipped: ' + ', '.join(f'{k} {n}' for k, n in self.skipped.items()) +
             f'. Drift reloads: {self.drift}; page reloads: {self.reloads}.', '',
             '## Flags by rule', '', '| Rule | Flags |', '|---|---|'] + [f'| {r} | {by_rule[r]} |' for r in SEVERITY if by_rule[r]]
        L += ['', '## Per user', '', '| Viewport | User | Pressed | ' + ' | '.join(SEVERITY) + ' |', '|---|---|---|' + '---|' * len(SEVERITY)]
        for (vp, u), n in sorted(self.pressed.items()):
            cnt = Counter(f['rule'] for f in flags if f['viewport'] == vp and f['user'] == u)
            L.append(f'| {vp} | {u} | {n} | ' + ' | '.join(str(cnt[r]) for r in SEVERITY) + ' |')
        worst = sorted(flags, key=lambda f: (SEVERITY.index(f['rule']), f['shot'] is None))[:30]
        L += ['', '## The worst 30', '']
        for f in worst:
            L.append(f"- **{f['rule']}** {f['viewport']} {f['user']} `{f['view']}` \"{f['label'][:50]}\": {f['detail']}" + (f" ([shot]({os.path.relpath(os.path.join(ROOT, f['shot']), OUT)}))" if f['shot'] else ''))
        L += ['', '## Every flag', '']
        for f in flags:
            L.append(f"- {f['rule']} | {f['viewport']} | {f['user']} | {f['view']} | {f['label'][:60]} | {f['detail']}")
        if self.infos:
            L += ['', '## Info (not flags)', '']
            for f in self.infos[:400]:
                L.append(f"- {f['viewport']} | {f['user']} | {f['view']} | {f['label'][:50]} | {f['detail']}")
        rpath = os.path.splitext(a.json)[0] + '.md' if a.json else os.path.join(OUT, 'report.md')
        with open(rpath, 'w') as fh: fh.write('\n'.join(L) + '\n')
        print('\nRule          Flags')
        for r in SEVERITY:
            if by_rule[r]: print(f'{r:<14}{by_rule[r]:>5}')
        if os.environ.get('CRAWL_DEBUG'): print('TIME', {k: round(v, 1) for k, v in self.tm.items()})
        print(f"INFO: {len(self.infos)} info lines; skipped {dict(self.skipped)}; drift {self.drift}; reloads {self.reloads}; {time.time() - t0:.0f}s")
        print(f'CRAWL {len(flags)} flags (clicked {clicked} controls over {self.screens} screens)')
        return 1 if flags else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--user'); ap.add_argument('--view'); ap.add_argument('--rule')
    ap.add_argument('--phone', action='store_true'); ap.add_argument('--desktop', action='store_true')
    ap.add_argument('--max-per-view', type=int, default=60); ap.add_argument('--per-family', type=int, default=3)
    ap.add_argument('--json'); ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--no-confirm', action='store_true', help='skip pressing each flag again from a fresh boot')
    a = ap.parse_args()
    a.rules = set(a.rule.upper().split(',')) if a.rule else None
    a.users = a.user.split(',') if a.user else CRAWL_USERS
    a.views = set(a.view.split(',')) if a.view else None
    a.vps = [False, True]
    if a.phone and not a.desktop: a.vps = [True]
    if a.desktop and not a.phone: a.vps = [False]
    t0 = time.time()
    cr = Crawler(a)
    asyncio.run(cr.run())
    sys.exit(cr.write(t0))


if __name__ == '__main__':
    main()
