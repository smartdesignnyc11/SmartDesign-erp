/*<<tasks.js>>*/
/* ==== tasks: one task list and one task sheet, phone first (consolidation lane 1, 2026-10-21) =======================
   Alan, 2026-10-21: "The task module is one of the most important and it isn't great on mobile." docs/CONSOLIDATION.md
   §2.3 (the task module on the phone) and the task rows of §2.1; the evidence is docs/IA_MAP.md §4 and the four role
   experts (owner, PM, coordinator, foreman: tasks graded 4, 4, 4 and 6).
   Design gate (BACKLOG §1.16). The noun is the task. Its stores stay as they are (p.tasks the schedule, p.actions a job's
   to-dos, DB.tasks the office's, DB.hub.tasks sales, DB.obligations, the assistant's notes) behind the one accessor
   (tkItems() / tkAll()). The list is Tasks (view tkall); the queue is Today (home). Nothing new is added:
     - Projects › Tasks (view tasks) is the same list with the job chip set; Sales Tasks (hbtasks) and the owner's and
       PM's My Day (sday) forward to it with their chip set; the crew's separate Tasks page leaves the crew's menu,
       because Clock is their list. Old links land: the view ids forward instead of 404ing.
     - One sheet opens a task wherever it is tapped (tkSheet): Today, Tasks, the job, Sales, the foreman's Today's Work,
       the designer's Today and the toasts' Open. Edit is its secondary button; a schedule line opens the card first.
     - A hand-off is the record's own rec.handoff and rec.handoffs (tdyHandOff, tdyAccept, tdyDecline from Today's
       lane): the sender owns it until the receiver accepts.
     - Two fields ride on the existing task record: rec.thread (notes, photos and earlier notes, append-only, so a
       note is never overwritten) and rec.checklist ([{t, done, by, at}]).
   "Mine" is openTasks("me"), which calls tkOwnerMatch (owned by the fix lane), so the list, its counts and Ask read
   one set: one number for Due Soon (overdue and the next 7 days), Today and Overdue.
--------------------------------------------------------------------------------------------------------------------- */
// ---- the views: Due Soon first, and one number for each ------------------------------------------------------------
const TK_VIEWS = [
  ["week", "Due Soon"],
  ["today", "Today"],
  ["overdue", "Overdue"],
  ["nodate", "No Date"],
  ["blocked", "Waiting"],
  ["later", "Later"],
  ["done", "Done"],
  ["all", "All"],
];
const TK_VIEW_SAY = { week: "overdue and the next 7 days", today: "overdue and due today", overdue: "past their date", nodate: "no date on them", blocked: "waiting on someone outside the team", later: "put off for later", done: "finished", all: "every open task" };
t2View = "week";
const tkViewName = (v) => (TK_VIEWS.find(([k]) => k === v) || TK_VIEWS[0])[1];
const tkIsManager = () => {
  try {
    return TDY_MANAGERS.includes(role());
  } catch (e) {
    return !1;
  }
};
// A person goes by first name; a system author keeps its whole name (taskfix #15: "The Standard" printed as "The"). A
// name is shortened only when each word starts with a capital and the first is not an article, so "Chief of Staff",
// "LPC staff" and "Purchase history" stay whole and "Chen Biron" reads "Chen".
const tkFirst = (n) => {
  const s = String(n || "").trim();
  if (!s) return "";
  const w = s.split(/[\s\/]+/).filter(Boolean);
  if (/^(the|a|an)$/i.test(w[0]) || w.some((x) => !/^[A-Z0-9]/.test(x))) return s.split("/")[0].trim();
  return w[0];
};
const tkPhone = () => ("function" == typeof isMobile ? isMobile() : !1);
const TK_IC = {
  search: '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
  chev: '<path d="M6 9l6 6 6-6"/>',
  plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  camera: '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  hand: '<path d="M5 12h12"/><path d="M13 7l5 5-5 5"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
};
const tkSvg = (k, s) => `<svg viewBox="0 0 24 24" width="${s || 18}" height="${s || 18}" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${TK_IC[k] || ""}</svg>`;

// The person's own counts, read the same way the list reads them (openTasks("me") less what is put off). Ask, the
// list's chips and Today's "Tasks due soon" line all call this: one number each.
function tkCountsOf(R) {
  const out = {};
  TK_VIEWS.forEach(([k]) => {
    if ("done" === k) return;
    try {
      out[k] = t2ViewOf(R, k).length;
    } catch (e) {
      out[k] = 0;
    }
  });
  return out;
}
function tkMyCounts() {
  let R = [];
  try {
    R = openTasks("me");
  } catch (e) {}
  return tkCountsOf(R);
}
// THE "Tasks" number (taskfix #1, 2026-10-25): the person's own Due Soon, late or due in the next 7 days and not put
// off, the Tasks list's first view. The side menu, Today's sub-tab and its Tasks chip (those rows), the phone bar and
// the Tasks page all read this one function; counts_lint fails when any of them reads another number.
function tkTasksN() {
  return tkMyCounts().week || 0;
}
// Due soon for one person by name (Today's line, Ask): the same views over openTasks(name).
function tkSoonFor(name) {
  try {
    const me = tkMe();
    const R = !name || name === me ? openTasks("me") : openTasks(name);
    return t2ViewOf(R, "week");
  } catch (e) {
    return [];
  }
}
// What is offered to me and waits on my yes or no: it is not mine until I accept, so it is not in Mine's counts; the
// list shows it as one line above the rows and Today shows it with Accept.
function tkOfferedToMe() {
  try {
    const me = tdyMe();
    return me.id ? tkAll({ open: !0 }).filter((t) => t.offeredToUid === me.id) : [];
  } catch (e) {
    return [];
  }
}

// ---- the pool: Team is everyone's but mine (managers) ---------------------------------------------------------------
{
  const base = t2Pool;
  t2Pool = function () {
    if ("team" === tkWho) {
      const me = tkMe();
      return t2Narrow(openTasks("all").filter((x) => !tkOwnerMatch(x.assignee, me)));
    }
    return base.apply(this, arguments);
  };
}
{
  const base = t2DonePool;
  t2DonePool = function () {
    if ("team" !== tkWho) return base.apply(this, arguments);
    const keep = tkWho;
    try {
      tkWho = "all";
      const me = tkMe();
      return base.apply(this, arguments).filter((x) => !tkOwnerMatch(x.assignee, me));
    } finally {
      tkWho = keep;
    }
  };
}
// a fresh job list opens on Due Soon too (it opened on All, 25 rows with the first at y 433)
{
  const base = t2Enter;
  t2Enter = function () {
    const c = t2Ctx(),
      fresh = "home" !== c && c !== t2Last && !t2State[c];
    const r = base.apply(this, arguments);
    fresh && (t2View = "week");
    TK_VIEWS.some(([k]) => k === t2View) || (t2View = "week");
    return r;
  };
}

// An obligation's task says what is late (taskfix #11): its due date is the filing (or renewal) date, the expiry less
// the lead, so the row reads "filing 5d late" or "file by Tue", never a bare "5d late" beside "expires 9/28".
function tkObOf(x) {
  if (!x) return null;
  try {
    const O = DB.obligations || [];
    return (x.obId && O.find((o) => o.id === x.obId)) || ("ob" === x.kind && O.find((o) => o.id === x.id)) || O.find((o) => o.taskId && o.taskId === x.id) || null;
  } catch (e) {
    return null;
  }
}
{
  const base = t2When;
  t2When = function (x) {
    const w = base.apply(this, arguments);
    try {
      const o = !x.done && x.due ? tkObOf(x) : null;
      // only where the date is the filing date; a row that carries the expiry itself keeps its own words
      if (!o || ("function" == typeof flObFile && x.due !== flObFile(o))) return w;
      const filing = "filing" === o.kind,
        L = String(w.label || "");
      return Object.assign({}, w, {
        label: "late" === w.cls ? `${filing ? "filing" : "renewal"} ${L}` : "today" === w.cls ? `${filing ? "file" : "renew"} today` : `${filing ? "file" : "renew"} by ${L}`,
      });
    } catch (e) {
      return w;
    }
  };
}
// a title that ends with its own job ("Friday client update — 121 State Street") drops it: the line under it says the job
function tkTitleShort(x) {
  const t = String(x.title || ""),
    p = x.projectId ? (DB.projects || []).find((q) => q.id === x.projectId) : null,
    names = [x.project, p && shortName(p), p && p.project && p.project.name].filter(Boolean);
  for (const n of names) {
    const cut = t.lastIndexOf(" — " + n);
    if (cut > 8 && cut + 3 + n.length === t.length) return t.slice(0, cut);
  }
  return t;
}
// ---- one row: 64 to 72px, a 44px circle, a 16px title on two lines, due and job on one line, the owner's first name -
function tkRowHtml(x, o) {
  const O = o || {},
    key = t2Key(x),
    w = t2When(x),
    def = t2DeferOf(x),
    rec = (() => {
      try {
        return tdyRec(x);
      } catch (e) {
        return null;
      }
    })(),
    H = rec && rec.handoff && "offered" === rec.handoff.state ? rec.handoff : null,
    sales = "hub" === x.kind || "lead" === x.kind,
    job = sales ? "Sales" : x.project || "Firm-wide",
    who = tkFirst(x.assignee || x.owner),
    showWho = "me" !== tkWho && !O.hideWho && who,
    fyi = "fyi" === x.status,
    bits = [fyi ? '<span class="tk2-when tk2-w-fyi">FYI</span>' : `<span class="tk2-when tk2-w-${w.cls}">${esc(w.label)}</span>`];
  O.hideJob || bits.push(`<span class="tk2-job">${esc(job)}</span>`);
  def && bits.push(`<span class="tk2-later">Later · ${esc(fmt(def))}</span>`);
  x.waitsOn && bits.push(`<span class="tk2-wait">${esc(x.waitingOn && "function" == typeof tkWaitSay ? tkWaitSay(x.waitingOn, !0) : "Waiting on " + x.waitsOn)}</span>`);
  !x.done && x.followUp && x.followUp !== x.due && bits.push(`<span class="tk2-fu">Follow up ${esc(fmt(x.followUp))}</span>`);
  H && bits.push(`<span class="tk2-off">Offered to ${esc(tkFirst(H.to))}</span>`);
  return `<div class="t2-row tk2-row ${x.late ? "late" : ""} ${x.done ? "done" : ""}" data-t2key="${esc(key)}" data-tkkey="${esc(key)}" data-edit="tk:${esc(x.kind)}|${esc(x.projectId || "")}|${esc(x.id)}" tabindex="0">
  <div class="tk2-slide">${
    x.done
      ? '<span class="tk2-check tk2-donemark" aria-hidden="true"><span></span></span>'
      : `<button type="button" class="t2-check tk2-check" data-t2done="${esc(key)}" aria-label="Mark done" title="Mark done"><span></span></button>`
  }<div class="tk2-mid"><div class="tk2-title">${x.code ? `<span class="tk2-key">${esc(x.code)}</span>` : ""}${"high" === x.priority ? '<i class="tk2-hi" title="High priority"></i>' : ""}${esc(O.hideJob ? x.title : tkTitleShort(x))}</div><div class="tk2-sub">${bits.join('<span class="tk2-dot"> · </span>')}</div></div>${showWho ? `<span class="tk2-who" title="${esc(x.assignee || x.owner || "")}">${esc(who)}</span>` : ""}</div>${
    x.done ? "" : `<div class="tk2-acts"><button type="button" class="tk2-act" data-t2later="${esc(key)}" tabindex="-1">Later</button><button type="button" class="tk2-act hand" data-tkhand="${esc(key)}" tabindex="-1">Hand Off</button></div>`
  }</div>`;
}
// the day a row falls under in Due Soon: Overdue, Today, Tomorrow, then each day by name
function tkDayOf(x) {
  const td = today();
  if (!x.due) return ["~nodate", "No Date"];
  if (x.due < td) return ["0", "Overdue"];
  if (x.due === td) return ["1" + x.due, "Today"];
  const n = dayDiff(td, x.due);
  if (1 === n) return ["1" + x.due, "Tomorrow"];
  if (n <= 7) return ["1" + x.due, fmtL(x.due)];
  return ["2", "Later On"];
}
function tkGroupOf(x, gb) {
  if ("day" === gb) return tkDayOf(x);
  if ("project" === gb) {
    const g = "hub" === x.kind || "lead" === x.kind ? "Sales" : x.project || "Firm-wide";
    return [g, g];
  }
  // By Status (the phone's chip, Alan 2026-10-24): To Do, Doing, Waiting On, FYI, Done, in that order
  if ("status" === gb) {
    const st = x.done ? ["4", "Done"] : "fyi" === x.status ? ["3", "FYI"] : x.waitsOn ? ["2", "Waiting On"] : "doing" === x.status || "in-progress" === x.status ? ["1", "Doing"] : ["0", "To Do"];
    return st;
  }
  if ("assignee" === gb) {
    const g = x.assignee || "Unassigned";
    return [g, g];
  }
  if ("area" === gb) {
    const g = TK_AREA_LABEL[x.area] || x.area || "Other";
    return [g, g];
  }
  return ["", ""];
}
// the list's grouping: by day unless a person chose otherwise (Team groups by person, a manager's who-owes-what)
function tkGroupBy() {
  if (null === t2Group || void 0 === t2Group) return "team" === tkWho ? "assignee" : "day";
  return t2Group;
}
function tkChipLabel(ctx) {
  if ("job" === ctx) return shortName(S) || "This Job";
  if ("__sales" === tkProject) return "Sales";
  if (tkProject) {
    const p = (DB.projects || []).find((q) => q.id === tkProject);
    return p ? shortName(p) : "A Job";
  }
  return { me: "Mine", team: "Team", all: "Everyone", none: "Unassigned" }[tkWho] || tkFirst(tkWho) || "Mine";
}
// counts on the view chips only where they are the person's own: Mine with no other filter. Anywhere else the chip
// carries no number, so "Due Soon", "Today" and "Overdue" each read one number on every screen.
// a field filter (taskviews.js, tvFF) narrows the list too, so its chips then count the rows shown
const tkOwnCounts = (ctx) => "home" === ctx && "me" === tkWho && !tkProject && !tkArea && !tkPri && !t2Q && !tkQueue && !("function" == typeof tvFFOn && tvFFOn());

