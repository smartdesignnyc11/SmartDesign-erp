"""Role specialists (BACKLOG §1.28, §1.30, §1.31, §1.32 item 2): a standing auditor per role, proven on a planted bank.

  bank       Problems are planted into the demo the way they happen (records, never a seeder): a duplicate charge, a
             bill over its PO, an expired COI on an open order, unbilled design work, a cash-negative job, a line over
             budget, a missed early-pay discount, a client question unanswered past 2 business hours, a material not
             ordered by its order-by date, a late submittal, a request short of five days, a designer question past
             two days, and an unbudgeted cost over $1,000. Decoys sit beside them: a bill at its PO, a valid COI, a
             question asked 30 minutes ago, a discount with days left, a material ordered in time, two different
             charges of one amount, a job with cash in over cash out, a request with time, a fresh designer question,
             a cost under the line. Each role's checklist is read before and after. Every plant must be found by every
             role it belongs to, under the right line, with the right fix drafted (recall); every new finding must
             name a planted record, none a decoy (precision).
  six        One finding handled the six steps as the people do it: the rule and evidence, the cause from the
             records, the fix drafted and approved (the owner's short-pay; a credit-memo request drafted on
             Approvals), the task made through the one creator for the right person with a due date, the follow-up
             that re-reads the record (ticked but not fixed reopens; fixed closes the task), a dismissal with a reason
             never raised again, an approved fix proposed as the default under Company › Changes and drafted on its
             own once the owner approves.
  thresholds three quotes, the unbudgeted escalation, a milestone slip, the client acknowledgement and the Friday
             update: each from the live setting; a change drafted under Company › Changes moves the count once
             approved; a subcontract issued under three quotes is recorded on the PO.
  savings    the ledger from the records (the short-pay above, a disputed duplicate, discounts taken), by source and
             person; the owner's shares and a bonus credit; SV_SOURCES takes another lane's source; Ask reads it.
  workload   the overloaded person, a named person with room, the manager's yes offers the tasks (hand-offs).
  privacy    no person sees another's mail through a finding's cause; a field role reads no money in any line, Ask
             table or answer; a client reads none of it.
  screens    the checklist in Findings and the six-step sheet, desktop and phone (390px): the count on a line equals
             its source's rows, one blue button, no sideways scroll; the one-liner on each Home (Spanish for a
             Spanish-speaking foreman). Screenshots in review/specialists/.

All data is invented. The last line is `N flags`; exit 1 when N > 0.
    python3 specialists_test.py
"""
import asyncio, os, sys, json
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'specialists')
os.makedirs(SHOTS, exist_ok=True)
ROLES = [('owner', 'u_owner'), ('controller', 'u_controller'), ('pm', 'u_alan'), ('coord', 'u_chen'), ('billing', 'u_billing'), ('designer', 'u_sarah'), ('foreman', 'u_angel')]

# every role's open findings, as that person reads them: {role: {key: {check, what, sub, amount}}}
SNAP = r"""(roles) => { const out = {}; const was = (currentUser() || {}).id;
  for (const [r, u] of roles) { signIn(u); render.__tick = (render.__tick || 0) + 1;
    out[r] = {}; rsFindings(r).forEach(f => out[r][f.key] = { check: f.check.id, what: f.what, sub: f.sub || '', amount: f.amount }); }
  was && signIn(was); return out; }"""

