/*<<taskviews.js>>*/
/* ==== task views: List, Table, Board and Calendar, filters and saved views per person (lane C, 2026-10-23) ===========
   Alan, 2026-10-23: "The current views for tasks in the platform are terrible except for boards and table, but the table
   needs updating as it looks like a spreadsheet", and "more modern than a spreadsheet and very easy to read, sort,
   filter". docs/TASKS_PLAN.md §2 item 5. The team walks the board project by project at the Monday and Thursday
   meeting, so the views are built for the coordinator who runs it, on a screen share and on the phone.
   What the leaders do and where this goes past them:
     - Linear's table and list (an ID per task, quiet one-line rows, the keyboard, a floating bar for what is selected,
       filter chips, views per person) and Asana's (groups that fold, cells that edit in place): the Table and the List.
       Past them: the Waiting On chip says who owes what and by when they promised it, the follow-up (the chase date)
       sits apart from the due date, and every date picker offers the next meeting, the date the team moves things to.
     - Notion's and Monday's tables (column chooser, widths, a summary on each group): kept, without the spreadsheet look:
       no cell borders, a faint line between rows, status as coloured pills, relative dates ("Today", "Tue",
       "3 days late"), full first names with an avatar, and a done/total bar on each project.
     - Trello's and ClickUp's board (status or project columns, drag, quick add): the Board, with Undo on every move and
       columns that swipe one at a time on the phone.
     - Calendars (month and week): due dates as solid chips coloured by project, follow-ups outlined; drag to re-date.
     - A task opens in a panel on the right at 1024px and wider, so the table stays in view (tkSheet itself, restyled).
   Design gate (BACKLOG §1.16). The noun is the task; its stores stay as they are behind tkItems() / tkAll(). The list is
   Tasks (view tkall): these are layouts of the same rows, the rows the list's chips count (tvRows: t2Pool and t2ViewOf,
   as t2Html reads them), so every view shows one number. No new store, list, queue or menu item:
     - the layouts ride on the existing mode switch (tkMode, data-tkmode): "cards" is the List (tasks.js's rows, by day,
       with the cells added on a wide screen), "table", "board" and "cal" are drawn here;
     - the filter chips are the list's own filters (tkWho, tkProject, tkArea, tkPri), shown as chips; search also reads
       the task's ID;
     - every row opens the one task sheet, tkSheet(key); the cells edit through the writers the sheet uses (tkSetDue,
       tdySetOwner and tdyHandOff, tkToggle through tkCheckDone and its proof gate) and log on rec.thread;
     - saved views, the table's columns, widths, sort, grouping and density are the person's own settings, kept with
       their assistant's record (DB.asst[uid].tkViews), theirs alone (their private shard on the hosted copy), so one
       person's views never change another's;
     - the fields the meeting adds (lane A: key, waitingOn, followUp, watchUntil, status waiting and fyi, order,
       comments, lastDiscussed) are read defensively from the record and written only where a cell edits them.
--------------------------------------------------------------------------------------------------------------------- */
const TV_MODES = [
  ["cards", "List"],
  ["table", "Table"],
  ["board", "Board"],
  ["cal", "Calendar"],
];
const TV_OWN = ["table", "board", "cal"];
const TV_STATUS = [
  ["todo", "To Do"],
  ["doing", "Doing"],
  ["waiting", "Waiting On"],
  ["done", "Done"],
  ["fyi", "FYI"],
];
const TV_STATUS_SAY = Object.fromEntries(TV_STATUS);
// who reassigns in place (the meeting's chair and the managers); anyone else offers it and the other person accepts
const TV_ASSIGNERS = ["owner", "pm", "coord"];
const TV_IC = {
  chevR: '<path d="M9 6l6 6-6 6"/>',
  chevD: '<path d="M6 9l6 6 6-6"/>',
  chevL: '<path d="M15 6l-6 6 6 6"/>',
  up: '<path d="M12 19V5"/><path d="M6 11l6-6 6 6"/>',
  down: '<path d="M12 5v14"/><path d="M6 13l6 6 6-6"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  wait: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l-3 2"/>',
  cols: '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M9.5 4.5v15M15 4.5v15"/>',
  user: '<circle cx="12" cy="8.5" r="3.6"/><path d="M5 20c1.2-3.6 4-5.4 7-5.4s5.8 1.8 7 5.4"/>',
  filter: '<path d="M4 5h16l-6 7.5V19l-4-2v-4.5z"/>',
};
const tvSvg = (k, s) => `<svg viewBox="0 0 24 24" width="${s || 16}" height="${s || 16}" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${TV_IC[k] || ""}</svg>`;
const tvMine = () => TV_OWN.includes(tkMode);
// the field keeps its one-job screens: the layouts, filters and saved views are the office's
const tvMayUse = () => {
  try {
    return !/^(foreman|crew|driver|client)$/.test(role());
  } catch (e) {
    return !1;
  }
};
const tvPhone = () => ("function" == typeof isMobile ? isMobile() : !1);
const tvOnTasks = () => "tkall" === view || !!T2_SCOPED[view];
const tvMonth = (s) => {
  const d = parse(s);
  return d ? d.toLocaleDateString("en-US", { month: "short" }) : "";
};
// "Sep 5" (the year only when it is not the app's)
function tvD(s) {
  const d = parse(s);
  if (!d) return "";
  return `${tvMonth(s)} ${d.getDate()}${d.getFullYear() !== fmtYear() ? ` ${d.getFullYear()}` : ""}`;
}
// relative: "3 days late", "Today", "Tomorrow", "Tue", then "Sep 12"
function tvRel(s, noLate) {
  if (!s) return "";
  const n = dayDiff(today(), s);
  if (n < 0 && !noLate) return `${-n} day${-1 === n ? "" : "s"} late`;
  if (0 === n) return "Today";
  if (1 === n) return "Tomorrow";
  if (n > 1 && n < 7) return DOW[parse(s).getDay()];
  return tvD(s);
}
// a promise date as people say it: "Thu 10/29"
const tvDay = (s) => {
  const d = parse(s);
  return d ? `${DOW[d.getDay()]} ${d.getMonth() + 1}/${d.getDate()}` : "";
};
const tvHash = (s) => {
  let h = 0;
  for (const c of String(s || "")) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return h;
};
const TV_HUES = [212, 152, 28, 272, 340, 190, 96, 4];
const tvHue = (s) => TV_HUES[tvHash(s) % TV_HUES.length];
const tvAv = (name) => (name ? `<span class="tv-av" style="--h:${tvHue(name)}" aria-hidden="true">${tvSvg("user", 13)}</span>` : "");

// ---- the person's own settings ---------------------------------------------------------------------------------------
function tvPrefs() {
  let A = null;
  try {
    A = paInit();
  } catch (e) {}
  if (!A) return { views: [], table: {}, folded: {}, boardBy: "status", calMode: "" };
  const P = (A.tkViews = A.tkViews && "object" == typeof A.tkViews ? A.tkViews : {});
  Array.isArray(P.views) || (P.views = []);
  (P.table && "object" == typeof P.table) || (P.table = {});
  (P.folded && "object" == typeof P.folded) || (P.folded = {});
  P.boardBy || (P.boardBy = "status");
  return P;
}
const tvTableGroup = () => {
  const g = tvPrefs().table.group;
  return null == g ? "project" : g;
};
const tvDense = () => "compact" === tvPrefs().table.density;

// ---- the rows: exactly the list's rows (the chip's number) -----------------------------------------------------------
function tvRows() {
  try {
    if ("done" === t2View) return t2DonePool();
    return t2Sort(t2ViewOf(t2Pool(), t2View));
  } catch (e) {
    console.warn("task views rows", e);
    return [];
  }
}
function tvRec(x) {
  try {
    return tdyRec(x);
  } catch (e) {
    return null;
  }
}
// The task's ID ("PAD-23"): the meeting's key on the record (lane A), else the board's code (the Asana import)
function tvRef(x, rec) {
  const k = rec && rec.key;
  if ("string" == typeof k && /^[A-Z][A-Z0-9]{0,7}-\d+$/.test(k)) return k;
  return x.code || "";
}
function tvWaitOf(x, rec) {
  const w = rec && rec.waitingOn;
  if (w && "object" == typeof w && w.name) return { name: w.name, what: w.what || "", promised: w.promised || "" };
  if ("string" == typeof w && w) return { name: w, what: "", promised: "" };
  return x.waitsOn ? { name: x.waitsOn, what: "", promised: "" } : null;
}
function tvStatusOf(x, rec) {
  if (x.done) return "done";
  const s = String((rec && rec.status) || x.status || "");
  if ("fyi" === s) return "fyi";
  if (x.waitsOn) return "waiting";
  if ("doing" === s || "in-progress" === s) return "doing";
  return "todo";
}
// the latest word on the task: a comment (lane A's comments, else the thread's notes)
function tvLatest(rec) {
  if (!rec) return null;
  const C = Array.isArray(rec.comments) ? rec.comments.filter((c) => c && (c.text || c.body)) : [];
  if (C.length) {
    const c = C[C.length - 1];
    return { by: c.by || c.who || "", text: c.text || c.body };
  }
  const T = Array.isArray(rec.thread) ? rec.thread.filter((e) => e && e.text) : [];
  if (T.length) return { by: T[T.length - 1].by || "", text: T[T.length - 1].text };
  return null;
}
// what each kind of task can change in place; anything else opens the sheet
const TV_CAN = {
  due: (x) => TK_DUE_KINDS.test(x.kind),
  owner: (x) => /^(action|firm|hub|issue)$/.test(x.kind),
  status: (x) => /^(action|firm|sched)$/.test(x.kind),
  follow: (x) => /^(action|firm|hub)$/.test(x.kind),
  wait: (x) => /^(action|firm)$/.test(x.kind),
};
function tvProjectOf(x) {
  if ("hub" === x.kind || "lead" === x.kind) return { id: "__sales", name: "Sales" };
  if ("firm" === x.kind) return { id: "firm:" + (x.board || "Office"), name: x.board || "Office" };
  if (x.projectId) {
    const p = (DB.projects || []).find((q) => q.id === x.projectId);
    return { id: x.projectId, name: p ? shortName(p) : x.project || "A Job" };
  }
  return { id: "__firm", name: x.project || "Firm-wide" };
}
function tvOwnerName(x) {
  if (x.ownerUid) {
    const u = (DB.users || []).find((y) => y.id === x.ownerUid);
    if (u && u.name) return u.name;
  }
  return x.owner || x.assignee || "";
}
function tvInfo(x) {
  const rec = tvRec(x),
    P = tvProjectOf(x),
    num = (v) => ("number" == typeof v ? v : "string" == typeof v && v !== "" && !isNaN(+v) ? +v : null),
    ld = rec && rec.lastDiscussed;
  return {
    x: x,
    rec: rec,
    key: t2Key(x),
    ref: tvRef(x, rec),
    owner: tvOwnerName(x),
    status: tvStatusOf(x, rec),
    wait: tvWaitOf(x, rec),
    follow: (rec && rec.followUp) || x.followUp || "",
    watch: (rec && rec.watchUntil) || x.watchUntil || "",
    last: ld ? ("string" == typeof ld ? ld : ld.date || ld.at || "") : "",
    latest: tvLatest(rec),
    order: num(rec && rec.order),
    pid: P.id,
    pname: P.name,
    section: x.section || (rec && rec.section) || "",
  };
}
function tvFind(key) {
  try {
    const R = tkResolve(key);
    return R ? tvInfo(R.x) : null;
  } catch (e) {
    return null;
  }
}

// ---- the next meeting: the team meets Monday and Thursday (Alan, 10-23); Meeting Mode may name its own date ---------
function tvNextMeeting() {
  try {
    if ("function" == typeof mmNextMeetingDate) {
      const d = mmNextMeetingDate();
      if (d) return d;
    }
  } catch (e) {}
  const days = (DB.company && Array.isArray(DB.company.meetingDays) && DB.company.meetingDays.length ? DB.company.meetingDays : [1, 4]).map(Number),
    td = today();
  for (let i = 1; i <= 7; i++) {
    const d = addDays(parse(td), i);
    if (days.includes(d.getDay())) return iso(d);
  }
  return iso(addDays(parse(td), 7));
}
function tvDateChoices(withClear) {
  const td = today(),
    L = [
      ["Today", td],
      ["Tomorrow", iso(addDays(parse(td), 1))],
      ["Next Meeting", tvNextMeeting()],
      ["Next Week", addWork(td, 5)],
    ];
  withClear && L.push(["No Date", ""]);
  return L;
}

