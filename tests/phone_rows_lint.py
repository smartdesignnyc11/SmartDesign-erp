"""phone_rows_lint: every list the phone opens is a phone list (the mobile designer's review, 2026-10-25, "What would
make this a 9" item 1; lane phonerows).

For every role and every page in that role's menu (mnBuild: the phone bar, the menu's groups, More), opened the way
the menu opens it (mnGo), at 390x844 with touch, it flags:
  TABLE_WIDE      a <table> wider than the screen, or clipped by the box it sits in (a desktop table shrunk to 390)
  LV_CARDS        a label/value card list (cells that print their column name beside the value) showing fewer than
                  4 records on a screen
                  (or a card list: 3+ full-width sibling cards of one kind, each with its own controls, fewer than 4 a screen)
  LOW_DENSITY     any list of 4 or more rows (table rows or phone rows) whose rows are so tall that fewer than 4 fit
                  on a screen
  TITLE_SMALL     a row title under 13px
  TARGET_SMALL    a button, select, input, tab or chip under 44px tall (its label or hit area counts), or a row action
  PRIMARY_MULTI   more than one blue primary button on the page
A screen is the space between the header and the bottom bar. Inline links in sentences are not targets.

The pages the procurement lane is rebuilding (Buy Board, Purchasing, RFQs, Purchase Orders) and the Tasks page (the
taskfix lane) are listed in OWNED and reported as INFO, not flags, until those lanes merge; remove a page from OWNED
when its lane lands.

Usage: python3 phone_rows_lint.py [--user u_owner,...] [--view v,...] [--shots DIR] [--json PATH] [--quiet]
Exit 1 when anything is flagged.
"""
import asyncio, sys, json, argparse, os, re
from collections import Counter
from harness import *

ROLES = ['u_owner', 'u_alan', 'u_chen', 'u_billing', 'u_controller', 'u_sarah', 'u_angel', 'u_alberto', 'u_alex']
# pages another lane owns right now (CLAUDE.md lane rules): reported, not flagged
OWNED = {'proc': 'procurement P1', 'ovbuy': 'procurement P1', 'rfq': 'procurement P1', 'po': 'procurement P1',
         'tkall': 'taskfix'}

ENTRIES = r"""() => { const B = mnBuild(role()); if (!B) return [];
  const groups = B.field ? [{ id: 'field', items: B.bar.concat(B.rest, B.more) }] : B.groups.concat(B.more.length ? [{ id: 'more', items: B.more }] : []);
  const out = [], seen = new Set();
  groups.forEach(g => g.items.forEach(it => { const k = it.v + ':' + (it.tab || ''); if (seen.has(k)) return; seen.add(k); out.push({ g: g.id, v: it.v, tab: it.tab || '', l: it.l }); }));
  return out; }"""

OPEN = r"""([gid, v, tab]) => { const B = mnBuild(role());
  const groups = B.field ? [{ id: 'field', items: B.bar.concat(B.rest, B.more) }] : B.groups.concat(B.more.length ? [{ id: 'more', items: B.more }] : []);
  const g = groups.find(x => x.id === gid), it = g && g.items.find(i => i.v === v && (i.tab || '') === tab);
  if (typeof mbCloseModal === 'function') try { mbCloseModal(); } catch (e) {}
  if (it) mnGo(g, it); else { view = v; render(); }
  window.scrollTo(0, 0); return view; }"""

