"""counts_lint: one question, one number (BACKLOG.md §0 item 2).

For each role (owner, pm, coord, billing, controller, designer, foreman, client) on desktop 1440x900,
plus foreman and client on phone 390x844, it walks every view the role may open and fails when:
  (a) one visible label shows two different numbers for one role and one scope
      (rail badge, sub-tab badge, tile, card header "N · ...", "All N" button, chip, header line);
  (b) a tile, chip, tab badge or "All N" button differs from the rows its target shows
      (it is clicked for real, then the list's "N of M" or its rows are counted);
  (c) a rail badge differs from its overview's count, or from needs(gid);
  (d) Ask's headline count (paAsk(q).headline) differs from the screen that lists the same things.

Each flag prints as `RULE | role | label | numbers seen with where`. The last line is `N flags`; exit 1 if N > 0.
  python3 counts_lint.py [--role owner,pm] [--json] [--verbose] [--all-projects]
--all-projects also runs the click checks (b) on every job, not just the current one (slower).
Labels are normalised: case, punctuation, trailing counts and plural "s" are ignored. One-word and generic
labels on tiles, chips and header lines ("Late", "All", "Everything", "Overdue") are qualified with the
page heading, because "Late" on Tasks and "Late" on Decisions are different questions.
Scope is the firm for firm views and the job for project views, so a job's Today is compared only with the
same job's other views."""
import asyncio, re, sys, json, time, argparse
from harness import *

RUNS = [  # (role tag, user id, phone)
    ('owner', 'u_owner', False), ('pm', 'u_alan', False), ('coord', 'u_chen', False),
    ('billing', 'u_billing', False), ('controller', 'u_controller', False), ('designer', 'u_sarah', False),
    ('foreman', 'u_angel', False), ('client', 'u_klein', False),
    ('foreman', 'u_angel', True), ('client', 'u_klein', True),
]
ASK_JOB = '121 State Street'
ASK_PERSON = 'Chen'
SKIP_VIEWS = {'pa', 'conn', 'setup'}  # Ask itself, connections, setup wizard: no counted lists

# Labels that only mean something next to the page they sit on.
GENERIC = {'all', 'everything', 'open', 'done', 'late', 'overdue', 'today', 'waiting', 'mine', 'everyone',
           'unassigned', 'due now', 'this week', 'next 7 day', 'no date', 'blocked', 'new', 'active', 'pending',
           'draft', 'sent', 'paid', 'approved', 'closed', 'call', 'bill', 'hour', 'decision', 'review',
           'to review', 'to approve', 'urgent', 'at risk', 'on hold', 'won', 'lost', 'needs you'}

