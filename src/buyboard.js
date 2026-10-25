/* ---------------------------------------------------------------------------------------------------------------------
   Procurement P1: One Buy Board (docs/PROCUREMENT_PLAN.md sections 4 and 6; Alan's yes, 2026-10-24).

   The noun is the Need: what must be bought. It is not a new store. A need is a row of buyList (src/app.js), the
   Buy Board's one reader, read from the records that already exist:
     material    the job's materials (p.materials), not yet on site
     line        a converted estimate's line, or an approved change order's line (src "co"), with budget left to buy
     ffe         an approved FF&E selection (DB.sel.items, stage approved or later, not yet at the office or site)
     request     an open field request (p.requests) that no material stands for yet
   Each row carries its line link (lineKey: the estimate, change-order or FF&E line; a request's is set by the
   coordinator through a picker, never guessed), the job, cost code, qty, need-by, order-by, who asked, and the one
   "late" (bbLateOf): not ordered by its order-by date; or ordered with a promise after the day the site needs it; or
   promised and not delivered by the promise. bbFinish decides it once per row; PRED.lateMaterial, the rail badge,
   Today's Do Now (tdyBuyItems), the morning brief (b2Facts), the Materials tiles, matState, selLate and Ask read it.

   The page (#v-proc) has two tabs: To Buy (Late, Order This Week, Waiting on Quotes, Later) and Arriving. On the phone
   the rows are cards (Main.dc.html, PhoneArriving.dc.html); on the desktop grouped rows with the need's side panel
   (Desk.dc.html). Lines are picked and ordered or sent for quotes together; the order goes through the existing
   order sheet (buyOrderDialog, ctPOPicker, the FF&E buy run); P2 makes that one sheet. Hooks left for P3 (receive,
   reconfirm) and P4 (claims): the Arriving card shows a reconfirmation only when the follow-ups log holds one.
   --------------------------------------------------------------------------------------------------------------------- */

// ---- the one late, and the sections -----------------------------------------------------------------------------------
function bbSectionRank(s) {
  return { late: 0, week: 1, quotes: 2, later: 3, arriving: 4, received: 5 }[s] ?? 6;
}
// A short day: the weekday inside a week of today ("Fri"), else the date ("9/24").
function bbDay(d) {
  if (!d) return "";
  const n = dayDiff(today(), d);
  return Math.abs(n) <= 6 ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][parse(d).getDay()] : fmt(d);
}
// The rule. o: { ordered, received, eta, needBy, orderBy }. Returns { late, kind: "order" | "promise" | "overdue", why }.
function bbLateOf(o) {
  const td = today();
  if (!o || o.received) return { late: !1, kind: "", why: "" };
  if (!o.ordered)
    return o.orderBy && o.orderBy < td
      ? { late: !0, kind: "order", why: `Order by ${bbDay(o.orderBy)}, passed` }
      : { late: !1, kind: "", why: "" };
  if (o.eta && o.needBy && o.eta > o.needBy)
    return { late: !0, kind: "promise", why: `Promised ${fmt(o.eta)}, needed on site ${fmt(o.needBy)}` };
  if (o.eta && o.eta < td) return { late: !0, kind: "overdue", why: `Promised ${bbDay(o.eta)}. Not here` };
  return { late: !1, kind: "", why: "" };
}
// A contract line has something to buy when it has items under it or names a material (the estimate rule since round 4,
// now shared by change-order lines).
function bbBuysLine(l) {
  return (
    (l.items || []).length > 0 ||
    /material|millwork|tile|fixture|appliance|window|door|stone|floor|light|hardware|cabinet|lumber|glass|counter|vanit|radiator|radiant/i.test(
      l.item || "",
    )
  );
}
// A subcontract scope the firm buys out (bids, then a subcontract), not a material and never our own labour.
function bbSubScope(l) {
  return /demoli|scaffold|abatement|asbestos|shoring|underpin|excavat|sidewalk shed/i.test(`${l.item || ""} ${l.desc || ""}`);
}
// A sub scope is bought out ten working days before its task starts: the bids, the leveling and the subcontract.
const BB_BUYOUT_DAYS = 10;
// An estimate or change-order line with something left to buy (src "line" or "co"): the line's material portion when
// the line carries one (rfqMatBudget), never its labour; or a subcontract scope to buy out (kind "sub").
function bbLineNeed(p, c, d, l, key, src) {
  const f = lineFin(key);
  if (!f) return null;
  const remaining = Math.max(0, r2(f.budget - f.actual - f.committed)),
    sub = !bbBuysLine(l) && bbSubScope(l);
  if (!f.budget || remaining < 1 || !(bbBuysLine(l) || sub)) return null;
  let M = { budget: null };
  try {
    M = sub ? { budget: null } : rfqMatBudget(key, l, d) || { budget: null };
  } catch (e) {}
  const matLeft = null != M.budget ? Math.max(0, r2(M.budget - f.committed)) : null;
  if (null != matLeft && matLeft < 1) return null;
  const { needBy: needBy, task: tk } = lineNeedBy(p, l),
    lead = sub ? BB_BUYOUT_DAYS : l.leadWeeks ? 5 * +l.leadWeeks : 5,
    orderBy = needBy ? addWork(needBy, -lead, !1) : "",
    funds = clientFundsLedger().find((r) => r.key === key);
  return {
    kind: sub ? "sub" : "line",
    matBudget: M.budget,
    matUnknown: !sub && null == M.budget,
    src: src,
    p: p,
    c: c,
    d: d,
    l: l,
    key: key,
    name: (l.num ? l.num + ". " : "") + (l.item || ""),
    needBy: needBy,
    orderBy: orderBy,
    lead: lead,
    task: tk,
    vendor: l.vendor || "",
    price: null != matLeft ? matLeft : remaining,
    budget: f.budget,
    held: funds ? funds.reserved : 0,
    po: null,
    ordered: !1,
    eta: "",
    dec: null,
    qty: l.qty ? `${+l.qty} ${l.unit || ""}`.trim() : "",
    code: l.code || ("function" == typeof codeForLine ? codeForLine(l) : "") || "",
    askedBy: "",
  };
}
// Change-order lines, approved FF&E selections and open field requests: the needs buyList did not read before P1.
// Runs inside withProject(p) from buyList.
function bbMoreNeeds(p, c, covered, rows) {
  c &&
    (c.changeOrders || [])
      .filter((x) => ["approved", "billed"].includes(x.status) && (!x.projectId || x.projectId === p.id))
      .forEach((d) =>
        (d.lines || []).forEach((l) => {
          if (l.parent) return;
          const key = `co:${d.id}:${l.id}`;
          if (covered.has(key)) return;
          const r = bbLineNeed(p, c, d, l, key, "co");
          r && rows.push(r);
        }),
      );
  // what is on order against a contract line and not yet here: the line's ordered part, arriving (its budget may be
  // fully committed, so the line itself is off To Buy). Lines a material or FF&E item stands for are read there.
  (DB.pos || [])
    .filter((po) => po.projectId === p.id && ["pending", "issued", "partial"].includes(po.status))
    .forEach((po) =>
      (po.lines || []).forEach((pl) => {
        if (pl.materialId || pl.selId || pl.requestId || !/^(estimate|co):/.test(pl.line || "") || (+pl.received || 0) >= (+pl.qty || 0)) return;
        const ref = findLine(pl.line),
          nb = ref ? lineNeedBy(p, ref.line) : { needBy: po.needBy || "", task: null };
        rows.push({
          kind: "order",
          src: "order",
          p: p,
          c: c,
          pl: pl,
          key: `po:${po.id}:${pl.id}`,
          presetLine: pl.line,
          name: pl.item || pl.desc || "Order line",
          needBy: nb.needBy || po.needBy || "",
          orderBy: "",
          lead: 0,
          task: nb.task,
          vendor: po.vendor || "",
          price: r2((+pl.qty || 0) * (+pl.price || 0)),
          budget: 0,
          held: 0,
          po: po,
          ordered: !0,
          eta: po.expected || "",
          dec: null,
          qty: `${r2((+pl.qty || 0) - (+pl.received || 0))} ${pl.unit || ""}`.trim(),
          code: pl.code || "",
          askedBy: "",
        });
      }),
    );
  ((DB.sel || {}).items || [])
    .filter((it) => it.projectId === p.id && ["appr", "po", "ord", "ship"].includes(it.stage))
    .forEach((it) => {
      const po = it.poId ? (DB.pos || []).find((x) => x.id === it.poId && "cancelled" !== x.status) : null,
        ordered = ["ord", "ship"].includes(it.stage) || (!!po && !["draft", "pending"].includes(po.status));
      let lead = 0;
      try {
        lead = selEffLead(it).days || +it.leadDays || 0;
      } catch (e) {
        lead = +it.leadDays || 0;
      }
      rows.push({
        kind: "ffe",
        src: "ffe",
        p: p,
        c: c,
        it: it,
        key: "sel:" + it.id,
        name: it.name,
        needBy: selNeedOnSite(it),
        orderBy: selOrderBy(it),
        lead: lead,
        task: selTask(it),
        vendor: it.vendor || "",
        price: selLineCost(it),
        budget: selLineCost(it),
        held: 0,
        po: po,
        ordered: ordered,
        eta: (it.dates || {}).eta || (po && po.expected) || "",
        dec: null,
        qty: `${+it.qty || 1} ${it.unit || "ea"}`,
        code: "",
        room: it.room || "",
        askedBy: "",
      });
    });
  (p.requests || [])
    .filter((q) => ["new", "ack", "ordered"].includes(q.status) && !q.materialId)
    .forEach((q) => {
      const po = q.poId ? (DB.pos || []).find((x) => x.id === q.poId && !["cancelled", "draft"].includes(x.status)) : null,
        lf = q.line ? lineFin(q.line) : null;
      rows.push({
        kind: "request",
        src: "request",
        p: p,
        c: c,
        q: q,
        key: "req:" + q.id,
        name: "function" == typeof reqLabel ? reqLabel(q) : q.what,
        needBy: q.neededBy || "",
        orderBy: q.neededBy ? addWork(q.neededBy, -1, !1) : "",
        lead: 1,
        task: q.taskId ? task(q.taskId) : null,
        vendor: (po && po.vendor) || "",
        price: lf ? Math.max(0, r2(lf.budget - lf.actual - lf.committed)) : 0,
        budget: lf ? lf.budget : 0,
        held: 0,
        po: po,
        ordered: !!po || "ordered" === q.status,
        eta: q.eta || (po && po.expected) || "",
        dec: null,
        qty: `${+q.qty || 1} ${q.unit || "ea"}`,
        code: (lf && lf.line && lf.line.code) || "",
        askedBy: q.by || "",
      });
    });
}
// The one place a need's late, section, tab and severity are decided.
function bbFinish(r) {
  const td = today();
  r.lineKey = r.presetLine ? r.presetLine : "line" === r.kind || "sub" === r.kind ? r.key : "material" === r.kind ? (r.m && r.m.line) || "" : "ffe" === r.kind ? (r.it && r.it.line) || "" : (r.q && r.q.line) || "";
  r.received = !!r.received;
  const L = bbLateOf(r);
  (r.late = L.late), (r.lateKind = L.kind), (r.lateWhy = L.why);
  // the quote out for it: a request's own RFQ, or one open on its line or FF&E item
  let rfqs = [];
  try {
    rfqs = r.ordered ? [] : ("request" === r.kind ? [r.q.rfqId && rfqById(r.q.rfqId)].filter((x) => x && !["awarded", "closed"].includes(x.status)) : rfqOpenOnLine(r.lineKey || r.key));
  } catch (e) {
    rfqs = [];
  }
  r.rfqs = rfqs;
  if (r.received) (r.section = "received"), (r.tab = "done");
  else if (!r.ordered)
    (r.tab = "buy"),
      (r.section = r.late ? "late" : rfqs.length ? "quotes" : r.orderBy && r.orderBy >= td && wd(td, r.orderBy) <= 5 ? "week" : "later");
  else if ("promise" === r.lateKind) (r.tab = "buy"), (r.section = "late");
  else (r.tab = "arriving"), (r.section = "arriving");
  r.arr =
    "arriving" !== r.tab
      ? ""
      : "overdue" === r.lateKind
        ? "late"
        : !r.eta
          ? "nodate"
          : r.eta === td
            ? "today"
            : wd(td, r.eta) <= 2
              ? "next2"
              : "later";
  r.sev = r.late
    ? 3
    : (!r.ordered && ("week" === r.section || r.dec || !r.vendor || !r.price)) || (r.ordered && !r.eta)
      ? 2
      : !r.ordered && !r.needBy
        ? 1
        : 0;
  r.why = r.late
    ? L.why
    : r.ordered
      ? r.eta
        ? `arriving ${fmt(r.eta)}`
        : "ordered, no date promised"
      : r.dec
        ? "waiting on decision"
        : "quotes" === r.section
          ? "waiting on quotes"
          : "week" === r.section
            ? `order by ${fmt(r.orderBy)}`
            : !r.needBy
              ? "no task date, link a task"
              : !r.vendor
                ? "no vendor"
                : !r.price
                  ? "no price"
                  : `order by ${fmt(r.orderBy)}`;
  r.id = ovBuyId(r);
  return r;
}
// "EST-2026-004 line 10", "CO-2026-001", "FF&E, Primary bath", "Material", "No line yet"
function bbLineLabel(r) {
  const ref = r.lineKey ? findLine(r.lineKey) : null,
    l = ref ? ref.line : r.l,
    d = ref ? ref.doc : r.d;
  if (d && l) return `${d.number || ""}${l.num ? ` line ${l.num}` : ""}`.trim();
  if ("ffe" === r.kind) return `FF&E${r.room ? `, ${r.room}` : ""}`;
  if ("sub" === r.kind) return "Subcontract";
  if ("request" === r.kind) return "No line yet";
  return "Material";
}
const bbJob = (p) => (p && p.project ? String(p.project.name).replace(/ —.*$/, "") : "");
const bbNum = (q) => {
  const m = String(q || "").match(/^\s*(\d+(?:\.\d+)?)\s*([a-zA-Z]*)/);
  return m ? { n: +m[1], unit: m[2] || "" } : { n: 0, unit: "" };
};
// What the shop holds for a need still to buy (the stock check every order runs), memoised per draw.
let bbStockMemo = { k: "", m: new Map() };
function bbStock(r) {
  if (r.ordered || "buy" !== r.tab || "function" != typeof stockCheck) return null;
  const k = String(SPD && SPD.ver);
  bbStockMemo.k !== k && (bbStockMemo = { k: k, m: new Map() });
  if (bbStockMemo.m.has(r.id)) return bbStockMemo.m.get(r.id);
  let out = null;
  try {
    const q = bbNum(r.qty);
    if (q.n > 0) {
      const S0 = stockCheck({ item: r.name.replace(/^\d+\.\s*/, ""), qty: q.n, unit: q.unit });
      S0 && S0.fromStock > 0 && (out = { from: S0.fromStock, buy: S0.toBuy, where: (S0.match && S0.match.where) || "the shop", reason: S0.reason });
    }
  } catch (e) {}
  return bbStockMemo.m.set(r.id, out), out;
}
// One chip per card: the reason that matters most, in plain words.
function bbChip(r) {
  if ("buy" !== r.tab) return null;
  if (r.ordered && "promise" === r.lateKind)
    return r.po ? { t: `${r.po.number} from ${r.po.vendor || r.vendor}: expedite, another vendor or move the task`, k: "red" } : { t: "Marked ordered with no order behind it", k: "red" };
  if (r.dec) return { t: `Waiting on a decision: ${r.dec.name || "open"}`, k: "amber" };
  if ("sub" === r.kind && !(r.rfqs || []).length) return { t: `No sub contracted: bids due before ${r.task ? r.task.name : "the work"} starts`, k: r.late ? "red" : "amber" };
  if ("request" === r.kind && !r.lineKey) return { t: `Asked from the site by ${r.askedBy || "the crew"}. No line yet`, k: "amber" };
  if ("request" === r.kind) return { t: `Asked from the site by ${r.askedBy || "the crew"}`, k: "blue" };
  if ((r.rfqs || []).length) {
    const q = r.rfqs[0],
      got = (q.quotes || []).length,
      asked = (q.vendors || []).length || (q.sent || []).length;
    return { t: `${q.number}: ${asked ? `${got} of ${asked} quotes in` : "not sent yet"}${q.dueDate ? `, due ${bbDay(q.dueDate)}` : ""}`, k: "blue" };
  }
  const st = bbStock(r);
  if (r.matUnknown) return { t: "Material portion not set: the line includes labour", k: "amber" };
  if (st) return { t: `${st.from} in stock at ${st.where}${st.buy > 0 ? `: buy ${st.buy}` : ": nothing to buy"}`, k: "blue" };
  if (!r.price) return { t: "No price yet", k: "amber" };
  return null;
}
// The day line on a card ("Order by Fri, passed", "Promised 9/25, needed on site 9/10", "Order by Wed").
function bbWhen(r) {
  if (r.late) return r.lateWhy;
  if (r.ordered) return r.eta ? `Promised ${fmt(r.eta)}` : "Ordered, no date promised";
  if (!r.orderBy) return r.needBy ? `Needed on site ${fmt(r.needBy)}` : "No task date yet";
  return `Order by ${bbDay(r.orderBy)}`;
}

