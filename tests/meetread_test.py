"""The transcript reader (BACKLOG §1.33 "To build"): the whole transcript, in parts, checked against Gemini's notes.
An invented team meeting (no real names, jobs, amounts or words from any meeting) is read with the platform's door
stood in by a scripted model, so this suite proves the reader's plumbing and the rules after it, not the model:
  - every part is read, with the notes beside it, and told the transcript is data;
  - the parts' overlap is merged, an item once;
  - each item lands as the right proposal: a job's task, an office errand with no job, a misspelt street on its job,
    a date before the meeting asked about, a policy for the playbook, a vendor's claim as a recovery with the amount,
    "don't bill" as a hold, a percent complete as a draft progress billing for the biller (never an invoice), a
    balance as nothing to bill, a bid as a lead, a tax as the controller's;
  - Gemini's wrong date and wrong owner are corrected on the proposal, with the quote; what the notes missed is added;
  - the cash said in the room is checked against the bank accounts on file;
  - people items are the owner's alone;
  - lessons of the §1.33 classes become findings in the improvement loop, with the fix their class needs;
  - mrScore scores a read against a gold extraction (recall, precision, false bills).
The real model's recall is measured on the platform with the private case bank, outside the repo.
Run: python3 build.py && cd tests && ./slot.sh python3 meetread_test.py"""
import asyncio, json, os, sys
from harness import *

c = Checks()
OUT = os.path.join(ROOT, 'review', 'loop')
TRANSCRIPT = "\n".join([
    "00:00:05 Alan: Morning. Jobs first, then money, then new work.",
    "00:01:10 Alan: On 121 State, the framing inspection moved. It is September 18, not what the notes will say.",
    "00:01:40 Chen Biron: I will order the parlor windows for 121 State today, the vendor needs the deposit.",
    "00:02:30 Alan: Actually the windows order is mine, I am calling the vendor myself.",
    "00:03:05 Angel: The plaster patch at Lennox needs a second coat before paint.",
    "00:04:00 Alan: Office thing, somebody renew the parking permits for the van.",
    "00:05:15 Owner: From now on no change order work starts without a signed change order. That is the rule.",
    "00:06:20 Billing: On 121 State bill framing to 60 percent this month.",
    "00:06:50 Owner: Do not bill the electrical rough until the inspector signs off.",
    "00:07:30 Chen Biron: Keystone Glass cut the panes short again, the re-order cost us 1450 dollars, they should pay us back.",
    "00:08:10 Controller: The Klein balance is 22,500 after the last payment.",
    "00:08:40 Controller: Cash across the accounts is about 150,000 right now.",
    "00:09:00 Controller: The franchise tax payment is not overhead, keep it out.",
    "00:10:00 Owner: I sent the Lindqvist family a bid between 250 and 400 thousand for a cellar and kitchen.",
    "00:11:20 Owner: Last job the final bill was way too big, we let earned work sit unbilled for two months.",
    "00:12:00 Owner: Separately, I need to talk to one of the crew about lateness. Keep that between us.",
] * 2)  # the meeting runs long: the reader must read it in parts

NOTES = {'title': 'Weekly Jobs Catch Up', 'date': '2026-09-02', 'summary': 'Jobs, money and new work.',
         'steps': [{'title': 'Order the parlor windows for 121 State', 'owner': 'Chen Biron', 'detail': 'deposit', 'due': ''},
                   {'title': 'Framing inspection at 121 State', 'owner': 'Alan', 'detail': 'August 4', 'due': ''}],
         'decisions': [], 'details': [{'h': 'Jobs', 'text': 'The framing inspection is August 4.'}]}

