"""Client documents (lane p2fix3): Pilot 2's Documents Workshop, reproduced the way the owner, the designer, billing and
the client (Sarah Klein) read each document, then held. Invented data only: the seed plus what each check adds.

1  S1 Internal text never reaches a client. Every client-facing document type is drawn from the demo data (proposal,
   construction proposal, design proposal, change order, invoice, design-fee invoice, deposit invoice, pay
   application, the statement, the portal's view of each, the client mail) plus the pilot's own cases made through the
   app's paths: the billing queue's pay application (the app wrote "5 lines fell back to cost — check them before
   sending" and "measured by foreman update 9/2" onto it) and a change order typed with "Angel asked 9/8". The check
   fails on any working note, a staff first name in an internal phrase, a line's cost, a margin, a cost code or
   "check"/"before sending" wording. Its patterns are written here, not read from the app, so a change in the app's
   own list cannot hide a leak.
2  S1 A $0 or blank document cannot be sent, printed for the client, signed or published to the portal: the reason
   is shown. A blank bill-to is refused the same way.
3  S2 One letterhead from the company settings (SmartDesign, never "SmartDesigns"; address, phone, licences, SD
   Plumbing and SD Electric), every date with its year, one terms source (no "net 7" beside "within 15 days"), a footer
   that fits the type, due dates on business days, units in words.
4  S2 Every unpaid invoice says how to pay: bank name and the last 4 only, check payable to, the portal.
5  S2 The pay application shows each total once, explains retainage to date, and carries every approved change order.
6  S3 Every change order prints the contract sum before and after, the reason type and the schedule effect.
7  The portal (the client's coordinator answers): every sent, unsigned proposal and change order is in Waiting on You,
   approvable from there; what the client approved is shown; estimates and design invoices are on the portal; the
   Invoices Due tile equals the invoices listed; no client sees another client's document (portal and mail).
8  A Preview from the billing queue uses no invoice number; a draft deleted unsent gives its number back.
Desktop 1440 and phone 390."""
import asyncio, json, os, re, sys
from harness import *

SLEEP = "ms => new Promise(r => setTimeout(r, ms))"
SHOTS = os.environ.get('SD_SHOTS') or os.path.join(ROOT, 'review', 'p2fix3', 'after')
TAG = os.environ.get('SD_SHOT_TAG', '')


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = " + SLEEP + "; " + body + " }", arg)


# The independent list of what never reaches a client (the test's own, not the app's)
LEAKS = [r'fell back to', r'before sending', r'check (it|them|this|these) before', r'measured by', r'elapsed time',
         r'percentages proposed', r'below what was already billed', r'correction is a credit with a reason',
         r'fill in what you know', r'cost \(fallback\)', r'\bcost codes?\b', r'\bbudget cost\b', r'\bmargin\b',
         r'\bmark-?up\b', r'foreman update', r'PM update', r'Internal notes', r'nothing else speaks',
         r'stays at its billed %', r'\d% against \d', r'running tasks? still', r'labelled']