// ---- the page --------------------------------------------------------------------------------------------------------
let bbTab = "buy",
  bbSel = "",
  bbPick = new Set(),
  bbQ = "",
  bbProj = "",
  bbVendor = "",
  bbTrade = "",
  bbFilter = "all",
  bbSearchOn = !1,
  bbFilterOn = !1,
  bbLastView = "";
const BB_SECTIONS = [
    ["late", "Late"],
    ["week", "Order This Week"],
    ["quotes", "Waiting on Quotes"],
    ["later", "Later"],
  ],
  BB_ARR = [
    ["late", "Late"],
    ["today", "Today"],
    ["next2", "Next 2 Working Days"],
    ["later", "Later"],
    ["nodate", "No Date Promised"],
  ];
const bbTradeOf = (r) => {
  if ("ffe" === r.kind) return (r.it && r.it.category) || "FF&E";
  const c = r.code && (COST_CODES.find((x) => x[0] === r.code) || [])[1];
  return c || (r.m && r.m.cat ? ("rough" === r.m.cat ? "Rough materials" : "Finish materials") : "Other");
};
// The rows a tab shows, after the project, vendor, trade and search filters (the tab counts are these rows).
function bbRowsFor(tab) {
  const q = bbQ.trim().toLowerCase(),
    f = "undefined" != typeof tlFocus && tlFocus.proc && "buy" === tlFocus.proc.grid ? tlFocus.proc : null;
  let R = buyList(f && null != f.scope ? f.scope : "").filter((r) => r.tab === tab);
  bbProj && (R = R.filter((r) => r.p.id === bbProj));
  bbVendor && (R = R.filter((r) => (r.vendor || "") === bbVendor));
  bbTrade && (R = R.filter((r) => bbTradeOf(r) === bbTrade));
  q && (R = R.filter((r) => `${r.name} ${r.vendor} ${bbJob(r.p)} ${bbLineLabel(r)} ${r.askedBy || ""}`.toLowerCase().includes(q)));
  return R;
}
const bbAll = () => buyList("").filter((r) => "buy" === r.tab || "arriving" === r.tab);
const bbFind = (id) => buyList("").find((r) => r.id === id) || null;
const BB_IC = {
  search: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>',
  filter: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M7 12h10M10 18h4"/></svg>',
  on: '<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="#2456C9"/><path d="M7.5 12.5l3 3 6-6.5" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  off: '<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.8" y="3.8" width="16.4" height="16.4" rx="4.5" fill="none" stroke="#B8BEC9" stroke-width="1.6"/></svg>',
  x: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
};
function bbPickBox(r) {
  const on = bbPick.has(r.id);
  return `<button type="button" class="bb-pick" data-bbpick="${esc(r.id)}" aria-pressed="${on}" aria-label="${on ? "Unpick" : "Pick"} ${esc(r.name)}">${on ? BB_IC.on : BB_IC.off}</button>`;
}
function bbChipHtml(r) {
  const c = bbChip(r);
  return c ? `<span class="bb-chip ${c.k}" data-nocase>${esc(c.t)}</span>` : "";
}
// phone card (Main.dc.html)
function bbCardHtml(r) {
  return `<div class="bb-card" data-bbrow="${esc(r.id)}">${bbPickBox(r)}<button type="button" class="bb-cbody" data-bbopen="${esc(r.id)}"><span class="bb-t" data-nocase>${esc(r.name)}</span><span class="bb-s" data-nocase>${esc([bbJob(r.p), r.vendor || "No vendor", r.qty, bbLineLabel(r)].filter(Boolean).join(" · "))}</span><span class="bb-w ${r.late ? "late" : ""}">${esc(bbWhen(r))}</span>${bbChipHtml(r)}</button></div>`;
}
// desktop row (Desk.dc.html): pick, need and line, project, qty, need by, where it stands
function bbRowHtml(r) {
  const c = bbChip(r),
    sub = c ? c.t : [r.vendor, r.price ? `${money(r.price)} ${r.ordered ? "on order" : "left on the line"}` : ""].filter(Boolean).join(" · "),
    stCls = r.late ? "late" : "quotes" === r.section ? "blue" : "";
  return `<div class="bb-row ${bbSel === r.id ? "sel" : ""}" data-bbrow="${esc(r.id)}">${bbPickBox(r)}<button type="button" class="bb-rbody" data-bbopen="${esc(r.id)}"><span class="bb-c1"><b data-nocase>${esc(r.name)}</b><span data-nocase>${esc(bbLineLabel(r))}</span></span><span class="bb-c2" data-nocase>${esc(bbJob(r.p))}</span><span class="bb-c3" data-nocase>${esc(r.qty || "—")}</span><span class="bb-c4 ${r.needBy && r.needBy < today() ? "late" : ""}">${r.needBy ? fmt(r.needBy) : "—"}</span><span class="bb-c5"><b class="${stCls}">${esc("quotes" === r.section ? "Quote out" : bbWhen(r))}</b><span data-nocase>${esc(sub)}</span></span></button></div>`;
}
// Arriving card (PhoneArriving.dc.html): what, vendor · project · order, the promise or reconfirmation, one action
function bbReconfirm(r) {
  const po = r.po;
  if (!po) return "";
  const f = (po.followups || []).filter((x) => "reconfirm" === x.type);
  const sent = f.filter((x) => "function" == typeof trkSent && trkSent(x)).pop();
  if (sent) return `Reconfirmed ${fmt(String(sent.sentAt || sent.at || sent.date || "").slice(0, 10)) || ""}`.trim();
  if (f.length) return "Reconfirmation drafted";
  return ["today", "next2"].includes(r.arr) ? "Not reconfirmed" : "";
}
function bbArrAct(r) {
  return "late" === r.arr ? "Chase" : "today" === r.arr && r.po ? "Receive" : "Open";
}
function bbArrHtml(r) {
  const rc = bbReconfirm(r),
    line = [r.late ? r.lateWhy : r.eta ? `Promised ${bbDay(r.eta)}` : "No date promised", rc].filter(Boolean).join(" · "),
    tone = r.late ? "late" : /^Reconfirmed/.test(rc) ? "ok" : rc ? "warn" : "";
  return `<div class="bb-arr" data-bbrow="${esc(r.id)}"><button type="button" class="bb-abody" data-bbopen="${esc(r.id)}"><span class="bb-t" data-nocase>${esc(r.name)}</span><span class="bb-s" data-nocase>${esc([r.vendor || "no vendor", bbJob(r.p), r.po ? r.po.number : "no order"].join(" · "))}</span><span class="bb-conf ${tone}">${esc(line)}</span></button><button type="button" class="btn bb-act" data-bbact="${esc(r.id)}">${bbArrAct(r)}</button></div>`;
}
function bbSectionsHtml(R, defs, key, phone) {
  return defs
    .map(([k, n]) => {
      const L = R.filter((r) => r[key] === k);
      if (!L.length) return "";
      return `<div class="bb-sec" data-bbsec="${k}"><div class="bb-sh ${"late" === k ? "late" : ""}"><span>${n.toUpperCase()}</span><i>${L.length}</i></div><div class="bb-box">${L.map((r) => ("arr" === key ? bbArrHtml(r) : phone ? bbCardHtml(r) : bbRowHtml(r))).join("")}</div></div>`;
    })
    .join("");
}
// The need's panel (desktop aside; the phone opens it as a sheet): where it stands, the money, the stock, what happened,
// and the next step as the one blue button.
function bbLastPrices(r) {
  const nm = "function" == typeof normItem ? normItem(r.name.replace(/^\d+\.\s*/, "")) : "";
  return (DB.pos || [])
    .filter((po) => !["cancelled", "draft"].includes(po.status))
    .flatMap((po) => (po.lines || []).filter((l) => (r.lineKey && l.line === r.lineKey) || (r.m && l.materialId === r.m.id) || (nm && normItem(l.item || "") === nm)).map((l) => ({ d: po.date || "", p: +l.price || 0, u: l.unit || "" })))
    .filter((x) => x.p > 0)
    .sort((a, b) => b.d.localeCompare(a.d))
    .slice(0, 3);
}
function bbHistory(r) {
  const H = [];
  r.po && H.push({ d: r.po.date || "", t: `Ordered, ${r.po.number}${r.po.createdBy ? `, by ${r.po.createdBy}` : ""}` });
  r.m && r.m.expedite && H.push({ d: r.m.expedite.at, t: `Expedited by ${r.m.expedite.by}${r.m.expedite.note ? `: ${r.m.expedite.note}` : ""}` });
  (r.rfqs || []).forEach((q) => H.push({ d: String(q.createdAt || "").slice(0, 10), t: `${q.number} started` }));
  r.q && (r.q.log || []).slice(-3).forEach((e) => H.push({ d: "", when: e.t, t: `${e.text}${e.by ? `, ${e.by}` : ""}` }));
  r.it && r.it.dates && ["approved", "ordered"].forEach((k) => r.it.dates[k] && H.push({ d: r.it.dates[k], t: "approved" === k ? "Approved by the client" : "Ordered" }));
  return H.sort((a, b) => String(b.d).localeCompare(String(a.d))).slice(0, 4);
}
// The next steps for a need: [label, action key], the first is the one blue button.
function bbSteps(r) {
  if ("arriving" === r.tab) return "late" === r.arr ? [["Chase the Vendor", "chase"], ["Open the Order", "po"]] : r.po ? [["today" === r.arr ? "Receive" : "Open the Order", "today" === r.arr ? "recv" : "po"], ["Chase the Vendor", "chase"]] : [["Expedite", "expedite"]];
  if (r.ordered && "promise" === r.lateKind) return [[`Expedite${r.vendor ? " " + r.vendor : ""}`, "expedite"], ["Other Vendor", "other"], ["Move the Task", "move"]];
  if (r.dec) return [["Get the Decision", "dec"]];
  const S1 = [];
  if ("request" === r.kind) {
    !r.lineKey && S1.push(["Link to a Line", "link"]);
    S1.push(["Order", "order"], ["Ask for Quotes", "quote"]);
    r.lineKey && S1.push(["Change the Line", "link"]);
    S1.push(["Open the Request", "req"]);
    return S1;
  }
  if ("sub" === r.kind) return (r.rfqs || []).length ? [["Open the Bids", "rfq"]] : [["Ask for Bids", "quote"]].concat(r.task ? [["Move the Task", "move"]] : []);
  if ((r.rfqs || []).length) return [["Open the Quote", "rfq"], ["Order", "order"]];
  S1.push(["Order", "order"]);
  (r.lineKey || "ffe" === r.kind) && S1.push(["Ask for Quotes", "quote"]);
  r.task && S1.push(["Move the Task", "move"]);
  return S1;
}
function bbOrderKey(r) {
  return `order|${r.p.id}|${r.d ? r.d.id : ""}|${"line" === r.kind ? r.key : ""}|${r.m ? r.m.id : ""}`;
}
function bbPanelHtml(r, picks) {
  if (!r) return '<div class="bb-empty" data-nocase>Pick a need to see its line, its money and what happened.</div>';
  const lf = r.lineKey ? lineFin(r.lineKey) : null,
    budget = lf ? lf.budget : r.budget,
    committed = lf ? lf.committed : r.po && "function" == typeof poTotal ? poTotal(r.po).total : 0,
    last = bbLastPrices(r),
    st = bbStock(r),
    H = bbHistory(r),
    steps = bbSteps(r),
    ref = [bbLineLabel(r), bbJob(r.p), r.task ? r.task.name : r.room || ""].filter(Boolean).join(" · "),
    lateBox = r.late
      ? `<div class="bb-latebox" data-nocase><b>${esc(r.ordered && r.needBy && r.eta ? `${dayDiff(r.needBy, r.eta)} days late to the site.` : r.lateWhy + ".")}</b><span data-nocase>${esc(
          r.ordered ? `${r.vendor || "No vendor"}${r.po ? `, ${r.po.number}` : ", no order behind it"}, promised ${fmt(r.eta)}.${r.task ? ` ${r.task.name} starts ${fmt(r.task.start)}.` : ""}` : `It is needed on site ${r.needBy ? fmt(r.needBy) : "soon"}${r.task ? ` for ${r.task.name}` : ""}; ${r.lead || 0} working days of lead time.`,
        )}</span></div>`
      : "",
    fix =
      r.ordered && "promise" === r.lateKind
        ? `<div class="bb-prop" data-nocase><b>The choices</b><span>Expedite with ${esc(r.vendor || "the vendor")}, order from another vendor who has it now, or move ${esc(r.task ? r.task.name : "the task")} to the promised date. The Standard: lead times are your schedule.</span></div>`
        : "",
    grid = [
      ["Line budget", budget ? money(budget) : "—"],
      ["Committed", money(committed || 0)],
      [`Last ${last.length || 3} buys`, last.length ? last.map((x) => `${money(x.p)}${x.u ? "/" + x.u : ""}`).join(", ") : "none on file"],
      ["At the shop", st ? `${st.from} in stock` : "none"],
      r.askedBy ? ["Asked by", r.askedBy] : null,
    ].filter(Boolean);
  return `<div class="bb-ph"><span class="bb-ref" data-nocase>${esc(ref)}</span><h3 data-nocase>${esc(r.name)}</h3></div>${lateBox}${fix}<div class="bb-grid" data-nocase>${grid.map(([k, v]) => `<span>${esc(k)}</span><b data-nocase>${esc(v)}</b>`).join("")}</div>${H.length ? `<div class="bb-hist" data-nocase><span class="bb-hh">WHAT HAPPENED</span>${H.map((h) => `<span><b>${esc(h.d ? fmt(h.d) : h.when || "")}</b> · <span data-nocase>${esc(h.t)}</span></span>`).join("")}</div>` : ""}<div class="bb-steps">${steps
    .map(([l, k], i) => `<button type="button" class="btn ${0 === i && !picks ? "primary" : ""}" data-bbstep="${k}" data-bbid="${esc(r.id)}"${"order" === k && ("material" === r.kind || "line" === r.kind) ? ` data-buy="${esc(bbOrderKey(r))}"` : ""}>${esc(l)}</button>`)
    .join("")}</div>`;
}
function bbRender() {
  const root = document.getElementById("proc-body");
  if (!root) return;
  const phone = mOn(),
    f = "undefined" != typeof tlFocus && tlFocus.proc && "buy" === tlFocus.proc.grid ? tlFocus.proc : null,
    BUY = bbRowsFor("buy"),
    ARR = bbRowsFor("arriving"),
    lateN = bbAll().filter((r) => r.late).length;
  let R = "buy" === bbTab ? BUY : ARR;
  // a tile elsewhere (Materials, Today, Ask) may open the board on one predicate: exactly those rows
  f && f.pred && ((R = R.filter((r) => { try { return !!f.pred(r); } catch (e) { return !1; } })), (f.n = R.length), (f.m = ("buy" === bbTab ? BUY : ARR).length));
  const chipN = (k) => ("all" === k ? R.length : R.filter((r) => r.section === k).length);
  "buy" === bbTab && "all" !== bbFilter && (R = R.filter((r) => r.section === bbFilter));
  [...bbPick].forEach((id) => R.some((r) => r.id === id) || BUY.some((r) => r.id === id) || bbPick.delete(id));
  const picked = [...bbPick].map(bbFind).filter(Boolean),
    sel = (bbSel && R.find((r) => r.id === bbSel)) || (!phone ? R[0] : null);
  sel && (bbSel = sel.id);
  const all = bbAll(),
    projs = [...new Map(all.map((r) => [r.p.id, bbJob(r.p)])).entries()],
    vendors = [...new Set(all.map((r) => r.vendor).filter(Boolean))].sort(),
    trades = [...new Set(all.map(bbTradeOf))].sort(),
    selOpt = (id, label, cur, L) => `<select id="${id}" aria-label="${label}"><option value="">${label}: All</option>${L.map(([v, n]) => `<option value="${esc(v)}" ${cur === v ? "selected" : ""}>${esc(n)}</option>`).join("")}</select>`,
    filters = `${selOpt("bb-proj", "Project", bbProj, projs)}${selOpt("bb-vendor", "Vendor", bbVendor, vendors.map((v) => [v, v]))}${selOpt("bb-trade", "Trade", bbTrade, trades.map((v) => [v, v]))}`,
    tabs = `<div class="seg bb-tabs" role="tablist" aria-label="Buy Board"><button type="button" role="tab" class="${"buy" === bbTab ? "on" : ""}" data-bbtab="buy" aria-selected="${"buy" === bbTab}">To Buy <span class="n">${BUY.length}</span></button><button type="button" role="tab" class="${"arriving" === bbTab ? "on" : ""}" data-bbtab="arriving" aria-selected="${"arriving" === bbTab}">Arriving <span class="n">${ARR.length}</span></button></div>`,
    chips =
      "buy" === bbTab && !phone
        ? `<div class="seg bb-chips">${[["all", "All"]].concat(BB_SECTIONS.filter(([k]) => "later" !== k)).map(([k, n]) => `<button type="button" class="${bbFilter === k ? "on" : ""} ${"late" === k ? "late" : ""}" data-bbf="${k}">${n} <span class="n">${chipN(k)}</span></button>`).join("")}</div>`
        : "",
    focus = f ? `<div class="bb-focus" data-nocase><span>${esc(f.label || "Filtered")}: ${R.length} of ${f.m}</span><button type="button" class="btn sm" id="bb-unfocus">Show All</button></div>` : "",
    list = "buy" === bbTab ? bbSectionsHtml(R, BB_SECTIONS, "section", phone) : bbSectionsHtml(R, BB_ARR, "arr", phone),
    empty = R.length ? "" : `<div class="bb-none">${"buy" === bbTab ? (BUY.length ? "Nothing in this filter." : "Nothing to buy. Every need is ordered.") : "Nothing on order."}</div>`,
    bar = picked.length
      ? `<div class="bb-bar"><span><b>${picked.length} line${1 === picked.length ? "" : "s"}</b> picked</span><button type="button" class="btn" id="bb-quote">Ask for Quotes</button><button type="button" class="btn primary" id="bb-order">Order ${picked.length} Line${1 === picked.length ? "" : "s"}</button></div>`
      : "",
    head = `<div class="ph bb-ph0"><div class="bb-title"><h2>Buy Board</h2><span class="ov-count bb-latepill ${lateN ? "on" : ""}" data-ovneeds="buy">${lateN ? `${lateN} late` : "Nothing late"}</span></div><div class="bb-tools">${phone ? "" : `<label class="bb-search">${BB_IC.search}<input id="bb-q" aria-label="Search needs, vendors and lines" placeholder="Search needs, vendors, lines" value="${esc(bbQ)}"></label>`}${phone ? `<button type="button" class="bb-ib" id="bb-sbtn" aria-label="Search the Buy Board">${BB_IC.search}</button><button type="button" class="bb-ib ${bbProj || bbVendor || bbTrade ? "on" : ""}" id="bb-fbtn" aria-label="Filter by project, vendor or trade">${BB_IC.filter}</button>` : `<button type="button" class="btn" id="bb-more">FF&amp;E Buying Tools</button>`}</div></div>`,
    phoneTools = phone && (bbSearchOn || bbFilterOn || bbQ) ? `<div class="bb-ptools">${bbSearchOn || bbQ ? `<input id="bb-q" aria-label="Search needs, vendors and lines" placeholder="Search needs, vendors, lines" value="${esc(bbQ)}">` : ""}${bbFilterOn ? `<div class="bb-fl">${filters}</div>` : ""}</div>` : "";
  root.innerHTML = `<div class="bb ${phone ? "bb-phone" : "bb-desk"} ${picked.length ? "bb-picking" : ""}" id="buy-board" data-bbon="${bbTab}" data-os-keep>${head}<div class="bb-top">${tabs}${phone ? "" : `${chips}<span class="bb-sep"></span><div class="bb-fl">${filters}</div>`}</div>${phoneTools}${focus}<div class="bb-main"><div class="bb-list" data-nocase>${list}${empty}<div class="dg bb-foot"><span class="cnt">${R.length} of ${("buy" === bbTab ? BUY : ARR).length} shown</span>${phone ? `<button type="button" class="btn sm" id="bb-more">FF&amp;E Buying Tools</button>` : ""}</div></div>${phone ? "" : `<aside class="bb-panel" aria-label="${esc(sel ? sel.name : "The need")}">${bbPanelHtml(sel, picked.length)}</aside>`}</div>${bar}</div>`;
  bbWire(root);
}
function bbWire(root) {
  const q = (s) => root.querySelector(s),
    re = () => render(),
    tb = document.getElementById("mtabs");
  // the pick bar rides just above the phone's bottom bar, as in Main.dc.html
  tb && root.firstElementChild && root.firstElementChild.style.setProperty("--bb-tabs", (tb.offsetHeight || 64) + "px");
  root.querySelectorAll("[data-bbtab]").forEach((b) => b.matches("button") && (b.onclick = () => ((bbTab = b.dataset.bbtab), (bbSel = ""), re())));
  root.querySelectorAll("[data-bbf]").forEach((b) => (b.onclick = () => ((bbFilter = b.dataset.bbf), re())));
  root.querySelectorAll("[data-bbpick]").forEach((b) => (b.onclick = (e) => (e.stopPropagation(), bbPick.has(b.dataset.bbpick) ? bbPick.delete(b.dataset.bbpick) : bbPick.add(b.dataset.bbpick), re())));
  root.querySelectorAll("[data-bbopen]").forEach(
    (b) =>
      (b.onclick = () => {
        const r = bbFind(b.dataset.bbopen);
        if (!r) return;
        mOn() ? bbSheet(r) : ((bbSel = r.id), re());
      }),
  );
  root.querySelectorAll("[data-bbact]").forEach((b) => (b.onclick = () => bbDo(bbFind(b.dataset.bbact), "Chase" === b.textContent ? "chase" : "Receive" === b.textContent ? "recv" : "open")));
  root.querySelectorAll("[data-bbstep]").forEach((b) => (b.onclick = () => bbDo(bbFind(b.dataset.bbid), b.dataset.bbstep)));
  [["#bb-proj", (v) => (bbProj = v)], ["#bb-vendor", (v) => (bbVendor = v)], ["#bb-trade", (v) => (bbTrade = v)]].forEach(([s, set]) => {
    const el = q(s);
    el && (el.onchange = () => (set(el.value), re()));
  });
  const qi = q("#bb-q");
  qi &&
    (qi.oninput = () => {
      bbQ = qi.value;
      clearTimeout(bbWire.t);
      bbWire.t = setTimeout(() => {
        re();
        const n = document.querySelector("#bb-q");
        n && (n.focus(), n.setSelectionRange(n.value.length, n.value.length));
      }, 250);
    });
  q("#bb-sbtn") && (q("#bb-sbtn").onclick = () => ((bbSearchOn = !bbSearchOn), re()));
  q("#bb-fbtn") && (q("#bb-fbtn").onclick = () => ((bbFilterOn = !bbFilterOn), re()));
  q("#bb-unfocus") && (q("#bb-unfocus").onclick = () => (delete tlFocus.proc, re()));
  q("#bb-more") && (q("#bb-more").onclick = () => ((procMode = "finish"), re()));
  q("#bb-order") && (q("#bb-order").onclick = () => bbOrderPicked());
  q("#bb-quote") && (q("#bb-quote").onclick = () => bbQuotePicked());
}
// The phone's need sheet: the same panel, as a bottom sheet.
function bbSheet(r) {
  const m = mbModal(esc(r.name), `<div class="bb-sheet">${bbPanelHtml(r, 0).replace(/<div class="bb-ph">[\s\S]*?<\/div>/, `<div class="bb-ph"><span class="bb-ref" data-nocase>${esc([bbLineLabel(r), bbJob(r.p)].join(" · "))}</span></div>`)}</div>`, { submit: null });
  m.classList.add("bb-mbm");
  m.querySelectorAll("[data-bbstep]").forEach((b) => (b.onclick = () => (mbCloseModal(), bbDo(r, b.dataset.bbstep))));
  return m;
}
// ---- what the buttons do: each routes to the path that already exists (P2 makes one order sheet) ----------------------
function bbDo(r, k) {
  if (!r) return toast("That need is no longer on the Buy Board");
  const p = r.p;
  if ("open" === k) return r.po ? flowGo.po(r.po)() : ((bbSel = r.id), (bbTab = r.tab), setView("proc"));
  if ("order" === k) return bbOrder([r]);
  if ("quote" === k) return bbQuote([r]);
  if ("dec" === k) return setCurrent(p.id), (view = "dec"), render();
  if ("rfq" === k) return r.rfqs && r.rfqs[0] ? rfqOpenFor(r.rfqs[0].id) : setView("rfq");
  if ("req" === k) return setCurrent(p.id), (view = "req"), render();
  if ("link" === k) return bbLinkLine(r);
  if ("po" === k) return r.po ? flowGo.po(r.po)() : toast("No order behind it yet");
  if ("recv" === k) return setCurrent(p.id), r.po && (poOpen = null), (view = "recv"), render();
  if ("move" === k) return bbMoveTask(r);
  if ("other" === k) return bbOtherVendor(r);
  if ("expedite" === k || "chase" === k) return bbExpedite(r, k);
}
function bbOrder(L) {
  const R = L.filter(Boolean);
  if (!R.length) return toast("Pick at least one line");
  const jobs = new Set(R.map((r) => r.p.id));
  if (jobs.size > 1) return toast(`Order one job at a time: these lines are on ${jobs.size} jobs`);
  const pid = R[0].p.id,
    held = R.find((r) => r.dec);
  if (held) return toast(`${held.name} waits on a decision; it can be ordered once it is made`);
  const sub = R.find((r) => "sub" === r.kind);
  if (sub) return toast(`${sub.name} is a subcontract scope: Ask for Bids, then award it as a subcontract`);
  if (R.some((r) => r.ordered)) return toast(`${R.find((r) => r.ordered).name} is on order already: expedite it or pick another vendor`);
  const ffe = R.filter((r) => "ffe" === r.kind),
    req = R.filter((r) => "request" === r.kind),
    rest = R.filter((r) => "ffe" !== r.kind && "request" !== r.kind);
  if (ffe.length && (req.length || rest.length)) return toast("Order the FF&E items on their own: they go on one order per vendor through the buy run");
  if (ffe.length) return (procSel = new Set(ffe.map((r) => r.it.id))), procRunModal(), bbPick.clear();
  if (req.length > 1 || (req.length && rest.length)) return toast("Order a field request on its own: it becomes a material and an order");
  if (req.length) {
    const r = req[0];
    return bbPick.clear(), requestAction(pid, r.q.id, "po"), void setTimeout(() => render(), 0);
  }
  if (1 === rest.length) return bbPick.clear(), buyOrderDialog({ pid: pid, mid: rest[0].m ? rest[0].m.id : "", key: "line" === rest[0].kind ? rest[0].key : "" });
  const keys = rest.map((r) => r.lineKey).filter(Boolean);
  if (keys.length < rest.length) return toast(`${rest.find((r) => !r.lineKey).name} has no line to order against: order it on its own`);
  return bbPick.clear(), ctPOPicker(pid, "*", keys);
}
const bbOrderPicked = () => bbOrder([...bbPick].map(bbFind));
function bbQuote(L) {
  const R = L.filter(Boolean);
  if (!R.length) return toast("Pick at least one line");
  const jobs = new Set(R.map((r) => r.p.id));
  if (jobs.size > 1) return toast(`Ask for quotes one job at a time: these lines are on ${jobs.size} jobs`);
  const pid = R[0].p.id,
    req = R.filter((r) => "request" === r.kind);
  if (req.length) {
    if (R.length > 1) return toast("Ask for quotes on a field request on its own");
    return bbPick.clear(), reqRfq(pid, req[0].q.id);
  }
  const keys = R.map((r) => ("ffe" === r.kind ? "sel:" + r.it.id : r.lineKey)),
    miss = R.find((r, i) => !keys[i]),
    subs = R.filter((r) => "sub" === r.kind);
  if (miss) return toast(`${miss.name} has no estimate or change-order line to quote from`);
  if (subs.length && subs.length !== R.length) return toast("Ask for bids on a subcontract scope on its own: it is leveled by scope, not by price per item");
  const trade = subs.length ? ((COST_CODES.find((c) => c[0] === subs[0].code) || [])[1] || "Subcontract").split(/[ &,]/)[0] : "",
    q = rfqFromLines(pid, keys, subs.length ? { sub: !0, category: trade } : {});
  // the RFQ line names the material it buys, so the award marks that material ordered
  q &&
    R.forEach((r) => {
      if (!r.m) return;
      (q.lines || []).forEach((l) => (l.fromLine === r.lineKey || l.line === r.lineKey) && !l.materialId && (l.materialId = r.m.id));
    });
  q && (bbPick.clear(), save());
  return q;
}
const bbQuotePicked = () => bbQuote([...bbPick].map(bbFind));
// Expedite or chase: a material keeps its own sheet (buyExpedite); anything on an order gets a drafted chase to the
// vendor, which a person sends (AI assists, people commit).
function bbExpedite(r, k) {
  if (r.m && !r.po) return buyExpedite(r.p, r.m.id);
  const v = (DB.vendors || []).find((x) => x.name === (r.vendor || (r.po && r.po.vendor)));
  if (!v) return toast(`${r.name} has no vendor on file to chase: set the vendor on the order first`);
  const job = bbJob(r.p);
  eaNudge({
    kind: "expedite",
    t: `${v.name} — ${r.name}`,
    vendor: v,
    subject: `${r.po ? r.po.number + " " : ""}${r.name} for ${job} — ${"chase" === k ? "where is it" : "delivery date"}`,
    msg:
      "chase" === k
        ? `Hi — ${r.po ? r.po.number : "our order"} (${r.name}) was promised for ${fmtL(r.eta)} and has not arrived at ${job}. Please confirm today when it will be delivered. Thanks.`
        : `Hi — the site needs ${r.name} by ${r.needBy ? fmtL(r.needBy) : "the earliest date you can"}, and ${r.po ? r.po.number : "the order"} is promised for ${fmtL(r.eta)}. Can you ship it sooner, in part or in full? Please reply today. Thanks.`,
  });
}
function bbOtherVendor(r) {
  if (r.lineKey || "ffe" === r.kind) return bbQuote([r]);
  if (r.m) return toast(`Link ${r.name} to its estimate line to ask other vendors, or order it from another vendor on the order sheet`), openEditor("mat", r.m.id);
  return toast("Ask other vendors from the Quotes page"), setView("rfq");
}
function bbMoveTask(r) {
  const t = r.task;
  if (!t) return toast(`${r.name} has no schedule task to move`);
  setCurrent(r.p.id);
  try {
    openEditor("task", t.id);
  } catch (e) {
    (view = "sched"), render();
  }
  r.eta && toast(`${t.name} starts ${fmt(t.start)}; the promise is ${fmt(r.eta)}. Move it, and the schedule moves what follows`);
}
// A field request gets its line from the coordinator: the job's estimate, change-order and FF&E lines, those that match
// the request's words first, one tap to link. Nothing is linked by guess.
function bbLineSuggest(r) {
  const words = new Set(String(r.name || "").toLowerCase().split(/[^a-z0-9]+/).filter((w) => w.length > 2));
  let S0 = [];
  try {
    S0 = rfqLineSources(r.p.id);
  } catch (e) {}
  return S0.map((s) => {
    const it = String(`${s.item} ${s.spec || ""}`).toLowerCase(),
      hit = [...words].filter((w) => it.includes(w)).length,
      tk = r.task && r.task.trade && s.code && ((COST_CODES.find((c) => c[0] === s.code) || [])[2] || []).includes(r.task.trade) ? 1 : 0;
    return { s: s, score: hit * 2 + tk };
  }).sort((a, b) => b.score - a.score);
}
function bbLinkLine(r) {
  if ("request" !== r.kind) return toast("Only a field request is linked by hand; the others carry their line");
  const L = bbLineSuggest(r),
    cur = r.q.line || "";
  const m = mbModal(
    `Link to a Line — <span data-nocase>${esc(r.name)}</span>`,
    `<p class="small muted" style="margin:0 0 8px">${esc(r.askedBy || "The crew")} asked for ${esc(r.qty)} for ${esc(bbJob(r.p))}. Pick the line it is bought for; the best matches are first. The order and the bill then cost to that line.</p><div class="bb-links">${L.map(({ s: s, score: sc }, i) => `<label class="bb-link"><input type="radio" name="bbl" data-bbl="${esc(s.key)}" ${s.key === cur || (!cur && 0 === i && sc > 0) ? "checked" : ""}><span><b data-nocase>${esc(s.item)}</b><span class="small muted" data-nocase>${esc(s.docNo || "Selection")}${sc > 1 ? " · matches the request" : ""}${null != s.budget ? ` · ${money(s.budget)}` : ""}</span></span></label>`).join("") || '<p class="small muted">This job has no approved estimate, change-order or FF&amp;E lines yet.</p>'}</div>`,
    {
      submit: "Link the Line",
      onSubmit: () => {
        const el = m.querySelector("[data-bbl]:checked");
        if (!el) return toast("Pick a line"), !1;
        const key = el.dataset.bbl,
          s = L.find((x) => x.s.key === key);
        r.q.line = key;
        (r.q.log = r.q.log || []).push({ t: "function" == typeof nowStamp ? nowStamp() : appNowIso(), by: ((currentUser() || {}).name) || role(), text: `Linked to ${s ? `${s.s.docNo || "Selection"} · ${s.s.item}` : key}` });
        try {
          audit("request", r.q.id, "line linked", cur, key);
        } catch (e) {}
        save(), render();
        rcToast(`${r.name} is bought for ${s ? s.s.item : key}`, [{ label: "Open", run: () => ((bbSel = ovBuyId(Object.assign({}, r, { key: "req:" + r.q.id }))), setView("proc")) }]);
      },
    },
  );
  return m;
}
// After an order is made for needs (an RFQ award today; P2's one order sheet next): the request, the material and the
// FF&E item it is for read "ordered" on that order, with its promised date.
function bbAfterOrder(po, why) {
  if (!po) return;
  const p = (DB.projects || []).find((x) => x.id === po.projectId),
    live = !["draft", "cancelled"].includes(po.status),
    issued = ["issued", "partial", "received"].includes(po.status),
    by = ((currentUser() || {}).name) || role();
  (po.lines || []).forEach((l) => {
    const q = p && l.requestId && (p.requests || []).find((x) => x.id === l.requestId);
    q &&
      ((q.poId = po.id),
      po.expected && (q.eta = po.expected),
      (q.path = "order"),
      issued && ["new", "ack"].includes(q.status) ? (q.status = "ordered") : "new" === q.status && ((q.status = "ack"), (q.ackBy = q.ackBy || by), (q.ackAt = q.ackAt || appNowIso())),
      l.line && !q.line && (q.line = l.line),
      (q.log = q.log || []).push({ t: "function" == typeof nowStamp ? nowStamp() : appNowIso(), by: by, text: `${issued ? "Ordered" : "On"} ${po.number} from ${po.vendor}${po.expected ? `, promised ${fmt(po.expected)}` : ""}${why ? ` (${why})` : ""}` }));
    const m = p && l.materialId && (p.materials || []).find((x) => x.id === l.materialId);
    m &&
      live &&
      ((m.po = po.number),
      (m.vendor = m.vendor || po.vendor),
      issued && "on-site" !== m.status && (m.status = "ordered"),
      po.expected && (m.eta = po.expected));
    const it = l.selId && ((DB.sel || {}).items || []).find((x) => x.id === l.selId);
    it && live && ((it.poId = po.id), SEL_OPEN.includes(it.stage) && (it.stage = issued ? "ord" : "po"), issued && ((it.dates = it.dates || {}), (it.dates.ordered = it.dates.ordered || today()), po.expected && (it.dates.eta = po.expected)));
  });
}
// One path per field request (buying day finding 2): an order, the driver's store run, or stock. Choosing one closes the
// others: an ordered request leaves the driver's list (runItems), and a request bought on the run or taken from stock
// cancels any order still drafted or waiting for approval for it, so the same studs are never bought twice.
function bbReqPath(p, r, path, why) {
  if (!r) return [];
  r.path = path;
  const D = (DB.pos || []).filter((po) => ["draft", "pending"].includes(po.status) && (po.id === r.poId || (po.lines || []).some((l) => l.requestId === r.id || (r.materialId && l.materialId === r.materialId))));
  D.forEach((po) => {
    (po.status = "cancelled"), (po.cancelReason = `Superseded: the request was ${why}`), (po.supersededAt = appNowIso());
    try {
      audit("po", po.id, "superseded", "draft", "cancelled", `request ${r.id} ${why}`);
    } catch (e) {}
  });
  const m = r.materialId && p && (p.materials || []).find((x) => x.id === r.materialId);
  m && "on-site" !== m.status && ("stock" === path ? ((m.status = "on-site"), (m.onSiteDate = today())) : ((m.status = "ordered"), (m.eta = today()), (m.po = ""), (m.notes = `${m.notes ? m.notes + " · " : ""}${why}`)));
  D.length &&
    rcToast(`${D.map((x) => x.number).join(", ")} cancelled: ${r.what || "the request"} was ${why}, so it is not bought twice`, [{ label: "Open", run: flowGo.po(D[0]) }]);
  return D;
}
// The page: the Buy Board, or the FF&E buying tools behind its More until P4 folds returns and credits into Issues.
{
  const bbProcTools = renderProc;
  renderProc = function () {
    bbLastView !== "proc" && "proc" === view && "finish" === procMode && bbLastView && (procMode = "lines");
    bbLastView = view;
    if ("finish" === procMode) {
      bbProcTools.apply(this, arguments);
      const root = document.getElementById("proc-body");
      root &&
        !root.querySelector("#bb-back") &&
        root.insertAdjacentHTML("afterbegin", '<div class="bb-back"><button type="button" class="btn sm" id="bb-back">Back to the Buy Board</button><span class="small muted">FF&amp;E buying tools: buy runs, receiving, returns and credits. Approved FF&amp;E items are on the Buy Board.</span></div>');
      root && root.querySelector("#bb-back") && (root.querySelector("#bb-back").onclick = () => ((procMode = "lines"), render()));
      return;
    }
    bbRender();
  };
}
// The Purchasing overview's rows are the Buy Board's: the overview hands over to the board for every role that may open it.
"object" == typeof OC_RETIRED && (OC_RETIRED.ovbuy = "proc");
// The Buy Board's badge, on the rail, the sub-tab and the phone bar: the one late set (needs("buy")).
"object" == typeof OC_BADGE && (OC_BADGE.proc = { n: () => ("function" == typeof needs ? needs("buy") : 0) });

