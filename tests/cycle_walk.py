#!/usr/bin/env python3
"""tests/cycle_walk.py: the ten core journeys of docs/JOURNEYS.md, done the way a person does them (Alan, 2026-10-26).

"All these checks pass and then as soon as we do actual work, we fail almost immediately." The net drives the app by
calling its functions on seeded data; this suite drives it only through the screens, with the agent harness's own verbs
(sim/server.py /act: go by menu label, tap by label, type into a labelled field, pick a visible option, do batches, the
person's own mailbox), on a NEW client and job (the Ashbys, 214 Lincoln Place, sim/cycle_book.json), with no AI and no
randomness of its own. Progress is N of 10 journeys passing per device (docs/PROCESS.md rule 10); this is the number.

  J1  owner        win the inquiry: the mail > a lead > the walk-through noted > won > one client > the project
  J2  pm           price the job: the 12-line estimate from the takeoff on the project, the margin read, sent to the
                   client's mail and portal (the Ashbys then sign it, by world rules)
  J3  pm           price a change: the foreman's field issue (photo, note) > a change order with cost, margin and days,
                   sent within 48 hours, the client's approval recorded with who and when
  J4  pm           review the job (Friday): schedule, costs per estimate line, change orders, decisions, submittals;
                   the client update naming the lines over budget
  J5  coord        get three quotes: one RFQ from three estimate lines to three yards, the foreman's check, the quotes
                   recorded from the replies (one in prose), levelled, awarded
  J6  coord        buy it: the award's PO issued and sent, the tile moved to the tile house and checked against the last
                   price, two buys on the same plumbing line, the stock checked before buying the electrical rough-in
  J7  coord        receive and match: the trucks (6 cement boards short, 31 sf of tile cracked) received with what came,
                   the bills matched three ways and held at what arrived, the claim, the vendor's credit memo
  J8  billing      bill the deposit: the signed copy recorded and the contract made (the owner), the 25% deposit invoice,
                   sent; the next morning the Ashbys' transfer is matched to its bank line, not typed
  J9  billing      bill the progress: the progress invoice from the SOV with retainage, the approved change order and the
                   pendants bought for the client, sent, the chase set
  J10 controller   know the week's money: the week's bank and card lines matched, the payroll built and approved by the
                   owner on his phone, cash, AR and job cost per estimate line read off the books and graded
  X1  owner        (an extra, not one of the ten) a proposal started at won: is it tied to its job?

The chain runs in the book's days (Thu 9/3, Fri 9/4, Tue 9/8): J1, X1, J2 and J8 on Thursday (J8 ends Friday morning at
the bank), J5, J6 and J4 on Friday, J3, J7, J9 and J10 on Tuesday. The world (sim/world.py, sim/script_p3.js) plays the
outside: the inquiry, the client's answers and signature, the vendors' quotes and bills, the foreman's field issue and
field day, the trucks (told to the coordinator: she receives them), the bank feed and the credit memo. The coordinator
receives and the controller sits in this walk (`cycle on --play u_controller,u_angel:receive --feed`), so nothing a journey
owns is scripted for it.

Every journey runs twice: on the desktop (1440) and on the phone (390). The desktop chain runs first and keeps a
checkpoint of the company before each journey (`--keep` leaves them under sim/runs/<run>.ck/<J>); each phone journey starts
from that checkpoint in its own world, so a phone failure upstream never hides a phone failure downstream. Per journey and
device it records the taps (every tap, type, pick, go, back and key, each step of a `do` counted, every person in it) and
the modelled person-minutes (sim/server.py MINUTES), holding the taps to JOURNEYS.md's budget (BUDGET); the minutes are
printed beside their budget as "modelled" and do not gate until calibrated against real recorded sessions. After each
journey the records are read raw (db.json, the harness's snapshot) and graded with sim/cycle.py's own step checks (the
"done when"). A journey passes on a device only with no stop, no failed expectation, every record check right and the tap
budget kept; the report names the step each journey stops at.

Then the dangerous-button class (Pilot 3 day 1): for every bill, estimate, invoice, PO and obligation in a held, paid,
posted or draft state, on the owner's, the PM's, the coordinator's and billing's screens, phone and desktop:
  - the blue button and the first button are a safe next step for that state (no Approve on a held or paid bill, no
    Mark Sent first under a draft nobody has reviewed, no Record Payment on a draft invoice ...);
  - no sheet opens prefilled to record something that has not happened (Draft the Renewal opening Record the Filing
    with today's date in Filed On);
  - no "recommended / approved by <person>" stamp without that person's own action in the audit trail.

    python3 tests/cycle_walk.py                 everything (about an hour on this machine; run it through tests/slot.sh)
    python3 tests/cycle_walk.py --only J2       one journey (the chain up to it runs on the desktop first)
    python3 tests/cycle_walk.py --devices desktop --no-danger
    python3 tests/cycle_walk.py --from <run>:J7 --only J7   start from a kept checkpoint (development: no chain before it)
    python3 tests/cycle_walk.py --attach <run>  drive a world already running (development)
    python3 tests/cycle_walk.py --selftest      the walk's own units (no browser): the lint, the reader, the budgets and
                                                journeys against docs/JOURNEYS.md, the pass rule

Writes review/cycle_walk/report.md and report.json; the last two lines are `JOURNEYS desktop N of 10 · phone M of 10` and
`CYCLE WALK N checks · F failed`; exit 1 on any failure. docs/CYCLE_WALK.md says how to add a journey.
"""
import argparse, ast, json, os, re, shutil, signal, subprocess, sys, time, urllib.request

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
VERBS_OK = {'screen', 'find', 'tap', 'type', 'pick', 'do', 'go', 'back', 'key', 'scroll', 'mail', 'news', 'call', 'device', 'upload', 'photo'}


def lint_self():
    src = open(os.path.abspath(__file__), encoding='utf-8').read().split('\n')
    bad = []
    for i, line in enumerate(src, 1):
        code = line.split('#')[0] if not line.lstrip().startswith(('"', "'")) else line
        for rx, why in FORBIDDEN:
            if re.search(rx, code): bad.append(f'line {i}: {why}: {line.strip()[:100]}')
    return bad


# ---------------------------------------------------------------------------------------------------- the budgets
# docs/JOURNEYS.md's "Budget (taps / minutes)" for each journey, on the devices it names (`--selftest` reads the table and
# fails if these drift from it). Taps are counted the way the harness counts a person's actions: every tap, type, pick, go,
# back and key, each step of a `do`, every person in the journey (a hand-off's taps count too). Minutes are the person's
# working minutes as the harness models them (sim/server.py MINUTES per action), summed over every turn of the journey:
# reported beside the budget, never gating, until calibrated against real recorded sessions. JOURNEYS.md names a budget
# for one device on most journeys; the other device is held to the same one (shown as "(the phone's)" in the report).
BUDGET = {
    'J1': {'phone': (15, 6)},
    'J2': {'phone': (60, 20), 'desktop': (40, 15)},
    'J3': {'phone': (20, 8)},
    'J4': {'desktop': (25, 15)},
    'J5': {'desktop': (30, 20), 'phone': (30, 20)},
    'J6': {'phone': (25, 10)},
    'J7': {'phone': (15, 8)},
    'J8': {'desktop': (12, 6)},
    'J9': {'desktop': (25, 15)},
    'J10': {'desktop': (30, 20)},
    'X1': {'desktop': (40, 20)},   # the extra (not in JOURNEYS.md): twice the ~20 taps of the proposal path
}
DEVICES = ('desktop', 'phone')
# a person's minutes per action: sim/server.py's own table (Pilot 3 charges a person by it), read from its source
_SV = open(os.path.join(SIM, 'server.py'), encoding='utf-8').read()
MINUTES = ast.literal_eval(re.search(r'^MINUTES = (\{.*?\})\n', _SV, re.M | re.S).group(1))
MAIL_MINUTES = ast.literal_eval(re.search(r'^MAIL_MINUTES = (\{.*?\})\n', _SV, re.M | re.S).group(1))


def budget_for(jid, device):
    """(taps, minutes, the device the budget is JOURNEYS.md's for)"""
    B = BUDGET[jid]
    dev = device if device in B else next(iter(B))
    return B[dev][0], B[dev][1], dev
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
        env = dict(os.environ, SIM_DIST=self.dist, SIM_RUN=self.run, SIM_PICTURES='0')   # the walk reads text; no screen pictures
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
        seed = os.path.join(self.dir, 'seed_txns.json')   # the company it starts from (kept with every checkpoint)
        if not os.path.exists(seed):
            try: json.dump([t.get('id') for t in self.db().get('txns') or []], open(seed, 'w'))
            except Exception: pass
        return self

    def seed_txns(self):
        p = os.path.join(self.dir, 'seed_txns.json')
        return json.load(open(p)) if os.path.exists(p) else []

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

    def actions(self):
        """the run's action log (where each person was: the Friday review's pages are graded from it)"""
        p = os.path.join(self.dir, 'actions.jsonl')
        out = []
        if os.path.exists(p):
            for l in open(p, encoding='utf-8'):
                try: out.append(json.loads(l))
                except ValueError: pass
        return out

    def cycle(self):
        st = self.world_state(); W = st.get('world') or {}
        return CY.Cycle(self.db(), CY.load_book(), {'gated': W.get('gated', {}), 'calls': st.get('calls', []), 'interrupts_done': W.get('interrupts_done', {}), 'seed_txns': self.seed_txns()},
                        self.actions(), st.get('day'))

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
        end = min([i for i in (self.text.find('== Behind it:'), self.text.find('== Under it, still usable:')) if i >= 0] or [len(self.text)]) \
            if region == 'sheet' and self.sheet else len(self.text)
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
            if l.startswith('== Toast =='): break   # a toast names the record but is not its row (tapping it opens nothing)
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
    TAPS = {'tap', 'type', 'pick', 'go', 'back', 'key', 'upload', 'photo'}

    def __init__(self, world, uid, device, journey, log):
        self.w, self.uid, self.device, self.j, self.log = world, uid, device, journey, log
        self._taps, self.calls, self.scr, self.last_control, self.trail = 0, 0, Screen(''), '', []
        self.soft = []   # expectations that failed while the person could still go on
        self.by, self.minutes, self.answers, self.notes = {}, 0.0, {}, []   # taps per person; the journey's person-minutes; J10's answers

    # every tap counts against the journey, and against the person who made it (a hand-off shows whose taps they were)
    @property
    def taps(self): return self._taps

    @taps.setter
    def taps(self, v):
        self.by[self.uid] = self.by.get(self.uid, 0) + (v - self._taps); self._taps = v

    def end_turn(self):
        return self.w.admin('end_turn')

    def spend(self, verb, sub=None):
        """a person's minutes for one of their own actions (sim/server.py's MINUTES, as Pilot 3 charges a person), never the
        walk's own re-reads of the screen: the eye reads each result as part of the action that brought it"""
        self.minutes += MAIL_MINUTES.get(str(sub or 'list').lower(), 1.0) if verb == 'mail' else MINUTES.get(verb, 0.0) if verb != 'screen' else 0.0

    def world_step(self, slot):
        """time passes inside the journey: the turn closes, the world runs the slot ('next' is the next working day's
        morning), and the same person picks the work up again on the same device"""
        self.end_turn()
        if slot == 'next':
            self.w.admin('advance'); slot = 'morning'
        r = self.w.admin('world', slot=slot, watchers=True)
        self.slot = slot
        self.w.admin('begin_turn', uid=self.uid, slot=slot, cap=9999, device=self.device)
        self.scr = Screen('')
        self.trail.append(f'(the world: {slot}; ' + ', '.join(f'{e[0]} {str(e[2])[:40]}' for e in (r or {}).get('events', [])[:6]) + ')')
        self.look()
        return r

    # ---- the verbs
    def _act(self, cmd, *args, **opts):
        self.calls += 1
        if cmd in ('tap', 'go', 'back', 'key', 'do', 'upload', 'photo'): opts = dict({'full': True, 'marks': True}, **opts)   # the whole screen, as the eye takes it in
        r = self.w.act(self.uid, cmd, args, **opts)
        txt = r.get('text') or ''
        if cmd in self.TAPS: self.taps += 1
        if cmd in self.TAPS or cmd in ('news', 'mail'): self.spend(cmd, args[0] if cmd == 'mail' and args else None)
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
        if 'the tap took over 4 seconds to land' in txt[:300]:   # sim/server.py: the control was covered, then tapped
            self.timed(5, 4, f'"{c.label[:60]}" can be tapped at once (it took over 4 seconds to land: something covered it)')
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
        c = next((x for x in self.look().ctls if x.action and re.search(r' · .*(due|valid to) | · (Mon|Tue|Wed|Thu|Fri|Sat|Sun), \w{3} \d+', x.label)), None)
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
        return self._batch(out)

    def _batch(self, out):
        """the steps in batches of 8; an interruption from the world (a call, a client's mail) stops a batch after the step it
        came in on: the person deals with it and goes on with the rest, as a person does (it is not the app's failure)"""
        for i in range(0, len(out), 8):
            chunk = out[i:i + 8]
            while chunk:
                r, txt = self._act('do', '; '.join(chunk))
                head = txt.split('\n')[0]
                m = re.match(r'do: (\d+) of (\d+) steps', head)
                done = int(m.group(1)) if m else len(chunk)
                self.taps += done
                for st in chunk[:done]: self.spend(st.split(' ')[0])
                self.scr = screen_of(txt)
                if not r.get('ok') and 'you were interrupted' in head:
                    self.note('interrupted mid-batch by the world: ' + next((l for l in txt.split('\n') if l.startswith('INTERRUPTION')), '')[:120])
                    chunk = chunk[done:]; continue
                if not r.get('ok'):
                    raise Stuck('do ' + '; '.join(chunk)[:160], 'every step to land', self.scr, self.last_control + ': ' + head[:200])
                chunk = []
        return self.scr

    def do_ctls(self, steps):
        """a batch on controls already read off the screen: ('type', ctl, text) / ('pick', ctl, option) / ('tap', ctl)"""
        out = []
        for st in steps:
            verb, c = st[0], st[1]
            if c is None: raise Stuck(f'{verb} {st[2] if len(st) > 2 else ""}', 'the field on the screen', self.scr, self.last_control)
            out.append(f'{verb} {c.n}' + (f' {json.dumps(str(st[2]))}' if len(st) > 2 else ''))
            self.last_control = c.label
        return self._batch(out)

    def mail(self, *args):
        r, txt = self._act('mail', *args)
        if not r.get('ok'): raise Stuck('mail ' + ' '.join(args)[:80], 'the mail to go', self.scr, 'mail: ' + txt[:200])
        self.taps += 1
        return txt

    def upload(self, label, path, after=None):
        """a file into a file field (the person's own file: their notes, the slip's photo)"""
        c = self._target(label, True, after, 1, kinds=('file',))
        if c is None: raise Stuck(f'upload into "{label}"', f'a place to add a file labelled "{label}"', self.scr, self.last_control)
        self.last_control = c.label
        r, txt = self._act('upload', c.n, path)
        if not r.get('ok'): raise Stuck(f'upload into "{label}"', 'the file to be taken', screen_of(txt) if CHROME.search(txt) else self.scr, c.label + ': ' + txt[:160])
        self.scr = screen_of(txt)
        return self.scr

    def note(self, text):
        """something the walk did as a person would that is not the app's own path (a mail sent by hand): in the trail"""
        self.notes.append(text); self.trail.append('(note) ' + text[:160])

    def timed(self, took, limit, what):
        """a wait a person feels, judged only when the machine is not loaded: under load a slow sheet is the machine's, not
        the app's (round one: J4 failed at load 17 and passed alone), so it is noted instead of failed"""
        if took <= limit: return True
        la, n = os.getloadavg()[0], os.cpu_count() or 1
        if la > 0.75 * n:
            self.note(f'{what}: it took {took}s; not judged, the machine was loaded ({la:.1f} on {n} CPUs)'); return True
        return self.expect(False, what, f'it took {took}s (load {la:.1f} on {n} CPUs)')

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
CONTRACT = sum(t['qty'] * t['price'] for t in TAKEOFF)
WALK_NOTES = ('Walk-through, 214 Lincoln Place (Wren and Julian Ashby), 9/2 5 pm: parlor kitchen gut and a new garden-level bath, '
              'about $90,000, start Tue 9/8. Takeoff: ' + '; '.join(f"{t['item']} {t['qty']:g} {t['unit']}" for t in TAKEOFF) +
              '. Garden bath radiator: ask Wren before pricing the plumbing (keep or move under the window).')


