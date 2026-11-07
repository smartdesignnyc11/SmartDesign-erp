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
  const k = ("function" == typeof dataVer ? dataVer() : "") + "|" + ((DB.inventory || []).map((i) => i.qty).join(","));
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
// A need's stock, in two kinds (CoS 11-06: the rule was "rough-in" in the line's name, an instance fix that missed
// "Electrical wiring" and "Plumbing supply and waste"):
//   sure  what the need's own words name, or the items under its line (puStockFor on each): the stock gate asks about
//         these before money is committed
//   hint  for a contract line that buys material and names no stocked item, the stock filed under the line's cost code
//         ("may be it"): said on the row and in the panel, never a gate, so an allowance on the same code (fixtures
//         beside the PEX) is not held behind a stock check that is not about it
// Each entry carries how: "name", "items" or "code".
function puStockForNeed(r) {
  if (!r || r.ordered) return [];
  const S0 = puStockFor(r.name).map((s) => Object.assign({ how: "name" }, s)),
    L = r.l || (r.lineKey && "function" == typeof findLine ? (findLine(r.lineKey) || {}).line : null),
    seen = new Set(S0.map((s) => s.id));
  ((L && L.items) || []).forEach((it) => puStockFor(it.name || it.item || "").forEach((s) => seen.has(s.id) || (seen.add(s.id), S0.push(Object.assign({ how: "items" }, s)))));
  if (S0.length || !["line", "sub"].includes(r.kind) || !r.code || "99" === r.code || !(L ? "function" != typeof bbBuysLine || bbBuysLine(L) : !0)) return S0;
  return (DB.inventory || [])
    .filter((i) => "tool" !== i.type && String(i.code || "") === String(r.code) && ("function" == typeof invAvailable ? invAvailable(i) : +i.qty) > 0)
    .slice(0, 4)
    .map((i) => ({ id: i.id, part: r.name, name: i.name, qty: "function" == typeof invAvailable ? invAvailable(i) : +i.qty, unit: i.unit || "", where: "function" == typeof locName ? locName(i.loc) : i.loc || "the shop", sure: !1, how: "code" }));
}
// the stock the gate asks about: sure matches only (the need's words or its line's items), never a cost-code hint
const puStockSure = (r) => puStockForNeed(r).filter((s) => "code" !== s.how);
const puUnits = (n, u) => `${n} ${u || ""}${1 === +n || /s$|^ea$|^ls$|^sf$|^lf$/.test(u || "") || !u ? "" : /(x|ch|sh)$/.test(u) ? "es" : "s"}`.trim(),
  puReorder = (i) => +(i.reorderAt != null ? i.reorderAt : i.reorder) || 0;
function puStockSay(S0) {
  if (!S0 || !S0.length) return "";
  const where = [...new Set(S0.map((s) => s.where))].join(" and ");
  return `At the ${where.toLowerCase() === "truck" ? "truck" : where.toLowerCase()}: ${S0.map((s) => `${puUnits(s.qty, s.unit)} of ${s.name}${"code" === s.how ? " (may be it)" : ""}`).join(", ")}. Count before you buy.`;
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
  if (ref && ref.doc) return `${ref.doc.number || ""}${ref.line && ref.line.num ? ` line ${ref.line.num}` : ""}${"sub" === r.kind ? " · subcontract" : ""}`.trim();
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
// A need's one money figure (11-05: the rows read the line's whole budget, $21,500 and $75,000, while the pick bar added
// what was left, $19,850, and the countertop read "$0 priced"): what is left to buy on a contract line or a subcontract
// scope, the price of an FF&E item or a priced material; none when nothing prices it. The row shows it and the pick bar
// adds it, so the bar is always the sum of the picked rows.
function puNeedValue(r) {
  const amt = r && +r.price > 0 ? r2(+r.price) : 0;
  return { amt: amt, say: amt ? `${money(amt)}${(r.draftPOs || []).length ? " in a draft order" : ["line", "sub"].includes(r.kind) ? " left on the line" : ""}` : "" };
}
function puNeed(r) {
  if (!r || r.received || "done" === r.tab) return null;
  const td = today(),
    stock = puStockForNeed(r),
    val = puNeedValue(r),
    drafts = r.draftPOs || [],
    base = { r: r, id: r.id, name: r.name, job: puJob(r.p), line: [puLineWord(r), val.say].filter(Boolean).join(" · "), val: val, stock: stock, pick: !r.ordered && !drafts.length };
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
  // covered only by a draft order: nothing is ordered until it is issued, so it stays the coordinator's, with its date
  else if (drafts.length)
    o = { b: "draft", actor: "coord", why: `${drafts.map((po) => po.number).join(", ")} drafted for ${money(r.price)}${drafts[0].vendor ? ` with ${drafts[0].vendor}` : ""}, not issued: nothing is ordered yet.`, act: "Issue the Draft", k: "draftpo", tone: r.late ? "bad" : "warn" };
  else if (r.dec) {
    const w = puDecWho(r),
      late = r.dec.due && r.dec.due < td ? `, ${dayDiff(r.dec.due, td)} days late` : "";
    o = { actor: w.actor, who: w.who, why: `the decision: ${r.dec.name || "open"}${late}.`, act: "Open the Decision", k: "dec" };
  } else if (puSubmittalOf(r)) {
    const s = puSubmittalOf(r);
    o = "revise" === s.status ? { actor: "sub", who: s.sub || "the sub", why: `submittal ${s.number} came back Revise and Resubmit; the order waits for it.`, act: "Open the Submittal", k: "subm" } : { actor: "designer", who: "the architect", why: `submittal ${s.number} is in review; the order waits for it.`, act: "Open the Submittal", k: "subm" };
  } else if (r.matUnknown) o = { actor: "pm", who: "the PM", why: "the material portion of the line is not set; the line includes labour.", act: "Set the Material Portion", k: "split" };
  else if ((r.rfqs || []).length || puQuoteStage(r)) o = puQuoteStep(r); else if ("sub" === r.kind) o = { actor: "coord", why: "No sub contracted. Over $2,500: three bids, or a reason.", act: "Ask for Bids", k: "quote", tone: r.late ? "bad" : "warn" };
  else if (!r.price) o = { actor: "coord", why: "No price yet.", act: "Ask for Quotes", k: "quote", tone: r.late ? "bad" : "" };
  else o = { actor: "coord", why: `Order by ${fmt(r.orderBy)}.`, act: "Order", k: "order", tone: r.late ? "bad" : "" };
  const st = puStockSay(stock),
    b = "draft" === o.b ? (o.actor === puMe() ? "mine" : "others") : o.b || (!due ? "later" : o.actor === puMe() ? "mine" : "others");
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
// Committed is one number, read through the one money function (jobFin: open orders net of their bills and of what was
// paid on them with no bill); this page adds no definition of its own. A payment on an order before its bill (Tino's
// $8,000) is cost to date, not committed: it is said on its own line under the figure, here and on the job's Budget.
function puCommitted(pid) {
  const P = (DB.projects || []).filter((p) => (!pid || p.id === pid) && (DB.pos || []).some((po) => po.projectId === p.id && puLive(po)));
  let total = 0;
  P.forEach((p) => {
    try {
      total += +jobFin(p).committed || 0;
    } catch (e) {}
  });
  return { total: r2(total), pos: (DB.pos || []).filter((po) => puLive(po) && (!pid || po.projectId === pid)), prepaid: puPrepaid(pid) };
}
function puPrepaid(pid) {
  return (DB.pos || [])
    .filter((po) => ["issued", "partial"].includes(po.status) && (!pid || po.projectId === pid))
    .map((po) => ({ po: po, amt: "function" == typeof poPaidDirect ? poPaidDirect(po) : 0 }))
    .filter((x) => x.amt > 0.5);
}
const puPrepaidSay = (X) => (X.length ? `Paid before a bill: ${money(r2(X.reduce((a, x) => a + x.amt, 0)))} (${X.map((x) => `${x.po.vendor}, ${x.po.number}`).join("; ")}). It is cost to date, not committed; it comes off the next bill.` : "");
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
  puLineOverRows(pid).forEach(put);
  puPreAwardRows(pid).forEach(put);
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
        .filter((i) => (i.claim || ["short", "damaged", "wrong"].includes(i.type)) && "open" === (i.status || "open"))
        .forEach((i, k) =>
          put({ id: `claim:${po.id}:${k}`, name: `${po.vendor}: ${i.type} on ${po.number}`, job: puJob(DB.projects.find((p) => p.id === po.projectId)), line: `${i.qty || ""} ${(po.lines.find((l) => l.id === i.lineId) || {}).item || ""}`.trim(), why: "Claim the replacement or the credit before the bill is paid.", act: "Close the Claim", actRun: () => puCloseClaimSheet(po, i), run: () => flowGo.po(po)(), tone: "bad" }),
        );
    });
  try {
    selClaims()
      .filter((c) => "undefined" != typeof CLAIM_OPEN && CLAIM_OPEN.includes(c.status) && (!pid || c.projectId === pid))
      .forEach((c) => {
        const it = selItem(c.itemId),
          age = dayDiff(c.raisedAt, today());
        put({ id: "selclaim:" + c.id, name: `${it ? it.name : "Item"}: ${c.kind} on arrival`, job: puJob(DB.projects.find((p) => p.id === c.projectId)), line: `Claim with ${c.vendor || "the vendor"}${age > 0 ? `, ${age} days open` : ""}`, why: `It does not go to the site until the claim closes. ${c.vendor || "The vendor"} owes a replacement${it && +it.cost ? `, or a ${money(r2(+it.cost * (+c.qty || 1)))} credit` : ""}.`, act: "Open the Item", run: () => ("function" == typeof selOpenItem ? selOpenItem(c.itemId) : setView("sel")), tone: "bad", tile: "owed", money: 0, claim: 1 });
      });
  } catch (e) {}
  try {
    retOpen()
      .filter((r) => !pid || r.projectId === pid)
      .forEach((r) => {
        const risk = retRisk(r),
          exp = retExpected(r),
          credit = ["shipped", "received"].includes(r.status);
        put({ id: "ret:" + r.id, name: credit ? `${r.vendor}: ${money(exp)} credit to confirm` : `${r.name}: ${money(exp)} owed back`, job: puJob(DB.projects.find((p) => p.id === r.projectId)), line: `${r.vendor}${r.rma ? ` · ${r.rma}` : ""} · ${risk.label || "no return-by date"}${Math.abs(retValue(r) - exp) > 0.5 ? ` · ${money(retValue(r))} of goods, less ${money(r2(retValue(r) - exp))} in fees` : ""}`, why: credit ? "Shipped back; the credit is not on a statement yet." : (retDaysLeft(r) ?? 0) < 0 ? "The return window closed. Ask anyway, or write it off with a reason." : "Ship it back before the window closes.", act: credit ? "Find the Credit" : "Open the Return", run: () => ("function" == typeof retOne ? retOne(r) : retModal()), tone: 3 === risk.lvl ? "bad" : "warn", money: exp, tile: "owed" });
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
// who comes on site needs a certificate (Alan, 10-25): a subcontract, a service or a delivery carried inside, never a
// curb drop or a shipment (poOnSite, the one rule the order's papers read)
function puVendorOnSite(v) {
  const n = v.name,
    po = (DB.pos || []).find((x) => x.vendor === n && puLive(x) && ("function" != typeof poOnSite || poOnSite(x)));
  if (po) return ["subcontract", "service"].includes(po.type) ? `${po.number} puts them on site` : `${po.number} is carried inside`;
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
      open = (DB.pos || []).filter((po) => po.vendor === v.name && puLive(po) && ("function" != typeof poOnSite || poOnSite(po)));
    if (lapsed && (open.length || (DB.bills || []).some((b) => b.vendor === v.name && !["paid", "void"].includes(b.status)) || /window|plumb|electr|tile|mill/i.test(v.trade || "")))
      return R.push({ b: "mine", actor: "coord", id: "v:coi:" + v.id, name: `${v.name}: blocked`, job: v.trade || "", line: `Insurance lapsed ${fmt(v.insuranceExp)}`, why: "No new order and no one on site until the certificate lands.", act: "Chase the Certificate", run: () => puChasePaper(v, "coi"), tone: "bad" });
    const unpaid = (DB.bills || []).filter((b) => b.vendor === v.name && !["paid", "verified", "void", "rejected"].includes(b.status) && !b.paidAt);
    if (!v.w9 && unpaid.length) {
      const b = unpaid[0],
        out = "function" == typeof billBankCovers && billBankCovers(b);
      return R.push({ b: "mine", actor: "coord", id: "v:w9:" + v.id, name: `${v.name}: W-9 before ${b.number}`, job: v.trade || "", line: `${b.number} · ${money(billTotal(b))}${out ? " · the bank shows it already left" : ""}`, why: "Ask for the W-9 today: without it the year-end 1099 is wrong and the payment may need backup withholding.", act: "Ask for the W-9", run: () => puChasePaper(v, "w9"), tone: "warn" });
    }
    const site = !v.insuranceExp && puVendorOnSite(v);
    site && R.push({ b: "mine", actor: "coord", id: "v:site:" + v.id, name: `${v.name}: no certificate on file`, job: v.trade || "", line: site, why: "Anyone coming on site or inside needs a current certificate of insurance.", act: "Chase the Certificate", run: () => puChasePaper(v, "coi"), tone: "warn" });
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
  Q.forEach((q) => {
    // the request's one stage (rfqStateOf: the same reading rfqLineState gives the line's need status); a request not
    // sent yet is the coordinator's or the foreman's, never "waiting on the vendors"
    const st = rfqStateOf(q),
      asked = (q.vendors || []).length,
      got = (q.vendors || []).filter((iv) => {
        const x = rfqQuoteOf(q, iv.id, 1);
        return x && !x.unreadable;
      }).length,
      budget = (() => {
        let t = 0,
          any = !1;
        try {
          rfqBudgetsNow(q).forEach((b) => {
            const c = "function" == typeof lineCommitment && !String(b.key).startsWith("sel:") ? lineCommitment(b.key) : null,
              v = c && null != c.left ? +c.left : null != b.budget ? +b.budget : null != b.whole ? +b.whole : null;
            null != v && ((t += v), (any = !0));
          });
        } catch (e) {}
        return any ? r2(t) : null;
      })(),
      mine = "coord" === st.actor;
    R.push({ b: mine ? "mine" : "others", actor: st.actor, who: mine ? "" : st.who, id: "rfq:" + q.id, name: `${q.number} · ${q.title || (q.lines || []).map((l) => l.item).slice(0, 2).join(", ") || "request for quote"}`, job: puJob(DB.projects.find((p) => p.id === q.projectId)), line: st.label, why: `Budget ${null != budget ? money(budget) : "none on the line"} · Quotes In ${got} of ${asked || 0} · Due ${q.dueDate ? fmt(q.dueDate) : q.dueWanted ? fmt(q.dueWanted) : "not set"}. ${st.why}`, act: st.act, run: () => rfqOpenFor(q.id) });
  });
  return R;
}
// one count per page: the rows whose next tap is the person's
const PU_ROWS = {
  // the menu's Buy Board is every job's; the page's own heading counts the rows its filters show
  proc: () => puNeeds("").filter((x) => "mine" === x.b),
  po: () => puOrderRows("").filter((x) => x.actor === puMe()),
  recv: () => puDelivRows("").filter((x) => x.actor === puMe()),
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
  // Orders opens on every order (a draft from an award is found where its order is), drafts first
  puFilter = { po: "all", vendors: "all", inv: "all" },
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
  return `<div class="pu-row ${x.tone || ""}${pick ? " pu-pickable" : ""}${o.sel && o.sel === x.id ? " sel" : ""}" data-purow="${esc(x.id)}"${x.val ? ` data-puamt="${x.val.amt}"` : ""}>${pick}<button type="button" class="pu-rb" data-puopen="${esc(x.id)}"><b data-nocase>${esc(x.name)}</b>${sub ? `<span class="pu-sub" data-nocase>${esc(sub)}</span>` : ""}${who}<span class="pu-why" data-nocase>${esc(x.why || "")}</span>${x.when ? `<span class="pu-when ${x.r && x.r.late ? "bad" : ""}">${esc(x.when)}</span>` : ""}</button>${x.act && !o.others && !o.quiet ? `<button type="button" class="btn sm pu-act" data-puact="${esc(x.id)}">${esc(x.act)}</button>` : ""}</div>`;
}
function puSecHtml(key, title, rows, o) {
  o = o || {};
  if (!rows.length && !o.empty) return "";
  // the count is the menu badge's source only on the firm's page; inside a job it counts the job (the menu counts the firm)
  // nothing waiting carries no number (the rail shows none either): the empty sentence says it
  const n = o.count && rows.length ? `<span class="n"${puInJob() || o.scoped ? "" : ` data-ocbadge="${esc(o.count)}"`}>${rows.length}</span>` : "";
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
      ["Blank Need", "Only when no line covers it; the line is asked for first", () => puNewNeed()],
    ],
    // One New on Orders (SPEC: from lines first, a blank order behind More). Both open the one New PO sheet: Which
    // Lines? for the job, with its job switch (src/puorders.js); the blank order is the same sheet's Start Blank.
    po: [
      ["New Purchase Order From Lines", "Pick the job's estimate, change-order or invoice lines", () => puNewPOFromLines()],
      ["Blank Purchase Order", "Only when no line covers it: shop supplies, tools", () => puNewPOFromLines(!0), { more: 1 }],
    ],
    rfq: [["New Request for Quote", "Starts from the lines you are buying for", () => ("function" == typeof rfqNewSheet ? rfqNewSheet() : puBuyFromDoc("quote"))]],
    recv: [["Log Something That Arrived", "With no order behind it", () => ("function" == typeof openEditor ? openEditor("mat", null) : null)]],
    vendors: [],
    inv: [
      ["New Stock Item", "A consumable or a tool", click("btn-newinv")],
      ["Count a Shelf", "Set what is really there", click("btn-invmove")],
      ["Move a Tool", "A pickup and a drop-off on the driver's list", click("btn-invmove")],
    ],
  }[v] || [];
}
let puPlusOpen = "",
  puPlusMore = "";
// the menu's items; an item marked more sits behind More (a blank start is secondary, never first)
function puMenuHtml(v, items) {
  const more = items.some((it) => it[3] && it[3].more) && puPlusMore !== v;
  return items.map((it, i) => (it[3] && it[3].more && more ? "" : `<button type="button" role="menuitem" class="pu-mi" data-pumi="${i}"><b>${esc(it[0])}</b><span>${esc(it[1])}</span></button>`)).join("") + (more ? `<button type="button" role="menuitem" class="pu-mi pu-mimore" data-pumore="${v}" aria-expanded="false"><b>More</b><span>A blank order</span></button>` : "");
}
function puHeadHtml(v, extra) {
  // inside a job the page is the job's Purchasing tab: its name, the job's words, and the job's one + (src/jobpage.js)
  const job = "function" == typeof jpOn && jpOn(),
    // the controller and billing read Purchasing and buy nothing (src/puorders.js puReadOnly): no + for them
    items = job || ["controller", "billing"].includes(role()) ? [] : puPlusItems(v),
    name = job && "proc" === v ? "Purchasing" : PU_NAME[v],
    lead = job ? "This job's needs, orders and deliveries: what to buy and what is coming." : PU_LEAD[v];
  // on the phone the job's header names the section (src/jobpage.js): no second heading under it
  if (job && puPhone()) return "";
  return `<div class="ph pu-ph bb-ph0"><div class="pu-tt bb-title"><h2>${esc(name)}</h2><p class="lead" data-nocase>${esc(lead)}</p></div><div class="acts">${extra || ""}${items.length ? `<div class="pu-plus"><button type="button" class="btn pu-plusb" data-puplus="${v}" aria-expanded="${puPlusOpen === v}" aria-label="New">${PU_IC.plus}<span>New</span></button>${puPlusOpen === v ? `<div class="pu-menu" role="menu">${puMenuHtml(v, items)}</div>` : ""}</div>` : ""}</div></div>`;
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
  puHideOld(sec, !puFull[v], v);
  return host;
}
// The old page's own New button (its handlers, its id) rides in the new head, not blue (housekeeping is never blue); it
// goes home before each draw and when the old page shows (a record open)
const PU_MOVE = { vendors: ["btn-newvendor"] },
  PU_BTN = {};
// v: only that page's buttons (dropping another page never takes this page's button away)
function puBtnHome(v) {
  Object.keys(PU_BTN)
    .filter((id) => !v || (PU_MOVE[v] || []).includes(id))
    .map((id) => PU_BTN[id])
    .forEach((x) => {
    x.b.classList.toggle("primary", x.primary);
    x.b.parentElement !== x.home && x.home.appendChild(x.b);
  });
}
function puBtnMove(v, host) {
  const acts = host.querySelector(".pu-ph .acts");
  acts &&
    (PU_MOVE[v] || []).forEach((id) => {
      const b = (PU_BTN[id] && PU_BTN[id].b) || document.getElementById(id);
      if (!b) return;
      PU_BTN[id] || (PU_BTN[id] = { b: b, home: b.parentElement, primary: b.classList.contains("primary") });
      b.classList.remove("primary"), acts.appendChild(b);
    });
}
// What stays on screen of the old page: on the desktop the receiving line by line is Deliveries' Arriving (the phone has
// the Receive sheet); Orders keeps the per-line New PO table (buying starts from the line) until Reports' Cash holds it.
// (Orders' Client Funds card folds under Matching, Promises and Client Funds: its per-line New PO buttons were a second
// New, and Reports' Cash holds it; CoS 11-06)
const PU_KEEP = { recv: ["recv-body"] },
  puKeep = (v, c) => (PU_KEEP[v] || []).includes(c.id) && !("recv" === v && puPhone());
// the old page's parts are hidden inline (a phone rule with !important on an id would show them otherwise).
// A part's own display is put back only while our hide still holds it (display none, !important): once the old page's
// render has written the part's display itself (renderPO opening an order shows #po-doc and hides #po-table), that value
// is the current one, and putting back the one saved before would show the list over the open order (the walk's J6, 11-04).
function puHideOld(sec, hide0, v) {
  [...sec.children].forEach((c) => c.classList.contains("pu") || uiHideOld(c, hide0 && !puKeep(v, c), "puhid"));
}
// one part of an old page hidden (hide) or shown again; key is the page's marker (the Design overview has its own)
function uiHideOld(c, hide, key) {
  const ours = "important" === c.style.getPropertyPriority("display");
  hide
    ? ((null == c.dataset[key] || !ours) && (c.dataset[key] = c.style.display || ""), c.style.setProperty("display", "none", "important"))
    : null != c.dataset[key] && (ours && (c.style.removeProperty("display"), c.dataset[key] && (c.style.display = c.dataset[key])), delete c.dataset[key]);
}
function puDrop(v) {
  const sec = document.getElementById("v-" + v);
  if (!sec) return;
  puBtnHome(v), puHideOld(sec, !1);
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
    const priced = picked.filter((x) => x.val && x.val.amt > 0),
      unpriced = picked.filter((x) => !(x.val && x.val.amt > 0)),
      total = r2(priced.reduce((a, x) => a + x.val.amt, 0)),
      quotes = unpriced.length > 0 || total > 2500,
      jobs = [...new Set(picked.map((x) => x.job))];
    bar = `<div class="bb-bar pu-bar"><span class="pu-bt"><b>${picked.length} line${1 === picked.length ? "" : "s"} picked</b><span data-nocase data-pubar="${total}" data-punoprice="${unpriced.length}"> · ${priced.length ? `${money(total)} for ${priced.length === picked.length ? (1 === picked.length ? "it" : "all") : priced.length} priced` : "none priced"}${unpriced.length ? `, ${unpriced.length} with no price yet` : ""} · ${esc(jobs.join(", "))}</span></span><span class="pu-bb"><button type="button" class="btn sm ghost" id="pu-clear">Clear</button><button type="button" class="btn ${quotes ? "" : "primary"}" id="bb-order">${quotes ? "Order, With a Reason" : `Order ${picked.length} Line${1 === picked.length ? "" : "s"}`}</button><button type="button" class="btn ${quotes ? "primary" : ""}" id="bb-quote">Ask for Quotes</button></span></div>`;
  }
  const laterFirst = later[0] && later[0].r.orderBy,
    laterLast = later.length && later[later.length - 1].r.orderBy,
    laterBtn = later.length ? `<button type="button" class="pu-link pu-laterb" data-pulater="1" aria-expanded="${puLaterOpen}">${puLaterOpen ? "Hide the Later Needs" : `Show the Later Needs${laterFirst ? `, Order by ${fmt(laterFirst)}${laterLast && laterLast !== laterFirst ? ` to ${fmt(laterLast)}` : ""}` : ""}`}${puLaterOpen ? PU_IC.up : PU_IC.down}</button>` : "",
    list =
      puSecHtml("mine", "Needs You", mine, { count: "proc", scoped: !!(bbProj || bbVendor || bbTrade), pick: 1, sel: bbSel, empty: "Nothing waits on you. Every due need is ordered, asked for or with someone else." }) +
      puSecHtml("route", "On Today's Route", route, { quiet: 1, note: "Counted once, in the route approval on Deliveries" }) +
      // inside a job, its orders promised after the day the site needs them (they live on Deliveries; the PM reads them here)
      (puInJob() ? puSecHtml("promise", "Promised After It Is Needed", puDelivRows(puInJob()).filter((x) => x.need).map((x) => Object.assign({}, x, { who: "the coordinator, expediting" })), { others: 1 }) : "") +
      puSecHtml("others", "Waiting on Someone Else", others, { others: 1, sel: bbSel }) +
      (later.length ? `<section class="pu-sec" data-pusec="laterfold"><div class="pu-sh"><h3>Later</h3></div>${laterBtn}</section>${puLaterOpen ? puSecHtml("later", "Later Needs", later, { pick: 1, sel: bbSel }) : ""}` : ""),
    panel = !phone ? `<aside class="bb-panel" aria-label="${esc(sel ? sel.name : "The need")}">${sel ? bbPanelHtml(sel.r, picked.length) : bbPanelHtml(null)}</aside>` : "",
    foot = `<div class="pu-foot"><button type="button" class="pu-link" id="bb-more">FF&amp;E Buying Tools</button></div>`;
  root.innerHTML = `<div class="pu pr-keep bb ${phone ? "bb-phone" : "bb-desk"} ${picked.length ? "bb-picking" : ""}" data-pupage="proc" id="buy-board" data-os-keep>${puHeadHtml("proc")}${filters}<div class="bb-main"><div class="bb-list pu-list" data-nocase>${list}${foot}</div>${panel}</div>${bar}</div>`;
  bbWire(root);
  const q = (s) => root.querySelector(s);
  q("#pu-clear") && (q("#pu-clear").onclick = () => (bbPick.clear(), render()));
}

