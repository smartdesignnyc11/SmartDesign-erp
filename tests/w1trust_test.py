"""w1trust_test: wave 1, Trust (docs/PATH_TO_9.md; src/w1trust.js), each class held where the Pilot 2 experts hit it.
The sheets' drafts are walked by drafts_test.py and the buttons by tap_label_lint.py; this suite holds the rest.

D3  Defaults from context.
    - Make It a Task from Chen's mail "by noon today (order-by 9/16)", on a thread whose subject is another
      conversation ("Re: Laundry depth"): due today, notes from that mail's own words; once the designer has replied
      "send the count by end of day Wed 9/9", due Wed 9/9. The Inbox's Task From This Message takes the same rule.
    - A promise in mail: "by Friday" written on a Friday is that Friday; "by end of day" is the day it was written.
    - Quick add: "Call a backup mason for 121 State restoration (Tomas out to 9/14) Wed 9/9 8am" is due Wed 9/9 and
      keeps "(Tomas out to 9/14)" and the time in its title.
    - Clock-out: Alberto's sheet ticks his own framing, never Windows & interior trim; a line he logged comes ticked
      with its hours; the driver's sheet has driving, pickups and deliveries on cost code 01 and ticks nothing unknown.
    - Purchase tax: an order made on the order sheet keeps P0's one rule (no sheet sets it otherwise).
D2  Labels: a mail row's verb says what it does (Watch the Feed, File on the Vendor); applying a certificate toasts
    Open to the vendor, not the Inbox; Route's Clock In clocks in on Route; the hold sheet is Book the Meeting with
    Book It; Add Milestone's editor says New Milestone.
D4  Silent saves: Yes, Continue on a button the screen drew again still does the step; a payroll save says so with
    Open; Re-Read on a meeting says what it found.
Desktop 1440 and phone 390 where the person was on that device.
"""
import asyncio, re, sys
from harness import *

SLEEP = "ms => new Promise(r => setTimeout(r, ms))"


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = " + SLEEP + "; " + body + " }", arg)


async def fresh(p, uid, phone=False):
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, uid)
    await pg.evaluate("() => { getGeo = () => Promise.resolve(null); }")
    return b, pg, errs