t2Html = function () {
  const ctx = t2Fix();
  TK_VIEWS.some(([k]) => k === t2View) || (t2View = "week");
  const phone = tkPhone(),
    R = t2Pool(),
    C = tkCountsOf(R),
    own = tkOwnCounts(ctx),
    gb = tkGroupBy(),
    list = "done" === t2View ? t2DonePool() : t2Sort(t2ViewOf(R, t2View)),
    groups = [];
  list.forEach((x) => {
    const [k, n] = gb ? tkGroupOf(x, gb) : ["", ""];
    let b = groups.find((y) => y.k === k);
    b || ((b = { k: k, n: n, rows: [] }), groups.push(b)), b.rows.push(x);
  });
  ("day" === gb || "status" === gb) && groups.sort((a, b) => String(a.k).localeCompare(String(b.k)));
  const rowO = { hideJob: "job" === ctx || ("project" === gb && "day" !== gb) },
    // a day carries no number (the chip has it); on a job's list the Overdue day is the source of the job's Tasks badge
    odJob = (b) => "day" === gb && "job" === ctx && "Overdue" === b.n,
    countN = (b) => ("day" !== gb || odJob(b) ? `<span class="n">${b.rows.length}</span>` : ""),
    markOd = (b) => (odJob(b) ? ' data-ocbadge="tasks"' : ""),
    rowsHtml = groups
      .map((b) =>
        gb
          ? `<div class="t2-group tk2-group"><div class="t2-ghd tk2-ghd${"Overdue" === b.n ? " late" : ""}"${markOd(b)}>${esc(b.n)}${countN(b)}</div>${b.rows.map((x) => tkRowHtml(x, rowO)).join("")}</div>`
          : b.rows.map((x) => tkRowHtml(x, rowO)).join(""),
      )
      .join("");
  // never empty while work is coming: an empty Due Soon shows what comes next
  let empty = "";
  if (!list.length) {
    const next = "week" === t2View ? t2Sort(t2ViewOf(R, "all").filter((x) => x.due && !t2DeferOf(x))).slice(0, 5) : [];
    empty = next.length
      ? `<div class="empty tk2-empty">Nothing due in the next 7 days. Coming up next:</div><div class="t2-group tk2-group"><div class="t2-ghd tk2-ghd">Coming Up</div>${next.map((x) => tkRowHtml(x, rowO)).join("")}</div><button type="button" class="btn tk2-showall" data-t2view="all">Show All Open Tasks</button>`
      : `<div class="empty tk2-empty">${
          {
            week: "Nothing due in the next 7 days, and nothing late.",
            today: "Nothing due today and nothing late.",
            overdue: "Nothing is overdue.",
            nodate: "Every open task has a date on it.",
            blocked: "Nothing is waiting on anybody outside the team.",
            later: "Nothing has been put off.",
            done: "Nothing done yet in this list.",
            all: "No task matches these filters.",
          }[t2View]
        }</div>`;
  }
  const offered = "home" === ctx ? tkOfferedToMe() : [],
    offerHtml = offered.length
      ? `<button type="button" class="tk2-offer" data-tkoffer><span class="tk2-offer-n">${offered.length}</span><span class="grow">${offered.length === 1 ? `${esc(tkFirst(offered[0].owner) || "Someone")} offered you “${esc(tdWords(offered[0].title, 7))}”` : `${offered.length} tasks offered to you`}</span><b>Review</b></button>`
      : "",
    nodate = ["today", "week", "overdue"].includes(t2View) && C.nodate ? `<p class="small muted t2-nodate no-print" data-t2nodate="${C.nodate}">${C.nodate} task${1 === C.nodate ? " has" : "s have"} no date, so ${1 === C.nodate ? "it is" : "they are"} not in ${esc(tkViewName(t2View))}. <button type="button" class="btn sm" data-t2view="nodate">Show No Date</button></p>` : "",
    chip = `${esc(tkChipLabel(ctx))} · ${esc(tkViewName(t2View))}${own && "done" !== t2View && "all" !== t2View ? ` <span class="n">${C[t2View] || 0}</span>` : ""}`,
    quick = "job" === ctx && "done" !== t2View ? '<div class="t2-quick no-print"><input id="t2-quickadd" class="t2-quickin" aria-label="Quick add a task" placeholder="Add a task on this job — Call Nemo about tile ETA @Chen !high due fri"></div>' : "",
    salesActs =
      "__sales" === tkProject || "sales" === ctx
        ? `<button class="btn" id="t2-queues">Manage Queues</button><button class="btn" id="t2-start">Start the Sales Tasks</button>`
        : "",
    jobActs = "job" === ctx && ["owner", "pm", "coord", "design_mgr"].includes(role()) ? '<button class="btn" id="t2-meeting">Process a Meeting</button>' : "";
  if (phone) {
    const searching = !!t2Q || !!window.__tkSearch;
    return `<div class="ph tk2-ph"><div><h2>Tasks</h2></div></div>
  <div class="tk2-hline no-print">${
    searching
      ? `<input id="t2-q" class="tk2-q" aria-label="Search tasks" placeholder="Search tasks" value="${esc(t2Q)}"><button type="button" class="tk2-ic" data-tksearchx aria-label="Close search" title="Close search">${tkSvg("x")}</button>`
      : `<button type="button" class="tk2-chip" data-tkfilter aria-haspopup="dialog">${chip}${tkSvg("chev", 16)}</button><span class="grow"></span><button type="button" class="tk2-ic" data-tksearch aria-label="Search tasks" title="Search tasks">${tkSvg("search")}</button>`
  }</div>
  ${offerHtml}${nodate}
  ${window.__t2Undo ? '<div class="t2-undo no-print"><span class="grow">Moved. Not what you meant?</span><button class="btn sm" id="t2-undo">Put It Back</button></div>' : ""}
  <div class="t2-list tk2-list">${rowsHtml || empty}${quick}</div>
  <button type="button" class="tk2-fab no-print" id="tk-new" aria-label="New Task" title="New Task">${tkSvg("plus", 26)}</button>`;
  }
  // the wide screen: the same list and chips, laid out in one bar
  const projects = (DB.projects || []).map((p) => [p.id, shortName(p)]),
    people = (() => {
      try {
        return crPeopleOf(tkItems().filter((x) => !x.done));
      } catch (e) {
        return [];
      }
    })(),
    named = tkWho && !["me", "all", "none", "team"].includes(tkWho),
    scope = [["me", "Mine"]].concat(tkIsManager() ? [["team", "Team"]] : [], [["all", "Everyone"], ["none", "Unassigned"]]),
    views = TK_VIEWS.map(([k, n]) => `<button class="${t2View === k ? "on" : ""}" data-t2view="${k}">${n}${own && "done" !== k && "all" !== k && C[k] ? `<span class="n">${C[k]}</span>` : ""}</button>`).join("");
  return `<div class="ph tk2-ph"><div><h2>Tasks</h2><div class="lead"></div></div><div class="acts">${jobActs}${salesActs}<button class="btn primary" id="tk-new">New Task</button></div></div>
  <div class="tk2-bar no-print"><div class="seg sm t2-scope">${scope.map(([k, n]) => `<button class="${tkWho === k || ("all" === k && named) ? "on" : ""}" data-tkwho="${k}">${n}</button>`).join("")}</div>${
    "home" === ctx
      ? `<select id="t2-proj" class="btn" aria-label="Filter by job" title="Filter by job"><option value="">All Jobs</option><option value="__sales" ${"__sales" === tkProject ? "selected" : ""}>Sales</option>${projects.map(([id, n]) => `<option value="${esc(id)}" ${tkProject === id ? "selected" : ""}>${esc(n)}</option>`).join("")}</select>`
      : ""
  }${"all" === tkWho || named ? `<select id="t2-person" class="btn" aria-label="Filter by person" title="Filter by person"><option value="">Anyone</option>${people.map((n) => `<option ${tkWho === n ? "selected" : ""}>${esc(n)}</option>`).join("")}</select>` : ""}<input id="t2-q" class="btn t2-q" aria-label="Search tasks" placeholder="Search tasks" value="${esc(t2Q)}"><span class="grow"></span><select id="t2-area" class="btn" aria-label="Filter by area" title="Filter by area"><option value="">All Areas</option>${TK_AREAS.map(([k, n]) => `<option value="${k}" ${tkArea === k ? "selected" : ""}>${esc(n)}</option>`).join("")}</select><select id="t2-pri" class="btn" aria-label="Filter by priority" title="Filter by priority"><option value="">Any Priority</option><option value="high" ${"high" === tkPri ? "selected" : ""}>High Only</option></select><select id="t2-group" class="btn" aria-label="How the list is grouped" title="How the list is grouped"><option value="day" ${"day" === gb ? "selected" : ""}>By Day</option><option value="project" ${"project" === gb ? "selected" : ""}>By Project</option><option value="assignee" ${"assignee" === gb ? "selected" : ""}>By Person</option><option value="area" ${"area" === gb ? "selected" : ""}>By Area</option><option value="" ${"" === gb ? "selected" : ""}>No Grouping</option></select><div class="seg sm tk-mode no-print"><button class="${"table" !== tkMode && "board" !== tkMode ? "on" : ""}" data-tkmode="cards">List</button><button class="${"board" === tkMode ? "on" : ""}" data-tkmode="board">Board</button><button class="${"table" === tkMode ? "on" : ""}" data-tkmode="table">Table</button></div></div>
  <div class="ctabs t2-views tk2-views no-print">${views}</div>
  ${offerHtml}${nodate}
  ${window.__t2Undo ? '<div class="t2-undo no-print"><span class="grow">Moved. Not what you meant?</span><button class="btn sm" id="t2-undo">Put It Back</button></div>' : ""}
  <div class="t2-list tk2-list">${rowsHtml || empty}${quick}</div>`;
};
// New Task from the list starts where the list is: the job, Sales, or the person's own list
tkNewDialog = function () {
  const c = t2Ctx();
  newTaskDialog(
    "job" === c && S ? { projectId: S.id } : "sales" === c || "__sales" === tkProject ? { sales: !0 } : tkProject && "home" === c ? { projectId: tkProject } : {},
  );
};

