"""ia_map: the information map (Alan, 2026-10-21). A measurement, not a fix: it changes no app code.

"Make sure the desktop and mobile versions give each role the information they need to do their job, see what
priorities there are before they become delays ... the pages are clean ... the task module isn't great on mobile ...
there aren't 12 different sections to see similar information."

For every role (the nine office and field seats and the client), at 1440 and at 390, it walks every page the role may
open (ROLE_VIEWS, Mercer & Bond and Ask left out), plus the filters of the queue pages (Today's Do Now tabs, the task
list's views), and reads each screen: its heading, its tabs, its sections (cards with a heading), the count each
section shows, and which records each section lists. Records are found by their own words: a catalog of every
record a person may be shown (tasks, schedule tasks, approvals, inbox, decisions, materials, field requests,
submittals, inspections, site questions, COI lapses, invoices, bills, POs, money flags, specialist findings) gives
each one its title (`IA.catalog`, tests/ia_js.js); a record is in a section when its title is in the section's text.
Then:
  places      each noun, for each role and screen size: every screen and section that lists it, how many of the same
              records show in more than one place, and the question clusters ("what do I owe today") per role
  numbers     the same label showing different numbers on different screens (one question, one number)
  precursors  what becomes a delay in the next 10 working days if nobody acts (order-by dates, decisions due,
              inspections to book, submittals, crew requests, subs to confirm, late predecessors, site questions,
              COI lapses): for the person who must act, where it shows, its rank and y on their first screen, above the
              fold on the phone or not, and from how many working days ahead (the app's day is moved back and forward
              without running the day's hooks; only what the screens show changes)
  tasks       every task screen on the phone: what shows first, rows above the fold, taps to complete, update, hand
              off and add, what is cut off; screenshots in review/ia/
  clutter     per phone screen: sections above the fold, visual groups, empty cards, internal words
Writes review/ia/data.json and review/ia/tables.md (the tables map.md quotes).

  python3 ia_map.py                 everything (about 25 minutes; run it through tests/slot.sh)
  python3 ia_map.py --walk|--pre|--tasks|--report   one step (report reads data.json)
  python3 ia_map.py --check         the measurable checks against data.json; fails today by design (map.md, Checks)
  python3 ia_map.py --user u_alan   one role (walk only)
"""
import asyncio, json, os, re, sys, time
from collections import defaultdict
from harness import *

OUT = os.path.join(ROOT, 'review', 'ia')
DATA = os.path.join(OUT, 'data.json')
JS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ia_js.js')).read()
ROLE = {'u_owner': 'owner', 'u_alan': 'pm', 'u_chen': 'coord', 'u_angel': 'foreman', 'u_alberto': 'crew', 'u_alex': 'driver',
        'u_sarah': 'designer', 'u_billing': 'billing', 'u_controller': 'controller', 'u_klein': 'client'}
WHO = {'u_owner': 'Owner', 'u_alan': 'PM (Alan)', 'u_chen': 'Coordinator (Chen)', 'u_angel': 'Foreman (Angel)', 'u_alberto': 'Crew (Alberto)',
       'u_alex': 'Driver (Alex)', 'u_sarah': 'Designer (Sarah)', 'u_billing': 'Billing', 'u_controller': 'Controller', 'u_klein': 'Client (Klein)'}
ORDER = ['u_owner', 'u_alan', 'u_chen', 'u_angel', 'u_alberto', 'u_alex', 'u_sarah', 'u_billing', 'u_controller', 'u_klein']
NOUN = {'task': 'tasks (to-dos)', 'sched': 'schedule tasks', 'approval': 'approvals', 'inbox': 'inbox mail', 'decision': 'decisions',
        'material': 'materials to buy', 'request': 'field requests', 'submittal': 'submittals', 'inspection': 'inspections',
        'siteq': 'site questions / RFIs', 'coi': 'COI lapses', 'invoice': 'invoices', 'bill': 'bills', 'po': 'purchase orders',
        'flag': 'money flags', 'finding': 'specialist findings', 'subconfirm': 'subs to confirm'}
# The questions a person asks of the app, and the nouns that answer each (clusters of "similar information")
QUESTIONS = {
    'What do I owe today?': ['task', 'approval', 'inbox', 'siteq'],
    'What is late or at risk on my jobs?': ['sched', 'decision', 'submittal', 'inspection', 'subconfirm'],
    'What has to be bought or ordered?': ['material', 'request', 'po'],
    'Where is money leaking or owed?': ['flag', 'finding', 'bill', 'invoice', 'coi'],
}
QUEUE_TABS = '.td-tabs button, .ctabs.t2-views button'
# reference and file pages: their words name records (the Standard's duties, a file named for its submittal) without
# listing them as work, so they are left out of the places count
REFERENCE = {'standard', 'conn', 'rdata', 'rpbox', 'setup', 'hbsettings', 'files', 'photos'}
TAB_VIEWS = {'home', 'tkall', 'tasks'}
TASK_SCREENS = [  # (user, view, tab selector index or None, label)
    ('u_owner', 'home', 'Tasks', 'Owner Today, Tasks filter'),
    ('u_alan', 'home', None, 'PM Today (All)'),
    ('u_alan', 'home', 'Tasks', 'PM Today, Tasks filter'),
    ('u_alan', 'tkall', None, 'PM Tasks (tkall), first view'),
    ('u_alan', 'tkall', 'Next 7 Days', 'PM Tasks, Next 7 Days'),
    ('u_alan', 'tkall', 'Overdue', 'PM Tasks, Overdue'),
    ('u_alan', 'tasks', None, 'PM project Tasks'),
    ('u_chen', 'home', 'Tasks', 'Coordinator Today, Tasks filter'),
    ('u_chen', 'tkall', None, 'Coordinator Tasks'),
    ('u_sarah', 'sday', None, 'Designer Today'),
    ('u_sarah', 'tkall', None, 'Designer Tasks'),
    ('u_angel', 'ftoday', None, "Foreman Today (Today's Work)"),
    ('u_alberto', 'tasks', None, 'Crew Tasks'),
    ('u_billing', 'tkall', None, 'Billing Tasks'),
    ('u_controller', 'tkall', None, 'Controller Tasks'),
]