MEASURE = r"""() => {
  const W = innerWidth, H = innerHeight, v = document.querySelector('.view.on');
  if (!v) return { err: 'no page on screen' };
  const cs = (e, p) => getComputedStyle(e, p);
  const vis = e => { if (!e || !e.getBoundingClientRect) return false; const r = e.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return false;
    const s = cs(e); if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0) return false;
    if (e.closest('[hidden], .m-hide')) return false; return true; };
  const txt = e => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 48);
  const bar = [...document.querySelectorAll('#mtabs, #tabbar, .fm-tabs')].find(vis);
  const top = (() => { const t = [...document.querySelectorAll('#topbar, .topbar, header.tb')].find(vis); return t ? Math.max(0, t.getBoundingClientRect().bottom) : 56; })();
  const usable = (bar ? bar.getBoundingClientRect().top : H) - top;
  const out = { tables: [], lv: [], dense: [], small: [], targets: [], prim: [], usable: Math.round(usable) };
  // 1. tables wider than the screen or clipped by their box
  v.querySelectorAll('table').forEach(t => {
    if (!vis(t) || t.closest('.gantt-wrap, .gantt, [data-chart], .chart')) return;
    const r = t.getBoundingClientRect(); let L = 0, R = W;
    for (let a = t.parentElement; a && a !== document.body; a = a.parentElement) { const s = cs(a); if (s.overflowX !== 'visible') { const b = a.getBoundingClientRect(); L = Math.max(L, b.left); R = Math.min(R, b.right); } }
    if (r.right > R + 1 || r.left < L - 1 || r.width > W) out.tables.push(`${Math.round(r.width)}px in ${Math.round(R - L)}px: ` + txt(t.tHead || t.rows[0] || t));
  });
  // 2. label/value card lists and 3. lists too sparse for a phone
  const lvRow = tr => !!tr.cells && [...tr.cells].filter(td => { if (!vis(td)) return false; const c = cs(td, '::before').content; return c && c !== 'none' && c !== 'normal' && c !== '""'; }).length >= 2;
  const lists = [];
  v.querySelectorAll('table').forEach(t => { if (!vis(t)) return; const rows = [...t.querySelectorAll(':scope > tbody > tr')].filter(tr => vis(tr) && !tr.classList.contains('m-row-flat') && tr.cells.length > 1); if (rows.length) lists.push({ rows, t, name: txt(t.tHead || rows[0]) }); });
  const prs = new Map(); v.querySelectorAll('.pr-row').forEach(r => { if (!vis(r)) return; const p = r.parentElement; prs.has(p) || prs.set(p, []); prs.get(p).push(r); });
  prs.forEach((rows, p) => lists.push({ rows, t: p, name: txt(rows[0]) }));
  lists.forEach(({ rows, t, name }) => {
    const hs = rows.map(r => r.getBoundingClientRect().height), avg = hs.reduce((s, h) => s + h, 0) / hs.length, fit = Math.floor(usable / avg);
    const lv = rows.filter(lvRow).length, first = rows.filter(r => { const b = r.getBoundingClientRect(); return b.top >= top - 1 && b.bottom <= top + usable + 1; }).length;
    if (lv && first < Math.min(4, rows.length)) out.lv.push(`${first} of ${rows.length} on the first screen (${Math.round(avg)}px each): ${name}`);
    else if (!lv && rows.length >= 4 && fit < 4) out.dense.push(`${fit} of ${rows.length} per screen (${Math.round(avg)}px each): ${name}`);
  });
  // card lists: three or more full-width sibling cards of one kind, each holding a control (a record with its buttons),
  // fewer than four to a screen. Sections that group records are not records: the app declares them (PR_SECTIONS in
  // src/phonerows.js: a card on its own, a week of the look-ahead, a day of photos, a chain of checks).
  const SECTIONS = new Set(typeof PR_SECTIONS !== 'undefined' ? PR_SECTIONS : ['card']), NOT_RECORDS = { test: k => SECTIONS.has(k) };
  const parents = new Set(); v.querySelectorAll('*').forEach(e => { const p = e.parentElement; if (p && p.children.length >= 3 && p.tagName !== 'TBODY' && p.tagName !== 'TR') parents.add(p); });
  parents.forEach(p => { if (p.closest('table')) return; const by = {};
    [...p.children].forEach(c => { if (!vis(c) || typeof c.className !== 'string') return; const k = c.className.trim().split(/\s+/).filter(x => x !== 'card' && !/^(on|bad|warn|ok|info|late|sev\d)$/.test(x))[0]; if (!k || NOT_RECORDS.test(k) || /^pr-/.test(k)) return; (by[k] = by[k] || []).push(c); });
    Object.entries(by).forEach(([k, cs]) => { if (cs.length < 3) return; const rs = cs.map(c => c.getBoundingClientRect()); if (rs.some(r => r.width < W * 0.75)) return;
      if (!cs.every(c => c.querySelector('button, select, input'))) return;
      const avg = rs.reduce((s, r) => s + r.height, 0) / rs.length, fit = Math.floor(usable / avg);
      if (fit < Math.min(4, cs.length)) out.lv.push(`card list .${k}: ${fit} of ${cs.length} per screen (${Math.round(avg)}px each)`); }); });
  // 4. row titles
  v.querySelectorAll('.pr-t, td.m-title, .tk2-title').forEach(e => { if (!vis(e)) return; const f = parseFloat(cs(e).fontSize); if (f < 13) out.small.push(`${f}px: ${txt(e)}`); });
  // 5. targets: 44px tall, or held in a 44px label or hit area
  const T = 'button, a.btn, .btn, select, input:not([type=hidden]), [role=button], [role=tab], .chip';
  const seen = new Set();
  v.querySelectorAll(T).forEach(e => {
    if (!vis(e) || e.closest('.tk2-row, .gantt-wrap, .gantt, svg, .mbm, [data-chart]')) return;
    const r = e.getBoundingClientRect(); if (r.right < 0 || r.left > W) return;
    if (r.height >= 43.5) return;
    const hit = e.closest('label, .hit44, .pr-act, .pr-row');
    if (hit && hit !== e && hit.getBoundingClientRect().height >= 43.5 && (hit.matches('label, .hit44, .pr-act') || e.matches('input[type=checkbox], input[type=radio]'))) return;
    if (e.matches('input[type=checkbox], input[type=radio]')) { const p = e.parentElement; if (p && p.getBoundingClientRect().height >= 43.5) return; }
    const k = (e.tagName + ' ' + (e.className || '').toString().split(' ')[0] + ' ' + txt(e)).slice(0, 60);
    if (seen.has(k)) return; seen.add(k);
    out.targets.push(`${Math.round(r.width)}x${Math.round(r.height)} ${e.tagName.toLowerCase()}${e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).slice(0, 2).join('.') : ''} "${txt(e) || e.getAttribute('aria-label') || e.placeholder || ''}"`);
  });
  // 6. one blue primary (the screen lint's definition: blue on screen)
  const blue = e => { const c = cs(e).backgroundColor; return c && !/rgba?\(255, 255, 255|rgba\(0, 0, 0, 0\)|transparent/.test(c) && cs(e).color === 'rgb(255, 255, 255)'; };
  const prim = [...v.querySelectorAll('.btn.primary')].filter(e => vis(e) && blue(e));
  if (prim.length > 1) out.prim.push(`${prim.length} blue: ` + prim.map(e => '"' + txt(e).slice(0, 26) + '"').join(', '));
  out.sw = document.documentElement.scrollWidth;
  return out;
}"""

