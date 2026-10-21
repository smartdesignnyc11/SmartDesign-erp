"""The field in Spanish (BACKLOG §1.20): every field screen, as the foreman, the crew and the driver, at 390px.

For each person the walk opens every screen they have (their bar, Today, Site, Crew, Daily Log and each of its steps,
Requests, Clock, Schedule, Photos, Documents, Receipts, Route, Deliveries, Tasks, Drawings, Chat, Raise, Connections,
the Standard, the assistant, the menu) and the sheets those screens open (Update, Clock In, Ask About a Room, Change
the Plan, Add a Sub Day, Add Item, Fix, Toolbox Talk, Incident, the request kits and lines, a drawing, a photo, a
thread, the receipt, Missing Hours, Need Something, New Task, the store run).

  english   the same walk in English first: every word the app itself draws there is the vocabulary to look for
  spanish   the walk again with the person's language set to Spanish: any label, button, heading, sheet or toast
            still holding one of those English words fails (a record's own words are excluded: names, notes, task
            names, what someone wrote, read from the records themselves); no sideways scroll at 390px; the house
            label rule in Spanish (a button or tab label starts with a capital); dates read "3 sept", never "9/3"
  pieces    the setting is the person's (the menu's Idioma control and the owner's Team list), the office stays in
            English, switching back puts every English word back, voice listens in Spanish, the assistant is told to
            answer in Spanish, the field's Standard reads in Spanish and says when the English has changed, a chat
            line is translated on request through the platform's door and labelled, toasts read in Spanish
Screenshots: review/items_spanish/es_*.png (phone) and es_office_desktop.png.

    python3 spanish_test.py               the test
    python3 spanish_test.py --inventory   print the English strings the walk finds that have no Spanish yet
"""
import asyncio, json, os, re, sys
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'items_spanish')
os.makedirs(SHOTS, exist_ok=True)
INVENTORY = '--inventory' in sys.argv

C = lambda sel: f"(document.querySelector('.view.on {sel}, #mbm {sel}, {sel}') || {{ click() {{}} }}).click()"
# (role user, screen, what to do on it, a name for the screenshot or None)
WALK = {
    'u_angel': [
        ('ftoday', '', 'today'), ('ftoday', C('[data-prgopen]'), 'today_update'), ('ftoday', C('[data-fclock="in"]'), None),
        ('ftoday', C('.f-row:has([data-fdone]) .grow > b'), 'today_task_sheet'),
        ('ftoday', C('#froom-btn'), None), ('ftoday', C('[data-fraise="blocker"]'), 'today_plan'),
        ('fsite', '', 'site'), ('fsite', C('#fsub-add'), None), ('fsite', C('#fpunch-add'), None), ('fsite', C('[data-fraise="delivery"]'), None),
        ('fcrew', '', 'crew'), ('fcrew', C('[data-ffix]'), None), ('fcrew', C('#ftalk'), None), ('fcrew', C('[data-fraise="incident"]'), None),
        ('flog', '', 'log')] + [('flog', C(f'[data-dlgo="{k}"]'), 'log_step%d' % k if k in (1, 3, 6) else None) for k in range(7)] + [
        ('flog', C('[data-dlopen]'), None),
        ('req', '', 'requests'), ('req', C('#cp-morekits'), None),
        ('req', "const t = document.getElementById('cp-text'); t.value = '40 2x4x8, a box of 3 inch screws, 2 rolls of tape'; t.dispatchEvent(new Event('input', {bubbles: true})); " + C('#cp-read'), 'requests_read'),
        ('sched', '', 'schedule'), ('sched', C('#fm-fullsched'), None),
        ('plans', '', 'drawings'), ('plans', C('[data-plopen]'), None), ('plans', C('[data-plcompare]'), None),
        ('photos', '', 'photos'), ('photos', C('[data-pstopen]'), None),
        ('files', '', None), ('files', C('[data-fv="list"]'), None),
        ('chat', '', 'chat_list'), ('chat', "const r = document.querySelector('.view.on [data-msgopen], .view.on .msg-row, .view.on [data-msgkey]'); r && r.click()", 'chat_thread'),
        ('chat', C('#msg-plus'), None),
        ('fraise', '', 'raise'), ('fraise', C('[data-f3ask="materials"]'), None), ('fraise', C('[data-f3ask="dump"]'), None), ('fraise', C('[data-f3ask="problem"]'), None),
        ('conn', '', None), ('standard', '', 'standard'), ('pa', '', 'assistant'),
        ('ftoday', C('#menu-btn'), 'menu'),
    ],
    'u_alberto': [
        ('time', '', 'clock'), ('time', C('#clock-in'), None), ('time', C('[data-tmlate]'), None), ('time', C('[data-fm-need]'), None),
        # the crew's Tasks page left their menu (Clock is their list, 2026-10-21): a work row opens the task sheet
        ('req', '', None), ('sched', '', None), ('chat', '', None), ('time', C('.f-row:has([data-fdone]) .grow > b'), 'task_sheet'),
        ('files', '', 'crew_photos'), ('plans', '', None), ('recv', '', 'deliveries'), ('recv', C('[data-rissue]'), None),
        ('conn', '', None), ('standard', '', None), ('pa', '', None), ('time', C('#menu-btn'), None),
    ],
    'u_alex': [
        ('route', '', 'route'), ('route', C('#fm-rclock'), None), ('route', C('#run-start'), None), ('route', C('[data-stkcount]'), None),
        ('route', C('[data-stkreturn]'), None), ('route', C('[data-drvdrop]'), None),
        ('chat', '', None), ('time', '', None), ('files', '', 'receipts'), ('files', "setCurrent('p121'); spCaptureModal({ projectId: 'p121' })", 'receipt_sheet'),
        ('req', '', None), ('conn', '', None), ('standard', '', None), ('pa', '', None), ('route', C('#menu-btn'), None),
    ],
}