# the page side: every client document of every client, drawn the way it leaves the firm, as text
DRAW = r"""
  const txt = h => { const t = document.createElement('textarea');
    t.innerHTML = String(h || '').replace(/<style[\s\S]*?<\/style>/g, ' ').replace(/<script[\s\S]*?<\/script>/g, ' ').replace(/<br\s*\/?>/g, '\n').replace(/<\/(div|tr|p|li|h\d)>/g, '\n').replace(/<[^>]+>/g, ' ');
    return t.value.replace(/[ \t]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim(); };
  const staff = [...new Set([...(DB.users || []).filter(u => u.role && u.role !== 'client' && !/^mb/.test(u.role)), ...(DB.employees || [])]
    .map(u => String(u.name || '').split(/\s+/)[0]).filter(f => /^[A-Z][a-z]{2,}$/.test(f) && !/^(Owner|Billing|Controller|Design|Crew|Office)$/.test(f)))];
  const out = [];
  for (const c of DB.clients) {
    const mine = new Set([c.name, ...(c.contacts || []).map(x => x.name)].join(' ').split(/[\s&,]+/).map(w => w.toLowerCase()));
    const names = staff.filter(n => !mine.has(n.toLowerCase()));
    for (const d of [...c.estimates, ...c.changeOrders, ...c.invoices]) {
      if (d.status === 'void') continue;
      const html = docPrintHtml(c, d), t = txt(html);
      let sum = ''; try { sum = txt(docSummaryHtml(c, d)); } catch (e) { sum = 'ERR ' + e; }
      let mail = {}; try { const E = crDocEmail(c, d); mail = { to: (E.to || {}).email || '', body: E.body || '', subject: E.subject || '' }; } catch (e) {}
      const costs = (d.lines || []).filter(l => +l.cost > 0 && Math.abs(+l.cost - (+l.rate || 0)) > 0.5).map(l => money(+l.cost));
      const amounts = new Set([...(d.lines || []).flatMap(l => [money(+l.rate || 0), money(lineAmount(l, d)), money(+l.scheduled || 0)]), money(docTotal(d).total)]);
      out.push({ client: c.id, cname: c.name, number: d.number, type: d.type, mode: d.mode || '', kind: typeof cxKind === 'function' ? cxKind(d) : '', status: d.status,
        total: docTotal(d).total, due: d.due || '', text: t, sum, mail, names, emails: (c.contacts || []).map(x => (x.email || '').toLowerCase()),
        costs: costs.filter(m => !amounts.has(m)), html_len: html.length });
    }
  }
  return out;
"""


async def make_pilot_docs(pg):
    """The pilot's documents, made through the app's own paths."""
    return await js(pg, """
      appConfirm = () => true;
      const c = DB.clients.find(x => x.id === 'cl121'); setCurrent('p121');
      // the pay application drafted on purpose (the app writes its evidence notes). Since lane 1 (TRIAGE class 2's
      // accept: the queue proposes nothing on a job billed ahead) 121 State's application is a held row, so billing
      // drafts it from Progress Billing (blDraftApplication), not from a ready row
      view = 'billing'; billTab = 'billable'; render(); await sleep(100);
      const before = c.invoices.length;
      blDraftApplication('p121'); await sleep(250);
      const pa = c.invoices.find(i => i.mode === 'sov' && i.status === 'draft');
      // a change order typed the way the PM typed CO-2026-004 (a staff name and the day in the description)
      clientOpen = c.id; finProj = 'p121';
      const co = newDoc(c, 'co'); co.projectId = 'p121'; co.title = 'Stair landing guard raised to 42 inches (code)';
      co.lines = [{ id: uid('l'), item: 'Stair landing guard to 42 in (code)', desc: 'Raise stair landing guard to 42 inches per code: new posts and rail, finish to match. Angel asked 9/8.', qty: 1, unit: 'ls', rate: 1450, cost: 980, code: '10', taxable: false }];
      co.memo = 'Guard at the stair landing raised to 42 inches to meet code.';
      // the $0 proposal: New Estimate on the construction template, nothing typed (EST-2026-016)
      const e0 = newDoc(c, 'estimate', { template: 'construction' }); e0.projectId = 'p121';
      // the design-fee milestone invoice (INV-2026-039): Draft on the billing queue row
      const r = DB.clients.find(x => x.id === 'cl45'), rb = r.invoices.length;
      rtbAct('dmilestone:esD45'); await sleep(250);
      const mo = document.querySelector('#mbm #mbm-ok'); mo && mo.click(); await sleep(250);
      const dm = r.invoices.slice(rb)[0] || null;
      // the contract's deposit invoice, drafted from the Billing Queue's deposit row (lane 1, 2026-10-26). The seed's
      // INV-2026-031 ("Deposit — 20%") was billed as a % on the SOV and is booked as work, so it prints as an
      // application now (one deposit predicate for the ledger, lineFin and the printout)
      const ca = blankClient('Wren & Julian Ashby'); ca.contacts = [{ id: uid('ct'), name: 'Wren Ashby', email: 'wren.ashby@example.com', primary: true }]; DB.clients.push(ca);
      const pj = blankProject('214 Lincoln Place', '214 Lincoln Place, Brooklyn', today(), ''); pj.clientId = ca.id; DB.projects.push(pj);
      const ea = newDoc(ca, 'estimate', { template: 'construction', fields: { title: '214 Lincoln Place — renovation', projectId: pj.id } });
      ea.lines = [{ id: uid('l'), item: 'Demolition and protection', qty: 1, unit: 'ls', rate: 91120, cost: 60000 }]; ea.status = 'converted'; ea.approvedOn = today(); docMark(ea);
      rtbAct('deposit:' + ea.id); await sleep(250);
      const dq = document.querySelector('#mbm #mbm-ok'); dq && dq.click(); await sleep(250);
      save();
      return { pa: pa && pa.number, paMemo: pa && pa.memo, paInternal: pa && pa.internal, paDesc: pa ? pa.lines.map(l => l.desc).filter(Boolean) : [],
               paEv: pa ? pa.lines.map(l => l.evidence).filter(Boolean) : [], co: co.number, e0: e0.number, e0terms: e0.terms, dm: dm && dm.number, dmDue: dm && dm.due };""")


