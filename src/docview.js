/* ---------------------------------------------------------------------------------------------------------------------
   docview: open the document first (Alan, 11-06).
   "On the control and billing when you click an invoice, CO, estimate, etc - it should take you to a pdf and from the
   pdf, you should have options to edit, create credit, refund, etc."

   One open path, one viewer. Every list that opens an invoice, change order, estimate or credit memo sets docOpen (the
   Billing page, Accounting's Collections, the client's and the job's Contract and Billing, Today and Your Day, Cmd-K,
   Ask's links, toasts' Open). For billing and the controller (DV_ROLES) the outermost draw reads that request once
   (dvIntercept, inside render) and opens the document as its recipient reads it instead of the editor: the same
   render as Print (cxDocHtml in src/clientdocs.js), reflowed inline at any width, never a PDF in a frame. A bill
   (openBill) opens the same way for them. The viewer's action bar (dvActions) is decided by the record's type, its
   status and the person's role; it has one blue button (the safe next step), and money-out or destructive actions
   are never blue and sit under More.

   What it extends (BACKLOG §1.16, the design gate), never a second copy:
   - the document: cxDocHtml (one renderer; a credit memo is one more kind of it, "credit") and printDoc (Print);
   - the noun "invoice": a credit memo is an invoice in c.invoices (creditMemo, creditOf), applied to the one invoice
     it credits by two linked application records in c.payments (cmApply) that net to zero, so every balance path
     (invoicePaid, clientFin, invoiceStatus, aging, the portal) reads it with no change. No cash moves: an application
     is never bank evidence (payBankedAmt), never posts Undeposited Funds (glPaymentLines), and the memo posts its own
     reversal of revenue, sales tax and retainage (glInvoiceLinesLive);
   - the client-credit register DB.clientCredits (blCreditRows): each credit memo is registered there, approved;
   - the revision (lkRevise / lkSupersede): Edit on a sent or paid invoice is a linked void and re-issue with a reason;
     the original stays as sent until the re-issue goes out, then it is voided (its posting reversed) and its payments
     follow the re-issue;
   - the approval queue (mApprovals, DELEGATION): a refund is a proposal (c.refunds) the owner approves (Settings may
     name another approver: DB.company.refundApprover); approved, it posts as a negative payment tied to the payment it
     returns (refundOf), back to the account that paid, and reads "approved, not in the bank" until a bank line on
     that account is matched to it;
   - the audit trail (audit, apStamp, docAudit): every mutation names who, when and why.
   Suite: tests/docview_test.py. Journey check: tests/cycle_walk.py open_document (J8).
--------------------------------------------------------------------------------------------------------------------- */
const DV_ROLES = ["billing", "controller"],
  DV_CREDIT_ROLES = ["owner", "billing", "controller"],
  DV_LABEL = { estimate: "Estimate", co: "Change Order", invoice: "Invoice", credit: "Credit Memo", bill: "Bill" };
let dvCur = null, // { kind, id, cid }: the record open in the viewer
  dvEditing = null, // the document the person chose to edit: its editor draws as before
  dvMore = !1,
  dvBillEdit = null;
const dvFresh = new Set(); // documents made this turn (New Invoice, Draft, Duplicate, a revision): they open in the editor
const dvOn = () => DV_ROLES.includes(role());
const dvWho = () => (S && S.project && S.project.userName) || ((currentUser() || {}).name) || role();

// ---- finding a record ---------------------------------------------------------------------------------------------------
function dvFind(kind, id, cid) {
  if ("bill" === kind) {
    const b = (DB.bills || []).find((x) => x.id === id);
    return b ? { kind: kind, b: b } : null;
  }
  const K = "credit" === kind ? "invoice" : kind;
  for (const c of DB.clients || []) {
    if (cid && c.id !== cid) continue;
    const d = (docColl(c, K) || []).find((x) => x.id === id);
    if (d) return { kind: d.creditMemo ? "credit" : K, c: c, d: d };
  }
  return cid ? dvFind(kind, id, null) : null;
}
// what is still owed on an invoice
function dvBal(c, d) {
  return r2(docTotal(d).total - invoicePaid(c, d));
}
// the money the client paid on an invoice that a refund can return: payments the bank has, less what was refunded
// or is proposed against each
function dvRefundable(c, d) {
  return (c.payments || [])
    .filter((p) => p.invoiceId === d.id && +p.amount > 0 && !p.cmApply && !p.reverses && !p.reversalId && !p.refundOf)
    .map((p) => {
      const out = r2(
        (c.refunds || []).filter((f) => f.paymentId === p.id && !["declined", "void"].includes(f.status)).reduce((a, f) => a + (+f.amount || 0), 0),
      );
      return { p: p, banked: payBanked(c, p), left: r2(+p.amount - out) };
    })
    .filter((x) => x.left > 0.005);
}
function dvCreditsOn(c, d) {
  return (c.invoices || []).filter((x) => x.creditMemo && x.creditOf === d.id && "void" !== x.status);
}

// ---- the open path: every list sets docOpen; billing and the controller read the document first --------------------------
function dvOpen(kind, id, cid) {
  const r = dvFind(kind, id, cid);
  if (!r) return toast("That document is not on file");
  (dvCur = { kind: r.kind, id: id, cid: r.c ? r.c.id : "" }), (dvMore = !1);
  dvDraw();
}
function dvClose() {
  dvCur = null;
  dvMore = !1;
  const el = document.getElementById("dv");
  el && el.remove();
  document.body.classList.remove("dv-open");
}
function dvIntercept() {
  if ("undefined" == typeof docOpen || !docOpen) return void (dvEditing = null);
  const id = docOpen.id;
  if (id === dvEditing) return;
  if (dvFresh.has(id) || !dvOn()) return dvFresh.delete(id), void (dvEditing = id);
  const cid = clientOpen || "",
    r = dvFind(docOpen.kind, id, cid);
  if (!r) return void (dvEditing = id);
  // the page under the document stays the list the person came from; the document opens on top of it
  (docOpen = null), (dvEditing = null), (dvCur = { kind: r.kind, id: id, cid: r.c.id }), (dvMore = !1);
  // Billing's flag for a client opened from its list (setView("clients") then shows the list) is the editor's; with the
  // document on top instead, the next open of the same client's record (Cmd-K, a link) must land on it
  "undefined" != typeof blClientFlag && (blClientFlag = "");
}
function dvEdit(r) {
  // the editor, as it always opened
  dvClose();
  const k = "credit" === r.kind ? "invoice" : r.kind;
  dvEditing = r.d.id;
  "undefined" != typeof flowGo && flowGo.doc ? flowGo.doc(r.c, k, r.d)() : ((clientOpen = r.c.id), (docOpen = { kind: k, id: r.d.id }), render());
}
if ("function" == typeof newDoc) {
  const base = newDoc;
  newDoc = function () {
    const d = base.apply(this, arguments);
    try {
      d && d.id && dvFresh.add(d.id);
    } catch (e) {}
    return d;
  };
}
{
  const base = render;
  render = function () {
    try {
      dvIntercept();
    } catch (e) {
      console.warn("docview: open", e);
    }
    const r = base.apply(this, arguments);
    try {
      dvCur ? dvDraw() : document.getElementById("dv") && dvClose();
    } catch (e) {
      console.warn("docview: draw", e);
    }
    return r;
  };
}
// a bill opens as its document for billing and the controller; Edit opens the bill sheet as before
if ("function" == typeof openBill) {
  const base = openBill;
  openBill = function (id) {
    if (dvOn() && id && id !== dvBillEdit && (DB.bills || []).some((b) => b.id === id)) return dvOpen("bill", id);
    dvBillEdit = null;
    return base.apply(this, arguments);
  };
}
// the client's portal: the same document and the same viewer, with the client's own actions (Approve, How to Pay, Ask)
if ("function" == typeof portalView) {
  const base = portalView;
  portalView = function (c, k, d) {
    if ("client" !== role() || !c || !d || !CX_TYPES.includes(k)) return base.apply(this, arguments);
    dvCur = { kind: k, id: d.id, cid: c.id, portal: !0 };
    dvMore = !1;
    dvDraw();
  };
}

