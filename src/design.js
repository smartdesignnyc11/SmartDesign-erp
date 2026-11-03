/* =====================================================================================================================
   Design: Selections and Drawings, and the In Design filter of All Projects (Alan, 11-03; docs/mockups/design/SPEC.md,
   its chief-of-staff review and must-fix list; docs/mockups/QUESTIONS.md).

   What was wrong. Design was five pages (the studio overview, Project Board, Filings, Selections, Drawings) and eight tab
   screens. Selections' "To Check 4" sat beside six cards with no spec sheet; its tiles were counts nobody acted on; the
   picture light could go to the Kleins at $385 while the vendor's page said $412; the shower drain was bought on no
   approved estimate line and nobody was asked to bill it back. The studio overview counted "5 designer-days" where the
   designer's Today said 4.

   The structure. Two pages, each opening on Needs You (the designer's next taps, a count equal to its rows, the menu
   reads it), then With Someone Else (who, no number), then the full list one tap down; job and room are filters.
     Selections   every product specified, on every job: why it needs the designer (the checks as reasons), its estimate
                  line or that it has none, one action (bill it back, update the price, find the spec sheet)
     Drawings     the field's questions to the designer, each re-issue (one row naming its sheets), each survey (one row
                  naming its rooms); At the Agency (the filings in review, linking the job's permit record); the sheets
                  By Sheet or By Room
     In Design    All Projects' filter (ovjobs): the design jobs with phase, hours against the proposal (red only when
                  over), survey, drawings and filings; Hours Not Logged at its foot, read as the designer's Today reads it
   The PM and the coordinator have no Design menu; they reach a selection from a decision or a Buy Board row and the
   drawings from the job's Documents.

   Design gate (BACKLOG §1.16). No new store. Selections read DB.sel.items and their checks (selOpenChecks); a client's
   approval is a Decision on the job (p.decisions, owner Client); a bill-back is a draft change order on the job's
   client (c.changeOrders), the record the PM already approves. Drawings read DB.field.raises, the studio rows
   (ovRows("studio")), DB.studio.filings and plSheets. Rows draw with the purchasing pages' markup (src/purchasing.js).
   ===================================================================================================================== */

let pdJob = "",
  pdRoom = "",
  pdGroup = "sheet",
  pdInDesign = !1;
const pdIsDesigner = () => "designer" === puMe();
const pdProj = (id) => (DB.projects || []).find((p) => p.id === id) || null;