{
  const base = t2Lead;
  t2Lead = function (ctx, R, C) {
    if ("team" === tkWho && "home" === ctx) return `${R.length} open on the team${C.overdue ? ` · ${C.overdue} overdue` : ""} · ${openTasks("me").length} yours`;
    return base.apply(this, arguments);
  };
}
// ---- the filter sheet (the phone's one chip): scope, job, view, grouping, and the rest -------------------------------
function tkFilterSheet() {
  const ctx = t2Ctx(),
    C = tkCountsOf(t2Pool()),
    own = tkOwnCounts(ctx),
    scope = [["me", "Mine"]].concat(tkIsManager() ? [["team", "Team"]] : [], [["all", "Everyone"], ["none", "Unassigned"]]),
    jobs = [["", "All Jobs"], ["__sales", "Sales"]].concat((DB.projects || []).map((p) => [p.id, shortName(p)])),
    gb = tkGroupBy(),
    btn = (attr, v, on, label, n) => `<button type="button" class="tkf-b ${on ? "on" : ""}" ${attr}="${esc(v)}">${esc(label)}${null != n && n !== "" ? `<span class="n">${n}</span>` : ""}</button>`;
  const body = `<div class="tkf">
  ${"home" === ctx ? `<div class="tkf-h">Whose</div><div class="tkf-row">${scope.map(([k, n]) => btn("data-tkfwho", k, tkWho === k, n)).join("")}</div>
  <div class="tkf-h">Job</div><div class="tkf-row">${jobs.map(([k, n]) => btn("data-tkfjob", k, tkProject === k, n)).join("")}</div>` : `<p class="small muted">${esc(tkChipLabel(ctx))}: every open task on it, whoever owns it.</p>`}
  <div class="tkf-h">Show</div><div class="tkf-row">${TK_VIEWS.map(([k, n]) => btn("data-tkfview", k, t2View === k, n, own && "done" !== k && "all" !== k ? C[k] || 0 : "")).join("")}</div>
  <div class="tkf-h">Group</div><div class="tkf-row">${[["day", "By Day"], ["project", "By Project"], ["assignee", "By Person"], ["area", "By Area"], ["", "None"]].map(([k, n]) => btn("data-tkfgroup", k, gb === k, n)).join("")}</div>
  <div class="tkf-h">Priority</div><div class="tkf-row">${btn("data-tkfpri", "", !tkPri, "Any")}${btn("data-tkfpri", "high", "high" === tkPri, "High Only")}</div>
  ${"job" === ctx && ["owner", "pm", "coord", "design_mgr"].includes(role()) ? `<div class="tkf-h">This Job</div><div class="tkf-row"><button type="button" class="tkf-b" data-tkfmeeting>Process a Meeting</button></div>` : ""}
  ${"__sales" === tkProject ? `<div class="tkf-h">Sales</div><div class="tkf-row"><button type="button" class="tkf-b" data-tkfstart>Start the Sales Tasks</button></div>` : ""}
</div>`;
  const m = mbModal("Show Tasks", body, { submit: "Done" });
  m && m.classList.add("tks-on");
  // one tap picks and shows the list: the sheet closes on a choice
  const set = (fn) => (e) => {
    e.preventDefault();
    fn(e.currentTarget);
    mbCloseModal();
    try {
      renderTkAll();
    } catch (err) {}
    window.scrollTo(0, 0);
  };
  m.querySelectorAll("[data-tkfwho]").forEach((b) => (b.onclick = set((el) => ((tkWho = el.dataset.tkfwho), (t2Group = null)))));
  m.querySelectorAll("[data-tkfjob]").forEach((b) => (b.onclick = set((el) => ((tkProject = el.dataset.tkfjob), "__sales" === tkProject && "me" === tkWho && (tkWho = "all")))));
  m.querySelectorAll("[data-tkfview]").forEach((b) => (b.onclick = set((el) => (t2View = el.dataset.tkfview))));
  m.querySelectorAll("[data-tkfgroup]").forEach((b) => (b.onclick = set((el) => (t2Group = el.dataset.tkfgroup))));
  m.querySelectorAll("[data-tkfpri]").forEach((b) => (b.onclick = set((el) => (tkPri = el.dataset.tkfpri))));
  const mt = m.querySelector("[data-tkfmeeting]");
  mt && (mt.onclick = () => (mbCloseModal(), (document.getElementById("btn-meeting") || { click() {} }).click()));
  const st = m.querySelector("[data-tkfstart]");
  st &&
    (st.onclick = () => {
      mbCloseModal();
      const ids = t2Sort(t2ViewOf(t2Pool(), "done" === t2View ? "all" : t2View)).filter((x) => "hub" === x.kind).map((x) => x.id);
      ids.length ? ((hbQueueRun = { ids: ids, i: 0 }), hbRunQueue()) : toast("No sales task in this list to start");
    });
  tkKeyboardDown(m);
  return m;
}
// the keyboard stays down when a sheet opens: nothing is focused for typing until the person taps a field
function tkKeyboardDown(m) {
  const blur = () => {
    const a = document.activeElement;
    a && m && m.contains(a) && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName) && a.blur();
  };
  setTimeout(blur, 31), setTimeout(blur, 80);
}