# ---------------------------------------------------------------------------------------------------- shared steps
def inquiry_to_won(p, subject, client, value, close, note=None):
    """the owner: an inquiry mail becomes a lead (the app's own proposal from the mail), an opportunity (with the walk-through
    noted on it, when there is one), then won"""
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
    if note:   # the walk-through goes on the opportunity, the way a CRM keeps a visit (its Note)
        p.tap('Note', exact=True)
        f = p.look().find('Start typing', field=True) or (p.scr.sheet and next((c for c in p.scr.ctls if c.kind == 'text'), None))
        if not f: raise Stuck('note the walk-through', 'a note box on the opportunity', p.scr, 'Note')
        p.do_ctls([('type', f, note)])
        p.tap('Save note', exact=True)
        p.expect('note saved' in norm(p.scr.toast) or p.look().has('walk-through'), 'the walk-through note is saved on the opportunity', p.scr.toast)
    p.tap('Closed Won', expect='Close as Won')
    p.tap(close, exact=True)
    p.expect(not p.scr.toast or norm(client) in norm(p.scr.toast) and not re.search(r'— design-build is a client', norm(p.scr.toast)),
             f'the toast names the client that was made ({client})', p.scr.toast)


def new_project(p, name, addr, start, client):
    p.go('Projects')
    p.tap('New Project', expect='Project Name')
    p.do([('type', 'Project Name', name), ('type', 'Address / Scope', addr), ('type', 'Start Date', start), ('pick', 'Client', client), ('tap', 'Add Project')])
    p.expect('Created' in p.scr.toast, 'a toast that the project was made, with Open', p.scr.toast)


def open_job(p, page=None):
    """the job's own page, the way a PM gets to it: Projects, the job, then the page in the job's menu"""
    p.go('Projects', expect_menu=False)
    sw = p.scr.find('Switch project', field=True)
    if sw and norm(sw.value) != norm(JOB['job']): p.pick('Switch project', JOB['job']); p.look()   # the page redraws for the job: read it again
    elif not sw:
        r = p.look().row(JOB['job'], after='Every job') or p.scr.row(JOB['job'])
        if r: p.tap_ctl(r)
    if page: p.tap(page, exact=True)
    return p.look()


def notes_file(p, name, text):
    """the person's own notes, as a file they carry (the walk-through written up)"""
    d = os.path.join(p.w.dir, 'files', p.uid); os.makedirs(d, exist_ok=True)
    f = os.path.join(d, name); open(f, 'w', encoding='utf-8').write(text)
    return f


# ---------------------------------------------------------------------------------------------------- J1 win the inquiry
def j1_win_inquiry(p):
    """The owner: the Ashbys' mail becomes a lead, the walk-through is noted, the lead is won into one client, the project
    opens under it, and the walk-through notes are on the project."""
    inquiry_to_won(p, '214 Lincoln Place: thank you for yesterday', JOB['client'], CONTRACT, 'Close as Won', note=WALK_NOTES)
    new_project(p, JOB['job'], JOB['addr'], JOB['start'], JOB['client'])
    sc = open_job(p, 'Overview')
    on = sc.has('walk-through') or open_job(p, 'Documents').has('walk-through')
    p.expect(on, 'the walk-through noted on the opportunity is on the project once it is won (Overview or Documents)',
             'neither the Overview nor the Documents of 214 Lincoln Place mention the walk-through')
    if not on:   # a person puts their notes where the job keeps its papers
        if not p.scr.find('Upload Files', field=True): open_job(p, 'Documents')
        p.upload('Upload Files', notes_file(p, 'Walk-through notes 214 Lincoln Place.txt', WALK_NOTES))
        p.note('the walk-through notes uploaded to the job\'s Documents as a file (no place for notes on the project)')


# ---------------------------------------------------------------------------------------------------- X1 (extra) proposal at won
PROBE = {'client': 'Nadia Okoro', 'job': '88 Garfield Place', 'subject': 'Renovating 88 Garfield Place', 'addr': '88 Garfield Place, Park Slope: kitchen'}


def header_field(p, label):
    """a field of a record's header; on the phone the header is folded under its one-line summary, which a person taps open"""
    f = p.look().find(label, field=True)
    if f is None and p.expand(): f = p.scr.find(label, field=True)
    return f


def x1_owner_proposal_first(p):
    """The owner on another inquiry (the world's Nadia Okoro, 88 Garfield Place), taking the app's own next step at won,
    Close and Start the Proposal: the estimate starts before the job exists. Can it be tied to its job?"""
    inquiry_to_won(p, PROBE['subject'], PROBE['client'], 120000, 'Close and Start the Proposal')
    f = header_field(p, 'Project')
    p.expect(f is not None and (any(o not in ('—', '-', '') for o in f.opts) or any('new project' in norm(o) for o in f.opts)),
             'the new estimate\'s Project list offers the job, or a way to open it, so the estimate can be tied to its project',
             f'Project = "{f.value if f else ""}", options {{{"|".join(f.opts) if f else ""}}}')
    num = (re.findall(r'EST-\d{4}-\d+', p.scr.text) or [''])[0]
    new_project(p, PROBE['job'], PROBE['addr'], JOB['start'], PROBE['client'])
    p.go('Sales')
    p.tap('Estimates', exact=True)
    p.tap_row(num or PROBE['client'], after='Search', expect='Estimate EST-')
    f = header_field(p, 'Project')
    p.expect(f is not None and norm(f.value) == norm(PROBE['job']), f'{num} shows its job, {PROBE["job"]}, once the job is open', f'Project = "{f.value if f else ""}"')


def probe_tied(w, p=None):
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


# ---------------------------------------------------------------------------------------------------- J2 price the job
def open_estimate(p, menu_check=False, create=False):
    """where the PM looks for the Ashbys' estimate: Estimates in the menu; else the job's own Estimates"""
    if menu_check:
        p.expect(any(norm(re.sub(r'\s+\d+$', '', m)) == 'estimates' for m in p.scr.menu),
                 'Estimates in the PM\'s menu', 'the menu has: ' + ' · '.join(p.scr.menu))
    open_job(p, 'Estimates')
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
        # the phone's full-screen line editor (.ct-sheet, read as a sheet since 10-26): the item first (it may pull a price
        # from the library and redraw the sheet), then each field read again; the budget cost input has no label of its
        # own, so it is the field under the words "Budget cost", as a person finds it
        F = lambda rx: next((c for c in p.scr.ctls if not c.action and re.search(rx, c.label, re.I)), None)
        item = F(r'item|descr')
        if item is None: raise Stuck(f'line {k}: the line sheet', 'an Item field on the line sheet', p.scr, 'Add Line Item')
        p.do_ctls([('type', item, t['item'])])
        for rx, key, what in ((r'qty|quant', 'qty', 'quantity'), (r'unit|^ls$', 'unit', 'unit'), (r'rate|price', 'price', 'price'), (None, 'cost', 'budget cost')):
            p.look()
            c = F(rx) if rx else (F(r'cost|budget') or p.scr.find('', field=True, after='Budget cost'))
            if c is None: raise Stuck(f'line {k}: the line sheet', f'a {what} field on the line sheet', p.scr, 'Add Line Item')
            if not rx: p.expect(bool(re.search(r'cost|budget', c.label, re.I)), 'the line\'s budget cost field has a label of its own on the phone', f'it reads as "{c.label}"')
            try: p.do_ctls([('type', c, t[key])])
            except Stuck as e:
                if rx: raise
                p.expect(False, f'line {k}: the budget cost can be typed on the phone', (e.control or '')[-160:])
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


def j2_price_job(p):
    """The PM: the 12 lines of the takeoff keyed into the estimate on the job, the margin read, then sent to the Ashbys."""
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
    # the margin, read before it goes (what a pro checks: per line and in total)
    p.look()
    p.expect(bool(re.search(r'margin[^\n]{0,60}?\d+(\.\d+)?\s?%|\d+(\.\d+)?\s?%\s*margin', p.scr.text, re.I)),
             'the estimate shows its margin (in total) before it is sent', p.scr.excerpt('margin', 4))
    send_estimate(p)


