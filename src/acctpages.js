/* =====================================================================================================================
   The Accounting pages (Alan, 11-03: docs/mockups/accounting/, SPEC.md). Accounting is where money is acted on; Reports
   is where it is read. Four pages, each a queue first ("Needs You"), then where things stand, then the records one tap
   down with chips. Firm-wide pages hold the same records as the job's own pages (Contract and Billing, Budget), across
   all jobs with a job filter; they are never a second home.

     Billing (billing)            billing's home: Needs You (what is ready to bill or drafted, and payments recorded but
                                  not in the bank), Collections (aging, retainage in its own bucket, the reminder at
                                  due, 7, 15 and 30 days), then the client's documents (estimates signed, change orders,
                                  invoices, payments) with a job filter
     Banking (bank)               the controller's home and the one queue for money in and out: To Review (the lines
                                  nothing explains: Spend, Today's Review, Controls' exceptions and Unassigned Cost fold
                                  in), Money In (recorded, not at the bank), Receipts, Matched; the accounts
     Bills and Payroll (ap, time) what the firm owes vendors and its own people: the payroll split checked before pay
                                  day, hours to approve, bills held, paid without a lien waiver; With Others; chips
     Books (gl, verify, budget)   the controller's: the close, the ledger, the controls, the operating budget, tax and
                                  1099. Not on the owner's menu (his sign-offs reach Today and Approvals); open by link

   Old pages forward or are hosted (SPEC §3): the Accounting overview (ovmoney) and Spend forward to Banking; Time and
   Crew is Bills and Payroll's Payroll chip; Controls and the operating Budget are Books' chips. A role that may open a
   hosted page but not its host (the coordinator's Time and Crew) keeps the page as it was.

   Design gate (BACKLOG §1.16): no new store, list or queue. The nouns extended: invoice/estimate/CO/payment (billing),
   bank and card line and receipt (bank), bill/time entry/payroll run (ap), journal and account (gl); the registry is
   ONE_PLACE in tests/ia_map.py (bankline: bank, journal: gl). Every figure is read from the functions every other screen
   reads (billingRows, readyToBill, billedAhead, toBill, clientFin, bankUnmatched, undepositedReceipts, apAging,
   closeChecklist, wipAtClose, analystFindings). Nothing here posts or changes money; every button opens the record or
   the existing action that does.
   ===================================================================================================================== */

const AC_PAGES = {
    billing: { name: "Billing", lead: "The client's documents for every job, what to bill next and what is still owed", badge: ["billing"] },
    bank: { name: "Banking", lead: "Every bank and card line, matched to the line it pays", badge: ["controller"] },
    ap: { name: "Bills and Payroll", lead: "What the firm owes vendors and its own people, from arrival to paid", badge: ["controller"] },
    gl: { name: "Books", lead: "The ledger, the month's close and the controls behind the numbers", badge: ["controller"] },
  },
  // old pages whose content folds into a new page's chip (the page is shown under the new page's name)
  AC_HOST = { time: "ap", verify: "gl", budget: "gl" },
  // old pages that are gone: they forward to the new page and its chip
  AC_FWD = { ovmoney: ["bank", "review"], spend: ["bank", "review"] };
let acChip = { billing: "all", bank: "review", ap: "approve", gl: "close" },
  acJob = "",
  acNewOpen = "",
  acJobOpen = !1;
const acMay = (v) => (ROLE_VIEWS[role()] || []).includes(v),
  acPhone = () => ("function" == typeof isMobile ? isMobile() : innerWidth <= 760),
  acIco = {
    plus: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
    down: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>',
  };
// the page the screen belongs to: the view's own, or the page that hosts it (when the role may open that page)
function acPageOf(v) {
  v = v || view;
  if (AC_PAGES[v]) return acMay(v) ? v : "";
  const h = AC_HOST[v];
  return h && acMay(h) ? h : "";
}
const acJobName = (pid) => {
  const p = (DB.projects || []).find((x) => x.id === pid);
  return p ? shortName(p) : "";
};
const acIn = (pid) => !acJob || pid === acJob;

