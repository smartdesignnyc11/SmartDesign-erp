/*<<livejobs.js>>*/
// Live jobs (BACKLOG §1.25 and §1.26; Alan, Cowork session 2026-10-17): what the firm's real work needs that the ERP
// could not do. Built on invented equivalents; the real job details load into the private platform database only.
//   1. Two payers on one contract (a landlord and a tenant): each payer is billed for their own lines and has their
//      own AR, aging, statement, collections and portal view.
//   2. Range estimates with allowances for the unknowns of an old building, and a paid exploratory phase that turns
//      into the construction contract once discovery is done.
//   3. A normal estimate walked end to end (the suite does it: tests/livejobs_test.py).
//   4. The hard / soft / contingency cost model as the estimate, and the historic tax credit (HTC) budget calculator
//      (federal 20% plus the state's rate on 98.5% of hard and soft costs), finish materials per SF per property, and
//      the job that is also a Mercer & Bond deal.
//   5. A contractor user who can become an employee: approved hours become their bill, not payroll; converting keeps
//      the history.
// Design gate (BACKLOG §1.16): no new store, list, queue or menu item. Every piece rides on a noun that exists:
//   client (the contract party) gains `payers`; estimate lines gain payer, range, allowance, phase, bucket, prop;
//   SOV lines, change orders, invoices and payments carry the payer; an employee record gains workerType and the
//   vendor it is paid through; a bill built from approved hours is an ordinary bill (fromTime) in Bills; a portal user
//   gains payerId. Receivables (arRows) gain the payer, so aging, the Receivables report, statements and the portal
//   read one list. The demo jobs sit behind one switch (Settings, owner): off by default, so every other suite and the
//   pinned figures see the firm exactly as before.

// ---- 1. Payers ---------------------------------------------------------------------------------------------------
const LJ = { scope: new Map(), pick: "", demo: "lj", stmtPayer: "" };
function ljPayers(c) {
  return c && Array.isArray(c.payers) ? c.payers : [];
}
function ljMulti(c) {
  return ljPayers(c).length > 1;
}
function ljPayerById(c, id) {
  return ljPayers(c).find((p) => p.id === id) || null;
}
function ljPayerName(c, id) {
  const p = ljPayerById(c, id);
  return p ? p.name : "";
}
function ljPrimary(c) {
  return (ljPayers(c)[0] || {}).id || "";
}
const ljOkPayer = (c, id) => !!(id && ljPayerById(c, id));
// whose a line is: the line's own payer, else its document's, else the first payer on the contract
function ljEstLinePayer(c, d, l) {
  return ljOkPayer(c, l && l.payer) ? l.payer : ljOkPayer(c, d && d.payer) ? d.payer : ljPrimary(c);
}
function ljSvPayer(c, sv) {
  if (!sv) return ljPrimary(c);
  if (ljOkPayer(c, sv.payer)) return sv.payer;
  if (sv.lineRef && "function" == typeof findLine) {
    const r = findLine(sv.lineRef);
    if (r && r.client === c) return ljEstLinePayer(c, r.doc, r.line);
  }
  const co = (c.changeOrders || []).find((x) => (sv.coId && x.id === sv.coId) || (!sv.coId && sv.source && x.number === sv.source));
  return co && ljOkPayer(c, co.payer) ? co.payer : ljPrimary(c);
}
function ljLinePayer(c, inv, l) {
  if (ljOkPayer(c, l && l.payer)) return l.payer;
  if (l && l.sovId) {
    const sv = (c.sov || []).find((v) => v.id === l.sovId);
    if (sv) return ljSvPayer(c, sv);
  }
  const key = l && (l.fromLine || l.line || l.lineRef);
  if (key && "function" == typeof findLine) {
    const r = findLine(key);
    if (r && r.client === c) return ljEstLinePayer(c, r.doc, r.line);
  }
  return ljOkPayer(c, inv && inv.payer) ? inv.payer : ljPrimary(c);
}
function ljInvPayers(c, inv) {
  const s = [...new Set((inv.lines || []).filter((l) => l.item || l.desc || +l.rate || +l.scheduled).map((l) => ljLinePayer(c, inv, l)))];
  return s.length ? s : [ljOkPayer(c, inv.payer) ? inv.payer : ljPrimary(c)];
}
function ljInvPayer(c, inv) {
  const s = ljInvPayers(c, inv);
  return 1 === s.length ? s[0] : "mixed";
}
function ljPayPayer(c, py) {
  if (py && py.invoiceId) {
    const i = (c.invoices || []).find((x) => x.id === py.invoiceId);
    if (i) {
      const p = ljInvPayer(c, i);
      if ("mixed" !== p) return p;
    }
  }
  return ljOkPayer(c, py && py.payer) ? py.payer : ljPrimary(c);
}
function ljCoPayer(c, x) {
  return ljOkPayer(c, x && x.payer) ? x.payer : ljPrimary(c);
}
// An estimate as one payer reads it: only the lines that payer pays for (a copy; the record is never changed).
function ljEstForPayer(c, e, pid) {
  const lines = (e.lines || []).filter((l) => ljEstLinePayer(c, e, l) === pid);
  return lines.length ? Object.assign({}, e, { lines: lines, _ljOf: e.id }) : null;
}
// The client record as one payer sees it, swapped in place for the length of fn (a draw, a statement, an Ask read)
// and put back in finally. A save asked for while it is swapped waits until it is put back (persist, below), so the
// stored record is always the whole one.
function ljWithPayer(c, pid, fn) {
  if (!c || !ljMulti(c) || !ljPayerById(c, pid)) return fn();
  const was = LJ.scope.get(c.id);
  if (was) return fn();
  const P = ljPayerById(c, pid),
    keep = {};
  const K = ["invoices", "payments", "changeOrders", "estimates", "sov", "contract", "contractNet", "name", "billingAddr", "contacts"];
  K.forEach((k) => (keep[k] = c[k]));
  const sov = (c.sov || []).filter((v) => ljSvPayer(c, v) === pid),
    base = r2(sov.filter((v) => "Contract" === v.source).reduce((a, v) => a + (+v.scheduled || 0), 0)),
    invs = (c.invoices || []).filter((i) => ljInvPayer(c, i) === pid),
    pays = (c.payments || []).filter((py) => ljPayPayer(c, py) === pid),
    cos = (c.changeOrders || []).filter((x) => ljCoPayer(c, x) === pid),
    ests = (c.estimates || []).map((e) => ljEstForPayer(c, e, pid)).filter(Boolean),
    contacts = (P.contacts && P.contacts.length ? P.contacts : [{ id: P.id + "c", name: P.contact || P.name, email: P.email || "", phone: P.phone || "", role: P.role || "", primary: !0 }]);
  LJ.scope.set(c.id, pid);
  // a push onto a swapped list reaches the record too, so nothing made while it is swapped is lost
  const twin = (arr, real) => ((arr.push = function () {
    return Array.prototype.push.apply(real, arguments), Array.prototype.push.apply(arr, arguments);
  }), arr);
  Object.assign(c, {
    invoices: twin(invs, keep.invoices),
    payments: twin(pays, keep.payments),
    changeOrders: twin(cos, keep.changeOrders),
    estimates: twin(ests, keep.estimates),
    sov: twin(sov, keep.sov),
    contract: base,
    contractNet: base,
    name: P.name,
    billingAddr: P.addr || keep.billingAddr,
    contacts: contacts,
  });
  try {
    return fn();
  } finally {
    K.forEach((k) => (c[k] = keep[k])), LJ.scope.delete(c.id);
  }
}
const ljScoped = () => LJ.scope.size > 0;
// The payer a signed-in portal user is: a client user with payerId on a contract with two payers.
function ljUserPayer() {
  const u = "function" == typeof currentUser ? currentUser() : null;
  if (!u || "client" !== u.role || !u.payerId || !u.clientId) return null;
  const c = (DB.clients || []).find((x) => x.id === u.clientId);
  return c && ljMulti(c) && ljPayerById(c, u.payerId) ? { c: c, pid: u.payerId } : null;
}
function ljAsUser(fn) {
  const up = ljUserPayer();
  return up ? ljWithPayer(up.c, up.pid, fn) : fn();
}

// Each payer's side of the contract: their share of the contract and change orders, billed, paid, open, overdue, the
// aging buckets, retainage held and credits on account. Read from the same records clientFin reads.
function ljPayerFin(c, pid) {
  // while the record is swapped to one payer (that payer's own portal), no other payer's figures can be read
  const cur = LJ.scope.get(c.id);
  if (cur && cur !== pid) return null;
  return ljWithPayer(c, pid, () => {
    const f = clientFin(c);
    return {
      pid: pid,
      name: ljPayerName(c, pid),
      role: (ljPayerById(c, pid) || {}).role || "",
      contract: r2(+c.contract || 0),
      approvedCO: r2(f.approvedCO),
      revised: r2(f.revised),
      invoiced: r2(f.invoiced),
      paid: r2(f.paid),
      outstanding: r2(f.outstanding),
      overdue: r2(f.overdue),
      buckets: Object.assign({}, f.buckets),
      retHeld: r2(f.retHeld),
      credits: r2(f.credits),
      remaining: r2(f.remaining),
      open: f.open.map((o) => ({ id: o.x.id, number: o.x.number, bal: o.bal, age: o.age, due: o.x.due })),
    };
  });
}
function ljByPayer(c) {
  return ljPayers(c)
    .map((p) => ljPayerFin(c, p.id))
    .filter(Boolean);
}

// ---- 2. Keeping every record's payer true (runs before each save) ------------------------------------------------
// Stamps the payer onto SOV lines, change orders, invoices and payments from where it comes from (the estimate line,
// the change order, the invoice), and splits a progress invoice that holds two payers' lines into one per payer: a
// pay application goes to the party who owes it. Nothing else is touched, and a client with one payer is never read.
function ljSync() {
  const made = [];
  (DB.clients || []).forEach((c) => {
    if (!ljMulti(c) || LJ.scope.has(c.id)) return;
    (c.sov || []).forEach((v) => {
      const p = ljSvPayer(c, v);
      v.payer !== p && (v.payer = p);
    });
    (c.changeOrders || []).forEach((x) => {
      x.payer || (x.payer = ljPrimary(c));
    });
    (c.invoices || []).slice().forEach((inv) => {
      const p = ljInvPayer(c, inv);
      if ("mixed" === p && "sov" === inv.mode && "draft" === inv.status) return void made.push(...ljSplitInvoice(c, inv, !0));
      "mixed" !== p && inv.payer !== p && (inv.payer = p);
    });
    (c.payments || []).forEach((py) => {
      const p = ljPayPayer(c, py);
      py.payer !== p && (py.payer = p);
    });
  });
  made.length &&
    setTimeout(() => {
      const c = made[0].c;
      toastDone(
        `Split by payer: ${made.map((m) => `${m.inv.number} for ${ljPayerName(c, m.inv.payer)}`).join(", ")}`,
        flowGo.doc(c, "invoice", made[made.length - 1].inv),
      );
    }, 30);
  return made;
}
// One invoice per payer: the lines of every payer but the first move onto a new invoice with the same header (title,
// template, deposit link, terms, retainage, dates). Returns the new invoices.
function ljSplitInvoice(c, inv, quiet) {
  const by = {};
  (inv.lines || []).forEach((l) => (by[ljLinePayer(c, inv, l)] = by[ljLinePayer(c, inv, l)] || []).push(l));
  const pids = Object.keys(by);
  if (pids.length < 2) return [];
  const first = pids.includes(inv.payer) ? inv.payer : pids[0],
    out = [],
    wasClean = !docDirty(inv),
    titled = (t, pid) => `${String(t || "Invoice").replace(/ · .*$/, "")} · ${ljPayerName(c, pid)}`;
  pids
    .filter((p) => p !== first)
    .forEach((pid) => {
      const n = newDoc(c, "invoice", {
        mode: inv.mode,
        fields: {
          title: titled(inv.title, pid),
          projectId: inv.projectId,
          template: inv.template,
          depositOf: inv.depositOf,
          due: inv.due,
          date: inv.date,
          terms: inv.terms,
          taxRate: inv.taxRate,
          retainagePct: inv.retainagePct,
          memo: inv.memo,
          lines: by[pid].map((l) => Object.assign({}, l, { payer: pid })),
        },
      });
      (n.payer = pid), n.retainageRelease || delete n.retainageRelease, inv.rebill && (n.rebill = inv.rebill), docMark(n), out.push({ c: c, inv: n });
      c.activity.push({ t: nowStamp(), by: (S && S.project && S.project.userName) || "", text: `${n.number} split from ${inv.number} for ${ljPayerName(c, pid)}: ${money(docTotal(n).total)}` });
    });
  (inv.lines = by[first].map((l) => Object.assign(l, { payer: first }))), (inv.payer = first), (inv.title = titled(inv.title, first));
  wasClean && docMark(inv);
  try {
    audit("invoice", inv.id, "split-by-payer", null, out.map((o) => o.inv.number).join(", "), `${inv.number}: one invoice per payer`);
  } catch (e) {}
  quiet || toastDone(`${inv.number} is now ${ljPayerName(c, first)}'s; ${out.map((o) => `${o.inv.number} for ${ljPayerName(c, o.inv.payer)}`).join(", ")}`, flowGo.doc(c, "invoice", inv));
  return out;
}

