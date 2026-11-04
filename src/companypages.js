/* =====================================================================================================================
   Company and Settings: a hub and six pages (docs/mockups/company/SPEC.md, its chief of staff review; BACKLOG section 10
   items 2, 8 and 9; DECISIONS 11-03: "Insurance and Licenses"; the PM gets his own Team entry; Messages to Clients
   never Act Alone; only the owner changes an approval limit; a required firm record not on file is Needs You).

   What was wrong. Thirteen pages in two groups. The headcount read 13, 14, "4 of 9" and 9; the PM, a login with ten
   tasks, was not on Team; Billing and Angel shared (917) 555-0104 and the Controller and Alberto (917) 555-0105, because
   two seed tables gave out the same numbers; the assistant's rules sat in four places; The Brain read 18 against 17
   rows (one lesson drafted twice); Obligations mixed vendor certificates with the firm's own policies and never said
   that workers' comp and the trade licenses are not on file at all; the 2-hour client acknowledgement read 0 while two
   clients waited past it; Clear Everything was one click.

   The structure (the hub, cohub, is the group's own page; each row a page with one home):
     Team (team)                    every person once (ydPeople: the logins and the employees, joined); Needs You
                                    (no phone or email, a phone or email two people share, a login with no person);
                                    a person's page: open tasks (Tasks' own count), What Reaches You for Approval (only
                                    the owner changes a limit), Your Assistant (the one rules control, paRulesHtml), What
                                    It Did on Its Own
     The Brain (brain)              To Approve: lessons, changes to the ERP and job checklist steps, each once
     Insurance and Licenses         the firm's own policies, licenses and filings; the required records the Standard
       (obligations)                names, missing or lapsing, are Needs You; vendor certificates and a job's permits
                                    stay with their record
     Connections (conn)             the firm's one-time Google setup, your account, banks and cards with reconciled dates
     The SmartDesign Standard       Open Today (the measured lines with rows), then the document
       (standard)
     Company Settings (cosettings)  the firm, money and buying, sales, data; As Of, Clear Everything and Turn the Demo On
                                    behind the owner and a typed confirm
   Old pages forward: Company (ovoffice) and Settings (setup) to the hub; Sales Settings, Your Own Data and Problem
   Reports to Company Settings, which opens each in place; Calendar and Meetings live in Your Day (src/yourday.js).

   Design gate (BACKLOG 1.16). No new store: people are DB.users and DB.employees read as one list; lessons the queue's
   rows; obligations DB.obligations; the rules DB.asst; limits DB.company. Nothing posts money.
   ===================================================================================================================== */

// ---- people: one list, one headcount ------------------------------------------------------------------------------
function ydPeople() {
  const out = [],
    seen = new Set(),
    E = DB.employees || [];
  (DB.users || [])
    .filter((u) => u && u.id && u.name && "client" !== u.role && !/^mb_/.test(u.role || ""))
    .forEach((u) => {
      const e = E.find((x) => x.id === (u.employeeId || u.empId)) || E.find((x) => String(x.name || "").toLowerCase() === String(u.name).toLowerCase()) || null;
      e && seen.add(e.id), seen.add("n:" + u.name.toLowerCase());
      out.push({ id: u.id, uid: u.id, empId: e ? e.id : "", name: u.name, role: u.role, title: (e && (e.role || e.title)) || ("undefined" != typeof ROLE_NAMES && ROLE_NAMES[u.role]) || u.role, email: u.email || (e && e.email) || "", phone: u.phone || (e && e.phone) || "", login: !0 });
    });
  E.filter((e) => e && !1 !== e.active && !seen.has(e.id) && !seen.has("n:" + String(e.name || "").toLowerCase())).forEach((e) =>
    out.push({ id: "em:" + e.id, uid: "", empId: e.id, name: e.name, role: "", title: e.role || e.title || "Team", email: e.email || "", phone: e.phone || "", login: !1 }),
  );
  return out;
}
const ydDigits = (p) => String(p || "").replace(/\D/g, "").replace(/^1(?=\d{10}$)/, "");
// the data lint: a phone or email two people share; a login that is no person
function ydPeopleLint() {
  const P = ydPeople(),
    dupes = [],
    by = {};
  P.forEach((p) => {
    [["phone", ydDigits(p.phone)], ["email", String(p.email || "").toLowerCase()]].forEach(([k, v]) => {
      if (!v) return;
      const key = k + ":" + v;
      (by[key] = by[key] || []).push(p);
    });
  });
  Object.entries(by).forEach(([k, L]) => L.length > 1 && dupes.push({ k: k, who: L.map((p) => p.name), v: "phone" === k.split(":")[0] ? L[0].phone : L[0].email }));
  const noPerson = (DB.users || []).filter((u) => u && u.id && "client" !== u.role && !/^mb_/.test(u.role || "") && !P.some((p) => p.uid === u.id)).map((u) => u.id);
  return { dupes: dupes, noPerson: noPerson };
}
// the two seed tables gave Billing Angel's number and the Controller Alberto's (p2nav's table was fixed to agree):
// a book seeded before the fix gets the numbers the seed now gives
(function ydPhoneRepair() {
  try {
    if (!DB || !DB.users || DB.__ydPhones) return;
    const fix = { u_billing: "(917) 555-0109", u_controller: "(917) 555-0110" },
      old = { u_billing: "(917) 555-0104", u_controller: "(917) 555-0105" };
    DB.users.forEach((u) => fix[u.id] && u.phone === old[u.id] && (u.phone = fix[u.id]));
    DB.__ydPhones = 1;
  } catch (e) {}
})();
function ydTasksOf(p) {
  try {
    const me = currentUser() || {};
    return p.uid && p.uid === me.id ? openTasks("me") : openTasks(p.name);
  } catch (e) {
    return [];
  }
}

