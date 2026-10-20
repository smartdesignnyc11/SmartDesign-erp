/* src/reports.js — Reporting that is right, proven, and ties to the bank (BACKLOG §1.13, the Reporting lane).

   build.py appends this file after app.js, mind.js and assistant.js, so its wrappers are the outermost ones and every
   name those files declare is in scope.

   Design gate (BACKLOG §1.16). The noun is the report. Nothing here is a new store or a new list:
   - the readers it builds on are the app's own: companyPL / ledger (the P&L and its rows), jobFin (the job, its
     cost codes and its estimate lines, J.eacLines), lineFin (billing per line), companyBalance, clientFin, apAging,
     ohAlloc / ohMonth (overhead), cashForecast, glBalances (the books), truthBacking / truthManual (the bank behind
     a row, the hand-posted journals);
   - the screens it extends are the Reports tabs that exist: P&L Detail (P&L by project and by client), Statements
     (every tie, overhead analysis, the accounting choices), Monthly Pack (every tie, for the phone), Project
     Profitability (By Line becomes income to cost), All Projects, WIP, Receivables and Payables (their tie lines);
   - one Reports sub-tab is added, Cash & Receivables › Cash Forecast: the 13-week cash flow, backlog and retainage
     both ways. Its reader (cashForecast) existed, but only a Dashboard widget showed it, so it could not be printed,
     exported or tied to the books;
   - Ask reads each report through EQ_TABLES (rp* tables, money, gated to a role that can open Reports) and through
     one Ask route for the questions the local parser answered wrongly (audit, review/reports/audit.md).
   The accounting choices Alan settles with the accountant live on DB.company.acctChoices (a setting, with its
   history), not in a new collection. */

