/* =====================================================================================================================
   Purchasing, lane P3 (Alan, 11-05 evening: "go full force on the purchasing module"; docs/mockups/purchasing/SPEC.md):
   the Orders page's one New, the purchase order's own page, the vendor's first screen, and the read-only Purchasing
   pages of the controller and billing. Rides right after src/purchasing.js, so its wrappers sit outside that file's.

   What was wrong (the screen capture of 11-05 and the coordinator expert's day):
   - Orders had "+ New" and "New PO" side by side, opening two different sheets for the same order.
   - Opening an order showed the firm's seven-tile documents panel and a "Purchase Orders" heading above the order, and
     the next step sat at the foot of a long page (Close PO was the blue on an order paid $3,800 past its total).
   - The vendor's page had no price history, no returns and nothing owed back; the list said nothing of open orders.
   The record is the order first: who, which job, its state, each line with its estimate line, received against
   ordered, billed against ordered, paid; then one blue, the safe next step. The order's paper and its documents follow.
   ===================================================================================================================== */

// ---- New: one sheet for a new order (Which Lines? on the job, its Start Blank the blank order) --------------------------
// The jobs a New PO can buy for from their lines: the same documents newPODialog reads (src/app.js, "New PO opens on the
// job's lines"), so the job picked here never lands on the blank form by surprise.
function puPOJobs() {
  return (DB.projects || []).filter((p) => {
    if (p.archived) return !1;
    const c = (DB.clients || []).find((x) => x.id === p.clientId);
    return (
      !!c &&
      [
        ...(c.estimates || []).filter((e) => !["rejected", "expired"].includes(e.status) && (!e.projectId || e.projectId === p.id)),
        ...(c.changeOrders || []).filter((x) => ["approved", "billed"].includes(x.status) && (!x.projectId || x.projectId === p.id)),
        ...(c.invoices || []).filter((x) => "sov" !== x.mode && "void" !== x.status && (!x.projectId || x.projectId === p.id)),
      ].some((d) => (d.lines || []).length)
    );
  });
}
// From lines: the job on screen (or the job the person last worked), with a Job switch on the sheet itself when more
// than one job has lines. Blank: the same form's blank start (shop supplies, tools), on the job on screen.
function puNewPOFromLines(blank) {
  const P = puPOJobs(),
    inJob = "function" == typeof puInJob ? puInJob() : "",
    cur = inJob || (S && P.some((p) => p.id === S.id) ? S.id : P[0] ? P[0].id : "");
  if (blank) return newPODialog({ blank: !0 });
  if (!cur) return toast("No job has an estimate, change order or invoice to buy from yet. Start a blank order from More.");
  S && S.id !== cur && setCurrent(cur);
  newPODialog();
  puPOJobSwitch(P, cur);
}
function puPOJobSwitch(P, cur) {
  const m = document.getElementById("mbm");
  if (!m || P.length < 2 || m.querySelector("#pu-pojob")) return;
  const at = m.querySelector(".mbm-bd, .mbm-body") || m.querySelector(".mbm-box");
  if (!at) return;
  const w = document.createElement("label");
  (w.className = "f pu-pojob"),
    (w.innerHTML = `<span>Job</span><select id="pu-pojob" aria-label="Job">${P.map((p) => `<option value="${esc(p.id)}" ${p.id === cur ? "selected" : ""}>${esc(puJob(p))}</option>`).join("")}</select>`),
    at.insertBefore(w, at.firstChild);
  w.querySelector("select").onchange = (e) => {
    const j = e.target.value;
    "function" == typeof mbCloseModal && mbCloseModal(), setCurrent(j), render(), setTimeout(() => puNewPOFromLines(), 0);
  };
}

