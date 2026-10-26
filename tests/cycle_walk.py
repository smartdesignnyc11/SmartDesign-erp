#!/usr/bin/env python3
"""tests/cycle_walk.py: Pilot 3's required work, replayed the way a person does it (Alan, 2026-10-26).

"All these checks pass and then as soon as we do actual work, we fail almost immediately." The net drives the app by
calling its functions on seeded data; this suite drives it only through the screens, with the agent harness's own verbs
(sim/server.py /act: go by menu label, tap by label, type into a labelled field, pick a visible option, do batches), on
a NEW client and job (the Ashbys, 214 Lincoln Place, sim/cycle_book.json), with no AI and no randomness of its own.

  J1 owner      the inquiry mail > a lead > won > the client > the project
  J2 pm         the radiator asked back to the client (mail), then the 12-line estimate from the takeoff, every line
                (description, quantity, unit, price, cost), tied to the project
  J3 pm         the estimate sent to the Ashbys
  J4 owner      the Ashbys' signature (their signed copy, by world rules) recorded; the contract and the SOV
  J5 coord      one RFQ from three estimate lines at once, sent to three vendors
  J6 coord      the quotes recorded from the vendors' replies; the award
  J7 coord      POs from the lines: one PO with several lines, the tile, two buys on the same plumbing line; sent
  J8 billing    the deposit invoice from the contract, sent

Every journey runs twice: on the desktop (1440) and on the phone (390). The desktop chain runs first and keeps a
checkpoint of the company before each journey; each phone journey starts from that checkpoint in its own world, so a
phone failure upstream never hides a phone failure downstream. Per journey and device it records the taps (every tap,
type, pick, go, back and key, each step of a `do` counted) and the wall time, and holds the taps to TAP_BUDGET.
After each journey the records are read raw (db.json, the harness's snapshot) and graded with sim/cycle.py's own step
checks (C01-C14, C30): right, or the suite fails with the step, the screen, the last control and what it expected.

Then the dangerous-button class (Pilot 3 day 1): for every bill, estimate, invoice, PO and obligation in a held, paid,
posted or draft state, on the owner's, the PM's, the coordinator's and billing's screens, phone and desktop:
  - the blue button and the first button are a safe next step for that state (no Approve on a held or paid bill, no
    Mark Sent first under a draft nobody has reviewed, no Record Payment on a draft invoice ...);
  - no sheet opens prefilled to record something that has not happened (Draft the Renewal opening Record the Filing
    with today's date in Filed On);
  - no "recommended / approved by <person>" stamp without that person's own action in the audit trail.

    python3 tests/cycle_walk.py                 everything (about 40-70 minutes on this machine; run it through tests/slot.sh)
    python3 tests/cycle_walk.py --only J2       one journey (the chain up to it runs on the desktop first)
    python3 tests/cycle_walk.py --devices desktop --no-danger
    python3 tests/cycle_walk.py --attach <run>  drive a world already running (development)

Writes review/cycle_walk/report.md and report.json; the last line is `CYCLE WALK N checks · F failed`; exit 1 on any failure.
docs/CYCLE_WALK.md says how to add a journey.
"""
import argparse, json, os, re, shutil, signal, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SIM = os.path.join(ROOT, 'sim')
RUNS = os.path.join(SIM, 'runs')
OUT = os.path.join(ROOT, 'review', 'cycle_walk')
sys.path.insert(0, SIM)
import cycle as CY   # the referee's step checks, on the raw records


# ---------------------------------------------------------------------------------------------------- the lint
# This suite may touch the app only through the harness's verbs. A call that writes the page, runs app code or jumps
# a view fails the suite before anything runs. The patterns are built from pieces so this block does not match itself.
_J = ''.join
FORBIDDEN = [
    (_J(['\\.', 'evaluate', '\\(']), 'running JavaScript in the page'),
    (_J(['\\bview', '\\s*=\\s*[\'"]']), 'jumping a view'),
    (_J(['\\brender', '\\(\\)']), 'calling the app\'s render'),
    (_J(['\\bgo', '\\(\\s*pg']), 'the old harness navigation'),
    (_J(['sign', 'In\\(']), 'signing in by code'),
    (_J(['debug', '[_-]eval']), 'the developer eval'),
    (_J(['play', 'wright']), 'a browser of its own'),
    (_J(['import ', 'harness']), 'the old harness'),
    (_J(['\\bDB', '\\.']), 'the app\'s DB object'),
    (_J(['save', 'Now\\(']), 'the app\'s save'),
]
ADMIN_OK = {'status', 'begin_turn', 'end_turn', 'world', 'cycle', 'world_client', 'slot', 'shutdown', 'party', 'advance'}   # never 'script', 'check', 'debug_eval'
VERBS_OK = {'screen', 'find', 'tap', 'type', 'pick', 'do', 'go', 'back', 'key', 'scroll', 'mail', 'news', 'call', 'device'}


def lint_self():
    src = open(os.path.abspath(__file__), encoding='utf-8').read().split('\n')
    bad = []
    for i, line in enumerate(src, 1):
        code = line.split('#')[0] if not line.lstrip().startswith(('"', "'")) else line
        for rx, why in FORBIDDEN:
            if re.search(rx, code): bad.append(f'line {i}: {why}: {line.strip()[:100]}')
    return bad


# ---------------------------------------------------------------------------------------------------- tap budgets
# Twice what a professional needs for the journey (PATH_TO_9 wave 5 has a target only for the foreman's log), counted
# the way the harness counts a person's actions: every tap, type, pick, go, back and key.
TAP_BUDGET = {
    'J1b': 40,   # the same, on the proposal path, and a look at the estimate's Project: ~20
    'J1': 40,    # open the mail, accept the proposed lead (3 fields), convert with the value, won, the project (4 fields): ~20
    'J2': 160,   # the question back (1), find the estimate (3), 12 lines x (description, price, quantity, unit, cost, add): ~78
    'J3': 12,    # open the estimate, review, send it to the client: ~6
    'J4': 20,    # open the signed copy, record the signature (who, when), the contract and SOV from the estimate: ~10
    'J5': 56,    # three new vendors (name, trade, kind, contact, email, add: 18), pick three lines, Create RFQ, the foreman's check, three vendors, send: ~28
    'J6': 36,    # three quotes (vendor, total, lead time) from the mail, the award: ~18
    'J7': 50,    # a PO of two lines, the tile PO, two plumbing buys, each sent: ~25
    'J8': 14,    # the deposit invoice from the contract, sent: ~7
}
DEVICES = ('desktop', 'phone')
DANGER_ROLES = ('u_owner', 'u_alan', 'u_chen', 'u_billing')
SEED = 9806211


# ---------------------------------------------------------------------------------------------------- the world
class World:
    """One sim/server.py world: started fresh (or resumed from a checkpoint) on a pinned copy of the build."""

    def __init__(self, run, dist, resume_from=None, attach=False):
        self.run, self.dir, self.proc = run, os.path.join(RUNS, run), None
        self.dist, self.resume_from, self.attached = dist, resume_from, attach

    def start(self):
        if self.attached: return self
        if os.path.exists(self.dir): shutil.rmtree(self.dir)
        args = [sys.executable, os.path.join(SIM, 'server.py'), '--run', self.run, '--seed', str(SEED)]
        if self.resume_from:
            shutil.copytree(self.resume_from, self.dir, ignore=shutil.ignore_patterns('server.json', 'shots', 'files'))
            args.append('--resume')
        os.makedirs(self.dir, exist_ok=True)
        env = dict(os.environ, SIM_DIST=self.dist, SIM_RUN=self.run)
        env.pop('SIM_AI_TOKEN', None); env.pop('SIM_AI_TOKEN_FILE', None)   # no AI: the assistant answers from its rules
        self.log = open(os.path.join(RUNS, f'{self.run}.server.log'), 'w')
        self.proc = subprocess.Popen(args, cwd=ROOT, env=env, stdout=self.log, stderr=subprocess.STDOUT)
        t0 = time.time()
        while time.time() - t0 < 600:
            if self.proc.poll() is not None: raise SystemExit(f'the world {self.run} did not start: {open(self.log.name).read()[-800:]}')
            if 'sim: ready' in open(self.log.name).read(): break
            time.sleep(1)
        else: raise SystemExit(f'the world {self.run} did not get ready in 10 minutes')
        self.boot_s = round(time.time() - t0, 1)
        return self

    def _post(self, path, body, admin=False):
        port = json.load(open(os.path.join(self.dir, 'server.json')))['port']
        h = {'Content-Type': 'application/json'}
        if admin: h['X-Sim-Token'] = open(os.path.join(self.dir, '.admin_token')).read().strip()
        req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=json.dumps(body).encode(), headers=h)
        with urllib.request.urlopen(req, timeout=900) as f: return json.loads(f.read())

    def admin(self, cmd, **kw):
        assert cmd in ADMIN_OK, f'admin {cmd} is not a world control this suite may use'
        return self._post('/admin', {'cmd': cmd, **kw}, admin=True)

    def act(self, uid, cmd, args=(), **opts):
        assert cmd in VERBS_OK, cmd
        return self._post('/act', {'uid': uid, 'cmd': cmd, 'args': [str(a) for a in args], 'opts': opts})

    def db(self):
        return json.load(open(os.path.join(self.dir, 'db.json'), encoding='utf-8'))

    def world_state(self):
        return json.load(open(os.path.join(self.dir, 'world.json'), encoding='utf-8'))

    def cycle(self):
        st = self.world_state(); W = st.get('world') or {}
        return CY.Cycle(self.db(), CY.load_book(), {'gated': W.get('gated', {}), 'calls': st.get('calls', []), 'interrupts_done': W.get('interrupts_done', {})}, None, st.get('day'))

    def checkpoint(self, name):
        """a copy of the company as it is now (the turn closed, everything saved), for the phone's own world"""
        d = os.path.join(RUNS, f'{self.run}.ck', name)
        if os.path.exists(d): shutil.rmtree(d)
        shutil.copytree(self.dir, d, ignore=shutil.ignore_patterns('server.json', 'shots', 'files'))
        return d

    def stop(self):
        if self.attached or not self.proc: return
        try: self.admin('shutdown')
        except Exception: pass
        try: self.proc.wait(60)
        except Exception:
            self.proc.send_signal(signal.SIGKILL)


# ---------------------------------------------------------------------------------------------------- the screen
CTL_RX = re.compile(r'\[(\d+)(?: (tab|link))?(?: ([^\[\]]*?))?\](\{blue\})?(\{disabled\})?')
FLD_RX = re.compile(r'\[(\d+) (input|select|text|date|check|file) "([^"]*)"(?: =?"([^"]*)")?(?: (on|off))?(?: \{([^}]*)\})?')
CHROME = re.compile(r'^(Thu|Fri|Mon|Tue|Wed|Sat|Sun) \w{3} \d+ \d\d:\d\d · ')


