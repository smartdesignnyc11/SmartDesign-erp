"""module_census: every module, page by page (Alan, 2026-10-26). A measurement, not a fix: it changes no app code.

"Go through all the modules with screenshots. It's important to understand the format of every page and what's on
it." The Projects module has its own census (tests/projects_census.py, docs/modules/projects_census.md); this one
extends it to every other module, in the same format, so the loop's experts (owner, PM, procurement, accounting) and
the client expert walk every page of their modules with it in hand (docs/IMPROVEMENT_LOOP.md, round one).

A page belongs to the module whose menu group holds it (the running menu, mnMap(), not the source's MENU: later
sections add groups). The few pages a menu group shares are placed by noun: Time & Crew is Time and Payroll wherever it
sits, Billing (with no tab) is Billing, Tasks, Meetings and Messages are Tasks and Messages, and More and Settings
place each page by its noun (MOD_OF_VIEW). Field roles' menus place their own pages under Field and Site.

For every role, at 1440 and at 390, on a fresh app (each role a new device: a page a tab press saved never reaches
the next role), it
  1. reads the role's menu as the entries a person taps (CMOD.entries: rail groups, their strips, More, Settings, the
     phone bar, the field roles' and the client's own menus);
  2. for each module, reaches each of its pages the way the person does (CMOD.go: the phone bar, else the menu, the
     hamburger on the phone, the group, then the strip; a swipe recorded when the strip entry sits off screen);
  3. reads the page (the projects census's reader, tests/census_js.js, on the information map's, tests/ia_js.js, plus
     this census's nouns and the first button, tests/module_census_js.js), presses every tab of every tab group and
     the tabs those reveal (words that commit are never pressed), and shoots every screen;
  4. follows the page's own links to pages of the same module the menu did not reach;
Then, per module, it writes docs/modules/<module>_census.md (the tree, duplications and disagreements, empty and dead
pages, the phone, page by page, the other roles), review/census/<module>/data.json and tables.md and shots/, and
docs/modules/README.md (one row per module, the Projects census's data included).

  python3 module_census.py                          walk every module and report (run it through tests/slot.sh)
  python3 module_census.py --walk|--report          one step (report reads review/census/*/data.json)
  python3 module_census.py --module sales,billing   some modules (walk; the report always covers every module walked)
  python3 module_census.py --user u_owner --device phone   one role, one device (merged into data.json)
  python3 module_census.py --no-shots               no screenshots
  python3 module_census.py --dry                    one role, one device, one module, into review/census/_dry/
"""
import asyncio, json, os, re, subprocess, sys, time
from collections import defaultdict, Counter
from harness import *
import projects_census as PC
from projects_census import (CJS, IA_JS, close_sheets, settle, compact, read, Walker, secs_of, above, screens_tall,
                             fig_key, close, esc, flags_of, rec_line, page_block, page_of, tab_label, reset_lists, DEVS)

HERE = os.path.dirname(os.path.abspath(__file__))
MJS = open(os.path.join(HERE, 'module_census_js.js')).read()
CENSUS = os.path.join(ROOT, 'review', 'census')
DOCS = os.path.join(ROOT, 'docs', 'modules')
USERS = ['u_owner', 'u_alan', 'u_chen', 'u_angel', 'u_sarah', 'u_billing', 'u_controller', 'u_klein', 'u_alberto', 'u_alex']
ROLE_OF = {'u_owner': 'owner', 'u_alan': 'pm', 'u_chen': 'coord', 'u_angel': 'foreman', 'u_alberto': 'crew', 'u_alex': 'driver',
           'u_sarah': 'designer', 'u_billing': 'billing', 'u_controller': 'controller', 'u_klein': 'client'}
ROLE_NAME = PC.ROLE_NAME
FIELD_ROLES = {'u_angel', 'u_alberto', 'u_alex'}
FIRST_JOB = 'p121'
# the modules, in menu order; Projects has its own census (projects_census.py) and is read, not walked, here
MODULES = [
    ('today', 'Today', 'every role', USERS),
    ('sales', 'Sales and Clients', 'the owner', ['u_owner']),
    ('projects', 'Projects', 'the PM', ['u_alan']),
    ('field', 'Field and Site', 'the foreman and the PM', ['u_angel', 'u_alan']),
    ('design', 'Design', 'the designer and the PM', ['u_sarah', 'u_alan']),
    ('purchasing', 'Purchasing', 'the coordinator', ['u_chen']),
    ('billing', 'Billing', 'billing', ['u_billing']),
    ('accounting', 'Accounting', 'the controller', ['u_controller']),
    ('timepay', 'Time and Payroll', 'the controller, the coordinator and the crew', ['u_controller', 'u_chen', 'u_alberto']),
    ('tasks', 'Tasks and Messages', 'every office role', ['u_owner', 'u_alan', 'u_chen', 'u_sarah', 'u_billing', 'u_controller']),
    ('company', 'Company and Settings', 'the owner', ['u_owner']),
    ('client', 'The Client Portal', 'the client', ['u_klein']),
]
TITLE = {m[0]: m[1] for m in MODULES}
PRIMARY = {m[0]: m[3] for m in MODULES}
PRIMARY_TXT = {m[0]: m[2] for m in MODULES}
WALKED = [m[0] for m in MODULES if m[0] != 'projects']
# an office menu group's module
GROUP_MOD = {'home': 'today', 'mytasks': 'tasks', 'msgs': 'tasks', 'jobs': 'projects', 'money': 'accounting', 'sales': 'sales',
             'clients': 'sales', 'buy': 'purchasing', 'studio': 'design', 'drawings': 'design', 'office': 'company',
             'reports': 'accounting', 'billing': 'billing', 'bank': 'accounting', 'ap': 'accounting', 'gl': 'accounting',
             'setup': 'company'}
# a page's module by its noun: More and Settings, links, and the pages a group shares
MOD_OF_VIEW = {}
for _m, _vs in {
    'today': 'home sday ftoday mapprove comms cos',
    'sales': 'ovsales salesnum partners playbook hbcontacts hbcompanies hbtasks hbforecast hbdash hbdeals hbworkspace hbsequences hbquotes hbplaybooks leads scleads clients',
    'projects': 'ovjobs port dash proj sched tasks dec subm insp field mat costs inbox files photos',
    'field': 'fsite flog fcrew req fraise route',
    'design': 'ovstudio studio sboard sdraw plans sfile sel',
    'purchasing': 'ovbuy proc rfq po recv vendors inv',
    'billing': 'billing',
    'accounting': 'ovmoney ap bank spend gl verify budget reports dashboard',
    'timepay': 'time',
    'tasks': 'tkall meetings chat',
    'company': 'ovoffice calendar team brain obligations setup conn standard rpbox rdata hbsettings',
    'client': 'client clacct',
}.items():
    for _v in _vs.split(): MOD_OF_VIEW[_v] = _m
# Settings (setup) holds the company's own switches (basis, entities, rules) in rows of buttons; the job's settings
# likewise. They are read, never pressed.
NO_PRESS = {'setup', 'proj', 'hbsettings'}
MAX_LINKS = 10
# a link to another module's page that belongs to this one: Settings' Company Settings tile opens the job's settings
# page in its company mode (users, entities, approval rules, the company block)
EXTRA_LINKS = {('company', 'setup', 'proj'): 'Company Settings'}
WAIT = 180
# nouns that are names: a page that writes the name counts as listing it, so they are kept out of "the same list twice"
NAMES = {'client', 'vendor', 'lead', 'contact', 'company', 'partner', 'employee'}
NOUN = dict(PC.NOUN)
NOUN.update({'client': 'clients', 'vendor': 'vendors', 'lead': 'leads', 'contact': 'contacts', 'company': 'companies',
             'payroll': 'payroll runs', 'stock': 'stock items', 'meeting': 'meetings', 'obligation': 'obligations',
             'lesson': 'lessons', 'partner': 'partners', 'employee': 'employees', 'journal': 'journal entries',
             'bankline': 'bank and card lines', 'thread': 'message threads'})
PC.NOUN.update(NOUN)   # page_block and rec_line read the projects census's table


