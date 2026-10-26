"""sim/voicer.py: the world answers like people (Alan 10-26). Invented parties only; no real mail ever reaches it.

The world's rules (sim/world.py) decide WHO answers, WHEN, and the FACTS (prices, dates, quantities, numbers) and the
money that follows. Before this, they also wrote the words: one template per kind, so every vendor sounded the same
and every reply was complete, on time and in the firm's own layout. The voicer writes the words a real person in that
seat would send, through the live AI door (/api/ai, the same SIM_AI_TOKEN_FILE path the assistant uses), and keeps the
rule's facts exactly:
- every fact in the template (a $ amount, an ISO date, a document number, a quantity with its unit, a time) must be in
  the voiced text, and the voiced text may carry no $ amount, date or document number the template did not;
- on any failure (no token, the door down, a fact dropped or invented, an empty answer) the template is sent and the
  ledger (world/voice.jsonl, and "World voice" in ledger.md) says which and why.

Real vendors vary, so each reply gets a style, seeded per run and reply id (deterministic per seed; the words are kept
in world/answers/<id>.txt, so a resumed run sends the same words):
  plain             the person's own voice
  terse             two lines from a phone
  question_back     the facts, then one question a real person in that seat would ask back
  different_format  the same facts in another layout (a list instead of a table, a sentence instead of a list)
  late              sent one slot later than the rules said (the words are plain)
  partial           the facts in two mails: the first now ("the rest to follow"), the rest one slot later
A planted quote keeps its book format (the table, the PDF, the prose, the per-box price are the journey's test), so it
never gets different_format; a reply with an attachment never gets partial (the attachment carries the facts).

    python3 sim/voicer.py <pending.json> [--style S] [--seed N]   voice one pending reply and print it with its fact check
"""
import hashlib, json, os, random, re, ssl, sys, time, urllib.error, urllib.request

AI_URL = os.environ.get('SIM_AI_URL', 'https://smartdesigns-erp.netlify.app').rstrip('/')
TIER = os.environ.get('SIM_VOICE_TIER', 'small')
STYLES = [('plain', 30), ('terse', 15), ('question_back', 15), ('different_format', 15), ('late', 12), ('partial', 13)]
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