# ---------------------------------------------------------------- in-page helpers
JS_HELPERS = r"""
() => {
  const vis = el => { if (!el) return false; const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden' && el.offsetParent !== null; };
  const txt = el => (el ? (el.innerText || el.textContent || '') : '').replace(/\s+/g, ' ').trim();
  const cnt = s => /^\d{1,4}\s*(days?|d|h|hrs?|hours?|min|wks?|weeks?|mos?|months?|%|yrs?)\b/i.test(String(s).trim()) ? null : lead(s);
  const lead = s => { const m = String(s).trim().match(/^(\d{1,4})(?![\d.,\/:%$])(?:\s|$)/); return m ? +m[1] : null; };
  const V = () => document.querySelector('.view.on');
  const title = () => { const v = V(); if (!v) return '';
    const h = [...v.querySelectorAll('.ph h2, h2, h1')].find(vis); return h ? txt(h) : ''; };
  const nOf = b => { const n = b.querySelector('.n, i.n'); return n ? txt(n) : ''; };
  const minusN = b => { const c = b.cloneNode(true); c.querySelectorAll('.n, i.n, svg').forEach(x => x.remove()); return txt(c); };
  const markN = el => { if (!el) return null;
    const g = el.querySelector('.gl-v, b, .n, i.n'); if (g && lead(txt(g)) != null) return lead(txt(g));
    const m = txt(el).match(/(\d{1,4})/); return m ? +m[1] : null; };

  window.__cl = {
    vis, txt, lead, title,
    // every label/number pair on the screen right now
    collect() {
      const out = [], v = V(); if (!v) return { view: '', title: '', obs: [] };
      const vid = v.id.replace(/^v-/, ''), T = title();
      const push = (kind, label, n, extra) => { label = String(label || '').trim();
        if (!label || n == null || isNaN(n)) return; out.push(Object.assign({ kind, label, n, title: T }, extra || {})); };
      document.querySelectorAll('#nav-groups button[data-grp]').forEach(b => { if (!vis(b)) return;
        const s = nOf(b); push('rail', minusN(b), s ? +s : 0, { grp: b.dataset.grp, target: b.dataset.v, implicit: !s }); });
      document.querySelectorAll('#mtabs button[data-mv]').forEach(b => { if (!vis(b)) return;
        const s = nOf(b); push('rail', minusN(b), s ? +s : 0, { target: b.dataset.mv, implicit: !s, phone: 1 }); });
      document.querySelectorAll('#subnav [data-sub]').forEach(b => { if (!vis(b)) return;
        const s = nOf(b); if (s) push('subtab', minusN(b), +s, { target: b.dataset.sub }); });
      v.querySelectorAll('button.gl').forEach(b => { if (!vis(b)) return;
        const k = b.querySelector('.gl-k'), val = b.querySelector('.gl-v');
        push('tile', txt(k), cnt(txt(val)), { tl: b.dataset.tl, static: b.classList.contains('static') }); });
      v.querySelectorAll('.kpi').forEach(b => { if (!vis(b)) return;
        const val = b.querySelector('b'), k = b.querySelector('span'); if (val && k) push('tile', txt(k), cnt(txt(val))); });
      v.querySelectorAll('.ctabs button, .seg button, .sub-tabs button, .td-tabs button').forEach(b => { if (!vis(b)) return;
        const s = nOf(b); if (s && lead(s) != null) push('chip', minusN(b), +s); });
      v.querySelectorAll('h2, h3, h4').forEach(h => { if (!vis(h)) return;
        const t = txt(h), m = t.match(/^(.+?)\s*(?:·|—|–|:)\s*(\d{1,4})$/);
        if (m) push('heading', m[1], +m[2]);
        let s = h.nextElementSibling;
        for (let i = 0; s && i < 2; i++, s = s.nextElementSibling) {
          const st = txt(s), mm = st.match(/^(\d{1,4}) · /); if (mm) { push('card', t, +mm[1]); break; } }
        const hd = h.parentElement; if (hd) [...hd.querySelectorAll(':scope > button, :scope > a')].forEach(b => {
          const mm = txt(b).match(/^All (\d{1,4})$/); if (mm && vis(b)) push('allbtn', t, +mm[1]); });
      });
      v.querySelectorAll('.ph .lead, .ov-count').forEach(el => { if (!vis(el)) return;
        if (el.classList.contains('ov-count')) { const n = lead(txt(el)); push('ovcount', T, n == null ? 0 : n, { grp: el.dataset.ovneeds }); }
        txt(el).split(/ · /).forEach(seg => { const m = seg.match(/^(\d{1,4}) ([A-Za-z][^\d]{2,60})$/); if (m) push('lead', m[2], +m[1]); }); });
      v.querySelectorAll('[data-ocbadge]').forEach(el => { if (!vis(el)) return; push('marked', T, markN(el), { badge: el.dataset.ocbadge }); });
      return { view: vid, title: T, obs: out };
    },
    // the rows a list on the screen shows now
    rows(gridId, want) {
      const v = V(); if (!v) return null;
      if (gridId) { const g = v.querySelector(`[data-grid="${gridId}"] .cnt`);
        if (g) { const m = txt(g).match(/(\d+) of (\d+)/); if (m) return { n: +m[1], how: `"${txt(g)}" in list ${gridId}` }; } }
      const cands = [];
      const lists = [['.m-appr-list', '.m-appr', 'approval cards'], ['.ib-list', '.ib-item', 'inbox items'],
                     ['.t2-list', '.t2-row', 'task rows'], ['.fgrid', '.fcard', 'document cards']];
      for (const [c, r, how] of lists) { const box = v.querySelector(c);
        if (box && vis(box)) cands.push({ n: box.querySelectorAll(r).length, how }); }
      // Today's one queue (lane "today"): the cards shown plus what "N more" (in place, or "N more in <page>") holds
      const tdy = v.querySelector('.td-do[data-tdytab]');
      if (tdy) { const mm = tdy.querySelector('.td-more'), k = mm ? (txt(mm).match(/^(\d+) more/) || []) : [];
        cands.push({ n: tdy.querySelectorAll('.td-card').length + (k[1] ? +k[1] : 0), how: `Today's ${tdy.dataset.tdytab} cards and "N more"` }); }
      const rev = [...v.querySelectorAll('.ls-rev-row')].filter(vis);
      if (rev.length) cands.push({ n: rev.reduce((a, r) => a + (lead(txt(r.querySelector('b'))) || 0), 0), how: `the sum of ${rev.length} review line(s)` });
      [...v.querySelectorAll('.dg .cnt')].filter(vis).forEach((g, i) => { const m = txt(g).match(/(\d+) of (\d+)/);
        if (m) cands.push({ n: +m[1], how: `"${txt(g)}" in list ${i + 1} on the page` }); });
      if (!cands.length) [...v.querySelectorAll('table')].filter(t => vis(t) && t.querySelector('tbody')).forEach((t, i) => {
        const rs = [...t.querySelectorAll(':scope > tbody > tr')].filter(tr => vis(tr) && tr.querySelectorAll(':scope > td').length > 1);
        cands.push({ n: rs.length, how: `${rs.length} rows in table ${i + 1} on the page` }); });
      if (!cands.length) { const empty = [...v.querySelectorAll('.dg .empty')].filter(vis)[0];
        if (empty) cands.push({ n: 0, how: 'an empty list' }); }
      if (!cands.length) return null;
      // lenient: when the page shows several lists, any one that holds the stated number counts as a match
      return cands.find(c => c.n === want) || cands[0];
    },
    marked(badge) { const v = V(); const el = v && [...v.querySelectorAll(`[data-ocbadge="${badge}"]`)].find(vis);
      return el ? { n: markN(el), how: `"${txt(el).slice(0, 50)}" (marked as this badge's source)` } : null; },
  };
}
"""

