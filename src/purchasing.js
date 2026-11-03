/* =====================================================================================================================
   Purchasing: the menu's six pages (Alan, 11-03, "do the same thing for every menu and sub menu page"; the mock-up and
   spec in docs/mockups/purchasing/, its chief-of-staff review and must-fix list; docs/mockups/QUESTIONS.md).

   What was wrong. Purchasing was 9 pages and 19 tab screens: the Buy Board's To Buy and Arriving tabs and five chips, the
   FF&E tools' own board with six status tabs, Quotes' four tabs, Stock's five, Orders' and Vendors' tiles; PO-2026-047
   sat on four pages and the Buy Board and Orders shared nine records. Its number (17) counted rows that wait on other
   people. Money leaked where nobody looked: tape bought with 18 rolls on the shelf, needs "ordered" with no order
   behind them, $53,150+ paid to vendors with no W-9, and an open commitment read from payments, not bills.

   The structure. Six pages, no tab rows: Buy Board, Orders, Quotes, Deliveries, Vendors and Stock (Stock is the
   coordinator's and the driver's; every other role sees Alan's five, in his order). Each opens on:
     Needs You                 the rows whose next tap is yours, with a count equal to its rows (the menu reads it)
     Waiting on Someone Else   each row names who; no number
     the rest                  one tap down on the same page (Later, the orders, the vendors, the register)
   Job, vendor, trade and document are filters, never tabs. Inside a job (the job's Purchasing tab, src/jobpage.js) the
   same pages show that job only. Every row is its record: it opens the need, the order, the vendor or the item.
   A row's actor is a role (coord, pm, controller, billing, designer) or someone outside (a vendor, a sub, the client):
   Needs You for a role is the rows whose actor is that role, so one record counts once per person. The owner's pages
   carry no count (he sees escalations on Today).

   Design gate (BACKLOG §1.16). No new store, list or queue: each page reads the records that exist (buyList, DB.pos,
   DB.bills, the returns and claims of the FF&E tools, rfqInit, DB.vendors, DB.inventory, the route plan) through the
   functions the old pages read. The old pages' tools stay one tap down at each page's foot until their records move
   (P4, P5). A claim from receiving is the order's delivery issue (po.issues), the record Report a Problem writes.
   ===================================================================================================================== */

// ---- the one stock check every buying door runs (BACKLOG §9 item 4) --------------------------------------------------
// A need is often two things ("Blue tape + 4 mil plastic", "GWB boards (~25) & cement board"): each part is checked on
// its own, and a likely match is said, never silently bought around ("may be it" is a question for the person).
function puParts(name) {
  return String(name || "")
    .replace(/^\d+(\.\d+)?\s*\w*\s+(?=[A-Za-z])/, "")
    .replace(/\(.*?\)/g, " ")
    .split(/\s*(?:\+|&|,|\band\b)\s*/i)
    .map((s) => s.trim())
    .filter((s) => s.length > 2);
}
let puStockMemo = { k: "", m: new Map() };
function puStockFor(name) {
  if ("function" != typeof stockCheck) return [];
  const k = String((typeof SPD !== "undefined" && SPD && SPD.ver) || "") + "|" + ((DB.inventory || []).map((i) => i.qty).join(","));
  puStockMemo.k !== k && (puStockMemo = { k: k, m: new Map() });
  if (puStockMemo.m.has(name)) return puStockMemo.m.get(name);
  const out = [];
  puParts(name).forEach((part) => {
    try {
      const sc = stockCheck({ item: part, qty: 1, unit: "" });
      (sc.candidates || [])
        .filter((c) => c.available > 0 && !out.some((o) => o.id === c.id))
        .forEach((c) => out.push({ id: c.id, part: part, name: c.name, qty: c.available, unit: c.unit, where: c.where, sure: "high" === c.level }));
    } catch (e) {}
  });
  return puStockMemo.m.set(name, out), out;
}
const puUnits = (n, u) => `${n} ${u || ""}${1 === +n || /s$|^ea$|^ls$|^sf$|^lf$/.test(u || "") || !u ? "" : /(x|ch|sh)$/.test(u) ? "es" : "s"}`.trim(),
  puReorder = (i) => +(i.reorderAt != null ? i.reorderAt : i.reorder) || 0;
function puStockSay(S0) {
  if (!S0 || !S0.length) return "";
  const where = [...new Set(S0.map((s) => s.where))].join(" and ");
  return `At the ${where.toLowerCase() === "truck" ? "truck" : where.toLowerCase()}: ${S0.map((s) => `${puUnits(s.qty, s.unit)} of ${s.name}`).join(", ")}. Count before you buy.`;
}

// ---- who acts on a row ----------------------------------------------------------------------------------------------
const PU_ROLE_WORD = { coord: "the coordinator", pm: "the PM", controller: "the controller", billing: "billing", designer: "the designer", owner: "the owner", driver: "the driver" };
function puMe() {
  const r = role();
  return "design_mgr" === r ? "designer" : r;
}
// the person's word for whoever a row waits on: a role by its word, else the name (a vendor, a sub, the client)
function puWho(actor, name) {
  return name || PU_ROLE_WORD[actor] || actor || "someone";
}
function puClientWord(p) {
  const c = p && (DB.clients || []).find((x) => x.id === p.clientId);
  if (!c) return "the client";
  const last = String(c.name || "").split(/\s+/).pop();
  return /&| and /.test(c.name || "") && last ? `the ${last}s` : c.name;
}
const puJob = (p) => (p && p.project ? String(p.project.name).replace(/ —.*$/, "") : "");
const puInJob = () => ("function" == typeof jpOn && jpOn() && S ? S.id : "");

// ---- the Buy Board's rows: where each need stands and whose tap it is ---------------------------------------------
// One reader (buyList) and one place each need's bucket is decided:
//   gone    ordered, with an order behind it: it lives on Deliveries until it is here (decision 3)
//   route   a field request on today's store run: counted once, in the route approval on Deliveries
//   mine / others   due (late, to acknowledge, or to order within the working week): the actor's next tap
//   later   not due yet; it keeps its reason and its stock
function puSubmittalOf(r) {
  const ref = "ffe" === r.kind && r.it ? { kind: "sel", id: r.it.id } : "material" === r.kind && r.m ? { kind: "mat", id: r.m.id } : null;
  if (!ref || !r.p) return null;
  return (r.p.submittals || []).find((s) => ["revise", "review", "submitted"].includes(s.status) && (s.items || []).some((x) => x.kind === ref.kind && x.id === ref.id)) || null;
}
function puDecWho(r) {
  const o = String((r.dec && (r.dec.owner || r.dec.who)) || "");
  if (/client/i.test(o)) return { actor: "client", who: puClientWord(r.p) };
  if (/architect|designer/i.test(o)) return { actor: "designer", who: "the architect" };
  return { actor: "pm", who: "the PM" };
}
function puLineWord(r) {
  const ref = r.lineKey ? findLine(r.lineKey) : null;
  if (ref && ref.doc) return `${ref.doc.number || ""}${ref.line && ref.line.num ? ` line ${ref.line.num}` : ""}${"sub" === r.kind ? " · subcontract" : ""}${r.budget ? ` · ${money(r.budget)}` : ""}`.trim();
  if ("ffe" === r.kind) return `FF&E, ${r.room || "selection"}${r.it && r.it.line ? "" : " · No estimate line"}`;
  if ("request" === r.kind) return `Request from ${r.askedBy || "the site"} · No estimate line`;
  return "No estimate line: link one";
}
let puRouteMemo = { k: -1, ids: new Set() };
function puOnRoute() {
  const k = (typeof render !== "undefined" && render.__tick) || 0;
  if (puRouteMemo.k === k && k) return puRouteMemo.ids;
  const ids = new Set();
  try {
    const W = "function" == typeof bbRouteWaiting ? bbRouteWaiting() : null;
    W && W.N.plan.stops.forEach((s) => (s.items || []).forEach((a) => ids.add(String((a.b || a).key || "").split(":")[0])));
    // once approved, the day's run holds them
    const run = "function" == typeof ciRunFor ? ciRunFor(today()) : null;
    run && "approved" === run.status && ((run.plan || {}).stops || []).forEach((s) => (s.items || []).forEach((a) => ids.add(String(a.key || "").split(":")[0])));
  } catch (e) {}
  return (puRouteMemo = { k: k, ids: ids }), ids;
}
function puNeed(r) {
  if (!r || r.received || "done" === r.tab) return null;
  const td = today(),
    stock = r.ordered ? [] : puStockFor(r.name),
    base = { r: r, id: r.id, name: r.name, job: puJob(r.p), line: puLineWord(r), stock: stock, pick: !r.ordered };
  if (r.ordered && r.po) return Object.assign(base, { b: "gone" });
  // due: the board's own sections (bbFinish): late, to acknowledge, or to order within five working days
  const due = r.late || ["ack", "week", "late"].includes(r.section);
  let o;
  if (r.ordered)
    o = { actor: "coord", why: `Marked ordered with no order behind it.${r.eta ? ` Promised ${fmt(r.eta)}${r.needBy ? `, needed ${fmt(r.needBy)}` : ""}.` : ""} Find the order, the store receipt or the card line.`, act: "Find the Order", k: "find", tone: r.late ? "bad" : "warn" };
  else if ("request" === r.kind && r.q && "new" === r.q.status) {
    const h = "function" == typeof reqAgeH ? Math.round(reqAgeH(r.q)) : 0;
    o = { actor: "coord", why: `Not acknowledged${h ? ` in ${h} hours` : ""}. ${r.askedBy || "The crew"} needs it on site ${r.needBy ? fmt(r.needBy) : "soon"}.`, act: "Acknowledge and Link", k: "ack", tone: "warn" };
  } else if ("request" === r.kind && r.q && puOnRoute().has(r.q.id)) o = { b: "route", actor: "coord", why: "On today's store run.", act: "Open the Route", k: "route" };
  else if (r.dec) {
    const w = puDecWho(r),
      late = r.dec.due && r.dec.due < td ? `, ${dayDiff(r.dec.due, td)} days late` : "";
    o = { actor: w.actor, who: w.who, why: `the decision: ${r.dec.name || "open"}${late}.`, act: "Open the Decision", k: "dec" };
  } else if (puSubmittalOf(r)) {
    const s = puSubmittalOf(r);
    o = "revise" === s.status ? { actor: "sub", who: s.sub || "the sub", why: `submittal ${s.number} came back Revise and Resubmit; the order waits for it.`, act: "Open the Submittal", k: "subm" } : { actor: "designer", who: "the architect", why: `submittal ${s.number} is in review; the order waits for it.`, act: "Open the Submittal", k: "subm" };
  } else if (r.matUnknown) o = { actor: "pm", who: "the PM", why: "the material portion of the line is not set; the line includes labour.", act: "Set the Material Portion", k: "split" };
  else if ((r.rfqs || []).length) {
    const q = r.rfqs[0];
    o = { actor: "vendor", who: (q.vendors || []).length ? `${(q.vendors || []).length} vendors` : "the vendors", why: `${q.number}: quotes due ${q.dueDate ? fmt(q.dueDate) : "soon"}.`, act: "Open the Request", k: "rfq" };
  } else if ("sub" === r.kind) o = { actor: "coord", why: "No sub contracted. Over $2,500: three bids, or a reason.", act: "Ask for Bids", k: "quote", tone: r.late ? "bad" : "warn" };
  else if (!r.price) o = { actor: "coord", why: "No price yet.", act: "Ask for Quotes", k: "quote", tone: r.late ? "bad" : "" };
  else o = { actor: "coord", why: `Order by ${fmt(r.orderBy)}.`, act: "Order", k: "order", tone: r.late ? "bad" : "" };
  const st = puStockSay(stock),
    b = o.b || (!due ? "later" : o.actor === puMe() ? "mine" : "others");
  return Object.assign(base, o, { b: b, why: [o.why, st].filter(Boolean).join(" "), when: r.ordered && r.eta ? `Promised ${fmt(r.eta)}${r.needBy ? `, needed on site ${fmt(r.needBy)}` : ""}` : r.orderBy ? `Order by ${fmt(r.orderBy)}${r.orderBy < td ? ", passed" : ""}` : r.needBy ? `On site ${fmt(r.needBy)}` : "No date yet" });
}
function puNeeds(pid) {
  let R = [];
  try {
    R = buyList("").map(puNeed).filter(Boolean);
  } catch (e) {
    console.warn("purchasing needs", e);
  }
  return pid ? R.filter((x) => x.r.p && x.r.p.id === pid) : R;
}
// the job filter of the Buy Board: inside a job, that job (bbProj, the job's Purchasing tab)
const puBuyScope = () => ("undefined" != typeof bbProj && bbProj) || "";
function puBuyRows(scope) {
  let R = puNeeds(scope);
  "undefined" != typeof bbVendor && bbVendor && (R = R.filter((x) => (x.r.vendor || "") === bbVendor));
  "undefined" != typeof bbTrade && bbTrade && (R = R.filter((x) => bbTradeOf(x.r) === bbTrade));
  return R;
}

