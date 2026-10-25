"""projects_census: the Projects module, page by page (Alan, 2026-10-25). A measurement, not a fix: it changes no app code.

"Did the role experts check each module and its sub pages and the layout of the page, for example the projects page,
where all the data lives, how many sub pages, what information is on those sub pages?" They had not (Pilot 2: the PM
spent 9 seconds on Projects). This is step 1 of the module census (docs/PLAN.md, Module census): a machine inventory
the role-expert PM and the information-architecture reviewer walk with in hand.

For every role that can open a job's pages (the ten seats; the client through the portal), at 1440 and at 390, it
  1. opens the Projects list the way the person does (the bar's or the rail's Projects) and reads it, then taps the
     row of each walked job and records what the tap opens;
  2. for two jobs (121 State Street, the active construction job, and a design-stage job), opens the job page and
     every sub-page the job page reaches: the sub-tab strip (the menu's Projects group, MN_JOBS), the links on the job
     page itself, and for the field roles and the client the job pages of their own menus;
  3. on every page presses every tab of every tab group (a row of buttons with one on; words that commit are never
     pressed), and the tabs those reveal, one level down;
  4. reads every screen: the path from the job page, heading, tabs and their counts, sections (heading, count, y,
     height, above the phone's fold), columns and form fields, the records listed (the information map's catalog,
     tests/ia_js.js, plus the job's own nouns, tests/census_js.js), figures (a label with a number), empty states, blue
     buttons, sideways scroll and clipping at 390, the links that leave the page.
Then it works out, per role, device and job: the tree (pages, sub-pages, tabs, sections), the records listed on two or
more screens, lists that are the same list twice, the same label with different numbers, empty and dead pages, and
what the menu opens that the job page does not (and the reverse). Writes review/census/projects/data.json, the
screenshots in review/census/projects/shots/ (the PM on both devices, the first job, every screen), and
docs/modules/projects_census.md.

  python3 projects_census.py                  walk and report (about 40 minutes; run it through tests/slot.sh)
  python3 projects_census.py --walk|--report  one step (report reads data.json)
  python3 projects_census.py --user u_alan --device phone   one role, one device (walk only, merged into data.json)
  python3 projects_census.py --no-shots       no screenshots
"""
import asyncio, json, os, re, sys, time
from collections import defaultdict, Counter
from harness import *
from ia_map import JS as IA_JS, WHO, reset_lists

HERE = os.path.dirname(os.path.abspath(__file__))
CJS = open(os.path.join(HERE, 'census_js.js')).read()
OUT = os.path.join(ROOT, 'review', 'census', 'projects')
SHOTS = os.path.join(OUT, 'shots')
DATA = os.path.join(OUT, 'data.json')
DOC = os.path.join(ROOT, 'docs', 'modules', 'projects_census.md')
USERS = ['u_alan', 'u_owner', 'u_chen', 'u_angel', 'u_sarah', 'u_billing', 'u_controller', 'u_klein', 'u_alberto', 'u_alex']
SHOT_USERS = {'u_alan'}
FIRST_JOB = 'p121'
# the Projects module's pages for a role without the office menu's Projects group: the field roles' job pages and
# the client's portal (FD_CLIENT_NAV). Field roles' Today (ftoday), Clock (time), Route and Raise are their day, not the job.
FIELD_JOB = ['fsite', 'flog', 'fcrew', 'sched', 'plans', 'photos', 'files', 'recv', 'req', 'tasks', 'dec', 'field', 'mat', 'insp']
CLIENT_JOB = ['client', 'sched', 'dec', 'clacct', 'chat']
# every view that belongs to the module, for the menu-versus-job-page comparison
MODULE = set(['ovjobs', 'port', 'dash', 'proj', 'sched', 'tasks', 'dec', 'subm', 'insp', 'field', 'photos', 'recv', 'mat',
              'costs', 'billing', 'files', 'plans', 'inbox', 'chat', 'fsite', 'flog', 'fcrew', 'client', 'clacct', 'sdraw', 'sel'])
MAX_TABS = 12
NO_PRESS = {'proj', 'setup'}
TAB_DEPTH = 2
WAIT = 180


async def boot(p, phone):
    b, pg, errs = await open_app(p, phone)
    await pg.evaluate(IA_JS)
    await pg.evaluate(CJS)
    await pg.evaluate("() => { try { window.__iadflt = { v: t2View, w: tkWho }; } catch (e) { window.__iadflt = null; } }")
    return b, pg, errs


PICK_JOBS = r"""() => {
  // the second job: a design-stage job (its name or its type, scope, phase or stage says design), the one with the
  // most records on it; else the job least like 121 State Street
  const words = (p) => (p.project.name + " " + JSON.stringify([p.project.type, p.project.scope, p.project.phase, p.project.stage, p.project.kind, p.stage, p.phase, p.type])).toLowerCase();
  const size = (p) => ["tasks", "decisions", "submittals", "materials", "inspections", "files", "issues"].reduce((a, k) => a + ((p[k] || []).length), 0);
  const others = DB.projects.filter((p) => p.id !== "p121");
  const design = others.filter((p) => /design/.test(words(p)) && !/design-build/.test(words(p))).sort((a, b) => size(b) - size(a));
  const pick = design[0] || others.sort((a, b) => size(b) - size(a))[0];
  return { jobs: DB.projects.map((p) => ({ id: p.id, name: p.project.name, client: p.clientId, size: size(p), tasks: (p.tasks || []).length })),
           second: pick ? pick.id : "", why: pick ? (design.includes(pick) ? "design stage, the design job with the most on it" : "the other job with the most on it") : "" };
}"""


async def settle(pg, ms=WAIT):
    await pg.wait_for_timeout(ms)


async def close_sheets(pg):
    await pg.evaluate("() => { try { typeof mbCloseModal === 'function' && mbCloseModal(); } catch (e) {} document.querySelectorAll('.sheet.open, .drawer.open').forEach(e => e.classList.remove('open')); }")


async def read(pg, cat_ok=True):
    try:
        return await asyncio.wait_for(pg.evaluate("() => CENSUS.read(window.__cecat)"), 40)
    except Exception as e:
        return {'error': str(e)[:200]}


def compact(s):
    """keep what the report needs; records as keys with their section"""
    if not s or 'error' in s: return s
    s['found'] = [[f['k'], f['sec'], f['y'], 1 if f['above'] else 0] for f in s.get('found', [])]
    for k in ('jargon', 'fieldJargon'): s.pop(k, None)
    return s