// ---- Selections -------------------------------------------------------------------------------------------------------
// the fields of a check the designer fixes (the field needs the spec sheet; the price, SKU and finish match the page;
// an item bought on no line is billed back)
const PD_MINE = ["spec", "price", "sku", "finish", "dims", "funding", "condition", "link"];
function pdLineWord(it) {
  const ref = it.line && "function" == typeof findLine ? findLine(it.line) : null;
  if (ref && ref.doc) {
    let left = "";
    try {
      const f = lineFin(it.line);
      f && (left = ` · ${money(Math.max(0, f.budget - f.actual - f.committed))} left`);
    } catch (e) {}
    return `${ref.doc.number || ""}${ref.line && ref.line.num ? ` line ${ref.line.num}` : ""}${left}`;
  }
  return "No estimate line";
}
// One rule for the price a client may be shown: never older than the vendor's current one (must-fix 3)
function selClientPriceStale(it) {
  const c = it && selOpenChecks(it).find((k) => "price" === k.field && /moved up/i.test(k.msg));
  if (!c) return "";
  const m = String(c.msg).match(/page \$([\d,.]+)/),
    page = m ? m[1] : "";
  return `Update the price to $${page} before ${puClientWord(pdProj(it.projectId))} see it (budgeted ${money(selCost(it))})`;
}
function pdUpdatePrice(it) {
  const clip = it.clip || {},
    c = selOpenChecks(it).find((k) => "price" === k.field),
    m = c && String(c.msg).match(/page \$([\d,.]+)/),
    to = +(clip.price || (m ? m[1].replace(/,/g, "") : 0));
  if (!(to > 0)) return toast("The page's price is not known: verify the item first");
  const was = selCost(it);
  it.cost = to;
  c && (c.cleared = !0);
  try {
    audit("sel", it.id, "price", was, to, "updated to the vendor's current price");
  } catch (e) {}
  save(), render();
  toast(`${it.name}: ${money(was)} to ${money(to)}; the client sees the current price`, { label: "Open", run: () => selOpenItem(it.id) });
}
// The client's approval is a Decision on the job; it never goes out at a stale price
function selSendForApproval(it) {
  const stale = selClientPriceStale(it);
  if (stale) return toast(stale), null;
  const p = pdProj(it.projectId);
  if (!p) return null;
  const open = it.decId && (p.decisions || []).find((d) => d.id === it.decId && "open" === d.status);
  if (open) return toast(`${it.name} is already with ${puClientWord(p)}`), open;
  const d = { id: uid("dec"), name: `Approve ${it.name} at ${money(selUnitPrice(it))} each`, owner: "Client", kind: "selection", ref: it.id, status: "open", due: addWork(today(), 3), notes: `${it.manufacturer || ""} ${it.sku || ""} ${it.finish || ""}`.trim(), scope: { kind: "sel", id: it.id }, options: [], impactDays: 0, impactCost: 0, timeline: [{ at: appNowIso(), by: ((currentUser() || {}).name) || role(), what: "Sent to the client" }] };
  (p.decisions = p.decisions || []).push(d);
  it.decId = d.id;
  save(), render();
  toast(`${it.name} sent to ${puClientWord(p)} for approval`, { label: "Open", run: () => (setCurrent(p.id), setView("dec")) });
  return d;
}
// Bought on no approved estimate line: a drafted change order for the PM (BACKLOG §9 item 6); nothing reaches the client
// until he sends it, or absorbs it with his reason
function pdBillBack(it) {
  const p = pdProj(it.projectId),
    c = p && (DB.clients || []).find((x) => x.id === p.clientId);
  if (!p || !c) return toast("This item has no job or client to bill back to");
  const had = it.billBackCo && (c.changeOrders || []).find((x) => x.id === it.billBackCo && "void" !== x.status);
  if (had) return flowGo.doc(c, "co", had)();
  const co = newDoc(c, "co", {});
  Object.assign(co, {
    projectId: p.id,
    title: `Bill back: ${it.name}`,
    status: "draft",
    billBack: { selId: it.id, by: ((currentUser() || {}).name) || role(), at: appNowIso() },
    lines: [{ id: uid("l"), item: it.name, desc: `${[it.manufacturer, it.sku, it.finish].filter(Boolean).join(", ")}. Bought for ${it.room || "the job"}; on no approved estimate line.`, qty: +it.qty || 1, unit: it.unit || "ea", rate: selUnitPrice(it), cost: selCost(it), taxable: !!it.taxable }],
  });
  (c.changeOrders = c.changeOrders || []).push(co);
  it.billBackCo = co.id;
  // the PM's next tap: send it to the client, or absorb it with a reason
  const pm = ((DB.users || []).find((u) => "pm" === u.role) || {}).name || "the PM";
  (p.actions = p.actions || []).push({ id: uid("a"), title: `Bill back ${it.name}: send ${co.number} to ${puClientWord(p)}, or absorb it with a reason`, assignee: pm, due: today(), priority: "high", status: "todo", link: { kind: "co", id: co.id }, notes: "", createdAt: today(), completedAt: "", createdBy: ((currentUser() || {}).name) || role() });
  try {
    audit("co", co.id, "bill-back drafted", "", it.name, `${money(selLinePrice(it))} for ${it.name}`);
  } catch (e) {}
  save(), render();
  toast(`${co.number} drafted for ${pm}: ${it.name}, ${money(selLinePrice(it))}. Money not billed back cannot go to raises, bonuses, staff, charity or the client's extras.`, { label: "Open", run: () => flowGo.doc(c, "co", co)() }, 9e3);
  return co;
}
function pdSelRow(it) {
  const p = pdProj(it.projectId),
    C = selOpenChecks(it).sort((a, b) => b.sev - a.sev),
    mineC = C.filter((k) => PD_MINE.includes(k.field)),
    subm = p && (p.submittals || []).find((s) => ["revise", "review", "submitted"].includes(s.status) && (s.items || []).some((x) => "sel" === x.kind && x.id === it.id)),
    dec = it.decId && p && (p.decisions || []).find((d) => d.id === it.decId && "open" === d.status),
    price = selClientPriceStale(it),
    fund = C.find((k) => "funding" === k.field),
    spec = C.find((k) => "spec" === k.field);
  let b = "rest",
    who = "",
    actor = "designer";
  // the sub's resubmittal fixes a wrong product (SKU, finish, size): until it comes back the item waits on the sub; an
  // item whose only gap is ours (the spec sheet, the price, the bill-back) is the designer's even with a submittal open
  const subFix = subm && ("revise" !== subm.status || C.some((k) => ["sku", "finish", "dims"].includes(k.field)));
  if (!["inst"].includes(it.stage)) {
    if (subFix) (b = "others"), (actor = "sub"), (who = "revise" === subm.status ? subm.sub || "the sub" : "the architect");
    else if (mineC.length) b = "mine";
    else if ("sel" === it.stage || dec) (b = "others"), (actor = "client"), (who = puClientWord(p));
  }
  // the reasons, in the order the designer acts: the stale price, what blocks (sev 3), the spec sheet the field needs
  const rest = C.filter((k) => !(price && "price" === k.field)),
    reasons = (price ? [price] : []).concat(rest.filter((k) => 3 === k.sev), rest.filter((k) => "spec" === k.field && 3 !== k.sev), rest.filter((k) => 3 !== k.sev && "spec" !== k.field)).map((k) => (k.msg ? k.msg : k)).slice(0, 4),
    act = fund ? ["Draft the Bill-Back for the PM", () => pdBillBack(it)] : price ? ["Update the Price", () => pdUpdatePrice(it)] : spec ? ["Find the Spec Sheet", () => selOpenItem(it.id)] : ["Open", () => selOpenItem(it.id)];
  if ("mine" === b && !pdIsDesigner()) (b = "others"), (who = "the designer");
  return {
    id: "sel:" + it.id,
    b: b,
    actor: actor,
    who: who,
    it: it,
    name: it.name,
    job: puJob(p),
    line: [it.room, `${+it.qty || 1} ${it.unit || "each"} at ${money(selCost(it))}`, pdLineWord(it)].filter(Boolean).join(" · "),
    why: subm ? `submittal ${subm.number}: ${"revise" === subm.status ? "Revise and Resubmit" : "in review"}. ${reasons.join(". ")}` : reasons.join(". "),
    act: act[0],
    run: act[1],
    tone: C.some((k) => 3 === k.sev) ? "bad" : C.length ? "warn" : "",
  };
}
function pdSelRows() {
  const job = puInJob() || pdJob;
  return ((DB.sel || {}).items || []).filter((it) => (!job || it.projectId === job) && (!pdRoom || it.room === pdRoom)).map(pdSelRow);
}
const pdSelMine = () => ((DB.sel || {}).items || []).map(pdSelRow).filter((x) => "mine" === x.b);
function pdSelections() {
  const R = pdSelRows(),
    mine = R.filter((x) => "mine" === x.b),
    others = R.filter((x) => "others" === x.b),
    rest = R.filter((x) => "rest" === x.b),
    items = (DB.sel || {}).items || [],
    jobs = [...new Set(items.map((i) => i.projectId))].map(pdProj).filter(Boolean),
    rooms = [...new Set(items.filter((i) => !(puInJob() || pdJob) || i.projectId === (puInJob() || pdJob)).map((i) => i.room).filter(Boolean))].sort(),
    inJob = !!puInJob(),
    filters = `<div class="pu-filters">${inJob ? "" : `<select class="pu-sel" id="pd-job" aria-label="Job"><option value="">Job: All</option>${jobs.map((p) => `<option value="${esc(p.id)}" ${pdJob === p.id ? "selected" : ""}>${esc(puJob(p))}</option>`).join("")}</select>`}<span class="pu-fl">Room:</span><button type="button" class="pu-chip ${pdRoom ? "" : "on"}" data-puroom="" aria-pressed="${!pdRoom}">All</button>${rooms.map((r) => `<button type="button" class="pu-chip ${pdRoom === r ? "on" : ""}" data-puroom="${esc(r)}" aria-pressed="${pdRoom === r}">${esc(r)}</button>`).join("")}</div>`,
    body =
      filters +
      puSecHtml("mine", "Needs You", mine, { count: "sel", empty: "Nothing waits on you: every item is verified and on its line." }) +
      puSecHtml("others", "With Someone Else", others, { others: 1 }) +
      (rest.length ? `<section class="pu-sec" data-pusec="restfold"><div class="pu-sh"><h3>Everything Else</h3><span class="pu-note">${rest.length} items, ordered or installed</span></div><button type="button" class="pu-link pu-laterb" data-pdrest="1" aria-expanded="${!!puShowAll.selrest}">${puShowAll.selrest ? "Hide Them" : "Show Them"}${puShowAll.selrest ? PU_IC.up : PU_IC.down}</button>${puShowAll.selrest ? `<div class="pu-rows">${rest.map((x) => puRowHtml(x, { quiet: 1 })).join("")}</div>` : ""}</section>` : "") +
      `<div class="pu-foot"><button type="button" class="pu-link" data-pdclient="1">See This Job as the Client Does</button></div>`;
  return `<div class="pu-page" data-pupage="sel">${pdHead("sel", "Selections", "Every product we specified, on every job: what it is, what it costs, and where it stands.")}${body}</div>`;
}

