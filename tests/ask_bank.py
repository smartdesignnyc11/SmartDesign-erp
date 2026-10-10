"""The Ask question bank (BACKLOG §0 item 3).

Every question is asked through paAsk() in a fresh signed-in state (Ask thread, carry-over context and
cached answers cleared, then signIn(role); render()). Ground truth is a JS expression evaluated in the page
from DB or from the function the screen renders from (needs(), mApprovals(), readyToBill(), companyPL(),
jobFin(), apOpenBills(), b2Facts(), ...). It is never taken from paAsk or its intent helpers, and never
typed by hand.

Checks:
  number   the headline contains the number, formatted like the app ($12,345 / 12,345 / 12.3; "pct" adds %).
           A truth of 0 also accepts "no", "none", "nothing".
  names    headline + work rows mention every listed name.
  contains headline + work rows contain every listed string.
  any      headline + work rows contain at least one listed string.
  date     headline + work rows show the date (12/15, Dec 15, December 15, Tue, Dec 15, 2026-12-15).
A refusal ("I have nothing called…", "Nothing in the records matches…") fails unless refuse_ok.
Optional fields:
  setup    JS run in the page before the question (connect a Demo Workspace, run a close). Questions with the
           same setup share one fresh browser, in order; `isolate: true` gives a question a browser of its own.
  before   questions asked first in the same thread, with no reset between (carry-over, pronouns, memory).
  post     JS evaluated after the answer; it must be truthy (a stored memo, a task's date, a draft's cc).
  absent   JS list of strings the answer must not show (another client, a staff name for a client's).
  maxMs    the answer must come back within this many milliseconds (a slow reader must not hang the thread).
  noread   words that must be taken as typed: the answer may not say it read one of them as another word
           ("Amex" is a card, not Alex; "aging" is not "again").
Separately reported, not a failure: a non-refusal answer shows how it was read (interp, readAs,
"I ran:" or "I read this as").

  python3 ask_bank.py                    # tune + held-out, prints TUNE x/y  HELDOUT a/b
  python3 ask_bank.py --set tune -v      # failures with headline vs truth
  python3 ask_bank.py --id F06 --tag typo --json
  python3 ask_bank.py --truths           # print every truth value and sanity-check against HANDOFF.md
"""
import argparse, asyncio, json, os, re, sys
from collections import Counter, defaultdict
from harness import *

HERE = os.path.dirname(os.path.abspath(__file__))
SETS = {'tune': os.path.join(HERE, 'ask_bank_tune.json'), 'heldout': os.path.join(HERE, 'ask_bank_heldout.json'),
        'heldout2': os.path.join(HERE, 'ask_bank_heldout2.json')}

# Raw-DB helpers for truth expressions. Test code, not app code: it reads DB and screen functions only.
HELPERS = r"""
window.__AB = (() => {
  const lc = s => String(s || '').toLowerCase(), r2 = x => Math.round(x * 100) / 100, H = {};
  H.P = n => (DB.projects || []).find(p => lc(p.project.name).includes(lc(n)));
  H.C = n => (DB.clients || []).find(c => lc(c.name).includes(lc(n)));
  H.E = n => (DB.employees || []).find(e => lc(e.name) === lc(n)) || (DB.employees || []).find(e => lc(e.name).includes(lc(n)));
  H.short = p => String(p.project.name).replace(/ —.*$/, '');
  H.sum = (L, f) => r2((L || []).reduce((a, x) => a + (+f(x) || 0), 0));
  H.invs = () => (DB.clients || []).flatMap(c => (c.invoices || []).map(d => {
    const total = docTotal(d).total, paid = H.sum((c.payments || []).filter(x => x.invoiceId === d.id), x => x.amount);
    return { c, d, total, paid, open: !['paid', 'void'].includes(d.status), bal: r2(total - paid) };
  }));
  H.cos = () => (DB.clients || []).flatMap(c => (c.changeOrders || []).map(d => ({ c, d, total: docTotal(d).total })));
  H.spendTx = (re, from, to) => (DB.txns || []).filter(t => t.amt < 0 && !['cc-payment', 'transfer'].includes(t.cat) && re.test((t.desc || '') + ' ' + (t.vendor || ''))
    && (!from || t.date >= from) && (!to || t.date <= to));
  H.spend = (re, from, to) => H.sum(H.spendTx(re, from, to), t => -t.amt);
  H.hrs = (name, from, to) => { const e = H.E(name); return H.sum((DB.time || []).filter(t => t.empId === e.id && t.date >= from && t.date <= to), hoursOf); };
  H.yday = () => iso(addDays(parse(today()), -1));
  H.me = () => currentUser();
  H.myProjects = () => (DB.projects || []).filter(p => p.clientId === (currentUser() || {}).clientId);
  H.openDec = p => (p.decisions || []).filter(d => d.status === 'open');
  return H;
})();
"""

