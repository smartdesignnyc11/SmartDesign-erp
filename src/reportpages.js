/* =====================================================================================================================
   The Reports pages (Alan, 11-03: docs/mockups/reports/, SPEC.md). Reports is where money is read, by the question a
   person asks; Accounting is where it is acted on. Four pages, each opening on what is at risk (every line names whose
   it is and opens the page where that person acts), then where things stand, then the detail one tap down with chips.
   A report holds no queue and creates nothing but a report.

     Job Profitability (reports: jobs)   one row per job; Margin and Work in Progress are two views of the same rows.
                                         The WIP Schedule stays a named standard report (the bank, the surety)
     Cash (reports: cash)                one Safe to Spend (safeToSpend), its parts, the 13 weeks; Client Funds,
                                         Receivables and Payables are its views
     Financial Statements (reports: stmt) the P&L, Balance Sheet, Cash Flow, Budget vs Actual and the Pack for any period
                                         (a month not closed is a Draft; the Weekly Flash is the Pack for a week), and
                                         what stands behind the numbers, manual entries flagged
     Report Builder (reports: builder)   saved reports, the standard reports (moved to the role that acts, kept here),
                                         Pinned (the Dashboard's My Dashboard), and Start From every queryable table

   One view, `reports`, holds the four (the registry: tests/ia_map.py CONTEXT_OK). The old tabs (repTab) are the detail
   under each page's chip and forward to it (SPEC §3): All Projects and Project Profitability are Margin, the WIP
   Schedule is Work in Progress, Receivables, Payables and the Cash Forecast are Cash's views, P&L Detail, Statements,
   Budget vs Actual, the Monthly Pack, the Weekly Flash and the Three-Way Tie-Out are Financial Statements, and every
   other tab is a standard report in the Report Builder. Billing's Client Funds tab is Cash's Client Funds. The
   Dashboard is the Report Builder's Pinned; the coordinator and the designer, who open no Reports page, keep it as
   their Report Builder.

   Design gate (BACKLOG §1.16): no new store, list or queue. Every figure is read from the one function its Accounting
   definition lives in (safeToSpend, PRED.safeToSpend.rows, setAside, jobFin and jobCostPosted, jobCostTie,
   billedAhead, companyBalance, cashForecast, acCollections, apAging, companyPL, glBS, budRows, truthCoverage,
   truthManual, closeChecklist, wipAtClose); nothing here recomputes one. Reading never writes.
   ===================================================================================================================== */

const RW_PAGES = {
    jobs: { name: "Job Profitability", lead: "Every job: what it will make, and where its billing stands" },
    cash: { name: "Cash", lead: "What is ours to spend, what is the client's, and the next 13 weeks" },
    stmt: { name: "Financial Statements", lead: "The firm's statements and the Pack, for any week or month" },
    builder: { name: "Report Builder", lead: "Any record in the system, filtered, grouped and totalled, then saved, pinned or sent to Excel" },
  },
  // the old tabs, each placed on its new page (SPEC §3)
  RW_TAB_PAGE = {
    portfolio: "jobs",
    profit: "jobs",
    wip: "jobs",
    cash13: "cash",
    funds: "cash",
    ar: "cash",
    payables: "cash",
    company: "stmt",
    financials: "stmt",
    statements: "stmt",
    budget: "stmt",
    pack: "stmt",
    flash: "stmt",
    tieout: "stmt",
    searches: "builder",
    costintel: "builder",
    studio: "builder",
    library: "builder",
    submittals: "builder",
    dlsum: "builder",
    progvp: "builder",
    statement: "builder",
    analyst: "builder",
  },
  // where each seat lands when it opens Reports without naming a page (SPEC §4)
  // the standard reports: each lives with the role that acts on it and is kept here too, so nothing is lost and
  // Cmd-K finds it. [key, name, where it lives, how it opens, the page a role must open for it to be listed]
  RW_STD = [
    ["wip", "Work in Progress Schedule", "Lives on Job Profitability, Work in Progress. For the bank and the surety.", { page: "jobs", jobs: "wip" }],
    ["statement", "Client Statement", "Lives on the client record and the job's Contract and Billing.", { std: "statement" }],
    ["cash13", "13-Week Cash Forecast", "Lives on Cash, Next 13 Weeks.", { page: "cash", cash: "weeks" }],
    ["ar", "Receivables Aging", "Lives on Cash, Receivables. The chase is Billing's Collections.", { page: "cash", cash: "ar" }],
    ["payables", "Payables Aging", "Lives on Cash, Payables. Bills are paid on Bills and Payroll.", { page: "cash", cash: "ap" }],
    ["pack", "Monthly Pack", "Lives on Financial Statements, for any month.", { page: "stmt", pack: 1 }],
    ["flash", "Weekly Flash", "Lives on Financial Statements, This Week.", { page: "stmt", pack: 1, per: "week" }],
    ["tieout", "Three-Way Tie-Out", "QuickBooks, the bank and the ERP by month. Lives on Financial Statements.", { page: "stmt", detail: "tieout" }],
    ["library", "Cost Library", "Lives on Purchasing, the price book. Saved here too.", { std: "library" }],
    ["costintel", "Cost Intelligence", "Lives on each job's Budget and Purchasing's price history.", { std: "costintel" }],
    ["submittals", "Submittal Log", "Lives on Decisions, every job. Saved here too.", { std: "submittals" }],
    ["dlsum", "Daily Log Summary", "Lives on each job's Site. Saved here too.", { std: "dlsum" }],
    ["progvp", "Progress vs Plan", "Lives on each job's Contract and Billing, the measure billing bills on.", { std: "progvp" }],
    ["studio", "Studio", "Design fees, hours and utilization. Lives on Design.", { std: "studio" }],
    ["analyst", "The Analyst's Review", "Each finding lives on the page whose role acts on it; the review itself is Ask.", { std: "analyst" }],
    ["irs", "1099 Register", "Lives on Books, Tax and 1099.", { view: "gl", chip: "tax" }],
    ["waivers", "Lien-Waiver Register", "Lives on Bills and Payroll, on each sub's bill.", { view: "ap" }],
  ];
// the page's state. `tab` is the repTab this state was set for: a link that sets repTab itself (Books' "Open the WIP
// Schedule", a test, the old tab buttons) is honoured by reading the page from it
const rwS = { page: "", jobs: "margin", cash: "weeks", kind: "pl", pack: !1, detail: "", builder: "saved", std: "", wk: -1, q: "", tab: null, landed: !1, packYm: "" };
const rwMay = (v) => (ROLE_VIEWS[role()] || []).includes(v),
  rwPhone = () => ("function" == typeof isMobile ? isMobile() : innerWidth <= 760),
  rwWho = (seat) => {
    const r = role();
    return seat === r || ("owner" === seat && "owner" === r) ? "you" : { owner: "Alan", controller: "the controller", billing: "billing", pm: "the PM" }[seat] || seat;
  },
  rwCap = (s) => String(s || "").replace(/^./, (c) => c.toUpperCase()),
  rwC = (v) => ("function" == typeof rpCents ? rpCents(v) : money(v)),
  // a figure in whole dollars (the figure), its build-up to the cent (one text, the chief of staff, 11-03)
  rwD = (v) => ((+v || 0) < -0.004 ? "−" : "") + money(Math.abs(Math.round(+v || 0))),
  rwPct = (v) => `${Math.round(+v || 0) < 0 ? "−" : ""}${Math.abs(Math.round(+v || 0))}%`,
  rwEsc = (s) => esc(String(null == s ? "" : s)),
  // the entity the Reports bar scopes to (Consolidated is every entity)
  rwEnt = () => ("undefined" != typeof repEntity && repEntity ? repEntity : "all");
// the page on screen (the menu reads it: mnTabOf)
function rwPageNow() {
  if ("dashboard" === view) return "builder";
  if ("reports" !== view) return "";
  return rwS.page || RW_TAB_PAGE[repTab] || rwLand();
}
// a seat's Reports page with no page named is its first Reports entry (the chief of staff, 11-04): never a page its menu
// does not list (the PM and billing landed on the firm's P&L and the Pack)
function rwLand() {
  try {
    const g = (mnBuild(role()) || { work: [] }).work.find((x) => "reports" === x.id),
      it = g && g.items.find((x) => "reports" === x.v);
    return it ? (it.tab && RW_PAGES[it.tab] ? it.tab : "jobs") : "jobs";
  } catch (e) {
    return "jobs";
  }
}

// ---- the state follows repTab, and repTab follows the state ---------------------------------------------------------
function rwFromTab(t) {
  const pg = RW_TAB_PAGE[t] || rwLand();
  rwS.page = pg;
  if ("jobs" === pg) rwS.jobs = "wip" === t ? "wip" : "margin";
  if ("cash" === pg) rwS.cash = { cash13: "weeks", funds: "funds", ar: "ar", payables: "ap" }[t] || "weeks";
  if ("stmt" === pg) {
    rwS.detail = "tieout" === t ? "tieout" : "";
    // the Pack open: the month's ("pack") or the week's Flash ("flash"); opening an old tab never moves the period
    rwS.pack = "pack" === t ? "pack" : "flash" === t ? "flash" : !1;
    rwS.kind = { company: "pl", financials: "bs", statements: "bs", budget: "bva" }[t] || rwS.kind;
  }
  if ("builder" === pg) "searches" === t || !RW_TAB_PAGE[t] ? ((rwS.builder = "saved"), (rwS.std = "")) : ((rwS.builder = "standard"), (rwS.std = t));
}
function rwTabOf() {
  const P = rwS.page;
  if ("jobs" === P) return "wip" === rwS.jobs ? "wip" : "profit" === repTab ? "profit" : "portfolio";
  if ("cash" === P) return { weeks: "cash13", funds: "cash13", ar: "ar", ap: "payables" }[rwS.cash] || "cash13";
  if ("stmt" === P) return "tieout" === rwS.detail ? "tieout" : rwS.pack ? ("flash" === rwS.pack ? "flash" : "pack") : { pl: "company", bs: "financials", cf: "financials", bva: "budget" }[rwS.kind] || "company";
  if ("builder" === P) return rwS.std || "searches";
  return repTab;
}
// before the old renderer draws: the page from repTab when a link set it, then repTab from the page
function rwSync() {
  if ("reports" !== view) return;
  // Billing's old Client Funds tab and Reports' old "funds" are Cash's Client Funds (SPEC §3)
  if ("dash" === repTab) rwGo(rwLand());
  else if (rwS.tab !== repTab) rwFromTab(repTab);
  const t = rwTabOf();
  repTab = t;
  rwS.tab = t;
}
// the period the statements read: REP is the source (the old controls and the tests set it); the chips set REP
const RW_PER = [
  ["week", "This Week"],
  ["last", ""],
  ["month", ""],
  ["ytd", "Year to Date"],
];
const rwYm = () => today().slice(0, 7),
  rwPrevYm = () => {
    const d = parse(today().slice(0, 7) + "-01");
    return iso(addDays(d, -1)).slice(0, 7);
  },
  rwMonthName = (ym) => `${["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][+String(ym).slice(5, 7) - 1] || ""} ${String(ym).slice(0, 4)}`,
  rwWeekStart = () => {
    const d = parse(today()),
      k = (d.getDay() + 6) % 7;
    return iso(addDays(d, -k));
  },
  rwPerLabel = (k) => ({ week: "This Week", last: rwMonthName(rwPrevYm()), month: `${rwMonthName(rwYm()).split(" ")[0]} to Date`, ytd: "Year to Date" })[k] || "";
