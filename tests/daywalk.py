"""The day walk: a working day per role, step by step through the real buttons (BACKLOG.md §0 item 4,
REVIEW_PROTOCOL.md UX lens "the eight jobs").

Every walk starts in a fresh browser context (fresh IndexedDB, so the demo seeds load again). JS is used
only to sign in and, where the protocol says so, to put the person on their starting view; everything
after that is page.click / page.fill on visible text.

For each step it records:
  - clicks/taps and typed fields (the cost);
  - whether the control clicked was VISIBLE on screen before the click (no scrolling or hunting);
  - for a mutation: whether a toast appeared with a link to the record (CLAUDE.md: every mutation toasts
    with Open), and whether DB actually changed, and still holds after a reload (persisted).
A walk fails at a dead end: no way forward, a page error, the wrong record, a missing toast link, or a
mutation that did not persist. Invisible next steps are reported as flags too: the UX lens counts them.

Usage: python3 daywalk.py [--walk owner,pm,...] [--json]
Screenshots of each flag: review/daywalk/<walk>_<n>.png (review/ is git-ignored).
Prints per walk: steps, cost (clicks + fields), flags. Final line `N flags`; exit 1 if N > 0.
"""
import asyncio, json, os, re, sys, time
from harness import *

SHOTS = os.path.join(ROOT, 'review', 'daywalk')

# Round-4 costs from docs/REVIEW_PROTOCOL.md (the eight jobs), as clicks + typed fields where it gives them.
ROUND4 = {
    'owner': 'Brief 0; 2 clicks each for WW-2026-118 and AMP-311; 1 click to open a decision',
    'pm': 'CO: 3 clicks + 1 field + 1 tick, then 3 (Start, price, Send to Client, Send); Task: New Task > title > assignee > Friday > Enter (no cost given)',
    'coord': '4 clicks + 1 field',
    'billing': '6 clicks, 0 typed',
    'controller': 'no round-4 cost (reconcile one account; open Close)',
    'foreman': 'Clock in 1 tap; Materials 5 taps + 1 select + 1 line; Hidden condition 4 taps + 1 line; Daily Log no cost given',
    'client': 'Decision 3 taps, no typing; CO approve no cost given',
    'designer': 'no round-4 cost (My Day; log hours)',
}

# Finds the element to click. Candidates are visible clickables whose text matches; when an overlay
# (modal, drawer, sheet) is open the candidates inside it win, because that is what the person faces.
FIND_JS = r"""
([text, opts]) => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity !== 0; };
  document.querySelectorAll('[data-dw]').forEach(e => e.removeAttribute('data-dw'));
  const sel = opts.css || 'button, a, [role=button], [role=tab], [role=option], label, summary, .chip, .btn, [data-act], [onclick], [tabindex], li, .opt, .card, td, div, span';
  const want = opts.regex ? new RegExp(text, 'i') : null;
  const match = el => {
    const t = norm(el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || '');
    if (want) return want.test(t);
    return opts.prefix ? t.toLowerCase().startsWith(text.toLowerCase()) : t.toLowerCase() === text.toLowerCase();
  };
  let c = [...document.querySelectorAll(sel)].filter(el => vis(el) && match(el));
  // innermost match only (a span inside a button that also matches: keep the clickable one)
  const clickable = el => el.matches('button, a, [role=button], [role=tab], [role=option], label, summary, .chip, .btn, [data-act], [onclick], [tabindex], input, select');
  c = c.filter(el => !c.some(o => o !== el && el.contains(o) && (clickable(o) || !clickable(el))));
  if (opts.within) {
    const w = opts.within.toLowerCase();
    c = c.filter(el => { let p = el; for (let i = 0; i < 9 && p; i++, p = p.parentElement) if (norm(p.innerText).toLowerCase().includes(w)) return true; return false; });
  }
  if (opts.scope) { const s = [...document.querySelectorAll(opts.scope)].filter(vis); c = c.filter(el => s.some(x => x.contains(el))); }
  const inOverlay = el => { for (let p = el; p && p !== document.body; p = p.parentElement) {
      const cs = getComputedStyle(p); if ((cs.position === 'fixed') && +cs.zIndex >= 10 && !p.matches('#toast, .toast, nav, aside, .rail, .topbar, .mbar, .m-bar, .bottombar')) return +cs.zIndex || 1; } return 0; };
  const overlayOpen = c.some(el => inOverlay(el) > 0);
  const toastEl = document.getElementById('toast');
  if (!opts.toast) c = c.filter(el => !(toastEl && toastEl.contains(el)));
  else c = c.filter(el => toastEl && toastEl.contains(el));
  if (overlayOpen && !opts.any) { const z = Math.max(...c.map(inOverlay)); c = c.filter(el => inOverlay(el) === z); }
  const onScreen = el => { const r = el.getBoundingClientRect();
    if (r.bottom <= 0 || r.top >= innerHeight || r.right <= 0 || r.left >= innerWidth) return false;
    const x = Math.min(Math.max(r.left + r.width / 2, 1), innerWidth - 1), y = Math.min(Math.max(r.top + r.height / 2, 1), innerHeight - 1);
    const top = document.elementFromPoint(x, y); return !!top && (el.contains(top) || top.contains(el)); };
  c.sort((a, b) => (clickable(b) - clickable(a)) || (onScreen(b) - onScreen(a)));
  const el = c[opts.nth || 0];
  if (!el) return null;
  el.setAttribute('data-dw', '1');
  return {n: c.length, visible: onScreen(el), tag: el.tagName.toLowerCase(), text: norm(el.innerText || el.value || '').slice(0, 80)};
}
"""

