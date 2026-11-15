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
   - the approval queue (mApprovals, DELEGATION): a refund is a proposal in the client-credit register (DB.clientCredits, kind "refund") the owner approves (Settings may
     name another approver: DB.company.refundApprover); approved, it posts as a negative payment tied to the payment it
     returns (refundOf), back to the account that paid, and reads "approved, not in the bank" until a bank line on
     that account is matched to it;
   - the audit trail (audit, apStamp, docAudit): every mutation names who, when and why.
   Suite: tests/docview_test.py. Journey check: tests/cycle_walk.py open_document (J8).
--------------------------------------------------------------------------------------------------------------------- */
const DV_ROLES = ["owner", "billing", "controller"],
  DV_CREDIT_ROLES = ["owner", "billing", "controller"],
  DV_LABEL = { estimate: "Estimate", co: "Change Order", invoice: "Invoice", credit: "Credit Memo", bill: "Bill" };
let dvCur = null, // { kind, id, cid }: the record open in the viewer
  dvEditing = null, // the document the person chose to edit: its editor draws as before
  dvMore = !1,
  dvBillEdit = null;
// Documents just made (New Invoice, the queue's Draft, Duplicate, a revision: every one goes through newDoc) open in
// the editor. The flag is set on create and lasts for the person's action that made it: their next tap or key clears
// it, so a document made in passing (a sweep, an import, a draft the assistant wrote) opens as its document when it is
// opened later. No clock is read.
const dvFresh = new Set();
["pointerdown", "keydown"].forEach((t) => document.addEventListener(t, () => dvFresh.clear(), !0));
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
// what the client is asked to pay now: one rule with the lists (invoiceStatus), so a paid invoice never asks again
function dvDue(c, d) {
  return d && "invoice" === d.type && !d.creditMemo && ["sent", "partial", "overdue"].includes(invoiceStatus(c, d)) ? Math.max(0, dvBal(c, d)) : 0;
}
// the date a paid invoice was settled: its last payment in (a credit memo's application counts)
function dvPaidOn(c, d) {
  const P = (c.payments || []).filter((p) => p.invoiceId === d.id && +p.amount > 0).map((p) => p.date || "").sort();
  return P.length ? P[P.length - 1] : d.paidOn || "";
}
// the header's money line for an invoice: what is due, Paid, or Draft (the office and the portal alike)
function dvDueLine(c, d) {
  if (!d || "invoice" !== d.type || d.creditMemo) return "";
  if ("draft" === d.status) return "Draft";
  if ("void" === d.status) return "";
  if ("paid" === invoiceStatus(c, d)) {
    const on = dvPaidOn(c, d);
    return `Paid${on ? " " + fmtL(on) : ""}`;
  }
  const due = dvDue(c, d);
  return due > 0.005 ? `${money(due)} due${d.due ? " " + fmtL(d.due) : ""}` : "";
}
// the money the client paid on an invoice that a refund can return: payments the bank has, less what was refunded
// or is proposed against each
function dvRefundable(c, d) {
  const ids = new Set(dvChain(c, d).map((x) => x.id));
  return (c.payments || [])
    .filter((p) => ids.has(p.invoiceId) && +p.amount > 0 && !p.xferOf && !p.cmApply && !p.creditApply && !p.reverses && !p.reversalId && !p.refundOf)
    .map((p) => {
      const out = r2(
        dvRefunds(c).filter((f) => f.paymentId === p.id && !["declined", "void"].includes(f.status)).reduce((a, f) => a + (+f.amount || 0), 0),
      );
      // never more than the bank has of it: a payment recorded and not in the bank returns nothing
      return { p: p, banked: payBanked(c, p), left: r2(Math.min(+p.amount, payBankedAmt(c, p)) - out) };
    })
    .filter((x) => x.left > 0.005 || !x.banked);
}
// the invoice and the ones it revises: a credit given on INV-2026-038 still stands on INV-2026-038-R1
function dvChain(c, d) {
  const out = [d];
  let o = d;
  for (let i = 0; o && o.revisionOf && i < 20; i++) (o = (c.invoices || []).find((x) => x.number === o.revisionOf && x.id !== o.id)), o && out.push(o);
  return out;
}
function dvCreditsOn(c, d) {
  const ids = new Set(dvChain(c, d).map((x) => x.id));
  return (c.invoices || []).filter((x) => x.creditMemo && ids.has(x.creditOf) && "void" !== x.status);
}
// The one register of what the firm owes a client back (DB.clientCredits, blCreditRows): a vendor credit passed on, a
// credit memo (source "credit-memo"), and a refund (kind "refund": proposed, approved or declined, its bank line txnId)
function dvRefunds(c) {
  return (DB.clientCredits || []).filter((x) => "refund" === x.kind && (!c || x.clientId === c.id));
}
function dvCreditAsks(c) {
  return (DB.clientCredits || []).filter((x) => "credit-ask" === x.kind && (!c || x.clientId === c.id));
}
// the Billing Queue's "credit the client" rows are vendor credits passed on; a refund or a credit waiting on the owner
// is in Approvals, never a second row there
if ("function" == typeof blCreditRows) {
  const base = blCreditRows;
  blCreditRows = function () {
    return (base.apply(this, arguments) || []).filter((r) => !(r && r.cc && ["refund", "credit-ask"].includes(r.cc.kind)));
  };
}