# what the reader sees: each text node outside a record's own words, and the words on placeholders, titles and labels
COLLECT = r"""() => {
  const skip = typeof ES_SKIP === 'string' ? ES_SKIP : '[data-nocase],[data-verbatim],.msg-tx,.msg-quote,.pa-answer,script,style,textarea';
  const vis = el => { const r = el.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return false; const s = getComputedStyle(el); return s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity !== 0; };
  const out = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = w.nextNode())) { const t = n.data.replace(/\s+/g, ' ').trim(); if (!t || !/[A-Za-z]/.test(t)) continue; const p = n.parentElement; const k = p && p.closest(skip); if (!p || (k && !(typeof ES_FORCE === 'string' && k.matches(ES_FORCE))) || p.closest('#sd-standard-md, #sd-standard-es-md, [aria-hidden="true"]') || !vis(p)) continue;
    out.push({ t, tag: p.tagName, ctl: !!p.closest('button, a, [role=button], [role=tab], label, th, h1, h2, h3, h4') }); }
  document.querySelectorAll('[placeholder],[aria-label],[title]').forEach(e => { if (!vis(e) || e.closest('[data-nocase],[data-verbatim],[data-es-skip]')) return;
    for (const a of ['placeholder', 'aria-label', 'title']) { const v = e.getAttribute(a); if (v && /[A-Za-z]/.test(v)) out.push({ t: v.replace(/\s+/g, ' ').trim(), tag: '@' + a, ctl: true }); } });
  return { strings: out, sw: document.documentElement.scrollWidth, toast: (document.getElementById('toast') || {}).innerText || '' };
}"""

# the records' own words: every string the records hold (names, notes, task names, messages), so they are never
# counted as English the app left behind. Single lower-case words are statuses the screens must translate, not data.
DATA = r"""() => { const out = new Set(); const seen = new Set();
  const walk = (o, d) => { if (!o || d > 9 || seen.has(o)) return; if (typeof o === 'string') { const s = o.replace(/\s+/g, ' ').trim(); if (s.length >= 2 && /[A-Za-z]/.test(s) && s.length < 400 && !/^[a-z]+$/.test(s)) out.add(s); return; }
    if (typeof o !== 'object') return; seen.add(o); if (Array.isArray(o)) o.forEach(x => walk(x, d + 1)); else for (const k of Object.keys(o)) { if (/^(blob|img|src|svg|b64|thumb|audio)$/i.test(k)) continue; walk(o[k], d + 1); } };
  walk(DB, 0); return [...out]; }"""