async def t_mail_task(c, p, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await fresh(p, 'u_sarah', phone)
    r = await js(pg, """
      const td = today(), th = 'w1t-door';
      const ask = { id: 'w1c1', threadId: th, direction: 'in', date: td + 'T07:10:00', subject: 'Re: Laundry depth', from: { name: 'Chen Biron', email: 'chen@smartdesignnyc.com' },
        to: [{ name: 'Sarah Davis' }], text: "Sarah, still need your check of Angel's 6-door count on the 3rd floor by noon today (order-by 9/16).", route: { projectId: 'p121' }, proposals: [] };
      DB.comms.push(ask);
      const pr = { id: 'w1p1', kind: 'request', task: "Check Angel's 6-door count — 121 State", due: '2026-09-16', summary: "Check Angel's 6-door count — Chen Biron, by Wed, Sep 16", projectId: 'p121', on: true };
      ask.proposals.push(pr);
      flTaskDialog(ask, pr); await sleep(200);
      const m = document.getElementById('mbm'), q = s => m && m.querySelector(s);
      const one = { due: q('[data-f="due"]') && q('[data-f="due"]').value, notes: q('[data-f="notes"]') && q('[data-f="notes"]').value, from: (m && m.innerText.match(/From [^\\n]*/) || [''])[0] };
      m && m.remove();
      // her reply on the thread names the day she will have it
      DB.comms.push({ id: 'w1c2', threadId: th, direction: 'out', owner: 'u_sarah', date: td + 'T10:40:00', subject: 'Re: Laundry depth', from: { name: 'Sarah Davis', email: 'sarah@smartdesignnyc.com' },
        to: [{ name: 'Chen Biron' }], text: 'Chen, there is no door schedule yet. I build the 3rd-floor door schedule from the plan and send the count by end of day Wed 9/9 (order-by 9/16).', proposals: [] });
      flTaskDialog(ask, pr); await sleep(200);
      const m2 = document.getElementById('mbm');
      const two = { due: m2 && m2.querySelector('[data-f="due"]').value };
      m2 && m2.remove();
      // the Inbox's Task From This Message: the same rule
      cmTaskDialog(ask, null); await sleep(200);
      const m3 = document.getElementById('mbm');
      const three = { due: m3 && (m3.querySelector('[data-f="due"]') || {}).value, notes: m3 && (m3.querySelector('[data-f="notes"]') || {}).value };
      m3 && m3.remove();
      // a mail whose only dates are when things ship and must be ordered: never the task's date
      const o = { id: 'w1c6', threadId: 'w1t6', direction: 'in', date: td + 'T08:10:00', subject: 'Doors', from: { name: 'Window Works', email: 'ww@example.com' },
        text: 'The windows ship 9/11. Please look at the door hardware list; order by 9/16 for the 9/30 install.', route: { projectId: 'p121' }, proposals: [] };
      DB.comms.push(o);
      flTaskDialog(o, { id: 'w1p6', kind: 'request', task: 'Look at the door hardware list', due: '2026-09-16', summary: 'Look at the door hardware list', projectId: 'p121' }); await sleep(200);
      const m4 = document.getElementById('mbm');
      const four = { due: m4 && m4.querySelector('[data-f="due"]').value, want: addWork(td, 2) };
      m4 && m4.remove();
      return { td, one, two, three, four };""")
    c.ok(r['one']['due'] == r['td'], f"{tag} mail task: Chen's 'by noon today (order-by 9/16)' is due today, never the order-by date ({r['one']['due']})")
    c.ok('6-door' in (r['one']['notes'] or '') and 'Laundry' not in (r['one']['notes'] or ''), f"{tag} mail task: notes from that mail's words, not the thread's old subject ({r['one']['notes']!r})")
    c.ok('due ' in r['one']['from'].lower(), f"{tag} mail task: the sheet says where the date came from ({r['one']['from']!r})")
    c.ok(r['two']['due'] == '2026-09-09', f"{tag} mail task: after her reply, due the day she gave, Wed 9/9 ({r['two']['due']})")
    c.ok(r['three']['due'] == '2026-09-09' and 'Laundry' not in (r['three']['notes'] or ''), f"{tag} Task From This Message takes the same date and notes ({r['three']})")
    c.ok(r['four']['due'] == r['four']['want'], f"{tag} mail task: a mail dated only by ship and order-by dates takes the usual two working days, never 9/16 ({r['four']})")
    c.ok(not errs, f'{tag} mail task: no page errors ({errs[:2]})')
    await b.close()


async def t_promise_quick(c, p):
    b, pg, errs = await fresh(p, 'u_alan', True)
    r = await js(pg, """
      return {
        fri: lnPromiseOf({ date: '2026-09-04T07:40:00', text: "Cambri, I'll send both island layouts by Friday.", to: [{ name: 'Cambri' }] }),
        eod: lnPromiseOf({ date: '2026-08-31T09:00:00', text: "Elena, I'll send the window drawing by end of day.", to: [{ name: 'Elena' }] }),
        nxt: lnPromiseOf({ date: '2026-09-04T07:40:00', text: "I'll send the revised set next Friday.", to: [{ name: 'Cambri' }] }),
        q: tvQaParse('Call a backup mason for 121 State restoration (Tomas out to 9/14) Wed 9/9 8am') };""")
    c.ok(r['fri'] and r['fri']['due'] == '2026-09-04', f"promise: 'by Friday' written on Friday 9/4 is due 9/4, not 9/11 ({r['fri']})")
    c.ok(r['eod'] and r['eod']['due'] == '2026-08-31', f"promise: 'by end of day' is due the day it was written ({r['eod']})")
    c.ok(r['nxt'] and r['nxt']['due'] == '2026-09-11', f"promise: 'next Friday' is the Friday after ({r['nxt']})")
    q = r['q']
    c.ok(q['due'] == '2026-09-09', f"quick add: 'Wed 9/9 8am' is the due date, never the 9/14 in the parenthesis ({q['due']})")
    c.ok('(Tomas out to 9/14)' in q['title'] and '8 AM' in q['title'] and 'Wed' not in q['title'], f"quick add: the parenthesis stays whole and the time stays ({q['title']!r})")
    c.ok(q['pid'] == 'p121', f"quick add: still filed on 121 State ({q['pid']})")
    await b.close()


async def t_clock(c, p):
    b, pg, errs = await fresh(p, 'u_alberto', True)
    r = await js(pg, """
      setCurrent('p121');
      DB.time = DB.time.filter(t => !(t.date === today() && ['em2', 'em3'].includes(t.empId)));
      const e = { id: 'w1te1', empId: 'em2', date: today(), in: today() + 'T07:32:00', out: today() + 'T16:38:00', breakMin: 30, projectId: 'p121', status: 'open', source: 'phone', work: [] };
      DB.time.push(e);
      f3DaySheet(e); await sleep(250);
      let m = document.getElementById('mbm');
      const rows = [...m.querySelectorAll('.f3-dayrow')].map(l => ({ id: l.querySelector('[data-f3t2]').dataset.f3t2, name: l.querySelector('b').innerText, on: l.querySelector('[data-f3t2]').checked }));
      m.remove();
      // a line he logged with Add a Line comes ticked, with its hours
      e.work = [{ projectId: 'p121', taskId: 'frame', code: '03', hours: 3, note: 'Framing' }];
      f3DaySheet(e); await sleep(250);
      m = document.getElementById('mbm');
      const lg = { on: m.querySelector('[data-f3t2="frame"]').checked, h: m.querySelector('[data-f3h="frame"]').value };
      m.remove();
      return { rows, lg };""")
    on = [x['name'] for x in r['rows'] if x['on']]
    c.ok(not any('Windows' in n for n in on), f"clock-out: Windows & interior trim is never ticked for the framer ({on})")
    c.ok(any('Framing' in n for n in on) and all('Framing' in n for n in on), f"clock-out: only Alberto's own framing is ticked ({on})")
    c.ok(r['lg']['on'] and r['lg']['h'] == '3', f"clock-out: the line he logged comes ticked with its 3 h ({r['lg']})")
    await b.close()
    b, pg, errs = await fresh(p, 'u_alex', True)
    r = await js(pg, """
      setCurrent('p121');
      DB.time = DB.time.filter(t => !(t.date === today() && t.empId === 'em3'));
      const e = { id: 'w1te2', empId: 'em3', date: today(), in: today() + 'T07:32:00', out: today() + 'T16:12:00', breakMin: 30, projectId: 'p121', status: 'open', source: 'phone', work: [] };
      DB.time.push(e);
      f3DaySheet(e); await sleep(250);
      const m = document.getElementById('mbm');
      const rows = [...m.querySelectorAll('.f3-dayrow')].map(l => ({ id: l.querySelector('[data-f3t2]').dataset.f3t2, name: l.querySelector('b').innerText, on: l.querySelector('[data-f3t2]').checked }));
      m.querySelector('[data-f3t2="w1drv:pickup"]').click(); m.querySelector('[data-f3t2="w1drv:drive"]').click();
      m.querySelector('#mbm-ok').click(); await sleep(250);
      const t = document.getElementById('toast');
      return { rows, work: e.work, toast: t.innerText, open: !!t.querySelector('.toast-open') };""")
    names = [x['name'] for x in r['rows']]
    c.ok(names[:3] == ['Driving and material runs', 'Pickups', 'Deliveries'], f"clock-out: the driver's sheet leads with his own work ({names[:4]})")
    c.ok(not any(x['on'] for x in r['rows']), f"clock-out: nothing the driver did not log is ticked ({[x['name'] for x in r['rows'] if x['on']]})")
    c.ok(len(r['work']) == 2 and all(w['code'] == '01' for w in r['work']) and abs(sum(w['hours'] for w in r['work']) - 8.17) < 0.05,
         f"clock-out: the driver's hours land on cost code 01, split across what he ticked ({r['work']})")
    c.ok('logged' in r['toast'] and r['open'], f"clock-out: the driver's day toasts with Open ({r['toast']!r})")
    c.ok(not errs, f'clock-out: no page errors ({errs[:2]})')
    await b.close()


async def t_labels(c, p):
    b, pg, errs = await fresh(p, 'u_chen', False)
    r = await js(pg, """
      const v = DB.vendors.find(x => /window works/i.test(x.name)) || DB.vendors[0];
      const was = v.coiReceivedAt;
      DB.comms.push({ id: 'w1c3', threadId: 'w1t3', direction: 'in', date: today() + 'T08:00:00', subject: 'Certificate of insurance', from: { name: 'Harbor Insurance Brokers', email: 'certs@harbor.example' },
        text: 'Attached is the certificate for ' + v.name + ', policy 9/3/26 to 9/2/27.', route: { vendorId: v.id }, proposals: [{ id: 'w1p3', kind: 'coi', vendorId: v.id, exp: '2027-09-02', summary: v.name + ' certificate covers to 9/2/27', on: true }] });
      DB.comms.push({ id: 'w1c4', threadId: 'w1t4', direction: 'in', date: today() + 'T08:30:00', subject: 'Wire sent', from: { name: 'Jaleena Jessop', email: 'jj@example.com' },
        text: 'The money is sent: $12,000 by wire this morning.', route: {}, proposals: [{ id: 'w1p4', kind: 'deposit', amount: 12000, summary: 'Jaleena Jessop says $12,000 is sent', on: true }] });
      nyhInvalidate();
      const rows = nyhRows({ everyone: true }).filter(x => x.commId === 'w1c3' || x.commId === 'w1c4').map(x => ({ c: x.commId, verb: x.verb }));
      const c3 = DB.comms.find(x => x.id === 'w1c3');
      nyhApplyMail(c3, c3.proposals[0]); await sleep(150);
      const t = document.getElementById('toast'), a = t.querySelector('.toast-open');
      const said = t.innerText;
      a && a.click(); await sleep(250);
      return { rows, said, open: !!a, view, vendorOn: !!document.querySelector('.view.on') && document.querySelector('.view.on').innerText.includes(v.name), coi: v.coiReceivedAt !== was };""")
    verbs = {x['c']: x['verb'] for x in r['rows']}
    c.ok(verbs.get('w1c4') == 'Watch the Feed', f"labels: the money-is-sent row says Watch the Feed, not Apply ({verbs})")
    c.ok(verbs.get('w1c3') == 'File on the Vendor', f"labels: the certificate row says File on the Vendor ({verbs})")
    c.ok(r['coi'] and r['open'] and r['view'] != 'comms' and r['vendorOn'], f"labels: the certificate's toast Open goes to the vendor, not the Inbox ({r['said']!r} -> {r['view']})")
    # the hold sheet and Add Milestone
    r = await js(pg, """
      const cm = { id: 'w1c5', threadId: 'w1t5', direction: 'in', date: today() + 'T09:00:00', subject: 'Meeting', from: { name: 'Samantha Field', email: 'sf@example.com' }, text: 'Could we meet on 9/10 at 10 at the house?', route: {} };
      DB.comms.push(cm);
      flHoldDialog(cm, { who: 'Samantha Field', date: '2026-09-10', from: '10:00', to: '11:00', sentence: 'Could we meet on 9/10 at 10?' }); await sleep(100);
      const m = document.getElementById('mbm'); const h = m.querySelector('h3').innerText, ok = m.querySelector('#mbm-ok').innerText; m.remove();
      view = 'sched'; render(); await sleep(150);
      const ms = document.getElementById('btn-addms'); ms && ms.click(); await sleep(150);
      const t = (document.getElementById('d-title') || {}).innerText; try { closeEditor(); } catch (e) {}
      return { h, ok, t, ms: !!ms };""")
    c.ok(r['h'].startswith('Book the Meeting') and r['ok'] == 'Book It', f"labels: Book It opens Book the Meeting, whose button is Book It ({r})")
    c.ok(not r['ms'] or r['t'] == 'New Milestone', f"labels: Add Milestone's editor is titled New Milestone ({r})")
    c.ok(not errs, f'labels: no page errors ({errs[:2]})')
    await b.close()
    b, pg, errs = await fresh(p, 'u_alex', True)
    r = await js(pg, """
      setCurrent('p121'); DB.time = DB.time.filter(t => !(t.empId === 'em3' && !t.out));
      view = 'route'; render(); await sleep(250);
      const btn = document.getElementById('fm-rclock'); const lab = btn && btn.innerText;
      btn && btn.click(); await sleep(400);
      return { lab, view, open: DB.time.some(t => t.empId === 'em3' && !t.out), after: (document.getElementById('fm-rclock') || {}).innerText };""")
    c.ok(r['lab'] == 'Clock In' and r['view'] == 'route' and r['open'], f"labels: Route's Clock In clocks in and the driver stays on Route ({r})")
    c.ok((r['after'] or '').startswith('Clock Out'), f"labels: Route's button then reads Clock Out ({r['after']!r})")
    await b.close()


async def t_silent(c, p):
    b, pg, errs = await fresh(p, 'u_controller', False)
    r = await js(pg, """
      view = 'ap'; render(); await sleep(200);
      const host = document.querySelector('.view.on');
      let did = 0;
      const mk = () => { const b = document.createElement('button'); b.className = 'btn'; b.dataset.w1test = 'go'; b.textContent = 'Do the Test Step';
        b.onclick = () => { if (!appConfirm('Do the test step now?')) return; did++; toast('Test step done'); }; host.prepend(b); return b; };
      let b = mk(); b.click(); await sleep(120);
      const asked = !!document.querySelector('#mbm #mbm-ok');
      // the list is drawn again under the question: the same button, a new element
      b.remove(); b = mk();
      document.querySelector('#mbm #mbm-ok').click(); await sleep(250);
      const t1 = document.getElementById('toast').innerText;
      b.remove();
      // a payroll run saved from its sheet says so
      const run = (DB.payroll || []).find(x => ['draft', 'submitted'].includes(x.status)) || (DB.payroll || [])[0];
      let pay = null;
      if (run) { openPayroll(run.id); await sleep(200); const t0 = document.getElementById('toast'); t0.classList.remove('on');
        savePayroll(); await sleep(150); const t = document.getElementById('toast'); pay = { on: t.classList.contains('on'), text: t.innerText, open: !!t.querySelector('.toast-open') }; }
      return { asked, did, t1, pay };""")
    c.ok(r['asked'] and r['did'] == 1 and 'Test step done' in r['t1'], f"silent: Yes, Continue does the step though the screen drew its button again ({r})")
    c.ok(r['pay'] is None or (r['pay']['on'] and 'saved' in r['pay']['text'] and r['pay']['open']), f"silent: a payroll save toasts with Open ({r['pay']})")
    await b.close()
    # the net under every sheet: a Save that changed the records and said nothing says what it saved (the crew Fix)
    b, pg, errs = await fresh(p, 'u_angel', True)
    r = await js(pg, """
      setCurrent('p121'); view = 'fcrew'; render(); await sleep(200);
      const t = document.getElementById('toast'); t.classList.remove('on');
      mbModal('Fix Alberto · Thu, Sep 3', '<div class="f"><label>In</label><input type="time" data-f="in" value="07:30"></div>', { submit: 'Save & approve', onSubmit: () => { const e = DB.time[0]; e.breakMin = (+e.breakMin || 0) + 5; save(); render(); } });
      await sleep(80); document.querySelector('#mbm #mbm-ok').click(); await sleep(400);
      const one = { on: t.classList.contains('on'), text: t.innerText, open: !!t.querySelector('.toast-open') };
      // a sheet that says it itself is left alone
      t.classList.remove('on');
      mbModal('Toolbox talk', '<input data-f="topic" value="Ladders">', { submit: 'Log it', onSubmit: () => { DB.time[0].breakMin += 1; toast('Toolbox talk logged'); } });
      await sleep(80); document.querySelector('#mbm #mbm-ok').click(); await sleep(400);
      return { one, two: t.innerText };""")
    c.ok(r['one']['on'] and r['one']['text'].startswith('Saved: Fix Alberto') and r['one']['open'], f"silent: a sheet that saved with no word now says what it saved, with Open ({r['one']})")
    c.ok(r['two'].startswith('Toolbox talk logged'), f"silent: a sheet that toasts for itself keeps its own words ({r['two']!r})")
    await b.close()
    b, pg, errs = await fresh(p, 'u_owner', False)
    r = await js(pg, """
      const m = (DB.meetings || [])[0]; if (!m) return { none: true };
      view = 'meetings'; mtOpen = m.id; render(); await sleep(200);
      const b = document.getElementById('mt-redo'); if (!b) return { nobtn: true };
      b.click(); await sleep(200);
      return { text: document.getElementById('toast').innerText, on: document.getElementById('toast').classList.contains('on') };""")
    c.ok(r.get('none') or r.get('nobtn') or (r['on'] and 'Read the notes again' in r['text']), f"silent: Re-Read says what it found ({r})")
    # Add Line on an estimate says which line it added, with Open to it
    r = await js(pg, """
      let pick = null;
      for (const cl of DB.clients || []) { const d = (cl.estimates || []).find(x => x.status === 'draft'); if (d) { pick = [cl, d]; break; } }
      if (!pick) return { none: true };
      const [cl, d] = pick; clientOpen = cl.id; docOpen = { kind: 'estimate', id: d.id }; view = 'billing'; billTab = 'estimates'; render(); await sleep(300);
      const add = document.querySelector('.view.on [data-ctadd], .view.on [data-addline]'); if (!add) return { nobtn: true, n: d.lines.length };
      const n0 = d.lines.length; add.click(); await sleep(250);
      const t = document.getElementById('toast');
      return { n0, n1: d.lines.length, text: t.innerText, open: !!t.querySelector('.toast-open'), num: d.number };""")
    c.ok(r.get('none') or (not r.get('nobtn') and r['n1'] == r['n0'] + 1 and f"Line {r['n1']} added" in r['text'] and r['open']), f"silent: Add Line says which line it added, with Open ({r})")
    await b.close()


async def t_tax(c, p):
    b, pg, errs = await fresh(p, 'u_chen', False)
    r = await js(pg, """
      const out = [];
      (DB.pos || []).filter(po => ['draft', 'issued', 'pending'].includes(po.status) && !po.taxRule).forEach(po => out.push(po.number + ' has no tax rule'));
      // every order page drawn: no sheet or page sets the tax another way
      for (const po of (DB.pos || []).filter(x => !['received', 'closed', 'cancelled'].includes(x.status)).slice(0, 12)) {
        poOpen = po.id; view = 'po'; try { render(); } catch (e) {} await sleep(30);
        const want = p0PurchaseTax(po).status, kept = ['exempt-resale', 'exempt-st120'].includes(po.taxStatus) || (po.taxRule && /quote|entered/.test(po.taxRule.by || ''));
        po.taxStatus !== want && !kept && out.push(`${po.number}: ${po.taxStatus} on the page, the rule says ${want}`);
      }
      poOpen = null; view = 'home'; render();
      return out;""")
    c.ok(not r, f"purchase tax: every open order keeps P0's one rule through its page ({r[:5]})")
    await b.close()


async def main():
    c = Checks()
    async with async_playwright() as p:
        await t_mail_task(c, p, False)
        await t_mail_task(c, p, True)
        await t_promise_quick(c, p)
        await t_clock(c, p)
        await t_labels(c, p)
        await t_silent(c, p)
        await t_tax(c, p)
    sys.exit(c.done())

asyncio.run(main())