# Visible controls, for a dead-end report: what the person could see instead.
CONTROLS_JS = r"""
() => { const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && getComputedStyle(el).visibility !== 'hidden'; };
  return [...document.querySelectorAll('button, a, [role=button], input, select, textarea')].filter(vis)
    .map(el => norm(el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || '').slice(0, 40)).filter(Boolean).slice(-40); }
"""

FIELD_JS = r"""
([label, css, nth]) => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  document.querySelectorAll('[data-dwf]').forEach(e => e.removeAttribute('data-dwf'));
  const F = 'input:not([type=hidden]):not([type=checkbox]):not([type=radio]), select, textarea, [contenteditable=true]';
  let c = [];
  if (css) c = [...document.querySelectorAll(css)].filter(vis);
  else {
    const L = norm(label);
    // by placeholder or aria-label
    c = [...document.querySelectorAll(F)].filter(el => vis(el) && (norm(el.placeholder).includes(L) || norm(el.getAttribute('aria-label')) === L));
    // by a caption: a label/div whose own text is the label, then the first field in its container
    const caps = [...document.querySelectorAll('label, .lbl, .f > div, .f > span, th, dt, h4, b, span, div')]
      .filter(el => vis(el) && el.children.length <= 3 && norm([...el.childNodes].filter(n => n.nodeType === 3 || /^(B|SPAN|SMALL)$/.test(n.tagName)).map(n => n.textContent).join(' ')).replace(/[*:]$/, '').trim() === L);
    for (const cap of caps) {
      if (cap.htmlFor) { const t = document.getElementById(cap.htmlFor); if (t && vis(t)) { c.push(t); continue; } }
      const inner = cap.querySelector(F); if (inner && vis(inner)) { c.push(inner); continue; }
      let p = cap.parentElement;
      for (let i = 0; i < 3 && p; i++, p = p.parentElement) { const f = [...p.querySelectorAll(F)].filter(vis); if (f.length) { c.push(f[0]); break; } }
    }
  }
  c = [...new Set(c)];
  const inOverlay = el => { for (let p = el; p && p !== document.body; p = p.parentElement) { const cs = getComputedStyle(p); if (cs.position === 'fixed' && +cs.zIndex >= 10) return +cs.zIndex; } return 0; };
  if (c.some(inOverlay)) { const z = Math.max(...c.map(inOverlay)); c = c.filter(el => inOverlay(el) === z); }
  const el = nth < 0 ? c[c.length - 1] : c[nth || 0];
  if (!el) return null;
  el.setAttribute('data-dwf', '1');
  const r = el.getBoundingClientRect();
  return {tag: el.tagName.toLowerCase(), visible: r.bottom > 0 && r.top < innerHeight, n: c.length};
}
"""

TOAST_HOOK = r"""
() => { if (window.__dwT) return; window.__dwT = []; const t = document.getElementById('toast'); if (!t) return;
  const rec = () => { const txt = (t.innerText || '').replace(/\s+/g, ' ').trim(); if (!txt) return;
    const links = [...t.querySelectorAll('a, button')].map(a => (a.innerText || '').trim()).filter(Boolean);
    const last = window.__dwT[window.__dwT.length - 1];
    if (last && last.text === txt) { last.links = Array.from(new Set(last.links.concat(links))); return; }
    window.__dwT.push({text: txt, links, at: Date.now()}); };
  new MutationObserver(rec).observe(t, {childList: true, subtree: true, characterData: true, attributes: true}); }
"""