// ---- the task sheet: tap a task anywhere and this opens -------------------------------------------------------------
// key: "kind:id:projectId" (t2Key, tdyKeyOf), a tkAll shape, or a tkItems row.
function tkResolve(k) {
  const key = "string" == typeof k ? k : k && (k.key || (k.kind && t2Key(k)));
  if (!key) return null;
  let x = null,
    t = null;
  try {
    x = tkItems().find((y) => t2Key(y) === key) || null;
  } catch (e) {}
  try {
    t = tkAll().find((y) => y.key === key) || null;
  } catch (e) {}
  // a schedule line the crew or a sub does is not anybody's task, but the field still opens its card
  if (!x && !t && /^sched:/.test(key)) {
    const [, id, pid] = key.split(":"),
      p = (DB.projects || []).find((q) => q.id === pid),
      s = p && (p.tasks || []).find((q) => q.id === id);
    if (!s) return null;
    const td = today(),
      due = s.end || s.start || "";
    x = { kind: "sched", id: id, projectId: pid, project: shortName(p), title: s.name, assignee: s.owner || "Crew", due: due, priority: "", status: "done" === s.status ? "done" : "todo", done: "done" === s.status, late: "done" !== s.status && !!due && due < td, area: "construction", source: "schedule", notes: s.notes || "" };
    try {
      const o = tdyOwnerOf(x);
      Object.assign(x, { owner: o.name, ownerUid: o.uid || "", ownerHow: o.how, party: o.party || "" });
      t = tdyShape(x);
    } catch (e) {}
  }
  if (!x && !t) return null;
  const rec = x ? tdyRec(x) : null;
  return { key: key, x: x || (t && t.row) || t, t: t, rec: rec };
}
const TK_DUE_KINDS = /^(action|firm|hub|issue|lead)$/;
function tkSetDue(R, date) {
  const x = R.x,
    rec = R.rec,
    was = x.due || "";
  if ("lead" === x.kind) {
    const l = (DB.leads || []).find((y) => y.id === x.id);
    if (!l) return !1;
    l.nextDue = date;
  } else {
    if (!rec) return !1;
    rec.due = date;
    "firm" === x.kind && (rec.modifiedAt = today());
  }
  try {
    audit("task", x.id, "due", was, date, "");
  } catch (e) {}
  rec && tkLog(rec, { ev: "due", from: was, to: date });
  return !0;
}
function tkLog(rec, e) {
  const me = tdyMe();
  // each entry has an id, so two devices that each add a comment keep both when they merge (cloud.js merge3)
  (rec.thread = rec.thread || []).push(Object.assign({ id: uid("c"), at: appNowIso(), by: me.name || "", byUid: me.id || "" }, e));
}
// where the task came from, one tap away
function tkSourceOf(R) {
  const x = R.x,
    rec = R.rec || {},
    p = x.projectId ? (DB.projects || []).find((q) => q.id === x.projectId) : null,
    src = rec.source || {},
    link = rec.link || {},
    go = (v, pid) => () => (pid && setCurrent(pid), (view = v), render());
  if ("sched" === x.kind && p) return { label: `Schedule line on ${shortName(p)}`, go: go("sched", p.id) };
  if ("issue" === x.kind && p) return { label: `Field question on ${shortName(p)}`, go: () => (setCurrent(p.id), openEditor("iss", x.id)) };
  if ("ob" === x.kind || x.obId) return { label: "Obligation (a renewal or a filing)", go: () => tdyOpenSource(R.t || x) };
  if ("hub" === x.kind || "lead" === x.kind) return { label: "Sales", go: () => tdyOpenSource(R.t || x) };
  if ("draft" === x.kind) return { label: "The assistant's draft", go: () => tdyOpenSource(R.t || x) };
  if (src.commId) {
    const c = (DB.comms || []).find((m) => m.id === src.commId);
    return { label: `Message${c && c.from && c.from.name ? " from " + c.from.name : ""}${c && c.subject ? ": " + tdWords(c.subject, 6) : ""}`, go: () => ((cmOpen = src.commId), (view = "comms"), render()) };
  }
  if (src.chat && src.chat.key) return { label: src.label ? tdWords(src.label, 8) : "A chat message", go: () => ("function" == typeof msgOpen ? msgOpen(src.chat.key) : ((view = "chat"), render())) };
  if (src.meetingId || "meeting" === src.kind) return { label: "A meeting's next step", go: go("meetings") };
  if (rec.recur) return { label: `The SmartDesign Standard${TDY_DUTY[rec.recur.duty] ? " · " + TDY_DUTY[rec.recur.duty].every : ""}`, go: () => ((view = (ROLE_VIEWS[role()] || []).includes("standard") ? "standard" : view), render()) };
  if ("dec" === link.kind && p) return { label: `Decision on ${shortName(p)}`, go: go("dec", p.id) };
  if ("po" === link.kind) {
    const po = (DB.pos || []).find((q) => q.id === link.id);
    if (po) return { label: `Purchase order ${po.number}`, go: () => flowGo.po(po)() };
  }
  if ("mat" === link.kind && p) return { label: `Material on ${shortName(p)}`, go: go("mat", p.id) };
  if ("task" === link.kind && p) return { label: `Schedule line on ${shortName(p)}`, go: go("sched", p.id) };
  if ("insp" === link.kind && p) return { label: `Inspection on ${shortName(p)}`, go: go("insp", p.id) };
  if (src.label) return { label: tdWords(src.label, 8), go: p ? go("dash", p.id) : null };
  if (p) return { label: shortName(p), go: go("dash", p.id) };
  return null;
}
// the task's next step, where it has one; Done otherwise
function tkNextStep(R) {
  const x = R.x,
    t = R.t || {},
    rec = R.rec || {},
    me = tdyMe();
  if (t.offeredToUid && t.offeredToUid === me.id) return { label: "Accept", run: () => tdyAccept(x), accept: !0 };
  if ("draft" === x.kind) return { label: "Open the Draft", run: () => tdyOpenSource(t) };
  if ("action" === x.kind) {
    try {
      const f = clTaskFind(x.id),
        src = f && clSrc(f.a, f.p);
      if (src && src.verb && src.run) return { label: src.verb, run: () => src.run() };
    } catch (e) {}
  }
  if (rec.recur && "friday" === rec.recur.duty && x.projectId && "function" == typeof rsFridayDraft) {
    const p = (DB.projects || []).find((q) => q.id === x.projectId);
    if (p)
      return {
        label: "Draft the Update",
        run: () => {
          const d = rsFridayDraft(p);
          save();
          toast(d ? `The Friday update for ${shortName(p)} is drafted: read it, then send it` : "Nothing to draft yet", [{ label: "Open", run: () => mGo({ view: "brain", bnTab: "hands" }) }]);
        },
      };
  }
  if (rec.recur && "delivery" === rec.recur.duty) return { label: "Open the Order", run: () => tdyOpenSource(t.key ? t : x) };
  if ("sched" === x.kind && rec && "done" !== rec.status) {
    if ("in-progress" !== rec.status)
      return {
        label: "Start It",
        run: () => {
          const was = { status: rec.status, actualStart: rec.actualStart };
          rec.status = "in-progress";
          rec.actualStart || (rec.actualStart = today());
          try {
            log(`${rec.name}: started`, "field", tdyMe().name || "");
          } catch (e) {}
          save(), render();
          toast(`Started: ${tdWords(rec.name, 8)}`, [{ label: "Open", run: () => tkSheet(R.key) }, { label: "Undo", run: () => (Object.assign(rec, was), save(), render()) }]);
        },
      };
    if ("function" == typeof prgSheet) return { label: "Update Progress", run: () => prgSheet(x.id, x.projectId) };
  }
  return null;
}
function tkPeopleFor(R) {
  const me = tdyMe(),
    owner = (R.t && R.t.ownerUid) || "",
    sched = "sched" === R.x.kind;
  return tdyUsers()
    .filter((u) => u.id !== me.id && u.id !== owner && (sched || !/^(crew|driver)$/.test(u.role)))
    .sort((a, b) => (/^(crew|driver)$/.test(a.role) ? 1 : 0) - (/^(crew|driver)$/.test(b.role) ? 1 : 0) || a.name.localeCompare(b.name));
}
const TK_ROLE_SAY = { owner: "Owner", pm: "Project Manager", coord: "Coordinator", foreman: "Foreman", crew: "Crew", driver: "Driver", designer: "Designer", design_mgr: "Design", billing: "Billing", controller: "Controller" };
function tkThreadHtml(R) {
  const rec = R.rec || {},
    out = [];
  rec.notes && !rec.notesMoved && out.push(`<div class="tks-note"><span class="small muted">Note${rec.createdBy ? " · " + esc(rec.createdBy) : ""}</span><div>${esc(rec.notes)}</div></div>`);
  (rec.thread || []).forEach((e) => {
    const when = `${esc(tkFirst(e.by) || "Someone")} · ${esc(fmt(String(e.at || "").slice(0, 10)))}`;
    if (e.text) out.push(`<div class="tks-note"><span class="small muted">${when}</span><div>${esc(e.text)}</div></div>`);
    else if (e.photo || e.img) out.push(`<div class="tks-note"><span class="small muted">${when} · photo</span>${e.img ? `<img class="tks-img" src="${esc(e.img)}" alt="Photo on the task">` : ""}</div>`);
    else if ("file" === e.ev && e.file) out.push(`<div class="tks-note"><span class="small muted">${when} · file</span><div>${esc(e.name || "file")}</div></div>`);
    else if ("note" === e.ev && e.was) out.push(`<div class="tks-note was"><span class="small muted">${when} · earlier note, kept</span><div>${esc(e.was)}</div></div>`);
  });
  return out.join("");
}
function tkHistoryLines(R) {
  const rec = R.rec || {},
    L = [];
  (rec.handoffs || []).forEach((h) =>
    L.push([h.at, "offered" === h.ev ? `${h.by || h.from} offered it to ${h.to}${h.note ? `: ${h.note}` : ""}` : "accepted" === h.ev ? `${h.by} accepted it` : "declined" === h.ev ? `${h.by} declined: ${h.reason || ""}` : `${h.ev} by ${h.by || ""}`]),
  );
  (rec.thread || []).forEach((e) => {
    "due" === e.ev && L.push([e.at, `${tkFirst(e.by)} set the due date to ${e.to ? fmtL(e.to) : "none"}${e.from ? ` (was ${fmtL(e.from)})` : ""}`]);
    "step" === e.ev && L.push([e.at, `${tkFirst(e.by)} ${e.done ? "ticked" : "unticked"} “${e.t}”`]);
  });
  return L.sort((a, b) => String(a[0]).localeCompare(String(b[0])))
    .slice(-8)
    .map(([at, s]) => `<li><span class="small muted">${esc(fmt(String(at || "").slice(0, 10)))}</span> ${esc(s)}</li>`)
    .join("");
}
let tkSheetKey = "";
// Hand Off (taskfix #2, #3): one sheet of people, on the first screen, nothing folded. A tap picks a person (it hands
// nothing off), a note is optional, and one blue "Hand Off to <Name>" commits. The swipe's Hand Off, the task sheet's
// and Today's all open it. The sender owns the task until the other person accepts (tdyHandOff, rec.handoff).
function tkHandSheet(k) {
  const R = tkResolve(k);
  if (!R) return toast("That task is no longer here"), null;
  const x = R.x,
    t = R.t || {},
    me = tdyMe(),
    P = tkPeopleFor(R),
    code = (R.rec && R.rec.code) || x.code || "",
    from = t.owner && t.owner !== me.name ? tkFirst(t.owner) + "'s" : "yours";
  if (!R.rec || !P.length) return toast("Nobody else on the team can take this one"), null;
  let pick = "";
  const m = mbModal(
    `Hand Off${code ? ` ${esc(code)}` : ""}`,
    `<p class="small muted tkh-say">${esc(tdWords(x.title || t.title || "", 10))}. It stays ${esc(from)} until they accept.</p>
<div class="tkh-people" role="radiogroup" aria-label="Hand off to">${P.map((u) => `<button type="button" class="tkh-p" role="radio" aria-checked="false" data-tkhto="${esc(u.name)}"><b>${esc(tkFirst(u.name))}</b>${TK_ROLE_SAY[u.role] && TK_ROLE_SAY[u.role] !== tkFirst(u.name) ? `<small>${esc(TK_ROLE_SAY[u.role])}</small>` : ""}</button>`).join("")}</div>
<input class="tks-in tkh-note" data-tkhnote placeholder="What they need to know (optional)" aria-label="What they need to know">`,
    {
      submit: "Hand Off",
      onSubmit: () => {
        if (!pick) return toast("Pick who takes it"), !1;
        const note = ((m.querySelector("[data-tkhnote]") || {}).value || "").trim();
        tdyHandOff(R.t && R.t.key ? Object.assign({}, x, { owner: R.t.owner, ownerUid: R.t.ownerUid, ownerHow: R.t.ownerHow }) : x, pick, note);
        return !0;
      },
    },
  );
  if (!m) return null;
  m.classList.add("tkh-on");
  const ok = m.querySelector("#mbm-ok"),
    cancel = m.querySelector("#mbm-cancel");
  ok && ok.classList.add("tkh-ok");
  cancel && (cancel.textContent = "Cancel");
  m.querySelectorAll("[data-tkhto]").forEach(
    (b) =>
      (b.onclick = () => {
        pick = b.dataset.tkhto;
        m.querySelectorAll("[data-tkhto]").forEach((y) => (y.classList.toggle("on", y === b), y.setAttribute("aria-checked", y === b ? "true" : "false")));
        ok && (ok.textContent = `Hand Off to ${tkFirst(pick)}`);
      }),
  );
  const n = m.querySelector("[data-tkhnote]");
  n && n.addEventListener("keydown", (e) => "Enter" === e.key && (e.preventDefault(), e.stopPropagation()));
  tkKeyboardDown(m);
  return m;
}
function tkSheet(k, opts) {
  const R = tkResolve(k);
  if (!R) return toast("That task is no longer here"), null;
  if (R && (opts || {}).hand) return tkHandSheet(R.key);
  const O = opts || {},
    x = R.x,
    t = R.t || {},
    rec = R.rec,
    me = tdyMe(),
    td = today(),
    H = t.handoff || (rec && rec.handoff) || null,
    offeredToMe = !!(t.offeredToUid && t.offeredToUid === me.id),
    sched = "sched" === x.kind,
    done = !!(x.done || t.done || (rec && "done" === rec.status)),
    src = tkSourceOf(R),
    next = done ? null : tkNextStep(R),
    w = t2When(x),
    canDue = !done && TK_DUE_KINDS.test(x.kind) && !!(rec || "lead" === x.kind),
    canHand = !done && "draft" !== x.kind && !offeredToMe && !!rec,
    proofNeed = !done && t.proofNeed ? t.proofNeed : null,
    proofMet = proofNeed ? tdyProofMet(x, proofNeed, rec) : null,
    steps = (rec && rec.checklist) || [],
    dates = [
      ["Today", td],
      ["Tomorrow", iso(addDays(parse(td), 1))],
      ["Next Week", addWork(td, 5)],
    ],
    lines = [
      `<span class="tk2-when tk2-w-${w.cls}">${esc(x.due ? (x.due < td ? `Overdue since ${fmtL(x.due)}` : `Due ${fmtL(x.due)}`) : "No date")}</span>`,
      sched && rec && rec.start ? `<span>${esc(fmtL(rec.start))} to ${esc(fmtL(rec.end))}</span>` : "",
      sched && rec ? `<span>${esc({ "in-progress": "under way", done: "finished" }[rec.status] || "not started")}</span>` : "",
      `<span>Owner: ${esc(t.owner || x.assignee || "nobody yet")}${t.party ? ` (done by ${esc(t.party)})` : ""}${(x.collaborators || []).length ? `, with ${esc(x.collaborators.join(", "))}` : ""}</span>`,
      x.project && !src ? `<span>${esc(x.project)}</span>` : "",
    ].filter(Boolean);
  tkSheetKey = R.key;
  const body = `<div class="tks" data-tks="${esc(R.key)}">
  <div class="tks-lines">${lines.join('<span class="tk2-dot"> · </span>')}</div>
  ${src ? `<button type="button" class="tks-src" data-tkssrc>${tkSvg("link", 16)}<span class="grow">From: ${esc(src.label)}</span><b>Open</b></button>` : ""}
  ${H && "offered" === H.state ? `<div class="tks-hand ${offeredToMe ? "me" : ""}">${offeredToMe ? `${esc(H.from)} offered this to you${H.note ? `: “${esc(H.note)}”` : ""}. It is ${esc(tkFirst(H.from))}'s until you accept.` : `Offered to ${esc(H.to)} by ${esc(H.from)}, not accepted yet: it stays on ${esc(tkFirst(H.from))}'s list until then.`}</div>${offeredToMe ? `<div class="tks-row"><input class="tks-in" data-tksreason placeholder="If you decline, say why"><button type="button" class="btn" data-tksdecline>Decline</button></div>` : ""}` : H && "declined" === H.state ? `<div class="tks-hand">${esc(H.to)} declined: ${esc(H.reason || "")}</div>` : ""}
  ${proofNeed ? `<div class="tks-proof ${proofMet ? "ok" : ""}">${esc(proofMet ? `Proof on file: ${proofMet.what}` : `Done asks for ${proofNeed.label.toLowerCase()}: the Standard needs the proof`)}</div>` : ""}
  ${
    canDue
      ? `<div class="tks-h">Due</div><div class="tks-chips">${dates.map(([n, d]) => `<button type="button" class="tks-chip ${x.due === d ? "on" : ""}" data-tksdue="${d}">${n}<small>${esc(fmt(d))}</small></button>`).join("")}<label class="tks-chip tks-pick">Pick<input type="date" data-tkspick value="${esc(x.due || "")}" aria-label="Pick a day"></label></div>`
      : !done && "draft" !== x.kind
        ? `<div class="tks-h">Remind Me</div><div class="tks-chips">${dates.slice(1).map(([n, d]) => `<button type="button" class="tks-chip" data-tksdefer="${d}">${n}<small>${esc(fmt(d))}</small></button>`).join("")}</div><p class="small muted tks-why">${sched ? "This moves it on your list only. The schedule's dates move through Edit Schedule." : "This moves it on your list only."}</p>`
        : ""
  }
  ${
    canHand
      ? `<button type="button" class="tks-handbtn" data-tkshandopen>${tkSvg("hand", 18)}<span class="grow">Hand Off</span><small>${esc(t.owner ? `${tkFirst(t.owner)} owns it until the other person accepts` : "it stays yours until they accept")}</small></button>`
      : ""
  }
  ${rec && /^(action|firm|hub)$/.test(x.kind) && "function" == typeof tkRecSheetHtml ? tkRecSheetHtml(R, done) : ""}
  ${
    rec
      ? `<div class="tks-h">Checklist</div><div class="tks-steps">${steps
          .map((s, i) => `<button type="button" class="tks-step ${s.done ? "on" : ""}" data-tksstep="${i}"><span class="tks-box"></span><span class="grow">${esc(s.t)}</span></button>`)
          .join("")}<div class="tks-row"><input class="tks-in" data-tksstepin placeholder="Add a step"><button type="button" class="btn" data-tksstepadd>Add</button></div></div>`
      : ""
  }
  ${
    rec
      ? `<div class="tks-h">Notes and Photos</div><div class="tks-thread">${tkThreadHtml(R) || '<p class="small muted">Nothing written yet.</p>'}</div><div class="tks-row"><input class="tks-in" data-tksnote placeholder="Add a note"><button type="button" class="btn" data-tksnoteadd>Add</button><button type="button" class="btn tks-cam" data-tkscam aria-label="Add a Photo" title="Add a Photo">${tkSvg("camera")}</button></div>`
      : ""
  }
  ${(() => {
    const h = tkHistoryLines(R);
    return h ? `<details class="tks-hist"><summary>History</summary><ul>${h}</ul></details>` : "";
  })()}
  <div class="tks-more">${!done && "draft" !== x.kind ? `<button type="button" class="btn" data-tkslater>Later</button>` : ""}${"draft" !== x.kind ? `<button type="button" class="btn" data-tksedit>${sched ? "Edit Schedule" : "Edit"}</button>` : ""}${next && !offeredToMe && !done ? `<button type="button" class="btn" data-tksdone>Mark Done</button>` : ""}</div>
</div>`;
  const primary = offeredToMe ? "Accept" : done ? null : next ? next.label : "Mark Done";
  const code = (rec && rec.code) || x.code || "";
  const m = mbModal(`${code ? `<span class="tks-key">${esc(code)}</span> ` : ""}${esc(x.title || t.title || "Task")}`, body, {
    submit: primary,
    onSubmit: () => {
      if (offeredToMe) return tdyAccept(x), !0;
      if (next) return setTimeout(() => next.run(), 0), !0;
      return setTimeout(() => tdyDone(t.key ? t : Object.assign({ row: x }, x)), 0), !0;
    },
  });
  if (!m) return null;
  m.classList.add("tks-on");
  // the dialog's name is the title as written (mbModal escapes it a second time for the attribute)
  const box = m.querySelector(".mbm-box");
  box && box.setAttribute("aria-label", `${code ? code + " " : ""}${x.title || t.title || "Task"}`);
  const cancel = m.querySelector("#mbm-cancel");
  cancel && (cancel.textContent = "Close");
  const q = (s) => m.querySelector(s),
    again = () => setTimeout(() => tkSheet(R.key), 0),
    refresh = () => {
      save();
      try {
        "tkall" === view || T2_SCOPED[view] ? renderTkAll() : render();
      } catch (e) {}
      again();
    };
  rec && /^(action|firm|hub)$/.test(x.kind) && "function" == typeof tkRecSheetWire && tkRecSheetWire(m, R, refresh);
  const sb = q("[data-tkssrc]");
  sb && src && src.go && (sb.onclick = () => (mbCloseModal(), src.go()));
  m.querySelectorAll("[data-tksdue]").forEach(
    (b) =>
      (b.onclick = () => {
        tkSetDue(R, b.dataset.tksdue) && (refresh(), toast(`Due ${fmtL(b.dataset.tksdue)}: ${tdWords(x.title, 8)}`, [{ label: "Open", run: () => tkOpen(R.key) }]));
      }),
  );
  const pick = q("[data-tkspick]");
  pick &&
    (pick.onchange = () => {
      pick.value && tkSetDue(R, pick.value) && (refresh(), toast(`Due ${fmtL(pick.value)}: ${tdWords(x.title, 8)}`, [{ label: "Open", run: () => tkOpen(R.key) }]));
    });
  m.querySelectorAll("[data-tksdefer]").forEach(
    (b) =>
      (b.onclick = () => {
        t2SetDefer(x, b.dataset.tksdefer), mbCloseModal();
        try {
          "tkall" === view || T2_SCOPED[view] ? renderTkAll() : render();
        } catch (e) {}
        toast(`On your list again ${fmtL(b.dataset.tksdefer)}: ${tdWords(x.title, 8)}`, [{ label: "Open", run: () => tkOpen(R.key) }]);
      }),
  );
  const ho = q("[data-tkshandopen]");
  ho && (ho.onclick = () => (mbCloseModal(), tkHandSheet(R.key)));
  const dec = q("[data-tksdecline]");
  dec &&
    (dec.onclick = () => {
      const why = ((q("[data-tksreason]") || {}).value || "").trim();
      tdyDecline(x, why) && mbCloseModal();
    });
  m.querySelectorAll("[data-tksstep]").forEach(
    (b) =>
      (b.onclick = () => {
        const s = steps[+b.dataset.tksstep];
        if (!s) return;
        (s.done = !s.done), (s.by = me.name || ""), (s.at = appNowIso());
        tkLog(rec, { ev: "step", t: s.t, done: s.done });
        refresh();
      }),
  );
  const addStep = () => {
    const i = q("[data-tksstepin]"),
      v = ((i && i.value) || "").trim();
    if (!v) return toast("Say what the step is");
    (rec.checklist = rec.checklist || []).push({ t: v, done: !1, by: me.name || "", at: appNowIso() });
    refresh();
  };
  const sa = q("[data-tksstepadd]");
  sa && (sa.onclick = addStep);
  const addNote = () => {
    const i = q("[data-tksnote]"),
      v = ((i && i.value) || "").trim();
    if (!v) return toast("Write the note first");
    tkLog(rec, { text: v });
    try {
      audit("task", x.id, "note", "", v.slice(0, 80), "");
    } catch (e) {}
    refresh();
    toast(`Note added to ${tdWords(x.title, 8)}`, [{ label: "Open", run: () => tkOpen(R.key) }]);
  };
  const na = q("[data-tksnoteadd]");
  na && (na.onclick = addNote);
  // Enter in a field adds what was typed; it never presses the sheet's blue button
  [
    ["[data-tksnote]", addNote],
    ["[data-tksstepin]", addStep],
  ].forEach(([s, fn]) => {
    const i = q(s);
    i &&
      i.addEventListener("keydown", (e) => {
        "Enter" === e.key && (e.preventDefault(), e.stopPropagation(), fn());
      });
  });
  ["[data-tksreason]"].forEach((s) => {
    const i = q(s);
    i && i.addEventListener("keydown", (e) => "Enter" === e.key && (e.preventDefault(), e.stopPropagation()));
  });
  const cam = q("[data-tkscam]");
  cam && (cam.onclick = () => mReadPhoto((url) => (tkAddPhoto(R, url), refresh(), toast(`Photo added to ${tdWords(x.title, 8)}`, [{ label: "Open", run: () => tkOpen(R.key) }])), "environment"));
  const later = q("[data-tkslater]");
  later && (later.onclick = () => (mbCloseModal(), t2LaterDialog(R.key)));
  const ed = q("[data-tksedit]");
  ed &&
    (ed.onclick = () => {
      mbCloseModal();
      rec && (tkNoteWatch = { key: R.key, notes: rec.notes || "" });
      if ("hub" === x.kind && "function" == typeof hbTaskPanel) return hbTaskPanel({ task: rec }, () => render());
      if ("lead" === x.kind || "ob" === x.kind) return tdyOpenSource(R.t || x);
      x.projectId && "function" == typeof setCurrent && (!S || S.id !== x.projectId) && setCurrent(x.projectId);
      tkEditBypass = !0;
      try {
        openEditor("tk", `${x.kind}|${x.projectId || ""}|${x.id}`);
      } finally {
        tkEditBypass = !1;
      }
    });
  const dn = q("[data-tksdone]");
  dn && (dn.onclick = () => (mbCloseModal(), setTimeout(() => tdyDone(t.key ? t : Object.assign({ row: x }, x)), 0)));
  O.keyboard || tkKeyboardDown(m);
  return m;
}
// a photo on the task: on the job's files, linked to the task (the proof check reads the same link), and on its thread
function tkAddPhoto(R, url) {
  const x = R.x,
    rec = R.rec,
    p = x.projectId ? (DB.projects || []).find((q) => q.id === x.projectId) : null,
    id = uid("f");
  if (p) {
    p.files = p.files || [];
    const f = { id: id, name: `task-${today()}.jpg`, type: "image/jpeg", size: Math.round(0.75 * url.length), cat: "photo", date: today(), by: tdyMe().name || "", link: { kind: "task", id: x.id }, notes: x.title, shareClient: !1, ai: null, persisted: !1, uploadedAt: appNowIso(), dataUrl: url };
    p.files.push(f);
    try {
      putBlob(id, url).then((ok) => (f.persisted = ok));
    } catch (e) {}
    rec && tkLog(rec, { photo: id, img: url });
  } else rec && tkLog(rec, { photo: id, img: url });
}
// the editor opened from the sheet: a note it replaces is kept on the thread (never overwritten)
let tkNoteWatch = null,
  tkEditBypass = !1;
