/* =====================================================================================================================
   Purchasing, lane P5: the item table (Alan, 11-06: "the purchasing modules should have columns: Invoice ie: FM1 / Lead
   Time / Item # / Description / Qnty / Room ie:Primary Bathroom/Powder Room/Kitchen, etc / Budget Price / Purchased Price
   / Vendor / Status ie:purchased/pricing/delivered / Delivery Date"). Rides right after src/puorders.js.

   What it is. One row per thing a job buys, across its whole life: selecting, needed, pricing (a request for quote out),
   a draft order, purchased, backordered, partly delivered, delivered, installed, returned. It is the Buy Board's Table
   view (a Needs / Table switch on the Buy Board and on the job's Purchasing tab), not a new page or menu item.

   Design gate (BACKLOG §1.16, the chief of staff 11-06). The noun is the material (what must be bought, ia_map ONE_PLACE
   'material' in view proc); the list is buyList, the Buy Board's one reader. No new store, list, queue or menu item:
   buyList(scope, { all: true }) also returns what is ordered and what has arrived (order lines, FF&E items at every
   stage, materials on site), and buyList(scope) with no options is exactly what it was (psBuyListBase; the counts lint
   holds it). Status words are read off the records; the next step under them is puNeedStatus's. Purchased Price is the
   order's or the bill's, never typed; status moves only through Order and Receive. The one import (a coordinator's sheet)
   writes the FF&E items' own store (DB.sel.items), through selNew, as the person confirms it.

   The columns, each filled from its record:
     Invoice          the FM package (the client's materials invoice, it.fm or po.fm) where one is set, else the ERP
                      invoice that billed the line (lineFin(key).invoices); the estimate line on the second line
     Lead Time        the item's own (the selection's observed or quoted lead, the material's, the estimate line's weeks),
                      else the order's promise, else the vendor's history (lsVendorLead); working days, as order-by reads them
     Item #           the order line's, the selection's or its clip's SKU
     Budget Price     the selection's budget (qty x unit cost + freight); an item alone on its estimate line carries the
                      line's budget (lineCommitment); items sharing a lump-sum line say so and the line's budget is
                      counted once in the totals
     Purchased Price  the order line (qty x price, pre-tax, its share of the freight said beside the unit price); what
                      was billed or paid past the order is said apart, never folded into the amount. Over and under the
                      budget show alike, in plain words.

   The coordinator's wave-2 review (11-12), each fixed as a class:
     One budget       a line's budget counts once under every grouping: to the one group that holds every item on it,
                      else in the "Across ..." row, and each group on it says which line it shares and with whom
                      (psGroupShare). The groups' budgets plus the shared lines are the header's Budget.
     The source       a Purchased price is an order's (its number is the label). A figure typed from a receipt on a
                      selection (it.actual, "What it actually cost") has no order, bill or card charge behind it: it is
                      shown as typed, kept out of Purchased and Under budget, and totalled apart, as an imported price is.
                      So the table and the vendor's record (itemPriceHistory) see the same purchases.
     The proof        purchased or delivered rests on a record: an issued order, or for where it is, a receipt or a return
                      on file (psProofOf). With none the status is "Marked bought, no order on file", with Find the Order
                      (psFindOrder), and it is counted. A receipt marked damaged or wrong, or an open claim, reads
                      "Delivered, damaged: claim open" (psCondOf).
     One date         Delivery Date sorts the date the row shows: delivered or promised, else need-by; blanks last.
   ===================================================================================================================== */

// ---- buyList's opt-in: what is ordered and what has arrived ------------------------------------------------------------
const psBuyListBase = buyList;
buyList = function (scope, opts) {
  const rows = psBuyListBase.apply(this, arguments);
  if (!opts || !opts.all) return rows;
  try {
    return rows.concat(psMoreRows(scope, rows));
  } catch (e) {
    console.warn("buyList all", e);
    return rows;
  }
};
const psPlKey = (po, pl) => po.id + ":" + pl.id;
const psLivePos = () => (DB.pos || []).filter((po) => "cancelled" !== po.status);
const SEL_DONE = ["office", "site", "inst"];
// The rows buyList leaves out: order lines nobody's row stands for, materials on site, FF&E items at the other stages.
function psMoreRows(scope, base) {
  const out = [],
    havePl = new Set(),
    haveMat = new Set(),
    haveSel = new Set();
  base.forEach((r) => {
    r.pl && r.po && havePl.add(psPlKey(r.po, r.pl));
    r.m && haveMat.add(r.m.id);
    r.it && haveSel.add(r.it.id);
    (r.draftPOs || []).forEach((po) => (po.lines || []).forEach((l) => l.line === r.key && havePl.add(psPlKey(po, l))));
    r.q && psLivePos().forEach((po) => (po.lines || []).forEach((l) => l.requestId === r.q.id && havePl.add(psPlKey(po, l))));
  });
  psLivePos().forEach((po) => (po.lines || []).forEach((pl) => ((pl.materialId && haveMat.has(pl.materialId)) || (pl.selId && haveSel.has(pl.selId))) && havePl.add(psPlKey(po, pl))));
  (DB.projects || [])
    .filter((p) => !scope || p.id === scope)
    .forEach((p) =>
      withProject(p, () => {
        const c = (DB.clients || []).find((x) => x.id === p.clientId);
        psLivePos()
          .filter((po) => po.projectId === p.id)
          .forEach((po) =>
            (po.lines || []).forEach((pl) => {
              if (havePl.has(psPlKey(po, pl))) return;
              havePl.add(psPlKey(po, pl));
              const m = pl.materialId ? (p.materials || []).find((x) => x.id === pl.materialId) || null : null,
                it = pl.selId ? ((DB.sel || {}).items || []).find((x) => x.id === pl.selId) || null : null,
                ref = pl.line && /^(estimate|co):/.test(pl.line) ? findLine(pl.line) : null;
              m && haveMat.add(m.id), it && haveSel.add(it.id);
              let needBy = po.needBy || "";
              try {
                needBy = (m ? matDates(m).needBy : it ? selNeedOnSite(it) : ref ? lineNeedBy(p, ref.line).needBy : "") || needBy;
              } catch (e) {}
              const qty = +pl.qty || 0,
                got = +pl.received || 0;
              out.push({
                kind: "order", src: "order", extra: 1, p: p, c: c, pl: pl, po: po, m: m, it: it,
                key: `po:${po.id}:${pl.id}`, presetLine: pl.line || "", name: pl.item || pl.desc || "Order line",
                needBy: needBy, orderBy: "", lead: 0, task: null, vendor: po.vendor || "", price: r2(qty * (+pl.price || 0)),
                budget: 0, held: 0, ordered: "draft" !== po.status, received: ["received", "closed"].includes(po.status) || (qty > 0 && got >= qty),
                eta: pl.eta || po.expected || "", dec: null, qty: `${qty} ${pl.unit || ""}`.trim(), code: pl.code || "", askedBy: "", room: (it && it.room) || "",
              });
            }),
          );
        (p.materials || [])
          .filter((m) => "on-site" === m.status && !haveMat.has(m.id))
          .forEach((m) => {
            haveMat.add(m.id);
            let needBy = "";
            try {
              needBy = matDates(m).needBy || "";
            } catch (e) {}
            out.push({ kind: "material", src: "material", extra: 1, p: p, c: c, m: m, key: m.line || "", name: m.name, needBy: needBy, orderBy: "", lead: +m.lead || 0, task: null, vendor: m.vendor || "", price: +m.cost || 0, budget: 0, held: 0, po: null, ordered: !0, received: !0, eta: m.eta || "", dec: null, qty: m.qty || "", code: "", askedBy: "" });
          });
        ((DB.sel || {}).items || [])
          .filter((it) => it.projectId === p.id && !haveSel.has(it.id))
          .forEach((it) => {
            haveSel.add(it.id);
            let needBy = "";
            try {
              needBy = selNeedOnSite(it) || "";
            } catch (e) {}
            out.push({ kind: "ffe", src: "ffe", extra: 1, p: p, c: c, it: it, key: "sel:" + it.id, name: it.name, needBy: needBy, orderBy: "", lead: +it.leadDays || 0, task: null, vendor: it.vendor || "", price: selLineCost(it), budget: selLineCost(it), held: 0, po: null, ordered: SEL_ORDER.indexOf(it.stage) >= SEL_ORDER.indexOf("ord"), received: SEL_DONE.includes(it.stage), eta: (it.dates || {}).eta || "", dec: null, qty: `${+it.qty || 1} ${it.unit || "ea"}`, code: "", room: it.room || "", askedBy: "" });
          });
      }),
    );
  out.forEach((r) => {
    try {
      bbFinish(r);
    } catch (e) {
      r.id = ovBuyId(r);
    }
  });
  return out;
}

// ---- one item per row ----------------------------------------------------------------------------------------------
const PS_STATUS = [
  ["selecting", "Selecting", ""],
  ["needed", "Needed", "amber"],
  ["unbacked", "Marked bought, no order on file", "red"],
  ["pricing", "Pricing", "blue"],
  ["draft", "Draft order", "amber"],
  ["approval", "Waiting for approval", "amber"],
  ["purchased", "Purchased", "blue"],
  ["backordered", "Backordered", "red"],
  ["partial", "Partly delivered", "blue"],
  ["delivered", "Delivered", "green"],
  ["installed", "Installed", "green"],
  ["returned", "Returned", "grey"],
];
const PS_WORD = Object.fromEntries(PS_STATUS.map(([k, w]) => [k, w])),
  PS_TONE = Object.fromEntries(PS_STATUS.map(([k, , t]) => [k, t])),
  PS_RANK = Object.fromEntries(PS_STATUS.map(([k], i) => [k, i])),
  PS_BOUGHT = ["purchased", "backordered", "partial", "delivered", "installed", "returned"];