def mod_of(uid, e):
    """the module an entry of the role's menu belongs to"""
    v, tab, grp = e['v'], e.get('tab') or '', e.get('grp') or ''
    if uid == 'u_klein':
        return 'client' if v in ('client', 'clacct', 'sched', 'dec', 'chat') else MOD_OF_VIEW.get(v, 'client')
    if uid in FIELD_ROLES:
        if v == 'ftoday': return 'today'
        if v == 'time': return 'timepay'
        if v == 'chat': return 'tasks'
        if v in ('team', 'conn', 'standard'): return 'company'
        return 'field'
    if v == 'time': return 'timepay'
    if v == 'billing':
        if tab and grp == 'jobs': return 'projects'
        if tab == 'estimates' and grp == 'sales': return 'sales'
        return 'billing'
    if v in ('tkall', 'meetings', 'chat'): return 'tasks'
    if v == 'comms': return 'today'
    if grp in ('more', 'setup') or grp not in GROUP_MOD: return MOD_OF_VIEW.get(v, 'company')
    return GROUP_MOD[grp]


def dirs(mod):
    out = os.path.join(CENSUS, mod)
    return out, os.path.join(out, 'shots'), os.path.join(out, 'data.json')


def build_hash():
    try:
        return subprocess.check_output([os.path.join(HERE, 'ledger.sh'), '--hash'], text=True).strip()
    except Exception:
        return '?'


def git_head():
    try:
        return subprocess.check_output(['git', '-C', ROOT, 'rev-parse', '--short', 'HEAD'], text=True).strip()
    except Exception:
        return '?'


async def boot(p, phone):
    b, pg, errs = await open_app(p, phone)
    await pg.evaluate(IA_JS)
    await pg.evaluate(CJS)
    await pg.evaluate(MJS)
    await pg.evaluate("() => { try { window.__iadflt = { v: t2View, w: tkWho }; } catch (e) { window.__iadflt = null; } }")
    return b, pg, errs


class MWalker(Walker):
    """the projects census's walker: the screen's first button and the job on screen added, shots per module and role"""
    def __init__(self, pg, errs, uid, phone, shots):
        super().__init__(pg, errs, uid, phone, shots)
        self.mod = None
        self.shotdir = None

    async def record(self, name, path, req, job, extra=None):
        t0 = time.time()
        n0 = len(self.errs)
        sv0 = await self.pg.evaluate("() => CENSUS.saves")
        await self.pg.evaluate("() => IA.scrollTop()")
        s = compact(await read(self.pg))
        s = s or {'error': 'no view on screen'}
        try:
            fb = await self.pg.evaluate("() => CMOD.firstBtn()")
        except Exception:
            fb = None
        s.update({'name': name, 'path': path, 'req': req, 'job': job, 'ms': int((time.time() - t0) * 1000), 'first': fb})
        s['saves'] = (await self.pg.evaluate("() => CENSUS.saves")) - sv0
        s['errors'] = self.errs[n0:n0 + 3]
        if extra: s.update(extra)
        if self.shots and self.shotdir:
            slug = re.sub(r'[^a-z0-9]+', '_', f'{ROLE_OF[self.uid]}_{name}'.lower()).strip('_')[:90]
            fn = f'{self.dev}_{slug}.jpg'
            base = PHONE if self.phone else DESKTOP
            try:
                h = max(base['height'], min(int(s.get('pageH') or 0) + 260, 5 * 844 if self.phone else 3 * 900))
                if h > base['height']:
                    await self.pg.set_viewport_size({'width': base['width'], 'height': h})
                    await self.pg.wait_for_timeout(150)
                await self.pg.screenshot(path=os.path.join(self.shotdir, fn), type='jpeg', quality=55)
                s['shot'] = fn
            except Exception as e:
                s['shotErr'] = str(e)[:100]
            finally:
                await self.pg.set_viewport_size(base)
                await self.pg.wait_for_timeout(60)
        self.screens.append(s)
        return s

    async def tabs(self, base, path, req, job, groups, depth, seen_groups):
        """the projects census's tab walk, with the tabs it could not press kept on the page (a row of tiles that
        stops being a tab row once one is pressed is walked only as far as it stays one)"""
        start_view = await self.view()
        if depth == 1: seen_groups = [set(g['labels']) for g in groups]
        page = next((s for s in reversed(self.screens) if s['name'] == base), None)
        for g in groups[:6]:
            if self.walked(job, start_view, g['labels']):
                continue
            self.seen[(job, start_view)].append(set(g['labels']))
            on = g['labels'][g['on']] if 0 <= g['on'] < len(g['labels']) else None
            for lab in g['labels'][:PC.MAX_TABS]:
                if lab == on or not lab: continue
                ok = await self.pg.evaluate("([g, l]) => CENSUS.press(g, l)", [g['labels'], lab])
                if not ok:
                    if page is not None: page.setdefault('unpressed', []).append(lab)
                    continue
                await settle(self.pg)
                now = await self.view()
                modal = await self.pg.evaluate("() => { const m = document.querySelector('#mbm'); return !!m && m.getClientRects().length > 0; }")
                nm = f'{base}[{lab}]'
                s = await self.record(nm, path + [lab], req, job, {'tabOf': base, 'tabGroup': g['labels'], 'leftTo': now if now != start_view else '', 'tabModal': modal})
                if modal: await close_sheets(self.pg)
                if now != start_view:
                    await self.open(start_view)
                    continue
                if depth < PC.TAB_DEPTH and 'groups' in s:
                    new = [x for x in s['groups'] if not self.walked(job, start_view, x['labels']) and not self.same(x['labels'], seen_groups)]
                    if new: await self.tabs(nm, path + [lab], req, job, new, depth + 1, seen_groups)
                    await self.pg.evaluate("([g, l]) => CENSUS.press(g, l)", [g['labels'], lab])
            if on:
                await self.pg.evaluate("([g, l]) => CENSUS.press(g, l)", [g['labels'], on])
                await settle(self.pg, 100)

    async def page(self, name, path, req, job, extra=None):
        s = await self.record(name, path, req, job, extra)
        if s.get('view') in NO_PRESS: s['notPressed'] = True
        elif s.get('groups'):
            await self.tabs(name, path, req, job, s['groups'], 1, [])
        return s


async def fresh(pg, uid):
    await close_sheets(pg)
    await reset_lists(pg)
    await pg.evaluate("() => { try { localStorage.removeItem('dashAll'); dashAll = !!(typeof mOn === 'function' && mOn()); } catch (e) {} }")
    await sign_in(pg, uid)
    await settle(pg, 250)
    # every role on the same job where it may open it (121 State Street, the active job and the client's), so the
    # modules list the same job's records for every role
    job = await pg.evaluate("""pid => { let sc = null; try { const x = eqScopeOf(); sc = x && x.pids ? [...x.pids] : null; } catch (e) {}
        if ((!sc || sc.includes(pid)) && DB.projects.some(p => p.id === pid) && S.id !== pid) { try { setCurrent(pid); render(); } catch (e) {} }
        return { id: S.id, name: (S.project || {}).name || '' }; }""", FIRST_JOB)
    await settle(pg, 150)
    return job