// ---------------------------------------------------------------------------------------------------------------
// 0. Small helpers
// ---------------------------------------------------------------------------------------------------------------
const RP_EPS = 0.005;
const rpRange = () => {
  try {
    return cfoRange();
  } catch (e) {
    return [today().slice(0, 4) + "-01-01", today()];
  }
};
const rpProj = (id) => (DB.projects || []).find((p) => p.id === id) || null;
const rpProjName = (id) => {
  const p = rpProj(id);
  return p ? p.project.name : "No project";
};
const rpClientOfProj = (id) => {
  const p = rpProj(id);
  return p ? (DB.clients || []).find((c) => c.id === p.clientId) || null : null;
};
const rpInEnt = (p) => {
  try {
    return !repEntity || !p || entityOfProject(p) === repEntity;
  } catch (e) {
    return !0;
  }
};
const rpCents = (v) => {
  const n = r2(v);
  return (n < 0 ? "−$" : "$") + Math.abs(n).toLocaleString(void 0, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};
const rpSum = (a, f) => r2(a.reduce((s, x) => s + (+(f ? f(x) : x) || 0), 0));
const rpYmEnd = (ym) => iso(new Date(+ym.slice(0, 4), +ym.slice(5, 7), 0));
// a range is month-aligned when it starts on a 1st and ends on a month end or today (the overhead pool is monthly)
const rpAligned = (R) => (!R[0] || /-01$/.test(R[0])) && (!R[1] || R[1] >= today() || R[1] === rpYmEnd(R[1].slice(0, 7)));
const RP_ICON_TIE = typeof ICON_CHECK !== "undefined" ? ICON_CHECK : "";
const RP_ICON_OFF = typeof ICON_WARN !== "undefined" ? ICON_WARN : "";
const RP_ICON_PEN = ICON_SVG('<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>', 11);
const RP_ICON_XLS = ICON_SVG('<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8l8 8M16 8l-8 8"/>', 13);
const rpCanEditChoices = () => {
  try {
    return "owner" === role() || "controller" === role();
  } catch (e) {
    return !1;
  }
};

// Vendor payments recorded from an account that no bank or card line carries yet (a check not yet cleared)
function rpOutstanding(a) {
  return (DB.payments || []).filter((p) => p.acctId === a.id && !p.void && !(p.txnId && (DB.txns || []).some((t) => t.id === p.txnId)) && !(DB.txns || []).some((t) => t.paymentId === p.id));
}
// a row of fin2RetainagePayable ({v: the vendor, projectId, amt}): who and how much
const rpRetAmt = (x) => r2(+x.amt || 0);
const rpRetWho = (x) => `${(x.v && x.v.name) || ""}${x.projectId ? " · " + rpProjName(x.projectId) : ""}`;
// The row of a P&L ledger line as money: a bank line keeps its sign (a vendor credit reduces cost), a bill, a
// payroll split or a stock issue is its amount.
const rpRowAmt = (r) => (r && "txn" === r.kind && r.ref && "number" == typeof r.ref.amt ? r2(-r.ref.amt) : r2(+r.amt || 0));
const rpRowType = (r) => ("payroll_oh" === r.cat ? "oh" : catType(r.cat));
const rpSkipRow = (r) => !r || r.income || ("txn" === r.kind && r.ref && ["cc-payment", "transfer"].includes(r.cat));

// ---------------------------------------------------------------------------------------------------------------
// 1. P&L by project and by client (the company P&L split, on the active basis, entity and period)
// ---------------------------------------------------------------------------------------------------------------
// Each project row carries its income (accrual: invoiced in the period + the change in its over/under-billing;
// cash: payments received on its invoices), its job cost (the P&L's own cost rows on that project) and its share of
// the overhead pool (the app's allocation, month by month). Below the projects: cost on no project, overhead in
// months with no job cost, spend not yet coded, property income. The rows add up to the company net to the cent, or
// the tie says by how much they do not.
function rpPL(range) {
  const R = range || rpRange(),
    P = companyPL(R),
    cash = "cash" === basis(),
    L = P.L || [],
    rows = {},
    row = (id) =>
      rows[id] ||
      (rows[id] = { id: id, p: rpProj(id), income: 0, invoiced: 0, wip: 0, cost: 0, oh: 0, inc: [], costRows: [] });
  // income
  if (cash)
    (DB.clients || []).forEach((c) =>
      (c.payments || []).forEach((pay) => {
        if (pay.unapplied || !within(pay.date, R)) return;
        const inv = (c.invoices || []).find((i) => i.id === pay.invoiceId),
          pid = (inv && inv.projectId) || "";
        if (repEntity && !(pid && rpInEnt(rpProj(pid)))) return;
        const r = row(pid);
        (r.income = r2(r.income + (+pay.amount || 0))),
          r.inc.push({ kind: "payment", date: pay.date, desc: `Payment${inv ? " on " + inv.number : ""} · ${c.name}`, amt: +pay.amount || 0, c: c, d: inv, pay: pay });
      }),
    );
  else {
    (DB.clients || []).forEach((c) =>
      (c.invoices || []).forEach((i) => {
        if (["void", "draft"].includes(i.status) || i.retainageRelease || !within(i.date, R)) return;
        const pid = i.projectId || "";
        if (repEntity && !(pid && rpInEnt(rpProj(pid)))) return;
        const r = row(pid),
          v = docNet(i);
        (r.invoiced = r2(r.invoiced + v)), r.inc.push({ kind: "invoice", date: i.date, desc: `${i.number} · ${c.name}`, amt: v, c: c, d: i });
      }),
    );
    (DB.projects || [])
      .filter(rpInEnt)
      .forEach((p) => {
        const w = wipAdjustment(R, [p.id]);
        w && (row(p.id).wip = r2(w));
      });
    Object.values(rows).forEach((r) => (r.income = r2(r.invoiced + r.wip)));
  }
  // job cost, from the P&L's own rows
  L.forEach((r) => {
    if (rpSkipRow(r) || "cogs" !== rpRowType(r)) return;
    const x = row(r.projectId || ""),
      a = rpRowAmt(r);
    (x.cost = r2(x.cost + a)), x.costRows.push(r);
  });
  // overhead: the app's month-by-month allocation (ohAlloc) when the period is whole months, else the period's
  // pool shared on each job's cost in the period
  const uncoded = r2((P.oh || {})["Needs Category"] || 0),
    pool = r2((+P.ohT || 0) - uncoded);
  let unalloc = 0,
    ohNote = "";
  if (rpAligned(R) && "function" == typeof ohAlloc) {
    const A = ohAlloc(R);
    Object.entries(A.jobs || {}).forEach(([pid, v]) => {
      v && rpInEnt(rpProj(pid)) && (row(pid).oh = r2(v));
    });
    unalloc = r2(A.unabsorbed || 0);
    ohNote = `Overhead is shared month by month on ${(OH_BASES[ohBasis()] || ["total direct cost"])[0]}; a month with no job cost keeps its overhead off the jobs.`;
    // what ohAlloc's pool and this P&L's pool disagree on (an entity filter, a part month) stays visible
    const rest = r2(pool - rpSum(Object.values(rows), (r) => r.oh) - unalloc);
    Math.abs(rest) > RP_EPS && ((unalloc = r2(unalloc + rest)), (ohNote += ` ${rpCents(rest)} of the period's pool falls outside its whole months and is shown with the unallocated overhead.`));
  } else {
    const base = {};
    (DB.projects || []).filter(rpInEnt).forEach((p) => {
      const v = r2(rpSum(row(p.id).costRows.filter(() => !0), rpRowAmt));
      v > RP_EPS && (base[p.id] = v);
    });
    const T = rpSum(Object.values(base)),
      ids = Object.keys(base);
    let left = pool;
    T
      ? ids.forEach((id, i) => {
          const v = i === ids.length - 1 ? r2(left) : r2((pool * base[id]) / T);
          (row(id).oh = v), (left = r2(left - v));
        })
      : (unalloc = pool);
    ohNote = "The period is not whole months, so its overhead is shared on each job's cost in the period.";
  }
  const list = Object.values(rows)
    .filter((r) => r.id && (Math.abs(r.income) > RP_EPS || Math.abs(r.cost) > RP_EPS || Math.abs(r.oh) > RP_EPS))
    .map((r) => Object.assign(r, { gross: r2(r.income - r.cost), net: r2(r.income - r.cost - r.oh) }))
    .sort((a, b) => rpProjName(a.id).localeCompare(rpProjName(b.id)));
  const none = rows[""] || { id: "", income: 0, cost: 0, oh: 0, inc: [], costRows: [] },
    noi = r2(P.propertyNOI || 0),
    // an entity's own column: what it billed the group for its crews (eliminated in the consolidated view)
    icRev = repEntity ? r2(P.icRevenue || 0) : 0,
    // whatever the company P&L carries beyond its income, job cost, overhead and property lines
    other = r2((+P.net || 0) - ((+P.income || 0) - (+P.cogsT || 0) - (+P.ohT || 0)) - noi),
    projNet = rpSum(list, (r) => r.net),
    parts = [
      { id: "projects", label: `Projects' net (${list.length})`, amt: projNet },
      { id: "noproj-income", label: "Income on no project", amt: r2(none.income) },
      { id: "ic", label: "Billed to the group for its crews (intercompany, eliminated in consolidation)", amt: icRev },
      { id: "noproj-cost", label: "Job cost on no project", amt: -r2(none.cost) },
      { id: "oh-unalloc", label: "Overhead not on a job (months with no job cost)", amt: -r2(unalloc) },
      { id: "oh-uncoded", label: "Spend not yet coded (Needs Category)", amt: -uncoded },
      { id: "noi", label: "Property net operating income", amt: noi },
      { id: "other", label: "Other P&L lines", amt: other },
    ].filter((x) => Math.abs(x.amt) > RP_EPS || "projects" === x.id),
    sum = rpSum(parts, (x) => x.amt),
    // the P&L's own totals against the split, line by line
    incomeSplit = r2(rpSum(list, (r) => r.income) + none.income + icRev),
    costSplit = r2(rpSum(list, (r) => r.cost) + none.cost),
    ohSplit = r2(rpSum(list, (r) => r.oh) + unalloc + uncoded);
  return {
    range: R,
    basis: cash ? "cash" : "accrual",
    P: P,
    rows: list,
    none: none,
    unalloc: unalloc,
    uncoded: uncoded,
    pool: pool,
    noi: noi,
    other: other,
    parts: parts,
    sum: sum,
    net: r2(P.net),
    diff: r2(sum - P.net),
    ok: Math.abs(sum - P.net) <= RP_EPS,
    split: { income: [incomeSplit, r2(P.income)], cost: [costSplit, r2(P.cogsT)], oh: [ohSplit, r2(P.ohT)] },
    ohNote: ohNote,
  };
}
// The same split grouped by client: a client's projects, added.
function rpPLByClient(range) {
  const S = rpPL(range),
    by = {};
  S.rows.forEach((r) => {
    const c = rpClientOfProj(r.id),
      k = c ? c.id : "";
    const o = (by[k] = by[k] || { id: k, c: c, name: c ? c.name : "No client", projects: [], income: 0, cost: 0, oh: 0, gross: 0, net: 0 });
    o.projects.push(r.id), ["income", "cost", "oh", "gross", "net"].forEach((f) => (o[f] = r2(o[f] + r[f])));
  });
  const rows = Object.values(by).sort((a, b) => b.net - a.net);
  return Object.assign({}, S, { clients: rows, clientNet: rpSum(rows, (r) => r.net) });
}

// ---------------------------------------------------------------------------------------------------------------
// 2. Job cost: the job's actual is its bills + bank lines + labor + stock; its cost codes and its estimate lines add
//    up to it; and the job report's cost differs from the P&L's cost on that project only by named causes
// ---------------------------------------------------------------------------------------------------------------
function rpJobCost(p, range) {
  const J = range ? jobFin(p, range) : jobFin(p),
    parts = [
      { id: "bills", label: "Bills", amt: r2(+J.billsAmt || 0) },
      { id: "bank", label: "Bank and card lines", amt: r2(+J.txnAmt || 0) },
      { id: "labor", label: "Labor (clocked hours at burdened rates)", amt: r2(+J.laborCost || 0) },
      { id: "stock", label: "Stock used from the shop", amt: r2(+J.stockAmt || 0) },
    ],
    rebill = r2(+J.rebillCost || 0),
    sumParts = rpSum(parts, (x) => x.amt),
    codes = (J.byCode || []).map((b) => ({ code: b.code, name: b.name || "", amt: r2((+b.bills || 0) + (+b.bank || 0) + (+b.labor || 0)) })),
    codeSum = rpSum(codes, (x) => x.amt),
    lines = (J.eacLines || []).map((x) => ({ key: x.key, name: x.name || (x.line && (x.line.item || x.line.desc)) || x.key, code: x.code, actual: r2(+x.actual || 0) })),
    lineSum = rpSum(lines, (x) => x.actual),
    lineCodes = new Set(lines.map((x) => x.code)),
    noLine = r2(rpSum(codes.filter((x) => !lineCodes.has(x.code)), (x) => x.amt));
  return {
    J: J,
    actual: r2(+J.actual || 0),
    parts: parts,
    rebill: rebill,
    partsDiff: r2(J.actual - sumParts),
    codes: codes,
    codeSum: codeSum,
    // rounded code rows may differ from the job by a cent each; more than that is a fault
    codeDiff: r2(J.actual - codeSum),
    lines: lines,
    lineSum: lineSum,
    noLine: noLine,
    lineDiff: lines.length && Math.abs(r2(J.actual - lineSum - noLine)) > 0.01 * lines.length ? r2(J.actual - lineSum - noLine) : 0,
    // each line rounds to the cent on its own: a cent a line at most, shown as its own row so the lines add up
    lineRounding: lines.length && Math.abs(r2(J.actual - lineSum - noLine)) <= 0.01 * lines.length ? r2(J.actual - lineSum - noLine) : 0,
  };
}
// The job report against the P&L by project, per project: the same cost, read two ways, and why they differ.
function rpJobBridge(range) {
  const R = range || rpRange(),
    S = rpPL(R),
    L = (S.P.L || []).filter((r) => !rpSkipRow(r) && "cogs" === rpRowType(r));
  return (DB.projects || [])
    .filter(rpInEnt)
    .map((p) => {
      const J = jobFin(p, R),
        mine = L.filter((r) => r.projectId === p.id),
        of = (k) => rpSum(mine.filter((r) => r.kind === k), rpRowAmt),
        pl = rpSum(mine, rpRowAmt),
        diffs = [
          { id: "labor", label: "Labor", why: "the job report carries clocked hours at burdened rates; the P&L carries payroll runs once approved or paid", amt: r2((+J.laborCost || 0) - of("payroll") - of("accrual")) },
          { id: "bills", label: "Bills", why: "the job report carries a bill when it is entered; the P&L once it is approved or paid", amt: r2((+J.billsAmt || 0) - of("bill")) },
          { id: "bank", label: "Bank and card lines", why: "lines the job report reads on this job that the P&L files elsewhere", amt: r2((+J.txnAmt || 0) - of("txn")) },
          { id: "stock", label: "Stock", why: "stock issued to the job", amt: r2((+J.stockAmt || 0) - of("stock")) },
        ],
        job = r2(+J.actual || 0),
        rest = r2(job - pl - rpSum(diffs, (d) => d.amt));
      return { p: p, job: job, pl: pl, diff: r2(job - pl), diffs: diffs.filter((d) => Math.abs(d.amt) > RP_EPS), rest: rest };
    })
    .filter((x) => Math.abs(x.job) > RP_EPS || Math.abs(x.pl) > RP_EPS);
}

// ---------------------------------------------------------------------------------------------------------------
// 3. The ties: each report's figure, how it is made up, and whether the parts add up to it
// ---------------------------------------------------------------------------------------------------------------
// A tie is { id, report, title, figure: {label, amt}, parts: [{label, amt, drill}], mode, ok, diff, note }.
// mode "sum": the parts add up to the figure. mode "same": every part is the same figure read another way.
// Invoices the client record treats as paid that the ledger still carries a balance on (short by under $0.50)
function rpShortPaid() {
  const out = [];
  (DB.clients || []).forEach((c) =>
    (c.invoices || []).forEach((d) => {
      if (["void", "draft"].includes(d.status) || d.retainageRelease) return;
      if (repEntity && d.projectId && !rpInEnt(rpProj(d.projectId))) return;
      const total = r2(docTotal(d).total),
        paid = rpSum((c.payments || []).filter((p) => p.invoiceId === d.id && !p.unapplied), (p) => +p.amount || 0),
        bal = r2(total - paid);
      bal > RP_EPS && bal <= 0.5 && out.push({ c: c, d: d, total: total, paid: paid, bal: bal });
    }),
  );
  return out;
}
function rpTie(id, report, title, figure, parts, mode, note, go) {
  const m = mode || "sum",
    diff =
      "same" === m
        ? r2(Math.max(...parts.map((x) => Math.abs(r2(x.amt - figure.amt))), 0))
        : r2(figure.amt - rpSum(parts, (x) => x.amt));
  return { id: id, report: report, title: title, figure: figure, parts: parts, mode: m, diff: diff, ok: Math.abs(diff) <= RP_EPS, note: note || "", go: go || null };
}
function rpGL() {
  try {
    return glBalances({ entityId: repEntity || "all", to: today() }) || {};
  } catch (e) {
    return {};
  }
}
const rpGLBal = (G, k) => r2(((G || {})[k] || {}).bal || 0);
function rpTies(range, only) {
  const R = range || rpRange(),
    want = (k) => !only || only.includes(k),
    out = [],
    push = (t) => t && out.push(t),
    safe = (k, f) => {
      if (!want(k)) return;
      try {
        f();
      } catch (e) {
        console.warn("rpTies", k, e);
        out.push({ id: k, report: k, title: k, figure: { label: "could not be read", amt: 0 }, parts: [], mode: "sum", diff: 0, ok: !1, note: String(e && e.message) });
      }
    },
    G = rpGL(),
    cash = "cash" === basis();
  safe("pl", () => {
    const S = rpPL(R),
      P = S.P;
    push(
      rpTie(
        "pl",
        "P&L Detail",
        "P&L by project adds up to the company P&L",
        { label: `Company net profit (${cash ? "cash" : "accrual"})`, amt: S.net },
        S.parts.map((x) => ({ label: x.label, amt: x.amt, drill: "pl:" + x.id })),
        "sum",
        "Each project's income less its job cost and its share of overhead, then what sits on no project.",
        { view: "reports", tab: "company" },
      ),
    );
    push(
      rpTie(
        "income",
        "P&L Detail",
        cash ? "Income is the payments received" : "Revenue is what was invoiced plus the change in over/under-billing",
        { label: cash ? "Income (cash)" : "Revenue (earned)", amt: r2(P.income) },
        cash
          ? (() => {
              const bank = rpSum((DB.txns || []).filter((t) => within(t.date, R) && t.amt > 0 && "income" === t.cat && (!repEntity || "function" != typeof entityOfTxn || entityOfTxn(t) === repEntity)), (t) => t.amt);
              return [
                { label: "Received at the bank", amt: bank, drill: "inc:bank" },
                { label: "Recorded, not yet at the bank (undeposited)", amt: r2(P.income - bank), drill: "inc:undeposited" },
              ];
            })()
          : [
              { label: "Invoiced in the period", amt: r2(P.invoiced), drill: "inc:invoiced" },
              { label: "Change in over/under-billing (WIP)", amt: r2(P.wipAdj), drill: "inc:wip" },
            ].concat(repEntity && P.icRevenue ? [{ label: "Billed to the group for its crews (intercompany)", amt: r2(P.icRevenue) }] : []),
        "sum",
        cash ? "Cash basis: a payment counts the day it is recorded; the bank shows it once deposited." : "",
        { view: "reports", tab: "company" },
      ),
    );
    push(
      rpTie(
        "split",
        "P&L Detail",
        "Income, job cost and overhead split across projects add back to the P&L",
        { label: "Income + job cost + overhead on the P&L", amt: r2(S.split.income[1] + S.split.cost[1] + S.split.oh[1]) },
        [
          { label: "Income on the projects and on no project", amt: S.split.income[0], drill: "pl:income" },
          { label: "Job cost on the projects and on no project", amt: S.split.cost[0], drill: "pl:cost" },
          { label: "Overhead on the jobs, not on a job, not yet coded", amt: S.split.oh[0], drill: "pl:oh" },
        ],
      ),
    );
  });
  safe("months", () => {
    // the months add up to the period: each month's P&L, read on its own (a closed month from its seal), added
    if (!R[0] || !rpAligned(R)) return;
    const ms = "function" == typeof ohMonthsIn ? ohMonthsIn(R) : [];
    if (ms.length < 2 || ms.length > 24) return;
    const P = companyPL(R),
      M = ms.map((ym) => {
        const end = rpYmEnd(ym);
        return { ym: ym, P: companyPL([ym + "-01", end > R[1] ? R[1] : end]) };
      });
    push(
      rpTie(
        "months",
        "P&L Detail",
        "The months add up to the period",
        { label: `Net profit, ${R[0]} to ${R[1]}`, amt: r2(P.net) },
        M.filter((m) => Math.abs(m.P.net) > RP_EPS).map((m) => ({ label: `${monthLabel(m.ym)}${m.P.closedRead ? " (sealed)" : ""}`, amt: r2(m.P.net) })),
        "sum",
        `Income ${rpCents(P.income)} = the months' ${rpCents(rpSum(M, (m) => m.P.income))}; job cost ${rpCents(P.cogsT)} = ${rpCents(rpSum(M, (m) => m.P.cogsT))}; overhead ${rpCents(P.ohT)} = ${rpCents(rpSum(M, (m) => m.P.ohT))}.`,
        { view: "reports", tab: "company" },
      ),
    );
  });
  safe("wip", () => {
    if (cash) return;
    const B = companyBalance(),
      J = (DB.projects || []).filter(rpInEnt).map((p) => ({ p: p, J: jobFin(p) })).filter((x) => x.J.contract),
      net = rpSum(J, (x) => (+x.J.billed || 0) - (+x.J.earned || 0)),
      over = rpSum(J, (x) => Math.max(0, +x.J.overUnder || 0)),
      under = rpSum(J, (x) => Math.max(0, -(+x.J.overUnder || 0)));
    push(
      rpTie(
        "wip",
        "WIP Schedule",
        "Net over-billing is billed less earned, job by job",
        { label: "Net over-billing (WIP)", amt: r2(repEntity ? net : B.wip) },
        J.map((x) => ({ label: `${x.p.project.name}: billed ${rpCents(x.J.billed)} − earned ${rpCents(x.J.earned)}`, amt: r2((+x.J.billed || 0) - (+x.J.earned || 0)), drill: "wip:" + x.p.id })),
        "sum",
        `Over-billed ${rpCents(over)} less under-billed ${rpCents(under)}. Billed is gross, before retainage.`,
        { view: "reports", tab: "wip" },
      ),
    );
  });
  safe("ar", () => {
    const B = companyBalance(),
      F = (DB.clients || []).map((c) => ({ c: c, f: clientFin(c) })),
      open = rpSum(F, (x) => rpSum(x.f.open, (o) => o.bal)),
      bk = F.reduce((a, x) => (["current", "d30", "d60", "d90"].forEach((k) => (a[k] = r2(a[k] + (+x.f.buckets[k] || 0)))), a), { current: 0, d30: 0, d60: 0, d90: 0 });
    push(
      rpTie(
        "ar",
        "Receivables",
        "Receivables: the aging adds up to the open invoices and to the books",
        { label: "Receivables", amt: r2(B.arOut) },
        [
          { label: "Current", amt: bk.current, drill: "ar:open" },
          { label: "1–30 days past due", amt: bk.d30, drill: "ar:open" },
          { label: "31–60 days", amt: bk.d60, drill: "ar:open" },
          { label: "Over 60 days", amt: bk.d90, drill: "ar:open" },
        ],
        "sum",
        `Open invoices on the client records ${rpCents(open)}; the ledger's Accounts receivable (1100) ${rpCents(rpGLBal(G, "1100"))}.`,
        { view: "reports", tab: "ar" },
      ),
    );
    // An invoice short-paid by under 50 cents reads as paid on the client record (clientFin keeps balances over
    // $0.50) while the ledger still holds the cents in 1100. They are listed, not hidden: collect or write them off.
    const short = rpShortPaid(),
      shortAmt = rpSum(short, (x) => x.bal);
    push(
      rpTie(
        "ar-books",
        "Receivables",
        "Receivables agree with the ledger",
        { label: "Ledger 1100 Accounts receivable", amt: rpGLBal(G, "1100") },
        [
          { label: "Open invoices (Reports, the Brief, Billing)", amt: open, drill: "ar:open" },
          { label: `Short-paid by cents, shown as paid (${short.length})`, amt: shortAmt, drill: "ar:short" },
        ],
        "sum",
        short.length ? `${short.map((x) => `${x.d.number} · ${x.c.name} paid ${rpCents(x.paid)} of ${rpCents(x.total)}`).join("; ")}: collect it or write it off with a reason, so the ledger and the client record agree. Every dollar matters.` : "",
      ),
    );
    push(
      rpTie(
        "ret-recv",
        "Receivables",
        "Retainage receivable agrees with the ledger",
        { label: "Retainage held by clients", amt: r2(B.ret) },
        [
          { label: "Held on the client records", amt: rpSum(F, (x) => x.f.retHeld), drill: "ret:recv" },
          { label: "Ledger 1150 Retainage receivable", amt: rpGLBal(G, "1150") },
        ],
        "same",
      ),
    );
  });
  safe("ap", () => {
    const B = companyBalance(),
      A = apAging(today()),
      unpaid = (b) => !(b.paidAt || b.txnId) && !b.ic && !("function" == typeof billPaidUnapproved && billPaidUnapproved(b)),
      approvedOpen = (DB.bills || []).filter((b) => "approved" === b.status && unpaid(b)),
      openAmt = rpSum(approvedOpen, (b) => billTotal(b)),
      waiting = (DB.bills || []).filter((b) => BILL_ACCRUED.includes(b.status) && unpaid(b)),
      waitAmt = rpSum(waiting, (b) => billTotal(b));
    // The Reports, the Brief and the AP aging count a vendor bill as owed once it is entered; the ledger books it
    // (2000) only once it is approved. Both are shown, with the bills awaiting approval named, so the two numbers
    // are never read as one.
    push(
      rpTie(
        "ap",
        "Payables",
        "Payables: bills owed, approved and awaiting approval",
        { label: "Vendor bills owed (Reports, the Brief, AP aging)", amt: r2(B.ap) },
        [
          { label: "Approved, unpaid (in the ledger)", amt: openAmt, drill: "ap:open" },
          { label: `Awaiting approval, unpaid (${waiting.length}; not yet in the ledger)`, amt: waitAmt, drill: "ap:waiting" },
        ],
        "sum",
        `${waiting.length ? `${waiting.map((b) => `${b.vendor} ${b.number}`).join("; ")} wait for approval. ` : ""}${A.payroll ? `Payroll owed is apart: ${rpCents(A.payroll)} (${A.payrollOverdue ? "past due" : "not yet due"}).` : ""}`.trim(),
        { view: "reports", tab: "payables" },
      ),
    );
    push(
      rpTie(
        "ap-books",
        "Payables",
        "Approved bills owed agree with the aging and the ledger",
        { label: "Approved vendor bills, unpaid", amt: openAmt },
        [
          { label: "AP aging, vendor bills", amt: r2(A.bills || 0) - waitAmt, drill: "ap:open" },
          { label: "Ledger 2000 Accounts payable", amt: rpGLBal(G, "2000") },
        ],
        "same",
      ),
    );
    if ("function" == typeof fin2RetainagePayable) {
      const RP = fin2RetainagePayable();
      push(
        rpTie(
          "ret-pay",
          "Payables",
          "Retainage payable agrees with the ledger",
          { label: "Retainage held from subs", amt: r2(RP.total || 0) },
          [
            { label: "Held on the subs' bills", amt: rpSum(RP.rows || [], (x) => rpRetAmt(x)), drill: "ret:pay" },
            { label: "Ledger 2050 Retainage payable", amt: r2(RP.ledger || rpGLBal(G, "2050")) },
          ],
          "same",
        ),
      );
    }
  });
  safe("cash", () => {
    (DB.accounts || [])
      .filter((a) => !repEntity || (a.entityId || "ent1") === repEntity)
      .forEach((a) => {
        const lines = (DB.txns || []).filter((t) => t.acct === a.id && "void" !== t.status && !t.voided),
          reg = r2((+a.opening || 0) + rpSum(lines, (t) => t.amt)),
          gl = rpGLBal(G, "acct:" + a.id),
          glSigned = "card" === a.type ? -gl : gl,
          out = rpOutstanding(a),
          outAmt = rpSum(out, (p) => +p.amount || 0);
        push(
          rpTie(
            "cash:" + a.id,
            "Statements",
            `${a.name}${a.last4 ? " ···" + a.last4 : ""}: the register and the books agree`,
            { label: "Ledger (cash on the books)", amt: glSigned },
            [{ label: `Register: opening ${rpCents(a.opening || 0)} + ${lines.length} lines`, amt: reg, drill: "cash:" + a.id }].concat(
              out.length ? [{ label: `Payments recorded, not yet through the bank (${out.length})`, amt: -outAmt, drill: "cash-out:" + a.id }] : [],
            ),
            "sum",
            `${Math.abs(r2(+a.balance || 0) - reg) > RP_EPS ? `The account's stored balance reads ${rpCents(a.balance)}. ` : ""}${out.length ? "A payment recorded in the ERP leaves the books at once and the bank when it clears. " : ""}${"card" === a.type ? "A card balance below zero is money owed on the card." : ""}`.trim(),
            { view: "bank" },
          ),
        );
      });
  });
  safe("jobcost", () => {
    (DB.projects || [])
      .filter(rpInEnt)
      .forEach((p) => {
        const C = rpJobCost(p);
        if (Math.abs(C.actual) < RP_EPS && !C.codes.length) return;
        push(
          rpTie(
            "job:" + p.id,
            "Project Profitability",
            `${p.project.name}: job cost is bills + bank lines + labor + stock`,
            { label: "Actual cost to date", amt: C.actual },
            C.parts.map((x) => ({ label: x.label, amt: x.amt, drill: `job:${p.id}:${x.id}` })),
            "sum",
            `By cost code the rows add to ${rpCents(C.codeSum)}${Math.abs(C.codeDiff) > RP_EPS ? ` (${rpCents(C.codeDiff)} of rounding, a cent a row)` : ""}. ${C.lines.length ? `By estimate line ${rpCents(C.lineSum)}, plus ${rpCents(C.noLine)} on cost codes with no estimate line.` : ""}`.trim(),
            { view: "reports", tab: "profit", proj: p.id },
          ),
        );
      });
  });
  safe("manual", () => {
    if ("function" != typeof truthManual) return;
    const M = truthManual(R, { entityId: repEntity || "all", manualOnly: !0 }),
      rows = M.rows || [];
    rows.length &&
      push(
        Object.assign(
          rpTie(
            "manual",
            "Statements",
            "Manual journal entries in the period (flagged: on the ledger only)",
            { label: `${rows.length} manual entr${1 === rows.length ? "y" : "ies"}`, amt: rpSum(rows, (m) => rpSum(m.j.lines, (l) => l.dr || 0)) },
            rows.map((m) => ({ label: `${fmt(m.j.date)} · ${m.j.memo || "journal"} · ${(m.flag && m.flag.text) || ""}`, amt: rpSum(m.j.lines, (l) => l.dr || 0), drill: "je:" + m.j.id })),
            "sum",
          ),
          { manual: !0 },
        ),
      );
  });
  return out;
}

// A correction dated in a sealed month lands in the open period it was entered in (postOn): the sealed month keeps
// its figures and the current period lists the correction, with the record to open.
function rpLate(range) {
  const R = range || rpRange(),
    P = companyPL(R);
  return (P.L || []).filter((r) => r.ref && r.ref.postOn && r.ref.date && r.ref.date !== r.ref.postOn && within(r.ref.postOn, R) && !within(r.ref.date, R));
}
function rpLateHtml(range) {
  const L = rpLate(range);
  if (!L.length) return "";
  return `<div class="card rp-late" data-rplate="${L.length}"><h3 class="rep-h" style="margin-top:0">Corrections to Sealed Months</h3><p class="small muted">Dated in a month that is closed, so they post to this period; the sealed month keeps its figures.</p><table class="t"><tbody>${L.map(
    (r, i) => `<tr><td class="dim">${fmt(r.ref.date)} to ${fmt(r.ref.postOn)}</td><td>${esc(r.desc || "")}${r.ref.postOnWhy ? `<div class="small muted">${esc(r.ref.postOnWhy)}</div>` : ""}</td>${rpMoneyCell(rpRowAmt(r))}<td><a href="#" data-rplateopen="${i}">Open</a></td></tr>`,
  ).join("")}</tbody></table></div>`;
}
document.addEventListener("click", (e) => {
  const a = e.target.closest("[data-rplateopen]");
  if (!a) return;
  e.preventDefault();
  const r = rpLate()[+a.dataset.rplateopen];
  r && rpDrillOpen(rpOpenOfRow(r));
});
// ---------------------------------------------------------------------------------------------------------------
// 4. Drill: every part opens the records behind it, each with the bank or card line that backs it
// ---------------------------------------------------------------------------------------------------------------
function rpBackingOf(x) {
  try {
    if (x.row) return truthBacking(x.row);
    if ("invoice" === x.kind || "payment" === x.kind) {
      const c = x.c,
        pays = x.pay ? [x.pay] : (c.payments || []).filter((p) => x.d && p.invoiceId === x.d.id && !p.unapplied),
        hit = pays
          .map((p) => (DB.txns || []).find((t) => (p.txnId && t.id === p.txnId) || t.paymentId === p.id || (t.amt > 0 && Math.abs(t.amt - (+p.amount || 0)) < 0.005 && Math.abs(dayDiff(t.date, p.date)) <= 5 && ["income", "uncat", ""].includes(t.cat || ""))))
          .filter(Boolean);
      return hit.length && hit.every((t) => bfBacked(t))
        ? { kind: "bank", why: `deposited ${hit.map((t) => fmt(t.date) + " " + truthAcctWords(t)).join(", ")}` }
        : pays.length
          ? { kind: "document", why: "payment recorded; no bank deposit matched yet" }
          : { kind: "document", why: "invoiced; not yet paid" };
    }
    if ("txn" === x.kind && x.t) return truthBacking({ kind: "txn", ref: x.t });
    if ("bill" === x.kind && x.b) return truthBacking({ kind: "bill", ref: x.b });
  } catch (e) {}
  return { kind: "document", why: "no bank or card line behind it" };
}
function rpDrillRows(key) {
  const R = rpRange(),
    [kind, a, b] = String(key).split(":"),
    out = [],
    fromRow = (r) => ({ date: r.date, desc: r.desc, amt: rpRowAmt(r), row: r, kind: r.kind, open: rpOpenOfRow(r) });
  if ("pl" === kind) {
    const S = rpPL(R);
    if ("projects" === a || "cost" === a) S.rows.forEach((r) => r.costRows.forEach((x) => out.push(fromRow(x))));
    if ("projects" === a || "income" === a)
      S.rows.forEach((r) => r.inc.forEach((x) => out.push({ date: x.date, desc: x.desc, amt: x.amt, kind: x.kind, c: x.c, d: x.d, pay: x.pay, open: x.d ? { type: "invoice", c: x.c, d: x.d } : null })));
    "noproj-cost" === a && S.none.costRows.forEach((x) => out.push(fromRow(x)));
    "noproj-income" === a && S.none.inc.forEach((x) => out.push({ date: x.date, desc: x.desc, amt: x.amt, kind: x.kind, c: x.c, d: x.d, open: x.d ? { type: "invoice", c: x.c, d: x.d } : null }));
    ("oh-uncoded" === a || "oh" === a) && (S.P.needsCatRows || []).forEach((t) => out.push({ date: t.date, desc: t.desc, amt: r2(-t.amt), kind: "txn", t: t, open: { type: "txn", t: t } }));
    ("oh-unalloc" === a || "oh" === a) &&
      (S.P.L || []).filter((r) => !rpSkipRow(r) && "oh" === rpRowType(r)).forEach((x) => out.push(fromRow(x)));
    if ("proj" === a) {
      const r = S.rows.find((x) => x.id === b);
      r && (r.inc.forEach((x) => out.push({ date: x.date, desc: x.desc, amt: x.amt, kind: x.kind, c: x.c, d: x.d, pay: x.pay, open: x.d ? { type: "invoice", c: x.c, d: x.d } : null })), r.costRows.forEach((x) => out.push(Object.assign(fromRow(x), { amt: -rpRowAmt(x) }))));
    }
  } else if ("inc" === kind) {
    const S = rpPL(R);
    if ("wip" === a) S.rows.filter((r) => Math.abs(r.wip) > RP_EPS).forEach((r) => out.push({ date: R[1], desc: `${rpProjName(r.id)}: change in over/under-billing`, amt: r.wip, kind: "wip", open: { go: { view: "reports", tab: "wip" } } }));
    else if ("bank" === a) (DB.txns || []).filter((t) => within(t.date, R) && t.amt > 0 && "income" === t.cat).forEach((t) => out.push({ date: t.date, desc: t.desc, amt: t.amt, kind: "txn", t: t, open: { type: "txn", t: t } }));
    else if ("undeposited" === a)
      (DB.clients || []).forEach((c) =>
        (c.payments || []).forEach((pay) => {
          if (pay.unapplied || !within(pay.date, R)) return;
          const x = { kind: "payment", c: c, pay: pay, d: (c.invoices || []).find((i) => i.id === pay.invoiceId) };
          "bank" !== rpBackingOf(x).kind && out.push(Object.assign(x, { date: pay.date, desc: `Payment${x.d ? " on " + x.d.number : ""} · ${c.name}`, amt: +pay.amount || 0, open: x.d ? { type: "invoice", c: c, d: x.d } : null }));
        }),
      );
    else S.rows.concat([S.none]).forEach((r) => (r.inc || []).forEach((x) => out.push({ date: x.date, desc: x.desc, amt: x.amt, kind: x.kind, c: x.c, d: x.d, pay: x.pay, open: x.d ? { type: "invoice", c: x.c, d: x.d } : null })));
  } else if ("wip" === kind) {
    const p = rpProj(a),
      J = p && jobFin(p);
    J &&
      (J.invs || []).forEach((i) => out.push({ date: i.date, desc: `${i.number} billed (gross)`, amt: r2(docTotal(i).sub - docTotal(i).disc), kind: "invoice", c: J.c, d: i, open: { type: "invoice", c: J.c, d: i } }));
    J && out.push({ date: today(), desc: `Earned to date: ${rpCents(J.contract)} × ${(100 * (+J.pct || 0)).toFixed(2)}% (cost ${rpCents(J.actual)} ÷ estimate at completion ${rpCents(J.eac)})`, amt: -r2(J.earned), kind: "earned", open: { go: { view: "reports", tab: "profit", proj: p.id } } });
  } else if ("ar" === kind && "short" === a) {
    rpShortPaid().forEach((x) => out.push({ date: x.d.date, desc: `${x.d.number} · ${x.c.name} · paid ${rpCents(x.paid)} of ${rpCents(x.total)}`, amt: x.bal, kind: "invoice", c: x.c, d: x.d, open: { type: "invoice", c: x.c, d: x.d } }));
  } else if ("ar" === kind || "ret" === kind) {
    (DB.clients || []).forEach((c) => {
      const f = clientFin(c);
      "ret" === kind && "recv" === a
        ? (c.invoices || []).filter((i) => !["void", "draft"].includes(i.status) && docTotal(i).ret).forEach((i) => out.push({ date: i.date, desc: `${i.number} · ${c.name} · retainage withheld`, amt: r2(docTotal(i).ret), kind: "invoice", c: c, d: i, open: { type: "invoice", c: c, d: i } }))
        : f.open.forEach((o) => out.push({ date: o.x.due || o.x.date, desc: `${o.x.number} · ${c.name}${o.age > 0 ? ` · ${o.age} days past due` : " · current"}`, amt: o.bal, kind: "invoice", c: c, d: o.x, open: { type: "invoice", c: c, d: o.x } }));
    });
    "ret" === kind &&
      "pay" === a &&
      ((out.length = 0), (fin2RetainagePayable().rows || []).forEach((x) => out.push({ date: x.date || "", desc: rpRetWho(x), amt: rpRetAmt(x), kind: "bill", open: null })));
  } else if ("cash-out" === kind) {
    const ac = (DB.accounts || []).find((x) => x.id === a);
    ac && rpOutstanding(ac).forEach((p) => out.push({ date: p.date, desc: `${p.vendor || ""} · payment recorded, not yet at the bank`, amt: -(+p.amount || 0), kind: "payment", open: p.billId ? { type: "bill", b: (DB.bills || []).find((x) => x.id === p.billId) } : null, manual: !1 }));
  } else if ("ap" === kind && "waiting" === a) {
    (DB.bills || []).filter((b) => BILL_ACCRUED.includes(b.status) && !(b.paidAt || b.txnId) && !b.ic && !("function" == typeof billPaidUnapproved && billPaidUnapproved(b))).forEach((b) => out.push({ date: b.due || b.date, desc: `${b.vendor} · ${b.number} · awaiting approval`, amt: billTotal(b), kind: "bill", b: b, open: { type: "bill", b: b } }));
  } else if ("ap" === kind) {
    (DB.bills || []).filter((b) => "approved" === b.status && !(b.paidAt || b.txnId) && !b.ic).forEach((b) => out.push({ date: b.due || b.date, desc: `${b.vendor} · ${b.number}`, amt: billTotal(b), kind: "bill", b: b, open: { type: "bill", b: b } }));
  } else if ("cash" === kind) {
    (DB.txns || []).filter((t) => t.acct === a).sort((x, y) => String(x.date).localeCompare(String(y.date))).forEach((t) => out.push({ date: t.date, desc: t.desc, amt: t.amt, kind: "txn", t: t, open: { type: "txn", t: t } }));
  } else if ("job" === kind) {
    const p = rpProj(a),
      J = p && jobFin(p);
    if (J) {
      const L = ledger(["", today()]).filter((r) => r.projectId === p.id && !r.income && "cogs" === rpRowType(r));
      "bills" === b && (DB.bills || []).filter((x) => x.projectId === p.id && ((J.byCode || []).some((c) => (c.src || []).includes("bill:" + x.id)) || L.some((r) => r.ref === x))).forEach((x) => out.push({ date: x.date, desc: `${x.vendor} · ${x.number} (${x.status})`, amt: billCost(x), kind: "bill", b: x, open: { type: "bill", b: x } }));
      "bank" === b && L.filter((r) => "txn" === r.kind).forEach((r) => out.push(fromRow(r)));
      "labor" === b && (J.laborByEmp || []).forEach((e) => out.push({ date: "", desc: `${e.name || e.emp || "Crew"} · ${e.hours || ""} h`, amt: r2(+e.cost || +e.amt || 0), kind: "labor", open: { go: { view: "time" } } }));
      "stock" === b && (J.stockRows || []).forEach((u) => out.push({ date: String(u.at || "").slice(0, 10), desc: `${u.invName || "Stock"} · ${u.qty || ""} ${u.unit || ""}`, amt: r2(+u.amount || 0), kind: "stock", open: null }));
    }
  } else if ("je" === kind) {
    const j = ((DB.gl || {}).journals || []).find((x) => x.id === a);
    j && j.lines.forEach((l) => out.push({ date: j.date, desc: `${l.acct} ${l.memo || j.memo || ""}`, amt: r2((l.dr || 0) - (l.cr || 0)), kind: "journal", manual: !0, open: { go: { view: "gl" } } }));
  }
  return out.map((x) => Object.assign(x, { backing: x.manual ? { kind: "hand", why: "posted by hand, with a reason" } : rpBackingOf(x) }));
}
function rpOpenOfRow(r) {
  if (!r || !r.ref) return null;
  if ("bill" === r.kind) return { type: "bill", b: r.ref };
  if ("txn" === r.kind) return { type: "txn", t: r.ref };
  if ("payroll" === r.kind) return { go: { view: "ap" } };
  return null;
}
// Named apart from Report a Problem's rpOpen (src/app.js): one script, so a second `function rpOpen` replaced the
// Report a Problem button's and the button opened nothing (found by the loop lane, 2026-10-20; tests/dupnames_test.py).
function rpDrillOpen(o) {
  if (!o) return;
  if (o.go) {
    try {
      mbCloseModal();
    } catch (e) {}
    return o.go.tab && (repTab = o.go.tab), o.go.proj && (repProj = o.go.proj), (view = o.go.view), void render();
  }
  if ("txn" === o.type && o.t) {
    try {
      mbCloseModal();
    } catch (e) {}
    view = "bank";
    render();
    try {
      "function" == typeof openTxn && setTimeout(() => openTxn(o.t.id), 60);
    } catch (e) {}
    return;
  }
  drillOpen(o);
}
let rpDrillNow = [];
function rpDrill(key, title) {
  const rows = (rpDrillNow = rpDrillRows(key)),
    total = rpSum(rows, (r) => r.amt),
    noBank = rows.filter((r) => "bank" !== r.backing.kind),
    tag = (b) =>
      "bank" === b.kind
        ? `<span class="pill ok rp-bk">Bank line</span>`
        : "hand" === b.kind
          ? `<span class="pill bad rp-bk">${RP_ICON_PEN} By hand</span>`
          : `<span class="pill warn rp-bk">No bank or card line</span>`;
  mbModal(
    esc(title || "The records behind this figure"),
    `<div class="small muted" style="margin-bottom:6px">${rows.length} record${1 === rows.length ? "" : "s"} · ${rpCents(total)}${noBank.length ? ` · ${noBank.length} with no bank or card line behind ${1 === noBank.length ? "it" : "them"} (${rpCents(rpSum(noBank, (r) => r.amt))})` : rows.length ? " · every one backed by a bank or card line" : ""}. Tap a row to open it.</div><div class="tw" style="max-height:60vh;overflow:auto"><table class="t rp-drill"><thead><tr><th>Date</th><th>What</th><th>Backed By</th><th class="money">Amount</th></tr></thead><tbody>${
      rows
        .map(
          (r, i) =>
            `<tr class="${r.open ? "click" : ""}" data-rprow="${i}"><td class="dim">${r.date ? fmt(r.date) : ""}</td><td>${esc(r.desc || "")}</td><td>${tag(r.backing)}<div class="small muted">${esc(r.backing.why || "")}</div></td><td class="money ${r.amt < 0 ? "bad" : ""}">${rpCents(r.amt)}</td></tr>`,
        )
        .join("") || '<tr><td colspan="4" class="muted">Nothing behind this figure in the period.</td></tr>'
    }<tr style="font-weight:600"><td colspan="3">Total</td><td class="money">${rpCents(total)}</td></tr></tbody></table></div>`,
    { submit: null },
  );
  const cl = document.getElementById("mbm-cancel");
  cl && (cl.textContent = "Close");
  document.querySelectorAll("[data-rprow]").forEach((tr) => (tr.onclick = () => rpDrillOpen(rpDrillNow[+tr.dataset.rprow].open)));
}
document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-rpdrill]");
  if (!el) return;
  e.preventDefault(), rpDrill(el.dataset.rpdrill, el.dataset.rptitle || el.innerText.trim());
});