// ---- 3. Ranges, allowances and the paid exploratory phase -------------------------------------------------------
// A line can carry a range (lo, hi) for an unknown; the contract carries its "carried" figure (qty x rate). An
// allowance line is an amount carried in the contract that is reconciled against what it really costs: over it is a
// change order, under it is a credit. A phased estimate has phase 1 (the paid exploratory work, fixed) and phase 2
// (construction, mostly ranges); phase 2 is off the contract (its lines count $0) until discovery is done and the
// client approves it, when its lines join the contract and the schedule of values.
const LJ_UNKNOWNS = [
  ["mep", "MEP rerouting"],
  ["code", "Code upgrades"],
  ["foundation", "Foundation depth and underpinning"],
  ["structure", "Structure"],
  ["storm", "Storm and sewer"],
  ["hidden", "Other hidden conditions"],
];
const ljPhaseOff = (l, d) => !!(d && d.phased && 2 === +l.phase && !l.on && "invoice" !== d.type);
{
  const base = lineAmount;
  lineAmount = function (l, doc) {
    return l && doc && doc.phased && ljPhaseOff(l, doc) ? 0 : base.apply(this, arguments);
  };
}
{
  const base = lineBudget;
  lineBudget = function (l, d) {
    return l && d && d.phased && ljPhaseOff(l, d) ? { budget: 0, defaulted: !1 } : base.apply(this, arguments);
  };
}
const ljRaw = (l) => r2((+l.qty || 0) * (+l.rate || 0));
function ljLineRange(l) {
  const v = ljRaw(l),
    R = l.range || null,
    lo = R && "" !== R.lo && null != R.lo ? +R.lo : v,
    hi = R && "" !== R.hi && null != R.hi ? +R.hi : v;
  return { lo: r2(Math.min(lo, hi)), hi: r2(Math.max(lo, hi)), carried: v, isRange: !!(R && (lo !== v || hi !== v)) };
}
// The estimate's money read three ways: what is fixed, the range of the unknowns, and what the contract carries.
function ljRange(d) {
  const O = { fixed: 0, lo: 0, hi: 0, carried: 0, allowances: 0, ranges: 0, p1: 0, p2: { lo: 0, hi: 0, carried: 0, n: 0, on: 0 } };
  (d.lines || []).forEach((l) => {
    const R = ljLineRange(l);
    if (d.phased && 2 === +l.phase) {
      (O.p2.lo += R.lo), (O.p2.hi += R.hi), (O.p2.carried += R.carried), O.p2.n++, l.on && O.p2.on++;
      if (!l.on) return;
    } else d.phased && (O.p1 += R.carried);
    (O.lo += R.lo), (O.hi += R.hi), (O.carried += R.carried), R.isRange ? O.ranges++ : (O.fixed += R.carried), l.allowance && (O.allowances += R.carried);
  });
  ["fixed", "lo", "hi", "carried", "allowances", "p1"].forEach((k) => (O[k] = r2(O[k]))), ["lo", "hi", "carried"].forEach((k) => (O.p2[k] = r2(O.p2[k])));
  return O;
}
const ljHasRanges = (d) => !!(d && (d.lines || []).some((l) => l.range || l.allowance || l.unknown));
// After a conversion: phase-2 lines that are not on yet leave the schedule of values (they were added at $0), SOV
// lines from allowance lines say so, and the estimate remembers when phase 1 became the contract.
function ljAfterConvert(c, d) {
  if (!d || "estimate" !== d.type || "converted" !== d.status) return;
  const keyOf = (l) => `estimate:${d.id}:${l.id}`;
  if (d.phased) {
    const off = new Set((d.lines || []).filter((l) => ljPhaseOff(l, d)).map(keyOf));
    (c.sov = (c.sov || []).filter((v) => !off.has(v.lineRef))), c.sov.forEach((v, i) => (v.order = i)), d.phase1At || (d.phase1At = today());
  }
  const allow = new Set((d.lines || []).filter((l) => l.allowance).map(keyOf));
  (c.sov || []).forEach((v) => allow.has(v.lineRef) && (v.allowance = !0));
}
// A discovery finding on a phase-2 line: what opening up showed it costs. Outside the range is said plainly: the
// client hears it before the construction phase is priced (Truth, early).
function ljFound(c, d, lineId, amount, note) {
  const l = (d.lines || []).find((x) => x.id === lineId);
  if (!l) return { ok: !1, why: "No such line" };
  const a = r2(+amount);
  if (!(a >= 0) || "" === String(amount).trim()) return { ok: !1, why: "Enter what discovery says the line costs" };
  const R = ljLineRange(l),
    by = (S && S.project && S.project.userName) || role(),
    clean = !docDirty(d);
  l.found = { amount: a, note: String(note || "").trim(), by: by, at: appNowIso(), outside: a < R.lo - 0.5 || a > R.hi + 0.5 };
  try {
    audit("estimate", d.id, "discovery-finding", null, { line: l.item, amount: a }, `${d.number} · ${l.item}: ${money(a)} (range ${money(R.lo)}–${money(R.hi)})`);
  } catch (e) {}
  clean && docMark(d);
  return { ok: !0, outside: l.found.outside, l: l };
}
// The client approves the construction phase: each phase-2 line takes its discovery figure (an unresolved range is
// carried as an allowance at its carried figure), the lines join the contract and the schedule of values, and the
// contract grows by exactly their total. Recorded with who and when, like an estimate's approval.
function ljApprovePhase2(c, d, opts) {
  const o = opts || {},
    P2 = (d.lines || []).filter((l) => d.phased && 2 === +l.phase && !l.on);
  if (!P2.length) return { ok: !1, why: "Nothing left in the construction phase to approve" };
  if (!["converted", "approved"].includes(d.status)) return { ok: !1, why: "Approve the exploratory phase first: it becomes the contract" };
  const by = (S && S.project && S.project.userName) || role(),
    before = docTotal(d),
    open = P2.filter((l) => !l.found);
  P2.forEach((l) => {
    l.found ? ((l.rate = r2(l.found.amount / ((+l.qty || 1) || 1))), l.range && (l.range.settled = !0)) : l.range && (l.allowance = !0), (l.on = !0);
  });
  const after = docTotal(d),
    addTotal = r2(after.total - before.total),
    addNet = r2(after.sub - after.disc - (before.sub - before.disc)),
    k = after.sub ? (after.sub - after.disc + after.tax) / after.sub : 1;
  P2.forEach((l) => {
    const key = `estimate:${d.id}:${l.id}`;
    (c.sov || []).some((v) => v.lineRef === key) ||
      c.sov.push({ id: uid("sv"), taxable: !!l.taxable, desc: (l.num ? l.num + ". " : "") + (l.item || l.desc), scheduled: r2(lineAmount(l, d) * k), source: "Contract", order: c.sov.length, lineRef: key, allowance: !!l.allowance || void 0, phase: 2 });
  });
  (c.contract = r2((+c.contract || 0) + addTotal)), (c.contractNet = r2((null != c.contractNet ? +c.contractNet : +c.contract - addTotal) + addNet));
  d.phase2 = { status: "approved", at: appNowIso(), on: today(), by: by, name: o.name || "", total: addTotal, lines: P2.length, allowances: open.length };
  (d.history = d.history || []).push({ t: nowStamp(), by: by, from: d.status, action: "phase2-approved", note: `construction phase: ${P2.length} lines, ${money(addTotal)}${open.length ? `, ${open.length} carried as allowances` : ""}`, total: after.total });
  docMark(d);
  c.activity.push({ t: nowStamp(), by: by, text: `${d.number}: construction phase approved, contract ${money(c.contract)} (+${money(addTotal)})` });
  try {
    audit("estimate", d.id, "phase2-approved", before.total, after.total, `${d.number} construction phase approved by ${o.name || "the client"} (recorded by ${by}): +${money(addTotal)}`);
  } catch (e) {}
  return { ok: !0, add: addTotal, allowances: open.length };
}

// Allowances against what they really cost. Spent and committed come from the line's own records (lineFin: bills, bank
// lines, POs, labor and stock on the line), at cost against the line's budget; an overage is priced at the line's own
// markup (price over budget), so the change order says exactly what the contract would have said.
function ljAllowanceRows(c) {
  const out = [];
  (c.estimates || [])
    .filter((d) => "converted" === d.status)
    .forEach((d) =>
      (d.lines || [])
        .filter((l) => l.allowance && !ljPhaseOff(l, d))
        .forEach((l) => {
          const key = `estimate:${d.id}:${l.id}`,
            F = ("function" == typeof lineFin && lineFin(key)) || { actual: 0, committed: 0 },
            price = r2(lineAmount(l, d)),
            budget = r2(lineBudget(l, d).budget),
            used = r2((+F.actual || 0) + (+F.committed || 0)),
            factor = budget ? price / budget : 1,
            over = r2(used - budget),
            cos = (c.changeOrders || []).filter((x) => x.allowanceOf === key && !["void", "rejected", "superseded"].includes(x.status)),
            covered = r2(cos.filter((x) => !x.allowanceCredit).reduce((a, x) => a + docTotal(x).total, 0)),
            overPrice = over > 0.5 ? r2(over * factor) : 0,
            credit = l.allowanceClosed && over < -0.5 ? r2(-over * factor) : 0,
            st = l.allowanceClosed ? "closed" : over > 0.5 ? (covered >= overPrice - 0.5 ? "covered" : "over") : budget && used >= 0.9 * budget ? "near" : "ok";
          out.push({ c: c, d: d, l: l, key: key, item: l.item || l.desc || "", unknown: l.unknown || "", payer: ljMulti(c) ? ljEstLinePayer(c, d, l) : "", price: price, budget: budget, spent: r2(+F.actual || 0), committed: r2(+F.committed || 0), used: used, over: over, overPrice: overPrice, covered: covered, toCO: r2(Math.max(0, overPrice - covered)), credit: credit, status: st, cos: cos, projectId: d.projectId || "" });
        }),
    );
  return out;
}
function ljAllowanceAll() {
  return (DB.clients || []).flatMap((c) => ljAllowanceRows(c));
}
// The change order an overage needs, drafted for a person to send (No extra work without a signed change order).
function ljAllowanceCO(c, key) {
  const r = ljAllowanceRows(c).find((x) => x.key === key);
  if (!r) return { ok: !1, why: "Not an allowance on this contract" };
  if (r.toCO <= 0.5) return { ok: !1, why: "Nothing over the allowance that a change order does not already cover" };
  const n = newDoc(c, "co", {
    fields: {
      title: `Allowance overage: ${r.item}`,
      projectId: r.projectId,
      payer: r.payer || void 0,
      allowanceOf: key,
      memo: `The contract carried ${money(r.price)} for ${r.item}. Spent and committed so far: ${money(r.used)} at cost against a budget of ${money(r.budget)}. This change order covers the difference at the contract's own markup.`,
      lines: [{ id: uid("l"), item: `${r.item}: over the allowance`, desc: `Allowance ${money(r.price)}; cost ${money(r.used)} against ${money(r.budget)}`, qty: 1, unit: "ls", rate: r.toCO, taxable: !1, cost: r2(r.toCO / (r.budget ? r.price / r.budget : 1)) }],
    },
  });
  docMark(n);
  try {
    audit("co", n.id, "allowance-overage-drafted", null, r.toCO, `${n.number} drafted for ${r.item}: ${money(r.toCO)}`);
  } catch (e) {}
  return { ok: !0, co: n, amount: r.toCO };
}
// Closing an allowance: what was not used goes back to the client as a credit change order (drafted, never sent alone).
function ljAllowanceClose(c, key) {
  const r = ljAllowanceRows(c).find((x) => x.key === key);
  if (!r) return { ok: !1, why: "Not an allowance on this contract" };
  if (r.committed > 0.5) return { ok: !1, why: `Close it once the open orders are billed: ${money(r.committed)} still committed` };
  const by = (S && S.project && S.project.userName) || role(),
    clean = !docDirty(r.d);
  r.l.allowanceClosed = { at: appNowIso(), by: by, spent: r.spent };
  clean && docMark(r.d);
  const under = r2(r.budget - r.spent);
  let n = null;
  if (under > 0.5) {
    const credit = r2(under * (r.budget ? r.price / r.budget : 1));
    (n = newDoc(c, "co", {
      fields: {
        title: `Allowance credit: ${r.item}`,
        projectId: r.projectId,
        payer: r.payer || void 0,
        allowanceOf: key,
        allowanceCredit: !0,
        memo: `The contract carried ${money(r.price)} for ${r.item}; it cost ${money(r.spent)} against a budget of ${money(r.budget)}. The unused part comes back to you as a credit.`,
        lines: [{ id: uid("l"), item: `${r.item}: unused allowance`, desc: `Credit at the contract's markup`, qty: 1, unit: "ls", rate: -credit, taxable: !1, cost: -under }],
      },
    })),
      docMark(n);
  }
  try {
    audit("estimate", r.d.id, "allowance-closed", null, r.spent, `${r.item} closed at ${money(r.spent)}${n ? `; credit ${n.number}` : ""}`);
  } catch (e) {}
  return { ok: !0, co: n };
}

// ---- 4. Hard / soft / contingency and the historic tax credit budget --------------------------------------------
const LJ_BUCKETS = [
  ["hard", "Hard Costs"],
  ["soft", "Soft Costs"],
  ["contingency", "Contingency"],
];
const LJ_SOFT_RX = /\b(design|architect\w*|engineer\w*|permit\w*|filing|expedit\w*|insurance|legal|survey\w*|consultant\w*|fees?|special inspection\w*|testing|lpc|shpo|tax credit|appraisal|financing|developer)\b/i;
function ljBucketOf(l) {
  if (l && l.bucket) return l.bucket;
  const t = `${(l && l.item) || ""} ${(l && l.desc) || ""}`;
  return /contingenc/i.test(t) ? "contingency" : LJ_SOFT_RX.test(t) ? "soft" : "hard";
}
// Every line's price into its bucket (and property, for the tax credit), with the firm's own budget beside it.
function ljCostModel(d) {
  const B = { hard: { price: 0, cost: 0, n: 0 }, soft: { price: 0, cost: 0, n: 0 }, contingency: { price: 0, cost: 0, n: 0 } };
  (d.lines || []).forEach((l) => {
    if (ljPhaseOff(l, d)) return;
    const b = B[ljBucketOf(l)] || B.hard;
    (b.price += lineAmount(l, d)), (b.cost += lineBudget(l, d).budget), b.n++;
  });
  Object.values(B).forEach((b) => ((b.price = r2(b.price)), (b.cost = r2(b.cost))));
  const total = r2(B.hard.price + B.soft.price + B.contingency.price);
  return { B: B, total: total, contPct: B.hard.price ? r2((100 * B.contingency.price) / B.hard.price) : 0 };
}
// The HTC calculator. Per property: its hard and soft costs (lines tagged to it, plus its share of the lines tagged
// to none, by floor area), the qualified basis (98.5% of hard plus soft: contingency is not spent money), the federal
// credit (20%) and the state credit at the property's own rate. Credits are an estimate until the state historic
// office and the National Park Service certify the work.
function ljHtcDefaults(d) {
  return (d.htc = d.htc || { fed: 20, qual: 98.5, props: [] });
}
function ljHtc(d) {
  const H = d.htc;
  if (!H || !(H.props || []).length) return null;
  const props = H.props,
    sfAll = props.reduce((a, p) => a + (+p.sf || 0), 0),
    shareOf = (p) => (sfAll ? (+p.sf || 0) / sfAll : 1 / props.length),
    rows = props.map((p) => ({ id: p.id, name: p.name, state: +p.state || 0, sf: +p.sf || 0, finishPerSf: +p.finishPerSf || 0, hard: 0, soft: 0, contingency: 0 }));
  (d.lines || []).forEach((l) => {
    if (ljPhaseOff(l, d)) return;
    const amt = lineAmount(l, d),
      b = ljBucketOf(l),
      own = rows.find((r) => r.id === l.prop);
    own ? (own[b] += amt) : rows.forEach((r, i) => (r[b] += amt * shareOf(props[i])));
  });
  const fed = +H.fed || 0,
    qual = +H.qual || 0;
  rows.forEach((r) => {
    ["hard", "soft", "contingency"].forEach((k) => (r[k] = r2(r[k])));
    (r.total = r2(r.hard + r.soft + r.contingency)), (r.basis = r2(((r.hard + r.soft) * qual) / 100)), (r.fedCredit = r2((r.basis * fed) / 100)), (r.stateCredit = r2((r.basis * r.state) / 100)), (r.credits = r2(r.fedCredit + r.stateCredit)), (r.net = r2(r.total - r.credits));
  });
  const T = { hard: 0, soft: 0, contingency: 0, total: 0, basis: 0, fedCredit: 0, stateCredit: 0, credits: 0, net: 0 };
  rows.forEach((r) => Object.keys(T).forEach((k) => (T[k] = r2(T[k] + r[k]))));
  return { fed: fed, qual: qual, rows: rows, T: T };
}
// Finish materials priced per SF per property become estimate lines (hard costs, tagged to their property); a second
// press updates them rather than adding more.
function ljFinishLines(c, d) {
  const H = ljHtcDefaults(d);
  let n = 0;
  (H.props || []).forEach((p) => {
    if (!(+p.sf > 0 && +p.finishPerSf > 0)) return;
    let l = (d.lines || []).find((x) => x.ljFinish === p.id);
    l || ((l = { id: uid("l"), item: `Finish materials: ${p.name}`, desc: `${(+p.sf).toLocaleString()} SF at ${money(p.finishPerSf)}/SF`, qty: 0, unit: "sf", rate: 0, taxable: !1, ljFinish: p.id }), d.lines.push(l));
    Object.assign(l, { qty: +p.sf, rate: +p.finishPerSf, unit: "sf", bucket: "hard", prop: p.id, desc: `${(+p.sf).toLocaleString()} SF at $${(+p.finishPerSf).toLocaleString()}/SF` }), n++;
  });
  return n;
}

