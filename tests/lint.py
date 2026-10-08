"""The screen standard as code (docs/BACKLOG.md §0 items 1 and 7).

For every user in USERS x every view in ROLE_VIEWS[role()] x desktop (1440x900) and phone (390x844) it flags:
  PRIMARY_MULTI        more than one visible blue `.btn.primary` on the screen
  PRIMARY_HOUSEKEEPING a blue primary whose label is housekeeping (Refresh, Save, Sync, Export ...)
  EMOJI                any emoji on screen
  GLYPH_ICON           a glyph standing in for an icon inside a button, link, tab or chip (› → ▾ ✓ ✎ ⋮ ×, "+ Add")
  TITLE_CASE           a button, tab, h1-h3, th, tile/kpi label or chip label that is not Title Case
  MONEY_WORD           the word "Money" in a label ("Accounting", never "Money")
  HEADING_NAV          the page heading does not match its nav entry (active sub-tab, else rail group)
  HIDDEN_TAB           a visible tab strip holding a tab whose box is 0x0 while its siblings show (in the page,
                       but nobody can see or click it)
  PHONE_HSCROLL        phone: the document scrolls sideways
  PHONE_OFFSCREEN      phone: an element's right edge passes the viewport (outside a horizontal scroller)
  CLIPPED_TEXT         phone: overflow hidden/clip cuts an element's own text (scrollWidth > clientWidth+1)
  TAP_SPACING          phone: two tap targets closer than 8px (inline links inside sentences ignored)
  INPUT_LABEL_OVERLAP  an input/select/textarea box overlaps its own label's text
  SVG_SIZE             an svg rendered larger than 64px that is not a chart/illustration
  ONE_CLOCK            "as of" + a wall-clock time, or the machine's real date on screen, or a "today/now/live"
                       claim next to a date that is not the app day (2026-09-03)
  PAGE_ERROR / CONSOLE_ERROR
Horizontal scrollers on phone are not flags; their count is printed as INFO lines.

Usage: python3 lint.py [--rule R[,R]] [--user u[,u]] [--view v[,v]] [--phone|--desktop] [--json path] [--quiet]
Output: one line per flag `RULE | viewport | user | view | detail`, a summary by rule, then `N flags`. Exit 1 if N > 0.
Chrome (rail, top bar, sub-tabs, phone tab bar) is shared by every view, so a chrome flag is reported once per
user and viewport with view `(chrome)`."""
import asyncio, re, sys, json, time, datetime, argparse
from collections import Counter, defaultdict
from harness import *

HOUSEKEEPING = ['Refresh', 'Reload', 'Save', 'Filter', 'Export', 'Download', 'Settings', 'Sync', 'Connect',
                'Close', 'Cancel', 'Clear', 'Reset', 'Read', 'Mark Read', 'Print', 'Edit', 'Delete', 'Remove',
                'Archive', 'Dismiss', 'Hide', 'Show', 'Sort', 'Copy', 'Duplicate', 'Back', 'Configure',
                'Customize', 'Manage', 'Preferences', 'Columns', 'View All', 'See All', 'Open Settings']
SMALL = {'a', 'an', 'the', 'and', 'or', 'but', 'of', 'to', 'in', 'on', 'at', 'by', 'for', 'with', 'from', 'as',
         'per', 'vs', 'vs.', 'via', 'into', 'nor'}
# Units and abbreviations that stay lowercase in a label ("Area (sq ft)"); CLAUDE.md: never Title Case a unit.
UNITS = {'sq', 'ft', 'sf', 'lf', 'in', 'hr', 'hrs', 'h', 'min', 'mo', 'yr', 'ea', 'pcs', 'lbs', 'lb', 'x', 'pct',
         'e.g.', 'i.e.', 'etc.', 'am', 'pm', 'k', 'm', 'w', 'd'}
CHARTS = ['.gantt', '.gantt-wrap', '.spark', '.chart', '[class*="chart"]', '[class*="spark"]', '[class*="gantt"]',
          '.hb-empty-art', '[class*="illus"]', '[class*="-art"]', '.hero', '.f-hero', '[class*="plan"]',
          '[class*="map"]', '[class*="markup"]', '[class*="photo"]', '[class*="sig"]', '[role="img"]']