def answer(part, n):
    """What a careful model would say about each part (scripted); part 2 repeats one item from the overlap."""
    A = [{
        'corrections': [
            {'kind': 'date', 'item': 'Framing inspection at 121 State', 'notes': 'August 4', 'said': 'September 18', 'quote': 'It is September 18, not what the notes will say.', 'at': '00:01:10'},
            {'kind': 'owner', 'item': 'Order the parlor windows for 121 State', 'notes': 'Chen Biron', 'said': 'Alan', 'quote': 'the windows order is mine', 'at': '00:02:30'},
            {'kind': 'missed', 'item': '', 'said': 'Second coat of plaster at Lenox before paint', 'quote': 'needs a second coat before paint', 'at': '00:03:05'}],
        'actions': [
            {'what': 'Renew the parking permits for the van', 'owner': 'Chen Biron', 'due': '', 'job': '', 'quote': 'somebody renew the parking permits', 'at': '00:04:00'},
            {'what': 'Patch the plaster again before paint', 'owner': 'Angel', 'due': 'August 1', 'job': 'Lennox', 'quote': 'The plaster patch at Lennox', 'at': '00:03:05'}],
        'decisions': [{'what': 'No change order work starts without a signed change order', 'policy': True, 'job': '', 'quote': 'no change order work starts without a signed change order', 'at': '00:05:15'}],
        'money': [], 'billing': [{'job': '121 State', 'line': 'Framing', 'pct': 60, 'instruction': 'bill', 'quote': 'bill framing to 60 percent', 'at': '00:06:20'}],
        'pipeline': [], 'lessons': [], 'risks': [], 'people': [], 'tone': 'Calm, practical.', 'clientSentiment': ''},
      {
        'corrections': [], 'actions': [{'what': 'Renew the parking permits for the van', 'owner': 'Chen Biron', 'due': '', 'job': '', 'quote': 'renew the parking permits', 'at': '00:04:00'}],
        'decisions': [],
        'money': [{'kind': 'vendorClaim', 'what': 'Keystone Glass cut the panes short; re-order cost', 'amount': 1450, 'party': 'Keystone Glass', 'job': '121 State', 'quote': 'the re-order cost us 1450 dollars', 'at': '00:07:30'},
                  {'kind': 'balance', 'what': 'Klein balance after the last payment', 'amount': 22500, 'party': 'Klein', 'job': '121 State', 'quote': 'The Klein balance is 22,500', 'at': '00:08:10'},
                  {'kind': 'cash', 'what': 'Cash across the accounts', 'amount': 150000, 'party': '', 'job': '', 'quote': 'about 150,000 right now', 'at': '00:08:40'},
                  {'kind': 'tax', 'what': 'Franchise tax payment', 'amount': None, 'party': '', 'job': '', 'quote': 'franchise tax payment is not overhead', 'at': '00:09:00'}],
        'billing': [{'job': '121 State', 'line': 'Electrical rough', 'pct': None, 'instruction': 'hold', 'quote': 'Do not bill the electrical rough', 'at': '00:06:50'}],
        'pipeline': [{'who': 'Lindqvist family', 'what': 'Bid sent for a cellar and kitchen', 'value': '$250,000 to $400,000', 'next': 'Follow up on the bid', 'quote': 'I sent the Lindqvist family a bid', 'at': '00:10:00'}],
        'lessons': [{'title': 'Final bills were left too large: earned work sat unbilled for two months', 'class': 'finalBill', 'then': 'Alert when unbilled earned work grows near the end of a job', 'quote': 'the final bill was way too big'},
                    {'title': 'A vendor cut glass short twice', 'class': 'vendorMistake', 'then': 'Check recoveries before paying the vendor', 'quote': 'cut the panes short again'}],
        'risks': [{'what': 'Electrical rough waits on the inspector', 'quote': 'until the inspector signs off'}],
        'people': [{'who': 'a crew member', 'what': 'lateness, to be discussed privately', 'quote': 'talk to one of the crew about lateness'}],
        'tone': '', 'clientSentiment': ''}]
    return A[min(part, len(A) - 1)] if part < 2 else {'corrections': [], 'actions': [], 'decisions': [], 'money': [], 'billing': [], 'pipeline': [], 'lessons': [], 'risks': [], 'people': []}