// The pages drawn over the old ones (#v-po, #v-rfq, #v-recv, #v-vendors, #v-inv)
function puTile(id, k, v, s, extra) {
  // extra: a line of its own under the figure (what the figure leaves out, said where it is read)
  return `<button type="button" class="pu-tile ${puShowAll.tile === id ? "on" : ""}" data-putile="${id}" aria-pressed="${puShowAll.tile === id}"><span class="pu-tk">${esc(k)}</span><b>${esc(v)}</b><span class="pu-ts" data-nocase>${esc(s)}</span>${extra ? `<span class="pu-tx" data-pux="${id}" data-nocase>${esc(extra)}</span>` : ""}</button>`;
}
function puPageHtml(v, parts) {
  return `<div class="pu-page pr-keep" data-pupage="${v}">${puHeadHtml(v, parts.acts)}${parts.tiles ? `<div class="pu-tiles">${parts.tiles}</div>` : ""}${parts.filters || ""}${parts.body}</div>`;
}
function puOrders() {
  const pid = puInJob(),
    rows = puOrderRows(pid),
    me = puMe(),
    mine = rows.filter((x) => x.actor === me),
    others = rows.filter((x) => x.actor !== me && "tile" !== x.actor).map((x) => Object.assign({}, x, { who: PU_ROLE_WORD[x.actor] })),
    owed = rows.filter((x) => "owed" === x.tile),
    lineOver = rows.filter((x) => "lineover" === x.tile),
    lineOverSum = r2(lineOver.reduce((a, x) => a + (x.money || 0), 0)),
    over = rows.filter((x) => "over" === x.tile),
    cnb = puCommitted(pid),
    owedSum = r2(owed.reduce((a, x) => a + (x.money || 0), 0)),
    overSum = r2(over.reduce((a, x) => a + (x.money || 0), 0)),
    cnbSum = cnb.total,
    t = puShowAll.tile || "",
    f = puFilter.po,
    pos = (DB.pos || []).filter((po) => (!pid || po.projectId === pid) && ("all" === f ? !0 : "draft" === f ? "draft" === po.status : "received" === f ? "received" === po.status : puLive(po))).sort((a, b) => ({ draft: 0, pending: 1, issued: 2, partial: 2, received: 3 }[a.status] ?? 4) - ({ draft: 0, pending: 1, issued: 2, partial: 2, received: 3 }[b.status] ?? 4)),
    poRow = (po) => {
      const st = "function" == typeof poState ? poState(po) : { msg: po.status };
      // one line names the order, its vendor, its job and what it buys: an order is found by any of them
      return { id: "po:" + po.id, name: `${po.number} · ${po.vendor || "No vendor"} · ${puJob(DB.projects.find((p) => p.id === po.projectId))}: ${(po.lines || []).map((l) => l.item).filter(Boolean).slice(0, 3).join(", ")}`, job: "", line: `Total ${money(poTotal(po).total)} · Paid ${money(poPaid(po))} · Billed ${money(puPoBilled(po))}${po.expected ? ` · Expected ${fmt(po.expected)}` : ""}`, why: st.msg || po.status, run: () => flowGo.po(po)() };
    },
    tileRows = "lineover" === t ? lineOver : "owed" === t ? owed : "over" === t ? over : "cnb" === t ? cnb.pos.map((po) => Object.assign(poRow(po), { id: "cnb:" + po.id, why: `Ordered ${money(poTotal(po).total)} · billed ${money(puPoBilled(po))}${poPaidDirect(po) > 0.5 ? ` · paid before a bill ${money(poPaidDirect(po))}` : ""}` })) : null,
    tiles =
      puTile("mine", "Needs You", String(mine.length), "rows whose next tap is yours") +
      puTile("owed", "Owed Back", money(owedSum), `${owed.filter((x) => !x.claim).length} return${1 === owed.filter((x) => !x.claim).length ? "" : "s"} and credits${owed.some((x) => x.claim) ? `, ${owed.filter((x) => x.claim).length} claim${owed.filter((x) => x.claim).length > 1 ? "s" : ""} for a replacement` : ""}`) +
      puTile("over", "Over the Order", money(overSum), over.length ? over.map((x) => x.po.number).join(", ") : "nothing paid past an order") +
      puTile("lineover", "Over the Line", money(lineOverSum), lineOver.length ? `${lineOver.length} line${1 === lineOver.length ? "" : "s"}: spent and ordered past the budget` : "every line within its budget") +
      puTile("cnb", "Committed, Not Yet Billed", money(cnbSum), `${cnb.pos.length} open order${1 === cnb.pos.length ? "" : "s"}, net of their bills`, puPrepaidSay(cnb.prepaid)),
    chips = [["draft", "Draft"], ["open", "Open"], ["received", "Received"], ["all", "All"]],
    filters = `<div class="pu-filters"><span class="pu-fl">Orders:</span>${chips.map(([k, l]) => `<button type="button" class="pu-chip ${f === k ? "on" : ""}" data-pupof="${k}" aria-pressed="${f === k}">${l}</button>`).join("")}</div>`,
    body =
      (tileRows ? puSecHtml("tile", { owed: "Owed Back", over: "Over the Order", lineover: "Over the Line", cnb: "Committed, Not Yet Billed" }[t], tileRows, { empty: "Nothing here." }) : "") +
      puSecHtml("mine", "Needs You", mine, { count: "po", empty: "Nothing waits on you." }) +
      puSecHtml("others", "Waiting on Someone Else", others, { others: 1 }) +
      filters +
      puSecHtml("orders", "Orders", pos.map(poRow), { quiet: 1, empty: "draft" === f ? "Nothing sits in draft." : "No orders in this filter." }) +
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
    office = ((DB.sel || {}).items || []).filter((it) => ["office", "ship"].includes(it.stage) && (!pid || it.projectId === pid)).map((it) => ({ id: "sel:" + it.id, name: it.name, job: puJob(DB.projects.find((p) => p.id === it.projectId)), line: `${it.vendor || ""} · ${"ship" === it.stage ? "in transit" : "at the office"}`, why: puHeldBy(it) ? `Held: ${puHeldBy(it).kind} on arrival, claim open with ${puHeldBy(it).vendor || it.vendor || "the vendor"}. It does not go to the site until the claim closes.` : "ship" === it.stage ? ((it.dates || {}).eta ? `Arriving ${fmt(it.dates.eta)}` : "No date yet") : `On site ${fmt(selNeedOnSite(it))}: deliver it with the route`, tone: puHeldBy(it) ? "bad" : "", run: () => ("function" == typeof selOpenItem ? selOpenItem(it.id) : setView("sel")) })),
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
      // the phone receives from the sheet; the desktop receives line by line below (the old page's cards, kept on screen)
      (arriving.length && puPhone() ? `<section class="pu-sec" data-pusec="arriving"><div class="pu-sh"><h3>Arriving</h3></div><div class="pu-rows">${arrBody.join("")}</div></section>` : "") +
      puSecHtml("office", "In Transit and At the Office", office, { quiet: 1 }) +
      puSecHtml("back", "Going Back", back, { quiet: 1 }) +
      (puPhone() ? puFullHtml("recv", "Receive Line by Line") : `<h3 class="pu-h3">Arriving: Receive Line by Line</h3>`);
  return puPageHtml("recv", { body: body });
}
// an item at the office under an open claim on arrival (damaged, short, wrong) is held there, never sent with the route
// (the coordinator expert, 11-05: the damaged range read "deliver it with the route")
function puHeldBy(it) {
  try {
    return selClaims().find((c) => c.itemId === it.id && ("undefined" == typeof CLAIM_OPEN || CLAIM_OPEN.includes(c.status))) || null;
  } catch (e) {
    return null;
  }
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
    phone = puPhone(),
    // one row per vendor, the same facts on both devices (puVendorFacts, src/puorders.js): every row opens the record
    list = phone
      ? `<div class="pu-rows">${V.map((v) => {
          const F = puVendorFacts(v),
            x = { id: "vend:" + v.id, name: v.name, job: v.trade || "", line: "", why: "", run: () => puVendorOpen(v) };
          puOpenRows[x.id] = x;
          return `<div class="pu-row ${F.tone}" data-purow="${esc(x.id)}"><button type="button" class="pu-rb" data-puopen="${esc(x.id)}"><b data-nocase>${esc(v.name)}</b><span class="pu-sub" data-nocase>${esc([v.trade, F.openSay].filter(Boolean).join(" · "))}</span><span class="pu-why" data-nocase>${F.owed > 0.5 ? `Owed back ${money(F.owed)} · ` : ""}${F.over.length ? `${money(F.overAmt)} paid over ${esc(F.over.map((x) => x.po.number).join(", "))} · ` : ""}${esc(F.papersSay)} · <span data-puw9="${v.w9 ? "on" : "none"}">W-9 ${v.w9 ? "on file" : "none"}</span> · Paid ${money(F.paid)}${F.perf ? ` · ${esc(F.perf)}` : ""}</span></button></div>`;
        }).join("")}</div>`
      : `<table class="t pu-vt"><thead><tr><th>Vendor</th><th>Open Orders</th><th class="num">Owed Back</th><th>Insurance</th><th>W-9</th><th class="num">Paid</th><th>On Time</th></tr></thead><tbody>${V.map((v) => {
          const F = puVendorFacts(v);
          return `<tr data-puvend="${esc(v.id)}" tabindex="0"><td><b data-nocase>${esc(v.name)}</b>${v.trade ? `<div class="small muted" data-nocase>${esc(v.trade)}</div>` : ""}</td><td data-nocase>${F.open.length ? `${esc(F.open.map((po) => po.number).join(", "))}<div class="small muted">${money(F.openAmt)}</div>` : '<span class="muted">none open</span>'}</td><td class="num ${F.owed > 0.5 || F.over.length ? "warn" : ""}">${F.owed > 0.5 ? money(F.owed) : ""}${F.over.length ? `<div class="small">${money(F.overAmt)} paid over ${esc(F.over.map((x) => x.po.number).join(", "))}</div>` : ""}</td><td class="${F.coiTone}" data-nocase>${esc(F.coiSay)}</td><td data-puw9="${v.w9 ? "on" : "none"}">${v.w9 ? "On file" : "None"}</td><td class="num">${money(F.paid)}</td><td data-nocase>${esc(F.perf)}</td></tr>`;
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
  puNeeds("").filter((x) => !x.r.ordered && "gone" !== x.b && (x.stock || []).length).forEach((x) => x.stock.forEach((s) => want.push({ id: `want:${x.id}:${s.id}`, name: `${puUnits(s.qty, s.unit)} of ${s.name}${"code" === s.how ? " (may be it)" : ""}`, job: x.job, line: `at the ${String(s.where).toLowerCase()}`, why: `Wanted by ${x.name}`, run: () => ((bbSel = x.id), setView("proc")) })));
  const chips = [["all", "All"], ["mat", "Materials"], ["tool", "Tools"], ["job", "At a Job"]],
    filters = `<div class="pu-filters"><span class="pu-fl">Show:</span>${chips.map(([k, l]) => `<button type="button" class="pu-chip ${f === k ? "on" : ""}" data-puinvf="${k}" aria-pressed="${f === k}">${l}</button>`).join("")}</div>`,
    wantOf = (i) => want.filter((w) => w.id.endsWith(":" + i.id)),
    list = I.map((i) => {
      const W = wantOf(i);
      return { id: "item:" + i.id, name: i.name, job: "", line: `${puUnits(invAvailable(i), i.unit)} on hand · ${locName(i.loc)}`, why: W.length ? `Needed by ${W.map((w) => `${w.why.replace(/^Wanted by /, "")}${w.job ? ` (${w.job})` : ""}`).join("; ")}` : "tool" === i.type ? "Tool" : puReorder(i) ? `Reorder at ${puUnits(puReorder(i), i.unit)}` : "", tone: W.length ? "warn" : "", run: () => ("function" == typeof openEditor ? openEditor("inv", i.id) : null) };
    }),
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
// The phone's header names the page from its first heading, read before this page is drawn over the old one (whose
// heading named a job: "Selections — 121 State Street"). A firm-wide page names itself, never a job.
function puCrumbs() {
  if (!puPhone()) return;
  const h = document.querySelector(".view.on .pu .pu-ph h2, .view.on .pu-page .pu-ph h2"),
    c = document.getElementById("crumbs");
  if (!h || !c) return;
  const t = h.textContent.trim();
  c.textContent.trim() !== t && (c.innerHTML = `<b>${esc(t)}</b>`);
  document.querySelectorAll(".view.on h2.td-in-hdr").forEach((x) => x !== h && x.classList.remove("td-in-hdr"));
  h.classList.add("td-in-hdr");
}
// the field roles keep their own pages (the crew's Deliveries is the site's receiving)
const puOffice = () => !["foreman", "crew", "client"].includes(role());
// a role's first Purchasing page: the Buy Board for those who buy, Orders for the controller and billing (SPEC §2)
const puHomeView = () => ((ROLE_VIEWS[role()] || []).includes("proc") && !["controller", "billing"].includes(role()) ? "proc" : "po");
function puDraw() {
  const v = view;
  Object.keys(PU_PAGES).forEach((x) => x !== v && puDrop(x));
  if (!PU_PAGES[v] || !puOffice() || puRecordOpen(v)) return void (PU_PAGES[v] && puDrop(v));
  const host = puHost(v);
  if (!host) return;
  puOpenRows = {};
  try {
    puBtnHome(v), (host.innerHTML = PU_PAGES[v]()), puBtnMove(v, host);
  } catch (e) {
    console.warn("purchasing page", v, e), puDrop(v);
  }
}

// ---- what the buttons do --------------------------------------------------------------------------------------------
function puVendorOpen(v) {
  "function" == typeof vendorPage ? vendorPage(v.id) : openVendor(v.id);
}
// A chase opens its draft, never the vendor's page (Chase the Certificate opened the page and drafted nothing): the one
// chase sheet (eaNudge) with the address, the subject and a message naming the missing paper and the date it is needed
// by; it goes to the person's mailbox to read and send, an expectation is logged and the follow-up set. The lapsed or
// lapsing certificate uses the coordinator's Do Now chase (coiChaseItem, the booking named); the rest says the same.
// A claim on an order closes three ways: the credit came (its amount), the replacement came (received on the sheet),
// or it is written off with a reason. Until then it holds its row on Orders; it could not close at all before (the
// CoS, 11-06), so the row never left. Every close is an audit row with who, when, how and why.
function puClaimClose(po, c, res) {
  if (!po || !c) return;
  (c.status = "closed"), (c.resolution = Object.assign({ at: appNowIso(), by: ((currentUser() || {}).name) || role() }, res || {}));
  try {
    audit("po", po.id, "claim-closed", { type: c.type, qty: c.qty, item: c.item || "" }, c.resolution, (res && res.why) || "");
  } catch (e) {}
  const still = (po.issues || []).filter((x) => x.claim && "open" === (x.status || "open"));
  still.length || delete po.flag;
  log(`${po.number}: the ${c.type} claim on ${c.item || "a line"} closed — ${"credit" === res.how ? `credit ${money(+res.amount || 0)}` : "replaced" === res.how ? "replaced" : `written off: ${res.why}`}`);
}
function puCloseClaimSheet(po, c) {
  if (!po || !c) return;
  const m = mbModal(
    `Close the Claim — <span data-nocase>${esc(po.number)}</span>`,
    `<p class="small muted" style="margin:0 0 10px" data-nocase>${esc(po.vendor)} · ${esc(c.type)}: ${esc(String(c.qty || ""))} ${esc(c.unit || "")} ${esc(c.item || "")}${c.amount ? ` · ${money(c.amount)}` : ""}</p><label class="f"><span>How It Closed</span><select data-f="how"><option value="credit">The credit came</option><option value="replaced">The replacement came</option><option value="writeoff">Written off</option></select></label><label class="f"><span>Credit Amount</span><input type="number" inputmode="decimal" step="0.01" min="0" data-f="amount" value="" placeholder="${c.amount ? r2(c.amount) : "0.00"}"></label><label class="f"><span>Why (Required to Write It Off)</span><input data-f="why" placeholder="e.g. under $50; the vendor will not credit glass breakage"></label>`,
    {
      submit: "Close the Claim",
      onSubmit: (f) => {
        const how = f.how || "credit",
          why = String(f.why || "").trim(),
          amount = +f.amount || 0;
        if ("writeoff" === how && !why) return "function" == typeof vfMark && vfMark(m.querySelector('[data-f="why"]'), "Say why it is written off"), !1;
        if ("credit" === how && !(amount > 0)) return "function" == typeof vfMark && vfMark(m.querySelector('[data-f="amount"]'), "How much was credited"), !1;
        puClaimClose(po, c, { how: how, amount: "credit" === how ? amount : 0, why: why });
        save(), render();
        toast(`${po.number}: the ${c.type} claim is closed${"credit" === how ? `, ${money(amount)} credited` : "replaced" === how ? "; receive the replacement on the sheet" : ", written off"}`, { label: "Open", run: () => flowGo.po(po)() });
      },
    },
  );
  return m;
}
function puChasePaper(v, kind) {
  if (!v) return;
  if ("function" != typeof eaNudge) return puVendorOpen(v);
  const r = "coi" === kind && PRED.vendorsCoiLapsing && PRED.vendorsCoiLapsing.row(v);
  if (r && "function" == typeof coiChaseItem) return void eaNudge(coiChaseItem(r));
  const open = (DB.pos || []).filter((po) => po.vendor === v.name && puLive(po)),
    need = open.map((po) => po.needBy || po.expected).filter(Boolean).sort()[0] || "",
    by = need && need > today() ? ("function" == typeof addWork ? addWork(need, -2) : need) : "function" == typeof addWork ? addWork(today(), 3, !1) : today(),
    byW = "function" == typeof fmtL ? fmtL(by) : fmt(by),
    lapsed = v.insuranceExp && v.insuranceExp < today();
  if ("w9" === kind)
    return void eaNudge({ kind: "w9", n: "W-9", t: `${esc(v.name)} — W-9`, sub: "before the next payment", vendor: v, subject: `W-9 for ${v.name}`,
      msg: `Hi — we need a signed W-9 for ${v.name} before we can release the next payment. Could you send it by ${byW}? Thanks.` });
  eaNudge({ kind: "coi", n: "!COI", t: `${esc(v.name)} — insurance ${lapsed ? "expired " + fmt(v.insuranceExp) : "not on file"}`, sub: "no new order until it arrives", vendor: v,
    msg: `Hi — ${lapsed ? `the certificate of insurance we have for ${v.name} expired ${fmtL(v.insuranceExp)}` : `we do not have a certificate of insurance on file for ${v.name}`}${open.length ? `, and ${open.map((po) => po.number).join(", ")} ${1 === open.length ? "is" : "are"} open with you` : ""}. Could you send a current one by ${byW}, with SmartDesign named as certificate holder? Thanks.` });
}
function puPlus(v, what) {
  if ("restock" === what) {
    const low = (DB.inventory || []).filter((i) => "tool" !== i.type && puReorder(i) > 0 && invAvailable(i) <= puReorder(i));
    if (!low.length) return toast("Nothing is at its reorder point");
    return puRestockSheet(low);
  }
}
// Restock the Warehouse: the sheet offered only Cancel. Its action is the restock order: a draft purchase order for the
// firm's own stock (no job: overhead, shipped to the warehouse), numbered like every PO (nextPO), one line per stock item
// with the quantity to buy and the last cost, each line linked to its stock item (invId) so receiving it can restock the
// shelf. The vendor is picked from the vendors on file (an unknown name is not created here); the draft is issued from
// the order like any other, so the order's own checks (insurance, W-9, approval over the limit) apply.
function puRestockSheet(low) {
  const V = (DB.vendors || []).slice().sort((a, b) => String(a.name).localeCompare(String(b.name))),
    want = (i) => Math.max(1, r2(puReorder(i) * 2 - invAvailable(i)));
  const m = mbModal(
    "Restock the Warehouse",
    `<p class="small muted" style="margin:0 0 8px">At or under the reorder point. Draft one order for what to buy; it waits as a draft for you to check and issue.</p>${low.map((i) => `<label class="pu-rq"><span data-nocase><b>${esc(i.name)}</b><span class="small muted">${puUnits(invAvailable(i), i.unit)} at the ${esc(String(locName(i.loc)).toLowerCase())} · reorder at ${puUnits(puReorder(i), i.unit)}</span></span><input type="number" inputmode="decimal" min="0" step="any" data-purs="${esc(i.id)}" value="${want(i)}" aria-label="${esc(i.name)}: how many to buy (${esc(i.unit || "")})"></label>`).join("")}<label class="f"><span>Vendor</span><select data-f="vendor" data-pursv="1"><option value="">Choose the vendor…</option>${V.map((v) => `<option value="${esc(v.name)}">${esc(v.name)}</option>`).join("")}</select></label>`,
    {
      submit: "Draft the Restock Order",
      onSubmit: () => {
        const vendor = (m.querySelector("[data-pursv]") || {}).value || "";
        if (!vendor) {
          const s = m.querySelector("[data-pursv]");
          return s && "function" == typeof vfMark ? vfMark(s, "Choose who to buy it from") : toast("Choose who to buy it from"), !1;
        }
        const lines = low
          .map((i) => ({ i: i, q: Math.max(0, +((m.querySelector(`[data-purs="${i.id}"]`) || {}).value || 0)) }))
          .filter((x) => x.q > 0)
          .map(({ i, q }) => ({ id: uid("pl"), item: i.name, desc: "Warehouse stock", qty: q, unit: i.unit || "ea", price: +i.cost || 0, materialId: "", invId: i.id, code: i.code || "", line: "", received: 0 }));
        if (!lines.length) return toast("Nothing to buy: every quantity is 0"), !1;
        const v = (DB.vendors || []).find((x) => x.name === vendor),
          po = { id: uid("po"), number: nextPO(), projectId: "", vendor: vendor, vendorId: v ? v.id : "", date: today(), expected: "", needBy: "", status: "draft", shipTo: "Warehouse", notes: `Restock: ${lines.length} stock item${1 === lines.length ? "" : "s"} at or under the reorder point`, lines: lines, tax: 0, shipping: 0, matchedTxns: [], createdBy: ((currentUser() || {}).name) || role(), restock: !0 };
        DB.pos.push(po);
        try {
          audit("po", po.id, "created", null, { number: po.number, vendor: vendor, from: "restock", items: lines.map((l) => `${l.qty} ${l.unit} ${l.item}`).join("; ") });
        } catch (e) {}
        try {
          log(`${po.number} drafted to restock the warehouse from ${vendor}: ${lines.map((l) => `${l.qty} ${l.unit} ${l.item}`).join(", ")}`);
        } catch (e) {}
        save(), render();
        toast(`${po.number} drafted for ${vendor} — ${lines.length} stock item${1 === lines.length ? "" : "s"}, ${money(poTotal(po).total)}. Check it and issue it`, { label: "Open", run: () => ((poOpen = po.id), setView("po")) });
      },
    },
  );
  return m;
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
// One receipt, as the old Deliveries page writes it (its helper lives inside renderRecv), with the material read on the
// order's own job, not the job on screen: every line that came, in one receipt row and one audit row. Every receiving
// path writes through here (the receive sheet, the desktop's line cards, the Selections box, a slip read from a file),
// so the cap is here: no line is received past what is still to come on it (the CoS, 11-06: 1,000 sf received on a
// 900 sf line). What is over is returned in `capped`, never written; a caller that can ask the person refuses first.
function puReceiveLines(po, got, note, slip) {
  const p = (DB.projects || []).find((x) => x.id === po.projectId),
    left = (l) => Math.max(0, r2((+l.qty || 0) - (+l.received || 0))),
    capped = [],
    ok = [];
  (got || []).forEach(({ l, q }) => {
    const want = r2(+q || 0),
      take = Math.min(want, left(l));
    want > take + 0.001 && capped.push({ l: l, asked: want, left: left(l) });
    take > 0 && ok.push({ l: l, q: take });
  });
  if (!ok.length) return { full: !1, capped: capped, got: ok };
  ok.forEach(({ l, q }) => {
    l.received = r2((+l.received || 0) + q);
    const m = l.materialId && p && (p.materials || []).find((x) => x.id === l.materialId);
    m && l.received >= (+l.qty || 0) - 0.001 && ((m.status = "on-site"), (m.onSiteDate = m.onSiteDate || today()));
    // a restock order's line puts what came on the shelf it was bought for
    const iv = l.invId && (DB.inventory || []).find((x) => x.id === l.invId);
    iv && (iv.qty = r2((+iv.qty || 0) + q));
  });
  const full = po.lines.every((x) => (+x.received || 0) >= (+x.qty || 0) - 0.001);
  (po.status = full ? "received" : "partial"), full && (po.receivedOn = today());
  (po.receipts = po.receipts || []).push({ date: today(), t: nowStamp(), by: ((currentUser() || {}).name) || role(), lines: ok.map(({ l, q }) => ({ lineId: l.id, item: l.item || l.desc || "", unit: l.unit || "", qty: q })), slip: slip || "", note: note || "" });
  try {
    audit("po", po.id, "received", "", ok.map(({ l, q }) => `${l.item || l.desc}: ${q}`).join("; "), note || "");
  } catch (e) {}
  try {
    log(`${po.number}: received ${ok.map(({ l, q }) => `${q} ${l.unit || ""} ${l.item || l.desc || ""}`.replace(/\s+/g, " ")).join(", ")}${note ? " — " + note : ""}`);
  } catch (e) {}
  return { full: full, capped: capped, got: ok };
}
const puReceiveLeft = (l) => Math.max(0, r2((+l.qty || 0) - (+l.received || 0)));
// The one receive sheet (BACKLOG 1.36), however receiving starts: the phone's Deliveries (Receive), the order's Receive
// Some…, the foreman's It Arrived on Site and Check In on Today (rcReceiveSome opens this one). Receiving counts what
// came: every count starts empty, what is still to come is only the hint, and a line left empty records nothing. A count
// over what is still to come is refused: what was not ordered is not received onto the order. A photo of the slip.
// Condition is per line (the coordinator's day, S1: one choice for the whole delivery put the damage claim on the good
// studs and no claim on the short): Good, Short, Damaged or Wrong on each line. Short claims what did not come; Damaged
// and Wrong ask how many and claim those. Only the good quantity is received, so Bill What Arrived bills only what can
// be used, and each claim holds the difference against the vendor on its own line.
function puReceive(po) {
  if (!po) return;
  const left = (l) => Math.max(0, r2((+l.qty || 0) - (+l.received || 0))),
    L = (po.lines || []).filter((l) => left(l) > 0);
  if ("function" == typeof poIsSub && poIsSub(po)) return void toast(poSubWords(po));
  if (!L.length) return void toast(`${po.number} has nothing left to receive`);
  const field = ["foreman", "crew", "driver"].includes(role()),
    early = po.expected && "function" == typeof workdays && po.expected > today() ? workdays(today(), po.expected) - 1 : 0;
  const cond = {},
    CONDS = [["good", "Good"], ["short", "Short"], ["damaged", "Damaged"], ["wrong", "Wrong"]];
  L.forEach((l) => (cond[l.id] = "good"));
  const lineHtml = (l) => {
    const item = esc(l.item || l.desc || "Line"),
      u = esc(l.unit || "");
    return `<div class="pu-rql" data-purl="${esc(l.id)}"><label class="pu-rq"><span data-nocase><b>${item}</b><span class="small muted">${r2(+l.received || 0)} of ${r2(+l.qty || 0)} ${u} in · ${left(l)} to come</span></span><input type="number" inputmode="decimal" min="0" step="any" data-purq="${esc(l.id)}" data-f="q_${esc(l.id)}" value="" placeholder="${left(l)} to come" aria-label="${item}: how many arrived (${left(l)} ${u} still to come)"></label><div class="pu-conds" role="radiogroup" aria-label="Condition of ${item}"><button type="button" class="pu-chip" data-puall="${esc(l.id)}" data-left="${left(l)}">All Here</button>${CONDS.map(([k, w]) => `<button type="button" class="pu-chip ${"good" === k ? "on" : ""}" data-pucond="${k}" data-pul="${esc(l.id)}" aria-pressed="${"good" === k}">${w}</button>`).join("")}</div><label class="pu-rq pu-bad" data-pubadw="${esc(l.id)}" hidden><span>${puLotLine(l) ? `<b>How Many Pieces Are Short, Damaged or Wrong</b><span class="small muted">the ${u} came; the pieces of it that did not, or came broken, are claimed at the vendor's quoted price</span>` : `<b>How Many Are Damaged or Wrong</b><span class="small muted">of the ${u || "ones"} that came; they are claimed, not received</span>`}</span><input type="number" inputmode="decimal" min="0" step="any" data-pubad="${esc(l.id)}" value="" aria-label="${item}: how many are damaged or wrong"></label></div>`;
  };
  const m = mbModal(
    `Receive Some — <span data-nocase>${esc(po.number)}</span>`,
    `<p class="small muted" style="margin:0 0 10px" data-nocase>${esc(po.vendor)} · ${esc(puJob(DB.projects.find((p) => p.id === po.projectId)))}. Count what is really here; leave a line empty if none of it came. Mark each line's condition.</p>${early > 3 ? `<p class="note warn pu-early" style="margin:0 0 10px">${esc(po.vendor)} promised this for ${fmt(po.expected)}, ${early} working days from now. Check the slip says ${esc(po.number)} before you count it in.</p>` : ""}${L.map(lineHtml).join("")}<label class="f"><span>Photo of the Slip${field ? "" : ' <span class="muted">(optional)</span>'}</span><input type="file" accept="image/*" capture="environment" data-puslip="1"></label><label class="f"><span>Note</span><input data-punote="1" data-f="note" placeholder="What is short, damaged or wrong; the slip number"></label>`,
    {
      submit: "Record Receipt",
      onSubmit: () => {
        const mark = (i, msg) => (i && "function" == typeof vfMark ? vfMark(i, msg) : toast(msg), !1),
          rows = L.map((l) => {
            const i = m.querySelector(`[data-purq="${l.id}"]`),
              bi = m.querySelector(`[data-pubad="${l.id}"]`);
            return { l: l, i: i, bi: bi, k: cond[l.id] || "good", raw: String((i && i.value) || "").trim(), badRaw: String((bi && bi.value) || "").trim() };
          });
        // a line marked Short, Damaged or Wrong needs its count (0 when none of it came)
        const sl = m.querySelector("[data-puslip]");
        if (field && !(sl && sl.files && sl.files.length)) return mark(sl, "Take a photo of the packing slip first");
        const unCounted = rows.find((x) => "good" !== x.k && "" === x.raw);
        if (unCounted) return mark(unCounted.i, "Count what arrived on this line (0 if none of it came)");
        const R = rows.filter((x) => "" !== x.raw);
        if (!R.length) return mark(m.querySelector("[data-purq]"), "Count what arrived (0 if none of it came)");
        const over = R.find((x) => +x.raw > left(x.l) + 0.001);
        if (over) return mark(over.i, `Only ${left(over.l)} ${over.l.unit || ""} are still to come: the rest goes back, or onto a change to the order`);
        // a lump-sum line (1 ls) that came whole with pieces of it short, damaged or wrong: the lot is received and the
        // pieces are claimed (the walk's J7: 6 cement boards short on the 1 ls drywall line could not be said here)
        const pieces = (x) => puLotLine(x.l) && "good" !== x.k && Math.max(0, +x.raw || 0) >= left(x.l) - 0.001;
        for (const x of R) {
          const c = Math.max(0, +x.raw || 0);
          if (pieces(x)) {
            if ("" === x.badRaw || !(+x.badRaw > 0)) return mark(x.bi, `How many pieces of the ${x.l.unit || "lot"} are ${x.k}?`);
            continue;
          }
          if ("short" === x.k && c >= left(x.l) - 0.001) return mark(x.i, `Nothing is short: ${c} is everything still to come`);
          if (["damaged", "wrong"].includes(x.k)) {
            const bad = +x.badRaw;
            if ("" === x.badRaw || !(bad > 0)) return mark(x.bi, `How many are ${x.k}?`);
            if (bad > c + 0.001) return mark(x.bi, `Only ${c} came: count the ${x.k} among them`);
          }
        }
        const note = String((m.querySelector("[data-punote]") || {}).value || "").trim(),
          slip = m.querySelector("[data-puslip]"),
          slipName = slip && slip.files && slip.files[0] ? slip.files[0].name : "",
          claims = [],
          came = [];
        R.forEach((x) => {
          if (pieces(x)) {
            came.push({ l: x.l, q: Math.max(0, +x.raw || 0) });
            return void claims.push({ l: x.l, type: x.k, qty: +x.badRaw, pieces: !0 });
          }
          const c = Math.max(0, +x.raw || 0),
            bad = ["damaged", "wrong"].includes(x.k) ? +x.badRaw || 0 : 0,
            good = r2(c - bad),
            q = "short" === x.k ? r2(left(x.l) - c) : bad;
          good > 0 && came.push({ l: x.l, q: good });
          "good" !== x.k && q > 0 && claims.push({ l: x.l, type: x.k, qty: q });
        });
        if (!came.length && !claims.length) return mark(R[0].i, "Nothing is counted as arrived: type what came, or mark the line Short");
        const full = came.length ? puReceiveLines(po, came, note, slipName).full : !1;
        slipName && (po.slips = (po.slips || []).concat([{ at: appNowIso(), name: slipName }]));
        // one claim per line and kind, on its own line: what did not come, or what came damaged or wrong
        claims.forEach((k) => {
          const claim = { t: nowStamp(), at: appNowIso(), by: ((currentUser() || {}).name) || role(), type: k.type, lineId: k.l.id, item: k.l.item || k.l.desc || "", qty: k.qty, unit: k.l.unit || "", amount: r2(k.qty * (+k.l.price || 0)), note: note, claim: !0, status: "open" };
          // a lump-sum line's claim is priced from the vendor's quoted piece, never a count at the lot's price
          "function" == typeof puClaimAmount && Object.assign(claim, puClaimAmount(po, k.l, k.qty, note));
          k.pieces && ((claim.unit = "pc"), (claim.of = k.l.unit || ""));
          k.amount = claim.amount;
          (po.issues = po.issues || []).push(claim);
          k.l.issue = k.type;
          try {
            audit("po", po.id, "delivery-claim", "", k.type, `${k.qty} ${k.l.unit || ""} ${k.l.item}`.replace(/\s+/g, " "));
          } catch (e) {}
        });
        claims.length && (po.flag = claims.map((k) => `${k.type}: ${k.l.item} ${k.qty}`).join("; "));
        save(), render();
        const amt = r2(came.reduce((a, x) => a + x.q * (+x.l.price || 0), 0)),
          what = full ? "received in full" : came.length ? `${came.length} line${1 === came.length ? "" : "s"} received` : "nothing received",
          held = r2(claims.reduce((a, k) => a + (+k.amount || 0), 0));
        claims.length
          ? toast(`${po.number}: ${what}${amt ? `, ${money(amt)}` : ""}; ${claims.map((k) => `${k.qty} ${k.pieces ? "pieces" : k.l.unit || ""} ${k.type} on ${k.l.item}`.replace(/\s+/g, " ")).join(", ")} claimed from ${po.vendor}${held ? `, ${money(held)} held` : ""}. Every dollar not credited comes out of raises, bonuses and the client's extras.`, { label: "Open", run: () => flowGo.po(po)() }, 9e3)
          : // the receipt's next step is the bill for what came (Bill It), as on the desktop's line-by-line cards
            "function" == typeof rcReceiptToast
            ? rcReceiptToast(po, `${po.number} · ${po.vendor} — ${what}${amt ? `, ${money(amt)}` : ""}`)
            : toast(`${po.number}: ${what}`, { label: "Open", run: () => flowGo.po(po)() });
      },
    },
  );
  m.querySelectorAll("[data-puall]").forEach(
    (b) =>
      (b.onclick = () => {
        const i = m.querySelector(`[data-purq="${b.dataset.puall}"]`);
        i && ((i.value = b.dataset.left), i.dispatchEvent(new Event("input", { bubbles: !0 })));
      }),
  );
  m.querySelectorAll("[data-pucond]").forEach(
    (b) =>
      (b.onclick = () => {
        const id = b.dataset.pul;
        cond[id] = b.dataset.pucond;
        m.querySelectorAll(`[data-pucond][data-pul="${id}"]`).forEach((x) => (x.classList.toggle("on", x === b), x.setAttribute("aria-pressed", String(x === b))));
        const w = m.querySelector(`[data-pubadw="${id}"]`),
          l = L.find((x) => x.id === id);
        w && (w.hidden = !(["damaged", "wrong"].includes(cond[id]) || (l && puLotLine(l) && "short" === cond[id])));
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
    if ((b = at("[data-puplus]"))) return e.preventDefault(), e.stopPropagation(), (puPlusMore = ""), (puPlusOpen = puPlusOpen === b.dataset.puplus ? "" : b.dataset.puplus), render();
    if ((b = at("[data-pumore]"))) return e.preventDefault(), e.stopPropagation(), (puPlusMore = b.dataset.pumore), render();
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
    if ("draftpo" === x.k && (r.draftPOs || [])[0]) return flowGo.po(r.draftPOs[0])();
    if ("route" === x.k) return setView("recv");
    if ("split" === x.k) return puMatSheet(r.lineKey || r.key);
    if ("subm" === x.k) return setCurrent(r.p.id), setView("subm");
    if ("quote" === x.k) return puStockGate([r], () => bbQuote([r]));
    if ("order" === x.k) return puStockGate([r], () => bbOrder([r]));
    return bbDo(r, x.k);
  }
  // a row whose button does something other than open it (Close the Claim) carries actRun; its name still opens it
  return x.actRun ? x.actRun() : x.run && x.run();
}
// The stock check at the door: before money is committed on a need the shelf may cover, the person is asked
// (11-05, the coordinator expert: its blue was Buy It Anyway, with no way to use the stock.) The blue takes what the
// person says from the shelf (a pick for the driver, on the need's job) and buys the rest; a need the shelf covers in
// full is not bought at all. Buy It Anyway stays, second.
function puStockGate(R, go) {
  const S0 = R.flatMap((r) => puStockSure(r).map((s) => Object.assign({ need: r }, s)));
  if (!S0.length) return go();
  const want = (s) => {
    const q = "function" == typeof bbNum ? bbNum(s.need.qty) : { n: 0, unit: "" },
      one = puParts(s.need.name).length <= 1;
    return one && q.n > 0 && (!q.unit || !s.unit || String(q.unit).replace(/s$/, "") === String(s.unit).replace(/s$/, "")) ? Math.min(q.n, s.qty) : "";
  };
  const m = mbModal(
    "Check the Stock First",
    `<p class="small muted" style="margin:0 0 8px">On the shelf now. Say how many to take; the driver picks them for the job, and the order buys the rest.</p>${S0.map((s, i) => `<div class="pu-rq"><span><b data-nocase>${esc(s.name)}</b><span class="small muted" data-nocase>${esc(puUnits(s.qty, s.unit))} at the ${esc(String(s.where).toLowerCase())}, for ${esc(s.need.name)}${s.sure ? "" : " (may be it: check)"}</span></span><input type="number" inputmode="decimal" min="0" max="${s.qty}" step="any" data-pustk="${i}" value="${want(s)}" aria-label="How many to take of ${esc(s.name)}"></div>`).join("")}<p class="small muted" style="margin:8px 0 0">Use what we own before buying: money spent on what is on the shelf cannot go to raises, bonuses, the client or charity.</p>`,
    {
      submit: "Use the Stock, Buy the Rest",
      alt: { label: "Buy It Anyway", run: () => void setTimeout(go, 0) },
      onSubmit: () => {
        const took = [];
        S0.forEach((s, i) => {
          const n = Math.min(+((m.querySelector(`[data-pustk="${i}"]`) || {}).value || 0), s.qty);
          if (!(n > 0)) return;
          const q = "function" == typeof stockTakeForLine ? stockTakeForLine({ projectId: s.need.p.id, invId: s.id, qty: n, unit: s.unit, needBy: s.need.needBy, note: `From stock for ${s.need.name}` }) : null;
          q && took.push({ s: s, n: n, q: q });
        });
        if (!took.length) return toast("Say how many to take, or tap Buy It Anyway"), !1;
        // a need the shelf covers in full is not bought: its request goes the stock path (it leaves the store run)
        const full = R.filter((r) => {
          const q = "function" == typeof bbNum ? bbNum(r.qty) : { n: 0 },
            got = took.filter((t) => t.s.need === r).reduce((a, t) => a + t.n, 0);
          return puParts(r.name).length <= 1 && q.n > 0 && got >= q.n;
        });
        full.forEach((r) => {
          try {
            r.q && "function" == typeof bbReqPath ? bbReqPath(r.p, r.q, "stock", "taken from stock") : r.m && "on-site" !== r.m.status && ((r.m.status = "ordered"), (r.m.notes = `${r.m.notes ? r.m.notes + " · " : ""}taken from stock`));
            r.q && r.q.status === "new" && ((r.q.status = "ack"), (r.q.ackAt = appNowIso()));
          } catch (e) {}
        });
        save();
        const rest = R.filter((r) => !full.includes(r));
        rcToast(`${took.map((t) => `${puUnits(t.n, t.s.unit)} ${t.s.name}`).join(", ")} from stock: a pick for the driver${rest.length ? "; now the order for the rest" : ""}`, [{ label: "Open", run: () => setView("recv") }]);
        rest.length && setTimeout(go, 0);
        render();
      },
    },
  );
  return m;
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
    puStockGate(R, () => (R.forEach((r) => (r.__puChecked = 1)), (out = puQuoteDoor(R) || bq.apply(self, args)), R.forEach((r) => delete r.__puChecked)));
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
    Object.defineProperty(MN_ALIAS, "ovbuy", { configurable: !0, enumerable: !0, get: () => puHomeView() });
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
// a page's sections (Needs You, Waiting on Someone Else, Later) group records; they are not records (the phone row pass
// and tests/phone_rows_lint.py read them as sections, as the old board's bb-sec)
"undefined" != typeof PR_SECTIONS && !PR_SECTIONS.includes("pu-sec") && PR_SECTIONS.push("pu-sec");
// A promise later than the need date reaches the PM the day it is known (decision 3, 11-03): a card on his Today, on his
// jobs, with Move the Task (the schedule is his) and the job's Purchasing one tap away. The coordinator expedites it from
// Deliveries; the PM decides whether the work waits. It is its own card, not a Buy Board line, so the Buy Board's
// number stays its Needs You.
function puLatePromises(pm) {
  const me = String(((currentUser() || {}).name) || "").toLowerCase().split(" ")[0];
  return buyList("")
    .filter((r) => r.ordered && r.po && "promise" === r.lateKind && !r.received)
    .filter((r) => !pm || !r.p.project.pm || String(r.p.project.pm).toLowerCase().includes(me));
}
if ("function" == typeof tdyModel) {
  const base = tdyModel;
  tdyModel = function () {
    const M = base.apply(this, arguments);
    try {
      if ("pm" !== role()) return M;
      const L = puLatePromises(!0).map((r) => ({
        kind: "tdyPromise",
        id: "promise:" + r.id,
        src: "purchasing",
        r: r,
        title: `${r.name}: promised ${fmt(r.eta)}, needed ${fmt(r.needBy)}`,
        detail: `${puJob(r.p)} · ${r.po.number} from ${r.po.vendor}${r.task ? ` · ${r.task.name} starts ${fmt(r.task.start)}` : ""}. The coordinator is expediting; move the task, or keep it and hold the crew`,
        due: r.needBy,
        urgency: 1,
      }));
      L.length && (M.all = (M.all || []).concat(L));
      M.promise = L;
    } catch (e) {
      console.warn("late promise on Today", e);
    }
    return M;
  };
}
// The late promise is its own thing on Today (a part of the model, M.promise, beside the approvals, the inbox, the tasks,
// the orders and the minutes): a supplier's date the PM decides about, which is neither a Buy Board need (it is
// ordered) nor an approval. Each is listed once; it ranks with the work the site waits on.
"function" == typeof tdScore &&
  (() => {
    const base = tdScore;
    tdScore = function (it) {
      return it && "tdyPromise" === it.kind ? 40 : base.apply(this, arguments);
    };
  })();
if ("function" == typeof tdCard) {
  const base = tdCard;
  tdCard = function (it) {
    const c = base.apply(this, arguments);
    try {
      if (it && "tdyPromise" === it.kind) {
        const r = it.r;
        (c.line1 = esc(it.title)), (c.why = esc(it.detail)), (c.verb = "Move the Task"), (c.run = () => bbMoveTask(r)), (c.go = () => jpOpenJob(r.p.id, "proc"));
      }
    } catch (e) {}
    return c;
  };
}
// The demo's 121 State Street materials, seeded with no line, are linked to the estimate and change-order lines they
// are bought for (invented demo data, read off EST-2026-014 and CO-2026-001; each id is checked against its name, and
// a firm's own data, with the seeds off, is never touched). The plumbing, electrical and exterior materials sit on lines a
// sub holds (Alberto, Satish, the exterior scaffold): whose they are is the coordinator's to say with the picker. Shower
// glass, the parlor kitchen's appliances and the
// washer/dryer are on no line of the contract: they say so.
const PU_DEMO_LINES = {
  m2: ["Framing", "estimate:es1:l2"], m4: ["Insulation", "estimate:es1:l6"],
  m5: ["GWB", "estimate:es1:l6"], m6: ["Radiant heat mats", "co:co1:l1"], m7: ["Waterproofing", "estimate:es1:l7"],
  m8: ["Tile", "estimate:es1:l7"], m9: ["Tile", "estimate:es1:l7"], m10: ["White oak", "estimate:es1:l8"],
  m11: ["LVP", "estimate:es1:l8"], m12: ["Interior doors", "estimate:es1:l10"], m13: ["Base molding", "estimate:es1:l10"],
  m14: ["Interior paint", "estimate:es1:l10"],
  m19: ["Parlor kitchen countertop", "estimate:es1:l9"],
  m20: ["Garden kitchen countertop", "estimate:es1:l9"], m22: ["Door hardware", "estimate:es1:l10"], m23: ["Stair runner", "estimate:es1:l8"],
};
function puDemoLines() {
  if (!DB || DB.__puLines || ("function" == typeof sdSeedsOff && sdSeedsOff())) return;
  const p = (DB.projects || []).find((x) => "p121" === x.id);
  if (!p || "function" != typeof findLine) return;
  DB.__puLines = 1;
  (p.materials || []).forEach((m) => {
    const L = PU_DEMO_LINES[m.id];
    L && !m.line && String(m.name).toLowerCase().startsWith(L[0].toLowerCase()) && findLine(L[1]) && (m.line = L[1]);
  });
  save();
}
// A blank need asks for its line before it is saved (one picker: the job's estimate and change-order lines), or for why
// there is none; it is a material on the job, on the Buy Board at once
function puNewNeed() {
  const P = (DB.projects || []).filter((p) => p.project && "function" == typeof rfqLineSources);
  const pid = (S && P.some((p) => p.id === S.id) && S.id) || (P[0] && P[0].id);
  if (!pid) return toast("Open a job to add a need");
  const opts = (j) => rfqLineSources(j).filter((s) => /^(estimate|co):/.test(s.key)).map((s) => `<option value="${esc(s.key)}">${esc(`${s.docNo} · ${s.item}`)}</option>`).join("");
  const m = mbModal(
    "Blank Need",
    `<p class="small muted" style="margin:0 0 8px">Only when no line covers it. Name the line it is bought for; with none, say why, and the PM sees it as cost on no line.</p><label class="f"><span>Job</span><select id="pu-nj">${P.map((p) => `<option value="${esc(p.id)}" ${p.id === pid ? "selected" : ""}>${esc(puJob(p))}</option>`).join("")}</select></label><label class="f"><span>What</span><input id="pu-nw" placeholder="What has to be bought"></label><label class="f"><span>Quantity</span><input id="pu-nq" inputmode="decimal" placeholder="e.g. 12 sheets"></label><label class="f"><span>Estimate Line</span><select id="pu-nl"><option value="">Pick the line it is bought for</option>${opts(pid)}<option value="__none">No line covers it</option></select></label><label class="f"><span>Why No Line</span><input id="pu-nwhy" placeholder="Only when no line covers it"></label>`,
    {
      submit: "Add the Need",
      onSubmit: () => {
        const j = m.querySelector("#pu-nj").value,
          what = m.querySelector("#pu-nw").value.trim(),
          line = m.querySelector("#pu-nl").value,
          why = m.querySelector("#pu-nwhy").value.trim(),
          p = (DB.projects || []).find((x) => x.id === j);
        if (!what) return toast("Say what has to be bought"), !1;
        if (!line) return toast("Pick the estimate line it is bought for, or No line covers it"), !1;
        if ("__none" === line && !why) return toast("Say why no line covers it"), !1;
        const mm = { id: uid("m"), name: what, cat: "finish", taskId: "", lead: 5, when: "start", status: "not-ordered", eta: "", vendor: "", po: "", qty: m.querySelector("#pu-nq").value.trim(), cost: 0, deliverTo: "site", notes: "__none" === line ? `No estimate line: ${why}` : "", line: "__none" === line ? "" : line };
        (p.materials = p.materials || []).push(mm);
        try {
          audit("material", mm.id, "need added", "", mm.line || "no line", why);
        } catch (e) {}
        save(), render();
        toast(`${what} is on the Buy Board for ${puJob(p)}${mm.line ? "" : ", on no estimate line"}`, { label: "Open", run: () => ((bbProj = ""), setView("proc")) });
      },
    },
  );
  const js = m.querySelector("#pu-nj");
  js && (js.onchange = () => (m.querySelector("#pu-nl").innerHTML = `<option value="">Pick the line it is bought for</option>${opts(js.value)}<option value="__none">No line covers it</option>`));
  return m;
}
// the old Purchasing overview opens the role's first Purchasing page
{
  const base = render;
  render = function () {
    if ("ovbuy" === view) view = puHomeView();
    const r = base.apply(this, arguments);
    try {
      puDemoLines(), puDraw(), puCrumbs(), puDocDecorate(), puFfeCrumb();
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
    if ("finish" === procMode || "board" !== pane) {
      const out = base.apply(this, arguments);
      try {
        puFfeDress(document.getElementById("proc-body"));
      } catch (e) {}
      return out;
    }
    try {
      return puBuyRender();
    } catch (e) {
      console.warn("buy board", e);
      return base.apply(this, arguments);
    }
  };
}

// ---- one status per need (11-05): Today, the Buy Board, Quotes and Deliveries read puNeedStatus -----------------------
// The quote stage of a need: lane P4's rfqLineState when it is there, else the request's own status. A draft request is the
// coordinator's to send (it read "Waiting on 1 vendors"); an awarded one is not a quote any more.
function puQuoteStage(r) {
  const key = r && (r.lineKey || r.key);
  if (key && "function" == typeof rfqLineState) {
    try {
      const s = rfqLineState(key);
      if (s && s.stage && "awarded" !== s.stage) return s;
      if (s && "awarded" === s.stage) return null;
    } catch (e) {}
  }
  const q = ((r && r.rfqs) || [])[0];
  if (!q) return null;
  const st = q.status,
    nq = (q.quotes || []).filter((x) => !x.unreadable).length,
    nv = (q.vendors || []).length;
  return { stage: "draft" === st ? "draft" : "foreman-review" === st ? "foreman" : "purchasing" === st ? "pick" : ["leveled", "negotiating"].includes(st) || (nv && nq >= nv) ? "leveled" : (q.quotes || []).some((x) => x.unreadable) ? "price-needed" : "out", rfq: q, label: (("undefined" != typeof RFQ_STATUS && RFQ_STATUS[st]) || st) };
}
function puQuoteStep(r) {
  const s = puQuoteStage(r) || { stage: "out", rfq: (r.rfqs || [])[0] || {} },
    q = s.rfq || {},
    n = q.number || "The request",
    nv = (q.vendors || []).length,
    base = { act: "Open the Request", k: "rfq" };
  if ("draft" === s.stage) return Object.assign(base, { actor: "coord", why: `${n} is a draft: add the vendors and send it.` });
  if ("pick" === s.stage) return Object.assign(base, { actor: "coord", why: `${n}: pick the vendors and send it.` });
  if ("foreman" === s.stage) return Object.assign(base, { actor: "foreman", who: q.foreman || "the foreman", why: `checks the quantities on ${n}.` });
  if ("price-needed" === s.stage) return Object.assign(base, { actor: "coord", why: `${n}: a reply is in that needs its prices entered.` });
  if ("leveled" === s.stage) return Object.assign(base, { actor: "coord", why: `${n}: the quotes are in; level and award.`, act: "Open the Quotes" });
  return Object.assign(base, { actor: "vendor", who: nv ? `${nv} vendor${1 === nv ? "" : "s"}` : "the vendors", why: `${n}: quotes due ${q.dueDate ? fmt(q.dueDate) : "soon"}.` });
}
// The one status of a need (a buyList row): its bucket (mine, others, later, route, gone), whose tap it is, why, and the
// next step. Lane P4 reads it for Quotes, P1 for Deliveries; Today's Buy Board cards read it below.
function puNeedStatus(r) {
  const x = puNeed(r);
  return x ? { b: x.b, actor: x.actor, who: x.who || "", why: x.why, act: x.act, k: x.k, tone: x.tone || "", when: x.when } : null;
}
// The status of the open need on a contract line (or null when nothing on the line is left to buy)
function puNeedStatusFor(lineKey) {
  const r = buyList("").find((x) => (x.lineKey === lineKey || x.key === lineKey) && !x.received && !(x.ordered && x.po));
  return r ? puNeedStatus(r) : null;
}
// Today's Buy Board card says what the board says (11-05: "Ask for Bids" after the award), and does what its row does
if ("function" == typeof bbTodayCard) {
  const base = bbTodayCard;
  bbTodayCard = function (it) {
    const c = base.apply(this, arguments);
    try {
      const x = it && it.x && puNeed(it.x);
      // the card leads with the date it is due by (Order by 9/1, passed), then the reason, as the row says both: the card's
      // line is cut to a few words, and the date is what Today ranks by
      x && x.act && ((c.verb = x.act), (c.run = () => puDo(x)), (c.why = esc(`Buy Board · ${x.when ? `${x.when}. ` : ""}${x.why}`)));
    } catch (e) {}
    return c;
  };
}
// Ask for Quotes on the Buy Board opens the request sheet (lane P4's rfqStartFromLines) prefilled from the picked lines;
// until it is there, the request is made as before
function puQuoteDoor(R) {
  if ("function" != typeof rfqStartFromLines || !R.length) return null;
  if (new Set(R.map((r) => r.p.id)).size > 1 || R.some((r) => "request" === r.kind)) return null;
  const items = R.map((r) => ("ffe" === r.kind && r.it ? "sel:" + r.it.id : r.m ? (r.lineKey ? { key: r.lineKey, materialId: r.m.id } : null) : r.lineKey || null));
  if (items.some((i) => !i)) return null;
  const subs = R.filter((r) => "sub" === r.kind);
  if (subs.length && subs.length !== R.length) return null;
  const category = subs.length ? (((("undefined" != typeof COST_CODES && COST_CODES.find((c) => c[0] === subs[0].code)) || [])[1]) || "Subcontract").split(/[ &,]/)[0] : void 0;
  bbPick.clear();
  return rfqStartFromLines(items, { pid: R[0].p.id, sub: !!subs.length, category: category }) || !0;
}
// The best price known for a need's item, from the one price history (itemPriceHistory: our orders, bills, receipts and
// quotes), read per part of its name (11-05: the studs read "no buys on file" while Price Watch had four stores)
function puBookPrice(r) {
  if (!r || "function" != typeof itemPriceHistory || ["sub", "line"].includes(r.kind)) return null;
  const k = "pb|" + r.id + "|" + ("function" == typeof dataVer ? dataVer() : "");
  puBookPrice.memo = puBookPrice.memo || new Map();
  if (puBookPrice.memo.has(k)) return puBookPrice.memo.get(k);
  let out = null;
  for (const part of puParts(String(r.name || "").replace(/^\d+\.\s*/, ""))) {
    let H = null;
    try {
      H = itemPriceHistory(part);
    } catch (e) {}
    if (H && H.best && +H.best.price > 0) {
      out = { label: H.label, unit: H.unit || "", price: +H.best.price, vendor: H.best.vendor || "", date: H.best.date || "", say: `${unitMoney(H.best.price)}/${H.unit || "ea"} at ${H.best.vendor || "a store"}${H.best.date ? `, ${fmt(H.best.date)}` : ""} (${H.label})` };
      break;
    }
  }
  puBookPrice.memo.size > 400 && puBookPrice.memo.clear();
  return puBookPrice.memo.set(k, out), out;
}
// The best price known for a name typed or read on the order sheet (the item, or the request the order covers)
function puBestFor(name, unit) {
  if ("function" != typeof itemPriceHistory) return null;
  for (const part of puParts(name)) {
    let H = null;
    try {
      H = itemPriceHistory(part);
    } catch (e) {}
    if (!H || !H.best || !(+H.best.price > 0)) continue;
    const u = (x) => String(x || "").toLowerCase().replace(/s$/, "");
    if (unit && H.unit && u(unit) !== u(H.unit) && !["ls", "lot"].includes(u(unit))) continue;
    if (["ls", "lot"].includes(u(unit))) continue;
    return { label: H.label, unit: H.unit, price: +H.best.price, vendor: H.best.vendor || "", date: H.best.date || "" };
  }
  return null;
}

// ---- the job's Orders: lines spent and ordered past their budget (the one budget test, lineCommitment) ---------------
// A draft that puts its line over is the coordinator's (Needs You); a line already over with nothing drafted is shown on
// the tile only (it is the PM's change order or reason, and Over the Order already carries a paid overrun).
function puLineOverRows(pid) {
  if ("function" != typeof lineCommitment) return [];
  const keys = new Set();
  (DB.pos || []).filter((po) => "cancelled" !== po.status && (!pid || po.projectId === pid)).forEach((po) => (po.lines || []).forEach((l) => l.line && keys.add(l.line)));
  const out = [];
  keys.forEach((k) => {
    const c = lineCommitment(k);
    if (!c || !(c.budget > 0) || !(c.over > Math.max(1, 0.001 * c.budget))) return;
    let ref = null;
    try {
      ref = findLine(k);
    } catch (e) {}
    if (!ref) return;
    "function" == typeof ctNumber && ctNumber(ref.doc);
    const p = (DB.projects || []).find((x) => x.id === ref.doc.projectId) || null,
      draft = c.drafts[0] || null;
    out.push({
      id: "lineover:" + k,
      name: `${ref.doc.number}${ref.line.num ? ` line ${ref.line.num}` : ""}: ${money(c.over)} over its budget`,
      job: puJob(p),
      line: `${ref.line.item || ref.line.desc || ""} · budget ${money(c.budget)} · spent ${money(c.actual)} · on order ${money(c.onOrder)}${c.drafted ? ` (${money(c.drafted)} in draft ${c.drafts.map((po) => po.number).join(", ")})` : ""}`,
      why: draft ? `Draft ${draft.number} puts the line over. Cut it to what is left, or issue it with a reason.` : "Spent and ordered past the line's budget: a change order, or the reason it is absorbed.",
      act: draft ? "Open the Draft" : "Open the Line",
      run: draft ? () => flowGo.po(draft)() : () => ("function" == typeof finLineModal ? finLineModal(k) : null),
      tone: "bad",
      money: c.over,
      tile: "lineover",
      actor: draft ? "coord" : "tile",
    });
  });
  return out;
}

// ---- Set the Material Portion: one field, the PM's (11-05: it opened the Budget page, which has no split field) --------
function puMatSheet(key) {
  let ref = null;
  try {
    ref = key ? findLine(key) : null;
  } catch (e) {}
  if (!ref) return toast("This need is on no contract line yet: link it to a line first");
  const name = `${ref.doc.number}${ref.line.num ? ` line ${ref.line.num}` : ""} · ${ref.line.item || ref.line.desc || ""}`;
  if (!["owner", "pm"].includes(role())) {
    ref.line.matAsk = { by: ((currentUser() || {}).name) || role(), at: appNowIso() };
    save(), render();
    return toast(`Asked the PM to set the material portion of ${name}: it is in his Approvals`, { label: "Open", run: () => setView("proc") });
  }
  const M = "function" == typeof rfqMatBudget ? rfqMatBudget(key, ref.line, ref.doc) : { whole: +ref.line.cost || 0 },
    whole = M.whole || +ref.line.cost || 0;
  return mbModal(
    "Set the Material Portion",
    `<p class="small" style="margin:0 0 8px" data-nocase>${esc(name)}: a budget of ${money(whole)} for labour and material together. Enter the material part in dollars, or as a percent of the line ("40%"); the rest is labour. The price and the client's document do not change.</p>${mbF("Material", `<input data-f="mat" inputmode="decimal" placeholder="e.g. 12000 or 40%" value="${M.split ? esc(String(M.budget)) : ""}">`)}`,
    {
      submit: "Save the Portion",
      onSubmit: (f) => {
        const s = String(f.mat || "").trim(),
          v = /%\s*$/.test(s) ? r2((whole * parseFloat(s)) / 100) : +s.replace(/[$,\s]/g, "");
        if (!s || !isFinite(v)) return toast("Enter dollars, or a percent like 40%"), !1;
        const out = rfqSetMatBudget(key, v);
        return out ? (delete ref.line.matAsk, save(), void 0) : !1;
      },
    },
  );
}
// the PM's Approvals: every line on his jobs whose material portion the buying waits on
if ("function" == typeof mApprovals) {
  const base = mApprovals;
  mApprovals = function (opts) {
    const out = base.apply(this, arguments);
    try {
      if (!Array.isArray(out) || !((opts && opts.everyone) || "pm" === role())) return out;
      const me = String(((currentUser() || {}).name) || "").toLowerCase().split(" ")[0];
      const R = buyList("").filter((r) => r.matUnknown && !r.ordered && (r.lineKey || r.key) && (!me || !r.p.project.pm || String(r.p.project.pm).toLowerCase().includes(me)));
      const seen = new Set();
      return out.concat(
        R.filter((r) => !seen.has(r.lineKey || r.key) && seen.add(r.lineKey || r.key)).map((r) => {
          const k = r.lineKey || r.key,
            ask = r.l && r.l.matAsk;
          return { kind: "matsplit", id: k, sev: "warn", n: "Split", title: `Set the material portion: ${r.name}`, detail: `${puJob(r.p)} · ${puLineWord(r)} · budget ${money(r.budget || 0)} for labour and material together · the coordinator buys against the material part${ask ? ` · asked by ${ask.by}` : ""}`, yes: "Set the Portion", who: "pm", due: r.orderBy || "", open: { puMat: k } };
        }),
      );
    } catch (e) {
      return out;
    }
  };
}
if ("function" == typeof mGo) {
  const base = mGo;
  mGo = function (go) {
    if (go && go.puMat) return void puMatSheet(go.puMat);
    return base.apply(this, arguments);
  };
}

// ---- the order sheet from lines (ctPOPicker), the one order path's sheet ----------------------------------------------
// On the phone each line is a card: the item in full, its estimate line, quantity with unit, unit cost, then a full-width
// vendor (11-05: a desktop table that opened scrolled sideways, names cut, the vendor box reading "ve"). On both devices
// each ticked line shows the one budget test as it is typed (lineBudgetTest), the best price known for the item, and the
// field request the order covers (ticked, it leaves the store run, so the studs are bought once).
function puCtpDecorate(pid, m) {
  if (!m || !m.querySelector("table.ctp")) return;
  const p = (DB.projects || []).find((x) => x.id === pid) || null,
    cl = p && (DB.clients || []).find((c) => c.id === p.clientId),
    docs = cl ? [...cl.estimates, ...cl.changeOrders, ...cl.invoices] : [],
    route = puOnRoute();
  m.classList.add("pu-ctp");
  m.classList.toggle("pu-ctp-ph", puPhone());
  const LAB = ["", "Line", "Quantity", "Unit", "Unit Cost", "Vendor", "On Order"];
  m.querySelectorAll("table.ctp tr.ctp-line, table.ctp tr.ctp-item").forEach((tr) => {
    if (tr.dataset.pudone) return;
    tr.dataset.pudone = "1";
    const cb = tr.querySelector("[data-ctpsel]");
    if (!cb) return;
    const sel = cb.dataset.ctpsel,
      lid = sel.split("#")[0],
      d = docs.find((x) => (x.lines || []).some((l) => l.id === lid)),
      l = d && d.lines.find((x) => x.id === lid),
      key = d && l ? ctKey(d, l) : "";
    tr.dataset.pukey = key;
    [...tr.cells].forEach((td, i) => LAB[i] && td.setAttribute("data-lab", LAB[i]));
    const lab = { ctpq: "Quantity", ctpu: "Unit", ctpc: "Unit cost", ctpv: "Vendor" };
    Object.keys(lab).forEach((k) => {
      const inp = tr.querySelector(`[data-${k}]`);
      inp && inp.setAttribute("aria-label", `${lab[k]}, ${(l && l.item) || "line"}`);
    });
    cb.setAttribute("aria-label", `Buy ${(l && l.item) || "this line"}`);
    // before award only the long-lead lines can be ticked; the rest wait for the estimate's approval
    d && l && "function" == typeof docBuyable && !docBuyable(d) && !puLongLead(l) && ((cb.checked = !1), (cb.disabled = !0), tr.classList.add("pu-ctpwait"), tr.cells[1] && tr.cells[1].insertAdjacentHTML("beforeend", `<div class="pu-ctpn">Waits for ${esc(d.number)} to be approved</div>`));
    const cell = tr.cells[1];
    if (!cell) return;
    tr.classList.contains("ctp-line") && d && cell.insertAdjacentHTML("beforeend", `<div class="pu-ctpdoc small muted" data-nocase>${esc(d.number)}${l.num ? ` line ${l.num}` : ""}</div>`);
    // the field requests on this line that this order may cover
    if (tr.classList.contains("ctp-line") && p && key) {
      const Q = (p.requests || []).filter((q) => q.line === key && !["ordered", "delivered", "closed", "declined"].includes(q.status) && "order" !== q.path && "stock" !== q.path);
      Q.length &&
        cell.insertAdjacentHTML(
          "beforeend",
          Q.map((q) => `<label class="pu-ctpreq"><input type="checkbox" data-ctpreq="${esc(sel)}" value="${esc(q.id)}" checked><span data-nocase>This order covers ${esc(q.by || "the site")}'s request: ${esc([q.qty, q.unit, q.what].filter(Boolean).join(" "))}${route.has(q.id) ? ", now on today's store run (it comes off the run)" : ""}</span></label>`).join(""),
        );
    }
    cell.insertAdjacentHTML("beforeend", `<div class="pu-ctpn" data-puctpn="${esc(sel)}" data-nocase></div>`);
  });
  puCtpCheck(m);
}
function puCtpCheck(m) {
  const rows = [...m.querySelectorAll("table.ctp tr[data-pukey]")],
    v = (tr, k) => (tr.querySelector(`[data-${k}]`) || {}).value || "",
    on = (tr) => !!(tr.querySelector("[data-ctpsel]") || {}).checked,
    adds = {};
  rows.forEach((tr) => on(tr) && tr.dataset.pukey && (adds[tr.dataset.pukey] = (adds[tr.dataset.pukey] || 0) + (+v(tr, "ctpq") || 1) * (+v(tr, "ctpc") || 0)));
  // one Why in the sheet when a ticked line needs a reason: a second subcontract order on its line, or a long-lead line
  // bought before its estimate is approved (create reads it; a prompt over the sheet would close the sheet)
  const keys = Object.keys(adds),
    refOf = (k) => {
      try {
        return findLine(k);
      } catch (e) {
        return null;
      }
    },
    second = keys.filter((k) => {
      const r = refOf(k);
      return r && "function" == typeof bbSubScope && bbSubScope(r.line) && (DB.pos || []).some((po) => "cancelled" !== po.status && (po.lines || []).some((pl) => pl.line === k));
    }),
    early = keys.filter((k) => {
      const r = refOf(k);
      return r && "function" == typeof docBuyable && !docBuyable(r.doc);
    });
  let box = m.querySelector(".pu-ctpwhy");
  if (second.length || early.length) {
    const lab = early.length ? `Why buy before ${refOf(early[0]).doc.number} is approved? The owner reads it before approving.` : `Why a second subcontract order on this line (it has ${(DB.pos || []).filter((po) => "cancelled" !== po.status && (po.lines || []).some((pl) => pl.line === second[0])).map((po) => po.number).join(", ")})?`;
    if (!box) {
      const bd = m.querySelector(".mbm-bd");
      bd && bd.insertAdjacentHTML("afterbegin", `<div class="f pu-ctpwhy"><label for="pu-ctpwhy"></label><input id="pu-ctpwhy" placeholder="A sentence: e.g. the scope is split, or the lead time is 14 weeks"></div>`);
      box = m.querySelector(".pu-ctpwhy");
    }
    box && ((box.hidden = !1), (box.querySelector("label").textContent = lab));
  } else box && (box.hidden = !0);
  rows.forEach((tr) => {
    const n = tr.querySelector("[data-puctpn]"),
      key = tr.dataset.pukey;
    if (!n || !key) return;
    const say = [];
    let tone = "";
    if (on(tr)) {
      const t = lineBudgetTest(key, adds[key] || 0);
      t.ok ? t.c && t.c.budget > 0 && say.push(`${money(Math.max(0, r2(t.c.budget - t.after)))} left on the line after this buy`) : ((tone = "bad"), say.push(`Over budget: ${t.say}.`));
      // the price against the best known for the item (the request it covers names the item when the line does not)
      const req = tr.querySelector("[data-ctpreq]:checked"),
        q = req && ((DB.projects || []).flatMap((p) => p.requests || []).find((x) => x.id === req.value) || null),
        name = q ? q.what || "" : ((tr.cells[1] || {}).querySelector ? (tr.cells[1].querySelector("b") || tr.cells[1]).textContent : "").replace(/^\d+\.\s*/, ""),
        unit = q ? q.unit : v(tr, "ctpu"),
        price = +v(tr, "ctpc") || 0,
        qty = +v(tr, "ctpq") || 1;
      // one verdict at entry and at Issue: lane P1's poLinePriceCheck (the item's own price-book key, no look-alikes)
      // when it is in the build; this sheet's own reading of the price history until it is
      if ("function" == typeof poLinePriceCheck) {
        const P = price > 0 && name ? poLinePriceCheck(name, unit, price, qty) : null;
        P && !P.ok && ((tone = tone || "warn"), say.push(`${unitMoney(price)} is ${unitMoney(P.gap)} above the ${"best" === P.kind ? "best recent" : "last"} price, ${unitMoney(P.ref)}${P.vendor ? ` at ${P.vendor}` : ""}${P.doc ? ` on ${P.doc}` : ""}${P.date ? `, ${fmt(P.date)}` : ""}.`));
      } else {
        const best = price > 0 && name ? puBestFor(name, unit) : null;
        best && price > best.price * 1.03 + 0.005 && ((tone = tone || "warn"), say.push(`${unitMoney(price)} is ${Math.round((price / best.price - 1) * 100)}% above the best price known: ${unitMoney(best.price)}/${best.unit || "ea"} at ${best.vendor}${best.date ? `, ${fmt(best.date)}` : ""} (${best.label}).`));
      }
    } else {
      const c = lineCommitment(key);
      c && c.budget > 0 && c.left < 1 && ((tone = "warn"), say.push(c.over ? `${money(c.over)} over the line already` : "Nothing left to buy on this line"));
    }
    n.className = `pu-ctpn ${tone}`;
    n.textContent = say.join(" ");
  });
}
{
  const base = ctPOPicker;
  ctPOPicker = function (projectId, preferId, preKey) {
    const r = base.apply(this, arguments);
    puPreAwardId = "";
    try {
      const m = document.getElementById("mbm");
      if (m && m.querySelector("table.ctp")) {
        puCtpDecorate(projectId, m);
        m.addEventListener("input", () => puCtpCheck(m));
        m.addEventListener("change", (e) => (e.target && "ctp-doc" === e.target.id ? setTimeout(() => puCtpDecorate(projectId, m), 0) : puCtpCheck(m)));
        // a request ticked as covered names the item on the order's line: keep the request's words on the line
      }
    } catch (e) {
      console.warn("order sheet", e);
    }
    return r;
  };
}

// ---- the document's door: Buy These Lines on the estimate, change order and invoice (SPEC: one order path, two doors) --
// Tap Buy These Lines, tick one line or several on the document itself (phone cards too), then the bar's Buy These Lines
// opens the same order sheet with those lines ticked and linked.
let puDocPick = null;
if ("function" == typeof docAction) {
  const base = docAction;
  docAction = function (c, d, a) {
    if ("pos" === a && d && d.projectId && "function" == typeof docBuyable && docBuyable(d)) {
      puDocPick = { id: d.id, cid: c.id, type: d.type, keys: new Set() };
      return void render();
    }
    return base.apply(this, arguments);
  };
}
const PU_TICK = {
  on: '<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="#2456C9"/><path d="M7.5 12.5l3 3 6-6.5" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  off: '<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.8" y="3.8" width="16.4" height="16.4" rx="4.5" fill="none" stroke="#8A93A3" stroke-width="1.6"/></svg>',
};
function puDocDoc() {
  if (!puDocPick || "undefined" == typeof docOpen || !docOpen || docOpen.id !== puDocPick.id) return null;
  const c = (DB.clients || []).find((x) => x.id === puDocPick.cid);
  return (c && findDoc(c, puDocPick.type, puDocPick.id)) || null;
}
function puDocDecorate() {
  document.querySelectorAll(".pu-docbar").forEach((b) => b.remove());
  if (!puDocPick) return;
  const v = document.querySelector(".view.on"),
    d = puDocDoc(),
    rows = v ? [...v.querySelectorAll("table.rx-lines tr[data-rxline]")] : [];
  if (!d || !rows.length) return void (puDocPick = null);
  const keyOf = (lid) => ctKey(d, d.lines.find((l) => l.id === lid) || { id: lid });
  rows.forEach((tr) => {
    const lid = tr.dataset.rxline,
      l = d.lines.find((x) => x.id === lid);
    if (!l || tr.querySelector(".pu-docpick")) return;
    const key = keyOf(lid),
      c = lineCommitment(key),
      cell = tr.cells[0],
      item = tr.cells[1];
    tr.classList.add("pu-docrow");
    cell && cell.insertAdjacentHTML("afterbegin", `<button type="button" class="pu-docpick" data-pubuy="${esc(lid)}" aria-pressed="${puDocPick.keys.has(key)}" aria-label="Buy ${esc(l.item || "this line")}">${puDocPick.keys.has(key) ? PU_TICK.on : PU_TICK.off}</button>`);
    c && c.budget > 0 && item && item.insertAdjacentHTML("beforeend", `<div class="small pu-docleft ${c.left < 1 ? "bad" : ""}" data-nocase>${c.over ? `${money(c.over)} over the line` : `${money(c.left)} left to buy`}${c.pos.length ? ` · ${c.pos.map((po) => po.number).join(", ")}` : ""}</div>`);
  });
  // one blue on the screen while picking: the bar's
  v.querySelectorAll(".btn.primary").forEach((b) => b.closest(".pu-docbar") || (b.classList.remove("primary"), b.classList.add("pu-wasprimary")));
  const bar = document.createElement("div");
  bar.className = "pu-docbar";
  v.appendChild(bar);
  const draw = () => {
    const K = [...puDocPick.keys],
      left = r2(K.reduce((a, k) => a + ((lineCommitment(k) || {}).left || 0), 0));
    bar.innerHTML = `<span class="pu-bt" data-nocase><b>${K.length ? `${K.length} line${1 === K.length ? "" : "s"} picked` : "Tick the lines to buy"}</b>${K.length ? ` · ${money(left)} left on ${1 === K.length ? "it" : "them"}` : ` on ${esc(d.number)}`}</span><span class="pu-bb"><button type="button" class="btn" id="pu-docbuy-x">Cancel</button><button type="button" class="btn primary" id="pu-docbuy-go">Buy These Lines</button></span>`;
    bar.querySelector("#pu-docbuy-x").onclick = () => ((puDocPick = null), render());
    bar.querySelector("#pu-docbuy-go").onclick = () => {
      if (!puDocPick.keys.size) return toast("Tick at least one line");
      const keys = [...puDocPick.keys];
      puDocPick = null;
      render();
      ctPOPicker(d.projectId, d.id, keys);
    };
  };
  draw();
  v.querySelectorAll("[data-pubuy]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.stopPropagation();
        const k = keyOf(b.dataset.pubuy),
          on = !puDocPick.keys.has(k);
        on ? puDocPick.keys.add(k) : puDocPick.keys.delete(k);
        b.setAttribute("aria-pressed", String(on));
        b.innerHTML = on ? PU_TICK.on : PU_TICK.off;
        b.closest("tr") && b.closest("tr").classList.toggle("pu-docon", on);
        draw();
      }),
  );
}

// ---- FF&E Buying Tools: its own name, a buy run only when there is something to buy, labels that stay Title Case ------
// (11-05: the page was headed "Buy Board" under the Buy Board's own button, its blue New Buy Run only toasted with nothing
// ticked, and its tabs fell to sentence case after a tap, because a tab redraws the board alone and the label pass runs
// on render(); it now runs on every draw of this page.)
function puFfeDress(root) {
  if (!root || "undefined" == typeof procMode || "finish" !== procMode) return;
  const pane = "undefined" != typeof procPane ? procPane : "board";
  root.querySelectorAll('[data-ppane="board"]').forEach((b) => (b.textContent = "FF&E Items"));
  if ("board" === pane) {
    const h = root.querySelector(".ph h2");
    h && ((h.textContent = "FF&E Buying Tools"), (h.dataset.iaKeep = "1"));
    const run = root.querySelector("#proc-run");
    if (run && !(procSel && procSel.size)) run.outerHTML = `<span class="small muted pu-runhint">Tick the items to buy: a buy run makes one order per vendor.</span>`;
  }
  try {
    "function" == typeof tcLabels && tcLabels(root);
  } catch (e) {}
}
// the phone's header names the page (the desktop's crumb is the menu's place, Buy Board)
function puFfeCrumb() {
  if ("proc" !== view || "undefined" == typeof procMode || "finish" !== procMode || ("undefined" != typeof procPane && "board" !== procPane) || !puPhone()) return;
  const c = document.getElementById("crumbs");
  c && (c.innerHTML = "<b>FF&amp;E Buying Tools</b>");
}

// ---- a second subcontract on one line: a reason, on every path (the chief of staff, 11-05) -----------------------------
// The order sheet asks for it at create; an award, a copy or any other path that makes a second subcontract order on the
// same contract line is held at Issue by the one validator (poValid) until the reason is on the order.
function puSecondSub(po) {
  if (!po || "cancelled" === po.status) return [];
  const out = [],
    at = (DB.pos || []).indexOf(po);
  [...new Set((po.lines || []).map((l) => l.line).filter(Boolean))].forEach((k) => {
    let ref = null;
    try {
      ref = findLine(k);
    } catch (e) {}
    const l = ref && ref.line;
    if (!l) return;
    // a subcontract scope line (demolition, scaffold, abatement: bbSubScope): a tile or plumbing line rightly carries a
    // material order and an install sub side by side, so the order's type alone is not the test (chain step 10)
    const sub = "function" == typeof bbSubScope && bbSubScope(l) && !("function" == typeof bbBuysLine && bbBuysLine(l));
    if (!sub) return;
    const others = (DB.pos || []).filter((x, i) => x !== po && i < at && "cancelled" !== x.status && (x.lines || []).some((y) => y.line === k));
    others.length && out.push({ key: k, name: `${ref.doc.number}${l.num ? ` line ${l.num}` : ""} (${l.item || l.desc || ""})`, others: others.map((x) => x.number) });
  });
  return out;
}
function puSecondSheet(po) {
  const S0 = puSecondSub(po);
  if (!S0.length) return;
  return mbModal(
    "A Second Order on This Line",
    `<p class="small" style="margin:0 0 8px" data-nocase>${S0.map((x) => `${esc(x.name)} already has ${esc(x.others.join(", "))}.`).join(" ")} A second sub for the same scope buys it twice unless the scope is split.</p>${mbF("Why", `<input data-f="why" value="${esc(po.secondOrderWhy || "")}" placeholder="e.g. the scope is split: the garden unit goes to a second sub">`)}`,
    {
      submit: "Save the Reason",
      onSubmit: (f) => {
        if (!f.why || f.why.trim().length < 8) return toast("A sentence, so the owner and the job cost know why"), !1;
        po.secondOrderWhy = f.why.trim();
        try {
          audit("po", po.id, "second order on a subcontract line", "", po.number, po.secondOrderWhy);
        } catch (e) {}
        save(), render();
        toast(`${po.number}: the reason for a second order on the line is saved`, { label: "Open", run: () => flowGo.po(po)() });
      },
    },
  );
}

// ---- long-lead lines before award: an owner-approved exception (the chief of staff, 11-05, for Alan's call) ----------
// The Standard releases long-lead items at design approval. A long-lead line of an estimate not yet approved can be
// drafted (marked "Long-Lead, Before Award", with the reason); it is issued only once the owner approves it in Approvals
// (exceptions only); if the estimate is lost the order is held and flagged on Orders to cancel. Every other line waits
// for approval (docBuyable).
const PU_LONG_LEAD_WEEKS = 4;
const puLongLead = (l) => !!l && (!!l.longLead || +l.leadWeeks >= PU_LONG_LEAD_WEEKS || /\blong[- ]lead\b/i.test(`${l.item || ""} ${l.desc || ""}`));
const puPreAwardDoc = (d) => !!d && "estimate" === d.type && ["draft", "sent"].includes(d.status) && (d.lines || []).some(puLongLead);
let puPreAwardId = "";
const puPreAwardOpen = (d) => !!d && d.id === puPreAwardId && puPreAwardDoc(d);
const puEstOf = (po) => {
  const a = po && po.preAward;
  if (!a) return null;
  for (const c of DB.clients || []) {
    const d = (c.estimates || []).find((e) => e.id === a.estimateId);
    if (d) return d;
  }
  return null;
};
const puPreAwardLost = (po) => {
  const d = puEstOf(po);
  return !!d && ["rejected", "expired"].includes(d.status);
};
if ("function" == typeof docActions) {
  const base = docActions;
  docActions = function (c, d, st) {
    let h = base.apply(this, arguments);
    try {
      d && d.projectId && !docBuyable(d) && puPreAwardDoc(d) && !/data-docact="preaward"/.test(h) && (h += `<button class="btn sm" data-docact="preaward">Long-Lead Lines Before Award</button>`);
    } catch (e) {}
    return h;
  };
}
if ("function" == typeof docAction) {
  const base = docAction;
  docAction = function (c, d, a) {
    if ("preaward" === a && d && puPreAwardDoc(d)) {
      puPreAwardId = d.id;
      ctPOPicker(d.projectId, d.id, (d.lines || []).filter(puLongLead).map((l) => ctKey(d, l)));
      return;
    }
    return base.apply(this, arguments);
  };
}
function puPreAwardSheet(po) {
  if (!po || !po.preAward) return;
  const d = puEstOf(po),
    owner = "owner" === role(),
    a = po.preAward;
  return mbModal(
    `Long-Lead, Before Award: <span data-nocase>${esc(po.number)}</span>`,
    `<p class="small" style="margin:0 0 8px" data-nocase>${esc(po.vendor || "No vendor")} · ${money(poTotal(po).total)} on ${esc(a.number)}, which is ${esc(d ? d.status : "not found")}. ${esc((po.lines || []).map((l) => l.item).join(", "))}.</p><p class="small" style="margin:0 0 8px" data-nocase><b>Why now:</b> ${esc(a.why || "no reason given")} (${esc(a.by || "")})</p>${a.approved ? `<p class="small muted">Approved by ${esc(a.approved.by)}, ${esc(stampText(a.approved.at))}.</p>` : `<p class="small muted">${owner ? "Approving lets it be issued before the estimate is approved. If the estimate is lost, the order is flagged to cancel." : "The owner approves it in Approvals before it can be issued."}</p>`}`,
    {
      submit: owner && !a.approved ? "Approve Before Award" : null,
      onSubmit: () => {
        a.approved = { by: ((currentUser() || {}).name) || "Owner", at: appNowIso() };
        try {
          audit("po", po.id, "long-lead before award approved", "", po.number, a.why);
        } catch (e) {}
        save(), render();
        toast(`${po.number} approved before award: it can be issued`, { label: "Open", run: () => flowGo.po(po)() });
      },
    },
  );
}
// the owner's Approvals (exceptions only): each long-lead order waiting before award
if ("function" == typeof mApprovals) {
  const base = mApprovals;
  mApprovals = function (opts) {
    const out = base.apply(this, arguments);
    try {
      if (!Array.isArray(out) || !((opts && opts.everyone) || "owner" === role())) return out;
      const P = (DB.pos || []).filter((po) => po.preAward && !po.preAward.approved && ["draft", "pending"].includes(po.status) && !puPreAwardLost(po));
      return out.concat(P.map((po) => ({ kind: "preaward", id: po.id, sev: "warn", n: money(poTotal(po).total), title: `${po.number}: long-lead before award`, detail: `${po.vendor || "No vendor"} · ${po.preAward.number} not approved yet · why: ${po.preAward.why || "no reason given"}`, yes: "Review the Order", who: "owner", due: po.needBy || "", open: { puPreAward: po.id } })));
    } catch (e) {
      return out;
    }
  };
}
if ("function" == typeof mGo) {
  const base = mGo;
  mGo = function (go) {
    if (go && go.puPreAward) return void puPreAwardSheet((DB.pos || []).find((x) => x.id === go.puPreAward));
    return base.apply(this, arguments);
  };
}
// Orders: a long-lead order whose estimate was lost is flagged to cancel (it is the coordinator's)
function puPreAwardRows(pid) {
  return (DB.pos || [])
    .filter((po) => po.preAward && !["cancelled", "received"].includes(po.status) && (!pid || po.projectId === pid) && puPreAwardLost(po))
    .map((po) => ({ id: "preaward:" + po.id, name: `${po.number}: ${po.preAward.number} was lost`, job: puJob((DB.projects || []).find((p) => p.id === po.projectId)), line: `Long-Lead, Before Award · ${po.vendor || "no vendor"} · ${money(poTotal(po).total)}`, why: "The estimate it was bought for is lost. Cancel the order, or ask the vendor what a cancellation costs.", act: "Open the Order", run: () => flowGo.po(po)(), tone: "bad", actor: "coord" }));
}
// the one validator: a second sub with no reason, and a long-lead order before award without the owner, are held at Issue
if ("function" == typeof poValid) {
  const base = poValid;
  poValid = function (po) {
    const R = base.apply(this, arguments);
    try {
      if (po && ["draft", "pending"].includes(po.status || "draft")) {
        const S0 = puSecondSub(po);
        S0.length && !po.secondOrderWhy && R.push(`a second subcontract order on ${S0.map((x) => `${x.name}, which has ${x.others.join(", ")}`).join("; ")}: say why on the order`);
        po.preAward && puPreAwardLost(po) && R.push(`${po.preAward.number} was lost: cancel this long-lead order`);
        po.preAward && !po.preAward.approved && !puPreAwardLost(po) && R.push(`a long-lead order before ${po.preAward.number} is approved: the owner approves it first (Approvals)`);
      }
    } catch (e) {
      console.warn("second sub and pre-award", e);
    }
    return R;
  };
}
// the order page says both before anyone presses Issue, each with its one next step
if ("function" == typeof renderPODoc) {
  const base = renderPODoc;
  renderPODoc = function (po) {
    let h = base.apply(this, arguments);
    try {
      if (po && ["draft", "pending"].includes(po.status) && "string" == typeof h) {
        const S0 = puSecondSub(po),
          box =
            (S0.length && !po.secondOrderWhy ? `<div class="qcheck po-second" role="alert"><b>A Second Order on This Line</b><span data-nocase>${esc(S0.map((x) => `${x.name} already has ${x.others.join(", ")}`).join("; "))}.</span><div class="row" style="gap:6px;margin-top:6px"><button type="button" class="btn sm" data-pu2nd="${esc(po.id)}">Give the Reason</button></div></div>` : "") +
            (po.preAward ? `<div class="qcheck po-preaward ${puPreAwardLost(po) ? "" : "warn"}" role="alert"><b>Long-Lead, Before Award</b><span data-nocase>${esc(po.preAward.number)}${puPreAwardLost(po) ? " was lost: cancel this order." : po.preAward.approved ? `: approved by ${esc(po.preAward.approved.by)}.` : " is not approved yet: the owner approves this order before it is issued."}</span><div class="row" style="gap:6px;margin-top:6px"><button type="button" class="btn sm" data-pupre="${esc(po.id)}">Open the Approval</button></div></div>` : "");
        box && (h = box + h);
      }
    } catch (e) {
      console.warn("po second and pre-award", e);
    }
    return h;
  };
}
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest && e.target.closest("[data-pu2nd],[data-pupre]");
    if (!b) return;
    const po = (DB.pos || []).find((x) => x.id === (b.dataset.pu2nd || b.dataset.pupre));
    po && (b.dataset.pu2nd ? puSecondSheet(po) : puPreAwardSheet(po));
  },
  !0,
);