// ---- writers: each logs on the task's thread, audits, saves, and toasts with Open and Undo ---------------------------
function tvKeep(rec, fields) {
  const was = {};
  fields.forEach((f) => (was[f] = rec && Object.prototype.hasOwnProperty.call(rec, f) ? JSON.parse(JSON.stringify(undefined === rec[f] ? null : rec[f])) : undefined));
  return () => {
    if (!rec) return;
    fields.forEach((f) => (undefined === was[f] ? delete rec[f] : (rec[f] = was[f])));
  };
}
function tvRedraw() {
  try {
    tvOnTasks() ? renderTkAll() : render();
  } catch (e) {}
}
function tvDone(msg, key, undo) {
  save();
  tvRedraw();
  const L = [{ label: "Open", run: () => tkOpen(key) }];
  undo &&
    L.push({
      label: "Undo",
      run: () => {
        undo();
        save();
        tvRedraw();
        toast("Put back as it was", [{ label: "Open", run: () => tkOpen(key) }]);
      },
    });
  toast(msg, L);
}
function tvCant(I, what) {
  toast(`${what} is changed from the task itself: opening it`);
  setTimeout(() => tkSheet(I.key), 0);
  return !1;
}
const tvTitle = (x) => tdWords(x.title || "", 8);
function tvAudit(x, field, from, to) {
  try {
    audit("task", x.id, field, null == from ? "" : String(from), null == to ? "" : String(to), "");
  } catch (e) {}
}
function tvSetDue(I, date, quiet) {
  const x = I.x,
    rec = I.rec;
  if (!TV_CAN.due(x)) return quiet ? null : tvCant(I, "This date");
  const was = x.due || "",
    lead = "lead" === x.kind ? (DB.leads || []).find((y) => y.id === x.id) : null,
    undo = lead ? ((w) => () => (lead.nextDue = w))(lead.nextDue) : tvKeep(rec, ["due", "modifiedAt"]);
  if ((date || "") === was) return quiet ? null : !1;
  if (!tkSetDue({ key: I.key, x: x, rec: rec }, date || "")) return quiet ? null : !1;
  if (quiet) return undo;
  tvDone(date ? `Due ${fmtL(date)}: ${tvTitle(x)}${was ? ` (was ${fmtL(was)})` : ""}` : `No date now: ${tvTitle(x)}`, I.key, undo);
  return !0;
}
function tvSetField(I, field, val, label) {
  const x = I.x,
    rec = I.rec;
  if (!rec) return tvCant(I, label);
  const was = rec[field],
    undo = tvKeep(rec, [field]);
  if ((was || "") === (val || "")) return !1;
  val ? (rec[field] = val) : delete rec[field];
  tkLog(rec, { ev: field, from: was || "", to: val || "" });
  tvAudit(x, field, was, val);
  const say = { followUp: "Follow up", watchUntil: "Watch until" }[field] || label;
  tvDone(val ? `${say} ${fmtL(val)}: ${tvTitle(x)}` : `${say} cleared: ${tvTitle(x)}`, I.key, undo);
  return !0;
}
function tvSetOwner(I, name, quiet) {
  const x = I.x,
    rec = I.rec;
  if (!TV_CAN.owner(x) || !rec) return quiet ? null : tvCant(I, "The owner");
  // anyone but the chair and the managers offers it: it stays theirs until the other person accepts
  if (!TV_ASSIGNERS.includes(role())) return quiet ? null : tdyHandOff(x, name, "");
  const f = TDY_OWNER_FIELD[x.kind] || "assignee",
    was = rec[f] || x.owner || "",
    undo = tvKeep(rec, [f, "handoff"]);
  if (!name || name === was) return quiet ? null : !1;
  tdySetOwner(x, rec, name);
  rec.handoff && "offered" === rec.handoff.state && (rec.handoff = Object.assign({}, rec.handoff, { state: "withdrawn", decidedAt: appNowIso() }));
  tkLog(rec, { ev: "owner", from: was, to: name });
  tvAudit(x, "owner", was, name);
  if (quiet) return undo;
  tvDone(`${tkFirst(name)} owns it now: ${tvTitle(x)}${was ? ` (was ${tkFirst(was)})` : ""}`, I.key, undo);
  return !0;
}
// Done in bulk skips a task the Standard needs proof for: that one is closed from its own sheet, with the proof
function tvProofHeld(I) {
  try {
    const need = tdyProofNeed(I.x, I.rec);
    return !!need && !tdyProofMet(I.x, need, I.rec);
  } catch (e) {
    return !1;
  }
}
// status: To Do, Doing, Waiting On, FYI on the task; Done through the list's own Done (the Standard's proof gate)
function tvSetStatus(I, st, opt) {
  const O = opt || {},
    x = I.x,
    rec = I.rec,
    was = I.status;
  if (st === was) return O.quiet ? null : !1;
  const [kk, ki, kp] = I.key.split(":");
  if ("done" === st) {
    if (!O.quiet) return tkCheckDone(I.key), !0;
    if (tvProofHeld(I) || /^(ob|lead|draft)$/.test(x.kind)) return null;
    tkToggle(kk, ki, kp || "");
    const now = tkItems().find((y) => t2Key(y) === I.key);
    return now && now.done ? () => tkToggle(kk, ki, kp || "") : null;
  }
  if (!TV_CAN.status(x) || !rec) return O.quiet ? null : tvCant(I, "This status");
  if ("sched" === x.kind && !/^(todo|doing)$/.test(st)) return O.quiet ? null : tvCant(I, "A schedule line's status");
  if ("waiting" === st && !(I.wait && I.wait.name)) return O.quiet ? null : tvEditWait(I, O.anchor);
  const undo = tvKeep(rec, ["status", "waitsOn", "waitingOn", "completedAt", "actualEnd", "actualStart", "modifiedAt"]);
  "done" === was && tkToggle(kk, ki, kp || "");
  if ("sched" === x.kind) {
    rec.status = "doing" === st ? "in-progress" : "planned";
    "doing" === st && (rec.actualStart || (rec.actualStart = today()));
  } else {
    rec.status = st;
    "firm" === x.kind && (rec.modifiedAt = today());
    if ("waiting" !== st && I.wait) {
      // no longer waiting: what was owed stays on the thread
      tkLog(rec, { ev: "waiting", was: I.wait });
      rec.waitsOn = "";
      rec.waitingOn = null;
    }
  }
  tkLog(rec, { ev: "status", from: was, to: st });
  tvAudit(x, "status", was, st);
  if (O.quiet) return undo;
  tvDone(`${TV_STATUS_SAY[st]}: ${tvTitle(x)}`, I.key, undo);
  return !0;
}
function tvSetWait(I, W) {
  const x = I.x,
    rec = I.rec;
  if (!TV_CAN.wait(x) || !rec) return tvCant(I, "Waiting On");
  const undo = tvKeep(rec, ["waitsOn", "waitingOn", "status"]),
    was = I.wait;
  if (W && W.name) {
    const prev = rec.waitingOn && "object" == typeof rec.waitingOn ? rec.waitingOn : {};
    rec.waitingOn = Object.assign({}, prev, { name: W.name, what: W.what || "", promised: W.promised || "", since: prev.since || today(), by: tdyMe().name || "" });
    rec.waitsOn = W.name;
    "done" !== rec.status && (rec.status = "waiting");
  } else {
    rec.waitingOn = null;
    rec.waitsOn = "";
    "waiting" === rec.status && (rec.status = "todo");
  }
  tkLog(rec, { ev: "waiting", was: was || null, to: W && W.name ? W : null });
  tvAudit(x, "waitingOn", was && was.name, W && W.name);
  tvDone(W && W.name ? `Waiting on ${W.name}${W.promised ? `, promised ${fmtL(W.promised)}` : ""}: ${tvTitle(x)}` : `Not waiting on anyone now: ${tvTitle(x)}`, I.key, undo);
  return !0;
}
// a job's to-do moves to another job (the board by project); its ID stays, as the board's import keeps it
function tvSetProject(I, pid) {
  const x = I.x;
  if ("action" !== x.kind || !pid || 0 === pid.indexOf("_") || 0 === pid.indexOf("firm:")) return tvCant(I, "The job");
  const from = (DB.projects || []).find((p) => p.id === x.projectId),
    to = (DB.projects || []).find((p) => p.id === pid);
  if (!from || !to || from === to) return !1;
  const i = (from.actions || []).findIndex((a) => a.id === x.id);
  if (i < 0) return !1;
  const a = from.actions.splice(i, 1)[0];
  (to.actions = to.actions || []).push(a);
  tkLog(a, { ev: "job", from: shortName(from), to: shortName(to) });
  tvAudit(x, "job", shortName(from), shortName(to));
  tvDone(`Moved to ${shortName(to)}: ${tvTitle(x)}`, `action:${x.id}:${to.id}`, () => {
    const j = (to.actions || []).findIndex((y) => y.id === a.id);
    j >= 0 && to.actions.splice(j, 1), from.actions.push(a);
  });
  return !0;
}
// a task made here must be on the screen that made it (BACKLOG §1.16 layer 3): if the filters hide it, they open up
function tvMakeFindable(key) {
  if (tvRows().some((x) => t2Key(x) === key)) return;
  "me" === tkWho || "all" === tkWho || (tkWho = "all");
  "done" !== t2View && (t2View = "all");
  tkArea = "";
  tkPri = "";
  t2Q = "";
}
function tvQuickAdd(col, title) {
  const by = tvPrefs().boardBy,
    me = tdyMe(),
    real = (id) => (DB.projects || []).some((p) => p.id === id),
    pid = "project" === by ? (real(col) ? col : "") : real(tkProject) ? tkProject : "";
  if ("project" === by && "__sales" === col) return toast("A sales task is added from Sales");
  const m = crCreateTask({ title: title, for: pid ? "p:" + pid : "firm", assignee: me.name || tkMe(), due: "" });
  if (!m) return;
  const key = `${m.kind}:${m.id}:${m.projectId || ""}`;
  const I = tvFind(key);
  if (I && "status" === by && /^(doing|fyi)$/.test(col) && I.rec) I.rec.status = col;
  save();
  tvMakeFindable(key);
  try {
    crFlash = m.id;
    crFlashUntil = Date.now() + 4e3;
  } catch (e) {}
  renderTkAll();
  toast(`Added: ${tdWords(title, 8)}${pid ? ` on ${shortName((DB.projects || []).find((p) => p.id === pid))}` : ""}`, [{ label: "Open", run: () => tkOpen(key) }]);
  if ("status" === by && "waiting" === col) {
    const J = tvFind(key),
      card = document.querySelector(`#tkall-body [data-tvrow="${CSS.escape(key)}"]`);
    J && setTimeout(() => tvEditWait(J, card), 0);
  }
}

// ---- one small picker: a popover by the cell on a wide screen, a sheet from the bottom on the phone ------------------
let tvPopAnchor = null;
function tvPopClose(back) {
  const d = document.getElementById("tv-pop");
  d && d.remove();
  document.removeEventListener("mousedown", tvPopOut, !0);
  document.removeEventListener("keydown", tvPopKey, !0);
  back && tvPopAnchor && document.body.contains(tvPopAnchor) && tvPopAnchor.focus();
  tvPopAnchor = null;
}
function tvPopOut(e) {
  const d = document.getElementById("tv-pop");
  d && !d.contains(e.target) && tvPopClose();
}
function tvPopKey(e) {
  "Escape" === e.key && (e.preventDefault(), e.stopPropagation(), tvPopClose(!0));
}
function tvPop(anchor, title, html, wire) {
  tvPopClose();
  const d = document.createElement("div"),
    ph = tvPhone();
  d.id = "tv-pop";
  d.className = "tv-pop" + (ph ? " tv-pop-sheet" : "");
  d.setAttribute("role", "dialog");
  d.setAttribute("aria-label", title);
  d.innerHTML = `<div class="tv-pop-hd"><b>${esc(title)}</b><button type="button" class="tv-pop-x" data-tvpx aria-label="Close" title="Close">${tvSvg("x", 18)}</button></div><div class="tv-pop-bd">${html}</div>`;
  document.body.appendChild(d);
  tvPopAnchor = anchor || null;
  if (!ph) {
    const w = d.offsetWidth,
      h = d.offsetHeight,
      W = vw(),
      H = window.innerHeight;
    if (anchor && anchor.getBoundingClientRect && document.body.contains(anchor)) {
      const r = anchor.getBoundingClientRect();
      let top = r.bottom + 6;
      top + h > H - 8 && (top = Math.max(8, r.top - h - 6));
      d.style.left = Math.min(Math.max(8, r.left), W - w - 8) + "px";
      d.style.top = top + "px";
    } else {
      d.style.left = Math.max(8, (W - w) / 2) + "px";
      d.style.top = Math.max(8, (H - h) / 3) + "px";
    }
  }
  d.querySelector("[data-tvpx]").onclick = () => tvPopClose(!0);
  setTimeout(() => document.addEventListener("mousedown", tvPopOut, !0), 0);
  document.addEventListener("keydown", tvPopKey, !0);
  try {
    wire && wire(d);
  } catch (e) {
    console.warn("task picker", e);
  }
  const first = d.querySelector("[data-tvfirst]") || d.querySelector(".tv-pop-bd button");
  !ph && first && first.focus();
  return d;
}
function tvDatePop(anchor, title, cur, apply, withClear) {
  const L = tvDateChoices(withClear);
  return tvPop(
    anchor,
    title,
    `<div class="tv-chips">${L.map(([n, d], i) => `<button type="button" class="tv-chip ${cur === d && (d || withClear) ? "on" : ""}" data-tvd="${d}" ${0 === i ? "data-tvfirst" : ""}>${n}${d ? `<small>${esc(tvDay(d))}</small>` : ""}</button>`).join("")}<label class="tv-chip tv-pick">Pick<small>a day</small><input type="date" data-tvdpick value="${esc(cur || "")}" aria-label="Pick a day"></label></div>`,
    (d) => {
      d.querySelectorAll("[data-tvd]").forEach((b) => (b.onclick = () => (tvPopClose(), apply(b.dataset.tvd))));
      const p = d.querySelector("[data-tvdpick]");
      p && (p.onchange = () => p.value && (tvPopClose(), apply(p.value)));
    },
  );
}
function tvPeople() {
  try {
    return tdyUsers()
      .filter((u) => "client" !== u.role)
      .sort((a, b) => (/^(crew|driver)$/.test(a.role) ? 1 : 0) - (/^(crew|driver)$/.test(b.role) ? 1 : 0) || a.name.localeCompare(b.name));
  } catch (e) {
    return [];
  }
}
// a person picker with search: type a few letters, the list narrows
function tvPersonPop(anchor, cur, apply, title, list) {
  const P = list || tvPeople().map((u) => ({ name: u.name, sub: TK_ROLE_SAY[u.role] || "" })),
    may = TV_ASSIGNERS.includes(role());
  return tvPop(
    anchor,
    title || (may ? "Owner" : "Offer It To"),
    `${!list && !may ? '<p class="small muted tv-pop-note">It stays yours until they accept.</p>' : ""}<input class="tv-psearch" data-tvpq placeholder="Search people" aria-label="Search people" autocomplete="off"><div class="tv-people">${P.map((u, i) => `<button type="button" class="tv-person ${cur && tkOwnerMatch(cur, u.name) ? "on" : ""}" data-tvp="${esc(u.name)}" ${0 === i ? "data-tvfirst" : ""}>${tvAv(u.name)}<span class="grow"><b>${esc(u.name)}</b>${u.sub ? `<small>${esc(u.sub)}</small>` : ""}</span></button>`).join("")}</div>`,
    (d) => {
      d.querySelectorAll("[data-tvp]").forEach((b) => (b.onclick = () => (tvPopClose(), apply(b.dataset.tvp))));
      const q = d.querySelector("[data-tvpq]");
      q.oninput = () => {
        const s = q.value.trim().toLowerCase();
        d.querySelectorAll("[data-tvp]").forEach((b) => (b.hidden = !!s && !b.dataset.tvp.toLowerCase().includes(s)));
      };
      q.onkeydown = (e) => {
        if ("Enter" !== e.key) return;
        e.preventDefault();
        const b = [...d.querySelectorAll("[data-tvp]")].find((y) => !y.hidden);
        b && b.click();
      };
      tvPhone() || setTimeout(() => q.focus(), 0);
    },
  );
}
function tvStatusPop(anchor, I, apply) {
  const can = (k) => "done" === k || (TV_CAN.status(I.x) && ("sched" !== I.x.kind || /^(todo|doing)$/.test(k)));
  return tvPop(
    anchor,
    "Status",
    `<div class="tv-menu">${TV_STATUS.filter(([k]) => can(k))
      .map(([k, n], i) => `<button type="button" class="tv-mi ${I.status === k ? "on" : ""}" data-tvs="${k}" ${0 === i ? "data-tvfirst" : ""}><span class="tv-pill tv-st-${k}">${n}</span></button>`)
      .join("")}</div>`,
    (d) => d.querySelectorAll("[data-tvs]").forEach((b) => (b.onclick = () => (tvPopClose(), apply(b.dataset.tvs)))),
  );
}
function tvEditWait(I, anchor) {
  const W = I.wait || { name: "", what: "", promised: "" },
    names = [...new Set([].concat((DB.vendors || []).map((v) => v && v.name), (DB.clients || []).map((c) => c && c.name)).filter(Boolean))].slice(0, 400),
    dates = tvDateChoices(!1).slice(0, 3);
  tvPop(
    anchor,
    "Waiting On",
    `<label class="tv-f"><span>Who owes it</span><input data-tvw="name" list="tv-wnames" value="${esc(W.name)}" placeholder="A vendor, consultant, designer or client" autocomplete="off"></label><datalist id="tv-wnames">${names.map((n) => `<option value="${esc(n)}">`).join("")}</datalist>
<label class="tv-f"><span>What they owe</span><input data-tvw="what" value="${esc(W.what)}" placeholder="The quote, the drawings, a date"></label>
<div class="tv-f"><span>Promised by</span><div class="tv-chips">${dates.map(([n, d]) => `<button type="button" class="tv-chip ${W.promised === d ? "on" : ""}" data-tvwd="${d}">${n}<small>${esc(tvDay(d))}</small></button>`).join("")}<label class="tv-chip tv-pick">Pick<small>${W.promised && !dates.some(([, d]) => d === W.promised) ? esc(tvDay(W.promised)) : "a day"}</small><input type="date" data-tvwpick value="${esc(W.promised || "")}" aria-label="Pick the promised day"></label></div></div>
<div class="tv-pop-ft">${I.wait ? '<button type="button" class="btn" data-tvwclear>Not Waiting</button>' : ""}<button type="button" class="btn tv-go" data-tvwsave>Save</button></div>`,
    (d) => {
      let promised = W.promised || "";
      const mark = () => d.querySelectorAll("[data-tvwd]").forEach((b) => b.classList.toggle("on", b.dataset.tvwd === promised));
      d.querySelectorAll("[data-tvwd]").forEach((b) => (b.onclick = () => ((promised = promised === b.dataset.tvwd ? "" : b.dataset.tvwd), mark())));
      const p = d.querySelector("[data-tvwpick]");
      p && (p.onchange = () => ((promised = p.value), mark()));
      const val = (k) => ((d.querySelector(`[data-tvw="${k}"]`) || {}).value || "").trim();
      const go = () => {
        const name = val("name");
        if (!name) return toast("Say who it waits on");
        tvPopClose();
        tvSetWait(I, { name: name, what: val("what"), promised: promised });
      };
      d.querySelector("[data-tvwsave]").onclick = go;
      d.querySelectorAll("[data-tvw]").forEach((i) => i.addEventListener("keydown", (e) => "Enter" === e.key && (e.preventDefault(), go())));
      const c = d.querySelector("[data-tvwclear]");
      c && (c.onclick = () => (tvPopClose(), tvSetWait(I, null)));
      const n = d.querySelector('[data-tvw="name"]');
      n && !tvPhone() && setTimeout(() => n.focus(), 0);
    },
  );
  return !0;
}
// one cell's editor, by field
function tvEdit(key, field, anchor) {
  const I = tvFind(key);
  if (!I) return toast("That task is no longer here");
  if ("title" === field) return tkSheet(key);
  if ("due" === field) return TV_CAN.due(I.x) ? tvDatePop(anchor, "Due", I.x.due || "", (d) => tvSetDue(I, d), !0) : tvCant(I, "This date");
  if ("follow" === field) return TV_CAN.follow(I.x) ? tvDatePop(anchor, "Follow Up", I.follow, (d) => tvSetField(I, "followUp", d, "Follow-up"), !0) : tvCant(I, "The follow-up");
  if ("watch" === field) return TV_CAN.follow(I.x) ? tvDatePop(anchor, "Watch Until", I.watch, (d) => tvSetField(I, "watchUntil", d, "Watch until"), !0) : tvCant(I, "Watch until");
  if ("owner" === field) return TV_CAN.owner(I.x) && I.rec ? tvPersonPop(anchor, I.owner, (n) => tvSetOwner(I, n)) : tvCant(I, "The owner");
  if ("status" === field) return tvStatusPop(anchor, I, (s) => tvSetStatus(I, s, { anchor: anchor }));
  if ("wait" === field) return TV_CAN.wait(I.x) ? tvEditWait(I, anchor) : tvCant(I, "Waiting On");
  return tkSheet(key);
}