function rwPer() {
  try {
    if ("custom" === REP.preset && REP.from === rwWeekStart() && (REP.to || today()) >= today()) return "week";
    return { lm: "last", tm: "month", ty: "ytd" }[REP.preset] || "";
  } catch (e) {
    return "";
  }
}
function rwSetPer(k, quiet) {
  if ("week" === k) (REP.preset = "custom"), (REP.from = rwWeekStart()), (REP.to = today());
  else REP.preset = { last: "lm", month: "tm", ytd: "ty" }[k] || "ty";
  // the Pack follows the period: last month (a Draft until it is closed), the open month, the week's Flash
  rwS.packYm = "last" === k ? rwPrevYm() : "";
  quiet || (rwS.tab = null);
}
function rwRange() {
  try {
    return repRangeOf().range;
  } catch (e) {
    return [today().slice(0, 4) + "-01-01", today()];
  }
}

// ---- the figures, each from its one function ------------------------------------------------------------------------
function rwJobs() {
  let P = [];
  if ("pm" === role() && "function" == typeof ovRows)
    try {
      P = ovRows("jobs").map((x) => x.p).filter(Boolean);
    } catch (e) {}
  P.length || (P = (DB.projects || []).slice());
  return P.map((p) => {
    let J = null,
      C = null,
      A = null;
    try {
      J = jobFin(p);
    } catch (e) {
      return null;
    }
    try {
      C = jobCostPosted(p);
    } catch (e) {}
    try {
      A = billedAhead(p.id);
    } catch (e) {}
    return { p: p, J: J, C: C, A: A };
  }).filter((x) => x && (x.J.contract > 0 || x.J.actual > 0.005 || x.J.committed > 0.005 || x.J.billed > 0.005));
}
// cost to cost, as jobFin works it: the cost for progress is cost to date less money paid ahead (not progress) and
// purchases billed back to the client; earned is the contract times that over the projected cost (less the same
// billed-back cost), plus what was billed back. The WIP view prints each number it rests on.
function rwCtc(J) {
  const pre = r2(+J.prepaidNotProgress || 0),
    rc = r2(+J.rebillCost || 0),
    cost = r2(Math.max(0, (+J.actual || 0) - pre - rc)),
    proj = r2((+J.eac || 0) - rc),
    pct = +J.pct || 0;
  return { pre: pre, rc: rc, cost: cost, proj: proj, pct: pct, held: J.pctHeld || null, earned: r2(+J.earned || 0), rb: r2(+J.rebillBilled || 0) };
}
function rwJobRisk() {
  const out = [],
    B = (() => {
      try {
        return companyBalance();
      } catch (e) {
        return {};
      }
    })(),
    early = new Set((B.paidBeforeApproval || []).map((b) => b.id));
  rwJobs().forEach(({ p, J }) => {
    if (!J.contract || !(J.plannedGPPct > 0) || !(J.estGPPct < J.plannedGPPct - 0.005)) return;
    // the estimate line that moved the margin most: its estimate at completion past its budget (jobFin's own lines)
    const over = (J.eacLines || [])
      .map((l) => ({ l: l, amt: r2((+l.eac || 0) - (+l.budget || 0)) }))
      .filter((x) => x.amt > 0.5)
      .sort((a, b) => b.amt - a.amt)[0];
    let why = "",
      go = { kind: "budget", pid: p.id };
    if (over) {
      const amt = over.amt,
        ref = "function" == typeof findLine ? findLine(over.l.key) : null,
        name = (ref && ref.line && (ref.line.item || ref.line.desc)) || over.l.name || over.l.item || "One",
        b = (DB.bills || []).find((x) => early.has(x.id) && x.projectId === p.id && (x.line === over.l.key || (x.lines || []).some((y) => y.line === over.l.key))),
        po = b && b.poId && (DB.pos || []).find((x) => x.id === b.poId);
      why = `${name} line ${money(amt)} over its budget`;
      if (b) {
        why += `: ${b.number} billed ${money(billTotal(b))}${po ? ` on a ${money(poTotal(po).total)} PO` : ""}. With ${rwWho("owner")}, on the bill.`;
        go = { kind: "bill", id: b.id };
      } else why += `. With ${rwWho("pm")}, on the job's Budget.`;
    } else why = `With ${rwWho("pm")}, on the job's Budget.`;
    out.push({ title: `${shortName(p)}: margin at completion ${J.estGPPct}%, bid ${J.plannedGPPct}%`, why: why, go: go });
  });
  if ("pm" !== role()) {
    // payroll that sits on no job: the job margins leave it out until the controller splits it
    (DB.payroll || [])
      .filter((r) => r.total && ["draft", "submitted", "pm-approved"].includes(r.status))
      .forEach((r) => {
        const un = (r.alloc || []).filter((x) => x.unallocated && !x.projectId).reduce((a, x) => a + (+x.pct || 0), 0);
        if (!(un > 0.5)) return;
        const amt = r2((r.total * un) / 100);
        out.push({ title: `Job margins leave out ${money(amt)} of payroll`, why: `Payroll ${r.period || ""} is ${Math.round(un)}% on Unallocated Labor. With ${rwWho("controller")}: split it and the labor lands on the jobs.`, go: { kind: "payroll", id: r.id } });
      });
    const J = rwJobs().filter((x) => x.J.over > 0.005),
      over = r2(J.reduce((a, x) => a + x.J.over, 0));
    J.length &&
      out.push({
        title: `Over-Billed (WIP) ${money(over)} on ${J.length} job${1 === J.length ? "" : "s"}`,
        why: `Billed ahead of the work earned. With ${rwWho("controller")}, who reconciles it with Billed Ahead of the Work before the close.`,
        go: rwMay("gl") ? { kind: "close" } : { kind: "wip" },
      });
  }
  return out;
}
function rwCashRisk() {
  const out = [];
  let B = {};
  try {
    B = companyBalance();
  } catch (e) {}
  const pr = (DB.payroll || []).filter((r) => r.total && r.payDate && r.payDate < today() && !["paid", "void", "approved"].includes(r.status));
  pr.forEach((r) => {
    const d = dayDiff(r.payDate, today()),
      split = (r.alloc || []).some((x) => x.unallocated && !x.projectId && +x.pct > 0.5);
    out.push({
      title: `Payroll ${money(r.total)} is ${d} day${1 === d ? "" : "s"} past pay day`,
      why: split ? `With ${rwWho("controller")} to split by job; then it reaches ${rwWho("owner")} to approve.` : `With ${rwWho("owner")} to approve.`,
      go: { kind: "payroll", id: r.id },
    });
  });
  (B.paidBeforeApproval || []).forEach((b) => {
    const po = b.poId && (DB.pos || []).find((x) => x.id === b.poId),
      over = po ? r2(billTotal(b) - poTotal(po).total) : 0;
    out.push({
      title: `${money(billTotal(b))} left the bank before approval`,
      why: `${b.number}, ${b.vendor}${over > 0.5 ? `, ${money(over)} over its PO` : ""}. With ${rwWho("owner")}, on the bill.`,
      go: { kind: "bill", id: b.id },
    });
  });
  let U = [];
  try {
    U = undepositedReceipts();
  } catch (e) {}
  const byC = {};
  U.forEach((x) => ((byC[x.c.id] = byC[x.c.id] || { c: x.c, amt: 0 }).amt = r2(byC[x.c.id].amt + x.amt)));
  Object.values(byC).forEach(({ c, amt }) =>
    out.push({
      title: `${money(amt)} of ${c.name.replace(/ family$/, "")} payments ${amt === 1 ? "is" : "are"} not in the bank`,
      why: `With ${rwWho("billing")}, who asks the client; not cash until the bank shows it.`,
      go: { kind: "undep", id: c.id },
    }),
  );
  return out;
}
// the parts of Safe to Spend: the one build-up Today's sheet prints (PRED.safeToSpend.rows), with what each rests on
function rwSafeParts() {
  const X = safeToSpend(),
    B = X.B,
    rows = PRED.safeToSpend.rows(),
    acct = (DB.accounts || []).filter((a) => "bank" === a.type),
    cards = (DB.accounts || []).filter((a) => "bank" !== a.type),
    stmt = (a) => {
      const L = (DB.bankImports || []).filter((r) => r.acct === a.id || r.acctId === a.id).map((r) => r.to || r.end || r.through || "").filter(Boolean).sort();
      return L[L.length - 1] || "";
    },
    sub = (k) => {
      if (/^In the bank/.test(k)) return acct.map((a) => `${a.name.split(" ")[0]} ····${a.last4 || ""}${stmt(a) ? `, statement through ${fmt(stmt(a))}` : ""}`).join(" · ");
      if (/^Credit cards/.test(k)) return cards.map((a) => `${a.name.split(" ").slice(0, 2).join(" ")} ····${a.last4 || ""} ${money(Math.abs("function" == typeof acctBook ? acctBook(a) : +a.balance || 0))}`).join(" · ");
      if (/^Payroll due/.test(k)) return (DB.payroll || []).filter((r) => r.total && !["paid", "void"].includes(r.status) && (!r.payDate || r.payDate <= today())).map((r) => `${r.period || ""}${r.payDate && r.payDate < today() ? `, past due since ${fmt(r.payDate)}` : ""}`).join(" · ");
      if (/^Set aside/.test(k)) return "Client money for work not done, job by job: paid to us with a bank line, less earned (the work measured or billed on the job, or its cost to date, whichever is more), never below $0. Billed and unpaid is never set aside; client funds sit inside it.";
      if (/^Ours today/.test(k)) return "Before the 13-week check";
      if (/^13-week low/.test(k)) return "The same set-aside comes off every week of the forecast, so the low compares like with like";
      return "";
    };
  return {
    X: X,
    safe: X.safe,
    rows: rows.filter((r) => "figure" !== r[2]).map((r) => ({ k: r[0], v: r[1], total: "total" === r[2], sub: sub(r[0]) })),
    notCounted: B.undeposited ? `Not counted: ${money(B.undeposited)} recorded, not in the bank.` : "",
  };
}
function rwCashLists(k) {
  let B = {};
  try {
    B = companyBalance();
  } catch (e) {}
  const R = [];
  if ("funds" === k) {
    // the client's money on hand for purchases still to make, and what was spent ahead of what the client paid: parts
    // of the cash above, sitting inside the set-aside, never a second "ours" figure
    let F = null;
    try {
      F = "function" == typeof clientFundsLedger ? clientFundsLedger() : null;
    } catch (e) {}
    const L = Array.isArray(F) ? F : [];
    R.push({ k: "Client funds held for materials", sub: "Collected on lines with buying left. Inside the set-aside above, never added to it.", v: money(B.clientFunds || 0), strong: 1 });
    L.filter((x) => (+x.reserved || 0) > 0.005)
      .sort((a, b) => (b.reserved || 0) - (a.reserved || 0))
      .forEach((x) => {
        const p = x.projectId ? (DB.projects || []).find((y) => y.id === x.projectId) : null;
        R.push({ k: x.item || x.name || x.desc || x.key, sub: `${p ? shortName(p) + " · " : ""}collected ${money(x.collected || 0)} · spent ${money(x.spent || 0)}`, v: money(x.reserved) });
      });
    R.push({ k: "Spent ahead of what the client has paid", sub: L.filter((x) => (+x.floated || 0) > 0.005).map((x) => `${x.item || x.name || x.key} ${money(x.floated)}`).join(" · ") || "Nothing spent ahead", v: money(B.floated || 0), strong: 1, tone: B.floated > 0.005 ? "warn" : "" });
    R.push({ k: "Set aside, all jobs", sub: (B.setAsideBy || []).filter((x) => x.amt > 0.005).map((x) => `${x.name} ${money(x.collected)} received less ${money(x.earned)} earned`).join(" · ") || "Nothing received ahead of the work", v: money(B.setAside || 0) });
    return { lead: "The client's money on hand for purchases still to make, and what we have spent ahead of what the client has paid. Parts of the cash above, never a second \"ours\" figure.", rows: R };
  }
  if ("ar" === k) {
    const C = acCollections("");
    C.rows.forEach((r) => R.push({ k: `${r.c.name} · ${r.i.number}`, sub: `${r.p ? shortName(r.p) + " · " : ""}${r.age > 0 ? `${r.age} days past due` : `due ${fmt(r.i.due)}`}`, v: money(r.bal), tone: r.age > 0 ? "bad" : "", open: { kind: "invoice", c: r.c.id, id: r.i.id } }));
    const ag = C.aging.filter(([l]) => "Current" !== l).map(([l, v]) => `${l.replace(" Days", "")} ${money(v)}`).join(" · ");
    R.push({ k: C.aging.slice(1).some(([, v]) => v > 0.005) ? "Open" : "Open, all current", sub: ag, v: money(C.open), strong: 1, key: "artotal" });
    R.push({ k: "Retainage held by clients", sub: "In its own bucket until release", v: money(C.retainage) });
    B.undeposited && R.push({ k: "Recorded, not in the bank", sub: "Not counted as collected until the bank shows it", v: money(B.undeposited), tone: "bad" });
    return { lead: "Every open invoice by age; retainage in its own bucket. The chase is on Billing, Collections.", rows: R };
  }
  if ("ap" === k) {
    let A = { items: [], total: 0 };
    try {
      A = apAging();
    } catch (e) {}
    (A.items || []).forEach((x) => R.push({ k: `${"payroll" === x.kind ? "Payroll" : x.who} ${x.number || ""}`.trim(), sub: x.days > 0 ? `${x.days} day${1 === x.days ? "" : "s"} past due` : `due ${fmt(x.due)}`, v: money(x.amt), tone: x.days > 0 ? "bad" : "", open: "payroll" === x.kind ? { kind: "payroll", id: x.id } : { kind: "bill", id: x.id } }));
    R.push({ k: "Open, bills and payroll", sub: `Bills ${money(A.bills || 0)} · payroll ${money(A.payroll || 0)} · ${money(A.overdue || 0)} past due`, v: money(A.total || 0), strong: 1, key: "aptotal" });
    (B.paidBeforeApproval || []).length && R.push({ k: "Paid before approval, not in the aging", sub: `${B.paidBeforeApproval.map((b) => b.number).join(", ")} needs a signature, not a payment`, v: money(B.paidBeforeApprovalAmt || 0), tone: "warn" });
    (B.possiblyPaid || []).length && R.push({ k: "Held, possibly already paid", sub: B.possiblyPaid.map((b) => b.number).join(", "), v: money(B.possiblyPaidAmt || 0), tone: "warn" });
    R.push({ k: "Open purchase orders", sub: "Committed, not yet billed", v: money(B.openPO || 0) });
    R.push({ k: "Retainage held from subs", sub: "Paid at release", v: money(B.apRet || 0) });
    return { lead: "What the firm owes, by days past due. Bills are paid on Bills and Payroll.", rows: R };
  }
  return { lead: "", rows: [] };
}
// the statements for the period on screen, each from its function
function rwStmtRows(kind) {
  const R = rwRange(),
    rows = [];
  if ("pl" === kind) {
    const P = companyPL(R);
    rows.push({ k: "Revenue, earned", v: money(P.income), sub: `${money(P.collected)} collected with a bank line${P.unbanked ? ` · ${money(P.unbanked)} recorded, not in the bank` : ""}`, key: "income" });
    rows.push({ k: `Job cost${P.income ? ", " + rwPct((100 * P.cogsT) / P.income) : ""}`, v: money(P.cogsT), key: "cogs" });
    rows.push({ k: `Gross profit${P.income ? ", " + rwPct(P.grossPct) : ""}`, v: money(P.gross), strong: 1, key: "gross" });
    rows.push({ k: `Overhead${P.needsCat ? `, incl. ${money(P.needsCat)} not yet coded` : ""}`, v: money(P.ohT), key: "oh" });
    P.payrollAwaiting && rows.push({ k: "Payroll approved or paid", v: money(P.payroll || 0), sub: `${money(P.payrollAwaiting)} submitted, awaiting approval`, tone: "bad" });
    rows.push({ k: `Net profit${P.income ? ", " + rwPct(P.netPct) : ""}`, v: money(P.net), strong: 2, tone: P.net < 0 ? "bad" : "", key: "net" });
    "week" === rwPer() && rows.push({ k: "Safe to Spend", v: rwD(stsSafe()), sub: "The same figure as Cash", strong: 1, key: "safe" });
    return { head: `Profit and Loss · ${rwPerLabel(rwPer()) || `${fmt(R[0])} to ${fmt(R[1])}`}`, rows: rows };
  }
  if ("bva" === kind) {
    let T = null;
    try {
      T = budTotals(budRows({ range: R, ent: "function" == typeof repEntity ? "" : repEntity || "" }));
    } catch (e) {}
    if (!T) return { head: "Budget vs Actual", rows: [{ k: "No budget for the period", v: "" }] };
    const line = (k, key, inc) => {
      const a = T.actual[key],
        b = T.budget[key],
        d = r2(a - b);
      rows.push({ k: k, v: money(a), sub: `budget ${money(b)} · ${d >= 0 ? "+" : "−"}${money(Math.abs(d))}${b ? `, ${d >= 0 ? "+" : "−"}${Math.abs(Math.round((100 * d) / Math.abs(b)))}%` : ""}`, tone: (inc ? d < -0.5 : d > 0.5) ? "bad" : "", key: key, strong: "net" === key ? 2 : 0 });
    };
    line("Revenue", "rev", 1), line("Job cost", "cogs"), line("Operating expenses", "opex"), line("Net profit", "net", 1);
    return { head: `Budget vs Actual · ${rwPerLabel(rwPer()) || `${fmt(R[0])} to ${fmt(R[1])}`}`, rows: rows };
  }
  if ("bs" === kind) {
    const S = glBS(rwEnt(), R[1] > today() ? today() : R[1]),
      top = (L) => L.slice().sort((a, b) => Math.abs(b.bal) - Math.abs(a.bal));
    top(S.assets).forEach((r) => rows.push({ k: `${r.a.name}, ${r.a.number || r.a.id}`, v: rwC(r.bal), key: "a:" + (r.a.number || r.a.id) }));
    rows.push({ k: "Total assets", v: rwC(S.A), strong: 1, key: "A" });
    top(S.liab).forEach((r) => rows.push({ k: `${r.a.name}, ${r.a.number || r.a.id}`, v: rwC(r.bal), key: "l:" + (r.a.number || r.a.id) }));
    rows.push({ k: "Total liabilities", v: rwC(S.L), strong: 1, key: "L" });
    S.eqRows.forEach((r) => rows.push({ k: `${r.a.name}${r.a.number ? ", " + r.a.number : ""}`, v: rwC(r.bal), key: "e:" + (r.a.number || r.a.id) }));
    rows.push({ k: "Total equity", v: rwC(S.E), strong: 1, key: "E" });
    rows.push({ k: Math.abs(r2(S.A - S.L - S.E)) < 0.005 ? "Assets equal liabilities and equity" : `Out of balance by ${rwC(S.A - S.L - S.E)}`, v: "", tone: Math.abs(r2(S.A - S.L - S.E)) < 0.005 ? "" : "bad", key: "bal" });
    let W = null;
    try {
      W = "function" == typeof wipAtClose ? wipAtClose() : null;
    } catch (e) {}
    return { head: `Balance Sheet · the ledger at ${fmtL(R[1] > today() ? today() : R[1])}`, rows: rows, note: `The ledger's own balances. The WIP schedule's over-billing posts to 2500 and 1200 at the close${W ? `: the ${W.label} close posts ${money(W.toPost)}, the same figure as Job Profitability and Books` : ""}; until then the management P&L carries it (the bridge is on Books).` };
  }
  if ("cf" === kind) {
    // cash, account by account: the bank's own register from the start of the period to its end
    (DB.accounts || [])
      .filter((a) => "bank" === a.type)
      .forEach((a) => {
        const T = (DB.txns || []).filter((t) => t.acct === a.id && "void" !== t.status),
          before = r2(T.filter((t) => t.date < R[0]).reduce((s, t) => s + (+t.amt || 0), 0)),
          inR = T.filter((t) => t.date >= R[0] && t.date <= R[1]),
          xfer = (t) => ["cc-payment", "transfer"].includes(t.cat),
          inn = r2(inR.filter((t) => +t.amt > 0 && !xfer(t)).reduce((s, t) => s + +t.amt, 0)),
          out = r2(inR.filter((t) => +t.amt < 0 && !xfer(t)).reduce((s, t) => s + +t.amt, 0)),
          tr = r2(inR.filter(xfer).reduce((s, t) => s + +t.amt, 0)),
          open = r2((+a.opening || 0) + before),
          end = r2(open + inn + out + tr);
        rows.push({ k: `Cash at the start, ${a.name.split(" ")[0]} ····${a.last4 || ""}`, v: rwC(open), key: "open" });
        rows.push({ k: "Money in", v: rwC(inn), sub: "Client payments and other deposits", key: "in" });
        rows.push({ k: "Money out", v: rwC(out), sub: "Vendors, payroll and overhead", key: "out" });
        rows.push({ k: "Card payments and transfers, outside the P&L", v: rwC(tr), key: "xfer" });
        rows.push({ k: `Cash at the end, ${a.name.split(" ")[0]} ····${a.last4 || ""}`, v: rwC(end), strong: 1, key: "end" });
      });
    return { head: `Cash Flow · ${rwPerLabel(rwPer()) || `${fmt(R[0])} to ${fmt(R[1])}`}`, rows: rows, note: "Read from the bank register line by line; it ends on the account's balance." };
  }
  return { head: "", rows: [] };
}
// what stands behind the numbers (Financial truth): cost by bank line, by hand and not yet coded add to the P&L's cost
// to the cent; income with a bank line; every entry not made from a document, flagged with who, when and why
function rwBehind() {
  const R = rwRange(),
    C = truthCoverage(R),
    P = companyPL(R),
    k = C.cost,
    uncoded = r2(+P.needsCat || 0),
    other = r2(k.adjust - uncoded);
  let M = { rows: [] };
  try {
    M = truthManual(R, { entityId: rwEnt() });
  } catch (e) {}
  const man = (M.rows || []).filter((m) => !/^(Close|Accrual)\b/i.test((m.flag && m.flag.text) || "") || /manual/i.test(m.j.source || "")),
    opening = man.filter((m) => /^Opening/i.test((m.flag && m.flag.text) || "") || "opening" === m.j.source),
    manual = man.filter((m) => !opening.includes(m)),
    amtOf = (m) => r2((m.j.lines || []).reduce((a, l) => a + (+l.dr || 0), 0));
  return {
    cost: { bank: k.bank, document: k.document, hand: k.hand, uncoded: uncoded, other: other, total: k.total, rows: k.rows },
    income: { bank: C.income.bank, total: P.income, collected: P.collected },
    opening: opening.map((m) => ({ j: m.j, amt: amtOf(m), flag: (m.flag && m.flag.text) || "" })),
    manual: manual.map((m) => ({ j: m.j, amt: amtOf(m), flag: (m.flag && m.flag.text) || "" })),
  };
}
// the Pack's state for the period: closed months final, the open one and an unclosed one a Draft
function rwPackState() {
  const per = rwPer(),
    closes = ((DB.periods && DB.periods.closes) || []).map((c) => c.month);
  if ("week" === per) return { title: `The Weekly Flash, week ending ${fmtL(today())}`, state: "One page for the Monday meeting: cash, collections, jobs, people and what to act on.", cta: "Open the Weekly Flash" };
  if ("last" === per) {
    const ym = rwPrevYm(),
      n = rwMonthName(ym).split(" ")[0];
    if (closes.includes(ym)) return { title: `The ${n} Pack`, state: `Final: ${n} is closed.`, cta: `Open the ${n} Pack` };
    let L = [];
    try {
      L = closeChecklist(ym);
    } catch (e) {}
    const open = L.filter((i) => !i.ok).length;
    return { title: `The ${n} Pack`, state: `Draft: ${n} is not closed.${L.length ? ` ${open} of ${L.length} close checks are open;` : ""} the Pack becomes final when the controller closes the month.`, cta: `Open the ${n} Pack, Draft`, draft: 1 };
  }
  if ("month" === per) {
    const n = rwMonthName(rwYm()).split(" ")[0];
    return { title: `The ${n} Pack`, state: `Draft: the month is open, through ${fmtL(today())}.`, cta: `Open the ${n} Pack`, draft: 1 };
  }
  return { title: `Year to date, ${fmt(rwRange()[0])} to ${fmt(rwRange()[1])}`, state: "The Pack's year-to-date columns, compared with the budget.", cta: "Open the Year to Date Pack" };
}