// ---- Drawings ---------------------------------------------------------------------------------------------------------
function pdStudioRows() {
  try {
    return ovRows("studio");
  } catch (e) {
    return [];
  }
}
function pdDrawRows() {
  const job = puInJob() || "",
    R = [],
    me = pdIsDesigner();
  (DB.field.raises || [])
    .filter((r) => "designer" === r.to && !["closed", "answered", "resolved"].includes(r.status) && (!job || r.projectId === job))
    .forEach((r) =>
      R.push({ b: me ? "mine" : "others", who: "the designer", id: "q:" + r.id, name: `${r.by || "The field"}'s question${r.sheet ? ` on ${r.sheet}` : ""}`, job: puJob(pdProj(r.projectId)), line: r.dueBy ? `Answer by ${fmt(r.dueBy)}` : "", why: r.title, act: "Answer", run: () => fAnswerRaise(r), tone: r.dueBy && r.dueBy <= today() ? "bad" : "warn" }),
    );
  pdStudioRows()
    .filter((r) => !job || r.p.id === job)
    .forEach((r) => {
      if (r.stale > 0) {
        let S0 = [];
        try {
          S0 = sheetsOf(r.p.id).filter((s) => s.stale && "current" === s.status);
        } catch (e) {}
        R.push({ b: me ? "mine" : "others", who: "the designer", id: "re:" + r.p.id, name: `Re-issue ${puJob(r.p)}: ${r.stale} sheets`, job: "", line: S0.map((s) => s.number).join(", "), why: "Changed under a current set: the field is building from the old one.", act: "Issue a Set", run: () => ("function" == typeof jpOpenJob ? jpOpenJob(r.p.id, "plans") : (setCurrent(r.p.id), setView("plans"))), tone: "bad" });
      }
      r.unv > 0 &&
        R.push({ b: me ? "mine" : "others", who: "the designer", id: "sv:" + r.p.id, name: `Survey ${puJob(r.p)}: ${r.unv} rooms`, job: "", line: "on listing dimensions", why: "Design development, the set issue and the orders wait for the survey.", act: "Open the Rooms", run: () => (setCurrent(r.p.id), setView("sboard")), tone: "warn" });
    });
  return R;
}
function pdAgency() {
  const job = puInJob() || "",
    td = today();
  return ((DB.studio && DB.studio.filings) || [])
    .filter((f) => "submitted" === f.status && (!job || f.projectId === job))
    .map((f) => ({ id: "fl:" + f.id, name: f.name, job: puJob(pdProj(f.projectId)), line: f.submittedOn ? `${dayDiff(f.submittedOn, td)} days at the agency` : "at the agency", why: "The job's permit record holds the filing.", run: () => ("function" == typeof jpOpenJob ? jpOpenJob(f.projectId, "files") : (setCurrent(f.projectId), setView("files"))) }));
}
function pdDrawings() {
  const R = pdDrawRows(),
    mine = R.filter((x) => "mine" === x.b),
    others = R.filter((x) => "others" === x.b),
    jobs = (DB.projects || []).filter((p) => "function" == typeof plSheets && plSheets(p.id, { current: 1 }).length),
    job = puInJob() || pdJob || (S && jobs.some((p) => p.id === S.id) ? S.id : jobs[0] && jobs[0].id) || "",
    sheets = job && "function" == typeof plSheets ? plSheets(job, { current: 1 }).sort((a, b) => String(a.number).localeCompare(String(b.number), void 0, { numeric: !0 })) : [],
    sheetRow = (s) => {
      const st = (PL_STATUS[plStatus(s)] || [plStatus(s)])[0];
      return { id: "sh:" + s.id, name: `${s.number} Rev ${s.rev} · ${s.title || ""}`, job: "", line: `${st}${s.issuedOn ? ` · ${fmt(s.issuedOn)}` : ""}${s.stale ? " · Stale" : ""}`, why: s.change || s.what || s.notes || "", run: () => ("function" == typeof jpOpenJob ? jpOpenJob(job, "plans") : setView("plans")) };
    },
    rooms = (() => {
      try {
        return plDB().rooms.filter((r) => r.projectId === job);
      } catch (e) {
        return [];
      }
    })(),
    byRoom = rooms
      .map((r) => ({ r: r, S0: sheets.filter((s) => (s.rooms || []).includes(r.id) || ("function" == typeof plHit && plHit(r, `${s.title} ${s.change || ""}`))) }))
      .filter((x) => x.S0.length),
    filters = `<div class="pu-filters">${puInJob() ? "" : `<select class="pu-sel" id="pd-djob" aria-label="Job">${jobs.map((p) => `<option value="${esc(p.id)}" ${job === p.id ? "selected" : ""}>${esc(puJob(p))}</option>`).join("")}</select>`}<button type="button" class="pu-chip ${"sheet" === pdGroup ? "on" : ""}" data-pugroup="sheet" aria-pressed="${"sheet" === pdGroup}">By Sheet</button><button type="button" class="pu-chip ${"room" === pdGroup ? "on" : ""}" data-pugroup="room" aria-pressed="${"room" === pdGroup}">By Room</button></div>`,
    list =
      "room" === pdGroup
        ? byRoom.length
          ? byRoom.map((x) => puSecHtml("room:" + x.r.id, x.r.name, x.S0.map(sheetRow), { quiet: 1 })).join("")
          : `<p class="pu-empty">No sheet names a room on this job yet.</p>`
        : puSecHtml("sheets", "Current Sheets", sheets.map(sheetRow), { quiet: 1, empty: "No current sheets on this job." }),
    body =
      puSecHtml("mine", "Needs You", mine, { count: "plans", empty: "Nothing waits on you: the field has its answers and every set is current." }) +
      puSecHtml("others", "With Someone Else", others, { others: 1 }) +
      puSecHtml("agency", "At the Agency", pdAgency(), { quiet: 1 }) +
      filters +
      list +
      `<div class="pu-foot"><button type="button" class="pu-link" data-pdreg="1">The Full Register, Set Check and Lessons</button></div>`;
  return `<div class="pu-page" data-pupage="plans">${pdHead("plans", "Drawings", "Every job's current sheets, and what the field and the agencies are waiting on.")}${body}</div>`;
}
let pdPlusOpen = "";
function pdPlusItems(v) {
  const legacy = (re) => () => {
    puFull[v] = !0;
    render();
    const b = [...document.querySelectorAll(`#v-${v} button`)].find((x) => re.test(x.textContent.trim()));
    b ? b.click() : toast("Open the job to do that");
  };
  return {
    sel: [
      ["Clip From a Web Page", "The vendor's page, read once", legacy(/^Clip an Item$/i)],
      ["From a Spec Sheet or Photo", "The assistant reads it", legacy(/^Get Clips$/i)],
    ],
    plans: [
      ["New Revision", "On the job in the filter", legacy(/^New Revision$/i)],
      ["Issue a Set", "To the field and the consultants", legacy(/^Issue a Set$/i)],
    ],
  }[v] || [];
}
function pdHead(v, h, lead) {
  const items = pdPlusItems(v);
  return `<div class="ph pu-ph"><div class="pu-tt"><h2>${esc(h)}</h2><p class="lead" data-nocase>${esc(lead)}</p></div><div class="acts"><div class="pu-plus"><button type="button" class="btn pu-plusb" data-pdplus="${v}" aria-expanded="${pdPlusOpen === v}" aria-label="New">${PU_IC.plus}<span>New</span></button>${pdPlusOpen === v ? `<div class="pu-menu" role="menu">${items.map((it, i) => `<button type="button" role="menuitem" class="pu-mi" data-pdmi="${i}"><b>${esc(it[0])}</b><span>${esc(it[1])}</span></button>`).join("")}</div>` : ""}</div></div></div>`;
}

