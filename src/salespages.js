/* =====================================================================================================================
   Sales and Clients: the Pipeline, Clients, a client's page and a deal's page (docs/mockups/sales/SPEC.md, its chief
   of staff review; BACKLOG section 10 items 1, 3, 4 and 5; DECISIONS 10-26: Won means signed and Set Up the Job comes
   before Won; 11-03: Estimates leaves the Sales menu, reversibly).

   What was wrong. Sales was eleven pages for the owner (Pipeline, Numbers, Forecast, a Dashboard, Partners, Playbook,
   Estimates, Clients, People, Companies, a client's six tabs). "No Next Step 3" read "3 past their date"; Ana
   Petrova's deal said 9/2 while her task said 9/4, so the Pipeline counted her late; the Nakamuras signed on 7/25 and
   no job was ever set up, and nothing said so; Aliya Chen wrote as a client with no record; the Kleins read $253,684
   billed and $238,015 invoiced with no word on which was which; the activity named an invoice "INV-003".

   The structure.
     Pipeline (ovsales)   Need You (one rule, slNeedYou: a next step past its date, no touch in 14 days, or signed with
                          no job set up), then On Track; All Open and Won and Lost one tap; How Sales Is Going (the
                          Numbers, the Forecast, the Dashboard and Partners' figures) one fold down; Proposals Out,
                          where an old Estimates link lands, each estimate with its deal.
     Clients (clients)    Need You (a client waiting on us, money past due, someone writing as a client with no
                          record, a "repeat client" with none), All, Partners.
     A client             Waiting on Us, Waiting on Them, They Owe, Left to Bill, each equal to its rows; Overview,
                          Contract and Billing, Messages; one + tied to the client. Billed is gross or net, labelled,
                          from one function (slBilled) that ties to the cent.
     A deal (deal)        the next step with its button, the road to signed (Set Up the Job before Won), the proposal,
                          why they are buying, people, building, every touch.
   A deal's next step is its open task (slNextStep): the earliest open task linked to the deal; the deal's copy of the
   date is refreshed from it, so the Pipeline, the deal, Tasks and Today read one date.

   Design gate (BACKLOG 1.16). No new store or list: deals are DB.leads, clients DB.clients, partners DB.partners;
   the deal page and the hub of figures read them. Estimates stay in Billing (Accounting) and on the job.
   ===================================================================================================================== */

// Estimates in the Sales menu: off (DECISIONS 11-03, flagged for Alan). Set true and the entry returns, as the
// Pipeline's Proposals Out filter; old links then open Billing's Estimates as before.
const YD_ESTIMATES_IN_MENU = !1;
// The seats whose Accounting group holds Billing (and its Estimates): for them Estimates leaves the Sales menu. Everyone
// else who writes estimates (the PM above all) keeps Estimates under Sales and Clients, one tap (coordinator, 11-04)
const YD_EST_VIA_ACCOUNTING = ["owner", "billing", "controller"];
const ydEstInMenu = (r) => YD_ESTIMATES_IN_MENU || !YD_EST_VIA_ACCOUNTING.includes(r || role());
const SL_LABEL = { inquiry: "Lead", qualified: "Qualified", "site-visit": "Site Visit", design: "Design Proposal", proposal: "Proposal Out", won: "Signed", lost: "Lost" };
const slIsOpen = (l) => !["won", "lost"].includes(l.stage);
const slTd = () => today();

// ---- one record, one date: the deal's next step is its open task -------------------------------------------------
function slTasksOf(l) {
  let T = [];
  try {
    T = tkAll({ open: !0 }).filter((t) => t.row && !t.approval && (t.row.dealId === l.id || ("lead" === t.row.kind && t.row.id === l.id)));
  } catch (e) {}
  // a task the person keeps on the deal comes before the deal's own line (the "lead:" row is the copy)
  return T.sort((a, b) => ("hub" === b.row.kind) - ("hub" === a.row.kind) || String(a.due || "9999").localeCompare(String(b.due || "9999")));
}
function slNextStep(l) {
  const T = slTasksOf(l).filter((t) => "hub" === t.row.kind),
    own = slTasksOf(l).filter((t) => "lead" === t.row.kind),
    pick = T.slice().sort((a, b) => String(a.due || "9999").localeCompare(String(b.due || "9999")))[0] || own[0] || null;
  if (!pick) return { title: "No Next Step", due: "", task: null, key: "" };
  const title = String(pick.title || "").replace(/\s+[—-]\s+.*$/, "");
  return { title: title, due: pick.due || "", task: pick, key: "function" == typeof tdyShape ? tdyShape(pick).key : "" };
}
// the deal's own copy of the date follows its task (the Pipeline table, the old board and Ask read l.nextDue)
function slSyncNext() {
  let ch = !1;
  (DB.leads || []).filter(slIsOpen).forEach((l) => {
    const s = slNextStep(l);
    if (!s.task || "hub" !== s.task.row.kind) return;
    s.due !== l.nextDue && ((l.nextDue = s.due), (ch = !0));
    s.title && s.title !== l.next && ((l.next = s.title), (ch = !0));
  });
  return ch;
}
const slClientOf = (l) => (l.clientId && (DB.clients || []).find((c) => c.id === l.clientId)) || (DB.clients || []).find((c) => String(c.name).toLowerCase() === String(l.name || "").toLowerCase()) || null;
// Each signed deal has its own job (a repeat client's second deal is not set up by the first job): the deal's own link
// (l.projectId, written by Set Up the Job), else a job that names the deal, else the client's signed deals and jobs
// paired in order, oldest first. A signed deal with no job of its own still needs one, and its deposit cannot be billed.
function slJobOf(l) {
  const P = DB.projects || [],
    own = (l.projectId && P.find((p) => p.id === l.projectId)) || P.find((p) => p.dealId === l.id);
  if (own) return own;
  const c = slClientOf(l);
  if (!c) return null;
  const L = DB.leads || [],
    claimed = new Set(L.map((x) => x.projectId).concat(P.map((p) => p.dealId && p.id)).filter(Boolean)),
    jobs = P.filter((p) => p.clientId === c.id && !claimed.has(p.id) && !p.dealId).sort((a, b) => String((a.project || {}).start || a.createdAt || "").localeCompare(String((b.project || {}).start || b.createdAt || ""))),
    deals = L.filter((x) => "won" === x.stage && slClientOf(x) === c && !x.projectId && !P.some((p) => p.dealId === x.id)).sort((a, b) => String(a.wonAt || "").localeCompare(String(b.wonAt || "")));
  // pair in order, a job only with a deal signed on or before the job began (a job that started before the deal was
  // signed belongs to an earlier deal: the Kleins' 121 State Street is not their second deal's job)
  // when the job was signed: its contract date (the job's, else the client's when it has one job), else its start
  const solo = jobs.length + P.filter((p) => p.clientId === c.id && (claimed.has(p.id) || p.dealId)).length === 1,
    begun = (p) => String((p.project || {}).contractDate || p.contractDate || (solo && c.contractDate) || (p.project || {}).start || p.createdAt || "9999-12-31").slice(0, 10),
    used = new Set();
  let mine = null;
  deals.forEach((d) => {
    const j = jobs.find((p) => !used.has(p.id) && begun(p) >= String(d.wonAt || "").slice(0, 10));
    j && used.add(j.id);
    d === l && (mine = j || null);
  });
  return mine;
}
// Set Up the Job ties the job it makes to the deal
let slSetUpFor = null;
const slQuiet = (l) => {
  const la = "function" == typeof slLastTouch ? slLastTouch(l) : l.created;
  return la ? dayDiff(String(la).slice(0, 10), slTd()) : 0;
};
const slVerb = (t) => (/^call\b/i.test(t) ? "Call" : /^(send|write|draft)\b/i.test(t) ? "Draft" : /^follow\b/i.test(t) ? "Follow Up" : /^book\b/i.test(t) ? "Book" : "Open");
// Need You: one rule, read by the Pipeline, its chip, Today's rows and Today's "Deals That Need You"
function slNeedYou() {
  const td = slTd(),
    out = [];
  (DB.leads || []).forEach((l) => {
    if ("lost" === l.stage) return;
    if ("won" === l.stage) {
      if (slJobOf(l)) return;
      const days = l.wonAt ? dayDiff(l.wonAt, td) : 0;
      return void out.push({ l: l, why: "signed", due: l.wonAt || td, title: `Set up ${l.name}'s job`, meta: `signed ${l.wonAt ? fmt(l.wonAt) : ""}${days ? `, ${days} days ago` : ""} · ${l.addr || ""} · nothing can be bought or billed until the job exists`, act: "Set Up the Job", run: () => slSetUpJob(l), taskKeys: [], when: days ? `Signed ${days} days ago` : "Signed" });
    }
    const s = slNextStep(l),
      quiet = slQuiet(l),
      keys = slTasksOf(l).map((t) => ("function" == typeof tdyShape ? tdyShape(t).key : ""));
    if (s.due && s.due < td) out.push({ l: l, why: "late", due: s.due, title: `${l.name}: ${s.title}`, meta: `${SL_LABEL[l.stage] || l.stage} · ${ydMoney0(l.value || 0)}`, act: slVerb(s.title), run: () => (s.task ? tkSheet(s.key) : slOpenDeal(l.id)), taskKeys: keys, when: `${dayDiff(s.due, td)} days late` });
    else if (quiet >= 14) out.push({ l: l, why: "quiet", due: td, title: `${l.name}: quiet ${quiet} days`, meta: `${SL_LABEL[l.stage] || l.stage} · ${ydMoney0(l.value || 0)} · ${s.title}`, act: "Follow Up", run: () => slOpenDeal(l.id), taskKeys: keys, when: `Quiet ${quiet} days` });
    else if (!s.task) out.push({ l: l, why: "nostep", due: td, title: `${l.name}: no next step`, meta: `${SL_LABEL[l.stage] || l.stage} · ${ydMoney0(l.value || 0)}`, act: "Open", run: () => slOpenDeal(l.id), taskKeys: keys, when: "No Next Step" });
  });
  const rank = { signed: 0, late: 1, quiet: 2, nostep: 3 };
  return out.sort((a, b) => rank[a.why] - rank[b.why] || String(a.due).localeCompare(String(b.due)));
}
// Set Up the Job: the client (made from the deal when there is none), then the job, on the client
function slSetUpJob(l) {
  if (!isOwner() && !["pm"].includes(role())) return toast("The owner sets up a signed client's job");
  let c = slClientOf(l);
  if (!c) {
    c = blankClient(l.name);
    Object.assign(c, { type: "Residential owner", propertyAddr: l.addr || "", billingAddr: l.addr || "" });
    (l.email || l.phone) && c.contacts.push({ id: uid("ct"), name: l.name, email: l.email || "", phone: l.phone || "", role: "Owner — decisions", primary: !0 });
    DB.clients.push(c), (l.clientId = c.id);
    c.activity.push({ t: nowStamp(), by: (currentUser() || {}).name || "", text: `Client record made from the deal to set up the job` });
    save();
    toast(`${c.name} is a client now`, () => slOpenClient(c.id));
  }
  slSetUpFor = { lead: l.id, before: new Set((DB.projects || []).map((p) => p.id)) };
  newProjectDialog(c.id);
}
function slTieNewJob() {
  if (!slSetUpFor) return;
  const l = (DB.leads || []).find((x) => x.id === slSetUpFor.lead),
    p = (DB.projects || []).find((x) => !slSetUpFor.before.has(x.id));
  if (!l || !p) return;
  (l.projectId = p.id), (p.dealId = l.id), (slSetUpFor = null), save();
}