MONEY = re.compile(r'\$\s?\d[\d,]*(?:\.\d{1,2})?')
ISO = re.compile(r'\b20\d\d-\d\d-\d\d\b')
DOCNO = re.compile(r'\b(?:PO|RFQ|EST|INV|CO|BILL)-\d{4}-\d+\b|\b[A-Z]{2,4}-\d{3,6}\b')
QTY = re.compile(r'\b\d+(?:\.\d+)?\s?(?:sf|ls|ea|lf|pcs?|sheets?|boxes|box|rolls?|working days|days)\b', re.I)
TIME = re.compile(r'\b\d{1,2}(?::\d\d)?\s?(?:am|pm)\b|\bbetween \d{1,2} and \d{1,2}\b', re.I)
DAYWORD = re.compile(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b|\bthe \d{1,2}(?:st|nd|rd|th)\b')


# ---------------------------------------------------------------------------------------------------- the facts
def facts(text, lines=False):
    """the facts a template reply carries, in reading order, each once (lines: with the line each is on)"""
    hits = sorted(((m.start(), m.group(0).strip()) for rx in (MONEY, ISO, DOCNO, QTY, TIME, DAYWORD) for m in rx.finditer(text or '')), key=lambda x: (x[0], -len(x[1])))
    out, at = [], []
    for pos, f in hits:
        if f not in out and not any(f in o for o in out): out.append(f); at.append((text or '').count('\n', 0, pos))
    if lines: return list(zip(out, at))
    if not out and (text or '').strip():   # a decision with no figures ("Move it, please", "Approved."): its opening words are the fact
        out.append(' '.join(re.split(r'[:,.;]', text.strip())[0].split()[:4]))
    return out


def _num(s): return float(re.sub(r'[^\d.]', '', s) or 0)


def _date_forms(iso):
    y, m, d = map(int, iso.split('-'))
    mon = MONTHS[m - 1]
    return [iso, f'{mon} {d}', f'{mon[:3]} {d}', f'{mon[:3]}. {d}', f'{m}/{d}', f'{m:02d}/{d:02d}', f'{d} {mon}']


def kept(fact, text):
    """is this fact in the text, as a person might write it (1,234.50 or 1234.50; Sept 10 for 2026-09-10)"""
    t = text or ''
    if MONEY.fullmatch(fact):
        v = _num(fact)
        return any(abs(_num(x) - v) < 0.005 for x in re.findall(r'\$?\s?\d[\d,]*(?:\.\d{1,2})?', t))
    if ISO.fullmatch(fact):
        low = t.lower().replace('sept ', 'sep ')
        return any(f.lower() in low for f in _date_forms(fact))
    norm = lambda s: re.sub(r'\s+', ' ', s.lower()).replace(' ', '')
    return norm(fact) in norm(t)


def check(template, voiced, parts=None):
    """(ok, missing facts, invented facts): every fact of the template is in the voiced words (across the parts of a
    partial reply), and no $ amount, date or document number appears that the template did not have"""
    text = voiced if parts is None else '\n'.join(parts)
    F = facts(template)
    missing = [f for f in F if not kept(f, text)]
    tmoney = [_num(x) for x in MONEY.findall(template or '')]
    invented = [x for x in MONEY.findall(text) if not any(abs(_num(x) - v) < 0.005 for v in tmoney)]
    invented += [x for x in ISO.findall(text) if x not in (template or '')]
    invented += [x for x in DOCNO.findall(text) if x not in (template or '')]
    return (not missing and not invented and bool((text or '').strip())), missing, invented


# ---------------------------------------------------------------------------------------------------- the style
def style_for(rec, seed):
    """a style for this reply, the same for the same run seed and reply id"""
    r = random.Random(int(hashlib.sha1(f'{seed}:voice:{rec.get("id")}'.encode()).hexdigest()[:12], 16))
    party = rec.get('party') or {}
    banned = set()
    if isinstance(party, dict) and party.get('quotes'): banned.add('different_format')   # the book's format is the test
    if rec.get('att'): banned.add('partial')
    if len(facts(rec.get('template_reply') or '')) < 2: banned.add('partial')
    S = [(s, w) for s, w in STYLES if s not in banned]
    x = r.uniform(0, sum(w for _, w in S))
    for s, w in S:
        x -= w
        if x <= 0: return s
    return S[-1][0]


GUIDE = {
    'plain': 'Write it the way this person really writes: their own words, their own greeting and sign-off.',
    'terse': 'Write it as two or three short lines tapped out on a phone between jobs. No greeting beyond a name.',
    'question_back': 'Give every fact, then ask one short question back that a real person in this seat would ask '
                     '(a delivery window, an access detail, a spec, whether a substitute is acceptable). Do not answer it yourself.',
    'different_format': 'Give the same facts in a different layout from the template: if it is a table, write a list or '
                        'sentences; if it is sentences, write a short list.',
    'late': 'Write it the way this person really writes. It goes out later than promised; you may open with a one-line apology.',
    'partial': 'Split it into two mails. The FIRST carries the facts marked FIRST and says the rest follows shortly. The '
               'SECOND carries the facts marked SECOND. Reply with JSON only: {"first": "...", "second": "..."}.',
}


def prompt(rec, style, split=None):
    party = rec.get('party') or {}
    name = party.get('name', '') if isinstance(party, dict) else str(party)
    contact = party.get('contact', '') if isinstance(party, dict) else ''
    persona = rec.get('persona') or (party.get('voice', '') if isinstance(party, dict) else '')
    F = facts(rec.get('template_reply') or '')
    if split:
        fl = '\n'.join(f'- FIRST: {f}' for f in split[0]) + '\n' + '\n'.join(f'- SECOND: {f}' for f in split[1])
    else:
        fl = '\n'.join(f'- {f}' for f in F) or '- (no figures: keep its meaning)'
    system = ('You write one email as an outside party replying to a design-build firm in Brooklyn. It is a simulation with '
              'invented people. Write only the email body, no subject line, no notes about what you did. House rules: plain, '
              'specific, no exclamation marks. Copy every fact below exactly as written (the same digits, the same date, the '
              'same document number). Do not add any price, date, quantity, document number or term that is not in the '
              'facts or the template. Keep any mistake in the template as it is (a wrong price stays wrong): it is theirs.')
    user = (f"You are {contact + ' at ' if contact else ''}{name}. {persona}\n\n"
            f"The firm wrote to you:\n---\n{(rec.get('their_message') or '')[:1500]}\n---\n\n"
            f"What you are replying, as the plain template (its facts are what count):\n---\n{rec.get('template_reply') or ''}\n---\n\n"
            f"The facts to keep exactly:\n{fl}\n\nStyle: {GUIDE[style]}")
    return system, user


def call_ai(system, user, max_tokens=900):
    f = os.environ.get('SIM_AI_TOKEN_FILE', '')
    tok = open(f).read().strip() if f and os.path.exists(f) else os.environ.get('SIM_AI_TOKEN', '').strip()
    if not tok: raise RuntimeError('no session token (SIM_AI_TOKEN_FILE)')
    ca = os.environ.get('SSL_CERT_FILE') or os.environ.get('REQUESTS_CA_BUNDLE')
    ctx = ssl.create_default_context(cafile=ca) if ca and os.path.exists(ca) else ssl.create_default_context()
    body = {'tier': TIER, 'max_tokens': max_tokens, 'system': system, 'messages': [{'role': 'user', 'content': user}]}
    req = urllib.request.Request(AI_URL + '/api/ai', data=json.dumps(body).encode(), method='POST',
                                 headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tok})
    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as r: j = json.loads(r.read().decode().strip())
    except urllib.error.HTTPError as e: raise RuntimeError(f'the AI door answered {e.code}')
    if j.get('type') == 'error': raise RuntimeError('the model: ' + str((j.get('error') or {}).get('message', ''))[:120])
    text = ''.join(b.get('text', '') for b in j.get('content') or [] if b.get('type') == 'text').strip()
    u = j.get('usage') or {}
    return text, {'model': j.get('model', ''), 'in': (u.get('input_tokens') or 0) + (u.get('cache_creation_input_tokens') or 0) + (u.get('cache_read_input_tokens') or 0),
                  'out': u.get('output_tokens') or 0}


