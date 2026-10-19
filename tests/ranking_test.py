"""Ranking (Alan, 2026-10-11; docs/DECISIONS.md, PLAN v11.1): every person's queue is in one order.

  immediate safety and law first (a missing insurance certificate counts as immediate);
  then anyone blocked today (crew or field waiting: a field question or request, material needed today, an
  inspection today);
  then overdue, today, this week, later;
  then the decision principle (standardTier) inside each bucket.

A crew waiting today ranks above older overdue items, and both stay visible: the reorder hides nothing and every
count keeps its rows. One sort does it (standardOrder); this suite proves that every screen shows that one order,
on the owner's, the PM's, the coordinator's and the foreman's screens, on a 390px phone and on desktop:
  - Home's Do Now cards (owner, PM) and the Approvals page (owner, PM, coordinator) are tdQueue() in order;
  - the coordinator's Home lists its Approvals rows in the same order;
  - the foreman's Now lines are fNowItems() in order;
  - the brief's "First thing" is Do Now's first card;
  - Ask's "what should I do first" starts with the same item, for every one of the four.

The data is invented here (a scaffold plank, an idle plasterer, a tile-saw cut, corner bead, an inspection), on top
of the demo seed, so the order is proved on records whose bucket is known, not on whatever the seed holds today."""
import asyncio, re, sys
from harness import *

SEED = r"""() => {
  const td = today(), ago = (n) => iso(addDays(td, -n)), ahead = (n) => iso(addDays(td, n)),
        p = DB.projects.find(x => x.id === 'p121'),
        R = (o) => DB.field.raises.push(Object.assign({ projectId: 'p121', note: '', cc: [], by: 'Angel', at: td + 'T08:00:00', status: 'sent', escalated: false, photos: [], calls: [] }, o));
  // the PM: an unsafe condition (immediate, answer due in two days), plasterers idle today (blocked today)
  R({ id: 'rk_safe', type: 'blocker', title: 'Loose plank on the 3rd floor scaffold, unsafe to walk', to: 'pm', dueBy: ahead(2) });
  R({ id: 'rk_idle', type: 'rfi', title: 'Plasterers standing by: which corner bead on the parlor arch?', to: 'pm', dueBy: td });
  // the owner: an incident (safety, the owner's), and a PO over the threshold for material needed on site today
  R({ id: 'rk_cut', type: 'incident', title: 'Laborer cut his hand on the tile saw, first aid given', to: 'pm', dueBy: ahead(1) });
  DB.pos.push({ id: 'rk_po', number: 'PO-2026-990', vendor: 'Brooklyn Lumber', projectId: 'p121', status: 'pending', needBy: td,
    lines: [{ item: 'Corner bead', desc: 'Corner bead, 10 ft', qty: 400, unit: 'ea', price: 40, line: '' }], submittedBy: 'Chen Biron', submittedAt: ago(1) });
  // the coordinator: a field request needed today (blocked today), and a renewal of his that lapsed three days ago
  (p.requests = p.requests || []).push({ id: 'rk_req', what: 'Corner bead, 10 ft', qty: 20, unit: 'ea', neededBy: td, taskId: '', urgency: 'normal',
    note: 'Plasterers on the parlor arch', fileId: '', by: 'Angel', at: td + 'T08:15:00', status: 'new', ackBy: '', ackAt: '', materialId: '', poId: '', eta: '', deliveredAt: '', log: [] });
  (DB.obligations = DB.obligations || []).push({ id: 'rk_ob', name: 'Fire extinguisher service tags, 121 State Street', kind: 'license', party: 'FDNY', owner: 'Chen Biron',
    starts: ago(368), expires: ago(3), renewLead: 30, status: 'active' });
  // the foreman: a DOB inspection today
  (p.inspections = p.inspections || []).push({ id: 'rk_insp', name: 'DOB framing inspection, 3rd floor', agency: 'DOB', gates: '', after: null, status: 'scheduled', date: td, permit: '', notes: '' });
  save();
  return true;
}"""

KEY = "it => standardRankKey(it)"