// ---- figures ------------------------------------------------------------------------------------------------------
// Billed, gross and net of retainage, per client (or job), summed in cents from each invoice's own total
function slBilled(cid, pid) {
  const c = (DB.clients || []).find((x) => x.id === cid);
  let g = 0,
    r = 0,
    n = 0;
  ((c && c.invoices) || [])
    .filter((i) => !["void", "voided", "draft", "deleted"].includes(i.status) && (!pid || !i.projectId || i.projectId === pid))
    .forEach((i) => {
      const t = docTotal(i);
      g += Math.round(100 * ((+t.sub || 0) - (+t.disc || 0) + (+t.tax || 0)));
      r += Math.round(100 * (+t.ret || 0));
      n += Math.round(100 * (+t.total || 0));
    });
  return { gross: g / 100, ret: r / 100, net: n / 100 };
}
const slQuarter = () => {
  const d = parse(slTd());
  return `${d.getFullYear()}-${String(3 * Math.floor(d.getMonth() / 3) + 1).padStart(2, "0")}-01`;
};
function slNums() {
  const L = DB.leads || [],
    q = slQuarter(),
    open = L.filter(slIsOpen),
    props = open.filter((l) => "proposal" === l.stage),
    wonQ = L.filter((l) => "won" === l.stage && String(l.wonAt || l.closedate || "") >= q),
    lostQ = L.filter((l) => "lost" === l.stage && String(l.lostAt || l.closedate || "") >= q),
    mins = L.map((l) => ("function" == typeof slResponseMin ? slResponseMin(l) : null)).filter((x) => null != x).sort((a, b) => a - b),
    med = mins.length ? mins[Math.floor(mins.length / 2)] : null,
    thanks = (DB.partners || []).reduce((a, p) => a + (p.thanks || []).filter((t) => !t.done).length, 0),
    owed = (DB.partners || []).filter((p) => (p.thanks || []).some((t) => !t.done)).map((p) => p.name),
    days = wonQ.map((l) => (l.inquiredAt || l.created ? dayDiff(String(l.inquiredAt || l.created).slice(0, 10), l.wonAt || l.closedate) : null)).filter((x) => null != x),
    pipe = open.reduce((a, l) => a + (+l.value || 0), 0),
    src = {};
  L.forEach((l) => {
    const k = String(l.source || "Other").split(" — ")[0];
    (src[k] = src[k] || { n: 0, won: 0 }).n++, "won" === l.stage && src[k].won++;
  });
  return [
    { k: "First Reply", v: null == med ? "—" : med < 60 ? `${med} min` : `${Math.round(med / 60)} h`, sub: `Median across ${mins.length} leads; the firms that win reply inside the hour` },
    { k: "Proposals Out", v: ydMoney0(props.reduce((a, l) => a + (+l.value || 0), 0)), sub: props.map((l) => `${l.name} ${ydMoney0(l.value)}`).join(" · ") || "None out", go: () => slOpenPipeline("props") },
    { k: "Signed This Quarter", v: ydMoney0(wonQ.reduce((a, l) => a + (+l.value || 0), 0)), sub: wonQ.map((l) => `${l.name}, signed ${fmt(l.wonAt || l.closedate)}`).join(" · ") || "None yet" },
    { k: "Close Rate on Presented Proposals", v: wonQ.length + lostQ.length ? `${Math.round((100 * wonQ.length) / (wonQ.length + lostQ.length))}%` : "—", sub: `${wonQ.length} won, ${lostQ.length} lost this quarter` },
    { k: "Inquiry to Agreement", v: days.length ? `${Math.round(days.reduce((a, b) => a + b, 0) / days.length)} days` : "—", sub: `The ${ydPlural(days.length, "job")} won this quarter` },
    { k: "Open Pipeline", v: ydMoney0(pipe), sub: `${ydPlural(open.length, "open deal")}` },
    { k: "By Source", v: "", sub: Object.entries(src).map(([k, x]) => `${k} ${x.n}${x.won ? ` (${x.won} won)` : ""}`).join(" · ") },
    { k: "Lost and Why", v: String(L.filter((l) => "lost" === l.stage).length), sub: L.filter((l) => "lost" === l.stage).map((l) => `${l.name}: ${l.lostWhy || "no reason recorded"}`).join(" · ") || "None lost" },
    { k: "Thank-Yous Owed to Partners", v: String(thanks), sub: owed.length ? `${owed.join(", ")} sent us work and heard nothing back` : "Every referral has been thanked", go: () => slOpenClients("partners") },
  ];
}