class Ctl:
    def __init__(self, n, kind, label, pos, line, value='', opts=None, blue=False, disabled=False, state=None):
        self.n, self.kind, self.label, self.pos, self.line = n, kind, label, pos, line
        self.value, self.opts, self.blue, self.disabled, self.state = value, opts or [], blue, disabled, state

    @property
    def action(self): return self.kind in ('button', 'tab', 'link')

    def __repr__(self): return f'[{self.n} {self.kind} "{self.label}"' + (f' ={self.value}' if self.value else '') + (' blue' if self.blue else '') + ']'


def norm(s): return re.sub(r'\s+', ' ', str(s or '')).strip().lower()


class Screen:
    """The text the harness returns for a screen, read back into its controls in reading order."""

    def __init__(self, text):
        self.text = text or ''
        lines = self.text.split('\n')
        self.head = lines[0] if lines else ''
        self.title = self.head.split(' · ')[-1] if CHROME.match(self.head) else ''
        self.menu = next((l[6:].split(' · ') for l in lines[:3] if l.startswith('Menu: ')), [])
        self.sheet = '== Open on top ==' in self.text
        self.sheet_title = ''
        if self.sheet:
            after = self.text.split('== Open on top ==', 1)[1].split('\n')
            bare = [re.sub(r'\[\d+[^\]]*\]', '', l).strip() for l in after]
            self.sheet_title = next((b for b in bare if b), '')
        self.ctls, taken = [], set()
        for m in FLD_RX.finditer(self.text):
            n = int(m.group(1)); taken.add(m.start())
            opts = [o for o in (m.group(6) or '').split('|') if o and not re.match(r'^\+\d+ more$', o)]
            self.ctls.append(Ctl(n, m.group(2), m.group(3), m.start(), self.text.count('\n', 0, m.start()), m.group(4) or '', opts,
                                 state=m.group(5)))
        for m in CTL_RX.finditer(self.text):
            if m.start() in taken: continue
            lab = (m.group(3) or '').strip()
            if re.match(r'^(input|select|text|date|check|file) "', lab): continue
            self.ctls.append(Ctl(int(m.group(1)), m.group(2) or 'button', lab, m.start(), self.text.count('\n', 0, m.start()),
                                 blue=bool(m.group(4)), disabled=bool(m.group(5))))
        self.ctls.sort(key=lambda c: c.pos)
        for c in self.ctls:   # a row or card is one control around its words: its label is the words after it
            if c.action and not c.label:
                m = re.match(r'\]\S*\s*([^\[]{1,200})', self.text[self.text.find(']', c.pos):])
                c.label = re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''

    def where(self, anchor):
        if anchor is None: return 0
        i = self.text.lower().find(anchor.lower())
        return i if i >= 0 else None

    def find(self, label, field=False, after=None, nth=1, exact=False, kinds=None):
        """the control a person means by this label: exact first, then starts-with, then contains, optionally the first
        one after the text `after` (the line it sits on), the nth of several"""
        start = self.where(after)
        if start is None: return None
        want = norm(label)
        C = [c for c in self.ctls if c.pos >= start and (c.action != field) and (not kinds or c.kind in kinds)]
        strip = lambda s: re.sub(r'\s*\d+$', '', norm(s))
        for test in ((lambda c: norm(c.label) == want or strip(c.label) == want),) + (() if exact else (
                lambda c: norm(c.label).startswith(want), lambda c: want in norm(c.label))):
            hit = [c for c in C if test(c)]
            if len(hit) >= nth: return hit[nth - 1]
        return None

    def actions(self, region=None):
        txt0 = 0
        if region == 'sheet' and self.sheet: txt0 = self.text.find('== Open on top ==')
        end = self.text.find('== Behind it:') if region == 'sheet' and self.sheet else len(self.text)
        return [c for c in self.ctls if c.action and txt0 <= c.pos < (end if end > 0 else len(self.text))]

    def has(self, text): return text.lower() in self.text.lower()

    def next_action(self, text):
        """the first button or link after the words (a card's own button)"""
        i = self.text.find(text) if text else -1
        if i < 0: return None
        return next((c for c in self.ctls if c.pos > i and c.action and c.kind in ('button', 'link')), None)

    def row(self, text, after=None):
        """the row a person taps for a record: the first control on the first line that carries its words"""
        start = self.where(after) or 0
        L = self.text.split('\n'); pos = 0
        for i, l in enumerate(L):
            if pos >= start and text.lower() in l.lower():
                C = [c for c in self.ctls if c.line == i and c.action]
                if C: return C[0]
                C = [c for c in self.ctls if i - 3 <= c.line < i and c.action and self.text.split('\n')[c.line].lstrip().startswith('[')]
                if C: return C[-1]
            pos += len(l) + 1
        return None

    def excerpt(self, around=None, n=14):
        L = [l for l in self.text.split('\n') if l.strip()]
        if around:
            i = next((k for k, l in enumerate(L) if around.lower() in l.lower()), None)
            if i is not None: return '\n'.join(L[max(0, i - 3): i + n])
        return '\n'.join(L[:n])


def screen_of(txt):
    L = (txt or '').split('\n')
    i = next((k for k, l in enumerate(L) if CHROME.match(l)), None)
    sc = Screen('\n'.join(L[i:]) if i is not None else '')
    sc.toast = ' / '.join(l[7:] for l in L[:i or 0] if l.startswith('Toast: ')) + ''.join(' / ' + l[8:] for l in L if l.startswith('Toasts: '))
    sc.reply = '\n'.join(L[:i or 0])
    return sc


class Stuck(Exception):
    """a person could not go on: the step, the screen, the last control and what they expected"""
    def __init__(self, what, expected, screen=None, control=None):
        super().__init__(what)
        self.what, self.expected, self.screen, self.control = what, expected, screen, control


class Person:
    """One person on one device, acting only through the harness's verbs; every action is counted."""
    TAPS = {'tap', 'type', 'pick', 'go', 'back', 'key'}

    def __init__(self, world, uid, device, journey, log):
        self.w, self.uid, self.device, self.j, self.log = world, uid, device, journey, log
        self.taps, self.calls, self.scr, self.last_control, self.trail = 0, 0, Screen(''), '', []
        self.soft = []   # expectations that failed while the person could still go on

    # ---- the verbs
    def _act(self, cmd, *args, **opts):
        self.calls += 1
        if cmd in ('tap', 'go', 'back', 'key', 'do'): opts = dict({'full': True, 'marks': True}, **opts)   # the whole screen, as the eye takes it in
        r = self.w.act(self.uid, cmd, args, **opts)
        txt = r.get('text') or ''
        if cmd in self.TAPS: self.taps += 1
        self.trail.append(f'{cmd} ' + ' '.join(f'"{a}"' for a in args)[:120] + ('' if r.get('ok', True) else '  -> ' + txt.split('\n')[0][:120]))
        return r, txt

    def look(self, full=True, marks=False):
        r, txt = self._act('screen', **({'full': True} if full else {}), **({'marks': True} if marks else {}))
        self.scr = screen_of(txt)
        return self.scr

    def go(self, label, expect_menu=True):
        """the menu entry a person reads in their menu (the rail, or the tab bar and More on the phone)"""
        if expect_menu and self.scr.text and self.scr.menu and not any(norm(re.sub(r'\s+\d+$', '', m)) == norm(label) for m in self.scr.menu):
            self.expect(False, f'"{label}" in the menu', f'the menu has: {" · ".join(self.scr.menu)}')
        if self.scr.sheet: self._act('back')   # a sheet left open is closed first, as a person does
        self.last_control = f'menu: {label}'
        r, txt = self._act('go', label)
        if not r.get('ok'): raise Stuck(f'go to {label}', f'"{label}" in the menu', screen_of(txt) if CHROME.search(txt) else self.scr, self.last_control + ': ' + txt[:200])
        self.scr = screen_of(txt)
        return self.scr

    def _target(self, label, field, after, nth, exact=False, kinds=None):
        c = self.scr.find(label, field, after, nth, exact, kinds) if self.scr.text else None
        if c is None:
            self.look()
            c = self.scr.find(label, field, after, nth, exact, kinds)
        return c

    def tap(self, label, after=None, nth=1, expect=None, exact=False, kinds=None):
        c = self._target(label, False, after, nth, exact, kinds)
        if c is None: raise Stuck(f'tap "{label}"' + (f' (after "{after}")' if after else ''), f'a control labelled "{label}"', self.scr, self.last_control)
        if c.disabled: raise Stuck(f'tap "{label}"', f'"{label}" can be tapped (it is greyed out)', self.scr, c.label)
        self.last_control = c.label
        r, txt = self._act('tap', c.n)
        self.trail[-1] += f'  ({c.label[:60]})'
        if not r.get('ok') and self.landed_slow(txt, c.label): r = {'ok': True}; txt = self.look().text
        if not r.get('ok'): raise Stuck(f'tap "{label}"', 'the tap to land', screen_of(txt), c.label + ': ' + txt.split(chr(10))[0][:160])
        self.scr = screen_of(txt)
        if expect and not self.scr.has(expect):
            self.look()
            if not self.scr.has(expect): raise Stuck(f'tap "{label}"', f'"{expect}" on the screen after it', self.scr, c.label)
        return self.scr

    def landed_slow(self, txt, label):
        if 'Toast: ' in txt and 'Timeout' in txt:
            self.expect(False, f'the screen settles after "{label}" (it was still busy after 30 seconds)', txt.split(chr(10))[0][:200])
            return True
        return False

    def expand(self):
        """a record's collapsed header on the phone ("Invoice · Fri, Sep 4 · due Mon, Sep 21"): tap it open"""
        c = next((x for x in self.look().ctls if x.action and re.search(r' · .*(due|valid to) ', x.label)), None)
        if not c: return False
        self.last_control = c.label
        self._act('tap', c.n); self.look()
        return True

    def tap_ctl(self, c, expect=None):
        if not c or not c.n: raise Stuck('tap', 'the control on the screen', self.scr, self.last_control)
        self.last_control = c.label
        r, txt = self._act('tap', c.n)
        self.trail[-1] += f'  ({c.label[:60]})'
        if not r.get('ok'): raise Stuck(f'tap "{c.label}"', 'the tap to land', screen_of(txt), c.label + ': ' + txt.split(chr(10))[0][:160])
        self.scr = screen_of(txt)
        if expect and not self.scr.has(expect):
            self.look()
            if not self.scr.has(expect): raise Stuck(f'tap "{c.label}"', f'"{expect}" on the screen after it', self.scr, c.label)
        return self.scr

    def pick_ctl(self, c, option):
        self.last_control = c.label
        r, txt = self._act('pick', c.n, option)
        if not r.get('ok'): raise Stuck(f'pick "{option}" in "{c.label}"', f'"{option}" among the options', self.scr, c.label + ': ' + txt[:160])
        self.scr.toast = ' / '.join(l[7:] for l in txt.split(chr(10)) if l.startswith('Toast: '))
        return c

    def tap_row(self, text, after=None, expect=None):
        c = self.scr.row(text, after) if self.scr.text else None
        if c is None: self.look(); c = self.scr.row(text, after) or self.scr.row(text)
        if c is None: raise Stuck(f'open "{text}"', f'a row for "{text}" on the screen', self.scr, self.last_control)
        self.last_control = c.label or text
        r, txt = self._act('tap', c.n)
        self.trail[-1] += f'  (row: {text[:50]})'
        if not r.get('ok'): raise Stuck(f'open "{text}"', 'the tap to land', screen_of(txt), c.label + ': ' + txt.split(chr(10))[0][:160])
        self.scr = screen_of(txt)
        if expect and not self.scr.has(expect):
            self.look()
            if not self.scr.has(expect): raise Stuck(f'open "{text}"', f'"{expect}" on the screen after it', self.scr, c.label)
        return self.scr

    def type(self, label, text, after=None, nth=1):
        c = self._target(label, True, after, nth)
        if c is None: raise Stuck(f'type into "{label}"', f'a field labelled "{label}"' + (f' after "{after}"' if after else ''), self.scr, self.last_control)
        self.last_control = c.label
        r, txt = self._act('type', c.n, text)
        if not r.get('ok'): raise Stuck(f'type into "{label}"', 'the field to take the text', screen_of(txt), c.label + ': ' + txt.split(chr(10))[0][:160])
        return c

    def pick(self, label, option, after=None, nth=1):
        c = self._target(label, True, after, nth)
        if c is None: raise Stuck(f'pick "{option}" in "{label}"', f'a list labelled "{label}"', self.scr, self.last_control)
        self.last_control = c.label
        r, txt = self._act('pick', c.n, option)
        if not r.get('ok'): raise Stuck(f'pick "{option}" in "{label}"', f'"{option}" among the options', self.scr, c.label + ': ' + txt[:160])
        return c

    def do(self, steps, _again=True):
        """a person's run of quick actions (up to 8), each resolved to its control on the screen in front of them"""
        try:
            return self._do(steps)
        except Stuck as e:
            if _again and 'Timeout' in (e.control or '') and self.expand():
                return self.do(steps, False)
            raise

    def _do(self, steps):
        out = []
        for verb, *a in steps:
            if verb == 'type':
                c = self._target(a[0], True, a[2] if len(a) > 2 else None, a[3] if len(a) > 3 else 1)
                if c is None: raise Stuck(f'type into "{a[0]}"', f'a field labelled "{a[0]}"', self.scr, self.last_control)
                out.append(f'type {c.n} {json.dumps(str(a[1]))}')
            elif verb == 'pick':
                c = self._target(a[0], True, a[2] if len(a) > 2 else None, a[3] if len(a) > 3 else 1)
                if c is None: raise Stuck(f'pick in "{a[0]}"', f'a list labelled "{a[0]}"', self.scr, self.last_control)
                out.append(f'pick {c.n} {json.dumps(str(a[1]))}')
            elif verb == 'tap':
                c = self._target(a[0], False, a[1] if len(a) > 1 else None, a[2] if len(a) > 2 else 1)
                if c is None: raise Stuck(f'tap "{a[0]}"', f'a control labelled "{a[0]}"', self.scr, self.last_control)
                out.append(f'tap {c.n}')
            self.last_control = c.label
        for i in range(0, len(out), 8):
            r, txt = self._act('do', '; '.join(out[i:i + 8]))
            self.taps += len(out[i:i + 8])
            self.scr = screen_of(txt)
            if not r.get('ok'):
                raise Stuck('do ' + '; '.join(out[i:i + 8])[:160], 'every step to land', self.scr, self.last_control + ': ' + txt.split('\n')[0][:200])
        return self.scr

    def do_ctls(self, steps):
        """a batch on controls already read off the screen: ('type', ctl, text) / ('pick', ctl, option) / ('tap', ctl)"""
        out = []
        for st in steps:
            verb, c = st[0], st[1]
            if c is None: raise Stuck(f'{verb} {st[2] if len(st) > 2 else ""}', 'the field on the screen', self.scr, self.last_control)
            out.append(f'{verb} {c.n}' + (f' {json.dumps(str(st[2]))}' if len(st) > 2 else ''))
            self.last_control = c.label
        for i in range(0, len(out), 8):
            r, txt = self._act('do', '; '.join(out[i:i + 8]))
            self.taps += len(out[i:i + 8])
            self.scr = screen_of(txt)
            if not r.get('ok'):
                raise Stuck('do ' + '; '.join(out[i:i + 8])[:160], 'every step to land', self.scr, self.last_control + ': ' + txt.split('\n')[0][:200])
        return self.scr

    def mail(self, *args):
        r, txt = self._act('mail', *args)
        if not r.get('ok'): raise Stuck('mail ' + ' '.join(args)[:80], 'the mail to go', self.scr, 'mail: ' + txt[:200])
        self.taps += 1
        return txt

    def expect(self, cond, expected, got='', stop=False):
        """an outcome a person checks with their eyes; a miss is a failure of the journey, and stops it if `stop`"""
        if cond: return True
        f = {'journey': self.j, 'device': getattr(self, 'jdev', self.device), 'step': (f'({self.uid} on the {self.device}) ' if getattr(self, 'jdev', self.device) != self.device else '') + expected, 'screen': self.scr.title or self.scr.head[:60],
             'control': self.last_control, 'expected': expected, 'got': got[:300]}
        self.soft.append(f)
        if stop: raise Stuck(expected, expected, self.scr, self.last_control)
        return False