// ---- the cells: the same control and words in the List, the Table and the Board ---------------------------------------
function tvCell(I, field) {
  const x = I.x,
    td = today();
  if ("owner" === field) {
    const n = I.owner ? tkFirst(I.owner) : "";
    return `<button type="button" class="tv-c tv-own ${n ? "" : "tv-empty"}" data-tved="owner" aria-label="Owner: ${esc(I.owner || "nobody")}" title="${esc(I.owner || "")}">${n ? `${tvAv(I.owner)}<span>${esc(n)}</span>` : "No Owner"}</button>`;
  }
  if ("due" === field) {
    const d = x.due,
      late = d && d < td && !x.done;
    return `<button type="button" class="tv-c tv-due ${late ? "late" : d === td ? "today" : ""} ${d ? "" : "tv-empty"}" data-tved="due" aria-label="Due ${esc(d ? fmtL(d) : "no date")}" title="${esc(d ? fmtL(d) : "")}">${d ? esc(tvRel(d, x.done)) : "No Date"}</button>`;
  }
  if ("follow" === field) {
    const f = I.follow,
      late = f && f < td && !x.done;
    return `<button type="button" class="tv-c tv-fu ${late ? "late" : f === td ? "today" : ""} ${f ? "" : "tv-empty"}" data-tved="follow" aria-label="Follow up ${esc(f ? fmtL(f) : "not set")}" title="${esc(f ? fmtL(f) : "")}">${tvSvg("clock", 14)}<span>${f ? esc(tvRel(f, x.done)) : "Follow Up"}</span></button>`;
  }
  if ("watch" === field) {
    const f = I.watch;
    return `<button type="button" class="tv-c tv-watch ${f ? "" : "tv-empty"}" data-tved="watch" aria-label="Watch until ${esc(f ? fmtL(f) : "not set")}">${f ? esc(tvD(f)) : "Watch Until"}</button>`;
  }
  if ("status" === field) return `<button type="button" class="tv-c tv-stc" data-tved="status" aria-label="Status: ${esc(TV_STATUS_SAY[I.status])}"><span class="tv-pill tv-st-${I.status}">${esc(TV_STATUS_SAY[I.status])}</span></button>`;
  if ("wait" === field) {
    const W = I.wait;
    if (!W) return `<button type="button" class="tv-c tv-wait tv-empty" data-tved="wait" aria-label="Waiting on nobody: set it">${tvSvg("wait", 14)}<span>Waiting On</span></button>`;
    const late = W.promised && W.promised < td && !x.done,
      who = W.name.split(/\s+/).length > 2 ? W.name.split(/\s+/).slice(0, 2).join(" ") : W.name;
    return `<button type="button" class="tv-c tv-wait on ${late ? "late" : ""}" data-tved="wait" aria-label="Waiting on ${esc(W.name)}${W.what ? " for " + esc(W.what) : ""}${W.promised ? ", promised " + esc(fmtL(W.promised)) : ""}" title="${esc(W.what ? `${W.name}: ${W.what}` : W.name)}"><span class="tv-chip-in">${esc(who)}${W.promised ? ` · ${esc(tvDay(W.promised))}` : ""}</span></button>`;
  }
  return "";
}
const tvRefHtml = (I) => (I.ref ? `<span class="tv-ref">${esc(I.ref)}</span>` : "");
const tvCheck = (I) =>
  I.x.done
    ? '<span class="tv-check tv-donemark" aria-hidden="true"><span></span></span>'
    : `<button type="button" class="tv-check" data-tvdone="${esc(I.key)}" aria-label="Mark done" title="Mark done"><span></span></button>`;
const tvEditAttr = (x) => `data-edit="tk:${esc(x.kind)}|${esc(x.projectId || "")}|${esc(x.id)}"`;

// ---- grouping: Project (and its sections), Owner, Status, Due (Late, Today, This Week, Later), or none ------------------
const TV_GROUPS = [
  ["project", "By Project"],
  ["owner", "By Owner"],
  ["status", "By Status"],
  ["due", "By Due Date"],
  ["", "No Grouping"],
];
function tvProjOrder() {
  const o = {};
  (DB.projects || []).forEach((p, i) => (o[p.id] = i));
  return (id) => (id in o ? o[id] : "__sales" === id ? 9e3 : 0 === String(id).indexOf("firm:") ? 9e3 + 1 : 9e3 + 2);
}
function tvDueBucket(I) {
  const d = I.x.due,
    td = today();
  if (!d) return ["4", "No Date"];
  if (d < td) return ["0", "Late"];
  if (d === td) return ["1", "Today"];
  if (d <= iso(addDays(parse(td), 7))) return ["2", "This Week"];
  return ["3", "Later"];
}
function tvGroupKey(I, gb) {
  if ("project" === gb) return [I.pid, I.pname];
  if ("owner" === gb || "assignee" === gb) return [I.owner || "~", I.owner || "No Owner"];
  if ("status" === gb) return [String(TV_STATUS.findIndex(([k]) => k === I.status)), TV_STATUS_SAY[I.status]];
  if ("due" === gb) return tvDueBucket(I);
  try {
    return tkGroupOf(I.x, gb);
  } catch (e) {
    return ["", ""];
  }
}
function tvGroups(infos, gb, sections) {
  const out = [],
    at = {};
  if (!gb) return [{ k: "", n: "", rows: infos }];
  infos.forEach((I) => {
    const [k, n] = tvGroupKey(I, gb);
    let b = at[k];
    b || ((b = at[k] = { k: k, n: n, rows: [] }), out.push(b));
    b.rows.push(I);
  });
  if ("project" === gb) {
    const ord = tvProjOrder();
    out.sort((a, b) => ord(a.k) - ord(b.k) || String(a.n).localeCompare(String(b.n)));
    // sections inside a project, in the order they first appear; rows in the meeting's order where it is set
    sections &&
      out.forEach((g) => {
        const S = [],
          sat = {};
        g.rows.forEach((I) => {
          const s = I.section || "";
          let b = sat[s];
          b || ((b = sat[s] = { k: s, n: s, rows: [] }), S.push(b));
          b.rows.push(I);
        });
        S.sort((a, b) => (a.k ? 1 : 0) - (b.k ? 1 : 0));
        S.forEach((s) => s.rows.sort((a, b) => (null != a.order && null != b.order ? a.order - b.order : 0)));
        g.secs = S.length > 1 || (S[0] && S[0].k) ? S : null;
      });
  } else out.sort((a, b) => String(a.k).localeCompare(String(b.k)));
  return out;
}
const tvFolded = (gid) => !!tvPrefs().folded[gid];
function tvFold(gid) {
  const P = tvPrefs();
  P.folded[gid] ? delete P.folded[gid] : (P.folded[gid] = 1);
  save();
  tvKeepScroll(() => renderTkAll());
}
// a group's header: its name, its count, the late count and a thin bar of what is done of the whole
function tvGhd(gid, name, rows, doneN, cls) {
  const f = tvFolded(gid),
    late = rows.filter((I) => I.x.late && !I.x.done).length,
    open = rows.filter((I) => !I.x.done).length,
    tot = open + (doneN || 0),
    pct = tot ? Math.round((100 * (doneN || 0)) / tot) : 0;
  return `<button type="button" class="${cls || "tv-ghd"}" data-tvfold="${esc(gid)}" aria-expanded="${f ? "false" : "true"}">${tvSvg(f ? "chevR" : "chevD", 16)}<span class="tv-gn">${esc(name)}</span><span class="n">${rows.length}</span>${late ? `<span class="tv-glate">${late} late</span>` : ""}${
    null != doneN && tot ? `<span class="tv-bar" role="img" aria-label="${doneN} of ${tot} done"><i style="width:${pct}%"></i></span><span class="tv-gdone">${doneN} of ${tot} done</span>` : ""
  }</button>`;
}
// done tasks in the same scope, counted per group for the bar
function tvDoneBy(gb) {
  const out = {};
  if (!gb) return out;
  let D = [];
  try {
    D = "done" === t2View ? [] : t2DonePool();
  } catch (e) {}
  D.forEach((x) => {
    const I = { x: x, owner: tvOwnerName(x), status: "done", pid: tvProjectOf(x).id, pname: "" },
      k = tvGroupKey(I, gb)[0];
    out[k] = (out[k] || 0) + 1;
  });
  return out;
}