// ---- the Pipeline -------------------------------------------------------------------------------------------------
let slChip = "need",
  slNumsOpen = !1,
  slNewOpen = !1;
function slOpenPipeline(chip) {
  (slChip = chip || "need"), setView("ovsales");
}
const slMayEdit = () => isOwner();
// money on the client pages: the owner, the PM, billing and the controller (the designer reads decisions, not money)
const slMoneyOk = () => ["owner", "pm", "billing", "controller"].includes(role()) && !("function" == typeof tdNoMoney && tdNoMoney());
function slDealRow(l, sec, o) {
  o = o || {};
  const s = slNextStep(l),
    td = slTd(),
    late = s.due && s.due < td;
  return {
    id: l.id,
    sec: sec,
    title: l.name,
    meta: [`${SL_LABEL[l.stage] || l.stage}`, String(l.source || "").replace(/^Referral — /, "referral: "), l.addr, o.meta || s.title].filter(Boolean).join(" · "),
    amt: ydMoney0(l.value || 0),
    when: o.when || ("won" === l.stage ? `Signed ${fmt(l.wonAt || l.closedate)}` : "lost" === l.stage ? `Lost ${fmt(l.lostAt || l.closedate)}` : s.due ? (late ? `${dayDiff(s.due, td)} days late` : ydWhen(s.due)) : "No Next Step"),
    late: o.late != null ? o.late : late,
    act: slMayEdit() ? o.act || "Open" : "",
    primary: !!o.primary,
    // a lead not yet qualified opens as the lead it is (its own record: Convert to Opportunity, Unqualify); a deal opens
    // its page
    run: o.run || (() => ("inquiry" === l.stage && "function" == typeof scOpen ? scOpen(l.id) : slOpenDeal(l.id))),
  };
}
function slPipelineRows() {
  const L = DB.leads || [],
    need = slNeedYou(),
    needIds = new Set(need.map((x) => x.l.id)),
    open = L.filter(slIsOpen),
    order = ["inquiry", "qualified", "site-visit", "design", "proposal"],
    q = slQuarter();
  if ("need" === slChip)
    return need
      .map((x, i) => slDealRow(x.l, "need", { act: x.act, primary: 0 === i, run: x.run, when: x.when, late: !0, meta: "signed" === x.why ? "no job set up, so nothing can be bought or billed" : x.title.replace(/^[^:]+:\s*/, "") }))
      .concat(open.filter((l) => !needIds.has(l.id)).sort((a, b) => String(slNextStep(a).due || "9").localeCompare(String(slNextStep(b).due || "9"))).map((l) => slDealRow(l, "track")));
  if ("open" === slChip) return open.slice().sort((a, b) => order.indexOf(a.stage) - order.indexOf(b.stage)).map((l) => slDealRow(l, "open"));
  if ("closed" === slChip)
    return L.filter((l) => ("won" === l.stage || "lost" === l.stage) && String(l.wonAt || l.lostAt || l.closedate || "") >= q).map((l) =>
      slDealRow(l, "closed", "won" === l.stage && !slJobOf(l) ? { act: "Set Up the Job", run: () => slSetUpJob(l), meta: "client on file; no job set up yet" } : "lost" === l.stage && !l.lostWhy ? { act: "Record the Reason", meta: "no reason recorded: ask why while it is fresh" } : { meta: "won" === l.stage ? "job set up" : l.lostWhy }),
    );
  // Proposals Out: every proposal with its deal (an old Estimates link lands here)
  const rows = open
    .filter((l) => "proposal" === l.stage || "design" === l.stage)
    .map((l) => {
      const c = slClientOf(l),
        est = c ? (c.estimates || []).filter((e) => ["sent", "draft"].includes(e.status)) : [];
      return slDealRow(l, "props", { meta: est.length ? est.map((e) => `${e.number} ${e.status}`).join(", ") : `proposal ${l.proposal && l.proposal.sentAt ? `sent ${fmt(l.proposal.sentAt)}` : "being written"}; no estimate linked yet` });
    });
  (DB.clients || []).forEach((c) =>
    (c.estimates || [])
      .filter((e) => ["sent", "draft"].includes(e.status))
      .forEach((e) => {
        const deal = (DB.leads || []).find((l) => slClientOf(l) === c);
        rows.push({ id: "est:" + c.id + ":" + e.id, sec: "props", title: `${e.number} · ${c.name}`, meta: `${e.status === "sent" ? "Sent" : "Draft"} · ${deal ? `deal: ${deal.name}` : "on the job (no open deal)"}`, amt: ydMoney0(docTotal(e).total), when: e.date ? fmt(e.date) : "", act: "Open", run: () => ((clientOpen = c.id), (docOpen = { kind: "estimate", id: e.id }), setView("clients")) });
      }),
  );
  return rows;
}
function slPipelineRender() {
  // a deal's or a lead's full record open on the page (hbOpen) is shown as it is: the Pipeline steps aside until it closes
  const on = "ovsales" === view && ydOffice() && !("undefined" != typeof hbOpenId && hbOpenId && hbOpenId.deal);
  const h = ydHost("ovsales", on);
  if (!on || !h) return;
  try {
    slSyncNext() && save();
  } catch (e) {}
  const need = slNeedYou(),
    rows = slPipelineRows(),
    phone = ydPhone(),
    pipe = (DB.leads || []).filter(slIsOpen).reduce((a, l) => a + (+l.value || 0), 0);
  ydActs = {};
  rows.forEach((r) => ydAct(r.id, r.run));
  const defs = [
    { k: "need", label: "Need You", n: need.length || "" },
    { k: "open", label: "All Open", n: "" },
    { k: "closed", label: "Won and Lost", n: "" },
    // where an estimate is found now Estimates is off the menu (each with its deal): a chip, one tap (review 11-03)
    { k: "props", label: "Proposals Out", n: "" },
  ];
  const sec = (k) => rows.filter((r) => r.sec === k);
  const body =
    "need" === slChip
      ? ydSectionHtml("Need You", need.length, "past its date, quiet 14 days, or signed with no job", sec("need"), "No deal needs you today.") + ydSectionHtml("On Track", sec("track").length, "", sec("track"), "Nothing else open.")
      : "open" === slChip
        ? ydSectionHtml("All Open, by Stage", sec("open").length, "", sec("open"), "No open deals.")
        : "closed" === slChip
          ? ydSectionHtml("Won and Lost This Quarter", sec("closed").length, "", sec("closed"), "Nothing won or lost this quarter.")
          : ydSectionHtml("Proposals Out", sec("props").length, "each estimate with its deal", sec("props"), "No proposals out.");
  const nums = slNums();
  const fold = ydFoldHtml("nums", "How Sales Is Going", slNumsOpen, nums.map((x) => `<div class="yd-kv"${x.go ? ` data-ydnum="${esc(x.k)}" role="button" tabindex="0"` : ""}><span>${esc(x.k)}<i>${esc(x.sub)}</i></span><b>${esc(x.v)}</b></div>`).join(""));
  const plus = slMayEdit()
    ? `<span class="yd-plus"><button type="button" class="btn yd-plusb" data-ydnew aria-haspopup="menu" aria-expanded="${slNewOpen}" aria-label="New Lead">${ydSvg("plus")}${phone ? "" : "New Lead"}</button>${
        slNewOpen ? `<div class="yd-menu" role="menu"><span class="yd-mh">New lead, for you</span><button type="button" role="menuitem" data-ydnewitem="mail">Lead from a Mail</button><button type="button" role="menuitem" data-ydnewitem="typed">Lead, Typed In</button></div>` : ""
      }</span>`
    : "";
  h.innerHTML = `<div class="yd-ph"><div class="grow"><h2>Pipeline</h2><div class="yd-sub">${need.length ? `${ydPlural(need.length, "deal needs", "deals need")} you` : "No deal needs you"} · open pipeline ${esc(ydMoney0(pipe))}${slMayEdit() ? "" : " · read only"}</div></div>${plus}</div>${ydChipsHtml(defs, slChip, "pipe")}${body}${fold}`;
}