# ---------------------------------------------------------------------------------------------------- the book
BOOK = CY.load_book()
TAKEOFF = BOOK['takeoff']
JOB = BOOK['job']


# ---------------------------------------------------------------------------------------------------- the journeys
def inquiry_to_won(p, subject, client, value, close):
    """the owner: an inquiry mail becomes a lead (the app's own proposal from the mail), an opportunity, then won"""
    p.go('Messages')
    p.tap('Mail', kinds=('tab',))
    p.tap_row(subject, expect='New lead')
    p.tap('Apply', after='New lead', expect='New Lead from This Message')
    p.do([('type', 'Name', client), ('pick', 'Building', 'Townhouse'), ('type', 'Due', '2026-09-04'), ('tap', 'New Lead')])
    p.expect('is a lead' in p.scr.toast, 'a toast that the lead was made, with Open', p.scr.toast)
    p.go('Sales')
    p.tap_row(client, expect='Convert to Opportunity')
    p.tap('Convert to Opportunity', expect='Opportunity Name')
    p.do([('type', 'Value', str(int(value))), ('tap', 'Convert')])
    p.tap('Closed Won', expect='Close as Won')
    p.tap(close, exact=True)
    p.expect(not p.scr.toast or norm(client) in norm(p.scr.toast) and not re.search(r'— design-build is a client', norm(p.scr.toast)),
             f'the toast names the client that was made ({client})', p.scr.toast)


def new_project(p, name, addr, start, client):
    p.go('Projects')
    p.tap('New Project', expect='Project Name')
    p.do([('type', 'Project Name', name), ('type', 'Address / Scope', addr), ('type', 'Start Date', start), ('pick', 'Client', client), ('tap', 'Add Project')])
    p.expect('Created' in p.scr.toast, 'a toast that the project was made, with Open', p.scr.toast)


def j1_owner_sales(p):
    """The owner, as the book has it: the Ashbys' mail becomes a lead, the lead is won, the client and the project open."""
    inquiry_to_won(p, '214 Lincoln Place: thank you for yesterday', JOB['client'], sum(t['qty'] * t['price'] for t in TAKEOFF), 'Close as Won')
    new_project(p, JOB['job'], JOB['addr'], JOB['start'], JOB['client'])


PROBE = {'client': 'Nadia Okoro', 'job': '88 Garfield Place', 'subject': 'Renovating 88 Garfield Place', 'addr': '88 Garfield Place, Park Slope: kitchen'}


def j1b_owner_proposal_first(p):
    """The owner on another inquiry (the world's Nadia Okoro, 88 Garfield Place), taking the app's own next step at won,
    Close and Start the Proposal: the estimate starts before the job exists. Can it be tied to its job?"""
    inquiry_to_won(p, PROBE['subject'], PROBE['client'], 120000, 'Close and Start the Proposal')
    p.look()
    f = p.scr.find('Project', field=True)
    p.expect(f is not None and (any(o not in ('—', '-', '') for o in f.opts) or any('new project' in norm(o) for o in f.opts)),
             'the new estimate\'s Project list offers the job, or a way to open it, so the estimate can be tied to its project',
             f'Project = "{f.value if f else ""}", options {{{"|".join(f.opts) if f else ""}}}')
    num = (re.findall(r'EST-\d{4}-\d+', p.scr.text) or [''])[0]
    new_project(p, PROBE['job'], PROBE['addr'], JOB['start'], PROBE['client'])
    p.go('Sales')
    p.tap('Estimates', exact=True)
    p.tap_row(num or PROBE['client'], after='Search', expect='Estimate EST-')
    f = p.scr.find('Project', field=True)
    p.expect(f is not None and norm(f.value) == norm(PROBE['job']), f'{num} shows its job, {PROBE["job"]}, once the job is open', f'Project = "{f.value if f else ""}"')


def probe_tied(w):
    """the records: the proposal started at won is on the job (its projectId), not only shown on it"""
    db = w.db()
    c = next((c for c in db['clients'] if norm(c.get('name')) == norm(PROBE['client'])), None)
    if not c: return 'not done', 'no client Nadia Okoro'
    pj = next((x for x in db['projects'] if x.get('clientId') == c['id']), None)
    E = [e for e in c.get('estimates') or [] if e.get('status') != 'void']
    if not E: return 'not done', 'no estimate for Nadia Okoro'
    if not pj: return 'not done', 'no project for Nadia Okoro'
    bad = [e['number'] for e in E if e.get('projectId') != pj['id']]
    return ('wrong', f"{', '.join(bad)} shows {PROBE['job']} in Project but is not on it in the records (projectId empty): converting it opens a second job") if bad \
        else ('right', f"{E[0]['number']} on {pj['id']}")


def open_estimate(p, menu_check=False, create=False):
    """where the PM looks for the Ashbys' estimate: Estimates in the menu; else the job's own Estimates"""
    if menu_check:
        p.expect(any(norm(re.sub(r'\s+\d+$', '', m)) == 'estimates' for m in p.scr.menu),
                 'Estimates in the PM\'s menu', 'the menu has: ' + ' · '.join(p.scr.menu))
    p.go('Projects', expect_menu=False)
    sw = p.scr.find('Switch project', field=True)
    if sw and norm(sw.value) != norm(JOB['job']): p.pick('Switch project', JOB['job'])
    elif not sw:
        r = p.look().row(JOB['job'], after='Every job') or p.scr.row(JOB['job'])
        if r: p.tap_ctl(r)
    p.tap('Estimates', exact=True)
    row = p.look().row('Wren & Julian Ashby', after='Search') or p.scr.row('EST-20', after='Search')
    if row is None and create:
        p.tap('New Estimate', exact=True, expect='Start Estimate')
        p.tap('Start Estimate', expect='Estimate EST-')
        return
    if row is None: raise Stuck('open the Ashbys\' estimate', 'the estimate in 214 Lincoln Place\'s Estimates', p.scr, p.last_control)
    p.tap_row('EST-20', after='Search', expect='Estimate EST-')