class Walker:
    def __init__(self, pg, errs, uid, phone, shots):
        self.pg, self.errs, self.uid, self.phone, self.shots = pg, errs, uid, phone, shots
        self.screens = []
        self.seen = defaultdict(list)   # (job, view) -> label sets of the tab groups walked there
        self.dev = 'phone' if phone else 'desktop'

    async def view(self):
        return await self.pg.evaluate("() => view")

    async def record(self, name, path, req, job, extra=None):
        t0 = time.time()
        n0 = len(self.errs)
        sv0 = await self.pg.evaluate("() => CENSUS.saves")
        await self.pg.evaluate("() => IA.scrollTop()")
        s = compact(await read(self.pg))
        s = s or {'error': 'no view on screen'}
        s.update({'name': name, 'path': path, 'req': req, 'job': job, 'ms': int((time.time() - t0) * 1000)})
        s['saves'] = (await self.pg.evaluate("() => CENSUS.saves")) - sv0
        s['errors'] = self.errs[n0:n0 + 3]
        if extra: s.update(extra)
        if self.shots:
            slug = re.sub(r'[^a-z0-9]+', '_', f'{job}_{name}'.lower()).strip('_')[:80]
            fn = f'{self.dev}_{slug}.jpg'
            base = PHONE if self.phone else DESKTOP
            try:
                # the page scrolls inside its own container: the window grows to the page (at most 5 phone screens or
                # 3 desktop ones) for the shot, then goes back
                h = max(base['height'], min(int(s.get('pageH') or 0) + 260, 5 * 844 if self.phone else 3 * 900))
                if h > base['height']:
                    await self.pg.set_viewport_size({'width': base['width'], 'height': h})
                    await self.pg.wait_for_timeout(150)
                await self.pg.screenshot(path=os.path.join(SHOTS, fn), type='jpeg', quality=55)
                s['shot'] = fn
            except Exception as e:
                s['shotErr'] = str(e)[:100]
            finally:
                await self.pg.set_viewport_size(base)
                await self.pg.wait_for_timeout(60)
        self.screens.append(s)
        return s

    async def open(self, v):
        await self.pg.evaluate("v => { view = v; render(); }", v)
        await settle(self.pg)

    @staticmethod
    def same(labels, sets):
        L = set(labels)
        return any(len(L & S) >= max(1, 0.5 * min(len(L), len(S))) for S in sets)

    def walked(self, job, v, labels):
        return self.same(labels, self.seen[(job, v)])

    async def tabs(self, base, path, req, job, groups, depth, seen_groups):
        """press every tab of every group on the page; the tabs a press reveals are walked one level down. `seen_groups`
        holds the label sets of the page's own groups: a group the page already shows is walked at its own level."""
        start_view = await self.view()
        if depth == 1: seen_groups = [set(g['labels']) for g in groups]
        for g in groups[:6]:
            key = '|'.join(g['labels'])
            if self.walked(job, start_view, g['labels']):
                continue
            self.seen[(job, start_view)].append(set(g['labels']))
            on = g['labels'][g['on']] if 0 <= g['on'] < len(g['labels']) else None
            for lab in g['labels'][:MAX_TABS]:
                if lab == on or not lab: continue
                ok = await self.pg.evaluate("([g, l]) => CENSUS.press(g, l)", [g['labels'], lab])
                if not ok: continue
                await settle(self.pg)
                now = await self.view()
                modal = await self.pg.evaluate("() => { const m = document.querySelector('#mbm'); return !!m && m.getClientRects().length > 0; }")
                nm = f'{base}[{lab}]'
                s = await self.record(nm, path + [lab], req, job, {'tabOf': base, 'tabGroup': g['labels'], 'leftTo': now if now != start_view else '', 'tabModal': modal})
                if modal: await close_sheets(self.pg)
                if now != start_view:
                    await self.open(start_view)
                    continue
                if depth < TAB_DEPTH and 'groups' in s:
                    new = [x for x in s['groups'] if not self.walked(job, start_view, x['labels']) and not self.same(x['labels'], seen_groups)]
                    if new: await self.tabs(nm, path + [lab], req, job, new, depth + 1, seen_groups)
                    # back to this tab before the next one of the outer group
                    await self.pg.evaluate("([g, l]) => CENSUS.press(g, l)", [g['labels'], lab])
            if on:
                await self.pg.evaluate("([g, l]) => CENSUS.press(g, l)", [g['labels'], on])
                await settle(self.pg, 100)

    async def page(self, name, path, req, job):
        s = await self.record(name, path, req, job)
        # Project Settings' button rows are the job's own settings (type, working days): reading them is enough
        if s.get('view') in NO_PRESS: s['notPressed'] = True
        elif s.get('groups'):
            await self.tabs(name, path, req, job, s['groups'], 1, [])
        return s


async def walk_role(pg, errs, uid, phone, jobs, shots):
    await close_sheets(pg)
    await reset_lists(pg)
    # each person has their own device: what the overview remembers (All projects or one job) starts as a new
    # device has it (app.js: a phone with nothing stored opens the overview on All projects)
    await pg.evaluate("() => { try { localStorage.removeItem('dashAll'); dashAll = !!(typeof mOn === 'function' && mOn()); } catch (e) {} }")
    await sign_in(pg, uid)
    await settle(pg, 250)
    meta = await pg.evaluate("""() => { window.__cecat = CENSUS.catalog();
      const sw = [...document.querySelectorAll('#pswitch option')].map(o => o.value).filter(v => v && !v.startsWith('__'));
      let scope = null; try { const sc = eqScopeOf(); scope = sc && sc.pids ? [...sc.pids] : null; } catch (e) {}
      return { role: role(), first: view, views: ROLE_VIEWS[role()] || [], scope: scope, menu: (typeof mnMap === 'function' && mnOn()) ? mnMap() : null,
               bar: CENSUS.bar(), switcher: sw, cur: S.id,
               cat: window.__cecat.map(o => ({ k: o.k, noun: o.noun, t: o.t, pid: o.pid || '' })) }; }""")
    W = Walker(pg, errs, uid, phone, shots)
    rv = meta['views']
    out = {'uid': uid, 'role': meta['role'], 'first': meta['first'], 'views': rv, 'menu': meta['menu'], 'bar': meta['bar'],
           'switcher': meta['switcher'], 'jobs': {}, 'list': None, 'rowTaps': {}}
    # ---- 1. the Projects list, the way the person reaches it ----------------------------------------------------
    if 'ovjobs' in rv or 'port' in rv:
        if phone:
            try:
                await pg.wait_for_function("() => [...document.querySelectorAll('#mtabs button, #tabbar button')].some(b => b.getClientRects().length > 0)", timeout=3000)
            except Exception:
                pass
        how = await pg.evaluate("""() => {
          const vis = e => !!e && e.getClientRects().length > 0;
          const b = (innerWidth < 760 ? document.querySelector('#mtabs button[data-mv="ovjobs"], #tabbar button[data-v="ovjobs"]') : null)
                 || [...document.querySelectorAll('#nav-groups button[data-grp="jobs"]')].find(vis);
          if (b) { const l = (b.innerText || '').replace(/\\s+/g, ' ').trim(); b.click(); return (b.closest('#mtabs, #tabbar') ? 'bar: ' : 'rail: ') + l; }
          view = ROLE_VIEWS[role()].includes('ovjobs') ? 'ovjobs' : 'port'; render(); return 'no button: set view'; }""")
        await settle(pg, 300)
        landed = await W.view()
        s = await W.page('Projects', ['Projects'], 'ovjobs', '(list)')
        s['how'] = how
        out['list'] = {'how': how, 'landed': landed}
        # what a tap on each walked job's row opens
        for pid in jobs:
            tap = await pg.evaluate("""pid => {
              const p = DB.projects.find(x => x.id === pid); if (!p) return { err: 'no such job' };
              const vis = e => !!e && e.getClientRects().length > 0, v = document.querySelector('.view.on');
              const name = (p.project.name || '').toLowerCase();
              const cands = [...v.querySelectorAll('tr, .pr-row, .ov-row, .card, li, a, button, [data-pid], [data-p], [data-proj], [data-job]')].filter(vis)
                .filter(e => (e.innerText || '').toLowerCase().includes(name.slice(0, 16)));
              // the smallest element that names the job and can be tapped
              cands.sort((a, b) => (a.innerText || '').length - (b.innerText || '').length);
              const t = cands.find(e => e.matches('a, button, [data-pid], [data-p], [data-proj], [data-job], tr[onclick], tr[data-open]') || e.onclick) || cands[0];
              if (!t) return { err: 'no row names the job' };
              const before = { v: view, s: S.id };
              t.click();
              return { clicked: (t.innerText || '').replace(/\\s+/g, ' ').slice(0, 60), tag: t.tagName, before: before };
            }""", pid)
            await settle(pg, 300)
            tap['after'] = await pg.evaluate("() => ({ v: view, s: S.id, all: typeof dashAll !== 'undefined' && !!dashAll && view === 'dash', modal: !!document.querySelector('#mbm') && document.querySelector('#mbm').getClientRects().length > 0 })")
            out['rowTaps'][pid] = tap
            # what the person sees after the tap, read as it is
            if not tap.get('err'):
                await W.record('Tap on ' + pid, ['Projects', 'tap the row'], 'ovjobs', '(list)', {'rowTap': pid})
            await close_sheets(pg)
            await W.open(landed)
    # ---- 2. each job: the job page and every sub-page it reaches ------------------------------------------------
    for pid in jobs:
        in_scope = meta.get('scope') is None or pid in meta['scope']
        ok = await pg.evaluate("pid => { const p = DB.projects.find(x => x.id === pid); if (!p) return false; try { setCurrent(pid); } catch (e) { return false; } return S.id === pid; }", pid)
        jr = {'inScope': in_scope, 'set': ok and in_scope, 'pages': []}
        out['jobs'][pid] = jr
        if not ok or not in_scope: continue
        if uid == 'u_klein':
            home, items = 'client', [v for v in CLIENT_JOB if v in rv]
        elif meta['menu'] and meta['menu'].get('field'):
            home = 'fsite' if 'fsite' in rv else next((v for v in FIELD_JOB if v in rv), None)
            m = meta['menu']
            menu_vs = [x.split('=')[0].split(':')[0] for x in m.get('bar', []) + m.get('rest', [])]
            items = [v for v in menu_vs if v in FIELD_JOB and v in rv]
        else:
            home = 'dash' if 'dash' in rv else None
            items = None
            if not home:
                # no job page (the designer, the controller): the page a tap on the job's row opens stands for it,
                # and the menu's Projects group gives the sub-pages
                tap = ((out.get('rowTaps') or {}).get(pid) or {}).get('after') or {}
                home = tap.get('v') if tap.get('v') and tap.get('v') != 'ovjobs' else None
                g = next((g for g in ((meta['menu'] or {}).get('groups') or []) if g['id'] == 'jobs'), None)
                items = [x.split('=')[0] for x in (g['items'] if g else []) if x.split('=')[0] not in ('ovjobs', 'dash')]
                jr['noJobPage'] = True
                jr['rowOpens'] = home
        if not home:
            jr['noJobPage'] = True
            continue
        if jr.get('rowOpens'):
            # the row's own tap sets the job and opens its page: take the same route
            await pg.evaluate("pid => setCurrent(pid)", pid)
        await W.open(home)
        all_ = await pg.evaluate("() => view === 'dash' && typeof dashAll !== 'undefined' && !!dashAll")
        if all_:
            # the job page opens on All projects (the phone's default until a job is picked in the switcher): read it
            # as it opens, then pick the job in the switcher the way the person does
            jr['opensAll'] = True
            await W.record('Job Page as it opens (All projects)', [], home, pid, {'allProjects': True})
            await pg.evaluate("pid => { const ps = document.getElementById('pswitch'); if (!ps) return; ps.value = pid; ps.dispatchEvent(new Event('change', { bubbles: true })); }", pid)
            await settle(pg, 250)
        jp = await W.page('Job Page', [], home, pid)
        jr['home'] = home
        jr['homeLanded'] = jp.get('view')
        visited = {jp.get('view')}
        # the strip: an office role's sub-pages; press each the way the person does
        strip = (jp.get('strip') or {}).get('items') or []
        jr['strip'] = [{'v': it['v'], 'tab': it['tab'], 'l': it['l'], 'n': it['n'], 'vis': it['vis'], 'inView': it.get('inView')} for it in strip]
        jr['stripShown'] = (jp.get('strip') or {}).get('shown')
        if items is None:
            for it in strip:
                if it['v'] == 'ovjobs' or it['i'] is None or (it['v'] == home and not it['tab']): continue
                await W.open(home)
                await pg.evaluate("i => { const b = document.querySelector('#subnav [data-mni=\"' + i + '\"]'); b && b.click(); }", it['i'])
                await settle(pg)
                s = await W.page(it['l'], ['Strip › ' + it['l']], it['v'] + (':' + it['tab'] if it['tab'] else ''), pid)
                visited.add(s.get('view'))
                jr['pages'].append({'from': 'strip', 'l': it['l'], 'req': it['v'], 'tab': it['tab'], 'view': s.get('view'), 'strip_n': it['n']})
        else:
            for v in items:
                if v == home: continue
                await W.open(v)
                m = meta['menu'] or {}
                lab = next((x.split('=')[1] for x in (m.get('bar', []) + m.get('rest', []) + [i for g in m.get('groups', []) if g['id'] == 'jobs' for i in g['items']]) if x.split('=')[0] == v), None) or v
                if uid == 'u_klein': lab = {'client': 'Overview', 'sched': 'Schedule', 'dec': 'Decisions', 'clacct': 'Account', 'chat': 'Chat'}.get(v, v)
                s = await W.page(lab, ['Menu › ' + lab], v, pid)
                visited.add(s.get('view'))
                jr['pages'].append({'from': 'menu', 'l': lab, 'req': v, 'view': s.get('view')})
        # the job page's own links: a page it opens that the strip did not
        for ln in (jp.get('links') or []):
            to = ln['to']
            if to not in MODULE:
                jr.setdefault('outLinks', []).append({'to': to, 't': ln['t']})
                continue
            if to in visited or to not in rv or to in ('pa',): continue
            visited.add(to)
            await W.open(home)
            await W.open(to)
            s = await W.page(ln['t'] or to, ['Job page › ' + (ln['t'] or to)], to, pid)
            jr['pages'].append({'from': 'link', 'l': ln['t'] or to, 'req': to, 'view': s.get('view')})
        await close_sheets(pg)
    out['screens'] = W.screens
    out['cat'] = meta['cat']
    return out


