/* =====================================================================================================================
   The job page (Alan, 11-03: docs/mockups/job-structure/, docs/DECISIONS.md 11-03 row). Inside a job everything is that
   job. Alan, 10-27: "If we're in the projects page, anything we click within that project should take us to information
   regarding that particular project."

   What was wrong. Tapping 121 State Street on the phone opened All Projects > Overview (the phone defaulted the job's
   Overview to every job, dashAll), whose tiles counted the firm and opened firm pages; on the desktop the job was about
   eighteen tabs on three rows, "Needs You 23" counted beyond the job, and Estimates, Change Orders and Billing opened the
   firm's Billing page behind a hidden bill-client filter (TRIAGE class 6 and CX1: the wrong-client estimate).

   The structure. A job is one header (its name with the switcher, the client, Day N of M, Ask About This Job and one +
   that opens "New for <job>") over eight tabs, each this job only:
     Overview (dash)                four tiles (At Risk, Margin at Completion, Approvals, Materials), Next Up, Ready to Bill
     Schedule (sched)               the schedule; Tasks on This Job under it
     Contract and Billing (jbill)   Needs You, The Contract (jobFin's figures: bank-backed collected, retainage), one
                                    Documents list (estimates, change orders, invoices, payments); the Billing Queue under it
     Budget (costs)                 the Costs page reshaped: margin at completion on top, one row per estimate line (budget,
                                    committed, actual, forecast, variance, % done, % billed) from lineProfit and jobFin, the
                                    bought-for-the-client line; the cost-code table, WIP and transactions stay below
     Purchasing (proc)              the one Buy Board filtered to the job (bbProj); Materials, Deliveries, Orders under it
     Decisions (jdec)               everything waiting on an answer: decisions, selections, RFIs, submittals; the Decisions
                                    and Submittals logs under it
     Site (jsite)                   the crew's open questions, today on site, coming to site; Field and Requests under it
     Documents (files)              Drawings, Permits and Inspections, Photos, Mail and Filings under it
   On the phone the Overview lists the other seven (This Job) and every section has a back arrow to the job.

   Design gate (BACKLOG §1.16). No new store or queue. The nouns extended: the job's strip (MN_JOBS, the menu's own
   registry) is eight items; a page reached from a tab lights that tab (JP_UNDER through mnCur; MN_ALIAS for pages the
   role's menu no longer places), so nothing is lost and nothing lands in More. Three views are new pages over existing
   records: Contract and Billing reads the client's documents and jobFin; Decisions reads p.decisions, DB.sel.items,
   p.issues (type rfi) and the submittals; Site reads DB.field (raises, logs, subs), DB.time, DB.photos and the schedule.
   The RFI is the existing issue record (p.issues, type "rfi"), given an answer: New RFI and Answer write it.
   Nothing here posts or changes money; every figure is read from the functions the other pages read.
   ===================================================================================================================== */

// ---- the tabs, and the pages that live under each ------------------------------------------------------------------
const JP_TABS = [
    ["dash", "Overview"],
    ["sched", "Schedule"],
    ["jbill", "Contract and Billing"],
    ["costs", "Budget"],
    ["proc", "Purchasing"],
    ["jdec", "Decisions"],
    ["jsite", "Site"],
    ["files", "Documents"],
  ],
  // a page opened from a tab lights that tab while the person is in the job (mnCur reads it when they came through
  // Projects); the tab is where its control lives
  JP_UNDER = {
    proj: "dash",
    sboard: "dash",
    tasks: "sched",
    billing: "jbill",
    mat: "proc",
    recv: "proc",
    po: "proc",
    rfq: "proc",
    dec: "jdec",
    subm: "jdec",
    sel: "jdec",
    field: "jsite",
    req: "jsite",
    plans: "files",
    insp: "files",
    photos: "files",
    inbox: "files",
    sfile: "files",
  },
  // pages the old strip placed that no menu entry places now: they open under their tab's name, never under More
  JP_ALIAS = { tasks: "sched", proj: "dash", dec: "jdec", subm: "jdec", insp: "files", field: "jsite", photos: "files", mat: "proc", recv: "proc", inbox: "files", plans: "files" },
  // the phone's section line under the header
  JP_BLURB = {
    sched: "the plan to finish",
    jbill: "",
    costs: "what the job costs us",
    proc: "what to buy and what is coming",
    jdec: "everything waiting on an answer",
    jsite: "what is happening on site",
    files: "drawings, permits, photos and mail",
  },
  JP_IC = {
    back: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>',
    down: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>',
    plus: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
    next: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>',
    warn: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4M12 17.5v.01"/></svg>',
  };
// The tab a page sits under while the person is in the job, or "": a page that shows another client's records is not
// this job's page (Billing opened on 45 Cranberry's invoice is Billing, not 121 State's Contract and Billing)
function jpUnder(v) {
  const t = JP_UNDER[v];
  if (!t || !S) return "";
  if ("billing" === v) {
    const cid = ("undefined" != typeof docOpen && docOpen && "undefined" != typeof clientOpen && clientOpen) || ("undefined" != typeof billClient ? billClient : "");
    return cid && cid === S.clientId ? t : "";
  }
  return t;
}
let jpSub = "", // phone: the Overview's own page (risk, appr, mat); "" is the Overview
  jpPanel = "risk", // desktop: the panel the tiles choose
  jpMenuOpen = !1,
  jpDecKind = "All",
  jpDocKind = "All",
  jpBudOpen = "";

// ---- the registry: labels, views, who may open them --------------------------------------------------------------
(function jpRegister() {
  const L = { jbill: "Contract and Billing", jdec: "Decisions", jsite: "Site" };
  [void 0 !== NAV_LABELS ? NAV_LABELS : null, void 0 !== IA_LABELS ? IA_LABELS : null].forEach((x) => x && Object.assign(x, L));
  try {
    Object.keys(L).forEach((v) => mnKnow(v, L[v])), mnKnow("costs", "Budget");
  } catch (e) {}
  // a page the menu no longer places opens under its tab's name; never one the role's menu places elsewhere
  "object" == typeof MN_ALIAS && Object.assign(MN_ALIAS, JP_ALIAS);
  // a new document started on these pages is the job's, with the job's client (crDocContext)
  "undefined" != typeof CR_PROJECT_VIEWS && ["jbill", "jdec", "jsite"].forEach((v) => CR_PROJECT_VIEWS.includes(v) || CR_PROJECT_VIEWS.push(v));
  jpGrant();
})();
// Who may open the new pages: a role with a Projects menu that could open the pages folded into them. Later sections
// still add pages to a role at sign-in, so this runs again before each draw (it only ever adds).
function jpGrant() {
  Object.keys(ROLE_VIEWS).forEach((r) => {
    const rv = ROLE_VIEWS[r],
      M = "object" == typeof MENU && MENU[r];
    if (!rv || !M || M.field || "client" === r || !(M.groups || []).some((g) => "jobs" === g.id)) return;
    rv.includes("billing") && !rv.includes("jbill") && rv.push("jbill");
    (rv.includes("dec") || rv.includes("subm")) && !rv.includes("jdec") && rv.push("jdec");
    (rv.includes("field") || rv.includes("req")) && !rv.includes("jsite") && rv.push("jsite");
  });
}

const jpMay = (v) => (ROLE_VIEWS[role()] || []).includes(v);
const jpClient = (p) => ((p = p || S), p ? (DB.clients || []).find((c) => c.id === p.clientId) || null : null);
const jpName = (p) => ((p = p || S), (p && p.project && p.project.name) || "");
const jpShort = (p) => ("function" == typeof shortName ? shortName(p || S) : jpName(p));
const jpFirst = (c) =>
  !c
    ? "the client"
    : /&| and /.test(c.name)
      ? "the " + String(c.name).split(/\s+/).pop().replace(/s$/, "") + "s"
      : String(c.name).split(" ")[0];
const jpDay = (d) => {
  if (!d) return "";
  const n = dayDiff(today(), d);
  return 0 === n ? "Today" : 1 === n ? "Tomorrow" : n > 1 && n <= 6 ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][parse(d).getDay()] : fmt(d);
};
const jpPhone = () => ("function" == typeof mOn ? mOn() : innerWidth <= 760);

// The page on screen, as the menu reads it: the jobs group's item (a tab), or null.
let jpCurMemo = { k: "", v: null };
function jpCur() {
  const k = [render.__tick, view, S && S.id, mnLastGrp, role(), typeof bbProj !== "undefined" ? bbProj : ""].join("|");
  if (jpCurMemo.k === k) return jpCurMemo.v;
  let v = null;
  try {
    const r = role();
    if (MENU[r] && !MENU[r].field && "client" !== r && mnOn(r)) {
      const c = mnCur(mnBuild(r));
      c && "jobs" === c.g.id && !c.it.nostrip && (v = c);
    }
  } catch (e) {}
  return (jpCurMemo = { k: k, v: v }), v;
}
function jpOn() {
  return !!(S && S.id && (DB.projects || []).some((p) => p.id === S.id) && jpCur());
}
// the tab the page on screen sits under
const jpTab = () => {
  const c = jpCur();
  return c ? c.it.v : "";
};

// The one way into a job: its page, on its Overview (or a tab), from the list, a menu entry, a link or the switcher.
function jpOpenJob(pid, v) {
  if (!(DB.projects || []).some((p) => p.id === pid)) return;
  setCurrent(pid);
  try {
    mnLastGrp = "jobs";
  } catch (e) {}
  "undefined" != typeof dashAll && (dashAll = !1);
  (jpSub = ""), (jpMenuOpen = !1);
  "proc" === v && "undefined" != typeof bbProj && (bbProj = pid);
  // the job's first tab the person may open (the designer, who has no Overview, lands on its Schedule)
  const tabs = JP_TABS.map((t) => t[0]).filter(jpMay);
  save(), setView(tabs.includes(v) ? v : tabs[0] || (v && jpMay(v) ? v : "dash"));
}
// a page in or under the job, opened from the job: it stays the job's page
function jpGo(v) {
  const [vv, tab] = String(v).split(":");
  try {
    mnLastGrp = "jobs";
  } catch (e) {}
  (jpMenuOpen = !1), (jpSub = "");
  if ("ovjobs" === vv) return void setView("ovjobs");
  if ("billing" === vv) (billTab = tab || "billable"), (docOpen = null), (billClient = (S && S.clientId) || "");
  "proc" === vv && "undefined" != typeof bbProj && (bbProj = S.id);
  setView(vv);
}

// ---- the header ----------------------------------------------------------------------------------------------------
function jpDayLine(p) {
  const P = p.project || {},
    td = today();
  let finish = P.target || "";
  try {
    const h = projectHealth(p);
    h && h.tasks && h.sc && (finish = h.sc);
  } catch (e) {}
  if (!P.start) return finish ? `finish ${fmtL(finish)}` : "";
  if (td < P.start) return `starts ${fmtL(P.start)}`;
  const n = workdays(P.start, td),
    m = finish ? Math.max(n, workdays(P.start, finish)) : 0;
  return `Day ${n}${m ? ` of ${m}` : ""}${finish ? ` · finish ${fmtL(finish)}` : ""}`;
}
function jpWhat(p) {
  return String((p.project && (p.project.type || p.project.addr)) || "")
    .split("·")[0]
    .trim();
}
function jpHeadHtml() {
  const p = S,
    c = jpClient(p),
    phone = jpPhone(),
    tab = jpTab(),
    cur = jpCur(),
    ov = "dash" === view && !jpSub,
    sect = phone && !ov,
    title = "dash" === view && jpSub ? { risk: "At Risk", appr: "Approvals", mat: "Materials" }[jpSub] : (cur && cur.it.l) || "",
    line = sect
      ? `${jpName(p)} · ${"jbill" === tab ? `with ${c ? c.name : "the client"}` : "dash" === view && jpSub ? "this job only" : JP_BLURB[tab] || mnLabel(view)}`
      : [c && c.name, jpWhat(p), jpDayLine(p)].filter(Boolean).join(" · ");
  return `<div class="jp-row">${phone ? `<button type="button" class="jp-back jp-ib" data-jpback aria-label="${ov ? "Back to Projects" : "Back to " + esc(jpName(p))}">${JP_IC.back}</button>` : ""}${
    sect ? `<b class="jp-sect">${esc(title)}</b>` : `<span class="jp-name"><span class="jp-sw"></span><span class="jp-chev">${JP_IC.down}</span></span>`
  }<span class="jp-grow"></span>${phone ? "" : `<button type="button" class="btn jp-ask" id="jp-ask">Ask About This Job</button>`}${
    // the + is on every page of the job, the phone's sections too: anything new on a job starts where the person is
    `<span class="jp-newwrap"><button type="button" class="jp-plus jp-ib" id="jp-new" aria-label="New for this job" aria-haspopup="menu" aria-expanded="${jpMenuOpen}">${JP_IC.plus}</button>${jpMenuOpen ? jpNewMenuHtml() : ""}</span>`
  }</div><div class="jp-sub">${esc(line)}</div>`;
}
function jpHead() {
  const on = jpOn(),
    sub = document.getElementById("subnav"),
    nav = document.getElementById("nav");
  let H = document.getElementById("jp-head");
  document.body.classList.toggle("jp-on", on), document.body.classList.toggle("jp-ovw", on && "dash" === view);
  if (!on) {
    H && (H.hidden = !0);
    nav && nav._projsel && H && H.contains(nav._projsel) && (nav.appendChild(nav._projsel), (nav._projsel.hidden = !0));
    return;
  }
  H || ((H = document.createElement("div")), (H.id = "jp-head"), (H.className = "jp-head jp-keep no-print"));
  sub && sub.parentNode ? H.nextSibling !== sub && sub.parentNode.insertBefore(H, sub) : H.isConnected || (document.querySelector(".main") || document.body).prepend(H);
  (H.hidden = !1), (H.innerHTML = jpHeadHtml());
  const slot = H.querySelector(".jp-sw");
  if (slot && nav && nav._projsel) slot.appendChild(nav._projsel), (nav._projsel.hidden = !1);
  else nav && nav._projsel && !H.contains(nav._projsel) && (nav._projsel.hidden = !0);
  const ps = document.getElementById("pswitch");
  ps && ps.setAttribute("aria-label", "Switch project");
}