// ---- Billing ---------------------------------------------------------------------------------------------------------
// Needs You: billingRows' rows that wait on billing (ready to bill, drafted and not sent), each with the existing next
// step (data-blact: Draft, Review), then each client's payments recorded and not in the bank (the chase). A job with
// lines billed ahead says so on its row, with the one billed-ahead figure (billedAhead) and what it holds (toBill).
function acBillNeeds(pid) {
  let rows = [];
  try {
    rows = billingRows() || [];
  } catch (e) {}
  const out = [];
  rows
    .filter((r) => r.needs)
    .forEach((r) => {
      const p = r.job || null;
      let why = r.what && r.kind !== "draft" ? `${r.what}.` : "",
        // one basis on every row: the work billed, before retainage (what Ready to Bill counts and what the application
        // bills); what the client pays after retainage is said beside it. The draft row printed its total after
        // retainage ($35,112) beside a ready row's work ($35,426): two bases for one question.
        amount = r.amount;
      if ("draft" === r.kind) {
        const T = r.inv ? docTotal(r.inv) : null;
        T && T.ret > 0.005 && (amount = r2(T.sub - T.disc + (T.tax || 0)));
        why = `${r.what}: written, not sent. The client has not seen it.${T && T.ret > 0.005 ? ` ${money(T.ret)} held as retainage; ${money(T.total)} due.` : ""}`;
      } else if (p) {
        // the row's own reason is the queue's (readyToBill: what the application bills and what it holds, with the one
        // billed-ahead figure); Needs You never composes a second sentence with its own figures. What else is held on
        // the job is toBill's held rows, named by their own reasons.
        const TB = toBill(p.id),
          extra = TB.heldRows.filter((h) => !(r.rtb && r.rtb.key && h.hid && h.hid.endsWith(r.rtb.key)));
        r.why && (why += ` ${r.why.charAt(0).toUpperCase() + r.why.slice(1)}.`);
        extra.length && TB.held > 0.005 && (why += ` Held with it: ${extra.map((h) => String(h.why || "").replace(/\.$/, "")).join("; ")}.`);
        // an application holds the contract's retainage: say what the client will pay on it
        if (r.rtb && "application" === r.rtb.kind && r.c) {
          const sov = (r.c.invoices || []).filter((i) => i.projectId === p.id && "sov" === i.mode && "void" !== i.status).pop(),
            est = (r.c.estimates || []).find((e) => e.projectId === p.id && ["converted", "approved"].includes(e.status)),
            pct = +((sov && sov.retainagePct) ?? (est && est.retainagePct) ?? 0) || 0;
          pct > 0 && (why += ` ${pct}% retainage holds ${money(r2((r.amount * pct) / 100))}; ${money(r2(r.amount - (r.amount * pct) / 100))} due.`);
        }
      }
      out.push({
        id: r.id,
        pid: p ? p.id : "",
        amount: amount,
        title: "draft" === r.kind ? `${money(amount)} drafted, not sent · ${p ? shortName(p) : r.client ? r.client.name : ""}` : `${money(r.amount)} ready to bill · ${p ? shortName(p) : r.client ? r.client.name : ""}`,
        why: why.trim(),
        act: blActLabel(r),
        blact: r.id,
        verb: "draft" === r.kind ? "Review the Draft" : "application" === (r.rtb || {}).kind ? "Draft the Application" : "Draft the Invoice",
      });
    });
  // the chase: recorded, not yet in the bank (one row per client), from the one reading every "collected" uses
  let U = [];
  try {
    U = undepositedReceipts();
  } catch (e) {}
  const byC = {};
  U.forEach((x) => (byC[x.c.id] = byC[x.c.id] || { c: x.c, L: [] }).L.push(x));
  Object.values(byC).forEach(({ c, L }) => {
    const inv = (x) => (c.invoices || []).find((i) => i.id === x.py.invoiceId),
      pids = [...new Set(L.map((x) => (inv(x) || {}).projectId).filter(Boolean))],
      amt = r2(L.reduce((a, x) => a + x.amt, 0));
    out.push({
      id: "undep:" + c.id,
      pid: pids[0] || "",
      pids: pids,
      amount: amt,
      title: `${money(amt)} recorded, not in the bank · ${c.name}`,
      why: `${L.map((x) => `${x.py.method || "Payment"} ${fmt(x.py.date)}${inv(x) ? ` on ${inv(x).number}` : ""}`).join(", ")}. Not collected until Banking finds them. Ask the client whether they were sent.`,
      act: "Open",
      undep: c.id,
      verb: "Open the Payments",
    });
  });
  return out.filter((x) => !pid || x.pid === pid || (x.pids || []).includes(pid));
}
// the reminder schedule (the Standard: collections at due, 7, 15 and 30 days)
function acNextReminder(due) {
  if (!due) return "";
  const td = today(),
    steps = [0, 7, 15, 30].map((d) => iso(addDays(parse(due), d)));
  const next = steps.find((d) => d >= td);
  return next ? `Reminder ${fmt(next)}` : "Past 30 days: call";
}
function acCollections(pid) {
  let A = [];
  try {
    A = arRows();
  } catch (e) {}
  A = A.filter((r) => !pid || (r.p && r.p.id === pid));
  const B = { current: 0, "1–30": 0, "31–60": 0, "60+": 0 };
  A.forEach((r) => (B[r.bucket] = r2((B[r.bucket] || 0) + r.bal)));
  const ret = r2(
    (DB.projects || [])
      .filter((p) => !pid || p.id === pid)
      .reduce((a, p) => {
        try {
          return a + (+jobFin(p).retHeld || 0);
        } catch (e) {
          return a;
        }
      }, 0),
  );
  return {
    aging: [
      ["Current", B.current],
      ["1 to 30 Days", B["1–30"]],
      ["31 to 60 Days", B["31–60"]],
      ["Over 60 Days", B["60+"]],
    ],
    open: r2(A.reduce((a, r) => a + r.bal, 0)),
    retainage: ret,
    rows: A.map((r) => ({
      c: r.c,
      i: r.i,
      p: r.p,
      bal: r.bal,
      age: r.age,
      who: `${r.c.name}${r.p ? " · " + shortName(r.p) : ""} · sent ${fmt(r.i.sentAt || r.i.date)}${r.contact && r.contact.date ? ` · last touch ${fmt(r.contact.date)}` : ""}`,
      next: r.promise && r.promise.date ? `Promised ${fmt(r.promise.date)}` : r.age > 0 ? `${r.age} day${1 === r.age ? "" : "s"} past due · ${acNextReminder(r.i.due)}` : acNextReminder(r.i.due),
    })),
  };
}
// the client's documents: the same records as each job's Contract and Billing, every job, filtered by job. Estimates
// still being priced or sent live in Sales and Clients, Estimates (the firm's one estimates list).
const AC_DOC_KINDS = [
  ["all", "All"],
  ["estimate", "Estimates"],
  ["co", "Change Orders"],
  ["invoice", "Invoices"],
  ["payment", "Payments"],
];
function acDocs(pid, kind) {
  const out = [];
  (DB.clients || []).forEach((c) => {
    const banked = (py) => ("function" == typeof payBankedAmt ? payBankedAmt(c, py) : +py.amount || 0);
    (c.estimates || [])
      .filter((d) => ["approved", "converted", "billed"].includes(d.status))
      .forEach((d) => out.push({ kind: "estimate", c: c, d: d, pid: d.projectId || "", no: d.number, what: d.title || "Estimate", amt: docTotal(d).total, date: d.approvedAt || d.date || "", status: "converted" === d.status ? "Converted" : "Signed", tone: "ok" }));
    (c.changeOrders || [])
      .filter((d) => !["draft", "void"].includes(d.status))
      .forEach((d) => out.push({ kind: "co", c: c, d: d, pid: d.projectId || "", no: d.number, what: d.title || "Change order", amt: docTotal(d).total, date: d.date || "", status: "sent" === d.status ? "Waiting on client" : "approved" === d.status ? "Approved" : "billed" === d.status ? "Billed" : d.status, tone: "sent" === d.status ? "warn" : "ok" }));
    (c.invoices || [])
      .filter((d) => "void" !== d.status)
      .forEach((d) => {
        const paidOn = (c.payments || []).filter((py) => py.invoiceId === d.id && !py.unapplied),
          rec = r2(paidOn.reduce((a, py) => a + (+py.amount || 0), 0)),
          bank = r2(paidOn.reduce((a, py) => a + banked(py), 0)),
          tot = docTotal(d).total,
          st = "draft" === d.status ? ["Draft, not sent", "warn"] : rec >= tot - 0.5 ? (bank >= rec - 0.5 ? ["Paid", "ok"] : ["Recorded, not in the bank", "bad"]) : d.due ? [d.due < today() ? `Past due ${fmt(d.due)}` : `Due ${fmt(d.due)}`, d.due < today() ? "bad" : "warn"] : ["Sent", "warn"];
        out.push({ kind: "invoice", c: c, d: d, pid: d.projectId || "", no: d.number, what: d.title || "Invoice", amt: tot, date: d.date || "", status: st[0], tone: st[1] });
      });
    (c.payments || [])
      .filter((py) => !py.unapplied && +py.amount > 0 && !py.reversalId)
      .forEach((py) => {
        const i = (c.invoices || []).find((x) => x.id === py.invoiceId),
          inBank = banked(py) >= (+py.amount || 0) - 0.005;
        out.push({ kind: "payment", c: c, d: i || null, py: py, pid: (i && i.projectId) || "", no: `${py.method || "Payment"}${py.ref ? " " + py.ref : ""} ${fmt(py.date)}`.trim(), what: i ? `Applied to ${i.number}` : "Not applied", amt: +py.amount || 0, date: py.date || "", status: inBank ? `In the bank ${fmt(py.date)}` : "Not in the bank", tone: inBank ? "ok" : "bad" });
      });
  });
  return out
    .filter((x) => (!pid || x.pid === pid) && ("all" === (kind || "all") || x.kind === kind))
    .sort((a, b) => String(b.date).localeCompare(String(a.date)));
}

// ---- Banking ---------------------------------------------------------------------------------------------------------
// To Review is the one money-in-and-out queue: bankUnmatched (the same 15 the ledger, Spend and the Chief of Staff
// counted), its money at stake (credits counted as dollars, hence "at stake", not "out"), its oldest line, and what of
// it blocks the month's close.
function acBankReview() {
  let U = { rows: [], n: 0, amt: 0, oldest: null };
  try {
    U = bankUnmatched();
  } catch (e) {}
  const ym = "function" == typeof fin2CloseYm ? fin2CloseYm() : null,
    inM = ym ? U.rows.filter((t) => String(t.date).slice(0, 7) <= ym) : [],
    typed = U.rows.filter((t) => "function" == typeof bfBacked && !bfBacked(t));
  return {
    n: U.n,
    amt: U.amt,
    rows: U.rows,
    oldest: U.oldest,
    days: U.oldest ? dayDiff(U.oldest.date, today()) : 0,
    ym: ym,
    close: { n: inM.length, amt: r2(inM.reduce((a, t) => a + Math.abs(+t.amt || 0), 0)) },
    typed: typed.length,
  };
}
function acMoneyIn() {
  let U = [];
  try {
    U = undepositedReceipts();
  } catch (e) {}
  return U.map((x) => {
    const i = (x.c.invoices || []).find((v) => v.id === x.py.invoiceId);
    return { c: x.c, py: x.py, i: i, amt: x.amt, pid: (i && i.projectId) || "" };
  });
}
function acReceipts() {
  const L = "function" == typeof spAll ? spAll() : DB.spend || [];
  return L.filter((s) => "submitted" === s.status).map((s) => ({ s: s, amt: "function" == typeof spTotal ? spTotal(s) : 0, pid: s.projectId || "" }));
}
function acAccounts() {
  return (DB.accounts || []).map((a) => {
    const recs = ((DB.bankRecons || []).filter((r) => r.acct === a.id || r.acctId === a.id) || []).map((r) => r.to || r.end || r.through || "").filter(Boolean).sort(),
      imps = ((DB.bankImports || []).filter((r) => r.acct === a.id || r.acctId === a.id) || []).map((r) => r.to || r.end || r.through || "").filter(Boolean).sort();
    return {
      a: a,
      bal: "bank" === a.type && "function" == typeof acctBook ? acctBook(a) : +a.balance || 0,
      stmt: imps[imps.length - 1] || "",
      rec: recs[recs.length - 1] || a.reconciledThrough || "",
    };
  });
}