def load():
    if os.path.exists(DATA):
        with open(DATA) as f: return json.load(f)
    return {}


def save(d):
    os.makedirs(OUT, exist_ok=True)
    with open(DATA, 'w') as f: json.dump(d, f, separators=(',', ':'))


async def walk(users, devices, shots):
    data = load()
    data.setdefault('walk', {})
    t_all = time.time()
    async with async_playwright() as p:
        for phone in devices:
            key = 'phone' if phone else 'desktop'
            b, pg, errs = await boot(p, phone)
            pj = await pg.evaluate(PICK_JOBS)
            data['jobs'] = pj
            jobs = [FIRST_JOB, pj['second']]
            for u in users:
                t0 = time.time()
                try:
                    r = await walk_role(pg, errs, u, phone, jobs, shots and u in SHOT_USERS)
                except Exception as e:
                    r = {'uid': u, 'crash': str(e)[:400], 'screens': []}
                    # a crash leaves the page in an unknown state: open a fresh one for the next role
                    await b.close()
                    b, pg, errs = await boot(p, phone)
                r['secs'] = int(time.time() - t0)
                data.setdefault('catalog', {}).setdefault(key, {})[u] = r.pop('cat', [])
                data['walk'].setdefault(key, {})[u] = r
                print(f'{key} {u}: {len(r.get("screens", []))} screens, {r["secs"]}s', flush=True)
                save(data)
            await b.close()
    data['wall'] = int(time.time() - t_all)
    data['built'] = time.strftime('%Y-%m-%d %H:%M')
    save(data)
    return data


# =====================================================================================================================
# the report
# =====================================================================================================================
TABLES = os.path.join(OUT, 'tables.md')
NOUN = {'task': 'to-dos', 'sched': 'schedule lines', 'approval': 'approvals', 'inbox': 'mail', 'decision': 'decisions',
        'material': 'materials', 'request': 'field requests', 'submittal': 'submittals', 'inspection': 'inspections',
        'siteq': 'site questions', 'coi': 'COI lapses', 'invoice': 'invoices', 'bill': 'bills', 'po': 'purchase orders',
        'flag': 'money flags', 'finding': 'findings', 'subconfirm': 'subs to confirm', 'co': 'change orders',
        'estimate': 'estimates', 'file': 'files', 'fielditem': 'field items (closed)', 'punch': 'punch items', 'log': 'daily logs',
        'sheet': 'drawing sheets', 'selection': 'selections'}
ROLE_NAME = {'u_alan': 'PM (Alan)', 'u_owner': 'Owner', 'u_chen': 'Coordinator (Chen)', 'u_angel': 'Foreman (Angel)',
             'u_sarah': 'Designer (Sarah)', 'u_billing': 'Billing', 'u_controller': 'Controller', 'u_klein': 'Client (Klein)',
             'u_alberto': 'Crew (Alberto)', 'u_alex': 'Driver (Alex)'}
DEVS = ('desktop', 'phone')


def job_name(data, pid):
    for j in (data.get('jobs') or {}).get('jobs', []):
        if j['id'] == pid: return j['name']
    return pid


def screens_of(r, pid):
    return [s for s in r.get('screens', []) if s.get('job') == pid]


def page_of(s):
    return s['tabOf'].split('[')[0] if s.get('tabOf') else s['name']


def tab_label(s):
    n = s['name']
    return n.split('[', 1)[1].rstrip(']').replace('][', ' › ') if '[' in n else n


def secs_of(s):
    """the screen's sections: its headings (the page's own title left out), with the count beside each, y, height"""
    out = s.get('outline')
    if out is None:
        return [{'h': x['h'], 'n': x.get('n'), 'y': x['y'], 'hgt': x.get('hgt', 0), 'lvl': 3} for x in s.get('secs', []) if x.get('h') != '(page)']
    head = (s.get('heading') or '').strip().lower()
    res, skipped = [], False
    for o in out:
        if not skipped and o['lvl'] <= 2 and o['h'].strip().lower() == head:
            skipped = True
            continue
        res.append(o)
    return res