def singular(w):
    if len(w) > 3 and w.endswith('ies'): return w[:-3] + 'y'
    if len(w) > 3 and w.endswith('s') and not w.endswith('ss'): return w[:-1]
    return w

def norm(label):
    s = label.lower().replace('’', '').replace("'", '').replace('&', ' and ')
    s = re.sub(r'\(\d+\)', ' ', s)
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = re.sub(r'(\s\d+)+\s*$', '', ' ' + s).strip()
    return ' '.join(singular(w) for w in s.split())

def key_for(o):
    k = norm(o['label'])
    if not k: return None
    if o['kind'] == 'lead' or (o['kind'] in ('tile', 'chip', 'heading') and (k in GENERIC or ' ' not in k)):
        k = norm(o['title'] or o['view']) + ' > ' + k
    return k

def first_int(s):
    m = re.search(r'(?<![\d$.,])(\d{1,4})(?![\d.,%])', s or '')
    return int(m.group(1)) if m else None

class Lint:
    def __init__(self, args):
        self.args = args; self.flags = []; self.notes = []; self.seen = set()
    def flag(self, rule, run, label, seen):
        sig = (rule, run, label, seen)
        if sig in self.seen: return
        self.seen.add(sig); self.flags.append({'rule': rule, 'role': run, 'label': label, 'seen': seen})
        if not self.args.json: print(f'{rule} | {run} | {label} | {seen}', flush=True)
    def note(self, s):
        self.notes.append(s)
        if self.args.verbose and not self.args.json: print('  note:', s, flush=True)

# ---------------------------------------------------------------- page driving
async def settle(pg, ms=120):
    await pg.wait_for_timeout(ms)

async def cur_view(pg):
    return await pg.evaluate("() => view")

async def to_view(pg, v):
    await pg.evaluate("v => { view = v; render(); }", v); await settle(pg)
    return await cur_view(pg) == v

async def set_job(pg, pid):
    await pg.evaluate("id => { try { setCurrent(id); } catch (e) {} }", pid)

async def collect(pg):
    return await pg.evaluate("() => __cl.collect()")

async def click(pg, loc):
    try:
        await loc.scroll_into_view_if_needed(timeout=2000)
        await loc.click(timeout=3000)
    except Exception:
        try: await loc.evaluate("el => el.click()")
        except Exception: return False
    await settle(pg, 180)
    return True