// ---- the other pages' rows ------------------------------------------------------------------------------------------
const puVendorOf = (name) => (DB.vendors || []).find((v) => v.name === name) || null;
const puLive = (po) => ["issued", "partial", "pending"].includes(po.status);
function puPoBilled(po) {
  return r2(
    (DB.bills || [])
      .filter((b) => b.poId === po.id && !["void", "rejected"].includes(b.status))
      .reduce((a, b) => a + ("function" == typeof billTotal ? billTotal(b) : (b.lines || []).reduce((s, l) => s + (+l.amount || 0), 0)), 0),
  );
}
// Committed, Not Yet Billed: each live order's total less what its vendor has billed (P5: the bill, through the one
// "paid", is the cost; a payment with no bill is a prepayment, never billed work)
function puCommitted(pid) {
  return (DB.pos || [])
    .filter((po) => puLive(po) && (!pid || po.projectId === pid))
    .map((po) => ({ po: po, left: r2(Math.max(0, poTotal(po).total - puPoBilled(po))) }))
    .filter((x) => x.left > 0.5);
}
function puOverOrder(pid) {
  return (DB.pos || [])
    .filter((po) => "cancelled" !== po.status && (!pid || po.projectId === pid))
    .map((po) => {
      const tot = poTotal(po).total,
        out = Math.max(poPaid(po), puPoBilled(po));
      return { po: po, over: r2(out - tot), out: out, tot: tot };
    })
    .filter((x) => x.over > Math.max(1, x.tot * ((DB.company.matchTol || 2) / 100)));
}
function puReceivedValue(po) {
  return r2((po.lines || []).reduce((a, l) => a + Math.min(+l.received || 0, +l.qty || 0) * (+l.price || 0), 0));
}
function puOrderRows(pid) {
  const R = [],
    put = (o) => R.push(Object.assign({ actor: "coord", b: "mine" }, o));
  puOverOrder(pid).forEach((x) =>
    put({ id: "over:" + x.po.id, name: `${x.po.vendor}: ${money(x.over)} over ${x.po.number}`, job: puJob(DB.projects.find((p) => p.id === x.po.projectId)), line: `Paid or billed ${money(x.out)} against an order of ${money(x.tot)}`, why: "Ask for the credit, or approve the difference with a reason. Money paid over the order is money that cannot go to raises, bonuses, more staff or charity.", act: "Open the Order", run: () => flowGo.po(x.po)(), tone: "bad", money: x.over, tile: "over", po: x.po }),
  );
  (DB.pos || [])
    .filter((po) => puLive(po) && (!pid || po.projectId === pid))
    .forEach((po) => {
      const paid = poPaid(po),
        rec = puReceivedValue(po),
        dep = po.termsPreset && /deposit|% on order/i.test(String(po.termsPreset)) ? 1 : 0;
      paid > rec + 1 &&
        !dep &&
        !(po.sc || po.retainagePct) &&
        put({ id: "prepay:" + po.id, name: `${po.vendor}: ${money(paid)} paid before delivery`, job: puJob(DB.projects.find((p) => p.id === po.projectId)), line: `${po.number} · ${money(rec)} received · promised ${po.expected ? fmt(po.expected) : "no date"}`, why: "It comes off the next bill; hold the bill until it does.", act: "Open the Order", run: () => flowGo.po(po)(), tone: "warn" });
      (po.issues || [])
        .filter((i) => i.claim && "open" === (i.status || "open"))
        .forEach((i, k) =>
          put({ id: `claim:${po.id}:${k}`, name: `${po.vendor}: ${i.type} on ${po.number}`, job: puJob(DB.projects.find((p) => p.id === po.projectId)), line: `${i.qty || ""} ${(po.lines.find((l) => l.id === i.lineId) || {}).item || ""}`.trim(), why: "Claim the replacement or the credit before the bill is paid.", act: "Open the Order", run: () => flowGo.po(po)(), tone: "bad" }),
        );
    });
  try {
    selClaims()
      .filter((c) => "undefined" != typeof CLAIM_OPEN && CLAIM_OPEN.includes(c.status) && (!pid || c.projectId === pid))
      .forEach((c) => {
        const it = selItem(c.itemId),
          age = dayDiff(c.raisedAt, today());
        put({ id: "selclaim:" + c.id, name: `${it ? it.name : "Item"}: ${c.kind} on arrival`, job: puJob(DB.projects.find((p) => p.id === c.projectId)), line: `Claim with ${c.vendor || "the vendor"}${age > 0 ? `, ${age} days open` : ""}`, why: "It does not go to the site until the claim closes.", act: "Open the Item", run: () => ("function" == typeof selOpenItem ? selOpenItem(c.itemId) : setView("sel")), tone: "bad" });
      });
  } catch (e) {}
  try {
    retOpen()
      .filter((r) => !pid || r.projectId === pid)
      .forEach((r) => {
        const risk = retRisk(r),
          exp = retExpected(r),
          credit = ["shipped", "received"].includes(r.status);
        put({ id: "ret:" + r.id, name: credit ? `${r.vendor}: ${money(exp)} credit to confirm` : `${r.name}: ${money(retValue(r))} to send back`, job: puJob(DB.projects.find((p) => p.id === r.projectId)), line: `${r.vendor}${r.rma ? ` · ${r.rma}` : ""} · ${risk.label || "no return-by date"}`, why: credit ? "Shipped back; the credit is not on a statement yet." : (retDaysLeft(r) ?? 0) < 0 ? "The return window closed. Ask anyway, or write it off with a reason." : "Ship it back before the window closes.", act: credit ? "Find the Credit" : "Open the Return", run: () => ("function" == typeof retOne ? retOne(r) : retModal()), tone: 3 === risk.lvl ? "bad" : "warn", money: exp, tile: "owed" });
      });
  } catch (e) {}
  try {
    "function" == typeof rmOrphans &&
      rmOrphans()
        .filter((t) => !pid || t.projectId === pid)
        .forEach((t) => put({ id: "orphan:" + t.id, name: `${money(t.amt)} credit from ${t.vendor || "a vendor"} with nothing behind it`, job: "", line: `${t.desc || "statement line"} · ${fmt(t.date)}`, why: "Usually a credit we were owed and forgot. Attach it to its return, or say it is not ours.", act: "Attach to a Return", run: () => retModal(), tone: "warn" }));
  } catch (e) {}
  try {
    if ("function" == typeof pwCasesAll) {
      const C = pwCasesAll().filter((c) => "pwStoreCheaper" === c.det && (!pid || c.projectId === pid));
      const sum = r2(C.reduce((a, c) => a + (+c.amount || 0), 0));
      C.length &&
        put({ id: "pw:store", name: `${money(sum)} paid above the best price`, job: "", line: `${C.length} store buy${1 === C.length ? "" : "s"}: ${C.map((c) => c.what || c.vendor).slice(0, 3).join(", ")}`, why: "Another store had it for less. Every dollar paid above the best price is a dollar not spent on raises, bonuses or the client.", act: "See the Buys", run: () => ((window.rfqTab = "pricewatch"), setView("rfq")), tone: "warn" });
    }
  } catch (e) {}
  return R;
}
// Deliveries: what is on its way, promised later than it is needed, on today's route, at the office, going back
function puDelivRows(pid) {
  const R = [],
    td = today();
  const ord = buyList("").filter((r) => r.ordered && r.po && !r.received && (!pid || r.p.id === pid));
  ord
    .filter((r) => r.late)
    .forEach((r) =>
      R.push({ b: "mine", actor: "coord", id: "late:" + r.id, name: `${r.po.number} · ${r.po.vendor}: ${r.name}`, job: puJob(r.p), line: r.lateWhy, why: `${r.task ? `${r.task.name} starts ${fmt(r.task.start)}. ` : ""}Expedite, another vendor, or ask the PM to move the task.`, act: "Expedite", run: () => bbExpedite(r, "expedite"), tone: "bad", need: r }),
    );
  try {
    const W = !pid && "function" == typeof bbRouteWaiting ? bbRouteWaiting() : null;
    if (W) {
      const P = W.N.plan,
        first = W.driver.split(" ")[0],
        buys = P.stops.flatMap((s) => (s.items || []).map((a) => a.b || a)).filter((b) => b.what),
        st = buys.flatMap((b) => puStockFor(b.what).map((s) => Object.assign({ buy: b }, s)));
      R.push({ b: "mine", actor: "coord", id: "route:" + W.N.date, name: `Approve ${first}'s route`, job: "", line: `${P.stops.length} stop${1 === P.stops.length ? "" : "s"}${(P.stores || []).length ? `, buying at ${P.stores.join(" and ")}` : ""} · before the van leaves at ${W.leave}`, why: st.length ? `${st.map((s) => `${puUnits(s.qty, s.unit)} of ${s.name} at the ${String(s.where).toLowerCase()}`).join("; ")}: pick ${st.length > 1 ? "them" : "it"} there and buy only the rest.` : "Nothing on it is in stock.", act: "Approve the Route", run: () => puApproveRoute(W, st), tone: "warn", stock: st });
    }
  } catch (e) {
    console.warn("route", e);
  }
  return R;
}
// Vendors: whose papers or payments need the person
function puNoW9Paid() {
  return (DB.vendors || []).filter((v) => !v.w9).map((v) => ({ v: v, paid: r2(vendorSpend(v)) })).filter((x) => x.paid > 0.5);
}
function puVendorOnSite(v) {
  const n = v.name;
  if ((DB.pos || []).some((po) => po.vendor === n && puLive(po))) return "an order open with them, delivered to the site";
  if (((DB.sel || {}).items || []).some((it) => it.vendor === n && /appliance/i.test(it.category || "") && !["inst", "installed", "done"].includes(it.stage))) return "they deliver and set inside the house";
  return "";
}
function puVendorRows() {
  const R = [],
    me = puMe(),
    td = today();
  (DB.vendors || []).forEach((v) => {
    const st = vendorState(v),
      lapsed = v.insuranceExp && v.insuranceExp < td,
      open = (DB.pos || []).filter((po) => po.vendor === v.name && puLive(po));
    if (lapsed && (open.length || (DB.bills || []).some((b) => b.vendor === v.name && !["paid", "void"].includes(b.status)) || /window|plumb|electr|tile|mill/i.test(v.trade || "")))
      return R.push({ b: "mine", actor: "coord", id: "v:coi:" + v.id, name: `${v.name}: blocked`, job: v.trade || "", line: `Insurance lapsed ${fmt(v.insuranceExp)}`, why: "No new order and no one on site until the certificate lands.", act: "Chase the Certificate", run: () => puVendorOpen(v), tone: "bad" });
    const unpaid = (DB.bills || []).filter((b) => b.vendor === v.name && !["paid", "verified", "void", "rejected"].includes(b.status) && !b.paidAt);
    if (!v.w9 && unpaid.length) {
      const b = unpaid[0],
        out = "function" == typeof billBankCovers && billBankCovers(b);
      return R.push({ b: "mine", actor: "coord", id: "v:w9:" + v.id, name: `${v.name}: W-9 before ${b.number}`, job: v.trade || "", line: `${b.number} · ${money(billTotal(b))}${out ? " · the bank shows it already left" : ""}`, why: "Ask for the W-9 today: without it the year-end 1099 is wrong and the payment may need backup withholding.", act: "Ask for the W-9", run: () => puVendorOpen(v), tone: "warn" });
    }
    const site = !v.insuranceExp && puVendorOnSite(v);
    site && R.push({ b: "mine", actor: "coord", id: "v:site:" + v.id, name: `${v.name}: no certificate on file`, job: v.trade || "", line: site, why: "Anyone coming on site or inside needs a current certificate of insurance.", act: "Chase the Certificate", run: () => puVendorOpen(v), tone: "warn" });
  });
  // the controller's: money already out to vendors with no W-9 (backup withholding, the year-end 1099)
  const W9 = puNoW9Paid();
  W9.length &&
    R.push({
      b: "controller" === me ? "mine" : "others",
      actor: "controller",
      who: "the controller",
      id: "v:w9paid",
      name: `${money(W9.reduce((a, x) => a + x.paid, 0))} paid with no W-9 on file`,
      job: "",
      line: W9.map((x) => `${x.v.name} ${money(x.paid)}`).join(" · "),
      why: "Collect each W-9 before the next payment and before year end. Money that goes out wrong comes back out of raises, bonuses, staff and charity.",
      act: "See the Vendors",
      run: () => puFilterVendors("now9"),
      tone: "bad",
    });
  return R.map((x) => Object.assign(x, { b: "controller" === x.actor ? (me === "controller" ? "mine" : "others") : x.actor === me ? "mine" : "others", who: x.who || PU_ROLE_WORD[x.actor] }));
}
function puStockRows() {
  const R = [];
  (DB.inventory || [])
    .filter((i) => "tool" !== i.type && puReorder(i) > 0 && invAvailable(i) <= puReorder(i))
    .forEach((i) => R.push({ b: "coord" === puMe() ? "mine" : "others", actor: "coord", who: "the coordinator", id: "inv:" + i.id, name: `${i.name}: at its reorder point`, job: "", line: `${puUnits(invAvailable(i), i.unit)} at the ${String(locName(i.loc)).toLowerCase()} · reorder at ${puUnits(puReorder(i), i.unit)}`, why: "Restock it from the warehouse order, or let the next store run pick it up.", act: "Restock", run: () => puPlus("inv", "restock"), tone: "warn" }));
  return R;
}
function puQuoteRows() {
  const R = [];
  let Q = [];
  try {
    Q = rfqInit().filter((q) => !["awarded", "closed", "cancelled"].includes(q.status));
  } catch (e) {}
  const td = today();
  Q.forEach((q) => {
    const got = (q.quotes || []).length,
      asked = (q.vendors || []).length || (q.sent || []).length,
      due = q.dueDate && q.dueDate < td,
      mine = !asked || got >= asked || (due && got < asked) || (got > 0 && got >= 3);
    R.push({ b: mine ? "mine" : "others", actor: mine ? "coord" : "vendor", who: mine ? "" : `${asked - got} of ${asked} vendors`, id: "rfq:" + q.id, name: `${q.number}: ${q.title || (q.lines || []).map((l) => l.item).slice(0, 2).join(", ") || "request for quote"}`, job: puJob(DB.projects.find((p) => p.id === q.projectId)), line: `${got} of ${asked || 0} quotes in${q.dueDate ? ` · due ${fmt(q.dueDate)}` : ""}`, why: !asked ? "Not sent yet." : got >= asked || got >= 3 ? "Every quote is in: level them and award." : due ? "Past its due date: chase the vendors who have not quoted." : "Out to the vendors.", act: !asked ? "Send It" : got >= asked || got >= 3 ? "Level and Award" : due ? "Chase" : "Open", run: () => rfqOpenFor(q.id) });
  });
  return R;
}
// one count per page: the rows whose next tap is the person's
const PU_ROWS = {
  // the menu's Buy Board is every job's; the page's own heading counts the rows its filters show
  proc: () => puNeeds("").filter((x) => "mine" === x.b),
  po: () => puOrderRows(puInJob()).filter((x) => x.actor === puMe()),
  recv: () => puDelivRows(puInJob()).filter((x) => x.actor === puMe()),
  vendors: () => puVendorRows().filter((x) => "mine" === x.b),
  inv: () => puStockRows().filter((x) => "mine" === x.b),
  rfq: () => puQuoteRows().filter((x) => "mine" === x.b && "coord" === puMe()),
};
function puCount(v) {
  try {
    return PU_ROWS[v] ? PU_ROWS[v]().length : 0;
  } catch (e) {
    return 0;
  }
}