// ---- Bills and Payroll -----------------------------------------------------------------------------------------------
function acApNeeds() {
  const out = [],
    td = today();
  // payroll runs past or near pay day that are not on jobs yet: split them first, then Alan approves
  (DB.payroll || [])
    .filter((r) => r.total && ["draft", "submitted", "pm-approved"].includes(r.status))
    .forEach((r) => {
      const un = r2((r.alloc || []).filter((x) => x.unallocated && !x.projectId).reduce((a, x) => a + (+x.pct || 0), 0)),
        late = r.payDate && r.payDate < td ? dayDiff(r.payDate, td) : 0,
        jobs = (r.alloc || []).filter((x) => x.projectId).map((x) => `${acJobName(x.projectId)} ${x.pct}%`);
      out.push({
        id: "pay:" + r.id,
        kind: "payroll",
        approve: !0,
        title: `Payroll ${r.period || ""} · ${money(r.total)}${late ? ` · ${late} day${1 === late ? "" : "s"} past pay day` : r.payDate ? ` · pay day ${fmt(r.payDate)}` : ""}`,
        why: `${r.employees ? r.employees + " employees. " : ""}${un ? `${Math.round(un)}% sits on Unallocated Labor${jobs.length ? `, ${jobs.join(", ")}` : ""}. Split it by job; then it goes to Alan to approve.` : "On its jobs; it goes to Alan to approve."}`,
        open: () => openPayroll(r.id),
        verb: un ? "Split the Payroll by Job" : "Open the Payroll",
        split: !!un,
      });
    });
  // hours to approve (payroll waits on them)
  const T = (DB.time || []).filter((e) => "submitted" === e.status);
  if (T.length) {
    const hrs = r2(T.reduce((a, e) => a + ("function" == typeof hoursOf ? hoursOf(e) : 0), 0)),
      fl = T.filter((e) => "function" == typeof timeFlags && timeFlags(e).length);
    out.push({
      id: "time",
      kind: "time",
      approve: !0,
      title: `${T.length} time entr${1 === T.length ? "y" : "ies"} to approve · ${hrs.toFixed(1)} h`,
      why: fl.length ? `${fl.length} flagged: ${fl.slice(0, 3).map((e) => `${((DB.employees || []).find((x) => x.id === e.empId) || {}).name || "someone"}: ${timeFlags(e)[0]}`).join("; ")}.` : "Payroll waits on them.",
      open: () => ((acChip.ap = "payroll"), setView("time")),
      verb: "Review the Hours",
    });
  }
  // a bill an earlier bank line may already have paid: held, not owed, until a person decides
  let B = {};
  try {
    B = companyBalance();
  } catch (e) {}
  (B.possiblyPaid || []).forEach((b) => {
    const t = "function" == typeof billEarlyTxn ? billEarlyTxn(b) : null;
    out.push({
      id: "maybe:" + b.id,
      kind: "held",
      approve: !0,
      title: `${b.number || "Bill"} · ${b.vendor} · ${money(billTotal(b))} held`,
      why: t ? `${t.desc || "A bank line"} for ${money(Math.abs(t.amt))} cleared ${fmt(t.date)}, before the bill's date. Confirm it paid this bill, or that it paid something else.` : "Possibly already paid by an earlier bank line.",
      open: () => openBill(b.id),
      verb: "Open the Bill",
    });
  });
  // a sub paid with no unconditional lien waiver on file
  let L = [];
  try {
    L = "function" == typeof scLedgerRows ? scLedgerRows() : [];
  } catch (e) {}
  L.forEach((x) =>
    (x.waiversMissing || []).forEach((b) =>
      out.push({
        id: "waiver:" + b.id,
        kind: "waiver",
        title: `${b.number || "Bill"} · ${b.vendor} · ${money(billTotal(b))} paid${b.paidAt ? " " + fmt(b.paidAt) : ""}`,
        why: "No unconditional lien waiver on file. Record it before the next payment to this sub.",
        open: () => openBill(b.id),
        verb: "Open the Bill",
      }),
    ),
  );
  return out;
}
// what waits on someone else (the owner's approvals): shown, never counted as the controller's
function acApOthers() {
  return ("function" == typeof billsPaidUnapproved ? billsPaidUnapproved() : []).map((b) => {
    const po = b.poId && (DB.pos || []).find((x) => x.id === b.poId),
      t = "function" == typeof billPaidTxn ? billPaidTxn(b) : null,
      over = po ? r2(billTotal(b) - poTotal(po).total) : 0;
    return {
      b: b,
      title: `${b.number || "Bill"} · ${b.vendor}`,
      amt: billTotal(b),
      why: `With Alan. Paid${t ? ` ${fmt(t.date)}` : ""} before approval${po ? `; ${po.number} covers ${money(poTotal(po).total)}${over > 0.5 ? `, ${money(over)} over` : ""}` : ""}.`,
    };
  });
}

// ---- Books -------------------------------------------------------------------------------------------------------------
function acBooksNeeds() {
  const out = [],
    ym = "function" == typeof fin2CloseYm ? fin2CloseYm() : null;
  if (ym) {
    let items = [];
    try {
      items = closeChecklist(ym);
    } catch (e) {}
    const open = items.filter((i) => !i.ok),
      R = acBankReview();
    out.push({
      id: "close",
      title: `Close ${fin3Label(ym)}: ${open.length} of ${items.length} checks open`,
      why: `${R.close.n ? `${R.close.n} bank line${1 === R.close.n ? "" : "s"} not matched (${money(R.close.amt)}). ` : ""}${open
        .filter((i) => !/bank items? not yet matched/i.test(i.label || i.title || ""))
        .slice(0, 3)
        .map((i) => String(i.label || i.title || "").replace(/\s+$/, ""))
        .join("; ")}. Books by the 10th.`,
      go: "close",
      verb: `Continue the ${fin3Label(ym).split(" ")[0]} Close`,
    });
  }
  let F = [];
  try {
    F = analystFindings().filter((f) => "Controller" === f.area);
  } catch (e) {}
  const strip = (h) => String(h || "").replace(/<[^>]+>/g, "").trim();
  F.filter((f) => /booked as the first draw/i.test(f.title)).forEach((f) => out.push({ id: "dep:" + f.title, title: strip(f.title), why: strip(f.detail), go: f.go, verb: "Open" }));
  const gap = F.filter((f) => /Over-Billed \(WIP\).*against Billed Ahead of the Work/.test(f.title));
  gap.length &&
    out.push({
      id: "wipgap",
      title: "Over-Billed (WIP) against Billed Ahead of the Work",
      why: `${gap.map((f) => strip(f.title).replace(/^([^:]+): Over-Billed \(WIP\) (\$[\d,]+) against Billed Ahead of the Work (\$[\d,]+), (\$[\d,]+) apart$/, "$1 $2 against $3, $4 apart")).join("; ")}. Reconcile before the close.`,
      go: { view: "reports", tab: "wip" },
      verb: "Open the WIP Schedule",
    });
  let SP = [];
  try {
    SP = "function" == typeof rpShortPaid ? rpShortPaid() : [];
  } catch (e) {}
  SP.forEach((x) => out.push({ id: "short:" + x.d.id, title: `${x.d.number} short-paid by ${money(x.bal)}`, why: `${x.c.name}: ${money(x.total)} billed, ${money(x.paid)} paid. Collect it or write it off with a reason.`, go: { view: "clients", client: x.c.id }, verb: "Open" }));
  return out;
}
// Tax and 1099: the register by payee from the payments themselves (the 2026 $2,000 threshold), W-9s on file
function acTax() {
  const by = {};
  (DB.bills || [])
    .filter((b) => ["paid", "verified"].includes(b.status) && String(b.paidAt || b.date || "").slice(0, 4) === today().slice(0, 4))
    .forEach((b) => {
      const k = b.vendor || "";
      k && ((by[k] = by[k] || { name: k, amt: 0 }).amt = r2(by[k].amt + billTotal(b)));
    });
  const rows = Object.values(by)
    .filter((x) => x.amt >= 2e3)
    .map((x) => Object.assign(x, { v: (DB.vendors || []).find((v) => v.name === x.name) }))
    .sort((a, b) => b.amt - a.amt);
  return { rows: rows, noW9: rows.filter((x) => !(x.v && x.v.w9)) };
}