def line_fields(p, k):
    """line k's fields, in the order a person fills them: the card editor (Construction) or the table (Simple)"""
    sc = p.scr
    item = sc.find('Item name', field=True, nth=k)
    if item:   # the card editor: one card per line
        rate, qty = sc.find('Rate', field=True, nth=k), sc.find('Quantity', field=True, nth=k)
        unit = next((c for c in sc.ctls if qty and c.pos > qty.pos and not c.action), None)
        return item, rate, qty, unit, sc.find('budget', field=True, nth=k, exact=True)
    rows = [c for c in sc.ctls if c.kind == 'check' and norm(c.label) == 'select the line']
    if len(rows) < k: return None, None, None, None, None
    a = rows[k - 1].pos
    after = [c for c in sc.ctls if c.pos > a and not c.action]
    first = lambda rx: next((c for c in after if re.match(rx, norm(c.label))), None)
    return first(r'^item$'), first(r'^rate'), first(r'^qty'), first(r'^unit'), first(r'^(cost|budget)')


def j2_pm_estimate(p):
    """The PM: the radiator asked back to the Ashbys, then the 12 lines of the takeoff keyed into the estimate, tied to the job."""
    rad = BOOK['radiator']
    p.mail('send', 'Wren Ashby', '214 Lincoln Place: the garden bath radiator',
           'Wren, before we price the plumbing: do you want to keep the garden bath radiator where it is, or move it under the window? '
           f'Moving it is ${rad["price"]:,} more. Alan')
    open_estimate(p, menu_check=True, create=True)
    p.look()
    f = p.scr.find('Project', field=True)
    p.expect(f is not None and norm(f.value) == norm(JOB['job']), 'the estimate shows its project, 214 Lincoln Place',
             f'Project = "{f.value if f else "(no field)"}" {{{"|".join(f.opts) if f else ""}}}')
    if f and norm(JOB['job']) in [norm(o) for o in f.opts] and norm(f.value) != norm(JOB['job']):
        p.pick('Project', JOB['job'])
    saves_twice = False
    for k, t in enumerate(TAKEOFF, 1):
        if p.device == 'phone':
            phone_line(p, k, t); continue
        p.look()
        if not line_fields(p, k)[0]:
            p.tap('Add Line', exact=True)
            p.look()
        item, rate, qty, unit, cost = line_fields(p, k)
        if not item: raise Stuck(f'line {k}: the description', f'an empty line {k} to type into', p.scr, p.last_control)
        p.do_ctls([('type', item, t['item'])])   # the description may pull a price from the library and redraw the line
        item, rate, qty, unit, cost = line_fields(p.look() and p, k)
        p.do_ctls([('type', rate, t['price']), ('type', qty, t['qty']), ('type', unit, t['unit']), ('type', cost, t['cost'])])
        if p.scr.has('Unsaved changes') or p.look().has('Unsaved changes'):
            p.tap('Save', exact=True)
            if p.scr.has('Unsaved changes') or p.look().has('Unsaved changes'):
                saves_twice = True
                p.tap('Save', exact=True)
        p.expect(not p.look().has('Unsaved changes'), f'line {k} saved', p.scr.excerpt('Unsaved', 4))
    p.expect(not saves_twice, 'Save saves on the first tap after typing a line (it took a second tap)', 'the first Save after the last field left "Unsaved changes"')


def phone_line(p, k, t):
    """a line on the phone: Add Line Item, then whatever it opens (a sheet, or a new line on the page)"""
    p.look()
    m = re.search(r'(\d+) lines?\b', p.scr.text); n0 = int(m.group(1)) if m else 0
    if not (k == 1 and n0 == 1 and p.scr.has('Item name')):
        p.tap('Add Line Item')
        p.look()
    m = re.search(r'(\d+) lines?\b', p.scr.text); n1 = int(m.group(1)) if m else 0
    item = p.scr.find('Item name', field=True, nth=1) if not p.scr.sheet else (p.scr.find('Item', field=True) or p.scr.find('Description', field=True))
    if not p.scr.sheet and n1 <= n0 and not (item and not item.value):
        raise Stuck(f'line {k}: Add Line Item', f'a new line {k} to fill (a sheet, or line {k} on the page): the screen still says {n1} lines',
                    p.scr, 'Add Line Item')
    if p.scr.sheet:
        F = lambda rx: next((c for c in p.scr.ctls if not c.action and re.search(rx, c.label, re.I)), None)
        steps = [(F(r'item|descr'), t['item']), (F(r'rate|price'), t['price']), (F(r'qty|quant'), t['qty']), (F(r'unit|^ls$'), t['unit']), (F(r'cost|budget'), t['cost'])]
        missing = [x for (c, x) in steps if c is None]
        if missing: raise Stuck(f'line {k}: the line sheet', 'fields for description, price, quantity, unit and cost', p.scr, 'Add Line Item')
        p.do_ctls([('type', c, v) for c, v in steps])
        b = next((c for c in p.scr.actions('sheet') if re.match(r'(save|done|add)', norm(c.label))), None)
        if not b: raise Stuck(f'line {k}: the line sheet', 'a Save or Done on the line sheet', p.scr, p.last_control)
        p.tap(b.label, exact=True)
    else:
        item, rate, qty, unit, cost = line_fields(p, k)
        p.do_ctls([('type', item, t['item']), ('type', rate, t['price']), ('type', qty, t['qty']), ('type', unit, t['unit']), ('type', cost, t['cost'])])
def wait_for(p, sheet, secs=20, every=3):
    """a person waiting for a sheet to open (the drafting service, a slow sheet)"""
    t0 = time.time()
    while time.time() - t0 < secs:
        sc = p.look()
        if sc.sheet and norm(sheet) in norm(sc.sheet_title): return round(time.time() - t0, 1)
        time.sleep(every)
    return None


def est_number(p):
    return (re.findall(r'EST-\d{4}-\d+', p.scr.text) or [''])[0]


def j3_pm_send(p):
    """The PM sends the estimate to the Ashbys: the cover email, sent, and the estimate marked sent."""
    open_estimate(p)
    num = est_number(p)
    p.tap('Draft Cover Email')
    took = wait_for(p, 'Cover Email', 25)
    if took is None: raise Stuck('Draft Cover Email', 'the cover email to open', p.scr, 'Draft Cover Email')
    p.expect(took <= 5, 'the cover email opens within 5 seconds with the assistant off', f'it took {took}s')
    to = (p.scr.find('To', field=True) or Ctl(0, 'input', '', 0, 0)).value or JOB['emails'][0]
    subj = (p.scr.find('Subject', field=True) or Ctl(0, 'input', '', 0, 0)).value or f'{num} 214 Lincoln Place'
    body = (p.scr.find('Body', field=True) or Ctl(0, 'text', '', 0, 0)).value.replace('…', '')
    p.tap('Open in Mail App')
    p.expect(False, 'Send to Client sends the estimate from the app (it hands off to a mail app; nothing is sent or recorded)',
             'Open in Mail App opens a mailto: link; the PM sends from their own mailbox and comes back to Mark Sent')
    p.mail('send', to, subj, (body or f'Attached is estimate {num}.') + f'\n\nEstimate {num} attached (PDF). Alan')
    p.look()
    if not p.scr.has(num) or not p.scr.find('Mark Sent'): open_estimate(p)
    p.tap('Mark Sent', exact=True)
    p.expect(p.look().has('Sent'), f'{num} reads Sent', p.scr.excerpt('draft', 6))


def j4_owner_signed(p):
    """The owner: the Ashbys' signed copy (the world's reply to the estimate that reached them) recorded on the
    estimate with who and when; the contract and the schedule of values from the estimate."""
    p.go('Messages')
    p.tap('Mail', kinds=('tab',))
    p.tap_row(': signed', expect='accept it as written')
    num = (re.findall(r'EST-\d{4}-\d+', p.scr.text) or [''])[0]
    p.expect(bool(re.search(r'record (the )?(client )?approval|approved|signed .*EST-|mark .*approved', p.scr.text[p.scr.text.find('accept it as written'):], re.I)),
             f'the signed copy is read as {num} approved, with a proposal to record it (not only a note)',
             p.scr.excerpt('accept it as written', 10))
    p.go('Sales')
    p.tap('Estimates', exact=True)
    p.tap_row(num, after='Search', expect='Estimate EST-')
    if not p.scr.find('Record Client Approval'):
        p.tap('More', exact=True, after='Bill to')
    p.tap('Record Client Approval', expect='How They Approved')
    p.do([('type', 'How They Approved', 'Signed copy by email from Wren Ashby, 9/3 (Signed PDF on file)'), ('tap', 'Record Approval')])
    p.expect('approved' in norm(p.scr.toast), f'a toast that {num} is approved', p.scr.toast)
    p.look()
    if not p.scr.has('Converted'):   # an estimate on its job converts as it is approved; one that is not waits for this
        p.tap('Convert to Contract & SOV', expect='Please Confirm')
        p.tap('Yes, Continue')
        p.expect(not re.search(r'job created', p.scr.toast, re.I), 'the contract and SOV land on 214 Lincoln Place, the job already open (no second job)', p.scr.toast)
    p.look()
    if p.scr.has('read only'):
        ed = [c for c in p.scr.ctls if c.kind in ('input', 'text') and re.match(r'item name|rate|quantity|budget', norm(c.label))]
        p.expect(not ed, f'{num} reads "read only" and its lines cannot be typed into', f'{len(ed)} line fields still editable (Rate, Quantity, budget)')


def switch(p, uid, device):
    """another person picks up the work (a hand-off inside one journey); the journey's counts go on"""
    p.w.admin('end_turn')
    p.uid, p.device, p.scr = uid, device, Screen('')
    p.w.admin('begin_turn', uid=uid, slot=p.slot, cap=9999, device=device)
    p.look()


YARDS = [('Brooklyn Lumber', 'Sal Ferro', 'orders@brooklynlumber.example'), ('Gowanus Building Supply', 'Dee Marsh', 'orders@gowanusbuilding.example'),
         ('Atlantic Yard Supply', 'Ray Quint', 'sales@atlanticyardsupply.example')]
RFQ_LINES = ['Framing lumber: supply', 'Drywall & cement board: supply', 'Porcelain floor tile 12x24 matte: supply']


