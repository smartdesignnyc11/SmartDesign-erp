"""tasks_field: the task module on the receiver's side of the phone (lane T1, 11-05), each item checked the way the
field expert and the PM expert saw it (scratchpad tasks_review/field and pm), at 390x844 with touch. Invented data.

  rows      S1  A task row on a field screen opens the task sheet and has Done: the foreman's Put on You (Alan's
                "Photograph both garden bath joists", which also asks for its photo), the crew's Clock rows.
  question  S1  A task made from a field question (STA-21, Angel's 3" vs 2" drop) asks for the answer on Done, closes
                the question and puts the answer on Angel's Today (For You).
  need          The crew's Need Something on a task carries the task into the request it sends.
  plan          The foreman's Change the Plan to the PM defaults Send To to the PM.
  punch         Site's Punch Done asks for a photo of the finished work, and every Site redraw goes through render()
                (the phone pass): no direct fRender* call outside the field's own render step.
  offers    S1  An offer lands where the receiver looks, with Accept and Decline: the foreman's Today (a PM's quick
                hand-off), the crew's Clock (Angel's hand-off, named as Angel's), the coordinator's Today. A meeting
                item for the crew lands on his Clock.
  blocked       The crew's Blocked sends the reason to the foreman as a task of his; the top bar's flag reads
                "Report an App Problem".
  dm            A direct message offers a photo and the camera, not only Share a Record.
  designer      The designer's "Waiting on Decisions" tile equals its rows, and a decision row opens the decision.
  quick         A quick add naming PO-2026-047 is linked to the PO and filed on its job (needs tkRefsIn, lane T2).
  es            The crew's schedule in Spanish reads its dates in Spanish, with no arrow glyph; a request's state reads
                in Spanish.
  clock         Clock In on a day already sent does not overlap it; 0.02 h clocked against 0 logged is not balanced.
  toast         A toast's Undo is a 44px target.
  autoclock     (Alan, 11-06) Clock-in is automatic by location once the notice is accepted (who and when, audited):
                entering a site clocks in with Undo, 15 minutes away clocks out at the time they left, another site
                switches the job, a poor fix asks, no acknowledgement stays manual, Spanish is in place.
  payhold       (Alan, 11-06) Overlapping punches are held out of the pay run, the rest pays, the review says
                "Held: N hours, overlap", the foreman is reminded the day before the cutoff and picks one, the kept one
                is paid on the next run, and nothing is paid twice.
Run: python3 tasks_field_test.py [section ...]   (SD_DIST names another build, e.g. the one before the fix)"""
import asyncio, os, re, sys
from harness import async_playwright, open_app, sign_in, go, Checks, ROOT

SHOTS = os.environ.get('T1_SHOTS') or os.path.join(ROOT, 'review', 'tasks_field')
os.makedirs(SHOTS, exist_ok=True)
CLOSE = "() => { try { mbCloseModal(); } catch (e) {} document.querySelectorAll('#mbm').forEach(e => e.remove()); }"
PHOTO = "() => { window.mReadPhoto = (cb) => cb('data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP'); }"
VIS = "(s) => [...document.querySelectorAll(s)].filter(e => e.getClientRects().length)"


async def shot(pg, name):
    try:
        await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
    except Exception:
        pass


async def mbm_text(pg):
    return await pg.evaluate("() => (document.querySelector('#mbm') || {}).innerText || ''")


async def tap(pg, sel, text=None):
    """a real tap on the first visible element matching sel (and holding text)"""
    h = await pg.evaluate_handle("([s, t]) => [...document.querySelectorAll(s)].find(e => e.getClientRects().length && (!t || (e.innerText || '').includes(t))) || null", [sel, text])
    el = h.as_element()
    if not el: return False
    await el.scroll_into_view_if_needed()
    await el.tap()
    await pg.wait_for_timeout(350)
    return True


async def make_task(pg, as_uid, title, assignee, **kw):
    await sign_in(pg, as_uid)
    return await pg.evaluate("""([t, a, kw]) => { const m = crCreateTask(Object.assign({ title: t, for: 'p:p121', assignee: a, due: '2026-09-04' }, kw)); save(); return m ? `${m.kind}:${m.id}:${m.projectId || ''}` : ''; }""", [title, assignee, kw])


async def s_rows(pg, c):
    key = await make_task(pg, 'u_alan', 'Photograph both garden bath joists before and after sistering', 'Angel', handoff=False)
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday')
    await pg.evaluate("() => document.querySelectorAll('details.pr-more').forEach(d => d.open = true)")
    row = await pg.evaluate("() => { const r = [...document.querySelectorAll('.f-mine *')].find(e => /Photograph both garden bath/.test(e.innerText || '') && (e.matches('[data-tkopen]') || e.matches('.f-row'))); return r ? { open: r.matches('[data-tkopen]'), done: !!r.querySelector('[data-tkrowdone]') } : null; }")
    c.ok(row is not None, "rows: Alan's task is on the foreman's Put on You")
    await shot(pg, 'rows_foreman_today')
    c.ok(bool(row and row['open'] and row['done']), f"rows: the Put on You row opens and has Done ({row})")
    if await tap(pg, '.f-mine [data-tkopen]', 'Photograph both garden'):
        t = await mbm_text(pg)
        await shot(pg, 'rows_foreman_sheet')
        c.ok('Photograph both garden bath' in t and 'Mark Done' in t, f"rows: a tap opens the task sheet with Mark Done ({t[:80]!r})")
        await pg.evaluate(CLOSE)
    else:
        c.ok(False, 'rows: no Put on You row to tap')
    if await pg.evaluate("() => { const r = [...document.querySelectorAll('.f-mine [data-tkopen]')].find(e => /Photograph both garden/.test(e.innerText)); const b = r && r.querySelector('[data-tkrowdone]'); if (!b) return false; b.click(); return true; }"):
        t = await mbm_text(pg)
        await shot(pg, 'rows_foreman_proof')
        c.ok('Proof Needed' in t and 'Take a Photo' in t, f"rows: Done on a photograph task asks for the photo ({t[:80]!r})")
        await pg.evaluate(PHOTO)
        await tap(pg, '#mbm [data-tdycam]')
        await tap(pg, '#mbm #mbm-ok')
        await pg.wait_for_timeout(300)
        done = await pg.evaluate("k => { const x = tkItems().find(y => t2Key(y) === k); return !!(x && x.done); }", key)
        c.ok(done, 'rows: with the photo it is done')
    else:
        c.ok(False, 'rows: no Done on the Put on You row')
    # what is his and due today is above the fold, and the coloured bar never cuts a row's words
    await go(pg, 'ftoday')
    r = await pg.evaluate("""() => { const m = document.querySelector('#ftoday-body .f-mine');
      const bars = [...document.querySelectorAll('#ftoday-body .f-row.warn, #ftoday-body .f-row.bad, #ftoday-body .f-row.ok')].filter(e => e.getClientRects().length);
      return { folded: !m || !!m.closest('details.pr-more'), huddle: !!m && /Morning huddle/.test(m.innerText), tight: bars.filter(e => parseFloat(getComputedStyle(e).paddingLeft) < 8).length, bars: bars.length }; }""")
    c.ok(not r['folded'] and r['huddle'], f"rows: Put on You (the morning huddle due today) is above More for Today ({r})")
    c.ok(r['tight'] == 0, f"rows: a row's coloured bar leaves its words clear ({r['tight']} of {r['bars']} rows touch the bar)")
    # the crew's Clock: a schedule row opens its card
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    ok = await tap(pg, '#fm-today .fm-row .grow b')
    t = await mbm_text(pg)
    c.ok(ok and len(t) > 20, f"rows: a schedule row on the crew's Clock opens its sheet ({t[:60]!r})")
    await pg.evaluate(CLOSE)


