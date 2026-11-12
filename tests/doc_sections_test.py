"""The client document prints the way the firm's estimates read (lane P, 11-12). Invented data only.

1  A grouped estimate (each line carries `group`) prints a section header with that section's subtotal, then its
   lines, sections in first-appearance order; the section subtotals add up to the document's subtotal.
2  An estimate with no groups prints the flat table exactly as before (the expected markup is written here).
3  A line marked Excluded prints its item with "Excluded" where the amount was and counts $0: line amount, section
   subtotal, document total, budget, and the schedule of values built from the estimate.
4  A line marked TBD prints "TBD" the same way.
5  The editor: a Section input per line with the document's sections offered, and Priced / Excluded / TBD per line.
6  The document at 390px does not scroll sideways.
7  The HVAC & mechanical cost code: in the code select, in Cost by Code, and a workspace's own code keeps its number.
"""
import asyncio, json, re, sys
from harness import *

SLEEP = "ms => new Promise(r => setTimeout(r, ms))"


async def js(pg, body, arg=None):
    return await pg.evaluate("async (arg) => { const sleep = " + SLEEP + "; " + body + " }", arg)


MAKE = r"""
  const c = DB.clients.find(x => x.id === 'cl121') || DB.clients[0];
  const L = (id, item, qty, rate, x) => Object.assign({ id, item, desc: '', qty, unit: 'ls', rate, taxable: false, cat: 'construction', code: '01' }, x || {});
  const doc = (id, lines) => { const d = { id, type: 'estimate', number: 'EST-T-' + id, status: 'draft', date: today(), title: 'Invented sections test', projectId: '', taxRate: 0, terms: '', memo: '', lines };
    c.estimates = c.estimates.filter(e => e.id !== id); c.estimates.push(d); docMark(d); return d; };
  const G = doc('tsecG', [
    L('g1', 'Site protection', 1, 1200.5, { group: 'General Conditions' }),
    L('g2', 'Rough plumbing', 1, 100000.37, { group: 'Plumbing', code: '05' }),
    L('g3', 'Fixture setting', 1, 24500, { group: 'Plumbing', code: '05' }),
    L('g4', 'Panel upgrade', 2, 4100, { group: 'Electrical', code: '06' }),
    L('g5', 'Dumpsters', 3, 650, { unit: 'ea', group: 'General Conditions' }),
    L('g6', 'Steam boiler replacement', 1, 18000, { group: 'Plumbing', code: '05', excluded: true }),
    L('g7', 'Roof condenser pad', 1, 7000, { group: 'Electrical', code: '06', tbd: true }),
  ]);
  const U = doc('tsecU', [L('u1', 'Site protection', 1, 1200), L('u2', 'Dumpsters', 3, 650, { unit: 'ea', desc: 'Twenty yard' })]);
"""

READ = r"""
  const parse = h => new DOMParser().parseFromString(h, 'text/html');
  const rows = d => [...parse(cxDocHtml(c, d, { print: false })).querySelectorAll('.cxd table tbody tr')].map(tr => ({
    sec: tr.classList.contains('cx-sec'), cells: [...tr.children].map(td => td.textContent.trim()), muted: !!tr.querySelector('.cx-np') }));
"""


