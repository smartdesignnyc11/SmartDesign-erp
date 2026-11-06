"""tasks_pm: the PM's and the owner's side of tasks on the phone (lane T2, 2026-11-05). The PM role expert scored the
phone 5/10 and the owner 6/10 (scratchpad tasks_review/pm/ and the capture of every task screen); each check below
fails the way they saw it, at 390x844 with touch, and then holds the class on the neighbouring roles.

  meet     S1  A PM starts a site meeting for their job (it was "The owner or the coordinator starts the team
               meeting"); its agenda is that job only. Paste Notes reads plain bullets ("Angel to X by Friday",
               "Angel: check bolts Fri", "[Chen] Order ...") as action items with owner and date, and matches the job
               from "121 State Street" in the title or the notes.
  counts   S2  The job's Tasks is the one task list filtered to the job (it was the old list: 4 open, Overdue 0);
               the Tasks number is one function (tkTasksN) on the phone bar, the side menu and the list's Due Soon
               chip, for every office role; the Team view's count per person equals Mine for that person; a pending
               hand-off counts in Waiting and its rows.
  quick    S2  Quick add: the first person named owns it ("Angel check ..." was Alan's); "Tell Angel to ..." keeps the
               verb and the name; record numbers link the record and its job; chips show owner, job, due and the
               link before saving, and a tap corrects one; one parser (tkRefsIn) for every quick add.
  offer    S2  After Hand Off the sender's row says "Offered to Chen", Waiting counts it, Take Back ends it.
  link     S2  Link a Record lists the job's change orders, POs, estimates and invoices first with their amounts
               (bills read $0), and finds a number by search.
  sheet    S2  The task sheet's first screen is Due, Owner, Remind and Hand Off; "Move the Date" is gone (Due sets
               it); Remind sets a time and fires once through the app's reminder path; Mark Done is the blue button;
               Edit's old form is not a way in.
  mmadd    S2  Meeting Mode's add line reads the sentence with the quick-add parser (owner, due), "by Friday" leaves
               the title, and the end dialog sets each missing date.
  ask      S2  "What do I owe the Kleins" answers from tasks, not AR; Owed to a Client and Owed by the Crew filters.
  bar      S2  The owner's phone bar has Tasks, and the Tasks tab carries the Tasks number for each office role.
  swipe    S3  Swipe right is Done; swipe left opens Later, Reschedule and Hand Off with the title still in view;
               at 130% text the header's Ask is not cut off; the active filter shows as a removable chip; a search
               does not stick after leaving Tasks.
Invented demo data only."""
import asyncio, os, re, sys
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT

SHOTS = os.path.join(ROOT, 'review', 'tasks_pm')
os.makedirs(SHOTS, exist_ok=True)
CLOSE = "() => { try { tvPopClose && tvPopClose(); } catch (e) {} try { mbCloseModal(); } catch (e) {} document.querySelectorAll('#mbm, #tv-pop').forEach(e => e.remove()); }"
ONLY = set(sys.argv[1:])
VIS = "e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden'"
SWIPE = """([key, dx]) => { const el = document.querySelector(`#tkall-body .tk2-row[data-tkkey="${key}"]`); if (!el) return 'no row';
  const r = el.getBoundingClientRect(), x = r.left + r.width * (dx < 0 ? 0.8 : 0.2), y = r.top + r.height / 2;
  const mk = (X) => new Touch({ identifier: 1, target: el, clientX: X, clientY: y });
  el.dispatchEvent(new TouchEvent('touchstart', { touches: [mk(x)], bubbles: true }));
  for (let i = 1; i <= 6; i++) el.dispatchEvent(new TouchEvent('touchmove', { touches: [mk(x + dx * i / 6)], bubbles: true }));
  el.dispatchEvent(new TouchEvent('touchend', { touches: [], bubbles: true })); return 'ok'; }"""


async def shot(pg, name):
    await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))


async def toast(pg):
    return await pg.evaluate("() => (document.getElementById('toast') || {}).innerText || ''")


async def add_line(pg, text):
    i = pg.locator('#tkall-body [data-tvqa]').first
    await i.fill(text)
    await pg.wait_for_timeout(150)
    chips = await pg.evaluate("() => [...document.querySelectorAll('#tkall-body [data-tvqchips] .tvqc')].map(b => b.innerText.replace(/\\s+/g, ' ').trim())")
    await i.press('Enter')
    await pg.wait_for_timeout(300)
    return chips


async def rec_of(pg, words):
    return await pg.evaluate("""w => { const x = tkAll().find(t => (t.title || '').includes(w)); if (!x) return null; const R = tkResolve(x.key);
      return { key: x.key, title: x.title, owner: (R.rec || {}).assignee || x.owner, offeredTo: x.offeredTo || '', pid: x.projectId || '', due: x.due || '', links: (typeof tkLinks === 'function' ? tkLinks(R.rec || {}) : []).map(l => l.kind + ':' + l.id) }; }""", words)


