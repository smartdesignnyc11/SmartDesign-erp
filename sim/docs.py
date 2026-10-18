"""sim/docs.py: the Documents Workshop (sim/workshop_docs.md). Estimates, change orders, invoices, pay applications,
POs, RFQs, bills and field requests, created as real work in the pilot.

    python3 sim/docs.py usage                 # runs/<run>/docs_usage.json: every document a person created, measured
    python3 sim/docs.py prompt creator <uid>  # the creator's questions, with their own measurements
    python3 sim/docs.py prompt client         # the client reads each client-facing document (after `simctl client-docs`)
    python3 sim/docs.py prompt brand <uid>    # the owner or the designer judges the look against the brand
    python3 sim/docs.py score                 # runs/<run>/docs_workshop.md (measured, back end, client view) + synthesis prompt
    python3 sim/docs.py gallery               # runs/<run>/client_docs/index.html, for Alan

The referee (sim/referee.py) runs AUDIT_JS on every document a person created, every day: the back-end fields
each type needs for accounting and reporting, and whether the document reached the reports with its own numbers.
"""
import html, json, os, re, statistics, sys
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# where each kind of document lives (the keys the harness logs for a create) and its name in the workshop
COLLS = {'c.estimates': 'estimate', 'c.changeOrders': 'change order', 'c.invoices': 'invoice', 'pos': 'PO', 'bills': 'bill',
         'rfqs': 'RFQ', 'p.requests': 'material request'}
CLIENT_FACING = ('estimate', 'change order', 'invoice', 'pay application')
TARGETS = {   # taps and seconds a seasoned person should need (seconds of agent wall time are reported, not compared)
    'estimate': {'phone_taps': 25, 'desk_taps': 20}, 'change order': {'phone_taps': 12, 'desk_taps': 10, 'phone_minutes': 2},
    'invoice': {'desk_taps': 8}, 'pay application': {'desk_taps': 10}, 'PO': {'phone_taps': 12, 'desk_taps': 10},
    'RFQ': {'desk_taps': 12}, 'bill': {'desk_taps': 6}, 'material request': {'phone_taps': 5}}
VALIDATION = re.compile(r'\b(required|missing|cannot|can\'t|must|invalid|enter a|choose a|pick a|not allowed|refused|before you)\b', re.I)

