/* =====================================================================================================================
   specialists.js: a standing auditor per role, the savings ledger and workload (BACKLOG §1.28, §1.30, §1.31, §1.32 #2)
   Alan, 2026-10-17: "Each role gets an assistant that works through that role's checklist all the time."

   Design gate (§1.16). What this extends, and the one store it adds:
     - The detectors stay where they are: CATCH (Caught for You), PRED (the predicate registry), STANDARD_RULES (the
       Standard Watch), Needs Your Hand (nyhRows), the Payment Check (pcHeldBills), price watch (PW_DET), track,
       stock, the leak detectors and the brain. A checklist line READS them by name (RS_SRC); it never keeps a second
       list of the same thing, so a line's count is its sources' rows, the same rows they show where they live.
       Four checks the lists asked for had no detector: they are added as predicates (one rule each, counted once):
       PRED.discountsAtRisk, PRED.jobsCashNegative, PRED.linesOverBudget, PRED.billsDuplicate, and the workload one,
       PRED.peopleOverloaded. Two thresholds became Standard Watch rules (unbudgeted1k, slip2days) that escalate to
       the owner on Needs Your Hand.
     - The six steps ride on what exists: the Standard (standardWhy, standardEscalation), the one task creator
       (crCreateTask), the assistant's outbox drafts (DB.outbox, approved on Approvals like every draft), the record
       sheets that already apply a fix (the short-pay sheet, the duplicate dispute, the order sheet, the reply to a
       client), Company › Changes (DB.changes) for a rule the owner approves, and the hand-off on the task record.
     - ONE new store, DB.specialist {cases, dismissed, approved}: the handling state of a finding (its task, the fix
       approved, fixed or reopened, a dismissal with its reason). Findings themselves are never stored: they are
       read from the detectors every time. No existing record holds "this finding was dismissed for this reason" or
       "the task for it was ticked but the record is not fixed yet".
     - The savings ledger is computed from the records (short-pays, disputed duplicates, discounts taken, RFQ awards
       under the first quote, findings fixed) through window.SV_SOURCES, a registry any lane pushes to; the owner's
       share to the pools and the bonus credits he approves sit on DB.company (savingsShare, savingsAttr). No list of
       savings is typed in.
     - No new view or menu item: the checklist is a part ("Checklist") of the assistant's Findings tab, the
       thresholds sit on its Brain Settings tab, the one-liner on each person's Home.
   ===================================================================================================================== */

// ---- 1. the store, and the thresholds the owner adjusts ------------------------------------------------------------
// Each default is the Standard's own number; the owner moves one by approving a change under Company › Changes
// (rsThresholdPropose drafts it, mtChangeApply writes DB.company.spThresholds on approval).
const RS_T = {
  threeQuotes: { label: "Three Quotes Above", unit: "$", def: 2500, cite: ["pb", "procurement", "standards", /^Three quotes/i] },
  unbudgeted: { label: "Unbudgeted Cost Escalates Above", unit: "$", def: 1000, cite: ["esc", /Cost impact over \$1,000/i] },
  slipDays: { label: "Milestone Slip Escalates After", unit: "working days", def: 2, cite: ["esc", /Milestone slip/i] },
  clientAckHours: { label: "Client Acknowledgement Within", unit: "business hours", def: 2, cite: ["std", "communication", /Client messages/i] },
};
function rsInit() {
  DB.specialist = DB.specialist || {};
  const S = DB.specialist;
  return (S.cases = S.cases || {}), (S.dismissed = S.dismissed || {}), (S.approved = S.approved || {}), S;
}
const rsT = (k) => {
  const T = ((DB.company || {}).spThresholds) || {},
    v = T[k];
  return null != v && "" !== v && isFinite(+v) ? +v : RS_T[k].def;
};
const RS_FIELD = ["foreman", "crew", "driver"];
const rsMe = () => ("function" == typeof currentUser ? currentUser() : null) || {};
const rsIsField = (r) => RS_FIELD.includes(r || role());
const rsJob = (p) => (p ? String((p.project || {}).name || "").replace(/ —.*$/, "") : "");
const rsProj = (id) => (DB.projects || []).find((p) => p.id === id) || null;
const rsLive = (p) => p && !p.archived && "closed" !== (p.project || {}).status;
const rsMoney = (n) => money(Math.abs(+n || 0));
function rsWorkAdd(d, n) {
  let x = d || today(),
    k = 0;
  for (let i = 0; i < 40 && k < n; i++) (x = iso(addDays(x, 1))), isWork(x) && k++;
  return x;
}
const rsUserOfRole = (r) => ("function" == typeof tdyRoleUser ? tdyRoleUser(r) : (DB.users || []).find((u) => u.role === r)) || null;

// ---- 2. the checks the lists asked for that had no detector (one predicate each, counted once) ---------------------
predDef("discountsAtRisk", {
  label: "Discounts at Risk",
  rule: "an early-pay discount on an unpaid bill whose window closes within 3 working days, or has already closed while the bill sat unpaid",
  rows() {
    let R = [];
    try {
      R = tmRows() || [];
    } catch (e) {}
    const td = today();
    return R.filter((r) => r.tm && r.tm.disc > 0 && r.save > 0 && r.discBy && !["paid", "void", "rejected", "draft"].includes(r.bill.status) && (r.discBy < td || workdays(td, r.discBy) <= 3)).map((r) => ({
      key: "disc:" + r.bill.id,
      b: r.bill,
      save: r.save,
      discBy: r.discBy,
      missed: r.discBy < td,
      terms: r.tm.label,
      what: `${r.discBy < td ? "Discount missed" : "Discount closing"}: ${r.bill.vendor} ${r.bill.number || ""}`.trim(),
      sub: `${money(r.save)} for paying by ${fmtL(r.discBy)} (${r.tm.label}) · the bill is ${r.bill.status}`,
      amount: r.save,
    }));
  },
});
// One count, one rule (coordinator, 2026-10-20): a job spending more than it brings in is the cost-intelligence rule,
// PRED.jobsOverspending in src/costintel.js (cash out above cash in, with cash in the larger of the bank deposits coded
// to the job and the payments recorded; cost ahead of billings; a line over budget or forecast to go over). This name
// is that predicate under the checklist's word for it, so the checklist, Caught for You, the Cost Intelligence tab and
// Ask show the same jobs and the same count.
predDef("jobsCashNegative", {
  label: "Jobs Spending More Than They Bring In",
  rule: "the cost-intelligence rule (PRED.jobsOverspending): cash out above cash in, cost ahead of billings, or a line over budget or forecast to go over",
  rows: (scope) => ("undefined" != typeof PRED && PRED.jobsOverspending ? PRED.jobsOverspending.rows(scope) : []),
});
predDef("linesOverBudget", {
  label: "Lines Over Budget",
  rule: "an estimate or change-order line whose estimate at completion (the larger of its budget and its actual plus committed cost) is above its budget",
  rows() {
    return (DB.projects || []).filter(rsLive).flatMap((p) => {
      let J = null;
      try {
        J = jobFin(p);
      } catch (e) {}
      return ((J && J.eacLines) || [])
        .filter((l) => +l.budget > 0 && (+l.eac || 0) - +l.budget > 0.5)
        .map((l) => ({ key: "eac:" + p.id + ":" + l.key, p: p, l: l, over: r2(l.eac - l.budget), what: `Over budget: ${l.name} · ${rsJob(p)}`, sub: `forecast ${money(l.eac)} against a budget of ${money(l.budget)} (actual ${money(l.actual)}, committed ${money(l.committed)})`, amount: r2(l.eac - l.budget) }));
    });
  },
});
// The Payment Check's own duplicate rule (pcCheck: the same invoice number, the same amount and date, the same pay
// application), read on every live unpaid bill from the day it is entered, not only when someone goes to pay it.
predDef("billsDuplicate", {
  label: "Duplicate Vendor Invoices",
  rule: "the Payment Check's duplicate rule on every unpaid bill: another live bill from the vendor with the same invoice number, the same amount and date, or the same pay application",
  rows() {
    if ("function" != typeof pcCheck) return [];
    return (DB.bills || [])
      .filter((b) => !["void", "rejected", "paid", "draft"].includes(b.status) && billTotal(b) > 0)
      .map((b) => {
        let h = null;
        try {
          h = (pcCheck(b).holds || []).find((x) => "dup" === x.key);
        } catch (e) {}
        return h ? { key: "billdup:" + b.id, b: b, twin: (DB.bills || []).find((x) => x.id === h.other) || null, what: `Billed twice? ${b.vendor} ${b.number || ""}`.trim(), sub: `${money(billTotal(b))} · ${h.what}`, amount: billTotal(b) } : null;
      })
      .filter(Boolean);
  },
});
Object.assign(STD_MAP, {
  discountsAtRisk: { p: "cost", leak: !0, c: ["pb", "office", "actFrom", /Cash is oxygen/i] },
  jobsCashNegative: { p: "cost", leak: !0, c: ["value", "dollar", /Waste nothing/i], esc: () => /Cost impact over \$1,000/i },
  linesOverBudget: { p: "cost", leak: !0, c: ["std", "money", /Budget vs\. actual/i], esc: (it) => STD_OVER1K(it) },
  billsDuplicate: { p: "cost", leak: !0, c: ["value", "dollar", /Waste nothing/i] },
  peopleOverloaded: { p: "", c: ["value", "team", /./] },
  specialist: { p: "", c: ["value", "own", /If you see it/i] },
});

// ---- 3. the thresholds the Standard sets, enforced from the live settings --------------------------------------------
// Three quotes: the Watch's rule reads the owner's figure (it was a fixed $2,500). A Friday update counts only when it
// went out (a draft waiting for the PM is not an update the client received). Client acknowledgement: 2 business
// hours, on portal questions and on client mail in the reader's own mailbox (never another person's).
{
  const R3 = STANDARD_RULES.find((r) => "threeQuotes" === r.id);
  R3 &&
    (R3.rows = () =>
      (DB.pos || [])
        .filter((po) => !["cancelled", "void", "draft"].includes(po.status) && (poTotal(po).total > rsT("threeQuotes") || "subcontract" === po.type))
        .map((po) => ({ po: po, n: stdPOQuoteCount(po) }))
        .filter((x) => x.n < 3)
        .map((x) => ({ key: "q3:" + x.po.id, what: `${x.n ? `${x.n} quote${1 === x.n ? "" : "s"}` : "No quotes"} on record: ${x.po.number} · ${x.po.vendor}`, sub: `${money(poTotal(x.po).total)} on ${stdJob(x.po.projectId)}${"subcontract" === x.po.type ? " · a subcontract" : ""}`, amount: poTotal(x.po).total, go: flowGo.po(x.po) })));
  const RF = STANDARD_RULES.find((r) => "fridayUpdate" === r.id);
  if (RF) {
    const base = RF.rows;
    RF.rows = function () {
      const keep = DB.outbox;
      try {
        DB.outbox = (keep || []).filter((o) => "sent" === o.status);
        return base.apply(this, arguments);
      } finally {
        DB.outbox = keep;
      }
    };
  }
  const RA = STANDARD_RULES.find((r) => "clientAck" === r.id);
  RA &&
    ((RA.partial = "Measured on portal questions and on client mail in your own mailbox: no reply within the business hours the owner set. A message read and answered by phone is not recorded, so it still counts until someone replies or files it."),
    (RA.rows = () => rsClientAckRows()));
}
function rsClientEmails() {
  const S = new Set();
  (DB.clients || []).forEach((c) => {
    [c.email].concat((c.contacts || []).map((x) => x && x.email)).forEach((e) => e && S.add(String(e).toLowerCase()));
  });
  (DB.users || []).filter((u) => "client" === u.role && u.email).forEach((u) => S.add(String(u.email).toLowerCase()));
  return S;
}
function rsClientAckRows() {
  const H = rsT("clientAckHours"),
    out = [];
  (DB.projects || []).filter(stdLive).forEach((p) =>
    (p.clientQs || [])
      .filter((q) => "open" === q.status && q.at && stdWorkHoursSince(q.at) >= H)
      .forEach((q) => out.push({ key: "cq:" + q.id, q: q, p: p, what: `${q.by || "The client"} asked ${String(q.at).length > 10 ? stampText(q.at) : fmtL(q.at)}: ${String(q.text || "").slice(0, 60)}`, sub: `${stdJob(p.id)} · ${Math.floor(stdWorkHoursSince(q.at))} business hours with no answer`, go: () => clqAnswer(q.id) })),
  );
  try {
    const CL = rsClientEmails(),
      me = ("function" == typeof paMe ? paMe() : rsMe()).id;
    (("function" == typeof cmNeedsAnswer ? cmNeedsAnswer() : []) || [])
      .filter((c) => c && (!c.owner || c.owner === me) && CL.has(String((c.from || {}).email || "").toLowerCase()) && c.date && stdWorkHoursSince(c.date) >= H)
      .forEach((c) => out.push({ key: "cm:" + c.id, c: c, what: `${(c.from || {}).name || (c.from || {}).email} wrote: ${String(c.subject || "").slice(0, 60)}`, sub: `${Math.floor(stdWorkHoursSince(c.date))} business hours with no reply`, go: () => ("function" == typeof cmOpen ? cmOpen(c.id) : setView("comms")) }));
  } catch (e) {}
  return out;
}
// Unbudgeted cost: money spent on a job that rests on no line of the approved budget (an estimate or change-order
// line), above the owner's figure. Escalated to the owner the same day, in the Standard's format.
function rsLinked(x) {
  return !!(x && (x.line || x.estimateLineId || x.coLineId || ((x.lines || []).some((l) => l && (l.line || l.estimateLineId || l.coLineId)))));
}
function rsUnbudgetedRows() {
  const T = rsT("unbudgeted"),
    live = new Set((DB.projects || []).filter(rsLive).map((p) => p.id)),
    out = [];
  (DB.bills || [])
    .filter((b) => live.has(b.projectId) && !["void", "rejected", "draft"].includes(b.status) && billTotal(b) > T && !rsLinked(b))
    .forEach((b) => {
      const po = b.poId && (DB.pos || []).find((x) => x.id === b.poId);
      po && rsLinked(po) || out.push({ key: "unb:b:" + b.id, b: b, what: `Not in the budget: ${b.vendor} ${b.number || ""}`.trim(), sub: `${money(billTotal(b))} on ${stdJob(b.projectId)}, on no estimate or change-order line`, amount: billTotal(b), go: flowGo.bill(b) });
    });
  (DB.txns || [])
    .filter((t) => live.has(t.projectId) && +t.amt < -T && !rsLinked(t) && !t.billId && !t.poId && !t.payrollId && !["transfer", "cc-payment", "payroll", "income"].includes(t.cat) && !["void", "voided"].includes(t.status) && "disputed" !== t.dupState)
    .forEach((t) => out.push({ key: "unb:t:" + t.id, t: t, what: `Not in the budget: ${t.vendor || t.desc}`, sub: `${money(-t.amt)} on ${stdJob(t.projectId)} ${fmtL(t.date)}, on no estimate or change-order line`, amount: -t.amt, go: () => txnDialog(t.id) }));
  return out;
}
// A milestone slip: a milestone's finish later than its baseline finish by more than the owner's working days.
function rsSlipRows() {
  const T = rsT("slipDays"),
    out = [];
  (DB.projects || []).filter(rsLive).forEach((p) =>
    (p.tasks || [])
      .filter((t) => "milestone" === t.type && t.origEnd && t.end && t.end > t.origEnd && "done" !== t.status)
      .forEach((t) => {
        const d = workdays(t.origEnd, t.end) - 1;
        d > T && out.push({ key: `slip:${p.id}:${t.id}`, p: p, t: t, what: `Milestone slipped ${d} working days: ${t.name}`, sub: `${rsJob(p)} · was ${fmtL(t.origEnd)}, now ${fmtL(t.end)}`, due: today(), go: () => (setCurrent(p.id), setView("sched")) });
      }),
  );
  return out;
}
standardRegisterRule(
  { id: "unbudgeted1k", owner: "owner", p: "cost", leak: !0, c: ["esc", /Cost impact over \$1,000/i], surface: "nyh", esc: () => /Cost impact over \$1,000/i, rows: () => rsUnbudgetedRows() },
  { id: "slip2days", owner: "owner", p: "schedule", c: ["esc", /Milestone slip/i], surface: "nyh", esc: () => /Milestone slip/i, rows: () => rsSlipRows() },
);
// Three quotes at issue (including a subcontract): the PO records that it went out under the rule, who issued it and
// the count, so the exception is on the record and on the procurement checklist. It does not block the order.
if ("function" == typeof poAction) {
  const base = poAction;
  poAction = function (po, act) {
    const was = po && po.status,
      r = base.apply(this, arguments);
    try {
      if (po && "issue" === act && "issued" === po.status && "issued" !== was && (poTotal(po).total > rsT("threeQuotes") || "subcontract" === po.type)) {
        const n = stdPOQuoteCount(po);
        n < 3 && ((po.q3 = { n: n, by: rsMe().name || role(), at: appNowIso(), limit: rsT("threeQuotes") }), audit("po", po.id, "under-three-quotes", "", String(n), `issued over ${money(rsT("threeQuotes"))} with ${n} quote${1 === n ? "" : "s"}`));
      }
    } catch (e) {}
    return r;
  };
}