// ---- New for <job>: every kind starts on this job, for this job's client --------------------------------------------
// Each kind is offered only to a person who may open the page its record lives on (ROLE_VIEWS, the gate setView uses):
// an estimate, a change order and an invoice live on Billing; an order on Orders or the Buy Board; a task on Tasks; a
// decision on Decisions; a site note or photo on the job's Site, Field or Photos; a document on Documents. A hard-coded
// role list offered the designer an invoice she could not open.
const JP_NEW_LIVES = {
  est: ["billing"],
  co: ["billing"],
  inv: ["billing"],
  po: ["po", "proc"],
  task: ["tkall", "tasks"],
  dec: ["dec", "jdec"],
  note: ["field", "jsite", "photos"],
  doc: ["files"],
};
function jpNewItems() {
  return [
    ["est", "Estimate", () => docNewEstimate(S.clientId, S.id)],
    ["co", "Change Order", () => (newChangeOrderDialog({ clientId: S.clientId, projectId: S.id }), jpFixFor())],
    [
      "inv",
      "Invoice",
      () => {
        const c = jpClient();
        if (!c) return toast("This job has no client yet");
        "undefined" != typeof finProj && (finProj = S.id);
        try {
          mnLastGrp = "jobs";
        } catch (e) {}
        crNewInvoice(c);
      },
    ],
    ["po", "Purchase Order", () => newPODialog()],
    ["task", "Task", () => newTaskDialog({ projectId: S.id })],
    ["dec", "Decision", () => crQuick("decision")],
    ["note", "Site Note or Photo", () => crQuick("note")],
    ["doc", "Document", () => jpUploadDoc()],
  ]
    .filter(([k]) => (JP_NEW_LIVES[k] || []).some(jpMay))
    .map(([k, l, run]) => [k, l, !0, run]);
}
function jpNewMenuHtml() {
  return `<div class="jp-menu" id="jp-newmenu" role="menu"><span class="jp-nh">New for ${esc(jpName())}</span>${jpNewItems()
    .map(([k, l]) => `<button type="button" role="menuitem" class="jp-mi" data-jpnew="${k}">${esc(l)}</button>`)
    .join("")}</div>`;
}
// A sheet started from the job's + is for this job and its client: the Client and Project pickers it would show are
// set from the project and stated, not offered (the wrong-client estimate came from a picker set by a billing filter).
function jpFixFor() {
  const m = document.getElementById("mbm");
  if (!m || !S) return;
  const c = jpClient(),
    cs = m.querySelector('[data-f="clientId"]'),
    ps = m.querySelector('[data-f="projectId"]');
  if (!cs || !c || cs.value !== c.id || (ps && ps.value !== S.id)) return;
  [cs, ps].forEach((e) => {
    const f = e && (e.closest(".f") || e.parentElement);
    f && ((f.hidden = !0), (f.style.display = "none"));
  });
  const at = (cs.closest(".f") || cs).parentElement;
  at && !m.querySelector(".jp-for") && (cs.closest(".f") || cs).insertAdjacentHTML("beforebegin", `<p class="jp-for small muted" style="margin:0 0 8px">For <b>${esc(jpName())}</b> · ${esc(c.name)}</p>`);
}
function jpUploadDoc() {
  jpGo("files");
  setTimeout(() => {
    const i = [...document.querySelectorAll('#v-files input[type="file"]')].find((x) => !x.disabled);
    i ? i.click() : toast(`Drop the file on ${jpShort()}'s Documents`);
  }, 80);
}

