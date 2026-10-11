"""month_sim: a month of the company, September 2026, and what fell through the cracks.

Alan asked for the test to be "a simulation of a month of the company", not one day: did each person get
what they needed to move things forward, and what fell through the cracks? A one-day walk cannot show a chase
that never went out, a promise past its date, a credit never matched by month-end, or a lesson that never
fires twice. This suite runs 21 working days, 2026-09-03 to 2026-10-02 (Labor Day 9/7 is skipped).

THE CLOCK. One browser page for the whole month. Each simulated day moves the app's day through
appSetDay(day) (src/app.js, the one writer of the day: it pins DB.company.asOf, re-reads every project's
today, moves the Demo Workspaces' clock, and runs APP_DAY_HOOKS: fTick, clTaskSweep, b4Sweep, smSweep,
hbSeqTick, bnTick). The browser's own clock is pinned to the simulated moment (page.clock) so the time of day
is deterministic and no real date leaks in; Math.random is seeded, so ids repeat run to run. Each staff
persona's watcher (gsRun: the mail, calendar and drive pull, then paWatch, the expectation chases, payment
claims and master-data sweeps) runs twice a day, the way the lost hosted watcher would have.

THE BOOK (tests/month_book.json, invented data only). About 300 dated events, each with
expect {who, what, by (working days), money?, days?, see[], check{}}. They go in through the app's own
paths: mail, calendar and drive items are appended to the persona's Demo Workspace (DEMO_WS) and synced;
bank and card lines arrive as a CSV statement through the Import Statement dialog; field events through the
foreman's and crew's functions (fSend, addRequest, prgSet); client actions through the portal's functions.
Events of kind "seed" are what the seed and the built-in Demo Workspace already hold on 9/3; "due" events
are things the calendar brings due.

THE ACTORS (scripted, deterministic, no AI). Each day, each role signs in and acts ONLY on what its own
screens show: Home's Do Now and Caught for You (owner, PM), the classic Home's "Today, in the order I'd do
it" and "Waiting on other people" (coordinator, billing, controller), Approvals, the Inbox's proposals, the
Billing Queue, Banking, the foreman's Today, the designer's My Day, the client's Waiting on You. A role never
reads the book to decide what to do (the clients' late choices are world facts in the book, and the client
waits on them). Up to 12 actions a day each. Buttons are pressed in the page (element.click() on the real
button, so the button's own handler runs); where a step lives in a sheet the generic sheet driver fills the
blanks with a plain sentence and presses the sheet's primary (the house rule: the blue button is the safe
next step). Where clicking would be slow or the flow has no button on the person's screen, the policy calls
the function the button calls; the action log says which ("fn:" prefix).

THE LEDGER. After each day every due event is scored: caught on time / caught late (days late) / missed;
whether it reached the screen of the person who should have seen it, and on which day; money left behind and
schedule days lost. Output: review/month/ledger.json, review/month/ledger.md (a day-by-day of the month: what
each person saw, did and missed), screenshots per role on day 1, the worst day and the close day, and the line
    MONTH caught X/Y on time · Z late · W missed · $M left behind · D schedule days lost
Exit 1 when anything is missed (it will be, today; that is the point).

    python3 month_sim.py                 # the month (about 10-20 minutes)
    python3 month_sim.py --days 3        # the first three days only (quick check)
    python3 month_sim.py --no-shots      # skip screenshots
"""
import asyncio, json, os, sys, time, argparse, shutil, re
from harness import *

HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = os.path.join(HERE, 'month_book.json')
OUT = os.path.join(ROOT, 'review', 'month')
SITE = {'latitude': 40.6893, 'longitude': -73.9908}   # 121 State Street, Brooklyn (the seed's job address)
TZ = '-04:00'                                           # the firm's clock (America/New_York, EDT in September)
PERSONAS = ['u_owner', 'u_alan', 'u_chen', 'u_angel', 'u_sarah', 'u_billing', 'u_controller', 'u_alberto', 'u_alex']
ROLES = [  # (uid, role, phone), in the order their mornings start: the field first, then the office, the clients last
    ('u_angel', 'foreman', True), ('u_alberto', 'crew', True), ('u_alex', 'driver', True), ('u_controller', 'controller', False),
    ('u_owner', 'owner', False), ('u_alan', 'pm', False), ('u_chen', 'coord', False), ('u_billing', 'billing', False),
    ('u_sarah', 'designer', False), ('u_klein', 'client', True), ('u_cambri', 'client', True)]
