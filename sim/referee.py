"""sim/referee.py: the independent scorer of the agent month (BACKLOG §1.17 item 7). The players never see it.

After each day (and on demand) it reads the world and writes sim/runs/<run>/ledger.json and ledger.md:
- every due event (the book's and the held-out ones): done on time, late or missed, and whether and when it
  reached the screen of the person who should act (from what that person's `screen` actually showed). The
  checks are tests/month_runtime.js's M.check, run on the world page, so the agent month and the scripted month
  score the same things the same way; the ledger arithmetic (working days, verdicts, money left behind,
  schedule days lost) is month_sim's;
- find-it-again failures: a person created a record and could not see it on their own screen right after
  (and, if it was missing then, after their next reload);
- places to look: per person, per day, per kind (owed / approve / money), the distinct screens they had to act
  from. More than one screen for the same kind is a finding (BACKLOG §1.16 layer 4);
- ties to the bank: every account's ERP lines against the lines the world's bank actually sent, lines typed by
  hand that the bank never sent, client payments recorded with no deposit, bills marked paid with no debit, and
  lines still matched to nothing (the figures finance_xcheck reads off the screens, computed from the records);
- outside the Standard: mail that left the firm without a person's own send (the system sent it), approvals
  by a role the delegation does not give that kind, and refused attempts to reach the database;
- the PERSIST check at the end (month_sim's: every record survives saveNow and a reload).
"""
import json, os, re
from collections import Counter, defaultdict
from datetime import date

APPROVE = re.compile(r'\b(approve|approved|approve as billed|reject|decline|authori[sz]e|sign off|accept)\b', re.I)
MONEY = re.compile(r'\b(pay|paid|bill it|record payment|match|reconcile|code it|categor|invoice|deposit|import|post|close|payroll|short-?pay|dispute)\b', re.I)
OWED = re.compile(r'\b(done|mark done|complete|send|reply|answer|order|receive|received|submit|file|log|clock|confirm|chase|got it|raise|request)\b', re.I)
# who may approve what (DELEGATION in the app, in plain terms; a tap outside this is a finding to look at)
MAY_APPROVE = [(re.compile(r'payroll', re.I), {'owner', 'controller'}), (re.compile(r'journal|entry', re.I), {'owner'}),
               (re.compile(r'\bCO-|change order', re.I), {'client', 'owner', 'pm'}), (re.compile(r'bill|invoice from|AMP-|WW-|CM-', re.I), {'owner', 'pm', 'controller', 'coord'})]

TIE_JS = """(bank) => { const out = { accounts: {}, typed: [], paymentsNoDeposit: [], billsPaidNoDebit: [], unmatched: 0 };
  const T = DB.txns || [];
  const key = l => String(l.ref || '') || (l.date + '|' + l.amt);
  const sent = {}; bank.forEach(l => { (sent[l.acct] = sent[l.acct] || []).push(l); });
  (DB.accounts || []).forEach(a => { const mine = T.filter(t => t.acct === a.id);
    const refs = new Set(mine.map(t => String(t.ref || t.bankRef || t.fitid || '')));
    const missing = (sent[a.id] || []).filter(l => !refs.has(String(l.ref)) && !mine.some(t => t.date === l.date && Math.abs(+t.amt - +l.amt) < 0.01));
    out.accounts[a.id] = { name: a.name, erpLines: mine.length, bankSent: (sent[a.id] || []).length, notImported: missing.map(l => `${l.date} ${l.desc} ${l.amt}`).slice(0, 20),
      erpSum: Math.round(mine.reduce((s, t) => s + (+t.amt || 0), 0) * 100) / 100 }; });
  const since = '2026-09-03';
  T.filter(t => t.date >= since && /manual|typed|hand/i.test(String(t.src || t.source || t.via || '')) ).forEach(t => out.typed.push(`${t.date} ${t.desc} ${t.amt} (${t.acct})`));
  (DB.clients || []).forEach(c => (c.payments || []).filter(p => (p.date || '') >= since).forEach(p => {
    if (!T.some(t => +t.amt > 0 && Math.abs(+t.amt - +p.amount) < 1)) out.paymentsNoDeposit.push(`${c.name}: ${p.date} $${p.amount}`); }));
  (DB.bills || []).filter(b => b.status === 'paid' && (b.paidOn || b.paidDate || '') >= since).forEach(b => {
    let amt = 0; try { amt = billTotal(b); } catch (e) {}
    if (!T.some(t => +t.amt < 0 && (t.billId === b.id || Math.abs(Math.abs(+t.amt) - amt) < 1))) out.billsPaidNoDebit.push(`${b.number} ${b.vendor} $${amt}`); });
  try { out.unmatched = PRED.unmatchedTxns.rows().length; } catch (e) { out.unmatched = null; }
  return out; }"""

