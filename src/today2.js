// =====================================================================================================================
// Today, each role's first screen, to the mockups Alan approved on 2026-10-25 (Today Mockups, version 4: TodayOwner,
// TodayPM, TodayCoord, TodayForeman, TodayBilling, TodayController on the phone; Main and DeskController on the desktop).
//
// The page (tdRender, called by renderHome for every office role on Today):
//   header   the menu, "Today" over a date line ("Thu, Sep 3 · 6 for you, 2 late"), Search and Ask (the phone's
//            header; the desktop keeps the app's top bar and puts the title, date line and filters on the page);
//   chips    All, Late and Approvals (the owner, the controller) or All, Late and Waiting (the PM, the coordinator,
//            billing); each chip's count is the rows it shows;
//   update   the AI update: "Since 7:40", at most two lines on the phone and three on the desktop, each line with one
//            linked phrase, and Ask About This (below);
//   sections Now, then the role's own (Approvals / For You / Waiting on Others / You Promised / This Week); each row is
//            an icon, a title, its due and a short meta, a waiting chip, and one action; the first row carries the
//            page's one blue button and a note on why it matters (the Standard's line);
//   quiet    one line at the foot (the Pulse numbers and what was caught); it opens to the Pulse, Caught for You and
//            the morning brief;
//   desktop  a list with What, Amount and When columns, the selected row in a side panel with the blue button, and
//            Your Day (today's calendar).
// The owner's Today opens on All (the mockup), not on Approvals (p2nav N5, superseded).
//
// Design gate (BACKLOG §1.16). Nothing new is stored or listed:
//  - the rows are tdyModel() (the one queue: Approvals, Inbox, Tasks, the Buy Board's orders, the minutes), each
//    drawn by tdCard() (its title, why, verb and run). Sections, chips and the fold are views of that list.
//  - the AI update's facts are read by rules from the same sources the page shows: the queue's rows, the CATCH
//    registry (Caught for You), PRED.safeToSpend, PRED.jobsAtRisk, PRED.vendorsCoiLapsing, the client invoices
//    (clientFin) and the person's assistant log. Its cache and the person's last look live on the person's own
//    assistant record (paInit().td2); the model is the app's ai() (the platform's /api/ai), as the brief uses.
// =====================================================================================================================
const TD2_SPEC = {
  owner: { chips: ["all", "late", "appr"], secs: ["now", "appr", "promised", "week"], rest: "week" },
  controller: { chips: ["all", "late", "appr"], secs: ["now", "appr", "waiting", "week"], rest: "week" },
  pm: { chips: ["all", "late", "wait"], secs: ["now", "for", "promised"], rest: "for" },
  coord: { chips: ["all", "late", "wait"], secs: ["now", "for", "promised"], rest: "for" },
  billing: { chips: ["all", "late", "wait"], secs: ["now", "waiting", "week"], rest: "week" },
};
const TD2_SEC = { now: "Now", appr: "Approvals", promised: "You Promised", waiting: "Waiting on Others", week: "This Week", for: "For You" };
const TD2_CHIP = { all: "All", late: "Late", appr: "Approvals", wait: "Waiting" };
// the mockup's line icons (24px grid, stroked)
const TD2_I = {
  doc: "M7 3h7l5 5v13H7z M14 3v5h5 M10 13h6 M10 17h4",
  phone: "M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a1 1 0 0 1-1 1A16 16 0 0 1 4 5a1 1 0 0 1 1-1z",
  mail: "M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z M3 7l9 6 9-6",
  people: "M9 11a3 3 0 1 0 0-6a3 3 0 1 0 0 6z M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6 M16 5a3 3 0 0 1 0 6 M21 20c0-2.8-1.8-5-4-5.7",
  alert: "M12 4l9 16H3z M12 10v4 M12 17v.5",
  question: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6v.6 M12 17v.5",
  box: "M4 8l8-4 8 4v8l-8 4-8-4z M4 8l8 4 8-4 M12 12v8",
  clipboard: "M8 4h8v3H8z M6 5.5H5v15.5h14V5.5h-1 M9 12h6 M9 16h4",
  receipt: "M6 3h12v18l-3-2-3 2-3-2-3 2z M9 8h6 M9 12h6 M9 16h3",
  bank: "M3 10l9-5 9 5 M5 10v8 M9.5 10v8 M14.5 10v8 M19 10v8 M3 20h18",
  book: "M5 4h11a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2z M5 18a2 2 0 0 1 2-2h11",
  chat: "M4 5h16v10H9l-5 4z",
  tasks: "M9 6h11 M9 12h11 M9 18h11 M4 6l1 1 2-2 M4 12l1 1 2-2 M4 18l1 1 2-2",
  cart: "M4 6h2l2 10h10l2-7H7 M9 17.6a1.4 1.4 0 1 0 0 2.8a1.4 1.4 0 1 0 0-2.8z M17 17.6a1.4 1.4 0 1 0 0 2.8a1.4 1.4 0 1 0 0-2.8z",
  wallet: "M4 6h16a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1z M3 10h18 M15 15h3",
  clock: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M12 7v5l3 2",
  spark: "M12 3.5l1.9 5.1 5.1 1.9-5.1 1.9L12 17.5l-1.9-5.1L5 10.5l5.1-1.9z",
  down: "M6 9l6 6 6-6",
};
const td2Svg = (k, n, sw) =>
  `<svg width="${n || 20}" height="${n || 20}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${sw || 1.8}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${TD2_I[k] || TD2_I.doc}"/></svg>`;
const td2Txt = (h) =>
  String(h || "")
    .replace(/<[^>]*>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, " ")
    .trim();