// ---- 4. the checklists: each line names the detectors it reads ---------------------------------------------------
// A source returns rows {key, what, sub, amount, run, rec}. "catch:x" is a Caught for You detector, "pred:x" a
// predicate, "rule:x" a Standard Watch rule, "nyh:x" a Needs Your Hand kind, "fn:x" a reader below that calls an
// existing function. Nothing here counts a thing a second way: a line is the union of its sources' rows.
const rsCatch = (name) => {
  const C = CATCH.find((x) => x.name === name);
  if (!C) return [];
  try {
    return (C.rows() || []).map((r) => ({ key: r.key, what: r.what, sub: r.sub || "", amount: +r.amount || 0, run: r.run, verb: r.verb, rec: rsRecOfKey(r.key) }));
  } catch (e) {
    return [];
  }
};
const rsRule = (id) => {
  const R = STANDARD_RULES.find((x) => x.id === id);
  const def = (o) => (Object.keys(o).forEach((k) => null == o[k] && delete o[k]), o);
  return R ? standardRuleRows(R).map((r) => ({ key: r.key, what: r.what, sub: r.sub || "", amount: +r.amount || 0, run: r.go, rec: Object.assign(rsRecOfKey(r.key), def({ b: r.b, t: r.t && r.t.acct ? r.t : null, task: r.t && !r.t.acct ? r.t : null, p: r.p, q: r.q, c: r.c })) })) : [];
};
const rsNyh = (kind) => {
  let R = [];
  try {
    R = nyhRows({ everyone: !0 }) || [];
  } catch (e) {}
  return R.filter((r) => r.kind === kind).map((r) => ({ key: r.key, what: r.title, sub: r.why || "", amount: +r.amount || 0, run: r.run || r.open, rec: rsRecOfKey(r.key) }));
};
// the record a row's key names (bill:<id>, lk:dup:<txn>, coi:<vendor>, q3:<po>, um:<txn>, rcpt:<txn>, ...)
function rsRecOfKey(key) {
  const k = String(key || ""),
    o = {},
    bill = (id) => (DB.bills || []).find((b) => b.id === id),
    txn = (id) => (DB.txns || []).find((t) => t.id === id);
  let m;
  if ((m = k.match(/^(?:bill|3way|nopo|coneed|billdup|disc|unb:b):(.+)$/))) o.b = bill(m[1]);
  else if ((m = k.match(/^(?:lk:dup|um|rcpt|txn|unb:t):(.+)$/))) (o.t = txn(m[1])), o.t && o.t.dupOf && (o.twin = txn(o.t.dupOf));
  else if ((m = k.match(/^(?:q3|src|po):(.+)$/))) o.po = (DB.pos || []).find((x) => x.id === m[1]);
  else if ((m = k.match(/^(?:coi|coi30|vblock):(.+)$/))) o.v = (DB.vendors || []).find((x) => x.id === m[1]);
  o.b && o.b.poId && (o.po = (DB.pos || []).find((x) => x.id === o.b.poId));
  o.b && (o.p = rsProj(o.b.projectId));
  o.po && !o.p && (o.p = rsProj(o.po.projectId));
  o.t && (o.p = rsProj(o.t.projectId));
  return o;
}
const RS_SRC = {
  // controller and finance
  unmatched: () => rsCatch("unmatchedTxns"),
  notAtBank: () => (PRED.notAtBank ? PRED.notAtBank.rows() : []).map((r) => ({ key: "nab:" + (r.id || r.key), what: `Not at the bank: ${r.desc || r.what || ""}`, sub: r.sub || (r.date ? fmtL(r.date) : ""), amount: Math.abs(+r.amt || +r.amount || 0), run: () => txnDialog(r.id), rec: { t: r } })),
  undeposited: () => rsNyh("undeposited"),
  dupCharge: () => rsNyh("dup").concat(rsCatch("pwDupCharge")),
  cardNoReceipt: () => (PRED.cardNoReceipt ? PRED.cardNoReceipt.rows() : []).map((r) => ({ key: r.key, what: `No receipt: ${r.what}`, sub: r.sub, amount: +r.amount || 0, run: r.go, rec: rsRecOfKey(r.key) })).concat(rsCatch("pwCardNoJob")),
  books10: () => rsRule("books10"),
  overPO: () => rsCatch("overPO"),
  noPO: () => rsRule("poBeforeOrder"),
  vendorsBlocked: () => (PRED.vendorsBlocked ? PRED.vendorsBlocked.rows() : []).map((v) => ({ key: "vblock:" + v.id, what: `${v.name}: ${v.insuranceExp ? "insurance expired " + fmtL(v.insuranceExp) : "no insurance certificate on file"}`, sub: "an order is open with them: no new PO, no payment until it lands", amount: 0, run: () => setView("vendors"), rec: { v: v } })),
  payHoldPapers: () =>
    ("function" == typeof pcHeldBills ? pcHeldBills() : [])
      .filter((x) => x.R.holds.some((h) => ["papers", "w9"].includes(h.key)))
      .map((x) => ({ key: "pchold:" + x.b.id, what: `Payment held: ${x.b.vendor} ${x.b.number || ""}`.trim(), sub: x.R.holds.filter((h) => ["papers", "w9"].includes(h.key)).map((h) => h.what).join("; "), amount: billTotal(x.b), run: () => ("function" == typeof pcPaySheet ? pcPaySheet(x.b.id) : openBill(x.b.id)), rec: { b: x.b } })),
  ten99: () => {
    let R = null;
    try {
      R = fin2Register1099();
    } catch (e) {}
    return ((R && R.missing) || []).map((r) => ({ key: "1099:" + r.v.id, what: `No W-9: ${r.v.name}`, sub: `${money(r.reportable)} reportable this year, over the 1099 line`, amount: r.reportable, run: () => setView("vendors"), rec: { v: r.v } }));
  },
  discounts: () => PRED.discountsAtRisk.rows().map((r) => ({ key: r.key, what: r.what, sub: r.sub, amount: r.amount, run: () => openBill(r.b.id), rec: { b: r.b, disc: r } })),
  billsDuplicate: () => PRED.billsDuplicate.rows().map((r) => ({ key: r.key, what: r.what, sub: r.sub, amount: r.amount, run: () => openBill(r.b.id), rec: { b: r.b, twin: r.twin } })),
  earned: () => rsCatch("earnedNotBilled"),
  costNotBilled: () => rsCatch("costNotBilled"),
  drafts: () => rsCatch("clientDrafts"),
  collections: () => rsRule("collections"),
  deposits: () => rsNyh("deposit").concat(rsNyh("undeposited")),
  rebill: () => rsNyh("rebill"),
  overBudget: () => rsCatch("budgetOverrun").concat(PRED.linesOverBudget.rows().map((r) => ({ key: r.key, what: r.what, sub: r.sub, amount: r.amount, run: () => (setCurrent(r.p.id), setView("costs")), rec: { p: r.p, line: r.l } }))),
  uncoded: () => (PRED.uncodedCost ? PRED.uncodedCost.rows() : []).map((r) => ({ key: "gl:" + ((r.j && r.j.id) || "") + ":" + ((r.l && r.l.acct) || ""), what: `Cost on no job: ${String((r.j && r.j.memo) || "a ledger line").slice(0, 60)}`, sub: `${money((r.l && (r.l.dr || r.l.cr)) || 0)} · ${(r.j && fmtL(r.j.date)) || ""}`, amount: +((r.l && (r.l.dr || r.l.cr)) || 0), run: () => setView("gl"), rec: { j: r.j } })),
  accruals: () => (PRED.orphanAccruals ? PRED.orphanAccruals.rows() : []).map((r) => ({ key: "acc:" + (r.id || (r.j && r.j.id) || ""), what: `Payroll accrual with no run: ${r.memo || (r.j && r.j.memo) || ""}`, sub: r.date ? fmtL(r.date) : "", amount: +r.amount || 0, run: () => setView("gl"), rec: {} })),
  useTax: () => rsCatch("pwUseTax"),
  closedMonth: () =>
    ("function" == typeof truthVerifyAll ? truthVerifyAll() : [])
      .filter((v) => !1 === v.ok)
      .map((v) => ({ key: "chain:" + v.ym, what: `Changed after close: ${v.label}`, sub: [v.changed.length ? `${v.changed.length} changed` : "", v.missing.length ? `${v.missing.length} missing` : "", v.added.length ? `${v.added.length} added` : ""].filter(Boolean).join(", "), amount: 0, run: () => ("function" == typeof truthVerifyDialog ? truthVerifyDialog() : setView("gl")), rec: {} })),
  closeBlockers: () => {
    let C = null;
    try {
      const ym = iso(addDays(today().slice(0, 7) + "-01", -1)).slice(0, 7);
      C = ctCloseStatus(ym);
      C.ym = ym;
    } catch (e) {}
    return ((C && C.blockers) || []).map((why, i) => ({ key: `close:${C.ym}:${i}`, what: `Close blocker: ${String(why).slice(0, 80)}`, sub: `${C.ym}`, amount: 0, run: () => setView("gl"), rec: {} }));
  },
  // PM, three weeks out
  lateDecision: () => PRED.lateDecision.rows().map(({ p: p, d: d }) => ({ key: "dec:" + d.id, what: `Decision past due: ${String(d.name || "").replace(/ — .*$/, "")}`, sub: `${rsJob(p)}${d.owner ? " · " + d.owner + " decides" : ""}`, amount: 0, run: () => ("function" == typeof flowDecide ? flowDecide(p, d) : setView("dec")), rec: { p: p, d: d } })),
  lateMaterial: () => PRED.lateMaterial.rows().map((r) => ({ key: `mat:${(r.p || {}).id}:${r.key || (r.m && r.m.id) || r.name}`, what: `Not ordered: ${r.name}`, sub: `order-by ${fmtL(r.orderBy)} passed · needed ${fmtL(r.needBy)} · ${rsJob(r.p)}`, amount: +r.price || 0, run: () => ("function" == typeof buyOrderDialog ? buyOrderDialog(r) : setView("proc")), rec: { p: r.p, buy: r } })),
  lateSubmittal: () => PRED.lateSubmittal.rows().map((r) => ({ key: "subm:" + r.s.id, what: `Late submittal: ${r.s.number} ${String(r.s.title || "").slice(0, 50)}`, sub: `${(r.L && r.L.why) || "late"}${r.B && r.B.who ? ` · with ${r.B.who}` : ""} · ${rsJob(r.p)}`, amount: 0, run: () => ("function" == typeof smOpenRec ? smOpenRec(r.s.id, r.p) : setView("subm")), rec: { p: r.p, s: r.s, ball: r.B, late: r.L } })),
  inspToBook: () => PRED.inspToBook.rows().map(({ p: p, i: i }) => ({ key: "insp:" + i.id, what: `Book the inspection: ${i.name || i.type || "inspection"}`, sub: rsJob(p), amount: 0, run: () => ("function" == typeof inspBookDialog ? (setCurrent(p.id), inspBookDialog(i.id)) : setView("insp")), rec: { p: p, i: i } })),
  subsAhead: () => rsCatch("subsAhead"),
  lateTasks: () => rsCatch("lateTasks"),
  slip: () => rsRule("slip2days"),
  needsCO: () => PRED.needsChangeOrder.rows().map((r) => ({ key: "needco:" + ((r.r && r.r.id) || r.name), what: `Change order to write: ${r.name}`, sub: rsJob(r.p), amount: +r.amount || 0, run: () => setView("mapprove"), rec: { p: r.p, raise: r.r } })).concat(rsCatch("coNeeded")),
  unsigned: () => (PRED.unsignedDocs ? PRED.unsignedDocs.rows() : []).map(({ c: c, d: d }) => ({ key: "unsigned:" + d.id, what: `Not signed: ${d.number} · ${c.name}`, sub: `${money(docTotal(d).total)} sent ${fmtL(d.sentAt || d.date)}`, amount: docTotal(d).total, run: () => setView("clients"), rec: { c: c, d: d } })),
  clientAck: () => rsRule("clientAck"),
  friday: () => rsRule("fridayUpdate"),
  unbudgeted: () => rsRule("unbudgeted1k"),
  // founder
  cashLow: () => {
    let v = null;
    try {
      v = tdPulseValue((TD_PULSE.owner || []).find((t) => "safe" === t.k));
    } catch (e) {}
    return null != v && v < 0 ? [{ key: "cash:safe", what: `Safe to spend is ${tdMoney(v)}`, sub: "cash less what is owed and over-billed; the 13-week low is on the cash forecast", amount: -v, run: () => setView("reports"), rec: {} }] : [];
  },
  jobsAtRisk: () => PRED.jobsAtRisk.rows().map((x) => ({ key: "risk:" + x.p.id, what: `At risk: ${rsJob(x.p)}`, sub: (x.why || []).join("; ").slice(0, 120), amount: 0, run: () => (setCurrent(x.p.id), setView("dash")), rec: { p: x.p } })),
  cashNeg: () => PRED.jobsCashNegative.rows().map((x) => ({ key: x.key, what: x.what, sub: x.sub, amount: x.amount, run: () => (setCurrent(x.p.id), setView("costs")), rec: { p: x.p, cash: x } })),
  pipeline: () => rsCatch("chasePeople").filter((r) => /^chase:lead:/.test(r.key)),
  overload: () => PRED.peopleOverloaded.rows().map((x) => ({ key: x.key, what: x.what, sub: x.sub, amount: 0, run: () => rsOpenChecklist("owner"), rec: { wl: x } })),
  notBack: () => rsCatch("notBack"),
  coi30: () => rsRule("coi30"),
  obligations: () => rsNyh("oblig"),
  // operations and procurement
  promisesBroken: () => (PRED.promisesBroken ? PRED.promisesBroken.rows() : []).map((r) => ({ key: r.key || "prom:" + r.id, what: r.what || `Promise broken: ${r.vendor || ""}`, sub: r.sub || "", amount: +r.amount || 0, run: r.go || (() => setView("po")), rec: rsRecOfKey(r.key) })),
  threeQuotes: () => rsRule("threeQuotes").concat(rsCatch("rfqUnderQuoted")),
  notDelivered: () => rsCatch("pwNotDelivered"),
  creditsOwed: () =>
    ("function" == typeof retList ? retList() : [])
      .filter((r) => ["shipped", "received"].includes(r.status) && "function" == typeof retChase && retChase(r) > retCfg().chaseDays)
      .map((r) => ({ key: "ret:" + r.id, what: `Sent back, not credited: ${r.name}`, sub: `${r.vendor} · ${money(retExpected(r))} · ${retChase(r)} days`, amount: retExpected(r), run: () => setView("sel"), rec: { ret: r } }))
      .concat(rsCatch("unmatchedCredit")),
  boughtTwice: () => rsCatch("pwQtyOver"),
  stock: () => rsCatch("boughtWhileInStock"),
  paidMore: () => rsCatch("pwPaidMore"),
  // foreman
  dailyLog: () => rsRule("dailyLog"),
  request5: () => rsRule("request5days"),
  plansAck: () => rsCatch("plansNotAcked"),
  siteQuestions: () => (PRED.siteQuestions ? PRED.siteQuestions.rows() : []).map(({ p: p, x: x }) => ({ key: "raise:" + x.id, what: `Open question: ${String(x.title || "").slice(0, 70)}`, sub: rsJob(p), amount: 0, run: () => (flowGo && "function" == typeof flowGo.raise ? flowGo.raise(x)() : setView("mapprove")), rec: { p: p, raise: x } })),
  // designer
  designer2days: () => rsRule("designer2days"),
  plansAmend: () => rsCatch("plansAmendment"),
};
// who a line's task goes to, and why that person (the Standard's playbooks)
const RS_WHO = {
  controller: "the controller keeps the books true and reconciled (Office playbook)",
  billing: "billing issues every invoice and runs collections (Office playbook)",
  owner: "only the owner approves part of a bill, posts by hand or decides past the budget (Decide or escalate)",
  pm: "the PM owns the job, its client and its dates (PM playbook)",
  coord: "procurement places every order and owns lead times and quotes (Procurement playbook)",
  foreman: "the foreman runs the site day to day (Foreman playbook)",
  designer: "the designer answers the field and owns selections (Designer playbook)",
};
// The lines. who: the role whose task it is; fix: the drafted fix (RS_FIX); saves: the savings-ledger source a fixed
// finding counts under; missing: no detector yet, said plainly and never counted.
const RS_CHECKS = [
  // ---- controller and finance
  { id: "c.unmatched", roles: ["controller"], area: "Bank", label: "Unmatched Bank Lines", src: ["unmatched"], std: "unmatchedTxns", who: "controller", fix: "open", where: "Caught for You · Bank" },
  { id: "c.typed", roles: ["controller"], area: "Bank", label: "Typed by Hand, Not at the Bank", src: ["notAtBank", "undeposited"], std: "nyh:undeposited", who: "controller", fix: "open", where: "Needs Your Hand · Bank" },
  { id: "c.dup", roles: ["controller"], area: "Bank", label: "Duplicate Charges", src: ["dupCharge"], std: "nyh:dup", who: "controller", fix: "dispute", saves: "duplicate", where: "Needs Your Hand · price watch" },
  { id: "c.receipt", roles: ["controller"], area: "Bank", label: "Card Charges With No Receipt or Job", src: ["cardNoReceipt"], std: "cardNoReceipt", who: "controller", fix: "receipt", where: "order tracking · price watch" },
  { id: "c.recon", roles: ["controller"], area: "Bank", label: "Accounts Not Reconciled", src: ["books10"], std: "std:books10", who: "controller", fix: "open", where: "Needs Your Hand (Standard Watch)" },
  { id: "c.paidUnapproved", roles: ["controller"], area: "Payables", label: "Bills Paid Before Approval", missing: "The Payment Check refuses a payment before approval; a bill marked paid outside it (by hand, in the bank) is not detected yet." },
  { id: "c.overPO", roles: ["controller"], area: "Payables", label: "Bills Over Their PO", src: ["overPO"], std: "overPO", who: "owner", fix: "shortpay", saves: "overpay", where: "Caught for You · Approvals" },
  { id: "c.noPO", roles: ["controller"], area: "Payables", label: "Bills With No PO", src: ["noPO"], std: "std:poBeforeOrder", who: "coord", fix: "open", where: "Needs Your Hand (Standard Watch)" },
  { id: "c.papers", roles: ["controller"], area: "Payables", label: "No W-9 or Expired COI at Payment", src: ["vendorsBlocked", "payHoldPapers"], std: "compliance", who: "coord", fix: "coiRequest", where: "Vendors (Blocked) · the Payment Check" },
  { id: "c.1099", roles: ["controller"], area: "Payables", label: "1099 Payees Not Set Up", src: ["ten99"], std: "chase:w9", who: "controller", fix: "w9Request", where: "the 1099 register" },
  { id: "c.discount", roles: ["controller"], area: "Payables", label: "Early-Pay Discounts", src: ["discounts"], std: "discountsAtRisk", who: "controller", fix: "payEarly", saves: "discount", where: "Bills · Terms" },
  { id: "c.dupInvoice", roles: ["controller"], area: "Payables", label: "Duplicate Vendor Invoices", src: ["billsDuplicate"], std: "billsDuplicate", who: "controller", fix: "open", saves: "duplicate", where: "Bills" },
  { id: "c.earned", roles: ["controller", "billing"], area: "Receivables", label: "Earned, Not Billed", src: ["earned"], std: "earnedNotBilled", who: "billing", fix: "invoice", saves: "unbilled", where: "Caught for You · Billing Queue" },
  { id: "c.drafts", roles: ["controller", "billing"], area: "Receivables", label: "Drafts Never Sent", src: ["drafts"], std: "draft", who: "billing", fix: "open", where: "Caught for You · Billing" },
  { id: "c.overdue", roles: ["controller", "billing", "owner"], area: "Receivables", label: "Overdue Invoices Not Chased", src: ["collections"], std: "std:collections", who: "billing", fix: "chaseInvoice", where: "Billing (Standard Watch)" },
  { id: "c.retainage", roles: ["controller"], area: "Receivables", label: "Retainage Due", missing: "Retainage held is on every invoice; nothing marks it due (substantial completion, the final walk) yet." },
  { id: "c.deposits", roles: ["controller", "billing"], area: "Receivables", label: "Deposits Not Applied", src: ["deposits"], std: "nyh:deposit", who: "billing", fix: "open", where: "Needs Your Hand" },
  { id: "c.wip", roles: ["controller"], area: "Jobs", label: "WIP Over or Under Billing Moving", missing: "The WIP ties to the ledger on close day (closetie); a move from one week to the next is not measured yet." },
  { id: "c.budget", roles: ["controller", "pm"], area: "Jobs", label: "Lines Forecasting Over Budget", src: ["overBudget"], std: "linesOverBudget", who: "pm", fix: "overBudget", saves: "overrun", where: "Caught for You · Job Costs" },
  { id: "c.committed", roles: ["controller"], area: "Jobs", label: "Committed Cost Not Relieved", missing: "A PO's committed cost falls as its bills land; one left open after the work is done is not detected yet." },
  { id: "c.coBilled", roles: ["controller"], area: "Jobs", label: "Change Orders Approved, Not Billed", same: "c.earned", why: "An approved change order's lines join the next progress bill from zero, so they show under Earned, Not Billed." },
  { id: "c.overhead", roles: ["controller"], area: "Jobs", label: "Job Spend Coded to Overhead", src: ["uncoded"], std: "unmatchedTxns", who: "controller", fix: "open", where: "the Ledger" },
  { id: "c.close", roles: ["controller"], area: "Close", label: "Close Blockers", src: ["closeBlockers"], std: "close", who: "controller", fix: "open", where: "Close" },
  { id: "c.accrual", roles: ["controller"], area: "Close", label: "Payroll Accrual Against the Run", src: ["accruals"], std: "close", who: "controller", fix: "open", where: "Close" },
  { id: "c.tax", roles: ["controller"], area: "Close", label: "Sales and Use Tax", src: ["useTax"], std: "pwUseTax", who: "controller", fix: "open", where: "Caught for You (price watch)" },
  { id: "c.variance", roles: ["controller"], area: "Close", label: "Unexplained Budget Variances", missing: "A budget-vs-actual review is not logged with a date and a reviewer (the Standard Watch says the same)." },
  { id: "c.closedMonth", roles: ["controller", "owner"], area: "Close", label: "Changed After the Month Closed", src: ["closedMonth"], std: "journal", who: "controller", fix: "open", where: "Verify the Books" },
  // ---- the founder
  { id: "o.cash", roles: ["owner"], area: "Cash", label: "Cash Runway and the 13-Week Low", src: ["cashLow"], std: "nyh:deposit", who: "owner", fix: "open", where: "Home (Safe to Spend) · cash forecast" },
  { id: "o.losing", roles: ["owner"], area: "Jobs", label: "Jobs Losing Money, and Why", src: ["jobsAtRisk", "cashNeg"], std: "jobsCashNegative", who: "pm", fix: "cashNeg", saves: "unbilled", where: "Home (Jobs at Risk)" },
  { id: "o.margin", roles: ["owner"], area: "Jobs", label: "Margin Slipping", missing: "The margin trend by job and trade is the cost-intelligence lane's (benchmarks, §1.29); not measured here." },
  { id: "o.collections", roles: ["owner"], area: "Cash", label: "Collections Risk", same: "c.overdue", why: "The same rows as the controller's Overdue Invoices Not Chased." },
  { id: "o.pipeline", roles: ["owner"], area: "Growth", label: "Pipeline Gone Quiet", src: ["pipeline"], std: "chase:lead", who: "owner", fix: "open", where: "Caught for You (Gone Quiet)" },
  { id: "o.overload", roles: ["owner"], area: "People", label: "Overloaded People", src: ["overload"], std: "peopleOverloaded", who: "owner", fix: "moveWork", where: "this checklist (Workload)" },
  { id: "o.clients", roles: ["owner"], area: "Clients", label: "Client Relationships at Risk", src: ["clientAck", "notBack"], std: "std:clientAck", who: "pm", fix: "clientAck", where: "Do Now · Caught for You" },
  { id: "o.compliance", roles: ["owner"], area: "Compliance", label: "Licences, Insurance, Filings", src: ["vendorsBlocked", "coi30", "obligations"], std: "compliance", who: "coord", fix: "coiRequest", where: "Vendors · Needs Your Hand" },
  { id: "o.escalations", roles: ["owner"], area: "Escalations", label: "Escalated to You", src: ["unbudgeted", "slip"], std: "std:unbudgeted1k", who: "owner", fix: "escalation", where: "Needs Your Hand" },
  // ---- the PM, three weeks out
  { id: "p.decisions", roles: ["pm", "designer"], area: "Three Weeks Out", label: "Decisions Past Due", src: ["lateDecision"], std: "dec", who: "pm", fix: "decisionChase", where: "Home (Jobs With Late Items)" },
  { id: "p.materials", roles: ["pm", "coord"], area: "Three Weeks Out", label: "Materials Not Ordered by Their Order-By Date", src: ["lateMaterial"], std: "req", who: "coord", fix: "order", where: "Buy Board · Home" },
  { id: "p.submittals", roles: ["pm", "coord"], area: "Three Weeks Out", label: "Late Submittals", src: ["lateSubmittal"], std: "subm", who: "pm", fix: "subChase", where: "Submittals · Home" },
  { id: "p.inspections", roles: ["pm", "foreman"], area: "Three Weeks Out", label: "Inspections to Book", src: ["inspToBook"], std: "subm", who: "pm", fix: "open", where: "Inspections" },
  { id: "p.subs", roles: ["pm", "foreman"], area: "Three Weeks Out", label: "Subs Not Confirmed", src: ["subsAhead"], std: "chasePeople", who: "pm", fix: "open", where: "Caught for You" },
  { id: "p.tasks", roles: ["pm"], area: "Three Weeks Out", label: "Tasks Behind", src: ["lateTasks", "slip"], std: "lateTasks", who: "pm", fix: "open", where: "Caught for You · Needs Your Hand" },
  { id: "p.cos", roles: ["pm"], area: "Money", label: "Change Orders Unpriced or Unsigned", src: ["needsCO", "unsigned"], std: "nyh:needco", who: "pm", fix: "open", saves: "unbilled", where: "Do Now · Caught for You" },
  { id: "p.unbudgeted", roles: ["pm"], area: "Money", label: "Unbudgeted Cost Over the Limit", src: ["unbudgeted"], std: "std:unbudgeted1k", who: "pm", fix: "escalation", where: "Needs Your Hand (the owner's)" },
  { id: "p.client", roles: ["pm"], area: "Client", label: "Client Messages Unanswered", src: ["clientAck"], std: "std:clientAck", who: "pm", fix: "clientAck", where: "Do Now · Inbox" },
  { id: "p.friday", roles: ["pm"], area: "Client", label: "The Friday Update", src: ["friday"], std: "std:fridayUpdate", who: "pm", fix: "friday", where: "Caught for You (Standard Watch)" },
  // ---- operations and procurement
  { id: "q.lead", roles: ["coord"], area: "Orders", label: "Lead Times and Promised Dates", src: ["promisesBroken"], std: "promisesBroken", who: "coord", fix: "open", where: "order tracking" },
  { id: "q.quotes", roles: ["coord"], area: "Price", label: "Three Quotes", src: ["threeQuotes"], std: "std:threeQuotes", who: "coord", fix: "quotes", where: "Standard Watch · RFQs" },
  { id: "q.gate", roles: ["coord"], area: "Orders", label: "The Submittal Gate", same: "p.submittals", why: "The gate refuses a PO at issue; a line waiting on its submittal shows under Late Submittals." },
  { id: "q.late", roles: ["coord"], area: "Orders", label: "Paid, Not Delivered", src: ["notDelivered"], std: "pwNotDelivered", who: "coord", fix: "open", where: "Caught for You (price watch)" },
  { id: "q.credits", roles: ["coord"], area: "Money Back", label: "Credits Not Received", src: ["creditsOwed"], std: "unmatchedCredit", who: "coord", fix: "creditChase", saves: "waste", where: "Returns · Caught for You" },
  { id: "q.twice", roles: ["coord"], area: "Money Back", label: "Bought More Than Ordered", src: ["boughtTwice"], std: "pwQtyOver", who: "coord", fix: "open", saves: "waste", where: "Caught for You (price watch)" },
  { id: "q.stock", roles: ["coord"], area: "Money Back", label: "Bought While in Stock", src: ["stock"], std: "boughtWhileInStock", who: "coord", fix: "open", saves: "waste", where: "Caught for You (stock)" },
  { id: "q.price", roles: ["coord"], area: "Price", label: "Paid More Than the Best Price", src: ["paidMore"], std: "pwPaidMore", who: "coord", fix: "open", saves: "price", where: "Caught for You (price watch)" },
  // ---- the foreman (no money on any line)
  { id: "f.log", roles: ["foreman"], area: "Every Day", label: "Daily Log With Photos", src: ["dailyLog"], std: "std:dailyLog", who: "foreman", fix: "open", where: "Daily Log" },
  { id: "f.requests", roles: ["foreman"], area: "Every Day", label: "Material Requests Five Days Ahead", src: ["request5"], std: "std:request5days", who: "foreman", fix: "open", where: "Requests" },
  { id: "f.plans", roles: ["foreman"], area: "Build It Right", label: "Current Drawings Acknowledged", src: ["plansAck"], std: "plansNotAcked", who: "foreman", fix: "open", where: "Drawings" },
  { id: "f.questions", roles: ["foreman"], area: "Build It Right", label: "Site Questions Open", src: ["siteQuestions"], std: "raise", who: "pm", fix: "open", where: "Raise · Approvals" },
  { id: "f.quality", roles: ["foreman"], area: "Build It Right", label: "Quality Checkpoints", missing: "Layout, rough-in, pre-close, finish and punch checkpoints are not recorded as steps with photos yet." },
  // ---- billing
  { id: "b.rebill", roles: ["billing"], area: "Bill It", label: "Cost Not Billed Back", src: ["costNotBilled", "rebill"], std: "costNotBilled", who: "billing", fix: "invoice", saves: "unbilled", where: "Caught for You · Needs Your Hand" },
  // ---- the designer
  { id: "d.questions", roles: ["designer"], area: "The Field", label: "Field Questions Past Two Days", src: ["designer2days"], std: "std:designer2days", who: "designer", fix: "open", where: "Do Now (Standard Watch)" },
  { id: "d.plans", roles: ["designer"], area: "The Field", label: "Drawings Waiting on an Amendment", src: ["plansAmend"], std: "plansAmendment", who: "designer", fix: "open", where: "Caught for You (plans)" },
  { id: "d.selections", roles: ["designer"], area: "Selections", label: "Selections Schedule Complete", missing: "Each selection's spec, supplier, price, lead time and approval date is not checked for gaps as one rule yet (the verifier checks each item)." },
];
const RS_ROLE_LABEL = { owner: "Founder", controller: "Controller", billing: "Billing", pm: "PM", coord: "Procurement", foreman: "Foreman", designer: "Designer" };
const rsRoleOf = (r) => ("design_mgr" === r ? "designer" : r);
const rsChecksFor = (r) => RS_CHECKS.filter((c) => c.roles.includes(rsRoleOf(r)));
const rsCheck = (id) => RS_CHECKS.find((c) => c.id === id) || null;