# English words that are also Spanish words, or the trade's own words the crew says in English, or names of things
SAME = set('''a no me se son local total normal final general plan plans chat material real error central ideal idea radio
 hotel taxi actual similar regular popular formal mil pdf po pos lpc dob sd ok id nyc ny am pm wifi email gmail google kit kits
 sheetrock smartdesign mercer bond app online gps sms ea sf lf ls hr hrs h min km mi in ft lbs gal pcs box studs kd gwb led
 pex pvc hvac ce dot zip ip api ai cpa coi coi's oz x sub subs piso de la el del y o
 en es te dos tu su al lo le mi ni ya va da ve vez web ticket tickets oauth apis javascript submittal gantt kb enter
 expeditor punch list framing taping tile van drive gowanus rev supervisor panel extra erp high demo'''.split())


async def reset(pg):
    """what the last step opened is closed the way a person closes it: the X, then Escape"""
    await pg.evaluate("() => { document.querySelectorAll('.pst-lb-x, #clv-x').forEach(x => x.getClientRects().length && x.click()); try { mbCloseModal(); } catch (e) {} document.querySelectorAll('.drawer.on, #scrim.on, .sheet.on, .mn-open, .rail.open').forEach(x => x.classList.remove('on', 'mn-open', 'open')); document.body.classList.remove('rail-open', 'menu-open'); }")
    await pg.keyboard.press('Escape')
    await pg.wait_for_timeout(100)


async def menu(pg):
    """open the side menu unless it is open"""
    if not await pg.evaluate("() => !!document.querySelector('#es-lang') && document.querySelector('#es-lang').getBoundingClientRect().width > 0 && document.querySelector('#es-lang').getBoundingClientRect().left >= 0"):
        await pg.click('#menu-btn')
    await pg.wait_for_timeout(300)


async def walk(pg, uid, lang, shots=False):
    """Every step of this person's walk; returns [(step, strings, sw, toast)]"""
    await pg.evaluate("([u, l]) => { const x = DB.users.find(y => y.id === u); x.lang = l; }", [uid, lang])
    await sign_in(pg, uid)
    out = []
    for i, (v, js, name) in enumerate(WALK[uid]):
        await reset(pg)
        await pg.evaluate("v => { view = v; render(); window.scrollTo(0, 0); }", v)
        await pg.wait_for_timeout(250)
        if js:
            try:
                await pg.evaluate("async () => { " + js + " }")
            except Exception as e:
                out.append((f'{uid}:{v}:{i}', [], 0, f'STEP ERROR {e}'))
                continue
            await pg.wait_for_timeout(450)
        r = await pg.evaluate(COLLECT)
        out.append((f'{uid}:{v}:{i}', r['strings'], r['sw'], r['toast']))
        if shots and name:
            await pg.screenshot(path=os.path.join(SHOTS, f'es_{name}.png'))
    return out


# a word: letters (accented ones too, so "Menú" is one Spanish word, not "Men"), not glued to a number ("3er")
WORD = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’]*")