// ---- Today and Do Now: the coordinator's Buy Board lines (tdyBuyItems reads these) -------------------------------------
// Late, or due to order this week, from the one reader; a field request not yet acknowledged is an Approvals card
// (kind "req"), so it is not listed twice.
function bbTodayItems() {
  let X = null;
  try {
    X = tdFacts().X || b2Facts(briefFacts());
  } catch (e) {
    return [];
  }
  const seen = new Set(),
    out = [],
    pm = "pm" === role(),
    me = ((currentUser() || {}).name || "").toLowerCase(),
    mine = (p) => !pm || !p.project.pm || String(p.project.pm).toLowerCase().includes(me.split(" ")[0]);
  // the PM sees the late needs on his own jobs (buying day: he saw none of the coordinator's orders); the coordinator
  // owes the late ones and those due to order this week
  ((X && X.buyLate) || []).concat(pm ? [] : (X && X.buyWeek) || []).forEach((x) => {
    const id = x.id || ovBuyId(x);
    if (seen.has(id) || ("request" === x.kind && "new" === x.q.status) || !mine(x.p)) return;
    seen.add(id);
    const ea = x.dec
      ? { view: "dec", proj: x.p.id }
      : x.ordered
        ? { fix: id }
        : "material" === x.kind || "line" === x.kind
          ? { order: { pid: x.p.id, mid: x.m ? x.m.id : "", key: "line" === x.kind ? x.key : "" } }
          : "sub" === x.kind && !(x.rfqs || []).length
            ? { bids: id }
            : { board: id };
    out.push({
      kind: "tdyBuy",
      id: id,
      src: "buy",
      x: x,
      title: `${x.name} — ${shortName(x.p)}`,
      detail: x.dec ? `held by a decision${x.orderBy ? ` · order-by ${fmt(x.orderBy)}${x.late ? " passed" : ""}` : ""}` : (x.late ? x.lateWhy : bbWhen(x)).replace(/^./, (c) => c.toLowerCase()),
      due: x.orderBy || "",
      ea: ea,
    });
  });
  return out;
}
// The card: Order for a line still to buy, Fix for an ordered one whose promise is late (Expedite, Other Vendor, Move
// the Task), Decide for one held by a decision, Open for the rest.
function bbTodayCard(it) {
  const x = it.x,
    open = () => ((bbSel = it.id), (bbTab = x.tab || "buy"), mOn() ? (setView("proc"), setTimeout(() => bbSheet(bbFind(it.id) || x), 0)) : setView("proc")),
    go = it.ea.order ? () => buyOrderDialog(it.ea.order) : it.ea.view ? () => (setCurrent(x.p.id), (view = "dec"), render()) : it.ea.bids ? () => bbQuote([bbFind(it.id) || x]) : open;
  return { line1: `<a href="#" data-tdrec>${esc(tdWords(it.title, 12))}</a>`, why: esc(`Buy Board · ${it.detail}`), verb: it.ea.order ? "Order" : it.ea.view ? "Decide" : it.ea.fix ? "Fix" : it.ea.bids ? "Ask for Bids" : "Open", go: open, run: go, ea: it.ea };
}

