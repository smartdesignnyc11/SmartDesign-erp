"""The page's main button survives the Made Today card (2026-10-19).
After a record is made, the Made Today card (#fnd-made) goes in at the top of the page and is repainted on every
render. The header pass (bhHeader) took the card for the page's first block, built the page header inside it and
lifted the primary button there, so the next repaint deleted it: after sending one invoice, the next draft invoice
had no Send to Client. Checked here for invoices and change orders, desktop and phone, as the billing person.
Run: python3 made_today_test.py"""
import asyncio
from harness import async_playwright, open_app, sign_in, Checks

FLOW = """async (kind) => {
  const c = DB.clients.find(x => x.id === 'cl45'), wait = (ms) => new Promise(r => setTimeout(r, ms));
  const mk = (t) => { const d = newDoc(c, kind); d.projectId = 'p45'; d.title = t; d.lines = [{ id: uid('l'), item: 'Check', qty: 1, unit: 'ls', rate: 100, taxable: false }];
    const L = kind === 'co' ? (c.cos = c.cos || c.changeOrders || []) : c.invoices; if (!L.includes(d) && !(c.invoices.includes(d) || (c.cos || []).includes(d))) L.push(d); return d; };
  const A = mk('First'), B = mk('Second'); save();
  const open = async (d) => { billTab = kind === 'co' ? 'co' : 'billable'; clientOpen = c.id; docOpen = { kind, id: d.id }; view = 'billing'; render(); await wait(300); };
  const btn = () => [...document.querySelectorAll('section.view.on [data-docact=sendclient]')].find(b => b.offsetParent);
  const out = { kind };
  await open(A); out.first = !!btn();
  if (!out.first) return out;
  btn().click(); await wait(500); const ok = document.querySelector('#mbm-ok'); ok && ok.click(); await wait(800);
  out.sent = A.status; out.card = !!document.getElementById('fnd-made');
  await open(B); out.second = !!btn(); render(); await wait(200); out.afterRender = !!btn();
  out.inCard = !!document.querySelector('#fnd-made [data-docact], #fnd-made .ph');
  return out; }"""

async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            tag = 'phone' if phone else 'desktop'
            for kind in ('invoice', 'co'):
                b, pg, errs = await open_app(p, phone)
                await sign_in(pg, 'u_billing')
                r = await pg.evaluate(FLOW, kind)
                c.ok(r.get('first'), f'{tag} {kind}: the first draft has Send to Client ({r})')
                if r.get('first'):
                    c.ok(r.get('sent') == 'sent' and r.get('card'), f'{tag} {kind}: sent, and Made Today shows it ({r})')
                    c.ok(r.get('second') and r.get('afterRender'), f'{tag} {kind}: the next draft still has Send to Client, after another render too ({r})')
                    c.ok(not r.get('inCard'), f'{tag} {kind}: nothing of the page header is built inside the Made Today card ({r})')
                c.ok(not errs, f'{tag} {kind}: page errors {errs[:2]}')
                await b.close()
            # a chat line says which of the job's conversations it is in, and Open goes there (2026-10-20: a driver's
            # store-run notice, a team line, read "posted for the client")
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_owner')
            r = await pg.evaluate("""() => { const p = DB.projects.find(x => x.id === 'p45'), E = FND_HOME['p.chat'];
            const team = { id: 'x1', system: true, by: 'System', text: 'Store run: Alex picked up 6 bags of thinset' }, cl = { id: 'x2', system: true, by: 'System', text: 'INV-9 is ready for you under Account' };
            const out = { team: E.where(team, p), client: E.where(cl, p) }; (p.chat = p.chat || []).push(team); E.open(team, p); out.key = msgKey; return out; }""")
            c.ok('team chat' in r['team'] and 'client' not in r['team'] and 'chat with the client' in r['client'] and r['key'] == 'job:p45', f'{tag}: a team line says team chat and opens the team thread; a client line says so ({r})')
            await b.close()
    print(f'{len(c.fail)} FAILED ({c.n} checks)' if c.fail else f'ALL PASS ({c.n} checks)')
    raise SystemExit(1 if c.fail else 0)

asyncio.run(main())