// ---- the Table: modern rows, not a spreadsheet ----------------------------------------------------------------------
const TV_COLS = [
  { k: "title", n: "Task", w: 420, fixed: 1, sort: (I) => String(I.x.title || "").toLowerCase() },
  { k: "owner", n: "Owner", w: 150, sort: (I) => I.owner || "~" },
  { k: "wait", n: "Waiting On", w: 190, sort: (I) => (I.wait ? I.wait.promised || "9" : "~") },
  { k: "due", n: "Due", w: 128, sort: (I) => I.x.due || "9999" },
  { k: "follow", n: "Follow-Up", w: 132, sort: (I) => I.follow || "9999" },
  { k: "status", n: "Status", w: 132, sort: (I) => TV_STATUS.findIndex(([k]) => k === I.status) },
  { k: "ref", n: "ID", w: 96, sort: (I) => I.ref || "~" },
  { k: "project", n: "Project", w: 150, sort: (I) => I.pname },
  { k: "section", n: "Section", w: 140, sort: (I) => I.section || "~" },
  { k: "priority", n: "Priority", w: 104, sort: (I) => ({ high: 0, med: 1, low: 2 })[I.x.priority] ?? 1 },
  { k: "watch", n: "Watch Until", w: 132, sort: (I) => I.watch || "9999" },
  { k: "last", n: "Last Discussed", w: 140, sort: (I) => I.last || "0000" },
  { k: "area", n: "Area", w: 130, sort: (I) => I.x.area || "~" },
];
const TV_COLS_DEFAULT = ["title", "owner", "wait", "due", "follow", "status"];
function tvTableCols() {
  const T = tvPrefs().table,
    on = Array.isArray(T.cols) && T.cols.length ? T.cols : TV_COLS_DEFAULT;
  return TV_COLS.filter((c) => c.fixed || on.includes(c.k));
}
const tvColW = (c) => Math.max(72, Math.min(720, +((tvPrefs().table.widths || {})[c.k]) || c.w));
function tvSorts() {
  const s = tvPrefs().table.sort;
  const L = Array.isArray(s) ? s : s && s.k ? [s] : [];
  return L.filter((y) => y && TV_COLS.some((c) => c.k === y.k));
}
function tvSortRows(rows) {
  const S = tvSorts();
  if (!S.length) return rows;
  const C = S.map((s) => [TV_COLS.find((c) => c.k === s.k), "desc" === s.dir ? -1 : 1]);
  return rows.slice().sort((a, b) => {
    for (const [c, dir] of C) {
      const va = c.sort(a),
        vb = c.sort(b);
      if (va < vb) return -dir;
      if (va > vb) return dir;
    }
    return 0;
  });
}
function tvTd(I, c) {
  const x = I.x;
  switch (c.k) {
    case "title": {
      const W = I.wait,
        L = I.latest,
        second = L ? `<span class="tv-sub2">${L.by ? `<b>${esc(tkFirst(L.by))}:</b> ` : ""}${esc(L.text)}</span>` : W ? `<span class="tv-sub2">Waiting on ${esc(W.name)}${W.what ? ` for ${esc(W.what)}` : ""}</span>` : "";
      return `<td class="tv-td-title"><div class="tv-tcell">${tvCheck(I)}${tvRefHtml(I)}<button type="button" class="tv-tt" data-tved="title"><span class="tv-ttx">${esc(x.title || "")}</span>${second}</button></div></td>`;
    }
    case "ref":
      return `<td><span class="tv-txt">${I.ref ? `<span class="tv-ref">${esc(I.ref)}</span>` : ""}</span></td>`;
    case "project":
      return `<td><span class="tv-txt">${esc(I.pname)}</span></td>`;
    case "section":
      return `<td><span class="tv-txt">${esc(I.section || "")}</span></td>`;
    case "priority":
      return `<td><span class="tv-txt tv-pri-${esc(x.priority || "med")}">${esc({ high: "High", med: "Medium", low: "Low" }[x.priority] || x.priority || "")}</span></td>`;
    case "last":
      return `<td><span class="tv-txt">${I.last ? esc(tvRel(I.last, !0)) : ""}</span></td>`;
    case "area":
      return `<td><span class="tv-txt">${esc(TK_AREA_LABEL[x.area] || x.area || "")}</span></td>`;
    default:
      return `<td>${tvCell(I, c.k)}</td>`;
  }
}
let tvSel = new Set();
function tvTableHtml(infos) {
  const cols = tvTableCols(),
    S = tvSorts(),
    gb = tvTableGroup(),
    rows = tvSortRows(infos),
    G = tvGroups(rows, gb, !1),
    doneBy = tvDoneBy(gb),
    keys = new Set(infos.map((I) => I.key));
  [...tvSel].forEach((k) => keys.has(k) || tvSel.delete(k));
  const allOn = infos.length > 0 && infos.every((I) => tvSel.has(I.key)),
    span = cols.length + 1,
    tr = (I) =>
      `<tr class="tv-tr ${I.x.late && !I.x.done ? "late" : ""} ${I.x.done ? "done" : ""} ${tvSel.has(I.key) ? "sel" : ""}" data-tvrow="${esc(I.key)}" ${tvEditAttr(I.x)}><td class="tv-td-sel"><label class="tv-cb"><input type="checkbox" data-tvsel="${esc(I.key)}" ${tvSel.has(I.key) ? "checked" : ""} aria-label="Select ${esc(tvTitle(I.x))}"></label></td>${cols.map((c) => tvTd(I, c)).join("")}</tr>`;
  const body = gb
    ? G.map((g) => {
        const gid = `t:${gb}:${g.k}`;
        return `<tbody class="tv-tg"><tr class="tv-grow"><td colspan="${span}">${tvGhd(gid, g.n, g.rows, doneBy[g.k] || 0)}</td></tr>${tvFolded(gid) ? "" : g.rows.map(tr).join("")}</tbody>`;
      }).join("")
    : `<tbody>${rows.map(tr).join("")}</tbody>`;
  const head = `<thead><tr><th class="tv-th-sel" scope="col"><label class="tv-cb"><input type="checkbox" data-tvselall ${allOn ? "checked" : ""} aria-label="Select all"></label></th>${cols
    .map((c) => {
      const i = S.findIndex((s) => s.k === c.k),
        s = S[i];
      return `<th scope="col" data-tvcol="${c.k}" aria-sort="${s ? ("desc" === s.dir ? "descending" : "ascending") : "none"}"><button type="button" class="tv-sortb" data-tvsort="${c.k}" title="Sort; Shift adds a second sort">${esc(c.n)}${s ? `${tvSvg("desc" === s.dir ? "down" : "up", 14)}${S.length > 1 ? `<small class="tv-sortn">${i + 1}</small>` : ""}` : ""}</button><span class="tv-rs" data-tvrs="${c.k}" aria-hidden="true"></span></th>`;
    })
    .join("")}</tr></thead>`;
  const W = 52 + cols.reduce((a, c) => a + tvColW(c), 0);
  return `<div class="tv-tframe ${tvDense() ? "dense" : ""}" tabindex="-1"><table class="tv-table" style="min-width:${W}px"><colgroup><col style="width:52px">${cols.map((c) => `<col data-tvc="${c.k}" style="width:${tvColW(c)}px">`).join("")}</colgroup>${head}${body}</table></div>${tvBulkHtml()}`;
}
// the phone: the table's rows become the list's cards, in the table's groups and sort
function tvCardsHtml(infos) {
  const gb = tvTableGroup(),
    G = tvGroups(tvSortRows(infos), gb, !1),
    doneBy = tvDoneBy(gb),
    o = { hideJob: "project" === gb };
  return `<div class="tv-cards">${G.map((g) => {
    if (!gb) return g.rows.map((I) => tkRowHtml(I.x, o)).join("");
    const gid = `t:${gb}:${g.k}`;
    return `<div class="tv-grp">${tvGhd(gid, g.n, g.rows, doneBy[g.k] || 0)}${tvFolded(gid) ? "" : g.rows.map((I) => tkRowHtml(I.x, o)).join("")}</div>`;
  }).join("")}</div>`;
}
function tvBulkHtml() {
  const n = tvSel.size;
  if (!n) return "";
  return `<div class="tv-bulk" role="toolbar" aria-label="Selected tasks"><b>${n} Selected</b><button type="button" class="btn" data-tvbulk="due">Move Date</button><button type="button" class="btn" data-tvbulk="owner">Reassign</button><button type="button" class="btn" data-tvbulk="status">Status</button><button type="button" class="btn" data-tvbulk="done">Done</button><button type="button" class="btn tv-ic" data-tvbulk="clear" aria-label="Clear the selection" title="Clear the selection">${tvSvg("x", 18)}</button></div>`;
}
// one action over every selected task: one toast, one Undo for all of them
function tvBulk(what, anchor) {
  const L = [...tvSel].map(tvFind).filter(Boolean);
  if ("clear" === what) return tvSel.clear(), tvKeepScroll(() => renderTkAll());
  if (!L.length) return;
  const run = (fn, say) => {
    const undos = [],
      moved = [],
      skipped = [];
    L.forEach((I) => {
      const u = fn(I);
      "function" == typeof u ? (undos.push(u), moved.push(I)) : skipped.push(I);
    });
    if (!undos.length) return toast(`Nothing changed: ${1 === skipped.length ? "that task is changed" : "these are changed"} from the task itself`);
    tvSel.clear();
    tvDone(`${say} · ${undos.length} task${1 === undos.length ? "" : "s"}${skipped.length ? `; ${skipped.length} left for their own sheet` : ""}`, moved[0].key, () => undos.reverse().forEach((u) => u()));
  };
  if ("due" === what) return tvDatePop(anchor, `Move ${L.length} To`, "", (d) => run((I) => tvSetDue(I, d, !0), d ? `Moved to ${fmtL(d)}` : "Date taken off"), !0);
  if ("owner" === what) {
    if (!TV_ASSIGNERS.includes(role())) return toast("Reassigning many at once is for the coordinator and the managers; offer each one from its sheet");
    return tvPersonPop(anchor, "", (n) => run((I) => tvSetOwner(I, n, !0), `${tkFirst(n)} owns them now`), "Reassign To");
  }
  if ("done" === what) return run((I) => tvSetStatus(I, "done", { quiet: !0 }), "Done");
  if ("status" === what)
    return tvPop(
      anchor,
      "Status",
      `<div class="tv-menu">${TV_STATUS.filter(([k]) => "waiting" !== k)
        .map(([k, n], i) => `<button type="button" class="tv-mi" data-tvs="${k}" ${0 === i ? "data-tvfirst" : ""}><span class="tv-pill tv-st-${k}">${n}</span></button>`)
        .join("")}</div><p class="small muted tv-pop-note">Waiting On names who owes it, so it is set one task at a time.</p>`,
      (d) => d.querySelectorAll("[data-tvs]").forEach((b) => (b.onclick = () => (tvPopClose(), run((I) => tvSetStatus(I, b.dataset.tvs, { quiet: !0 }), TV_STATUS_SAY[b.dataset.tvs])))),
    );
}
function tvColsPanel(anchor) {
  const on = new Set(tvTableCols().map((c) => c.k));
  tvPop(
    anchor,
    "Columns",
    `<div class="tv-colset">${TV_COLS.map((c) => `<label class="tv-colck ${c.fixed ? "fixed" : ""}"><input type="checkbox" data-tvcolck="${c.k}" ${on.has(c.k) ? "checked" : ""} ${c.fixed ? "disabled" : ""}><span>${esc(c.n)}</span></label>`).join("")}</div><div class="tv-pop-ft"><button type="button" class="btn" data-tvcolreset>Reset Columns</button></div>`,
    (d) => {
      d.querySelectorAll("[data-tvcolck]").forEach(
        (i) =>
          (i.onchange = () => {
            tvPrefs().table.cols = [...d.querySelectorAll("[data-tvcolck]")].filter((y) => y.checked).map((y) => y.dataset.tvcolck);
            save();
            tvKeepScroll(() => renderTkAll());
          }),
      );
      d.querySelector("[data-tvcolreset]").onclick = () => {
        const T = tvPrefs().table;
        delete T.cols, delete T.widths, delete T.sort;
        save(), tvPopClose(), renderTkAll(), toast("The table is back to its standard columns");
      };
    },
  );
}

// ---- the Board: by status or by project; drag with Undo; quick add; swipe between columns on the phone ----------------
function tvCard(I, showStatus) {
  const x = I.x,
    td = today(),
    late = x.due && x.due < td && !x.done;
  return `<div class="tv-card ${late ? "late" : ""} ${x.done ? "done" : ""}" data-tvrow="${esc(I.key)}" ${tvEditAttr(x)} ${tvPhone() ? "" : 'draggable="true"'} tabindex="0" role="listitem" aria-label="${esc(x.title || "")}">
  <div class="tv-card-top">${tvRefHtml(I)}<span class="grow"></span>${x.due ? `<span class="tv-card-due ${late ? "late" : ""}" title="${esc(fmtL(x.due))}">${esc(tvRel(x.due, x.done))}</span>` : ""}</div>
  <div class="tv-card-t">${esc(x.title || "")}</div>
  ${I.wait ? `<div class="tv-card-w">${tvCell(I, "wait")}</div>` : ""}
  <div class="tv-card-ft">${tvCell(I, "owner")}<span class="grow"></span>${showStatus ? tvCell(I, "status") : ""}</div></div>`;
}
function tvBoardCols(infos) {
  const by = tvPrefs().boardBy;
  if ("project" === by)
    return {
      by: by,
      cols: tvGroups(infos, "project", !1).map((g) => ({ k: g.k, n: g.n, rows: g.rows, can: !!g.k && 0 !== g.k.indexOf("_") && 0 !== g.k.indexOf("firm:"), add: "__sales" !== g.k })),
    };
  const cols = [
    { k: "todo", n: "To Do", rows: infos.filter((I) => "todo" === I.status), can: !0, add: !0 },
    { k: "doing", n: "Doing", rows: infos.filter((I) => "doing" === I.status), can: !0, add: !0 },
    { k: "waiting", n: "Waiting On", rows: infos.filter((I) => "waiting" === I.status), can: !0, add: !0 },
  ];
  infos.some((I) => "fyi" === I.status) && cols.push({ k: "fyi", n: "FYI", rows: infos.filter((I) => "fyi" === I.status), can: !0, add: !0 });
  // Done: what this list shows as done, or the last ten done in the same scope (said, so the number is not the list's)
  let done = infos.filter((I) => "done" === I.status),
    note = "";
  if ("done" !== t2View) {
    try {
      done = t2DonePool().slice(0, 10).map(tvInfo);
      note = "the last 10";
    } catch (e) {
      done = [];
    }
  }
  cols.push({ k: "done", n: "Done", rows: done, can: !0, note: note, extra: "done" !== t2View });
  return { by: by, cols: cols };
}
function tvBoardHtml(infos) {
  const B = tvBoardCols(infos),
    ph = tvPhone(),
    showStatus = ph || "project" === B.by;
  const tabs = ph ? `<div class="tv-btabs" role="tablist">${B.cols.map((c, i) => `<button type="button" role="tab" class="tv-btab" data-tvbtab="${i}" aria-selected="${0 === i ? "true" : "false"}">${esc(c.n)}<span class="n">${c.rows.length}</span></button>`).join("")}</div>` : "";
  return `${tabs}<div class="tv-board ${ph ? "tv-board-ph" : ""}" data-tvboard="${B.by}">${B.cols
    .map(
      (c) =>
        `<section class="tv-bcol ${c.extra ? "tv-bextra" : ""}" data-tvdrop="${esc(c.k)}" data-tvcan="${c.can ? 1 : 0}" aria-label="${esc(c.n)}"><div class="tv-bhd"><span class="tv-pill tv-st-${"status" === B.by ? c.k : "x"}">${esc(c.n)}</span><span class="n">${c.rows.length}</span>${c.note ? `<span class="small muted">${esc(c.note)}</span>` : ""}</div><div class="tv-bcards" role="list">${c.rows.map((I) => tvCard(I, showStatus)).join("") || '<div class="tv-bempty small muted">Nothing here.</div>'}</div>${
          c.add ? `<div class="tv-qadd">${tvSvg("plus", 16)}<input data-tvqadd="${esc(c.k)}" placeholder="Add a task" aria-label="Add a task to ${esc(c.n)}" enterkeyhint="done"></div>` : ""
        }</section>`,
    )
    .join("")}</div>`;
}
function tvBoardMove(key, col) {
  const I = tvFind(key);
  if (!I) return;
  if ("project" === tvPrefs().boardBy) return I.pid === col ? null : tvSetProject(I, col);
  if (I.status === col) return null;
  const card = document.querySelector(`#tkall-body [data-tvrow="${CSS.escape(key)}"]`);
  return tvSetStatus(I, col, { anchor: card });
}

// ---- the Calendar: month and week; due dates solid by project, follow-ups outlined; drag to re-date ---------------------
let tvCalAt = "";
function tvCalMode() {
  return tvPrefs().calMode || (tvPhone() ? "week" : "month");
}
function tvCalRange() {
  const d = parse(tvCalAt || today()),
    mode = tvCalMode();
  if ("week" === mode) {
    const s = addDays(d, -d.getDay());
    return { mode: mode, from: iso(s), to: iso(addDays(s, 6)), days: [...Array(7)].map((_, i) => iso(addDays(s, i))), title: `Week of ${tvD(iso(s))}` };
  }
  const first = new Date(d.getFullYear(), d.getMonth(), 1),
    last = new Date(d.getFullYear(), d.getMonth() + 1, 0),
    s = addDays(first, -first.getDay()),
    n = Math.ceil((first.getDay() + last.getDate()) / 7) * 7;
  return { mode: mode, from: iso(first), to: iso(last), days: [...Array(n)].map((_, i) => iso(addDays(s, i))), title: first.toLocaleDateString("en-US", { month: "long", year: "numeric" }), month: first.getMonth() };
}
function tvEv(I, field) {
  const x = I.x,
    fu = "follow" === field;
  return `<button type="button" class="tv-ev ${fu ? "tv-ev-fu" : ""} ${x.late && !fu && !x.done ? "late" : ""} ${x.done ? "done" : ""}" style="--h:${tvHue(I.pid)}" data-tvrow="${esc(I.key)}" data-tvfield="${field}" ${tvEditAttr(x)} ${tvPhone() ? "" : 'draggable="true"'} aria-label="${fu ? "Follow up: " : ""}${esc(x.title || "")}" title="${esc(`${I.pname}: ${x.title || ""}`)}">${fu ? tvSvg("clock", 13) : ""}${I.ref ? `<span class="tv-ref">${esc(I.ref)}</span>` : ""}<span class="tv-evt">${esc(x.title || "")}</span></button>`;
}
function tvCalHtml(infos) {
  const C = tvCalRange(),
    td = today(),
    first = C.days[0],
    lastDay = C.days[C.days.length - 1],
    byDay = {},
    put = (d, h) => (byDay[d] = byDay[d] || []).push(h),
    before = [],
    after = [],
    none = [];
  infos.forEach((I) => {
    const d = I.x.due;
    if (!d) none.push(I);
    else if (d < first) before.push(I);
    else if (d > lastDay) after.push(I);
    else put(d, tvEv(I, "due"));
    I.follow && I.follow >= first && I.follow <= lastDay && !I.x.done && put(I.follow, tvEv(I, "follow"));
  });
  const ph = tvPhone(),
    cell = (d) => {
      const out = null != C.month && parse(d).getMonth() !== C.month;
      return `<div class="tv-day ${d === td ? "tv-isday" : ""} ${out ? "tv-outm" : ""}" data-tvday="${d}"><div class="tv-dn">${"week" === C.mode ? `<b>${DOW[parse(d).getDay()]}</b> ` : ""}${parse(d).getDate()}${d === td ? '<span class="tv-tdy">Today</span>' : ""}</div><div class="tv-evs">${(byDay[d] || []).join("")}</div></div>`;
    },
    grid =
      "week" === C.mode && ph
        ? `<div class="tv-wk-ph">${C.days.map(cell).join("")}</div>`
        : `<div class="tv-cal ${C.mode}"><div class="tv-dows">${DOW.map((d) => `<div class="tv-dow">${d}</div>`).join("")}</div><div class="tv-days">${C.days.map(cell).join("")}</div></div>`,
    tray = (k, name, L) => (L.length ? `<div class="tv-tray">${tvGhd(`c:${k}`, name, L, null, "tv-shd")}${tvFolded(`c:${k}`) ? "" : `<div class="tv-trayrows">${L.map((I) => tvEv(I, "due")).join("")}</div>`}</div>` : "");
  return `<div class="tv-calbar"><div class="seg sm tv-calmode"><button type="button" class="${"month" === C.mode ? "on" : ""}" data-tvcalmode="month">Month</button><button type="button" class="${"week" === C.mode ? "on" : ""}" data-tvcalmode="week">Week</button></div><button type="button" class="btn tv-ic" data-tvcalgo="-1" aria-label="Previous" title="Previous">${tvSvg("chevL", 18)}</button><button type="button" class="btn" data-tvcalgo="0">Today</button><button type="button" class="btn tv-ic" data-tvcalgo="1" aria-label="Next" title="Next">${tvSvg("chevR", 18)}</button><b class="tv-caltitle">${esc(C.title)}</b><span class="grow"></span><span class="tv-legend small muted"><span class="tv-ev tv-key">Due</span><span class="tv-ev tv-ev-fu tv-key">${tvSvg("clock", 13)}Follow-Up</span></span></div>
${grid}${tray("before", `Before ${tvD(first)}`, before)}${tray("after", `After ${tvD(lastDay)}`, after)}${tray("none", "No Date", none)}`;
}
function tvCalDrop(key, field, day) {
  const I = tvFind(key);
  if (!I || !day) return;
  if ("follow" === field) return I.follow === day ? null : TV_CAN.follow(I.x) ? tvSetField(I, "followUp", day, "Follow-up") : tvCant(I, "The follow-up");
  return I.x.due === day ? null : tvSetDue(I, day);
}

