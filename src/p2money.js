// =====================================================================================================================
// Pilot 2 money fixes (lane p2fix2, 2026-10-25). The controller and billing worked three days and found money the app
// let leak. Each class is fixed at its root and proven to the cent in tests/p2money_test.py:
//  1  one vendor invoice booked twice (Satish SE-0922 $7,400: one ACH, two bills, two $7,400 payments);
//  2  a one-tap "Enter the Bill" that posted a paid bill nobody had looked at, with a toast that said otherwise;
//  3  client cash with no bank line ("Apply" on a "money is sent" mail), a bank receipt left in Needs Category after it
//     was recorded, and a journal in Made Today nobody made;
//  4  Record Payment defaulting the whole invoice ($24,000) when the bank line was $12,000;
//  5  two invoices on one PO a day apart (Tino TIN-7194 $8,491 and TIN-3277 $8,651 on PO-2026-047) as two to-dos
//     with no word of each other;
//  6  a grid subline run into its line ("Payroll 8/31 - 9/46 employees");
//  7  lines billed ahead of the work flagged only inside the progress grid (INV-2026-038 at 51.67% against 0-20%
//     complete on six lines, CO-2026-001 at 50% against 0%).
//
// Design gate (BACKLOG §1.16). No new store, list, queue or menu item. The nouns extended:
//  - Bill (DB.bills): every path that makes one goes through vbAdd(b), which first asks vbFind for the same vendor
//    and invoice number, or the same bank line, or the same amount inside ten days. A bill carries dupOf when a person
//    says it is a different invoice; billFlags (the Approvals flag list) reads it.
//  - Bank line (DB.txns): a "no bill on file" proposal is re-read against the bills on file before it is shown or
//    confirmed (vbRefreshProps); a deposit is linked to the payment that records it (truthSetMatch, the one link).
//  - Client payment (client.payments): Record Payment (paymentAllocate) carries the bank line it records.
//  - Expected client money (DB.expected, the existing store the mail reader writes): shown on Billing's Payments tab.
//  - Progress lines (pgRows): the existing billed % and complete %; CATCH portalBilledAhead (Caught for You on
//    Today) reads the line-by-line amount; an invoice carries aheadWhy when it is sent further ahead with a reason.
// Functions wrapped here, outermost to the chains in app.js, subs.js and p0money.js: saveBill, confirmMatch,
// truthSetMatch, renderBank, nyhRowsAll, billFlags, paymentAllocate, renderDocEditor, docAction, billingRows,
// renderPODoc, renderBilling (the Payments tab note). Root edits in app.js call vbAdd, vbReviewMail, vbDepositApply,
// vbMatchWords and dgSubSep.
// =====================================================================================================================