# ---------------------------------------------------------------- one role
async def run_role(pg, lint, tag, uid, phone):
    run = tag + ('@phone' if phone else '')
    t0 = time.time()
    await sign_in(pg, uid)
    await pg.evaluate(JS_HELPERS)
    info = await pg.evaluate(r"""uid => {
      const pv = new Set(); (typeof NAV_GROUPS !== 'undefined' ? NAV_GROUPS : IA_GROUPS).forEach(g => { if (g.proj) g.views.forEach(v => pv.add(v)); });
      ['subm','photos','cos','budget','sched','dec','tasks','insp','field','mat','files','costs','inbox','chat','recv','proj','dash','client','ftoday','fsite','fcrew','flog','fraise']
        .forEach(v => pv.add(v));
      ['port','ovjobs','ovstudio','studio','sday','tkall'].forEach(v => pv.delete(v));
      const sw = document.getElementById('pswitch');
      let jobs = sw ? [...sw.options].map(o => o.value).filter(v => DB.projects.some(p => p.id === v)) : [];
      if (role() === 'client') {   // the switcher is hidden from a client: only their own jobs count
        const u = (DB.users || []).find(x => x.id === uid) || {};
        jobs = DB.projects.filter(p => p.clientId === u.clientId).map(p => p.id); }
      if (!jobs.length && typeof S !== 'undefined' && S) jobs = [S.id];
      return { views: (ROLE_VIEWS[role()] || []).slice(), projViews: [...pv], jobs, cur: S ? S.id : null,
               role: role(), names: Object.fromEntries(DB.projects.map(p => [p.id, p.project.name])) };
    }""", uid)
    views = [v for v in info['views'] if v not in SKIP_VIEWS]
    proj_views = set(info['projViews'])
    jobs = info['jobs'] or [info['cur']]
    cur = info['cur'] if info['cur'] in jobs else jobs[0]
    names = info['names']
    def scope_of(v, pid):  # Mercer & Bond views are the owner's other workspace; project views are per job
        if v.startswith('mb'): return 'mercer-bond'
        return ('job:' + names.get(pid, pid)) if v in proj_views else 'firm'

    # ---- pass 1: read every view (project views once per job), no clicks
    obs = []          # (scope, key, n, where, raw)
    pages = []        # (view, pid) actually reached
    for pid in jobs:
        await set_job(pg, pid)
        for v in views:
            if pid != jobs[0] and v not in proj_views: continue
            try:
                ok = await to_view(pg, v)
            except Exception as e:
                lint.note(f'{run}: {v} did not render ({str(e)[:80]})'); continue
            if not ok: continue
            r = await collect(pg)
            pages.append((v, pid))
            if lint.args.verbose: print(f'  {run} read {v} {names.get(pid, "") if v in proj_views else ""} ({len(r["obs"])} numbers)', flush=True)
            for o in r['obs']:
                o['view'] = v
                if o['kind'] == 'rail': sc = scope_of(o.get('target', ''), pid)   # a client's rail follows the job
                elif o['kind'] == 'subtab': sc = scope_of(o.get('target', v), pid)
                else: sc = scope_of(v, pid)
                obs.append((sc, o, f"{v}{'@' + names.get(pid, pid) if v in proj_views else ''} {o['kind']}"))
    # rule (a)
    groups = {}
    for sc, o, where in obs:
        if o.get('implicit'): continue           # an empty badge is not a stated number
        if o['kind'] == 'ovcount': continue      # checked under (c)
        k = key_for(o)
        if not k: continue
        groups.setdefault((sc, k), {}).setdefault(o['n'], []).append(where)
    if lint.args.dump:
        with open(lint.args.dump, 'a') as fh:
            for (sc, k), byn in sorted(groups.items()):
                fh.write(f"{run} | {sc} | {k} | " + '; '.join(f"{n}@{','.join(sorted(set(w))[:6])}" for n, w in sorted(byn.items())) + '\n')
    for (sc, k), byn in sorted(groups.items()):
        if len(byn) > 1:
            seen = '; '.join(f"{n} at {', '.join(sorted(set(w))[:4])}{' …' if len(set(w)) > 4 else ''}" for n, w in sorted(byn.items()))
            lint.flag('A', run, f'{k} [{sc}]', seen)

    # ---- rule (c): rail badge = overview count = needs(gid)
    await set_job(pg, cur)
    await to_view(pg, views[0])
    rails = [o for sc, o, w in obs if o['kind'] == 'rail' and o['view'] == views[0]]
    gids = await pg.evaluate(r"""() => { const m = {};
      document.querySelectorAll('#nav-groups button[data-grp]').forEach(b => {
        const g = b.dataset.grp; let n = null; try { n = (typeof OV_BUILD !== 'undefined' && OV_BUILD[g]) ? needs(g) : null; } catch (e) {}
        const grp = NAV_GROUPS.find(x => x.id === g);
        m[g] = { own: !!grp && b.textContent.trim().startsWith(grp.n), needs: n, ov: (typeof OV_VIEW !== 'undefined' && OV_VIEW[g] && (ROLE_VIEWS[role()] || []).includes(OV_VIEW[g])) ? OV_VIEW[g] : null }; });
      document.querySelectorAll('#mtabs button[data-mv]').forEach(b => { const g = (typeof OV_GROUP !== 'undefined' && OV_GROUP[b.dataset.mv]) || null;
        if (g) { let n = null; try { n = needs(g); } catch (e) {} m['mv:' + b.dataset.mv] = { needs: n, ov: b.dataset.mv }; } });
      return m; }""")
    for o in rails:
        g = gids.get(o.get('grp')) or gids.get('mv:' + o.get('target', ''))
        if not g: continue
        seen = [f"{o['n']} on the {'phone tab' if o.get('phone') else 'rail'}"]
        nums = {o['n']}
        # needs(gid) is the overview's number. When the role cannot open that overview, the rail shows the one
        # view it can open under that view's own name ("Time & Crew"), and needs(gid) is not what it claims.
        if g['needs'] is not None and (g['ov'] or (g.get('own') and not o.get('phone'))):
            nums.add(g['needs']); seen.append(f"{g['needs']} from needs()")
        if g['ov']:
            await to_view(pg, g['ov'])
            r = await collect(pg)
            ov = [x for x in r['obs'] if x['kind'] == 'ovcount']
            if ov: nums.add(ov[0]['n']); seen.append(f"{ov[0]['n']} on {g['ov']} (\"late or waiting\" line)")
            await to_view(pg, views[0])
        if len(nums) > 1: lint.flag('C', run, o['label'], '; '.join(seen))

    # ---- rule (b): click tiles, chips, tab badges and "All N" for real; compare with the rows shown.
    # Renders are the cost (about half a second each on a shared box), so a view is re-rendered only when a click moved it.
    click_jobs = [] if lint.args.no_clicks else jobs if lint.args.all_projects else [cur]
    by_page = {}
    for sc, o, where in obs:
        by_page.setdefault((o['view'], sc), []).append(o)
    done_tabs = set()
    for pid in click_jobs:
        await set_job(pg, pid)
        for v in views:
            if pid != click_jobs[0] and v not in proj_views: continue
            sc = scope_of(v, pid)
            os_ = by_page.get((v, sc), [])
            tiles = [o for o in os_ if o['kind'] == 'tile' and not o.get('static') and o.get('tl') is not None]
            tabs = [o for o in os_ if o['kind'] == 'subtab' and (o['target'], scope_of(o['target'], pid), o['n']) not in done_tabs]
            alls = [o for o in os_ if o['kind'] == 'allbtn']
            has_chips = any(o['kind'] == 'chip' for o in os_)
            if not (tiles or tabs or alls or has_chips): continue
            here = f"{v}{'@' + names.get(pid, pid) if v in proj_views else ''}"
            async def back():
                # a tile clicked on another page may have opened another job (Over Budget Now opens 45 Cranberry's
                # board): come back to this job too, or the next click is read against the wrong job's list
                await set_job(pg, pid)
                await pg.evaluate("v => { try { delete tlFocus[v]; } catch (e) {} view = v; render(); }", v); await settle(pg)
            await back()
            if await cur_view(pg) != v: continue
            fresh_obs = (await collect(pg))['obs']   # the tiles as they read now (some follow the current job)
            tiles = [o for o in fresh_obs if o['kind'] == 'tile' and not o.get('static') and o.get('tl') is not None]
            alls = [o for o in fresh_obs if o['kind'] == 'allbtn']
            dirty = False
            for o in tiles:
                if dirty: await back()
                before = await pg.evaluate("w => __cl.rows(null, w)", o['n'])
                loc = pg.locator(f'.view.on button.gl[data-tl="{o["tl"]}"]').first
                if not await loc.count() or not await click(pg, loc): dirty = True; continue
                dirty = True
                nv = await cur_view(pg)
                grid = await pg.evaluate("v => { try { return tlFocus[v] && tlFocus[v].grid || null; } catch (e) { return null; } }", v)
                rows = await pg.evaluate("([g, w]) => __cl.rows(g, w)", [grid if nv == v else None, o["n"]])
                claims = await pg.evaluate("() => !!document.querySelector('.view.on .tl-focus')")
                if o['n'] == 0 and not claims:
                    lint.note(f'{run}: tile {here} "{o["label"]}" 0: opens {nv} with no filter stated ({rows["n"] if rows else "?"} rows), not compared')
                elif rows is None:
                    lint.note(f'{run}: tile {here} "{o["label"]}" {o["n"]}: no list to count after the click (landed on {nv})')
                elif rows['n'] != o['n']:
                    dead = ' — the click did not filter the list' if (nv == v and rows == before) else (' — the tile opens an unfiltered list' if nv != v else '')
                    lint.flag('B', run, f"tile {o['label']}", f"{o['n']} on the tile at {here}; {rows['n']} rows after the click at {nv} ({rows['how']}){dead}")
            if has_chips:
                if dirty: await back(); dirty = False
                sel = '.view.on .ctabs button, .view.on .seg button, .view.on .td-tabs button'
                chips = await pg.evaluate(r"""() => [...document.querySelectorAll('.view.on .ctabs button, .view.on .seg button, .view.on .td-tabs button')].map((b, i) => ({ i,
                    on: b.classList.contains('on'), n: ((b.querySelector('.n, i.n') || {}).textContent || '').trim(), vis: __cl.vis(b),
                    label: (() => { const x = b.cloneNode(true); x.querySelectorAll('.n, i.n, svg').forEach(e => e.remove()); return x.textContent.trim(); })() }))""")
                on_i = [c['i'] for c in chips if c['on']]
                fresh = None
                for c in sorted(chips, key=lambda c: not c['on']):   # the selected chips first, while the page is as it loaded
                    if not c['vis'] or not c['n'].isdigit(): continue
                    if dirty and await cur_view(pg) != v: await back()
                    loc = pg.locator(sel).nth(c['i'])
                    if c['on']:   # already applied: the page's rows are its rows
                        fresh = await pg.evaluate("w => __cl.rows(null, w)", int(c['n']))
                        if fresh and fresh['n'] != int(c['n']):
                            lint.flag('B', run, f"chip {c['label']}", f"{c['n']} on the selected chip at {here}; {fresh['n']} rows shown ({fresh['how']})")
                        continue
                    before = await pg.evaluate("w => __cl.rows(null, w)", int(c['n']))
                    if not await click(pg, loc): continue
                    dirty = True
                    nv = await cur_view(pg)
                    n = int(c['n'])
                    rows = await pg.evaluate("w => __cl.rows(null, w)", n)
                    if nv == v and rows == before and n == 0:
                        lint.note(f'{run}: chip {here} "{c["label"]}" 0: the click changes nothing, not compared')
                    elif rows is None:
                        lint.note(f'{run}: chip {here} "{c["label"]}" {n}: no list to count')
                    elif rows['n'] != n:
                        lint.flag('B', run, f"chip {c['label']}", f"{n} on the chip at {here}; {rows['n']} rows after the click at {nv} ({rows['how']})")
                if dirty and await cur_view(pg) == v:   # put the screen's own filter back
                    for i in on_i:
                        try: await click(pg, pg.locator(sel).nth(i))
                        except Exception: pass
            for o in tabs:
                done_tabs.add((o['target'], scope_of(o['target'], pid), o['n']))
                if dirty: await back()
                loc = pg.locator(f'#subnav [data-sub="{o["target"]}"]').first
                if not await loc.count() or not await click(pg, loc): continue
                dirty = True
                nv = await cur_view(pg)
                src = await pg.evaluate("b => __cl.marked(b)", o['target'])
                if src is None: src = await pg.evaluate("w => __cl.rows(null, w)", o['n'])
                if src is None:
                    lint.note(f'{run}: tab {o["label"]} {o["n"]} at {here}: nothing to compare on {nv}')
                elif src['n'] != o['n']:
                    lint.flag('B', run, f"tab {o['label']}", f"{o['n']} on the tab badge at {here}; {src['n']} at {nv} ({src['how']})")
            for o in alls:
                if dirty: await back()
                loc = pg.locator('.view.on button, .view.on a').filter(has_text=re.compile(rf'^\s*All {o["n"]}\s*$')).first
                if not await loc.count() or not await click(pg, loc): continue
                dirty = True
                nv = await cur_view(pg)
                src = await pg.evaluate("w => __cl.rows(null, w)", o['n'])
                if src is None:
                    lint.note(f'{run}: "All {o["n"]}" ({o["label"]}) at {here}: no list on {nv}')
                elif src['n'] != o['n']:
                    lint.flag('B', run, f"All {o['label']}", f"{o['n']} on the button at {here}; {src['n']} rows at {nv} ({src['how']})")

    # ---- rule (d): Ask against the screen that lists the same things
    await set_job(pg, cur)
    await ask_checks(pg, lint, run, info, views, names)
    lint.note(f'{run}: {len(pages)} pages, {len(obs)} numbers read, {time.time() - t0:.0f}s')