// ---- 5. findings: a line's rows, less what was dismissed in that form ------------------------------------------------
const rsForm = (check, row) => `${check.id}|${row.key}|${Math.round(+row.amount || 0)}`;
const RS_NO_MONEY = /(?:−|-)?\$[\d,]+(?:\.\d+)?k?/g;
function rsLineRows(check) {
  if (!check || !check.src) return [];
  const seen = new Set(),
    out = [];
  check.src.forEach((s) => {
    let R = [];
    try {
      R = (RS_SRC[s] ? RS_SRC[s]() : []) || [];
    } catch (e) {
      console.warn("specialist source", s, e);
    }
    R.forEach((r) => r && r.key && !seen.has(r.key) && (seen.add(r.key), out.push(Object.assign({ src: s }, r))));
  });
  return out;
}
// The checklist of a role, as the signed-in person reads it: each line with its rows (findings), its count, and the
// lines nothing checks yet. A field person never reads a dollar (the money lines are not theirs; amounts are dropped).
function rsChecklist(r) {
  const S = rsInit(),
    rr = rsRoleOf(r || role()),
    noMoney = rsIsField(role()) || rsIsField(rr);
  return rsChecksFor(rr).map((c) => {
    if (c.missing || c.same) return { check: c, rows: [], n: 0 };
    const rows = rsLineRows(c)
      .map((row) => {
        const f = { key: c.id + "|" + row.key, form: rsForm(c, row), check: c, row: row, what: row.what, sub: row.sub, amount: noMoney ? 0 : +row.amount || 0, case: S.cases[c.id + "|" + row.key] || null };
        noMoney && ((f.sub = String(f.sub || "").replace(RS_NO_MONEY, "").replace(/\s+·\s+·/g, " ·").trim()), (f.what = String(f.what || "").replace(RS_NO_MONEY, "").trim()));
        return f;
      })
      .filter((f) => !S.dismissed[f.form]);
    return { check: c, rows: rows, n: rows.length };
  });
}
const rsFindings = (r) => rsChecklist(r).flatMap((L) => L.rows);
function rsFinding(key, r) {
  const id = String(key).split("|")[0],
    c = rsCheck(id);
  if (!c) return null;
  const S = rsInit(),
    rows = rsLineRows(c),
    row = rows.find((x) => c.id + "|" + x.key === key);
  if (!row) return null;
  const noMoney = rsIsField(role());
  return { key: key, form: rsForm(c, row), check: c, row: row, what: noMoney ? String(row.what).replace(RS_NO_MONEY, "") : row.what, sub: noMoney ? String(row.sub || "").replace(RS_NO_MONEY, "") : row.sub, amount: noMoney ? 0 : +row.amount || 0, case: S.cases[key] || null, viewRole: r || role() };
}