def views_of(rv):
    seen = []
    for v in rv:
        if v in seen or v == 'pa' or v.startswith('mb'): continue
        seen.append(v)
    return seen


async def boot(p, phone):
    b, pg, errs = await open_app(p, phone)
    await pg.evaluate(JS)
    await pg.evaluate("() => { try { window.__iadflt = { v: t2View, w: tkWho }; } catch (e) { window.__iadflt = null; } }")
    return b, pg, errs


async def reset_lists(pg):
    """the task list's filters as a fresh sign-in has them (they are page state shared by every task screen)"""
    await pg.evaluate("() => { const d = window.__iadflt; if (d) try { t2View = d.v; tkWho = d.w; } catch (e) {} try { for (const k in tdyTabs) delete tdyTabs[k]; tdyAllOpen = false; } catch (e) {} }")


async def open_view(pg, v):
    await pg.evaluate("v => { view = v; render(); }", v)
    await pg.wait_for_timeout(160)


async def scan(pg):
    return await pg.evaluate("() => IA.scan(window.__iacat)")


def compact(s, name):
    if not s: return None
    s['name'] = name
    s['found'] = [[f['k'], f['sec'], f['y'], f['rank'], 1 if f['above'] else 0] for f in s['found']]
    return s


async def walk_role(pg, uid, phone):
    await reset_lists(pg)
    await sign_in(pg, uid)
    await pg.wait_for_timeout(200)
    meta = await pg.evaluate("""() => { window.__iacat = IA.catalog();
      const by = {}; window.__iacat.forEach(o => by[o.noun] = (by[o.noun] || 0) + 1);
      const m = typeof mnMap === 'function' && mnOn && mnOn() ? mnMap() : null;
      const bar = [...document.querySelectorAll('#mtabs button, #tabbar button')].filter(b => b.getClientRects().length).map(b => (b.innerText || '').replace(/\\s+/g, ' ').replace(/\\s*\\d+$/, '').trim());
      return { role: role(), first: view, views: ROLE_VIEWS[role()] || [], menu: m, bar: bar, nouns: by,
               cat: window.__iacat.map(o => ({ k: o.k, noun: o.noun, t: o.t, n: o.n, due: o.due || '', who: o.who || o.appr || '', risk: o.risk || '' })) }; }""")
    first = meta['first']
    out = {'uid': uid, 'role': meta['role'], 'first': first, 'menu': meta['menu'], 'bar': meta['bar'], 'nouns': meta['nouns'], 'screens': []}
    vs = views_of(meta['views'])
    if first in vs: vs.remove(first)
    vs.insert(0, first)
    for v in vs:
        t0 = time.time()
        try:
            await open_view(pg, v)
            s = compact(await scan(pg), v)
        except Exception as e:
            s = {'name': v, 'error': str(e)[:200]}
        if s: s['ms'] = int((time.time() - t0) * 1000); out['screens'].append(s)
        # the queue pages' filters: each tab is a screen of its own
        if v in TAB_VIEWS:
            n = await pg.evaluate(f"() => [...document.querySelectorAll('.view.on :is({QUEUE_TABS})')].filter(b => b.getClientRects().length).length")
            on = await pg.evaluate(f"() => [...document.querySelectorAll('.view.on :is({QUEUE_TABS})')].filter(b => b.getClientRects().length).findIndex(b => b.classList.contains('on'))")
            for i in range(n):
                if i == on: continue
                lab = await pg.evaluate(f"i => {{ const b = [...document.querySelectorAll('.view.on :is({QUEUE_TABS})')].filter(b => b.getClientRects().length)[i]; if (!b) return ''; const l = (b.getAttribute('aria-label') || b.title || b.textContent || '').replace(/\\s+/g, ' ').replace(/\\s*\\d+\\+?$/, '').trim(); b.click(); return l; }}", i)
                await pg.wait_for_timeout(160)
                s2 = compact(await scan(pg), f'{v}[{lab}]')
                if s2: out['screens'].append(s2)
            if on >= 0 and n:
                await pg.evaluate(f"i => {{ const b = [...document.querySelectorAll('.view.on :is({QUEUE_TABS})')].filter(b => b.getClientRects().length)[i]; b && b.click(); }}", on)
                await pg.wait_for_timeout(100)
    return out, meta['cat']


async def walk(users):
    data = load()
    data.setdefault('walk', {})
    data.setdefault('catalog', {})
    async with async_playwright() as p:
        for phone in (False, True):
            key = 'phone' if phone else 'desktop'
            b, pg, errs = await boot(p, phone)
            for u in users:
                t0 = time.time()
                r, cat = await walk_role(pg, u, phone)
                r['errors'] = errs[:5]; del errs[:]
                data['walk'].setdefault(key, {})[u] = r
                data['catalog'][u] = cat
                print(f'{key} {u}: {len(r["screens"])} screens, {int(time.time() - t0)}s', flush=True)
                save(data)
            await b.close()
    return data