// ---- the counts: one per page, the rows it names --------------------------------------------------------------------
function acCount(pg) {
  try {
    if ("billing" === pg) return acBillNeeds(acJob).length;
    if ("bank" === pg) return acBankReview().n;
    if ("ap" === pg) return acApNeeds().length;
    if ("gl" === pg) return acBooksNeeds().length;
  } catch (e) {}
  return 0;
}
// the one billing count every surface reads (the menu, Today, Ask): Billing's Needs You, all jobs
billingNeeds = function () {
  try {
    return acBillNeeds("").length;
  } catch (e) {
    return 0;
  }
};

// ---- drawing -----------------------------------------------------------------------------------------------------------
const acTone = (t) => (t ? ` ac-${t}` : "");
function acRowHtml(o) {
  // one row: what (bold), its line under it, the amount and status on the right, the row's one action
  return `<tr class="ac-row${acTone(o.tone)}"${o.edit ? ` data-edit="${esc(o.edit)}"` : ""}${o.open ? ` data-acopen="${esc(o.open)}"` : ""} tabindex="0"><td class="ac-what"><b>${esc(o.title)}</b>${o.sub ? `<span class="ac-sub">${o.sub}</span>` : ""}</td>${o.amt != null || o.status ? `<td class="ac-amt">${o.amt != null ? `<b>${esc(o.amt)}</b>` : ""}${o.status ? `<span class="ac-st${acTone(o.tone)}">${esc(o.status)}</span>` : ""}</td>` : ""}${o.btn ? `<td class="ac-act">${o.btn}</td>` : ""}</tr>`;
}
const acTable = (rows, empty) => (rows.length ? `<table class="ac-rows"><tbody>${rows.join("")}</tbody></table>` : `<p class="ac-empty small muted">${esc(empty || "Nothing here.")}</p>`);
function acChipsHtml(pg, list) {
  return `<div class="ac-chips" role="tablist" aria-label="${esc(AC_PAGES[pg].name)}">${list.map(([k, l, n]) => `<button type="button" role="tab" class="ac-chip${acChip[pg] === k ? " on" : ""}" aria-selected="${acChip[pg] === k}" data-acchip="${pg}:${k}">${esc(l)}${n ? ` <b class="n">${n}</b>` : ""}</button>`).join("")}</div>`;
}
function acNeedsHtml(pg, rows, go, noCount) {
  return `<section class="card ac-needs" aria-label="Needs You"><div class="ac-cap">Needs You${noCount ? "" : ` <b data-ocbadge="${pg}" data-occount="${pg}">${rows.length}</b>`}</div>${acTable(rows.map(acRowHtml), "Nothing waits on you here.")}${go ? `<div class="ac-go">${go}</div>` : ""}</section>`;
}
const AC_NEW = {
  billing: [
    ["app", "Progress Application"],
    ["dep", "Deposit Invoice"],
    ["inv", "Invoice"],
    ["co", "Change Order"],
  ],
  bank: [
    ["import", "Import a Statement", "QFX, OFX or CSV from the bank"],
    ["connect", "Connect a Bank", "A live feed for an account"],
    ["rule", "Bank Rule", "Code lines like this one from now on"],
    ["receipt", "Receipt", "A photo of a receipt, tied to its job and line"],
    ["typed", "Typed Line", "Not from the bank: flagged until a bank line backs it"],
  ],
  ap: [
    ["bill", "Vendor Bill"],
    ["payroll", "Payroll Run"],
    ["time", "Time Entry"],
  ],
  gl: [["je", "Journal Entry", "Drafted by the controller, posted by Alan"]],
};
function acHeadHtml(pg) {
  const P = AC_PAGES[pg],
    jobs = (DB.projects || []).filter((p) => (DB.clients || []).some((c) => c.id === p.clientId && ((c.invoices || []).some((i) => i.projectId === p.id) || (c.estimates || []).some((e) => e.projectId === p.id)))),
    jobBtn =
      "billing" === pg
        ? `<button type="button" class="btn ac-jobbtn" data-acjob aria-expanded="${acJobOpen}" aria-haspopup="listbox" aria-label="Job: ${esc(acJob ? acJobName(acJob) : "All Jobs")}">${esc(acJob ? acJobName(acJob) : "All Jobs")}${acIco.down}</button>`
        : "",
    jobMenu = "billing" === pg && acJobOpen ? `<div class="ac-menu" role="listbox" aria-label="Job">${[["", "All Jobs"]].concat(jobs.map((p) => [p.id, shortName(p)])).map(([id, l]) => `<button type="button" role="option" aria-selected="${acJob === id}" class="ac-mi${acJob === id ? " on" : ""}" data-acjobpick="${esc(id)}">${esc(l)}</button>`).join("")}</div>` : "",
    newMenu =
      acNewOpen === pg
        ? `<div class="ac-menu" role="menu">${"billing" === pg ? `<span class="ac-mh small muted">New for ${esc(acJob ? acJobName(acJob) : "which job? (asked next)")}</span>` : ""}${(AC_NEW[pg] || []).map(([k, l, s]) => `<button type="button" role="menuitem" class="ac-mi" data-acnewpick="${pg}:${k}"><b>${esc(l)}</b>${s ? `<span class="small muted">${esc(s)}</span>` : ""}</button>`).join("")}</div>`
        : "";
  return `<div class="ac-top"><h2>${esc(P.name)}</h2><span class="grow"></span>${jobBtn}<button type="button" class="btn ac-newbtn" data-acnew="${pg}" aria-expanded="${acNewOpen === pg}" aria-haspopup="menu" aria-label="New in ${esc(P.name)}">${acIco.plus}<span>New</span></button></div><p class="lead ac-lead">${esc(P.lead)}</p>${newMenu}${jobMenu}`;
}

// Billing
function acBillingHtml() {
  const N = acBillNeeds(acJob),
    top = N.find((x) => x.blact),
    go = top ? `<button type="button" class="btn primary" data-blact="${esc(top.blact)}">${esc(top.verb)}, ${money(top.amount)}</button>` : N[0] ? `<button type="button" class="btn primary" data-acundep="${esc(N[0].undep)}">${esc(N[0].verb)}</button>` : "",
    C = acCollections(acJob),
    D = acDocs(acJob, acChip.billing),
    rows = N.map((x) => ({ title: x.title, sub: esc(x.why), btn: x.blact ? `<button type="button" class="btn sm" data-blact="${esc(x.blact)}">${esc(x.act)}</button>` : `<button type="button" class="btn sm" data-acundep="${esc(x.undep)}">Open</button>`, edit: x.blact ? "bl:" + x.blact : "" }));
  return `${acNeedsHtml("billing", rows, go)}
  <section class="card ac-stand" aria-label="Collections"><div class="ac-cap">Collections <span class="small muted">Reminders at due, 7, 15 and 30 days</span></div>
    <div class="ac-aging">${C.aging.map(([k, v]) => `<div class="ac-age${k !== "Current" && v ? " bad" : ""}"><span>${esc(k)}</span><b>${money(v)}</b></div>`).join("")}</div>
    <p class="small ac-ret">Retainage held by clients <b>${money(C.retainage)}</b>, in its own bucket until release.</p>
    ${acTable(C.rows.map((r) => acRowHtml({ title: r.i.number, sub: esc(r.who), amt: money(r.bal), status: r.next, tone: r.age > 0 ? "bad" : "", open: `invoice:${r.c.id}:${r.i.id}` })), "Nothing owed.")}</section>
  ${acChipsHtml("billing", AC_DOC_KINDS.map(([k, l]) => [k, l, ""]))}
  <section class="ac-list" aria-label="Documents">${acTable(D.map((d) => acRowHtml({ title: d.no || "", sub: `${esc(d.pid ? acJobName(d.pid) : d.c.name)} · ${esc(d.what)}`, amt: money(d.amt), status: d.status, tone: d.tone, open: d.d ? `${"payment" === d.kind ? "invoice" : d.kind}:${d.c.id}:${d.d.id}` : "" })), "Nothing of this kind on this job.")}
    <p class="small ac-foot"><a href="#" data-acgo="billing:estimates">Estimates still being priced or sent are in Sales and Clients, Estimates</a></p></section>`;
}