RULES = [('tables', 'TABLE_WIDE'), ('lv', 'LV_CARDS'), ('dense', 'LOW_DENSITY'), ('small', 'TITLE_SMALL'), ('targets', 'TARGET_SMALL'), ('prim', 'PRIMARY_MULTI')]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--user'); ap.add_argument('--view'); ap.add_argument('--shots'); ap.add_argument('--json'); ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    users = a.user.split(',') if a.user else ROLES
    only = set(a.view.split(',')) if a.view else None
    flags, info, pages = [], [], 0
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, True)
        for u in users:
            await sign_in(pg, u)
            entries = await pg.evaluate(ENTRIES)
            for e in entries:
                if only and e['v'] not in only: continue
                tag = e['v'] + (':' + e['tab'] if e['tab'] else '')
                if e['v'] in OWNED:
                    info.append(f"INFO | {u} | {tag} | owned by the {OWNED[e['v']]} lane"); continue
                try:
                    await pg.evaluate(OPEN, [e['g'], e['v'], e['tab']])
                    await pg.wait_for_timeout(260)
                    m = await pg.evaluate(MEASURE)
                except Exception as ex:
                    flags.append(('PAGE_ERROR', u, tag, str(ex)[:160])); continue
                pages += 1
                if a.shots:
                    os.makedirs(a.shots, exist_ok=True)
                    await pg.screenshot(path=os.path.join(a.shots, f"{u}_{tag.replace(':', '-')}.png"))
                if m.get('err'): flags.append(('PAGE_ERROR', u, tag, m['err'])); continue
                for key, rule in RULES:
                    for d in m[key]: flags.append((rule, u, tag, d))
                if m['sw'] > 390: flags.append(('HSCROLL', u, tag, f"the page is {m['sw']}px wide"))
            await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} }")
        for x in errs[:5]: flags.append(('PAGE_ERROR', '-', '-', x[:160]))
        await b.close()
    if not a.quiet:
        for x in info: print(x)
    for f in flags: print(' | '.join(f))
    c = Counter(f[0] for f in flags)
    print('By rule:', ', '.join(f'{k} {n}' for k, n in sorted(c.items())) or 'none')
    pc = Counter((f[1], f[2]) for f in flags)
    print(f'{len(pc)} of {pages} pages flagged')
    if a.json:
        with open(a.json, 'w') as fh: json.dump({'flags': flags, 'pages': pages}, fh, indent=1)
    print(f'{len(flags)} flags ({pages} pages, {len(users)} roles)')
    return 1 if flags else 0

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