async def meet(c, pg):
    # S1: the PM runs a site meeting for their job
    await sign_in(pg, 'u_alan')
    await pg.evaluate("setCurrent('p121')"); await go(pg, 'tasks'); await pg.wait_for_timeout(250)
    line = await pg.evaluate("() => { const b = document.querySelector('#tkall-body [data-mmstartline=\"site\"]'); return b ? b.innerText.replace(/\\s+/g, ' ') : null; }")
    c.ok(line and 'Site Meeting' in line, f'meet: the PM sees Start a Site Meeting on the job’s Tasks ({line})')
    await pg.evaluate("() => { const b = document.querySelector('#tkall-body [data-mmstartline=\"site\"]'); b && b.click(); }")
    await pg.wait_for_timeout(250)
    await shot(pg, 'pm_site_start')
    t = await pg.evaluate("() => (document.querySelector('#mbm') || {}).innerText || ''")
    c.ok('Start a Site Meeting' in t and '121 State' in t, f'meet: the site meeting dialog opens on the job ({t[:120]!r})')
    await pg.evaluate("() => document.querySelector('#mbm-ok').click()"); await pg.wait_for_timeout(500)
    m = await pg.evaluate("() => { const m = mtCurrent(); return m ? { title: m.title, boards: m.agenda.map(b => b.board), pid: m.projectId, site: !!m.site } : null; }")
    c.ok(m and m['site'] and m['boards'] == ['p:p121'] and m['pid'] == 'p121', f'meet: the PM’s site meeting walks 121 State only ({m})')
    await shot(pg, 'pm_site_meeting')
    # the add line: one sentence, chips, the date out of the title
    await pg.evaluate("() => { const b = document.querySelector('[data-mmact=\"add\"]'); b && b.click(); }"); await pg.wait_for_timeout(250)
    inp = pg.locator('[data-mmaddt]').first
    ok = await inp.count()
    c.ok(ok, 'mmadd: Meeting Mode has its add line')
    if ok:
        await inp.fill('Angel sister the two notched joists in the garden bath by Friday'); await pg.wait_for_timeout(200)
        chips = await pg.evaluate("() => [...document.querySelectorAll('[data-mmaddchips] .tvqc')].map(b => b.innerText.replace(/\\s+/g, ' ').trim())")
        await shot(pg, 'pm_mm_add_chips')
        c.ok(any('Angel' in x for x in chips) and any(re.search(r'Due.*(Fri|Sep 4)', x) for x in chips), f'mmadd: the add line shows owner Angel and the Friday date as chips ({chips})')
        sel = await pg.evaluate("() => !!document.querySelector('.mm-addo, [data-mmaddo]')")
        c.ok(not sel, 'mmadd: no bare owner dropdown')
        await pg.evaluate("() => document.querySelector('[data-mmadd]').click()"); await pg.wait_for_timeout(400)
        r = await rec_of(pg, 'notched joists')
        c.ok(r and 'by Friday' not in r['title'] and r['due'] == '2026-09-04' and 'Angel' in (r['owner'] or ''), f'mmadd: saved with owner Angel, due Fri 9/4, "by Friday" out of the title ({r})')
    # an undated item: the end dialog sets its date
    await pg.evaluate("() => { const b = document.querySelector('[data-mmact=\"add\"]'); b && b.click(); }"); await pg.wait_for_timeout(200)
    if await pg.locator('[data-mmaddt]').count():
        await pg.locator('[data-mmaddt]').first.fill('Chen chase the window shop drawings'); await pg.wait_for_timeout(150)
        await pg.evaluate("() => document.querySelector('[data-mmadd]').click()"); await pg.wait_for_timeout(300)
    await pg.evaluate("() => mmEndDialog()"); await pg.wait_for_timeout(300)
    await shot(pg, 'pm_mm_end')
    nd = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-mmnd]')].map(b => b.dataset.mmnd)")
    c.ok(len(nd) >= 1, f'mmadd: the end dialog offers Set Date for each task with no date ({nd})')
    if nd:
        await pg.evaluate("c => document.querySelector(`#mbm [data-mmnd=\"${c}\"]`).click()", nd[0]); await pg.wait_for_timeout(250)
        await pg.evaluate("() => { const b = [...document.querySelectorAll('#tv-pop button')].find(b => /Tomorrow/.test(b.innerText)); b && b.click(); }"); await pg.wait_for_timeout(400)
        due = await pg.evaluate("c => (tkByCode(c) || {rec: {}}).rec.due || ''", nd[0])
        c.ok(due == '2026-09-04', f'mmadd: Set Date in the end dialog dates it ({nd[0]} due {due!r})')
    await pg.evaluate(CLOSE)
    await pg.evaluate("() => { const m = mtCurrent(); m && mtEnd(m); }")
    # Paste Notes: plain bullets and the job from the title
    NOTES = "Site meeting 121 State Street, Sep 3\nPresent: Alan, Angel, Chen\n- Angel to sister the two notched joists in the garden bath by Friday\n- Chen: order the 3rd floor lighting Mon\n- [Alan] Send the CO for the joist extra to the Kleins tomorrow\nAngel: check bolts Fri"
    for title, tag in (('121 State Street site meeting', 'title'), ('', 'text')):
        # the PM's way in: Messages > Meetings > Paste Notes
        await sign_in(pg, 'u_alan'); await go(pg, 'meetings'); await pg.wait_for_timeout(250)
        await pg.evaluate("() => { const b = document.querySelector('#mt-paste') || document.querySelector('[data-ydmtpaste]'); b && b.click(); }"); await pg.wait_for_timeout(300)
        await pg.evaluate("([t, n]) => { const m = document.getElementById('mbm'); m.querySelector('[data-f=\"title\"]').value = t; m.querySelector('[data-f=\"text\"]').value = n; m.querySelector('#mbm-ok').click(); }", [title, NOTES])
        await pg.wait_for_timeout(600)
        r = await pg.evaluate("() => { const m = DB.meetings[DB.meetings.length - 1]; return { pid: m.projectId, steps: (m.steps || []).map(s => [s.owner, s.title, s.detail]), tasks: (m.proposals || []).filter(p => p.kind === 'task' || p.kind === 'update').map(p => [p.apply.assignee || p.apply.owner, p.apply.due]) }; }")
        if tag == 'title': await shot(pg, 'pm_paste_notes')
        c.ok(r['pid'] == 'p121', f'meet: pasted notes ({tag}) match 121 State Street ({r["pid"]!r})')
        c.ok(len(r['steps']) >= 4 and {s[0].split(' ')[0] for s in r['steps']} >= {'Angel', 'Chen', 'Alan'}, f'meet: plain bullets ({tag}) read as action items with owners ({r["steps"]})')
        c.ok(len([t for t in r['tasks'] if t[1]]) >= 3, f'meet: the action items ({tag}) carry their dates ({r["tasks"]})')