# The back end, checked on the world page as the owner. Every missing or wrong field is a finding naming the field.
AUDIT_JS = r"""(keys) => { try { __MS.as('u_owner'); } catch (e) {}
  const out = [], tot = d => { try { return +(docTotal(d).total || 0); } catch (e) { return 0; } };
  const has = v => !(v == null || v === '' || (Array.isArray(v) && !v.length));
  const eq = (entity, q) => { try { return (erpQuery({ entity, q }).rows || []); } catch (e) { return null; } };
  const find = key => { const coll = key.slice(0, key.lastIndexOf(':')), id = key.slice(key.lastIndexOf(':') + 1);
    if (coll.startsWith('c.')) { for (const c of DB.clients) { const d = (c[coll.slice(2)] || []).find(x => x.id === id); if (d) return { coll, d, c }; } }
    else if (coll === 'p.requests') { for (const p of DB.projects) { const d = (p.requests || []).find(x => x.id === id); if (d) return { coll, d, p }; } }
    else { const d = (DB[coll] || []).find(x => x.id === id || x.number === id); if (d) return { coll, d }; }
    return { coll, d: null }; };
  for (const key of keys) { const { coll, d, c, p: pr } = find(key);
    if (!d) { out.push({ key, type: coll, gone: true, findings: ['the record is gone'] }); continue; }
    const F = [], N = [], miss = (cond, field) => { if (!cond) F.push(field); };
    const p = DB.projects.find(x => x.id === (d.projectId || (pr || {}).id));
    let J = null; try { J = p ? jobFin(p) : null; } catch (e) {}
    const L = d.lines || [];
    let type = { 'c.estimates': 'estimate', 'c.changeOrders': 'change order', 'c.invoices': 'invoice', pos: 'PO', bills: 'bill', rfqs: 'RFQ', 'p.requests': 'material request' }[coll] || coll;
    if (type === 'invoice' && d.mode === 'sov') type = 'pay application';
    const T = tot(d);
    if (['estimate', 'change order', 'invoice', 'pay application'].includes(type)) {
      miss(has(d.projectId), 'job (projectId)'); miss(c && has(c.id), 'client'); miss(has(d.entityId), 'entity (entityId)');
      miss(has(d.number), 'number'); miss(has(d.date), 'date'); miss(T > 0, 'a total above zero');
      miss(d.taxRate != null && d.taxRate !== '', 'sales tax rate (taxRate, even 0)');
      miss(has(d.terms), 'payment terms');
      if (type !== 'pay application') { miss(L.length && L.every(l => has(l.code)), 'cost code on every line');
        miss(L.every(l => +l.rate > 0 || +l.amount > 0), 'a price on every line'); }
    }
    if (type === 'estimate') { miss(has(d.validUntil), 'valid until'); miss(L.every(l => l.cost != null && l.cost !== ''), 'cost on every line (for budget and margin)');
      N.push(`total $${T}`); if (eq('estimates', d.number) && !eq('estimates', d.number).length) F.push('not reportable (not in erpQuery estimates)'); }
    if (type === 'change order') { miss(has(d.scope) || L.some(l => has(l.src) || has(l.lineId)), 'link to the estimate line or scope it changes');
      miss(d.scheduleDays != null && d.scheduleDays !== '', 'schedule days (even 0)');
      if (d.status === 'approved') { miss(has(d.approvedOn || d.approvedAt || d.signedAt) || (d.log || []).some(x => /approv/i.test(JSON.stringify(x))), 'approval record (who, when)');
        if (J) { const appr = ((c || {}).changeOrders || []).filter(x => x.status === 'approved' && x.projectId === d.projectId).reduce((a, x) => a + tot(x), 0);
          if (Math.abs((+J.coAmt || 0) - appr) > 1) F.push(`budget effect: jobFin coAmt $${J.coAmt} vs approved COs $${Math.round(appr)}`);
          if (Math.abs((+J.contract || 0) - ((+J.base || 0) + (+J.coAmt || 0))) > 1) F.push('contract is not base plus approved COs'); } }
      else N.push(`status ${d.status}: no budget effect yet`); }
    if (type === 'invoice' || type === 'pay application') { miss(has(d.due), 'due date');
      if (type === 'pay application') { miss(d.retainagePct != null && d.retainagePct !== '', 'retainage % (pay application)');
        miss(L.length && L.every(l => has(l.sovId)), 'schedule-of-values link on every line');
        let rows = []; try { rows = pgRows(p.id); } catch (e) {}
        // on a schedule-of-values line `pct` is this period's percent and `prevPct` the cumulative already billed:
        // complete to date is prevPct + pct (the app's lineAmount). The rule compared this period's % with the
        // previous cumulative, so every line that billed less this period than before read as lowered (pilot1, d1).
        L.forEach(l => { const toDate = +l.prevPct + (+l.pct || 0);
          if (toDate < +l.prevPct - 0.001) F.push(`line ${l.item}: complete to date ${toDate}% below the ${+l.prevPct}% already billed`); if (toDate > 100.001) F.push(`line ${l.item}: over 100%`);
          const r = rows.find(x => x.sv && x.sv.id === l.sovId); const meas = r && r.pr ? +r.pr.pct || 0 : null;
          if (meas != null && +l.pct > 0 && toDate > meas + 5) F.push(`line ${l.item}: billed ${Math.round(toDate * 100) / 100}% to date vs measured ${Math.round(meas)}%`); }); }
      if (['sent', 'partial', 'paid', 'overdue'].includes(d.status)) { const R = eq('invoices', d.number) || [];
        if (!R.length) F.push('not in the AR report (erpQuery invoices)'); else if (Math.abs((+R[0].amount || 0) - T) > 1) F.push(`AR shows $${R[0].amount}, the invoice says $${T}`);
        if (J && !(J.invs || []).some(x => x.id === d.id)) F.push('not in the job\'s billed (jobFin)'); }
      else N.push(`status ${d.status}: not in AR yet`); }
    if (type === 'PO') { const PT = (() => { try { return poTotal(d).total; } catch (e) { return L.reduce((a, l) => a + (+l.qty || 0) * (+l.price || 0), 0); } })();
      miss(has(d.vendorId) || has(d.vendor), 'vendor'); miss(has(d.vendorId), 'vendor on file (vendorId)'); miss(has(d.projectId), 'job (projectId)'); miss(has(d.entityId), 'buying entity');
      miss(L.length && L.every(l => has(l.code)), 'cost code on every line'); miss(L.length && L.every(l => has(l.line)), 'estimate-line link on every line');
      miss(has(d.taxStatus) || d.tax != null, 'tax status'); miss(has(d.termsPreset) || has(d.terms), 'payment terms'); miss(has(d.expected), 'expected / needed date');
      if (PT > 2500) miss(has(d.rfqId) || (d.srcDocs || []).some(x => /quote|rfq/i.test(JSON.stringify(x))) || has(d.quoteRef), 'sourcing: an RFQ or quotes behind an order over $2,500 (three quotes)');
      if (!['draft', 'cancelled'].includes(d.status)) { const R = eq('purchaseorders', d.number) || [];
        if (!R.length) F.push('not in the PO report (erpQuery purchaseorders)'); else if (Math.abs((+R[0].amount || 0) - PT) > 1) F.push(`PO report shows $${R[0].amount}, the PO says $${PT}`); }
      N.push(`$${PT} ${d.status}`); }
    if (type === 'bill') { const BT = (() => { try { return billTotal(d); } catch (e) { return (d.lines || []).reduce((a, l) => a + (+l.amount || 0), 0); } })();
      miss(has(d.vendor), 'vendor'); miss(has(d.number), 'vendor invoice number'); miss(has(d.date), 'bill date'); miss(has(d.due), 'due date'); miss(has(d.terms), 'terms');
      miss(has(d.projectId) || has(d.cat), 'job or overhead account'); miss(has(d.code) || (d.lines || []).every(l => has(l.code)), 'cost code'); miss(has(d.entityId), 'entity');
      miss(has(d.poId) || /overhead|admin/i.test(d.cat || ''), 'PO link (three-way match)'); miss(has(d.line) || has(d.poId), 'estimate-line link');
      if (J && d.projectId && !['void', 'rejected'].includes(d.status) && (+J.billsAmt || 0) + 1 < BT) F.push(`job cost: jobFin billsAmt $${J.billsAmt} is below this bill $${BT}`);
      N.push(`$${BT} ${d.status}`); }
    if (type === 'RFQ') { miss(has(d.projectId), 'job'); miss(L.length && L.every(l => has(l.src) || has(l.line) || has(l.lineKey)), 'estimate-line link on every line');
      miss((d.sent || d.vendors || []).length >= 3, 'three vendors asked'); miss(has(d.due || d.dueBy), 'quotes due date'); }
    if (type === 'material request') { miss(has(d.taskId), 'the task it is for (cost line)'); miss(has(d.neededBy), 'needed-by date'); miss(has(d.qty) && has(d.unit), 'quantity and unit'); }
    out.push({ key, type, number: d.number || d.what || d.id, status: d.status || '', project: (p || {}).id || '', total: T, findings: F, notes: N,
      lines: L.slice(0, 15).map(l => [String(l.item || l.desc || '').slice(0, 80), String(l.item && l.desc ? l.desc : '').slice(0, 160)]) });
  }
  return out; }"""