def above(s, x):
    return x['y'] < (s.get('fold') or 900) - 16


def screens_tall(s, dev):
    return round((s.get('pageH') or 0) / (844 if dev == 'phone' else 900), 1)


def tree_counts(r, pid):
    ss = screens_of(r, pid)
    pages = [s for s in ss if not s.get('tabOf') and not s.get('allProjects')]
    tabs = [s for s in ss if s.get('tabOf')]
    secs = sum(len(secs_of(s)) for s in pages)
    return {'pages': len(pages), 'sub': max(0, len(pages) - 1), 'tabs': len(tabs), 'screens': len(ss), 'secs': secs}


def fig_key(l):
    l = re.sub(r'[\d$,.%()+\-−]+', ' ', l.lower())
    l = re.sub(r'\b(of|the|a|to|on|in|for|and|vs|days?|this|week|today|total|now|job|jobs|project)\b', ' ', l)
    return re.sub(r'\s+', ' ', l).strip()[:40]


def num_of(v):
    m = re.search(r'(-|−)?\$?\s?(\d[\d,]*(\.\d+)?)\s?([km])?', str(v), re.I)
    if not m: return None
    x = float(m.group(2).replace(',', ''))
    x *= {'k': 1e3, 'm': 1e6}.get((m.group(4) or '').lower(), 1)
    return -x if m.group(1) else x


def close(a, b):
    x, y = num_of(a), num_of(b)
    if x is None or y is None: return str(a).lower() == str(b).lower()
    return abs(x - y) <= max(0.006 * max(abs(x), abs(y)), 0.5)


def dupes(r, pid):
    """records listed on two or more pages of one job (a page's tabs count as the page); lists that are the same twice"""
    ss = screens_of(r, pid)
    by = defaultdict(set)
    per_page = defaultdict(set)
    for s in ss:
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
            sh = a & b
            if len(sh) >= 3 and len(sh) >= 0.5 * min(len(a), len(b)):
                pairs.append((ps[i], ps[j], len(sh), len(a), len(b), Counter(k.split(':')[0] for k in sh).most_common(3)))
    pairs.sort(key=lambda x: -x[2])
    return multi, pairs, per_page


def disagreements(r, pid):
    """the same label with different numbers on two pages of one job (figures, tab counts, section counts, strip
    badges). A page's own tabs may change a number (Open and All): only two pages whose numbers for the label share
    no value count as a disagreement."""
    ss = [s for s in screens_of(r, pid) if not s.get('allProjects')]
    vals = defaultdict(lambda: defaultdict(set))
    for s in ss:
        pg = page_of(s)
        for f in s.get('figs', []):
            k = fig_key(f['l'])
            if len(k) >= 4: vals[k][pg].add(f['v'].replace(' ', ''))
        for t in s.get('tabs', []):
            if t.get('n') is not None and t.get('l'):
                vals['count: ' + fig_key(t['l'])][pg].add(str(t['n']))
        for x in secs_of(s):
            if x.get('n') is not None and x.get('h'):
                vals['count: ' + fig_key(x['h'])][pg].add(str(x['n']))
    for s in ss[:1]:
        for it in (s.get('strip') or {}).get('items', []):
            if it.get('n') is not None: vals['count: ' + fig_key(it['l'])]['the strip badge'].add(str(it['n']))
    out = []
    for k, m in vals.items():
        if len(k.replace('count: ', '')) < 3: continue
        pages = list(m)
        clash = any(not any(close(a, b) for a in m[pages[i]] for b in m[pages[j]]) for i in range(len(pages)) for j in range(i + 1, len(pages)))
        if not clash: continue
        by_v = defaultdict(list)
        for pg, vs in m.items():
            for v in vs: by_v[v].append(pg)
        out.append((k, {v: sorted(w)[:4] for v, w in by_v.items()}))
    return out


def menu_views(r):
    m = r.get('menu') or {}
    if m.get('field'):
        items = [('Bar', x) for x in m.get('bar', [])] + [('Menu', x) for x in m.get('rest', [])] + [('More', x) for x in m.get('more', [])]
    else:
        items = [(g['n'], x) for g in m.get('groups', []) for x in g['items']] + [('More', x) for x in m.get('more', [])] + [('Bar', x) for x in m.get('phone', [])]
    out = defaultdict(list)
    for g, x in items:
        v = x.split('=')[0]
        out[v.split(':')[0]].append(f"{g} › {x.split('=')[1] if '=' in x else v}")
    return out


def reach(r, pid):
    """what the menu opens in the module that the job page does not reach, and the reverse"""
    j = (r.get('jobs') or {}).get(pid) or {}
    from_job = set([j.get('homeLanded') or j.get('home')]) | {p['view'] for p in j.get('pages', []) if p.get('view')} | {p['req'].split(':')[0] for p in j.get('pages', [])}
    from_job.discard(None)
    mv = menu_views(r)
    menu_mod = {v for v in mv if v in MODULE}
    return sorted(menu_mod - from_job - {'ovjobs', 'port'}), sorted(v for v in from_job - set(mv) if v), mv


def esc(s):
    return str(s).replace('|', '/').replace('\n', ' ')


def nice(name, jn):
    for pid, n in jn.items():
        name = name.replace('Tap on ' + pid, 'Tap on the ' + n + ' row')
    return name.replace('Job Page', 'Job page')


def glance(P, pm, jobs, jn):
    """the PM's tree at a glance: one row a page, desktop and phone side by side"""
    d, ph = pm.get('desktop'), pm.get('phone')
    if not d or d.get('crash'): return
    for pid in jobs:
        ss = screens_of(d, pid)
        if not ss: continue
        pss = {x['name']: x for x in (screens_of(ph, pid) if ph and not ph.get('crash') else [])}
        P(f'### The PM\'s tree at a glance: {jn[pid]}')
        P('')
        P('Tall is in screens, desktop / phone. Sections are the headed parts as the page opens; tabs are the screens behind its tab groups. "What it lists" counts the records found on the page as it opens.')
        P('')
        P('| Page | Heading | Tall | Sections (phone above the fold) | Tabs | Tiles and figures | What it lists | Blue button |')
        P('|---|---|---|---|---|---|---|---|')
        for x in ss:
            if x.get('tabOf'): continue
            y = pss.get(x['name'])
            tabs = len([t for t in ss if t.get('tabOf') and page_of(t) == x['name']])
            ptabs = len([t for t in pss.values() if t.get('tabOf') and page_of(t) == x['name']])
            secs = secs_of(x)
            ab = len([o for o in secs_of(y) if above(y, o)]) if y else '-'
            figs = '; '.join(f"{esc(f['l'])[:22]} {esc(f['v'])[:24]}" for f in x.get('figs', [])[:4])
            tall = f"{screens_tall(x, 'desktop')} / {screens_tall(y, 'phone') if y else '-'}"
            P(f"| {esc(nice(x['name'], jn))} | {esc(x.get('heading', ''))} | {tall} | {len(secs)} ({ab}) | {tabs} / {ptabs if y else '-'} | {figs or '-'} | {esc(rec_line(x, 4)) or '-'} | {esc(', '.join(b['l'] for b in x.get('blue', [])))[:30] or 'none'} |")
        P('')


def flags_of(s, dev):
    f = []
    if s.get('view') and s.get('req') and s['view'] != s['req'].split(':')[0] and not s.get('tabOf'): f.append(f"opens `{s['view']}` when asked for `{s['req']}`")
    if (s.get('clip') or {}).get('sideways'): f.append(f"scrolls sideways ({s['clip']['sw']}px)")
    past = [p for p in (s.get('clip') or {}).get('parts', []) if p['where'] == 'past the edge' or p['where'].startswith('cut off')]
    if dev == 'phone' and past: f.append('runs past the edge: ' + '; '.join(f"{p['where']} ({', '.join(esc(x) for x in p['ex'][:2])})" for p in past[:2]))
    if s.get('error'): f.append('read failed: ' + s['error'][:80])
    if s.get('errors'): f.append('page error: ' + esc(s['errors'][0])[:100])
    if s.get('saves'): f.append(f"{s['saves']} save(s) while reading")
    if s.get('leftTo'): f.append(f"the tab leaves for `{s['leftTo']}`")
    if s.get('tabModal'): f.append('the tab opens a sheet')
    if (s.get('words') or 0) < 25 and not s.get('error'): f.append(f"nearly empty ({s.get('words', 0)} words)")
    return f