class Records:
    """The records' own words. A screen shows them whole, cut short ("…"), or inside a sentence of the app's own, so a
    word counts as the records' when it sits in a run of three words (two for a two-word record) that a record holds,
    in English or as the Spanish pass would show it. Short records (a name, a code) are taken out whole, as whole
    words: "Sub" in the records is not "Sub" in "Submittal". People's and companies' names are never English."""
    def __init__(self, data, data_es, names):
        self.short = sorted([d for d in set(data) | set(data_es) if len(WORD.findall(d)) <= 2], key=len, reverse=True)
        self.tri, self.bi = set(), set()
        for d in set(data) | set(data_es):
            w = [x.lower() for x in WORD.findall(d)]
            if len(w) == 2: self.bi.add(tuple(w))
            for i in range(len(w) - 2): self.tri.add(tuple(w[i:i + 3]))
        self.names = names

    def words(self, t):
        """the words of t that are the app's, not the records'"""
        s = re.sub(r'\S*\b[\w-]+\.(?:com|org|net|io|app|dev|gov)\b\S*', ' ', t)
        s = re.sub(r'\bGoogle(?: [A-Z][a-z]+)+', ' ', s)  # product names: Google Cloud, Google Calendar API
        toks = [(m.group(0), m.start(), m.end()) for m in WORD.finditer(s)]
        lw = [x[0].lower() for x in toks]
        cov = [False] * len(toks)
        for i in range(len(toks)):
            if i + 3 <= len(toks) and tuple(lw[i:i + 3]) in self.tri: cov[i] = cov[i + 1] = cov[i + 2] = True
            if i + 2 <= len(toks) and tuple(lw[i:i + 2]) in self.bi: cov[i] = cov[i + 1] = True
        # a record cut short ("… and open is…"): its last, cut word is the record's
        if toks and re.search(r'…\s*$', s) and s[toks[-1][2]:].strip().startswith('…'): cov[-1] = cov[-1] or (len(toks) > 1 and cov[-2])
        for d in self.short:
            if d not in s: continue
            for m in re.finditer(r'(?<![A-Za-zÀ-ÿ])' + re.escape(d) + r'(?![A-Za-zÀ-ÿ])', s):
                for i, (w, a, b) in enumerate(toks):
                    if a >= m.start() and b <= m.end(): cov[i] = True
        return [w for (w, a, b), k in zip(toks, cov) if not k and w.lower() not in self.names]


NAMES = r"""() => { const out = new Set(), add = (s) => String(s || '').split(/[^A-Za-zÀ-ÿ']+/).forEach(w => w.length > 1 && /^[A-Z]/.test(w) && out.add(w.toLowerCase()));
  (DB.users || []).forEach(u => add(u.name)); (DB.employees || []).forEach(e => add(e.name)); (DB.vendors || []).forEach(v => add(v.name));
  (DB.clients || []).forEach(c => { add(c.name); (c.contacts || []).forEach(x => add(x.name)); });
  (DB.field && DB.field.subs || []).forEach(s => (add(s.vendor), add(s.lead))); (DB.projects || []).forEach(p => { (p.team || []).forEach(t => add(t.name || t)); add(typeof shortName === 'function' ? shortName(p) : ''); add(p.project && p.project.name); add(p.project && p.project.addr); });
  return [...out]; }"""


def english_in(R, vocab, text):
    return [w for w in R.words(text) if w.lower() in vocab]