async def walk_role(p, uid, phone, mods, shots):
    """one role on one device, on a fresh app: every module page the role's menu reaches, then the links"""
    b, pg, errs = await boot(p, phone)
    try:
        job = await fresh(pg, uid)
        meta = await pg.evaluate("""() => { window.__cecat = CENSUS.catalog().concat(CMOD.extra());
          return { role: role(), first: view, views: ROLE_VIEWS[role()] || [], menu: (typeof mnMap === 'function' && mnOn()) ? mnMap() : null,
                   bar: CENSUS.bar(), entries: CMOD.entries(),
                   cat: window.__cecat.map(o => ({ k: o.k, noun: o.noun, t: o.t, pid: o.pid || '' })) }; }""")
        home = meta['first']
        W = MWalker(pg, errs, uid, phone, shots)
        ents = meta['entries']
        for e in ents: e['mod'] = mod_of(uid, e)
        out = {}
        for mod in mods:
            mine = [e for e in ents if e['mod'] == mod]
            if not mine: continue
            _, sd, _ = dirs(mod)
            os.makedirs(sd, exist_ok=True)
            W.mod, W.shotdir = mod, sd
            n0 = len(W.screens)
            t0 = time.time()
            visited, pages, seen_req = set(), [], set()
            for e in mine:
                key = e['v'] + (':' + e['tab'] if e.get('tab') else '')
                if key in seen_req: continue
                seen_req.add(key)
                await close_sheets(pg)
                # every entry starts from the role's first page, as after a sign-in
                await pg.evaluate("v => { try { setView(v); } catch (e) { view = v; render(); } }", home)
                await settle(pg, 120)
                try:
                    how = await pg.evaluate("e => CMOD.go(e)", e)
                except Exception as x:
                    how = {'taps': ['go failed: ' + str(x)[:80]], 'how': 'none'}
                await settle(pg, 260)
                landed = await W.view()
                others = [f"{x['gname']} › {x['l']}" if x['gname'] != x['l'] else x['l'] for x in ents if x['v'] == e['v'] and x is not e]
                place = f"{e['gname']} › {e['l']}" if e['gname'] != e['l'] else e['l']
                s = await W.page(e['l'], how.get('taps') or [], key, mod, {'how': how.get('how'), 'swipe': bool(how.get('swipe')), 'place': place,
                                                                           'entryPlace': e['place'], 'onBar': bool(e.get('bar')), 'otherPlaces': others,
                                                                           'from': 'menu'})
                visited.add(s.get('view'))
                visited.add(e['v'])
                pages.append({'from': 'menu', 'l': e['l'], 'req': key, 'view': s.get('view'), 'taps': how.get('taps'), 'how': how.get('how'), 'place': place})
            # the pages' own links to the module's pages the menu did not reach
            rv = set(meta['views'])
            followed = 0
            for s in list(W.screens[n0:]):
                if s.get('tabOf'): continue
                for ln in (s.get('links') or []):
                    to = ln['to']
                    extra = (mod, s.get('view'), to) in EXTRA_LINKS
                    if to in visited or to not in rv or to in ('pa',) or followed >= MAX_LINKS: continue
                    if mod_of(uid, {'v': to, 'grp': 'more'}) != mod and not extra: continue
                    visited.add(to)
                    followed += 1
                    await close_sheets(pg)
                    await pg.evaluate("v => { try { setView(v); } catch (e) { view = v; render(); } }", s.get('view'))
                    await settle(pg, 150)
                    ok = await pg.evaluate("([to, t]) => CMOD.follow(to, t)", [to, ln['t']])
                    if not ok:
                        await pg.evaluate("v => { try { setView(v); } catch (e) { view = v; render(); } }", to)
                    await settle(pg, 260)
                    nm = EXTRA_LINKS.get((mod, s.get('view'), to)) or (ln['t'] or to)[:40]
                    s2 = await W.page(nm, [s['name'], 'link: ' + (ln['t'] or to)], to, mod, {'from': 'link', 'linkFrom': s['name'], 'tapped': bool(ok)})
                    pages.append({'from': 'link', 'l': nm, 'req': to, 'view': s2.get('view'), 'via': s['name'], 'tapped': bool(ok)})
            # the role may open a page of this module that no menu entry or followed link reached
            unplaced = sorted(v for v in rv if mod_of(uid, {'v': v, 'grp': 'more'}) == mod and v not in visited and v not in seen_req and v != 'pa' and not v.startswith('mb'))
            out[mod] = {'uid': uid, 'role': meta['role'], 'first': home, 'views': meta['views'], 'menu': meta['menu'], 'bar': meta['bar'],
                        'entries': [e for e in ents], 'pages': pages, 'unplaced': unplaced, 'job': job,
                        'screens': W.screens[n0:], 'secs': int(time.time() - t0), 'cat': meta['cat']}
        return out, None
    except Exception as e:
        return {}, str(e)[:400]
    finally:
        await b.close()


def load(mod):
    _, _, D = dirs(mod)
    if os.path.exists(D):
        with open(D) as f: return json.load(f)
    return {}


def save(mod, d):
    out, _, D = dirs(mod)
    os.makedirs(out, exist_ok=True)
    with open(D, 'w') as f: json.dump(d, f, separators=(',', ':'))


async def walk(users, devices, mods, shots):
    data = {m: load(m) for m in mods}
    for m in mods:
        data[m].setdefault('walk', {})
        data[m]['build'] = build_hash()
        data[m]['head'] = git_head()
    t_all = time.time()
    async with async_playwright() as p:
        for phone in devices:
            key = 'phone' if phone else 'desktop'
            for u in users:
                t0 = time.time()
                r, crash = await walk_role(p, u, phone, mods, shots)
                for m in mods:
                    if crash:
                        data[m]['walk'].setdefault(key, {})[u] = {'uid': u, 'crash': crash, 'screens': []}
                    elif m in r:
                        x = r[m]
                        data[m].setdefault('catalog', {}).setdefault(key, {})[u] = x.pop('cat', [])
                        data[m]['walk'].setdefault(key, {})[u] = x
                    else:
                        data[m]['walk'].setdefault(key, {}).pop(u, None)
                n = sum(len(x.get('screens', [])) for x in r.values())
                print(f'{key} {u}: {n} screens in {len(r)} modules, {int(time.time() - t0)}s' + (f' CRASH {crash}' if crash else ''), flush=True)
                for m in mods: save(m, data[m])
    wall = int(time.time() - t_all)
    for m in mods:
        if '--user' not in sys.argv: data[m]['walkWall'] = wall
        data[m]['built'] = time.strftime('%Y-%m-%d %H:%M')
        save(m, data[m])
    return data


# =====================================================================================================================
# the report
# =====================================================================================================================
def screens(r):
    return (r or {}).get('screens', []) if r and not r.get('crash') else []


def pages_of(r):
    return [s for s in screens(r) if not s.get('tabOf')]


def counts(r):
    ss = screens(r)
    pg = [s for s in ss if not s.get('tabOf')]
    return {'pages': len(pg), 'tabs': len(ss) - len(pg), 'screens': len(ss), 'secs': sum(len(secs_of(s)) for s in pg)}


def roles_of(D):
    W = D.get('walk') or {}
    return [u for u in USERS if any((W.get(d) or {}).get(u) for d in DEVS)]


def cat_titles(D, dev, u):
    return {c['k']: c['t'] for c in (((D.get('catalog') or {}).get(dev) or {}).get(u) or [])}


def dupes(r):
    """records listed on two or more pages of the module (a page's tabs count as the page); lists that are the same twice"""
    by = defaultdict(set)
    per_page = defaultdict(set)
    for s in screens(r):
        page = page_of(s)
        for f in s.get('found', []):
            by[f[0]].add(page)
            per_page[page].add(f[0])
    multi = {k: v for k, v in by.items() if len(v) >= 2}
    pairs = []
    ps = sorted(per_page)
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            a, b = per_page[ps[i]], per_page[ps[j]]
            a2, b2 = unnamed(a), unnamed(b)
            sh = a2 & b2
            if len(sh) >= 3 and len(sh) >= 0.5 * min(len(a2), len(b2)):
                pairs.append((ps[i], ps[j], len(sh), len(a2), len(b2), Counter(k.split(':')[0] for k in sh).most_common(3)))
    pairs.sort(key=lambda x: -x[2])
    return multi, pairs, per_page


def unnamed(keys):
    return {k for k in keys if k.split(':')[0] not in NAMES}


def fig_vals(ss, label_of):
    vals = defaultdict(lambda: defaultdict(set))
    for s in ss:
        pg = label_of(s)
        for f in s.get('figs', []):
            k = fig_key(f['l'])
            if len(k) >= 4: vals[k][pg].add(f['v'].replace(' ', ''))
        for t in s.get('tabs', []):
            if t.get('n') is not None and t.get('l'):
                vals['count: ' + fig_key(t['l'])][pg].add(str(t['n']))
        for x in secs_of(s):
            if x.get('n') is not None and x.get('h'):
                vals['count: ' + fig_key(x['h'])][pg].add(str(x['n']))
    return vals