// ---- the purchase order's own page -------------------------------------------------------------------------------------
const PU_PO_WORD = { draft: "Draft", pending: "Waiting for Approval", issued: "Issued", partial: "Partly Received", received: "Received", closed: "Closed", cancelled: "Cancelled" };
function puPoBills(po) {
  return (DB.bills || []).filter((b) => b.poId === po.id && !["void", "rejected"].includes(b.status));
}
// a line's billed amount, when a bill line names it (its PO line or its estimate line); null when bills are not split by line
function puPoLineBilled(po, l) {
  const B = puPoBills(po).flatMap((b) => b.lines || []),
    on = B.filter((x) => (x.poLine && x.poLine === l.id) || (l.line && x.line === l.line));
  return on.length ? r2(on.reduce((a, x) => a + (+x.amount || 0), 0)) : null;
}
function puLineLabel(po, l) {
  if (!l.line) return "";
  try {
    const o = lineOptions(po.projectId).find((x) => x.key === l.line);
    if (o) return o.label;
  } catch (e) {}
  return /^overhead/.test(l.line) ? "Overhead" : "";
}
// the one safe next step on an order: an order paid or billed past its total is settled on its bill first (never closed);
// otherwise the order page's own blue (Receive All, Close PO, Mark Work Complete) or a draft's Submit or Issue
function puPoNext(po, doc) {
  const over = "function" == typeof puOverOrder ? puOverOrder(po.projectId).find((x) => x.po.id === po.id) : null;
  if (over) {
    const b = puPoBills(po).sort((a, c) => String(c.date || "").localeCompare(String(a.date || "")))[0];
    return { over: over, make: b ? { label: "Open the Bill", run: () => flowGo.bill(b)() } : null, say: `Paid or billed ${money(over.out)} on an order of ${money(over.tot)}: ${money(over.over)} over. Ask ${po.vendor || "the vendor"} for the credit on the bill, or approve the difference with a reason; do not close the order until it is settled.` };
  }
  const own = [...doc.querySelectorAll("button.primary")].filter((x) => !x.closest("#pu-poh, #mbm, .modal") && !x.disabled && x.offsetParent !== null);
  const pick = own.find((x) => x.closest(".docacts")) || own[0] || ("draft" === po.status || "pending" === po.status ? [...doc.querySelectorAll(".docacts button")].find((x) => /^(Submit for Approval|Issue|Send to Vendor|Approve)/i.test(x.textContent.trim()) && !x.disabled) : null);
  return { btn: pick || null };
}
function puPoHeadHtml(po) {
  const p = (DB.projects || []).find((x) => x.id === po.projectId),
    t = poTotal(po).total,
    paid = poPaid(po),
    billed = puPoBilled(po),
    rec = puReceivedValue(po),
    st = "function" == typeof poState ? poState(po) : { msg: "", sev: 0 },
    word = PU_PO_WORD[po.status] || po.status,
    tone = "cancelled" === po.status ? "bad" : st.sev >= 3 ? "bad" : st.sev >= 2 ? "warn" : "received" === po.status || "closed" === po.status ? "ok" : "info",
    one = (po.lines || []).length === 1,
    lines = (po.lines || []).filter((l) => l.item || l.desc || +l.qty || +l.price),
    fig = (k, v, s) => `<div class="pu-pof"><span class="pu-pok">${esc(k)}</span><b>${esc(v)}</b>${s ? `<span class="pu-pos" data-nocase>${esc(s)}</span>` : ""}</div>`,
    lineHtml = (l) => {
      const est = puLineLabel(po, l),
        amt = r2((+l.qty || 0) * (+l.price || 0)),
        lb = puPoLineBilled(po, l),
        recd = +l.received || 0,
        recTone = recd > (+l.qty || 0) + 1e-9 ? "bad" : recd >= (+l.qty || 0) && +l.qty ? "ok" : "";
      return `<li class="pu-pol"><b data-nocase>${esc(l.item || l.desc || "Line")}</b><span class="pu-pole ${est ? "" : "warn"}" data-nocase>${est ? `Estimate line: ${esc(est)}` : "No estimate line: link one below"}</span><span class="pu-polv" data-nocase><span class="${recTone}">Received ${esc(String(r2(recd)))} of ${esc(String(+l.qty || 0))} ${esc(l.unit || "")}</span>${null != lb ? ` · Billed ${money(lb)} of ${money(amt)}` : one ? ` · Billed ${money(billed)} of ${money(t)}` : ""}</span></li>`;
    };
  return `<section class="pu-poh card" id="pu-poh" data-pupoh="${esc(po.id)}" aria-label="The order">
    <div class="pu-poh-hd"><div class="pu-poh-tt"><span class="pu-pok">Purchase Order</span><h2 data-nocase>${esc(po.number || "Draft")}</h2><span class="pu-poh-who" data-nocase>${esc(po.vendor || "No vendor yet")}${p ? ` · ${esc(puJob(p))}` : ""}</span></div><span class="pill ${tone}">${esc(word)}</span></div>
    ${st.msg ? `<p class="pu-poh-msg" data-nocase>${esc(st.msg)}</p>` : ""}
    <div class="pu-pofs">${fig("Ordered", money(t), po.expected ? `Expected ${fmt(po.expected)}` : "")}${fig("Received", money(rec), `of ${money(r2((po.lines || []).reduce((a, l) => a + (+l.qty || 0) * (+l.price || 0), 0)))} before tax`)}${fig("Billed", money(billed), `of ${money(t)}`)}${fig("Paid", money(paid), paid > billed + 0.5 ? `${money(r2(paid - billed))} before a bill` : billed > paid + 0.5 ? `${money(r2(billed - paid))} still to pay` : "")}</div>
    <ul class="pu-pols">${lines.map(lineHtml).join("")}</ul>
    <div class="pu-poh-next" id="pu-ponext"></div>
  </section>`;
}
// one blue on the order: the step moves to the top (its own handler goes with it); every other blue on the page turns
// plain. A later pass (the page's own blue for Receive All, Bill What Arrived) may add one back: this runs after it.
function puPoBlue(po, doc) {
  const slot = doc.querySelector("#pu-ponext");
  if (!slot) return;
  let keep = slot.querySelector("button:not(#pu-potask)");
  if (!keep && !slot.querySelector(".pu-poh-why")) {
    const nx = puPoNext(po, doc);
    if (nx.over) {
      slot.innerHTML = `<p class="pu-poh-why bad" data-nocase>${esc(nx.say)}</p>`;
      if (nx.make) {
        keep = document.createElement("button");
        (keep.type = "button"), (keep.className = "btn"), (keep.id = "pu-ponext-b"), (keep.textContent = nx.make.label), (keep.onclick = nx.make.run), slot.appendChild(keep);
      }
    } else if (nx.btn) slot.appendChild((keep = nx.btn));
    else slot.innerHTML = `<p class="pu-poh-why" data-nocase>${"closed" === po.status || "cancelled" === po.status ? "Nothing more to do on this order." : "Nothing waits on you on this order."}</p>`;
  }
  // New Task on the order (lane T1, 11-05): the one task sheet, its title starting with the order and the vendor, on the
  // order's job, the order as its source. Plain: the order's next step stays the one blue.
  if (!slot.querySelector("#pu-potask") && "function" == typeof newTaskDialog && !puReadOnly()) {
    const t = document.createElement("button");
    (t.type = "button"), (t.className = "btn"), (t.id = "pu-potask"), (t.textContent = "New Task");
    t.onclick = () =>
      newTaskDialog({
        title: `${po.number || "Draft order"} (${po.vendor || "no vendor"}): `,
        projectId: po.projectId || "",
        notes: `${po.number || "Draft order"} · ${po.vendor || "no vendor"} · ${money(poTotal(po).total)}`,
        source: { kind: "po", id: po.id, label: `${po.number || "the draft order"} · ${po.vendor || ""}` },
      });
    slot.appendChild(t);
  }
  const sec = document.getElementById("v-po") || doc;
  sec.querySelectorAll(".btn.primary").forEach((x) => x !== keep && !x.closest("#mbm") && (x.classList.remove("primary"), (x.dataset.flowDemoted = "1")));
  keep && (keep.classList.add("primary"), delete keep.dataset.flowDemoted);
}
function puPoRecord(final) {
  const sec = document.getElementById("v-po");
  if (!sec) return;
  const po = "po" === view && poOpen ? (DB.pos || []).find((x) => x.id === poOpen) : null;
  // the order alone on its page: the firm's documents panel and the list's heading stay with the list
  sec.classList.toggle("pu-rec", !!po);
  const doc = document.getElementById("po-doc");
  if (!po || !doc || "none" === doc.style.display) return;
  // drawn once per draw of the order; a later pass of the same render only re-asserts the one blue
  if (!doc.querySelector(`#pu-poh[data-pupoh="${po.id}"]`)) {
    doc.querySelector("#pu-poh") && doc.querySelector("#pu-poh").remove();
    doc.insertAdjacentHTML("afterbegin", puPoHeadHtml(po));
    // the way back to Orders sits above the order (its own handler goes with it)
    const crumb = doc.querySelector(".crumb");
    crumb && doc.insertBefore(crumb, doc.firstChild);
  }
  final && puPoBlue(po, doc);
  // the order's paper and documents follow under their own heading
  const wrap = doc.querySelector(".docwrap");
  wrap && !doc.querySelector(".pu-podoc-h") && wrap.insertAdjacentHTML("beforebegin", `<h3 class="pu-podoc-h">The Order as Sent</h3>`);
}
{
  const base = renderPOs;
  renderPOs = function () {
    const r = base.apply(this, arguments);
    try {
      puPoRecord();
    } catch (e) {
      console.warn("purchase order page", e);
    }
    return r;
  };
}