class Walk:
    def __init__(self, name, pg, errs):
        self.name, self.pg, self.errs = name, pg, errs
        self.steps, self.flags, self.notes, self.persist = [], [], [], []
        self.cur = None

    # ---- bookkeeping
    def step(self, label):
        self.cur = {'step': label, 'clicks': 0, 'fields': 0, 'hidden': [], 'toast': None, 'db': None}
        self.steps.append(self.cur)

    @property
    def cost(self):
        return sum(s['clicks'] for s in self.steps), sum(s['fields'] for s in self.steps)

    async def flag(self, kind, msg, controls=True):
        n = len(self.flags) + 1
        os.makedirs(SHOTS, exist_ok=True)
        shot = os.path.join(SHOTS, f'{self.name}_{n}.png')
        try: await self.pg.screenshot(path=shot)
        except Exception: shot = None
        seen = []
        if controls:
            try: seen = await self.pg.evaluate(CONTROLS_JS)
            except Exception: pass
        f = {'walk': self.name, 'step': self.cur and self.cur['step'], 'kind': kind, 'msg': msg,
             'shot': shot and os.path.relpath(shot, ROOT), 'on_screen': seen}
        self.flags.append(f)
        print(f'  FLAG [{kind}] {self.cur and self.cur["step"]}: {msg}')

    def note(self, msg):
        self.notes.append({'step': self.cur and self.cur['step'], 'msg': msg})
        print(f'  note: {msg}')

    async def errors(self):
        if self.errs:
            e = self.errs[:]; del self.errs[:]
            await self.flag('error', f'page error: {e[0][:200]}')
            return True
        return False

    # ---- actions
    async def find(self, text, **o):
        return await self.pg.evaluate(FIND_JS, [text, o])

    async def click(self, text, wait=350, optional=False, **o):
        """Click a visible control by its text. Records whether it was on screen before the click."""
        hit = await self.find(text, **o)
        if not hit:
            # give a slow render a moment
            await self.pg.wait_for_timeout(700)
            hit = await self.find(text, **o)
        if not hit:
            if optional: return None
            await self.flag('dead end', f'no visible control "{text}"' + (f' near "{o["within"]}"' if o.get('within') else ''))
            raise DeadEnd(text)
        if not hit['visible']:
            self.cur['hidden'].append(text)
            sy = await self.pg.evaluate('Math.max(scrollY, document.body.scrollTop, document.documentElement.scrollTop)')
            where = await self.pg.evaluate(r"""() => { const v = document.querySelector('.view.on') || document.body; const h = v.querySelector('h1, h2');
              const m = (v.innerText || '').match(/Step \d+ of \d+/); return [h && h.innerText.trim(), m && m[0]].filter(Boolean).join(', ') }""")
            await self.flag('next step hidden', f'"{text}" exists but is off screen or covered' + (f' on {where}' if where else '') + ': the person must scroll or hunt'
                            + (f' (the page kept a {sy}px scroll from the previous screen)' if sy else ''), controls=False)
        loc = self.pg.locator('[data-dw="1"]').first
        try:
            await loc.scroll_into_view_if_needed(timeout=3000)
            await loc.click(timeout=5000)
        except Exception as e:
            try: await loc.click(timeout=3000, force=True)
            except Exception:
                await self.flag('dead end', f'"{text}" could not be clicked: {str(e).splitlines()[0][:120]}')
                raise DeadEnd(text)
        self.cur['clicks'] += 1
        await self.pg.wait_for_timeout(wait)
        await self.errors()
        return hit

    async def fill(self, value, label=None, css=None, nth=0, press=None):
        """Type into a visible field, found by its label text (a <label> or a field caption next to it),
        its placeholder, or a css selector. Fields inside an open overlay win."""
        hit = await self.pg.evaluate(FIELD_JS, [label, css, nth])
        if not hit:
            await self.pg.wait_for_timeout(700)
            hit = await self.pg.evaluate(FIELD_JS, [label, css, nth])
        if not hit:
            await self.flag('dead end', f'no visible field "{label or css}"')
            raise DeadEnd(label or css)
        if not hit['visible']:
            self.cur['hidden'].append('field ' + (label or css))
        el = self.pg.locator('[data-dwf="1"]').first
        await el.scroll_into_view_if_needed(timeout=3000)
        if hit['tag'] == 'select':
            opts = await el.evaluate('e => [...e.options].map(o => [o.value, o.text])')
            pick = next((v for v, t in opts if value.lower() in t.lower()), None)
            if pick is None:
                await self.flag('dead end', f'select "{label or css}" has no option "{value}" (has {[t for v, t in opts][:8]})')
                raise DeadEnd(value)
            await el.select_option(pick)
        else:
            await el.click()
            await el.fill(value)
        self.cur['fields'] += 1
        if press:
            await self.key(press, el)
        await self.errors()
        return el

    async def tick(self, css=None, label=None, nth=0):
        loc = self.pg.locator(css).locator('visible=true') if css else self.pg.get_by_label(label).locator('visible=true')
        if not await loc.count():
            await self.flag('dead end', f'no visible checkbox "{label or css}"')
            raise DeadEnd(label or css)
        el = loc.nth(nth)
        await el.scroll_into_view_if_needed(timeout=3000)
        await el.check(timeout=4000)
        self.cur['clicks'] += 1
        await self.pg.wait_for_timeout(250)

    async def fill_row(self, text, value, css='input, textarea'):
        """Type into the field on the row that carries this text (a task row on a sheet)."""
        ok = await self.pg.evaluate(r"""([t, css]) => { document.querySelectorAll('[data-dwf]').forEach(e => e.removeAttribute('data-dwf'));
          const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
          for (const f of [...document.querySelectorAll(css)].filter(vis)) { let p = f.parentElement;
            for (let i = 0; i < 5 && p; i++, p = p.parentElement) { const tx = p.innerText || '';
              if (tx.includes(t)) { if (tx.length > t.length + 200) break; f.setAttribute('data-dwf', '1'); return true; } } }
          return false; }""", [text, css])
        if not ok:
            await self.flag('dead end', f'no field on the row "{text}"')
            raise DeadEnd(text)
        el = self.pg.locator('[data-dwf="1"]').first
        await el.scroll_into_view_if_needed(timeout=3000)
        await el.fill(value)
        self.cur['fields'] += 1
        return el

    async def tick_row(self, text):
        """Tick the checkbox on the row (label / li / tr) that carries this text."""
        ok = await self.pg.evaluate(r"""t => { document.querySelectorAll('[data-dwc]').forEach(e => e.removeAttribute('data-dwc'));
          const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
          const boxes = [...document.querySelectorAll('input[type=checkbox]')].filter(vis);
          for (const b of boxes) { let p = b.parentElement; for (let i = 0; i < 4 && p; i++, p = p.parentElement)
            if ((p.innerText || '').includes(t)) { if ((p.innerText || '').length > t.length + 160) break; b.setAttribute('data-dwc', '1');
              const r = b.getBoundingClientRect(); return {visible: r.bottom > 0 && r.top < innerHeight}; } }
          return null; }""", text)
        if not ok:
            await self.flag('dead end', f'no checkbox on a row "{text}"')
            raise DeadEnd(text)
        if not ok['visible']: self.cur['hidden'].append('tick ' + text)
        el = self.pg.locator('[data-dwc="1"]').first
        await el.scroll_into_view_if_needed(timeout=3000)
        await el.check(timeout=4000)
        self.cur['clicks'] += 1
        await self.pg.wait_for_timeout(250)

    async def key(self, key, el=None):
        """A key press (Enter to submit). Counted apart from clicks: the protocol's costs leave Enter out."""
        await (el.press(key) if el else self.pg.keyboard.press(key))
        if key == 'Enter': self.cur['keys'] = self.cur.get('keys', 0) + 1
        await self.pg.wait_for_timeout(700)
        await self.errors()

    # ---- checks
    async def toast_mark(self):
        await self.pg.evaluate('() => (window.__dwT || []).length')
        self._tmark = await self.pg.evaluate('() => (window.__dwT || []).length')

    async def toasts_since(self):
        return await self.pg.evaluate('m => (window.__dwT || []).slice(m)', getattr(self, '_tmark', 0))

    async def mutated(self, what, js, arg=None, need_toast=True, persist=True):
        """After a mutation: DB check (js returns truthy) and a toast with a link to the record."""
        await self.pg.wait_for_timeout(300)
        ok = await self.pg.evaluate(js, arg)
        self.cur['db'] = bool(ok)
        if not ok:
            await self.flag('not saved', f'{what}: DB did not change')
        elif persist:
            self.persist.append((self.cur['step'], what, js, arg))
        ts = await self.toasts_since()
        linked = [t for t in ts if t['links']]
        self.cur['toast'] = (linked or ts or [None])[-1]
        if need_toast:
            if not ts:
                await self.flag('no toast', f'{what}: no toast said what happened')
            elif not linked:
                await self.flag('toast without Open', f'{what}: toast "{ts[-1]["text"][:90]}" has no link to the record')
        return ok

    async def see(self, text, what=None, timeout=1500):
        """The next thing the person needs is on screen (text visible in the viewport)."""
        t0 = time.time()
        while time.time() - t0 < timeout / 1000:
            ok = await self.pg.evaluate(r"""t => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
              const tl = t.toLowerCase(); let n;
              while ((n = w.nextNode())) { if (!(n.nodeValue || '').toLowerCase().includes(tl)) continue;
                const el = n.parentElement; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
                if (r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && cs.visibility !== 'hidden' && cs.display !== 'none') return true; }
              return false; }""", text)
            if ok: return True
            await self.pg.wait_for_timeout(200)
        return False