// ---- the open path: every list sets docOpen; billing and the controller read the document first --------------------------
function dvOpen(kind, id, cid) {
  const r = dvFind(kind, id, cid);
  if (!r) return toast("That document is not on file");
  // a draft estimate is being built: it opens in its editor from anywhere (a toast's Open, a link), never the viewer
  if ("estimate" === r.kind && r.d && "draft" === r.d.status && "client" !== role()) return dvEdit(r);
  (dvCur = { kind: r.kind, id: id, cid: r.c ? r.c.id : "", view: view }), (dvMore = !1);
  dvDraw();
}
function dvClose() {
  dvCur = null;
  dvMore = !1;
  const el = document.getElementById("dv");
  el && el.remove();
  document.body.classList.remove("dv-open");
}
// An estimate being built opens in its editor, whoever opens it: a draft, or any estimate opened from a building
// workflow (the client's Estimates panel, which Sales and Clients opens it on; Discovery's Open Discovery). Sent and
// signed documents opened from anywhere else (Billing's lists, the job's Contract and Billing, Today, Cmd-K, Ask, a
// toast) open as the document. Decided by the record's status and where it was opened from, never per screen.
let dvBuildId = ""; // one-shot: the estimate a building workflow just asked to open
function dvBuilding(r) {
  if (!r || "estimate" !== r.kind || !r.d) return !1;
  if ("draft" === r.d.status || dvBuildId === r.d.id) return !0;
  return "clients" === view && "undefined" != typeof clientTab && "fin" === clientTab && "undefined" != typeof finTab && "estimates" === finTab;
}
// Discovery (src/livejobs.js: Open Discovery, the estimate's panel) opens its estimate to work on it
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("[data-ljopen]") : null;
    if (!b) return;
    const [, kind, id] = String(b.dataset.ljopen || "").split("|");
    "estimate" === kind && id && (dvBuildId = id);
  },
  !0,
);
// The job's Contract and Billing is a list of the job's documents, not a building workflow: a sent or signed estimate
// opened there is the document (Record Client Approval is its blue, one tap; the walk's J8 took one more with the
// editor), and a draft opens its editor by its status.
function dvIntercept() {
  if ("undefined" == typeof docOpen || !docOpen) return void (dvEditing = null);
  const id = docOpen.id;
  if (id === dvEditing) return;
  if (dvFresh.has(id) || !dvOn()) return dvFresh.delete(id), dvBuildId === id && (dvBuildId = ""), void (dvEditing = id);
  const cid = clientOpen || "",
    r = dvFind(docOpen.kind, id, cid);
  if (!r) return void (dvEditing = id);
  if (dvBuilding(r)) return (dvBuildId = ""), void (dvEditing = id);
  dvBuildId = "";
  // the page under the document stays the list the person came from; the document opens on top of it
  (docOpen = null), (dvEditing = null), (dvCur = { kind: r.kind, id: id, cid: r.c.id, view: view }), (dvMore = !1);
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
      // the document sits over the page it was opened from: a move to another page (a link, a toast, the menu) closes it
      dvCur && dvCur.view && dvCur.view !== view && dvClose();
      dvCur ? dvDraw() : document.getElementById("dv") && dvClose();
    } catch (e) {
      console.warn("docview: draw", e);
    }
    return r;
  };
}
// a bill opens as its document for the controller (the spec: "Bill (AP), for the controller"); Edit opens the bill sheet as before;
// billing keeps the bill sheet, where it enters and codes bills
if ("function" == typeof openBill) {
  const base = openBill;
  openBill = function (id) {
    if ("controller" === role() && id && id !== dvBillEdit && (DB.bills || []).some((b) => b.id === id)) return dvOpen("bill", id);
    dvBillEdit = null;
    return base.apply(this, arguments);
  };
}
// the client's portal: the same document and the same viewer, with the client's own actions (Approve, How to Pay, Ask)
if ("function" == typeof portalView) {
  const base = portalView;
  portalView = function (c, k, d) {
    if ("client" !== role() || !c || !d || !CX_TYPES.includes(k)) return base.apply(this, arguments);
    dvCur = { kind: k, id: d.id, cid: c.id, portal: !0, view: view };
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
    return `<!doctype html><html><head><meta charset="utf-8"><title>${esc(d.number)} · ${esc(K.name)}</title><style>body{margin:36px;background:#fff}${CX_CSS}@media print{html body{margin:0}}</style></head><body><div class="cxd" data-cxkind="credit">${"void" === d.status ? '<div class="cxd-draft">VOID</div>' : ""}
  ${cxLetterhead(d)}
  <div class="cxd-hd"><div class="cxd-kind">Credit Memo</div><div class="cxd-num sans"><b>${esc(d.number)}</b><br>Date: ${cxDate(d.date)}${inv ? `<br>Credits invoice ${esc(inv.number)}` : ""}</div></div>
  <div class="cxd-meta"><div><div class="cxd-k sans">Credit to</div><b>${esc(c.name)}</b><br>${esc(cxBillAddr(c, d))}${cxContactLine(c, bt)}</div><div><div class="cxd-k sans">Project</div><b>${esc(pr.name)}</b>${pr.addr ? `<br>${esc(pr.addr)}` : ""}</div></div>
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
    if ("invoice" === r.kind && dvDue(c, d) > 0.005) add("howtopay", "How to Pay", { blue: !0 });
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
    // the Hold row the bill sheet carries (app.js, next to billHoldSheet), under the same conditions; never blue
    if (["submitted", "pm-approved"].includes(b.status) && !["client", "crew", "driver", "foreman"].includes(me)) {
      b.onHold && "open" === b.onHold.state ? add("brelease", "Release the Hold") : add("bhold", "Hold");
      add("bback", "Send Back");
    }
    dvBillFile(b) && add("bfile", "Vendor's Document");
    add("pdf", "Download PDF");
    // Edit only on a draft, or while a hold is open: a short-paid bill that is approved, paid or verified is posted, so
    // its difference is a Dispute or a Request Credit, never an edit (controller review, 11-12)
    ("draft" === b.status || !!(b.onHold && "open" === b.onHold.state)) && add("bedit", "Edit");
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
      paid = "paid" === st,
      money_in = dvRefundable(c, d).some((x) => x.banked),
      // the owner's blue on an open invoice is the reminder when one is due, else the PDF; billing and the controller
      // find the client's money in the bank's own lines first (a typed payment is "recorded, not yet in the bank")
      ownerSeat = "owner" === me;
    // a refund or a credit waiting on this person: Approve is on the bar (never blue: it is money back to the client)
    // and opens a sheet that restates the amount, who it goes to and the account, with one Approve
    if (!d.creditMemo) {
      dvRefunds(c)
        .filter((f) => f.invoiceId === d.id && "proposed" === f.status && dvMayApproveRefund(f))
        .forEach((f) => add("rfapprove:" + f.id, "Approve the Refund", { phone: !0 }));
      dvCreditAsks(c)
        .filter((a) => a.invoiceId === d.id && "proposed" === a.status && dvMayApproveCredit(a))
        .forEach((a) => add("crapprove:" + a.id, "Approve the Credit", { phone: !0 }));
    }
    // a paid invoice's next step is its PDF (the receipt): Edit, a linked void and re-issue, waits under More
    if (draft) add("send", "Send to Client", { blue: !0 });
    // paid by a payment the bank has not shown yet (Rivera, 11-15 S2-12): its next step is still Find in Bank
    const unbanked = paid && "function" == typeof invoiceUnbanked && invoiceUnbanked(c, d) > 0.005;
    (open || unbanked) && add("findbank", "Find in Bank", { blue: !ownerSeat });
    open && add("pay", "Record Payment");
    !dead && add("edit", "Edit", paid ? { more: !0 } : draft ? { phone: !0 } : {});
    !draft && !dead && add("email", "overdue" === st ? "Send Reminder" : "Send to Client", ownerSeat && "overdue" === st ? { blue: !0 } : {});
    add("pdf", "Download PDF", (ownerSeat && open && "overdue" !== st) || paid ? { blue: ownerSeat && (open || unbanked) && "overdue" !== st, phone: !0 } : {});
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
    "sent" === d.status && add("lkapprove", "Record Client Approval", { blue: !0 }); // the editor's own: How They Approved, with who and when
    "approved" === d.status && ("construction" === d.template ? add("convert", "Convert to Contract & SOV", { blue: !0 }) : add("invoice", "Convert to Invoice", { blue: !0 }));
    if ("converted" === d.status) {
      // a signed estimate's blue is what the Billing Queue says is next for it (jobReadyToBill, through estBillable):
      // the open application, a milestone, design hours, a deposit, the line-by-line application, received materials.
      // With nothing earned and not billed there is no blue invoice step (11-15 round 2, S1-A: the blue Convert to
      // Invoice drafted EST-2026-D140's whole fee and EST-2026-D45's signing 50% again).
      const K = "function" == typeof estContractBilled ? estContractBilled(c, d) : null,
        B = "function" == typeof estBillable ? estBillable(c, d) : { cap: 0 },
        W = { dmilestone: "Bill the Milestone", dhours: "Bill Design Hours", deposit: "Create Deposit Invoice", application: "Draft the Application", progress: "New Progress Invoice", retainer: "Retainer Invoice" };
      K && K.draft
        ? add("progress", `Open ${K.draft.number}`, { blue: !0 })
        : B.row
          ? add("rtb:" + blRtbKey(B.row), W[B.row.kind] || "Bill It", { blue: !0 })
          : B.cap > 0.5 && add("invoice", "Bill Received Materials", { blue: !0 });
    }
    // a signed estimate is part of the contract: a change goes on a New Change Order, never an edit
    draft ? add("edit", "Edit", { phone: !0 }) : ["approved", "converted"].includes(d.status) ? add("newco", "New Change Order") : "sent" === d.status && add("edit", "Edit");
    add("pdf", "Download PDF");
    !draft && !dead && add("email", "Send to Client", { more: !0 });
    add("dup", "Duplicate", { more: !0 });
    add("print", "Print", { more: !0 }), add("history", "View History", { more: !0 });
    return A;
  }
  // change order
  if (draft) add("send", "Send to Client", { blue: !0 });
  "sent" === d.status && add("lkapprove", "Record Client Approval", { blue: !0 });
  "approved" === d.status && add("billco", "Bill It", { blue: !0 });
  (draft || "sent" === d.status) && add("edit", "Edit", draft ? { phone: !0 } : {});
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
  if ("invoice" === r.kind) {
    if ("function" != typeof invoiceStatusShown) return invoiceStatus(r.c, r.d);
    // how much the bank has not seen, in the words the editor's pill uses ("$5,000 recorded, not yet in the bank")
    const s = invoiceStatusShown(r.c, r.d).text,
      u = "function" == typeof invoiceUnbanked ? invoiceUnbanked(r.c, r.d) : 0;
    return u > 0.005 && s.includes(PAY_NOT_IN_BANK) ? s.replace(PAY_NOT_IN_BANK, `${money(u)} ${PAY_NOT_IN_BANK}`) : s;
  }
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
  // the office's own warning the editor shows over a progress invoice: the job billed ahead of its work (never on the
  // client's copy)
  try {
    if ("invoice" === d.type && "sov" === d.mode && d.projectId && "function" == typeof pbAhead && !["void"].includes(d.status)) {
      const A = pbAhead(d.projectId);
      A && A.total > 0.5 && out.push(`The job is billed ahead of the work: ${money(A.total)} on ${A.lines.length} line${1 === A.lines.length ? "" : "s"}. For the office; the client's copy does not say it.`);
    }
  } catch (e) {}
  if ("invoice" === d.type && !d.creditMemo) {
    dvCreditsOn(c, d).forEach((x) => out.push(`Credit memo ${esc(x.number)} of ${esc(dvCreditBreakWords(dvCreditBreakOf(x)))} is applied to it${x.creditWhy ? ` (${esc(x.creditWhy)})` : ""}.`));
    dvCreditAsks(c)
      .filter((a) => a.invoiceId === d.id && "proposed" === a.status)
      .forEach((a) => {
        // Approve is on the action bar and asks to confirm (dvCreditConfirm); Decline stays here, beside the ask
        const may = dvMayApproveCredit(a);
        out.push(
          `<span data-dvcredit="${esc(a.id)}">Credit of ${esc(dvCreditBreakWords(dvCreditBreakAsk(d, a)))} asked by ${esc(a.by)}: ${esc(a.why)} · over ${money(dvCreditLimit())}, waiting on the owner; nothing is credited yet.${may ? ` <button type="button" class="btn sm" data-dvact="crdecline:${esc(a.id)}">Decline</button>` : ""}</span>`,
        );
      });
    dvRefunds(c)
      .filter((f) => f.invoiceId === d.id && "void" !== f.status)
      .forEach((f) => {
        const pend = "proposed" === f.status;
        out.push(
          `<span data-dvrefund="${esc(f.id)}">Refund of ${esc(dvRefundWords(c, f))}: ${esc(dvRefundWord(c, f))}${pend ? ` · waiting on ${esc(dvRefundApproverWord())}` : ""}.${pend && dvMayApproveRefund(f) ? ` <button type="button" class="btn sm" data-dvact="rfdecline:${esc(f.id)}">Decline</button>` : ""}${"approved" === f.status && !f.txnId ? ` <button type="button" class="btn sm" data-dvact="rfmatch:${esc(f.id)}">Match to Bank Line</button>` : ""}</span>`,
        );
      });
  }
  return out.length ? `<div class="dv-notes small">${out.map((x) => `<div>${x}</div>`).join("")}</div>` : "";
}
// the record's History (who posted, reversed, re-posted or changed what, and why): the strip the editor and the bill
// sheet carry (truthHistoryHtml), under the document, for the office only; a draft has nothing posted, as in the editor
function dvHistoryStrip(r) {
  if ((dvCur && dvCur.portal) || "function" != typeof truthHistoryHtml || "function" != typeof truthKeyOf) return "";
  try {
    if ("bill" === r.kind) return ["draft", "submitted"].includes(r.b.status) ? "" : `<div class="dv-hist no-doc-print">${truthHistoryHtml(truthKeyOf("bill", r.b.id)) || ""}</div>`;
    if ("draft" === r.d.status) return "";
    const h = truthHistoryHtml(truthKeyOf(r.d.type || ("credit" === r.kind ? "invoice" : r.kind), r.d.id));
    return h ? `<div class="dv-hist no-doc-print">${h}</div>` : "";
  } catch (e) {
    return "";
  }
}
function dvDraw() {
  if (!dvCur) return;
  const r = dvFind(dvCur.kind, dvCur.id, dvCur.cid);
  if (!r) return dvClose();
  const ph = isMobile(),
    A = dvActions(r),
    blue = A.find((a) => a.blue),
    // the phone's bar: the blue, and an action marked for the phone (a draft's Edit beside its Send, a paid invoice's
    // PDF); with neither, the first inline action. Record Payment and the rest open first under More, in order.
    pho = A.filter((a) => a.phone && !a.blue && !a.more),
    inline = ph ? (blue ? [blue].concat(pho.slice(0, 1)) : pho.length ? pho.slice(0, 1) : A.filter((a) => !a.more).slice(0, 1)) : A.filter((a) => !a.more),
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
  el.innerHTML = `<div class="dv-sheet"><div class="dv-hd"><div class="dv-ttl"><h2>${esc(DV_LABEL[r.kind])} ${esc(num)}${"bill" !== r.kind && r.d.title ? `<span class="dv-tt"> — ${esc(r.d.title)}</span>` : ""}</h2><div class="small muted">${esc(who)} · <span class="dv-st">${esc(dvStatusWord(r))}</span></div>${"bill" !== r.kind && dvDueLine(r.c, r.d) ? `<div class="dv-due" data-dvdue>${esc(dvDueLine(r.c, r.d))}</div>` : ""}</div><button type="button" class="btn dv-x" data-dvact="close" aria-label="Close">${DV_ICON.x}<span>Close</span></button></div>${dvNotes(r)}<div class="dv-body"><style>${CX_CSS}</style><div class="dv-doc">${dvDocHtml(r)}</div>${dvHistoryStrip(r)}</div><div class="dv-bar">${more.length ? `<button type="button" class="btn dv-b dv-moreb" data-dvact="more" aria-expanded="${dvMore}" aria-haspopup="menu">${DV_ICON.more}<span>More</span></button>` : ""}<span class="grow"></span>${inline.slice().reverse().map(btn).join("")}</div>${dvMore && more.length ? `<div class="dv-menu" role="menu">${more.map((a) => `<button type="button" role="menuitem" class="dv-mi" data-dvact="${esc(a.id)}">${esc(a.label)}</button>`).join("")}</div>` : ""}</div>`;
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
  // a Billing Queue step offered on the document (an estimate's next billing): the queue's own action
  if ("rtb" === verb) return dvClose(), void rtbAct(String(a).slice(4));
  if ("rfapprove" === verb) return dvRefundConfirm(r.c, arg);
  if ("crapprove" === verb) return dvCreditConfirm(r.c, arg);
  if ("rfdecline" === verb) return dvRefundDecide(r.c, arg, !1);
  if ("rfmatch" === verb) return dvRefundMatchSheet(r.c, arg);
  if ("crdecline" === verb) return dvCreditDecide(r.c, arg, !1);
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
    // the billed-ahead reason is asked over the document first: cancelling it leaves the person in the viewer
    // (round 2, S3-G); with the reason given, the send opens over the editor as before
    const go = () => (dvEdit(r), setTimeout(() => ("function" == typeof crSendToClient ? crSendToClient(c, d) : docAction(c, d, "email")), 30));
    if ("function" == typeof pbAheadGate && pbAheadGate(c, d, go, "sendclient")) return;
    return void go();
  }
  if ("billco" === a) {
    const sv = (c.sov || []).find((v) => v.coId === d.id);
    if (sv) {
      // the change order's own lines go on the job's open application, or a new one (round 2, S1-C)
      return dvClose(), void docAction(c, d, "progress");
    }
    return dvClose(), void docAction(c, d, "invoice");
  }
  if ("pay" === a) return dvClose(), (clientOpen = c.id), void docAction(c, d, "pay");
  // the rest are the document's own actions, run as the editor runs them
  // a step that changes the document keeps it open, so the next step (Convert after the approval) is in front of the person
  const keepOpen = ["email", "lkapprove", "convert"].includes(a);
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
  // Hold and Send Back open the bill sheet's own sheet (billHoldSheet); Release the Hold writes what its button writes
  if ("bhold" === a || "bback" === a) return dvClose(), void ("function" == typeof billHoldSheet && billHoldSheet(b, "bhold" === a ? "hold" : "back"));
  if ("brelease" === a) {
    if (!b.onHold || "open" !== b.onHold.state) return;
    (b.onHold.state = "released"), (b.onHold.releasedBy = (currentUser() || {}).name || role()), (b.onHold.releasedAt = appNowIso());
    audit("bill", b.id, "hold-released", "held", b.status, `released by ${b.onHold.releasedBy}; it was held: ${b.onHold.why}`);
    return save(), render(), void rcToast(`Hold released on ${b.vendor} ${b.number || ""}`, [{ label: "Open", run: () => dvOpen("bill", b.id) }]);
  }
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
// The original is voided when its revision goes out (lkSupersede). What was settled on it (payments, credit memos'
// applications) follows the re-issue without touching a posted record: each one stays exactly as it was, on the
// original, and a linked pair of transfer records moves its amount (out of the original, into the revision), netting
// to zero, as a credit memo's application does. A transfer is never cash: it carries the bank standing of the record it
// moves (payBankedAmt) and posts nothing to the ledger (glPaymentLines). Each pair writes one audit row.
function dvTransferSettled(c, o, n) {
  const by = dvWho(),
    done = new Set((c.payments || []).filter((p) => p.xferOf && p.invoiceId === n.id).map((p) => p.xferOf));
  (c.payments || [])
    .filter((p) => p.invoiceId === o.id && !p.unapplied && !p.xferOf && Math.abs(+p.amount || 0) > 0.005 && !done.has(p.id))
    .forEach((p) => {
      const amt = r2(+p.amount || 0),
        stamp = { date: today(), method: "Transfer", ref: `${o.number} to ${n.number}`, xferOf: p.id, txnId: "xfer:" + p.id, recordedBy: by, recordedAt: appNowIso() };
      c.payments.push(Object.assign({ id: uid("py"), invoiceId: o.id, amount: -amt, note: `${money(amt)} moved to ${n.number}, which replaces ${o.number}` }, stamp));
      c.payments.push(Object.assign({ id: uid("py"), invoiceId: n.id, amount: amt, note: `${money(amt)} from ${o.number} (${p.cmApply ? "credit " + (p.ref || "") : (p.method || "payment") + " of " + fmtL(p.date)})` }, stamp));
      audit("payment", p.id, "transferred-to-revision", { invoice: o.number }, { invoice: n.number }, `${money(amt)} of ${fmtL(p.date)} settles ${n.number}, which replaces ${o.number}; the record itself is unchanged`);
    });
}
if ("function" == typeof lkSupersede) {
  const base = lkSupersede;
  lkSupersede = function (c, o, n) {
    const was = o && o.status;
    const r = base.apply(this, arguments);
    try {
      if (o && n && "invoice" === o.type && "void" === o.status && "void" !== was) {
        // A revision that changes no amount changes nothing in the ledger (billing review 11-15 round 2, S1-B:
        // INV-2026-031, $97,000 revised for wording, moved from August revenue to September and was dated after its
        // own due date). It posts as the original posted: its accounting date is the original's (revisedOn keeps the
        // day it was made, for print and the trail), and the ledger keeps the original's posting live, with no
        // reversal and no re-post (glDerive, glSameRevision). One that changes an amount is dated the day it goes out:
        // the original is reversed on that day in the open period and the revision posts, which nets to the
        // difference there, and a closed month is never written into (dvRevisionReversalDate).
        if ("function" == typeof glSameRevision && glSameRevision(c, n) === o && o.date) {
          n.date !== o.date && ((n.revisedOn = n.revisedOn || n.date), (n.date = o.date));
          null != n.dateRec && (n.dateRec = o.dateRec || o.date);
          n.postsAs = o.id;
          Array.isArray(o.glLines) && (n.glLines = o.glLines.map((l) => Object.assign({}, l)));
          docAudit(c, n, "revised-same-amount", `${n.number} changes no amount: it keeps ${o.number}'s date (${fmtL(o.date)}) and posting; nothing in the ledger moves`);
        } else null == n.postsAs && (n.postsAs = "");
        dvTransferSettled(c, o, n);
        "sent" === n.status && invoicePaid(c, n) >= docTotal(n).total - 0.005 && (n.status = "paid");
      }
    } catch (e) {
      console.warn("docview: supersede", e);
    }
    return r;
  };
}
// The ledger's date for reversing an invoice its revision replaced (glSync calls this for a posting no longer
// derived). The reversal posts on the revision's own posting date, so the original's month is untouched and the
// revision's month nets to the difference (nothing when the amounts agree); a locked month is never written into:
// the revision's date if it is open, else the first open day. "" for any other posting, which keeps glSync's rule.
function dvRevisionReversalDate(j, sub) {
  try {
    if (!j || "inv" !== j.sourceType) return "";
    const c = (DB.clients || []).find((x) => x.id === j.clientId) || (DB.clients || []).find((x) => (x.invoices || []).some((i) => i.id === j.sourceId));
    const o = c && (c.invoices || []).find((i) => i.id === j.sourceId);
    if (!o || "void" !== o.status || !o.supersededBy) return "";
    // the revision that stands now: a revision of a revision replaces the one before it (round 2, S1-B: the second
    // revision of INV-2026-035 reversed its posting back in August, because the first revision was void by then)
    let n = (c.invoices || []).find((i) => i.number === o.supersededBy && i.id !== o.id);
    for (let k = 0; n && "void" === n.status && n.supersededBy && k < 20; k++) {
      const m = n;
      n = (c.invoices || []).find((i) => i.number === m.supersededBy && i.id !== m.id);
    }
    if (!n || ["draft", "void"].includes(n.status)) return "";
    const live = ((DB.gl || {}).journals || []).find((x) => x.key === "inv:" + n.id && "posted" === x.status && "reversal" !== x.kind),
      d = (live && live.date) || n.date || today();
    return glLocked(d, j.entityId, sub) ? glFirstOpenDay(j.entityId, sub) : d;
  } catch (e) {
    return "";
  }
}
// a revision's lines remember the lines they copy, so a credit given on the original is not given twice
if ("function" == typeof lkRevise) {
  const base = lkRevise;
  lkRevise = function (c, d) {
    const n = base.apply(this, arguments);
    try {
      n && d && (n.lines || []).forEach((l, i) => d.lines && d.lines[i] && !l.revOfLine && (l.revOfLine = d.lines[i].id));
      if (n && d) {
        // The revision is dated the day it is made and remembers the original's date (it prints "Revised <its date>,
        // original <that date>"; a pay application's "Work through" stays the original's). It KEEPS the original's
        // due date (Alan's rule, 11-13): the client already owed the original by that day, so re-issuing an overdue
        // invoice, for a description or for an amount, never makes it read as current or drops it off the collections
        // ladder (due / 7 / 15 / 30). The due date moves only when the person changes the terms on the revision
        // (dvRevisionTerms) or types a due date, as on any invoice.
        n.originalDate = d.originalDate || d.date || "";
        "invoice" === n.type && d.due && (n.due = d.due);
        "function" == typeof docMark && docMark(n);
        save();
      }
    } catch (e) {}
    return n;
  };
}
// The terms changed on a draft revision: its due date is worked out from the revision's own date and the new terms
// (cxDueFor, the one terms source). Terms that state the same number of days as the invoice it replaces (a reworded
// "Net 15") change nothing: the original's due date stands. The move is written to the invoice's trail.
function dvRevisionTerms(c, d) {
  if (!c || !d || "invoice" !== d.type || !d.revisionOf || "draft" !== d.status || "function" != typeof cxDueFor || "function" != typeof cxTermsDays) return !1;
  const o = (c.invoices || []).find((x) => x.number === d.revisionOf && x.id !== d.id),
    days = cxTermsDays(d.terms),
    was = d.due || "",
    same = null == days || (o && days === cxTermsDays(o.terms)),
    // back to the original's days after a move: the original's due date again; a due date typed by hand is left alone
    to = same ? (d.dueByTerms && o && o.due) || was : cxDueFor(d.date, d.terms);
  if (!to || to === was) return !1;
  (d.due = to), same ? delete d.dueByTerms : (d.dueByTerms = !0);
  try {
    docAudit(c, d, "due-moved", `terms changed to "${d.terms || ""}": due ${fmtL(was)} becomes ${fmtL(to)}${o ? `; ${o.number} was due ${fmtL(o.due)}` : ""}`);
  } catch (e) {}
  return save(), !0;
}
// the editor's Terms field (wireDocEditor writes the value first, on the field itself; this hears the same change after)
document.addEventListener("change", (e) => {
  try {
    const el = e.target;
    if (!el || !el.dataset || "terms" !== el.dataset.d || "undefined" == typeof docOpen || !docOpen || "invoice" !== docOpen.kind) return;
    const root = el.closest && el.closest('[id^="doc-"]'),
      c = (DB.clients || []).find((x) => (x.invoices || []).some((i) => i.id === docOpen.id)),
      d = c && c.invoices.find((i) => i.id === docOpen.id);
    if (!d || (root && root.id !== "doc-" + d.id)) return;
    if (dvRevisionTerms(c, d)) {
      const due = root && root.querySelector('[data-d="due"]');
      due && (due.value = d.due);
      toast(`Due ${fmtL(d.due)}: worked out from ${d.number}'s date and its new terms`);
    }
  } catch (x) {
    console.warn("docview: revision terms", x);
  }
});
// A draft that has never been sent: its due date follows its date and terms (billing review 11-15, S2-11: a new date
// left the due date where it was). A due date typed by hand stays; a sent invoice and a revision keep theirs (a
// revision keeps the original's due date, Alan's rule of 11-13, and moves only with new terms, dvRevisionTerms).
document.addEventListener("change", (e) => {
  try {
    const el = e.target,
      f = el && el.dataset && el.dataset.d;
    if (!["date", "terms", "due"].includes(f) || "undefined" == typeof docOpen || !docOpen || "invoice" !== docOpen.kind) return;
    const root = el.closest && el.closest('[id^="doc-"]'),
      c = (DB.clients || []).find((x) => (x.invoices || []).some((i) => i.id === docOpen.id)),
      d = c && c.invoices.find((i) => i.id === docOpen.id);
    if (!d || (root && root.id !== "doc-" + d.id) || "draft" !== d.status || d.sentAt || d.revisionOf || "function" != typeof cxDueFor) return;
    if ("due" === f) return void (d.dueTyped = !0);
    if (d.dueTyped || !d.date) return;
    const to = cxDueFor(d.date, d.terms);
    if (!to || to === d.due) return;
    d.due = to;
    const due = root && root.querySelector('[data-d="due"]');
    due && (due.value = to);
    save();
    toast(`Due ${fmtL(to)}: worked out from ${d.number}'s date and terms`);
  } catch (x) {
    console.warn("docview: draft due", x);
  }
});
// A revision asks for a billed-ahead reason only for the lines it bills further than the invoice it replaces: one that
// changes a description, and no amount, bills nothing further and is not asked (re-review, 11-13).
if ("function" == typeof pbFurther) {
  const base = pbFurther;
  pbFurther = function (c, d) {
    const F = base.apply(this, arguments) || [];
    try {
      if (!F.length || !d || !d.revisionOf) return F;
      const o = (c.invoices || []).find((x) => x.number === d.revisionOf && x.id !== d.id);
      if (!o) return F;
      return F.filter((x) => {
        const ol = (o.lines || []).find((y) => y.id === x.l.revOfLine);
        return !ol || (+x.l.pct || 0) > (+ol.pct || 0) + 0.005 || Math.abs((+x.l.scheduled || 0) - (+ol.scheduled || 0)) > 0.005;
      });
    } catch (e) {
      return F;
    }
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
    prior = dvCreditsOn(c, inv),
    chain = dvChain(c, inv),
    // a line and the lines it copies back through the revisions (revOfLine): one credit counts against all of them
    roots = (l) => {
      const out = new Set([l.id]);
      let cur = l;
      for (let i = 1; i < chain.length && cur && cur.revOfLine; i++) {
        out.add(cur.revOfLine);
        cur = (chain[i].lines || []).find((y) => y.id === cur.revOfLine);
      }
      return out;
    };
  return (inv.lines || [])
    .map((l) => {
      const ids = roots(l),
        amt = lineAmount(l, inv),
        done = r2(-prior.reduce((a, x) => a + (x.lines || []).filter((y) => ids.has(y.creditOfLine)).reduce((s, y) => s + lineAmount(y, x), 0), 0));
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
  // a credit over the company's limit (DB.company.creditApprovalOver, $1,000 unless Settings say otherwise) is the
  // owner's to approve: it waits in the register, with the lines and the reason, and is issued only on that yes
  const over = dvCreditLimit(),
    X0T = docTotal({ type: "invoice", mode: sov ? "sov" : "items", lines: lines, taxRate: +inv.taxRate || 0, retainagePct: +inv.retainagePct || 0, discount: inv.discount && "pct" === inv.discount.type ? inv.discount : { type: "pct", value: 0 } }),
    X0 = r2(-X0T.total);
  if (X0 > over + 0.005 && "owner" !== role() && !o.approvedAsk) {
    const ask = { id: uid("cc"), kind: "credit-ask", clientId: c.id, projectId: inv.projectId || "", invoiceId: inv.id, invoiceNumber: inv.number, picks: (picks || []).map((p) => ({ lineId: p.lineId, amount: r2(+p.amount || 0) })), amount: X0, gross: r2(Math.abs(X0T.sub - X0T.disc)), ret: r2(Math.abs(X0T.ret || 0)), tax: r2(Math.abs(X0T.tax || 0)), why: w, status: "proposed", by: dvWho(), byRole: role(), at: today() };
    (DB.clientCredits = DB.clientCredits || []).push(ask);
    apStamp("client-credit", ask, `credit of ${money(X0)} on ${inv.number} proposed by ${ask.by}`, "proposed", { after: { amount: X0, invoice: inv.number }, note: w });
    docAudit(c, inv, "credit-proposed", `${money(X0)}: ${w} (over ${money(over)}: the owner approves)`);
    return save(), { ok: !0, ask: ask, total: X0 };
  }
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
    preparedBy: o.approvedAsk ? o.approvedAsk.by : dvWho(),
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
function dvCreditLimit() {
  const v = DB.company && DB.company.creditApprovalOver;
  return null == v || "" === v || isNaN(+v) ? 1e3 : +v;
}
const dvMayApproveCredit = (a) => "owner" === role() && !(a.by && String(a.by).toLowerCase() === String(dvWho()).toLowerCase());
// a credit's amount, read the whole way: the work credited, the sales tax and the retainage it reverses, and the net
// that comes off the balance (a memo from its own totals; an ask from what was stored when it was asked)
function dvCreditBreakOf(x) {
  const t = docTotal(x);
  return { gross: r2(Math.abs(t.sub - t.disc)), tax: r2(Math.abs(t.tax || 0)), ret: r2(Math.abs(t.ret || 0)), net: r2(Math.abs(t.total)) };
}
function dvCreditBreakAsk(inv, a) {
  const gross = null != a.gross ? +a.gross : r2((a.picks || []).reduce((s, p) => s + (+p.amount || 0), 0)),
    ret = null != a.ret ? +a.ret : r2((gross * (+(inv && inv.retainagePct) || 0)) / 100);
  return { gross: gross, ret: ret, tax: null != a.tax ? +a.tax : Math.max(0, r2(+a.amount - gross + ret)), net: r2(+a.amount) };
}
// to the cent: what a person approves, and a credit read the whole way, is never rounded to the dollar
const dvM = (v) => ("function" == typeof money2 ? money2(v) : money(v));
function dvCreditBreakWords(B) {
  const parts = [B.tax > 0.005 ? `plus ${dvM(B.tax)} sales tax` : "", B.ret > 0.005 ? `less ${dvM(B.ret)} retainage reversed` : ""].filter(Boolean);
  return parts.length ? `${dvM(B.net)} (${dvM(B.gross)} of work credited, ${parts.join(", ")})` : dvM(B.net);
}
// Approve, confirmed: the sheet restates what is credited, to whom and on which invoice, then one Approve
function dvCreditConfirm(c, id) {
  const a = dvCreditAsks(c).find((x) => x.id === id);
  if (!a || "proposed" !== a.status) return toast("That credit is not waiting on anyone");
  if (!dvMayApproveCredit(a)) return toast("A credit over the limit is approved by the owner, never by the person who asked for it");
  const inv = (c.invoices || []).find((x) => x.id === a.invoiceId),
    B = dvCreditBreakAsk(inv, a);
  mbModal(
    `Approve the Credit of ${dvM(B.net)}`,
    `<p style="margin:0 0 8px" data-dvconfirm>Credit ${esc(dvM(B.net))} to ${esc(c.name)} on invoice ${esc(a.invoiceNumber || (inv && inv.number) || "")}: ${esc(dvM(B.gross))} of work credited${B.tax > 0.005 ? `, plus ${esc(dvM(B.tax))} sales tax` : ""}${B.ret > 0.005 ? `, less ${esc(dvM(B.ret))} retainage reversed` : ""}.</p><p class="small muted" style="margin:0">Asked by ${esc(a.by)}: ${esc(a.why)}. A credit memo is issued and applied to the invoice; no money moves.</p>`,
    { submit: "Approve", onSubmit: () => void dvCreditDecide(c, id, !0) },
  );
}
// the owner's yes or no on a credit over the limit; the person who asked never decides it
function dvCreditDecide(c, id, yes, note) {
  const a = dvCreditAsks(c).find((x) => x.id === id);
  if (!a || "proposed" !== a.status) return toast("That credit is not waiting on anyone"), null;
  if (!dvMayApproveCredit(a)) return toast("A credit over the limit is approved by the owner, never by the person who asked for it"), null;
  const inv = (c.invoices || []).find((x) => x.id === a.invoiceId),
    by = dvWho();
  if (!yes) {
    if (void 0 === note) {
      mbModal(`Decline the Credit of ${money(a.amount)}`, mbF("Why", mbIn("why", "", "e.g. the client accepted the price")), {
        submit: "Decline",
        onSubmit: (v) => (v.why ? void dvCreditDecide(c, id, !1, v.why) : (toast("Say why"), !1)),
      });
      return null;
    }
    Object.assign(a, { status: "declined", decidedBy: by, decidedAt: today(), declineWhy: note });
    apStamp("client-credit", a, `credit declined by ${by}`, "declined", { before: "proposed", after: "declined", note: note });
    inv && docAudit(c, inv, "credit-declined", `${money(a.amount)}: ${note}`);
    save(), render();
    rcToast(`Credit of ${money(a.amount)} declined: ${note}`, inv ? [{ label: "Open", run: () => dvOpen("invoice", inv.id, c.id) }] : null);
    return a;
  }
  const R = inv ? dvCreditCreate(c, inv, a.picks, a.why, { approvedAsk: a }) : { ok: !1, why: "The invoice is not on file" };
  if (!R.ok || !R.cm) return toast(R.why || "Not issued"), null;
  Object.assign(a, { status: "approved", decidedBy: by, decidedAt: today(), creditMemoId: R.cm.id });
  apStamp("client-credit", a, `credit of ${money(a.amount)} approved by ${by}`, "approved", { by: by, approve: !0, before: "proposed", after: "approved", note: a.why });
  render();
  dvOpen("credit", R.cm.id, c.id);
  rcToast(`${R.cm.number} issued: ${money(R.total)} credited on ${inv.number}, asked by ${a.by}, approved by ${by}`, [{ label: "Open", run: () => dvOpen("credit", R.cm.id, c.id) }]);
  return R.cm;
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
        if (R.ask)
          return void (dvOpen("invoice", inv.id, c.id),
          rcToast(`A credit of ${money(R.total)} on ${inv.number} is over ${money(dvCreditLimit())}: it waits on the owner in Approvals, nothing is credited yet`, [{ label: "Open", run: () => dvOpen("invoice", inv.id, c.id) }]));
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
// credit the client holds on the account (an overpayment, a credit memo held for the next invoice): what a refund
// draws down first
function dvOnAccount(c) {
  return clientCredit(c).onAccount;
}
// Where a refund goes, in the words the confirm sheet uses, everywhere it is said (the note, the toasts, the trail,
// Approvals): "<amount> to <client>, to the <account> ending 4471 it was paid from", never "to Wire from Chase"
function dvRefundAcctWords(f) {
  const a = (DB.accounts || []).find((x) => x.id === f.acctId);
  return a ? `the ${a.name}${/account/i.test(a.name || "") ? "" : " account"}${a.last4 ? " ending " + a.last4 : ""}` : "the account";
}
function dvRefundWords(c, f) {
  return `${dvM(f.amount)} to ${(c && c.name) || "the client"}, to ${dvRefundAcctWords(f)} it was paid from`;
}
// What can be refunded on an invoice against one of its payments: the credit the client holds on the account when
// there is any, otherwise what this invoice is overpaid by; never more than the bank has of that payment (x.left), and
// less what is already proposed. With neither, a refund goes out only with a credit on the invoice for the same
// amount (withCredit), which is what makes the money the client's to have back.
function dvRefundLimit(c, inv, x, withCredit) {
  const cash = x && x.banked ? Math.max(0, x.left) : 0,
    asked = (f) => "proposed" === f.status,
    onAcct = dvOnAccount(c),
    over = Math.max(0, r2(invoicePaid(c, inv) - docTotal(inv).total));
  // what the account can still give is clientCredit's one reading: on account, less what is applied (already off
  // it) and less every refund proposed against it (11-15: a $900 credit was both proposed for refund and applied)
  if (onAcct > 0.005) return { basis: "account", has: onAcct, max: r2(Math.max(0, Math.min(cash, clientCredit(c).available))) };
  if (over > 0.005) return { basis: "overpaid", has: over, max: r2(Math.max(0, Math.min(cash, over - dvRefunds(c).filter((f) => asked(f) && f.invoiceId === inv.id).reduce((a, f) => a + (+f.amount || 0), 0)))) };
  return { basis: "credit", has: 0, max: withCredit ? r2(cash) : 0 };
}
// Approve, confirmed: the sheet says the amount, who it goes to and the account it goes out of, the right way round
function dvRefundConfirm(c, id) {
  const f = dvRefunds(c).find((x) => x.id === id);
  if (!f || "proposed" !== f.status) return toast("That refund is not waiting on anyone");
  if (!dvMayApproveRefund(f)) return toast(`A refund is approved by ${dvRefundApproverWord()}, never by the person who proposed it`);
  const src = (c.payments || []).find((p) => p.id === f.paymentId),
    a = (DB.accounts || []).find((x) => x.id === f.acctId),
    acct = a ? `${a.name}${a.last4 ? " ending " + a.last4 : ""}` : "the account it came into",
    onAcct = dvOnAccount(c),
    how = onAcct >= f.amount - 0.05 ? `It draws down the ${dvM(onAcct)} credit on the account; nothing billed changes.` : f.withCredit ? `A credit memo on ${f.invoiceNumber} goes with it, so nothing is owed again; it reduces what was billed.` : `${dvM(f.amount)} is owed again on ${f.invoiceNumber}.`;
  mbModal(
    `Approve the Refund of ${dvM(f.amount)}`,
    `<p style="margin:0 0 8px" data-dvconfirm>Refund of ${esc(dvRefundWords(c, f))}${src ? `: their ${esc(f.method || "payment")} of ${esc(fmtL(src.date))} on ${esc(f.invoiceNumber)}` : ""}.</p><p class="small muted" style="margin:0">${esc(how)} Proposed by ${esc(f.by)}: ${esc(f.why)}. It reads "approved, not in the bank" until its bank line is matched.</p>`,
    { submit: "Approve", onSubmit: () => void dvRefundDecide(c, id, !0) },
  );
}
function dvRefundPropose(c, inv, paymentId, amount, why, withCredit) {
  if (!DV_CREDIT_ROLES.includes(role())) return { ok: !1, why: "Billing, the Controller or the Owner proposes a refund" };
  const x = dvRefundable(c, inv).find((y) => y.p.id === paymentId),
    amt = r2(+amount || 0),
    w = String(why || "").trim();
  if (!x) return { ok: !1, why: "Pick a payment received on this invoice" };
  if (!x.banked) return { ok: !1, why: `That payment is ${PAY_NOT_IN_BANK}: only money the bank has is refunded` };
  if (!(amt > 0) || amt > x.left + 0.005) return { ok: !1, why: `Refund between $0.01 and ${money(x.left)} of that payment` };
  const L = dvRefundLimit(c, inv, x, withCredit);
  if (amt > L.max + 0.005)
    return {
      ok: !1,
      why:
        "account" === L.basis
          ? `${dvM(L.has)} is on the account${L.max < L.has - 0.005 ? ` and ${dvM(L.max)} of it can still be refunded` : ""}: refund ${dvM(L.max)} at most`
          : "overpaid" === L.basis
            ? `${inv.number} is overpaid by ${dvM(L.has)}: refund ${dvM(L.max)} at most`
            : `Nothing is on the account and ${inv.number} is not overpaid: credit ${inv.number} for the amount to refund it`,
    };
  if (!w) return { ok: !1, why: "Say why the money goes back" };
  const f = {
    id: uid("cc"),
    kind: "refund",
    clientId: c.id,
    projectId: inv.projectId || "",
    invoiceId: inv.id,
    invoiceNumber: inv.number,
    paymentId: x.p.id,
    amount: amt,
    acctId: dvPayAcctId(x.p),
    method: x.p.method || "",
    to: dvPayAcct(x.p),
    why: w,
    withCredit: !!withCredit,
    basis: L.basis,
    status: "proposed",
    by: dvWho(),
    byRole: role(),
    at: today(),
    approver: dvRefundApprover(),
  };
  (DB.clientCredits = DB.clientCredits || []).push(f);
  apStamp("client-refund", f, `refund of ${money(amt)} proposed by ${f.by}`, "proposed", { after: { amount: amt, paymentId: x.p.id, to: f.to }, note: w });
  docAudit(c, inv, "refund-proposed", `${dvRefundWords(c, f)}: ${w}`);
  return save(), { ok: !0, f: f };
}
// Approved: a negative payment tied to the payment it returns (refundOf). With a credit the invoice stays settled: the
// credit memo puts the amount on the account and the refund draws it out; without one the amount is owed again.
function dvRefundDecide(c, id, yes, note) {
  const f = dvRefunds(c).find((x) => x.id === id);
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
  // a refund draws down credit already on the account first; a credit memo is written only when it was asked for and
  // the account does not hold the amount (its reason names the invoice in plain words, never a record id)
  if (f.withCredit && inv && dvOnAccount(c) < f.amount - 0.05) {
    const R = dvCreditCreate(c, inv, dvCreditLump(c, inv, f.amount), `Refund on ${inv.number}: ${f.why}`, { onAccount: !0 });
    R.ok ? (f.creditMemoId = R.cm.id) : toast(`No credit memo: ${R.why}`);
  }
  const fromAcct = dvOnAccount(c) >= f.amount - 0.05,
    rec = { id: uid("py"), date: today(), amount: -f.amount, method: f.method || "Refund", ref: `Refund ${f.invoiceNumber}`, acctId: f.acctId, invoiceId: fromAcct ? "" : f.invoiceId, unapplied: fromAcct, refundOf: f.paymentId, refundId: f.id, why: f.why, recordedBy: by, recordedAt: appNowIso(), note: `refund of ${money(f.amount)} to ${f.to}: ${f.why}` };
  c.payments.push(rec);
  Object.assign(f, { status: "approved", decidedBy: by, decidedAt: today(), paymentRecId: rec.id });
  apStamp("client-refund", f, `refund of ${money(f.amount)} approved by ${by}`, "approved", { by: by, approve: !0, before: "proposed", after: "approved", note: f.why });
  if (inv && !["void", "draft"].includes(inv.status) && !fromAcct) {
    const paid = invoicePaid(c, inv);
    inv.status = paid >= docTotal(inv).total - 0.005 ? "paid" : paid > 0.005 ? "partial" : inv.due && inv.due < today() ? "overdue" : "sent";
  }
  inv && docAudit(c, inv, "refund-approved", dvRefundWords(c, f));
  (c.activity = c.activity || []).push({ t: nowStamp(), by: by, text: `Refund of ${dvRefundWords(c, f)} approved: ${f.why}` });
  save(), render();
  rcToast(`Refund of ${dvRefundWords(c, f)} approved; it reads "approved, not in the bank" until the bank line is matched`, inv ? [{ label: "Open", run: () => dvOpen("invoice", inv.id, c.id) }] : null);
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
  const banked = R.filter((x) => x.banked),
    x0 = banked[0] || R[0],
    L0 = dvRefundLimit(c, inv, x0, !1);
  mbModal(
    `Refund on ${esc(inv.number)}`,
    `<p class="small" style="margin:0 0 8px">A refund is a proposal until ${esc(dvRefundApproverWord())} approves it. It goes back only to the account the payment came from, and reads "approved, not in the bank" until its bank line is matched.</p>
    ${banked.length ? "" : `<div class="note warn">No payment on ${esc(inv.number)} is in the bank yet; only money the bank has is refunded.</div>`}
    ${mbF("Payment It Returns", mbSel("pay", R.map((x) => [x.p.id, `${fmtL(x.p.date)} · ${money(+x.p.amount)} · ${dvPayAcct(x.p)}${x.banked ? "" : " (not in the bank)"}${x.left < +x.p.amount - 0.005 ? ` · ${money(x.left)} left` : ""}`]), (banked[0] || R[0]).p.id))}
    ${mbF("Amount", mbIn("amount", L0.max > 0.005 ? String(L0.max) : "", "", "number"))}
    ${mbF("Why", mbIn("why", "", "e.g. the client overpaid; the tile line was credited"))}
    ${
      // a refund returns credit the client holds or overpaid: with credit on the account it draws that down, with no
      // credit memo and nothing billed changed; only with none is crediting the invoice offered, unticked, said plainly
      "account" === L0.basis
        ? `<div class="small" style="margin-top:8px" data-dvonacct>${esc(dvM(L0.has))} is held as credit on ${esc(c.name)}'s account: the refund draws it down, with no credit memo, and nothing billed changes. ${esc(dvM(L0.max))} at most can be refunded${L0.max < L0.has - 0.005 ? " (the rest is already asked for, or is more than the bank has of this payment)" : ""}.</div>`
        : "overpaid" === L0.basis
          ? `<div class="small" style="margin-top:8px" data-dvoverpaid>${esc(inv.number)} is overpaid by ${esc(dvM(L0.has))}: ${esc(dvM(L0.max))} at most can be refunded, with no credit memo, and nothing billed changes.</div>`
          : `<div class="small" style="margin-top:8px" data-dvnothing>Nothing is on ${esc(c.name)}'s account and ${esc(inv.number)} is not overpaid, so there is nothing to refund as it stands.</div><label class="small" style="display:flex;gap:8px;align-items:flex-start;margin-top:8px"><input type="checkbox" data-f="credit"> <span>Credit ${esc(inv.number)} for the amount and refund it: a credit memo that reduces what was billed. Without it nothing is refunded.</span></label>`
    }`,
    {
      submit: "Propose the Refund",
      onSubmit: (f) => {
        const x = dvRefundPropose(c, inv, f.pay, f.amount, f.why, f.credit);
        if (!x.ok) return toast(x.why), !1;
        render();
        dvOpen("invoice", inv.id, c.id);
        rcToast(`Refund of ${dvRefundWords(c, x.f)} proposed: it waits on ${dvRefundApproverWord()} in Approvals`, [{ label: "Open", run: () => dvOpen("invoice", inv.id, c.id) }]);
      },
    },
  );
}
// the bank lines that can be this refund: money out of the account that paid, the same amount, from the approval on
function dvRefundLines(f) {
  const used = new Set(dvRefunds(null).map((x) => x.txnId).filter(Boolean));
  return (DB.txns || []).filter(
    (t) => +t.amt < 0 && Math.abs(-t.amt - f.amount) < 0.01 && (!f.acctId || t.acct === f.acctId) && !used.has(t.id) && !t.billId && !(t.match && (t.match.billId || t.match.paymentId)) && (!f.decidedAt || (t.date || "") >= addDaysIso(f.decidedAt, -3)),
  );
}
function addDaysIso(d, n) {
  const x = new Date(d + "T12:00:00");
  return x.setDate(x.getDate() + n), x.toISOString().slice(0, 10);
}
function dvRefundMatch(c, id, txnId) {
  const f = dvRefunds(c).find((x) => x.id === id),
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
  const f = dvRefunds(c).find((x) => x.id === id);
  if (!f) return;
  const L = dvRefundLines(f);
  if (!L.length) return toast(`No ${dvM(f.amount)} out of ${dvRefundAcctWords(f)} is in the bank's lines yet; it stays "approved, not in the bank" until it is`);
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
if ("object" == typeof DELEGATION) DELEGATION.creditmemo = { role: "owner", rule: "a credit to a client over the company limit (DB.company.creditApprovalOver, $1,000) is the owner's to approve, never the person who asked for it", who: () => "owner" };
if ("object" == typeof APPR_CHIPS && Array.isArray(APPR_CHIPS) && !APPR_CHIPS.some(([k]) => "creditmemo" === k)) APPR_CHIPS.splice(Math.max(0, APPR_CHIPS.length - 1), 0, ["creditmemo", "Credits"]);
if ("function" == typeof mApprovals) {
  const base = mApprovals;
  mApprovals = function (opts) {
    const out = base.apply(this, arguments);
    try {
      if (!Array.isArray(out) || !((opts && opts.everyone) || role() === dvRefundApprover())) return out;
      (DB.clients || []).forEach((c) =>
        dvRefunds(c)
          .filter((f) => "proposed" === f.status)
          .forEach((f) =>
            out.push({
              kind: "refund",
              id: f.id,
              sev: "warn",
              n: money(f.amount),
              title: `Refund ${money(f.amount)} to ${c.name}`,
              detail: `${f.invoiceNumber} · ${dvRefundWords(c, f)} · ${f.why} · proposed by ${f.by}`,
              yes: "Review the Refund",
              who: dvRefundApprover(),
              due: today(),
              open: { view: "billing", dvInvoice: f.invoiceId, dvClient: c.id },
            }),
          ),
      );
      (opts && opts.everyone) || "owner" === role()
        ? (DB.clients || []).forEach((c) =>
            dvCreditAsks(c)
              .filter((a) => "proposed" === a.status)
              .forEach((a) =>
                out.push({
                  kind: "creditmemo",
                  id: a.id,
                  sev: "warn",
                  n: money(a.amount),
                  title: `Credit ${money(a.amount)} to ${c.name}`,
                  // the amount read the whole way (work credited, tax, retainage reversed, net), as the note and the confirm sheet say it
                  detail: `${a.invoiceNumber} · ${dvCreditBreakWords(dvCreditBreakAsk((c.invoices || []).find((x) => x.id === a.invoiceId), a))} · ${a.why} · over the ${money(dvCreditLimit())} limit · asked by ${a.by}`,
                  yes: "Review the Credit",
                  who: "owner",
                  due: today(),
                  open: { view: "billing", dvInvoice: a.invoiceId, dvClient: c.id },
                }),
              ),
          )
        : null;
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
    // a transfer to a revision stands as the record it moves stood: in the bank or not, and never twice
    if (py && py.xferOf) {
      const o = ((c && c.payments) || []).find((x) => x.id === py.xferOf);
      return o && +o.amount ? r2(payBankedAmt(c, o) * ((+py.amount || 0) / +o.amount)) : 0;
    }
    if (py && py.refundId) return py.txnId ? r2(+py.amount || 0) : 0;
    // an application of credit on account (and its draw) stands as the payment it draws on stood, in proportion
    if (py && py.creditApply) {
      const o = ((c && c.payments) || []).find((x) => x.id === py.creditApply);
      return o && +o.amount ? r2(payBankedAmt(c, o) * ((+py.amount || 0) / +o.amount)) : 0;
    }
    return base.apply(this, arguments);
  };
}
if ("function" == typeof glPaymentLines) {
  const base = glPaymentLines;
  glPaymentLines = function (c, p) {
    if (p && p.creditApply) {
      // the application's own journal: the client's credit on account (a credit in receivables, where an unapplied
      // payment posts) moves onto the invoice it pays, in receivables; the draw posts nothing of its own
      if (p.unapplied || !+p.amount) return [];
      const inv = (c.invoices || []).find((i) => i.id === p.invoiceId),
        src = (c.payments || []).find((x) => x.id === p.creditApply),
        on = { projectId: "", partyType: "client", partyId: c.id, memo: `credit on account (payment ${src ? fmtL(src.date) + " " + money(+src.amount || 0) : p.creditApply})` },
        to = { projectId: inv ? inv.projectId : "", partyType: "client", partyId: c.id, memo: `applied to ${inv ? inv.number : "the invoice"}` };
      // a reversal of an application (negative) posts the same lines the other way round
      const x = Math.abs(+p.amount);
      return +p.amount > 0 ? [glL("1100", x, 0, on), glL("1100", 0, x, to)] : [glL("1100", 0, x, on), glL("1100", x, 0, to)];
    }
    return p && (p.cmApply || p.xferOf) ? [] : base.apply(this, arguments);
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
// One layout (owner, 11-15). The document is rendered in a page-width frame with the same stylesheet the print uses
// (CX_CSS plus CX_PAGED_CSS), and every word, band, rule and the firm's mark is placed where that render put it: the
// writer reads the boxes, it does not re-lay the text out. So a section's title sits at the left of its band and its
// subtotal in the Amount column, an item is its own line above its lighter description, and nothing can land on top
// of anything else unless it does in the render. Pages break only between rows (a row, a section band with its first
// row, the acceptance with its signature never split), the column header repeats on each page a table continues onto,
// and every page carries the document's number and "Page N of M" at the foot.
// Fonts are the PDF's standard Times (for the document's serif) and Helvetica (for its sans), each line set to the
// exact width the render gave it, so columns stay true on every device. Nothing is loaded from a network.
const DV_PDF = { W: 612, H: 792, ML: 50, MR: 50, MT: 54, MB: 50, PX: 640, FOOT: 26 };
// a page's usable height in px of a render that is px wide (a wide pay application renders wider and prints smaller)
const DV_PDF_FULL = (px) => (DV_PDF.H - DV_PDF.MT - DV_PDF.MB - DV_PDF.FOOT) / ((DV_PDF.W - DV_PDF.ML - DV_PDF.MR) / (px || DV_PDF.PX));
// Adobe's widths (1/1000 em) of the standard fonts for WinAnsi codes 32 to 255, two base-36 digits each
const DV_PDF_AFM = {
  "Helvetica": "7q7q9vfgfgopij5b9999atg87q997q7qfgfgfgfgfgfgfgfgfgfg7q7qg8g8g8fgs7ijijk2k2ijgzlmk27qdwijfgn5k2lmijlmk2ijgzk2ijq8ijijgz7q7q7qd1fg99fgfgdwfgfg7qfgfg6666dw66n5fgfgfgfg99dw7qfgdwk2dwdwdw9a789ag800000066fg99rsfgfg99rsij99rs00gz0000666699999qfgrs99rsdw99q800dwij7q99fgfgfgfg78fg99khaafgg800kh99b4g8999999fgex7q9999a5fgn6n6n6gzijijijijijijrsk2ijijijij7q7q7q7qk2k2lmlmlmlmlmg8lmk2k2k2k2ijijgzfgfgfgfgfgfgopdwfgfgfgfg7q7q7q7qfgfgfgfgfgfgfgg8gzfgfgfgfgdwfgdw",
  "Helvetica-Bold": "7q99d6fgfgopk26m9999atg87q997q7qfgfgfgfgfgfgfgfgfgfg9999g8g8g8gzr3k2k2k2k2ijgzlmk27qfgk2gzn5k2lmijlmk2ijgzk2ijq8ijijgz997q99g8fg99fggzfggzfg99gzgz7q7qfg7qopgzgzgzgzatfg99gzfglmfgfgdwat7satg80000007qfgdwrsfgfg99rsij99rs00gz00007q7qdwdw9qfgrs99rsfg99q800dwij7q99fgfgfgfg7sfg99khaafgg800kh99b4g8999999gzfg7q9999a5fgn6n6n6gzk2k2k2k2k2k2rsk2ijijijij7q7q7q7qk2k2lmlmlmlmlmg8lmk2k2k2k2ijijgzfgfgfgfgfgfgopfgfgfgfgfg7q7q7q7qgzgzgzgzgzgzgzg8gzgzgzgzgzfggzfg",
  "Helvetica-Oblique": "7q7q9vfgfgopij5b9999atg87q997q7qfgfgfgfgfgfgfgfgfgfg7q7qg8g8g8fgs7ijijk2k2ijgzlmk27qdwijfgn5k2lmijlmk2ijgzk2ijq8ijijgz7q7q7qd1fg99fgfgdwfgfg7qfgfg6666dw66n5fgfgfgfg99dw7qfgdwk2dwdwdw9a789ag800000066fg99rsfgfg99rsij99rs00gz0000666699999qfgrs99rsdw99q800dwij7q99fgfgfgfg78fg99khaafgg800kh99b4g8999999fgex7q9999a5fgn6n6n6gzijijijijijijrsk2ijijijij7q7q7q7qk2k2lmlmlmlmlmg8lmk2k2k2k2ijijgzfgfgfgfgfgfgopdwfgfgfgfg7q7q7q7qfgfgfgfgfgfgfgg8gzfgfgfgfgdwfgdw",
  "Helvetica-BoldOblique": "7q99d6fgfgopk26m9999atg87q997q7qfgfgfgfgfgfgfgfgfgfg9999g8g8g8gzr3k2k2k2k2ijgzlmk27qfgk2gzn5k2lmijlmk2ijgzk2ijq8ijijgz997q99g8fg99fggzfggzfg99gzgz7q7qfg7qopgzgzgzgzatfg99gzfglmfgfgdwat7satg80000007qfgdwrsfgfg99rsij99rs00gz00007q7qdwdw9qfgrs99rsfg99q800dwij7q99fgfgfgfg7sfg99khaafgg800kh99b4g8999999gzfg7q9999a5fgn6n6n6gzk2k2k2k2k2k2rsk2ijijijij7q7q7q7qk2k2lmlmlmlmlmg8lmk2k2k2k2ijijgzfgfgfgfgfgfgopfgfgfgfgfg7q7q7q7qgzgzgzgzgzgzgzg8gzgzgzgzgzfggzfg",
  "Times-Roman": "6y99bcdwdwn5lm509999dwfo6y996y7qdwdwdwdwdwdwdwdwdwdw7q7qfofofoccplk2ijijk2gzfgk2k299atk2gzopk2k2fgk2ijfggzk2k2q8k2k2gz997q99d1dw99ccdwccdwcc99dwdw7q7qdw7qlmdwdwdwdw99at7qdwdwk2dwdwccdc5kdcf100000099dwccrsdwdw99rsfg99op00gz00009999cccc9qdwrs99r8at99k200cck26y99dwdwdwdw5kdw99l47odwfo00l499b4fo8c8c99dwcl6y998c8mdwkukukucck2k2k2k2k2k2opijgzgzgzgz99999999k2k2k2k2k2k2k2fok2k2k2k2k2k2fgdwccccccccccccijcccccccccc7q7q7q7qdwdwdwdwdwdwdwfodwdwdwdwdwdwdwdw",
  "Times-Bold": "6y99ffdwdwrsn57q9999dwfu6y996y7qdwdwdwdwdwdwdwdwdwdw9999fufufudwpuk2ijk2k2ijgzlmlmatdwlmijq8k2lmgzlmk2fgijk2k2rsk2k2ij997q99g5dw99dwfgccfgcc99dwfg7q99fg7qn5fgdwfgfgccat99fgdwk2dwdwccay64ayeg00000099dwdwrsdwdw99rsfg99rs00ij00009999dwdw9qdwrs99rsat99k200cck26y99dwdwdwdw64dw99kr8cdwfu00kr99b4fu8c8c99fgf06y998c96dwkukukudwk2k2k2k2k2k2rsk2ijijijijatatatatk2k2lmlmlmlmlmfulmk2k2k2k2k2gzfgdwdwdwdwdwdwk2cccccccccc7q7q7q7qdwfgdwdwdwdwdwfudwfgfgfgfgdwfgdw",
  "Times-Italic": "6y99bodwdwn5lm5y9999dwir6y996y7qdwdwdwdwdwdwdwdwdwdw9999iririrdwpkgzgzijk2gzgzk2k299ccijfgn5ijk2gzk2gzdwfgk2gzn5gzfgfgat7qatbqdw99dwdwccdwcc7qdwdw7q7qcc7qk2dwdwdwdwatat7qdwccijccccatb47nb4f100000099dwfgopdwdw99rsdw99q800fg00009999fgfg9qdwop99r8at99ij00atfg6yatdwdwdwdw7ndw99l47odwir00l499b4ir8c8c99dwej6y998c8mdwkukukudwgzgzgzgzgzgzopijgzgzgzgz99999999k2ijk2k2k2k2k2irk2k2k2k2k2fggzdwdwdwdwdwdwdwijcccccccccc7q7q7q7qdwdwdwdwdwdwdwirdwdwdwdwdwccdwcc",
  "Times-BoldItalic": "6yatffdwdwn5lm7q9999dwfu6y996y7qdwdwdwdwdwdwdwdwdwdw9999fufufudwn4ijijijk2ijijk2lmatdwijgzopk2k2gzk2ijfggzk2ijopijgzgz997q99fudw99dwdwccdwcc99dwfg7q7qdw7qlmfgdwdwdwatat7qfgccijdwccat9o649ofu00000099dwdwrsdwdw99rsfg99q800gz00009999dwdw9qdwrs99rsat99k200atgz6yatdwdwdwdw64dw99kr7edwgu00kr99b4fu8c8c99g0dw6y998c8cdwkukukudwijijijijijijq8ijijijijijatatatatk2k2k2k2k2k2k2fuk2k2k2k2k2gzgzdwdwdwdwdwdwdwk2cccccccccc7q7q7q7qdwfgdwdwdwdwdwfudwfgfgfgfgccdwcc",
};
const DV_PDF_FONTS = ["Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique", "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"];
const dvPdfW = (() => {
  const T = {};
  return (font) => {
    if (T[font]) return T[font];
    const s = DV_PDF_AFM[font],
      a = [];
    for (let i = 0; i < s.length; i += 2) a.push(parseInt(s.substr(i, 2), 36));
    return (T[font] = a);
  };
})();
// unicode to the WinAnsi byte the standard fonts draw; anything else falls back to its plain letter or a space
const DV_PDF_CP = { 8364: 128, 8218: 130, 402: 131, 8222: 132, 8230: 133, 8224: 134, 8225: 135, 710: 136, 8240: 137, 352: 138, 8249: 139, 338: 140, 381: 142, 8216: 145, 8217: 146, 8220: 147, 8221: 148, 8226: 149, 8211: 150, 8212: 151, 732: 152, 8482: 153, 353: 154, 8250: 155, 339: 156, 382: 158, 376: 159, 8722: 150, 8209: 45, 8239: 32, 8201: 32, 8202: 32, 8200: 32 };
function dvPdfBytesOf(str) {
  const out = [];
  for (const ch of String(str)) {
    const u = ch.codePointAt(0);
    if (u >= 32 && u < 127) out.push(u);
    else if (u >= 160 && u < 256) out.push(u);
    else if (DV_PDF_CP[u]) out.push(DV_PDF_CP[u]);
    else {
      const b = ch.normalize("NFD").charCodeAt(0);
      out.push(b >= 32 && b < 127 ? b : 32);
    }
  }
  return out;
}
const dvPdfStr = (bytes) => "(" + bytes.map((b) => (40 === b || 41 === b || 92 === b ? "\\" + String.fromCharCode(b) : b < 127 ? String.fromCharCode(b) : "\\" + b.toString(8).padStart(3, "0"))).join("") + ")";
const dvPdfWidth = (bytes, font, pt) => (bytes.reduce((a, b) => a + (dvPdfW(font)[b - 32] || 0), 0) / 1000) * pt;
function dvPdfColor(css) {
  const m = /rgba?\(([^)]+)\)/.exec(css || "");
  if (!m) return null;
  const p = m[1].split(/[\s,/]+/).filter(Boolean).map(parseFloat),
    al = p.length > 3 ? p[3] : 1;
  if (!(al > 0.01)) return null;
  // a translucent colour is drawn as it looks on white paper
  return p.slice(0, 3).map((v) => (1 - al + (al * v) / 255).toFixed(3)).join(" ");
}
function dvPdfFont(cs) {
  const fam = String(cs.fontFamily || "").split(",")[0].replace(/["']/g, "").trim().toLowerCase(),
    serif = /georgia|times|serif|garamond|palatino|cambria/.test(fam) && !/sans/.test(fam),
    bold = (parseInt(cs.fontWeight, 10) || 400) >= 600,
    it = /italic|oblique/.test(cs.fontStyle || "");
  return (serif ? 4 : 0) + (bold ? 1 : 0) + (it ? 2 : 0);
}
// a simple SVG (the firm's mark): rect, line, polyline and path with straight segments, as PDF strokes
function dvPdfSvg(svg, R0) {
  const box = svg.getBoundingClientRect(),
    vb = (svg.getAttribute("viewBox") || `0 0 ${box.width} ${box.height}`).split(/[\s,]+/).map(Number),
    kx = box.width / (vb[2] || 1),
    ky = box.height / (vb[3] || 1),
    P = (x, y) => [box.left - R0.left + (x - vb[0]) * kx, box.top - R0.top + (y - vb[1]) * ky],
    segs = [];
  svg.querySelectorAll("rect,line,polyline,polygon,path").forEach((e) => {
    const cs = getComputedStyle(e),
      stroke = dvPdfColor(cs.stroke),
      sw = (parseFloat(cs.strokeWidth) || 1) * kx,
      pts = [];
    if (!stroke) return;
    const T = e.tagName.toLowerCase(),
      n = (a) => parseFloat(e.getAttribute(a)) || 0;
    if ("rect" === T) pts.push([["M", ...P(n("x"), n("y"))], ["L", ...P(n("x") + n("width"), n("y"))], ["L", ...P(n("x") + n("width"), n("y") + n("height"))], ["L", ...P(n("x"), n("y") + n("height"))], ["Z"]]);
    else if ("line" === T) pts.push([["M", ...P(n("x1"), n("y1"))], ["L", ...P(n("x2"), n("y2"))]]);
    else if ("polyline" === T || "polygon" === T) {
      const v = (e.getAttribute("points") || "").trim().split(/[\s,]+/).map(Number),
        s = [];
      for (let i = 0; i + 1 < v.length; i += 2) s.push([i ? "L" : "M", ...P(v[i], v[i + 1])]);
      "polygon" === T && s.push(["Z"]);
      pts.push(s);
    } else {
      const tok = (e.getAttribute("d") || "").match(/[MLHVZmlhvz]|-?[\d.]+(?:e-?\d+)?/g) || [],
        s = [];
      let cx = 0,
        cy = 0,
        sx = 0,
        sy = 0,
        cmd = "";
      for (let i = 0; i < tok.length; ) {
        if (/[A-Za-z]/.test(tok[i])) cmd = tok[i++];
        const num = () => parseFloat(tok[i++]);
        if ("Z" === cmd || "z" === cmd) {
          s.push(["Z"]), (cx = sx), (cy = sy);
          continue;
        }
        const rel = cmd === cmd.toLowerCase(),
          C = cmd.toUpperCase();
        if ("H" === C) cx = (rel ? cx : 0) + num();
        else if ("V" === C) cy = (rel ? cy : 0) + num();
        else {
          const x = num(),
            y = num();
          (cx = (rel ? cx : 0) + x), (cy = (rel ? cy : 0) + y);
        }
        "M" === C ? ((sx = cx), (sy = cy), s.push(["M", ...P(cx, cy)]), (cmd = rel ? "l" : "L")) : s.push(["L", ...P(cx, cy)]);
      }
      pts.push(s);
    }
    pts.forEach((s) => segs.push({ stroke: stroke, sw: sw, s: s }));
  });
  return { kind: "svg", top: box.top - R0.top, bottom: box.bottom - R0.top, segs: segs };
}
// the render, read: text lines, filled boxes, rules, marks and images, in CSS px from the document's top left
function dvPdfRead(doc, root) {
  const win = doc.defaultView,
    R0 = root.getBoundingClientRect(),
    out = { text: [], fills: [], marks: [], rot: [], atoms: [], heads: [], rows: [], width: R0.width, height: R0.height },
    skip = new Set(),
    vis = (cs) => "none" !== cs.display && "hidden" !== cs.visibility;
  const add = (el, x, y, w, h, color) => w > 0.2 && h > 0.2 && color && out.fills.push({ x: x, y: y, w: w, h: h, color: color, top: y, bottom: y + h });
  [root, ...root.querySelectorAll("*")].forEach((el) => {
    if ([...skip].some((s) => s.contains(el))) return;
    const cs = win.getComputedStyle(el);
    if (!vis(cs)) return void skip.add(el);
    const r = el.getBoundingClientRect(),
      x = r.left - R0.left,
      y = r.top - R0.top;
    if ("svg" === el.tagName.toLowerCase()) return skip.add(el), void out.marks.push(dvPdfSvg(el, R0));
    if ("IMG" === el.tagName) return void out.marks.push({ kind: "img", el: el, x: x, y: y, w: r.width, h: r.height, top: y, bottom: y + r.height });
    if (cs.transform && "none" !== cs.transform) {
      // the DRAFT / VOID stamp: its words, turned as the render turns them
      const m = /matrix\(([^)]+)\)/.exec(cs.transform),
        v = m ? m[1].split(",").map(parseFloat) : [1, 0];
      skip.add(el);
      return void out.rot.push({ text: (el.textContent || "").trim(), angle: Math.atan2(v[1], v[0]), cx: x + r.width / 2, cy: y + r.height / 2, px: parseFloat(cs.fontSize) || 12, f: dvPdfFont(cs), color: dvPdfColor(cs.color), ls: parseFloat(cs.letterSpacing) || 0, top: y + r.height / 2, bottom: y + r.height / 2 });
    }
    add(el, x, y, r.width, r.height, dvPdfColor(cs.backgroundColor));
    [
      ["Top", x, y, r.width, null],
      ["Bottom", x, null, r.width, null],
      ["Left", x, y, null, r.height],
      ["Right", null, y, null, r.height],
    ].forEach(([side, bx, by, bw, bh]) => {
      const w = parseFloat(cs[`border${side}Width`]) || 0;
      if (!w || "none" === cs[`border${side}Style`]) return;
      add(el, null == bx ? x + r.width - w : bx, null == by ? y + r.height - w : by, null == bw ? w : bw, null == bh ? w : bh, dvPdfColor(cs[`border${side}Color`]));
    });
    const tag = el.tagName;
    // what may not be cut by a page break: a row; a section band with the row after it; the blocks that read as one
    if ("TR" === tag) {
      out.rows.push(y);
      const nx = el.classList.contains("cx-sec") && el.nextElementSibling,
        b = nx ? nx.getBoundingClientRect().bottom - R0.top : y + r.height;
      // a row reads as one: it never splits, unless it alone is taller than a third of a page (a scope written out
      // floor by floor); then it may break between its description lines, and its title keeps two lines under it
      if (b - y < DV_PDF_FULL(R0.width) / 3) out.atoms.push([y, b]);
      else {
        const first = el.querySelector(".ds");
        out.atoms.push([y, first ? Math.min(b, first.getBoundingClientRect().top - R0.top + 2 * (parseFloat(win.getComputedStyle(first).lineHeight) || 18)) : b]);
      }
      el.parentElement && "THEAD" === el.parentElement.tagName && out.heads.push({ top: y, bottom: y + r.height, tTop: el.closest("table").getBoundingClientRect().top - R0.top, tBottom: el.closest("table").getBoundingClientRect().bottom - R0.top });
    } else if (el.matches(".cx-accept") && r.height > 1) {
      // the acceptance and signature never stand alone on a page: they keep the block just above them (the totals,
      // the notes or the scope) when the two fit in half a page
      let top = y;
      for (let p = el.previousElementSibling; p; p = p.previousElementSibling) {
        const pr = p.getBoundingClientRect();
        if (!pr.height || "none" === win.getComputedStyle(p).display) continue;
        if (y + r.height - (pr.top - R0.top) > DV_PDF_FULL(R0.width) * 0.5) break;
        top = pr.top - R0.top;
        break;
      }
      out.atoms.push([top, y + r.height, "keep"]);
    } else if (el.matches(".cxd-lh,.cxd-hd,.cxd-meta,.cxd-tot>div,.cxd-sig,.cx-accept,.cxd-box,.cxd-foot,.cxd-tot")) out.atoms.push([y, y + r.height, el.matches(".cxd-tot,.cxd-box,.cx-accept") ? "soft" : ""]);
  });
  // every line of text: the words of each text node, grouped by the line the render set them on
  const tw = doc.createTreeWalker(root, win.NodeFilter.SHOW_TEXT),
    rg = doc.createRange();
  for (let n = tw.nextNode(); n; n = tw.nextNode()) {
    const el = n.parentElement;
    if (!el || [...skip].some((s) => s.contains(el)) || !/\S/.test(n.data)) continue;
    const cs = win.getComputedStyle(el);
    if (!vis(cs)) continue;
    const tt = cs.textTransform,
      tf = (s) => ("uppercase" === tt ? s.toUpperCase() : "lowercase" === tt ? s.toLowerCase() : "capitalize" === tt ? s.replace(/\b\w/g, (m) => m.toUpperCase()) : s),
      base = { px: parseFloat(cs.fontSize) || 12, f: dvPdfFont(cs), color: dvPdfColor(cs.color) || "0 0 0", ls: parseFloat(cs.letterSpacing) || 0 },
      re = /\S+/g;
    let m,
      cur = null;
    const flush = () => cur && out.text.push(Object.assign({}, base, cur, { s: tf(n.data.slice(cur.a, cur.b).replace(/\s+/g, " ")) }));
    // a word the render broke across two lines (after a hyphen, or anywhere in a long one) is read piece by piece
    const pieces = (a, b) => {
      rg.setStart(n, a), rg.setEnd(n, b);
      const rs = [...rg.getClientRects()].filter((q) => q.width > 0);
      if (rs.length < 2) return rs.length ? [[a, b, rs[0]]] : [];
      const P = [];
      for (let k = a; k < b; k++) {
        rg.setStart(n, k), rg.setEnd(n, k + 1);
        const q = rg.getBoundingClientRect(),
          last = P[P.length - 1];
        if (!q.width) {
          last && (last[1] = k + 1);
          continue;
        }
        last && Math.abs(q.top - last[2].top) < 2 ? ((last[1] = k + 1), (last[2] = { top: last[2].top, bottom: last[2].bottom, left: last[2].left, right: q.right })) : P.push([k, k + 1, { top: q.top, bottom: q.bottom, left: q.left, right: q.right }]);
      }
      return P;
    };
    while ((m = re.exec(n.data)))
      pieces(m.index, m.index + m[0].length).forEach(([a, b, q]) => {
        const top = q.top - R0.top;
        if (cur && Math.abs(top - cur.top) < 2) (cur.b = b), (cur.x1 = q.right - R0.left);
        else flush(), (cur = { a: a, b: b, top: top, bottom: q.bottom - R0.top, x0: q.left - R0.left, x1: q.right - R0.left });
      });
    flush();
  }
  out.text.forEach((t) => out.atoms.push([t.top, t.bottom]));
  return out;
}
// page breaks, in px of the render: as much as fits, never through an atom; the header row again on a continuation
function dvPdfPages(L) {
  const s = (DV_PDF.W - DV_PDF.ML - DV_PDF.MR) / L.width,
    full = DV_PDF_FULL(L.width),
    atoms = L.atoms.filter((a) => a[1] - a[0] < full * ("soft" === a[2] ? 0.4 : "keep" === a[2] ? 0.55 : 0.95)).sort((a, b) => a[0] - b[0]),
    // where a page may start: a word, a band, a mark, or a row's own top (so a row keeps its top padding)
    content = [...L.text, ...L.fills.filter((f) => f.h > 3), ...L.marks].map((x) => x.top).concat(L.rows),
    end = Math.max(0, ...L.text.map((t) => t.bottom), ...L.fills.map((f) => f.bottom), ...L.marks.map((m) => m.bottom)),
    pages = [];
  let start = Math.min(0, ...content);
  for (let guard = 0; start < end - 0.5 && guard < 500; guard++) {
    const head = L.heads.find((h) => start >= h.bottom - 0.5 && start < h.tBottom - 2),
      avail = full - (head ? head.bottom - head.top : 0),
      limit = start + avail;
    let stop = end;
    if (limit < end) {
      stop = limit;
      // step back past every atom the line would cut
      for (let moved = !0; moved; ) {
        moved = !1;
        for (const a of atoms) if (a[0] < stop - 0.5 && a[1] > stop + 0.5 && a[0] > start + 0.5) (stop = a[0]), (moved = !0);
      }
      stop <= start + 1 && (stop = limit);
    }
    pages.push({ start: start, stop: stop, head: head });
    const next = content.filter((y) => y >= stop - 0.5).sort((a, b) => a - b)[0];
    if (null == next) break;
    start = Math.max(stop, next);
  }
  return { pages: pages, s: s };
}
function dvPdfJpeg(img) {
  try {
    const w = img.naturalWidth,
      h = img.naturalHeight;
    if (!w || !h) return null;
    const cv = document.createElement("canvas");
    (cv.width = w), (cv.height = h);
    const g = cv.getContext("2d");
    (g.fillStyle = "#fff"), g.fillRect(0, 0, w, h), g.drawImage(img, 0, 0);
    return { w: w, h: h, data: atob(cv.toDataURL("image/jpeg", 0.92).split(",")[1]) };
  } catch (e) {
    return null;
  }
}
function dvPdfBuild(L, title, footLeft) {
  const { W, H, ML, MT, MB } = DV_PDF,
    { pages, s } = dvPdfPages(L),
    imgs = [],
    streams = [],
    n = (v) => (Math.round(v * 100) / 100).toString();
  L.marks.filter((m) => "img" === m.kind).forEach((m) => ((m.jpg = dvPdfJpeg(m.el)), m.jpg && ((m.im = imgs.length + 1), imgs.push(m.jpg))));
  pages.forEach((pg, pi) => {
    const ops = [],
      hh = pg.head ? pg.head.bottom - pg.head.top : 0,
      Y = (y, src) => H - MT - (src ? y - src.top : y - pg.start + hh) * s,
      X = (x) => ML + x * s,
      inWin = (t, a, b) => t >= a - 0.5 && t < b - 0.5,
      draw = (a, b, src) => {
        // bands and rules first, then marks, then words
        L.fills.forEach((f) => {
          const y0 = Math.max(f.top, a),
            y1 = Math.min(f.bottom, b);
          if (y1 - y0 < 0.2) return;
          ops.push(`${f.color} rg ${n(X(f.x))} ${n(Y(y1, src))} ${n(f.w * s)} ${n((y1 - y0) * s)} re f`);
        });
        L.marks.forEach((m) => {
          if (!inWin(m.top, a, b)) return;
          if ("svg" === m.kind)
            m.segs.forEach((g) => ops.push(`${g.stroke} RG ${n(g.sw * s)} w 1 j ${g.s.map((p) => ("Z" === p[0] ? "h" : `${n(X(p[1]))} ${n(Y(p[2], src))} ${"M" === p[0] ? "m" : "l"}`)).join(" ")} S`));
          else if (m.im) ops.push(`q ${n(m.w * s)} 0 0 ${n(m.h * s)} ${n(X(m.x))} ${n(Y(m.bottom, src))} cm /Im${m.im} Do Q`);
        });
        L.text.forEach((t) => {
          if (!inWin((t.top + t.bottom) / 2, a, b)) return;
          const font = DV_PDF_FONTS[t.f],
            pt = t.px * s,
            by = dvPdfBytesOf(t.s),
            tc = t.ls * s,
            nat = dvPdfWidth(by, font, pt) + by.length * tc,
            want = (t.x1 - t.x0 - Math.max(0, t.ls)) * s,
            tz = nat > 0 ? Math.min(160, Math.max(60, (100 * want) / nat)) : 100,
            base = t.bottom - (t.bottom - t.top) * 0.2;
          ops.push(`BT ${t.color} rg /F${t.f + 1} ${n(pt)} Tf ${n(tz)} Tz ${n(tc)} Tc 1 0 0 1 ${n(X(t.x0))} ${n(Y(base, src))} Tm ${dvPdfStr(by)} Tj ET`);
        });
      };
    // a stamp under the words, on the page its centre falls on
    L.rot.forEach((r) => {
      if (!inWin(r.cy, pg.start, pg.stop)) return;
      const font = DV_PDF_FONTS[r.f],
        pt = r.px * s,
        by = dvPdfBytesOf(r.text),
        w = dvPdfWidth(by, font, pt) + by.length * r.ls * s,
        a = -r.angle,
        c = Math.cos(a),
        sn = Math.sin(a),
        cx = X(r.cx),
        cy = Y(r.cy),
        x0 = cx - (w / 2) * c + pt * 0.35 * sn,
        y0 = cy - (w / 2) * sn - pt * 0.35 * c;
      ops.push(`BT ${r.color || "0.9 0.9 0.9"} rg /F${r.f + 1} ${n(pt)} Tf ${n(r.ls * s)} Tc ${n(c)} ${n(sn)} ${n(-sn)} ${n(c)} ${n(x0)} ${n(y0)} Tm ${dvPdfStr(by)} Tj ET`);
    });
    pg.head && draw(pg.head.top, pg.head.bottom, pg.head);
    draw(pg.start, pg.stop, null);
    // the foot of every page: which document, and which page of how many
    const fl = dvPdfBytesOf(footLeft),
      fr = dvPdfBytesOf(`Page ${pi + 1} of ${pages.length}`),
      fy = MB - 18;
    ops.push(`0.42 0.455 0.5 rg BT /F1 7.5 Tf 100 Tz 0 Tc 1 0 0 1 ${ML} ${fy} Tm ${dvPdfStr(fl)} Tj ET`);
    ops.push(`BT /F1 7.5 Tf 100 Tz 0 Tc 1 0 0 1 ${n(W - DV_PDF.MR - dvPdfWidth(fr, "Helvetica", 7.5))} ${fy} Tm ${dvPdfStr(fr)} Tj ET`);
    streams.push(ops.join("\n"));
  });
  // the file: catalog, pages, eight standard fonts, the images, then each page and its content
  const objs = ["<< /Type /Catalog /Pages 2 0 R >>", ""];
  DV_PDF_FONTS.forEach((f) => objs.push(`<< /Type /Font /Subtype /Type1 /BaseFont /${f} /Encoding /WinAnsiEncoding >>`));
  const imRef = imgs.map((im) => (objs.push(`<< /Type /XObject /Subtype /Image /Width ${im.w} /Height ${im.h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${im.data.length} >>\nstream\n${im.data}\nendstream`), objs.length)),
    res = `<< /Font << ${DV_PDF_FONTS.map((f, i) => `/F${i + 1} ${i + 3} 0 R`).join(" ")} >>${imRef.length ? ` /XObject << ${imRef.map((r, i) => `/Im${i + 1} ${r} 0 R`).join(" ")} >>` : ""} >>`,
    kids = [];
  streams.forEach((c) => {
    objs.push(`<< /Length ${c.length} >>\nstream\n${c}\nendstream`);
    const ci = objs.length;
    objs.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${W} ${H}] /Resources ${res} /Contents ${ci} 0 R >>`);
    kids.push(objs.length);
  });
  objs[1] = `<< /Type /Pages /Kids [${kids.map((k) => k + " 0 R").join(" ")}] /Count ${kids.length} >>`;
  objs.push(`<< /Title ${dvPdfStr(dvPdfBytesOf(title))} /Producer (SmartDesigns Projects) >>`);
  let out = "%PDF-1.4\n%\xe2\xe3\xcf\xd3\n";
  const offs = [];
  objs.forEach((o, i) => (offs.push(out.length), (out += `${i + 1} 0 obj\n${o}\nendobj\n`)));
  const x = out.length;
  out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n${offs.map((v) => String(v).padStart(10, "0") + " 00000 n \n").join("")}trailer\n<< /Size ${objs.length + 1} /Root 1 0 R /Info ${objs.length} 0 R >>\nstartxref\n${x}\n%%EOF\n`;
  return { bytes: out, pages: pages.length };
}
// the document laid out in a page-width frame of its own (the app's phone styles never reach it), read, and written
async function dvPdfMake(r) {
  const fr = document.createElement("iframe");
  fr.setAttribute("aria-hidden", "true");
  fr.style.cssText = `position:fixed;left:-20000px;top:0;width:${DV_PDF.PX}px;height:1200px;border:0;opacity:0;pointer-events:none`;
  document.body.appendChild(fr);
  try {
    const doc = fr.contentDocument;
    doc.open();
    doc.write(`<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:#fff}${CX_CSS}${"undefined" != typeof CX_PAGED_CSS ? CX_PAGED_CSS : ""}.cxd{max-width:none}</style></head><body>${dvDocHtml(r)}</body></html>`);
    doc.close();
    const imgs = [...doc.images];
    await Promise.race([Promise.all(imgs.map((im) => (im.complete ? 0 : new Promise((ok) => ((im.onload = im.onerror = ok)))))), new Promise((ok) => setTimeout(ok, 2500))]);
    try {
      doc.fonts && (await Promise.race([doc.fonts.ready, new Promise((ok) => setTimeout(ok, 1500))]));
    } catch (e) {}
    const root = doc.querySelector(".cxd") || doc.body;
    // a table wider than the page (a pay application's nine columns) widens the render, never runs off the paper
    const wide = Math.max(root.scrollWidth, ...[...root.querySelectorAll("table")].map((t) => t.scrollWidth));
    wide > DV_PDF.PX + 1 && (fr.style.width = Math.min(1100, Math.ceil(wide) + 4) + "px");
    const
      bill = "bill" === r.kind,
      num = bill ? r.b.number || "" : r.d.number,
      label = bill ? "Bill" : ((root.querySelector(".cxd-kind") || {}).textContent || "").trim(),
      firm = bill ? r.b.vendor || "" : (cxCo(r.d) || {}).name || "",
      title = [label, num].filter(Boolean).join(" ") + (firm ? ` · ${firm}` : ""),
      L = dvPdfRead(doc, root),
      out = dvPdfBuild(L, title, title);
    return { bytes: out.bytes, pages: out.pages, title: title, name: `${(bill ? `${r.b.vendor || "Bill"} ${r.b.number || ""}` : r.d.number).replace(/[^\w.-]+/g, "_")}.pdf` };
  } finally {
    fr.remove();
  }
}
async function dvPdf(r) {
  const P = await dvPdfMake(r),
    u8 = new Uint8Array(P.bytes.length);
  for (let i = 0; i < P.bytes.length; i++) u8[i] = P.bytes.charCodeAt(i) & 255;
  const blob = new Blob([u8], { type: "application/pdf" }),
    a = document.createElement("a");
  (a.href = URL.createObjectURL(blob)), (a.download = P.name), document.body.appendChild(a), a.click(), a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4e3);
  toast(`${P.name} downloaded`);
  return P.name;
}

// ---- View History: every change, payment, credit and refund on the record, with who and when -------------------------------
function dvHistory(r) {
  const id = "bill" === r.kind ? r.b.id : r.d.id,
    au = (DB.audit || []).filter((x) => x.refId === id || (r.c && dvRefunds(r.c).some((f) => f.invoiceId === id && f.id === x.refId))),
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
#dv .dv-ttl{flex:1;min-width:0}#dv .dv-tt{font-weight:400;color:var(--muted,#6b7480);font-size:.85em}#dv .dv-ttl h2{margin:0;font-size:18px;overflow-wrap:anywhere}#dv .dv-due{margin-top:4px;font-size:16px;font-weight:600;color:var(--ink,#1D2430)}
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
      dvRefunds(c).map((f) => ({
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