# ------------------------------------------------------------------ precursors: where each shows, and from how far ahead
async def precursors():
    data = load()
    async with async_playwright() as p:
        b, pg, errs = await boot(p, True)
        await sign_in(pg, 'u_owner')
        P = await pg.evaluate("() => IA.precursors()")
        orig = await pg.evaluate("() => ({ asOf: DB.company.asOf || '', manual: !!DB.company.asOfManual })")
        days = await pg.evaluate("t => { const out = []; for (let i = -10; i <= 10; i++) out.push(addWork(t, i, false)); return [...new Set(out)]; }", P['today'])
        actors = sorted({a for it in P['items'] for a in it['actors']})
        seen = {}  # actor -> day -> {k: [y, rank, above]}
        for a in actors:
            mine = [it for it in P['items'] if a in it['actors']]
            await pg.evaluate("c => { window.__iapre = c; }", [{'k': it['k'], 'noun': it['kind'], 'n': it['n'], 'ctx': it.get('ctx')} for it in mine])
            seen[a] = {}
            for d in days:
                # the day moves, nothing else: no day hooks run, so no record is created or escalated by the scan
                await pg.evaluate("d => { DB.company.asOf = d; DB.company.asOfManual = true; iaOneClock(); }", d)
                await sign_in(pg, a)
                await pg.wait_for_timeout(120)
                f = await pg.evaluate("() => IA.find(window.__iapre)")
                seen[a][d] = {x['k']: [x['y'], x['rank'], 1 if x['above'] else 0, x['sec']] for x in f}
            print(f'precursors: {a} scanned {len(days)} days', flush=True)
        await pg.evaluate("o => { DB.company.asOf = o.asOf; DB.company.asOfManual = o.manual; iaOneClock(); }", orig)
        # the same first screen on the desktop, today: rank and y
        b2, pg2, _ = await boot(p, False)
        desk = {}
        for a in actors:
            mine = [it for it in P['items'] if a in it['actors']]
            await pg2.evaluate("c => { window.__iapre = c; }", [{'k': it['k'], 'noun': it['kind'], 'n': it['n'], 'ctx': it.get('ctx')} for it in mine])
            await sign_in(pg2, a)
            await pg2.wait_for_timeout(150)
            f = await pg2.evaluate("() => IA.find(window.__iapre)")
            desk[a] = {x['k']: [x['y'], x['rank'], 1 if x['above'] else 0, x['sec']] for x in f}
        await b2.close()
        await b.close()
    data['pre'] = {'meta': {k: P[k] for k in ('today', 'window', 'tomorrow')}, 'days': days, 'items': P['items'], 'phone': seen, 'desktop': desk}
    save(data)
    return data


# ------------------------------------------------------------------ the task module on the phone
TASK_MEASURE = r"""() => {
  const vis = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  IA.scrollTop();
  const v = document.querySelector('.view.on'), F = IA.fold(), txt = el => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
  const RS = '.t2-row, .td-card, .f-row, .tk-row, .tkrow, tr.tk, .task-row, li.tk', scope = v.querySelector('.td-do') || v;
  const rows = [...scope.querySelectorAll(RS)].filter(vis).filter(r => !r.parentElement.closest(RS));
  const btns = [...v.querySelectorAll('button, a.btn, input[type=checkbox], select, summary')].filter(vis);
  const small = btns.filter(b => { const r = b.getBoundingClientRect(); return r.top < F && (r.height < 44 || r.width < 44) && r.width > 0; });
  const cut = [...v.querySelectorAll('*')].filter(e => vis(e) && e.children.length === 0 && e.scrollWidth > e.clientWidth + 2 && /hidden|clip/.test(getComputedStyle(e).overflow + getComputedStyle(e).textOverflow + getComputedStyle(e).overflowX)).map(txt).filter(Boolean).slice(0, 8);
  const tiny = [...new Set([...v.querySelectorAll('span, small, em, div, b, a, button')].filter(e => vis(e) && e.children.length === 0 && txt(e) && parseFloat(getComputedStyle(e).fontSize) < 12.5).map(e => txt(e).slice(0, 30)))].slice(0, 10);
  const first = [...v.querySelectorAll('h1, h2, h3, .td-l1, .t2-title, b')].filter(vis).filter(e => e.getBoundingClientRect().top >= 0).slice(0, 4).map(e => txt(e).slice(0, 60));
  const rowInfo = rows.slice(0, 12).map(r => { const b = r.getBoundingClientRect();
    const ctl = [...r.querySelectorAll('button, a.btn, input[type=checkbox], select')].filter(vis).map(c => (c.type === 'checkbox' ? '[checkbox]' : (c.getAttribute('aria-label') || txt(c) || c.title || '?')).slice(0, 24));
    return { t: txt(r).slice(0, 90), y: Math.round(b.top), h: Math.round(b.height), ctl: ctl, above: b.top < F - 16 }; });
  const newBtn = btns.find(b => /^(new task|add task|\+ ?task|add)$/i.test(txt(b)) || b.id === 'tk-new');
  const nb = newBtn ? newBtn.getBoundingClientRect() : null;
  return { heading: (([...v.querySelectorAll('h1,h2')].find(vis) || {}).textContent || '').trim().slice(0, 50), first: first, fold: F, pageH: Math.round(v.scrollHeight),
    rows: rows.length, rowsAbove: rowInfo.filter(r => r.above).length, firstRowY: rowInfo[0] ? rowInfo[0].y : null, rowInfo: rowInfo,
    smallTargets: small.length, smallEx: small.slice(0, 6).map(b => (txt(b) || b.getAttribute('aria-label') || '?').slice(0, 20) + ' ' + Math.round(b.getBoundingClientRect().width) + 'x' + Math.round(b.getBoundingClientRect().height)),
    cut: cut, tiny: tiny, newTask: nb ? { y: Math.round(nb.top), label: txt(newBtn) } : null, sw: document.documentElement.scrollWidth,
    empty: [...v.querySelectorAll('.empty')].filter(vis).map(txt).slice(0, 2), words: txt(v).split(' ').length };
}"""
OPEN_ROW = r"""() => {
  const vis = el => !!el && el.getClientRects().length > 0;
  const RS = '.t2-row, .td-card, .f-row, .tk-row';
  const r = [...document.querySelectorAll('.view.on ' + RS.split(', ').join(', .view.on '))].filter(vis)[0];
  if (!r) return null;
  const t = [...r.querySelectorAll('[data-t2open], .t2-title, .t2-t, .td-l1, .td-txt, b, .grow')].find(vis) || r;
  const before = view;
  t.click();
  return { clicked: (t.innerText || '').slice(0, 50), before: before };
}"""
SHEET = r"""() => {
  const vis = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  const m = ['#mbm', '.sheet.open', '.drawer.open', '#drawer.open', '.modal.open', '.t2-sheet', '#tk-sheet', '.tk-detail'].map(s => document.querySelector(s)).find(vis);
  const root = m || document.querySelector('.view.on');
  const txt = el => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
  const ctl = [...root.querySelectorAll('button, select, input, a.btn')].filter(vis).map(c => (c.tagName === 'SELECT' ? '[select ' + (c.getAttribute('aria-label') || c.id || c.name || (c.previousElementSibling && txt(c.previousElementSibling)) || '') + ']' : c.type === 'checkbox' ? '[checkbox]' : c.tagName === 'INPUT' ? '[input ' + (c.placeholder || c.type) + ']' : txt(c) || c.getAttribute('aria-label') || '').slice(0, 30)).filter(Boolean);
  return { sheet: !!m, view: view, title: m ? txt(m).slice(0, 80) : '', controls: ctl.slice(0, 30),
    assign: ctl.some(c => /assign|owner|hand|reassign|offer|who/i.test(c)), done: ctl.some(c => /done|complete|\[checkbox\]/i.test(c)), due: ctl.some(c => /due|date|tomorrow|today/i.test(c)) };
}"""