// ---- the look ---------------------------------------------------------------------------------------------------------
(() => {
  const css = `
.view.pu-host.pu-full>:not(.pu){margin-top:16px}
#v-recv.pu-host #recv-body>.ph{display:none}
.pu-h3{margin:18px 0 8px;font-size:15px}
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
.pu-tx{font-size:12.5px;color:var(--warn);border-top:1px dashed var(--rule);padding-top:4px;margin-top:2px;line-height:1.35}
.pu-note2{font-size:13px;color:var(--ink-3);margin:0 0 12px}
table.pu-vt{width:100%} table.pu-vt td.bad{color:var(--bad);font-weight:600} table.pu-vt tbody tr{cursor:pointer}
.pu-bar{position:sticky;bottom:0;display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:10px 14px;box-shadow:0 -6px 20px rgba(17,26,46,.08);z-index:20}
.pu-bt{flex:1;min-width:0;font-size:14px} .pu-bb{display:flex;gap:8px;flex-wrap:wrap}
.pu-rq{display:flex;align-items:center;gap:10px;padding:8px 0;border-top:1px solid var(--rule-2)}
.pu-rq>span{flex:1;display:flex;flex-direction:column;gap:2px} .pu-rq input{width:96px;min-height:44px}
.pu-conds{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
/* the count box holds its whole hint ("1,000 to come"), on the desktop and at 390px (it read "900 to con") */
#mbm .pu-rql .pu-rq input[data-purq]{width:9.5em;min-width:9.5em;flex:0 0 auto;font-size:16px;padding-left:10px;padding-right:10px;box-sizing:border-box}
#mbm .pu-rql, #mbm .pu-rql .small, #mbm .pu-rql .pu-chip, #mbm .pu-early, .mbm-bd:has(.pu-rql) > p, .mbm-bd:has(.pu-rql) label.f > span{font-size:15px}
/* the foreman's request (the field expert): Urgent is a 44px target, and Send stays in reach with the keyboard up */
label:has(> #cp-urgent){min-height:44px;min-width:44px;display:inline-flex;align-items:center;gap:8px;padding:0 10px 0 4px;cursor:pointer} #cp-urgent{width:24px;height:24px}
@media (max-width:600px){ .sendbar:has(#cp-urgent), .frq-when-row + .sendbar{position:sticky;bottom:0;z-index:3;background:var(--paper);padding:8px 0;box-shadow:0 -1px 0 var(--rule-2)} }
.pu-rql{border-top:1px solid var(--rule-2);padding-bottom:4px} .pu-rql .pu-rq{border-top:0} .pu-rql .pu-conds{margin:4px 0 8px} .pu-rql .pu-bad[hidden]{display:none}
.pu-lines{display:flex;flex-direction:column;gap:6px;max-height:50vh;overflow:auto;margin-top:8px}
.pu-line{display:flex;gap:10px;align-items:flex-start;padding:6px 0;border-top:1px solid var(--rule-2)} .pu-line>span{display:flex;flex-direction:column}
.pu-kv{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-top:1px solid var(--rule-2)}
#buy-board.pu .bb-main{display:flex;gap:16px;align-items:flex-start}
#buy-board.pu .bb-list{flex:1;min-width:0}
#buy-board.pu .pu-row .bb-pick{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;border:0;background:none;cursor:pointer;padding:0}
.pu-ctpn{font-size:12.5px;color:var(--ink-3);margin-top:3px;line-height:1.35} .pu-ctpn:empty{display:none}
.pu-ctpn.bad{color:var(--bad);font-weight:600} .pu-ctpn.warn{color:var(--warn);font-weight:600}
.pu-ctpreq{display:flex;gap:8px;align-items:flex-start;font-size:12.5px;margin-top:6px;color:var(--ink-2);font-weight:400}
.pu-ctpreq input{margin-top:2px;flex:none}
.pu-runhint{align-self:center}
.pu-docpick{width:44px;height:44px;display:inline-flex;align-items:center;justify-content:center;border:0;background:none;padding:0;cursor:pointer;vertical-align:middle}
tr.pu-docon{background:var(--accent-2)}
.pu-docleft{color:var(--ink-3)} .pu-docleft.bad{color:var(--bad);font-weight:600}
.pu-docbar{position:sticky;bottom:0;display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:10px 14px;box-shadow:0 -6px 20px rgba(17,26,46,.08);z-index:25;margin-top:12px}
@media (max-width:760px){
  .pu-ph{flex-direction:column;gap:8px}
  .pu-ph .acts{width:100%}
  .pu-menu{position:fixed;left:16px;right:16px;top:auto;width:auto}
  .pu-tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
  /* a phone row is one record, four or more to a screen (tests/phone_rows_lint.py): the words clamp, the action sits beside */
  .pu-row{flex-wrap:nowrap;align-items:center;padding:10px 12px;gap:8px}
  .pu-row .pu-rb{flex:1 1 auto;min-width:0}
  .pu-sub,.pu-when{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
  .pu-why{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .pu-rb b{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .pu-act{min-height:44px !important;max-width:38%;flex:none;white-space:normal;line-height:1.15;font-size:13px;padding:4px 10px}
  .pu-link,.pu-chip,.pu-plusb{min-height:44px !important}
  .pu-chip{padding:0 14px;font-size:14px}
  .pu-sel{min-height:44px;flex:1 1 140px}
  .pu-bar{position:fixed;left:8px;right:8px;bottom:calc(var(--bb-tabs, 64px) + 8px)}
  .bb-picking .pu-list{padding-bottom:180px}
  .pu-bb{width:100%} .pu-bb .btn{flex:1;min-height:44px}
  #buy-board.pu .bb-main{display:block}
  .pu-tile{min-height:84px}
  /* the order sheet from lines: a card per line, nothing sideways (11-05) */
  #mbm.pu-ctp-ph .tw{max-height:none !important;overflow:visible !important}
  #mbm.pu-ctp-ph table.ctp{display:block;width:100%;min-width:0 !important;border:0}
  #mbm.pu-ctp-ph table.ctp thead{display:none}
  #mbm.pu-ctp-ph table.ctp tbody{display:block;width:100%}
  #mbm.pu-ctp-ph table.ctp tr{display:grid;grid-template-columns:44px minmax(0,1fr) minmax(0,1fr) minmax(0,1.3fr);gap:6px 8px;padding:12px 0;border-top:1px solid var(--rule-2);width:100%;box-sizing:border-box}
  #mbm.pu-ctp-ph table.ctp tr.ctp-doc{display:block}
  #mbm.pu-ctp-ph table.ctp td{display:block;padding:0 !important;border:0 !important;width:auto !important;min-width:0;white-space:normal;height:auto !important;min-height:0 !important;max-height:none !important;overflow:visible}
  #mbm.pu-ctp-ph table.ctp tr{height:auto !important}
  #mbm.pu-ctp-ph table.ctp td:nth-child(1){grid-column:1;grid-row:1;align-self:start}
  #mbm.pu-ctp-ph table.ctp td:nth-child(1) .ctp-tick{display:flex;width:44px;height:44px;align-items:center;justify-content:center}
  #mbm.pu-ctp-ph table.ctp td:nth-child(1) input{width:22px;height:22px}
  #mbm.pu-ctp-ph table.ctp td:nth-child(2){grid-column:2 / -1;grid-row:1;padding-left:0 !important}
  #mbm.pu-ctp-ph table.ctp td:nth-child(3){grid-column:2;grid-row:2}
  #mbm.pu-ctp-ph table.ctp td:nth-child(4){grid-column:3;grid-row:2}
  #mbm.pu-ctp-ph table.ctp td:nth-child(5){grid-column:4;grid-row:2}
  #mbm.pu-ctp-ph table.ctp td:nth-child(6){grid-column:1 / -1;grid-row:3}
  #mbm.pu-ctp-ph table.ctp td:nth-child(n+7){grid-column:1 / -1}
  #mbm.pu-ctp-ph table.ctp td:nth-child(7):empty{display:none}
  #mbm.pu-ctp-ph table.ctp td[data-lab]:not(:nth-child(2))::before{content:attr(data-lab);display:block;font-size:12px;color:var(--ink-3);margin-bottom:2px}
  #mbm.pu-ctp-ph table.ctp td input:not([type=checkbox]){width:100% !important;min-height:44px;font-size:16px;box-sizing:border-box}
  #mbm.pu-ctp-ph table.ctp td b{white-space:normal;overflow-wrap:anywhere}
  .pu-docbar{position:fixed;left:8px;right:8px;bottom:calc(var(--bb-tabs, 64px) + 8px)}
  .pu-docbar .pu-bb{width:100%} .pu-docbar .pu-bb .btn{flex:1;min-height:44px}
  .view.on:has(.pu-docbar){padding-bottom:180px}
}
`;
  const st = document.createElement("style");
  (st.id = "purchasing-css"), (st.textContent = css), document.head.appendChild(st);
})();
// The bill's own page, outermost (later wrappers of openBill rebuild the sheet, so this runs last): a bill billed over its
// PO or over what arrived offers the Owner Approve Part, Dispute the Rest beside Approve (the three-way match, J7); the
// person who received, the coordinator, the PM or the controller, has Hold at What Arrived for the Owner instead.
if ("function" == typeof openBill) {
  const base = openBill;
  openBill = function (id) {
    const r = base.apply(this, arguments);
    try {
      const b = (DB.bills || []).find((x) => x.id === id),
        body = document.getElementById("d-body");
      if (!b || !body || b.short || b.dispute || "function" != typeof pay3Can || !pay3Can(b)) return r;
      const over = pay3Default(b) > 0,
        arrived = pay3OverArrived(b),
        ap = body.querySelector('[data-bact="approve"]'),
        pm = body.querySelector('[data-bact="pmok"]'),
        row = (ap || pm || {}).parentElement || null;
      if (isOwner() && (over || null != arrived) && !body.querySelector("[data-pay3short]") && ![...body.querySelectorAll("button")].some((x) => /^(Approve Part|Approve PO Amount)/.test(x.textContent.trim()))) {
        const btn = document.createElement("button");
        (btn.className = "btn sm primary"), (btn.dataset.pay3short = "1"), (btn.textContent = pay3Label(b)), (btn.onclick = () => pay3ShortPay(b));
        ap && ap.classList.remove("primary");
        row ? (ap || pm).before(btn) : body.prepend(btn);
      }
      if (!isOwner() && null != arrived && ["coord", "pm", "controller"].includes(role()) && !body.querySelector("[data-pay3arr]")) {
        const hb = document.createElement("button");
        (hb.className = "btn sm"), (hb.dataset.pay3arr = "1"), (hb.textContent = b.arrivedHold ? "Change the Hold at What Arrived" : "Hold at What Arrived"), (hb.onclick = () => pay3ArrivedHold(b));
        row ? row.prepend(hb) : body.prepend(hb);
      }
    } catch (e) {
      console.warn("three-way on the bill page", e);
    }
    return r;
  };
}
// The order's page, for the person who received it (the coordinator cannot open Bills and Payroll): a bill on this order
// billed over what arrived says so, with Hold at What Arrived for the Owner (J7: "the coordinator who received the
// trucks holds the bills at what arrived; only the Owner approves part of a bill").
if ("function" == typeof renderPODoc) {
  const base = renderPODoc;
  renderPODoc = function (po) {
    const h = base.apply(this, arguments);
    try {
      if (!po || "function" != typeof pay3OverArrived || isOwner()) return h;
      const B = (DB.bills || []).filter((b) => b.poId === po.id && !b.short && !b.dispute && pay3Can(b) && null != pay3OverArrived(b));
      return B.length
        ? `<div class="note warn pu-arr" role="status">${B.map((b) => `<div class="row" style="gap:8px;align-items:center;flex-wrap:wrap"><span class="grow" data-nocase><b>${esc(b.number || "A bill")}</b> bills ${money(billTotal(b))}; what arrived on ${esc(po.number)} comes to ${money2(pay3ArrivedLeft(b))}${"function" == typeof pay3ClaimWords && pay3ClaimWords(po) ? ` (${esc(pay3ClaimWords(po))})` : ""}${b.arrivedHold ? `. Held at ${money(b.arrivedHold.amount)} by ${esc(b.arrivedHold.by)} for the Owner` : ""}.</span><button type="button" class="btn sm" data-pay3arrpo="${esc(b.id)}">${b.arrivedHold ? "Change the Hold at What Arrived" : "Hold at What Arrived"}</button></div>`).join("")}</div>` + h
        : h;
    } catch (e) {
      return h;
    }
  };
}
document.addEventListener("click", (e) => {
  const x = e.target.closest && e.target.closest("[data-pay3arrpo]");
  if (!x) return;
  const b = (DB.bills || []).find((y) => y.id === x.dataset.pay3arrpo);
  b && (e.preventDefault(), pay3ArrivedHold(b));
});
// The Owner's brief says what vendor credits were applied since he last looked (the CoS, 11-06: a credit memo applied
// by the coordinator was visible only on the bill): who applied it, on what, and what went to Owed Back.
if ("function" == typeof paBriefBuild) {
  const base = paBriefBuild;
  paBriefBuild = function () {
    const m = base.apply(this, arguments);
    try {
      if (!m || "function" != typeof isOwner || !isOwner()) return m;
      const A = "function" == typeof paInit ? paInit() : {},
        since = String(A.lookPrev || iso(addDays(today(), -3))).slice(0, 10);
      (DB.bills || [])
        .filter((b) => b.short && "credited" === b.short.state && String(b.short.resolvedOn || "") >= since)
        .forEach((b) => {
          const s = b.short,
            po = b.poId && (DB.pos || []).find((x) => x.id === b.poId);
          (m.today = m.today || []).push({
            key: "vcm:" + b.id,
            k: "Vendor Credit",
            title: `${b.vendor} credited ${money2(s.held)} on ${b.number}${s.creditMemo ? ` (credit memo ${s.creditMemo})` : ""}`,
            sub: [po ? po.number : "", s.resolvedBy ? `applied by ${s.resolvedBy} ${fmtL(s.resolvedOn)}` : "", s.creditOver ? `${money2(s.creditOver.amount)} over the dispute is under Owed Back` : "", s.refundRet ? "the bill was paid: a refund due, to match a bank line" : ""].filter(Boolean).join(" · "),
            acts: [{ label: "Open", run: () => flowGo.bill(b)() }],
          });
        });
    } catch (e) {
      console.warn("owner brief vendor credits", e);
    }
    return m;
  };
}