// ---------------------------------------------------------------------------------------------------------------
// 5. Rendering: the tie table, P&L by project/client, line income to cost, overhead, cash forecast, choices
// ---------------------------------------------------------------------------------------------------------------
const rpMoneyCell = (v, drill, title) =>
  `<td class="money ${v < -RP_EPS ? "bad" : ""}">${drill ? `<a href="#" data-rpdrill="${esc(drill)}" data-rptitle="${esc(title || "")}">${rpCents(v)}</a>` : rpCents(v)}</td>`;
function rpTieStatus(t) {
  return t.ok
    ? `<span class="rp-ok">${RP_ICON_TIE} Ties</span>`
    : `<span class="rp-off">${RP_ICON_OFF} Off by ${rpCents(Math.abs(t.diff))}</span>`;
}
function rpTiesHtml(ties, opts) {
  const o = opts || {},
    n = ties.filter((t) => !t.manual).length,
    off = ties.filter((t) => !t.manual && !t.ok);
  if (!ties.length) return "";
  return `<div class="card rp-ties" data-rpties="${esc(o.id || "all")}"><div class="row" style="align-items:baseline;gap:8px;flex-wrap:wrap"><h3 class="rep-h" style="margin:0">${esc(o.title || "Report Ties")}</h3><span class="small ${off.length ? "rp-off" : "rp-ok"}">${off.length ? `${off.length} of ${n} do not tie` : `${n} of ${n} tie to the cent`}</span></div>${o.lead ? `<p class="small muted" style="margin:4px 0 8px">${o.lead}</p>` : ""}<div class="rp-tie-list">${ties
    .map(
      (t) =>
        `<div class="rp-tie ${t.ok ? "" : "off"} ${t.manual ? "manual" : ""}" data-rptie="${esc(t.id)}"><div class="rp-tie-hd"><b>${esc(t.title)}</b>${t.manual ? `<span class="rp-off">${RP_ICON_PEN} Flagged</span>` : rpTieStatus(t)}</div><div class="rp-tie-fig"><span>${esc(t.figure.label)}</span><b class="rp-amt">${rpCents(t.figure.amt)}</b></div><div class="rp-tie-parts">${t.parts
          .map(
            (x, i) =>
              `<div class="rp-part"><span>${t.mode === "same" ? "" : i ? "+ " : "= "}${esc(x.label)}</span>${x.drill ? `<a href="#" class="rp-amt" data-rpdrill="${esc(x.drill)}" data-rptitle="${esc(x.label)}">${rpCents(x.amt)}</a>` : `<span class="rp-amt">${rpCents(x.amt)}</span>`}</div>`,
          )
          .join("")}</div>${t.note ? `<div class="small muted">${esc(t.note)}</div>` : ""}</div>`,
    )
    .join("")}</div></div>`;
}
function rpPLHtml(range) {
  const S = rpPLByClient(range),
    cash = "cash" === S.basis,
    head = `<tr><th>Project</th><th>Client</th><th class="money">Income</th><th class="money">Job Cost</th><th class="money">Gross Profit</th><th class="money">Overhead</th><th class="money">Net Profit</th><th class="money">Net %</th></tr>`,
    body = S.rows
      .map(
        (r) =>
          `<tr data-rpproj="${esc(r.id)}"><td>${esc(rpProjName(r.id))}</td><td class="dim">${esc((rpClientOfProj(r.id) || {}).name || "")}</td>${rpMoneyCell(r.income, "pl:proj:" + r.id, rpProjName(r.id))}${rpMoneyCell(r.cost)}${rpMoneyCell(r.gross)}${rpMoneyCell(r.oh)}${rpMoneyCell(r.net)}<td class="money">${r.income ? Math.round((100 * r.net) / r.income) + "%" : ""}</td></tr>`,
      )
      .join(""),
    tail = S.parts
      .filter((x) => "projects" !== x.id)
      .map((x) => `<tr class="dim"><td colspan="6"><a href="#" data-rpdrill="pl:${x.id}" data-rptitle="${esc(x.label)}">${esc(x.label)}</a></td>${rpMoneyCell(x.amt)}<td></td></tr>`)
      .join(""),
    cl = S.clients
      .map(
        (r) =>
          `<tr><td>${esc(r.name)}</td><td class="dim">${r.projects.map((id) => esc(rpProjName(id))).join(", ")}</td>${rpMoneyCell(r.income)}${rpMoneyCell(r.cost)}${rpMoneyCell(r.gross)}${rpMoneyCell(r.oh)}${rpMoneyCell(r.net)}<td class="money">${r.income ? Math.round((100 * r.net) / r.income) + "%" : ""}</td></tr>`,
      )
      .join("");
  return `<div class="rp-pl" data-rppl="1"><h3 class="rep-h">P&amp;L by Project</h3><p class="small muted">${cash ? "Cash basis: income is the payments received on each project's invoices; cost is what was paid." : "Accrual: income is what each project invoiced in the period plus the change in its over/under-billing; cost is the P&L's own cost rows on the project."} ${esc(S.ohNote)}</p><div class="tw"><table class="t rep-t rp-t"><thead>${head}</thead><tbody>${body}${tail}<tr class="grand"><td colspan="6">Company net profit</td>${rpMoneyCell(S.net)}<td class="money">${S.P.income ? Math.round((100 * S.net) / S.P.income) + "%" : ""}</td></tr></tbody></table></div><div class="small rp-tieline" data-rptieline="pl">${S.ok ? `<span class="rp-ok">${RP_ICON_TIE} Ties</span>` : `<span class="rp-off">${RP_ICON_OFF} Off by ${rpCents(Math.abs(S.diff))}</span>`} Projects' net ${rpCents(S.parts[0].amt)}${S.parts.slice(1).map((x) => ` ${x.amt < 0 ? "−" : "+"} ${esc(x.label.toLowerCase())} ${rpCents(Math.abs(x.amt))}`).join("")} = ${rpCents(S.sum)}; the company P&L says ${rpCents(S.net)}.</div>
    <h3 class="rep-h">P&amp;L by Client</h3><div class="tw"><table class="t rep-t rp-t"><thead><tr><th>Client</th><th>Projects</th><th class="money">Income</th><th class="money">Job Cost</th><th class="money">Gross Profit</th><th class="money">Overhead</th><th class="money">Net Profit</th><th class="money">Net %</th></tr></thead><tbody>${cl}<tr class="grand"><td colspan="6">Clients' net</td>${rpMoneyCell(S.clientNet)}<td></td></tr></tbody></table></div><div class="small muted">Clients' net equals the projects' net (${rpCents(S.parts[0].amt)}); what sits on no project is in the project table above.</div></div>`;
}
// The job report against the P&L by project: why a job's cost reads differently in the two
function rpJobBridgeHtml(range) {
  const B = rpJobBridge(range).filter((x) => Math.abs(x.diff) > RP_EPS);
  if (!B.length) return `<p class="small muted rp-bridge">Each job's cost on its job report equals its cost on the P&amp;L by project.</p>`;
  return `<h3 class="rep-h">Job Reports and the P&amp;L</h3><p class="small muted">A job report counts cost as the job sees it; the P&amp;L as the books recognise it. Where they differ, this is why.</p><div class="tw"><table class="t rep-t rp-t rp-bridge"><thead><tr><th>Project</th><th class="money">Job Report</th><th class="money">P&amp;L</th><th class="money">Difference</th><th>Why</th></tr></thead><tbody>${B.map(
    (x) =>
      `<tr><td>${esc(x.p.project.name)}</td>${rpMoneyCell(x.job)}${rpMoneyCell(x.pl)}${rpMoneyCell(x.diff)}<td class="small">${x.diffs.map((d) => `${esc(d.label)} ${rpCents(d.amt)}: ${esc(d.why)}`).join("<br>")}${Math.abs(x.rest) > RP_EPS ? `<br><span class="rp-off">${RP_ICON_OFF} ${rpCents(x.rest)} not explained</span>` : ""}</td></tr>`,
  ).join("")}</tbody></table></div>`;
}
// Project Profitability › By Line: each estimate and approved change-order line, income to cost, one total that is
// the job's. Actual and committed are the job's own figures by line (J.eacLines), so the lines, the cost codes and
// the job say one number.
function rpLineRows(p) {
  const J = jobFin(p),
    E = J.eacLines || [];
  return E.map((x) => {
    let f = null;
    try {
      f = lineFin(x.key);
    } catch (e) {}
    const price = r2(f ? +f.price || 0 : 0),
      eac = r2(+x.eac || 0),
      actual = r2(+x.actual || 0),
      pct = eac ? Math.min(1, actual / eac) : 0,
      earned = r2(price * pct);
    return {
      key: x.key,
      name: x.name || (x.line && x.line.item) || x.key,
      co: String(x.key).startsWith("co:"),
      code: x.code,
      contract: price,
      billed: r2(f ? +f.billed || 0 : 0),
      collected: r2(f ? +f.collected || 0 : 0),
      retained: r2(f ? +f.retained || 0 : 0),
      earned: earned,
      actual: actual,
      committed: r2(+x.committed || 0),
      budget: r2(+x.budget || 0),
      eac: eac,
      marginToDate: r2(earned - actual),
      marginAtCompletion: r2(price - eac),
    };
  });
}
function rpLineHtml(p) {
  const J = jobFin(p),
    rows = rpLineRows(p);
  if (!rows.length) return "";
  const C = rpJobCost(p),
    T = {};
  ["contract", "billed", "collected", "earned", "actual", "committed", "eac", "marginToDate", "marginAtCompletion"].forEach((k) => (T[k] = rpSum(rows, (r) => r[k])));
  const earnDiff = r2((+J.earned || 0) - T.earned),
    eacDiff = r2((+J.eac || 0) - T.eac),
    cell = (v) => rpMoneyCell(v);
  return `<div class="rp-lines" data-rplines="${esc(p.id)}"><p class="small muted">Each estimate line and approved change-order line: contract value, what was billed and collected, what is earned (the line's contract × its cost ÷ its estimate at completion), cost and commitments, and margin to date and at completion. Cost by line is the job's own: a cost code with several lines shares its untraced cost by budget, so lines, cost codes and the job agree.</p><div class="tw"><table class="t rep-t rp-t"><thead><tr><th>Line</th><th class="money">Contract</th><th class="money">Billed</th><th class="money">Collected</th><th class="money">Earned</th><th class="money">Cost to Date</th><th class="money">Committed</th><th class="money">Est. at Completion</th><th class="money">Margin to Date</th><th class="money">Margin at Completion</th></tr></thead><tbody>${rows
    .map(
      (r) =>
        `<tr><td>${esc(r.name)}${r.co ? ' <span class="small muted">· change order</span>' : ""}<div class="small muted">${esc(r.code || "")}</div></td>${cell(r.contract)}${cell(r.billed)}${cell(r.collected)}${cell(r.earned)}${cell(r.actual)}${cell(r.committed)}${cell(r.eac)}${cell(r.marginToDate)}${cell(r.marginAtCompletion)}</tr>`,
    )
    .join("")}<tr class="grand"><td>Lines</td>${["contract", "billed", "collected", "earned", "actual", "committed", "eac", "marginToDate", "marginAtCompletion"].map((k) => cell(T[k])).join("")}</tr>${
    Math.abs(C.noLine) > RP_EPS
      ? `<tr class="dim"><td>Cost on cost codes with no estimate line</td><td></td><td></td><td></td><td></td>${cell(C.noLine)}<td></td><td></td><td></td><td></td></tr>`
      : ""
  }${Math.abs(C.lineRounding) > RP_EPS ? `<tr class="dim"><td>Rounding (each line rounds to the cent)</td><td></td><td></td><td></td><td></td>${cell(C.lineRounding)}<td></td><td></td><td></td><td></td></tr>` : ""}${Math.abs(earnDiff) > RP_EPS ? `<tr class="dim"><td>The job earns on its total cost, not line by line</td><td></td><td></td><td></td>${cell(earnDiff)}<td></td><td></td>${Math.abs(eacDiff) > RP_EPS ? cell(eacDiff) : "<td></td>"}<td></td><td></td></tr>` : ""}<tr class="grand"><td>Job</td>${cell(J.contract)}${cell(J.billed)}${cell(J.collected)}${cell(J.earned)}${cell(J.actual)}${cell(J.committed)}${cell(J.eac)}${cell(r2(J.earned - J.actual))}${cell(r2(J.contract - J.eac))}</tr></tbody></table></div><div class="small rp-tieline" data-rptieline="lines">${Math.abs(C.lineDiff) <= RP_EPS ? `<span class="rp-ok">${RP_ICON_TIE} Ties</span>` : `<span class="rp-off">${RP_ICON_OFF} Off by ${rpCents(Math.abs(C.lineDiff))}</span>`} Lines ${rpCents(C.lineSum)} + cost on codes with no line ${rpCents(C.noLine)}${Math.abs(C.lineRounding) > RP_EPS ? ` + rounding ${rpCents(C.lineRounding)}` : ""} = ${rpCents(r2(C.lineSum + C.noLine + C.lineRounding))}; the job's cost to date is ${rpCents(C.actual)}.</div></div>`;
}
// Overhead analysis: the pool by category, month by month, as a % of revenue; the burden rate; absorbed against
// actual; and the monthly revenue that covers the overhead at the current gross margin.
function rpOverhead(range) {
  const R = range || rpRange(),
    months = ("function" == typeof ohMonthsIn ? ohMonthsIn(R) : []).slice(-12),
    cats = {},
    M = months.map((ym) => {
      const end = rpYmEnd(ym),
        P = companyPL([ym + "-01", end > today() ? today() : end]),
        lines = Object.assign({}, P.oh || {});
      Object.keys(lines).forEach((k) => (cats[k] = 1));
      return { ym: ym, P: P, lines: lines, ohT: r2(P.ohT), income: r2(P.income), gross: r2(P.gross), pct: P.income ? (100 * P.ohT) / P.income : null };
    }),
    T = "function" == typeof ohTrailing ? ohTrailing() : null,
    full = M.filter((m) => rpYmEnd(m.ym) < today()).slice(-3),
    avgOH = full.length ? r2(rpSum(full, (m) => m.ohT) / full.length) : 0,
    gIncome = rpSum(full, (m) => m.income),
    gGross = rpSum(full, (m) => m.gross),
    gm = gIncome ? gGross / gIncome : 0,
    breakEven = gm > 0 ? r2(avgOH / gm) : null,
    ab = "function" == typeof ohAbsorption ? ohAbsorption(R) : null;
  return { range: R, months: M, cats: Object.keys(cats).sort(), trailing: T, full: full, avgOH: avgOH, gm: gm, breakEven: breakEven, absorption: ab };
}
function rpOverheadHtml(range) {
  const O = rpOverhead(range);
  if (!O.months.length) return "";
  const pct = (v) => (null == v ? "—" : `${Math.round(v)}%`);
  return `<div class="rp-oh" data-rpoh="1"><h3 class="rep-h">Overhead Analysis</h3><div class="cash-grid rp-oh-kpi"><div><span>Average Monthly Overhead</span><b>${money(O.avgOH)}</b><i>${O.full.length ? `${O.full[0].ym} to ${O.full[O.full.length - 1].ym}, the last ${O.full.length} full month${1 === O.full.length ? "" : "s"}` : "no full month yet"}</i></div><div><span>Gross Margin</span><b>${O.gm ? Math.round(100 * O.gm) + "%" : "—"}</b><i>the same months</i></div><div><span>Break-Even Monthly Revenue</span><b data-rpbreakeven="${O.breakEven || 0}">${null == O.breakEven ? "—" : money(O.breakEven)}</b><i>${null == O.breakEven ? "no gross margin in those months to cover it" : `overhead ${money(O.avgOH)} ÷ gross margin ${Math.round(100 * O.gm)}%`}</i></div><div><span>Burden Rate</span><b>${O.trailing ? (100 * O.trailing.rate).toFixed(1) + "%" : "—"}</b><i>${O.absorption ? `${O.absorption.under >= 0 ? "under" : "over"}-absorbed ${money(Math.abs(O.absorption.under))} in the period` : ""}</i></div></div><div class="tw"><table class="t rep-t rp-t"><thead><tr><th>Category</th>${O.months.map((m) => `<th class="money">${m.ym}</th>`).join("")}<th class="money">Total</th></tr></thead><tbody>${O.cats
    .map((c) => `<tr><td>${esc(c)}</td>${O.months.map((m) => `<td class="money">${m.lines[c] ? money(m.lines[c]) : "—"}</td>`).join("")}<td class="money">${money(rpSum(O.months, (m) => m.lines[c] || 0))}</td></tr>`)
    .join("")}<tr class="grand"><td>Overhead</td>${O.months.map((m) => `<td class="money">${money(m.ohT)}</td>`).join("")}<td class="money">${money(rpSum(O.months, (m) => m.ohT))}</td></tr><tr class="dim"><td>Revenue</td>${O.months.map((m) => `<td class="money">${m.income ? money(m.income) : "—"}</td>`).join("")}<td class="money">${money(rpSum(O.months, (m) => m.income))}</td></tr><tr class="dim"><td>Overhead % of Revenue</td>${O.months.map((m) => `<td class="money">${pct(m.pct)}</td>`).join("")}<td class="money">${pct(rpSum(O.months, (m) => m.income) ? (100 * rpSum(O.months, (m) => m.ohT)) / rpSum(O.months, (m) => m.income) : null)}</td></tr></tbody></table></div><p class="small muted">Each month's operating expenses on the P&amp;L by category, Needs Category included until it is coded. Break-even monthly revenue is the revenue whose gross profit pays one month's overhead: below it the firm loses money before any project margin is counted. Money wasted is money that cannot go to raises, bonuses, more staff, charity or extra value for the client.</p></div>`;
}
// Cash & Receivables › Cash Forecast: 13 weeks, backlog and retainage both ways
function rpCashHtml() {
  const F = cashForecast(),
    B = companyBalance(),
    G = rpGL(),
    backlog = (DB.projects || []).filter(rpInEnt).map((p) => ({ p: p, J: jobFin(p) })).filter((x) => x.J.contract),
    RP = "function" == typeof fin2RetainagePayable ? fin2RetainagePayable() : { rows: [], total: 0, ledger: 0 },
    recv = (DB.clients || []).map((c) => ({ c: c, f: clientFin(c) })).filter((x) => x.f.retHeld > RP_EPS),
    lowW = F.weeks.reduce((a, w) => (w.balance < a.balance ? w : a), F.weeks[0] || { balance: 0 });
  return `<div class="rep-head"><div><h2 style="margin:0">Cash Forecast</h2><div class="small muted">The next 13 weeks from ${fmtL(today())}, backlog and retainage both ways</div></div></div>
  <div class="cash-grid rp-cash-kpi"><div><span>Cash Today</span><b>${money(F.cash)}</b><i>bank ${money(B.cash)}${B.undeposited ? ` + not yet deposited ${money(B.undeposited)}` : ""}</i></div><div><span>13-Week Low</span><b class="${F.low < 0 ? "bad" : ""}" data-rplow="${r2(F.low)}">${money(F.low)}</b><i>week of ${lowW ? fmtL(lowW.start) : "—"}</i></div><div><span>Backlog</span><b>${money(rpSum(backlog, (x) => x.J.backlog))}</b><i>contract not yet earned, ${backlog.length} job${1 === backlog.length ? "" : "s"}</i></div><div><span>Retainage</span><b>${money(B.ret)} in · ${money(RP.total || 0)} out</b><i>held by clients · held from subs</i></div></div>
  <h3 class="rep-h">13-Week Cash Flow</h3><div class="tw"><table class="t rep-t rp-t rp-13w"><thead><tr><th>Week Of</th><th class="money">In</th><th class="money">Out</th><th class="money">Net</th><th class="money">Balance</th><th>What Moves</th></tr></thead><tbody>${F.weeks
    .map(
      (w) =>
        `<tr class="${w.balance < 0 ? "bad" : ""}"><td>${fmt(w.start)}</td><td class="money">${w.inflow ? money(w.inflow) : "—"}</td><td class="money">${w.outflow ? money(w.outflow) : "—"}</td><td class="money ${w.net < 0 ? "bad" : ""}">${money(w.net)}</td><td class="money"><b>${money(w.balance)}</b></td><td class="small">${w.items.map(([l, a]) => `${esc(l)} ${a < 0 ? "−" : "+"}${money(Math.abs(a))}`).join(" · ") || '<span class="muted">nothing scheduled</span>'}</td></tr>`,
    )
    .join("")}<tr class="grand"><td>13 weeks</td><td class="money">${money(rpSum(F.weeks, (w) => w.inflow))}</td><td class="money">${money(rpSum(F.weeks, (w) => w.outflow))}</td><td class="money">${money(rpSum(F.weeks, (w) => w.net))}</td><td class="money">${money(F.weeks.length ? F.weeks[F.weeks.length - 1].balance : F.cash)}</td><td></td></tr></tbody></table></div><p class="small muted">In: open invoices at their due date (or the date the client promised), the next progress bill, retainage at release. Out: bills to pay (not those the bank has already paid), open PO balances, the payroll cadence, recurring overhead and what is owed on the cards. Cash today ${money(F.cash)} + 13 weeks' net ${money(rpSum(F.weeks, (w) => w.net))} = ${money(F.weeks.length ? F.weeks[F.weeks.length - 1].balance : F.cash)}.</p>
  <h3 class="rep-h">Backlog</h3><div class="tw"><table class="t rep-t rp-t"><thead><tr><th>Job</th><th class="money">Contract</th><th class="money">Earned</th><th class="money">Backlog</th><th class="money">Backlog Gross Profit</th></tr></thead><tbody>${backlog
    .map((x) => `<tr><td>${esc(x.p.project.name)}</td>${rpMoneyCell(x.J.contract)}${rpMoneyCell(x.J.earned)}${rpMoneyCell(x.J.backlog)}${rpMoneyCell(x.J.backlogGP || 0)}</tr>`)
    .join("")}<tr class="grand"><td>All jobs</td>${rpMoneyCell(rpSum(backlog, (x) => x.J.contract))}${rpMoneyCell(rpSum(backlog, (x) => x.J.earned))}${rpMoneyCell(rpSum(backlog, (x) => x.J.backlog))}${rpMoneyCell(rpSum(backlog, (x) => x.J.backlogGP || 0))}</tr></tbody></table></div>
  <h3 class="rep-h">Retainage</h3><div class="grid2 rp-ret"><div class="card"><h4 style="margin:0 0 6px">Receivable · Held by Clients</h4><table class="t"><tbody>${recv.map((x) => `<tr><td>${esc(x.c.name)}</td>${rpMoneyCell(x.f.retHeld, "ret:recv", "Retainage held by clients")}</tr>`).join("") || '<tr><td class="muted">None held.</td></tr>'}<tr class="grand"><td>Total · ledger 1150 ${rpCents(rpGLBal(G, "1150"))}</td>${rpMoneyCell(B.ret)}</tr></tbody></table></div><div class="card"><h4 style="margin:0 0 6px">Payable · Held from Subs</h4><table class="t"><tbody>${(RP.rows || []).map((x) => `<tr><td>${esc(rpRetWho(x))}</td>${rpMoneyCell(rpRetAmt(x))}</tr>`).join("") || '<tr><td class="muted">None held.</td></tr>'}<tr class="grand"><td>Total · ledger 2050 ${rpCents(RP.ledger || 0)}</td>${rpMoneyCell(RP.total || 0)}</tr></tbody></table></div></div>${rpTiesHtml(rpTies(null, ["wip", "ar"]).filter((t) => /ret-recv|wip/.test(t.id)).concat(rpTies(null, ["ap"]).filter((t) => "ret-pay" === t.id)), { id: "cash", title: "Ties" })}`;
}