class DeadEnd(Exception):
    pass


# ---------------------------------------------------------------- walks
# Each walk gets a Walk object; it raises DeadEnd to stop at the first place there is no way forward.

async def walk_owner(w):
    pg = w.pg
    w.step('Morning Brief on landing')
    ok = await w.see('Morning Brief')
    if not ok: await w.flag('next step hidden', 'the Morning Brief is not on the owner\'s landing screen')

    # WW-2026-118: $33,500 billed against PO-2026-044 ($29,700), paid from Amex before approval, COI and W-9 blocks.
    w.step('Approve WW-2026-118 (short-pay: Approve PO Amount, Dispute Difference)')
    await w.toast_mark()
    # The brief's inline Approve only offers Approve as Billed (the full $33,500, $3,800 over the PO): check it.
    hit = await w.find('Approve', within='WW-2026-118', css='button')
    if hit:
        await w.pg.locator('[data-dw="1"]').first.click(); await pg.wait_for_timeout(400)
        dlg = await w.see('Approve PO Amount') or await w.see('Dispute Difference')
        if not dlg:
            await w.flag('wrong path', 'the brief\'s inline Approve on WW-2026-118 opens "Approve as Billed" only: no Approve PO Amount / Dispute Difference, '
                   'although the bill is $3,800 over PO-2026-044 (flowBillInline -> billAction approve -> fin2ApproveAsBilled)', controls=False)
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
        await w.click('Cancel', optional=True, wait=200)
        w.cur['clicks'] = 0
    await w.click('WW-2026-118', css='a')
    await w.click('Approve PO Amount, Dispute Difference')
    await w.fill('credit memo requested for the 10th unit', label='Reason')
    await w.click('Approve and Dispute', wait=600)
    await w.mutated('WW-2026-118 short-paid', "() => { const b = DB.bills.find(x => x.number === 'WW-2026-118'); return b && b.short && b.short.approved === 29700 && ['approved', 'paid', 'verified'].includes(b.status) }")

    w.step('Back to Home (close the bill sheet, Home in the rail)')
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
    await w.click('Home', prefix=True, scope='nav, aside, .rail, #rail')
    w.step('Approve AMP-311')
    await w.toast_mark()
    await w.click('Approve', within='AMP-311', css='button')
    await w.see('Approve as Billed')
    if await w.find('Reason', css='label'):
        await w.fill('COI renewal requested', label='Reason')
    await w.click('Approve as Billed', wait=600, optional=True) or await w.click('Approve', wait=600)
    await w.mutated('AMP-311 approved', "() => { const b = DB.bills.find(x => x.number === 'AMP-311'); return b && ['approved', 'paid', 'verified'].includes(b.status) }")

    w.step('Back to Home (Home in the rail)')
    await w.click('Home', prefix=True, scope='nav, aside, .rail, #rail')
    w.step('Open a decision (Approvals > Decisions > Open)')
    await w.click('Decisions', regex=False, optional=True) or await w.click('Approvals', prefix=True)
    await w.click('Decisions', prefix=True, optional=True)
    await w.click('Open', within='ecision')
    ok = await pg.evaluate("() => view === 'dec' || !!document.querySelector('.view.on [data-dec], #ops-dec')")
    if not ok: await w.flag('wrong record', 'Open on a decision row did not open a decision')
    elif not await w.see('Decide'): await w.flag('next step hidden', 'the decision opened but its next step (Decide) is not on screen')