// ---- Clients ------------------------------------------------------------------------------------------------------
let slClChip = "need",
  slClChipKeep = "need";
function slOpenClients(chip) {
  (slClChip = chip || "need"), (clientOpen = null), (docOpen = null), setView("clients");
}
// the messages waiting on us that belong to a client (their own mail, their job's calls and mail)
function slClientMsgs(c) {
  const pids = new Set((DB.projects || []).filter((p) => p.clientId === c.id).map((p) => p.id)),
    mails = new Set((c.contacts || []).map((x) => String(x.email || "").toLowerCase()).filter(Boolean));
  let L = [];
  try {
    L = cmNeedsAnswer();
  } catch (e) {}
  // the owner's rule reaches every client message; read it whoever is signed in
  if (!isOwner())
    try {
      const keep = DB.deviceUser,
        o = (DB.users || []).find((u) => "owner" === u.role);
      if (o) {
        DB.deviceUser = o.id;
        try {
          L = cmNeedsAnswer();
        } finally {
          DB.deviceUser = keep;
        }
      }
    } catch (e) {}
  return L.filter((m) => {
    const R = m.route || {};
    return R.clientId === c.id || (R.projectId && pids.has(R.projectId)) || mails.has(String((m.from || {}).email || "").toLowerCase());
  });
}
// someone writing as a client with no client record ("Who Is This?"), and a "repeat client" with none
function slStrangers() {
  const out = [],
    seen = new Set();
  (DB.comms || []).forEach((c) => {
    const R = c.route || {};
    if ((R.bot || R.clientId || R.vendorId || R.employee || R.leadName) && !R.existingJob) return;
    if (!(R.contact || R.existingJob) || R.projectId) return;
    const who = R.contact || ydMsgWho(c);
    if (seen.has(who) || (DB.clients || []).some((x) => String(x.name).toLowerCase().includes(String(who).toLowerCase()))) return;
    seen.add(who);
    out.push({ id: "who:" + c.id, who: who, title: `Who is ${who}?`, meta: `writes as a client${R.existingJob ? ` about ${R.existingJob}` : ""}; no client record on file`, act: "Add as a Client", run: () => slAddClient(who, R.existingJob || R.addr || "", c) });
  });
  (DB.leads || [])
    .filter((l) => /repeat/i.test(l.source || "") && !slClientOf(l))
    .forEach((l) => out.push({ id: "rep:" + l.id, who: l.name, title: `${l.name}: a repeat client with no client record`, meta: `the deal says repeat client; no past job or client on file`, act: "Add as a Client", run: () => slAddClient(l.name, l.addr || "", null, l) }));
  return out;
}
function slAddClient(name, addr, comm, lead) {
  if (!slMayEdit() && "pm" !== role()) return toast("The owner or the PM adds a client");
  const c = blankClient(name);
  Object.assign(c, { type: "Residential owner", propertyAddr: addr || "", billingAddr: addr || "" });
  const email = comm && comm.from && comm.from.email;
  email && c.contacts.push({ id: uid("ct"), name: name, email: email, phone: "", role: "Owner — decisions", primary: !0 });
  DB.clients.push(c);
  lead && (lead.clientId = c.id);
  comm && (comm.route = Object.assign({}, comm.route || {}, { clientId: c.id }));
  c.activity.push({ t: nowStamp(), by: (currentUser() || {}).name || "", text: `Client record made${comm ? " from their mail" : lead ? " from the deal" : ""}` });
  save(), toast(`${name} is a client now`, () => slOpenClient(c.id)), render();
}
function slClientsRows() {
  const td = slTd();
  if ("partners" === slClChip)
    return (DB.partners || []).map((p) => {
      const L = (DB.leads || []).filter((l) => l.partnerId === p.id),
        owe = (p.thanks || []).filter((t) => !t.done).length,
        last = (p.touches || []).map((t) => t.at).sort().pop() || "";
      return { id: "pt:" + p.id, sec: "partners", title: `${p.name}${p.firm ? `, ${p.firm}` : ""}`, meta: `${L.length} referrals${owe ? ` · a thank-you owed` : ""}${last ? ` · last touch ${fmt(String(last).slice(0, 10))}` : " · never touched"}`, act: "Open", run: () => ("function" == typeof slPartnerSheet ? slPartnerSheet(p) : null) };
    });
  const C = DB.clients || [],
    rowOf = (c, sec, o) => {
      const F = clientFin(c);
      return Object.assign({ id: c.id, sec: sec, title: c.name, meta: [((c.contacts || [])[0] || {}).name, c.propertyAddr].filter(Boolean).join(" · "), amt: F.outstanding && slMoneyOk() ? `owes ${ydMoney0(F.outstanding)}` : "", act: "Open", run: () => slOpenClient(c.id) }, o || {});
    };
  if ("all" === slClChip) return C.slice().sort((a, b) => clientFin(b).outstanding - clientFin(a).outstanding || String(a.name).localeCompare(String(b.name))).map((c) => rowOf(c, "all"));
  const need = [];
  C.forEach((c) => {
    const M = slClientMsgs(c),
      F = clientFin(c);
    if (M.length) need.push(rowOf(c, "need", { meta: `waiting on us: ${M.map((m) => `${ydMsgWho(m)} ${fmt(String(m.date || "").slice(0, 10))}`).join(", ")}`, act: "Open", when: ydAge(M[M.length - 1].date), late: !0 }));
    else if (F.overdue > 0 && slMoneyOk()) need.push(rowOf(c, "need", { meta: `${ydMoney0(F.overdue)} past due`, act: "Open" }));
  });
  slStrangers().forEach((x) => need.push({ id: x.id, sec: "need", title: x.title, meta: x.meta, act: slMayEdit() || "pm" === role() ? x.act : "", run: x.run }));
  return need;
}
function slClientsRender() {
  const on = "clients" === view && ydOffice() && !clientOpen && !docOpen;
  const h = ydHost("clients", on);
  if (!on) return;
  const keep = slClChip;
  slClChip = "need";
  const needN = slClientsRows().length;
  slClChip = keep;
  const shown = slClientsRows();
  ydActs = {};
  shown.forEach((r) => ydAct(r.id, r.run));
  const owed = (DB.clients || []).reduce((a, c) => a + clientFin(c).outstanding, 0),
    past = (DB.clients || []).reduce((a, c) => a + clientFin(c).overdue, 0);
  const title = { need: "Need You", all: "All Clients", partners: "Partners" }[slClChip];
  h.innerHTML = `<div class="yd-ph"><div class="grow"><h2>Clients</h2><div class="yd-sub">${slMoneyOk() ? `Owed to us ${esc(ydMoney0(owed))}, ${past ? `${esc(ydMoney0(past))} past due` : "none past due"}` : "Everyone the firm works for, and who is waiting on us"}</div></div>${slMayEdit() ? `<button type="button" class="btn" data-ydnewclient>New Client</button>` : ""}</div>${ydChipsHtml(
    [
      { k: "need", label: "Need You", n: needN || "" },
      { k: "all", label: "All", n: "" },
      { k: "partners", label: "Partners", n: "" },
    ],
    slClChip,
    "clients",
  )}${ydSectionHtml(title, shown.length, "need" === slClChip ? "waiting on us, money past due, or not on file" : "", shown, "need" === slClChip ? "No client needs you." : "Nobody here yet.")}`;
}