async def office(c, pg, uid, tag, expect):
    """Do Now, Approvals and (coordinator) Home rows are the one ranked queue, top first as expected."""
    await sign_in(pg, uid)
    q = await pg.evaluate(f"""() => {{ const Q = tdQueue(), k = {KEY};
      return {{ n: Q.length, pn: PRED.waitingOnMe.count(), keys: Q.map(k), ids: Q.map(it => it.kind + ':' + it.id), titles: Q.map(it => it.title || '') }}; }}""")
    c.ok(q['n'] == q['pn'], f'{tag}: Do Now holds {q["n"]} items, PRED.waitingOnMe {q["pn"]}: the reorder dropped nothing')
    c.ok(all(a <= b for a, b in zip(q['keys'], q['keys'][1:])), f'{tag}: the queue is in immediate, blocked-today, urgency, principle order: {q["keys"][:8]}')
    pos = {}
    for name, (re_, want) in expect.items():
        i = next((j for j, t in enumerate(q['titles']) if re_ in t), -1)
        pos[name] = i
        c.ok(i >= 0, f'{tag}: "{re_}" is in the queue')
        if i >= 0 and want is not None:
            c.ok(q['keys'][i][:2] == want, f'{tag}: "{re_}" ranks {q["keys"][i]}, want immediate/blocked {want}')
    order = [k for k in expect if pos[k] >= 0]
    c.ok([pos[k] for k in order] == sorted(pos[k] for k in order), f'{tag}: order {[(k, pos[k]) for k in order]}, want {order}')
    # the Approvals page lists the same rows in the same order, nothing hidden
    await go(pg, 'mapprove'); await pg.wait_for_timeout(250)
    ap = await pg.evaluate("() => [...document.querySelectorAll('#v-mapprove .m-appr-list > .m-appr')].map(e => e.dataset.mk + ':' + e.dataset.mid)")
    c.ok(ap == q['ids'], f'{tag}: Approvals lists {len(ap)} rows in Do Now\'s order; first {ap[:4]} vs {q["ids"][:4]}')
    return q, pos

