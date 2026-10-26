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
    await two_jobs(c, pg)
    await job_rules(c, pg)
    await replay(c, pg)
    c.ok(not errs, f'page errors {errs[:2]}')
    await b.close()


async def two_jobs(c, pg):
    """JOB2: a repeat client with live jobs at 214 Lincoln Place and 88 Pierrepont St (chief of staff, 10-26: an estimate
    titled 88 Pierrepont went on 214 Lincoln, and one naming no address too). The title's address alone decides; no
    address and two jobs is blank; Convert's confirmation names the job before it is used; a new job never moves an
    approved estimate, and each tie it makes is on the audit trail."""
    r = await pg.evaluate("""() => { const c = blankClient('Rhea Castellan'); c.propertyAddr = '214 Lincoln Place, Brooklyn'; DB.clients.push(c);
        (DB.leads = DB.leads || []).push({id: uid('ld'), name: '214 Lincoln Place — Design-build', addr: '214 Lincoln Place', clientId: c.id, stage: 'won'});
        const mk = (n, a) => { const p = blankProject(n, a, today(), ''); p.clientId = c.id; DB.projects.push(p); return p; };
        const L = mk('214 Lincoln Place', '214 Lincoln Place, Brooklyn'), P = mk('88 Pierrepont St', '88 Pierrepont St, Brooklyn Heights');
        const e1 = newDoc(c, 'estimate', {template: 'construction', fields: {title: '88 Pierrepont St — basement proposal', projectId: ''}});
        const e2 = newDoc(c, 'estimate', {template: 'construction', fields: {title: 'Kitchen proposal', projectId: ''}});
        [e1, e2].forEach(e => { e.status = 'approved'; e.lines = [{id: uid('l'), item: 'Demo', qty: 1, unit: 'ls', rate: 1000, cost: 600}]; });
        return {cid: c.id, L: L.id, P: P.id, e1: e1.id, e2: e2.id, j1: (estJobFor(c, e1) || {}).id || '', j2: (estJobFor(c, e2) || {}).id || ''}; }""")
    c.ok(r['j1'] == r['P'], f"JOB2: an estimate titled 88 Pierrepont St goes on 88 Pierrepont St, not 214 Lincoln: {r['j1']} (Pierrepont {r['P']}, Lincoln {r['L']})")
    c.ok(r['j2'] == '', f"JOB2: an estimate naming no address, for a client with two jobs, is left blank: {r['j2']!r}")
    # Convert through the screen: the confirmation names the job, and the job is set only once the person says yes
    async def convert(eid):
        await pg.evaluate("([cid, eid]) => { clientOpen = cid; clientTab = 'fin'; finTab = 'estimates'; docOpen = {kind: 'estimate', id: eid}; view = 'clients'; render(); }", [r['cid'], eid])
        await pg.wait_for_timeout(300)
        await pg.locator(f'#doc-{eid} [data-docact="convert"]').first.click(); await pg.wait_for_timeout(300)
        return await pg.evaluate("() => { const m = document.getElementById('mbm'); return m ? m.innerText : ''; }")
    m1 = await convert(r['e1'])
    pid0 = await pg.evaluate("([cid, eid]) => DB.clients.find(x => x.id === cid).estimates.find(e => e.id === eid).projectId", [r['cid'], r['e1']])
    c.ok('It goes on 88 Pierrepont St' in m1 and pid0 == '', f'JOB2: Convert says the job before it is used ({pid0!r} until yes): {m1[:240]!r}')
    n0 = await pg.evaluate('DB.projects.length')
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(600)
    a1 = await pg.evaluate("([cid, eid]) => { const d = DB.clients.find(x => x.id === cid).estimates.find(e => e.id === eid); return [d.status, d.projectId, DB.projects.length]; }", [r['cid'], r['e1']])
    c.ok(a1 == ['converted', r['P'], n0], f'JOB2: yes converts it on 88 Pierrepont St, no new job: {a1}')
    m2 = await convert(r['e2'])
    # (asked, 10-26 second review: a repeat client's estimate with no address is a choice, never a guess or a new job)
    c.ok('choose' in m2 and '214 Lincoln Place' in m2 and '88 Pierrepont St' in m2, f"JOB2: Convert of an estimate with no address asks which of the client's jobs first: {m2[:240]!r}")
    await pg.evaluate("() => { try { mbCloseModal(); } catch (e) { document.getElementById('mbm')?.remove(); } }")
    # a new job takes a draft at its address and logs it; an approved estimate is never moved
    t = await pg.evaluate("""([cid]) => { const c = DB.clients.find(x => x.id === cid);
        const ed = newDoc(c, 'estimate', {fields: {title: '9 Remsen St — proposal', projectId: ''}});
        const ea = newDoc(c, 'estimate', {fields: {title: '9 Remsen St — garden proposal', projectId: ''}}); ea.status = 'approved';
        const p = blankProject('9 Remsen St', '9 Remsen St', today(), ''); p.clientId = cid; DB.projects.push(p);
        const tied = estTieNewJob(p).map(e => e.id);
        return [tied.includes(ed.id), ed.projectId === p.id, ea.projectId, (DB.audit || []).some(a => a.refId === ed.id && a.action === 'tie job')]; }""", [r['cid']])
    c.ok(t == [True, True, '', True], f'JOB2: a new job takes the draft at its address with an audit entry, never the approved one: {t}')