// ---- 5. A contractor who can become an employee -----------------------------------------------------------------
// The person is an employee record (the one list of people who log hours) with workerType "contractor": their hours
// are logged and approved like anyone's, but an approved hour becomes a line on their bill (a vendor bill in Bills,
// paid through Payables and reported on the 1099), never payroll. Their record's payroll rate is 0, so the hours
// themselves cost nothing in job cost: the bill carries the cost to the job, once. Converting to an employee closes
// the contractor record (its hours and bills stay exactly as they were) and opens an employee record that payroll
// pays from the effective date; the person and their sign-in move to it.
const ljIsContractor = (emp) => !!(emp && "contractor" === emp.workerType);
const ljEmp = (id) => (DB.employees || []).find((e) => e.id === id) || null;
function ljVendorFor(emp) {
  let v = (DB.vendors || []).find((x) => x.id === emp.vendorId);
  return (
    v ||
      ((v = { id: uid("v"), name: emp.businessName || emp.name, trade: "Design (independent contractor)", email: emp.email || "", w9: !1, insuranceExp: "", bankChangedAt: "", contractorOf: emp.id, terms: "NET 15" }),
      DB.vendors.push(v),
      (emp.vendorId = v.id)),
    v
  );
}
// Approved, unbilled hours of every contractor, up to today, onto one bill per person, job and pay period. An open
// bill (not yet approved for payment) of the same period takes the new hours; an approved one is never changed, so
// late hours start a new bill. Returns the bills touched.
function ljBillHours() {
  const td = today(),
    touched = new Map();
  (DB.time || [])
    .filter((e) => "approved" === e.status && !e.billId && e.date <= td && ljIsContractor(ljEmp(e.empId)))
    .sort((a, b) => String(a.date).localeCompare(b.date))
    .forEach((e) => {
      const emp = ljEmp(e.empId),
        v = ljVendorFor(emp),
        P = payPeriodOf(e.date),
        rate = +emp.contractRate || 0,
        h = hoursOf(e);
      let b = (DB.bills || []).find((x) => x.fromTime && x.empId === emp.id && x.projectId === (e.projectId || "") && x.period && x.period.from === P.from && ["submitted", "draft"].includes(x.status));
      if (!b) {
        const ini = String(emp.name || "C").split(/\s+/).map((w) => w[0]).join("").toUpperCase(),
          job = (DB.projects || []).find((p) => p.id === e.projectId);
        let num = `HRS-${ini}-${P.to.slice(5).replace("-", "")}`;
        const same = (DB.bills || []).filter((x) => x.vendor === v.name && String(x.number || "").startsWith(num)).length;
        same && (num += "-" + (same + 1));
        b = {
          id: uid("b"),
          vendor: v.name,
          vendorId: v.id,
          number: num,
          date: td,
          due: iso(addDays(td, 15)),
          terms: v.terms || "NET 15",
          entityId: (job && job.entityId) || emp.entityId || "ent1",
          projectId: e.projectId || "",
          poId: "",
          cat: "design",
          code: e.code || "",
          line: "",
          lines: [],
          payMethod: "ACH",
          fileId: "",
          notes: `Approved hours, ${fmt(P.from)} – ${fmt(P.to)}, at ${money(rate)}/h. Built from the hours ${emp.name} logged; not payroll.`,
          status: "submitted",
          approvals: [{ t: nowStamp(), ts: appNowIso(), by: "Hours", role: "system", action: "built from approved hours" }],
          createdBy: emp.name,
          fromTime: !0,
          empId: emp.id,
          period: { from: P.from, to: P.to },
          rate: rate,
          hours: 0,
          timeIds: [],
        };
        DB.bills.push(b);
      }
      b.lines.push({ id: uid("bl"), desc: `${fmt(e.date)} · ${h.toFixed(2)} h${e.notes ? " · " + String(e.notes).slice(0, 80) : ""}`, amount: r2(h * rate), timeId: e.id });
      (b.hours = r2((+b.hours || 0) + h)), b.timeIds.push(e.id), (e.billId = b.id), (e.billedAs = "contractor");
      try {
        audit("time", e.id, "billed-as-contractor", null, b.number, `${emp.name} ${fmt(e.date)} ${h.toFixed(2)} h on ${b.number}`);
      } catch (x) {}
      touched.set(b.id, b);
    });
  return [...touched.values()];
}
// The person becomes an employee from a date. Returns the new employee record.
function ljConvertToEmployee(empId, o) {
  const old = ljEmp(empId);
  if (!ljIsContractor(old)) return { ok: !1, why: "Only a contractor is converted" };
  const opts = o || {},
    eff = opts.effective || today(),
    rate = +opts.rate;
  if (!(rate > 0)) return { ok: !1, why: "Set the hourly wage the person is paid as an employee" };
  const by = (S && S.project && S.project.userName) || role(),
    n = {
      id: uid("em"),
      name: old.name,
      role: opts.role || old.role,
      rate: rate,
      burden: null != opts.burden ? +opts.burden : 20,
      billRate: old.billRate,
      entityId: opts.entityId || old.entityId || "ent1",
      active: !0,
      workerType: "employee",
      since: eff,
      convertedFrom: old.id,
      history: [...(old.history || []), { at: appNowIso(), by: by, from: "contractor", to: "employee", effective: eff, why: opts.why || "" }],
    };
  DB.employees.push(n);
  Object.assign(old, { active: !1, until: iso(addDays(eff, -1)), convertedTo: n.id, history: n.history.slice() });
  // hours on or after the effective date that no bill holds are the employee's
  let moved = 0;
  (DB.time || []).forEach((e) => {
    e.empId === old.id && e.date >= eff && !e.billId && ((e.empId = n.id), moved++);
  });
  (DB.users || []).forEach((u) => u.employeeId === old.id && (u.employeeId = n.id));
  try {
    audit("employee", old.id, "converted-to-employee", { workerType: "contractor", rate: old.contractRate }, { id: n.id, workerType: "employee", rate: rate, effective: eff }, `${old.name}: contractor to employee from ${fmt(eff)} (${moved} later entries moved)`);
  } catch (x) {}
  return { ok: !0, emp: n, moved: moved };
}
// Payroll never pays a contractor's hours: a run built from time, or a run typed by hand that covers their dates, sees
// them as already paid elsewhere (they are, on the bill) for the length of the call.
function ljHideContractorTime(fn) {
  const hid = (DB.time || []).filter((e) => !e.payrollId && ljIsContractor(ljEmp(e.empId)));
  hid.forEach((e) => (e.payrollId = "__lj_contractor"));
  try {
    return fn();
  } finally {
    hid.forEach((e) => "__lj_contractor" === e.payrollId && delete e.payrollId);
  }
}
if ("function" == typeof payrollFromTime) {
  const base = payrollFromTime;
  payrollFromTime = function () {
    const a = arguments,
      self = this;
    return ljHideContractorTime(() => base.apply(self, a));
  };
}
if ("function" == typeof prLinkTime) {
  const base = prLinkTime;
  prLinkTime = function () {
    const a = arguments,
      self = this;
    return ljHideContractorTime(() => base.apply(self, a));
  };
}
if ("function" == typeof timeAction) {
  const base = timeAction;
  timeAction = function (e, a) {
    const r = base.apply(this, arguments);
    if (e && "approved" === e.status && ljIsContractor(ljEmp(e.empId))) {
      const B = ljBillHours();
      B.length &&
        (save(),
        setTimeout(() => {
          const b = B[0];
          toastDone(`${empName(e.empId)}'s approved hours are on bill ${b.number}: ${(+b.hours).toFixed(2)} h, ${money(billGross(b))}`, flowGo.bill(b));
        }, 40));
    }
    return r;
  };
}

// ---- 6. Wrappers: the payer in the books, the reports and the portal -------------------------------------------
// The speed memo keys every reader on the settings it reads besides the records (spdCtx): the payer a record is
// swapped to is one, so a payer's figures are never answered from the whole contract's, or the other way round.
if ("function" == typeof spdCtx) {
  const base = spdCtx;
  spdCtx = function () {
    const k = base.apply(this, arguments);
    return LJ.scope.size || LJ.stmtPayer ? `${k}|lj:${[...LJ.scope].map(([a, b]) => a + "=" + b).join(",")}:${LJ.stmtPayer}` : k;
  };
}
{
  const base = persist;
  persist = function () {
    const a = arguments,
      self = this;
    if (ljScoped()) return new Promise((res) => setTimeout(() => res(persist.apply(self, a)), 0));
    try {
      ljSync();
    } catch (e) {
      console.warn("livejobs sync", e);
    }
    return base.apply(self, a);
  };
}
{
  const base = clientFin;
  clientFin = function (c) {
    const f = base.apply(this, arguments);
    if (c && ljMulti(c) && !LJ.scope.has(c.id)) {
      // each open invoice says whose it is: aging, collections and the portal read it from here
      f.open.forEach((o) => (o.payer = ljInvPayer(c, o.x)));
    }
    return f;
  };
}
if ("function" == typeof arRows) {
  const base = arRows;
  arRows = function () {
    const rows = base.apply(this, arguments);
    rows.forEach((r) => {
      if (r && r.c && ljMulti(r.c)) {
        const pid = ljInvPayer(r.c, r.i);
        (r.payer = pid), (r.payerName = ljPayerName(r.c, pid)), (r.payerRole = (ljPayerById(r.c, pid) || {}).role || "");
      }
    });
    return rows;
  };
}
if ("function" == typeof repAR) {
  const base = repAR;
  repAR = function () {
    const h = base.apply(this, arguments),
      multi = (DB.clients || []).filter(ljMulti);
    if (!multi.length) return h;
    const rows = multi.flatMap((c) => ljByPayer(c).map((f) => ({ c: c, f: f })));
    return (
      h +
      `<h3 class="rep-h">By Payer</h3><p class="small muted fin2-sub">Contracts with more than one payer: each payer's own invoices, aging and statement.</p><div class="tw"><table class="t rep-t lj-ar-payer"><thead><tr><th>Payer</th><th>Contract</th><th class="money">Open</th><th class="money">Current</th><th class="money">1–30</th><th class="money">31–60</th><th class="money">Over 60</th><th></th></tr></thead><tbody>${rows
        .map(
          ({ c, f }) =>
            `<tr data-ljpayer="${esc(c.id)}|${esc(f.pid)}"><td><b>${esc(f.name)}</b>${f.role ? ` <span class="small muted">${esc(f.role)}</span>` : ""}</td><td class="small">${esc(c.name)}</td><td class="money"><b>${money(f.outstanding)}</b></td><td class="money">${money(f.buckets.current)}</td><td class="money ${f.buckets.d30 ? "warn" : ""}">${money(f.buckets.d30)}</td><td class="money ${f.buckets.d60 ? "warn" : ""}">${money(f.buckets.d60)}</td><td class="money ${f.buckets.d90 ? "bad" : ""}">${money(f.buckets.d90)}</td><td><button class="btn sm" data-ljstmt="${esc(c.id)}|${esc(f.pid)}">Statement</button></td></tr>`,
        )
        .join("")}</tbody></table></div>`
    );
  };
}
// A statement for one payer reads only that payer's invoices and payments, addressed to them.
if ("function" == typeof repStatement) {
  const base = repStatement;
  repStatement = function () {
    const a = arguments,
      self = this,
      c = (DB.clients || []).find((x) => x.id === repClient);
    return c && LJ.stmtPayer && ljMulti(c) ? ljWithPayer(c, LJ.stmtPayer, () => base.apply(self, a)) : base.apply(self, a);
  };
}
function ljStatementHtml(c, pid) {
  const keep = [repClient, repFrom, repTo, LJ.stmtPayer];
  (repClient = c.id), (repFrom = ""), (repTo = ""), (LJ.stmtPayer = pid);
  try {
    return repStatement();
  } finally {
    [repClient, repFrom, repTo, LJ.stmtPayer] = keep;
  }
}
function ljOpenStatement(c, pid) {
  mbModal(`Statement: ${esc(ljPayerName(c, pid))}`, `<div class="pv">${ljStatementHtml(c, pid)}</div>`, { submit: null });
}
// The portal: a payer's user sees their own share everywhere, the draw, the statement, a document and Ask.
{
  const base = render;
  render = function () {
    const a = arguments,
      self = this;
    return ljAsUser(() => base.apply(self, a));
  };
}
if ("function" == typeof portalStatement) {
  const base = portalStatement;
  portalStatement = function (c) {
    const a = arguments,
      self = this,
      up = ljUserPayer();
    if (up && c && c.id === up.c.id) {
      const keep = LJ.stmtPayer;
      LJ.stmtPayer = up.pid;
      try {
        return base.apply(self, a);
      } finally {
        LJ.stmtPayer = keep;
      }
    }
    return base.apply(self, a);
  };
}
if ("function" == typeof portalView) {
  const base = portalView;
  portalView = function () {
    const a = arguments,
      self = this;
    return ljAsUser(() => base.apply(self, a));
  };
}
if ("function" == typeof eqRows) {
  const base = eqRows;
  eqRows = function () {
    const a = arguments,
      self = this;
    return ljAsUser(() => base.apply(self, a));
  };
}
// Collections: a reminder or cover email for an invoice goes to the payer who owes it.
if ("function" == typeof draftDocEmail) {
  const base = draftDocEmail;
  draftDocEmail = async function (c, d) {
    const a = arguments,
      self = this;
    if (c && d && ljMulti(c) && ("invoice" === d.type || "co" === d.type)) {
      const pid = "invoice" === d.type ? ljInvPayer(c, d) : ljCoPayer(c, d);
      if ("mixed" !== pid) return ljWithPayer(c, pid, () => base.apply(self, a));
    }
    return base.apply(self, a);
  };
}
// New progress invoice for one payer: LJ.pick names the payer while newDoc runs; the SOV lines are that payer's.
{
  const base = newDoc;
  newDoc = function (c, kind, opts) {
    const d = base.apply(this, arguments);
    try {
      if (c && "invoice" === kind && ljMulti(c)) {
        const pid = (opts && opts.payer) || LJ.pick || "";
        if (pid && ljPayerById(c, pid)) {
          const clean = !docDirty(d);
          (d.payer = pid),
            "sov" === d.mode &&
              ((d.lines = (d.lines || []).filter((l) => ljLinePayer(c, d, l) === pid)),
              (d.title = `Progress billing #${(c.invoices || []).filter((i) => "sov" === i.mode && i !== d && ljInvPayer(c, i) === pid).length + 1} · ${ljPayerName(c, pid)}`)),
            clean && docMark(d);
        }
      }
      if (c && "co" === kind && ljMulti(c) && !d.payer) d.payer = (opts && opts.payer) || LJ.pick || ljPrimary(c);
    } catch (e) {
      console.warn("livejobs newDoc", e);
    }
    return d;
  };
}
{
  const base = docAction;
  docAction = async function (c, d, a) {
    // a pay application goes to the party who owes it: an invoice holding two payers' lines is split before it is sent
    if (c && d && "invoice" === d.type && "send" === a && ljMulti(c) && "mixed" === ljInvPayer(c, d))
      return void toast(`${d.number} holds lines for ${ljInvPayers(c, d).map((p) => ljPayerName(c, p)).join(" and ")}: Split by Payer first, so each one gets their own invoice`);
    const r = await base.apply(this, arguments);
    try {
      d && "estimate" === d.type && ["convert", "approveconvert", "approve"].includes(a) && ljAfterConvert(c, d);
    } catch (e) {
      console.warn("livejobs convert", e);
    }
    return r;
  };
}
// An allowance over its budget with no change order covering it is money the firm is carrying: it is raised until a
// change order is drafted (No extra work without a signed change order).
{
  const base = reminders;
  reminders = function () {
    const out = base.apply(this, arguments);
    try {
      const over = ljAllowanceAll().filter((r) => "over" === r.status);
      over.length &&
        out.push({
          n: over.length,
          label: `allowance${1 === over.length ? "" : "s"} over budget with no change order: ${over
            .slice(0, 2)
            .map((r) => `${r.item} ${money(r.toCO)}`)
            .join("; ")}`,
          go: { view: "clients" },
          sev: "bad",
        });
    } catch (e) {}
    return out;
  };
}