COLLECT = r"""
(args) => {
  const {SMALL, UNITS, HOUSEKEEPING, NAMES, DATA, CHARTS, PHONE, WALL} = args;
  const small = new Set(SMALL), units = new Set(UNITS);
  const W = innerWidth, H = innerHeight;
  const flags = [];
  const view = document.querySelector('.view.on');
  const flag = (rule, el, detail, key) => flags.push({rule, detail, key: key || detail, chrome: !!(el && view && !view.contains(el) && !(el.closest && el.closest('.modal,.drawer,.sheet,.overlay')))});
  const cs = el => getComputedStyle(el);
  const vis = el => {
    if (!el || !el.getBoundingClientRect) return false;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const s = cs(el);
    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0) return false;
    if (el.closest('[aria-hidden="true"]') && el.tagName !== 'svg') return false;
    if (el.closest('.toast')) return false;
    // The body of a closed <details> is not rendered, but Chromium still reports a layout box and a visible
    // computed style for it; its buttons were read as on-screen taps (false positive, 2026-10-08).
    const det = el.closest('details:not([open])');
    if (det && !el.closest('summary') && el !== det) return false;
    return true;
  };
  const sel = el => {
    const parts = [];
    for (let x = el, i = 0; x && x !== document.body && i < 3; x = x.parentElement, i++) {
      let s = x.tagName.toLowerCase();
      if (x.id) { s += '#' + x.id; parts.unshift(s); break; }
      const c = (typeof x.className === 'string' ? x.className : '').trim().split(/\s+/).filter(Boolean).slice(0, 2);
      if (c.length) s += '.' + c.join('.');
      parts.unshift(s);
    }
    return parts.join(' > ');
  };
  // Source text: the text nodes the person sees, before any CSS text-transform. Count badges (.n, numeric-only
  // spans), kbd hints and svg are left out.
  const isBadge = e => e.matches('.n, .badge, .cnt, .count, kbd, svg, .sr-only, .visually-hidden') ||
                       (e.children.length === 0 && /^\s*\d+\+?\s*$/.test(e.textContent) && e.tagName !== 'B');
  const srcText = el => {
    let out = '';
    const walk = n => {
      for (const c of n.childNodes) {
        if (c.nodeType === 3) out += c.data;
        else if (c.nodeType === 1) {
          if (isBadge(c)) { out += ' '; continue; }
          const s = cs(c);
          if (s.display === 'none' || s.visibility === 'hidden') continue;
          const blk = /^(block|flex|grid|table|list-item)/.test(s.display);
          if (blk) out += ' ';
          walk(c);
          if (blk || c.tagName === 'BR') out += ' ';
        }
      }
    };
    walk(el);
    return out.replace(/\s+/g, ' ').trim();
  };
  const ownText = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.data).join('').replace(/\s+/g, ' ').trim();

  const all = [...document.querySelectorAll('body *')];
  const shown = all.filter(e => !(e.closest('svg') && e.tagName !== 'svg') && vis(e));
  const shownSet = new Set(shown);

  // ---------- primary buttons ----------
  const prim = shown.filter(e => e.matches('.btn.primary'));
  if (prim.length > 1) flag('PRIMARY_MULTI', view, `${prim.length} blue primaries: ` + prim.map(p => `"${srcText(p).slice(0, 30)}"`).join(', '));
  const hk = new RegExp('^(?:' + HOUSEKEEPING.join('|') + ')\\b', 'i');
  for (const p of prim) {
    const t = srcText(p);
    if (hk.test(t) || /\b(settings|mark (all )?read|refresh|sync)\b/i.test(t)) flag('PRIMARY_HOUSEKEEPING', p, `"${t.slice(0, 40)}" (${sel(p)})`);
  }

  // ---------- emoji and glyphs ----------
  const EMOJI = /(?![©®™])[\p{Extended_Pictographic}\u{1F1E6}-\u{1F1FF}️]/u;
  const GLYPH = /[›‹»«→←↑↓↗↘↔⇢⇒⟶➔➜▾▸▴◂▼▲►◄▶◀✓✔✗✘✎✏⋮⋯✕✖×☰★☆●○◉•◦⌄⌃↻⟳⤓⤴⧉☐☑]/;
  const seenEmoji = new Set();
  for (const e of shown) {
    if (e.matches('script,style,svg')) continue;
    const t = ownText(e);
    if (!t) continue;
    const m = t.match(EMOJI);
    if (m && !seenEmoji.has(t)) { seenEmoji.add(t); flag('EMOJI', e, `"${m[0]}" in "${t.slice(0, 50)}" (${sel(e)})`); }
  }
  const CTRL = 'button, a, [role="tab"], [role="button"], .btn, .tab, .chip, [class*="chip"] > *, .sub-tabs > *, .seg > *, button.pill, a.pill';
  const glyphSeen = new Set();
  for (const e of shown.filter(e => e.matches(CTRL))) {
    if (e.closest('#crumbs') && e.tagName !== 'A') continue;
    const t = srcText(e);
    let m = t.match(GLYPH);
    let what = m && m[0];
    // "×" between numbers is multiplication data (2×4), not a close glyph
    if (what === '×' && /\d\s*×\s*\d/.test(t)) what = null;
    if (!what && /^\+\s?[A-Za-z]/.test(t)) what = '+';
    if (!what) continue;
    const key = sel(e) + t;
    if (glyphSeen.has(key)) continue; glyphSeen.add(key);
    flag('GLYPH_ICON', e, `"${what}" in "${t.slice(0, 50)}" (${sel(e)})`);
  }

  // ---------- Title Case ----------
  // Names from DB are data: replace each whole-word occurrence with a capitalised placeholder before judging.
  const esc = x => x.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const nameRes = NAMES.map(n => [n, new RegExp('(^|[^A-Za-z])' + esc(n) + '(?![A-Za-z])', 'g')]);
  const stripNames = t => { let s = t; for (const [n, re] of nameRes) if (s.includes(n)) s = s.replace(re, '$1Name'); return s; };
  const dataSet = new Set(DATA);
  const longData = DATA.filter(d => d.length >= 12);
  const isData = t => /[\d$@#%]|[A-Z]{2,}-\d/.test(t) || dataSet.has(t) || longData.some(d => t.includes(d));
  const tcCheck = (t) => {
    // returns the offending word or null
    let s = stripNames(t);
    s = s.replace(/\([^)]*\)/g, m => /[a-z]/.test(m) && !/\d/.test(m) ? m : ' ');  // keep word-only parentheticals
    const segs = s.split(/\s*(?:[·:—–|\/•]|\s-\s|\.\s)\s*/).filter(x => x && /[A-Za-z]/.test(x));
    for (const seg of segs) {
      const words = seg.split(/\s+/).filter(Boolean);
      for (let i = 0; i < words.length; i++) {
        let w = words[i].replace(/^[("'“‘\[]+|[)"'”’\],;:!?…]+$/g, '');
        if (!w || !/[A-Za-z]/.test(w)) continue;
        if (/[\d$@#%&+=<>]/.test(w)) continue;
        const head = w.split('-')[0];                          // judge a hyphenated word by its first part
        const lw = w.toLowerCase();
        if (/^[a-z]+[A-Z]/.test(w)) continue;                   // iPhone, eSign: brand casing
        if (units.has(lw) && i > 0) continue;
        const first = i === 0, last = i === words.length - 1;
        if (small.has(lw) && !first && !last) { if (w !== lw && !/^[A-Z]{2,}$/.test(w)) return {bad: w, why: 'small word capitalised'}; continue; }
        if (/^[a-z]/.test(head)) return {bad: w, why: 'lowercase'};
      }
    }
    return null;
  };
  const labelSeen = new Set();
  const checkLabel = (e, kind) => {
    let t = srcText(e);
    if (!t || t.length > 70) return;
    if (/\bmoney\b/i.test(t)) flag('MONEY_WORD', e, `${kind} "${t.slice(0, 50)}" (${sel(e)})`);
    if (!/[A-Za-z]/.test(t) || (kind === 'th' ? /[\d$@#%]/.test(t) : isData(t))) return;   // digits, $, @, ids, or a value stored in DB (a th is always a label)
    if (/\?$/.test(t) || (/[.!]$/.test(t) && t.split(' ').length > 3)) return;   // a question or sentence, not a label
    if (t.split(' ').length > 9) return;
    const key = kind + '|' + t;
    if (labelSeen.has(key)) return;
    const bad = tcCheck(t);
    if (bad) { labelSeen.add(key); flag('TITLE_CASE', e, `${kind} "${t.slice(0, 60)}" (${bad.why}: "${bad.bad}") (${sel(e)})`); }
  };
  const LABEL_SETS = [
    ['button', 'button, .btn, [role="button"]'],
    ['tab', '[role="tab"], .sub-tabs > *, .seg > *, .tabs > *, .ctabs > *, .tab'],
    ['heading', 'h1, h2, h3'],
    ['th', 'th'],
    ['chip', '.chip, .ops-chip, .st-chip, [class*="chips"] > button, [class*="chips"] > a, button.pill, a.pill'],
  ];
  const done = new Set();
  const TILES = '.kpi, .dx-tile, .gl, .tile, .ov-tiles > *, .dtiles > *, .fd-tiles > *';
  for (const [kind, q] of LABEL_SETS) for (const e of shown.filter(x => x.matches(q))) {
    if (done.has(e) || e.matches(TILES)) continue; done.add(e);
    if (e.closest('#crumbs, .rolesel, select, .cmdk, .pa-answer, .msg, .bubble')) continue;
    if (kind === 'button' && e.closest('td') && e.matches('.link, a')) continue;
    if (kind === 'button' && srcText(e).split(' ').length > 6) continue;  // a card-like button holding a record
    checkLabel(e, kind);
  }
  // tile/kpi labels: the caption child of a KPI tile (.kpi > span, .dx-tile > span, .gl > .gl-k). The value
  // (b, .gl-v) is data and the sub-line (.gl-s) is a sentence describing the value.
  for (const tile of shown.filter(x => x.matches(TILES))) {
    const kids = [...tile.children].filter(k => shownSet.has(k) && !k.matches('button, a, svg, .btn, b, strong, .gl-v, .gl-s, .gl-chev, .sub, .small'));
    // only the first caption is the label; a later one is a note on the value ("safe-to-spend is already negative")
    const k = kids.find(k => srcText(k));
    if (k && !done.has(k)) { done.add(k); checkLabel(k, 'tile'); }
  }

  // ---------- tabs that cannot be seen or clicked ----------
  // A visible tab strip holding a tab whose box is 0x0 while its siblings show: the tab is in the page but a
  // person can neither see nor click it (the Reports group tabs were left at 0x0 behind a select).
  const STRIP = '[role="tablist"], .ctabs, .sub-tabs, .seg, .tabs, .hb-tabs, .hb-subtabs, .rep-groups, .rep-sub';
  const stripSeen = new Set();
  for (const s of shown.filter(e => e.matches(STRIP))) {
    const kids = [...s.children].filter(k => k.matches('button, a, [role="tab"]'));
    if (kids.length < 2) continue;
    const on = kids.filter(k => shownSet.has(k));
    const dead = kids.filter(k => { const r = k.getBoundingClientRect(); return r.width < 1 && r.height < 1; });
    if (!on.length || !dead.length) continue;
    const key = sel(s) + '|' + dead.map(k => srcText(k)).join(',');
    if (stripSeen.has(key)) continue; stripSeen.add(key);
    flag('HIDDEN_TAB', s, `${dead.length} of ${kids.length} tabs at 0x0: ${dead.map(k => '"' + (srcText(k) || k.textContent.trim()).slice(0, 20) + '"').join(', ')} (${sel(s)})`, key);
  }

  // ---------- heading vs nav ----------
  const norm = s => (s || '').replace(/\d+\+?\s*$/, '').replace(/&/g, 'and').replace(/\s+/g, ' ').trim().toLowerCase();
  const tabOn = document.querySelector('#subnav .sub-tabs button.on, #subnav .sub-tabs .on');
  const grpOn = document.querySelector('#nav-groups button.on');
  const tabL = tabOn && vis(tabOn) ? srcText(tabOn) : '';
  // the group: the rail on desktop; the phone tab bars (#mtabs, the foreman's #tabbar) on phone
  const grpEls = [grpOn, ...document.querySelectorAll('#mtabs .on, #tabbar .on, .mtabs .on')].filter(Boolean);
  const grpL = (grpEls.find(vis) ? srcText(grpEls.find(vis)) : '') || (grpOn ? (grpOn.textContent || '').replace(/\d+\s*$/, '').trim() : '');
  let hEl = view && ([...view.querySelectorAll('h1')].find(vis) || [...view.querySelectorAll('h2')].find(vis));
  const heading = hEl ? srcText(hEl) : '';
  const navL = tabL || grpL;
  // "Selections — 45 Cranberry St" matches "Selections": the nav label plus a record suffix after a dash or dot
  const okHead = heading && [tabL, grpL].filter(Boolean).some(l => norm(l) === norm(heading) || norm(heading).startsWith(norm(l) + ' — ') || norm(heading).startsWith(norm(l) + ' · '));
  if (!heading) flag('HEADING_NAV', view, `no h1/h2 heading; nav reads "${navL}"`);
  else if (!okHead && !navL) flag('HEADING_NAV', view, `heading "${heading.slice(0, 50)}" has no active nav entry (no rail, tab-bar or sub-tab item is on)`);
  else if (!okHead && !tabL && document.querySelector('#subnav .sub-tabs') && vis(document.querySelector('#subnav .sub-tabs'))) flag('HEADING_NAV', view, `heading "${heading.slice(0, 50)}" has no active sub-tab (group "${grpL}")`);
  else if (!okHead) flag('HEADING_NAV', view, `heading "${heading.slice(0, 50)}" vs nav "${navL}"${tabL && grpL ? ' (group "' + grpL + '")' : ''} (${hEl.tagName.toLowerCase()} ${sel(hEl)})`);

  // ---------- phone layout ----------
  const info = {};
  if (PHONE) {
    const over = document.documentElement.scrollWidth - W;
    if (over > 1) flag('PHONE_HSCROLL', view, `document scrollWidth ${document.documentElement.scrollWidth} > ${W} (+${over}px)`);
    const scrollers = new Set();
    const clipAnc = e => {
      for (let x = e.parentElement; x && x !== document.body; x = x.parentElement) {
        const s = cs(x);
        if (/(auto|scroll)/.test(s.overflowX) && x.scrollWidth > x.clientWidth + 1) return {kind: 'scroller', el: x};
        if (/(hidden|clip)/.test(s.overflowX)) { const r = x.getBoundingClientRect(); if (r.right <= W + 1) return {kind: 'clip', el: x}; }
        if (s.position === 'fixed') { const r = x.getBoundingClientRect(); if (r.left >= W - 1 || r.right <= 1) return {kind: 'parked', el: x}; }
      }
      return null;
    };
    const offenders = new Set();
    for (const e of shown) {
      const r = e.getBoundingClientRect();
      if (r.right <= W + 1) continue;
      const s = cs(e);
      if (s.position === 'fixed' && (r.left >= W - 1)) continue;   // a drawer parked off screen
      const a = clipAnc(e);
      if (a && a.kind === 'scroller') { scrollers.add(a.el); continue; }
      if (a) continue;
      if (e.parentElement && offenders.has(e.parentElement)) { offenders.add(e); continue; }
      offenders.add(e);
      flag('PHONE_OFFSCREEN', e, `right edge ${Math.round(r.right)}px > ${W} "${srcText(e).slice(0, 30)}" (${sel(e)})`);
    }
    info.scrollers = [...scrollers].map(sel);

    // clipped text: overflow hidden/clip cutting the element's own text
    const clipSeen = new Set();
    for (const e of shown) {
      if (e.matches('svg, img, input, select, textarea, canvas, video')) continue;
      const s = cs(e);
      if (!/(hidden|clip)/.test(s.overflowX) && !/(hidden|clip)/.test(s.overflow)) continue;
      if (e.scrollWidth <= e.clientWidth + 1) continue;
      // text-level content only: its own text, or children that are all inline (a button holding a <span>)
      const leaf = ownText(e) || ([...e.children].length && [...e.children].every(k => /^inline/.test(cs(k).display) || k.tagName === 'svg'));
      if (!leaf) continue;
      const t = srcText(e);
      if (!t) continue;
      const ctrl = e.matches('button, .btn, [role="tab"], th, h1, h2, h3, label, .chip, .pill') || !!e.closest('.btn, [role="tab"], .sub-tabs, .seg, .chip');   // not a card-like <button> holding a record
      // A data value cut with a visible ellipsis (file names, captions, previews) is deliberate truncation and
      // only counted; a label cut at all, or any text cut with no ellipsis ("Need Somethin"), is a flag.
      if (s.textOverflow === 'ellipsis' && !ctrl) { info.ellipsis = (info.ellipsis || 0) + 1; continue; }
      const key = sel(e) + '|' + t;
      if (clipSeen.has(key)) continue; clipSeen.add(key);
      flag('CLIPPED_TEXT', e, `"${t.slice(0, 40)}" shows ${e.clientWidth}px of ${e.scrollWidth}px${s.textOverflow === 'ellipsis' ? ' (ellipsis on a label)' : ''} (${sel(e)})`, `${sel(e)}|${t}`);
    }

    // tap targets closer than 8px
    const TAP = 'button, a[href], a[onclick], a[data-v], input:not([type="hidden"]), select, textarea, [role="button"], [role="tab"]';
    const inSentence = e => {
      if (e.tagName !== 'A' || cs(e).display !== 'inline') return false;
      const p = e.parentElement; if (!p) return false;
      const pt = (p.textContent || '').replace(/\s+/g, ' ').trim(), lt = (e.textContent || '').trim();
      return pt.length > lt.length + 8;
    };
    // A target's tappable box is the part its scrolling or clipping ancestors show. A tab scrolled under the
    // edge of a horizontal tab strip (or under the strip's "More" button) cannot be tapped there; measuring
    // its full box reported 0px between it and the "More" beside the strip (false positive, 2026-10-08).
    const clipRect = e => {
      let l, t, r, b; ({left: l, top: t, right: r, bottom: b} = e.getBoundingClientRect());
      for (let x = e.parentElement; x && x !== document.body; x = x.parentElement) {
        const s = cs(x);
        if (s.overflowX === 'visible' && s.overflowY === 'visible') continue;
        const c = x.getBoundingClientRect();
        if (s.overflowX !== 'visible') { l = Math.max(l, c.left); r = Math.min(r, c.right); }
        if (s.overflowY !== 'visible') { t = Math.max(t, c.top); b = Math.min(b, c.bottom); }
        if (s.position === 'fixed') break;
      }
      return {left: l, top: t, right: r, bottom: b, width: r - l, height: b - t};
    };
    const taps = shown.filter(e => e.matches(TAP) && !e.closest('#nav, .rail') && !inSentence(e) && !(e.tagName === 'INPUT' && /^(checkbox|radio)$/.test(e.type) && e.closest('label')))
      .map(e => { let layer = null; for (let x = e; x && x !== document.body; x = x.parentElement) { const p = cs(x).position; if (p === 'fixed' || p === 'sticky') { layer = x; break; } } return {e, r: clipRect(e), layer}; })
      .filter(o => o.r.width >= 1 && o.r.height >= 1 && o.r.right > 0 && o.r.left < W);
    taps.sort((a, b) => a.r.top - b.r.top);
    const pairSeen = new Set();
    for (let i = 0; i < taps.length; i++) {
      const A = taps[i];
      for (let j = i + 1; j < taps.length; j++) {
        const B = taps[j];
        if (B.r.top > A.r.bottom + 8) break;
        if (A.e.contains(B.e) || B.e.contains(A.e)) continue;
        if (A.layer !== B.layer) continue;   // a fixed bar over scrolling content is not a spacing fault
        const dx = Math.max(0, B.r.left - A.r.right, A.r.left - B.r.right);
        const dy = Math.max(0, B.r.top - A.r.bottom, A.r.top - B.r.bottom);
        const gap = Math.max(dx, dy);
        if (gap >= 8) continue;
        // Policy (2026-10-08): the segments of ONE segmented control or tab bar are one control, as on iOS,
        // provided each segment is at least 40px tall. Separate controls still need 8px.
        const SEG = '.seg, .ctabs, .sub-tabs, nav#mtabs, nav#tabbar, [role="tablist"]';
        const sa = A.e.closest(SEG), sb = B.e.closest(SEG);
        if (sa && sa === sb && A.r.height >= 40 && B.r.height >= 40) continue;
        // a label wrapping its own control, or the two halves of one segmented control, are judged by container
        const box = A.e.parentElement === B.e.parentElement ? sel(A.e.parentElement) : sel(A.e) + ' ~ ' + sel(B.e);
        const key = box + '|' + gap;
        if (pairSeen.has(key)) continue; pairSeen.add(key);
        flag('TAP_SPACING', A.e, `${Math.round(gap)}px between "${srcText(A.e).slice(0, 20) || A.e.tagName.toLowerCase()}" and "${srcText(B.e).slice(0, 20) || B.e.tagName.toLowerCase()}" (${box})`, `${box}|${Math.round(gap)}`);
      }
    }
  }

  // ---------- inputs over their own label ----------
  for (const inp of shown.filter(e => e.matches('input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]), select, textarea'))) {
    let lab = inp.id ? document.querySelector(`label[for="${CSS.escape(inp.id)}"]`) : null;
    if (!lab) lab = inp.closest('label');
    if (!lab && inp.previousElementSibling && inp.previousElementSibling.tagName === 'LABEL') lab = inp.previousElementSibling;
    if (!lab || !shownSet.has(lab)) continue;
    const ri = inp.getBoundingClientRect();
    for (const n of [...lab.childNodes].filter(n => n.nodeType === 3 && n.data.trim())) {
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const rt of rg.getClientRects()) {
        const ox = Math.min(ri.right, rt.right) - Math.max(ri.left, rt.left), oy = Math.min(ri.bottom, rt.bottom) - Math.max(ri.top, rt.top);
        if (ox > 1 && oy > 1) { flag('INPUT_LABEL_OVERLAP', inp, `"${n.data.trim().slice(0, 30)}" under its ${inp.tagName.toLowerCase()} by ${Math.round(ox)}x${Math.round(oy)}px (${sel(inp)})`); break; }
      }
    }
  }

  // ---------- svg size ----------
  const chartQ = CHARTS.join(',');
  const allowed = {};
  const svgSeen = {};
  for (const s of shown.filter(e => e.tagName === 'svg')) {
    const r = s.getBoundingClientRect();
    if (r.width <= 64 && r.height <= 64) continue;
    const ill = s.closest(chartQ) || (s.matches(chartQ) ? s : null);
    // a data graphic carries its own geometry (axes, bars, many paths); an icon is a handful of strokes in a 24 box
    const vb = (s.getAttribute('viewBox') || '').split(/[\s,]+/).map(Number);
    const iconBox = vb.length === 4 && vb[2] <= 32 && vb[3] <= 32;
    if (ill && !iconBox) { const k = (typeof ill.className === 'string' ? ill.className : ill.className.baseVal || '').split(/\s+/)[0] || ill.tagName; allowed[k] = (allowed[k] || 0) + 1; continue; }
    if (!iconBox && s.querySelectorAll('*').length > 12) { allowed['(data graphic)'] = (allowed['(data graphic)'] || 0) + 1; continue; }
    const k = `${Math.round(r.width)}x${Math.round(r.height)} viewBox "${s.getAttribute('viewBox') || ''}" (${sel(s)})`;
    if (svgSeen[k]) { svgSeen[k].n++; continue; }
    svgSeen[k] = {n: 1, s};
  }
  for (const [k, o] of Object.entries(svgSeen)) flag('SVG_SIZE', o.s, k + (o.n > 1 ? ` x${o.n}` : ''));
  info.svgAllowed = allowed;

  // ---------- one clock ----------
  const scope = [view, document.querySelector('.topbar'), document.querySelector('#subnav')].filter(Boolean);
  const txt = scope.map(e => e.innerText || '').join('\n');
  let m;
  const asOf = /\bas of\s+(\d{1,2}:\d{2}\s*(?:[ap]\.?m\.?)?)/gi;
  while ((m = asOf.exec(txt))) flag('ONE_CLOCK', view, `"${txt.slice(Math.max(0, m.index - 20), m.index + m[0].length + 10).replace(/\s+/g, ' ')}" (wall-clock time)`);
  for (const w of WALL) { const i = txt.indexOf(w); if (i >= 0) flag('ONE_CLOCK', view, `real-clock date "${w}" on screen: "${txt.slice(Math.max(0, i - 30), i + w.length + 10).replace(/\s+/g, ' ')}"`); }
  const MON = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec';
  const claim = new RegExp(`\\b(today|now|live|as of)\\b[^\\n.]{0,12}?\\b((?:${MON})[a-z]*\\.? \\d{1,2}(?:, \\d{4})?|\\d{4}-\\d{2}-\\d{2}|\\d{1,2}/\\d{1,2}/\\d{2,4})`, 'gi');
  while ((m = claim.exec(txt))) {
    const d = m[2];
    if (/^(Sep|Sept)[a-z]*\.? 3\b|^2026-09-03$|^0?9\/0?3\b/i.test(d)) continue;
    flag('ONE_CLOCK', view, `"${m[0].replace(/\s+/g, ' ')}" claims now/today with a date that is not the app day`);
  }
  return {flags, info, heading, navL};
}
"""