def clashes(vals):
    out = []
    for k, m in vals.items():
        if len(k.replace('count: ', '')) < 3 or len(m) < 2: continue
        pages = list(m)
        clash = any(not any(close(a, b) for a in m[pages[i]] for b in m[pages[j]]) for i in range(len(pages)) for j in range(i + 1, len(pages)))
        if not clash: continue
        by_v = defaultdict(list)
        for pg, vs in m.items():
            for v in vs: by_v[v].append(pg)
        out.append((k, {v: sorted(w)[:4] for v, w in by_v.items()}))
    out.sort(key=lambda x: -len(x[1]))
    return out


def disagreements(r):
    return clashes(fig_vals(screens(r), page_of))


class World:
    """every module's walk, the Projects census's included, for what shows in two modules"""
    def __init__(self):
        self.D = {m: load(m) for m in WALKED}
        pj = os.path.join(CENSUS, 'projects', 'data.json')
        self.P = json.load(open(pj)) if os.path.exists(pj) else {}
        # (dev, uid) -> record key -> {(module, page)}
        self.where = defaultdict(lambda: defaultdict(set))
        # (dev, uid) -> [screen with its module]
        self.all = defaultdict(list)
        for m, D in self.D.items():
            for dev in DEVS:
                for u, r in ((D.get('walk') or {}).get(dev) or {}).items():
                    for s in screens(r):
                        self.all[(dev, u)].append((m, s))
                        for f in s.get('found', []): self.where[(dev, u)][f[0]].add((m, page_of(s)))
        for dev in DEVS:
            for u, r in ((self.P.get('walk') or {}).get(dev) or {}).items():
                for s in screens(r):
                    if s.get('job') != FIRST_JOB: continue
                    self.all[(dev, u)].append(('projects', s))
                    for f in s.get('found', []): self.where[(dev, u)][f[0]].add(('projects', PC.page_of(s)))

    def elsewhere(self, mod, dev, u, keys):
        """the pages of other modules that list these records, for this role and device"""
        c = Counter()
        for k in keys:
            for (m, pg) in self.where[(dev, u)].get(k, ()):
                if m != mod: c[(m, pg)] += 1
        return c

    def inbound(self, dev, u, v):
        """the pages (any module) whose links lead to view v"""
        out = set()
        for m, s in self.all[(dev, u)]:
            if s.get('view') == v: continue
            for ln in s.get('links') or []:
                if ln['to'] == v: out.add(f"{TITLE.get(m, m)} › {page_of(s)}")
        return sorted(out)

    def cross_clash(self, mod, dev, u):
        ss = self.all[(dev, u)]
        vals = defaultdict(lambda: defaultdict(set))
        for m, s in ss:
            lab = f"{TITLE.get(m, m)} › {page_of(s) if m != 'projects' else PC.page_of(s)}"
            for f in s.get('figs', []):
                k = fig_key(f['l'])
                if len(k) >= 4: vals[k][lab].add(f['v'].replace(' ', ''))
        out = []
        T = TITLE[mod] + ' › '
        for k, mm in clashes(vals):
            mine = [p for ps in mm.values() for p in ps if p.startswith(T)]
            other = [p for ps in mm.values() for p in ps if not p.startswith(T)]
            if mine and other: out.append((k, mm))
        return out


def how_txt(s):
    t = s.get('path') or []
    if s.get('from') == 'link': return ' › '.join(t)
    return ' › '.join(t) + (f" ({len(t)} tap{'s' if len(t) != 1 else ''})" if t else '')


def shot_link(mod, s):
    return f"[{s['shot'].split('_')[0]}](../../review/census/{mod}/shots/{s['shot']})" if s.get('shot') else ''


def headline(mod, D, Wd, w):
    H = []
    W = D.get('walk') or {}
    prim = [u for u in PRIMARY[mod] if any((W.get(d) or {}).get(u) for d in DEVS)]
    for u in prim:
        d, ph = (W.get('desktop') or {}).get(u), (W.get('phone') or {}).get(u)
        if not d or d.get('crash'): continue
        c, cp = counts(d), counts(ph) if ph else None
        tall = sum((s.get('pageH') or 0) for s in pages_of(d)) / 900
        H.append(f"- **{ROLE_NAME[u]}: {c['pages']} pages with {c['tabs']} more screens behind their tabs on the desktop" + (f" ({cp['pages']} pages and {cp['tabs']} tab screens on the phone)" if cp else '') + f"**, about {round(tall)} desktop screens end to end.")
    rows = []
    for u in roles_of(D):
        d = (W.get('desktop') or {}).get(u)
        if d and not d.get('crash'): rows.append(f"{ROLE_NAME[u].split(' (')[0]} {counts(d)['pages']}")
    if rows: H.append('- **Pages each role reaches in this module, desktop:** ' + ', '.join(rows) + '.')
    # one way in
    one = []
    for u in prim:
        for dev in DEVS:
            r = (W.get(dev) or {}).get(u)
            if not r or r.get('crash'): continue
            for pgx in reach_rows(mod, r, dev, u, w):
                if pgx['ways'] == 1: one.append(f"{pgx['page']} ({dev})")
    if one: H.append(f"- **Reached only one way** by {', '.join(ROLE_NAME[u].split(' (')[0] for u in prim)}: " + ', '.join(sorted(set(one))[:10]) + (f' and {len(set(one)) - 10} more' if len(set(one)) > 10 else '') + ' (section 1, how each page is reached).')
    for u in prim[:1]:
        r = (W.get('desktop') or {}).get(u)
        if not r or r.get('crash'): continue
        multi, pairs, per = dupes(r)
        cat = cat_titles(D, 'desktop', u)
        if multi:
            bn = Counter(k.split(':')[0] for k in multi)
            top = sorted(multi.items(), key=lambda x: (x[0].split(':')[0] in NAMES, -len(x[1])))[0]
            H.append(f"- **{len(multi)} records show on two or more of this module's pages** for {ROLE_NAME[u]} on the desktop ({', '.join(f'{n} {NOUN.get(k, k)}' for k, n in bn.most_common(4))}). \"{esc(cat.get(top[0], top[0]))[:50]}\" is on {len(top[1])}: {', '.join(sorted(top[1]))}.")
        if pairs:
            H.append(f"- **{len(pairs)} pairs of pages list largely the same records,** led by " + '; '.join(f'{a} and {b} ({n} shared)' for a, b, n, *_ in pairs[:4]) + '.')
        allk = unnamed(k for ks in per.values() for k in ks)
        el = w.elsewhere(mod, 'desktop', u, allk)
        if el:
            H.append(f"- **The same records in other modules** ({ROLE_NAME[u].split(' (')[0]}, desktop): " + '; '.join(f"{TITLE.get(m, m)} › {p} lists {n}" for (m, p), n in el.most_common(5)) + f" of the {len(allk)} records this module lists.")
        dz = disagreements(r)
        if dz:
            H.append('- **One label, different numbers inside the module:** ' + '; '.join(f"\"{k}\" " + ' against '.join(f'{v} on {wh[0]}' for v, wh in list(m.items())[:2]) for k, m in dz[:3]) + f" ({len(dz)} in all, section 3).")
        xz = w.cross_clash(mod, 'desktop', u)
        if xz:
            H.append('- **One label, different numbers against other modules:** ' + '; '.join(f"\"{k}\" " + ' against '.join(f'{v} on {wh[0]}' for v, wh in list(m.items())[:2]) for k, m in xz[:3]) + f" ({len(xz)} in all, section 3).")
    for u in prim[:1]:
        ph = (W.get('phone') or {}).get(u)
        if not ph or ph.get('crash'): continue
        pg = pages_of(ph)
        tall = [s['name'] for s in pg if (s.get('pageH') or 0) > 3 * 844]
        side = [s['name'] for s in screens(ph) if (s.get('clip') or {}).get('sideways')]
        none_above = [s['name'] for s in pg if not any(above(s, o) for o in secs_of(s))]
        sw = [s['name'] for s in pg if s.get('swipe')]
        bits = []
        if tall: bits.append(f"{len(tall)} of the {len(pg)} pages are taller than three screens ({', '.join(tall[:5])})")
        if none_above: bits.append(f"{len(none_above)} have no section heading above the fold")
        if sw: bits.append(f"{len(sw)} are reached through a strip entry that sits off screen until the strip is swiped ({', '.join(sw[:4])})")
        bits.append(f"{len(set(side))} screens scroll sideways" + (f" ({', '.join(sorted(set(side))[:4])})" if side else ''))
        H.append(f"- **On the phone** ({ROLE_NAME[u].split(' (')[0]}): " + '; '.join(bits) + '.')
    dead, crashes = [], []
    for dev in DEVS:
        for u, r in (W.get(dev) or {}).items():
            if r.get('crash'): crashes.append(f"{ROLE_NAME[u]} {dev}"); continue
            for s in screens(r):
                if s.get('error') or s.get('errors'): dead.append(f"{ROLE_NAME[u]} {dev} {s['name']}")
    H.append("- **Nothing crashed and no page raised an error**; every page opened." if not dead and not crashes else f"- **{len(dead)} screens failed to read or raised a page error** ({'; '.join(dead[:4])}){'; the walk crashed for ' + ', '.join(crashes) if crashes else ''}.")
    saves = [(u, dev, s['name']) for dev in DEVS for u, r in (W.get(dev) or {}).items() for s in screens(r) if s.get('saves')]
    H.append("- **Reading changed nothing:** no save during the walk." if not saves else f"- **{len(saves)} screen(s) saved while the census only read and pressed tabs** ({'; '.join(f'{ROLE_NAME[u]} {d}, {n}' for u, d, n in saves[:3])}). Each role ran on a fresh app, so a save never reached the next role.")
    return H