// ---- 7. Queryable: Ask, the Report Builder and erpQuery read the same rows --------------------------------------
function ljPayerRows() {
  return (DB.clients || [])
    .filter(ljMulti)
    .flatMap((c) =>
      ljByPayer(c).map((f) => {
        const p = (DB.projects || []).find((x) => x.clientId === c.id);
        return { _id: `${c.id}:${f.pid}`, _module: "Billing", _label: `${f.name} (${f.role || "payer"})`, _go: null, clientId: c.id, client: c.name, projectId: p ? p.id : "", project: p ? p.project.name : "", payer: f.name, payerId: f.pid, payerRole: f.role, contract: f.revised, billed: f.invoiced, paid: f.paid, outstanding: f.outstanding, overdue: f.overdue, current: r2(f.buckets.current), d1to30: r2(f.buckets.d30), d31to60: r2(f.buckets.d60), over60: r2(f.buckets.d90), retainage: f.retHeld };
      }),
    );
}
function ljAllowanceQRows() {
  return ljAllowanceAll().map((r) => {
    const p = (DB.projects || []).find((x) => x.id === r.projectId);
    return { _id: r.key, _module: "Billing", _label: `${r.item}: allowance`, _go: null, clientId: r.c.id, client: r.c.name, projectId: r.projectId, project: p ? p.project.name : "", estimate: r.d.number, item: r.item, unknown: (LJ_UNKNOWNS.find((u) => u[0] === r.unknown) || ["", ""])[1], payer: r.payer ? ljPayerName(r.c, r.payer) : "", allowance: r.price, budget: r.budget, spent: r.spent, committed: r.committed, overBy: r2(Math.max(0, r.over)), toChangeOrder: r.toCO, status: r.status };
  });
}
function ljRangeQRows() {
  return (DB.clients || []).flatMap((c) =>
    (c.estimates || [])
      .filter((d) => d.phased || ljHasRanges(d) || d.costModel)
      .map((d) => {
        const R = ljRange(d),
          M = ljCostModel(d),
          H = ljHtc(d),
          p = (DB.projects || []).find((x) => x.id === d.projectId);
        return { _id: d.id, _module: "Estimates", _label: `${d.number} ${d.title || ""}`.trim(), _go: null, clientId: c.id, client: c.name, projectId: d.projectId || "", project: p ? p.project.name : "", estimate: d.number, status: d.status, low: R.lo, high: R.hi, carried: R.carried, allowances: R.allowances, phase1: d.phased ? R.p1 : "", phase2Low: d.phased ? R.p2.lo : "", phase2High: d.phased ? R.p2.hi : "", phase2Approved: d.phase2 ? d.phase2.on : "", hard: M.B.hard.price, soft: M.B.soft.price, contingency: M.B.contingency.price, taxCredits: H ? H.T.credits : "", netAfterCredits: H ? H.T.net : "" };
      }),
  );
}
try {
  (EQ_TABLES.payers = () => ljPayerRows()), (EQ_TABLES.allowances = () => ljAllowanceQRows()), (EQ_TABLES.estimateranges = () => ljRangeQRows());
  Object.assign(EQ_ALIAS, { payer: "payers", landlord: "payers", tenant: "payers", allowance: "allowances", ranges: "estimateranges", range: "estimateranges", htc: "estimateranges", taxcredit: "estimateranges", costmodel: "estimateranges" });
  EQ_MONEY_TABLES.push("payers", "allowances", "estimateranges"), EQ_CLIENT_TABLES.push("payers");
  "undefined" != typeof MD_VIEWS && Object.assign(MD_VIEWS, { payers: ["clients", "billing"], allowances: ["clients", "billing", "costs"], estimateranges: ["clients", "billing"] });
  REP_DS.payers = { n: "Payers on shared contracts", rows: () => ljPayerRows(), dims: ["client", "project", "payer", "payerRole"], sums: ["contract", "billed", "paid", "outstanding", "overdue"] };
  REP_DS.allowances = { n: "Allowances", rows: () => ljAllowanceQRows(), dims: ["client", "project", "payer", "unknown", "status"], sums: ["allowance", "budget", "spent", "committed", "overBy", "toChangeOrder"] };
} catch (e) {
  console.warn("livejobs tables", e);
}

// ---- 8. Screens -------------------------------------------------------------------------------------------------
(function ljCss() {
  if (document.getElementById("lj-css")) return;
  const s = document.createElement("style");
  (s.id = "lj-css"),
    (s.textContent = `
.lj-card{border:1px solid var(--line,#D9DDE3);border-radius:10px;padding:12px 14px;margin:0 0 12px;background:var(--panel,#fff)}
.lj-card h3{margin:0 0 4px;font-size:15px}.lj-card h4{margin:12px 0 6px;font-size:13px}
.lj-sub{font-size:12.5px;color:var(--mut,#6b7480);margin:0 0 8px}
.lj-rows{display:flex;flex-direction:column;gap:6px}
.lj-row{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;padding:8px 0;border-top:1px solid var(--line2,#EEF0F3)}
.lj-row:first-child{border-top:0}
.lj-row .lj-nm{flex:1 1 220px;min-width:0}.lj-row .lj-nm b{overflow-wrap:anywhere}
.lj-kv{display:flex;flex-direction:column;min-width:86px}.lj-kv span{font-size:11px;color:var(--mut,#6b7480)}.lj-kv b{font-size:13.5px;font-variant-numeric:tabular-nums}
.lj-kv.bad b{color:var(--bad,#b42318)}.lj-kv.warn b{color:var(--warn,#b54708)}
.lj-acts{display:flex;flex-wrap:wrap;gap:8px}
.lj-in{width:96px;height:32px}.lj-in.wide{width:180px}.lj-sel{height:32px;max-width:170px}
.lj-sum{display:flex;flex-wrap:wrap;gap:8px 18px;margin:6px 0 2px}
.lj-tog{display:flex;flex-wrap:wrap;gap:8px 16px;margin:4px 0 8px}.lj-tog label{display:flex;align-items:center;gap:6px;font-size:13px;min-height:32px}
.lj-tog input{width:auto}
.lj-note{font-size:12.5px;padding:8px 10px;border-radius:8px;background:var(--warnbg,#FFF6E5);margin:6px 0}
.lj-note.ok{background:var(--okbg,#ECFDF3)}
.lj-pill{font-size:11px;padding:2px 8px;border-radius:10px;background:var(--line2,#EEF0F3);white-space:nowrap}
.lj-pill.bad{background:#FEE4E2;color:#912018}.lj-pill.warn{background:#FEF0C7;color:#93370D}.lj-pill.ok{background:#D1FADF;color:#05603A}
.lj-field{display:flex;flex-direction:column;gap:2px;font-size:11px;color:var(--mut,#6b7480)}
@media (max-width:760px){.lj-row .lj-nm{flex-basis:100%}.lj-in{width:84px}.lj-in.wide{width:100%}.lj-kv{min-width:74px}}
`),
    document.head.appendChild(s);
})();
const ljKv = (k, v, cls) => `<div class="lj-kv ${cls || ""}"><span>${k}</span><b>${v}</b></div>`;
const ljBtn = (attr, label, cls) => `<button class="btn sm ${cls || ""}" ${attr}>${label}</button>`;
const ljWho = () => (S && S.project && S.project.userName) || ((currentUser && currentUser()) || {}).name || role();
const ljCanMoney = () => ["owner", "pm", "coord", "billing", "controller"].includes(role());

// The payers card on a client's billing page: each payer's contract, billed, paid, open and overdue, with their
// statement and a progress invoice of their own.
function ljPayersCard(c) {
  const F = ljByPayer(c);
  return `<div class="lj-card lj-payers no-doc-print"><h3>Payers on This Contract</h3><p class="lj-sub">Each payer is billed for their own lines and has their own invoices, aging and statement.</p><div class="lj-rows">${F.map(
    (f) =>
      `<div class="lj-row" data-ljpayer="${esc(c.id)}|${esc(f.pid)}"><div class="lj-nm"><b>${esc(f.name)}</b> <span class="lj-pill">${esc(f.role || "Payer")}</span></div>${ljKv("Contract", money(f.revised))}${ljKv("Billed", money(f.invoiced))}${ljKv("Paid", money(f.paid))}${ljKv("Open", money(f.outstanding), f.outstanding ? "" : "")}${ljKv("Overdue", money(f.overdue), f.overdue ? "bad" : "")}<div class="lj-acts">${ljBtn(`data-ljstmt="${esc(c.id)}|${esc(f.pid)}"`, "Statement")}${c.sov && c.sov.length ? ljBtn(`data-ljprog="${esc(c.id)}|${esc(f.pid)}"`, "New Progress Invoice") : ""}</div></div>`,
  ).join("")}</div><div class="lj-acts" style="margin-top:6px">${ljBtn(`data-ljpayers="${esc(c.id)}"`, "Edit Payers")}</div></div>`;
}
function ljAllowanceCard(c) {
  const R = ljAllowanceRows(c);
  if (!R.length) return "";
  const pill = (s) => ({ over: '<span class="lj-pill bad">Over</span>', covered: '<span class="lj-pill ok">Covered by CO</span>', near: '<span class="lj-pill warn">Near</span>', closed: '<span class="lj-pill">Closed</span>', ok: '<span class="lj-pill ok">Within</span>' })[s] || "";
  return `<div class="lj-card lj-allow no-doc-print"><h3>Allowances</h3><p class="lj-sub">What the contract carries for each unknown, against what it is costing. Over the allowance needs a change order before the work goes on; what is not used comes back as a credit.</p><div class="lj-rows">${R.map(
    (r) =>
      `<div class="lj-row" data-ljallow="${esc(r.key)}"><div class="lj-nm"><b>${esc(r.item)}</b> ${pill(r.status)}${r.payer ? ` <span class="small muted">${esc(ljPayerName(c, r.payer))}</span>` : ""}</div>${ljKv("Allowance", money(r.price))}${ljKv("Budget", money(r.budget))}${ljKv("Spent", money(r.spent))}${ljKv("Committed", money(r.committed))}${ljKv(r.over > 0 ? "Over By" : "Left", money(Math.abs(r.over)), r.over > 0.5 ? "bad" : "")}<div class="lj-acts">${r.toCO > 0.5 ? ljBtn(`data-ljallowco="${esc(c.id)}|${esc(r.key)}"`, `Draft Change Order ${money(r.toCO)}`) : ""}${r.cos.map((x) => ljBtn(`data-ljopen="${esc(c.id)}|co|${esc(x.id)}"`, `Open ${esc(x.number)}`)).join("")}${"closed" !== r.status && r.over <= 0.5 ? ljBtn(`data-ljallowclose="${esc(c.id)}|${esc(r.key)}"`, "Close Allowance") : ""}</div></div>`,
  ).join("")}</div></div>`;
}
function ljPhaseCard(c) {
  const E = (c.estimates || []).filter((d) => d.phased && ["approved", "converted"].includes(d.status) && (d.lines || []).some((l) => 2 === +l.phase && !l.on));
  if (!E.length) return "";
  return E.map((d) => {
    const R = ljRange(d),
      P2 = d.lines.filter((l) => 2 === +l.phase && !l.on),
      found = P2.filter((l) => l.found).length;
    return `<div class="lj-card lj-phase no-doc-print"><h3>Construction Phase: Discovery</h3><p class="lj-sub">${esc(d.number)}: the exploratory phase is the contract (${money(R.p1)}). The construction phase joins it when discovery is done and the client approves it.</p><div class="lj-sum">${ljKv("Construction Range", `${money(R.p2.lo)} – ${money(R.p2.hi)}`)}${ljKv("Carried", money(R.p2.carried))}${ljKv("Lines Found", `${found} of ${P2.length}`)}</div><div class="lj-acts">${ljBtn(`data-ljopen="${esc(c.id)}|estimate|${esc(d.id)}"`, "Open Discovery")}</div></div>`;
  }).join("");
}
function ljClientPanel(c) {
  if (!c) return "";
  let h = "";
  try {
    ljMulti(c) && (h += ljPayersCard(c)), (h += ljPhaseCard(c)), (h += ljAllowanceCard(c));
  } catch (e) {
    console.warn("livejobs panel", e);
  }
  return h;
}
if ("function" == typeof renderFinTab) {
  const base = renderFinTab;
  renderFinTab = function (c, f, projs) {
    let h = base.apply(this, arguments);
    if (docOpen || !c) return h;
    const add = ljClientPanel(c),
      setup = "estimates" === finTab && !ljMulti(c) ? `<div class="lj-acts no-doc-print" style="margin:0 0 8px">${ljBtn(`data-ljpayers="${esc(c.id)}"`, "Add a Second Payer")}<span class="small muted" style="align-self:center">For a contract two parties pay, such as a landlord and a tenant.</span></div>` : "";
    // a function replacer: the panel holds dollar figures, and "$1" in a replacement string is a group reference
    return add || setup ? h.replace(/<div class="card">/, (m) => add + m + setup) : h;
  };
}