async def ask(pg, q):
    return await pg.evaluate(r"""async q => { let a = paAsk(q); if (a && a.then) a = await a;
      return { headline: (a && a.headline) || '', kind: (a && a.kind) || '' }; }""", q)

async def ask_checks(pg, lint, run, info, views, names):
    can = set(views)
    # 1. what is waiting on me  vs  Home > Approvals
    a = await ask(pg, 'what is waiting on me')
    an = first_int(a['headline']); refused = an is None and re.search(r'not part of|outside what', a['headline'])
    screen = []
    if 'mapprove' in can and await to_view(pg, 'mapprove'):
        m = await pg.evaluate("() => __cl.marked('mapprove')")
        if m: screen.append((m['n'], 'Approvals page "Everything"'))
    if 'home' in can and await to_view(pg, 'home'):
        r = await collect(pg)
        for o in r['obs']:
            if o['kind'] in ('card', 'subtab') and norm(o['label']) == 'approval':
                screen.append((o['n'], f"Home {o['kind']} Approvals")); break
    if 'client' in can and await to_view(pg, 'client'):
        # the portal splits what waits on the client over tiles (BACKLOG §1.4): their sum is the one waiting count
        r = await collect(pg)
        w = [o for o in r['obs'] if o['kind'] == 'tile' and re.search(r'waiting on you|your decision|to sign|approve before', o['label'], re.I)]
        if w: screen.append((sum(o['n'] for o in w), 'client home tiles ' + ' + '.join(f"{o['label']} {o['n']}" for o in w)))
    if screen:
        nums = {n for n, _ in screen}
        ask_n = 0 if an is None else an
        if refused or ask_n not in nums or len(nums) > 1:
            lint.flag('D', run, 'what is waiting on me',
                      f"Ask: \"{a['headline'][:90]}\" ({'refused' if refused else ask_n}); " + '; '.join(f'{n} on {w}' for n, w in screen))
    else:
        lint.note(f'{run}: no Approvals screen to hold "what is waiting on me" against (Ask: {a["headline"][:60]})')

    # 2. what's late on <job>  vs  that job's Today "Needs You" and its Materials late tile
    pid = next((k for k, n in names.items() if n == ASK_JOB), None)
    a = await ask(pg, f"what's late on {ASK_JOB}")
    h = a['headline']
    hs = h.replace(ASK_JOB, 'the job')
    parts = {singular(w.lower()): int(n) for n, w in re.findall(r'(\d{1,4}) ([A-Za-z]+)', hs)}
    total = sum(parts.values()) if parts else (0 if re.search(r'nothing|no .* late', h, re.I) else None)
    if total is None or re.search(r'outside what|not part of', h):
        lint.note(f'{run}: Ask gave no late count for {ASK_JOB}: {h[:60]}')
    elif pid and pid in info['jobs']:
        await set_job(pg, pid)
        seen = [f'Ask {total} ("{h[:80]}")']; nums = {total}
        if 'dash' in can and await to_view(pg, 'dash'):
            d = await pg.evaluate(r"""() => { const v = document.querySelector('.view.on');
              const els = [...v.querySelectorAll('div, section, button, a')].filter(e => __cl.vis(e) && /^Needs You (\d+) now/.test(__cl.txt(e)));
              const el = els[els.length - 1]; if (!el) return null; const t = __cl.txt(el);
              return { n: +t.match(/^Needs You (\d+)/)[1], t }; }""")
            if d: nums.add(d['n']); seen.append(f"{d['n']} on Today \"{d['t'][:120]}\"")
        if 'mat' in can and await to_view(pg, 'mat'):
            r = await collect(pg)
            late = [o for o in r['obs'] if o['kind'] == 'tile' and re.search(r'late|order-by|past', o['label'], re.I)]
            if late and 'material' in parts:
                lt = late[0]
                if lt['n'] != parts['material']:
                    lint.flag('D', run, f"what's late on {ASK_JOB} (materials)",
                              f"Ask {parts['material']} materials; {lt['n']} on Materials tile \"{lt['label']}\"")
        if 'proc' in can or 'ovbuy' in can:
            if 'ovbuy' in can and await to_view(pg, 'ovbuy'):
                c = await pg.evaluate(r"""j => { const v = document.querySelector('.view.on');
                  return [...v.querySelectorAll('.dg tbody tr')].filter(tr => tr.innerText.includes(j) && /Order-By Passed/.test(tr.innerText)).length; }""", ASK_JOB)
                if 'material' in parts and c != parts['material']:
                    lint.flag('D', run, f"what's late on {ASK_JOB} (materials)",
                              f"Ask {parts['material']} materials; {c} \"Order-By Passed\" rows for {ASK_JOB} on the Purchasing overview")
        if len(nums) > 1: lint.flag('D', run, f"what's late on {ASK_JOB}", '; '.join(seen))
        if len(seen) == 1: lint.note(f'{run}: no late list for {ASK_JOB} on screen')

    # 3. how many tasks does Chen have  vs  Tasks, everyone, all, grouped by person
    a = await ask(pg, f'how many tasks does {ASK_PERSON} have')
    an = first_int(a['headline'])
    if 'tkall' in can and an is not None and await to_view(pg, 'tkall'):
        for sel in ['[data-tkmode="cards"]', '[data-tkwho="all"]', '[data-t2view="all"]']:
            loc = pg.locator('.view.on ' + sel).first
            if await loc.count(): await click(pg, loc)
        for sid, val in [('#t2-proj', ''), ('#t2-group', 'assignee')]:
            loc = pg.locator('.view.on ' + sid)
            if await loc.count():
                try: await loc.select_option(val); await settle(pg, 200)
                except Exception: pass
        g = await pg.evaluate(r"""p => [...document.querySelectorAll('.view.on .t2-ghd')].map(h => ({ who: (() => { const c = h.cloneNode(true); c.querySelectorAll('.n, button, .t2-odage').forEach(e => e.remove()); return __cl.txt(c); })(),
            n: +((h.querySelector('.n') || {}).textContent || 0) || h.parentElement.querySelectorAll('.t2-row').length })).filter(x => new RegExp('\\b' + p + '\\b', 'i').test(x.who))""", ASK_PERSON)
        if not g:
            g_all = await pg.evaluate(r"""() => ({ group: (document.querySelector('.view.on #t2-group') || {}).value, view,
              heads: [...document.querySelectorAll('.view.on .t2-ghd')].map(h => __cl.txt(h)).slice(0, 8), rows: document.querySelectorAll('.view.on .t2-row').length,
              who: (typeof tkWho !== 'undefined') ? tkWho : null })""")
            lint.note(f'{run}: Tasks by person found no {ASK_PERSON} group: {g_all}')
        n = sum(x['n'] for x in g)
        if n != an:
            lint.flag('D', run, f'how many tasks does {ASK_PERSON} have',
                      f"Ask {an} (\"{a['headline'][:70]}\"); {n} on Tasks › Everyone › All › By Person ({', '.join(f'{x['who']} {x['n']}' for x in g) or 'no group'})")
        # put the Tasks screen back the way the role found it
        for sel in ['[data-tkwho="me"]', '[data-t2view="today"]']:
            loc = pg.locator('.view.on ' + sel).first
            if await loc.count(): await click(pg, loc)
        loc = pg.locator('.view.on #t2-group')
        if await loc.count():
            try: await loc.select_option('project')
            except Exception: pass
    elif an is not None and 'tkall' not in can:
        lint.note(f'{run}: Ask counts {an} tasks for {ASK_PERSON}, but this role has no Tasks list to check it against')

    # 4. decisions waiting on the client  vs  each job's Decisions "With Client" (client: their Decisions list)
    a = await ask(pg, 'how many decisions are waiting on the client')
    an = first_int(a['headline']); h = a['headline']
    if 'dec' in can:
        tot = 0; per = []
        for pid in info['jobs']:
            await set_job(pg, pid)
            if not await to_view(pg, 'dec'): continue
            if info['role'] == 'client':
                m = await pg.evaluate("() => __cl.marked('dec')")
                rows = m or await pg.evaluate("() => __cl.rows(null)")
                if rows and rows['n'] is not None: tot += rows['n']; per.append(f"{names[pid]} {rows['n']}")
                continue
            loc = pg.locator('.view.on button.gl').filter(has=pg.locator('.gl-k', has_text=re.compile('With Client', re.I))).first
            if not await loc.count(): continue
            await pg.evaluate("() => { try { delete tlFocus[view]; } catch (e) {} render(); }"); await settle(pg)
            await click(pg, loc)
            grid = await pg.evaluate("() => { try { return tlFocus[view] && tlFocus[view].grid || null; } catch (e) { return null; } }")
            rows = await pg.evaluate("g => __cl.rows(g)", grid)
            await pg.evaluate("() => { try { delete tlFocus[view]; } catch (e) {} }")
            if rows and rows['n'] is not None: tot += rows['n']; per.append(f"{names[pid]} {rows['n']}")
        ask_n = 0 if an is None else an
        refused = re.search(r'outside what|not part of', h)
        if per and (refused or ask_n != tot):
            lint.flag('D', run, 'how many decisions are waiting on the client',
                      f"Ask: \"{h[:90]}\" ({'refused' if refused else ask_n}); {tot} on {'the client' + chr(39) + 's Decisions page' if info['role'] == 'client' else 'Decisions "With Client"'} ({', '.join(per)})")
        await set_job(pg, info['cur'])