def inb_txt(x):
    t = ', '.join(x['in'][:4]) + (' and %d more' % (len(x['in']) - 4) if len(x['in']) > 4 else '')
    return esc(t) or '-'


def reach_rows(mod, r, dev, u, w):
    """per page of the module the role reached: its menu places, the phone bar, the pages that link to it"""
    out = []
    ents = r.get('entries') or []
    for s in pages_of(r):
        v = s.get('view') or (s.get('req') or '').split(':')[0]
        rq = (s.get('req') or '').split(':')
        places = [f"{e['gname']} › {e['l']}" if e['gname'] != e['l'] else e['l'] for e in ents if e['v'] == rq[0] and (e.get('tab') or '') == (rq[1] if len(rq) > 1 else '')]
        bar = any(e.get('bar') for e in ents if e['v'] == rq[0])
        inb = w.inbound(dev, u, v)
        ways = len(places) + (1 if bar and dev == 'phone' else 0) + len(inb)
        out.append({'page': s['name'], 'view': v, 'places': places, 'bar': bar, 'in': inb, 'ways': ways, 'from': s.get('from')})
    return out


def report_module(mod, w):
    D = w.D[mod]
    W = D.get('walk') or {}
    L = []
    P = L.append
    title = TITLE[mod]
    prim = PRIMARY[mod]
    n_screens = sum(len(screens(r)) for d in DEVS for r in (W.get(d) or {}).values())
    P(f'# The {title} Module, Page by Page: the Census')
    P('')
    P('**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It\'s important to understand the format of every page and what\'s on it." The loop\'s experts and the client expert walk every page of their module with this in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).')
    P('')
    P(f"**What this is.** A machine inventory, not a judgment, in the format of the Projects census (`docs/modules/projects_census.md`). No app code changed. `tests/module_census.py` (its helpers `tests/module_census_js.js` sit on the projects census's reader `tests/census_js.js` and the information map's `tests/ia_js.js`) signs in as each role on a fresh app at 1440 and at 390, reads the role's running menu, and reaches each page of this module the way the person does: the phone bar, or the menu (the hamburger on the phone), the group, then the strip. It presses every tab of every tab group and the tabs those reveal, follows the page's own links to this module's pages the menu did not reach, reads every screen and shoots it. The primary role is {PRIMARY_TXT[mod]}; every role whose menu holds a page of this module is walked. Job-scoped pages show **121 State Street** wherever the role may open it.")
    P('')
    P(f"**Build {D.get('build', '?')}** (master {D.get('head', '?')}), the one build every module census of this round ran on. {n_screens} screens in all. Walked {D.get('built', '')} on the demo day (Thu 2026-09-03); the walk of every module took {round((D.get('walkWall') or 0) / 60, 1)} minutes. Raw read: `review/census/{mod}/data.json`. Every screen per role in tables: `review/census/{mod}/tables.md`. Screenshots of every screen, both devices: `review/census/{mod}/shots/` (`desktop_` or `phone_`, the role, the page, then the tab; up to 3 desktop or 5 phone screens tall). The first screen of each page is committed; the tabs stay on the machine that ran it.")
    P('')
    P(f"Run it: `python3 build.py && cd tests && ./slot.sh python3 module_census.py --module {mod}` (then `python3 module_census.py --report` rewrites every module's page from data.json).")
    P('')
    P('## Headline')
    P('')
    for h in headline(mod, D, W, w): P(h)
    P('')
    # ------------------------------------------------------------------------------------------- 1. the tree
    P('## 1. The Tree, Role by Role')
    P('')
    P('**Pages** are the module\'s pages the role reaches from its menu (and the links those pages show). **Tabs** are the screens behind each page\'s tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.')
    P('')
    P('| Role | Primary | First page of the module, reached by (desktop / phone) | Pages | Tab screens | Sections | Screens |')
    P('|---|---|---|---|---|---|---|')
    for u in roles_of(D):
        d, ph = (W.get('desktop') or {}).get(u), (W.get('phone') or {}).get(u)
        cs = [counts(x) if x and not x.get('crash') else None for x in (d, ph)]
        f = lambda k: ' / '.join(str(c[k]) if c else ('crashed' if x and x.get('crash') else '-') for c, x in zip(cs, (d, ph)))
        first = ' / '.join(esc(how_txt(pages_of(x)[0])) if x and pages_of(x) else '-' for x in (d, ph))
        P(f"| {ROLE_NAME[u]} | {'yes' if u in prim else ''} | {first} | {f('pages')} | {f('tabs')} | {f('secs')} | {f('screens')} |")
    P('')
    # the page by role grid
    P('### Which pages each role reaches (desktop)')
    P('')
    P('Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it.')
    P('')
    order, grid = [], defaultdict(dict)
    us = [u for u in roles_of(D) if (W.get('desktop') or {}).get(u)]
    for u in us:
        r = (W.get('desktop') or {}).get(u)
        for s in screens(r):
            pg = page_of(s)
            k = (s.get('req') or '').split(':')[0] if not s.get('tabOf') else None
            if pg not in order: order.append(pg)
            grid[pg][u] = grid[pg].get(u, 0) + 1
    if us:
        P('| Page | ' + ' | '.join(ROLE_NAME[u].split(' (')[0] for u in us) + ' |')
        P('|---|' + '---|' * len(us))
        for pg in order:
            P(f'| {esc(pg)} | ' + ' | '.join(str(grid[pg].get(u, '-')) for u in us) + ' |')
        P('')
    # the primary role's tree at a glance
    for u in prim:
        d, ph = (W.get('desktop') or {}).get(u), (W.get('phone') or {}).get(u)
        if not d or d.get('crash'): continue
        pss = {x['name']: x for x in pages_of(ph)} if ph else {}
        P(f"### {ROLE_NAME[u]}'s tree at a glance")
        P('')
        P('Reached by is the taps from the role\'s first page, desktop then phone. Tall is in screens, desktop / phone. Sections are the headed parts as the page opens (phone above the fold). Tabs are the screens behind its tab groups, desktop / phone. "What it lists" counts the records found on the page as it opens.')
        P('')
        P('| Page | Reached by (desktop / phone) | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button | First button | Shots |')
        P('|---|---|---|---|---|---|---|---|---|---|---|')
        for x in pages_of(d):
            y = pss.get(x['name'])
            tabs = len([t for t in screens(d) if t.get('tabOf') and page_of(t) == x['name']])
            ptabs = len([t for t in screens(ph) if t.get('tabOf') and page_of(t) == x['name']]) if ph else '-'
            ab = len([o for o in secs_of(y) if above(y, o)]) if y else '-'
            figs = '; '.join(f"{esc(f['l'])[:22]} {esc(f['v'])[:24]}" for f in x.get('figs', [])[:4])
            tall = f"{screens_tall(x, 'desktop')} / {screens_tall(y, 'phone') if y else '-'}"
            fb = x.get('first') or {}
            first = (esc(fb.get('l', ''))[:28] + (' (blue)' if fb.get('blue') else '')) if fb else 'none'
            shots = ' '.join(z for z in (shot_link(mod, x), shot_link(mod, y) if y else '') if z)
            P(f"| {esc(x['name'])} | {esc(how_txt(x))} / {esc(how_txt(y)) if y else '-'} | {esc(x.get('heading', ''))} | {tall} | {len(secs_of(x))} ({ab}) | {tabs} / {ptabs} | {figs or '-'} | {esc(rec_line(x, 4)) or '-'} | {esc(', '.join(b['l'] for b in x.get('blue', [])))[:30] or 'none'} | {first} | {shots} |")
        P('')
    # how each page is reached
    P('### How each page is reached, and the pages reached only one way')
    P('')
    P('Menu places are the role\'s menu entries that open the page (a page in two groups has two). The phone bar counts as one more way in on the phone (its pages are in the menu too). Links are the walked pages, in any module, that show a link to it. **One way** means one menu place and nothing else: lose that entry and the page is lost.')
    P('')
    P('| Role | Device | Page | Menu places | Phone bar | Linked from | Ways in |')
    P('|---|---|---|---|---|---|---|')
    for u in roles_of(D):
        for dev in DEVS:
            r = (W.get(dev) or {}).get(u)
            if not r or r.get('crash'): continue
            for x in reach_rows(mod, r, dev, u, w):
                P(f"| {ROLE_NAME[u]} | {dev} | {esc(x['page'])} | {esc('; '.join(x['places'])) or ('none (reached by a link)' if x['from'] == 'link' else 'none')} | {'yes' if x['bar'] else '-'} | {inb_txt(x)} | {x['ways']}{' (one way)' if x['ways'] == 1 else ''} |")
    P('')
    un = [(u, dev, r.get('unplaced')) for u in roles_of(D) for dev in DEVS for r in [(W.get(dev) or {}).get(u)] if r and r.get('unplaced')]
    if un:
        P('**Pages of this module the role may open (ROLE_VIEWS) that no menu entry or walked link reached:** ' + '; '.join(f"{ROLE_NAME[u]} {dev}: {', '.join('`' + v + '`' for v in vs)}" for u, dev, vs in un) + '. Most are retired pages that land on another (the menu\'s aliases, MN_ALIAS and OC_RETIRED); each is a page a person can still reach only through search or an old link.')
        P('')
    # ------------------------------------------------------------------------------------------- 2. data
    P('## 2. Where the Data Lives, and Where It Shows Twice')
    P('')
    P('Records are found by their own words (the information map\'s catalog, the job\'s nouns and this census\'s: clients, vendors, leads, contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals, obligations, lessons, partners, bank lines, threads), so these are floors. A page\'s tabs count as the page.')
    P('')
    for u in prim[:1]:
        r = (W.get('desktop') or {}).get(u)
        if not r or r.get('crash'): continue
        multi, pairs, per = dupes(r)
        by_noun = defaultdict(lambda: defaultdict(int))
        allrec = defaultdict(set)
        for page, ks in per.items():
            for k in ks:
                by_noun[k.split(':')[0]][page] += 1
                allrec[k.split(':')[0]].add(k)
        if by_noun:
            P(f'### {ROLE_NAME[u]}, desktop: each kind of record, and the pages that list it')
            P('')
            P('| Records | Found | Pages that list them (how many each) | Also in other modules |')
            P('|---|---|---|---|')
            for n, pages in sorted(by_noun.items(), key=lambda x: -len(x[1])):
                el = w.elsewhere(mod, 'desktop', u, allrec[n])
                P(f"| {NOUN.get(n, n)} | {len(allrec[n])} | {len(pages)}: " + ', '.join(f'{esc(p)} {c}' for p, c in sorted(pages.items(), key=lambda x: -x[1])) + ' | ' + (esc(', '.join(f"{TITLE.get(m, m)} › {p} {c}" for (m, p), c in el.most_common(4))) or '-') + ' |')
            P('')
    P('### Records on two or more pages, and lists that are the same list twice')
    P('')
    for dev in DEVS:
        for u in roles_of(D):
            r = (W.get(dev) or {}).get(u)
            if not r or r.get('crash'): continue
            if dev == 'phone' and u not in prim: continue
            cat = cat_titles(D, dev, u)
            multi, pairs, per = dupes(r)
            if not multi: continue
            by_noun = defaultdict(list)
            for k, pages in multi.items(): by_noun[k.split(':')[0]].append(len(pages))
            P(f"**{ROLE_NAME[u]}, {dev}:** {len(multi)} records on two or more pages: " + '; '.join(f"{NOUN.get(n, n)} {len(v)} (up to {max(v)} pages)" for n, v in sorted(by_noun.items(), key=lambda x: -len(x[1]))) + '.')
            P('')
            if u in prim:
                for k, pages in sorted(multi.items(), key=lambda x: -len(x[1]))[:6]:
                    P(f"- \"{esc(cat.get(k, k))[:60]}\" ({NOUN.get(k.split(':')[0], k.split(':')[0])}) on {len(pages)} pages: {', '.join(sorted(pages))}")
            if pairs:
                P('- the same list twice (3 or more shared records, at least half of the shorter list): ' + '; '.join(f"{a} and {b} ({n} shared, of {na} and {nb}: {', '.join(NOUN.get(x, x) for x, _ in kinds)})" for a, b, n, na, nb, kinds in pairs[:6]))
            P('')
    P('### The same records in other modules')
    P('')
    P('For each role on the desktop: the pages of other modules (the Projects census\'s 121 State Street pages included) that list records this module lists, with how many.')
    P('')
    for u in roles_of(D):
        r = (W.get('desktop') or {}).get(u)
        if not r or r.get('crash'): continue
        _, _, per = dupes(r)
        allk = unnamed(k for ks in per.values() for k in ks)
        el = w.elsewhere(mod, 'desktop', u, allk)
        if el: P(f"- **{ROLE_NAME[u]}** ({len(allk)} records here): " + '; '.join(f"{TITLE.get(m, m)} › {esc(p)} {n}" for (m, p), n in el.most_common(8)))
        else: P(f"- **{ROLE_NAME[u]}**: none found.")
    P('')
    P('Names (clients, vendors, leads, contacts, companies, partners) are left out here: a page that writes a name counts as listing it.')
    P('')
    # ------------------------------------------------------------------------------------------- 3. numbers
    P('## 3. One Label, Different Numbers')
    P('')
    P('The same label (a tile, a figure, a tab or section count) with numbers that share no value on two pages, for one role. Some are right about different scopes ("Open" against "All", one job against every job); the person still reads one word with two numbers. Each needs a person to judge.')
    P('')
    for dev in DEVS:
        for u in roles_of(D):
            r = (W.get(dev) or {}).get(u)
            if not r or r.get('crash'): continue
            if dev == 'phone' and u not in prim: continue
            dz = disagreements(r)
            if not dz: continue
            P(f"**Inside the module, {ROLE_NAME[u]}, {dev}** ({len(dz)}):")
            for k, m in dz[:12]:
                P(f"- {esc(k)}: " + '; '.join(f"{esc(v)} on {', '.join(esc(x) for x in wh)}" for v, wh in list(m.items())[:4]))
            P('')
    if not any(disagreements((W.get(dev) or {}).get(u)) for dev in DEVS for u in roles_of(D) if (dev == 'desktop' or u in prim) and (W.get(dev) or {}).get(u)):
        P('Inside the module: none found.')
        P('')
    for u in prim:
        xz = w.cross_clash(mod, 'desktop', u)
        if not xz:
            P(f"Against other modules, {ROLE_NAME[u]}, desktop: none found.")
            P('')
            continue
        P(f"**Against other modules, {ROLE_NAME[u]}, desktop** ({len(xz)}):")
        for k, m in xz[:12]:
            P(f"- {esc(k)}: " + '; '.join(f"{esc(v)} on {', '.join(esc(x) for x in wh)}" for v, wh in list(m.items())[:4]))
        P('')
    # ------------------------------------------------------------------------------------------- 4. empty, dead
    P('## 4. Empty, Dead and Broken Screens')
    P('')
    rows = []
    for dev in DEVS:
        for u in roles_of(D):
            r = (W.get(dev) or {}).get(u)
            if not r: continue
            if r.get('crash'): rows.append((dev, u, '(the walk)', 'crashed: ' + r['crash'][:120])); continue
            for s in screens(r):
                why = []
                if s.get('error'): why.append('read failed: ' + s['error'][:80])
                if s.get('errors'): why.append('page error: ' + s['errors'][0][:100])
                if (s.get('words') or 0) < 25 and not s.get('error'): why.append(f"{s.get('words', 0)} words")
                rq = (s.get('req') or '').split(':')[0]
                if s.get('view') and rq and s['view'] != rq and not s.get('tabOf'): why.append(f"opens {s['view']} when asked for {rq}")
                if 'no button: set view' in (s.get('path') or []): why.append('no menu button found: opened by setting the view')
                if 'no strip entry' in (s.get('path') or []): why.append('the strip entry was not there')
                if s.get('saves'): why.append(f"{s['saves']} save(s) while reading")
                if s.get('leftTo'): why.append(f"the tab leaves for {s['leftTo']}")
                em = [e['t'] for e in (s.get('empties') or [])]
                if em and not s.get('found') and not s.get('tabOf') and (s.get('words') or 0) < 150: why.append('lists nothing: "' + em[0][:60] + '"')
                if why: rows.append((dev, u, s['name'], '; '.join(why)))
    if rows:
        P('| Device | Role | Screen | What |')
        P('|---|---|---|---|')
        for dev, u, nm, why in rows[:150]:
            P(f'| {dev} | {ROLE_NAME[u]} | {esc(nm)} | {esc(why)} |')
        if len(rows) > 150: P(f'| | | and {len(rows) - 150} more in tables.md | |')
    else:
        P('None found.')
    P('')
    # ------------------------------------------------------------------------------------------- 5. phone
    P('## 5. The Phone at 390')
    P('')
    P('"Cut off" is text the phone ends early; "scrolls inside" is a strip of tiles or tabs the person swipes sideways inside the page (the page itself does not move). "Strip swipe" counts pages whose strip entry sits off screen until the strip is swiped. Pages taller than 3 phone screens are listed with their height.')
    P('')
    P('| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | Strip swipe | Pages taller than 3 screens |')
    P('|---|---|---|---|---|---|---|')
    for u in roles_of(D):
        r = (W.get('phone') or {}).get(u)
        if not r or r.get('crash'): continue
        ss = screens(r)
        side = sorted({page_of(s) for s in ss if (s.get('clip') or {}).get('sideways')})
        past = sorted({page_of(s) for s in ss if any(p['where'] == 'past the edge' or p['where'].startswith('cut off') for p in (s.get('clip') or {}).get('parts', []))})
        inner = sorted({page_of(s) for s in ss if any(p['where'].startswith('scrolls in') for p in (s.get('clip') or {}).get('parts', []))})
        tall = [f"{s['name']} {screens_tall(s, 'phone')}" for s in pages_of(r) if (s.get('pageH') or 0) > 3 * 844]
        sw = [s['name'] for s in pages_of(r) if s.get('swipe')]
        P(f"| {ROLE_NAME[u]} | {len(ss)} | {len(side)}{': ' + esc(', '.join(side[:6])) if side else ''} | {len(past)}{': ' + esc(', '.join(past[:8])) if past else ''} | {len(inner)}{': ' + esc(', '.join(inner[:8])) if inner else ''} | {len(sw)}{': ' + esc(', '.join(sw[:6])) if sw else ''} | {len(tall)}{': ' + esc(', '.join(tall[:8])) if tall else ''} |")
    P('')
    # ------------------------------------------------------------------------------------------- 6. in full
    P('## 6. Page by Page, in Full')
    P('')
    P('Every page the primary role reaches, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone.')
    P('')
    for u in prim:
        for dev in DEVS:
            r = (W.get(dev) or {}).get(u)
            if not r or r.get('crash'): continue
            P(f'### {ROLE_NAME[u]}, {dev}')
            P('')
            for s in pages_of(r):
                tabs = [x for x in screens(r) if x.get('tabOf') and page_of(x) == s['name']]
                P(f"- reached by: {esc(how_txt(s))}" + (f"; also in {esc('; '.join(s['otherPlaces']))}" if s.get('otherPlaces') else '') + (f"; first button \"{esc((s.get('first') or {}).get('l', ''))}\"" if s.get('first') else '') + (f"; shot {shot_link(mod, s)}" if s.get('shot') else ''))
                page_block(P, s, tabs, dev, full=True)
                if s.get('unpressed'): P(f"  - tabs that would not press (the row changed once one was pressed): {esc(', '.join(s['unpressed'][:8]))}")
            P('')
    # ------------------------------------------------------------------------------------------- 7. others
    P('## 7. The Other Roles, One Line a Page')
    P('')
    for u in roles_of(D):
        if u in prim: continue
        for dev in DEVS:
            r = (W.get(dev) or {}).get(u)
            if not r: continue
            if r.get('crash'):
                P(f'### {ROLE_NAME[u]}, {dev}: the walk crashed: {esc(r["crash"][:200])}')
                P('')
                continue
            P(f'### {ROLE_NAME[u]}, {dev}')
            P('')
            for s in pages_of(r):
                tabs = [x for x in screens(r) if x.get('tabOf') and page_of(x) == s['name']]
                P(f"- reached by: {esc(how_txt(s))}" + (f"; shot {shot_link(mod, s)}" if s.get('shot') else ''))
                page_block(P, s, tabs, dev, full=False)
            P('')
    # ------------------------------------------------------------------------------------------- 8. limits
    P('## 8. What This Census Did Not Check, and How Sure It Is')
    P('')
    P('- **Records are found by their words** (the information map\'s rule): a record shown as a number, a chart or in other words is not counted, so duplication counts are floors. Names (clients, vendors, leads, contacts, companies, partners) match wherever the name is written, so a page that only mentions a client counts as listing it.')
    P('- **Figures** are read from tiles, two-column tables, definition lists and the bold money that leads a note; a figure inside a sentence is not read. Labels are compared with numbers and small words removed, so two different figures with one label show as a disagreement and need a person to judge.')
    P('- **Tabs** are rows of two or more buttons with exactly one on. A dropdown that switches the view, a row of toggles, the rows of Settings and Project Settings, and a button that commits (New, Send, Approve...) are never pressed. One level of revealed tabs is walked; a tab group seen once on a page is not walked again from another route to the same page.')
    P('- **What opens, not what is two taps away:** a record opened from a row (an invoice, a PO, a bill), "N more" rows, folded cards and sheets are not walked.')
    P('- **One job:** job-scoped pages are read on 121 State Street where the role may open it. The Projects census reads two jobs.')
    P('- **Each role runs on a fresh app,** as a new device: what a page remembers (a tab, All projects on the phone) starts as a first visit.')
    P('- **Not judged:** whether the content is right, what is missing, and what should merge. That is the experts\' walk with this census in hand.')
    P('')
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, f'{mod}_census.md'), 'w') as f: f.write('\n'.join(L) + '\n')
    tables(mod, D)