// ---- Vendors: the facts a row and the record share ------------------------------------------------------------------------
function puVendorFacts(v) {
  const td = today(),
    open = (DB.pos || []).filter((po) => po.vendor === v.name && puLive(po)),
    openAmt = r2(open.reduce((a, po) => a + poTotal(po).total, 0)),
    rets = (() => {
      try {
        return retOpen().filter((r) => r.vendor === v.name);
      } catch (e) {
        return [];
      }
    })(),
    owed = r2(rets.reduce((a, r) => a + (+retExpected(r) || 0), 0)),
    days = v.insuranceExp ? dayDiff(td, v.insuranceExp) : null,
    coiSay = v.insuranceExp ? (days < 0 ? `Lapsed ${fmt(v.insuranceExp)}` : days <= 30 ? `Expires ${fmt(v.insuranceExp)}` : `To ${fmt(v.insuranceExp)}`) : "None on file",
    coiTone = v.insuranceExp ? (days < 0 ? "bad" : days <= 30 ? "warn" : "") : "",
    perf = (() => {
      try {
        const s = "function" == typeof selVendorStats ? selVendorStats()[v.name] : null;
        return s && s.onTimePct != null ? `${s.onTimePct}% on time` : "";
      } catch (e) {
        return "";
      }
    })(),
    paid = r2(vendorSpend(v)),
    // paid or billed past an order (the Orders page's Over the Order, the same function): said beside what is owed back
    over = "function" == typeof puOverOrder ? puOverOrder("").filter((x) => x.po.vendor === v.name) : [];
  return {
    open: open,
    openAmt: openAmt,
    openSay: open.length ? `${open.length} open order${1 === open.length ? "" : "s"}, ${money(openAmt)}` : "",
    rets: rets,
    owed: owed,
    coiSay: coiSay,
    coiTone: coiTone,
    papersSay: `Insurance ${coiSay.toLowerCase()}`,
    perf: perf,
    paid: paid,
    over: over,
    overAmt: r2(over.reduce((a, x) => a + x.over, 0)),
    tone: "bad" === coiTone && open.length ? "bad" : owed > 0.5 || over.length ? "warn" : "",
  };
}
// Price history per item bought from a vendor: the last price paid this vendor, the best price anyone got, and the trend
// (the last price against the item's median). One history: itemPriceHistory (src/app.js), which reads the order lines,
// the bills, the card and bank receipts and the quotes. The items are the ones on this vendor's orders, and the receipt
// price book's items bought at its stores.
const puVendorIs = (v, name) => {
  const a = String(v.name || "").toLowerCase(),
    b = String(name || "").toLowerCase();
  return !!a && (b === a || b.startsWith(a + " ") || b.startsWith(a + " \u2014"));
};
function puVendorPrices(v) {
  if ("function" != typeof itemPriceHistory) return [];
  const keys = new Map();
  (DB.pos || [])
    .filter((po) => puVendorIs(v, po.vendor) && !["draft", "cancelled"].includes(po.status))
    .forEach((po) => (po.lines || []).forEach((l) => (l.item || l.desc) && keys.set("function" == typeof pwKeyFor ? pwKeyFor(l.item || l.desc, l.unit) : l.item || l.desc, l.item || l.desc)));
  try {
    ("function" == typeof ciPriceBook ? ciPriceBook() : []).forEach((b) => (b.stores || []).some((x) => puVendorIs(v, x.store)) && keys.set(b.key, b.item));
  } catch (e) {}
  const out = [];
  keys.forEach((item, key) => {
    let H = null;
    try {
      H = itemPriceHistory(key, { vendor: v.name, vendorId: v.id }) || itemPriceHistory(item, { vendor: v.name, vendorId: v.id });
    } catch (e) {}
    if (!H || !(H.rows || []).length) return;
    // until the history filters by vendor itself, the vendor's own rows are picked here; best stays every vendor's
    const mine = H.rows.filter((r) => puVendorIs(v, r.vendor) && "quote" !== r.kind && +r.price > 0).sort((a, c) => String(a.date).localeCompare(String(c.date)));
    if (!mine.length) return;
    const last = mine[mine.length - 1],
      best = H.best && +H.best.price > 0 ? H.best : last,
      base = +H.median > 0 && H.rows.length > 1 ? +H.median : mine.length > 1 ? mine[0].price : 0,
      pct = base ? Math.round(((last.price - base) / base) * 100) : null;
    out.push({ item: H.label || item, unit: H.unit || last.unit || "", last: last, best: { price: +best.price, date: best.date, where: best.vendor || "" }, n: mine.length, trend: null == pct ? "One buy" : pct > 0 ? `Up ${pct}% on the usual` : pct < 0 ? `Down ${-pct}% on the usual` : "At the usual", up: pct > 0 });
  });
  return out;
}
const puPrice = (n) => ("function" == typeof pwU2 ? pwU2(n) : money(n));
function puVendorGlanceHtml(v) {
  const F = puVendorFacts(v),
    PR = puVendorPrices(v),
    w9 = v.w9 ? "On file" : "None on file",
    tile = (k, val, sub, tone) => `<div class="pu-vg-t ${tone || ""}"><span class="pu-pok">${esc(k)}</span><b>${esc(val)}</b>${sub ? `<span class="pu-pos" data-nocase>${esc(sub)}</span>` : ""}</div>`;
  return `<section class="card pu-vg" id="pu-vg" aria-label="At a glance">
    <div class="pu-vg-ts">${tile("Open Orders", F.open.length ? money(F.openAmt) : "None", F.open.length ? F.open.map((po) => po.number).join(", ") : "nothing on order")}${tile("Owed Back", money(F.owed), [F.rets.length ? `${F.rets.length} return${1 === F.rets.length ? "" : "s"}` : "no returns open", F.over.length ? `and ${money(F.overAmt)} paid over ${F.over.map((x) => x.po.number).join(", ")}` : ""].filter(Boolean).join(" "), F.owed > 0.5 || F.over.length ? "warn" : "")}${tile("Insurance", F.coiSay, F.coiTone === "bad" ? "new orders are blocked" : "", F.coiTone)}${tile("W-9", w9, v.w9 ? "" : "needed before a 1099", v.w9 ? "" : "warn")}</div>
    ${F.rets.length ? `<div class="pu-vg-sec"><h3>Returns</h3><ul class="pu-vg-l">${F.rets.map((r) => `<li><button type="button" class="pu-vg-row" data-puvret="${esc(r.id)}"><b data-nocase>${esc(r.name)}</b><span data-nocase>${money(retExpected(r))} owed back${r.rma ? ` · ${esc(r.rma)}` : ""}</span></button></li>`).join("")}</ul></div>` : ""}
    <div class="pu-vg-sec"><h3>Price History</h3>${
      PR.length
        ? `<table class="t pu-vg-pt"><thead><tr><th>Item</th><th class="num">Last</th><th class="num">Best</th><th>Trend</th></tr></thead><tbody>${PR.map((x) => `<tr><td data-nocase><b>${esc(x.item)}</b><div class="small muted">${x.n} buy${1 === x.n ? "" : "s"}</div></td><td class="num" data-nocase>${puPrice(x.last.price)}${x.unit ? `/${esc(x.unit)}` : ""}<div class="small muted">${x.last.date ? fmt(x.last.date) : ""}</div></td><td class="num ${x.best.price < x.last.price - 0.005 ? "warn" : ""}" data-nocase>${puPrice(x.best.price)}<div class="small muted">${esc(x.best.where || "")}</div></td><td class="${x.up ? "warn" : ""}">${esc(x.trend)}</td></tr>`).join("")}</tbody></table>`
        : `<p class="pu-empty" data-nocase>No prices from ${esc(v.name)} yet: the first order or receipt starts its history.</p>`
    }</div>
  </section>`;
}
function puVendorRecord() {
  if ("vendors" !== view || "undefined" == typeof vendOpen || !vendOpen) return;
  const v = (DB.vendors || []).find((x) => x.id === vendOpen),
    vr = document.querySelector("#v-vendors .vr");
  if (!v || !vr || vr.querySelector("#pu-vg")) return;
  const head = vr.querySelector(".vr-head");
  head ? head.insertAdjacentHTML("afterend", puVendorGlanceHtml(v)) : vr.insertAdjacentHTML("afterbegin", puVendorGlanceHtml(v));
  vr.querySelectorAll("[data-puvret]").forEach(
    (b) =>
      (b.onclick = () => {
        const r = retOpen().find((x) => x.id === b.dataset.puvret);
        r && ("function" == typeof retOne ? retOne(r) : retModal());
      }),
  );
}