// ---- 6. the six steps ---------------------------------------------------------------------------------------------
// 1. the rule and the evidence
function rsEvidence(f) {
  const R = f.row.rec || {},
    ev = [];
  R.b && ev.push({ label: `Bill ${R.b.number || ""} · ${R.b.vendor} · ${money(billTotal(R.b))}`, run: () => openBill(R.b.id) });
  R.twin && R.twin.vendor && R.twin.number && ev.push({ label: `Bill ${R.twin.number} · ${fmtL(R.twin.date)}`, run: () => openBill(R.twin.id) });
  R.po && ev.push({ label: `${R.po.number} · ${R.po.vendor} · ${money(poTotal(R.po).total)}`, run: flowGo.po(R.po) });
  R.t && ev.push({ label: `Bank line · ${R.t.desc || R.t.vendor} · ${money(Math.abs(+R.t.amt || 0))} · ${fmtL(R.t.date)}`, run: () => txnDialog(R.t.id) });
  R.twin && R.twin.acct && ev.push({ label: `Bank line · ${R.twin.desc || R.twin.vendor} · ${fmtL(R.twin.date)}`, run: () => txnDialog(R.twin.id) });
  R.v && ev.push({ label: `Vendor · ${R.v.name}${R.v.insuranceExp ? " · insurance to " + fmtL(R.v.insuranceExp) : " · no insurance on file"}`, run: () => setView("vendors") });
  R.p && ev.push({ label: `Job · ${rsJob(R.p)}`, run: () => (setCurrent(R.p.id), setView("dash")) });
  R.s && ev.push({ label: `Submittal ${R.s.number} · ${R.s.title}`, run: f.row.run });
  R.d && ev.push({ label: `Decision · ${String(R.d.name || "").replace(/ — .*$/, "")}`, run: f.row.run });
  R.q && ev.push({ label: `Portal question · ${String(R.q.text || "").slice(0, 50)}`, run: f.row.run });
  R.buy && ev.push({ label: `Buy Board · ${R.buy.name}`, run: () => setView("proc") });
  R.line && ev.push({ label: `Budget line · ${R.line.name}`, run: f.row.run });
  ev.length || ev.push({ label: f.what, run: f.row.run });
  rsIsField(role()) && ev.forEach((e) => (e.label = e.label.replace(RS_NO_MONEY, "").replace(/\s·\s*$/, "")));
  return ev;
}
// 2. the root cause, from the records; mail and documents only the reader may read (their own mailbox, the firm's
// shared one) and never for a field role
function rsMailFor(terms) {
  if (rsIsField(role())) return [];
  const me = ("function" == typeof paMe ? paMe() : rsMe()).id,
    T = terms.filter((t) => t && String(t).length > 2).map((t) => String(t).toLowerCase());
  if (!T.length) return [];
  return (DB.comms || [])
    .filter((c) => (!c.owner || c.owner === me) && "ignored" !== c.status && T.some((t) => `${c.subject || ""} ${c.snippet || ""} ${(c.from || {}).name || ""} ${(c.from || {}).email || ""}`.toLowerCase().includes(t)))
    .sort((a, b) => String(b.date || "").localeCompare(a.date || ""))
    .slice(0, 3)
    .map((c) => ({ id: c.id, owner: c.owner || "", line: `${c.subject || "(no subject)"} · ${(c.from || {}).name || (c.from || {}).email || ""} · ${fmtL(String(c.date || "").slice(0, 10))}` }));
}
function rsCause(f) {
  const R = f.row.rec || {},
    L = [];
  try {
    if (R.b) {
      const b = R.b,
        P = "function" == typeof pay3PO ? pay3PO(b) : null;
      P && P.po && L.push(`${b.number} is ${money(billTotal(b))}; ${P.po.number} has ${money(P.left)} left on it.`);
      b.notes && L.push(`The bill's note: "${String(b.notes).slice(0, 140)}".`);
      (b.approvals || []).slice(-2).forEach((a) => L.push(`${a.by} (${a.role}) ${a.action}${a.note ? `: "${String(a.note).slice(0, 100)}"` : ""}${a.t ? ", " + a.t : ""}.`));
      b.terms && L.push(`Terms on the bill: ${b.terms}; it is ${b.status}.`);
      R.disc && L.push(R.disc.missed ? `The window closed ${fmtL(R.disc.discBy)} while the bill was ${b.status}: it was not approved in time to pay early.` : `The window closes ${fmtL(R.disc.discBy)}; the bill is ${b.status}${"approved" === b.status ? ", so it can be paid now" : ", so it has to be approved first"}.`);
    }
    if (R.t) {
      L.push(`${R.t.desc || R.t.vendor} for ${money(Math.abs(+R.t.amt || 0))} on ${fmtL(R.t.date)}${R.t.prov && R.t.prov.kind ? ", from the " + R.t.prov.kind : R.t.source === "manual" ? ", typed by hand" : ""}.`);
      R.twin && L.push(`The same payee and amount ${Math.abs(dayDiff(R.twin.date, R.t.date))} day(s) apart, on the same account (${fmtL(R.twin.date)}).`);
    }
    if (R.v) {
      const n = String(R.v.name).toLowerCase(),
        open = (DB.pos || []).filter((po) => String(po.vendor || "").toLowerCase() === n && ["issued", "partial", "pending"].includes(po.status));
      L.push(`${R.v.name}: ${R.v.insuranceExp ? `insurance ran to ${fmtL(R.v.insuranceExp)}` : "no certificate on file"}; ${open.length} open order${1 === open.length ? "" : "s"}${open.length ? ` (${open.map((po) => po.number).join(", ")})` : ""}; W-9 ${R.v.w9 ? "on file" : "not on file"}.`);
    }
    if (R.buy) {
      const r = R.buy;
      L.push(`${r.name}: lead time ${r.lead || "?"} days, needed ${fmtL(r.needBy)}${r.task ? ` for ${r.task.name || r.task}` : ""}, so it had to be ordered by ${fmtL(r.orderBy)}.`);
      r.vendor && L.push(`Its vendor on the line: ${r.vendor}.`);
    }
    if (R.s) {
      R.late && R.late.why && L.push(`It is late because ${R.late.why}.`);
      R.ball && R.ball.who && L.push(`The ball is with ${R.ball.who} (${R.ball.role || ""}) since ${fmtL(R.ball.since)}: ${R.ball.days} day(s), ${R.ball.allowed} allowed.`);
    }
    if (R.q) L.push(`${R.q.by || "The client"} asked ${String(R.q.at).length > 10 ? stampText(R.q.at) : fmtL(R.q.at)}; ${Math.floor(stdWorkHoursSince(R.q.at))} business hours since, the Standard asks for ${rsT("clientAckHours")}.`);
    if (R.cash) L.push(`On the bank: ${money(R.cash.cout)} out for this job, ${money(R.cash.cin)} in. ${(() => {
      try {
        const rtb = readyToBill().rows.filter((x) => x.p && x.p.id === R.p.id).reduce((a, x) => a + (+x.amount || 0), 0);
        return rtb ? `${money(rtb)} is earned and ready to bill on it.` : "Nothing on it is ready to bill.";
      } catch (e) {
        return "";
      }
    })()}`);
    if (R.line) L.push(`${R.line.name}: budget ${money(R.line.budget)}, actual ${money(R.line.actual)}, committed ${money(R.line.committed)}.`);
    if (R.wl) L.push(R.wl.sub);
  } catch (e) {}
  L.length || L.push(f.sub || f.what);
  const R0 = f.row.rec || {},
    terms = [R0.b && R0.b.vendor, R0.b && R0.b.number, R0.po && R0.po.number, R0.v && R0.v.name, R0.t && R0.t.vendor, R0.s && R0.s.number, R0.s && R0.s.sub, R0.buy && R0.buy.name];
  const docs = (DB.docs || []).filter((d) => (R0.b && d.billId === R0.b.id) || (R0.po && d.poId === R0.po.id) || (R0.t && d.txnId === R0.t.id)).slice(0, 3).map((d) => `${d.kind || "document"}${d.name ? " · " + d.name : ""}${d.at ? " · " + fmtL(String(d.at).slice(0, 10)) : ""}`);
  rsIsField(role()) && L.forEach((x, i) => (L[i] = x.replace(RS_NO_MONEY, "")));
  return { lines: L, mail: rsMailFor(terms), docs: docs };
}
// 3. options, a recommendation and the fix, drafted. kind: what is drafted (the planted bank checks it).
const rsVendor = (name) => (DB.vendors || []).find((v) => String(v.name).toLowerCase() === String(name || "").toLowerCase()) || null;
function rsDraftMail(f, o) {
  const me = rsMe(),
    S = rsInit(),
    c = S.cases[f.key] || {};
  if (c.draftId && (DB.outbox || []).some((x) => x.id === c.draftId && "draft" === x.status)) return (DB.outbox || []).find((x) => x.id === c.draftId);
  DB.outbox = DB.outbox || [];
  const d = { id: uid("ox"), kind: "specialist", to: o.to || {}, subject: o.subject, body: o.body, about: { label: f.what, spKey: f.key, projectId: (f.row.rec && f.row.rec.p && f.row.rec.p.id) || "" }, aboutKey: "sp|" + f.key, forName: o.forName || me.name || "", status: "draft", at: today(), by: "Assistant", because: standardWhy(f.check.std) };
  DB.outbox.push(d);
  return d;
}
const RS_FIX = {
  open: (f) => ({ kind: "open", label: f.row.verb || "Open the Record", rec: `Open it and put it right at the record: ${f.what}.`, options: ["Put it right on the record now", "Hand it to the person who owns it", "Dismiss it with the reason it is not a problem"], apply: () => f.row.run && f.row.run() }),
  shortpay(f) {
    const b = f.row.rec.b,
      P = b && "function" == typeof pay3PO ? pay3PO(b) : null,
      over = r2(f.amount),
      co = rsCatch("coNeeded").find((r) => r.key === "coneed:" + (b && b.id));
    return {
      kind: "shortpay",
      label: "Approve to the PO and Dispute the Difference",
      who: "owner",
      rec: co ? `Approve ${b.number} to ${P && P.po ? P.po.number : "the PO"} and dispute ${money(over)}; the bill's note says the extra was added in the field, so write the change order and bill it to the client too.` : `Approve ${b.number} to ${P && P.po ? P.po.number : "the PO"} and dispute ${money(over)}, asking ${b.vendor} for a credit memo.`,
      options: [`Approve to the PO, dispute ${money(over)} (recommended)`, "Approve as billed, with the reason (a priced extra the client signs for)", `Revise ${P && P.po ? P.po.number : "the PO"} if the extra was ordered`],
      preview: `A credit-memo request to ${b.vendor} is drafted for your approval, and the short-pay sheet opens with ${money(P ? P.left : 0)} approved.`,
      apply: () => {
        const v = rsVendor(b.vendor) || {};
        rsDraftMail(f, { to: { name: b.vendor, email: v.email || "" }, subject: `${b.number}: credit memo for ${money(over)} over ${P && P.po ? P.po.number : "our PO"}`, body: `Hello,\n\nYour invoice ${b.number} is ${money(billTotal(b))}. Our purchase order ${P && P.po ? P.po.number : ""} covers ${money(P ? P.left : 0)}. We are paying to the PO and holding ${money(over)} until we receive a credit memo or a signed change.\n\nThank you,\n${rsMe().name || ""}`, forName: (rsUserOfRole("owner") || {}).name });
        "function" == typeof billAction && isOwner() && billAction(b, "short");
      },
    };
  },
  dispute(f) {
    const t = f.row.rec.t;
    return { kind: "dispute", label: "Dispute the Duplicate", who: "controller", rec: t ? `Dispute the second ${money(Math.abs(+t.amt || 0))} with the card or bank issuer (a typed copy is voided instead), with the first line as the evidence.` : "Open the duplicate and dispute or void the second charge.", options: ["Dispute the second charge with the issuer (recommended)", "Void the typed copy if the statement holds it once", "Mark it not a duplicate, with the reason"], preview: "The dispute sheet opens with the reason filled in; the ledger reverses nothing until you confirm.", apply: () => (t && "function" == typeof lkDupSheet && "proposed" === t.dupState ? lkDupSheet(t) : f.row.run && f.row.run()) };
  },
  coiRequest(f) {
    const v = f.row.rec.v || (f.row.rec.b && rsVendor(f.row.rec.b.vendor)) || {};
    return { kind: "coiRequest", label: "Ask for the Certificate", who: "coord", rec: `Ask ${v.name || "the vendor"} for a current certificate of insurance naming SmartDesign; no new PO and no payment until it lands.`, options: ["Ask for the certificate today (recommended)", "Hold their payments and orders until it lands (the Payment Check already does)", "Owner override with a reason, for one payment"], preview: `A request to ${v.name || "the vendor"} is drafted for your approval.`, apply: () => rsDraftMail(f, { to: { name: v.name || "", email: v.email || "" }, subject: "Current certificate of insurance", body: `Hello,\n\nOur file shows ${v.insuranceExp ? `your insurance certificate expired on ${fmtL(v.insuranceExp)}` : "no insurance certificate for you"}. Please send a current certificate naming SmartDesign as additional insured. We cannot release payments or new orders until it is on file.\n\nThank you,\n${rsMe().name || ""}`, forName: (rsUserOfRole("coord") || {}).name }) };
  },
  w9Request(f) {
    const v = f.row.rec.v || {};
    return { kind: "w9Request", label: "Ask for the W-9", who: "controller", rec: `Ask ${v.name} for a W-9 before the next payment; the 1099 is due in January.`, options: ["Ask for the W-9 (recommended)", "Mark them exempt with the reason"], preview: `A W-9 request to ${v.name} is drafted for your approval.`, apply: () => rsDraftMail(f, { to: { name: v.name, email: v.email || "" }, subject: "W-9 for our records", body: `Hello,\n\nPlease send a signed W-9 so we can keep paying you on time and file the 1099 in January.\n\nThank you,\n${rsMe().name || ""}` }) };
  },
  invoice: (f) => ({ kind: "invoice", label: "Draft the Invoice", who: "billing", rec: `Bill it now: ${f.what}. The Standard asks for invoices within 2 business days of the milestone.`, options: ["Draft the invoice from the earned lines (recommended)", "Hold it with the reason (a line still being measured)"], preview: "The invoice opens drafted from the earned lines; nothing is sent until billing sends it.", apply: () => f.row.run && f.row.run() }),
  payEarly(f) {
    const D = f.row.rec.disc,
      b = f.row.rec.b;
    return D && D.missed
      ? { kind: "discountAsk", label: "Ask to Keep the Discount", who: "controller", rec: `The window closed ${fmtL(D.discBy)}. Pay it now and ask ${b.vendor} to honour the ${money(D.save)} discount; approve bills on terms the day they land so the next one is not missed.`, options: ["Ask the vendor to honour it (recommended)", "Pay the full amount and record why"], preview: `A note to ${b.vendor} is drafted for your approval.`, apply: () => rsDraftMail(f, { to: { name: b.vendor, email: (rsVendor(b.vendor) || {}).email || "" }, subject: `${b.number}: early-pay discount`, body: `Hello,\n\nWe are paying ${b.number} now. It reached us inside your ${D.terms} window; would you honour the ${money(D.save)} discount on this one?\n\nThank you,\n${rsMe().name || ""}` }) }
      : { kind: "payEarly", label: "Pay Early and Keep the Discount", who: "controller", rec: `Pay ${b.vendor} ${b.number} by ${fmtL(D ? D.discBy : "")} and keep ${money(D ? D.save : 0)}.`, options: ["Pay by the discount date (recommended)", "Let it run to the due date (only if cash is short)"], preview: "approved" === b.status ? "The payment sheet opens with the discounted amount; the Payment Check runs before anything leaves." : `${b.number} is ${b.status}: it opens for approval first.`, apply: () => ("approved" === b.status && "function" == typeof pcPaySheet ? pcPaySheet(b.id) : openBill(b.id)) };
  },
  order: (f) => ({ kind: "order", label: "Order It", who: "coord", rec: `Order ${f.row.rec.buy ? f.row.rec.buy.name : "it"} today, or move the date it is needed on the schedule with the PM.`, options: ["Order it today (recommended)", "Move the need-by date with the PM, and tell the client if the finish moves"], preview: "The order sheet opens filled from the line: vendor, price, quantity and the on-site date.", apply: () => f.row.run && f.row.run() }),
  subChase(f) {
    const s = f.row.rec.s || {},
      v = rsVendor(s.sub) || {};
    return { kind: "subChase", label: "Chase the Submittal", who: "pm", rec: `Ask ${s.sub || "the sub"} for ${s.number} by a date that still protects the order-by date${f.row.rec.late && f.row.rec.late.why ? ` (${f.row.rec.late.why})` : ""}.`, options: ["Chase the sub with a date (recommended)", "Move the task on the look-ahead if it cannot make it"], preview: `A note to ${s.sub || "the sub"} is drafted for your approval.`, apply: () => rsDraftMail(f, { to: { name: s.sub || "", email: v.email || "" }, subject: `${s.number}: submittal needed`, body: `Hello,\n\n${s.number} (${s.title}) is late${f.row.rec.late && f.row.rec.late.why ? `: ${f.row.rec.late.why}` : ""}. Please send it by ${fmtL(rsWorkAdd(today(), 2))} so the order goes out on time.\n\nThank you,\n${rsMe().name || ""}` }) };
  },
  clientAck: (f) => ({ kind: "clientAck", label: "Answer the Client", who: "pm", rec: "Acknowledge now, with when the full answer comes; never end the day with a client question open.", options: ["Answer now (recommended)", "Acknowledge now and answer by a set time"], preview: "Your reply opens with an answer drafted from the job's records; nothing goes to the client until you send it.", apply: () => f.row.run && f.row.run() }),
  friday(f) {
    const p = rsProj(String(f.row.key).replace(/^upd:/, ""));
    return { kind: "friday", label: "Draft the Friday Update", who: "pm", rec: `Send ${p ? rsJob(p) : "the client"} the week's update: what was done, what is next, what we need from them.`, options: ["Approve the drafted update (recommended)", "Write it yourself"], preview: "Drafted from this week's daily logs, progress and photos; it waits on your Approvals.", apply: () => p && rsFridayDraft(p) };
  },
  cashNeg(f) {
    const p = f.row.rec.p;
    let rtb = null;
    try {
      rtb = readyToBill().rows.find((x) => x.p && x.p.id === p.id);
    } catch (e) {}
    return rtb ? { kind: "invoice", label: "Bill What Is Earned", who: "billing", rec: `Bill ${rsJob(p)} now: ${money(rtb.amount)} is earned and not billed.`, options: ["Bill the earned work (recommended)", "Escalate to the owner with the cause"], preview: "The invoice opens drafted; nothing goes to the client until billing sends it.", apply: () => rtbAct(blRtbKey(rtb)) } : { kind: "escalation", label: "Escalate With the Cause", who: "owner", rec: `Nothing on ${rsJob(p)} is ready to bill: the owner decides (a deposit call, a draw, or a change order), in the Standard's format.`, options: ["Escalate to the owner today (recommended)", "Ask the client for the next draw"], preview: "A task for the owner is made with the escalation: what happened, the impact, the options and the deadline.", apply: () => rsEscalate(f) };
  },
  overBudget(f) {
    const co = rsCatch("coNeeded")[0],
      big = f.amount > rsT("unbudgeted");
    return { kind: big ? "escalation" : "co", label: big ? "Escalate to the Owner" : "Price It as a Change", who: big ? "owner" : "pm", rec: big ? `${money(f.amount)} past the budget is over the ${money(rsT("unbudgeted"))} line: escalate to the owner today with the cause; if the client asked for it, write the change order.` : "If the client caused it, write the change order; if we did, revise the forecast and say why.", options: ["Write the change order if the client caused it", "Revise the forecast with the reason", "Escalate to the owner"], preview: big ? "A task for the owner with the escalation in the Standard's format." : co ? "The change order opens prefilled from the line." : "The job's costs open on the line.", apply: () => (big ? rsEscalate(f) : co ? co.run() : f.row.run && f.row.run()) };
  },
  escalation: (f) => ({ kind: "escalation", label: "Escalate in the Standard's Format", who: "owner", rec: "Raise it to the owner today: what happened, the impact on cost, schedule and quality, the options, the recommendation and the deadline.", options: ["Escalate now (recommended)", "Fix it first and report it"], preview: "A task for the owner carrying the escalation text.", apply: () => rsEscalate(f) }),
  decisionChase: (f) => ({ kind: "decisionChase", label: "Bring the Decision", who: "pm", rec: "Bring it to the client with options and a recommendation, and the date the schedule needs it.", options: ["Send the client the choice with a recommendation (recommended)", "Move the date if the schedule allows"], preview: "The decision opens with its options to send.", apply: () => f.row.run && f.row.run() }),
  quotes: (f) => ({ kind: "quotes", label: "Ask Two More Vendors", who: "coord", rec: `Get the other quotes the rule asks for (over ${money(rsT("threeQuotes"))} and every subcontract), at least one from outside Manhattan and Brooklyn.`, options: ["Open a request for quotes on its lines (recommended)", "Record why one source is enough (a sole supplier)"], preview: "A request for quotes opens.", apply: () => ("function" == typeof rfqNewSheet ? rfqNewSheet() : setView("rfq")) }),
  chaseInvoice(f) {
    return { kind: "chaseInvoice", label: "Send the Reminder", who: "billing", rec: "Remind on the due date, call at 7 days, the PM at 15, leadership at 30 (the collections cadence).", options: ["Send the reminder (recommended)", "Call today and log it"], preview: "The reminder opens drafted.", apply: () => f.row.run && f.row.run() };
  },
  creditChase(f) {
    const r = f.row.rec.ret;
    return { kind: "creditChase", label: "Chase the Credit", who: "coord", rec: r ? `Ask ${r.vendor} for the ${money(retExpected(r))} credit on ${r.name}.` : "Match the credit to its return, or chase it.", options: ["Chase the vendor (recommended)", "Match it to the bank line if it came"], preview: r ? `A note to ${r.vendor} is drafted for your approval.` : "The match opens.", apply: () => (r ? rsDraftMail(f, { to: { name: r.vendor, email: (rsVendor(r.vendor) || {}).email || "" }, subject: `Credit for returned ${r.name}`, body: `Hello,\n\nWe returned ${r.name}${r.tracking ? ` (${r.carrier} ${r.tracking})` : ""}. We have not seen the ${money(retExpected(r))} credit yet; please confirm when it will post.\n\nThank you,\n${rsMe().name || ""}` }) : f.row.run && f.row.run()) };
  },
  receipt: (f) => ({ kind: "receipt", label: "Ask for the Receipt", who: "controller", rec: "Ask whoever holds the card for the receipt and the job, or code it to overhead with the reason.", options: ["Ask for the receipt (recommended)", "Code it with the reason"], preview: "The line opens to attach the receipt.", apply: () => f.row.run && f.row.run() }),
  moveWork(f) {
    const W = f.row.rec.wl || {},
      mv = W.move;
    return mv ? { kind: "moveWork", label: `Offer ${mv.tasks.length} to ${mv.to.name}`, who: mv.manager, rec: `Take ${mv.tasks.length} task${1 === mv.tasks.length ? "" : "s"} off ${W.u.name}'s plate: offer them to ${mv.to.name}, who has ${mv.to.open} open and nothing overdue. They stay with ${W.u.name.split(" ")[0]} until ${mv.to.name.split(" ")[0]} accepts.`, options: [`Offer them to ${mv.to.name} (recommended)`, "Move the due dates with the person", "Leave it, with the reason"], preview: mv.tasks.map((x) => x.title).slice(0, 4).join(" · "), apply: () => wlApply(W) } : RS_FIX.open(f);
  },
};
function rsFix(f) {
  const F = RS_FIX[f.check.fix] || RS_FIX.open;
  let x = null;
  try {
    x = F(f);
  } catch (e) {
    console.warn("specialist fix", f.check.id, e);
  }
  x = x || RS_FIX.open(f);
  return Object.assign({ who: f.check.who }, x, { defaultOn: !!(((DB.company || {}).spDefaults || {})[rsDefKey(f.check.id)]) });
}
// 4. the right person, a due date and why
function rsOwner(f, fix) {
  const r = (fix && fix.who) || f.check.who || "owner",
    p = f.row.rec && f.row.rec.p;
  let u = null;
  "pm" === r && p && "function" == typeof tdyLeadOf && (u = (() => {
    try {
      const n = tdyLeadOf({ projectId: p.id, kind: "action" });
      return n && "function" == typeof tdyUserOf ? tdyUserOf(n.name || n) : null;
    } catch (e) {
      return null;
    }
  })());
  u = u || rsUserOfRole(r) || rsUserOfRole("owner");
  const tier = standardTier(f.check.std),
    due = tier <= 2 ? today() : standardIsLeak(f.check.std) || "escalation" === (fix || {}).kind ? rsWorkAdd(today(), 1) : rsWorkAdd(today(), 2);
  return { name: (u && u.name) || "", uid: (u && u.id) || "", role: r, why: RS_WHO[r] || "it is theirs by the Standard", due: due };
}
function rsTask(f, fix) {
  const S = rsInit(),
    c = (S.cases[f.key] = S.cases[f.key] || rsNewCase(f)),
    O = rsOwner(f, fix);
  if (c.task && rsTaskRec(c.task)) return c.task;
  const p = f.row.rec && f.row.rec.p,
    made = crCreateTask({
      title: `${f.check.label}: ${String(f.what).replace(/^[A-Z][^:]{0,30}:\s/, "")}`.slice(0, 110),
      for: p ? "p:" + p.id : "firm",
      assignee: O.name,
      due: O.due,
      notes: `${standardWhy(f.check.std)}.\nWhy ${O.name}: ${O.why}.\n${f.sub || ""}${fix && fix.rec ? `\nRecommended: ${fix.rec}` : ""}\nThe ${RS_ROLE_LABEL[rsRoleOf(f.check.roles[0])] || ""} checklist closes this when the record itself is fixed, not when the box is ticked.`,
      source: { assistant: !0, label: `${RS_ROLE_LABEL[rsRoleOf(f.check.roles[0])] || "The"} checklist`, specialist: f.key },
      area: rsIsField(O.role) ? "field" : "office",
      handoff: !1,
    });
  if (!made) return null;
  c.task = { kind: made.kind, id: made.id, projectId: made.projectId || "", owner: O.name, due: O.due, why: O.why };
  c.log.push({ at: appNowIso(), ev: "task", by: rsMe().name || "", to: O.name, due: O.due });
  return c.task;
}
const rsNewCase = (f) => ({ key: f.key, check: f.check.id, form: f.form, what: f.what, amount: f.amount, raisedAt: appNowIso(), role: f.check.roles[0], status: "open", log: [] });
function rsTaskRec(T) {
  if (!T) return null;
  try {
    return T.projectId ? (rsProj(T.projectId) && (rsProj(T.projectId).actions || []).find((a) => a.id === T.id)) || null : ("function" == typeof asFirmTasks ? asFirmTasks() : DB.tasks || []).find((a) => a.id === T.id) || null;
  } catch (e) {
    return null;
  }
}
const rsTaskDone = (a) => !!a && ("done" === a.status || !!a.completedAt);
// an escalation to the owner, in the Standard's format, as the owner's task
function rsEscalate(f) {
  const E = standardEscalationText(Object.assign({ what: f.what, sub: f.sub, amount: f.amount }, { src: f.check.std })),
    owner = rsUserOfRole("owner"),
    S = rsInit(),
    c = (S.cases[f.key] = S.cases[f.key] || rsNewCase(f)),
    p = f.row.rec && f.row.rec.p,
    made = crCreateTask({ title: `Escalation: ${String(f.what).slice(0, 90)}`, for: p ? "p:" + p.id : "firm", assignee: owner ? owner.name : "Owner", due: today(), notes: E.join("\n"), source: { assistant: !0, label: "Escalated by the checklist", specialist: f.key }, handoff: !1 });
  made && ((c.escalation = { id: made.id, kind: made.kind, projectId: made.projectId || "", at: appNowIso(), text: E }), c.log.push({ at: appNowIso(), ev: "escalated", by: rsMe().name || "" }));
  return made;
}
// The six steps of one finding, as data (the sheet draws it; the planted bank reads it)
function rsSix(key, r) {
  const f = typeof key === "object" ? key : rsFinding(key, r);
  if (!f) return null;
  const fix = rsFix(f),
    cite = standardCite(standardMapOf(standardKey(f.check.std)).e.c) || {};
  return {
    f: f,
    rule: { text: cite.text || "", label: cite.label || "", why: standardWhy(f.check.std), leak: standardIsLeak(f.check.std) ? STD_WASTE : "" },
    evidence: rsEvidence(f),
    cause: rsCause(f),
    fix: fix,
    owner: rsOwner(f, fix),
    follow: rsFollowText(f),
    learn: { dismissed: !!rsInit().dismissed[f.form], defaultOn: fix.defaultOn },
  };
}
// 5. follow-up: the record is re-read, not the checkbox
function rsFollowText(f) {
  const c = f.case || rsInit().cases[f.key];
  if (!c) return "Not raised yet: approving the fix or making the task starts the follow-up.";
  const T = c.task && rsTaskRec(c.task);
  return c.reopened ? `Reopened ${c.reopened}× : the task was ticked, but the record still shows the problem. It stays open until the record is fixed.` : T ? `Task for ${c.task.owner}, due ${fmtL(c.task.due)}. I re-read the record on every check; when it no longer shows the problem the task closes itself.` : c.fix ? `Fix approved ${fmtL(String(c.fix.at).slice(0, 10))} by ${c.fix.by}; I re-read the record until it is fixed.` : "Raised; waiting on a fix or a task.";
}
function rsSweep() {
  const S = rsInit(),
    open = Object.values(S.cases).filter((c) => "open" === c.status);
  if (!open.length) return 0;
  const byCheck = {},
    noMoney = rsIsField(role());
  let n = 0;
  open.forEach((c) => {
    const C = rsCheck(c.check);
    if (!C || !C.src) return;
    if (noMoney && !rsIsField(C.roles[0])) return;
    byCheck[c.check] = byCheck[c.check] || new Set(rsLineRows(C).map((r) => C.id + "|" + r.key));
    const still = byCheck[c.check].has(c.key),
      T = c.task && rsTaskRec(c.task);
    if (!still) {
      (c.status = "fixed"), (c.fixedAt = appNowIso()), c.log.push({ at: c.fixedAt, ev: "fixed", by: "the record" });
      T && !rsTaskDone(T) && ((T.status = "done"), (T.completedAt = today()), (T.notes = `${T.notes || ""}\nClosed by the checklist: the record is fixed.`.trim()));
      n++;
    } else if (T && rsTaskDone(T)) {
      // ticked, not fixed: reopen it with the reason, once per tick
      (T.status = "todo"), (T.completedAt = ""), (T.notes = `${T.notes || ""}\nReopened ${fmtL(today())}: the box was ticked but the record still shows the problem.`.trim());
      (c.reopened = (c.reopened || 0) + 1), c.log.push({ at: appNowIso(), ev: "reopened", by: "the checklist" });
      n++;
    }
  });
  n && save();
  return n;
}
// 6. learning: a dismissal with a reason, and an approved fix proposed as the default
function rsDismiss(key, why) {
  const f = rsFinding(key);
  if (!f) return toast("That finding is no longer open"), !1;
  if (!String(why || "").trim()) return toast("Say why it is not a problem: the reason is what stops it coming back"), !1;
  const S = rsInit(),
    by = rsMe().name || role();
  S.dismissed[f.form] = { why: String(why).trim(), by: by, at: appNowIso(), check: f.check.id, what: f.what };
  const c = (S.cases[f.key] = S.cases[f.key] || rsNewCase(f));
  (c.status = "dismissed"), c.log.push({ at: appNowIso(), ev: "dismissed", by: by, why: String(why).trim() });
  const T = c.task && rsTaskRec(c.task);
  T && !rsTaskDone(T) && ((T.status = "done"), (T.completedAt = today()), (T.notes = `${T.notes || ""}\nDismissed by ${by}: ${why}`.trim()));
  try {
    audit("specialist", f.key, "dismissed", "", f.what, String(why).trim());
  } catch (e) {}
  save(), render(), toast(`Dismissed: ${tdWords(f.what, 8)}. It will not be raised again in this form.`, [{ label: "Open", run: () => rsOpenChecklist(f.check.roles[0]) }]);
  return !0;
}
function rsApprove(key) {
  const six = rsSix(key);
  if (!six) return toast("That finding is no longer open"), null;
  const { f: f, fix: fix } = six,
    S = rsInit(),
    c = (S.cases[f.key] = S.cases[f.key] || rsNewCase(f)),
    by = rsMe().name || role();
  let out = null;
  try {
    out = fix.apply && fix.apply();
  } catch (e) {
    console.warn("specialist apply", e);
    return toast("That did not work; nothing was changed"), null;
  }
  c.fix = { kind: fix.kind, at: appNowIso(), by: by };
  c.log.push({ at: appNowIso(), ev: "fix", by: by, kind: fix.kind });
  // an emailed fix is a draft on the owner's Approvals: that draft is the task; any other fix gets a task
  const draft = (DB.outbox || []).find((o) => o.aboutKey === "sp|" + f.key && "draft" === o.status);
  draft ? ((c.draftId = draft.id), (draft.forName = draft.forName || six.owner.name), (draft.due = six.owner.due)) : "escalation" === fix.kind || c.task || rsTask(f, fix);
  S.approved[f.check.id] = (S.approved[f.check.id] || 0) + 1;
  rsProposeDefault(f, fix);
  try {
    audit("specialist", f.key, "fix-approved", "", fix.kind, f.what);
  } catch (e) {}
  save();
  // a fix that opens the record's own sheet toasts there, when the person acts on it
  rsQuiet ? 0 : draft
    ? toast(`Drafted for approval: ${draft.subject}`, [{ label: "Open", run: () => ((window.mApprKind = "draft"), setView("mapprove")) }])
    : "escalation" === fix.kind && c.escalation
      ? toast(`Escalated to the owner, due today: ${tdWords(f.what, 6)}`, [{ label: "Open", run: () => setView("tkall") }])
      : c.task && toast(`Task for ${c.task.owner}, due ${fmtL(c.task.due)}: ${tdWords(f.what, 6)}`, [{ label: "Open", run: () => setView("tkall") }]);
  return out || c;
}
function rsProposeDefault(f, fix) {
  if (!fix || !/^(coiRequest|w9Request|subChase|discountAsk|creditChase|friday)$/.test(fix.kind)) return;
  DB.changes = DB.changes || [];
  const key = "sp:default:" + f.check.id;
  if (DB.changes.some((c) => c.key === key)) return;
  DB.changes.push({ id: uid("ch"), key: key, kind: "rule", title: `Draft "${fix.label}" on its own for ${f.check.label}`, why: `${rsMe().name || "A person"} approved this fix on ${fmtL(today())}. Approve it and the ${RS_ROLE_LABEL[rsRoleOf(f.check.roles[0])] || ""} checklist drafts it the moment the finding appears; the draft still waits for a person to send it. ${standardWhy("change")}.`, evidence: [{ t: f.what, m: "the finding" }], delta: { path: `company.spDefaults.${rsDefKey(f.check.id)}`, to: !0 }, status: "draft", at: today(), by: "The checklist", source: "specialist" });
}
// once the owner has approved a default, its drafts are made as the finding appears (still drafts). The path a
// change writes is dotted (company.spDefaults.<key>), so a line's id is stored with its dot as an underscore.
const rsDefKey = (id) => String(id).replace(/\./g, "_");
let rsQuiet = !1;
function rsAutoDrafts() {
  const D = (DB.company || {}).spDefaults || {},
    ids = Object.keys(D).filter((k) => D[k]);
  if (!ids.length) return 0;
  let n = 0;
  ids.forEach((id) => {
    const C = RS_CHECKS.find((x) => rsDefKey(x.id) === id);
    C &&
      C.src &&
      rsLineRows(C).forEach((row) => {
        const key = C.id + "|" + row.key,
          S = rsInit();
        if (S.dismissed[rsForm(C, row)] || (S.cases[key] && S.cases[key].fix)) return;
        const six = rsSix(key);
        if (!six || !/^(coiRequest|w9Request|subChase|discountAsk|creditChase|friday)$/.test(six.fix.kind)) return;
        rsQuiet = !0;
        try {
          rsApprove(key);
        } finally {
          rsQuiet = !1;
        }
        S.cases[key] && S.cases[key].fix && ((S.cases[key].fix.by = "the checklist (the default the owner approved)"), n++);
      });
  });
  return n;
}

