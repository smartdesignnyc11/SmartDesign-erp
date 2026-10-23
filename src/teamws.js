/*<<teamws.js>>*/
/* ==== the team's own workspace, and the Asana board brought in once (lane D, 2026-10-23) ==============================
   docs/TASKS_PLAN.md §2 Phase 1, items 1 and 2. Alan, the coordinator and the office admin run Monday's meeting from the
   hosted app with their real projects and tasks.
   Design gate (BACKLOG §1.16). Nouns extended, nothing new where something exists:
     - the workspace: the hosted copy's own (profiles.workspace_id); the server now says its kind (demo or team) before
       the page boots (platform/supabase/schema.sql, my_workspace_info). A team workspace seeds nothing (sdSeedsOff),
       runs on the real date (the one clock: today(), appNow(); the Firm's Clock cannot pin it) and starts in the pilot.
     - the pilot: a setting on the company record (DB.company.pilot.tasksOnly), not a store. It narrows ROLE_VIEWS,
       the one list of what each role may open, so the menu, the phone's shortcuts, links and Ask all read the same
       list; the owner turns it off in Settings.
     - the task: Asana rows become the existing job to-dos (p.actions, read by tkItems and the one task sheet) with the
       fields lane A adds (key, prefix, owner, collaborators, waitingOn, followUp, watchUntil, status, order, comments,
       links). The project: the existing job record (blankProject), with project.prefix.
     - one new record, with its reason: DB.asanaImport keeps the import's runs and the rows still waiting for an
       internal owner. Those rows cannot be tasks yet (Alan, 10-23: no task without an internal owner), so they wait on
       the import's own screen (Your Own Data), never in a "General" project; it empties as owners are picked.
   Privacy: the export is read in the browser and written only to the workspace. Nothing of it is logged.
--------------------------------------------------------------------------------------------------------------------- */

// ---- the workspace ------------------------------------------------------------------------------------------------
// window.__sdWs is the server's answer ({id, kind, name, others}) on the hosted copy; DB.__teamWs marks the records of a
// team workspace (it travels in __meta, so every device and a reload know it even before the server answers).
function twsIsTeam() {
  try {
    return !!((window.__sdWs && "team" === window.__sdWs.kind) || (void 0 !== DB && DB && DB.__teamWs));
  } catch (e) {
    return !1;
  }
}
// What an empty team workspace starts from: no projects, no people (each person adds themself at sign-in, from their
// profile), the real date and the pilot on. load() fills the defaults (company terms, the first entity, settings).
function twsSkeleton(info) {
  const I = info || {};
  return {
    projects: [],
    currentId: "",
    users: [],
    clients: [],
    __liveData: 1,
    __teamWs: { id: I.id || "", name: I.name || "", at: tzNow() },
    company: { asOf: "", asOfManual: !1, pilot: { tasksOnly: !0, since: tzToday() } },
  };
}

// ---- the pilot: tasks, projects, people and contacts only ------------------------------------------------------------
// Pages that would show an empty money screen in the pilot (Alan, 10-23: money records follow later, with the live-jobs
// load and the server's field-privacy rule). They stay in the app, empty and unbroken; only the menu leaves them out.
const TWS_PILOT_HIDE = new Set([
  "billing", "ovmoney", "spend", "ap", "time", "bank", "verify", "budget", "gl", "reports", "costs", "dashboard", "mapprove",
  "ovbuy", "sel", "proc", "po", "rfq", "recv", "req", "route", "inv", "mat",
  "ovsales", "scleads", "hbdeals", "salesnum", "hbquotes", "hbforecast", "hbdash", "hbsequences", "hbworkspace",
  "hbplaybooks", "leads", "playbook", "partners", "hbsettings",
]);
const twsPilotHides = (v) => TWS_PILOT_HIDE.has(v) || /^mb/.test(v);
function twsPilotOn() {
  try {
    return !!(DB && DB.company && DB.company.pilot && DB.company.pilot.tasksOnly);
  } catch (e) {
    return !1;
  }
}
const TWS_RV_OFF = {};
// Narrow ROLE_VIEWS in place while the pilot is on; when it is off, give back only what the pilot took, at its place.
// Nothing else is touched, so a view another part of the app took out of a role's list stays out.
function twsPilotApply() {
  if ("object" != typeof ROLE_VIEWS) return;
  const on = twsPilotOn();
  Object.keys(ROLE_VIEWS).forEach((r) => {
    const L = ROLE_VIEWS[r];
    if (!Array.isArray(L)) return;
    const off = (TWS_RV_OFF[r] = TWS_RV_OFF[r] || []);
    if (on) {
      for (let i = L.length - 1; i >= 0; i--) twsPilotHides(L[i]) && (off.unshift([L[i], i]), L.splice(i, 1));
    } else if (off.length) {
      off.sort((a, b) => a[1] - b[1]).forEach(([v, i]) => L.includes(v) || L.splice(Math.min(i, L.length), 0, v));
      off.length = 0;
    }
  });
}
function twsPilotSet(on) {
  if ("owner" !== role()) return toast("Only the owner changes the pilot"), !1;
  (DB.company = DB.company || {}), (DB.company.pilot = Object.assign({}, DB.company.pilot || {}, { tasksOnly: !!on, at: appNowIso(), by: (currentUser() || {}).name || "" }));
  try {
    audit("company", "pilot", "tasksOnly", String(!on), String(!!on), "");
  } catch (e) {}
  twsPilotApply(), save(), render();
  toast(on ? "Pilot on: the menu shows tasks, projects, people and contacts" : "Pilot off: every page is back in the menu", () => ((view = "proj"), render()));
  return !0;
}
{
  const base = render;
  render = function () {
    let on = !1;
    try {
      twsPilotApply(), (on = twsPilotOn());
      // the investment arm's switch (SmartDesign | Mercer & Bond) is out of the pilot too
      on && "mb" === DB.workspace && (DB.workspace = "sd");
      document.body.classList.toggle("tws-pilot", on);
    } catch (e) {
      console.warn("pilot", e);
    }
    return base.apply(this, arguments);
  };
  const st = document.createElement("style");
  (st.textContent = "body.tws-pilot #ws{display:none!important}"), document.head.appendChild(st);
}