# Plants and decoys, written straight into the records the way the app holds them. Returns the ids each one made.
PLANT = r"""() => {
  const td = today(), P = (id) => DB.projects.find(p => p.id === id), U = {};
  const pad = (n) => String(n).padStart(2, '0'), local = (ms) => { const d = new Date(ms); return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`; };
  const vPlant = { id: 'vPLANTWOOD', name: 'Plantwood Supply', trade: 'Lumber', insuranceExp: '2027-06-30', w9: true, email: 'orders@plantwood.example', region: 'nyc', terms: 'NET 30' };
  const vLapsed = { id: 'vLAPSED', name: 'Lapsed Masonry LLC', trade: 'Masonry', insuranceExp: '2026-08-01', w9: true, email: 'office@lapsedmasonry.example', region: 'nyc' };
  const vDecoy = { id: 'vDECOYMASON', name: 'Decoy Masonry Co', trade: 'Masonry', insuranceExp: '2027-05-01', w9: true, email: 'hi@decoymasonry.example', region: 'nyc' };
  DB.vendors.push(vPlant, vLapsed, vDecoy);
  const po = (id, number, vendor, total, line, extra) => Object.assign({ id, number, projectId: 'p121', vendor, vendorId: '', date: '2026-08-20', expected: '2026-09-20', status: 'issued', shipTo: 'site', notes: '', lines: [{ id: id + 'l', item: 'Planted line', desc: '', qty: 1, unit: 'ls', price: total, line: line || '', code: '07', received: 0 }], tax: 0, shipping: 0, matchedTxns: [], createdBy: 'Chen', type: 'materials', entityId: 'ent1', receipts: [], srcDocs: [], __v2: 1 }, extra || {});
  const bill = (id, number, vendor, amount, o) => Object.assign({ id, vendor, number, date: '2026-08-28', due: '2026-09-27', entityId: 'ent1', projectId: 'p121', poId: '', cat: 'materials', code: '07', line: '', lines: [{ id: id + 'l', desc: 'Planted', amount: amount }], status: 'pm-approved', approvals: [{ t: '8/28 9:00 AM', by: 'Chen', role: 'coord', action: 'submitted' }], createdBy: 'Chen', terms: 'NET 30' }, o || {});
  // P1 a duplicate charge: the same card payee and amount a day apart
  const t1 = { id: 'tPLANTDUP1', date: '2026-09-01', acct: 'ac2', desc: 'PLANTDUP LUMBER CO', amt: -742.18, cat: 'materials', projectId: '', code: '', vendor: 'Plantdup Lumber', memo: '', receipt: '', status: 'categorized', actor: 'Chen', source: 'manual', line: '' },
    t2 = Object.assign({}, t1, { id: 'tPLANTDUP2', date: '2026-09-02' });
  DB.txns.push(t1, t2); lkDupScan(['tPLANTDUP2']); U.dup = 'tPLANTDUP2';
  // P2 a bill over its PO
  // (on no job, so its cost moves no billing line: the bank's view of it is the plant)
  DB.pos.push(po('poPLANTOVER', 'PO-PLANT-OVER', 'Plantwood Supply', 5000, '', { projectId: '' }));
  DB.bills.push(bill('bPLANTOVER', 'PLANT-OVERPO', 'Plantwood Supply', 5600, { projectId: '', poId: 'poPLANTOVER', notes: 'Billed for 12 sheets; the PO was for 10.' })); U.overpo = 'bPLANTOVER';
  // P3 an expired COI on a vendor with an order open
  DB.pos.push(po('poPLANTCOI', 'PO-PLANT-COI', 'Lapsed Masonry LLC', 900, '', { projectId: '' })); U.coi = 'vLAPSED';
  // P4 design work reached and not billed: a converted design estimate whose first milestone is due
  const c140 = DB.clients.find(c => c.id === 'cl140');
  c140.estimates.push({ id: 'esPLANTDES', number: 'E-PLANT-DES', title: 'Planted design fee', date: '2026-08-20', status: 'converted', approvedOn: '2026-08-21', projectId: 'p140', template: 'design', billing: 'fixed', lines: [{ id: 'lPD1', item: 'Planted design phase', desc: '', qty: 1, unit: 'ls', rate: 12000, taxable: false, cost: 0, code: '15' }], discount: { type: 'pct', value: 0 }, taxRate: 0, terms: '', memo: '', entityId: 'ent1', milestonesBilled: [] }); U.unbilled = 'esPLANTDES';
  // P5 a cash-negative job: cost paid on 206 Lenox with nothing in
  DB.txns.push({ id: 'tPLANTCASH', date: '2026-09-01', acct: 'ac1', desc: 'PLANTCASH DEMO CONTRACTORS', amt: -18500, cat: 'subs', projectId: 'p206', code: '05', vendor: 'Plantcash Demo Contractors', memo: '', receipt: 'r.pdf', status: 'categorized', actor: 'Chen', source: 'manual', line: '' }); U.cashneg = 'p206';
  // P6 a line over budget (General conditions, budget $5,200): a bill on it for $6,000 with its PO
  DB.pos.push(po('poPLANTGC', 'PO-PLANT-GC', 'Plantwood Supply', 6000, 'estimate:es1:l13', { lines: [{ id: 'poPLANTGCl', item: 'Site protection', desc: '', qty: 1, unit: 'ls', price: 6000, line: 'estimate:es1:l13', code: '01', received: 1 }] }));
  DB.bills.push(bill('bPLANTGC', 'PLANT-GC', 'Plantwood Supply', 6000, { poId: 'poPLANTGC', line: 'estimate:es1:l13', code: '01' })); U.overbudget = 'eac:p121:estimate:es1:l13';
  // P7 a missed early-pay discount: 2/10 on a bill dated 8/20, approved, unpaid
  DB.bills.push(bill('bPLANTDISC', 'PLANT-DISC', 'Plantwood Supply', 4000, { projectId: '', date: '2026-08-20', due: '2026-09-19', status: 'approved', terms: '2/10 NET 30', approvedAt: '2026-08-31' })); U.discount = 'bPLANTDISC';
  // P8 a client question unanswered past 2 business hours (asked yesterday morning)
  const p121 = P('p121'); p121.clientQs = p121.clientQs || [];
  p121.clientQs.push({ id: 'cqPLANT', projectId: 'p121', by: 'Sarah Klein', text: 'PLANT: will the parlor floor be refinished before the movers come?', at: '2026-09-02T09:00:00', status: 'open', via: 'chat' }); U.client = 'cqPLANT';
  // P9 a material not ordered by its order-by date (rough plumbing starts 9/10, 20 working days' lead)
  p121.materials.push({ id: 'mPLANT', name: 'PLANT cast-iron radiator valves', cat: 'rough', taskId: 'rplumb', lead: 20, when: 'start', status: 'not-ordered', eta: '', vendor: 'Plantwood Supply', po: '', qty: '12 ea', cost: 1800, deliverTo: 'Site', notes: '', line: '' }); U.material = 'PLANT cast-iron radiator valves';
  // P10 a late submittal (a second plumbing submittal, with the sub since 8/31 and the approval date past)
  const sb = JSON.parse(JSON.stringify(p121.submittals.find(s => s.id === 'sb121plmb')));
  Object.assign(sb, { id: 'sbPLANT', number: '22 40 00-PLANT', title: 'PLANT shower valves, product data' }); p121.submittals.push(sb); U.submittal = 'sbPLANT';
  // P11 a field request short of five working days
  p121.requests.push({ id: 'rqPLANT', what: 'PLANT joist hangers', qty: 30, unit: 'ea', neededBy: iso(addDays(td, 1)), taskId: 'gframe', urgency: 'normal', note: '', fileId: '', by: 'Angel', at: td + 'T08:05:00', status: 'new', ackBy: '', ackAt: '', materialId: '', poId: '', eta: '', deliveredAt: '', log: [] }); U.request = 'rqPLANT';
  // P12 a field question to the designer, three working days old
  DB.field.raises.push({ id: 'frPLANT', projectId: 'p121', type: 'rfi', title: 'PLANT: which tile edge at the garden shower niche?', note: '', sheet: 'A-501', taskId: 'gframe', to: 'designer', cc: [], dueBy: '', by: 'Angel', at: '2026-08-31T09:00:00', status: 'seen', escalated: false, photos: [], calls: [] }); U.designer = 'frPLANT';
  // P13 an unbudgeted cost over $1,000: a bill on 121 State on no budget line, with no PO
  DB.bills.push(bill('bPLANTUNB', 'PLANT-UNB', 'Plantwood Supply', 2400, { status: 'submitted' })); U.unbudgeted = 'bPLANTUNB';
  // ---- decoys: near misses that must raise nothing
  DB.pos.push(po('poDECOYATPO', 'PO-DECOY-ATPO', 'Plantwood Supply', 2000, '', { projectId: '' }));
  DB.bills.push(bill('bDECOYATPO', 'DECOY-ATPO', 'Plantwood Supply', 2000, { projectId: '', poId: 'poDECOYATPO', cat: 'office', code: '' }));
  DB.pos.push(po('poDECOYCOI', 'PO-DECOY-COI', 'Decoy Masonry Co', 700, '', { projectId: '' }));
  p121.clientQs.push({ id: 'cqDECOY', projectId: 'p121', by: 'Sarah Klein', text: 'DECOY: is Friday still the walk-through?', at: local(Date.parse(appNowIso()) - 30 * 60e3), status: 'open', via: 'chat' });
  DB.bills.push(bill('bDECOYDISC', 'DECOY-DISC', 'Plantwood Supply', 3000, { projectId: '', date: iso(addDays(td, -1)), due: iso(addDays(td, 29)), status: 'approved', terms: '2/10 NET 30', cat: 'office', code: '' }));
  const far = p121.tasks.filter(t => t.start >= iso(addDays(td, 45))).sort((a, b) => a.start.localeCompare(b.start))[0];
  p121.materials.push({ id: 'mDECOY', name: 'DECOY brass escutcheons', cat: 'finish', taskId: far.id, lead: 2, when: 'start', status: 'not-ordered', eta: '', vendor: '', po: '', qty: '12 ea', cost: 120, deliverTo: 'Site', notes: '', line: '' });
  DB.txns.push({ id: 'tDECOYA', date: '2026-09-01', acct: 'ac2', desc: 'DECOY ALPHA HARDWARE', amt: -315.4, cat: 'office', projectId: '', code: '', vendor: 'Decoy Alpha', memo: '', receipt: 'a.pdf', status: 'categorized', actor: 'Chen', source: 'manual', line: '' },
                { id: 'tDECOYB', date: '2026-09-01', acct: 'ac2', desc: 'DECOY BETA SUPPLY', amt: -315.4, cat: 'office', projectId: '', code: '', vendor: 'Decoy Beta', memo: '', receipt: 'b.pdf', status: 'categorized', actor: 'Chen', source: 'manual', line: '' });
  lkDupScan(['tDECOYA', 'tDECOYB']);
  p121.requests.push({ id: 'rqDECOY', what: 'DECOY drywall screws', qty: 10, unit: 'box', neededBy: iso(addDays(td, 14)), taskId: 'gframe', urgency: 'normal', note: '', fileId: '', by: 'Angel', at: td + 'T08:05:00', status: 'new', ackBy: '', ackAt: '', materialId: '', poId: '', eta: '', deliveredAt: '', log: [] });
  DB.field.raises.push({ id: 'frDECOY', projectId: 'p121', type: 'rfi', title: 'DECOY: grout color for the powder room?', note: '', sheet: '', taskId: '', to: 'designer', cc: [], dueBy: '', by: 'Angel', at: local(Date.parse(appNowIso()) - 45 * 60e3), status: 'seen', escalated: false, photos: [], calls: [] });
  // the planted General conditions cost is also earned and not billed on its schedule-of-values line: its line ids
  U.svTokens = (DB.clients.find(c => c.id === 'cl121').sov || []).filter(s => /General conditions/i.test(`${s.desc || ''} ${s.name || ''} ${s.source || ''}`) || /es1:l13/.test(s.line || s.key || '')).map(s => s.id);
  save(); render.__tick = (render.__tick || 0) + 1; render();
  return U; }"""