// ---- the job's buying, on its Overview: late needs and open orders on this job, for whoever runs the job --------------
function bbJobCardHtml(p) {
  const late = buyList(p.id).filter((r) => r.late),
    pos = (DB.pos || []).filter((po) => po.projectId === p.id && ["pending", "issued", "partial"].includes(po.status)),
    rows = late
      .slice(0, 4)
      .map((r) => `<button type="button" class="bb-jrow" data-bbjob="${esc(r.id)}"><span class="grow"><b data-nocase>${esc(r.name)}</b><span class="small bad" data-nocase>${esc(r.lateWhy)}</span></span></button>`)
      .concat(
        pos
          .slice(0, 4)
          .map((po) => `<button type="button" class="bb-jrow" data-bbjpo="${esc(po.id)}"><span class="grow"><b data-nocase>${esc(po.number)} · ${esc(po.vendor || "no vendor")}</b><span class="small muted" data-nocase>${money(poTotal(po).total)} · ${"pending" === po.status ? "waiting for approval" : po.expected ? `promised ${fmt(po.expected)}` : "no date promised"}</span></span></button>`),
      );
  return `<div class="card bb-job" id="bb-job"><div class="hd"><h3>Buying on This Job</h3><span class="small muted">${late.length} late · ${pos.length} order${1 === pos.length ? "" : "s"} open</span><button type="button" class="btn sm" id="bb-job-all">Open the Buy Board</button></div>${rows.join("") || '<p class="small muted">Nothing late, nothing on order.</p>'}</div>`;
}
if ("function" == typeof renderDash) {
  const base = renderDash;
  renderDash = function () {
    const out = base.apply(this, arguments);
    try {
      const v = document.getElementById("v-dash");
      if (v && S && ["owner", "pm", "coord"].includes(role()) && (ROLE_VIEWS[role()] || []).includes("proc")) {
        const old = v.querySelector("#bb-job");
        old && old.remove();
        const ph = v.querySelector(".ph");
        ph ? ph.insertAdjacentHTML("afterend", bbJobCardHtml(S)) : v.insertAdjacentHTML("afterbegin", bbJobCardHtml(S));
        const c = v.querySelector("#bb-job"),
          pid = S.id;
        c.querySelector("#bb-job-all").onclick = () => ((bbProj = pid), (bbTab = "buy"), (bbFilter = "all"), setView("proc"));
        c.querySelectorAll("[data-bbjob]").forEach((b) => (b.onclick = () => ((bbProj = pid), (bbSel = b.dataset.bbjob), (bbTab = "buy"), setView("proc"))));
        c.querySelectorAll("[data-bbjpo]").forEach((b) => (b.onclick = () => flowGo.po((DB.pos || []).find((x) => x.id === b.dataset.bbjpo))()));
      }
    } catch (e) {
      console.warn("job buying card", e);
    }
    return out;
  };
}
// ---- the driver's route waits on the coordinator: an Approvals card and a Do Now item, due before the van leaves (F6) --
"object" == typeof DELEGATION &&
  (DELEGATION.route = { role: "coord", rule: "the driver's planned route and store buys wait on the coordinator's approval before the van leaves" });