// ---- drawing ----------------------------------------------------------------------------------------------------------
let puOpenRows = {}, // id -> row (this draw's), so a tap finds its record
  puLaterOpen = !1,
  puShowAll = {},
  puFilter = { po: "open", vendors: "all", inv: "all" },
  puFull = {};
const PU_IC = {
  plus: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
  down: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>',
  up: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 15l6-6 6 6"/></svg>',
};
const PU_LEAD = {
  proc: "Every job's needs: estimate and change-order lines, approved selections and site requests, by the date each must be ordered.",
  po: "Every order and store run from issue to paid, with the claims, returns and credits that hang on them.",
  rfq: "What things cost: requests out to vendors and subs, and the prices we already know.",
  recv: "Everything on its way to a site, the office or back to a vendor, and the receiving.",
  vendors: "One record per supplier and sub: papers, terms, and everything bought from them.",
  inv: "What the firm owns and where it is: the warehouse, the truck or a site.",
};
const PU_NAME = { proc: "Buy Board", po: "Orders", rfq: "Quotes", recv: "Deliveries", vendors: "Vendors", inv: "Stock" };
function puRowHtml(x, o) {
  o = o || {};
  puOpenRows[x.id] = x;
  const pick = o.pick && x.pick ? bbPickBox(x.r) : "",
    who = o.others ? `<span class="pu-who">Waiting on ${esc(x.who || "someone")}</span>` : "",
    sub = [x.job, x.line].filter(Boolean).join(" · ");
  return `<div class="pu-row ${x.tone || ""}${pick ? " pu-pickable" : ""}${o.sel && o.sel === x.id ? " sel" : ""}" data-purow="${esc(x.id)}">${pick}<button type="button" class="pu-rb" data-puopen="${esc(x.id)}"><b data-nocase>${esc(x.name)}</b>${sub ? `<span class="pu-sub" data-nocase>${esc(sub)}</span>` : ""}${who}<span class="pu-why" data-nocase>${esc(x.why || "")}</span>${x.when ? `<span class="pu-when ${x.r && x.r.late ? "bad" : ""}">${esc(x.when)}</span>` : ""}</button>${x.act && !o.others && !o.quiet ? `<button type="button" class="btn sm pu-act" data-puact="${esc(x.id)}">${esc(x.act)}</button>` : ""}</div>`;
}
function puSecHtml(key, title, rows, o) {
  o = o || {};
  if (!rows.length && !o.empty) return "";
  const n = o.count ? `<span class="n" data-ocbadge="${esc(o.count)}">${rows.length}</span>` : "";
  return `<section class="pu-sec" data-pusec="${key}"><div class="pu-sh"><h3>${esc(title)}</h3>${n}${o.note ? `<span class="pu-note" data-nocase>${esc(o.note)}</span>` : ""}</div>${rows.length ? `<div class="pu-rows">${rows.map((x) => puRowHtml(x, o)).join("")}</div>` : `<p class="pu-empty" data-nocase>${esc(o.empty)}</p>`}${o.foot || ""}</section>`;
}
function puPlusItems(v) {
  const click = (id) => () => {
    const b = document.getElementById(id);
    b ? b.click() : toast("That is not available here");
  };
  return {
    proc: [
      ["Buy From an Estimate or Invoice", "Pick the job, the document, then its lines", () => puBuyFromDoc()],
      ["Restock the Warehouse", "From Stock items at or under their reorder point", () => puPlus("inv", "restock")],
      ["Blank Need", "Only when no line covers it; the line is asked for before approval", () => ("function" == typeof openEditor ? openEditor("mat", null) : toast("Open a job to add a need"))],
    ],
    po: [
      ["New Purchase Order From Lines", "Pick the job's estimate or change-order lines", () => puBuyFromDoc()],
      ["Blank Purchase Order", "Only when no line covers it", click("btn-newpo")],
    ],
    rfq: [["New Request for Quote", "Starts from the lines you are buying for", () => ("function" == typeof rfqNew ? rfqNew() : puBuyFromDoc("quote"))]],
    recv: [["Log Something That Arrived", "With no order behind it", () => ("function" == typeof openEditor ? openEditor("mat", null) : null)]],
    vendors: [["New Vendor", "Filled from a mail or a card photo", click("btn-newvendor")]],
    inv: [
      ["New Stock Item", "A consumable or a tool", click("btn-newinv")],
      ["Count a Shelf", "Set what is really there", click("btn-invmove")],
      ["Move a Tool", "A pickup and a drop-off on the driver's list", click("btn-invmove")],
    ],
  }[v] || [];
}
let puPlusOpen = "";
function puHeadHtml(v, extra) {
  // inside a job the page is the job's Purchasing tab: its name, the job's words, and the job's one + (src/jobpage.js)
  const job = "function" == typeof jpOn && jpOn(),
    items = job ? [] : puPlusItems(v),
    name = job && "proc" === v ? "Purchasing" : PU_NAME[v],
    lead = job ? "This job's needs, orders and deliveries: what to buy and what is coming." : PU_LEAD[v];
  return `<div class="ph pu-ph bb-ph0"><div class="pu-tt"><h2>${esc(name)}</h2><p class="lead" data-nocase>${esc(lead)}</p></div><div class="acts">${extra || ""}${items.length ? `<div class="pu-plus"><button type="button" class="btn pu-plusb" data-puplus="${v}" aria-expanded="${puPlusOpen === v}" aria-label="New">${PU_IC.plus}<span>New</span></button>${puPlusOpen === v ? `<div class="pu-menu" role="menu">${items.map((it, i) => `<button type="button" role="menuitem" class="pu-mi" data-pumi="${i}"><b>${esc(it[0])}</b><span>${esc(it[1])}</span></button>`).join("")}</div>` : ""}</div>` : ""}</div></div>`;
}
// the old page's tools, one tap down, until their records move here (P4, P5)
function puFullHtml(v, label) {
  return `<div class="pu-foot"><button type="button" class="pu-link" data-pufull="${v}" aria-expanded="${!!puFull[v]}">${esc(label)}${puFull[v] ? PU_IC.up : PU_IC.down}</button></div>`;
}
function puHost(v) {
  const sec = document.getElementById("v-" + v);
  if (!sec) return null;
  let host = sec.querySelector(":scope > .pu");
  host || ((host = document.createElement("div")), (host.className = "pu"), sec.insertBefore(host, sec.firstChild));
  sec.classList.add("pu-host");
  sec.classList.toggle("pu-full", !!puFull[v]);
  puHideOld(sec, !puFull[v]);
  return host;
}
// the old page's parts are hidden inline (a phone rule with !important on an id would show them otherwise)
function puHideOld(sec, hide) {
  [...sec.children].forEach((c) => {
    if (c.classList.contains("pu")) return;
    hide
      ? (null == c.dataset.puhid && (c.dataset.puhid = c.style.display || ""), c.style.setProperty("display", "none", "important"))
      : null != c.dataset.puhid && (c.style.removeProperty("display"), c.dataset.puhid && (c.style.display = c.dataset.puhid), delete c.dataset.puhid);
  });
}
function puDrop(v) {
  const sec = document.getElementById("v-" + v);
  if (!sec) return;
  puHideOld(sec, !1);
  sec.classList.remove("pu-host", "pu-full");
  const h = sec.querySelector(":scope > .pu");
  h && h.remove();
}
const puPhone = () => ("function" == typeof mOn ? mOn() : innerWidth <= 760);