async def job_rules(c, pg):
    """JOB3 (chief of staff, 10-26, second review): a one-job client with an open lead elsewhere is not guessed for, and
    the proposal started from that lead carries the lead's address; Record Client Approval names the job (and asks when
    there is more than one) before it converts; two jobs at the same street are asked about, never "not at this
    address"; a client's approval in the portal with no settled job approves without opening a job; every convert
    toast names the job with Open."""
    mk = """([cname, prop, jobs]) => { const c = blankClient(cname); c.propertyAddr = prop; DB.clients.push(c);
        const J = jobs.map(([n, a]) => { const p = blankProject(n, a, today(), ''); p.clientId = c.id; DB.projects.push(p); return p.id; });
        return [c.id, J]; }"""
    est = """([cid, title, st]) => { const c = DB.clients.find(x => x.id === cid);
        const e = newDoc(c, 'estimate', {template: 'construction', fields: {title: title, projectId: ''}});
        e.status = st; e.lines = [{id: uid('l'), item: 'Demo', qty: 1, unit: 'ls', rate: 1000, cost: 600}]; return e.id; }"""
    def info(cid, eid):
        return pg.evaluate("""([cid, eid]) => { const c = DB.clients.find(x => x.id === cid); const d = c.estimates.find(e => e.id === eid);
            return {status: d.status, pid: d.projectId || '', n: DB.projects.length}; }""", [cid, eid])
    async def open_doc(cid, eid):
        await pg.evaluate("([cid, eid]) => { try { mbCloseModal(); } catch (e) {} clientOpen = cid; clientTab = 'fin'; finTab = 'estimates'; docOpen = {kind: 'estimate', id: eid}; view = 'clients'; render(); }", [cid, eid])
        await pg.wait_for_timeout(300)
    modal = "() => { const m = document.getElementById('mbm'); return m ? m.innerText : ''; }"

    # (a) one job at 214 Lincoln, the old won lead and the property there, a new open lead at 88 Pierrepont
    cid, J = await pg.evaluate(mk, ['Ines Okafor', '214 Lincoln Place, Brooklyn', [['214 Lincoln Place', '214 Lincoln Place, Brooklyn']]])
    r = await pg.evaluate("""([cid]) => { const c = DB.clients.find(x => x.id === cid);
        DB.leads.push({id: uid('ld'), name: '214 Lincoln Place — Design-build', addr: '214 Lincoln Place', clientId: cid, stage: 'won', history: []});
        const nl = {id: uid('ld'), name: 'Basement for the Okafors', addr: '88 Pierrepont St', clientId: cid, stage: 'qualified', value: 40000, history: []}; DB.leads.push(nl);
        const e = newDoc(c, 'estimate', {fields: {title: 'Kitchen proposal', projectId: ''}});
        return [(estJobFor(c, e) || {}).id || '', nl.id]; }""", [cid])
    c.ok(r[0] == '', f'JOB3: a one-job client with an open lead at another address is not guessed for: {r[0]!r}')
    # the proposal started from that lead at won ("Close and Start the Proposal"), through its sheet
    await pg.evaluate("([lid]) => { const l = DB.leads.find(x => x.id === lid); view = 'hbdeals'; render(); hbMoveStage(l, 'won'); }", [r[1]])
    await pg.wait_for_timeout(400)
    b = pg.get_by_role('button', name='Close and Start the Proposal')
    if await b.count():
        await b.first.click(); await pg.wait_for_timeout(500)
        p = await pg.evaluate("([cid]) => { const c = DB.clients.find(x => x.id === cid); const e = c.estimates[c.estimates.length - 1]; return [e.title, e.projectId || '', e.siteAddr || '']; }", [cid])
        c.ok(p[1] == '' and '88 pierrepont' in (p[2] or p[0]).lower(), f"JOB3: the proposal from the 88 Pierrepont lead is not put on 214 Lincoln and carries the lead's address: {p}")
    else:
        c.ok(False, 'JOB3: Close and Start the Proposal on the won sheet')

    # (b) Record Client Approval for a two-job client, estimate naming no address: the sheet asks which job
    cid, J = await pg.evaluate(mk, ['Tomas Brandt', '', [['214 Lincoln Place', '214 Lincoln Place'], ['88 Pierrepont St', '88 Pierrepont St']]])
    eid = await pg.evaluate(est, [cid, 'Kitchen proposal', 'sent'])
    await open_doc(cid, eid)
    n0 = (await info(cid, eid))['n']
    await pg.evaluate("([eid]) => document.querySelector(`#doc-${eid} [data-docact=\"lkapprove\"]`).click()", [eid])
    await pg.wait_for_timeout(300)
    m = await pg.evaluate(modal)
    sel = await pg.locator('#mbm [data-f="job"]').count()
    c.ok(sel == 1 and '214 Lincoln Place' in m and '88 Pierrepont St' in m, f'JOB3: Record Client Approval asks which job when the client has two: {m[:260]!r}')
    if sel:
        await pg.locator('#mbm [data-f="job"]').select_option(J[1])
    await pg.fill('#mbm [data-f="why"]', 'signed PDF returned by email')
    await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
    a = await info(cid, eid)
    t = await pg.evaluate("() => { const t = document.getElementById('toast'); return [t.innerText, !!t.querySelector('a')]; }")
    c.ok(a == {'status': 'converted', 'pid': J[1], 'n': n0}, f'JOB3: the approval converts it on the job chosen, no new job: {a}')
    c.ok('88 Pierrepont St' in t[0] and t[1], f'JOB3: the approval toast names the job, with Open: {t}')
    # with one settled job the approval sheet says where it goes
    eid2 = await pg.evaluate(est, [cid, '214 Lincoln Place — garden proposal', 'sent'])
    await open_doc(cid, eid2)
    await pg.evaluate("([eid]) => document.querySelector(`#doc-${eid} [data-docact=\"lkapprove\"]`).click()", [eid2])
    await pg.wait_for_timeout(300)
    m = await pg.evaluate(modal)
    c.ok('It goes on 214 Lincoln Place' in m, f'JOB3: Record Client Approval says the job it goes on: {m[:200]!r}')
    await pg.evaluate("() => { try { mbCloseModal(); } catch (e) {} }")

    # (c) two live jobs at the same street (Phase 1 and Phase 2): Convert asks which
    cid, J = await pg.evaluate(mk, ['Hollis Reyes', '', [['121 State St — Phase 1', '121 State St, Brooklyn'], ['121 State St — Phase 2', '121 State St, Brooklyn']]])
    eid = await pg.evaluate(est, [cid, '121 State St — parlor proposal', 'approved'])
    await open_doc(cid, eid)
    n0 = (await info(cid, eid))['n']
    await pg.locator(f'#doc-{eid} [data-docact="convert"]').first.click(); await pg.wait_for_timeout(300)
    m = await pg.evaluate(modal)
    sel = await pg.locator('#mbm [data-f="job"]').count()
    c.ok(sel == 1 and 'are not at' not in m and 'Phase 1' in m and 'Phase 2' in m, f'JOB3: two jobs at the same street are asked about: {m[:260]!r}')
    if sel:
        await pg.locator('#mbm [data-f="job"]').select_option(J[1])
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(400)
        m = await pg.evaluate(modal)
        c.ok('It goes on 121 State St — Phase 2' in m, f'JOB3: Convert then names the job chosen: {m[:200]!r}')
        await pg.locator('#mbm #mbm-ok').click(); await pg.wait_for_timeout(700)
    a = await info(cid, eid)
    t = await pg.evaluate("() => { const t = document.getElementById('toast'); return [t.innerText, !!t.querySelector('a')]; }")
    c.ok(a == {'status': 'converted', 'pid': J[1], 'n': n0}, f'JOB3: converted on Phase 2, no third job: {a}')
    c.ok('Phase 2' in t[0] and t[1], f'JOB3: the convert toast names the job, with Open: {t}')

    # (d) the client approves in the portal and no job is settled: approved, not converted, no job opened, a task
    eid = await pg.evaluate(est, [cid, 'Kitchen proposal', 'sent'])
    n0 = (await info(cid, eid))['n']
    await pg.evaluate("([cid, eid]) => { const c = DB.clients.find(x => x.id === cid); return Promise.resolve(docAction(c, c.estimates.find(e => e.id === eid), 'approve')); }", [cid, eid])
    await pg.wait_for_timeout(300)
    a = await info(cid, eid)
    task = await pg.evaluate("([cid, eid]) => (DB.projects || []).some(p => (p.actions || []).some(x => x.source && x.source.chooseJob === eid))", [cid, eid])
    c.ok(a == {'status': 'approved', 'pid': '', 'n': n0} and task, f'JOB3: an approval with no settled job opens no job and asks the PM to choose: {a}, task {task}')