// ---- the real clock: a team workspace is never pinned -----------------------------------------------------------------
{
  const base = appSetDay;
  appSetDay = function (day) {
    if (twsIsTeam() && day) throw new Error("appSetDay: the team's workspace runs on the real date");
    return base.apply(this, arguments);
  };
}
{
  const base = iaOneClock;
  iaOneClock = function () {
    try {
      twsIsTeam() && DB && DB.company && (DB.company.asOf || DB.company.asOfManual) && ((DB.company.asOf = ""), (DB.company.asOfManual = !1));
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
// The Firm's Clock card: no As Of field on a team workspace, a sentence instead.
{
  const base = renderProj;
  renderProj = function () {
    const r = base.apply(this, arguments);
    try {
      const f = twsIsTeam() && document.getElementById("asof-date");
      if (f) {
        const box = f.closest(".f");
        box && (box.innerHTML = `<label>As Of</label><div class="small muted">Today, always: the team's workspace runs on the real date.</div>`);
      }
    } catch (e) {}
    return r;
  };
}

// ---- Settings: the workspace card (owner: the pilot, opening the team workspace, switching) -----------------------------
function twsCardHtml() {
  const I = window.__sdWs || null,
    team = twsIsTeam(),
    owner = "owner" === role(),
    others = (I && I.others) || [],
    pilot = twsPilotOn();
  const name = (I && I.name) || (DB.__teamWs && DB.__teamWs.name) || "";
  return `<h3>Workspace</h3>
    <p class="small muted" style="margin:0 0 8px">${team ? `${esc(name || "The team's workspace")}: the team's own projects, tasks, people and contacts. No sample data, and every date is today's.` : `${esc(name || "This workspace")} holds the sample company and reads as of the demo's day.`}</p>
    ${team ? `<label class="row" style="gap:8px;min-height:44px"><input type="checkbox" id="tws-pilot" ${pilot ? "checked" : ""} ${owner ? "" : "disabled"}><span><b>Pilot: Tasks Only</b><br><span class="small muted">The menu shows tasks, projects, people and contacts. The money pages stay out of it until the money records come in.${owner ? "" : " The owner changes this."}</span></span></label>` : ""}
    ${others.length ? `<div class="row" style="gap:8px;flex-wrap:wrap;margin-top:8px">${others.map((o) => `<button class="btn" data-twsgo="${esc(o.id)}">${"team" === o.kind ? `Switch to ${esc(o.name || "the Team's Workspace")}` : "Switch to the Demo"}</button>`).join("")}</div><p class="small muted" style="margin:6px 0 0">Switching reloads the app on this device with that workspace's records.</p>` : ""}
    ${owner && !team && I ? `<div class="row" style="gap:8px;margin-top:10px;flex-wrap:wrap"><button class="btn" id="tws-open">Open the Team's Workspace</button></div><p class="small muted" style="margin:6px 0 0">A new, empty workspace for the team's real work. You move into it and can switch back here at any time.</p>` : ""}`;
}
function twsCard() {
  if (document.getElementById("tws-card")) return;
  const anchor = document.getElementById("cl-team");
  if (!anchor) return;
  const card = document.createElement("div");
  (card.className = "card"), (card.id = "tws-card"), (card.style.marginTop = "12px"), (card.innerHTML = twsCardHtml()), anchor.after(card);
  const pv = card.querySelector("#tws-pilot");
  pv && (pv.onchange = () => (twsPilotSet(pv.checked) || (pv.checked = !pv.checked), card.remove(), twsCard()));
  card.querySelectorAll("[data-twsgo]").forEach(
    (b) =>
      (b.onclick = async () => {
        b.disabled = !0;
        try {
          await persist();
        } catch (e) {}
        try {
          await Cloud.switchWorkspace(b.dataset.twsgo), location.reload();
        } catch (e) {
          (b.disabled = !1), toast(e.message || "Could not switch");
        }
      }),
  );
  const op = card.querySelector("#tws-open");
  op &&
    (op.onclick = () =>
      mbModal(
        "Open the Team's Workspace",
        `<p class="small">A new workspace with no sample data: the team's own projects and tasks, on today's date, with the pilot's tasks-only menu. Nothing moves out of this one, and you can switch back from Settings.</p><div class="f"><label>Name</label><input data-f="name" value="SmartDesign"></div><div class="f"><label>Short ID</label><input data-f="id" value="sd-team" autocapitalize="off"><span class="hint">Lowercase letters, digits and dashes.</span></div>`,
        {
          submit: "Open It",
          onSubmit: (f) => {
            Cloud.openTeamWorkspace(f.id, f.name)
              .then(() => location.reload())
              .catch((e) => toast(e.message || "Could not open it"));
          },
        },
      ));
}
// Team Accounts in the team's workspace: an invitation names the person, and a person new to the app is added to its
// people with that name and role, so their tasks can be theirs before they first sign in.
function twsInviteWire() {
  const card = document.getElementById("cl-team"),
    inv = card && card.querySelector("#cl-inv-go");
  if (!inv || inv.dataset.tws) return;
  inv.dataset.tws = "1";
  const sel = card.querySelector("#cl-inv-user");
  if (sel && !card.querySelector("#cl-inv-name")) {
    const f = document.createElement("div");
    (f.className = "f"), (f.innerHTML = '<label>Name</label><input id="cl-inv-name" autocomplete="off" placeholder="First and last name">');
    sel.closest(".f").before(f);
    sel.options[0] && (sel.options[0].textContent = "New person in the app");
  }
  inv.onclick = () => {
    const email = (card.querySelector("#cl-inv-email").value || "").trim().toLowerCase(),
      rl = card.querySelector("#cl-inv-role").value,
      name = ((card.querySelector("#cl-inv-name") || {}).value || "").trim();
    if (!email) return toast("Type their email first");
    let uidv = (sel && sel.value) || "";
    if (!uidv) {
      if (!name) return toast("Type their name, or pick the person in the app");
      let u = (DB.users || []).find((x) => String(x.contact || "").toLowerCase() === email);
      u || ((u = { id: uid("u"), name: name, role: rl, contact: email }), DB.users.push(u), save());
      uidv = u.id;
    }
    inv.disabled = !0;
    Cloud.invite({ email: email, role: rl, appUserId: uidv, name: name })
      .then((r) => {
        toast(
          r.invited ? `Invitation sent to ${r.email}` : r.moved ? `${r.email} is now in this workspace as ${ROLE_NAMES[r.role] || r.role}` : `${r.email} already had an account: role set to ${ROLE_NAMES[r.role] || r.role}`,
          () => ((view = "proj"), render()),
        );
        card.remove(), cloudSettingsCard();
      })
      .catch((e) => toast(e.message))
      .finally(() => (inv.disabled = !1));
  };
}
{
  const base = cloudSettingsCard;
  cloudSettingsCard = function () {
    const r = base.apply(this, arguments);
    try {
      twsInviteWire(), twsCard();
    } catch (e) {
      console.warn("workspace card", e);
    }
    return r;
  };
}

// ---- the Asana import ---------------------------------------------------------------------------------------------
// Asana's CSV export (each project's menu › Export › CSV): Task ID, Created At, Completed At, Last Modified, Name,
// Section/Column, Assignee, Assignee Email, Start Date, Due Date, Tags, Notes, Projects, Parent task, Blocked By
// (Dependencies), Blocking (Dependencies), then one column per custom field.
const AIM_COLS = {
  id: /^task id$/i,
  created: /^created at$/i,
  completed: /^completed at$/i,
  modified: /^last modified$/i,
  name: /^name$/i,
  section: /^section\/column$|^section$/i,
  assignee: /^assignee$/i,
  email: /^assignee email$/i,
  start: /^start date$/i,
  due: /^due date$/i,
  tags: /^tags$/i,
  notes: /^notes$/i,
  projects: /^projects$/i,
  parent: /^parent task$/i,
  blockedBy: /^blocked by/i,
  blocking: /^blocking/i,
  // the team board's own custom field: the job a row is about (rows without one are the firm's own lists)
  projectName: /^project name$/i,
};
const AIM_KEY = /^\s*\[?([A-Z][A-Z0-9]{0,7})-(\d{1,5})\]?(?:[\s:.\u2013\u2014-]+|$)/;
// RFC 4180: quoted fields, doubled quotes, line breaks inside quotes, a byte-order mark, CRLF or LF. A column name used
// twice (the team board's custom "Task ID" beside Asana's own) is kept as "Task ID (2)", so neither is lost.
function aimParseCsv(text) {
  const s = String(text || "").replace(/^\uFEFF/, ""),
    rows = [];
  let row = [],
    f = "",
    q = !1;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (q) {
      if ('"' === c) {
        if ('"' === s[i + 1]) (f += '"'), i++;
        else q = !1;
      } else f += c;
    } else if ('"' === c) q = !0;
    else if ("," === c) row.push(f), (f = "");
    else if ("\n" === c || "\r" === c) {
      "\r" === c && "\n" === s[i + 1] && i++;
      row.push(f), rows.push(row), (row = []), (f = "");
    } else f += c;
  }
  (f || row.length) && (row.push(f), rows.push(row));
  const out = rows.filter((r) => r.some((x) => String(x).trim()));
  if (!out.length) return { header: [], rows: [] };
  const seen = {},
    header = out[0].map((h) => {
      const t = String(h).trim(),
        k = t.toLowerCase();
      return (seen[k] = (seen[k] || 0) + 1), seen[k] > 1 ? `${t} (${seen[k]})` : t;
    });
  return { header: header, rows: out.slice(1).map((r) => header.reduce((o, h, i) => ((o[h] = String(null == r[i] ? "" : r[i])), o), {})) };
}
function aimDate(v) {
  const t = String(v || "").trim();
  let m = /^(\d{4})-(\d{2})-(\d{2})/.exec(t);
  if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})/.exec(t);
  return m ? `${m[3]}-${String(m[1]).padStart(2, "0")}-${String(m[2]).padStart(2, "0")}` : "";
}
const aimSplit = (v) =>
  String(v || "")
    .split(/\s*,\s*/)
    .map((x) => x.trim())
    .filter(Boolean);