def j5_coord_rfq(p):
    """The coordinator: the three yards from the huddle on file, one RFQ from three estimate lines at once, the
    foreman's quantity check on his phone, the three yards picked, sent."""
    me, dev = p.uid, p.device
    p._act('news')
    p.go('Purchasing')
    p.tap('Vendors', exact=True)
    for name, who, mail in YARDS:
        if p.look().has(name): continue
        p.tap('New Vendor', expect='Add Vendor')
        p.do([('type', 'Name', name), ('type', 'Trade', 'Lumber & drywall'), ('pick', 'Kind', 'Supplier'), ('type', 'Contact', who), ('type', 'Email', mail), ('tap', 'Add Vendor')])
    p.tap('Quotes', exact=True)
    p.tap('New RFQ', expect='Which Lines?')
    p.pick('Job', JOB['job'])
    p.look()
    boxes = [p.scr.find(ln, field=True, kinds=('check',)) for ln in RFQ_LINES]
    p.expect(all(boxes), 'each of the three estimate lines can be ticked in Which Lines?', str(boxes))
    p.do_ctls([('tap', b) for b in boxes if b])
    p.tap('Create RFQ', exact=True)
    while p.scr.sheet and 'material list' in norm(p.scr.sheet_title):   # a lump-sum line: the app proposes a material list
        sc = p.look(marks=True)
        m = re.search(r'I propose these (\d+) materials', sc.text)
        blue = next((c for c in sc.actions('sheet') if c.blue), None)
        p.expect(not (m and int(m.group(1)) == 0 and blue and 'use this list' in norm(blue.label)),
                 'the blue button never proposes an empty material list for a lump-sum line', f'"{blue.label if blue else ""}" (blue) on "I propose these 0 materials"')
        p.tap('Keep the Line as Is', exact=True)
    rfq = (re.findall(r'RFQ-\d{4}-\d+', p.scr.toast) or re.findall(r'RFQ-\d{4}-\d+', p.look().text) or [''])[0]
    p.expect(bool(re.search(r'RFQ-\d{4}-\d+', p.scr.toast or '')) or bool(rfq), 'a toast naming the RFQ, with Open', p.scr.toast)
    if p.look().has('Foreman Review') or p.scr.has('Angel checks'):
        switch(p, 'u_angel', 'phone')
        c = p.scr.next_action(rfq or 'RFQ-20')
        p.expect(c is not None and bool(re.match(r'[A-Za-z]', c.label or '')), f'the foreman\'s {rfq} card has a labelled button', c.label if c else 'no card')
        if c is None: raise Stuck('the foreman checks the quantities', f'{rfq} under Materials to Check on his Today', p.scr, '')
        p.tap_ctl(c, expect='Check the Quantities')
        p.tap('Approve', exact=True)
        switch(p, me, dev)
        p.go('Purchasing')
        p.tap('Quotes', exact=True)
    p.look()
    open_rfq(p, rfq)
    want = [y[0] for y in YARDS]
    picks = [c for c in p.scr.ctls if c.kind == 'check' and c.label]
    steps = [('tap', c) for c in picks if (c.state == 'on') != any(norm(c.label).startswith(norm(w)) for w in want)]
    p.expect(all(any(norm(c.label).startswith(norm(w)) for c in picks) for w in want), 'the three yards from the huddle among the vendors to pick',
             'the picks: ' + '; '.join(c.label[:30] for c in picks))
    if steps: p.do_ctls(steps)
    p.tap('Send RFQ', exact=True)
    sent = bool(re.search(r'\bsent\b', p.scr.toast, re.I)) and not re.search(r'drafted', p.scr.toast, re.I)
    p.expect(sent, f'Send RFQ sends {rfq} to the vendors (its own note: "Send RFQ is the approval: one email per vendor")', p.scr.toast)
    if not sent: send_drafts(p, rfq)


def open_rfq(p, rfq):
    """the RFQ's own page: from its card on Quotes, unless Quotes still has it open"""
    if p.look().has('RFQs — ' + rfq): return
    p.tap('Open', after=rfq + ' · ', exact=True, expect='RFQs')


def send_drafts(p, rx):
    """what the app left in the person's mailbox as drafts, sent from the mailbox the way Gmail's Send does"""
    for _ in range(8):
        L = p.mail('drafts')
        hit = next((m for m in re.finditer(r'^(\d+)\. .*\| (.*)$', L, re.M) if re.search(re.escape(rx), m.group(2))), None)
        if not hit: return
        p.mail('senddraft', hit.group(1))


def j6_coord_quotes(p):
    """The coordinator: the yards' replies read into the RFQ (one in prose the app cannot read: typed in by hand), each
    price confirmed against the reply, leveled."""
    p.go('Purchasing')
    p.tap('Quotes', exact=True)
    rfq = (re.findall(r'RFQ-\d{4}-\d+', p.look().text) or [''])[0]
    open_rfq(p, rfq)
    if p.scr.find('Check Replies', exact=True): p.tap('Check Replies', exact=True)
    p.look()
    while p.scr.find('Enter Prices', exact=True):
        p.tap('Enter Prices', exact=True, expect='Enter the Prices')
        who = p.scr.sheet_title.split(' · ')[0]
        prices = QUOTE_TYPED.get(who)
        if not prices: raise Stuck(f'enter {who}\'s prices', 'a reply the suite knows how to read', p.scr, 'Enter Prices')
        F = [c for c in p.scr.ctls if not c.action and re.match(r'^l\d', norm(c.label))]
        p.do_ctls([('type', c, prices[k]) for k, c in enumerate(F[:len(prices)])] + [('type', p.scr.find('Freight', field=True), '0')])
        p.tap('Save the Quote', exact=True)
        p.look()
    for _ in range(6):
        c = p.look().find('Confirm', exact=True)
        if not c: break
        p.tap_ctl(c)
        if p.scr.sheet and 'confirm the prices' in norm(p.scr.sheet_title): p.tap('Confirm These Prices', exact=True)
    p.expect(not p.look().find('Confirm', exact=True), 'every quote confirmed', p.scr.excerpt('Not Confirmed', 4))
    lev = p.scr.text[p.scr.text.find('Leveling'):] if 'Leveling' in p.scr.text else ''
    p.expect(bool(re.search(r'over (the )?(line|budget)|above the (line|budget)|\$\d[\d,]* over', lev, re.I)),
             'the leveling warns that the yards\' tile ($21,470 and up) is three times the line ($7,220 sell, $5,510 budget)',
             'it reads "No material budget on this line" and recommends the yards\' tile')


QUOTE_TYPED = {'Atlantic Yard Supply': ['891', '2288', '61']}   # Ray Quint's prose reply, as a person reads it


def j7_coord_pos(p):
    """The coordinator: the award (lumber and drywall on one PO, the tile moved to the tile house at the line's price),
    each PO issued and sent to its vendor; then two buys on the same plumbing line."""
    p.go('Purchasing')
    p.tap('Quotes', exact=True)
    rfq = (re.findall(r'RFQ-\d{4}-\d+', p.look().text) or [''])[0]
    open_rfq(p, rfq)
    if p.scr.find('Award Without Negotiating'): p.tap('Award Without Negotiating', exact=True)
    p.tap('Award and Create POs', exact=True)
    po = (re.findall(r'PO-\d{4}-\d+', p.scr.toast) or [''])[0]
    if not po: raise Stuck('Award and Create POs', 'a toast naming the PO the award made', p.scr, 'Award and Create POs')
    open_po(p, po)
    mv = [c for c in p.scr.ctls if c.kind == 'select' and norm(c.label).startswith('buy this line from someone else')]
    p.expect(len(mv) >= 3, 'each PO line can move to another vendor', f'{len(mv)} move lists')
    tile_po = ''
    if len(mv) >= 3:
        p.pick_ctl(mv[2], 'Nemo Tile')
        tile_po = (re.findall(r'(?:PO-\d{4}-\d+|FM-\d+)', p.scr.toast.split('→')[-1] if '→' in p.scr.toast else '') or [''])[0]
        p.expect(bool(re.match(r'PO-\d{4}-\d+', tile_po)), 'the moved line\'s new order is numbered like every PO (PO-2026-nnn)', f'it is {tile_po or "(no number)"}: ' + p.scr.toast)
    p.look()
    if p.scr.find('Give the Reason', exact=True):
        p.tap('Give the Reason', exact=True, expect='Why')
        p.do([('type', 'Why', f'Three quotes on {rfq}; Gowanus lowest landed. The line budget was set before the yards priced it.'), ('tap', 'Save the Reason')])
    issue_and_send(p, po)
    if tile_po:
        open_po(p, tile_po)
        up = p.scr.find('Unit Price', field=True, nth=1)
        if up: p.do_ctls([('type', up, '14.50')])
        p.look()
        last = BOOK['last_price']
        p.expect(bool(re.search(r'12\.50|last (time|buy|price)|paid .* before', p.scr.text[:p.scr.text.find('Purchase Order ' + tile_po)] if tile_po in p.scr.text else p.scr.text, re.I)),
                 f'the price check on {tile_po} says Nemo Tile charged ${last["unit_price"]:.2f}/sf on {last["po"]} for the same porcelain 12x24 (now $14.50)',
                 (re.findall(r'Price Check[^\n]*\n[^\n]*', p.scr.text) or [''])[0][:200])
        if p.scr.find('Give the Reason', exact=True):
            p.tap('Give the Reason', exact=True)
            if p.look().find('Why', field=True):
                p.do([('type', 'Why', 'Nemo Tile, the tile house, at the line\'s price'), ('tap', 'Save the Reason')])
        issue_and_send(p, tile_po)
    for k, (item, price) in enumerate(PLUMB_BUYS):
        p.go('Purchasing')
        p.tap('Buy Board', exact=True)
        p.pick('Project', JOB['job'])
        p.look()
        c = p.scr.find('Pick 11. Plumbing fixture allowance') or p.scr.find('Pick Plumbing fixture allowance')
        if not c: raise Stuck(f'buy {k + 1} on the plumbing line', 'the plumbing fixture allowance on the Buy Board', p.scr, 'Project')
        p.tap_ctl(c)
        p.tap('Order 1 Line', exact=True, expect='Supplier')
        left = p.scr.find('Unit Price', field=True)
        if k == 1:
            p.expect(left is not None and CY.num(left.value) == 6500 - PLUMB_BUYS[0][1], 'the second buy starts from what is left on the line',
                     f'Unit Price = {left.value if left else "?"}')
        p.do([('pick', 'Supplier', 'Ferguson'), ('type', 'Item', item), ('type', 'Unit Price', str(price)), ('type', 'Needed on Site', '2026-09-14'),
              ('pick', 'Sourcing', 'Distributor or middleman'), ('type', 'Reason', 'Wren chose the pieces at the Ferguson showroom'), ('tap', 'Issue PO')])
        n = (re.findall(r'PO-\d{4}-\d+', p.scr.toast) or [''])[0] if 'issued' in norm(p.scr.toast) else ''
        p.expect(bool(n), f'plumbing buy {k + 1} issued as a PO on the same line', p.scr.toast)
        if n:
            open_po(p, n)
            draft_po_mail(p, n)
            send_drafts(p, n)


PLUMB_BUYS = [('Toilet and vanity faucet (allowance picks)', 1800), ('Shower valve and trim (allowance picks)', 1200)]


def open_po(p, number):
    p.go('Purchasing')
    p.tap('Orders', exact=True)
    if not p.look().row(number, after='Search'):   # the phone keeps the last order open: back to the list
        c = p.scr.find('Purchasing', kinds=('link',))
        if c: p.tap_ctl(c)
        else: p._act('back')
        p.look()
    p.tap_row(number, after='Search', expect=number)