// Banking
function acBankHtml() {
  const R = acBankReview(),
    lines = [
      `${money(R.amt)} at stake${R.oldest ? ` · oldest ${R.days} day${1 === R.days ? "" : "s"}, since ${fmt(R.oldest.date)}` : ""}`,
      R.ym && R.close.n ? `${fin3Label(R.ym).split(" ")[0]} closes only when its ${R.close.n} line${1 === R.close.n ? "" : "s"}, ${money(R.close.amt)}, are matched to a line or carry a signed exception.` : "",
      R.typed ? `${R.typed} line${1 === R.typed ? " is" : "s are"} typed by hand and not yet at the bank.` : "",
    ].filter(Boolean),
    needs = R.n ? [{ title: `${R.n} line${1 === R.n ? "" : "s"} to match`, sub: lines.map(esc).join("<br>") }] : [],
    go = R.n ? `<button type="button" class="btn primary" data-acchip="bank:review" data-acscroll>Start the Review, ${R.n} Line${1 === R.n ? "" : "s"}</button>` : "",
    MI = acMoneyIn(),
    RC = acReceipts(),
    A = acAccounts();
  let body = "";
  "money" === acChip.bank &&
    (body = `<p class="small muted ac-chiplead">Client payments recorded in Billing that the bank has not shown. They are not collected and not cash until a bank line backs them. Billing chases them from its Needs You; they match here when a statement shows them.</p>${acTable(MI.map((x) => acRowHtml({ title: `${x.c.name} · ${x.py.method || "Payment"}${x.i ? ", " + x.i.number : ""}`, sub: `${fmt(x.py.date)}${x.i ? ` · recorded against ${esc(x.i.number)}` : ""} · Recorded, not in the bank. Find it on a bank statement, or mark it bounced.`, amt: money(x.amt), tone: "bad", open: x.i ? `invoice:${x.c.id}:${x.i.id}` : "" })), "Every recorded payment is in the bank.")}`);
  "receipts" === acChip.bank &&
    (body = `<p class="small muted ac-chiplead">Captured at the counter. The job's PM approves them on his Approvals, never the person who bought. Approving makes them payable and billable.</p>${acTable(RC.map((x) => acRowHtml({ title: `${x.s.vendor || "Receipt"}${x.s.by ? " · " + x.s.by : ""}`, sub: `${fmt(x.s.date)}${x.pid ? " · " + esc(acJobName(x.pid)) : ""}${x.s.note ? " · " + esc(x.s.note) : ""}${x.s.reimburse ? " · paid himself: approving it adds a reimbursement" : ""}`, amt: money(x.amt), status: "With the PM", open: "spend:" + x.s.id })), "No receipt waits on anyone.")}`);
  return `${acNeedsHtml("bank", needs, go, !0)}
  ${acChipsHtml("bank", [
    ["review", "To Review", R.n],
    ["money", "Money In", ""],
    ["receipts", "Receipts", ""],
    ["matched", "Matched", ""],
  ])}
  ${body ? `<section class="ac-list">${body}</section>` : `<p class="small muted ac-chiplead">${"review" === acChip.bank ? `${R.n} line${1 === R.n ? "" : "s"} no bill, order, invoice, receipt or payroll line explains yet. Tap a line to see what it would link to before you confirm.` : "Every line already tied to the line it pays."}</p>`}
  <section class="card ac-accts" aria-label="Accounts"><div class="ac-cap">Accounts</div>${acTable(A.map((x) => acRowHtml({ title: `${x.a.name}${x.a.last4 ? " ····" + x.a.last4 : ""}`, sub: `${x.stmt ? `Statement through ${fmt(x.stmt)}` : "No statement imported"} · ${x.rec ? `reconciled through ${fmt(x.rec)}` : "never reconciled"}`, amt: money(x.bal), tone: x.rec ? "" : "warn", open: "acct:" + x.a.id, btn: `<button type="button" class="btn sm" data-acrecon="${esc(x.a.id)}">Reconcile</button>` })))}</section>`;
}

// Bills and Payroll
function acApHtml() {
  const N = acApNeeds(),
    W = acApOthers(),
    split = N.find((x) => x.split),
    go = split ? `<button type="button" class="btn primary" data-acneed="${esc(split.id)}">${esc(split.verb)}</button>` : N[0] ? `<button type="button" class="btn primary" data-acneed="${esc(N[0].id)}">${esc(N[0].verb)}</button>` : "";
  return `${acNeedsHtml("ap", N.map((x) => ({ title: x.title, sub: esc(x.why), tone: x.split ? "bad" : "", btn: `<button type="button" class="btn sm" data-acneed="${esc(x.id)}">${x.split ? "Split" : "Open"}</button>` })), go)}
  ${W.length ? `<section class="card ac-stand" aria-label="With Others"><div class="ac-cap">With Others</div>${acTable(W.map((x) => acRowHtml({ title: x.title, sub: esc(x.why), amt: money(x.amt), open: "bill:" + x.b.id, btn: `<button type="button" class="btn sm" data-acopenbtn="bill:${esc(x.b.id)}">Review</button>` })))}</section>` : ""}
  ${acChipsHtml("ap", [
    ["approve", "To Approve", ""],
    ["pay", "To Pay", ""],
    ["paid", "Paid", ""],
    ["payroll", "Payroll", ""],
  ])}
  <p class="small muted ac-chiplead">${{ approve: "Bills and payroll runs waiting on a yes. A PM recommends each bill and the owner approves it, and the owner approves the payroll run the controller builds. Whoever entered an item cannot approve it.", pay: "Approved and unpaid, by due date. The Payment Run is built from here; the bank pays it.", paid: "Each payment names its bill, its account and the bank line that cleared it.", payroll: "Hours become payroll and labor cost on each job. The split is checked before pay day." }[acChip.ap] || ""}</p>`;
}

// Books
const AC_GL_CHIPS = [
  ["close", "Close"],
  ["ledger", "Ledger"],
  ["controls", "Controls"],
  ["budget", "Operating Budget"],
  ["tax", "Tax and 1099"],
];
function acBooksHtml() {
  const N = acBooksNeeds(),
    first = N[0],
    go = first ? `<button type="button" class="btn primary" data-acbook="${esc(first.id)}">${esc(first.verb)}</button>` : "";
  let body = "";
  if ("close" === acChip.gl) {
    const W = "function" == typeof wipAtClose ? wipAtClose() : null;
    W &&
      (body = `<section class="card ac-stand" aria-label="Posts at the close"><div class="ac-cap">Posts at the ${esc(W.label)} close</div>${acTable([
        acRowHtml({ title: "WIP adjustment", sub: `The WIP schedule at ${fmt(W.end)}, job by job, to 2500 and 1200: ${W.rows.filter((r) => Math.abs(r.toPost) >= 0.005).map((r) => `${esc(shortName(r.p))} ${money(r.toPost)}`).join(", ") || "nothing to post"}. One figure with Job Profitability.`, amt: money(W.toPost) }),
      ])}</section>`);
  }
  if ("tax" === acChip.gl) {
    const T = acTax();
    body = `<p class="small muted ac-chiplead">Year-end and filings: the 1099 register (payees at $2,000 or more in ${today().slice(0, 4)}) and the W-9s on file.</p><section class="ac-list">${acTable(T.rows.map((x) => acRowHtml({ title: x.name, sub: x.v && x.v.w9 ? "W-9 on file" : "No W-9 on file: request it before year end", amt: money(x.amt), tone: x.v && x.v.w9 ? "" : "warn" })), "No payee at $2,000 or more this year.")}</section>`;
  }
  return `${acNeedsHtml("gl", N.map((x) => ({ title: x.title, sub: esc(x.why), btn: `<button type="button" class="btn sm" data-acbook="${esc(x.id)}">Open</button>` })), go)}
  ${acChipsHtml("gl", AC_GL_CHIPS.map(([k, l]) => [k, l, ""]))}${body}`;
}