def voice(rec, seed, style=None):
    """Voice one pending reply. Returns {style, ok, text, second, why, missing, invented, usage}: on ok False, text is the
    template (the rules' own words) and why says what failed."""
    tpl = rec.get('template_reply') or ''
    style = style or style_for(rec, seed)
    res = {'id': rec.get('id'), 'style': style, 'ok': False, 'text': tpl, 'second': '', 'why': '', 'missing': [], 'invented': [], 'usage': {}}
    split = None
    if style == 'partial':
        # the first lines now, the rest later (as a yard sends what it has priced and the rest after a call): cut at the
        # line nearest the middle of the facts, never inside a line
        FL = facts(tpl, lines=True); half = len(FL) / 2
        cuts = sorted({ln for _, ln in FL[1:]}, key=lambda ln: abs(sum(1 for _, x in FL if x < ln) - half))
        cut = cuts[0] if cuts else None
        split = ([f for f, x in FL if x < cut], [f for f, x in FL if x >= cut]) if cut is not None else None
        if not split or not split[0] or not split[1]: style = res['style'] = 'plain'; split = None
    try:
        system, user = prompt(rec, style, split)
        t0 = time.time()
        out, use = call_ai(system, user)
        use['ms'] = int((time.time() - t0) * 1000); res['usage'] = use
        if style == 'partial':
            m = re.search(r'\{.*\}', out, re.S)
            J = json.loads(m.group(0)) if m else {}
            first, second = str(J.get('first') or '').strip(), str(J.get('second') or '').strip()
            if not first or not second: raise RuntimeError('the two parts did not come back')
            ok1, miss1, inv1 = check(' '.join(split[0]), first)
            ok2, miss2, inv2 = check(' '.join(split[1]), second)
            ok, miss, inv = check(tpl, first, [first, second])
            if not ok: res.update(missing=miss, invented=inv); raise RuntimeError('a fact was dropped or invented')
            res.update(ok=True, text=first, second=second)
        else:
            out = re.sub(r'^\s*(subject|re):.*\n', '', out, flags=re.I).strip()
            ok, miss, inv = check(tpl, out)
            if not ok: res.update(missing=miss, invented=inv); raise RuntimeError('a fact was dropped or invented' if out else 'an empty answer')
            res.update(ok=True, text=out)
    except Exception as e:
        res['why'] = str(e)[:200]
        res['text'], res['second'] = tpl, ''
    return res


# ---------------------------------------------------------------------------------------------------- the ledger
def log(run_dir, rec):
    with open(os.path.join(run_dir, 'world', 'voice.jsonl'), 'a', encoding='utf-8') as f: f.write(json.dumps(rec) + '\n')


def ledger_md(run_dir):
    p = os.path.join(run_dir, 'world', 'voice.jsonl')
    if not os.path.exists(p): return ''
    L = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    if not L: return ''
    by = {}
    for x in L: by.setdefault(x.get('style'), [0, 0]); by[x['style']][0 if x.get('ok') else 1] += 1
    out = ['## World voice: who answered in their own words, and where the template was used\n',
           f"- {sum(1 for x in L if x.get('ok'))} replies voiced, {sum(1 for x in L if not x.get('ok'))} sent as the template (facts kept either way).",
           '- By style: ' + '; '.join(f'{s} {a} voiced, {b} template' for s, (a, b) in sorted(by.items())) + '.']
    bad = [x for x in L if not x.get('ok')]
    if bad:
        out.append('\n| Reply | Party | Kind | Style | Why the template was sent |\n|---|---|---|---|---|')
        out += [f"| {x.get('id')} | {x.get('party', '')[:30]} | {x.get('kind', '')} | {x.get('style')} | {x.get('why', '')[:80]}"
                f"{(' · missing ' + ', '.join(x.get('missing') or [])) if x.get('missing') else ''}{(' · invented ' + ', '.join(x.get('invented') or [])) if x.get('invented') else ''} |" for x in bad[:30]]
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    rec = json.load(open(a[0]))
    st = a[a.index('--style') + 1] if '--style' in a else None
    sd = int(a[a.index('--seed') + 1]) if '--seed' in a else 0
    r = voice(rec, sd, st)
    print(json.dumps({k: v for k, v in r.items() if k not in ('text', 'second')}, indent=1))
    print('--- voiced' if r['ok'] else '--- TEMPLATE SENT', '\n' + r['text'])
    if r['second']: print('--- second part\n' + r['second'])