async def s_question(pg, c):
    await sign_in(pg, 'u_sarah'); await go(pg, 'tkall')
    key = await pg.evaluate("() => (tkAll().find(t => t.kind === 'issue' && t.id === 'is1') || {}).key || ''")
    c.ok(bool(key), 'question: the drawing question is a task (issue is1)')
    await pg.evaluate("k => tkSheet(k)", key)
    await pg.wait_for_timeout(300)
    await tap(pg, '#mbm #mbm-ok')
    await pg.wait_for_timeout(400)
    t = await mbm_text(pg)
    await shot(pg, 'question_answer_sheet')
    asked = 'Answer' in t and 'Angel' in t
    c.ok(asked, f"question: Done asks for the answer to Angel's question ({t[:80]!r})")
    if asked:
        await pg.fill('#mbm textarea[data-f="a"]', '3 inch, per the framing notes. A-301 rev 3 follows.')
        await tap(pg, '#mbm #mbm-ok')
        await pg.wait_for_timeout(400)
    r = await pg.evaluate("() => { const r = DB.field.raises.find(x => x.id === 'fr1'); const i = DB.projects.find(p => p.id === 'p121').issues.find(x => x.id === 'is1'); return { st: r.status, a: r.answer || '', by: r.answeredBy || '', is: i.status }; }")
    c.ok(r['st'] == 'answered' and '3 inch' in r['a'], f"question: the question is answered and closed ({r})")
    c.ok(r['is'] in ('done', 'answered', 'closed'), f"question: the task is closed ({r['is']})")
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday')
    body = await pg.evaluate("() => document.querySelector('#ftoday-body').innerText")
    await shot(pg, 'question_foreman_for_you')
    c.ok('answered: Exposed-beam' in body or 'answered: Exposed' in body, "question: Angel's Today has the answer (For You)")


async def s_need(pg, c):
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    tid = await pg.evaluate("() => { const b = document.querySelector('#fm-today [data-fm-need]'); return b ? b.dataset.fmNeed : ''; }")
    await tap(pg, '#fm-today [data-fm-need]')
    got = await pg.evaluate("() => ({ v: view, t: (typeof comp !== 'undefined' && comp.taskId) || '' })")
    c.ok(got['v'] == 'req' and tid and got['t'] == tid, f"need: Need Something carries the task into the request ({tid} -> {got})")


async def s_plan(pg, c):
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday')
    await pg.evaluate("() => document.querySelectorAll('details.pr-more').forEach(d => d.open = true)")
    ok = await tap(pg, '[data-fraise="blocker"]', 'Change the')
    v = await pg.evaluate("() => { const s = document.querySelector('#mbm [data-f=\"to\"]'); return s ? s.value : ''; }")
    await shot(pg, 'plan_send_to')
    c.ok(ok and v == 'pm', f"plan: Change the Plan's Send To is the PM ({ok}, {v!r})")
    await pg.evaluate(CLOSE)


async def s_punch(pg, c):
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => { DB.field.punch.push({ id: 'fp_t1', projectId: S.id, room: 'Garden bath', item: 'Replace the cracked outlet cover', assignee: 'Angel', status: 'open', by: 'Angel', at: appNowIso(), photos: [] }); save(); }")
    await go(pg, 'fsite')
    heads0 = await pg.evaluate("() => [...document.querySelectorAll('#fsite-body h3')].map(h => h.innerText)")
    await tap(pg, '[data-fpunch="fp_t1:done"]')
    t = await mbm_text(pg)
    await shot(pg, 'punch_proof')
    c.ok('Take a Photo' in t, f"punch: Done asks for a photo of the finished work ({t[:80]!r})")
    await tap(pg, '#mbm #mbm-ok')
    st = await pg.evaluate("() => DB.field.punch.find(x => x.id === 'fp_t1').status")
    c.ok(st == 'open', f'punch: without a photo or a reason it stays open ({st})')
    await pg.evaluate(PHOTO)
    await tap(pg, '#mbm [data-tkrcam]')
    await tap(pg, '#mbm #mbm-ok')
    r = await pg.evaluate("() => { const x = DB.field.punch.find(x => x.id === 'fp_t1'); return { st: x.status, n: (x.photos || []).length }; }")
    c.ok(r['st'] == 'done' and r['n'] >= 1, f'punch: with the photo it is done and the photo is on it ({r})')
    heads1 = await pg.evaluate("() => [...document.querySelectorAll('#fsite-body h3')].map(h => h.innerText)")
    # done with no photo needs a reason, and the reason is on the record
    await pg.evaluate("() => { DB.field.punch.push({ id: 'fp_t2', projectId: S.id, room: 'Garden bath', item: 'Caulk behind the vanity', assignee: 'Angel', status: 'open', by: 'Angel', at: appNowIso(), photos: [] }); save(); render(); }")
    await tap(pg, '[data-fpunch="fp_t2:done"]')
    await pg.fill('#mbm [data-f="why"]', 'behind the vanity, no clear shot')
    await tap(pg, '#mbm #mbm-ok')
    r2 = await pg.evaluate("() => { const x = DB.field.punch.find(x => x.id === 'fp_t2'); return { st: x.status, why: (x.noPhotoWhy || {}).why || '' }; }")
    c.ok(r2['st'] == 'done' and 'no clear shot' in r2['why'], f'punch: done without a photo carries its logged reason ({r2})')
    await shot(pg, 'punch_after')
    c.ok(heads0 == heads1, f'punch: Site redrawn through render keeps its phone headings ({heads0[:3]} vs {heads1[:3]})')
    # the class: no direct fRender* redraw outside the field's own render step (fRenderView)
    src = ''.join(open(os.path.join(ROOT, 'src', f), encoding='utf-8').read() for f in sorted(os.listdir(os.path.join(ROOT, 'src'))) if f.endswith('.js'))
    i = src.find('function fRenderView() {')
    rest = src[:i] + src[src.find('\n}', i):] if i >= 0 else src
    # and its wrappers' own dispatch (the foreman's Ask page is fRenderView's "fraise" branch)
    while 'fRenderView = function' in rest:
        k = rest.find('fRenderView = function')
        rest = rest[:k] + rest[rest.find('\n  };', k):]
    # a declaration, a wrapper's call of its base, or fRenderView's own dispatch is not a redraw
    calls = [m.group(1) for m in re.finditer(r'(?<!function )(?<![\w.])(fRender(?!View\b)[A-Z]\w*)\(\)', rest) if 'Base' not in m.group(1)]
    c.ok(not calls, f'punch: no direct field redraw outside render ({len(calls)} outside fRenderView: {calls})')