// ---- mounting on the page --------------------------------------------------------------------------------------------
// The page's own heading, tiles and filter strip give way to the front (they carried counts the front now states once);
// the records below stay, under the chip that shows them.
// A hosted page keeps its own tools (Build Payroll from Approved Time, Run Verification) as plain buttons: the front's is
// the one blue.
const AC_HIDE = {
    // the old tiles and cards that stated the same counts the front states once (To Review 15, Not Matched 15, Paid
    // Before Approval beside With Others, Journals to Approve, the second "Books" heading)
    bank: ["#v-bank > .ph", "#bank-accts", "#txn-filter", "#tl-bank", "#tr-unm"],
    ap: ["#v-ap > .ph", "#ap-kpis", "#ap-filter", "#fin-pbu"],
    time: ["#v-time > .ph > div:first-child", "#time-kpis"],
    gl: ["#v-gl > .glance", "#gl-body > .ph"],
    verify: ["#v-verify > .ph > div:first-child", "#vf-kpis"],
    budget: ["#budget-body > .ph"],
  },
  AC_PLAIN = { bank: "#v-bank #txn-props .btn.primary, #v-bank #txn-table .btn.primary", time: "#v-time > .ph .btn.primary", verify: "#v-verify > .ph .btn.primary", budget: "#v-budget .btn.primary:not(.ac-front .btn)", gl: "#v-gl .btn.primary:not(.ac-front .btn)" };