// The Buy Board (#proc-body): Needs You with picks, On Today's Route, Waiting on Someone Else, Later folded
function puBuyRender() {
  const root = document.getElementById("proc-body");
  if (!root) return;
  puOpenRows = {};
  const phone = puPhone(),
    scope = puBuyScope(),
    R = puBuyRows(scope),
    byDate = (a, b) => ("ack" === b.k) - ("ack" === a.k) || String(a.r.orderBy || "9").localeCompare(String(b.r.orderBy || "9")),
    mine = R.filter((x) => "mine" === x.b).sort(byDate),
    route = R.filter((x) => "route" === x.b),
    others = R.filter((x) => "others" === x.b),
    later = R.filter((x) => "later" === x.b).sort((a, b) => String(a.r.orderBy || "9").localeCompare(String(b.r.orderBy || "9")));
  [...bbPick].forEach((id) => mine.concat(later, others).some((x) => x.id === id) || bbPick.delete(id));
  const picked = [...bbPick].map((id) => R.find((x) => x.id === id)).filter(Boolean),
    sel = (!phone && ((bbSel && R.find((x) => x.id === bbSel)) || mine[0] || others[0])) || null;
  sel && (bbSel = sel.id);
  // the filters: job (not inside a job), vendor, trade
  const all = puNeeds(""),
    projs = [...new Map(all.map((x) => [x.r.p.id, puJob(x.r.p)])).entries()],
    vendors = [...new Set(all.map((x) => x.r.vendor).filter(Boolean))].sort(),
    trades = [...new Set(all.map((x) => bbTradeOf(x.r)))].sort(),
    selOpt = (id, label, cur, L) => `<select id="${id}" class="pu-sel" aria-label="${label}"><option value="">${label}: All</option>${L.map(([v, n]) => `<option value="${esc(v)}" ${cur === v ? "selected" : ""}>${esc(n)}</option>`).join("")}</select>`,
    inJob = "function" == typeof jpOn && jpOn(),
    filters = `<div class="pu-filters">${inJob ? "" : selOpt("bb-proj", "Job", bbProj, projs)}${selOpt("bb-vendor", "Vendor", bbVendor, vendors.map((v) => [v, v]))}${selOpt("bb-trade", "Trade", bbTrade, trades.map((v) => [v, v]))}</div>`;
  // the pick bar: count and total; the Standard's three quotes over $2,500 (and any line with no price) make Ask for
  // Quotes the one blue, and the other reads Order, With a Reason
  let bar = "";
  if (picked.length) {
    const priced = picked.filter((x) => +x.r.price > 0),
      unpriced = picked.filter((x) => !(+x.r.price > 0)),
      total = r2(priced.reduce((a, x) => a + +x.r.price, 0)),
      quotes = unpriced.length > 0 || total > 2500,
      jobs = [...new Set(picked.map((x) => x.job))];
    bar = `<div class="bb-bar pu-bar"><span class="pu-bt"><b>${picked.length} line${1 === picked.length ? "" : "s"} picked</b><span data-nocase> · ${money(total)}${unpriced.length ? ` priced, ${unpriced.length} with no price yet` : ""} · ${esc(jobs.join(", "))}</span></span><span class="pu-bb"><button type="button" class="btn sm ghost" id="pu-clear">Clear</button><button type="button" class="btn ${quotes ? "" : "primary"}" id="bb-order">${quotes ? "Order, With a Reason" : `Order ${picked.length} Line${1 === picked.length ? "" : "s"}`}</button><button type="button" class="btn ${quotes ? "primary" : ""}" id="bb-quote">Ask for Quotes</button></span></div>`;
  }
  const laterFirst = later[0] && later[0].r.orderBy,
    laterLast = later.length && later[later.length - 1].r.orderBy,
    laterBtn = later.length ? `<button type="button" class="pu-link pu-laterb" data-pulater="1" aria-expanded="${puLaterOpen}">${puLaterOpen ? "Hide the Later Needs" : `Show the Later Needs${laterFirst ? `, Order by ${fmt(laterFirst)}${laterLast && laterLast !== laterFirst ? ` to ${fmt(laterLast)}` : ""}` : ""}`}${puLaterOpen ? PU_IC.up : PU_IC.down}</button>` : "",
    list =
      puSecHtml("mine", "Needs You", mine, { count: "proc", pick: 1, sel: bbSel, empty: "Nothing waits on you. Every due need is ordered, asked for or with someone else." }) +
      puSecHtml("route", "On Today's Route", route, { quiet: 1, note: "Counted once, in the route approval on Deliveries" }) +
      puSecHtml("others", "Waiting on Someone Else", others, { others: 1, sel: bbSel }) +
      (later.length ? `<section class="pu-sec" data-pusec="laterfold"><div class="pu-sh"><h3>Later</h3></div>${laterBtn}</section>${puLaterOpen ? puSecHtml("later", "Later Needs", later, { pick: 1, sel: bbSel }) : ""}` : ""),
    panel = !phone ? `<aside class="bb-panel" aria-label="${esc(sel ? sel.name : "The need")}">${sel ? bbPanelHtml(sel.r, picked.length) : bbPanelHtml(null)}</aside>` : "",
    foot = `<div class="pu-foot"><button type="button" class="pu-link" id="bb-more">FF&amp;E Buy Runs, Receiving and Returns</button></div>`;
  root.innerHTML = `<div class="pu bb ${phone ? "bb-phone" : "bb-desk"} ${picked.length ? "bb-picking" : ""}" data-pupage="proc" id="buy-board" data-os-keep>${puHeadHtml("proc")}${filters}<div class="bb-main"><div class="bb-list pu-list" data-nocase>${list}${foot}</div>${panel}</div>${bar}</div>`;
  bbWire(root);
  const q = (s) => root.querySelector(s);
  q("#pu-clear") && (q("#pu-clear").onclick = () => (bbPick.clear(), render()));
}