async def pieces(pg, c, vocab, R):
    """the setting, switching back, the Team list, voice, the assistant, the Standard, chat translation, toasts"""
    # crews keep English until the owner records Jeanette's review (Alan, 2026-10-20): no switch of their own until then
    await pg.evaluate("() => { DB.users.find(u => u.id === 'u_alberto').lang = 'en'; delete DB.company.esReview; save(); }")
    await reset(pg)
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    c.ok(await pg.evaluate("() => !document.getElementById('es-lang')"), 'review: before the review, the crew has no Spanish switch')
    await sign_in(pg, 'u_owner')
    await pg.evaluate("() => { settingsMode = 'company'; setView('proj'); }"); await pg.wait_for_timeout(400)
    c.ok(await pg.locator('#es-review-go').count() == 1, 'review: the owner sees Spanish is in review, with Open Spanish to the Crews')
    await pg.click('#es-review-go'); await pg.wait_for_timeout(300)
    await pg.fill('#mbm [data-f="by"]', 'Jeanette'); await pg.click('#mbm-ok'); await pg.wait_for_timeout(300)
    c.ok(await pg.evaluate("() => (DB.company.esReview || {}).reviewedBy") == 'Jeanette', 'review: the owner records who reviewed it')
    # the crew's own setting, from the menu: Idioma · Language
    await sign_in(pg, 'u_alberto'); await go(pg, 'time')
    await menu(pg)
    L = await pg.evaluate("""() => { const b = [...document.querySelectorAll('#es-lang [data-eslang]')]; return b.map(x => { const r = x.getBoundingClientRect(); return { t: x.innerText, h: Math.round(r.height), on: x.classList.contains('on') }; }); }""")
    c.ok(len(L) == 2 and all(x['h'] >= 44 for x in L), f'setting: the menu has English and Español, 44px each ({L})')
    await pg.screenshot(path=os.path.join(SHOTS, 'es_setting_menu.png'))
    await pg.click('#es-lang [data-eslang="es"]'); await pg.wait_for_timeout(400)
    S = await pg.evaluate("() => ({ lang: DB.users.find(u => u.id === 'u_alberto').lang, bar: [...document.querySelectorAll('[data-tab]')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()), toast: document.getElementById('toast').innerText, html: document.documentElement.lang, audit: DB.audit.slice(-3).map(a => a.action) })")
    c.ok(S['lang'] == 'es' and S['html'] == 'es', f"setting: Español saves the person's language ({S['lang']}, page {S['html']})")
    c.ok('Horas' in S['bar'] and 'Pedidos' in S['bar'], f"setting: the bar reads Spanish at once ({S['bar']})")
    c.ok(S['toast'].startswith('Listo: la app está en español'), f"setting: it says so, in Spanish ({S['toast']!r})")
    c.ok(any('language en → es' in a for a in S['audit']), 'setting: the change is on the audit trail')
    await menu(pg)
    await pg.click('#es-lang [data-eslang="en"]'); await pg.wait_for_timeout(400)
    E = await pg.evaluate("() => ({ bar: [...document.querySelectorAll('[data-tab]')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()), body: document.querySelector('.view.on').innerText, toast: document.getElementById('toast').innerText })")
    c.ok('Clock' in E['bar'] and 'Requests' in E['bar'], f"switch back: the bar is English again ({E['bar']})")
    c.ok(not re.search(r'\b(Marcar Entrada|Pedidos|Esperando Aprobación)\b', E['body']), 'switch back: no Spanish label left on the screen')
    c.ok(E['toast'].startswith('Done: the app is in English'), f"switch back: it says so in English ({E['toast']!r})")
    # the owner sets the driver's language from the Team list
    await sign_in(pg, 'u_owner')
    await pg.evaluate("() => { settingsMode = 'company'; setView('proj'); }"); await pg.wait_for_timeout(400)
    has = await pg.locator('#users-list select[data-ulang="u_alex"]').count()
    c.ok(has == 1, 'team: the owner sets each person\'s language beside their role')
    if has:
        await pg.select_option('#users-list select[data-ulang="u_alex"]', 'es'); await pg.wait_for_timeout(300)
    c.ok(await pg.evaluate("() => DB.users.find(u => u.id === 'u_alex').lang") == 'es', 'team: the driver now reads Spanish')
    c.ok(await pg.evaluate("() => document.documentElement.lang") == 'en', "team: the owner's own screen stays English")
    # voice listens in Spanish; the assistant answers in Spanish
    await sign_in(pg, 'u_alex')
    V = await pg.evaluate("""() => { const C = window.SpeechRecognition || window.webkitSpeechRecognition; if (!C) return null; const r = new C(); r.lang = 'en-US'; return r.lang; }""")
    c.ok(V in (None, 'es-US'), f'voice: a recogniser asked for en-US listens in es-US ({V})')
    M = await pg.evaluate("() => { try { return mindSystem('¿dónde está la van?', {}); } catch (e) { return 'ERR ' + e.message; } }")
    c.ok('Answer in plain Spanish' in M, 'assistant: told to answer the driver in Spanish')
    # toasts: an action's toast reads in Spanish
    await go(pg, 'route')
    await pg.evaluate("() => toast('Clocked in at 121 State Street')"); await pg.wait_for_timeout(150)
    T = await pg.evaluate("() => document.getElementById('toast').innerText")
    c.ok(T.startswith('Entrada marcada en 121 State Street'), f'toast: reads in Spanish ({T!r})')
    # the field's Standard in Spanish, with the English one tap away and a note when the English moves on
    await go(pg, 'standard'); await pg.wait_for_timeout(300)
    St = await pg.evaluate("() => document.getElementById('standard-body').innerText")
    c.ok('para la obra' in St and 'Capataz' in St and 'Cuadrilla' in St and 'Cuándo avisar' in St, 'standard: the field\'s parts read in Spanish (values, principles, jobsite, escalation, foreman, crew)')
    c.ok('El inglés cambió' not in St, 'standard: no change note while the translation matches version 1')
    await pg.screenshot(path=os.path.join(SHOTS, 'es_standard_phone.png'))
    await pg.click('[data-esstden]'); await pg.wait_for_timeout(300)
    St2 = await pg.evaluate("() => document.getElementById('standard-body').innerText")
    c.ok('Ver en Español' in St2 and ('Standard Watch' in St2 or 'Values' in St2), 'standard: Ver Todo en Inglés shows Alan\'s English')
    await pg.evaluate("() => { const b = document.querySelector('[data-esstdes]'); b && b.click(); }")
    await sign_in(pg, 'u_owner')
    sv = await pg.evaluate("() => { const B = JSON.parse(JSON.stringify(standard())); B.whoWeAre.push({ p: 'A line Alan added after the translation.' }); standardSave(B, 'a line added after the Spanish was written'); return standardLive().version; }")
    c.ok(sv == 2, f'standard: the owner publishes version 2 ({sv})')
    await sign_in(pg, 'u_alex'); await go(pg, 'standard'); await pg.wait_for_timeout(300)
    St3 = await pg.evaluate("() => document.getElementById('standard-body').innerText")
    c.ok('El inglés cambió' in St3, 'standard: once Alan publishes a new version, the Spanish page says the English changed')
    # chat: an office line, translated for the foreman on request; a foreman's Spanish line, in English for the office
    # the PM writes on the job's thread in English
    await sign_in(pg, 'u_alan')
    await pg.evaluate("() => { MSG_TRANSLATE = null; const p = DB.projects.find(x => x.id === 'p121'); (p.chat = p.chat || []).push(msgLine('Tile for the 3rd floor bath lands Friday morning. Keep the hall clear.')); save(); }")
    await pg.evaluate("() => { DB.users.find(u => u.id === 'u_angel').lang = 'es'; }")
    await sign_in(pg, 'u_angel'); await go(pg, 'chat')
    await pg.evaluate("() => { const r = [...document.querySelectorAll('.view.on [data-msgopen]')].find(x => x.dataset.msgopen === 'job:p121'); r ? r.click() : msgOpen('job:p121'); }"); await pg.wait_for_timeout(500)
    btn = await pg.evaluate("""() => { const b = [...document.querySelectorAll('.view.on .es-trb')].pop(); return b ? { id: b.dataset.estr, t: b.innerText } : null; }""")
    c.ok(btn and btn['t'] == 'Traducir', f'chat: an English line shows Traducir under it ({btn})')
    if btn:
        await pg.click(f'.view.on .es-trb[data-estr="{btn["id"]}"]'); await pg.wait_for_timeout(300)
        T = await pg.evaluate("() => document.getElementById('toast').innerText")
        c.ok(T.startswith('Para traducir hace falta'), f'chat: with no translation door (this copy is offline) it says so, in Spanish ({T!r})')
        await pg.evaluate("() => { MSG_TRANSLATE = async (t, to) => (to === 'es' ? '[es] ' : '[en] ') + t; }")
        await pg.click(f'.view.on .es-trb[data-estr="{btn["id"]}"]'); await pg.wait_for_timeout(500)
        X = await pg.evaluate("""id => { const row = document.querySelector(`.cm[data-mid="${id}"]`), m = esMsgFind(id); return { shown: row ? row.querySelector('.msg-tx').innerText : '', tr: m && m.tr, b: row ? row.querySelector('.es-trb').innerText : '' }; }""", btn['id'])
        c.ok(X['tr'] and X['tr'].get('es', '').startswith('[es] '), 'chat: the translation is kept on the line for the next reader')
        c.ok(X['shown'].startswith('[es] ') and X['b'] == 'Traducido · Ver Original', f"chat: the bubble reads the translation, labelled ({X['b']!r})")
        await pg.screenshot(path=os.path.join(SHOTS, 'es_chat_translated.png'))
        await pg.click(f'.view.on .es-trb[data-estr="{btn["id"]}"]'); await pg.wait_for_timeout(300)
        O2 = await pg.evaluate("id => document.querySelector(`.cm[data-mid=\"${id}\"] .msg-tx`).innerText", btn['id'])
        c.ok(not O2.startswith('[es] '), 'chat: Ver Original shows the words as written')
    # the foreman writes in Spanish; the PM reads it in English, on its own, and the original is kept
    mid = await pg.evaluate("() => { const p = DB.projects.find(x => x.id === 'p121'); const m = msgLine('Ya llegó el sheetrock, falta la cinta'); (p.chat = p.chat || []).push(m); save(); return m.id; }")
    await sign_in(pg, 'u_alan'); await go(pg, 'chat')
    await pg.evaluate("() => { const r = [...document.querySelectorAll('.view.on [data-msgopen]')].find(x => x.dataset.msgopen === 'job:p121'); r ? r.click() : msgOpen('job:p121'); }"); await pg.wait_for_timeout(900)
    P = await pg.evaluate("""id => { const m = esMsgFind(id), row = document.querySelector(`.cm[data-mid="${id}"]`); return { lang: m && m.lang, en: m && m.tr && m.tr.en, shown: row ? row.querySelector('.msg-tx').innerText : '', b: row && row.querySelector('.es-trb') ? row.querySelector('.es-trb').innerText : '', text: m && m.text }; }""", mid)
    c.ok(P['lang'] == 'es' and P['text'] == 'Ya llegó el sheetrock, falta la cinta', "chat: the foreman's line is kept as written, marked Spanish")
    c.ok((P['en'] or '').startswith('[en] ') and P['shown'].startswith('[en] ') and P['b'] == 'Translated · Show Original', f"chat: the PM reads it in English on its own, labelled ({P['b']!r})")
    # the PM's answer on the foreman's Today (For You): Traducir under it, the translation kept on the raise
    await sign_in(pg, 'u_angel'); await go(pg, 'ftoday'); await pg.wait_for_timeout(300)
    A0 = await pg.evaluate("() => { const b = document.querySelector('.view.on [data-fack^=\"answer:\"]'); const t = b && b.parentElement.querySelector('.es-trb'); return t ? t.innerText : null; }")
    c.ok(A0 == 'Traducir', f"for you: the PM's answer has Traducir under it ({A0!r})")
    await pg.click('.view.on .es-trb'); await pg.wait_for_timeout(500)
    A1 = await pg.evaluate("() => { const b = document.querySelector('.view.on [data-fack^=\"answer:\"]'); const row = b.parentElement; const id = b.dataset.fack.slice(7); const r = DB.field.raises.find(x => x.id === id); return { tr: r.answerTr && r.answerTr.es, shown: row.querySelector('.grow .small').innerText, b: row.querySelector('.es-trb').innerText, answer: r.answer }; }")
    c.ok((A1['tr'] or '').startswith('[es] ') and '[es] ' in A1['shown'] and A1['shown'].startswith('Sigue como extra.'), f"for you: the answer reads translated after the PM's decision, in Spanish ({A1['shown']!r})")
    c.ok(A1['b'] == 'Traducido · Ver Original' and not A1['answer'].startswith('[es]'), "for you: labelled, and the PM's words are kept as written")
    await pg.screenshot(path=os.path.join(SHOTS, 'es_foryou_translated.png'))
    await pg.evaluate("() => { MSG_TRANSLATE = null; }")


