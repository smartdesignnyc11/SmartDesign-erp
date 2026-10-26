"""estimate_lane_test: the estimate journeys' fixes held in one quick suite (the walk, tests/cycle_walk.py, takes an hour).

Real clicks and keys through Playwright on the seeded company, phone (390) and desktop (1440):
  TAP     a press that commits a focused field (its change redraws the editor) still lands: one Save saves an
          estimate line on the desktop; one Done closes the phone's line editor (J2: 101 taps for 12 lines)
  LABEL   every field of the phone's line editor has its own visible label; Budget cost is visible and typeable,
          and the next field takes the first tap after a figure is typed (no redraw under the finger)
  MENU    the PM's rail has Estimates; it opens Billing's Estimates list on his jobs (J2)
  JOB     the proposal started at won takes the client's job at its address; with none, the Project select shows a
          blank (what shows is what is saved) and New Project, and the job opened later takes the estimate; Convert
          never opens a second job (J1b)
  RO      a converted construction estimate has no line field to type into, and says why (J4)
  SAFE    on a draft estimate neither the blue nor the first document action is Mark Sent; Mark Sent asks how and
          the day, with nothing filled in for the day (the walk's dangerous buttons)
  TOAST   the won toast names the client, not the opportunity (J1)
Usage: python3 estimate_lane_test.py
"""
import asyncio
from harness import *

OPEN_DRAFT = """() => { const c = DB.clients.find(c => c.estimates.some(e => e.status === 'draft' && e.template === 'construction'));
  const d = c.estimates.find(e => e.status === 'draft' && e.template === 'construction');
  clientOpen = c.id; clientTab = 'fin'; finTab = 'estimates'; docOpen = {kind: 'estimate', id: d.id}; view = 'clients'; render();
  return [c.id, d.id]; }"""
DOC = "([cid, did]) => { const c = DB.clients.find(x => x.id === cid); return c.estimates.find(e => e.id === did); }"