// ---- In Design: a filter of All Projects ---------------------------------------------------------------------------
// the last five working days with no time entry, per person: the designer's Today reads the same days
function pdMissing(emp) {
  const td = today(),
    days = [];
  for (let i = 1; i <= 7 && days.length < 5; i++) {
    const d = iso(addDays(td, -i));
    [0, 6].includes(parse(d).getDay()) || days.push(d);
  }
  return days.filter((d) => !(DB.time || []).some((t) => t.empId === emp.id && t.date === d));
}
function pdInDesignHtml() {
  const rows = pdStudioRows().filter((r) => r.est > 0 || r.cur),
    me = "function" == typeof tlMyProjects ? (tlMyProjects() || {}).emp : null,
    designers = (DB.employees || []).filter((e) => "function" == typeof isDesignStaff && isDesignStaff(e)),
    miss = designers.map((e) => ({ e: e, m: pdMissing(e) })).filter((x) => x.m.length),
    mine = me ? pdMissing(me).length : null,
    phase = (r) => (r.cur && r.cur.line ? String(r.cur.line.item || "").split(" and ")[0] : "—"),
    cards = rows
      .map((r) => {
        let current = 0;
        try {
          current = sheetsOf(r.p.id).filter((s) => "current" === s.status).length;
        } catch (e) {}
        return `<button type="button" class="pd-card" data-pdproj="${esc(r.p.id)}"><b data-nocase>${esc(puJob(r.p))}</b><span class="pu-sub" data-nocase>${esc((r.c && r.c.name) || "")} · ${esc(phase(r))}</span><span class="pd-kv"><span>Hours</span><b class="${r.used > r.est ? "bad" : ""}">${r2(r.used)} of ${r2(r.est)}${r.used > r.est ? ", over the proposal" : ""}</b></span><span class="pd-kv"><span>Survey</span><b>${r.unv ? `${r.unv} rooms on listing dimensions` : "Measured"}</b></span><span class="pd-kv"><span>Drawings</span><b>${r.stale ? `${r.stale} to re-issue` : `${current} current`}</b></span><span class="pd-kv"><span>Filings</span><b data-nocase>${esc(r.inRev.join(", ") || (r.F.length ? `${r.F.length} on file` : "none"))}</b></span></button>`;
      })
      .join(""),
    foot = `<div class="pu-sec pd-hours"><div class="pu-sh"><h3>Hours Not Logged${null != mine ? ` ${mine}` : ""}</h3><span class="pu-note">working days in the last five with no time entry</span></div>${miss.map((x) => `<div class="pu-row"><span class="pu-rb"><b data-nocase>${esc(x.e.name)}</b><span class="pu-sub">${x.m.length} day${1 === x.m.length ? "" : "s"}: ${x.m.map(fmt).join(", ")}</span></span><button type="button" class="btn sm" data-stnudge="${esc(x.e.id)}">Ask for Them</button></div>`).join("") || '<p class="pu-empty">Everyone is current.</p>'}</div>`;
  return `<div class="pd-indesign" data-pupage="indesign"><div class="pd-cards">${cards || '<p class="pu-empty">No job is in design.</p>'}</div>${foot}</div>`;
}
function pdOvJobs() {
  const host = document.getElementById("ovjobs-body");
  if (!host) return;
  host.querySelectorAll(":scope > .pd-ovf, :scope > .pd-indesign").forEach((x) => x.remove());
  if ("ovjobs" !== view) return;
  const ph = host.querySelector(":scope > .ph"),
    bar = `<div class="pd-ovf pu-filters"><span class="pu-fl">Show:</span><button type="button" class="pu-chip ${pdInDesign ? "" : "on"}" data-pdindesign="0" aria-pressed="${!pdInDesign}">All Projects</button><button type="button" class="pu-chip ${pdInDesign ? "on" : ""}" data-pdindesign="1" aria-pressed="${pdInDesign}">In Design</button></div>`;
  ph ? ph.insertAdjacentHTML("afterend", bar) : host.insertAdjacentHTML("afterbegin", bar);
  const ovf = host.querySelector(":scope > .pd-ovf");
  pdInDesign && ovf.insertAdjacentHTML("afterend", pdInDesignHtml());
  [...host.children].forEach((c) => {
    if (c === ph || c.classList.contains("pd-ovf") || c.classList.contains("pd-indesign")) return;
    pdInDesign ? (null == c.dataset.pdhid && (c.dataset.pdhid = c.style.display || ""), c.style.setProperty("display", "none", "important")) : null != c.dataset.pdhid && (c.style.removeProperty("display"), c.dataset.pdhid && (c.style.display = c.dataset.pdhid), delete c.dataset.pdhid);
  });
  // the email card the overview moves after the list
  const mail = host.nextElementSibling;
  mail && mail.classList && mail.classList.contains("oc-mail") && (pdInDesign ? mail.style.setProperty("display", "none", "important") : mail.style.removeProperty("display"));
}

