"""The audit trail, as the controller and the Owner see it (BACKLOG §1.36, "Audit trail follow-ups", CoS 11-05).

line     Accounting > Books > Controls carries the audit line: the trail's row count, the last verify (who, when, what it
         found) and Verify Now. Verify Now writes its own row, and the line then names who ran it. A row edited after its
         seal is named on the line and in the toast, with Open the Record to the record it is about. Only the
         controller and the Owner may run it (the PM is refused and no row is written). Desktop and the 390px phone,
         no sideways scroll, no blue Verify Now (the page's one blue is the close).
close    The month close runs verify first: an edited row blocks it, and the refusal names the row; nothing is posted or
         locked. A clean close records DB.auditHead in its close record. Re-sealing the whole trail after an edit is then
         caught at the next verify, because the row at the recorded head no longer carries the recorded seal.
reattr   The boot re-attribution of a sealed seed approval is a new row whose action reads "re-attributed", never
         "approve".
owner    The demo owner is a person with a name, not the role's word ("Owner").
The close's own blockers (bank lines, bills, the WIP tie) are chain_test's; here they are stubbed so the gate under
test is the audit check alone."""
import asyncio, sys
from harness import *

LINE = r"""() => { const el = document.getElementById('au-line'); if (!el) return null;
  const b = el.querySelector('[data-auverify]');
  return { text: el.innerText, btn: b ? b.innerText.trim() : '', blue: !!el.querySelector('.btn.primary'), open: !!el.querySelector('[data-auopen]'),
    sw: document.scrollingElement.scrollWidth, w: innerWidth, rows: DB.audit.length }; }"""