// Rooms, for an item whose record names none (a material's name, an order line's description): the job's own rooms
// first (its selections'), then the rooms of a townhouse. Read from the words, never guessed past them.
const PS_ROOMS = ["Primary bath", "Primary bedroom", "Guest bath", "Garden bath", "Powder room", "Parlor kitchen", "Garden kitchen", "Kitchen", "Laundry", "Parlor", "Dining room", "Living room", "Library", "Bedroom", "Stair", "Hall", "Cellar", "Exterior", "Garden floor", "3rd floor", "2nd floor", "4th floor", "Whole house"];
const PS_ROOM_ALIAS = [[/\b3rd fl\b/i, "3rd floor"], [/\b2nd fl\b/i, "2nd floor"], [/\b4th fl\b/i, "4th floor"], [/\bprimary bathroom\b/i, "Primary bath"], [/\bpowder\b/i, "Powder room"]];
function psRoomFrom(text, pid) {
  const s = String(text || "");
  if (!s) return "";
  const own = [...new Set(((DB.sel || {}).items || []).filter((i) => i.projectId === pid && i.room).map((i) => i.room))],
    L = [...new Set(own.concat(PS_ROOMS))].sort((a, b) => b.length - a.length),
    hit = L.find((r) => new RegExp("\\b" + r.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b", "i").test(s));
  if (hit) return hit;
  const a = PS_ROOM_ALIAS.find(([re]) => re.test(s));
  return a ? a[1] : "";
}
// the order lines a row stands for (cancelled orders left out)
function psPoLines(r) {
  if (r.pl && r.po) return [{ po: r.po, pl: r.pl }];
  const out = [];
  psLivePos().forEach((po) =>
    (po.lines || []).forEach((pl) => {
      if ((r.m && pl.materialId === r.m.id) || (r.it && (pl.selId === r.it.id || (r.it.poId === po.id && !pl.selId && (pl.item || "") === r.it.name))) || (r.q && pl.requestId === r.q.id) || ((r.draftPOs || []).includes(po) && pl.line === r.key)) out.push({ po: po, pl: pl });
    }),
  );
  return out;
}
const psExt = (pl) => r2((+pl.qty || 0) * (+pl.price || 0));
// what was billed or paid against an order line: the line's share of its order's bills and card or bank payments
// (lineOrderPaid, the one reading job cost uses), else the order's own bills when it has one line
function psPaidOn(po, pl) {
  try {
    if (pl.line && 1 === (po.lines || []).filter((l) => l.line === pl.line).length && "function" == typeof lineOrderPaid) {
      const o = lineOrderPaid(po, pl.line);
      return r2((o.billed || 0) + (o.txnPaid || 0));
    }
    if (1 === (po.lines || []).length) return r2(puPoBills(po).reduce((a, b) => a + billCost(b), 0));
    const b = puPoLineBilled(po, pl);
    return null == b ? 0 : b;
  } catch (e) {
    return 0;
  }
}
function psReturnOf(it) {
  return it ? ((DB.sel || {}).returns || []).find((x) => x.itemId === it.id && !["cancelled", "rejected"].includes(x.status)) || null : null;
}
function psStatusOf(r, pls) {
  const live = pls.filter((x) => "draft" !== x.po.status),
    it = r.it;
  if (psReturnOf(it) || live.some((x) => +x.pl.returned > 0)) return "returned";
  if (it && "inst" === it.stage) return "installed";
  if (r.received || (it && ["office", "site"].includes(it.stage)) || (live.length && live.every((x) => (+x.pl.received || 0) >= (+x.pl.qty || 0) && +x.pl.qty > 0))) return "delivered";
  if (live.some((x) => +x.pl.backordered > 0)) return "backordered";
  if (live.some((x) => (+x.pl.received || 0) > 0)) return "partial";
  if (live.length && live.every((x) => "pending" === x.po.status)) return "approval";
  if (live.length || r.ordered) return "purchased";
  if (pls.length || (r.draftPOs || []).length) return "draft";
  if (it && "sel" === it.stage) return "selecting";
  let q = null;
  try {
    q = "function" == typeof puQuoteStage ? puQuoteStage(r) : null;
  } catch (e) {}
  if (q || (r.rfqs || []).length || (r.m && "quoted" === r.m.status)) return "pricing";
  return "needed";
}
// What stands behind a bought status (CLAUDE.md, Financial truth): an issued order; and for where the thing is, a
// selection's receipt (its own, or the receiving log's) or its return.
function psProofOf(r, pls) {
  const it = r.it;
  return { order: pls.some((x) => "draft" !== x.po.status), receipt: !!(it && (it.receipt || (((DB.sel || {}).recv) || []).some((x) => x.itemId === it.id) || psReturnOf(it))) };
}
// What arrived damaged, wrong or short and is not settled: a selection's open claim (a split shipment is not one), or its
// receipt marked damaged or wrong with no claim ever raised; an order line's open delivery claim (po.issues).
function psCondOf(it, pls) {
  try {
    if (it) {
      const C = claimsFor(it.id).filter((c) => "partial" !== c.kind),
        open = C.find((c) => CLAIM_OPEN.includes(c.status)),
        rc = it.receipt && ["damaged", "wrong"].includes(it.receipt.condition) ? it.receipt.condition : "";
      if (open) return { kind: open.kind, claim: "open", vendor: open.vendor || it.vendor || "" };
      if (rc && !C.length) return { kind: rc, claim: "none", vendor: it.vendor || "" };
    }
    for (const { po: po, pl: pl } of pls) {
      const c = (po.issues || []).find((i) => i.claim && i.lineId === pl.id && "open" === (i.status || "open"));
      if (c) return { kind: c.type || "damaged", claim: "open", vendor: po.vendor || "" };
    }
  } catch (e) {}
  return null;
}
const PS_COND_WORD = { damaged: "damaged", wrong: "wrong item", short: "short" };
const psStatusWord = (x) => (x.cond && ["delivered", "partial", "installed"].includes(x.status) ? `${PS_WORD[x.status]}, ${PS_COND_WORD[x.cond.kind] || x.cond.kind}: ${"open" === x.cond.claim ? "claim open" : "no claim raised"}` : PS_WORD[x.status]);
function psLeadOf(r, pls) {
  const it = r.it,
    m = r.m,
    ref = r.lineKey ? findLine(r.lineKey) : null;
  if (it) {
    let L = null;
    try {
      L = selEffLead(it);
    } catch (e) {}
    if (L && L.days) return { days: L.days, from: "observed" === L.basis ? `observed over ${L.n || "past"} orders${L.quoted ? `, quoted ${L.quoted}` : ""}` : "quoted" };
    if (+it.leadDays) return { days: +it.leadDays, from: "quoted" };
    if (it.clip && +it.clip.leadDays) return { days: +it.clip.leadDays, from: "the vendor's page" };
  }
  if (m && +m.lead) return { days: +m.lead, from: "the material" };
  if (ref && +ref.line.leadWeeks) return { days: 5 * +ref.line.leadWeeks, from: `${+ref.line.leadWeeks} weeks on the estimate line` };
  const o = pls.find((x) => x.po.date && (x.pl.eta || x.po.expected));
  if (o)
    try {
      const d = wd(o.po.date, o.pl.eta || o.po.expected);
      if (d > 0) return { days: d, from: `${o.po.number}'s promise` };
    } catch (e) {}
  const v = r.vendor ? lsVendorLead(r.vendor) : 0;
  return v ? { days: v, from: `${r.vendor}'s history` } : { days: null, from: "" };
}
// Every item, one row each (its record, its job, its line link), for a job or every job.
function psItems(scope) {
  let R = [];
  try {
    R = buyList(scope || "", { all: !0 });
  } catch (e) {
    console.warn("item table", e);
  }
  const X = R.map(psItem);
  // budgets: an item alone on its estimate line carries the line's; items sharing a line say so (the line counted once)
  const onLine = {};
  X.forEach((x) => x.lineKey && null == x.budget && (onLine[x.lineKey] = (onLine[x.lineKey] || []).concat(x)));
  Object.entries(onLine).forEach(([k, L]) => {
    const C = lineCommitment(k);
    if (!C) return;
    const own = L.find((x) => ["line", "sub"].includes(x.r.kind)) || (1 === L.length ? L[0] : null);
    own && ((own.budget = C.budget), (own.budgetFrom = "line"));
    L.filter((x) => x !== own).forEach((x) => (x.shared = { budget: C.budget, n: L.length, key: k }));
  });
  // the money rules this table shares, read once: Over the Order (puOverOrder, the Orders page's tile and the bill gate's
  // reading of an order paid or billed past its total) and the one bill-back reading (rbRows: Ready to Bill, the Billing
  // queue, Needs Your Hand, spUnbilled's "Cost not billed" and Ask)
  let OV = [],
    RB = [];
  try {
    OV = "function" == typeof puOverOrder ? puOverOrder(scope || "") : [];
  } catch (e) {}
  try {
    RB = "function" == typeof rbRows ? rbRows(scope || "").filter((x) => "reimbursable" === x.kind) : [];
  } catch (e) {}
  const ctx = { over: new Map(OV.map((o) => [o.po.id, o])), rb: new Set(RB.map((x) => x.key)), rows: new Map() };
  X.forEach((x) => x.pos.forEach((po) => ctx.rows.set(po.id, (ctx.rows.get(po.id) || 0) + 1)));
  X.forEach((x) => psMoney(x, ctx));
  X.rb = RB;
  return X;
}
// The client invoice that bills an item: a line naming the item itself (its selection, its order line, its material,
// or a bank line bought for the client and pulled onto an invoice), else the invoice that last billed its contract line.
// Void invoices never count; a draft does, and says so.
function psInvoiceOf(o) {
  const c = o.c || (o.lineKey && (findLine(o.lineKey) || {}).client) || null;
  if (!c) return null;
  const D = (c.invoices || []).filter((d) => "void" !== d.status),
    plIds = new Set(o.pls.map((x) => x.pl.id)),
    poIds = new Set(o.pls.map((x) => x.po.id)),
    rebill = new Set((DB.txns || []).filter((t) => t.invoiceRebillId && t.poId && poIds.has(t.poId)).map((t) => t.invoiceRebillId));
  const stamped = new Set(o.pls.map((x) => x.pl.invoiceId).filter(Boolean));
  let d = D.find((x) => stamped.has(x.id) || rebill.has(x.id) || (x.lines || []).some((l) => (o.it && (l.selId === o.it.id || (l.selIds || []).includes(o.it.id))) || (l.poLineId && plIds.has(l.poLineId)) || (o.m && l.materialId === o.m.id)));
  if (d) return { d: d, c: c, how: "item" };
  if (!o.lineKey) return null;
  let nums = [];
  try {
    nums = lineFin(o.lineKey).invoices || [];
  } catch (e) {}
  const n = nums[nums.length - 1];
  d = n ? D.find((x) => x.number === n) : D.filter((x) => (x.lines || []).some((l) => l.fromLine === o.lineKey)).pop();
  return d ? { d: d, c: c, how: "line" } : null;
}
function psItem(r) {
  const p = r.p,
    pls = psPoLines(r),
    it = r.it,
    m = r.m,
    pl0 = (pls[0] || {}).pl || null,
    lineKey = r.lineKey && /^(estimate|co):/.test(r.lineKey) ? r.lineKey : "",
    ref = lineKey ? findLine(lineKey) : null,
    // where the records say it is; with no order behind a bought word it is only marked so, and with no receipt either
    // the status itself says that
    said = psStatusOf(r, pls),
    proof = psProofOf(r, pls),
    marked = PS_BOUGHT.includes(said) && !proof.order ? said : "",
    status = marked && !proof.receipt ? "unbacked" : said,
    L = psLeadOf(r, pls);
  // Invoice (Alan, 11-06: "FM 1 is an invoice #"): the client invoice that bills this item, opened from the cell; else
  // the FM number as entered on the selection or its order, not yet invoiced in the app; else not invoiced
  const fm = (it && it.fm) || (pls.map((x) => x.po.fm).find(Boolean) || "").split(/,\s*/)[0] || "",
    I = psInvoiceOf({ it: it, m: m, pls: pls, lineKey: lineKey, c: r.c }),
    lineRef = ref ? `${ref.doc.number || ""}${ref.line.num ? ` line ${ref.line.num}` : ""}`.trim() : "",
    inv = I ? I.d.number : fm;
  // qty
  const qn = pl0 ? { n: +pl0.qty || 0, u: pl0.unit || "" } : it ? { n: +it.qty || 0, u: it.unit || "ea" } : ref && ["line", "sub"].includes(r.kind) ? { n: +ref.line.qty || 0, u: ref.line.unit || "" } : (() => {
    const b = bbNum(r.qty);
    return { n: b.n, u: b.unit };
  })();
  const desc = (it && it.name) || (pl0 && (pl0.item || pl0.desc)) || (m && m.name) || (ref && ["line", "sub"].includes(r.kind) && ref.line.item) || String(r.name || "").replace(/^\d+\.\s*/, ""),
    descSub = [(pl0 && pl0.item && pl0.desc) || "", it ? [it.manufacturer, it.finish].filter(Boolean).join(", ") : ""].filter(Boolean).join(" · "),
    roomOwn = (it && it.room) || (m && m.room) || (pl0 && pl0.room) || (ref && ref.line.room) || (r.q && r.q.room) || r.room || "",
    room = roomOwn || psRoomFrom([desc, pl0 && pl0.desc, m && m.notes].filter(Boolean).join(" "), p.id),
    sku = (pl0 && pl0.sku) || (it && (it.sku || (it.clip && it.clip.sku))) || (m && m.sku) || "",
    // delivery: the day it came, else the day promised
    arrived = ["delivered", "installed", "returned"].includes(said) || "partial" === said,
    rec = pls.map((x) => x.po).find((po) => po.receivedOn || (po.receipts || []).length),
    lastRec = rec ? rec.receivedOn || [...(rec.receipts || [])].map((x) => x.date || x.at || "").filter(Boolean).sort().pop() || "" : "",
    itCame = it ? (it.dates || {}).site || (it.dates || {}).office || "" : "",
    promised = (pl0 && pl0.eta) || (pls[0] && pls[0].po.expected) || (it && (it.dates || {}).eta) || r.eta || (m && m.eta) || "",
    deliv = arrived ? String(lastRec || itCame || promised).slice(0, 10) : PS_BOUGHT.includes(said) || "draft" === said || "approval" === said ? String(promised).slice(0, 10) : "",
    needBy = r.needBy || "";
  let orderBy = r.orderBy || "";
  try {
    orderBy = orderBy || (it && !["ord", "ship", "office", "site", "inst"].includes(it.stage) ? selOrderBy(it) : "");
  } catch (e) {}
  const POs = [...new Set(pls.map((x) => x.po))];
  return {
    id: r.id,
    r: r,
    p: p,
    pid: p.id,
    job: puJob(p),
    kind: r.kind,
    it: it,
    m: m,
    po: POs[0] || null,
    pos: POs,
    pls: pls,
    lineKey: lineKey,
    lineRef: lineRef,
    fm: fm,
    inv: inv,
    invDoc: I,
    invoiced: !!I,
    lead: L.days,
    orderBy: orderBy,
    orderLate: !!(orderBy && orderBy < today() && ["selecting", "needed", "pricing"].includes(status)),
    imported: (it && it.imported) || null,
    leadFrom: L.from,
    sku: sku,
    desc: desc,
    descSub: descSub,
    qty: qn.n || null,
    unit: qn.u,
    room: room,
    roomRead: !roomOwn && !!room,
    vendor: (POs[0] && POs[0].vendor) || r.vendor || (it && it.vendor) || (m && m.vendor) || "",
    status: status,
    marked: marked,
    cond: psCondOf(it, pls),
    deliv: deliv,
    delivKind: deliv ? (arrived ? "arrived" : "promised") : "",
    // the one date the row shows and sorts by: delivered or promised, else the day it is needed
    dateShown: deliv || needBy || "",
    needBy: needBy,
    late: !!(deliv && needBy && deliv > needBy && !["installed", "returned"].includes(status)),
    budget: it ? selLineCost(it) : null,
    budgetFrom: it ? "selection" : "",
    shared: null,
    pickable: !!(r && !r.ordered && !r.received && "buy" === r.tab && !(r.draftPOs || []).length && !pls.length),
  };
}
// Purchased Price, on the budget's basis: before tax, freight in. An order line is its qty x price plus its share of the
// order's freight (the budget of a selection carries its freight too). What was billed or paid past the order's total
// (puOverOrder, the Orders page's Over the Order) is said beside it and totalled apart, never added to the amount: the
// windows read the order's $29,700 at $3,300 each, and "Billed $33,500: $3,800 over". A selection with no order may carry
// a figure typed from a receipt (it.actual, "What it actually cost"): no order, bill or card charge is behind it, so it is
// shown as typed and is not a purchase (the vendor's record and itemPriceHistory do not have it either). A coordinator's
// imported sheet likewise.
function psFreight(po, pl) {
  const sub = (po.lines || []).reduce((a, l) => a + psExt(l), 0);
  return sub > 0 && +po.shipping ? r2((+po.shipping * psExt(pl)) / sub) : 0;
}
function psMoney(x, ctx) {
  ctx = ctx || { over: new Map(), rb: new Set(), rows: new Map() };
  const live = x.pls.filter((y) => "draft" !== y.po.status),
    drafts = x.pls.filter((y) => "draft" === y.po.status),
    ordered = r2(live.reduce((a, y) => a + psExt(y.pl) + psFreight(y.po, y.pl), 0));
  x.ordered = ordered;
  // Over the Order, as the Orders page says it: each of this row's orders paid or billed past its total
  x.poOver = [...new Set(live.map((y) => y.po))].map((po) => ctx.over.get(po.id)).filter(Boolean);
  x.importedPrice = null;
  x.typedPrice = null;
  x.typedRef = "";
  if (live.length) (x.bought = ordered), (x.boughtFrom = live.map((y) => y.po.number).filter((v, i, a) => a.indexOf(v) === i).join(", ")), (x.source = "order");
  else if (drafts.length) (x.bought = r2(drafts.reduce((a, y) => a + psExt(y.pl) + psFreight(y.po, y.pl), 0))), (x.boughtFrom = `${drafts[0].po.number} (draft)`), (x.source = "draft");
  else (x.bought = null), (x.boughtFrom = ""), (x.source = "");
  // the receipt figure typed on the selection, before tax as the budget is: said, not counted
  if (null == x.bought && x.it && x.it.actual && selActual(x.it)) (x.typedPrice = r2((+x.it.actual.cost || 0) + (+x.it.actual.shipping || 0))), (x.typedRef = String(x.it.actual.ref || "")), (x.source = "typed");
  null == x.bought && null == x.typedPrice && x.imported && +x.imported.bought > 0 && ((x.importedPrice = r2(+x.imported.bought)), (x.source = "imported"));
  // bought by its mark or its receipt, with no order on file: found from the row (psFindOrder)
  x.noOrder = !!x.marked && null == x.bought;
  let C = null;
  try {
    C = x.lineKey ? lineCommitment(x.lineKey) : null;
  } catch (e) {}
  const b = x.budget,
    firm = live.length > 0 || (null != x.bought && !drafts.length);
  // over the budget: a line's is Over the Line's (lineCommitment), a selection's its purchase against its budget
  x.over = "line" === x.budgetFrom ? (C && C.over > 0.5 ? C.over : 0) : null != b && null != x.bought && x.bought > b + 0.5 ? r2(x.bought - b) : 0;
  x.under = "selection" === x.budgetFrom && firm && null != b && null != x.bought && x.bought < b - 0.5 ? r2(b - x.bought) : 0;
  x.lineOver = C && C.over > 0.5 && x.shared ? C.over : 0;
  // bought for the client and not billed back: the one bill-back reading (rbRows), for this row's order lines
  x.notBilled = x.pls.some((y) => ctx.rb.has("rbpl:" + y.pl.id));
  // which columns the record holds a value for (the suite holds each to a filled cell)
  x.src = { inv: !0, lead: null != x.lead, sku: !!x.sku, desc: !!x.desc, qty: !!x.qty, room: !!x.room, budget: null != x.budget || !!x.shared, bought: null != x.bought || null != x.importedPrice || null != x.typedPrice, vendor: !!x.vendor, status: !0, deliv: !!x.dateShown };
  return x;
}
// The price against what the firm paid before: the PO page's one check (poLinePriceCheck, the order itself left out of its
// history), so the row and the order say the same thing. And what the shop already holds for a need: the stock reading
// every buying door runs (puStockForNeed, its "may be it" hints included), in the same words (puStockSay).
function psPriceUp(x) {
  if (1 !== x.pls.length || "function" != typeof poLinePriceCheck) return null;
  const { po: po, pl: pl } = x.pls[0];
  if (!(+pl.price > 0) || !(pl.item || pl.desc)) return null;
  try {
    const c = poLinePriceCheck(pl.item || pl.desc, pl.unit || "", +pl.price, +pl.qty || 1, po.id);
    return c && !c.ok && c.ref ? { was: c.ref, from: [c.vendor, c.doc].filter(Boolean).join(", ") } : null;
  } catch (e) {
    return null;
  }
}
function psStock(x) {
  if (!x.r || x.r.ordered || "buy" !== x.r.tab || "function" != typeof puStockSay) return "";
  try {
    return puStockSay("function" == typeof puStockForNeed ? puStockForNeed(x.r) : puStockFor(x.r.name)) || "";
  } catch (e) {
    return "";
  }
}

// ---- the columns, in Alan's order ----------------------------------------------------------------------------------
const PS_COLS = [
  { k: "inv", n: "Invoice", w: 132, val: (x) => x.inv || "", cmp: (a, b) => tvNatCmp(a, b) },
  { k: "lead", n: "Lead Time", w: 84, num: 1, val: (x) => (null == x.lead ? "" : x.lead) },
  { k: "sku", n: "Item #", w: 92, val: (x) => x.sku },
  { k: "desc", n: "Description", w: 0, val: (x) => x.desc },
  { k: "qty", n: "Qty", w: 54, num: 1, val: (x) => x.qty || "" },
  { k: "room", n: "Room", w: 92, val: (x) => x.room },
  { k: "budget", n: "Budget Price", w: 88, num: 1, val: (x) => (null != x.budget ? x.budget : x.shared ? x.shared.budget : "") },
  { k: "bought", n: "Purchased Price", w: 112, num: 1, val: (x) => (null == x.bought ? "" : x.bought) },
  { k: "vendor", n: "Vendor", w: 88, val: (x) => x.vendor },
  { k: "status", n: "Status", w: 124, val: (x) => x.status, rank: PS_RANK },
  { k: "deliv", n: "Delivery Date", w: 84, type: "date", val: (x) => x.dateShown || "" },
];
const psCol = (k) => PS_COLS.find((c) => c.k === k) || null;

// ---- the view's state (per viewer, for the session) ----------------------------------------------------------------
const PS_KEY = "sd.pu.view.";
let psChoice = {},
  psF = { room: "", vendor: "", status: "", q: "" },
  psGroup = "room",
  psSorts = [],
  psPick = new Set(),
  psToolsOpen = !1;
const psLayout = () => (psPhone() ? "phone" : "desk");
// the view on screen: the person's last choice on this layout (this session, else this browser), else the layout's
// default: the Table on the desktop (Alan, 11-06, the chief of staff's verdict), Needs on the phone
function psMode() {
  const k = psLayout();
  if (psChoice[k]) return psChoice[k];
  let v = "";
  try {
    v = localStorage.getItem(PS_KEY + k) || "";
  } catch (e) {}
  return "table" === v || "needs" === v ? v : "phone" === k ? "needs" : "table";
}
const psIsOn = () => "table" === psMode();
function psChoose(table) {
  const k = psLayout(),
    v = table ? "table" : "needs";
  psChoice[k] = v;
  try {
    localStorage.setItem(PS_KEY + k, v);
  } catch (e) {}
}
function psReset() {
  psChoice = {};
  try {
    localStorage.removeItem(PS_KEY + "desk"), localStorage.removeItem(PS_KEY + "phone");
  } catch (e) {}
  (psToolsOpen = !1), (psF = { room: "", vendor: "", status: "", q: "" }), (psGroup = "room"), (psSorts = []), psPick.clear();
}
function psSet(o) {
  o = o || {};
  "group" in o && (psGroup = o.group);
  ["room", "vendor", "status", "q"].forEach((k) => k in o && (psF[k] = o[k]));
  "on" in o && psChoose(!!o.on);
  render();
}
function psSortBy(k, dir) {
  const cur = psSorts[0];
  psSorts = [{ k: k, dir: dir || (cur && cur.k === k && "asc" === cur.dir ? "desc" : "asc") }];
  render();
}
const psScope = () => ("function" == typeof puInJob && puInJob()) || ("undefined" != typeof bbProj && bbProj) || "";
// read fresh on each draw and each tap (one buyList pass): a record changed without a save still reads as it is
const psAll = () => psItems(psScope());
const psRoomKey = (x) => (x.room ? x.room.charAt(0).toUpperCase() + x.room.slice(1).toLowerCase() : "No room");
function psView() {
  const all = psAll(),
    q = psF.q.trim().toLowerCase();
  let rows = all.filter(
    (x) =>
      (!psF.room || psRoomKey(x) === psF.room) &&
      (!psF.vendor || (x.vendor || "No vendor") === psF.vendor) &&
      (!psF.status || x.status === psF.status) &&
      (!q || `${x.desc} ${x.sku} ${x.vendor} ${x.room} ${x.inv} ${x.lineRef} ${x.boughtFrom || ""} ${x.job}`.toLowerCase().includes(q)),
  );
  const S = psSorts.length ? psSorts : [];
  rows = S.length ? tvSortWith(rows, S.map((s) => [psCol(s.k), "desc" === s.dir ? -1 : 1])) : tvSortWith(rows, [[{ val: (x) => PS_RANK[x.status], rank: null }, 1], [{ val: (x) => x.needBy || x.deliv || "", type: "date" }, 1]]);
  return { all: all, rows: rows };
}
function psGroups(rows) {
  if ("none" === psGroup) return [{ name: "", rows: rows }];
  const keyOf = { room: psRoomKey, inv: (x) => x.fm || x.lineKey || x.inv || "No invoice or estimate line", vendor: (x) => x.vendor || "No vendor", status: (x) => x.status, job: (x) => x.job }[psGroup] || psRoomKey,
    M = new Map();
  rows.forEach((x) => {
    const k = keyOf(x);
    M.has(k) || M.set(k, []), M.get(k).push(x);
  });
  const none = (k) => /^No /.test(k);
  return [...M.entries()]
    .sort((a, b) => ("status" === psGroup ? PS_RANK[a[0]] - PS_RANK[b[0]] : none(a[0]) - none(b[0]) || tvNatCmp(a[0], b[0])))
    .map(([k, L]) => {
    const ref = /^(estimate|co):/.test(k) ? findLine(k) : null;
    return { key: k, name: "status" === psGroup ? PS_WORD[k] : ref ? `${L[0].lineRef}: ${ref.line.item || ""}` : k, rows: L, line: ref ? k : "" };
  });
}
// A line's budget counts once (the coordinator, 11-12: by room the groups added up to $507,861 against a header of
// $331,260, one $75,000 line in two kitchens). Under any grouping a line whose items all sit in one group is that group's;
// a line whose items sit in several is nobody's alone: it goes in the Across row, and each group on it says which line it
// shares and with whom. So the groups' budgets plus the shared lines are the header's Budget.
const PS_GROUP_NOUN = { room: ["room", "rooms"], inv: ["invoice", "invoices"], vendor: ["vendor", "vendors"], status: ["status", "statuses"], job: ["job", "jobs"] };
function psGroupShare(G) {
  const at = new Map();
  G.forEach((g, i) => ((g.shares = []), g.rows.forEach((x) => ("line" === x.budgetFrom || x.shared) && x.lineKey && (at.has(x.lineKey) || at.set(x.lineKey, new Set()), at.get(x.lineKey).add(i)))));
  const across = [];
  at.forEach((S, k) => {
    if (S.size < 2) return;
    let C = null;
    try {
      C = lineCommitment(k);
    } catch (e) {}
    const b = (C && C.budget) || 0,
      x = G[[...S][0]].rows.find((y) => y.lineKey === k);
    across.push({ key: k, budget: b, ref: (x && x.lineRef) || k, groups: [...S].map((i) => G[i].name) });
    S.forEach((i) => G[i].shares.push({ key: k, budget: b, others: [...S].filter((j) => j !== i).map((j) => G[j].name) }));
  });
  G.forEach((g) => (g.sharedKeys = new Set(g.shares.map((s) => s.key))));
  return across;
}
function psShareSay(g) {
  const N = PS_GROUP_NOUN[psGroup] || PS_GROUP_NOUN.room;
  return (g.shares || []).map((s) => `shares the ${money(s.budget)} line with ${s.others.length > 2 ? `${s.others.length} other ${N[1]}` : s.others.join(" and ")}`).join(" · ");
}
// the totals: budgets counted once per estimate line (a line in skip is left out: a group's shared lines), purchases
// summed; over the budget is each selection's plus each line's Over the Line once; over the order is each order's Over the
// Order once; typed and imported figures are not purchases and are totalled apart
function psTotals(rows, skip) {
  let budget = 0,
    bought = 0,
    over = 0,
    under = 0,
    imported = 0,
    typed = 0,
    unbacked = 0,
    recvNoOrder = 0;
  const lines = new Map(),
    pos = new Map();
  rows.forEach((x) => {
    if ("line" === x.budgetFrom || x.shared) (skip && skip.has(x.lineKey)) || lines.set(x.lineKey, lineCommitment(x.lineKey) || {});
    else if (null != x.budget) budget += x.budget;
    null != x.bought && (bought += x.bought);
    null != x.importedPrice && (imported += x.importedPrice);
    null != x.typedPrice && (typed += x.typedPrice);
    "unbacked" === x.status ? unbacked++ : x.noOrder && recvNoOrder++;
    "selection" === x.budgetFrom && ((over += x.over || 0), (under += x.under || 0));
    (x.poOver || []).forEach((o) => pos.set(o.po.id, o.over));
  });
  lines.forEach((c) => ((budget += c.budget || 0), (over += c.over > 0.5 ? c.over : 0)));
  const poOver = [...pos.values()].reduce((a, v) => a + v, 0);
  return { budget: r2(budget), bought: r2(bought), over: r2(over), under: r2(under), poOver: r2(poOver), imported: r2(imported), typed: r2(typed), unbacked: unbacked, recvNoOrder: recvNoOrder };
}

// ---- drawing -------------------------------------------------------------------------------------------------------
const PS_IC = {
  up: '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 19V5M6 11l6-6 6 6"/></svg>',
  down: '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M6 13l6 6 6-6"/></svg>',
  list: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/></svg>',
  table: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/></svg>',
  dl: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>',
  print: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><path d="M7 9V4h10v5M7 17H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2"/><rect x="7" y="14" width="10" height="6"/></svg>',
  filter: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M7 12h10M10 18h4"/></svg>',
  up2: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><path d="M12 20V9M7 14l5-5 5 5M5 4h14"/></svg>',
};
const psPhone = () => ("function" == typeof puPhone ? puPhone() : innerWidth <= 760);
function psModesHtml() {
  const on = psIsOn(),
    scope = psScope();
  let n = 0;
  try {
    n = scope ? puNeeds(scope).filter((x) => "mine" === x.b).length : puCount("proc");
  } catch (e) {}
  // the firm's number is the menu badge's (Needs You); inside a job or with the Job filter it is that job's, unmarked
  const badge = n ? `<span class="n"${scope ? "" : ' data-ocbadge="proc"'}>${n}</span>` : "";
  return `<div class="ps-modes" role="group" aria-label="Show the Buy Board as"><button type="button" class="ps-mode${on ? "" : " on"}" data-psmode="needs" aria-pressed="${!on}">${PS_IC.list}<span>Needs</span>${badge}</button><button type="button" class="ps-mode${on ? " on" : ""}" data-psmode="table" aria-pressed="${on}">${PS_IC.table}<span>Table</span></button></div>`;
}
const psDays = (n) => (null == n ? "" : `${n} day${1 === +n ? "" : "s"}`);
// A unit price is shown only where it multiplies to the amount beside it (the coordinator, 11-12: "$33,500 / $3,300.00
// each" for 9 windows): qty x price, with the freight in the amount said after it. "each", or "per sf" for a measure.
const psPer = (u) => (!u || /^(ea|each|pc|pcs|piece|pieces|set|sets)$/i.test(String(u)) ? "each" : `per ${u}`);
function psUnitSay(qty, price, unit, total, freight) {
  if (!(+qty > 1) || !(+price > 0) || null == total) return "";
  const f = +freight || 0;
  if (Math.abs(r2(+qty * +price) + f - total) > 0.5) return "";
  return `${unitMoney(+price)} ${esc(psPer(unit))}${f > 0.005 ? ` + ${money(f)} freight` : ""}`;
}
// what took an order past its total: its bills, else a card charge or a bank payment matched to it
function psOverHow(o) {
  let billed = 0,
    paid = 0;
  try {
    (billed = puPoBilled(o.po)), (paid = poPaid(o.po));
  } catch (e) {}
  if (billed >= paid - 0.005) return "Billed";
  const cards = new Set((DB.accounts || []).filter((a) => /card/i.test(a.kind || a.type || "")).map((a) => a.id)),
    T = (DB.txns || []).filter((t) => (o.po.matchedTxns || []).includes(t.id));
  return T.length && T.every((t) => cards.has(t.acct)) ? "Charged on the card" : "Paid";
}
const psMarkSay = (x) => `Marked ${String(PS_WORD[x.marked] || "bought").toLowerCase()} ${x.m ? "on the materials list" : x.imported ? "in the imported sheet" : "on the selection"}`;
const psFindBtn = (x) => (x.noOrder && !psRO() ? `<button type="button" class="btn sm ps-find" data-psfind="${esc(x.id)}">Find the Order</button>` : "");
const psQty = (x) => (x.qty ? `${+x.qty}${x.unit ? " " + x.unit : ""}` : "");
function psCellHtml(x, k, card) {
  const sv = (v) => esc(String(null == v ? "" : v)),
    // a sub-line is one line on the desktop: its whole text rides in its title
    sub = (t, cls) => (t ? `<span class="ps-sub${cls ? " " + cls : ""}" title="${sv(String(t).replace(/<[^>]*>/g, ""))}" data-nocase>${t}</span>` : "");
  if ("inv" === k) {
    const I = x.invDoc,
      main = I
        ? `<a href="#" class="ps-inv" data-psinv="${sv(x.id)}" title="Open ${sv(I.d.number)}${"line" === I.how ? `: it bills ${sv(x.lineRef)}` : ""}" data-nocase>${esc(I.d.number)}</a>${"draft" === I.d.status ? sub("draft") : ""}`
        : x.fm
          ? `<span class="ps-main" data-nocase>${esc(x.fm)}</span><span class="ps-sub warn" title="Not yet invoiced in the app: the FM number as entered" data-nocase>Not yet invoiced</span>`
          : `<span class="ps-main ps-dim${x.notBilled ? " warn" : ""}" data-nocase>Not invoiced</span>`;
    // on no contract line and marked so at the order (bbAskLine), or its order line billed back: said, not a warning
    const back = !x.lineRef && (((x.it || x.m || {}).billBack && !0) || x.pls.some((y) => y.pl.billable));
    return main + sub(esc(x.lineRef || (back ? "Billed back to the client" : "No estimate line")), x.lineRef || back ? "" : "warn") + (x.notBilled ? sub("Bought for the client, not billed back", "bad") : "");
  }
  if ("lead" === k)
    return `<span class="ps-main${x.orderLate ? " bad" : ""}" title="${sv(x.leadFrom)}" data-nocase>${psDays(x.lead)}</span>${x.orderLate ? `<span class="ps-sub bad" title="Order by ${fmt(x.orderBy)}: passed" data-nocase>${fmt(x.orderBy)} passed</span>` : x.leadFrom && /observed/.test(x.leadFrom) ? sub("observed") : ""}`;
  if ("sku" === k) return `<span class="ps-main ps-mono" data-nocase>${esc(x.sku || "")}</span>`;
  if ("desc" === k)
    return `<button type="button" class="ps-open" data-psopen="${sv(x.id)}"><b data-nocase>${esc(x.desc)}</b></button>${sub(esc([x.descSub, psScope() ? "" : x.job].filter(Boolean).join(" · ")))}`;
  if ("qty" === k) return `<span class="ps-main" data-nocase>${esc(psQty(x))}</span>`;
  if ("room" === k) return `<span class="ps-main" title="${sv(x.room)}${x.roomRead ? ": read from the item's words" : ""}" data-nocase>${esc(x.room || "")}</span>`;
  if ("budget" === k)
    return null != x.budget
      ? `<span class="ps-main" data-nocase>${money(x.budget)}</span>${x.it ? sub(psUnitSay(selQty(x.it), selCost(x.it), x.it.unit, x.budget, selShip(x.it))) : sub("line" === x.budgetFrom ? "line budget" : "")}`
      : x.shared
        ? `<span class="ps-main ps-dim" title="${money(x.shared.budget)} for the ${x.shared.n} items on the line" data-nocase>In the line</span>${sub(`${money(x.shared.budget)} line`)}`
        : "";
  if ("bought" === k) {
    if (null == x.bought)
      return null != x.typedPrice
        ? `<span class="ps-main ps-dim" data-nocase>${money(x.typedPrice)}</span>${sub(`Typed from a receipt${x.typedRef ? ` (${esc(x.typedRef)})` : ""}: no order, bill or card charge behind it`, "warn")}`
        : null != x.importedPrice
          ? `<span class="ps-main ps-dim" data-nocase>${money(x.importedPrice)}</span>${sub("Imported from a sheet: no bill or bank line behind it", "warn")}`
          : "";
    const one = 1 === x.pls.length ? x.pls[0] : null,
      up = psPriceUp(x);
    // the order's amount and the unit price that multiplies to it; what was billed or paid past the order is said apart
    return `<span class="ps-main" data-nocase>${money(x.bought)}</span>${one ? sub(psUnitSay(one.pl.qty, one.pl.price, one.pl.unit, x.bought, psFreight(one.po, one.pl))) : ""}${sub(esc(x.boughtFrom || ""))}${(x.poOver || [])
      .map((o) => sub(`${psOverHow(o)} ${money(o.out)}: ${money(o.over)} over ${esc(o.po.number)}'s ${money(o.tot)}`, "bad"))
      .join("")}${x.over ? sub(`${money(x.over)} over budget`, "bad") : x.under ? sub(`${money(x.under)} under budget`, "good") : ""}${x.lineOver ? sub(`The line is ${money(x.lineOver)} over its budget`, "bad") : ""}${
      up ? sub(`Up from ${unitMoney(up.was)} last time${up.from ? ` (${esc(up.from)})` : ""}`, "bad") : ""
    }`;
  }
  if ("vendor" === k) return `<span class="ps-main" title="${sv(x.vendor)}" data-nocase>${esc(x.vendor || "")}</span>`;
  if ("status" === k) {
    let next = "";
    try {
      const s = !PS_BOUGHT.includes(x.status) && "unbacked" !== x.status && x.r && "buy" === x.r.tab ? puNeedStatus(x.r) : null;
      next = s ? s.why || "" : "";
    } catch (e) {}
    const st = psStock(x),
      word = psStatusWord(x),
      hurt = word !== PS_WORD[x.status],
      // marked bought with nothing behind it says how it was marked; received with no order says that; the way to the
      // order is on the row (the phone's card carries the button on its own line)
      mark = "unbacked" === x.status ? sub(esc(psMarkSay(x))) : x.noOrder ? sub("No order on file", "bad") : "";
    return `<span class="ps-chip ${hurt ? "red" : PS_TONE[x.status] || ""}${word.length > 18 ? " long" : ""}" data-nocase>${esc(word)}</span>${mark}${next ? `<span class="ps-sub ps-next" title="${esc(next)}" data-nocase>${esc(next)}</span>` : ""}${st ? sub(esc(st), "blue") : ""}${card ? "" : psFindBtn(x)}`;
  }
  if ("deliv" === k)
    return x.deliv
      ? `<span class="ps-main${x.late ? " bad" : ""}" data-nocase>${fmt(x.deliv)}</span>${sub(x.late ? `need ${fmt(x.needBy)}` : "arrived" === x.delivKind ? "arrived" : "promised", x.late ? "bad" : "")}`
      : x.needBy
        ? `<span class="ps-sub" title="Needed on site ${fmt(x.needBy)}" data-nocase>need ${fmt(x.needBy)}</span>`
        : "";
  return "";
}
function psSortVal(x, c) {
  const v = c.val(x);
  return "status" === c.k ? PS_RANK[v] : v;
}
// the controller and billing read Purchasing and buy nothing (src/puorders.js puReadOnly): no picks, no import
const psRO = () => "function" == typeof puReadOnly && puReadOnly();
function psPickHtml(x) {
  return x.pickable && !psRO() ? `<label class="ps-pk" aria-label="Pick ${esc(x.desc)}"><input type="checkbox" data-pspick="${esc(x.id)}" ${psPick.has(x.id) ? "checked" : ""}></label>` : "";
}
function psRowHtml(x) {
  return `<tr data-psrow="${esc(x.id)}" class="${psPick.has(x.id) ? "on" : ""}"><td class="ps-pkc">${psPickHtml(x)}</td>${PS_COLS.map((c) => `<td data-pscol="${c.k}" data-sv="${esc(String(psSortVal(x, c)))}" class="ps-c-${c.k}${c.num ? " num" : ""}">${psCellHtml(x, c.k)}</td>`).join("")}</tr>`;
}
function psCardHtml(x) {
  // a label shows only beside a value; the cell is there either way (the sort and the suite read it)
  const cell = (k, label) => {
      const h = psCellHtml(x, k, !0),
        has = !!h.replace(/<[^>]*>/g, "").trim();
      return `${label && has ? `<span class="ps-k">${label}</span>` : ""}<span data-pscol="${k}" data-sv="${esc(String(psSortVal(x, psCol(k))))}"${has ? "" : " hidden"}>${has ? h : ""}</span>`;
    },
    line = (cls, html) => (/<span class="ps-k">/.test(html) ? `<div class="ps-cl${cls ? " " + cls : ""}">${html}</div>` : html);
  return `<div class="ps-card${psPick.has(x.id) ? " on" : ""}" data-psrow="${esc(x.id)}">${psPickHtml(x)}<div class="ps-cb"><div class="ps-ct">${cell("desc")}${cell("status")}</div>${line("", cell("room", "Room") + cell("vendor", "Vendor"))}${line("", cell("deliv", "Delivery"))}${line("ps-cm", cell("budget", "Budget") + cell("bought", "Purchased"))}${line("ps-meta", cell("inv", "Invoice") + cell("sku", "Item #") + cell("qty", "Qty") + cell("lead", "Lead"))}${psFindBtn(x) ? `<div class="ps-act">${psFindBtn(x)}</div>` : ""}</div></div>`;
}
function psGroupHead(g, phone, span) {
  if (!g.name) return "";
  // the group's own budget: its selections', and the lines whose items all sit in it (a line shared with another group
  // is said, and counted once in the Across row)
  const T = psTotals(g.rows, g.sharedKeys),
    share = psShareSay(g);
  let C = null;
  try {
    C = g.line ? lineCommitment(g.line) : null;
  } catch (e) {}
  const items = r2(g.rows.reduce((a, x) => a + (x.bought || 0), 0)),
    // a line's own group counts the line when an item under it carries it and no other group holds one of its items
    mine = !!C && !(g.sharedKeys && g.sharedKeys.has(g.line)) && g.rows.some((x) => x.lineKey === g.line && ("line" === x.budgetFrom || x.shared)),
    extra = C ? r2(T.budget - (mine ? C.budget : 0)) : 0,
    attrs = ` data-psgbudget="${T.budget}"${C ? ` data-pskey="${esc(g.line)}" data-psbudget="${C.budget}" data-psused="${C.used}" data-psitems="${items}"` : ""}`,
    say = C
      ? `${mine ? `Line budget ${money(C.budget)}` : `The ${money(C.budget)} line`} · spent and on order ${money(C.used)}${C.over > 0.5 ? ` · ${money(C.over)} over` : ` · ${money(C.left)} left`}${C.used - items > 1 ? ` · ${money(r2(C.used - items))} of it labour, stock or bills with no order line` : ""}${extra > 0.5 ? ` · selections budget ${money(extra)}` : ""}${share ? ` · ${share}` : ""}`
      : `${g.rows.length} item${1 === g.rows.length ? "" : "s"}${T.budget ? ` · budget ${money(T.budget)}` : ""}${share ? ` · ${share}` : ""}${T.bought ? ` · purchased ${money(T.bought)}` : ""}`;
  return phone
    ? `<div class="ps-gh" data-psgroup="${esc(g.key)}"${attrs}><div class="ps-ght" role="heading" aria-level="3" data-nocase>${esc(g.name)}</div><span class="ps-gs" data-nocase>${esc(say)}</span></div>`
    : `<tr class="ps-g" data-psgroup="${esc(g.key)}"${attrs}><td colspan="${span}"><b data-nocase>${esc(g.name)}</b><span class="ps-gs" data-nocase>${esc(say)}</span></td></tr>`;
}
// The lines whose items sit in more than one group: each budget once, after the groups.
function psAcrossHtml(across, phone, span) {
  if (!across.length) return "";
  const N = PS_GROUP_NOUN[psGroup] || PS_GROUP_NOUN.room,
    tot = r2(across.reduce((a, l) => a + l.budget, 0)),
    name = `Across ${N[1]}`,
    say = `${money(tot)} in ${across.length} estimate line${1 === across.length ? "" : "s"} whose items sit in more than one ${N[0]}, each counted once: ${across.map((l) => `${l.ref} ${money(l.budget)} (${l.groups.join(", ")})`).join("; ")}`;
  return phone
    ? `<div class="ps-gh ps-across" data-psacross="${tot}"><div class="ps-ght" role="heading" aria-level="3" data-nocase>${esc(name)}</div><span class="ps-gs" data-nocase>${esc(say)}</span></div>`
    : `<tr class="ps-g ps-across" data-psacross="${tot}"><td colspan="${span}"><b data-nocase>${esc(name)}</b><span class="ps-gs" data-nocase>${esc(say)}</span></td></tr>`;
}
function psSelHtml(id, label, cur, opts) {
  return `<select id="${id}" class="ps-sel" aria-label="${esc(label)}"><option value="">${esc(label)}: All</option>${opts.map(([v, n]) => `<option value="${esc(v)}" ${cur === v ? "selected" : ""}>${esc(n)}</option>`).join("")}</select>`;
}
function psRender(root) {
  const phone = psPhone(),
    V = psView(),
    rows = V.rows,
    all = V.all,
    inJob = "function" == typeof jpOn && jpOn(),
    count = (f) => {
      const M = new Map();
      all.forEach((x) => {
        const k = f(x);
        M.set(k, (M.get(k) || 0) + 1);
      });
      return [...M.entries()].sort((a, b) => tvNatCmp(a[0], b[0]));
    },
    // each option's number is the rows it shows with the other filters as they are
    within = (skip) => all.filter((x) => (skip === "room" || !psF.room || psRoomKey(x) === psF.room) && (skip === "vendor" || !psF.vendor || (x.vendor || "No vendor") === psF.vendor) && (skip === "status" || !psF.status || x.status === psF.status)),
    nOf = (skip, f, v) => within(skip).filter((x) => f(x) === v).length,
    rooms = count(psRoomKey).map(([k]) => [k, `${k} (${nOf("room", psRoomKey, k)})`]),
    vendors = count((x) => x.vendor || "No vendor").map(([k]) => [k, `${k} (${nOf("vendor", (x) => x.vendor || "No vendor", k)})`]),
    sts = PS_STATUS.filter(([k]) => all.some((x) => x.status === k)).map(([k, w]) => [k, `${w} (${nOf("status", (x) => x.status, k)})`]),
    projs = (DB.projects || []).filter((p) => !p.archived).map((p) => [p.id, puJob(p)]),
    T = psTotals(rows),
    picked = [...psPick].map((id) => rows.find((x) => x.id === id) || all.find((x) => x.id === id)).filter(Boolean);
  [...psPick].forEach((id) => all.some((x) => x.id === id && x.pickable) || psPick.delete(id));
  const nOn = [psF.room, psF.vendor, psF.q, inJob ? "" : ("undefined" != typeof bbProj && bbProj) || ""].filter(Boolean).length + (psSorts.length ? 1 : 0) + ("room" !== psGroup ? 1 : 0),
    toolsBtn = phone ? `<button type="button" class="btn ps-toolsb" data-pstools="1" aria-expanded="${psToolsOpen}">${PS_IC.filter}<span>Filter and Sort${nOn ? ` (${nOn})` : ""}</span></button>` : "";
  const filters = `${toolsBtn}<div class="ps-tools"${phone && !psToolsOpen ? " hidden" : ""}>${inJob ? "" : psSelHtml("ps-job", "Job", ("undefined" != typeof bbProj && bbProj) || "", projs)}${psSelHtml("ps-room", "Room", psF.room, rooms)}${psSelHtml("ps-vendor", "Vendor", psF.vendor, vendors)}${
      phone ? "" : psSelHtml("ps-status", "Status", psF.status, sts)
    }<select id="ps-group" class="ps-sel" aria-label="Group by">${[["room", "Room"], ["inv", "Invoice"], ["vendor", "Vendor"], ["status", "Status"], ["job", "Job"], ["none", "None"]].map(([v, n]) => `<option value="${v}" ${psGroup === v ? "selected" : ""}>Group by ${n}</option>`).join("")}</select>${
      phone ? `<select id="ps-sort" class="ps-sel" aria-label="Sort by"><option value="">Sort: Status</option>${PS_COLS.map((c) => `<option value="${c.k}" data-pssort="${c.k}" ${psSorts[0] && psSorts[0].k === c.k ? "selected" : ""}>Sort: ${esc(c.n)}${psSorts[0] && psSorts[0].k === c.k ? ("desc" === psSorts[0].dir ? ", High to Low" : ", Low to High") : ""}</option>`).join("")}</select>` : ""
    }<input id="ps-q" class="ps-q" type="search" placeholder="Search item, SKU, vendor" aria-label="Search the items" value="${esc(psF.q)}"></div>${
      phone ? `<div class="ps-chips" role="group" aria-label="Status">${[["", `All (${within("status").length})`]].concat(sts).map(([k, w]) => `<button type="button" class="ps-chipb${psF.status === k ? " on" : ""}" data-psst="${esc(k)}" aria-pressed="${psF.status === k}">${esc(w)}</button>`).join("")}</div>` : ""
    }`,
    rb = all.rb || [],
    rbAmt = r2(rb.reduce((a, x) => a + (+x.cost || 0), 0)),
    sum = `<div class="ps-sum" data-nocase><span class="ps-n" data-pscount="${rows.length}"><b>${rows.length}</b> item${1 === rows.length ? "" : "s"}</span><span data-pstot="budget" data-v="${T.budget}">Budget <b>${money(T.budget)}</b></span><span data-pstot="bought" data-v="${T.bought}">Purchased <b>${money(T.bought)}</b></span>${
      T.over ? `<span class="bad" data-pstot="over" data-v="${T.over}">Over budget <b>${money(T.over)}</b></span>` : ""
    }${T.under ? `<span class="good" data-pstot="under" data-v="${T.under}">Under budget <b>${money(T.under)}</b></span>` : ""}${T.poOver ? `<span class="bad" data-pstot="poover" data-v="${T.poOver}">Over the order <b>${money(T.poOver)}</b></span>` : ""}${
      rb.length ? `<span class="bad" data-pstot="notbilled" data-v="${rb.length}"><b>${rb.length}</b> bought for the client, not billed back (${money(rbAmt)})</span>` : ""
    }${T.unbacked ? `<span class="bad" data-pstot="noorder" data-v="${T.unbacked}"><b>${T.unbacked}</b> marked bought, no order on file</span>` : ""}${T.recvNoOrder ? `<span class="warn" data-pstot="recvnoorder" data-v="${T.recvNoOrder}"><b>${T.recvNoOrder}</b> received, no order on file</span>` : ""}${
      T.typed ? `<span class="warn" data-pstot="typed" data-v="${T.typed}">Typed from a receipt, no bill behind it <b>${money(T.typed)}</b></span>` : ""
    }${T.imported ? `<span class="warn" data-pstot="imported" data-v="${T.imported}">Imported, no bill behind it <b>${money(T.imported)}</b></span>` : ""}</div>`,
    exp = `<div class="ps-x"><button type="button" class="btn" data-psx="csv">${PS_IC.dl}<span>Export CSV</span></button><button type="button" class="btn" data-psx="client">${PS_IC.print}<span>Client FF&amp;E Schedule</span></button><button type="button" class="btn" data-psx="internal">${PS_IC.print}<span>Internal Schedule</span></button>${psRO() ? "" : `<button type="button" class="btn" data-psx="import">${PS_IC.up2}<span>Import a Sheet</span></button>`}</div>`,
    G = psGroups(rows),
    across = "none" === psGroup ? [] : psGroupShare(G),
    span = PS_COLS.length + 1,
    body = !rows.length
      ? `<p class="pu-empty" data-nocase>No items${psF.room || psF.vendor || psF.status || psF.q ? " match these filters" : " on this job yet"}.</p>`
      : phone
        ? `<div class="ps-cards">${G.map((g) => psGroupHead(g, !0) + g.rows.map(psCardHtml).join("")).join("")}${psAcrossHtml(across, !0)}</div>`
        : `<div class="ps-wrap"><table class="ps-t"><thead><tr><th class="ps-pkc" aria-label="Pick"></th>${PS_COLS.map((c) => {
            const s = psSorts[0] && psSorts[0].k === c.k ? psSorts[0] : null;
            return `<th data-pscol="${c.k}" class="ps-c-${c.k}${c.num ? " num" : ""}"${c.w ? ` style="width:${c.w}px"` : ""} aria-sort="${s ? ("desc" === s.dir ? "descending" : "ascending") : "none"}"><button type="button" class="ps-sortb" data-pssort="${c.k}" title="Sort by ${esc(c.n)}">${esc(c.n)}${s ? ("desc" === s.dir ? PS_IC.down : PS_IC.up) : ""}</button></th>`;
          }).join("")}</tr></thead><tbody>${G.map((g) => psGroupHead(g, !1, span) + g.rows.map(psRowHtml).join("")).join("")}${psAcrossHtml(across, !1, span)}</tbody></table></div>`;
  let bar = "";
  if (picked.length) {
    const priced = picked.filter((x) => x.r && +x.r.price > 0),
      total = r2(priced.reduce((a, x) => a + +x.r.price, 0)),
      quotes = priced.length < picked.length || total > 2500;
    bar = `<div class="ps-bar bb-bar" data-nocase><span class="ps-bt"><b>${picked.length} picked</b>${total ? ` · ${money(total)} to buy` : ""}${quotes ? " · three quotes over $2,500" : ""}</span><button type="button" class="btn${quotes ? " primary" : ""}" data-psdo="quote">Request Quotes</button><button type="button" class="btn${quotes ? "" : " primary"}" data-psdo="order">Order</button><button type="button" class="btn ps-clear" data-psdo="clear">Clear</button></div>`;
  }
  root.innerHTML = `<div class="pu pr-keep ps ${phone ? "ps-phone" : "ps-desk"}${picked.length ? " ps-picking" : ""}" data-pupage="proc" id="pu-table" data-os-keep>${puHeadHtml("proc")}${psModesHtml()}${filters}${sum}${body}${exp}${bar}</div>`;
  psWire(root);
}
function psWire(root) {
  const q = (s) => root.querySelector(s),
    re = () => render();
  root.querySelectorAll("[data-psmode]").forEach((b) => (b.onclick = () => (psChoose("table" === b.dataset.psmode), psPick.clear(), re())));
  q("[data-pstools]") && (q("[data-pstools]").onclick = () => ((psToolsOpen = !psToolsOpen), re()));
  root.querySelectorAll("[data-pssort]").forEach((b) => b.matches("button") && (b.onclick = () => psSortBy(b.dataset.pssort)));
  root.querySelectorAll("[data-psst]").forEach((b) => (b.onclick = () => ((psF.status = b.dataset.psst), re())));
  [["#ps-room", "room"], ["#ps-vendor", "vendor"], ["#ps-status", "status"]].forEach(([s, k]) => {
    const el = q(s);
    el && (el.onchange = () => ((psF[k] = el.value), re()));
  });
  q("#ps-job") && (q("#ps-job").onchange = () => ((bbProj = q("#ps-job").value), (psF.room = ""), re()));
  q("#ps-group") && (q("#ps-group").onchange = () => ((psGroup = q("#ps-group").value), re()));
  q("#ps-sort") &&
    (q("#ps-sort").onchange = () => {
      const k = q("#ps-sort").value;
      k ? psSortBy(k, psSorts[0] && psSorts[0].k === k && "asc" === psSorts[0].dir ? "desc" : "asc") : ((psSorts = []), re());
    });
  const qi = q("#ps-q");
  qi &&
    (qi.oninput = () => {
      psF.q = qi.value;
      clearTimeout(psWire.t);
      psWire.t = setTimeout(() => {
        re();
        const n = document.querySelector("#ps-q");
        n && (n.focus(), n.setSelectionRange(n.value.length, n.value.length));
      }, 250);
    });
  root.querySelectorAll("[data-pspick]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.stopPropagation();
        const id = b.dataset.pspick;
        psPick.has(id) ? psPick.delete(id) : psPick.add(id), re();
      }),
  );
  root.querySelectorAll("[data-psrow]").forEach(
    (tr) =>
      (tr.onclick = (e) => {
        if (e.target.closest("[data-pspick], .ps-pk, a, [data-psfind]")) return;
        psOpen(tr.dataset.psrow);
      }),
  );
  root.querySelectorAll("[data-psfind]").forEach((b) => (b.onclick = (e) => (e.stopPropagation(), psFindOrder(b.dataset.psfind))));
  root.querySelectorAll("[data-psinv]").forEach(
    (a) =>
      (a.onclick = (e) => {
        e.preventDefault(), e.stopPropagation();
        const x = psAll().find((y) => y.id === a.dataset.psinv);
        x && x.invDoc ? flowGo.doc(x.invDoc.c, "invoice", x.invDoc.d)() : toast("That invoice is no longer on file");
      }),
  );
  root.querySelectorAll("[data-psdo]").forEach((b) => (b.onclick = () => psDo(b.dataset.psdo)));
  root.querySelectorAll("[data-psx]").forEach(
    (b) =>
      (b.onclick = () => {
        const k = b.dataset.psx;
        "csv" === k ? psCsv(!0) : "client" === k ? psPrint(!0) : "internal" === k ? psPrint(!1) : psImportSheet();
      }),
  );
}
// a row opens its record: the order, the request for quote, the need's sheet, the selection
function psOpen(id) {
  const x = psAll().find((y) => y.id === id);
  if (!x) return toast("That item is no longer on the list");
  const live = x.pos.find((po) => "draft" !== po.status) || x.pos[0];
  if (live) return flowGo.po(live)();
  const rq = x.r && (x.r.rfqs || [])[0];
  if ("pricing" === x.status && rq && "function" == typeof rfqOpenFor) return rfqOpenFor(rq.id);
  const need = x.r && ["buy", "arriving"].includes(x.r.tab) ? x.r : null;
  if (need) return bbSheet(need);
  if (x.it && "function" == typeof selOpenItem) return selOpenItem(x.it.id);
  if (x.m && "function" == typeof openEditor) return openEditor("mat", x.m.id);
  toast("Nothing more to open on this item");
}
// Find the Order: a row bought by its mark or its receipt, with no order on file, is linked to the order line that bought
// it. The candidates are the job's order lines nobody's item stands for (the table's own order rows), the vendor's and
// the closest words first. Linking writes the order line's own link (materialId, selId), as an order made from the row
// does, so the row then reads the order's price, dates and bills. A material only marked ordered can be put back to buy.
function psFindOrder(id) {
  if (psRO()) return toast("Purchasing is read only for your role: the coordinator finds the order");
  const all = psItems(""),
    x = all.find((y) => y.id === id);
  if (!x || !(x.m || x.it)) return toast("That item is no longer on the list");
  const words = (t) => new Set(String(t || "").toLowerCase().split(/[^a-z0-9]+/).filter((w) => w.length > 2)),
    W = words(x.desc),
    C = all
      .filter((y) => y !== x && y.pid === x.pid && y.r && y.r.pl && y.r.po && 1 === y.pls.length && "draft" !== y.r.po.status && !y.r.pl.materialId && !y.r.pl.selId && !y.r.pl.requestId)
      .map((y) => {
        const H = words(`${y.desc} ${y.r.pl.desc || ""}`);
        return { po: y.r.po, pl: y.r.pl, score: 2 * [...W].filter((w) => H.has(w)).length + (x.vendor && y.vendor === x.vendor ? 3 : 0) + (x.lineKey && y.lineKey === x.lineKey ? 1 : 0) };
      })
      .sort((a, b) => b.score - a.score),
    back = x.m && "purchased" === x.marked;
  const m = mbModal(
    `Find the Order — <span data-nocase>${esc(x.desc)}</span>`,
    `<p class="small muted" style="margin:0 0 8px" data-nocase>${esc(x.desc)}, ${esc(x.job)}: ${esc(psMarkSay(x).toLowerCase())}, with no order on file. ${C.length ? "Pick the order line that bought it; the vendor's and the closest words are first. The row then reads the order's price, dates and bills." : "No order line on this job is waiting for an item: every one already stands for something."}${back ? " If it was never ordered, put it back to buy." : ""}</p><div class="bb-links">${C.map((c, i) => `<label class="bb-link"><input type="radio" name="psfo" data-psfo="${esc(c.po.id + ":" + c.pl.id)}" ${0 === i && c.score > 1 ? "checked" : ""}><span><b data-nocase>${esc(c.po.number)} · ${esc(c.po.vendor || "")}</b><span class="small muted" data-nocase>${esc(c.pl.item || c.pl.desc || "Order line")} · ${esc(`${+c.pl.qty || 0} ${c.pl.unit || ""}`.trim())} · ${money(psExt(c.pl))}${c.po.date ? ` · ordered ${fmt(c.po.date)}` : ""}${c.score > 1 ? " · matches it" : ""}</span></span></label>`).join("")}</div>`,
    {
      submit: C.length ? "Link the Order" : null,
      alt: back
        ? {
            label: "It Was Not Ordered",
            run: () => {
              const was = x.m.status;
              (x.m.status = "not-ordered"), (x.m.po = "");
              try {
                audit("material", x.m.id, "status", was, "not-ordered", "Find the Order on the Buy Board: no order on file, back to buy");
              } catch (e) {}
              save(), render();
              toast(`${x.desc} is back to buy: no order was on file`, { label: "Open", run: () => psOpen(id) });
            },
          }
        : void 0,
      onSubmit: () => {
        const el = m.querySelector("[data-psfo]:checked"),
          c = el && C.find((k) => k.po.id + ":" + k.pl.id === el.dataset.psfo);
        if (!c) return toast("Pick the order line that bought it"), !1;
        x.m ? ((c.pl.materialId = x.m.id), (x.m.po = c.po.number), x.m.vendor || (x.m.vendor = c.po.vendor || "")) : ((c.pl.selId = x.it.id), (x.it.poId = c.po.id));
        try {
          audit("po", c.po.id, "line linked to its item", "", x.desc, `Find the Order on the Buy Board: ${c.po.number} · ${c.pl.item || c.pl.desc || ""}`);
        } catch (e) {}
        save(), render();
        toast(`${x.desc} is on ${c.po.number} from ${c.po.vendor || "the vendor"}`, { label: "Open", run: () => flowGo.po(c.po)() });
      },
    },
  );
  return m;
}
// Request Quotes and Order: the Buy Board's own doors (bbQuote reaches rfqStartFromLines through puQuoteDoor; bbOrder
// the one order sheet), each behind the stock check
function psDo(k) {
  if ("clear" === k) return psPick.clear(), render();
  if (psRO()) return toast("Purchasing is read only for your role: the coordinator orders and asks for quotes");
  const R = [...psPick].map((id) => psAll().find((x) => x.id === id)).filter((x) => x && x.pickable).map((x) => x.r);
  if (!R.length) return toast("Pick at least one item to buy");
  const out = "quote" === k ? bbQuote(R) : bbOrder(R);
  psPick.clear();
  return out;
}

// ---- export: CSV, and the FF&E schedule for the client (no cost) or the office (budget and purchased) ---------------
function psCsvRows(rows) {
  const head = PS_COLS.map((c) => c.n).concat(["Job", "Estimate Line", "Order"]);
  return [head].concat(
    rows.map((x) => [x.inv || "Not invoiced", null == x.lead ? "" : x.lead, x.sku, x.desc, x.qty || "", x.room, null != x.budget ? x.budget : x.shared ? `in the line (${x.shared.budget})` : "", null == x.bought ? "" : x.bought, x.vendor, psStatusWord(x), x.deliv, x.job, x.lineRef, x.boughtFrom || ""]),
  );
}
function psCsv(download) {
  const V = psView(),
    csv = asCsvOut(psCsvRows(V.rows));
  if (download)
    try {
      const a = document.createElement("a"),
        jobs = [...new Set(V.rows.map((x) => x.job))];
      (a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }))), (a.download = `Purchasing items ${1 === jobs.length ? jobs[0] : "all jobs"} ${today()}.csv`.replace(/[^\w .-]+/g, "")), document.body.appendChild(a), a.click(), a.remove();
      toast(`Exported ${V.rows.length} item${1 === V.rows.length ? "" : "s"} to CSV`);
    } catch (e) {
      toast("The CSV could not be saved");
    }
  return csv;
}
// The client's copy: what is chosen for each room, its state and when it comes. No cost, no vendor, no subcontract scope.
function psScheduleHtml(client) {
  const V = psView(),
    rows = V.rows.filter((x) => !client || !["sub", "line"].includes(x.kind)),
    jobs = [...new Set(rows.map((x) => x.job))],
    groups = new Map();
  rows.forEach((x) => {
    const k = (jobs.length > 1 ? x.job + " · " : "") + (x.room || "Not yet placed");
    groups.has(k) || groups.set(k, []), groups.get(k).push(x);
  });
  const cols = client
      ? [["Invoice", (x) => x.inv || ""], ["Item #", (x) => x.sku], ["Description", (x) => x.desc + (x.descSub ? `\n${x.descSub}` : "")], ["Qty", psQty], ["Status", (x) => psStatusWord(x)], ["Delivery Date", (x) => (x.deliv ? fmt(x.deliv) : "")]]
      : [["Invoice", (x) => x.inv], ["Lead Time", (x) => psDays(x.lead)], ["Item #", (x) => x.sku], ["Description", (x) => x.desc], ["Qty", psQty], ["Budget Price", (x) => (null != x.budget ? money(x.budget) : x.shared ? "in the line" : "")], ["Purchased Price", (x) => (null == x.bought ? "" : money(x.bought) + (x.over ? ` (${money(x.over)} over)` : x.under ? ` (${money(x.under)} under)` : ""))], ["Vendor", (x) => x.vendor], ["Status", (x) => psStatusWord(x)], ["Delivery Date", (x) => (x.deliv ? fmt(x.deliv) : "")]],
    T = psTotals(rows),
    co = (DB.company && DB.company.name) || "";
  return `<!doctype html><html><head><meta charset="utf-8"><title>FF&amp;E Schedule</title><style>body{font:12px/1.45 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:#1D2430;margin:32px}h1{font-size:22px;margin:0 0 4px}.s{color:#6B7383}h2{font-size:14px;margin:22px 0 6px;border-bottom:1px solid #E2E5EA;padding-bottom:4px}table{width:100%;border-collapse:collapse}th{text-align:left;font-size:11px;color:#4B5563;border-bottom:1px solid #E2E5EA;padding:5px 6px}td{padding:5px 6px;border-bottom:1px solid #F1F3F6;vertical-align:top;white-space:pre-line}.p{margin-top:16px}@media print{.p{display:none}}</style></head><body><h1>FF&amp;E Schedule</h1><div class="s">${esc([co, jobs.length === 1 ? jobs[0] : "All jobs", `Prepared ${fmtL(today())}`].filter(Boolean).join(" · "))}</div>${
    client ? "" : `<p>Budget ${money(T.budget)} · Purchased ${money(T.bought)}${T.over ? ` · Over ${money(T.over)}` : ""}${T.under ? ` · Under ${money(T.under)}` : ""}</p>`
  }${[...groups.entries()].map(([k, L]) => `<h2>${esc(k)}</h2><table><thead><tr>${cols.map(([n]) => `<th>${esc(n)}</th>`).join("")}</tr></thead><tbody>${L.map((x) => `<tr>${cols.map(([, f]) => `<td>${esc(String(f(x) || ""))}</td>`).join("")}</tr>`).join("")}</tbody></table>`).join("")}<button class="p" onclick="print()">Print</button></body></html>`;
}
function psPrint(client) {
  const w = window.open("", "_blank");
  if (!w) return toast("Allow pop-ups to print the schedule");
  w.document.write(psScheduleHtml(client)), w.document.close();
}

// ---- the one import: a coordinator's own sheet into the job's FF&E items -------------------------------------------
// The sheet's shape (invented demo, tests/pu_table_test.py): Alan's columns, with a section row per FM package and
// category ("FM1 - 1.Accessories and Hardware") whose package and category the items under it take.
const PS_IMP_COLS = [
  ["inv", /^(invoice|fm)/i],
  ["lead", /lead/i],
  ["sku", /item\s*#|sku|model|item no/i],
  ["desc", /desc/i],
  ["qty", /^q(ua)?n?ti?t?y?$|^qnty$|^qty$/i],
  ["room", /room|location|space/i],
  ["budget", /budget/i],
  ["bought", /purchas|actual|paid/i],
  ["vendor", /vendor|supplier|source/i],
  ["status", /status/i],
  ["deliv", /deliver|eta|arriv/i],
];
const psNum = (s) => {
  const v = parseFloat(String(s || "").replace(/[$,\s]/g, ""));
  return isFinite(v) ? v : 0;
};
function psLeadDays(s) {
  const t = String(s || "").trim();
  if (!t) return 0;
  const m = t.match(/(\d+(?:\.\d+)?)\s*(w|wk|wks|week|weeks)\b/i);
  if (m) return Math.round(+m[1] * 7);
  const d = t.match(/(\d+(?:\.\d+)?)/);
  return d ? Math.round(+d[1]) : 0;
}
function psStageOf(s) {
  const t = String(s || "").toLowerCase();
  return /install/.test(t) ? "inst" : /deliver|receiv|on site|arriv/.test(t) ? "site" : /office|warehouse/.test(t) ? "office" : /ship|transit/.test(t) ? "ship" : /purchas|order|bought/.test(t) ? "ord" : /approv/.test(t) ? "appr" : "sel";
}
function psDateOf(s) {
  const t = String(s || "").trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(t)) return t.slice(0, 10);
  const m = t.match(/^(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?$/);
  if (!m) return "";
  const y = m[3] ? (m[3].length === 2 ? "20" + m[3] : m[3]) : today().slice(0, 4);
  return `${y}-${String(m[1]).padStart(2, "0")}-${String(m[2]).padStart(2, "0")}`;
}
function psParseSheet(text) {
  const rows = asCsv(text),
    hi = rows.findIndex((r) => r.some((c) => /desc/i.test(c))),
    out = [];
  if (hi < 0) return { items: out, error: "No Description column: the first row with Description is read as the header." };
  const H = rows[hi],
    at = {};
  PS_IMP_COLS.forEach(([k, re]) => {
    const i = H.findIndex((h) => re.test(String(h).trim()));
    i >= 0 && !(k in at) && (at[k] = i);
  });
  let fm = "",
    cat = "";
  rows.slice(hi + 1).forEach((r) => {
    const v = (k) => (k in at ? String(r[at[k]] || "").trim() : ""),
      first = String(r[0] || "").trim(),
      sec = first.match(/^(FM\s*-?\s*\d+)\s*[-–—:]\s*(?:(\d+)\s*[.)]?\s*)?(.+)$/i);
    if (sec && r.slice(1).every((c) => !String(c || "").trim())) return void ((fm = sec[1].replace(/\s|-/g, "").toUpperCase()), (cat = sec[3].trim()));
    if (!v("desc")) return;
    const qty = psNum(v("qty")) || 1;
    out.push({ fm: (v("inv") || fm).replace(/\s|-/g, "").toUpperCase(), category: cat, lead: psLeadDays(v("lead")), sku: v("sku"), name: v("desc"), qty: qty, room: v("room"), cost: psNum(v("budget")), bought: psNum(v("bought")), vendor: v("vendor"), stage: psStageOf(v("status")), statusText: v("status"), deliv: psDateOf(v("deliv")) });
  });
  return { items: out, error: "" };
}
// One item on the job: the same FM number, the same room and the same SKU (or, with none, the same name). The sheet's own
// repeats count too: the second of two identical rows is not imported twice.
const psImpKey = (pid, x) => [pid, String(x.fm || "").toUpperCase(), String(x.room || "").trim().toLowerCase(), x.sku ? "#" + String(x.sku).trim().toLowerCase() : String(x.name || "").trim().toLowerCase()].join("|");
function psImpMark(pid, L) {
  const have = new Set(((DB.sel || {}).items || []).filter((i) => i.projectId === pid).map((i) => psImpKey(pid, i))),
    seen = new Set();
  return L.map((x) => {
    const k = psImpKey(pid, x),
      why = have.has(k) ? "already on this job" : seen.has(k) ? "repeats a row above" : "";
    seen.add(k);
    return Object.assign({}, x, { skip: why });
  });
}
// the sheet's prices: per unit (a budget of $145 for 2 is $290) or line totals (the $290 is the line); said in the preview
function psImpMoney(x, perUnit) {
  const q = +x.qty || 1;
  return perUnit ? { costEach: x.cost, budget: r2(x.cost * q), boughtEach: x.bought, bought: r2(x.bought * q) } : { costEach: r2(x.cost / q), budget: x.cost, boughtEach: r2(x.bought / q), bought: x.bought };
}
function psImportSheet() {
  if (psRO()) return toast("Purchasing is read only for your role: the coordinator imports the sheet");
  const P = (DB.projects || []).filter((p) => !p.archived),
    cur = psScope() || (S && S.id) || (P[0] || {}).id || "";
  let parsed = { items: [], error: "" };
  const marked = () => psImpMark(m.querySelector("#ps-imp-job").value, parsed.items),
    perUnit = () => "line" !== m.querySelector("#ps-imp-basis").value;
  const m = mbModal(
    "Import a Sheet",
    `<p class="small muted" data-nocase>Paste the purchasing sheet as CSV (Invoice, Lead Time, Item #, Description, Qty, Room, Budget Price, Purchased Price, Vendor, Status, Delivery Date), or choose the file. Each item becomes one of the job's FF&amp;E items. The sheet's purchased prices are kept as imported, not as what was paid: a bill or a bank line makes them true.</p><label class="f"><span>Job</span><select id="ps-imp-job">${P.map((p) => `<option value="${esc(p.id)}" ${p.id === cur ? "selected" : ""}>${esc(puJob(p))}</option>`).join("")}</select></label><label class="f"><span>The Sheet's Prices Are</span><select id="ps-imp-basis"><option value="unit">Per unit: the line is price x qty</option><option value="line">Line totals: already price x qty</option></select></label><label class="f"><span>File</span><input id="ps-imp-file" type="file" accept=".csv,text/csv"></label><label class="f"><span>Sheet</span><textarea id="ps-imp-text" rows="6" placeholder="Invoice,Lead Time,Item #,Description,..."></textarea></label><div class="ps-imp-prev" data-nocase></div>`,
    {
      submit: "Import",
      onSubmit: () => {
        const pid = m.querySelector("#ps-imp-job").value,
          p = (DB.projects || []).find((x) => x.id === pid),
          L = marked(),
          N = L.filter((x) => !x.skip),
          pu = perUnit();
        if (!p) return toast("Pick the job these items are for"), !1;
        if (!N.length) return toast(L.length ? "Every row is already on this job or repeats another: nothing imported" : "Nothing to import: paste the sheet first"), !1;
        let no = ((DB.sel || {}).items || []).filter((i) => i.projectId === pid).length;
        const who = (currentUser() || {}).name || "",
          rooms = ((DB.sel || {}).items || []).filter((i) => i.projectId === pid && i.room).map((i) => i.room),
          made = N.map((x) => {
            x = Object.assign({}, x, { room: rooms.find((r) => r.toLowerCase() === String(x.room || "").toLowerCase()) || x.room });
            const dates = { created: today(), approved: "", ordered: "", eta: "", office: "", site: "" },
              M = psImpMoney(x, pu);
            ["ord", "ship"].includes(x.stage) ? (dates.eta = x.deliv) : ["site", "office", "inst"].includes(x.stage) && (dates["office" === x.stage ? "office" : "site"] = x.deliv);
            // the budget is the selection's own (its unit cost); the purchased price is the sheet's word, kept beside it as
            // imported, never as the item's actual (no bill or bank line is behind it)
            return selNew({ projectId: pid, no: ++no, room: x.room, name: x.name, qty: x.qty, cost: M.costEach, vendor: x.vendor, sku: x.sku, leadDays: x.lead, fm: x.fm, stage: x.stage, category: x.category || "", dates: dates, actual: null, imported: { at: today(), from: "sheet", by: who, basis: pu ? "unit" : "line", bought: x.bought ? M.bought : 0, boughtEach: x.bought ? M.boughtEach : 0 }, by: who });
          });
        const skip = L.length - N.length;
        try {
          audit("sel", pid, "imported from a sheet", "", `${made.length} item${1 === made.length ? "" : "s"}: ${made.map((i) => [i.fm, i.name].filter(Boolean).join(" ")).join("; ").slice(0, 400)}`, `Import a Sheet on the Buy Board${skip ? `; ${skip} row${1 === skip ? "" : "s"} skipped` : ""}; prices read as ${pu ? "per unit" : "line totals"}; purchased prices kept as imported`, { by: who || void 0 });
        } catch (e) {}
        save();
        toast(`Imported ${made.length} item${1 === made.length ? "" : "s"} to ${puJob(p)}${skip ? `; ${skip} skipped` : ""}`, { label: "Open", run: () => ((bbProj = pid), psChoose(!0), (psF = { room: "", vendor: "", status: "", q: "" }), setView("proc")) });
        setTimeout(() => render(), 0);
      },
    },
  );
  const draw = () => {
    const L = marked(),
      n = L.filter((x) => !x.skip).length,
      dup = L.filter((x) => "already on this job" === x.skip).length,
      rep = L.length - n - dup,
      pu = perUnit(),
      ok = m.querySelector("#mbm-ok"),
      each = (v, t) => (pu ? `${unitMoney(v)} each, ${money(t)}` : `${money(t)} for the line, ${unitMoney(v)} each`);
    m.querySelector(".ps-imp-prev").innerHTML = parsed.error
      ? `<p class="warn">${esc(parsed.error)}</p>`
      : L.length
        ? `<p class="ps-imp-sum">${n ? `${n} item${1 === n ? "" : "s"} to import` : "Nothing new to import"}${dup ? `; ${dup} already on this job` : ""}${rep ? `; ${rep} repeat${1 === rep ? "s" : ""} a row above` : ""}</p>${L.map((x) => {
            const M = psImpMoney(x, pu);
            return `<div class="ps-imp-row${x.skip ? " dup" : ""}">${esc([x.fm, x.category, x.name, x.room, `qty ${x.qty}`, x.statusText || "pricing"].filter(Boolean).join(" · "))}<span class="ps-imp-m">Budget ${x.cost ? esc(each(M.costEach, M.budget)) : "none"} · Purchased ${x.bought ? esc(each(M.boughtEach, M.bought)) + " (imported)" : "none"}${x.skip ? ` · ${esc(x.skip)}` : ""}</span></div>`;
          }).join("")}`
        : "";
    ok && (ok.textContent = n > 0 ? `Import ${n} Item${1 === n ? "" : "s"}` : "Import");
  };
  const ta = m.querySelector("#ps-imp-text");
  ta.oninput = () => ((parsed = psParseSheet(ta.value)), draw());
  m.querySelector("#ps-imp-job").onchange = draw;
  m.querySelector("#ps-imp-basis").onchange = draw;
  m.querySelector("#ps-imp-file").onchange = (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    const rd = new FileReader();
    (rd.onload = () => ((ta.value = String(rd.result || "")), (parsed = psParseSheet(ta.value)), draw())), rd.readAsText(f);
  };
  return m;
}

// ---- where it lives: the Buy Board's switch (the board and the job's Purchasing tab draw through puBuyRender) ---------
{
  const base = puBuyRender;
  puBuyRender = function () {
    const root = document.getElementById("proc-body");
    if (root && psIsOn()) {
      try {
        return psRender(root);
      } catch (e) {
        console.warn("item table", e);
      }
    }
    const out = base.apply(this, arguments);
    try {
      const bb = root && root.querySelector("#buy-board");
      if (bb && !bb.querySelector(".ps-modes")) {
        const head = bb.querySelector(":scope > .pu-ph"),
          w = document.createElement("div");
        w.innerHTML = psModesHtml();
        const el = w.firstElementChild;
        head ? head.after(el) : bb.insertBefore(el, bb.firstChild);
        el.querySelectorAll("[data-psmode]").forEach((b) => (b.onclick = () => (psChoose("table" === b.dataset.psmode), psPick.clear(), render())));
      }
    } catch (e) {}
    return out;
  };
}
(function psStyle() {
  if (document.getElementById("ps-style")) return;
  const st = document.createElement("style");
  st.id = "ps-style";
  st.textContent = `
.ps-modes{display:inline-flex;border:1px solid var(--rule);border-radius:8px;overflow:hidden;margin:4px 0 10px;background:var(--paper)}
.ps-mode{display:inline-flex;align-items:center;gap:6px;border:0;background:transparent;padding:0 14px;min-height:34px;font-size:12.5px;color:var(--ink-2);cursor:pointer}
.ps-mode .n{margin-left:4px;background:var(--bad);color:#fff;border-radius:9px;font-size:11px;font-weight:600;padding:0 6px;line-height:16px}
.ps-mode+.ps-mode{border-left:1px solid var(--rule)} .ps-mode.on{background:var(--accent-2);color:var(--accent-3);font-weight:600}
.ps .ps-tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 8px} .ps .ps-tools[hidden],.ps-card [hidden]{display:none !important}
.ps .ps-sel,.ps .ps-q{min-height:32px;border:1px solid var(--rule);border-radius:6px;background:var(--paper);padding:0 8px;font-size:12.5px;max-width:100%}
.ps .ps-q{min-width:200px;flex:1 1 200px}
.ps-sum{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline;font-size:12.5px;color:var(--ink-2);margin:2px 0 10px}
.ps-sum b{color:var(--ink);font-variant-numeric:tabular-nums} .ps-sum .bad,.ps-sum .bad b{color:var(--bad)} .ps-sum .good,.ps-sum .good b{color:var(--ok)} .ps-sum .warn{color:var(--warn)}
.ps-wrap{overflow-x:auto;border:1px solid var(--rule);border-radius:8px;background:var(--paper)}
table.ps-t{width:100%;border-collapse:collapse;font-size:12.5px;table-layout:auto}
table.ps-t th{position:sticky;top:0;background:var(--paper-3);text-align:left;font-size:11.5px;font-weight:600;color:var(--ink-2);border-bottom:1px solid var(--rule);padding:0;white-space:nowrap;z-index:1}
table.ps-t th.num{text-align:right}
.ps-sortb{display:inline-flex;align-items:center;gap:4px;border:0;background:transparent;font:inherit;color:inherit;padding:8px 8px;cursor:pointer;width:100%;justify-content:inherit}
table.ps-t th.num .ps-sortb{justify-content:flex-end}
table.ps-t td{padding:7px 8px;border-bottom:1px solid var(--rule-2);vertical-align:top}
@media (min-width:761px){
  /* a fixed grid that fits the content width at 1440: nothing to scroll sideways */
  .ps-wrap{overflow-x:hidden}
  table.ps-t{table-layout:fixed;font-size:12px}
  table.ps-t td{padding:6px 7px}
  table.ps-t .ps-sub,table.ps-t .ps-main,table.ps-t .ps-inv{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  table.ps-t .ps-chip{max-width:100%;overflow:hidden;text-overflow:ellipsis;vertical-align:top}
  table.ps-t .ps-chip.long{white-space:normal}
  table.ps-t .ps-find{max-width:100%;padding:0 8px}
  table.ps-t .ps-open b{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
}
table.ps-t td.num{text-align:right;font-variant-numeric:tabular-nums}
table.ps-t tr[data-psrow]{cursor:pointer} table.ps-t tr[data-psrow]:hover td{background:var(--paper-2)} table.ps-t tr.on td{background:var(--accent-2)}
table.ps-t tr.ps-g td{background:var(--paper-3);font-size:12px;color:var(--ink-2);padding:6px 10px}
.ps-g b,.ps-gh .ps-ght{color:var(--ink);font-weight:600;margin-right:10px} .ps-gs{color:var(--ink-3);font-size:12px}
.ps-pkc{width:28px} .ps-pk{display:inline-flex;align-items:center;justify-content:center;min-width:24px;min-height:24px;cursor:pointer}
.ps-main{display:block} .ps-mono{font-family:var(--mono);font-size:11.5px} .ps-dim{color:var(--ink-3)}
.ps-sub{display:block;color:var(--ink-3);font-size:11.5px;line-height:1.35} .ps-sub.bad,.ps-main.bad{color:var(--bad);font-weight:600} .ps-sub.good{color:var(--ok);font-weight:600} .ps-sub.warn{color:var(--warn)}
.ps-inv{color:var(--accent);font-weight:600;text-decoration:none} .ps-inv:hover{text-decoration:underline} .ps-main.warn{color:var(--warn)}
.ps-open{border:0;background:transparent;padding:0;text-align:left;font:inherit;color:var(--ink);cursor:pointer} .ps-open:hover b{color:var(--accent)}
.ps-chip{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11.5px;font-weight:600;background:var(--neutral-2);color:var(--neutral);white-space:nowrap}
.ps-chip.long{white-space:normal;border-radius:8px;line-height:1.3;padding:2px 8px}
.ps-find{margin-top:4px;white-space:nowrap} .ps-act{margin-top:8px}
.ps-sub.blue{color:var(--info)} .ps-chip.blue{background:var(--info-2);color:var(--info)} .ps-chip.green{background:var(--ok-2);color:var(--ok)} .ps-chip.amber{background:var(--warn-2);color:var(--warn)} .ps-chip.red{background:var(--bad-2);color:var(--bad)}
.ps-x{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.ps-x .btn{display:inline-flex;align-items:center;gap:6px}
.ps-bar{position:sticky;bottom:0;display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:var(--paper);border:1px solid var(--rule);border-radius:8px;padding:8px 10px;margin-top:10px;box-shadow:0 -2px 8px rgba(0,0,0,.06)}
.ps-bar .ps-bt{flex:1 1 auto;font-size:12.5px}
.ps-imp-prev{margin-top:8px;font-size:12.5px} .ps-imp-row{padding:4px 0;border-bottom:1px solid var(--rule-2)} .ps-imp-row.dup{color:var(--ink-3);text-decoration:line-through} .ps-imp-sum{font-weight:600;margin:0 0 4px} .ps-imp-m{display:block;color:var(--ink-3);font-size:12px}
.ps-phone .ps-modes{display:flex;width:100%}
.ps-modes .ps-mode{flex:1 1 0;justify-content:center}
@media (max-width:760px){
  .ps-modes{display:flex;width:100%}
  /* the page's own rule for buttons in a view (.view.on button:not(...)) sets 36px; the id makes these the person's 44 */
  #v-proc .ps-mode,#v-proc .ps-chipb,#v-proc .ps-x .btn,#v-proc .ps-bar .btn,#v-proc .ps-card .ps-open,#v-proc .ps-card .ps-find{min-height:44px}
  .ps-card .ps-find{margin-top:0;padding:0 16px}
  .ps .ps-tools{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .ps .ps-sel,.ps .ps-q{min-height:44px;width:100%;min-width:0;font-size:14px}
  .ps .ps-q{grid-column:1 / -1}
  .ps-chips{display:flex;flex-wrap:wrap;gap:8px;padding:2px 0 8px;margin:0 0 4px}
  .ps-chipb{flex:0 0 auto;min-height:44px;padding:0 14px;border:1px solid var(--rule);border-radius:22px;background:var(--paper);font-size:13px;color:var(--ink-2);white-space:nowrap}
  .ps-chipb.on{background:var(--accent-2);border-color:var(--accent);color:var(--accent-3);font-weight:600}
  .ps-gh{margin:14px 0 6px} .ps-gh .ps-ght{font-size:14px;margin:0;display:block} .ps-gh .ps-gs{display:block}
  .ps-card{display:flex;gap:8px;background:var(--paper);border:1px solid var(--rule);border-radius:10px;padding:10px;margin:0 0 8px;min-width:0}
  .ps-card.on{border-color:var(--accent);background:var(--accent-2)}
  .ps-card .ps-pk{min-width:44px;min-height:44px;flex:0 0 44px;margin:-4px 0 0 -4px;align-self:flex-start}
  .ps-toolsb{display:flex;width:100%;justify-content:center;gap:6px;margin:0 0 8px}
  #v-proc .ps-toolsb{min-height:44px}
  .ps-cb{flex:1 1 auto;min-width:0}
  .ps-ct{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
  .ps-ct [data-pscol="desc"]{flex:1 1 auto;min-width:0} .ps-ct [data-pscol="status"]{flex:0 0 auto;text-align:right;max-width:46%}
  .ps-card .ps-open{display:block;min-height:44px;width:100%;font-size:14px;overflow-wrap:anywhere}
  .ps-cl{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 8px;font-size:13px;margin-top:4px;min-width:0}
  .ps-cl > [data-pscol]{min-width:0;overflow-wrap:anywhere}
  .ps-k{color:var(--ink-3);font-size:11.5px;flex:0 0 auto}
  .ps-cl .ps-main{display:inline}
  .ps-meta{font-size:12px}
  .ps-card .ps-inv{display:inline-flex;align-items:center;min-height:44px;min-width:44px}
  .ps-x .btn{min-height:44px;flex:1 1 calc(50% - 8px);justify-content:center}
  .ps-bar{bottom:calc(var(--bb-tabs, 64px) + 6px)} .ps-bar .btn{min-height:44px}
}`;
  document.head.appendChild(st);
})();
