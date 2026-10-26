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
// (Dependencies), Blocking (Dependencies), then one column per custom field. The team board adds its own: GENERAL
// NOTES, PROJECT NAME, a second Task ID (the team's key), NEW?CARRIED and PRIORITY.
// The rules (Alan, 10-26, after the first dry run of the real board scrambled it):
//   - a task keeps its key exactly as the team wrote it: the team's Task ID column first, else the key the name starts
//     with; case and zero padding kept, numeric series ("144-01") too. A key mentioned in the notes is never the
//     task's key. Only a row with no key gets one, in its project's series, padded like its neighbours.
//   - a series is firm-wide (a finance and an ops series sit on the Office list and on jobs): a project can hold keys
//     of several series. A key is unique firm-wide; a true duplicate is refused to the review list.
//   - the owner is the assignee: by Assignee Email, else by the exact full name; never by a first name alone, never
//     someone else. An assignee who is not on the team waits for an owner on this screen; nobody is given the task
//     silently.
//   - PROJECT NAME is the project, trimmed, its case and spacing evened out ("141St st" and "141st St" are one).
//     "General" and the meeting-notes section are the firm's own Office list. A project that is a job here joins it.
//   - every field is kept: dates, both notes, priority, NEW or CARRIED, parent, dependencies, tags, the Asana id.
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
  // the team board's own custom fields: the job a row is about (rows without one are the firm's own lists), and the
  // team's key (a second "Task ID" column beside Asana's own)
  projectName: /^project name$/i,
  key: /^task id \(\d+\)$|^task key$|^key$/i,
};
// the team board's other custom fields, read by name and kept in custom as well
const AIM_EXTRA = { general: /^general notes$/i, carried: /^new\s*[?\/]\s*carried$|^new or carried$/i, pri: /^priority$/i };
// A key in its own cell: letters ("PAT-02", "ops-3") or a numeric series ("144-01").
const AIM_KEY_CELL = /^\s*\[?([A-Za-z][A-Za-z0-9]{0,7}|\d{1,6})-(\d{1,5})\]?\s*$/;
// A key the name starts with ("PAT-02 Close out selections"); never a date ("2026-10-22 notes").
const AIM_KEY = /^\s*\[?([A-Z][A-Z0-9]{0,7}|\d{2,6})-(\d{1,5})\]?(?!\d|[-\/]\d)(?:[\s:.\u2013\u2014-]+|$)/;
// a custom column that holds words, never a key (a key mentioned in the notes is not the task's key)
const AIM_WORDS_COL = /note|comment|description|summary|update|status|tag|carried|priority|project/i;
const aimNorm = (s) => String(s || "").trim().replace(/\s+/g, " ");
const aimPjKey = (s) => aimNorm(s).toLowerCase();
const aimKeyNorm = (k) => ("function" == typeof tkKeyNorm ? tkKeyNorm(k) : String(k || "").trim().toUpperCase());
// "General" (and "Office") on the team board is the firm's own work, not a job
const AIM_FIRM = /^(general|office)$/i;
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
// P1 to P3 (the team board), or High, Medium, Low: the task's one scale (priority) and the board's word (pri3)
function aimPriority(v) {
  const t = String(v || "").trim().toUpperCase();
  if (/^P[123]$/.test(t)) return { pri3: t, priority: { P1: "high", P2: "med", P3: "low" }[t] };
  const w = /^(HIGH|URGENT)$/.test(t) ? "high" : /^(MED|MEDIUM|NORMAL)$/.test(t) ? "med" : /^LOW$/.test(t) ? "low" : "";
  return w ? { pri3: { high: "P1", med: "P2", low: "P3" }[w], priority: w } : { pri3: "", priority: "" };
}
// One file's rows in the import's own shape, with the custom fields kept by their column names.
function aimReadFile(file) {
  const P = aimParseCsv(file.text),
    col = {},
    ex = {};
  P.header.forEach((h) => {
    for (const [k, re] of Object.entries(AIM_COLS)) if (re.test(h) && !col[k]) return void (col[k] = h);
  });
  P.header.forEach((h) => {
    for (const [k, re] of Object.entries(AIM_EXTRA)) re.test(h) && !ex[k] && (ex[k] = h);
  });
  if (!col.id || !col.name) return { error: `${file.name || "That file"} is not an Asana export: it has no Task ID and Name columns`, rows: [] };
  const known = new Set(Object.entries(col).filter(([k]) => "key" !== k).map(([, h]) => h)),
    // the columns the import maps to no built-in field: each becomes one of the board's own fields (Alan, 10-26)
    mapped = new Set([...known, ...Object.values(ex), col.key].filter(Boolean)),
    customCols = P.header.filter((h) => h && !mapped.has(h));
  return {
    board: !!col.projectName,
    customCols: customCols,
    rows: P.rows.map((r, i) => {
      const g = (k) => (col[k] ? String(r[col[k]] || "").trim() : ""),
        x = (k) => (ex[k] ? String(r[ex[k]] || "").trim() : ""),
        custom = {};
      P.header.forEach((h) => {
        !known.has(h) && String(r[h] || "").trim() && (custom[h] = String(r[h]).trim());
      });
      const pr = aimPriority(x("pri")),
        cv = x("carried");
      return {
        file: file.name || "",
        line: i + 2,
        id: g("id"),
        created: aimDate(g("created")),
        completed: aimDate(g("completed")),
        modified: aimDate(g("modified")),
        name: g("name"),
        section: g("section"),
        assignee: aimNorm(g("assignee")),
        email: g("email").toLowerCase(),
        start: aimDate(g("start")),
        due: aimDate(g("due")),
        tags: aimSplit(g("tags")),
        notes: col.notes ? String(r[col.notes] || "").trim() : "",
        general: ex.general ? String(r[ex.general] || "").trim() : "",
        projects: aimSplit(g("projects")),
        parent: g("parent"),
        blockedBy: aimSplit(g("blockedBy")),
        blocking: aimSplit(g("blocking")),
        boardFile: !!col.projectName,
        projectName: aimNorm(g("projectName")),
        keyCell: g("key"),
        keyCol: col.key || "",
        pri3: pr.pri3,
        priority: pr.priority,
        carried: /carried/i.test(cv) ? "CARRIED" : /new/i.test(cv) ? "NEW" : "",
        custom: custom,
        customCols: customCols,
      };
    }),
  };
}
// The team's people who can own a task: users of the app, never a client.
function aimPeople() {
  return (DB.users || []).filter((u) => u && u.id && "client" !== u.role && !/^mb_/.test(u.role || ""));
}
// The team member an Asana assignee is: by their Asana email, else by the exact full name, and only when one person
// carries it. Never by a first name alone, never a role word, never the board's lead: a person who is not on the team
// here is nobody's to guess (the row waits for an owner).
function aimMatch(name, email) {
  const U = aimPeople(),
    e = String(email || "").trim().toLowerCase();
  if (e) {
    const u = U.find((x) => String(x.contact || x.email || "").trim().toLowerCase() === e);
    if (u) return { u: u, how: "email" };
  }
  const low = aimNorm(name).toLowerCase();
  if (!low) return null;
  const full = U.filter((x) => aimNorm(x.name).toLowerCase() === low);
  return 1 === full.length ? { u: full[0], how: "name" } : null;
}
function aimPersonOf(name, email) {
  const m = aimMatch(name, email);
  return m ? m.u : null;
}
// Someone outside the team, on file here: a vendor, a client's contact or a consultant, by email, else by the exact
// name (never a first name: a staff member Asana names is not a vendor because a vendor shares her first name).
function aimContactOf(name, email) {
  const e = String(email || "").trim().toLowerCase(),
    n = aimNorm(name).toLowerCase(),
    em = (v) => !!e && String(v || "").trim().toLowerCase() === e,
    eq = (v) => !!n && aimNorm(v).toLowerCase() === n,
    out = (kind, id, nm) => ({ kind: kind, id: id, name: name || nm || "" });
  const V = DB.vendors || [],
    C = DB.clients || [],
    H = (DB.hub && DB.hub.contacts) || [],
    hn = (x) => `${x.first || ""} ${x.last || ""}`.trim() || x.name;
  let v = V.find((x) => x && em(x.email)),
    c = !v && C.find((x) => x && (em(x.email) || (x.contacts || []).some((k) => k && em(k.email)))),
    h = !v && !c && H.find((x) => x && em(x.email));
  if (v) return out("vendor", v.id, v.name);
  if (c) return out("client", c.id, c.name);
  if (h) return out("consultant", h.id, hn(h));
  v = V.find((x) => x && (eq(x.name) || eq(x.contact)));
  if (v) return out("vendor", v.id, v.name);
  c = C.find((x) => x && (eq(x.name) || (x.contacts || []).some((k) => k && eq(k.name))));
  if (c) return out("client", c.id, c.name);
  h = H.find((x) => x && (eq(hn(x)) || eq(x.company)));
  return h ? out("consultant", h.id, hn(h)) : null;
}
// A prefix for a project whose rows carry no key of its own: the street number the team names its series by
// ("144th St" 144), else the app's guess from the words (Hollis Kitchen Renovation HKR); never one already taken.
function aimPrefixFromName(name, taken) {
  const t = aimNorm(name),
    tries = [],
    num = /^(\d{2,6})(?:st|nd|rd|th)?\b/i.exec(t);
  num && tries.push(num[1]);
  try {
    "function" == typeof tkPrefixGuess && tries.push(tkPrefixGuess(t));
  } catch (e) {}
  const words = t
    .replace(/[^A-Za-z0-9 ]+/g, " ")
    .split(/\s+/)
    .filter((w) => w && !/^(the|and|of|at|on|for|a|an)$/i.test(w));
  let p = (words.length > 1 ? words.map((w) => w[0]).join("") : (words[0] || "PRJ").slice(0, 3)).toUpperCase().slice(0, 4);
  /^[A-Z0-9]/.test(p) || (p = "P" + p);
  tries.push(p);
  const up = (x) => String(x || "").toUpperCase();
  for (const x of tries) if (x && !taken.has(up(x))) return up(x);
  let out = up(tries[tries.length - 1]),
    i = 2;
  for (; taken.has(out + i); ) i++;
  return out + i;
}
// Every task on every board (a job's to-dos, the firm's own lists, Sales), by Asana id and by key.
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
    a && a.code && codes.set(aimKeyNorm(a.code), { a: a, p: r.p, board: r.board });
  });
  return { byAsana: byAsana, codes: codes };
}
// The task a row already is: by its Asana id; else by its key, when that task came from an Asana import (the older
// one-step board import marked source.asana) or carries the same title. A hand-made task that holds the key is
// someone else's: the row is a duplicate.
function aimFind(idx, id, code, title) {
  const a = id && idx.byAsana.get(String(id));
  if (a) return a;
  const c = code && idx.codes.get(aimKeyNorm(code));
  if (!c || (c.a.asana && c.a.asana.id && id && String(c.a.asana.id) !== String(id))) return null;
  const low = (x) => aimNorm(x).toLowerCase();
  return (c.a.source && (c.a.source.asana || "asana" === c.a.source.kind)) || low(c.a.title) === low(title) ? c : null;
}
const aimHolder = (a) => (a.asana && a.asana.id ? "asana:" + a.asana.id : "app:" + a.id);
// A board's meta (its prefix and next number): a job's own project record, or the firm's map for its own lists.
function aimMeta(board) {
  if ("function" == typeof tkBoardMeta) return tkBoardMeta(board);
  const p = /^p:/.test(board) ? (DB.projects || []).find((q) => "p:" + q.id === board) : null;
  return p ? p.project : null;
}
function aimPrefixesTaken() {
  const S = new Set();
  (DB.projects || []).forEach((p) => p.project && p.project.prefix && S.add(String(p.project.prefix).toUpperCase()));
  Object.values((DB.company && DB.company.tkBoards) || {}).forEach((m) => m && m.prefix && S.add(String(m.prefix).toUpperCase()));
  return S;
}
// The job a project name means: the one an earlier import made for it, the same name or address with case and
// spacing evened out, or one job known by two names (asProjectFor, the rule the board import used).
function aimJobFor(name) {
  const low = aimPjKey(name);
  let p =
    (DB.projects || []).find((q) => q.project && aimPjKey(q.project.asanaName) === low) ||
    (DB.projects || []).find((q) => q.project && (aimPjKey(q.project.name) === low || aimPjKey(q.project.address) === low)) ||
    null;
  if (!p)
    try {
      const h = "function" == typeof asProjectFor ? asProjectFor({ projectName: name }) : null;
      h && !h.__property && (p = h);
    } catch (e) {}
  return p || null;
}
// the spelling a project is shown by, of the ones the rows use: the most rows, then the most Title-like
// ("141st St" over "141St st")
function aimBestSpelling(names) {
  const n = {};
  names.forEach((x) => (n[x] = (n[x] || 0) + 1));
  const score = (x) => x.split(" ").reduce((a, w) => a + (/^[A-Z0-9]/.test(w) ? 1 : 0) - (w.slice(1).match(/(?<=[a-z0-9])[A-Z]/g) || []).length, 0);
  return Object.keys(n).sort((a, b) => n[b] - n[a] || score(b) - score(a))[0] || "";
}
// The dry run: what the files would do, and nothing written. files: [{name, text}]. opts.prefix: {project name: prefix}
// the person typed over the suggested ones.
// Where a row goes: a per-project export's rows go to that project (a job here); the team board's export names the job
// in PROJECT NAME, and a row without one (or "General") is on the firm's own lists: the Office list, or the list its
// section names (Finance & Admin).
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
    S0 = "function" == typeof tkSeriesScan ? tkSeriesScan() : {},
    pend = new Map((((DB.asanaImport || {}).pending) || []).filter((x) => x && x.asanaId).map((x) => [x.asanaId, x]));
  // ---- the key each row carries: the team's Task ID column, else the name's leading key, else a custom field that
  // holds only a key (never a column of words: a key mentioned in the notes is not the task's key)
  const cellKey = (v) => {
    const m = AIM_KEY_CELL.exec(String(v || ""));
    return m ? `${m[1]}-${m[2]}` : "";
  };
  const knownSeries = new Set(Object.keys(S0));
  rows.forEach((r) => {
    const k = cellKey(r.keyCell);
    k && knownSeries.add(k.split("-")[0].toUpperCase());
  });
  rows.forEach((r) => {
    let k = cellKey(r.keyCell),
      from = k ? "column" : "";
    const m = AIM_KEY.exec(r.name),
      nk = m && (/^[A-Z]/.test(m[1]) || /^0\d/.test(m[2]) || knownSeries.has(m[1])) ? `${m[1]}-${m[2]}` : "";
    if (!k && nk) (k = nk), (from = "name");
    if (!k)
      for (const [h, v] of Object.entries(r.custom)) {
        if (h === r.keyCol || AIM_WORDS_COL.test(h)) continue;
        const c = cellKey(v);
        if (c) {
          (k = c), (from = "field");
          break;
        }
      }
    r.keyFound = k;
    r.keyFrom = from;
    // the title without the key it starts with (only when that key is the row's own)
    r.title = nk && aimKeyNorm(nk) === aimKeyNorm(k) ? r.name.slice(m[0].length).trim() || r.name : r.name;
  });
  // a subtask with a key of its own is a task the team names in the meeting; one without is a checklist step
  const top = rows.filter((r) => !r.parent || r.keyFound),
    subs = rows.filter((r) => r.parent && !r.keyFound);
  // ---- the project each row is on
  const fileProj = {};
  top.forEach((r) => !r.boardFile && r.projects[0] && ((fileProj[r.file] = fileProj[r.file] || new Set()).add(r.projects[0])));
  const spell = {};
  top.forEach((r) => {
    if (r.boardFile) {
      const notes = /meeting notes/i.test(r.section) || /^untitled section$/i.test(r.section) || !r.section;
      if (!r.projectName || AIM_FIRM.test(r.projectName)) (r.project = !r.projectName && !notes ? aimNorm(r.section) : "Office"), (r.firm = !0);
      else (r.project = r.projectName), (r.firm = !1);
    } else {
      r.project = aimNorm(r.projects[0] || (fileProj[r.file] && 1 === fileProj[r.file].size ? [...fileProj[r.file]][0] : ""));
      r.firm = AIM_FIRM.test(r.project);
      r.firm && (r.project = "Office");
    }
    r.project && ((spell[aimPjKey(r.project)] = spell[aimPjKey(r.project)] || []).push(r.project));
  });
  // a keyed subtask with no project of its own is on its parent's
  top.forEach((r) => {
    if (r.project || !r.parent) return;
    const par = top.find((x) => x !== r && x.project && (x.name === r.parent || (x.keyFound && aimKeyNorm(x.keyFound) === aimKeyNorm(r.parent))));
    par && ((r.project = par.project), (r.firm = par.firm));
  });
  // one project, however its rows spell it
  const best = {};
  Object.entries(spell).forEach(([k, L]) => (best[k] = aimBestSpelling(L)));
  top.forEach((r) => r.project && (r.project = best[aimPjKey(r.project)]));
  // ---- the series: a series whose keys sit in one project only is that project's own; one that sits in several (or
  // on a board here other than the project's) is firm-wide, and never a project's prefix
  const serIn = {};
  top.forEach((r) => r.keyFound && r.project && (serIn[r.keyFound.split("-")[0].toUpperCase()] = serIn[r.keyFound.split("-")[0].toUpperCase()] || new Set()).add(r.project));
  const taken = aimPrefixesTaken(),
    projects = new Map();
  top.forEach((r) => {
    if (!r.project || projects.has(r.project)) return;
    const name = r.project,
      typed = O.prefix && O.prefix[name] ? String(O.prefix[name]).toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8) : "";
    let p = null,
      board = "";
    if (r.firm) board = "s:" + name;
    else (p = aimJobFor(name)), (board = p ? "p:" + p.id : "");
    const meta = board ? aimMeta(board) : null,
      had = String((r.firm && (((DB.company || {}).tkBoards || {})[board] || {}).prefix) || (p && p.project && p.project.prefix) || "");
    const cnt = {};
    top.forEach((x) => {
      if (x.project !== name || !x.keyFound) return;
      const s = x.keyFound.split("-")[0],
        u = s.toUpperCase(),
        z = S0[u];
      serIn[u].size > 1 || (z && [...z.boards].some((b) => b !== board)) || (taken.has(u) && u !== had.toUpperCase()) || (cnt[s] = (cnt[s] || 0) + 1);
    });
    const own = Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a])[0] || "",
      prefix = typed || (meta && meta.prefixSet && had) || own || had || aimPrefixFromName(name, new Set([...taken, ...Object.keys(serIn)]));
    taken.add(prefix.toUpperCase());
    projects.set(name, { name: name, prefix: prefix, typed: !!typed, firm: !!r.firm, board: board, projectId: p ? p.id : "", existing: !!(p || had), create: 0, update: 0, same: 0, done: 0, review: 0, flag: 0, sub: 0, kept: 0, made: 0, waiting: 0, refused: 0 });
  });
  // ---- keys: never one already used (as it reads aloud: PAT-2 is PAT-02); a new one in its project's series
  const used = new Map([...idx.codes].map(([k, x]) => [k, aimHolder(x.a)])),
    Z = {};
  Object.entries(S0).forEach(([k, x]) => (Z[k] = { max: x.max, width: x.width }));
  top.forEach((r) => {
    const m = /^(.+)-(\d+)$/.exec(r.keyFound || "");
    if (!m) return;
    const k = m[1].toUpperCase(),
      x = (Z[k] = Z[k] || { max: 0, width: 0 });
    x.max = Math.max(x.max, +m[2]);
    /^0\d/.test(m[2]) && (x.width = Math.max(x.width, m[2].length));
  });
  const num = (P) => {
    const k = P.prefix.toUpperCase(),
      meta = P.board ? aimMeta(P.board) : null,
      x = (Z[k] = Z[k] || { max: 0, width: 0 });
    // a new series is padded like the project's other keys
    if (!x.width && !x.max) {
      const pad = top.filter((r) => r.project === P.name && /-0\d/.test(r.keyFound || ""));
      pad.length && pad.length * 2 >= top.filter((r) => r.project === P.name && r.keyFound).length && (x.width = 2);
    }
    const n = Math.max(x.max + 1, (meta && String(meta.prefix || "").toUpperCase() === k && +meta.keyNext) || 1);
    x.max = n;
    return `${P.prefix}-${String(n).padStart(x.width, "0")}`;
  };
  const tasks = [],
    review = [],
    people = {},
    // one line per person: a team member however Asana spells them, else the Asana email or name
    tell = (nm, em) => {
      const m = aimMatch(nm, em),
        k = m ? "u:" + m.u.id : (em || aimNorm(nm).toLowerCase() || "nobody").toLowerCase();
      return (people[k] = people[k] || { name: nm || "Nobody", email: em || "", here: "", how: "", owner: 0, waiting: 0, waitingOn: 0, flag: 0 });
    },
    order = {};
  top.forEach((r) => {
    const P = projects.get(r.project),
      ex = aimFind(idx, r.id, r.keyFound, r.title),
      M = aimMatch(r.assignee, r.email),
      outside = !M && r.assignee ? aimContactOf(r.assignee, r.email) : null;
    const t = {
      asanaId: r.id,
      row: r,
      project: r.project,
      firm: !!(P && P.firm),
      code: "",
      keyFound: r.keyFound,
      title: r.title,
      section: r.section,
      order: 0,
      ownerName: "",
      ownerHow: "",
      flag: null,
      waitingOn: outside,
      unmatched: null,
      done: !!r.completed,
      completedAt: r.completed,
      checklist: [],
      exists: !!ex,
    };
    if (!P) return (t.why = "The row names no project: add it to its project in Asana and export again"), (t.code = r.keyFound), review.push(t), void tell(r.assignee, r.email).waiting++;
    t.order = order[r.project] = (order[r.project] || 0) + 1;
    // the key: the team's, exactly; a true duplicate is refused; a row with none takes the next in its series
    if (r.keyFound) {
      const holder = used.get(aimKeyNorm(r.keyFound)),
        mine = ex ? aimHolder(ex.a) : "asana:" + (r.id || r.file + ":" + r.line);
      if (holder && holder !== mine) {
        const other = idx.codes.get(aimKeyNorm(r.keyFound)),
          what = other ? `the task “${other.a.title}”` : "another row of this export";
        t.code = r.keyFound;
        t.refused = "duplicate";
        t.why = `${r.keyFound} is already the key of ${what}: a key names one task. Fix the key in Asana and export again`;
        P.refused++, P.review++, review.push(t), tell(r.assignee, r.email).waiting++;
        return;
      }
      t.code = r.keyFound;
      P.kept++;
    } else {
      // a row with no key: the key it already has here, or the one it was given while it waits for an owner (so a
      // second import of the same file gives the same key), else the next in its project's series
      const w = pend.get(r.id);
      (t.code = (ex && ex.a.code) || (w && w.code && !w.t.keyFound ? w.code : "") || num(P)), (t.made = !ex), ex || P.made++;
    }
    used.set(aimKeyNorm(t.code), ex ? aimHolder(ex.a) : "asana:" + (r.id || r.file + ":" + r.line));
    // the owner: the assignee on the team, or nobody yet. A task already here keeps the owner it has, unless the
    // older import gave it to someone else (flagged, the assignee now on the team): then it is the assignee's.
    const pe = tell(r.assignee, r.email);
    if (ex && ex.a.assignee) {
      const f = ex.a.ownerFlag;
      if (M && f && f.was && aimNorm(f.was).toLowerCase() === aimNorm(r.assignee).toLowerCase() && f.to === ex.a.assignee) (t.ownerName = M.u.name), (t.ownerHow = M.how), (t.ownerFix = !0);
      else (t.ownerName = ex.a.assignee), (t.ownerHow = "kept");
    } else if (M) (t.ownerName = M.u.name), (t.ownerHow = M.how);
    if (M) (pe.here = M.u.name), (pe.how = M.how);
    if (!t.ownerName) {
      // Every task has one team member who makes sure it gets done (Alan, 10-23), and it is the person Asana names
      // (10-26): the row waits here for the owner to pick one, or to add the person to the team.
      t.unmatched = r.assignee ? { name: r.assignee, email: r.email } : null;
      t.why = r.assignee
        ? outside
          ? `Assigned in Asana to ${r.assignee}, who is outside the team: pick the team member who owns it (${r.assignee} stays Waiting On)`
          : `Assigned in Asana to ${r.assignee}${r.email ? ` (${r.email})` : ""}, who is not on the team here: pick the owner, or add them to the team`
        : "No one is assigned in Asana: pick the owner";
      P.review++, P.waiting++, pe.waiting++, outside && pe.waitingOn++;
      review.push(t);
      return;
    }
    pe.owner++;
    t.ex = ex;
    tasks.push(t);
  });
  // subtasks: checklist steps on their parent (by the parent's name, in the same export first); a keyed subtask is a
  // task of its own, linked to its parent by the parent's key
  const all = tasks.concat(review),
    orphans = [],
    parentOf = (r) => all.find((t) => t.row.name === r.parent && t.row.file === r.file) || all.find((t) => t.row.name === r.parent) || all.find((t) => t.code && aimKeyNorm(t.code) === aimKeyNorm(r.parent));
  subs.forEach((r) => {
    const par = parentOf(r);
    if (!par) return void orphans.push(r);
    const who = r.assignee ? ` (${r.assignee}${r.due ? ", " + r.due : ""})` : r.due ? ` (${r.due})` : "";
    par.checklist.push({ t: r.name + who, done: !!r.completed, by: "Asana", at: r.completed || r.created || "", asanaId: r.id });
    projects.get(par.project) && projects.get(par.project).sub++;
  });
  // parent and dependencies as links: each named by the key it has here (Asana names them by its id or the name)
  const codeOf = (v) => {
    const s = String(v || "").trim(),
      t = all.find((x) => x.asanaId && x.asanaId === s) || all.find((x) => x.row.name === s) || all.find((x) => x.code && aimKeyNorm(x.code) === aimKeyNorm(s));
    if (t && t.code) return t.code;
    const e = idx.byAsana.get(s);
    return (e && e.a.code) || s;
  };
  all.forEach((t) => {
    t.parentCode = t.row.parent ? codeOf(t.row.parent) : "";
    t.blockedBy = t.row.blockedBy.map(codeOf);
    t.blocking = t.row.blocking.map(codeOf);
  });
  // new, updated or unchanged: told once every field is known (the links above included)
  tasks.forEach((t) => {
    const P = projects.get(t.project);
    t.exists ? (aimChanged(t.ex.a, t) ? P.update++ : P.same++) : P.create++, t.done && P.done++;
    delete t.ex;
  });
  const P = [...projects.values()],
    peopleL = Object.values(people).filter((x) => x.owner || x.waiting || x.waitingOn),
    allRows = tasks.concat(review);
  return {
    errors: errors,
    rows: raw.length,
    duplicates: dup.length,
    projects: P,
    people: peopleL.sort((a, b) => b.owner + b.waiting - (a.owner + a.waiting)),
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
      flagged: tasks.filter((t) => t.ownerFix).length,
      steps: subs.length - orphans.length,
      review: review.length,
      waitingOwner: review.filter((t) => !t.refused && t.project).length,
      refused: review.filter((t) => t.refused).length,
      noProject: review.filter((t) => !t.project).length,
      keysKept: allRows.filter((t) => t.keyFound && t.code === t.keyFound && !t.refused).length,
      keysMade: allRows.filter((t) => t.made).length,
      byEmail: tasks.filter((t) => "email" === t.ownerHow).length,
      byName: tasks.filter((t) => "name" === t.ownerHow).length,
      due: allRows.filter((t) => t.row.due).length,
      noDue: allRows.filter((t) => !t.row.due).length,
      orphans: orphans.length,
      duplicates: dup.length,
      newProjects: P.filter((x) => !x.existing && !x.firm).length,
    },
  };
}
// What one import writes on the task, kept so a later import can tell the app's own edits from Asana's.
function aimSnap(t) {
  const r = t.row;
  return {
    title: t.title,
    code: t.code,
    due: r.due,
    start: r.start,
    section: t.section,
    done: t.done,
    owner: t.ownerName,
    notes: r.notes,
    general: r.general || "",
    pri3: r.pri3 || "",
    carried: r.carried || "",
    tags: (r.tags || []).join(", "),
    parentCode: t.parentCode || "",
    blockedBy: (t.blockedBy || []).join(", "),
    blocking: (t.blocking || []).join(", "),
  };
}
function aimChanged(a, t) {
  const s = (a.asana && a.asana.snap) || {},
    n = aimSnap(t);
  if (!a.asana) return !0; // a task an earlier import made without Asana's id: brought under this import once
  // a field an older import did not keep counts as changed only when the export now says something
  return (
    Object.keys(n).some((k) => "owner" !== k && (k in s ? String(s[k] == null ? "" : s[k]) !== String(n[k] == null ? "" : n[k]) : "" !== String(n[k] == null ? "" : n[k]) && String(n[k]) !== String(aimField(a, k)))) ||
    !!t.ownerFix ||
    (t.checklist || []).some((c) => !(a.checklist || []).some((x) => x.asanaId && x.asanaId === c.asanaId))
  );
}
// the task's own field a snap key stands for (arrays read as "a, b")
const AIM_FIELD = { due: "due", start: "start", title: "title", section: "section", general: "generalNotes", pri3: "pri3", carried: "carried", tags: "tags", parentCode: "parentCode", blockedBy: "blockedBy", blocking: "blocking", code: "code" };
const aimField = (a, k) => {
  const v = a[AIM_FIELD[k] || k];
  return Array.isArray(v) ? v.join(", ") : null == v ? "" : v;
};
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
  let p = (P.projectId && (DB.projects || []).find((q) => q.id === P.projectId)) || aimJobFor(P.name);
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
// the comment a row's notes make: Asana's Notes. The team's GENERAL NOTES is the task's General Notes field
// (generalNotes), its own place in the sheet, never a comment and never a column (Alan, 10-26).
function aimNotesOf(t) {
  const r = t.row,
    at = (r.created || today()) + "T09:00:00",
    id = "asn_" + (t.asanaId || uid("n")),
    out = [];
  r.notes && out.push({ id: id, at: at, by: "Asana", text: r.notes, ev: "notes", source: "asana" });
  return out;
}
// An older import wrote GENERAL NOTES as a comment ("General notes: …"): it moves to the General Notes field once,
// the field keeping what it already holds, and the comment leaves the thread (it was the import's, not a person's).
const AIM_GEN_RE = /^(?:Notes in Asana now read: )?General notes: /;
function aimGeneralMove(a) {
  const T = a.thread || [],
    G = T.filter((c) => c && "asana" === c.source && AIM_GEN_RE.test(String(c.text || "")));
  if (!G.length) return !1;
  const last = String(G[G.length - 1].text).replace(AIM_GEN_RE, "").trim();
  a.generalNotes || (a.generalNotes = last);
  a.thread = T.filter((c) => !G.includes(c));
  return !0;
}
// The board's own fields: each column the import maps to nothing, with what it holds. A select when its values repeat
// (a handful of short choices), long text when a value runs long, else text. Registered once, by column name.
function aimCustomFields(plan) {
  if ("function" != typeof tvAddField) return [];
  const rows = plan.tasks.concat(plan.review).map((t) => t.row),
    cols = [...new Set(rows.flatMap((r) => r.customCols || []))],
    board = [...new Set(rows.flatMap((r) => r.projects || []))][0] || "";
  return cols
    .map((col) => {
      const V = rows.map((r) => String((r.custom || {})[col] || "").trim()).filter(Boolean),
        D = [...new Set(V)];
      if (!V.length) return null;
      const type = V.some((v) => v.length > 80 || /\n/.test(v)) ? "long" : D.length <= 12 && D.length < V.length && D.every((v) => v.length <= 32) ? "select" : "text";
      return tvAddField({ name: col, col: col, type: type, values: "select" === type ? D.sort() : [], board: board, from: "the Asana import" });
    })
    .filter(Boolean);
}
// Write one planned task (new, or an update that keeps the app's own edits). Returns {a, p, created} or
// {refused: why} when its key is now another task's.
function aimWrite(t, plan, now, ownerName) {
  const P = plan.projects.find((x) => x.name === t.project);
  if (!P || t.refused) return null;
  const who = ownerName || t.ownerName;
  if (!who) return null;
  const idx = aimIndex(),
    ex = aimFind(idx, t.asanaId, t.code, t.title);
  // a key is one task's: a row picked from the waiting list after the board moved on is checked again
  if (!ex && t.code) {
    const h = idx.codes.get(aimKeyNorm(t.code));
    if (h) {
      if (t.keyFound) return { refused: `${t.code} is already the key of the task “${h.a.title}”: a key names one task. Fix the key in Asana and export again` };
      t.code = "";
    }
  }
  const B = aimBoard(P, now),
    me = currentUser() || {};
  t.code || (t.code = ("function" == typeof tkNextKey && tkNextKey(B.board)) || "");
  const notes = aimNotesOf(t),
    wo = t.waitingOn ? { name: t.waitingOn.name, contactRef: t.waitingOn.id ? { kind: t.waitingOn.kind, id: t.waitingOn.id } : null, what: t.title, promised: t.row.due || "", evidence: "Assigned to them in Asana" } : null,
    snap = aimSnap(Object.assign({}, t, { ownerName: who })),
    r = t.row,
    asanaOf = (a) => Object.assign({}, a.asana, { id: t.asanaId || "", project: t.project, lastModified: r.modified, importedAt: now, snap: snap, blockedBy: r.blockedBy || [], blocking: r.blocking || [], parent: r.parent || "" });
  if (ex) {
    const a = ex.a,
      s = (a.asana && a.asana.snap) || {},
      // a field takes Asana's value unless the app changed it since the last import
      put = (k, v) => {
        const f = AIM_FIELD[k] || k,
          cur = aimField(a, k);
        if (a.asana && k in s && String(cur) !== String(s[k] == null ? "" : s[k]) && !(null == s[k] && !cur)) return;
        a[f] = Array.isArray(a[f]) || /^(tags|blockedBy|blocking)$/.test(k) ? aimSplit(v) : v;
      };
    put("title", snap.title), put("due", snap.due), put("start", snap.start), B.p && put("section", snap.section);
    ["general", "pri3", "carried", "tags", "parentCode", "blockedBy", "blocking"].forEach((k) => put(k, snap[k]));
    snap.pri3 && a.pri3 === snap.pri3 && (a.priority = { P1: "high", P2: "med", P3: "low" }[snap.pri3]);
    // the team's key, exactly: an older import that changed it (PAT-2 for PAT-02, a made-up prefix) is put right,
    // and the old one still finds the task; a key a person renamed here (keyWas holds the team's) stays
    if (t.keyFound && a.code !== t.keyFound && !(a.keyWas || []).some((k) => aimKeyNorm(k) === aimKeyNorm(t.keyFound) && aimKeyNorm(a.code) !== aimKeyNorm(k))) {
      a.code && aimKeyNorm(a.code) !== aimKeyNorm(t.keyFound) && (a.keyWas = a.keyWas || []).push(a.code);
      a.code = t.keyFound;
    }
    s.done !== snap.done && ("done" === a.status) === !!s.done && ((a.status = snap.done ? "done" : aimStatus(t)), (a.completedAt = snap.done ? t.completedAt || today() : ""));
    aimGeneralMove(a);
    // the board's own fields: a value the export holds and the task does not yet
    Object.keys(r.custom || {}).length && (a.custom = Object.assign({}, r.custom, a.custom || {}));
    notes.forEach((note) => {
      if ((a.thread || []).some((c) => c && c.text && c.text.endsWith(note.text))) return;
      const was = s.notes;
      if (a.asana && was === r.notes) return;
      (a.thread = a.thread || []).push(Object.assign({}, note, { id: note.id + "_" + (r.modified || today()), text: a.asana && was ? "Notes in Asana now read: " + note.text : note.text }));
    });
    (t.checklist || []).forEach((c) => {
      const was = (a.checklist = a.checklist || []).find((x) => x.asanaId && x.asanaId === c.asanaId);
      was ? (was.done = was.done || c.done) : a.checklist.push(c);
    });
    if (t.ownerFix) {
      a.assignee = who;
      delete a.ownerFlag;
    }
    a.assignee || (a.assignee = who);
    a.code || (a.code = t.code);
    a.assigneeEmail || (a.assigneeEmail = r.email || "");
    a.asana = asanaOf(a);
    return { a: a, p: ex.p, created: !1 };
  }
  const pr = r.pri3 ? { P1: "high", P2: "med", P3: "low" }[r.pri3] : r.priority;
  const a = {
    id: uid("a"),
    code: t.code,
    title: t.title,
    assignee: who,
    assigneeEmail: r.email || "",
    collaborators: [],
    waitingOn: wo,
    waitsOn: wo ? wo.name : "",
    status: aimStatus(t),
    due: r.due || "",
    start: r.start || "",
    followUp: "",
    watchUntil: "",
    order: t.order,
    section: B.section || t.section || "",
    priority: pr || "med",
    pri3: r.pri3 || "",
    carried: r.carried || "",
    notes: "",
    generalNotes: r.general || "",
    thread: notes,
    checklist: t.checklist || [],
    tags: r.tags || [],
    links: [],
    parentCode: t.parentCode || "",
    blockedBy: t.blockedBy || [],
    blocking: t.blocking || [],
    board: (r.projects || []).join(", "),
    custom: Object.keys(r.custom || {}).length ? r.custom : null,
    createdAt: r.created || today(),
    createdBy: "Asana import",
    importedBy: me.name || "",
    completedAt: t.done ? t.completedAt || today() : "",
    modifiedAt: r.modified || "",
    source: { kind: "asana", asana: !0, id: t.asanaId || "" },
  };
  // an owner picked here over the person Asana names: said on the task, so the Asana assignee is never lost
  ownerName &&
    r.assignee &&
    aimNorm(r.assignee).toLowerCase() !== aimNorm(who).toLowerCase() &&
    a.thread.push({ id: "asn_" + (t.asanaId || a.id) + "_o", at: now, by: me.name || "", text: `Asana named ${r.assignee} as the assignee; ${who} was picked as the owner at the import.`, ev: "owner", source: "asana" });
  a.asana = asanaOf(a);
  return B.list.push(a), { a: a, p: B.p, created: !0 };
}
function aimStore() {
  return (DB.asanaImport = DB.asanaImport || { runs: [], pending: [] }), (DB.asanaImport.runs = DB.asanaImport.runs || []), (DB.asanaImport.pending = DB.asanaImport.pending || []), DB.asanaImport;
}
const aimPendingOf = (t, plan, why) => ({ asanaId: t.asanaId, project: t.project, code: t.code, title: t.title, why: why || t.why, done: t.done, refused: t.refused || "", assignee: t.row.assignee || "", email: t.row.email || "", t: JSON.parse(JSON.stringify(t)), projects: JSON.parse(JSON.stringify(plan.projects.filter((x) => x.name === t.project))) });
// Write the plan. owners: {asana id: a team member's id or name} for rows on the review list. Rows still without a
// board or an owner, and refused rows, wait on the review list.
function aimApply(plan, owners) {
  try {
    aimCustomFields(plan);
  } catch (e) {
    console.warn("the board's own fields", e);
  }
  const W = owners || {},
    now = appNowIso(),
    S = aimStore(),
    out = { created: 0, updated: 0, same: 0, flagged: 0, waiting: 0, refused: 0, projects: 0, steps: 0 },
    before = (DB.projects || []).length,
    left = [];
  plan.tasks.forEach((t) => {
    const I = aimIndex(),
      was = aimFind(I, t.asanaId, t.code, t.title),
      changed = was ? aimChanged(was.a, t) : !0,
      r = aimWrite(t, plan, now);
    if (r && r.refused) return void left.push([t, r.refused]);
    r && (r.created ? out.created++ : changed ? out.updated++ : out.same++), r && (out.steps += (t.checklist || []).length), r && t.ownerFix && out.flagged++;
  });
  plan.review.forEach((t) => {
    const o = W[t.asanaId];
    if (o && t.project && !t.refused) {
      const r = aimWrite(t, plan, now, aimOwnerName(o));
      if (r && r.refused) return void left.push([t, r.refused]);
      if (r) return r.created ? out.created++ : out.updated++, void (out.steps += (t.checklist || []).length);
    }
    left.push([t, t.why]);
  });
  // what still waits: kept by Asana id, so a second import replaces it instead of adding it twice
  const I2 = aimIndex(),
    keep = S.pending.filter((x) => !left.some(([t]) => t.asanaId && t.asanaId === x.asanaId) && !I2.byAsana.has(x.asanaId));
  S.pending = keep.concat(left.map(([t, why]) => aimPendingOf(t, plan, why)));
  out.waiting = S.pending.length;
  out.refused = S.pending.filter((x) => x.refused).length;
  out.projects = (DB.projects || []).length - before;
  S.runs.push({ at: now, by: (currentUser() || {}).name || "", files: [...new Set(plan.tasks.concat(plan.review).map((t) => t.row.file))], rows: plan.totals.rows, created: out.created, updated: out.updated, same: out.same, flagged: out.flagged, waiting: out.waiting, refused: out.refused, steps: out.steps, projects: out.projects });
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
  if (!x || !who || !x.projects.length || x.refused) return null;
  const r = aimWrite(x.t, { projects: x.projects }, appNowIso(), who);
  if (r && r.refused) return (x.why = r.refused), (x.refused = "duplicate"), save(), null;
  return r && ((S.pending = S.pending.filter((y) => y !== x)), save()), r;
}
// The person Asana names joins the team here (the owner's call on the review screen): their rows become their tasks.
// The sign-in invitation is sent from Settings › Team Accounts, where they now appear.
const aimMayAdd = () => ["owner", "coord"].includes(role());
function aimAddPerson(name, email, rl) {
  if (!aimMayAdd()) return toast("Only the owner or the coordinator adds a person"), null;
  const nm = aimNorm(name),
    em = String(email || "").trim().toLowerCase();
  if (!nm) return null;
  let u = aimMatch(nm, em);
  u = u ? u.u : null;
  if (!u) {
    u = { id: uid("u"), name: nm, role: rl || "pm", contact: em };
    (DB.users = DB.users || []).push(u);
    try {
      audit("user", u.id, "added", "", `${nm} (${ROLE_NAMES[u.role] || u.role})`, "from the Asana import");
    } catch (e) {}
  }
  return u;
}