// ---- drawing and wiring -----------------------------------------------------------------------------------------------
const PD_PAGES = { sel: pdSelections, plans: pdDrawings };
function pdDraw() {
  Object.keys(PD_PAGES).forEach((x) => x !== view && puDrop(x));
  const v = view;
  if (!PD_PAGES[v]) return;
  // inside a job the register is the job's (its Documents tab); the field keeps its own sheets
  if (!puOffice() || ("plans" === v && puInJob())) return void puDrop(v);
  const host = puHost(v);
  if (!host) return;
  try {
    host.innerHTML = PD_PAGES[v]();
  } catch (e) {
    console.warn("design page", v, e), puDrop(v);
  }
}
document.addEventListener(
  "click",
  (e) => {
    const t = e.target && e.target.closest ? e.target : null;
    if (!t) return;
    const at = (s) => t.closest(s);
    let b;
    if ((b = at("[data-pdplus]"))) return e.preventDefault(), e.stopPropagation(), (pdPlusOpen = pdPlusOpen === b.dataset.pdplus ? "" : b.dataset.pdplus), render();
    if ((b = at("[data-pdmi]"))) {
      e.preventDefault(), e.stopPropagation();
      const it = pdPlusItems(pdPlusOpen)[+b.dataset.pdmi];
      return (pdPlusOpen = ""), void (it && it[2]());
    }
    pdPlusOpen && !at(".pu-menu") && ((pdPlusOpen = ""), setTimeout(render, 0));
    if ((b = at("[data-pdindesign]"))) return e.preventDefault(), (pdInDesign = "1" === b.dataset.pdindesign), void render();
    if ((b = at("[data-pdproj]"))) return e.preventDefault(), void ("function" == typeof jpOpenJob ? jpOpenJob(b.dataset.pdproj) : (setCurrent(b.dataset.pdproj), setView("dash")));
    if (!at(".pu-page")) return;
    if ((b = at("[data-puroom]"))) return e.preventDefault(), (pdRoom = b.dataset.puroom), void render();
    if ((b = at("[data-pugroup]"))) return e.preventDefault(), (pdGroup = b.dataset.pugroup), void render();
    if ((b = at("[data-pdrest]"))) return e.preventDefault(), (puShowAll.selrest = !puShowAll.selrest), void render();
    if ((b = at("[data-pdreg]"))) return e.preventDefault(), (puFull.plans = !puFull.plans), void render();
    if ((b = at("[data-pdclient]"))) {
      e.preventDefault();
      const c = [...document.querySelectorAll("#sel-body button")].find((x) => /^Client View$/i.test(x.textContent.trim()));
      return void (c ? c.click() : toast("Open a job to see it as its client does"));
    }
  },
  !0,
);
document.addEventListener("change", (e) => {
  const t = e.target;
  if (!t || !t.id) return;
  if ("pd-job" === t.id) return (pdJob = t.value), (pdRoom = ""), void render();
  if ("pd-djob" === t.id) return (pdJob = t.value), void render();
});
(function pdRegister() {
  "object" == typeof OC_BADGE && ((OC_BADGE.sel = { n: () => (pdIsDesigner() ? pdSelMine().length : 0) }), (OC_BADGE.plans = { n: () => (pdIsDesigner() ? pdDrawRows().filter((x) => "mine" === x.b).length : 0) }));
  // the old Design pages' homes: the overview is All Projects' In Design filter; Project Board and Filings light Drawings
  "object" == typeof MN_ALIAS && Object.assign(MN_ALIAS, { ovstudio: "ovjobs", sboard: "plans", sfile: "plans", sdraw: "plans" });
  "object" == typeof OC_RETIRED && OC_RETIRED.ovstudio && delete OC_RETIRED.ovstudio;
  const L = { sel: "Selections", plans: "Drawings" };
  [void 0 !== NAV_LABELS ? NAV_LABELS : null, void 0 !== IA_LABELS ? IA_LABELS : null].forEach((x) => x && Object.assign(x, L));
})();
{
  const base = render;
  render = function () {
    if ("ovstudio" === view) (view = "ovjobs"), (pdInDesign = !0);
    if ("sdraw" === view) view = "plans";
    const r = base.apply(this, arguments);
    try {
      pdDraw(), pdOvJobs();
    } catch (e) {
      console.warn("design", e);
    }
    return r;
  };
}
(() => {
  const css = `
.pd-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin:0 0 14px}
.pd-card{display:flex;flex-direction:column;align-items:stretch;gap:6px;text-align:left;background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:14px 16px;font:inherit;color:var(--ink);cursor:pointer;min-height:44px}
.pd-card>b{font-size:15px}
.pd-kv{display:flex;justify-content:space-between;gap:10px;font-size:13px;border-top:1px solid var(--rule-2);padding-top:5px}
.pd-kv>span{color:var(--ink-3)} .pd-kv b{font-weight:600;text-align:right} .pd-kv b.bad{color:var(--bad)}
@media (max-width:760px){ .pd-cards{grid-template-columns:1fr} }
`;
  const st = document.createElement("style");
  (st.id = "design-css"), (st.textContent = css), document.head.appendChild(st);
})();