function acMount() {
  const pg = acPageOf();
  document.querySelectorAll(".view .ac-front").forEach((f) => !f.closest(".view.on") && (f.closest(".view").classList.remove("ac-host"), f.remove()));
  if (!pg) return;
  const sec = document.querySelector(`#v-${view}`);
  if (!sec || !sec.classList.contains("on")) return;
  if ("billing" === pg && (("undefined" != typeof docOpen && docOpen) || "billable" !== billTab)) {
    sec.querySelector(":scope > .ac-front")?.remove(), sec.classList.remove("ac-host");
    return;
  }
  // the chip follows the page on screen (a hosted page is its chip)
  "time" === view && (acChip.ap = "payroll"),
    "verify" === view && (acChip.gl = "controls"),
    "budget" === view && (acChip.gl = "budget"),
    "gl" === view && ["controls", "budget"].includes(acChip.gl) && (acChip.gl = "periods" === glTab ? "close" : "ledger"),
    "ap" === view && "payroll" === acChip.ap && (acChip.ap = "approve");
  const inner = { billing: acBillingHtml, bank: acBankHtml, ap: acApHtml, gl: acBooksHtml }[pg];
  let html = "";
  try {
    html = `<div class="ac-front" data-acpage="${pg}">${acHeadHtml(pg)}${inner()}</div>`;
  } catch (e) {
    return void console.warn("accounting page", e);
  }
  sec.classList.add("ac-host");
  sec.querySelector(":scope > .ac-front")?.remove();
  sec.insertAdjacentHTML("afterbegin", html);
  (AC_HIDE[view] || []).forEach((s) => document.querySelectorAll(s).forEach((e) => (e.hidden = !0)));
  sec.querySelector(".ac-front .btn.primary") && AC_PLAIN[view] && document.querySelectorAll(AC_PLAIN[view]).forEach((b) => b.classList.remove("primary"));
  // the page's body under the chips: what each chip shows of the records below
  if ("billing" === pg) {
    const B = sec.querySelector("#billing-body");
    B && [...B.children].forEach((c) => c.matches(".bl-ph, .ctabs, #bl-tiles, #bl-list, .ov-tiles, .bl-tiles") && (c.hidden = !0));
  }
  if ("bank" === pg) {
    const show = ["review", "matched"].includes(acChip.bank);
    [...sec.children].forEach((c) => {
      c.classList.contains("ac-front") || c.matches(".ph, #bank-accts") || (c.hidden = !show);
    });
  }
  if ("gl" === pg && "gl" === view) {
    const B = sec.querySelector("#gl-body");
    B && (B.hidden = "tax" === acChip.gl);
  }
  "bank" === pg && acPhone() && acSheetOnly(sec);
}
// On the phone a bank line is never confirmed from the list (SPEC §2 Banking, 9: "no Confirm on a list row; the line's
// sheet names the target and the warning first", the experts' S1: a phone Confirm that hid what it linked to). Each row's
// Confirm gives way to Review, which opens the line's sheet: the warning, what it would link to, the line, then Confirm.
// Confirm in the sheet presses the row's own Confirm, so the match, its reason sheet and its toast are the existing ones.
function acSheetOnly(sec) {
  // To Review's count is its rows: on the phone the list sits right under the chips (it was some 3,500px down, under
  // the coverage, import and suggestion cards), each row names the line and its amount in full, and a tap opens the
  // line's review sheet, never the edit form
  if (["review", "matched"].includes(acChip.bank)) {
    const F = sec.querySelector(":scope > .ac-front"),
      T = sec.querySelector("#txn-table");
    if (F && T && F.nextElementSibling !== T) {
      F.after(T);
      [sec.querySelector(":scope > .prop-card"), sec.querySelector("#pay3-needs")].filter(Boolean).reverse().forEach((c) => T.after(c));
    }
    // the accounts are where things stand: under the lines on the phone
    const AC = F && F.querySelector(".ac-accts"),
      last = sec.querySelector("#pay3-needs") || sec.querySelector(":scope > .prop-card") || T;
    AC && last && (sec.querySelectorAll(":scope > .ac-accts").forEach((x) => x.remove()), last.after(AC));
    sec.querySelectorAll("#txn-table tr.pr-tr").forEach((tr) => {
      const id = (tr.querySelector("[data-tsel]") || {}).dataset?.tsel,
        t = id && (DB.txns || []).find((x) => x.id === id),
        row = tr.querySelector(".pr-row");
      if (!t || !row || row.dataset.acline) return;
      row.dataset.acline = t.id;
      const a = (DB.accounts || []).find((x) => x.id === t.acct),
        tt = row.querySelector(".pr-t"),
        m = row.querySelector(".pr-m span:last-child");
      tt && (tt.textContent = t.desc || t.vendor || "Bank line");
      m && (m.textContent = `${t.amt < 0 ? "−" : "+"}${money(Math.abs(+t.amt || 0))} · ${fmt(t.date)} · ${a ? `${a.name.split(" ")[0]} ${a.last4 || ""}`.trim() : ""}`);
      // a line with a match proposed says what it would link to on the row, and its first step is Review (its sheet
      // holds Confirm)
      const P = t.proposal;
      if (P && !row.querySelector(".ac-link")) {
        const tg = "po" === P.kind ? (DB.pos || []).find((x) => x.id === P.poId) : "bill" === P.kind ? (DB.bills || []).find((x) => x.id === P.billId) : null,
          link = tg ? `${"po" === P.kind ? "" : "Bill "}${tg.number || ""} · ${tg.vendor || ""}` : String(P.label || "").replace(/<[^>]+>/g, "");
        if (link) {
          const d = document.createElement("div");
          (d.className = "pr-m ac-link"), (d.textContent = "→ " + link), row.querySelector(".pr-mid").appendChild(d);
        }
        const slot = row.querySelector(".pr-act-slot");
        if (slot && !slot.querySelector("[data-acreview], [data-acline-open]")) {
          const b = document.createElement("button");
          (b.type = "button"), (b.className = "btn sm"), (b.textContent = "Review"), (b.dataset.aclineOpen = t.id), slot.prepend(b);
        }
      }
    });
  }
  [...sec.querySelectorAll("button")]
    .filter((b) => /^confirm$/i.test((b.textContent || "").trim()) && !b.closest(".ac-front, #mbm") && !b.dataset.acsheet)
    .forEach((b, i) => {
      // the same Confirm keeps the same id on every draw (the bank line it confirms, else its place), so a Review
      // found on one draw is the same Review on the next
      const id = "acs" + i + (b.dataset.mconfirm ? "-" + b.dataset.mconfirm : "");
      (b.dataset.acsheet = id), (b.hidden = !0);
      const r = document.createElement("button");
      (r.type = "button"), (r.className = "btn sm"), (r.textContent = "Review"), (r.dataset.acreview = id), b.parentNode.insertBefore(r, b);
    });
}
// The line's review sheet (the phone): what is wrong first, then what it would link to, then the line; Confirm when a
// match is proposed (it presses the match's own Confirm), else the row's own next step; Edit the Line is the old form.
function acLineSheet(id, actBtn) {
  const t = (DB.txns || []).find((x) => x.id === id);
  if (!t) return;
  const a = (DB.accounts || []).find((x) => x.id === t.acct),
    st = "function" == typeof txnState ? txnState(t) : {},
    typed = "function" == typeof txnFromBank && !txnFromBank(t),
    P = t.proposal,
    target = P ? ("po" === P.kind ? (DB.pos || []).find((x) => x.id === P.poId) : "bill" === P.kind ? (DB.bills || []).find((x) => x.id === P.billId) : null) : null,
    link = P ? (target ? `${"po" === P.kind ? "" : "Bill "}${target.number || ""} · ${target.vendor || ""}` : P.label || "") : "",
    warn = [typed ? "Typed by hand, not yet at the bank: it is not matched until a bank line backs it." : "", st && st.msg ? st.msg : ""].filter(Boolean),
    conf = document.querySelector(`[data-mconfirm="${CSS.escape(t.id)}"]`);
  mbModal(
    "Review the Line",
    `${warn.length ? `<div class="note warn small">${warn.map((w) => `<div>${esc(w)}</div>`).join("")}</div>` : ""}<p><b>It would link to</b><br>${link ? esc(link) : "Nothing yet: no bill, order, invoice, receipt or payroll line explains it."}${P && P.why ? `<br><span class="small muted">${P.why}</span>` : ""}</p><p><b>The line</b><br>${esc(t.desc || t.vendor || "")}<br><span class="small muted">${t.amt < 0 ? "−" : "+"}${money(Math.abs(+t.amt || 0))} · ${fmtL(t.date)} · ${esc(a ? a.name : "")}${a && a.last4 ? " ····" + esc(a.last4) : ""}</span></p>`,
    conf
      ? { submit: "Confirm", onSubmit: () => void setTimeout(() => conf.click(), 0), alt: { label: "Edit the Line", run: () => txnDialog(t.id) } }
      : actBtn
        ? { submit: (actBtn.textContent || "Open").trim().replace(/…$/, ""), onSubmit: () => void setTimeout(() => actBtn.click(), 0), alt: { label: "Edit the Line", run: () => txnDialog(t.id) } }
        : { submit: "Edit the Line", onSubmit: () => void setTimeout(() => txnDialog(t.id), 0) },
  );
}
function acReviewSheet(id) {
  const b = document.querySelector(`[data-acsheet="${id}"]`);
  if (!b) return;
  const row = b.closest(".prop-row, tr, .pay3-row, .pr-row, .rem-row, .card, li") || b.parentNode,
    txt = (e) => (e ? e.innerText || e.textContent || "" : "").replace(/\s+/g, " ").trim(),
    warn = [...row.querySelectorAll(".bad-t, .warn-t, .bad, .warn")].map(txt).filter(Boolean),
    lines = (row.innerText || "").split("\n").map((s) => s.trim()).filter((s) => s && !/^(Review|Confirm|Not This|Not this)$/.test(s)),
    target = lines.find((s) => /^→|^->/.test(s)) || "",
    head = lines[0] || "";
  mbModal(
    "Confirm the Match",
    `${warn.length ? `<div class="note warn small">${[...new Set(warn)].map((w) => `<div>${esc(w)}</div>`).join("")}</div>` : ""}${target ? `<p><b>It links to</b><br>${esc(target.replace(/^(→|->)\s*/, ""))}</p>` : ""}<p><b>The line</b><br>${esc(head)}</p>${lines.slice(1).filter((s) => s !== target && !warn.includes(s)).map((s) => `<p class="small muted" style="margin:4px 0">${esc(s)}</p>`).join("")}`,
    { submit: "Confirm", onSubmit: () => void setTimeout(() => b.click(), 0) },
  );
}
// the chip's records: the old page's own filter, set before it draws
function acPrep() {
  if (!acPageOf()) return;
  try {
    "bank" === view && ("review" === acChip.bank ? (txnFilter = "open") : "matched" === acChip.bank && "open" === txnFilter && (txnFilter = "all"));
    "ap" === view && (apFilter = { approve: "queue", pay: "approved", paid: "paid" }[acChip.ap] || apFilter);
    // Books' chip follows the ledger's own tab (a link that opens a tab, New Entry among them, keeps it)
    "gl" === view && "tax" !== acChip.gl && (acChip.gl = "periods" === glTab ? "close" : "ledger");
  } catch (e) {}
}
function acGoChip(pg, k) {
  acChip[pg] = k;
  acNewOpen = "";
  const to = "ap" === pg ? ("payroll" === k ? "time" : "ap") : "gl" === pg ? ("controls" === k ? "verify" : "budget" === k ? "budget" : "gl") : pg;
  "gl" === pg && "ledger" === k && "periods" === glTab && (glTab = "overview");
  "gl" === pg && "close" === k && (glTab = "periods");
  to === view ? render() : setView(to);
}
// forward the retired pages to their new homes (SPEC §3)
{
  const base = setView;
  setView = function (v) {
    try {
      const f = AC_FWD[v];
      f && acMay(f[0]) && ((acChip[f[0]] = f[1]), (v = f[0]));
      // Books opens on its Close (the controller's first question: can I close the month?); on the phone, where the close
      // is read and not run (SPEC §2 Books, 9), on its Ledger
      "gl" === v && "gl" !== view && acMay("gl") && (acPhone() ? ((glTab = "overview"), (acChip.gl = "ledger")) : ((glTab = "periods"), (acChip.gl = "close")));
    } catch (e) {}
    return base.call(this, v);
  };
}
{
  const base = render;
  render = function () {
    try {
      const f = AC_FWD[view];
      f && acMay(f[0]) && ((acChip[f[0]] = f[1]), (view = f[0]));
      acPrep();
    } catch (e) {}
    const r = base.apply(this, arguments);
    // the page's renderer mounted the front (later layers, the billing Preview among them, drew onto it); mount here
    // only where none is on screen, and clear one left on a page that is no longer an Accounting page
    try {
      const on = document.querySelector(".view.on");
      (!on || !on.querySelector(":scope > .ac-front") || !acPageOf()) && acMount();
      // the phone's rows are drawn by later layers (phonerows): Banking's rows are fitted once they are there
      "bank" === acPageOf() && acPhone() && on && on.querySelector(":scope > .ac-front") && acSheetOnly(on);
    } catch (e) {
      console.warn("accounting front", e);
    }
    return r;
  };
}
// Pages a role may open that its menu, by design, does not list (SPEC §4): the PM works the job's Contract and Billing
// and Budget and approves bills on his Approvals; the owner's Books, Controls and operating Budget reach him as
// sign-offs on Today and Approvals; billing's Bills and Payroll is the controller's. Each still opens by link and Cmd-K.
const MN_LINK = { pm: ["bank", "ap", "time", "spend", "verify", "ovmoney"], owner: ["gl", "verify", "budget"], billing: ["ap", "time"] };
// a page's own renderer may draw again outside render (a held draw, a tab inside the page): the front follows it
if ("function" == typeof renderBilling) {
  const base = renderBilling;
  renderBilling = function () {
    const r = base.apply(this, arguments);
    try {
      acMount();
    } catch (e) {}
    return r;
  };
}
if ("function" == typeof renderBank) {
  const base = renderBank;
  renderBank = function () {
    const r = base.apply(this, arguments);
    try {
      acMount();
    } catch (e) {}
    return r;
  };
}
if ("function" == typeof renderAP) {
  const base = renderAP;
  renderAP = function () {
    const r = base.apply(this, arguments);
    try {
      acMount();
    } catch (e) {}
    return r;
  };
}
if ("function" == typeof renderTime) {
  const base = renderTime;
  renderTime = function () {
    const r = base.apply(this, arguments);
    try {
      acMount();
    } catch (e) {}
    return r;
  };
}
if ("function" == typeof renderGL) {
  const base = renderGL;
  renderGL = function () {
    const r = base.apply(this, arguments);
    try {
      acMount();
    } catch (e) {}
    return r;
  };
}
if ("function" == typeof renderVerify) {
  const base = renderVerify;
  renderVerify = function () {
    const r = base.apply(this, arguments);
    try {
      acMount();
    } catch (e) {}
    return r;
  };
}
if ("function" == typeof renderBudget) {
  const base = renderBudget;
  renderBudget = function () {
    const r = base.apply(this, arguments);
    try {
      acMount();
    } catch (e) {}
    return r;
  };
}
// a page reached under another page's name lights that page in the menu
"object" == typeof MN_ALIAS && Object.assign(MN_ALIAS, { time: "ap", verify: "gl", budget: "gl", spend: "bank", ovmoney: "bank" });
// the menu's numbers: only where something waits on the person in that seat (SPEC §4: billing's Billing, the
// controller's Banking, Bills and Payroll and Books); the owner's Accounting entries carry none
"object" == typeof OC_BADGE &&
  Object.assign(OC_BADGE, {
    bank: { n: () => acBankReview().n },
    ap: { n: () => acApNeeds().length },
    gl: { n: () => acBooksNeeds().length },
  });
{
  const base = mnItemN;
  mnItemN = function (it) {
    if (it && AC_PAGES[it.v] && !it.tab && !it.job) return AC_PAGES[it.v].badge.includes(role()) ? acCount(it.v) : 0;
    return base.apply(this, arguments);
  };
}