async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p, True)
        data = await pg.evaluate(DATA)
        data_es = await pg.evaluate("L => L.map(s => esT(s)).filter((s, i) => s !== L[i])", data)
        names = set(await pg.evaluate(NAMES))
        R = Records(data, data_es, names)
        # ------------------------------------------------------------------ english
        en = {}
        vocab = {}
        for uid in WALK:
            for step, strings, sw, toast in await walk(pg, uid, 'en'):
                for s in strings:
                    ws = R.words(s['t'])
                    if not ws: continue
                    en.setdefault(s['t'], step)
                    for w in ws:
                        vocab.setdefault(w.lower(), s['t'])
        for w in list(vocab):
            if w in SAME or len(w) < 2: vocab.pop(w)
        if INVENTORY:
            todo = await pg.evaluate("L => L.filter(s => esT(s) === s)", sorted(en))
            json.dump({'todo': todo, 'all': sorted(en)}, open(os.path.join(SHOTS, 'es_inventory.json'), 'w'), indent=0, ensure_ascii=False)
            print(f'{len(en)} English strings on the field screens, {len(todo)} with no Spanish yet (review/items_spanish/es_inventory.json)')
            await b.close()
            return 0
        c.ok(len(vocab) > 300, f'english: the walk read the field screens ({len(en)} strings, {len(vocab)} words)')
        # ------------------------------------------------------------------ spanish
        left = {}
        for uid in WALK:
            for step, strings, sw, toast in await walk(pg, uid, 'es', shots=True):
                if toast.startswith('STEP ERROR'): c.ok(False, f'{step}: {toast}')
                c.ok(sw <= 390, f'{step}: no sideways scroll in Spanish ({sw}px)')
                for s in strings:
                    ws = R.words(s['t'])
                    bad = [w for w in ws if w.lower() in vocab]
                    if bad: left.setdefault(s['t'], (step, bad))
                    # the house label rule in Spanish: a button's own label starts with a capital
                    if s['ctl'] and s['tag'] in ('BUTTON', 'A') and re.match(r'^[a-záéíóúñ]', s['t']) and len(s['t']) < 40 and len(ws) == len(WORD.findall(s['t'])):
                        left.setdefault('LABEL CASE: ' + s['t'], (step, []))
                    # a date the app wrote reads "3 sept", never "9/3", next to Spanish words
                    if re.search(r'(?<![\d/.])(?:1[0-2]|[1-9])/(?:3[01]|[12]\d|[1-9])(?![\d/])', s['t']) and re.search(r'\b(?:termina|vence|desde|hasta|se necesita|llega)\b', s['t']):
                        left.setdefault('DATE: ' + s['t'], (step, []))
        for t, (step, bad) in sorted(left.items(), key=lambda x: x[1][0]):
            c.ok(False, f'{step}: English left on a Spanish screen: {t!r} {bad}')
        await pieces(pg, c, vocab, R)
        await b.close()
        # the office stays in English, on a desktop too
        b, pg, errs2 = await open_app(p)
        errs += errs2
        await pg.evaluate("() => { DB.users.find(u => u.id === 'u_owner').lang = 'es'; }")
        await sign_in(pg, 'u_owner'); await go(pg, 'home')
        O = await pg.evaluate("() => ({ lang: document.documentElement.lang, rail: [...document.querySelectorAll('.rail .nav button[data-v]')].filter(b => b.getClientRects().length).map(b => b.innerText.trim()).slice(0, 4), ctl: !!document.getElementById('es-lang') })")
        c.ok(O['lang'] == 'en' and 'Today' in ' '.join(O['rail']) and not O['ctl'], f"office: the owner's screens stay in English even with Spanish set ({O})")
        await pg.screenshot(path=os.path.join(SHOTS, 'es_office_desktop.png'))
        await b.close()
    c.ok(not errs, f'no page errors ({errs[:3]})')
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
