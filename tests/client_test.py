"""The client portal, as the client walks it (review/r5_client, round 5): phone 390x844, real taps.

Findings reproduced here, each as a check that failed the way the client reviewer saw it:
 1. "View the Sheets" opened the staff file editor (Type, Linked to, Notes, Save, Delete) and a client could
    save a note onto the firm's file. Now one read-only client viewer (image/PDF/preview, caption, Download,
    Close) opens wherever a client opens a file; every file write (save, note, link, delete) is refused for
    the client role in the functions themselves; closing the viewer keeps the approval sheet open (12).
 2. The design-phase Overview (u_cambri, 140 Prospect) printed construction cards ("Completed to Date",
    retainage, "as the crew signs it off") on an unpaid design retainer. Now: retainer hours used/left, the
    phases and their status, the deliverables and the kick-off deck with its outcomes, the survey date, the
    designer's name, and no construction card until the schedule is published; the statement prints no
    re-dating note (9); "Where the Design Stands" stacks at 390px (10).
 3. Portal actions were inbox work: a signature and a question arrived "New · Review / Ignore / Delete", the
    choice and the sample never reached Messages. Now each is one handled activity line in Project Messages,
    and a client question is a Do Now item "Answer <client>" for the PM with a drafted reply.
 4. The client's chat showed firm routing ("Assistant is reading…", "Waiting for review in Inbox", a
    "Reading 1 message…" toast). Now "Sent to Alan", and the answer when it comes.
 5. A toast sat over the sign sheet's tick for 6 s and swallowed the tap, and the error named the wrong miss.
    Now a toast never covers an open sheet's controls, dismisses on tap, and names the real miss.
 6. No Ask door for clients. Now Ask in the client header (phone and desktop), an "Ask the Assistant / Write
    to Alan" switch in Chat, and a client `pa` surface scoped by eqRows.
 7. Client Ask intents: the finish date, deciding late, the next payment, the contract with changes,
    retainage, this week's work (no crew names), photos without the photographer; for a design client the fee,
    the survey date, the kick-off outcomes, the hours used and the designer's name.
 8. Two "billed" figures. Now one: "Billed to date $238,015 after retainage ($253,684 before)", no "ex tax".
 9. (11) Pulse chips clipped with no swipe affordance: they wrap under 480px.
 Also: Already Settled lists the signed CO and the approved sample; billing's client record reads the same
 % as the portal (tpJobPct).

  python3 client_test.py        # prints ALL PASS (n checks) or each failure
"""
import asyncio, re, json, sys
from harness import *

CLICK_JS = r"""
([text, within, prefix, css, nth]) => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  let els = [...document.querySelectorAll(css || 'button, a, [role=button], .click, .tile, .gl, summary, label.btn, label')].filter(vis);
  els = els.filter(e => { const t = norm(e.innerText || e.textContent || e.getAttribute('aria-label')); return prefix ? t.startsWith(text) : t === text; });
  if (within) els = els.filter(e => { let a = e.parentElement; for (let i = 0; i < 8 && a; i++, a = a.parentElement) { if (norm(a.innerText).includes(within)) return true; } return false; });
  if (!els.length) return null;
  const e = els[nth || 0]; e.scrollIntoView({block: 'center'});
  const r = e.getBoundingClientRect(); return {x: r.x + r.width / 2, y: r.y + r.height / 2, text: norm(e.innerText).slice(0, 60), n: els.length};
}
"""
TOAST_HOOK = r"""
() => { if (window.__ctT) return; window.__ctT = []; const t = document.getElementById('toast'); if (!t) return;
  const rec = () => { const txt = (t.innerText || '').replace(/\s+/g, ' ').trim(); if (!txt) return;
    const last = window.__ctT[window.__ctT.length - 1]; if (last && last.text === txt) return; window.__ctT.push({text: txt, at: Date.now()}); };
  new MutationObserver(rec).observe(t, {childList: true, subtree: true, characterData: true, attributes: true}); }
"""
INTERNAL = re.compile(r'earned revenue|daily log|\bAngel\b|\bAlberto\b|\bTomas\b|\bCarlos\b|\bChen\b|\bRivera|Lenox|Cranberry|margin|EAC|cost basis|over.?billing|\bWIP\b|gross profit', re.I)


