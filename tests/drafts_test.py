"""drafts_test: what a person types in a sheet is never lost (wave 1, Trust; docs/PATH_TO_9.md, src/w1trust.js D1).

Pilot 2: the PM's Answer sheet lost its text twice, the foreman's crew-hours Fix sheet lost the typed In time when he
moved pages, the owner's half-filled New Lead vanished between turns, the coordinator's Payment Terms sheet and the
controller's open import went silently, the designer's Make It a Task sheet was gone when she came back.

The walk. For every role (harness.USERS), desktop 1440 and phone 390, every page in the role's menu is opened and every
control a person can press on it (a button, a row, a card; one of each kind per page) is pressed from a fresh state.
Each press that opens a sheet with a field that takes typing is a sheet; each sheet is counted once per role and
device. Then, for every sheet found:
  1. it is opened as the person would, a line is typed in its first text field,
  2. the person leaves it, each sheet a different way in turn: a tap on another menu entry, Escape, a tap outside the
     sheet, the browser's Back (another menu entry when there is no screen to go back to),
  3. the sheet has closed (it never stays over the next screen) and says the draft was kept,
  4. the person comes back to the page and opens the same sheet again: the typed line is there, with Discard Draft.
For the first sheet of each role and device, Discard Draft asks first and then empties the field; and a reload with
the sheet open brings it back open, with the line. The pilot's named sheets are walked by name as well when the menu
walk did not reach them (the Answer sheet, the crew Fix sheet, Make It a Task from a mail, the bill entry, a page
form's field on the estimate).

  python3 drafts_test.py [--user u_owner] [--phone|--desktop] [--max N]   (N: sheets per role and device, default all)
Last line: `DRAFTS ok/total sheets kept their text (desktop x, phone y)`. Exit 1 on any failure.
"""
import asyncio, json, os, re, sys, time, argparse
from collections import Counter, defaultdict
from harness import *
import crawl
from tap_label_lint import TapLint, PAGES, OPEN

OUT = os.path.join(ROOT, 'review', 'w1trust')

SHEET_NOW = r"""() => {
  const hosts = [...document.querySelectorAll('#mbm, #drawer.on, #ct-sheet, #msg-sheet, #tv-pop, #rp-panel, #hb-composer')].filter(e => e.getClientRects().length);
  const h = hosts[hosts.length - 1];
  if (!h) return null;
  const st = W1.get(h) || (w1Register(h), W1.get(h));
  if (!st) return null;
  const body = (st.def.body && h.querySelector(st.def.body)) || h;
  const f = w1Fields(body).find(x => x.getClientRects().length && (x.tagName === 'TEXTAREA' || /^(text|email|tel|url|)$/.test(x.type || '')) && !x.value);
  if (!f) return { key: st.key, title: st.title, field: null };
  const sig = w1Sigs(body).get(f);
  document.querySelectorAll('[data-w1t]').forEach(x => x.removeAttribute('data-w1t')); f.setAttribute('data-w1t', '1');
  return { key: st.key, title: st.title, field: sig, sel: '[data-w1t="1"]', host: h.id || h.className };
}"""
FIELD_VAL = r"""(sig) => {
  const hosts = [...document.querySelectorAll('#mbm, #drawer.on, #ct-sheet, #msg-sheet, #tv-pop, #rp-panel, #hb-composer')].filter(e => e.getClientRects().length);
  const h = hosts[hosts.length - 1];
  if (!h) return { open: false };
  const st = W1.get(h);
  const body = st && ((st.def.body && h.querySelector(st.def.body)) || h) || h;
  let val = null;
  w1Sigs(body).forEach((s, f) => { if (s === sig) val = w1Val(f); });
  return { open: true, val, bar: !!h.querySelector('.w1-dr'), title: st ? st.title : '' };
}"""
CLEAN = r"""() => { try { localStorage.removeItem('sd-drafts'); } catch (e) {} document.querySelectorAll('#mbm, #mbm-held, #ct-sheet, #msg-sheet, #tv-pop, #rp-panel, #rp-scrim, #hb-composer').forEach(x => x.remove());
  try { document.querySelector('#drawer.on') && closeEditor(); } catch (e) {} const t = document.getElementById('toast'); t && t.classList.remove('on', 'act', 'toast-up'); }"""