async def quick(c, pg):
    await sign_in(pg, 'u_alan'); await go(pg, 'tkall'); await pg.wait_for_timeout(250)
    chips = await add_line(pg, 'Angel check joist sistering at 121 State tomorrow 8am')
    c.ok(any('Owner' in x and 'Angel' in x for x in chips) and any('121 State' in x for x in chips) and any('Due' in x and 'Tomorrow' in x for x in chips), f'quick: chips show owner Angel, the job and the date before saving ({chips})')
    r = await rec_of(pg, 'joist sistering')
    c.ok(r and ('Angel' in (r['owner'] or '') or 'Angel' in r['offeredTo']) and r['pid'] == 'p121', f'quick: the first person named owns it (or has it offered), on 121 State ({r})')
    c.ok(r and not r['title'].lower().startswith('angel'), f'quick: the name leaves the title ({r and r["title"]})')
    await add_line(pg, 'Tell Angel to photograph the rear wall')
    r = await rec_of(pg, 'photograph the rear wall')
    c.ok(r and r['title'].startswith('Tell Angel to photograph'), f'quick: "Tell Angel to ..." keeps its verb and name ({r and r["title"]})')
    # a record number links the record and names the job
    co = await pg.evaluate("() => { for (const c of DB.clients) for (const d of (c.changeOrders || [])) if (d.projectId) return { n: d.number, id: d.id, pid: d.projectId }; return null; }")
    if co:
        chips = await add_line(pg, f'Chen order the radiant mats for {co["n"]} by Friday')
        c.ok(any(co['n'] in x for x in chips), f'quick: the chips show the linked {co["n"]} ({chips})')
        r = await rec_of(pg, 'radiant mats')
        c.ok(r and f'co:{co["id"]}' in r['links'] and r['pid'] == co['pid'], f'quick: {co["n"]} is linked and names its job ({r})')
    # a tap corrects a chip: the job
    i = pg.locator('#tkall-body [data-tvqa]').first
    await i.fill('Call the tile setter about the grout'); await pg.wait_for_timeout(150)
    await pg.evaluate("() => document.querySelector('#tkall-body [data-tvqc=\"pid\"]').click()"); await pg.wait_for_timeout(200)
    await shot(pg, 'pm_quick_chip_pick')
    await pg.evaluate("() => { const b = document.querySelector('#tv-pop [data-tvqcp=\"p121\"]'); b && b.click(); }"); await pg.wait_for_timeout(150)
    chips = await pg.evaluate("() => [...document.querySelectorAll('#tkall-body [data-tvqchips] .tvqc')].map(b => b.innerText.replace(/\\s+/g, ' ').trim())")
    await i.press('Enter'); await pg.wait_for_timeout(300)
    r = await rec_of(pg, 'tile setter about the grout')
    c.ok(r and r['pid'] == 'p121', f'quick: a tap on the Job chip corrects it before saving ({chips}, {r and r["pid"]})')
    # a name owns the task only when the sentence starts with it (chief of staff 11-06): anywhere else it stays in the
    # title as said, possessives included, and the speaker owns it; the Owner chip offers the people named first
    P = await pg.evaluate("""() => ["Call Wren about Angel's hours", "Order tile for Sarah's selection at 206 Lenox", 'Angel: check the bolts Friday', 'Sarah to confirm the tile selection'].map(t => { const r = tvQaParse(t); return { t, title: r.title, owner: r.owner, named: r.named }; })""")
    me = await pg.evaluate("() => tkMe()")
    c.ok(P[0]['title'] == "Call Wren about Angel's hours" and P[0]['owner'] == me and 'Angel' in (P[0]['named'] or []), f'quick: a name inside the sentence stays in the title, and the speaker owns it ({P[0]})')
    c.ok(P[1]['title'].startswith("Order tile for Sarah's selection") and P[1]['owner'] == me, f'quick: a possessive stays whole ({P[1]})')
    c.ok(P[2]['owner'] == 'Angel' and P[2]['title'].lower().startswith('check the bolts') and P[3]['owner'].startswith('Sarah') and P[3]['title'].startswith('Confirm'), f'quick: a name that starts the sentence owns it ({P[2:]})')
    i = pg.locator('#tkall-body [data-tvqa]').first
    await i.fill("Call Wren about Angel's hours"); await pg.wait_for_timeout(150)
    await pg.evaluate("() => document.querySelector('#tkall-body [data-tvqc=\"owner\"]').click()"); await pg.wait_for_timeout(200)
    first = await pg.evaluate("() => { const b = [...document.querySelectorAll('#tv-pop [data-tvp], #tv-pop .tv-person')].filter(e => e.getClientRects().length)[0]; return b ? b.innerText.replace(/\\s+/g, ' ') : ''; }")
    c.ok('Angel' in first, f'quick: the Owner chip offers the person named first ({first!r})')
    await pg.evaluate(CLOSE); await i.fill('')
    # the mic: what is heard redraws the chips before saving
    await pg.evaluate("""() => { window.SpeechRecognition = function () { const r = this; r.start = () => setTimeout(() => { r.onresult && r.onresult({ results: [Object.assign([{ transcript: 'Angel check the gutters at 121 State tomorrow' }], { isFinal: true })] }); r.onend && r.onend(); }, 30); }; }""")
    await pg.evaluate("() => document.querySelector('#tkall-body [data-tvqamic]').click()"); await pg.wait_for_timeout(300)
    chips = await pg.evaluate("() => [...document.querySelectorAll('#tkall-body [data-tvqchips] .tvqc')].map(b => b.innerText.replace(/\\s+/g, ' ').trim())")
    c.ok(any('Angel' in x for x in chips) and any('121 State' in x for x in chips), f'quick: the mic fills the line and the chips show the parse before saving ({chips})')
    await i.fill('')
    one = await pg.evaluate("() => typeof tkRefsIn === 'function' && tkRefsIn('PO-2026-041 and INV-2026-031').length === 2")
    c.ok(one, 'quick: one record-number parser (tkRefsIn) reads PO and INV numbers')