FIRST = {'foreman': 'ftoday', 'crew': 'time', 'driver': 'route', 'controller': 'home', 'owner': 'home', 'pm': 'home', 'coord': 'home',
         'billing': 'billing', 'designer': 'sday', 'client': 'client'}
CAP = 12

# Where to look when an expectation is missed: the app function that owns that step (the fix lanes start here).
RESPONSIBLE = {
    'bill': 'cmApply (bill proposal: PO and job named in the PDF are dropped) / cmRoute (subject names the job)',
    'billOnce': 'cmApply (bill): no dedupe on vendor + invoice number across mailboxes',
    'billShort': 'billAction "short" / apprBillYes over-PO sheet',
    'billShortAny': 'billFlags + apprBillYes: a bill past its PO balance',
    'mat': 'cmApply (quote): Apply opens New Task instead of pricing the Buy Board line',
    'po': 'newPODialog / poAction("issue"): no order path from the late line; Buy goes to the FF&E board',
    'poEta': 'cmApply (delivery): a vendor date stays a note, never the PO expected date',
    'poEtaAny': 'cmApply (delivery): a vendor date stays a note, never the PO expected date',
    'poStatus': 'poAction("receive") / lkBillPO: nothing tells the coordinator a delivery is due',
    'coi': 'cmApply (coi): a certificate for a sub not on file is only "noted"',
    'outreach': 'eaNudge: Chase writes a note on the record; no mail, draft or outbox to the party (paChaseWatch)',
    'txn': 'pay3Suggest / truthCandidates / bfIngest rules: the line is coded but reaches no bill, PO, invoice or run',
    'dup': 'bfIngest: no duplicate-charge check at import (analystFindings only)',
    'payment': 'the bank deposit raises no "record this payment" for billing (billingNeeds / readyToBill)',
    'invoice': 'readyToBill / blRtb: the item never reached the Billing Queue',
    'rebilled': 'readyToBill: no reimbursable row for client purchases (BACKLOG 1.5 #1, spUnbilled)',
    'rtbGone': 'spUnbilled / readyToBill: floating client purchases are reported, never billed',
    'raise': 'DELEGATION.raise / PRED.waitingOnMe: the field item never reached the person who answers it',
    'request': 'addRequest / cmApply (request): a field ask in mail never becomes a request; requestAction',
    'task': 'cmRead promise rule / mtIngest: a promise or ask becomes no dated task for its owner',
    'taskDone': 'cmApply (permit / lpc): agency mail closes no schedule task',
    'insp': 'cmApply (permit): a DOB NOW window is a permit note, no booking proposal',
    'co': 'fAnswerRaise / opsRaiseCO: an approved overage never becomes a priced CO',
    'coStatus': 'portal CO approval',
    'coResolved': 'a client CO dispute lands as Inbox mail; no revise / withdraw path from it',
    'coBilled': 'readyToBill: approved CO lines held with the job (wipRow over)',
    'decision': 'cmApply (decision): a choice made by mail is logged but the decision stays open on the portal',
    'subm': 'smRespond / Release Order',
    'meeting': 'mtIngest proposals waiting in Meetings',
    'meetingFrom': 'gsRouteFile: a transcript in Drive is only nudged (mtIngest not run on Drive text)',
    'lesson': 'bnSuggestLessons runs only when The Brain renders; no lesson from a repeated no-show',
    'payroll': 'payrollAction("approve") is the Owner\'s; a submitted run is in no one\'s Approvals (DELEGATION has no payroll kind)',
    'payrollRun': 'payrollFromTime: nothing prompts the run before payday; approval sits with the Owner',
    'hours': 'timeAction approve / mApprovals time rows',
    'logs': 'dlSubmit',
    'recon': 'cmApply (statement): a statement in mail or Drive becomes a task, not an import and a reconcile',
    'close': 'fin2RunClose / ctCloseStatus blockers',
    'unmatched': 'bankUnmatched / truthCandidates: lines left with no match or exception at close',
    'journal': 'glEntrySave → owner Approvals (DELEGATION.journal)',
    'seenBy': 'the role\'s Home / Today collectors (tdQueue, eaToday, fToday)',
    'ignored': 'cmRead: promotions and newsletters',
    'lead': 'cmApply (lead) / paMasterApply: a new inquiry is never put on file',
    'oblig': 'bnObligationTasks: the renewal is listed, nothing files it',
    'riveraFixed': 'billingNeeds: payments recorded but not in the bank',
    'clientCredit': 'readyToBill: no client credit row when a billed purchase is refunded (BACKLOG 1.5 #4)',
    'clientAnswered': 'cmRoute (portal): a client question is Inbox work ("New · Review / Ignore / Delete"), not Do Now',
    'confirmSub': 'fAnswerRaise (noshow): answering slips nothing, rebooks nothing, confirms nothing',
    'fileRouted': 'gsRouteFile',
    'calendar': 'paEvents / gaHold: no booking from the mail',
    'noDupBill': 'cmRead: a vendor statement for a paid order',
    'noBillFrom': 'cmRead: money direction (a Zelle credit read as a bill)',
    'disputeResolved': 'pay3 dispute: a vendor credit memo has no path to close the held difference (1300)',
    'lineBilled': 'readyToBill: a job-level hold (wipRow over) hides measured lines ahead of billing (BACKLOG 1.5 #2)',
}