// One file's rows in the import's own shape, with the custom fields kept by their column names.
function aimReadFile(file) {
  const P = aimParseCsv(file.text),
    col = {};
  P.header.forEach((h) => {
    for (const [k, re] of Object.entries(AIM_COLS)) if (re.test(h) && !col[k]) return void (col[k] = h);
  });
  if (!col.id || !col.name) return { error: `${file.name || "That file"} is not an Asana export: it has no Task ID and Name columns`, rows: [] };
  const known = new Set(Object.values(col));
  return {
    board: !!col.projectName,
    rows: P.rows.map((r, i) => {
      const g = (k) => (col[k] ? String(r[col[k]] || "").trim() : ""),
        custom = {};
      P.header.forEach((h) => {
        !known.has(h) && String(r[h] || "").trim() && (custom[h] = String(r[h]).trim());
      });
      return {
        file: file.name || "",
        line: i + 2,
        id: g("id"),
        created: aimDate(g("created")),
        completed: aimDate(g("completed")),
        modified: aimDate(g("modified")),
        name: g("name"),
        section: g("section"),
        assignee: g("assignee"),
        email: g("email").toLowerCase(),
        start: aimDate(g("start")),
        due: aimDate(g("due")),
        tags: aimSplit(g("tags")),
        notes: col.notes ? String(r[col.notes] || "").trim() : "",
        projects: aimSplit(g("projects")),
        parent: g("parent"),
        blockedBy: aimSplit(g("blockedBy")),
        blocking: aimSplit(g("blocking")),
        boardFile: !!col.projectName,
        projectName: g("projectName"),
        custom: custom,
      };
    }),
  };
}
// The team's people who can own a task: users of the app, never a client.
function aimPeople() {
  return (DB.users || []).filter((u) => u && u.id && "client" !== u.role && !/^mb_/.test(u.role || ""));
}
// A team member by their Asana email, else the way the task record reads a name (tkInternal: a full name, a first name
// only one person carries, a role word); only a person who signs in owns a task.
function aimPersonOf(name, email) {
  const U = aimPeople(),
    e = String(email || "").toLowerCase();
  if (e) {
    const u = U.find((x) => String(x.contact || x.email || "").toLowerCase() === e);
    if (u) return u;
  }
  const n = String(name || "").trim();
  if (!n) return null;
  let hit = null;
  try {
    const t = "function" == typeof tkInternal ? tkInternal(n) : null;
    hit = t && t.id ? U.find((u) => u.id === t.id) || null : null;
  } catch (e2) {}
  if (hit) return hit;
  const low = n.toLowerCase(),
    full = U.filter((x) => String(x.name || "").trim().toLowerCase() === low);
  if (1 === full.length) return full[0];
  const f = low.split(/\s+/)[0],
    first = U.filter((x) => String(x.name || "").trim().toLowerCase().split(/\s+/)[0] === f);
  return !full.length && 1 === first.length && low === f ? first[0] : null;
}
// Someone outside the team, found among the contacts the app already holds (by email first, then as the task record
// finds them: tkContactRef).
function aimContactOf(name, email) {
  const e = String(email || "").toLowerCase();
  if (e) {
    const v = (DB.vendors || []).find((x) => x && String(x.email || "").toLowerCase() === e);
    if (v) return { kind: "vendor", id: v.id, name: name || v.name };
  }
  let ref = null;
  try {
    ref = "function" == typeof tkContactRef ? tkContactRef(name) : null;
  } catch (e2) {}
  return ref ? Object.assign({ name: name }, ref) : null;
}
function aimPrefixFromName(name, taken) {
  const t = String(name || "").trim(),
    lead = /^\[?([A-Z][A-Z0-9]{1,5})\]?(?:\s*[-:\u2013\u2014]\s*|\s+)/.exec(t);
  let p = lead ? lead[1] : "";
  if (!p) {
    const words = t
      .replace(/[^A-Za-z0-9 ]+/g, " ")
      .split(/\s+/)
      .filter((w) => w && !/^(the|and|of|at|on|for|a|an)$/i.test(w));
    p = (words.length > 1 ? words.map((w) => w[0]).join("") : (words[0] || "PRJ").slice(0, 3)).toUpperCase().slice(0, 4);
    /^[A-Z]/.test(p) || (p = "P" + p);
  }
  let out = p,
    i = 2;
  for (; taken.has(out); ) out = p + i++;
  return out;
}
// Every task on every board (a job's to-dos, the firm's own lists, Sales), by Asana id and by code.
function aimRecs() {
  if ("function" == typeof tkKeyedRecs) return tkKeyedRecs();
  const out = [];
  (DB.projects || []).forEach((p) => (p.actions || []).forEach((a) => a && out.push({ kind: "action", rec: a, p: p, board: "p:" + p.id })));
  return out;
}
function aimIndex() {
  const byAsana = new Map(),
    codes = new Map();
  aimRecs().forEach((r) => {
    const a = r.rec;
    a && a.asana && a.asana.id && byAsana.set(String(a.asana.id), { a: a, p: r.p, board: r.board });
    a && a.code && codes.set(String(a.code).toUpperCase(), { a: a, p: r.p, board: r.board });
  });
  return { byAsana: byAsana, codes: codes };
}
// A board's meta (its prefix and next number): a job's own project record, or the firm's map for its own lists.
function aimMeta(board) {
  if ("function" == typeof tkBoardMeta) return tkBoardMeta(board);
  const p = /^p:/.test(board) ? (DB.projects || []).find((q) => "p:" + q.id === board) : null;
  return p ? p.project : null;
}
function aimPrefixesTaken() {
  const S = new Set();
  (DB.projects || []).forEach((p) => p.project && p.project.prefix && S.add(p.project.prefix));
  Object.values((DB.company && DB.company.tkBoards) || {}).forEach((m) => m && m.prefix && S.add(m.prefix));
  return S;
}
// The job a project name means: the one an earlier import made for it, the same name or address (one job known by
// two names is matched by the same rule the board import used: asProjectFor), or the board's prefix.
function aimJobFor(name, prefix) {
  const low = String(name || "").toLowerCase();
  let p =
    (DB.projects || []).find((q) => q.project && String(q.project.asanaName || "").toLowerCase() === low) ||
    (DB.projects || []).find((q) => q.project && String(q.project.name || "").trim().toLowerCase() === low) ||
    null;
  if (!p)
    try {
      const h = "function" == typeof asProjectFor ? asProjectFor({ projectName: name }) : null;
      h && !h.__property && (p = h);
    } catch (e) {}
  return p || (prefix && (DB.projects || []).find((q) => q.project && q.project.prefix === prefix)) || null;
}
// The dry run: what the files would do, and nothing written. files: [{name, text}]. opts.prefix: {project name: prefix}
// the person typed over the suggested ones.
// Where a row goes: a per-project export's rows go to that project (a job here); the team board's export names the job
// in PROJECT NAME, and a row without one is on one of the firm's own lists (its section: Operations, Finance & Admin).
function aimPlan(files, opts) {
  const O = opts || {},
    errors = [],
    raw = [];
  (files || []).forEach((f) => {
    const r = aimReadFile(f);
    r.error ? errors.push(r.error) : raw.push(...r.rows);
  });
  // a task in two projects comes in each project's export: the copy kept is the one from its own project's file, so
  // its place in that project's order is the board's
  const seen = new Map(),
    rows = [],
    dup = [],
    main = {};
  raw.forEach((r) => r.projects[0] && ((main[r.file] = main[r.file] || {})[r.projects[0]] = (main[r.file][r.projects[0]] || 0) + 1));
  const home = (r) => {
    const m = main[r.file] || {},
      top1 = Object.keys(m).sort((a, b) => m[b] - m[a])[0];
    return !r.projects[0] || r.projects[0] === top1;
  };
  raw.forEach((r) => {
    if (!r.id) return void rows.push(r);
    const was = seen.get(r.id);
    if (!was) return seen.set(r.id, r), void rows.push(r);
    if (!home(was) && home(r)) return rows.splice(rows.indexOf(was), 1), rows.push(r), seen.set(r.id, r), void dup.push(was);
    dup.push(r);
  });
  const idx = aimIndex(),
    top = rows.filter((r) => !r.parent),
    subs = rows.filter((r) => r.parent);
  const fileProj = {};
  top.forEach((r) => !r.boardFile && r.projects[0] && ((fileProj[r.file] = fileProj[r.file] || new Set()).add(r.projects[0])));
  top.forEach((r) => {
    if (r.boardFile) (r.project = r.projectName || r.section || "Office"), (r.firm = !r.projectName);
    else (r.project = r.projects[0] || (fileProj[r.file] && 1 === fileProj[r.file].size ? [...fileProj[r.file]][0] : "")), (r.firm = !1);
    // the ID the row already carries: in its name ("PAD-23 Order tile"), or a custom field that holds only an ID
    const m = AIM_KEY.exec(r.name);
    (r.keyFound = ""), (r.title = r.name);
    if (m) (r.keyFound = `${m[1]}-${+m[2]}`), (r.title = r.name.slice(m[0].length).trim() || r.name);
    else
      for (const v of Object.values(r.custom)) {
        const c = /^\s*\[?([A-Z][A-Z0-9]{0,7})-(\d{1,5})\]?\s*$/.exec(v);
        if (c) {
          r.keyFound = `${c[1]}-${+c[2]}`;
          break;
        }
      }
  });
  // the boards: a job matched here or new, or one of the firm's own lists
  const taken = aimPrefixesTaken(),
    projects = new Map();
  top.forEach((r) => {
    if (!r.project || projects.has(r.project)) return;
    const name = r.project,
      keysIn = top.filter((x) => x.project === name && x.keyFound).map((x) => x.keyFound.split("-")[0]),
      common = keysIn.length ? Object.entries(keysIn.reduce((m, k) => ((m[k] = (m[k] || 0) + 1), m), {})).sort((a, b) => b[1] - a[1])[0][0] : "",
      typed = O.prefix && O.prefix[name] ? String(O.prefix[name]).toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8) : "";
    let p = null,
      board = "";
    if (r.firm) board = "s:" + name;
    else (p = aimJobFor(name, typed || common)), (board = p ? "p:" + p.id : "");
    const meta = board ? aimMeta(board) : null,
      had = (r.firm && (((DB.company || {}).tkBoards || {})[board] || {}).prefix) || (p && p.project && p.project.prefix) || "";
    const prefix = typed || (meta && meta.prefixSet && had) || common || had || aimPrefixFromName(name, taken);
    taken.add(prefix);
    projects.set(name, { name: name, prefix: prefix, typed: !!typed, firm: !!r.firm, board: board, projectId: p ? p.id : "", existing: !!(p || had), create: 0, update: 0, same: 0, done: 0, review: 0, flag: 0, sub: 0 });
  });
  // codes: the one the row carries, else the next number on its board in the export's order; never one already used
  const used = new Map([...idx.codes].map(([k, x]) => [k, x.a.asana && x.a.asana.id ? String(x.a.asana.id) : "app:" + x.a.id])),
    next = {},
    num = (P) => {
      const prefix = P.prefix;
      if (!(prefix in next)) {
        let m = 0;
        used.forEach((v, k) => {
          const x = /^([A-Z0-9]+)-(\d+)$/.exec(k);
          x && x[1] === prefix && (m = Math.max(m, +x[2]));
        });
        top.forEach((r) => {
          const x = /^([A-Z0-9]+)-(\d+)$/.exec(r.keyFound || "");
          x && x[1] === prefix && (m = Math.max(m, +x[2]));
        });
        const meta = P.board ? aimMeta(P.board) : null;
        next[prefix] = Math.max(m + 1, (meta && meta.prefix === prefix && +meta.keyNext) || 1);
      }
      return `${prefix}-${next[prefix]++}`;
    };
  const tasks = [],
    review = [],
    people = {},
    tell = (nm) => (people[nm] = people[nm] || { name: nm, owner: 0, waitingOn: 0, flag: 0 }),
    order = {};
  top.forEach((r) => {
    const P = projects.get(r.project),
      ex = (r.id && idx.byAsana.get(r.id)) || (r.keyFound && idx.codes.get(r.keyFound.toUpperCase())) || null;
    const owner = aimPersonOf(r.assignee, r.email),
      outside = !owner && r.assignee && !/^(the (group|team|crew)|crew|all|tbd)$/i.test(r.assignee) ? aimContactOf(r.assignee, r.email) || { kind: "", id: "", name: r.assignee } : null;
    const t = {
      asanaId: r.id,
      row: r,
      project: r.project,
      firm: !!(P && P.firm),
      code: (ex && ex.a.code) || r.keyFound,
      title: r.title,
      section: r.section,
      order: 0,
      ownerName: owner ? owner.name : "",
      flag: null,
      waitingOn: outside,
      done: !!r.completed,
      completedAt: r.completed,
      checklist: [],
      exists: !!ex,
    };
    if (!P) return (t.why = "The row names no project: add it to its project in Asana and export again"), review.push(t), void (tell(r.assignee || "Nobody").flag += 0);
    t.order = order[r.project] = (order[r.project] || 0) + 1;
    if (t.code) {
      const holder = used.get(t.code.toUpperCase());
      holder && holder !== (r.id || "") && !(ex && ex.a.code === t.code) && ((t.keyWas = t.code), (t.code = ""));
    }
    t.code || (t.code = num(P));
    used.set(t.code.toUpperCase(), r.id || t.code);
    // Every task has one team member who makes sure it gets done (Alan, 10-23). Someone outside the team, or nobody,
    // gives the board's lead the task, flagged for the meeting to confirm (the task record's ownerFlag); the outsider
    // is Waiting On. A task already here keeps the owner it has.
    if (!t.ownerName && ex && ex.a.assignee) t.ownerName = ex.a.assignee;
    if (!t.ownerName) {
      let lead = { name: "" };
      try {
        lead = tdyLeadOf({ kind: P.firm ? "firm" : "action", projectId: P.projectId || "", area: "" }) || lead;
      } catch (e) {}
      if (!lead.name) return (t.why = "No team member to own it: pick one"), review.push(t), void P.review++;
      (t.ownerName = lead.name), (t.flag = { was: r.assignee || "", why: outside ? "outside" : "none", to: lead.name, at: today() }), P.flag++, tell(r.assignee || "Nobody").flag++;
    }
    tell(t.ownerName).owner++;
    outside && tell(outside.name).waitingOn++;
    tasks.push(t), t.exists ? (aimChanged(ex.a, t) ? P.update++ : P.same++) : P.create++, t.done && P.done++;
  });
  // subtasks: checklist steps on their parent (by the parent's name, in the same export first)
  const all = tasks.concat(review),
    orphans = [];
  subs.forEach((r) => {
    const par = all.find((t) => t.row.name === r.parent && t.row.file === r.file) || all.find((t) => t.row.name === r.parent);
    if (!par) return void orphans.push(r);
    const who = r.assignee ? ` (${r.assignee}${r.due ? ", " + r.due : ""})` : r.due ? ` (${r.due})` : "";
    par.checklist.push({ t: r.name + who, done: !!r.completed, by: "Asana", at: r.completed || r.created || "", asanaId: r.id });
    projects.get(par.project) && projects.get(par.project).sub++;
  });
  const P = [...projects.values()];
  return {
    errors: errors,
    rows: raw.length,
    duplicates: dup.length,
    projects: P,
    people: Object.values(people).filter((x) => x.owner || x.waitingOn || x.flag).sort((a, b) => b.owner + b.waitingOn - (a.owner + a.waitingOn)),
    tasks: tasks,
    review: review,
    orphans: orphans,
    totals: {
      rows: raw.length,
      tasks: tasks.length,
      create: P.reduce((a, x) => a + x.create, 0),
      update: P.reduce((a, x) => a + x.update, 0),
      same: P.reduce((a, x) => a + x.same, 0),
      done: tasks.filter((t) => t.done).length,
      flagged: tasks.filter((t) => t.flag).length,
      steps: subs.length - orphans.length,
      review: review.length,
      orphans: orphans.length,
      duplicates: dup.length,
      newProjects: P.filter((x) => !x.existing && !x.firm).length,
    },
  };
}
// What one import writes on the task, kept so a later import can tell the app's own edits from Asana's.
function aimSnap(t) {
  return { title: t.title, due: t.row.due, start: t.row.start, section: t.section, done: t.done, owner: t.ownerName, notes: t.row.notes };
}
function aimChanged(a, t) {
  const s = (a.asana && a.asana.snap) || {},
    n = aimSnap(t);
  if (!a.asana) return !0; // a task an earlier import made without Asana's id: brought under this import once
  return Object.keys(n).some((k) => "owner" !== k && String(s[k] == null ? "" : s[k]) !== String(n[k] == null ? "" : n[k])) || (t.checklist || []).some((c) => !(a.checklist || []).some((x) => x.asanaId && x.asanaId === c.asanaId));
}
function aimStatus(t) {
  if (t.done) return "done";
  if (t.waitingOn) return "waiting";
  const s = String(t.section || "");
  return /waiting|blocked/i.test(s) ? "waiting" : /\bfyi\b|info only|for info/i.test(s) ? "fyi" : /doing|in progress|underway|working/i.test(s) ? "doing" : "todo";
}
// The board a planned project lands on: a job (found again, or made), or one of the firm's own lists.
function aimBoard(P, now) {
  if (P.firm) {
    const id = "s:" + P.name,
      meta = aimMeta(id);
    meta && (meta.prefix || (meta.prefix = P.prefix), P.typed && ((meta.prefix = P.prefix), (meta.prefixSet = 1)));
    return { list: asFirmTasks(), p: null, section: P.name, board: id };
  }
  let p = (P.projectId && (DB.projects || []).find((q) => q.id === P.projectId)) || aimJobFor(P.name, P.prefix);
  if (!p) {
    (p = blankProject(P.name, "", today(), "")), (p.project.today = ""), (p.project.asanaName = P.name), (p.project.prefix = P.prefix);
    p.log = [{ t: nowStamp(), ts: now, msg: `Project created by the Asana import, prefix ${P.prefix}.`, by: (currentUser() || {}).name || "", src: "import" }];
    DB.projects.push(p);
  }
  (P.projectId = p.id), (P.existing = !0);
  p.project.prefix || (p.project.prefix = P.prefix);
  P.typed && ((p.project.prefix = P.prefix), (p.project.prefixSet = 1));
  p.project.asanaName || (p.project.asanaName = P.name);
  return { list: (p.actions = p.actions || []), p: p, section: "", board: "p:" + p.id };
}
// Write one planned task (new, or an update that keeps the app's own edits).
function aimWrite(t, plan, now, ownerName) {
  const P = plan.projects.find((x) => x.name === t.project);
  if (!P) return null;
  const who = ownerName || t.ownerName;
  if (!who) return null;
  const B = aimBoard(P, now),
    me = currentUser() || {},
    idx = aimIndex(),
    ex = (t.asanaId && idx.byAsana.get(t.asanaId)) || (t.code && idx.codes.get(String(t.code).toUpperCase())) || null,
    note = t.row.notes ? { id: "asn_" + (t.asanaId || uid("n")), at: (t.row.created || today()) + "T09:00:00", by: "Asana", text: t.row.notes, ev: "notes", source: "asana" } : null,
    wo = t.waitingOn ? { name: t.waitingOn.name, contactRef: t.waitingOn.id ? { kind: t.waitingOn.kind, id: t.waitingOn.id } : null, what: t.title, promised: t.row.due || "", evidence: "Assigned to them in Asana" } : null,
    snap = aimSnap(Object.assign({}, t, { ownerName: who }));
  if (ex) {
    const a = ex.a,
      s = (a.asana && a.asana.snap) || {},
      put = (k, field, v) => {
        !a.asana || String(a[field] == null ? "" : a[field]) === String(s[k] == null ? "" : s[k]) || (null == s[k] && !a[field]) ? (a[field] = v) : 0;
      };
    put("title", "title", snap.title), put("due", "due", snap.due), put("start", "start", snap.start), B.p && put("section", "section", snap.section);
    s.done !== snap.done && ("done" === a.status) === !!s.done && ((a.status = snap.done ? "done" : aimStatus(t)), (a.completedAt = snap.done ? t.completedAt || today() : ""));
    if (note && snap.notes !== s.notes && !(a.thread || []).some((c) => c && c.text && c.text.endsWith(note.text))) {
      const c = Object.assign({}, note, { id: note.id + "_" + (t.row.modified || today()), text: a.asana ? "Notes in Asana now read: " + note.text : note.text });
      (a.thread = a.thread || []).push(c);
    }
    (t.checklist || []).forEach((c) => {
      const was = (a.checklist = a.checklist || []).find((x) => x.asanaId && x.asanaId === c.asanaId);
      was ? (was.done = was.done || c.done) : a.checklist.push(c);
    });
    a.assignee || (a.assignee = who);
    a.code || (a.code = t.code);
    a.asana = Object.assign({}, a.asana, { id: t.asanaId || "", lastModified: t.row.modified, importedAt: now, snap: snap });
    return { a: a, p: ex.p, created: !1 };
  }
  const a = {
    id: uid("a"),
    code: t.code,
    title: t.title,
    assignee: who,
    collaborators: [],
    waitingOn: wo,
    waitsOn: wo ? wo.name : "",
    status: aimStatus(t),
    due: t.row.due || "",
    start: t.row.start || "",
    followUp: "",
    watchUntil: "",
    order: t.order,
    section: B.section || t.section || "",
    priority: "med",
    notes: "",
    thread: note ? [note] : [],
    checklist: t.checklist || [],
    tags: t.row.tags || [],
    links: [],
    blockedBy: t.row.blockedBy || [],
    blocking: t.row.blocking || [],
    custom: Object.keys(t.row.custom || {}).length ? t.row.custom : null,
    createdAt: t.row.created || today(),
    createdBy: "Asana import",
    importedBy: me.name || "",
    completedAt: t.done ? t.completedAt || today() : "",
    modifiedAt: t.row.modified || "",
    source: { kind: "asana", asana: !0, id: t.asanaId || "" },
    asana: { id: t.asanaId || "", project: t.project, keyWas: t.keyWas || "", lastModified: t.row.modified, importedAt: now, snap: snap },
  };
  t.keyWas && (a.keyWas = [t.keyWas]);
  t.flag && !ownerName && (a.ownerFlag = Object.assign({}, t.flag));
  return B.list.push(a), { a: a, p: B.p, created: !0 };
}
function aimStore() {
  return (DB.asanaImport = DB.asanaImport || { runs: [], pending: [] }), (DB.asanaImport.runs = DB.asanaImport.runs || []), (DB.asanaImport.pending = DB.asanaImport.pending || []), DB.asanaImport;
}
// Write the plan. owners: {asana id: a team member's name} for rows on the review list. Rows still without a board or
// an owner wait on the review list.
function aimApply(plan, owners) {
  const W = owners || {},
    now = appNowIso(),
    S = aimStore(),
    out = { created: 0, updated: 0, same: 0, flagged: 0, waiting: 0, projects: 0, steps: 0 },
    before = (DB.projects || []).length;
  plan.tasks.forEach((t) => {
    const I = aimIndex(),
      was = (t.asanaId && I.byAsana.get(t.asanaId)) || (t.code && I.codes.get(String(t.code).toUpperCase())) || null,
      changed = was ? aimChanged(was.a, t) : !0,
      r = aimWrite(t, plan, now);
    r && (r.created ? (out.created++, t.flag && out.flagged++) : changed ? out.updated++ : out.same++), r && (out.steps += (t.checklist || []).length);
  });
  const left = [];
  plan.review.forEach((t) => {
    const o = W[t.asanaId];
    if (o && t.project) {
      const r = aimWrite(t, plan, now, aimOwnerName(o));
      if (r) return r.created ? out.created++ : out.updated++, void (out.steps += (t.checklist || []).length);
    }
    left.push(t);
  });
  // what still waits: kept by Asana id, so a second import replaces it instead of adding it twice
  const I2 = aimIndex(),
    keep = S.pending.filter((x) => !left.some((t) => t.asanaId && t.asanaId === x.asanaId) && !I2.byAsana.has(x.asanaId));
  S.pending = keep.concat(left.map((t) => ({ asanaId: t.asanaId, project: t.project, code: t.code, title: t.title, why: t.why, done: t.done, t: JSON.parse(JSON.stringify(t)), projects: JSON.parse(JSON.stringify(plan.projects.filter((x) => x.name === t.project))) })));
  out.waiting = S.pending.length;
  out.projects = (DB.projects || []).length - before;
  S.runs.push({ at: now, by: (currentUser() || {}).name || "", files: [...new Set(plan.tasks.concat(plan.review).map((t) => t.row.file))], rows: plan.totals.rows, created: out.created, updated: out.updated, same: out.same, flagged: out.flagged, waiting: out.waiting, steps: out.steps, projects: out.projects });
  try {
    "function" == typeof tkRecSweep && tkRecSweep();
  } catch (e) {}
  save();
  return out;
}
const aimOwnerName = (v) => ((DB.users || []).find((u) => u.id === v || u.name === v) || {}).name || "";
// A row from the review list gets its owner and becomes a task.
function aimResolve(asanaId, owner) {
  const S = aimStore(),
    x = S.pending.find((y) => y.asanaId === asanaId),
    who = aimOwnerName(owner);
  if (!x || !who || !x.projects.length) return null;
  const r = aimWrite(x.t, { projects: x.projects }, appNowIso(), who);
  return r && ((S.pending = S.pending.filter((y) => y !== x)), save()), r;
}