function tkNoteCheck() {
  if (!tkNoteWatch) return;
  const W = tkNoteWatch,
    R = tkResolve(W.key);
  if (!R || !R.rec) return void (tkNoteWatch = null);
  if (document.getElementById("mbm") || (typeof editing !== "undefined" && editing)) return;
  tkNoteWatch = null;
  W.notes && (R.rec.notes || "") !== W.notes && (tkLog(R.rec, { ev: "note", was: W.notes }), save());
}
// open a task where it lives: the list with it in view and highlighted, then its sheet
function tkOpen(k) {
  const R = tkResolve(k);
  if (!R) return;
  const x = R.x;
  try {
    const may = (v) => (ROLE_VIEWS[role()] || []).includes(v);
    if (may("tkall") && !T2_SCOPED[view]) {
      view = "tkall";
      tkWho = tkOwnerMatch(x.assignee, tkMe()) ? "me" : "all";
      tkProject = "";
      tkArea = "";
      tkPri = "";
      t2Q = "";
      t2View = x.done ? "done" : !x.due || t2DeferOf(x) ? (t2DeferOf(x) ? "later" : "nodate") : x.due <= iso(addDays(parse(today()), 7)) ? "week" : "all";
      crFlash = x.id;
      crFlashUntil = Date.now() + 4e3;
      render();
    }
  } catch (e) {}
  setTimeout(() => tkSheet(R.key), 0);
}