async def walk_pm(w):
    pg = w.pg
    w.step('New Change Order from the estimate: Billing > Change Orders > New Change Order')
    await w.click('Billing', prefix=True, scope='nav, aside, .rail, #rail')
    await w.click('Change Orders', prefix=True)
    await w.click('New Change Order')
    w.step('Title + tick a line + Start')
    await w.fill('Extra blocking for the garden wall cabinets', label='Title')
    await w.tick_row('Framing, blocking & rough carpentry')
    n0 = await pg.evaluate("() => DB.clients.flatMap(c => c.changeOrders || []).length")
    await w.toast_mark()
    await w.click('Start Change Order', wait=800)
    await w.mutated('CO drafted from EST-2026-014', "n => { const a = DB.clients.flatMap(c => c.changeOrders || []); return a.length > n && a.some(d => /garden wall cabinets/.test(d.title || '')) }", n0)
    w.step('Price the line > Send to Client > Send')
    desc = await pg.evaluate("() => (document.querySelector('.view.on [data-f=desc]') || {}).value || ''")
    if 'for reference' in desc:
        w.note(f'the CO line description is pre-filled with the estimate hint "{desc[:70]}..." and would print on the client CO (BACKLOG 1.4 #3)')
    await w.fill('1', css='.view.on [data-f=qty]')
    await w.fill('2400', css='.view.on [data-f=rate]', press='Tab')
    await w.toast_mark()
    if not await w.find('Send to Client') and await w.find('Save'):
        await w.flag('next step hidden', 'pricing the line hides "Send to Client"; only "Unsaved changes / Save" shows, so the person must Save first '
                     '(renderDocEditor docbar, app.js ~8528; BACKLOG 1.4 #9)')
        await w.click('Save')
    await w.click('Send to Client')
    await w.click('Send', wait=800)
    await w.mutated('CO sent to the client at $2,400', "() => { const d = DB.clients.flatMap(c => c.changeOrders || []).find(d => /garden wall cabinets/.test(d.title || '')); return d && d.status === 'sent' && JSON.stringify(d.lines || d.items || []).includes('2400') }")

    w.step("Answer the foreman's field question (Home brief > Answer > Send to the Field)")
    await w.click('Home', prefix=True, scope='nav, aside, .rail, #rail')
    await w.toast_mark()
    await w.click('Answer')
    await w.fill('Go with the 3 inch drop; A-301 rev 3 shows it', css='textarea')
    await w.click('Send to the Field', wait=700)
    await w.mutated('answer stored on the field question', "() => ((DB.field || {}).raises || []).some(r => r.status === 'answered' && /3 inch drop/.test(r.answer || ''))")

    w.step('New Task for Chen due Friday (Tasks > New Task > title > assignee > Friday > Enter)')
    await w.click('Tasks')
    await w.click('New Task')
    await w.toast_mark()
    title = await w.fill('Confirm the brick mold credit with Window Works', label='What needs doing')
    await w.fill('Chen', css='[data-f=assignee]')
    await w.click('Friday')
    await w.key('Enter', title)
    if await w.find('Save Task'):
        w.note('Enter in the title did not save the task; clicked Save Task')
        await w.click('Save Task', wait=600)
    await w.mutated('task for Chen due Fri 9/4', "() => { const all = (DB.tasks || []).concat(...DB.projects.map(p => (p.tasks || []).concat(p.actions || []))); return all.some(t => /brick mold credit/.test(t.title || t.name || '') && /Chen/.test(t.assignee || t.who || t.owner || '') && (t.due || '') === '2026-09-04') }")