// ---- drawing ----------------------------------------------------------------------------------------------------------
const RW_ICO = {
  plus: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
  search: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>',
};
const rwTone = (t) => (t ? ` rw-${t}` : "");
function rwChips(group, list, on) {
  return `<div class="rw-chips" role="tablist" aria-label="${rwEsc(group)}">${list.map(([k, l]) => `<button type="button" role="tab" class="rw-chip${on === k ? " on" : ""}" aria-selected="${on === k}" aria-pressed="${on === k}" data-rwchip="${rwEsc(group)}:${rwEsc(k)}">${rwEsc(l)}</button>`).join("")}</div>`;
}
function rwRiskHtml(rows) {
  return `<section class="card rw-risk" aria-label="At Risk"><div class="rw-cap">At Risk <b class="n" data-rwrisk>${rows.length}</b></div>${
    rows.length ? rows.map((r, i) => `<a href="#" class="rw-rrow" data-rwgo="${i}"><b>${rwEsc(r.title)}</b><span>${rwEsc(r.why)}</span></a>`).join("") : '<p class="small muted rw-empty">Nothing at risk here.</p>'
  }</section>`;
}
function rwRowsHtml(rows, cls) {
  return `<div class="rw-rows ${cls || ""}">${rows
    .map((r) => {
      const open = r.open ? ` data-rwopen="${rwEsc(JSON.stringify(r.open))}" tabindex="0" role="button"` : "";
      return `<div class="rw-lrow${r.strong ? " rw-strong" + (2 === r.strong ? " rw-grand" : "") : ""}${rwTone(r.tone)}"${r.key ? ` data-k="${rwEsc(r.key)}"` : ""}${open}><span class="rw-lk"><b>${rwEsc(r.k)}</b>${r.sub ? `<span class="rw-ls">${rwEsc(r.sub)}</span>` : ""}</span>${r.v != null && "" !== r.v ? `<b class="rw-lv">${rwEsc(r.v)}</b>` : ""}</div>`;
    })
    .join("")}</div>`;
}
function rwHead(pg, extra) {
  const P = RW_PAGES[pg];
  return `<div class="rw-top"><h2 class="rw-h">${rwEsc(P.name)}</h2><span class="grow"></span>${extra || ""}</div><p class="lead rw-lead">${rwEsc(P.lead)} · as of ${rwEsc(fmtL(today()))}</p>`;
}