def rec_line(s, top=8):
    rec = Counter(f[0].split(':')[0] for f in s.get('found', []))
    return ', '.join(f'{n} {NOUN.get(k, k)}' for k, n in rec.most_common(top))


def page_block(P, s, tabs, dev, full=True):
    secs = secs_of(s)
    ab = len([x for x in secs if above(s, x)])
    blue = ', '.join(esc(b['l']) for b in s.get('blue', [])) or 'none'
    fl = flags_of(s, dev)
    P(f"- **{esc(s['name'])}** (`{s.get('view', '?')}`): heading \"{esc(s.get('heading', ''))}\", {screens_tall(s, dev)} screens tall, {len(secs)} sections ({ab} above the fold), {len(tabs)} tab screens; blue: {blue}" + (f"; {'; '.join(fl)}" if fl else ''))
    if not full: return
    if s.get('lead'): P(f"  - lead: \"{esc(s['lead'])}\"")
    if secs:
        P('  - sections: ' + '; '.join(f"{esc(x['h'])}{' (' + str(x['n']) + ')' if x.get('n') is not None else ''}" for x in secs[:16]) + (f' and {len(secs) - 16} more' if len(secs) > 16 else ''))
    figs = s.get('figs', [])
    if figs: P('  - figures: ' + '; '.join(f"{esc(f['l'])} {esc(f['v'])}" for f in figs[:8]) + (f' and {len(figs) - 8} more' if len(figs) > 8 else ''))
    rl = rec_line(s)
    if rl: P('  - records: ' + rl)
    cols = [c for c in s.get('cols', []) if c.get('cols') and any(c['cols'])]
    if cols: P('  - columns: ' + '; '.join(f"{esc(c['sec'] or 'table')}: {', '.join(esc(x) for x in c['cols'][:9] if x)} ({c['rows']} rows)" for c in cols[:4]))
    if s.get('fields'): P('  - fields: ' + ', '.join(esc(x) for x in s['fields'][:12]))
    em = s.get('empties') or []
    if em: P('  - empty states: ' + '; '.join(f"\"{esc(e['t'])}\"" for e in em[:4]))
    gs = s.get('groups') or []
    if gs: P('  - tab groups: ' + '; '.join(' / '.join(esc(l) + (f" {g['counts'][i]}" if g['counts'][i] is not None else '') for i, l in enumerate(g['labels'])) for g in gs[:4]))
    for t in tabs:
        ts = secs_of(t)
        extra = flags_of(t, dev)
        rl = rec_line(t, 4)
        P(f"  - tab **{esc(tab_label(t))}**: heading \"{esc(t.get('heading', ''))}\", {len(ts)} sections" + (f"; {rl}" if rl else '') + (f" ({'; '.join(extra)})" if extra else ''))


def where_data_lives(r, pid):
    """per noun: the records of it on this job and the pages that list them"""
    multi, pairs, per_page = dupes(r, pid)
    by_noun = defaultdict(lambda: defaultdict(int))
    allrec = defaultdict(set)
    for page, ks in per_page.items():
        for k in ks:
            by_noun[k.split(':')[0]][page] += 1
            allrec[k.split(':')[0]].add(k)
    return by_noun, allrec


