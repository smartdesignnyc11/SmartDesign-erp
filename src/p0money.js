/*<<p0money.js>>*/
// ==== Procurement P0: money first (docs/PROCUREMENT_PLAN.md §5 and §6 P0; the coordinator's buying day of 2026-10-25,
// review/procurement/coordinator_day.md findings 1, 3, 6, 7, 25 and 32). Money wasted is money that cannot go to raises,
// bonuses, staff, charity or extra value for the client. Three rules, each one function that every path reads:
//
// 1. A deposit is a prepayment on its order, applied once. A deposit bill on an order (billing marks it a deposit, or
//    its words say so) and a bank or card line paid to the vendor against the order before any bill (rule 2) are the
//    order's prepayments. When the order's bill arrives, by any path (Bill This PO, the bill drawer, the mail reader),
//    each prepayment is applied to it as a line of its own, "Less prepaid on PO-…", so the bill reads invoice, less
//    prepaid, due, and only the balance is payable. Job cost, the cash forecast, AP aging and the vendor ledger all
//    read the bill's lines, so the deposit is counted once in each: a $4,400 deposit and an $8,800 invoice leave $4,400
//    due and $8,800 of cost. An order's "billed" is what the vendor invoiced (its deposits are prepayments, not a
//    billing of the goods), and its "paid" is every payment of its bills and every bank line held by the order, each once.
//    Subcontracts keep their own rule (src/subs.js: a deposit counts toward the contract as the work is billed, and a
//    pay application that does not take it off is held by the Payment Check).
// 2. A vendor prepayment is never left uncategorised. A bank or card line paid out to a vendor who has an open order
//    and no bill behind the line is linked to that order as a prepayment (the job, cost code and line of the order),
//    and waits on the coordinator's and the controller's Today until one of them confirms it, with the vendor's papers
//    (COI, W-9) and the order shown. Not This Order puts it back for Banking to code, and it is never linked again.
// 3. One purchase-tax rule (p0PurchaseTax). The firm is the consumer of the materials it puts into a capital
//    improvement: it pays NY sales tax to the vendor, or accrues use tax when the vendor charges none. The job's
//    capital-improvement status (the client's ST-124 on file) only means the client's invoice carries no sales tax
//    (client-side tax is unchanged here). Labour, services and subcontract work carry no purchase tax (the existing
//    rule). A real exemption (resale, or an exempt organisation's project with its ST-120.1) is a person's choice on
//    the order. Every path that makes an order reads this rule (the Order sheet, Which Lines, New PO, the RFQ award,
//    a submittal release, a field request, the FF&E run, the assistant) because save() decides any order not yet
//    decided; orders issued under the old default ("Exempt — capital improvement") are repaired once at boot, each
//    with a note on the order and a review card for the controller, never silently. To be confirmed with the firm's
//    accountant: said where a person chooses the treatment (the order's Sales Tax field), nowhere else.
//
// Design gate (BACKLOG §1.16): no new store, list or queue. It extends the Order (DB.pos: taxRule, taxRepair, useTax),
// the Bill (DB.bills: deposit, its "Less prepaid" lines), the Bank Line (DB.txns: prepay), and the one Approvals queue
// (two kinds: "prepay" for the coordinator and the controller, "taxfix" for the controller).

const P0_V = 1,
  P0_TAX_LABOUR = ["subcontract", "service"],
  P0_OPEN_BILL = ["draft", "submitted", "pm-approved", "approved", "exception"],
  P0_TOL = 0.5,
  p0Me = () => ((("function" == typeof currentUser && currentUser()) || {}).name || role()),
  p0PO = (id) => (id && (DB.pos || []).find((p) => p.id === id)) || null,
  p0Live = (b) => !!b && !["void", "rejected"].includes(b.status),
  p0Sub = (po) => !!po && "subcontract" === po.type,
  p0Vend = (name) => {
    const n = String(name || "").trim().toLowerCase();
    return (n && (DB.vendors || []).find((v) => String(v.name || "").trim().toLowerCase() === n)) || null;
  },
  p0Job = (pid) => {
    const p = (DB.projects || []).find((x) => x.id === pid);
    return p ? String(p.project.name).replace(/ —.*$/, "") : "overhead";
  },
  p0M = (n) => ("function" == typeof money2 && Math.abs((+n || 0) % 1) > 0.004 ? money2(n) : money(n)),
  p0Rate = () => +((DB.company || {}).taxRate || 8.875),
  P0_STD_WHY = "Every dollar matters: no money is committed without approval, a budget line and a paper trail";

// ---------------------------------------------------------------------------------------------------- 3. purchase tax
// The statuses an order can carry. "exempt-ci" is gone: a capital improvement never exempts the firm's purchases.
(function () {
  if ("undefined" == typeof TAX_STATUS) return;
  Object.keys(TAX_STATUS).forEach((k) => delete TAX_STATUS[k]);
  Object.assign(TAX_STATUS, {
    taxable: "Taxable — the vendor charges NY sales tax",
    "use-tax": "No tax charged — use tax to accrue",
    "exempt-resale": "Exempt — resale (ST-120 on file)",
    "exempt-st120": "Exempt — exempt organization's project (ST-120.1 on file)",
    none: "No tax (labor / service)",
  });
})();
// Does the vendor charge NY sales tax? Their record says so; else a vendor out of state charges none; else they do.
function p0VendorCharges(v) {
  if (v && null != v.chargesTax) return !!v.chargesTax;
  if (v && "function" == typeof pwOutOfState && pwOutOfState(v)) return !1;
  return !0;
}
// The one rule. po: an order or anything shaped like one ({ type, vendor, projectId, lines }).
function p0PurchaseTax(po) {
  const type = (po && po.type) || "materials",
    rate = p0Rate(),
    v = p0Vend(po && po.vendor),
    vn = (v && v.name) || (po && po.vendor) || "the vendor";
  if (P0_TAX_LABOUR.includes(type)) return { status: "none", rate: 0, why: "labour and subcontract work carry no purchase tax" };
  return p0VendorCharges(v)
    ? { status: "taxable", rate: rate, why: `${vn} charges NY sales tax at ${rate}%, which the firm pays: a capital improvement exempts the client's invoice, never our purchases` }
    : { status: "use-tax", rate: rate, why: `${vn} charges no NY sales tax, so the firm accrues use tax at ${rate}%` };
}
// The status for an order being made now (the root paths call this; save() calls it for every other path).
function p0TaxStatusFor(po) {
  return p0PurchaseTax(po).status;
}
const p0TaxSig = (po) => [po.type || "materials", String(po.vendor || "").trim().toLowerCase()].join("|");
const p0Goods = (po) => r2((po.lines || []).reduce((a, l) => a + (+l.qty || 0) * (+l.price || 0), 0));
function p0UseTaxOf(po) {
  const rate = p0Rate();
  return { rate: rate, amount: r2((p0Goods(po) * rate) / 100), note: "use tax to accrue: the vendor charges no NY sales tax (confirm with the accountant)" };
}
// Put the decision on the order: its status, the vendor's tax on the order (taxable), or the use tax to accrue.
function p0TaxPut(po, status, by) {
  po.taxStatus = status;
  po.tax = "taxable" === status ? p0Rate() : 0;
  if ("use-tax" === status) {
    const keep = po.useTax && +po.useTax.amount > 0 && Math.abs(+po.useTax.amount - p0UseTaxOf(po).amount) < 0.05;
    keep || (po.useTax = p0UseTaxOf(po));
  } else po.useTax = null;
  po.taxRule = Object.assign({ v: P0_V, sig: p0TaxSig(po), by: by || "rule", at: appNowIso() }, po.taxRule && po.taxRule.chosen ? { chosen: po.taxRule.chosen } : {});
  return po;
}
// Decide an order's tax by the rule (a new order, or one whose vendor or type changed before it went out).
function p0TaxDecide(po, by) {
  if (!po) return po;
  const labour = P0_TAX_LABOUR.includes(po.type || ""),
    keep = ["exempt-resale", "exempt-st120"].includes(po.taxStatus) && !labour,
    // the path that made the order may already know what the vendor charges (an RFQ quote with or without NY
    // tax): the same rule, read from the quote instead of the vendor's record
    quoted = !labour && !keep && !po.taxRule ? (po.useTax && (!0 === po.useTax || +po.useTax.amount > 0) && !(+po.tax > 0) ? "use-tax" : +po.tax > 0 ? "taxable" : "") : "";
  return p0TaxPut(po, keep ? po.taxStatus : quoted || p0PurchaseTax(po).status, keep ? "as entered" : quoted ? "the quote" : by || "rule");
}
// The order's tax in words, for the order sheet and the order page.
function p0TaxWords(po) {
  const s = po.taxStatus || p0PurchaseTax(po).status,
    g = p0Goods(po),
    rate = p0Rate();
  return "taxable" === s
    ? `NY sales tax ${rate}%, ${p0M(r2((g * rate) / 100))}, charged by the vendor and paid by us`
    : "use-tax" === s
      ? `no tax charged by the vendor: use tax ${p0M(r2((g * rate) / 100))} (${rate}%) to accrue`
      : "exempt-resale" === s
        ? "exempt, resale (ST-120 on file)"
        : "exempt-st120" === s
          ? "exempt, an exempt organization's project (ST-120.1 on file)"
          : "no tax (labour or service)";
}
// The boot repair: an order issued under the old default, or never decided, is decided once, with a note a person
// reviews. An order that has gone out and been billed or paid keeps its total: the vendor charged no tax on it, so use
// tax is accrued. An order not yet billed takes the rule (the vendor will charge NY tax, and the order now says so).
function p0TaxRepair(po) {
  if (!po || (po.taxRule && po.taxRule.v === P0_V)) return null;
  const from = po.taxStatus || ("materials" === (po.type || "materials") ? "exempt-ci" : "none"),
    fromTotal = poTotal(po).total,
    R = p0PurchaseTax(po),
    bills = (DB.bills || []).filter((b) => b.poId === po.id && p0Live(b)),
    taxedBill = bills.some((b) => (b.lines || []).some((l) => /\btax\b/i.test(l.desc || "") && +l.amount > 0)),
    gone = bills.length || (po.matchedTxns || []).length || ["received", "closed"].includes(po.status) || (po.lines || []).some((l) => +l.received > 0);
  let to = R.status;
  if (["exempt-resale", "exempt-st120"].includes(from)) to = from;
  else if ("none" === R.status) to = "none";
  else if (taxedBill) to = "taxable";
  else if (gone) to = "use-tax";
  if (from === to && ("taxable" !== to || +po.tax > 0)) return p0TaxPut(po, to, "rule"), null;
  const keepTax = gone && "taxable" === to ? +po.tax : null;
  p0TaxPut(po, to, "boot repair");
  null != keepTax && (po.tax = keepTax);
  const toTotal = poTotal(po).total,
    fromWords = { "exempt-ci": "Exempt — capital improvement (ST-124)", taxable: "Taxable", none: "No tax (labor / service)" }[from] || from,
    why =
      "use-tax" === to
        ? `${po.vendor || "The vendor"} charged no sales tax on this order, and a capital improvement does not exempt our purchases: use tax of ${p0M((po.useTax || {}).amount || 0)} is to accrue`
        : "taxable" === to
          ? `the firm pays NY sales tax on materials: ${po.vendor || "the vendor"} will charge it, so the order now reads ${p0M(toTotal)} (was ${p0M(fromTotal)}); send the vendor the corrected order`
          : "labour carries no purchase tax";
  po.taxRepair = { from: from, fromWords: fromWords, to: to, fromTotal: fromTotal, toTotal: toTotal, on: today(), at: appNowIso(), why: why, reviewed: null };
  try {
    audit("po", po.id, "purchase-tax-repaired", fromWords, TAX_STATUS[to] || to, why);
  } catch (e) {}
  try {
    log(`Purchase tax on ${po.number || "an order"} corrected: ${fromWords} to ${TAX_STATUS[to] || to}. ${why}`, "rule", "the purchase-tax rule");
  } catch (e) {}
  return po.taxRepair;
}
// Bills carry their order's status; a bill keyed with the old default takes the rule.
function p0BillTaxSync(b) {
  if (!b || "exempt-ci" !== b.taxStatus) return;
  const po = p0PO(b.poId);
  b.taxStatus = po ? po.taxStatus || "none" : p0PurchaseTax({ type: { materials: "materials", equipment: "equipment" }[b.cat] || "service", vendor: b.vendor }).status;
}
// applyTax (the order page's own setter) keeps the use tax with the status
if ("function" == typeof applyTax) {
  const base = applyTax;
  applyTax = function (po) {
    const r = base.apply(this, arguments);
    try {
      po && ("use-tax" === po.taxStatus ? (po.useTax = p0UseTaxOf(po)) : po.taxStatus && "use-tax" !== po.taxStatus && po.useTax && po.origin !== "rfq" && (po.useTax = null));
    } catch (e) {}
    return r;
  };
}

