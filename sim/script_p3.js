// sim/script_p3.js: Pilot 3's scripted world actions (sim/cycle_book.json, kind "script"), installed on the world page.
// Four roles play Pilot 3 (Alan, 10-25). The steps of the roles that do not play are done here, the way that person
// would record them, so the business cycle still closes: the foreman receives against the PO (one short, one
// damaged), clocks the crew on cost codes, writes the daily log and measures % complete; the controller imports the
// bank and card statements, confirms only the matches the app itself proposed, and builds the payroll from approved
// hours. The referee (sim/cycle.py) checks every one of them like any step and grades none of them. Invented data only.
() => {
if (window.__P3) return 'ok';
const P3 = window.__P3 = {};
const num = x => +x || 0, r2 = x => Math.round(num(x) * 100) / 100;
const as = u => { try { __MS.as(u); } catch (e) { signIn(u); } };
const pid = id => DB.projects.find(p => p.id === id);
const empOf = u => { const U = (DB.users || []).find(x => x.id === u); return U ? U.employeeId : ''; };
const audit_ = (...a) => { try { audit(...a); } catch (e) {} };
const log_ = (pr, msg) => { try { setCurrent(pr.id); log(msg); } catch (e) {} };

// the foreman receives a delivery against its PO: every line as it came, the short line backordered, the damaged
// quantity reported (Deliveries > Report a problem writes po.issues the same way)
P3.receive = (p) => {
  const po = (DB.pos || []).find(x => x.number === p.number);
  if (!po) return { ok: false, text: 'no PO ' + p.number };
  const pr = pid(po.projectId); const got = [], notes = [];
  po.lines.forEach(l => {
    const t = `${l.item || ''} ${l.desc || ''}`, q = num(l.qty);
    let rec = q;
    if (p.short && new RegExp(p.short.rx, 'i').test(t) && q > p.short.qty) rec = q - p.short.qty;
    const was = num(l.received); l.received = r2(Math.max(was, rec));
    got.push({ lineId: l.id, item: l.item || l.desc || '', unit: l.unit || '', qty: r2(l.received - was) });
    if (p.short && new RegExp(p.short.rx, 'i').test(t)) {
      (po.issues = po.issues || []).push({ t: nowStamp(), by: 'Angel', type: 'short', lineId: l.id, qty: p.short.qty, eta: '', note: `${p.short.qty} cement boards ${p.short.why}` });
      l.backordered = p.short.qty; l.issue = 'short'; po.flag = `short: ${l.item || ''} ${p.short.qty}`; notes.push(`${p.short.qty} cement boards short (${p.short.why})`);
    }
    if (p.damaged && new RegExp(p.damaged.rx, 'i').test(t)) {
      (po.issues = po.issues || []).push({ t: nowStamp(), by: 'Angel', type: 'damaged', lineId: l.id, qty: p.damaged.qty, eta: '', note: `${p.damaged.qty} ${p.damaged.unit} ${p.damaged.why}` });
      l.issue = 'damaged'; po.flag = `damaged: ${l.item || ''} ${p.damaged.qty}`; notes.push(`${p.damaged.qty} ${p.damaged.unit} damaged (${p.damaged.why})`);
    }
  });
  const short = (po.issues || []).some(i => i.type === 'short' || i.type === 'backorder');
  po.status = short ? 'partial' : 'received'; if (!short) po.receivedOn = today();
  (po.receipts = po.receipts || []).push({ date: today(), t: nowStamp(), by: 'Angel', lines: got, slip: 'photo of the packing slip', note: notes.join('; ') });
  audit_('po', po.id, 'received', '', notes.join('; ') || 'complete', 'scripted foreman (Pilot 3)');
  pr && log_(pr, `${po.number}: received${notes.length ? ' — ' + notes.join('; ') : ' complete'} (Angel)`);
  save();
  return { ok: true, text: `${po.number} ${po.vendor}: ${po.status}${notes.length ? '; ' + notes.join('; ') : ''}`, vendor: po.vendor, notes };
};

// the foreman's day on the new job: the crew's hours on the estimate line's cost code (submitted for the PM), the
// daily log, and the measured % on the task the line names
P3.field_day = (p) => {
  const pr = pid(p.project); if (!pr) return { ok: false, text: 'no project ' + p.project };
  const out = [];
  (p.hours || []).forEach(([u, key, h, note]) => {
    const e = empOf(u); if (!e) { out.push('no employee for ' + u); return; }
    // the estimate line's own cost code (the app's lineCode), from the line the referee resolved for this work
    const ref = (p.refs || {})[key] || '', f = ref ? findLine(ref) : null;
    let code = ''; try { code = f ? (f.line.code || lineCode(f.line, f.doc)) : ''; } catch (e) {}
    const start = `${today()}T07:00:00`, end = new Date(new Date(start).getTime() + (num(h) * 60 + 30) * 60000);
    const pad = n => String(n).padStart(2, '0');
    DB.time.push({ id: uid('te'), empId: e, date: today(), in: start, out: `${today()}T${pad(end.getHours())}:${pad(end.getMinutes())}:00`, breakMin: 30, projectId: pr.id, code,
      notes: note, status: 'submitted', approvedBy: '', source: 'phone', work: [{ projectId: pr.id, code, line: ref, hours: num(h), note }], scripted: 'Pilot 3 field' });
    out.push(`${u} ${h}h on ${code || 'no code'}`);
  });
  const measured = {};
  (p.measure || []).forEach(([key, pct]) => {
    const rx = new RegExp((p.task_rx || {})[key] || key, 'i');
    const t = (pr.tasks || []).find(x => rx.test(x.name || ''));
    if (!t) { out.push(`no task for ${key}`); return; }
    try { prgSet(pr, t, { pct, by: 'Angel', role: 'foreman', src: 'field', note: 'measured on site' }); measured[key] = pct; out.push(`${t.name} ${pct}%`); }
    catch (e) { t.pct = pct; measured[key] = pct; out.push(`${t.name} ${pct}% (set)`); }
  });
  DB.field = DB.field || {}; DB.field.logs = DB.field.logs || [];
  DB.field.logs.push({ id: uid('fl'), projectId: pr.id, date: today(), v: 2, weather: 'Clear', temp: '74', weatherSrc: 'manual',
    crew: (p.hours || []).map(([u, key, h]) => ({ name: ((DB.users || []).find(x => x.id === u) || {}).name || u, empId: empOf(u), hours: num(h), clockH: num(h) })),
    subs: [], deliveries: [], inspections: [], visitors: [], work: Object.entries(measured).map(([k, v]) => ({ name: k, pct: v, note: '' })),
    done: [p.log], delays: [], notes: p.log, by: 'Angel', signedAt: appNowIso(), scripted: 'Pilot 3 field' });
  save();
  return { ok: true, text: out.join('; '), bind: { measured } };
};

// the controller's statements: Banking > Import Statement with the bank's CSV (month_runtime's importCsv), then only
// what the app proposed itself is confirmed (bills and POs; client payments are billing's to record), and the card
// purchase bought for the client is coded to its job like any material, with the receipt's words as the memo
P3.import_statement = async (p) => {
  const r = await __MS.importCsv(p.acct, p.name, p.csv);
  return { ok: !r.err, text: r.err ? 'import: ' + r.err : `imported ${p.name}: ${r.label}` };
};
P3.match = (p) => {
  const out = [];
  (DB.txns || []).filter(t => new RegExp(p.rx, 'i').test(t.desc || '')).forEach(t => {
    if (t.proposal && ['po', 'bill'].includes(t.proposal.kind)) {
      try { const ok = confirmMatch(t, 'Confirmed the app\'s own proposal (scripted controller, Pilot 3)'); out.push(`${t.desc} ${ok === false ? 'not confirmed' : 'confirmed'}`); } catch (e) { out.push(`${t.desc} error ${e.message}`); }
    }
    const code = (p.code || []).find(c => new RegExp(c.rx, 'i').test(t.desc || ''));
    if (code && !t.projectId) {
      t.projectId = code.project; t.cat = code.cat || 'materials'; t.memo = code.memo || ''; t.status = 'categorized'; t.classedBy = 'Controller (scripted)';
      out.push(`${t.desc} coded to ${code.project}`);
    }
  });
  save();
  return { ok: true, text: out.join('; ') || 'nothing to confirm' };
};
P3.payroll = () => {
  try { const r = payrollFromTime({ quiet: true }); save(); return r ? { ok: true, text: `payroll ${r.from} to ${r.to} ${r.status} $${r2(r.total)}` } : { ok: false, text: 'no approved hours for a run' }; }
  catch (e) { return { ok: false, text: 'payroll: ' + e.message }; }
};
P3.run = async (p) => {
  if (!P3[p.do]) return { ok: false, text: 'no script ' + p.do };
  const prev = (currentUser() || {}).id;
  as(p.as || 'u_controller');
  try { return await P3[p.do](p); } finally { try { if (prev) as(prev); } catch (e) {} }
};
return 'ok';
}
