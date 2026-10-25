// sim/checks_p2.js: the Pilot 2 checks (sim/make_book.py PILOT2), installed on the world page after
// tests/month_runtime.js. It wraps __MS.check: a check type it knows is answered here, every other one goes to the
// scripted month's own M.check, unchanged, so Pilot 1's events score exactly as they did. Each check returns
// [ok, detail]; what a later gated event needs (a number, a total, a vendor) is left in __MS.lastBind.
// Invented data only: every name and amount comes from the world book.
() => {
if (!window.__MS) return 'no month runtime';
if (window.__MS.p2) return 'ok';
const M = window.__MS, base = M.check;
M.p2 = true; M.lastBind = {};
const RX = s => new RegExp(s, 'i');
const r2 = x => Math.round((+x || 0) * 100) / 100;
const tot = d => { try { return +(docTotal(d).total || 0); } catch (e) { return 0; } };
const poTot = po => { try { return +(poTotal(po).total || 0); } catch (e) { return (po.lines || []).reduce((a, l) => a + (+l.qty || 0) * (+l.cost || +l.rate || +l.price || 0), 0); } };
const clientsLike = rx => (DB.clients || []).filter(c => RX(rx).test(c.name || '') || (c.contacts || []).some(x => RX(rx).test(x.name || '')));
const sentStatus = ['sent', 'viewed', 'partial', 'paid', 'overdue'];
const allTasks = () => { try { if (typeof tkItems === 'function') return tkItems().map(r => r.rec || r); } catch (e) {}
  return DB.projects.flatMap(p => (p.actions || []).map(a => Object.assign({ projectId: p.id }, a))).concat(DB.tasks || []); };
const userEmp = u => { const U = (DB.users || []).find(x => x.id === u); return U ? U.employeeId : ''; };
const sentMail = (rx, after) => { const R = RX(rx), out = [];
  Object.entries(DB.demoWs || {}).forEach(([u, A]) => (A.messages || []).forEach(m => { const L = (A.labels || {})[m.id] || m.labelIds || [];
    if (!L.includes('SENT')) return; const day = (typeof appIso === 'function' ? appIso(new Date(m.internalDate)) : new Date(m.internalDate).toISOString()).slice(0, 10);
    const to = String((m.headers || {}).To || '');
    if (day >= after && !/smartdesign\.nyc/i.test(to) && R.test(`${(m.headers || {}).Subject} ${m.body || ''} ${(m.attachments || []).map(a => a.filename).join(' ')}`)) out.push('mail by ' + u + ' to ' + to.slice(0, 40)); }));
  (DB.outbox || []).forEach(o => { if (String(o.at || '').slice(0, 10) >= after && /sent|delivered/.test(String(o.status || '')) && R.test(`${o.subject || ''} ${o.body || o.text || ''}`)) out.push('outbox ' + o.status); });
  return out; };
const P2 = {
  // the prospect is a client: the lead is won (with its client) or a client by that name exists
  leadWon(c) { const L = (DB.leads || []).filter(l => RX(c.rx).test(l.name || ''));
    const won = L.find(l => l.stage === 'won' && l.clientId); const C = clientsLike(c.rx);
    const cl = won ? DB.clients.find(x => x.id === won.clientId) : C[0];
    if (cl) M.lastBind = { client: cl.name, clientId: cl.id };
    return [!!cl, cl ? `client ${cl.name}${won ? ' (won from the lead)' : ' (no lead marked won)'}` : L.length ? 'a lead at ' + L.map(l => l.stage).join(',') : 'not on file']; },
  // an estimate for that client in one of the statuses (sent / approved / converted = the contract)
  estFor(c) { const C = clientsLike(c.rx); const E = C.flatMap(cl => (cl.estimates || []).map(d => ({ d, cl })));
    const hit = E.filter(x => c.status.includes(x.d.status) && tot(x.d) >= (c.min || 1)).pop();
    if (hit) { const T = r2(tot(hit.d)); M.lastBind = { number: hit.d.number, total: T, ten: r2(T * 0.1), client: hit.cl.name, estId: hit.d.id }; }
    return [!!hit, hit ? `${hit.d.number} ${hit.d.status} $${r2(tot(hit.d))}` : E.length ? E.map(x => `${x.d.number} ${x.d.status} $${r2(tot(x.d))}`).join(', ') : C.length ? 'no estimate' : 'not a client']; },
  // the deposit invoice on that client's contract
  depositFor(c) { const C = clientsLike(c.rx); const I = C.flatMap(cl => (cl.invoices || []).filter(i => i.depositOf && i.status !== 'void'));
    const hit = I.filter(i => c.status.includes(i.status)).pop();
    if (hit) M.lastBind = { number: hit.number, total: r2(tot(hit)) };
    return [!!hit, hit ? `${hit.number} ${hit.status} $${r2(tot(hit))}` : I.length ? I.map(i => `${i.number} ${i.status}`).join(', ') : 'no deposit invoice']; },
  // a progress invoice (not the deposit) on that client
  progressFor(c) { const C = clientsLike(c.rx); const I = C.flatMap(cl => (cl.invoices || []).filter(i => !i.depositOf && i.status !== 'void' && (i.date || '') >= (c.after || '2026-09-03')));
    const hit = I.filter(i => c.status.includes(i.status) && tot(i) > 0).pop();
    if (hit) M.lastBind = { number: hit.number, total: r2(tot(hit)) };
    return [!!hit, hit ? `${hit.number} ${hit.status} $${r2(tot(hit))}` : I.length ? I.map(i => `${i.number} ${i.status} $${r2(tot(i))}`).join(', ') : 'no progress invoice']; },
  // a payment from that client recorded on or after the day, of about the amount
  paymentFor(c, ev) { const C = clientsLike(c.rx); const P = C.flatMap(cl => (cl.payments || []).filter(p => (p.date || '') >= ev.day && (!c.amount || Math.abs(+p.amount - +c.amount) < 1)));
    return [P.length > 0, P.length ? `recorded ${P[0].date} $${P[0].amount}` : 'no payment recorded']; },
  // a change order on the job (title, memo or lines match), in one of the statuses; binds its number and total
  coFor(c, ev) { const p = DB.projects.find(x => x.id === c.project) || {}; const cl = DB.clients.find(x => x.id === p.clientId);
    const C = ((cl && cl.changeOrders) || []).filter(d => (d.date || '') >= (c.after || ev.day || '') && RX(c.rx).test(`${d.title || ''} ${d.memo || ''} ${JSON.stringify(d.lines || [])}`));
    const hit = C.filter(d => c.status.includes(d.status) && tot(d) > 0).pop();
    if (hit) M.lastBind = { number: hit.number, total: r2(tot(hit)) };
    return [!!hit, hit ? `${hit.number} ${hit.status} $${r2(tot(hit))}` : C.length ? C.map(d => `${d.number} ${d.status} $${r2(tot(d))}`).join(', ') : 'no change order']; },
  // an approved change order is on an invoice that went to the client
  coInvoiced(c) { const co = DB.clients.flatMap(x => (x.changeOrders || []).map(d => ({ d, cl: x }))).find(x => x.d.number === c.number);
    if (!co) return [false, 'no ' + c.number];
    const I = (co.cl.invoices || []).filter(i => !['draft', 'void'].includes(i.status) && (i.lines || []).some(l => RX(String(c.number).replace(/-/g, '.?')).test(`${l.desc || ''} ${l.item || ''} ${l.source || ''}`) || l.coId === co.d.id || l.srcCo === co.d.id));
    return [I.length > 0, I.length ? 'on ' + I.map(i => `${i.number} ${i.status}`).join(', ') : `${c.number} ${co.d.status}, on no invoice sent`]; },
  // the person clocked in and out that day (one closed time entry at least)
  // (the seed already holds hours for some of these days: an entry counts only if the run made it, or closed one the
  // seed left open; M.p2base is the time entries as the run began, {id: out}, set by the world)
  clocked(c) { const e = userEmp(c.uid); if (!e) return [false, 'no employee for ' + c.uid];
    const B = M.p2base || {}, mine = t => !(t.id in B) || (!B[t.id] && t.out);
    const T = (DB.time || []).filter(t => t.empId === e && t.date === c.day && mine(t)); const closed = T.filter(t => t.in && t.out);
    return [closed.length > 0, closed.length ? closed.map(t => `${String(t.in).slice(11, 16)}-${String(t.out).slice(11, 16)}`).join(', ') : T.length ? 'clocked in, never out' : 'no clock-in']; },
  // a PO on the job with a line matching the item, issued with a vendor and a price; linked = every line from an estimate line
  poFor(c) { const P = (DB.pos || []).filter(po => po.projectId === c.project && (po.lines || []).some(l => RX(c.rx).test(`${l.item || ''} ${l.desc || ''}`)));
    const good = P.filter(po => !['draft', 'cancelled'].includes(po.status) && (po.vendor || po.vendorId) && poTot(po) > 0 && (!c.status || c.status.includes(po.status)));
    const hit = good[good.length - 1];
    if (hit) { const L = hit.lines || [], sl = L.find(l => RX(c.short || 'cement').test(`${l.item || ''} ${l.desc || ''}`) && +l.qty >= 2) || L.filter(l => +l.qty >= 2).pop() || L[0] || {};
      const rate = +sl.cost || +sl.rate || +sl.price || 0, n = Math.min(2, +sl.qty || 1);
      M.lastBind = { number: hit.number, vendor: hit.vendor || '', total: r2(poTot(hit)), short_item: String(sl.item || sl.desc || 'one line').slice(0, 60), short_n: n, short_value: r2(rate * n) }; }
    if (hit && c.linked && !(hit.lines || []).every(l => l.line || l.lineKey || l.src)) return [false, `${hit.number} issued, not from the estimate line`];
    return [!!hit, hit ? `${hit.number} ${hit.vendor || hit.vendorId} $${r2(poTot(hit))} ${hit.status}` : P.length ? P.map(po => `${po.number} ${po.vendor || 'NO VENDOR'} $${r2(poTot(po))} ${po.status}`).join('; ') : 'no PO']; },
  // the PO reached the vendor (mail or the app's own send) on or after the day
  poSent(c, ev) { const po = (DB.pos || []).find(p => p.number === c.number); if (!po) return [false, 'no PO ' + c.number];
    const S = sentMail(String(c.number).replace(/[-]/g, '.?'), ev.day);
    return [S.length > 0 || /sent|partial|received/.test(String(po.sentStatus || po.emailed || '')) && !!po.sentAt, S.length ? S[0] : 'not sent to the vendor']; },
  // a task (any board) by title, owner and state
  taskBy(c) { const T = allTasks().filter(a => RX(c.rx).test(a.title || a.name || ''));
    const T2 = T.filter(a => !c.assignee || RX(c.assignee).test(String(a.assignee || a.owner || '')));
    if (!T2.length) return [false, T.length ? `nearest: ${String(T[0].title || '').slice(0, 30)} · ${T[0].assignee || 'nobody'}` : 'no task'];
    if (c.done) return [T2.some(a => a.status === 'done' || a.done === true), T2.map(a => a.status || 'open').join(',')];
    return [true, `${T2[0].assignee || ''} due ${T2[0].due || '-'}`]; },
  // the team meeting ran in Meeting Mode that day and wrote its minutes
  teamMeeting(c) { const Mt = (DB.meetings || []).filter(m => m.kind === 'team' && m.date === c.day);
    const ended = Mt.filter(m => m.endedAt && m.minutes);
    const n = ended.length ? +(ended[0].minutes.discussed || 0) : 0;
    return [ended.length > 0 && n >= (c.min || 1), ended.length ? `minutes: ${ended[0].summary || ''}` : Mt.length ? 'started, never ended (no minutes)' : 'no meeting in Meeting Mode'];
  },
};
M.check = function (c, ev) { M.lastBind = {}; if (c && P2[c.t]) { try { return P2[c.t](c, ev || {}); } catch (e) { return [false, 'check error: ' + String(e.message || e).slice(0, 100)]; } } return base(c, ev); };
M.checkAll = list => list.map(([c, ev]) => M.check(c, ev));
M.gate = (c, ev) => { const r = M.check(c, ev); return [!!r[0], r[1], M.lastBind || {}]; };
return 'ok';
}