// ---- the document: the render the recipient reads (cxDocHtml), reflowed inline ---------------------------------------
"object" == typeof CX_LABEL && (CX_LABEL.credit = "Credit Memo");
"object" == typeof CX_FOOTERS && (CX_FOOTERS.credit = "This credit is applied to the invoice named above. Nothing more is owed on the amount credited.");
if ("function" == typeof cxKind) {
  const base = cxKind;
  cxKind = function (d) {
    return d && d.creditMemo ? "credit" : base.apply(this, arguments);
  };
}
// A credit memo is one more kind of the one client document: the letterhead, the lines credited (by their amount, an
// SOV line by its share of the work), the sales tax and retainage reversed, and what it is applied to.
if ("function" == typeof cxDocHtml) {
  const base = cxDocHtml;
  cxDocHtml = function (c, d, o) {
    if (!d || !d.creditMemo) return base.apply(this, arguments);
    o = o || {};
    const K = cxCo(d),
      re = cxStaffRe(c),
      t = docTotal(d),
      inv = (c.invoices || []).find((x) => x.id === d.creditOf),
      pr = cxProject(c, d),
      bt = "function" == typeof crBillTo ? crBillTo(c) : (c.contacts || [])[0] || {},
      amt = (v) => money(Math.abs(+v || 0)),
      rows = (d.lines || [])
        .map((l, i) => `<tr><td class="n">${i + 1}</td><td>${esc(cxClean(l.item, c, re))}${l.desc ? `<div class="ds">${esc(cxClean(l.desc, c, re))}</div>` : ""}</td><td class="r">${amt(lineAmount(l, d))}</td></tr>`)
        .join(""),
      ap = (c.payments || []).filter((p) => p.cmApply && p.creditMemoId === d.id && +p.amount > 0),
      onInv = r2(ap.filter((p) => !p.unapplied && p.invoiceId === (inv && inv.id)).reduce((a, p) => a + +p.amount, 0)),
      onAcct = r2(ap.filter((p) => p.unapplied).reduce((a, p) => a + +p.amount, 0)),
      left = inv ? dvBal(c, inv) : 0;
    return `<!doctype html><html><head><meta charset="utf-8"><title>${esc(d.number)} · ${esc(K.name)}</title><style>body{margin:36px;background:#fff}${CX_CSS}@media print{body{margin:.45in}}</style></head><body><div class="cxd" data-cxkind="credit">${"void" === d.status ? '<div class="cxd-draft">VOID</div>' : ""}
  ${cxLetterhead(d)}
  <div class="cxd-hd"><div class="cxd-kind">Credit Memo</div><div class="cxd-num sans"><b>${esc(d.number)}</b><br>Date: ${cxDate(d.date)}${inv ? `<br>Credits invoice ${esc(inv.number)}` : ""}</div></div>
  <div class="cxd-meta"><div><div class="cxd-k sans">Credit to</div><b>${esc(c.name)}</b><br>${esc(cxBillAddr(c, d))}${bt && bt.name ? `<br><span class="sans" style="font-size:11.5px">${esc(bt.name)}${bt.email ? " · " + esc(bt.email) : ""}</span>` : ""}</div><div><div class="cxd-k sans">Project</div><b>${esc(pr.name)}</b>${pr.addr ? `<br>${esc(pr.addr)}` : ""}</div></div>
  <table><thead><tr><th class="n">#</th><th>Credited</th><th class="r">Credit</th></tr></thead><tbody>${rows}</tbody></table>
  <div class="cxd-tot sans"><div><span>Subtotal credited</span><span>${amt(t.sub - t.disc)}</span></div>${t.tax ? `<div><span>Sales tax reversed (${+d.taxRate}%)</span><span>${amt(t.tax)}</span></div>` : ""}${t.ret ? `<div><span>Less retainage no longer held (${+d.retainagePct}%)</span><span>− ${amt(t.ret)}</span></div>` : ""}<div class="big"><span>Total credit</span><span>${amt(t.total)}</span></div></div>
  ${d.creditWhy ? `<div class="cxd-memo"><b>Reason</b>\n${esc(cxClean(d.creditWhy, c, re))}</div>` : ""}
  <div class="cxd-box sans cx-applied"><b>Applied</b><div style="margin-top:4px">${inv ? `${amt(onInv)} applied to invoice ${esc(inv.number)} of ${cxDate(inv.date)}. ${"void" === inv.status ? "" : left > 0.005 ? `${money(left)} is still due on it.` : `Nothing is due on ${esc(inv.number)} now.`}` : ""}${onAcct > 0.005 ? ` ${money(onAcct)} is held as a credit on your account for your next invoice or a refund.` : ""}</div></div>
  <div class="cxd-foot sans">${esc(K.footers.credit || "")}<br>${esc(K.legal)}${K.addr ? " · " + esc(K.addr) : ""}${K.phone ? " · " + esc(K.phone) : ""}</div>
  </div>${o.print === !1 ? "" : "<script>window.onload=()=>{window.print();}<\/script>"}</body></html>`;
  };
}
// a bill, for the office: the vendor's invoice as it is on file (the vendor's document itself opens from Vendor's
// Document), what it is for, and who has approved it
function dvBillHtml(b) {
  const p = (DB.projects || []).find((x) => x.id === b.projectId),
    po = b.poId && (DB.pos || []).find((x) => x.id === b.poId),
    ent = (DB.entities || []).find((e) => e.id === b.entityId) || (DB.entities || [])[0] || { name: (DB.company && DB.company.name) || "" },
    st = billState(b),
    gross = "function" == typeof billGross ? r2(billGross(b)) : billTotal(b),
    net = billTotal(b),
    file = dvBillFile(b);
  return `<div class="cxd" data-cxkind="bill"><div class="cxd-lh"><div><div class="cxd-word">${esc(b.vendor || "Vendor")}</div><div class="cxd-tag sans">Vendor bill on file</div></div><div class="cxd-firm sans">${file ? `The vendor's own invoice is attached: ${esc(file.name || "")}` : "No vendor document is attached; this is the bill as entered."}</div></div>
  <div class="cxd-hd"><div class="cxd-kind">Bill</div><div class="cxd-num sans"><b>${esc(b.number || "(no number)")}</b><br>Date: ${cxDate(b.date)}${b.due ? `<br>Due: ${cxDate(b.due)}` : ""}<br>${esc(st.text)}</div></div>
  <div class="cxd-meta"><div><div class="cxd-k sans">Billed to</div><b>${esc(ent.name || "")}</b></div><div><div class="cxd-k sans">Job</div><b>${esc(p ? p.project.name : "Office")}</b>${po ? `<br><span class="sans" style="font-size:11.5px">Purchase order ${esc(po.number)}</span>` : ""}</div></div>
  <table><thead><tr><th class="n">#</th><th>Item</th><th class="r">Amount</th></tr></thead><tbody>${(b.lines || [])
    .map((l, i) => `<tr><td class="n">${i + 1}</td><td>${esc(l.desc || l.item || "")}${l.code ? `<div class="ds">Cost code ${esc(l.code)}</div>` : ""}</td><td class="r">${money(+l.amount || 0)}</td></tr>`)
    .join("")}</tbody></table>
  <div class="cxd-tot sans">${Math.abs(gross - net) > 0.005 ? `<div><span>Billed</span><span>${money(gross)}</span></div><div><span>Retainage held</span><span>− ${money(r2(gross - net))}</span></div>` : ""}<div class="big"><span>Bill total</span><span>${money(net)}</span></div></div>
  ${(b.approvals || []).length ? `<div class="cxd-box sans"><b>Approvals</b>${(b.approvals || []).map((a) => ("function" == typeof apTrailLine ? apTrailLine(b, a) : `<div>${esc(a.t || "")} ${esc(a.action)} · ${esc(a.by || "")}</div>`)).join("")}</div>` : ""}
  ${b.dispute ? `<div class="cxd-box sans"><b>In dispute</b><div>${esc(b.dispute.why || "")}</div></div>` : ""}
  </div>`;
}
function dvBillFile(b) {
  if (!b || !b.fileId) return null;
  for (const p of DB.projects || []) {
    const f = (p.files || []).find((x) => x.id === b.fileId);
    if (f) return f;
  }
  return null;
}
// the document's HTML for the viewer: the body of the one render, without its print script
function dvDocHtml(r) {
  if ("bill" === r.kind) return dvBillHtml(r.b);
  const html = cxDocHtml(r.c, r.d, { print: !1, draft: "draft" === r.d.status }),
    m = /<body[^>]*>([\s\S]*)<\/body>/i.exec(html);
  return (m ? m[1] : html).replace(/<script[\s\S]*?<\/script>/gi, "");
}

// ---- the actions: by type, status and role ------------------------------------------------------------------------------
// { id, label, blue } inline; more: under More. One blue at most, and only a safe next step; money out and anything
// destructive is never blue and always under More.
function dvActions(r) {
  const A = [],
    add = (id, label, o) => A.push(Object.assign({ id: id, label: label }, o || {})),
    me = role();
  if (dvCur && dvCur.portal) {
    const d = r.d,
      c = r.c;
    if ("invoice" === r.kind && dvBal(c, d) > 0.005) add("howtopay", "How to Pay", { blue: !0 });
    if (["estimate", "co"].includes(r.kind) && "sent" === d.status) add("papprove", "Approve", { blue: !0 });
    add("pdf", "Download PDF");
    add("ask", "Ask About This");
    return A;
  }
  if ("bill" === r.kind) {
    const b = r.b,
      held = ("function" == typeof pay3Short && pay3Short(b)) || !!b.dispute || !!(b.onHold && "open" === b.onHold.state) || ["hold", "on-hold", "held", "exception"].includes(b.status),
      waiting = ["submitted", "pm-approved"].includes(b.status),
      mayApprove = waiting && (isOwner() || ("object" == typeof DELEGATION && DELEGATION.bill && DELEGATION.bill.who && DELEGATION.bill.who({ id: b.id }) === me));
    mayApprove && add("bapprove", "Approve", { blue: !held });
    // paying is money out: never the blue button
    "approved" === b.status && add("bpay", "Pay");
    dvBillFile(b) && add("bfile", "Vendor's Document");
    add("pdf", "Download PDF");
    ("draft" === b.status || held) && add("bedit", "Edit");
    !["paid", "verified", "void", "draft"].includes(b.status) && !b.dispute && add("bdispute", "Dispute", { more: !0 });
    !["void", "draft"].includes(b.status) && add("bcredit", "Request Credit", { more: !0 });
    add("print", "Print", { more: !0 }), add("history", "View History", { more: !0 });
    return A;
  }
  const c = r.c,
    d = r.d,
    k = r.kind,
    st = "invoice" === k || "credit" === k ? invoiceStatus(c, d) : d.status,
    draft = "draft" === d.status,
    dead = ["void", "superseded", "rejected", "expired"].includes(d.status);
  if ("credit" === k) {
    !dead && add("email", "Send to Client", { blue: !0 });
    add("pdf", "Download PDF");
    add("openinv", "Open the Invoice");
    add("print", "Print", { more: !0 }), add("history", "View History", { more: !0 });
    return A;
  }
  if ("invoice" === k) {
    const open = ["sent", "partial", "overdue"].includes(st),
      money_in = dvRefundable(c, d).some((x) => x.banked);
    if (draft) add("send", "Send to Client", { blue: !0 });
    // the client's money is found in the bank's own lines first: a typed payment is "recorded, not yet in the bank"
    open && add("findbank", "Find in Bank", { blue: !0 });
    !dead && add("edit", "Edit");
    !draft && !dead && add("email", "overdue" === st ? "Send Reminder" : "Send to Client");
    add("pdf", "Download PDF");
    open && add("pay", "Record Payment", { more: !0 });
    !draft && !dead && DV_CREDIT_ROLES.includes(me) && add("credit", "Create Credit", { more: !0 });
    !draft && !dead && money_in && DV_CREDIT_ROLES.includes(me) && add("refund", "Refund", { more: !0 });
    add("print", "Print", { more: !0 });
    add("dup", "Duplicate", { more: !0 });
    draft && add("void", "Void", { more: !0 });
    add("history", "View History", { more: !0 });
    return A;
  }
  if ("estimate" === k) {
    if (draft) add("send", "Send to Client", { blue: !0 });
    "sent" === d.status && add("approve", "Record Client Approval", { blue: !0 });
    "approved" === d.status && ("construction" === d.template ? add("convert", "Convert to Contract", { blue: !0 }) : add("invoice", "Convert to Invoice", { blue: !0 }));
    if ("converted" === d.status) {
      "function" == typeof ctDepositDue && ctDepositDue(c, d)
        ? add("deposit", "Create Deposit Invoice", { blue: !0 })
        : "construction" === d.template
          ? add("progress", "New Progress Invoice", { blue: !0 })
          : add("invoice", "Convert to Invoice", { blue: !0 });
    }
    // a signed estimate is part of the contract: a change goes on a New Change Order, never an edit
    draft ? add("edit", "Edit") : ["approved", "converted"].includes(d.status) ? add("newco", "New Change Order") : "sent" === d.status && add("edit", "Edit");
    add("pdf", "Download PDF");
    !draft && !dead && add("email", "Send to Client", { more: !0 });
    add("dup", "Duplicate", { more: !0 });
    add("print", "Print", { more: !0 }), add("history", "View History", { more: !0 });
    return A;
  }
  // change order
  if (draft) add("send", "Send to Client", { blue: !0 });
  "sent" === d.status && add("approve", "Record Approval", { blue: !0 });
  "approved" === d.status && add("billco", "Bill It", { blue: !0 });
  (draft || "sent" === d.status) && add("edit", "Edit");
  add("pdf", "Download PDF");
  !draft && !dead && add("email", "Send to Client", { more: !0 });
  add("dup", "Duplicate", { more: !0 });
  add("print", "Print", { more: !0 }), add("history", "View History", { more: !0 });
  return A;
}

// ---- the viewer ----------------------------------------------------------------------------------------------------------
const DV_ICON = {
  x: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  more: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="5" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="19" cy="12" r="1.4"/></svg>',
  down: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>',
};
function dvStatusWord(r) {
  if ("bill" === r.kind) return billState(r.b).text;
  if ("credit" === r.kind) {
    const inv = (r.c.invoices || []).find((x) => x.id === r.d.creditOf);
    return "void" === r.d.status ? "void" : `applied to ${inv ? inv.number : "the invoice"}`;
  }
  if ("invoice" === r.kind) return "function" == typeof invoiceStatusShown ? invoiceStatusShown(r.c, r.d).text : invoiceStatus(r.c, r.d);
  return r.d.status;
}
// what a person needs to know before acting, above the document: a revision, credits on it, refunds and their state
function dvNotes(r) {
  if ("bill" === r.kind || (dvCur && dvCur.portal)) return "";
  const c = r.c,
    d = r.d,
    out = [];
  d.supersededBy && out.push(`${esc(d.number)} was replaced by ${esc(d.supersededBy)}; it is kept as it was sent.`);
  d.revisedBy && !d.supersededBy && out.push(`${esc(d.revisedBy)} revises this ${"invoice" === d.type ? "invoice" : "document"}; ${esc(d.number)} stands as sent until ${esc(d.revisedBy)} goes out.`);
  d.revisionOf && out.push(`This revises ${esc(d.revisionOf)}${d.reviseReason ? `: ${esc(d.reviseReason)}` : ""}.`);
  if ("invoice" === d.type && !d.creditMemo) {
    dvCreditsOn(c, d).forEach((x) => out.push(`Credit memo ${esc(x.number)} of ${money(Math.abs(docTotal(x).total))} is applied to it${x.creditWhy ? ` (${esc(x.creditWhy)})` : ""}.`));
    (c.refunds || [])
      .filter((f) => f.invoiceId === d.id && "void" !== f.status)
      .forEach((f) => {
        const pend = "proposed" === f.status;
        out.push(
          `<span data-dvrefund="${esc(f.id)}">Refund of ${money(f.amount)} to ${esc(f.to)}: ${esc(dvRefundWord(c, f))}${pend ? ` · waiting on ${esc(dvRefundApproverWord())}` : ""}.${pend && dvMayApproveRefund(f) ? ` <button type="button" class="btn sm" data-dvact="rfapprove:${esc(f.id)}">Approve the Refund</button> <button type="button" class="btn sm" data-dvact="rfdecline:${esc(f.id)}">Decline</button>` : ""}${"approved" === f.status && !f.txnId ? ` <button type="button" class="btn sm" data-dvact="rfmatch:${esc(f.id)}">Match to Bank Line</button>` : ""}</span>`,
        );
      });
  }
  return out.length ? `<div class="dv-notes small">${out.map((x) => `<div>${x}</div>`).join("")}</div>` : "";
}
function dvDraw() {
  if (!dvCur) return;
  const r = dvFind(dvCur.kind, dvCur.id, dvCur.cid);
  if (!r) return dvClose();
  const ph = isMobile(),
    A = dvActions(r),
    blue = A.find((a) => a.blue),
    inline = ph ? (blue ? [blue] : A.filter((a) => !a.more).slice(0, 1)) : A.filter((a) => !a.more),
    more = A.filter((a) => !inline.includes(a)),
    num = r.kind === "bill" ? r.b.number || "Bill" : r.d.number,
    who = r.kind === "bill" ? `${r.b.vendor || ""}` : `${r.c.name}${r.d.projectId ? " · " + (((DB.projects || []).find((p) => p.id === r.d.projectId) || {}).project || {}).name : ""}`,
    btn = (a) => `<button type="button" class="btn${a.blue ? " primary" : ""} dv-b" data-dvact="${esc(a.id)}">${"pdf" === a.id ? DV_ICON.down : ""}<span>${esc(a.label)}</span></button>`;
  let el = document.getElementById("dv");
  const keep = el && el.dataset.rec === dvCur.kind + ":" + dvCur.id ? (el.querySelector(".dv-body") || {}).scrollTop || 0 : 0;
  el || ((el = document.createElement("div")), (el.id = "dv"), document.body.appendChild(el));
  el.setAttribute("role", "dialog"), el.setAttribute("aria-modal", "true"), el.setAttribute("aria-label", `${DV_LABEL[r.kind]} ${num}`);
  el.dataset.rec = dvCur.kind + ":" + dvCur.id;
  el.className = ph ? "dv-ph" : "";
  el.innerHTML = `<div class="dv-sheet"><div class="dv-hd"><div class="dv-ttl"><h2>${esc(DV_LABEL[r.kind])} ${esc(num)}</h2><div class="small muted">${esc(who)} · <span class="dv-st">${esc(dvStatusWord(r))}</span></div></div><button type="button" class="btn dv-x" data-dvact="close" aria-label="Close">${DV_ICON.x}<span>Close</span></button></div>${dvNotes(r)}<div class="dv-body"><style>${CX_CSS}</style><div class="dv-doc">${dvDocHtml(r)}</div></div><div class="dv-bar">${more.length ? `<button type="button" class="btn dv-b dv-moreb" data-dvact="more" aria-expanded="${dvMore}" aria-haspopup="menu">${DV_ICON.more}<span>More</span></button>` : ""}<span class="grow"></span>${inline.slice().reverse().map(btn).join("")}</div>${dvMore && more.length ? `<div class="dv-menu" role="menu">${more.map((a) => `<button type="button" role="menuitem" class="dv-mi" data-dvact="${esc(a.id)}">${esc(a.label)}</button>`).join("")}</div>` : ""}</div>`;
  document.body.classList.add("dv-open");
  ph && dvReflow(el);
  const body = el.querySelector(".dv-body");
  body && keep && (body.scrollTop = keep);
}
// at phone width a table reads as one block per row, each value under its column's name: nothing scrolls sideways
function dvReflow(el) {
  el.querySelectorAll(".dv-doc table").forEach((t) => {
    const H = [...t.querySelectorAll("thead th")].map((th) => (th.textContent || "").trim());
    t.classList.add("dv-stack");
    t.querySelectorAll("tbody tr").forEach((tr) => [...tr.children].forEach((td, i) => H[i] && td.setAttribute("data-k", H[i])));
  });
}
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("#dv [data-dvact]") : null;
    if (!b) return;
    e.preventDefault(), e.stopPropagation();
    dvAct(b.dataset.dvact);
  },
  !0,
);
document.addEventListener("keydown", (e) => {
  "Escape" === e.key && dvCur && !document.getElementById("mbm") && dvClose();
});

// ---- doing it ------------------------------------------------------------------------------------------------------------
function dvAct(a) {
  if (!dvCur) return;
  const r = dvFind(dvCur.kind, dvCur.id, dvCur.cid);
  if ("close" === a) return dvClose();
  if ("more" === a) return (dvMore = !dvMore), void dvDraw();
  dvMore = !1;
  if (!r) return dvClose();
  const [verb, arg] = String(a).split(":");
  if ("rfapprove" === verb) return dvRefundDecide(r.c, arg, !0);
  if ("rfdecline" === verb) return dvRefundDecide(r.c, arg, !1);
  if ("rfmatch" === verb) return dvRefundMatchSheet(r.c, arg);
  if ("pdf" === a) return dvPdf(r);
  if ("history" === a) return dvHistory(r);
  if ("bill" === r.kind) return dvBillAct(r, a);
  const c = r.c,
    d = r.d,
    k = "credit" === r.kind ? "invoice" : r.kind;
  if (dvCur.portal) {
    if ("howtopay" === a) return void (el => el && el.scrollIntoView({ block: "start" }))(document.querySelector("#dv .cx-remit"));
    if ("papprove" === a) return dvClose(), void ("function" == typeof portalApprove && portalApprove(c, d));
    if ("ask" === a) return dvClose(), void ("function" == typeof portalQuestion && portalQuestion(c, d));
    return;
  }
  if ("print" === a) return printDoc(c, d);
  if ("openinv" === a) {
    const inv = (c.invoices || []).find((x) => x.id === d.creditOf);
    return inv ? dvOpen("invoice", inv.id, c.id) : toast("The invoice it credits is not on file");
  }
  if ("edit" === a) {
    if ("draft" === d.status) return dvEdit(r);
    return dvReviseSheet(r);
  }
  if ("newco" === a) return dvNewCO(r);
  if ("credit" === a) return dvCreditSheet(c, d);
  if ("refund" === a) return dvRefundSheet(c, d);
  if ("void" === a) return dvVoidSheet(c, d);
  if ("send" === a) {
    // a draft goes out through the one Send (the client gate, the mail, the portal); its sheet opens over the editor
    dvEdit(r);
    return void setTimeout(() => ("function" == typeof crSendToClient ? crSendToClient(c, d) : docAction(c, d, "email")), 30);
  }
  if ("billco" === a) {
    const sv = (c.sov || []).find((v) => v.coId === d.id);
    if (sv) {
      const est = (c.estimates || []).find((x) => "converted" === x.status && (!d.projectId || x.projectId === d.projectId));
      return dvClose(), est ? void docAction(c, est, "progress") : void toast(`${d.number} is on the schedule of values: it bills on the next progress invoice`);
    }
    return dvClose(), void docAction(c, d, "invoice");
  }
  if ("pay" === a) return dvClose(), (clientOpen = c.id), void docAction(c, d, "pay");
  // the rest are the document's own actions, run as the editor runs them
  const keepOpen = "email" === a;
  keepOpen || dvClose();
  const done = docAction(c, k === "invoice" ? d : d, a);
  Promise.resolve(done).then(() => {
    try {
      ["approve", "dup", "convert", "deposit", "progress", "invoice"].includes(a) && save();
      "approve" === a && rcToast(`${d.number} approved by the client, recorded by ${dvWho()}`, [{ label: "Open", run: () => dvOpen(k, d.id, c.id) }]);
    } catch (e) {}
  });
}
function dvBillAct(r, a) {
  const b = r.b;
  if ("bedit" === a) return dvClose(), (dvBillEdit = b.id), void openBill(b.id);
  if ("bfile" === a) return "function" == typeof openFile ? void openFile(b.fileId) : void 0;
  if ("print" === a) {
    const w = window.open("", "_blank");
    return w && w.document ? (w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${esc(b.number || "Bill")}</title><style>body{margin:36px}${CX_CSS}</style></head><body>${dvBillHtml(b)}<script>window.onload=()=>window.print()<\/script></body></html>`), void w.document.close()) : void toast("Allow pop-ups to print");
  }
  dvClose();
  if ("bapprove" === a) return void apprBillYes({ kind: "bill", id: b.id, act: "pm" === role() && "submitted" === b.status ? "pmok" : "approve" });
  if ("bpay" === a) return void payDialog(b.id);
  if ("bdispute" === a) return void billAction(b, "dispute");
  if ("bcredit" === a) return void billAction(b, "short");
}