NAMES_JS = r"""
() => {
  const keys = new Set(['name', 'n', 'address', 'addr', 'company', 'vendor', 'client', 'who', 'fullName', 'first', 'last', 'short', 'display', 'title_name', 'org', 'firm', 'contact', 'person', 'payee', 'merchant', 'nick', 'label_name', 'property', 'street']);
  const out = new Set();
  const seen = new Set();
  const walk = (o, d) => {
    if (!o || typeof o !== 'object' || seen.has(o) || d > 6) return; seen.add(o);
    if (Array.isArray(o)) { o.forEach(x => walk(x, d + 1)); return; }
    for (const [k, v] of Object.entries(o)) {
      if (typeof v === 'string') { if (keys.has(k) && v.length >= 2 && v.length <= 60 && /[A-Z]/.test(v)) out.add(v.trim()); }
      else walk(v, d + 1);
    }
  };
  for (const k of ['clients', 'projects', 'vendors', 'users', 'employees', 'properties', 'deals', 'investors', 'partners', 'leads', 'entities', 'accounts', 'cards', 'hub', 'principals', 'company', 'studio']) walk(DB[k], 0);
  // first names / surnames alone ("Chen", "Angel") also appear in labels such as "Chen's Queue"
  for (const v of [...out]) if (/^[A-Z][a-z]+( [A-Z][a-z]+)+$/.test(v) && v.split(' ').length <= 3) v.split(' ').forEach(p => p.length > 2 && out.add(p));
  // Every other string value stored in DB (photo captions, task titles, material names, statuses) is a record
  // value: a label that equals one, or contains a long one, is data and not judged for Title Case.
  const data = new Set(); const seen2 = new Set();
  const walk2 = (o, d) => {
    if (!o || typeof o !== 'object' || seen2.has(o) || d > 7) return; seen2.add(o);
    for (const v of Array.isArray(o) ? o : Object.values(o)) {
      if (typeof v === 'string') { const t = v.replace(/\s+/g, ' ').trim(); if (t.length >= 3 && t.length <= 90 && / /.test(t) && !/[<>{}]/.test(t)) data.add(t); }
      else walk2(v, d + 1);
    }
  };
  walk2(DB, 0);
  return {names: [...out].sort((a, b) => b.length - a.length), data: [...data]};
}
"""