// ---- 1. one gate for every vendor bill ------------------------------------------------------------------------------
const vbNum = (s) => String(s || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
const vbWho = () => ((typeof currentUser === "function" && currentUser()) || {}).name || role();
function vbSameVendor(a, b) {
  const x = String(a || "").trim().toLowerCase(),
    y = String(b || "").trim().toLowerCase();
  if (!x || !y) return !1;
  if (x === y) return !0;
  const A = truthNorm(a),
    B = truthNorm(b);
  return !!A.length && !!B.length && (A.every((w) => B.includes(w)) || B.every((w) => A.includes(w)));
}
// the bank or card line that pays a bill, by whichever link a path wrote
function vbBankOf(b) {
  if (!b) return "";
  if (b.txnId || b.paidTxnId) return b.txnId || b.paidTxnId;
  const t = (DB.txns || []).find((x) => x.billId === b.id);
  if (t) return t.id;
  const p = (DB.payments || []).find((x) => x.billId === b.id && !x.void && x.txnId);
  return p ? p.txnId : "";
}
const vbLive = (b) => b && !["void", "rejected"].includes(b.status) && !b.ic && !b.retainageRelease;
const vbIsDeposit = (b) => !!b && ("function" == typeof p0IsDeposit ? p0IsDeposit(b) : !0 === b.deposit);
const vbPlaceholder = (b) => !!b && !!b.fromTxn && /^(PAY|CHK)-/.test(String(b.number || ""));
// The one finder. s: {vendor, number, amount, date, txnId, excludeId}. Returns {bill, how, exact, why} or null.
//  - number: the same vendor's same invoice number (SE-0922 = se 0922) is the same invoice: exact;
//  - bank:   a bill of the same vendor already paid by this bank line: exact (one payment pays one bill);
//  - amount: the same vendor's bill for the same amount within ten days: exact when this is a bank line and that bill
//            has no bank line of its own yet (the payment pays it), otherwise a possible duplicate a person decides.
function vbFind(s) {
  const o = s || {},
    L = (DB.bills || []).filter((b) => vbLive(b) && b.id !== o.excludeId && vbSameVendor(b.vendor, o.vendor));
  if (!L.length) return null;
  const n = vbNum(o.number),
    say = (b) => `${b.number || "a bill"} from ${b.vendor}, ${money(billTotal(b))}${b.date ? ` dated ${fmtL(b.date)}` : ""}`;
  if (n.length >= 3) {
    const b = L.find((x) => vbNum(x.number) === n);
    if (b) return { bill: b, how: "number", exact: !0, why: `${say(b)}, is already on file` };
  }
  if (o.txnId) {
    const b = L.find((x) => vbBankOf(x) === o.txnId);
    if (b) {
      const t = (DB.txns || []).find((x) => x.id === o.txnId);
      return { bill: b, how: "bank", exact: !0, why: `the ${t ? fmtL(t.date) + " " : ""}bank line already pays ${say(b)}` };
    }
  }
  const amt = r2(+o.amount || 0);
  if (amt > 0) {
    // the same amount is no duplicate when the two are on different orders, or one is the order's deposit and the
    // other its final bill (a 50% deposit and the balance after it are both $4,400 on an $8,800 order)
    const d = o.date || today(),
      b = L.find(
        (x) =>
          (Math.abs(billTotal(x) - amt) < 0.01 || Math.abs(billGross(x) - amt) < 0.01) &&
          [x.date, x.paidAt].some((y) => y && Math.abs(dayDiff(y, d)) <= 10) &&
          !(x.poId && o.poId && x.poId !== o.poId) &&
          !vbIsDeposit(x) &&
          !o.deposit,
      );
    if (b) {
      const exact = !!o.txnId && !vbBankOf(b) && (!n || vbPlaceholder(b));
      return { bill: b, how: "amount", exact: exact, why: `${say(b)}, is the same vendor and amount within ten days` };
    }
  }
  return null;
}
// Every path that makes a vendor bill adds it here. A bill already on file (the same invoice number, or the same bank
// line) is never added again: the bill on file is returned and the caller links to it. A possible duplicate (the same
// amount within ten days) is added carrying dupOf, so Approvals shows it before anyone approves or pays it.
function vbAdd(b, ctx) {
  const o = ctx || {};
  DB.bills = DB.bills || [];
  vbAdd.last = null;
  if (!b) return b;
  if (!o.allowDup) {
    const hit = vbFind({ vendor: b.vendor, number: b.number, amount: billTotal(b), date: b.date, txnId: o.txnId || b.txnId || b.paidTxnId || "", excludeId: b.id, poId: b.poId || "", deposit: vbIsDeposit(b) });
    if (hit && hit.exact) {
      vbAdd.last = hit;
      try {
        audit("bill", hit.bill.id, "duplicate-refused", "", `${b.vendor} ${b.number || ""} ${money(billTotal(b))}`, `${o.src || "a path"} tried to enter it again: ${hit.why}`);
      } catch (e) {}
      return hit.bill;
    }
    hit && !b.dupOf && (b.dupOf = { billId: hit.bill.id, number: hit.bill.number || "", why: hit.why, at: appNowIso(), by: vbWho() });
  }
  DB.bills.push(b);
  return b;
}
// The same check where a person is entering a bill on a form: before it is saved, never after. An invoice already on
// file stops the save and offers Open; a possible duplicate asks the person to say it is a different invoice.
function vbGate(b, root, okSel) {
  const hit = b && vbFind({ vendor: b.vendor, number: b.number, amount: billTotal(b), date: b.date, txnId: b.txnId || "", excludeId: b.id, poId: b.poId || "", deposit: vbIsDeposit(b) });
  if (!hit) return !0;
  const sig = `${hit.bill.id}:${vbNum(b.number)}:${r2(billTotal(b))}`;
  if (!hit.exact && root && root.dataset.vbAck === sig) {
    b.dupOf = { billId: hit.bill.id, number: hit.bill.number || "", why: hit.why, at: appNowIso(), by: vbWho(), ack: !0 };
    return !0;
  }
  if (!root) return !hit.exact;
  root.querySelectorAll(".vb-dup").forEach((x) => x.remove());
  const note = document.createElement("div");
  (note.className = "note bad vb-dup"),
    (note.innerHTML = `<div class="small"><b>${hit.exact ? "Already on file" : "Possible duplicate"}:</b> ${esc(hit.why)}${hit.exact ? ". Entering it again would count the cost twice and pay it twice." : ". Open it to compare, or say this is a different invoice."}</div><div class="row" style="gap:8px;margin-top:8px;flex-wrap:wrap"><button type="button" class="btn sm" data-vbopen>Open ${esc(hit.bill.number || "the Bill")}</button>${hit.exact ? "" : '<button type="button" class="btn sm" data-vback>It Is a Different Invoice</button>'}</div>`);
  const host = root.querySelector(".mbm-bd, #d-body") || root;
  host.prepend(note);
  note.querySelector("[data-vbopen]").onclick = () => {
    try {
      mbCloseModal();
    } catch (e) {}
    try {
      "function" == typeof closeEditor && document.getElementById("drawer") && document.getElementById("drawer").classList.contains("on") && closeEditor();
    } catch (e) {}
    flowGo.bill(hit.bill)();
  };
  const ack = note.querySelector("[data-vback]");
  ack &&
    (ack.onclick = () => {
      root.dataset.vbAck = sig;
      note.remove();
      const ok = root.querySelector(okSel || "#mbm-ok, #d-save");
      ok && ok.click();
    });
  try {
    note.scrollIntoView({ block: "nearest" });
  } catch (e) {}
  return !1;
}
// the bill form (Bills & Payroll > New Vendor Bill): the check runs on the typed vendor, number, amount and date
{
  const base = saveBill;
  saveBill = function () {
    let tmp = null;
    try {
      const id = editing && editing.id,
        o = !id && editing && editing.collect ? editing.collect() : null,
        dr = document.getElementById("drawer");
      tmp = o && o.vendor ? Object.assign({ id: "__new" }, o) : null;
      if (tmp && !vbGate(tmp, dr, "#d-save")) return;
    } catch (e) {
      console.warn("bill duplicate check", e);
    }
    const n0 = (DB.bills || []).length,
      r = base.apply(this, arguments);
    // the person's "it is a different invoice" goes on the bill the form saved
    tmp && tmp.dupOf && (DB.bills || []).length > n0 && Object.assign(DB.bills[DB.bills.length - 1], { dupOf: tmp.dupOf }) && save();
    return r;
  };
}
// a person said it is a different invoice: Approvals says so, with the other bill
{
  const base = billFlags;
  billFlags = function (b) {
    const f = base.apply(this, arguments) || [];
    try {
      const d = b && b.dupOf && (DB.bills || []).find((x) => x.id === b.dupOf.billId && vbLive(x));
      // the person's word replaces the plain "possible duplicate" line, so Approvals reads one line for one question
      d && b.dupOf.ack && f.splice(0, f.length, ...f.filter((x) => !/^Possible duplicate/.test(x)));
      d && !f.some((x) => /duplicate/i.test(x)) && f.push(`Possible duplicate of ${d.number || "a bill"} (${money(billTotal(d))}${d.date ? ", " + fmtL(d.date) : ""})${b.dupOf.ack ? `: ${b.dupOf.by} said it is a different invoice` : ""}`);
      const S2 = b && b.poId && vbPoSiblings(b.poId, { billId: b.id });
      S2 && S2.others.length && f.push(S2.words);
    } catch (e) {}
    return f;
  };
}

// ---- 1b. the bank: a "no bill on file" proposal is re-read before it is shown or confirmed ------------------------------
// Banking's match card said "no bill on file" for the Satish ACH after SE-0922 had been entered and paid by it, because
// the proposal was written the evening before and nobody looked again; Confirm then entered PAY-260902. A proposal to
// enter a bill from a payment now goes when the line is already paid to a bill, and becomes a proposal to match the
// bill on file when one is there.
function vbRefreshProps(ids) {
  let n = 0;
  (DB.txns || []).forEach((t) => {
    const P = t.proposal;
    if (!P || "newbill" !== P.kind || (ids && !ids.includes(t.id))) return;
    const live = t.billId && (DB.bills || []).find((b) => b.id === t.billId && vbLive(b));
    if (live) return (t.proposal = null), n++;
    const nb = (P.m || {}).newBill || {},
      hit = vbFind({ vendor: nb.vendor, number: nb.number, amount: Math.abs(+t.amt), date: t.date, txnId: t.id });
    if (hit && hit.exact) {
      const b = hit.bill;
      (t.proposal = { t: nowStamp(), by: "auto", kind: "bill", billId: b.id, m: { billId: b.id, poId: b.poId || "" }, why: `${b.number || "the bill"} from ${b.vendor} is on file for ${money(billTotal(b))}: this payment pays it (no second bill)`, label: `Bill ${b.number || ""} · ${b.vendor}` }), n++;
    }
  });
  return n;
}
if ("function" == typeof renderBank) {
  const base = renderBank;
  renderBank = function () {
    try {
      vbRefreshProps();
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
{
  const base = confirmMatch;
  confirmMatch = function (t) {
    try {
      if (t && t.proposal && "newbill" === t.proposal.kind) {
        vbRefreshProps([t.id]);
        if (!t.proposal) {
          const b = (DB.bills || []).find((x) => x.id === t.billId);
          window.vbMatchSaid = b ? `Already matched: ${b.number || "the bill"} from ${b.vendor} is paid by this line. No second bill` : "";
          return save(), !0;
        }
        if ("bill" === t.proposal.kind) {
          const b = (DB.bills || []).find((x) => x.id === t.proposal.billId);
          b && (window.vbMatchSaid = `Matched to ${b.number || "the bill"} from ${b.vendor}, already on file: no second bill`);
        }
      }
    } catch (e) {
      console.warn("refresh proposal", e);
    }
    return base.apply(this, arguments);
  };
}
// a bill entered from a payment is the one on file when it is (lkBillFromTxn calls vbAdd); a line already paid to a
// live bill is linked, never given a second one
{
  const base = truthSetMatch;
  truthSetMatch = function (t, m0, o) {
    if (t && m0 && m0.newBill) {
      const live = t.billId && (DB.bills || []).find((b) => b.id === t.billId && vbLive(b));
      if (live) return (t.proposal = null), save(), { ok: !0, m: truthMatchOf(t), linked: live };
    }
    return base.apply(this, arguments);
  };
}
// the words on the match card: a deposit reads as money in, a payment as money out
function vbMatchWords(t) {
  return +t.amt > 0 ? `${money(+t.amt)} received` : money(-t.amt);
}

// ---- 2. Enter the Bill opens the bill, filled in, and posts only on a person's yes ---------------------------------
// The review: vendor, invoice number and dates, amount, job, cost code, estimate line, the order, the bank line that
// paid it, who approves it, and any bill on file for the same invoice. Nothing is written until Enter the Bill.
function vbCodeFor(text) {
  const t = String(text || "").toLowerCase(),
    k = LINE_KW.find(([w]) => t.includes(w));
  return k ? k[1] : "";
}
function vbLineFor(pid, code) {
  if (!pid || !code) return "";
  const L = lineOptions(pid).filter((o) => codeForLine(o.line) === code || o.line.code === code);
  return L.length ? L[0].key : "";
}
// bank and card lines that could be this bill's payment: money out, to this vendor, for this amount, not paid to
// another bill; the one the reader named first
function vbBankCands(vendor, amount, txnId) {
  const amt = r2(+amount || 0),
    out = (DB.txns || []).filter((t) => +t.amt < 0 && (t.id === txnId || (!t.billId && !t.payrollId && truthVendorHit(t, vendor) && Math.abs(Math.abs(+t.amt) - amt) < 0.01)));
  return out.sort((a, b) => (a.id === txnId ? -1 : b.id === txnId ? 1 : String(b.date).localeCompare(String(a.date)))).slice(0, 6);
}
function vbRouteWords(amount) {
  return "function" == typeof needsOwner && needsOwner(amount) ? "the PM's review, then the Owner's approval" : "the PM's approval (under the Owner's threshold)";
}
function vbReviewable(c, p) {
  const R = (c && c.route) || {};
  return !!p && "bill" === p.kind && !p.amountUnread && +p.amount > 0 && !!(p.vendorId || R.vendorId);
}
function vbReviewMail(c, p) {
  if (!vbReviewable(c, p)) return "";
  const R = c.route || {},
    po = (p.poId && (DB.pos || []).find((x) => x.id === p.poId)) || ("function" == typeof cmBillPO ? cmBillPO(c, p) : null),
    v = (DB.vendors || []).find((x) => x.id === (p.vendorId || R.vendorId)) || ("function" == typeof vendorRec ? vendorRec(p.vendor) : null),
    pid = p.projectId || R.projectId || (po && po.projectId) || "",
    words = [c.subject, c.text, ...(c.attachments || []).map((a) => a.text || ""), v && v.trade].join(" "),
    pl = po && (po.lines || [])[0],
    code = (pl && pl.code) || vbCodeFor(words),
    date = String(p.invDate || c.date || today()).slice(0, 10);
  return vbReview(
    {
      vendor: p.vendor || (v && v.name) || "",
      number: p.number || "",
      date: date,
      due: ("function" == typeof cmDueIso && cmDueIso(p.due)) || iso(addDays(date, 30)),
      amount: r2(+p.amount || 0),
      projectId: pid,
      poId: po ? po.id : "",
      code: code,
      line: (pl && pl.line) || vbLineFor(pid, code),
      txnId: p.txnId || "",
      entityId: p.entityId || "",
      desc: c.subject || "",
      commId: c.id,
      src: "mail",
    },
    (b, how) => {
      const did = how;
      (p.applied = did), (p.appliedAt = appNowIso()), (p.by = vbWho());
      try {
        nyhMarkCopies(c, p, did);
      } catch (e) {}
      (c.proposals || []).every((z) => z.applied || !1 === z.on) && (c.status = "applied");
      try {
        audit("comm", c.id, "apply-bill", "", did, "");
      } catch (e) {}
    },
  );
}
function vbReview(pre, after) {
  const x = Object.assign({}, pre),
    jobs = (DB.projects || []).filter((p) => !p.archived),
    jobOpts = (sel) => `<option value="">Overhead (no job)</option>${jobs.map((p) => `<option value="${p.id}" ${p.id === sel ? "selected" : ""}>${esc(p.project.name)}</option>`).join("")}`,
    codeOpts = (sel) => `<option value="">Choose…</option>${COST_CODES.map(([k, n]) => `<option value="${k}" ${k === sel ? "selected" : ""}>${k} ${esc(n)}</option>`).join("")}`,
    lineOpts = (pid, sel) => `<option value="">No estimate line</option>${(pid ? lineOptions(pid) : []).map((o) => `<option value="${esc(o.key)}" ${o.key === sel ? "selected" : ""}>${esc(o.label)}</option>`).join("")}`,
    pos = (DB.pos || []).filter((po) => vbSameVendor(po.vendor, x.vendor) && !["draft", "cancelled", "void"].includes(po.status)),
    poOpts = (sel) => `<option value="">No purchase order</option>${pos.map((po) => `<option value="${po.id}" ${po.id === sel ? "selected" : ""}>${esc(po.number)} · ${money(poTotal(po).total)}</option>`).join("")}`,
    bankOpts = (sel) => {
      const C = vbBankCands(x.vendor, x.amount, x.txnId);
      return `<option value="">Not paid yet</option>${C.map((t) => `<option value="${t.id}" ${t.id === sel ? "selected" : ""}>${fmtL(t.date)} · ${esc(t.desc)} · ${money(-t.amt)} · ${esc(truthAcctWords(t))}</option>`).join("")}`;
    };
  const m = mbModal(
    `Enter the Bill: ${esc(x.vendor)}${x.number ? " " + esc(x.number) : ""}`,
    `<p class="small muted" style="margin:0 0 10px">Read from the vendor's invoice. Check each field; nothing is entered until you press Enter the Bill.</p>
    <div id="vb-warn"></div>
    <div class="grid2">${mbF("Vendor", `<input data-f="vendor" value="${esc(x.vendor)}" list="vb-vendors" autocomplete="off"><datalist id="vb-vendors">${(DB.vendors || []).map((v) => `<option value="${esc(v.name)}">`).join("")}</datalist>`)}${mbF("Invoice #", `<input data-f="number" value="${esc(x.number)}" autocomplete="off">`)}</div>
    <div class="grid2">${mbF("Invoice Date", `<input type="date" data-f="date" value="${esc(x.date)}">`)}${mbF("Due", `<input type="date" data-f="due" value="${esc(x.due)}">`)}</div>
    <div class="grid2">${mbF("Amount", `<input type="number" step="0.01" min="0" data-f="amount" value="${x.amount}">`)}${mbF("Job", `<select data-f="projectId">${jobOpts(x.projectId)}</select>`)}</div>
    <div class="grid2">${mbF("Cost Code", `<select data-f="code">${codeOpts(x.code)}</select>`)}${mbF("Estimate Line", `<select data-f="line">${lineOpts(x.projectId, x.line)}</select>`)}</div>
    <div class="grid2">${mbF("Purchase Order", `<select data-f="poId">${poOpts(x.poId)}</select>`)}${mbF("Paid by Bank Line", `<select data-f="txnId">${bankOpts(x.txnId)}</select>`)}</div>
    <div class="small muted" id="vb-route" style="margin-top:6px"></div>`,
    { submit: "Enter the Bill", onSubmit: (f) => vbPost(x, f, m, after) },
  );
  if (!m) return "";
  const val = (k) => (m.querySelector(`[data-f="${k}"]`) || {}).value || "",
    paint = () => {
      const amt = r2(+val("amount") || 0),
        t = val("txnId") && (DB.txns || []).find((y) => y.id === val("txnId")),
        hit = vbFind({ vendor: val("vendor"), number: val("number"), amount: amt, date: val("date"), txnId: val("txnId"), poId: val("poId") }),
        sib = val("poId") && vbPoSiblings(val("poId"), { commId: x.commId, amount: amt, number: val("number") }),
        W = m.querySelector("#vb-warn"),
        ok = m.querySelector("#mbm-ok");
      W.innerHTML = `${hit ? `<div class="note ${hit.exact ? "bad" : "warn"} small" style="margin-bottom:8px"><b>${hit.exact ? "Already on file" : "Possible duplicate"}:</b> ${esc(hit.why)}. ${hit.exact ? (vbPlaceholder(hit.bill) ? `It was entered from the payment; this invoice is that bill, so its number goes on it.` : "Entering it again would count the cost twice.") : "Say it is a different invoice to enter it."} <button type="button" class="btn sm" data-vbopen>Open ${esc(hit.bill.number || "the Bill")}</button></div>` : ""}${sib && sib.others.length ? `<div class="note warn small" style="margin-bottom:8px">${esc(sib.words)}</div>` : ""}`;
      const ob = W.querySelector("[data-vbopen]");
      ob && (ob.onclick = () => (mbCloseModal(), flowGo.bill(hit.bill)()));
      ok && (ok.textContent = hit && hit.exact ? (vbPlaceholder(hit.bill) ? `Put ${val("number") || "the Number"} on ${hit.bill.number}` : `Open ${hit.bill.number || "the Bill"}`) : hit ? "It Is a Different Invoice: Enter It" : "Enter the Bill");
      m.querySelector("#vb-route").textContent = `${t ? `Paid ${fmtL(t.date)} from ${truthAcctWords(t)} before anyone approved it: it waits under Paid Before Approval for ` : "It waits in Bills & Payroll for "}${vbRouteWords(amt)}. Whoever enters a bill cannot approve it.`;
    };
  m.addEventListener("input", paint);
  m.addEventListener("change", (e) => {
    const k = e.target && e.target.dataset && e.target.dataset.f;
    if ("projectId" === k) m.querySelector('[data-f="line"]').innerHTML = lineOpts(val("projectId"), vbLineFor(val("projectId"), val("code")));
    if ("code" === k && !val("line")) m.querySelector('[data-f="line"]').innerHTML = lineOpts(val("projectId"), vbLineFor(val("projectId"), val("code")));
    if ("poId" === k && val("poId")) {
      const po = (DB.pos || []).find((y) => y.id === val("poId")),
        l = po && (po.lines || [])[0];
      po && po.projectId && (m.querySelector('[data-f="projectId"]').value = po.projectId);
      l && l.code && (m.querySelector('[data-f="code"]').value = l.code);
      po && (m.querySelector('[data-f="line"]').innerHTML = lineOpts(po.projectId || val("projectId"), (l && l.line) || ""));
    }
    paint();
  });
  paint();
  return "Check the bill, then Enter the Bill: nothing is entered until you do";
}
function vbPost(x, f, m, after) {
  const vendor = String(f.vendor || "").trim(),
    v = "function" == typeof vendorRec ? vendorRec(vendor) : null,
    amt = r2(+f.amount || 0);
  if (!vendor || !v) return toast(`${vendor || "The vendor"} is not a vendor on file: pick one from the list`), !1;
  if (!(amt > 0)) return toast("Say the amount the invoice asks for"), !1;
  const hit = vbFind({ vendor: v.name, number: f.number, amount: amt, date: f.date, txnId: f.txnId, poId: f.poId || "" });
  // the invoice for a bill entered from its payment: the number and the mail go on that bill
  if (hit && hit.exact && vbPlaceholder(hit.bill)) {
    const b = hit.bill,
      was = b.number;
    (b.number = f.number || b.number), (b.commId = x.commId || b.commId || ""), (b.date = f.date || b.date), (b.notes = `${b.notes ? b.notes + " · " : ""}vendor invoice ${f.number} received ${fmtL(today())}; it is this bill (was ${was})`);
    try {
      audit("bill", b.id, "invoice-received", was, b.number, `${vbWho()}: the vendor's invoice for the payment`);
    } catch (e) {}
    const did = `${b.number} put on the bill entered from the payment (${was}); no second bill`;
    after && after(b, did), save(), mbCloseModal(), render();
    return rcToast(`${did}: ${money(billTotal(b))}, ${billState(b).text}`, [{ label: "Open", run: flowGo.bill(b) }]), !1;
  }
  if (hit && hit.exact) return mbCloseModal(), toast(`${hit.why}: nothing entered`), flowGo.bill(hit.bill)(), !1;
  const ack = hit ? `${vbWho()} said it is a different invoice in the review` : "",
    pid = f.projectId || "",
    po = f.poId && (DB.pos || []).find((y) => y.id === f.poId),
    t = f.txnId && (DB.txns || []).find((y) => y.id === f.txnId),
    by = vbWho(),
    b = {
      id: uid("b"),
      vendor: v.name,
      number: String(f.number || "").trim(),
      date: f.date || today(),
      due: f.due || iso(addDays(f.date || today(), 30)),
      entityId: x.entityId || ("function" == typeof entDefault ? entDefault() : "ent1"),
      projectId: pid,
      poId: "",
      cat: pid ? (isSub(v) ? "subs" : "materials") : "office",
      code: f.code || "",
      line: f.line || "",
      lines: [{ id: uid("bl"), desc: x.desc || `Invoice ${f.number || ""}`.trim(), amount: amt, code: f.code || "", line: f.line || "" }],
      payMethod: t ? (payFromBank(t).method || "ACH") : v.payMethod || "ACH",
      fileId: "",
      notes: `Entered from the vendor's invoice${x.src === "mail" ? " in mail" : ""}, checked by ${by}`,
      status: "submitted",
      approvals: [{ t: nowStamp(), ts: appNowIso(), by: by, role: role(), action: "entered from the vendor's invoice after review" }],
      // the mail reader entered it and the person checked it, as before: separation of duties is between the one who
      // enters and the one who approves, and approving stays with the PM and the Owner
      createdBy: "mail" === x.src ? "reader" : by,
      checkedBy: by,
      createdAt: appNowIso(),
      commId: x.commId || "",
    };
  po && (poLinkBill(b, po), f.code && ((b.code = f.code), (b.lines[0].code = f.code)), f.line && ((b.line = f.line), (b.lines[0].line = f.line)), pid && (b.projectId = pid));
  hit && (b.dupOf = { billId: hit.bill.id, number: hit.bill.number || "", why: hit.why, at: appNowIso(), by: by, ack: !0 });
  "function" == typeof billLinesNorm && billLinesNorm(b);
  const kept = vbAdd(b, { src: "the bill review", allowDup: !!hit });
  if (kept !== b) return mbCloseModal(), toast(`${vbAdd.last ? vbAdd.last.why : "It is on file"}: nothing entered`), flowGo.bill(kept)(), !1;
  try {
    audit("bill", b.id, "entered-after-review", "", `${b.vendor} ${b.number} ${money(amt)}`, ack || by);
  } catch (e) {}
  let paid = "";
  if (t) {
    const r = truthSetMatch(t, { billId: b.id }, { why: `the payment the invoice names, confirmed by ${by} in the review`, earlyWhy: `the vendor's invoice ${b.number} names this payment; ${by} confirmed it in the review` });
    r && r.ok ? (paid = ` · paid ${fmtL(t.date)} from ${truthAcctWords(t)} before approval`) : toast((r && r.why) || "The bank line was not linked");
  }
  const did = `bill ${b.number || ""} entered after review`.replace(/\s+/g, " ");
  after && after(b, did);
  save(), mbCloseModal(), render();
  rcToast(`Bill ${b.number || ""} entered: ${money(billTotal(b))} to ${b.vendor}${paid}. It waits ${paid ? "under Paid Before Approval" : "in Bills & Payroll"} for ${vbRouteWords(billTotal(b))}`, [{ label: "Open", run: flowGo.bill(b) }]);
  return !1;
}

// ---- 3. client money: recorded only against a bank line ---------------------------------------------------------------
// The unmatched deposits a client's money could be: money in, to a bank account, not yet linked to an invoice
function vbDepositCands(cl, amount) {
  const named = (t) => truthVendorHit(t, cl.name) || (cl.contacts || []).some((k) => k && k.name && truthVendorHit(t, String(k.name).split(" ").slice(-1)[0]));
  return (DB.txns || [])
    .filter((t) => +t.amt > 0 && lnIsBank(t.acct) && !lnMatched(t) && !["transfer", "cc-payment", "loan", "owner"].includes(t.cat) && !(DB.clients || []).some((c) => (c.payments || []).some((py) => py.txnId === t.id)))
    .map((t) => ({ t: t, named: named(t), same: amount ? Math.abs(+t.amt - +amount) < 0.01 : !1 }))
    .filter((x) => x.named || x.same)
    .sort((a, b) => b.named + b.same - (a.named + a.same) || String(b.t.date).localeCompare(String(a.t.date)))
    .map((x) => x.t);
}
let vbDepFrom = null;
// "Jessop family says the money is sent: Apply". The claim is linked to the bank line when the line is there (Record
// Payment opens on it, at the bank's amount, and records nothing until Record); otherwise it is an expectation, never
// a payment: it waits on Billing > Payments as expected money, and the deposit row comes to Today when the line lands.
function vbDepositApply(c, p) {
  const cl = (DB.clients || []).find((x) => x.id === p.clientId);
  if (!cl) return "";
  const amt = r2(+p.amount || 0),
    said = String(c.date || today()).slice(0, 10),
    cand = vbDepositCands(cl, amt).filter((t) => !amt || Math.abs(+t.amt - amt) < 0.01);
  DB.expected = DB.expected || [];
  let e = DB.expected.find((x) => x.commId === c.id);
  e || ((e = { id: uid("ex"), amount: amt, clientId: cl.id, from: (c.from && (c.from.name || c.from.email)) || "", said: said, commId: c.id, by: vbWho(), at: appNowIso(), followUp: iso(addWork(said, 5, !1)) }), DB.expected.push(e));
  if (cand.length && !window.__cmBulk) {
    const t = cand[0],
      open = (clientFin(cl).open || []).sort((a, b) => String(a.x.due || a.x.date).localeCompare(String(b.x.due || b.x.date)))[0];
    vbDepFrom = { c: c, p: p, e: e, txnId: t.id };
    setTimeout(() => paymentAllocate(cl, open ? open.x.id : ""), 0);
    return `the bank has it: ${money(+t.amt)} ${t.desc} on ${fmtL(t.date)}. Record Payment is open on that line; nothing is recorded until you press Record`;
  }
  return `expected, not cash: ${money(amt)} from ${cl.name} waits on Billing > Payments until a bank line shows it (nothing recorded; follow up ${fmtL(e.followUp)} if it has not landed)`;
}
// One row for one deposit on Today: when the bank line for a client's "money is sent" is in, the bank line's Record
// Payment row is the row (it carries what the client said), and the mail's Apply row goes.
{
  const base = nyhRowsAll;
  nyhRowsAll = function () {
    const out = base.apply(this, arguments);
    try {
      const deps = out.filter((r) => "deposit" === r.kind && /^dep:/.test(r.key));
      if (!deps.length) return out;
      const D = nyhDeposits();
      for (let i = out.length - 1; i >= 0; i--) {
        const r = out[i];
        if ("mail" !== r.kind || "deposit" !== r.pkind || !r.commId) continue;
        const c = (DB.comms || []).find((x) => x.id === r.commId),
          pr = c && (c.proposals || []).find((x) => "deposit" === x.kind && !x.applied);
        if (!pr) continue;
        const hit = D.find((d) => d.c.id === pr.clientId && Math.abs(+d.t.amt - +pr.amount) < 0.01),
          row = hit && deps.find((x) => x.key === "dep:" + hit.t.id);
        if (!row) continue;
        row.why = `${row.why} · ${(c.from && c.from.name) || hit.c.name} said it was sent ${fmtL(String(c.date || "").slice(0, 10))}`;
        out.splice(i, 1);
      }
    } catch (e) {
      console.warn("one deposit row", e);
    }
    return out;
  };
}
// Record Payment carries the bank line: the amount is the bank's, never the invoice's, and the line is matched when the
// payment is recorded, so it leaves Needs Category and the cash is counted once. A wire, ACH or Zelle is recorded only
// from its bank line; a check in hand may wait for the deposit.
{
  const base = paymentAllocate;
  paymentAllocate = function (c, presetInvoiceId) {
    const from = vbDepFrom;
    vbDepFrom = null;
    const r = base.apply(this, arguments);
    try {
      vbPayBankField(c, presetInvoiceId, from);
    } catch (e) {
      console.warn("record payment bank line", e);
    }
    return r;
  };
}
function vbPayBankField(c, presetInvoiceId, from) {
  const m = document.getElementById("mbm");
  if (!m || !m.querySelector("#py-amt")) return;
  const C = vbDepositCands(c, 0),
    pre = (from && from.txnId) || (C[0] && C[0].id) || "",
    row = document.createElement("div");
  (row.className = "f2"),
    (row.innerHTML = `<label class="f"><span>Bank Line</span><select id="py-txn" data-f="txn"><option value="">None: not in the bank yet</option>${C.map((t) => `<option value="${t.id}" ${t.id === pre ? "selected" : ""}>${fmtL(t.date)} · ${esc(t.desc)} · ${money(+t.amt)} · ${esc(truthAcctWords(t))}</option>`).join("")}</select></label><span class="small muted" id="py-txn-note" style="align-self:end"></span>`);
  const first = m.querySelector(".mbm-bd .f2");
  first ? first.before(row) : m.querySelector(".mbm-bd").prepend(row);
  const sel = row.querySelector("#py-txn"),
    note = row.querySelector("#py-txn-note"),
    put = (q, v) => {
      const el = m.querySelector(q);
      el && null != v && v !== "" && (el.value = v);
    },
    apply = () => {
      const t = (DB.txns || []).find((x) => x.id === sel.value);
      if (!t) return void (note.textContent = "Without a bank line a wire, ACH or Zelle is not recorded; a check waits as money not yet deposited.");
      const amt = r2(+t.amt),
        fb = payFromBank(t);
      put("#py-amt", amt), put("#py-date", t.date), put("#py-method", fb.method), put("#py-ref", fb.ref || t.desc), put("#py-acct", t.acct);
      // the bank's amount goes on the invoice it was sent for (or the oldest first), never the invoice's whole balance
      let left = amt;
      const ins = [...m.querySelectorAll("[data-pyalloc]")],
        order = presetInvoiceId ? ins.sort((a, b) => (b.dataset.pyalloc === presetInvoiceId) - (a.dataset.pyalloc === presetInvoiceId)) : ins;
      order.forEach((i) => {
        const v = Math.min(+i.max || 0, Math.max(0, left));
        (i.value = r2(v)), (left = r2(left - v));
      });
      m.querySelectorAll("[data-pyalloc], #py-amt").forEach((i) => i.dispatchEvent(new Event("input", { bubbles: !0 })));
      note.textContent = `${money(amt)} from the bank line; it is matched when you press Record.`;
    };
  sel.addEventListener("change", apply);
  pre && apply();
  const ok = m.querySelector("#mbm-ok");
  if (!ok) return;
  let before = null;
  ok.addEventListener(
    "click",
    (ev) => {
      const t = (DB.txns || []).find((x) => x.id === sel.value),
        method = (m.querySelector("#py-method") || {}).value || "",
        amt = r2(+(m.querySelector("#py-amt") || {}).value || 0);
      before = null;
      if (!t && /^(Wire|ACH|Zelle)$/i.test(method)) return ev.stopImmediatePropagation(), ev.preventDefault(), void toast(`A ${method.toLowerCase()} is recorded from its bank line: pick it, or record it when it lands`);
      if (t && amt > r2(+t.amt) + 0.005) return ev.stopImmediatePropagation(), ev.preventDefault(), void toast(`The bank line holds ${money(+t.amt)}: record that, not ${money(amt)}`);
      t && (before = { t: t, ids: new Set((c.payments || []).map((p) => p.id)) });
    },
    !0,
  );
  ok.addEventListener("click", () => {
    if (!before) return;
    const { t: t, ids: ids } = before,
      made = (c.payments || []).filter((p) => !ids.has(p.id));
    before = null;
    if (!made.length) return;
    made.forEach((p) => ((p.txnId = t.id), (p.acctId = t.acct)));
    const first = made.find((p) => p.invoiceId) || made[0],
      r = first.invoiceId ? truthSetMatch(t, { invoiceId: first.invoiceId, paymentId: first.id }, { why: "recorded on Record Payment from its bank line" }) : null;
    if (!first.invoiceId) {
      (t.cat && "uncat" !== t.cat) || (t.cat = "income"), "reconciled" !== t.status && (t.status = "categorized"), (t.match = Object.assign({}, t.match || {}, { clientId: c.id, paymentId: first.id })), (t.proposal = null);
    }
    vbClaimAnswered(c, t, first.id);
    const inv = first.invoiceId && (c.invoices || []).find((i) => i.id === first.invoiceId),
      bal = inv ? r2(docTotal(inv).total - invoicePaid(c, inv)) : 0;
    try {
      audit("payment", first.id, "matched-on-record", "", t.id, `${c.name} ${money(+t.amt)} from ${t.desc}`);
    } catch (e) {}
    save(), render();
    rcToast(`${money(+t.amt)} recorded from ${c.name}${inv ? ` on ${inv.number}` : " on account"}, matched to the ${fmtL(t.date)} ${truthAcctWords(t)} line (${t.desc})${inv ? (bal > 0.005 ? `; ${money(bal)} still open` : "; paid in full") : ""}${r && !r.ok ? ` · ${r.why}` : ""}`, [{ label: "Open", run: inv ? flowGo.doc(c, "invoice", inv) : flowGo.client(c) }]);
  });
}
// the client's claim ("the money is sent") and its expectation are answered by the bank line that records it, on every
// path that records a deposit (Record Payment, Today's Record Payment row, Banking's match)
function vbClaimAnswered(c, t, paymentId) {
  if (!c || !t || !(+t.amt > 0)) return;
  (DB.expected || []).filter((e) => e.clientId === c.id && !e.txnId && Math.abs((+e.amount || 0) - +t.amt) < 0.01).forEach((e) => ((e.txnId = t.id), (e.matched = t.id), (e.paymentId = paymentId || "")));
  (DB.comms || []).forEach((cm) =>
    (cm.proposals || []).forEach((pr) => {
      "deposit" === pr.kind && pr.clientId === c.id && !pr.applied && Math.abs((+pr.amount || 0) - +t.amt) < 0.01 && ((pr.applied = `recorded from the ${fmtL(t.date)} bank line`), (pr.appliedAt = appNowIso()), (pr.by = vbWho()), (cm.proposals || []).every((z) => z.applied || !1 === z.on) && (cm.status = "applied"));
    }),
  );
}
{
  const base = truthSetMatch;
  truthSetMatch = function (t, m0) {
    const r = base.apply(this, arguments);
    try {
      if (r && r.ok && t && m0 && m0.invoiceId && +t.amt > 0) {
        const c = (DB.clients || []).find((x) => (x.invoices || []).some((i) => i.id === m0.invoiceId));
        c && vbClaimAnswered(c, t, (t.match || {}).paymentId);
      }
    } catch (e) {}
    return r;
  };
}
// Billing > Payments: the money clients say they sent that no bank line shows yet, one list, with its follow-up day
function vbExpectedRows() {
  return (DB.expected || [])
    .filter((e) => e && +e.amount > 0 && !e.txnId && !e.matched)
    .map((e) => ({ e: e, c: (DB.clients || []).find((x) => x.id === e.clientId) }))
    .filter((x) => x.c);
}
if ("function" == typeof renderBilling) {
  const base = renderBilling;
  renderBilling = function () {
    const r = base.apply(this, arguments);
    try {
      const v = document.getElementById("billing-body");
      if (v && "payments" === billTab && !docOpen && !v.querySelector("#vb-expected")) {
        const R = vbExpectedRows();
        if (R.length) {
          const d = document.createElement("div");
          (d.className = "card"), (d.id = "vb-expected");
          d.innerHTML = `<div class="hd"><h3>Expected, Not in the Bank</h3><span class="small muted">a client said it was sent; nothing is recorded until a bank line shows it</span></div><div class="tw"><table class="t"><thead><tr><th>Client</th><th class="money">Amount</th><th>Said</th><th>Follow Up</th></tr></thead><tbody>${R.map((x) => `<tr><td><b>${esc(x.c.name)}</b> <span class="small muted">${esc(x.e.from || "")}</span></td><td class="money">${money(+x.e.amount)}</td><td>${fmtL(x.e.said)}</td><td>${x.e.followUp ? fmtL(x.e.followUp) : ""}</td></tr>`).join("")}</tbody></table></div>`;
          const tabs = v.querySelector(".ctabs");
          tabs ? tabs.after(d) : v.prepend(d);
        }
      }
    } catch (e) {
      console.warn("expected money", e);
    }
    return r;
  };
}

// ---- 5. two invoices on one order ------------------------------------------------------------------------------------
// The invoices waiting on a PO: its live bills and the vendor invoices read from mail and not yet entered. Two inside
// fourteen days, or together more than the order holds, are flagged on each other, on the PO and in Approvals.
function vbPoSiblings(poId, self) {
  const po = (DB.pos || []).find((x) => x.id === poId);
  if (!po) return null;
  const s = self || {},
    all = [];
  (DB.bills || []).filter((b) => b.poId === po.id && vbLive(b) && !vbIsDeposit(b)).forEach((b) => all.push({ key: "bill:" + b.id, number: b.number || "", amount: billTotal(b), date: b.date || "", bill: b }));
  (DB.comms || []).forEach((c) =>
    (c.proposals || []).forEach((pr) => {
      if ("bill" !== pr.kind || pr.applied || !1 === pr.on || pr.poId !== po.id || !(+pr.amount > 0)) return;
      if (all.some((x) => vbNum(x.number) && vbNum(x.number) === vbNum(pr.number))) return;
      all.push({ key: "mail:" + c.id, number: pr.number || "", amount: r2(+pr.amount), date: String(c.date || "").slice(0, 10), commId: c.id });
    }),
  );
  const me = all.find((x) => (s.billId && x.key === "bill:" + s.billId) || (s.commId && x.key === "mail:" + s.commId)) || (s.amount ? { key: "self", number: s.number || "", amount: r2(+s.amount), date: s.date || today() } : null);
  if (!me) return { po: po, others: [], words: "" };
  const others = all.filter((x) => x.key !== me.key && (!me.date || !x.date || Math.abs(dayDiff(x.date, me.date)) <= 14)),
    tot = r2(poTotal(po).total),
    sum = r2(others.reduce((a, x) => a + x.amount, 0) + me.amount),
    over = r2(sum - tot);
  if (!others.length) return { po: po, others: [], words: "" };
  const list = [me, ...others].sort((a, b) => String(a.date).localeCompare(String(b.date)));
  return {
    po: po,
    others: others,
    sum: sum,
    over: over,
    words: `${list.length} invoices on ${po.number} within two weeks: ${list.map((x) => `${x.number || "no number"} ${money(x.amount)}${x.date ? " (" + fmtL(x.date) + ")" : ""}`).join(" and ")}, ${money(sum)} against a ${money(tot)} order${over > 0.5 ? `, ${money(over)} over` : ""}. Check they are not one delivery billed twice before either is entered or paid`,
  };
}
{
  const base = nyhRowsAll;
  nyhRowsAll = function () {
    const out = base.apply(this, arguments);
    try {
      out.forEach((r) => {
        if ("mail" !== r.kind || "bill" !== r.pkind || !r.commId) return;
        const c = (DB.comms || []).find((x) => x.id === r.commId),
          pr = c && (c.proposals || []).find((x) => "bill" === x.kind && !x.applied);
        if (!pr || !pr.poId) return;
        const S2 = vbPoSiblings(pr.poId, { commId: c.id });
        S2 && S2.others.length && ((r.why = `${S2.words} · ${r.why || ""}`), (r.flag = S2.words), (r.sev = "bad"));
      });
    } catch (e) {
      console.warn("po siblings", e);
    }
    return out;
  };
}
if ("function" == typeof renderPODoc) {
  const base = renderPODoc;
  renderPODoc = function (po) {
    let h = base.apply(this, arguments);
    try {
      const live = po ? (DB.bills || []).filter((b) => b.poId === po.id && vbLive(b) && !vbIsDeposit(b)) : [],
        mail = [];
      po && (DB.comms || []).forEach((c) => (c.proposals || []).forEach((pr) => "bill" === pr.kind && !pr.applied && !1 !== pr.on && pr.poId === po.id && +pr.amount > 0 && mail.push({ c: c, pr: pr })));
      const first = live[0] ? { billId: live[0].id } : mail[0] ? { commId: mail[0].c.id } : null,
        S2 = first && vbPoSiblings(po.id, first);
      S2 && S2.others.length && (h = `<div class="note bad small no-doc-print vb-posib" style="margin-bottom:10px">${esc(S2.words)}.</div>` + h);
    } catch (e) {}
    return h;
  };
}

// ---- 6. a grid's subline is its own words -------------------------------------------------------------------------
// "Payroll · 8/31 – 9/4" and "6 employees" sat side by side with only a margin between them, so the line read (and
// copied, and was read aloud) as "9/46 employees". The data grid puts a space before every inline subline.
function dgSubSep(h) {
  return String(h).replace(/([^\s>])(<span class="sub")/g, "$1 $2");
}

// ---- 7. billed ahead of the work, line by line ------------------------------------------------------------------------
// The progress grid knew: each line's billed % beside its complete % (pgRows). Outside the grid nothing said it: a line
// billed at the same % as its neighbours ("lump billed", 51.67% on thirteen lines) was even left out of the grid's own
// over-billed finding. A line is billed ahead when its billed % runs more than the firm's tolerance (pgCfg().ahead,
// 5 points) past its measured complete %; on a contract line the deposit credited across the lines is not counted
// (the client paid it up front, by contract). The same rows give the line, the total and the dollar amount on the pay
// application, the Billing Queue row and Today (Caught for You).
let pbCache = null;
function pbAhead(pid) {
  if (!pbCache) {
    pbCache = {};
    try {
      setTimeout(() => (pbCache = null), 0);
    } catch (e) {}
  }
  if (pid in pbCache) return pbCache[pid];
  const p = (DB.projects || []).find((x) => x.id === pid),
    c = p && (DB.clients || []).find((x) => x.id === p.clientId),
    out = { pid: pid, lines: [], total: 0, depPct: 0, depAmt: 0 };
  if (!p || !c) return (pbCache[pid] = out);
  let rows = [];
  try {
    rows = pgRows(pid) || [];
  } catch (e) {}
  const cfg = "function" == typeof pgCfg ? pgCfg() : { ahead: 5 },
    dep = (() => {
      try {
        return +tpCertified(c, pid).depPct || 0;
      } catch (e) {
        return 0;
      }
    })();
  out.depPct = dep;
  rows.forEach((r) => {
    if (!r.pr || null == r.pr.pct || r.pr.stale || !["schedule", "delivered"].includes(r.pr.basis)) return;
    const co = pgIsCO(r.sv),
      billed = r2(r.ev.billedPct),
      pct = r2(r.pr.pct),
      pts = r2(billed - pct),
      depPts = co ? 0 : r2(Math.min(dep, Math.max(0, pts))),
      net = r2(pts - depPts);
    if (!(net > (cfg.ahead || 5))) return;
    const sched = +r.ev.scheduled || 0,
      amount = r2((sched * net) / 100);
    out.lines.push({ svId: r.sv.id, item: r.sv.desc || r.sv.item || "", source: r.sv.source || "Contract", billed: billed, pct: pct, net: net, depPts: depPts, scheduled: sched, amount: amount, depAmt: r2((sched * depPts) / 100) });
  });
  out.total = r2(out.lines.reduce((a, l) => a + l.amount, 0));
  out.depAmt = r2(out.lines.reduce((a, l) => a + l.depAmt, 0));
  return (pbCache[pid] = out);
}
const pbWords = (A) =>
  A.lines.length
    ? `${money(A.total)} billed ahead of the work on ${A.lines.length} line${1 === A.lines.length ? "" : "s"} (${A.lines
        .slice(0, 3)
        .map((l) => `${l.item} ${l.billed}% billed, ${l.pct}% complete`)
        .join("; ")}${A.lines.length > 3 ? "; …" : ""})${A.depPct ? `, not counting the ${A.depPct}% deposit` : ""}`
    : "";
// the pay application: a line under each line billed ahead, and the total on top; internal, never printed
{
  const base = renderDocEditor;
  renderDocEditor = function (c, d) {
    let h = base.apply(this, arguments);
    try {
      if (!d || "invoice" !== d.type || "sov" !== d.mode || "void" === d.status || !d.projectId) return h;
      const A = pbAhead(d.projectId);
      if (!A.lines.length) return h;
      A.lines.forEach((l) => {
        const dl = (d.lines || []).find((x) => x.sovId === l.svId);
        if (!dl) return;
        const a = h.indexOf(`<tr data-line="${dl.id}">`);
        if (a < 0) return;
        const b = h.indexOf("</tr>", a);
        b > -1 && (h = h.slice(0, b + 5) + `<tr class="pb-ahead no-doc-print"><td></td><td colspan="9"><span class="small bad-t" data-nocase>Billed ahead: ${esc(l.item)} is ${l.billed}% billed against ${l.pct}% complete${l.depPts ? ` (${l.depPts} points are the deposit)` : ""}, ${money(l.amount)} ahead of the work</span></td></tr>` + h.slice(b + 5));
      });
      h = `<div class="note bad small no-doc-print pb-ahead-total" id="pb-ahead-total"><b>Billed ahead of the work: ${money(A.total)}</b> on ${A.lines.length} line${1 === A.lines.length ? "" : "s"}${A.depPct ? `, not counting the ${A.depPct}% deposit credited across the lines` : ""}. Nothing is changed; billing any of these lines further needs a reason.${d.aheadWhy ? ` Sent further ahead by ${esc(d.aheadWhy.by)}: ${esc(d.aheadWhy.why)}` : ""}</div>` + h;
    } catch (e) {
      console.warn("billed ahead lines", e);
    }
    return h;
  };
}
// billing a line further ahead of its work needs a reason, recorded on the invoice and in the audit
function pbFurther(c, d) {
  if (!d || "invoice" !== d.type || "sov" !== d.mode || !d.projectId) return [];
  const A = pbAhead(d.projectId),
    rows = (() => {
      try {
        return pgRows(d.projectId) || [];
      } catch (e) {
        return [];
      }
    })(),
    cfg = "function" == typeof pgCfg ? pgCfg() : { ahead: 5 };
  return (d.lines || [])
    .filter((l) => l.sovId && +l.pct > 0)
    .map((l) => {
      const r = rows.find((x) => x.sv && x.sv.id === l.sovId);
      if (!r || !r.pr || null == r.pr.pct || r.pr.stale || !["schedule", "delivered"].includes(r.pr.basis)) return null;
      const prev = r2("draft" === d.status ? sovBilled(c, l.sovId, d.id) : +l.prevPct || 0),
        to = r2(prev + (+l.pct || 0)),
        dep = pgIsCO(r.sv) ? 0 : A.depPct,
        net = r2(to - r.pr.pct - Math.min(dep, Math.max(0, to - r.pr.pct)));
      return net > (cfg.ahead || 5) ? { l: l, to: to, pct: r2(r.pr.pct), amount: r2(((+l.scheduled || r.ev.scheduled || 0) * (+l.pct || 0)) / 100) } : null;
    })
    .filter(Boolean);
}
{
  const base = docAction;
  docAction = async function (c, d, a) {
    try {
      if (["send", "sent", "approve", "sendclient"].includes(a) && d && !d.aheadWhy) {
        const F = pbFurther(c, d);
        if (F.length)
          return void billAskWhy(
            `Billed Ahead of the Work: ${esc(d.number || "")}`,
            `${F.map((x) => `${esc(x.l.item)}: ${x.to}% billed to date against ${x.pct}% complete`).join("<br>")}<br>Say why these lines bill further ahead of the work. Nothing is changed in what is billed; the reason goes on the invoice's record.`,
            "Send With the Reason",
            "e.g. the contract bills the windows on delivery to the shop",
            (w) => {
              (d.aheadWhy = { why: w, by: vbWho(), at: appNowIso(), lines: F.map((x) => x.l.item) }), save();
              try {
                audit("invoice", d.id, "billed-ahead", "", F.map((x) => `${x.l.item} ${x.to}%`).join("; "), `${vbWho()}: ${w}`);
              } catch (e) {}
              // after this sheet closes, so the send's own sheet is not closed with it
              setTimeout(() => docAction(c, d, a), 0);
            },
          );
      }
    } catch (e) {
      console.warn("billed ahead gate", e);
    }
    return base.apply(this, arguments);
  };
}
// the Billing Queue row carries it
if ("function" == typeof billingRows) {
  const base = billingRows;
  billingRows = function () {
    const R = base.apply(this, arguments) || [];
    try {
      R.forEach((r) => {
        const pid = (r.job && r.job.id) || (r.inv && r.inv.projectId);
        if (!pid || r.ahead || !(r.inv ? "sov" === r.inv.mode : ["progress", "held", "ready"].includes(r.kind) || /application|line/i.test(r.what || ""))) return;
        const A = pbAhead(pid);
        A.lines.length && ((r.ahead = { n: A.lines.length, amount: A.total }), (r.why = `${r.why ? r.why + " · " : ""}billed ahead of the work: ${money(A.total)} on ${A.lines.length} line${1 === A.lines.length ? "" : "s"}`));
      });
    } catch (e) {}
    return R;
  };
}
// Today (Caught for You) for the PM and billing: one row per job, the line-by-line amount. It takes the place of the
// job's "billed ahead of the site" row, so the job reads one number about billing ahead.
{
  const K = (typeof CATCH !== "undefined" ? CATCH : []).find((k) => k.name === "portalBilledAhead");
  if (K) {
    const base = K.rows;
    K.rows = function () {
      const R = base.apply(this, arguments) || [];
      try {
        if (!["pm", "billing"].includes(role())) return R;
        const jobs = (DB.projects || []).filter((p) => !p.archived && "closed" !== (p.project || {}).status && p.clientId);
        jobs.forEach((p) => {
          const A = pbAhead(p.id);
          if (!A.lines.length) return;
          const i = R.findIndex((x) => x.key === "ahead:" + p.id),
            row = {
              key: "ahead:" + p.id,
              what: `Billed ahead: ${tdJob(p)}, ${A.lines.length} line${1 === A.lines.length ? "" : "s"}`,
              sub: `${pbWords(A)} · billing these lines further needs a reason`,
              amount: A.total,
              verb: "Review",
              run: () => (setCurrent(p.id), setView("billing")),
            };
          i >= 0 ? (R[i] = row) : R.push(row);
        });
      } catch (e) {
        console.warn("billed ahead catch", e);
      }
      return R;
    };
  }
}
// It leads the PM's Caught for You: it is his to see before the client asks, and the four shown above the fold were
// other detectors' turns (tdCaught takes each detector's biggest in turn). The approved Today (2026-10-25) keeps
// Caught for You behind the quiet line, so it reaches him as the update's "Billed ahead" fact (src/today2.js).
// Billing holds it as a row of her own Today (Needs Your Hand, below), so her Caught for You does not say it twice.
if ("function" == typeof tdCaught) {
  const base = tdCaught;
  tdCaught = function () {
    const out = base.apply(this, arguments) || [];
    try {
      const lead = out.filter((x) => "portalBilledAhead" === x.src && /^Billed ahead: /.test(x.what || ""));
      if ("billing" === role()) return out.filter((x) => !lead.includes(x));
      if ("pm" === role()) return lead.concat(out.filter((x) => !lead.includes(x)));
    } catch (e) {}
    return out;
  };
}
// Billing's Today: one row per job billed ahead of the work, with the dollar amount, her Review before the next
// application goes out. It was a Caught for You row only, and the approved Today keeps Caught for You behind the
// quiet line, so billing's first screen never said it (p2money_test 7). Billing ahead is an integrity question (an
// invoice says what was done; the client sees both numbers), so it ranks with the Standard's integrity items.
if ("function" == typeof nyhRowsAll) {
  const base = nyhRowsAll;
  nyhRowsAll = function () {
    const out = base.apply(this, arguments) || [];
    try {
      (DB.projects || [])
        .filter((p) => !p.archived && "closed" !== (p.project || {}).status && p.clientId)
        .forEach((p) => {
          const A = pbAhead(p.id),
            key = "ahead:" + p.id;
          if (!A.lines.length || !(A.total > 0) || out.some((x) => x.key === key)) return;
          const n = A.lines.length;
          out.push({
            key: key,
            route: "billing",
            kind: "ahead",
            projectId: p.id,
            title: `Billed ahead: ${tdJob(p)}, ${money(A.total)} on ${n} line${1 === n ? "" : "s"}`,
            why: `${pbWords(A)} · billing these lines further needs a reason`,
            amount: A.total,
            verb: "Review",
            no: "",
            run: () => (setCurrent(p.id), setView("billing")),
            open: () => (setCurrent(p.id), setView("billing")),
          });
        });
    } catch (e) {
      console.warn("billed ahead row", e);
    }
    return out;
  };
}
if ("undefined" != typeof STD_MAP)
  Object.assign(STD_MAP, {
    portalBilledAhead: { p: "integrity", c: ["std", "money", /Invoices are accurate/i] },
    "nyh:ahead": { p: "integrity", c: ["std", "money", /Invoices are accurate/i] },
  });
// the client's own money ahead of the work is "money or a client waiting now" (standardMoneyNow), as a credit owed to
// them is: their portal shows the lines billed past what is done until billing holds or explains them
"undefined" != typeof STD_NOW_CLIENT && !STD_NOW_CLIENT.includes("ahead") && STD_NOW_CLIENT.push("ahead");