def send_estimate(p):
    """the cover email, sent, and the estimate marked sent"""
    open_estimate(p)
    num = est_number(p)
    # a draft's safe next step is Review and Send, the cover email (it was Draft Cover Email beside a blue Mark Sent;
    # the estimate lane, 2026-10-26, cycle walk dangerous buttons)
    p.tap('Review and Send') if p.look().find('Review and Send') else p.tap('Draft Cover Email')
    took = wait_for(p, 'Cover Email', 25)
    if took is None: raise Stuck('Draft Cover Email', 'the cover email to open', p.scr, 'Draft Cover Email')
    p.timed(took, 5, 'the cover email opens within 5 seconds with the assistant off')
    to = (p.scr.find('To', field=True) or Ctl(0, 'input', '', 0, 0)).value or JOB['emails'][0]
    subj = (p.scr.find('Subject', field=True) or Ctl(0, 'input', '', 0, 0)).value or f'{num} 214 Lincoln Place'
    body = (p.scr.find('Body', field=True) or Ctl(0, 'text', '', 0, 0)).value.replace('…', '')
    p.tap('Open in Mail App')
    p.expect(False, 'Send to Client sends the estimate from the app (it hands off to a mail app; nothing is sent or recorded)',
             'Open in Mail App opens a mailto: link; the PM sends from their own mailbox and comes back to Mark Sent')
    p.mail('send', to, subj, (body or f'Attached is estimate {num}.') + f'\n\nEstimate {num} attached (PDF). Alan')
    p.note(f'{num} sent from the PM\'s own mailbox (the app hands off to a mail app)')
    p.look()
    if not p.scr.has(num) or not p.scr.find('Mark Sent'): open_estimate(p)
    p.tap('Mark Sent', exact=True)
    if p.look().sheet and p.scr.find('Sent On', field=True):   # Mark Sent asks how it went and the day (the estimate lane)
        p.do([('pick', 'How It Went', 'Email from my own mailbox'), ('type', 'Sent On', p.w.world_state().get('day') or ''),
              ('tap', 'Record It Sent')])
    p.expect(p.look().has('Sent'), f'{num} reads Sent', p.scr.excerpt('draft', 6))


# ---------------------------------------------------------------------------------------------------- hand-offs
def switch(p, uid, device):
    """another person picks up the work (a hand-off inside one journey); the journey's counts go on"""
    p.end_turn()
    p.uid, p.device, p.scr = uid, device, Screen('')
    p.w.admin('begin_turn', uid=uid, slot=p.slot, cap=9999, device=device)
    p.look()


# ---------------------------------------------------------------------------------------------------- J8 bill the deposit
def record_signature(p):
    """The owner: the Ashbys' signed copy (the world's reply to the estimate that reached them) recorded on the estimate
    with who and when; the contract and the schedule of values from the estimate."""
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


def open_meta(p):
    """an invoice's title and dates: on the phone they sit folded under the "Invoice · <date> · due <date>" line, which a
    person taps open to edit"""
    if not p.look().find('Title', field=True, exact=True): p.expand()


def deposit_invoice(p):
    """Billing: the Ashbys' 25% deposit, invoiced from the contract and sent; returns its number"""
    p._act('news')
    p.go('Billing')
    p.expect(p.scr.has('Wren & Julian Ashby') or p.scr.has('214 Lincoln'), 'the signed contract\'s deposit waits in Billing\'s queue (Ready to Bill)',
             p.scr.excerpt('Ready', 6))
    p.go('Clients', expect_menu=False)
    p.tap_row(JOB['client'], after='Search')
    p.tap('Billing', after=JOB['client'], exact=True)
    p.expect(bool(p.look().find('Deposit Invoice') or p.scr.find('New Deposit Invoice') or p.scr.find('Bill the Deposit')),
             'a Deposit Invoice from the signed contract (25%, no retainage)', 'only New Invoice: the deposit is typed by hand')
    p.tap('New Invoice', exact=True)
    open_meta(p)
    dep = round(CONTRACT * JOB['deposit_pct'] / 100, 2)
    p.do([('type', 'Title', f"Deposit — {JOB['deposit_pct']}% on signing")])
    p.tap('Add Line', exact=True)
    p.look()
    it, rate = p.scr.find('Item', field=True, exact=True), p.scr.find('Rate', field=True)
    p.do_ctls([('type', it, f"Deposit on signing: {JOB['deposit_pct']}% of the ${CONTRACT:,.0f} contract"), ('type', rate, str(dep))])
    for _ in range(2):
        if p.look().has('Unsaved changes'): p.tap('Save', exact=True)
    inv = (re.findall(r'INV-\d{4}-\d+', p.scr.text) or [''])[0]
    p.tap('Send to Client', exact=True, expect='Send to Client')
    to = (p.scr.find('To', field=True) or Ctl(0, 'input', '', 0, 0)).value
    subj = (p.scr.find('Subject', field=True) or Ctl(0, 'input', '', 0, 0)).value
    p.tap('Send', exact=True)
    out = 'in your mail app to send' in p.scr.toast
    p.expect(not out, f'Send sends {inv} from the app (the toast: "in your mail app to send")', p.scr.toast)
    if out:
        p.mail('send', to or JOB['emails'][0], subj or f'{inv} deposit', f'Attached is invoice {inv} for ${dep:,.2f}, the deposit on signing. Billing')
        p.note(f'{inv} also mailed from billing\'s own mailbox')
    return inv, dep


def match_deposit(p, inv, dep):
    """Billing, the next morning: the Ashbys' transfer is on the bank feed; it is matched to the deposit invoice (the bank
    line, not a typed payment). The way a bookkeeper finds it: Banking's line, else the invoice's own payment."""
    p.go('Banking', expect_menu=False)
    sc = p.look()
    i = sc.text.find('FROM ASHBY')
    p.expect(i >= 0, 'the Ashbys\' transfer is on billing\'s Banking the morning it clears', sc.excerpt('Banking', 10))
    if i >= 0:
        prop = sc.text[i: i + 400]
        p.expect(inv in prop, f'the app proposes the transfer for {inv}', prop[:200])
        c = next((x for x in sc.ctls if x.pos > i and x.action), None)
        if c is None or not re.match(r'^(confirm|match|record|apply)', norm(c.label)):
            raise Stuck('match the Ashbys\' transfer', f'a Confirm or Match to {inv} on the bank line', sc, c.label if c else '')
        p.tap_ctl(c)
        sc = p.look()
        if sc.sheet:   # a sheet that asks which invoice, or a reason
            f = next((x for x in sc.ctls if x.kind == 'select' and any(inv in o for o in x.opts)), None)
            if f: p.pick_ctl(f, next(o for o in f.opts if inv in o))
            b = next((x for x in sc.actions('sheet') if re.match(r'^(match|confirm|record|apply|save|link)', norm(x.label))), None)
            if b: p.tap_ctl(b)
        p.expect(bool(re.search(r'match|record|paid|applied|confirm', p.scr.toast, re.I)), f'a toast that the transfer is matched to {inv}, with Open', p.scr.toast)
        return
    # no line on Banking: the invoice's own payment, and whether it offers the bank line
    p.go('Clients', expect_menu=False)
    p.tap_row(JOB['client'], after='Search')
    p.tap('Billing', after=JOB['client'], exact=True)
    p.tap_row(inv)
    c = p.look().find('Find in Bank') or p.scr.find('Match Payment') or p.scr.find('Record Payment')
    if c is None: raise Stuck(f'record the payment on {inv}', 'Find in Bank or Record Payment on the invoice', p.scr, inv)
    p.tap_ctl(c)
    p.expect(p.look().has('ASHBY'), f'the payment sheet offers the bank line (ONLINE TRANSFER FROM ASHBY W ${dep:,.2f}) to match', p.scr.excerpt('', 12))
    raise Stuck(f'record the payment on {inv}', 'the bank line to match (not a typed amount)', p.scr, c.label)


def j8_bill_deposit(p):
    """The deposit: the owner records the Ashbys' signature and the contract (the hand-off that starts it), billing
    invoices 25% and sends it; the next morning the transfer clears and billing matches it to its bank line."""
    me, dev = p.uid, p.device
    switch(p, 'u_owner', dev)
    try: record_signature(p)
    finally: switch(p, me, dev)
    inv, dep = deposit_invoice(p)
    p.world_step('next')   # Friday morning: the Ashbys' transfer clears; the bank feed brings the line in
    match_deposit(p, inv, dep)


# ---------------------------------------------------------------------------------------------------- J5 get three quotes
YARDS = [('Brooklyn Lumber', 'Sal Ferro', 'orders@brooklynlumber.example'), ('Gowanus Building Supply', 'Dee Marsh', 'orders@gowanusbuilding.example'),
         ('Atlantic Yard Supply', 'Ray Quint', 'sales@atlanticyardsupply.example')]
RFQ_LINES = ['Framing lumber: supply', 'Drywall & cement board: supply', 'Porcelain floor tile 12x24 matte: supply']
QUOTE_TYPED = {'Atlantic Yard Supply': ['891', '2288', '61']}   # Ray Quint's prose reply, as a person reads it


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


def j5_three_quotes(p):
    """The coordinator: the three yards from the huddle on file, one RFQ from three estimate lines at once, the foreman's
    quantity check on his phone, the three yards picked and sent; after the replies come in, each quote recorded and
    confirmed against its reply (one in prose, typed by hand), levelled, awarded."""
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
        more = p.scr.find('More for Today')
        p.expect(c is not None, f'{rfq} is on the foreman\'s Today when he opens it (not folded away)',
                 'folded under "More for Today"' if more else 'not on his Today')
        if c is None and more:   # a person looks in the fold the Today offers
            p.tap_ctl(more)
            c = p.look().next_action(rfq or 'RFQ-20')
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
    if not sent:
        send_drafts(p, rfq); p.note(f'{rfq} sent from the coordinator\'s mailbox drafts')
    p.world_step('work2')   # the yards answer by mail
    record_quotes(p)
    award(p)


def record_quotes(p):
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


def award(p):
    """the award from the levelled quotes: the order it makes is J6's to issue"""
    p.look()
    if p.scr.find('Award Without Negotiating'): p.tap('Award Without Negotiating', exact=True)
    p.tap('Award and Create POs', exact=True)
    po = (re.findall(r'PO-\d{4}-\d+', p.scr.toast) or [''])[0]
    p.expect(bool(po), 'a toast naming the PO the award made, with Open', p.scr.toast)


# ---------------------------------------------------------------------------------------------------- J6 buy it
PLUMB_BUYS = [('Toilet and vanity faucet (allowance picks)', 1800), ('Shower valve and trim (allowance picks)', 1200)]
TILE_PRICE = 14.50   # what Nemo Tile asked this time, per sf ($12.50 on PO-2026-041): the price the coordinator types on the moved tile line
VENDOR_MAIL = {'nemo tile': 'sales@nemotile.example', 'ferguson': 'orders@ferguson.example', 'gowanus building supply': 'orders@gowanusbuilding.example',
               'brooklyn lumber': 'orders@brooklynlumber.example', 'atlantic yard supply': 'sales@atlanticyardsupply.example'}   # the huddle's list, the vendor's card


def open_po(p, number):
    p.go('Purchasing')
    p.tap('Orders', exact=True)
    if not p.look().row(number, after='Search'):   # the phone keeps the last order open: back to the list
        c = p.scr.find('Purchasing', kinds=('link',))
        if c: p.tap_ctl(c)
        else: p._act('back')
        p.look()
    p.tap_row(number, after='Search', expect=number)


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
        if p.look().sheet and 'email to vendor' in norm(p.scr.sheet_title): p._act('back')
    return True


def reached_vendor(p, number):
    """the order went out: a mail naming it in the person's Sent"""
    return number in p.mail('sent')


def issue_and_send(p, number):
    p.look()
    lab = next((l for l in ('Issue PO', 'Submit for Approval') if p.scr.find(l, exact=True)), None)
    if lab: p.tap(lab, exact=True)
    if lab == 'Submit for Approval' or 'approv' in norm(p.scr.toast) and 'issued' not in norm(p.scr.toast):
        # over a house threshold: the owner approves it (on the same device), then the coordinator issues it
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
    if not reached_vendor(p, number):   # nothing left the app: the order goes from the coordinator's own mailbox, as she would
        vend = next((v for v in VENDOR_MAIL if v in norm(p.look().text)), '')
        if vend:
            p.mail('send', f'{vend.title()} <{VENDOR_MAIL[vend]}>', f'Purchase order {number}: 214 Lincoln Place',
                   f'Please confirm purchase order {number} for 214 Lincoln Place (the PDF is in the order). Chen')
            p.note(f'{number} sent from the coordinator\'s own mailbox (the app\'s own send did not go)')


