"""Speed on a mid-range phone (BACKLOG §1.11 item 5). The CPU is throttled 4x through CDP
(Emulation.setCPUThrottlingRate), at 390px, as the phone the 2026-10-19 measure used.

For each of owner, PM, coordinator and foreman it records:
- reopen: the app is opened once (seeding the demo company), the person signs in, then the page is reloaded,
  the way a phone reopens it (data read back from IndexedDB, the device user remembered). Measured from the
  navigation start: booted (document.body.dataset.booted === '1'), first screen (the frame after the role's home is
  drawn) and settled (the end of the last long task before a second of quiet: everything deferred has run);
- view switches: ten common views, each the time from `view = v; render()` to the next frame.

`python3 speed_test.py --profile` also takes a JS CPU profile of the owner's reopen (CDP Profiler) and writes the
top functions by self and total time to review/speed/profile_<tag>.txt. Results go to review/speed/speed_<tag>.json.
`--tag before` names the files. Thresholds sit a little above what the build reaches, so a regression fails loudly.
"""
import asyncio, json, os, sys, time
from harness import *

RATE = 4
ROLES = [('u_owner', 'owner'), ('u_alan', 'pm'), ('u_chen', 'coord'), ('u_angel', 'foreman')]
# Ten common views per role, the pages each person opens most in a day (their phone bar first).
SWITCH = {
    'u_owner': ['mapprove', 'ovjobs', 'ovmoney', 'ovsales', 'proj', 'inv', 'bank', 'reports', 'tkall', 'home'],
    'u_alan': ['mapprove', 'ovjobs', 'tkall', 'field', 'proj', 'sched', 'inv', 'po', 'chat', 'home'],
    'u_chen': ['mapprove', 'req', 'proc', 'po', 'vendors', 'recv', 'rfq', 'tkall', 'sched', 'home'],
    'u_angel': ['fraise', 'fsite', 'fcrew', 'flog', 'req', 'sched', 'photos', 'chat', 'plans', 'ftoday'],
}
# Limits on the throttled phone (ms). The goal is first screen under 3 s, settled under 5 s, a switch under 300 ms.
# The limits sit a little above what the build reaches on the shared test machine (other lanes' suites running), so a
# regression fails loudly. Boot meets the goal; office switches (Approvals, Today, Bank, Projects) do not yet: lower
# the switch limit as the passes after a draw are folded (review/speed/ has the profile).
LIMIT = {'booted': 3600, 'first': 3700, 'settled': 4500, 'switch': 1100}

OBSERVE = """
(() => {
  window.__sp = {long: []};
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) __sp.long.push([e.startTime, e.duration]); })
        .observe({type: 'longtask', buffered: true}); } catch (e) {}
  const mark = () => { if (__sp.booted) return; __sp.booted = performance.now();
    requestAnimationFrame(() => setTimeout(() => { __sp.first = performance.now(); }, 0)); };
  const watch = () => {
    if (!document.body) return setTimeout(watch, 5);
    if (document.body.dataset.booted === '1') return mark();
    new MutationObserver(() => document.body.dataset.booted === '1' && mark())
      .observe(document.body, {attributes: true, attributeFilter: ['data-booted']});
  };
  watch();
})();
"""

async def settled(pg, quiet=1000, cap=30000):
    """The end of the last long task before `quiet` ms with none."""
    t0 = time.time()
    while True:
        r = await pg.evaluate("() => { const L = __sp.long; const e = L.length ? Math.max(...L.map(x => x[0] + x[1])) : 0; return {e, now: performance.now(), first: __sp.first || 0}; }")
        if r['first'] and r['now'] - max(r['e'], r['first']) > quiet: return max(r['e'], r['first'])
        if time.time() - t0 > cap / 1000: return max(r['e'], r['first'])
        await pg.wait_for_timeout(200)

async def switch_time(pg, v):
    return await pg.evaluate("""v => new Promise(res => { const t0 = performance.now(); view = v; render();
      const sync = performance.now() - t0;
      requestAnimationFrame(() => setTimeout(() => res({sync, frame: performance.now() - t0}), 0)); })""", v)