async def offer(c, pg):
    await sign_in(pg, 'u_alan'); await go(pg, 'tkall'); await pg.wait_for_timeout(250)
    k = await pg.evaluate("() => { const x = openTasks('me').find(t => t.kind === 'action' && !t.waitsOn); return x ? t2Key(x) : null; }")
    c.ok(k, 'offer: the PM has an open task to hand off')
    if not k: return
    before = await pg.evaluate("() => tkMyCounts().blocked")
    await pg.evaluate("k => tkHandSheet(k)", k); await pg.wait_for_timeout(200)
    await pg.evaluate("() => { const b = [...document.querySelectorAll('#mbm [data-tkhto]')].find(b => /Chen/.test(b.dataset.tkhto)); b && b.click(); document.querySelector('#mbm-ok').click(); }")
    await pg.wait_for_timeout(400)
    await go(pg, 'tkall'); await pg.evaluate("() => { t2View = 'all'; renderTkAll(); }"); await pg.wait_for_timeout(250)
    row = await pg.evaluate("k => { const r = document.querySelector(`#tkall-body .tk2-row[data-tkkey=\"${k}\"]`); return r ? r.innerText.replace(/\\s+/g, ' ') : null; }", k)
    await shot(pg, 'pm_offered_row')
    c.ok(row and 'Offered to Chen' in row, f'offer: the sender’s row says Offered to Chen ({row})')
    after = await pg.evaluate("() => tkMyCounts().blocked")
    inwait = await pg.evaluate("k => t2ViewOf(openTasks('me'), 'blocked').some(x => t2Key(x) === k)", k)
    c.ok(after == before + 1 and inwait, f'offer: Waiting counts the pending hand-off and lists it ({before} -> {after}, listed {inwait})')
    mine = await pg.evaluate("() => tkOfferedByMe().length")
    c.ok(mine >= 1, f'offer: tkOfferedByMe lists it ({mine})')
    await pg.evaluate("k => tkSheet(k)", k); await pg.wait_for_timeout(300)
    tb = await pg.evaluate("() => !!document.querySelector('#mbm [data-tvtakeback]')")
    c.ok(tb, 'offer: the sheet has Take Back for the sender')
    await shot(pg, 'pm_offer_sheet')
    if tb:
        await pg.evaluate("() => document.querySelector('#mbm [data-tvtakeback]').click()"); await pg.wait_for_timeout(300)
        st = await pg.evaluate("k => (tkResolve(k).rec.handoff || {}).state", k)
        c.ok(st == 'taken-back' and 'Taken back' in await toast(pg), f'offer: Take Back ends the offer, with a toast ({st})')
    await pg.evaluate(CLOSE)