// The pages drawn over the old ones (#v-po, #v-rfq, #v-recv, #v-vendors, #v-inv)
function puTile(id, k, v, s, rows) {
  return `<button type="button" class="pu-tile ${puShowAll.tile === id ? "on" : ""}" data-putile="${id}" aria-pressed="${puShowAll.tile === id}"><span class="pu-tk">${esc(k)}</span><b>${esc(v)}</b><span class="pu-ts" data-nocase>${esc(s)}</span></button>`;
}
function puPageHtml(v, parts) {
  return `<div class="pu-page" data-pupage="${v}">${puHeadHtml(v, parts.acts)}${parts.tiles ? `<div class="pu-tiles">${parts.tiles}</div>` : ""}${parts.filters || ""}${parts.body}</div>`;
}
function puOrders() {
  const pid = puInJob(),
    rows = puOrderRows(pid),
    me = puMe(),
    mine = rows.filter((x) => x.actor === me),
    others = rows.filter((x) => x.actor !== me).map((x) => Object.assign({}, x, { who: PU_ROLE_WORD[x.actor] })),
    owed = rows.filter((x) => "owed" === x.tile),
    over = rows.filter((x) => "over" === x.tile),
    cnb = puCommitted(pid),
    owedSum = r2(owed.reduce((a, x) => a + (x.money || 0), 0)),
    overSum = r2(over.reduce((a, x) => a + (x.money || 0), 0)),
    cnbSum = r2(cnb.reduce((a, x) => a + x.left, 0)),
    t = puShowAll.tile || "",
    f = puFilter.po,
    pos = (DB.pos || []).filter((po) => (!pid || po.projectId === pid) && ("all" === f ? "cancelled" !== po.status : "draft" === f ? "draft" === po.status : "received" === f ? "received" === po.status : puLive(po))),
    poRow = (po) => {
      const st = "function" == typeof poState ? poState(po) : { msg: po.status };
      return { id: "po:" + po.id, name: `${po.number} · ${po.vendor || "No vendor"}`, job: puJob(DB.projects.find((p) => p.id === po.projectId)), line: `Total ${money(poTotal(po).total)} · Paid ${money(poPaid(po))} · Billed ${money(puPoBilled(po))}${po.expected ? ` · Expected ${fmt(po.expected)}` : ""}`, why: st.msg || po.status, run: () => flowGo.po(po)() };
    },
    tileRows = "owed" === t ? owed : "over" === t ? over : "cnb" === t ? cnb.map((x) => Object.assign(poRow(x.po), { id: "cnb:" + x.po.id, why: `${money(x.left)} committed, not yet billed` })) : null,
    tiles =
      puTile("mine", "Needs You", String(mine.length), "rows whose next tap is yours") +
      puTile("owed", "Owed Back", money(owedSum), `${owed.length} return${1 === owed.length ? "" : "s"} and credits`) +
      puTile("over", "Over the Order", money(overSum), over.length ? over.map((x) => x.po.number).join(", ") : "nothing paid past an order") +
      puTile("cnb", "Committed, Not Yet Billed", money(cnbSum), `${cnb.length} open order${1 === cnb.length ? "" : "s"}, by their bills`),
    chips = [["draft", "Draft"], ["open", "Open"], ["received", "Received"], ["all", "All"]],
    filters = `<div class="pu-filters"><span class="pu-fl">Orders:</span>${chips.map(([k, l]) => `<button type="button" class="pu-chip ${f === k ? "on" : ""}" data-pupof="${k}" aria-pressed="${f === k}">${l}</button>`).join("")}</div>`,
    body =
      (tileRows ? puSecHtml("tile", { owed: "Owed Back", over: "Over the Order", cnb: "Committed, Not Yet Billed" }[t], tileRows, { empty: "Nothing here." }) : "") +
      puSecHtml("mine", "Needs You", mine, { count: "po", empty: "Nothing waits on you." }) +
      puSecHtml("others", "Waiting on Someone Else", others, { others: 1 }) +
      filters +
      puSecHtml("orders", "Orders", pos.map(poRow), { quiet: 1, empty: "draft" === f ? "Nothing sits in draft." : "No orders in this filter." }) +
      `<p class="pu-note2" data-nocase>Store runs join as orders with P5; until then their receipts sit with the route and Price Watch. Missing invoice copies are chased by the assistant.</p>` +
      puFullHtml("po", "Matching, Promises and Client Funds");
  return puPageHtml("po", { tiles: tiles, body: body });
}
function puDeliveries() {
  const pid = puInJob(),
    rows = puDelivRows(pid),
    me = puMe(),
    mine = rows.filter((x) => x.actor === me),
    others = rows.filter((x) => x.actor !== me).map((x) => Object.assign({}, x, { who: PU_ROLE_WORD[x.actor] })),
    td = today(),
    arriving = (DB.pos || [])
      .filter((po) => ["issued", "partial"].includes(po.status) && (!pid || po.projectId === pid))
      .map((po) => ({ id: "arr:" + po.id, po: po, name: `${po.number} · ${po.vendor}`, job: puJob(DB.projects.find((p) => p.id === po.projectId)), line: `${(po.lines || []).map((l) => `${l.item} ${+l.received || 0} of ${l.qty} ${l.unit || ""}`.trim()).slice(0, 2).join("; ")}`, why: po.expected ? `Promised ${fmt(po.expected)}` : "No date promised", act: "Receive", run: () => puReceive(po) })),
    office = ((DB.sel || {}).items || []).filter((it) => ["office", "ship"].includes(it.stage) && (!pid || it.projectId === pid)).map((it) => ({ id: "sel:" + it.id, name: it.name, job: puJob(DB.projects.find((p) => p.id === it.projectId)), line: `${it.vendor || ""} · ${"ship" === it.stage ? "in transit" : "at the office"}`, why: "ship" === it.stage ? ((it.dates || {}).eta ? `Arriving ${fmt(it.dates.eta)}` : "No date yet") : `On site ${fmt(selNeedOnSite(it))}: deliver it with the route`, run: () => ("function" == typeof selOpenItem ? selOpenItem(it.id) : setView("sel")) })),
    back = (() => {
      try {
        return retOpen().filter((r) => ["raise", "authorised", "toship"].includes(r.status) && (!pid || r.projectId === pid)).map((r) => ({ id: "back:" + r.id, name: r.name, job: r.vendor, line: retRisk(r).label || "", why: r.rma ? `${r.rma}: ship it back` : "No return authorisation yet", run: () => ("function" == typeof retOne ? retOne(r) : retModal()) }));
      } catch (e) {
        return [];
      }
    })(),
    arrBody = arriving.map((x) => {
      puOpenRows[x.id] = x;
      return `<div class="pu-row" data-purow="${esc(x.id)}"><button type="button" class="pu-rb" data-puopen="${esc(x.id)}"><b data-nocase>${esc(x.name)}</b><span class="pu-sub" data-nocase>${esc([x.job, x.line].filter(Boolean).join(" · "))}</span><span class="pu-why" data-nocase>${esc(x.why)}</span></button><button type="button" class="btn sm pu-act" data-purecv="${esc(x.po.id)}">Receive</button></div>`;
    }),
    body =
      puSecHtml("mine", "Needs You", mine, { count: "recv", empty: "Nothing waits on you: every delivery is on time." }) +
      puSecHtml("others", "Waiting on Someone Else", others, { others: 1 }) +
      (arriving.length ? `<section class="pu-sec" data-pusec="arriving"><div class="pu-sh"><h3>Arriving</h3></div><div class="pu-rows">${arrBody.join("")}</div></section>` : "") +
      puSecHtml("office", "In Transit and At the Office", office, { quiet: 1 }) +
      puSecHtml("back", "Going Back", back, { quiet: 1 }) +
      puFullHtml("recv", "Receive Line by Line");
  return puPageHtml("recv", { body: body });
}
let puVendFilter = "all";
function puFilterVendors(k) {
  (puVendFilter = k), setView("vendors");
}
function puVendors() {
  const rows = puVendorRows(),
    mine = rows.filter((x) => "mine" === x.b),
    others = rows.filter((x) => "others" === x.b),
    V = (DB.vendors || []).filter((v) => ("now9" === puVendFilter ? !v.w9 : "suggested" === puVendFilter ? !1 : !0)),
    noW9 = (DB.vendors || []).filter((v) => !v.w9).length,
    sugg = (() => {
      try {
        return (DB.rfqProspects || []).slice(0, 12);
      } catch (e) {
        return [];
      }
    })(),
    perf = (v) => {
      try {
        const s = "function" == typeof selVendorStats ? selVendorStats()[v.name] : null;
        return s && s.onTimePct != null ? `${s.onTimePct}% on time` : "";
      } catch (e) {
        return "";
      }
    },
    phone = puPhone(),
    list = phone
      ? `<div class="pu-rows">${V.map((v) => {
          const x = { id: "vend:" + v.id, name: v.name, job: v.trade || "", line: `Insurance ${v.insuranceExp ? fmt(v.insuranceExp) : "none on file"} · W-9 ${v.w9 ? "on file" : "none"} · Paid ${money(vendorSpend(v))}`, why: perf(v), run: () => puVendorOpen(v) };
          puOpenRows[x.id] = x;
          return `<div class="pu-row" data-purow="${esc(x.id)}"><button type="button" class="pu-rb" data-puopen="${esc(x.id)}"><b data-nocase>${esc(v.name)}</b><span class="pu-sub" data-nocase>${esc(x.job)}</span><span class="pu-why" data-nocase>Insurance ${esc(v.insuranceExp ? fmt(v.insuranceExp) : "none on file")} · <span data-puw9="${v.w9 ? "on" : "none"}">W-9 ${v.w9 ? "on file" : "none"}</span> · Paid ${money(vendorSpend(v))}${perf(v) ? ` · ${esc(perf(v))}` : ""}</span></button></div>`;
        }).join("")}</div>`
      : `<table class="t pu-vt"><thead><tr><th>Vendor</th><th>Trade</th><th>Insurance</th><th>W-9</th><th class="num">Paid</th><th>Open Orders</th><th>On Time</th></tr></thead><tbody>${V.map((v) => {
          const open = (DB.pos || []).filter((po) => po.vendor === v.name && puLive(po));
          return `<tr data-puvend="${esc(v.id)}"><td><b data-nocase>${esc(v.name)}</b></td><td data-nocase>${esc(v.trade || "")}</td><td class="${v.insuranceExp && v.insuranceExp < today() ? "bad" : ""}">${v.insuranceExp ? fmt(v.insuranceExp) : "none"}</td><td data-puw9="${v.w9 ? "on" : "none"}">${v.w9 ? "On file" : "None"}</td><td class="num">${money(vendorSpend(v))}</td><td data-nocase>${open.length ? open.map((po) => po.number).join(", ") : ""}</td><td data-nocase>${esc(perf(v))}</td></tr>`;
        }).join("")}</tbody></table>`,
    filters = `<div class="pu-filters"><span class="pu-fl">Show:</span>${[["all", "All"], ["now9", "No W-9"], ["suggested", "Suggested"]].map(([k, l]) => `<button type="button" class="pu-chip ${puVendFilter === k ? "on" : ""}" data-puvf="${k}" aria-pressed="${puVendFilter === k}">${l}</button>`).join("")}</div>`,
    body =
      puSecHtml("mine", "Needs You", mine, { count: "vendors", empty: "Nothing waits on you: every vendor's papers are in order." }) +
      puSecHtml("others", "Waiting on Someone Else", others, { others: 1 }) +
      filters +
      ("suggested" === puVendFilter
        ? puSecHtml("suggested", "Suggested", sugg.map((s, i) => ({ id: "sugg:" + i, name: s.name || s.vendor || "Prospect", job: s.trade || s.category || "", line: s.why || s.city || "", why: "", run: () => ((window.rfqTab = "prospects"), setView("rfq")) })), { quiet: 1, empty: "No suggested vendors yet: they come from requests for quote and sourcing research." })
        : `<section class="pu-sec" data-pusec="list"><div class="pu-sh"><h3>All Vendors</h3><span class="pu-note" data-nocase>${noW9} of ${(DB.vendors || []).length} have no W-9</span></div>${list}</section>`) +
      puFullHtml("vendors", "Bank Changes, Balances and Performance");
  return puPageHtml("vendors", { body: body });
}
function puStock() {
  const rows = puStockRows(),
    mine = rows.filter((x) => "mine" === x.b),
    others = rows.filter((x) => "others" === x.b),
    f = puFilter.inv,
    I = (DB.inventory || []).filter((i) => ("tool" === f ? "tool" === i.type : "mat" === f ? "tool" !== i.type : "job" === f ? /^p/.test(String(i.loc || "")) || !/^(wh|truck|shop)$/i.test(String(i.loc || "")) : !0)),
    // what today's needs could use from the shelf: shown here with no count (the pick is decided on the need's row)
    want = [];
  puNeeds("").filter((x) => !x.r.ordered && "gone" !== x.b && (x.stock || []).length).forEach((x) => x.stock.forEach((s) => want.push({ id: `want:${x.id}:${s.id}`, name: `${puUnits(s.qty, s.unit)} of ${s.name}`, job: x.job, line: `at the ${String(s.where).toLowerCase()}`, why: `Wanted by ${x.name}`, run: () => ((bbSel = x.id), setView("proc")) })));
  const chips = [["all", "All"], ["mat", "Materials"], ["tool", "Tools"], ["job", "At a Job"]],
    filters = `<div class="pu-filters"><span class="pu-fl">Show:</span>${chips.map(([k, l]) => `<button type="button" class="pu-chip ${f === k ? "on" : ""}" data-puinvf="${k}" aria-pressed="${f === k}">${l}</button>`).join("")}</div>`,
    list = I.map((i) => ({ id: "item:" + i.id, name: i.name, job: "", line: `${puUnits(invAvailable(i), i.unit)} · ${locName(i.loc)}`, why: "tool" === i.type ? "Tool" : puReorder(i) ? `Reorder at ${puUnits(puReorder(i), i.unit)}` : "", run: () => ("function" == typeof openEditor ? openEditor("inv", i.id) : null) })),
    body =
      puSecHtml("mine", "Needs You", mine, { count: "inv", empty: "Nothing waits on you: nothing is at its reorder point." }) +
      puSecHtml("others", "Waiting on Someone Else", others, { others: 1 }) +
      puSecHtml("want", "Wanted by a Need", want, { quiet: 1, note: "Picked on the need's Buy Board row" }) +
      filters +
      puSecHtml("list", "Everything We Own", list, { quiet: 1, empty: "Nothing in this filter." }) +
      puFullHtml("inv", "Stock Log and Moves");
  return puPageHtml("inv", { body: body });
}
function puQuotes() {
  const rows = puQuoteRows(),
    me = puMe(),
    mine = "coord" === me ? rows.filter((x) => "mine" === x.b) : [],
    others = rows.filter((x) => "others" === x.b || ("coord" !== me && "mine" === x.b)).map((x) => Object.assign({}, x, { who: x.who || "the coordinator" })),
    subs = puNeeds("").filter((x) => "sub" === x.r.kind && !(x.r.rfqs || []).length && +x.r.price > 2500),
    emptyNote = subs.length ? `Nothing waits on you. ${subs.length} subcontract scope${1 === subs.length ? "" : "s"} over $2,500 ${1 === subs.length ? "has" : "have"} no bids yet: ${subs.map((x) => x.name).join(" and ")}, on the Buy Board.` : "Nothing waits on you.",
    book = (() => {
      try {
        return "function" == typeof ciPriceBook ? ciPriceBook() : [];
      } catch (e) {
        return [];
      }
    })(),
    bookRows = book.slice(0, puShowAll.book ? 200 : 8).map((x) => ({ id: "pb:" + x.key, name: x.item, job: "", line: x.best ? `Best ${"function" == typeof pwU2 ? pwU2(x.best.price) : money(x.best.price)} at ${x.best.store}, ${fmt(x.best.date)}` : "none in 90 days", why: `per ${x.unit}${x.stores.length > 1 ? ` · ${x.stores.length} stores` : ""}`, run: () => ((window.rfqTab = "pricewatch"), puFull.rfq = !0, render()) })),
    body =
      puSecHtml("mine", "Needs You", mine, { count: "rfq", empty: emptyNote, foot: subs.length && !mine.length ? `<div class="pu-foot"><button type="button" class="pu-link" data-pugo="proc">Open the Buy Board</button></div>` : "" }) +
      puSecHtml("others", "Waiting on Someone Else", others, { others: 1 }) +
      puSecHtml("book", "Prices We Know", bookRows, { quiet: 1, empty: "No receipt has been read yet.", foot: book.length > 8 ? `<div class="pu-foot"><button type="button" class="pu-link" data-pubook="1">${puShowAll.book ? "Show Fewer" : `Show All ${book.length}`}</button></div>` : "" }) +
      puFullHtml("rfq", "Requests, Price Watch and Savings");
  return puPageHtml("rfq", { body: body });
}
const PU_PAGES = { po: puOrders, recv: puDeliveries, vendors: puVendors, inv: puStock, rfq: puQuotes };
// a record open on its page (an order, a vendor, a request for quote) is drawn by its own page, not the list
function puRecordOpen(v) {
  try {
    if ("po" === v) return !!poOpen;
    if ("vendors" === v) return !!vendOpen;
    if ("rfq" === v) return !!window.rfqOpen;
  } catch (e) {}
  return !1;
}
// the field roles keep their own pages (the crew's Deliveries is the site's receiving)
const puOffice = () => !["foreman", "crew", "client"].includes(role());
function puDraw() {
  const v = view;
  Object.keys(PU_PAGES).forEach((x) => x !== v && puDrop(x));
  if (!PU_PAGES[v] || !puOffice() || puRecordOpen(v)) return void (PU_PAGES[v] && puDrop(v));
  const host = puHost(v);
  if (!host) return;
  puOpenRows = {};
  try {
    host.innerHTML = PU_PAGES[v]();
  } catch (e) {
    console.warn("purchasing page", v, e), puDrop(v);
  }
}