// ---- read-only Purchasing for the controller and billing: they see every page, and buy nothing --------------------------
const puReadOnly = () => ["controller", "billing"].includes(role());
// Reading Purchasing does not make a job page the controller's or billing's: their Projects still lists no job (the
// menu's rule, mnJobLanding: "" when the role opens no job page), so the Buy Board is never a job's landing for them.
if ("function" == typeof mnJobLanding) {
  const base = mnJobLanding;
  mnJobLanding = function (r) {
    const v = base.apply(this, arguments);
    return "proc" === v && ["controller", "billing"].includes(r) ? "" : v;
  };
}
function puReadOnlyNote() {
  document.body.classList.toggle("pu-ro", puReadOnly());
  if (!puReadOnly()) return;
  // under the page's head (on the phone the head's title moves into the header, so the note sits below it)
  const h = document.querySelector(".view.on .pu-ph");
  h && !h.parentElement.querySelector(":scope > .pu-ro-note") && h.insertAdjacentHTML("afterend", `<p class="pu-ro-note" data-nocase>Read only: the coordinator orders and receives here.</p>`);
}
{
  const base = puDraw;
  puDraw = function () {
    const r = base.apply(this, arguments);
    try {
      puPoRecord(!0), puVendorRecord(), puReadOnlyNote();
    } catch (e) {
      console.warn("purchasing records", e);
    }
    return r;
  };
}