async def tasks():
    data = load()
    res = []
    async with async_playwright() as p:
        b, pg, errs = await boot(p, True)
        # the task list's filters are shared page state (t2View, tkWho): each screen starts from what a fresh
        # sign-in shows, so a filter pressed on one screen does not carry into the next
        for uid, v, tab, label in TASK_SCREENS:
            await reset_lists(pg)
            await sign_in(pg, uid)
            await open_view(pg, v)
            if tab:
                ok = await pg.evaluate(f"l => {{ const b = [...document.querySelectorAll('.view.on :is({QUEUE_TABS})')].find(b => b.getClientRects().length && (b.getAttribute('aria-label') || b.title || b.textContent || '').replace(/\\s+/g, ' ').replace(/\\s*\\d+$/, '').trim().toLowerCase().startsWith(l.toLowerCase())); if (b) b.click(); return !!b; }}", tab)
                await pg.wait_for_timeout(200)
            await pg.evaluate("() => IA.scrollTop()")
            m = await pg.evaluate(TASK_MEASURE)
            slug = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')
            await pg.screenshot(path=os.path.join(OUT, f'task_{slug}.png'))
            await pg.screenshot(path=os.path.join(OUT, f'task_{slug}_full.png'), full_page=True)
            # one tap on the first row: what opens, and whether it holds done, due and hand-off
            o = await pg.evaluate(OPEN_ROW)
            await pg.wait_for_timeout(350)
            sh = await pg.evaluate(SHEET) if o else None
            if sh and sh['sheet']:
                await pg.screenshot(path=os.path.join(OUT, f'task_{slug}_open.png'))
            await pg.evaluate("() => { try { mbCloseModal && mbCloseModal(); } catch (e) {} document.querySelectorAll('.sheet.open, .drawer.open').forEach(e => e.classList.remove('open')); }")
            m.update({'uid': uid, 'view': v, 'tab': tab, 'label': label, 'shot': f'task_{slug}.png', 'open': o, 'sheet': sh})
            res.append(m)
            print(f'tasks: {label}: rows {m["rows"]}, above fold {m["rowsAbove"]}, first row y {m["firstRowY"]}', flush=True)
        # every role's first screen on the phone, for the clutter read
        for uid in ORDER:
            await reset_lists(pg)
            await sign_in(pg, uid)
            await pg.wait_for_timeout(250)
            await pg.evaluate("() => IA.scrollTop()")
            await pg.screenshot(path=os.path.join(OUT, f'first_{ROLE[uid]}.png'))
        await b.close()
    data['tasks'] = res
    save(data)
    return data


# ------------------------------------------------------------------ the tables
def load():
    if os.path.exists(DATA):
        with open(DATA) as f: return json.load(f)
    return {}


def save(d):
    os.makedirs(OUT, exist_ok=True)
    with open(DATA, 'w') as f: json.dump(d, f, separators=(',', ':'))


_LABELS = {}