async def run(phone):
    c = Checks()
    w = 'phone' if phone else 'desktop'
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, phone)
        await pg.evaluate(SEED)
        # ---------------------------------------------------------------- owner
        q, pos = await office(c, pg, 'u_owner', f'owner {w}', {
            'incident': ('tile saw', [0, 1]),
            'po today': ('PO-2026-990', [1, 0]),
            'overdue payroll': ('Payroll 8/17', [1, 1]),
            'LLC 25 days out': ('LLC', [1, 1]),
        })
        await go(pg, 'home'); await pg.wait_for_timeout(300)
        cards = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td-do .td-card')].map(e => e.innerText.replace(/\\s+/g, ' '))")
        c.ok(cards and 'tile saw' in cards[0], f'owner {w}: Do Now opens on the incident: {cards[:1]}')
        c.ok(len(cards) > 2 and 'PO-2026-990' in cards[1] and any('Payroll 8/17' in x for x in cards[2:]), f'owner {w}: the PO needed today is second and the overdue payroll stays on Do Now under it: {[x[:40] for x in cards]}')
        first = await pg.evaluate("() => { const L = briefSentences(tdFacts().F, role()); return (L.find(s => /^First thing:/.test(s)) || ''); }")
        c.ok('tile saw' in first, f'owner {w}: the brief\'s first thing is the incident, Do Now\'s first card: {first[:90]}')
        catch = await pg.evaluate(f"() => {{ const C = tdCaught(tdQueue()), k = {KEY}; return C.slice(0, 3).map(r => [r.src, r.what, k(r)]); }}")
        c.ok(catch and catch[0][0] == 'compliance' and catch[0][2][0] == 0, f'owner {w}: Caught for You opens on the missing insurance certificate, immediate: {catch[:1]}')
        # ---------------------------------------------------------------- PM
        q, pos = await office(c, pg, 'u_alan', f'pm {w}', {
            'unsafe plank': ('scaffold, unsafe', [0, 1]),
            'plasterers idle': ('Plasterers standing by', [1, 0]),
            'crew no-show': ('did not show today', [1, 0]),
            'overdue decision': ('Laundry layout', [1, 1]),
            'question tomorrow': ('Exposed-beam', [1, 1]),
        })
        await go(pg, 'home'); await pg.wait_for_timeout(300)
        cards = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td-do .td-card')].map(e => e.innerText.replace(/\\s+/g, ' '))")
        ci = lambda s: next((i for i, x in enumerate(cards) if s in x), -1)
        c.ok(ci('unsafe') == 0, f'pm {w}: Do Now opens on the unsafe scaffold plank: {[x[:40] for x in cards]}')
        c.ok(0 < ci('Plasterers') < ci('Laundry layout') and 0 < ci('did not show') < ci('Laundry layout'),
             f'pm {w}: the crew waiting today (plasterers {ci("Plasterers")}, no-show {ci("did not show")}) ranks above the decision overdue since 8/26 ({ci("Laundry layout")}), and both are on Do Now')
        first = await pg.evaluate("() => { const L = briefSentences(tdFacts().F, role()); return (L.find(s => /^First thing:/.test(s)) || ''); }")
        c.ok('scaffold' in first, f'pm {w}: the brief\'s first thing is Do Now\'s first card: {first[:90]}')
        # ---------------------------------------------------------------- coordinator
        q, pos = await office(c, pg, 'u_chen', f'coord {w}', {
            'request needed today': ('Corner bead', [1, 0]),
            'lapsed renewal': ('Fire extinguisher', [1, 1]),
            'insulation this week': ('Insulation for 3rd fl', [1, 1]),
        })
        c.ok(q['keys'][pos['lapsed renewal']][2] == 0, f'coord {w}: the lapsed renewal is overdue ({q["keys"][pos["lapsed renewal"]]})')
        # the coordinator's Home is Today (lane "today", 2026-10-19): its Approvals filter is the queue in order
        await go(pg, 'home'); await pg.wait_for_timeout(300)
        await pg.click('.view.on [data-tdytabbtn="appr"]'); await pg.wait_for_timeout(250)
        rows = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td-do .td-card')].map(e => e.dataset.kind + ':' + e.dataset.id)")
        texts = await pg.evaluate("() => [...document.querySelectorAll('.view.on .td-do .td-card')].map(e => e.innerText.replace(/\\s+/g, ' '))")
        c.ok(rows and rows == q['ids'][:len(rows)], f'coord {w}: Today\'s Approvals rows are the queue in order: {rows[:3]} vs {q["ids"][:3]}')
        c.ok(texts and 'Corner bead' in texts[0] and any('Fire extinguisher' in r for r in texts), f'coord {w}: the field\'s request for today is first and the lapsed renewal is still listed: {[t[:40] for t in texts]}')
        await pg.click('.view.on [data-tdytabbtn="all"]'); await pg.wait_for_timeout(250)
        allfirst = await pg.evaluate("() => (document.querySelector('.view.on .td-do .td-card') || {}).innerText || ''")
        c.ok('Corner bead' in allfirst, f'coord {w}: All starts where Approvals does: {allfirst[:60]!r}')
        await pg.click('.view.on [data-tdbrief]'); await pg.wait_for_timeout(250)
        home = await pg.evaluate("() => (document.querySelector('.view.on').innerText.match(/First thing:[^\\n]*/) || [''])[0]")
        c.ok('Corner bead' in home, f'coord {w}: the brief on Home starts where Approvals does: {home[:90]}')
        await pg.click('.view.on [data-tdbrief]'); await pg.wait_for_timeout(150)
        # ---------------------------------------------------------------- foreman
        await sign_in(pg, 'u_angel')
        await go(pg, 'ftoday'); await pg.wait_for_timeout(300)
        fn = await pg.evaluate(f"""() => {{ const N = fNowItems(), k = {KEY};
          return {{ keys: N.map(k), titles: N.map(x => x.title),
                   dom: [...document.querySelectorAll('#ftoday-body .f-nowcard .f-now')].map(e => e.innerText.replace(/\\s+/g, ' ').trim()) }}; }}""")
        c.ok(all(a <= b for a, b in zip(fn['keys'], fn['keys'][1:])), f'foreman {w}: Now is in the one order: {fn["keys"]}')
        c.ok(len(fn['dom']) == len(fn['titles']) and all(t.split(' Send ')[0][:30] in d for t, d in zip(fn['titles'], fn['dom'])), f'foreman {w}: the Now card shows fNowItems in order: {fn["dom"]}')
        fi = lambda s: next((i for i, x in enumerate(fn['dom']) if (re.match(r'^\d+ waiting on the office', x) if s == 'waiting on the office' else s in x)), -1)
        c.ok(fi('unsafe') == 0, f'foreman {w}: the unsafe plank leads Now: {fn["dom"][:2]}')
        c.ok(0 < fi('Inspection today') and 0 < fi('no-show') and fi('Inspection today') < fi('waiting on the office') and fi('no-show') < fi('waiting on the office'),
             f'foreman {w}: the inspection today and the no-show (blocked today) rank above the questions still in time: {fn["dom"]}')
        # ---------------------------------------------------------------- Ask, for all four
        for uid, tag, want in (('u_owner', 'owner', 'tile saw'), ('u_alan', 'pm', 'unsafe'), ('u_chen', 'coord', 'Corner bead'), ('u_angel', 'foreman', 'unsafe')):
            await sign_in(pg, uid)
            a = await pg.evaluate("""async () => { const out = [];
              for (const q of ['what should I do first', "what's on my plate", 'where do I start']) { const a = (await Promise.resolve(paAsk(q))) || {}; out.push([q, a.headline || '', (a.work || []).length, a.reader || '']); }
              return out; }""")
            for q_, head, n, rd in a:
                c.ok(rd == 'myfirst' and head.startswith('Start with') and want in head and n >= 3, f'{tag} {w}: Ask "{q_}" -> {head[:90]!r} ({n} listed, reader {rd})')
        c.ok(not errs, f'{w}: page errors {errs[:3]}')
        await b.close()
    return c

async def main():
    fails = 0
    for phone in (True, False):
        c = await run(phone)
        print(('phone 390' if phone else 'desktop'), end=': ')
        fails += c.done()
    sys.exit(1 if fails else 0)

asyncio.run(main())