function bbRouteWaiting() {
  if ("function" != typeof ciRoutePlanNow) return null;
  let N = null;
  try {
    N = ciRoutePlanNow();
  } catch (e) {
    return null;
  }
  if (!N || !N.plan || !(N.plan.stops || []).length) return null;
  const run = "function" == typeof ciRunFor ? ciRunFor(N.date) : null;
  if (run && "approved" === run.status && !("function" == typeof ciRunStale && ciRunStale(run))) return null;
  const leave = "undefined" != typeof CI_ROUTE ? CI_ROUTE.startMin : 420,
    hh = Math.floor(leave / 60),
    mm = String(leave % 60).padStart(2, "0"),
    driver = ((DB.users || []).find((u) => "driver" === u.role) || {}).name || "the driver";
  return { N: N, run: run, driver: driver, leave: `${hh > 12 ? hh - 12 : hh}:${mm} ${hh >= 12 ? "PM" : "AM"}`, stale: !!run };
}
{
  const base = mApprovals;
  mApprovals = function (opts) {
    const out = base.apply(this, arguments);
    try {
      if (!Array.isArray(out) || !((opts && opts.everyone) || "coord" === role())) return out;
      const W = bbRouteWaiting();
      if (!W) return out;
      const P = W.N.plan,
        first = W.driver.split(" ")[0];
      return out.concat([
        {
          kind: "route",
          id: "route:" + W.N.date,
          sev: "warn",
          n: "Route",
          title: `Approve ${first}'s route`,
          detail: `${W.stale ? "the list changed since it was approved · " : ""}${P.stops.length} stop${1 === P.stops.length ? "" : "s"}${(P.stores || []).length ? `, buying at ${P.stores.join(" and ")}` : ""} · due before the van leaves at ${W.leave}`,
          yes: "Approve Route",
          who: "coord",
          due: W.N.date,
          open: { view: "route" },
        },
      ]);
    } catch (e) {
      return out;
    }
  };
}
{
  const base = tdCard;
  tdCard = function (it) {
    if (it && "tdyBuy" === it.kind) return bbTodayCard(it);
    const c = base.apply(this, arguments);
    try {
      it && "route" === it.kind && ((c.line1 = esc(it.title)), (c.why = esc(it.detail || "")), (c.verb = it.yes), (c.run = () => ciApproveRoute()), (c.go = () => setView("route")));
    } catch (e) {}
    return c;
  };
}
"function" == typeof tdScore &&
  (() => {
    const base = tdScore;
    tdScore = function (it) {
      // the van waits on it: right after the field's own questions
      return it && "route" === it.kind ? 57 : base.apply(this, arguments);
    };
  })();