// ---- a client's page -----------------------------------------------------------------------------------------------
let slClTab = "overview",
  slClNewOpen = !1;
// the client's billing record as it was (its Billing tab: New Invoice, progress and deposit invoices, change orders),
// one tap from Contract and Billing
let slClOld = !1;
// A link to a client's billing record (a toast's Open on a new invoice, a statement, a job's billing link) sets the old
// page's own tab, clientTab "fin": it lands on the record it names, as before, not on the client's page above it. The
// client's page itself never sets "fin" except through Billing Record, so a change to "fin" is such a link.
let slClSeen = { c: null, tab: "overview" };
function slBillingLink() {
  if ("clients" !== view || !clientOpen) return void (slClSeen = { c: null, tab: "undefined" != typeof clientTab ? clientTab : "" });
  const tab = "undefined" != typeof clientTab ? clientTab : "";
  "fin" === tab && (slClSeen.tab !== "fin" || slClSeen.c !== clientOpen) && (slClOld = !0);
  slClSeen = { c: clientOpen, tab: tab };
}
function slOpenClient(id) {
  (clientOpen = id), (docOpen = null), (slClNewOpen = !1), (slClOld = !1);
  "undefined" != typeof clientTab && (clientTab = "overview"), (slClSeen = { c: id, tab: "overview" });
  slClTab = "billing" === role() ? "billing" : "overview";
  setView("clients");
}
const slFirstNames = (c) => (/&| and /.test(c.name) ? "the " + String(c.name).split(/\s+/).pop().replace(/s$/, "") + "s" : String(c.name).split(" ")[0]);
// the activity names a record by its own number: the entry keeps the record's id and prints its number now
function slActivityText(c, a) {
  let t = String((a && a.text) || "");
  (a.refs || []).forEach((r) => {
    const L = c[r.list] || [],
      d = L.find((x) => x.id === r.id);
    d && d.number && (t = t.split(r.was).join(d.number));
  });
  return t;
}
// legacy entries: a number that names no record, where the client's nth invoice (or change order, estimate) has one
function slActivityRefs() {
  const K = { INV: "invoices", CO: "changeOrders", EST: "estimates" };
  let ch = !1;
  (DB.clients || []).forEach((c) => {
    const nums = new Set();
    Object.values(K).forEach((k) => (c[k] || []).forEach((d) => d.number && nums.add(d.number)));
    (c.activity || []).forEach((a) => {
      if (a.refsDone) return;
      a.refs = a.refs || [];
      String(a.text || "").replace(/\b(INV|CO|EST)-(\d{1,4})\b/g, (m, k, n) => {
        if (nums.has(m)) return m;
        const L = c[K[k]] || [],
          d = L[+n - 1];
        d && d.number && a.refs.push({ list: K[k], id: d.id, was: m });
        return m;
      });
      (a.refsDone = 1), (ch = !0);
    });
  });
  return ch;
}
function slClientParts(c) {
  const P = (DB.projects || []).filter((p) => p.clientId === c.id),
    us = slClientMsgs(c).map((m) => ({ id: "m:" + m.id, sec: "us", title: `${ydMsgWho(m)}: ${ydMsgAbout(m)}`, meta: [ydMsgKind(m), ydMsgWhere(m), fmt(String(m.date || "").slice(0, 10))].filter(Boolean).join(" · "), when: ydAge(m.date), late: !0, act: "call" === m.channel ? "Call Back" : "Reply", run: () => ydMsgOpen(m) })),
    them = [];
  P.forEach((p) => {
    let R = [];
    try {
      R = PRED.clientWaiting.rows(p.id);
    } catch (e) {}
    R.forEach((x, i) => {
      const nm = (x.d && (x.d.name || x.d.number)) || (x.doc && x.doc.number) || "a document";
      them.push({ id: `w:${p.id}:${i}`, sec: "them", title: "decision" === x.kind ? String(nm).replace(/ — .*$/, "") : `${nm}: to sign`, meta: `${"decision" === x.kind ? "a decision" : "change order" === x.kind ? "a change order to sign" : x.kind} · ${shortName(p)}`, act: "Open", run: () => (setCurrent(p.id), "decision" === x.kind ? setView(ydMay("jdec") ? "jdec" : "dec") : ((clientOpen = c.id), (docOpen = { kind: "co", id: x.d && x.d.id }), setView("clients"))) });
    });
  });
  return { P: P, us: us, them: them };
}
function slClientRender() {
  const on = "clients" === view && ydOffice() && !!clientOpen && !docOpen && !slClOld;
  if (!on) return;
  const c = (DB.clients || []).find((x) => x.id === clientOpen);
  if (!c) return;
  const h = ydHost("clients", !0);
  try {
    slActivityRefs() && save();
  } catch (e) {}
  const phone = ydPhone(),
    F = clientFin(c),
    B = slBilled(c.id),
    X = slClientParts(c),
    left = r2((+F.revised || 0) - B.gross),
    mayMoney = slMoneyOk();
  ydActs = {};
  X.us.concat(X.them).forEach((r) => ydAct(r.id, r.run));
  const tiles = [
    ["us", "Waiting on Us", X.us.length, X.us.length ? "messages without our answer" : "nothing waits on us", X.us.length],
    ["them", "Waiting on Them", X.them.length, "decisions and documents to sign", 0],
  ].concat(
    mayMoney
      ? [
          ["owe", "They Owe", ydMoney0(F.outstanding), F.overdue ? `${ydMoney0(F.overdue)} past due` : "none past due", F.overdue],
          ["left", "Left to Bill", ydMoney0(left), "the contract less billed, gross", 0],
        ]
      : [],
  );
  const tilesHtml = `<div class="yd-tiles">${tiles.map(([k, l, v, s, bad]) => `<button type="button" class="yd-tile${bad ? " bad" : ""}" data-ydtile="${k}" data-n="${esc(String(typeof v === "number" ? v : ""))}"><span>${esc(l)}</span><b>${esc(String(v))}</b><i>${esc(s)}</i></button>`).join("")}</div>`;
  const tabs = [
    ["overview", "Overview"],
    ["billing", "Contract and Billing"],
    ["msgs", "Messages"],
  ].filter(([k]) => "billing" !== k || mayMoney);
  ["overview", "billing", "msgs"].includes(slClTab) && tabs.some(([k]) => k === slClTab) || (slClTab = "overview");
  const tabsHtml = `<div class="yd-tabs" role="tablist">${tabs.map(([k, l]) => `<button type="button" role="tab" class="yd-tab${slClTab === k ? " on" : ""}" data-ydtab="${k}" aria-selected="${slClTab === k}">${esc(l)}</button>`).join("")}</div>`;
  let body = "";
  if ("overview" === slClTab) {
    const jobs = X.P.map((p) => ({ id: "j:" + p.id, sec: "job", title: shortName(p), meta: [p.project.type, ("function" == typeof jpDayLine ? jpDayLine(p) : "")].filter(Boolean).join(" · "), act: "Open", run: () => ("function" == typeof jpOpenJob ? jpOpenJob(p.id) : (setCurrent(p.id), setView("dash"))) }));
    jobs.forEach((r) => ydAct(r.id, r.run));
    const people = (c.contacts || []).map((p) => ydKv(p.name, p.role || "", [p.email, p.phone].filter(Boolean).join(" · "))).join(""),
      bld = (c.properties || []).map((p) => ydKv(p.addr, p.buildingType || "", [p.mgmtCompany, p.mgmtAgent, p.superName].filter(Boolean).join(" · "))).join("");
    body =
      ydSectionHtml("Waiting on Us", X.us.length, "", X.us, "Nothing waits on us.") +
      ydSectionHtml("Waiting on Them", X.them.length, "", X.them, "Nothing waits on them.") +
      ydSectionHtml(jobs.length === 1 ? "Their Job" : "Their Jobs", jobs.length, "", jobs, "No job set up yet.") +
      `<section class="yd-card"><div class="yd-sh"><h3>People and Building</h3></div>${people || '<div class="yd-empty">No people on file.</div>'}${bld}</section>`;
  } else if ("billing" === slClTab) {
    const pay = (c.payments || []).reduce((a, p) => a + (+p.amount || 0), 0);
    const kv = [
      ["Contract", ydMoney0(F.revised - (F.approvedCO || 0)), ""],
      ["Approved changes", ydMoney0(F.approvedCO || 0), ""],
      ["Revised contract", ydMoney0(F.revised), ""],
      ["Billed, gross", money(B.gross), "before retainage"],
      ["Retainage held", money(B.ret), "released with the final invoice"],
      ["Billed, net of retainage", money(B.net), "the invoices' totals"],
      ["Paid", money(F.paid), ""],
      ["They owe", money(F.outstanding), F.overdue ? `${money(F.overdue)} past due` : "none past due"],
      ["Left to bill", money(left), "revised contract less billed, gross"],
    ];
    const docs = [];
    (c.estimates || []).forEach((d) => docs.push({ id: "d:estimate:" + d.id, sec: "doc", title: `${d.number} · Estimate`, meta: `${d.status}${d.date ? " · " + fmt(d.date) : ""}`, amt: ydMoney0(docTotal(d).total), act: "Open", run: () => ((docOpen = { kind: "estimate", id: d.id }), render()) }));
    (c.changeOrders || []).forEach((d) => docs.push({ id: "d:co:" + d.id, sec: "doc", title: `${d.number} · Change Order`, meta: `${d.status}${d.date ? " · " + fmt(d.date) : ""}`, amt: ydMoney0(docTotal(d).total), act: "Open", run: () => ((docOpen = { kind: "co", id: d.id }), render()) }));
    (c.invoices || []).forEach((d) => {
      const t = docTotal(d);
      docs.push({ id: "d:invoice:" + d.id, sec: "doc", title: `${d.number} · Invoice`, meta: `${d.status}${d.date ? " · " + fmt(d.date) : ""}${t.ret ? ` · ${money(t.sub - (t.disc || 0))} gross, ${money(t.ret)} retainage` : ""}`, amt: ydMoney0(t.total), act: "Open", run: () => ((docOpen = { kind: "invoice", id: d.id }), render()) });
    });
    (c.payments || []).forEach((p) => docs.push({ id: "d:pay:" + p.id, sec: "doc", title: `Payment${p.method ? `, ${p.method}` : ""}`, meta: p.date ? fmt(p.date) : "", amt: ydMoney0(p.amount), act: "", run: () => null }));
    docs.forEach((r) => ydAct(r.id, r.run));
    body = `<div class="yd-ph"><button type="button" class="btn" data-ydclold>Billing Record</button><span class="small muted">new invoices, progress and deposit invoices, change orders and payments start there</span></div><section class="yd-card"><div class="yd-sh"><h3>The Contract</h3></div>${kv.map(([k, v, s]) => ydKv(k, v, s)).join("")}</section>${ydSectionHtml("Documents", docs.length, "estimates, change orders, invoices and payments", docs, "No documents yet.")}`;
    void pay;
  } else {
    const mine = (DB.comms || []).filter((m) => {
      const R = m.route || {};
      return R.clientId === c.id || X.P.some((p) => p.id === R.projectId);
    });
    const rows = mine
      .sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")))
      .map((m) => ({ id: "mm:" + m.id, sec: "msg", title: `${ydMsgWho(m)}: ${ydMsgAbout(m)}`, meta: [ydMsgKind(m), fmt(String(m.date || "").slice(0, 10))].join(" · "), act: "Open", run: () => ydMsgOpen(m) }))
      .concat((c.activity || []).slice().reverse().map((a, i) => ({ id: "ac:" + i, sec: "log", title: slActivityText(c, a), meta: [a.by, a.t].filter(Boolean).join(" · ") })));
    rows.forEach((r) => r.run && ydAct(r.id, r.run));
    body = ydSectionHtml("Messages", rows.length, "mail, texts, calls, portal chat and what was logged", rows, "No messages yet.");
  }
  const newItems = slClientNewItems(c);
  const plus = newItems.length
    ? `<span class="yd-plus"><button type="button" class="btn yd-plusb" data-ydnew aria-haspopup="menu" aria-expanded="${slClNewOpen}" aria-label="New for ${esc(c.name)}">${ydSvg("plus")}${phone ? "" : "New"}</button>${
        slClNewOpen ? `<div class="yd-menu" role="menu"><span class="yd-mh">New for ${esc(slFirstNames(c))}</span>${newItems.map(([k, l]) => `<button type="button" role="menuitem" data-ydnewitem="${k}">${esc(l)}</button>`).join("")}</div>` : ""
      }</span>`
    : "";
  const job = X.P[0];
  h.innerHTML = `<div class="yd-ph"><button type="button" class="yd-back" data-ydclback aria-label="Back to Clients">${ydSvg("back")}${phone ? "" : "Clients"}</button></div><div class="yd-ph"><div class="grow"><h2>${esc(c.name)}</h2><div class="yd-sub">${esc([job ? shortName(job) : c.propertyAddr, job && "function" == typeof tpJobPct ? `${Math.round(tpJobPct(job))}% done` : "", mayMoney ? `contract ${ydMoney0(F.revised)}` : ""].filter(Boolean).join(" · "))}</div></div>${plus}</div>${tilesHtml}${tabsHtml}${body}`;
}
function slClientNewItems(c) {
  const P = (DB.projects || []).find((p) => p.clientId === c.id),
    may = ydMay,
    withJob = (f) => () => (P && setCurrent(P.id), f());
  return [
    ["msg", "Message", may("chat") || may("comms"), () => ("function" == typeof msgNewThread ? msgNewThread() : setView("chat"))],
    ["task", "Task", may("tkall"), withJob(() => newTaskDialog(P ? { projectId: P.id } : {}))],
    ["note", "Note or Call", may("clients"), withJob(() => crQuick("note"))],
    ["meet", "Meeting", may("tkall"), withJob(() => newTaskDialog(Object.assign({ title: `Meeting with ${c.name}` }, P ? { projectId: P.id } : {})))],
    ["est", "Estimate", may("billing"), () => docNewEstimate(c.id, P ? P.id : "")],
    ["co", "Change Order", may("billing") && !!P, () => newChangeOrderDialog({ clientId: c.id, projectId: P && P.id })],
    ["inv", "Invoice", may("billing"), () => crNewInvoice(c)],
    ["job", "Job", isOwner() || "pm" === role(), () => newProjectDialog(c.id)],
  ]
    .filter((x) => x[2])
    .map((x) => [x[0], x[1], x[3]]);
}