async def s_offers(pg, c):
    # a PM's quick hand-off to the foreman (S1_01)
    await make_task(pg, 'u_alan', 'Check the flitch beam bolts at the garden bedroom', 'Angel')
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday')
    card = await pg.evaluate("() => { const c = document.querySelector('#ftoday-body .tkr-offers'); return c ? c.innerText : ''; }")
    await shot(pg, 'offers_foreman_today')
    c.ok('Check the flitch beam bolts' in card and 'Accept' in card and 'Decline' in card, f"offers: the PM's hand-off is on the foreman's Today with Accept and Decline ({card[:80]!r})")
    vis = await pg.evaluate("() => { const c = document.querySelector('#ftoday-body .tkr-offers'); return !!c && !c.closest('details.pr-more'); }")
    c.ok(vis, 'offers: it is on the first screen, not folded under More for Today')
    # the 11-06 capture: Put on You sat below the first screen; his own tasks and offers start inside the first 844px
    tops = await pg.evaluate("""() => { window.scrollTo(0, 0); const m = document.scrollingElement; m && (m.scrollTop = 0);
      const t = (s) => { const e = document.querySelector(s); return e && e.getClientRects().length ? Math.round(e.getBoundingClientRect().top) : null; };
      return { offers: t('#ftoday-body .tkr-offers'), mine: t('#ftoday-body .f-mine'), h: innerHeight }; }""")
    await shot(pg, 'offers_foreman_first_screen')
    c.ok(tops['offers'] is not None and tops['mine'] is not None and tops['offers'] < tops['h'] and tops['mine'] < tops['h'], f"offers: the foreman's offers and Put on You start on the first screen, no scroll ({tops})")
    if await tap(pg, '.tkr-offers [data-tkoffacc]'):
        own = await pg.evaluate("() => { const a = DB.projects.find(p => p.id === 'p121').actions.find(x => /flitch beam bolts/.test(x.title)); return a ? a.assignee : ''; }")
        c.ok(own.startswith('Angel'), f'offers: Accept makes it his ({own})')
    # Angel hands the crew's schedule line to Alberto: the sheet names Angel (S2 hand-off)
    key = await pg.evaluate("() => { const t = DB.projects.find(p => p.id === 'p121').tasks.find(x => /Demo & subfloor/.test(x.name)); return t ? `sched:${t.id}:p121` : ''; }")
    await pg.evaluate("k => tkHandSheet(k)", key)
    await pg.wait_for_timeout(300)
    await tap(pg, '#mbm [data-tkhto]', 'Alberto')
    await tap(pg, '#mbm #mbm-ok')
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    card = await pg.evaluate("() => { const c = document.querySelector('#v-time .tkr-offers'); return c ? c.innerText : ''; }")
    await shot(pg, 'offers_crew_clock')
    c.ok('Demo & subfloor' in card and 'Angel' in card and 'Accept' in card, f"offers: Angel's hand-off is on Alberto's Clock, from Angel, with Accept ({card[:90]!r})")
    await pg.evaluate("k => tkSheet(k)", key)
    await pg.wait_for_timeout(300)
    t = await mbm_text(pg)
    c.ok('Angel' in t.split('offered this to you')[0][-40:] if 'offered this to you' in t else False, f"offers: the sheet says Angel offered it ({t[t.find('offered') - 30:t.find('offered') + 20]!r})")
    await pg.evaluate(CLOSE)
    # a meeting item for the crew lands on his Clock (S1_02)
    await make_task(pg, 'u_alan', 'Bring the laser level to 121 State', 'Alberto', source={'meetingId': 'mt_t1'})
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    mine = await pg.evaluate("() => { const c = document.querySelector('#v-time .tkr-mine'); return c ? c.innerText : ''; }")
    await shot(pg, 'offers_crew_meeting_item')
    c.ok('Bring the laser level' in mine, f"offers: the meeting's item for Alberto is on his Clock ({mine[:80]!r})")
    # an office receiver: the coordinator's Today shows the offer once, as its row with Accept, on the first screen
    await make_task(pg, 'u_alan', 'Order the vanity tops for 121 State', 'Chen Biron')
    await sign_in(pg, 'u_chen'); await go(pg, 'home')
    r = await pg.evaluate("""() => { const v = document.querySelector('#v-home');
      const hits = [...v.querySelectorAll('.td-card, .tkr-row, .td2-row, [data-tdrec]')].filter(e => e.getClientRects().length && /Order the vanity tops/.test(e.innerText) && !e.parentElement.closest('.td-card, .tkr-row, .td2-row'));
      return { n: hits.length, accept: hits.some(e => /Accept/.test(e.innerText)), card: !!v.querySelector('.tkr-offers'), folded: /Order the vanity tops/.test((v.querySelector('.td2-list') || {}).innerText || '') }; }""")
    await shot(pg, 'offers_coord_today')
    c.ok(r['n'] == 1 and r['accept'] and not r['card'] and r['folded'], f"offers: the coordinator's offer is on her Today once, with Accept, not folded ({r})")
    # one function counts offers: Today's offered rows, the Clock and the foreman's card all read tkOfferedToMe()
    r = await pg.evaluate("() => ({ fn: tkOfferedToMe().length, today: (tdyModel().offered || []).length })")
    c.ok(r['fn'] >= 1 and r['fn'] == r['today'], f"offers: Today's offers are tkOfferedToMe()'s ({r})")
    await sign_in(pg, 'u_alberto')
    r = await pg.evaluate("() => { const me = tdyMe().id; return { fn: tkOfferedToMe().length, today: (tdyModel().offered || []).length, sched: tkOfferedToMe().filter(t => t.kind === 'sched').length }; }")
    c.ok(r['sched'] >= 1 and r['fn'] == r['today'], f'offers: a schedule line offered to the crew counts the same everywhere ({r})')
    # a crew member's own question is answered on his own Clock
    await pg.evaluate("""() => { DB.field.raises.push({ id: 'fr_t1', projectId: 'p121', type: 'rfi', title: 'Which way does the garden door swing?', note: '', taskId: '', to: 'pm', cc: [], dueBy: today(), by: 'Alberto', at: appNowIso(), status: 'answered', answer: 'In, hinged on the left.', answeredBy: 'Alan Mishali', answeredAt: appNowIso(), photos: [], calls: [] }); save(); }""")
    await go(pg, 'time')
    ans = await pg.evaluate("() => (document.querySelector('#v-time .tkr-answers') || {}).innerText || ''")
    await shot(pg, 'question_crew_clock_answer')
    c.ok('garden door swing' in ans and 'hinged on the left' in ans, f"question: Alberto's answer is on his own Clock ({ans[:80]!r})")
    if await tap(pg, '#v-time .tkr-answers [data-fack]'):
        st = await pg.evaluate("() => DB.field.raises.find(x => x.id === 'fr_t1').status")
        c.ok(st == 'closed', f'question: Got It closes it ({st})')