// Job Profitability
function rwJobsHtml() {
  // one job's own report (a job opened from the list, for a seat with no Budget of its own): inside a record,
  // everything is that record; the firm's At Risk, tiles and cards are one tap back
  const one = "profit" === repTab && "undefined" != typeof repProj && repProj && (DB.projects || []).find((p) => p.id === repProj);
  if (one)
    return `<div class="rw-stdopen"><a href="#" class="rw-link" data-rwchip="jobs:margin">Job Profitability, every job</a><b>${rwEsc(one.project.name)}</b><span class="small muted">This job's profitability: contract, cost by line, billed and collected, and the bank line behind each figure.</span></div>`;
  const L = rwJobs(),
    pm = "pm" === role(),
    risk = rwJobRisk(),
    withC = L.filter((x) => x.J.contract > 0),
    sum = (f) => r2(withC.reduce((a, x) => a + (+f(x) || 0), 0)),
    contract = sum((x) => x.J.contract),
    gp = sum((x) => x.J.estGP),
    billed = sum((x) => x.J.billed),
    coll = sum((x) => x.J.collected),
    unb = sum((x) => x.J.unbanked),
    tiles = [
      ["Contracts", money(contract), `${withC.length} job${1 === withC.length ? "" : "s"} with a contract`, "contract"],
      ["Margin at Completion", money(gp), `${contract ? rwPct((100 * gp) / contract) : "0%"} of contract`, "gp"],
      ["Billed", money(billed), "gross, before retainage", "billed"],
      ["Collected", money(coll), `with a bank line${unb ? ` · ${money(unb)} not in the bank` : ""}`, "collected"],
    ],
    wip = "wip" === rwS.jobs,
    fact = (k, l, v, sub) => `<div class="rw-fact" data-k="${k}"><span>${rwEsc(l)}${sub ? `<i>${rwEsc(sub)}</i>` : ""}</span><b>${rwEsc(v)}</b></div>`,
    card = ({ p, J, C, A }) => {
      const c = (DB.clients || []).find((x) => x.id === p.clientId),
        site = "function" == typeof tpJobPct ? tpJobPct(p) : null;
      let head, tone, sub, facts;
      if (!wip) {
        head = J.contract ? `${money(J.estGP)} · ${rwPct(J.estGPPct)}` : "Cost only";
        tone = J.contract && J.plannedGPPct && J.estGPPct < J.plannedGPPct - 0.005 ? "warn" : "";
        sub = [c ? c.name : "", J.contract && J.plannedGPPct ? `bid ${rwPct(J.plannedGPPct)}` : "", null != site && J.contract ? `${site}% done on site` : "", J.contract ? "" : "no contract"].filter(Boolean).join(" · ");
        facts = (J.contract ? fact("contract", "Contract", money(J.contract)) : "") + fact("cost", "Cost to date", money(J.actual), C && Math.abs(C.notPosted) >= 0.5 ? `${money(C.posted)} posted · ${money(C.notPosted)} hours clocked, not yet posted` : "") + (J.committed > 0.5 ? fact("committed", "Committed, open POs", money(J.committed)) : "") + (J.contract ? fact("eac", "Projected cost", money(J.eac)) : "");
      } else {
        const K = rwCtc(J),
          pctTxt = `${(100 * K.pct).toFixed(2)}%`;
        head = J.over > 0.005 ? `${money(J.over)} over` : J.under > 0.005 ? `${money(J.under)} under` : J.contract ? "Billed = earned" : "Cost only";
        tone = J.over > 0.005 ? "bad" : J.under > 0.005 ? "warn" : "";
        sub = `Earned on cost to cost, ${pctTxt}${null != site ? ` · measured on site ${site}%` : ""}${K.held ? ` · held at ${Math.round(100 * K.held.at)}% until the PM reviews the cost to complete` : ""}`;
        facts = J.contract
          ? fact("cost", "Cost to date", money(J.actual)) +
            (K.pre ? fact("pre", "Less money paid ahead, not progress", money(K.pre)) : "") +
            (K.rc ? fact("rc", "Less purchases billed back to the client", money(K.rc)) : "") +
            (K.pre || K.rc ? fact("ctc", "Cost for progress", money(K.cost)) : "") +
            fact("proj", K.rc ? "Projected cost, less billed back" : "Projected cost", money(K.proj)) +
            fact("pct", "Percent complete, cost to cost", pctTxt) +
            fact("contract", "Contract", money(J.contract)) +
            fact("earned", K.rb ? "Earned, with billed-back purchases" : "Earned, contract × percent complete", money(J.earned)) +
            fact("billed", "Billed, gross", money(J.billed)) +
            fact("over", J.under > 0.005 ? "Under-Billed (WIP)" : "Over-Billed (WIP)", money(J.under > 0.005 ? J.under : J.over)) +
            (A && A.total > 0.005 ? fact("ahead", "Billed Ahead of the Work, by line", `${money(A.total)} on ${A.n} line${1 === A.n ? "" : "s"}`) : "") +
            fact("backlog", "Backlog", money(J.backlog))
          : fact("cost", "Cost to date", money(J.actual));
      }
      return `<a href="#" class="rw-job" data-rwjob="${rwEsc(p.id)}" aria-label="Open ${{ costs: "the Budget", jbill: "the Contract and Billing", profit: "the profitability" }[rwJobTarget()]} of ${rwEsc(shortName(p))}"><div class="rw-jh"><b>${rwEsc(p.project.name)}</b><b class="rw-jv${rwTone(tone)}">${rwEsc(head)}</b></div><div class="rw-js">${rwEsc(sub)}</div>${facts}</a>`;
    },
    all = wip
      ? (() => {
          const s = (f) => r2(withC.reduce((a, x) => a + (+f(x) || 0), 0)),
            over = s((x) => x.J.over),
            under = s((x) => x.J.under);
          // what the month's close posts is the WIP schedule at its month end, job by job (wipAtClose, Books' close row)
          let W = null;
          try {
            W = "pm" !== role() && "function" == typeof wipAtClose ? wipAtClose() : null;
          } catch (e) {}
          return `<div class="rw-job rw-alljobs" data-rwjob=""><div class="rw-jh"><b>All jobs</b><b class="rw-jv${over > 0.005 ? " rw-bad" : ""}">${money(over)} over</b></div><div class="rw-js">Under-billed ${money(under)} · backlog gross profit ${money(s((x) => x.J.backlogGP))}</div>${fact("earned", "Earned", money(s((x) => x.J.earned)))}${fact("billed", "Billed, gross", money(s((x) => x.J.billed)))}${fact("backlog", "Backlog", money(s((x) => x.J.backlog)))}${
            W ? fact("posts", `Posts at the ${W.label} close, to 2500 and 1200`, money(W.toPost), `the WIP schedule at ${fmt(W.end)}, job by job: ${W.rows.filter((r) => Math.abs(r.toPost) >= 0.005).map((r) => `${shortName(r.p)} ${money(r.toPost)}`).join(", ") || "nothing to post"}`) : ""
          }</div>`;
        })()
      : "",
    lead = wip
      ? "Earned is the contract times the percent complete: cost for progress (cost to date less money paid ahead) over the projected cost. Over-Billed (WIP) is the accounting number the close posts; Billed Ahead of the Work is billing's line-by-line check. The gap goes to the controller."
      : "Margin at completion is each job's contract less its projected cost: every estimate and change-order line at the greater of budget and actual plus committed. A job opens its own page.";
  let company = "";
  if (!pm) {
    const R = [today().slice(0, 4) + "-01-01", today()],
      P = companyPL(R),
      T = jobCostTie(R),
      row = (k, v, fw) => `<div class="rw-lrow${fw ? " rw-strong" : ""}"><span class="rw-lk"><b>${rwEsc(k)}</b></span><b class="rw-lv">${rwEsc(v)}</b></div>`;
    company = `<section class="card rw-company" aria-label="The Company, After Overhead"><div class="rw-cap">The Company, After Overhead <span class="small">Year to date</span></div>${row("Revenue, earned", money(P.income))}${row("Job cost", money(P.cogsT))}${row(`Gross profit, ${rwPct(P.grossPct)}`, money(P.gross), 1)}${row(`Overhead${P.needsCat ? `, incl. ${money(P.needsCat)} not yet coded` : ""}`, money(P.ohT))}${row(`Net profit, ${rwPct(P.netPct)}`, money(P.net), 1)}<p class="small rw-tie" data-rwtie>Job cost on the P&L is ${rwEsc(rwC(T.plCost))}; the jobs' own cost to date is ${rwEsc(rwC(T.jobs))}. The ${rwEsc(rwC(Math.abs(T.diff)))} between them: ${rwEsc(T.why)}.</p>${
      rwMay("reports") ? `<a href="#" class="rw-link" data-rwchip="page:stmt">Open the P&L</a>` : ""
    }</section>`;
  }
  return `${rwRiskHtml(risk)}<div class="rw-tiles">${tiles.map(([k, v, s, key]) => `<div class="rw-tile" data-k="${key}"><span>${rwEsc(k)}</span><b>${rwEsc(v)}</b><i>${rwEsc(s)}</i></div>`).join("")}</div>${rwChips("jobs", [
    ["margin", "Margin"],
    ["wip", "Work in Progress"],
  ], rwS.jobs)}<p class="small muted rw-chiplead">${rwEsc(lead)}</p><div class="rw-jobs">${L.map(card).join("")}${all}</div>${company}`;
}