// ---- the screen: on Your Own Data (owner) ----------------------------------------------------------------------------
let aimFiles = [],
  aimPlanNow = null,
  aimPrefix = {},
  aimOwners = {};
const AIM_ROLES = ["pm", "coord", "billing", "controller", "designer"];
function aimPersonSelect(attr, val) {
  return `<select ${attr}><option value="">Pick the owner</option>${aimPeople()
    .map((u) => `<option value="${esc(u.id)}" ${u.id === val ? "selected" : ""}>${esc(u.name)}</option>`)
    .join("")}</select>`;
}
const aimS = (n, one, many) => `${n} ${1 === n ? one : many || one + "s"}`;
// The plan before anything is written, checkable in a minute: the projects and their counts, the keys kept, the owners
// matched and not, the due dates, and anything refused; then every row with its key, owner and due date.
function aimHtml() {
  const S = aimStore(),
    L = aimPlanNow,
    T = L && L.totals;
  const head = `<div class="card" id="aim-card"><h3>Import from Asana</h3>
    <p class="small muted">In Asana, open each project's menu, choose Export, then CSV. Pick the files here: nothing is written until you have looked at the summary. The team board's export works too: each row goes to the project in its PROJECT NAME ("General" is the Office list). Every task keeps its key exactly as the team wrote it (PAT-02 stays PAT-02), and its owner is the person Asana names. Someone who is not on the team here waits on this screen for you to pick the owner or add them.</p>
    <div class="row" style="gap:8px;flex-wrap:wrap"><label class="btn">Choose CSV Files<input type="file" id="aim-file" accept=".csv,text/csv" multiple hidden></label>${aimFiles.length ? `<span class="small muted">${aimFiles.length} file${1 === aimFiles.length ? "" : "s"}: ${aimFiles.map((f) => esc(f.name)).join(", ")}</span>` : ""}</div>`;
  if (!L) return head + aimPendingHtml(S) + "</div>";
  const tie = T.tasks + T.steps + T.review + T.orphans + T.duplicates,
    un = L.people.filter((x) => x.waiting && !x.here),
    made = L.tasks.concat(L.review).filter((t) => t.made);
  const body = `${L.errors.length ? `<div class="note warn">${L.errors.map(esc).join("<br>")}</div>` : ""}
    <div class="note" id="aim-tie">${aimS(T.rows, "row")} read: ${aimS(T.tasks, "task")} (${T.create} new, ${T.update} updated, ${T.same} unchanged; ${T.done} done), ${aimS(T.steps, "checklist step")}, ${T.review} waiting on this screen (${T.waitingOwner} for an owner${T.refused ? `, ${T.refused} refused` : ""}${T.noProject ? `, ${T.noProject} with no project` : ""})${T.orphans ? `, ${aimS(T.orphans, "subtask")} whose parent is not in these files` : ""}${T.duplicates ? `, ${T.duplicates} repeated in a second file` : ""}. ${tie === T.rows ? "Nothing is lost." : `<b>${T.rows - tie} unaccounted for.</b>`}</div>
    <ul class="small" id="aim-check" style="margin:8px 0 0;padding-left:18px">
      <li id="aim-keys">Keys: ${T.keysKept} kept exactly as written${T.keysMade ? `; ${T.keysMade} new for rows with none (${made.map((t) => esc(t.code)).join(", ")})` : ""}.</li>
      <li id="aim-owners">Owners: ${T.byEmail} matched by email, ${T.byName} by full name${T.tasks - T.byEmail - T.byName ? `, ${T.tasks - T.byEmail - T.byName} kept from the task already here` : ""}${un.length ? `; <b>not on the team here:</b> ${un.map((x) => `${esc(x.name)}${x.email ? ` (${esc(x.email)})` : ""}, ${x.waiting}`).join("; ")}` : "; everyone Asana names is on the team"}.</li>
      <li id="aim-due">Due dates: ${T.due} kept${T.noDue ? `, ${T.noDue} with none in Asana` : ""}.</li>
      ${T.refused ? `<li id="aim-refused"><b>Refused:</b> ${L.review.filter((t) => t.refused).map((t) => esc(t.why)).join("; ")}.</li>` : ""}
    </ul>
    <div class="tw" style="margin-top:10px"><table class="t" id="aim-projects"><thead><tr><th>Project</th><th>Prefix</th><th>Here</th><th class="r">New</th><th class="r">Updated</th><th class="r">Done</th><th class="r">Keys Kept</th><th class="r">Need an Owner</th></tr></thead><tbody>${L.projects
      .map(
        (P) =>
          `<tr><td>${esc(P.name)}</td><td><input class="aim-pfx" data-aimpfx="${esc(P.name)}" value="${esc(P.prefix)}" size="5" aria-label="Prefix for ${esc(P.name)}"></td><td class="small">${P.firm ? "The firm's list" : P.projectId ? "Matched" : "New project"}</td><td class="r">${P.create}</td><td class="r">${P.update}</td><td class="r">${P.done}</td><td class="r">${P.kept}</td><td class="r">${P.waiting}</td></tr>`,
      )
      .join("")}</tbody></table></div>
    <div class="tw" style="margin-top:10px"><table class="t" id="aim-people"><thead><tr><th>In Asana</th><th>Here</th><th class="r">Owns</th><th class="r">Need an Owner</th></tr></thead><tbody>${L.people
      .map((x) => `<tr><td>${esc(x.name)}${x.email ? `<div class="small muted">${esc(x.email)}</div>` : ""}</td><td class="small">${x.here ? `${esc(x.here)} <span class="muted">(by ${x.how === "email" ? "email" : "full name"})</span>` : '<span class="muted">Not on the team</span>'}</td><td class="r">${x.owner}</td><td class="r">${x.waiting}</td></tr>`)
      .join("")}</tbody></table></div>
    ${aimRowsHtml(L)}
    ${L.review.length ? aimReviewHtml(L.review, "plan") : ""}
    <div class="row" style="gap:8px;margin-top:12px;flex-wrap:wrap"><button class="btn ${rdRows && rdRows.length ? "" : "primary"}" id="aim-go">Import ${T.tasks + L.review.filter((t) => aimOwners[t.asanaId] && !t.refused).length} Task${1 === T.tasks ? "" : "s"}</button><button class="btn" id="aim-clear">Start Over</button></div>
    <p class="small muted" style="margin:6px 0 0">Running it again with the same export changes nothing; a newer export updates what changed in Asana and keeps what was changed here.</p>`;
  return head + body + "</div>";
}
// every row, by project: key, title, owner (or who it waits on), due date
function aimRowsHtml(L) {
  const by = new Map();
  L.tasks.concat(L.review).forEach((t) => {
    const k = t.project || "No project";
    by.has(k) || by.set(k, []);
    by.get(k).push(t);
  });
  return `<details id="aim-rows" open style="margin-top:10px"><summary class="small"><b>Every Row</b> <span class="muted">key, owner and due date</span></summary>${[...by]
    .map(
      ([pj, R]) =>
        `<div class="aim-grp" style="margin-top:6px"><div class="small"><b>${esc(pj)}</b> <span class="muted">${R.length}</span></div>${R.map(
          (t) =>
            `<div class="aim-line small" data-aimline="${esc(t.asanaId)}" style="padding:4px 0;border-top:1px solid var(--line,#e5e5e5)"><b class="aim-key">${esc(t.code || "No key")}</b> ${esc(t.title)}<div class="muted">${t.refused ? "Refused: duplicate key" : t.ownerName ? `${esc(t.ownerName)}${t.ownerHow === "kept" ? " (as here)" : ""}` : `Needs an owner${t.row.assignee ? `: ${esc(t.row.assignee)} in Asana` : ""}`} · ${t.row.due ? `due ${esc(fmt(t.row.due))}` : "no due date"}${t.done ? " · done" : ""}${t.row.pri3 ? ` · ${esc(t.row.pri3)}` : ""}${t.row.carried ? ` · ${esc(t.row.carried === "CARRIED" ? "Carried" : "New")}` : ""}</div></div>`,
        ).join("")}</div>`,
    )
    .join("")}</details>`;
}
// The rows waiting for an owner, by the person Asana names: pick the owner for all of theirs at once, or add them to
// the team; a refused row says why and how to fix it.
function aimReviewHtml(rows, mode) {
  const by = new Map();
  rows.forEach((t) => {
    const a = (t.row && t.row.assignee) || t.assignee || "",
      e = (t.row && t.row.email) || t.email || "",
      k = t.refused ? "refused" : !t.project ? "noproject" : a ? (e || a).toLowerCase() : "nobody";
    by.has(k) || by.set(k, { name: a, email: e, kind: k, L: [] });
    by.get(k).L.push(t);
  });
  const contact = (g) => {
    try {
      return aimContactOf(g.name, g.email);
    } catch (e) {
      return null;
    }
  };
  return `<div id="aim-review" style="margin-top:12px"><h4 style="margin:0 0 6px">Waiting for You</h4><p class="small muted" style="margin:0 0 8px">Every task has one team member who makes sure it gets done, and Asana names who. Someone outside the team stays on the task as Waiting On.</p>${[...by.values()]
    .map((g) => {
      const head =
        "refused" === g.kind
          ? `<b>Refused</b><span class="small muted">${aimS(g.L.length, "row")}: a key names one task</span>`
          : "noproject" === g.kind
            ? `<b>No project</b><span class="small muted">${aimS(g.L.length, "row")}</span>`
            : "nobody" === g.kind
              ? `<b>No one assigned in Asana</b><span class="small muted">${aimS(g.L.length, "row")}</span>`
              : `<b>${esc(g.name)}</b><span class="small muted">${g.email ? esc(g.email) + " · " : ""}${aimS(g.L.length, "row")}, not on the team here</span>`;
      const pick = /^(refused|noproject)$/.test(g.kind) ? "" : `<label class="small">All of these ${aimPersonSelect(`data-aimall="${esc(g.kind)}" data-aimmode="${mode}"`, "")}</label>`;
      const add = /^(refused|noproject|nobody)$/.test(g.kind) || contact(g) || !aimMayAdd() ? "" : `<div class="row aim-add" style="gap:8px;flex-wrap:wrap;align-items:center;margin-top:6px"><select data-aimrole="${esc(g.kind)}" aria-label="Role for ${esc(g.name)}">${AIM_ROLES.map((r) => `<option value="${r}">${esc(ROLE_NAMES[r] || r)}</option>`).join("")}</select><button class="btn" data-aimadd="${esc(g.kind)}" data-aimname="${esc(g.name)}" data-aimemail="${esc(g.email)}" data-aimmode="${mode}">Add ${esc(g.name)} to the Team</button></div>`;
      return `<div class="aim-grp" data-aimgrp="${esc(g.kind)}" style="margin-top:8px"><div class="row" style="gap:8px;flex-wrap:wrap;align-items:center">${head}<span class="grow"></span>${pick}</div>${add}
      ${g.L.map(
        (t) =>
          `<div class="aim-row" data-aimrow="${esc(t.asanaId)}"><div class="aim-t"><span class="small muted">${esc(t.code || "")}</span> ${esc(t.title)}<div class="small muted">${esc(t.project || "")}${t.project ? " · " : ""}${esc(t.why || "")}${t.row && t.row.due ? ` · due ${esc(fmt(t.row.due))}` : ""}${t.done ? " · done in Asana" : ""}</div></div>${t.project && !t.refused ? aimPersonSelect(`data-aimown="${esc(t.asanaId)}" data-aimmode="${mode}"`, aimOwners[t.asanaId] || "") : ""}</div>`,
      ).join("")}</div>`;
    })
    .join("")}</div>`;
}
function aimPendingHtml(S) {
  if (!S.pending.length) {
    const last = S.runs[S.runs.length - 1];
    return last ? `<p class="small muted" style="margin:10px 0 0">Last import ${esc(stampText(last.at))}${last.by ? " by " + esc(last.by) : ""}: ${last.created} new, ${last.updated} updated, ${last.waiting} waiting here.</p>` : "";
  }
  // a person added to the team since: their rows are offered to them, one tap to create
  S.pending.forEach((x) => {
    if (aimOwners[x.asanaId] || x.refused) return;
    const m = aimMatch(x.assignee || (x.t.row || {}).assignee, x.email || (x.t.row || {}).email);
    m && (aimOwners[x.asanaId] = m.u.id);
  });
  return aimReviewHtml(S.pending.map((x) => Object.assign({}, x.t, { why: x.why, refused: x.refused })), "pending") + `<div class="row" style="margin-top:10px"><button class="btn primary" id="aim-resolve">Create the Tasks with an Owner</button></div>`;
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
  const rowsOf = (mode) => ("pending" === mode ? aimStore().pending.map((x) => Object.assign({}, x.t, { refused: x.refused })) : (aimPlanNow && aimPlanNow.review) || []),
    grpOf = (t) => {
      const a = (t.row && t.row.assignee) || "",
        e = (t.row && t.row.email) || "";
      return t.refused ? "refused" : !t.project ? "noproject" : a ? (e || a).toLowerCase() : "nobody";
    };
  host.querySelectorAll("[data-aimown]").forEach((s) => (s.onchange = () => ((aimOwners[s.dataset.aimown] = s.value), "plan" === s.dataset.aimmode && renderRealData())));
  host.querySelectorAll("[data-aimall]").forEach(
    (s) =>
      (s.onchange = () => {
        rowsOf(s.dataset.aimmode)
          .filter((t) => grpOf(t) === s.dataset.aimall)
          .forEach((t) => (aimOwners[t.asanaId] = s.value));
        renderRealData();
      }),
  );
  host.querySelectorAll("[data-aimadd]").forEach(
    (b) =>
      (b.onclick = () => {
        const g = b.dataset.aimadd,
          rs = host.querySelector(`[data-aimrole="${CSS.escape(g)}"]`),
          u = aimAddPerson(b.dataset.aimname, b.dataset.aimemail, rs ? rs.value : "pm");
        if (!u) return;
        let n = 0;
        if ("pending" === b.dataset.aimmode) {
          rowsOf("pending")
            .filter((t) => grpOf(t) === g)
            .forEach((t) => aimResolve(t.asanaId, u.id) && n++);
        } else {
          aimPlanNow = aimPlan(aimFiles, { prefix: aimPrefix });
          n = aimPlanNow.tasks.filter((t) => t.ownerName === u.name).length;
        }
        save();
        toast(`${u.name} added to the team as ${ROLE_NAMES[u.role] || u.role}: ${aimS(n, "task")} ${"pending" === b.dataset.aimmode ? "created" : "will be"} theirs. Send the sign-in invitation from Settings, Team Accounts`, () => ((view = "proj"), render()));
        renderRealData();
      }),
  );
  const go = host.querySelector("#aim-go");
  go &&
    (go.onclick = () => {
      const r = aimApply(aimPlanNow, aimOwners);
      (aimPlanNow = null), (aimFiles = []), (aimOwners = {}), render();
      toast(
        `Imported: ${r.created} new task${1 === r.created ? "" : "s"}${r.updated ? `, ${r.updated} updated` : ""}${r.projects ? `, ${r.projects} new project${1 === r.projects ? "" : "s"}` : ""}${r.waiting ? `; ${r.waiting} wait on Your Own Data for an owner${r.refused ? ` (${r.refused} refused)` : ""}` : ""}`,
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