VENDOR_MAIL = {'nemo tile': 'sales@nemotile.example', 'ferguson': 'orders@ferguson.example'}   # from the huddle's list and the vendor's card


def draft_po_mail(p, number):
    p.look()
    if not p.scr.find('Draft Email to Vendor', exact=True): return False
    p.tap('Draft Email to Vendor', exact=True, expect='Email to Vendor')
    to = p.look().find('To', field=True)
    if to is not None and not to.value:
        vend = next((v for v in VENDOR_MAIL if v in norm(p.scr.text)), '')
        p.expect(False, f'{number}\'s vendor email is on file, so its mail is addressed', 'To is empty: "' + (p.scr.toast or 'no email on file') + '"')
        if vend: p.do_ctls([('type', to, f'{vend.title()} <{VENDOR_MAIL[vend]}>')])
    p.tap('Save to Mailbox Drafts', exact=True)
    if p.look().sheet and 'email to vendor' in norm(p.scr.sheet_title):   # the tap after typing was lost (as on the estimate's Save)
        p.expect(False, 'Save to Mailbox Drafts saves on the first tap after typing the To', 'the sheet stayed open')
        p.tap('Save to Mailbox Drafts', exact=True)
    return True


def issue_and_send(p, number):
    p.look()
    lab = next((l for l in ('Issue PO', 'Submit for Approval') if p.scr.find(l, exact=True)), None)
    if lab: p.tap(lab, exact=True)
    if lab == 'Submit for Approval' or 'approv' in norm(p.scr.toast) and 'issued' not in norm(p.scr.toast):
        # over a house threshold: the owner approves it (on the same device), then the coordinator issues it
        why = (re.findall(r'Submit for Approval\]\s*\n([^\n]*)', p.scr.text) or [''])[0][:200]
        me, dev = p.uid, p.device
        switch(p, 'u_owner', dev)
        try:
            p.go('Purchasing', expect_menu=False)
            p.tap('Orders', exact=True)
            p.tap_row(number, after='Search', expect=number)
            c = next((x for x in p.look().ctls if x.action and re.match(r'^approve', norm(x.label))), None)
            if c is None: raise Stuck(f'the owner approves {number}', f'an Approve on {number}', p.scr, 'Orders')
            p.tap_ctl(c)
        finally:
            switch(p, me, dev)
        open_po(p, number)
        if p.look().find('Issue PO', exact=True): p.tap('Issue PO', exact=True)
    p.expect('issued' in norm(p.scr.toast) or p.look().has('Issued'), f'{number} issued', p.scr.toast)
    if draft_po_mail(p, number):
        p.expect(False, f'Issue PO sends {number} to the vendor (it waits for Draft Email to Vendor, a mailbox draft, then Gmail)', 'issued, nothing sent')
    send_drafts(p, number)


def j8_billing_deposit(p):
    """Billing: the Ashbys' 25% deposit, invoiced from the contract and sent."""
    p._act('news')
    p.go('Billing')
    p.expect(p.scr.has('Wren & Julian Ashby') or p.scr.has('214 Lincoln'), 'the signed contract\'s deposit waits in Billing\'s queue (Ready to Bill)',
             p.scr.excerpt('Ready', 6))
    p.go('Clients', expect_menu=False)
    p.tap_row(JOB['client'])
    p.tap('Billing', after=JOB['client'], exact=True)
    p.tap('New Invoice', exact=True)
    p.look()
    con = sum(t['qty'] * t['price'] for t in TAKEOFF); dep = round(con * JOB['deposit_pct'] / 100, 2)
    p.do([('type', 'Title', f"Deposit — {JOB['deposit_pct']}% on signing")])
    p.tap('Add Line', exact=True)
    p.look()
    it, rate = p.scr.find('Item', field=True, exact=True), p.scr.find('Rate', field=True)
    p.do_ctls([('type', it, f"Deposit on signing: {JOB['deposit_pct']}% of the ${con:,.0f} contract"), ('type', rate, str(dep))])
    for _ in range(2):
        if p.look().has('Unsaved changes'): p.tap('Save', exact=True)
    inv = (re.findall(r'INV-\d{4}-\d+', p.scr.text) or [''])[0]
    p.tap('Send to Client', exact=True, expect='Send to Client')
    to = (p.scr.find('To', field=True) or Ctl(0, 'input', '', 0, 0)).value
    subj = (p.scr.find('Subject', field=True) or Ctl(0, 'input', '', 0, 0)).value
    p.tap('Send', exact=True)
    out = 'in your mail app to send' in p.scr.toast
    p.expect(not out, f'Send sends {inv} from the app (the toast: "in your mail app to send")', p.scr.toast)
    if out: p.mail('send', to or JOB['emails'][0], subj or f'{inv} deposit', f'Attached is invoice {inv} for ${dep:,.2f}, the deposit on signing. Billing')



# ---------------------------------------------------------------------------------------------------- the registry
# id, who, title, the function, the world before it (its slots; 'next' moves to the next working day), and the
# referee's steps (sim/cycle.py) it must leave right. Adding a journey: a function above and a row here.
JOURNEYS = [
    ('J1', 'u_owner', 'The inquiry to the project', 'j1_owner_sales', ['morning'], ['C01', 'C02', 'C03']),
    ('J1b', 'u_owner', 'A proposal started at won, tied to its job', 'j1b_owner_proposal_first', [], [probe_tied]),
    ('J2', 'u_alan', 'The estimate from the takeoff', 'j2_pm_estimate', ['work1'], ['C04', 'C05']),
    ('J3', 'u_alan', 'The estimate sent', 'j3_pm_send', ['work2'], ['C06']),
    ('J4', 'u_owner', 'Signed; the contract and the SOV', 'j4_owner_signed', ['eod'], ['C07', 'C08']),
    ('J5', 'u_chen', 'One RFQ from three estimate lines', 'j5_coord_rfq', ['next', 'morning', 'work1'], ['C10', 'C11']),
    ('J6', 'u_chen', 'The quotes and the award', 'j6_coord_quotes', ['work2'], ['C13']),
    ('J7', 'u_chen', 'POs from the lines, sent', 'j7_coord_pos', [], ['C12', 'C14']),
    ('J8', 'u_billing', 'The deposit invoice', 'j8_billing_deposit', ['eod'], ['C30']),
]


def world_before(w, steps, slot):
    for s in steps:
        if s == 'next': w.admin('advance'); slot = 'morning'; continue
        w.admin('world', slot=s, watchers=True); slot = s
    return slot


def run_journey(w, J, device, slot, log=None):
    jid, uid, title, fn, _, steps = J
    p = Person(w, uid, device, jid, log); p.slot = slot; p.jdev = device
    t0 = time.time(); stuck = None
    w.admin('begin_turn', uid=uid, slot=slot, cap=9999, device=device)
    try:
        p.look()
        globals()[fn](p)
    except Stuck as e:
        sc = e.screen
        stuck = {'journey': jid, 'device': device, 'step': e.what, 'screen': (sc.title or sc.head[:80]) if sc else '',
                 'control': e.control or '', 'expected': e.expected, 'got': (sc.excerpt(n=12) if sc else '')[:1200],
                 'screen_text': sc.text if sc else ''}
    except NotImplementedError:
        stuck = {'journey': jid, 'device': device, 'step': 'not written yet', 'screen': '', 'control': '', 'expected': 'the journey', 'got': ''}
    finally:
        w.admin('end_turn')
    secs = round(time.time() - t0, 1)
    cy = w.cycle()
    grades = [dict(zip(('status', 'detail'), cy.step(sid)[:2]), step=sid) if isinstance(sid, str) else
              dict(zip(('status', 'detail'), sid(w)), step=sid.__name__) for sid in steps]
    return {'journey': jid, 'title': title, 'uid': uid, 'device': device, 'taps': p.taps, 'calls': p.calls, 'seconds': secs,
            'budget': TAP_BUDGET[jid], 'stuck': stuck, 'soft': p.soft, 'grades': grades, 'trail': p.trail[-60:]}


def failures_of(r):
    F = []
    if r['stuck']: F.append(dict(r['stuck'], kind='stuck'))
    F += [dict(s, kind='expect') for s in r['soft']]
    for g in r['grades']:
        if g['status'] != 'right':
            F.append({'kind': 'record', 'journey': r['journey'], 'device': r['device'], 'step': g['step'], 'expected': f"{g['step']} right in the records",
                      'got': f"{g['status']}: {g['detail']}", 'screen': (r['stuck'] or {}).get('screen', ''), 'control': (r['stuck'] or {}).get('control', '')})
    if r['taps'] > r['budget'] and not r['stuck']:
        F.append({'kind': 'taps', 'journey': r['journey'], 'device': r['device'], 'step': 'tap budget', 'expected': f"at most {r['budget']} taps",
                  'got': f"{r['taps']} taps", 'screen': '', 'control': ''})
    return F


# ---------------------------------------------------------------------------------------------------- dangerous buttons
# The class from Pilot 3 day 1: a button that commits what has not been reviewed or has not happened. For each record
# in a held, paid, posted or draft state (read raw from the records), the blue button and the first button on its row,
# card or page must be a safe next step for that state.
UNSAFE = {
    ('bill', 'held'): r'^(approve|approve .*|pay|pay now|pay .*|schedule payment|release|mark paid|recommend)$',
    ('bill', 'paid'): r'^(approve|approve .*|pay|pay now|pay .*|schedule payment|release|mark paid|recommend)$',
    ('bill', 'paid before approval'): r'^(approve|approve .*|pay|pay now|schedule payment|release|mark paid)$',
    ('estimate', 'draft'): r'^(mark sent|mark approved|record client approval|record approval|convert.*|approve)$',
    ('invoice', 'draft'): r'^(mark sent|record payment|mark paid|apply payment)$',
    ('invoice', 'paid'): r'^(record payment|mark sent|send reminder|follow up|chase)$',
    ('po', 'draft'): r'^(mark sent|mark received|receive|record delivery|close)$',
    ('po', 'closed'): r'^(send|send to vendor|issue|approve|receive)$',
    ('obligation', 'not filed'): r'^(mark filed|record the filing|mark renewed|record the renewal)$',
}
DRAFTY = r'^(draft the|draft a|prepare|renew|start the|request)'
RECORDY = r'^(record|mark)\b|filed on|paid on|sent on'
ROLE_OF = {'pm': 'pm', 'alan': 'pm', 'owner': 'owner', 'chen': 'coord', 'billing': 'billing', 'controller': 'controller', 'angel': 'foreman'}