// Cash
function rwCashHtml() {
  const S = rwSafeParts(),
    risk = rwCashRisk(),
    W = (S.X.F && S.X.F.weeks) || [],
    lowI = W.reduce((m, w, i) => (m < 0 || w.balance - (w.setAside || 0) < W[m].balance - (W[m].setAside || 0) ? i : m), -1),
    sel = rwS.wk >= 0 && rwS.wk < W.length ? rwS.wk : lowI,
    max = Math.max(1, ...W.map((w) => Math.max(0, w.balance))),
    scale = Math.ceil(max / 5e4) * 5e4;
  let view = "";
  if ("weeks" === rwS.cash) {
    const w = W[sel],
      items = (x) => (x.items || []).map(([d, a]) => `${d} ${a > 0 ? "+" : "−"}${money(Math.abs(a))}`).join(" · ") || "Nothing scheduled";
    view = rwPhone()
      ? `<div class="rw-weeks rw-weeklist" role="list" aria-label="The next 13 weeks">${W.map(
          (x, i) =>
            `<button type="button" class="rw-wk${i === sel ? " on" : ""}${i === lowI ? " low" : ""}" role="listitem" data-rwwk="${i}" aria-pressed="${i === sel}"><span class="rw-wd">${rwEsc(fmt(x.start))}</span><span class="rw-wbar" aria-hidden="true"><i style="width:${Math.max(2, Math.round((100 * Math.max(0, x.balance)) / scale))}%"></i></span><b>${rwEsc(money(x.balance))}</b></button>${
              i === sel ? `<div class="rw-wkd" data-rwwkd><span>In ${rwEsc(x.inflow ? money(x.inflow) : "nothing")} · out ${rwEsc(x.outflow ? money(x.outflow) : "nothing")} · set aside ${rwEsc(money(x.setAside || 0))} · ours ${rwEsc(money(x.ours != null ? x.ours : x.balance - (x.setAside || 0)))}</span><span>${rwEsc(items(x))}</span></div>` : ""
            }`,
        ).join("")}</div><p class="small muted">Each bar is the week's closing balance, on a scale of $0 to ${rwEsc(money(scale))}. ${lowI >= 0 ? `The low after the set-aside is the week of ${rwEsc(fmt(W[lowI].start))}.` : ""}</p>`
      : `<div class="rw-weeks rw-bars" role="list" aria-label="The next 13 weeks">${W.map((x, i) => `<button type="button" class="rw-bar${i === sel ? " on" : ""}${i === lowI ? " low" : ""}" role="listitem" data-rwwk="${i}" aria-pressed="${i === sel}" aria-label="Week of ${rwEsc(fmt(x.start))}, ${rwEsc(money(x.balance))}"><i style="height:${Math.max(2, Math.round((100 * Math.max(0, x.balance)) / scale))}%"></i><span>${rwEsc(fmt(x.start))}</span></button>`).join("")}</div><p class="small muted">Closing balance each week, on a scale of $0 to ${rwEsc(money(scale))}.</p>${
          w ? `<div class="card rw-wkd" data-rwwkd><b>Week of ${rwEsc(fmt(w.start))}${sel === lowI ? ", the 13-week low after the set-aside" : ""}</b><div class="rw-wkn"><span>In <b>${rwEsc(w.inflow ? money(w.inflow) : "nothing")}</b></span><span>Out <b>${rwEsc(w.outflow ? money(w.outflow) : "nothing")}</b></span><span>Balance <b>${rwEsc(money(w.balance))}</b></span><span>Set aside <b>${rwEsc(money(w.setAside || 0))}</b></span><span>Ours <b>${rwEsc(money(w.ours != null ? w.ours : w.balance - (w.setAside || 0)))}</b></span></div><span class="small">${rwEsc(items(w))}</span></div>` : ""
        }`;
  } else {
    const V = rwCashLists(rwS.cash);
    view = `<p class="small muted rw-chiplead">${rwEsc(V.lead)}</p><section class="card rw-list">${rwRowsHtml(V.rows)}</section>`;
  }
  return `<div class="rw-two"><section class="card rw-safe" aria-label="Safe to Spend"><div class="rw-safe-h"><span>Safe to Spend</span><b class="rw-fig${S.safe < 0 ? " rw-bad" : ""}" data-rwfig="safe">${rwEsc(rwD(S.safe))}</b></div><p class="small muted">The lower of ours today and the 13-week low after the same set-aside.</p>${rwRowsHtml(
    S.rows.map((r) => ({ k: r.k, sub: r.sub, v: rwC(r.v), strong: r.total ? 1 : 0, key: r.total ? (/^Ours/.test(r.k) ? "ours" : "low") : /^In the bank/.test(r.k) ? "bank" : /^Credit/.test(r.k) ? "cards" : /^Payroll/.test(r.k) ? "payroll" : /^Set aside/.test(r.k) ? "setaside" : /bills/i.test(r.k) ? "bills" : "" })),
    "rw-parts",
  )}${S.notCounted ? `<p class="small rw-nc">${rwEsc(S.notCounted)}</p>` : ""}</section>${rwRiskHtml(risk)}</div>${rwChips("cash", [
    ["weeks", "Next 13 Weeks"],
    ["funds", "Client Funds"],
    ["ar", "Receivables"],
    ["ap", "Payables"],
  ], rwS.cash)}${view}`;
}