def board_for_job(p):
    """the Buy Board for 214 Lincoln: its Project list (on the phone, behind "Filter by project, vendor or trade")"""
    if not p.look().find('Project', field=True):
        f = p.scr.find('Filter by project')
        if f: p.tap_ctl(f)
    p.pick('Project', JOB['job'])


def award_po(p):
    """the order the award made (a draft on 214 Lincoln from one of the yards), from the Orders list"""
    p.go('Purchasing')
    p.tap('Orders', exact=True)
    for l in p.look().text.split('\n'):
        if re.search(r'214 Lincoln', l) and re.search(r'Gowanus|Brooklyn Lumber|Atlantic Yard', l):
            m = re.search(r'PO-\d{4}-\d+', l)
            if m: return m.group(0)
    raise Stuck('find the award\'s order', 'the yard\'s order for 214 Lincoln in Orders', p.scr, 'Orders')


def j6_buy_it(p):
    """The coordinator: the award's order (lumber and drywall; the tile moved to the tile house at the line's price and
    checked against the last price paid) issued and sent; two buys on the same plumbing line; the stock looked at before
    the electrical rough-in material is bought."""
    po = award_po(p)
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
        p.do([('type', 'Why', 'Three quotes; Gowanus lowest landed. The line budget was set before the yards priced it.'), ('tap', 'Save the Reason')])
    issue_and_send(p, po)
    if tile_po:
        open_po(p, tile_po)
        up = p.scr.find('Unit Price', field=True, nth=1)
        if up: p.do_ctls([('type', up, f'{TILE_PRICE:.2f}')])
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
        board_for_job(p)
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
    # the stock, before buying the electrical rough-in material: the shop has the 12/2, the boxes and the Type X
    p.go('Purchasing')
    p.tap('Buy Board', exact=True)
    board_for_job(p)
    sc = p.look()
    i = sc.text.find('Electrical rough-in')
    near = sc.text[max(0, i - 200): i + 600] if i >= 0 else ''
    p.expect(i >= 0 and bool(re.search(r'(in stock|on hand|at the shop|in the shop|warehouse|from stock)', near, re.I)),
             'the Buy Board shows the firm\'s own stock against the electrical rough-in line before anything is ordered (12/2 NM-B, 1-gang boxes, 5/8 Type X are on the shelf)',
             near[:300] or 'no electrical line on the Buy Board')


# ---------------------------------------------------------------------------------------------------- J4 review the job (Friday)
REVIEW_PAGES = ('Schedule', 'Costs', 'Change Orders', 'Decisions', 'Submittals')


def cost_rows(text):
    """the Costs page's Line Profitability table, read the way a PM reads it: each estimate line's budget cost, actual
    and committed (columns found by their headings)"""
    head = next((l for l in text.split('\n') if re.search(r'BUDGET COST', l) and re.search(r'COMMITTED', l)), '')
    if not head: return []
    H = [re.sub(r'\[\d+\s*|\]', '', c).strip().upper() for c in head.split('|')]
    col = lambda name: next((i for i, h in enumerate(H) if h.startswith(name)), None)
    ib, ia, ic = col('BUDGET COST'), col('ACTUAL'), col('COMMITTED')
    out = []
    for l in text.split('\n'):
        if 'EST-' not in l or '|' not in l: continue
        c = [x.strip() for x in l.split('|')]
        if None in (ib, ia, ic) or len(c) <= max(ib, ia, ic): continue
        name = re.sub(r'EST-\d{4}-\d+.*$', '', re.sub(r'\[\d+[^\]]*\]', '', c[0])).strip()
        out.append({'line': name, 'budget': CY.num(c[ib]), 'actual': CY.num(c[ia]), 'committed': CY.num(c[ic])})
    return out


def over_lines(text):
    """the estimate lines over budget on the Costs page: committed or actual above the line's budget cost (as a PM reads
    the columns, whether or not the page flags them)"""
    return [f"{r['line']} ${max(r['actual'], r['committed']) - r['budget']:,.0f} over" for r in cost_rows(text)
            if r['budget'] > 0 and max(r['actual'], r['committed']) > r['budget'] + 0.5]


def j4_friday_review(p):
    """The PM on Friday: 214 Lincoln's next weeks of schedule, budget against committed and actual by estimate line, the
    open change orders, decisions and submittals; then the client update, naming the lines over budget."""
    over = []
    for page in REVIEW_PAGES:
        sc = open_job(p, page)
        if page == 'Schedule':
            p.expect(bool(re.search(r'\b(9/8|9/9|9/1\d|9/2\d|Sep \d)', sc.text)) and not sc.has('No Schedule'),
                     'the schedule shows 214 Lincoln\'s next three weeks', sc.excerpt('Schedule', 8))
        if page == 'Costs':
            p.expect(bool(cost_rows(sc.text)), 'Costs shows budget, committed and actual for each estimate line', sc.excerpt('Costs', 10))
            over = over_lines(sc.text)
            flagged = [l for l in sc.text.split('\n') if 'EST-' in l and '|' in l and re.search(r'over|⚠|flag', l.split('|')[1] if len(l.split('|')) > 1 else '', re.I)]
            p.expect(not over or len(flagged) >= len(over), 'Costs flags the estimate lines over budget (committed or actual above the budget cost)',
                     f'{len(over)} over by the columns ({"; ".join(over)}), {len(flagged)} flagged')
    sc = open_job(p, 'Overview')
    c = next((x for x in sc.ctls if x.action and re.search(r'^(draft|send|write|prepare)\b.{0,20}\bupdate', x.label, re.I)), None)
    p.expect(c is not None, 'the app drafts the client update from the week (schedule, logs, decisions, money)', 'no update to draft on the job')
    if c is not None:
        p.tap_ctl(c)
        sc = p.look()
        body = next((x for x in sc.ctls if x.kind == 'text'), None)
        if body and over: p.do_ctls([('type', body, (body.value or '') + '\n\nOver budget this week: ' + '; '.join(over) + '.')])
        b = next((x for x in (sc.actions('sheet') if sc.sheet else sc.actions()) if re.match(r'^send', norm(x.label))), None)
        if b is None: raise Stuck('send the client update', 'a Send on the update', sc, c.label)
        p.tap_ctl(b)
        return
    text = ('Wren, Julian: the week at 214 Lincoln Place. Signed Thursday; demo starts Tuesday 9/8 with the parlor kitchen, '
            'then framing and the garden bath rough. Material is ordered. ' + (('Over budget: ' + '; '.join(over) + '. ') if over else 'Nothing is over budget. ') + 'Alan')
    p.mail('send', 'Wren Ashby', '214 Lincoln Place: this week and next week', text)
    p.note('the client update sent from the PM\'s own mailbox' + (f' naming {len(over)} lines over' if over else ' (Costs named no line over budget)'))


# ---------------------------------------------------------------------------------------------------- J7 receive and match
def receive_po(p, key, number_rx, how):
    """the coordinator records a truck against its order: what came, what is short, what is damaged (with the photo)"""
    p.go('Purchasing')
    c = p.look().find('Deliveries', exact=True) or p.scr.find('Receive', exact=True)
    if c: p.tap_ctl(c)
    sc = p.look()
    row = next((r for r in (sc.row(n) for n in re.findall(number_rx, sc.text)) if r), None)
    if row is None: raise Stuck(f'receive the {key} order', f'the {key} order among Deliveries to receive', sc, 'Deliveries')
    p.tap_ctl(row)
    sc = p.look()
    rc = next((x for x in sc.ctls if x.action and re.match(r'^(receive|record (the )?delivery|log (the )?delivery|mark received)', norm(x.label))), None)
    if rc is None: raise Stuck(f'receive the {key} order', 'a Receive on the order', sc, row.label)
    p.tap_ctl(rc)
    how(p)


SHORT_BOARDS, DAMAGED_SF = 6, 31


def po_for(p, words):
    """the 214 Lincoln order that carries a line, read off Purchasing > Orders"""
    p.go('Purchasing')
    p.tap('Orders', exact=True)
    for l in p.look().text.split('\n'):
        if '214 Lincoln' in l and words.lower() in l.lower():
            m = re.search(r'\b(PO-\d{4}-\d+|FM-\d+)', l)
            if m: return m.group(1)
    raise Stuck(f'find the order for {words}', f'the 214 Lincoln order with {words} in Orders', p.scr, 'Orders')


def report_problem(p, po, kind, line, qty, note):
    """Report a Problem on a delivery: what happened, the line, how many, what the driver said"""
    c = p.look().find('Report a Problem', after=po, exact=True)
    if c is None: raise Stuck(f'report the {kind} on {po}', f'Report a Problem on {po}\'s delivery', p.scr, po)
    p.tap_ctl(c, expect='What happened')
    p.do([('pick', 'What happened', 'Short' if kind == 'short' else 'Damaged'), ('pick', 'Line', line), ('type', 'Quantity affected', str(qty)),
          ('type', 'Note', note), ('tap', 'Report')])
    p.expect('reported' in norm(p.scr.toast), f'a toast that the {kind} on {po} is reported, with Open', p.scr.toast)


def slip_photo(p, po):
    """the packing slip's photo on the order (what a pro checks)"""
    open_po(p, po)
    c = p.look().find('Take Photo', exact=True)
    if c is None:
        p.expect(False, f'a place on {po} for the slip\'s photo', 'no Take Photo on the order'); return
    r, txt = p._act('photo', c.n)
    p.expect(r.get('ok'), f'the slip\'s photo lands on {po}', txt.split('\n')[0][:160])


def receive_desktop(p, dw, tile):
    """the job's Deliveries: each line as it came (the qty is typed, Received), the short and the damage reported on the line"""
    open_job(p, 'Deliveries')
    report_problem(p, dw, 'short', 'Drywall & cement board: supply', SHORT_BOARDS, f'{SHORT_BOARDS} cement boards backordered, balance next week (Angel)')
    report_problem(p, tile, 'damaged', 'Porcelain floor tile 12x24 matte: supply', DAMAGED_SF, 'two boxes cracked in the pallet; photo of the boxes (Angel)')
    for line, qty in (('Framing lumber: supply', 1), ('Drywall & cement board: supply', 1)):
        q = p.look().find('', field=True, after=line)
        b = p.scr.find('Received', after=line, exact=True)
        if q is None or b is None: raise Stuck(f'receive {line} on {dw}', f'a quantity and Received for {line}', p.scr, dw)
        p.expect(not q.value or CY.num(q.value) == 0, f'the received quantity starts empty, not at the full order ({line})', f'it starts at {q.value}')
        p.do_ctls([('type', q, qty), ('tap', b)])
    q = p.look().find('', field=True, after='Porcelain floor tile')
    b = p.scr.find('Received', after='Porcelain floor tile', exact=True)
    if q is None or b is None: raise Stuck(f'receive the tile on {tile}', 'a quantity and Received for the tile', p.scr, tile)
    p.do_ctls([('type', q, 380 - DAMAGED_SF), ('tap', b)])


def receive_phone(p, dw, tile):
    """the phone's Deliveries, else the order's own Receive Some (what came, and the condition in its note)"""
    p.go('Purchasing')
    p.tap('Deliveries', exact=True)
    if p.look().find('All Projects', exact=True): p.tap('All Projects', exact=True)
    c = p.scr.find('Receive', after=dw, exact=True)
    if c is None: raise Stuck(f'receive {dw}', f'{dw} among Deliveries', p.scr, 'Deliveries')
    p.tap_ctl(c)
    sc = p.look()
    ok = bool(sc.find('', field=True, after=dw)) and bool(re.search(r'short|damaged|problem', sc.text[sc.text.find(dw):sc.text.find(dw) + 900], re.I))
    p.expect(ok, f'Receive on the phone takes what came on {dw}: the quantity per line, short and damaged, the slip photo',
             sc.text[sc.text.find(dw):sc.text.find(dw) + 240] if dw in sc.text else 'nothing')
    for po, lines, note in ((dw, [('Framing lumber', 1), ('Drywall', 1)], f'{SHORT_BOARDS} cement boards short: backordered, balance next week'),
                            (tile, [('Porcelain floor tile', 380 - DAMAGED_SF)], f'{DAMAGED_SF} sf damaged: two boxes cracked in the pallet')):
        open_po(p, po)
        p.tap('Receive Some…', exact=True, expect='Receive Some')
        steps = []
        for words, qty in lines:
            f = next((x for x in p.look().ctls if not x.action and x.label.lower().startswith(words.lower())), None)
            if f is None: raise Stuck(f'receive {po}', f'a quantity for {words}', p.scr, 'Receive Some…')
            steps.append(('type', f, qty))
        steps.append(('type', p.scr.find('Note', field=True), note))
        p.do_ctls(steps)
        p.tap('Record Receipt', exact=True)
        p.note(f'{po} received through its own Receive Some, the condition in the note (the phone\'s Deliveries takes no quantity)')