const td2Desk = () => !("function" == typeof mOffice && mOffice());
// "7:40" in the morning, "1:30 pm" after noon (the mockup's clock words), from an app-clock stamp
function td2Clock(ts) {
  const m = /T(\d{2}):(\d{2})/.exec(String(ts || ""));
  if (!m) return "";
  const h = +m[1];
  return `${h % 12 || 12}:${m[2]}${h >= 12 ? " pm" : ""}`;
}
const TD2_DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
// a due date in the row's words: "2 days late", "Today", "Tomorrow", "Fri", "9/14"
function td2DueWords(d, late) {
  if (!d) return "";
  const td = today(),
    n = dayDiff(d, td);
  if (late || d < td) return `${Math.max(1, n)} day${1 === Math.max(1, n) ? "" : "s"} late`;
  if (d === td) return "Today";
  const k = dayDiff(td, d);
  if (1 === k) return "Tomorrow";
  if (k < 7) return TD2_DOW[parse(d).getDay()];
  return fmt(d);
}
function td2Icon(it) {
  const k = it.kind,
    nk = (it.nyh && it.nyh.kind) || "";
  if ("tdyMail" === k || "draft" === k || "promise" === nk || "mail" === nk) return "mail";
  if ("tdyChat" === k || "clientq" === k) return "chat";
  if ("tdyBuy" === k || "req" === k) return "cart";
  if ("tdyMinutes" === k || "meeting" === k) return "clipboard";
  if ("tdyTask" === k) return "tasks";
  if ("bill" === k) return "receipt";
  if ("payroll" === k || "time" === k || "tdyPerson" === k) return "people";
  if ("dec" === k || "raise" === k) return "question";
  if ("lesson" === k || "learn" === k || "change" === k) return "book";
  if ("prepay" === k) return "wallet";
  if ("coi" === k || /^std:|^oblig:/.test(String(it.id || ""))) return "alert";
  return "doc";
}
function td2Amount(it, c) {
  try {
    if ("bill" === it.kind) {
      const b = (DB.bills || []).find((x) => x.id === it.id);
      if (b) return billTotal(b);
    }
    if (+it.amount) return +it.amount;
    const m = /\$\s?([\d,]+(?:\.\d\d)?)/.exec(`${it.title || ""} ${td2Txt(c && c.why)}`);
    return m ? +m[1].replace(/,/g, "") : 0;
  } catch (e) {
    return 0;
  }
}
// the date a row is due, from the record behind it (the Standard's clocks for mail and client messages)
function td2DueOf(it) {
  if ("tdyTask" === it.kind || "tdyBuy" === it.kind) return String(it.due || "").slice(0, 10);
  if ("tdyMail" === it.kind) return String((it.c && it.c.date) || "").slice(0, 10) || today();
  if ("tdyChat" === it.kind) return today();
  if ("tdyMinutes" === it.kind) return "";
  try {
    return String(stdDueOf(it) || "").slice(0, 10);
  } catch (e) {
    return "";
  }
}
function td2IsPromise(it) {
  return !!((it.nyh && "promise" === it.nyh.kind) || /^You promised\b/i.test(String(it.title || "")) || (it.t && /promis/i.test(`${it.t.source || ""} ${it.t.origin || ""}`)));
}
// what a row waits on (someone else holds the next step), in the mockup's chip words
function td2WaitOf(it) {
  try {
    const t = it.t,
      me = tdyMe();
    if (t && t.waitsOn) return `Waiting on ${t.waitsOn}`;
    if (t && t.handoff && "offered" === t.handoff.state && t.handoff.fromUid === me.id) return `Waiting on ${t.handoff.to} to accept`;
    if (t && t.party) return `Waiting on ${t.party}`;
    if ("tdyBuy" === it.kind && it.x && it.x.dec) return "Waiting on a client decision";
  } catch (e) {}
  return "";
}
// The rows of the person's Today: the one queue (tdyModel), each with its card (tdCard), section, due and chips.
function td2Rows(M) {
  const r = role(),
    S = TD2_SPEC[r] || TD2_SPEC.pm,
    td = today(),
    has = (k) => S.secs.includes(k),
    last = S.rest,
    appr = new Set(M.appr || []);
  return (M.all || []).map((it) => {
    let c = null;
    try {
      c = tdCard(it);
    } catch (e) {
      console.warn("today card", it && it.kind, e);
    }
    c = c || { line1: esc(tdPlain(it.title)), why: esc(it.detail || ""), verb: "Open", go: () => mGo(it.open), run: () => mGo(it.open) };
    const due = td2DueOf(it),
      late = !!((it.t && it.t.late) || (due && due < td)),
      wait = td2WaitOf(it),
      promise = td2IsPromise(it),
      isAppr = appr.has(it),
      now = late || (due && due <= td) || ["raise", "clientq", "tdyMail", "tdyChat"].includes(it.kind),
      sec = now ? "now" : promise && has("promised") ? "promised" : isAppr && has("appr") ? "appr" : wait && has("waiting") ? "waiting" : last;
    return {
      it: it,
      c: c,
      key: `${it.kind}:${it.id}`,
      sec: has(sec) ? sec : last,
      due: due,
      late: late,
      appr: isAppr,
      wait: wait,
      promise: promise,
      title: tdWords(td2Txt(c.line1) || tdPlain(it.title), 9),
      meta: tdWords(td2Txt(c.why) || td2Txt(it.detail), 7),
      dueW: td2DueWords(due, late),
      amt: td2Amount(it, c),
      icon: td2Icon(it),
    };
  });
}
const td2Match = (k, x) => ("late" === k ? x.late : "appr" === k ? x.appr : "wait" === k ? !!x.wait : !0);
// per-render state the page and its handlers read
let td2Cur = null,
  td2Sel = {},
  td2QuietOpen = !1,
  td2Entered = !1,
  td2Calls = 0,
  td2EnteredMs = 0,
  td2Busy = "";
function td2Model() {
  const M = tdyModel(),
    r = role(),
    S = TD2_SPEC[r] || TD2_SPEC.pm,
    rows = td2Rows(M),
    chips = S.chips.map((k) => ({ k: k, label: TD2_CHIP[k], n: rows.filter((x) => td2Match(k, x)).length })),
    stored = tdyTabOf(),
    tab = S.chips.includes(stored) ? stored : "all",
    Q = rows.filter((x) => td2Match(tab, x)),
    desk = td2Desk(),
    // All folds to the first rows of each section (the phone's first screen, the mockup's six); a chip shows its
    // whole list in place; "N more" opens the rest of All in place
    fold = "all" === tab && !tdyAllOpen,
    cap = desk ? { now: 5, rest: 3, total: 12 } : { now: 3, rest: 2, total: 6 },
    shown = [];
  S.secs.forEach((s) => {
    const R = Q.filter((x) => x.sec === s);
    (fold ? R.slice(0, "now" === s ? cap.now : cap.rest) : R).forEach((x) => (!fold || shown.length < cap.total) && shown.push(x));
  });
  const secs = S.secs.map((s) => ({ k: s, name: TD2_SEC[s], rows: shown.filter((x) => x.sec === s), n: Q.filter((x) => x.sec === s).length })).filter((s) => s.rows.length);
  return { M: M, r: r, S: S, rows: rows, chips: chips, tab: tab, Q: Q, shown: shown, secs: secs, hidden: Q.length - shown.length, late: rows.filter((x) => x.late).length };
}
// the Today badge on the bar and the menu: the late rows (the mockup's red count), one number everywhere
let td2LateMemo = { t: -1, n: 0, u: "" };
function td2LateN() {
  const u = (tdyMe() || {}).id || role();
  if (td2LateMemo.t === td2Tick && td2LateMemo.u === u) return td2LateMemo.n;
  let n = 0;
  try {
    n = TD2_SPEC[role()] ? td2Rows(tdyModel()).filter((x) => x.late).length : 0;
  } catch (e) {}
  return (td2LateMemo = { t: td2Tick, n: n, u: u }), n;
}
let td2Tick = 0;