# a real tap on another menu entry: the rail on a desktop, the bottom bar on a phone
NAV_AWAY = r"""(cur) => {
  const C = [...document.querySelectorAll('#nav-groups button[data-grp], #mtabs button, #tabbar button, #mtabs a, #tabbar a')].filter(b => b.getClientRects().length);
  const b = C.find(x => !x.classList.contains('on') && !x.matches('[aria-current=page]') && !/menu|more/i.test(x.innerText || x.getAttribute('aria-label') || '')) || null;
  if (!b) return null;
  b.setAttribute('data-w1nav', '1');
  const r = b.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
  // a phone sheet covers the bottom bar: the person cannot tap the bar through it (they tap outside or go Back)
  const top = document.elementFromPoint(x, y);
  if (!(top && b.contains(top))) return null;
  return { x, y, label: (b.innerText || b.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 30) };
}"""
OPEN_KEEP = r"""([u, gid, v, tab]) => { signIn(u); const B = mnBuild(role()) || { groups: [], more: [] };
  const groups = B.field ? [{ id: 'field', items: B.bar.concat(B.rest || [], B.more || []) }] : B.groups.concat(B.more.length ? [{ id: 'more', items: B.more }] : []);
  const g = groups.find(x => x.id === gid), it = g && g.items.find(i => i.v === v && (i.tab || '') === tab);
  if (it) mnGo(g, it); else { view = v; render(); } return view; }"""
# The pilot's sheets by name (Q14, Q44), opened the way the person reached them; walked whether or not the menu walk
# reached them. (person, phone?, name, what opens it, the field typed in). A page form (no sheet) is typed on the page.
NAMED = [
    ('u_owner', False, 'New Lead (Sales)', "view = 'ovsales'; render(); scLeadSheet(null);", '#mbm [data-f="name"]'),
    ('u_alan', False, 'Answer to the field', "const r = DB.field.raises.find(x => !['answered', 'closed'].includes(x.status)) || DB.field.raises[0]; setCurrent(r.projectId); view = 'home'; render(); fAnswerRaise(r);", '#mbm [data-f="a"]'),
    ('u_alan', True, 'Answer to the field', "const r = DB.field.raises.find(x => !['answered', 'closed'].includes(x.status)) || DB.field.raises[0]; setCurrent(r.projectId); view = 'home'; render(); fAnswerRaise(r);", '#mbm [data-f="a"]'),
    ('u_angel', True, 'Crew hours Fix', "setCurrent('p121'); view = 'fcrew'; render(); const b = document.querySelector('[data-ffix]'); b ? b.click() : openTime((DB.time.find(t => t.empId === 'em2') || DB.time[0]).id);", '#mbm input[type="time"], #mbm textarea, #drawer.on #d-body input[type="time"], #drawer.on #d-body textarea'),
    ('u_sarah', False, 'Make It a Task from a mail', "const c = DB.comms.find(x => x.direction !== 'out' && (x.route || {}).projectId) || DB.comms[0]; view = 'home'; render(); newTaskDialog({ title: 'Answer ' + ((c.from || {}).name || 'them'), projectId: (c.route || {}).projectId || '', source: { commId: c.id, label: 'a message' } });", '#mbm [data-f="waitsOn"]'),
    ('u_chen', False, 'Payment terms, Custom', "const po = DB.pos.find(x => x.status === 'draft') || DB.pos[0]; poOpen = po.id; view = 'po'; render(); poTermsDialog(po);", '#mbm textarea, #mbm input[type="number"], #mbm input[data-f]'),
    ('u_chen', True, 'Payment terms, Custom', "const po = DB.pos.find(x => x.status === 'draft') || DB.pos[0]; poOpen = po.id; view = 'po'; render(); poTermsDialog(po);", '#mbm textarea, #mbm input[type="number"], #mbm input[data-f]'),
    ('u_controller', False, 'Bill entry', "view = 'ap'; render(); openEditor('bill', null);", '#drawer.on #d-body textarea, #drawer.on #d-body input[type="text"], #drawer.on #d-body input:not([type])'),
    ('u_alberto', True, 'The request sheet (Requests)', "setCurrent('p121'); view = 'req'; render();", '#cp-text'),
]
TEXTLIKE_KINDS = {'button', 'card', 'link', 'tile', 'chip', 'summary'}