// Financial Statements
function rwStmtHtml() {
  const per = rwPer(),
    pk = rwPackState(),
    B = rwBehind(),
    K = rwStmtRows(rwS.kind),
    pc = (k) => rwC(k),
    b = (k, l, v, tone, sub) => `<div class="rw-lrow${rwTone(tone)}" data-k="${k}"><span class="rw-lk"><b>${rwEsc(l)}</b>${sub ? `<span class="rw-ls">${sub}</span>` : ""}</span><b class="rw-lv">${rwEsc(v)}</b></div>`,
    mj = (m, why) => `<div class="rw-mj" data-rwmj="${rwEsc(m.j.id)}"><b>${rwEsc(m.j.number || "Journal")} · ${rwEsc(fmt(m.j.date))} · ${rwEsc(rwC(m.amt))}</b><span>${rwEsc(new RegExp("^" + why + "\\b", "i").test(m.flag || "") ? m.flag : `${why}: ${m.flag || m.j.memo || ""}`)}</span></div>`;
  const behind = `<section class="card rw-behind" aria-label="What Stands Behind These Numbers"><div class="rw-cap">What Stands Behind These Numbers <span class="small">${rwEsc(rwPerLabel(per) || "the period")}</span></div>${b("income", "Client payments backed by a bank line", pc(B.income.collected), "ok")}${b("bank", "Cost backed by a bank or card line", pc(B.cost.bank), "ok")}${
    B.cost.document ? b("document", "Cost backed by an approved document only (accrual)", pc(B.cost.document)) : ""
  }${b("hand", "Cost typed in, not yet on the card or bank statement (flagged)", pc(B.cost.hand), B.cost.hand ? "warn" : "ok")}${"function" == typeof truthHandList ? truthHandList(B.cost) : ""}${b("uncoded", "Cost not yet coded to an account (Needs Category)", pc(B.cost.uncoded), B.cost.uncoded ? "warn" : "ok")}${
    Math.abs(B.cost.other) >= 0.005 ? b("other", "Adjustments the P&L makes outside these rows", pc(B.cost.other), "warn") : ""
  }${b("total", "The P&L's cost: job cost and overhead", pc(B.cost.total), "", "")}${b("opening", `Entries not from a document: ${B.opening.length} opening entr${1 === B.opening.length ? "y" : "ies"}`, pc(B.opening.reduce((a, m) => a + m.amt, 0)), B.opening.length ? "warn" : "ok")}${B.opening.map((m) => mj(m, "Opening")).join("")}${b("manual", "Manual journal entries", String(B.manual.length), B.manual.length ? "warn" : "ok")}${B.manual
    .map((m) => mj(m, "Manual"))
    .join("")}<a href="#" class="rw-link" data-rwchip="detail:tieout">Open the Three-Way Tie-Out</a></section>`;
  return `${rwChips("per", RW_PER.map(([k]) => [k, rwPerLabel(k)]), per)}${per ? "" : `<p class="small muted rw-chiplead">${rwEsc(`${fmt(rwRange()[0])} to ${fmt(rwRange()[1])}`)}</p>`}<section class="card rw-pack${pk.draft ? " rw-draft" : ""}" aria-label="The Pack"><b>${rwEsc(pk.title)}</b><span class="small">${rwEsc(pk.state)}</span><button type="button" class="btn primary" data-rwpack>${rwEsc(pk.cta)}</button></section>${rwChips("kind", [
    ["pl", "Profit and Loss"],
    ["bs", "Balance Sheet"],
    ["cf", "Cash Flow"],
    ["bva", "Budget vs Actual"],
  ], rwS.pack || rwS.detail ? "" : rwS.kind)}<section class="card rw-stmt" aria-label="${rwEsc(K.head)}"><div class="rw-cap">${rwEsc(K.head)}</div>${rwRowsHtml(K.rows)}${K.note ? `<p class="small muted">${rwEsc(K.note)}</p>` : ""}</section>${behind}`;
}

// Report Builder
function rwBuilderRows() {
  return RW_STD.filter(([, , , o]) => (o.view ? rwMay(o.view) : rwMay("reports")));
}
function rwPinned() {
  // the person's pinned reports and widgets: the Dashboard's own list, read without creating it
  const r = role(),
    key = DB.deviceUser ? "u:" + DB.deviceUser : r,
    H = (DB.dashboards || {})[key] || (DB.published || {})[r] || (DB.dashboards || {})[r] || ("object" == typeof ROLE_HOME ? ROLE_HOME[r] || ROLE_HOME.pm : null) || { portlets: [] },
    names = {};
  try {
    Object.values("object" == typeof DASH_GROUPS ? DASH_GROUPS : {}).forEach((L) => L.forEach(([k, l]) => (names[k] = l)));
  } catch (e) {}
  "object" == typeof PORTLETS && Object.keys(PORTLETS).forEach((k) => (names[k] = names[k] || PORTLETS[k]));
  return (H.portlets || []).map((p) => ({ name: (p.cfg && p.cfg.title) || names[p.type] || rwCap(p.type), what: "search" === p.type ? "A saved report, as a list" : "A figure or a list on your Today" }));
}
function rwSources() {
  rwEqDs();
  const alias = {};
  Object.keys(EQ_TABLES || {}).forEach((k) => {
    const ds = REP_DS[k] ? k : RW_EQ_ALIAS[k] && REP_DS[RW_EQ_ALIAS[k]] ? RW_EQ_ALIAS[k] : "eq_" + k;
    (alias[ds] = alias[ds] || []).push(k);
  });
  return Object.entries(REP_DS).map(([k, d]) => ({ k: k, n: d.n, eq: alias[k] || [] }));
}
function rwBuilderHtml() {
  const dash = "dashboard" === view,
    canRep = rwMay("reports"),
    chip = dash ? "pinned" : rwS.builder,
    std = rwS.std && RW_STD.find((x) => x[3].std === rwS.std);
  let body = "";
  if (std && !dash) body = `<div class="rw-stdopen"><a href="#" class="rw-link" data-rwchip="builder:standard">Report Builder, Standard</a><b>${rwEsc(std[1])}</b><span class="small muted">${rwEsc(std[2])}</span></div>`;
  else if ("standard" === chip)
    body = `<p class="small muted rw-chiplead">Reports that used to sit under Reports and now live with the person who acts on them. Each is still here, so nothing is lost.</p><section class="card rw-list">${rwRowsHtml(
      rwBuilderRows().map(([k, n, w]) => ({ k: n, sub: w, v: "Standard", open: { kind: "std", id: k } })),
      "rw-filter",
    )}</section>`;
  else if ("pinned" === chip) {
    const P = rwPinned();
    body = `<p class="small muted rw-chiplead">${P.length ? "Your pinned reports and figures, as they sit on your Today. Customize adds one; a saved report pins from its own page." : "Pin a report to your Today as a list, a figure or a reminder. Nothing is pinned yet."}</p>${dash ? "" : `<section class="card rw-list">${rwRowsHtml(P.map((x) => ({ k: x.name, sub: x.what, open: { kind: "pinned" } })), "rw-filter")}</section>`}`;
  } else body = `<p class="small muted rw-chiplead">The firm's saved reports. Each opens, filters, sorts and goes to Excel; a report's name says what it filters.</p>`;
  // the builder's own datasets first; every other table the system keeps one tap down
  const S = canRep && !dash && !std ? rwSources() : [],
    sb = (s) => `<button type="button" class="rw-srcb" data-rwsrc="${rwEsc(s.k)}" data-rweq="${rwEsc(s.eq.join(" "))}">${rwEsc(s.n)}</button>`,
    main = S.filter((s) => !(REP_DS[s.k] || {}).eq),
    more = S.filter((s) => (REP_DS[s.k] || {}).eq),
    src = S.length
      ? `<section class="card rw-src" aria-label="Start From"><div class="rw-cap">Start From <span class="small">Every record the system keeps, ${S.length} tables</span></div><div class="rw-srcs">${main.map(sb).join("")}</div>${
          more.length ? `<details class="rw-more"><summary>Every Other Table, ${more.length}</summary><div class="rw-srcs">${more.map(sb).join("")}</div></details>` : ""
        }</section>`
      : "";
  const chips = canRep
    ? rwChips("builder", [
        ["saved", "Saved"],
        ["standard", "Standard"],
        ["pinned", "Pinned"],
      ], std ? "standard" : chip)
    : "";
  return `${canRep && !dash ? `<label class="rw-q">${RW_ICO.search}<input type="search" data-rwq placeholder="Find a report" aria-label="Find a report" value="${rwEsc(rwS.q)}"></label>` : ""}${chips}${body}${src}`;
}

// ---- every queryable table, in the Report Builder (NetSuite's differentiator) ---------------------------------------
// The tables Ask reads (EQ_TABLES) that the builder had no dataset for get one: their rows as Ask reads them, the
// fields that name things as group-bys and the numbers as sums. The same entity under two names is one source.
const RW_EQ_ALIAS = { purchaseorders: "pos", transactions: "txns", changeorders: "cos", projects: "jobs" },
  RW_EQ_NAMES = { irs_register: "1099 Register", apaging: "Payables Aging", araging: "Receivables Aging", wiptie: "WIP Tie to the Ledger", pnlbyproject: "P&L by Project", pnlbyclient: "P&L by Client", reportties: "Report Ties", cashforecast: "13-Week Cash Forecast", rfqs: "Requests for Quote", rfqquotes: "Quotes Received", rfqprospects: "Vendor Prospects", rfqlines: "Request for Quote Lines", jobrfis: "RFIs", polines: "Purchase Order Lines", costcodes: "Cost Codes", estimatelines: "Estimate Lines", colines: "Change Order Lines", invoicelines: "Invoice Lines", billlines: "Bill Lines", bankmatches: "Bank Matches", expenselines: "Expense Lines", scheduletasks: "Schedule Tasks", buyboard: "Buy Board", jobinspections: "Inspections", punchlist: "Punch List", fieldrequests: "Field Requests", meetinglog: "Meetings", meetingsteps: "Meeting Steps", laborcost: "Labor Cost", vendorledger: "Vendor Ledger", paymentholds: "Payment Holds", waiverrows: "Lien Waivers by Payment", lienwaivers: "Lien Waivers", salestax: "Sales Tax", bankfeeds: "Bank Feeds", bankstatements: "Bank Statements", bankpending: "Bank Lines Pending", orphanaccruals: "Accruals with No Record", assistantActivity: "Assistant Activity", estimateranges: "Estimate Ranges", overheadmonths: "Overhead by Month", linecost: "Income to Cost by Line", jobmoney: "Job Cash In and Out", benchflags: "Benchmark Flags", pricebook: "Price Book", routeplan: "Route Plan", feedbackSessions: "Feedback Sessions", itemproposals: "Item Proposals", orderdocs: "Order Documents", vendorontime: "Vendor On-Time", stockoverrides: "Stock Overrides", stockadjustments: "Stock Adjustments", stocksplits: "Stock Splits", stockuse: "Stock Issued to Jobs", sheetacks: "Sheet Acknowledgements", planholds: "Plan Holds", planoverrides: "Plan Overrides", setfindings: "Drawing Set Findings", setfacts: "Drawing Set Facts", pricewatch: "Price Watch", pricehistory: "Price History", priceexplanations: "Price Explanations", paidabovebest: "Paid Above Best Price", standard: "The SmartDesign Standard", financials: "Financials by Period", closes: "Month Closes", delegations: "Delegations", learned: "Learned", improvements: "Improvements" };