// ---- 7. the Friday update, drafted from the week's logs, progress and photos -----------------------------------------
function rsFridayDraft(p) {
  if (!p) return null;
  const dow = parse(today()).getDay(),
    fri = iso(addDays(today(), 6 === dow ? -1 : 0 === dow ? -2 : 5 - dow)),
    from = iso(addDays(fri, -4)),
    key = `fri|${p.id}|${from}`;
  DB.outbox = DB.outbox || [];
  const have = DB.outbox.find((o) => o.aboutKey === key && "skipped" !== o.status);
  if (have) return have;
  const c = (DB.clients || []).find((x) => x.id === p.clientId) || {},
    logs = (((DB.field || {}).logs) || []).filter((l) => l.projectId === p.id && l.date >= from && l.date <= fri),
    photos = logs.reduce((a, l) => a + (l.photos || l.photoIds || []).length, 0),
    did = logs.flatMap((l) => (l.work || l.done || []).map((w) => (w && (w.text || w.what || w.name)) || w)).filter((x) => "string" == typeof x).slice(0, 5),
    next = (p.tasks || []).filter((t) => t.start && t.start > fri && t.start <= iso(addDays(fri, 14)) && "done" !== t.status).slice(0, 4).map((t) => `${t.name} (${fmtL(t.start)})`),
    needs = (p.decisions || []).filter((d) => "Client" === d.owner && "open" === d.status).slice(0, 3).map((d) => String(d.name).replace(/ — .*$/, "")),
    pct = (() => {
      try {
        return Math.round(tpJobPct(p));
      } catch (e) {
        return null;
      }
    })(),
    pm = rsUserOfRole("pm") || {},
    first = String(c.name || "").split(/\s|&/)[0] || "",
    body = `Hi ${first},\n\nHere is where ${rsJob(p)} stands this week${null != pct ? ` (${pct}% complete on site)` : ""}.\n\nThis week: ${did.length ? did.join("; ") : logs.length ? `${logs.length} working day${1 === logs.length ? "" : "s"} on site, logged with ${photos} photo${1 === photos ? "" : "s"}` : "no site days logged"}.\nNext two weeks: ${next.length ? next.join("; ") : "the schedule is unchanged"}.\n${needs.length ? `What we need from you: ${needs.join("; ")}.` : "Nothing is waiting on you."}\n\n${photos ? "Photos from the week are in your portal.\n\n" : ""}Best,\n${pm.name || ""}`,
    o = { id: uid("ox"), kind: "clientUpdate", to: { name: c.name || "", email: c.email || "" }, subject: `${rsJob(p)}: this week`, body: body, about: { projectId: p.id, label: `Friday update · ${rsJob(p)}` }, aboutKey: key, forName: pm.name || "", status: "draft", at: today(), by: "Assistant", because: standardWhy("std:fridayUpdate") };
  DB.outbox.push(o);
  return o;
}
// Friday morning: one draft per live job with a client, for the PM to approve (never sent by itself)
function rsFridaySweep(force) {
  if (!force && 5 !== parse(today()).getDay()) return 0;
  let n = 0;
  (DB.projects || []).filter((p) => rsLive(p) && p.clientId && (p.tasks || []).length).forEach((p) => {
    const before = (DB.outbox || []).length;
    rsFridayDraft(p), (DB.outbox || []).length > before && n++;
  });
  n && save();
  return n;
}