# Clears everything Ask carries between questions: the per-user thread and context (DB.asst[uid].ctx holds
# the pronoun "who" and the last "row"), the live answer (paNow), steps, and the Chief of Staff cache.
RESET = r"""
() => {
  try { Object.values(DB.asst || {}).forEach(A => { if (A && typeof A === 'object') { A.thread = []; delete A.ctx; } }); } catch (e) {}
  try { paNow = null; } catch (e) {}
  try { paSteps = []; } catch (e) {}
  try { paBusy = false; } catch (e) {}
  try { csLast = null; csAsk = ''; csAskHits = null; csAnsNow = null; } catch (e) {}
  try { briefAsk = ''; } catch (e) {}
}
"""

ASK_ONE = r"""
async ({ e, reset }) => {
  const R = eval(reset);
  R(); signIn(e.role); view = 'home'; render();
  let truth = null, terr = '';
  try { truth = await new Function('H', `return (async () => (${e.truth}))()`)(window.__AB); }
  catch (err) { terr = String(err && err.message || err); }
  let absent = [];
  if (e.absent) { try { absent = await new Function('H', `return (async () => (${e.absent}))()`)(window.__AB); } catch (err) { terr = 'absent: ' + String(err && err.message || err); } }
  let dates = [];
  if (e.check === 'date' && !terr) {
    const L = (Array.isArray(truth) ? truth : [truth]).filter(Boolean);
    dates = L.map(d => {
      const D = new Date(d + 'T12:00:00'), out = [d];
      try { out.push(fmt(d)); } catch (x) {}
      try { out.push(fmtL(d)); } catch (x) {}
      out.push(D.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
      out.push(D.toLocaleDateString('en-US', { month: 'long', day: 'numeric' }));
      out.push(`${D.getMonth() + 1}/${D.getDate()}`);
      return [...new Set(out.filter(Boolean))];
    });
  }
  R();
  for (const b of (e.before || [])) { try { await Promise.resolve(paAsk(b)); } catch (err) {} }
  let a = null, aerr = '', ms = 0;
  const t0 = performance.now();
  try { a = await Promise.resolve(paAsk(e.q)); } catch (err) { aerr = String(err && err.message || err); }
  ms = Math.round(performance.now() - t0);
  let post = null;
  if (e.post) { try { post = !!(await new Function('H', `return (async () => (${e.post}))()`)(window.__AB)); } catch (err) { post = false; terr = 'post: ' + String(err && err.message || err); } }
  R();
  a = a || {};
  const str = x => typeof x === 'string' ? x : x == null ? '' : JSON.stringify(x);
  return { truth, terr, dates, absent, aerr, headline: str(a.headline), note: str(a.note), work: (a.work || []).map(str),
           kind: str(a.kind), interp: str(a.interp), readAs: str(a.readAs), ms, post };
}
"""

REFUSAL = re.compile(r"I have nothing called|Nothing in the records matches|not part of what your account|so I hold no|"
                     r"I do not hold|I don't hold|I cannot (?:answer|tell|see)|I can't (?:answer|tell|see)|"
                     r"not something I (?:hold|keep|track)|I have no record of|I could not find|I couldn't find|I cannot find|"
                     r"sits outside what your account can see|I can't answer that", re.I)