async def s_blocked(pg, c):
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    lbl = await pg.evaluate("() => (document.getElementById('rp-btn') || {}).getAttribute ? document.getElementById('rp-btn').getAttribute('aria-label') : ''")
    c.ok(lbl == 'Report an App Problem', f'blocked: the flag reads Report an App Problem ({lbl!r})')
    ok = await tap(pg, '#fm-today [data-fm-block]')
    c.ok(ok, 'blocked: the crew has Blocked on a task')
    if ok:
        await shot(pg, 'blocked_sheet')
        await tap(pg, '#mbm [data-tkrwhy]', 'Waiting on material')
        await pg.fill('#mbm [data-f="note"]', 'no LVL on site')
        await tap(pg, '#mbm #mbm-ok')
    r = await pg.evaluate("""() => { const p = DB.projects.find(p => p.id === 'p121'), a = p.actions.find(x => /^Blocked:/.test(x.title)), w = p.actions.find(x => /^(Watch|Escalated):/.test(x.title)),
      t = a && p.tasks.find(q => q.blocked && q.blocked.taskId === a.id), fore = (DB.users || []).find(u => (p.team || []).includes(u.id) && u.role === 'foreman');
      return a ? { who: a.assignee, t: a.title, fore: fore ? fore.name : '', pm: w ? w.assignee : '', waits: w ? w.waitsOn : '', line: t ? t.id : '' } : null; }""")
    c.ok(bool(r and r['who'] == (r['fore'] or r['who']) and r['who'].startswith('Angel') and 'no LVL' in r['t']), f"blocked: the job's foreman has the task with the reason ({r})")
    c.ok(bool(r and r['pm'] and r['waits'].startswith('Angel')), f'blocked: the PM watches it, Waiting On the foreman ({r})')
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday')
    r2 = await pg.evaluate("() => ({ mine: (document.querySelector('#ftoday-body .f-mine') || {}).innerText || '', mark: [...document.querySelectorAll('#ftoday-body .tkr-blk')].map(e => e.innerText).join(' | ') })")
    await shot(pg, 'blocked_foreman_today')
    c.ok('Blocked:' in r2['mine'] and 'no LVL' in r2['mark'], f"blocked: on the foreman's Put on You and his Today's Work line ({r2['mark'][:80]!r})")
    # the end of the shift: untouched, it goes to the PM
    esc = await pg.evaluate("""() => { const p = DB.projects.find(p => p.id === 'p121'), t = p.tasks.find(q => q.blocked); t.blocked.at = iso(addDays(parse(today()), -1)) + 'T09:00:00'; render();
      const w = p.actions.find(x => x.id === t.blocked.watchId); return { esc: !!t.blocked.escalated, title: w ? w.title : '', pri: w ? w.priority : '' }; }""")
    c.ok(esc['esc'] and esc['title'].startswith('Escalated:') and esc['pri'] == 'high', f'blocked: untouched by the end of the shift it escalates to the PM ({esc})')
    # the job's schedule shows it; closing the foreman's task clears the line and the PM's watch
    await pg.evaluate("() => { setCurrent('p121'); view = 'sched'; try { schedView = 'list'; } catch (e) {} render(); }")
    await tap(pg, '#fm-fullsched')
    job = await pg.evaluate("() => [...document.querySelectorAll('#sched-list .pr-m')].map(e => e.innerText).filter(t => /blocked/.test(t)).join(' | ')")
    c.ok('no LVL' in job, f"blocked: the job's schedule shows the line blocked ({job[:80]!r})")
    r3 = await pg.evaluate("""() => { const p = DB.projects.find(p => p.id === 'p121'), a = p.actions.find(x => /^Blocked:/.test(x.title)); tkToggle('action', a.id, 'p121');
      const t = p.tasks.find(q => (q.blockHist || []).some(h => h.taskId === a.id)), w = p.actions.find(x => /^(Watch|Escalated):/.test(x.title));
      return { cleared: !!t && !t.blocked, watch: w ? w.status : '' }; }""")
    c.ok(r3['cleared'] and r3['watch'] == 'done', f"blocked: done clears the line and the PM's watch ({r3})")
    # not safe to work: the foreman and the PM at once, in the Standard's format, ranked first
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    if await tap(pg, '#fm-today [data-fm-block]'):
        await tap(pg, '#mbm [data-tkrwhy]', 'Not safe to work')
        await pg.fill('#mbm [data-f="note"]', 'shoring under the garden joists moved')
        await tap(pg, '#mbm #mbm-ok')
    r4 = await pg.evaluate("""() => { const p = DB.projects.find(p => p.id === 'p121'), S2 = p.actions.filter(x => /^Safety:/.test(x.title));
      const it = S2.map(a => tkAll().find(t => t.kind === 'action' && t.id === a.id)).filter(Boolean);
      return { who: S2.map(a => a.assignee), fmt: S2.every(a => /What happened:/.test(a.notes) && /Impact:/.test(a.notes) && /Options:/.test(a.notes) && /Recommendation:/.test(a.notes) && /Decide by:/.test(a.notes)),
               first: it.every(t => standardRank(tdyTaskItem(t)).imm === 0) }; }""")
    c.ok(len(r4['who']) == 2 and any(w.startswith('Angel') for w in r4['who']) and r4['fmt'] and r4['first'], f"blocked: not safe goes to the foreman and the PM at once, in the escalation format, ranked first ({r4})")