// ---- saved views as tabs: My Week, Waiting on Others, By Project, All Open, and the person's own -------------------
const TV_STATE_KEYS = ["tkWho", "tkProject", "tkArea", "tkPri", "t2View", "t2Group", "t2Q"];
function tvBuiltIns() {
  const S = (o) => Object.assign({ tkWho: "all", tkProject: "", tkArea: "", tkPri: "", t2View: "all", t2Group: null, t2Q: "" }, o);
  return [
    { id: "b:week", name: "My Week", mode: "cards", s: S({ tkWho: "me", t2View: "week", t2Group: "day" }) },
    { id: "b:wait", name: "Waiting on Others", mode: "table", group: "project", s: S({ t2View: "blocked" }) },
    { id: "b:proj", name: "By Project", mode: "table", group: "project", s: S({}) },
    { id: "b:all", name: "All Open", mode: "cards", s: S({ t2Group: "day" }) },
  ];
}
const tvViews = () => tvBuiltIns().concat(tvPrefs().views || []);
const tvStateNow = () => ({ tkWho: tkWho, tkProject: tkProject, tkArea: tkArea, tkPri: tkPri, t2View: t2View, t2Group: t2Group, t2Q: t2Q });
function tvIsOn(v) {
  const s = tvStateNow(),
    m = v.mode || "cards";
  if (m !== (tkMode || "cards")) return !1;
  if ("table" === m && null != v.group && v.group !== tvTableGroup()) return !1;
  return TV_STATE_KEYS.filter((k) => "table" !== m || "t2Group" !== k).every((k) => String(null == v.s[k] ? "" : v.s[k]) === String(null == s[k] ? "" : s[k]));
}
function tvApply(id) {
  const v = tvViews().find((y) => y.id === id);
  if (!v) return;
  tkWho = v.s.tkWho || "me";
  tkProject = v.s.tkProject || "";
  tkArea = v.s.tkArea || "";
  tkPri = v.s.tkPri || "";
  t2View = v.s.t2View || "week";
  t2Group = null == v.s.t2Group ? null : v.s.t2Group;
  t2Q = v.s.t2Q || "";
  const T = tvPrefs().table;
  null != v.group && (T.group = v.group);
  if (v.table) {
    v.table.cols && (T.cols = v.table.cols.slice());
    v.table.sort ? (T.sort = JSON.parse(JSON.stringify(v.table.sort))) : delete T.sort;
    v.table.density && (T.density = v.table.density);
  }
  v.boardBy && (tvPrefs().boardBy = v.boardBy);
  tvSel.clear();
  tkSetMode(v.mode || "cards");
}
function tvSaveDialog() {
  const mine = tvPrefs().views || [];
  const m = mbModal(
    "New View",
    `<p class="small muted">Keeps what this list shows now: whose tasks, the filters, the dates, the grouping and the layout${"table" === tkMode ? ", with the table's columns and sort" : ""}. Your views are yours; nobody else's list changes.</p>${mbF("Name", mbIn("name", "", "Kitchen jobs this week"))}${
      mine.length ? `<div class="tks-h">Your Views</div><div class="tv-myviews">${mine.map((v) => `<div class="tv-myv"><span class="grow">${esc(v.name)}</span><button type="button" class="btn" data-tvdel="${esc(v.id)}">Remove</button></div>`).join("")}</div>` : ""
    }`,
    {
      submit: "Save View",
      onSubmit: (f) => {
        const name = String(f.name || "").trim();
        if (!name) return toast("Name the view"), !1;
        const P = tvPrefs(),
          T = P.table,
          v = { id: uid("tv"), name: name.slice(0, 40), mode: tkMode || "cards", s: tvStateNow(), at: appNowIso() };
        "table" === tkMode && ((v.group = tvTableGroup()), (v.table = { cols: tvTableCols().map((c) => c.k), sort: tvSorts(), density: T.density || "" }));
        "board" === tkMode && (v.boardBy = P.boardBy);
        const same = P.views.findIndex((y) => y.name.toLowerCase() === v.name.toLowerCase());
        same >= 0 ? (P.views[same] = Object.assign(v, { id: P.views[same].id })) : P.views.push(v);
        save();
        renderTkAll();
        toast(`Saved: ${v.name}, in your views`, [{ label: "Open", run: () => tvApply(v.id) }]);
      },
    },
  );
  m &&
    m.querySelectorAll("[data-tvdel]").forEach(
      (b) =>
        (b.onclick = () => {
          const P = tvPrefs(),
            i = P.views.findIndex((y) => y.id === b.dataset.tvdel);
          if (i < 0) return;
          const gone = P.views.splice(i, 1)[0];
          save(), mbCloseModal(), renderTkAll();
          toast(`Removed: ${gone.name}`, [{ label: "Undo", run: () => (tvPrefs().views.splice(i, 0, gone), save(), renderTkAll()) }]);
        }),
    );
  return m;
}
function tvSavedHtml() {
  return `<div class="tv-saved no-print" role="tablist" aria-label="Saved views">${tvViews()
    .map((v) => `<button type="button" role="tab" class="tv-sv ${tvIsOn(v) ? "on" : ""}" data-tvview="${esc(v.id)}" aria-selected="${tvIsOn(v) ? "true" : "false"}">${esc(v.name)}</button>`)
    .join("")}<button type="button" class="tv-sv tv-svnew" data-tvsave>${tvSvg("plus", 15)}<span>New View</span></button></div>`;
}

// ---- filter chips: the list's own filters, said as chips; "Filter" adds one ------------------------------------------
function tvFilterChips() {
  const L = [],
    named = tkWho && !["me", "all", "none", "team"].includes(tkWho);
  named && L.push(["owner", `Owner: ${tkFirst(tkWho)}`]);
  if (tkProject && "home" === t2Ctx()) {
    const p = (DB.projects || []).find((q) => q.id === tkProject);
    L.push(["project", `Project: ${"__sales" === tkProject ? "Sales" : p ? shortName(p) : "A Job"}`]);
  }
  tkArea && L.push(["area", `Area: ${TK_AREA_LABEL[tkArea] || tkArea}`]);
  tkPri && L.push(["pri", "Priority: High"]);
  return `<div class="tv-filters" role="group" aria-label="Filters">${L.map(([k, n]) => `<span class="tv-fchip"><button type="button" class="tv-fchip-b" data-tvfedit="${k}">${esc(n)}</button><button type="button" class="tv-fchip-x" data-tvfx="${k}" aria-label="Remove ${esc(n)}" title="Remove this filter">${tvSvg("x", 14)}</button></span>`).join("")}<button type="button" class="tv-fadd" data-tvfadd>${tvSvg("plus", 15)}<span>Filter</span></button></div>`;
}
function tvFilterPick(what, anchor) {
  const done = () => (tvSel.clear(), renderTkAll());
  if ("owner" === what) {
    let names = [];
    try {
      names = crPeopleOf(tkItems().filter((x) => !x.done));
    } catch (e) {
      names = tvPeople().map((u) => u.name);
    }
    return tvPersonPop(anchor, tkWho, (n) => ((tkWho = n), done()), "Owner", names.map((n) => ({ name: n, sub: "" })));
  }
  if ("project" === what)
    return tvPop(
      anchor,
      "Project",
      `<input class="tv-psearch" data-tvpq placeholder="Search jobs" aria-label="Search jobs" autocomplete="off"><div class="tv-people">${[["__sales", "Sales"]]
        .concat((DB.projects || []).map((p) => [p.id, shortName(p)]))
        .map(([id, n], i) => `<button type="button" class="tv-person ${tkProject === id ? "on" : ""}" data-tvfp="${esc(id)}" ${0 === i ? "data-tvfirst" : ""}><span class="grow"><b>${esc(n)}</b></span></button>`)
        .join("")}</div>`,
      (d) => {
        d.querySelectorAll("[data-tvfp]").forEach((b) => (b.onclick = () => (tvPopClose(), (tkProject = b.dataset.tvfp), "__sales" === tkProject && "me" === tkWho && (tkWho = "all"), done())));
        const q = d.querySelector("[data-tvpq]");
        q.oninput = () => d.querySelectorAll("[data-tvfp]").forEach((b) => (b.hidden = !!q.value.trim() && !b.textContent.toLowerCase().includes(q.value.trim().toLowerCase())));
        tvPhone() || setTimeout(() => q.focus(), 0);
      },
    );
  if ("area" === what)
    return tvPop(anchor, "Area", `<div class="tv-menu">${TK_AREAS.map(([k, n], i) => `<button type="button" class="tv-mi ${tkArea === k ? "on" : ""}" data-tvfa="${k}" ${0 === i ? "data-tvfirst" : ""}>${esc(n)}</button>`).join("")}</div>`, (d) =>
      d.querySelectorAll("[data-tvfa]").forEach((b) => (b.onclick = () => (tvPopClose(), (tkArea = b.dataset.tvfa), done()))),
    );
  if ("pri" === what) return (tkPri = "high"), done();
  return tvPop(
    anchor,
    "Filter By",
    `<div class="tv-menu">${[
      ["owner", "Owner"],
      "home" === t2Ctx() ? ["project", "Project"] : null,
      ["area", "Area"],
      ["pri", "High Priority"],
    ]
      .filter(Boolean)
      .map(([k, n], i) => `<button type="button" class="tv-mi" data-tvfk="${k}" ${0 === i ? "data-tvfirst" : ""}>${n}</button>`)
      .join("")}</div>`,
    (d) => d.querySelectorAll("[data-tvfk]").forEach((b) => (b.onclick = () => tvFilterPick(b.dataset.tvfk, anchor))),
  );
}
function tvFilterClear(what) {
  "owner" === what && (tkWho = "all");
  "project" === what && (tkProject = "");
  "area" === what && (tkArea = "");
  "pri" === what && (tkPri = "");
  tvSel.clear();
  renderTkAll();
}