async def walk_coord(w):
    pg = w.pg
    w.step('Purchasing > Deliveries')
    await w.click('Purchasing', prefix=True, scope='nav, aside, .rail, #rail')
    await w.click('Deliveries', prefix=True)
    w.step('Received (first delivery)')
    po = await pg.evaluate("() => { const a = document.querySelector('.view.on a'); return [...document.querySelectorAll('.view.on a')].map(a => a.innerText.trim()).find(t => /^PO-/.test(t)) }")
    w.note(f'receiving {po}')
    rcv0 = await pg.evaluate("n => JSON.stringify((DB.pos || []).find(p => p.number === n) || {})", po)
    await w.toast_mark()
    await w.click('Received', within=po)
    await w.mutated(f'{po} received', "([n, before]) => { const p = (DB.pos || []).find(p => p.number === n); return p && JSON.stringify(p) !== before && /receiv/i.test(JSON.stringify(p)) }", [po, rcv0])
    w.step('"Bill It" in the toast > invoice # > Enter')
    nb = await pg.evaluate("() => (DB.bills || []).length")
    if not await w.find('Bill It', toast=True):
        await w.flag('dead end', 'the receive toast carries no "Bill It" link (lkBillPO, app.js ~141116)')
        raise DeadEnd('Bill It')
    await w.click('Bill It', toast=True, wait=700)
    await w.toast_mark()
    await w.fill('INV-55120', label='Invoice', press='Enter')
    await pg.wait_for_timeout(500)
    await w.mutated('vendor bill entered from the PO', "([n, po]) => (DB.bills || []).length > n && DB.bills.some(b => b.number === 'INV-55120' && (b.poId ? DB.pos.find(p => p.id === b.poId).number === po : true))", [nb, po])



INV_JS = "() => DB.clients.flatMap(c => (c.invoices || []).map(d => ({id: d.id, number: d.number, status: d.status, client: c.name})))"

async def walk_billing(w):
    pg = w.pg
    w.step('Brief "Draft It" > New Invoice')
    before = {d['id'] for d in await pg.evaluate(INV_JS)}
    await w.click('Draft It')
    await w.toast_mark()
    await w.click('New Invoice', wait=800)
    await w.mutated('progress invoice drafted', "ids => DB.clients.some(c => (c.invoices || []).some(d => !ids.includes(d.id)))", list(before))
    new = [d for d in await pg.evaluate(INV_JS) if d['id'] not in before]
    inv = new[0]['number'] if new else None
    w.note(f'drafted {inv} for {new[0]["client"] if new else "?"}')
    w.step('Send to Client > Send')
    await w.toast_mark()
    if not await w.find('Send to Client') and await w.find('Save'):
        await w.flag('next step hidden', '"Send to Client" is hidden behind "Unsaved changes / Save" (BACKLOG 1.4 #9)')
        await w.click('Save')
    await w.click('Send to Client')
    await w.click('Send', wait=900)
    await w.mutated(f'{inv} sent', "n => DB.clients.some(c => (c.invoices || []).some(d => d.number === n && ['sent', 'paid', 'partial'].includes(d.status)))", inv)
    w.step('Record Payment > Enter')
    pay0 = await pg.evaluate("() => JSON.stringify(DB.payments || []).length")
    await w.toast_mark()
    await w.click('Record Payment', wait=600)
    await w.key('Enter')
    if await w.find('Record Payment', css='.modal button, [role=dialog] button, #mbm button'):
        w.note('Enter did not submit the payment dialog')
    await w.mutated(f'payment recorded on {inv}', "([n, before]) => JSON.stringify(DB.payments || []).length > before || DB.clients.some(c => (c.invoices || []).some(d => d.number === n && /paid/.test(d.status || '')))", [inv, pay0])



async def walk_controller(w):
    pg = w.pg
    w.step('Banking > Reconcile > Start Reconciling')
    await w.click('Banking', prefix=True)
    n0 = await pg.evaluate("() => (DB.bankRecons || []).length")
    await w.click('Reconcile')
    await w.click('Start Reconciling', wait=800)
    w.step('Finish Now (the statement balances)')
    if not await w.see('$0.00'):
        w.note('the difference is not $0.00 on opening the statement')
    await w.toast_mark()
    await w.click('Finish Now', wait=800)
    for label in ('Finish', 'Finish Reconciling', 'Reconcile', 'Confirm'):
        if await w.find(label, css='#mbm button, .modal button, [role=dialog] button'):
            await w.click(label, css='#mbm button, .modal button, [role=dialog] button', wait=800); break
    await w.mutated('Chase July reconciled', "n => (DB.bankRecons || []).length > n", n0)
    w.step('Open Close (Ledger > Close)')
    await w.click('Ledger', css='button, a, [role=tab]')
    await w.click('Close', css='button, a, [role=tab]')
    if not await w.see('Checklist') and not await w.see('Close August'):
        await w.flag('wrong record', 'Close did not open the month-end close')



LOG_JS = "() => JSON.stringify(DB.field || {}).includes('Pulled home runs on the 3rd floor') && /\"2026-09-03\"/.test(JSON.stringify((DB.field || {}).logs || DB.field))"
PCT_JS = "() => { const t = DB.projects.flatMap(p => (p.schedule || []).concat(p.tasks || [])).find(t => /^Rough electrical/.test(t.name || t.title || '')); return t ? t.pct : null }"