async def t_desktop(c, p):
    b, pg, errs = await open_app(p)
    await sign_in(pg, 'u_owner')
    r = await js(pg, MAKE + READ + r"""
      const RG = rows(G), t = docTotal(G), html = cxDocHtml(c, U, { print: false });
      const m = html.match(/<table>[\s\S]*?<\/table>/);
      return { RG, sub: t.sub, total: t.total, uTable: m ? m[0] : '', uSec: /cx-sec/.test(html),
        amt: Object.fromEntries(G.lines.map(l => [l.id, lineAmount(l, G)])), bud: Object.fromEntries(G.lines.map(l => [l.id, lineBudget(l, G).budget])),
        money: { gc: money(1200.5 + 1950), pl: money(100000.37 + 24500), el: money(8200), sub: money(t.sub) },
        totText: parse(cxDocHtml(c, G, { print: false })).querySelector('.cxd-tot').textContent };
    """)
    RG = r['RG']
    secs = [x for x in RG if x['sec']]
    c.ok([s['cells'][0] for s in secs] == ['General Conditions', 'Plumbing', 'Electrical'],
         f"[1] section headers in first-appearance order: {[s['cells'] for s in secs]}")
    c.ok([s['cells'][-1] for s in secs] == [r['money']['gc'], r['money']['pl'], r['money']['el']],
         f"[1] each header carries its section's subtotal: {[s['cells'][-1] for s in secs]} vs {r['money']}")
    order = [('S ' + x['cells'][0]) if x['sec'] else x['cells'][1].split('\n')[0] for x in RG]
    c.ok(order == ['S General Conditions', 'Site protection', 'Dumpsters', 'S Plumbing', 'Rough plumbing', 'Fixture setting',
                   'Steam boiler replacement', 'S Electrical', 'Panel upgrade', 'Roof condenser pad'], f'[1] each section is followed by its lines: {order}')
    c.ok(abs(r['sub'] - (1200.5 + 1950 + 124500.37 + 8200)) < 0.01, f"[1] the section subtotals add up to the subtotal: {r['sub']}")
    c.ok(r['money']['sub'] in r['totText'], '[1] the document total block shows that subtotal')
    # [2] ungrouped: the flat table, as it was
    want = ('<table><thead><tr><th class="n">#</th><th>Item</th><th class="r">Quantity</th><th class="r">Rate</th><th class="r">Amount</th></tr></thead><tbody>'
            '<tr class=""><td class="n">1</td><td>Site protection</td><td class="r">Lump sum</td><td class="r">$1,200</td><td class="r">$1,200</td></tr>'
            '<tr class=""><td class="n">2</td><td>Dumpsters<div class="ds">Twenty yard</div></td><td class="r">QTY</td><td class="r">$650</td><td class="r">$1,950</td></tr></tbody></table>')
    got = re.sub(r'<td class="r">[^<]*</td>(?=<td class="r">\$650)', '<td class="r">QTY</td>', r['uTable']).replace('<td class="r">1</td><td class="r">$1,200</td>', '<td class="r">Lump sum</td><td class="r">$1,200</td>')
    c.ok(not r['uSec'], '[2] an ungrouped estimate prints no section header')
    c.ok(got == want, f'[2] an ungrouped estimate prints the flat table unchanged:\n{got}')
    # [3] [4] Excluded and TBD
    ex = next((x for x in RG if not x['sec'] and x['cells'][1].startswith('Steam boiler')), None)
    tb = next((x for x in RG if not x['sec'] and x['cells'][1].startswith('Roof condenser')), None)
    c.ok(ex and ex['cells'][-1] == 'Excluded' and ex['muted'] and '$18,000' not in ' '.join(ex['cells']), f'[3] the excluded line prints Excluded, muted, with no price: {ex}')
    c.ok(tb and tb['cells'][-1] == 'TBD' and tb['muted'] and '$7,000' not in ' '.join(tb['cells']), f'[4] the to-be-priced line prints TBD, muted, with no price: {tb}')
    c.ok(r['amt']['g6'] == 0 and r['amt']['g7'] == 0, f"[3][4] neither counts: {r['amt']}")
    c.ok(r['bud']['g6'] == 0 and r['bud']['g7'] == 0, f"[3][4] neither carries a budget: {r['bud']}")
    c.ok(abs(r['total'] - r['sub']) < 0.01 and abs(r['total'] - 135850.87) < 0.01, f"[3] the total ignores them: {r['total']}")
    # the schedule of values built from the estimate carries no line for them
    sv = await js(pg, r"""
      const c = DB.clients.find(x => x.id === 'cl121') || DB.clients[0], G = c.estimates.find(e => e.id === 'tsecG');
      const made = typeof sovLinesFromEstimate === 'function' ? sovLinesFromEstimate(c, G, docTotal(G)) : null;
      return made ? { n: made.length, refs: made.map(v => v.lineRef.split(':').pop()), sum: r2(made.reduce((a, v) => a + v.scheduled, 0)) } : null;
    """)
    c.ok(sv and 'g6' not in sv['refs'] and 'g7' not in sv['refs'] and sv['n'] == 5 and abs(sv['sum'] - 135850.87) < 0.01,
         f'[3] the schedule of values from the estimate leaves them out and still adds up to the contract: {sv}')
    # [5] the editor
    await js(pg, "view = 'clients'; clientOpen = arg; clientTab = 'fin'; finTab = 'estimates'; docOpen = { kind: 'estimate', id: 'tsecU' }; render(); await sleep(400);",
             await js(pg, "return (DB.clients.find(x => x.id === 'cl121') || DB.clients[0]).id"))
    ed = await js(pg, r"""
      const c = DB.clients.find(x => x.id === clientOpen), d = c.estimates.find(e => e.id === 'tsecU');
      const row = id => document.querySelector(`#doc-tsecU tr[data-line="${id}"]`);
      const set = async (el, v) => { el.value = v; el.dispatchEvent(new Event('change', { bubbles: true })); await sleep(300); };
      const out = { sec: !!row('u1')?.querySelector('[data-f="group"]'), sel: [...(row('u1')?.querySelectorAll('[data-f="pricing"] option') || [])].map(o => o.textContent.trim()) };
      if (!out.sec || !out.sel.length) return out;
      await set(row('u1').querySelector('[data-f="group"]'), 'General Conditions');
      out.group = d.lines[0].group;
      const dl = row('u2').querySelector('[data-f="group"]').getAttribute('list');
      out.offered = [...document.querySelectorAll(`#${dl} option`)].map(o => o.value);
      const before = docTotal(d).total;
      await set(row('u2').querySelector('[data-f="pricing"]'), 'excluded');
      out.excluded = d.lines[1].excluded === true && !d.lines[1].tbd; out.afterEx = docTotal(d).total; out.before = before;
      out.amtCell = row('u2').querySelector('td.amt').textContent.trim();
      await set(row('u2').querySelector('[data-f="pricing"]'), 'tbd');
      out.tbd = d.lines[1].tbd === true && !d.lines[1].excluded; out.amtCellTbd = row('u2').querySelector('td.amt').textContent.trim();
      await set(row('u2').querySelector('[data-f="pricing"]'), 'priced');
      out.back = !d.lines[1].tbd && !d.lines[1].excluded; out.afterBack = docTotal(d).total; out.rate = d.lines[1].rate;
      out.sx = document.documentElement.scrollWidth - innerWidth;
      return out;
    """)
    c.ok(ed.get('sec'), '[5] each line of the simple editor has a Section input')
    c.ok(ed.get('sel') == ['Priced', 'Excluded', 'TBD'], f"[5] each line has Priced / Excluded / TBD: {ed.get('sel')}")
    c.ok(ed.get('group') == 'General Conditions', f"[5] typing a section sets it on the line: {ed.get('group')}")
    c.ok('General Conditions' in (ed.get('offered') or []), f"[5] the document's sections are offered on the other lines: {ed.get('offered')}")
    c.ok(ed.get('excluded') and ed.get('afterEx') == 1200 and ed.get('before') == 3150, f'[5] Excluded takes the line out of the total: {ed}')
    c.ok(ed.get('amtCell') == 'Excluded' and ed.get('amtCellTbd') == 'TBD', f"[5] the editor's amount says Excluded, then TBD: {ed.get('amtCell')} / {ed.get('amtCellTbd')}")
    c.ok(ed.get('tbd'), '[5] TBD replaces Excluded, never both')
    c.ok(ed.get('back') and ed.get('afterBack') == 3150 and ed.get('rate') == 650, f'[5] back to Priced restores the rate and the total: {ed}')
    c.ok((ed.get('sx') or 0) <= 1, f"[5] the editor does not scroll sideways on the desktop: {ed.get('sx')}")
    # [7] the cost code
    cc = await js(pg, r"""
      const hv = COST_CODES.find(x => /^HVAC/.test(x[1])), code = hv && hv[0];
      const p = DB.projects.find(x => x.id === 'p121') || DB.projects[0];
      const out = { code, name: hv && hv[1], inCat: !!code && LINE_CATS.construction.codes.includes(code), order: COST_CODES.map(x => x[0]),
        select: /HVAC &amp; mechanical|HVAC & mechanical/.test(catCodeCell({ cat: 'construction', code: '01', item: 'x' }, { type: 'estimate' }, 'data-f', true)),
        guess: codeForLine({ item: 'HVAC ductwork and air handler', desc: '' }), keep: codeForLine({ item: 'Rough plumbing', desc: '' }) };
      if (!code) return out;
      DB.txns.push({ id: 'tHvacT', date: today(), acct: (DB.accounts[0] || {}).id || 'ac1', desc: 'INVENTED MECHANICAL SUPPLY', amt: -812, cat: 'materials', projectId: p.id, code, vendor: '', memo: '', receipt: '', status: 'categorized', actor: '', source: 'test', line: '' });
      const row = jobFin(p).byCode.find(x => x.code === code);
      out.row = row && { name: row.name, bank: row.bank };
      setCurrent(p.id); view = 'costs'; render(); await sleep(400);
      out.screen = /HVAC & mechanical/.test((document.querySelector('#v-costs') || document.body).innerText);
      // a workspace that already gave this number to its own code keeps it; HVAC takes the next free number
      const keepCodes = JSON.stringify(COST_CODES), keepCat = LINE_CATS.construction.codes.slice(), keepCustom = DB.company.customCodes;
      DB.company.customCodes = [[code, 'Invented site security', 'construction']]; codesInit();
      const hv2 = COST_CODES.find(x => /^HVAC/.test(x[1]));
      out.clash = { own: codeName(code), hvac: hv2 && hv2[0], guess: codeForLine({ item: 'HVAC ductwork', desc: '' }), inCat: !!hv2 && LINE_CATS.construction.codes.includes(hv2[0]) && LINE_CATS.construction.codes.includes(code) };
      DB.company.customCodes = keepCustom; COST_CODES.length = 0; JSON.parse(keepCodes).forEach(x => COST_CODES.push(x)); LINE_CATS.construction.codes = keepCat; codesInit();
      out.restored = (COST_CODES.find(x => /^HVAC/.test(x[1])) || [])[0];
      DB.txns = DB.txns.filter(t => t.id !== 'tHvacT');
      return out;
    """)
    c.ok(cc.get('name') == 'HVAC & mechanical' and cc.get('code') and cc['code'] not in ('05', '99'), f'[7] there is an HVAC & mechanical cost code: {cc.get("code")} {cc.get("name")}')
    c.ok(cc.get('order') == sorted(cc.get('order') or []), f"[7] the codes stay in number order: {cc.get('order')}")
    c.ok(cc.get('inCat') and cc.get('select'), '[7] it is a construction code and is in the code select')
    c.ok(cc.get('guess') == cc.get('code') and cc.get('keep') == '05', f"[7] a new HVAC line defaults to it; plumbing stays plumbing: {cc.get('guess')} / {cc.get('keep')}")
    c.ok(cc.get('row') and cc['row']['name'] == 'HVAC & mechanical' and cc['row']['bank'] == 812, f"[7] a cost on it is on its own row in Cost by Code: {cc.get('row')}")
    c.ok(cc.get('screen'), '[7] Job Costs shows HVAC & mechanical by name')
    k = cc.get('clash') or {}
    c.ok(k.get('own') == 'Invented site security' and k.get('hvac') and k.get('hvac') != cc.get('code') and k.get('guess') == k.get('hvac') and k.get('inCat'),
         f"[7] a workspace's own code on that number keeps it and HVAC takes the next: {k}")
    c.ok(cc.get('restored') == cc.get('code'), '[7] (test tidy-up) the codes are as they were')
    c.ok(not errs, f'no page errors: {errs[:3]}')
    html = await js(pg, MAKE + "return cxDocHtml(c, G, { print: false });")
    await b.close()
    return html


async def t_phone(c, p, html):
    b = await p.chromium.launch()
    pg = await (await b.new_context(viewport=PHONE)).new_page()
    await pg.set_content(html)
    r = await pg.evaluate("""() => ({ w: innerWidth, sx: document.documentElement.scrollWidth - innerWidth,
      secs: document.querySelectorAll('tr.cx-sec').length,
      over: [...document.querySelectorAll('.cxd *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1).map(e => e.className || e.tagName).slice(0, 6) })""")
    c.ok(r['w'] == 390, f"[6] the document is laid out at 390px: {r['w']}")
    c.ok(r['secs'] == 3, f"[6] the phone document has its three section headers: {r['secs']}")
    c.ok(r['sx'] <= 1 and not r['over'], f"[6] the document does not scroll sideways at 390px: {r['sx']}px, {r['over']}")
    await b.close()


async def main():
    c = Checks()
    async with async_playwright() as p:
        html = await t_desktop(c, p)
        await t_phone(c, p, html)
    sys.exit(c.done())

asyncio.run(main())