// ---- what the buttons do --------------------------------------------------------------------------------------------
function puVendorOpen(v) {
  "function" == typeof vendorPage ? vendorPage(v.id) : openVendor(v.id);
}
function puPlus(v, what) {
  if ("restock" === what) {
    const low = (DB.inventory || []).filter((i) => "tool" !== i.type && puReorder(i) > 0 && invAvailable(i) <= puReorder(i));
    if (!low.length) return toast("Nothing is at its reorder point");
    return mbModal(
      "Restock the Warehouse",
      `<p class="small muted" style="margin:0 0 8px">At or under the reorder point. The next store run buys them, or order them from a supplier.</p>${low.map((i) => `<div class="pu-kv"><span data-nocase>${esc(i.name)}</span><b>${puUnits(invAvailable(i), i.unit)} at the ${esc(String(locName(i.loc)).toLowerCase())}</b></div>`).join("")}`,
      { submit: null },
    );
  }
}
// Buy from a document's lines: the job, the document, then its lines (the order sheet the Buy Board's picks use)
function puBuyFromDoc(kind) {
  const P = (DB.projects || []).filter((p) => "function" != typeof rfqLineSources || rfqLineSources(p.id).length);
  const pid = (S && P.some((p) => p.id === S.id) && S.id) || (P[0] && P[0].id);
  if (!pid) return toast("No job has an approved estimate or change order to buy from yet");
  const L = rfqLineSources(pid);
  const m = mbModal(
    "Buy From an Estimate or Invoice",
    `<label class="f"><span>Job</span><select id="pu-bj">${P.map((p) => `<option value="${esc(p.id)}" ${p.id === pid ? "selected" : ""}>${esc(puJob(p))}</option>`).join("")}</select></label><div class="pu-lines" id="pu-bl">${L.map((s) => `<label class="pu-line"><input type="checkbox" data-publ="${esc(s.key)}"><span><b data-nocase>${esc(s.item)}</b><span class="small muted" data-nocase>${esc(s.docNo || "Selection")}${null != s.budget ? ` · ${money(s.budget)}` : ""}</span></span></label>`).join("")}</div>`,
    {
      submit: "quote" === kind ? "Ask for Quotes" : "Order the Lines",
      onSubmit: () => {
        const keys = [...m.querySelectorAll("[data-publ]:checked")].map((x) => x.dataset.publ),
          j = m.querySelector("#pu-bj").value;
        if (!keys.length) return toast("Pick at least one line"), !1;
        setTimeout(() => ("quote" === kind ? rfqFromLines(j, keys, {}) : ctPOPicker(j, "*", keys)), 0);
      },
    },
  );
  const sel = m.querySelector("#pu-bj");
  sel &&
    (sel.onchange = () => {
      m.querySelector("#pu-bl").innerHTML = rfqLineSources(sel.value).map((s) => `<label class="pu-line"><input type="checkbox" data-publ="${esc(s.key)}"><span><b data-nocase>${esc(s.item)}</b><span class="small muted" data-nocase>${esc(s.docNo || "Selection")}${null != s.budget ? ` · ${money(s.budget)}` : ""}</span></span></label>`).join("");
    });
  return m;
}
// Receive (the phone's sheet, the desktop's too): the count starts empty; Good, Short, Damaged or Wrong; a photo of the
// slip; Short, Damaged or Wrong opens a claim on the order (its delivery issue), with Open
function puReceive(po) {
  if (!po) return;
  let cond = "good";
  const L = (po.lines || []).filter((l) => (+l.received || 0) < (+l.qty || 0));
  const m = mbModal(
    `Receive <span data-nocase>${esc(po.number)}</span>`,
    `<p class="small muted" style="margin:0 0 10px" data-nocase>${esc(po.vendor)} · ${esc(puJob(DB.projects.find((p) => p.id === po.projectId)))}. Count what is really here.</p>${L.map((l) => `<label class="pu-rq"><span data-nocase><b>${esc(l.item)}</b><span class="small muted">${r2((+l.qty || 0) - (+l.received || 0))} ${esc(l.unit || "")} expected</span></span><input type="number" inputmode="decimal" min="0" data-purq="${esc(l.id)}" value="" placeholder="Count" aria-label="Count of ${esc(l.item)}"></label>`).join("")}<div class="pu-conds" role="radiogroup" aria-label="Condition">${[["good", "Good"], ["short", "Short"], ["damaged", "Damaged"], ["wrong", "Wrong"]].map(([k, l]) => `<button type="button" class="pu-chip ${"good" === k ? "on" : ""}" data-pucond="${k}" aria-pressed="${"good" === k}">${l}</button>`).join("")}</div><label class="f"><span>Photo of the Slip</span><input type="file" accept="image/*" capture="environment" data-puslip="1"></label><label class="f"><span>What Is Wrong</span><input data-punote="1" placeholder="Only if something is short, damaged or wrong"></label>`,
    {
      submit: "Receive",
      onSubmit: () => {
        const got = L.map((l) => ({ l: l, q: m.querySelector(`[data-purq="${l.id}"]`).value })).filter((x) => "" !== x.q);
        if (!got.length) return toast("Count at least one line, even if it is 0"), !1;
        got.forEach((x) => +x.q > 0 && receive(po, x.l, +x.q));
        const slip = m.querySelector("[data-puslip]");
        slip && slip.files && slip.files[0] && (po.slips = (po.slips || []).concat([{ at: appNowIso(), name: slip.files[0].name }]));
        let claim = null;
        if ("good" !== cond) {
          const x = got[0],
            short = Math.max(0, r2((+x.l.qty || 0) - (+x.l.received || 0)));
          claim = { t: nowStamp(), at: appNowIso(), by: ((currentUser() || {}).name) || role(), type: cond, lineId: x.l.id, qty: "short" === cond ? short : +x.q || 0, note: (m.querySelector("[data-punote]") || {}).value || "", claim: !0, status: "open" };
          (po.issues = po.issues || []).push(claim);
          x.l.issue = cond;
          po.flag = `${cond}: ${x.l.item} ${claim.qty}`;
          try {
            audit("po", po.id, "delivery-claim", "", cond, `${claim.qty} ${x.l.item}`);
          } catch (e) {}
        }
        save(), render();
        claim
          ? toast(`${po.number}: ${got.length} line${1 === got.length ? "" : "s"} received; a ${cond} claim is open with ${po.vendor}. Every dollar not credited comes out of raises, bonuses and the client's extras.`, { label: "Open", run: () => flowGo.po(po)() }, 9e3)
          : toast(`${po.number}: ${got.length} line${1 === got.length ? "" : "s"} received`, { label: "Open", run: () => flowGo.po(po)() });
      },
    },
  );
  m.querySelectorAll("[data-pucond]").forEach(
    (b) =>
      (b.onclick = () => {
        cond = b.dataset.pucond;
        m.querySelectorAll("[data-pucond]").forEach((x) => (x.classList.toggle("on", x === b), x.setAttribute("aria-pressed", String(x === b))));
      }),
  );
  return m;
}
// Approve the route, with the stock picked first: what the shelf holds is loaded at the warehouse and the store buys
// only the rest. The coordinator says how many (the count is never guessed).
function puApproveRoute(W, st) {
  if (!st || !st.length) return ciApproveRoute(), void render();
  const m = mbModal(
    "Approve the Route",
    `<p class="small" style="margin:0 0 10px">These sit in stock. Take them from the shelf and buy only the rest: buying what we own is money that cannot go to raises, bonuses or the client.</p>${st.map((s, i) => `<label class="pu-rq"><span data-nocase><b>${esc(s.name)}</b><span class="small muted">${puUnits(s.qty, s.unit)} at the ${esc(String(s.where).toLowerCase())} · for ${esc(s.buy.what)}</span></span><input type="number" inputmode="decimal" min="0" max="${s.qty}" data-pupick="${i}" placeholder="${esc(s.unit)}" aria-label="How many ${esc(s.unit)} of ${esc(s.name)}"></label>`).join("")}`,
    {
      submit: "Pick From Stock and Approve",
      onSubmit: () => {
        st.forEach((s, i) => {
          const n = +m.querySelector(`[data-pupick="${i}"]`).value || 0;
          if (!(n > 0)) return;
          const [rid] = String(s.buy.key || "").split(":"),
            P = (DB.projects || []).find((p) => (p.requests || []).some((q) => q.id === rid)),
            q = P && P.requests.find((x) => x.id === rid);
          if (!q) return;
          const rest = puParts(q.what).filter((x) => x !== s.part);
          q.items = [{ what: s.name, qty: n, unit: s.unit, invId: s.id, pickupFrom: "wh" }].concat(rest.length ? [{ what: rest.join(" and "), qty: q.qty, unit: q.unit }] : []);
          (q.log = q.log || []).push({ t: nowStamp(), by: ((currentUser() || {}).name) || role(), text: `${n} ${s.unit} of ${s.name} picked from stock; the store buys only the rest` });
        });
        ciApproveRoute();
        save(), render();
      },
    },
  );
  return m;
}