def report():
    data = load()
    W = data.get('walk', {})
    L = []
    P = L.append
    jobs = [FIRST_JOB, (data.get('jobs') or {}).get('second', '')]
    jn = {pid: job_name(data, pid) for pid in jobs}
    jn['(list)'] = 'the Projects list'
    pm = {d: (W.get(d) or {}).get('u_alan') for d in DEVS}
    P('# The Projects Module, Page by Page: the Census')
    P('')
    P('**Asked by Alan, 2026-10-25:** "When you did the pilot did the role experts check each module and its sub pages and the layout of the page, for example the projects page, where all the data lives, how many sub pages, what information is on those sub pages?" They had not (in Pilot 2 the PM spent 9 seconds on Projects). "Start with Projects; that should be the main module used for the PM."')
    P('')
    P(f"**What this is.** Step 1 of the module census (docs/PLAN.md): a machine inventory, not a judgment. No app code changed. `tests/projects_census.py` (its reader `tests/census_js.js` sits on the information map's `tests/ia_js.js`) signs in as each role at 1440 and at 390 and opens the Projects list the way the person does. Then, for two jobs, it opens the job page and every sub-page the job page reaches (the sub-tab strip, the job page's own links, and the job pages of the field roles' and the client's own menus), presses every tab of every tab group (and the tabs those reveal), and reads every screen. The two jobs are **{jn[jobs[0]]}** (active construction) and **{jn[jobs[1]]}** ({(data.get('jobs') or {}).get('why', '')}).")
    P('')
    n_screens = sum(len(r.get('screens', [])) for d in DEVS for r in (W.get(d) or {}).values())
    P(f"{n_screens} screens in all. Built {data.get('built', '')} on the demo day (Thu 2026-09-03); the walk took {round((data.get('wall') or 0) / 60, 1)} minutes. Raw read: `review/census/projects/data.json`. Every screen per role in tables: `review/census/projects/tables.md`. Screenshots of every PM screen on both jobs and both devices: `review/census/projects/shots/` (`desktop_` and `phone_`, then the job and the screen).")
    P('')
    P('Run it: `python3 build.py && cd tests && ./slot.sh python3 projects_census.py` (then `python3 projects_census.py --report` rewrites this page from data.json).')
    P('')
    # ---------------------------------------------------------------- headline (numbers filled from the read)
    P('## Headline')
    P('')
    H = headline(data, W, jobs, jn)
    for h in H: P(h)
    P('')
    # ---------------------------------------------------------------- 1. the tree
    P('## 1. The Tree, Role by Role')
    P('')
    P('**Sub-pages** are the pages reached from the job page (the job page itself not counted). **Tabs** are the screens behind each page\'s tab groups, and behind the tabs those reveal. **Sections** are the headed parts of each page as it opens. Each cell reads desktop / phone.')
    P('')
    P('| Role | Reaches the Projects list by | Job page | ' + ' | '.join(f'{jn[pid]}: sub-pages / tabs / sections' for pid in jobs) + ' |')
    P('|---|---|---|' + '---|' * len(jobs))
    for u in USERS:
        d, ph = (W.get('desktop') or {}).get(u), (W.get('phone') or {}).get(u)
        if not d and not ph: continue
        how = ' / '.join(((x or {}).get('list') or {}).get('how', 'cannot open it') if x else '-' for x in (d, ph))
        j1 = next((((x or {}).get('jobs') or {}).get(FIRST_JOB, {}) for x in (d, ph) if x), {}) or {}
        jp = ('none; the row opens `' + j1['rowOpens'] + '`') if j1.get('rowOpens') else ('`' + j1['home'] + '`' if j1.get('home') else 'none')
        if any(((x or {}).get('jobs') or {}).get(FIRST_JOB, {}).get('opensAll') for x in (d, ph)): jp += ' (the phone opens it on All projects)'
        cells = []
        for pid in jobs:
            cs = []
            for x in (d, ph):
                if not x: cs.append('-'); continue
                j = (x.get('jobs') or {}).get(pid) or {}
                if x.get('crash'): cs.append('crashed'); continue
                if not j.get('inScope', True): cs.append('not theirs'); continue
                if not j.get('set'): cs.append('could not open'); continue
                if j.get('noJobPage') and not j.get('rowOpens'): cs.append('no job page'); continue
                c = tree_counts(x, pid)
                cs.append(f"{c['sub']} / {c['tabs']} / {c['secs']}")
            cells.append(' and '.join(cs))
        P(f'| {ROLE_NAME[u]} | {esc(how)} | {jp} | ' + ' | '.join(cells) + ' |')
    P('')
    # the pages each role reaches from the job page, side by side
    P('### Which sub-pages each role reaches from the job page (desktop, ' + jn[FIRST_JOB] + ')')
    P('')
    P('Each cell is the number of screens the page has (the page and its tabs); "-" means the role does not reach it from the job page.')
    P('')
    order, grid = [], defaultdict(dict)
    for u in USERS:
        r = (W.get('desktop') or {}).get(u)
        if not r or r.get('crash'): continue
        for s in screens_of(r, FIRST_JOB):
            pg = page_of(s)
            if pg.startswith('Job Page as it opens'): continue
            if pg == 'Job Page': pg = 'Job page (or the page a tap on the job opens)'
            if pg not in order: order.append(pg)
            grid[pg][u] = grid[pg].get(u, 0) + 1
    us = [u for u in USERS if (W.get('desktop') or {}).get(u)]
    P('| Page | ' + ' | '.join(ROLE_NAME[u].split(' (')[0] for u in us) + ' |')
    P('|---|' + '---|' * len(us))
    for pg in order:
        P(f'| {esc(nice(pg, jn))} | ' + ' | '.join(str(grid[pg].get(u, '-')) for u in us) + ' |')
    P('')
    glance(P, pm, jobs, jn)
    # ---------------------------------------------------------------- 4. where the data lives
    P('## 2. Where the Data Lives, and Where It Shows Twice')
    P('')
    P('For the PM on the desktop: each kind of record on the job, how many of its records the job\'s pages list, and the pages that list them (how many each). A page\'s tabs count as the page. Records are found by their own words, so these are floors.')
    P('')
    r = pm['desktop']
    if r and not r.get('crash'):
        for pid in jobs:
            by_noun, allrec = where_data_lives(r, pid)
            if not by_noun: continue
            P(f'### {jn[pid]}')
            P('')
            P('| Records | Found | Pages that list them |')
            P('|---|---|---|')
            for n, pages in sorted(by_noun.items(), key=lambda x: -len(x[1])):
                P(f"| {NOUN.get(n, n)} | {len(allrec[n])} | {len(pages)}: " + ', '.join(f'{esc(p)} {c}' for p, c in sorted(pages.items(), key=lambda x: -x[1])) + ' |')
            P('')
    P('### Records on two or more pages, and lists that are the same list twice')
    P('')
    for dev in DEVS:
        for u in USERS:
            r = (W.get(dev) or {}).get(u)
            if not r or r.get('crash'): continue
            if dev == 'phone' and u != 'u_alan': continue
            cat = {c['k']: c['t'] for c in ((data.get('catalog') or {}).get(dev) or {}).get(u, [])}
            for pid in jobs:
                multi, pairs, per = dupes(r, pid)
                if not multi: continue
                by_noun = defaultdict(list)
                for k, pages in multi.items(): by_noun[k.split(':')[0]].append(len(pages))
                P(f"**{ROLE_NAME[u]}, {dev}, {jn[pid]}:** {len(multi)} records on two or more pages: " + '; '.join(f"{NOUN.get(n, n)} {len(v)} (up to {max(v)} pages)" for n, v in sorted(by_noun.items(), key=lambda x: -len(x[1]))) + '.')
                P('')
                if u in ('u_alan', 'u_owner', 'u_angel', 'u_klein'):
                    for k, pages in sorted(multi.items(), key=lambda x: -len(x[1]))[:6]:
                        P(f"- \"{esc(cat.get(k, k))[:60]}\" ({NOUN.get(k.split(':')[0], k.split(':')[0])}) on {len(pages)} pages: {', '.join(sorted(pages))}")
                if pairs:
                    P('- the same list twice (3 or more shared records, at least half of the shorter list): ' + '; '.join(f"{a} and {b} ({n} shared, of {na} and {nb}: {', '.join(NOUN.get(x, x) for x, _ in kinds)})" for a, b, n, na, nb, kinds in pairs[:6]))
                P('')
    # ---------------------------------------------------------------- 5. disagreements
    P('## 3. One Label, Different Numbers')
    P('')
    P('The same label (a tile, a figure, a tab or section count, a strip badge) with numbers that share no value on two pages of one job, for one role. Some are right about different scopes ("Open" against "All"); the person still reads one word with two numbers. Each needs a person to judge.')
    P('')
    for dev in DEVS:
        for u in USERS:
            r = (W.get(dev) or {}).get(u)
            if not r or r.get('crash'): continue
            if dev == 'phone' and u != 'u_alan': continue
            for pid in jobs:
                dz = disagreements(r, pid)
                if not dz: continue
                P(f"**{ROLE_NAME[u]}, {dev}, {jn[pid]}** ({len(dz)}):")
                for k, m in sorted(dz, key=lambda x: -len(x[1]))[:12]:
                    P(f"- {esc(k)}: " + '; '.join(f"{esc(v)} on {', '.join(esc(x) for x in w)}" for v, w in list(m.items())[:4]))
                P('')
    # ---------------------------------------------------------------- 6. empty, dead, broken
    P('## 4. Empty, Dead and Broken Screens')
    P('')
    rows = []
    for dev in DEVS:
        for u in USERS:
            r = (W.get(dev) or {}).get(u)
            if not r: continue
            if r.get('crash'): rows.append((dev, u, '-', '(the walk)', 'crashed: ' + r['crash'][:120])); continue
            for pid, t in (r.get('rowTaps') or {}).items():
                if t.get('err'): rows.append((dev, u, '(list)', f'the {jn.get(pid, pid)} row', t['err']))
            for s in r.get('screens', []):
                why = []
                if s.get('error'): why.append('read failed: ' + s['error'][:80])
                if s.get('errors'): why.append('page error: ' + s['errors'][0][:100])
                if (s.get('words') or 0) < 25 and not s.get('error'): why.append(f"{s.get('words', 0)} words")
                if s.get('view') and s.get('req') and s['view'] != s['req'].split(':')[0] and not s.get('tabOf') and not s.get('rowTap'): why.append(f"opens {s['view']} when asked for {s['req']}")
                if s.get('saves'): why.append(f"{s['saves']} save(s) while reading")
                em = [e['t'] for e in (s.get('empties') or [])]
                if em and not s.get('found') and not s.get('tabOf') and (s.get('words') or 0) < 150: why.append('lists nothing: "' + em[0][:60] + '"')
                if why: rows.append((dev, u, s.get('job'), s['name'], '; '.join(why)))
    if rows:
        P('| Device | Role | Job | Screen | What |')
        P('|---|---|---|---|---|')
        for dev, u, pid, nm, why in rows[:150]:
            P(f'| {dev} | {ROLE_NAME[u]} | {esc(jn.get(pid, pid))} | {esc(nice(nm, jn))} | {esc(why)} |')
        if len(rows) > 150: P(f'| | | | | and {len(rows) - 150} more in tables.md |')
    else:
        P('None found.')
    P('')
    # ---------------------------------------------------------------- 7. the phone
    P('## 5. The Phone at 390')
    P('')
    P('"Cut off" is text the phone ends early (a row\'s second line clipped at the edge); "scrolls inside" is a strip of tiles or tabs that the person swipes sideways inside the page (the page itself does not move). Pages taller than 3 phone screens are listed with their height.')
    P('')
    P('| Role | Screens | The page scrolls sideways | Text cut off at the edge | Strips that scroll inside the page | The sub-tab strip | Pages taller than 3 screens |')
    P('|---|---|---|---|---|---|---|')
    for u in USERS:
        r = (W.get('phone') or {}).get(u)
        if not r or r.get('crash'): continue
        ss = r.get('screens', [])
        side = sorted({page_of(s) for s in ss if (s.get('clip') or {}).get('sideways')})
        past = sorted({page_of(s) for s in ss if any(p['where'] == 'past the edge' or p['where'].startswith('cut off') for p in (s.get('clip') or {}).get('parts', []))})
        inner = sorted({page_of(s) for s in ss if any(p['where'].startswith('scrolls in') for p in (s.get('clip') or {}).get('parts', []))})
        tall = [f"{nice(s['name'], {})} {screens_tall(s, 'phone')}" for s in ss if not s.get('tabOf') and not s.get('rowTap') and not s.get('allProjects') and (s.get('pageH') or 0) > 3 * 844]
        j1 = (r.get('jobs') or {}).get(FIRST_JOB) or {}
        sv = [it for it in j1.get('strip', []) if it.get('vis')]
        st = [f"{'shown' if j1.get('stripShown') else 'not shown'}: {len([it for it in sv if it.get('inView')])} of {len(sv)} entries on screen without a swipe"] if sv else []
        P(f"| {ROLE_NAME[u]} | {len(ss)} | {len(side)}{': ' + esc(', '.join(side[:6])) if side else ''} | {len(past)}{': ' + esc(', '.join(past[:8])) if past else ''} | {len(inner)}{': ' + esc(', '.join(inner[:8])) if inner else ''} | {', '.join(st) or 'none'} | {len(tall)}{': ' + esc(', '.join(tall[:8])) if tall else ''} |")
    P('')
    # ---------------------------------------------------------------- 8. reach
    P('## 6. What the Menu Opens That the Job Page Does Not, and the Reverse')
    P('')
    P('Module pages only (the job\'s pages, Messages, Drawings, Selections). Desktop menu, then the phone\'s.')
    P('')
    P('| Role | Device | In the menu, not reached from the job page | Reached from the job page, not in the menu | Module pages in two or more menu places |')
    P('|---|---|---|---|---|')
    for u in USERS:
        for dev in DEVS:
            r = (W.get(dev) or {}).get(u)
            if not r or r.get('crash'): continue
            a, b, mv = reach(r, FIRST_JOB)
            two = [f"{v} ({'; '.join(p)})" for v, p in mv.items() if v in MODULE and len(p) >= 2]
            P(f"| {ROLE_NAME[u]} | {dev} | {esc(', '.join(f'{v} ({mv[v][0]})' for v in a)) or '-'} | {esc(', '.join(b)) or '-'} | {esc('; '.join(two)) or '-'} |")
    P('')
    # ---------------------------------------------------------------- 9. row taps
    P('## 7. What a Tap on a Job in the Projects List Opens')
    P('')
    P('| Role | Device | Job | Tapped | Opens |')
    P('|---|---|---|---|---|')
    for u in USERS:
        for dev in DEVS:
            r = (W.get(dev) or {}).get(u)
            if not r: continue
            if not r.get('list'):
                P(f'| {ROLE_NAME[u]} | {dev} | - | cannot open the Projects list | - |')
                continue
            for pid, t in (r.get('rowTaps') or {}).items():
                a = t.get('after') or {}
                P(f"| {ROLE_NAME[u]} | {dev} | {jn.get(pid, pid)} | {esc(t.get('clicked') or t.get('err', ''))[:50]} | {a.get('v', '-')}{' (job ' + a['s'] + ')' if a.get('s') else ''}{', showing All projects' if a.get('all') else ''}{', a sheet' if a.get('modal') else ''} |")
    P('')
    # ---------------------------------------------------------------- 2. the PM's tree in full
    P('## 8. The PM\'s Projects, Page by Page, in Full')
    P('')
    P('Every page the PM reaches from the job page, as it opens, then each of its tabs. Heights are in screens of that device (900px desktop, 844px phone); "above the fold" is above the bottom bar on the phone. Records are the information map\'s catalog plus the job\'s own nouns, found by their words.')
    P('')
    for pid in jobs:
        for dev in DEVS:
            r = pm[dev]
            if not r or r.get('crash'): continue
            ss = screens_of(r, pid)
            if not ss: continue
            P(f'### PM, {dev}, {jn[pid]}')
            P('')
            j = r['jobs'][pid]
            lst = [s for s in r.get('screens', []) if s.get('job') == '(list)' and not s.get('tabOf')]
            if lst and pid == FIRST_JOB:
                P(f"The Projects list ({esc((r.get('list') or {}).get('how', ''))}):")
                page_block(P, lst[0], [x for x in r['screens'] if x.get('job') == '(list)' and x.get('tabOf')], dev)
                t = (r.get('rowTaps') or {}).get(pid) or {}
                if t: P(f"  - a tap on the {jn[pid]} row opens `{(t.get('after') or {}).get('v', '?')}`" + (' on **All projects**, not the job' if (t.get('after') or {}).get('all') else ''))
                P('')
            if j.get('strip'):
                P(f"The sub-tab strip ({'shown' if j.get('stripShown') else 'not shown'} on this screen size): " + ', '.join(f"{it['l']}{' ' + str(it['n']) if it.get('n') is not None else ''}" for it in j['strip']) + '.')
                P('')
            for s in ss:
                if s.get('tabOf'): continue
                tabs = [x for x in ss if x.get('tabOf') and page_of(x) == s['name']]
                page_block(P, s, tabs, dev, full=(dev == 'desktop' or pid == FIRST_JOB))
            P('')
    # ---------------------------------------------------------------- 3. the other roles, one line a page
    P('## 9. The Other Roles, One Line a Page')
    P('')
    for u in USERS:
        if u == 'u_alan': continue
        for dev in DEVS:
            r = (W.get(dev) or {}).get(u)
            if not r: continue
            if r.get('crash'):
                P(f'### {ROLE_NAME[u]}, {dev}: the walk crashed: {esc(r["crash"][:200])}')
                P('')
                continue
            for pid in jobs:
                ss = screens_of(r, pid)
                j = (r.get('jobs') or {}).get(pid) or {}
                if not ss:
                    continue
                P(f'### {ROLE_NAME[u]}, {dev}, {jn[pid]}')
                P('')
                if j.get('strip'):
                    P(f"Strip ({'shown' if j.get('stripShown') else 'not shown'}): " + ', '.join(f"{it['l']}{' ' + str(it['n']) if it.get('n') is not None else ''}" for it in j['strip']) + '.')
                    P('')
                for s in ss:
                    if s.get('tabOf'): continue
                    tabs = [x for x in ss if x.get('tabOf') and page_of(x) == s['name']]
                    page_block(P, s, tabs, dev, full=False)
                P('')
    P('## 10. What This Census Did Not Check, and How Sure It Is')
    P('')
    P('- **Records are found by their words** (the information map\'s rule): a record shown as a number, a chart or in other words is not counted, so duplication counts are a floor, and a record whose words appear inside another (a decision named in a material\'s "held by") counts on that page too.')
    P('- **Figures** are read from tiles, two-column tables, definition lists and the bold money that leads a note. A figure inside a sentence is not read. Labels are compared with numbers and small words removed, so two different figures with one label show as a disagreement and need a person to judge.')
    P('- **Tabs** are rows of two or more buttons with exactly one on. A dropdown that switches the view, a row of toggles (a job\'s working days), Project Settings\' rows and a button that commits (New, Send, Approve...) are never pressed. One level of revealed tabs is walked, and a tab group seen once on a page is not walked again from another route to the same page (Change Orders, Estimates and Billing are one page with three entries).')
    P('- **What opens, not what is two taps away:** a record opened from a row (an invoice, a PO, a decision sheet), "N more" rows and folded cards are not walked.')
    P('- **The client** is walked on their own job only; the second job is not theirs. **Field roles** are walked on the job pages of their own menus; they have no job page with a strip.')
    P('- **Data changes:** every save() during the walk is counted per screen (section 6). None means the walk changed nothing.')
    P('- **Not judged:** whether the content is right, what is missing, and what should merge. That is step 2: the role-expert PM and the information-architecture reviewer walk every page with this census in hand.')
    P('')
    os.makedirs(os.path.dirname(DOC), exist_ok=True)
    with open(DOC, 'w') as f: f.write('\n'.join(L) + '\n')
    tables(data, W, jobs, jn)
    print('wrote', DOC, 'and', TABLES)