// ---- the AI update ---------------------------------------------------------------------------------------------------
// What it may say, by role (the categories in Alan's order; ranked below by the Standard's decision principles).
const TD2_FACTS = {
  owner: ["decide", "cash", "leak", "slip", "promise", "mail", "pipeline", "people", "did"],
  pm: ["decide", "leak", "slip", "promise", "mail", "did"],
  coord: ["decide", "leak", "slip", "promise", "people", "did"],
  billing: ["decide", "cash", "leak", "mail", "did"],
  controller: ["decide", "cash", "leak", "did"],
};
// the money leaks each role answers for (CATCH detector -> the words for it)
const TD2_LEAK = {
  earnedNotBilled: "of work done not billed",
  costNotBilled: "bought for clients not billed back",
  overPO: "billed over its PO",
  unmatchedCredit: "in credits not matched to a return",
  pwStoreCheaper: "paid above a cheaper store",
};
const TD2_LEAK_ROLE = {
  owner: ["earnedNotBilled", "costNotBilled", "overPO", "unmatchedCredit"],
  pm: ["costNotBilled", "overPO"],
  coord: ["overPO", "pwStoreCheaper"],
  billing: ["earnedNotBilled", "costNotBilled"],
  controller: ["overPO", "unmatchedCredit"],
};
// the principle's rank in the live Standard (1 safety .. 7 cost; 8 when none is at stake)
function td2Tier(id) {
  try {
    const i = (standard().principles || []).findIndex((p) => p.id === id);
    return i >= 0 ? i + 1 : 8;
  } catch (e) {
    return 8;
  }
}
// The Standard's own words on why money matters (Value "Every dollar matters"), loaded, never paraphrased
function td2MoneyWhy() {
  try {
    const v = (standard().values || []).find((x) => "dollar" === x.id);
    if (!v) return { name: "", why: "" };
    const all = JSON.stringify(v),
      m = /(Money wasted is[^"]*?\.)(?=\s|")/.exec(all);
    return { name: v.name || "", why: m ? m[1].replace(/\\u2019/g, "’") : "" };
  } catch (e) {
    return { name: "", why: "" };
  }
}
const td2Money = (v) => (+v < 0 ? "−" : "") + money(Math.abs(Math.round(+v || 0))).replace(/\.00$/, "");
function td2Look() {
  const A = paInit();
  return (A.td2 = A.td2 && "object" == typeof A.td2 ? A.td2 : {});
}
// The facts, selected by rules from the records (deterministic). Each: {k, cat, tier, pre, link, post, go, why}.
function td2Facts(T) {
  const r = role(),
    want = TD2_FACTS[r] || [],
    td = today(),
    out = [],
    vis = new Set(T.shown.map((x) => x.key)),
    add = (f) => out.push(Object.assign({ why: "" }, f)),
    s = (n, a, b) => (1 === n ? a : b);
  const run = (cat, f) => {
    if (!want.includes(cat)) return;
    try {
      f();
    } catch (e) {
      console.warn("today update", cat, e);
    }
  };
  // only-you decisions with a deadline: the approvals past their date (or due today)
  run("decide", () => {
    const L = T.rows.filter((x) => x.appr && x.due && x.due <= td);
    if (!L.length) return;
    const late = L.filter((x) => x.due < td),
      o = (late.length ? late : L).slice().sort((a, b) => a.due.localeCompare(b.due))[0],
      n = late.length ? late.length : L.length,
      days = late.length ? dayDiff(o.due, td) : 0;
    add({
      k: `decide:${o.key}:${n}:${days}`,
      cat: "decide",
      tier: (() => {
        try {
          return standardTier(o.it);
        } catch (e) {
          return 8;
        }
      })(),
      pre: late.length
        ? n > 1
          ? `${n} decisions only you can make are past their date; `
          : `1 decision only you can make has waited ${days} day${s(days, "", "s")} past its date: `
        : `${n} decision${s(n, "", "s")} only you can make ${s(n, "is", "are")} due today: `,
      link: late.length && n > 1 ? "the oldest" : n > 1 ? "open the first" : "open it",
      post: late.length && n > 1 ? ` has waited ${days} day${s(days, "", "s")}.` : ".",
      go: o.c.go,
    });
  });
  // cash for the next two weeks: Safe to Spend and the client invoices that fall due
  run("cash", () => {
    const safe = PRED.safeToSpend.figure(),
      in14 = iso(addDays(td, 14));
    let ar = 0;
    (DB.clients || []).forEach((c) =>
      clientFin(c).open.forEach((o) => o.x && o.x.due && o.x.due >= td && o.x.due <= in14 && (ar += +o.bal || 0)),
    );
    const od = PRED.overdueAR.figure();
    if (safe >= 0 && !od && "owner" === r) return;
    add({
      k: `cash:${Math.round(safe)}:${Math.round(ar)}:${Math.round(od)}`,
      cat: "cash",
      tier: td2Tier("cost"),
      pre: "Cash: ",
      link: "Safe to Spend",
      post: ` is ${td2Money(safe)}; ${ar ? `${td2Money(ar)} of client invoices fall due in the next two weeks` : "no client invoice falls due in the next two weeks"}${od ? `, and ${td2Money(od)} is past due` : ""}.`,
      go: () => tdPulseOpen(TD_PULSE.owner.find((t) => "safe" === t.k)),
    });
  });
  // money leaking, in dollars, with the Standard's line on why money matters
  run("leak", () => {
    const names = TD2_LEAK_ROLE[r] || [],
      parts = [];
    let big = null;
    names.forEach((nm) => {
      const C = CATCH.find((x) => x.name === nm);
      if (!C) return;
      const R = (C.rows() || []).filter((x) => +x.amount > 0);
      if (!R.length) return;
      const sum = R.reduce((a, x) => a + (+x.amount || 0), 0);
      parts.push({ nm: nm, sum: sum });
      R.forEach((x) => (!big || +x.amount > +big.amount) && (big = x));
    });
    if (!parts.length) return;
    parts.sort((a, b) => b.sum - a.sum);
    const total = parts.reduce((a, p) => a + p.sum, 0),
      W = td2MoneyWhy();
    add({
      k: `leak:${parts.map((p) => p.nm + Math.round(p.sum)).join(",")}`,
      cat: "leak",
      tier: td2Tier("cost"),
      pre: W.name ? `${W.name}: ` : "",
      link: `${td2Money(total)} is leaking`,
      post: ` (${parts
        .slice(0, 2)
        .map((p) => `${td2Money(p.sum)} ${TD2_LEAK[p.nm]}`)
        .join(", ")}).`,
      go: big && big.run ? () => big.run() : () => ((td2QuietOpen = !0), render()),
      why: W.why,
    });
  });
  // a job slipping: the first job at risk (the schedule, a late decision or order, the margin)
  run("slip", () => {
    const mine = new Set(("pm" === r ? tdMyJobs() : DB.projects || []).map((p) => p.id)),
      R = PRED.jobsAtRisk.rows().filter((x) => mine.has(x.p.id) && (x.risks.length || x.why.length) && ("coord" !== r || x.risks.some((k) => "material" === k.kind)));
    if (!R.length) return;
    const x = R[0],
      k = x.risks[0],
      w = k
        ? `${k.holds} ${k.by >= td ? `starts ${fmt(k.by)}` : "is due now"}, held by ${"noshow" === k.kind ? "a sub who did not show" : `a late ${k.kind}`}${k.slip ? `, about ${k.slip} working day${s(k.slip, "", "s")} behind` : ""}`
        : x.why.join(", ");
    add({ k: `slip:${x.p.id}:${w}`, cat: "slip", tier: td2Tier("schedule"), pre: "", link: shortName(x.p), post: ` is slipping: ${w}.`, go: flowGo.project(x.p) });
  });
  // a promise at risk that the list does not show on its first screen
  run("promise", () => {
    const x = T.rows.find((y) => y.promise && !vis.has(y.key) && y.due && y.due <= iso(addDays(td, 1)));
    if (!x) return;
    add({ k: `promise:${x.key}:${x.due}`, cat: "promise", tier: td2Tier("client"), pre: "You promised ", link: tdWords(x.title.replace(/^You promised\s*/i, ""), 6), post: ` by ${x.dueW.toLowerCase()}; it is still open.`, go: x.c.go });
  });
  // a client's mail unanswered past the Standard's two hours
  run("mail", () => {
    const now = appNowMs(),
      x = T.rows.find((y) => {
        if ("tdyMail" !== y.it.kind || !y.it.c) return !1;
        const c = y.it.c,
          client = !!((c.route && c.route.clientId) || ("function" == typeof cmClientOf && cmClientOf(c)));
        return client && now - new Date(c.date).getTime() > 72e5;
      });
    if (!x) return;
    const c = x.it.c,
      who = (c.from && (c.from.name || c.from.email)) || "a client";
    add({ k: `mail:${c.id}`, cat: "mail", tier: td2Tier("client"), pre: "A client has waited past the Standard's 2 business hours: ", link: `${td2Pos(who)} mail`, post: ".", go: x.c.go });
  });
  // pipeline: a proposal gone quiet (Caught for You's chase list)
  run("pipeline", () => {
    const C = CATCH.find((c) => "chasePeople" === c.name),
      R = C ? (C.rows() || []).slice().sort((a, b) => (+b.amount || 0) - (+a.amount || 0)) : [];
    if (!R.length) return;
    const x = R[0];
    add({ k: `pipe:${x.key}`, cat: "pipeline", tier: 8, pre: "", link: String(x.what || "").replace(/^Gone quiet:\s*/, ""), post: `: ${tdWords(String(x.sub || "").replace(/\s+—.*$/, ""), 9)}.`, go: () => x.run && x.run() });
  });
  // people: a certificate of insurance lapsing before the vendor is on site
  run("people", () => {
    const R = PRED.vendorsCoiLapsing.rows().filter((x) => x.next);
    if (!R.length) return;
    const x = R[0],
      p = x.next.p && "object" == typeof x.next.p ? x.next.p : x.next.p ? (DB.projects || []).find((q) => q.id === x.next.p) : null;
    add({
      k: `coi:${x.v.id}:${x.exp}`,
      cat: "people",
      tier: td2Tier("law"),
      pre: "",
      link: `${td2Pos(x.v.name)} insurance`,
      post: ` ${"expired" === x.state ? "expired" : "lapses"} ${fmt(x.exp)}, and they are booked${p ? ` at ${shortName(p)}` : ""} on ${fmt(x.next.date)}.`,
      go: flowGo.vendor(x.v),
    });
  });
  // what the assistant did since the last look, and the drafts that wait for a yes
  run("did", () => {
    const L = td2Look(),
      since = L.seen || `${td}T00:00:00`,
      A = paInit(),
      done = (A.log || []).filter((x) => String(x.at || x.t || "") > since && /sent|chase|filed|scheduled/i.test(String(x.text || x.what || ""))).length,
      drafts = T.rows.filter((x) => "draft" === x.it.kind);
    if (!done && !drafts.length) return;
    add({
      k: `did:${done}:${drafts.length}`,
      cat: "did",
      tier: 9,
      pre: done ? `Done for you since your last look: ${done} thing${s(done, "", "s")}. ` : "",
      link: drafts.length ? `${drafts.length} draft${s(drafts.length, "", "s")} wait${s(drafts.length, "s", "")} for your yes` : "See what was done",
      post: ".",
      go: drafts.length ? drafts[0].c.go : () => setView("pa"),
    });
  });
  // never repeat a row: a line that carries a title shown on the screen is dropped
  const titles = T.shown.map((x) => x.title.replace(/…$/, "").toLowerCase()).filter((t) => t.length >= 12);
  const order = want;
  return out
    .filter((f) => {
      const line = (f.pre + f.link + f.post).toLowerCase();
      return !titles.some((t) => line.includes(t));
    })
    .sort((a, b) => a.tier - b.tier || order.indexOf(a.cat) - order.indexOf(b.cat));
}
const td2Pos = (n) => (/s$/.test(String(n)) ? `${n}\u2019` : `${n}\u2019s`);
const td2Plain = (f) => f.pre + f.link + f.post;
const td2KeyOf = (F) => `${today()}|${F.map((f) => f.k).join("|")}`;
// The model may only re-word the facts: every number and every name it writes must be in them, and each line keeps
// its linked phrase word for word. Anything else throws its words away (null), and the plain sentences stand.
const TD2_COMMON = new Set("The A An Your You It Its This That These Those There They We I And But So Also Today Now Cash Done Since".split(" "));
function td2Guard(out, F) {
  if (!out || "string" != typeof out || out.startsWith("__ERR")) return null;
  const lines = out
    .split(/\n+/)
    .map((l) => l.trim().replace(/^[-*•\d.)\s]+(?=\S)/, ""))
    .filter(Boolean);
  if (lines.length !== F.length) return null;
  const plain = F.map(td2Plain).join(" "),
    nums = (t) => (String(t).match(/\d[\d,.]*\d|\d/g) || []).map((n) => n.replace(/,/g, "")),
    allowN = new Set(nums(plain)),
    words = new Set(plain.match(/[A-Za-z’'][\w’'&-]*/g) || []),
    res = [];
  for (let i = 0; i < F.length; i++) {
    const f = F[i],
      L = lines[i],
      tag = `[${f.link}]`,
      at = L.indexOf(tag);
    if (at < 0) return null;
    const text = L.replace(tag, f.link);
    if (nums(text).some((n) => !allowN.has(n))) return null;
    if ((text.match(/\b[A-Z][\w’'&-]*/g) || []).some((w) => !words.has(w) && !TD2_COMMON.has(w))) return null;
    if (/!/.test(text)) return null;
    res.push({ pre: L.slice(0, at), link: f.link, post: L.slice(at + tag.length) });
  }
  return res;
}
async function td2Polish(F, key) {
  const L = td2Look();
  if (td2Busy === key || (L.cache && L.cache.key === key)) return;
  td2Busy = key;
  td2Calls++;
  let out = "";
  try {
    out = await ai(
      `Re-word these facts for the ${(typeof ROLE_NAMES != "undefined" && ROLE_NAMES[role()]) || role()}'s Today screen, one line per fact, in the same order, each about as short as it is now. Keep every number, date and name exactly as written; add no number, name or fact. Keep the phrase in square brackets word for word, inside its brackets. Plain, calm words; no exclamation marks. Return only the lines.\n\n${F.map((f) => `${f.pre}[${f.link}]${f.post}`).join("\n")}`,
      400,
      3e4,
    );
  } catch (e) {
    out = "__ERR " + (e && e.message);
  }
  td2Busy = "";
  const lines = td2Guard(out, F);
  // written once for these facts, kept or thrown away: the same facts are not sent again
  td2Look().cache = { key: key, lines: lines, at: appNowIso(), kept: !!lines };
  try {
    save();
  } catch (e) {}
  "home" === view && tdOn() && render();
}
// The update as drawn: its head ("Since 7:40"), its lines, and whether the model's words are used.
function td2Brief(T) {
  const L = td2Look(),
    F = td2Facts(T),
    n = td2Desk() ? 3 : 2,
    top = F.slice(0, n),
    key = td2KeyOf(top),
    since = L.seen || "",
    sinceW = !since ? "Since yesterday" : since.slice(0, 10) === today() ? `Since ${td2Clock(since)}` : 1 === dayDiff(since.slice(0, 10), today()) ? "Since yesterday" : `Since ${fmt(since.slice(0, 10))}`,
    nothing = !!since && L.seenKey === key;
  let lines = top.map((f) => ({ pre: f.pre, link: f.link, post: f.post, go: f.go, why: f.why, model: !1 }));
  const C = L.cache;
  C && C.key === key && C.lines && C.lines.length === top.length && (lines = C.lines.map((x, i) => Object.assign({}, x, { go: top[i].go, why: top[i].why, model: !0 })));
  return { head: sinceW, since: since, facts: top, all: F, key: key, nothing: nothing, lines: nothing ? [] : lines, plain: top.map(td2Plain) };
}
function td2BriefHtml(B, desk) {
  if (!B.facts.length && !B.since) return "";
  const body = B.nothing || !B.lines.length
    ? `<p class="td2-bl">Nothing new since ${esc(B.since ? td2Clock(B.since) || fmt(B.since.slice(0, 10)) : "yesterday")}.</p>`
    : B.lines
        .map(
          (l, i) =>
            `<p class="td2-bl" data-td2line="${i}"${l.model ? ' data-td2model="1"' : ""}>${esc(l.pre)}<a href="#" data-td2go="${i}">${esc(l.link)}</a>${esc(l.post)}${desk && l.why ? ` <span class="td2-why">${esc(l.why)}</span>` : ""}</p>`,
        )
        .join("");
  return `<section class="td2-brief" aria-label="What changed and what matters" data-td2key="${esc(B.key)}"><div class="td2-bh">${td2Svg("spark", 14, 1.9)}<span class="td2-bhead">${esc(B.head)}${desk ? " · what changed and what needs you" : ""}</span><span class="grow"></span><a href="#" data-td2ask>Ask About This</a></div>${body}</section>`;
}
// Ask About This: Ask opens with the update's facts as its context
function td2AskAbout(text) {
  try {
    (paCtx().today = { at: appNowIso(), facts: text }), save();
  } catch (e) {}
  setView("pa");
  setTimeout(() => {
    const i = document.getElementById("pa-in");
    i && ((i.value = `About my Today update: ${text} `), i.focus());
  }, 60);
}

// ---- the quiet line and what it opens: the Pulse, Caught for You, the morning brief ---------------------------------
function td2Pulse() {
  return (TD_PULSE[role()] || [])
    .filter((t) => !(t.money && tdNoMoney()))
    .map((t) => {
      let v = 0;
      try {
        v = tdPulseValue(t);
      } catch (e) {
        console.warn("pulse", t.k, e);
      }
      return { t: t, v: v };
    });
}
function td2QuietWords(P, caught) {
  return P.map(({ t, v }) => (t.money ? `${t.label} ${tdMoney(v)}` : `${v} ${t.label.replace(/^Jobs?\b/, (m) => (1 === v ? "Job" : "Jobs"))}`))
    .concat(caught ? [`${caught} caught for you`] : [])
    .join(" · ") || "Nothing else waits on you";
}
function td2QuietHtml(P, caught, shownC) {
  const ic = '<path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z"/>';
  return `${P.length ? `<div class="td-pulse">${P.map(({ t, v }) => `<a href="#" class="td-pl ${t.tone ? t.tone(v) : ""}" data-tdpulse="${t.k}" data-n="${v}"><b>${t.money ? esc(tdMoney(v)) : v}</b><span>${esc(t.label)}</span></a>`).join("")}</div>` : ""}
  <section class="td-sec td-catch" aria-label="Caught for You"><div class="td-hd"><h3>Caught for You</h3><span class="td-cnt" data-tdcaught="${caught.length}">${caught.length}</span></div>${
    shownC.length
      ? shownC
          .map(
            (x, i) =>
              `<div class="td-card td-c" data-src="${x.src}"><span class="td-ic"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ic}</svg></span><div class="td-txt"><div class="td-l1">${esc(tdWords(x.what, 7))}</div><div class="td-l2">${esc(tdWords(x.sub, 8))}</div></div><button type="button" class="btn sm td-verb" data-tdcatch="${i}">${esc(x.verb)}</button></div>`,
          )
          .join("")
      : '<div class="td-empty">Nothing caught today.</div>'
  }${(tdCatchAll ? caught.length > 4 : caught.length > shownC.length) ? `<a href="#" class="td-more" data-tdcatchall>${tdCatchAll ? "Show Fewer" : `${caught.length - shownC.length} more`}</a>` : ""}</section>
  <section class="td-sec td-brief" aria-label="Morning Brief"><div class="td-hd"><h3>Morning Brief</h3></div>${
    tdBriefFull
      ? `<div id="jv" class="td-jv"><div class="jv-body">${tdBriefText()
          .map((s, i) => `<p class="${0 === i ? "jv-lead" : ""}">${esc(s)}</p>`)
          .join("")}</div></div><a href="#" class="td-more" data-tdbrief>Shorter</a>`
      : '<a href="#" class="td-more" data-tdbrief>Read the Full Brief</a>'
  }</section>`;
}

// ---- the page ---------------------------------------------------------------------------------------------------------
function td2DateLine(T, long) {
  const d = parse(today()),
    day = long ? d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" }) : d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  return `${day} · ${T.rows.length} for you, ${T.late} late`;
}
function td2RowHtml(x, i, lead, desk, sel) {
  const c = x.c,
    ea = c.ea ? ` data-ea='${esc(JSON.stringify(c.ea))}'` : "",
    due = x.dueW ? `<span class="td2-due${x.late ? " late" : ""}">${esc(x.dueW)}</span>` : "",
    wait = x.wait ? `<span class="td2-wait">${td2Svg("clock", 12, 2.2)}${esc(x.wait)}</span>` : "";
  if (desk)
    return `<div class="td-card td2-row${sel ? " sel" : ""}" data-td2sel="${i}" data-kind="${esc(x.it.kind)}" data-id="${esc(String(x.it.id))}"${ea}><span class="td2-ic">${td2Svg(x.icon)}</span><span class="td2-what"><a href="#" data-tdrec>${esc(x.title)}</a><span class="td2-meta">${esc(x.meta)}</span>${wait}</span><span class="td2-amt">${x.amt ? esc(td2Money(x.amt)) : ""}</span><span class="td2-when${x.late ? " late" : ""}">${esc(x.dueW)}</span><span class="td2-act">${sel ? "" : `<button type="button" class="btn td-verb${c.ea ? " h4-act" : ""}" data-tdverb="${i}">${esc(c.verb)}</button>`}</span></div>`;
  let note = "";
  if (lead)
    try {
      note = tdWords(String(standardWhy(x.it) || "").replace(/^Because:\s*/, ""), 12);
    } catch (e) {}
  return `<div class="td-card td2-row" data-kind="${esc(x.it.kind)}" data-id="${esc(String(x.it.id))}"${ea}><span class="td2-ic">${td2Svg(x.icon)}</span><div class="td-txt td2-txt"><a href="#" class="td2-t" data-tdrec>${esc(x.title)}</a><span class="td2-meta">${due}${due && x.meta ? " · " : ""}${esc(x.meta)}</span>${wait}${note ? `<span class="td2-note">${esc(note)}</span>` : ""}${lead ? `<button type="button" class="btn primary td2-lead td-verb${c.ea ? " h4-act" : ""}" data-tdverb="${i}">${esc(c.verb)}${x.amt && !/\$/.test(c.verb) ? `, ${esc(td2Money(x.amt))}` : ""}</button>` : ""}</div>${lead ? "" : `<button type="button" class="btn td2-act td-verb${c.ea ? " h4-act" : ""}" data-tdverb="${i}">${esc(c.verb)}</button>`}</div>`;
}
function td2AsideHtml(x) {
  if (!x) return "";
  const c = x.c;
  let why = "",
    P = null;
  try {
    why = String(standardWhy(x.it) || "").replace(/^Because:\s*/, "");
    P = standardPrincipleOf(x.it);
  } catch (e) {}
  let leak = "";
  try {
    leak = standardIsLeak(x.it) ? td2MoneyWhy().why : "";
  } catch (e) {}
  const job = (() => {
      try {
        const pid = (x.it.t && x.it.t.projectId) || (x.it.open && x.it.open.project) || (x.it.nyh && x.it.nyh.projectId) || "";
        const p = pid && (DB.projects || []).find((q) => q.id === pid);
        return p ? shortName(p) : "";
      } catch (e) {
        return "";
      }
    })(),
    facts = [
      ["Due", x.dueW || "No date"],
      x.amt ? ["Amount", td2Money(x.amt)] : null,
      job ? ["Job", job] : null,
      x.wait ? ["Waiting", x.wait.replace(/^Waiting on /, "")] : null,
      P ? ["Principle", P.name || P.title || P.id] : null,
    ].filter(Boolean);
  return `<aside class="td2-aside" aria-label="${esc(x.title)}"><div class="td2-ak"><span class="td2-kick">${esc(td2Txt(c.why) || "")}</span><div class="td2-ah" role="heading" aria-level="2">${esc(td2Txt(c.line1) || x.title)}</div></div>${why ? `<p class="td2-anote">${esc(why)}</p>` : ""}<div class="td2-agrid">${facts.map(([k, v]) => `<span class="k">${esc(k)}</span><span>${esc(v)}</span>`).join("")}</div>${leak ? `<p class="td2-aleak">${esc(leak)}</p>` : ""}<span class="grow"></span><div class="td2-abtns"><button type="button" class="btn primary td2-lead td-verb${c.ea ? " h4-act" : ""}" data-td2lead>${esc(c.verb)}${x.amt && !/\$/.test(c.verb) ? `, ${esc(td2Money(x.amt))}` : ""}</button><div class="td2-a2"><button type="button" class="btn" data-td2open>Open the Record</button><button type="button" class="btn" data-td2rowask>Ask About This</button></div></div></aside>`;
}
function tdRender() {
  const root = homeRoot();
  if (!root) return;
  tdCtx = null;
  const desk = td2Desk(),
    T = td2Model(),
    r = T.r,
    k = (tdyMe() || {}).id || r;
  if (!td2Entered) {
    td2Entered = !0;
    td2EnteredMs = Date.now();
    td2Look().open = appNowIso();
  }
  const B = td2Brief(T),
    P = td2Pulse(),
    caught = tdCaught(T.M.appr),
    shownC = (tdShownC = tdCatchAll ? caught : caught.filter((x, i) => i < 4 || x.fresh)),
    selI = desk ? Math.min(Math.max(0, td2Sel[k] || 0), Math.max(0, T.shown.length - 1)) : -1,
    sel = desk ? T.shown[selI] : null,
    chips = `<div class="td-tabs td2-chips" role="${desk ? "tablist" : "group"}" aria-label="Show">${T.chips
      .map((x) => `<button type="button" ${desk ? 'role="tab" aria-selected' : "aria-pressed"}="${x.k === T.tab}" class="${x.k === T.tab ? "on" : ""}${"late" === x.k ? " late" : ""}" data-tdytabbtn="${x.k}">${esc(x.label)}<span class="n">${x.n}</span></button>`)
      .join("")}</div>`;
  let i = -1;
  const list = T.secs
    .map(
      (s) =>
        `<div class="td2-sh"><h2>${esc(s.name)}</h2><span>${s.n}</span></div><div class="td2-sec" data-td2sec="${s.k}">${s.rows
          .map((x) => {
            i++;
            return td2RowHtml(x, i, !desk && 0 === i, desk, desk && i === selI);
          })
          .join("")}</div>`,
    )
    .join("");
  const empty = `<div class="td-empty">${{ late: "Nothing of yours is late.", appr: "Nothing waits on your approval.", wait: "Nothing of yours waits on someone else." }[T.tab] || "Nothing waits on you today."}</div>`,
    more = T.hidden > 0 ? `<a href="#" class="td-more td2-more" data-tdyopen>${T.hidden} more</a>` : "all" === T.tab && tdyAllOpen ? '<a href="#" class="td-more td2-more" data-tdyopen>Show Fewer</a>' : "",
    quiet = `<button type="button" class="td2-quiet" aria-expanded="${td2QuietOpen}" data-td2quiet><span class="grow">${esc(td2QuietWords(P, caught.length))}</span>${td2Svg("down", 16, 2)}</button>${td2QuietOpen ? `<div class="td2-quietbox">${td2QuietHtml(P, caught, shownC)}</div>` : ""}`,
    cal = (() => {
      if (!desk || "function" != typeof lnCalFor) return "";
      try {
        const C = lnCalFor(lnUid()).filter((x) => x.day === today()).slice(0, 3);
        return C.length ? `<section class="td2-day" aria-label="Your Day"><h2>Your Day</h2><div class="td2-dayg">${C.map((x) => `<div class="td2-ev"><b>${esc(td2Clock(x.e.start) || "All day")}</b><span>${esc(tdWords(x.title, 7))}</span></div>`).join("")}</div></section>` : "";
      } catch (e) {
        return "";
      }
    })(),
    rowsHtml = `<section class="td-sec td-do td2-list" aria-label="Your work today" data-tdytab="${T.tab}"><span class="td-cnt" hidden data-tdcount="${T.Q.length}">${T.Q.length}</span>${desk ? '<div class="td2-cols"><span></span><span>What</span><span>Amount</span><span>When</span><span></span></div>' : ""}${T.shown.length ? list : empty}${more}</section>`;
  root.innerHTML = desk
    ? `<div class="td-home td2 td2-desk" data-tdrole="${r}">${td2BriefHtml(B, !0)}<div class="ph td-ph td2-ph"><div class="td2-title"><h2>Today</h2><span class="td2-date">${esc(td2DateLine(T, !0))}</span>${chips}</div></div><div class="td2-main"><div class="td2-left">${rowsHtml}${quiet}${cal}</div>${td2AsideHtml(sel)}</div></div>`
    : `<div class="td-home td2 td2-phone" data-tdrole="${r}"><div class="ph td-ph td2-ph"><div><h2>Today</h2></div></div>${chips}${td2BriefHtml(B, !1)}${rowsHtml}${quiet}</div>`;
  td2Cur = { T: T, B: B, sel: sel, shownC: shownC, P: P };
  // wiring
  root.querySelectorAll(".td-do .td-card").forEach((el, j) => {
    const x = T.shown[j];
    if (!x) return;
    const a = el.querySelector("[data-tdrec]");
    a &&
      (a.onclick = (e) => {
        e.preventDefault(), e.stopPropagation(), x.c.go();
      });
    const v = el.querySelector("[data-tdverb]");
    v &&
      (v.onclick = (e) => {
        e.preventDefault(), e.stopPropagation(), x.c.run();
      });
    desk &&
      (el.onclick = (e) => {
        if (e.target.closest("a, button")) return;
        (td2Sel[k] = j), render();
      });
  });
  const lead = root.querySelector("[data-td2lead]");
  lead && sel && (lead.onclick = (e) => (e.preventDefault(), sel.c.run()));
  const op = root.querySelector("[data-td2open]");
  op && sel && (op.onclick = (e) => (e.preventDefault(), sel.c.go()));
  const ra = root.querySelector("[data-td2rowask]");
  ra && sel && (ra.onclick = (e) => (e.preventDefault(), td2AskAbout(`${sel.title} (${sel.meta}${sel.dueW ? ", " + sel.dueW : ""}).`)));
  root.querySelectorAll("[data-td2go]").forEach(
    (a) =>
      (a.onclick = (e) => {
        e.preventDefault();
        const l = B.lines[+a.dataset.td2go];
        l && l.go && l.go();
      }),
  );
  const ask = root.querySelector("[data-td2ask]");
  ask && (ask.onclick = (e) => (e.preventDefault(), td2AskAbout(B.plain.join(" ") || "nothing new since my last look.")));
  root.querySelectorAll("[data-tdytabbtn]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.preventDefault(), tdyTabSet(b.dataset.tdytabbtn), (td2Sel[k] = 0), render();
      }),
  );
  const topen = root.querySelector("[data-tdyopen]");
  topen && (topen.onclick = (e) => (e.preventDefault(), (tdyAllOpen = !tdyAllOpen), render()));
  const q = root.querySelector("[data-td2quiet]");
  q && (q.onclick = (e) => (e.preventDefault(), (td2QuietOpen = !td2QuietOpen), render()));
  const PP = TD_PULSE[r] || TD_PULSE.owner;
  root.querySelectorAll("[data-tdpulse]").forEach(
    (a) =>
      (a.onclick = (e) => {
        e.preventDefault();
        const t = PP.find((y) => y.k === a.dataset.tdpulse);
        t && tdPulseOpen(t);
      }),
  );
  root.querySelectorAll("[data-tdcatch]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.preventDefault();
        const x = shownC[+b.dataset.tdcatch];
        x && x.run();
      }),
  );
  const ca = root.querySelector("[data-tdcatchall]");
  ca && (ca.onclick = (e) => (e.preventDefault(), (tdCatchAll = !tdCatchAll), render()));
  const br = root.querySelector("[data-tdbrief]");
  br && (br.onclick = (e) => (e.preventDefault(), (tdBriefFull = !tdBriefFull), render()));
  try {
    stdLastQueue = T.shown.map((x) => x.it);
  } catch (e) {}
  // the model re-words the facts once for these facts; until it answers (or when it cannot) the plain lines stand
  try {
    !B.nothing && B.facts.length && !(td2Look().cache && td2Look().cache.key === B.key) && aiReady() && td2Polish(B.facts, B.key);
  } catch (e) {}
  tdCtx = null;
}