async def link(c, pg):
    await sign_in(pg, 'u_alan'); await go(pg, 'tkall')
    k = await pg.evaluate("() => { const x = tkAll().find(t => t.kind === 'action' && t.projectId === 'p121' && !t.done); return x ? x.key : null; }")
    await pg.evaluate("k => tkLinkDialog(k)", k); await pg.wait_for_timeout(250)
    await shot(pg, 'pm_link_record')
    L = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-tklk]')].map(b => [b.dataset.tklk.split('|')[0], b.innerText.replace(/\\s+/g, ' ')])")
    kinds = [x[0] for x in L]
    c.ok(L and kinds[0] in ('co', 'po') and 'vendor' not in kinds[:6], f'link: the job’s records come first, vendors last ({kinds[:8]})')
    c.ok({'co', 'estimate', 'invoice'} <= set(kinds), f'link: change orders, estimates and invoices can be linked ({sorted(set(kinds))})')
    bills = [x[1] for x in L if x[0] == 'bill']
    c.ok(not any(re.search(r'\\$0(\\.00)?\\b', b) for b in bills), f'link: bills show their amounts ({bills[:3]})')
    await pg.evaluate("() => { const q = document.querySelector('#mbm [data-tklq]'); q.value = 'INV-2026-031'; q.oninput(); }"); await pg.wait_for_timeout(150)
    f = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-tklk]')].map(b => b.innerText.replace(/\\s+/g, ' '))")
    c.ok(len(f) == 1 and 'INV-2026-031' in f[0], f'link: search finds an invoice by number ({f})')
    await pg.evaluate("() => document.querySelector('#mbm [data-tklk]').click()"); await pg.wait_for_timeout(300)
    t = await toast(pg)
    c.ok('linked to Invoice INV-2026-031' in t, f'link: linking toasts what it linked ({t!r})')
    await pg.evaluate(CLOSE)