// ---- Edit on a posted document: a linked void and re-issue, with a reason (Financial truth: append-only) -----------------
function dvReviseSheet(r) {
  const c = r.c,
    d = r.d,
    inv = "invoice" === d.type,
    paid = inv && invoicePaid(c, d) > 0.005;
  if (d.revisedBy && !d.supersededBy) {
    const n = (docColl(c, d.type) || []).find((x) => x.number === d.revisedBy);
    if (n) return toast(`${d.revisedBy} already revises ${d.number}: open it`), dvOpen(d.type, n.id, c.id);
  }
  mbModal(
    `Edit ${esc(d.number)}`,
    `<p class="small" style="margin:0 0 10px">${esc(d.number)} is ${esc(dvStatusWord(r))}, so it is not changed. Edit starts ${esc(d.revisionRoot || d.number)}-R${1 + (docColl(c, d.type) || []).filter((x) => x.revisionRoot === (d.revisionRoot || d.number)).reduce((a, x) => Math.max(a, +x.rev || 0), 0)}, a draft copy you change. ${inv ? `When it is sent, ${esc(d.number)} is voided (its posting is reversed) and the revision replaces it${paid ? `; the ${money(invoicePaid(c, d))} received moves to the revision` : ""}.` : `When it is sent, it replaces ${esc(d.number)}.`} Both stay on file, linked.</p>${mbF("Why It Changes", mbIn("why", "", "e.g. wrong quantity on the tile line"))}`,
    {
      submit: "Start the Revision",
      onSubmit: (f) => {
        if (!f.why) return toast("Say why it changes: the reason goes on both records"), !1;
        dvRevise(c, d, f.why);
      },
    },
  );
}
function dvRevise(c, d, why) {
  dvClose();
  const n = lkRevise(c, d);
  if (!n) return null;
  n.reviseReason = why;
  const h = (d.history || [])[d.history.length - 1];
  h && "revised" === h.action && (h.note = `${n.number}: ${why}`);
  try {
    audit(d.type, d.id, "revise-reason", { number: d.number }, { number: n.number }, `${d.number} → ${n.number}: ${why}`);
  } catch (e) {}
  dvEditing = n.id;
  save();
  rcToast(`${n.number} started from ${d.number} (${why}); ${d.number} stands as sent until ${n.number} goes out`, [{ label: "Open", run: () => dvOpen(d.type, n.id, c.id) }]);
  return n;
}
// The original is voided when its revision goes out (lkSupersede). The money received on it follows the re-issue, each
// payment with an audit row: the payment is unchanged in amount, date and bank line; only the invoice it settles moves.
if ("function" == typeof lkSupersede) {
  const base = lkSupersede;
  lkSupersede = function (c, o, n) {
    const was = o && o.status;
    const r = base.apply(this, arguments);
    try {
      if (o && n && "invoice" === o.type && "void" === o.status && "void" !== was) {
        (c.payments || [])
          .filter((p) => p.invoiceId === o.id && !p.unapplied)
          .forEach((p) => {
            (p.invoiceId = n.id), (p.movedFrom = o.number);
            audit("payment", p.id, "moved-to-revision", { invoice: o.number }, { invoice: n.number }, `${money(+p.amount || 0)} of ${fmtL(p.date)} follows ${o.number} to ${n.number}`);
          });
        dvCreditsOn(c, o).forEach((x) => ((x.creditOf = n.id), (x.creditOfNumber = n.number)));
        "sent" === n.status && invoicePaid(c, n) >= docTotal(n).total - 0.005 && (n.status = "paid");
      }
    } catch (e) {
      console.warn("docview: supersede", e);
    }
    return r;
  };
}
// a signed estimate is the contract: the change is a New Change Order on its job
function dvNewCO(r) {
  const c = r.c,
    d = r.d;
  dvClose();
  const co = newDoc(c, "co", { fields: { projectId: d.projectId || "", title: "" } });
  co.changeOf = d.number;
  dvEditing = co.id;
  save();
  (clientOpen = c.id), (docOpen = { kind: "co", id: co.id });
  "undefined" != typeof billTab && (billTab = "co");
  render();
  rcToast(`${co.number} started for ${d.number}: ${d.number} is signed, so the change goes on a change order`, [{ label: "Open", run: () => dvOpen("co", co.id, c.id) }]);
  return co;
}
function dvVoidSheet(c, d) {
  if ("draft" !== d.status) return toast(`${d.number} is sent: Edit makes a linked void and re-issue`);
  mbModal(`Void ${esc(d.number)}`, `<p class="small" style="margin:0 0 10px">The draft is kept, marked void, with the reason. Nothing was sent or posted.</p>${mbF("Why", mbIn("why", "", "e.g. drafted twice"))}`, {
    submit: "Void the Draft",
    onSubmit: (f) => {
      if (!f.why) return toast("Say why it is voided"), !1;
      docAudit(c, d, "void", f.why), (d.status = "void"), (d.voidReason = f.why);
      (c.activity = c.activity || []).push({ t: nowStamp(), by: dvWho(), text: `${d.number} voided: ${f.why}` });
      save(), render();
      rcToast(`${d.number} voided: ${f.why}`, [{ label: "Open", run: () => dvOpen(d.type, d.id, c.id) }]);
    },
  });
}