SNAP_JS = """() => { const out = {}; const add = (k, arr) => { if (!Array.isArray(arr)) return;
    arr.forEach((r, i) => { if (r && typeof r === 'object') out[k + ':' + (r.id || r.number || i)] = JSON.stringify(r); }); };
  for (const [k, v] of Object.entries(DB)) {
    if (Array.isArray(v)) add(k, v);
    if (k === 'projects') v.forEach(p => { for (const [pk, pv] of Object.entries(p)) if (Array.isArray(pv)) add('p.' + p.id + '.' + pk, pv); });
    if (k === 'clients') v.forEach(c => { for (const ck of ['estimates', 'invoices', 'changeOrders', 'payments']) add('c.' + c.id + '.' + ck, c[ck]); });
  }
  return { recs: out, day: today() }; }"""


class Referee:
    def __init__(self, sim):
        self.sim = sim

    def wd_between(self, a, b):
        if b <= a: return 0
        x, n = date.fromisoformat(a), 0
        y = date.fromisoformat(b)
        from datetime import timedelta
        while x < y:
            x += timedelta(days=1)
            if x.weekday() < 5: n += 1
        return n

    def actions(self):
        p = os.path.join(self.sim.dir, 'actions.jsonl')
        if not os.path.exists(p): return []
        return [json.loads(l) for l in open(p) if l.strip()]

    async def score(self, final=False):
        sim, W = self.sim, self.sim.world
        day = sim.state['day']
        pg, _ = await sim.fresh('__world')
        events = [e for e in W.all_events() if e.get('expect') and e['day'] <= day]
        st = sim.state.setdefault('ref', {})
        done = W.st['done']
        todo = [e for e in events if e['id'] not in done]
        checks = [[e['expect']['check'], {**e, 'payload': e.get('payload') or {}}] for e in todo if e['expect']['check']['t'] != 'seenBy']
        res = await pg.evaluate("L => __MS.checkAll(L)", checks) if checks else []
        detail = st.setdefault('detail', {})
        for (c, e), (ok, d) in zip(checks, res):
            detail[e['id']] = d
            if ok: done[e['id']] = day
        for e in todo:
            c = e['expect']['check']
            if c['t'] == 'seenBy':
                s = sim.state['seen'].get(e['id'], {}).get(c.get('uid') or e['expect']['who'])
                detail[e['id']] = f'seen {s[0]} {s[1]} on {s[2]}' if s else 'not on their screens'
                if s: done[e['id']] = s[0]
        rows = []
        for e in events:
            x = e['expect']; d = done.get(e['id'])
            if d:
                late = self.wd_between(e['day'], d) - x['by']; verdict = 'on time' if late <= 0 else 'late'
            else:
                late = None; verdict = 'open' if self.wd_between(e['day'], day) < x['by'] else 'missed'
            seen = sim.state['seen'].get(e['id'], {}).get(x['who'])
            money_left = float(x.get('money') or 0) if verdict == 'missed' else 0.0
            days_lost = (x.get('days') or 0) if verdict == 'missed' else min(x.get('days') or 0, late or 0) if verdict == 'late' else 0
            rows.append({'id': e['id'], 'day': e['day'], 'kind': e['kind'], 'who': x['who'], 'what': x['what'], 'by': x['by'], 'verdict': verdict, 'done': d,
                         'late': late if verdict == 'late' else 0, 'detail': detail.get(e['id'], ''), 'seen': seen, 'money_left': money_left, 'days_lost': days_lost,
                         'heldout': 'held-out' in (e.get('tags') or []), 'check': x['check']['t']})
        scored = [r for r in rows if r['verdict'] != 'open']
        on = sum(r['verdict'] == 'on time' for r in scored); la = sum(r['verdict'] == 'late' for r in scored); mi = sum(r['verdict'] == 'missed' for r in scored)
        money = sum(r['money_left'] for r in scored); dl = sum(r['days_lost'] for r in scored)
        A = self.actions()
        fia = self.fia(A)
        places = self.places(A)
        tie = await pg.evaluate(TIE_JS, W.st['bank'] + [b for b in W.st.get('scheduled_bank', []) if False])
        standard = self.standard(A)
        from docs import AUDIT_JS, doc_type
        dkeys = list(dict.fromkeys(c['key'] for a in A for c in (a.get('creates') or []) if a.get('uid', '').startswith('u_') and doc_type(c['key'])))
        docs = await pg.evaluate(AUDIT_JS, dkeys) if dkeys else []
        line = (f"AGENT MONTH ({sim.run}, through {day}) caught {on}/{len(scored)} on time · {la} late · {mi} missed · ${money:,.0f} left behind · "
                f"{dl} schedule days lost · {len(fia['failures'])} find-it-again failures · {places['findings']} places-to-look findings · "
                f"{sum(len(d['findings']) for d in docs)} back-end gaps on {len(docs)} documents")
        out = {'line': line, 'day': day, 'events': rows, 'fia': fia, 'places': places, 'tie': tie, 'standard': standard, 'docs': docs,
               'actions': {'total': sum(1 for a in A if a.get('uid') in sim.state['people'] or a.get('uid', '').startswith('u_')),
                           'by_person': Counter(a['uid'] for a in A if a.get('uid', '').startswith('u_') and a.get('cmd') not in ('end_turn',))},
               'persist': st.get('persist')}
        json.dump(out, open(os.path.join(sim.dir, 'ledger.json'), 'w'), indent=1, default=str)
        self.write_md(out)
        sim.save_state()
        return {'line': line, 'ledger': os.path.join(sim.dir, 'ledger.md')}

    def fia(self, A):
        fails, ok = [], 0
        after = {}
        for a in A:
            if a.get('cmd') == 'fia_after_reload': after[(a['uid'], a['args'][0])] = a.get('ok')
        for a in A:
            for c in a.get('creates') or []:
                if c['on_screen']: ok += 1
                else:
                    fails.append({'uid': a['uid'], 'day': a['day'], 'slot': a['slot'], 'screen': a.get('after') or a.get('screen'), 'record': c['key'], 'name': c['name'],
                                  'in_toast': c['in_toast'], 'after_reload': after.get((a['uid'], c['key']))})
        return {'found': ok, 'failures': fails}

    def places(self, A):
        by = defaultdict(lambda: defaultdict(set))
        for a in A:
            if a.get('cmd') not in ('tap', 'key') or not a.get('ok'): continue
            lab = str(a.get('control') or '')
            for kind, rx in (('approve', APPROVE), ('money', MONEY), ('owed', OWED)):
                if rx.search(lab):
                    by[(a['uid'], a['day'])][kind].add(a.get('screen') or '?'); break
        rows, findings = [], 0
        for (uid, day), K in sorted(by.items()):
            r = {'uid': uid, 'day': day, **{k: sorted(v) for k, v in K.items()}}
            r['over'] = [k for k, v in K.items() if len(v) > 1]
            findings += len(r['over']); rows.append(r)
        return {'rows': rows, 'findings': findings}

    def standard(self, A):
        sim = self.sim
        out = {'sent_by_system': [], 'approvals_by_role': [], 'refused': []}
        for mid, r in sim.state['sent_seen'].items():
            if r.get('how') == 'system' and r.get('to') and 'smartdesign.nyc' not in str(r.get('to')):
                out['sent_by_system'].append(f"{r.get('day')} {r.get('slot')} {r.get('by')} -> {r.get('to')}: {r.get('subject', '')[:80]}")
        from server import PEOPLE
        for a in A:
            if a.get('refused'): out['refused'].append(f"{a['day']} {a['uid']}: {a.get('cmd')}")
            if a.get('cmd') == 'tap' and APPROVE.search(str(a.get('control') or '')):
                role = PEOPLE.get(a['uid'], ('?',))[0]
                ctx_ = f"{a.get('screen', '')} {a.get('result', '')}"
                for rx, roles in MAY_APPROVE:
                    if rx.search(ctx_) and role not in roles:
                        out['approvals_by_role'].append(f"{a['day']} {a['uid']} ({role}) tapped {a.get('control')} on {a.get('screen')}"); break
        return out

    async def persist_check(self):
        sim = self.sim
        pg, _ = await sim.fresh('__world')
        before = await pg.evaluate(SNAP_JS)
        await sim.commit('__world')
        await sim.boot('__world')
        after = await pg.evaluate(SNAP_JS)
        b, a = before['recs'], after['recs']
        lost = sorted(k for k in b if k not in a); changed = sorted(k for k in b if k in a and b[k] != a[k])
        r = {'records': len(b), 'lost': lost[:60], 'n_lost': len(lost), 'changed': changed[:60], 'n_changed': len(changed),
             'added': len([k for k in a if k not in b]), 'dayBefore': before['day'], 'dayAfter': after['day']}
        sim.state.setdefault('ref', {})['persist'] = r
        sim.save_state()
        r['line'] = f"PERSIST {r['records']} records · {r['n_lost']} lost after reload · {r['n_changed']} changed by boot · day {r['dayBefore']} -> {r['dayAfter']}"
        return r

    def write_md(self, out):
        sim = self.sim
        L = [f"# The agent month: {sim.run}\n", out['line'] + '\n',
             'Invented data only. Scored by sim/referee.py from the world, never by the players. "Reached" is the first time the event was on the screen of the person who should act.\n']
        rows = out['events']; scored = [r for r in rows if r['verdict'] != 'open']
        L.append('## Missed and late, most expensive first\n')
        L.append('| Event | Day | Who | Reached their screen | Verdict | Detail | $ left | Days |')
        L.append('|---|---|---|---|---|---|---|---|')
        for r in sorted([r for r in scored if r['verdict'] in ('missed', 'late')], key=lambda r: (-r['money_left'], -r['days_lost'], r['day']))[:60]:
            seen = f"{r['seen'][0][5:]} {r['seen'][1]} ({r['seen'][2][:24]})" if r['seen'] else 'never'
            L.append(f"| {r['id']}{' (held-out)' if r['heldout'] else ''} {r['what'][:80]} | {r['day'][5:]} | {r['who']} | {seen} | {r['verdict']}{' +' + str(r['late']) + 'd' if r['late'] else ''} | {str(r['detail'])[:70]} | {r['money_left']:,.0f} | {r['days_lost']} |")
        L.append('\n## By person\n')
        by = defaultdict(list)
        for r in scored: by[r['who']].append(r)
        for who, R in sorted(by.items()):
            L.append(f"- **{who}**: {len(R)} due · {sum(r['verdict'] == 'on time' for r in R)} on time · {sum(r['verdict'] == 'late' for r in R)} late · "
                     f"{sum(r['verdict'] == 'missed' for r in R)} missed · {sum(1 for r in R if r['seen'])} reached their screens · {out['actions']['by_person'].get(who, 0)} actions")
        f = out['fia']
        L.append(f"\n## Find it again: {f['found']} creates seen by their creator, {len(f['failures'])} not\n")
        for x in f['failures'][:40]:
            L.append(f"- {x['day']} {x['slot']} {x['uid']} created \"{x['name'][:60]}\" ({x['record']}) on {x['screen']}: "
                     f"{'only in the toast' if x['in_toast'] else 'not on their screen'}{'; after a reload: ' + ('found' if x['after_reload'] else 'still not found') if x['after_reload'] is not None else ''}")
        p = out['places']
        L.append(f"\n## Places to look: {p['findings']} findings (more than one screen for the same kind of thing in a day)\n")
        for r in p['rows']:
            if r['over']: L.append(f"- {r['day']} {r['uid']}: " + '; '.join(f"{k} on {len(r.get(k, []))} screens ({', '.join(x[:30] for x in r.get(k, []))})" for k in r['over']))
        t = out['tie']
        L.append('\n## Ties to the bank\n')
        for k, a in (t.get('accounts') or {}).items():
            L.append(f"- {a['name']} ({k}): {a['erpLines']} lines in the ERP · the bank sent {a['bankSent']} this run · {len(a['notImported'])} not imported"
                     + (f" ({'; '.join(a['notImported'][:5])})" if a['notImported'] else ''))
        L.append(f"- lines matched to nothing: {t.get('unmatched')} · typed by hand: {len(t.get('typed') or [])} · client payments with no deposit: "
                 f"{len(t.get('paymentsNoDeposit') or [])} · bills paid with no debit: {len(t.get('billsPaidNoDebit') or [])}")
        for k in ('paymentsNoDeposit', 'billsPaidNoDebit', 'typed'):
            for x in (t.get(k) or [])[:8]: L.append(f"  - {k}: {x}")
        L.append(f"\n## Documents: back end of every document a person created ({len(out.get('docs') or [])})\n")
        for d in out.get('docs') or []:
            L.append(f"- {d['type']} {d.get('number', '')} ({d.get('status', '')}, {d.get('project', '')}): " + ('; '.join(d['findings']) or 'complete') + (f" · {'; '.join(d.get('notes') or [])}" if d.get('notes') else ''))
        s = out['standard']
        L.append('\n## Outside the Standard (to look at)\n')
        L.append(f"- mail that left the firm with no person's own send: {len(s['sent_by_system'])}")
        for x in s['sent_by_system'][:20]: L.append(f"  - {x}")
        L.append(f"- approvals by a role the delegation does not name: {len(s['approvals_by_role'])}")
        for x in s['approvals_by_role'][:20]: L.append(f"  - {x}")
        L.append(f"- refused attempts to go around the screens: {len(s['refused'])}")
        if out.get('persist'): L.append(f"\n## Persist\n\n{json.dumps({k: v for k, v in out['persist'].items() if k != 'line'})[:900]}\n")
        L.append('\n## Every event\n')
        L.append('| Event | Day | Kind | Who | Expected | By | Verdict | Reached | Detail |')
        L.append('|---|---|---|---|---|---|---|---|---|')
        for r in rows:
            L.append(f"| {r['id']} | {r['day'][5:]} | {r['kind']} | {r['who']} | {r['what'][:70]} | {r['by']} | {r['verdict']} | {(r['seen'] or ['-'])[0][5:]} | {str(r['detail'])[:60]} |")
        open(os.path.join(sim.dir, 'ledger.md'), 'w').write('\n'.join(L) + '\n')