def labels(r):
    """view -> the name a person sees in the menu; a name two views share is told apart by its menu group
    ("Today › Tasks", "Projects › Tasks"); a page with no menu entry goes by its heading and view id"""
    key = id(r)
    if key in _LABELS: return _LABELS[key]
    m = r.get('menu') or {}
    if m.get('field'): pairs = [('Bar', i) for i in m.get('bar', [])] + [('Menu', i) for i in m.get('rest', [])]
    else: pairs = [(g['n'], i) for g in m.get('groups', []) for i in g['items']]
    pairs += [('More', i) for i in m.get('more', [])] + [('Settings', i) for i in m.get('bottom', [])] + [('Bar', i) for i in m.get('phone', [])]
    first = {}
    for g, it in pairs:
        k, _, l = it.partition('=')
        v = k.split(':')[0]
        if v not in first or (':' not in k and ':' in first[v][2]): first[v] = (g, l, k)
    uses = defaultdict(set)
    for v, (g, l, k) in first.items(): uses[l].add(v)
    out = {v: (f'{g} › {l}' if len(uses[l]) > 1 else l) for v, (g, l, k) in first.items()}
    for s in r.get('screens', []):
        if s and s.get('name') and '[' not in s['name'] and s['name'] not in out:
            out[s['name']] = f"{s.get('heading') or s['name']} ({s['name']})"
    _LABELS[key] = out
    return out


def daily(r):
    """a role's daily pages: its first page, its phone bar, the head of each menu group (field: the bar and the menu)"""
    m = r.get('menu') or {}
    if m.get('field'): items = m.get('bar', []) + m.get('rest', [])
    else: items = m.get('phone', []) + [g['items'][0] for g in m.get('groups', []) if g.get('items')]
    out = {r['first']} | {it.split('=')[0].split(':')[0] for it in items}
    if not m:  # the client portal: every page it has
        out |= {s['name'] for s in r['screens'] if '[' not in s['name']}
    return out


def label_of(r, v):
    base, _, tab = v.partition('[')
    return labels(r).get(base, base) + (' [' + tab if tab else '')


def chrome_keys(r):
    """records whose words match on so many screens that they are the page's furniture, not a list (left out)"""
    from collections import Counter
    cnt, n = Counter(), 0
    for s in r['screens']:
        if not s or 'found' not in s or '[' in s['name']: continue
        n += 1
        for k in {f[0] for f in s['found']}: cnt[k] += 1
    return {k for k, c in cnt.items() if c >= max(10, 0.4 * n)}


def places(r, nouns=None):
    """noun -> {place(screen > section): set(keys)}; screen-level too"""
    P = defaultdict(lambda: defaultdict(set))
    S = defaultdict(lambda: defaultdict(set))
    noise = chrome_keys(r)
    for s in r['screens']:
        if not s or 'found' not in s or s['name'].split('[')[0] in REFERENCE: continue
        scr = label_of(r, s['name'].split('[')[0])
        for k, sec, y, rank, above in s['found']:
            n = k.split(':')[0]
            if (nouns and n not in nouns) or k in noise: continue
            P[n][f'{scr} › {sec}'].add(k)
            S[n][scr].add(k)
    return P, S


GENERIC = {'all', 'open', 'done', 'everything', 'mine', 'everyone', 'unassigned', 'list', 'board', 'new', 'accepted', 'fixed', 'other', 'this week', 'team'}


def number_clash(r):
    """the same label showing different numbers on different screens: tabs and section counts (a filter word that
    names no noun, such as All or Done, is left out)"""
    seen = defaultdict(set)
    for s in r['screens']:
        if not s or 'tabs' not in s: continue
        scr = label_of(r, s['name'].split('[')[0])
        for t in s['tabs']:
            if t['n'] is not None and t['l'] and t['l'].lower() not in GENERIC: seen[t['l'].lower()].add((t['n'], scr))
        for c in s['secs']:
            if c['n'] is not None and c['h'] and c['h'] != '(page)' and c['h'].lower() not in GENERIC: seen[c['h'].lower()].add((c['n'], scr))
    out = []
    for lab, vals in seen.items():
        # a count that moves with a filter on the same screen (Do Now under each tab) is not a clash: two screens are
        by = defaultdict(set)
        for n, scr in vals: by[scr].add(n)
        if len(by) > 1 and len({n for n, _ in vals}) > 1 and any(by[a] != by[b] for a in by for b in by if a != b):
            out.append((lab, sorted(vals)))
    return out