// ---- Create Credit: a credit memo in c.invoices, applied to the one invoice it credits ------------------------------------
// The memo carries the invoice's tax rate, retainage and percentage discount, so it reverses each in proportion; an SOV
// line is credited by a negative share of its scheduled value, which lowers the line's billed-to-date (sovBilled).
function dvCreditable(c, inv) {
  const sov = "sov" === inv.mode,
    prior = dvCreditsOn(c, inv);
  return (inv.lines || [])
    .map((l) => {
      const amt = lineAmount(l, inv),
        done = r2(-prior.reduce((a, x) => a + (x.lines || []).filter((y) => y.creditOfLine === l.id).reduce((s, y) => s + lineAmount(y, x), 0), 0));
      return { l: l, amt: amt, left: r2(amt - done), sov: sov };
    })
    .filter((x) => x.left > 0.005 && !(x.sov && !(+x.l.scheduled > 0)));
}
// o.onAccount: the whole credit goes on the client's account (a refund's credit pays money back; it settles nothing)
function dvCreditCreate(c, inv, picks, why, o) {
  o = o || {};
  if (!DV_CREDIT_ROLES.includes(role())) return { ok: !1, why: "Billing, the Controller or the Owner credits an invoice" };
  if (!inv || "invoice" !== inv.type || inv.creditMemo || ["draft", "void"].includes(inv.status)) return { ok: !1, why: "Only a sent invoice is credited" };
  const w = String(why || "").trim();
  if (!w) return { ok: !1, why: "Say why it is credited" };
  const can = dvCreditable(c, inv),
    sov = "sov" === inv.mode,
    lines = [];
  for (const pk of picks || []) {
    const x = can.find((y) => y.l.id === pk.lineId),
      amt = r2(+pk.amount || 0);
    if (!(amt > 0)) continue;
    if (!x) return { ok: !1, why: "That line is already credited in full" };
    if (amt > x.left + 0.005) return { ok: !1, why: `${x.l.item || "A line"} can be credited at most ${money(x.left)}` };
    const l = x.l,
      common = { id: uid("l"), item: l.item || l.desc || "Line", desc: sov ? "" : l.desc || "", taxable: !!l.taxable, creditOfLine: l.id, code: l.code || "", cat: l.cat || "" };
    lines.push(
      sov
        ? Object.assign(common, { sovId: l.sovId, scheduled: +l.scheduled || 0, prevPct: 0, pct: -((amt / +l.scheduled) * 100), stored: 0 })
        : Object.assign(common, { qty: 1, unit: "ls", rate: -amt, fromLine: l.fromLine || "" }),
    );
  }
  if (!lines.length) return { ok: !1, why: "Pick at least one line and an amount to credit" };
  // the memo takes the next credit memo number (CM-), never an invoice number: the invoice sequence keeps no gap
  const keep = JSON.stringify({ seq: DB.company.seq || {}, free: DB.company.cxFree || null }),
    cm = newDoc(c, "invoice", {
      mode: sov ? "sov" : "items",
      fields: { projectId: inv.projectId || "", title: `Credit memo for ${inv.number}`, lines: [], taxRate: +inv.taxRate || 0, retainagePct: +inv.retainagePct || 0, terms: "", memo: "" },
    });
  try {
    const K = JSON.parse(keep);
    (DB.company.seq = K.seq), K.free ? (DB.company.cxFree = K.free) : delete DB.company.cxFree;
  } catch (e) {}
  dvFresh.delete(cm.id);
  const seqN = ((DB.company.seq = DB.company.seq || {}).cm = (+DB.company.seq.cm || 0) + 1);
  Object.assign(cm, {
    number: `CM-${appNow().getFullYear()}-${String(seqN).padStart(3, "0")}`,
    lines: lines,
    creditMemo: !0,
    creditOf: inv.id,
    creditOfNumber: inv.number,
    creditWhy: w,
    discount: inv.discount && "pct" === inv.discount.type ? Object.assign({}, inv.discount) : { type: "pct", value: 0 },
    date: today(),
    due: today(),
    status: "sent",
    isDeposit: !1,
    issuedBy: dvWho(),
    issuedAt: appNowIso(),
    printKind: "credit",
  });
  delete cm.depositOf, delete cm.depositApplied;
  const X = r2(-docTotal(cm).total),
    bal = o.onAccount ? 0 : Math.max(0, dvBal(c, inv)),
    onInv = r2(Math.min(X, bal)),
    rest = r2(X - onInv),
    by = dvWho(),
    stamp = { date: today(), method: "Credit memo", ref: cm.number, cmApply: !0, creditMemoId: cm.id, txnId: "cm:" + cm.id, recordedBy: by, recordedAt: appNowIso() };
  onInv > 0.005 && c.payments.push(Object.assign({ id: uid("py"), amount: onInv, invoiceId: inv.id, note: `${cm.number} applied to ${inv.number}` }, stamp));
  rest > 0.005 && c.payments.push(Object.assign({ id: uid("py"), amount: rest, invoiceId: "", unapplied: !0, voidedInvoice: cm.number, note: `${cm.number}: credit on account (${inv.number} had ${money(bal)} due)` }, stamp));
  c.payments.push(Object.assign({ id: uid("py"), amount: -X, invoiceId: cm.id, note: `${cm.number} applied` }, stamp));
  inv.status !== "void" && invoicePaid(c, inv) >= docTotal(inv).total - 0.005 && (inv.status = "paid");
  // the one register of credits to clients (blCreditRows reads it): approved by the person who issued it
  const cc = { id: uid("cc"), projectId: inv.projectId || "", clientId: c.id, amount: X, why: w, status: "proposed", at: today(), by: by, invoiceId: cm.id, invoiceLineId: lines[0].id, creditMemoId: cm.id, creditOf: inv.id, source: "credit-memo" };
  (DB.clientCredits = DB.clientCredits || []).push(cc);
  (cc.status = "approved"), apStamp("client-credit", cc, `credit memo ${cm.number} issued by ${by}`, "approved", { by: by, approve: !0, before: "proposed", after: "approved", note: w });
  docAudit(c, cm, "issued", `${money(X)} credit on ${inv.number}: ${w}`);
  docAudit(c, inv, "credited", `${cm.number} ${money(X)}: ${w}`);
  (c.activity = c.activity || []).push({ t: nowStamp(), by: by, text: `${cm.number} credits ${inv.number} ${money(X)}: ${w}` });
  "function" == typeof docMark && docMark(cm);
  return save(), { ok: !0, cm: cm, applied: onInv, onAccount: rest, total: X };
}
function dvCreditSheet(c, inv) {
  const can = dvCreditable(c, inv);
  if (!can.length) return toast(`Every line of ${inv.number} is credited already`);
  const t = docTotal(inv);
  mbModal(
    `Create Credit on ${esc(inv.number)}`,
    `<p class="small" style="margin:0 0 8px">Tick the lines to credit and how much of each. The credit memo reverses the sales tax${+inv.retainagePct ? " and the retainage" : ""} on what it credits and is applied to ${esc(inv.number)}${dvBal(c, inv) > 0.005 ? ` (${money(dvBal(c, inv))} due)` : "; it is paid, so the credit is held on the client's account for the next invoice or a refund"}.${"sov" === inv.mode ? " A progress line's credit lowers its billed to date." : ""}</p>
    <div class="dv-cl">${can
      .map(
        (x) =>
          `<label class="dv-cr"><input type="checkbox" data-crpick="${esc(x.l.id)}"><span class="grow"><b>${esc(x.l.item || x.l.desc || "Line")}</b><span class="small muted"> · billed ${money(x.amt)}${x.left < x.amt - 0.005 ? `, ${money(x.left)} left to credit` : ""}</span></span><input type="number" step="0.01" min="0" max="${x.left}" inputmode="decimal" data-cramt="${esc(x.l.id)}" value="${x.left}" aria-label="Credit on ${esc(x.l.item || "line")}"></label>`,
      )
      .join("")}</div>
    ${mbF("Why", mbIn("why", "", "e.g. tile line billed twice; agreed with the client"))}
    <div class="small muted" data-crsum>${t.tax || t.ret ? "Tax and retainage are worked out from the lines you tick." : ""}</div>`,
    {
      submit: "Issue the Credit Memo",
      onSubmit: (f) => {
        const m = document.getElementById("mbm"),
          picks = [...m.querySelectorAll("[data-crpick]")]
            .filter((x) => x.checked)
            .map((x) => ({ lineId: x.dataset.crpick, amount: +((m.querySelector(`[data-cramt="${x.dataset.crpick}"]`) || {}).value || 0) }));
        if (!picks.length) return toast("Tick at least one line to credit"), !1;
        const R = dvCreditCreate(c, inv, picks, f.why);
        if (!R.ok) return toast(R.why), !1;
        render();
        dvOpen("credit", R.cm.id, c.id);
        rcToast(`${R.cm.number} issued: ${money(R.total)} credited on ${inv.number}${R.onAccount > 0.005 ? `, ${money(R.onAccount)} held on the account` : ""}`, [{ label: "Open", run: () => dvOpen("credit", R.cm.id, c.id) }]);
      },
    },
  );
}