async def tap(pg, text, within=None, prefix=False, css=None, wait=400, nth=0):
    hit = await pg.evaluate(CLICK_JS, [text, within, prefix, css, nth])
    if not hit: return None
    await pg.wait_for_timeout(60)
    await pg.mouse.click(hit['x'], hit['y'])
    await pg.wait_for_timeout(wait)
    return hit

async def text(pg, sel='body'):
    return await pg.evaluate("s => { const e = document.querySelector(s); return e ? e.innerText : '' }", sel)

async def modal(pg):
    return await pg.evaluate("() => { const m = document.getElementById('mbm'); return m ? m.innerText : '' }")

async def toasts(pg):
    return await pg.evaluate("() => { const t = window.__ctT || []; window.__ctT = []; return t.map(x => x.text) }")

async def settle(pg, ms=7000):
    for _ in range(int(ms / 250)):
        if not await pg.evaluate("() => { const t = document.getElementById('toast'); return t && t.classList.contains('on') }"): return
        await pg.wait_for_timeout(250)

ASK = r"""
async q => { try { Object.values(DB.asst || {}).forEach(A => { if (A && typeof A === 'object') { A.thread = []; delete A.ctx; } }); } catch (e) {}
  const r = await paAsk(q); return { h: String(r && r.headline || ''), n: String(r && r.note || ''), w: (r && r.work || []).map(x => typeof x === 'string' ? x : JSON.stringify(x)), kind: r && r.kind, interp: r && r.interp } }
"""

async def ask(pg, q):
    a = await pg.evaluate(ASK, q)
    a['all'] = ' '.join([a['h'], a['n']] + a['w'])
    return a