// ---- wiring --------------------------------------------------------------------------------------------------------------
function acOpen(key) {
  const [k, a, b] = String(key || "").split(":");
  const c = (DB.clients || []).find((x) => x.id === a);
  if (["invoice", "estimate", "co"].includes(k) && c) {
    "undefined" != typeof blClientFlag && (blClientFlag = c.id);
    (clientOpen = c.id), (docOpen = { kind: k, id: b }), "billing" !== view ? setView("billing") : render();
    return void window.scrollTo(0, 0);
  }
  if ("bill" === k) return void openBill(a);
  if ("spend" === k) {
    const s = (DB.spend || []).find((x) => x.id === a);
    return void (s && "function" == typeof spCaptureModal ? spCaptureModal({ edit: s }) : setView("bank"));
  }
  if ("acct" === k) return (txnAcct = a), (acChip.bank = "matched"), void render();
}
function acNew(pg, k) {
  acNewOpen = "";
  const p = (DB.projects || []).find((x) => x.id === acJob),
    c = p && (DB.clients || []).find((x) => x.id === p.clientId);
  if ("billing" === pg) {
    if (!p || !c) return (acJobOpen = !0), render(), void toast("Pick the job first: the new document is for that job and its client");
    if ("app" === k) return void blDraftApplication(p.id);
    if ("dep" === k) {
      const est = (c.estimates || []).find((e) => e.projectId === p.id && ["approved", "converted"].includes(e.status));
      return void (est ? ctDepositInvoice(c, est) : toast(`${shortName(p)} has no signed estimate to take a deposit on`));
    }
    if ("inv" === k) return "undefined" != typeof finProj && (finProj = p.id), void crNewInvoice(c);
    if ("co" === k) return void newChangeOrderDialog({ clientId: c.id, projectId: p.id });
  }
  if ("bank" === pg) {
    if ("import" === k) return void bfImportDialog(txnAcct || "");
    if ("connect" === k) return void bfConnect();
    if ("rule" === k) return (bfRulesOpen = !0), render(), void setTimeout(() => document.getElementById("bf-rules")?.scrollIntoView({ block: "start" }), 60);
    if ("receipt" === k) return void spCaptureModal();
    if ("typed" === k) return void document.getElementById("btn-addtxn")?.click();
  }
  if ("ap" === pg) {
    if ("bill" === k) return void openBill();
    if ("payroll" === k) return void openPayroll();
    if ("time" === k) return void openTime();
  }
  if ("gl" === pg && "je" === k) return (glTab = "entry"), (acChip.gl = "ledger"), void ("gl" === view ? render() : setView("gl"));
}
document.addEventListener(
  "click",
  (e) => {
    const t = e.target && e.target.closest ? e.target : null;
    if (!t || !t.closest(".ac-front")) {
      // a tap outside an open menu closes it
      (acNewOpen || acJobOpen) && t && !t.closest(".ac-menu") && ((acNewOpen = ""), (acJobOpen = !1), document.querySelector(".ac-front") && acMount());
      return;
    }
    const at = (s) => t.closest(s);
    let b;
    if ((b = at("[data-acnew]"))) return e.preventDefault(), (acNewOpen = acNewOpen === b.dataset.acnew ? "" : b.dataset.acnew), (acJobOpen = !1), void acMount();
    if ((b = at("[data-acnewpick]"))) {
      e.preventDefault();
      const [pg, k] = b.dataset.acnewpick.split(":");
      acNew(pg, k);
      // acNew closes the menu in its state; a pick that opens a form or a sheet draws nothing, so the menu is drawn away
      // here (a pick that draws the page has already taken it)
      return void (!acNewOpen && document.querySelector('.ac-front .ac-menu[role="menu"]') && acMount());
    }
    if ((b = at("[data-acjob]"))) return e.preventDefault(), (acJobOpen = !acJobOpen), (acNewOpen = ""), void acMount();
    if ((b = at("[data-acjobpick]"))) return e.preventDefault(), (acJob = b.dataset.acjobpick), (acJobOpen = !1), void render();
    if ((b = at("[data-acchip]"))) {
      e.preventDefault();
      const [pg, k] = b.dataset.acchip.split(":");
      acGoChip(pg, k);
      b.hasAttribute("data-acscroll") && setTimeout(() => document.querySelector(".view.on #txn-table")?.scrollIntoView({ block: "start" }), 60);
      return;
    }
    if ((b = at("[data-acrecon]"))) return e.preventDefault(), e.stopPropagation(), void bfReconStart(b.dataset.acrecon);
    if ((b = at("[data-acundep]"))) {
      e.preventDefault();
      return void (acMay("bank") ? ((acChip.bank = "money"), setView("bank")) : ((clientOpen = b.dataset.acundep), (docOpen = null), setView("clients")));
    }
    if ((b = at("[data-acneed]"))) {
      e.preventDefault(), e.stopPropagation();
      const x = acApNeeds().find((y) => y.id === b.dataset.acneed);
      return void (x && x.open && x.open());
    }
    if ((b = at("[data-acbook]"))) {
      e.preventDefault(), e.stopPropagation();
      const x = acBooksNeeds().find((y) => y.id === b.dataset.acbook);
      if (!x) return;
      if ("close" === x.go) return void acGoChip("gl", "close");
      const g = x.go || {};
      g.client ? ((clientOpen = g.client), (docOpen = null), setView("clients")) : g.view && ("reports" === g.view && g.tab && "undefined" != typeof repTab && (repTab = g.tab), setView(g.view));
      return;
    }
    if ((b = at("[data-acgo]"))) {
      e.preventDefault();
      const tab = b.dataset.acgo.split(":")[1];
      return (billTab = tab), (docOpen = null), void render();
    }
    // a row's own Review (With Others): a bill waiting on someone else still opens from its row by a button, where it
    // can be held (BACKLOG §1.36: WW-2026-118 could not be put on hold from Bills and Payroll; its row had no control)
    if ((b = at("[data-acopenbtn]"))) return e.preventDefault(), e.stopPropagation(), void acOpen(b.dataset.acopenbtn);
    if ((b = at("tr[data-acopen]")) && !at("button, a, input, select")) return e.preventDefault(), void acOpen(b.dataset.acopen);
  },
  !0,
);
// the phone's Review on a bank line, and a tap on a To Review row (outside the front: the rows are the page's own)
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest && e.target.closest("[data-acreview]");
    if (b) return e.preventDefault(), e.stopPropagation(), void acReviewSheet(b.dataset.acreview);
    const o = e.target && e.target.closest && e.target.closest("[data-acline-open]");
    if (o) return e.preventDefault(), e.stopPropagation(), void acLineSheet(o.dataset.aclineOpen, null);
    const r = e.target && e.target.closest && e.target.closest("#v-bank.ac-host .pr-row[data-acline]");
    if (!r || e.target.closest(".pr-act-slot, input, select, button, a") || !acPhone()) return;
    e.preventDefault(), e.stopPropagation(), acLineSheet(r.dataset.acline, r.querySelector(".pr-act-slot button"));
  },
  !0,
);
document.addEventListener("keydown", (e) => {
  if ("Enter" !== e.key) return;
  const r = e.target && e.target.closest && e.target.closest(".ac-front tr[data-acopen]");
  r && (e.preventDefault(), acOpen(r.dataset.acopen));
});