// ---- Refund: a proposal the owner approves; it returns money the bank has, to the account that paid ------------------
const dvRefundApprover = () => (DB.company && DB.company.refundApprover) || "owner";
const dvRefundApproverWord = () => ("object" == typeof APPR_WHO && APPR_WHO[dvRefundApprover()]) || "the owner";
function dvMayApproveRefund(f) {
  const me = String(dvWho()).toLowerCase();
  return role() === dvRefundApprover() && !(f.by && String(f.by).toLowerCase() === me);
}
function dvRefundWord(c, f) {
  if ("proposed" === f.status) return "proposed, not approved";
  if ("declined" === f.status) return `declined by ${f.decidedBy || ""}${f.declineWhy ? ": " + f.declineWhy : ""}`;
  return f.txnId ? `refunded, in the bank ${fmtL(f.bankDate || f.decidedAt)}` : "approved, not in the bank";
}
// the account a payment came into: its own, else the bank line that backs it
function dvPayAcctId(p) {
  if (p.acctId) return p.acctId;
  try {
    const bk = payBacking().get(p);
    return (bk && bk.t && bk.t.acct) || "";
  } catch (e) {
    return "";
  }
}
function dvPayAcct(p) {
  const a = (DB.accounts || []).find((x) => x.id === dvPayAcctId(p));
  return `${p.method || "payment"}${a ? ` from ${a.name}${a.last4 ? " ending " + a.last4 : ""}` : ""}`;
}
function dvRefundPropose(c, inv, paymentId, amount, why, withCredit) {
  if (!DV_CREDIT_ROLES.includes(role())) return { ok: !1, why: "Billing, the Controller or the Owner proposes a refund" };
  const x = dvRefundable(c, inv).find((y) => y.p.id === paymentId),
    amt = r2(+amount || 0),
    w = String(why || "").trim();
  if (!x) return { ok: !1, why: "Pick a payment received on this invoice" };
  if (!x.banked) return { ok: !1, why: `That payment is ${PAY_NOT_IN_BANK}: only money the bank has is refunded` };
  if (!(amt > 0) || amt > x.left + 0.005) return { ok: !1, why: `Refund between $0.01 and ${money(x.left)} of that payment` };
  if (!w) return { ok: !1, why: "Say why the money goes back" };
  const f = {
    id: uid("rf"),
    invoiceId: inv.id,
    invoiceNumber: inv.number,
    paymentId: x.p.id,
    amount: amt,
    acctId: dvPayAcctId(x.p),
    method: x.p.method || "",
    to: dvPayAcct(x.p),
    why: w,
    withCredit: !!withCredit,
    status: "proposed",
    by: dvWho(),
    byRole: role(),
    at: today(),
    approver: dvRefundApprover(),
  };
  (c.refunds = c.refunds || []).push(f);
  apStamp("client-refund", f, `refund of ${money(amt)} proposed by ${f.by}`, "proposed", { after: { amount: amt, paymentId: x.p.id, to: f.to }, note: w });
  docAudit(c, inv, "refund-proposed", `${money(amt)} to ${f.to}: ${w}`);
  return save(), { ok: !0, f: f };
}
// Approved: a negative payment tied to the payment it returns (refundOf). With a credit the invoice stays settled: the
// credit memo puts the amount on the account and the refund draws it out; without one the amount is owed again.
function dvRefundDecide(c, id, yes, note) {
  const f = (c.refunds || []).find((x) => x.id === id);
  if (!f || "proposed" !== f.status) return toast("That refund is not waiting on anyone"), null;
  if (!dvMayApproveRefund(f)) return toast(`A refund is approved by ${dvRefundApproverWord()}, never by the person who proposed it`), null;
  const inv = (c.invoices || []).find((x) => x.id === f.invoiceId),
    by = dvWho();
  if (!yes) {
    if (void 0 === note) {
      mbModal(`Decline the Refund of ${money(f.amount)}`, mbF("Why", mbIn("why", "", "e.g. the client is paying the balance instead")), {
        submit: "Decline",
        onSubmit: (v) => (v.why ? void dvRefundDecide(c, id, !1, v.why) : (toast("Say why"), !1)),
      });
      return null;
    }
    Object.assign(f, { status: "declined", decidedBy: by, decidedAt: today(), declineWhy: note });
    apStamp("client-refund", f, `refund declined by ${by}`, "declined", { before: "proposed", after: "declined", note: note });
    inv && docAudit(c, inv, "refund-declined", `${money(f.amount)}: ${note}`);
    save(), render();
    rcToast(`Refund of ${money(f.amount)} declined: ${note}`, inv ? [{ label: "Open", run: () => dvOpen("invoice", inv.id, c.id) }] : null);
    return f;
  }
  if (f.withCredit && inv) {
    const R = dvCreditCreate(c, inv, dvCreditLump(c, inv, f.amount), `Refund ${f.id}: ${f.why}`, { onAccount: !0 });
    R.ok ? (f.creditMemoId = R.cm.id) : toast(`No credit memo: ${R.why}`);
  }
  const fromAcct = r2((c.payments || []).filter((p) => p.unapplied).reduce((a, p) => a + (+p.amount || 0), 0)) >= f.amount - 0.05,
    rec = { id: uid("py"), date: today(), amount: -f.amount, method: f.method || "Refund", ref: `Refund ${f.invoiceNumber}`, acctId: f.acctId, invoiceId: fromAcct ? "" : f.invoiceId, unapplied: fromAcct, refundOf: f.paymentId, refundId: f.id, why: f.why, recordedBy: by, recordedAt: appNowIso(), note: `refund of ${money(f.amount)} to ${f.to}: ${f.why}` };
  c.payments.push(rec);
  Object.assign(f, { status: "approved", decidedBy: by, decidedAt: today(), paymentRecId: rec.id });
  apStamp("client-refund", f, `refund of ${money(f.amount)} approved by ${by}`, "approved", { by: by, approve: !0, before: "proposed", after: "approved", note: f.why });
  if (inv && !["void", "draft"].includes(inv.status) && !fromAcct) {
    const paid = invoicePaid(c, inv);
    inv.status = paid >= docTotal(inv).total - 0.005 ? "paid" : paid > 0.005 ? "partial" : inv.due && inv.due < today() ? "overdue" : "sent";
  }
  inv && docAudit(c, inv, "refund-approved", `${money(f.amount)} to ${f.to}`);
  (c.activity = c.activity || []).push({ t: nowStamp(), by: by, text: `Refund of ${money(f.amount)} to ${f.to} approved: ${f.why}` });
  save(), render();
  rcToast(`Refund of ${money(f.amount)} approved: it goes back to ${f.to}; it reads "approved, not in the bank" until the bank line is matched`, inv ? [{ label: "Open", run: () => dvOpen("invoice", inv.id, c.id) }] : null);
  return f;
}
// a credit for a refund with no line chosen: spread over the invoice's lines in order, as far as each allows (pre-tax)
function dvCreditLump(c, inv, amount) {
  const can = dvCreditable(c, inv),
    t = docTotal(inv),
    k = t.total ? Math.max(0.0001, (t.sub - t.disc) / t.total) : 1;
  let left = r2(amount * k);
  const out = [];
  can.forEach((x) => {
    if (left <= 0.005) return;
    const a = r2(Math.min(x.left, left));
    out.push({ lineId: x.l.id, amount: a }), (left = r2(left - a));
  });
  return out;
}
function dvRefundSheet(c, inv) {
  const R = dvRefundable(c, inv);
  if (!R.length) return toast(`No money received on ${inv.number} is left to refund`);
  const banked = R.filter((x) => x.banked);
  mbModal(
    `Refund on ${esc(inv.number)}`,
    `<p class="small" style="margin:0 0 8px">A refund is a proposal until ${esc(dvRefundApproverWord())} approves it. It goes back only to the account the payment came from, and reads "approved, not in the bank" until its bank line is matched.</p>
    ${banked.length ? "" : `<div class="note warn">No payment on ${esc(inv.number)} is in the bank yet; only money the bank has is refunded.</div>`}
    ${mbF("Payment It Returns", mbSel("pay", R.map((x) => [x.p.id, `${fmtL(x.p.date)} · ${money(+x.p.amount)} · ${dvPayAcct(x.p)}${x.banked ? "" : " (not in the bank)"}${x.left < +x.p.amount - 0.005 ? ` · ${money(x.left)} left` : ""}`]), (banked[0] || R[0]).p.id))}
    ${mbF("Amount", mbIn("amount", String((banked[0] || R[0]).left), "", "number"))}
    ${mbF("Why", mbIn("why", "", "e.g. the client overpaid; the tile line was credited"))}
    <label class="small" style="display:flex;gap:8px;align-items:flex-start;margin-top:8px"><input type="checkbox" data-f="credit" checked> <span>Credit ${esc(inv.number)} for the same amount, so the client does not owe it again (leave unticked to refund credit already on the account)</span></label>`,
    {
      submit: "Propose the Refund",
      onSubmit: (f) => {
        const x = dvRefundPropose(c, inv, f.pay, f.amount, f.why, f.credit);
        if (!x.ok) return toast(x.why), !1;
        render();
        dvOpen("invoice", inv.id, c.id);
        rcToast(`Refund of ${money(x.f.amount)} proposed: it waits on ${dvRefundApproverWord()} in Approvals`, [{ label: "Open", run: () => dvOpen("invoice", inv.id, c.id) }]);
      },
    },
  );
}
// the bank lines that can be this refund: money out of the account that paid, the same amount, from the approval on
function dvRefundLines(f) {
  const used = new Set((DB.clients || []).flatMap((c) => (c.refunds || []).map((x) => x.txnId)).filter(Boolean));
  return (DB.txns || []).filter(
    (t) => +t.amt < 0 && Math.abs(-t.amt - f.amount) < 0.01 && (!f.acctId || t.acct === f.acctId) && !used.has(t.id) && !t.billId && !(t.match && (t.match.billId || t.match.paymentId)) && (!f.decidedAt || (t.date || "") >= addDaysIso(f.decidedAt, -3)),
  );
}
function addDaysIso(d, n) {
  const x = new Date(d + "T12:00:00");
  return x.setDate(x.getDate() + n), x.toISOString().slice(0, 10);
}
function dvRefundMatch(c, id, txnId) {
  const f = (c.refunds || []).find((x) => x.id === id),
    t = (DB.txns || []).find((x) => x.id === txnId);
  if (!f || "approved" !== f.status) return { ok: !1, why: "Only an approved refund is matched to the bank" };
  if (!t || !dvRefundLines(f).includes(t)) return { ok: !1, why: "That line is not this refund: the amount, the account or the date do not fit" };
  const rec = (c.payments || []).find((p) => p.id === f.paymentRecId);
  (f.txnId = t.id), (f.bankDate = t.date), rec && (rec.txnId = t.id);
  (t.match = Object.assign({}, t.match || {}, { refundId: f.id, paymentId: rec ? rec.id : "" })), (t.refundId = f.id);
  audit("client-refund", f.id, "matched", "approved, not in the bank", t.id, `${money(f.amount)} matched to ${t.desc || "the bank line"} of ${fmtL(t.date)}`);
  "function" == typeof payBackReset && payBackReset();
  return save(), { ok: !0 };
}
function dvRefundMatchSheet(c, id) {
  const f = (c.refunds || []).find((x) => x.id === id);
  if (!f) return;
  const L = dvRefundLines(f);
  if (!L.length) return toast(`No ${money(f.amount)} out of ${f.to} is in the bank's lines yet; it stays "approved, not in the bank" until it is`);
  mbModal(`Match the Refund of ${money(f.amount)}`, mbF("Bank Line", mbSel("t", L.map((t) => [t.id, `${fmtL(t.date)} · ${t.desc || ""} · ${money(t.amt)}`]), L[0].id)), {
    submit: "Match",
    onSubmit: (v) => {
      const R = dvRefundMatch(c, id, v.t);
      if (!R.ok) return toast(R.why), !1;
      render();
      rcToast(`Refund of ${money(f.amount)} matched to its bank line`, [{ label: "Open", run: () => dvOpen("invoice", f.invoiceId, c.id) }]);
    },
  });
}
// the refund in the owner's Approvals (one item per proposal), and its open: the invoice's document with the decision
if ("object" == typeof DELEGATION) DELEGATION.refund = { role: "owner", rule: "a refund to a client sends money out: the owner approves it (or the approver Settings names), never the person who proposed it", who: () => dvRefundApprover() };
if ("object" == typeof APPR_CHIPS && Array.isArray(APPR_CHIPS) && !APPR_CHIPS.some(([k]) => "refund" === k)) APPR_CHIPS.splice(Math.max(0, APPR_CHIPS.length - 1), 0, ["refund", "Refunds"]);
if ("function" == typeof mApprovals) {
  const base = mApprovals;
  mApprovals = function (opts) {
    const out = base.apply(this, arguments);
    try {
      if (!Array.isArray(out) || !((opts && opts.everyone) || role() === dvRefundApprover())) return out;
      (DB.clients || []).forEach((c) =>
        (c.refunds || [])
          .filter((f) => "proposed" === f.status)
          .forEach((f) =>
            out.push({
              kind: "refund",
              id: f.id,
              sev: "warn",
              n: money(f.amount),
              title: `Refund ${money(f.amount)} to ${c.name}`,
              detail: `${f.invoiceNumber} · back to ${f.to} · ${f.why} · proposed by ${f.by}`,
              yes: "Review the Refund",
              who: dvRefundApprover(),
              due: today(),
              open: { view: "billing", dvInvoice: f.invoiceId, dvClient: c.id },
            }),
          ),
      );
    } catch (e) {}
    return out;
  };
}
if ("function" == typeof mGo) {
  const base = mGo;
  mGo = function (go) {
    if (go && go.dvInvoice) return dvOpen("invoice", go.dvInvoice, go.dvClient);
    return base.apply(this, arguments);
  };
}