async def s_dm(pg, c):
    await sign_in(pg, 'u_alberto')
    await pg.evaluate("() => { const T = msgDirectWith('u_angel', true); msgOpen(T.key); }")
    await pg.wait_for_timeout(300)
    await tap(pg, '#msg-plus')
    vis = await pg.evaluate("() => ['#msg-cam', '.chat-compose .msg-attach', '#msg-rec'].map(s => { const e = document.querySelector(s); return !!e && !e.hidden && e.getClientRects().length > 0; })")
    await shot(pg, 'dm_attach')
    c.ok(vis[0] and vis[1], f'dm: a direct message offers the camera and a photo ({vis})')
    png = os.path.join(SHOTS, 'dm_attach.png')
    n0 = await pg.evaluate("() => DB.projects.reduce((a, p) => a + (p.files || []).length, 0)")
    await pg.set_input_files('#chat-file', png)
    await pg.wait_for_timeout(1500)
    r = await pg.evaluate("""() => { const T = msgDirectWith('u_angel'); return { own: (T.t.files || []).length, priv: (T.t.files || []).every(f => f.private), line: (T.all().slice(-1)[0] || {}).files || [],
      jobs: DB.projects.reduce((a, p) => a + (p.files || []).length, 0), img: !!document.querySelector('#chat-list .msg-dmimg') }; }""")
    await shot(pg, 'dm_photo_sent')
    c.ok(r['own'] == 1 and r['priv'] and len(r['line']) == 1 and r['jobs'] == n0 and r['img'], f'dm: a photo in a thread with no job stays on the thread, not on any job ({r}, jobs before {n0})')
    await pg.evaluate("() => { const T = msgDirectWith('u_angel'); T.t.projectId = 'p121'; save(); msgOpen(T.key); }")
    await pg.set_input_files('#chat-file', png)
    await pg.wait_for_timeout(1500)
    r = await pg.evaluate("() => { const f = DB.projects.find(p => p.id === 'p121').files.filter(f => f.link && f.link.kind === 'thread'); return { n: f.length, client: f.some(x => x.shareClient) }; }")
    c.ok(r['n'] == 1 and not r['client'], f"dm: a thread tied to a job files it on that job, never shared with the client ({r})")


async def s_photo(pg, c):
    await make_task(pg, 'u_alan', 'Picture frame rail in the parlor', 'Alan', handoff=False)
    k2 = await make_task(pg, 'u_alan', 'Photograph the stair stringer for the record', 'Alan', handoff=False)
    r = await pg.evaluate("""() => { const tk = (re) => tkAll().find(t => re.test(t.title)); return { frame: !!(tk(/^Picture frame rail/) || {}).proofNeed, photo: !!(tk(/^Photograph the stair/) || {}).proofNeed }; }""")
    c.ok(not r['frame'] and r['photo'], f'photo: the title pre-ticks Needs a Photo for a photograph, not for a picture frame ({r})')
    await go(pg, 'tkall')
    await pg.evaluate("k => tkSheet(k)", k2)
    await pg.wait_for_timeout(300)
    box = await pg.evaluate("() => { const b = document.querySelector('#mbm [data-tkrneedphoto]'); return b ? b.checked : null; }")
    await shot(pg, 'photo_needs_box')
    c.ok(box is True, f'photo: the sheet shows Needs a Photo, ticked ({box})')
    await pg.evaluate("() => { const b = document.querySelector('#mbm [data-tkrneedphoto]'); b.scrollIntoView({ block: 'center' }); b.click(); }")
    r = await pg.evaluate("k => { const t = tkAll().find(x => x.key === k); const R = tkResolve(k); return { need: !!(t && t.proofNeed), rec: R.rec.needsPhoto }; }", k2)
    c.ok(not r['need'] and r['rec'] is False, f'photo: unticked, Done asks for no photo, and the choice is on the record ({r})')
    await pg.evaluate(CLOSE)


async def s_designer(pg, c):
    await sign_in(pg, 'u_sarah'); await go(pg, 'sday')
    r = await pg.evaluate("() => { const t = (TL_SETS.sday() || []).find(x => x.k === 'Waiting on Decisions'); return { tile: t ? t.v : -1, rows: [...document.querySelectorAll('#sday-body [data-stdec]')].length }; }")
    await shot(pg, 'designer_today')
    c.ok(r['tile'] >= 0 and r['tile'] == r['rows'], f"designer: Waiting on Decisions equals its rows ({r})")
    ok = await tap(pg, '#sday-body [data-stdec]')
    v = await pg.evaluate("() => view")
    c.ok(ok and v != 'sday', f'designer: a decision row opens the decision ({v})')


async def s_quick(pg, c):
    has = await pg.evaluate("() => typeof tkRefsIn === 'function' && (DB.pos || []).some(p => p.number === 'PO-2026-047')")
    if not has:
        print('SKIP quick: tkRefsIn (lane T2) or PO-2026-047 is not in this build')
        return
    await sign_in(pg, 'u_chen')
    made = await pg.evaluate("() => { const m = tvQaCreate(tvQaParse('Chase the tile on PO-2026-047 by Friday')); return m ? { pid: m.projectId || '', link: JSON.stringify(m.rec.links || m.rec.link || null) } : null; }")
    po = await pg.evaluate("() => { const p = DB.pos.find(x => x.number === 'PO-2026-047'); return { id: p.id, pid: p.projectId }; }")
    c.ok(bool(made and made['pid'] == po['pid'] and po['id'] in made['link']), f'quick: linked to the PO and filed on its job ({made}, {po})')