// ------------------------------------------------------------------------------------- 1. deposits and prepayments
// A deposit bill on an order: marked by billing, or its words say "deposit" (and not "less", "balance", "final"...).
function p0IsDeposit(b) {
  if (!b) return !1;
  if (!0 === b.deposit) return !0;
  if (!1 === b.deposit) return !1;
  if ((b.lines || []).some((l) => l.prepayOf || /^bl_p0_/.test(l.id || ""))) return !1;
  const t = [b.notes || "", ...(b.lines || []).map((l) => l.desc || "")].join(" ");
  return /\bdeposit\b/i.test(t) && !/\b(less|balance|final|remaining|minus|applied|after)\b/i.test(t);
}
const p0IsAppLine = (l) => !!l && (!!l.prepayOf || /^bl_p0_/.test(l.id || ""));
// What the vendor invoiced on a bill: its lines without the prepayments taken off it.
const p0Invoice = (b) => r2((b.lines || []).filter((l) => !p0IsAppLine(l)).reduce((a, l) => a + (+l.amount || 0), 0));
const p0AppliedOn = (b) => r2(-(b.lines || []).filter(p0IsAppLine).reduce((a, l) => a + (+l.amount || 0), 0));
// A bill that takes prepayments: on a non-subcontract order, not itself a deposit, not a retainage release or a
// pay application, with something invoiced.
function p0Taker(b, po) {
  return !!b && !!po && b.poId === po.id && p0Live(b) && !p0Sub(po) && !p0IsDeposit(b) && !b.retainageRelease && !b.payApp && !b.ic && p0Invoice(b) > 0.005;
}
// The order's prepayments, oldest first: its deposit bills and the bank or card lines linked to it as prepayments.
function p0Sources(po) {
  if (!po || p0Sub(po)) return [];
  const out = [];
  (DB.bills || [])
    .filter((b) => b.poId === po.id && p0Live(b) && "draft" !== b.status && !b.retainageRelease && p0IsDeposit(b) && billGross(b) > 0.005)
    .forEach((b) => out.push({ key: "bill:" + b.id, kind: "deposit", ref: b, date: b.date || "", amount: r2(billGross(b)), label: `deposit ${b.number || "bill"}` }));
  (DB.txns || [])
    .filter((t) => t.prepay && t.prepay.poId === po.id && (t.poId === po.id || (po.matchedTxns || []).includes(t.id)) && +t.amt < 0 && !t.billId && "void" !== t.status && !t.voided)
    .forEach((t) => {
      const a = (DB.accounts || []).find((x) => x.id === t.acct);
      out.push({ key: "txn:" + t.id, kind: "txn", ref: t, date: t.date || "", amount: r2(-t.amt), label: `${a && "card" === a.type ? "card charge" : "bank payment"} of ${fmt(t.date)}` });
    });
  return out.sort((a, b) => String(a.date).localeCompare(String(b.date)) || a.key.localeCompare(b.key));
}
// How the order's prepayments land on its bills: bills already paid keep what they took; open bills take the rest,
// oldest first, never more than they invoice. Returns the wanted lines per open bill and what is left unapplied.
function p0Allocate(po) {
  const S = p0Sources(po),
    left = Object.fromEntries(S.map((s) => [s.key, s.amount])),
    bills = (DB.bills || []).filter((b) => p0Taker(b, po)).sort((a, b) => String(a.date || "").localeCompare(String(b.date || "")) || String(a.createdAt || "").localeCompare(String(b.createdAt || "")) || String(a.id).localeCompare(String(b.id))),
    frozen = bills.filter((b) => !P0_OPEN_BILL.includes(b.status)),
    open = bills.filter((b) => P0_OPEN_BILL.includes(b.status)),
    want = {};
  frozen.forEach((b) => (b.lines || []).filter(p0IsAppLine).forEach((l) => l.prepayOf && null != left[l.prepayOf] && (left[l.prepayOf] = r2(left[l.prepayOf] + (+l.amount || 0)))));
  open.forEach((b) => {
    let room = p0Invoice(b);
    want[b.id] = [];
    S.forEach((s) => {
      const x = r2(Math.min(Math.max(0, left[s.key]), room));
      x > 0.005 && (want[b.id].push({ s: s, amount: x }), (left[s.key] = r2(left[s.key] - x)), (room = r2(room - x)));
    });
  });
  return { sources: S, bills: bills, open: open, want: want, left: left, unapplied: r2(Object.values(left).reduce((a, x) => a + Math.max(0, x), 0)) };
}
// Make each open bill's "Less prepaid" lines match the allocation. Returns the bills whose lines moved.
function p0ApplyPO(po) {
  if (!po || p0Sub(po)) return [];
  const A = p0Allocate(po),
    moved = [];
  // a source that is gone (a deposit bill voided) comes off the open bills that took it
  A.open.forEach((b) => {
    const W = A.want[b.id] || [],
      ids = W.map((w) => "bl_p0_" + w.s.key.replace(/[^a-z0-9]/gi, "")),
      before = JSON.stringify((b.lines || []).filter(p0IsAppLine).map((l) => [l.id, l.amount])),
      code = (b.lines || []).find((l) => !p0IsAppLine(l) && l.code)?.code || b.code || ((po.lines || [])[0] || {}).code || "",
      line = (b.lines || []).find((l) => !p0IsAppLine(l) && l.line)?.line || b.line || ((po.lines || [])[0] || {}).line || "";
    b.lines = (b.lines || []).filter((l) => !p0IsAppLine(l) || ids.includes(l.id));
    W.forEach((w, i) => {
      const id = ids[i],
        desc = `Less prepaid on ${po.number}: ${w.s.label}${"txn" === w.s.kind ? "" : `, ${fmt(w.s.date)}`}`;
      let l = b.lines.find((x) => x.id === id);
      l || ((l = { id: id }), b.lines.push(l));
      Object.assign(l, { desc: desc, qty: 1, unit: "ls", amount: -w.amount, code: code, line: line, prepayOf: w.s.key, p0: 1 });
    });
    const after = JSON.stringify((b.lines || []).filter(p0IsAppLine).map((l) => [l.id, l.amount]));
    if (before !== after) {
      moved.push({ b: b, po: po, applied: p0AppliedOn(b) });
      try {
        audit("bill", b.id, "prepayment-applied", before, after, `${po.number}: ${p0M(p0AppliedOn(b))} prepaid comes off ${b.number || "this bill"}`);
      } catch (e) {}
    }
  });
  return moved;
}
// Every order with a prepayment, or a bill that took one, is brought up to date (save() calls this).
let p0Moved = [];
function p0ApplyAll() {
  const ids = new Set();
  (DB.bills || []).forEach((b) => b.poId && (p0IsDeposit(b) || (b.lines || []).some(p0IsAppLine)) && ids.add(b.poId));
  (DB.txns || []).forEach((t) => t.prepay && t.prepay.poId && ids.add(t.prepay.poId));
  const out = [];
  ids.forEach((id) => {
    const po = p0PO(id);
    po && out.push(...p0ApplyPO(po));
  });
  return out;
}
// The order's prepayments in one reading: what was paid ahead, what is applied, what still comes off the next bill.
function p0Prepaid(po) {
  const A = p0Allocate(po),
    total = r2(A.sources.reduce((a, s) => a + s.amount, 0));
  return { sources: A.sources, total: total, applied: r2(total - A.unapplied), unapplied: A.unapplied, txn: r2(A.sources.filter((s) => "txn" === s.kind).reduce((a, s) => a + s.amount, 0)) };
}
// Bank and card prepayments applied on the order's bills (they are not bills themselves, so a PO-total check adds them)
const p0TxnApplied = (po) =>
  r2((DB.bills || []).filter((b) => b.poId === po.id && p0Live(b)).reduce((a, b) => a - (b.lines || []).filter((l) => /^txn:/.test(l.prepayOf || "")).reduce((s, l) => s + (+l.amount || 0), 0), 0));