async def sheet(c, pg):
    await sign_in(pg, 'u_alan'); await go(pg, 'tkall'); await pg.wait_for_timeout(250)
    k = await pg.evaluate("() => { const x = openTasks('me').find(t => t.kind === 'action'); return x ? t2Key(x) : null; }")
    await pg.evaluate("k => tkSheet(k)", k); await pg.wait_for_timeout(400)
    await shot(pg, 'pm_sheet_first')
    s = await pg.evaluate("""() => { const m = document.getElementById('mbm'), vis = """ + VIS + """, bd = m.querySelector('.mbm-bd') || m;
      const H = bd.getBoundingClientRect().bottom;
      const firstScreen = [...m.querySelectorAll('[data-tvsf]:not([data-tvsf="status"]), [data-tkshandopen]')].filter(e => vis(e) && e.getBoundingClientRect().bottom <= H).map(e => e.dataset.tvsf || 'hand');
      return { first: firstScreen, move: [...m.querySelectorAll('.tks-h')].some(h => vis(h) && /Move the Date/.test(h.textContent)),
        ok: (m.querySelector('#mbm-ok') || {}).textContent, edit: !!m.querySelector('[data-tksedit]'), next: (m.querySelector('[data-tvsnext]') || {}).textContent || '' }; }""")
    c.ok(s['first'][:3] == ['due', 'owner', 'remind'] and 'hand' in s['first'], f'sheet: the first screen leads with Due, Owner, Remind and Hand Off ({s["first"]})')
    c.ok(not s['move'], 'sheet: Move the Date is gone (Due sets the date)')
    c.ok(s['ok'] == 'Mark Done' and not s['edit'], f'sheet: the blue button is Mark Done, the old Edit form is not offered ({s["ok"]!r}, next {s["next"]!r})')
    # Remind at a set time fires once through the app's reminder path
    await pg.evaluate("() => document.querySelector('#mbm [data-tvsf=\"remind\"]').click()"); await pg.wait_for_timeout(200)
    await shot(pg, 'pm_sheet_remind')
    await pg.evaluate("() => { const p = document.getElementById('tv-pop'); p.querySelector('[data-tvrmd]').value = today(); p.querySelector('[data-tvrmt]').value = '23:59'; p.querySelector('[data-tvrmset]').click(); }")
    await pg.wait_for_timeout(300)
    rm = await pg.evaluate("k => tkResolve(k).rec.remind", k)
    c.ok(rm and rm['at'].endswith('T23:59') and not rm['sent'] and await pg.evaluate("() => tvRemindSweep()") == 0, f'sheet: Remind keeps a day and time, and waits for it ({rm})')
    await pg.evaluate(CLOSE)
    # the app's clock passes the time (moved back rather than waiting): it fires once
    await pg.evaluate("k => { tkResolve(k).rec.remind.at = today() + 'T00:01'; }", k)
    n = await pg.evaluate("() => tvRemindSweep()")
    t = await toast(pg)
    rm = await pg.evaluate("k => tkResolve(k).rec.remind", k)
    c.ok(n == 1 and 'Reminder' in t and rm['sent'], f'sheet: the reminder fires once when the time comes ({n}, {t!r})')
    c.ok(await pg.evaluate("() => tvRemindSweep()") == 0, 'sheet: and never twice')
    c.ok('was due' in t and rm.get('late'), f'sheet: a reminder that fires after its time says when it was due ({t!r})')
    # the Remind sheet says where it works
    await pg.evaluate("k => tkSheet(k)", k); await pg.wait_for_timeout(300)
    await pg.evaluate("() => document.querySelector('#mbm [data-tvsf=\"remind\"]').click()"); await pg.wait_for_timeout(200)
    say = await pg.evaluate("() => ((document.querySelector('#tv-pop .tvrm-say') || {}).innerText || '')")
    c.ok('while SmartDesigns is open on your phone or computer' in say, f'sheet: Remind says it reminds while the app is open ({say!r})')
    await pg.evaluate(CLOSE)
    # a bad parse is put right from the sheet: Rename, Move to Another Job, Remove with a reason (soft, findable)
    made = await pg.evaluate("() => { const m = tvQaCreate(tvQaParse('Chase the guttter quote')); return m ? `${m.kind}:${m.id}:${m.projectId || ''}` : null; }")
    await pg.evaluate("k => tkSheet(k)", made); await pg.wait_for_timeout(300)
    fx = await pg.evaluate("() => [...document.querySelectorAll('#mbm [data-tvsfix]')].map(b => b.textContent.trim())")
    c.ok(fx == ['Rename', 'Move to Another Job', 'Remove'], f'fix: the sheet offers Rename, Move to Another Job and Remove ({fx})')
    await pg.evaluate("() => document.querySelector('#mbm [data-tvsfix=\"rename\"]').click()"); await pg.wait_for_timeout(200)
    await pg.evaluate("() => { document.querySelector('#tv-pop [data-tvrn]').value = 'Chase the gutter quote'; document.querySelector('#tv-pop [data-tvrnok]').click(); }"); await pg.wait_for_timeout(400)
    await pg.evaluate(CLOSE)
    t1 = await pg.evaluate("k => (tkResolve(k) || {rec: {}}).rec.title", made)
    c.ok(t1 == 'Chase the gutter quote' and 'Renamed' in await toast(pg), f'fix: Rename saves the title, with a toast ({t1})')
    ok = await pg.evaluate("k => tvMoveJob(k, 'p121')", made)
    r = await rec_of(pg, 'Chase the gutter quote')
    c.ok(ok and r and r['pid'] == 'p121' and r['key'].startswith('action:'), f'fix: Move to Another Job moves it from the firm list to 121 State ({r})')
    bad = await pg.evaluate("k => tvRemove(k, '')", r['key'])
    ok = await pg.evaluate("k => tvRemove(k, 'made by mistake')", r['key'])
    st = await pg.evaluate("""k => { const R = tkResolve(k); const x = tkItems().find(y => t2Key(y) === k); return { done: !!(x && x.done), removed: R && R.rec.removed, inDone: (() => { t2View = 'done'; tkWho = 'me'; return t2DonePool().some(y => t2Key(y) === k); })(), audit: (DB.audit || []).some(a => a && a.refId === R.rec.id && a.action === 'removed' && a.note === 'made by mistake') }; }""", r['key'])
    c.ok(not bad and ok and st['done'] and st['removed'] and st['removed']['why'] == 'made by mistake' and st['inDone'] and st['audit'], f'fix: Remove needs a reason, closes it softly and keeps it under Done ({st})')
    await pg.evaluate("() => { t2View = 'all'; renderTkAll(); }")
    # Mark Done from the blue button
    await pg.evaluate("k => tkSheet(k)", k); await pg.wait_for_timeout(300)
    await pg.evaluate("() => document.querySelector('#mbm-ok').click()"); await pg.wait_for_timeout(500)
    await pg.evaluate(CLOSE)
    done = await pg.evaluate("k => { const x = tkItems().find(y => t2Key(y) === k); return !x || !!x.done; }", k)
    c.ok(done, 'sheet: the blue Mark Done marks it done')


async def ask(c, pg):
    await sign_in(pg, 'u_alan')
    a = await pg.evaluate("async () => { const r = await paAsk('what do I owe the Kleins'); return { h: r.headline, w: r.work, n: r.note, go: r.go }; }")
    c.ok(a and 'Klein' in a['h'] and '$' not in a['h'] and a['go'] and a['go'].get('tkOwed') == 'client', f'ask:"what do I owe the Kleins" answers from tasks, not money ({a and a["h"]})')
    a2 = await pg.evaluate("async () => { const r = await paAsk('what does the crew owe me'); return { h: r.headline, w: r.work }; }")
    c.ok(a2 and 'crew owes' in a2['h'], f'ask: "what does the crew owe me" answers from the crew’s tasks ({a2 and a2["h"]})')
    # the filters, and their counts equal their rows
    await go(pg, 'tkall')
    for k in ('client', 'crew'):
        r = await pg.evaluate("k => { tvFF = { owed: k }; tkWho = 'all'; t2View = 'all'; tkProject = ''; renderTkAll(); return { rows: document.querySelectorAll('#tkall-body .tk2-row').length, want: openTasks('all').filter(x => tkOwedBy(x, k)).length, chip: !!document.querySelector('#tkall-body [data-tvphfx=\"ff:owed\"]') }; }", k)
        c.ok(r['rows'] == r['want'] and r['want'] > 0 and r['chip'], f'ask: the {k} filter shows its rows and a removable chip ({r})')
    await shot(pg, 'pm_owed_filter')
    await pg.evaluate("() => { tvFF = {}; tkWho = 'me'; t2View = 'week'; renderTkAll(); }")