def enter_bill(p, po, two_lines=False):
    """the vendor's invoice from the mail, entered against its order (the mail's own Enter the Bill)"""
    sc = open_mail(p, r'^Invoice \S+ for ' + re.escape(po), 'the invoice')
    if sc is None: raise Stuck(f'the bill for {po}', f'the vendor\'s invoice for {po} in the mail', p.scr, 'Mail')
    c = p.look().find('Enter the Bill', exact=True)
    if c is None: raise Stuck(f'enter the bill for {po}', 'Enter the Bill on the vendor\'s invoice', p.scr, po)
    p.tap_ctl(c, expect='Purchase Order')
    sc = p.look()
    f = sc.find('Purchase Order', field=True)
    p.expect(f is not None and po in (f.value or ''), f'the bill is entered against {po}', f'Purchase Order = {f.value if f else "(none)"}')
    if po and f and po not in (f.value or '') and any(po in o for o in f.opts): p.pick_ctl(f, next(o for o in f.opts if po in o))
    el = sc.find('Estimate Line', field=True)
    if two_lines:
        p.expect(el is None or not el.value or el.value.startswith('No estimate') or 'two lines' in sc.text.lower(),
                 f'the bill for {po} keeps the order\'s two lines (lumber and drywall) on their own estimate lines, not all on one',
                 f'Estimate Line = {el.value if el else ""}')
    p.tap('Enter the Bill', exact=True)
    inv = (re.findall(r'Bill (\S+) entered', p.scr.toast) or [''])[0]
    p.expect(bool(inv), f'a toast that the bill for {po} is entered, with Open', p.scr.toast)
    return inv


def approve_what_arrived(p, inv, po, less, why):
    """the three-way match: the bill approved at what arrived and the rest held in dispute (the claim). Only the Owner
    approves part of a bill: the coordinator hands it over"""
    p.go('Accounting', expect_menu=False)
    p.tap('Bills & Payroll', exact=True)
    c = p.look().find('Review', after=inv, exact=True) or p.scr.row(inv)   # the bill's own row (its control comes before its words)
    if c is None: raise Stuck(f'hold {inv}', f'{inv} among the bills to approve', p.scr, 'Bills & Payroll')
    p.tap_ctl(c)
    sc = p.look()
    b = next((x for x in sc.ctls if x.action and re.match(r'^(approve part|approve po amount|short)', norm(x.label))), None)
    p.expect(b is not None, f'{inv} can be approved at what arrived and the rest disputed (the three-way match against the receipt)',
             'its only Approve is the whole bill: the app compares a bill with its PO, not with what was received')
    if b is None:   # the owner's way round: hold the whole bill, saying why, until the vendor credits what did not arrive
        h = sc.find('Hold', exact=True)
        if h is None: p._act('back'); return False
        p.tap_ctl(h)
        if not p.look().has('Hold the Bill'): p.tap('Hold', exact=True)
        p.do([('type', 'Reason', why), ('pick', 'Task For', 'Chen Biron'), ('tap', 'Hold the Bill')])
        p.note(f'{inv} held whole by the owner (no way to approve part against what arrived)')
        p._act('back')
        return False
    p.tap_ctl(b)
    sc = p.look()
    amt = next((x for x in sc.ctls if not x.action and re.search(r'amount|approve', x.label, re.I)), None)
    w = next((x for x in sc.ctls if not x.action and re.search(r'why|reason', x.label, re.I)), None)
    if amt is None or w is None: raise Stuck(f'hold {inv}', 'the amount to approve and the reason', sc, b.label)
    # what arrived: the order's amount the sheet starts from (else the bill's), less what did not come or came broken
    base = CY.num(amt.value) or CY.num((re.findall(r'is \$([\d,]+(?:\.\d\d)?)', sc.text) or ['0'])[0])
    approve = round(max(0.0, base - less), 2)
    p.do_ctls([('type', amt, f'{approve:.2f}'), ('type', w, why)])
    s2 = next((x for x in sc.actions('sheet') if re.match(r'^approve and dispute|^dispute|^approve part', norm(x.label))), None)
    if s2 is None: raise Stuck(f'hold {inv}', 'Approve and Dispute on the sheet', sc, b.label)
    p.tap_ctl(s2)
    p.expect(bool(re.search(r'disputed|held', p.scr.toast, re.I)), f'a toast that {inv} is approved at ${approve:,.2f} and the rest held', p.scr.toast)
    return True


def j7_receive_match(p):
    """The coordinator: two trucks (the drywall 6 cement boards short, the tile with two boxes cracked) received as they came;
    the vendors' bills matched three ways and held at what arrived; the damaged tile claimed; the credit memo recorded."""
    me, dev = p.uid, p.device
    p._act('news')
    dw, tile = po_for(p, 'Drywall & cement board'), po_for(p, 'Porcelain floor tile')
    both = dw == po_for(p, 'Framing lumber')
    (receive_desktop if dev == 'desktop' else receive_phone)(p, dw, tile)
    slip_photo(p, dw); slip_photo(p, tile)
    p.world_step('work1')   # the vendors' invoices come by mail
    bills = {dw: enter_bill(p, dw, two_lines=both), tile: enter_bill(p, tile)}
    # what did not arrive, at the order's prices: the yard's 1/2" cement board at its quoted price, the tile at the price on its order
    board = BOOK['parties']['gowanus_supply']['quotes']['prices'].get('cement', 26.50)
    p.expect(False, 'the coordinator who received the trucks holds the bills at what arrived (only the Owner approves part of a bill)',
             'the bills wait for the PM\'s review and the Owner\'s approval; the three-way hold is the Owner\'s')
    switch(p, 'u_owner', dev)
    try:
        if bills[dw]: approve_what_arrived(p, bills[dw], dw, SHORT_BOARDS * board, f'{SHORT_BOARDS} cement boards not delivered (backordered); paid when they come')
        if bills[tile]: approve_what_arrived(p, bills[tile], tile, DAMAGED_SF * TILE_PRICE, f'{DAMAGED_SF} sf of tile arrived cracked (claimed); the fuel and pallet charges are not on the PO')
    finally:
        switch(p, me, dev)
    p.world_step('work2')   # the tile house answers the claim with a credit memo
    record_credit(p, tile, bills[tile])


def record_credit(p, tile, inv):
    """the tile house's credit memo: recorded against the held bill, closing the claim. The Owner or the controller
    records a vendor credit; the coordinator reads it and hands it on if the app says so"""
    sc = open_mail(p, r'^Credit memo \S+ for ' + re.escape(tile), 'the credit memo')
    if sc is None: raise Stuck('the credit memo', f'the tile house\'s credit memo for {tile} in the mail (it comes once the damage is claimed on the bill)', p.scr, 'Mail')
    # the app's reading of the memo: the proposal headed "Credit memo" (or one naming the bill), and what it credits
    m = re.search(r'(?m)^Credit memo\s*$', sc.text) or re.search(re.escape(inv), sc.text[sc.text.find('Attachment'):] if 'Attachment' in sc.text else '')
    i = m.start() if m else -1
    block = sc.text[i:i + 500] if i >= 0 else ''
    p.expect(bool(block) and (inv in block or (tile in block and '214 Lincoln' in block)) and '121 State' not in block,
             f'the memo is read as a credit against {inv} ({tile}, 214 Lincoln)', block[:240] or 'no credit proposal on the memo')
    c = next((x for x in sc.ctls if x.action and i >= 0 and x.pos > i and re.match(r'^(apply|record|approve)', norm(x.label))), None)
    if c is None or not (inv in block or tile in block) or '121 State' in block:   # a pro does not apply a credit to the wrong purchase
        raise Stuck('record the credit memo', f'a proposal that credits {inv} on {tile} (214 Lincoln) to apply', sc, 'Credit memo')
    p.tap_ctl(c)
    if re.search(r'owner or the controller', p.scr.toast, re.I):
        p.expect(False, 'the coordinator who claimed the damage records the vendor\'s credit (the app sends it to the Owner or the controller)', p.scr.toast)
        me, dev = p.uid, p.device
        switch(p, 'u_controller', 'desktop')
        try:
            p.go('Today', expect_menu=False)
            x = p.look().next_action('Credit memo') or p.scr.next_action(inv)
            if x is None: raise Stuck('the controller records the credit', f'the credit memo for {inv} on the controller\'s Today', p.scr, 'Today')
            p.tap_ctl(x)
        finally:
            switch(p, me, dev)
    p.expect(bool(re.search(r'credit', p.scr.toast, re.I)), f'a toast that the credit is recorded on {inv}', p.scr.toast)


# ---------------------------------------------------------------------------------------------------- J3 price a change
JOIST = {'amount': 2400, 'cost': 1600, 'days': 1, 'to_foreman': 'Sister both joists with LVL; photograph before and after. I will send the change order to Wren today.'}


def open_co(p, number):
    """the change order's own page: Clients > the Ashbys > Billing > Change Orders > its row"""
    p.go('Clients', expect_menu=False)
    p.tap_row(JOB['client'], after='Search')
    p.tap('Billing', after=JOB['client'], exact=True)
    c = p.look().find('Change Orders', exact=True)
    if c: p.tap_ctl(c)
    r = p.look().row(number, after='Search') or p.scr.row(number)
    if r is None: raise Stuck(f'open {number}', f'{number} among the Ashbys\' change orders', p.scr, 'Change Orders')
    p.tap_ctl(r, expect=number)


def open_mail(p, rx, what):
    """a message in the person's Mail, the way they find it: the Mail tab, then Everything when the tab's filter hides it"""
    p.go('Messages')
    p.tap('Mail', kinds=('tab',))
    find = lambda: next((p.scr.row(l.strip()) for l in p.scr.text.split('\n') if re.search(rx, l) and not l.strip().startswith('[')), None)
    r = find() if p.look() else None
    if r is None:
        c = p.scr.find('Everything')
        if c: p.tap_ctl(c); r = find()
    if r is None: return None
    p.tap_ctl(r)
    return p.look()