// Money paid ahead is cost on the job (it left the bank for the job's line) but never progress: until the goods come
// and the bill takes it, it earns no revenue on the cost-to-cost % complete (the line's % already leaves deposits out).
// Without this, the $8,000 to Tino for flooring due 10/5 earned 121 State $10,105 of revenue on 9/3.
function p0JobPrepaid(p, R) {
  let s = 0;
  (DB.pos || [])
    .filter((po) => po.projectId === p.id && !p0Sub(po) && !["cancelled", "draft"].includes(po.status))
    .forEach((po) => {
      const A = p0Allocate(po);
      A.sources.forEach((x) => (!R || "function" != typeof within || within(x.date, R)) && (s += Math.max(0, A.left[x.key] || 0)));
    });
  return r2(s);
}
if ("function" == typeof jobFin && "function" == typeof jobFinDerive) {
  const base = jobFin;
  jobFin = function (p, range) {
    const J = base.apply(this, arguments);
    try {
      const pre = J && p ? p0JobPrepaid(p, range || ["", today()]) : 0;
      if (pre > 0.005 && "number" == typeof J.actual) {
        const a = J.actual;
        J.actual = r2(a - Math.min(pre, a));
        jobFinDerive(J, p, J.eac);
        J.actual = a;
      }
      J && (J.prepaidNotProgress = pre);
    } catch (e) {
      console.warn("p0 job prepaid", e);
    }
    return J;
  };
}
// the line's own % complete reads deposits apart (jobFinEacLines); a bank prepayment on the line is one too
if ("function" == typeof jobFinEacLines) {
  const base = jobFinEacLines;
  jobFinEacLines = function (J, p) {
    const L = base.apply(this, arguments);
    try {
      if (!Array.isArray(L) || !L.length || !p) return L;
      const by = Object.fromEntries(L.map((x) => [x.key, x]));
      (DB.pos || [])
        .filter((po) => po.projectId === p.id && !p0Sub(po) && !["cancelled", "draft"].includes(po.status))
        .forEach((po) => {
          const A = p0Allocate(po);
          A.sources.forEach((s) => {
            const left = Math.max(0, A.left[s.key] || 0),
              x = "txn" === s.kind && left > 0.005 && by[s.ref.line];
            x && (x.deposit = r2(Math.min(x.actual, (x.deposit || 0) + left)));
          });
        });
    } catch (e) {
      console.warn("p0 line prepaid", e);
    }
    return L;
  };
}
// One "paid" for an order: every payment of its bills, by any method, and every bank or card line the order holds
// that no bill or payment holds, each once. The Vendors page reads it too (scVendorPaid below).
function p0PoPaid(po) {
  if (!po) return 0;
  const bills = (DB.bills || []).filter((b) => b.poId === po.id && p0Live(b) && "draft" !== b.status),
    held = new Set((DB.payments || []).filter((p) => !p.void).map((p) => p.txnId).filter(Boolean)),
    paidBills = r2(bills.reduce((a, b) => a + ("function" == typeof scPaidBill ? scPaidBill(b) : 0), 0)),
    direct = r2(
      (DB.txns || [])
        .filter((t) => +t.amt < 0 && !t.billId && !held.has(t.id) && "void" !== t.status && !t.voided && (t.poId === po.id || (po.matchedTxns || []).includes(t.id)))
        .reduce((a, t) => a - +t.amt, 0),
    );
  return r2(paidBills + direct);
}
{
  const base = poPaid;
  poPaid = function (po) {
    try {
      return p0PoPaid(po);
    } catch (e) {
      return base.apply(this, arguments);
    }
  };
}
// An order's "billed": what the vendor invoiced for the goods. A deposit bill is a prepayment, not a billing of the
// goods (Bill This PO after a deposit bills the whole order, and the deposit comes off it). Subcontracts keep theirs.
{
  const base = poBilled;
  poBilled = function (po) {
    try {
      if (!po || p0Sub(po)) return base.apply(this, arguments);
      return r2((DB.bills || []).filter((b) => b.poId === po.id && p0Live(b) && !p0IsDeposit(b)).reduce((a, b) => a + (b.retainageRelease ? 0 : p0Invoice(b)), 0));
    } catch (e) {
      return base.apply(this, arguments);
    }
  };
}
// A bank prepayment taken off a bill is its own cost (the bill's net leaves it out), never that bill's payment.
if ("function" == typeof txnViaBill) {
  const base = txnViaBill;
  txnViaBill = function (t) {
    try {
      if (t && t.prepay && (DB.bills || []).some((b) => p0Live(b) && (b.lines || []).some((l) => l.prepayOf === "txn:" + t.id))) return !1;
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
// The over-the-PO checks count a bank prepayment applied on a bill as billed (it is part of the vendor's invoice).
if ("function" == typeof pay3PO) {
  const base = pay3PO;
  pay3PO = function (b) {
    const P = base.apply(this, arguments);
    try {
      if (P && P.po && !p0Sub(P.po)) {
        const t = p0TxnApplied(P.po);
        t > 0.005 && (P.left = r2(Math.max(0, P.left - t)));
      }
    } catch (e) {}
    return P;
  };
}
// The vendor ledger: paid is the orders' one "paid" plus their bills off any order; billed is what they invoiced.
if ("function" == typeof scLedger) {
  const base = scLedger;
  scLedger = function (vname, pid) {
    const L = base.apply(this, arguments);
    try {
      const mine = new Set((L.pos || []).map((p) => p.id)),
        off = (L.bills || []).filter((b) => !mine.has(b.poId) && billTotal(b) > 0),
        paid = r2((L.pos || []).reduce((a, po) => a + p0PoPaid(po), 0) + off.reduce((a, b) => a + scPaidBill(b), 0)),
        txn = r2((L.pos || []).filter((po) => !p0Sub(po)).reduce((a, po) => a + p0TxnApplied(po), 0)),
        pre = (L.pos || []).filter((po) => !p0Sub(po)).map(p0Prepaid);
      L.paid = paid;
      L.billed = r2(L.billed + txn);
      L.prepaidOpen = r2(pre.reduce((a, x) => a + x.unapplied, 0));
      L.deposits = r2((L.deposits || 0) + pre.reduce((a, x) => a + x.total, 0) - (L.bills || []).filter((b) => mine.has(b.poId) && !p0Sub(p0PO(b.poId)) && p0IsDeposit(b)).reduce((a, b) => a + billGross(b), 0));
      L.pos.length && ((L.left = r2(L.contract - L.paid)), (L.balanceToFinish = r2(L.contract - L.billed)));
    } catch (e) {
      console.warn("p0 ledger", e);
    }
    return L;
  };
}
// The Vendors page's "paid to date" reads the same: the ledger's paid plus bank lines to the vendor that no bill,
// payment or order holds.
if ("function" == typeof scVendorPaid) {
  scVendorPaid = function (v) {
    if (!v || !v.name) return 0;
    const L = scLedger(v.name, ""),
      n = scLow(v.name),
      held = new Set((DB.payments || []).map((p) => p.txnId).filter(Boolean));
    (DB.pos || []).forEach((po) => (po.matchedTxns || []).forEach((id) => held.add(id)));
    const loose = (DB.txns || []).filter((t) => +t.amt < 0 && !t.billId && !t.poId && !held.has(t.id) && !["transfer", "cc-payment"].includes(t.cat) && (scLow(t.vendor) === n || scLow(t.desc).replace(/[^a-z0-9 ]/g, " ").includes(n.replace(/[^a-z0-9 ]/g, " "))));
    return r2(L.paid + loose.reduce((a, t) => a - +t.amt, 0));
  };
}

// --------------------------------------------------------------------------------- 2. bank and card prepayments
// An outgoing bank or card line to a vendor with an open order and no bill behind it is a prepayment on that order.
const P0_PRE_CATS = ["", "uncat", "materials", "equipment", "subs", "other"],
  P0_NAME_SKIP = /^(the|and|of|inc|llc|co|corp|company|ltd|nyc|ny)$/;
// The line names the vendor: its vendor field is theirs, or its words hold every word of their name (a word may be
// cut short on the statement, "FAB" for fabrication). One shared word is not enough: "CHIPOTLE 1122 ATLANTIC AVE" is
// not Atlantic Stone Fab.
function p0PaidTo(t, vname) {
  const vn = String(vname || "").trim().toLowerCase();
  if (!vn) return !1;
  if (String(t.vendor || "").trim().toLowerCase() === vn) return !0;
  const words = String(`${t.vendor || ""} ${t.desc || ""}`).toLowerCase().replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter(Boolean),
    need = vn.replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter((w) => w.length > 1 && !P0_NAME_SKIP.test(w));
  return !!need.length && need.every((w) => words.some((x) => x === w || (w.length >= 3 && x.startsWith(w)) || (x.length >= 3 && w.startsWith(x) && x.length >= w.length - 3)));
}
function p0PrepayCandidates(t) {
  if (!t || !(+t.amt < 0) || t.billId || t.poId || t.prepay || t.prepayNo || "void" === t.status || t.voided || !P0_PRE_CATS.includes(t.cat || "")) return [];
  if ((DB.pos || []).some((po) => (po.matchedTxns || []).includes(t.id)) || (DB.payments || []).some((p) => p.txnId === t.id)) return [];
  if (t.proposal && !t.proposal.rejected && !t.proposal.declined) return [];
  // a line the bank or the card company sent goes to Banking, where the import proposes its match and a person
  // confirms it (a confirmed match to an order nothing has arrived on is a prepayment: truthSetMatch below); this
  // rule takes the lines no import will propose, typed from a receipt
  if (t.extId || t.origin || t.importId || (t.prov && /feed|statement|plaid/i.test(t.prov.kind || "")) || ("function" == typeof bfBacked && bfBacked(t))) return [];
  const amt = r2(-t.amt),
    tol = ((DB.company || {}).matchTol || 2) / 100;
  return (DB.pos || []).filter((po) => {
    if (!["issued", "partial", "pending"].includes(po.status) || p0Sub(po)) return !1;
    if (!p0PaidTo(t, po.vendor)) return !1;
    if (t.projectId && po.projectId && t.projectId !== po.projectId) return !1;
    if (po.date && t.date && t.date < iso(addDays(po.date, -3))) return !1;
    // a bill on the order the line could be paying is a bill payment, not a prepayment
    if ((DB.bills || []).some((b) => b.poId === po.id && p0Live(b) && !p0IsDeposit(b) && Math.abs(billTotal(b) - amt) < 1)) return !1;
    const open = r2(poTotal(po).total - poBilled(po) - p0Prepaid(po).total);
    return amt <= open * (1 + tol) + 1;
  });
}
function p0PrepayLink(t, po, by) {
  const l1 = (po.lines || [])[0] || {};
  t.poId = po.id;
  t.projectId = t.projectId || po.projectId || "";
  ["", "uncat", "other"].includes(t.cat || "") && (t.cat = "function" == typeof poCat ? poCat(po) : "materials");
  t.code = t.code || l1.code || "";
  t.line = t.line || (1 === (po.lines || []).length ? l1.line || "" : "");
  t.status = "categorized";
  t.actor = t.actor || "rule";
  t.noPO = !1;
  t.prepay = { poId: po.id, by: by || "rule", at: appNowIso(), confirmed: null };
  try {
    audit("txn", t.id, "vendor-prepayment-linked", "", po.number, `${p0M(-t.amt)} to ${po.vendor} before any bill or delivery`);
  } catch (e) {}
  return t;
}
// Link every line that has exactly one open order it can belong to; a line with two or more is asked about.
function p0PrepayScan() {
  const linked = [];
  (DB.txns || []).forEach((t) => {
    const C = p0PrepayCandidates(t);
    if (1 === C.length) p0PrepayLink(t, C[0], "rule"), linked.push(t);
    else if (C.length > 1) t.prepayAsk = C.map((po) => po.id);
    else t.prepayAsk && delete t.prepayAsk;
  });
  return linked;
}
// The prepayments a person has not confirmed yet, and lines that could belong to more than one order.
function p0PrepayOpen() {
  return (DB.txns || []).filter((t) => (t.prepay && !t.prepay.confirmed && t.poId === t.prepay.poId && !t.billId) || (t.prepayAsk && t.prepayAsk.length && !t.poId));
}
function p0Papers(vname) {
  const v = p0Vend(vname),
    td = today();
  return {
    v: v,
    coi: v && v.insuranceExp ? (v.insuranceExp < td ? { ok: !1, text: `COI expired ${fmt(v.insuranceExp)}` } : { ok: !0, text: `COI through ${fmt(v.insuranceExp)}` }) : { ok: !1, text: "No COI on file" },
    w9: v && v.w9 ? { ok: !0, text: "W-9 on file" } : { ok: !1, text: "No W-9 on file" },
  };
}
function p0PrepayWords(t) {
  const po = p0PO(t.poId || (t.prepayAsk || [])[0]),
    a = (DB.accounts || []).find((x) => x.id === t.acct),
    P = po ? p0Papers(po.vendor) : null,
    recvd = po && (po.lines || []).some((l) => +l.received > 0),
    billed = po ? poBilled(po) : 0;
  return {
    po: po,
    acct: a,
    papers: P,
    head: `${p0M(-t.amt)} to ${po ? po.vendor : t.vendor || t.desc} on ${fmt(t.date)}`,
    line: po
      ? `${a ? a.name + (a.last4 || a.mask ? " ····" + (a.last4 || a.mask) : "") : "bank"} · ${po.number} ${(po.lines[0] || {}).item || ""}, ${p0Job(po.projectId)}${po.expected ? `, due ${fmt(po.expected)}` : ""} · ${recvd ? "part received" : "nothing received"}${billed ? `, ${p0M(billed)} billed` : ", no bill yet"}`
      : "",
  };
}
// The sheet a person confirms a prepayment on: the line, the order, the job, the vendor's papers, what happens next.
function p0PrepaySheet(tid) {
  const t = (DB.txns || []).find((x) => x.id === tid);
  if (!t) return toast("That bank line is no longer on file");
  const ask = !t.poId && (t.prepayAsk || []).map(p0PO).filter(Boolean),
    W = p0PrepayWords(t),
    po = W.po,
    P = W.papers,
    pill2 = (x) => `<span class="pill ${x.ok ? "ok" : "bad"}">${esc(x.text)}</span>`;
  const m = mbModal(
    "Vendor Prepayment",
    `<p class="small muted" style="margin:0 0 10px">Money that left before any bill or delivery is a prepayment on the order. It is linked to the order's job and line, counted once, and taken off the vendor's bill when it comes, so only the rest is paid.</p>
    <div class="card" style="margin:0 0 10px"><div><b>${esc(W.head)}</b></div><div class="small muted">${esc(t.desc || "")}${W.acct ? ` · ${esc(W.acct.name)}` : ""}</div></div>
    ${ask && ask.length ? mbF("Which Order", `<select data-f="po">${ask.map((x) => `<option value="${esc(x.id)}">${esc(x.number)} · ${esc(x.vendor)} · ${p0M(poTotal(x).total)} · ${esc(p0Job(x.projectId))}</option>`).join("")}</select>`) : po ? `<div class="kv small" style="margin:0 0 10px"><span>Order</span><span><b>${esc(po.number)}</b> · ${esc(po.vendor)} · ${p0M(poTotal(po).total)} ordered${po.expected ? ` · due ${fmt(po.expected)}` : ""}</span><span>Job</span><span>${esc(p0Job(po.projectId))}${t.code ? ` · cost code ${esc(t.code)}` : ""}</span><span>Bill</span><span>${poBilled(po) ? p0M(poBilled(po)) + " billed" : "none yet"}</span></div>` : ""}
    ${P ? `<div class="row" style="gap:6px;flex-wrap:wrap;margin:0 0 10px">${pill2(P.coi)}${pill2(P.w9)}</div>${!P.coi.ok || !P.w9.ok ? `<p class="small" style="margin:0 0 10px">Ask ${esc(po.vendor)} for ${[!P.coi.ok ? "the COI" : "", !P.w9.ok ? "the W-9" : ""].filter(Boolean).join(" and ")} before the next payment: the Payment Check holds the bill until they are in.</p>` : ""}` : ""}
    <p class="small muted" style="margin:0">${esc(P0_STD_WHY)}. ${esc(typeof STD_WASTE == "string" ? STD_WASTE : "")}</p>`,
    {
      submit: "Confirm Prepayment",
      alt: { label: "Not This Order", run: () => p0PrepayUnlink(t.id) },
      onSubmit: (f) => {
        if (!t.poId) {
          const x = p0PO(f.po);
          if (!x) return toast("Choose the order this payment is for"), !1;
          p0PrepayLink(t, x, p0Me()), delete t.prepayAsk;
        }
        t.prepay.confirmed = { by: p0Me(), at: appNowIso() };
        const o = p0PO(t.poId);
        try {
          audit("txn", t.id, "vendor-prepayment-confirmed", "", o ? o.number : "", p0Me());
        } catch (e) {}
        save(), render();
        rcToast(`${p0M(-t.amt)} to ${o ? o.vendor : "the vendor"} confirmed as a prepayment on ${o ? o.number : "the order"}: it comes off the bill when it arrives`, o ? [{ label: "Open", run: flowGo.po(o) }] : null);
      },
    },
  );
  return m;
}
function p0PrepayUnlink(tid) {
  const t = (DB.txns || []).find((x) => x.id === tid);
  if (!t) return;
  const po = p0PO(t.poId);
  t.prepayNo = { by: p0Me(), at: appNowIso(), poId: t.poId || "" };
  if (t.prepay && "rule" === t.prepay.by && t.poId) Object.assign(t, { poId: "", projectId: "", cat: "uncat", code: "", line: "", status: "new", actor: "" });
  t.prepay = null;
  delete t.prepayAsk;
  try {
    audit("txn", t.id, "vendor-prepayment-declined", po ? po.number : "", "", p0Me());
  } catch (e) {}
  save(), render();
  rcToast(`${p0M(-t.amt)} ${t.desc || ""} is not a prepayment on ${po ? po.number : "an order"}: it waits in Banking to be coded`, (ROLE_VIEWS[role()] || []).includes("banking") ? [{ label: "Open", run: () => setView("banking") }] : null);
}

// A person matching a bank line to an order nothing has arrived on, with no bill on it, records a prepayment: the
// order's next bill takes it off (Banking's Confirm, the Match sheet, any path through truthSetMatch).
if ("function" == typeof truthSetMatch) {
  const base = truthSetMatch;
  truthSetMatch = function (t, m0) {
    const r = base.apply(this, arguments);
    try {
      const po = r && r.ok !== !1 && m0 && m0.poId && !m0.billId ? p0PO(m0.poId) : null;
      if (po && t && !t.billId && !t.prepay && +t.amt < 0 && !p0Sub(po) && !(po.lines || []).some((l) => +l.received > 0) && !["received", "closed"].includes(po.status) && !(DB.bills || []).some((b) => b.poId === po.id && p0Live(b) && !p0IsDeposit(b))) {
        const by = p0Me();
        t.prepay = { poId: po.id, by: by, at: appNowIso(), confirmed: { by: by, at: appNowIso() } };
        try {
          audit("txn", t.id, "vendor-prepayment-matched", "", po.number, `${p0M(-t.amt)} to ${po.vendor} before delivery: it comes off the next bill`);
        } catch (e) {}
      }
    } catch (e) {
      console.warn("p0 match prepayment", e);
    }
    return r;
  };
}
// A line typed by hand with no bank line behind it says so wherever it is coded, a seeded or imported-by-hand one too.
if ("function" == typeof lkTxnMoreFlags) {
  const base = lkTxnMoreFlags;
  lkTxnMoreFlags = function (t) {
    const h = base.apply(this, arguments);
    try {
      if (!h && t && "manual" !== t.source && t.prov && "manual" === t.prov.kind && "function" == typeof bfBacked && !bfBacked(t) && !t.exception)
        return `<span class="sub warn-t lk-flag">No bank line behind it: typed by hand${t.prov.by ? " by " + esc(t.prov.by) : ""}, never seen at ${esc(truthAcctWords(t))} <button type="button" class="btn sm" data-lknobank="${esc(t.id)}">Match to a Line…</button></span>`;
    } catch (e) {}
    return h;
  };
}
// --------------------------------------------------------------------------------- the sweep, the boot repair
let p0Sweeping = !1;
function p0Sweep() {
  if (p0Sweeping || "undefined" == typeof DB || !DB || !DB.pos) return;
  p0Sweeping = !0;
  try {
    // tax: decide every order not yet decided; re-decide an unsent order whose vendor or type changed
    DB.pos.forEach((po) => {
      const R = po.taxRule;
      if (!R || R.v !== P0_V) {
        if (DB.company && DB.company.p0TaxRepairAt) p0TaxDecide(po, "rule");
      } else if (!R.chosen && R.sig !== p0TaxSig(po) && ["draft", "pending"].includes(po.status)) p0TaxDecide(po, "rule");
    });
    (DB.bills || []).forEach(p0BillTaxSync);
    p0PrepayScan();
    const moved = p0ApplyAll();
    moved.length && (p0Moved = p0Moved.concat(moved));
  } finally {
    p0Sweeping = !1;
  }
  // the person who saved the bill is told what came off it
  if (p0Moved.length) {
    const x = p0Moved[p0Moved.length - 1];
    p0Moved = [];
    setTimeout(() => {
      try {
        x.applied > 0.005 && rcToast(`${p0M(x.applied)} prepaid on ${x.po.number} comes off ${x.b.vendor} ${x.b.number || "bill"}: ${p0M(p0Invoice(x.b))} invoiced, ${p0M(billTotal(x.b))} due`, [{ label: "Open", run: flowGo.bill(x.b) }]);
      } catch (e) {}
    }, 0);
  }
}
{
  const base = save;
  save = function () {
    try {
      p0Sweep();
    } catch (e) {
      console.warn("p0 sweep", e);
    }
    return base.apply(this, arguments);
  };
}
// Once per data set: the orders issued under the old tax default are repaired with a note, then the sweep runs.
function p0BootRepair() {
  if (!DB || !DB.pos) return;
  DB.company = DB.company || {};
  if (!DB.company.p0TaxRepairAt) {
    const fixed = [];
    DB.pos.forEach((po) => {
      if (po.taxRule && po.taxRule.v === P0_V) return;
      // an order not yet sent is decided as if made now; one the vendor has is repaired, with its note
      ["draft", "pending"].includes(po.status) ? p0TaxDecide(po, "rule") : p0TaxRepair(po) && fixed.push(po.id);
    });
    DB.company.p0TaxRepairAt = appNowIso();
    DB.company.p0TaxRepaired = fixed;
  }
  p0Sweep();
}
if ("function" == typeof finishBoot) {
  const base = finishBoot;
  finishBoot = function () {
    const r = base.apply(this, arguments);
    try {
      p0BootRepair();
    } catch (e) {
      console.warn("p0 boot repair", e);
    }
    return r;
  };
}

// --------------------------------------------------------------------------------- the gates on a bill
// Approve and pay read the bill with its prepayments applied first; a bill that could still take one never goes out
// at the full amount.
function p0Gate(b) {
  const po = b && p0PO(b.poId);
  if (!po || !p0Taker(b, po)) return "";
  p0ApplyPO(po);
  const A = p0Allocate(po);
  return A.unapplied > P0_TOL && billTotal(b) > P0_TOL && P0_OPEN_BILL.includes(b.status)
    ? `${po.number} has ${p0M(A.unapplied)} prepaid that is not taken off ${b.number || "this bill"} yet: it comes off first, so only the rest is paid`
    : "";
}
if ("function" == typeof billAction) {
  const base = billAction;
  billAction = function (b, a) {
    try {
      if (b && ["approve", "approvebilled", "pmok", "pm-approve", "paid", "pay", "submit"].includes(a)) {
        const g = p0Gate(b);
        if (g) return void toast(g);
      }
    } catch (e) {
      console.warn("p0 gate", e);
    }
    return base.apply(this, arguments);
  };
}
// The owner's over-the-PO sheet never offers Approve as Billed while a prepayment on the order is not taken off.
if ("function" == typeof pay3ShortPay) {
  const base = pay3ShortPay;
  pay3ShortPay = function (b, amt, why, opts) {
    try {
      const po = b && p0PO(b.poId);
      if (po && !p0Sub(po)) {
        p0ApplyPO(po);
        if (opts && opts.billed && p0Allocate(po).unapplied > P0_TOL) opts = Object.assign({}, opts, { billed: null });
      }
    } catch (e) {}
    return base.call(this, b, amt, why, opts);
  };
}
// Controls on the bill: a deposit the order's terms allow is not "nothing received"; a final bill is not a duplicate
// of the deposit it takes; the order total counts a bank prepayment it takes.
function p0DepositRoom(po, b) {
  const tot = poTotal(po).total,
    pct = +po.depositPct || ((po.schedule || []).find((s) => "on order" === s.trigger) || {}).pct || 0,
    before = r2((DB.bills || []).filter((x) => x.poId === po.id && x.id !== b.id && p0Live(x) && p0IsDeposit(x)).reduce((a, x) => a + billGross(x), 0) + p0Prepaid(po).txn);
  return { pct: +pct || 0, allowed: r2((tot * (+pct || 0)) / 100), before: before, tot: tot };
}
const p0SameMoney = (b, other) => !!other && ((b.lines || []).some((l) => l.prepayOf === "bill:" + other.id) || (other.lines || []).some((l) => l.prepayOf === "bill:" + b.id));
if ("function" == typeof billFlags) {
  const base = billFlags;
  billFlags = function (b) {
    let f = base.apply(this, arguments);
    try {
      const po = b && p0PO(b.poId);
      if (!po || p0Sub(po) || !Array.isArray(f)) return f;
      f = f.filter((x) => {
        const m = /^Possible duplicate of (.+?) \(/.exec(String(x));
        if (!m) return !0;
        const other = (DB.bills || []).find((y) => y.id !== b.id && y.poId === po.id && (y.number || "bill " + fmt(y.date)) === m[1]);
        return !p0SameMoney(b, other);
      });
      if (p0IsDeposit(b)) {
        const R = p0DepositRoom(po, b),
          amt = billGross(b);
        f = f.filter((x) => !/shows nothing received yet|^Bills against .* vs PO |^Round-dollar amount/.test(String(x)));
        !R.pct
          ? f.push(`A deposit on ${po.number}, whose terms ask for none: set the order's payment terms first`)
          : R.before + amt > R.allowed + 1 && f.push(`Deposit ${p0M(R.before + amt)} is more than the ${R.pct}% (${p0M(R.allowed)}) ${po.number}'s terms allow`);
      } else {
        const t = p0TxnApplied(po);
        if (t > 0.005) {
          const others = r2((DB.bills || []).filter((x) => x.poId === po.id && x.id !== b.id && p0Live(x)).reduce((a, x) => a + billTotal(x), 0)),
            pt = poTotal(po).total,
            all = r2(billTotal(b) + others + t);
          f = f.filter((x) => !/^Bills against .* vs PO /.test(String(x)));
          all > pt * (1 + ((DB.company.ap || {}).tol || 2) / 100) + 1 && f.push(`Bills against ${po.number} total ${p0M(all)} with the ${p0M(t)} paid ahead, vs PO ${p0M(pt)}`);
        }
      }
    } catch (e) {
      console.warn("p0 bill flags", e);
    }
    return f;
  };
}
// The Payment Check: a deposit the terms allow is paid before delivery by design; a final bill is not a duplicate of
// its deposit; a bank prepayment counts in what the order has been billed.
if ("function" == typeof pcCheck) {
  const base = pcCheck;
  pcCheck = function (b, o) {
    const R = base.apply(this, arguments);
    try {
      const po = b && p0PO(b.poId);
      if (!R || !po || p0Sub(po)) return R;
      const drop = (key, test) => {
        const i = R.holds.findIndex((h) => h.key === key && (!test || test(h)));
        return i >= 0 ? R.holds.splice(i, 1)[0] : null;
      };
      if (p0IsDeposit(b)) {
        const D = p0DepositRoom(po, b);
        D.pct && D.before + billGross(b) <= D.allowed + 1 && drop("threeway") && R.ok.push({ key: "threeway", text: `A deposit ${po.number}'s terms allow (${D.pct}% on order): a prepayment, taken off the vendor's bill when it comes` });
      }
      drop("dup", (h) => p0SameMoney(b, (DB.bills || []).find((x) => x.id === h.other))) && R.ok.push({ key: "dup", text: "The deposit this bill takes is the same money, not a duplicate" });
      const t = p0TxnApplied(po);
      if (t > 0.005 && !R.holds.some((h) => "contract" === h.key)) {
        const C = poTotal(po).total,
          billed = r2((DB.bills || []).filter((x) => x.poId === po.id && p0Live(x)).reduce((a, x) => a + billGross(x), 0) + t);
        billed > C + P0_TOL &&
          R.holds.push({ key: "contract", what: `Billed ${p0M(billed)} on ${po.number} with the ${p0M(t)} paid ahead, against its ${p0M(C)}: ${p0M(r2(billed - C))} over`, money: r2(billed - C), next: "Open the PO", act: "po", who: "owner", fixed: !1, why: "function" == typeof pcWhy ? pcWhy("contract") : "" });
      }
      R.pass = !R.holds.length;
    } catch (e) {
      console.warn("p0 payment check", e);
    }
    return R;
  };
}

// --------------------------------------------------------------------------------- the screens
const p0CanBill = () => ["owner", "coord", "billing", "controller"].includes(role());
// A bill's prepayments in one line: invoice, less prepaid, due.
function p0BillMoneyHtml(b) {
  const L = (b.lines || []).filter((l) => l.prepayOf);
  if (!L.length) return "";
  const po = p0PO(b.poId);
  return `<div class="note small p0-billdep" data-p0due="${billTotal(b)}"><b>${p0M(p0Invoice(b))} invoiced</b>${L.map((l) => ` · less ${esc(String(l.desc || "").replace(/^Less prepaid on [^:]+: /, ""))} ${p0M(-l.amount)}`).join("")} · <b>${p0M(billTotal(b))} due</b>. The prepayment${L.length > 1 ? "s were" : " was"} paid on ${esc(po ? po.number : "the order")} before this bill; it comes off here once, so only the rest is paid.</div>`;
}
// The order's Accounting card: what was paid ahead and where it went; Bill the Deposit when the terms ask for one.
function p0PoMoneyExtra(po) {
  if (!po || p0Sub(po) || "cancelled" === po.status) return "";
  const P = p0Prepaid(po),
    R = p0DepositRoom(po, { id: "" }),
    canDep = p0CanBill() && R.pct > 0 && R.before < R.allowed - 1 && ["issued", "partial", "pending"].includes(po.status),
    rows = P.sources.map((s) => {
      const on = (DB.bills || []).filter((b) => b.poId === po.id && p0Live(b) && (b.lines || []).some((l) => l.prepayOf === s.key));
      return `${esc(s.label)} ${p0M(s.amount)}${"deposit" === s.kind ? ` (${esc(billState(s.ref).text || s.ref.status)})` : ""}: ${on.length ? `taken off ${on.map((b) => esc(b.number || "a bill")).join(", ")}` : "comes off the next bill"}`;
    });
  return rows.length || canDep
    ? `<div class="small p0-pomoney" style="margin-top:6px">${rows.length ? `<b>Paid ahead ${p0M(P.total)}</b>: ${rows.join(" · ")}.` : ""}${canDep ? ` <button type="button" class="btn sm" data-p0dep="${esc(po.id)}">Bill the Deposit ${p0M(r2(R.allowed - R.before))}</button>` : ""}</div>`
    : "";
}
if ("function" == typeof poMoneyHtml) {
  const base = poMoneyHtml;
  poMoneyHtml = function (po) {
    const h = base.apply(this, arguments);
    try {
      const x = p0PoMoneyExtra(po);
      if (x && "string" == typeof h) {
        const i = h.lastIndexOf("</div>");
        return i > 0 ? h.slice(0, i) + x + h.slice(i) : h + x;
      }
    } catch (e) {
      console.warn("p0 po money", e);
    }
    return h;
  };
}
// The deposit bill: billing keys the vendor's deposit invoice against the order's terms.
function p0DepositDialog(po) {
  if (!po) return;
  const R = p0DepositRoom(po, { id: "" }),
    v = p0Vend(po.vendor),
    td = today(),
    amt = r2(Math.max(0, R.allowed - R.before)),
    REQ = [['[data-f="number"]', "The vendor's invoice or deposit request number"]];
  const m = mbModal(
    `Bill the Deposit — ${esc(po.number)}`,
    `<p class="small muted" style="margin:0 0 10px">${esc(po.vendor)} · ${p0M(R.tot)} ordered · terms ${R.pct}% on order. The deposit is a prepayment on ${esc(po.number)}: it is paid before delivery, and it comes off the vendor's bill when it arrives.</p>
    <div class="grid2">${mbF("Vendor Invoice #", '<input data-f="number" placeholder="As printed on their deposit request" autocomplete="off">')}${mbF("Invoice Date", `<input type="date" data-f="date" value="${td}">`)}</div>
    <div class="grid2">${mbF("Due", `<input type="date" data-f="due" value="${td}">`)}${mbF("Deposit", `<input type="number" step="0.01" min="0" data-f="amount" value="${amt}">`)}</div>`,
    {
      submit: "Save Deposit Bill",
      onSubmit: (f) => {
        const root = document.getElementById("mbm");
        if ("function" == typeof vfRequire && !vfRequire(root, REQ)) return !1;
        const a = r2(+f.amount || 0);
        if (!(a > 0)) return toast("Say how much the deposit is"), !1;
        if (R.before + a > R.allowed + 1) return toast(`${p0M(R.before + a)} is more than the ${R.pct}% deposit ${po.number}'s terms allow (${p0M(R.allowed)})`), !1;
        const l1 = (po.lines || [])[0] || {},
          b = {
            id: uid("b"),
            vendor: po.vendor,
            number: f.number,
            date: f.date || td,
            due: f.due || td,
            entityId: "function" == typeof poEntity ? poEntity(po) : po.entityId || "",
            projectId: po.projectId || "",
            poId: po.id,
            cat: "function" == typeof poCat ? poCat(po) : "materials",
            code: l1.code || "",
            line: (1 === (po.lines || []).length && l1.line) || "",
            lines: [{ id: uid("bl"), desc: `Deposit ${R.pct}% on ${po.number}`, qty: 1, unit: "ls", amount: a, code: l1.code || "", line: l1.line || "" }],
            payMethod: (v && v.payMethod) || "ACH",
            fileId: "",
            notes: `Deposit on ${po.number}, ${R.pct}% on order`,
            status: "submitted",
            approvals: [{ t: nowStamp(), ts: appNowIso(), by: p0Me(), role: role(), action: "submitted" }],
            createdBy: p0Me(),
            createdAt: appNowIso(),
            deposit: !0,
            taxStatus: po.taxStatus || "none",
          };
        "function" == typeof billLinesNorm && billLinesNorm(b);
        DB.bills.push(b);
        try {
          audit("bill", b.id, "deposit-billed", "", po.number, `${p0M(a)} deposit, ${R.pct}% on order`);
          log(`Deposit bill ${b.number} on ${po.number}: ${p0M(a)}`);
        } catch (e) {}
        save(), render();
        rcToast(`Deposit bill ${b.number} on ${po.number} submitted: ${p0M(a)}, due ${fmt(b.due)}. It comes off ${po.vendor}'s bill when it arrives`, [{ label: "Open", run: flowGo.bill(b) }]);
      },
    },
  );
  m && "function" == typeof vfGate && vfGate(m, m.querySelector("#mbm-ok"), REQ);
  return m;
}
// The order page: the tax repair note to review, and the Sales Tax field's rule (a person chooses the treatment here).
function p0PoTaxNote(po) {
  const X = po && po.taxRepair;
  if (!X) return "";
  return X.reviewed
    ? `<div class="note small p0-taxfix" style="margin:0 0 10px">Purchase tax corrected ${fmt(X.on)} (was ${esc(X.fromWords)}), reviewed by ${esc(X.reviewed.by)} ${fmt(String(X.reviewed.at).slice(0, 10))}.</div>`
    : `<div class="note warn small p0-taxfix" style="margin:0 0 10px"><b>Purchase tax corrected ${fmt(X.on)}.</b> It was ${esc(X.fromWords)}; it is now ${esc(TAX_STATUS[X.to] || X.to)}: ${esc(X.why)}.${["owner", "controller"].includes(role()) ? ' <button type="button" class="btn sm" data-p0taxok>Mark Reviewed</button>' : " The controller reviews it."}</div>`;
}
if ("function" == typeof renderPODoc) {
  const base = renderPODoc;
  renderPODoc = function (po) {
    const h = base.apply(this, arguments);
    try {
      if ("string" == typeof h && po && !["client", "crew", "driver", "foreman"].includes(role())) return p0PoTaxNote(po) + h;
    } catch (e) {}
    return h;
  };
}
function p0TaxReviewed(ids) {
  const by = p0Me(),
    done = [];
  (DB.pos || []).forEach((po) => {
    po.taxRepair && !po.taxRepair.reviewed && (!ids || ids.includes(po.id)) && ((po.taxRepair.reviewed = { by: by, at: appNowIso() }), done.push(po));
  });
  done.forEach((po) => {
    try {
      audit("po", po.id, "purchase-tax-reviewed", "", TAX_STATUS[po.taxStatus] || po.taxStatus, by);
    } catch (e) {}
  });
  return done;
}
if ("function" == typeof wirePODoc) {
  const base = wirePODoc;
  wirePODoc = function (po) {
    const r = base.apply(this, arguments);
    try {
      const root = document.getElementById("po-" + po.id) || document.querySelector(".view.on");
      if (root) {
        const sel = root.querySelector('.po-meta [data-p="taxStatus"]');
        if (sel && !sel.dataset.p0) {
          sel.dataset.p0 = "1";
          // a person's choice of treatment is theirs: the rule never re-decides it
          sel.addEventListener(
            "change",
            () => {
              po.taxRule = Object.assign({}, po.taxRule || { v: P0_V, sig: p0TaxSig(po) }, { chosen: { by: p0Me(), at: appNowIso(), status: sel.value } });
              try {
                audit("po", po.id, "purchase-tax-chosen", "", sel.value, p0Me());
              } catch (e) {}
            },
            !0,
          );
          const f = sel.closest(".f");
          f &&
            !f.querySelector(".p0-taxrule") &&
            f.insertAdjacentHTML(
              "beforeend",
              `<div class="small muted p0-taxrule">${esc(p0TaxWords(po))}. The rule: the firm pays NY sales tax on materials, or accrues use tax when the vendor charges none; the client's ST-124 only takes tax off the client's invoice. Confirm the treatment with the accountant.</div>`,
            );
        }
        const ok = root.querySelector("[data-p0taxok]");
        ok &&
          (ok.onclick = () => {
            p0TaxReviewed([po.id]), save(), render();
            rcToast(`Purchase tax on ${po.number} reviewed`, [{ label: "Open", run: flowGo.po(po) }]);
          });
        root.querySelectorAll("[data-p0dep]").forEach((x) => (x.onclick = () => p0DepositDialog(p0PO(x.dataset.p0dep))));
      }
    } catch (e) {
      console.warn("p0 po page", e);
    }
    return r;
  };
}
document.addEventListener("click", (e) => {
  const x = e.target && e.target.closest && e.target.closest("[data-p0dep]");
  x && !x.onclick && p0DepositDialog(p0PO(x.dataset.p0dep));
});
// The bill drawer: invoice, less prepaid, due; the "Less prepaid" lines are the rule's, not typed; a deposit is
// marked as one when the bill is against an order.
if ("function" == typeof openBill) {
  const base = openBill;
  openBill = function (id) {
    const r = base.apply(this, arguments);
    try {
      const b = id && (DB.bills || []).find((x) => x.id === id),
        body = document.getElementById("d-body");
      if (body) {
        if (b && !body.querySelector(".p0-billdep")) {
          const h = p0BillMoneyHtml(b);
          h && body.insertAdjacentHTML("afterbegin", h);
          body.querySelectorAll('tr[data-bl^="bl_p0_"]').forEach((tr) => {
            tr.querySelectorAll("input").forEach((i) => ((i.readOnly = !0), (i.title = "Taken off by the prepayment rule")));
            tr.querySelectorAll("[data-rmbl]").forEach((x) => x.remove());
          });
        }
        const poSel = body.querySelector("#e-po");
        if (poSel && !body.querySelector("#e-p0dep") && editing && "bill" === editing.kind) {
          const was = !!b && p0IsDeposit(b),
            wrap = poSel.closest(".f2") || poSel.closest(".f");
          wrap &&
            wrap.insertAdjacentHTML(
              "afterend",
              `<label class="small p0-depchk" style="display:${poSel.value ? "flex" : "none"};gap:8px;align-items:center;min-height:44px"><input type="checkbox" id="e-p0dep" ${was ? "checked" : ""} ${poSel.disabled ? "disabled" : ""}> This bill is a deposit on the order (a prepayment, taken off the vendor's bill later)</label>`,
            );
          const chk = body.querySelector("#e-p0dep"),
            lab = chk && chk.closest("label");
          poSel.addEventListener("change", () => lab && (lab.style.display = poSel.value ? "flex" : "none"));
          const collect = editing.collect;
          collect &&
            (editing.collect = function () {
              const o = collect.apply(this, arguments);
              try {
                o && o.poId && chk ? (chk.checked ? (o.deposit = !0) : was && (o.deposit = !1)) : o && was && !o.poId && (o.deposit = !1);
                // the rule's own lines keep their link through an edit
                o &&
                  Array.isArray(o.lines) &&
                  b &&
                  o.lines.forEach((l) => {
                    const old = (b.lines || []).find((x) => x.id === l.id);
                    old && old.prepayOf && Object.assign(l, { prepayOf: old.prepayOf, p0: 1, code: old.code, line: old.line, qty: 1, unit: "ls", amount: old.amount });
                  });
              } catch (e) {}
              return o;
            });
        }
      }
    } catch (e) {
      console.warn("p0 bill drawer", e);
    }
    return r;
  };
}
// The vendor's record says whether they charge NY sales tax: the one input the purchase-tax rule reads from a person.
if ("function" == typeof openVendor) {
  const base = openVendor;
  openVendor = function (id) {
    const r = base.apply(this, arguments);
    try {
      const v = id ? (DB.vendors || []).find((x) => x.id === id) : null,
        w9 = document.getElementById("e-w9"),
        body = document.getElementById("d-body");
      if (w9 && body && !body.querySelector("#e-p0tax") && editing) {
        const on = p0VendorCharges(v),
          wrap = w9.closest(".f2") || w9.closest(".f") || w9.parentElement;
        wrap.insertAdjacentHTML(
          "afterend",
          `<div class="f"><label>NY Sales Tax</label><select id="e-p0tax"><option value="1" ${on ? "selected" : ""}>Charges NY sales tax: the firm pays it on the order</option><option value="0" ${on ? "" : "selected"}>Charges none: the firm accrues use tax</option></select><div class="small muted">Materials for a capital improvement are taxed to the firm either way; the client's ST-124 only takes tax off the client's invoice. Confirm with the accountant.</div></div>`,
        );
        const collect = editing.collect;
        collect &&
          (editing.collect = function () {
            const o = collect.apply(this, arguments),
              s = document.getElementById("e-p0tax");
            o && s && (o.chargesTax = "1" === s.value);
            return o;
          });
      }
    } catch (e) {
      console.warn("p0 vendor tax", e);
    }
    return r;
  };
}
// The order sheet says the tax the order will carry, by the one rule, as the supplier and price are entered.
function p0SheetTax(root) {
  const el = root && root.querySelector(".p0-taxline");
  if (!el) return;
  const q = (k) => root.querySelector(`[data-f="${k}"]`),
    vn = q("vendor") ? q("vendor").value : "",
    po = { type: "materials", vendor: "__quote__" === vn ? "" : vn, lines: [{ qty: +((q("qty") || {}).value || 0), price: +((q("price") || {}).value || 0) }] };
  el.textContent = vn && "__quote__" !== vn ? `Tax: ${p0TaxWords(Object.assign(po, { taxStatus: p0PurchaseTax(po).status }))}.` : "Tax: set by the supplier's record when it is chosen.";
}
if ("function" == typeof buyOrderDialog) {
  const base = buyOrderDialog;
  buyOrderDialog = function () {
    const m = base.apply(this, arguments);
    try {
      const root = document.getElementById("mbm");
      if (root && root.querySelector('[data-f="price"]') && !root.querySelector(".p0-taxline")) {
        const at = root.querySelector(".fl-paper") || root.querySelector('[data-f="needBy"]');
        at && (at.closest(".grid2") || at).insertAdjacentHTML("beforebegin", '<div class="small muted p0-taxline" style="margin:0 0 8px"></div>');
        p0SheetTax(root);
      }
    } catch (e) {
      console.warn("p0 order sheet tax", e);
    }
    return m;
  };
}
["input", "change"].forEach((ev) =>
  document.addEventListener(ev, (e) => {
    const root = e.target && e.target.closest && e.target.closest("#mbm");
    root && root.querySelector(".p0-taxline") && e.target.matches('[data-f="qty"],[data-f="price"],[data-f="vendor"]') && p0SheetTax(root);
  }),
);

// --------------------------------------------------------------------------------- Approvals and Today
if ("undefined" != typeof APPR_CHIPS) {
  const at = APPR_CHIPS.findIndex(([k]) => "other" === k);
  APPR_CHIPS.splice(at < 0 ? APPR_CHIPS.length : at, 0, ["prepay", "Prepayments"], ["taxfix", "Purchase Tax"]);
}
if ("undefined" != typeof DELEGATION) {
  DELEGATION.prepay = {
    role: "coord",
    rule: "money paid to a vendor before any bill or delivery is confirmed as a prepayment on its order by the coordinator, who placed the order; the controller sees it in Caught for You until it is",
  };
  DELEGATION.taxfix = { role: "controller", rule: "a purchase-tax correction the rule made to an order already with the vendor is the controller's to review" };
}
// The controller's Today: the same prepayments, in Caught for You (the coordinator owns the confirmation)
if ("undefined" != typeof CATCH)
  CATCH.push({
    name: "prepaidAhead",
    label: "Paid Ahead, No Bill",
    rows: () =>
      "controller" === role()
        ? p0PrepayOpen().map((t) => {
            const W = p0PrepayWords(t),
              P = W.papers;
            return { key: "prepay:" + t.id, what: `Paid ahead: ${W.po ? W.po.vendor : t.vendor || t.desc}`, sub: `${p0M(-t.amt)} on ${fmt(t.date)}${W.po ? `, ${W.po.number}, no bill` : ""}${P && (!P.coi.ok || !P.w9.ok) ? `; ${[!P.coi.ok ? "no COI" : "", !P.w9.ok ? "no W-9" : ""].filter(Boolean).join(", ")}` : ""}`, amount: r2(-t.amt), verb: "Review", run: () => p0PrepaySheet(t.id) };
          })
        : [],
  });
if ("undefined" != typeof STD_MAP)
  Object.assign(STD_MAP, {
    prepaidAhead: { p: "integrity", leak: !0, c: ["value", "dollar", /No money is committed/i] },
    // money out with no bill is a paper-trail question (integrity); to a vendor with no COI or W-9 it is the law's
    prepay: { p: (it) => (it && "bad" === it.sev ? "law" : "integrity"), leak: !0, c: ["value", "dollar", /No money is committed/i] },
    taxfix: { p: "law", c: ["value", "dollar", /paper trail/i] },
  });
function p0ApprItems() {
  const add = [];
  p0PrepayOpen().forEach((t) => {
    const W = p0PrepayWords(t),
      P = W.papers;
    add.push({
      kind: "prepay",
      id: t.id,
      projectId: (W.po && W.po.projectId) || t.projectId || "",
      sev: P && (!P.coi.ok || !P.w9.ok) ? "bad" : "warn",
      n: p0M(-t.amt),
      amount: r2(-t.amt),
      // money already out with no bill behind it: it ranks with the money waiting now (the Standard's own mark)
      moneyNow: r2(-t.amt) >= (+((DB.company || {}).moneyFirstOver != null ? DB.company.moneyFirstOver : 1e3) || 0),
      title: `Paid before delivery · ${W.po ? W.po.vendor : t.vendor || t.desc}`,
      detail: [W.po ? W.line : `could be ${(t.prepayAsk || []).map((id) => (p0PO(id) || {}).number).filter(Boolean).join(" or ")}`, P ? `${P.coi.text}; ${P.w9.text}` : ""].filter(Boolean).join(" · "),
      yes: "Review",
      no: "Not This Order",
      act: "review",
      open: W.po ? { view: "po", po: W.po.id } : { view: "banking" },
    });
  });
  const fix = (DB.pos || []).filter((po) => po.taxRepair && !po.taxRepair.reviewed);
  fix.length &&
    add.push({
      kind: "taxfix",
      id: "taxfix",
      projectId: "",
      sev: "warn",
      n: `${fix.length} order${1 === fix.length ? "" : "s"}`,
      title: `Purchase tax corrected on ${fix.length} order${1 === fix.length ? "" : "s"}`,
      detail: `${fix.map((po) => po.number).join(", ")} · the firm pays sales tax on materials, or accrues use tax; an ST-124 only exempts the client's invoice`,
      yes: "Review",
      no: "Later",
      act: "review",
      open: { view: "po" },
    });
  return add;
}
if ("function" == typeof mApprovals) {
  const base = mApprovals;
  mApprovals = function (opts) {
    const out = base.apply(this, arguments);
    try {
      if (!Array.isArray(out)) return out;
      // a bill that took a prepayment says so on its card
      out.forEach((it) => {
        if ("bill" !== it.kind) return;
        const b = (DB.bills || []).find((x) => x.id === it.id),
          ap = b ? p0AppliedOn(b) : 0;
        ap > 0.005 && (it.detail = `${p0M(p0Invoice(b))} invoiced less ${p0M(ap)} prepaid, ${p0M(billTotal(b))} due · ${it.detail || ""}`);
      });
      const add = p0ApprItems();
      add.forEach((it) => (it.who = "prepay" === it.kind ? "coord" : "controller"));
      return out.concat(opts && opts.everyone ? add : add.filter((it) => it.who === role()));
    } catch (e) {
      console.warn("p0 approvals", e);
      return out;
    }
  };
}
function p0TaxFixSheet() {
  const fix = (DB.pos || []).filter((po) => po.taxRepair && !po.taxRepair.reviewed);
  if (!fix.length) return toast("Every purchase-tax correction is reviewed");
  const can = ["owner", "controller"].includes(role());
  return mbModal(
    "Purchase Tax Corrected",
    `<p class="small muted" style="margin:0 0 10px">These orders were issued as "Exempt — capital improvement". A capital improvement takes sales tax off the client's invoice; it never exempts what the firm buys. Each order now pays the vendor's tax or accrues use tax. Confirm the treatment with the accountant.</p>${fix
      .map(
        (po) =>
          `<div class="card" style="margin:0 0 8px"><div class="row" style="gap:8px;align-items:baseline"><b>${esc(po.number)}</b><span class="small muted">${esc(po.vendor)} · ${esc(p0Job(po.projectId))}</span><span class="grow"></span><a href="#" data-p0open="${esc(po.id)}">Open</a></div><div class="small">${esc(TAX_STATUS[po.taxStatus] || po.taxStatus)} · ${p0M(po.taxRepair.fromTotal)}${po.taxRepair.toTotal !== po.taxRepair.fromTotal ? ` now ${p0M(po.taxRepair.toTotal)}` : ""}${po.useTax && po.useTax.amount ? ` · use tax ${p0M(po.useTax.amount)} to accrue` : ""}</div><div class="small muted">${esc(po.taxRepair.why)}</div></div>`,
      )
      .join("")}`,
    {
      submit: can ? "Mark Reviewed" : null,
      onSubmit: () => {
        const d = p0TaxReviewed(fix.map((po) => po.id));
        save(), render();
        rcToast(`Purchase tax reviewed on ${d.map((po) => po.number).join(", ")}`, d[0] ? [{ label: "Open", run: flowGo.po(d[0]) }] : null);
      },
    },
  );
}
document.addEventListener("click", (e) => {
  const a = e.target && e.target.closest && e.target.closest("[data-p0open]");
  if (!a) return;
  e.preventDefault();
  const po = p0PO(a.dataset.p0open);
  po && ("function" == typeof mbCloseModal && mbCloseModal(), flowGo.po(po)());
});
function p0ApprYes(it) {
  return it && ("prepay" === it.kind ? p0PrepaySheet(it.id) : "taxfix" === it.kind ? p0TaxFixSheet() : null);
}
function p0ApprNo(it) {
  return it && ("prepay" === it.kind ? p0PrepayUnlink(it.id) : "taxfix" === it.kind ? void setView("po") : null);
}
if ("function" == typeof renderMApprove) {
  const base = renderMApprove;
  renderMApprove = function () {
    const r = base.apply(this, arguments);
    try {
      const v = document.getElementById("v-mapprove");
      if (v && v.querySelector('.m-appr[data-mk="prepay"], .m-appr[data-mk="taxfix"]')) {
        const items = mApprovals();
        v.querySelectorAll('.m-appr[data-mk="prepay"], .m-appr[data-mk="taxfix"]').forEach((el) => {
          const it = items.find((x) => x.kind === el.dataset.mk && String(x.id) === el.dataset.mid);
          if (!it) return;
          const y = el.querySelector("[data-myes]"),
            n = el.querySelector("[data-mno]");
          y && (y.onclick = (e) => (e.preventDefault(), e.stopPropagation(), p0ApprYes(it)));
          n && (n.onclick = (e) => (e.preventDefault(), e.stopPropagation(), p0ApprNo(it)));
        });
      }
    } catch (e) {
      console.warn("p0 approvals page", e);
    }
    return r;
  };
}
// Do Now ranks money paid ahead with the held payments, and the tax corrections just under them
if ("function" == typeof tdScore) {
  const base = tdScore;
  tdScore = function (it) {
    if (it && "prepay" === it.kind) return 53 + ("bad" === it.sev ? 4 : 0);
    if (it && "taxfix" === it.kind) return 48;
    return base.apply(this, arguments);
  };
}
if ("function" == typeof tdCard) {
  const base = tdCard;
  tdCard = function (it) {
    const c = base.apply(this, arguments);
    try {
      if (it && ("prepay" === it.kind || "taxfix" === it.kind)) {
        c.line1 = esc(`${it.title} · ${it.n}`);
        c.why = esc(String(it.detail || "").split(" · ")[0]);
        c.verb = it.yes;
        c.run = () => p0ApprYes(it);
        const po = "prepay" === it.kind && it.open && it.open.po ? p0PO(it.open.po) : null;
        po && (c.go = flowGo.po(po));
      }
    } catch (e) {}
    return c;
  };
}

// --------------------------------------------------------------------------------- Ask: vendor-direction money
// "what deposits have I paid" and "what does Nemo Tile owe us" are about vendors: they never answer with client money.
function p0AskRoute(q) {
  const r = role(),
    l = String(q || "").toLowerCase().replace(/\s+/g, " ").trim();
  if (["client", "foreman", "crew", "driver", "designer"].includes(r)) return null;
  const pre = /\b(prepayments?|prepaid|paid ahead|paid before (delivery|the bill))\b/.test(l),
    dep = /\bdeposits?\b/.test(l) && /\b(i|we) (have )?(paid|made|put down)\b|\bpaid\b|\bon (the |our )?(orders?|pos?|purchase orders?)\b|\bvendors?\b|\bsuppliers?\b/.test(l);
  if ((pre || dep) && !/\b(client|customer|receiv|retainer|from the|collected)\b/.test(l)) {
    const rows = (DB.pos || []).filter((po) => !p0Sub(po) && "cancelled" !== po.status).map((po) => ({ po: po, P: p0Prepaid(po) })).filter((x) => x.P.total > 0.005),
      tot = r2(rows.reduce((a, x) => a + x.P.total, 0)),
      open = r2(rows.reduce((a, x) => a + x.P.unapplied, 0)),
      conf = p0PrepayOpen().length;
    return {
      kind: "p0-deposits",
      headline: rows.length
        ? `${rows.length} order${1 === rows.length ? " has" : "s have"} money paid ahead: ${p0M(tot)}, ${p0M(r2(tot - open))} taken off bills, ${p0M(open)} to come off the next bill${conf ? `; ${conf} prepayment${1 === conf ? "" : "s"} to confirm` : ""}.`
        : "No deposits or prepayments are open on any order.",
      work: rows.map((x) => `${x.po.number} · ${x.po.vendor} · ${p0Job(x.po.projectId)}: ${x.P.sources.map((s) => `${s.label} ${p0M(s.amount)}`).join(", ")}${x.P.unapplied > 0.005 ? `, ${p0M(x.P.unapplied)} not taken off a bill yet` : ", all taken off"}`),
      go: { view: "po" },
      n: rows.length,
    };
  }
  const m = /\b(?:what|how much) (?:does|do) (.+?) owe us\b|\bdoes (.+?) owe us\b|\bcredits? (?:from|with) (.+?)\b(?:\?|$)/.exec(l),
    name = m && (m[1] || m[2] || m[3] || "").replace(/^the /, "").trim();
  if (name) {
    const v = (DB.vendors || []).find((x) => {
      const n = String(x.name || "").toLowerCase();
      return n && (n === name || n.startsWith(name) || name.startsWith(n));
    });
    if (!v) return null;
    const credits = (DB.bills || []).filter((x) => scLow(x.vendor) === scLow(v.name) && "approved" === x.status && billTotal(x) < -0.005).map((x) => ({ b: x, left: r2(-billTotal(x) - (x.takenBy || []).reduce((a, t) => a + (+t.amount || 0), 0)) })).filter((c) => c.left > 0.005),
      over = "function" == typeof pcOverpaid ? pcOverpaid().filter((x) => scLow(x.b.vendor) === scLow(v.name)) : [],
      pre = (DB.pos || []).filter((po) => scLow(po.vendor) === scLow(v.name) && !p0Sub(po)).map((po) => ({ po: po, P: p0Prepaid(po) })).filter((x) => x.P.unapplied > 0.005),
      sum = r2(credits.reduce((a, c) => a + c.left, 0) + over.reduce((a, x) => a + x.open, 0) + pre.reduce((a, x) => a + x.P.unapplied, 0));
    return {
      kind: "p0-vendor-owes",
      headline: sum > 0.005 ? `${v.name} owes us ${p0M(sum)}: ${[credits.length ? `${p0M(r2(credits.reduce((a, c) => a + c.left, 0)))} of credit not taken` : "", over.length ? `${p0M(r2(over.reduce((a, x) => a + x.open, 0)))} overpaid` : "", pre.length ? `${p0M(r2(pre.reduce((a, x) => a + x.P.unapplied, 0)))} paid ahead, to come off the next bill` : ""].filter(Boolean).join(", ")}.` : `${v.name} owes us nothing: no open credit, no overpayment and nothing paid ahead.`,
      work: credits.map((c) => `Credit ${c.b.number || ""}: ${p0M(c.left)} not taken`).concat(over.map((x) => `${x.b.number || "A bill"} overpaid ${p0M(x.open)}`), pre.map((x) => `${x.po.number}: ${p0M(x.P.unapplied)} paid ahead`)),
      go: { view: "vendors" },
      n: credits.length + over.length + pre.length,
    };
  }
  return null;
}
if ("function" == typeof paAsk) {
  const base = paAsk;
  paAsk = function (q) {
    let a = null;
    try {
      a = p0AskRoute(q);
    } catch (e) {
      console.warn("p0 ask", e), (a = null);
    }
    if (a) {
      try {
        paInit();
      } catch (e) {}
      return paOut(Object.assign({}, a, { routedBy: "p0money", go: a.go ? paGo(a.go) : null, offers: [] }));
    }
    return base.apply(this, arguments);
  };
}