async def main():
    c = Checks()
    async with async_playwright() as p:
        for phone in (False, True):
            dev = 'phone' if phone else 'desktop'
            b, pg, errs = await open_app(p, phone)
            await sign_in(pg, 'u_controller')
            await go(pg, 'verify')
            L = await pg.evaluate(LINE)
            c.ok(L is not None, f'{dev}: Controls carries the audit line')
            if L:
                c.ok(f"{L['rows']:,} rows" in L['text'].replace('\n', ' ').lower() or f"{L['rows']:,} ROWS" in L['text'], f"{dev}: the line states the trail's row count ({L['rows']}): {L['text'][:160]!r}")
                c.ok(L['btn'] == 'Verify Now' and not L['blue'], f"{dev}: Verify Now is there and not blue: {L['btn']!r} blue={L['blue']}")
                c.ok(L['sw'] <= L['w'], f"{dev}: no sideways scroll on Controls ({L['sw']} > {L['w']})")
            n0 = await pg.evaluate('DB.audit.length')
            await pg.click('#au-line [data-auverify]')
            await pg.wait_for_timeout(250)
            L2 = await pg.evaluate(LINE)
            last = await pg.evaluate("() => { const a = DB.audit[DB.audit.length - 1]; return { kind: a.kind, action: a.action, by: a.by, ok: a.after && a.after.ok }; }")
            toast = await pg.evaluate("document.getElementById('toast').innerText")
            c.ok(last['kind'] == 'audit' and last['action'] == 'verify' and last['ok'] and last['by'] == 'Controller' and await pg.evaluate('DB.audit.length') == n0 + 1,
                 f'{dev}: Verify Now writes its own row, by the controller: {last}')
            c.ok(L2 and 'Last verified by Controller' in L2['text'] and 'intact' in L2['text'], f"{dev}: the line names the last verify, who and the result: {L2 and L2['text'][:200]!r}")
            c.ok('Audit trail verified' in toast and 'Open' in toast, f'{dev}: the toast says what happened, with Open: {toast!r}')
            # a row edited after its seal: the line and the toast name it, with the record
            r = await pg.evaluate("""() => { const k = DB.audit.findIndex(a => a.kind === 'bill'); window.__k = k; window.__was = DB.audit[k].note; DB.audit[k].note = 'changed quietly'; return { k, id: DB.audit[k].refId }; }""")
            await pg.click('#au-line [data-auverify]')
            await pg.wait_for_timeout(250)
            L3 = await pg.evaluate(LINE)
            toast = await pg.evaluate("document.getElementById('toast').innerText")
            num = await pg.evaluate("id => (DB.bills.find(b => b.id === id) || {}).number", r['id'])
            c.ok(L3 and 'does not verify' in L3['text'] and f"row {r['k'] + 1}" in L3['text'] and num in L3['text'] and 'edited' in L3['text'], f"{dev}: the line names the edited row and its bill {num}: {L3 and L3['text'][:300]!r}")
            c.ok('does not verify' in toast and num in toast, f'{dev}: the toast names it: {toast!r}')
            c.ok(L3 and L3['open'], f'{dev}: Open the Record is on the line')
            if L3 and L3['open']:
                await pg.click('#au-line [data-auopen]')
                await pg.wait_for_timeout(400)
                v = await pg.evaluate("view")
                c.ok(v == 'ap', f'{dev}: Open the Record opens the bill on Bills and Payroll ({v})')
            await pg.evaluate("() => { DB.audit[window.__k].note = window.__was; }")
            c.ok(not errs, f'{dev}: no page errors: {errs[:3]}')
            await b.close()

        b, pg, errs = await open_app(p)
        # read-only for everyone but the controller and the Owner
        await sign_in(pg, 'u_alan')
        r = await pg.evaluate("() => { const n = DB.audit.length; acAuditVerifyNow(); return { n0: n, n1: DB.audit.length, toast: document.getElementById('toast').innerText, html: acAuditLineHtml() }; }")
        c.ok(r['n1'] == r['n0'] and 'Only the controller or the Owner' in r['toast'] and 'data-auverify' not in r['html'], f'the PM cannot run the check (no row, no button): {r}')

        # the close runs verify, and records the head
        await sign_in(pg, 'u_owner')
        await go(pg, 'gl')
        r = await pg.evaluate("""() => { fin2CloseBlockers = () => [];
          const k = DB.audit.findIndex(a => a.kind === 'bill'), was = DB.audit[k].note, locked0 = (DB.periods || {}).lockedThrough || '', j0 = DB.gl.journals.length;
          DB.audit[k].note = 'changed quietly';
          const bad = fin2RunClose('2026-08', 'audit check');
          const after = { locked: (DB.periods || {}).lockedThrough || '', journals: DB.gl.journals.length, row: DB.audit[DB.audit.length - 1] };
          DB.audit[k].note = was;
          const good = fin2RunClose('2026-08', 'audit check');
          const rec = good && good.rec, head = rec && rec.auditHead, A = DB.audit, at = head ? A.find(x => +x.n === head.n) : null;
          return { k, bad: { ok: bad.ok, why: bad.why }, locked0, j0, after: { locked: after.locked, journals: after.journals, action: after.row.action, ok: after.row.after && after.row.after.ok },
            good: !!(good && good.ok), head, atOk: !!(at && at.h === head.h), verify: auditVerify().ok }; }""")
        c.ok(not r['bad']['ok'] and 'audit trail does not verify' in (r['bad']['why'] or '') and f"row {r['k'] + 1}" in r['bad']['why'], f"a close over an edited row is blocked and says why: {r['bad']}")
        c.ok(r['after']['locked'] == r['locked0'] and r['after']['journals'] == r['j0'], f"the blocked close posted nothing and locked nothing: {r['after']}")
        c.ok(r['after']['action'] == 'verify' and r['after']['ok'] is False, f"the close's verify is its own row on the trail: {r['after']}")
        c.ok(r['good'] and r['head'] and r['atOk'] and r['verify'], f"a clean close records DB.auditHead in its close record and the trail verifies: {r}")
        r = await pg.evaluate("""() => { const k = DB.audit.findIndex(a => a.kind === 'bill'); DB.audit[k].note = 'changed and re-sealed';
          DB.audit.forEach(a => { delete a.h; delete a.n; delete a.prev; }); DB.auditHead = null; auditSeal();
          const V = auditVerify(); return { ok: V.ok, why: V.broken[0] && V.broken[0].why, words: auditBrokenWords(V) }; }""")
        c.ok(not r['ok'] and 'August 2026 close' in (r['why'] or '') and 're-sealed' in (r['why'] or ''), f're-sealing the whole trail after the close is caught by the recorded head: {r}')
        await go(pg, 'verify')
        await pg.click('#au-line [data-auverify]')
        await pg.wait_for_timeout(250)
        t = await pg.evaluate("document.getElementById('au-line').innerText")
        c.ok('does not verify' in t and 'August 2026 close' in t and 'Last verified by' in t, f"Controls' Verify Now shows it: {t[:300]!r}")

        # the boot re-attribution of a sealed approval reads "re-attributed"
        r = await pg.evaluate("""() => { const j = DB.gl.journals.find(x => x.kind === 'opening' && x.seedSigned);
          if (!j) return { none: true };
          j.approvedBy = 'Someone'; audit('ledger', j.id, 'approve', null, null, 'seeded', { by: 'Someone', role: 'owner' }); auditSeal();
          fin2SeedSignOpening(); auditSeal();
          const R = DB.audit.filter(a => a.refId === j.id && /re-attributed/.test(a.note || ''));
          return { rows: R.map(a => a.action), approveBySeed: DB.audit.filter(a => a.refId === j.id && a.action === 'approve' && a.by === FIN3_SEED).length }; }""")
        c.ok(not r.get('none') and r['rows'] and all(a == 're-attributed' for a in r['rows']), f'the re-attribution row reads "re-attributed", not "approve": {r}')

        # the demo owner is a person
        r = await pg.evaluate("() => { const u = DB.users.find(x => x.id === 'u_owner'); return { name: u.name, me: S.project.userName }; }")
        c.ok(r['name'] and r['name'] != 'Owner' and ' ' in r['name'] and r['me'] == r['name'], f"the demo owner has a person's name: {r}")
        c.ok(not errs, f'no page errors: {errs[:3]}')
        await b.close()
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