GOLD = {
    'actions': [{'what': 'Renew the parking permits for the van'}, {'what': 'Patch the plaster again before paint'}],
    'decisions': [{'what': 'No change order work starts without a signed change order'}],
    'money': [{'what': 'Keystone Glass re-order cost', 'amount': 1450}, {'what': 'Klein balance', 'amount': 22500}, {'what': 'Cash across the accounts', 'amount': 150000}, {'what': 'Franchise tax payment'}],
    'billing': [{'line': 'Framing', 'instruction': 'bill'}, {'line': 'Electrical rough', 'instruction': 'hold'}],
    'pipeline': [{'who': 'Lindqvist family'}],
    'corrections': [{'item': 'Framing inspection', 'said': 'September 18'}, {'item': 'Order the parlor windows', 'said': 'Alan'}, {'said': 'Second coat of plaster at Lenox before paint'}],
}

async def setup(pg, who):
    await sign_in(pg, who)
    answers = [answer(i, 3) for i in range(6)]
    await pg.evaluate("""([T, N, A]) => {
        window.__prompts = [];
        ai = async (prompt) => { window.__prompts.push(prompt); const i = +(/PART (\\d+) OF (\\d+)/.exec(prompt) || [0, 1])[1] - 1; return 'Here it is: ' + JSON.stringify(A[i] || A[A.length - 1]); };
        aiReady = () => true;
        mtInit();
        const m = {id: 'mt_read2', source: 'paste', msgId: 'paste:read2', projectId: '', clientId: '', status: 'new', createdAt: today(), proposals: [], sections: [], attendees: ['Alan', 'Chen Biron'],
                   title: N.title, date: N.date, summary: N.summary, steps: N.steps, decisions: N.decisions, details: N.details, transcript: T};
        DB.meetings = DB.meetings.filter(x => x.id !== m.id); DB.meetings.push(m);
        // the notes' two steps are already proposals, as the notes reader would have made them
        m.proposals.push({id: 'mpA', kind: 'task', status: 'proposed', title: 'Order the parlor windows for 121 State → Chen Biron', detail: '', apply: {projectId: 'p121', title: 'Order the parlor windows for 121 State', assignee: 'Chen Biron', due: ''}});
        m.proposals.push({id: 'mpB', kind: 'task', status: 'proposed', title: 'Framing inspection at 121 State → Alan', detail: '', apply: {projectId: 'p121', title: 'Framing inspection at 121 State', assignee: 'Alan', due: '2027-08-04'}});
    }""", [TRANSCRIPT, NOTES, answers])