def j3_price_change(p):
    """The PM on the phone: the foreman's find (two rotted joists, with a photo) answered as an extra, priced as a change
    order with its cost, margin and days, sent to the Ashbys; when Wren approves, her approval recorded with who and when."""
    p.go('Today')
    i = p.scr.text.lower().find('joists rotted')
    c = p.scr.next_action('joists rotted') if i >= 0 else None
    if c is None: raise Stuck('the foreman\'s find on Today', 'the joist item on the PM\'s Today, with its photo', p.scr, 'Today')
    p.tap_ctl(c)
    sc = p.look()
    if not sc.find('Amount', field=True):   # a choice first: proceed as an extra
        x = next((b for b in sc.ctls if b.action and re.search(r'extra', b.label, re.I)), None)
        if x: p.tap_ctl(x); sc = p.look()
    tell, amt = sc.find('Tell the Foreman', field=True), sc.find('Amount', field=True)
    if not amt: raise Stuck('answer the joist item as an extra', 'an Amount for the change order on the answer', sc, c.label)
    w = sc.find('Write the Change Order', field=True, kinds=('check',))
    if w and w.state != 'on': p.do_ctls([('tap', w)])
    p.do_ctls(([('type', tell, JOIST['to_foreman'])] if tell else []) + [('type', amt, JOIST['amount'])])
    p.tap('Send to the Field', exact=True)
    co = (re.findall(r'CO-\d{4}-\d+', p.scr.toast) or re.findall(r'CO-\d{4}-\d+', p.look().text) or [''])[0]
    p.expect(bool(co), 'a toast naming the change order drafted from the find, with Open', p.scr.toast)
    if p.look().sheet and 'send to client' in norm(p.scr.sheet_title):
        # the app opens Send at once, with no cost and no days on the change order: a pro prices it first
        p.expect(False, f'the change order asks for its cost and days before it can be sent ({co} opened Send to Client at $2,400 with no cost and 0 days)',
                 p.scr.sheet_title)
        p.tap('Cancel', exact=True)
    o = p.look().find(f'Open {co}') if co else None
    if o: p.tap_ctl(o)
    else: open_co(p, co)
    sc = p.look()
    days = sc.find('Schedule Impact', field=True)
    if days is None and p.expand():   # the numbers move once the header is open: read both from the new screen
        sc = p.scr
        days = sc.find('Schedule Impact', field=True)
    cost = sc.find('cost', field=True, exact=True)
    if days is None or cost is None: raise Stuck(f'price {co}', 'the change order\'s Schedule Impact and the line\'s cost', p.scr, co)
    p.do_ctls([('type', days, JOIST['days']), ('type', cost, JOIST['cost'])])
    p.expect(bool(re.search(r'margin\s+\d+(\.\d+)?\s?%', p.look().text, re.I)), f'{co} shows its margin once the cost is in', p.scr.excerpt('margin', 3))
    p.tap('Send to Client', exact=True, expect='Send to Client')
    p.tap('Send', exact=True)
    p.expect(bool(re.search(r'sent', p.scr.toast, re.I)), f'a toast that {co} went to the Ashbys', p.scr.toast)
    p.world_step('work1')   # Wren answers
    sc = open_mail(p, r'^Re: ' + re.escape(co), 'Wren\'s approval')
    p.expect(sc is not None and sc.has('Approved'), f'Wren\'s approval of {co} in the PM\'s mail', (sc or p.scr).excerpt('Mail', 8))
    open_co(p, co)
    if not p.look().find('Record Client Approval'):
        m = p.scr.find('More', exact=True)
        if m: p.tap_ctl(m)
    if not p.look().find('Record Client Approval'):
        raise Stuck(f'record Wren\'s approval of {co}', 'Record Client Approval on the change order', p.scr, co)
    p.tap('Record Client Approval', expect='How They Approved')
    p.do([('type', 'How They Approved', f'Approved by email from Wren Ashby, 9/8 ({co})'), ('tap', 'Record Approval')])
    p.expect('approved' in norm(p.scr.toast), f'a toast that {co} is approved', p.scr.toast)


# ---------------------------------------------------------------------------------------------------- J9 bill the progress
def client_billing(p):
    """the Ashbys' own Billing tab: Clients, the Ashbys, Billing (the tab with its count)"""
    sc = p.go('Clients', expect_menu=False)
    l = sc.find(JOB['client'], kinds=('link',))   # inside one of the Ashbys' documents: its trail leads back to them
    if l: p.tap_ctl(l)
    elif not (sc.find('Overview', exact=True) and sc.has(JOB['client'])): p.tap_row(JOB['client'], after='Search')
    p.tap('Billing', after='Overview', exact=True)
    return p.look()


def j9_bill_progress(p):
    """Billing: the progress invoice from the SOV (the demolition measured on site), 10% retainage, the approved change
    order and the pendants bought for the Ashbys on it, sent, the chase set."""
    p._act('news')
    client_billing(p)
    p.tap('New Progress Invoice…', exact=True, expect='bill off which document')
    p.tap('Start Progress Invoice', exact=True)
    sc = p.look()
    inv = (re.findall(r'INV-\d{4}-\d+', p.scr.toast) or re.findall(r'Invoice (INV-\d{4}-\d+)', sc.text) or [''])[0]
    if not inv: raise Stuck('start the progress invoice', 'a draft progress invoice', sc, 'Start Progress Invoice')
    # the measure from the field: the foreman measured the demolition at 40% (the field day); a line with no measure is not billed
    ret = sc.find('Retainage held', field=True) or next((c for c in sc.ctls if not c.action and c.value == '10' and 'retainage' in sc.text[max(0, c.pos - 40):c.pos].lower()), None)
    p.expect(bool(re.search(r'Retainage held[^\n]*="10"', sc.text)) or (ret is not None and ret.value == '10'), 'the progress invoice holds 10% retainage (the contract\'s)', sc.excerpt('Retainage', 2))
    p.expect(not re.search(r'No Field Measure', sc.text) or bool(re.search(r'measured|foreman update', sc.text[sc.text.find('1. Demolition'):sc.text.find('2. Framing')], re.I)),
             'the demolition line carries the foreman\'s measure from the field (40%), not cost as a fallback', sc.excerpt('1. Demolition', 4))
    steps = []
    for k in range(1, 13):
        f = sc.find(f'This Period % — {k}', field=True, exact=True)
        if f is None: continue
        want = 40 if k == 1 else 0
        if CY.num(f.value) != want: steps.append(('type', f, want))
    co = next((c for c in sc.ctls if not c.action and re.match(r'item — \d+$', norm(c.label)) and re.search(r'joist', c.value or '', re.I)), None)
    p.expect(co is not None, 'the approved change order (the joists) is a line on the progress invoice', 'no change order line among the SOV lines')
    if co is not None:   # the joists were sistered Tuesday (the foreman's one day)
        n = re.search(r'— (\d+)$', co.label)
        pf = sc.find(f'This Period % — {n.group(1)}', field=True, exact=True) if n else None
        if pf and CY.num(pf.value) != 100: steps.append(('type', pf, 100))
    if steps: p.do_ctls(steps)
    sc = p.look()
    exp = next((c for c in sc.ctls if c.action and re.search(r'billable expense|reimbursable|add expense|bill back', c.label, re.I)), None)
    p.expect(exp is not None, 'the pendants bought for the Ashbys ($612.40 on the Amex) can go on the progress invoice (Billable Expenses)', 'no way to add an expense to it')
    if exp is not None:
        p.tap_ctl(exp)
        t = next((c for c in p.look().ctls if c.kind == 'check' and re.search(r'lightology|pendant', c.label, re.I)), None)
        if t: p.do_ctls([('tap', t)])
        a = next((c for c in (p.scr.actions('sheet') if p.scr.sheet else []) if re.match(r'^(add|bill|save)', norm(c.label))), None)
        if a: p.tap_ctl(a)
    for _ in range(2):
        if p.look().has('Unsaved changes'): p.tap('Save', exact=True)
    p.tap('Send to Client', exact=True, expect='Send to Client')
    p.tap('Send', exact=True)
    p.expect(bool(re.search(r'sent', p.scr.toast, re.I)), f'a toast that {inv} went to the Ashbys', p.scr.toast)
    if exp is None:   # the pendants on an invoice of their own, the way billing would still bill them back
        client_billing(p)
        p.tap('New Invoice', exact=True)
        open_meta(p)
        p.do([('type', 'Title', 'Pendant lights for the island (bought for you, at cost)')])
        p.tap('Add Line', exact=True)
        p.look()
        it, rate = p.scr.find('Item', field=True, exact=True), p.scr.find('Rate', field=True)
        p.do_ctls([('type', it, 'Pendant lights for the island: Lightology, 9/4, at cost (receipt attached)'), ('type', rate, '612.40')])
        for _ in range(2):
            if p.look().has('Unsaved changes'): p.tap('Save', exact=True)
        p.tap('Send to Client', exact=True, expect='Send to Client')
        p.tap('Send', exact=True)
        p.note('the pendants billed back on an invoice of their own (the progress invoice takes no expense)')
    sc = p.look()
    p.expect(bool(re.search(r'due|reminder|chase|collect', sc.text, re.I)), f'{inv} shows when it is due and when it will be chased', sc.excerpt('Due', 3))


# ---------------------------------------------------------------------------------------------------- J10 the week's money
KNOWN_LINES = {'LIGHTOLOGY': ('Materials', JOB['job']), 'RESTORATION HARDWARE': ('Materials', '121 State Street')}


def j10_week_money(p):
    """The controller: the week's bank and card lines matched, the 8/31-9/4 payroll built and the owner's approval on his
    phone; then cash, AR and job cost by estimate line read off the books."""
    me, dev = p.uid, p.device
    # 1. the week's lines: confirm what the app proposes for 9/3-9/8 and code the rest (never a typed line)
    p.go('Banking', expect_menu=False)
    for _ in range(12):
        sc = p.look()
        c = None
        for m in re.finditer(r'(?m)^(?:\[\d+\] )?9/[3-8] · ', sc.text):   # the phone's cards carry their number in front
            x = next((y for y in sc.ctls if y.pos > m.start() and y.action), None)
            if x is not None and norm(x.label) == 'confirm' and x.pos - m.start() < 700: c = x; break
        if c is None: break
        p.tap_ctl(c)
        if p.look().sheet:   # a confirmation that asks why (a payment before its bill)
            w = next((x for x in p.scr.ctls if not x.action and x.kind in ('input', 'text')), None)
            b = next((x for x in p.scr.actions('sheet') if re.match(r'^(confirm|save|match|yes)', norm(x.label))), None)
            if w is not None and b is not None: p.do_ctls([('type', w, 'Confirmed against the statement (controller, weekly close)'), ('tap', b)])
            elif b is not None: p.tap_ctl(b)
            else: p._act('back'); break
    # the week's lines that need a category: the app's own suggestion accepted; a line the app cannot place is coded from what
    # the firm knows about it (KNOWN: the PM's pendants for the Ashbys; the designer's pendants for the Kleins, world_book E058)
    for _ in range(10):
        sc = p.look()
        k = sc.text.find('Needs Category')
        if k < 0: break
        c = None
        for m in re.finditer(r'(?m)^(?:\[\d+\] )?9/[3-8] · ', sc.text[k:]):
            x = next((y for y in sc.ctls if y.pos > k + m.start() and y.action), None)
            if x is not None and norm(x.label) == 'accept' and x.pos - (k + m.start()) < 400: c = x; break
        if c is None: break
        p.tap_ctl(c)
    for words, (cat_name, job_name) in KNOWN_LINES.items():
        sc = p.look()
        row = next((i for i, l in enumerate(sc.text.split('\n')) if words in l and '|' in l), None)
        if row is None:   # the phone: the line is a card; tapped, it opens the transaction with its Category and Job
            c = next((c for c in sc.ctls if c.action and words in c.label and 'statement' in norm(c.label)), None)
            if c is None: continue
            p.tap_ctl(c)
            if not (p.scr.find('Category', field=True, exact=True) and p.scr.find('Job', field=True, exact=True)): p._act('back'); continue
            for verb, lab, val in (('pick', 'Category', cat_name), ('pick', 'Job', job_name)):   # the sheet may change under a pick
                p.look(); p.do([(verb, lab, val)])
            p.look(); p.tap('Save', exact=True)
            continue
        F = [c for c in sc.ctls if c.line == row and c.kind == 'select']
        cat = next((c for c in F if c.label.lower().startswith('category')), None)
        job = next((c for c in F if c.label.lower().startswith('job')), None)
        if cat and job:
            if norm(cat.value) != norm(cat_name): p.pick_ctl(cat, cat_name); p.look()
            job = next((c for c in p.scr.ctls if c.line == row and c.kind == 'select' and c.label.lower().startswith('job')), None) or job
            if norm(job.value) != norm(job_name): p.pick_ctl(job, job_name)
    sc = p.look()
    k = sc.text.find('Needs Category')
    end = sc.text.find('input "Search', k) if k >= 0 else -1
    left = [l[:40] for l in re.findall(r'(?m)^9/[3-8] · [^\n]*', sc.text[k:end if end > k else len(sc.text)])] if k >= 0 else []
    p.expect(not left, 'every line of the week is matched or coded from its own proposal', f'{len(left)} of the week\'s lines still need a category: ' + '; '.join(left))
    # 2. the payroll from approved hours, for the owner
    p.go('Bills & Payroll', expect_menu=False)
    p.tap('Time & Crew', exact=True)
    p.tap('Build Payroll from Approved Time', exact=True)
    sc = p.scr
    if sc.sheet:
        f, t = sc.find('Period From', field=True) or sc.find('From', field=True), sc.find('Period To', field=True) or sc.find('To', field=True)
        steps = ([('type', f, '2026-08-31')] if f else []) + ([('type', t, '2026-09-04')] if t else [])
        if steps: p.do_ctls(steps)
        b = next((x for x in p.look().actions('sheet') if re.match(r'^(build|create|add|submit)', norm(x.label))), None)
        if b is None: raise Stuck('build the payroll', 'Build on the payroll sheet', p.scr, 'Build Payroll from Approved Time')
        p.tap_ctl(b)
    built = p.scr.toast
    p.expect(bool(re.search(r'payroll 8/31', built, re.I)), 'a toast that the payroll from 8/31 is built, with Open', built)
    # 3. the owner approves it on his phone
    switch(p, 'u_owner', 'phone')
    try:
        sc = p.go('Today', expect_menu=False)
        m = re.search(r'Payroll 8/31', sc.text)
        c = next((x for x in sc.ctls if m and x.pos > m.start() and x.action and re.match(r'^approve', norm(x.label))), None)
        if c is None:
            sc = p.go('Approvals', expect_menu=False)
            m = re.search(r'Payroll[^\n]{0,20}8/31', sc.text)
            c = next((x for x in sc.ctls if m and x.pos > m.start() and x.action and re.match(r'^(approve|review)', norm(x.label))), None)
        if c is None: raise Stuck('the owner approves the payroll', 'the payroll from 8/31 with its Approve on the owner\'s Today or Approvals', p.scr, 'Today')
        p.tap_ctl(c)
        if p.scr.sheet:   # a confirmation ("differs from the recent average ... Approve anyway?"), or the run itself
            a = next((x for x in p.scr.actions('sheet') if re.match(r'^(approve|yes|confirm)', norm(x.label))), None)
            if a: p.tap_ctl(a)
        p.expect(bool(re.search(r'approved', p.scr.toast, re.I)), 'a toast that the payroll is approved', p.scr.toast)
    finally:
        switch(p, me, dev)
    # 4. the numbers the books hand the owner (Reports): cash, AR, job cost by estimate line on 214 Lincoln, the lines over
    sc = p.go('Reports', expect_menu=False)
    m = re.search(r'(\$[\d,]+(?:\.\d\d)?) Cash in bank', sc.text)
    p.answers['Q1'] = m.group(1) if m else ''
    m = re.search(r'(\$[\d,]+(?:\.\d\d)?) Receivables', sc.text)
    p.answers['Q2'] = m.group(1) if m else ''
    p.tap('Projects', exact=True)
    r = p.look().row(JOB['job'])
    if r is None: raise Stuck('job cost on 214 Lincoln', '214 Lincoln among Reports > Projects', p.scr, 'Projects')
    p.tap_ctl(r)
    sc = p.look()
    i = sc.text.find('By Line')
    p.answers['Q3'] = sc.text[i:i + 4000] if i >= 0 else ''
    p.answers['Q4'] = '; '.join(over_lines(sc.text)) or 'none over'
    p.expect(i >= 0, 'job cost by estimate line on 214 Lincoln (Reports > Projects > the job: By Line)', sc.excerpt('Code', 6))
    p.expect(all(p.answers.get(q) for q in ('Q1', 'Q2')), 'cash and AR are each one figure the controller can read', str({k: v[:60] for k, v in p.answers.items()}))