const rwEqName = (k) => RW_EQ_NAMES[k] || k.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
function rwEqRows(k) {
  let R = [];
  try {
    R = EQ_TABLES[k]() || [];
  } catch (e) {
    return [];
  }
  return (Array.isArray(R) ? R : []).map((r) => {
    const o = {};
    Object.keys(r || {}).forEach((f) => {
      if (/^_/.test(f)) return;
      const v = r[f];
      o[f] = null == v ? "" : Array.isArray(v) ? v.map((x) => (x && "object" == typeof x ? x.name || x.label || x.number || x.id || "" : x)).join(", ") : "object" == typeof v ? v.name || v.label || v.number || v.id || "" : v;
    });
    return o;
  });
}
function rwEqDs() {
  if ("object" != typeof EQ_TABLES || "object" != typeof REP_DS) return;
  Object.keys(EQ_TABLES).forEach((k) => {
    if (REP_DS[k] || (RW_EQ_ALIAS[k] && REP_DS[RW_EQ_ALIAS[k]]) || REP_DS["eq_" + k]) return;
    let memo = null;
    const shape = () => {
      if (memo) return memo;
      const R = rwEqRows(k),
        keys = R.length ? Object.keys(R[0]) : [],
        sums = keys.filter((f) => R.some((r) => "number" == typeof r[f]) && R.every((r) => "" === r[f] || "number" == typeof r[f]) && !/id$|Id$|^id$|year|month|pct|rate|days/i.test(f)),
        dims = keys.filter((f) => !sums.includes(f) && R.every((r) => "number" != typeof r[f] && String(r[f]).length < 60) && new Set(R.map((r) => r[f])).size <= Math.max(2, Math.min(30, R.length - 1)));
      return (memo = { sums: sums, dims: dims });
    };
    REP_DS["eq_" + k] = {
      n: rwEqName(k),
      eq: k,
      rows: () => ((memo = null), rwEqRows(k)),
      get dims() {
        return shape().dims;
      },
      get sums() {
        return shape().sums;
      },
    };
  });
}
// "Invoices due this week" filters by its name: open invoices due by the end of the week (it listed every open one)
const RW_DUE_WEEK = {
  label: "Due this week",
  rule: "an invoice with a balance, due on or before the end of this week",
  rows: () => {
    const end = iso(addDays(parse(rwWeekStart()), 6));
    let R = [];
    try {
      R = REP_DS.invoices.rows();
    } catch (e) {}
    return R.filter((r) => (+r.balance || 0) > 0.005 && r.due && r.due <= end);
  },
  key: (r) => r.number,
};
"object" == typeof PRED && (PRED.invoicesDueThisWeek = PRED.invoicesDueThisWeek || RW_DUE_WEEK);
function rwFixSaved() {
  (DB.searches || []).forEach((s) => {
    "Invoices due this week" === s.name && "invoices" === s.ds && !s.pred && (s.pred = "invoicesDueThisWeek");
  });
}