def tables(mod, D):
    W = D.get('walk') or {}
    L = []
    P = L.append
    P(f'# {TITLE[mod]} Census: Every Screen')
    P('')
    P('Per role and device: the screen, how it was reached, the view it landed on, its height in screens, sections (above the fold), tab groups, records, blue buttons, the first button, figures. Written by `tests/module_census.py --report` from data.json.')
    P('')
    for dev in DEVS:
        for u in USERS:
            r = (W.get(dev) or {}).get(u)
            if not r or r.get('crash'): continue
            P(f'## {ROLE_NAME[u]}, {dev}')
            P('')
            P('| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |')
            P('|---|---|---|---|---|---|---|---|---|---|---|')
            for s in screens(r):
                secs = secs_of(s)
                ab = len([x for x in secs if above(s, x)])
                fb = s.get('first') or {}
                P(f"| {esc(s['name'])} | {esc(' › '.join(s.get('path', [])))} | {s.get('view', '?')} | {screens_tall(s, dev)} | {len(secs)} ({ab}) | {len(s.get('groups', []))} | {esc(rec_line(s, 5))} | {esc(', '.join(b['l'] for b in s.get('blue', []))[:40])} | {esc(fb.get('l', ''))[:30]} | {esc('; '.join(f['l'][:24] + ' ' + f['v'] for f in s.get('figs', [])[:4]))} | {s.get('shot', '')} |")
            P('')
    out, _, _ = dirs(mod)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'tables.md'), 'w') as f: f.write('\n'.join(L) + '\n')