// ---- wiring: a tap opens the sheet, a swipe shows Later and Hand Off, the check finishes ------------------------------
function tkWireList(host) {
  if (!host) return;
  host.querySelectorAll(".tk2-row").forEach((r) => {
    r.onclick = (e) => {
      if (e.target.closest("button, a, input, select")) return;
      if (r.classList.contains("swiped")) return void r.classList.remove("swiped");
      tkSheet(r.dataset.tkkey);
    };
    r.onkeydown = (e) => {
      "Enter" === e.key && e.target === r && (e.preventDefault(), tkSheet(r.dataset.tkkey));
    };
    tkSwipe(r);
  });
  host.querySelectorAll("[data-t2done]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.stopPropagation(), tkCheckDone(b.dataset.t2done);
      }),
  );
  host.querySelectorAll("[data-tkhand]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.stopPropagation();
        const r = b.closest(".tk2-row");
        r && r.classList.remove("swiped");
        tkHandSheet(b.dataset.tkhand);
      }),
  );
  host.querySelectorAll("[data-t2later]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.stopPropagation();
        const r = b.closest(".tk2-row");
        r && r.classList.remove("swiped");
        t2LaterDialog(b.dataset.t2later);
      }),
  );
  const f = host.querySelector("[data-tkfilter]");
  f && (f.onclick = () => tkFilterSheet());
  const s = host.querySelector("[data-tksearch]");
  s &&
    (s.onclick = () => {
      window.__tkSearch = !0;
      renderTkAll();
      const i = document.getElementById("t2-q");
      i && i.focus();
    });
  const sx = host.querySelector("[data-tksearchx]");
  sx && (sx.onclick = () => ((window.__tkSearch = !1), (t2Q = ""), renderTkAll()));
  const o = host.querySelector("[data-tkoffer]");
  o &&
    (o.onclick = () => {
      const L = tkOfferedToMe();
      if (1 === L.length) return tkSheet(L[0].key);
      const m = mbModal(
        "Offered to You",
        `<div class="tks-offers">${L.map((t, i) => `<button type="button" class="tks-src" data-tkofferi="${i}"><span class="grow"><b>${esc(t.title)}</b><small class="muted"> · from ${esc(t.owner)}${t.due ? ` · due ${esc(fmtL(t.due))}` : ""}</small></span><b>Open</b></button>`).join("")}</div>`,
        { submit: null },
      );
      m && m.querySelectorAll("[data-tkofferi]").forEach((b) => (b.onclick = () => (mbCloseModal(), tkSheet(L[+b.dataset.tkofferi].key))));
    });
}
// Done from the row: the proof gate in tkToggle asks for the photo where the Standard needs one
function tkCheckDone(key) {
  const [kind, id, pid] = String(key).split(":"),
    x = tkItems().find((y) => t2Key(y) === key);
  if (!x) return;
  tkToggle(kind, id, pid || "");
  if ("ob" === kind || "lead" === kind) return;
  const now = tkItems().find((y) => t2Key(y) === key);
  if (!now || !now.done) return;
  save();
  try {
    renderTkAll();
  } catch (e) {}
  toast(`Done: ${tdWords(x.title, 8)}`, [
    { label: "Open", run: () => tkOpen(key) },
    { label: "Undo", run: () => (tkToggle(kind, id, pid || ""), save(), renderTkAll()) },
  ]);
}
// swipe left on a row: Later and Hand Off slide in (the same two are in the sheet for anyone who doesn't swipe)
function tkSwipe(r) {
  let x0 = 0,
    y0 = 0,
    on = !1;
  r.addEventListener(
    "touchstart",
    (e) => {
      const t = e.touches[0];
      (x0 = t.clientX), (y0 = t.clientY), (on = !0);
    },
    { passive: !0 },
  );
  r.addEventListener(
    "touchmove",
    (e) => {
      if (!on) return;
      const t = e.touches[0],
        dx = t.clientX - x0,
        dy = t.clientY - y0;
      if (Math.abs(dy) > Math.abs(dx)) return void (on = !1);
      dx < -40 && (r.classList.add("swiped"), (on = !1));
      dx > 30 && (r.classList.remove("swiped"), (on = !1));
    },
    { passive: !0 },
  );
  r.addEventListener("touchend", () => (on = !1), { passive: !0 });
}
{
  const base = t2Wire;
  t2Wire = function (host) {
    const r = base.apply(this, arguments);
    try {
      tkWireList(host);
    } catch (e) {
      console.warn("task list wiring", e);
    }
    return r;
  };
}
// the outermost list render: the phone shows the list only (no board or table), and the rows open the sheet
{
  const base = renderTkAll;
  renderTkAll = function () {
    const ph = tkPhone(),
      keep = tkMode;
    ph && "cards" !== keep && (tkMode = "cards");
    try {
      base.apply(this, arguments);
    } finally {
      ph && (tkMode = keep);
    }
    try {
      const host = document.getElementById("tkall-body");
      host && (tkWireList(host), host.querySelectorAll(".ph .lead").forEach((l) => ph && l.remove()));
      // a chip that shows no number is no badge's source (the job's Overdue day is)
      host && host.querySelectorAll("[data-t2view][data-ocbadge]").forEach((el) => el.querySelector(".n") || el.removeAttribute("data-ocbadge"));
    } catch (e) {
      console.warn("task list", e);
    }
  };
}
// Make an open of a task (New Task's toast, Ask's reminder, a chat's task) land on the task and open its sheet
crOpenTask = function (m) {
  if (!m) return;
  const key = `${m.kind}:${m.id}:${m.projectId || ""}`;
  try {
    "hub" !== m.kind && tkLand(m);
  } catch (e) {}
  setTimeout(() => tkSheet(key), 0);
};
{
  const base = tkLand;
  tkLand = function (m) {
    const r = base.apply(this, arguments);
    try {
      if ("today" === t2View || "week" === t2View) {
        t2View = "week";
        render();
      }
    } catch (e) {}
    return r;
  };
}
// openEditor("tk", ...) from anywhere outside the sheet (a toast's Open, an old link) opens the sheet first; the
// sheet's own Edit goes through to the editor
if ("function" == typeof openEditor) {
  const base = openEditor;
  openEditor = function (kind, id) {
    if ("tk" === kind && !tkEditBypass) {
      const [k, pid, tid] = String(id).split("|");
      if (tkResolve(`${k}:${tid}:${pid || ""}`)) return void tkSheet(`${k}:${tid}:${pid || ""}`);
    }
    return base.apply(this, arguments);
  };
}

// ---- Today: the same sheet, a tap on the card opens it, and an offer is answered today -------------------------------
tdyTaskSheet = function (t) {
  return tkSheet(t && (t.key || t2Key(t)));
};
tdyGoTask = function (x) {
  const key = x && (x.key || (x.kind && t2Key(x)));
  key && tkResolve(key) ? tkOpen(key) : (tdyTabSet("tasks"), setView("home"));
};
// an offer to me is owed an answer today: Accept or Decline before it ages (the Standard: close every loop)
{
  const base = tdyTaskItem;
  tdyTaskItem = function (t) {
    const it = base.apply(this, arguments);
    try {
      const me = tdyMe();
      t && t.offeredToUid && t.offeredToUid === me.id && (it.due = today());
      // an obligation's date is its filing (or renewal) date: Today says so, as the list's row does (taskfix #11)
      const o = t && t.row && !t.done && t.due ? tkObOf(t.row) : null;
      o && "function" == typeof flObFile && t.due === flObFile(o) && (it.detail = it.detail.replace(/\b(overdue since|due) /, (m0) => `${"filing" === o.kind ? "filing" : "renewal"} ${m0}`));
    } catch (e) {}
    return it;
  };
}
// a tap anywhere on a Today card's words opens what its title opens (the task's sheet for a task)
document.addEventListener(
  "click",
  (e) => {
    const el = e.target && e.target.closest ? e.target : null;
    if (!el || el.closest("a, button, input, select, textarea, label")) return;
    const card = el.closest(".td-do .td-card");
    // on the desktop a tap on a row selects it into the side panel (today2.js); its title still opens the record
    if (!card || card.hasAttribute("data-td2sel")) return;
    const a = card.querySelector("[data-tdrec]");
    a && (e.preventDefault(), a.click());
  },
  !0,
);
// The foreman's Today's Work and the designer's Today: a tap on a work row opens the same sheet (a schedule line opens
// its card; Started, the % and Done stay on the row).
document.addEventListener(
  "click",
  (e) => {
    const el = e.target && e.target.closest ? e.target : null;
    if (!el || el.closest("a, button, input, select, textarea, label, summary")) return;
    if (!["ftoday", "sday", "time"].includes(view)) return;
    const row = el.closest(".f-row, .fm-row, .sd-trow, [data-tkkey]");
    if (!row || row.closest("#mbm")) return;
    let key = row.dataset.tkkey || "";
    if (!key) {
      const b = row.querySelector("[data-fdone], [data-fm-done], [data-prgopen]");
      if (!b) return;
      const id = b.dataset.fdone || b.dataset.fmDone || String(b.dataset.prgopen || "").split("|")[0],
        pid = String(b.dataset.prgopen || "").split("|")[1] || (S && S.id) || "";
      key = `sched:${id}:${pid}`;
    }
    if (!tkResolve(key)) return;
    e.preventDefault(), e.stopPropagation(), tkSheet(key);
  },
  !0,
);
// Done on the foreman's row asks for the photo where the Standard needs proof (it closed the line with no check)
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("[data-fdone], [data-fm-done]") : null;
    if (!b || b.closest("#mbm")) return;
    try {
      const id = b.dataset.fdone || b.dataset.fmDone,
        pid = (S && S.id) || "",
        x = (tkResolve(`sched:${id}:${pid}`) || {}).x;
      if (!x || x.done) return;
      const rec = tdyRec(x),
        need = tdyProofNeed(x, rec);
      if (!need || tdyProofMet(x, need, rec)) return;
      e.preventDefault(), e.stopPropagation();
      toast(`Not done yet: ${need.label.toLowerCase()} first`);
      tdyProofSheet(x, () => tdyComplete(x));
    } catch (err) {
      console.warn("field proof", err);
    }
  },
  !0,
);

// ---- the designer's Today and the foreman's first screen read the same list ---------------------------------------
// The designer keeps My Day as her Today; its "Due This Week" card said "Nothing due this week" under a "Due or Late 7"
// chip (IA_MAP §2). It now lists her Due Soon from the one list, rows that open the sheet, with the list's own count.
function tkSdayCard(v) {
  const card = [...v.querySelectorAll(".card")].find((c) => /^(today|due this week)$/i.test(((c.querySelector("h3") || {}).textContent || "").trim()));
  if (!card || card.dataset.tk2) return;
  let R = [];
  try {
    R = t2Sort(t2ViewOf(openTasks("me"), "week"));
  } catch (e) {}
  const may = tkMay("tkall"),
    more = R.length > 6 ? R.length - 6 : 0;
  card.dataset.tk2 = "1";
  card.classList.add("tk2-host");
  card.innerHTML = `<div class="hd tk2-hd"><h3>Due Soon</h3><span class="n">${R.length}</span></div><div class="tk2-list tk2-inline">${
    R.slice(0, 6)
      .map((x) => tkRowHtml(x, {}))
      .join("") || '<div class="empty tk2-empty">Nothing due in the next 7 days, and nothing late.</div>'
  }</div>${may ? `<a href="#" class="td-more tk2-more" data-tkallgo>${more ? `${more} more on Tasks` : "Open Tasks"}</a>` : ""}`;
  tkWireList(card);
  const a = card.querySelector("[data-tkallgo]");
  a && (a.onclick = (e) => (e.preventDefault(), (tkWho = "me"), (tkProject = ""), (t2View = "week"), setView("tkall")));
}
// The foreman's first screen on the phone: the intro sentence goes and the packing slip is one camera button, so
// Today's Work starts on the first screen (three rows above the fold, not two; IA_MAP §4 and the foreman's review).
function tkFieldCompact(v) {
  const cap = v.querySelector("#trk-capture");
  if (!cap || cap.dataset.tk2) return;
  cap.dataset.tk2 = "1";
  cap.classList.add("tk2-capcompact");
  const b = cap.querySelector(".trk-big");
  if (b) {
    const svg = b.querySelector("svg");
    b.textContent = "";
    svg && b.appendChild(svg);
    b.appendChild(document.createTextNode(" Packing Slip or Receipt"));
    b.setAttribute("aria-label", "Take a photo of a packing slip or receipt");
  }
}
function tkDecorate() {
  const v = document.querySelector(".view.on");
  if (!v) return;
  "sday" === view && ["designer", "design_mgr"].includes(role()) && (v.classList.add("tk2-sday"), tkSdayCard(v));
  "ftoday" === view && tkPhone() && tkFieldCompact(v);
  // the crew's Clock is their task list: its toggles are thumb-sized too
  if ("time" === view && "crew" === role()) {
    v.classList.add("tk2-clock");
    // Clock In, then today's work: "Worked a day you did not clock?" is housekeeping, so it follows the work on the phone
    const miss = v.querySelector("#tm-missing"),
      work = v.querySelector("#fm-today");
    tkPhone() && miss && work && work.nextElementSibling !== miss && work.after(miss);
  }
}
// ---- one list: the old pages forward to it with their chip set, and leave the menus ----------------------------------
// Sales Tasks is Tasks with the Sales chip; My Day is the designer's Today, and for the owner and the PM it was a second
// Today: it opens Tasks, Mine. The crew's Tasks page goes: Clock is their list.
const TK_FORWARD = {
  hbtasks: () => (tkMay("tkall") ? { view: "tkall", set: () => ((tkProject = "__sales"), (tkWho = "all"), (t2View = "week")) } : null),
  sday: () => (!["designer", "design_mgr"].includes(role()) && tkMay("tkall") ? { view: "tkall", set: () => ((tkProject = ""), (tkWho = "me"), (t2View = "week")) } : null),
  tasks: () => ("crew" === role() ? { view: "time" } : null),
};
const tkMay = (v) => {
  try {
    return (ROLE_VIEWS[role()] || []).includes(v);
  } catch (e) {
    return !1;
  }
};
function tkForward() {
  try {
    const f = TK_FORWARD[view] && TK_FORWARD[view]();
    f && ((view = f.view), f.set && f.set());
  } catch (e) {}
}
function tkPruneViews() {
  try {
    Object.keys(ROLE_VIEWS).forEach((r) => {
      const L = ROLE_VIEWS[r];
      if (!Array.isArray(L)) return;
      const drop = ["hbtasks"].concat(["designer", "design_mgr"].includes(r) ? [] : ["sday"], "crew" === r ? ["tasks"] : []);
      for (let i = L.length - 1; i >= 0; i--) drop.includes(L[i]) && L.splice(i, 1);
    });
  } catch (e) {}
  try {
    for (let i = MN_SALES.length - 1; i >= 0; i--) Array.isArray(MN_SALES[i]) && "hbtasks" === MN_SALES[i][0] && MN_SALES.splice(i, 1);
    MENU.crew.rest = MENU.crew.rest.filter((x) => "tasks" !== x[0]);
  } catch (e) {}
}
tkPruneViews();
{
  const base = render;
  render = function () {
    tkForward();
    const r = base.apply(this, arguments);
    try {
      tkNoteCheck();
    } catch (e) {}
    try {
      tkDecorate();
    } catch (e) {
      console.warn("task rows", e);
    }
    return r;
  };
}
{
  const base = signIn;
  signIn = function () {
    const r = base.apply(this, arguments);
    try {
      tkPruneViews();
      (t2View = "week"), (tkWho = "me"), (tkProject = ""), (t2Group = null), (window.__tkSearch = !1);
    } catch (e) {}
    return r;
  };
}