async def desktop(c, p):
    b, pg, errs = await open_app(p, False)
    await sign_in(pg, 'u_alan')
    # MENU
    rail = await pg.evaluate("() => [...document.querySelectorAll('#nav-groups button[data-grp]')].map(b => b.textContent.replace(/\\d+$/, '').trim())")
    c.ok('Estimates' in rail, f"MENU: the PM's rail has Estimates: {rail}")
    await pg.evaluate("() => { const b = [...document.querySelectorAll('#nav-groups button[data-grp]')].find(x => x.textContent.trim().startsWith('Estimates')); b.click(); }")
    await pg.wait_for_timeout(300)
    st = await pg.evaluate("() => [view, typeof billTab !== 'undefined' ? billTab : '', document.querySelectorAll('#bill-estimate tbody tr, [data-edit^=\"billdoc:\"]').length]")
    c.ok(st[0] == 'billing' and st[1] == 'estimates', f"MENU: Estimates opens Billing's Estimates list: {st}")
    # TAP: type a figure into a line, then one Save
    ids = await pg.evaluate(OPEN_DRAFT)
    await pg.wait_for_timeout(300)
    f = pg.locator('[data-ctf="cost"]').nth(1)
    await f.click(); await f.fill('4321')
    await pg.keyboard.press('Tab'); await pg.wait_for_timeout(200)   # the change lands; Unsaved changes shows
    await f.click(); await f.fill('4322')   # typed again, still focused: the press on Save commits it
    save = pg.locator('[data-docact="save"]').first
    c.ok(await save.count() == 1, 'TAP: Save shows while a line is changed')
    if await save.count():
        await save.click(); await pg.wait_for_timeout(400)
        dirty = await pg.evaluate("() => [...document.querySelectorAll('.docbar .pill.warn')].map(x => x.textContent)")
        cost = await pg.evaluate("a => { const d = (" + DOC + ")(a); return d.lines[1].cost; }", ids)
        c.ok(not dirty and str(cost) == '4322', f'TAP: one Save saves the line (left {dirty}, cost {cost})')
    # SAFE (desktop)
    acts = await pg.evaluate("() => [...document.querySelectorAll('.docacts button')].filter(b => b.offsetParent).map(b => [b.textContent.trim(), b.classList.contains('primary')])")
    c.ok(acts and acts[0][0] != 'Mark Sent' and not any(a[0] == 'Mark Sent' and a[1] for a in acts), f'SAFE: Mark Sent is neither first nor blue: {acts[:4]}')
    c.ok(any(a[0] == 'Review and Send' for a in acts), f'SAFE: Review and Send is offered: {acts[:4]}')
    await pg.locator('[data-docact="marksent"]').first.click(); await pg.wait_for_timeout(300)
    on = await pg.evaluate("() => { const m = document.getElementById('mbm'); const i = m && m.querySelector('[data-f=\"on\"]'); return m ? [i ? i.value : null, !!m.querySelector('[data-f=\"how\"]')] : null; }")
    c.ok(on and on[0] == '' and on[1], f'SAFE: Mark Sent asks how and the day, the day left empty: {on}')
    await pg.evaluate("() => { try { mbCloseModal(); } catch (e) { document.getElementById('mbm')?.remove(); } }")
    # RO: a converted construction estimate
    ro = await pg.evaluate("""a => { const d = (""" + DOC + """)(a); d.status = 'converted'; render();
        const w = document.getElementById('doc-' + d.id);
        return [w.querySelectorAll('.ct input, .ct textarea, .ct select, .est-scope textarea').length, (w.querySelector('.docbar') || {}).innerText || '']; }""", ids)
    c.ok(ro[0] == 0, f'RO: a converted estimate has {ro[0]} line fields to type into')
    c.ok('read only' in ro[1].lower() and 'change order' in ro[1].lower(), f'RO: the bar says read only and why: {ro[1][:160]!r}')
    # JOB: the proposal at won, the select, the job opened later, convert
    j = await pg.evaluate("""() => { const c = blankClient('Juniper Hale'); DB.clients.push(c);
        const l = {id: uid('ld'), name: '77 Juniper Street — Design-build', addr: '77 Juniper Street', clientId: c.id, stage: 'qualified', value: 50000};
        (DB.leads = DB.leads || []).push(l);
        const d = newDoc(c, 'estimate', {fields: {title: l.name + ' — proposal', projectId: (estJobFor(c, {title: l.name + ' — proposal'}) || {}).id || ''}});
        clientOpen = c.id; clientTab = 'fin'; finTab = 'estimates'; docOpen = {kind: 'estimate', id: d.id}; view = 'clients'; render();
        const sel = document.querySelector('#doc-' + d.id + ' select[data-d="projectId"]');
        return [c.id, d.id, d.projectId, sel ? [...sel.options].map(o => [o.value, o.text]) : null, sel ? sel.value : null]; }""")
    c.ok(j[2] == '' and j[3] and j[3][0][0] == '' and j[4] == '' and any(o[0] == '__newjob' for o in j[3]),
         f'JOB: with no job the select shows a blank and New Project: {j[3]} = {j[4]!r}')
    t = await pg.evaluate("""([cid, did]) => { const c = DB.clients.find(x => x.id === cid);
        const p = blankProject('77 Juniper Street', '77 Juniper Street, Brooklyn', today(), ''); p.clientId = cid; DB.projects.push(p);
        const tied = estTieNewJob(p); const d = c.estimates.find(e => e.id === did);
        return [p.id, d.projectId, tied.map(e => e.id)]; }""", j[:2])
    c.ok(t[1] == t[0], f'JOB: the job opened later takes the estimate: {t}')
    n = await pg.evaluate("""([cid, did]) => { const c = DB.clients.find(x => x.id === cid); const d = c.estimates.find(e => e.id === did);
        d.projectId = ''; d.status = 'approved'; d.template = 'construction'; d.lines = [{id: uid('l'), item: 'Demo', qty: 1, unit: 'ls', rate: 1000, cost: 600}];
        const n0 = DB.projects.length; return Promise.resolve(docAction(c, d, 'approveconvert')).then(() => [n0, DB.projects.length, d.projectId, (c.sov || []).filter(v => String(v.lineRef || '').startsWith('estimate:' + d.id)).map(v => v.projectId)]); }""", j[:2])
    c.ok(n[0] == n[1] and n[2] == t[0] and n[3] and all(x == t[0] for x in n[3]), f'JOB: convert uses the job at the address, no second job, the SOV on it: {n}')
    c.ok(not errs, f'page errors {errs[:2]}')
    await b.close()