# ------------------------------------------------------------------------------------------- the README
def module_dups(mod, w):
    """the module's biggest duplications, ranked by how many records they share"""
    if mod == 'projects':
        r = ((w.P.get('walk') or {}).get('desktop') or {}).get('u_alan')
        if not r: return []
        _, pairs, _ = PC.dupes(r, FIRST_JOB)
        return [(n, f"{a} and {b} list {n} of the same records") for a, b, n, *_ in pairs]
    D = w.D[mod]
    W = D.get('walk') or {}
    out = []
    for u in PRIMARY[mod][:1]:
        r = (W.get('desktop') or {}).get(u)
        if not r or r.get('crash'): continue
        _, pairs, per = dupes(r)
        out += [(n, f"{a} and {b} list {n} of the same records") for a, b, n, *_ in pairs]
        for pg, ks in per.items():
            ks = unnamed(ks)
            for (m, p), n in w.elsewhere(mod, 'desktop', u, ks).most_common(2):
                if n >= 3 and n >= 0.5 * len(ks): out.append((n, f"{pg} and {TITLE.get(m, m)} › {p} list {n} of the same records"))
        pl = Counter(e['v'] for e in (r.get('entries') or []) if e.get('mod') == mod)
        for v, n in pl.items():
            if n >= 2:
                es = [f"{e['gname']} › {e['l']}" for e in r['entries'] if e['v'] == v]
                out.append((n, f"`{v}` sits in {n} menu places ({', '.join(es)})"))
    out.sort(key=lambda x: -x[0])
    seen, res = set(), []
    for n, t in out:
        if t in seen: continue
        seen.add(t)
        res.append((n, t))
    return res