// ---- the last look: "Since <time>" is when the person last had Today open, on the app's clock ----------------------
function td2LeaveToday() {
  if (!td2Entered) return;
  td2Entered = !1;
  // a look is the person on Today, not a draw on the way somewhere else (a sign-in that passes through Today): the
  // wall clock only measures that pause; the stamp kept is the app's clock
  if (Date.now() - td2EnteredMs < 1200) return;
  try {
    const L = td2Look();
    L.open && (L.seen = L.open);
    td2Cur && td2Cur.B && (L.seenKey = td2Cur.B.key);
    save();
  } catch (e) {}
}
{
  const base = render;
  render = function () {
    td2Tick++;
    try {
      ("home" !== view || !tdOn()) && td2LeaveToday();
    } catch (e) {}
    const r = base.apply(this, arguments);
    try {
      td2Chrome();
    } catch (e) {
      console.warn("today chrome", e);
    }
    return r;
  };
}
if ("function" == typeof signIn) {
  const base = signIn;
  signIn = function () {
    td2LeaveToday();
    td2QuietOpen = !1;
    tdyAllOpen = !1;
    return base.apply(this, arguments);
  };
}

// ---- the chrome: the phone's header (Today over its date line, Search, Ask) and the Today badge -------------------
function td2Chrome() {
  const on = "home" === view && tdOn() && !!td2Cur,
    phone = on && !td2Desk(),
    // the foreman's Today (TodayForeman): the same header, his job and the day under the title, and the clock card
    fm = "ftoday" === view && "foreman" === role() && window.innerWidth <= 760,
    body = document.body;
  body.classList.toggle("td2-on", on);
  body.classList.toggle("td2-ph", phone || fm);
  body.classList.toggle("td2-fm", fm);
  const hb = document.querySelector("header.topbar");
  let d = document.getElementById("td2-hdate");
  if ((phone || fm) && hb) {
    const c = document.getElementById("crumbs");
    d || ((d = document.createElement("span")), (d.id = "td2-hdate"), (d.className = "td2-hdate"), c ? c.after(d) : hb.appendChild(d));
    const job = fm ? ((document.querySelector("#ftoday-body .f-hero b") || {}).textContent || "").trim() : "";
    d.textContent = fm ? [job, parse(today()).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })].filter(Boolean).join(" \u00b7 ") : td2DateLine(td2Cur.T, !1);
  } else d && d.remove();
  if (fm) {
    const h = document.querySelector("#ftoday-body .f-hero");
    if (h && !h.querySelector(".td2-clk")) {
      h.classList.add("td2-clock");
      const t = document.createElement("span");
      (t.className = "td2-clk"), (t.textContent = td2Clock(appNowIso()));
      const top = h.firstElementChild;
      top && top.appendChild(t);
    }
  }
  // the Today badge: the late rows, red, on the bar and in the menu
  const n = TD2_SPEC[role()] ? td2LateN() : 0;
  document.querySelectorAll('#mtabs [data-mv="home"]').forEach((b) => {
    let i = b.querySelector("i.n");
    n ? (i || ((i = document.createElement("i")), (i.className = "n"), b.appendChild(i)), (i.textContent = n), i.classList.add("late"), b.setAttribute("aria-label", `Today, ${n} late`)) : i && i.remove();
  });
}
// the menu's Today group counts the same late rows (it counted the Approvals queue)
if ("function" == typeof mnGroupN) {
  const base = mnGroupN;
  mnGroupN = function (g, r) {
    if (g && "home" === g.id && TD2_SPEC[r] && r === role()) return td2LateN();
    return base.apply(this, arguments);
  };
}
// The phone bars and the first screen, as the mockups draw them. Billing and the controller start on Today (their
// boards light Today first), as every office role does; Banking and Billing keep their place on the bar.
(function td2Bars() {
  if ("object" != typeof MENU) return;
  const set = (r, bar) => MENU[r] && (MENU[r].phone = bar);
  set("owner", [
    ["home", "Today", "today"],
    ["ovjobs", "Projects", "field"],
    ["ovsales", "Sales", "sales"],
    ["chat", "Messages", "chat"],
  ]);
  set("pm", [
    ["home", "Today", "today"],
    ["ovjobs", "Projects", "field"],
    ["clients", "Clients", "people"],
    ["tkall", "Tasks", "tasks"],
    ["chat", "Messages", "chat"],
  ]);
  set("coord", [
    ["home", "Today", "today"],
    ["chat", "Messages", "chat"],
    ["tkall", "Tasks", "tasks"],
    ["proc", "Buy Board", "buy"],
  ]);
  set("billing", [
    ["home", "Today", "today"],
    ["billing", "Billing", "billing"],
    ["clients", "Clients", "people"],
    ["chat", "Messages", "chat"],
  ]);
  set("controller", [
    ["home", "Today", "today"],
    ["bank", "Banking", "money"],
    ["ap", "Bills & Payroll", "billing"],
    ["chat", "Messages", "chat"],
  ]);
  ["billing", "controller"].forEach((r) => MENU[r] && ((MENU[r].home = "home"), "object" == typeof IA_HOME && (IA_HOME[r] = "home")));
  const F = MENU.foreman;
  F &&
    F.bar &&
    ((F.bar = [
      ["ftoday", "Today", "home"],
      ["flog", "Daily Log", "list"],
      ["fsite", "Site", "box"],
      ["req", "Requests", "box"],
      ["chat", "Messages", "chat"],
    ]),
    (F.rest = (F.rest || []).filter((x) => !["fsite", "req", "flog", "ftoday", "chat"].includes(x[0]))));
  try {
    "function" == typeof mnKnowAll && mnKnowAll();
    "function" == typeof mnHomeGroups && mnHomeGroups();
  } catch (e) {}
})();