# The keyword-search fallback: a count of records, not an answer to the question.
GENERIC = re.compile(r"^\d+ records? across \d+ modules?|^\d+ records?\b|^The earliest record is", re.I)
# Dates and clock times are stripped before numbers are matched, so "Sep 9" never passes for 9.
DATES = re.compile(r"\b(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*,? |\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}(?:, \d{4})?|"
                   r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b|\b\d{1,2}:\d{2}\b", re.I)
ZERO = re.compile(r"\b(nothing|none|nobody|no one|zero)\b|\$0(?![\d.,])|(?<![\d.,$])0(?![\d.,%])|^no\b|"
                  r"\bno [a-z][a-z -]{0,30}\b(is|are|was|were|has|have|needs?|to)\b|\bnot (any|one)\b", re.I)
SHOWN = re.compile(r"I ran:|I read this as|Read as:", re.I)

def norm(s):
    s = str(s).lower()
    s = s.replace('−', '-').replace('–', '-').replace('—', '-').replace('’', "'").replace(' ', ' ')
    return re.sub(r'\s+', ' ', s)

def num_forms(v, pct=False):
    v = abs(float(v))
    forms = {f"{round(v):,}"}
    if abs(v - round(v)) > 0.004:
        forms |= {f"{v:,.2f}", f"{v:,.1f}"}
    if pct:
        return [f + '%' for f in forms] + [f + ' %' for f in forms] + [f + ' percent' for f in forms]
    return sorted(forms)

def has_num(text, v, pct=False):
    t = DATES.sub(' ', norm(text))
    if float(v) == 0 and not pct and ZERO.search(t):
        return True
    for f in num_forms(v, pct):
        if re.search(r'(?<![\d.,])' + re.escape(f) + r'(?![\d]|[.,]\d)', t):
            return True
    return False

def judge(e, r):
    """Returns (ok, why, refused)."""
    head = r['headline']
    body = ' '.join([head] + r['work'])
    refused = bool(REFUSAL.search(head))
    if r['terr']:
        return False, f"TRUTH ERROR {r['terr']}", refused
    if r['aerr']:
        return False, f"paAsk threw {r['aerr']}", refused
    if refused and not e.get('refuse_ok'):
        return False, 'refused', refused
    if GENERIC.search(head.strip()):
        return False, 'generic record search, not an answer', refused
    leak = [s for s in (r.get('absent') or []) if s and norm(s) in norm(' '.join([head, r['note']] + r['work']))]
    if leak:
        return False, f"shows records outside the asker's own jobs: {leak}", refused
    if e.get('maxMs') and r.get('ms', 0) > e['maxMs']:
        return False, f"took {r['ms']} ms (limit {e['maxMs']})", refused
    said = norm(' '.join([r['interp'], r['readAs'], head, r['note']]))
    bad = [w for w in (e.get('noread') or []) if re.search(r'"' + re.escape(norm(w)) + r'" as\b|\b' + re.escape(norm(w)) + r'" as\b|read ' + re.escape(norm(w)) + r' as\b', said)]
    if bad:
        return False, f"corrected a word it should have taken as typed: {bad}", refused
    if e.get('post') and not r.get('post'):
        return False, 'post check failed', refused
    t, ck = r['truth'], e['check']
    if ck == 'number':
        vals = t if isinstance(t, list) else [t]
        miss = [v for v in vals if not has_num(head, v, e.get('fmt') == 'pct')]
        return (not miss), (f"headline lacks {miss}" if miss else ''), refused
    if ck in ('names', 'contains'):
        if not t:  # an empty truth list means the right answer is "none"
            return has_num(head, 0), ('' if has_num(head, 0) else 'expected a "none" answer'), refused
        miss = [s for s in t if norm(s) not in norm(body)]
        return (not miss), (f"missing {miss}" if miss else ''), refused
    if ck == 'any':
        hit = any(norm(s) in norm(body) for s in t)
        return hit, ('' if hit else f"none of {t}"), refused
    if ck == 'date':
        hit = any(any(norm(f) in norm(body) for f in forms) for forms in r['dates'])
        return hit, ('' if hit else f"no date among {r['dates']}"), refused
    return False, f"unknown check {ck}", refused

def load(which):
    out = []
    for s in (['tune', 'heldout'] if which == 'all' else [which]):
        if not os.path.exists(SETS[s]): continue
        for e in json.load(open(SETS[s]))['questions']:
            out.append(dict(e, _set=s))
    return out

async def fresh_page(p):
    b, pg, errs = await open_app(p)
    await pg.evaluate(HELPERS)
    return b, pg, errs

async def run(qs):
    res = []
    plain = [x for x in qs if not x.get('setup') and not x.get('isolate')]
    staged = [x for x in qs if x.get('setup') or x.get('isolate')]
    staged.sort(key=lambda x: (x.get('setup') or '', bool(x.get('isolate'))))  # stable: same setup together, in order
    async with async_playwright() as p:
        b, pg, errs = await fresh_page(p)
        cur = None  # the setup the open browser was prepared with
        for e in plain + staged:
            key = (e.get('setup') or '') + ('|' + e['id'] if e.get('isolate') else '')
            if (e.get('setup') or e.get('isolate')) and key != cur:  # a mutating setup gets its own browser
                await b.close()
                b, pg, errs = await fresh_page(p)
                if e.get('setup'): await pg.evaluate(e['setup'])
                cur = key
            r = await pg.evaluate(ASK_ONE, {'e': {k: e.get(k) for k in ('role', 'q', 'truth', 'check', 'absent', 'before', 'post')}, 'reset': RESET})
            ok, why, refused = judge(e, r)
            shown = bool(r['interp'] or r['readAs'] or SHOWN.search(' '.join([r['note'], r['headline']] + r['work'])))
            res.append(dict(id=e['id'], set=e['_set'], role=e['role'], q=e['q'], tags=e['tags'], ok=ok, why=why,
                            refused=refused, shown=shown, truth=r['truth'], headline=r['headline'], work=r['work'][:6],
                            kind=r['kind'], terr=r['terr'], ms=r.get('ms')))
        await b.close()
    return res

# HANDOFF.md figures (app day 2026-09-03). A truth that disagrees with these is wrong, not the app.
SANITY = {  # question text -> HANDOFF.md figure
    'how much cash do we have': 184231, 'How is cash?': 184231, "what's our AR": 92265, 'what should we invoice today': 20980,
    'What could we invoice today?': 20980, 'What can I invoice today?': 20980, 'How is cash, truly?': -4151,
    'what is safe to spend': -4151, 'how much is unmatched in the bank': 75272, 'what is the backlog': 582941,
    'net income year to date': -5330, 'what was revenue this year': 142759, 'what do we owe vendors': 0,
    'how much payroll is past due': 16040, 'how much is WIP over billed': 156274}  # HANDOFF.md after truthpct
# BACKLOG 1.3: the screens' Approvals counts. Since DELEGATION (one item, one queue) the owner holds WW-2026-118,
# the brain's change and 8 lessons; the PM the submitted bill, crew hours, site questions, decisions, a meeting and
# the submittal; billing and the controller own no approval kind (they were shown everyone's decisions and hours).
WAITING = {'u_owner': 10, 'u_alan': 16, 'u_billing': 0, 'u_controller': 0}

def sanity(res):
    bad = []
    for r in res:
        want = SANITY.get(r['q'])
        if re.match(r"(what is|what's|whats) waiting on me", r['q'], re.I):
            want = WAITING.get(r['role'])
        if want is not None and (not isinstance(r['truth'], (int, float)) or round(r['truth']) != want):
            bad.append(f"{r['id']} truth {r['truth']} != HANDOFF {want}")
        t = r['truth']
        if r['terr']: bad.append(f"{r['id']} truth error {r['terr']}")
        elif t is None or (isinstance(t, float) and t != t): bad.append(f"{r['id']} truth is empty")
        elif isinstance(t, list) and not t: print(f"note {r['id']}: empty truth list, expects a 'none' answer")
        elif isinstance(t, list) and any(x in (None, '') for x in t): bad.append(f"{r['id']} truth list empty or has blanks: {t}")
    return bad

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', default='all', choices=['tune', 'heldout', 'heldout2', 'all'])
    ap.add_argument('--id', action='append', help='question id (repeatable)')
    ap.add_argument('--tag', action='append', help='only questions with this tag (repeatable)')
    ap.add_argument('--json', action='store_true', help='print results as JSON')
    ap.add_argument('-v', action='store_true', help='print failures with headline vs truth')
    ap.add_argument('--truths', action='store_true', help='print every truth value and sanity-check them')
    a = ap.parse_args()
    qs = load(a.set)
    if a.id: qs = [e for e in qs if e['id'] in a.id]
    if a.tag: qs = [e for e in qs if set(a.tag) & set(e['tags'])]
    if not qs: sys.exit('no questions match')
    res = asyncio.run(run(qs))
    order = {e['id']: i for i, e in enumerate(qs)}
    res.sort(key=lambda r: order[r['id']])
    if a.truths:
        for r in res:
            print(f"{r['id']:5} {r['role']:12} {r['q'][:58]:58} = {json.dumps(r['truth'], ensure_ascii=False)[:120]}{'  ERR ' + r['terr'] if r['terr'] else ''}")
        bad = sanity(res)
        print('\n'.join(['TRUTH ' + b for b in bad]) or 'TRUTHS OK: every truth evaluated, and HANDOFF figures agree')
        sys.exit(1 if bad else 0)
    if a.json:
        print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    else:
        for r in res:
            if not r['ok'] and a.v:
                print(f"FAIL {r['id']} [{r['set']}] {r['role']} \"{r['q']}\" ({r['why']})\n     headline: {r['headline'][:220]}\n     truth:    {json.dumps(r['truth'], ensure_ascii=False)[:220]}")
        by = defaultdict(lambda: [0, 0])
        for r in res:
            by[r['set']][0] += r['ok']; by[r['set']][1] += 1
        nr = [r for r in res if not r['refused']]
        fails = Counter(t for r in res if not r['ok'] for t in r['tags'])
        print('failures by tag:', ', '.join(f'{t} {n}' for t, n in fails.most_common()) or 'none')
        print(f"shows how it read the question: {sum(r['shown'] for r in nr)}/{len(nr)} non-refusal answers;"
              f" refusals {len(res) - len(nr)}/{len(res)}")
        print('  '.join(f"{s.upper()} {by[s][0]}/{by[s][1]}" for s in ('tune', 'heldout', 'heldout2') if s in by))
    sys.exit(0 if all(r['ok'] for r in res) else 1)

if __name__ == '__main__':
    main()