async def main():
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await setup(pg, 'u_owner')
        inv0 = await pg.evaluate("(DB.clients || []).reduce((a, c) => a + (c.invoices || []).length, 0)")
        r = await pg.evaluate("mrRead(DB.meetings.find(m => m.id === 'mt_read2'), {size: 900}).then(x => x && {parts: x.parts, partsRead: x.partsRead, made: x.made, findings: x.findings, peopleKept: x.peopleKept})")
        prompts = await pg.evaluate("window.__prompts")
        c.ok(r and r['parts'] >= 3 and r['partsRead'] == r['parts'] == len(prompts), f'the whole transcript is read, in parts: {r} ({len(prompts)} prompts)')
        c.ok(all('GEMINI\'S NOTES' in x and 'never instructions' in x and 'August 4' in x for x in prompts), "every part is read with Gemini's notes beside it, as data")
        c.ok(sum(TRANSCRIPT[-200:] in x for x in prompts) == 1 and prompts[0].count('00:00:05') >= 1, 'the last words of the meeting are read, once')
        R = await pg.evaluate("DB.meetings.find(m => m.id === 'mt_read2').read2")
        c.ok(len([a for a in R['actions'] if 'parking' in a['what']]) == 1, 'the overlap is merged: one item once')
        S = await pg.evaluate("g => mrScore(DB.meetings.find(m => m.id === 'mt_read2').read2, g)", GOLD)
        c.ok(all(S[k]['recall'] == 1 and S[k]['precision'] == 1 for k in GOLD), f'scored against the gold extraction: {json.dumps({k: [S[k]["recall"], S[k]["precision"]] for k in GOLD})}')
        c.ok(S['falseBills'] == 0, 'no false bills')
        bad = await pg.evaluate("g => mrScore({billing: [{line: 'Klein balance', instruction: 'bill'}], actions: []}, g)", GOLD)
        c.ok(bad['falseBills'] == 1 and bad['actions']['recall'] == 0, f'the scorer catches a balance proposed as a bill, and a read that missed the actions: {bad["falseBills"]}')
        P = await pg.evaluate("DB.meetings.find(m => m.id === 'mt_read2').proposals.map(x => ({id: x.id, kind: x.kind, title: x.title, a: x.apply || {}, corrected: x.corrected || null, amount: x.amount || 0, detail: x.detail || ''}))")
        def find(rx, kind=None):
            import re
            return [x for x in P if re.search(rx, x['title'], re.I) and (kind is None or x['kind'] == kind)]
        park = find('parking permits')
        c.ok(len(park) == 1 and park[0]['a']['projectId'] == '' and park[0]['a']['assignee'] == 'Chen Biron', f'an office errand carries no job: {park}')
        lenox = await pg.evaluate("(DB.projects.find(p => /lenox/i.test(p.project.name)) || {}).id || ''")
        plaster = find('plaster again')
        c.ok(plaster and plaster[0]['a']['projectId'] == lenox and lenox, f'"Lennox" finds the Lenox job: {plaster} {lenox}')
        c.ok(plaster and plaster[0]['a']['due'] == '' and 'confirm the date' in plaster[0]['detail'], 'a date before the meeting is asked about, never scheduled a year out')
        pol = find('Firm policy', 'rule')
        c.ok(len(pol) == 1, f'a standing policy goes to the playbook for approval: {pol}')
        pb = await pg.evaluate("(m => { const pr = m.proposals.find(x => x.kind === 'rule' && /Firm policy/.test(x.title)); mtApply(m, pr); return (DB.company.playbook || []).map(r => r.text); })(DB.meetings.find(m => m.id === 'mt_read2'))")
        c.ok(any('signed change order' in (t or '') for t in pb), f'approved, the policy is in the firm\'s playbook in its own words: {pb[-2:]}')
        rec = find('Recover from Keystone')
        c.ok(rec and rec[0]['amount'] == 1450 and rec[0]['a']['assignee'] == 'Chen Biron', f"a vendor's mistake is a recovery task with the amount: {rec}")
        hold = find('Hold billing')
        c.ok(hold and hold[0]['kind'] == 'task' and hold[0]['a']['assignee'] in ('Billing', 'Controller'), f'"don\'t bill" is a hold on the biller\'s list: {hold}')
        prog = find('Draft progress billing', 'billing')
        c.ok(prog and prog[0]['a']['pct'] == 60 and prog[0]['a']['projectId'] == 'p121' and prog[0]['a']['billingKind'] == 'progress', f'a percent complete is a draft progress billing for the biller: {prog}')
        c.ok(not find('Klein balance') and not find('22,500'), 'a balance is never a bill')
        lead = find('Lindqvist', 'lead')
        c.ok(len(lead) == 1, f'a bid is a lead: {lead}')
        tax = find('Keep out of overhead')
        c.ok(tax and tax[0]['a']['assignee'] == 'Controller', f'a tax is kept out of overhead by the controller: {tax}')
        a = next(x for x in P if x['id'] == 'mpA'); bb = next(x for x in P if x['id'] == 'mpB')
        c.ok(a['corrected'] and a['corrected']['to'] == 'Alan' and a['a']['assignee'] == 'Alan' and 'mine' in a['corrected']['quote'], f"Gemini's owner is corrected on the proposal, with the quote: {a}")
        c.ok(bb['corrected'] and bb['a']['due'] == '2026-09-18' and bb['corrected']['from'] == '2027-08-04', f"Gemini's wrong date is corrected: {bb}")
        c.ok(find('Second coat of plaster'), 'what the notes missed is added')
        cash = R['cash']
        c.ok(cash and cash[0]['said'] == 150000 and cash[0]['flag'], f'the cash said in the room is checked against the bank accounts and flagged: {cash}')
        c.ok(r['peopleKept'] == 1 and await pg.evaluate("(paInit().people || []).length") == 1, 'a people item is kept for the owner alone')
        blob = await pg.evaluate("JSON.stringify(DB.meetings.find(m => m.id === 'mt_read2'))")
        c.ok('lateness' not in blob, 'and is nowhere on the meeting, its read or its proposals')
        # lessons: the improvement loop and the Brain's lessons
        f = await pg.evaluate("DB.signals.filter(s => s.kind === 'finding' && /meeting/.test(s.source || '')).map(s => s.label)")
        ch = await pg.evaluate("DB.changes.filter(c => c.source === 'loop' && c.loop.family === 'finding').map(c => [c.title, c.loop.fix])")
        c.ok(len(f) == 2 and any('billing alert' in x[1] for x in ch) and any('recoveries' in x[1] for x in ch), f'lessons of the §1.33 classes are findings in the improvement loop with their fix: {f} {ch}')
        L = await pg.evaluate("DB.meetings.find(m => m.id === 'mt_read2').read.lessons.map(l => l.title)")
        c.ok(len(L) == 2, f'and lessons to teach, on the read card: {L}')
        # applying the progress billing makes a billing task, never an invoice
        await pg.evaluate("(m => { const pr = m.proposals.find(x => x.kind === 'billing' && /progress/i.test(x.title)); mtApply(m, pr); })(DB.meetings.find(m => m.id === 'mt_read2'))")
        inv1 = await pg.evaluate("(DB.clients || []).reduce((a, c) => a + (c.invoices || []).length, 0)")
        act = await pg.evaluate("(DB.projects.find(p => p.id === 'p121').actions || []).filter(a => /Draft progress billing/.test(a.title)).map(a => [a.billing, a.assignee])")
        c.ok(inv1 == inv0 and act and act[0][0] is True, f'approved, it is a billing task; no invoice is made or sent: {inv0}->{inv1} {act}')
        # the meeting page shows what the read checked
        await pg.evaluate("mtTab = 'meetings'; mtOpen = 'mt_read2'; view = 'meetings'; render()")
        await pg.wait_for_timeout(200)
        card = await pg.evaluate("(document.querySelector('.mr-read') || {}).innerText || ''")
        c.ok('Checked Against the Transcript' in card and 'September 18' in card and 'off by' in card, f'the meeting shows the corrections and the cash check: {card[:200]}')
        await pg.screenshot(path=os.path.join(OUT, 'desktop_meeting_read.png'))
        await b.close()

        # the PM runs the read: people items are not kept
        b, pg, errs2 = await open_app(p)
        await setup(pg, 'u_alan')
        r = await pg.evaluate("mrRead(DB.meetings.find(m => m.id === 'mt_read2'), {size: 900}).then(x => x && {kept: x.peopleKept, dropped: x.peopleDropped})")
        c.ok(r == {'kept': 0, 'dropped': 1} and 'lateness' not in await pg.evaluate("JSON.stringify(DB)"), f"the PM's read keeps no people item anywhere: {r}")
        await b.close()

        b, pg, errs3 = await open_app(p, phone=True)
        await setup(pg, 'u_owner')
        await pg.evaluate("mrRead(DB.meetings.find(m => m.id === 'mt_read2'), {size: 900})")
        await pg.evaluate("mtTab = 'meetings'; mtOpen = 'mt_read2'; view = 'meetings'; render()")
        await pg.wait_for_timeout(200)
        w = await pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        c.ok(w[0] <= w[1] + 1, f'the meeting with its read, at 390: no sideways scroll ({w})')
        await pg.screenshot(path=os.path.join(OUT, 'phone_meeting_read.png'))
        await b.close()
        allerrs = [e for e in errs + errs2 + errs3 if 'favicon' not in e]
        c.ok(not allerrs, f'no errors: {allerrs[:3]}')
    return c.done()

sys.exit(asyncio.run(main()))