# the plants: (name, roles that must find it, the line, a piece of the finding's key, the fix it must draft)
EXPECT = [
    ('duplicate charge', ['controller'], 'c.dup', 'lk:dup:tPLANTDUP2', 'dispute'),
    ('bill over its PO', ['controller'], 'c.overPO', 'bill:bPLANTOVER', 'shortpay'),
    ('expired COI', ['controller'], 'c.papers', 'vblock:vLAPSED', 'coiRequest'),
    ('expired COI', ['owner'], 'o.compliance', 'vblock:vLAPSED', 'coiRequest'),
    ('unbilled work', ['controller', 'billing'], 'c.earned', 'esPLANTDES', 'invoice'),
    ('cash-negative job', ['owner'], 'o.losing', 'cashneg:p206', 'escalation'),
    ('line over budget', ['controller', 'pm'], 'c.budget', 'eac:p121:estimate:es1:l13', 'co'),
    ('missed discount', ['controller'], 'c.discount', 'disc:bPLANTDISC', 'discountAsk'),
    ('client message past 2 hours', ['pm'], 'p.client', 'cq:cqPLANT', 'clientAck'),
    ('client message past 2 hours', ['owner'], 'o.clients', 'cq:cqPLANT', 'clientAck'),
    ('material not ordered by its order-by date', ['pm', 'coord'], 'p.materials', 'PLANT cast-iron radiator valves', 'order'),
    ('late submittal', ['pm', 'coord'], 'p.submittals', 'subm:sbPLANT', 'subChase'),
    ('request short of five days', ['foreman'], 'f.requests', 'rq5:rqPLANT', 'open'),
    ('designer question past two days', ['designer'], 'd.questions', 'dq:frPLANT', 'open'),
    ('unbudgeted cost over $1,000', ['owner'], 'o.escalations', 'unb:b:bPLANTUNB', 'escalation'),
    ('unbudgeted cost over $1,000', ['pm'], 'p.unbudgeted', 'unb:b:bPLANTUNB', 'escalation'),
]
PLANT_TOKENS = ['PLANT', 'tPLANTDUP', 'bPLANT', 'poPLANT', 'vLAPSED', 'Lapsed Masonry', 'esPLANTDES', 'cashneg:p206', 'es1:l13', 'cqPLANT', 'sbPLANT', 'rqPLANT', 'frPLANT', 'Plantwood', 'Plantdup', 'Plantcash']
DECOY_TOKENS = ['DECOY', 'Decoy']
# a new bank line is unmatched and needs a receipt until someone matches it: true of every line, decoys included
DECOY_OK = {'c.unmatched', 'c.receipt', 'f.questions'}  # f.questions: an open site question is open whatever its age