// ---- the money paths a credit memo and a refund ride on ---------------------------------------------------------------
// A credit application is settled without cash: it is never "recorded, not yet in the bank", and its pair nets to zero
// in every sum. A refund counts as bank money only once its bank line is matched.
if ("function" == typeof payBankedAmt) {
  const base = payBankedAmt;
  payBankedAmt = function (c, py) {
    if (py && py.cmApply) return r2(+py.amount || 0);
    if (py && py.refundId) return py.txnId ? r2(+py.amount || 0) : 0;
    return base.apply(this, arguments);
  };
}
if ("function" == typeof glPaymentLines) {
  const base = glPaymentLines;
  glPaymentLines = function (c, p) {
    return p && p.cmApply ? [] : base.apply(this, arguments);
  };
}
// the memo's journal: the invoice's own posting of the same lines, reversed (Dr revenue and sales tax, Cr AR and retainage)
if ("function" == typeof glInvoiceLinesLive) {
  const base = glInvoiceLinesLive;
  glInvoiceLinesLive = function (c, d) {
    if (!d || !d.creditMemo) return base.apply(this, arguments);
    const pos = Object.assign({}, d, {
      creditMemo: !1,
      lines: (d.lines || []).map((l) => ("sov" === d.mode ? Object.assign({}, l, { pct: -(+l.pct || 0) }) : Object.assign({}, l, { rate: -(+l.rate || 0) }))),
    });
    return base.call(this, c, pos).map((l) => Object.assign({}, l, { dr: l.cr, cr: l.dr, memo: l.memo || "credit memo" }));
  };
}
if ("function" == typeof invoiceStatusShown) {
  const base = invoiceStatusShown;
  invoiceStatusShown = function (c, x) {
    if (x && x.creditMemo) return { text: "void" === x.status ? "void" : "credit applied", cls: "void" === x.status ? "void" : "paid", st: invoiceStatus(c, x) };
    return base.apply(this, arguments);
  };
}