async def phone(c, p):
    b, pg, errs = await open_app(p, True)
    await sign_in(pg, 'u_alan')
    ids = await pg.evaluate(OPEN_DRAFT)
    await pg.wait_for_timeout(300)
    await pg.locator('[data-ctopen]').first.click(); await pg.wait_for_timeout(300)
    labs = await pg.evaluate("""() => [...document.querySelectorAll('#ct-sheet input:not([type=checkbox]), #ct-sheet select, #ct-sheet textarea')]
        .map(el => [el.dataset.csf || '', (el.labels && el.labels[0] ? el.labels[0].innerText : '').trim(), el.getAttribute('aria-label') || '', !!el.offsetParent])""")
    c.ok(all(l[1] or l[2] for l in labs), f'LABEL: every field of the line editor has a label of its own: {[l for l in labs if not (l[1] or l[2])]}')
    cost = next((l for l in labs if l[0] == 'cost'), None)
    c.ok(cost and cost[3] and 'budget cost' in (cost[1] + cost[2]).lower(), f'LABEL: Budget cost is visible and labelled: {cost}')
    # type a figure, then tap the next field: it takes the first tap (no redraw under the finger)
    q = pg.locator('#ct-sheet [data-csf="qty"]'); await q.click(); await q.fill('3')
    u = pg.locator('#ct-sheet [data-csf="unit"]'); await u.click()
    focus = await pg.evaluate("() => document.activeElement && document.activeElement.dataset.csf")
    c.ok(focus == 'unit', f'LABEL: the next field takes the first tap after a figure is typed (focus on {focus})')
    k = pg.locator('#ct-sheet [data-csf="cost"]'); await k.click(); await k.fill('777')
    await pg.locator('#ct-sheet .ct-sheet-done').click(); await pg.wait_for_timeout(300)
    after = await pg.evaluate("a => { const d = (" + DOC + ")(a); return [!!document.getElementById('ct-sheet'), d.lines.find(l => l.cost == 777) ? 777 : null]; }", ids)
    c.ok(after == [False, 777], f'TAP: one Done closes the line editor with the cost kept: {after}')
    acts = await pg.evaluate("() => [...document.querySelectorAll('.view.on .docacts button')].filter(b => b.offsetParent).map(b => [b.textContent.trim(), b.classList.contains('primary')])")
    c.ok(acts and acts[0][0] != 'Mark Sent' and not any(a[0] == 'Mark Sent' and a[1] for a in acts), f'SAFE: on the phone Mark Sent is neither first nor blue: {acts[:4]}')
    # TOAST: won names the client
    w = await pg.evaluate("""() => { const c = blankClient('Odile Marsh'); DB.clients.push(c);
        const l = {id: uid('ld'), name: '12 Sterling Place — Design-build', leadName: 'Odile Marsh', addr: '12 Sterling Place', clientId: c.id, stage: 'qualified', value: 1, history: []};
        DB.leads.push(l); slMove(l.id, 'won'); return document.getElementById('toast').innerText; }""")
    c.ok('Odile Marsh is a client' in w and 'Design-build is a client' not in w, f'TOAST: the won toast names the client: {w!r}')
    c.ok(not errs, f'page errors {errs[:2]}')
    await b.close()


async def main():
    c = Checks()
    async with async_playwright() as p:
        await desktop(c, p)
        await phone(c, p)
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