def answers_graded(w, p):
    """J10's numbers, graded against the referee's own (sim/cycle.py figures)"""
    if not p.answers: return 'not done', 'no numbers read'
    G = w.cycle().grade_answers('u_controller', p.answers)
    right = sum(1 for g in G if g['grade'] == 'right')
    return ('right' if right == len(G) else 'wrong', f'{right} of {len(G)} right: ' + '; '.join(f"{g['q']} {g['grade']}" for g in G))


# ---------------------------------------------------------------------------------------------------- the registry
# id, who owns it, title, the function, the world before it (its slots; 'next' moves to the next working day), and the
# referee's steps (sim/cycle.py) it must leave right (JOURNEYS.md's "done when"). The order is the chain's, in the book's
# days; the report sorts by id. Adding a journey: a function above, a row here, its BUDGET, and a row in JOURNEYS.md.
JOURNEYS = [
    ('J1', 'u_owner', 'Win the inquiry', 'j1_win_inquiry', ['morning'], ['C01', 'C02', 'C03', 'C09']),
    ('X1', 'u_owner', '(extra) A proposal started at won, tied to its job', 'x1_owner_proposal_first', [], [probe_tied]),
    ('J2', 'u_alan', 'Price the job', 'j2_price_job', ['work1'], ['C05', 'C06', 'C37']),
    ('J8', 'u_billing', 'Bill the deposit', 'j8_bill_deposit', ['eod'], ['C07', 'C08', 'C30', 'C31']),
    ('J5', 'u_chen', 'Get three quotes', 'j5_three_quotes', ['work1'], ['C10', 'C11', 'C13']),
    ('J6', 'u_chen', 'Buy it', 'j6_buy_it', [], ['C12', 'C14']),
    ('J4', 'u_alan', 'Review the job (Friday)', 'j4_friday_review', ['eod'], ['C45']),
    ('J3', 'u_alan', 'Price a change', 'j3_price_change', ['next', 'morning'], ['C43', 'C44']),
    ('J7', 'u_chen', 'Receive and match', 'j7_receive_match', [], ['C16', 'C15', 'C17', 'C18', 'C19']),
    ('J9', 'u_billing', 'Bill the progress', 'j9_bill_progress', ['eod'], ['C32', 'C35', 'C34', 'C36']),
    ('J10', 'u_controller', 'Know the week\'s money', 'j10_week_money', [], ['C25', 'C23', 'C24', answers_graded]),
]
TEN = [J[0] for J in JOURNEYS if J[0].startswith('J')]


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
    except Exception as e:   # the walk's own fault, never the app's: named as such so it is fixed in the walk, not reported as a finding
        import traceback
        stuck = {'journey': jid, 'device': device, 'step': f'THE WALK ITSELF FAILED: {type(e).__name__}: {str(e)[:200]}', 'screen': p.scr.title, 'control': p.last_control,
                 'expected': 'the walk to run (a harness fault, not an app finding)', 'got': traceback.format_exc()[-800:], 'walk_error': True}
    finally:
        p.end_turn()
    secs = round(time.time() - t0, 1)
    cy = w.cycle()
    grades = []
    for sid in steps:
        st = cy.step(sid)[:2] if isinstance(sid, str) else sid(w, p)
        grades.append(dict(zip(('status', 'detail'), st), step=sid if isinstance(sid, str) else sid.__name__))
    bt, bm, bdev = budget_for(jid, device)
    r = {'journey': jid, 'title': title, 'uid': uid, 'device': device, 'taps': p.taps, 'by': p.by, 'minutes': round(p.minutes, 1), 'calls': p.calls,
         'seconds': secs, 'budget': bt, 'budget_min': bm, 'budget_of': bdev, 'stuck': stuck, 'soft': p.soft, 'grades': grades, 'notes': p.notes,
         'trail': p.trail[-80:], 'slot': p.slot}
    r['passed'] = not failures_of(r)
    r['stops_at'] = stops_at(r)
    return r


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
    # minutes are reported, not gating: they are the harness's model (sim/server.py MINUTES, a minute per typed field), not a
    # person's time; they gate once calibrated against real recorded sessions (docs/CYCLE_WALK.md)
    return F


def stops_at(r):
    """the first step the journey fails, as a person would name it: where they stopped, else the first thing that was not
    right on the way, else the records, else the budget"""
    if r['stuck']: return f"stopped: {r['stuck']['step']} (expected {r['stuck']['expected']})"
    if r['soft']: return f"on the way: {r['soft'][0]['expected']}"
    bad = [g for g in r['grades'] if g['status'] != 'right']
    if bad: return f"in the records: {bad[0]['step']} {bad[0]['status']} ({bad[0]['detail'][:120]})"
    if r['taps'] > r['budget']: return f"over budget: {r['taps']} taps against {r['budget']}"
    return 'passes'


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


def tally(results, devices):
    """N of 10 per device: a journey counts on a device when it ran there and passed"""
    out = {}
    for d in devices:
        R = {r['journey']: r for r in results if r['device'] == d}
        out[d] = (sum(1 for j in TEN if j in R and R[j]['passed']), sum(1 for j in TEN if j in R))
    return out


def tally_line(t):
    return 'JOURNEYS ' + ' · '.join(f'{d} {n} of 10' + (f' ({m} walked)' if m != 10 else '') for d, (n, m) in t.items())


def write_report(results, danger, t_all, build, devices):
    os.makedirs(OUT, exist_ok=True)
    F = [f for r in results for f in failures_of(r)] + danger
    T = tally(results, devices)
    json.dump({'build': build, 'seconds': t_all, 'tally': T, 'results': results, 'danger': danger, 'failures': F}, open(os.path.join(OUT, 'report.json'), 'w'), indent=1)
    M = [f'# Cycle walk: the ten journeys of docs/JOURNEYS.md', '', f'Build {build}. Run time {t_all / 60:.1f} minutes. **{tally_line(T)}.**', '',
         '| Journey | Owner | Device | Taps (whose) | Budget | Minutes (modelled, not gating) | Budget | Passes | Where it stops | Records |', '|---|---|---|---|---|---|---|---|---|---|']
    for r in sorted(results, key=lambda r: (TEN.index(r['journey']) if r['journey'] in TEN else 99, r['device'])):
        whose = ', '.join(f'{u[2:]} {n}' for u, n in r['by'].items() if n) if len(r['by']) > 1 else ''
        bud = f"{r['budget']}" + ('' if r['budget_of'] == r['device'] else f" (the {r['budget_of']}'s)")
        M.append(f"| {r['journey']} {r['title']} | {r['uid']} | {r['device']} | {r['taps']}" + (f' ({whose})' if whose else '') +
                 f" | {bud} | {r['minutes']:.0f} modelled | {r['budget_min']} | {'yes' if r['passed'] else 'no'} | {r['stops_at'][:140]} | "
                 f"{', '.join(g['step'] + ' ' + g['status'] for g in r['grades'])} |")
    M += ['', '## Failures', ''] + [fmt_fail(f) for f in F]
    M += ['', '## What the walk did by hand (a person\'s way round, not the app\'s own path)', '']
    M += [f"- {r['journey']} {r['device']}: {n}" for r in results for n in r.get('notes') or []] or ['- nothing']
    M += ['', '## Trails (the last actions of each journey)', '']
    for r in results:
        M += [f"### {r['journey']} {r['device']}", '```'] + r['trail'] + ['```']
    open(os.path.join(OUT, 'report.md'), 'w').write('\n'.join(M) + '\n')
    return F