// ---- drawing: after the list draws, the bar takes the chips, and the chosen layout takes the list's place -------------
function tvSummary(infos) {
  const late = infos.filter((I) => I.x.late && !I.x.done).length,
    wait = infos.filter((I) => "waiting" === I.status).length;
  return `<div class="tv-sum-line" data-tvn="${infos.length}"><b>${infos.length}</b> task${1 === infos.length ? "" : "s"}${late ? ` · <span class="late">${late} late</span>` : ""}${wait ? ` · ${wait} waiting on others` : ""}</div>`;
}
function tvToolbar() {
  if ("table" === tkMode) {
    const g = tvTableGroup();
    return `<select class="btn tv-tgroup" data-tvtgroup aria-label="Group the table" title="Group the table">${TV_GROUPS.map(([k, n]) => `<option value="${k}" ${g === k ? "selected" : ""}>${n}</option>`).join("")}</select>${
      tvPhone()
        ? ""
        : `<div class="seg sm tv-dens"><button type="button" class="${tvDense() ? "" : "on"}" data-tvdens="">Comfortable</button><button type="button" class="${tvDense() ? "on" : ""}" data-tvdens="compact">Compact</button></div><button type="button" class="btn" data-tvcols>${tvSvg("cols", 16)}<span>Columns</span></button>`
    }`;
  }
  if ("board" === tkMode) {
    const by = tvPrefs().boardBy;
    return `<div class="seg sm tv-boardby"><button type="button" class="${"project" !== by ? "on" : ""}" data-tvboardby="status">By Status</button><button type="button" class="${"project" === by ? "on" : ""}" data-tvboardby="project">By Project</button></div>`;
  }
  return "";
}
// the bar on a wide screen: the job, person, area and priority selects become chips; search reads the ID too
function tvBar(host) {
  const bar = host.querySelector(".tk2-bar");
  if (!bar || bar.dataset.tvbar) return;
  bar.dataset.tvbar = "1";
  ["#t2-proj", "#t2-person", "#t2-area", "#t2-pri"].forEach((s) => {
    const e = bar.querySelector(s);
    e && e.remove();
  });
  const q = bar.querySelector("#t2-q");
  q && (q.placeholder = "Search by ID or title");
  q ? q.insertAdjacentHTML("afterend", tvFilterChips()) : bar.insertAdjacentHTML("afterbegin", tvFilterChips());
  const gs = bar.querySelector("#t2-group");
  if (gs) {
    const o = gs.querySelector('option[value="assignee"]');
    o && (o.textContent = "By Owner");
    gs.querySelector('option[value="status"]') || gs.insertAdjacentHTML("beforeend", '<option value="status">By Status</option><option value="due">By Due Date</option>');
    // the table keeps its own grouping (by project); the list's select stays the list's
    "table" === tkMode && gs.remove();
  }
}
// the List's rows (tasks.js) on this screen: the ID first; on a wide screen the cells edit in place; Done joins the swipe
function tvDecorateRows(scope) {
  const ph = tvPhone(),
    rows = [...scope.querySelectorAll(".tk2-row[data-tkkey]")].filter((r) => !r.dataset.tvdec);
  if (!rows.length) return;
  const M = new Map();
  try {
    tkItems().forEach((x) => M.set(t2Key(x), x));
  } catch (e) {}
  rows.forEach((r) => {
    r.dataset.tvdec = "1";
    const x = M.get(r.dataset.tkkey);
    if (!x) return;
    const I = tvInfo(x);
    r.dataset.tvrow = I.key;
    const sub = r.querySelector(".tk2-sub");
    sub && I.ref && sub.insertAdjacentHTML("afterbegin", `<span class="tv-ref">${esc(I.ref)}</span><span class="tk2-dot"> · </span>`);
    const acts = r.querySelector(".tk2-acts");
    acts && !x.done && (acts.insertAdjacentHTML("afterbegin", `<button type="button" class="tk2-act tv-act-done" data-tvdone="${esc(I.key)}" tabindex="-1">Done</button>`), r.classList.add("tv-3acts"));
    if (ph) return;
    const slide = r.querySelector(".tk2-slide");
    if (!slide) return;
    const who = slide.querySelector(".tk2-who");
    who && who.remove();
    const when = sub && sub.querySelector(".tk2-when");
    if (when) {
      const dot = when.nextElementSibling;
      dot && dot.classList.contains("tk2-dot") && dot.remove();
      when.remove();
    }
    slide.insertAdjacentHTML("beforeend", `<span class="tv-cells">${I.wait ? tvCell(I, "wait") : ""}${tvCell(I, "owner")}${tvCell(I, "due")}${tvCell(I, "status")}</span>`);
  });
}
function tvAfter() {
  const host = document.getElementById("tkall-body");
  if (!host || !tvMayUse()) return;
  const ctx = t2Ctx(),
    ph = tvPhone();
  // the mode switch: List, Table, Board, Calendar
  const seg = host.querySelector(".tk-mode");
  seg && ((seg.innerHTML = TV_MODES.map(([k, n]) => `<button type="button" class="${(tkMode || "cards") === k ? "on" : ""}" data-tkmode="${k}">${n}</button>`).join("")), seg.classList.add("tv-modes"));
  host.querySelectorAll("[data-tkmode]").forEach((b) => (b.onclick = () => tkSetMode(b.dataset.tkmode)));
  ph || tvBar(host);
  // saved views as tabs, on the person's own Tasks, above the bar
  if ("home" === ctx && !ph && !host.querySelector(".tv-saved")) {
    const at = host.querySelector(".tk2-bar") || host.querySelector(".ph");
    at && at.insertAdjacentHTML("beforebegin", tvSavedHtml());
  }
  tvWireBar(host);
  if (!tvMine()) {
    tvDecorateRows(host);
    tvWireCells(host);
    return;
  }
  const list = host.querySelector(".t2-list");
  if (!list) return;
  const infos = tvRows().map(tvInfo),
    wrap = document.createElement("div");
  wrap.className = `t2-list tv-host tv-mode-${tkMode}`;
  wrap.dataset.tvmode = tkMode;
  const quick = list.querySelector(".t2-quick"),
    empty = !infos.length && "table" === tkMode;
  wrap.innerHTML = `<div class="tv-top">${tvSummary(infos)}<span class="grow"></span>${tvToolbar()}</div>${
    empty
      ? `<div class="empty tv-empty">${"week" === t2View ? "Nothing due in the next 7 days, and nothing late." : "No task matches these filters."}${"all" !== t2View ? ' <button type="button" class="btn" data-t2view="all">Show All Open Tasks</button>' : ""}</div>`
      : "table" === tkMode
        ? ph
          ? tvCardsHtml(infos)
          : tvTableHtml(infos)
        : "board" === tkMode
          ? tvBoardHtml(infos)
          : tvCalHtml(infos)
  }`;
  quick && wrap.appendChild(quick);
  list.replaceWith(wrap);
  host.querySelectorAll(".t2-undo").forEach((e) => e.remove());
  if ("table" === tkMode && ph) {
    try {
      tkWireList(wrap);
    } catch (e) {}
    tvDecorateRows(wrap);
  }
  tvWireCells(wrap);
  tvWire(wrap);
  // a task just made or opened lands highlighted, as on the list
  try {
    if (crFlash && Date.now() <= crFlashUntil) {
      const r = wrap.querySelector(`[data-edit$="|${CSS.escape(crFlash)}"]`);
      r && (r.classList.add("tk-flash"), r.scrollIntoView({ block: "center" }), setTimeout(() => r.classList.remove("tk-flash"), 2500));
    }
  } catch (e) {}
}
function tvWireBar(host) {
  host.querySelectorAll("[data-tvview]").forEach((b) => (b.onclick = () => tvApply(b.dataset.tvview)));
  host.querySelectorAll("[data-tvsave]").forEach((b) => (b.onclick = () => tvSaveDialog()));
  host.querySelectorAll("[data-tvfadd]").forEach((b) => (b.onclick = () => tvFilterPick("", b)));
  host.querySelectorAll("[data-tvfedit]").forEach((b) => (b.onclick = () => tvFilterPick(b.dataset.tvfedit, b)));
  host.querySelectorAll("[data-tvfx]").forEach((b) => (b.onclick = () => tvFilterClear(b.dataset.tvfx)));
}
let tvFocusAt = null;
function tvWireCells(w) {
  w.querySelectorAll("[data-tved]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.stopPropagation();
        const row = b.closest("[data-tvrow]");
        if (!row) return;
        tvFocusAt = { key: row.dataset.tvrow, f: b.dataset.tved };
        tvEdit(row.dataset.tvrow, b.dataset.tved, b);
      }),
  );
  w.querySelectorAll("[data-tvdone]").forEach(
    (b) =>
      (b.onclick = (e) => {
        e.stopPropagation();
        const r = b.closest(".tk2-row");
        r && r.classList.remove("swiped");
        tkCheckDone(b.dataset.tvdone);
      }),
  );
}
function tvWire(w) {
  w.querySelectorAll(".tv-card, .tv-ev[data-tvrow]").forEach(
    (c) =>
      (c.onclick = (e) => {
        if (e.target.closest("[data-tved], [data-tvdone]")) return;
        tkSheet(c.dataset.tvrow);
      }),
  );
  w.querySelectorAll(".tv-card").forEach((c) => (c.onkeydown = (e) => "Enter" === e.key && e.target === c && (e.preventDefault(), tkSheet(c.dataset.tvrow))));
  w.querySelectorAll("[data-tvfold]").forEach((b) => (b.onclick = () => tvFold(b.dataset.tvfold)));
  w.querySelectorAll("[data-t2view]").forEach((b) => (b.onclick = () => ((t2View = b.dataset.t2view), renderTkAll())));
  const cb = w.querySelector("[data-tvcols]");
  cb && (cb.onclick = () => tvColsPanel(cb));
  const tg = w.querySelector("[data-tvtgroup]");
  tg && (tg.onchange = () => ((tvPrefs().table.group = tg.value), save(), renderTkAll()));
  w.querySelectorAll("[data-tvdens]").forEach((b) => (b.onclick = () => ((tvPrefs().table.density = b.dataset.tvdens), save(), tvKeepScroll(() => renderTkAll()))));
  w.querySelectorAll("[data-tvboardby]").forEach((b) => (b.onclick = () => ((tvPrefs().boardBy = b.dataset.tvboardby), save(), renderTkAll())));
  "table" === tkMode && tvWireTable(w);
  "board" === tkMode && tvWireBoard(w);
  "cal" === tkMode && tvWireCal(w);
  // keep the keyboard where it was after an edit redraws the view
  if (tvFocusAt) {
    const r = w.querySelector(`[data-tvrow="${CSS.escape(tvFocusAt.key)}"] [data-tved="${tvFocusAt.f}"]`);
    r && (document.activeElement === document.body || !document.activeElement) && r.focus({ preventScroll: !0 });
  }
}
function tvWireTable(w) {
  w.querySelectorAll("[data-tvsel]").forEach(
    (i) =>
      (i.onchange = () => {
        i.checked ? tvSel.add(i.dataset.tvsel) : tvSel.delete(i.dataset.tvsel);
        tvKeepScroll(() => renderTkAll());
      }),
  );
  const all = w.querySelector("[data-tvselall]");
  all &&
    (all.onchange = () => {
      const keys = [...w.querySelectorAll("[data-tvsel]")].map((i) => i.dataset.tvsel);
      all.checked ? keys.forEach((k) => tvSel.add(k)) : tvSel.clear();
      tvKeepScroll(() => renderTkAll());
    });
  w.querySelectorAll("[data-tvbulk]").forEach((b) => (b.onclick = () => tvBulk(b.dataset.tvbulk, b)));
  // sort: a click sorts up, again down, a third time back to the list's order; Shift adds a second sort
  w.querySelectorAll("[data-tvsort]").forEach(
    (b) =>
      (b.onclick = (e) => {
        const T = tvPrefs().table,
          k = b.dataset.tvsort;
        let S = tvSorts();
        const i = S.findIndex((s) => s.k === k),
          next = i < 0 ? "asc" : "asc" === S[i].dir ? "desc" : "";
        if (e.shiftKey) {
          i < 0 ? S.push({ k: k, dir: "asc" }) : next ? (S[i] = { k: k, dir: next }) : S.splice(i, 1);
        } else S = next ? [{ k: k, dir: next }] : [];
        S.length ? (T.sort = S) : delete T.sort;
        save();
        tvKeepScroll(() => renderTkAll());
      }),
  );
  // widths: drag a header's edge; kept for the person
  w.querySelectorAll("[data-tvrs]").forEach((h) =>
    h.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const k = h.dataset.tvrs,
        col = w.querySelector(`col[data-tvc="${k}"]`),
        x0 = e.clientX,
        w0 = col ? parseFloat(col.style.width) : 120;
      const move = (ev) => col && (col.style.width = Math.max(72, Math.min(720, w0 + ev.clientX - x0)) + "px");
      const up = () => {
        document.removeEventListener("pointermove", move);
        document.removeEventListener("pointerup", up);
        const T = tvPrefs().table;
        T.widths = T.widths || {};
        col && (T.widths[k] = Math.round(parseFloat(col.style.width)));
        save();
      };
      document.addEventListener("pointermove", move);
      document.addEventListener("pointerup", up);
    }),
  );
  // the keyboard: arrows move between cells, Enter opens, D marks done, X selects, Escape clears the selection
  const fr = w.querySelector(".tv-tframe");
  fr &&
    fr.addEventListener("keydown", (e) => {
      const el = document.activeElement;
      if (!el || !fr.contains(el) || e.metaKey || e.ctrlKey || e.altKey) return;
      if (/^(SELECT|TEXTAREA)$/.test(el.tagName) || ("INPUT" === el.tagName && "checkbox" !== el.type)) return;
      const td = el.closest("td, th"),
        tr = el.closest("tr");
      if (!td || !tr) return;
      const rows = [...fr.querySelectorAll("thead tr, tr.tv-tr")],
        ri = rows.indexOf(tr),
        ci = [...tr.children].indexOf(td),
        focus = (f) => f && (f.focus(), f.scrollIntoView({ block: "nearest", inline: "nearest" }), !0),
        inCell = (c) => c && (c.querySelector('[data-tved="title"]') || c.querySelector("button, input"));
      const focusAt = (r, c) => {
        const R = rows[r];
        if (!R) return;
        const cells = [...R.children];
        for (let j = Math.min(c, cells.length - 1); j >= 0; j--) if (focus(inCell(cells[j]))) return;
      };
      const step = (dc) => {
        const cells = [...tr.children];
        for (let j = ci + dc; j >= 0 && j < cells.length; j += dc) if (focus(inCell(cells[j]))) return;
      };
      const k = e.key;
      if ("ArrowDown" === k) return e.preventDefault(), focusAt(ri + 1, ci);
      if ("ArrowUp" === k) return e.preventDefault(), focusAt(ri - 1, ci);
      if ("ArrowRight" === k) return e.preventDefault(), step(1);
      if ("ArrowLeft" === k) return e.preventDefault(), step(-1);
      const key = tr.dataset.tvrow;
      if (!key) return;
      if ("Enter" === k && "INPUT" === el.tagName) return e.preventDefault(), tkSheet(key);
      if ("d" === k || "D" === k) return e.preventDefault(), (tvFocusAt = { key: key, f: "title" }), tkCheckDone(key);
      if ("x" === k || "X" === k) {
        e.preventDefault();
        tvSel.has(key) ? tvSel.delete(key) : tvSel.add(key);
        tvFocusAt = { key: key, f: (el.dataset && el.dataset.tved) || "title" };
        return tvKeepScroll(() => renderTkAll());
      }
      if ("Escape" === k && tvSel.size && !document.getElementById("tv-pop")) return e.preventDefault(), tvSel.clear(), tvKeepScroll(() => renderTkAll());
    });
}
// a redraw keeps the page and the table frame where they were scrolled
function tvKeepScroll(fn) {
  const f = document.querySelector("#tkall-body .tv-tframe"),
    at = f ? [f.scrollTop, f.scrollLeft] : null,
    y = window.scrollY;
  fn();
  const g = document.querySelector("#tkall-body .tv-tframe");
  g && at && ((g.scrollTop = at[0]), (g.scrollLeft = at[1]));
  window.scrollTo(window.scrollX, y);
}
let tvDrag = null;
function tvWireDrop(zone, onDrop) {
  zone.addEventListener("dragover", (e) => {
    if (!tvDrag) return;
    e.preventDefault();
    e.dataTransfer && (e.dataTransfer.dropEffect = "move");
    zone.classList.add("tv-over");
  });
  zone.addEventListener("dragleave", (e) => zone.contains(e.relatedTarget) || zone.classList.remove("tv-over"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("tv-over");
    const d = tvDrag;
    tvDrag = null;
    d && onDrop(d);
  });
}
function tvWireDrag(el) {
  el.addEventListener("dragstart", (e) => {
    tvDrag = { key: el.dataset.tvrow, field: el.dataset.tvfield || "" };
    try {
      e.dataTransfer.setData("text/plain", tvDrag.key);
      e.dataTransfer.effectAllowed = "move";
    } catch (err) {}
    el.classList.add("tv-dragging");
  });
  el.addEventListener("dragend", () => (el.classList.remove("tv-dragging"), setTimeout(() => (tvDrag = null), 0)));
}
function tvWireBoard(w) {
  w.querySelectorAll(".tv-card[draggable]").forEach(tvWireDrag);
  w.querySelectorAll("[data-tvdrop]").forEach((z) => tvWireDrop(z, (d) => ("1" === z.dataset.tvcan ? tvBoardMove(d.key, z.dataset.tvdrop) : toast("A task moves into a job's column only"))));
  w.querySelectorAll("[data-tvqadd]").forEach(
    (i) =>
      (i.onkeydown = (e) => {
        if ("Enter" !== e.key) return;
        e.preventDefault();
        const t = i.value.trim();
        t && tvQuickAdd(i.dataset.tvqadd, t);
      }),
  );
  // the phone: one column at a time; the tabs jump, a swipe moves on, and the tab follows
  const B = w.querySelector(".tv-board-ph");
  if (!B) return;
  const tabs = [...w.querySelectorAll("[data-tvbtab]")],
    mark = (i) => tabs.forEach((t, j) => t.setAttribute("aria-selected", i === j ? "true" : "false"));
  tabs.forEach(
    (t) =>
      (t.onclick = () => {
        const i = +t.dataset.tvbtab,
          col = B.children[i];
        col && B.scrollTo({ left: col.offsetLeft - B.offsetLeft, behavior: "smooth" });
        mark(i);
      }),
  );
  let tm = 0;
  B.addEventListener(
    "scroll",
    () => {
      clearTimeout(tm);
      tm = setTimeout(() => {
        const cw = B.children[0] ? B.children[0].offsetWidth + 8 : B.clientWidth;
        mark(Math.max(0, Math.min(tabs.length - 1, Math.round(B.scrollLeft / Math.max(1, cw)))));
      }, 60);
    },
    { passive: !0 },
  );
}
function tvWireCal(w) {
  w.querySelectorAll(".tv-ev[draggable]").forEach(tvWireDrag);
  w.querySelectorAll("[data-tvday]").forEach((z) => tvWireDrop(z, (d) => tvCalDrop(d.key, d.field, z.dataset.tvday)));
  w.querySelectorAll("[data-tvcalmode]").forEach((b) => (b.onclick = () => ((tvPrefs().calMode = b.dataset.tvcalmode), save(), renderTkAll())));
  w.querySelectorAll("[data-tvcalgo]").forEach(
    (b) =>
      (b.onclick = () => {
        const n = +b.dataset.tvcalgo,
          C = tvCalRange();
        if (!n) tvCalAt = today();
        else if ("week" === C.mode) tvCalAt = iso(addDays(parse(C.from), 7 * n));
        else {
          const d = parse(C.from);
          tvCalAt = iso(new Date(d.getFullYear(), d.getMonth() + n, 1));
        }
        renderTkAll();
      }),
  );
}