// ---- a deal's page -------------------------------------------------------------------------------------------------
let slDealId = "";
function slOpenDeal(id) {
  slDealId = id;
  ydSection("deal");
  (ROLE_VIEWS[role()] || []).includes("deal") || (ydMay("ovsales") && ROLE_VIEWS[role()].push("deal"));
  setView("deal");
}
function slDealRender() {
  if ("deal" !== view) return;
  const s = ydSection("deal");
  const l = (DB.leads || []).find((x) => x.id === slDealId);
  if (!s) return;
  if (!l) return void (s.innerHTML = '<div class="yd-host"><p class="yd-empty">That deal is not on file.</p></div>');
  const n = slNextStep(l),
    td = slTd(),
    c = slClientOf(l),
    job = slJobOf(l),
    phone = ydPhone(),
    edit = slMayEdit();
  ydActs = {};
  const stages = ["inquiry", "qualified", "site-visit", "proposal"],
    far = Math.max(...(l.history || []).map((h) => stages.indexOf(h.stage)).concat([stages.indexOf(l.stage), "won" === l.stage ? stages.length : -1])),
    road = stages
      .map((st, i) => ({ k: SL_LABEL[st], done: i <= far, at: (l.history || []).filter((h) => h.stage === st).map((h) => h.at).pop() || "" }))
      .concat((l.closePlan || []).map((cp) => ({ k: cp.step, done: !!cp.done, at: cp.due, who: cp.owner })))
      .concat([
        { k: "Set Up the Job", done: !!job, at: "", who: "us" },
        { k: "Signed (Won)", done: "won" === l.stage, at: l.wonAt || "" },
      ]);
  let act = "",
    run = null;
  if ("won" === l.stage && !job) (act = "Set Up the Job"), (run = () => slSetUpJob(l));
  else if (n.task) (act = slVerb(n.title) === "Open" ? "Open the Task" : slVerb(n.title)), (run = () => tkSheet(n.key));
  else if (slIsOpen(l)) (act = "Add a Next Step"), (run = () => newTaskDialog({ title: "", dealId: l.id }));
  run && ydAct("next", run);
  const Q = l.qual || {};
  const why = [
    ["What set it off", Q.trigger],
    ["Today", Q.current],
    ["What it costs them", Q.cost],
    ["What they want", Q.future],
    ["By when", Q.deadline ? fmt(Q.deadline) : ""],
    ["Budget", Q.budgetLow || Q.budgetHigh ? `${ydMoney0(+Q.budgetLow || 0)} to ${ydMoney0(+Q.budgetHigh || 0)}` : ""],
    ["How they decide", Q.decide],
  ].filter((x) => x[1]);
  const late = n.due && n.due < td;
  const body = `<div class="yd-host"><div class="yd-ph"><button type="button" class="yd-back" data-ydgo="ovsales" aria-label="Back to the Pipeline">${ydSvg("back")}${phone ? "" : "Pipeline"}</button></div>
  <div class="yd-ph"><div class="grow"><h2>${esc(l.name)}</h2><div class="yd-sub">${esc([SL_LABEL[l.stage] || l.stage, ydMoney0(l.value || 0), l.addr, l.source].filter(Boolean).join(" · "))}</div></div></div>
  ${edit ? `<div class="yd-ph"><button type="button" class="btn" data-ydrecord="${esc(l.id)}">Open the Full Record</button><span class="small muted">notes, stage, close as won or lost</span></div>` : ""}
  <section class="yd-card"><div class="yd-sh"><h3>Next Step</h3></div><div class="yd-row" data-ydrow="next"><span class="yd-t"><b>${esc("won" === l.stage && !job ? "Set up the job: nothing can be bought or billed until it exists" : n.title)}</b><span>${esc(n.task ? `${n.task.code ? n.task.code + " · " : ""}due ${fmt(n.due)}${n.task.owner ? " · " + n.task.owner : ""}` : slIsOpen(l) ? "No open task on this deal" : "")}</span></span>${n.due ? `<span class="yd-when${late ? " late" : ""}">${esc(late ? `${dayDiff(n.due, td)} days late` : ydWhen(n.due))}</span>` : ""}${act && edit ? `<button type="button" class="btn primary" data-ydact="next">${esc(act)}</button>` : ""}</div></section>
  <section class="yd-card"><div class="yd-sh"><h3>Road to Signed</h3><span class="note">Set Up the Job comes before Won</span></div>${road.map((x) => ydKv(`${x.done ? "Done: " : ""}${x.k}`, x.at ? fmt(String(x.at).slice(0, 10)) : "", x.who ? `by ${x.who}` : "")).join("")}</section>
  <section class="yd-card"><div class="yd-sh"><h3>The Proposal</h3></div>${l.proposal && l.proposal.sentAt ? ydKv("Sent", fmt(l.proposal.sentAt)) : ydKv("Not sent yet", "")}${ydKv("Estimate", c && (c.estimates || []).length ? (c.estimates || []).map((e) => e.number).join(", ") : "No estimate linked yet")}${c ? ydKv("Client record", c.name) : ydKv("Client record", "none on file yet")}</section>
  ${why.length ? `<section class="yd-card"><div class="yd-sh"><h3>Why They Are Buying</h3></div>${why.map(([k, v]) => ydKv(k, "", v)).join("")}</section>` : ""}
  <section class="yd-card"><div class="yd-sh"><h3>People</h3></div>${(l.stakeholders || []).map((p) => ydKv(p.name, p.stance || "", [p.role, p.met ? "met" : "not met yet"].filter(Boolean).join(" · "))).join("") || '<div class="yd-empty">Nobody named yet.</div>'}</section>
  <section class="yd-card"><div class="yd-sh"><h3>Building</h3></div>${Object.entries(l.building || {}).map(([k, v]) => ydKv(k, String(v))).join("") || '<div class="yd-empty">Nothing on the building yet.</div>'}</section>
  <section class="yd-card"><div class="yd-sh"><h3>Every Touch</h3><span class="n">${(l.touches || []).length}</span></div>${(l.touches || []).slice().reverse().map((t) => ydKv(t.note || t.text || t.channel || "A touch", fmt(String(t.at || "").slice(0, 10)), [t.channel, t.direction === "in" ? "from them" : "from us", t.value].filter(Boolean).join(" \u00b7 "))).join("") || '<div class="yd-empty">No touch logged.</div>'}</section></div>`;
  s.innerHTML = body;
}