async def s_es(pg, c):
    await sign_in(pg, 'u_alberto')
    await pg.evaluate("() => { currentUser().lang = 'es'; save(); render(); }")
    await go(pg, 'sched')
    txt = await pg.evaluate("() => (document.querySelector('#fm-week') || {}).innerText || ''")
    await shot(pg, 'es_schedule')
    c.ok('→' not in txt, f'es: no arrow glyph on the schedule ({txt[:120]!r})')
    nums = re.findall(r'\b\d{1,2}/\d{1,2}\b', txt)
    c.ok(not nums, f'es: the schedule dates read in Spanish ({nums[:4]})')
    await go(pg, 'req')
    txt = await pg.evaluate("() => (document.querySelector('.view.on') || {}).innerText || ''")
    c.ok('waiting for procurement' not in txt, 'es: a request state reads in Spanish')
    await pg.evaluate("() => { currentUser().lang = 'en'; save(); }")


async def s_sched(pg, c):
    await sign_in(pg, 'u_angel')
    await pg.evaluate("() => { setCurrent('p121'); view = 'sched'; try { schedView = 'list'; } catch (e) {} render(); }")
    await pg.wait_for_timeout(400)
    await tap(pg, '#fm-fullsched')
    await pg.wait_for_timeout(300)
    r = await pg.evaluate("""() => { const rows = [...document.querySelectorAll('#sched-list tr.pr-tr')].filter(e => e.getClientRects().length);
      return { n: rows.length, titles: rows.slice(0, 6).map(r => (r.querySelector('.pr-t') || {}).innerText || ''), tips: rows.filter(r => r.getAttribute('title')).length,
               side: document.documentElement.scrollWidth - innerWidth }; }""")
    await shot(pg, 'sched_list')
    c.ok(r['n'] > 3, f"sched: the schedule's list draws phone rows ({r['n']})")
    bad = [t for t in r['titles'] if re.search(r'\d%|\d/\d', t)]
    c.ok(not bad, f"sched: a row's title is the line's name, not its progress words ({bad[:3]})")
    c.ok(r['tips'] == 0, f"sched: no row carries a tooltip that sticks on a long press ({r['tips']})")
    c.ok(r['side'] <= 0, f"sched: no sideways scroll ({r['side']})")


async def s_clock(pg, c):
    await sign_in(pg, 'u_alberto')
    r = await pg.evaluate("""async () => { const e = myEmp(); const td = today(), now = appNowIso();
      const a = new Date(new Date(now).getTime() - 3 * 36e5).toISOString().slice(0, 19), b = new Date(new Date(now).getTime() + 3 * 36e5).toISOString().slice(0, 19);
      DB.time = DB.time.filter(t => !(t.empId === e.id && t.date === td));
      DB.time.push({ id: 'te_t1', empId: e.id, date: td, in: a, out: b, breakMin: 0, projectId: S.id, code: '', notes: '', status: 'submitted', work: [{ projectId: S.id, code: '02', hours: 6, note: '' }] });
      const n0 = DB.time.filter(t => t.empId === e.id).length; window.getGeo = async () => null;
      try { await clockEvent('in'); } catch (x) {}
      // 11-12: it says the day is already sent before it punches, with Start Another Shift
      const m = document.getElementById('mbm'), asked = { text: m ? m.innerText : '', n: DB.time.filter(t => t.empId === e.id).length };
      const ok = m && m.querySelector('#mbm-ok'); ok && ok.click();
      await new Promise(r => setTimeout(r, 400));
      const nw = DB.time.find(t => t.empId === e.id && !t.out);
      return { before: n0, asked, after: DB.time.filter(t => t.empId === e.id).length, of: nw ? nw.overlapOf || '' : '', toast: (document.getElementById('toast') || {}).innerText || '' }; }""")
    c.ok('already sent for approval' in r['asked']['text'] and 'Start Another Shift' in r['asked']['text'] and r['asked']['n'] == r['before'], f"clock: Clock In on a day already sent says so first and punches nothing ({r['asked']})")
    c.ok(r['after'] == r['before'] + 1 and r['of'] == 'te_t1' and 'not counted twice' in r['toast'], f'clock: Start Another Shift inside a day already sent clocks in and marks the overlap, out loud ({r})')
    html = await pg.evaluate("""() => { const e = myEmp(); DB.time = DB.time.filter(t => t.id !== 'te_t1');
      const x = { id: 'te_t2', empId: e.id, date: '2026-09-02', in: '2026-09-02T07:30:00', out: '2026-09-02T07:31:12', breakMin: 0, projectId: S.id, code: '', notes: '', status: 'open', work: [] };
      DB.time.push(x); save(); try { openTime('te_t2'); } catch (z) {} return document.body.innerHTML; }""")
    m = re.search(r'h clocked[^<]*<[^>]*>[^<]*|h clocked[^<]{0,80}', html)
    seg = html[html.find('h clocked'):html.find('h clocked') + 240] if 'h clocked' in html else ''
    c.ok(bool(seg) and 'balanced' not in seg, f'clock: 0.02 h clocked with nothing logged is not "balanced" ({re.sub("<[^>]+>", "", seg)[:80]!r})')
    await pg.evaluate(CLOSE)