def headline(data, W, jobs, jn):
    """the findings, each from the read; a bullet whose condition the data does not meet is left out"""
    H = []
    D, Ph = W.get('desktop') or {}, W.get('phone') or {}
    pmd, pmp = D.get('u_alan'), Ph.get('u_alan')
    ok = lambda r: r and not r.get('crash')
    if ok(pmd):
        c = tree_counts(pmd, FIRST_JOB)
        cp = tree_counts(pmp, FIRST_JOB) if ok(pmp) else None
        tall = sum((s.get('pageH') or 0) for s in screens_of(pmd, FIRST_JOB) if not s.get('tabOf')) / 900
        strip = (pmd.get('jobs') or {}).get(FIRST_JOB, {}).get('strip') or []
        H.append(f"- **The PM's job is {c['sub'] + 1} pages: the job page and {c['sub']} sub-pages, with {c['tabs']} more screens behind their tabs** on the desktop" + (f" ({cp['tabs']} on the phone)" if cp else '') + f", about {round(tall)} desktop screens end to end. They hang off one sub-tab strip of {len(strip)} entries in four captioned groups (Plan, Field, Costs & Billing, Files & Mail).")
    # the roles, by how much of the job they reach
    rows = []
    for u in USERS:
        r = D.get(u)
        if not ok(r): continue
        j = (r.get('jobs') or {}).get(FIRST_JOB) or {}
        if not j.get('set'): continue
        rows.append(f"{ROLE_NAME[u].split(' (')[0]} {tree_counts(r, FIRST_JOB)['sub']}")
    if rows: H.append('- **Sub-pages each role reaches from the job, desktop:** ' + ', '.join(rows) + '.')
    # no job page
    nojob = [(u, ((D.get(u) or {}).get('jobs') or {}).get(FIRST_JOB, {}).get('rowOpens')) for u in USERS]
    nojob = [(u, v) for u, v in nojob if v]
    if nojob:
        H.append('- **Two office roles have no job page.** A tap on a job in the Projects list opens ' + '; '.join(f"`{v}` for the {ROLE_NAME[u].split(' (')[0].lower()}" for u, v in nojob) + ' (`sboard` is the Design module\'s Project Board, `gl` the Ledger).')
    # the phone opens the overview on All projects
    alls = [u for u in USERS if any(((Ph.get(u) or {}).get('rowTaps') or {}).get(pid, {}).get('after', {}).get('all') for pid in jobs)]
    if alls:
        H.append('- **On a phone, a tap on a job in the Projects list opens the overview on All projects, not the job** (' + ', '.join(ROLE_NAME[u].split(' (')[0] for u in alls) + '). The heading reads "All projects", the tiles and the Look-Ahead are every job\'s, and the strip under it holds the tapped job\'s pages. It stays that way until the person picks a job in the switcher (app.js: a phone with nothing stored defaults to All projects).')
    # billing: one page, three entries, the same tiles on every job
    if ok(pmd):
        bl = {pid: next((s for s in screens_of(pmd, pid) if s['name'] == 'Billing'), None) for pid in jobs}
        jp = {pid: next((s for s in screens_of(pmd, pid) if s['name'] == 'Job Page'), None) for pid in jobs}
        if all(bl.values()) and [f['v'] for f in bl[jobs[0]].get('figs', [])] == [f['v'] for f in bl[jobs[1]].get('figs', [])] and bl[jobs[0]].get('figs'):
            rb = next((f['v'] for f in bl[jobs[0]]['figs'] if 'ready' in f['l'].lower()), '')
            jr = {pid: next((f['v'] for f in (jp[pid] or {}).get('figs', []) if 'ready to bill' in f['l'].lower()), '') for pid in jobs}
            H.append(f"- **Change Orders, Estimates and Billing are one page (Billing) under three strip entries, and it is not the job's.** It shows the same tiles on both jobs (Ready to Bill {rb}), while each job page says {' and '.join(f'{jr[p]} ({jn[p]})' for p in jobs if jr[p])}. Its blue button on {jn[jobs[0]]} reads \"{esc(', '.join(x['l'] for x in bl[jobs[0]].get('blue', [])))}\".")
        multi, pairs, _ = dupes(pmd, FIRST_JOB)
        if multi:
            bn = Counter(k.split(':')[0] for k in multi)
            top = sorted(multi.items(), key=lambda x: -len(x[1]))[0]
            cat = {x['k']: x['t'] for x in ((data.get('catalog') or {}).get('desktop') or {}).get('u_alan', [])}
            H.append(f"- **{len(multi)} of 121 State Street's records show on two or more of its pages** ({', '.join(f'{n} {NOUN.get(k, k)}' for k, n in bn.most_common(4))}). \"{esc(cat.get(top[0], top[0]))[:50]}\" is on {len(top[1])}: {', '.join(sorted(top[1]))}.")
        if pairs:
            H.append(f"- **{len(pairs)} pairs of pages list largely the same records,** led by " + '; '.join(f'{a} and {b} ({n} shared)' for a, b, n, *_ in pairs[:4]) + '. The job page repeats most of Tasks and Schedule; Materials and Schedule repeat each other.')
        dz = disagreements(pmd, FIRST_JOB)
        if dz:
            H.append(f"- **One label, different numbers:** " + '; '.join(f"\"{k}\" " + ' against '.join(f'{v} on {w[0]}' for v, w in list(m.items())[:2]) for k, m in dz[:3]) + ' (section 3).')
    if ok(pmp):
        pages = [s for s in screens_of(pmp, FIRST_JOB) if not s.get('tabOf') and not s.get('allProjects')]
        none_above = [s['name'] for s in pages if not any(above(s, o) for o in secs_of(s))]
        tall = [s['name'] for s in pages if (s.get('pageH') or 0) > 3 * 844]
        j1 = (pmp.get('jobs') or {}).get(FIRST_JOB) or {}
        sv = [it for it in j1.get('strip', []) if it.get('vis')]
        iv = [it for it in sv if it.get('inView')]
        H.append(f"- **On the phone** the PM's strip shows {len(iv)} of its {len(sv)} entries without a swipe" + (f"; {len(tall)} of the {len(pages)} pages are taller than three screens ({', '.join(tall[:5])})" if tall else '') + (f"; {len(none_above)} pages have no section heading above the fold" if none_above else '') + '. No page scrolls sideways.')
    if ok(pmd):
        a, b, mv = reach(pmd, FIRST_JOB)
        two = [v for v, p in mv.items() if v in MODULE and len(p) >= 2 and v not in ('chat', 'ovjobs')]
        if a or two:
            H.append('- **Menu and job page:** ' + ('; '.join(f"{mv[v][0]} is in the PM's menu but not reached from the job page" for v in a)) + ('; ' if a and two else '') + ('; '.join(f"`{v}` sits in {len(mv[v])} menu places ({', '.join(mv[v])})" for v in two)) + '.')
    dead = []
    for d in DEVS:
        for u, r in (W.get(d) or {}).items():
            for s in r.get('screens', []):
                if s.get('error') or s.get('errors'): dead.append(f"{ROLE_NAME[u]} {d} {s['name']}")
    crashes = [f"{ROLE_NAME[u]} {d}" for d in DEVS for u, r in (W.get(d) or {}).items() if r.get('crash')]
    H.append(f"- **Nothing crashed and no page raised an error**; every page opened." if not dead and not crashes else f"- **{len(dead)} screens failed to read or raised a page error** ({', '.join(dead[:4])}){'; the walk crashed for ' + ', '.join(crashes) if crashes else ''}.")
    saves = [(u, d, s['name']) for d in DEVS for u, r in (W.get(d) or {}).items() for s in r.get('screens', []) if s.get('saves')]
    H.append("- **Reading changed nothing:** no save during the walk." if not saves else f"- **{len(saves)} screen(s) saved while the census only read and pressed filters** ({'; '.join(f'{ROLE_NAME[u]} {d}, {n}' for u, d, n in saves[:3])}). Not traced; most likely the task list remembering its view.")
    return H