def wall_dates():
    d = datetime.date.today()
    if d.isoformat() == '2026-09-03': return []
    mon = d.strftime('%b')
    return [d.isoformat(), f'{mon} {d.day}, {d.year}', f'{d.month}/{d.day}/{d.year}', f'{d.strftime("%B")} {d.day}, {d.year}']


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rule'); ap.add_argument('--user'); ap.add_argument('--view')
    ap.add_argument('--phone', action='store_true'); ap.add_argument('--desktop', action='store_true')
    ap.add_argument('--json'); ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    rules = set(a.rule.upper().split(',')) if a.rule else None
    users = a.user.split(',') if a.user else USERS
    only_views = set(a.view.split(',')) if a.view else None
    vps = [False, True]
    if a.phone and not a.desktop: vps = [True]
    if a.desktop and not a.phone: vps = [False]
    t0 = time.time()
    flags, infos = [], []
    seen_chrome = set()
    svg_allowed = Counter()
    nviews = 0
    n_ellipsis = 0
    async with async_playwright() as p:
        for phone in vps:
            vp = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            nd = await pg.evaluate(NAMES_JS)
            args = {'SMALL': sorted(SMALL), 'UNITS': sorted(UNITS), 'HOUSEKEEPING': HOUSEKEEPING, 'NAMES': nd['names'], 'DATA': nd['data'],
                    'CHARTS': CHARTS, 'PHONE': phone, 'WALL': wall_dates()}
            for u in users:
                await sign_in(pg, u)
                views = await pg.evaluate("() => (ROLE_VIEWS[role()] || []).slice()")
                for v in views:
                    if only_views and v not in only_views: continue
                    nviews += 1
                    del errs[:]
                    try:
                        await go(pg, v)
                        await pg.evaluate("() => { document.querySelectorAll('.toast.on').forEach(t => t.classList.remove('on')); scrollTo(0, 0); }")
                        r = await pg.evaluate(COLLECT, args)
                    except Exception as e:
                        errs.append('lint: ' + str(e).splitlines()[0])
                        r = {'flags': [], 'info': {}}
                    for e in errs:
                        rule = 'CONSOLE_ERROR' if e.startswith('console: ') else 'PAGE_ERROR'
                        r['flags'].append({'rule': rule, 'detail': e[:200], 'chrome': False})
                    for f in r['flags']:
                        if rules and f['rule'] not in rules: continue
                        vv = v
                        if f.get('chrome'):
                            k = (f['rule'], vp, u, f.get('key') or f['detail'])
                            if k in seen_chrome: continue
                            seen_chrome.add(k); vv = '(chrome)'
                        flags.append({'rule': f['rule'], 'viewport': vp, 'user': u, 'view': vv, 'detail': f['detail'], 'chrome': bool(f.get('chrome'))})
                    inf = r.get('info') or {}
                    for k, n in (inf.get('svgAllowed') or {}).items(): svg_allowed[k] += n
                    n_ellipsis += inf.get('ellipsis') or 0
                    if inf.get('scrollers'): infos.append((vp, u, v, inf['scrollers']))
            await b.close()
    for f in flags:
        if not a.quiet: print(f"{f['rule']} | {f['viewport']} | {f['user']} | {f['view']} | {f['detail']}")
    for vp, u, v, sc in infos:
        if not a.quiet and (not rules or 'PHONE_OFFSCREEN' in rules): print(f"INFO PHONE_SCROLLER | {vp} | {u} | {v} | {len(sc)} horizontal scroller(s): {', '.join(sc[:3])}")
    by = Counter(f['rule'] for f in flags)
    print('\nRule                    Flags')
    for k, n in sorted(by.items(), key=lambda x: -x[1]): print(f'{k:<24}{n:>5}')
    print(f"INFO: {len(infos)} phone screens hold horizontal scrollers ({sum(len(x[3]) for x in infos)} scrollers, not flagged)")
    print(f"INFO: {n_ellipsis} data values cut with a visible ellipsis on phone (deliberate truncation, not flagged)")
    print(f"INFO: svg over 64px allowed as charts/illustrations: {dict(svg_allowed)}")
    print(f"INFO: {nviews} screens in {time.time() - t0:.0f}s")
    if a.json:
        with open(a.json, 'w') as fh: json.dump({'flags': flags, 'scrollers': infos, 'svgAllowed': svg_allowed}, fh, indent=1)
    print(f'{len(flags)} flags')
    sys.exit(1 if flags else 0)

asyncio.run(main())