def report():
    D = load()
    W, CAT = D.get('walk', {}), D.get('catalog', {})
    L = ['# Information map: the tables', '', f'Generated by `tests/ia_map.py --report` from `review/ia/data.json`. Demo data, app day {D.get("pre", {}).get("meta", {}).get("today", "2026-09-03")}.', '']
    # 1. per role: screens walked, records in the catalog
    L += ['## 1. Screens walked', '', '| Role | First page | Pages (desktop) | Screens incl. filters (desktop / phone) | Phone bar |', '|---|---|---|---|---|']
    for u in ORDER:
        d, ph = W.get('desktop', {}).get(u), W.get('phone', {}).get(u)
        if not d: continue
        L.append(f"| {WHO[u]} | {label_of(d, d['first'])} | {len([s for s in d['screens'] if '[' not in s['name']])} | {len(d['screens'])} / {len(ph['screens']) if ph else '-'} | {', '.join(ph['bar']) if ph else ''} |")
    # 2. duplication: per role and screen size, each noun's places
    L += ['', '## 2. Where each noun shows, per role', '',
          'Places = distinct screens (sections in brackets) where at least one record of the noun is listed. "Shown twice+" = records of the noun that appear on two or more screens. Mine = records owned by or waiting on this person.', '']
    summary = {}
    for u in ORDER:
        for key in ('desktop', 'phone'):
            r = W.get(key, {}).get(u)
            if not r: continue
            P, S = places(r)
            mine_keys = {c['k'] for c in CAT.get(u, []) if c.get('who') in (u, ROLE[u])}
            summary[(u, key)] = {n: (len(S[n]), sum(len(v) for v in P[n].values()), len(P[n])) for n in S}
            if key == 'desktop' or True:
                L += [f'### {WHO[u]}, {key}', '', '| Noun | Screens | Sections | Records shown | Shown on 2+ screens | Screens (top 8 by records) |', '|---|---|---|---|---|---|']
                for n in NOUN:
                    if n not in S: continue
                    allk = set().union(*S[n].values())
                    multi = {k for k in allk if sum(1 for v in S[n].values() if k in v) > 1}
                    top = sorted(S[n].items(), key=lambda kv: -len(kv[1]))[:8]
                    L.append(f"| {NOUN[n]} | {len(S[n])} | {len(P[n])} | {len(allk)} | {len(multi)} | {'; '.join(f'{scr} ({len(ks)})' for scr, ks in top)} |")
                L.append('')
    # 2a. the matrix: screens per noun per role
    L += ['## 2a. Screens per noun, per role (desktop / phone)', '', '| Noun | ' + ' | '.join(WHO[u].split(' (')[0] for u in ORDER) + ' |', '|---|' + '---|' * len(ORDER)]
    for n in NOUN:
        cells = []
        for u in ORDER:
            d, ph = W.get('desktop', {}).get(u), W.get('phone', {}).get(u)
            a = len(places(d)[1].get(n, {})) if d else 0
            b = len(places(ph)[1].get(n, {})) if ph else 0
            cells.append('-' if not a and not b else f'{a} / {b}')
        L.append(f'| {NOUN[n]} | ' + ' | '.join(cells) + ' |')
    L.append('')
    # 3. question clusters
    L += ['## 3. Places that answer the same question', '', 'For each question, the number of distinct screens (sections) that list records answering it. One place per question is the target; Today plus the full list behind it counts as two.', '',
          '| Role | ' + ' | '.join(QUESTIONS) + ' |', '|---|' + '---|' * len(QUESTIONS)]
    clusters = {}
    for u in ORDER:
        cells = []
        for q, ns in QUESTIONS.items():
            vals = []
            for key in ('desktop', 'phone'):
                r = W.get(key, {}).get(u)
                if not r: vals.append('-'); continue
                P, S = places(r, set(ns))
                scr = set().union(*[set(S[n].keys()) for n in ns]) if any(n in S for n in ns) else set()
                sec = set().union(*[set(P[n].keys()) for n in ns]) if any(n in P for n in ns) else set()
                clusters[(u, key, q)] = (len(scr), len(sec))
                vals.append(f'{len(scr)} ({len(sec)})')
            cells.append(' / '.join(vals))
        L.append(f'| {WHO[u]} | ' + ' | '.join(cells) + ' |')
    L += ['', 'Cells: desktop screens (sections) / phone screens (sections).', '']
    # 4. one question, one number
    L += ['## 4. One label, two numbers', '', 'The same tab or section label showing different counts on different screens of the same role.', '']
    for u in ORDER:
        for key in ('desktop', 'phone'):
            r = W.get(key, {}).get(u)
            if not r: continue
            cl = number_clash(r)
            if not cl: continue
            L.append(f'- **{WHO[u]}, {key}:** ' + '; '.join(f'"{lab}" ' + ', '.join(f'{n} on {scr}' for n, scr in vals[:4]) for lab, vals in cl[:8]))
    # 5. precursors
    pre = D.get('pre')
    if pre:
        L += ['', '## 5. Delay precursors', '', f"As of {pre['meta']['today']}; window to {pre['meta']['window']} (10 working days). For each person who must act: rank and y on their first screen on the phone today (above the fold or not), the same on the desktop, and the earliest day in the scan ({pre['days'][0]} to {pre['days'][-1]}) it was on their first screen at all, in working days before it is due.", '',
              '| Precursor | Kind | Due | Who acts | Phone first screen today | Desktop first screen | First shown | Other places (desktop) | Gap |', '|---|---|---|---|---|---|---|---|---|']
        days = pre['days']
        for it in sorted(pre['items'], key=lambda x: (x['due'], x['kind'])):
            for a in it['actors']:
                ph = pre['phone'].get(a, {}).get(pre['meta']['today'], {}).get(it['k'])
                dk = pre['desktop'].get(a, {}).get(it['k'])
                shown = [d for d in days if it['k'] in pre['phone'].get(a, {}).get(d, {})]
                first = shown[0] if shown else None
                lead = (days.index(it['due']) - days.index(first)) if (first and it['due'] in days) else None
                r = W.get('desktop', {}).get(a)
                other = []
                if r:
                    for s in r['screens']:
                        if any(f[0] == it['k'] for f in s.get('found', [])) and s['name'] != r['first'] and s['name'].split('[')[0] not in REFERENCE:
                            other.append(label_of(r, s['name']))
                gaps = []
                if not ph: gaps.append('not on first screen (phone)')
                elif not ph[2]: gaps.append(f'below the fold (y {ph[0]})')
                if first is None: gaps.append('never on first screen in the scan')
                elif first >= it['due'] and it['due'] >= days[0]: gaps.append('only once due or late')
                if not other and not ph and not dk: gaps.append('NOT ON ANY SCREEN of this person')
                L.append(f"| {it['t'][:48]} | {it['kind']} | {it['due']} | {WHO.get(a, a)} | {f'#{ph[1]} y{ph[0]} ' + ('above' if ph[2] else 'below') + ' fold' if ph else '-'} | {f'#{dk[1]} y{dk[0]}' if dk else '-'} | {first or '-'}{f' ({lead} wd ahead)' if lead is not None and lead > 0 else ''} | {len(set(other))}: {', '.join(sorted(set(other))[:4])} | {'; '.join(gaps) or 'ok'} |")
    # 6. task module
    if D.get('tasks'):
        L += ['', '## 6. Task screens on the phone (390 x 844)', '', '| Screen | First thing seen | Rows | Rows above fold | First row y | Row controls (first row) | One tap on a row opens | Small targets | Cut off |', '|---|---|---|---|---|---|---|---|---|']
        for t in D['tasks']:
            r0 = t['rowInfo'][0] if t['rowInfo'] else None
            sh = t.get('sheet') or {}
            opened = ('sheet: ' + ', '.join(k for k in ('done', 'due', 'assign') if sh.get(k))) if sh.get('sheet') else (f"page {sh.get('view')}" if sh else '-')
            L.append(f"| {t['label']} | {' / '.join(t['first'][:2])[:70]} | {t['rows']} | {t['rowsAbove']} | {t['firstRowY']} | {', '.join(r0['ctl']) if r0 else (t['empty'][0][:50] if t['empty'] else '-')} | {opened} | {t['smallTargets']} | {'; '.join(t['cut'][:3])[:60]} |")
    # 7. clutter, phone
    L += ['', '## 7. Clean pages: the daily pages on the phone', '', "Each role's daily pages (the phone bar, the head of each menu group, the first page): page height in screens of 844px, sections (cards with a heading), sections starting above the fold, top-level visual groups, empty or near-empty cards, words on the page, internal words (and, for the field and the client, office or finance words). Every other page is in data.json.", '',
          '| Role | Page | Height (screens) | Sections | Above fold | Groups | Empty cards | Words | Internal words |', '|---|---|---|---|---|---|---|---|---|']
    tall = defaultdict(int)
    for u in ORDER:
        r = W.get('phone', {}).get(u)
        if not r: continue
        for s in r['screens']:
            if '[' not in s['name'] and 'pageH' in s and s['pageH'] > 3 * 844: tall[u] += 1
        for s in r['screens']:
            if '[' in s['name'] or 'secs' not in s or s['name'] not in daily(r): continue
            secs = [c for c in s['secs'] if c['h'] != '(page)']
            emp = [c['h'] for c in secs if c['empty']]
            jar = s['jargon'] + (s['fieldJargon'] if ROLE[u] in ('foreman', 'crew', 'driver', 'client') else [])
            L.append(f"| {WHO[u]} | {label_of(r, s['name'])} | {round(s['pageH'] / 844, 1)} | {len(secs)} | {s['above']} | {s['groups']} | {len(emp)}{': ' + ', '.join(emp[:3]) if emp else ''} | {s['words']} | {', '.join(sorted(set(jar))[:6])} |")
    L += ['', 'Pages taller than three phone screens, of all the pages each role may open: ' + '; '.join(f"{WHO[u]} {tall[u]} of {len([s for s in W['phone'][u]['screens'] if '[' not in s['name']])}" for u in ORDER if u in W.get('phone', {})) + '.']
    # 8. headline numbers
    L += ['', '## 8. Headline numbers', '', '| Role | Open to-dos: screens (desktop / phone) | Approvals and decisions: screens | Materials to buy: screens | Pages the role may open | Daily pages |', '|---|---|---|---|---|---|']
    for u in ORDER:
        d, ph = W.get('desktop', {}).get(u), W.get('phone', {}).get(u)
        if not d or not ph: continue
        Sd, Sp = places(d)[1], places(ph)[1]
        ad = len(set(Sd.get('approval', {})) | set(Sd.get('decision', {}))); ap = len(set(Sp.get('approval', {})) | set(Sp.get('decision', {})))
        L.append(f"| {WHO[u]} | {len(Sd.get('task', {}))} / {len(Sp.get('task', {}))} | {ad} / {ap} | {len(Sd.get('material', {}))} / {len(Sp.get('material', {}))} | {len([s for s in d['screens'] if '[' not in s['name']])} | {len(daily(d))} |")
    with open(os.path.join(OUT, 'tables.md'), 'w') as f: f.write('\n'.join(L) + '\n')
    print('wrote review/ia/tables.md', len(L), 'lines')