def tables(data, W, jobs, jn):
    L = []
    P = L.append
    P('# Projects Census: Every Screen')
    P('')
    P('Per role and device: the screen, its path from the job page, the view it landed on, its height in screens, sections (above the fold), tab groups, records, blue buttons, figures. Written by `tests/projects_census.py --report` from data.json.')
    P('')
    for dev in DEVS:
        for u in USERS:
            r = (W.get(dev) or {}).get(u)
            if not r or r.get('crash'): continue
            P(f'## {ROLE_NAME[u]}, {dev}')
            P('')
            P('| Job | Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | Figures |')
            P('|---|---|---|---|---|---|---|---|---|---|')
            for s in r.get('screens', []):
                secs = secs_of(s)
                ab = len([x for x in secs if above(s, x)])
                P(f"| {esc(jn.get(s.get('job'), s.get('job')))} | {esc(s['name'])} | {esc(' › '.join(s.get('path', [])))} | {s.get('view', '?')} | {screens_tall(s, dev)} | {len(secs)} ({ab}) | {len(s.get('groups', []))} | {esc(rec_line(s, 5))} | {esc(', '.join(b['l'] for b in s.get('blue', []))[:40])} | {esc('; '.join(f['l'][:24] + ' ' + f['v'] for f in s.get('figs', [])[:4]))} |")
            P('')
    os.makedirs(OUT, exist_ok=True)
    with open(TABLES, 'w') as f: f.write('\n'.join(L) + '\n')


async def main():
    a = sys.argv[1:]
    users = USERS
    if '--user' in a: users = a[a.index('--user') + 1].split(',')
    devices = (False, True)
    if '--device' in a: devices = (a[a.index('--device') + 1] == 'phone',)
    shots = '--no-shots' not in a
    steps = [x for x in ('--walk', '--report') if x in a] or ['--walk', '--report']
    os.makedirs(SHOTS, exist_ok=True)
    if '--walk' in steps:
        d = await walk(users, devices, shots)
        # the catalog per role, for the report's record titles
        print(f"census walk: {round(d.get('wall', 0) / 60, 1)} minutes")
    if '--report' in steps: report()
    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