async def replay(c, pg):
    """TAP2: a press replayed after a redraw never presses another record's control, and never twice (chief of staff,
    10-26: Today's Needs You draws a bare Approve per row, identity on the row, and its click handler stops the click
    on the window). Two identical Approve rows; a window capture handler like Needs You's counts presses per row."""
    await pg.evaluate("""() => { view = 'clients'; clientOpen = null; docOpen = null; render();
        const v = document.querySelector('section.view.on'); const box = document.createElement('div'); box.id = 'tap2'; box.style.cssText = 'position:fixed;top:120px;left:300px;z-index:99999;background:#fff';
        v.appendChild(box); window.__RC = {A: 0, B: 0};
        window.__rows = (order, dbl) => { box.innerHTML = order.map(k => `<div class="tap2r" data-row="${k}" style="padding:6px"><button type="button" class="btn sm">Approve</button></div>`).join('');
          if (dbl) box.querySelectorAll('button').forEach(b => b.addEventListener('mouseup', () => b.click())); };
        if (!window.__tap2) { window.__tap2 = 1; window.addEventListener('click', e => { const r = e.target.closest && e.target.closest('#tap2 [data-row]'); if (!r) return;
          e.stopPropagation(); e.stopImmediatePropagation(); __RC[r.dataset.row]++; }, true); }
        __rows(['A', 'B']); }""")
    async def press(after_down):
        await pg.evaluate("() => { __RC.A = 0; __RC.B = 0; __rows(['A', 'B']); }")
        bb = await pg.locator('#tap2 [data-row="A"] button').bounding_box()
        await pg.mouse.move(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2)
        await pg.mouse.down(); await pg.evaluate(after_down); await pg.mouse.up(); await pg.wait_for_timeout(250)
        return await pg.evaluate('({...__RC})')
    s = await press("() => __rows(['B', 'A'])")
    c.ok(s['B'] == 0 and s['A'] <= 1, f'TAP2: rows re-ordered under the finger: nothing or the same row is pressed, never the other: {s}')
    s = await press("() => __rows(['A', 'B'])")
    c.ok(s == {'A': 1, 'B': 0}, f'TAP2: the same row redrawn under the finger is pressed exactly once: {s}')
    s = await press("() => __rows(['A', 'B'], true)")
    c.ok(s == {'A': 1, 'B': 0}, f'TAP2: when the browser delivers the click to the redrawn button, it is not pressed a second time: {s}')
    await pg.evaluate("() => document.getElementById('tap2')?.remove()")


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