# ---------------------------------------------------------------------------------------------------- the walk's own units
def selftest():
    """no browser: the lint, the reader on fixture screens, the budgets and journeys against docs/JOURNEYS.md, the pass rule"""
    fails, n = [], [0]

    def check(ok, msg):
        n[0] += 1; print(('PASS ' if ok else 'FAIL ') + msg, flush=True)
        if not ok: fails.append(msg)
    check(not lint_self(), 'lint: the walk reaches the app only through the harness verbs')
    # docs/JOURNEYS.md's table: the ten journeys, their devices and budgets, and the walk's registry and BUDGET
    md = open(os.path.join(ROOT, 'docs', 'JOURNEYS.md'), encoding='utf-8').read()
    rows = {}
    for l in md.split('\n'):
        c = [x.strip() for x in l.strip().strip('|').split('|')]
        if len(c) >= 8 and re.match(r'^J\d+$', c[0]): rows[c[0]] = c
    check(sorted(rows, key=lambda j: int(j[1:])) == [f'J{i}' for i in range(1, 11)], f'JOURNEYS.md has the ten journeys ({", ".join(rows)})')
    check(TEN and sorted(TEN, key=lambda j: int(j[1:])) == sorted(rows, key=lambda j: int(j[1:])), f'the walk walks exactly JOURNEYS.md\'s ten ({", ".join(TEN)})')
    bad = []
    for j, c in rows.items():
        want = {}
        named = re.findall(r'phone|desktop', c[3].lower())   # "desktop and phone": both; "desktop, owner on the phone": the desktop
        both = bool(re.search(r'(phone|desktop) and (phone|desktop)', c[3].lower()))
        for dev, t, m in re.findall(r'(phone|desktop)?\s*(\d+)\s*/\s*(\d+)', c[4]):
            for d in ([dev] if dev else named if both else named[:1]): want[d] = (int(t), int(m))
        if BUDGET.get(j) != want: bad.append(f'{j}: walk {BUDGET.get(j)} vs JOURNEYS.md {want}')
    check(not bad, 'BUDGET is JOURNEYS.md\'s taps and minutes, on the devices it names' + (': ' + '; '.join(bad) if bad else ''))
    owner_of = {'Owner': 'u_owner', 'PM': 'u_alan', 'Procurement': 'u_chen', 'Billing': 'u_billing', 'Accounting and owner': 'u_controller'}
    reg = {J[0]: J for J in JOURNEYS}
    wrong_owner = [j for j, c in rows.items() if j in reg and owner_of.get(c[1]) != reg[j][1]]
    check(not wrong_owner, f'each journey is walked by JOURNEYS.md\'s owner ({wrong_owner or "all"})')
    steps = {s['id'] for s in BOOK['steps']}
    unknown = [f'{J[0]}:{s}' for J in JOURNEYS for s in J[5] if isinstance(s, str) and (s not in steps or not hasattr(CY.Cycle, 's_' + s))]
    check(not unknown and all(J[5] for J in JOURNEYS), f'every journey is graded on the records by referee steps that exist ({unknown or "all"})')
    check(all(J[3] in globals() for J in JOURNEYS), 'every journey\'s function exists')
    # the reader: exact labels first; a sheet that leaves the page usable
    sc = Screen('Thu Sep 3 10:00 · Billing (billing) · Invoice\n[1 input "This Period % — 1" ="0"] [2 input "This Period % — 10" ="0"] [3 input "This Period % — 11"]\n'
                '== Open on top ==\nNote\n[4 Save note]\n== Under it, still usable: Opportunity ==\n[5 Note]')
    check(sc.find('This Period % — 1', field=True).n == 1 and sc.find('This Period % — 10', field=True).n == 2, 'reader: an exact label wins over a longer one that starts the same')
    check([c.n for c in sc.actions('sheet')] == [4] and sc.sheet, 'reader: a floating sheet\'s own buttons are told from the page still usable under it')
    po = Screen('Fri Sep 4 13:57 · Chen Biron (coord, phone) · Orders\n[1 link Purchasing] ›FM-1\n[2 input "Search…"]\nPurchase Order FM-1\n[3 Receive All]\n'
                '== Toast ==\n[4] PO-2026-050 issued to Ferguson — $1,960\n[5 link Open]')
    check(po.row('PO-2026-050', after='Search') is None, 'reader: a toast that names a record is not that record\'s row')
    # the Costs table read as a PM reads it: a line committed over its budget cost is over, flagged or not
    costs = ('[32] Line | Flags | [33 CLIENT PRICE] | [34 BUDGET COST] | [35 ACTUAL TO DATE] | [36 SPENT % OF BUDGET] | [37 PROJECTED MARGIN] | [38 MARGIN %] | [39 BILLED %] | [40 COMMITTED]\n'
             'Framing lumber: supplyEST-2026-016 | — | $1,450 | $1,100 | — | — | $350 | 24% | 0% | $827\n'
             'Drywall & cement board: supplyEST-2026-016 | — | $2,450 | $1,800 | — | — | $650 | 27% | 0% | $2,169\n')
    check(over_lines(costs) == ['Drywall & cement board: supply $369 over'], f'reader: the Costs table\'s columns name the line over budget ({over_lines(costs)})')
    # the pass rule and where a journey stops
    base = {'journey': 'J8', 'device': 'desktop', 'taps': 10, 'budget': 12, 'minutes': 5.0, 'budget_min': 6, 'stuck': None, 'soft': [], 'grades': [{'step': 'C30', 'status': 'right', 'detail': ''}]}
    check(not failures_of(base) and stops_at(base) == 'passes', 'pass rule: no stop, no failed expectation, the records right and the budget kept is a pass')
    over = dict(base, minutes=70.0)
    check(not failures_of(over) and stops_at(over) == 'passes', 'pass rule: modelled minutes over the budget are reported, never a failure (not calibrated yet)')
    taps = dict(base, taps=13)
    check(failures_of(taps) and stops_at(taps).startswith('over budget: 13 taps'), 'pass rule: over the tap budget fails')
    rec = dict(base, grades=[{'step': 'C31', 'status': 'not done', 'detail': 'no payment yet'}])
    check(failures_of(rec) and 'C31' in stops_at(rec), 'pass rule: a record not right fails, and the report names it')
    st = dict(base, stuck={'step': 'match the Ashbys\' transfer', 'expected': 'a Match on the bank line'}, taps=40)
    check(stops_at(st).startswith('stopped: match') and not any(f['kind'] == 'taps' for f in failures_of(st)), 'pass rule: a stop names where, and its taps are not also blamed on the budget')
    soft = dict(base, soft=[{'expected': 'a Deposit Invoice from the signed contract', 'journey': 'J8', 'device': 'desktop', 'step': ''}])
    check(failures_of(soft) and stops_at(soft).startswith('on the way: a Deposit Invoice'), 'pass rule: a failed expectation on the way fails the journey (never a pass on a broken step)')
    T = tally([dict(base, journey='J1', passed=True), dict(base, journey='J2', passed=False), dict(base, journey='X1', passed=True)], ['desktop'])
    check(T['desktop'] == (1, 2) and tally_line(T) == 'JOURNEYS desktop 1 of 10 (2 walked)', f'tally: N of 10 counts the ten only, per device ({tally_line(T)})')
    print(f"\n{n[0] - len(fails)}/{n[0]} checks passed (the walk's units)")
    return 1 if fails else 0


def desktop_chain(a, pinned, stamp, resume, first, last, only, devices, results, worlds):
    """the chain on the desktop, in the book's days: a checkpoint of the company before each journey (each phone journey
    starts from it), each journey walked and graded where the desktop is asked for, the dangerous buttons at both ends"""
    desk = World(f'cw_{stamp}_desktop', pinned, resume_from=resume).start(); worlds.append(desk)
    print(f'world {desk.run} up in {desk.boot_s}s', flush=True)
    # the walk's world: the cycle book, the coordinator receives the trucks herself, the controller sits, the bank feeds
    desk.admin('cycle', on=True, play=['u_controller', 'u_angel:receive'], feed=True)
    slot, checkpoints, danger = (desk.world_state().get('slot') or 'morning') if resume else 'morning', {}, []
    try:
        if not a.no_danger and not resume:   # the morning's Today, before anyone has worked it (Pilot 3 met Draft the Renewal here at 7:30)
            desk.admin('world', slot='morning', watchers=True)
            danger += danger_walk(desk, devices, screens={u: [('Today',)] for u in DANGER_ROLES}, hold=False, slot='morning')
        for i, J in enumerate(JOURNEYS[:last + 1]):
            if i < first: continue
            if not (resume and i == first): slot = world_before(desk, J[4], slot)
            checkpoints[J[0]] = (desk.checkpoint(J[0]), slot)
            r = run_journey(desk, J, 'desktop', slot)   # the chain goes on for the phone's checkpoints even where only the phone is asked for
            if 'desktop' in devices and (not only or J[0] in only):
                results.append(r)
                print(f"{J[0]} desktop: {r['taps']} taps, {r['minutes']} min modelled, {r['seconds']}s, " + ('PASS' if r['passed'] else r['stops_at'][:160]) + ' · ' +
                      ', '.join(g['step'] + ' ' + g['status'] for g in r['grades']), flush=True)
            slot = r['slot']
        if not a.no_danger: danger += danger_walk(desk, devices)
    finally:
        desk.stop()
    return checkpoints, danger


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rereport', action='store_true', help='apply the pass rule again to review/cycle_walk/report.json and rewrite the report (no browser)')
    ap.add_argument('--only', default='', help='journeys to run, e.g. J2 or J1,J2 (the chain before them runs on the desktop)')
    ap.add_argument('--devices', default='desktop,phone')
    ap.add_argument('--no-danger', action='store_true')
    ap.add_argument('--attach', default='', help='a running world (development: no world steps, no checkpoints)')
    ap.add_argument('--danger-only', action='store_true', help='with --attach: only the dangerous-button walk')
    ap.add_argument('--from', dest='start', default='', help='<run>:<J>: start the desktop chain from that kept checkpoint (development)')
    ap.add_argument('--keep', action='store_true', help='leave the worlds\' folders in sim/runs')
    ap.add_argument('--checkpoints', default='', help='<run>: the phone journeys from that kept desktop run\'s checkpoints, no desktop chain (development)')
    ap.add_argument('--selftest', action='store_true', help='the walk\'s own units, no browser')
    a = ap.parse_args()
    if a.selftest: return selftest()
    if a.rereport:   # the pass rule changed: apply it again to the kept results (same measurements, no rerun)
        old = json.load(open(os.path.join(OUT, 'report.json'), encoding='utf-8'))
        results = old['results']
        for r in results: r['passed'], r['stops_at'] = not failures_of(r), stops_at(r)
        devices = [d for d in DEVICES if any(r['device'] == d for r in results)]
        F = write_report(results, old['danger'], old['seconds'], old['build'], devices)
        print(tally_line(tally(results, devices)))
        print(f"CYCLE WALK {sum(len(r['grades']) + 2 for r in results) + len(old['danger'])} checks · {len(F)} failed (re-reported from build {old['build']})")
        return 1 if F else 0
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
    first = 0
    results, worlds = [], []
    if a.attach and a.danger_only:
        w = World(a.attach, pinned, attach=True)
        danger = danger_walk(w, devices)
        F = write_report([], danger, round(time.time() - t_all), build, devices)
        os.remove(pinned)
        for f in F: print('FAIL', fmt_fail(f)[2:].split('\n')[0][:400])
        print(f"CYCLE WALK {len(danger)} danger findings"); return 1 if F else 0
    if a.attach:
        w = World(a.attach, pinned, attach=True); slot = w.world_state().get('slot') or 'morning'
        for J in JOURNEYS[:last + 1]:
            if only and J[0] not in only: continue
            for dev in devices:
                r = run_journey(w, J, dev, slot); results.append(r); print(json.dumps({k: r[k] for k in ('journey', 'device', 'taps', 'minutes', 'stops_at', 'grades')}, indent=1)[:3000], flush=True)
        F = write_report(results, [], round(time.time() - t_all), build, devices)
        os.remove(pinned)
        print(tally_line(tally(results, devices)))
        print(f"CYCLE WALK {sum(len(r['grades']) + 1 for r in results)} checks · {len(F)} failed"); return 1 if F else 0
    resume, danger = None, []
    if a.checkpoints:   # development: the phone journeys from a kept desktop run's checkpoints, no desktop chain
        checkpoints = {}
        for J in JOURNEYS:
            ck = os.path.join(RUNS, f'{a.checkpoints}.ck', J[0])
            if os.path.isdir(ck): checkpoints[J[0]] = (ck, json.load(open(os.path.join(ck, 'world.json'))).get('slot') or 'morning')
        devices = ['phone']
    elif a.start:
        run0, jid0 = a.start.split(':')
        resume = os.path.join(RUNS, f'{run0}.ck', jid0)
        if not os.path.isdir(resume): raise SystemExit(f'no checkpoint {resume} (run with --keep first)')
        first = next(i for i, J in enumerate(JOURNEYS) if J[0] == jid0)
    if not a.checkpoints: checkpoints, danger = desktop_chain(a, pinned, stamp, resume, first, last, only, devices, results, worlds)
    if 'phone' in devices:
        for i, J in enumerate(JOURNEYS[:last + 1]):
            if i < first or (only and J[0] not in only) or J[0] not in checkpoints: continue
            ck, slot = checkpoints[J[0]]
            ph = World(f'cw_{stamp}_phone_{J[0]}', pinned, resume_from=ck).start(); worlds.append(ph)
            try:
                r = run_journey(ph, J, 'phone', slot); results.append(r)
                print(f"{J[0]} phone: {r['taps']} taps, {r['minutes']} min modelled, {r['seconds']}s, " + ('PASS' if r['passed'] else r['stops_at'][:160]) + ' · ' +
                      ', '.join(g['step'] + ' ' + g['status'] for g in r['grades']), flush=True)
            finally:
                ph.stop()
    results.sort(key=lambda r: (TEN.index(r['journey']) if r['journey'] in TEN else 99, r['device']))
    F = write_report(results, danger, round(time.time() - t_all), build, devices)
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
    werr = [f"{r['journey']} {r['device']}" for r in results if (r['stuck'] or {}).get('walk_error')]
    if werr: print(f"WALK ERRORS (the walk's own faults; those journeys are not measured): {', '.join(werr)}")
    print(tally_line(tally(results, devices)))
    print(f"CYCLE WALK {n} checks · {len(F)} failed ({round((time.time() - t_all) / 60, 1)} minutes)")
    return 1 if F else 0


if __name__ == '__main__':
    sys.exit(main())