// ---- Estimate versus actual at close-out (the Standard, Estimating and preconstruction: "Estimate vs. actual review
// at close-out, by cost code, with lessons fed into the price book"). A job is in close-out at 85% of its estimated
// cost (the rule the Close-out list uses). Each cost code compares the estimate's budget with the cost at completion;
// a code off by 10% and $500 or more can be proposed to the price book. The proposal is a drafted change in Company ›
// Changes (DB.changes, the improvement loop's one list): the owner approves it, and only then does the code's cost
// factor (DB.company.costBook) change. Nothing here edits an estimate.
const RP_CO_PCT = 0.1,
  RP_CO_MIN = 500;
const rpInCloseout = (J) => (+J.pct || 0) >= 0.85;
function rpCloseout(p) {
  const J = jobFin(p),
    book = (DB.company || {}).costBook || {},
    rows = (J.byCode || [])
      .filter((b) => (+b.budget || 0) > RP_EPS || (+b.actual || 0) > RP_EPS)
      .map((b) => {
        const budget = r2(+b.budget || 0),
          actual = r2(+b.actual || 0),
          committed = r2(+b.committed || 0),
          atCompletion = r2(Math.max(budget, actual + committed)),
          final = rpInCloseout(J) ? r2(actual + committed) : atCompletion,
          variance = r2(final - budget),
          pct = budget ? variance / budget : null,
          key = `costbook:${p.id}:${b.code}`,
          proposed = (DB.changes || []).find((c) => c.key === key && "declined" !== c.status);
        return {
          code: b.code,
          name: b.name || "",
          budget: budget,
          actual: actual,
          committed: committed,
          final: final,
          variance: variance,
          pct: pct,
          factor: budget ? r2(final / budget) : null,
          book: book[b.code] || null,
          proposable: rpInCloseout(J) && budget > RP_EPS && null != pct && Math.abs(pct) >= RP_CO_PCT && Math.abs(variance) >= RP_CO_MIN,
          proposed: proposed || null,
        };
      });
  return { p: p, J: J, closeout: rpInCloseout(J), rows: rows };
}
function rpCloseoutHtml(p) {
  const C = rpCloseout(p);
  if (!C.rows.length) return "";
  const can = (() => {
    try {
      return ["owner", "pm", "controller"].includes(role());
    } catch (e) {
      return !1;
    }
  })();
  return `<div class="rp-closeout" data-rpcloseout="${esc(p.id)}"><h3 class="rep-h">Estimate Versus Actual</h3><p class="small muted">${
    C.closeout
      ? `${esc(p.project.name)} is in close-out (${Math.round(100 * C.J.pct)}% of its estimated cost). Each cost code: the estimate's budget against the final cost. A code off by 10% and ${money(RP_CO_MIN)} or more can be proposed to the price book; the owner approves it under Company › Changes.`
      : `Each cost code: the estimate's budget against the cost at completion as it stands. The review and the price-book proposals open at close-out (85% of the estimated cost; ${Math.round(100 * (+C.J.pct || 0))}% today).`
  }</p><div class="tw"><table class="t rep-t rp-t"><thead><tr><th>Cost Code</th><th class="money">Estimate</th><th class="money">Cost to Date</th><th class="money">Committed</th><th class="money">${C.closeout ? "Final" : "At Completion"}</th><th class="money">Variance</th><th class="money">Variance %</th><th>Price Book</th></tr></thead><tbody>${C.rows
    .map(
      (r) =>
        `<tr><td><b>${esc(r.code)}</b> ${esc(r.name)}</td>${rpMoneyCell(r.budget)}${rpMoneyCell(r.actual)}${rpMoneyCell(r.committed)}${rpMoneyCell(r.final)}<td class="money ${r.variance > RP_EPS ? "bad" : ""}">${rpCents(r.variance)}</td><td class="money">${null == r.pct ? "—" : `${r.pct > 0 ? "+" : ""}${Math.round(100 * r.pct)}%`}</td><td>${
          r.proposed
            ? `<span class="small">${"draft" === r.proposed.status ? "Proposed, awaiting the owner" : "live" === r.proposed.status ? "In the price book" : esc(r.proposed.status)}</span>`
            : r.proposable && can
              ? `<button class="btn sm" data-rpcostbook="${esc(p.id)}:${esc(r.code)}">Propose to the Price Book</button>`
              : `<span class="small muted">${r.book ? `cost factor ${r.book}` : ""}</span>`
        }</td></tr>`,
    )
    .join("")}</tbody></table></div></div>`;
}
function rpProposeCostBook(pid, code) {
  const p = rpProj(pid),
    C = p && rpCloseout(p),
    r = C && C.rows.find((x) => x.code === code);
  if (!r || !r.proposable) return void toast("Nothing to propose for this cost code yet");
  const key = `costbook:${pid}:${code}`;
  if ((DB.changes || []).some((c) => c.key === key && "declined" !== c.status)) return void toast("Already proposed");
  const by = (currentUser() || {}).name || role(),
    from = r.book || 1,
    to = r.factor,
    dir = r.variance > 0 ? "over" : "under",
    ch = {
      id: uid("ch"),
      key: key,
      title: `Price book: ${r.code} ${r.name} ran ${Math.abs(Math.round(100 * r.pct))}% ${dir} the estimate on ${p.project.name}`,
      why: `Estimated ${money(r.budget)}, final ${money(r.final)} (${dir} by ${money(Math.abs(r.variance))}). New estimates for ${r.code} ${r.name} carry a cost factor of ${to} until the next close-out says otherwise. (Estimating and preconstruction: estimate vs. actual review at close-out, by cost code, with lessons fed into the price book. Every dollar matters: ${r.variance > 0 ? "an estimate that runs short is margin given away" : "an estimate that runs long loses work we should win"}.)`,
      kind: "setting",
      delta: { path: `company.costBook.${r.code}`, from: from, to: to, label: `Cost factor for ${r.code} ${r.name} on new estimates` },
      evidence: [{ t: `${p.project.name}: estimate ${rpCents(r.budget)}, cost to date ${rpCents(r.actual)}, committed ${rpCents(r.committed)}, final ${rpCents(r.final)}`, m: "job cost, Reports › Project Profitability" }],
      status: "draft",
      at: today(),
      by: by,
      source: "closeout",
      projectId: pid,
    };
  (DB.changes = DB.changes || []).push(ch);
  try {
    log(`Proposed to the price book: ${ch.title}`, "change", by);
  } catch (e) {}
  save(), render(), toast(`Proposed to the price book: ${r.code} ${r.name}`, () => {
    try {
      (mtTab = "changes"), (mtOpen = "");
    } catch (e) {}
    (view = "meetings"), render();
  });
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-rpcostbook]");
  if (!b) return;
  e.preventDefault();
  const [pid, code] = b.dataset.rpcostbook.split(":");
  rpProposeCostBook(pid, code);
});

// ---- The accounting choices (BACKLOG §1.13 #8): Alan and the accountant decide; the ERP shows each one, its
// default, what it moves, and who changed it, when and why.
const RP_CHOICES = [
  {
    id: "devCosts",
    n: "Mercer & Bond Development Costs",
    opts: [
      ["expense", "Expense as incurred (the P&L today)"],
      ["capitalize", "Capitalise to the property"],
    ],
    def: "expense",
    note: "Costs on a property the firm owns and develops (206 Lenox) are probably capitalised to the property, not expensed; expensed, the P&L understates profit. Settle with the accountant.",
    stake: () => {
      const own = (DB.projects || []).filter((p) => {
        const c = rpClientOfProj(p.id);
        return c && /LLC|Lenox|Mercer/i.test(c.name || "") && !(+jobFin(p).contract || 0);
      });
      return { label: "Cost on owned-property jobs year to date", amt: rpSum(own, (p) => jobFin(p, [today().slice(0, 4) + "-01-01", today()]).actual) };
    },
  },
  {
    id: "taxRevRec",
    n: "Revenue Recognition for Tax",
    opts: [
      ["poc", "Percentage of completion (as the management view)"],
      ["completed", "Completed contract"],
    ],
    def: "poc",
    note: "The management view earns revenue cost-to-cost. For tax, a contractor under the small-contractor threshold may use completed contract instead. The P&L on these screens stays the management view either way.",
    stake: () => ({ label: "Revenue earned on unfinished jobs year to date", amt: r2(companyPL([today().slice(0, 4) + "-01-01", today()]).income) }),
  },
  {
    id: "ohBasis",
    n: "Overhead Allocation Basis",
    opts: Object.entries(typeof OH_BASES !== "undefined" ? OH_BASES : { cost: ["total direct cost"] }).map(([k, v]) => [k, v[0]]),
    def: "cost",
    note: "How overhead is shared across jobs. Total direct cost is the default; labor or hours suit a labor-heavy firm. It moves each job's net, never the company's.",
    read: () => ("function" == typeof ohBasis ? ohBasis() : "cost"),
    stake: null,
  },
];
function rpChoice(id) {
  const C = RP_CHOICES.find((c) => c.id === id),
    A = (DB.company.acctChoices = DB.company.acctChoices || {});
  return C ? (C.read ? C.read() : (A[id] && A[id].value) || C.def) : "";
}
function rpChoicesHtml() {
  const A = DB.company.acctChoices || {},
    can = rpCanEditChoices();
  return `<div class="card rp-choices" data-rpchoices="1"><h3 class="rep-h" style="margin-top:0">Accounting Choices to Settle with the Accountant</h3><p class="small muted">Alan and the accountant decide these. Each shows its default and what it moves; a change records who, when and why.</p>${RP_CHOICES.map((c) => {
    const v = rpChoice(c.id),
      h = ((A[c.id] || {}).history || []).slice(-1)[0],
      S = c.stake ? c.stake() : null;
    return `<div class="rp-choice"><label class="f"><span><b>${esc(c.n)}</b></span><select data-rpchoice="${c.id}" ${can ? "" : "disabled"}>${c.opts.map(([k, l]) => `<option value="${k}" ${k === v ? "selected" : ""}>${esc(l)}${k === c.def ? " · default" : ""}</option>`).join("")}</select></label><div class="small muted">${esc(c.note)}${S ? ` ${esc(S.label)}: ${money(S.amt)}.` : ""}${h ? ` Last changed by ${esc(h.by)} on ${fmtL(h.on)}: ${esc(h.why)}.` : v === c.def ? " Not yet decided; the default applies." : ""}</div></div>`;
  }).join("")}</div>`;
}
document.addEventListener("change", (e) => {
  const s = e.target.closest("[data-rpchoice]");
  if (!s) return;
  const id = s.dataset.rpchoice,
    C = RP_CHOICES.find((c) => c.id === id);
  if (!C || !rpCanEditChoices()) return;
  const before = rpChoice(id),
    to = s.value;
  if (to === before) return;
  const why = appPrompt(`Why change ${C.n} to "${(C.opts.find((o) => o[0] === to) || [0, to])[1]}"? (agreed with the accountant, the date)`);
  if (!why || !String(why).trim()) return (s.value = before), void toast("Not changed: a reason is needed");
  const A = (DB.company.acctChoices = DB.company.acctChoices || {}),
    rec = (A[id] = A[id] || { value: C.def, history: [] }),
    by = (currentUser() || {}).name || role();
  "ohBasis" === id && (DB.company.ohBasis = to);
  (rec.value = to), rec.history.push({ from: before, to: to, by: by, on: today(), at: appNowIso(), why: String(why).trim() });
  try {
    audit("company", "acctChoices", `${C.n}: ${before} → ${to}`, before, to, String(why).trim());
  } catch (err) {}
  save(), render(), toast(`${C.n} set to ${(C.opts.find((o) => o[0] === to) || [0, to])[1]}`, () => ((repTab = "financials"), (view = "reports"), render()));
});

// ---------------------------------------------------------------------------------------------------------------
// 6. Excel: any report, every table on it, one sheet each (a minimal .xlsx writer: stored zip, inline strings)
// ---------------------------------------------------------------------------------------------------------------
const RP_CRC = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = 1 & c ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
function rpCrc32(u8) {
  let c = 0xffffffff;
  for (let i = 0; i < u8.length; i++) c = RP_CRC[(c ^ u8[i]) & 255] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
function rpZip(files) {
  const enc = new TextEncoder(),
    parts = [],
    central = [];
  let off = 0;
  files.forEach(([name, text]) => {
    const nb = enc.encode(name),
      data = enc.encode(text),
      crc = rpCrc32(data),
      lh = new DataView(new ArrayBuffer(30));
    lh.setUint32(0, 0x04034b50, !0), lh.setUint16(4, 20, !0), lh.setUint16(6, 0x0800, !0), lh.setUint16(8, 0, !0), lh.setUint16(10, 0, !0), lh.setUint16(12, 0x21, !0), lh.setUint32(14, crc, !0), lh.setUint32(18, data.length, !0), lh.setUint32(22, data.length, !0), lh.setUint16(26, nb.length, !0), lh.setUint16(28, 0, !0);
    parts.push(new Uint8Array(lh.buffer), nb, data);
    const ch = new DataView(new ArrayBuffer(46));
    ch.setUint32(0, 0x02014b50, !0), ch.setUint16(4, 20, !0), ch.setUint16(6, 20, !0), ch.setUint16(8, 0x0800, !0), ch.setUint16(10, 0, !0), ch.setUint16(12, 0, !0), ch.setUint16(14, 0x21, !0), ch.setUint32(16, crc, !0), ch.setUint32(20, data.length, !0), ch.setUint32(24, data.length, !0), ch.setUint16(28, nb.length, !0), ch.setUint16(30, 0, !0), ch.setUint16(32, 0, !0), ch.setUint16(34, 0, !0), ch.setUint16(36, 0, !0), ch.setUint32(38, 0, !0), ch.setUint32(42, off, !0);
    central.push(new Uint8Array(ch.buffer), nb);
    off += 30 + nb.length + data.length;
  });
  const cdSize = central.reduce((a, x) => a + x.length, 0),
    end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, !0), end.setUint16(8, files.length, !0), end.setUint16(10, files.length, !0), end.setUint32(12, cdSize, !0), end.setUint32(16, off, !0), end.setUint16(20, 0, !0);
  const all = [...parts, ...central, new Uint8Array(end.buffer)],
    out = new Uint8Array(all.reduce((a, x) => a + x.length, 0));
  let p = 0;
  return all.forEach((x) => (out.set(x, p), (p += x.length))), out;
}
const rpXmlEsc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, "");
// "$1,234.50" -> 1234.5, "−$2,618" -> -2618, "(1,200)" -> -1200, "21%" -> 0.21; anything else stays text
function rpCellValue(s) {
  const t = String(s || "").trim();
  if (!t || t.length > 24) return t;
  const m = t.match(/^([−\-–]?)\(?\$?\s?([\d,]+(?:\.\d+)?)\)?(%?)$/);
  if (!m || !/\d/.test(m[2]) || (!/[$%]/.test(t) && /,\d{1,2}(,|$)/.test(m[2]))) return t;
  let v = +m[2].replace(/,/g, "");
  return m[1] || /^\(.*\)$/.test(t) ? (v = -v) : 0, m[3] ? v / 100 : v;
}
const rpColName = (i) => {
  let s = "";
  for (i++; i > 0; i = Math.floor((i - 1) / 26)) s = String.fromCharCode(65 + ((i - 1) % 26)) + s;
  return s;
};
function rpXlsxBytes(sheets) {
  const used = {},
    names = sheets.map((s, i) => {
      let n = String(s.name || `Sheet ${i + 1}`).replace(/[\[\]:*?\/\\]/g, " ").replace(/\s+/g, " ").trim().slice(0, 31) || `Sheet ${i + 1}`;
      for (let k = 2; used[n.toLowerCase()]; k++) n = n.slice(0, 28) + " " + k;
      return (used[n.toLowerCase()] = 1), n;
    }),
    sheetXml = (rows) =>
      `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${rows
        .map(
          (r, ri) =>
            `<row r="${ri + 1}">${r
              .map((c, ci) => {
                const ref = rpColName(ci) + (ri + 1),
                  v = "number" == typeof c ? c : rpCellValue(c);
                return "number" == typeof v && isFinite(v) ? `<c r="${ref}"${ri ? "" : ' s="1"'}><v>${v}</v></c>` : `<c r="${ref}" t="inlineStr"${ri ? "" : ' s="1"'}><is><t xml:space="preserve">${rpXmlEsc(v)}</t></is></c>`;
              })
              .join("")}</row>`,
        )
        .join("")}</sheetData></worksheet>`,
    files = [
      ["[Content_Types].xml", `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>${names.map((n, i) => `<Override PartName="/xl/worksheets/sheet${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join("")}</Types>`],
      ["_rels/.rels", `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`],
      ["xl/workbook.xml", `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>${names.map((n, i) => `<sheet name="${rpXmlEsc(n)}" sheetId="${i + 1}" r:id="rId${i + 1}"/>`).join("")}</sheets></workbook>`],
      ["xl/_rels/workbook.xml.rels", `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">${names.map((n, i) => `<Relationship Id="rId${i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${i + 1}.xml"/>`).join("")}<Relationship Id="rId${names.length + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>`],
      ["xl/styles.xml", `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs></styleSheet>`],
      ...sheets.map((s, i) => [`xl/worksheets/sheet${i + 1}.xml`, sheetXml(s.rows)]),
    ];
  return rpZip(files);
}
// The tables on the report on screen, each with the heading above it
function rpScreenSheets() {
  const host = document.getElementById("rep-print-area");
  if (!host) return [];
  const tables = [...host.querySelectorAll("table")].filter((t) => t.rows.length && !t.closest(".mbm"));
  return tables.map((t, i) => {
    let h = null,
      n = t;
    for (; n && n !== host && !h; ) {
      let s = n.previousElementSibling;
      for (; s && !h; ) (h = s.matches("h2,h3,h4") ? s : s.querySelector && [...s.querySelectorAll("h2,h3,h4")].pop()), (s = s.previousElementSibling);
      n = n.parentElement;
    }
    const rows = [...t.rows].map((r) => [...r.cells].flatMap((c) => [String(c.innerText || "").replace(/\s*\n\s*/g, " ").trim(), ...Array(Math.max(0, (+c.colSpan || 1) - 1)).fill("")]));
    return { name: (h && h.innerText.trim()) || `Table ${i + 1}`, rows: rows };
  });
}
function rpExportExcel() {
  const sheets = rpScreenSheets();
  if (!sheets.length) return void toast("Nothing on this report to export");
  const R = rpRange(),
    tabName = ((REP_GROUPS.flatMap((g) => g.tabs).find((t) => t[0] === repTab) || [0, repTab])[1] || "Report").replace(/[^A-Za-z0-9]+/g, "-"),
    file = `SmartDesign-${tabName}-${R[0] || "start"}-to-${R[1] || today()}.xlsx`,
    bytes = rpXlsxBytes(sheets),
    url = URL.createObjectURL(new Blob([bytes], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" })),
    a = Object.assign(document.createElement("a"), { href: url, download: file });
  document.body.appendChild(a), a.click(), a.remove(), setTimeout(() => URL.revokeObjectURL(url), 4000);
  RP.lastExport = { file: file, sheets: sheets.map((s) => s.name), bytes: bytes.length };
  toast(`Exported ${file} · ${sheets.length} sheet${1 === sheets.length ? "" : "s"}`);
}
const RP = { lastExport: null };

// ---------------------------------------------------------------------------------------------------------------
// 7. Wiring into the Reports tabs (renderReports is wrapped; this is the outermost layer)
// ---------------------------------------------------------------------------------------------------------------
(function rpStyles() {
  if (document.getElementById("rp-styles")) return;
  const s = document.createElement("style");
  s.id = "rp-styles";
  s.textContent = `.rp-ties{margin-top:14px}.rp-tie-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}.rp-tie{border:1px solid var(--line,#e3e3e3);border-radius:10px;padding:10px 12px;background:var(--card,#fff)}.rp-tie.off{border-color:var(--bad,#c0392b)}.rp-tie-hd{display:flex;justify-content:space-between;gap:8px;align-items:baseline}.rp-tie-hd b{font-size:13px}.rp-tie-fig,.rp-part{display:flex;justify-content:space-between;gap:10px;font-size:13px;padding:2px 0}.rp-tie-fig{border-bottom:1px solid var(--line,#e3e3e3);margin:6px 0 2px;padding-bottom:4px}.rp-part span:first-child{color:var(--ink-2,#555)}.rp-amt{font-variant-numeric:tabular-nums;white-space:nowrap}.rp-ok{color:var(--good,#1e7b45);white-space:nowrap;font-weight:600}.rp-off{color:var(--bad,#c0392b);white-space:nowrap;font-weight:600}.rp-tieline{margin:6px 0 12px}.rp-t td,.rp-t th{white-space:nowrap}.rp-13w td.small{white-space:normal;min-width:220px}.rp-choice{margin:10px 0}.rp-choice select{max-width:100%}.rp-bk{font-size:11px}.rep-bar .rp-xls{display:inline-flex;align-items:center;gap:4px}@media (max-width:520px){.rp-tie-list{grid-template-columns:1fr}.rp-oh-kpi,.rp-cash-kpi{grid-template-columns:1fr 1fr!important}.rp-tie-fig,.rp-part{font-size:14px}.rp-part{padding:5px 0}.rp-part a.rp-amt{min-height:44px;display:inline-flex;align-items:center}}`;
  document.head.appendChild(s);
})();
// the Cash Forecast sub-tab (Cash & Receivables)
try {
  const g = REP_GROUPS.find((x) => "cash" === x.id);
  g && !g.tabs.some((t) => "cash13" === t[0]) && g.tabs.push(["cash13", "Cash Forecast"]);
  REP_DEFS.cash13 = "The next 13 weeks of cash in and out, the backlog still to earn, and retainage held both ways, each tied to the books.";
  // a point-in-time tab: the period bar does not apply
  "undefined" != typeof POINT_IN_TIME_TABS && !POINT_IN_TIME_TABS.includes("cash13") && POINT_IN_TIME_TABS.push("cash13");
} catch (e) {}
function rpInsertAfterHeading(host, rx, html) {
  const h = [...host.querySelectorAll("h3.rep-h, h3")].find((x) => rx.test(x.innerText.trim()));
  if (!h) return !1;
  return h.insertAdjacentHTML("beforebegin", html), !0;
}
const rpRenderReportsBase = renderReports;
renderReports = function () {
  const out = rpRenderReportsBase.apply(this, arguments);
  try {
    if ("reports" !== view) return out;
    const host = document.getElementById("rep-print-area");
    if (!host) return out;
    // Excel next to Print / PDF, on every tab
    const pr = document.getElementById("rep-print");
    pr && !document.getElementById("rep-xls") && pr.insertAdjacentHTML("afterend", `<button class="btn rp-xls" id="rep-xls" title="Every table on this report, one sheet each">${RP_ICON_XLS}Excel</button>`);
    const xb = document.getElementById("rep-xls");
    xb && (xb.onclick = rpExportExcel);
    const R = rpRange(),
      tab = repTab;
    if ("cash13" === tab) host.innerHTML = rpCashHtml();
    else if ("company" === tab) host.insertAdjacentHTML("beforeend", rpPLHtml(R) + rpJobBridgeHtml(R) + rpLateHtml(R) + rpTiesHtml(rpTies(R, ["pl", "months"]), { id: "pl", title: "P&L Ties" }));
    else if ("financials" === tab)
      host.insertAdjacentHTML(
        "beforeend",
        rpOverheadHtml(R) +
          rpTiesHtml(rpTies(R), { id: "all", title: "Report Ties", lead: "Every report figure, how it is made up, and whether the parts add up to it. Tap an amount for the records behind it and the bank or card line that backs each one." }) +
          rpChoicesHtml(),
      );
    else if ("pack" === tab) host.insertAdjacentHTML("beforeend", rpTiesHtml(rpTies(R), { id: "pack", title: "Report Ties", lead: "The month's reports, each tied to its records and the books." }));
    else if ("wip" === tab) host.insertAdjacentHTML("beforeend", rpTiesHtml(rpTies(R, ["wip"]), { id: "wip", title: "WIP Tie" }));
    else if ("ar" === tab) host.insertAdjacentHTML("beforeend", rpTiesHtml(rpTies(R, ["ar"]), { id: "ar", title: "Receivables Ties" }));
    else if ("payables" === tab) host.insertAdjacentHTML("beforeend", rpTiesHtml(rpTies(R, ["ap"]), { id: "ap", title: "Payables Ties" }));
    else if ("portfolio" === tab) {
      const S = rpPL(R);
      host.insertAdjacentHTML(
        "beforeend",
        `<div class="small rp-tieline" data-rptieline="portfolio">${S.ok ? `<span class="rp-ok">${RP_ICON_TIE} Ties</span>` : `<span class="rp-off">${RP_ICON_OFF} Off by ${rpCents(Math.abs(S.diff))}</span>`} The table above is each job to date, as the job sees its cost. The company P&amp;L for the period, ${rpCents(S.net)}, is split by project on <a href="#" data-rpgo="company">P&amp;L Detail</a>, with the reasons a job's cost reads differently there.</div>`,
      );
    } else if ("profit" === tab) {
      const p = rpProj(repProj);
      if (p) {
        // By Line becomes income to cost: the section under the "By line" heading is replaced, not repeated
        const h = [...host.querySelectorAll("h3.rep-h")].find((x) => /^by line$/i.test(x.innerText.trim()));
        if (h) {
          for (let n = h.nextElementSibling; n && !n.matches("h3.rep-h"); ) {
            const nx = n.nextElementSibling;
            n.remove(), (n = nx);
          }
          (h.textContent = "By Line: Income to Cost"), h.insertAdjacentHTML("afterend", rpLineHtml(p));
        } else host.insertAdjacentHTML("beforeend", `<h3 class="rep-h">By Line: Income to Cost</h3>` + rpLineHtml(p));
        host.insertAdjacentHTML("beforeend", rpCloseoutHtml(p) + rpTiesHtml(rpTies(null, ["jobcost"]).filter((t) => t.id === "job:" + p.id), { id: "job", title: "Job Cost Tie" }));
      }
    }
    host.querySelectorAll("[data-rpgo]").forEach(
      (a) =>
        (a.onclick = (e) => {
          e.preventDefault(), (repTab = a.dataset.rpgo), render();
        }),
    );
  } catch (e) {
    console.warn("reports lane", e);
  }
  return out;
};

// ---------------------------------------------------------------------------------------------------------------
// 8. Ask: the reports as tables (the model reads them) and one route for the questions the local parser missed
// ---------------------------------------------------------------------------------------------------------------
const RP_EQ = {
  pnlbyproject: () => {
    const S = rpPL(rpRange());
    return S.rows
      .map((r) => ({ _id: "pl:" + r.id, _module: "Reports", _label: `${rpProjName(r.id)} · P&L`, _go: { view: "reports", tab: "company" }, project: rpProjName(r.id), projectId: r.id, client: (rpClientOfProj(r.id) || {}).name || "", from: S.range[0], to: S.range[1], basis: S.basis, income: r.income, jobCost: r.cost, gross: r.gross, overhead: r.oh, net: r.net }))
      .concat(S.parts.filter((x) => "projects" !== x.id).map((x) => ({ _id: "pl:" + x.id, _module: "Reports", _label: x.label, _go: { view: "reports", tab: "company" }, project: x.label, projectId: "", client: "", from: S.range[0], to: S.range[1], basis: S.basis, income: 0, jobCost: 0, gross: 0, overhead: 0, net: x.amt })));
  },
  pnlbyclient: () => {
    const S = rpPLByClient(rpRange());
    return S.clients.map((r) => ({ _id: "plc:" + r.id, _module: "Reports", _label: `${r.name} · P&L`, _go: { view: "reports", tab: "company" }, client: r.name, projects: r.projects.map(rpProjName).join(", "), from: S.range[0], to: S.range[1], basis: S.basis, income: r.income, jobCost: r.cost, gross: r.gross, overhead: r.oh, net: r.net }));
  },
  reportties: () =>
    rpTies(rpRange()).map((t) => ({ _id: "tie:" + t.id, _module: "Reports", _label: t.title, _go: t.go || { view: "reports", tab: "financials" }, report: t.report, tie: t.title, figure: t.figure.label, amount: t.figure.amt, made_up_of: t.parts.map((x) => `${x.label} ${rpCents(x.amt)}`).join("; "), ties: t.ok, off_by: Math.abs(t.diff), flagged: !!t.manual })),
  cashforecast: () => {
    const F = cashForecast();
    return F.weeks.map((w, i) => ({ _id: "cf:" + w.start, _module: "Reports", _label: `Week of ${fmt(w.start)}`, _go: { view: "reports", tab: "cash13" }, week: i + 1, start: w.start, end: w.end, inflow: r2(w.inflow), outflow: r2(w.outflow), net: r2(w.net), balance: r2(w.balance), lowest: Math.abs(w.balance - F.low) < RP_EPS, items: w.items.map(([l, a]) => `${l} ${rpCents(a)}`).join("; ") }));
  },
  retainage: () => {
    const RP2 = "function" == typeof fin2RetainagePayable ? fin2RetainagePayable() : { rows: [] };
    return (DB.clients || [])
      .map((c) => ({ c: c, f: clientFin(c) }))
      .filter((x) => x.f.retHeld > RP_EPS)
      .map((x) => ({ _id: "rr:" + x.c.id, _module: "Reports", _label: `${x.c.name} · retainage held`, _go: { view: "reports", tab: "cash13" }, side: "receivable", party: x.c.name, amount: r2(x.f.retHeld) }))
      .concat((RP2.rows || []).map((x, i) => ({ _id: "rp:" + i, _module: "Reports", _label: `${rpRetWho(x)} · retainage held`, _go: { view: "reports", tab: "cash13" }, side: "payable", party: rpRetWho(x), amount: r2(rpRetAmt(x)) })));
  },
  overheadmonths: () => {
    const O = rpOverhead(rpRange());
    return O.months.map((m) => ({ _id: "oh:" + m.ym, _module: "Reports", _label: `Overhead · ${m.ym}`, _go: { view: "reports", tab: "financials" }, month: m.ym, overhead: m.ohT, revenue: m.income, pctOfRevenue: null == m.pct ? null : Math.round(m.pct), byCategory: Object.entries(m.lines).map(([k, v]) => `${k} ${rpCents(v)}`).join("; "), breakEvenMonthlyRevenue: O.breakEven }));
  },
  linecost: () =>
    (DB.projects || []).flatMap((p) =>
      rpLineRows(p).map((r) => ({ _id: "lc:" + r.key, _module: "Reports", _label: `${p.project.name} · ${r.name}`, _go: { view: "reports", tab: "profit", proj: p.id }, project: p.project.name, projectId: p.id, line: r.name, changeOrder: r.co, contract: r.contract, billed: r.billed, collected: r.collected, earned: r.earned, costToDate: r.actual, committed: r.committed, estimateAtCompletion: r.eac, marginToDate: r.marginToDate, marginAtCompletion: r.marginAtCompletion })),
    ),
};
const RP_EQ_ALIAS = { plbyproject: "pnlbyproject", projectpl: "pnlbyproject", plbyclient: "pnlbyclient", clientpl: "pnlbyclient", ties: "reportties", forecast: "cashforecast", cashflow13: "cashforecast", retainageheld: "retainage", overhead: "overheadmonths", lineincome: "linecost" };
try {
  Object.keys(RP_EQ).forEach((k) => {
    EQ_TABLES[k] || EQ_ALIAS[k] || (EQ_TABLES[k] = () => RP_EQ[k]());
    "undefined" != typeof EQ_MONEY_TABLES && !EQ_MONEY_TABLES.includes(k) && EQ_MONEY_TABLES.push(k);
    // read only by a role whose screens include Reports (eqViewOk in src/mind.js)
    "undefined" != typeof MD_VIEWS && (MD_VIEWS[k] = ["reports"]);
  });
  Object.entries(RP_EQ_ALIAS).forEach(([a, k]) => EQ_TABLES[a] || EQ_ALIAS[a] || (EQ_ALIAS[a] = k));
} catch (e) {
  console.warn("reports: Ask tables", e);
}
// The local Ask route: the questions the audit found answered with the wrong figure. Each answer is the number the
// report shows, from the same reader.
const RP_ASK = [
  {
    id: "plproject",
    rx: /\b(p ?& ?l|p and l|profit and loss|net profit|net income)\b.*\b(by|per|each|for every) (project|job)s?\b|\b(project|job)s?\b.*\bp ?& ?l\b/,
    answer: () => {
      const S = rpPL(rpRange());
      return {
        headline: `${rpCents(S.net)} company net ${rpRangeWords(S.range)} (${S.basis}): projects' net ${rpCents(S.parts[0].amt)}${S.parts.slice(1).map((x) => `, ${x.label.toLowerCase()} ${rpCents(x.amt)}`).join("")}. ${S.ok ? "It ties." : `It is off by ${rpCents(Math.abs(S.diff))}.`}`,
        work: S.rows.map((r) => `${rpProjName(r.id)} · income ${rpCents(r.income)} · job cost ${rpCents(r.cost)} · overhead ${rpCents(r.oh)} · net ${rpCents(r.net)}`),
        note: "The company P&L split by project: the same rows as Reports › P&L Detail › P&L by Project.",
        go: { view: "reports", tab: "company" },
        total: S.net,
      };
    },
  },
  {
    id: "plclient",
    rx: /\b(p ?& ?l|p and l|profit and loss|net profit|net income)\b.*\b(by|per|each|for every) (client|customer)s?\b|\b(client|customer)s?\b.*\bp ?& ?l\b/,
    answer: () => {
      const S = rpPLByClient(rpRange());
      return {
        headline: `Clients' net ${rpRangeWords(S.range)} (${S.basis}): ${S.clients.map((c) => `${c.name} ${rpCents(c.net)}`).join(", ")}; ${rpCents(S.clientNet)} in all.`,
        work: S.clients.map((c) => `${c.name} · income ${rpCents(c.income)} · job cost ${rpCents(c.cost)} · overhead ${rpCents(c.oh)} · net ${rpCents(c.net)}`),
        note: "Each client's projects, added: Reports › P&L Detail › P&L by Client. What sits on no project is not on any client.",
        go: { view: "reports", tab: "company" },
        total: S.clientNet,
      };
    },
  },
  {
    id: "breakeven",
    rx: /\bbreak[- ]?even\b/,
    answer: () => {
      const O = rpOverhead(rpRange());
      return {
        headline: null == O.breakEven ? "No break-even yet: the last full months had no gross margin to cover overhead." : `${rpCents(O.breakEven)} of revenue a month covers the overhead: ${rpCents(O.avgOH)} a month at a ${Math.round(100 * O.gm)}% gross margin.`,
        work: O.full.map((m) => `${m.ym} · overhead ${rpCents(m.ohT)} · revenue ${rpCents(m.income)} · gross ${rpCents(m.gross)}`),
        note: "Average monthly overhead over the last full months ÷ their gross margin, the figure on Reports › Statements › Overhead Analysis.",
        go: { view: "reports", tab: "financials" },
        total: O.breakEven,
      };
    },
  },
  {
    id: "cash13",
    rx: /\b(13|thirteen)[- ]?weeks?\b|\bcash (forecast|projection|low)\b|\blowest (projected )?cash\b/,
    answer: () => {
      const F = cashForecast(),
        w = F.weeks.reduce((a, x) => (x.balance < a.balance ? x : a), F.weeks[0]);
      return {
        headline: `The 13-week low is ${rpCents(F.low)} in the week of ${fmtL(w.start)}, from ${rpCents(F.cash)} today.`,
        work: F.weeks.map((x) => `Week of ${fmt(x.start)} · in ${rpCents(x.inflow)} · out ${rpCents(x.outflow)} · balance ${rpCents(x.balance)}`),
        note: "Open invoices at their due or promised dates in; bills not yet paid, open POs, payroll, recurring overhead and card balances out: Reports › Cash & Receivables › Cash Forecast.",
        go: { view: "reports", tab: "cash13" },
        total: F.low,
      };
    },
  },
  {
    id: "retainage",
    rx: /\bretainage\b|\bretention\b/,
    answer: (l) => {
      const B = companyBalance(),
        RP2 = "function" == typeof fin2RetainagePayable ? fin2RetainagePayable() : { total: 0, rows: [] },
        pay = /\b(payable|we hold|held from|subs?|vendors?|owe)\b/.test(l),
        recv = /\b(receivable|clients? (hold|held|owe)|held by|owed to us)\b/.test(l);
      return {
        headline:
          pay && !recv
            ? `${rpCents(RP2.total || 0)} of retainage payable: held from subs on their bills.`
            : recv && !pay
              ? `${rpCents(B.ret)} of retainage receivable: held by clients until release.`
              : `Retainage receivable ${rpCents(B.ret)} (held by clients); retainage payable ${rpCents(RP2.total || 0)} (held from subs).`,
        work: (DB.clients || []).map((c) => ({ c: c, f: clientFin(c) })).filter((x) => x.f.retHeld > RP_EPS).map((x) => `${x.c.name} holds ${rpCents(x.f.retHeld)}`).concat((RP2.rows || []).map((x) => `We hold ${rpCents(rpRetAmt(x))} from ${rpRetWho(x)}`)),
        note: "Both sides on Reports › Cash & Receivables › Cash Forecast, each tied to the ledger (1150 and 2050).",
        go: { view: "reports", tab: "cash13" },
        total: pay && !recv ? RP2.total || 0 : B.ret,
      };
    },
  },
  {
    id: "ties",
    rx: /\b(do|does|did) (the )?(reports?|books|numbers|p ?& ?l|wip|ar|receivables|payables) (tie|reconcile|add up|agree)\b|\breport ties\b|\bwhat does(n't| not) tie\b/,
    answer: () => {
      const T = rpTies(rpRange()).filter((t) => !t.manual),
        off = T.filter((t) => !t.ok);
      return {
        headline: off.length ? `${off.length} of ${T.length} report ties do not tie: ${off.map((t) => `${t.title} (off by ${rpCents(Math.abs(t.diff))})`).join("; ")}.` : `All ${T.length} report ties tie to the cent.`,
        work: T.map((t) => `${t.ok ? "Ties" : "Off by " + rpCents(Math.abs(t.diff))} · ${t.title} · ${t.figure.label} ${rpCents(t.figure.amt)}`),
        note: "Every tie on Reports › Statements › Report Ties.",
        go: { view: "reports", tab: "financials" },
        total: off.length,
      };
    },
  },
];
const rpRangeWords = (R) => `${fmtL(R[0] || "")} to ${fmtL(R[1] || today())}`;
function rpAskRoute(q) {
  let r = "";
  try {
    r = role();
  } catch (e) {}
  if (["client", "foreman", "crew", "driver"].includes(r)) return null;
  try {
    if (!(ROLE_VIEWS[r] || []).includes("reports")) return null;
  } catch (e) {}
  const l = String(q || "").toLowerCase().replace(/\s+/g, " ").trim(),
    it = RP_ASK.find((x) => x.rx.test(l));
  return it ? Object.assign(it.answer(l), { kind: "rp-" + it.id, routedBy: "reports" }) : null;
}
if ("function" == typeof paAsk) {
  const rpPaAskBase = paAsk;
  paAsk = function (q) {
    let a = null;
    try {
      a = rpAskRoute(q);
    } catch (e) {
      console.warn("reports ask", e), (a = null);
    }
    if (a) {
      try {
        paInit();
      } catch (e) {}
      return paOut(Object.assign({}, a, { go: a.go ? paGo(a.go) : null, offers: [] }));
    }
    return rpPaAskBase.apply(this, arguments);
  };
}