# ---------------------------------------------------------------- main
async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--role', help='comma list: owner,pm,coord,billing,controller,designer,foreman,client')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--all-projects', action='store_true')
    ap.add_argument('--dump', help='append every label/number observation to this file')
    ap.add_argument('--no-clicks', action='store_true', help='skip the click checks (b); quick rule (a)/(c)/(d) run')
    args = ap.parse_args()
    want = set(args.role.split(',')) if args.role else None
    lint = Lint(args); t0 = time.time()
    async with async_playwright() as p:
        for phone in (False, True):
            runs = [r for r in RUNS if r[2] == phone and (not want or r[0] in want)]
            if not runs: continue
            b, pg, errs = await open_app(p, phone)
            for tag, uid, ph in runs:
                try:
                    await run_role(pg, lint, tag, uid, ph)
                except Exception as e:
                    lint.flag('ERR', tag + ('@phone' if ph else ''), 'run', str(e)[:200])
            await b.close()
    by = {}
    for f in lint.flags: by[f['rule']] = by.get(f['rule'], 0) + 1
    if args.json:
        print(json.dumps({'flags': lint.flags, 'by_rule': by, 'notes': lint.notes, 'seconds': round(time.time() - t0)}, indent=1))
    else:
        if args.verbose: print('by rule:', by, f'· {time.time() - t0:.0f}s')
        print(f'{len(lint.flags)} flags')
    sys.exit(1 if lint.flags else 0)

asyncio.run(main())
