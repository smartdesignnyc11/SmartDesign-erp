"""tap_label_lint: every button does what its label says (wave 1, Trust; docs/PATH_TO_9.md).

Pilot 2's referee checked every tap against its label (sim/referee.py, classify_clicks): 181 phone taps, 133 landed
where the label said, 5 were dead; two buttons posted money with no preview. This is that check made permanent and
run on every build, not only when nine experts are at work.

For every role (harness.USERS), desktop 1440 and phone 390, every page in that role's menu (mnBuild: the phone bar,
the menu's groups and More, each with its own tab), every visible primary and secondary button on the page (.btn,
not a ghost or an icon), one of each kind per page (a row's Approve once, not on every row), is pressed from a fresh
state: the DB, the app's own UI state and the browser's storage put back in memory before each press (crawl.py's
machinery, which this lint reuses whole). It fails when a press
  DEAD      does nothing: no page, sheet, toast, scroll, dialog or change in the records
  OFFLABEL  lands on a page or sheet its label does not name: the label's words (the referee's promise_words) are
            not in the heading, the first words on screen, the sheet's title or the toast
  SILENT    changes the records with no toast, or with a toast that has no Open (CLAUDE.md: every mutation toasts
            what happened, with Open); and a toast whose Open names a record but lands somewhere else
  MISMATCH, DEADEND, ERROR, DESTRUCTIVE  crawl.py's rules (Open X opens another record, a view the role may not
            open, a page error, a Delete with no confirmation)
Every flag is pressed again from a freshly booted page; one that does not come back was the lint's own sequence.

Buttons other lanes own right now (CLAUDE.md lane rules) are pressed and reported under "Owned elsewhere", not
failed: money posting (p2fix2), client documents and the portal (p2fix3), the Buy Board, RFQ and PO pages
(procurement P1). Each entry names its lane, so the list empties as they merge.

  python3 tap_label_lint.py [--user u_owner,u_alan] [--phone|--desktop] [--view home,billing] [--quiet]
Output: review/taplint/report.md and flags.json; the last line `TAPLINT N flags (pressed X buttons on Y pages)`.
Exit 1 if N > 0.
"""
import asyncio, json, os, re, sys, time, argparse
from collections import Counter, defaultdict
from harness import *
import crawl
from crawl import Crawler, judge, allowed, norm, share, DOC_RE, UI_KEYS

OUT = os.path.join(ROOT, 'review', 'taplint')

# ---- the referee's label promise (sim/referee.py: promise_words), so the lint and the pilot judge one way
NAV_WORDS = re.compile(r'^(open|view|see|show|go to|go|review|all|more|the|my|your|new|start|back to|to|menu:)\s+', re.I)
STOPW = {'with', 'from', 'this', 'that', 'your', 'for', 'and', 'the', 'all', 'more', 'view', 'open', 'new', 'item', 'items', 'link', 'icon',
         'you', 'are', 'its', 'our', 'out', 'not', 'one'}