async def walk_foreman(w):
    pg = w.pg
    w.step('Clock In')
    await w.toast_mark()
    await w.click('Clock In', wait=600)
    await w.mutated('clocked in', "() => (DB.time || []).some(t => t.date === '2026-09-03' && t.empId && !t.out && t.source === 'phone')")

    w.step('Materials: Ask > Materials > task > one line > Next > Send > Done')
    await w.click('Ask', prefix=True, scope='.mbar, .m-bar, .bottombar, nav, footer, body', nth=0)
    await w.click('Materials or a tool', prefix=True)
    await w.fill('Framing & blocking', css='select')
    await w.fill('40 2x4x8 studs', css='textarea')
    await w.toast_mark()
    await w.click('Next', prefix=True, wait=700)
    await w.click('Send 1 Line', prefix=True, wait=800)
    sheet = await w.see('Request Sent')
    await w.mutated('materials request on 121 State', "() => DB.projects.some(p => (p.requests || []).some(r => /2x4x8 studs/.test(JSON.stringify(r))))")
    if sheet and w.flags and w.flags[-1]['kind'] in ('no toast', 'toast without Open'):
        w.flags[-1]['msg'] += ' (a "Request Sent" sheet confirms it instead, with Take It Back / Done)'
    await w.click('Done')

    w.step('Hidden condition: Ask > A problem or question > Hidden Condition > one line > Send')
    await w.click('Ask', prefix=True, scope='.mbar, .m-bar, .bottombar, nav, footer, body', nth=0)
    await w.click('A problem or question', prefix=True)
    await w.click('Hidden condition', prefix=True)
    await w.fill('Rotted sill under the rear window, about 6 feet', css='textarea')
    await w.toast_mark()
    await w.click('Send', wait=800)
    await w.mutated('hidden condition raised', "() => ((DB.field || {}).raises || []).some(r => /Rotted sill/.test(JSON.stringify(r)))")
    for t in ('Done', 'Close'):
        if await w.click(t, optional=True): break

    w.step('Daily Log with a % update (Daily Log > 7 steps > Sign)')
    # the tab was renamed "Log" -> "Daily Log" so it matches the page heading (screen standard)
    await w.click('Daily Log', scope='.mbar, .m-bar, .bottombar, nav, footer, body')
    await w.click('Clear')
    await w.fill('79', label='e.g. 78')
    for _ in range(3):
        await w.click('Next')
        if await w.find('What got done', css='input') or await w.see("Today's tasks"): break
    await w.toast_mark()
    pct0 = await pg.evaluate(PCT_JS)
    w.note(f'Rough electrical at {pct0}% before the update')
    await w.click('55%')
    await w.click('75%', wait=600)
    await w.mutated('Rough electrical 55% -> 75%', "() => (" + PCT_JS + ")() === 75")
    w.step('Daily Log: what got done > Delays > Photos > Sign Off')
    await w.fill_row('Rough electrical', 'Pulled home runs on the 3rd floor')
    await w.toast_mark()
    # Next through Delays, Photos to Sign Off. Delays refuses Next until yesterday's carried delay is
    # answered ("Is yesterday's delay still holding the work, or cleared?"): answer Cleared when asked.
    for _ in range(6):
        if await w.find('Sign and Send', prefix=True): break
        if await w.see("Is yesterday's delay still holding", timeout=300):
            await w.click('Cleared')
        if not await w.click('Next', optional=True): break
    await w.tick_row('true record')
    await w.click('Sign and Send', wait=900)
    await w.mutated('daily log for 9/3 filed', LOG_JS)




DEC_JS = "() => DB.projects.flatMap(p => p.decisions || []).filter(d => /bathroom finishes/i.test((d.clientTitle || '') + ' ' + (d.title || ''))).map(d => ({status: d.status, choice: d.choice || d.chosen || d.picked || d.clientChoice || null}))"

async def walk_client(w):
    pg = w.pg
    w.step('Decision: Choose > option card > Confirm Choice')
    before = await pg.evaluate(DEC_JS)
    w.note(f'2nd floor bathroom finishes before: {before}')
    await w.toast_mark()
    await w.click('Choose', within='bathroom finishes')
    await w.click('Zellige, hand-cut', prefix=True)
    await w.click('Confirm Choice', wait=800)
    await w.mutated('client chose Zellige', "b => JSON.stringify((" + DEC_JS + ")()) !== JSON.stringify(b) && /zellige/i.test(JSON.stringify(DB.projects.flatMap(p => p.decisions || []).filter(d => /bathroom finishes/i.test((d.clientTitle || '') + ' ' + (d.title || '')))))", before)
    for t in ('Done', 'Close'):
        if await w.click(t, optional=True, css='#mbm button, .modal button, [role=dialog] button'): break

    w.step('Approve the change order (CO-2026-002)')
    await w.toast_mark()
    await w.click('Approve', within='CO-2026-002')
    nm = await pg.evaluate("() => { const i = document.querySelector('#mbm input:not([type=checkbox])'); return i ? [i.value, i.placeholder] : null }")
    if nm and not nm[0]:
        await w.fill('Sarah Klein', css='#mbm input:not([type=checkbox])')
    await w.tick_row('I approve this change order')
    await w.click('Approve $', prefix=True, wait=900)
    await w.mutated('CO-2026-002 approved by the client', "() => DB.clients.flatMap(c => c.changeOrders || []).some(d => d.number === 'CO-2026-002' && d.status === 'approved')")