// ---- the screen: on Your Own Data (owner) ----------------------------------------------------------------------------
let aimFiles = [],
  aimPlanNow = null,
  aimPrefix = {},
  aimOwners = {};
function aimPersonSelect(attr, val) {
  return `<select ${attr}><option value="">Pick the owner</option>${aimPeople()
    .map((u) => `<option value="${esc(u.id)}" ${u.id === val ? "selected" : ""}>${esc(u.name)}</option>`)
    .join("")}</select>`;
}
function aimHtml() {
  const S = aimStore(),
    L = aimPlanNow,
    T = L && L.totals;
  const head = `<div class="card" id="aim-card"><h3>Import from Asana</h3>
    <p class="small muted">In Asana, open each project's menu, choose Export, then CSV. Pick the files here: nothing is written until you have looked at the summary. The team board's export works too: each row goes to the job in its PROJECT NAME, and the rest to the firm's own lists. Each project here keeps its prefix and each task its ID (PAD-23 stays PAD-23). A task assigned in Asana to someone outside the team, or to nobody, goes to the project's lead, flagged for the meeting to confirm, and waits on that person.</p>
    <div class="row" style="gap:8px;flex-wrap:wrap"><label class="btn">Choose CSV Files<input type="file" id="aim-file" accept=".csv,text/csv" multiple hidden></label>${aimFiles.length ? `<span class="small muted">${aimFiles.length} file${1 === aimFiles.length ? "" : "s"}: ${aimFiles.map((f) => esc(f.name)).join(", ")}</span>` : ""}</div>`;
  if (!L) return head + aimPendingHtml(S) + "</div>";
  const tie = T.tasks + T.steps + T.review + T.orphans + T.duplicates;
  const body = `${L.errors.length ? `<div class="note warn">${L.errors.map(esc).join("<br>")}</div>` : ""}
    <div class="note" id="aim-tie">${T.rows} row${1 === T.rows ? "" : "s"} read: ${T.tasks} task${1 === T.tasks ? "" : "s"} (${T.create} new, ${T.update} updated, ${T.same} unchanged; ${T.done} done), ${T.flagged} with the owner to confirm, ${T.steps} checklist step${1 === T.steps ? "" : "s"}, ${T.review} waiting on this screen${T.orphans ? `, ${T.orphans} subtask${1 === T.orphans ? "" : "s"} whose parent is not in these files` : ""}${T.duplicates ? `, ${T.duplicates} repeated in a second file` : ""}. ${tie === T.rows ? "Nothing is lost." : `<b>${T.rows - tie} unaccounted for.</b>`}</div>
    <div class="tw"><table class="t" id="aim-projects"><thead><tr><th>Project</th><th>Prefix</th><th>Here</th><th class="r">New</th><th class="r">Updated</th><th class="r">Done</th><th class="r">Steps</th><th class="r">To Confirm</th></tr></thead><tbody>${L.projects
      .map(
        (P) =>
          `<tr><td>${esc(P.name)}</td><td><input class="aim-pfx" data-aimpfx="${esc(P.name)}" value="${esc(P.prefix)}" size="5" aria-label="Prefix for ${esc(P.name)}"></td><td class="small">${P.firm ? "The firm's list" : P.projectId ? "Matched" : "New project"}</td><td class="r">${P.create}</td><td class="r">${P.update}</td><td class="r">${P.done}</td><td class="r">${P.sub}</td><td class="r">${P.flag}</td></tr>`,
      )
      .join("")}</tbody></table></div>
    <div class="tw" style="margin-top:10px"><table class="t" id="aim-people"><thead><tr><th>Person</th><th class="r">Owns</th><th class="r">Waited On</th><th class="r">To Confirm</th></tr></thead><tbody>${L.people
      .map((x) => `<tr><td>${esc(x.name)}</td><td class="r">${x.owner}</td><td class="r">${x.waitingOn}</td><td class="r">${x.flag}</td></tr>`)
      .join("")}</tbody></table></div>
    ${L.review.length ? aimReviewHtml(L.review, "plan") : ""}
    <div class="row" style="gap:8px;margin-top:12px;flex-wrap:wrap"><button class="btn ${rdRows && rdRows.length ? "" : "primary"}" id="aim-go">Import ${T.tasks + Object.values(aimOwners).filter(Boolean).length} Task${1 === T.tasks ? "" : "s"}</button><button class="btn" id="aim-clear">Start Over</button></div>
    <p class="small muted" style="margin:6px 0 0">Running it again with a newer export updates what changed in Asana and keeps what was changed here.</p>`;
  return head + body + "</div>";
}
function aimReviewHtml(rows, mode) {
  const by = {};
  rows.forEach((t) => ((by[t.project || "No project"] = by[t.project || "No project"] || []).push(t)));
  return `<div id="aim-review" style="margin-top:12px"><h4 style="margin:0 0 6px">Waiting for You</h4><p class="small muted" style="margin:0 0 8px">Every task has one team member who makes sure it gets done. Someone outside the team stays on the task as Waiting On.</p>${Object.entries(by)
    .map(([pj, L]) => {
      const open = L.filter((t) => !t.done),
        fin = L.filter((t) => t.done);
      return `<div class="aim-grp"><div class="row" style="gap:8px;flex-wrap:wrap;align-items:center"><b>${esc(pj)}</b><span class="small muted">${L.length} row${1 === L.length ? "" : "s"}</span><span class="grow"></span>${pj !== "No project" ? `<label class="small">All in ${esc(pj)} ${aimPersonSelect(`data-aimall="${esc(pj)}" data-aimmode="${mode}"`, "")}</label>` : ""}</div>
      ${open
        .map(
          (t) =>
            `<div class="aim-row" data-aimrow="${esc(t.asanaId)}"><div class="aim-t"><span class="small muted">${esc(t.code || "")}</span> ${esc(t.title)}<div class="small muted">${esc(t.why || "")}${t.row && t.row.due ? ` · due ${esc(fmt(t.row.due))}` : ""}</div></div>${t.project ? aimPersonSelect(`data-aimown="${esc(t.asanaId)}" data-aimmode="${mode}"`, aimOwners[t.asanaId] || "") : '<span class="small muted">Add it to its project in Asana and export again</span>'}</div>`,
        )
        .join("")}
      ${fin.length ? `<div class="aim-row"><div class="aim-t">${fin.length} finished task${1 === fin.length ? "" : "s"} with no team owner</div>${aimPersonSelect(`data-aimfin="${esc(pj)}" data-aimmode="${mode}"`, "")}</div>` : ""}</div>`;
    })
    .join("")}</div>`;
}
function aimPendingHtml(S) {
  if (!S.pending.length) {
    const last = S.runs[S.runs.length - 1];
    return last ? `<p class="small muted" style="margin:10px 0 0">Last import ${esc(stampText(last.at))}${last.by ? " by " + esc(last.by) : ""}: ${last.created} new, ${last.updated} updated, ${last.flagged || 0} with the owner to confirm, ${last.waiting} waiting here.</p>` : "";
  }
  return aimReviewHtml(S.pending.map((x) => Object.assign({}, x.t, { why: x.why })), "pending") + `<div class="row" style="margin-top:10px"><button class="btn primary" id="aim-resolve">Create the Tasks with an Owner</button></div>`;
}
function aimRead(fileList) {
  const L = [...(fileList || [])];
  if (!L.length) return;
  Promise.all(L.map((f) => f.text().then((text) => ({ name: f.name, text: text })))).then((files) => {
    (aimFiles = files), (aimOwners = {}), (aimPlanNow = aimPlan(aimFiles, { prefix: aimPrefix })), renderRealData();
  });
}
function aimWire(host) {
  const fi = host.querySelector("#aim-file");
  fi && (fi.onchange = () => aimRead(fi.files));
  host.querySelectorAll("[data-aimpfx]").forEach(
    (i) =>
      (i.onchange = () => {
        (aimPrefix[i.dataset.aimpfx] = i.value), (aimPlanNow = aimPlan(aimFiles, { prefix: aimPrefix })), renderRealData();
      }),
  );
  const rowsOf = (mode) => ("pending" === mode ? aimStore().pending.map((x) => x.t) : (aimPlanNow && aimPlanNow.review) || []);
  host.querySelectorAll("[data-aimown]").forEach((s) => (s.onchange = () => ((aimOwners[s.dataset.aimown] = s.value), "plan" === s.dataset.aimmode && renderRealData())));
  host.querySelectorAll("[data-aimall]").forEach(
    (s) =>
      (s.onchange = () => {
        rowsOf(s.dataset.aimmode)
          .filter((t) => t.project === s.dataset.aimall && !t.done)
          .forEach((t) => (aimOwners[t.asanaId] = s.value));
        renderRealData();
      }),
  );
  host.querySelectorAll("[data-aimfin]").forEach(
    (s) =>
      (s.onchange = () => {
        rowsOf(s.dataset.aimmode)
          .filter((t) => t.project === s.dataset.aimfin && t.done)
          .forEach((t) => (aimOwners[t.asanaId] = s.value));
        renderRealData();
      }),
  );
  const go = host.querySelector("#aim-go");
  go &&
    (go.onclick = () => {
      const r = aimApply(aimPlanNow, aimOwners);
      (aimPlanNow = null), (aimFiles = []), (aimOwners = {}), render();
      toast(
        `Imported: ${r.created} new task${1 === r.created ? "" : "s"}${r.updated ? `, ${r.updated} updated` : ""}${r.projects ? `, ${r.projects} new project${1 === r.projects ? "" : "s"}` : ""}${r.flagged ? `; ${r.flagged} with the owner to confirm in the meeting` : ""}${r.waiting ? `; ${r.waiting} wait on Your Own Data` : ""}`,
        () => ((view = "tkall"), render()),
      );
    });
  const cl = host.querySelector("#aim-clear");
  cl && (cl.onclick = () => ((aimPlanNow = null), (aimFiles = []), (aimOwners = {}), (aimPrefix = {}), renderRealData()));
  const rs = host.querySelector("#aim-resolve");
  rs &&
    (rs.onclick = () => {
      let n = 0;
      Object.entries(aimOwners).forEach(([id, o]) => o && aimResolve(id, o) && n++);
      aimOwners = {};
      n ? toast(`${n} task${1 === n ? "" : "s"} created from the import`, () => ((view = "tkall"), render())) : toast("Pick an owner for a row first");
      renderRealData();
    });
}
{
  const base = renderRealData;
  renderRealData = function () {
    const r = base.apply(this, arguments);
    try {
      const host = document.getElementById("rdata-body");
      if (host && aimMay()) {
        // the coordinator runs the import too (the board was theirs in Asana); the rest of this page is the owner's
        "owner" !== role() && [...host.children].forEach((c) => c.classList && (c.classList.contains("card") || c.classList.contains("glance")) && c.remove());
        const box = document.createElement("div");
        (box.innerHTML = aimHtml()), host.querySelector(".glance") ? host.querySelector(".glance").after(box.firstElementChild) : host.prepend(box.firstElementChild);
        aimWire(host);
        // the team's workspace has no demo to take out and no sample company to start again from
        twsIsTeam() &&
          host.querySelectorAll("#rd-wipe-jobs, #rd-sample").forEach((b) => {
            const c = b.closest(".card");
            c && c.remove();
          });
      }
    } catch (e) {
      console.warn("asana import", e);
    }
    return r;
  };
}
// One import: Tasks' Import the Board opens this screen (the older one-step board import is folded into it), and the
// rows still waiting are named on Tasks, one tap from the list.
const aimMay = () => ["owner", "coord"].includes(role());
"object" == typeof ROLE_VIEWS && ROLE_VIEWS.coord && !ROLE_VIEWS.coord.includes("rdata") && ROLE_VIEWS.coord.push("rdata");
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      const b = document.querySelector("#v-tkall #tk-import");
      b && (aimMay() ? (b.onclick = () => ((view = "rdata"), render(), setTimeout(() => document.getElementById("aim-card") && document.getElementById("aim-card").scrollIntoView({ block: "start" }), 60))) : b.remove());
      const n = DB.asanaImport && DB.asanaImport.pending ? DB.asanaImport.pending.length : 0,
        v = "tkall" === view && aimMay() && n ? document.getElementById("v-tkall") : null;
      if (v && !v.querySelector("#aim-wait")) {
        const d = document.createElement("div");
        (d.id = "aim-wait"), (d.className = "note"), (d.style.margin = "0 0 10px");
        d.innerHTML = `${n} task${1 === n ? "" : "s"} from Asana ${1 === n ? "waits" : "wait"} for you. <a href="#" id="aim-wait-go">Open the Import</a>`;
        v.prepend(d);
        d.querySelector("#aim-wait-go").onclick = (e) => (e.preventDefault(), (view = "rdata"), render());
      }
    } catch (e) {}
    return r;
  };
}
// The Standard's job duties (the Friday client update, the weekly site walk, the huddle) are for a job with a client.
// In the team's workspace an Asana project is not always a job ("Operations"), and a project imported with no client
// would get a client update nobody can send: the duties start when the project has a client.
{
  const base = tdyRecurDue;
  tdyRecurDue = function () {
    const out = base.apply(this, arguments);
    if (!twsIsTeam()) return out;
    const noClient = new Set((DB.projects || []).filter((p) => !p.clientId).map((p) => p.id));
    return out.filter((d) => !(d.projectId && noClient.has(d.projectId) && /^(friday|walk|huddle)$/.test(d.duty)));
  };
}