async def main():
    flags = []
    def flag(m):
        flags.append(m); print('FLAG', m)
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        # ---------------------------------------------------------------- bank
        before = await pg.evaluate(SNAP, ROLES)
        ids = await pg.evaluate(PLANT)
        after = await pg.evaluate(SNAP, ROLES)
        new = {r: {k: v for k, v in after[r].items() if k not in before[r]} for r, _ in ROLES}
        found, missed, wrongfix = 0, [], []
        per_role = {r: {'tp': 0, 'exp': 0, 'fp': 0, 'new': len(new[r])} for r, _ in ROLES}
        for name, roles, line, keypart, fixkind in EXPECT:
            for r in roles:
                per_role[r]['exp'] += 1
                hit = [k for k, v in new[r].items() if v['check'] == line and (keypart in k or keypart in v['what'])]
                if not hit:
                    missed.append(f'{r}: {name} ({line}, {keypart})'); continue
                found += 1; per_role[r]['tp'] += 1
                user = dict(ROLES)[r]
                got = await pg.evaluate("([u, k]) => { signIn(u); const X = rsSix(k); return X ? X.fix.kind : null; }", [user, hit[0]])
                if got != fixkind: wrongfix.append(f'{r}: {name} drafted {got}, expected {fixkind}')
        total = sum(len(e[1]) for e in EXPECT)
        fp, side = [], []
        for r, _ in ROLES:
            for k, v in new[r].items():
                text = k + ' ' + v['what'] + ' ' + v['sub']
                on_plant = any(t in text for t in PLANT_TOKENS + ids.get('svTokens', []))
                on_decoy = any(t in text for t in DECOY_TOKENS)
                if on_decoy and v['check'] not in DECOY_OK: fp.append(f'{r} {v["check"]}: {v["what"]}'); per_role[r]['fp'] += 1
                elif not on_plant and not on_decoy: fp.append(f'{r} {v["check"]}: {v["what"]} (names no planted record)'); per_role[r]['fp'] += 1
                elif on_plant and not any(v['check'] == e[2] and r in e[1] for e in EXPECT): side.append(f'{r} {v["check"]}: {v["what"]}')
        recall = found / total
        tp_all = sum(len(new[r]) for r, _ in ROLES) - len(fp)
        precision = tp_all / max(1, tp_all + len(fp))
        print(f'BANK recall {found}/{total} = {recall:.0%} · precision {tp_all}/{tp_all + len(fp)} = {precision:.0%} · right fix {found - len(wrongfix)}/{found}')
        for r, _ in ROLES:
            x = per_role[r]
            print(f'  {r:<10} found {x["tp"]}/{x["exp"]} planted · {x["fp"]} false alarms · {x["new"]} new findings')
        for s in side: print('  side (true, on a planted record):', s)
        for m in missed: flag('missed ' + m)
        for m in wrongfix: flag('wrong fix ' + m)
        for m in fp: flag('false alarm ' + m)
        # the clean month: decoys alone raised nothing outside bank-line hygiene
        clean = [k for r, _ in ROLES for k, v in new[r].items() if any(t in k + v['what'] + v['sub'] for t in DECOY_TOKENS) and v['check'] not in DECOY_OK]
        clean and flag(f'clean month: decoys raised {clean}')

        # a line's count is its source's rows (one question, one number)
        cnt = await pg.evaluate("""() => { signIn('u_controller'); render.__tick++; const L = rsChecklist('controller'), n = (id) => (L.find(x => x.check.id === id) || {}).n;
          return { overPO: [n('c.overPO'), CATCH.find(c => c.name === 'overPO').rows().length], earned: [n('c.earned'), CATCH.find(c => c.name === 'earnedNotBilled').rows().length],
                   unmatched: [n('c.unmatched'), PRED.unmatchedTxns.rows().length], disc: [n('c.discount'), PRED.discountsAtRisk.rows().length], recon: [n('c.recon'), standardRuleRows(STANDARD_RULES.find(r => r.id === 'books10')).length] }; }""")
        for k, (a, b2) in cnt.items():
            a != b2 and flag(f'count: the checklist line {k} reads {a}, its source shows {b2}')

        # ---------------------------------------------------------------- six steps, as the people do it
        # the controller opens the over-PO finding: the rule, the evidence, the cause from the records, a mail only
        # the coordinator can read is not shown to the controller
        await pg.evaluate("""() => { DB.comms.push({ id: 'cmPLANTCHEN', owner: 'u_chen', channel: 'email', direction: 'in', from: { name: 'Plantwood Supply', email: 'orders@plantwood.example' }, to: [], cc: [], date: '2026-09-01T10:00:00', subject: 'PLANT-OVERPO: the two extra sheets', text: 'Private to Chen', status: 'new', proposals: [], links: [] },
                                                          { id: 'cmPLANTFIRM', channel: 'email', direction: 'in', from: { name: 'Plantwood Supply', email: 'orders@plantwood.example' }, to: [], cc: [], date: '2026-09-01T11:00:00', subject: 'Plantwood Supply statement', text: '', status: 'new', proposals: [], links: [] }); save(); }""")
        six = await pg.evaluate("""() => { signIn('u_controller'); const X = rsSix('c.overPO|bill:bPLANTOVER');
          return { why: X.rule.why, leak: X.rule.leak, ev: X.evidence.map(e => e.label), cause: X.cause.lines, mail: X.cause.mail.map(m => m.line), owner: X.owner, fix: X.fix.kind, rec: X.fix.rec, opts: X.fix.options.length }; }""")
        'Because:' in six['why'] or flag('six: no rule cited ' + six['why'])
        six['leak'] or flag('six: a money leak does not say why money matters')
        any('PLANT-OVERPO' in e for e in six['ev']) and any('PO-PLANT-OVER' in e for e in six['ev']) or flag(f'six: evidence misses the bill or PO {six["ev"]}')
        any('12 sheets' in c for c in six['cause']) or flag(f'six: the cause does not read the bill note {six["cause"]}')
        any('PO-PLANT-OVER' in c and '$5,000' in c for c in six['cause']) or flag(f'six: the cause does not compare bill and PO {six["cause"]}')
        any('statement' in m for m in six['mail']) or flag(f'six: the firm inbox mail is not in the cause {six["mail"]}')
        any('two extra sheets' in m for m in six['mail']) and flag('privacy: the controller reads Chen\'s private mail through a finding')
        six['owner']['name'] == 'Owner' or flag(f'six: a short-pay is the owner\'s; task went to {six["owner"]}')
        six['opts'] >= 2 or flag('six: fewer than two options')
        chen = await pg.evaluate("() => { signIn('u_chen'); return rsSix('c.overPO|bill:bPLANTOVER').cause.mail.map(m => m.line); }")
        any('two extra sheets' in m for m in chen) or flag(f'privacy: Chen does not see her own mail in the cause {chen}')

        # the owner approves the fix: a credit-memo request drafted on Approvals, the short-pay sheet opens
        r = await pg.evaluate("""() => { signIn('u_owner'); render(); rsApprove('c.overPO|bill:bPLANTOVER');
          const d = DB.outbox.find(o => o.aboutKey === 'sp|c.overPO|bill:bPLANTOVER'), m = document.getElementById('mbm');
          const c = DB.specialist.cases['c.overPO|bill:bPLANTOVER'];
          render.__tick = (render.__tick || 0) + 1; const AL = mApprovals({ everyone: true }).filter(it => it.kind === 'draft'), appr = AL.some(it => it.id === (d || {}).id && it.who === 'owner'), dbg = AL.map(it => it.id + ':' + it.who).concat([(d || {}).id]);
          return { draft: d ? { status: d.status, to: d.to.email, subject: d.subject, forName: d.forName } : null, sheet: m ? m.innerText.slice(0, 120) : '', fix: c && c.fix && c.fix.kind, appr, dbg, toast: (document.getElementById('toast') || {}).innerText || '' }; }""")
        r['draft'] and r['draft']['status'] == 'draft' and 'plantwood' in r['draft']['to'] or flag(f'six: no credit-memo draft to the vendor {r}')
        r['appr'] or flag(f'six: the drafted request is not on the owner\'s Approvals {r}')
        r['fix'] == 'shortpay' or flag(f'six: the case does not record the approved fix {r}')
        'Plantwood' in r['sheet'] or flag(f'six: the short-pay sheet did not open {r["sheet"]}')
        # the owner short-pays it to the PO: the record is fixed, the follow-up closes the case, the ledger shows it
        r = await pg.evaluate("""() => { mbCloseModal(); signIn('u_owner'); const b = DB.bills.find(x => x.id === 'bPLANTOVER');
          const ok = pay3ShortPay(b, 5000, 'Billed 12 sheets on a PO for 10; credit memo requested'); render.__tick++;
          const n = rsSweep(); const c = DB.specialist.cases['c.overPO|bill:bPLANTOVER'];
          const sv = svRows().find(x => x.key === 'short:bPLANTOVER');
          return { ok: !!ok, n, status: c.status, sv: sv ? { amount: sv.amount, by: sv.by, source: sv.source } : null }; }""")
        r['status'] == 'fixed' or flag(f'follow-up: the over-PO case did not close when the record was fixed {r}')
        r['sv'] and abs(r['sv']['amount'] - 600) < 0.005 and r['sv']['source'] == 'Overpayments Stopped' or flag(f'savings: the short-pay is not on the ledger as $600.00 {r}')

        # ticked, not fixed: the discount task is ticked; the record still shows it; the task reopens
        r = await pg.evaluate("""() => { signIn('u_controller'); const f = rsFinding('c.discount|disc:bPLANTDISC'); const T = rsTask(f, rsFix(f)); save();
          const rec = rsTaskRec(T); const own = T.owner, due = T.due, onList = tkAll({ open: true }).some(t => t.id === T.id && t.owner === own);
          rec.status = 'done'; rec.completedAt = today(); rsSweep(); const c = DB.specialist.cases['c.discount|disc:bPLANTDISC'];
          return { own, due, onList, reopened: c.reopened || 0, recStatus: rec.status, follow: rsSix('c.discount|disc:bPLANTDISC').follow }; }""")
        r['own'] == 'Controller' or flag(f'task: the discount went to {r["own"]}, not the controller')
        r['onList'] or flag('task: the made task is not findable on the person\'s list (tkAll)')
        r['reopened'] == 1 and r['recStatus'] == 'todo' or flag(f'follow-up: a ticked task on an unfixed record did not reopen {r}')
        'Reopened' in r['follow'] or flag(f'follow-up: the sheet does not say it reopened {r["follow"]}')

        # learning: a dismissal needs a reason and is never raised again in that form
        kmat = [k for k, v in new['coord'].items() if v['check'] == 'p.materials' and 'PLANT' in v['what']]
        r = await pg.evaluate("""(k) => { signIn('u_chen');
          const refused = rsDismiss(k, '') === false; const ok = rsDismiss(k, 'Bought from stock: the valves are in the van');
          render.__tick++; const still = rsFindings('coord').some(f => f.key === k); signIn('u_alan'); const pm = rsFindings('pm').some(f => f.key === k);
          return { refused, ok, still, pm }; }""", kmat[0] if kmat else '')
        r['refused'] or flag('learn: a dismissal with no reason was accepted')
        r['ok'] and not r['still'] and not r['pm'] or flag(f'learn: a dismissed finding came back {r}')
        # an approved COI request becomes a proposed default; once the owner approves it, the next one drafts itself
        r = await pg.evaluate("""() => { signIn('u_controller'); rsApprove('c.papers|vblock:vLAPSED'); const ch = DB.changes.find(c => c.key === 'sp:default:c.papers');
          const d1 = DB.outbox.find(o => o.aboutKey === 'sp|c.papers|vblock:vLAPSED');
          signIn('u_owner'); ch && (mtChangeApply(ch), ch.status = 'live');
          DB.vendors.push({ id: 'vLAPSED2', name: 'Second Lapsed Roofing', insuranceExp: '2026-07-01', email: 'x@second.example' });
          DB.pos.push(Object.assign(JSON.parse(JSON.stringify(DB.pos.find(p => p.id === 'poPLANTCOI'))), { id: 'poPLANTCOI2', number: 'PO-PLANT-COI2', vendor: 'Second Lapsed Roofing' }));
          render.__tick++; const n = rsAutoDrafts(); const d2 = DB.outbox.find(o => o.aboutKey === 'sp|c.papers|vblock:vLAPSED2');
          return { proposed: !!ch, kind: ch && ch.kind, path: ch && ch.delta.path, d1: !!d1, n, d2: d2 ? d2.status : null, on: !!(DB.company.spDefaults || {})['c_papers'] }; }""")
        r['d1'] or flag('learn: the approved COI request was not drafted')
        r['proposed'] and r['path'] == 'company.spDefaults.c_papers' or flag(f'learn: no default proposed under Company › Changes {r}')
        r['on'] and r['d2'] == 'draft' or flag(f'learn: the owner-approved default did not draft the next COI request {r}')

        # ---------------------------------------------------------------- thresholds
        r = await pg.evaluate("""() => { signIn('u_owner'); const R3 = () => standardRuleRows(STANDARD_RULES.find(r => r.id === 'threeQuotes')).length;
          const n0 = R3(); const ch = rsThresholdPropose('threeQuotes', 10000, 'Small orders were waiting on quotes'); const n1 = R3();
          mtChangeApply(ch); ch.status = 'live'; const n2 = R3();
          const sub = standardRuleRows(STANDARD_RULES.find(r => r.id === 'threeQuotes')).some(x => /subcontract/.test(x.sub));
          DB.company.spThresholds.threeQuotes = 2500;
          const esc = nyhRows({ everyone: true }).filter(x => x.route === 'owner' && /^std:unb:/.test(x.key)).map(x => x.key);
          const p = DB.projects.find(x => x.id === 'p121'), t = p.tasks.find(x => x.type === 'milestone');
          const keep = [t.end]; t.end = iso(addDays(t.origEnd, 7)); const slip = rsSlipRows().map(x => x.key); t.end = iso(addDays(t.origEnd, 1)); const slip1 = rsSlipRows().length; t.end = keep[0];
          return { n0, n1, n2, draft: ch.status, sub, esc, slip, slip1, fmt: standardEscalationText({ what: 'Not in the budget', amount: 2400, src: 'std:unbudgeted1k' }) }; }""")
        r['n0'] == r['n1'] or flag('thresholds: a drafted change moved the count before approval')
        r['n2'] < r['n0'] or flag(f'thresholds: approving $10,000 did not lower the three-quote count {r}')
        r['sub'] or flag('thresholds: a subcontract under three quotes is not counted at any amount')
        any('bPLANTUNB' in k for k in r['esc']) or flag(f'escalation: the unbudgeted $2,400 is not on the owner\'s Needs Your Hand {r["esc"]}')
        r['slip'] and r['slip1'] == 0 or flag(f'escalation: milestone slip over 2 working days {r}')
        all(any(s in l for l in r['fmt']) for s in ('What happened', 'Impact', 'Options', 'Recommendation', 'Decision needed by')) or flag(f'escalation: not in the Standard\'s format {r["fmt"]}')
        r = await pg.evaluate("""() => { signIn('u_alan'); const n0 = standardRuleRows(STANDARD_RULES.find(r => r.id === 'fridayUpdate')).length;
          const made = rsFridaySweep(true); const d = DB.outbox.filter(o => o.kind === 'clientUpdate' && o.status === 'draft');
          const n1 = standardRuleRows(STANDARD_RULES.find(r => r.id === 'fridayUpdate')).length;
          const onAppr = tkAll({ open: true }).filter(t => t.approval && d.some(o => o.id === t.id)).map(t => t.owner);
          const ack = standardRuleRows(STANDARD_RULES.find(r => r.id === 'clientAck')).map(x => x.key);
          return { made, n0, n1, onAppr, body: d[0] ? d[0].body.slice(0, 300) : '', ack }; }""")
        r['made'] >= 1 or flag('friday: no update drafted')
        r['n1'] == r['n0'] or flag('friday: a draft counted as an update sent')
        r['onAppr'] and all(o == 'Alan' for o in r['onAppr']) or flag(f'friday: the drafts are not on the PM\'s list {r["onAppr"]}')
        'This week' in r['body'] or flag(f'friday: the draft does not read the week {r["body"]}')
        'cq:cqPLANT' in r['ack'] and 'cq:cqDECOY' not in r['ack'] or flag(f'client acknowledgement: 2 business hours {r["ack"]}')
        r = await pg.evaluate("""() => { signIn('u_owner'); const po = Object.assign(JSON.parse(JSON.stringify(DB.pos.find(p => p.id === 'poPLANTCOI'))), { id: 'poPLANTSUB', number: 'PO-PLANT-SUB', vendor: 'Plantwood Supply', status: 'draft', type: 'subcontract', sc: { scope: 'Planted scope' } });
          DB.pos.push(po); try { poAction(po, 'issue'); } catch (e) {} mbCloseModal(); return { status: po.status, q3: po.q3 || null }; }""")
        r['status'] != 'issued' or r['q3'] or flag(f'thresholds: a subcontract issued under three quotes is not recorded on the PO {r}')

        # ---------------------------------------------------------------- savings
        r = await pg.evaluate("""() => { signIn('u_owner'); const t = DB.txns.find(x => x.id === 'tPLANTDUP2');
          t.dispute = { why: 'Charged twice', by: 'Controller', at: appNowIso(), with: 'Amex', amt: t.amt }; t.dupState = 'disputed';
          window.SV_SOURCES.push(() => [{ key: 'pb:test', kind: 'price', amount: 84, date: today(), by: 'Alex', what: 'PEX at the cheaper store', evidence: ['receipt'] }]);
          const ok = svSetShare({ wage: 20, bonus: 10, charity: 5 }); const bad = svSetShare({ wage: 90, bonus: 20, charity: 0 });
          const V = svSummary(); svCredit('short:bPLANTOVER', 'Owner'); const V2 = svSummary();
          const eqO = eqRows('savings').length; signIn('u_angel'); const eqF = eqRows('savings').length; signIn('u_alan'); const eqP = eqRows('savings').length;
          return { ytd: V.ytd, bySource: V.bySource, pools: V.pools, ok, bad, credited: V2.credited, eqO, eqF, eqP }; }""")
        r['bySource'].get('Duplicates Stopped', 0) >= 742.18 or flag(f'savings: the disputed duplicate is not counted {r["bySource"]}')
        r['bySource'].get('Price Differences', 0) >= 84 or flag('savings: another lane\'s SV_SOURCES row is not read')
        r['ok'] and not r['bad'] or flag('savings: shares over 100% were accepted')
        abs(r['pools']['charity'] - round(r['ytd'] * 0.05, 2)) < 0.02 or flag(f'savings: the charity pool is not 5% of the year {r}')
        r['credited'].get('Owner', 0) >= 600 or flag(f'savings: the bonus credit was not recorded {r["credited"]}')
        r['eqO'] > 0 and r['eqF'] == 0 or flag(f'savings: Ask reads {r["eqO"]} rows as the owner, {r["eqF"]} as the foreman')
        print(f'SAVINGS ytd ${r["ytd"]:,.2f} · {r["bySource"]}')

        # ---------------------------------------------------------------- workload
        r = await pg.evaluate("""() => { signIn('u_owner'); const W = PRED.peopleOverloaded.rows(); const w = W.find(x => x.u.role === 'owner');
          if (!w || !w.move) return { W: W.map(x => x.what) };
          const k = 'o.overload|' + w.key, X = rsSix(k);
          signIn('u_billing'); const refused = wlApply(w) === 0;
          signIn('u_owner'); rsApprove(k);
          const offered = w.move.tasks.map(t => { const rec = tdyRec(t); return rec && rec.handoff ? rec.handoff.state + ':' + rec.handoff.to : 'none'; });
          const eq = eqRows('workload').find(x => x.person === 'Owner'); signIn('u_alberto'); const eqCrew = eqRows('workload').length;
          return { to: w.move.to.name, n: w.move.tasks.length, fix: X.fix.kind, refused, offered, eq: eq ? eq.overloaded : null, eqCrew }; }""")
        r.get('fix') == 'moveWork' or flag(f'workload: no move proposed for the overloaded owner {r}')
        r.get('refused') or flag('workload: someone other than the manager moved the work')
        r.get('offered') and all(o.startswith('offered:') for o in r['offered']) or flag(f'workload: the tasks were not offered {r}')
        r.get('eqCrew') == 0 or flag('workload: crew read the workload table')
        print(f'WORKLOAD {r}')

        # ---------------------------------------------------------------- privacy: field roles read no money
        r = await pg.evaluate("""() => { signIn('u_angel'); render.__tick++; const F = rsFindings('foreman'), L = rsChecklist('foreman');
          const money = F.filter(f => /\\$\\d/.test(f.what + ' ' + f.sub) || f.amount > 0).map(f => f.what);
          const X = rsChecklist('controller'); const leak = X.flatMap(x => x.rows).filter(f => /\\$\\d/.test(f.what + ' ' + f.sub) || f.amount > 0).length;
          const eq = eqRows('checklist'); const eqMoney = eq.some(x => 'amount' in x);
          const six = F[0] ? rsSix(F[0].key) : null; const sixMoney = six ? /\\$\\d/.test(JSON.stringify([six.cause.lines, six.evidence.map(e => e.label), six.f.what, six.f.sub])) : false;
          const mail = six ? six.cause.mail.length : 0;
          signIn('u_klein'); const cl = eqRows('checklist').length + eqRows('savings').length + eqRows('workload').length;
          return { n: F.length, lines: L.map(x => x.check.id), money, leak, eqMoney, sixMoney, mail, cl }; }""")
        r['n'] > 0 or flag('privacy: the foreman has no checklist findings to check')
        r['money'] and flag(f'privacy: the foreman reads money {r["money"]}')
        r['leak'] and flag(f'privacy: the controller\'s lines read by the foreman carry {r["leak"]} amounts')
        r['eqMoney'] and flag('privacy: Ask\'s checklist table gives the foreman amounts')
        r['sixMoney'] and flag('privacy: the six steps show the foreman money')
        r['mail'] and flag('privacy: the foreman reads mail through a finding')
        r['cl'] and flag(f'privacy: the client reads {r["cl"]} specialist rows')

        # ---------------------------------------------------------------- screens: Home one-liner, Findings, the sheet
        for uid, view, want in [('u_alan', 'home', 'Think three weeks ahead'), ('u_controller', 'home', 'Accurate, on time'), ('u_owner', 'home', 'Everything you touch'), ('u_chen', 'home', 'Best total price'), ('u_angel', 'ftoday', 'el trabajo se hace bien')]:
            if uid == 'u_angel':
                await pg.evaluate("() => { const u = DB.users.find(x => x.id === 'u_angel'); u.lang = 'es'; save(); }")
            await sign_in(pg, uid); await go(pg, view)
            t = await pg.evaluate("() => { const e = document.querySelector('.view.on .rs-one'); return e ? e.textContent : ''; }")
            want.lower() in t.lower() or flag(f'one-liner: {uid} on {view} reads "{t}", expected "{want}"')
            if uid == 'u_angel':
                await pg.evaluate("() => { const u = DB.users.find(x => x.id === 'u_angel'); u.lang = 'en'; save(); }")
                await go(pg, view)
                t = await pg.evaluate("() => { const e = document.querySelector('.view.on .rs-one'); return e ? e.textContent : ''; }")
                'work gets done right' in t.lower() or 'right' in t.lower() or flag(f'one-liner: the foreman in English reads "{t}"')
        await sign_in(pg, 'u_controller'); await go(pg, 'pa')
        await pg.evaluate("() => paOpen('findings', 'check')"); await pg.wait_for_timeout(300)
        r = await pg.evaluate("""() => { const v = document.querySelector('.rs-pane'); if (!v) return null;
          const line = v.querySelector('[data-rsline="c.overPO"] [data-rsn]'), seg = [...document.querySelectorAll('[data-paseg]')].map(b => b.textContent);
          return { lines: v.querySelectorAll('.rs-line').length, overPO: line ? +line.dataset.rsn : -1, src: CATCH.find(c => c.name === 'overPO').rows().length, seg, primary: document.querySelectorAll('.view.on .btn.primary').length }; }""")
        if not r: flag('screens: the Checklist segment did not draw')
        else:
            r['overPO'] == r['src'] or flag(f'screens: the line shows {r["overPO"]}, Caught for You {r["src"]}')
            'Checklist' in r['seg'] or flag(f'screens: no Checklist segment {r["seg"]}')
            r['primary'] <= 1 or flag(f'screens: {r["primary"]} blue buttons on the checklist')
        await pg.screenshot(path=os.path.join(SHOTS, 'checklist_controller_desktop.png'), full_page=False)
        await pg.evaluate("() => rsSheet('c.discount|disc:bPLANTDISC')"); await pg.wait_for_timeout(200)
        r = await pg.evaluate("() => { const m = document.getElementById('mbm'); return m ? { steps: m.querySelectorAll('.rs-step').length, primary: m.querySelectorAll('.btn.primary').length, text: m.innerText.slice(0, 200) } : null; }")
        r and r['steps'] == 6 and r['primary'] == 1 or flag(f'screens: the six-step sheet {r}')
        await pg.screenshot(path=os.path.join(SHOTS, 'six_steps_desktop.png'), full_page=False)
        await pg.evaluate("() => mbCloseModal()")
        await sign_in(pg, 'u_owner'); await go(pg, 'pa')
        await pg.evaluate("() => { rsView = 'owner'; paOpen('findings', 'check'); }"); await pg.wait_for_timeout(300)
        r = await pg.evaluate("() => ({ sv: !!document.querySelector('.sv-card'), wl: !!document.querySelector('.wl-card'), roles: document.querySelectorAll('[data-rsrole]').length })")
        r['sv'] and r['wl'] and r['roles'] >= 6 or flag(f'screens: the founder\'s checklist lacks the ledger, workload or the role picker {r}')
        await pg.screenshot(path=os.path.join(SHOTS, 'checklist_founder_desktop.png'), full_page=True)
        await b.close()

        # phone: the PM's checklist and a sheet, no sideways scroll, 44px targets
        b, pg, errs2 = await open_app(p, phone=True)
        await pg.evaluate(PLANT)
        for uid in ('u_alan', 'u_angel', 'u_owner'):
            await sign_in(pg, uid); await go(pg, 'pa')
            await pg.evaluate("() => paOpen('findings', 'check')"); await pg.wait_for_timeout(300)
            r = await pg.evaluate("""() => ({ sw: document.documentElement.scrollWidth, w: innerWidth, pane: !!document.querySelector('.rs-pane'),
              small: [...document.querySelectorAll('.rs-pane .btn')].filter(b => b.getClientRects().length && b.getBoundingClientRect().height < 43.5).length })""")
            r['pane'] or flag(f'phone: {uid} has no checklist')
            r['sw'] <= r['w'] + 1 or flag(f'phone: {uid} checklist scrolls sideways ({r["sw"]} > {r["w"]})')
            r['small'] and flag(f'phone: {uid} has {r["small"]} buttons under 44px')
            await pg.screenshot(path=os.path.join(SHOTS, f'checklist_{uid}_phone.png'), full_page=False)
        await sign_in(pg, 'u_alan'); await go(pg, 'pa'); await pg.evaluate("() => paOpen('findings', 'check')"); await pg.wait_for_timeout(200)
        await pg.evaluate("() => rsSheet('p.client|cq:cqPLANT')"); await pg.wait_for_timeout(200)
        r = await pg.evaluate("() => ({ sw: document.documentElement.scrollWidth, w: innerWidth, m: !!document.getElementById('mbm') })")
        r['m'] and r['sw'] <= r['w'] + 1 or flag(f'phone: the six-step sheet {r}')
        await pg.screenshot(path=os.path.join(SHOTS, 'six_steps_pm_phone.png'), full_page=False)
        await sign_in(pg, 'u_alan'); await go(pg, 'home')
        await pg.screenshot(path=os.path.join(SHOTS, 'home_pm_phone.png'), full_page=False)
        await b.close()
        for e in errs + errs2: flag('page error: ' + e)
    print(f'{len(flags)} flags')
    return 1 if flags else 0

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