SEED_JS = r"""
// the phone at the job site answers at once (the crew's clock-in reads the location)
(() => { try { const pos = { coords: { latitude: 40.6893, longitude: -73.9908, accuracy: 12 }, timestamp: 0 };
  Object.defineProperty(navigator, 'geolocation', { value: { getCurrentPosition: (ok) => setTimeout(() => ok(pos), 0), watchPosition: (ok) => { setTimeout(() => ok(pos), 0); return 1; }, clearWatch: () => {} } }); } catch (e) {} })();
(() => { let s = 20260903 >>> 0;
  Math.random = function () { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; })();
"""

RUNTIME_JS = open(os.path.join(HERE, 'month_runtime.js'), encoding='utf-8').read()


def working_days(book):
    return book['days']


def csv_text(lines):
    return 'Date,Description,Amount,Reference\n' + ''.join(f"{l['date']},{l['desc']},{l['amt']:.2f},{l['ref']}\n" for l in lines)


def wd_between(days, a, b):
    """working days from a to b (b after a) on the month's calendar; days past the month count as working days"""
    if b <= a: return 0
    idx = {d: i for i, d in enumerate(days)}
    if a in idx and b in idx: return idx[b] - idx[a]
    return sum(1 for d in days if a < d <= b) + (0 if b <= days[-1] else 1)


def own_uid(e):
    """Whose turn injects an event that needs a person's hands (a field report, a portal action, a fact a due event puts in place)."""
    k, p = e['kind'], e.get('payload') or {}
    if k in ('field', 'client'): return e['actor']
    if k == 'due':
        if p.get('create'): return 'u_owner'
        if p.get('typed'): return 'u_chen'
        if p.get('journal'): return 'u_controller'
    return None