// ---- Download PDF: a real .pdf of the same document, laid out from the render the viewer shows ---------------------------
function dvPdfLines(root) {
  // reading order of the render: each block's text, and each table row as cells (the last ones right-aligned)
  const out = [],
    seen = new Set();
  const walk = (el) => {
    if (!el || seen.has(el) || /^(STYLE|SCRIPT|SVG)$/i.test(el.tagName)) return;
    if ("TABLE" === el.tagName) {
      seen.add(el);
      const H = [...el.querySelectorAll("thead th")].map((x) => (x.textContent || "").trim());
      H.length && out.push({ row: H, bold: !0 });
      el.querySelectorAll("tbody tr").forEach((tr) => out.push({ row: [...tr.children].map((td) => (td.innerText || td.textContent || "").replace(/\s+/g, " ").trim()) }));
      out.push({ gap: 6 });
      return;
    }
    const kids = [...el.children].filter((k) => !/^(STYLE|SCRIPT)$/.test(k.tagName));
    const blocky = kids.some((k) => /^(DIV|TABLE|P|H\d|UL)$/.test(k.tagName));
    if (!blocky) {
      const txt = (el.innerText || el.textContent || "").trim();
      if (!txt) return;
      const big = el.classList && (el.classList.contains("cxd-kind") || el.classList.contains("cxd-word"));
      const bold = el.classList && (el.classList.contains("big") || /^(B|H\d)$/.test(el.tagName) || el.classList.contains("cxd-k"));
      txt.split(/\n+/).forEach((t) => t.trim() && out.push({ text: t.trim(), size: big ? 16 : 10, bold: big || bold }));
      return;
    }
    kids.forEach(walk);
    el.classList && (el.classList.contains("cxd-lh") || el.classList.contains("cxd-hd") || el.classList.contains("cxd-meta")) && out.push({ gap: 6 });
  };
  walk(root);
  return out;
}
function dvPdfBytes(items, title) {
  const W = 612,
    H = 792,
    M = 48,
    pe = (s) =>
      String(s)
        .replace(/[—–]/g, "-")
        .replace(/[’‘]/g, "'")
        .replace(/[“”]/g, '"')
        .replace(/−/g, "-")
        .replace(/[^\x20-\x7e]/g, "")
        .replace(/[\\()]/g, (m) => "\\" + m),
    wid = (s, sz) => String(s).length * sz * 0.5,
    pages = [];
  let ops = [],
    y = H - M;
  const newPage = () => {
      ops.length && pages.push(ops.join("\n"));
      (ops = []), (y = H - M);
    },
    text = (x, s, sz, bold) => ops.push(`BT /${bold ? "F2" : "F1"} ${sz} Tf ${x.toFixed(1)} ${y.toFixed(1)} Td (${pe(s)}) Tj ET`),
    wrap = (s, sz, w) => {
      const words = String(s).split(/\s+/),
        L = [];
      let cur = "";
      words.forEach((wd) => {
        const t = cur ? cur + " " + wd : wd;
        wid(t, sz) > w && cur ? (L.push(cur), (cur = wd)) : (cur = t);
      });
      return cur && L.push(cur), L;
    },
    need = (h) => y - h < M && newPage();
  items.forEach((it) => {
    if (it.gap) return void (y -= it.gap);
    if (it.row) {
      const n = it.row.length,
        sz = 9,
        right = Math.min(3, Math.max(0, n - 2)),
        colW = 78,
        leftW = W - 2 * M - right * colW,
        firstW = n - right > 1 ? 24 : 0,
        mainW = leftW - firstW,
        lines = wrap(it.row[n - right - 1] || "", sz, mainW - 6);
      need(lines.length * 12 + 4);
      n - right > 1 && text(M, it.row[0], sz, it.bold);
      lines.forEach((l, i) => (text(M + firstW, l, sz, it.bold), i < lines.length - 1 && (y -= 12)));
      for (let i = 0; i < right; i++) {
        const s = it.row[n - right + i] || "";
        text(M + leftW + (i + 1) * colW - wid(s, sz) - 4, s, sz, it.bold);
      }
      y -= 14;
      return;
    }
    const sz = it.size || 10,
      L = wrap(it.text, sz, W - 2 * M);
    L.forEach((l) => (need(sz + 4), text(M, l, sz, it.bold), (y -= sz + 4)));
  });
  newPage();
  const objs = ["<< /Type /Catalog /Pages 2 0 R >>", ""],
    kids = [];
  objs.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>");
  pages.forEach((c) => {
    const ci = objs.length + 1;
    objs.push(`<< /Length ${c.length} >>\nstream\n${c}\nendstream`);
    kids.push(objs.length + 1);
    objs.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${W} ${H}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ${ci} 0 R >>`);
  });
  objs[1] = `<< /Type /Pages /Kids [${kids.map((k) => k + " 0 R").join(" ")}] /Count ${kids.length} >>`;
  objs.push(`<< /Title (${pe(title)}) /Producer (SmartDesigns Projects) >>`);
  let out = "%PDF-1.4\n";
  const offs = [];
  objs.forEach((o, i) => (offs.push(out.length), (out += `${i + 1} 0 obj\n${o}\nendobj\n`)));
  const x = out.length;
  out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n${offs.map((n) => String(n).padStart(10, "0") + " 00000 n \n").join("")}trailer\n<< /Size ${objs.length + 1} /Root 1 0 R /Info ${objs.length} 0 R >>\nstartxref\n${x}\n%%EOF\n`;
  return out;
}
function dvPdf(r) {
  const host = document.createElement("div");
  host.style.cssText = "position:absolute;left:-10000px;top:0;width:800px";
  host.innerHTML = `<style>${CX_CSS}</style>${dvDocHtml(r)}`;
  document.body.appendChild(host);
  let pdf;
  try {
    pdf = dvPdfBytes(dvPdfLines(host.querySelector(".cxd") || host), "bill" === r.kind ? `Bill ${r.b.number || ""}` : r.d.number);
  } finally {
    host.remove();
  }
  const name = `${("bill" === r.kind ? `${r.b.vendor || "Bill"} ${r.b.number || ""}` : r.d.number).replace(/[^\w.-]+/g, "_")}.pdf`,
    blob = new Blob([pdf], { type: "application/pdf" }),
    a = document.createElement("a");
  (a.href = URL.createObjectURL(blob)), (a.download = name), document.body.appendChild(a), a.click(), a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4e3);
  toast(`${name} downloaded`);
  return name;
}

// ---- View History: every change, payment, credit and refund on the record, with who and when -------------------------------
function dvHistory(r) {
  const id = "bill" === r.kind ? r.b.id : r.d.id,
    au = (DB.audit || []).filter((x) => x.refId === id || (r.c && (r.c.refunds || []).some((f) => f.invoiceId === id && f.id === x.refId))),
    rows = au
      .slice()
      .sort((a, b) => String(a.ts || "").localeCompare(String(b.ts || "")))
      .map((x) => `<tr><td class="small nowrap">${esc(x.t || "")}</td><td class="small">${esc(x.by || x.role || "")}</td><td class="small">${esc(String(x.action || "").replace(/-/g, " "))}${x.note ? ` <span class="muted">· ${esc(x.note)}</span>` : ""}</td></tr>`)
      .join(""),
    pays = r.c ? (r.c.payments || []).filter((p) => p.invoiceId === id) : [];
  mbModal(
    `History of ${esc("bill" === r.kind ? r.b.number || "the bill" : r.d.number)}`,
    `${rows ? `<div class="tw"><table class="t"><thead><tr><th>When</th><th>Who</th><th>What</th></tr></thead><tbody>${rows}</tbody></table></div>` : '<p class="small muted">Nothing recorded on it yet.</p>'}${pays.length ? `<h4 style="margin:12px 0 4px">Money On It</h4>${pays.map((p) => `<div class="small">${esc(fmtL(p.date))} · ${money(+p.amount || 0)} · ${esc(p.method || "")}${p.cmApply ? " (credit, no cash)" : p.refundId ? " (refund)" : ""}${p.note ? ` · ${esc(p.note)}` : ""}</div>`).join("")}` : ""}`,
    { submit: null },
  );
}

// ---- the viewer's look: a sheet over the page; at phone width the whole screen, the bar at the bottom ----------------------
(function () {
  const s = document.createElement("style");
  s.id = "dv-css";
  s.textContent = `#dv{position:fixed;inset:0;z-index:38;background:rgba(20,26,40,.45);display:flex;justify-content:center;align-items:stretch;padding:24px}
#dv .dv-sheet{position:relative;background:var(--paper,#fff);width:min(980px,100%);display:flex;flex-direction:column;border-radius:10px;box-shadow:0 12px 40px rgba(0,0,0,.25);overflow:hidden}
#dv .dv-hd{display:flex;gap:12px;align-items:flex-start;padding:14px 18px;border-bottom:1px solid var(--rule,#E6E9EE)}
#dv .dv-ttl{flex:1;min-width:0}#dv .dv-ttl h2{margin:0;font-size:18px;overflow-wrap:anywhere}
#dv .dv-x{display:inline-flex;gap:6px;align-items:center;min-height:40px}
#dv .dv-notes{padding:8px 18px;background:var(--wash,#F6F7F9);border-bottom:1px solid var(--rule,#E6E9EE)}#dv .dv-notes>div{padding:2px 0}
#dv .dv-body{flex:1;overflow:auto;padding:28px 34px;background:#fff;-webkit-overflow-scrolling:touch}
#dv .dv-doc{max-width:860px;margin:0 auto;overflow-wrap:anywhere}
#dv .dv-bar{display:flex;gap:8px;align-items:center;padding:10px 14px;border-top:1px solid var(--rule,#E6E9EE);background:var(--paper,#fff);flex-wrap:wrap}
#dv .dv-bar .grow{flex:1}#dv .dv-b{display:inline-flex;gap:6px;align-items:center;min-height:40px}
#dv .dv-menu{position:absolute;right:14px;bottom:64px;background:var(--paper,#fff);border:1px solid var(--rule,#D9DDE3);border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.18);display:flex;flex-direction:column;min-width:220px;padding:6px;z-index:2}
#dv .dv-mi{background:none;border:0;text-align:left;padding:10px 12px;min-height:44px;border-radius:6px;font:inherit;cursor:pointer;color:inherit}#dv .dv-mi:hover{background:var(--wash,#F2F4F7)}
#dv .dv-moreb{order:-1}
body.dv-open{overflow:hidden}body.dv-open #fsay,body.dv-open #fab{display:none}
#dv.dv-ph{padding:0}#dv.dv-ph .dv-sheet{border-radius:0;width:100%}
#dv.dv-ph .dv-hd{padding:10px 12px}#dv.dv-ph .dv-ttl h2{font-size:16px}
#dv.dv-ph .dv-body{padding:16px 16px 24px}
#dv.dv-ph .dv-bar{flex-wrap:nowrap;padding:10px 12px calc(10px + env(safe-area-inset-bottom));gap:12px}
#dv.dv-ph .dv-b{min-height:48px;padding:0 18px}
#dv.dv-ph .dv-bar .btn.primary{flex:1;justify-content:center}
#dv.dv-ph .dv-menu{left:8px;right:8px;bottom:76px}
#dv.dv-ph .dv-mi{min-height:48px}
#dv.dv-ph .cxd{font-size:13px;max-width:100%}
#dv.dv-ph .cxd-lh,#dv.dv-ph .cxd-hd{flex-direction:column;align-items:flex-start;gap:8px}
#dv.dv-ph .cxd-firm,#dv.dv-ph .cxd-num{text-align:left}
#dv.dv-ph .cxd-meta,#dv.dv-ph .cxd-grid,#dv.dv-ph .cxd-sig{grid-template-columns:1fr;gap:10px}
#dv.dv-ph .cxd-tot{width:auto;margin-left:0}
#dv.dv-ph .cxd-draft{font-size:34px;top:180px}
#dv.dv-ph table.dv-stack,#dv.dv-ph table.dv-stack tbody,#dv.dv-ph table.dv-stack tr,#dv.dv-ph table.dv-stack td{display:block;width:auto}
#dv.dv-ph table.dv-stack thead{display:none}
#dv.dv-ph table.dv-stack tr{border-bottom:1px solid #E6E9EE;padding:6px 0}
#dv.dv-ph table.dv-stack td{border:0;padding:2px 0;text-align:left;white-space:normal}
#dv.dv-ph table.dv-stack td.n{display:none}
#dv.dv-ph table.dv-stack td.r{display:flex;justify-content:space-between;gap:12px}
#dv.dv-ph table.dv-stack td.r::before{content:attr(data-k);color:#6b7480;font:11px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;text-transform:uppercase;letter-spacing:.04em}
.dv-cl{display:flex;flex-direction:column;gap:6px;margin-bottom:10px;max-height:46vh;overflow:auto}
.dv-cr{display:flex;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid var(--rule,#E6E9EE)}.dv-cr input[type=number]{width:110px}.dv-cr .grow{flex:1;min-width:0}`;
  document.head.appendChild(s);
})();

// ---- anything can be queried (NetSuite's differentiator): client refunds are a table in erpQuery, Ask and the Report
// Builder; credit memos are rows of "invoices" (creditMemo, creditOf), as they live
if ("object" == typeof EQ_TABLES) {
  EQ_TABLES.refunds = () =>
    (DB.clients || []).flatMap((c) =>
      (c.refunds || []).map((f) => ({
        _id: f.id,
        _module: "Billing",
        _label: `Refund ${money(f.amount)} to ${c.name} on ${f.invoiceNumber}`,
        _go: () => dvOpen("invoice", f.invoiceId, c.id),
        clientId: c.id,
        client: c.name,
        invoice: f.invoiceNumber,
        amount: f.amount,
        to: f.to,
        status: f.status,
        state: dvRefundWord(c, f),
        why: f.why,
        proposedBy: f.by,
        approvedBy: f.approvedBy || "",
        date: f.at,
      })),
    );
  "object" == typeof EQ_ALIAS && (EQ_ALIAS.refund = "refunds");
  "undefined" != typeof EQ_MONEY_TABLES && Array.isArray(EQ_MONEY_TABLES) && !EQ_MONEY_TABLES.includes("refunds") && EQ_MONEY_TABLES.push("refunds");
}

// ---- a revision replaces its original in the work billed to date --------------------------------------------------------
// While a progress invoice's revision is out (a draft or sent, the original not yet voided), the original's percentages
// are not counted beside the revision's: INV-2026-038-R1 read 66.67% billed to date on every line (the original's
// share twice) and the billed-ahead gate read the double count.
if ("function" == typeof sovBilled) {
  const base = sovBilled;
  sovBilled = function (c, sovId, exceptId) {
    let v = base.apply(this, arguments);
    try {
      (c.invoices || []).forEach((o) => {
        if (o.id === exceptId || "sov" !== o.mode || "void" === o.status || !o.revisedBy || ("function" == typeof invIsDeposit && invIsDeposit(o))) return;
        const n = (c.invoices || []).find((x) => x.number === o.revisedBy && x.id !== o.id && "void" !== x.status);
        n && (v -= (o.lines || []).filter((l) => l.sovId === sovId).reduce((a, l) => a + (+l.pct || 0), 0));
      });
    } catch (e) {}
    return v;
  };
}