// ---- 8. workload: who is overloaded, and who has room ----------------------------------------------------------------
const WL_GROUP = { owner: "lead", pm: "pm", coord: "coord", billing: "office", controller: "office", foreman: "foreman", crew: "crew", driver: "driver", designer: "design", design_mgr: "design" };
const WL_MANAGER = { lead: "owner", pm: "owner", coord: "owner", office: "owner", foreman: "pm", crew: "pm", driver: "pm", design: "design_mgr" };
// where a lead's work can go when nobody shares the role: office work to the office, job work to the PM
const WL_SPILL = { lead: ["controller", "billing", "pm", "coord"] };
const wlMedian = (A) => {
  const s = A.slice().sort((a, b) => a - b);
  return s.length ? (s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2) : 0;
};
function wlHours7(u) {
  const first = String(u.name || "").split(" ")[0].toLowerCase(),
    emp = (DB.employees || []).find((e) => String(e.name || "").toLowerCase() === String(u.name || "").toLowerCase() || String(e.name || "").split(" ")[0].toLowerCase() === first);
  if (!emp) return null;
  const from = iso(addDays(today(), -7));
  return r2(((DB.time || []).filter((t) => t.empId === emp.id && t.date >= from && t.date <= today())).reduce((a, t) => a + ((t.work || []).reduce((x, w) => x + (+w.hours || 0), 0) || (t.in && t.out ? (Date.parse(t.out) - Date.parse(t.in)) / 36e5 - (+t.breakMin || 0) / 60 : 0)), 0));
}
function wlResp(u) {
  const n = String(u.name || "").toLowerCase(),
    from = iso(addDays(today(), -30)),
    H = (((DB.field || {}).raises) || [])
      .filter((r) => r.answeredAt && String(r.at || "").slice(0, 10) >= from && String(r.answeredBy || r.answerBy || "").toLowerCase().startsWith(n.split(" ")[0]))
      .map((r) => {
        try {
          return (Date.parse(r.answeredAt) - Date.parse(r.at)) / 36e5;
        } catch (e) {
          return null;
        }
      })
      .filter((h) => null != h && h >= 0);
  return H.length ? r2(wlMedian(H)) : null;
}
function wlRows() {
  const U = ("function" == typeof tdyUsers ? tdyUsers() : DB.users || []).filter((u) => WL_GROUP[u.role]),
    T = tkAll({ open: !0 }).filter((t) => !t.approval),
    td = today(),
    R = U.map((u) => {
      const mine = T.filter((t) => t.ownerUid === u.id),
        over = mine.filter((t) => t.due && t.due < td);
      return { u: u, group: WL_GROUP[u.role], open: mine.length, overdue: over.length, tasks: mine, late: over, hours7: wlHours7(u), resp: wlResp(u) };
    }),
    med = wlMedian(R.filter((x) => x.open).map((x) => x.open));
  R.forEach((x) => {
    x.median = med;
    x.over = x.overdue >= 3 || (x.open >= 8 && x.open >= 2 * med);
    x.room = x.overdue === 0 && x.open <= med;
  });
  R.forEach((x) => x.over && (x.move = wlMove(x, R)));
  return R;
}
function wlMove(x, R) {
  const peers = R.filter((y) => y !== x && y.room && (y.group === x.group || (WL_SPILL[x.group] || []).includes(y.u.role))).sort((a, b) => a.open - b.open);
  if (!peers.length) return null;
  const to = peers[0],
    k = Math.max(1, Math.min(x.overdue || 0 || Math.ceil((x.open - x.median) / 2), Math.ceil((x.open - x.median) / 2), 6)),
    movable = x.tasks.filter((t) => /^(firm|action|hub)$/.test(t.kind) && !t.handoff && !t.recur && (!t.projectId || to.u.role !== "billing")).sort((a, b) => String(a.due || "9999").localeCompare(b.due || "9999"));
  const tasks = movable.slice(0, k);
  return tasks.length ? { to: { name: to.u.name, uid: to.u.id, role: to.u.role, open: to.open }, tasks: tasks, manager: WL_MANAGER[x.group] || "owner" } : null;
}
predDef("peopleOverloaded", {
  label: "Overloaded",
  rule: "three or more tasks overdue, or at least eight open and twice the firm's median; a move is proposed to a named person in the same role (or the office, for the owner) with nothing overdue and no more than the median open",
  rows() {
    return wlRows()
      .filter((x) => x.over)
      .map((x) => Object.assign(x, { key: "wl:" + x.u.id, what: `Overloaded: ${x.u.name}`, sub: `${x.open} open, ${x.overdue} overdue (the firm's median is ${x.median})${null != x.hours7 ? `, ${x.hours7} hours in 7 days` : ""}${null != x.resp ? `, answers in ${x.resp} hours` : ""}${x.move ? `; ${x.move.to.name} has room` : "; nobody in the role has room"}` }));
  },
});
// the manager's yes: each task is offered to the named person (a hand-off on the task record; it stays with its
// owner until the other accepts)
function wlApply(W) {
  const mv = W && W.move,
    me = rsMe();
  if (!mv) return 0;
  if (!(isOwner() || role() === mv.manager)) return toast(`The ${mv.manager === "pm" ? "PM" : mv.manager === "design_mgr" ? "design director" : "owner"} approves moving work`), 0;
  let n = 0;
  mv.tasks.forEach((x) => {
    const rec = tdyRec(x);
    if (!rec || (rec.handoff && "offered" === rec.handoff.state)) return;
    rec.handoff = { from: x.owner || W.u.name, fromUid: x.ownerUid || W.u.id, by: me.name || "", to: mv.to.name, toUid: mv.to.uid, at: appNowIso(), state: "offered", note: `Moved off ${W.u.name}'s plate (workload), approved by ${me.name || role()}` };
    tdyLog(rec, { ev: "offered", from: rec.handoff.from, to: mv.to.name, by: me.name || "", note: rec.handoff.note });
    try {
      audit("task", x.id, "handoff", rec.handoff.from, mv.to.name, rec.handoff.note);
    } catch (e) {}
    n++;
  });
  save(), render(), toast(`Offered ${n} task${1 === n ? "" : "s"} to ${mv.to.name}: they stay with ${W.u.name.split(" ")[0]} until accepted`, [{ label: "Open", run: () => setView("tkall") }]);
  return n;
}