def responsible(t, detail):
    # the step that failed depends on how far the record got
    d = str(detail or '')
    if t == 'bill' and d.startswith('submitted'):
        return 'mApprovals / DELEGATION.bill: the bill at this person\'s turn sits under "waiting on the others", not on their list'
    if t == 'bill' and d.startswith('approved'):
        return 'apprBillYes: approved in full with no PO or job to hold it to'
    if t == 'payment' and 'no payment' in d:
        return ('Banking + billingNeeds: once the deposit is coded as income it leaves billing\'s screen (only "$N not yet cleared" '
                'remains); nothing raises Record Payment on the open invoice')
    return RESPONSIBLE.get(t, '')


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=0)
    ap.add_argument('--no-shots', action='store_true')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    book = json.load(open(BOOK, encoding='utf-8'))
    days = working_days(book)
    run_days = days[:a.days] if a.days else days
    events = book['events']
    by_day = {}
    for e in events: by_day.setdefault(e['day'], []).append(e)
    os.makedirs(OUT, exist_ok=True)
    shots_tmp = os.path.join(OUT, 'shots_tmp')
    if os.path.isdir(shots_tmp): shutil.rmtree(shots_tmp)
    os.makedirs(shots_tmp, exist_ok=True)
    t_start = time.time()
    state = {e['id']: {'done': None, 'detail': '', 'seen': {}, 'injected': None} for e in events}
    daylog = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport=DESKTOP, geolocation=SITE, permissions=['geolocation'], timezone_id='America/New_York')
        await ctx.add_init_script(SEED_JS)
        pg = await ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
        async def at(day, hm):
            await pg.clock.set_system_time(f'{day}T{hm}:00{TZ}')
        await at(days[0], '06:00')
        await pg.goto(URL)
        await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=90000)
        await pg.evaluate(RUNTIME_JS)
        phone = False
        async def viewport(ph):
            nonlocal phone
            if ph != phone:
                await pg.set_viewport_size(PHONE if ph else DESKTOP); phone = ph
        def log(*x):
            if not a.quiet: print(*x, flush=True)
        for di, day in enumerate(run_days):
            D = {'day': day, 'clock': None, 'injected': [], 'imports': [], 'syncs': {}, 'actions': {}, 'seen': {}, 'evening': {}, 'errors': [], 'phase': {}}
            t_day = time.time()
            # ---- 1. the clock: the app's day turns, and what a new day runs runs
            await at(day, '06:30')
            D['clock'] = await pg.evaluate("d => appSetDay(d)", day)
            if di == 0:
                await at(day, '06:40')
                D['connect'] = {u: await pg.evaluate("u => __MS.connect(u)", u) for u in PERSONAS}
            todays = by_day.get(day, [])
            am = [e for e in todays if e['time'] < '10:00']
            pm_ = [e for e in todays if e['time'] >= '10:00']
            async def ws(batch):
                for e in batch:
                    k = e['kind']
                    try:
                        if k == 'mail': r = await pg.evaluate("e => __MS.wsMail(e)", e)
                        elif k == 'calendar': r = await pg.evaluate("e => __MS.wsEvent(e)", e)
                        elif k == 'drive': r = await pg.evaluate("e => __MS.wsFile(e)", e)
                        else: continue
                    except Exception as ex: r = 'ERR ' + str(ex)[:160]
                    state[e['id']]['injected'] = r; D['injected'].append([e['id'], k, str(r)[:80]])
            # ---- 2. overnight and early mail, calendar and drive land in the workspaces
            await at(day, '06:50'); t0 = time.time()
            await ws(am)
            bank_lines = {}
            for e in todays:
                if e['kind'] == 'bank': bank_lines.setdefault(e['payload']['acct'], []).append(e['payload']); state[e['id']]['injected'] = 'statement'
            # ---- 3. each person's morning: their own reports go in, the watcher pulls, they read their screens and act
            open_needles = {e['id']: e['expect']['see'] for e in events
                            if e['day'] <= day and state[e['id']]['done'] is None and e['expect'].get('see')}
            for i, (uid, rname, ph) in enumerate(ROLES):
                hm = f'{7 + (i * 25) // 60:02d}:{(i * 25) % 60:02d}'
                tr = time.time(); pt = {}
                await at(day, hm); pt['at'] = round(time.time() - tr, 2)
                await viewport(ph); pt['vp'] = round(time.time() - tr, 2)
                own = [e for e in am if own_uid(e) == uid]
                bank = [[acct, f"{acct}_{day}.csv", csv_text(L)] for acct, L in bank_lines.items()] if rname == 'controller' else []
                try:
                    T = await pg.evaluate("([u, r, o]) => __MS.turn(u, r, o)", [uid, rname, {'own': own, 'bank': bank}]); pt['turn'] = round(time.time() - tr, 2)
                    for eid, r in T['injected']: state[eid]['injected'] = r; D['injected'].append([eid, 'own', r])
                    D['imports'] += T['imported']
                    if T.get('sync'): D['syncs'][uid] = T['sync']
                    seen0 = await pg.evaluate("([u, r, o]) => __MS.look(u, r, o)", [uid, rname, {'needles': open_needles}])
                    if not a.no_shots:
                        await pg.screenshot(path=os.path.join(shots_tmp, f'{day}_{rname}_{uid}.png'))
                    pt['shot'] = round(time.time() - tr, 2)
                    W = await pg.evaluate("([u, r, o]) => __MS.work(u, r, o)", [uid, rname, {'needles': open_needles, 'cap': CAP, 'opened': True}]); pt['work'] = round(time.time() - tr, 2)
                    W['seen'] = {**seen0, **W['seen']}
                    D.setdefault('pt', {})[uid] = pt
                    for eid, surf in W['seen'].items(): state[eid]['seen'].setdefault(uid, [day, surf])
                    D['seen'][uid] = len(W['seen']); D['actions'][uid] = W['acts']; D.setdefault('t', {})[uid] = {**T.get('t', {}), **W.get('t', {})}
                    if W['errs'] or T['errs']: D['errors'] += [f'{uid}: {x}' for x in (T['errs'] + W['errs'])]
                except Exception as ex:
                    D['errors'].append(f'{uid}: {str(ex)[:300]}')
                D['phase'][uid] = round(time.time() - tr, 1)
            await viewport(False)
            # ---- 4. the afternoon: what arrives after 10:00 is read the next morning; the crew clocks out; the log is signed
            await at(day, '16:00')
            await ws(pm_)
            for uid, rname, ph in ROLES:
                own = [e for e in pm_ if own_uid(e) == uid]
                if not own and rname not in ('crew', 'foreman'): continue
                await at(day, '16:30' if rname in ('crew', 'foreman') else '17:30')
                try:
                    r = await pg.evaluate("([u, r, o]) => __MS.evening(u, r, o)", [uid, rname, own])
                    D['evening'][uid] = r
                    for x in r:
                        if x[0] in state: state[x[0]]['injected'] = x[1]
                except Exception as ex: D['errors'].append(f'evening {uid}: {str(ex)[:200]}')
            # ---- 5. score every event that is due by today
            await at(day, '18:30')
            todo = [e for e in events if e['day'] <= day and state[e['id']]['done'] is None]
            res = await pg.evaluate("L => __MS.checkAll(L)", [[e['expect']['check'], e] for e in todo])
            for e, (ok, detail) in zip(todo, res):
                state[e['id']]['detail'] = detail
                if ok: state[e['id']]['done'] = day
            D['errors'] += errs[:]; del errs[:]
            D['secs'] = round(time.time() - t_day, 1)
            daylog.append(D)
            n_done = sum(1 for e in events if e['day'] <= day and state[e['id']]['done'])
            n_due = sum(1 for e in events if e['day'] <= day)
            log(f"{day}: {len(todays)} events · {sum(len(v) for v in D['actions'].values())} actions · {n_done}/{n_due} done so far · {D['secs']}s "
                f"({' '.join(f'{k[2:]}={v}' for k, v in D['phase'].items())})" + (f" · {len(D['errors'])} errors" if D['errors'] else ''))
        # month-end facts: what each missed money event still leaves behind
        line_gap = await pg.evaluate("() => __MS.lineGap || {}")
        month_end = await pg.evaluate("""() => { const out = {};
          try { const R = readyToBill(); out.readyToBill = Math.round(R.amount || 0); out.held = (R.held || []).map(h => [h.p.id, Math.round(h.amount), h.why]); } catch (e) {}
          try { out.spUnbilled = Math.round((spUnbilled() || []).reduce((a, r) => a + (+r.gap || 0), 0)); } catch (e) {}
          try { const p = DB.projects.find(x => x.id === 'p121'); out.finish121 = (p.tasks.find(t => t.id === 'sc') || {}).start; } catch (e) {}
          try { out.unmatched = PRED.unmatchedTxns.rows().length; } catch (e) {}
          return out; }""")
        final_shot_day = run_days[-1]
        # Persistence: a month of actions must survive a reload (same browser, same IndexedDB). Every record is
        # keyed by collection and id; after saveNow() and a reload, a record that is gone is a lost save, and a
        # record whose content changed is reported (boot migrations may legitimately touch some).
        SNAP = """() => { const out = {}; const add = (k, arr) => { if (!Array.isArray(arr)) return;
            arr.forEach((r, i) => { if (r && typeof r === 'object') out[k + ':' + (r.id || r.number || i)] = JSON.stringify(r); }); };
          for (const [k, v] of Object.entries(DB)) {
            if (Array.isArray(v)) add(k, v);
            if (k === 'projects') v.forEach(p => { for (const [pk, pv] of Object.entries(p)) if (Array.isArray(pv)) add('p.' + p.id + '.' + pk, pv); });
            if (k === 'clients') v.forEach(c => { for (const ck of ['estimates', 'invoices', 'changeOrders', 'payments']) add('c.' + c.id + '.' + ck, c[ck]); });
          }
          return { recs: out, day: today() }; }"""
        before = await pg.evaluate(SNAP)
        await pg.evaluate("async () => { try { await saveNow(); } catch (e) {} }")
        await pg.wait_for_timeout(1500)
        await pg.reload()
        await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=120000)
        await pg.wait_for_timeout(1500)
        after = await pg.evaluate(SNAP)
        b_r, a_r = before['recs'], after['recs']
        lost = sorted(k for k in b_r if k not in a_r)
        changed = sorted(k for k in b_r if k in a_r and b_r[k] != a_r[k])
        persist = {'records': len(b_r), 'lost': lost, 'changed': changed, 'added': len([k for k in a_r if k not in b_r]),
                   'dayBefore': before['day'], 'dayAfter': after['day']}
        log(f"PERSIST {len(b_r)} records · {len(lost)} lost after reload · {len(changed)} changed by boot · "
            f"{persist['added']} added by boot · day {before['day']} -> {after['day']}")
        if lost: log('  lost: ' + ', '.join(lost[:40]))
        if changed: log('  changed: ' + ', '.join(changed[:40]))
        await b.close()
    # ---------------------------------------------------------------- the ledger
    last = run_days[-1]
    rows = []
    for e in events:
        if e['day'] > last: continue
        st = state[e['id']]; x = e['expect']
        deadline_ok = None
        if st['done']:
            late = wd_between(days, e['day'], st['done']) - x['by']
            verdict = 'on time' if late <= 0 else 'late'
        else:
            late = None
            # still inside its window on the last simulated day: not yet due, not missed
            verdict = 'open' if wd_between(days, e['day'], last) < x['by'] else 'missed'
        seen_by = st['seen'].get(x['who'])
        money_left = 0.0
        if verdict == 'missed' and x.get('money'):
            money_left = float(x['money'])
            if x['check']['t'] == 'lineBilled': money_left = float(line_gap.get(e['id'], 0))
        days_lost = 0
        if x.get('days'):
            if verdict == 'missed': days_lost = x['days']
            elif verdict == 'late': days_lost = min(x['days'], late)
        rows.append({'id': e['id'], 'day': e['day'], 'kind': e['kind'], 'who': x['who'], 'what': x['what'], 'by': x['by'],
                     'verdict': verdict, 'done': st['done'], 'late': late if verdict == 'late' else 0, 'detail': st['detail'],
                     'seen': seen_by, 'seen_any': st['seen'], 'money': x.get('money'), 'money_left': round(money_left, 2), 'days_lost': days_lost,
                     'tags': e.get('tags', []), 'check': x['check']['t'], 'injected': str(st['injected'])[:120],
                     'fn': x.get('fn') or responsible(x['check']['t'], st['detail'])})
    scored = [r for r in rows if r['verdict'] != 'open']
    on_time = sum(1 for r in scored if r['verdict'] == 'on time'); late_n = sum(1 for r in scored if r['verdict'] == 'late')
    missed = sum(1 for r in scored if r['verdict'] == 'missed')
    money = sum(r['money_left'] for r in scored); dlost = sum(r['days_lost'] for r in scored)
    summary = f"MONTH caught {on_time}/{len(scored)} on time · {late_n} late · {missed} missed · ${money:,.0f} left behind · {dlost} schedule days lost"
    # screenshots: day 1, the worst day (the most misses falling due), the close day
    worst = None
    if rows:
        from collections import Counter
        cnt = Counter(r['day'] for r in scored if r['verdict'] == 'missed')
        worst = cnt.most_common(1)[0][0] if cnt else None
    close_day = '2026-10-01' if '2026-10-01' in run_days else last
    keep = {run_days[0], worst, close_day} - {None}
    shots = os.path.join(OUT, 'shots')
    if os.path.isdir(shots): shutil.rmtree(shots)
    os.makedirs(shots, exist_ok=True)
    for f in sorted(os.listdir(shots_tmp)):
        if f[:10] in keep: shutil.move(os.path.join(shots_tmp, f), os.path.join(shots, f))
    shutil.rmtree(shots_tmp, ignore_errors=True)
    secs = round(time.time() - t_start)
    out = {'summary': summary, 'runtime_s': secs, 'days': run_days, 'worst_day': worst, 'month_end': month_end,
           'events': rows, 'daylog': daylog}
    json.dump(out, open(os.path.join(OUT, 'ledger.json'), 'w'), indent=1, default=str)
    write_md(out, book)
    print(summary)
    print(f'runtime {secs}s · ledger review/month/ledger.md')
    sys.exit(1 if missed else 0)