def src_lines():
    """Map a line of the built page to its source: the app's script starts on the line after the last bare <script>."""
    html = open(URL[len('file://'):], encoding='utf-8').read().split('\n')
    start = max(i for i, l in enumerate(html) if l == '<script>') + 1   # 0-based index of src/app.js line 1
    # build.py joins the files with a newline each, in this order
    parts = [(f, sum(1 for _ in open(os.path.join(ROOT, 'src', f), encoding='utf-8'))) for f in ('app.js', 'mind.js', 'subs.js', 'assistant.js', 'livejobs.js', 'reports.js', 'loop_core.js', 'loop.js', 'meetread.js', 'costintel.js', 'specialists.js', 'tasks.js', 'taskviews.js', 'meeting.js', 'teamws.js', 'meetdoc_core.js', 'mtreview.js', 'p0money.js', 'phonerows.js', 'p2fix.js', 'p2nav.js', 'buyboard.js', 'clientdocs.js', 'p2money.js', 'today2.js', 'w1trust.js', 'items.js', 'field_es.js', 'field_es_words.js')]
    def where(line0):
        if line0 < start: return f'page:{line0 + 1}'
        k = line0 - start + 1
        for f, n in parts:
            if k <= n: return f'{f}:{k}'
            k -= n + 1
        return f'assistant.js:{k}'
    return where

# Wrapper chains (render about 40 deep, finishBoot about 14) repeat the same total down the stack; the last list
# leaves them out so the costs underneath show.
WRAPPERS = {'render', 'finishBoot', '(root)', '(program)', '(idle)', '(anon)'}

def summarise(profile, top=40):
    where = src_lines()
    nodes = {n['id']: n for n in profile['nodes']}
    parent = {}
    for n in profile['nodes']:
        for c in n.get('children', []): parent[c] = n['id']
    def key(n):
        f = n['callFrame']; name = f['functionName'] or '(anon)'
        return f"{name} {where(f['lineNumber'])}" if f.get('url') and f['lineNumber'] >= 0 else name
    self_t, total_t = {}, {}
    samples, deltas = profile.get('samples', []), profile.get('timeDeltas', [])
    for i, s in enumerate(samples):
        d = (deltas[i + 1] if i + 1 < len(deltas) else 0) / 1000.0
        n = nodes[s]; k = key(n)
        self_t[k] = self_t.get(k, 0) + d
        seen, cur = set(), s
        while cur is not None:
            kk = key(nodes[cur])
            if kk not in seen: seen.add(kk); total_t[kk] = total_t.get(kk, 0) + d
            cur = parent.get(cur)
    fmt = lambda d, n=top: '\n'.join(f'{v:9.1f} ms  {k}' for k, v in sorted(d.items(), key=lambda x: -x[1])[:n])
    under = {k: v for k, v in total_t.items() if k.split(' ')[0] not in WRAPPERS}
    return (f'Self time (top {top})\n{fmt(self_t)}\n\nTotal time (top {top})\n{fmt(total_t)}\n\n'
            f'Total time below the render and finishBoot wrappers (top {top * 2})\n{fmt(under, top * 2)}\n')