// ---- Ask: the coordinator's buying questions, answered from the one reader --------------------------------------------
const BB_ASK = [
  {
    id: "late",
    rx: /\b(what'?s|what is|which|anything|items?|lines?)\b.*\blate\b.*\b(order|buy|buying|board|materials?)\b|\blate to (order|buy)\b|\bpast (its|their|the)? ?order[- ]?by\b|\bbuy board\b.*\blate\b/,
    answer: () => {
      const R = PRED.lateMaterial.rows(),
        o = R.filter((r) => !r.ordered).length,
        pr = R.filter((r) => "promise" === r.lateKind).length,
        ov = R.filter((r) => "overdue" === r.lateKind).length;
      return {
        headline: R.length ? `${agN(R.length, "need")} late on the Buy Board: ${[o ? `${o} not ordered by the order-by date` : "", pr ? `${pr} promised after the site needs ${1 === pr ? "it" : "them"}` : "", ov ? `${ov} promised and not here` : ""].filter(Boolean).join(", ")}.` : "Nothing is late on the Buy Board.",
        work: R.map((r) => `${r.name} (${bbJob(r.p)}): ${r.lateWhy}`),
        go: { view: "proc" },
        n: R.length,
      };
    },
  },
  {
    id: "arriving",
    rx: /\b(what'?s|what|which)\b.*\b(arriv\w*|coming|due in|delivered)\b.*\b(this week|week)\b/,
    answer: () => {
      const td = today(),
        end = iso(addDays(parse(td), 7 - (parse(td).getDay() || 7))),
        R = PRED.arrivingNeeds.rows().filter((r) => r.eta && r.eta <= end && !r.late),
        pos = (DB.pos || []).filter((po) => !["cancelled", "draft", "received"].includes(po.status) && po.expected && po.expected >= td && po.expected <= iso(addDays(parse(td), 7))),
        late = PRED.arrivingNeeds.rows().filter((r) => "overdue" === r.lateKind);
      return {
        headline: `${agN(pos.length, "delivery", "deliveries")} due in the next 7 days; ${agN(R.length, "line")} on the Buy Board arrive${1 === R.length ? "s" : ""} by ${fmt(end)}${late.length ? `, and ${late.length} promised earlier ${1 === late.length ? "is" : "are"} not here` : ""}.`,
        work: R.map((r) => `${r.name} (${bbJob(r.p)}): ${r.vendor || "no vendor"}${r.po ? `, ${r.po.number}` : ""}, promised ${fmt(r.eta)}`).concat(pos.map((po) => `${po.number} · ${po.vendor}: ${fmt(po.expected)}`)),
        go: { view: "proc" },
        n: R.length,
      };
    },
  },
  {
    id: "quotes",
    rx: /\b(which|what)\b.*\bquotes?\b.*\b(waiting|wait|out|pending|open)\b|\bwaiting on quotes?\b/,
    answer: () => {
      const Q = rfqInit().filter((r) => typeof RFQ_OPEN !== "undefined" && (RFQ_OPEN.includes(r.status) || "purchasing" === r.status || "foreman-review" === r.status)),
        R = PRED.waitingQuotes.rows();
      return {
        headline: Q.length ? `${agN(Q.length, "quote request")} open: ${Q.map((r) => `${r.number} (${RFQ_STATUS[r.status] || r.status}, ${(r.quotes || []).length} quote${1 === (r.quotes || []).length ? "" : "s"} in)`).join(", ")}; ${agN(R.length, "line")} on the Buy Board wait${1 === R.length ? "s" : ""} on them.` : "No quote requests are open.",
        work: Q.map((r) => `${r.number} · ${r.title}${r.dueDate ? `, due ${fmt(r.dueDate)}` : ""}`),
        go: { view: "rfq" },
        n: Q.length,
      };
    },
  },
  {
    id: "noprice",
    rx: /\b(which|what)\b.*\b(items?|lines?|materials?|needs?)\b.*\b(no|without a?|missing)\s+price\b|\bunpriced\b/,
    answer: () => {
      const R = PRED.unpriced.rows();
      return {
        headline: R.length ? `${agN(R.length, "need")} on the Buy Board ${1 === R.length ? "has" : "have"} no price to check against the estimate.` : "Every need on the Buy Board has a price.",
        work: R.map((r) => `${r.name} (${bbJob(r.p)}): ${bbLineLabel(r)}`),
        go: { view: "proc" },
        n: R.length,
      };
    },
  },
  {
    id: "above",
    rx: /\bis (the )?(.+?) (price )?(above|over|more than) (the )?(estimate|line|budget)\b|\b(above|over) (the )?(estimate|budget)\b.*\b(price|tile|item)\b/,
    answer: (l) => {
      const m = l.match(/\bis (?:the )?(.+?) (?:price )?(?:above|over|more than)/),
        w = ((m && m[1]) || l).replace(/\bprice\b/g, "").trim().split(/\s+/).filter((x) => x.length > 2),
        R = buyList("").filter((r) => w.some((x) => r.name.toLowerCase().includes(x)));
      if (!R.length) return null;
      const rows = R.map((r) => {
        const lf = r.lineKey ? lineFin(r.lineKey) : null,
          budget = lf ? lf.budget : r.budget || 0,
          spent = lf ? r2(lf.actual + lf.committed) : r.po && "function" == typeof poTotal ? poTotal(r.po).total : 0,
          last = bbLastPrices(r)[0];
        return { r: r, budget: budget, spent: spent, over: budget ? r2(spent - budget) : null, last: last };
      });
      const over = rows.filter((x) => null != x.over && x.over > 0);
      return {
        headline: over.length
          ? `Yes: ${over.map((x) => `${x.r.name} is ${money(x.over)} over its line (${money(x.spent)} against ${money(x.budget)})`).join("; ")}.`
          : `No: ${rows.map((x) => (x.budget ? `${x.r.name} has ${money(Math.max(0, x.budget - x.spent))} left of ${money(x.budget)} on its line` : `${x.r.name} has no line budget to compare`)).join("; ")}.`,
        work: rows.map((x) => `${x.r.name} (${bbJob(x.r.p)}): line ${x.budget ? money(x.budget) : "none"}, committed or spent ${money(x.spent)}${x.last ? `, last paid ${money(x.last.p)}${x.last.u ? "/" + x.last.u : ""}` : ""}`),
        go: { view: "proc" },
        n: rows.length,
      };
    },
  },
];
// The vendor a question names: the longest vendor name, or its first word, found in the question.
function bbAskVendor(l) {
  const V = (DB.vendors || []).slice().sort((a, b) => String(b.name).length - String(a.name).length);
  return V.find((v) => l.includes(String(v.name).toLowerCase())) || V.find((v) => { const w = String(v.name).toLowerCase().split(/\s+/)[0]; return w.length > 3 && new RegExp(`\\b${w.replace(/[^a-z0-9]/g, "")}\\b`).test(l); }) || null;
}
BB_ASK.push(
  {
    // "what does Nemo Tile owe us": a vendor's direction is credits and returns we are owed, never client receivables
    id: "owesus",
    rx: /\b(what|how much)\b.*\bowes?\b.*\b(us|me|the firm)\b|\bcredits? (due|owed) from\b/,
    answer: (l) => {
      const v = bbAskVendor(l);
      if (!v) return null;
      const n = String(v.name).toLowerCase(),
        R = ("function" == typeof retList ? retList() : []).filter((r) => String(r.vendor || "").toLowerCase() === n && RET_OPEN.includes(r.status)),
        C = ("function" == typeof claimsOpen ? claimsOpen() : []).filter((c) => String(c.vendor || "").toLowerCase() === n),
        amt = (r) => ("function" == typeof retExpected ? retExpected(r) : +r.expect || 0),
        tot = r2(R.reduce((a, r) => a + (+amt(r) || 0), 0));
      return {
        headline: R.length || C.length ? `${v.name} owes us ${money(tot)} on ${agN(R.length, "open return")}${C.length ? `, and ${agN(C.length, "open claim")} with no amount recorded yet` : ""}.` : `No credit, return or claim is recorded as owed by ${v.name}.`,
        work: R.map((r) => `${r.name || "Return"} (${r.qty || ""}): ${money(amt(r))} expected, ${r.status}${r.rma ? `, ${r.rma}` : ""}`).concat(C.map((c) => `Claim: ${c.kind} ${c.qty || ""} of ${c.ofQty || ""}, ${c.status}`)),
        go: { view: "proc" },
        n: R.length + C.length,
      };
    },
  },
  {
    id: "poapproval",
    rx: /\b(pos?|purchase orders?|orders?)\b.*\b(waiting|pending|awaiting|need(s|ing)?)\b.*\bapprov/,
    answer: () => {
      const P = (DB.pos || []).filter((po) => "pending" === po.status);
      return {
        headline: P.length ? `${agN(P.length, "order")} waiting for approval: ${P.map((po) => `${po.number} ${po.vendor} ${money(poTotal(po).total)}`).join("; ")}.` : "No order is waiting for approval.",
        work: P.map((po) => `${po.number} · ${po.vendor}: ${money(poTotal(po).total)}${"function" == typeof poApprovalWhy ? ` (${poApprovalWhy(po).join("; ")})` : ""}`),
        go: { view: "po" },
        n: P.length,
      };
    },
  },
  {
    id: "lastprice",
    rx: /\b(last (price|paid)|what did we pay|what we paid|last time)\b.*\bfor\b/,
    answer: (l) => {
      const what = (l.match(/\bfor (?:the )?(.+?)\??$/) || [])[1] || "",
        w = what.split(/[^a-z0-9]+/).filter((x) => x.length > 2 && !/^(last|time|our|the)$/.test(x));
      if (!w.length) return null;
      const H = (DB.pos || [])
        .filter((po) => !["cancelled", "draft"].includes(po.status))
        .flatMap((po) => (po.lines || []).filter((x) => w.every((t) => String(x.item || "").toLowerCase().includes(t))).map((x) => ({ po: po, l: x })))
        .filter((x) => +x.l.price > 0)
        .sort((a, b) => String(b.po.date).localeCompare(a.po.date));
      if (!H.length) return { headline: `No order on file has bought ${what}.`, work: [], go: { view: "po" }, n: 0 };
      const x = H[0];
      return {
        headline: `Last paid ${money(+x.l.price)} per ${x.l.unit || "ea"} for ${x.l.item}, from ${x.po.vendor} on ${x.po.number} (${fmt(x.po.date)}).`,
        work: H.slice(0, 5).map((y) => `${fmt(y.po.date)} · ${y.po.vendor} · ${y.po.number}: ${money(+y.l.price)}/${y.l.unit || "ea"}`),
        go: { view: "po" },
        n: H.length,
      };
    },
  },
  {
    id: "backorder",
    rx: /\bback ?order/,
    answer: () => {
      const R = PRED.lateMaterial.rows().filter((r) => r.ordered);
      return {
        headline: R.length ? `${agN(R.length, "line")} on order will not be on site when needed: ${R.map((r) => `${r.name} (${r.lateWhy.toLowerCase()})`).join("; ")}.` : "Nothing on order is promised late.",
        work: R.map((r) => `${r.name} (${bbJob(r.p)}): ${r.vendor || "no vendor"}${r.po ? `, ${r.po.number}` : ", no order behind it"}`),
        go: { view: "proc" },
        n: R.length,
      };
    },
  },
  {
    id: "rep",
    rx: /\b(who is|who's|whos)\b.*\b(rep|contact|salesperson|account manager)\b/,
    answer: (l) => {
      const v = bbAskVendor(l);
      if (!v) return null;
      const who = v.contact || v.rep || v.contactName || "";
      return {
        headline: who || v.email || v.phone ? `${v.name}: ${[who, v.phone, v.email].filter(Boolean).join(", ")}.` : `${v.name} has no contact on file. Add one on the vendor.`,
        work: [],
        go: { view: "vendors" },
        n: 1,
      };
    },
  },
);
BB_ASK.find((x) => "quotes" === x.id).rx = /\b(which|what)\b.*\bquotes?\b.*\b(waiting|wait|out|pending|open)\b|\bwaiting on quotes?\b|\bopen (rfqs?|quote requests?)\b|\brfqs?\b.*\bopen\b/;
function bbAskRoute(q) {
  const r = role();
  if (!["owner", "pm", "coord"].includes(r)) return null;
  const l = String(q || "").toLowerCase().replace(/\s+/g, " ").trim();
  for (const it of BB_ASK) {
    if (!it.rx.test(l)) continue;
    const a = it.answer(l);
    if (a) return Object.assign(a, { kind: "bb-" + it.id, routedBy: "buyboard" });
  }
  return null;
}
if ("function" == typeof paAsk) {
  const bbPaAskBase = paAsk;
  paAsk = function (q) {
    let a = null;
    try {
      a = bbAskRoute(q);
    } catch (e) {
      console.warn("buy board ask", e), (a = null);
    }
    if (a) {
      try {
        paInit();
      } catch (e) {}
      return paOut(Object.assign({}, a, { go: a.go ? paGo(a.go) : null, offers: [] }));
    }
    return bbPaAskBase.apply(this, arguments);
  };
}
"undefined" != typeof AG_DICT && "unpriced reconfirm reconfirmed expedite".split(" ").forEach((w) => AG_DICT.add(w));

// ---- the look: Main.dc.html, PhoneArriving.dc.html and Desk.dc.html ---------------------------------------------------
(() => {
  const css = `
#v-proc:has(.bb){background:#F7F8FA;font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#1A1D23}
.bb button,.bb input,.bb select{font-family:inherit}
.bb .bb-ph0{display:flex;align-items:center;gap:12px;margin:0 0 10px;flex-wrap:wrap}
.bb .bb-title{display:flex;align-items:center;gap:10px;flex:1 1 auto;min-width:0}
.bb .bb-title h2{margin:0;font-size:24px;line-height:30px;font-weight:700}
.bb .bb-latepill{display:inline-flex;align-items:center;height:24px;padding:0 8px;border-radius:999px;font-size:12px;font-weight:600;color:#6A7080;white-space:nowrap}
.bb .bb-latepill.on{background:#FDECEA;color:#B42318}
.bb .bb-tools{display:flex;align-items:center;gap:8px}
.bb .bb-search{display:flex;align-items:center;gap:8px;width:280px;height:38px;padding:0 12px;box-sizing:border-box;border:1px solid #DDE1E8;border-radius:10px;background:#fff;color:#6A7080}
.bb .bb-search input{border:0;outline:0;flex:1;min-width:0;font-size:14px;background:transparent;height:36px;padding:0}
.bb .bb-ib{display:flex;align-items:center;justify-content:center;width:44px;height:44px;border:0;border-radius:12px;background:#F1F3F6;color:#1A1D23;padding:0}
.bb .bb-ib.on{background:#EEF3FD;color:#1D47A8}
.bb .bb-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 10px}
.bb .bb-tabs{display:flex;gap:4px;padding:3px;background:#ECEEF2;border-radius:10px;border:0}
.bb .bb-tabs button{height:32px;padding:0 14px;border:0;border-radius:8px;background:transparent;color:#4A5060;font-size:14px;display:flex;align-items:center;gap:6px}
.bb .bb-tabs button.on{background:#fff;box-shadow:0 1px 2px rgba(16,24,40,.08);color:#1A1D23;font-weight:600}
.bb .bb-tabs .n,.bb .bb-chips .n{position:static;background:none;color:inherit;font-weight:700;padding:0;min-width:0;height:auto;font-size:inherit}
.bb .bb-chips{display:flex;gap:8px;border:0;background:none;padding:0}
.bb .bb-chips button{height:32px;padding:0 12px;border:0;border-radius:999px;background:#fff;box-shadow:0 0 0 1px #DDE1E8;color:#3E4450;font-size:13px}
.bb .bb-chips button.late{color:#B42318;font-weight:600}
.bb .bb-chips button.on{background:#1A1D23;color:#fff;box-shadow:none;font-weight:600}
.bb .bb-sep{width:1px;height:24px;background:#DDE1E8;margin:0 4px}
.bb .bb-fl{display:flex;gap:8px;flex-wrap:wrap}
.bb .bb-fl select{height:32px;padding:0 10px;border:0;border-radius:999px;background:#fff;box-shadow:0 0 0 1px #DDE1E8;color:#3E4450;font-size:13px;max-width:200px}
.bb .bb-main{display:flex;gap:16px;align-items:flex-start}
.bb .bb-list{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:6px}
.bb .bb-sh{display:flex;align-items:baseline;gap:8px;padding:8px 4px 2px;font-size:12px;font-weight:700;letter-spacing:.03em;color:#1A1D23}
.bb .bb-sh.late{color:#B42318}
.bb .bb-sh i{font-style:normal;font-weight:400;color:#6A7080}
.bb .bb-box{background:#fff;border-radius:12px;box-shadow:0 0 0 1px #E7E9EE;display:flex;flex-direction:column}
.bb .bb-box>*+*{border-top:1px solid #F0F1F4}
.bb .bb-row{display:flex;align-items:center;min-height:58px;padding:6px 14px 6px 4px}
.bb .bb-row.sel{background:#F5F8FF;box-shadow:inset 3px 0 0 #2456C9}
.bb .bb-pick{display:flex;align-items:center;justify-content:center;width:44px;height:44px !important;min-height:44px !important;flex:none;border:0;background:transparent;padding:0;cursor:pointer}
.bb .bb-rbody{flex:1;min-width:0;display:grid;grid-template-columns:minmax(0,2.4fr) minmax(0,1fr) 80px 72px minmax(0,1.6fr);gap:12px;align-items:center;border:0;background:transparent;text-align:left;padding:0;cursor:pointer;color:inherit;font-size:13px}
.bb .bb-c1,.bb .bb-c5{display:flex;flex-direction:column;gap:2px;min-width:0}
.bb .bb-c1 b{font-size:14px;font-weight:600}
.bb .bb-c1 span,.bb .bb-c5 span{font-size:12px;color:#5B616E;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bb .bb-c2,.bb .bb-c3,.bb .bb-c4{color:#3E4450}
.bb .late{color:#B42318 !important;font-weight:600}
.bb .blue{color:#1D47A8}
.bb .bb-c5 b{font-weight:600}
.bb .bb-panel{width:380px;flex:none;position:sticky;top:12px;display:flex;flex-direction:column;gap:12px;padding:18px;box-sizing:border-box;background:#fff;border-radius:14px;box-shadow:0 0 0 1px #E7E9EE,0 8px 24px rgba(16,24,40,.06)}
.bb-ph{display:flex;flex-direction:column;gap:4px}
.bb-ph .bb-ref{font-size:12px;color:#6A7080}
.bb-ph h3{margin:0;font-size:20px;line-height:1.25}
.bb-latebox{display:flex;flex-direction:column;gap:4px;padding:10px 12px;border-radius:10px;background:#FDECEA;color:#7A1A12;font-size:13px;line-height:1.4}
.bb-prop{display:flex;flex-direction:column;gap:6px;padding:12px;border-radius:10px;background:#EEF3FD;font-size:13px;line-height:1.4;color:#1D3A80}
.bb-prop b{color:#1D47A8}
.bb-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 12px;font-size:13px}
.bb-grid span{color:#6A7080}
.bb-grid b{text-align:right;font-weight:400}
.bb-hist{display:flex;flex-direction:column;gap:6px;font-size:13px;line-height:1.4}
.bb-hist .bb-hh{font-size:12px;font-weight:700;letter-spacing:.03em;color:#6A7080}
.bb-steps{display:flex;flex-direction:column;gap:8px}
.bb-steps .btn{min-height:44px;border-radius:12px;font-weight:600;font-size:14px}
.bb .bb-empty{color:#6A7080;font-size:13px}
.bb .bb-none{padding:24px;color:#6A7080;text-align:center;background:#fff;border-radius:12px;box-shadow:0 0 0 1px #E7E9EE}
.bb .bb-foot{display:flex;align-items:center;gap:8px;justify-content:space-between;padding:6px 4px;font-size:12px;color:#6A7080;border:0;background:none}
.bb .bb-focus{display:flex;align-items:center;gap:8px;margin:0 0 8px;padding:8px 12px;border-radius:10px;background:#EEF3FD;color:#1D47A8;font-size:13px}
.bb .bb-bar{position:sticky;bottom:0;display:flex;align-items:center;gap:8px;margin-top:10px;padding:10px 16px;background:#fff;border-top:1px solid #E7E9EE;border-radius:12px 12px 0 0;box-shadow:0 -4px 12px rgba(16,24,40,.06)}
.bb .bb-bar span{flex:1;font-size:13px;color:#4A5060}
.bb .bb-bar b{color:#1A1D23}
.bb .bb-bar .btn{height:44px;border-radius:12px;font-weight:600;font-size:14px;padding:0 14px}
.bb .bb-arr{display:flex;align-items:center;gap:10px;padding:10px 12px 10px 14px}
.bb .bb-abody{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px;border:0;background:transparent;text-align:left;padding:0;color:inherit;cursor:pointer}
.bb .bb-act{min-width:88px;height:44px;border-radius:12px;font-weight:600;font-size:14px}
.bb .bb-conf{font-size:12px;font-weight:600;color:#3E4450}
.bb .bb-conf.ok{color:#1F7A4D}.bb .bb-conf.warn{color:#9A5B00}.bb .bb-conf.late{color:#B42318}
.bb .bb-t{font-size:15px;font-weight:600;line-height:1.25}
.bb .bb-s{font-size:13px;color:#5B616E;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bb-back{display:flex;align-items:center;gap:10px;margin:0 0 10px}
.bb-links{display:flex;flex-direction:column;gap:4px;max-height:50vh;overflow:auto}
.bb-link{display:flex;align-items:flex-start;gap:10px;min-height:44px;padding:6px 4px}
.bb-link>span{display:flex;flex-direction:column}
.bb-chip{align-self:flex-start;display:inline-flex;align-items:center;min-height:24px;padding:2px 8px;border-radius:7px;font-size:12px;line-height:1.35}
.bb-chip.red{background:#FDECEA;color:#B42318}.bb-chip.amber{background:#FFF6E5;color:#7A4A00}.bb-chip.blue{background:#EEF3FD;color:#1D47A8}
/* the phone (Main.dc.html): one header row, two tabs, cards in sections, the pick bar above the bottom bar */
.bb.bb-phone .bb-ph0{margin:0 0 8px;flex-wrap:nowrap;flex-direction:row !important;align-items:center !important;justify-content:space-between;text-align:left}
.bb.bb-phone .bb-title{flex:1 1 auto;justify-content:flex-start}
.bb.bb-phone .bb-title h2{font-size:22px}
.bb.bb-phone .bb-top{margin:0 0 4px}
.bb.bb-phone .bb-tabs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));width:100%;border-radius:11px;background:#F1F3F6}
.bb.bb-phone .bb-tabs button{height:36px;justify-content:center;border-radius:9px}
.bb.bb-phone .bb-ptools{display:flex;flex-direction:column;gap:8px;margin:4px 0 8px}
.bb.bb-phone .bb-ptools input{height:44px;border:1px solid #DDE1E8;border-radius:12px;padding:0 12px;font-size:16px}
.bb.bb-phone .bb-ptools select{height:44px;border-radius:12px;max-width:none;flex:1 1 100%}
.bb.bb-phone .bb-sh{padding:10px 6px 4px}
.bb.bb-phone .bb-box{border-radius:14px;box-shadow:0 0 0 1px #ECEEF2}
.bb.bb-phone .bb-card{display:flex;align-items:flex-start;gap:4px;min-height:64px;padding:6px 12px 8px 0}
.bb.bb-phone .bb-cbody{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;padding:9px 0 0;border:0;background:transparent;text-align:left;color:inherit}
.bb.bb-phone .bb-cbody .bb-t{font-size:16px}
.bb.bb-phone .bb-w{font-size:13px;color:#3E4450}
.bb.bb-phone .bb-bar{position:fixed;left:0;right:0;bottom:var(--bb-tabs,64px);margin:0;border-radius:0;z-index:30}
.bb.bb-phone.bb-picking .bb-list{padding-bottom:72px}
.bb.bb-phone .bb-arr .bb-t{font-size:15px}
#mbm.bb-mbm .bb-sheet{display:flex;flex-direction:column;gap:12px}
#mbm.bb-mbm .bb-steps .btn{width:100%}
.bb-job .hd{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.bb-job .hd .btn{margin-left:auto}
.bb-jrow{display:flex;width:100%;min-height:44px;padding:6px 0;border:0;border-top:1px solid #F0F1F4;background:none;text-align:left;color:inherit;cursor:pointer}
.bb-jrow .grow{display:flex;flex-direction:column;gap:2px;min-width:0}
/* the order sheet's line picks: a 44px target, the whole cell (buying day finding 26) */
#mbm .ctp-tick{display:flex;align-items:center;justify-content:center;min-width:44px;min-height:44px;margin:0;cursor:pointer}
#mbm .ctp-tick input{width:20px;height:20px;margin:0}
`;
  const st = document.createElement("style");
  (st.id = "bb-css"), (st.textContent = css), document.head.appendChild(st);
})();