def run_dir():
    run = os.environ.get('SIM_RUN') or open(os.path.join(HERE, 'runs', '.current')).read().strip()
    return run, os.path.join(HERE, 'runs', run)


def doc_type(key):
    coll = key[:key.rfind(':')]
    return COLLS.get(coll)


def ts(a):
    try: return datetime.fromisoformat(a['t']).timestamp()
    except Exception: return 0


def usage():
    """Each document a person created, measured from the trail of actions that led to it."""
    run, d = run_dir()
    A = [json.loads(l) for l in open(os.path.join(d, 'actions.jsonl')) if l.strip()]
    audit = {x['key']: x for x in (json.load(open(os.path.join(d, 'ledger.json'))).get('docs') or [])} if os.path.exists(os.path.join(d, 'ledger.json')) else {}
    after = {(a['uid'], a['args'][0]): a.get('ok') for a in A if a.get('cmd') == 'fia_after_reload'}
    out, start = [], {}
    for i, a in enumerate(A):
        uid = a.get('uid') or ''
        if not uid.startswith('u_'): continue
        k0 = (uid, a['day'], a['slot'])
        if k0 not in start: start[k0] = i
        for c in a.get('creates') or []:
            t = doc_type(c['key'])
            if not t: continue
            trail = [x for x in A[start[k0]:i + 1] if x.get('uid') == uid]
            typed = [x for x in trail if x.get('cmd') in ('type', 'pick')]
            form = a.get('form') or {}
            aud = audit.get(c['key'], {})
            if aud.get('type') == 'pay application': t = 'pay application'
            out.append({'uid': uid, 'type': t, 'key': c['key'], 'name': c['name'], 'day': a['day'], 'slot': a['slot'], 'device': a.get('device') or '?',
                        'taps': sum(1 for x in trail if x.get('cmd') in ('tap', 'key', 'go', 'back')), 'actions': len(trail),
                        'seconds': round(ts(a) - ts(trail[0]) + (a.get('ms') or 0) / 1000), 'act_seconds': round(sum((x.get('ms') or 0) for x in trail) / 1000, 1),
                        'screens': list(dict.fromkeys(x.get('after') or x.get('screen') or '?' for x in trail)),
                        'typed': len({str((x.get('args') or [''])[0]) for x in typed}), 'fields_on_form': form.get('fields'), 'filled_on_form': form.get('filled'),
                        'defaulted': max(0, (form.get('filled') or 0) - len(typed)) if form else None,
                        'validation_stops': sum(1 for x in trail for tt in (x.get('toasts') or []) if VALIDATION.search(tt)) + sum(1 for x in trail if 'The app asked' in str(x.get('result', ''))),
                        'errors': sum(len(x.get('errors') or []) for x in trail),
                        'found_after_save': c['on_screen'] or c['in_toast'] and 'toast only', 'found_after_reload': after.get((uid, c['key'])),
                        'backend_findings': aud.get('findings'), 'status_now': aud.get('status')})
            # the lines: everything typed or picked from the start of this document's trail to the next document or the end
            # of the turn (lines are usually added after the record is first saved)
            j = i + 1
            while j < len(A) and not (A[j].get('uid') == uid and (A[j]['day'], A[j]['slot']) == (a['day'], a['slot']) and any(doc_type(x['key']) for x in A[j].get('creates') or [])) \
                    and (A[j]['day'], A[j]['slot']) == (a['day'], a['slot']): j += 1
            sess = [x for x in A[start[k0]:j] if x.get('uid') == uid]
            T_ = [x for x in sess if x.get('cmd') == 'type']; P_ = [x for x in sess if x.get('cmd') == 'pick']
            lab = lambda x: (re.findall(r'"([^"]*)"', str(x.get('result', '')).split('\n')[0]) or [''])[-1]
            nlines = len(aud.get('lines') or []) or 1
            LINEF = re.compile(r'item|desc|qty|quant|unit|rate|price|cost|amount|code|scope|line', re.I)
            out[-1].update({'typed_fields': [[lab(x), len(str((x.get('args') or ['', ''])[1] if len(x.get('args') or []) > 1 else ''))] for x in T_],
                            'picked_fields': [[lab(x), str((x.get('args') or ['', ''])[1])[:40] if len(x.get('args') or []) > 1 else ''] for x in P_],
                            'line_chars_typed': sum(len(str(x['args'][1])) for x in T_ if len(x.get('args') or []) > 1 and LINEF.search(lab(x) or 'line')),
                            'lines': aud.get('lines') or [], 'line_count': len(aud.get('lines') or [])})
            out[-1]['chars_per_line'] = round(out[-1]['line_chars_typed'] / nlines)
            start[k0] = i + 1
    p = os.path.join(d, 'docs_usage.json'); json.dump(out, open(p, 'w'), indent=1)
    print(f'wrote {p}: {len(out)} documents')
    return out