// ---- mounting -------------------------------------------------------------------------------------------------------
// The old heading and tab rows give way to the front; the old tab's content stays below it as the chip's detail (the
// readers and the drill-downs every other suite reads). Old blue buttons go plain: a report holds at most one blue,
// the Pack's.
function rwMount() {
  const on = document.querySelector(".view.on");
  document.querySelectorAll(".view .rw-front").forEach((f) => f.closest(".view") !== on && (f.closest(".view").classList.remove("rw-host"), f.remove()));
  if (!on) return;
  const pg = "reports" === view ? rwPageNow() : "dashboard" === view ? "builder" : "";
  if (!pg) return;
  const inner = { jobs: rwJobsHtml, cash: rwCashHtml, stmt: rwStmtHtml, builder: rwBuilderHtml }[pg];
  let html = "";
  try {
    const extra =
      ("reports" === view && !rwPhone() ? `<button type="button" class="btn rw-new" data-rwprint>Print</button>` : "") +
      ("builder" === pg && rwMay("reports") && "dashboard" !== view ? `<button type="button" class="btn rw-new" data-rwnew aria-label="New Report">${RW_ICO.plus}<span>New Report</span></button>` : "");
    html = `<div class="rw-front" data-rwpage="${pg}">${rwHead(pg, extra)}${inner()}</div>`;
  } catch (e) {
    return void console.warn("reports page", e);
  }
  on.classList.add("rw-host");
  on.querySelector(":scope > .rw-front")?.remove();
  on.insertAdjacentHTML("afterbegin", html);
  const F = on.querySelector(":scope > .rw-front");
  if ("reports" === view) {
    on.querySelectorAll(":scope > .ph, #rep-body > .rep-groups, #rep-body .ov-repsub").forEach((e) => (e.hidden = !0));
    // the period is the page's own chips: the old period controls (the desktop's buttons, the phone's select) give way
    "stmt" === pg && on.querySelectorAll("#rep-body .rep-frame > .seg, #rep-body .rep-frame > .ov-per").forEach((e) => (e.querySelector("[data-repp]") || e.matches(".ov-per")) && ((e.hidden = !0), (e.style.display = "none")));
    // the chips that are the page's own: the old content under them is not drawn twice
    const body = on.querySelector("#rep-body");
    if (body) {
      const own = ("cash" === pg && "funds" === rwS.cash) || ("builder" === pg && ["standard", "pinned"].includes(rwS.builder) && !rwS.std);
      body.hidden = own;
      // the saved reports' list is the page's Saved: its own heading and New button give way to the front's
      "builder" === pg && !rwS.std && !("undefined" != typeof ssOpen && ssOpen) && body.querySelectorAll("#rep-print-area > .rep-head").forEach((e) => (e.hidden = !0));
    }
    F && F.querySelector(".btn.primary") && on.querySelectorAll("#rep-body .btn.primary").forEach((b) => b.classList.remove("primary"));
  }
  if ("dashboard" === view) {
    // the Dashboard's own heading and its view tabs give way: it is the Report Builder's Pinned (My Dashboard); the
    // Owner and Projects views are Today, Cash, Job Profitability and All Projects now (SPEC §3). Customize stays.
    on.querySelectorAll("#dash-body > .ph h2, #dash-body > .ph .bh-lead, .home-bar h2, .home-bar .small.muted, #dash-body .dash-views").forEach((e) => ((e.hidden = !0), (e.style.display = "none")));
  }
  rwFilter(F);
}
// the search box filters the lists on the page by name, as it is typed
function rwFilter(F) {
  const q = String(rwS.q || "").trim().toLowerCase();
  const on = document.querySelector(".view.on");
  if (!on) return;
  on.querySelectorAll(".rw-filter .rw-lrow, #rep-print-area tr[data-ssopen]").forEach((r) => (r.hidden = !!q && !(r.innerText || r.textContent || "").toLowerCase().includes(q)));
}
// the WIP Schedule's % complete follows from its own numbers: say what money paid ahead it leaves out
{
  const base = repWIP;
  repWIP = function () {
    let h = base.apply(this, arguments);
    try {
      const notes = (DB.projects || [])
        .map((p) => {
          const J = jobFin(p),
            K = rwCtc(J);
          return J.contract && (K.pre || K.rc) ? `${p.project.name}: ${money(J.actual)} cost to date less ${K.pre ? `${money(K.pre)} paid ahead` : ""}${K.pre && K.rc ? " and " : ""}${K.rc ? `${money(K.rc)} billed back` : ""} is ${money(K.cost)} of ${money(K.proj)}, ${(100 * K.pct).toFixed(2)}%` : "";
        })
        .filter(Boolean);
      notes.length &&
        (h = h
          .replace(/% complete = cost to date ÷ estimated total cost\./, `% complete = cost to date, less money paid ahead of the work (not progress) and purchases billed back to the client, ÷ estimated total cost (${notes.join("; ")}).`)
          .replace(/Cost Basis % = cost to date ÷ estimated total cost;/, `Cost Basis % = cost to date, less money paid ahead of the work (not progress) and purchases billed back to the client, ÷ estimated total cost (${notes.join("; ")});`));
    } catch (e) {}
    return h;
  };
}
// the Pack for any month: one not yet closed is a Draft, and says how many close checks are open
{
  const base = repPack;
  repPack = function () {
    let h = base.apply(this, arguments);
    try {
      const pm = "undefined" != typeof packMonth ? packMonth : "",
        closed = ((DB.periods && DB.periods.closes) || []).some((c) => c.month === pm);
      if (pm && !closed) {
        let L = [];
        try {
          L = closeChecklist(pm);
        } catch (e) {}
        const n = rwMonthName(pm).split(" ")[0];
        h = h
          .replace(/(<select id="pack-month"[^>]*>)/, `$1<option value="${pm}" selected>${rwMonthName(pm)} (draft, not closed)</option>`)
          .replace(/<span class="small muted">Prepared from the frozen close of [^<]*<\/span>/, `<span class="small rw-draftnote">Draft: ${n} is not closed.${L.length ? ` ${L.filter((i) => !i.ok).length} of ${L.length} close checks are open;` : ""} the Pack becomes final when the controller closes the month.</span>`);
      }
    } catch (e) {}
    return h;
  };
}
// ---- wiring into the app ----------------------------------------------------------------------------------------------
{
  const base = renderReports;
  renderReports = function () {
    try {
      rwSync();
      // the Pack's month: a choice on its own month list is the page's; packMonth holds it only while the Pack draws,
      // because the as-of readers (companyBalance, Ask's cash and AR) read it (they read August after a person picked
      // August, the chief of staff, 11-04)
      "undefined" != typeof packMonth && packMonth && packMonth !== rwS.packYm && (rwS.packYm = packMonth);
      "undefined" != typeof packMonth && (packMonth = "reports" === view && "pack" === repTab ? rwS.packYm || "" : "");
    } catch (e) {
      console.warn("reports sync", e);
    }
    // a month's Pack reads that month (the old Pack's period follows REP, which meant July once the day is August's
    // last): its period is the month while it draws, and the person's period is put back after
    const packOf = "reports" === view && "pack" === repTab && rwS.packYm,
      keep = packOf ? { preset: REP.preset, from: REP.from, to: REP.to, rf: "undefined" != typeof repFrom ? repFrom : "", rt: "undefined" != typeof repTo ? repTo : "" } : null;
    packOf && ((REP.preset = "custom"), (REP.from = rwS.packYm + "-01"), (REP.to = fin2End(rwS.packYm)));
    let r;
    try {
      r = base.apply(this, arguments);
    } finally {
      "undefined" != typeof packMonth && (packMonth = "");
      keep && ((REP.preset = keep.preset), (REP.from = keep.from), (REP.to = keep.to), "undefined" != typeof repFrom && ((repFrom = keep.rf), (repTo = keep.rt)));
    }
    // a month picked on the Pack's own list is the page's month (the list's own handler sets packMonth and draws)
    document.getElementById("pack-month")?.addEventListener("change", (e) => (rwS.packYm = e.target.value || ""));
    try {
      "reports" === view && rwMount();
    } catch (e) {
      console.warn("reports front", e);
    }
    return r;
  };
}
{
  const base = render;
  render = function () {
    // Billing's Client Funds tab is Cash's Client Funds (its "Available Cash (Ours)" figure goes)
    try {
      "billing" === view && "undefined" != typeof billTab && "funds" === billTab && rwMay("reports") && ((billTab = "billable"), (view = "reports"), (repTab = "funds"));
      // the Dashboard is the Report Builder's Pinned (My Dashboard)
      "dashboard" === view && "undefined" != typeof dashView && "mine" !== dashView && (dashView = "mine");
    } catch (e) {}
    const r = base.apply(this, arguments);
    try {
      // the reports renderer mounted the front; every other page clears one left behind (the Dashboard draws its own)
      const on = document.querySelector(".view.on");
      ("reports" === view && on && on.querySelector(":scope > .rw-front")) || rwMount();
    } catch (e) {
      console.warn("reports front", e);
    }
    return r;
  };
}
// Reports opened with no page named lands on the seat's first Reports entry: the old renderer's default tab ("dash",
// read as P&L Detail) is the sign that no page was named, however Reports was reached (setView, a link, a test)
"undefined" != typeof repTab && "company" === repTab && (repTab = "dash");
// a menu entry opens its page on its first chip
function rwGo(pg) {
  rwS.page = pg;
  rwS.std = "";
  rwS.detail = "";
  rwS.pack = !1;
  "jobs" === pg && (rwS.jobs = "margin");
  "cash" === pg && (rwS.cash = "weeks");
  "builder" === pg && (rwS.builder = "saved");
  "undefined" != typeof ssOpen && (ssOpen = null);
  repTab = rwTabOf();
  rwS.tab = repTab;
  rwS.landed = !0;
}
{
  const base = mnGo;
  mnGo = function (g, it) {
    try {
      it && "reports" === it.v && rwGo(it.tab && RW_PAGES[it.tab] ? it.tab : "jobs");
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
"object" == typeof MN_ALIAS && Object.assign(MN_ALIAS, { dashboard: "reports" });

const rwJobTarget = () => (rwMay("costs") ? "costs" : rwMay("jbill") ? "jbill" : "profit");
function rwOpenGo(go) {
  if (!go) return;
  if ("bill" === go.kind) return void openBill(go.id);
  if ("payroll" === go.kind) return void openPayroll(go.id);
  // a job opens its Budget; a seat with no Budget its Contract and Billing; a seat that opens no job page (the
  // controller) that job's own profitability report, here (inside a record, everything is that record)
  if ("budget" === go.kind) {
    const v = rwJobTarget();
    if ("profit" === v) return (repProj = go.pid), (rwS.jobs = "margin"), (repTab = "profit"), (rwS.tab = repTab), void render();
    return void ("function" == typeof jpOpenJob ? jpOpenJob(go.pid, v) : (setCurrent(go.pid), setView(v)));
  }
  if ("close" === go.kind) return void ("function" == typeof acGoChip ? acGoChip("gl", "close") : setView("gl"));
  if ("wip" === go.kind) return (rwS.jobs = "wip"), (repTab = rwTabOf()), (rwS.tab = repTab), void render();
  if ("undep" === go.kind) return void (rwMay("billing") ? ((billTab = "billable"), (docOpen = null), setView("billing")) : ((clientOpen = go.id), (docOpen = null), setView("clients")));
  if ("invoice" === go.kind) return void ("function" == typeof acOpen ? acOpen(`invoice:${go.c}:${go.id}`) : setView("billing"));
  if ("pinned" === go.kind) return (dashView = "mine"), void setView("dashboard");
  if ("std" === go.kind) {
    const s = RW_STD.find((x) => x[0] === go.id);
    if (!s) return;
    const o = s[3];
    if (o.view) return void (o.chip && "function" == typeof acGoChip ? acGoChip(o.view, o.chip) : setView(o.view));
    if (o.std) return (rwS.page = "builder"), (rwS.builder = "standard"), (rwS.std = o.std), (repTab = o.std), (rwS.tab = repTab), void ("reports" === view ? render() : setView("reports"));
    rwGo(o.page);
    o.jobs && (rwS.jobs = o.jobs);
    o.cash && (rwS.cash = o.cash);
    o.detail && (rwS.detail = o.detail);
    o.per && rwSetPer(o.per, !0);
    o.pack && (rwS.pack = "week" === o.per ? "flash" : "pack");
    repTab = rwTabOf();
    rwS.tab = repTab;
    return void ("reports" === view ? render() : setView("reports"));
  }
}
function rwChipGo(group, k) {
  if ("page" === group) return rwGo(k), void ("reports" === view ? render() : setView("reports"));
  if ("jobs" === group) (rwS.jobs = k), "margin" === k && (repTab = "portfolio");
  if ("cash" === group) rwS.cash = k;
  if ("per" === group) rwSetPer(k, !0), rwS.pack && (rwS.pack = "week" === k ? "flash" : "pack");
  if ("kind" === group) (rwS.kind = k), (rwS.pack = !1), (rwS.detail = "");
  if ("detail" === group) (rwS.detail = k), (rwS.pack = !1);
  if ("builder" === group) {
    if ("pinned" === k) return (dashView = "mine"), void setView("dashboard");
    rwS.builder = k;
    rwS.std = "";
    "undefined" != typeof ssOpen && (ssOpen = null);
    if ("dashboard" === view) return rwGo("builder"), (rwS.builder = k), (repTab = rwTabOf()), (rwS.tab = repTab), void setView("reports");
  }
  repTab = rwTabOf();
  rwS.tab = repTab;
  render();
}
function rwNewReport(ds) {
  // a new report: the builder's own New, on the chosen table
  const s = { id: uid("ss"), name: ds ? `${(REP_DS[ds] || {}).n || "New"} report` : "New report", ds: ds || "invoices", group: "", criteria: [], summary: {}, highlight: null, audience: ["all"], kpi: !1, kpiField: "count", reminder: !1, reminderThreshold: 0, createdBy: (DB.me || "") };
  searchList().push(s);
  const go = () => {
    rwGo("builder");
    ssOpen = s.id;
    "reports" === view ? render() : setView("reports");
  };
  save();
  go();
  toast(`New report on ${(REP_DS[s.ds] || {}).n || s.ds}: name it and add criteria`, go);
}
document.addEventListener(
  "click",
  (e) => {
    const t = e.target && e.target.closest ? e.target : null;
    if (!t || !t.closest(".rw-front")) return;
    const at = (s) => t.closest(s);
    let b;
    if ((b = at("[data-rwchip]"))) {
      e.preventDefault();
      const [g, k] = b.dataset.rwchip.split(":");
      return void rwChipGo(g, k);
    }
    if ((b = at("[data-rwgo]"))) {
      e.preventDefault();
      const pg = rwPageNow(),
        L = "jobs" === pg ? rwJobRisk() : "cash" === pg ? rwCashRisk() : [];
      return void rwOpenGo((L[+b.dataset.rwgo] || {}).go);
    }
    if ((b = at("[data-rwjob]"))) {
      e.preventDefault();
      return void (b.dataset.rwjob && rwOpenGo({ kind: "budget", pid: b.dataset.rwjob }));
    }
    if ((b = at("[data-rwwk]"))) return e.preventDefault(), (rwS.wk = +b.dataset.rwwk), void rwMount();
    if ((b = at("[data-rwopen]"))) {
      e.preventDefault();
      let go = null;
      try {
        go = JSON.parse(b.dataset.rwopen);
      } catch (x) {}
      return void rwOpenGo(go);
    }
    if ((b = at("[data-rwpack]"))) {
      e.preventDefault();
      rwS.pack = "week" === rwPer() ? "flash" : "pack";
      rwS.detail = "";
      rwS.packYm = "last" === rwPer() ? rwPrevYm() : "";
      repTab = rwTabOf();
      rwS.tab = repTab;
      render();
      return void setTimeout(() => document.querySelector(".view.on #rep-print-area")?.scrollIntoView({ block: "start" }), 60);
    }
    if ((b = at("[data-rwsrc]"))) return e.preventDefault(), void rwNewReport(b.dataset.rwsrc);
    if ((b = at("[data-rwnew]"))) return e.preventDefault(), void rwNewReport("");
    if ((b = at("[data-rwprint]"))) return e.preventDefault(), void document.getElementById("rep-print")?.click();
  },
  !0,
);
// a typed-in card or bank line (Financial Statements, the Pack's coverage) opens the line itself
document.addEventListener(
  "click",
  (e) => {
    const a = e.target && e.target.closest && e.target.closest("[data-trtxn]");
    if (!a) return;
    e.preventDefault(), e.stopPropagation();
    "function" == typeof txnDialog ? txnDialog(a.dataset.trtxn) : setView("bank");
  },
  !0,
);
document.addEventListener("input", (e) => {
  const q = e.target && e.target.matches && e.target.matches(".rw-front [data-rwq]") ? e.target : null;
  q && ((rwS.q = q.value), rwFilter());
});
document.addEventListener("keydown", (e) => {
  if ("Enter" !== e.key && " " !== e.key) return;
  const r = e.target && e.target.closest && e.target.closest(".rw-front [data-rwopen]");
  r && (e.preventDefault(), r.click());
});
try {
  rwEqDs();
} catch (e) {}
// Cmd-K finds the four pages, every standard report and every saved report (SPEC §2, Report Builder, 3)
if ("function" == typeof palIndex) {
  const base = palIndex;
  palIndex = function () {
    const items = base.apply(this, arguments);
    try {
      if (rwMay("reports")) {
        Object.entries(RW_PAGES).forEach(([k, P]) => items.push({ k: "Report", t: P.name, s: P.lead, go: () => (rwGo(k), "reports" === view ? render() : setView("reports")) }));
        rwBuilderRows().forEach(([k, n, w]) => items.push({ k: "Report", t: n, s: w, go: () => rwOpenGo({ kind: "std", id: k }) }));
        (DB.searches || []).forEach((x) => items.push({ k: "Report", t: x.name, s: `Saved report · ${(REP_DS[x.ds] || {}).n || x.ds}`, go: () => (rwGo("builder"), (ssOpen = x.id), "reports" === view ? render() : setView("reports")) }));
      } else if (rwMay("dashboard")) items.push({ k: "Report", t: "Report Builder", s: "Your pinned reports", go: () => setView("dashboard") });
    } catch (e) {}
    return items;
  };
}