async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, phone=True)
        await sign_in(pg, 'u_klein'); await pg.wait_for_timeout(300)
        await pg.evaluate(TOAST_HOOK)

        # ------------------------------------------------------------- 6. the Ask door (phone)
        c.ok(await pg.evaluate("() => (ROLE_VIEWS.client || []).includes('pa')"), '6: the client role has a pa view')
        c.ok(await pg.evaluate("() => { const a = document.getElementById('tb-ask'); return !!(a && !a.hidden && a.getClientRects().length) }"),
             '6: Ask shows in the client header on the phone')
        await go(pg, 'chat')
        sw = await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-clmode]')].map(b => b.innerText.trim())")
        c.ok(sw == ['Ask the Assistant', 'Write to Alan'], f'6: Chat has the "Ask the Assistant / Write to Alan" switch, got {sw}')
        if await tap(pg, 'Ask the Assistant', css='[data-clmode]'):
            c.ok(await pg.evaluate("() => view === 'pa' && !!document.getElementById('pa-in')"), '6: "Ask the Assistant" opens the client Ask surface with its input')
            nav = await pg.evaluate("() => ({ h: (document.querySelector('#pa-body .ph h2') || {}).textContent, on: [...document.querySelectorAll('#mtabs .on, #nav-groups button.on')].filter(e => e.getClientRects().length).map(e => e.innerText.trim()) })")
            c.ok(nav['h'] == 'Chat' and any(x.startswith('Chat') for x in nav['on']), f'6: Ask is one place with Chat: headed Chat, the Chat entry on: {nav}')
            pa = await text(pg)
            c.ok(not re.search(r'Connect My Account|Watching|Thinking with the firm|Records only|What Changed|Needs A Reply', pa), f'6: the client Ask surface carries no firm chrome')
            c.ok(bool(re.search(r'your job|your schedule|your account', pa, re.I)), '6: the client Ask surface says what it answers about')
            sw2 = await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-clmode]')].map(b => b.innerText.trim())")
            c.ok(sw2 == ['Ask the Assistant', 'Write to Alan'], f'6: the switch is on the Ask surface too, got {sw2}')
            await pg.fill('#pa-in', 'how much retainage are you holding'); await tap(pg, 'Send', css='#pa-ask button', wait=900)
            th = await text(pg, '#pa-thread')
            c.ok('$15,668' in th, f'6: a typed question is answered on the client Ask surface: {th[-200:]!r}')
        await go(pg, 'client')

        # ------------------------------------------------------------- 7. client Ask intents (before anything is changed)
        F = await pg.evaluate("""() => { const p = S, c = DB.clients.find(x => x.id === p.clientId), f = clientFin(c), pub = p.published;
            const tk = (p.tasks || []).find(t => /rough plumbing/i.test(t.name));
            return { finish: pub ? fmtL(pub.finish) : '', revised: money(f.revised), ret: money(f.retHeld), out: money(f.outstanding), rp: tk ? fmtL(tk.start) : '' } }""")
        a = await ask(pg, 'why did the finish date move')
        c.ok(re.search(r'did not move|has not moved|still', a['h']) and F['finish'] in a['h'], f"7: finish date did not move: {a['h']!r} (want 'no, still {F['finish']}')")
        a = await ask(pg, 'what happens if I do not pick the bathroom finishes until next week')
        c.ok('Rough plumbing' in a['all'] and F['rp'] in a['all'] and 'Nothing dated' not in a['h'], f"7: deciding late names Rough plumbing and {F['rp']}: {a['h']!r}")
        a = await ask(pg, 'when is my next payment due')
        c.ok('INV-2026-038' in a['all'] and F['out'] in a['h'] and 'Sep 15' in a['all'] and 'last payment' not in a['h'], f"7: next payment due: {a['h']!r}")
        a = await ask(pg, 'how much is my total contract now with the change orders')
        c.ok(F['revised'] in a['h'], f"7: contract with approved changes {F['revised']}: {a['h']!r}")
        a = await ask(pg, 'how much retainage are you holding')
        c.ok(F['ret'] in a['h'], f"7: retainage held {F['ret']}: {a['h']!r}")
        a = await ask(pg, 'what is the crew doing this week')
        c.ok('Nothing dated' not in a['h'] and a['kind'] != 'none' and not INTERNAL.search(a['all']), f"7: this week's work from the published schedule, no crew names: {a['h']!r} {a['w'][:3]}")
        a = await ask(pg, 'show me the latest photos')
        c.ok(a['w'] and not re.search(r'\bAngel\b|\bAlberto\b|\bTomas\b', a['all']), f"7: photo rows carry no staff name: {a['w'][:2]}")
        a = await ask(pg, 'what did the change order for the stair treads cost')
        c.ok('CO-2026-002' in a['h'] and '$1,850' in a['h'], f"7: a named change order's cost: {a['h']!r}")
        a = await ask(pg, 'how much did the Riveras pay you')
        c.ok(a['kind'] == 'blocked' and 'Rivera' not in a['h'] + a['n'], '7: another client is still refused')
        a = await ask(pg, 'what does the firm have in the bank')
        c.ok(not re.search(r'\$\s?\d', a['all']), '7: the firm\'s bank stays out of a client answer')

        # ------------------------------------------------------------- 8. one billed figure
        ov = await text(pg)
        want = await pg.evaluate("() => { const c = DB.clients.find(x => x.id === S.clientId); return { net: money(clientFin(c).invoiced), gross: money(jobFin(S).billed) } }")
        m = re.search(r'BILLED TO DATE\n([^\n]+)\n([^\n]+)', ov, re.I)
        c.ok(m and m.group(1) == want['net'] and f"after retainage ({want['gross']} before)" in m.group(2), f"8: Overview billed line reads {m and m.groups()} , want {want['net']} after retainage ({want['gross']} before)")
        c.ok('ex tax' not in ov, '8: no "ex tax" when no tax exists')
        await tap(pg, 'Account Statement', wait=800)
        st = await modal(pg)
        c.ok(f"Invoiced to date (net of retainage)\t{want['net']}" in st or (want['net'] in st and 'net of retainage' in st), '8: the statement shows the same net figure')
        await pg.evaluate("() => mbCloseModal()")

        # ------------------------------------------------------------- 9/11. Pulse chips wrap under 480px, on every client page
        for v in ('client', 'sched', 'dec', 'clacct'):
            await go(pg, v)
            g = await pg.evaluate("""() => { const w = document.querySelector('.view.on .glance.tl'); if (!w) return null;
                const ch = [...w.querySelectorAll('.gl')].filter(e => e.getClientRects().length);
                return { n: ch.length, maxRight: Math.max(...ch.map(e => Math.round(e.getBoundingClientRect().right))), rows: new Set(ch.map(e => Math.round(e.getBoundingClientRect().top))).size,
                         ox: getComputedStyle(w).overflowX, sw: w.scrollWidth, cw: w.clientWidth, clipped: ch.filter(e => e.scrollWidth > e.clientWidth + 1).length } }""")
            if g and g['n']:
                c.ok(g['maxRight'] <= 390 and g['sw'] <= g['cw'] + 1 and g['clipped'] == 0, f"11: {v}: Pulse chips fit the phone without a sideways scroll: {g}")
                if g['n'] >= 3: c.ok(g['rows'] >= 2, f"11: {v}: {g['n']} chips wrap to two rows, got {g['rows']}")

        # ------------------------------------------------------------- 1. View the Sheets: a read-only client viewer; writes refused
        await go(pg, 'client')
        c.ok(bool(await tap(pg, 'Approve', css='[data-smcl^="ok"]', wait=500)), '1: the sample approval sheet opens')
        c.ok(bool(await tap(pg, 'View the Sheets', wait=900)), '1: View the Sheets is in the approval sheet')
        v = await pg.evaluate("""() => { const vis = e => !!(e && e.getClientRects().length);
            const staff = ['vf-notes', 'vf-save', 'vf-del', 'vf-link', 'vf-cat', 'vf-share', 'vf-read'].filter(id => vis(document.getElementById(id)));
            const cv = document.getElementById('clv'); const btns = cv ? [...cv.querySelectorAll('button, a')].map(b => b.innerText.trim()).filter(Boolean) : [];
            return { staff, clv: vis(cv), btns, txt: cv ? cv.innerText : '', sheet: !!document.getElementById('mbm') } }""")
        c.ok(not v['staff'], f"1: the client sees no staff file editor controls, saw {v['staff']}")
        c.ok(v['clv'] and 'Download' in v['btns'] and 'Close' in v['btns'], f"1: a client viewer with Download and Close opened: {v['btns']}")
        c.ok(not re.search(r'Linked to|Visible to the client|Read this document|Session only|Saved on this device', v['txt']), '1: the viewer shows no firm-internal fields')
        c.ok(v['sheet'], '12: opening the sheets keeps the approval sheet open underneath')
        await tap(pg, 'Close', css='#clv button', wait=400)
        c.ok(await pg.evaluate("() => !!document.getElementById('mbm') && !(document.getElementById('clv') && document.getElementById('clv').getClientRects().length)"), '12: closing the viewer leaves the approval sheet open')
        w = await pg.evaluate("""async () => { const p = DB.projects.find(x => /121 State/.test(x.project.name)); const f = (p.files || [])[0]; const n0 = p.files.length, notes = f.notes;
            const r1 = fileUpdate(f, { notes: 'CLIENT EDITED THIS', shareClient: true }); const r2 = await fileRemove(f.id);
            return { r1, r2, same: f.notes === notes, n: p.files.length === n0, any: DB.projects.some(q => (q.files || []).some(x => /CLIENT EDITED/.test(x.notes || ''))) } }""")
        c.ok(w['r1'] is False and w['same'] and not w['any'], f"1: fileUpdate refuses the client role in the function: {w}")
        c.ok(w['r2'] is False and w['n'], f"1: fileRemove refuses the client role in the function: {w}")
        await pg.evaluate("() => mbCloseModal()")

        # ------------------------------------------------------------- 5. toasts never over an open sheet; dismiss on tap; the real miss
        await tap(pg, 'Approve', within='CO-2026-002', wait=700)
        c.ok(bool(await pg.evaluate("() => document.getElementById('pa-agree')")), '5: the sign sheet opened')
        await pg.evaluate("() => toast('Sent to your project manager', () => {})")
        await pg.wait_for_timeout(250)
        hit = await pg.evaluate("""() => { const t = document.getElementById('toast').getBoundingClientRect();
            const ctl = [...document.querySelectorAll('#mbm button, #mbm input, #mbm label, #mbm a')].filter(e => e.getClientRects().length);
            const over = ctl.filter(e => { const r = e.getBoundingClientRect(); return r.left < t.right && r.right > t.left && r.top < t.bottom && r.bottom > t.top; });
            return { on: document.getElementById('toast').classList.contains('on'), over: over.map(e => (e.id || e.innerText || e.tagName).slice(0, 30)) } }""")
        c.ok(hit['on'] and not hit['over'], f"5: the toast covers none of the sheet's controls, covers {hit['over']}")
        tb = await pg.evaluate("() => { const r = document.getElementById('toast').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2] }")
        await pg.mouse.click(tb[0], tb[1]); await pg.wait_for_timeout(200)
        c.ok(not await pg.evaluate("() => document.getElementById('toast').classList.contains('on')"), '5: a tap on the toast dismisses it')
        c.ok(await pg.evaluate("() => document.getElementById('pa-name').value.trim().length > 0"), '5: the name is prefilled')
        await tap(pg, 'Approve $', prefix=True, css='#mbm button', wait=400)
        t = await toasts(pg)
        c.ok(any(re.search(r'^Tick the box', x) for x in t) and not any('Type your name' in x for x in t), f"5: the error names the real miss (the box), got {t}")
        await pg.evaluate("() => mbCloseModal()"); await settle(pg)

        # ------------------------------------------------------------- the client's day: choice, signature, sample, question
        await go(pg, 'client')
        await tap(pg, 'Choose', within='2nd floor bathroom finishes', wait=700)
        await tap(pg, 'Zellige', prefix=True, css='#mbm *', wait=300)
        await tap(pg, 'Confirm Choice', wait=900)
        c.ok(await pg.evaluate("() => DB.projects.flatMap(p => p.decisions || []).some(d => /bathroom finishes/i.test((d.clientTitle || '') + ' ' + (d.name || '')) && d.status === 'made')"), 'day: the choice is recorded')
        await pg.evaluate("() => mbCloseModal()"); await settle(pg)
        await tap(pg, 'Approve', within='CO-2026-002', wait=700)
        await pg.evaluate("() => { const i = document.getElementById('pa-name'); i.value || (i.value = 'Sarah Klein'); }")
        box = await pg.evaluate("() => { const c = document.querySelector('#pa-agree'); const r = c.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2] }")
        await pg.mouse.click(box[0], box[1]); await pg.wait_for_timeout(200)
        await tap(pg, 'Approve $', prefix=True, css='#mbm button', wait=1000)
        c.ok(await pg.evaluate("() => DB.clients.flatMap(c => c.changeOrders || []).some(d => d.number === 'CO-2026-002' && d.status === 'approved')"), 'day: CO-2026-002 is signed')
        await pg.evaluate("() => mbCloseModal()"); await settle(pg)
        await tap(pg, 'Approve', css='[data-smcl^="ok"]', wait=500)
        await tap(pg, 'Approve', css='#mbm button', wait=900)
        c.ok(await pg.evaluate("() => { const p = DB.projects.find(x => /121 State/.test(x.project.name)); return (p.submittals || []).some(s => /garden bath/i.test(JSON.stringify(s)) && s.status === 'approved') }"), 'day: the tile sample is approved')
        await settle(pg)
        # Already Settled holds the signed CO and the approved sample
        await go(pg, 'dec'); d = await text(pg); i = d.find('Already Settled'); settled = d[i:i + 900] if i >= 0 else ''
        c.ok('CO-2026-002' in settled, f'settled: Already Settled lists the signed change order: {settled[:300]!r}')
        c.ok('Garden bathroom tile' in settled, 'settled: Already Settled lists the approved sample')
        c.ok('Zellige' in settled, 'settled: Already Settled lists the choice')
        # chat: a question
        await go(pg, 'chat'); await toasts(pg)
        await pg.fill('#chat-text', 'When will the kitchen be done? We need to plan Thanksgiving.')
        await tap(pg, 'Send', css='.view.on button', wait=1200)
        t = await toasts(pg)
        c.ok(not any('Reading' in x for x in t), f'4: no "Reading N message" toast on the client\'s phone, got {t}')
        ch = await text(pg, '#chat-list')
        c.ok('Sent to Alan' in ch, f'4: the client sees "Sent to Alan" under the question: {ch[-200:]!r}')
        c.ok(not re.search(r'Assistant is reading|Waiting for review|review in Inbox|proposed update', ch), f'4: no firm routing words in the client chat: {ch[-300:]!r}')
        await pg.wait_for_timeout(1200)
        ch = await text(pg, '#chat-list')
        c.ok(not re.search(r'Assistant is reading|Waiting for review|review in Inbox', ch), '4: still nothing of the firm\'s routing after the read')
        c.ok(not errs, f'client: no page errors: {errs[:3]}')

        # ------------------------------------------------------------- 3. the PM: Do Now and Project Messages
        await pg.set_viewport_size({'width': 1440, 'height': 900})
        await sign_in(pg, 'u_alan'); await pg.wait_for_timeout(500)
        await go(pg, 'home'); await pg.wait_for_timeout(300)
        q = await pg.evaluate("() => PRED.waitingOnMe.rows().filter(it => it.kind === 'clientq').map(it => ({ title: it.title, yes: it.yes, who: it.who }))")
        c.ok(len(q) == 1 and q[0]['title'].startswith('Answer Sarah Klein') and q[0]['yes'] == 'Answer', f'3: one Do Now item "Answer Sarah Klein" for the PM, got {q}')
        hm = await text(pg)
        c.ok('Answer Sarah Klein' in hm or 'Sarah Klein' in hm, '3: the PM\'s Home shows the client question')
        card = await pg.evaluate("() => { const el = [...document.querySelectorAll('.td-card[data-kind=\"clientq\"]')][0]; return el ? { verb: el.querySelector('[data-tdverb]').innerText.trim(), l1: el.innerText } : null }")
        c.ok(card and card['verb'] == 'Answer', f'3: the Do Now card verb is Answer: {card}')
        if card:
            await pg.click('.td-card[data-kind="clientq"] [data-tdverb]'); await pg.wait_for_timeout(500)
            draft = await pg.evaluate("() => { const t = document.querySelector('#mbm textarea'); return t ? t.value : null }")
            c.ok(draft and 'Sep 18' in draft, f'3: the reply is drafted from the published schedule (the kitchen finishes Fri, Sep 18): {draft!r}')
            c.ok(draft and not INTERNAL.search(draft), '3: the draft carries nothing internal')
            mb = await pg.evaluate("() => [...document.querySelectorAll('#mbm button')].map(b => b.innerText.trim())")
            c.ok(any(x.startswith('Send to Sarah') for x in mb), f'3: the PM sends it: {mb}')
            await tap(pg, 'Send to Sarah', prefix=True, css='#mbm button', wait=800)
            c.ok(await pg.evaluate("() => PRED.waitingOnMe.rows().filter(it => it.kind === 'clientq').length === 0"), '3: answering clears the Do Now item')
        # Project Messages: one handled line each, no Review / Ignore / Delete
        await pg.evaluate("() => { const p = DB.projects.find(x => /121 State/.test(x.project.name)); setCurrent(p.id); view = 'inbox'; render(); }"); await pg.wait_for_timeout(500)
        rows = await pg.evaluate("""() => [...document.querySelectorAll('#inbox-list .cl-msg, #inbox-list .msg')].map(m => ({ t: m.innerText.replace(/\\s+/g, ' ').slice(0, 160), btns: [...m.querySelectorAll('button')].map(b => b.innerText.trim()) }))""")
        def row(kw): return [r for r in rows if kw.lower() in r['t'].lower()]
        for kw in ('Zellige', 'CO-2026-002', 'Garden bathroom tile', 'Thanksgiving'):
            R = row(kw)
            c.ok(len(R) == 1, f'3: Project Messages holds ONE line for "{kw}", found {len(R)}: {[r["t"][:80] for r in R]}')
            c.ok(R and not any(b in ('Review', 'Ignore', 'Delete') for b in R[0]['btns']), f'3: the "{kw}" line is handled activity, no Review/Ignore/Delete: {R and R[0]["btns"]}')
        new = await pg.evaluate("() => { const p = DB.projects.find(x => /121 State/.test(x.project.name)); return (p.comms || []).filter(x => (x.source === 'portal' || x.source === 'chat') && x.status === 'new').length }")
        c.ok(new == 0, f'3: no portal or client-chat message sits "new" in the PM\'s queue, {new} do')
        c.ok(not errs, f'pm: no page errors: {errs[:3]}')

        # ------------------------------------------------------------- 4. the client sees the answer
        await pg.set_viewport_size(PHONE)
        await sign_in(pg, 'u_klein'); await go(pg, 'chat'); await pg.wait_for_timeout(300)
        ch = await text(pg, '#chat-list')
        c.ok('Sep 18' in ch and re.search(r'Alan', ch), f'4: the client reads Alan\'s answer in Chat: {ch[-300:]!r}')
        c.ok(not re.search(r'Assistant is reading|Waiting for review|review in Inbox', ch), '4: and nothing of the firm\'s routing')

        # ------------------------------------------------------------- 6. the Ask door on the desktop too
        await pg.set_viewport_size({'width': 1440, 'height': 900})
        await sign_in(pg, 'u_klein'); await go(pg, 'chat'); await pg.wait_for_timeout(300)
        c.ok(await pg.evaluate("() => { const a = document.getElementById('tb-ask'); return !!(a && !a.hidden && a.getClientRects().length) }"), '6: Ask shows in the client header on the desktop')
        sw = await pg.evaluate("() => [...document.querySelectorAll('.view.on [data-clmode]')].map(b => b.innerText.trim())")
        c.ok(sw == ['Ask the Assistant', 'Write to Alan'], f'6: the Chat switch is on the desktop too, got {sw}')
        c.ok(not errs, f'desktop: no page errors: {errs[:3]}')

        # ------------------------------------------------------------- billing's client record reads tpJobPct
        await sign_in(pg, 'u_billing')
        await pg.evaluate("() => { const c = DB.clients.find(x => /Klein/.test(x.name)); clientOpen = c.id; clientTab = 'overview'; docOpen = null; view = 'clients'; render(); }"); await pg.wait_for_timeout(500)
        pct = await pg.evaluate("() => Math.round(tpJobPct(DB.projects.find(x => /121 State/.test(x.project.name))))")
        bt = await text(pg)
        c.ok(f'{pct}% done' in bt and '0% done' not in bt, f'billing: the client record reads "{pct}% done" like the portal: {re.findall(r"[0-9]+% done", bt)}')

        # ------------------------------------------------------------- 2. the Cambris: a design-phase Overview
        await pg.set_viewport_size(PHONE)
        await sign_in(pg, 'u_cambri'); await go(pg, 'client'); await pg.wait_for_timeout(400)
        ov = await text(pg)
        c.ok(not re.search(r'Completed to Date|Retainage held|certified|crew signs it off|Completed work will appear here', ov, re.I), '2: no construction card on a design client\'s Overview before the schedule is published')
        D = await pg.evaluate("""() => { const p = S; const ph = phaseHours(p), R = retainerLeft(p); const sv = p.tasks.find(t => /survey/i.test(t.name));
            return { used: r2(ph.reduce((a, x) => a + x.used, 0)), ret: R ? R.retainer : 0, survey: sv ? fmtL(sv.start) : '', phases: ph.map(x => clPhaseName(x.line)), designer: (p.tasks.find(t => t.assignee) || {}).assignee || '' } }""")
        c.ok(f"{D['used']} hrs" in ov and re.search(r'used', ov), f"2: retainer hours used ({D['used']} hrs) on the Overview")
        c.ok(re.search(r'left|remaining', ov) and 'Retainer' in ov, '2: retainer hours left on the Overview')
        c.ok(all(ph in ov for ph in D['phases'][:3]), f"2: the phases are listed: {D['phases'][:3]}")
        c.ok('Design direction kick-off' in ov, '2: the kick-off deck is on the Overview')
        c.ok(re.search(r'Bed goes in the existing arch niche|No recessed can lighting', ov) or re.search(r'confirm', ov, re.I), '2: the kick-off outcomes (or that they are being confirmed) are on the Overview')
        c.ok(D['survey'] and D['survey'] in ov, f"2: the survey date {D['survey']} is on the Overview")
        c.ok('Sarah Davis' in ov, '2: the designer\'s name is on the Overview')
        g = await pg.evaluate("""() => { const kv = [...document.querySelectorAll('#cl-studio .cl-kv')].filter(e => e.getClientRects().length);
            const card = document.querySelector('#cl-studio .card'); const cl = card ? card.getBoundingClientRect().left : 0;
            return { n: kv.length, lefts: kv.map(e => Math.round(e.getBoundingClientRect().left - cl)), widths: kv.map(e => Math.round(e.getBoundingClientRect().width)), maxRight: Math.max(0, ...[...document.querySelectorAll('#cl-studio *')].map(e => Math.round(e.getBoundingClientRect().right))) } }""")
        c.ok(g['n'] >= 2 and all(w >= 150 for w in g['widths']) and g['maxRight'] <= 390, f'10: "Where the Design Stands" stacks at 390px: {g}')
        await tap(pg, 'Account Statement', wait=800)
        st = await modal(pg)
        c.ok('originally dated' not in st, '9: the client statement prints no re-dating note')
        await pg.evaluate("() => mbCloseModal()")
        # 7. design-client Ask intents
        a = await ask(pg, 'what is the design fee')
        c.ok('$191,800' in a['all'] and '$200' in a['all'], f"7d: the design fee: {a['h']!r}")
        a = await ask(pg, 'when is the survey')
        c.ok(D['survey'] in a['h'], f"7d: the survey date {D['survey']}: {a['h']!r}")
        a = await ask(pg, 'what did we agree at the kick-off meeting')
        c.ok(re.search(r'kick-off', a['h'], re.I) and a['kind'] != 'none', f"7d: the kick-off outcomes: {a['h']!r} {a['w'][:2]}")
        a = await ask(pg, 'how many hours has the designer spent')
        c.ok(str(D['used']) in a['h'], f"7d: hours used {D['used']}: {a['h']!r}")
        a = await ask(pg, 'who is my designer')
        c.ok('Sarah Davis' in a['h'], f"7d: the designer's name: {a['h']!r}")
        a = await ask(pg, 'when will the design be done')
        c.ok(re.search(r'being set|not set yet|once the design phases|phases are agreed', a['h'] + a['n'], re.I) and 'Sep 22' not in a['h'], f"7d: no invented finish date while the schedule is being set: {a['h']!r}")
        a = await ask(pg, 'how is 121 State Street going')
        c.ok(a['kind'] == 'blocked', '7d: another job is refused')
        c.ok(not errs, f'cambri: no page errors: {errs[:3]}')
        await b.close()
    sys.exit(c.done())

asyncio.run(main())