def _tpl(name):
    s = open(os.path.join(HERE, 'workshop_docs.md')).read()
    return s.split(f'<!-- {name} -->')[1].split(f'<!-- /{name} -->')[0].strip()


def prompt(kind, uid=None):
    run, d = run_dir()
    from server import PEOPLE
    os.makedirs(os.path.join(d, 'workshop'), exist_ok=True)
    U = usage() if not os.path.exists(os.path.join(d, 'docs_usage.json')) else json.load(open(os.path.join(d, 'docs_usage.json')))
    cd = os.path.join(d, 'client_docs')
    docs = json.load(open(os.path.join(cd, 'docs.json'))) if os.path.exists(os.path.join(cd, 'docs.json')) else []
    if kind == 'creator':
        mine = [u for u in U if u['uid'] == uid]
        meas = '\n'.join(f"- {u['type']} {u['name'][:40]} ({u['device']}, {u['day']} {u['slot']}): {u['taps']} taps, {u['actions']} actions, {u['seconds']}s, "
                         f"{u.get('line_count', 0)} lines, {u.get('line_chars_typed', 0)} characters typed into lines, {len(u.get('picked_fields') or [])} picks, "
                         f"{len(u['screens'])} screens ({' > '.join(u['screens'][:6])}), typed {u['typed']} of {u['filled_on_form'] or '?'} filled fields, "
                         f"{u['validation_stops']} validation stops, found after save: {u['found_after_save']}; back end: {'; '.join(u['backend_findings'] or []) or 'complete'}"
                         for u in mine) or '- (the harness saw no document you created)'
        t = _tpl('CREATOR'); vals = {'name': PEOPLE[uid][2], 'role': PEOPLE[uid][0], 'measured': meas, 'answer': os.path.join(d, 'workshop', f'docs_{uid}.md'),
                                      'diary': os.path.join(d, 'diary', uid + '.md')}
    elif kind == 'client':
        lst = '\n'.join(f"- {x['type']} {x['number']}: text {x.get('txt')}, print {x.get('print_png')}, portal {x.get('portal_png') or 'not on the portal'}" for x in docs) or '- (none rendered: run `sim/simctl client-docs`)'
        t = _tpl('CLIENT'); vals = {'docs': lst, 'answer': os.path.join(d, 'workshop', 'docs_client.md')}
    else:
        lst = '\n'.join(f"- {x['type']} {x['number']}: print {x.get('print_png')}, portal {x.get('portal_png') or '-'}" for x in docs) or '- (none rendered)'
        t = _tpl('BRAND'); vals = {'name': PEOPLE[uid][2], 'role': PEOPLE[uid][0], 'docs': lst, 'answer': os.path.join(d, 'workshop', f'docs_brand_{uid}.md')}
    for k, v in vals.items(): t = t.replace('{' + k + '}', v)
    return t