// ---- 9. the savings ledger: computed from the records, by source, by person -------------------------------------------
window.SV_SOURCES = window.SV_SOURCES || [];
// who acted, only when the record names a person (an automatic rule or an import is not a person to credit)
const svPerson = (n) => {
  const u = n && "function" == typeof tdyUserOf ? tdyUserOf(n) : null;
  return u ? u.name : "";
};
const SV_KIND = { price: "Price Differences", waste: "Waste Avoided", discount: "Discounts Taken", duplicate: "Duplicates Stopped", unbilled: "Unbilled Work Caught", overrun: "Overruns Caught Early", overpay: "Overpayments Stopped" };
window.SV_SOURCES.push(
  // the Payment Check and the short-pay: a bill over its PO approved to the PO, the difference held back
  function svShortPays() {
    return (DB.bills || [])
      .filter((b) => b.short && +b.short.held > 0 && !/^(accepted|released|paid)$/.test(b.short.state || ""))
      .map((b) => ({ key: "short:" + b.id, kind: "overpay", amount: +b.short.held, date: b.short.on, by: b.short.by || "", what: `${b.vendor} ${b.number}: ${money(b.short.held)} held back over ${b.short.poNumber || "the PO"}`, evidence: [`Bill ${b.number}`, b.short.poNumber ? `PO ${b.short.poNumber}` : "", `Reason: ${b.short.why || ""}`].filter(Boolean), go: () => openBill(b.id) }));
  },
  function svDuplicates() {
    const out = (DB.txns || [])
      .filter((t) => "disputed" === t.dupState && t.dispute)
      .map((t) => ({ key: "dup:" + t.id, kind: "duplicate", amount: Math.abs(+t.amt || 0), date: String(t.dispute.at || "").slice(0, 10), by: t.dispute.by || "", what: `${t.desc}: charged twice, disputed with ${t.dispute.with || "the issuer"}`, evidence: [`Bank line ${fmtL(t.date)}`, `Reason: ${t.dispute.why || ""}`], go: () => txnDialog(t.id) }));
    return out.concat(
      (DB.voided || [])
        .filter((v) => /duplicate|twice/i.test(`${v.why || ""} ${v.reason || ""}`))
        .map((v) => ({ key: "void:" + (v.id || (v.txn && v.txn.id)), kind: "duplicate", amount: Math.abs(+(v.amt || (v.txn && v.txn.amt) || 0)), date: String(v.at || v.on || "").slice(0, 10), by: v.by || "", what: `${(v.txn && v.txn.desc) || v.desc || "A typed line"}: a duplicate voided`, evidence: [`Reason: ${v.why || v.reason || ""}`], go: () => setView("bank") })),
    );
  },
  function svDiscounts() {
    return (DB.bills || [])
      .filter((b) => "paid" === b.status && b.paidAt)
      .map((b) => ({ b: b, tm: "function" == typeof tmOf ? tmOf(b) : null }))
      .filter((x) => x.tm && x.tm.disc > 0 && String(x.b.paidAt).slice(0, 10) <= iso(addDays(x.b.date || today(), x.tm.discDays)))
      .map((x) => ({ key: "disc:" + x.b.id, kind: "discount", amount: r2((billTotal(x.b) * x.tm.disc) / 100), date: String(x.b.paidAt).slice(0, 10), by: x.b.paidBy || svPerson(((DB.txns || []).find((t) => t.billId === x.b.id) || {}).actor), what: `${x.b.vendor} ${x.b.number}: paid inside ${x.tm.label}`, evidence: [`Bill ${x.b.number}`, `Terms ${x.tm.label}`], go: () => openBill(x.b.id) }));
  },
  function svRfqAwards() {
    return ("function" == typeof rfqInit ? rfqInit() : [])
      .filter((r) => r.award && +r.award.savingsVsFirst > 0.005)
      .map((r) => ({ key: "rfq:" + r.id, kind: "price", amount: +r.award.savingsVsFirst, date: r.award.on, by: r.award.by || "", what: `${r.number}: final price under the first quote`, evidence: [`First quote ${money(r.award.firstQuote)}`, `Final ${money(r.award.final)}`, (r.award.numbers || []).join(", ")].filter(Boolean), go: () => ("function" == typeof rfqOpenFor ? rfqOpenFor(r.id) : setView("rfq")) }));
  },
  // a finding the checklist raised, fixed on the record (the amount it was worth when raised)
  function svFindingsFixed() {
    return Object.values(rsInit().cases)
      .filter((c) => "fixed" === c.status && +c.amount > 0 && (rsCheck(c.check) || {}).saves)
      .map((c) => ({ key: "case:" + c.key, kind: rsCheck(c.check).saves, amount: +c.amount, date: String(c.fixedAt || "").slice(0, 10), by: (c.fix && c.fix.by) || (c.task && c.task.owner) || "", what: `${rsCheck(c.check).label}: ${c.what}`, evidence: (c.log || []).map((e) => `${e.ev} ${fmtL(String(e.at).slice(0, 10))}${e.by ? " · " + e.by : ""}`), go: () => rsOpenChecklist(rsCheck(c.check).roles[0]) }));
  },
);
function svRows() {
  const seen = new Set(),
    out = [];
  (window.SV_SOURCES || []).forEach((fn) => {
    let R = [];
    try {
      R = ("function" == typeof fn ? fn() : []) || [];
    } catch (e) {
      console.warn("savings source", fn && fn.name, e);
    }
    R.forEach((r) => {
      // a case and the record it closed are one saving: the record's own source wins (short:b1 over case:...b1)
      r && r.key && +r.amount > 0.005 && !seen.has(r.key) && (seen.add(r.key), out.push(Object.assign({ source: SV_KIND[r.kind] || r.kind || "Other" }, r)));
    });
  });
  const recs = new Set(out.filter((r) => !/^case:/.test(r.key)).map((r) => r.key.split(":").pop()));
  return out.filter((r) => !/^case:/.test(r.key) || !recs.has(r.key.split(":").pop())).sort((a, b) => String(b.date || "").localeCompare(a.date || ""));
}
function svSummary() {
  const R = svRows(),
    td = today(),
    ym = td.slice(0, 7),
    yr = td.slice(0, 4),
    ytd = R.filter((r) => String(r.date || "").slice(0, 4) === yr),
    mo = R.filter((r) => String(r.date || "").slice(0, 7) === ym),
    sum = (A) => r2(A.reduce((a, r) => a + (+r.amount || 0), 0)),
    by = (A, f) => {
      const o = {};
      A.forEach((r) => {
        const k = f(r) || "Not recorded";
        o[k] = r2((o[k] || 0) + (+r.amount || 0));
      });
      return o;
    },
    share = Object.assign({ wage: 0, bonus: 0, charity: 0 }, (DB.company || {}).savingsShare || {}),
    attr = (DB.company || {}).savingsAttr || {},
    tot = sum(ytd);
  return { rows: R, ytd: tot, month: sum(mo), nYtd: ytd.length, bySource: by(ytd, (r) => r.source), byPerson: by(ytd, (r) => r.by), credited: by(ytd.filter((r) => attr[r.key]), (r) => attr[r.key].person), share: share, pools: { wage: r2((tot * (+share.wage || 0)) / 100), bonus: r2((tot * (+share.bonus || 0)) / 100), charity: r2((tot * (+share.charity || 0)) / 100) }, attr: attr };
}
function svSetShare(f) {
  if (!isOwner()) return toast("Only the owner sets the shares"), !1;
  const s = { wage: Math.max(0, +f.wage || 0), bonus: Math.max(0, +f.bonus || 0), charity: Math.max(0, +f.charity || 0) };
  if (s.wage + s.bonus + s.charity > 100) return toast("The three shares add up to more than 100%"), !1;
  const was = JSON.stringify((DB.company || {}).savingsShare || {});
  DB.company.savingsShare = s;
  try {
    audit("company", "savingsShare", "set", was, JSON.stringify(s), "the owner's share of savings to the pools");
  } catch (e) {}
  save(), render(), toast(`Savings shares set: ${s.wage}% wages, ${s.bonus}% bonuses, ${s.charity}% charity`, [{ label: "Open", run: () => rsOpenChecklist("owner") }]);
  return !0;
}
function svCredit(key, person) {
  if (!isOwner()) return toast("Only the owner approves a bonus credit"), !1;
  const r = svRows().find((x) => x.key === key);
  if (!r) return toast("That saving is no longer on the ledger"), !1;
  DB.company.savingsAttr = DB.company.savingsAttr || {};
  DB.company.savingsAttr[key] = { person: person || r.by || "", by: rsMe().name || "Owner", at: appNowIso(), amount: r.amount };
  try {
    audit("savings", key, "credited", "", person || r.by, money(r.amount));
  } catch (e) {}
  save(), render(), toast(`Credited to ${person || r.by}: ${money(r.amount)} (${r.source})`, [{ label: "Open", run: () => rsOpenChecklist("owner") }]);
  return !0;
}

// ---- 10. the screens: the checklist inside Findings, the one-liner on each Home ---------------------------------------
let rsView = "",
  rsViewWho = "";