async def shoot_doc(p, html, path, phone=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    b = await p.chromium.launch()
    pg = await (await b.new_context(viewport=PHONE if phone else {'width': 900, 'height': 1200})).new_page()
    await pg.set_content(html.replace('window.print()', '0'))
    await pg.screenshot(path=path, full_page=True)
    await b.close()


async def t_documents(c, p):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    made = await make_pilot_docs(pg)
    print('made', json.dumps({k: v for k, v in made.items() if k not in ('paMemo', 'paInternal')}))
    # [1] the app's own notes go to Internal Notes and the line's evidence, never to the client's memo or a line
    c.ok(made['pa'], '[1] billing drafted the pay application')
    c.ok(not re.search(r'fell back|check them|Percentages proposed|below what was already billed', made['paMemo'] or ''),
         f"[1] the pay application's client memo holds no working note: {made['paMemo']!r}")
    c.ok(not any(re.search(r'measured by|elapsed time', x) for x in made['paDesc']), f"[1] no line description carries the evidence: {made['paDesc'][:3]}")
    c.ok(any('measured by' in x for x in made['paEv']) or 'Percentages proposed' in (made['paInternal'] or ''),
         f"[1] the evidence stays for billing (Internal Notes / the line's evidence): {made['paEv'][:2]} {made['paInternal']!r}")
    D = await js(pg, DRAW)
    types = {(d['type'], d['kind']) for d in D}
    print('drawn', len(D), sorted(types))
    for need in [('estimate', 'estimate'), ('co', 'co'), ('invoice', 'progress'), ('invoice', 'deposit'), ('invoice', 'design')]:
        c.ok(need in types, f'[1] a {need} document was drawn')
    for d in D:
        where = f"{d['number']} ({d['kind']}, {d['status']})"
        for sect, text in (('print', d['text']), ('portal', d['sum']), ('mail', d['mail'].get('body', '') + ' ' + d['mail'].get('subject', ''))):
            for pat in LEAKS:
                m = re.search(pat, text, re.I)
                c.ok(not m, f"[1] {where} {sect}: internal wording {pat!r} reaches the client: ...{text[max(0, (m.start() if m else 0) - 60):(m.end() if m else 0) + 40]!r}")
            if d['names']:
                nre = re.compile(r'\b(?:per\s+(?:%s)|(?:%s)(?:\'s)?\s+(?:asked|said|says|called|wants|told|requested|flagged|noted|confirmed|measured|checked))\b' % ('|'.join(d['names']), '|'.join(d['names'])))
                m = nre.search(text)
                c.ok(not m, f"[1] {where} {sect}: a staff name in an internal phrase: {m and m.group(0)!r}")
        for m in d['costs']:
            c.ok(m not in d['text'], f"[1] {where}: a line's cost {m} prints")
        # [3] one letterhead, full dates, units in words, footers that fit
        t = d['text']
        c.ok('SmartDesigns' not in t and 'SmartDesign' in t, f'[3] {where}: the letterhead reads SmartDesign')
        c.ok('214 Court Street' in t and '(718) 555-0190' in t, f'[3] {where}: the address and phone are on the letterhead')
        c.ok('SD Plumbing' in t and 'SD Electric' in t and 'Home Improvement Contractor' in t, f'[3] {where}: the licences and the in-house trades are on the letterhead')
        c.ok(not re.search(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun), (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}\b(?!, \d{4})', t), f'[3] {where}: a date without its year: {re.findall(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), \w{3} \d{1,2}", t)[:3]}')
        c.ok(re.search(r'Date: [A-Z][a-z]+ \d{1,2}, 20\d\d', t), f'[3] {where}: the document date is written in full')
        c.ok(not re.search(r'\b\d+(\.\d+)? (ls|ea)\b', t), f'[3] {where}: trade units ("1 ls", "1 ea") print: {re.findall(r"[0-9.]+ (?:ls|ea)", t)[:3]}')
        c.ok('Progress invoices are due within 15 days' not in t, f'[3] {where}: the old boilerplate restates terms the document already states')
        if d['kind'] in ('co', 'design', 'estimate', 'invoice'):
            c.ok('Retainage is held' not in t, f'[3] {where}: the retainage footer prints on a {d["kind"]}')
        mm = re.search(r'Due: ([A-Z][a-z]+ \d{1,2}, 20\d\d)', t)
        if mm and d['status'] in ('draft', 'sent'):
            wd = await pg.evaluate("s => new Date(s).getDay()", mm.group(1))
            c.ok(wd not in (0, 6), f'[3] {where}: due {mm.group(1)} falls on a weekend')
        # [4] how to pay on every unpaid invoice, last 4 only
        if d['type'] == 'invoice' and d['total'] > 0.005 and d['status'] != 'paid':
            c.ok('How to Pay' in t and 'Atlantic Community Bank' in t and 'ending 4417' in t, f'[4] {where}: no How to Pay block (bank, last 4)')
            c.ok('payable to SmartDesign Group LLC' in t, f'[4] {where}: no check payable to')
            c.ok(not re.search(r'\b\d{7,}\b', re.sub(r'#\d+', '', t)), f'[4] {where}: a long account-like number prints')
        # [5] the pay application: one total, retainage explained
        if d['kind'] == 'progress':
            c.ok(t.count('Current payment due') == 1 and 'Total this invoice' not in t, f'[5] {where}: the answer shows once ({t.count("Current payment due")} times)')
            c.ok('Held to date' in t and 'released with the final invoice' in t, f'[5] {where}: retainage to date is explained')
            c.ok('Completed to date' in t and 'Balance to finish' in t and 'Previous applications' in t, f'[5] {where}: the G703 columns')
        # [6] the change order
        if d['kind'] == 'co':
            for w in ('Original contract sum', 'Contract sum before this change', 'New contract sum', 'Reason for the change:', 'Schedule:'):
                c.ok(w in t, f'[6] {where}: {w!r} missing')
        # [7] mail goes to the document's own client only
        if d['mail'].get('to'):
            c.ok(all(x.strip().lower() in d['emails'] for x in d['mail']['to'].split(',')), f"[7] {where}: client mail goes to {d['mail']['to']}, not one of {d['cname']}'s contacts")
    # the change order the PM typed never says "Angel asked", on the print or on the portal
    co = next((d for d in D if d['number'] == made['co']), None)
    c.ok(co and 'Angel' not in co['text'] and 'Angel' not in co['sum'], f"[1] {made['co']}: the staff note is off the client's copy")
    c.ok(co and 'Code requirement' in co['text'], f"[6] {made['co']}: the reason type is inferred (code) and printed")
    c.ok('net 7' not in (made['e0terms'] or ''), f"[3] the construction proposal's terms come from the one terms source: {made['e0terms']!r}")
    # the design-fee invoice: the fee summary, its due date
    dm = next((d for d in D if d['number'] == made['dm']), None)
    c.ok(dm and 'Your design fee' in dm['text'] and 'Remaining after this invoice' in dm['text'], f"[3] {made['dm']}: the design fee summary")
    c.ok(dm and '45 Cranberry St' in dm['text'].split('Project')[0], f"[3] {made['dm']}: the bill-to address fills from the client record")
    # screenshots: one of each kind
    for d in D:
        pass
    shots = await js(pg, """
      const pick = k => { for (const c of DB.clients) for (const d of [...c.estimates, ...c.changeOrders, ...c.invoices]) if (d.number === k) return docPrintHtml(c, d); return ''; };
      return arg.map(k => [k, pick(k)]);""", [made['pa'], made['co'], made['dm'], 'INV-2026-031', 'EST-2026-014', 'CO-2026-002'])
    for k, h in shots:
        if h:
            await shoot_doc(p, h, os.path.join(SHOTS, f'{TAG}doc_{k}.png'))
    c.ok(not errs, f'[docs] page errors: {errs[:3]}')
    await b.close()


async def t_gate(c, p):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    made = await make_pilot_docs(pg)
    r = await js(pg, """
      const c = DB.clients.find(x => x.id === 'cl121'), f = (n) => [...c.estimates, ...c.changeOrders, ...c.invoices].find(d => d.number === n);
      let opened = 0; const w0 = window.open; window.open = () => { opened++; return null; };
      const modal = () => { const m = document.getElementById('mbm'); const t = m ? m.innerText : ''; m && m.remove(); return t; };
      const out = {};
      docOpen = null; clientOpen = c.id; view = 'clients'; render();
      const e0 = f(arg.e0);
      await docAction(c, e0, 'send'); out.e0send = [e0.status, modal()];
      await docAction(c, e0, 'print'); out.e0print = [opened, modal()];
      await docAction(c, e0, 'approve'); out.e0approve = [e0.status, modal()];
      await crSendToClient(c, e0); out.e0client = [e0.status, modal()];
      // the change order with the staff note: refused, the note moves in one tap, then it goes
      const co = f(arg.co);
      await docAction(c, co, 'sendclient'); await sleep(50);
      const m = document.getElementById('mbm'); out.coWhy = m ? m.innerText : '';
      m && m.querySelector('#mbm-ok') && m.querySelector('#mbm-ok').click(); await sleep(80);
      out.coAfter = { desc: co.lines[0].desc, internal: co.internal, toast: (document.getElementById('toast') || {}).innerText || '' };
      await docAction(c, co, 'send'); out.coSent = co.status; modal();
      // a $0 application draft cannot go
      const inv0 = newDoc(c, 'invoice', { mode: 'sov' }); inv0.projectId = 'p121';
      await crSendToClient(c, inv0); out.inv0 = [inv0.status, modal()];
      // a blank bill-to
      // a client with no address and no job to take one from (a job's address fills the bill-to when the client has none)
      const n = blankClient('Hollis Row Partners'); n.contacts = [{ id: 'cth', name: 'Dana Hollis', email: 'dana@hollisrow.example', primary: true }]; DB.clients.push(n);
      const ba = [n.billingAddr, n.propertyAddr]; n.billingAddr = ''; n.propertyAddr = '';
      const i1 = newDoc(n, 'invoice'); i1.lines = [{ id: uid('l'), item: 'Design consultation', desc: '', qty: 1, unit: 'ls', rate: 800 }];
      await docAction(n, i1, 'send'); out.billto = [i1.status, modal()];
      n.billingAddr = '18 Hollis Row, Brooklyn, NY 11215';
      // a good one prints and sends
      await docAction(n, i1, 'print'); out.goodPrint = opened; modal();
      // the editor says why before the person tries
      clientOpen = c.id; view = 'billing'; billTab = 'estimates'; docOpen = { kind: 'estimate', id: e0.id }; render(); await sleep(60);
      out.banner = (document.querySelector('.cx-gate') || {}).innerText || '';
      window.open = w0;
      // the client never sees what was refused
      signIn('u_klein'); view = 'client'; render(); await sleep(100);
      out.portal = clWaitingItems().map(w => w.d.number || '');
      signIn('u_owner');
      return out;""", made)
    print('gate', json.dumps({k: (v if not isinstance(v, list) else [v[0], str(v[1])[:160]]) for k, v in r.items() if k != 'portal'})[:1800])
    c.ok(r['e0send'][0] == 'draft' and 'Not Ready for the Client' in r['e0send'][1] and 'totals $0' in r['e0send'][1], f"[2] a $0 proposal is refused on Send, with the reason: {r['e0send']}")
    c.ok('has no description' in r['e0send'][1], f"[2] the blank line is named: {r['e0send'][1][:200]!r}")
    c.ok(r['e0print'][0] == 0 and 'Print Draft Copy' in r['e0print'][1], f"[2] Print for the client is refused on a $0 proposal (a draft copy is offered): {r['e0print']}")
    c.ok(r['e0approve'][0] == 'draft' and 'Not Ready' in r['e0approve'][1], f"[2] a $0 proposal cannot be signed: {r['e0approve']}")
    c.ok(r['e0client'][0] == 'draft' and 'Not Ready' in r['e0client'][1], f"[2] Send to Client refuses it too: {r['e0client']}")
    c.ok('Angel asked 9/8' in r['coWhy'] and 'staff name' in r['coWhy'], f"[1] Send names the staff note: {r['coWhy'][:240]!r}")
    c.ok('Angel' not in r['coAfter']['desc'] and 'Angel asked 9/8' in (r['coAfter']['internal'] or ''), f"[1] Move Notes to Internal moves it: {r['coAfter']}")
    c.ok('moved to Internal Notes' in r['coAfter']['toast'], f"[1] the move toasts: {r['coAfter']['toast']!r}")
    c.ok(r['coSent'] == 'sent', f"[1] the cleaned change order sends: {r['coSent']}")
    c.ok(r['inv0'][0] == 'draft' and 'Nothing is billed' in r['inv0'][1], f"[2] a $0 application cannot be sent: {r['inv0']}")
    c.ok(r['billto'][0] == 'draft' and 'no billing or property address' in r['billto'][1], f"[2] a blank bill-to is refused: {r['billto']}")
    c.ok(r['goodPrint'] == 1, f"[2] a complete invoice prints: {r['goodPrint']}")
    c.ok('Not ready for the client' in r['banner'], f"[2] the editor shows what blocks Send: {r['banner'][:120]!r}")
    c.ok(made['e0'] not in r['portal'], f"[2] the refused proposal is not on the portal: {r['portal']}")
    c.ok(not errs, f'[gate] page errors: {errs[:3]}')
    await b.close()


async def t_payapp(c, p):
    """Every approved change order bills on the application; the contract sum is as of the application's date."""
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    r = await js(pg, """
      appConfirm = () => true;
      const c = DB.clients.find(x => x.id === 'cl121'), co2 = c.changeOrders.find(x => x.number === 'CO-2026-002');
      setCurrent('p121'); clientOpen = c.id;
      const sent = c.invoices.find(x => x.number === 'INV-2026-038'), before = payAppData(c, sent).coAmt;
      await docAction(c, co2, 'approve'); await sleep(50);
      const after = payAppData(c, sent).coAmt;
      view = 'billing'; billTab = 'billable'; render(); await sleep(80);
      blDraftApplication('p121'); await sleep(250);   // held on a job billed ahead: drafted on purpose (lane 1)
      const pa = c.invoices.find(i => i.mode === 'sov' && i.status === 'draft');
      const lines = pa.lines.map(l => l.item), A = payAppData(c, pa), t = docPrintHtml(c, pa);
      return { before, after, lines: lines.filter(x => /CO-/.test(x)), coAmt: A.coAmt, onPrint: /CO-2026-002/.test(t), approvedCos: c.changeOrders.filter(x => ['approved', 'billed'].includes(x.status)).map(x => x.number) };""")
    print('payapp', r)
    c.ok(abs(r['before'] - r['after']) < 0.01, f"[5] a sent application's contract sum does not move when a later change order is approved ({r['before']} vs {r['after']})")
    c.ok(all(any(n in x for x in r['lines']) for n in r['approvedCos']), f"[5] every approved change order has a line on the next application: {r['lines']} vs {r['approvedCos']}")
    c.ok(r['onPrint'], '[5] CO-2026-002 prints on the next application')
    c.ok(abs(r['coAmt'] - 8050) < 0.01, f"[5] the next application counts both approved change orders ($8,050): {r['coAmt']}")
    c.ok(not errs, f'[payapp] page errors: {errs[:3]}')
    await b.close()


async def t_portal(c, p, phone):
    tag = 'phone' if phone else 'desktop'
    b, pg, errs = await open_app(p, phone=phone)
    await sign_in(pg, 'u_owner')
    # a CO already sent with a staff note in it (written before this change): the portal still never shows it
    await js(pg, """
      appConfirm = () => true;
      const c = DB.clients.find(x => x.id === 'cl121'); setCurrent('p121');
      const co = newDoc(c, 'co'); co.projectId = 'p121'; co.title = 'Stair landing guard raised to 42 inches (code)';
      co.lines = [{ id: uid('l'), item: 'Stair landing guard to 42 in', desc: 'New posts and rail, finish to match. Angel asked 9/8.', qty: 1, unit: 'ls', rate: 1450, cost: 980 }];
      co.status = 'sent'; co.sentAt = today();
      const co3 = newDoc(c, 'co'); co3.projectId = 'p121'; co3.title = 'Pantry wall GFCI outlet';
      co3.lines = [{ id: uid('l'), item: 'GFCI outlet, pantry wall', desc: 'Supply and install one GFCI outlet', qty: 1, unit: 'ea', rate: 420 }];
      co3.status = 'sent'; co3.sentAt = today();
      co3.clientApproval = { name: 'Sarah Klein', t: '9/3, 10:30 AM', ts: today() + 'T10:30:00', total: 420, lines: 1, via: 'portal', user: 'u_klein' };
      co3.status = 'approved'; co3.approvedOn = today();
      save();""")
    out = {}
    for uid_, cid in (('u_klein', 'cl121'), ('u_cambri', 'cl140')):
        await sign_in(pg, uid_)
        r = await js(pg, """
          view = 'client'; render(); await sleep(200);
          const c = clientUserOf(), v = document.getElementById('v-client'), text = v ? v.innerText : '';
          const W = clWaitingItems().filter(w => w.kind === 'doc').map(w => w.d.number);
          const P = new Set(DB.projects.filter(p => p.clientId === c.id && (!S || p.id === S.id)).map(p => p.id));
          const should = [...c.estimates, ...c.changeOrders].filter(d => d.status === 'sent' && (!d.projectId || P.has(d.projectId))).map(d => d.number);
          const listed = [...document.querySelectorAll('#cl-approvals .pa-row')].filter(r => r.querySelector('[data-pview^="invoice:"]')).map(r => (r.querySelector('.pa-amt') || {}).innerText || '');
          const tile = [...document.querySelectorAll('#v-client .gl')].map(x => x.innerText).find(x => /Invoices Due/.test(x)) || '';
          const others = DB.clients.filter(x => x.id !== c.id).flatMap(x => [...x.estimates, ...x.changeOrders, ...x.invoices].map(d => d.number)).filter(n => n && text.includes(n));
          const mineDocs = [...c.estimates, ...c.changeOrders, ...c.invoices].filter(d => !['draft', 'void'].includes(d.status) && (!d.projectId || P.has(d.projectId))).map(d => d.number);
          const docsList = (document.querySelector('#cl-account .cx-docs') || {}).innerText || '';
          const done = (document.querySelector('.cx-done') || {}).innerText || '';
          // the View of an unpaid invoice says how to pay
          const inv = (clientFin(c).open || [])[0];
          let how = '';
          if (inv) { portalView(c, 'invoice', inv.x); await sleep(60); how = (document.getElementById('mbm') || {}).innerText || ''; mbCloseModal(); }
          const sx = document.documentElement.scrollWidth - innerWidth;
          return { W, should, listed, tile, others, missingDocs: mineDocs.filter(n => !docsList.includes(n)), done, how, sx, angel: /Angel/.test(text),
                   sumAngel: c.changeOrders.filter(d => d.status === 'sent').some(d => /Angel/.test(docSummaryHtml(c, d))) };""")
        out[uid_] = r
        print(tag, uid_, json.dumps({k: v for k, v in r.items() if k not in ('how',)})[:900])
        c.ok(all(n in r['W'] for n in r['should']), f"[7] {tag} {uid_}: every sent, unsigned proposal and change order is in Waiting on You: {r['should']} vs {r['W']}")
        c.ok(not r['others'], f"[7] {tag} {uid_}: another client's document shows on this client's portal: {r['others']}")
        c.ok(not r['missingDocs'], f"[7] {tag} {uid_}: Your Documents lists every document sent to the client (estimates and design invoices too): missing {r['missingDocs']}")
        if r['tile']:
            tv = re.search(r'\$([\d,]+)', r['tile'])
            tot = sum(float(re.sub(r'[^\d.]', '', x) or 0) for x in r['listed'])
            c.ok(tv and abs(float(tv.group(1).replace(',', '')) - tot) < 1, f"[7] {tag} {uid_}: the Invoices Due tile ({r['tile'][:40]!r}) equals the invoices listed ({r['listed']})")
        if r['how']:
            c.ok('How to Pay' in r['how'] and 'ending 4417' in r['how'], f"[4] {tag} {uid_}: the portal's invoice says how to pay: {r['how'][-300:]!r}")
        c.ok(not r['sumAngel'], f'[1] {tag} {uid_}: a staff note on a sent change order never shows on the portal')
        if phone: c.ok(r['sx'] <= 1, f'[7] {tag} {uid_}: the portal scrolls sideways by {r["sx"]}px')
        await pg.screenshot(path=os.path.join(SHOTS, f'{TAG}portal_{uid_}_{tag}.png'), full_page=True)
    k = out['u_klein']
    c.ok('you approved' in k['done'].lower() and 'Pantry wall GFCI outlet' in k['done'], f"[7] {tag}: the change order the client approved shows as approved, with the date: {k['done'][:200]!r}")
    c.ok(not errs, f'[portal {tag}] page errors: {errs[:3]}')
    await b.close()


async def t_numbers(c, p):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_billing')
    r = await js(pg, """
      appConfirm = () => true;
      const c = DB.clients.find(x => x.id === 'cl121'), seq0 = DB.company.seq.inv, n0 = c.invoices.length, a0 = (DB.audit || []).length;
      view = 'billing'; billTab = 'billable'; render(); await sleep(150);
      const btn = document.querySelector('[data-cxprev="p121"]');
      btn && btn.click(); await sleep(250);
      const m = document.getElementById('mbm'), txt = m ? m.innerText : '', frame = !!(m && m.querySelector('iframe.cx-prev'));
      mbCloseModal();
      const after = { seq: DB.company.seq.inv, n: c.invoices.length, audit: (DB.audit || []).length };
      // a draft deleted before it is sent gives its number back
      clientOpen = c.id;
      const d = newDoc(c, 'invoice'), num = d.number;
      await docAction(c, d, 'del'); await sleep(50);
      const d2 = newDoc(c, 'invoice');
      return { btn: !!btn, txt: txt.slice(0, 300), frame, seq0, n0, a0, after, num, num2: d2.number };""")
    print('numbers', r)
    c.ok(r['btn'], '[8] the billing queue offers Preview on the ready application')
    c.ok(r['frame'] and 'no invoice number was used' in r['txt'], f"[8] Preview shows the application: {r['txt'][:160]!r}")
    c.ok(r['after']['seq'] == r['seq0'] and r['after']['n'] == r['n0'], f"[8] Preview uses no number and makes no draft: {r['seq0']}->{r['after']['seq']}, {r['n0']}->{r['after']['n']}")
    c.ok(r['after']['audit'] == r['a0'], f"[8] Preview writes nothing to the audit trail ({r['a0']}->{r['after']['audit']})")
    c.ok(r['num'] == r['num2'], f"[8] a deleted unsent draft gives its number back: {r['num']} then {r['num2']}")
    c.ok(not errs, f'[numbers] page errors: {errs[:3]}')
    await b.close()


async def t_statement(c, p):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    r = await js(pg, """
      repClient = 'cl121'; const h = repStatement(); const t = document.createElement('div'); t.innerHTML = h;
      return t.innerText;""")
    c.ok('SmartDesign' in r and 'How to Pay' in r and 'ending 4417' in r, '[3] the statement is on the letterhead with How to Pay')
    c.ok('Progress invoices are due within 15 days' not in r, '[3] the statement drops the contradicting boilerplate')
    c.ok(not errs, f'[statement] page errors: {errs[:3]}')
    await b.close()


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    c = Checks()
    only = sys.argv[1:] or ['documents', 'gate', 'payapp', 'portal', 'numbers', 'statement']
    async with async_playwright() as p:
        if 'documents' in only: await t_documents(c, p)
        if 'gate' in only: await t_gate(c, p)
        if 'payapp' in only: await t_payapp(c, p)
        if 'portal' in only:
            await t_portal(c, p, False)
            await t_portal(c, p, True)
        if 'numbers' in only: await t_numbers(c, p)
        if 'statement' in only: await t_statement(c, p)
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