// The estimate's own panel: who pays each line, the ranges and allowances, the phases, the cost model and the tax
// credit budget. Inputs are live in a draft; after conversion only discovery and the tax credit inputs are.
function ljEstPanel(c, d) {
  const ed = "draft" === d.status,
    dis = ed ? "" : "disabled",
    multi = ljMulti(c),
    lines = (d.lines || []).filter((l) => l.item || l.desc || +l.rate),
    showRange = ljHasRanges(d) || ed,
    R = ljRange(d),
    H = d.costModel ? ljHtc(d) : null,
    num = (v) => (null == v || "" === v ? "" : +v),
    sel = (attr, opts, v, disabled) => `<select class="lj-sel" ${attr} ${disabled || ""}>${opts.map(([k, n]) => `<option value="${esc(k)}" ${String(v || "") === String(k) ? "selected" : ""}>${esc(n)}</option>`).join("")}</select>`,
    props = (d.htc && d.htc.props) || [];
  let h = `<div class="lj-card lj-est no-doc-print" data-ljest="${esc(c.id)}|${esc(d.id)}"><h3>Ranges, Phases and Payers</h3><p class="lj-sub">For the unknowns of an old building: give a line a low and high figure, carry an allowance, split the work into a paid exploratory phase and construction, and say who pays each line.</p>`;
  ed && (h += `<div class="lj-tog"><label><input type="checkbox" data-ljtog="phased" ${d.phased ? "checked" : ""} ${dis}> Paid Exploratory Phase</label><label><input type="checkbox" data-ljtog="costModel" ${d.costModel ? "checked" : ""} ${dis}> Hard, Soft and Contingency</label></div>`);
  // the totals, read three ways
  h += `<div class="lj-sum">${d.phased ? ljKv("Exploratory Phase (Contract Now)", money(R.p1)) + ljKv("Construction Range", `${money(R.p2.lo)} – ${money(R.p2.hi)}`) + ljKv("Construction Carried", money(R.p2.carried)) : ljKv("Fixed", money(R.fixed)) + (R.ranges ? ljKv("With the Unknowns", `${money(R.lo)} – ${money(R.hi)}`) : "") + ljKv("Contract Carries", money(R.carried))}${R.allowances ? ljKv("Allowances", money(R.allowances)) : ""}</div>`;
  if (d.phase2) h += `<div class="lj-note ok">Construction phase approved ${fmt(d.phase2.on)} by ${esc(d.phase2.name || "the client")} (recorded by ${esc(d.phase2.by)}): +${money(d.phase2.total)}${d.phase2.allowances ? `, ${d.phase2.allowances} line${1 === d.phase2.allowances ? "" : "s"} carried as allowances` : ""}.</div>`;
  h += `<div class="lj-rows">${lines
    .map((l) => {
      const LR = ljLineRange(l),
        off = ljPhaseOff(l, d),
        canFind = d.phased && 2 === +l.phase && !l.on && (LR.isRange || !!l.unknown) && ["approved", "converted"].includes(d.status),
        f = l.found;
      // a read-only line says what it is in words; inputs only where something can still change
      const tags = [
          multi ? ljPayerName(c, ljEstLinePayer(c, d, l)) : "",
          d.phased ? (2 === +l.phase ? "Construction" : "Exploratory") : "",
          l.unknown ? (LJ_UNKNOWNS.find((u) => u[0] === l.unknown) || ["", ""])[1] : "",
          d.costModel ? (LJ_BUCKETS.find((b) => b[0] === ljBucketOf(l)) || ["", ""])[1] : "",
          d.costModel && l.prop ? ((props.find((p) => p.id === l.prop) || {}).name || "") : "",
        ].filter(Boolean),
        ctl = ed
          ? `${multi ? `<label class="lj-field">Payer${sel(`data-ljlf="payer"`, ljPayers(c).map((p) => [p.id, p.name]), ljEstLinePayer(c, d, l))}</label>${ljBtn(`data-ljsplit="${esc(l.id)}"`, "Split")}` : ""}${d.phased ? `<label class="lj-field">Phase${sel(`data-ljlf="phase"`, [["1", "Exploratory"], ["2", "Construction"]], 2 === +l.phase ? "2" : "1")}</label>` : ""}${
              showRange
                ? `<label class="lj-field">Low<input class="lj-in" type="number" step="any" data-ljlf="lo" value="${num(l.range && l.range.lo)}" placeholder="${LR.carried}"></label><label class="lj-field">High<input class="lj-in" type="number" step="any" data-ljlf="hi" value="${num(l.range && l.range.hi)}" placeholder="${LR.carried}"></label><label class="lj-field">Unknown${sel(`data-ljlf="unknown"`, [["", "None"], ...LJ_UNKNOWNS], l.unknown)}</label><label class="lj-field">Allowance<input type="checkbox" data-ljlf="allowance" ${l.allowance ? "checked" : ""} style="width:22px;height:22px"></label>`
                : ""
            }${d.costModel ? `<label class="lj-field">Bucket${sel(`data-ljlf="bucket"`, LJ_BUCKETS, ljBucketOf(l))}</label>${props.length ? `<label class="lj-field">Property${sel(`data-ljlf="prop"`, [["", "Shared"], ...props.map((p) => [p.id, p.name])], l.prop)}</label>` : ""}` : ""}`
          : tags.map((t) => `<span class="lj-pill">${esc(t)}</span>`).join("");
      return `<div class="lj-row" data-ljline="${esc(l.id)}"><div class="lj-nm"><b>${esc(l.item || l.desc || "")}</b><div class="small muted">${money(LR.carried)}${LR.isRange ? ` · range ${money(LR.lo)} – ${money(LR.hi)}` : ""}${off ? " · not in the contract yet" : ""}${l.allowance ? " · allowance" : ""}</div></div>${ctl}${
        canFind
          ? `<div class="lj-acts" style="align-items:flex-end"><label class="lj-field">Discovery Says<input class="lj-in" type="number" step="any" data-ljfound="amt" value="${f ? f.amount : ""}"></label><label class="lj-field">What It Showed<input class="lj-in wide" data-ljfound="note" value="${esc((f && f.note) || "")}"></label>${ljBtn(`data-ljfoundsave="${esc(l.id)}"`, f ? "Update Finding" : "Record Finding")}${f && f.outside ? '<span class="lj-pill bad">Outside the Range</span>' : f ? '<span class="lj-pill ok">Within the Range</span>' : ""}</div>`
          : f
            ? `<span class="lj-pill ${f.outside ? "bad" : "ok"}">Found ${money(f.amount)}</span>`
            : ""
      }</div>`;
    })
    .join("")}</div>`;
  if (d.phased && ["approved", "converted"].includes(d.status) && (d.lines || []).some((l) => 2 === +l.phase && !l.on)) {
    const P2 = d.lines.filter((l) => 2 === +l.phase && !l.on),
      found = P2.filter((l) => l.found),
      out = found.filter((l) => l.found.outside),
      after = r2(R.p1 + P2.reduce((a, l) => a + (l.found ? +l.found.amount : ljRaw(l)), 0));
    h += `<h4>Approve the Construction Phase</h4><p class="lj-sub">${found.length} of ${P2.length} lines have a discovery figure; the rest are carried as allowances at their carried figure. The contract would become ${money(after)} (now ${money(R.p1)}).${out.length ? ` ${out.length} finding${1 === out.length ? " is" : "s are"} outside the range the client saw: tell them before they approve.` : ""}</p><div class="lj-acts"><label class="lj-field">Approved By (Client)<input class="lj-in wide" data-ljp2="name" value="${esc((c.contacts.find((x) => x.primary) || c.contacts[0] || {}).name || "")}"></label>${ljBtn(`data-ljp2go="${esc(c.id)}|${esc(d.id)}"`, "Client Approved Construction Phase")}</div>`;
  }
  if (d.costModel) {
    const M = ljCostModel(d),
      HD = d.htc || { fed: 20, qual: 98.5, props: [] },
      oldBldg = !!(DB.projects || []).find((p) => p.id === d.projectId && (p.project.lpc || /brownstone|townhouse|church|landmark|historic/i.test(p.project.name || "")));
    h += `<h4>Cost Model</h4><div class="lj-sum">${LJ_BUCKETS.map(([k, n]) => ljKv(n, money(M.B[k].price))).join("")}${ljKv("Total", money(M.total))}${ljKv("Contingency of Hard", M.contPct + "%", M.B.contingency.price ? "" : "warn")}</div>${!M.B.contingency.price && oldBldg ? '<div class="lj-note">No hidden-conditions contingency on an older building: the Standard asks for one, stated explicitly.</div>' : ""}`;
    h += `<h4>Historic Tax Credit Budget</h4><p class="lj-sub">Federal ${num(HD.fed)}% plus each property's state rate, on ${num(HD.qual)}% of hard and soft costs. Contingency is not in the basis. Credits are an estimate until the state historic office and the National Park Service certify the work.</p>`;
    h += `<div class="lj-acts" style="align-items:flex-end"><label class="lj-field">Federal %<input class="lj-in" type="number" step="any" data-ljhtc="fed" value="${num(HD.fed)}"></label><label class="lj-field">Qualified %<input class="lj-in" type="number" step="any" data-ljhtc="qual" value="${num(HD.qual)}"></label></div>`;
    h += `<div class="lj-rows">${(HD.props || [])
      .map((p) => {
        const r = H && H.rows.find((x) => x.id === p.id);
        return `<div class="lj-row" data-ljprop="${esc(p.id)}"><label class="lj-field">Property<input class="lj-in wide" data-ljpf="name" value="${esc(p.name)}"></label><label class="lj-field">State Credit %<input class="lj-in" type="number" step="any" data-ljpf="state" value="${num(p.state)}"></label><label class="lj-field">Area (SF)<input class="lj-in" type="number" step="any" data-ljpf="sf" value="${num(p.sf)}"></label><label class="lj-field">Finish per SF<input class="lj-in" type="number" step="any" data-ljpf="finishPerSf" value="${num(p.finishPerSf)}"></label>${r ? ljKv("Hard", money(r.hard)) + ljKv("Soft", money(r.soft)) + ljKv("Basis", money(r.basis)) + ljKv("Federal", money(r.fedCredit)) + ljKv("State", money(r.stateCredit)) + ljKv("Net After Credits", money(r.net)) : ""}</div>`;
      })
      .join("")}</div>`;
    H && (h += `<div class="lj-sum lj-htc-tot">${ljKv("Hard and Soft", money(r2(H.T.hard + H.T.soft)))}${ljKv("Qualified Basis", money(H.T.basis))}${ljKv("Federal Credit", money(H.T.fedCredit))}${ljKv("State Credit", money(H.T.stateCredit))}${ljKv("Total Credits", money(H.T.credits))}${ljKv("Net Cost After Credits", money(H.T.net))}</div>`);
    const p = (DB.projects || []).find((x) => x.id === d.projectId);
    h += `<div class="lj-acts" style="margin-top:6px">${ljBtn(`data-ljaddprop="${esc(c.id)}|${esc(d.id)}"`, "Add Property")}${ed && (HD.props || []).some((q) => +q.sf > 0 && +q.finishPerSf > 0) ? ljBtn(`data-ljfinish="${esc(c.id)}|${esc(d.id)}"`, "Price Finish Materials") : ""}${p ? `<label style="display:flex;align-items:center;gap:6px;font-size:13px;min-height:32px"><input type="checkbox" data-ljmb="${esc(p.id)}" ${p.mbDeal ? "checked" : ""} style="width:auto"> Also a Mercer &amp; Bond Deal</label>` : ""}</div>${p && p.mbDeal ? `<div class="lj-note">Mercer &amp; Bond deal: the client pays all costs; Mercer &amp; Bond is preparing an all-cash LOI${p.mbDeal.loiStatus ? ` (${esc(p.mbDeal.loiStatus)})` : ""}.</div>` : ""}`;
  }
  return h + "</div>";
}
// What the client reads on a proposal: the range, the allowances and the phases in plain words.
function ljClientSummary(c, d) {
  if (!d || "estimate" !== d.type || !(d.phased || ljHasRanges(d) || d.costModel)) return "";
  const R = ljRange(d),
    rng = (d.lines || []).filter((l) => ljLineRange(l).isRange),
    allw = (d.lines || []).filter((l) => l.allowance && !ljPhaseOff(l, d)),
    H = d.costModel ? ljHtc(d) : null;
  let h = '<div class="card lj-client" style="margin-top:10px">';
  d.phased &&
    (h += `<h3 style="margin:0 0 6px">Two Phases</h3><div class="small">Phase 1, exploratory: ${money(R.p1)}, a fixed fee. We open up, test and survey so the unknowns below become numbers. Phase 2, construction: between ${money(R.p2.lo)} and ${money(R.p2.hi)} today; once discovery is done we price it and you approve it before it starts.</div>`);
  rng.length &&
    (h += `<h3 style="margin:10px 0 6px">The Unknowns, as Ranges</h3><table class="t"><thead><tr><th>Item</th><th class="money">Low</th><th class="money">High</th></tr></thead><tbody>${rng.map((l) => `<tr><td>${esc(l.item)}${l.found ? `<div class="small muted">Discovery: ${money(l.found.amount)}${l.found.note ? ", " + esc(l.found.note) : ""}</div>` : ""}</td><td class="money">${money(ljLineRange(l).lo)}</td><td class="money">${money(ljLineRange(l).hi)}</td></tr>`).join("")}</tbody></table>`);
  allw.length &&
    (h += `<h3 style="margin:10px 0 6px">Allowances</h3><div class="small">${allw.map((l) => `${esc(l.item)}: ${money(lineAmount(l, d))}`).join("<br>")}</div><div class="small muted" style="margin-top:4px">An allowance is the amount the contract carries. If the real cost is higher we send a change order for the difference before the work goes on; if it is lower you get the difference back as a credit.</div>`);
  H &&
    (h += `<h3 style="margin:10px 0 6px">Budget and Tax Credits</h3><table class="t"><thead><tr><th>Property</th><th class="money">Budget</th><th class="money">Credits</th><th class="money">Net</th></tr></thead><tbody>${H.rows.map((r) => `<tr><td>${esc(r.name)}</td><td class="money">${money(r.total)}</td><td class="money">${money(r.credits)}</td><td class="money">${money(r.net)}</td></tr>`).join("")}</tbody></table><div class="small muted">Federal ${H.fed}% and the state's rate on ${H.qual}% of hard and soft costs; an estimate until the work is certified.</div>`);
  return h + "</div>";
}
if ("function" == typeof docSummaryHtml) {
  const base = docSummaryHtml;
  docSummaryHtml = function (c, d) {
    const h = base.apply(this, arguments);
    try {
      return h + ljClientSummary(c, d);
    } catch (e) {
      return h;
    }
  };
}
// The invoice and change-order editors on a two-payer contract: who it is for, and the split an invoice needs.
function ljDocStrip(c, d) {
  if (!ljMulti(c)) return "";
  if ("invoice" === d.type) {
    const p = ljInvPayer(c, d),
      ed = "draft" === d.status;
    if ("mixed" === p)
      return `<div class="lj-note no-doc-print lj-mixed">This invoice holds lines for ${ljInvPayers(c, d).map((x) => esc(ljPayerName(c, x))).join(" and ")}. Each payer gets their own invoice. <button class="btn sm" data-ljsplitinv="${esc(c.id)}|${esc(d.id)}">Split by Payer</button></div>`;
    return `<div class="lj-acts no-doc-print lj-billto" style="margin:0 0 8px;align-items:center"><span class="small">Bill to payer: <b>${esc(ljPayerName(c, p))}</b> (${esc((ljPayerById(c, p) || {}).role || "")})</span>${ed && "sov" !== d.mode ? `<select class="lj-sel" data-ljinvpayer="${esc(c.id)}|${esc(d.id)}">${ljPayers(c).map((x) => `<option value="${esc(x.id)}" ${x.id === p ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select>` : ""}</div>`;
  }
  if ("co" === d.type)
    return `<div class="lj-acts no-doc-print lj-billto" style="margin:0 0 8px;align-items:center"><span class="small">Paid by: <b>${esc(ljPayerName(c, ljCoPayer(c, d)))}</b></span>${"draft" === d.status ? `<select class="lj-sel" data-ljcopayer="${esc(c.id)}|${esc(d.id)}">${ljPayers(c).map((x) => `<option value="${esc(x.id)}" ${x.id === ljCoPayer(c, d) ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select>` : ""}</div>`;
  return "";
}
if ("function" == typeof renderDocEditor) {
  const base = renderDocEditor;
  renderDocEditor = function (c, d) {
    let h = base.apply(this, arguments);
    if (!c || !d) return h;
    try {
      if (ljMulti(c) && ("invoice" === d.type || "co" === d.type)) {
        const pid = "invoice" === d.type ? ljInvPayer(c, d) : ljCoPayer(c, d),
          P = "mixed" !== pid && ljPayerById(c, pid);
        P && (h = h.replace(`Bill to: <b>${esc(c.name)}</b>`, () => `Bill to: <b>${esc(P.name)}</b>`));
        const strip = ljDocStrip(c, d);
        h = h.replace(/<div class="dochd">/, (m) => strip + m);
      }
      if ("estimate" === d.type && ljCanMoney()) {
        const panel = ljEstPanel(c, d);
        h = h.replace(/<div class="docacts">/, (m) => panel + m);
      }
    } catch (e) {
      console.warn("livejobs editor", e);
    }
    return h;
  };
}

// The payer editor: names, role, who to write to.
function ljPayersDialog(c) {
  const P = ljPayers(c).length
      ? ljPayers(c).map((p) => Object.assign({}, p))
      : [
          { id: uid("pay"), name: c.name, role: "Owner", email: ((c.contacts || []).find((x) => x.primary) || (c.contacts || [])[0] || {}).email || "", contact: ((c.contacts || []).find((x) => x.primary) || (c.contacts || [])[0] || {}).name || "", addr: c.billingAddr || "" },
          { id: uid("pay"), name: "", role: "Tenant", email: "", contact: "", addr: "" },
        ],
    ROLES = ["Owner", "Landlord", "Tenant", "Lender", "Other"],
    row = (p, i) =>
      `<div class="lj-row" data-ljpi="${i}"><label class="lj-field">Payer Name<input class="lj-in wide" data-ljpe="name" value="${esc(p.name)}"></label><label class="lj-field">Role<select class="lj-sel" data-ljpe="role">${ROLES.map((r) => `<option ${r === p.role ? "selected" : ""}>${r}</option>`).join("")}</select></label><label class="lj-field">Contact<input class="lj-in wide" data-ljpe="contact" value="${esc(p.contact || "")}"></label><label class="lj-field">Email<input class="lj-in wide" type="email" data-ljpe="email" value="${esc(p.email || "")}"></label><label class="lj-field">Billing Address<input class="lj-in wide" data-ljpe="addr" value="${esc(p.addr || "")}"></label></div>`,
    m = mbModal(
      "Payers on This Contract",
      `<p class="small muted">Each payer is billed for their own lines and has their own invoices, aging and statement. Lines with no payer set are the first payer's.</p><div class="lj-rows" id="lj-pe">${P.map(row).join("")}</div>`,
      {
        submit: "Save Payers",
        onSubmit: () => {
          const out = [];
          m.querySelectorAll("[data-ljpi]").forEach((r) => {
            const o = Object.assign({}, P[+r.dataset.ljpi]);
            r.querySelectorAll("[data-ljpe]").forEach((i) => (o[i.dataset.ljpe] = String(i.value || "").trim()));
            o.name && out.push(o);
          });
          if (out.length < 2) return toast("Name both payers: a shared contract has two"), !1;
          const before = (c.payers || []).map((p) => p.name).join(", ");
          (c.payers = out), c.activity.push({ t: nowStamp(), by: ljWho(), text: `Payers: ${out.map((p) => `${p.name} (${p.role})`).join(", ")}` });
          try {
            audit("client", c.id, "payers-set", before, out.map((p) => p.name).join(", "));
          } catch (e) {}
          ljSync(), save(), render(), toastDone(`${c.name}: ${out.length} payers on the contract`, () => ((clientOpen = c.id), (clientTab = "fin"), (docOpen = null), (view = "clients"), render()));
        },
      },
    );
}
// A line two payers share becomes two lines, one each, at the share given (cost split the same way).
function ljSplitLine(c, d, lineId, pct) {
  const i = d.lines.findIndex((x) => x.id === lineId),
    l = d.lines[i];
  if (!l || !ljMulti(c)) return null;
  const P = ljPayers(c),
    a = Math.max(0, Math.min(100, +pct || 50)) / 100,
    amt = ljRaw(l),
    cost = +l.cost || 0,
    first = Object.assign({}, l, { id: uid("l"), item: `${l.item} (${P[0].role || P[0].name} share)`, qty: 1, unit: "ls", rate: r2(amt * a), cost: cost ? r2(cost * a) : l.cost, payer: P[0].id, splitOf: l.id }),
    second = Object.assign({}, l, { id: uid("l"), item: `${l.item} (${P[1].role || P[1].name} share)`, qty: 1, unit: "ls", rate: r2(amt - r2(amt * a)), cost: cost ? r2(cost - r2(cost * a)) : l.cost, payer: P[1].id, splitOf: l.id });
  return d.lines.splice(i, 1, first, second), [first, second];
}

// ---- 9. One listener for every control above ---------------------------------------------------------------------
const ljDocOf = (cid, did, kind) => {
  const c = (DB.clients || []).find((x) => x.id === cid);
  return { c: c, d: c && findDoc(c, kind || "estimate", did) };
};
document.addEventListener("click", (e) => {
  const t = e.target.closest && e.target.closest("[data-ljstmt],[data-ljprog],[data-ljpayers],[data-ljallowco],[data-ljallowclose],[data-ljopen],[data-ljsplit],[data-ljfoundsave],[data-ljp2go],[data-ljaddprop],[data-ljfinish],[data-ljsplitinv],[data-ljdemo],[data-ljconvert],[data-ljloghrs]");
  if (!t) return;
  const D = t.dataset;
  try {
    if (D.ljstmt) {
      const [cid, pid] = D.ljstmt.split("|"),
        c = DB.clients.find((x) => x.id === cid);
      return void (c && ljOpenStatement(c, pid));
    }
    if (D.ljpayers) {
      const c = DB.clients.find((x) => x.id === D.ljpayers);
      return void (c && ljPayersDialog(c));
    }
    if (D.ljprog) {
      const [cid, pid] = D.ljprog.split("|"),
        c = DB.clients.find((x) => x.id === cid);
      if (!c) return;
      LJ.pick = pid;
      let inv;
      try {
        inv = newDoc(c, "invoice", { mode: "sov", payer: pid });
      } finally {
        LJ.pick = "";
      }
      return (clientOpen = c.id), (clientTab = "fin"), (docOpen = { kind: "invoice", id: inv.id }), (finTab = "invoices"), save(), render(), void toastDone(`${inv.number} for ${ljPayerName(c, pid)}: enter this period's % per line`, flowGo.doc(c, "invoice", inv));
    }
    if (D.ljopen) {
      const [cid, kind, id] = D.ljopen.split("|");
      return (clientOpen = cid), (clientTab = "fin"), (docOpen = { kind: kind, id: id }), (view = "clients"), void render();
    }
    if (D.ljallowco) {
      const [cid, key] = D.ljallowco.split("|"),
        c = DB.clients.find((x) => x.id === cid),
        r = c && ljAllowanceCO(c, key);
      if (!r || !r.ok) return void toast((r && r.why) || "Not found");
      return save(), render(), void toastDone(`${r.co.number} drafted: ${money(r.amount)} over the allowance. Review it and send it to the client`, flowGo.doc(c, "co", r.co));
    }
    if (D.ljallowclose) {
      const [cid, key] = D.ljallowclose.split("|"),
        c = DB.clients.find((x) => x.id === cid),
        r = c && ljAllowanceClose(c, key);
      if (!r || !r.ok) return void toast((r && r.why) || "Not found");
      return save(), render(), void (r.co ? toastDone(`Allowance closed; ${r.co.number} drafted to credit the client ${money(-docTotal(r.co).total)}`, flowGo.doc(c, "co", r.co)) : toast("Allowance closed: it was used in full"));
    }
    if (D.ljsplitinv) {
      const [cid, id] = D.ljsplitinv.split("|"),
        { c, d } = ljDocOf(cid, id, "invoice");
      return void (c && d && (ljSplitInvoice(c, d), save(), render()));
    }
    const box = t.closest("[data-ljest]");
    if (box) {
      const [cid, did] = box.dataset.ljest.split("|"),
        { c, d } = ljDocOf(cid, did);
      if (!c || !d) return;
      if (D.ljsplit) {
        const pct = appPrompt(`What share of this line does ${ljPayers(c)[0].name} pay, in percent? The rest is ${ljPayers(c)[1].name}'s.`, "50", { title: "Split the Line", label: "Share (%)" });
        if (null == pct) return;
        const two = ljSplitLine(c, d, D.ljsplit, pct);
        return void (two && (save(), render(), toast(`Split: ${money(two[0].rate)} ${ljPayers(c)[0].name}, ${money(two[1].rate)} ${ljPayers(c)[1].name}`)));
      }
      if (D.ljfoundsave) {
        const row = t.closest("[data-ljline]"),
          amt = row.querySelector('[data-ljfound="amt"]').value,
          note = row.querySelector('[data-ljfound="note"]').value,
          r = ljFound(c, d, D.ljfoundsave, amt, note);
        if (!r.ok) return void toast(r.why);
        return save(), render(), void toastDone(`${r.l.item}: discovery says ${money(r.l.found.amount)}${r.outside ? ", outside the range the client saw: tell them before the construction phase is priced" : ", within the range"}`, flowGo.doc(c, "estimate", d));
      }
      if (D.ljp2go) {
        const name = (box.querySelector('[data-ljp2="name"]') || {}).value || "",
          r = ljApprovePhase2(c, d, { name: name.trim() });
        if (!r.ok) return void toast(r.why);
        return save(), render(), void toastDone(`${d.number}: construction phase approved, contract now ${money(c.contract)} (+${money(r.add)})`, flowGo.doc(c, "estimate", d));
      }
      if (D.ljaddprop) {
        const H = ljHtcDefaults(d);
        return H.props.push({ id: uid("pr"), name: `Property ${H.props.length + 1}`, state: 20, sf: 0, finishPerSf: 0 }), save(), void render();
      }
      if (D.ljfinish) {
        const n = ljFinishLines(c, d);
        return save(), render(), void toast(n ? `Finish materials priced on ${n} line${1 === n ? "" : "s"}: ${money(d.lines.filter((l) => l.ljFinish).reduce((a, l) => a + lineAmount(l, d), 0))}` : "Give each property its area and finish price per SF first");
      }
    }
    if (D.ljdemo) return void ljDemoSwitch("on" === D.ljdemo);
    if (D.ljconvert) return void ljConvertDialog(D.ljconvert);
    if (D.ljloghrs) return void ljLogHours();
  } catch (err) {
    console.warn("livejobs click", err), toast("That did not work: " + (err.message || err));
  }
});
document.addEventListener("change", (e) => {
  const t = e.target;
  if (!t || !t.closest) return;
  try {
    if (t.dataset.ljinvpayer || t.dataset.ljcopayer) {
      const [cid, id] = (t.dataset.ljinvpayer || t.dataset.ljcopayer).split("|"),
        kind = t.dataset.ljinvpayer ? "invoice" : "co",
        { c, d } = ljDocOf(cid, id, kind);
      if (!c || !d || "draft" !== d.status) return;
      d.payer = t.value;
      "invoice" === kind && (d.lines || []).forEach((l) => l.sovId || l.fromLine || (l.payer = t.value));
      return save(), void render();
    }
    const mb = t.dataset.ljmb;
    if (mb) {
      const p = DB.projects.find((x) => x.id === mb);
      return p && ((p.mbDeal = t.checked ? { clientPaysAll: !0, loi: "all-cash", loiStatus: "being prepared", at: appNowIso(), by: ljWho() } : null), audit("project", p.id, t.checked ? "mb-deal-on" : "mb-deal-off"), save(), render()), void 0;
    }
    const box = t.closest("[data-ljest]");
    if (!box) return;
    const [cid, did] = box.dataset.ljest.split("|"),
      { c, d } = ljDocOf(cid, did);
    if (!c || !d) return;
    if (t.dataset.ljtog) {
      if ("draft" !== d.status) return;
      d[t.dataset.ljtog] = t.checked || void 0;
      "phased" === t.dataset.ljtog && t.checked && d.lines.forEach((l) => l.phase || (l.phase = l.range || l.unknown ? 2 : 1));
      "costModel" === t.dataset.ljtog && t.checked && ljHtcDefaults(d);
      return save(), void render();
    }
    if (t.dataset.ljhtc) {
      const H = ljHtcDefaults(d);
      return (H[t.dataset.ljhtc] = +t.value || 0), save(), void render();
    }
    if (t.dataset.ljpf) {
      const H = ljHtcDefaults(d),
        p = H.props.find((x) => x.id === t.closest("[data-ljprop]").dataset.ljprop);
      return p && ((p[t.dataset.ljpf] = "name" === t.dataset.ljpf ? t.value : +t.value || 0), save(), render()), void 0;
    }
    const f = t.dataset.ljlf;
    if (f) {
      if ("draft" !== d.status) return;
      const l = d.lines.find((x) => x.id === t.closest("[data-ljline]").dataset.ljline);
      if (!l) return;
      if ("lo" === f || "hi" === f) {
        l.range = l.range || {};
        l.range[f] = "" === t.value ? "" : +t.value;
        "" === l.range.lo && "" === l.range.hi && delete l.range;
        l.range && null != l.range.lo && null != l.range.hi && "" !== l.range.lo && "" !== l.range.hi && !l.unknown && (l.unknown = "hidden");
      } else "allowance" === f ? (l.allowance = t.checked || void 0) : "phase" === f ? (l.phase = +t.value) : (l[f] = t.value || void 0);
      return save(), void render();
    }
  } catch (err) {
    console.warn("livejobs change", err);
  }
});

// ---- 10. The contractor's own screens and the conversion ------------------------------------------------------
function ljMyEmp() {
  const u = "function" == typeof currentUser ? currentUser() : null;
  return u && u.employeeId ? ljEmp(u.employeeId) : null;
}
// What a contractor sees on their Today: their hours this period, what is on their bill, what was paid.
function ljMyHoursCard(emp) {
  const P = payPeriodOf(today()),
    mine = (DB.time || []).filter((e) => e.empId === emp.id).sort((a, b) => String(b.date).localeCompare(a.date)),
    per = mine.filter((e) => e.date >= P.from && e.date <= P.to),
    bills = (DB.bills || []).filter((b) => b.fromTime && b.empId === emp.id).sort((a, b) => String(b.date).localeCompare(a.date)),
    sum = (L) => r2(L.reduce((a, e) => a + hoursOf(e), 0)),
    st = (s) => ({ submitted: "Waiting for Approval", approved: "Approved", rejected: "Sent Back" })[s] || s,
    bst = (b) => ("paid" === b.status ? "Paid" : ["approved", "verified"].includes(b.status) ? "Approved for Payment" : "Waiting for Approval");
  return `<div class="lj-card lj-myhours" id="lj-myhours"><h3>My Hours</h3><p class="lj-sub">You work with us as an independent contractor at ${money(emp.contractRate)}/h. Approved hours become your bill to us, paid through payables, not payroll.</p><div class="lj-sum">${ljKv("This Period", `${sum(per).toFixed(2)} h`)}${ljKv("Waiting for Approval", `${sum(mine.filter((e) => "submitted" === e.status)).toFixed(2)} h`)}${ljKv("On Your Bills", money(r2(bills.filter((b) => "paid" !== b.status).reduce((a, b) => a + billGross(b), 0))))}${ljKv("Paid", money(r2(bills.filter((b) => "paid" === b.status).reduce((a, b) => a + billGross(b), 0))))}</div><div class="lj-acts" style="margin:6px 0">${ljBtn("data-ljloghrs=1", "Log Hours", "primary")}</div><div class="lj-rows">${mine
    .slice(0, 6)
    .map((e) => `<div class="lj-row"><div class="lj-nm"><b>${fmt(e.date)} · ${hoursOf(e).toFixed(2)} h</b><div class="small muted">${esc(((DB.projects || []).find((p) => p.id === e.projectId) || { project: { name: "" } }).project.name)}${e.notes ? " · " + esc(e.notes) : ""}</div></div><span class="lj-pill ${"approved" === e.status ? "ok" : "rejected" === e.status ? "bad" : ""}">${st(e.status)}</span>${e.billId ? `<span class="small muted">on ${esc(((DB.bills || []).find((b) => b.id === e.billId) || {}).number || "")}</span>` : ""}</div>`)
    .join("")}</div>${bills.length ? `<h4>My Bills</h4><div class="lj-rows">${bills.map((b) => `<div class="lj-row"><div class="lj-nm"><b>${esc(b.number)}</b><div class="small muted">${fmt(b.period.from)} – ${fmt(b.period.to)} · ${(+b.hours).toFixed(2)} h</div></div>${ljKv("Amount", money(billGross(b)))}<span class="lj-pill ${"paid" === b.status ? "ok" : ""}">${bst(b)}</span></div>`).join("")}</div>` : ""}</div>`;
}
function ljLogHours() {
  const emp = ljMyEmp();
  if (!emp) return void toast("Your sign-in is not linked to a person who logs hours");
  const jobs = (DB.projects || []).filter((p) => !p.archived),
    codes = (DB.time || []).filter((e) => e.empId === emp.id && e.code).map((e) => e.code),
    code = codes.length ? codes[codes.length - 1] : "15",
    m = mbModal(
      "Log Hours",
      `<label class="f"><span>Job</span><select id="lj-h-job">${jobs.map((p) => `<option value="${esc(p.id)}" ${S && S.id === p.id ? "selected" : ""}>${esc(p.project.name)}</option>`).join("")}</select></label><div class="f2"><label class="f"><span>Date</span><input type="date" id="lj-h-date" value="${today()}"></label><label class="f"><span>Hours</span><input type="number" step="0.25" min="0.25" id="lj-h-hrs" inputmode="decimal" value=""></label></div><label class="f"><span>What You Worked On</span><input id="lj-h-note" placeholder="e.g. kitchen elevations, finish schedule"></label>`,
      {
        submit: "Submit Hours",
        onSubmit: () => {
          const h = r2(+$("#lj-h-hrs").value || 0),
            date = $("#lj-h-date").value || today(),
            pid = $("#lj-h-job").value;
          if (!(h > 0)) return toast("Enter the hours"), !1;
          if (date > today()) return toast("Hours are logged for a day that has happened"), !1;
          const mins = Math.round(h * 60),
            start = new Date(`${date}T09:00:00`),
            end = new Date(start.getTime() + mins * 6e4),
            pad = (n) => String(n).padStart(2, "0"),
            out = `${date}T${pad(end.getHours())}:${pad(end.getMinutes())}:00`,
            e = { id: uid("te"), empId: emp.id, date: date, in: `${date}T09:00:00`, out: out, breakMin: 0, projectId: pid, code: code, notes: $("#lj-h-note").value.trim(), status: "submitted", source: "contractor", work: [{ projectId: pid, code: code, hours: h, note: "" }] };
          emp.ljDemo && (e.ljDemo = 1), DB.time.push(e);
          try {
            audit("time", e.id, "logged", null, { hours: h, projectId: pid });
          } catch (x) {}
          save(), render(), toastDone(`${h.toFixed(2)} h on ${fmt(date)} sent for approval`, () => ((view = (MENU.designer || {}).home || view), render()));
        },
      },
    );
  return m;
}
function ljConvertDialog(empId) {
  const old = ljEmp(empId);
  if (!old) return;
  mbModal(
    `Convert ${esc(old.name)} to an Employee`,
    `<p class="small muted">${esc(old.name)} works as a contractor at ${money(old.contractRate)}/h. From the date below their hours go to payroll at the wage set here. Their contractor hours and bills stay exactly as they are, on the contractor record.</p><div class="f2"><label class="f"><span>Employee From</span><input type="date" id="lj-c-eff" value="${today()}"></label><label class="f"><span>Hourly Wage</span><input type="number" step="0.01" id="lj-c-rate" inputmode="decimal"></label></div><div class="f2"><label class="f"><span>Burden %</span><input type="number" step="0.5" id="lj-c-burden" value="20"></label><label class="f"><span>Entity</span><select id="lj-c-ent">${(DB.entities || []).map((x) => `<option value="${esc(x.id)}" ${x.id === (old.entityId || "ent1") ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select></label></div>`,
    {
      submit: "Convert to Employee",
      onSubmit: () => {
        const r = ljConvertToEmployee(empId, { effective: $("#lj-c-eff").value || today(), rate: +$("#lj-c-rate").value, burden: +$("#lj-c-burden").value, entityId: $("#lj-c-ent").value });
        if (!r.ok) return toast(r.why), !1;
        save(), render(), toastDone(`${old.name} is an employee from ${fmt(r.emp.since)}; the contractor history stays${r.moved ? `, ${r.moved} later entr${1 === r.moved ? "y" : "ies"} moved to payroll` : ""}`, () => "function" == typeof employeesDialog && employeesDialog());
      },
    },
  );
}
// The people list (Employees) says who is a contractor, and offers the conversion there.
function ljContractorsHtml() {
  const C = (DB.employees || []).filter((e) => ljIsContractor(e) || e.convertedFrom);
  if (!C.length) return "";
  return `<div class="lj-card" id="lj-contractors" style="margin-top:12px"><h3>Contractors</h3><p class="lj-sub">Paid by bill from approved hours (1099), not payroll.</p><div class="lj-rows">${C.map((e) => {
    const v = (DB.vendors || []).find((x) => x.id === e.vendorId);
    return ljIsContractor(e)
      ? `<div class="lj-row"><div class="lj-nm"><b>${esc(e.name)}</b><div class="small muted">${esc(e.role || "")} · ${money(e.contractRate)}/h · paid as ${esc((v && v.name) || "a vendor")}${v && !v.w9 ? " · W-9 missing" : ""}${e.until ? ` · until ${fmt(e.until)}` : ""}</div></div>${e.active ? ljBtn(`data-ljconvert="${esc(e.id)}"`, "Convert to Employee") : '<span class="lj-pill">Converted</span>'}</div>`
      : `<div class="lj-row"><div class="lj-nm"><b>${esc(e.name)}</b><div class="small muted">Employee since ${fmt(e.since)}; contractor before</div></div><span class="lj-pill ok">Employee</span></div>`;
  }).join("")}</div></div>`;
}
if ("function" == typeof employeesDialog) {
  const base = employeesDialog;
  employeesDialog = function () {
    const r = base.apply(this, arguments),
      body = document.getElementById("d-body"),
      put = () => {
        if (!body || !body.isConnected || "employees" !== (("undefined" != typeof editing && editing) || {}).kind) return void (obs && obs.disconnect());
        body.querySelector("#lj-contractors") || body.insertAdjacentHTML("beforeend", ljContractorsHtml());
      };
    let obs = null;
    if (body && ljContractorsHtml()) put(), (obs = new MutationObserver(put)).observe(body, { childList: !0 });
    return r;
  };
}

// ---- 11. The demo: four invented jobs and a contractor, behind one switch (owner, Settings) -------------------
// Off by default: every other suite and the figures HANDOFF.md pins see the firm exactly as before. Everything the demo
// adds carries an lj id or ljDemo, so turning it off removes exactly what it added.
const LJ_IDS = { clients: ["cl_lj_atl", "cl_lj_rug", "cl_lj_mac", "cl_lj_grace"], projects: ["p_lj_atl", "p_lj_rug", "p_lj_mac", "p_lj_grace"], users: ["u_lj_rosa", "u_lj_owen", "u_lj_shah", "u_lj_dana"], emp: "em_lj_dana" };
const ljIsDemo = (x) => !!(x && (x.ljDemo || /^(cl|p|u|em)_lj_/.test(String(x.id || ""))));
function ljDemoOn() {
  return !!(DB.company && DB.company.liveJobsDemo);
}
async function ljDemoSeed() {
  if (sdSeedsOff()) return { ok: !1, why: "The firm's own records are live here; the demo is not loaded over them" };
  if ((DB.clients || []).some((c) => "cl_lj_atl" === c.id)) return { ok: !0, already: !0 };
  const acct = ("function" == typeof payBankAccts && (payBankAccts()[0] || {}).id) || "",
    quiet = "undefined" != typeof flowQuiet;
  const keepOpen = [clientOpen, docOpen, finTab, LJ.pick];
  const mkLine = (item, rate, cost, x) => Object.assign({ id: uid("l"), item: item, desc: "", qty: 1, unit: "ls", rate: rate, taxable: !1, cost: cost }, x || {});
  const mkClient = (id, name, contacts, extra) => {
    const c = Object.assign(blankClient(name), { id: id, contacts: contacts, ljDemo: 1 }, extra || {});
    return (c.billingAddr = c.billingAddr || c.propertyAddr), DB.clients.push(c), c;
  };
  const mkJob = (id, c, name, addr, start, extra) => {
    const p = blankProject(name, addr, start, "");
    return (p.id = id), (p.clientId = c.id), (p.entityId = "ent1"), (p.ljDemo = 1), Object.assign(p.project, extra || {}), DB.projects.push(p), p;
  };
  const pay = (c, inv, date, amount, method, ref) => {
    c.payments.push(payStamp({ id: uid("py"), invoiceId: inv.id, date: date, amount: r2(amount), note: "", ljDemo: 1 }, { method: method, ref: ref, acct: acct }));
    const paid = invoicePaid(c, inv);
    inv.status = paid >= docTotal(inv).total - 0.005 ? "paid" : "partial";
  };
  const send = async (c, d, date, due) => {
    (d.date = date), due && (d.due = due), docMark(d), await docAction(c, d, "send"), (d.date = date), due && (d.due = due), (d.dateRec = date);
  };
  const progress = (c, pid, title, date, due, pcts) => {
    LJ.pick = pid;
    let inv;
    try {
      inv = newDoc(c, "invoice", { mode: "sov", payer: pid });
    } finally {
      LJ.pick = "";
    }
    (inv.template = "construction"), (inv.title = title), (inv.date = date), (inv.due = due), (inv.ljDemo = 1);
    inv.lines.forEach((l) => {
      const sv = c.sov.find((v) => v.id === l.sovId),
        k = Object.keys(pcts).find((w) => sv && sv.desc.includes(w));
      l.pct = void 0 !== k ? pcts[k] : 0;
      l.prevPct = r2(sovBilled(c, l.sovId, inv.id));
    });
    return (inv.lines = inv.lines.filter((l) => l.pct > 0)), docMark(inv), inv;
  };
  // 1. Two payers: a landlord's base building and a tenant's bakery fit-out on one contract
  const A = mkClient("cl_lj_atl", "Atlantic Row Holdings LLC", [{ id: "ct_lj_a1", name: "Rosa Delgado", email: "rosa@atlanticrow.example", phone: "(718) 555-0131", role: "Owner's representative", primary: !0 }], {
    type: "Commercial landlord",
    propertyAddr: "88 Atlantic Avenue, Brooklyn, NY 11201",
    payers: [
      { id: "pay_lj_l", name: "Atlantic Row Holdings LLC", role: "Landlord", contact: "Rosa Delgado", email: "rosa@atlanticrow.example", addr: "300 Court Street, Brooklyn, NY 11231" },
      { id: "pay_lj_t", name: "Morning Loaf Bakery Inc.", role: "Tenant", contact: "Owen Park", email: "owen@morningloaf.example", addr: "88 Atlantic Avenue, Brooklyn, NY 11201" },
    ],
  });
  const pA = mkJob("p_lj_atl", A, "88 Atlantic Ave — storefront and bakery fit-out", A.propertyAddr, "2026-08-03");
  clientOpen = A.id;
  const eA = newDoc(A, "estimate", { template: "construction", fields: { title: "Base building and bakery fit-out", projectId: pA.id, date: "2026-07-20" } });
  eA.ljDemo = 1;
  eA.lines = [
    mkLine("Storefront and facade restoration", 64e3, 49e3, { payer: "pay_lj_l" }),
    mkLine("Electrical service upgrade to 400A", 38500, 29500, { payer: "pay_lj_l" }),
    mkLine("Sprinkler and fire alarm", 27e3, 21e3, { payer: "pay_lj_l" }),
    mkLine("Bakery fit-out: walls, floors and ceilings", 72e3, 55e3, { payer: "pay_lj_t" }),
    mkLine("Kitchen plumbing and grease interceptor", 31500, 24e3, { payer: "pay_lj_t" }),
    mkLine("Ovens, hoods and make-up air", 46e3, 36500, { payer: "pay_lj_t" }),
    mkLine("General conditions and supervision", 18e3, 14e3),
  ];
  ljSplitLine(A, eA, eA.lines[6].id, 50);
  docMark(eA), await send(A, eA, "2026-07-20"), await docAction(A, eA, "approve");
  const depL = progress(A, "pay_lj_l", "Construction deposit · Atlantic Row Holdings LLC", "2026-08-03", "2026-08-10", { "": 20 }),
    depT = progress(A, "pay_lj_t", "Construction deposit · Morning Loaf Bakery Inc.", "2026-08-03", "2026-08-10", { "": 20 });
  (depL.depositOf = depT.depositOf = eA.id), (depL.retainagePct = depT.retainagePct = 0), docMark(depL), docMark(depT);
  await send(A, depL, "2026-08-03", "2026-08-10"), await send(A, depT, "2026-08-03", "2026-08-10");
  pay(A, depL, "2026-08-07", docTotal(depL).total, "Wire", "ARH-0807"), pay(A, depT, "2026-08-12", docTotal(depT).total, "Check", "1043");
  const prL = progress(A, "pay_lj_l", "Progress billing #1 · Atlantic Row Holdings LLC", "2026-08-25", "2026-09-01", { Storefront: 30, Electrical: 40, Sprinkler: 10, "General conditions": 25 }),
    prT = progress(A, "pay_lj_t", "Progress billing #1 · Morning Loaf Bakery Inc.", "2026-08-25", "2026-09-01", { "Bakery fit-out": 20, "Kitchen plumbing": 35, "General conditions": 25 });
  (prL.retainagePct = prT.retainagePct = 10), docMark(prL), docMark(prT);
  await send(A, prL, "2026-08-25", "2026-09-01"), await send(A, prT, "2026-08-25", "2026-09-01");
  pay(A, prL, "2026-09-02", docTotal(prL).total, "ACH", "ARH-0902");
  // 2. A paid exploratory phase, then construction priced in ranges for the unknowns
  const B = mkClient("cl_lj_rug", "Ada & Tunde Okafor", [{ id: "ct_lj_b1", name: "Ada Okafor", email: "ada.okafor@example.com", phone: "(347) 555-0166", role: "Owner — decisions", primary: !0 }], { propertyAddr: "17 Rugby Road, Brooklyn, NY 11226" });
  const pB = mkJob("p_lj_rug", B, "17 Rugby Road — house renovation", B.propertyAddr, "2026-08-10", { lpc: "Prospect Park South Historic District" });
  clientOpen = B.id;
  const eB = newDoc(B, "estimate", { template: "construction", fields: { title: "Exploratory phase and renovation", projectId: pB.id, date: "2026-07-28" } });
  Object.assign(eB, { ljDemo: 1, phased: !0, costModel: !0 });
  eB.lines = [
    mkLine("Exploratory demolition and test openings", 9500, 7e3, { phase: 1 }),
    mkLine("Test pits at the front and rear foundations", 6800, 5200, { phase: 1 }),
    mkLine("MEP survey and camera scope of the sewer line", 3200, 2400, { phase: 1 }),
    mkLine("Structural engineer: probes and report", 4500, 4500, { phase: 1, bucket: "soft" }),
    mkLine("Renovation per drawings: three floors and the garden level", 41e4, 318e3, { phase: 2 }),
    mkLine("MEP rerouting", 4e4, 31e3, { phase: 2, range: { lo: 28e3, hi: 52e3 }, unknown: "mep" }),
    mkLine("Code upgrades: egress and fire separation", 21e3, 16500, { phase: 2, range: { lo: 12e3, hi: 3e4 }, unknown: "code" }),
    mkLine("Foundation depth and underpinning", 45e3, 36e3, { phase: 2, range: { lo: 0, hi: 85e3 }, unknown: "foundation" }),
    mkLine("Structure: joist sistering and beam replacement", 35e3, 27500, { phase: 2, range: { lo: 15e3, hi: 6e4 }, unknown: "structure" }),
    mkLine("Storm and sewer to the street", 18e3, 14e3, { phase: 2, range: { lo: 9e3, hi: 26e3 }, unknown: "storm" }),
    mkLine("Kitchen appliances allowance", 18e3, 18e3, { phase: 2, allowance: !0 }),
    mkLine("Tile allowance", 12e3, 12e3, { phase: 2, allowance: !0 }),
    mkLine("Hidden-conditions contingency", 25e3, 25e3, { phase: 2, bucket: "contingency" }),
  ];
  docMark(eB), await send(B, eB, "2026-07-28"), await docAction(B, eB, "approve");
  const exB = progress(B, ljPrimary(B) || "", "Exploratory phase: 50% at start", "2026-08-10", "2026-08-17", { "": 50 });
  await send(B, exB, "2026-08-10", "2026-08-17"), pay(B, exB, "2026-08-13", docTotal(exB).total, "Check", "2210");
  const fl = (w) => eB.lines.find((l) => l.item.startsWith(w));
  ljFound(B, eB, fl("MEP rerouting").id, 46500, "The main stack reroutes around the new stair"), ljFound(B, eB, fl("Foundation").id, 62e3, "Test pits: footings at 4 ft; underpin the rear wall"), ljFound(B, eB, fl("Storm").id, 31e3, "The clay pipe collapsed under the sidewalk");
  // 3. A normal estimate, sent, for the walk from estimate to the books
  const Cc = mkClient("cl_lj_mac", "Daniel & Priya Shah", [{ id: "ct_lj_c1", name: "Priya Shah", email: "priya.shah@example.com", phone: "(917) 555-0175", role: "Owner — decisions and payments", primary: !0 }], { propertyAddr: "214 Macon Street, Brooklyn, NY 11216" });
  const pC = mkJob("p_lj_mac", Cc, "214 Macon Street — 4-family to 2-family", Cc.propertyAddr, "2026-09-14", { lpc: "Bedford Historic District" });
  clientOpen = Cc.id;
  const eC = newDoc(Cc, "estimate", { template: "construction", fields: { title: "Convert four apartments to two", projectId: pC.id, date: "2026-08-28" } });
  eC.ljDemo = 1;
  eC.lines = [
    mkLine("Demolition and disposal", 34e3, 26e3),
    mkLine("Framing: new stair opening and partitions", 48e3, 37e3),
    mkLine("Plumbing: remove two kitchens, new baths", 62e3, 48e3),
    mkLine("Electrical: combine services, new panels", 44e3, 34e3),
    mkLine("Drywall, taping and paint", 39e3, 30e3),
    mkLine("Flooring: refinish and patch", 22e3, 17e3),
    mkLine("Kitchen and millwork", 58e3, 45e3),
    mkLine("Permits, filing and DOB sign-off", 14e3, 14e3),
    mkLine("General conditions and supervision", 16e3, 12e3),
  ];
  docMark(eC), await send(Cc, eC, "2026-08-28");
  // 4. The hard / soft / contingency estimate and the tax credit budget: a landmarked church and its rectory
  const G = mkClient("cl_lj_grace", "Grace Chapel Trustees", [{ id: "ct_lj_g1", name: "Rev. Martha Hale", email: "trustees@gracechapel.example", phone: "(212) 555-0190", role: "Chair of the trustees", primary: !0 }], { type: "Institution", propertyAddr: "31 Hale Place, New York, NY 10027" });
  const pG = mkJob("p_lj_grace", G, "Grace Chapel and Rectory — restoration", G.propertyAddr, "2026-10-05", { lpc: "Individual landmark" });
  pG.mbDeal = { clientPaysAll: !0, loi: "all-cash", loiStatus: "being prepared", at: appNowIso(), by: "Owner" };
  clientOpen = G.id;
  const eG = newDoc(G, "estimate", { template: "construction", fields: { title: "Church and rectory restoration: budget", projectId: pG.id, date: "2026-09-01" } });
  Object.assign(eG, { ljDemo: 1, costModel: !0, htc: { fed: 20, qual: 98.5, props: [{ id: "pr_lj_ch", name: "Church", state: 20, sf: 6200, finishPerSf: 38 }, { id: "pr_lj_re", name: "Rectory", state: 30, sf: 3400, finishPerSf: 55 }] } });
  eG.lines = [
    mkLine("Masonry and stained glass restoration", 42e4, 33e4, { prop: "pr_lj_ch", bucket: "hard" }),
    mkLine("Roof and slate", 185e3, 145e3, { prop: "pr_lj_ch", bucket: "hard" }),
    mkLine("Sanctuary MEP", 16e4, 125e3, { prop: "pr_lj_ch", bucket: "hard" }),
    mkLine("Rectory interior renovation", 31e4, 24e4, { prop: "pr_lj_re", bucket: "hard" }),
    mkLine("Rectory MEP", 12e4, 93e3, { prop: "pr_lj_re", bucket: "hard" }),
    mkLine("Architect and preservation consultant", 14e4, 14e4, { bucket: "soft" }),
    mkLine("Structural and MEP engineering", 48e3, 48e3, { bucket: "soft" }),
    mkLine("Permits, LPC and filing", 22e3, 22e3, { bucket: "soft" }),
    mkLine("Builder's risk insurance", 18e3, 18e3, { bucket: "soft" }),
    mkLine("Tax credit consultant", 26e3, 26e3, { bucket: "soft" }),
    mkLine("Hidden-conditions contingency", 16e4, 16e4, { bucket: "contingency" }),
  ];
  ljFinishLines(G, eG), docMark(eG);
  // 5. The senior interior designer, an independent contractor
  const dana = { id: LJ_IDS.emp, name: "Dana Reyes", role: "Senior interior designer", rate: 0, burden: 0, contractRate: 85, billRate: 175, entityId: "ent1", active: !0, workerType: "contractor", businessName: "Dana Reyes Interiors", email: "dana@reyesinteriors.example", ljDemo: 1, history: [{ at: appNowIso(), by: "Owner", from: "", to: "contractor", effective: "2026-08-31", why: "Starts as an independent contractor" }] };
  DB.employees.push(dana);
  const v = ljVendorFor(dana);
  v.ljDemo = 1;
  const te = (date, h, pid, note, ok) => {
    const mins = Math.round(h * 60),
      end = new Date(new Date(`${date}T09:00:00`).getTime() + mins * 6e4),
      pad = (n) => String(n).padStart(2, "0"),
      e = { id: uid("te"), empId: dana.id, date: date, in: `${date}T09:00:00`, out: `${date}T${pad(end.getHours())}:${pad(end.getMinutes())}:00`, breakMin: 0, projectId: pid, code: "15", notes: note, status: ok ? "approved" : "submitted", approvedBy: ok ? "Alan" : "", source: "contractor", ljDemo: 1, work: [{ projectId: pid, code: "15", hours: h, note: "" }] };
    return DB.time.push(e), e;
  };
  te("2026-08-31", 6, "p140", "Kitchen elevations and the finish schedule", !0), te("2026-09-01", 7.5, "p_lj_grace", "Rectory finish palette and the SF takeoff", !0), te("2026-09-02", 5, "p140", "Lighting plan with the client", !0), te("2026-09-03", 4, "p140", "Tile layouts", !1);
  ljBillHours().forEach((b) => (b.ljDemo = 1));
  // portal users: each payer, the Shahs; the contractor's sign-in
  DB.users.push(
    { id: "u_lj_rosa", name: "Rosa Delgado", role: "client", contact: "rosa@atlanticrow.example", clientId: A.id, payerId: "pay_lj_l", ljDemo: 1 },
    { id: "u_lj_owen", name: "Owen Park", role: "client", contact: "owen@morningloaf.example", clientId: A.id, payerId: "pay_lj_t", ljDemo: 1 },
    { id: "u_lj_shah", name: "Priya Shah", role: "client", contact: "priya.shah@example.com", clientId: Cc.id, ljDemo: 1 },
    { id: "u_lj_dana", name: "Dana Reyes", role: "designer", contact: "dana@reyesinteriors.example", employeeId: dana.id, ljDemo: 1 },
  );
  [clientOpen, docOpen, finTab, LJ.pick] = keepOpen;
  ljSync();
  return { ok: !0 };
}
function ljDemoRemove() {
  const emps = new Set((DB.employees || []).filter((e) => ljIsDemo(e) || (e.convertedFrom && /^em_lj_/.test(e.convertedFrom))).map((e) => e.id));
  (DB.clients = (DB.clients || []).filter((c) => !ljIsDemo(c))),
    (DB.projects = (DB.projects || []).filter((p) => !ljIsDemo(p))),
    (DB.users = (DB.users || []).filter((u) => !ljIsDemo(u))),
    (DB.employees = (DB.employees || []).filter((e) => !emps.has(e.id))),
    (DB.vendors = (DB.vendors || []).filter((v) => !ljIsDemo(v) && !emps.has(v.contractorOf))),
    (DB.bills = (DB.bills || []).filter((b) => !ljIsDemo(b) && !emps.has(b.empId))),
    (DB.time = (DB.time || []).filter((e) => !ljIsDemo(e) && !emps.has(e.empId)));
  /^(cl|p)_lj_/.test(String(clientOpen || "")) && ((clientOpen = null), (docOpen = null));
  S && /^p_lj_/.test(S.id || "") && DB.projects[0] && setCurrent(DB.projects[0].id);
}
async function ljDemoSwitch(on) {
  if (!isOwner()) return void toast("The owner turns the Live Jobs demo on and off");
  if (on) {
    const r = await ljDemoSeed();
    if (!r.ok) return void toast(r.why);
    DB.company.liveJobsDemo = !0;
  } else ljDemoRemove(), (DB.company.liveJobsDemo = !1);
  try {
    audit("settings", "livejobs", on ? "demo-on" : "demo-off");
  } catch (e) {}
  save(), render(), toastDone(on ? "Live Jobs demo is on: 88 Atlantic Ave (two payers), 17 Rugby Road (exploratory phase and ranges), 214 Macon Street, Grace Chapel (tax credits) and Dana Reyes (contractor)" : "Live Jobs demo is off: its jobs, people and records are removed", on ? () => ((clientOpen = "cl_lj_atl"), (clientTab = "fin"), (docOpen = null), (finTab = "invoices"), (view = "clients"), render()) : null);
}
function ljDemoCard() {
  const on = ljDemoOn();
  return `<div class="lj-card" id="lj-demo-card" style="margin-top:12px"><h3>Live Jobs Demo</h3><p class="lj-sub">Invented jobs that show what the firm's live work needs: two payers on one contract, a paid exploratory phase with ranges and allowances, a normal estimate, the hard, soft and contingency budget with historic tax credits, and a contractor who can become an employee. ${on ? "It is on." : "It is off; the firm's figures are untouched."}</p><div class="lj-acts">${on ? ljBtn('data-ljdemo="off"', "Turn the Demo Off") : ljBtn('data-ljdemo="on"', "Turn the Demo On")}</div></div>`;
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      if ("setup" === view && "function" == typeof isOwner && isOwner()) {
        const host = document.getElementById("setup-body");
        host && (host.querySelector("#lj-demo-card") || host.insertAdjacentHTML("beforeend", ljDemoCard()));
      }
      const emp = ljMyEmp();
      if (emp && ljIsContractor(emp) && emp.active) {
        const v = document.querySelector(".view.on");
        if (v && v.id === "v-" + ((MENU[role()] || {}).home || "sday")) {
          const old = v.querySelector("#lj-myhours"),
            html = ljMyHoursCard(emp);
          old ? (old.outerHTML = html) : v.insertAdjacentHTML("afterbegin", html);
        }
      }
    } catch (e) {
      console.warn("livejobs render", e);
    }
    return r;
  };
}
/*<</livejobs.js>>*/