function rsOpenChecklist(r) {
  (rsView = rsRoleOf(r || role())), (rsViewWho = rsMe().id), "function" == typeof paOpen ? paOpen("findings", "check") : setView("pa");
}
const rsCanSee = () => !["client", "crew", "driver"].includes(role()) && rsChecksFor(role()).length > 0;
const RS_QUICK = { pm: /^Project Manager/i, coord: /^Procurement/i, foreman: /^Foreman/i, crew: /^Field crew/i, driver: /^Field crew/i, designer: /^Designer/i, design_mgr: /^Designer/i, billing: /^Office/i, controller: /^Office/i };
const RS_PB = { foreman: "Capataz", crew: "Cuadrilla" };
// The role's one thing, from the live Standard's quick reference (the owner: its first line); a field person whose
// language is Spanish reads their playbook's mission from the Spanish Standard.
function rsOneLiner(r) {
  r = r || role();
  try {
    if ("function" == typeof esOn && esOn() && RS_PB[r === "driver" ? "crew" : r]) {
      const md = (document.getElementById("sd-standard-es-md") || {}).textContent || "",
        sec = md.split(/\n## /).find((s) => s.startsWith(RS_PB[r === "driver" ? "crew" : r])) || "",
        m = sec.match(/\*\*Misión:\*\*\s+(.+)/);
      if (m) return { text: m[1].trim(), where: "" };
    }
    const Q = standard().quickRef || {};
    if ("owner" === r) return { text: stdStrip((Q.items || [])[0] || ""), where: "The SmartDesign Standard, quick reference" };
    const row = (Q.roles || []).find((x) => RS_QUICK[r] && RS_QUICK[r].test(x.role));
    return row ? { text: row.one, where: row.role } : null;
  } catch (e) {
    return null;
  }
}
function rsOneHtml(r) {
  const O = rsOneLiner(r);
  return O && O.text ? `<p class="rs-one" data-es-skip>${esc(O.text)}${O.where ? ` <span class="muted">· ${esc(O.where)}</span>` : ""}</p>` : "";
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      const v = document.querySelector(".view.on");
      // drawn fresh each time: a screen that keeps its markup between draws would otherwise keep yesterday's language
      if (v && ["home", "ftoday", "sday", "time", "route"].includes(view)) {
        v.querySelectorAll(".rs-one").forEach((e) => e.remove());
        const home = { home: TD_ROLES, ftoday: ["foreman"], sday: ["designer", "design_mgr"], time: ["crew"], route: ["driver"] }[view] || [];
        if (home.includes(role())) {
          const h = v.querySelector(".td-ph h2, .ph h2, h2"),
            box = document.createElement("div");
          box.innerHTML = rsOneHtml(role());
          const el = box.firstElementChild;
          el && (h && h.parentNode ? h.parentNode.insertBefore(el, h.nextSibling) : v.insertBefore(el, v.firstChild));
        }
      }
    } catch (e) {
      console.warn("one-liner", e);
    }
    // the follow-up re-reads open findings at most once a minute while the app is in use
    try {
      const now = Date.now();
      (!rsSweepAt || now - rsSweepAt > 6e4) && ((rsSweepAt = now), Object.values(rsInit().cases).some((c) => "open" === c.status) && setTimeout(() => rsSweep() && "pa" === view && render(), 0));
    } catch (e) {}
    return r;
  };
}
let rsSweepAt = 0;
// the brief, ordered by the role's one thing: the lines about the role's own checklist first, the rest as they were
const RS_BRIEF_FIRST = { owner: /cash|safe|risk|escalat|losing|overloaded/i, pm: /decid|order|submittal|inspect|client|late|look-ahead/i, coord: /order|quote|deliver|vendor|price|lead/i, controller: /bank|match|reconcil|close|bill|payroll|ledger/i, billing: /invoice|bill|collect|deposit|paid|owe/i };
if ("function" == typeof tdBriefLines) {
  const base = tdBriefLines;
  tdBriefLines = function () {
    const L = base.apply(this, arguments) || [],
      rx = RS_BRIEF_FIRST[role()];
    return rx ? L.filter((s) => rx.test(s)).concat(L.filter((s) => !rx.test(s))) : L;
  };
}
// the Findings part: one more segment, the checklist (the same rows the detectors show where they live). paSegsFor
// is a constant, so the segment bar is drawn here: the assistant's own segments with Checklist second.
if ("function" == typeof paPaneHtml) {
  const base = paPaneHtml;
  paPaneHtml = function () {
    try {
      if ("findings" === paTab && rsCanSee()) {
        const isCheck = "check" === paFindSeg;
        isCheck && (paFindSeg = "you");
        let h = "";
        try {
          h = base.apply(this, arguments);
        } finally {
          isCheck && (paFindSeg = "check");
        }
        const S = paSegsFor().slice();
        S.splice(1, 0, ["check", "Checklist"]);
        const seg = `<div class="seg pa-segs" role="tablist" aria-label="Findings">${S.map(([k, l]) => `<button type="button" role="tab" aria-selected="${paFindSeg === k}" class="${paFindSeg === k ? "on" : ""}" data-paseg="${k}">${l}</button>`).join("")}</div>`,
          i = h.indexOf('<div class="seg pa-segs"'),
          cut = [i, h.indexOf('<div class="pa-find">'), h.indexOf('<div id="brain-body">'), h.indexOf('<div id="cos-body">')].filter((x) => x >= 0).sort((a, b) => a - b)[0],
          head = null == cut ? h : h.slice(0, cut),
          rest = isCheck ? `<div class="pa-find rs-pane">${rsPaneHtml()}</div>` : i >= 0 ? h.slice(h.indexOf("</div>", i) + 6) : null == cut ? "" : h.slice(cut);
        return head + seg + rest;
      }
      const h = base.apply(this, arguments);
      return "brain" === paTab && isOwner() ? h + rsThresholdHtml() : h;
    } catch (e) {
      console.warn("checklist pane", e);
      return base.apply(this, arguments);
    }
  };
}
const RS_VIEW_ROLES = ["owner", "controller", "pm", "coord", "billing", "designer", "foreman"];
function rsPaneHtml() {
  const me = rsRoleOf(role());
  // the owner's choice of whose checklist to read is the owner's: another person signing in starts on their own
  rsViewWho !== rsMe().id && ((rsView = ""), (rsViewWho = rsMe().id));
  const r = isOwner() && rsView ? rsView : me;
  rsView = r;
  const L = rsChecklist(r),
    open = L.reduce((a, x) => a + x.n, 0),
    areas = [...new Set(L.map((x) => x.check.area))],
    pick = isOwner() ? `<div class="seg paf-kinds rs-roles" role="tablist" aria-label="Whose Checklist">${RS_VIEW_ROLES.map((k) => `<button type="button" role="tab" aria-selected="${k === r}" class="${k === r ? "on" : ""}" data-rsrole="${k}">${RS_ROLE_LABEL[k]}</button>`).join("")}</div>` : "";
  return `${pick}${rsOneHtml(r)}<p class="small muted rs-lead">The ${esc(RS_ROLE_LABEL[r] || "")} checklist: each line reads the detector that already checks it, so its count is the same rows you see where they live. ${open ? `${open} finding${1 === open ? "" : "s"} open.` : "Nothing open."} Handle one to see the rule, the cause, the drafted fix, the person and the follow-up.</p>
  ${"owner" === r || "controller" === r ? svCardHtml() : ""}${"owner" === r || ("pm" === r && "pm" === me) ? wlCardHtml() : ""}
  ${areas
    .map(
      (a) => `<section class="rs-area"><h4>${esc(a)}</h4>${L.filter((x) => x.check.area === a)
        .map((x) => {
          const c = x.check;
          if (c.missing) return `<div class="rs-line rs-miss" data-rsline="${esc(c.id)}"><div class="rs-l1"><b>${esc(c.label)}</b><span class="rs-n muted">Not Checked</span></div><div class="small muted">${esc(c.missing)}</div></div>`;
          if (c.same) return `<div class="rs-line rs-same" data-rsline="${esc(c.id)}"><div class="rs-l1"><b>${esc(c.label)}</b><span class="rs-n muted">See ${esc((rsCheck(c.same) || {}).label || "")}</span></div><div class="small muted">${esc(c.why || "")}</div></div>`;
          return `<div class="rs-line${x.n ? " rs-has" : ""}" data-rsline="${esc(c.id)}"><div class="rs-l1"><b>${esc(c.label)}</b><span class="rs-n" data-rsn="${x.n}">${x.n ? x.n : "Clear"}</span></div><div class="small muted">Read from ${esc(c.where || "")}</div>${x.rows
            .map((f) => {
              const st = f.case ? ("open" === f.case.status ? (f.case.reopened ? "Reopened: not fixed yet" : f.case.task ? `Task for ${f.case.task.owner}, due ${fmtL(f.case.task.due)}` : f.case.fix ? "Fix approved, re-checking" : "Raised") : "") : "";
              return `<div class="rs-row" data-rskey="${esc(f.key)}"><div class="rs-txt"><div>${esc(f.what)}</div><div class="small muted">${esc(f.sub || "")}${st ? ` · <span class="rs-st">${esc(st)}</span>` : ""}</div></div><button type="button" class="btn sm" data-rshandle="${esc(f.key)}">Handle</button></div>`;
            })
            .join("")}</div>`;
        })
        .join("")}</section>`,
    )
    .join("")}`;
}
function rsSheet(key) {
  const X = rsSix(key);
  if (!X) return toast("That finding is no longer open: the record was fixed"), void render();
  const { f: f, fix: fix, owner: O, cause: C } = X,
    canFix = fix.kind !== "open" || f.row.run,
    num = (n, t) => `<h4 class="rs-step"><span class="rs-sn">${n}</span>${t}</h4>`,
    body = `<div class="rs-six" data-rssix="${esc(f.key)}">
    <p class="rs-what"><b>${esc(f.what)}</b>${f.sub ? `<br><span class="small muted">${esc(f.sub)}</span>` : ""}</p>
    ${num(1, "The Rule and the Evidence")}<p class="small">${esc(X.rule.why)}${X.rule.leak ? ` <span class="muted">${esc(X.rule.leak)}</span>` : ""}</p><div class="rs-ev">${X.evidence.map((e, i) => `<button type="button" class="btn sm" data-rsev="${i}">${esc(e.label)}</button>`).join("")}</div>
    ${num(2, "Root Cause")}<ul class="small rs-cause">${C.lines.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>${rsIsField(role()) ? "" : `<div class="small muted">${C.mail.length ? `Mail you can read: ${C.mail.map((m) => esc(m.line)).join(" · ")}` : "No mail you can read mentions it."}${C.docs.length ? ` Documents: ${C.docs.map(esc).join(" · ")}.` : ""}</div>`}
    ${num(3, "Options and the Recommendation")}<ol class="small">${(fix.options || []).map((o) => `<li>${esc(o)}</li>`).join("")}</ol><p class="small"><b>Recommended:</b> ${esc(fix.rec || "")}</p>${fix.preview ? `<p class="small muted">Drafted: ${esc(fix.preview)}</p>` : ""}
    ${num(4, "The Task")}<p class="small">For <b>${esc(O.name || "nobody yet")}</b>, due ${esc(fmtL(O.due))}: ${esc(O.why)}.</p>${f.case && f.case.task ? `<p class="small muted">Made: on ${esc(f.case.task.owner)}'s list.</p>` : `<button type="button" class="btn sm" data-rstask="${esc(f.key)}">Make the Task for ${esc(String(O.name || "").split(" ")[0] || "Them")}</button>`}
    ${num(5, "Follow-Up")}<p class="small">${esc(X.follow)}</p>
    ${num(6, "Learn")}<p class="small muted">${X.learn.defaultOn ? "The owner made this fix the default: it is drafted as the finding appears, and still waits for a person to send it." : "Approving a fix that drafts a message proposes it as the default, for the owner to approve under Company › Changes."} A dismissal with its reason is never raised again in this form.</p><button type="button" class="btn sm" data-rsdismiss="${esc(f.key)}">Dismiss With a Reason</button>
  </div>`;
  const m = mbModal(esc(f.check.label), body, { submit: canFix ? fix.label : null, onSubmit: () => (mbCloseModal(), rsApprove(f.key), render(), !1) });
  if (!m) return;
  m.querySelectorAll("[data-rsev]").forEach((b) => (b.onclick = () => {
    const e = X.evidence[+b.dataset.rsev];
    mbCloseModal(), e && e.run && e.run();
  }));
  const t = m.querySelector("[data-rstask]");
  t &&
    (t.onclick = () => {
      const made = rsTask(f, fix);
      save(), mbCloseModal(), render();
      made && crToast(`Task for ${made.owner}, due ${fmtL(made.due)}: ${tdWords(f.what, 6)}`, { label: "Open", run: () => ("function" == typeof crOpenTask ? crOpenTask({ kind: made.kind, id: made.id, projectId: made.projectId, rec: rsTaskRec(made) }) : setView("tkall")) });
    });
  const d = m.querySelector("[data-rsdismiss]");
  d &&
    (d.onclick = () => {
      mbModal("Dismiss With a Reason", `<p class="small">${esc(f.what)}</p>${mbF("Why it is not a problem", mbIn("why", "", "e.g. the vendor credited it on the next invoice"))}`, { submit: "Dismiss", onSubmit: (v) => (rsDismiss(f.key, v.why) ? void 0 : !1) });
    });
  try {
    "function" == typeof bpPass && bpPass(m);
  } catch (e) {}
}
document.addEventListener("click", (e) => {
  const t = e.target && e.target.closest ? e.target : null;
  if (!t) return;
  const h = t.closest("[data-rshandle]");
  if (h) return e.preventDefault(), void rsSheet(h.dataset.rshandle);
  const rr = t.closest("[data-rsrole]");
  if (rr) return e.preventDefault(), (rsView = rr.dataset.rsrole), void ("function" == typeof renderPa ? renderPa() : render());
  const sv = t.closest("[data-svshare]");
  if (sv) return e.preventDefault(), void svShareSheet();
  const cr = t.closest("[data-svcredit]");
  if (cr) return e.preventDefault(), void svCredit(cr.dataset.svcredit);
  const tp = t.closest("[data-rstprop]");
  if (tp) return e.preventDefault(), void rsThresholdSheet(tp.dataset.rstprop);
});
function svCardHtml() {
  const V = svSummary(),
    own = isOwner(),
    row = (o) =>
      Object.keys(o)
        .sort((a, b) => o[b] - o[a])
        .map((k) => `<div class="rs-kv"><span>${esc(k)}</span><b>${esc(money(o[k]))}</b></div>`)
        .join("") || '<div class="small muted">None yet.</div>';
  return `<section class="card rs-card sv-card" data-svytd="${V.ytd}"><div class="hd"><h3>Savings Ledger</h3></div><div class="bd">
    <div class="rs-big"><b>${esc(money(V.ytd))}</b><span class="small muted">saved this year, ${V.nYtd} saving${1 === V.nYtd ? "" : "s"} · ${esc(money(V.month))} this month</span></div>
    <p class="small muted">Every row rests on a record: a bill held to its PO, a duplicate disputed, a discount taken, a quote negotiated down, a finding fixed. ${esc(STD_WASTE)}</p>
    <div class="rs-cols"><div><h4>By Source</h4>${row(V.bySource)}</div><div><h4>By Person</h4>${row(V.byPerson)}</div></div>
    <div class="rs-pools small">Shares: ${V.share.wage}% wages (${esc(money(V.pools.wage))}) · ${V.share.bonus}% bonuses (${esc(money(V.pools.bonus))}) · ${V.share.charity}% charity (${esc(money(V.pools.charity))})${own ? ' <button type="button" class="btn sm" data-svshare>Set the Shares</button>' : ""}</div>
    ${V.rows.length ? `<div class="rs-svrows">${V.rows.slice(0, 8).map((r) => `<div class="rs-row"><div class="rs-txt"><div>${esc(r.what)}</div><div class="small muted">${esc(money(r.amount))} · ${esc(r.source)} · ${esc(r.by || "who acted is not recorded")} · ${esc(fmtL(r.date))}${V.attr[r.key] ? ` · credited to ${esc(V.attr[r.key].person)}` : ""}</div></div>${own && !V.attr[r.key] && r.by ? `<button type="button" class="btn sm" data-svcredit="${esc(r.key)}">Credit ${esc(String(r.by).split(" ")[0])}</button>` : ""}</div>`).join("")}</div>` : ""}
  </div></section>`;
}
function svShareSheet() {
  const s = Object.assign({ wage: 0, bonus: 0, charity: 0 }, (DB.company || {}).savingsShare || {});
  mbModal("Set the Shares", `<p class="small">The part of every dollar saved that goes to each pool. ${esc(STD_WASTE)}</p><div class="grid2">${mbF("Wages %", mbIn("wage", String(s.wage), "", "number"))}${mbF("Bonuses %", mbIn("bonus", String(s.bonus), "", "number"))}</div>${mbF("Charity %", mbIn("charity", String(s.charity), "", "number"))}`, { submit: "Save the Shares", onSubmit: (f) => (svSetShare(f) ? void 0 : !1) });
}
function wlCardHtml() {
  // the owner reads everyone; a PM reads the people a PM manages (the field) and themself
  const mine = (x) => isOwner() || x.u.id === rsMe().id || "pm" === WL_MANAGER[x.group],
    R = wlRows().filter((x) => (x.open || x.overdue) && mine(x)).sort((a, b) => b.overdue - a.overdue || b.open - a.open);
  return `<section class="card rs-card wl-card"><div class="hd"><h3>Workload</h3></div><div class="bd"><p class="small muted">Open and overdue tasks per person, hours in the last 7 days and how fast they answer the field. An overloaded person shows under Overloaded People with a named person who has room; the manager approves the move.</p>${R.map((x) => `<div class="rs-kv${x.over ? " rs-over" : ""}" data-wl="${esc(x.u.id)}"><span>${esc(x.u.name)}${x.over ? ' <span class="pill warn">Overloaded</span>' : ""}</span><span class="small">${x.open} open · ${x.overdue} overdue${null != x.hours7 ? ` · ${Math.round(x.hours7)} hours this week` : ""}${null != x.resp ? ` · answers the field in ${x.resp < 1 ? Math.max(1, Math.round(x.resp * 60)) + " min" : Math.round(x.resp) + " h"}` : ""}</span></div>`).join("") || '<div class="small muted">Nobody has open tasks.</div>'}</div></section>`;
}
function rsThresholdHtml() {
  return `<section class="card rs-card rs-thr"><div class="hd"><h3>Thresholds the Checklists Enforce</h3></div><div class="bd"><p class="small muted">The Standard's numbers. Changing one drafts a change under Company › Changes; it applies when you approve it there.</p>${Object.keys(RS_T)
    .map((k) => {
      const c = standardCite(RS_T[k].cite);
      return `<div class="rs-kv"><span>${esc(RS_T[k].label)}${c ? `<br><span class="small muted">${esc(c.text)}</span>` : ""}</span><span><b>${"$" === RS_T[k].unit ? esc(money(rsT(k))) : `${rsT(k)} ${esc(RS_T[k].unit)}`}</b> <button type="button" class="btn sm" data-rstprop="${k}">Change</button></span></div>`;
    })
    .join("")}</div></section>`;
}
function rsThresholdPropose(k, v, why) {
  if (!RS_T[k]) return null;
  if (!(isFinite(+v) && +v > 0)) return toast("Enter a number above zero"), null;
  if (!String(why || "").trim()) return toast("Say why: the reason goes to the approval"), null;
  DB.changes = DB.changes || [];
  const ch = { id: uid("ch"), key: `sp:threshold:${k}:${+v}:${today()}`, kind: "rule", title: `${RS_T[k].label}: ${"$" === RS_T[k].unit ? money(rsT(k)) + " to " + money(+v) : `${rsT(k)} to ${+v} ${RS_T[k].unit}`}`, why: String(why).trim(), evidence: [{ t: (standardCite(RS_T[k].cite) || {}).text || "", m: "the Standard" }], delta: { path: `company.spThresholds.${k}`, to: +v }, status: "draft", at: today(), by: rsMe().name || role(), source: "specialist" };
  DB.changes.push(ch);
  try {
    audit("change", ch.id, "drafted", String(rsT(k)), String(+v), String(why).trim());
  } catch (e) {}
  save(), render(), toast(`Drafted for approval: ${ch.title}`, [{ label: "Open", run: () => ((mtTab = "changes"), setView("meetings")) }]);
  return ch;
}
function rsThresholdSheet(k) {
  mbModal(esc(RS_T[k].label), `${mbF(`New value (${esc(RS_T[k].unit)})`, mbIn("v", String(rsT(k)), "", "number"))}${mbF("Why", mbIn("why", "", "e.g. small orders were waiting on quotes"))}`, { submit: "Draft the Change", onSubmit: (f) => (rsThresholdPropose(k, f.v, f.why) ? void 0 : !1) });
}

// ---- 11. Ask reads it: the checklist, the savings ledger, the workload ------------------------------------------------
EQ_TABLES.checklist = () =>
  rsCanSee()
    ? rsFindings(role()).map((f) => ({ _id: f.key, _module: "Assistant", _label: f.what, _go: () => rsOpenChecklist(), role: RS_ROLE_LABEL[rsRoleOf(f.check.roles[0])], area: f.check.area, line: f.check.label, what: f.what, detail: f.sub, amount: f.amount, state: f.case ? f.case.status : "new", owner: f.case && f.case.task ? f.case.task.owner : "", due: f.case && f.case.task ? f.case.task.due : "" }))
    : [];
EQ_TABLES.savings = () => (["owner", "controller"].includes(role()) ? svRows().map((r) => ({ _id: r.key, _module: "Reports", _label: r.what, _go: () => rsOpenChecklist("owner"), source: r.source, amount: r.amount, date: r.date, person: r.by, credited: ((DB.company || {}).savingsAttr || {})[r.key] ? ((DB.company || {}).savingsAttr || {})[r.key].person : "" })) : []);
EQ_TABLES.workload = () => (["owner", "pm", "design_mgr"].includes(role()) ? wlRows().map((x) => ({ _id: x.u.id, _module: "Tasks", _label: x.u.name, _go: () => rsOpenChecklist("owner"), person: x.u.name, role: x.u.role, open: x.open, overdue: x.overdue, hours7: x.hours7, responseHours: x.resp, overloaded: x.over, moveTo: x.move ? x.move.to.name : "" })) : []);
Object.assign(EQ_ALIAS, { specialist: "checklist", checklists: "checklist", my_checklist: "checklist", saving: "savings", savings_ledger: "savings", savingsledger: "savings", workloads: "workload", capacity: "workload" });
EQ_MONEY_TABLES.includes("savings") || EQ_MONEY_TABLES.push("savings");
"undefined" != typeof MD_VIEWS && Object.assign(MD_VIEWS, { checklist: ["pa"], savings: ["reports", "gl", "ovmoney"], workload: ["tkall"] });

// ---- 12. when it runs: the app day, Fridays, the defaults the owner approved ----------------------------------------
APP_DAY_HOOKS.push(["rsDay", () => (rsFridaySweep(), rsAutoDrafts(), rsSweep(), !0)]);