// ---- Overview: the four tiles, Next Up, Ready to Bill (this job only) -----------------------------------------------
function jpRisks() {
  let A = [];
  try {
    A = attention().filter((a) => 3 === a.sev);
  } catch (e) {}
  return A.sort((a, b) => String(a.when || "").localeCompare(String(b.when || "")));
}
const JP_RISK_VERB = { dec: "Get an Answer", mat: "Expedite", po: "Review the Order", bill: "Review the Bill", task: "Open the Task", insp: "Book It", iss: "Open the RFI", permit: "Open the Permit", action: "Open the Task", view: "Open" };
const JP_RISK_KIND = { dec: "Decision", mat: "Order", po: "Order", bill: "Bill", task: "Schedule", insp: "Inspection", iss: "RFI", permit: "Permit", action: "Task", view: "Site" };
function jpApprJob(a) {
  const o = a.open || {};
  if (o.project) return o.project;
  if (a.projectId) return a.projectId;
  try {
    if ("bill" === a.kind) return ((DB.bills || []).find((x) => x.id === (o.billId || a.id)) || {}).projectId || "";
    if ("time" === a.kind) return ((DB.time || []).find((x) => x.id === a.id) || {}).projectId || "";
    if ("hand" === a.kind && /^needco:/.test(a.id)) return ((DB.field.raises || []).find((x) => x.id === a.id.split(":")[1]) || {}).projectId || "";
    if ("meeting" === a.kind) return ((DB.meetings || []).find((x) => x.id === (o.meeting || a.id)) || {}).projectId || "";
  } catch (e) {}
  const d = String(a.detail || "");
  return ((DB.projects || []).find((p) => d.startsWith(jpName(p))) || {}).id || "";
}
function jpApprovals(pid) {
  try {
    return (mApprovals() || []).filter((a) => jpApprJob(a) === pid);
  } catch (e) {
    return [];
  }
}
function jpLate(pid) {
  try {
    return PRED.lateMaterial.rows().filter((r) => r.p && r.p.id === pid);
  } catch (e) {
    return [];
  }
}
function jpOverBudget() {
  let L = [];
  try {
    L = jpLines().filter((r) => r.variance > 0.5);
  } catch (e) {}
  return L;
}
function jpNextUp(p) {
  const td = today(),
    end = addWork(td, 5),
    out = [];
  try {
    tkAll({ open: !0 })
      .filter((t) => t.projectId === p.id && !t.approval && "sched" !== t.kind && t.due && t.due <= end)
      .forEach((t) => out.push({ d: t.due < td ? td : t.due, what: t.title, key: t.key, late: t.due < td }));
  } catch (e) {}
  (p.inspections || [])
    .filter((i) => i.date && i.date >= td && i.date <= end && !["passed", "failed"].includes(i.status))
    .forEach((i) => out.push({ d: i.date, what: `${i.agency ? i.agency + " " : ""}${i.name}`, insp: i.id }));
  return out.sort((a, b) => a.d.localeCompare(b.d)).slice(0, 6);
}
function jpReady(pid) {
  let W = [];
  try {
    W = lkUnbilledWork(pid);
  } catch (e) {}
  const ready = W.filter((w) => !w.held);
  return { W: W, ready: ready, amt: r2(ready.reduce((a, w) => a + w.amount, 0)), held: W.length - ready.length };
}
const jpCanBill = () => ["owner", "pm", "billing", "controller"].includes(role()) && jpMay("billing");
function jpTileHtml(id, k, v, s, tone) {
  const on = !jpPhone() && jpPanel === id;
  return `<button type="button" class="gl jp-tile jp-tap ${tone || ""} ${on ? "on" : ""}" data-tl="${id}" aria-pressed="${on}"><span class="gl-k">${esc(k)}</span><b class="gl-v">${esc(v)}</b><span class="gl-s">${esc(s)}</span></button>`;
}
function jpTiles(p) {
  const R = jpRisks(),
    J = jobFin(p),
    A = jpApprovals(p.id),
    M = jpLate(p.id),
    O = jpOverBudget(),
    kinds = {};
  R.forEach((a) => {
    const k = (JP_RISK_KIND[a.go[0]] || "item").toLowerCase();
    kinds[k] = (kinds[k] || 0) + 1;
  });
  const parts = Object.entries(kinds).map(([k, n]) => `${n} ${k}${1 === n ? "" : "s"}`);
  return [
    jpTileHtml("risk", "At Risk", String(R.length), parts.join(", ") || "nothing urgent on this job", R.length ? "bad" : ""),
    jpTileHtml("margin", "Margin at Completion", `${Math.round(J.estGPPct || 0)}%`, `Plan ${Math.round(J.plannedGPPct || 0)}%${O.length ? ` · ${O[0].name.split(/ [—–-] /)[0]} ${jpOverWord(O[0])}` : " · this job"}`, (J.estGPPct || 0) < (J.plannedGPPct || 0) - 0.5 ? "warn" : ""),
    jpTileHtml("appr", "Approvals", String(A.length), A.length ? "For you, on this job" : "nothing waiting on you here", ""),
    jpTileHtml("mat", "Materials", `${M.length} late`, M.slice(0, 2).map((r) => r.name.split(/[,(]/)[0].trim()).join(", ") || "nothing late to order or arrive", M.length ? "warn" : ""),
  ].join("");
}
function jpRowsHtml(rows, empty) {
  if (!rows.length) return `<p class="jp-empty">${esc(empty)}</p>`;
  return jpPhone()
    ? `<div class="jp-cards">${rows
        .map(
          (r) =>
            `<div class="jp-card" data-jprow="${esc(r.key)}" role="button" tabindex="0"><span class="jp-ck"><b class="${r.tone || ""}">${esc(r.kind)}</b>${r.when ? ` · ${esc(r.when)}` : ""}</span><div class="jp-ct"><b>${esc(r.title)}</b>${r.amt ? `<b>${esc(r.amt)}</b>` : ""}</div><span class="jp-cw">${esc(r.why || "")}</span>${r.act ? `<div class="jp-ca"><button type="button" class="btn jp-tap" data-jpact="${esc(r.key)}">${esc(r.act)}</button></div>` : ""}</div>`,
        )
        .join("")}</div>`
    : `<table class="jp-rows"><tbody>${rows
        .map(
          (r) =>
            `<tr data-jprow="${esc(r.key)}" class="jp-click"><td class="jp-rk ${r.tone || ""}">${esc(r.kind)}${r.when ? ` · ${esc(r.when)}` : ""}</td><td class="jp-rt"><b>${esc(r.title)}</b><span>${esc(r.why || "")}</span></td><td class="jp-ra">${esc(r.amt || "")}</td><td class="jp-rb">${r.act ? `<button type="button" class="btn sm" data-jpact="${esc(r.key)}">${esc(r.act)}</button>` : ""}</td></tr>`,
        )
        .join("")}</tbody></table>`;
}
// the rows each tile opens: one list per tile, the same rows on the desktop's panel and the phone's page
let jpActs = {};
function jpPanelRows(id, p) {
  jpActs = {};
  const act = (key, fn) => ((jpActs[key] = fn), key);
  if ("risk" === id)
    return jpRisks().map((a, i) => {
      const [k, rid] = a.go,
        key = act(`risk:${i}`, () => ("view" === k ? jpGo(rid) : openEditor(k, rid)));
      return { key: key, kind: JP_RISK_KIND[k] || "Item", when: a.when ? fmt(a.when) : "", tone: "bad", title: a.t.replace(/^Decision: /, ""), why: [a.why, a.act].filter(Boolean).map((s) => String(s).trim().replace(/[^.!?]$/, "$&.")).join(" "), act: JP_RISK_VERB[k] || "Open" };
    });
  if ("appr" === id)
    return jpApprovals(p.id).map((a, i) => ({
      key: act(`appr:${i}`, () => (a.open && "function" == typeof mGo ? mGo(a.open) : setView("mapprove"))),
      kind: { bill: "Bill", time: "Hours", dec: "Decision", raise: "From the Site", subm: "Submittal", hand: "Change Order", meeting: "Meeting", clientq: "Client Question" }[a.kind] || "Approval",
      title: a.title.replace(new RegExp(` — ${jpName(p).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`), ""),
      why: String(a.detail || "").replace(jpName(p) + " · ", ""),
      act: "Review",
    }));
  if ("mat" === id)
    return jpLate(p.id).map((r, i) => ({
      key: act(`mat:${i}`, () => ((bbSel = r.id), (bbTab = "buy"), jpGo("proc"))),
      kind: "Late",
      tone: "warn",
      title: r.name,
      why: r.lateWhy || r.why || "",
      act: r.ordered || r.po ? "Expedite" : "Order",
    }));
  if ("margin" === id) {
    const J = jobFin(p),
      O = jpOverBudget();
    return [
      { key: "m:billed", kind: "Billed", title: "Billed to date", why: J.over ? `Billed ahead of the work by ${money(J.over)} (Over-Billed, WIP)` : "In step with the work", amt: money(J.billed) },
      { key: "m:cost", kind: "Cost", title: "Cost to date", why: "Bills, bank and card lines, stock and labor on this job", amt: money(J.actual) },
    ]
      .concat(O.map((o, i) => ({ key: `m:o${i}`, kind: "Over Budget", tone: "bad", title: `${o.name}: ${jpOverWord(o)} its budget`, why: `${money(o.forecast)} on a ${money(o.budget)} budget`, amt: "+" + money(r2(o.variance)) })))
      .concat([{ key: "m:contract", kind: "Contract", title: "Contract with approved changes", why: `Base ${money(J.base)}${J.coAmt ? ` plus ${money(J.coAmt)} of approved change orders` : ""}`, amt: money(J.contract) }]);
  }
  return [];
}
function jpPanelHtml(id, p) {
  const rows = jpPanelRows(id, p),
    head = {
      risk: ["At Risk on This Job", "Most urgent first", "nothing urgent on this job"],
      appr: ["Approvals on This Job", `${rows.length} waiting on you`, "nothing on this job waits on you"],
      mat: ["Materials on This Job", `${rows.length} late`, "nothing late to order or to arrive"],
      margin: ["Budget: Margin at Completion", "the full view is under Budget", ""],
    }[id] || ["", "", ""],
    links = {
      appr: jpMay("mapprove") ? `<button type="button" class="jp-link jp-tap" data-jpgo="mapprove">All Approvals, Every Job</button>` : "",
      mat: `<button type="button" class="jp-link jp-tap" data-jpgo="proc">Open Purchasing for This Job</button>`,
      margin: jpMay("costs") ? `<button type="button" class="jp-link jp-tap" data-jpgo="costs">Open Budget</button>` : "",
    }[id] || "";
  return `<section class="jp-card0" id="jp-panel" data-state="${id}"><div class="jp-ph"><h3>${esc(head[0])}</h3><span>${esc(head[1])}</span></div>${jpRowsHtml(rows, head[2])}${links ? `<div class="jp-pf">${links}</div>` : ""}</section>`;
}
function jpNextHtml(p) {
  const N = jpNextUp(p);
  return `<section class="jp-card0" id="jp-next"><div class="jp-ph"><h3>Next Up on This Job</h3><span>${esc(fmtL(today()))}</span></div>${
    N.length
      ? N.map((n) => `<button type="button" class="jp-nx jp-tap" data-jprow="${esc(n.key || "insp:" + n.insp)}" ${n.key ? `data-jptask="${esc(n.key)}"` : `data-jpinsp="${esc(n.insp)}"`}><span class="jp-nw ${n.late ? "bad" : ""}">${esc(n.late ? "Late" : jpDay(n.d))}</span><span>${esc(n.what)}</span></button>`).join("")
      : '<p class="jp-empty">Nothing due on this job this week.</p>'
  }${jpMay("tasks") ? `<div class="jp-pf"><button type="button" class="jp-link jp-tap" data-jpgo="tasks">Tasks on This Job</button></div>` : ""}</section>`;
}
function jpReadyHtml(p) {
  const R = jpReady(p.id);
  return `<section class="jp-ready" id="jp-rtb"><b>Ready to Bill on This Job</b><span>${
    R.amt
      ? `${money(R.amt)} of measured work on ${R.ready.length} line${1 === R.ready.length ? "" : "s"}: ${esc(R.ready.map((w) => (w.co ? w.co + " " : "") + w.desc.split(/ [—–-] |,/)[0]).join(" and "))}.${R.held ? ` ${R.held} line${1 === R.held ? "" : "s"} billed ahead ${1 === R.held ? "is" : "are"} held.` : ""}`
      : `Nothing measured and unbilled on this job${R.held ? `; ${R.held} line${1 === R.held ? "" : "s"} billed ahead ${1 === R.held ? "is" : "are"} held` : ""}.`
  }</span>${R.amt && jpCanBill() ? `<button type="button" class="jp-link jp-tap" data-jpdraft="1">Draft the Application</button>` : ""}</section>`;
}
function jpSectionsHtml(p) {
  const cur = jpCur(),
    items = cur ? cur.g.items.filter((it) => !it.nostrip && "dash" !== it.v) : [],
    R = jpReady(p.id),
    O = jpOverBudget(),
    M = jpLate(p.id),
    sub = {
      sched: () => {
        try {
          const h = projectHealth(p);
          return h.tasks ? `${h.late ? `${h.late} late` : "On track"} · ${fmt(h.sc)}` : "No schedule yet";
        } catch (e) {
          return "";
        }
      },
      jbill: () => (R.amt ? `${money(R.amt)} ready to bill` : "Nothing ready to bill"),
      costs: () => (O.length ? `${O[0].name.split(/ [—–-] /)[0]} ${jpOverWord(O[0])}` : "On budget"),
      proc: () => (M.length ? `${M.length} late` : "Nothing late"),
      jdec: () => {
        const n = jpDecRows(p).filter((r) => r.overdue).length;
        return n ? `${n} overdue` : "Nothing overdue";
      },
      jsite: () => {
        const n = jpQuestions(p).length;
        return n ? `${n} question${1 === n ? "" : "s"} from the crew` : "No open questions";
      },
      files: () => "Drawings, permits",
    };
  return `<div class="jp-cap">This Job</div><nav class="jp-card0 jp-secs" id="jp-sections" aria-label="This job">${items
    .map((it) => `<button type="button" class="jp-sec jp-tap" data-jpsec="${it.v}" aria-label="${esc(it.l)}"><span class="jp-sl">${esc(it.l)}</span><span class="jp-ss">${esc((sub[it.v] || (() => ""))())}</span>${JP_IC.next}</button>`)
    .join("")}</nav>`;
}
function jpOverview() {
  const v = document.getElementById("v-dash");
  if (!v || "dash" !== view) return;
  let host = document.getElementById("jp-ov");
  if (!jpOn()) return void (host && host.remove());
  host || ((host = document.createElement("div")), (host.id = "jp-ov"), (host.className = "jp-ov jp-keep"));
  v.firstElementChild !== host && v.prepend(host);
  const p = S,
    phone = jpPhone();
  phone || jpSub || (jpPanel = jpPanel || "risk");
  if (phone && jpSub) host.innerHTML = `<h2 class="jp-vh">Overview</h2>${jpPanelHtml(jpSub, p)}`;
  else if (phone)
    host.innerHTML = `<h2 class="jp-vh">Overview</h2><div class="jp-tiles">${jpTiles(p)}</div>${jpNextHtml(p)}${jpReadyHtml(p)}${jpSectionsHtml(p)}${jpMoreLinks(["proj"])}`;
  else
    host.innerHTML = `<h2 class="jp-vh">Overview</h2><div class="jp-tiles">${jpTiles(p)}</div><div class="jp-two"><div class="jp-main">${jpPanelHtml(jpPanel, p)}</div><aside class="jp-aside">${jpNextHtml(p)}${jpReadyHtml(p)}${jpMoreLinks(["proj", "sboard"])}</aside></div>`;
  // the job's pinned sheets (Alan, 2026-10-19: they live on the job's page) sit beside Next Up, drawn here: the old
  // layout they were put into is not drawn on a job's page any more
  !jpSub &&
    "function" == typeof plPinnedHtml &&
    "function" == typeof plStaff &&
    plStaff() &&
    plSheets(p.id).length &&
    (host.querySelector(".jp-aside") || host).insertAdjacentHTML("beforeend", plPinnedHtml(p, 5));
}
// The old dashboard (its tiles, Look-Ahead, Needs Attention, Daily Brief, Ahead of Schedule, Since Yesterday, and the
// notes other sections put under them) is not drawn on a job's page. It used to be drawn and hidden: about 8,600
// characters a person could not see and a check reading textContent could still pass on. Its own blocks are set aside
// while a job's Overview is on screen and put back for a dash with no job; whatever else lands in the view is removed.
let jpDashKept = null;
function jpDashClear() {
  const v = document.getElementById("v-dash");
  if (!v) return;
  [...v.children].forEach((el) => {
    if ("jp-ov" === el.id) return;
    if (el.matches("#kpis, .hero, .grid3")) (jpDashKept = jpDashKept || document.createDocumentFragment()).appendChild(el);
    else el.remove();
  });
}
function jpDashRestore() {
  const v = document.getElementById("v-dash");
  v && jpDashKept && jpDashKept.childNodes.length && v.appendChild(jpDashKept);
}
if ("function" == typeof renderDash) {
  const base = renderDash;
  renderDash = function () {
    if ("dash" === view && jpOn()) return;
    jpDashRestore();
    return base.apply(this, arguments);
  };
}
const JP_LINK = {
  proj: "Job Settings",
  sboard: "Project Board",
  tasks: "Tasks on This Job",
  dec: "Decisions Log",
  subm: "Submittals Log",
  sel: "Selections",
  field: "Daily Logs and Open Items",
  req: "Requests",
  mat: "Materials",
  recv: "Deliveries",
  po: "Orders",
  plans: "Drawings",
  insp: "Permits and Inspections",
  photos: "Photos",
  inbox: "Mail",
  sfile: "Filings",
  billing: "Billing Queue for This Job",
};
function jpMoreLinks(vs, id) {
  const L = vs.filter(jpMay);
  return L.length ? `<div class="jp-links"${id ? ` id="${id}"` : ""}>${L.map((x) => `<button type="button" class="jp-link jp-tap" data-jpgo="${x}">${esc(JP_LINK[x] || mnLabel(x))}</button>`).join("")}</div>` : "";
}

// ---- Contract and Billing --------------------------------------------------------------------------------------------
function jpDocWord(c, kind, x) {
  const s = x.status;
  if ("invoice" === kind) {
    const st = "function" == typeof invoiceStatus ? invoiceStatus(c, x) : s;
    return "paid" === st
      ? ["Paid", "ok"]
      : "draft" === st
        ? ["Draft", ""]
        : "void" === st
          ? ["Void", ""]
          : x.due && x.due < today()
            ? [`Overdue since ${fmt(x.due)}`, "bad"]
            : [x.due ? `Due ${fmt(x.due)}` : "Sent", "warn"];
  }
  if ("co" === kind)
    return { draft: ["Draft", ""], sent: ["Waiting on client", "warn"], approved: ["Approved", "ok"], billed: ["Billed", "ok"], rejected: ["Declined", "bad"], void: ["Void", ""] }[s] || [s, ""];
  return { draft: ["Draft", ""], sent: ["Sent, waiting on client", "warn"], approved: ["Signed", "ok"], converted: ["Signed", "ok"], superseded: ["Superseded", ""], declined: ["Declined", "bad"], lost: ["Lost", ""] }[s] || [s, ""];
}
function jpDocs(p) {
  const c = jpClient(p);
  if (!c) return [];
  const mine = (x) => x.projectId === p.id,
    inv = (c.invoices || []).filter(mine),
    ids = new Set(inv.map((x) => x.id)),
    out = [];
  (c.estimates || []).filter(mine).forEach((x) => out.push({ kind: "Estimates", k: "estimate", x: x, no: x.number, what: x.title || "Estimate", amt: docTotal(x).total, date: x.date || "", st: jpDocWord(c, "estimate", x) }));
  (c.changeOrders || []).filter(mine).forEach((x) => out.push({ kind: "Change Orders", k: "co", x: x, no: x.number, what: x.title || "Change order", amt: docTotal(x).total, date: x.date || "", st: jpDocWord(c, "co", x) }));
  inv.forEach((x) => out.push({ kind: "Invoices", k: "invoice", x: x, no: x.number, what: x.title || "Invoice", amt: docTotal(x).total, date: x.date || "", st: jpDocWord(c, "invoice", x) }));
  (c.payments || [])
    .filter((py) => ids.has(py.invoiceId) && !py.void)
    .forEach((py) => {
      const i = inv.find((x) => x.id === py.invoiceId),
        banked = "function" == typeof payBanked ? payBanked(c, py) : !!py.txnId;
      out.push({ kind: "Payments", k: "payment", x: py, inv: i, no: py.method || "Payment", what: `Applied to ${i ? i.number : "an invoice"}`, amt: +py.amount || 0, date: py.date || "", st: banked ? ["In the bank", "ok"] : ["No bank line yet", "warn"] });
    });
  return out.sort((a, b) => String(b.date).localeCompare(String(a.date)) || String(b.no).localeCompare(String(a.no)));
}
function jpOpenDoc(c, kind, id) {
  (clientOpen = c.id), (docOpen = { kind: kind, id: id });
  try {
    mnLastGrp = "jobs";
  } catch (e) {}
  jpMay("billing") ? ((billTab = "estimate" === kind ? "estimates" : "co" === kind ? "co" : "invoices"), (billClient = c.id), setView("billing")) : ((clientTab = "fin"), (finTab = "estimate" === kind ? "estimates" : "co" === kind ? "co" : "invoices"), setView("clients"));
}
function jpNeeds(p) {
  const c = jpClient(p),
    R = jpReady(p.id),
    out = [];
  if (R.amt)
    out.push({
      key: "rtb",
      title: `${money(R.amt)} of measured work ready to bill`,
      why: `${R.ready.map((w) => w.desc.split(/ [—–-] |,/)[0]).join(" and ")}.${R.held ? ` ${R.held} line${1 === R.held ? "" : "s"} billed ahead ${1 === R.held ? "is" : "are"} held.` : ""}`,
    });
  c &&
    (c.changeOrders || [])
      .filter((x) => x.projectId === p.id && "sent" === x.status)
      .forEach((x) => out.push({ key: "co:" + x.id, title: `${x.number} waiting on ${jpFirst(c)}`, why: `${x.title || "Change order"}, ${money(docTotal(x).total)}. Sent ${fmtL(x.sentAt ? String(x.sentAt).slice(0, 10) : x.date)}.`, open: () => jpOpenDoc(c, "co", x.id) }));
  (p.clientQs || [])
    .filter((q) => "open" === q.status)
    .forEach((q) => out.push({ key: "cq:" + q.id, title: `${q.by || "The client"} asked: ${String(q.text || "").slice(0, 70)}`, why: `Unanswered since ${fmt(String(q.at || "").slice(0, 10))}.`, open: () => clqAnswer(q.id), act: "Answer" }));
  return out;
}
function jpBill() {
  const host = document.getElementById("jbill-body");
  if (!host || "jbill" !== view) return;
  const p = S,
    c = jpClient(p),
    phone = jpPhone();
  if (!c) return void (host.innerHTML = '<h2 class="jp-vh">Contract and Billing</h2><p class="jp-empty">This job has no client yet. Set the client in Job Settings and its contract shows here.</p>');
  const J = jobFin(p),
    R = jpReady(p.id),
    N = jpNeeds(p),
    A = "function" == typeof pbAhead ? pbAhead(p.id) : { total: 0, lines: [] },
    rows = [
      ["Original contract", J.base, 400],
      ["Approved changes", J.coAmt, 400],
      ["Revised contract", J.contract, 700],
      ["Billed to date", J.billed, 400],
      ["Paid, in the bank", J.collected, 400],
      // recorded as paid with no bank line yet (jobFin's unbanked: the same reading Billing and the client page use)
      ["Recorded, not yet in the bank", J.unbanked || 0, 400],
      ["Retainage held", J.retHeld, 400],
      ["Left to bill", r2(J.contract - J.billed), 700],
    ],
    D = jpDocs(p),
    shown = D.filter((d) => "All" === jpDocKind || d.kind === jpDocKind),
    chips = ["All", "Estimates", "Change Orders", "Invoices", "Payments"],
    needs = `<section class="jp-card0" id="jb-needs"><div class="jp-ph"><h3>Needs You</h3>${!phone && R.amt && jpCanBill() ? `<button type="button" class="btn primary" data-jpdraft="1">Draft the Application, ${money(R.amt)}</button>` : ""}</div>${
      N.length
        ? N.map((n) => `<div class="jp-need ${n.open || "rtb" === n.key ? "jp-click" : ""}" data-jprow="${esc(n.key)}"><b>${esc(n.title)}</b><span>${esc(n.why)}</span>${n.open ? `<button type="button" class="btn sm jp-tap" data-jpneed="${esc(n.key)}">${esc(n.act || "Open")}</button>` : ""}</div>`).join("")
        : '<p class="jp-empty">Nothing on this contract needs you.</p>'
    }${phone && R.amt && jpCanBill() ? `<div class="jp-pf"><button type="button" class="btn primary jp-wide" data-jpdraft="1">Draft the Application, ${money(R.amt)}</button></div>` : ""}</section>`,
    contract = `<section class="jp-card0" id="jb-contract"><div class="jp-ph"><h3>The Contract</h3></div>${rows
      .map(([k, v, w]) => `<div class="jp-kv" data-label="${esc(k)}" data-amt="${r2(+v || 0)}"><span style="font-weight:${w}">${esc(k)}</span><b style="font-weight:${w}">${money(+v || 0)}</b></div>`)
      .join("")}${A.total ? `<p class="jp-note">Billed ahead of the work on ${A.lines.length} line${1 === A.lines.length ? "" : "s"}: ${money(A.total)}. Those lines hold until the work catches up.</p>` : ""}</section>`,
    chipRow = `<div class="jp-chips">${chips.map((l) => `<button type="button" class="jp-chip jp-tap ${jpDocKind === l ? "on" : ""}" data-jbchip="${esc(l)}" aria-pressed="${jpDocKind === l}">${esc(l)}</button>`).join("")}</div>`,
    list = phone
      ? `<div class="jp-card0 jp-docs" id="jb-docs">${
          shown.map((d) => `<button type="button" class="jp-doc jp-tap" data-jbdoc="${esc(d.k + ":" + d.x.id)}" data-date="${esc(d.date)}"><span class="jp-dl"><b>${esc(d.no)}</b><span>${esc(d.what)}</span></span><span class="jp-dr"><b>${money(d.amt)}</b><span class="${d.st[1]}">${esc(d.st[0])}</span></span></button>`).join("") ||
          '<p class="jp-empty">Nothing of this kind on this job.</p>'
        }</div>`
      : `<table class="jp-dt" id="jb-docs"><thead><tr><th>Kind</th><th>Number</th><th>What</th><th class="n">Amount</th><th>Status</th><th>Date</th></tr></thead><tbody>${
          shown.map((d) => `<tr data-jbdoc="${esc(d.k + ":" + d.x.id)}" data-date="${esc(d.date)}"><td class="dim">${esc(d.kind.replace(/s$/, ""))}</td><td><b>${esc(d.no)}</b></td><td>${esc(d.what)}</td><td class="n"><b>${money(d.amt)}</b></td><td class="${d.st[1]}"><b>${esc(d.st[0])}</b></td><td class="dim">${esc(d.date ? fmt(d.date) : "")}</td></tr>`).join("") ||
          '<tr><td colspan="6" class="jp-empty">Nothing of this kind on this job.</td></tr>'
        }</tbody></table>`,
    docs = `<section class="jp-card0" id="jb-docbox"><div class="jp-ph"><h3>Documents</h3>${phone ? "" : chipRow}</div>${phone ? chipRow : ""}${list}${jpMoreLinks(["billing"])}</section>`;
  host.innerHTML = `<h2 class="jp-vh">Contract and Billing</h2>${phone ? needs + contract + docs : `<div class="jp-two"><div class="jp-main">${needs}${docs}</div><aside class="jp-aside">${contract}</aside></div>`}`;
}

// ---- Budget: the Costs page, reshaped (the same figures: lineProfit and jobFin) --------------------------------------
function jpLines() {
  const p = S,
    J = jobFin(p),
    eac = new Map((J.eacLines || []).map((x) => [x.key, x])),
    pr = new Map();
  try {
    pgRows(p.id).forEach((r) => r.sv && r.sv.lineRef && pr.set(r.sv.lineRef, r));
  } catch (e) {}
  return lineProfit(p).map((r) => {
    const e = eac.get(r.key),
      g = pr.get(r.key),
      forecast = r2(e && null != e.eac ? +e.eac : Math.max(+r.budget || 0, (+r.actual || 0) + (+r.committed || 0))),
      done = g && g.pr && null != g.pr.pct && "cost" !== g.pr.basis ? Math.round(g.pr.pct) : null;
    return {
      key: r.key,
      r: r,
      name: (r.line && (r.line.item || r.line.desc)) || r.label,
      doc: r.doc ? r.doc.number : "",
      budget: +r.budget || 0,
      committed: +r.committed || 0,
      actual: +r.actual || 0,
      forecast: forecast,
      variance: r2(forecast - (+r.budget || 0)),
      spentPct: r.budget ? (100 * Math.max(r.actual, forecast)) / r.budget : 0,
      done: done,
      billed: null != r.billedPct ? Math.round(r.billedPct) : null,
    };
  });
}
// How far over its budget a line is, said one way everywhere (the card, the row, the tile, the This Job list, the margin
// panel): "13% over", never the share spent ("113%" read as 113% over).
const jpOverWord = (l) => `${Math.max(1, Math.round(l.spentPct - 100))}% over`;
// Cost on the job that sits on no estimate line (a bill, a card line or labour coded to the job but not to a line): the
// lines alone summed short of Cost to Date ($100,044 under $105,084). It is a row of its own, flagged: money with no line
// cannot be held to a budget or billed back.
function jpNoLine(J, L) {
  const a = r2((+J.actual || 0) - L.reduce((x, l) => x + l.actual, 0)),
    c = r2((+J.committed || 0) - L.reduce((x, l) => x + l.committed, 0));
  return Math.abs(a) < 0.5 && Math.abs(c) < 0.5
    ? null
    : { key: "__noline", noline: !0, name: "Not on an Estimate Line", doc: "", budget: 0, committed: c, actual: a, forecast: r2(a + c), variance: r2(a + c), spentPct: 0, done: null, billed: null };
}
function jpNoLineDetail(l) {
  const p = S,
    out = [],
    live = (b) => !["void", "rejected"].includes(b.status);
  (DB.bills || [])
    .filter((b) => b.projectId === p.id && !b.line && live(b))
    .forEach((b) => out.push([`${b.vendor || "Bill"}${b.number ? " " + b.number : ""} · ${fmt(b.date)}`, money("function" == typeof billCost ? billCost(b) : +b.amount || 0)]));
  (DB.txns || [])
    .filter((t) => t.projectId === p.id && !t.line && !t.billId && +t.amt < 0)
    .forEach((t) => out.push([`Card or bank: ${String(t.desc || t.vendor || "").slice(0, 40)} · ${fmt(t.date)}`, money(-t.amt)]));
  out.push(["Total with no estimate line (the rest is crew time and stock coded to the job only)", money(l.actual)]);
  out.push(["Put each on its line: cost with no line cannot be held to a budget or billed back. Money that leaks here cannot go to raises, bonuses, more staff, charity or extra value for the client.", ""]);
  return out;
}
function jpLineFlag(l) {
  if (l.noline) return [l.actual || l.committed ? "No estimate line" : "", "bad"];
  if (l.variance > 0.5) return [jpOverWord(l), "bad"];
  if (null != l.done && null != l.billed && l.done - l.billed > 5) return ["Billed behind", "warn"];
  if (null != l.done && null != l.billed && l.billed - l.done > 5) return ["Billed ahead", "warn"];
  return ["On budget", "ok"];
}
const jpPct = (n) => (null == n ? "—" : n + "%");
function jpLineDetail(l) {
  if (l.noline) return jpNoLineDetail(l);
  const out = [];
  (DB.pos || [])
    .filter((po) => !["void", "cancelled"].includes(po.status) && ((po.lines || []).some((x) => x.line === l.key || x.lineKey === l.key) || po.line === l.key))
    .forEach((po) => {
      const amt = (po.lines || []).filter((x) => x.line === l.key || x.lineKey === l.key).reduce((a, x) => a + (+x.qty || 0) * (+x.price || +x.rate || +x.cost || 0), 0);
      out.push([`${po.number} · ${po.vendor || ""}`, money(r2(amt || ("function" == typeof poTotal ? poTotal(po) : 0)))]);
    });
  try {
    clCosts(l.key).forEach((x) => out.push([`${"txn" === x.kind ? "Card or bank: " : "stock" === x.kind ? "" : ""}${x.ref || x.vendor}${x.vendor && x.ref && "stock" !== x.kind ? " · " + x.vendor : ""} · ${fmt(x.date)}`, money(x.amount)]));
  } catch (e) {}
  try {
    const f = lineFin(l.key);
    f && f.laborAmt && out.push([`Our crew, ${r2(f.hours || 0)} h`, money(f.laborAmt)]);
  } catch (e) {}
  const w = jpReady(S.id).W.find((x) => x.sv && x.sv.lineRef === l.key);
  w && w.amount && out.push([w.held ? "Measured, held (billed ahead)" : "Ready to bill", money(w.amount)]);
  l.variance > 0.5 && out.push(["Over its budget", "+" + money(l.variance)]);
  return out.length ? out : [["Nothing bought or spent on this line yet", ""]];
}
// The old line table and tiles are Budget's rows and figures now: emptied, not hidden. A hidden copy is text a person
// cannot see and a check can still read. The tile pass refills #jc-kpis after renderCosts, so this runs again after the
// whole draw. The cost-code table, WIP and transactions stay.
function jpCostsClear() {
  const v = document.getElementById("v-costs");
  if (!v || "costs" !== view) return;
  ["#jc-kpis", "#jl-table"].forEach((s) => {
    const e = v.querySelector(s);
    e && ((e.innerHTML = ""), (e.style.display = "none"));
  });
  const jf = v.querySelector("#jl-filter"),
    jr = jf && jf.closest(".row");
  jr && jr.remove();
}
// On the phone the page's lead line is hidden (the header's second line says what the page is), so on a job's pages it
// is emptied there and put back on a wider screen: hidden text is text a check can read and a person cannot.
function jpLeads() {
  const v = document.querySelector(".view.on");
  if (!v) return;
  const phone = jpPhone();
  v.querySelectorAll(":scope > .ph .lead").forEach((l) => {
    if (phone) {
      const t = l.textContent;
      t && ((l.dataset.jpLead = t), (l.textContent = ""));
    } else if (!l.textContent && l.dataset.jpLead) l.textContent = l.dataset.jpLead;
  });
}
function jpBudget() {
  const v = document.getElementById("v-costs");
  if (!v || "costs" !== view || !S) return;
  let host = document.getElementById("jp-budget");
  host || ((host = document.createElement("div")), (host.id = "jp-budget"), (host.className = "jp-budget jp-keep"));
  const ph = v.querySelector(":scope > .ph");
  ph ? ph.nextElementSibling !== host && ph.after(host) : v.firstElementChild !== host && v.prepend(host);
  jpCostsClear();
  const lead = v.querySelector(":scope > .ph .lead");
  lead && (lead.textContent = "What the job costs us, line by line: the budget with approved changes, what is committed, what is spent and the forecast to finish.");
  const p = S,
    J = jobFin(p),
    L0 = jpLines(),
    NL = jpNoLine(J, L0),
    L = NL ? L0.concat([NL]) : L0,
    O = L0.filter((l) => l.variance > 0.5),
    A = "function" == typeof pbAhead ? pbAhead(p.id) : { total: 0 },
    phone = jpPhone(),
    U = ("function" == typeof spUnbilled ? spUnbilled(p.id) : []).filter((r) => ["reimbursable", "floated"].includes(r.kind)),
    uAmt = r2(U.reduce((a, r) => a + (+r.gap || 0), 0)),
    est = Math.round(J.estGPPct || 0),
    plan = Math.round(J.plannedGPPct || 0),
    oSay = O.length ? `${O.length} line${1 === O.length ? "" : "s"} over budget · ${O.map((o) => `${o.name.split(/ [—–-] /)[0]}, ${money(o.variance)}`).join("; ")}` : "No line is over its budget",
    margin = `<div class="jp-card0 jp-margin" id="jp-margin"><span class="jp-mk">Margin at completion</span><div class="jp-mv"><b>${est}%</b><span class="${est < plan ? "warn" : "ok"}">Plan ${plan}%</span></div><span class="jp-ms">${esc(oSay)}</span></div>`,
    kpis = phone
      ? margin
      : `<div class="jp-kpis">${[
          ["Margin at Completion", `${est}%`, `Plan ${plan}%`, est < plan ? "warn" : "", "jp-margin"],
          ["Cost to Date", money(J.actual), "Bills, bank and card lines, stock and labor", "", ""],
          ["Over Budget", `${O.length} line${1 === O.length ? "" : "s"}`, O.length ? `${O[0].name.split(/ [—–-] /)[0]}, +${money(O[0].variance)}` : "every line within its budget", O.length ? "bad" : "", ""],
          ["Billed Ahead of the Work", money(A.total || 0), `Over-Billed (WIP) ${money(J.over || 0)}`, "", ""],
        ]
          .map(([k, val, s, tone, id]) => `<div class="jp-kpi"${id ? ` id="${id}"` : ""}><span>${esc(k)}</span><b class="${tone}">${esc(val)}</b><span>${esc(s)}</span></div>`)
          .join("")}</div>`,
    detail = (l) => `<div class="jp-detail">${jpLineDetail(l).map(([k, val]) => `<div><span>${esc(k)}</span><b>${esc(val)}</b></div>`).join("")}</div>`,
    attrs = (l) => `data-jpline="${esc(l.key)}" data-budget="${l.budget}" data-committed="${l.committed}" data-actual="${l.actual}"`,
    lines = phone
      ? `<div class="jp-bcards">${L.map((l) => {
          const f = jpLineFlag(l),
            open = jpBudOpen === l.key;
          return `<div class="jp-bcard ${"bad" === f[1] ? "over" : ""}" ${attrs(l)}><button type="button" class="jp-bbtn" data-jpopen="${esc(l.key)}" aria-expanded="${open}"><span class="jp-bt"><span class="jp-bn"><b>${esc(l.name)}</b> <span class="jp-bdoc">${esc(l.doc)}</span></span><b class="${f[1]}">${esc(f[0])}</b></span><span class="jp-bgrid">${[
            ["Budget", money(l.budget)],
            ["Committed", l.committed ? money(l.committed) : "—"],
            ["Actual", l.actual ? money(l.actual) : "—"],
            ["Forecast", money(l.forecast)],
            ["Variance", l.variance ? (l.variance > 0 ? "+" : "") + money(l.variance) : "—"],
            ["Done", jpPct(l.done)],
            ["Billed", jpPct(l.billed)],
          ]
            .map(([k, val]) => `<span class="jp-bf"><span class="jp-bk">${k}</span><b>${val}</b></span>`)
            .join("")}</span></button>${open ? detail(l) : ""}</div>`;
        }).join("")}</div>`
      : `<table class="jp-bt" id="jp-btable"><thead><tr><th>Line</th><th class="n">Budget</th><th class="n">Committed</th><th class="n">Actual</th><th class="n">Forecast</th><th class="n">Variance</th><th class="n">% Done</th><th class="n">% Billed</th></tr></thead><tbody>${L.map((l) => {
          const f = jpLineFlag(l),
            open = jpBudOpen === l.key;
          return `<tr class="${"bad" === f[1] ? "over" : ""} ${open ? "open" : ""}" ${attrs(l)}><td><button type="button" class="jp-lbtn" data-jpopen="${esc(l.key)}" aria-expanded="${open}"><b>${esc(l.name)}</b><span class="jp-bdoc">${esc(l.doc)}${"On budget" === f[0] ? "" : ` · <span class="${f[1]}">${esc("bad" === f[1] ? (l.noline ? "cost with no estimate line" : `${f[0]} budget`) : f[0].toLowerCase())}</span>`}</span></button>${open ? detail(l) : ""}</td><td class="n">${money(l.budget)}</td><td class="n">${l.committed ? money(l.committed) : "—"}</td><td class="n">${l.actual ? money(l.actual) : "—"}</td><td class="n">${money(l.forecast)}</td><td class="n ${l.variance > 0.5 ? "bad" : ""}"><b>${l.variance ? (l.variance > 0 ? "+" : "") + money(l.variance) : "—"}</b></td><td class="n">${jpPct(l.done)}</td><td class="n">${jpPct(l.billed)}</td></tr>`;
        }).join("")}</tbody><tfoot><tr><td>Total</td>${["budget", "committed", "actual", "forecast", "variance"].map((k) => `<td class="n">${money(r2(L.reduce((a, l) => a + l[k], 0)))}</td>`).join("")}<td></td><td></td></tr></tfoot></table>`,
    back = U.length
      ? `<div class="jp-billback" id="jp-billback"><b>Bought for the Client, Not Billed Back</b><span>${money(uAmt)} of ${esc(U.map((r) => ((r.line && (r.line.item || r.line.desc)) || r.label || "").split(/ [—–-] /)[0]).join(", "))} bought or delivered, not on an invoice yet. Money not billed back cannot go to raises, bonuses, more staff, charity or extra value for the client.</span>${jpCanBill() ? '<button type="button" class="jp-link jp-tap" data-jpdraft="1">Add to the Next Application</button>' : ""}</div>`
      : `<div class="jp-billback ok" id="jp-billback"><b>Bought for the Client, Not Billed Back</b><span>Nothing: everything bought for the client is on an invoice.</span></div>`;
  host.innerHTML = `${kpis}<div class="jp-cap">By Estimate Line · ${phone ? "tap" : "click"} one for what is behind it</div>${L.length ? lines : '<p class="jp-empty">No estimate lines on this job yet. Convert the signed estimate, or Load Budget from Estimate, and each line shows here.</p>'}${back}`;
}

// ---- Decisions: everything waiting on an answer --------------------------------------------------------------------
function jpDecRows(p) {
  const td = today(),
    c = jpClient(p),
    who = (o) => ("Client" === o ? jpFirst(c) : /architect|designer/i.test(o || "") ? "the architect" : o || "nobody named"),
    out = [];
  withProject(p, () => {
    (p.decisions || [])
      .filter((d) => !["made", "done", "decided"].includes(d.status))
      .forEach((d) => {
        const due = decDue(d),
          blocks = "mat" === d.kind ? (mat(d.ref) || {}).name : (task(d.ref) || {}).name;
        out.push({ key: "dec:" + d.id, kind: "Client" === d.owner ? "Selections" : "Design", title: d.name, who: who(d.owner), due: due, blocks: blocks || "", act: "Client" === d.owner ? `Ask ${jpFirst(c)}` : "Chase", run: () => openEditor("dec", d.id) });
      });
    ((DB.sel && DB.sel.items) || [])
      .filter((it) => it.projectId === p.id && "sel" === it.stage)
      .forEach((it) => {
        let due = "",
          blocks = "";
        try {
          due = selOrderBy(it) || "";
          blocks = (selTask(it) || {}).name || "";
        } catch (e) {}
        out.push({ key: "sel:" + it.id, kind: "Selections", title: `Approve ${it.name}${it.room ? `, ${it.room}` : ""}`, who: jpFirst(c), due: due, blocks: blocks || "its order", act: "Open", run: () => jpGo("sel") });
      });
    (p.issues || [])
      .filter((i) => "rfi" === i.type && "open" === i.status)
      .forEach((i) => out.push({ key: "iss:" + i.id, kind: "RFIs", title: `${i.code ? i.code + ": " : ""}${i.title}`, who: who(i.owner), due: issueDue(i), blocks: i.taskId ? (task(i.taskId) || {}).name || "" : "", act: "Answer", run: () => jpRfiAnswer(i.id) }));
    try {
      smRows(p)
        .filter((R) => SM_OPEN(R.s) && !["approved", "noted", "closed"].includes(R.s.status))
        .forEach((R) => out.push({ key: "subm:" + R.s.id, kind: "Submittals", title: R.s.title, who: (R.B && R.B.who) || "nobody named", due: R.D.approveBy || "", blocks: (R.D.tk && R.D.tk.name) || "", act: "Open", run: () => (jpGo("subm"), "function" == typeof smOpen && smOpen(R.s.id)) }));
    } catch (e) {}
  });
  out.forEach((r) => (r.overdue = !!r.due && r.due < td));
  return out.sort((a, b) => (b.overdue ? 1 : 0) - (a.overdue ? 1 : 0) || String(a.due || "9999").localeCompare(String(b.due || "9999")));
}
function jpDec() {
  const host = document.getElementById("jdec-body");
  if (!host || "jdec" !== view) return;
  const p = S,
    R = jpDecRows(p),
    shown = R.filter((r) => "All" === jpDecKind || r.kind === jpDecKind),
    td = today();
  jpActs = {};
  shown.forEach((r) => (jpActs[r.key] = r.run));
  const dueWord = (r) => (!r.due ? ["No date set", ""] : r.overdue ? [`Overdue since ${fmt(r.due)}`, "bad"] : dayDiff(td, r.due) <= 6 ? [`Due ${jpDay(r.due)}`, "warn"] : [`Due ${fmt(r.due)}`, ""]);
  host.innerHTML = `<h2 class="jp-vh">Decisions</h2><div class="jp-toolbar"><div class="jp-chips">${["All", "Selections", "Design", "RFIs", "Submittals"]
    .map((l) => `<button type="button" class="jp-chip jp-tap ${jpDecKind === l ? "on" : ""}" data-jdchip="${l}" aria-pressed="${jpDecKind === l}">${l}</button>`)
    .join("")}</div><span class="jp-grow"></span>${jpMay("field") || jpMay("dec") ? '<button type="button" class="btn jp-tap" id="jd-newrfi">New RFI</button>' : ""}</div><div class="jp-dlist">${
    shown
      .map((r) => {
        const d = dueWord(r);
        return `<div class="jp-drow jp-click ${r.overdue ? "od" : ""}" data-jdrow="${esc(r.key)}" data-kind="${esc(r.kind)}" data-overdue="${r.overdue ? 1 : 0}"><div class="jp-dh"><span class="jp-dk">${esc("RFIs" === r.kind ? "RFI" : "Submittals" === r.kind ? "Submittal" : r.kind)}</span><span class="jp-grow"></span><span class="jp-dd ${d[1]}">${esc(d[0])}</span></div><b>${esc(r.title)}</b><span class="jp-dw">Waiting on <b>${esc(r.who)}</b>${r.blocks ? ` · blocks ${esc(r.blocks)}` : ""}</span><div><button type="button" class="btn sm jp-tap" data-jdact="${esc(r.key)}">${esc(r.act)}</button></div></div>`;
      })
      .join("") || `<p class="jp-empty">Nothing on this job is waiting on an answer${"All" === jpDecKind ? "" : " of this kind"}.</p>`
  }</div>${jpMoreLinks(["dec", "subm", "sel"])}`;
}
// The RFI: the issue record of type rfi (the Field page's "Plan question / RFI"), with who owes it, by when, what it
// blocks and the answer. New RFI and Answer are the two writes; each toasts with Open.
function jpRfiNew() {
  const p = S,
    tasks = (p.tasks || []).filter((t) => "done" !== t.status).sort((a, b) => String(a.start).localeCompare(String(b.start)));
  mbModal(
    "New RFI",
    `${mbF("Question", '<input data-f="title" placeholder="e.g. Beam drop at the 3rd floor: 2 or 3 inches?">')}${mbF(
      "Who owes the answer",
      `<select data-f="owner">${["Architect / designer", "Engineer", "SmartDesigns", "Client", "Sub"].map((o) => `<option>${o}</option>`).join("")}</select>`,
    )}${mbF("Answer needed by", `<input type="date" data-f="due" value="${addWork(today(), 2)}">`)}${mbF(
      "What it blocks",
      `<select data-f="taskId"><option value="">Nothing on the schedule yet</option>${tasks.map((t) => `<option value="${t.id}">${esc(t.name)} · starts ${fmt(t.start)}</option>`).join("")}</select>`,
    )}${mbF("Detail", '<textarea data-f="notes" rows="3" placeholder="Sheet, location, what the field sees"></textarea>')}`,
    {
      submit: "Add the RFI",
      onSubmit: (f) => {
        const title = String(f.title || "").trim();
        if (!title) return toast("Write the question"), !1;
        const i = { id: uid("is"), title: title, type: "rfi", status: "open", owner: f.owner || "Architect / designer", taskId: f.taskId || "", due: f.due || "", notes: f.notes || "", commId: "", by: (currentUser() || {}).name || DB.me || "", at: appNowIso(), scope: f.taskId ? { kind: "task", id: f.taskId } : null };
        (p.issues = p.issues || []).push(i);
        try {
          withProject(p, () => log(`RFI: ${title} → ${i.owner}${i.due ? ", answer by " + fmt(i.due) : ""}`));
          audit("issue", i.id, "rfi-created", null, { title: title, owner: i.owner, due: i.due });
        } catch (e) {}
        save(), render(), toast(`RFI added: ${title}`, () => jpGo("jdec"));
      },
    },
  );
}
function jpRfiAnswer(id) {
  const p = S,
    i = (p.issues || []).find((x) => x.id === id);
  if (!i) return;
  mbModal("Answer the RFI", `<p class="small muted" style="margin:0 0 8px"><b>${esc(i.title)}</b>${i.notes ? ` · ${esc(i.notes)}` : ""}</p>${mbF("The answer", '<textarea data-f="answer" rows="3" placeholder="Short and definite: it goes to the field"></textarea>')}`, {
    submit: "Record the Answer",
    onSubmit: (f) => {
      const a = String(f.answer || "").trim();
      if (!a) return toast("Write the answer"), !1;
      (i.answer = a), (i.status = "answered"), (i.answeredBy = (currentUser() || {}).name || DB.me || ""), (i.answeredAt = appNowIso());
      try {
        withProject(p, () => log(`RFI answered: ${i.title} — ${a} (${i.answeredBy})`));
        audit("issue", i.id, "rfi-answered", null, { answer: a });
      } catch (e) {}
      save(), render(), toast(`Answered: ${i.title}`, () => jpGo("field"));
    },
  });
}

// ---- Site: the crew's questions, today on site, coming to site ------------------------------------------------------
function jpQuestions(p) {
  try {
    return (DB.field.raises || []).filter((r) => r.projectId === p.id && "answered" !== r.status).sort((a, b) => String(a.at).localeCompare(String(b.at)));
  } catch (e) {
    return [];
  }
}
function jpDayHours(pid) {
  const p = (DB.projects || []).find((x) => x.id === pid),
    h = p && p.project && p.project.hours;
  if (h && h.start && h.end) {
    const m = (s) => +s.split(":")[0] * 60 + +(s.split(":")[1] || 0);
    return Math.max(1, (m(h.end) - m(h.start) - (+h.lunch || 0)) / 60);
  }
  return 10;
}
// One person on two jobs' logs for more hours in a day than a site day holds: payroll and job cost double until one log
// is right. The rule reads every log of the day, whichever job wrote first.
function jpCrewClashes(pid) {
  const logs = (DB.field && DB.field.logs) || [],
    out = [],
    seen = new Set(),
    id = (x) => x.empId || x.name;
  logs
    .filter((l) => l.projectId === pid)
    .forEach((l) =>
      (l.crew || []).forEach((cw) => {
        const w = id(cw),
          others = logs.filter((o) => o !== l && o.date === l.date && o.projectId !== pid && (o.crew || []).some((x) => id(x) === w));
        if (!others.length) return;
        const there = others.map((o) => ({ pid: o.projectId, name: jpShort((DB.projects || []).find((x) => x.id === o.projectId)), hours: +((o.crew.find((x) => id(x) === w) || {}).hours || 0) })),
          tot = r2((+cw.hours || 0) + there.reduce((a, x) => a + x.hours, 0)),
          day = Math.max(jpDayHours(pid), ...others.map((o) => jpDayHours(o.projectId)));
        if (tot <= day + 0.01 || seen.has(w + "|" + l.date)) return;
        seen.add(w + "|" + l.date), out.push({ name: cw.name, date: l.date, hours: tot, day: r2(day), here: +cw.hours || 0, there: there });
      }),
    );
  return out.sort((a, b) => String(b.date).localeCompare(String(a.date)));
}
function jpClashSay(x, p) {
  return `${x.name} is on ${jpShort(p)}'s log for ${r2(x.here)} h and on ${x.there.map((t) => `${t.name}'s for ${r2(t.hours)} h`).join(" and ")} on ${fmt(x.date)}: ${r2(x.hours)} h in a ${x.day} h site day.`;
}
// one line per person: the latest day said in full, the other days listed
function jpClashGroups(X) {
  const by = new Map();
  X.forEach((x) => (by.get(x.name) || by.set(x.name, []).get(x.name)).push(x));
  return [...by.values()];
}
// the warning a log carries when it is signed (dlSubmit) and on the Site of both jobs
function jpLogWarn(rec) {
  if (!rec || !rec.projectId) return "";
  const p = (DB.projects || []).find((x) => x.id === rec.projectId),
    X = jpCrewClashes(rec.projectId).filter((x) => x.date === rec.date);
  return X.length ? X.map((x) => jpClashSay(x, p)).join(" ") + " One of the logs is wrong: payroll and job cost count both until it is fixed." : "";
}
function jpSite() {
  const host = document.getElementById("jsite-body");
  if (!host || "jsite" !== view) return;
  const p = S,
    td = today(),
    end = addWork(td, 7),
    Q = jpQuestions(p),
    X = jpCrewClashes(p.id),
    log = ((DB.field && DB.field.logs) || []).find((l) => l.projectId === p.id && l.date === td),
    tm = (DB.time || []).filter((t) => t.projectId === p.id && t.date === td),
    crew = log && (log.crew || []).length ? log.crew.map((c) => `${c.name} ${r2(+c.hours || 0)} h`) : [...new Set(tm.map((t) => t.name || ((DB.employees || []).find((e) => e.id === t.empId) || {}).name).filter(Boolean))],
    fromLog = !!(log && (log.crew || []).length),
    hrs = log && (log.crew || []).length ? r2(log.crew.reduce((a, c) => a + (+c.hours || 0), 0)) : r2(tm.reduce((a, t) => a + (+t.hours || ("function" == typeof hoursOf && t.out ? hoursOf(t) : 0)), 0)),
    // what is being worked: the day's log first, else the tasks under way (not every bar that spans today)
    running = (p.tasks || []).filter((t) => "done" !== t.status && t.start <= td && t.end >= td && "milestone" !== t.kind),
    underway = running.filter((t) => "in-progress" === t.status),
    active = log && (log.done || []).length ? log.done.map((x) => ({ name: String(x).split(":")[0] })) : underway.length ? underway : running,
    photos = (DB.photos || []).filter((x) => x.projectId === p.id && String(x.at || x.date || x.takenAt || "").slice(0, 10) === td).length,
    probs = Q.filter((r) => ["blocker", "noshow", "incident"].includes(r.type) && String(r.at).slice(0, 10) === td).map((r) => r.title).concat(log && log.notes ? [log.notes] : []),
    coming = [];
  withProject(p, () => {
    (p.inspections || []).filter((i) => i.date && i.date > td && i.date <= end && !["passed", "failed"].includes(i.status)).forEach((i) => coming.push([i.date, `${i.agency ? i.agency + " " : ""}${i.name}`]));
    (p.materials || []).forEach((m) => {
      if (["on-site", "installed"].includes(m.status)) return;
      let d = "";
      try {
        d = m.eta || matDates(m).needBy;
      } catch (e) {}
      d && d > td && d <= end && coming.push([d, `${m.name}${m.eta ? " on site" : ", needed on site"}`]);
    });
    ((DB.field && DB.field.subs) || []).filter((s) => s.projectId === p.id && s.date > td && s.date <= end).forEach((s) => coming.push([s.date, `${s.vendor}${s.trade ? ", " + s.trade.toLowerCase() : ""}`]));
  });
  coming.sort((a, b) => a[0].localeCompare(b[0]));
  const qOpen = (r) => {
      const u = (DB.users || []).find((x) => x.name === r.by);
      return u && u.phone ? `<a class="btn sm jp-tap" href="tel:${esc(String(u.phone).replace(/[^\d+]/g, ""))}">Call ${esc(r.by)}</a>` : jpMay("field") ? `<button type="button" class="btn sm jp-tap" data-jpgo="field">Open</button>` : "";
    },
    kv = (k, val) => `<div class="jp-kv2"><span>${esc(k)}</span><span>${esc(val)}</span></div>`;
  host.innerHTML = `<h2 class="jp-vh">Site</h2>${
    X.length
      ? `<div class="jp-clash" id="js-clash" role="alert">${JP_IC.warn}<div><b>Crew hours on two jobs</b>${jpClashGroups(X)
          .map((g) => `<span>${esc(jpClashSay(g[0], p))}${g.length > 1 ? ` Also on ${esc(g.slice(1).map((x) => `${fmt(x.date)} (${r2(x.hours)} h)`).join(", "))}.` : ""}</span>`)
          .join("")}<span>One of the logs is wrong: payroll and job cost count both until it is fixed.</span></div></div>`
      : ""
  }<div class="jp-cap">Questions from the Crew · ${Q.length} open</div><div class="jp-qs" id="js-q">${
    Q.map((r) => `<div class="jp-q jp-click" data-jsq="${esc(r.id)}"><span class="jp-ck">${esc(r.by)} · ${esc(String(r.at).slice(0, 10) === td ? stampTime(r.at) : fmt(String(r.at).slice(0, 10)))}</span><b>${esc(r.title)}</b>${r.note ? `<span class="jp-cw">${esc(r.note)}</span>` : ""}<div class="jp-ca"><button type="button" class="btn sm jp-tap" data-jsans="${esc(r.id)}">Answer</button>${qOpen(r)}</div></div>`).join("") ||
    '<p class="jp-empty">No open questions from the crew on this job.</p>'
  }</div><div class="jp-cap">Today on Site · ${esc(fmtL(td))}</div><div class="jp-card0" id="js-today">${kv("Crew", crew.length ? `${crew.join(", ")}${hrs && (!fromLog || crew.length > 1) ? ` · ${hrs} h in all` : ""}` : "Nobody logged or clocked in yet")}${kv("Progress", active.length ? active.slice(0, 4).map((t) => t.name).join("; ") + (active.length > 4 ? `; and ${active.length - 4} more` : "") : "Nothing scheduled to run today")}${kv("Photos", photos ? `${photos} today` : "None today")}${kv("Problems", probs.length ? probs.join(" · ") : "None reported")}</div><div class="jp-cap">Coming to Site</div><div class="jp-card0" id="js-coming">${
    coming.map(([d, w]) => kv(jpDay(d), w)).join("") || '<p class="jp-empty">Nothing booked to come to site in the next week.</p>'
  }</div>${jpMoreLinks(["field", "req"])}`;
}

// ---- links under the other tabs: the pages that live there ----------------------------------------------------------
function jpTabLinks() {
  const put = (vid, id, vs, where) => {
    const v = document.getElementById("v-" + vid);
    if (!v) return;
    v.querySelectorAll(":scope #" + id).forEach((e) => e.remove());
    if (view !== vid || !jpOn()) return;
    const html = jpMoreLinks(vs, id);
    if (!html) return;
    const at = where(v);
    at ? at.insertAdjacentHTML("afterend", html) : v.insertAdjacentHTML("afterbegin", html);
  };
  put("sched", "jp-schedlinks", ["tasks"], (v) => v.querySelector(":scope > .ph"));
  put("files", "jp-doclinks", ["plans", "insp", "photos", "inbox", "sfile"], (v) => v.querySelector(":scope > .ph"));
  put("proc", "jp-buylinks", ["mat", "recv", "po"], (v) => v.querySelector(".bb-ph0") || v.querySelector(".ph"));
  // the Buy Board's pill counts every job; on the job's Purchasing it counts the job's rows (the board's own chips)
  const pill = "proc" === view && jpOn() && document.querySelector("#v-proc .bb-latepill");
  if (pill) {
    // the same rows the rail's Buy Board count reads (PRED.buyNeeds: late or to order this week), this job's only
    let need = [];
    try {
      need = PRED.buyNeeds.rows().filter((r) => r.p && r.p.id === S.id);
    } catch (e) {}
    const late = jpLate(S.id).length,
      week = Math.max(0, need.length - late);
    pill.removeAttribute("data-ovneeds"), pill.removeAttribute("data-ocbadge"), pill.classList.toggle("on", !!late);
    pill.textContent = late + week ? `${late + week} ${week ? "late or to order this week" : "late"} on this job` : "Nothing late on this job";
  }
}

// ---- drawing and wiring ---------------------------------------------------------------------------------------------
{
  const base = render;
  render = function () {
    // the Buy Board under a job is that job's
    try {
      jpGrant();
      "proc" === view && "jobs" === mnLastGrp && S && "undefined" != typeof bbProj && bbProj && (bbProj = S.id);
      "undefined" != typeof dashAll && "dash" === view && (dashAll = !1);
    } catch (e) {}
    const r = base.apply(this, arguments);
    try {
      const jon = jpOn();
      "dash" === view && jon && jpDashClear();
      jon && (jpCostsClear(), jpLeads());
      jpHead(), jpOverview(), jpBill(), jpDec(), jpSite(), jpTabLinks();
      // the job's + is the job's New; the top bar's New would be a second one on the same screen
      const on = jpOn();
      ["tb-new", "fab"].forEach((id) => {
        const el = document.getElementById(id);
        el && (on ? (el.dataset.jpHid = "1", (el.style.display = "none")) : el.dataset.jpHid && (delete el.dataset.jpHid, (el.style.display = "")));
      });
    } catch (e) {
      console.warn("job page", e);
    }
    return r;
  };
}
{
  const base = renderCosts;
  renderCosts = function () {
    const r = base.apply(this, arguments);
    try {
      jpBudget();
    } catch (e) {
      console.warn("budget", e);
    }
    return r;
  };
}
// a daily log that puts someone on two jobs over a site day is signed with the warning (the office sees it on Site)
if ("function" == typeof dlSubmit) {
  const base = dlSubmit;
  dlSubmit = function (dr, p) {
    const r = base.apply(this, arguments);
    try {
      const rec = ((DB.field && DB.field.logs) || []).find((l) => p && l.projectId === p.id && l.date === dr.date),
        w = jpLogWarn(rec);
      w && toast(`Log signed. Check the hours: ${w}`, { label: "Open Site", run: () => jpOpenJob(p.id, "jsite") }, 12e3);
    } catch (e) {}
    return r;
  };
}
document.addEventListener(
  "click",
  (e) => {
    const t = e.target && e.target.closest ? e.target : null;
    if (!t) return;
    const at = (s) => t.closest(s);
    let b;
    if ((b = at("#jp-new"))) return e.preventDefault(), (jpMenuOpen = !jpMenuOpen), jpHead();
    if ((b = at("[data-jpnew]"))) {
      e.preventDefault(), e.stopPropagation(), (jpMenuOpen = !1);
      const it = jpNewItems().find((x) => x[0] === b.dataset.jpnew);
      jpHead();
      return void (it && it[3]());
    }
    jpMenuOpen && !at("#jp-newmenu") && ((jpMenuOpen = !1), jpHead());
    if ((b = at("#jp-ask"))) {
      const q = `About ${jpName()}: `;
      "function" == typeof paOpen ? paOpen("chat") : setView("pa");
      return void setTimeout(() => {
        const i = [...document.querySelectorAll("#v-pa textarea, #v-pa input[type=text], #v-pa input:not([type])")].find((x) => x.getClientRects().length);
        i && (i.value || ((i.value = q), i.dispatchEvent(new Event("input", { bubbles: !0 }))), i.focus());
      }, 80);
    }
    if ((b = at("[data-jpback]"))) {
      e.preventDefault();
      return void ("dash" === view && jpSub ? ((jpSub = ""), render()) : "dash" === view ? jpGo("ovjobs") : jpGo(JP_UNDER[view] && JP_UNDER[view] !== view && jpTab() !== view ? jpTab() : "dash"));
    }
    if ((b = at("#jp-ov button.gl[data-tl]"))) {
      e.preventDefault(), e.stopPropagation();
      const id = b.dataset.tl;
      return void (jpPhone() ? ("margin" === id ? jpGo("costs") : ((jpSub = id), render(), window.scrollTo(0, 0))) : ((jpPanel = id), render()));
    }
    if ((b = at("[data-jpsec]"))) return e.preventDefault(), void jpGo(b.dataset.jpsec);
    if ((b = at("[data-jpgo]"))) return e.preventDefault(), void jpGo(b.dataset.jpgo);
    if ((b = at("[data-jpact]"))) {
      e.preventDefault(), e.stopPropagation();
      const f = jpActs[b.dataset.jpact];
      return void (f && f());
    }
    if ((b = at("[data-jptask]"))) return e.preventDefault(), void ("function" == typeof tkOpen ? tkOpen(b.dataset.jptask) : jpGo("tasks"));
    if ((b = at("[data-jpinsp]"))) return e.preventDefault(), void openEditor("insp", b.dataset.jpinsp);
    if ((b = at("[data-jpdraft]"))) return e.preventDefault(), void blOpenProgress(S.id, !0);
    if ((b = at("[data-jbchip]"))) return e.preventDefault(), (jpDocKind = b.dataset.jbchip), void render();
    if ((b = at("[data-jdchip]"))) return e.preventDefault(), (jpDecKind = b.dataset.jdchip), void render();
    if ((b = at("[data-jbdoc]"))) {
      e.preventDefault();
      const [k, id] = b.dataset.jbdoc.split(":"),
        c = jpClient(),
        d = jpDocs(S).find((x) => x.k === k && x.x.id === id);
      return void (c && d && ("payment" === k ? d.inv && jpOpenDoc(c, "invoice", d.inv.id) : jpOpenDoc(c, k, id)));
    }
    if ((b = at("[data-jpneed]"))) {
      e.preventDefault();
      const n = jpNeeds(S).find((x) => x.key === b.dataset.jpneed);
      return void (n && n.open && n.open());
    }
    if ((b = at("[data-jdact]"))) {
      e.preventDefault(), e.stopPropagation();
      const f = jpActs[b.dataset.jdact];
      return void (f && f());
    }
    if ((b = at("#jd-newrfi"))) return e.preventDefault(), void jpRfiNew();
    if ((b = at("[data-jsans]"))) {
      e.preventDefault();
      const r = jpQuestions(S).find((x) => x.id === b.dataset.jsans);
      return void (r && fAnswerRaise(r));
    }
    if ((b = at("[data-jpopen]")) || ((b = at("[data-jpline]")) && !at("a, button"))) {
      const k = b.dataset.jpopen || b.dataset.jpline;
      return e.preventDefault(), (jpBudOpen = jpBudOpen === k ? "" : k), void render();
    }
    // a row is its record: the whole row does what its button does
    if (!at("a, button, input, select, textarea") && (b = at("[data-jprow], [data-jdrow], [data-jsq]"))) {
      const btn = b.querySelector("[data-jpact], [data-jpneed], [data-jdact], [data-jsans]");
      if (btn) return e.preventDefault(), void btn.click();
      if ("rtb" === b.dataset.jprow && jpCanBill()) return e.preventDefault(), void blOpenProgress(S.id, !0);
    }
  },
  !0,
);
document.addEventListener("keydown", (e) => {
  "Escape" === e.key && jpMenuOpen && ((jpMenuOpen = !1), jpHead());
});
// The phone's bottom bar, the header's Messages, Ask and Search, and the field's tab bar are not the job: a page opened
// from them is the firm's (the coordinator's Buy Board shortcut is every job's board, not the last job's)
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("#mtabs [data-mv], #tabbar [data-tab], #tb-chat, #tb-ask, #btn-search") : null;
    if (!b) return;
    try {
      mnLastGrp = "";
    } catch (x) {}
    "proc" === (b.dataset.mv || b.dataset.tab) && "undefined" != typeof bbProj && (bbProj = "");
  },
  !0,
);