# ------------------------------------------------------------------ the checks (map.md "Checks"): each fails today
# ONE_PLACE: for each role, the one list a noun lives in (plus the role's first page, which is the one queue). A noun
# found on any other screen of that role is a second place. Encoded from map.md's consolidation proposal.
QUEUE = {'owner': {'home'}, 'pm': {'home'}, 'coord': {'home'}, 'billing': {'home', 'billing'}, 'controller': {'home', 'bank'}, 'designer': {'sday'}, 'foreman': {'ftoday'}, 'crew': {'time'}, 'driver': {'route'}, 'client': {'client', 'dec'}}
ONE_PLACE = {
    # the register (the one list) and, for a yes/no or a to-do, the full list behind its Today filter
    'task': {'tkall', 'tasks'},            # Projects › Tasks stays only as Tasks filtered to the job (same rows, same counts)
    'approval': {'mapprove'}, 'inbox': {'comms'},
    # the job's Overview (dash, the look-ahead) is the job's own "what is coming": it may list what threatens the job
    'decision': {'dec', 'mapprove', 'dash'}, 'submittal': {'subm', 'mapprove', 'dash'}, 'siteq': {'mapprove', 'field', 'fraise', 'dash'},
    'request': {'req', 'mapprove', 'dash'}, 'bill': {'ap', 'mapprove'}, 'coi': {'vendors', 'mapprove'},
    'material': {'proc', 'mat', 'dash'},   # Materials stays only as the Buy Board filtered to the job
    'inspection': {'insp', 'dash'}, 'invoice': {'billing', 'clacct'}, 'po': {'po', 'recv'},
    'flag': set(), 'finding': set(),       # Caught for You on the first page is their one place
    'sched': {'sched', 'dash', 'fsite'},   # the schedule and the job's look-ahead; the foreman's Site
    'subconfirm': {'fsite', 'sched'},
}
# pages where a record's name is context, not a list of work: a bank or ledger line names its vendor, PO or bill; the
# calendar is a time view of dated records; a client's or job's settings page names its job
CONTEXT_OK = {'proj', 'clients', 'port', 'ovjobs', 'calendar', 'bank', 'spend', 'gl', 'verify', 'reports'}