// ---- wiring -----------------------------------------------------------------------------------------------------------
document.addEventListener(
  "click",
  (e) => {
    const t = e.target && e.target.closest ? e.target : null;
    if (!t) return;
    const at = (s) => t.closest(s);
    let b;
    if ((b = at("[data-puplus]"))) return e.preventDefault(), e.stopPropagation(), (puPlusOpen = puPlusOpen === b.dataset.puplus ? "" : b.dataset.puplus), render();
    if ((b = at("[data-pumi]"))) {
      e.preventDefault(), e.stopPropagation();
      const it = puPlusItems(puPlusOpen)[+b.dataset.pumi];
      return (puPlusOpen = ""), render(), void (it && it[2]());
    }
    puPlusOpen && !at(".pu-menu") && ((puPlusOpen = ""), setTimeout(render, 0));
    if (!at(".pu, .pu-page")) return;
    if ((b = at("[data-puact]"))) {
      e.preventDefault(), e.stopPropagation();
      const x = puOpenRows[b.dataset.puact];
      return void (x && puDo(x));
    }
    if ((b = at("[data-purecv]"))) return e.preventDefault(), e.stopPropagation(), void puReceive((DB.pos || []).find((po) => po.id === b.dataset.purecv));
    if ((b = at("[data-puopen]"))) {
      e.preventDefault();
      const x = puOpenRows[b.dataset.puopen];
      if (!x) return;
      if (x.r && "proc" === view) return void (puPhone() ? bbSheet(x.r) : ((bbSel = x.id), render()));
      return void (x.run ? x.run() : puDo(x));
    }
    if ((b = at("[data-pulater]"))) return e.preventDefault(), (puLaterOpen = !puLaterOpen), void render();
    if ((b = at("[data-pufull]"))) return e.preventDefault(), (puFull[b.dataset.pufull] = !puFull[b.dataset.pufull]), void render();
    if ((b = at("[data-putile]"))) return e.preventDefault(), (puShowAll.tile = puShowAll.tile === b.dataset.putile || "mine" === b.dataset.putile ? "" : b.dataset.putile), void render();
    if ((b = at("[data-pupof]"))) return e.preventDefault(), (puFilter.po = b.dataset.pupof), void render();
    if ((b = at("[data-puinvf]"))) return e.preventDefault(), (puFilter.inv = b.dataset.puinvf), void render();
    if ((b = at("[data-puvf]"))) return e.preventDefault(), (puVendFilter = b.dataset.puvf), void render();
    if ((b = at("[data-pubook]"))) return e.preventDefault(), (puShowAll.book = !puShowAll.book), void render();
    if ((b = at("[data-pugo]"))) return e.preventDefault(), void setView(b.dataset.pugo);
    if ((b = at("tr[data-puvend]"))) {
      const v = (DB.vendors || []).find((x) => x.id === b.dataset.puvend);
      return void (v && puVendorOpen(v));
    }
  },
  !0,
);
function puDo(x) {
  if (x.r) {
    const r = x.r;
    if ("ack" === x.k) {
      // acknowledge it (the site sees the office has it), then link it to the line it is bought for
      "function" == typeof requestAction && r.q && requestAction(r.p.id, r.q.id, "ack");
      save();
      toast(`${r.name}: acknowledged; ${r.askedBy || "the crew"} sees the office has it`, { label: "Open", run: () => ((bbSel = r.id), setView("proc")) });
      return r.lineKey ? render() : bbLinkLine(r);
    }
    if ("find" === x.k) return r.m ? openEditor("mat", r.m.id) : bbDo(r, "open");
    if ("route" === x.k) return setView("recv");
    if ("split" === x.k) return "function" == typeof jpOpenJob ? jpOpenJob(r.p.id, "costs") : (setCurrent(r.p.id), setView("costs"));
    if ("subm" === x.k) return setCurrent(r.p.id), setView("subm");
    if ("quote" === x.k) return puStockGate([r], () => bbQuote([r]));
    if ("order" === x.k) return puStockGate([r], () => bbOrder([r]));
    return bbDo(r, x.k);
  }
  return x.run && x.run();
}
// The stock check at the door: before money is committed on a need the shelf may cover, the person is asked
function puStockGate(R, go) {
  const S0 = R.flatMap((r) => (r.ordered ? [] : puStockFor(r.name).map((s) => Object.assign({ need: r }, s))));
  if (!S0.length) return go();
  return mbModal(
    "Check the Stock First",
    `<p class="small" style="margin:0 0 8px">${S0.map((s) => `<b data-nocase>${esc(puUnits(s.qty, s.unit))} of ${esc(s.name)}</b> at the ${esc(String(s.where).toLowerCase())}, for <span data-nocase>${esc(s.need.name)}</span>`).join("<br>")}</p><p class="small muted" style="margin:0">Use what we own before buying: money spent on what is on the shelf cannot go to raises, bonuses or the client.</p>`,
    { submit: "Buy It Anyway", onSubmit: () => void setTimeout(go, 0) },
  );
}
// the Buy Board's own Order and Ask for Quotes run the same stock check
{
  const bo = bbOrder,
    bq = bbQuote;
  bbOrder = function (L) {
    const R = (L || []).filter(Boolean),
      self = this,
      args = arguments;
    if (R.some((r) => r.__puChecked)) return bo.apply(self, args);
    return puStockGate(R, () => (R.forEach((r) => (r.__puChecked = 1)), bo.apply(self, args), R.forEach((r) => delete r.__puChecked)));
  };
  bbQuote = function (L) {
    const R = (L || []).filter(Boolean),
      self = this,
      args = arguments;
    if (R.some((r) => r.__puChecked)) return bq.apply(self, args);
    let out = null;
    puStockGate(R, () => (R.forEach((r) => (r.__puChecked = 1)), (out = bq.apply(self, args)), R.forEach((r) => delete r.__puChecked)));
    return out;
  };
}