// ---- forwards, menu, wiring -----------------------------------------------------------------------------------------
(function slMenu() {
  if ("undefined" == typeof MN_SALES) return;
  const items = [["ovsales", "Pipeline"], ["billing", "Estimates", "estimates", YD_ESTIMATES_IN_MENU ? {} : { not: YD_EST_VIA_ACCOUNTING }], ["clients", "Clients"]];
  MN_SALES.splice(0, MN_SALES.length, ...items);
  // with Estimates off the menu, the PM (who has no Accounting group) opens Billing by link only: from a job's Contract
  // and Billing and the Pipeline's Proposals Out (the Accounting lane's MN_LINK registry)

  try {
    // the stage the owner names "Design Proposal" (Sales must-fix 3)
    "undefined" != typeof SL_STAGES && SL_STAGES.forEach((x) => "design" === x[0] && (x[1] = "Design proposal"));
    mnKnowAll();
  } catch (e) {}
})();
function slRenameStage() {
  try {
    (((DB.hub || {}).pipelines) || []).forEach((P) => (P.stages || []).forEach((s) => "design" === s.id && "Design Agreement" === s.label && (s.label = "Design Proposal")));
  } catch (e) {}
}
function slForward() {
  if (!ydOffice()) return;
  const v = view;
  if (["salesnum", "hbforecast", "hbdash"].includes(v) && ydMay("ovsales")) return (view = "ovsales"), (slChip = "need"), (slNumsOpen = !0);
  // a record opened on purpose (a deal's or a lead's full record, a person's, a company's) stays; the old lists land here
  const rec = (o) => "undefined" != typeof hbOpenId && hbOpenId && hbOpenId[o];
  if ("hbdeals" === v && rec("deal")) return;
  if ("scleads" === v && "undefined" != typeof scOpenId && scOpenId) return;
  if (["hbdeals", "hbquotes", "hbsequences", "hbworkspace", "hbplaybooks", "scleads"].includes(v) && ydMay("ovsales")) return (view = "ovsales");
  // the Playbook is the Standard's Sales playbook section: the document, under the Standard
  if ("playbook" === v && ydMay("standard")) return (view = "standard"), (ydStdChip = "doc");
  if ("partners" === v && ydMay("clients")) return (view = "clients"), (clientOpen = null), (docOpen = null), (slClChip = slClChipKeep = "partners");
  if (("hbcontacts" === v && rec("contact")) || ("hbcompanies" === v && rec("company"))) return;
  if (["hbcontacts", "hbcompanies"].includes(v) && ydMay("clients")) return (view = "clients"), (clientOpen = null), (docOpen = null), (slClChip = slClChipKeep = "all");
  if ("billing" === v && !ydEstInMenu() && "sales" === mnLastGrp && ydMay("ovsales")) return (view = "ovsales"), (slChip = "props"), (mnLastGrp = "sales");
}
{
  const base = render;
  render = function () {
    try {
      slForward();
      slRenameStage();
      slTieNewJob();
      slBillingLink();
    } catch (e) {
      console.warn("sales: forward", e);
    }
    const r = base.apply(this, arguments);
    try {
      slPipelineRender();
      slClientsRender();
      slClientRender();
      slDealRender();
      // a client's page and the Clients list share the view: the host belongs to whichever is on
      "clients" === view && (docOpen || (clientOpen && slClOld)) && ydHost("clients", !1);
      ("clients" !== view || !clientOpen) && (slClOld = !1);
      document.querySelectorAll(".view").forEach((e) => e.classList.toggle("on", e.id === "v-" + view));
    } catch (e) {
      console.warn("sales", e);
    }
    return r;
  };
}
"object" == typeof MN_ALIAS && Object.assign(MN_ALIAS, { deal: "ovsales", salesnum: "ovsales", hbforecast: "ovsales", hbdash: "ovsales", partners: "clients", hbcontacts: "clients", hbcompanies: "clients" });
"object" == typeof NAV_LABELS && (NAV_LABELS.deal = "Deal");
document.addEventListener(
  "click",
  (e) => {
    const t = e.target && e.target.closest ? e.target : null;
    if (!t) return;
    const at = (s) => t.closest(s);
    let b;
    if (!at("#v-ovsales, #v-clients, #v-deal")) return;
    if ((b = at("#yd-ovsales [data-ydchip]"))) return e.preventDefault(), (slChip = b.dataset.ydchip), void render();
    if ((b = at("#yd-clients [data-ydchip]"))) return e.preventDefault(), (slClChip = slClChipKeep = b.dataset.ydchip), void render();
    if ((b = at("[data-ydfold='nums']"))) return e.preventDefault(), (slNumsOpen = !slNumsOpen), void render();
    if ((b = at("[data-ydnum]"))) {
      const x = slNums().find((y) => y.k === b.dataset.ydnum);
      return e.preventDefault(), void (x && x.go && x.go());
    }
    if ((b = at("#yd-ovsales [data-ydnew]"))) return e.preventDefault(), (slNewOpen = !slNewOpen), void render();
    if ((b = at("#yd-ovsales [data-ydnewitem]"))) {
      e.preventDefault(), (slNewOpen = !1);
      if ("mail" === b.dataset.ydnewitem) return (ydMsg.chip = "need"), void setView("chat");
      const nl = document.getElementById("oc-newlead");
      return void (nl ? nl.click() : "function" == typeof scLeadSheet ? scLeadSheet() : null);
    }
    if ((b = at("#yd-clients [data-ydnew]"))) return e.preventDefault(), (slClNewOpen = !slClNewOpen), void render();
    if ((b = at("#yd-clients [data-ydnewitem]"))) {
      e.preventDefault(), (slClNewOpen = !1);
      const c = (DB.clients || []).find((x) => x.id === clientOpen),
        it = c && slClientNewItems(c).find((x) => x[0] === b.dataset.ydnewitem);
      return render(), void (it && it[2]());
    }
    if ((b = at("[data-ydnewclient]"))) {
      e.preventDefault();
      const nc = document.getElementById("btn-newclient");
      return void (nc ? nc.click() : "function" == typeof openClientEditor ? openClientEditor("client") : null);
    }
    if ((b = at("[data-ydclback]"))) return e.preventDefault(), (clientOpen = null), (docOpen = null), (slClOld = !1), void render();
    if ((b = at("[data-ydclold]"))) return e.preventDefault(), (slClOld = !0), (clientTab = "fin"), (finTab = "invoices"), void render();
    if ((b = at("#yd-clients [data-ydtab]"))) return e.preventDefault(), (slClTab = b.dataset.ydtab), void render();
    if ((b = at("[data-ydgo]"))) return e.preventDefault(), void setView(b.dataset.ydgo);
    if ((b = at("[data-ydrecord]"))) {
      e.preventDefault();
      const l = (DB.leads || []).find((x) => x.id === b.dataset.ydrecord);
      return void (l && ("inquiry" === l.stage && "function" == typeof scOpen ? scOpen(l.id) : "function" == typeof hbOpen ? (hbOpen("deal", l.id), render()) : null));
    }
    if ((b = at("[data-ydtile]"))) {
      e.preventDefault();
      const k = b.dataset.ydtile;
      return (slClTab = "owe" === k || "left" === k ? "billing" : "overview"), void render();
    }
    if ((b = at("[data-ydact]"))) {
      e.preventDefault(), e.stopPropagation();
      const f = ydActs[b.dataset.ydact];
      return void (f && f());
    }
    if ((b = at("[data-ydrow]")) && !at("button, a")) {
      const f = ydActs[b.dataset.ydrow];
      if (f) return e.preventDefault(), void f();
    }
  },
  !0,
);