class DraftWalk(TapLint):
    def __init__(self, a):
        super().__init__(a)
        self.found = []          # {vp, user, entry, c, key, title, field}
        self.results = []        # {vp, user, title, how, ok, detail}
        self.checks = Checks()
        self.leaky = False

    async def discover(self, u, phone, vp):
        info = await self.start_user(u)
        if info['user'] != u: return []
        entries = await self.pg.evaluate(PAGES)
        seen, out = set(), []
        for e in entries:
            if self.a.views and e['v'] not in self.a.views: continue
            try: await self.open_entry(e)
            except Exception: continue
            lst = await self.pg.evaluate('() => window.__cr.list()')
            # the page's buttons (one of each kind), then its first rows and cards: a sheet opens from one or the other
            plan = [c for c in await self.buttons_of(lst['cands']) if not crawl.DESTRUCT_RE.match(c['label'])]
            fam, rows = Counter(), []
            for c in lst['cands']:
                if c['scope'] != 'view' or c['kind'] not in ('card', 'link') or any(x['key'] == c['key'] for x in plan): continue
                fam[c['family']] += 1
                if fam[c['family']] > 1 or crawl.DESTRUCT_RE.match(c['label']): continue
                rows.append(c)
            plan = plan[:30] + rows[:2]
            dirty = None
            for c in plan:
                await self.fresh(dirty, u)
                r = await self.press(c, phone)
                if r.get('missing') or r.get('covered'): dirty = 'full'; continue
                dirty = 'full' if (r['keys'] or r['viewChanged'] or r.get('reloaded') or self.navigated) else ('light' if (r['overlays'] or r['sigChanged'] or r['toasts']) else None)
                if r.get('reloaded') or self.navigated: continue
                s = await self.pg.evaluate(SHEET_NOW)
                if not s or not s.get('field'): continue
                k = re.sub(r'\d', '#', s['title'] or s['key'])[:60]
                if k in seen: continue
                seen.add(k)
                out.append({'vp': vp, 'user': u, 'entry': e, 'c': c, 'key': s['key'], 'title': s['title'], 'field': s['field']})
            await self.fresh(dirty, u)
        return out

    async def open_sheet(self, f, phone):
        """the page, then the control that opened the sheet, pressed as a person would"""
        # the page exactly as discovery drew it: the menu entry, a second render (some pages finish drawing on the
        # render after the first), the toast cleared. A plain OPEN left half the found sheets with no opener.
        await self.open_entry(f['entry'])
        pt = await self.pg.evaluate('([k, n]) => window.__cr.point(k, n)', [f['c']['key'], f['c']['n']])
        if pt.get('missing'):
            # the same control by its label and action when the count of its kind differs on this pass
            k = f['c']['key']
            pt = await self.pg.evaluate("""(k) => { const c = window.__cr.list().cands.find(x => x.key === k); return c ? window.__cr.point(c.key, c.n) : { missing: true }; }""", k)
        if pt.get('missing') or pt.get('covered'):
            self.why = 'the opener is gone' if pt.get('missing') else 'the opener is covered by ' + str(pt.get('covered'))[:60]
        if pt.get('missing') or pt.get('covered'): return False
        if phone: await self.pg.touchscreen.tap(pt['x'], pt['y'])
        else: await self.pg.mouse.click(pt['x'], pt['y'])
        await self.settle(150, 1500)
        await self.pg.wait_for_timeout(120)
        return True

    async def leave(self, how, phone, depth=0):
        pg = self.pg
        if depth > 1:
            # a phone sheet that covers the whole screen, opened from the first screen: no bar, no outside and no
            # screen of ours to go Back to. The person closes it with its own X (Back would leave the app; the
            # reload pick-up below covers that). The draft must survive the X just the same.
            pt = await pg.evaluate("""() => { const h = [...document.querySelectorAll('#mbm, #drawer.on, #ct-sheet, #msg-sheet, #tv-pop, #rp-panel, #hb-composer')].filter(e => e.getClientRects().length).pop();
              const x = h && [...h.querySelectorAll('.mbm-x, #mbm-cancel, #d-close, #d-cancel, #rp-x, #hb-comp-x, [data-tvpx], .tv-pop-x, [data-msgsheetx], [data-cts=done], .ct-sheet-back')].find(e => e.getClientRects().length);
              if (!x) return null; const r = x.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }""")
            if not pt: return None
            if phone: await pg.touchscreen.tap(pt['x'], pt['y'])
            else: await pg.mouse.click(pt['x'], pt['y'])
            await self.settle(120, 1200)
            return 'its own close (full-screen sheet)'
        if how == 'back':
            can = await pg.evaluate("() => !!(history.state && history.state.rx && (history.state.d || 0) > 0)")
            if can:
                await pg.evaluate("() => { window.__w1back = 1; }")
                await pg.go_back(); await self.settle(150, 1500); return 'Back'
            how = 'nav'
        if how == 'escape':
            await pg.keyboard.press('Escape'); await self.settle(120, 1200); return 'Escape'
        if how == 'outside':
            # the sheet's own backdrop, or the page beside a drawer: a tap where the sheet is not
            pt = await pg.evaluate("""() => { const h = [...document.querySelectorAll('#mbm, #drawer.on, #ct-sheet, #msg-sheet, #tv-pop, #rp-panel, #hb-composer')].filter(e => e.getClientRects().length).pop();
              // the task panel docked beside the table on a wide screen is not modal: the table stays live, so there is no
              // outside to tap (Asana's pane works the same way); the person leaves it by the menu
              if (!h || h.classList.contains('tv-under')) return null; const box = h.querySelector('.mbm-box, .msg-sheet-in, .tv-pop-bd') || h; const r = box.getBoundingClientRect();
              const pts = [[6, 6], [innerWidth - 6, 6], [6, innerHeight - 90], [innerWidth / 2, 4]];
              for (const [x, y] of pts) { if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) continue; const t = document.elementFromPoint(x, y); if (t) return { x, y }; } return null; }""")
            if pt:
                if phone: await pg.touchscreen.tap(pt['x'], pt['y'])
                else: await pg.mouse.click(pt['x'], pt['y'])
                await self.settle(120, 1200); return 'a tap outside'
            how = 'nav'
        nv = await pg.evaluate(NAV_AWAY, None)
        if not nv: return await self.leave('outside', phone, depth + 1)
        # the bar may sit under the sheet: the person closes nothing first, they tap the bar where it shows
        if phone: await pg.touchscreen.tap(nv['x'], nv['y'])
        else: await pg.mouse.click(nv['x'], nv['y'])
        await self.settle(150, 1500)
        return 'the menu (' + nv['label'] + ')'

    async def round_trip(self, f, how, phone, extra=False):
        pg, C = self.pg, self.checks
        tag = f"{f['vp']} {f['user']} \"{f['title'][:40]}\""
        await pg.evaluate(CLEAN)
        await pg.evaluate("([db, u]) => { DB = JSON.parse(db); signIn(u); render(); }", [self.boot_db, f['user']])
        await self.settle(150, 1500)
        if not await self.open_sheet(f, phone):
            self.results.append({'vp': f['vp'], 'user': f['user'], 'title': f['title'], 'how': how, 'ok': None, 'detail': getattr(self, 'why', 'the opener is gone')}); return None
        s = await pg.evaluate(SHEET_NOW)
        if not s or not s.get('field'):
            self.results.append({'vp': f['vp'], 'user': f['user'], 'title': f['title'], 'how': how, 'ok': None, 'detail': 'the sheet did not open the same way'}); return None
        token = f"Draft {len(self.results) + 1} kept for {f['user'][2:]}"
        try:
            await pg.fill(s['sel'], token)
        except Exception as e:
            self.results.append({'vp': f['vp'], 'user': f['user'], 'title': f['title'], 'how': how, 'ok': None, 'detail': 'could not type: ' + str(e)[:80]}); return None
        await pg.wait_for_timeout(400)
        said = await self.leave(how, phone)
        await pg.wait_for_timeout(250)
        after = await pg.evaluate(FIELD_VAL, s['field'])
        toast = await pg.evaluate("() => (document.getElementById('toast') || {}).innerText || ''")
        closed = not after.get('open') or after.get('title') != s['title']
        # back on the page, the same sheet again
        ok_open = await self.open_sheet(f, phone)
        await pg.wait_for_timeout(250)
        back = await pg.evaluate(FIELD_VAL, s['field'])
        kept = bool(ok_open and back.get('val') == token)
        ok = closed and kept
        C.ok(closed, f"{tag}: left by {said}, the sheet closed (it never stays over the next screen)")
        C.ok(kept, f"{tag}: left by {said}, opened again it holds what was typed ({back.get('val')!r})")
        C.ok(not kept or back.get('bar'), f"{tag}: the sheet says the draft is back and offers Discard Draft")
        self.results.append({'vp': f['vp'], 'user': f['user'], 'title': f['title'], 'how': said, 'ok': ok, 'toast': toast[:80],
                             'detail': '' if ok else f"closed={closed} value={back.get('val')!r}"})
        if extra and kept:
            # Discard asks first, then empties the field
            r = await pg.evaluate("""async () => { const sleep = ms => new Promise(r => setTimeout(r, ms));
              const b = document.querySelector('.w1-dr [data-w1ask]'); if (!b) return { asked: false };
              b.click(); await sleep(60); const ask = !!document.querySelector('.w1-dr [data-w1drop]');
              const k = document.querySelector('.w1-dr [data-w1keep]'); k && k.click(); await sleep(40);
              const stillDraft = w1Drafts().length;
              document.querySelector('.w1-dr [data-w1ask]').click(); await sleep(40); document.querySelector('.w1-dr [data-w1drop]').click(); await sleep(120);
              const f = document.querySelector('[data-w1t="1"]'); return { asked: ask, keptAfterKeep: stillDraft, left: w1Drafts().length, val: f ? f.value : null }; }""")
            C.ok(r.get('asked'), f"{tag}: Discard Draft asks first ({r})")
            C.ok(r.get('keptAfterKeep', 0) >= 1 and r.get('left') == 0, f"{tag}: Keep It keeps the draft; Discard empties it ({r})")
            # a reload with the sheet open brings it back open with the line
            await pg.evaluate(CLEAN)
            if await self.open_sheet(f, phone):
                s2 = await pg.evaluate(SHEET_NOW)
                if s2 and s2.get('field'):
                    await pg.fill(s2['sel'], token + ' after a reload'); await pg.wait_for_timeout(450)
                    # the lint's boot puts the browser's storage back to its first state on every load (so one press never
                    # reaches the next); this person's drafts are what a real reload keeps, so they are put back
                    kept = await pg.evaluate("() => localStorage.getItem('sd-drafts') || ''")
                    await self.load()
                    await pg.evaluate("v => localStorage.setItem('sd-drafts', v)", kept)
                    # the person signs in and is put back on the page they were on (as the app's own reload does): the
                    # sheet comes back by itself
                    await pg.evaluate(OPEN_KEEP, [f['user'], f['entry']['g'], f['entry']['v'], f['entry']['tab']])
                    await self.settle(200, 2500); await pg.wait_for_timeout(500)
                    rv = await pg.evaluate(FIELD_VAL, s2['field'])
                    if not rv.get('open') and os.environ.get('W1_DEBUG'):
                        print('RELOAD', await pg.evaluate("() => ({d: w1Drafts().map(x => ({open: x.open, sc: x.screen && w1ScreenKey(x.screen), op: x.opener, found: !!w1FindOpener(x.opener)})), k: w1ScreenKey(w1Screen()), u: DB.deviceUser, rl: w1Reloaded, opd: w1Opened})"))
                    C.ok(rv.get('open') and rv.get('val') == token + ' after a reload', f"{tag}: a reload with the sheet open brings it back open with the text ({rv})")
                    self.results.append({'vp': f['vp'], 'user': f['user'], 'title': f['title'], 'how': 'a reload', 'ok': bool(rv.get('open') and rv.get('val') == token + ' after a reload'), 'detail': json.dumps(rv)[:120]})
        await pg.evaluate(CLEAN)
        return ok

    async def named_trip(self, uid, phone, name, setup, sel):
        pg, C = self.pg, self.checks
        vp = 'phone' if phone else 'desktop'
        tag = f'{vp} {uid} "{name}"'
        await pg.evaluate(CLEAN)
        await pg.evaluate("([db, u]) => { DB = JSON.parse(db); signIn(u); render(); }", [self.boot_db, uid])
        await self.settle(150, 1500)
        run = "async (s) => { try { (new Function(s))(); } catch (e) { return String(e); } return ''; }"
        err = await pg.evaluate(run, setup)
        await pg.wait_for_timeout(350)
        pick = """(sel) => { document.querySelectorAll('[data-w1t]').forEach(x => x.removeAttribute('data-w1t'));
          const f = [...document.querySelectorAll(sel)].find(x => x.getClientRects().length && !x.disabled && !x.readOnly);
          if (!f) return null; f.setAttribute('data-w1t', '1'); return { type: f.type || f.tagName.toLowerCase(), sheet: !!f.closest('#mbm, #drawer.on') }; }"""
        f = await pg.evaluate(pick, sel)
        if not f:
            self.results.append({'vp': vp, 'user': uid, 'title': name, 'how': 'by name', 'ok': None, 'detail': 'did not open: ' + (err or 'no field')})
            C.ok(False, f"{tag}: the sheet opens with its field ({err or 'no field'})"); return
        val = {'number': '173', 'time': '06:45', 'date': '2026-09-09'}.get(f['type'], f"Typed for {name}, kept")
        await pg.fill('[data-w1t="1"]', val)
        await pg.wait_for_timeout(450)
        said = await self.leave('nav', phone)
        await pg.wait_for_timeout(300)
        open_after = await pg.evaluate("() => !!document.querySelector('#mbm, #drawer.on')")
        await pg.evaluate(run, setup)
        await pg.wait_for_timeout(400)
        f2 = await pg.evaluate(pick, sel)
        got = await pg.evaluate("() => { const f = document.querySelector('[data-w1t=\"1\"]'); return f ? f.value : null; }") if f2 else None
        ok = got == val and (not f['sheet'] or not open_after)
        if f['sheet']: C.ok(not open_after, f"{tag}: left by {said}, the sheet closed with its screen")
        C.ok(got == val, f"{tag}: left by {said} and opened again, it holds what was typed ({got!r})")
        self.results.append({'vp': vp, 'user': uid, 'title': name, 'how': f'by name, left by {said}', 'ok': ok, 'detail': '' if ok else f'value {got!r}, still open {open_after}'})
        await pg.evaluate(CLEAN)

    async def run(self):
        a = self.a
        hows = ['nav', 'escape', 'outside', 'back']
        async with async_playwright() as p:
            for phone in a.vps:
                vp = 'phone' if phone else 'desktop'
                await self.boot(p, phone)
                for u in a.users:
                    t0 = time.time()
                    F = [] if a.named else await self.discover(u, phone, vp)
                    self.found += F
                    if not a.quiet: print(f'-- {vp} {u}: {len(F)} sheets that take typing ({time.time() - t0:.0f}s): ' + ' | '.join(f['title'][:30] for f in F), flush=True)
                    for i, f in enumerate(F[:a.max] if a.max else F):
                        try: await self.round_trip(f, hows[i % len(hows)], phone, extra=(i == 0))
                        except Exception as e:
                            self.checks.ok(False, f"{vp} {u} \"{f['title'][:40]}\": the walk failed: {str(e).splitlines()[0][:120]}")
                            await self.load()
                    for (nu, nph, name, setup, sel) in NAMED:
                        if nu != u or nph != phone or a.views: continue
                        try: await self.named_trip(nu, nph, name, setup, sel)
                        except Exception as e:
                            self.checks.ok(False, f"{vp} {u} \"{name}\": the walk failed: {str(e).splitlines()[0][:120]}")
                            await self.load()
                    await self.pg.evaluate(CLEAN)
                await self.b.close()

    def write(self, t0):
        os.makedirs(OUT, exist_ok=True)
        R = [r for r in self.results if r['how'] != 'a reload']
        ok = [r for r in R if r['ok']]
        skipped = [r for r in R if r['ok'] is None]
        by = Counter((r['vp']) for r in ok)
        with open(os.path.join(OUT, 'drafts.json'), 'w') as fh: json.dump({'found': [{k: v for k, v in f.items() if k != 'c'} | {'label': f['c']['label']} for f in self.found], 'results': self.results}, fh, indent=1)
        L = ['# Drafts walk', '', f"{len(self.found)} sheets that take typing, found by pressing every control on every menu page, every role, both devices; "
             f"{len(ok)} of {len(R) - len(skipped)} kept their text ({len(skipped)} could not be opened the same way twice).", '',
             '| Device | Person | Sheet | Left by | Kept |', '|---|---|---|---|---|']
        L += [f"| {r['vp']} | {r['user']} | {r['title'][:50]} | {r['how']} | {'yes' if r['ok'] else ('n/a: ' + r['detail'] if r['ok'] is None else 'NO: ' + r['detail'])} |" for r in self.results]
        with open(os.path.join(OUT, 'drafts.md'), 'w') as fh: fh.write('\n'.join(L) + '\n')
        for r in skipped[:20]: print('skipped:', r['vp'], r['user'], r['title'][:40], r['detail'])
        rc = self.checks.done()
        print(f"DRAFTS {len(ok)}/{len(R) - len(skipped)} sheets kept their text (desktop {by['desktop']}, phone {by['phone']}; {len(self.found)} sheets found; {time.time() - t0:.0f}s)")
        return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--user'); ap.add_argument('--view')
    ap.add_argument('--phone', action='store_true'); ap.add_argument('--desktop', action='store_true')
    ap.add_argument('--max', type=int, default=0); ap.add_argument('--quiet', action='store_true'); ap.add_argument('--named', action='store_true', help='only the pilot sheets by name')
    a = ap.parse_args()
    a.rules = None; a.no_confirm = True
    a.users = a.user.split(',') if a.user else USERS
    a.views = set(a.view.split(',')) if a.view else None
    a.vps = [False, True]
    if a.phone and not a.desktop: a.vps = [True]
    if a.desktop and not a.phone: a.vps = [False]
    a.per_family, a.max_per_view, a.json = 1, 60, None
    t0 = time.time()
    w = DraftWalk(a)
    asyncio.run(w.run())
    sys.exit(w.write(t0))


if __name__ == '__main__':
    main()