// ---- the hooks ------------------------------------------------------------------------------------------------------
let tvDrawing = "";
{
  const base = renderTkAll;
  renderTkAll = function () {
    const own = tvMine() && tvMayUse(),
      keep = tkMode;
    tvPopClose();
    // the List draws first (its bar, chips and counts); the chosen layout then takes the list's place
    own && ((tkMode = "cards"), (tvDrawing = keep));
    try {
      base.apply(this, arguments);
    } finally {
      own && ((tkMode = keep), (tvDrawing = ""));
    }
    try {
      tvAfter();
    } catch (e) {
      console.warn("task views", e);
    }
  };
}
{
  const base = tkSetMode;
  tkSetMode = function (m) {
    tvSel.clear();
    if (!TV_OWN.includes(m)) return base.apply(this, arguments);
    tkMode = m;
    try {
      localStorage.setItem("sdp:tkmode", m);
    } catch (e) {}
    renderTkAll();
  };
}
// a new task lands on the list it is in; the Table keeps the person's layout (it highlights the row as the List does)
{
  const base = tkLand;
  tkLand = function (m) {
    const keep = tkMode;
    const r = base.apply(this, arguments);
    if ("table" === keep && tkMode !== keep && tvMayUse()) {
      tkMode = keep;
      try {
        renderTkAll();
      } catch (e) {}
    }
    return r;
  };
}
// search reads the task's ID ("PAD-23") as well as its words
{
  const base = t2Narrow;
  t2Narrow = function (R) {
    if (!t2Q) return base.apply(this, arguments);
    const q = t2Q;
    let out;
    t2Q = "";
    try {
      out = base.apply(this, arguments);
    } finally {
      t2Q = q;
    }
    const s = q.toLowerCase();
    return out.filter((x) => {
      const rec = /^(action|firm|hub)$/.test(x.kind) ? tvRec(x) : null;
      return `${tvRef(x, rec)} ${x.code || ""} ${x.title} ${x.project} ${x.assignee} ${x.owner || ""} ${x.notes || ""}`.toLowerCase().includes(s);
    });
  };
}
// the phone's one chip opens the sheet where filter, sort, group, layout and saved views live
{
  const base = tkFilterSheet;
  tkFilterSheet = function () {
    const m = base.apply(this, arguments);
    try {
      if (!m || !tvMayUse()) return m;
      const box = m.querySelector(".tkf");
      if (!box) return m;
      const btn = (attr, v, on, label) => `<button type="button" class="tkf-b ${on ? "on" : ""}" ${attr}="${esc(v)}">${esc(label)}</button>`,
        views = "home" === t2Ctx() ? `<div class="tkf-h">Saved Views</div><div class="tkf-row">${tvViews().map((v) => btn("data-tkfsv", v.id, tvIsOn(v), v.name)).join("")}${btn("data-tkfsvsave", "1", !1, "New View")}</div>` : "",
        lay = `<div class="tkf-h">Layout</div><div class="tkf-row">${TV_MODES.map(([k, n]) => btn("data-tkfmode", k, (tkMode || "cards") === k, n)).join("")}</div>`,
        S = tvSorts()[0],
        sort = "table" === tkMode ? `<div class="tkf-h">Sort</div><div class="tkf-row">${btn("data-tkfsort", "", !S, "List Order")}${["due", "follow", "owner", "status", "ref"].map((k) => btn("data-tkfsort", k, S && S.k === k, TV_COLS.find((c) => c.k === k).n)).join("")}</div>` : "";
      box.insertAdjacentHTML("afterbegin", views + lay + sort);
      // in the Table the grouping is the table's own: Project, Owner, Status, Due Date, or none
      if ("table" === tkMode) {
        const gb = tvTableGroup(),
          row = [...box.querySelectorAll("[data-tkfgroup]")][0];
        row && (row.parentElement.innerHTML = TV_GROUPS.map(([k, n]) => btn("data-tkftg", k, gb === k, n.replace(/^No Grouping$/, "None"))).join(""));
      }
      const go = (fn) => (e) => {
        e.preventDefault();
        mbCloseModal();
        fn(e.currentTarget);
        try {
          renderTkAll();
        } catch (err) {}
        window.scrollTo(0, 0);
      };
      m.querySelectorAll("[data-tkfsv]").forEach((b) => (b.onclick = go((el) => tvApply(el.dataset.tkfsv))));
      m.querySelectorAll("[data-tkfsvsave]").forEach((b) => (b.onclick = (e) => (e.preventDefault(), mbCloseModal(), tvSaveDialog())));
      m.querySelectorAll("[data-tkfmode]").forEach((b) => (b.onclick = go((el) => tkSetMode(el.dataset.tkfmode))));
      m.querySelectorAll("[data-tkfsort]").forEach((b) => (b.onclick = go((el) => (el.dataset.tkfsort ? (tvPrefs().table.sort = [{ k: el.dataset.tkfsort, dir: "asc" }]) : delete tvPrefs().table.sort, save()))));
      m.querySelectorAll("[data-tkftg]").forEach((b) => (b.onclick = go((el) => ((tvPrefs().table.group = el.dataset.tkftg), save()))));
    } catch (e) {
      console.warn("task layouts on the phone", e);
    }
    return m;
  };
}
// the chip on the phone names the layout when it is not the List
{
  const base = tkChipLabel;
  tkChipLabel = function (ctx) {
    const s = base.apply(this, arguments);
    try {
      const m = tvDrawing || tkMode;
      if (tvMayUse() && TV_OWN.includes(m) && tvPhone()) return `${s} · ${(TV_MODES.find(([k]) => k === m) || [])[1] || ""}`;
    } catch (e) {}
    return s;
  };
}
// The fields the meeting adds (lane A) reach the rows every list reads: a record waiting on someone is in Waiting
// (t2ViewOf "blocked"), so the chip, the board's column and the saved view count one set.
{
  const base = tkItems;
  tkItems = function () {
    const out = base.apply(this, arguments) || [];
    try {
      out.forEach((x) => {
        if (x.__tv || !/^(action|firm|hub)$/.test(x.kind)) return;
        x.__tv = 1;
        const rec = tvRec(x);
        if (!rec) return;
        const w = rec.waitingOn,
          wn = w && "object" == typeof w ? w.name || "" : "string" == typeof w ? w : "";
        !x.done && !x.waitsOn && (wn || "waiting" === rec.status) && (x.waitsOn = wn || "someone outside the team");
        rec.followUp && (x.followUp = rec.followUp);
        rec.watchUntil && (x.watchUntil = rec.watchUntil);
      });
    } catch (e) {
      console.warn("task view fields", e);
    }
    return out;
  };
}