def write_md(out, book):
    rows = out['events']; days = out['days']; L = []
    L.append('# The month: September 2026, what each person saw, did and missed\n')
    L.append(out['summary'] + '\n')
    L.append(f"Runtime {out['runtime_s']}s over {len(days)} working days. Worst day: {out['worst_day']}. "
             f"Month end: {json.dumps(out['month_end'])}\n")
    L.append('Invented data only (tests/month_book.json). "Seen" is the first day the event reached the screens of the person who should act; '
             '"fn" is the app function that owns the step that failed.\n')
    scored = [r for r in rows if r['verdict'] != 'open']
    L.append('## The most expensive cracks\n')
    L.append('| Event | Day | Who | Reached their screen | What happened | $ left | Days | Function responsible |')
    L.append('|---|---|---|---|---|---|---|---|')
    worst = sorted([r for r in scored if r['verdict'] in ('missed', 'late')], key=lambda r: (-(r['money_left'] or 0), -(r['days_lost'] or 0), r['verdict'] != 'missed', r['day']))[:40]
    for r in worst:
        seen = f"{r['seen'][0][5:]} ({r['seen'][1]})" if r['seen'] else 'never'
        L.append(f"| {r['id']} {r['what'][:90]} | {r['day'][5:]} | {r['who']} | {seen} | {r['verdict']}{' +' + str(r['late']) + 'd' if r['late'] else ''}: {r['detail'][:90]} | {r['money_left']:,.0f} | {r['days_lost']} | {r['fn'][:110]} |")
    L.append('\n## By person: did they get what they needed\n')
    by = {}
    for r in scored: by.setdefault(r['who'], []).append(r)
    for who, R in sorted(by.items()):
        on = sum(1 for r in R if r['verdict'] == 'on time'); la = sum(1 for r in R if r['verdict'] == 'late'); mi = sum(1 for r in R if r['verdict'] == 'missed')
        seen = sum(1 for r in R if r['seen']); never = [r for r in R if r['verdict'] == 'missed' and not r['seen']]
        L.append(f"- **{who}**: {len(R)} expected · {on} on time · {la} late · {mi} missed · {seen} reached their screens · "
                 f"{len(never)} missed without ever reaching them")
    L.append('\n## Day by day\n')
    for D in out['daylog']:
        day = D['day']
        L.append(f"### {day} ({D['secs']}s)")
        arrived = [r for r in rows if r['day'] == day]
        if arrived: L.append(f"- arrived: {len(arrived)} events ({', '.join(sorted(set(r['kind'] for r in arrived)))}); statements imported: "
                             + ('; '.join(f"{x[0]} {(x[1] or {}).get('label', x[1]) if isinstance(x[1], dict) else x[1]}" for x in D['imports']) or 'none'))
        for uid, acts in D['actions'].items():
            seen = D['seen'].get(uid, 0)
            did = [f"{x.get('verb')} ({x.get('sec')}: {x.get('item', '')[:60]})" for x in acts]
            L.append(f"- {uid}: {seen} open items on their screens; did {len(did)}" + (': ' + '; '.join(did[:12]) if did else ''))
        caught = [r for r in rows if r['done'] == day]
        fell = [r for r in scored if r['verdict'] == 'missed' and wd_between(days, r['day'], day) == r['by'] + 1]
        if caught: L.append(f"- caught today: {', '.join(r['id'] for r in caught)}")
        if fell: L.append("- fell past its window today: " + '; '.join(f"{r['id']} {r['what'][:60]} ({r['who']}: {r['detail'][:50]})" for r in fell))
        if D['errors']: L.append(f"- errors: {D['errors'][:3]}")
        L.append('')
    L.append('## Every event\n')
    L.append('| Event | Day | Kind | Who | Expected | By | Verdict | Seen | Detail |')
    L.append('|---|---|---|---|---|---|---|---|---|')
    for r in rows:
        L.append(f"| {r['id']} | {r['day'][5:]} | {r['kind']} | {r['who']} | {r['what'][:80]} | {r['by']} | {r['verdict']}{' +' + str(r['late']) + 'd' if r['late'] else ''} | {r['seen'][0][5:] if r['seen'] else '-'} | {r['detail'][:70]} |")
    open(os.path.join(OUT, 'ledger.md'), 'w').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    asyncio.run(main())