def parse_lines(path):
    if not os.path.exists(path): return []
    return [[p.strip() for p in l.lstrip('- ').split('|')] for l in open(path) if re.match(r'^\s*-?\s*(D|C|B)\d+\s*\|', l)]


def score():
    run, d = run_dir()
    U = usage()
    L = [f'# Documents Workshop: {run}\n', 'Measured by the harness, back end checked by the referee, client view judged by the client agent, '
         'the owner and the designer. Everything above "Synthesis" is mechanical.\n', '## Measured, per document type\n',
         '| Type | Device | Made | Median taps | Target taps | Median seconds | Screens | Typed / filled | Validation stops | Not found after save | Back-end gaps |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    by = defaultdict(list)
    for u in U: by[(u['type'], u['device'])].append(u)
    for (t, dev), X in sorted(by.items()):
        tgt = TARGETS.get(t, {}).get(f"{'phone' if dev == 'phone' else 'desk'}_taps", '')
        med = lambda k: statistics.median([x[k] for x in X if x[k] is not None] or [0])
        gaps = sorted({f for x in X for f in (x['backend_findings'] or [])})
        L.append(f"| {t} | {dev} | {len(X)} | {med('taps')} | {tgt} | {med('seconds')} | {med('actions')} actions, {statistics.median([len(x['screens']) for x in X])} screens | "
                 f"{sum(x['typed'] for x in X)} / {sum(x['filled_on_form'] or 0 for x in X)} | {sum(x['validation_stops'] for x in X)} | "
                 f"{sum(1 for x in X if not x['found_after_save'])} | {'; '.join(gaps)[:300] or 'none'} |")
    L.append('\n## Typed versus filled, per document type (the item library question, BACKLOG 1.18)\n')
    L.append('| Type | Documents | Lines | Fields typed | Characters typed into lines | Per line | Picked from a list | Filled, not typed (at save) |')
    L.append('|---|---|---|---|---|---|---|---|')
    byt = defaultdict(list)
    for u in U: byt[u['type']].append(u)
    for t, X in sorted(byt.items()):
        nl = sum(x.get('line_count') or 0 for x in X); ch = sum(x.get('line_chars_typed') or 0 for x in X)
        L.append(f"| {t} | {len(X)} | {nl} | {sum(len(x.get('typed_fields') or []) for x in X)} | {ch} | {round(ch / nl) if nl else '-'} | "
                 f"{sum(len(x.get('picked_fields') or []) for x in X)} | {sum(x.get('defaulted') or 0 for x in X)} |")
    L.append('\nLine descriptions as written (estimate, change order, invoice):')
    for u in U:
        if u['type'] in ('estimate', 'change order', 'invoice', 'pay application'):
            L += [f"- {u['type']} {u['name'][:30]}: {a}" + (f" — {b}" if b else '') for a, b in (u.get('lines') or [])[:8]]
    L.append('\n## Back end, every gap by field (from the referee\'s audit)\n')
    gaps = defaultdict(list)
    for u in U:
        for f in u['backend_findings'] or []: gaps[(u['type'], re.sub(r'line [^:]+:', 'line:', f))].append(u['name'][:30])
    L += [f"- {t}: **{f}** ({len(v)}: {', '.join(v[:4])})" for (t, f), v in sorted(gaps.items(), key=lambda kv: -len(kv[1]))] or ['- (none)']
    W = os.path.join(d, 'workshop')
    rows = defaultdict(list)
    for f in sorted(os.listdir(W)) if os.path.isdir(W) else []:
        if f.startswith('docs_') and f.endswith('.md'):
            who = f[5:-3]
            for p in parse_lines(os.path.join(W, f)):
                if len(p) >= 4: rows[p[0][0]].append((who, p))
    L.append('\n## Client view (client, owner, designer), grouped by document type, worst first\n')
    cv = sorted([r for k in ('C', 'B') for r in rows[k]], key=lambda r: (r[1][1].lower(), {'blocks': 0, 'slows': 1, 'annoys': 2}.get(r[1][2].lower(), 3)))
    L += [f"- {p[1]} · {p[2]} · {who}: {' | '.join(p[3:])[:220]}" for who, p in cv] or ['- (no answers yet)']
    L.append('\n## Creators, by document type\n')
    L += [f"- {p[1]} · {p[2]} · {who}: {p[0]} {' | '.join(p[3:])[:220]}" for who, p in sorted(rows['D'], key=lambda r: r[1][1])] or ['- (no answers yet)']
    L.append('\n## Synthesis, per document type: time and taps against the target, back-end gaps, client-view issues ranked, top fixes\n\n(to be written by the synthesis step)\n')
    p = os.path.join(d, 'docs_workshop.md'); open(p, 'w').write('\n'.join(L) + '\n')
    print(_tpl('SYNTHESIS').replace('{workshop}', p).replace('{usage}', os.path.join(d, 'docs_usage.json')).replace('{answers}', W)
          .replace('{gallery}', os.path.join(d, 'client_docs', 'index.html')))


def gallery():
    run, d = run_dir()
    cd = os.path.join(d, 'client_docs')
    docs = json.load(open(os.path.join(cd, 'docs.json'))) if os.path.exists(os.path.join(cd, 'docs.json')) else []
    W = os.path.join(d, 'workshop')
    notes = defaultdict(list)
    for f in ('docs_client.md', 'docs_brand_u_owner.md', 'docs_brand_u_sarah.md'):
        for p in parse_lines(os.path.join(W, f)):
            if len(p) >= 4: notes[p[1].lower()].append(f"{f[5:-3].replace('brand_', '')}: {' | '.join(p[3:])}")
    cards = []
    for x in docs:
        rel = lambda k: os.path.basename(x[k]) if x.get(k) else ''
        imgs = ''.join(f'<figure><figcaption>{cap}</figcaption><a href="{html.escape(rel(k))}"><img loading="lazy" src="{html.escape(rel(k))}" alt="{html.escape(cap + " " + x["number"])}"></a></figure>'
                       for k, cap in (('portal_png', 'Portal, on the client\'s phone'), ('print_png', 'Print / PDF')) if x.get(k))
        pdf = f'<a href="{html.escape(rel("pdf"))}">PDF</a>' if x.get('pdf') else ''
        nn = ''.join(f'<li>{html.escape(n)}</li>' for n in notes.get(x['number'].lower(), []) + notes.get(x['type'].lower(), [])[:6])
        cards.append(f'<section><h2>{html.escape(x["type"].title())} {html.escape(x["number"])}</h2><p class="meta">{html.escape(x.get("title", ""))} · '
                     f'{html.escape(x.get("client", ""))} · ${x.get("total", 0):,.2f} · {html.escape(x.get("status", ""))} {pdf}</p><div class="figs">{imgs}</div>'
                     + (f'<ul class="notes">{nn}</ul>' if nn else '') + '</section>')
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Client Documents Gallery</title><style>
:root{{--bg:#f7f6f3;--fg:#1d1d1b;--muted:#6b6a66;--card:#fff;--line:#e3e1dc}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#161615;--fg:#ecebe8;--muted:#a3a19c;--card:#20201e;--line:#34332f}}}}
:root[data-theme="dark"]{{--bg:#161615;--fg:#ecebe8;--muted:#a3a19c;--card:#20201e;--line:#34332f}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;padding:24px 16px}}
main{{max-width:1100px;margin:0 auto}} h1{{font-size:22px;margin:0 0 4px}} .lead,.meta{{color:var(--muted)}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:16px 0}} h2{{font-size:17px;margin:0}}
.figs{{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}} figure{{margin:0;flex:1 1 300px;min-width:0}} figcaption{{font-size:13px;color:var(--muted);margin:6px 0}}
img{{width:100%;height:auto;border:1px solid var(--line);border-radius:6px;background:#fff}} .notes{{font-size:14px;margin:10px 0 0;padding-left:18px}}
</style></head><body><main><h1>Client documents, as the client receives them</h1>
<p class="lead">Run {html.escape(run)}. Each document the team created in the pilot, rendered on the client's phone portal and as printed. Notes are the client's, the owner's and the designer's. Invented data.</p>
{''.join(cards) or '<p>No client-facing documents were created in this run.</p>'}</main></body></html>"""
    os.makedirs(cd, exist_ok=True)
    p = os.path.join(cd, 'index.html'); open(p, 'w').write(page)
    print(f'wrote {p} ({len(docs)} documents)')


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'): print(__doc__.strip()); sys.exit(2)
    if a[0] == 'usage': usage()
    elif a[0] == 'prompt': print(prompt(a[1], a[2] if len(a) > 2 else None))
    elif a[0] == 'score': score()
    elif a[0] == 'gallery': gallery()
    else: print(__doc__.strip()); sys.exit(2)