def danger_records(db):
    """every bill, estimate, invoice, PO and obligation in a state where a wrong tap commits money or the firm"""
    R = []
    for b in db.get('bills') or []:
        st = str(b.get('status') or '')
        paid_by_card = any(abs(abs(CY.num(t.get('amt'))) - CY.bill_total(b)) < 0.01 and CY.num(t.get('amt')) < 0 and str(t.get('date') or '') >= str(b.get('date') or '')
                           and norm(b.get('vendor')).split(' ')[0] in norm(t.get('desc') + ' ' + str(t.get('vendor') or ''))
                           for t in db.get('txns') or [])
        if st in ('hold', 'on-hold', 'held', 'disputed') or b.get('hold') or (b.get('onHold') or {}).get('state') == 'open' or (b.get('short') or {}).get('held'): k = 'held'
        elif st == 'paid' or b.get('paidAt'): k = 'paid'
        elif paid_by_card and st not in ('approved', 'verified'): k = 'paid before approval'
        else: k = None
        if k: R.append(('bill', k, b.get('number') or '', b))
    for c in db.get('clients') or []:
        for e in c.get('estimates') or []:
            if e.get('status') == 'draft' and e.get('number'): R.append(('estimate', 'draft', e['number'], e))
        for i in c.get('invoices') or []:
            st = str(i.get('status') or '')
            paid = sum(CY.num(p.get('amount')) for p in c.get('payments') or [] if p.get('invoiceId') == i.get('id'))
            if st == 'draft' and i.get('number'): R.append(('invoice', 'draft', i['number'], i))
            elif i.get('number') and (st == 'paid' or (paid and paid >= CY.doc_total(i) - 0.01)): R.append(('invoice', 'paid', i['number'], i))
    for po in db.get('pos') or []:
        st = str(po.get('status') or '')
        if st in ('draft', 'purchasing') and po.get('number'): R.append(('po', 'draft', po['number'], po))
        elif st in ('closed', 'received', 'billed') and po.get('number'): R.append(('po', 'closed', po['number'], po))
    for o in db.get('obligations') or []:
        if o.get('kind') == 'filing' and o.get('status') == 'active': R.append(('obligation', 'not filed', o.get('name') or '', o))
    return [r for r in R if r[2]]


def mentions(sc, needle):
    """where a record is itself on the screen (its link, its row, its page heading), not a passing mention in another
    record's text ("$3,800 over PO-2026-044" on a bill's card)"""
    rx = re.compile(r'\[\d+(?: link| tab)?\]? ?(?:[^\[\]\n]{0,40}?)' + re.escape(needle) + r'|^' + re.escape(needle) + r'|›' + re.escape(needle) +
                    r'|(?:Purchase Order|Estimate|Invoice|Bill)(?: #)? ' + re.escape(needle), re.M)
    return [m.start() if m.group(0).startswith('[') else m.end() - len(needle) for m in rx.finditer(sc.text)]


def region_actions(sc, needle, page=False):
    """the controls on a record's row, card or page: from where it shows to where the next record starts (its page:
    from its heading to the end)"""
    M = mentions(sc, needle)
    if not M: return None
    i = M[0]
    own = lambda c: needle in c.label or re.match(r'^(close|ask|cancel|back|more|open|×)$', norm(c.label))   # its own row or link, and the sheet's frame
    if page:   # its page: the whole sheet it opened in, or the page from its heading on
        top = sc.text.find('== Open on top ==') if sc.sheet else -1
        end = sc.text.find('== Behind it:') if sc.sheet else len(sc.text)
        lo = top if top >= 0 and top <= i else i
        return [c for c in sc.ctls if lo <= c.pos < (end if end > lo else len(sc.text)) and c.action and c.kind == 'button' and not c.disabled and not own(c)]
    nxt = [m.start() for m in re.finditer(r'\[\d+(?: link)?\]? ?(?:[A-Za-z &]{0,30})?\b(EST|INV|PO|RFQ|CO)-\d{4}-[\w-]+|\[\d+(?: link)?\] ?[A-Z]{2,4}-\d{2,4}-\d+\b', sc.text[i + len(needle):])]
    end = min(i + len(needle) + (nxt[0] if nxt else 1500), i + 1500)
    return [c for c in sc.ctls if i <= c.pos < end and c.action and c.kind == 'button' and not c.disabled and not own(c)]


WHO = r'(PM|Owner|owner|Alan|Chen|Billing|Controller|Angel)'
STAMP_RX = re.compile(r'(?:(?<![\w-])' + WHO + r' (recommended|approved|verified|ok)\b|(recommended|approved|verified|reviewed|signed off)(?: for payment)? by (?:the )?' + WHO + r'\b)')
NOT_A_STAMP = re.compile(r'(to be|needs?|must|until|waits?|waiting|awaits?|before|for|goes to|asks?|if)\s+(?:\w+\s+){0,2}$', re.I)


def stamp_findings(sc, rec, db, where, page=False):
    """a "recommended / approved by <person>" shown on a record needs that person's own action in the audit trail"""
    out = []
    M = mentions(sc, rec[2])
    if not M: return out
    seg = sc.text[M[0]:] if page else sc.text[M[0]: M[0] + 900]
    for m in STAMP_RX.finditer(seg):
        if NOT_A_STAMP.search(seg[max(0, m.start() - 30): m.start()]): continue
        who = (m.group(1) or m.group(4) or '').lower()
        role = ROLE_OF.get(who, who)
        A = [a for a in db.get('audit') or [] if a.get('refId') == rec[3].get('id') and (a.get('role') == role or norm(a.get('by')) == who)
             and re.search(r'recommend|approv|pmok|verif|review', str(a.get('action')), re.I)]
        if not A:
            out.append({'kind': 'stamp', 'journey': 'danger', 'device': where[1], 'step': f'{rec[0]} {rec[2]} ({rec[1]}) on {where[0]}',
                        'expected': f'"{m.group(0)}" backed by {who}\'s own action in the audit trail',
                        'got': f'no audit entry by {role or who} on {rec[2]}' + (' (only a line in the record\'s own approvals list, with no audit entry behind it)'
                                                                               if any(a.get('role') == role for a in rec[3].get('approvals') or []) else ''),
                        'screen': sc.title, 'control': ''})
    return out


def drafty_checks(p, sc, rec, where, page=False, only=None):
    """every draft-like button on the record (Draft the Renewal, Prepare, Request ...) must open a draft, not a sheet
    that records the thing as done, with today's date already in its Filed / Paid / Sent On"""
    F = []
    for d in (only or [x for x in (region_actions(sc, rec[2], page) or []) if re.match(DRAFTY, norm(x.label))][:2]):
        p.last_control = d.label
        n0 = sc.text.count('== Open on top ==')
        p._act('tap', d.n)
        s2 = p.look()
        if s2.text.count('== Open on top ==') > n0:   # a sheet of its own opened: read that one
            last = s2.text.rsplit('== Open on top ==', 1)[1]; off = len(s2.text) - len(last)
            title = next((b for b in (re.sub(r'\[\d+[^\]]*\]', '', l).strip() for l in last.split('\n')) if b), '')
            mine = [x for x in s2.ctls if x.pos >= off]
            today = (p.w.world_state().get('day') or '')
            filled = [x for x in mine if x.kind == 'date' and x.value and x.value == today and re.search(r'filed|paid|sent|done|completed|renewed|on$', norm(x.label))]
            subm = [c.label for c in mine if c.action and re.match(r'^(record|mark)\b', norm(c.label))]
            s2.sheet_title = title
            if re.search(RECORDY, norm(title)) or filled or subm:
                F.append({'kind': 'prefilled', 'journey': 'danger', 'device': where[1], 'step': f'{rec[0]} {rec[2]} on {where[0]}: "{d.label}"',
                          'expected': f'"{d.label}" opens a draft, not a sheet recording it as done',
                          'got': f'it opens "{s2.sheet_title}"' + (f', {", ".join(x.label for x in filled)} = {today} already filled' if filled else '') +
                                 (f', its button "{subm[0]}"' if subm else ''),
                          'screen': s2.title, 'control': d.label})
            p._act('back')
        sc = p.look(marks=True)
    return F


def button_findings(sc, rec, where, ctx, page=False):
    acts = region_actions(sc, rec[2], page)
    if not acts: return []
    rx = UNSAFE.get((rec[0], rec[1]))
    out = []
    first, blue = acts[0], [c for c in acts if c.blue]
    for c, why in [(first, 'the first button')] + [(b, 'the blue button') for b in blue]:
        if rx and re.match(rx, norm(c.label)):
            out.append({'kind': 'danger', 'journey': 'danger', 'device': where[1], 'step': f'{rec[0]} {rec[2]} ({rec[1]}) on {where[0]} ({ctx})',
                        'expected': f'{why} is a safe next step for a {rec[1]} {rec[0]}', 'got': f'{why} is "{c.label}"' + (' (blue)' if c.blue else ''),
                        'screen': sc.title, 'control': c.label})
    return out


# where each role looks for these records: menu label, then the tabs under it (as each role's menu holds them)
DANGER_SCREENS = {
    'u_owner': [('Today',), ('Accounting', 'Bills & Payroll'), ('Sales', 'Estimates'), ('Company', 'Obligations'), ('Purchasing', 'Orders')],
    'u_alan': [('Today',), ('Projects', 'Estimates'), ('Projects', 'Billing'), ('Purchasing', 'Orders')],
    'u_chen': [('Today',), ('Purchasing', 'Orders')],
    'u_billing': [('Today',), ('Billing', 'Estimates'), ('Billing', 'Invoices'), ('Billing',)],
}
HOLD = ('WW-2026-118', 'Paid on the Amex before approval and $3,800 over PO-2026-044; COI expired', 'Chen Biron')


def hold_bill(p, number, why, who):
    """the owner puts the bill on hold through its own Hold (Pilot 3 day 1: "the tap I fear most" came after this)"""
    p.go('Accounting', expect_menu=False)
    p.tap('Bills & Payroll', exact=True)
    c = p.scr.find('Review', after=number, exact=True) or p.scr.next_action(number)
    if not c: return False
    p.tap_ctl(c)
    if not p.scr.find('Hold', exact=True): return False
    p.tap('Hold', exact=True)
    if not p.look().has('Hold the Bill'):
        p.tap('Hold', exact=True)
    p.expect(p.look().has('Hold the Bill'), 'Hold opens its sheet on the first tap', 'the Hold sheet appeared only after another tap')
    p.do([('type', 'Reason', why), ('pick', 'Task For', who), ('tap', 'Hold the Bill')])
    p._act('back')
    return True