// ---- the look --------------------------------------------------------------------------------------------------------
(() => {
  const css = `
#v-tkall .tv-saved{display:flex;flex-wrap:wrap;gap:4px;margin:0 0 12px;border-bottom:1px solid var(--rule-2)}
#v-tkall .tv-sv{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border:0;border-bottom:2px solid transparent;background:none;font-size:15px;color:var(--ink-2);cursor:pointer;margin-bottom:-1px}
#v-tkall .tv-sv:hover{color:var(--ink)}
#v-tkall .tv-sv.on{border-bottom-color:var(--accent);color:var(--ink);font-weight:600}
#v-tkall .tv-svnew{color:var(--ink-3)}
#v-tkall .tk-mode.tv-modes button,#v-tkall .tv-top .seg button,#v-tkall .tv-calbar .seg button{display:inline-flex;align-items:center;justify-content:center}
#v-tkall .tv-filters{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
#v-tkall .tv-fchip{display:inline-flex;align-items:center;border:1px solid var(--accent);border-radius:22px;background:var(--accent-bg,#eaf1fb);overflow:hidden}
#v-tkall .tv-fchip-b{min-height:36px;padding:0 4px 0 14px;border:0;background:none;font-size:14px;color:var(--ink);cursor:pointer}
#v-tkall .tv-fchip-x{display:grid;place-items:center;width:36px;min-height:36px;border:0;background:none;color:var(--ink-2);cursor:pointer}
#v-tkall .tv-fadd{display:inline-flex;align-items:center;gap:6px;min-height:36px;padding:0 14px;border:1px dashed var(--rule);border-radius:22px;background:none;font-size:14px;color:var(--ink-2);cursor:pointer}
#v-tkall .tv-host{border:0;background:none;overflow:visible;border-radius:0}
#v-tkall .tv-top{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 10px;min-height:44px}
#v-tkall .tv-top .btn{display:inline-flex;align-items:center;gap:6px;min-height:40px}
#v-tkall .tv-sum-line{font-size:15px;color:var(--ink-2)}
#v-tkall .late,#v-tkall .tv-glate{color:var(--bad,#b3261e)}
#v-tkall .tv-empty{padding:18px 4px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:15px}
#v-tkall .tv-empty .btn{min-height:44px}
#v-tkall .tv-ref{flex:0 0 auto;font:500 13px/18px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink-3);white-space:nowrap;margin-right:8px}
#v-tkall .tk2-sub .tv-ref{margin-right:0}
/* status pills: one colour each, red only for late */
.tv-pill{display:inline-flex;align-items:center;height:26px;padding:0 10px;border-radius:13px;font-size:13px;font-weight:600;white-space:nowrap;background:#eef0f3;color:#4a5160;border:1.5px solid transparent;box-sizing:border-box}
.tv-pill.tv-st-doing{background:#e3eefc;color:#1f5fbf}
.tv-pill.tv-st-waiting{background:#fff1d6;color:#8a5300}
.tv-pill.tv-st-done{background:#e5f4e7;color:#22702a}
.tv-pill.tv-st-fyi{background:none;border-color:#9aa1ad;color:#4a5160}
.tv-pill.tv-st-x{background:none;padding:0;color:var(--ink);font-size:15px}
.tv-av{display:inline-grid;place-items:center;flex:0 0 24px;width:24px;height:24px;border-radius:50%;background:hsl(var(--h) 60% 90%);color:hsl(var(--h) 45% 32%)}
/* the cells: one control, the same everywhere */
#v-tkall .tv-c{display:inline-flex;align-items:center;gap:6px;min-height:44px;min-width:44px;padding:0 8px;border:0;border-radius:8px;background:none;font-size:15px;color:var(--ink-2);cursor:pointer;white-space:nowrap;overflow:hidden;max-width:100%;box-sizing:border-box;text-align:left}
#v-tkall .tv-c:hover,#v-tkall .tv-c:focus-visible{background:var(--paper-2)}
#v-tkall .tv-c span{overflow:hidden;text-overflow:ellipsis}
#v-tkall .tv-c.tv-empty{color:var(--ink-3)}
#v-tkall .tv-c.late{color:var(--bad,#b3261e);font-weight:600}
#v-tkall .tv-c.today{color:var(--ink);font-weight:600}
#v-tkall .tv-c.tv-own{color:var(--ink)}
#v-tkall .tv-wait.on .tv-chip-in{display:inline-block;padding:3px 10px;border-radius:13px;background:#fff1d6;color:#8a5300;font-size:13px;font-weight:600;overflow:hidden;text-overflow:ellipsis}
#v-tkall .tv-wait.on.late .tv-chip-in{background:#fdecea;color:var(--bad,#b3261e)}
#v-tkall .tv-check{flex:0 0 44px;width:44px;height:44px;border:0;background:none;display:grid;place-items:center;cursor:pointer;padding:0}
#v-tkall .tv-check>span{display:block;width:22px;height:22px;border:2px solid var(--ink-3);border-radius:50%;box-sizing:border-box}
#v-tkall .tv-check:hover>span{background:var(--paper-2)}
#v-tkall .late .tv-check>span{border-color:var(--bad,#b3261e)}
#v-tkall .tv-donemark>span{background:var(--ok-2,#2e7d32);border-color:var(--ok-2,#2e7d32)}
#v-tkall .tv-tt{flex:1 1 auto;min-width:0;min-height:44px;display:flex;flex-direction:column;justify-content:center;border:0;background:none;padding:0 8px 0 0;text-align:left;font-size:15px;color:var(--ink);cursor:pointer}
#v-tkall .tv-ttx{display:block;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:15px;line-height:20px}
#v-tkall .tv-sub2{display:block;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;line-height:18px;color:var(--ink-3)}
#v-tkall .tv-sub2 b{font-weight:600;color:var(--ink-2)}
#v-tkall .done .tv-ttx{color:var(--ink-3);text-decoration:line-through}
/* the List's rows (tasks.js) with the cells on a wide screen */
#v-tkall .tk2-row .tv-cells{display:flex;align-items:center;gap:8px;flex:0 0 auto;margin-left:8px}
#v-tkall .tk2-row .tv-cells>.tv-own{width:112px}
#v-tkall .tk2-row .tv-cells>.tv-due{width:112px}
#v-tkall .tk2-row .tv-cells>.tv-stc{width:116px}
#v-tkall .tk2-row .tv-cells>.tv-wait{max-width:200px}
#v-tkall .tk2-row.tv-3acts.swiped .tk2-slide{transform:translateX(-252px)}
#v-tkall .tk2-act.tv-act-done{background:var(--ok-2,#2e7d32)}
/* groups */
#v-tkall .tv-grp{margin:0 0 14px}
#v-tkall .tv-ghd,#v-tkall .tv-shd{display:flex;align-items:center;gap:10px;width:100%;min-height:44px;border:0;background:none;padding:0 6px;text-align:left;cursor:pointer;color:var(--ink)}
#v-tkall .tv-ghd{font-size:16px;font-weight:700}
#v-tkall .tv-shd{font-size:14px;font-weight:600;color:var(--ink-2)}
#v-tkall .tv-ghd .n,#v-tkall .tv-shd .n{font-weight:500;color:var(--ink-3);font-size:14px}
#v-tkall .tv-glate{font-size:13px;font-weight:600}
#v-tkall .tv-bar{display:inline-block;width:72px;height:4px;border-radius:2px;background:var(--rule-2);overflow:hidden;margin-left:4px}
#v-tkall .tv-bar i{display:block;height:100%;background:var(--ok-2,#2e7d32);border-radius:2px}
#v-tkall .tv-gdone{font-size:12px;font-weight:500;color:var(--ink-3)}
/* the Table: no cell borders, a faint line between rows, a highlight on hover */
#v-tkall .tv-tframe{position:relative;max-height:calc(100vh - 250px);overflow:auto;background:var(--paper);-webkit-overflow-scrolling:touch;overscroll-behavior-x:contain}
#v-tkall .tv-table{width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:15px}
#v-tkall .tv-table th,#v-tkall .tv-table td{border:0 !important;padding:0 4px;height:60px;box-sizing:border-box;vertical-align:middle;text-align:left;overflow:hidden;white-space:nowrap;background-color:transparent}
#v-tkall .tv-tframe.dense .tv-table td{height:44px}
#v-tkall .tv-tframe.dense .tv-sub2{display:none}
#v-tkall .tv-table tr.tv-tr td{background-image:linear-gradient(var(--rule-2),var(--rule-2));background-size:100% 1px;background-position:0 100%;background-repeat:no-repeat}
#v-tkall .tv-table tr.tv-tr:hover td{background-color:var(--paper-2)}
#v-tkall .tv-table tr.tv-tr.sel td{background-color:var(--accent-bg,#eaf1fb)}
#v-tkall .tv-table thead th{position:sticky;top:0;z-index:3;background:var(--paper);height:44px;font-size:13px;font-weight:600;color:var(--ink-3);box-shadow:0 1px 0 var(--rule-2)}
#v-tkall .tv-sortb{display:inline-flex;align-items:center;gap:4px;min-height:44px;width:calc(100% - 8px);border:0;background:none;padding:0 8px;font:inherit;color:inherit;text-align:left;cursor:pointer}
#v-tkall .tv-sortb:hover{color:var(--ink)}
#v-tkall .tv-sortn{font-size:11px;color:var(--accent)}
#v-tkall .tv-rs{position:absolute;right:0;top:10px;bottom:10px;width:8px;cursor:col-resize;border-right:2px solid transparent}
#v-tkall .tv-table th:hover .tv-rs{border-right-color:var(--rule)}
#v-tkall .tv-cb{display:grid;place-items:center;width:44px;height:44px;cursor:pointer}
#v-tkall .tv-cb input{width:18px;height:18px;margin:0;cursor:pointer;accent-color:var(--accent)}
#v-tkall .tv-tcell{display:flex;align-items:center;min-width:0}
#v-tkall .tv-txt{display:block;padding:0 8px;overflow:hidden;text-overflow:ellipsis;color:var(--ink-2)}
#v-tkall .tv-pri-high{color:var(--bad,#b3261e);font-weight:600}
#v-tkall .tv-table td .tv-c{max-width:100%}
#v-tkall .tv-tr .tv-c.tv-wait.tv-empty,#v-tkall .tv-tr .tv-c.tv-fu.tv-empty,#v-tkall .tk2-row .tv-c.tv-wait.tv-empty{visibility:hidden}
#v-tkall .tv-tr:hover .tv-c.tv-empty,#v-tkall .tv-tr:focus-within .tv-c.tv-empty{visibility:visible}
#v-tkall .tv-grow td{height:auto;padding:16px 0 4px;background:var(--paper)}
#v-tkall .tv-grow .tv-ghd{width:auto}
#v-tkall .tv-bulk{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:60;display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:8px 10px 8px 18px;border:1px solid var(--rule);border-radius:14px;background:var(--paper);box-shadow:0 10px 30px rgba(0,0,0,.18);font-size:15px}
#v-tkall .tv-bulk .btn{min-height:44px}
#v-tkall .tv-ic{width:44px;padding:0;display:inline-grid;place-items:center}
/* the Board */
#v-tkall .tv-board{display:flex;gap:12px;align-items:flex-start;overflow-x:auto;padding-bottom:8px;overscroll-behavior-x:contain}
#v-tkall .tv-bcol{flex:0 0 292px;min-width:0;background:var(--paper-2);border-radius:12px;padding:8px;box-sizing:border-box;min-height:140px}
#v-tkall .tv-bcol.tv-over{outline:2px solid var(--accent);outline-offset:-2px}
#v-tkall .tv-bextra{opacity:.85}
#v-tkall .tv-bhd{display:flex;align-items:center;gap:8px;padding:4px 4px 10px;font-size:14px}
#v-tkall .tv-bhd .n{color:var(--ink-3);font-weight:600}
#v-tkall .tv-bcards{display:flex;flex-direction:column;gap:8px}
#v-tkall .tv-card{background:var(--paper);border:1px solid var(--rule-2);border-radius:10px;padding:10px 10px 4px 12px;cursor:pointer;box-shadow:0 1px 2px rgba(0,0,0,.05)}
#v-tkall .tv-card:hover{border-color:var(--rule)}
#v-tkall .tv-card.tv-dragging{opacity:.4}
#v-tkall .tv-card-top{display:flex;align-items:center;min-height:18px;font-size:13px;color:var(--ink-3)}
#v-tkall .tv-card-due.late{color:var(--bad,#b3261e);font-weight:600}
#v-tkall .tv-card-t{font-size:15px;line-height:21px;color:var(--ink);margin:4px 0 4px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;word-break:break-word}
#v-tkall .done .tv-card-t{color:var(--ink-3);text-decoration:line-through}
#v-tkall .tv-card-ft,#v-tkall .tv-card-w{display:flex;align-items:center;gap:8px;margin:0 -6px}
#v-tkall .tv-card-w{margin-bottom:8px}
#v-tkall .tv-bempty{padding:10px 6px}
#v-tkall .tv-qadd{display:flex;align-items:center;gap:6px;margin-top:8px;padding:0 8px;border-radius:8px;color:var(--ink-3)}
#v-tkall .tv-qadd:focus-within{background:var(--paper)}
#v-tkall .tv-qadd input{flex:1 1 auto;min-width:0;height:44px;border:0;background:none;font-size:15px;outline:none}
#v-tkall .tv-btabs{display:flex;gap:8px;overflow-x:auto;margin:0 0 8px;padding-bottom:2px}
#v-tkall .tv-btab{flex:0 0 auto;min-height:44px;padding:0 14px;border:1px solid var(--rule);border-radius:22px;background:var(--paper);font-size:14px;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
#v-tkall .tv-btab[aria-selected=true]{border-color:var(--accent);font-weight:600}
#v-tkall .tv-btab .n{color:var(--ink-3)}
#v-tkall .tv-board-ph{scroll-snap-type:x mandatory;gap:8px}
#v-tkall .tv-board-ph .tv-bcol{flex:0 0 calc(100% - 28px);scroll-snap-align:start}
/* the Calendar: due solid by project, follow-ups outlined */
#v-tkall .tv-calbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 10px}
#v-tkall .tv-calbar .btn{min-height:44px}
#v-tkall .tv-caltitle{font-size:16px;margin-left:4px}
#v-tkall .tv-legend{display:flex;gap:8px;align-items:center}
#v-tkall .tv-legend .tv-ev{width:auto;--h:212;cursor:default}
#v-tkall .tv-cal{border-radius:12px;overflow:hidden;background:var(--paper);box-shadow:0 0 0 1px var(--rule-2)}
#v-tkall .tv-dows,#v-tkall .tv-days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr))}
#v-tkall .tv-dow{padding:8px 10px;font-size:13px;font-weight:600;color:var(--ink-3)}
#v-tkall .tv-day{min-height:116px;padding:4px;box-shadow:inset 0 1px 0 var(--rule-2);min-width:0}
#v-tkall .tv-cal.week .tv-day{min-height:360px}
#v-tkall .tv-day.tv-outm{background:var(--paper-2)}
#v-tkall .tv-day.tv-outm .tv-dn{color:var(--ink-3)}
#v-tkall .tv-day.tv-isday .tv-dn{color:var(--accent);font-weight:700}
#v-tkall .tv-day.tv-over{outline:2px solid var(--accent);outline-offset:-2px}
#v-tkall .tv-dn{font-size:14px;color:var(--ink-2);padding:2px 6px 4px;display:flex;align-items:center;gap:6px}
#v-tkall .tv-tdy{font-size:12px;font-weight:600}
#v-tkall .tv-evs{display:flex;flex-direction:column;gap:4px}
#v-tkall .tv-ev{display:flex;align-items:center;gap:4px;width:100%;min-height:28px;padding:2px 8px;border:1.5px solid transparent;border-radius:6px;background:hsl(var(--h) 65% 92%);font-size:13px;line-height:17px;color:hsl(var(--h) 45% 26%);text-align:left;cursor:pointer;overflow:hidden;white-space:nowrap;box-sizing:border-box}
#v-tkall .tv-ev .tv-ref{margin-right:2px;font-size:11px;color:inherit;opacity:.75}
#v-tkall .tv-evt{overflow:hidden;text-overflow:ellipsis}
#v-tkall .tv-ev.tv-ev-fu{background:none;border-color:hsl(var(--h) 45% 55%)}
#v-tkall .tv-ev.late{border-color:var(--bad,#b3261e);color:var(--bad,#b3261e)}
#v-tkall .tv-ev.done{opacity:.6;text-decoration:line-through}
#v-tkall .tv-tray{margin:12px 0 0}
#v-tkall .tv-trayrows{display:flex;flex-wrap:wrap;gap:8px;padding:4px 0 0 28px}
#v-tkall .tv-trayrows .tv-ev{width:auto;max-width:100%;min-height:44px;font-size:15px;padding:0 12px}
/* the picker */
.tv-pop{position:fixed;z-index:9000;width:340px;max-width:calc(100vw - 16px);background:var(--paper,#fff);border:1px solid var(--rule,#ddd);border-radius:12px;box-shadow:0 12px 32px rgba(0,0,0,.18);padding:10px 12px 12px;box-sizing:border-box;font-size:15px}
.tv-pop-hd{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:0 0 6px}
.tv-pop-x{width:44px;height:44px;border:0;background:none;display:grid;place-items:center;cursor:pointer;color:var(--ink-2);margin:-8px -8px -8px 0}
.tv-pop-note{margin:0 0 8px}
.tv-chips{display:flex;flex-wrap:wrap;gap:8px}
.tv-people,.tv-menu{display:flex;flex-direction:column;gap:2px;max-height:340px;overflow:auto}
.tv-person,.tv-mi{display:flex;align-items:center;gap:10px;min-height:44px;padding:4px 8px;border:0;border-radius:8px;background:none;text-align:left;font-size:15px;cursor:pointer}
.tv-person:hover,.tv-mi:hover,.tv-person:focus-visible,.tv-mi:focus-visible{background:var(--paper-2,#f4f4f4)}
.tv-person.on,.tv-mi.on{background:var(--accent-bg,#eaf1fb)}
.tv-person .grow{display:flex;flex-direction:column}
.tv-person small{font-size:12px;color:var(--ink-3,#777)}
.tv-person[hidden]{display:none}
.tv-psearch{width:100%;height:44px;font-size:16px;border:1px solid var(--rule,#ddd);border-radius:8px;padding:0 10px;margin:0 0 8px;box-sizing:border-box}
.tv-chip{display:inline-flex;flex-direction:column;align-items:flex-start;justify-content:center;min-height:44px;min-width:44px;padding:4px 12px;border:1px solid var(--rule,#ddd);border-radius:10px;background:var(--paper,#fff);font-size:15px;line-height:18px;cursor:pointer;box-sizing:border-box}
.tv-chip small{font-size:12px;color:var(--ink-3,#777)}
.tv-chip.on{border-color:var(--accent);background:var(--accent-bg,#eaf1fb);font-weight:600}
.tv-pick{position:relative;overflow:hidden}
.tv-pick input{position:absolute;inset:0;opacity:0;width:100%;height:100%;cursor:pointer}
.tv-f{display:flex;flex-direction:column;gap:4px;margin:0 0 10px;font-size:13px;color:var(--ink-2)}
.tv-f input{height:44px;font-size:16px;border:1px solid var(--rule,#ddd);border-radius:8px;padding:0 10px}
.tv-pop-ft{display:flex;justify-content:flex-end;gap:8px;margin-top:8px}
.tv-pop-ft .btn{min-height:44px}
.tv-go{background:var(--accent);color:#fff;border-color:var(--accent)}
.tv-colset{display:flex;flex-direction:column;max-height:380px;overflow:auto}
.tv-colck{display:flex;align-items:center;gap:10px;min-height:44px;font-size:15px;cursor:pointer}
.tv-colck input{width:18px;height:18px}
.tv-colck.fixed{color:var(--ink-3)}
.tv-myviews{display:flex;flex-direction:column;gap:8px}
.tv-myv{display:flex;align-items:center;gap:8px}
.tv-myv .btn{min-height:44px}
.tv-pop-sheet{left:0 !important;right:0;bottom:0;top:auto !important;width:100%;max-width:none;border-radius:16px 16px 0 0;padding:10px 16px calc(16px + env(safe-area-inset-bottom));max-height:80vh;overflow:auto}
/* a task opens in a panel on the right on a wide screen, so the table stays in view (tkSheet, restyled) */
@media (min-width:1024px){
  #mbm.tks-on{background:transparent;pointer-events:none;justify-content:flex-end;align-items:stretch;padding:0;overflow:hidden}
  #mbm.tks-on .mbm-box{pointer-events:auto;width:440px;max-width:440px;height:100vh;max-height:100vh;border-radius:0;display:flex;flex-direction:column;box-shadow:-10px 0 30px rgba(0,0,0,.14);border-left:1px solid var(--rule)}
  #mbm.tks-on .mbm-bd{flex:1 1 auto;overflow:auto}
  #mbm.tks-on .mbm-ft{border-top:1px solid var(--rule-2)}
  body:has(#mbm.tks-on) #v-tkall{padding-right:452px;box-sizing:border-box}
}
@media (max-width:760px){
  #v-tkall .tv-top{margin:0 0 12px}
  #v-tkall .tv-top select,#v-tkall .tv-top .btn{min-height:44px}
  #v-tkall .tv-top .seg,#v-tkall .tv-calbar .seg{gap:8px;display:inline-flex}
  #v-tkall .tv-top .seg > button,#v-tkall .tv-calbar .seg > button,#v-tkall .tv-btabs > button{min-height:44px !important;border-radius:22px}
  #v-tkall .tv-cards .tv-ghd{margin-bottom:4px}
  #v-tkall .tv-host{margin:0}
  #v-tkall .tv-cards{margin:0 -16px}
  #v-tkall .tv-cards .tv-ghd{padding-left:16px}
  #v-tkall .tv-gdone{display:none}
  #v-tkall .tv-calbar .tv-caltitle{flex:1 1 100%;margin:0}
  #v-tkall .tv-legend{display:none}
  #v-tkall .tv-cal.month .tv-day{min-height:64px;padding:2px}
  #v-tkall .tv-cal.month .tv-ev{min-height:22px;padding:1px 3px;font-size:11px}
  #v-tkall .tv-cal.month .tv-ev .tv-ref{display:none}
  #v-tkall .tv-dow{padding:6px 4px;font-size:12px}
  #v-tkall .tv-wk-ph{display:flex;flex-direction:column}
  #v-tkall .tv-wk-ph .tv-day{min-height:0;padding:8px 0}
  #v-tkall .tv-wk-ph .tv-evs{gap:8px}
  #v-tkall .tv-wk-ph .tv-ev{min-height:44px;font-size:15px;padding:0 12px}
  #v-tkall .tv-trayrows{padding-left:0}
}`;
  try {
    const s = document.createElement("style");
    (s.id = "tv-css"), (s.textContent = css), document.head.appendChild(s);
  } catch (e) {}
})();
/*<</taskviews.js>>*/