async def reopen(p, uid, profile=False):
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport=PHONE, is_mobile=True, has_touch=True)
    await ctx.add_init_script(OBSERVE)
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(URL)
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=120000)
    # A boot that holds draws must not leave work undone: the render layers seed the drawings that lnLoop("boot")
    # reads, so a first boot that skipped them left the learning loop behind (one approval short). Running the loop
    # again right after boot finds nothing new.
    lag = await pg.evaluate("""() => { const n = () => Object.keys(((DB.learn || {}).events) || {}).length + ':' +
      Object.keys(((DB.learn || {}).props) || {}).length; const a = n(); lnLoop('speed-check'); return [a, n()]; }""")
    await pg.evaluate("u => { signIn(u); render(); }", uid)
    await pg.evaluate("() => (typeof saveNow === 'function' ? saveNow() : null)")
    await pg.wait_for_timeout(1500)
    cdp = await ctx.new_cdp_session(pg)
    await cdp.send('Emulation.setCPUThrottlingRate', {'rate': RATE})
    if profile:
        await cdp.send('Profiler.enable'); await cdp.send('Profiler.setSamplingInterval', {'interval': 500})
        await cdp.send('Profiler.start')
    await pg.reload()
    await pg.wait_for_function("document.body.dataset.booted==='1' && window.__sp && __sp.first", timeout=180000)
    s = await settled(pg)
    prof = (await cdp.send('Profiler.stop'))['profile'] if profile else None
    r = await pg.evaluate("() => ({booted: __sp.booted, first: __sp.first, who: (currentUser()||{}).id, view, home: !!document.querySelector('.view.on')})")
    r['settled'] = s
    r['lag'] = [lag, await pg.evaluate("""() => { const n = () => Object.keys(((DB.learn || {}).events) || {}).length + ':' +
      Object.keys(((DB.learn || {}).props) || {}).length; const a = n(); lnLoop('speed-check'); return [a, n()]; }""")]
    sw = []
    for v in SWITCH[uid]:
        ok = await pg.evaluate("v => (ROLE_VIEWS[role()] || []).includes(v)", v)
        if not ok: continue
        t = await switch_time(pg, v)
        sw.append([v, round(t['sync']), round(t['frame'])])
    r['switch'] = sw
    # The memo of derived numbers (src/app.js, speed.js) must never answer from older records or another context.
    # Unthrottled: every hit is recomputed and compared (SPD.check) over the same views, and a record changed without
    # save() must still move the version the next draw reads.
    await cdp.send('Emulation.setCPUThrottlingRate', {'rate': 1})
    r['memo'] = await pg.evaluate("""async views => {
      if (typeof SPD === 'undefined') return null;   // a build from before the memo (a before/after run)
      SPD.check = true; SPD.bad = [];
      for (const v of views) { if (!(ROLE_VIEWS[role()] || []).includes(v)) continue; view = v; render(); }
      SPD.check = false;
      render(); const v0 = SPD.ver, m0 = SPD.min; render(); const same = SPD.ver === v0 || SPD.min !== m0;
      const b = DB.bills[0]; b.__probe = 1; render(); const moved = SPD.ver > v0; delete b.__probe; render();
      return {bad: SPD.bad.splice(0), same, moved, hits: SPD.hits, miss: SPD.miss};
    }""", SWITCH[uid])
    r['errors'] = errs[:3]
    await b.close()
    return r, prof

# A reopen draws once, after the whole boot chain (bootRun): the boot's records and the screen it leaves must be the
# ones a boot that draws first, as before, leaves (window.__sdBootDrawFirst), for each role at 390 and 1440. The
# reopens run back to back from the same stored records: a plain one first, so a one-time migration has run, then
# one each way. Clock stamps and "N min ago" are masked; anything else that differs is a boot that is not the same.
SAME = """() => { const mask = s => String(s).replace(/\\d{4}-\\d\\d-\\d\\dT\\d\\d:\\d\\d(:\\d\\d(\\.\\d+)?)?Z?/g, 'T')
    .replace(/\\d+ (sec|min|s|m)\\b[^<]{0,12}ago/g, 'ago');
  const v = document.querySelector('.view.on'), rail = document.querySelector('.rail'), mb = document.getElementById('nav-mb');
  return {db: mask(JSON.stringify(DB)), view: (v && v.id) + ':' + mask(v ? v.innerHTML : ''),
          nav: mask((rail ? rail.innerHTML : '') + (mb ? mb.innerHTML : '')), who: (currentUser() || {}).id}; }"""