def danger_walk(w, devices, screens=None, hold=True, slot='work2'):
    F, seen = [], set()
    w.admin('begin_turn', uid='u_owner', slot=slot, cap=99999, device='desktop')
    try:
        if not hold: raise StopIteration
        p0 = Person(w, 'u_owner', 'desktop', 'danger', None); p0.slot = 'work2'; p0.look()
        held = any(b.get('number') == HOLD[0] and (b.get('onHold') or {}).get('state') == 'open' for b in w.db().get('bills') or [])
        if not held and not hold_bill(p0, *HOLD): F.append({'kind': 'stuck', 'journey': 'danger', 'device': 'desktop', 'step': f'hold {HOLD[0]}', 'expected': 'Hold on the bill',
                                              'got': '', 'screen': p0.scr.title, 'control': p0.last_control})
        F += [dict(x, kind='expect') for x in p0.soft]
    except StopIteration:
        pass
    except Stuck as e:
        F.append({'kind': 'stuck', 'journey': 'danger', 'device': 'desktop', 'step': e.what, 'expected': e.expected, 'got': '', 'screen': e.screen.title if e.screen else '', 'control': e.control})
    finally:
        w.admin('end_turn')
    db = w.db()
    R = danger_records(db)
    for uid in DANGER_ROLES:
        for dev in devices:
            p = Person(w, uid, dev, 'danger', None); p.slot = slot
            w.admin('begin_turn', uid=uid, slot=slot, cap=99999, device=dev)
            try:
                p.look()
                for path in (screens or DANGER_SCREENS).get(uid, []):
                    try:
                        sc = open_path(p, path)
                    except Stuck:
                        continue
                    sc = p.look(marks=True)
                    # a draft-like button anywhere on the screen (a Today card names its record in its own words)
                    for d in [c for c in sc.actions() if c.kind == 'button' and re.match(DRAFTY, norm(c.label))][:4]:
                        near = [c for c in sc.ctls if c.kind == 'link' and d.pos - 600 < c.pos < d.pos]
                        ctx = (near[-1].label if near else norm(sc.text[max(0, d.pos - 120): d.pos]))[:80]
                        if (uid, dev, d.label, ctx) in seen: continue
                        seen.add((uid, dev, d.label, ctx))
                        F += drafty_checks(p, sc, ('card', 'not done', d.label, {}), (f'{uid} {" > ".join(path)}: {ctx}', dev), only=[d])
                        sc = open_path(p, path); sc = p.look(marks=True)
                    for rec in R:
                        if rec[2] not in sc.text: continue
                        where = (f'{uid} {" > ".join(path)}', dev)
                        if not mentions(sc, rec[2]): continue
                        F += button_findings(sc, rec, where, 'list')
                        F += stamp_findings(sc, rec, db, where)
                        if rec[0] == 'obligation': F += drafty_checks(p, sc, rec, where); sc = p.look(marks=True)
                        key = (uid, dev, rec[2])
                        if key in seen: continue
                        seen.add(key)
                        F += open_record_checks(p, rec, path, where, db)
                        sc = open_path(p, path); sc = p.look(marks=True)
            finally:
                w.admin('end_turn')
    uniq, out = set(), []
    for f in F:
        k = (f['step'], f['expected'], f['got'])
        if k not in uniq: uniq.add(k); out.append(f)
    return out


def open_path(p, path):
    p.go(path[0], expect_menu=False)
    for t in path[1:]: p.tap(t, exact=True)
    return p.scr


def open_record_checks(p, rec, path, where, db):
    """the record's own page: its buttons for its state, any stamp, and its draft-like buttons"""
    F = []
    M = mentions(p.scr, rec[2])
    c = (next((x for x in p.scr.ctls if x.action and rec[2] in x.label and abs(x.pos - M[0]) < 80), None) or
         next((x for x in p.scr.ctls if x.action and x.pos <= M[0] + 2 and M[0] - x.pos < 60), None)) if M else None
    if c is None: return F
    p.last_control = c.label
    r, txt = p._act('tap', c.n)
    sc = p.look(marks=True)
    if not mentions(sc, rec[2]): p._act('back'); return F
    where = (where[0] + f' > {rec[2]}', where[1])
    F += button_findings(sc, rec, where, 'its page', page=True)
    F += stamp_findings(sc, rec, db, where, page=True)
    F += drafty_checks(p, sc, rec, where, page=True)
    p._act('back')
    return F


# ---------------------------------------------------------------------------------------------------- the report
def fmt_fail(f):
    s = f"- **{f['journey']} {f['device']}** ({f['kind']}) {f['step']}: expected {f['expected']}"
    if f.get('screen'): s += f"; screen: {f['screen']}"
    if f.get('control'): s += f"; last control: {f['control']}"
    if f.get('got'): s += '\n  - got: ' + str(f['got']).replace('\n', ' / ')[:500]
    return s


def write_report(results, danger, t_all, build):
    os.makedirs(OUT, exist_ok=True)
    F = [f for r in results for f in failures_of(r)] + danger
    json.dump({'build': build, 'seconds': t_all, 'results': results, 'danger': danger, 'failures': F}, open(os.path.join(OUT, 'report.json'), 'w'), indent=1)
    M = [f'# Cycle walk: {len(F)} failures', '', f'Build {build}. Run time {t_all / 60:.1f} minutes.', '',
         '| Journey | Who | Device | Taps | Budget | Wall time | Stuck at | Steps |', '|---|---|---|---|---|---|---|---|']
    for r in results:
        st = r['stuck']
        M.append(f"| {r['journey']} {r['title']} | {r['uid']} | {r['device']} | {r['taps']} | {r['budget']} | {r['seconds']:.0f}s | "
                 f"{(st['step'][:60] if st else '')} | {', '.join(g['step'] + ' ' + g['status'] for g in r['grades'])} |")
    M += ['', '## Failures', ''] + [fmt_fail(f) for f in F]
    M += ['', '## Trails (the last actions of each journey)', '']
    for r in results:
        M += [f"### {r['journey']} {r['device']}", '```'] + r['trail'] + ['```']
    open(os.path.join(OUT, 'report.md'), 'w').write('\n'.join(M) + '\n')
    return F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='', help='journeys to run, e.g. J2 or J1,J2 (the chain before them runs on the desktop)')
    ap.add_argument('--devices', default='desktop,phone')
    ap.add_argument('--no-danger', action='store_true')
    ap.add_argument('--attach', default='', help='a running world (development: no world steps, no checkpoints)')
    ap.add_argument('--danger-only', action='store_true', help='with --attach: only the dangerous-button walk')
    ap.add_argument('--keep', action='store_true', help='leave the worlds\' folders in sim/runs')
    a = ap.parse_args()
    bad = lint_self()
    if bad:
        print('LINT: this suite reaches past the screens:\n  ' + '\n  '.join(bad)); print('CYCLE WALK 0 checks · 1 failed'); return 1
    t_all = time.time()
    dist_src = os.environ.get('SD_DIST') or os.path.join(ROOT, 'dist', 'smartdesigns_projects.html')
    if not os.path.exists(dist_src): raise SystemExit('build first: python3 build.py')
    stamp = time.strftime('%m%d_%H%M%S')
    os.makedirs(RUNS, exist_ok=True)
    pinned = os.path.join(RUNS, f'cw_{stamp}.build.html'); shutil.copy(dist_src, pinned)   # one build for every world of this run
    build = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    devices = [d for d in a.devices.split(',') if d in DEVICES]
    only = [x.strip() for x in a.only.split(',') if x.strip()]
    last = max((i for i, J in enumerate(JOURNEYS) if J[0] in only), default=len(JOURNEYS) - 1)
    results, worlds = [], []
    if a.attach and a.danger_only:
        w = World(a.attach, pinned, attach=True)
        danger = danger_walk(w, devices)
        F = write_report([], danger, round(time.time() - t_all), build)
        os.remove(pinned)
        for f in F: print('FAIL', fmt_fail(f)[2:].split('\n')[0][:400])
        print(f"CYCLE WALK {len(danger)} danger findings"); return 1 if F else 0
    if a.attach:
        w = World(a.attach, pinned, attach=True); slot = w.world_state().get('slot') or 'morning'
        for J in JOURNEYS[:last + 1]:
            if only and J[0] not in only: continue
            for dev in devices:
                r = run_journey(w, J, dev, slot); results.append(r); print(json.dumps({k: r[k] for k in ('journey', 'device', 'taps', 'seconds', 'stuck', 'soft', 'grades')}, indent=1)[:3000], flush=True)
        F = write_report(results, [], round(time.time() - t_all), build)
        os.remove(pinned)
        print(f"CYCLE WALK {sum(len(r['grades']) + 1 for r in results)} checks · {len(F)} failed"); return 1 if F else 0
    desk = World(f'cw_{stamp}_desktop', pinned).start(); worlds.append(desk)
    print(f'world {desk.run} up in {desk.boot_s}s', flush=True)
    desk.admin('cycle', on=True)
    slot, checkpoints = 'morning', {}
    danger = []
    try:
        if not a.no_danger:   # the morning's Today, before anyone has worked it (Pilot 3 met Draft the Renewal here at 7:30)
            desk.admin('world', slot='morning', watchers=True)
            danger += danger_walk(desk, devices, screens={u: [('Today',)] for u in DANGER_ROLES}, hold=False, slot='morning')
        for J in JOURNEYS[:last + 1]:
            slot = world_before(desk, J[4], slot)
            checkpoints[J[0]] = (desk.checkpoint(J[0]), slot)
            if 'desktop' in devices and (not only or J[0] in only):
                r = run_journey(desk, J, 'desktop', slot); results.append(r)
                print(f"{J[0]} desktop: {r['taps']} taps, {r['seconds']}s, " + ('STUCK ' + r['stuck']['step'] if r['stuck'] else 'through') + ' · ' +
                      ', '.join(g['step'] + ' ' + g['status'] for g in r['grades']), flush=True)
            elif only and J[0] not in only:
                r = run_journey(desk, J, 'desktop', slot)   # the chain before the journey asked for, on the desktop, not reported
        if not a.no_danger: danger += danger_walk(desk, devices)
    finally:
        desk.stop()
    if 'phone' in devices:
        for J in JOURNEYS[:last + 1]:
            if only and J[0] not in only: continue
            ck, slot = checkpoints[J[0]]
            ph = World(f'cw_{stamp}_phone_{J[0]}', pinned, resume_from=ck).start(); worlds.append(ph)
            try:
                r = run_journey(ph, J, 'phone', slot); results.append(r)
                print(f"{J[0]} phone: {r['taps']} taps, {r['seconds']}s, " + ('STUCK ' + r['stuck']['step'] if r['stuck'] else 'through') + ' · ' +
                      ', '.join(g['step'] + ' ' + g['status'] for g in r['grades']), flush=True)
            finally:
                ph.stop()
    results.sort(key=lambda r: (r['journey'], r['device']))
    F = write_report(results, danger, round(time.time() - t_all), build)
    for f in F: print('FAIL', fmt_fail(f)[2:].split('\n')[0][:300])
    if not a.keep:
        for x in worlds:
            shutil.rmtree(x.dir, ignore_errors=True); shutil.rmtree(x.dir + '.ck', ignore_errors=True)
            try: os.remove(os.path.join(RUNS, f'{x.run}.server.log'))
            except Exception: pass
        try: os.remove(pinned)
        except Exception: pass
    n = sum(len(r['grades']) + 2 for r in results) + len(danger)
    print(f'report: {os.path.join(OUT, "report.md")}')
    print(f"CYCLE WALK {n} checks · {len(F)} failed ({round((time.time() - t_all) / 60, 1)} minutes)")
    return 1 if F else 0


if __name__ == '__main__':
    sys.exit(main())