async def walk_designer(w):
    pg = w.pg
    w.step('My Day on landing')
    if not (await pg.evaluate("() => view") == 'sday' and await w.see('My Day')):
        await w.flag('next step hidden', 'the designer does not land on My Day')
    w.step('Hours Not Logged tile > the day sheet')
    await w.click('Hours Not Logged', prefix=True, wait=700)
    v = await pg.evaluate("() => view")
    if v != 'sday' and not await w.see('hrs'):
        await w.flag('wrong record', f'the My Day tile "Hours Not Logged" opens view "{v}" (Ask), not a day sheet: its go() sets view="time", '
                     'which the designer may not open (My Day tile list, app.js ~87350; ROLE_VIEWS.designer has no "time")')
        await w.click('Studio', prefix=True, scope='nav, aside, .rail, #rail')
        await w.click('My Day')
    w.step('Log hours from the day sheet (project > hrs > phase > what > Log)')
    t0 = await pg.evaluate("() => JSON.stringify(DB.time || []).length")
    await w.toast_mark()
    await w.fill('140 Prospect', css='.view.on select')
    await w.fill('2', label='hrs')
    await w.fill('Kitchen elevations for the rear wall change', label='what')
    await w.click('Log', css='.view.on button', wait=700)
    await w.mutated('2 h logged for Sarah on 9/3', "() => (DB.time || []).some(t => t.date === '2026-09-03' && /rear wall change/.test(JSON.stringify(t)))")


async def go_start(pg, view):
    """Navigation to the starting view, as the protocol allows."""
    await go(pg, view)


WALKS = {}
def walk(name, uid, phone=False, start=None):
    def deco(fn):
        WALKS[name] = (fn, uid, phone, start); return fn
    return deco

walk('owner', 'u_owner')(walk_owner)
walk('pm', 'u_alan')(walk_pm)
walk('coord', 'u_chen')(walk_coord)
walk('billing', 'u_billing')(walk_billing)
walk('controller', 'u_controller')(walk_controller)
walk('foreman', 'u_angel', phone=True)(walk_foreman)
walk('client', 'u_klein', phone=True)(walk_client)
walk('designer', 'u_sarah')(walk_designer)


async def run_walk(p, name):
    fn, uid, phone, start = WALKS[name]
    b, pg, errs = await open_app(p, phone)
    await sign_in(pg, uid)
    if start: await go_start(pg, start)
    await pg.evaluate(TOAST_HOOK)
    del errs[:]
    w = Walk(name, pg, errs)
    print(f'== {name} ({uid}{", phone" if phone else ""})')
    if os.path.isdir(SHOTS):
        for f in os.listdir(SHOTS):
            if f.startswith(name + '_') and f.endswith('.png'): os.remove(os.path.join(SHOTS, f))
    try:
        await fn(w)
    except DeadEnd:
        pass
    except Exception as e:
        await w.flag('dead end', f'walk crashed: {str(e).splitlines()[0][:200]}')
    # Persistence: reload the page (same context, same IndexedDB) and re-check every saved mutation.
    if w.persist:
        await pg.wait_for_timeout(1200)
        await pg.reload()
        await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
        for st, what, js, arg in w.persist:
            if not await pg.evaluate(js, arg):
                w.cur = {'step': st}
                await w.flag('not persisted', f'{what}: gone after a reload')
    await b.close()
    clicks, fields = w.cost
    keys = sum(s.get('keys', 0) for s in w.steps)
    for s in w.steps:
        t = s['toast']
        print(f"  - {s['step']}: {s['clicks']} clicks + {s['fields']} fields" + (f" + {s['keys']} Enter" if s.get('keys') else '')
              + (f"; hidden: {', '.join(s['hidden'])}" if s['hidden'] else '')
              + (f"; db {'ok' if s['db'] else 'NO'}" if s['db'] is not None else '')
              + (f"; toast \"{t['text'][:60]}\" links={t['links']}" if t else ''))
    print(f'  cost {clicks} clicks + {fields} fields' + (f' (+{keys} Enter)' if keys else '') + f' (round 4: {ROUND4.get(name, "-")}); {len(w.flags)} flags')
    return {'walk': name, 'user': uid, 'phone': phone, 'steps': w.steps, 'clicks': clicks, 'fields': fields, 'enter': keys,
            'round4': ROUND4.get(name), 'flags': w.flags, 'notes': w.notes}


async def main():
    args = sys.argv[1:]
    names = list(WALKS)
    if '--walk' in args:
        names = [n for n in args[args.index('--walk') + 1].split(',') if n]
        bad = [n for n in names if n not in WALKS]
        if bad: raise SystemExit(f'unknown walk {bad}; walks: {", ".join(WALKS)}')
    out = []
    async with async_playwright() as p:
        for n in names:
            out.append(await run_walk(p, n))
    nflags = sum(len(r['flags']) for r in out)
    if '--json' in args:
        print(json.dumps(out, indent=1, default=str))
    print(f'{nflags} flags')
    sys.exit(1 if nflags else 0)


if __name__ == '__main__':
    asyncio.run(main())