// ---- no duplicate tasks: Make It a Task offers the matching task or decision first ----------------------------------
const TK_STOP = new Set("the a an and or of to for on in at with from by re fwd follow up call email send get make about this that it is be our your their please".split(" "));
const tkWords = (s) =>
  String(s || "")
    .toLowerCase()
    .replace(/[^a-z0-9 ]+/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 2 && !TK_STOP.has(w));
// the open tasks and decisions on the same job (or the firm) whose words are mostly this title's
function tkMatches(title, projectId) {
  const W = tkWords(title);
  if (W.length < 1) return [];
  const nums = (s) => new Set(String(s || "").match(/\d+/g) || []),
    N = nums(title);
  const score = (s) => {
    // different numbers are different things ("unit 4" is not "unit 5", the second call is not the first)
    const M = nums(s);
    if (N.size && M.size && ![...N].some((n) => M.has(n))) return 0;
    const V = new Set(tkWords(s));
    const hit = W.filter((w) => V.has(w)).length;
    // most of the new title is in the old one, and most of the old one in the new: the same thing said twice
    return hit >= Math.min(2, W.length) && hit / W.length >= 0.7 && hit / Math.max(1, V.size) >= 0.5 ? hit / Math.max(W.length, V.size) : 0;
  };
  const out = [];
  try {
    openTasks("all").forEach((x) => {
      if (projectId && x.projectId && x.projectId !== projectId) return;
      const s = score(x.title);
      s && out.push({ kind: "task", s: s, key: t2Key(x), title: x.title, due: x.due, who: x.assignee || x.owner || "", x: x });
    });
  } catch (e) {}
  (DB.projects || []).forEach((p) => {
    if (projectId && p.id !== projectId) return;
    (p.decisions || [])
      .filter((d) => "open" === d.status)
      .forEach((d) => {
        const s = score(d.name);
        s && out.push({ kind: "decision", s: s, title: d.name, due: d.due || "", who: d.owner || "", p: p, d: d });
      });
  });
  return out.sort((a, b) => b.s - a.s).slice(0, 3);
}
// attach what was about to become a task to the one that exists: its note goes on the task's thread (or the decision's
// notes, kept with who and when), so the third copy is never made
function tkAttach(m, P) {
  const what = `${P.source && P.source.label ? `From ${P.source.label}: ` : ""}${P.notes || P.title || ""}`.trim();
  if ("task" === m.kind) {
    const R = tkResolve(m.key);
    if (!R || !R.rec) return !1;
    tkLog(R.rec, { text: what || P.title, attached: P.source || null });
    save(), render();
    toast(`Added to the task that was already there: ${tdWords(m.title, 8)}`, [{ label: "Open", run: () => tkOpen(m.key) }]);
    return !0;
  }
  const d = m.d,
    who = tdyMe().name || "";
  d.notes = `${d.notes ? d.notes + "\n" : ""}${fmt(today())} ${who}: ${what || P.title}`;
  try {
    audit("decision", d.id, "note", "", (what || P.title).slice(0, 80), "attached instead of a new task");
  } catch (e) {}
  save(), render();
  toast(`Added to the decision that was already open: ${tdWords(m.title, 8)}`, [{ label: "Open", run: () => (setCurrent(m.p.id), (view = "dec"), render()) }]);
  return !0;
}
let tkDupSkip = !1;
// the one guard every Make It a Task path calls: proceed() makes the new task; onSaved(made) hears an attach too
function tkDupGuard(P, proceed, onSaved) {
  if (tkDupSkip || !P || !P.title) return proceed();
  const M = tkMatches(P.title, P.projectId || "");
  if (!M.length) return proceed();
  const base = () => {
    tkDupSkip = !0;
    try {
      return proceed();
    } finally {
      tkDupSkip = !1;
    }
  };
  const m = mbModal(
    "This May Already Be There",
    `<p class="small muted">Before making a new task for “${esc(tdWords(P.title, 10))}”, these are open and read the same. Add it to one of them, or make a new task.</p><div class="tks-offers">${M.map((x, i) => `<button type="button" class="tks-src" data-tkdupi="${i}"><span class="grow"><b>${esc(x.title)}</b><small class="muted"> · ${x.kind === "decision" ? "decision" : "task"}${x.who ? ` · ${esc(x.who)}` : ""}${x.due ? ` · due ${esc(fmtL(x.due))}` : ""}</small></span><b>Add to It</b></button>`).join("")}</div>`,
    { submit: "Make a New Task", onSubmit: () => (setTimeout(base, 0), !0) },
  );
  m &&
    m.querySelectorAll("[data-tkdupi]").forEach(
      (b) =>
        (b.onclick = () => {
          const x = M[+b.dataset.tkdupi];
          mbCloseModal();
          if (tkAttach(x, P) && onSaved)
            try {
              onSaved({ assignee: x.who, due: x.due, attached: !0, kind: x.kind, id: x.kind === "task" ? x.x.id : x.d.id });
            } catch (e) {}
        }),
    );
  return m;
}
// a chat message's Make It a Task and the Inbox's Task From This Message ask the same question first
if ("function" == typeof msgMakeTask) {
  const base = msgMakeTask;
  msgMakeTask = function (key, mid) {
    const self = this,
      args = arguments;
    try {
      const T = msgThread(key, msgMe()),
        mm = T && T.all().find((y) => y.id === mid);
      if (mm && !mm.taskId) {
        const title = String(mm.text || "").slice(0, 90);
        return tkDupGuard({ title: title, projectId: T.pid || "", notes: mm.text, source: { label: `${mm.by || "a"}'s message in ${T.title}` } }, () => base.apply(self, args));
      }
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
if ("function" == typeof cmTaskDialog) {
  const base = cmTaskDialog;
  cmTaskDialog = function (c, p) {
    const self = this,
      args = arguments;
    try {
      const R = c.route || {},
        title = (p && p.task) || c.subject || "";
      return tkDupGuard({ title: title, projectId: R.projectId || "", notes: c.subject || "", source: { label: `a message${c.from && c.from.name ? " from " + c.from.name : ""}` } }, () => base.apply(self, args));
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
{
  const base = newTaskDialog;
  newTaskDialog = function (preset, opts) {
    const P = preset || {};
    if (tkDupSkip || !P.title || !P.source) return base.apply(this, arguments);
    const self = this,
      args = arguments;
    return tkDupGuard(P, () => base.apply(self, args), opts && opts.onSaved);
  };
}

// ---- one priority scale: High, Medium, Low everywhere (the board editor said P1, P2, P3) ------------------------------
if ("function" == typeof asTaskDialog) {
  const base = asTaskDialog;
  asTaskDialog = function () {
    const r = base.apply(this, arguments);
    try {
      const m = document.getElementById("mbm"),
        sel = m && m.querySelector('[data-f="pri3"]');
      if (sel) {
        const say = { P1: "High — first", P2: "Medium — this week", P3: "Low — when it comes round" };
        [...sel.options].forEach((o) => say[o.value] && (o.textContent = say[o.value]));
      }
      // the person comes before the code and the section: a hand-off is the common change
      const who = m && m.querySelector('[data-f="assignee"]'),
        code = m && m.querySelector('[data-f="code"]');
      const gw = who && who.closest(".grid2"),
        gc = code && code.closest(".grid2");
      gw && gc && gw !== gc && gc.parentNode.insertBefore(gw, gc);
      const h = m && m.querySelector(".mbm-hd h3");
      h && /^edit task$/i.test(h.textContent.trim()) && (h.textContent = "Edit Task");
    } catch (e) {}
    return r;
  };
}
// the board's P1/P2/P3 read as the one scale wherever a task shows its priority
const TK_PRI_SAY = { P1: "High", P2: "Medium", P3: "Low" };

// ---- Ask: "how many of my tasks are due soon / overdue / due today" reads the list's own counts ----------------------
"undefined" != typeof AG_ASST &&
  AG_ASST.unshift({
    id: "tkMine",
    first: !0,
    kind: "ops",
    re: /\b(tasks?|to-?dos?)\b[^?]*\b(due soon|next (7|seven) days|this week|overdue|late|past due|due today)\b|\b(due soon|overdue|late|past due)\b[^?]*\b(tasks?|to-?dos?)\b/,
    not: /\b(without|no owner|unassigned|nobody|by person|each|everyone|team|firm|whole company|schedule|moved|slip|finish)\b/,
    run(P) {
      if ("client" === role() || P.jobs.length || P.vendors.length || P.clients.length) return null;
      if (!P.self || (P.people.length && !(P.meEmp && P.people.length === 1 && P.people[0] === P.meEmp))) return null;
      const l = P.l,
        v = /\b(overdue|late|past due)\b/.test(l) && !/\bdue soon|next (7|seven) days|this week\b/.test(l) ? "overdue" : /\bdue today\b/.test(l) ? "today" : "week",
        R = t2Sort(t2ViewOf(openTasks("me"), v)),
        say = { week: "due soon (overdue and the next 7 days)", today: "due today or overdue", overdue: "overdue" }[v];
      return {
        headline: R.length ? `${agN(R.length, "task")} of yours ${1 === R.length ? "is" : "are"} ${say}: ${agList(R.map((x) => `${x.title} — ${x.due ? (x.due < today() ? "overdue since " : "due ") + fmtL(x.due) : "no date"}`), 5)}.` : `Nothing of yours is ${say}.`,
        note: `The same count as Tasks › Mine › ${tkViewName(v)}.`,
        work: R.map((x) => `${x.title} — ${x.due ? fmtL(x.due) : "no date"} — ${x.project || "firm-wide"}`),
        go: agGo("tkall"),
        ran: agRan("tasks", ["owner is me", "open", { week: "due by " + fmtL(iso(addDays(parse(today()), 7))), today: "due by today", overdue: "past due" }[v]], "", R.length),
      };
    },
  });

// ---- the look: rows of 64 to 72px, a 44px circle, 16px titles; the sheet from the bottom on the phone ------------------
(() => {
  const css = `
:is(#v-tkall,.tk2-host) .tk2-row{position:relative;display:block;padding:0;border-bottom:1px solid var(--rule-2);min-height:64px;overflow:hidden;cursor:pointer;grid-template-columns:none;grid-template-areas:none}
:is(#v-tkall,.tk2-host) .tk2-row:hover{background:var(--paper-2)}
:is(#v-tkall,.tk2-host) .tk2-slide{position:relative;z-index:1;display:flex;align-items:center;gap:8px;min-height:63px;max-height:71px;overflow:hidden;padding:4px 12px 4px 4px;background:var(--paper);transition:transform .18s ease;box-sizing:border-box}
:is(#v-tkall,.tk2-host) .tk2-row:hover .tk2-slide{background:var(--paper-2)}
:is(#v-tkall,.tk2-host) .tk2-row.swiped .tk2-slide{transform:translateX(-168px)}
:is(#v-tkall,.tk2-host) .tk2-check{flex:0 0 44px;width:44px;height:44px;border:0;background:none;display:grid;place-items:center;cursor:pointer;padding:0;margin:0}
:is(#v-tkall,.tk2-host) .tk2-check>span{display:block;width:26px;height:26px;border:2px solid var(--ink-3);border-radius:50%;box-sizing:border-box}
:is(#v-tkall,.tk2-host) .tk2-row.late .tk2-check>span{border-color:var(--bad,#b3261e)}
:is(#v-tkall,.tk2-host) .tk2-check:hover>span{background:var(--paper-3,#eee)}
:is(#v-tkall,.tk2-host) .tk2-donemark>span{background:var(--ok-2,#2e7d32);border-color:var(--ok-2,#2e7d32)}
:is(#v-tkall,.tk2-host) .tk2-mid{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:2px}
:is(#v-tkall,.tk2-host) .tk2-title{font-size:16px;line-height:20px;color:var(--ink);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;word-break:break-word}
:is(#v-tkall,.tk2-host) .tk2-row.done .tk2-title{color:var(--ink-3);text-decoration:line-through}
/* high priority is a dark mark, never red: late is the only red on a task row (taskfix #17) */
:is(#v-tkall,.tk2-host) .tk2-hi{display:inline-block;width:4px;height:14px;border-radius:2px;background:var(--ink-2,#3E4450);margin-right:6px;vertical-align:-1px}
:is(#v-tkall,.tk2-host) .tk2-sub{font-size:13px;line-height:17px;color:var(--ink-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
:is(#v-tkall,.tk2-host) .tk2-when.tk2-w-late{color:var(--bad,#b3261e);font-weight:600}
:is(#v-tkall,.tk2-host) .tk2-when.tk2-w-today{color:var(--ink);font-weight:600}
#v-tkall .t2-nodate{margin:0 0 10px}
#v-tkall .t2-nodate .btn{min-height:44px}
:is(#v-tkall,.tk2-host) .tk2-off{color:var(--accent)}
:is(#v-tkall,.tk2-host) .tk2-key{font-size:13px;font-weight:700;letter-spacing:.02em;color:var(--accent);margin-right:6px}
:is(#v-tkall,.tk2-host) .tk2-when.tk2-w-fyi{color:var(--ink-3);font-weight:600}
:is(#v-tkall,.tk2-host) .tk2-who{flex:0 0 auto;max-width:84px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;color:var(--ink-2);background:var(--paper-2);border-radius:12px;padding:3px 9px}
:is(#v-tkall,.tk2-host) .tk2-acts{position:absolute;right:0;top:0;bottom:0;display:flex;visibility:hidden}
:is(#v-tkall,.tk2-host) .tk2-row.swiped .tk2-acts{visibility:visible}
:is(#v-tkall,.tk2-host) .tk2-act{width:84px;border:0;font-size:14px;font-weight:600;color:#fff;background:var(--ink-3);cursor:pointer}
:is(#v-tkall,.tk2-host) .tk2-act.hand{background:var(--accent)}
:is(#v-tkall,.tk2-host) .tk2-ghd{display:flex;align-items:center;gap:8px;padding:14px 12px 6px 16px;font-size:13px;font-weight:600;letter-spacing:.02em;color:var(--ink-2);border-bottom:1px solid var(--rule-2);background:none}
:is(#v-tkall,.tk2-host) .tk2-ghd.late{color:var(--bad,#b3261e)}
:is(#v-tkall,.tk2-host) .tk2-ghd .n{font-weight:500;color:var(--ink-3)}
#v-tkall .tk2-list{border:1px solid var(--rule);border-radius:10px;background:var(--paper);overflow:hidden}
:is(#v-tkall,.tk2-host) .tk2-empty{padding:18px 16px}
:is(#v-tkall,.tk2-host) .tk2-showall{margin:10px 16px 14px;min-height:44px}
#v-tkall .tk2-offer,.td-do .td-offer{display:flex;align-items:center;gap:10px;width:100%;min-height:48px;margin:0 0 10px;padding:8px 14px;border:1px solid var(--accent);border-radius:10px;background:var(--paper);font-size:15px;text-align:left;cursor:pointer}
#v-tkall .tk2-offer-n,.td-do .td-offer .tk2-offer-n{display:grid;place-items:center;min-width:26px;height:26px;border-radius:13px;background:var(--accent);color:#fff;font-weight:700;font-size:13px}
#v-tkall .tk2-offer b{color:var(--accent)}
#v-tkall .tk2-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 10px}
#v-tkall .tk2-bar .t2-q{min-width:200px}
#v-tkall .tk2-views{margin:0 0 10px}
#v-tkall .tk2-hline{display:flex;align-items:center;gap:8px;margin:0 0 10px}
#v-tkall .tk2-chip{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border:1px solid var(--rule);border-radius:22px;background:var(--paper);font-size:15px;font-weight:600;color:var(--ink);cursor:pointer;max-width:calc(100% - 60px);overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
#v-tkall .tk2-chip .n{background:var(--accent);color:#fff;border-radius:10px;padding:0 7px;font-size:12px;line-height:20px}
#v-tkall .tk2-ic{display:grid;place-items:center;width:44px;height:44px;border:1px solid var(--rule);border-radius:22px;background:var(--paper);color:var(--ink-2);cursor:pointer;flex:0 0 44px}
#v-tkall .tk2-q{flex:1 1 auto;min-width:0;height:44px;border:1px solid var(--rule);border-radius:22px;padding:0 16px;font-size:16px;background:var(--paper)}
#v-tkall .tk2-fab{position:fixed;right:16px;bottom:calc(76px + env(safe-area-inset-bottom));z-index:29;width:56px;height:56px;border-radius:50%;border:0;background:var(--accent);color:#fff;display:grid;place-items:center;box-shadow:0 6px 18px rgba(0,0,0,.22);cursor:pointer}
#v-tkall .t2-quick{padding:8px 12px;border-top:1px solid var(--rule-2)}
@media (max-width:760px){
  #v-tkall .tk2-ph{display:none}
  #v-tkall .tk2-list{border-radius:0;border-left:0;border-right:0;margin:0 -16px;padding-bottom:80px}
  #v-tkall .tk2-offer{width:100%}
  .td-do .td-tabs[role=tablist] > button{min-height:44px !important}
  .td-do .td-card .td-txt{cursor:pointer}
}
.tk2-host .tk2-list.tk2-inline{border:0;border-radius:0;margin:0 -2px;padding:0;overflow:hidden}
.tk2-host .tk2-hd{display:flex;align-items:center;gap:8px}
.tk2-host .tk2-hd .n{color:var(--ink-3);font-size:13px}
.tk2-host .tk2-more{display:flex;align-items:center;min-height:44px}
@media (max-width:760px){
  #trk-capture.tk2-capcompact .ph .lead,#trk-capture.tk2-capcompact>.hd,#trk-capture.tk2-capcompact>p{display:none}
  #trk-capture.tk2-capcompact .trk-big{width:100%}
  .tk2-sday button.gl{min-height:44px !important}
  .tk2-clock .fm-row{padding-top:8px;padding-bottom:8px}
  .tk2-clock .chk > input[type=checkbox],.tk2-clock input[type=checkbox]{-webkit-appearance:none;appearance:none;flex:0 0 44px;width:44px !important;height:44px !important;min-width:44px !important;min-height:44px !important;margin:0 8px 0 0;border:2px solid var(--ink-3);border-radius:10px;background:var(--paper) center/26px 26px no-repeat;cursor:pointer}
  .tk2-clock input[type=checkbox]:checked{border-color:var(--accent);background-color:var(--accent);background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 6L9 17l-5-5'/%3E%3C/svg%3E")}
}
#mbm.tks-on .mbm-box{max-width:620px}
#mbm.tks-on .mbm-hd h3{font-size:18px;line-height:24px;font-weight:600}
#mbm .tks-key{font-weight:800;color:var(--accent);letter-spacing:.02em;margin-right:4px}
.tks{display:flex;flex-direction:column;gap:6px}
.tks-lines{font-size:14px;color:var(--ink-2);line-height:20px}
.tks-lines .tk2-when.tk2-w-late{color:var(--bad,#b3261e);font-weight:600}
.tks-h{font-size:14px;font-weight:700;color:var(--ink-2);margin:12px 0 4px}
.tks-src{display:flex;align-items:center;gap:10px;width:100%;min-height:48px;padding:8px 12px;border:1px solid var(--rule);border-radius:10px;background:var(--paper-2);font-size:14px;text-align:left;cursor:pointer;margin:2px 0}
.tks-src b{color:var(--accent)}
.tks-hand{padding:10px 12px;border-radius:10px;background:var(--paper-2);font-size:14px}
.tks-hand.me{border:1px solid var(--accent)}
.tks-proof{padding:8px 12px;border-radius:10px;background:var(--warn-bg,#fff4e0);font-size:14px}
.tks-proof.ok{background:var(--ok-bg,#e8f5e9)}
.tks-chips,.tks-people,.tkf-row{display:flex;flex-wrap:wrap;gap:8px}
.tks-chip,.tks-person,.tkf-b{display:inline-flex;flex-direction:column;align-items:flex-start;justify-content:center;min-height:44px;min-width:44px;padding:4px 14px;border:1px solid var(--rule);border-radius:12px;background:var(--paper);font-size:15px;cursor:pointer;line-height:18px}
.tks-chip small,.tks-person small{font-size:12px;color:var(--ink-3)}
.tks-chip.on,.tkf-b.on{border-color:var(--accent);background:var(--accent-bg,#eaf1fb);font-weight:600}
.tkf-b{flex-direction:row;align-items:center;gap:6px}
.tkf-b .n{font-size:12px;color:var(--ink-3)}
.tkf-h{font-size:14px;font-weight:700;color:var(--ink-2);margin:12px 0 6px}
.tks-pick{position:relative;overflow:hidden}
.tks-pick input{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
.tks-row{display:flex;gap:8px;align-items:center;margin-top:6px}
.tks-row .btn{min-height:44px;flex:0 0 auto}
.tks-in{flex:1 1 auto;min-width:0;height:44px !important;font-size:16px !important;border:1px solid var(--rule);border-radius:10px;padding:0 12px}
.tks-handnote{width:100%;margin-top:8px}
.tks-steps{display:flex;flex-direction:column;gap:4px}
.tks-step{display:flex;align-items:center;gap:10px;min-height:44px;padding:4px 8px;border:0;border-bottom:1px solid var(--rule-2);background:none;text-align:left;font-size:15px;cursor:pointer}
.tks-box{flex:0 0 22px;width:22px;height:22px;border:2px solid var(--ink-3);border-radius:6px;box-sizing:border-box}
.tks-step.on .tks-box{background:var(--ok-2,#2e7d32);border-color:var(--ok-2,#2e7d32)}
.tks-step.on .grow{text-decoration:line-through;color:var(--ink-3)}
.tks-thread{display:flex;flex-direction:column;gap:8px}
.tks-note{padding:8px 10px;border-radius:10px;background:var(--paper-2);font-size:14px;line-height:20px}
.tks-note.was{opacity:.8}
.tks-img{display:block;max-width:100%;max-height:220px;border-radius:8px;margin-top:6px}
.tks-cam{width:44px;padding:0;display:grid;place-items:center}
.tks-hist summary{min-height:44px;display:flex;align-items:center;cursor:pointer;font-size:14px;color:var(--ink-2)}
.tks-hist ul{margin:0;padding-left:18px;font-size:13px;line-height:20px}
.tks-more{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.tks-more .btn{min-height:44px}
.tks-offers{display:flex;flex-direction:column;gap:8px}
.tks-handbtn{display:flex;align-items:center;gap:10px;width:100%;min-height:48px;margin-top:10px;padding:8px 12px;border:1px solid var(--rule);border-radius:10px;background:var(--paper);font-size:15px;font-weight:600;text-align:left;cursor:pointer}
.tks-handbtn small{font-weight:400;font-size:12px;color:var(--ink-3);max-width:55%;text-align:right}
.tks-handbox{margin-top:8px}
.tkh-say{margin:0 0 10px}
.tkh-people{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin:0 0 12px}
.tkh-p{display:flex;flex-direction:column;align-items:flex-start;justify-content:center;min-height:52px;padding:6px 12px;border:1px solid var(--rule);border-radius:12px;background:var(--paper);color:var(--ink);font:inherit;font-size:15px;text-align:left;cursor:pointer}
.tkh-p small{font-size:12px;color:var(--ink-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
.tkh-p.on{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset;background:var(--paper-2)}
.tkh-p.on b{color:var(--accent)}
#mbm.tkh-on .tkh-note{width:100%;height:44px;font-size:16px}
@media (max-width:760px){.tkh-people{grid-template-columns:1fr 1fr}}
.tks-handbox[hidden]{display:none}
@media (max-width:760px){
  #mbm.tks-on{align-items:flex-end;padding:0}
  #mbm.tks-on .mbm-box{border-radius:16px 16px 0 0;max-height:92vh;overflow:auto;max-width:none}
  #mbm.tks-on .mbm-ft{position:sticky;bottom:0;background:var(--paper);border-top:1px solid var(--rule-2);padding-bottom:calc(12px + env(safe-area-inset-bottom))}
  #mbm.tks-on .mbm-ft .btn{min-height:48px;flex:1 1 0}
  #mbm.tks-on .mbm-x{width:44px;height:44px}
}`;
  try {
    const s = document.createElement("style");
    (s.id = "tk2-css"), (s.textContent = css), document.head.appendChild(s);
  } catch (e) {}
})();
/*<</tasks.js>>*/