// ---- the registry: the menu, the numbers, the old pages' homes -------------------------------------------------------
(function puRegister() {
  // the menu's numbers are the pages' Needs You (mnItemN reads OC_BADGE through ocBadgeN)
  if ("object" == typeof OC_BADGE) Object.keys(PU_ROWS).forEach((v) => (OC_BADGE[v] = { n: () => puCount(v) }));
  // One question, one number: the Buy Board's number everywhere (the rail, the phone's bar, Today's Buy Board chip, the
  // job's Purchasing, Ask) is the rows whose next tap is the person's (Needs You), not every late row
  try {
    PRED.buyNeeds.label = "Buy Board";
    PRED.buyNeeds.rule = "Needs You on the Buy Board: a due need (late, to acknowledge, or to order within the working week) whose next tap is yours; rows that wait on someone else name who and are not counted";
    PRED.buyNeeds.test = (r) => {
      const x = r && puNeed(r);
      return !!x && "mine" === x.b;
    };
  } catch (e) {}
  // the Purchasing overview and the store run's Route open their new homes; Stock for those it is not listed for
  if ("object" == typeof MN_ALIAS) {
    Object.defineProperty(MN_ALIAS, "ovbuy", { configurable: !0, enumerable: !0, get: () => ((ROLE_VIEWS[role()] || []).includes("proc") ? "proc" : "po") });
    Object.assign(MN_ALIAS, { route: "recv", req: "proc", inv: "proc" });
  }
  "object" == typeof OC_RETIRED && delete OC_RETIRED.ovbuy;
  const L = { proc: "Buy Board", po: "Orders", rfq: "Quotes", recv: "Deliveries", vendors: "Vendors", inv: "Stock" };
  [void 0 !== NAV_LABELS ? NAV_LABELS : null, void 0 !== IA_LABELS ? IA_LABELS : null].forEach((x) => x && Object.assign(x, L));
  try {
    Object.keys(L).forEach((v) => mnKnow(v, L[v]));
  } catch (e) {}
  // the driver picks for the route from Stock (decision 1, 11-03): the register is his too
  ROLE_VIEWS.driver && !ROLE_VIEWS.driver.includes("inv") && ROLE_VIEWS.driver.push("inv");
})();
// the old Purchasing overview opens the role's first Purchasing page
{
  const base = render;
  render = function () {
    if ("ovbuy" === view) view = (ROLE_VIEWS[role()] || []).includes("proc") ? "proc" : "po";
    const r = base.apply(this, arguments);
    try {
      puDraw();
    } catch (e) {
      console.warn("purchasing", e);
    }
    return r;
  };
}
// the Buy Board itself (renderProc's board pane): the FF&E tools and the reports keep their own panes, with the way back
{
  const base = renderProc;
  renderProc = function () {
    const pane = "undefined" != typeof procPane ? procPane : "board";
    if ("finish" === procMode || "board" !== pane) return base.apply(this, arguments);
    try {
      return puBuyRender();
    } catch (e) {
      console.warn("buy board", e);
      return base.apply(this, arguments);
    }
  };
}

// ---- the look ---------------------------------------------------------------------------------------------------------
(() => {
  const css = `
.view.pu-host:not(.pu-full)>:not(.pu){display:none !important}
.view.pu-host.pu-full>:not(.pu){margin-top:16px}
.pu-ph{display:flex;align-items:flex-start;gap:16px}
.pu-ph .pu-tt{flex:1;min-width:0}
.pu-ph .acts{display:flex;gap:8px;align-items:center}
.pu-plus{position:relative}
.pu-plusb{display:inline-flex;align-items:center;gap:6px;min-height:40px}
.pu-menu{position:absolute;right:0;top:46px;width:300px;background:var(--paper);border:1px solid var(--rule);border-radius:12px;box-shadow:0 12px 32px rgba(17,26,46,.16);padding:6px;z-index:60;display:flex;flex-direction:column}
.pu-mi{display:flex;flex-direction:column;align-items:flex-start;gap:2px;min-height:48px;padding:8px 12px;border:0;border-radius:8px;background:transparent;font:inherit;color:var(--ink);text-align:left;cursor:pointer}
.pu-mi span{font-size:12px;color:var(--ink-3)} .pu-mi:hover,.pu-mi:focus{background:var(--paper-3)}
.pu-filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 14px}
.pu-fl{font-size:13px;color:var(--ink-3)}
.pu-sel{min-height:36px}
.pu-chip{min-height:34px;padding:0 12px;border-radius:17px;border:1px solid var(--rule);background:var(--paper);color:var(--ink);font:inherit;font-size:13px;font-weight:600;cursor:pointer}
.pu-chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.pu-sec{background:var(--paper);border:1px solid var(--rule);border-radius:12px;margin:0 0 14px;overflow:hidden}
.pu-sh{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--rule-2)}
.pu-sh h3{margin:0;font-size:15px}
.pu-sh .n{display:inline-flex;align-items:center;justify-content:center;min-width:22px;height:22px;padding:0 7px;border-radius:11px;background:var(--bad);color:#fff;font-size:12px;font-weight:700}
.pu-note{font-size:12.5px;color:var(--ink-3);margin-left:auto}
.pu-empty{margin:0;padding:14px 16px;color:var(--ink-3);font-size:14px}
.pu-rows{display:flex;flex-direction:column}
.pu-row{display:flex;align-items:center;gap:10px;padding:10px 14px;border-top:1px solid var(--rule-2)}
.pu-row:first-child{border-top:0}
.pu-row.sel{background:var(--accent-2)}
.pu-row.bad{box-shadow:inset 3px 0 0 var(--bad)} .pu-row.warn{box-shadow:inset 3px 0 0 var(--warn)}
.pu-rb{flex:1;min-width:0;display:flex;flex-direction:column;align-items:flex-start;gap:2px;border:0;background:none;padding:2px 0;font:inherit;color:var(--ink);text-align:left;cursor:pointer}
.pu-rb b{font-size:14.5px}
.pu-sub,.pu-why,.pu-when{font-size:13px;color:var(--ink-3);line-height:1.4}
.pu-why{color:var(--ink-2)}
.pu-when.bad{color:var(--bad);font-weight:600}
.pu-who{font-size:13px;font-weight:600;color:var(--warn)}
.pu-act{flex:none}
.pu-foot{padding:10px 16px}
.pu-link{border:0;background:none;padding:0;min-height:36px;display:inline-flex;align-items:center;gap:6px;color:var(--accent);font:inherit;font-size:14px;font-weight:600;cursor:pointer}
.pu-laterb{margin:6px 16px}
.pu-tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:0 0 14px}
.pu-tile{display:flex;flex-direction:column;align-items:flex-start;gap:3px;text-align:left;background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:12px 14px;font:inherit;color:var(--ink);cursor:pointer;min-height:92px}
.pu-tile.on{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
.pu-tk{font-size:13px;color:var(--ink-3)} .pu-tile b{font-size:22px} .pu-ts{font-size:12.5px;color:var(--ink-3)}
.pu-note2{font-size:13px;color:var(--ink-3);margin:0 0 12px}
table.pu-vt{width:100%} table.pu-vt td.bad{color:var(--bad);font-weight:600} table.pu-vt tbody tr{cursor:pointer}
.pu-bar{position:sticky;bottom:0;display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:10px 14px;box-shadow:0 -6px 20px rgba(17,26,46,.08);z-index:20}
.pu-bt{flex:1;min-width:0;font-size:14px} .pu-bb{display:flex;gap:8px;flex-wrap:wrap}
.pu-rq{display:flex;align-items:center;gap:10px;padding:8px 0;border-top:1px solid var(--rule-2)}
.pu-rq>span{flex:1;display:flex;flex-direction:column;gap:2px} .pu-rq input{width:96px;min-height:44px}
.pu-conds{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.pu-lines{display:flex;flex-direction:column;gap:6px;max-height:50vh;overflow:auto;margin-top:8px}
.pu-line{display:flex;gap:10px;align-items:flex-start;padding:6px 0;border-top:1px solid var(--rule-2)} .pu-line>span{display:flex;flex-direction:column}
.pu-kv{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-top:1px solid var(--rule-2)}
#buy-board.pu .bb-main{display:flex;gap:16px;align-items:flex-start}
#buy-board.pu .bb-list{flex:1;min-width:0}
#buy-board.pu .pu-row .bb-pick{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;border:0;background:none;cursor:pointer;padding:0}
@media (max-width:760px){
  .pu-ph{flex-direction:column;gap:8px}
  .pu-ph .acts{width:100%}
  .pu-menu{position:fixed;left:16px;right:16px;top:auto;width:auto}
  .pu-tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
  .pu-row{flex-wrap:wrap;padding:12px}
  .pu-row .pu-rb{flex-basis:calc(100% - 56px)}
  .pu-act{min-height:44px;margin-left:auto}
  .pu-link,.pu-chip,.pu-plusb{min-height:44px}
  .pu-chip{padding:0 14px;font-size:14px}
  .pu-sel{min-height:44px;flex:1 1 140px}
  .pu-bar{position:fixed;left:8px;right:8px;bottom:calc(var(--bb-tabs, 64px) + 8px)}
  .pu-bb{width:100%} .pu-bb .btn{flex:1;min-height:44px}
  #buy-board.pu .bb-main{display:block}
  .pu-tile{min-height:84px}
}
`;
  const st = document.createElement("style");
  (st.id = "purchasing-css"), (st.textContent = css), document.head.appendChild(st);
})();