def check():
    D = load()
    c = Checks()
    W = D.get('walk', {})
    for key in ('desktop', 'phone'):
        for u in ORDER:
            r = W.get(key, {}).get(u)
            if not r: continue
            rl = ROLE[u]
            P, S = places(r)
            for n, scrs in S.items():
                allowed = ONE_PLACE.get(n, set()) | QUEUE.get(rl, set())
                extra = []
                for s in r['screens']:
                    base = s['name'].split('[')[0]
                    if base in allowed or base in CONTEXT_OK or base in REFERENCE: continue
                    if any(f[0].split(':')[0] == n for f in s.get('found', [])): extra.append(label_of(r, s['name']))
                c.ok(not extra, f'ONE PLACE {key} {WHO[u]}: {NOUN.get(n, n)} also listed on {sorted(set(extra))[:6]}')
            cl = number_clash(r)
            c.ok(not cl, f'ONE NUMBER {key} {WHO[u]}: {[(lab, vals[:3]) for lab, vals in cl[:4]]}')
            # the phone's first page: no empty card above the fold, at most 4 sections above the fold
            if key == 'phone':
                s0 = next((s for s in r['screens'] if s['name'] == r['first']), None)
                if s0 and 'secs' in s0:
                    emp = [x['h'] for x in s0['secs'] if x['empty'] and x['y'] < s0['fold']]
                    c.ok(not emp, f'CLEAN phone {WHO[u]} first page: empty cards above the fold {emp}')
                    c.ok(s0['pageH'] <= 3 * 844, f'CLEAN phone {WHO[u]} first page is {round(s0["pageH"] / 844, 1)} screens tall (want 3 at most)')
                    jar = s0['jargon'] + (s0['fieldJargon'] if rl in ('foreman', 'crew', 'driver', 'client') else [])
                    c.ok(not jar, f'WORDS phone {WHO[u]} first page: {jar}')
    pre = D.get('pre')
    if pre:
        t = pre['meta']['today']
        for it in pre['items']:
            for a in it['actors']:
                ph = pre['phone'].get(a, {}).get(t, {}).get(it['k'])
                c.ok(bool(ph), f'PRECURSOR {it["kind"]} "{it["t"][:40]}" (due {it["due"]}) is not on {WHO.get(a, a)}\'s first screen')
                if ph: c.ok(ph[2] == 1, f'PRECURSOR {it["kind"]} "{it["t"][:40]}" is below the fold on {WHO.get(a, a)}\'s phone (y {ph[0]})')
                shown = [d for d in pre['days'] if it['k'] in pre['phone'].get(a, {}).get(d, {})]
                if it['due'] in pre['days'] and it['due'] != pre['days'][0]:
                    lead = pre['days'].index(it['due']) - pre['days'].index(shown[0]) if shown else None
                    when = 'is never on the first screen in the scan' if lead is None else f'first shows {lead} working days before it is due' if lead >= 0 else f'first shows {-lead} working days after it was due'
                    c.ok(lead is not None and lead >= 3, f'PRECURSOR LEAD {it["kind"]} "{it["t"][:40]}" {when}, for {WHO.get(a, a)} (want 3+ ahead)')
    for t in D.get('tasks', []):
        c.ok(t['rowsAbove'] >= 3 or t['rows'] < 3, f'TASKS phone {t["label"]}: {t["rowsAbove"]} task rows above the fold (want 3+)')
        c.ok(t['smallTargets'] == 0, f'TASKS phone {t["label"]}: {t["smallTargets"]} targets under 44px above the fold {t["smallEx"][:3]}')
        # a task list must not open empty while work is due in the next seven days
        soon = sum(int(m) for m in re.findall(r'Next 7 Days(\d+) ', ' '.join(t['smallEx'])))  # the tab's badge, glued to its label (then its size)
        if not t['tab']: c.ok(t['rows'] > 0 or not soon, f'TASKS phone {t["label"]}: opens empty ("{(t["empty"] or [""])[0][:40]}") while {soon} are due in the next 7 days')
        sh = t.get('sheet') or {}
        if t['rows']: c.ok(bool(sh.get('sheet')) and sh.get('assign') and sh.get('done') and sh.get('due'), f'TASKS phone {t["label"]}: one tap on a task opens a sheet with done, due and hand-off ({sh})')
    return c.done()


async def main():
    a = sys.argv[1:]
    users = ORDER
    if '--user' in a: users = a[a.index('--user') + 1].split(',')
    if '--check' in a: return check()
    steps = [x for x in ('--walk', '--pre', '--tasks', '--report') if x in a] or ['--walk', '--pre', '--tasks', '--report']
    os.makedirs(OUT, exist_ok=True)
    if '--walk' in steps: await walk(users)
    if '--pre' in steps: await precursors()
    if '--tasks' in steps: await tasks()
    if '--report' in steps: report()
    return 0

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