// ---- The Brain: each proposal once ----------------------------------------------------------------------------------
const ydBrainKey = (it) =>
  String(it.title || "")
    .replace(/^Lesson:\s*/i, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
let ydBrainMemo = { k: "", L: [] };
function ydBrainItems() {
  const k = ["undefined" != typeof td2Tick ? td2Tick : 0, (currentUser() || {}).id].join("|");
  if (ydBrainMemo.k === k) return ydBrainMemo.L;
  let R = [];
  try {
    // the full queue: the owner's approvals are the exceptions, his lessons and rule changes are here
    R = isOwner() ? ydQueueBase().filter((it) => ["change", "lesson", "learn"].includes(it.kind)) : [];
  } catch (e) {}
  // Two proposals drafted from the same events (a lesson and the meeting reader's rule) are two records, each decided on
  // its own: both rows show, the second says it is the twin (a folded row left the other open after a decision)
  const at = {};
  R.forEach((it) => {
    const key = ydBrainKey(it);
    at[key] ? (it.ydTwin = at[key]) : (at[key] = it);
  });
  return (ydBrainMemo = { k: k, L: R }).L;
}
const YD_BRAIN_GROUP = { learn: "Lessons for the Firm", change: "Changes to the ERP", lesson: "Job Checklist Steps" };
let ydBrainChip = "need";
// The old Brain's own tabs (Workload, Lessons, the hands, Watching) live in Ask's Brain tab, as before: a link or a
// tap that names one (bnTab changed from what this page last saw) opens it there; The Brain page stays this one.
let ydBrainOld = !1,
  ydBrainTab = null;
function ydBrainSeen() {
  if ("brain" !== view) return void ((ydBrainOld = !1), (ydBrainTab = null));
  const t = "undefined" != typeof bnTab ? bnTab : "";
  null !== ydBrainTab && t !== ydBrainTab && (ydBrainOld = !0);
  ydBrainTab = t;
}
if ("function" == typeof renderBrain) {
  const base = renderBrain;
  renderBrain = function () {
    const r = base.apply(this, arguments);
    try {
      ydBrainSeen();
      ydBrainOld && "brain" === view && ydBrainFull();
    } catch (e) {}
    return r;
  };
}
// what the brain suggests from what happened (bnSuggestLessons): a lesson to approve or one to teach, each with its
// button, beside the queue's own proposals (nothing it proposes is only on a hidden page)
function ydBrainSugs() {
  try {
    const have = new Set(ydBrainItems().map((it) => String(it.id)));
    return ("function" == typeof bnSuggestLessons ? bnSuggestLessons() : []).map((x, i) => Object.assign({ ydI: i }, x)).filter((x) => !(x.learn && have.has(String(x.learn))));
  } catch (e) {
    return [];
  }
}
// the full Brain: Ask's Brain tab for the owner, Findings' Brain for anyone else (the assistant's own redirect)
function ydBrainFull() {
  ydBrainOld = !1;
  setTimeout(() => {
    try {
      isOwner() ? (paTabWant = "brain") : ((paTabWant = "findings"), (paFindSeg = "brain"));
      view = "pa";
      render();
    } catch (e) {}
  }, 0);
}
function ydBrainRender() {
  try {
    ydBrainSeen();
  } catch (e) {}
  const on = "brain" === view && !ydBrainOld;
  const h = ydHost("brain", on);
  if (!on || !h) return;
  const L = ydBrainItems();
  let ydSugAll = [];
  try {
    ydSugAll = isOwner() && "function" == typeof bnSuggestLessons ? bnSuggestLessons() : [];
  } catch (e) {}
  ydActs = {};
  const S = ydBrainSugs(),
    sugRows = S.map((x, i) => {
      const id = "s" + i;
      ydAct(id, () => {
        if (x.learn && isOwner() && "function" == typeof lnApprove) {
          const l = lnApprove(x.learn);
          l && (toast(`Lesson approved: ${l.title}`, () => ((bnTab = "lessons"), setView("brain"))), render());
        } else "function" == typeof bnTeachModal && bnTeachModal(Object.assign({}, x));
      });
      return { id: id, sec: "sug", title: String(x.title || "A lesson"), meta: String(x.why || (x.then && x.then.title) || "from what happened").slice(0, 160), act: x.learn && isOwner() ? "Approve" : "Teach It", i: x.ydI };
    }),
    sugHtml = sugRows.length ? `<section class="yd-card"><div class="yd-sh"><h3>Suggested From What Happened</h3><span class="n">${sugRows.length}</span><span class="note">${isOwner() ? "lessons the brain drew from the record; a yes makes each a rule" : "lessons the brain drew from the record; teach one and the owner approves it"}</span></div>${sugRows.map((r) => ydRowHtml(r).replace(`data-ydact="${r.id}"`, isOwner() ? `data-ydact="${r.id}" data-bnsug="${r.i}"` : `data-ydteach="${r.id}" data-bnsug="${r.i}"`)).join("")}</section>` : "",
    full = `<div class="yd-ph"><button type="button" class="btn" data-ydbrainfull>Open the Full Brain</button><span class="small muted">every lesson, the workload by person, what it watches</span></div>`;
  const rows = L.map((it, i) => {
    let c = null;
    try {
      c = tdCard(it);
    } catch (e) {}
    c = c || { line1: esc(it.title), why: esc(it.detail || ""), verb: "Open", run: () => mGo(it.open) };
    const id = "b" + i;
    ydAct(id, () => c.run());
    const meta = td2Txt ? td2Txt(c.why) : it.detail;
    return { id: id, sec: "need", kind: it.kind, title: String(td2Txt ? td2Txt(c.line1) : it.title).replace(/^Lesson:\s*/, ""), meta: it.ydTwin ? `drafted from the same events as the row of the same name above; decide each \u00b7 ${meta}`: meta, act: isOwner() ? c.verb || "Open" : "", sug: "learn" === it.kind ? ydSugAll.findIndex((x) => x.learn && String(x.learn) === String(it.id)) : -1 };
  });
  const groups = rows.length
    ? `<section class="yd-card">${["learn", "change", "lesson"]
        .map((k) => {
          const R = rows.filter((r) => r.kind === k);
          return R.length ? `<div class="yd-sh"><h3>${esc(YD_BRAIN_GROUP[k])}</h3><span class="n">${R.length}</span></div>${R.map((r) => (r.sug >= 0 && r.act ? ydRowHtml(r).replace(`data-ydact="${r.id}"`, `data-ydact="${r.id}" data-bnsug="${r.sug}"`) : ydRowHtml(r))).join("")}` : "";
        })
        .join("")}</section>`
    : "";
  let read = "";
  if ("read" === ydBrainChip) {
    const M = (DB.meetings || []).map((m, i) => ({ id: "rm" + i, sec: "read", title: `Notes: ${m.title}`, meta: fmt(m.date), act: "" }));
    const lessons = (DB.lessons || []).slice(0, 20).map((x, i) => ({ id: "rl" + i, sec: "read", title: String(x.title || x.text || x.what || "A lesson"), meta: x.status || "", act: "" }));
    read = ydSectionHtml("What It Read", M.length, "meeting notes and mail the brain learned from", M, "Nothing read yet.") + (lessons.length ? ydSectionHtml("Lessons on Record", lessons.length, "", lessons) : "");
  }
  h.innerHTML = `<div class="yd-ph"><div class="grow"><h2>The Brain</h2><div class="yd-sub">${isOwner() ? `${ydPlural(L.length, "change waits", "changes wait")} on your yes: what the firm learned and wants to change` : "The owner approves what the firm learned; it shows here once he does"}</div></div></div>${ydChipsHtml(
    [
      { k: "need", label: "To Approve", n: L.length || "" },
      { k: "read", label: "What It Read", n: "" },
    ],
    ydBrainChip,
    "brain",
  )}${"need" === ydBrainChip ? (groups || (sugHtml ? "" : '<section class="yd-card"><div class="yd-empty">Nothing waits on your approval.</div></section>')) + sugHtml : read}${full}`;
}

// ---- Insurance and Licenses ------------------------------------------------------------------------------------------
// The firm's required records (the Standard's company standards; law ranks second): what must be on file
const YD_REQUIRED = [
  { k: "gl", label: "General Liability Insurance", rx: /general liability/i, kind: "insurance" },
  { k: "wc", label: "Workers' Comp and Disability", rx: /workers'? ?comp|disability/i, kind: "insurance", why: "a crew is on payroll", need: () => (DB.payroll || []).length > 0 || (DB.employees || []).length > 0 },
  { k: "trade", label: "Trade Licenses: Plumbing and Electrical", rx: /(plumb|electric)[^.]*licen|licen[^.]*(plumb|electric)|master (plumber|electrician)/i, kind: "license", why: "SD Plumbing and SD Electric work under them" },
  { k: "llc", label: "LLC Biennial Statement", rx: /biennial/i, kind: "filing" },
];
const ydObLive = (o) => o && !["cancelled", "void", "deleted", "removed"].includes(o.status);
const ydObFirm = (o) => (o.covers || []).includes("company");
const ydObName = (o) => o.name || o.title || "";
function ydInsNeeds() {
  const td = today(),
    O = (DB.obligations || []).filter(ydObLive),
    out = [];
  YD_REQUIRED.forEach((R) => {
    if (R.need && !R.need()) return;
    const o = O.find((x) => R.rx.test(ydObName(x)));
    if (!o) out.push({ id: "req:" + R.k, sec: "need", title: `${R.label}: not on file`, meta: R.why ? `required: ${R.why}` : "required by law; the Standard ranks the law second", when: "Not on file", late: !0, act: "Add It", run: () => ydObNew(R) });
  });
  O.filter(ydObFirm).forEach((o) => {
    const exp = o.expires || "",
      lead = +o.renewLead || 30,
      lapsed = exp && exp < td,
      soon = exp && !lapsed && dayDiff(td, exp) <= lead;
    (lapsed || soon) && out.push({ id: "ob:" + o.id, sec: "need", title: ydObName(o), meta: `${o.party || ""}${lapsed ? ` · lapsed ${fmt(exp)}` : ` · expires ${fmt(exp)}; renew inside ${lead} days`}`, when: lapsed ? "Lapsed" : `${dayDiff(td, exp)} days`, late: !0, act: "Renew", run: () => ("function" == typeof bnObModal ? bnObModal(o.id) : setView("obligations")) });
  });
  DB.company && !String(DB.company.lic || "").trim() && out.push({ id: "lic", sec: "need", title: "The license number on our documents is blank", meta: "estimates, contracts and invoices print it; Company Settings holds it", when: "Blank", late: !0, act: "Fill It In", run: () => ydOpenSettings("firm") });
  return out;
}
function ydObNew(R) {
  if ("function" == typeof bnObModal) return bnObModal();
  setView("obligations");
}
// Compliance on Today: vendors on site without insurance, and the firm's own required records
function ydCompliance() {
  let V = [];
  try {
    V = PRED.vendorsCoiLapsing.rows() || [];
  } catch (e) {}
  return V.concat(ydInsNeeds());
}
function ydInsRender() {
  const on = "obligations" === view && ydOffice();
  const h = ydHost("obligations", on);
  if (!on || !h) return;
  const need = ydInsNeeds(),
    needIds = new Set(need.map((r) => r.id.replace(/^ob:/, ""))),
    O = (DB.obligations || []).filter(ydObLive);
  ydActs = {};
  need.forEach((r) => ydAct(r.id, r.run));
  const file = O.filter((o) => ydObFirm(o) && !needIds.has(o.id)).map((o) => ({ id: "f:" + o.id, sec: "file", title: ydObName(o), meta: [o.party, o.number, o.amount ? `${ydMoney0(o.amount)} a year` : ""].filter(Boolean).join(" · "), when: o.expires ? `to ${fmt(o.expires)}` : "", act: "Open", run: () => bnObModal(o.id) }));
  const kept = O.filter((o) => !ydObFirm(o)).map((o) => {
    const v = (o.covers || []).includes("vendor") || /certificate of insurance/i.test(ydObName(o)),
      p = (DB.projects || []).find((x) => (o.covers || []).includes(x.id));
    const vend = v && (DB.vendors || []).find((x) => (o.covers || []).includes("vendor") && (o.party === x.name || String(o.name || "").includes(x.name)));
    return { id: "k:" + o.id, sec: "kept", title: ydObName(o), meta: v ? "kept with the vendor" : p ? `kept with ${shortName(p)}` : "kept with its record", when: o.expires ? fmt(o.expires) : "", act: vend ? "Open Vendor" : "Open", run: () => (vend && "function" == typeof openVendor ? (setView("vendors"), setTimeout(() => openVendor(vend.id), 60)) : v ? setView("vendors") : p ? ("function" == typeof jpOpenJob ? jpOpenJob(p.id, "files") : setView("files")) : bnObModal(o.id)) };
  });
  // each vendor's certificate is kept on the vendor (the old page listed them with Open Vendor): one tap to its record
  (DB.vendors || [])
    .filter((v) => v && v.insuranceExp)
    .forEach((v) => kept.push({ id: "kv:" + v.id, sec: "kept", title: `${v.name}: certificate of insurance`, meta: "kept with the vendor", when: v.insuranceExp < today() ? `lapsed ${fmt(v.insuranceExp)}` : `to ${fmt(v.insuranceExp)}`, late: v.insuranceExp < today(), act: "Open Vendor", run: () => (setView("vendors"), "function" == typeof openVendor && setTimeout(() => openVendor(v.id), 60)) }));
  file.concat(kept).forEach((r) => ydAct(r.id, r.run));
  h.innerHTML = `<div class="yd-ph"><div class="grow"><h2>Insurance and Licenses</h2><div class="yd-sub">The firm's own policies, licenses and filings, and what lapses</div></div>${isOwner() || "controller" === role() ? `<button type="button" class="btn" data-ydobnew>New Policy, License or Filing</button>` : ""}</div>${ydSectionHtml("Needs You", need.length, "missing, lapsed or inside its renewal", need, "Everything required is on file and current.")}${ydSectionHtml("On File", file.length, "", file, "Nothing else on file.")}${ydFoldHtml("kept", "Kept With Their Record", ydKeptOpen, kept.map(ydRowHtml).join("") || '<div class="yd-empty">Nothing.</div>', kept.length)}`;
}
let ydKeptOpen = !1;

// ---- Team and a person -----------------------------------------------------------------------------------------------
let ydPersonId = "",
  ydPersonKeep = !1;
function ydOpenPerson(id) {
  (ydPersonId = id), (ydPersonKeep = !0), setView("team");
}
function ydTeamNeeds(P) {
  const L = ydPeopleLint(),
    out = [];
  L.dupes.forEach((d, i) => out.push({ id: "dup" + i, sec: "need", title: `${d.who.join(" and ")} share ${d.v}`, meta: "a text to one reaches the other; give each person their own", act: "Fix It", run: () => ydOpenPerson((P.find((p) => p.name === d.who[d.who.length - 1]) || {}).id) }));
  L.noPerson.forEach((u) => out.push({ id: "np:" + u, sec: "need", title: `${u}: a login with no person`, meta: "every login points at a person", act: "Open", run: () => ydOpenPerson(u) }));
  const none = P.filter((p) => !p.phone && !p.email),
    noMail = P.filter((p) => p.phone && !p.email);
  none.length && out.push({ id: "nocontact", sec: "need", title: `${ydPlural(none.length, "person has", "people have")} no phone or email`, meta: none.map((p) => p.name).join(", "), act: "Open", run: () => ydOpenPerson(none[0].id) });
  noMail.length && out.push({ id: "nomail", sec: "need", title: `${ydPlural(noMail.length, "person has", "people have")} no email`, meta: noMail.map((p) => p.name).join(", "), act: "Open", run: () => ydOpenPerson(noMail[0].id) });
  return out;
}
function ydTeamRender() {
  const on = "team" === view && ydOffice();
  const h = ydHost("team", on);
  if (!on || !h) return;
  if (ydPersonId) return ydPersonRender(h);
  const P = ydPeople(),
    td = today(),
    need = ydTeamNeeds(P);
  ydActs = {};
  need.forEach((r) => ydAct(r.id, r.run));
  const rows = P.map((p) => {
    const T = ydTasksOf(p),
      late = T.filter((t) => t.due && t.due < td).length;
    return { p: p, n: T.length, late: late };
  })
    .sort((a, b) => b.n - a.n || String(a.p.name).localeCompare(String(b.p.name)))
    .map((x) => ({ id: x.p.id, sec: "all", title: `${x.p.name}${x.p.uid === (currentUser() || {}).id ? " (you)" : ""}`, meta: [x.p.title, x.p.phone || "no phone", x.p.email || "no email", x.p.login ? "" : "no login"].filter(Boolean).join(" · "), amt: x.n ? `${x.n} open${x.late ? `, ${x.late} late` : ""}` : "", act: "Open", run: () => ydOpenPerson(x.p.id) }));
  rows.forEach((r) => ydAct(r.id, r.run));
  h.innerHTML = `<div class="yd-ph"><div class="grow"><h2>Team</h2><div class="yd-sub">${P.length} people · most loaded first · open one for their limits and their assistant</div></div></div>${need.length ? ydSectionHtml("Needs You", need.length, "", need) : ""}${ydSectionHtml("Everyone", P.length, "", rows)}`;
}
// What reaches each role for approval (DECISIONS 10-26: the owner sees exceptions only)
function ydLimits(p) {
  const po = +((DB.company || {}).poApprovalOver || 1e4);
  if ("owner" === p.role)
    return [
      ["A bill paid before it was approved", "Always"],
      ["A bill over its PO, or with no PO", "Always"],
      ["A vendor's bank details changed, or a first payment to a new vendor", "Always"],
      ["A purchase order over", money(po).replace(/\.00$/, ""), "po"],
      ["Payroll, split by job, before pay day", "Every run"],
    ];
  return (
    {
      pm: [["Bills on your jobs within their PO", "You recommend"], ["Hours on your jobs", "You approve"], ["Change orders on your jobs", "You send"], [`Purchase orders up to ${money(po).replace(/\.00$/, "")}`, "Without the owner"]],
      coord: [[`Purchase orders up to ${money(po).replace(/\.00$/, "")}`, "You issue"], ["Vendor bills you enter", "You submit"]],
      billing: [["Invoices and applications", "You send"], ["Payments recorded", "You record"]],
      controller: [["Bills approved to pay", "You schedule"], ["The books by the 10th", "You close"]],
    }[p.role] || [["Nothing reaches this person for approval", ""]]
  );
}
function ydPersonRender(h) {
  const P = ydPeople(),
    p = P.find((x) => x.id === ydPersonId || x.uid === ydPersonId);
  if (!p) return (ydPersonId = ""), void ydTeamRender();
  const me = currentUser() || {},
    self = p.uid === me.id,
    td = today(),
    T = ydTasksOf(p),
    late = T.filter((t) => t.due && t.due < td).length,
    lim = ydLimits(p),
    owner = isOwner(),
    phone = ydPhone();
  let did = [];
  try {
    const A = (DB.asst || {})[p.uid] || {};
    did = (A.log || []).slice(0, 8);
  } catch (e) {}
  const rules = p.uid && "function" == typeof paRulesHtml && (self || owner) ? paRulesHtml(p.uid) : '<div class="yd-empty">No login, so no assistant yet.</div>';
  h.innerHTML = `<div class="yd-ph"><button type="button" class="yd-back" data-ydteamback aria-label="Back to Team">${ydSvg("back")}${phone ? "" : "Team"}</button></div>
  <div class="yd-ph"><div class="grow"><h2>${esc(p.name)}${self ? " (you)" : ""}</h2><div class="yd-sub">${esc([p.title, p.phone || "no phone on file", p.email || "no email on file"].join(" · "))}</div></div>${p.uid && !self && ydMay("chat") ? `<button type="button" class="btn" data-p2nmsg="${esc(p.uid)}">Message</button>` : ""}${p.email && !self && "function" == typeof p2nCompose && (ydMay("comms") || ydMay("chat")) ? `<button type="button" class="btn" data-ydmail="${esc(p.id)}">Email</button>` : ""}</div>
  <section class="yd-card"><div class="yd-sh"><h3>Open Tasks</h3></div><div class="yd-row" data-ydrow="tasks" role="button" tabindex="0"><span class="yd-t"><b>${T.length} open${late ? `, ${late} late` : ""}</b><span>${esc(self ? "the same list as your Tasks' Mine" : `the same list as Tasks' Team chip, under ${p.name}`)}</span></span><button type="button" class="btn" data-ydgo="tkall">Open Tasks</button></div></section>
  <section class="yd-card"><div class="yd-sh"><h3>${self ? "What Reaches You for Approval" : "What Reaches Them for Approval"}</h3><span class="note">${owner ? "you change a limit; nobody else can" : "only the owner changes a limit"}</span></div>${lim
    .map(([k, v, edit]) => (edit ? `<div class="yd-kv"><span>${esc(k)}</span><label class="small"><span class="muted">$</span><input type="number" min="0" step="500" data-ydlimit="${esc(edit)}" value="${+((DB.company || {}).poApprovalOver || 1e4)}" style="width:110px;min-height:44px"${owner ? "" : " disabled"} aria-label="${esc(k)}"></label></div>` : ydKv(k, v)))
    .join("")}</section>
  <section class="yd-card"><div class="yd-sh"><h3>${self ? "Your Assistant" : "Their Assistant"}</h3><span class="note">Act Alone, Ask First or Hand It to Me; messages to clients, money and commitments always wait for a person</span></div><div style="padding:8px 16px 12px">${rules}</div></section>
  <section class="yd-card"><div class="yd-sh"><h3>What It Did on Its Own</h3><span class="n">${did.length}</span></div>${did.map((e) => ydKv(String(e.what || e.kind || "Did"), e.stamp ? String(e.stamp).slice(0, 16) : e.at ? String(e.at).slice(0, 10) : "", e.why || "")).join("") || '<div class="yd-empty">Nothing yet: everything it did was proposed first.</div>'}</section>
  <section class="yd-card"><div class="yd-sh"><h3>${self ? "Your Accounts" : "Their Accounts"}</h3></div>${ydKv("Google", (DB.conn && DB.conn[p.uid] && DB.conn[p.uid].google) ? "Connected" : "Not connected", "mail, calendar and drive, read by their assistant")}</section>`;
}

// ---- Connections ------------------------------------------------------------------------------------------------------
let ydConnOld = !1;
function ydConnRender() {
  const on = "conn" === view && ydOffice() && !ydConnOld;
  const h = ydHost("conn", on);
  if (!on || !h) return;
  const me = currentUser() || {},
    firm = !!(DB.company && (DB.company.googleClientId || DB.company.gClientId || (DB.integrations && DB.integrations.google && DB.integrations.google.clientId))),
    mine = !!(DB.conn && DB.conn[me.id] && DB.conn[me.id].google),
    owner = isOwner();
  ydActs = {};
  const rows = [];
  rows.push({ id: "firm", sec: "setup", title: "The Firm's Google Setup", meta: firm ? "Done once for everybody" : "Not done: a ten-minute job in the Google Cloud console, once for everybody, before anyone connects", when: firm ? "Set up" : "Not set up", late: !firm, act: firm ? "Open" : owner ? "Set It Up" : "", primary: !firm && owner, run: () => ((ydConnOld = !0), render()) });
  rows.push({ id: "me", sec: "mine", title: "Your Google Account", meta: mine ? `${(DB.conn[me.id].google || {}).email || "connected"}: your assistant reads your mail, calendar and drive` : firm ? "Not connected: your assistant cannot read your mail" : "Waits on the firm's setup above", when: mine ? "Connected" : "Not connected", act: mine ? "Open" : firm ? "Connect" : "", primary: !!firm && !mine && !(!firm && owner), run: () => ((ydConnOld = !0), render()) });
  (DB.accounts || []).forEach((a) => {
    const d = a.recon && a.recon.date;
    rows.push({ id: "acct:" + a.id, sec: "bank", title: `${a.name} ····${a.last4 || ""}`, meta: `${a.type === "card" ? "Card" : "Bank"} · ${d ? `Reconciled through ${fmt(d)}` : "Never reconciled"}; reconciling is in Accounting, Banking`, when: d ? fmt(d) : "Never", late: !d, act: ydMay("bank") ? "Open" : "", run: () => setView("bank") });
  });
  rows.push({ id: "books", sec: "books", title: "QuickBooks", meta: "a bridge for comparison and import, never the truth", act: "", run: null });
  rows.push({ id: "proc", sec: "books", title: "The Purchasing Mailbox", meta: "procurement@smartdesign.nyc sends RFQs and POs with the sender in CC; connected once here", act: "", run: null });
  rows.forEach((r) => r.run && ydAct(r.id, r.run));
  // one blue: the firm's setup first; once it is done, your own account
  let blue = !1;
  rows.forEach((r) => (r.primary = r.primary && !blue && (blue = !0)));
  h.innerHTML = `<div class="yd-ph"><div class="grow"><h2>Connections</h2><div class="yd-sub">What the ERP reads, and how fresh it is</div></div></div>${ydSectionHtml("Google", 2, "", rows.filter((r) => ["setup", "mine"].includes(r.sec)))}${ydSectionHtml("Banks and Cards", rows.filter((r) => "bank" === r.sec).length, "", rows.filter((r) => "bank" === r.sec), "No account connected.")}${ydSectionHtml("Mail and Books", null, "", rows.filter((r) => "books" === r.sec))}`;
}

// ---- The SmartDesign Standard -----------------------------------------------------------------------------------------
// the 2-hour client acknowledgement measures client mail too: a client's message waiting past 2 business hours
(function ydClientAck() {
  if ("undefined" == typeof STANDARD_RULES) return;
  const R = STANDARD_RULES.find((x) => "clientAck" === x.id);
  if (!R || R.ydMail) return;
  const base = R.rows;
  R.ydMail = 1;
  R.partial = "Measured on portal questions and on client mail: a client's message with no answer past 2 business hours.";
  R.rows = function () {
    const out = base ? base.apply(this, arguments) || [] : [];
    try {
      const o = (DB.users || []).find((u) => "owner" === u.role),
        keep = DB.deviceUser;
      let L = [];
      o && (DB.deviceUser = o.id);
      try {
        L = cmNeedsAnswer();
      } finally {
        DB.deviceUser = keep;
      }
      L.filter((c) => {
        const r = c.route || {};
        return (r.clientId || r.existingJob) && "call" !== c.channel && stdWorkHoursSince(String(c.date || "")) > 2;
      }).forEach((c) => out.push({ key: "mail:" + c.id, what: `${ydMsgWho(c)} wrote on ${fmtL(String(c.date || "").slice(0, 10))}: ${String(c.subject || "").slice(0, 60)}`, sub: ydMsgWhere(c), go: () => ydMsgOpen(c) }));
    } catch (e) {}
    return out;
  };
})();
let ydStdChip = "open";
function ydStdRows() {
  if ("undefined" == typeof STANDARD_RULES) return [];
  return STANDARD_RULES.filter((R) => !1 !== R.measured)
    .map((R) => {
      let n = 0;
      try {
        n = standardRuleRows(R).length;
      } catch (e) {}
      const cite = (("function" == typeof standardCite && standardCite(R.c)) || {}).text || R.id;
      const x = { id: "std:" + R.id, sec: "need", n: n, rules: [R], title: String(cite).replace(/\s+/g, " ").slice(0, 160), meta: `${("undefined" != typeof ROLE_NAMES && ROLE_NAMES[R.owner]) || R.owner} owns it`, amt: String(n), act: "Open" };
      x.run = () => ydStdOpen(x.rules);
      return x;
    })
    .filter((x) => x.n > 0)
    .reduce((out, x) => {
      const same = out.find((y) => y.title === x.title);
      same ? ((same.n += x.n), (same.amt = String(same.n)), (same.rules = same.rules.concat(x.rules))) : out.push(x);
      return out;
    }, []);
}
function ydStdOpen(RR) {
  const R = RR[0],
    L = RR.flatMap((x) => standardRuleRows(x));
  const m = mbModal(esc(((standardCite(R.c) || {}).text || R.id).slice(0, 80)), L.map((x, i) => `<div class="yd-row" data-ydstdrow="${i}"><span class="yd-t"><b>${esc(x.what || "")}</b><span>${esc(x.sub || "")}</span></span></div>`).join("") || '<p class="muted">Nothing today.</p>', { submit: null });
  m.querySelectorAll("[data-ydstdrow]").forEach((r) => (r.onclick = () => {
    const x = L[+r.dataset.ydstdrow];
    x && x.go && (mbCloseModal(), x.go());
  }));
}
function ydStdRender() {
  const on = "standard" === view && ydOffice();
  const h = ydHost("standard", on);
  if (!on || !h) return;
  const rows = ydStdRows();
  ydActs = {};
  rows.forEach((r) => ydAct(r.id, r.run));
  const s = document.getElementById("v-standard");
  // The Document is the page as it was, under the chips
  ydOwn(s, "open" === ydStdChip);
  let ver = "";
  try {
    const S0 = standard();
    ver = `Version ${S0.version || 1}${S0.by ? ", " + S0.by : ""}`;
  } catch (e) {}
  h.innerHTML = `<div class="yd-ph"><div class="grow"><h2>The SmartDesign Standard</h2><div class="yd-sub">${esc(ver)} · every person, agent and assistant works by it</div></div></div>${ydChipsHtml(
    [
      { k: "open", label: "Open Today", n: rows.length || "" },
      { k: "doc", label: "The Document", n: "" },
    ],
    ydStdChip,
    "std",
  )}${"open" === ydStdChip ? ydSectionHtml("Open Today", rows.length, "each measured line with what breaks it today", rows, "Every measured line is met today.") : ""}`;
}

// ---- Company Settings and the hub -------------------------------------------------------------------------------------
let ydSetKeep = !1;
function ydOpenSettings(k) {
  ydSetKeep = !0;
  if ("firm" === k) return (settingsMode = "company"), setView("proj");
  setView(k);
}
function ydConfirm(title, word, warn, run) {
  const m = mbModal(title, `<div class="note warn">${esc(warn)}</div><label class="f"><span class="small">Type ${esc(word)} to go on</span><input data-f="confirm" name="confirm" autocomplete="off" style="min-height:44px"></label>`, { submit: title, onSubmit: (f) => (String(f.confirm || "").trim().toUpperCase() === word ? run(f) : (toast(`Type ${word} to go on`), !1)) });
  const ok = m.querySelector("#mbm-ok"),
    inp = m.querySelector("[data-f=confirm]");
  ok && (ok.disabled = !0);
  inp && (inp.oninput = () => ok && (ok.disabled = inp.value.trim().toUpperCase() !== word));
  return m;
}
function ydSettingsRender() {
  if ("cosettings" !== view) return;
  const s = ydSection("cosettings");
  if (!s) return;
  const owner = isOwner(),
    n = ydPeople().length;
  ydActs = {};
  const row = (id, title, meta, run, act) => (ydAct(id, run), { id: id, sec: "set", title: title, meta: meta, act: act || "Open", run: run });
  const money_ok = ["owner", "controller"].includes(role());
  const firm = !money_ok ? [] : [row("firm", "The Firm", "entities, the company block, documents, appearance, the license number", () => ydOpenSettings("firm"))];
  const money_ = !money_ok ? [] : [row("limits", "Approval Limits", "each person's, on their page in Team; only the owner changes one", () => ydOpenPerson((currentUser() || {}).id)), row("items", "Item Library", "every line an estimate or a PO fills from", () => ydOpenSettings("firm"))];
  const sales = ydMay("hbsettings") ? [row("hbsettings", "Sales Settings", "pipelines and stages (Design Proposal), properties, products", () => ydOpenSettings("hbsettings"))] : [];
  const data = [
    ydMay("rdata") ? row("rdata", "Your Own Data", `${n} people, ${(DB.clients || []).length} clients, ${(DB.vendors || []).length} vendors, ${(DB.projects || []).length} jobs; backups and imports`, () => ydOpenSettings("rdata")) : null,
    ydMay("rpbox") ? row("rpbox", "Problem Reports", "what the team reported, and what became of it", () => ydOpenSettings("rpbox")) : null,
  ].filter(Boolean);
  const clock = owner
    ? [
        row("asof", "As Of", DB.company && DB.company.asOf ? `pinned to ${fmtL(DB.company.asOf)}: every screen reads this date` : "today: every screen reads the real date", () => ydAsOf(), "Change"),
        row("wipe", "Clear Everything", "everything but the settings goes; it cannot be undone from inside the app", () => ydConfirm("Clear Everything", "CLEAR", "Everything except your settings goes: jobs, clients, vendors, people, bills, the ledger.", () => rdWipe("all")), "Clear"),
      ]
    : [];
  const sec = (t, R) => (R.length ? ydSectionHtml(t, null, "", R) : "");
  s.innerHTML = `<div class="yd-host"><div class="yd-ph"><button type="button" class="yd-back" data-ydgo="cohub">${ydSvg("back")}Company and Settings</button></div><div class="yd-ph"><div class="grow"><h2>Company Settings</h2><div class="yd-sub">How the firm is set up</div></div></div>${sec("The Firm", firm)}${sec("Money and Buying", money_)}${sec("Sales", sales)}${sec("Your Data", data)}${owner ? sec("The Clock and the Demo", clock).replace('data-ydact="wipe"', 'data-ydact="wipe" data-ydwipe') : ""}${owner && "function" == typeof ljDemoCard ? ljDemoCard() : ""}</div>`;
}
function ydAsOf() {
  const m = ydConfirm("Change As Of", "CHANGE", "Every screen, figure and timestamp reads this date. Leave it blank for today.", (f) => {
    const d = (m.querySelector("[data-ydasof]") || {}).value || "";
    "function" == typeof appSetDay && appSetDay(d), render(), toast(d ? `Every screen now reads as of ${fmtL(d)}` : "Every screen now reads today");
  });
  const at = m.querySelector(".mbm-bd");
  at && at.insertAdjacentHTML("afterbegin", `<label class="f"><span class="small">As Of</span><input type="date" data-ydasof value="${esc((DB.company && DB.company.asOf) || "")}" style="min-height:44px"></label>`);
}
function ydHubRows() {
  const out = [],
    add = (v, l, sub, n) => ydMay(v) && out.push({ id: v, sec: "hub", title: l, meta: sub, n: n || "", amt: n ? String(n) : "", act: "Open", run: () => setView(v) });
  const P = ydPeople(),
    tn = ydTeamNeeds(P).length,
    bn = ydBrainItems().length,
    insN = ydInsNeeds().length;
  add("team", "Team", `${P.length} people · who approves what · each person's assistant`, tn);
  add("brain", "The Brain", "What the firm learned: lessons and changes to approve", bn);
  add("obligations", "Insurance and Licenses", insN ? ydInsNeeds().map((r) => r.title.replace(/: not on file$/, "")).slice(0, 3).join(" · ") : "Everything required is on file", insN);
  const me = currentUser() || {};
  add("conn", "Connections", `${DB.conn && DB.conn[me.id] && DB.conn[me.id].google ? "Your Google account is connected" : "Your Google account is not connected"} · banks and cards`, 0);
  add("standard", "The SmartDesign Standard", `${ydStdRows().length} measured lines open today`, 0);
  add("cosettings", "Company Settings", "The firm, money and buying, sales stages, your data", 0);
  return out;
}
function ydHubRender() {
  if ("cohub" !== view) return;
  const s = ydSection("cohub");
  if (!s) return;
  const R = ydHubRows();
  ydActs = {};
  R.forEach((r) => ydAct(r.id, r.run));
  s.innerHTML = `<div class="yd-host"><div class="yd-ph"><div class="grow"><h2>Company and Settings</h2><div class="yd-sub">Rarely visited: Today says when something here needs you. Each person's assistant settings live on their page in Team.</div></div></div><section class="yd-card">${R.map((r) => ydRowHtml(Object.assign({}, r, { act: "" }))).join("")}</section></div>`;
}

// ---- the menu, who may open what, forwards and wiring -------------------------------------------------------------------
(function ydFoot() {
  if ("undefined" == typeof MN_FOOT) return;
  MN_FOOT.items.splice(
    0,
    MN_FOOT.items.length,
    ["cohub", "Company and Settings", null, { head: 1 }],
    ["team", "Team"],
    ["brain", "The Brain"],
    ["obligations", "Insurance and Licenses"],
    ["conn", "Connections"],
    ["standard", "The SmartDesign Standard"],
    ["cosettings", "Company Settings"],
  );
  const L = { cohub: "Company and Settings", cosettings: "Company Settings", obligations: "Insurance and Licenses", deal: "Deal" };
  [void 0 !== NAV_LABELS ? NAV_LABELS : null, void 0 !== IA_LABELS ? IA_LABELS : null].forEach((x) => x && Object.assign(x, L));
  try {
    Object.keys(L).forEach((v) => mnKnow(v, L[v])), mnKnowAll();
  } catch (e) {}
  // The Brain is its own page again (the assistant opened it as a tab of Ask)
  "undefined" != typeof PA_REDIRECT && delete PA_REDIRECT.brain;
  // the Chief of Staff is no menu entry: its old link lands on Today (src/yourday.js), and Ask's Findings tab keeps
  // Every Chain under Ask's own heading
  "undefined" != typeof PA_REDIRECT && delete PA_REDIRECT.cos;
  // Messages to Clients never act alone (DECISIONS 11-03)
  try {
    const t = paType("clientMessages");
    t && (t.lock = !0);
  } catch (e) {}
})();
function ydGrant() {
  Object.keys(ROLE_VIEWS).forEach((r) => {
    const rv = ROLE_VIEWS[r],
      M = "object" == typeof MENU && MENU[r];
    if (!rv || !M || "client" === r) return;
    const push = (v) => rv.includes(v) || rv.push(v);
    // the field keeps its short menu: their own page, Connections and the Standard, no hub
    !M.field && ["team", "brain", "obligations", "conn", "standard", "setup", "ovoffice"].some((v) => rv.includes(v)) && push("cohub");
    // Company Settings: the owner's and the controller's; anyone who kept Sales Settings, Your Own Data or Problem
    // Reports finds them there (their rows only)
    (["owner", "controller"].includes(r) || ["hbsettings", "rdata", "rpbox"].some((v) => rv.includes(v))) && push("cosettings");
    rv.includes("ovsales") && push("deal");
    // Sales Settings, Your Own Data and Problem Reports keep their pages, opened from Company Settings' rows: pages by
    // design reached by link and not listed in the menu (the Accounting lane's MN_LINK registry)
    "object" == typeof MN_LINK && ["hbsettings", "rdata", "rpbox"].filter((v) => rv.includes(v)).forEach((v) => ((MN_LINK[r] = MN_LINK[r] || []).includes(v) || MN_LINK[r].push(v)));
  });
}
function ydCoForward() {
  if (!ydOffice()) return;
  const v = view;
  // the old Settings page is Company Settings now (its tiles are Company Settings' rows; the demo switch is there)
  if ("setup" === v && ydMay("cosettings")) return (view = "cosettings");
  if (("ovoffice" === v || "setup" === v) && ydMay("cohub")) return (view = "cohub");
  // Sales Settings, Your Own Data, Problem Reports and the firm's settings stay their own pages, opened from Company
  // Settings' rows and lit under it (MN_ALIAS, mnCur below): nothing that links to them breaks
}
{
  const base = setView;
  setView = function (v) {
    "team" === v && !ydPersonKeep && (ydPersonId = "");
    "conn" === v && (ydConnOld = !1);
    const r = base.apply(this, arguments);
    (ydSetKeep = !1), (ydPersonKeep = !1);
    return r;
  };
}
{
  const base = render;
  render = function () {
    try {
      ydGrant();
      ydCoForward();
      ydSection("cohub"), ydSection("cosettings"), ydSection("deal");
    } catch (e) {
      console.warn("company: forward", e);
    }
    const r = base.apply(this, arguments);
    try {
      ydHubRender();
      ydSettingsRender();
      ydTeamRender();
      ydBrainRender();
      ydInsRender();
      ydConnRender();
      ydStdRender();
      document.querySelectorAll(".view").forEach((e) => e.classList.toggle("on", e.id === "v-" + view));
    } catch (e) {
      console.warn("company", e);
    }
    return r;
  };
}
"object" == typeof MN_ALIAS && Object.assign(MN_ALIAS, { ovoffice: "cohub", setup: "cosettings", hbsettings: "cosettings", rdata: "cosettings", rpbox: "cosettings", playbook: "standard", cos: "home" });
// the firm's settings page (the job settings page in company mode) is lit as Company Settings
if ("function" == typeof mnCur) {
  const base = mnCur;
  mnCur = function (B) {
    try {
      if (B && !B.field && "proj" === view && "undefined" != typeof settingsMode && "company" === settingsMode) {
        const g = B.bottom,
          it = g && g.items.find((x) => "cosettings" === x.v);
        if (it) return { g: g, it: it };
      }
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
document.addEventListener(
  "click",
  (e) => {
    const t = e.target && e.target.closest ? e.target : null;
    if (!t || !t.closest("#v-cohub, #v-cosettings, #v-team, #v-brain, #v-obligations, #v-conn, #v-standard")) return;
    const at = (s) => t.closest(s);
    let b;
    if ((b = at("[data-ydteamback]"))) return e.preventDefault(), (ydPersonId = ""), void render();
    if ((b = at("#yd-brain [data-ydchip]"))) return e.preventDefault(), (ydBrainChip = b.dataset.ydchip), void render();
    if ((b = at("[data-ydmail]"))) {
      e.preventDefault(), e.stopPropagation();
      const P = ydPeople().find((x) => x.id === b.dataset.ydmail);
      return void (P && p2nCompose({ to: `${P.name} <${P.email}>` }));
    }
    if ((b = at("#yd-brain [data-ydbrainfull]"))) return e.preventDefault(), void ydBrainFull();
    // anyone but the owner reads The Brain; Teach It drafts a lesson for the owner's yes (it approves nothing)
    if ((b = at("#yd-brain [data-ydteach]"))) {
      e.preventDefault(), e.stopPropagation();
      const f = ydActs[b.dataset.ydteach];
      return void (f && f());
    }
    if ((b = at("#yd-standard [data-ydchip]"))) return e.preventDefault(), (ydStdChip = b.dataset.ydchip), void render();
    if ((b = at("[data-ydfold='kept']"))) return e.preventDefault(), (ydKeptOpen = !ydKeptOpen), void render();
    if ((b = at("[data-ydobnew]"))) return e.preventDefault(), void ydObNew();
    if ((b = at("[data-ydgo]"))) return e.preventDefault(), (ydPersonId = ""), void setView(b.dataset.ydgo);
    if ((b = at("[data-ydact]"))) {
      e.preventDefault(), e.stopPropagation();
      const f = ydActs[b.dataset.ydact];
      return void (f && f());
    }
    if ((b = at("[data-ydrow]")) && !at("button, a, input, select, label")) {
      const f = ydActs[b.dataset.ydrow];
      if (f) return e.preventDefault(), void f();
    }
  },
  !0,
);
document.addEventListener(
  "change",
  (e) => {
    const i = e.target && e.target.closest ? e.target.closest("[data-ydlimit]") : null;
    if (!i) return;
    if (!isOwner()) return void toast("Only the owner changes an approval limit");
    const v = Math.max(0, Math.round(+i.value || 0)),
      was = (DB.company || {}).poApprovalOver;
    DB.company.poApprovalOver = v;
    try {
      "function" == typeof audit && audit("company", "poApprovalOver", "approval limit changed", was, v, `Purchase orders over ${money(v)} reach the owner`);
    } catch (err) {}
    save(), toast(`Purchase orders over ${money(v).replace(/\.00$/, "")} now reach you`, () => ydOpenPerson((currentUser() || {}).id));
  },
  !0,
);