async def counts(c, pg):
    # the job's Tasks is the one list, filtered to the job
    await sign_in(pg, 'u_alan')
    await pg.evaluate("setCurrent('p121')"); await go(pg, 'tasks'); await pg.wait_for_timeout(300)
    j = await pg.evaluate("""() => ({ on: [...document.querySelectorAll('.view.on')].map(e => e.id), old: !!document.querySelector('.view.on #act-table'),
      rows: [...document.querySelectorAll('#tkall-body .tk2-row')].length, want: t2ViewOf(openTasks('all').filter(x => x.projectId === 'p121'), t2View).length, view: t2View })""")
    await shot(pg, 'pm_job_tasks')
    c.ok('v-tkall' in j['on'] and not j['old'] and j['rows'] == j['want'], f'counts: the job’s Tasks is the one list filtered to the job, rows equal its count ({j})')
    for uid in ('u_owner', 'u_alan', 'u_chen', 'u_billing'):
        await sign_in(pg, uid); await go(pg, 'home'); await pg.wait_for_timeout(200)
        n = await pg.evaluate("""() => { const vis = """ + VIS + """, num = s => { const e = [...document.querySelectorAll(s)].find(vis); return e ? +(e.textContent.replace(/\\D+/g, '') || 0) : null; };
          return { want: tkTasksN(), bar: num('#mtabs [data-mv="tkall"] .n'), hasTab: !!document.querySelector('#mtabs [data-mv="tkall"]') }; }""")
        # the approved menu (docs/mockups/today/SPEC.md: Tasks, "no badge") holds: a number on the tab, if any, is tkTasksN()
        c.ok(n['bar'] in (None, 0, n['want']), f'bar: {uid}: the Tasks tab shows no number but the Tasks number ({n})')
        await go(pg, 'tkall'); await pg.wait_for_timeout(200)
        ch = await pg.evaluate("""() => { const vis = """ + VIS + """; return [...document.querySelectorAll('#tkall-body .tv-qchips button, #tkall-body .yd-chips button')].filter(vis).map(b => [b.dataset.ydchip || b.dataset.tvqv, b.innerText.replace(/\\s+/g, ' ').trim(), (b.querySelector('.n') || {}).textContent || '']); }""")
        rows = await pg.evaluate("() => document.querySelectorAll('#tkall-body .tk2-row').length")
        on = [x for x in ch if x[2]]
        # every chip's number is the rows it shows, tapped
        bad = []
        for cid, label, num in on:
            got = await pg.evaluate("""c => { const b = [...document.querySelectorAll('#tkall-body [data-ydchip], #tkall-body [data-tvqv]')].find(b => (b.dataset.ydchip || b.dataset.tvqv) === c); if (!b) return -1; b.click(); return document.querySelectorAll('#tkall-body .tk2-row').length; }""", cid)
            await pg.wait_for_timeout(150)
            if str(got) != num.strip(): bad.append((label, num, got))
        c.ok(not bad, f'counts: {uid}: each Tasks chip’s number equals the rows it shows ({bad or ch})')
        # one label, one number: the bar's Waiting On chip and the filter sheet's Waiting On (capture 11-05: 2 beside 1)
        w = await pg.evaluate("""() => { tvApply('b:open'); const chip = document.querySelector('#tkall-body [data-ydchip="b:wait"]'); const cn = chip ? +((chip.querySelector('.n') || {}).textContent || 0) : null;
          tkFilterSheet(); const b = document.querySelector('#mbm [data-tkfview="blocked"]'); const r = { chip: chip ? chip.innerText.replace(/\\d+/g, '').trim() : null, cn, sheet: b ? b.innerText.replace(/\\d+/g, '').trim() : null, sn: b ? +((b.querySelector('.n') || {}).textContent || 0) : null, mine: tkMyCounts().blocked };
          mbCloseModal(); return r; }""")
        c.ok(w['chip'] == w['sheet'] == 'Waiting On' and w['cn'] == w['sn'] == w['mine'], f'counts: {uid}: Waiting On reads one label and one number on the chip and the filter sheet ({w})')
    # the Team view: each person's count is that person's open tasks, the same function as Mine
    await sign_in(pg, 'u_alan'); await go(pg, 'tkall')
    await pg.evaluate("() => tvApply('b:all')"); await pg.wait_for_timeout(300)
    T = await pg.evaluate("""() => [...document.querySelectorAll('.yd-teamv [data-ydteamwho]')].map(s => ({ who: s.dataset.ydteamwho, n: s.querySelectorAll('.yd-row').length, head: (s.querySelector('.yd-gh') || {}).innerText || '' }))""")
    want = await pg.evaluate("() => { const u = DB.users.find(x => x.id === 'u_alan'); return openTasks(u.name).length; }")
    mine = await pg.evaluate("() => openTasks('me').length")
    alan = [x for x in T if x['who'] == 'u_alan']
    c.ok(alan and alan[0]['n'] == want == mine and str(want) in alan[0]['head'], f'counts: the Team view gives Alan the count Mine gives him ({alan}, Mine {mine})')
    await shot(pg, 'pm_team_view')