async def s_autoclock(pg, c):
    """Alan, 11-06: clock-in is automatic by location, after the person accepts the notice"""
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    base = await pg.evaluate("""() => { const e = myEmp(); DB.time = DB.time.filter(t => !(t.empId === e.id && t.date === today())); save();
      const g = DB.projects.find(p => p.id === 'p121').project.geo; return { lat: g.lat, lng: g.lng, rad: g.radius || 250, emp: e.id }; }""")
    site = "{lat: %f, lng: %f, acc: 12}" % (base['lat'], base['lng'])
    far = "{lat: %f, lng: %f, acc: 12}" % (base['lat'] + 0.02, base['lng'])
    at = lambda hm: "today() + 'T%s:00'" % hm
    count = "() => DB.time.filter(t => t.empId === myEmp().id && t.date === today()).length"
    # no acknowledgement: manual
    r = await pg.evaluate(f"() => {{ delete currentUser().geoAck; return tkGeoTick({site}, {at('07:02')}); }}")
    c.ok(r['did'] == 'none' and await pg.evaluate(count) == 0, f'autoclock: without the acknowledgement nothing is automatic ({r})')
    # the notice, accepted: who and when, in the audit trail
    await go(pg, 'time')
    ok = await tap(pg, '#v-time [data-tkgon]')
    t = await mbm_text(pg)
    await shot(pg, 'autoclock_notice')
    c.ok(ok and 'never saved as a track' in t and 'I Agree' in t, f'autoclock: the notice says what it does and asks ({t[:80]!r})')
    await tap(pg, '#mbm #mbm-ok')
    r = await pg.evaluate("() => { const u = currentUser(); const a = (DB.audit || DB.auditLog || []).slice(-30).find(x => JSON.stringify(x).includes('auto-clock-by-location')); return { ack: !!(u.geoAck && u.geoAck.at), audit: !!a }; }")
    c.ok(r['ack'] and r['audit'], f'autoclock: the acknowledgement is stored with who and when, in the audit trail ({r})')
    # a poor fix never clocks in: it asks
    r = await pg.evaluate(f"() => tkGeoTick({{lat: {base['lat']}, lng: {base['lng']}, acc: {base['rad'] + 200}}}, {at('07:01')})")
    c.ok(r['did'] == 'asked' and await pg.evaluate(count) == 0, f'autoclock: a poor fix asks instead of clocking in ({r})')
    # entering the radius clocks in, marked automatic with the distance and the accuracy
    r = await pg.evaluate(f"() => tkGeoTick({site}, {at('07:02')})")
    e = await pg.evaluate("id => { const e = DB.time.find(t => t.id === id); return e ? { pid: e.projectId, how: (e.auto || {}).how, acc: (e.auto || {}).acc, dist: (e.auto || {}).dist, inn: e.in, track: Object.keys(e).filter(k => /track|path|positions/i.test(k)) } : null; }", r.get('id'))
    toast = await pg.evaluate("() => (document.getElementById('toast') || {}).innerText || ''")
    await shot(pg, 'autoclock_in_toast')
    c.ok(r['did'] == 'in' and e and e['pid'] == 'p121' and e['how'] == 'automatic, by location' and e['acc'] == 12 and e['dist'] is not None and not e['track'], f'autoclock: entering the radius clocks in, marked automatic, by location ({r}, {e})')
    c.ok('Clocked in at' in toast and '7:02' in toast and 'Undo' in toast, f'autoclock: the toast says where and when, with Undo ({toast!r})')
    # Undo reverses it
    await tap(pg, '#toast a, #toast button', 'Undo')
    c.ok(await pg.evaluate(count) == 0, 'autoclock: Undo takes the punch back')
    r = await pg.evaluate(f"() => tkGeoTick({site}, {at('07:02')})")
    # leaving: 10 minutes away is nothing, 15 clocks out at the time they left
    r1 = await pg.evaluate(f"() => tkGeoTick({far}, {at('11:30')})")
    r2 = await pg.evaluate(f"() => tkGeoTick({far}, {at('11:40')})")
    r3 = await pg.evaluate(f"() => tkGeoTick({far}, {at('11:46')})")
    out = await pg.evaluate("id => { const e = DB.time.find(t => t.id === id); return e ? e.out : ''; }", r.get('id'))
    c.ok(r2['did'] == 'none' and r3['did'] == 'out' and out.endswith('T11:30:00'), f'autoclock: away 15 minutes clocks out at the time they left ({r2}, {r3}, out {out})')
    await tap(pg, '#toast a, #toast button', 'Undo')
    out = await pg.evaluate("id => DB.time.find(t => t.id === id).out", r.get('id'))
    c.ok(out == '', f'autoclock: Undo puts them back on the clock ({out!r})')
    # moving to another site switches the job
    other = await pg.evaluate("() => { const p = DB.projects.find(p => p.id !== 'p121' && p.project.geo) || DB.projects.find(p => p.id !== 'p121'); p.project.geo = p.project.geo || { lat: 40.70, lng: -73.95, radius: 250 }; save(); return { id: p.id, lat: p.project.geo.lat, lng: p.project.geo.lng }; }")
    r4 = await pg.evaluate("([o, at]) => tkGeoTick({ lat: o.lat, lng: o.lng, acc: 10 }, at)", [other, await pg.evaluate(at('12:10'))])
    sw = await pg.evaluate("() => { const L = DB.time.filter(t => t.empId === myEmp().id && t.date === today()); return { open: L.filter(t => !t.out).map(t => t.projectId), n: L.length }; }")
    c.ok(r4['did'] == 'switch' and sw['open'] == [other['id']], f'autoclock: another site moves them to that job ({r4}, {sw})')
    # an automatic punch inside a day already on the clock is marked and goes to payroll's hold
    r5 = await pg.evaluate(f"""() => {{ const e = myEmp(); DB.time = DB.time.filter(t => !(t.empId === e.id && t.date === today()));
      DB.time.push({{ id: 'te_ov', empId: e.id, date: today(), in: today() + 'T07:00:00', out: today() + 'T15:30:00', breakMin: 30, projectId: 'p121', code: '05', notes: '', status: 'approved', work: [] }});
      const r = tkGeoTick({site}, {at('09:15')}); const n0 = DB.time.filter(t => t.empId === e.id && !t.out).length;
      const b = [...document.querySelectorAll('#toast a, #toast button')].find(x => /Start Another Shift/.test(x.innerText)); b && b.click();
      const n = DB.time.find(t => t.empId === e.id && !t.out); return {{ did: r.did, before: n0, of: n && n.overlapOf, held: tkTimeOverlaps(e.id).length }}; }}""")
    c.ok(r5['did'] == 'asked' and r5['before'] == 0, f'autoclock: arriving on a day already sent asks first and punches nothing ({r5})')
    c.ok(r5['of'] == 'te_ov' and r5['held'] >= 1, f"autoclock: Start Another Shift inside a day on the clock is marked and goes to payroll's hold ({r5})")
    await pg.evaluate("() => { currentUser().lang = 'es'; save(); render(); }")
    await pg.evaluate("() => { delete currentUser().geoAck; render(); }")
    await go(pg, 'time')
    es = await pg.evaluate("() => (document.querySelector('#v-time .tkg-card') || {}).innerText || ''")
    await shot(pg, 'autoclock_es')
    c.ok('Activar la Entrada Automática' in es, f'autoclock: the Clock reads it in Spanish ({es[:80]!r})')
    await tap(pg, '#v-time [data-tkgon]')
    t = await mbm_text(pg)
    c.ok('Entrada Automática por Ubicación' in t and 'nunca se guarda un recorrido' in t.lower(), f'autoclock: the notice reads in Spanish ({t[:80]!r})')
    await pg.evaluate(CLOSE)
    await pg.evaluate("() => { currentUser().lang = 'en'; save(); }")