def readme(w):
    L = []
    P = L.append
    P('# The Module Census')
    P('')
    P('**Asked by Alan, 2026-10-26:** "Go through all the modules with screenshots. It\'s important to understand the format of every page and what\'s on it." Each module has a census: every page, tab and sub-tab each role reaches, the way the person reaches it, at 1440 and at 390, with a screenshot of every screen. The four loop experts (owner, PM, procurement, accounting) and the client expert walk their modules with these in hand in round one of the improvement loop (docs/IMPROVEMENT_LOOP.md).')
    P('')
    bh = {m: (w.D[m].get('build') or '?') for m in WALKED}
    P(f"**One build:** {', '.join(sorted(set(bh.values())))} (every module census of this round, the Projects census included). Walked by `tests/module_census.py` (every module but Projects) and `tests/projects_census.py` (Projects, two jobs), each run once through `tests/slot.sh`. Screenshots: `review/census/<module>/shots/`; the first screen of each page is committed, the tabs stay on the machine that ran it.")
    P('')
    P('A page belongs to the module whose menu group holds it, read from the running menu (`mnMap()`); More and Settings place each page by its noun, and a page in two groups is walked in each module that holds it. Pages, tab screens and screens count what each role reaches; each cell reads desktop / phone.')
    P('')
    P('| Module | Primary role | Roles walked | Pages | Tab screens | Screens | Top three duplications | Census |')
    P('|---|---|---|---|---|---|---|---|')
    for mod, title, ptxt, prim in MODULES:
        if mod == 'projects':
            W = w.P.get('walk') or {}
            us = [u for u in USERS if any((W.get(d) or {}).get(u) for d in DEVS)]
            tc = {d: PC.tree_counts((W.get(d) or {}).get('u_alan') or {}, FIRST_JOB) for d in DEVS}
            pages = ' / '.join(str(tc[d]['pages']) for d in DEVS)
            tabs = ' / '.join(str(tc[d]['tabs']) for d in DEVS)
            scr = ' / '.join(str(sum(len((r or {}).get('screens', [])) for r in (W.get(d) or {}).values())) for d in DEVS)
            note = ' (PM, 121 State Street; screens: every role, two jobs)'
        else:
            D = w.D[mod]
            W = D.get('walk') or {}
            us = roles_of(D)
            pu = prim[0]
            c = {d: counts((W.get(d) or {}).get(pu)) for d in DEVS}
            pages = ' / '.join(str(c[d]['pages']) for d in DEVS)
            tabs = ' / '.join(str(c[d]['tabs']) for d in DEVS)
            scr = ' / '.join(str(sum(len(screens(r)) for r in (W.get(d) or {}).values())) for d in DEVS)
            note = f' ({ROLE_NAME[pu].split(" (")[0]}; screens: every role)'
        dd = module_dups(mod, w)[:3]
        P(f"| {title} | {ptxt} | {len(us)} | {pages}{note} | {tabs} | {scr} | {esc('; '.join(t for _, t in dd)) or '-'} | [{mod}_census.md]({mod}_census.md) |")
    P('')
    P('## Pages, Tabs and Screens per Role and Device')
    P('')
    P('Each cell: pages / tab screens / screens, desktop then phone. "-" means the role opens no page of the module.')
    P('')
    P('| Module | ' + ' | '.join(ROLE_NAME[u].split(' (')[0] for u in USERS) + ' |')
    P('|---|' + '---|' * len(USERS))
    for mod, title, _, _ in MODULES:
        cells = []
        for u in USERS:
            cs = []
            for d in DEVS:
                if mod == 'projects':
                    r = ((w.P.get('walk') or {}).get(d) or {}).get(u)
                    if not r or r.get('crash') or not PC.screens_of(r, FIRST_JOB): cs.append('-'); continue
                    t = PC.tree_counts(r, FIRST_JOB)
                    cs.append(f"{t['pages']}/{t['tabs']}/{t['screens']}")
                else:
                    r = ((w.D[mod].get('walk') or {}).get(d) or {}).get(u)
                    if not r: cs.append('-'); continue
                    if r.get('crash'): cs.append('crashed'); continue
                    t = counts(r)
                    cs.append(f"{t['pages']}/{t['tabs']}/{t['screens']}")
            cells.append(' · '.join(cs) if any(x != '-' for x in cs) else '-')
        P(f'| {title} | ' + ' | '.join(cells) + ' |')
    P('')
    P('Projects counts 121 State Street only (its census also walks a design-stage job).')
    P('')
    with open(os.path.join(DOCS, 'README.md'), 'w') as f: f.write('\n'.join(L) + '\n')


def report(mods=None):
    w = World()
    for m in (mods or WALKED):
        if not w.D.get(m) or not w.D[m].get('walk'): continue
        report_module(m, w)
        print('wrote', os.path.join(DOCS, f'{m}_census.md'))
    readme(w)
    print('wrote', os.path.join(DOCS, 'README.md'))


async def main():
    a = sys.argv[1:]
    users = USERS
    mods = WALKED
    if '--user' in a: users = a[a.index('--user') + 1].split(',')
    if '--module' in a: mods = [m for m in a[a.index('--module') + 1].split(',') if m in WALKED]
    devices = (False, True)
    if '--device' in a: devices = (a[a.index('--device') + 1] == 'phone',)
    shots = '--no-shots' not in a
    if '--dry' in a:
        global CENSUS, DOCS
        CENSUS = os.path.join(ROOT, 'review', 'census', '_dry')
        DOCS = os.path.join(CENSUS, 'docs')
        users = users if '--user' in a else ['u_controller']
        mods = mods if '--module' in a else ['accounting']
        devices = devices if '--device' in a else (True,)
    steps = [x for x in ('--walk', '--report') if x in a] or ['--walk', '--report']
    t0 = time.time()
    if '--walk' in steps:
        await walk(users, devices, mods, shots)
        print(f"module census walk: {round((time.time() - t0) / 60, 1)} minutes", flush=True)
    if '--report' in steps: report()
    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