async def swipe(c, pg):
    await sign_in(pg, 'u_alan'); await go(pg, 'tkall'); await pg.evaluate("() => { t2View = 'all'; renderTkAll(); }"); await pg.wait_for_timeout(250)
    ks = await pg.evaluate("() => [...document.querySelectorAll('#tkall-body .tk2-row[data-tkkey]')].filter(r => /^action:/.test(r.dataset.tkkey) && r.querySelector('[data-t2done]')).slice(0, 2).map(r => r.dataset.tkkey)")
    c.ok(len(ks) == 2, f'swipe: two rows to swipe ({ks})')
    if len(ks) < 2: return
    await pg.evaluate(SWIPE, [ks[0], -120]); await pg.wait_for_timeout(300)
    s = await pg.evaluate("""k => { const r = document.querySelector(`#tkall-body .tk2-row[data-tkkey="${k}"]`), t = r.querySelector('.tk2-title').getBoundingClientRect();
      return { swiped: r.classList.contains('swiped'), titleIn: t.left >= 0 && t.right <= innerWidth && t.width > 150, acts: [...r.querySelectorAll('.tk2-act')].filter(b => b.getClientRects().length).map(b => [b.innerText.trim(), Math.round(b.getBoundingClientRect().height)]) }; }""", ks[0])
    await shot(pg, 'pm_swipe_left')
    c.ok(s['swiped'] and s['titleIn'], f'swipe: left keeps the title in view ({s})')
    c.ok([a[0] for a in s['acts']] == ['Later', 'Reschedule', 'Hand Off'] and all(a[1] >= 44 for a in s['acts']), f'swipe: left opens Later, Reschedule and Hand Off, 44px ({s["acts"]})')
    await pg.evaluate(SWIPE, [ks[1], 140]); await pg.wait_for_timeout(600)
    d = await pg.evaluate("k => { const x = tkItems().find(y => t2Key(y) === k); return !x || !!x.done; }", ks[1])
    t = await toast(pg)
    c.ok(d and 'Done' in t and 'Undo' in t, f'swipe: right marks it Done with Undo ({d}, {t!r})')
    # the active filter shows, and a search does not stick
    await pg.evaluate("() => { t2View = 'overdue'; renderTkAll(); }"); await pg.wait_for_timeout(200)
    f = await pg.evaluate("() => [...document.querySelectorAll('#tkall-body [data-tvphfx]')].map(b => b.innerText.trim())")
    c.ok('Overdue' in f, f'swipe: the Overdue filter shows as a removable chip ({f})')
    await pg.evaluate("() => { t2Q = 'joist'; window.__tkSearch = true; renderTkAll(); }")
    await go(pg, 'home'); await go(pg, 'tkall')
    q = await pg.evaluate("() => [t2Q, !!window.__tkSearch]")
    c.ok(q == ['', False], f'swipe: a search is cleared on leaving Tasks ({q})')
    # 130% text: the header's Ask stays whole
    await pg.evaluate("() => { document.documentElement.style.zoom = '1.3'; t2View = 'week'; renderTkAll(); }"); await pg.wait_for_timeout(300)
    a = await pg.evaluate("""() => { const vis = """ + VIS + """; const b = [...document.querySelectorAll('#tb-ask, .tv-phhd [data-p2nask], .tv-phhd .tb-ask, [aria-label="Ask"]')].find(vis); if (!b) return null; const r = b.getBoundingClientRect(), z = 1.3; return { right: Math.round(r.right * 1), vw: Math.round(document.documentElement.clientWidth), sw: document.documentElement.scrollWidth }; }""")
    await shot(pg, 'pm_zoom130')
    await pg.evaluate("() => { document.documentElement.style.zoom = ''; }")
    c.ok(a and a['right'] <= a['vw'] + 1, f'swipe: at 130% text the Ask button is whole on screen ({a})')


async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, phone=True)
        for name, fn in (('meet', meet), ('quick', quick), ('offer', offer), ('link', link), ('sheet', sheet), ('ask', ask), ('counts', counts), ('swipe', swipe)):
            if ONLY and name not in ONLY: continue
            try:
                await fn(c, pg)
            except Exception as e:
                c.ok(False, f'{name}: raised {e}')
            await pg.evaluate(CLOSE)
        c.ok(not errs, f'no page errors ({errs[:3]})')
        await b.close()
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