async def boot_same(p, uid, vp):
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport=vp, is_mobile=vp is PHONE, has_touch=vp is PHONE)
    await ctx.add_init_script("try { sessionStorage.getItem('sdDrawFirst') && (window.__sdBootDrawFirst = 1); } catch (e) {}")
    pg = await ctx.new_page()
    await pg.goto(URL)
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=120000)
    await pg.evaluate("u => { signIn(u); render(); }", uid)
    out = []
    for first in (0, 1, 0):
        await pg.evaluate("f => { saveNow && saveNow(); f ? sessionStorage.setItem('sdDrawFirst', '1') : sessionStorage.removeItem('sdDrawFirst'); }", first)
        await pg.wait_for_timeout(800)
        await pg.reload()
        await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=120000)
        await pg.wait_for_timeout(300)
        out.append(await pg.evaluate(SAME))
    await b.close()
    a, c = out[1], out[2]
    diff = []
    for k in ('who', 'view', 'nav', 'db'):
        if a[k] != c[k]:
            x, y = a[k], c[k]; i = next((i for i in range(min(len(x), len(y))) if x[i] != y[i]), min(len(x), len(y)))
            diff.append(f'{k} at {i}: drawn first {x[max(0, i - 60):i + 100]!r} | drawn once {y[max(0, i - 60):i + 100]!r}')
    return diff

async def main():
    tag = 'run'
    if '--tag' in sys.argv: tag = sys.argv[sys.argv.index('--tag') + 1]
    want_prof = '--profile' in sys.argv
    out_dir = os.path.join(ROOT, 'review', 'speed'); os.makedirs(out_dir, exist_ok=True)
    c = Checks(); res = {}
    async with async_playwright() as p:
        only = sys.argv[sys.argv.index('--role') + 1].split(',') if '--role' in sys.argv else None
        for uid, name in ROLES:
            if only and name not in only: continue
            r, prof = await reopen(p, uid, profile=want_prof and uid == 'u_owner')
            res[name] = r
            sw = r['switch']; worst = max((x[2] for x in sw), default=0)
            print(f"{name:8} booted {r['booted']:7.0f}  first {r['first']:7.0f}  settled {r['settled']:7.0f}  "
                  f"switch max {worst} ms  [{' '.join(f'{v}:{f}' for v, s, f in sw)}]", flush=True)
            c.ok(r['who'] == uid, f'{name}: reopened as {r["who"]}, expected {uid}')
            c.ok(not r['errors'], f'{name}: page errors {r["errors"]}')
            c.ok(r['booted'] < LIMIT['booted'], f"{name}: booted at {r['booted']:.0f} ms (limit {LIMIT['booted']})")
            c.ok(r['first'] < LIMIT['first'], f"{name}: first screen at {r['first']:.0f} ms (limit {LIMIT['first']})")
            c.ok(r['settled'] < LIMIT['settled'], f"{name}: settled at {r['settled']:.0f} ms (limit {LIMIT['settled']})")
            for v, s, f in sw:
                c.ok(f < LIMIT['switch'], f"{name}: switch to {v} took {f} ms (limit {LIMIT['switch']})")
            m = r['memo'] or {'bad': ['no memo layer (SPD) in this build'], 'same': False, 'moved': False, 'hits': 0}
            c.ok(not m['bad'], f"{name}: the memo answered differently from a fresh computation: {m['bad'][:2]}")
            c.ok(m['same'], f'{name}: the data version moved with no change to the records')
            c.ok(m['moved'], f'{name}: a record changed without save() did not move the data version')
            c.ok(m['hits'] > 0, f'{name}: the memo of derived numbers is not in use')
            for when, (a, b) in zip(('first boot', 'reopen'), r['lag']):
                c.ok(a == b, f'{name}: after the {when} the learning loop still had work (events:proposals {a} -> {b})')
            if prof:
                txt = summarise(prof)
                open(os.path.join(out_dir, f'profile_{tag}.txt'), 'w').write(txt)
                json.dump(prof, open(os.path.join(out_dir, f'profile_{tag}.cpuprofile'), 'w'))
                print(txt[:4000])
        if '--no-same' not in sys.argv:
            for uid, name in ROLES:
                if only and name not in only: continue
                for vp in (PHONE, DESKTOP):
                    d = await boot_same(p, uid, vp)
                    print(f"{name:8} {vp['width']}: one draw leaves {'the same records and screen' if not d else 'a different boot'}", flush=True)
                    c.ok(not d, f"{name} at {vp['width']}: a reopen that draws once differs from one that draws first: {d[:2]}")
    json.dump(res, open(os.path.join(out_dir, f'speed_{tag}.json'), 'w'), indent=1)
    sys.exit(c.done())

if __name__ == '__main__':
    asyncio.run(main())