def promise_words(label):
    lab = re.split(r'[>›]', str(label or '').replace('menu: ', ''))[-1]
    lab = re.sub(r'\$[\d,.]+|\b\d[\d,./:%-]*\b|[()\[\]·|→+]', ' ', lab)
    for _ in range(3): lab = NAV_WORDS.sub('', lab.strip())
    return [w.lower()[:5] for w in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", lab) if w.lower() not in STOPW][:5]


# a label that is a verb promises an act, not a place (the referee's DOES): an act that opens its own sheet first is
# judged by that sheet
DOES = re.compile(r'^(save|send|approve|confirm|mark|record|apply|submit|done|got it|delete|remove|issue|import|sign|clock|pay|match|close|reject|hold|'
                  r'accept|acknowledge|post|assign|reply|answer|upload|take|check in|end|finish|create|add|book|log|request|order|receive|void|dispute|split|'
                  r'attach|copy|duplicate|convert|keep|dismiss|snooze|skip|yes|no|ok|next|continue|update|set|move|share|print|export|download|draft|email|'
                  r'text|call|won|lost|closed won|close as|unqualify|junk|refresh|run|build|release|reverse|credit|bill|invoice|categori|code|chase|'
                  r'follow|remind|speak|say|ask|start|stop|pause|resume|hand|offer|decline|scan|photo|attach|fix|edit|change|rename|filter|sort|pick|'
                  r'choose|select|connect|sync|link|unlink|enable|disable|turn|show|hide|expand|collapse|less|more|load|try)\b', re.I)

# Owned by another lane right now: (label regex, view regex or None, lane). Pressed and reported, never failed.
OWNED = [
    (r'^(enter the bill|confirm|record payment|record a payment|pay|pay now|mark paid|post|match)\b', r'^(home|today|banking|bank|bills|ap|pay|payments|recon|gl|ovacct|txns)', 'p2fix2 (money posting)'),
    (r'^(enter the bill)\b', None, 'p2fix2 (money posting)'),
    (r'^(record payment|record a payment)\b', None, 'p2fix2 (money posting)'),
    (r'.', r'^(portal|clportal|client|clacct|cldocs)$', 'p2fix3 (client documents and the portal)'),
    (r'^(send to client|preview|print|download pdf|client view|send|resend)\b', r'^(billing|inv|est|cos|docs)$', 'p2fix3 (client documents)'),
    (r'.', r'^(proc|ovbuy|rfq|po|buy|recv)$', 'procurement P1 (Buy Board, RFQ and PO pages)'),
]
OWNED_ROLES = {'client': 'p2fix3 (client documents and the portal)'}

# Demonstrable false positives of the label rule only, each with its reason: (label regex, view regex or None, why).
ALLOW = [
]

PAGES = r"""() => { const B = mnBuild(role()); if (!B) return [];
  const groups = B.field ? [{ id: 'field', items: B.bar.concat(B.rest || [], B.more || []) }] : B.groups.concat(B.more.length ? [{ id: 'more', items: B.more }] : []);
  const out = [], seen = new Set();
  groups.forEach(g => g.items.forEach(it => { const k = it.v + ':' + (it.tab || ''); if (seen.has(k)) return; seen.add(k); out.push({ g: g.id, v: it.v, tab: it.tab || '', l: it.l }); }));
  return out; }"""
OPEN = r"""([gid, v, tab]) => { const B = mnBuild(role());
  const groups = B.field ? [{ id: 'field', items: B.bar.concat(B.rest || [], B.more || []) }] : B.groups.concat(B.more.length ? [{ id: 'more', items: B.more }] : []);
  const g = groups.find(x => x.id === gid), it = g && g.items.find(i => i.v === v && (i.tab || '') === tab);
  document.querySelectorAll('#mbm, #mbm-held').forEach(x => x.remove());
  try { typeof closeEditor === 'function' && document.querySelector('#drawer.on') && closeEditor(); } catch (e) {}
  if (typeof docOpen !== 'undefined') docOpen = null;
  if (it) mnGo(g, it); else { view = v; render(); }
  window.scrollTo(0, 0); return view; }"""
# which listed candidates are the page's primary and secondary buttons
BUTTONS = r"""(ids) => ids.map(i => { const e = document.querySelector(`[data-cr-i="${i}"]`);
  if (!e) return null;
  const b = e.closest('.btn') === e || e.matches('.btn, button.btn, a.btn');
  return b && !e.matches('.ghost, .icon, .ico, .x, [class*="-x"]') && !e.closest('#nav-groups, #subnav, #mtabs, #tabbar, header.topbar, .topbar') ? (e.matches('.primary') ? 'primary' : 'secondary') : null; })"""


def owned_by(label, view, role):
    if role in OWNED_ROLES: return OWNED_ROLES[role]
    for lre, vre, lane in OWNED:
        if re.search(lre, label, re.I) and (vre is None or re.search(vre, view or '')): return lane
    return None


GENERIC = re.compile(r'^(review|respond|edit|details|view|open|see|look|check|more|show|show me|go|start|begin|resume|continue|next|back|answer|reply|fix|change|update|manage|choose|pick|select)(\s+(it|this|them|now|details|all))?$', re.I)


def label_flags(c, r):
    """The referee's rule: a press that went somewhere (a page, a sheet) lands where its label's words are."""
    L = c['label']
    # a label that names no place (Review, Respond, Edit, Details) promises the record it sits on: crawl's Open X rule
    # judges a named record; these are judged by the dead and silent rules only
    if GENERIC.match(L.strip()): return []
    # a row's whole text (a sentence, a name and an amount) is the record it opens, judged by crawl's Open X rule
    if len(L.split()) >= 6: return []
    words = promise_words(L)
    if not words or r.get('reloaded'): return []
    mutated = [k for k in r['keys'] if k not in UI_KEYS]
    toasts = ' '.join(t['text'] for t in r['toasts'])
    moved = r['viewChanged'] or bool(r['overlays'])
    if not moved or mutated or toasts: return []
    if r['overlays']:
        o = r['overlays'][-1]
        hay = o['title'] + ' ' + o['text'][:400]
    else:
        hay = ' '.join([r['heading'], r['top'][:300], r['tabL'], r['grpL'], ' '.join(r['activeTabs']), r.get('anchor', ''), ' '.join(r['hl'])])
    if any(w in hay.lower() for w in words) or share(L, hay):
        return []
    where = crawl.dest_title(r) or r['view']
    return [('OFFLABEL', f"\"{L[:40]}\" lands on \"{where[:60]}\" (view '{r['view']}'), which does not name {', '.join(words)}")]


def toast_open_flags(r, tl):
    """A toast that names a record (SE-0922, INV-2026-041) opens that record, not a list or the Inbox."""
    if not tl or not tl.get('acted'): return []
    toks = [m.group(0) for t in r['toasts'] for m in DOC_RE.finditer(t['text'])]
    if not toks: return []
    here = ' '.join([tl.get('title', ''), tl.get('here', '')])
    if any(k in here for k in toks): return []
    return [('SILENT', f"toast names {toks[0]} but its Open lands on \"{tl.get('title', '')[:50]}\" (view '{tl.get('view')}')")]


class TapLint(Crawler):
    def __init__(self, a):
        super().__init__(a)
        self.owned = []
        self.pages = 0
        self.entry = None

    async def open_entry(self, e):
        await self.pg.evaluate(OPEN, [e['g'], e['v'], e['tab']])
        await self.settle(200, 2500)
        await self.pg.evaluate("() => { render(); window.scrollTo(0, 0); }")
        await self.settle(150, 2000)
        await self.pg.evaluate("() => { const t = document.getElementById('toast'); t && t.classList.remove('on', 'act', 'toast-up'); window.scrollTo(0, 0); }")
        await self.pg.evaluate('() => window.__cr.snap()')
        self.view_db = await self.pg.evaluate('() => window.__cr.snapDb')
        self.view_v = await self.pg.evaluate('view')
        self.entry = e

    async def reboot_view(self, u):
        self.reloads += 1
        await self.load()
        await self.pg.evaluate("([db, u]) => { DB = JSON.parse(db); signIn(u); DB = JSON.parse(db); setCurrent(DB.currentId); render(); }", [self.view_db, u])
        await self.settle(200, 2500)
        e = self.entry
        await self.pg.evaluate(OPEN, [e['g'], e['v'], e['tab']])
        await self.settle(200, 2500)
        await self.pg.evaluate("() => { const t = document.getElementById('toast'); t && t.classList.remove('on', 'act', 'toast-up'); window.scrollTo(0, 0); }")
        await self.pg.evaluate('() => window.__cr.snap()')

    async def follow_toast(self, r, ctx):
        tl = await super().follow_toast(r, ctx)
        if tl:
            try:
                t = await self.pg.evaluate("() => { const v = document.querySelector('.view.on'); const o = window.__cr.overlays(); return (o.map(x => x.innerText).join(' ') + ' ' + (v ? v.innerText : '')).replace(/\\s+/g, ' ').slice(0, 3000); }")
                tl['here'] = t
            except Exception: tl['here'] = ''
        return tl

    async def buttons_of(self, cands):
        ids = [c['i'] for c in cands]
        kinds = await self.pg.evaluate(BUTTONS, ids)
        out, fam = [], Counter()
        for c, k in zip(cands, kinds):
            if not k or c['scope'] != 'view': continue
            fam[c['family']] += 1
            if fam[c['family']] > 1: continue
            c['btn'] = k
            out.append(c)
        return out

    async def judge_press(self, c, r, ctx, rw_cache):
        found = await self.assess(c, r, ctx, rw_cache, leaks=False)
        # crawl's NOOP is the referee's dead tap
        found = [('DEAD' if rule == 'NOOP' else rule, det) for rule, det in found if rule != 'INFO']
        found += [x for x in label_flags(c, r) if not any(f[0] == 'MISMATCH' for f in found)]
        if any(t['links'] for t in r['toasts']) and not r.get('reloaded'):
            tl = await self.follow_toast(r, ctx)
            if tl:
                for rule, det in judge(c, dict(r, toastLink=tl, errors=[]), ctx):
                    if 'toast' in det and 'link' in det and not allowed(rule, c, ctx['view']): found.append((rule, det))
                found += toast_open_flags(r, tl)
        # a press that asks first: Yes, Continue is the act, and it owes what the press owed (Pilot 2: the first Yes,
        # Continue on Done saved nothing, Yes, Continue on Delete said nothing)
        if r['overlays'] and not r.get('reloaded') and re.search(r'please confirm|one thing first', r['overlays'][-1]['title'], re.I):
            found += await self.yes_continue(c)
        return [(rule, det) for rule, det in found if not any(re.search(l, c['label'], re.I) and (v is None or re.search(v, ctx['view'])) for l, v, _ in ALLOW)]

    async def yes_continue(self, c):
        pg = self.pg
        ok = await pg.evaluate("() => { const b = document.querySelector('#mbm #mbm-ok'); if (!b || !/^(yes|continue)/i.test(b.innerText.trim())) return null; const r = b.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, t: b.innerText.trim() }; }")
        if not ok: return []
        if await pg.evaluate("() => !!document.querySelector('#mbm [data-f]')"): return []   # a question that wants an answer typed
        await pg.evaluate('() => window.__cr.before()')
        await pg.mouse.click(ok['x'], ok['y'])
        await self.settle()
        r2 = await pg.evaluate('o => window.__cr && window.__cr.after(o)', {})
        if not r2: return []
        mut = [k for k in r2['keys'] if k not in UI_KEYS]
        if not mut and not r2['toasts'] and not r2['viewChanged'] and not r2['overlays'] and not r2['sigChanged']:
            return [('DEAD', f"\"{c['label'][:40]}\" asks first, and {ok['t']} then does nothing")]
        if mut and not r2['toasts'] and not r2['overlays']:
            return [('SILENT', f"\"{c['label'][:40]}\": {ok['t']} changed {', '.join(mut)[:60]} with no toast")]
        if mut and r2['toasts'] and not any(t['links'] for t in r2['toasts']) and not crawl.DESTRUCT_RE.match(c['label']):
            return [('SILENT', f"\"{c['label'][:40]}\": {ok['t']} toasted \"{r2['toasts'][-1]['text'][:50]}\" with no Open")]
        return []

    def record(self, rule, vp, u, e, c, det, r, role):
        lane = owned_by(c['label'], e['v'], role)
        f = {'rule': rule, 'viewport': vp, 'user': u, 'view': e['v'], 'tab': e['tab'], 'page': e['l'], 'label': c['label'][:80], 'btn': c.get('btn'),
             'key': c['key'], 'n': c['n'], 'detail': det, 'g': e['g'], 'html': c.get('html', ''),
             'dest': {'view': r.get('view'), 'title': crawl.dest_title(r)[:80] if 'heading' in r else '',
                      'toasts': [t['text'][:80] + (' [' + ', '.join(t['links']) + ']' if t['links'] else '') for t in r.get('toasts', [])[:3]]}}
        if lane:
            f['lane'] = lane; self.owned.append(f)
        else:
            self.flags.append(f)
            if not self.a.quiet: print(f"{rule} | {vp} | {u} | {e['l']} ({e['v']}) | {c['label'][:50]} | {det}", flush=True)

    async def run(self):
        a = self.a
        async with async_playwright() as p:
            for phone in a.vps:
                vp = 'phone' if phone else 'desktop'
                await self.boot(p, phone)
                for u in a.users:
                    info = await self.start_user(u)
                    if info['user'] != u: print(f'skip {u}: no such user'); continue
                    role, may = info['role'], info['may']
                    self.cur_user = u; self.leaky = False
                    rw_cache = {}
                    t_user = time.time(); n_user = 0
                    entries = await self.pg.evaluate(PAGES)
                    for e in entries:
                        if a.views and e['v'] not in a.views: continue
                        try: await self.open_entry(e)
                        except Exception as ex:
                            await self.load(); await self.start_user(u)
                            try: await self.open_entry(e)
                            except Exception as ex2:
                                self.flags.append({'rule': 'ERROR', 'viewport': vp, 'user': u, 'view': e['v'], 'tab': e['tab'], 'page': e['l'], 'label': '(opening the page)',
                                                   'detail': str(ex2).splitlines()[0][:160]}); continue
                        self.pages += 1
                        lst = await self.pg.evaluate('() => window.__cr.list()')
                        plan = await self.buttons_of(lst['cands'])
                        ctx = {'user': u, 'role': role, 'views': may, 'view': e['v'], 'leakWords': [], 'vp': vp}
                        dirty = None
                        for c in plan:
                            await self.fresh(dirty, u)
                            # what was pressed, for the report (the page is drawn again by the press)
                            try: c['html'] = await self.pg.evaluate("([k, n]) => { const e = window.__cr.byKey && window.__cr.byKey.get(k + '#' + n); return e ? e.outerHTML.slice(0, 260) : ''; }", [c['key'], c['n']])
                            except Exception: c['html'] = ''
                            r = await self.press(c, phone)
                            if r.get('missing'): self.skipped['gone after restore'] += 1; dirty = 'full'; continue
                            if r.get('covered'): self.covered[(vp, u, e['v'])] += 1; self.skipped['covered'] += 1; dirty = None; continue
                            self.pressed[(vp, u)] += 1; n_user += 1
                            for rule, det in await self.judge_press(c, r, ctx, rw_cache):
                                self.record(rule, vp, u, e, c, det, r, role)
                            mut = [k for k in r['keys'] if k not in UI_KEYS]
                            # a toast's Open followed, or Yes, Continue pressed: the page moved on, draw it again
                            followed = r['toasts'] or (r['overlays'] and re.search(r'please confirm|one thing first', r['overlays'][-1]['title'], re.I))
                            if r.get('reloaded') or self.navigated or mut or followed or r['viewChanged'] or r['curChanged'] or r['keys'] or r.get('viewSigChanged'): dirty = 'full'
                            elif r['overlays'] or r['sigChanged'] or r['toasts'] or r['scrolled']: dirty = 'light'
                            else: dirty = None
                        await self.fresh(dirty, u)
                    if not a.quiet: print(f'-- {vp} {u}: {n_user} buttons in {time.time() - t_user:.0f}s', flush=True)
                if not a.no_confirm: await self.confirm_flags(phone)
                await self.b.close()

    async def confirm_flags(self, phone):
        """Each flag again from a freshly booted page: the page opened straight after sign-in, the button pressed once."""
        vp = 'phone' if phone else 'desktop'
        keep = []
        for f in self.flags:
            if f['viewport'] != vp or f['label'] == '(opening the page)': keep.append(f); continue
            await self.load()
            info = await self.start_user(f['user'])
            e = {'g': f['g'], 'v': f['view'], 'tab': f['tab'], 'l': f['page']}
            await self.open_entry(e)
            ctx = {'user': f['user'], 'role': info['role'], 'views': info['may'], 'view': f['view'], 'leakWords': [], 'vp': vp}
            lst = await self.pg.evaluate('() => window.__cr.list()')
            c = next((x for x in lst['cands'] if x['key'] == f['key'] and x['n'] == f['n']), None)
            if not c: self.infos.append(dict(f, detail='gone on a fresh boot: ' + f['detail'])); continue
            r = await self.press(c, phone)
            if r.get('missing') or r.get('covered'): self.infos.append(dict(f, detail='gone on a fresh boot: ' + f['detail'])); continue
            again = await self.judge_press(c, r, ctx, {})
            if any(rule == f['rule'] for rule, _ in again): keep.append(f)
            else:
                self.infos.append(dict(f, detail='not reproduced from a fresh boot: ' + f['detail']))
                if not self.a.quiet: print(f"not reproduced from a fresh boot: {f['rule']} | {vp} | {f['user']} | {f['page']} | {f['label'][:50]}", flush=True)
        self.flags = keep

    def write(self, t0):
        os.makedirs(OUT, exist_ok=True)
        pressed = sum(self.pressed.values())
        by = Counter(f['rule'] for f in self.flags)
        with open(os.path.join(OUT, 'flags.json'), 'w') as fh:
            json.dump({'flags': self.flags, 'owned': self.owned, 'info': self.infos, 'pressed': {f'{k[0]} {k[1]}': n for k, n in self.pressed.items()},
                       'pages': self.pages, 'skipped': dict(self.skipped), 'seconds': round(time.time() - t0)}, fh, indent=1)
        L = ['# Tap-label lint', '', f'{pressed} buttons pressed on {self.pages} menu pages in {(time.time() - t0) / 60:.1f} min; {len(self.flags)} flags; '
             f'{len(self.owned)} findings on buttons other lanes own.', '', '| Rule | Flags |', '|---|---|'] + [f'| {k} | {n} |' for k, n in by.most_common()]
        L += ['', '## Flags', ''] + [f"- {f['rule']} | {f['viewport']} | {f['user']} | {f['page']} ({f['view']}) | {f['label'][:60]} | {f['detail']}" for f in self.flags]
        L += ['', '## Owned elsewhere (reported, not failed)', ''] + [f"- {f['lane']}: {f['rule']} | {f['viewport']} | {f['user']} | {f['page']} | {f['label'][:60]} | {f['detail']}" for f in self.owned]
        L += ['', '## Not reproduced from a fresh boot', ''] + [f"- {f['viewport']} | {f['user']} | {f['page']} | {f['label'][:50]} | {f['detail']}" for f in self.infos[:300]]
        with open(os.path.join(OUT, 'report.md'), 'w') as fh: fh.write('\n'.join(L) + '\n')
        for k, n in by.most_common(): print(f'{k:<10}{n:>5}')
        print(f'owned elsewhere: {len(self.owned)}; per device and person: {dict((f"{k[0]} {k[1]}", n) for k, n in self.pressed.items())}')
        print(f'TAPLINT {len(self.flags)} flags (pressed {pressed} buttons on {self.pages} pages)')
        return 1 if self.flags else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--user'); ap.add_argument('--view')
    ap.add_argument('--phone', action='store_true'); ap.add_argument('--desktop', action='store_true')
    ap.add_argument('--quiet', action='store_true'); ap.add_argument('--no-confirm', action='store_true')
    a = ap.parse_args()
    a.rules = None
    a.users = a.user.split(',') if a.user else USERS
    a.views = set(a.view.split(',')) if a.view else None
    a.vps = [False, True]
    if a.phone and not a.desktop: a.vps = [True]
    if a.desktop and not a.phone: a.vps = [False]
    a.per_family, a.max_per_view, a.json = 1, 60, None
    t0 = time.time()
    lint = TapLint(a)
    asyncio.run(lint.run())
    sys.exit(lint.write(t0))


if __name__ == '__main__':
    main()