// ---- the look ---------------------------------------------------------------------------------------------------------
(() => {
  const css = `
.jp-head{background:var(--paper);border-bottom:1px solid var(--rule);padding:16px var(--gutter,32px) 10px;display:flex;flex-direction:column;gap:4px}
.jp-head[hidden]{display:none}
.jp-row{display:flex;align-items:center;gap:12px;min-width:0}
.jp-grow{flex:1}
.jp-name{display:flex;align-items:center;gap:6px;min-width:0;position:relative}
.jp-name .projsel{margin:0;padding:0;background:none}
.jp-name .projsel::after{display:none}
.jp-name select{appearance:none;-webkit-appearance:none;border:0;border-radius:0;background:transparent;width:auto;font:inherit;font-size:24px;font-weight:700;color:var(--ink);padding:0 26px 0 0;margin-right:-24px;max-width:100%;min-height:44px;cursor:pointer;text-overflow:ellipsis}
.jp-name .jp-chev{pointer-events:none;display:flex;color:var(--ink-3)}
.jp-sub{font-size:14px;color:var(--ink-3)}
.jp-ask{height:40px}
.jp-newwrap{position:relative}
.jp-ib{width:44px;height:44px;border-radius:10px;border:1px solid var(--rule);background:var(--paper);color:var(--ink);display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0}
.jp-ib[aria-expanded=true]{background:var(--accent-2)}
.jp-menu{position:absolute;right:0;top:50px;width:260px;background:var(--paper);border:1px solid var(--rule);border-radius:12px;box-shadow:0 12px 32px rgba(17,26,46,.16);padding:6px;z-index:60;display:flex;flex-direction:column}
.jp-nh{padding:8px 12px 6px;font-size:12px;color:var(--ink-3)}
.jp-mi{display:flex;align-items:center;min-height:44px;padding:0 12px;border:0;border-radius:8px;background:transparent;font:inherit;font-size:14px;color:var(--ink);text-align:left;cursor:pointer}
.jp-mi:hover,.jp-mi:focus{background:var(--paper-3)}
.jp-vh{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
.jp-ov{display:flex;flex-direction:column;gap:20px}
.jp-tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}
#jp-ov .jp-tile{display:flex;flex-direction:column;align-items:flex-start;gap:4px;text-align:left;background:var(--paper);border:2px solid var(--rule);border-radius:12px;padding:14px 16px;min-height:110px;font:inherit;color:var(--ink);cursor:pointer;box-shadow:none}
#jp-ov .jp-tile.on{border-color:var(--accent)}
#jp-ov .jp-tile .gl-k{font-size:13px;color:var(--ink-3)}
#jp-ov .jp-tile .gl-v{font-size:26px;font-weight:700;color:var(--ink)}
#jp-ov .jp-tile.bad .gl-v{color:var(--bad)} #jp-ov .jp-tile.warn .gl-v{color:var(--warn)}
#jp-ov .jp-tile .gl-s{font-size:13px;color:var(--ink-3);line-height:1.35}
.jp-two{display:flex;gap:20px;align-items:flex-start}
.jp-main{flex:1;min-width:0;display:flex;flex-direction:column;gap:16px}
.jp-aside{width:340px;flex:none;display:flex;flex-direction:column;gap:16px}
.jp-card0{background:var(--paper);border:1px solid var(--rule);border-radius:12px;overflow:hidden}
.jp-ph{display:flex;align-items:center;gap:12px;padding:12px 18px;border-bottom:1px solid var(--rule-2)}
.jp-ph h3{margin:0;flex:1;font-size:16px}
.jp-ph>span{font-size:13px;color:var(--ink-3)}
.jp-empty{padding:14px 18px;margin:0;color:var(--ink-3);font-size:14px}
table.jp-rows{width:100%;border-collapse:collapse}
table.jp-rows td{padding:12px 18px;border-top:1px solid var(--rule-2);vertical-align:middle}
.jp-click{cursor:pointer} tr.jp-click:hover td,.jp-drow.jp-click:hover,.jp-q.jp-click:hover{background:var(--paper-2)} table.jp-bt tr[data-jpline]{cursor:pointer}
table.jp-rows tr:first-child td{border-top:0}
.jp-rk{width:130px;font-size:12px;font-weight:700;color:var(--ink-3);text-transform:uppercase;letter-spacing:.03em}
.jp-keep .bad:not(.pill),#jp-head .bad{color:var(--bad)} .jp-keep .warn:not(.pill):not(.note),#jp-head .warn{color:var(--warn)} .jp-keep .ok:not(.pill),#jp-head .ok{color:var(--ok)}
.jp-keep .btn.bad,.jp-keep .jp-card.bad,.jp-keep .jp-card.warn{color:var(--ink)}
.jp-keep .jp-billback.ok,#jp-ov .jp-tile.bad,#jp-ov .jp-tile.warn{color:var(--ink-2)}
.jp-rt b{display:block;font-size:15px} .jp-rt span{display:block;font-size:13px;color:var(--ink-3);margin-top:2px}
.jp-ra{text-align:right;font-weight:700;white-space:nowrap} .jp-rb{text-align:right;white-space:nowrap;width:1%}
.jp-pf{padding:10px 18px;border-top:1px solid var(--rule-2)}
.jp-link{border:0;background:none;padding:0;min-height:32px;color:var(--accent);font:inherit;font-size:14px;cursor:pointer;text-align:left}
.jp-link:hover{color:var(--accent-3);text-decoration:underline}
.jp-links{display:flex;flex-wrap:wrap;gap:6px 18px;margin:0 0 14px}
.jp-aside .jp-links{margin:0}
.jp-nx{display:flex;gap:10px;align-items:baseline;width:100%;padding:10px 18px;border:0;border-top:1px solid var(--rule-2);background:none;font:inherit;font-size:14px;text-align:left;color:var(--ink);cursor:pointer}
.jp-nx:first-of-type{border-top:0}
.jp-nw{width:62px;flex:none;font-size:12px;color:var(--ink-3)}
.jp-ready{background:var(--accent-2);border:1px solid #bfdbfe;border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:8px;font-size:14px;line-height:1.45}
.jp-cap{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);margin:6px 0 -6px}
.jp-secs{display:flex;flex-direction:column}
.jp-sec{display:flex;align-items:center;gap:12px;min-height:52px;padding:0 14px;border:0;border-top:1px solid var(--rule-2);background:none;font:inherit;color:var(--ink);text-align:left;cursor:pointer}
.jp-sec:first-child{border-top:0}
.jp-sl{flex:1;font-size:15px;font-weight:600} .jp-ss{font-size:13px;color:var(--ink-3)}
.jp-need{display:flex;flex-direction:column;gap:3px;padding:10px 18px;border-top:1px solid var(--rule-2)}
.jp-need:first-of-type{border-top:0} .jp-need>span{font-size:13px;color:var(--ink-3)} .jp-need>button{align-self:flex-start;margin-top:4px}
.jp-kv{display:flex;align-items:baseline;padding:9px 16px;border-top:1px solid var(--rule-2);font-size:14px}
.jp-kv>span{flex:1}
.jp-note{margin:0;padding:10px 16px;border-top:1px solid var(--rule-2);font-size:13px;color:var(--warn)}
.jp-chips{display:flex;gap:8px;flex-wrap:wrap}
.jp-chip{min-height:34px;padding:0 12px;border-radius:17px;border:1px solid var(--rule);background:var(--paper);color:var(--ink);font:inherit;font-size:13px;font-weight:600;cursor:pointer}
.jp-chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}
table.jp-dt{width:100%;border-collapse:collapse;font-size:14px}
table.jp-dt th{text-align:left;font-size:12px;font-weight:500;color:var(--ink-3);padding:10px 18px;border-bottom:1px solid var(--rule-2)}
table.jp-dt td{padding:11px 18px;border-top:1px solid var(--rule-2);cursor:pointer}
table.jp-dt tr:hover td{background:var(--paper-2)}
table.jp-dt .n{text-align:right} table.jp-dt .dim{color:var(--ink-3)}
table.jp-dt td:nth-child(-n+2),table.jp-dt td:nth-child(n+4){white-space:nowrap}
#jb-docbox .jp-links{margin:10px 18px}
.jp-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:0 0 16px}
.jp-kpi{background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:4px}
.jp-kpi span{font-size:13px;color:var(--ink-3)} .jp-kpi b{font-size:24px}
.jp-budget .jp-cap{margin:0 0 8px}
table.jp-bt{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--rule);border-radius:12px;overflow:hidden;font-size:14px;margin:0 0 16px}
table.jp-bt th{font-size:12px;font-weight:500;color:var(--ink-3);text-align:left;padding:10px 14px;border-bottom:1px solid var(--rule-2)}
table.jp-bt td{padding:10px 14px;border-top:1px solid var(--rule-2);vertical-align:top}
table.jp-bt .n{text-align:right;white-space:nowrap}
table.jp-bt tr.over td{background:var(--bad-2)}
table.jp-bt tfoot td{font-weight:700}
.jp-lbtn{border:0;background:none;padding:0;font:inherit;color:var(--ink);text-align:left;cursor:pointer;display:inline-flex;flex-direction:column;gap:2px}
.jp-bdoc{font-size:12px;color:var(--ink-3)}
.jp-detail{margin-top:8px;display:flex;flex-direction:column;gap:2px;font-size:13px}
.jp-detail>div{display:flex;gap:12px;justify-content:space-between;padding:4px 0;border-top:1px dashed var(--rule)}
.jp-billback{background:#fff7ed;border:1px solid #fdba74;border-radius:12px;padding:14px 18px;display:flex;flex-direction:column;gap:6px;color:#7c2d12;font-size:14px;margin:0 0 16px}
.jp-billback.ok{background:var(--paper-2);border-color:var(--rule);color:var(--ink-2)}
.jp-billback .jp-link{color:#9a3412}
.jp-margin{padding:14px;display:flex;flex-direction:column;gap:4px;margin:0 0 16px}
.jp-mk{font-size:13px;color:var(--ink-3)} .jp-mv{display:flex;align-items:baseline;gap:10px} .jp-mv b{font-size:30px} .jp-mv span{font-size:14px;font-weight:600} .jp-ms{font-size:13px;color:var(--ink-3)}
.jp-toolbar{display:flex;align-items:center;gap:12px;margin:0 0 12px;flex-wrap:wrap}
.jp-dlist{display:flex;flex-direction:column;gap:10px;margin:0 0 14px}
.jp-drow{background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:5px}
.jp-drow.od{border-color:#fecaca}
.jp-dh{display:flex;align-items:baseline;gap:8px} .jp-dk{font-size:12px;font-weight:700;color:var(--ink-3)} .jp-dd{font-size:12px;font-weight:700;color:var(--ink-3)} .jp-dd.bad{color:var(--bad)} .jp-dd.warn{color:var(--warn)}
.jp-dw{font-size:13px;color:var(--ink-3)} .jp-dw b{color:var(--ink)}
.jp-qs{display:flex;flex-direction:column;gap:10px;margin:14px 0}
.jp-q{background:var(--paper);border:1px solid #fde68a;border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:5px}
.jp-ck{font-size:12px;font-weight:700;color:var(--ink-3)} .jp-cw{font-size:13px;color:var(--ink-3);line-height:1.4}
.jp-ca{display:flex;gap:8px;margin-top:4px;flex-wrap:wrap}
#js-today,#js-coming{margin:14px 0}
.jp-kv2{display:flex;gap:10px;padding:10px 14px;border-top:1px solid var(--rule-2);font-size:14px;line-height:1.4}
.jp-kv2:first-child{border-top:0} .jp-kv2>span:first-child{width:86px;flex:none;color:var(--ink-3);font-size:13px}
.jp-clash{display:flex;gap:10px;align-items:flex-start;background:var(--bad-2);border:1px solid #fecaca;border-radius:12px;padding:12px 14px;color:var(--bad);margin:0 0 14px}
.jp-clash>div{display:flex;flex-direction:column;gap:4px;color:var(--ink)} .jp-clash b{color:var(--bad)}
@media (max-width:760px){
  body.jp-on #subnav{display:none !important}
  .jp-head{background:#111a2e;color:#fff;padding:8px 16px 12px;border:0;gap:4px}
  .jp-head .jp-ib{background:transparent;border-color:#3a4866;color:#fff}
  .jp-head .jp-back{border:0;margin-left:-12px}
  .jp-head .jp-ib[aria-expanded=true]{background:#2a3a5e}
  .jp-name select{color:#fff;font-size:19px;background:transparent}
  .jp-name select option{color:#172033}
  .jp-name .jp-chev{color:#fff}
  .jp-sect{font-size:19px;color:#fff}
  .jp-sub{font-size:13px;color:#b9c3d8}
  .jp-menu{position:fixed;left:16px;right:16px;top:auto;width:auto;margin-top:8px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px}
  .jp-nh{grid-column:1/-1}
  .jp-mi{min-height:48px;font-size:15px;font-weight:600}
  .jp-tiles{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
  #jp-ov .jp-tile{min-height:96px;padding:12px;border-width:1px}
  #jp-ov .jp-tile .gl-v{font-size:22px} #jp-ov .jp-tile .gl-k,#jp-ov .jp-tile .gl-s{font-size:12px}
  #jp-ov .jp-tile.bad{border-color:#fecaca}
  .jp-two{flex-direction:column} .jp-aside{width:auto}
  #jbill-body>.jp-card0{margin:0 0 16px}
  .jp-cards{display:flex;flex-direction:column;gap:12px;padding:12px}
  .jp-card{background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:6px}
  .jp-ct{display:flex;gap:8px;align-items:baseline} .jp-ct b:first-child{flex:1;font-size:15px;line-height:1.35}
  #jp-panel{border:0;background:none} #jp-panel .jp-ph{display:none} #jp-panel .jp-cards{padding:0}
  .jp-link,.jp-tap,#jp-ov .jp-sec,#jp-ov .jp-nx{min-height:44px !important;min-width:44px;height:auto !important}
  .jp-head .jp-ib{flex:none;min-width:44px}
  .jp-links{gap:4px 16px}
  .jp-nx{padding:10px 14px}
  .jp-chip{min-height:44px;padding:0 14px;font-size:14px}
  #jb-docbox .jp-chips{padding:12px 14px 4px}
  .jp-docs{border:0}
  .jp-doc{display:flex;align-items:center;gap:12px;width:100%;min-height:60px;padding:8px 14px;border:0;border-top:1px solid var(--rule-2);background:none;font:inherit;color:var(--ink);text-align:left}
  .jp-doc:first-child{border-top:0}
  .jp-dl{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px} .jp-dl span{font-size:13px;color:var(--ink-3)}
  .jp-dr{display:flex;flex-direction:column;align-items:flex-end;gap:2px} .jp-dr span{font-size:12px;font-weight:700}
  .jp-wide{width:100%;min-height:48px;font-size:16px}
  .jp-bcards{display:flex;flex-direction:column;gap:10px;margin:0 0 16px}
  .jp-bcard{background:var(--paper);border:1px solid var(--rule);border-radius:12px;overflow:hidden}
  .jp-bcard.over{border-color:#fecaca}
  .jp-bbtn{width:100%;border:0;background:none;padding:10px 12px;display:flex;flex-direction:column;gap:6px;font:inherit;color:var(--ink);text-align:left}
  .jp-bt{display:flex;gap:8px;align-items:baseline;width:100%} .jp-bn{flex:1;min-width:0;font-size:15px} .jp-bt>b{white-space:nowrap;font-size:14px}
  .jp-bgrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:4px 6px;width:100%}
  .jp-bf b{font-size:13.5px}
  .jp-bf{display:flex;flex-direction:column} .jp-bk{font-size:11px;color:var(--ink-3)} .jp-bf b{font-size:14px}
  .jp-bcard .jp-detail{margin:0;padding:6px 14px 10px;background:var(--paper-2)}
  .jp-billback{padding:14px}
}
`;
  const st = document.createElement("style");
  (st.id = "jobpage-css"), (st.textContent = css), document.head.appendChild(st);
})();