// The phone bar's Deliveries carries the page's Needs You, the number its menu entry shows (one question, one number)
if ("function" == typeof mRenderTabs) {
  const base = mRenderTabs;
  mRenderTabs = function () {
    const r = base.apply(this, arguments);
    try {
      document.querySelectorAll('#mtabs button[data-mv="recv"]').forEach((b) => {
        const n = "function" == typeof puCount && "function" == typeof puOffice && puOffice() ? puCount("recv") : 0;
        let i = b.querySelector("i.n");
        n ? (i || ((i = document.createElement("i")), (i.className = "n"), (i.dataset.ocbadge = "recv"), b.appendChild(i)), (i.textContent = n)) : i && i.remove();
      });
    } catch (e) {}
    return r;
  };
}
// the receipt's split on the phone: each cell carries its column's words (as drawn, Spanish for a Spanish field user),
// so the one-column layout labels every field
if ("function" == typeof spCaptureModal) {
  const base = spCaptureModal;
  spCaptureModal = function () {
    const r = base.apply(this, arguments);
    const label = () =>
      document.querySelectorAll("#mbm table.sp-lines").forEach((t) => {
        const H = [...t.querySelectorAll("thead th")].map((h) => h.textContent.trim());
        t.querySelectorAll("tbody tr").forEach((tr) => [...tr.children].forEach((td, i) => H[i] && (td.dataset.k = H[i])));
      });
    setTimeout(label, 0);
    try {
      const m = document.getElementById("mbm");
      m && !m.dataset.puSpl && ((m.dataset.puSpl = "1"), new MutationObserver(label).observe(m, { childList: !0, subtree: !0 }));
    } catch (e) {}
    return r;
  };
}
// the job's Order This Week card: a row with no material behind it (an estimate line, a site request) opens its Buy Board
// row, the same record its chip opens
document.addEventListener("click", (e) => {
  const a = e.target && e.target.closest ? e.target.closest("[data-matwk]") : null;
  if (!a) return;
  e.preventDefault();
  "undefined" != typeof bbSel && (bbSel = a.dataset.matwk);
  setView("proc");
});