async def s_payhold(pg, c):
    """Alan, 11-06, option 1: overlapping hours are held out of the pay run until the foreman picks; never paid twice"""
    await sign_in(pg, 'u_owner')
    r = await pg.evaluate("""() => { DB.company.payAnchor = '2026-08-28'; const P = payPeriodOf(today());
      const alex = DB.employees.find(e => e.id === 'em3'), d = today(), y = DB.time.find(t => t.id === 'te9').date;
      DB.time.filter(t => t.date >= P.from && t.date <= d).forEach(t => (t.status = 'approved'));
      DB.time.push({ id: 'te_ov2', empId: 'em3', date: y, in: y + 'T10:00:00', out: y + 'T16:00:00', breakMin: 0, projectId: 'p121', code: '12', notes: '', status: 'approved', work: [], overlapOf: 'te9' });
      save(); const O = tkTimeOverlaps('em3'); const run = payrollFromTime({ quiet: true });
      const te9 = DB.time.find(t => t.id === 'te9'), ov = DB.time.find(t => t.id === 'te_ov2');
      const others = DB.time.filter(t => t.date >= P.from && t.date <= d && t.status === 'approved' && !['te9', 'te_ov2'].includes(t.id));
      return { n: O.length, h: O[0] && O[0].h, run: !!run, held: run && run.held, a: te9.payrollId || '', b: ov.payrollId || '', paid: others.filter(t => t.payrollId === (run && run.id)).length, others: others.length, runId: run && run.id }; }""")
    c.ok(r['n'] == 1 and r['run'] and not r['a'] and not r['b'], f'payhold: both overlapping punches are held out of the run ({r})')
    c.ok(r['paid'] == r['others'] and r['others'] > 0, f"payhold: the rest of the run pays ({r['paid']} of {r['others']})")
    c.ok(bool(r['held']) and r['held'][0]['hours'] > 0, f"payhold: the run says what is held ({r['held']})")
    await pg.evaluate("id => openPayroll(id)", r['runId'])
    await pg.wait_for_timeout(300)
    rv = await pg.evaluate("() => (document.querySelector('.tkg-held') || {}).innerText || ''")
    await shot(pg, 'payhold_review')
    c.ok('Held:' in rv and 'hours, overlap' in rv, f"payhold: the run's review shows Held: N hours, overlap ({rv[:80]!r})")
    await pg.evaluate("() => { try { closeEditor(); } catch (e) {} }")
    # the foreman's reminder, the day before the cutoff
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday')
    rem = await pg.evaluate("() => (document.querySelector('#ftoday-body .tkg-remind') || {}).innerText || ''")
    await shot(pg, 'payhold_foreman_today')
    c.ok('overlap: pick one before payroll' in rem, f"payhold: the foreman's Today says pick one before payroll ({rem[:90]!r})")
    # he picks the earlier punch: the other is voided, the pick is audited
    await tap(pg, '#ftoday-body [data-tkgpick]')
    await tap(pg, '#mbm [data-tkgk="a"]')
    await tap(pg, '#mbm #mbm-ok')
    r2 = await pg.evaluate("""() => { const a = DB.time.find(t => t.id === 'te9'), b = DB.time.find(t => t.id === 'te_ov2'), au = (DB.audit || DB.auditLog || []).slice(-20).some(x => JSON.stringify(x).includes('overlap-picked'));
      return { a: a.status, b: b.status, au, left: tkTimeOverlaps('em3').length }; }""")
    c.ok(r2['b'] == 'void' and r2['a'] == 'approved' and r2['au'] and r2['left'] == 0, f'payhold: picking one releases it, the other is voided, and the pick is audited ({r2})')
    # the next run pays the kept punch; nothing is paid twice
    await sign_in(pg, 'u_owner')
    r3 = await pg.evaluate("""() => { const run = payrollFromTime({ quiet: true }); const a = DB.time.find(t => t.id === 'te9'), b = DB.time.find(t => t.id === 'te_ov2');
      const ids = (DB.payroll || []).flatMap(x => x.timeIds || []); const twice = ids.filter((x, i) => ids.indexOf(x) !== i);
      return { a: a.payrollId || '', b: b.payrollId || '', twice: twice.length, held: (run && run.held || []).length }; }""")
    c.ok(r3['a'] and not r3['b'] and r3['twice'] == 0 and r3['held'] == 0, f'payhold: the kept punch is paid on the next run, the voided one never, nothing twice ({r3})')


async def s_toast(pg, c):
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await tap(pg, '#fm-today [data-fm-start]') or await tap(pg, '#fm-today [data-fm-done]')
    await pg.wait_for_timeout(200)
    r = await pg.evaluate("() => [...document.querySelectorAll('#toast a, #toast button')].filter(e => e.getClientRects().length).map(e => [e.innerText.trim(), Math.round(e.getBoundingClientRect().height), Math.round(e.getBoundingClientRect().width)])")
    await shot(pg, 'toast_undo')
    undo = [x for x in r if x[0] == 'Undo']
    c.ok(bool(undo) and undo[0][1] >= 44 and undo[0][2] >= 44, f"toast: Undo is a 44px target ({r})")


SECTIONS = {'rows': s_rows, 'question': s_question, 'need': s_need, 'plan': s_plan, 'punch': s_punch, 'offers': s_offers, 'blocked': s_blocked,
            'dm': s_dm, 'photo': s_photo, 'designer': s_designer, 'quick': s_quick, 'es': s_es, 'sched': s_sched, 'clock': s_clock, 'autoclock': s_autoclock, 'payhold': s_payhold, 'toast': s_toast}


async def main():
    c = Checks()
    want = [a for a in sys.argv[1:] if a in SECTIONS] or list(SECTIONS)
    async with async_playwright() as p:
        for name in want:
            b, pg, errs = await open_app(p, phone=True)
            try:
                await SECTIONS[name](pg, c)
            except Exception as e:
                c.ok(False, f'{name}: stopped: {str(e)[:200]}')
            c.ok(not errs, f'{name}: no page errors ({errs[:2]})')
            await b.close()
    return c.done()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