// ---- the look ---------------------------------------------------------------------------------------------------------
(() => {
  const css = `
#v-po.pu-rec>:not(#po-doc){display:none !important}
.pu-poh{padding:16px 18px;margin:0 0 14px}
.pu-poh-hd{display:flex;align-items:flex-start;gap:12px}
.pu-poh-tt{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.pu-poh-tt h2{margin:0;font-size:22px}
.pu-poh-who{font-size:15px;color:var(--ink-2)}
.pu-pok{font-size:12.5px;color:var(--ink-3)}
.pu-poh-msg{margin:8px 0 0;font-size:14px;color:var(--ink-2)}
.pu-pofs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:14px 0 4px}
.pu-pof{display:flex;flex-direction:column;gap:2px;background:var(--paper-2,#f7f8fa);border-radius:10px;padding:10px 12px;min-width:0}
.pu-pof b{font-size:19px}
.pu-pos{font-size:12.5px;color:var(--ink-3)}
.pu-pols{list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column}
.pu-pol{display:flex;flex-direction:column;gap:2px;padding:10px 0;border-top:1px solid var(--rule-2)}
.pu-pol b{font-size:14.5px}
.pu-pole,.pu-polv{font-size:13px;color:var(--ink-2)}
.pu-pole.warn{color:var(--warn);font-weight:600}
.pu-polv .bad{color:var(--bad);font-weight:600} .pu-polv .ok{color:var(--ok,#1f7a4d)}
.pu-poh-next{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-top:12px;padding-top:12px;border-top:1px solid var(--rule-2)}
.pu-poh-next .btn{min-height:44px}
.pu-poh-why{margin:0;font-size:14px;color:var(--ink-2);flex:1 1 280px}
.pu-poh-why.bad{color:var(--bad)}
.pu-podoc-h{margin:6px 0 8px;font-size:15px}
.pu-vg{padding:14px 16px;margin:0 0 14px}
.pu-vg-ts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.pu-vg-t{display:flex;flex-direction:column;gap:2px;background:var(--paper-2,#f7f8fa);border-radius:10px;padding:10px 12px;min-width:0}
.pu-vg-t b{font-size:18px} .pu-vg-t.bad b{color:var(--bad)} .pu-vg-t.warn b{color:var(--warn)}
.pu-vg-sec{margin-top:14px} .pu-vg-sec h3{margin:0 0 6px;font-size:15px}
.pu-vg-l{list-style:none;margin:0;padding:0}
.pu-vg-row{display:flex;flex-direction:column;align-items:flex-start;gap:2px;width:100%;min-height:44px;border:0;border-top:1px solid var(--rule-2);background:none;padding:8px 0;font:inherit;color:var(--ink);text-align:left;cursor:pointer}
.pu-vg-row span{font-size:13px;color:var(--ink-3)}
table.pu-vg-pt{width:100%} table.pu-vg-pt td.warn{color:var(--warn)}
.pu-ro-note{margin:4px 0 0;font-size:13px;color:var(--ink-3)}
body.pu-ro :is(#v-proc,#v-rfq,#v-recv,#v-po) :is(.pu-plus,.bb-pick,.pu-bar,[data-purecv]){display:none !important}
body.pu-ro #buy-board .bb-panel .btn,body.pu-ro #v-recv #recv-body :is(button,input,select),body.pu-ro #v-recv [data-pufull="recv"]{display:none !important}
.pu-ro-note{margin:-6px 0 12px}
table.pu-vt td.warn{color:var(--warn);font-weight:600}
table.pu-vt tbody tr:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.pu-pojob{margin:0 0 10px}
@media (max-width:760px){
  .pu-pofs,.pu-vg-ts{grid-template-columns:repeat(2,minmax(0,1fr))}
  /* 8px between the New menu's items, as between any two targets */
  .pu-menu{gap:8px}
  .pu-poh{padding:14px}
  .pu-poh-next .btn{flex:1 1 100%}
  table.pu-vg-pt thead{display:none}
  table.pu-vg-pt,table.pu-vg-pt tbody,table.pu-vg-pt tr,table.pu-vg-pt td{display:block;width:auto}
  table.pu-vg-pt tr{padding:8px 0;border-top:1px solid var(--rule-2)}
  table.pu-vg-pt td{border:0;padding:1px 0;text-align:left}
}
`;
  const st = document.createElement("style");
  (st.id = "puorders-css"), (st.textContent = css), document.head.appendChild(st);
})();
