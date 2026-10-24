/*<<meeting.js>>*/
/* ==== the task record and Meeting Mode (lane A of the Asana round, docs/TASKS_PLAN.md §2 Phase 1 items 3 and 4) =====
   Alan, 2026-10-23: the team meets Monday and Thursday at 10 and walks the board project by project, one task at a
   time, by IDs like PAD-23. The record has to carry what the meeting uses, and the meeting has to run from the app.
   Design gate (BACKLOG §1.16). The noun is the task; nothing new holds a task:
     - Its stores stay as they are (p.actions a job's to-dos, DB.tasks the firm's own lists, DB.hub.tasks sales) behind
       tkItems(), the one accessor. The new fields ride on those records:
         code         the key, "PAD-23". The field the Asana import already fills from its Task ID column, so a
                      re-import still matches; `key` on a tkItems row already means "kind:id:project" (t2Key,
                      tkResolve), so the human key is `code`, never `key`. Numbers are never reused.
         assignee     the owner, one internal person, always (Alan, 10-23). A vendor, consultant, outside designer or
                      client is never the owner: they are Waiting On.
         collaborators[], waitingOn {name, contactRef, what, promised, evidence}, followUp (the chase date), watchUntil,
         status (todo, doing, waiting, done, fyi), order, lastDiscussed {meetingId, at}, links[] beside the old link.
         comments are the record's own append-only thread (rec.thread, the tasks lane's): tkComments() reads them;
         notes move into it as the first comment. Attachments are the job's files (p.files) or the firm's (DB.files)
         linked {kind: "task", id}, the store a task's photos already use.
     - A board is a job (p.project.prefix, keyNext), a list of the firm's own (DB.company.tkBoards["s:<section>"]) or
       Sales. DB.company.tkBoards is a new map, not a list of tasks: the firm's own lists have no record of their own
       to hold a prefix and the next number.
     - The meeting is a record in the existing meetings store (DB.meetings, kind "team"), shown on Meetings with the
       Gemini notes. Meeting Mode is a view of Tasks (no menu item): Start Meeting on Tasks, for the owner and the
       coordinator. Minutes reach each person's Today as one line (the queue it already has), not a new list.
     - Settings: the cadence (DB.company.meetCadence, Monday and Thursday at 10) and the team's project order
       (DB.company.meetOrder) ride on the company record.
   Exports for lane B (the transcript reader): mtCurrent(), mtLog(change), mtScreenLog(), tkByCode(code).
--------------------------------------------------------------------------------------------------------------------- */
var tkRecReady = !1;
const TK_CODE_RE = /^([A-Z][A-Z0-9]{0,7})-(\d{1,5})$/;
const TK_STATUS = [
  ["todo", "To Do"],
  ["doing", "Doing"],
  ["waiting", "Waiting On"],
  ["done", "Done"],
  ["fyi", "FYI"],
];
const tkStatusSay = (s) => (TK_STATUS.find(([k]) => k === s) || TK_STATUS[0])[1];
const MM_IC = {
  prev: '<path d="M15 6l-6 6 6 6"/>',
  next: '<path d="M9 6l6 6-6 6"/>',
  cal: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16"/>',
  note: '<path d="M5 4h14v12H9l-4 4z"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  person: '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c1.2-3.6 4-5 7-5s5.8 1.4 7 5"/>',
  wait: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/>',
  info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
  skip: '<path d="M6 6l7 6-7 6z"/><path d="M17 6v12"/>',
  more: '<circle cx="5.5" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="18.5" cy="12" r="1.4"/>',
  plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
  team: '<circle cx="9" cy="9" r="3"/><circle cx="17" cy="10" r="2.5"/><path d="M3 19c.8-3 3.2-4.5 6-4.5s5.2 1.5 6 4.5"/><path d="M15 15.5c2.3 0 4.2 1 5 3.5"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  file: '<path d="M14 3H7a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V7z"/><path d="M14 3v4h4"/>',
};
const mmSvg = (k, s) => `<svg viewBox="0 0 24 24" width="${s || 18}" height="${s || 18}" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${MM_IC[k] || ""}</svg>`;
// "Thu 10/29": the meeting's way of saying a date
const tkDay = (d) => {
  const x = d && parse(d);
  return x ? `${DOW[x.getDay()]} ${fmt(d)}` : "";
};

// ---- who may own a task: a person on the team -----------------------------------------------------------------------
var tkIntMemo = null;
function tkInternal(name) {
  const n = String(name || "").trim();
  if (tkIntMemo) {
    if (!tkIntMemo.has(n)) tkIntMemo.set(n, tkInternal_(n));
    return tkIntMemo.get(n);
  }
  return tkInternal_(n);
}
function tkInternal_(n) {
  if (!n || TDY_NOT_PERSON.test(n) || /^the (group|team)$/i.test(n)) return null;
  const u = tdyUserOf(n);
  if (u) return { name: u.name, id: u.id, role: u.role };
  for (const [r, re] of TDY_ROLE_WORDS)
    if (re.test(n)) {
      const v = tdyRoleUser(r);
      if (v) return { name: v.name, id: v.id, role: v.role };
    }
  try {
    const c = crCanonName(n);
    if ((DB.employees || []).some((e) => e.name === c)) return { name: c, id: "", role: "" };
  } catch (e) {}
  return null;
}
// the people an owner is picked from: everyone who signs in on the team (never a client)
const tkOwnersList = () => tdyUsers().slice().sort((a, b) => (/^(crew|driver)$/.test(a.role) ? 1 : 0) - (/^(crew|driver)$/.test(b.role) ? 1 : 0) || a.name.localeCompare(b.name));
// who an outside party is, from the records the firm already keeps
function tkContactRef(name) {
  const n = String(name || "").trim().toLowerCase();
  if (!n) return null;
  const first = n.split(/\s+/)[0],
    hit = (s) => {
      const v = String(s || "").toLowerCase();
      return !!v && (v === n || v.startsWith(n) || (first.length > 2 && v.split(/\s+/)[0] === first));
    };
  const v = (DB.vendors || []).find((x) => hit(x.name) || (x.contact && hit(x.contact)));
  if (v) return { kind: "vendor", id: v.id };
  const c = (DB.clients || []).find((x) => hit(x.name) || (x.contacts || []).some((k) => hit(k.name)));
  if (c) return { kind: "client", id: c.id };
  const h = ((DB.hub && DB.hub.contacts) || []).find((x) => hit(`${x.first || ""} ${x.last || ""}`.trim()) || hit(x.name) || hit(x.company));
  if (h) return { kind: "consultant", id: h.id };
  const u = tdyUserOf(name);
  if (u && /^(foreman|crew|driver)$/.test(u.role)) return { kind: "foreman", id: u.id };
  return null;
}

// ---- the records behind the boards ----------------------------------------------------------------------------------
// every task that carries a key, with where it lives: {kind, rec, p, board}
function tkKeyedRecs() {
  const out = [];
  (DB.projects || []).forEach((p) => (p.actions || []).forEach((a) => a && out.push({ kind: "action", rec: a, p: p, board: "p:" + p.id })));
  asFirmTasks().forEach((a) => a && out.push({ kind: "firm", rec: a, p: null, board: "s:" + tkSectionOf(a) }));
  ((DB.hub && DB.hub.tasks) || []).forEach((a) => a && out.push({ kind: "hub", rec: a, p: null, board: "sales" }));
  return out;
}
// Every other kind of task the list shows carries an ID too (polish lane, 2026-10-24: most rows had none): a job's
// schedule lines a person owns and its open field items (the job's prefix), the open leads' next steps (Sales) and
// the firm's renewals (Office). They take numbers from the same boards, so a number is still never given twice. They
// get a key only; the meeting, its agenda and the owner sweep stay on the records above (tkKeyedRecs).
const TK_SCHED_NOBODY = /^(crew|all|vendor|tbd|sub|subs)$/i;
function tkOtherRecs() {
  const out = [],
    has = (r) => !!String(r.code || "").trim();
  (DB.projects || []).forEach((p) => {
    (p.tasks || []).forEach((t) => {
      const o = String((t && t.owner) || "").trim();
      t && (has(t) || ("milestone" !== t.type && "done" !== t.status && o && !TK_SCHED_NOBODY.test(o))) && out.push({ kind: "sched", rec: t, p: p, board: "p:" + p.id });
    });
    (p.issues || []).forEach((i) => i && (has(i) || "open" === i.status) && out.push({ kind: "issue", rec: i, p: p, board: "p:" + p.id }));
  });
  (DB.leads || []).forEach((l) => l && (has(l) || (!["won", "lost"].includes(l.stage) && !["Unqualified", "Junk"].includes(l.leadStatus || "") && (l.next || l.nextDue))) && out.push({ kind: "lead", rec: l, p: null, board: "sales" }));
  (DB.obligations || []).forEach((o) => o && (has(o) || ("active" === o.status && o.expires)) && out.push({ kind: "ob", rec: o, p: null, board: "s:Office" }));
  return out;
}
const tkCodedRecs = () => tkKeyedRecs().concat(tkOtherRecs());
const tkSectionOf = (a) => String((a && a.section) || "").trim() || "Office";
const tkRecDone = (k, a) => ("hub" === k ? !!a.completed : "done" === a.status);
const tkRecKey = (r) => `${r.kind}:${r.rec.id}:${r.p ? r.p.id : ""}`;
function tkBoardMap() {
  DB.company = DB.company || {};
  return (DB.company.tkBoards = DB.company.tkBoards || {});
}
// where a board keeps its prefix and next number: a job's own record, or the firm's map
function tkBoardMeta(id) {
  if (/^p:/.test(id)) {
    const p = (DB.projects || []).find((q) => "p:" + q.id === id);
    return p ? p.project : null;
  }
  const M = tkBoardMap();
  return (M[id] = M[id] || { name: "sales" === id ? "Sales" : id.slice(2) });
}
function tkBoardName(id) {
  if (/^p:/.test(id)) {
    const p = (DB.projects || []).find((q) => "p:" + q.id === id);
    return p ? shortName(p) : "A Job";
  }
  return "sales" === id ? "Sales" : (tkBoardMap()[id] || {}).name || id.slice(2);
}
// every board the firm has: its jobs, its own lists, Sales
function tkBoards() {
  const ids = (DB.projects || []).map((p) => "p:" + p.id),
    add = (id) => ids.includes(id) || ids.push(id);
  asFirmTasks().forEach((a) => add("s:" + tkSectionOf(a)));
  Object.keys(tkBoardMap()).forEach((k) => /^s:/.test(k) && add(k));
  ((DB.hub && DB.hub.tasks) || []).length && add("sales");
  return ids;
}
// a prefix from the name: "Park Ave Duplex" PAD, "206 Lenox" LEN; never one another board holds
const TK_PREFIX_SKIP = /^(the|and|of|at|for|st|street|ave|avenue|place|pl|road|rd|design|turnover|floor|3rd|llc|inc)$/i;
function tkPrefixTaken(pre, exceptId) {
  const P = String(pre || "").toUpperCase();
  return tkBoards().some((id) => id !== exceptId && String((tkBoardMeta(id) || {}).prefix || "").toUpperCase() === P);
}
function tkPrefixGuess(name, exceptId) {
  const words = String(name || "")
      .replace(/\s+—.*$/, "")
      .split(/[^A-Za-z0-9]+/)
      .filter(Boolean),
    alpha = words.filter((w) => /^[A-Za-z]/.test(w) && !TK_PREFIX_SKIP.test(w)),
    tries = [];
  alpha.length >= 2 && tries.push(alpha.slice(0, 3).map((w) => w[0]).join(""));
  alpha[0] && tries.push(alpha[0].slice(0, 3), alpha[0].slice(0, 4));
  !alpha.length && words[0] && tries.push(("T" + words[0]).slice(0, 4));
  tries.push("T");
  for (const t of tries) {
    const c = t.toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (c && /^[A-Z]/.test(c) && !tkPrefixTaken(c, exceptId)) return c;
  }
  const b = (tries[0] || "T").toUpperCase().replace(/[^A-Z0-9]/g, "") || "T";
  for (let i = 2; i < 99; i++) if (!tkPrefixTaken(b + i, exceptId)) return b + i;
  return b + "X";
}
// the prefix a board's codes already use (an imported board keeps its PAD), the most common one
function tkPrefixInUse(recs) {
  const n = {};
  recs.forEach((r) => {
    const m = TK_CODE_RE.exec(String(r.rec.code || ""));
    m && (n[m[1]] = (n[m[1]] || 0) + 1);
  });
  return Object.keys(n).sort((a, b) => n[b] - n[a])[0] || "";
}
// a person renames the prefix: the board's keys follow, and the old key still finds the task (keyWas)
function tkSetPrefix(id, pre) {
  const P = String(pre || "")
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "")
    .slice(0, 8);
  if (!P || !/^[A-Z]/.test(P)) return { ok: !1, why: "A prefix is letters, then letters or numbers (PAD, OPS, F)" };
  if (tkPrefixTaken(P, id)) return { ok: !1, why: `${P} is already another project's prefix` };
  const meta = tkBoardMeta(id);
  if (!meta) return { ok: !1, why: "That project is no longer here" };
  const was = meta.prefix || "";
  meta.prefixSet = 1; // a person chose it: an import never replaces it
  if (was === P) return { ok: !0, prefix: P };
  meta.prefix = P;
  tkCodedRecs()
    .filter((r) => r.board === id)
    .forEach((r) => {
      const m = TK_CODE_RE.exec(String(r.rec.code || ""));
      if (!m || m[1] !== was) return;
      (r.rec.keyWas = r.rec.keyWas || []).push(r.rec.code);
      r.rec.code = `${P}-${m[2]}`;
    });
  try {
    audit("board", id, "prefix", was, P, "");
  } catch (e) {}
  return { ok: !0, prefix: P, was: was };
}

// ---- the sweep: keys, owners, Waiting On and comments, idempotent and the same on every device ---------------------
// It runs at boot and once per save (tkItems' sweep guard in src/app.js). Two devices that each added a task to the
// same board while apart both said PAD-24: the later-made one (then the larger id) moves to the next number, so both
// devices reach the same answer after they merge. A number is never given twice: keyNext only goes up.
function tkRecSweep() {
  if (!tkRecReady) return 0;
  let n = 0;
  try {
    const R = tkCodedRecs(),
      byBoard = {};
    R.forEach((r) => (byBoard[r.board] = byBoard[r.board] || []).push(r));
    Object.keys(byBoard).forEach((id) => {
      const L = byBoard[id],
        meta = tkBoardMeta(id);
      if (!meta) return;
      const inUse = tkPrefixInUse(L),
        cnt = (pre) => L.filter((r) => String(r.rec.code || "").toUpperCase().startsWith(pre + "-")).length;
      let was = "";
      if (!meta.prefix) (meta.prefix = inUse || tkPrefixGuess(tkBoardName(id), id)), n++;
      else if (!meta.prefixSet && inUse && inUse !== meta.prefix && cnt(inUse) > cnt(meta.prefix) && !tkPrefixTaken(inUse, id)) {
        // an imported board (Asana's PAD-23) keeps its prefix over the one the app guessed before the import; the
        // few tasks keyed with the guess move on to the board's numbers and keep their old key as keyWas
        was = meta.prefix;
        meta.prefix = inUse;
        n++;
      }
      const P = meta.prefix;
      let max = 0;
      L.forEach((r) => {
        const m = TK_CODE_RE.exec(String(r.rec.code || ""));
        m && m[1] === P && (max = Math.max(max, +m[2]));
      });
      const next = Math.max(+meta.keyNext || 1, max + 1);
      meta.keyNext !== next && ((meta.keyNext = next), n++);
      was &&
        L.forEach((r) => {
          const m = TK_CODE_RE.exec(String(r.rec.code || ""));
          if (!m || m[1] !== was) return;
          (r.rec.keyWas = r.rec.keyWas || []).push(r.rec.code);
          r.rec.code = `${P}-${meta.keyNext++}`;
        });
    });
    // one code, one task: the first made keeps it
    const seen = {},
      order = R.slice().sort((a, b) => String(a.rec.createdAt || a.rec.created || "").localeCompare(String(b.rec.createdAt || b.rec.created || "")) || String(a.rec.id).localeCompare(String(b.rec.id)));
    order.forEach((r) => {
      const c = String(r.rec.code || "").trim();
      if (!c) return;
      const k = c.toUpperCase();
      if (!seen[k]) return void (seen[k] = r);
      const meta = tkBoardMeta(r.board);
      (r.rec.keyWas = r.rec.keyWas || []).push(c);
      r.rec.code = `${meta.prefix}-${meta.keyNext++}`;
      seen[r.rec.code.toUpperCase()] = r;
      n++;
    });
    // a task with no key gets the next one on its board, in the board's own order
    R.forEach((r) => {
      if (String(r.rec.code || "").trim()) return;
      const meta = tkBoardMeta(r.board);
      if (!meta) return;
      r.rec.code = `${meta.prefix}-${meta.keyNext++}`;
      n++;
    });
    tkIntMemo = new Map();
    R.forEach((r) => /^(action|firm|hub)$/.test(r.kind) && (n += tkRecFix(r)));
  } catch (e) {
    console.warn("task record sweep", e);
  } finally {
    tkIntMemo = null;
  }
  return n;
}
// One record: an owner on the team, Waiting On as a record, comments with ids (a merge keeps both devices' comments
// only when each has an id), notes as the first comment.
function tkRecFix(r) {
  const a = r.rec;
  let n = 0;
  const done = tkRecDone(r.kind, a);
  if (!done) n += tkOwnerFix(r);
  if (a.waitsOn && !a.waitingOn && String(a.waitsOn).trim()) {
    const nm = String(a.waitsOn).trim();
    a.waitingOn = { name: nm, contactRef: tkContactRef(nm), what: "", promised: a.escalateOn || "", evidence: "" };
    !done && "todo" === (a.status || "todo") && "hub" !== r.kind && (a.status = "waiting");
    n++;
  }
  if (Array.isArray(a.thread)) a.thread.forEach((e, i) => e && !e.id && ((e.id = `${a.id}_c${i}`), n++));
  if (a.notes && String(a.notes).trim() && !a.notesMoved) {
    (a.thread = a.thread || []).unshift({ id: `${a.id}_n`, at: a.createdAt || a.created || "", by: a.createdBy || "", text: String(a.notes).trim(), ev: "notes" });
    a.notesMoved = 1;
    n++;
  }
  return n;
}
function tkOwnerFix(r) {
  const a = r.rec,
    raw = String(a.assignee || "").trim(),
    parts = raw
      .split(/\s*[\/,]\s*/)
      .map((s) => s.trim())
      .filter(Boolean),
    inside = [],
    outside = [];
  parts.forEach((pt) => {
    const u = tkInternal(pt);
    u ? inside.some((x) => x.name === u.name) || inside.push(u) : TDY_NOT_PERSON.test(pt) || /^(the (group|team|crew)|crew|all|tbd|sub|subs)$/i.test(pt) || outside.push(pt);
  });
  if (1 === parts.length && 1 === inside.length) {
    if (inside[0].name === raw) return 0;
    a.assignee = inside[0].name; // a role word ("SmartDesigns PM") is that person
    return 1;
  }
  if (inside.length) {
    a.assignee = inside[0].name;
    const C = (a.collaborators = a.collaborators || []);
    inside.slice(1).forEach((u) => C.includes(u.name) || C.push(u.name));
  } else {
    const lead = tdyLeadOf({ kind: r.kind, projectId: r.p ? r.p.id : "", createdBy: a.createdBy || "", area: "hub" === r.kind ? "sales" : a.area || "", obId: a.source && "obligation" === a.source.kind ? a.source.id : "" });
    if (!lead || !lead.name) return 0;
    a.assignee = lead.name;
    a.ownerFlag = { was: raw, why: outside.length ? "outside" : "none", to: lead.name, at: today() };
  }
  if (outside.length && !a.waitingOn) {
    const nm = outside.join(" / ");
    a.waitingOn = { name: nm, contactRef: tkContactRef(outside[0]), what: "", promised: a.escalateOn || "", evidence: "" };
    a.waitsOn = nm;
    "todo" === (a.status || "todo") && "hub" !== r.kind && (a.status = "waiting");
  }
  return 1;
}

// ---- reading the record ---------------------------------------------------------------------------------------------
function tkByCode(code) {
  const c = String(code || "").trim().toUpperCase();
  if (!c) return null;
  const R = tkKeyedRecs();
  const r = R.find((x) => String(x.rec.code || "").toUpperCase() === c) || R.find((x) => (x.rec.keyWas || []).some((k) => String(k).toUpperCase() === c));
  return r ? Object.assign({ key: tkRecKey(r) }, r) : null;
}
const tkCodeOfKey = (key) => {
  try {
    const R = tkResolve(key);
    return (R && R.rec && R.rec.code) || "";
  } catch (e) {
    return "";
  }
};
function tkComments(rec) {
  return ((rec && rec.thread) || []).filter((e) => e && e.text).map((e) => ({ id: e.id || "", by: e.by || "", at: e.at || "", text: e.text }));
}
function tkStatusOf(kind, rec) {
  if (!rec) return "todo";
  if (tkRecDone(kind, rec)) return "done";
  return /^(doing|waiting|fyi)$/.test(rec.status || "") ? rec.status : "todo";
}
function tkWaitSay(W, short) {
  if (!W || !W.name) return "";
  return `Waiting on ${W.name}${W.what ? `: ${W.what}` : ""}${W.promised ? `, promised ${tkDay(W.promised)}` : ""}`.slice(0, short ? 80 : 400);
}
// the link kinds a task already uses (rec.link), plus vendor, bill, file and mail
const TK_LINK_SAY = { vendor: "Vendor", po: "Purchase Order", bill: "Bill", dec: "Decision", file: "File", comm: "Email", co: "Change Order", mat: "Material", task: "Schedule Line", insp: "Inspection" };
function tkLinks(rec) {
  const out = [];
  [rec && rec.link].concat((rec && rec.links) || []).forEach((l) => l && l.kind && l.id && !out.some((o) => o.kind === l.kind && o.id === l.id) && out.push(l));
  return out;
}
function tkLinkInfo(l, pid) {
  const p = (DB.projects || []).find((q) => q.id === pid) || null;
  try {
    if ("vendor" === l.kind) {
      const v = (DB.vendors || []).find((x) => x.id === l.id);
      return v && { label: `Vendor · ${v.name}`, go: () => openVendor(v.id) };
    }
    if ("po" === l.kind) {
      const po = (DB.pos || []).find((x) => x.id === l.id);
      return po && { label: `Purchase Order ${po.number} · ${po.vendor || ""}`.trim(), go: () => flowGo.po(po)() };
    }
    if ("bill" === l.kind) {
      const b = (DB.bills || []).find((x) => x.id === l.id);
      return b && { label: `Bill ${b.number || ""} · ${b.vendor || ""} · ${money(+b.amount || 0)}`.replace(/\s+/g, " "), go: () => flowGo.bill(b)() };
    }
    if ("dec" === l.kind) {
      const q = p || (DB.projects || []).find((x) => (x.decisions || []).some((d) => d.id === l.id));
      const d = q && (q.decisions || []).find((x) => x.id === l.id);
      return d && { label: `Decision · ${d.name}`, go: () => (setCurrent(q.id), (view = "dec"), render()) };
    }
    if ("file" === l.kind) {
      const q = p || (DB.projects || []).find((x) => (x.files || []).some((f) => f.id === l.id));
      const f = (q && (q.files || []).find((x) => x.id === l.id)) || (DB.files || []).find((x) => x.id === l.id);
      return f && { label: `File · ${f.name}`, go: () => (q ? (setCurrent(q.id), (view = "files"), render()) : ((view = "files"), render())) };
    }
    if ("comm" === l.kind) {
      const c = (DB.comms || []).find((x) => x.id === l.id);
      return c && { label: `Email · ${tdWords(c.subject || "(no subject)", 8)}`, go: () => ((cmOpen = c.id), (view = "comms"), render()) };
    }
    if ("co" === l.kind) return { label: "Change Order", go: () => (p && setCurrent(p.id), (view = "billing"), render()) };
    if (p && TK_LINK_SAY[l.kind]) return { label: TK_LINK_SAY[l.kind], go: () => (setCurrent(p.id), (view = { mat: "mat", task: "sched", insp: "insp" }[l.kind] || "dash"), render()) };
  } catch (e) {}
  return null;
}
function tkAddLink(rec, l) {
  if (!rec || !l || !l.kind || !l.id) return !1;
  if (tkLinks(rec).some((o) => o.kind === l.kind && o.id === l.id)) return !1;
  rec.link ? (rec.links = rec.links || []).push({ kind: l.kind, id: l.id }) : (rec.link = { kind: l.kind, id: l.id });
  return !0;
}
// what a task links to, offered in the picker: the job's records first, then the firm's
function tkLinkChoices(pid) {
  const p = (DB.projects || []).find((q) => q.id === pid) || null,
    out = [];
  (DB.vendors || []).forEach((v) => out.push({ kind: "vendor", id: v.id, label: v.name, sub: "Vendor" }));
  (DB.pos || []).filter((x) => !pid || x.projectId === pid).forEach((x) => out.push({ kind: "po", id: x.id, label: `${x.number} ${x.vendor || ""}`.trim(), sub: "Purchase Order" }));
  (DB.bills || []).filter((x) => !pid || x.projectId === pid).forEach((x) => out.push({ kind: "bill", id: x.id, label: `${x.number || "Bill"} ${x.vendor || ""}`.trim(), sub: `Bill · ${money(+x.amount || 0)}` }));
  p && (p.decisions || []).forEach((d) => out.push({ kind: "dec", id: d.id, label: d.name, sub: "Decision" }));
  p && (p.files || []).forEach((f) => out.push({ kind: "file", id: f.id, label: f.name, sub: "File" }));
  (DB.comms || []).filter((c) => !pid || ((c.route || {}).projectId || c.projectId) === pid).slice(-40).forEach((c) => out.push({ kind: "comm", id: c.id, label: c.subject || "(no subject)", sub: `Email${c.from && c.from.name ? " · " + c.from.name : ""}` }));
  return out;
}
// attachments: the job's files (or the firm's) linked to the task, and the photos on its thread
function tkAttachments(R) {
  const x = R.x || {},
    p = x.projectId ? (DB.projects || []).find((q) => q.id === x.projectId) : null,
    out = [];
  ((p && p.files) || []).concat(DB.files || []).forEach((f) => f && f.link && "task" === f.link.kind && f.link.id === x.id && out.push({ id: f.id, name: f.name || "file", type: f.type || f.mime || "", url: f.dataUrl || f.url || "" }));
  ((R.rec && R.rec.thread) || []).forEach((e) => e && e.file && !out.some((o) => o.id === e.file) && out.push({ id: e.file, name: e.name || "file", type: e.type || "", url: "" }));
  return out;
}
function tkAddFile(R, file, url) {
  const x = R.x,
    p = x.projectId ? (DB.projects || []).find((q) => q.id === x.projectId) : null,
    id = uid("f"),
    me = tdyMe(),
    f = { id: id, name: file.name || `task-${today()}`, type: file.type || "", size: file.size || 0, cat: /^image\//.test(file.type || "") ? "photo" : "doc", date: today(), by: me.name || "", link: { kind: "task", id: x.id }, notes: x.title, shareClient: !1, persisted: !1, uploadedAt: appNowIso(), dataUrl: url };
  p ? (p.files = p.files || []).push(f) : (DB.files = DB.files || []).push(Object.assign(f, { projectId: "", at: today(), source: "upload" }));
  try {
    putBlob(id, url).then((ok) => (f.persisted = ok));
  } catch (e) {}
  R.rec && tkLog(R.rec, { ev: "file", file: id, name: f.name, type: f.type });
  return f;
}

// ---- writing the record (one way for the sheet, Meeting Mode and lane B) --------------------------------------------
const TK_OWNER_KEY = { action: "assignee", firm: "assignee", hub: "assignee" };
function tkSetOwner(R, name) {
  const u = tkInternal(name);
  if (!u) return { ok: !1, why: `${name || "Nobody"} is not on the team. An outside person is Waiting On; the owner is someone on the team.` };
  const rec = R.rec,
    was = rec.assignee || "";
  rec.assignee = u.name;
  delete rec.ownerFlag;
  rec.handoff && "offered" === rec.handoff.state && (rec.handoff = Object.assign({}, rec.handoff, { state: "superseded" }));
  (rec.collaborators || []).includes(u.name) && (rec.collaborators = rec.collaborators.filter((c) => c !== u.name));
  try {
    audit("task", rec.id, "owner", was, u.name, "");
  } catch (e) {}
  return { ok: !0, from: was, to: u.name };
}
function tkSetWaiting(rec, W) {
  const was = rec.waitingOn ? Object.assign({}, rec.waitingOn) : null;
  if (!W || !String(W.name || "").trim()) {
    delete rec.waitingOn;
    rec.waitsOn = "";
    "waiting" === rec.status && (rec.status = "todo");
    return was;
  }
  const nm = String(W.name).trim();
  rec.waitingOn = { name: nm, contactRef: W.contactRef || tkContactRef(nm), what: String(W.what || "").trim(), promised: W.promised || "", evidence: String(W.evidence || "").trim() };
  rec.waitsOn = nm;
  "done" !== rec.status && !rec.completed && (rec.status = "waiting");
  W.promised && !rec.followUp && (rec.followUp = W.promised);
  return was;
}
function tkSetStatus(kind, rec, s) {
  const was = tkStatusOf(kind, rec);
  if ("done" === s || "done" === was) return was; // done goes through tkToggle and its proof gate
  rec.status = s;
  return was;
}

// ---- the task sheet: the record's fields, edited where the task is opened ------------------------------------------
function tkRecSheetHtml(R, done) {
  // the field's sheet stays one job, big targets, plain words: the record's office fields are for the office
  if (/^(foreman|crew|driver|client)$/.test(role())) return "";
  const a = R.rec,
    x = R.x,
    st = tkStatusOf(x.kind, a),
    td = today(),
    links = tkLinks(a)
      .map((l) => [l, tkLinkInfo(l, x.projectId)])
      .filter(([, i]) => i),
    files = tkAttachments(R),
    dchips = (attr, cur) =>
      [
        ["Today", td],
        ["Tomorrow", iso(addDays(td, 1))],
        ["Next Meeting", mtNextMeeting()],
      ]
        .map(([n, d]) => `<button type="button" class="tks-chip ${cur === d ? "on" : ""}" ${attr}="${d}">${n}<small>${esc(tkDay(d))}</small></button>`)
        .join("") + `<label class="tks-chip tks-pick">Pick<input type="date" ${attr}pick value="${esc(cur || "")}" aria-label="Pick a day"></label>${cur ? `<button type="button" class="tks-chip" ${attr}="">Clear</button>` : ""}`;
  return `<div class="tks-rec">
  ${a.ownerFlag ? `<div class="tks-proof">${esc(a.assignee)} owns it because ${esc(a.ownerFlag.was || "nobody")} ${"outside" === a.ownerFlag.why ? "is not on the team" : "was named"}. <button type="button" class="btn sm" data-tksflagok>Confirm</button> <button type="button" class="btn sm" data-tksowner>Pick the Owner</button></div>` : ""}
  ${done ? "" : `<div class="tks-h">Status</div><div class="tks-chips">${TK_STATUS.filter(([k]) => "done" !== k)
    .map(([k, n]) => `<button type="button" class="tks-chip ${st === k ? "on" : ""}" data-tksst="${k}">${n}</button>`)
    .join("")}</div>`}
  <div class="tks-h">Waiting On</div>${a.waitingOn && a.waitingOn.name ? `<button type="button" class="tks-src" data-tkswait>${tkSvg("clock", 16)}<span class="grow">${esc(tkWaitSay(a.waitingOn))}${a.waitingOn.evidence ? `<small class="muted"> · ${esc(a.waitingOn.evidence)}</small>` : ""}</span><b>Edit</b></button>` : `<button type="button" class="btn" data-tkswait>Waiting On Someone</button>`}
  ${done ? "" : `<div class="tks-h">Follow Up</div><div class="tks-chips">${dchips("data-tksfu", a.followUp || "")}</div><div class="tks-h">Track Until</div><div class="tks-chips">${dchips("data-tkswatch", a.watchUntil || "")}</div>`}
  <div class="tks-h">Collaborators</div><div class="tks-chips">${(a.collaborators || []).map((c) => `<span class="tks-chip">${esc(c)}</span>`).join("")}<button type="button" class="tks-chip" data-tkscollab>${(a.collaborators || []).length ? "Change" : "Add"}</button></div>
  <div class="tks-h">Links</div><div class="tks-links">${links.map(([l, i], k) => `<button type="button" class="tks-src" data-tkslink="${k}">${tkSvg("link", 16)}<span class="grow">${esc(i.label)}</span><b>Open</b></button>`).join("")}<button type="button" class="btn" data-tkslinkadd>Link a Record</button></div>
  <div class="tks-h">Attachments</div><div class="tks-links">${files.map((f) => `<div class="tks-note">${esc(f.name)}</div>`).join("")}<label class="btn tks-file">Add a File<input type="file" data-tksfile hidden></label></div>
  ${a.lastDiscussed ? `<p class="small muted">Last discussed ${esc(tkDay(String(a.lastDiscussed.at || "").slice(0, 10)))}${(() => {
    const mt = mtTeam().find((y) => y.id === a.lastDiscussed.meetingId);
    return mt ? ` in ${esc(mt.title)}` : "";
  })()}.</p>` : ""}
</div>`;
}
function tkRecSheetWire(m, R, refresh) {
  if (!m.querySelector(".tks-rec")) return;
  const a = R.rec,
    x = R.x,
    q = (s) => m.querySelector(s),
    key = R.key,
    code = a.code || "",
    inMeeting = () => {
      const M = mtCurrent();
      return M && code ? M : null;
    };
  const ok = q("[data-tksflagok]");
  ok &&
    (ok.onclick = () => {
      const was = a.ownerFlag;
      delete a.ownerFlag;
      try {
        audit("task", a.id, "owner-confirmed", was ? was.was : "", a.assignee, "");
      } catch (e) {}
      refresh();
      toast(`${a.assignee} confirmed as the owner of ${code}`, [{ label: "Open", run: () => tkOpen(key) }]);
    });
  const ow = q("[data-tksowner]");
  ow && (ow.onclick = () => (mbCloseModal(), tkOwnerDialog(key)));
  m.querySelectorAll("[data-tksst]").forEach(
    (b) =>
      (b.onclick = () => {
        const s = b.dataset.tksst;
        if ("waiting" === s && !(a.waitingOn && a.waitingOn.name)) return mbCloseModal(), tkWaitDialog(key);
        const was = tkSetStatus(x.kind, a, s);
        if (was === s) return;
        "waiting" !== s && a.waitingOn && "todo" === s && tkSetWaiting(a, null);
        const M = inMeeting();
        M && mtLog({ taskKey: code, field: "status", from: was, to: s }, M);
        try {
          audit("task", a.id, "status", was, s, "");
        } catch (e) {}
        refresh();
        toast(`${code || tdWords(x.title, 6)}: ${tkStatusSay(s)}`, [{ label: "Open", run: () => tkOpen(key) }]);
      }),
  );
  const setDate = (field, d) => {
    const was = a[field] || "";
    if (was === d) return;
    d ? (a[field] = d) : delete a[field];
    tkLog(a, { ev: field, from: was, to: d });
    const M = inMeeting();
    M && mtLog({ taskKey: code, field: field, from: was, to: d }, M);
    refresh();
    toast(`${code || tdWords(x.title, 6)}: ${"followUp" === field ? "follow up" : "tracking until"} ${d ? tkDay(d) : "cleared"}`, [{ label: "Open", run: () => tkOpen(key) }]);
  };
  [
    ["data-tksfu", "followUp"],
    ["data-tkswatch", "watchUntil"],
  ].forEach(([attr, field]) => {
    m.querySelectorAll(`[${attr}]`).forEach((b) => (b.onclick = () => setDate(field, b.getAttribute(attr))));
    const p = q(`[${attr}pick]`);
    p && (p.onchange = () => p.value && setDate(field, p.value));
  });
  const w = q("[data-tkswait]");
  w && (w.onclick = () => (mbCloseModal(), tkWaitDialog(key)));
  const co = q("[data-tkscollab]");
  co && (co.onclick = () => (mbCloseModal(), tkCollabDialog(key)));
  const la = q("[data-tkslinkadd]");
  la && (la.onclick = () => (mbCloseModal(), tkLinkDialog(key)));
  m.querySelectorAll("[data-tkslink]").forEach(
    (b) =>
      (b.onclick = () => {
        const l = tkLinks(a)
          .map((y) => [y, tkLinkInfo(y, x.projectId)])
          .filter(([, i]) => i)[+b.dataset.tkslink];
        l && l[1].go && (mbCloseModal(), l[1].go());
      }),
  );
  const fi = q("[data-tksfile]");
  fi &&
    (fi.onchange = () => {
      const file = fi.files && fi.files[0];
      if (!file) return;
      const fr = new FileReader();
      fr.onload = () => {
        tkAddFile(R, file, String(fr.result || ""));
        refresh();
        toast(`${file.name} attached to ${code || tdWords(x.title, 6)}`, [{ label: "Open", run: () => tkOpen(key) }]);
      };
      fr.readAsDataURL(file);
    });
}
function tkOwnerDialog(key) {
  const R = tkResolve(key);
  if (!R || !R.rec) return;
  const a = R.rec;
  const m = mbModal(
    `Owner of ${esc(a.code || tdWords(R.x.title, 6))}`,
    `<p class="small muted">One person on the team owns it and sees it through. Someone outside the team is Waiting On.</p><div class="tks-people">${tkOwnersList()
      .map((u) => `<button type="button" class="tks-person ${u.name === a.assignee ? "on" : ""}" data-tkown="${esc(u.name)}"><b>${esc(u.name)}</b><small>${esc(TK_ROLE_SAY[u.role] || "")}</small></button>`)
      .join("")}</div>`,
    { submit: null },
  );
  m && m.classList.add("tks-on");
  m &&
    m.querySelectorAll("[data-tkown]").forEach(
      (b) =>
        (b.onclick = () => {
          const r = tkSetOwner(R, b.dataset.tkown);
          if (!r.ok) return toast(r.why);
          const M = mtCurrent();
          M && a.code && r.from !== r.to && mtLog({ taskKey: a.code, field: "owner", from: r.from, to: r.to }, M);
          save();
          mbCloseModal();
          try {
            render();
          } catch (e) {}
          toast(`${a.code || tdWords(R.x.title, 6)} is ${r.to}'s now`, [{ label: "Open", run: () => tkOpen(key) }]);
          setTimeout(() => tkSheet(key), 0);
        }),
    );
}
function tkWaitDialog(key) {
  const R = tkResolve(key);
  if (!R || !R.rec) return;
  const a = R.rec,
    W = a.waitingOn || {},
    td = today();
  const m = mbModal(
    `Waiting On · ${esc(a.code || tdWords(R.x.title, 6))}`,
    `<p class="small muted">Who owes what, by when they promised it, and how we know. ${esc(a.assignee || "The owner")} stays the owner and chases it.</p>
    <div class="grid2"><div class="f"><label>Who</label><input data-f="name" list="tk-wait-names" value="${esc(W.name || "")}" placeholder="Carlos, the architect, the client"><datalist id="tk-wait-names">${mmContactNames()
      .map((n) => `<option value="${esc(n)}">`)
      .join("")}</datalist></div><div class="f"><label>For What</label><input data-f="what" value="${esc(W.what || "")}" placeholder="dining boxes"></div></div>
    <div class="grid2"><div class="f"><label>Promised</label><input type="date" data-f="promised" value="${esc(W.promised || "")}"></div><div class="f"><label>Evidence</label><input data-f="evidence" value="${esc(W.evidence || "")}" placeholder="mail of ${esc(fmt(td))}, a call, the meeting"></div></div>`,
    {
      submit: "Save",
      alt: W.name ? { label: "Not Waiting", run: () => tkWaitSave(key, null) } : null,
      onSubmit: (f) => {
        if (!f.name) return toast("Say who it waits on"), !1;
        tkWaitSave(key, f);
      },
    },
  );
  m && m.classList.add("tks-on");
}
function tkWaitSave(key, f) {
  const R = tkResolve(key);
  if (!R || !R.rec) return;
  const a = R.rec,
    was = tkSetWaiting(a, f);
  tkLog(a, { ev: "waitingOn", from: was ? was.name : "", to: f ? f.name : "" });
  const M = mtCurrent();
  M && a.code && mtLog({ taskKey: a.code, field: "waitingOn", from: was ? was.name : "", to: f ? f.name : "", what: f ? f.what : "", promised: f ? f.promised : "", evidence: f ? f.evidence : "" }, M);
  save();
  try {
    render();
  } catch (e) {}
  toast(f ? `${a.code || ""} ${tkWaitSay(a.waitingOn, !0)}`.trim() : `${a.code || tdWords(R.x.title, 6)} no longer waits on anyone`, [{ label: "Open", run: () => tkOpen(key) }]);
  setTimeout(() => tkSheet(key), 0);
}
function tkCollabDialog(key) {
  const R = tkResolve(key);
  if (!R || !R.rec) return;
  const a = R.rec,
    pick = new Set(a.collaborators || []);
  const m = mbModal(
    `Collaborators · ${esc(a.code || tdWords(R.x.title, 6))}`,
    `<p class="small muted">People on the team who work on it with ${esc(a.assignee || "the owner")}. The owner stays the one in charge.</p><div class="tks-people">${tkOwnersList()
      .filter((u) => u.name !== a.assignee)
      .map((u) => `<button type="button" class="tks-person ${pick.has(u.name) ? "on" : ""}" data-tkcol="${esc(u.name)}" aria-pressed="${pick.has(u.name)}"><b>${esc(u.name)}</b><small>${esc(TK_ROLE_SAY[u.role] || "")}</small></button>`)
      .join("")}</div>`,
    {
      submit: "Save",
      onSubmit: () => {
        const was = (a.collaborators || []).join(", ");
        a.collaborators = [...pick];
        tkLog(a, { ev: "collaborators", from: was, to: a.collaborators.join(", ") });
        const M = mtCurrent();
        M && a.code && mtLog({ taskKey: a.code, field: "collaborators", from: was, to: a.collaborators.join(", ") }, M);
        save();
        try {
          render();
        } catch (e) {}
        toast(`${a.code || tdWords(R.x.title, 6)}: ${a.collaborators.length ? "with " + a.collaborators.join(", ") : "no collaborators"}`, [{ label: "Open", run: () => tkOpen(key) }]);
        setTimeout(() => tkSheet(key), 0);
      },
    },
  );
  if (!m) return;
  m.classList.add("tks-on");
  m.querySelectorAll("[data-tkcol]").forEach(
    (b) =>
      (b.onclick = () => {
        const n = b.dataset.tkcol;
        pick.has(n) ? pick.delete(n) : pick.add(n);
        b.classList.toggle("on", pick.has(n));
        b.setAttribute("aria-pressed", pick.has(n) ? "true" : "false");
      }),
  );
}
function tkLinkDialog(key) {
  const R = tkResolve(key);
  if (!R || !R.rec) return;
  const a = R.rec,
    C = tkLinkChoices(R.x.projectId || ""),
    draw = (qs) => {
      const w = String(qs || "").toLowerCase();
      return C.filter((c) => !w || `${c.label} ${c.sub}`.toLowerCase().includes(w))
        .slice(0, 30)
        .map((c) => `<button type="button" class="tks-src" data-tklk="${esc(c.kind)}|${esc(c.id)}"><span class="grow"><b>${esc(c.label)}</b><small class="muted"> · ${esc(c.sub)}</small></span><b>Link</b></button>`)
        .join("") || '<p class="small muted">Nothing matches.</p>';
    };
  const m = mbModal(`Link a Record · ${esc(a.code || tdWords(R.x.title, 6))}`, `<input class="tks-in" data-tklq placeholder="Search vendors, POs, bills, decisions, files, mail" aria-label="Search records"><div class="tks-offers" data-tklres style="margin-top:8px">${draw("")}</div>`, { submit: null });
  if (!m) return;
  m.classList.add("tks-on");
  const wire = () =>
    m.querySelectorAll("[data-tklk]").forEach(
      (b) =>
        (b.onclick = () => {
          const [kind, id] = b.dataset.tklk.split("|");
          const added = tkAddLink(a, { kind: kind, id: id });
          if (added) {
            tkLog(a, { ev: "link", kind: kind, id: id });
            const M = mtCurrent();
            M && a.code && mtLog({ taskKey: a.code, field: "link", from: "", to: `${kind}:${id}` }, M);
          }
          save();
          mbCloseModal();
          const i = tkLinkInfo({ kind: kind, id: id }, R.x.projectId);
          toast(added ? `${a.code || "Task"} linked to ${i ? i.label : kind}` : "Already linked", [{ label: "Open", run: () => tkOpen(key) }]);
          setTimeout(() => tkSheet(key), 0);
        }),
    );
  const qi = m.querySelector("[data-tklq]");
  qi &&
    (qi.oninput = () => {
      m.querySelector("[data-tklres]").innerHTML = draw(qi.value);
      wire();
    });
  wire();
}

/* ==== Meeting Mode ================================================================================================ */
function mtTeam() {
  return mtInit().filter((m) => m && "team" === m.kind);
}
function mtCurrent() {
  return mtTeam().find((m) => m.startedAt && !m.endedAt) || null;
}
function mtLastEnded(beforeId) {
  return (
    mtTeam()
      .filter((m) => m.endedAt && m.id !== beforeId)
      .sort((a, b) => String(b.endedAt).localeCompare(String(a.endedAt)))[0] || null
  );
}
function mtScreenLog(m) {
  const M = m || mtCurrent() || mtLastEnded();
  return (M && M.screenLog) || [];
}
// One change in the meeting: who, when, which task, the field, from and to. It also marks the task discussed.
function mtLog(change, m) {
  const M = m || mtCurrent();
  if (!M || !change) return null;
  const me = tdyMe(),
    at = appNowIso(),
    c = Object.assign({ id: uid("mc"), taskKey: "", field: "", from: "", to: "", by: me.name || "", at: at }, change),
    T = c.taskKey ? tkByCode(c.taskKey) : null;
  // the record's own address rides with the key: two devices that each made PAD-24 while apart are put right after
  // they merge (one moves to PAD-25), and the meeting's lines follow the task, not the number
  T && !c.ref && (c.ref = T.key);
  (M.changes = M.changes || []).push(c);
  if ("created" === c.field && c.taskKey) (M.created = M.created || []).includes(c.taskKey) || M.created.push(c.taskKey);
  T && (T.rec.lastDiscussed = { meetingId: M.id, at: at });
  return c;
}
// after a merge: each line's key read again from its task, and the new tasks read from the changes (an array of
// plain keys keeps only one device's additions when both add at once; the changes carry ids and keep both)
function mtRekey(m) {
  if (!m) return;
  const fix = (o) => {
    if (!o || !o.ref) return;
    const c = tkCodeOfKey(o.ref);
    c && c !== o.taskKey && (o.taskKey = c);
  };
  (m.changes || []).forEach(fix);
  (m.screenLog || []).forEach(fix);
  const made = (m.changes || []).filter((c) => "created" === c.field && c.taskKey).map((c) => c.taskKey);
  m.created = [...new Set(made)];
}
// the cadence: Monday and Thursday at 10 unless Settings says otherwise
function mtCadence() {
  DB.company = DB.company || {};
  const c = DB.company.meetCadence || {};
  return { days: Array.isArray(c.days) && c.days.length ? c.days : [1, 4], time: c.time || "10:00" };
}
function mtNextMeeting(from) {
  const C = mtCadence(),
    d0 = from || today();
  for (let i = 1; i <= 14; i++) {
    const d = iso(addDays(d0, i));
    if (C.days.includes(parse(d).getDay())) return d;
  }
  return iso(addDays(d0, 7));
}
// the team's project order, saved; boards it has not placed yet follow, jobs first
function mtOrder() {
  DB.company = DB.company || {};
  const B = tkBoards(),
    saved = (DB.company.meetOrder || []).filter((id) => B.includes(id));
  return saved.concat(B.filter((id) => !saved.includes(id)));
}
function mtOrderMove(id, d) {
  const L = mtOrder(),
    i = L.indexOf(id),
    j = i + d;
  if (i < 0 || j < 0 || j >= L.length) return !1;
  [L[i], L[j]] = [L[j], L[i]];
  DB.company.meetOrder = L;
  return !0;
}
// a board's open tasks in their order (rec.order, then as written)
function mtBoardOpen(id) {
  return tkKeyedRecs()
    .filter((r) => r.board === id && !tkRecDone(r.kind, r.rec))
    .map((r, i) => ({ r: r, i: i }))
    .sort((a, b) => (+a.r.rec.order || (a.i + 1) * 10) - (+b.r.rec.order || (b.i + 1) * 10))
    .map((y) => y.r);
}
// why a task is on the agenda: changed since the last meeting, late, due or to chase before the next, waiting
function mtWhy(r, since, next) {
  const a = r.rec,
    td = today(),
    W = [],
    due = "hub" === r.kind ? a.due : a.due || "";
  if (since) {
    const sd = since.slice(0, 10),
      ch = (a.thread || []).some((e) => e && String(e.at || "") > since) || String(a.createdAt || a.created || "") > sd || String(a.modifiedAt || "") > sd || (a.handoffs || []).some((h) => String(h.at || "") > since);
    ch && W.push("changed");
  }
  due && due < td && W.push("late");
  due && due >= td && due <= next && W.push("due");
  a.followUp && a.followUp <= next && W.push("follow");
  a.watchUntil && a.watchUntil <= next && W.push("watch");
  (a.waitingOn || a.waitsOn || "waiting" === a.status) && W.push("waiting");
  return W;
}
const MT_WHY_SAY = { changed: "changed since the last meeting", late: "late", due: "due before the next meeting", follow: "to chase before the next meeting", watch: "tracking date comes up", waiting: "waiting on someone", all: "on the board" };
// The agenda builds itself: projects in the team's order; in each, what changed, what is late, due or to chase before
// the next meeting, and what waits on someone outside; FYI items last, folded.
function mtBuildAgenda(whole, beforeId) {
  const last = mtLastEnded(beforeId),
    since = last ? last.endedAt || last.startedAt : "",
    next = mtNextMeeting(),
    out = [];
  mtOrder().forEach((id) => {
    const open = mtBoardOpen(id),
      items = [],
      fyi = [],
      why = {};
    open.forEach((r) => {
      const code = r.rec.code;
      if (!code) return;
      if ("fyi" === tkStatusOf(r.kind, r.rec)) return void fyi.push(code);
      const w = mtWhy(r, since, next);
      (w.length || whole) && (items.push(code), (why[code] = w.length ? w : ["all"]));
    });
    (items.length || fyi.length) && out.push({ board: id, name: tkBoardName(id), prefix: (tkBoardMeta(id) || {}).prefix || "", items: items, fyi: fyi, why: why });
  });
  return out;
}
// the walk, in order: each task, then the project's FYI items as one folded card (open, they join the walk)
function mtSeq(m) {
  const out = [],
    fy = [];
  (m.agenda || []).forEach((b) => {
    // a project added in the meeting has a card of its own until its first task is added
    !b.items.length && !b.fyi.length && out.push({ t: "empty", code: "EMPTY:" + b.board, board: b.board });
    b.items.forEach((c) => out.push({ t: "task", code: c, board: b.board }));
    b.fyi.forEach((c) => fy.push({ t: "task", code: c, board: b.board, fyi: !0 }));
  });
  // FYI only comes last, folded into one card; opened, its items join the walk
  fy.length && ((m.fyiOpen || []).includes("all") ? out.push(...fy) : out.push({ t: "fyi", code: "FYI:all", board: "__fyi" }));
  return out;
}
let mmOn = !1,
  mmAt = "",
  mmFollow = !0,
  mmPanel = "",
  mmDateField = "";
const mmMe = () => tdyMe();
const mmCanRun = () => ["owner", "coord"].includes(role());
const mmPresenter = (m) => !!m && (!m.presenterUid || m.presenterUid === mmMe().id);
function mmActive() {
  return mmOn && "tkall" === view && !!mtCurrent();
}
// where this screen is: following the presenter, or its own place
function mmWhere(m) {
  const S_ = mtSeq(m);
  if (mmFollow && m.cursor && m.cursor.code && S_.some((s) => s.code === m.cursor.code)) mmAt = m.cursor.code;
  S_.some((s) => s.code === mmAt) || (mmAt = (S_[0] || {}).code || "");
  return { seq: S_, i: Math.max(0, S_.findIndex((s) => s.code === mmAt)) };
}
// what was on screen, from when to when (the presenter's screen is the screen share)
function mmShow(m, code) {
  if (!m || !mmPresenter(m)) return;
  const now = appNowIso(),
    L = (m.screenLog = m.screenLog || []),
    open = L.length ? L[L.length - 1] : null;
  if (open && !open.to) {
    if (open.taskKey === code) return;
    open.to = now;
  }
  if (code && !/^(FYI|EMPTY):/.test(code)) {
    const T = tkByCode(code);
    L.push({ id: uid("ms"), taskKey: code, ref: T ? T.key : "", from: now, to: "" });
  }
  m.cursor = { code: code, at: now, by: mmMe().name || "" };
}
function mmGo(d) {
  const m = mtCurrent();
  if (!m) return;
  const W = mmWhere(m),
    j = W.i + d;
  if (j < 0 || j >= W.seq.length) return void toast(d > 0 ? "That was the last item on the agenda: End Meeting writes the minutes" : "This is the first item on the agenda");
  mmAt = W.seq[j].code;
  mmPanel = "";
  mmDateField = "";
  mmPresenter(m) ? mmShow(m, mmAt) : (mmFollow = !1);
  save();
  renderTkAll();
}
function mmJump(code) {
  const m = mtCurrent();
  if (!m) return;
  mmAt = code;
  mmPanel = "";
  mmPresenter(m) ? mmShow(m, code) : (mmFollow = !1);
  save();
  renderTkAll();
}
// ---- start and end ------------------------------------------------------------------------------------------------
function mmStartDialog() {
  const cur = mtCurrent();
  if (cur) return (mmOn = !0), (mmFollow = !0), renderTkAll();
  if (!mmCanRun()) return toast("The owner or the coordinator starts the team meeting");
  const me = mmMe(),
    U = tkOwnersList(),
    pick = new Set(U.filter((u) => /^(owner|pm|coord)$/.test(u.role) || u.id === me.id).map((u) => u.id)),
    days = mtCadence().days.map((d) => DOW[d]).join(" and ");
  const m = mbModal(
    "Start the Team Meeting",
    `<div class="mm-start"><div class="f"><label>Title</label><input data-f="title" value="Team Meeting"></div>
    <div class="tks-h">Who Is In It</div><div class="tks-people">${U.map((u) => `<button type="button" class="tks-person ${pick.has(u.id) ? "on" : ""}" data-mmatt="${esc(u.id)}" aria-pressed="${pick.has(u.id)}"><b>${esc(u.name)}</b><small>${esc(TK_ROLE_SAY[u.role] || "")}</small></button>`).join("")}</div>
    <label class="chk mm-whole"><input type="checkbox" data-f="whole"> Walk every open task, not only what needs discussing</label>
    <p class="small muted">The agenda builds itself: each project in the team's order, then what changed since the last meeting, what is late, what is due or to chase before the next meeting (${esc(days)}), and what waits on someone outside the team. FYI items come last, folded.</p></div>`,
    {
      submit: "Start Meeting",
      onSubmit: (f) => {
        const att = tkOwnersList()
          .filter((u) => pick.has(u.id))
          .map((u) => u.name);
        mtStart({ title: f.title || "Team Meeting", attendees: att, whole: !!f.whole });
        return !0;
      },
    },
  );
  m &&
    m.querySelectorAll("[data-mmatt]").forEach(
      (b) =>
        (b.onclick = () => {
          const id = b.dataset.mmatt;
          pick.has(id) ? pick.delete(id) : pick.add(id);
          b.classList.toggle("on", pick.has(id));
          b.setAttribute("aria-pressed", pick.has(id) ? "true" : "false");
        }),
    );
  m && m.classList.add("tks-on");
  return m;
}
function mtStart(o) {
  const O = o || {},
    me = mmMe();
  if (mtCurrent()) return mtCurrent();
  tkRecSweep();
  const now = appNowIso(),
    m = {
      id: uid("mt"),
      kind: "team",
      source: "meeting-mode",
      title: O.title || "Team Meeting",
      date: today(),
      startedAt: now,
      endedAt: "",
      attendees: O.attendees || [me.name],
      agenda: [],
      screenLog: [],
      changes: [],
      created: [],
      minutes: null,
      decisions: [],
      // what the meetings list reads on every meeting
      projectId: "",
      clientId: "",
      status: "live",
      createdAt: today(),
      proposals: [],
      steps: [],
      summary: "",
      presenter: me.name || "",
      presenterUid: me.id || "",
      cursor: null,
      whole: !!O.whole,
      fyiOpen: [],
      openAtStart: [],
    };
  mtInit().push(m);
  m.agenda = mtBuildAgenda(m.whole, m.id);
  m.openAtStart = m.agenda.flatMap((b) => b.items.concat(b.fyi));
  mmOn = !0;
  mmFollow = !0;
  mmPanel = "";
  const first = mtSeq(m)[0];
  mmAt = first ? first.code : "";
  mmShow(m, mmAt);
  try {
    audit("meeting", m.id, "started", "", now, m.title);
  } catch (e) {}
  save();
  try {
    view = "tkall";
    render();
  } catch (e) {}
  const n = m.agenda.reduce((a, b) => a + b.items.length, 0);
  toast(`${m.title} started: ${n} task${1 === n ? "" : "s"} on the agenda across ${m.agenda.length} project${1 === m.agenda.length ? "" : "s"}`, [{ label: "Open", run: () => ((mmOn = !0), (view = "tkall"), render()) }]);
  return m;
}
// The minutes: what moved, what's new, what's done, the decisions, and who owes what by when.
function mtMinutesOf(m) {
  const C = m.changes || [],
    title = (code) => {
      const T = tkByCode(code);
      return T ? T.rec.title || "" : "";
    },
    moved = [],
    done = [],
    notes = [],
    owners = [],
    waits = [];
  C.forEach((c) => {
    if (/^(due|followUp|watchUntil)$/.test(c.field)) moved.push({ code: c.taskKey, title: title(c.taskKey), field: c.field, from: c.from, to: c.to, by: c.by });
    if ("status" === c.field && "done" === c.to) done.push({ code: c.taskKey, title: title(c.taskKey), by: c.by });
    if ("comment" === c.field) notes.push({ code: c.taskKey, text: c.to, by: c.by });
    if ("owner" === c.field) owners.push({ code: c.taskKey, title: title(c.taskKey), from: c.from, to: c.to });
    if ("waitingOn" === c.field && c.to) waits.push({ code: c.taskKey, title: title(c.taskKey), to: c.to });
  });
  // the last word on a field wins: a date moved twice is one line
  const last = {};
  moved.forEach((x) => (last[x.code + ":" + x.field] = Object.assign({}, last[x.code + ":" + x.field] ? { from: last[x.code + ":" + x.field].from } : {}, x, last[x.code + ":" + x.field] ? { from: last[x.code + ":" + x.field].from } : {})));
  const created = (m.created || []).map((code) => {
    const T = tkByCode(code);
    return { code: code, title: T ? T.rec.title : "", owner: T ? T.rec.assignee || "" : "", due: T ? T.rec.due || "" : "" };
  });
  // who owes what by when: every open task the meeting touched or made, by owner, with its date
  const touched = new Set(C.map((c) => c.taskKey).filter(Boolean).concat(m.created || [])),
    owes = {};
  touched.forEach((code) => {
    const T = tkByCode(code);
    if (!T || tkRecDone(T.kind, T.rec)) return;
    const a = T.rec,
      who = a.assignee || "Nobody yet";
    (owes[who] = owes[who] || []).push({ code: code, title: a.title || "", by: a.followUp && (!a.due || a.followUp < a.due) ? a.followUp : a.due || "", due: a.due || "", followUp: a.followUp || "", waitingOn: a.waitingOn ? a.waitingOn.name : "" });
  });
  Object.values(owes).forEach((L) => L.sort((x, y) => String(x.by || "9999").localeCompare(String(y.by || "9999"))));
  const D = (m.decisions || []).map((d) => ({ text: d.text || d.name || "", status: d.status, code: d.taskKey || "" }));
  return {
    moved: Object.values(last),
    created: created,
    done: done,
    notes: notes,
    owners: owners,
    waiting: waits,
    decisions: { aligned: D.filter((d) => "aligned" === d.status), discuss: D.filter((d) => "aligned" !== d.status) },
    owes: owes,
    discussed: (m.screenLog || []).filter((s) => s.taskKey).length,
  };
}
function mtMinutesText(m, M) {
  const L = [],
    f = { due: "due", followUp: "follow-up", watchUntil: "tracking until" };
  L.push(`${m.title}, ${tkDay(m.date)}${m.attendees && m.attendees.length ? `. With ${m.attendees.join(", ")}` : ""}.`);
  M.moved.length && L.push("Moved:", ...M.moved.map((x) => `- ${x.code} ${x.title}: ${f[x.field] || x.field} ${x.from ? tkDay(x.from) + " to " : ""}${x.to ? tkDay(x.to) : "none"}`));
  M.created.length && L.push("New:", ...M.created.map((x) => `- ${x.code} ${x.title}, ${x.owner}${x.due ? ", due " + tkDay(x.due) : ""}`));
  M.done.length && L.push("Done:", ...M.done.map((x) => `- ${x.code} ${x.title}`));
  M.decisions.aligned.length && L.push("Decisions, aligned:", ...M.decisions.aligned.map((d) => `- ${d.text}${d.code ? ` (${d.code})` : ""}`));
  M.decisions.discuss.length && L.push("Decisions, to discuss:", ...M.decisions.discuss.map((d) => `- ${d.text}${d.code ? ` (${d.code})` : ""}`));
  const who = Object.keys(M.owes);
  who.length && L.push("Who owes what by when:", ...who.flatMap((w) => [`${w}:`].concat(M.owes[w].map((x) => `- ${x.code} ${x.title}${x.by ? ` by ${tkDay(x.by)}` : ", no date"}${x.waitingOn ? ` (waiting on ${x.waitingOn})` : ""}`))));
  return L.join("\n");
}
function mmEndDialog() {
  const m = mtCurrent();
  if (!m) return;
  tkRecSweep();
  mtRekey(m);
  mmReconcile(m);
  const M = mtMinutesOf(m),
    n = (k) => M[k].length;
  const body = `<p class="small muted">${M.discussed} task${1 === M.discussed ? "" : "s"} on screen · ${n("moved")} moved · ${n("created")} new · ${n("done")} done · ${M.decisions.aligned.length + M.decisions.discuss.length} decision${1 === M.decisions.aligned.length + M.decisions.discuss.length ? "" : "s"}. The minutes go on the meeting's record and to each person's Today.</p>${mtMinutesHtml(m, M)}`;
  const mm = mbModal("End the Meeting", body, { submit: "End and Send Minutes", onSubmit: () => (mtEnd(m), !0) });
  mm && mm.classList.add("tks-on");
  return mm;
}
// a task closed through the proof sheet, or from its own sheet during the meeting, is in the minutes too
function mmReconcile(m) {
  const logged = new Set((m.changes || []).filter((c) => "status" === c.field && "done" === c.to).map((c) => c.taskKey));
  (m.openAtStart || []).concat(m.created || []).forEach((code) => {
    if (logged.has(code)) return;
    const T = tkByCode(code);
    if (T && tkRecDone(T.kind, T.rec) && (T.rec.completedAt || today()) >= m.date) mtLog({ taskKey: code, field: "status", from: "open", to: "done", via: "closed during the meeting" }, m);
  });
}
function mtEnd(m) {
  const M0 = m || mtCurrent();
  if (!M0) return null;
  tkRecSweep();
  mtRekey(M0);
  mmReconcile(M0);
  const now = appNowIso(),
    L = M0.screenLog || [],
    open = L.length ? L[L.length - 1] : null;
  open && !open.to && (open.to = now);
  M0.endedAt = now;
  M0.status = "ended";
  M0.cursor = null;
  const M = mtMinutesOf(M0);
  M0.minutes = Object.assign(M, { text: mtMinutesText(M0, M), at: now, by: mmMe().name || "" });
  M0.summary = `${M.discussed} discussed, ${M.moved.length} moved, ${M.created.length} new, ${M.done.length} done, ${M.decisions.aligned.length + M.decisions.discuss.length} decisions.`;
  M0.seen = M0.seen || {};
  try {
    audit("meeting", M0.id, "ended", M0.startedAt, now, M0.summary);
  } catch (e) {}
  mmOn = !1;
  mmPanel = "";
  save();
  try {
    render();
  } catch (e) {}
  toast(`Minutes written: ${M0.summary}`, [{ label: "Open", run: () => mtMinutesSheet(M0.id) }]);
  return M0;
}
function mtMinutesHtml(m, M) {
  const row = (code, words) => `<li><button type="button" class="mm-mlink" data-mmopen="${esc(code)}">${esc(code)}</button> ${esc(words)}</li>`,
    sec = (h, items) => (items.length ? `<div class="tks-h">${esc(h)}</div><ul class="mm-min">${items.join("")}</ul>` : ""),
    fld = { due: "due", followUp: "follow-up", watchUntil: "tracking until" };
  return `<div class="mm-minutes">${sec(
    "Moved",
    M.moved.map((x) => row(x.code, `${x.title}: ${fld[x.field] || x.field} ${x.from ? tkDay(x.from) + " to " : ""}${x.to ? tkDay(x.to) : "none"}`)),
  )}${sec(
    "New",
    M.created.map((x) => row(x.code, `${x.title}, ${x.owner}${x.due ? ", due " + tkDay(x.due) : ""}`)),
  )}${sec(
    "Done",
    M.done.map((x) => row(x.code, x.title)),
  )}${sec("Decisions, Aligned", M.decisions.aligned.map((d) => `<li>${esc(d.text)}${d.code ? ` <span class="small muted">${esc(d.code)}</span>` : ""}</li>`))}${sec(
    "Decisions, to Discuss",
    M.decisions.discuss.map((d) => `<li>${esc(d.text)}${d.code ? ` <span class="small muted">${esc(d.code)}</span>` : ""}</li>`),
  )}${Object.keys(M.owes).length ? `<div class="tks-h">Who Owes What by When</div>${Object.keys(M.owes).map((w) => `<div class="mm-owes"><b>${esc(w)}</b><ul class="mm-min">${M.owes[w].map((x) => row(x.code, `${x.title}${x.by ? ` by ${tkDay(x.by)}` : ", no date yet"}${x.waitingOn ? ` · waiting on ${x.waitingOn}` : ""}`)).join("")}</ul></div>`).join("")}` : ""}${
    !M.moved.length && !M.created.length && !M.done.length && !Object.keys(M.owes).length && !M.decisions.aligned.length && !M.decisions.discuss.length ? '<p class="small muted">Nothing changed in this meeting.</p>' : ""
  }</div>`;
}
// the minutes, opened from Today, the toast or the meeting's record; opening them is reading them
function mtMinutesSheet(id) {
  const m = mtTeam().find((x) => x.id === id);
  if (!m) return toast("Those minutes are no longer here");
  const M = m.minutes || mtMinutesOf(m),
    me = mmMe(),
    mine = (me.name && M.owes[me.name]) || [];
  const mm = mbModal(
    `Minutes · ${esc(m.title)} · ${esc(tkDay(m.date))}`,
    `${mine.length ? `<div class="mm-mine"><b>You owe ${mine.length}:</b> ${mine.map((x) => `${esc(x.code)} ${esc(tdWords(x.title, 7))}${x.by ? ` by ${esc(tkDay(x.by))}` : ""}`).join("; ")}</div>` : ""}<p class="small muted">${esc(m.summary || "")}${m.attendees && m.attendees.length ? ` With ${esc(m.attendees.join(", "))}.` : ""}</p>${mtMinutesHtml(m, M)}`,
    { submit: null },
  );
  if (!mm) return null;
  mm.classList.add("tks-on");
  const c = mm.querySelector("#mbm-cancel");
  c && (c.textContent = "Close");
  mm.querySelectorAll("[data-mmopen]").forEach(
    (b) =>
      (b.onclick = () => {
        const T = tkByCode(b.dataset.mmopen);
        mbCloseModal();
        T && tkOpen(T.key);
      }),
  );
  if (me.id) {
    m.seen = m.seen || {};
    m.seen[me.id] || ((m.seen[me.id] = appNowIso()), save());
  }
  return mm;
}

// ---- one card at a time ---------------------------------------------------------------------------------------------
function mmCardData(code) {
  const T = tkByCode(code);
  if (!T) return null;
  const R = tkResolve(T.key);
  return R ? Object.assign({ T: T, R: R }, {}) : null;
}
function mmCardHtml(m, s, W) {
  if ("empty" === s.t) return `<article class="mm-card mm-fyi"><div class="mm-key">${esc((tkBoardMeta(s.board) || {}).prefix || "")}</div><h2 class="mm-title">${esc(tkBoardName(s.board))} has no tasks yet</h2><p class="muted">Add its first task: it will be ${esc((tkBoardMeta(s.board) || {}).prefix || "")}-${esc(String((tkBoardMeta(s.board) || {}).keyNext || 1))}.</p></article>`;
  if ("fyi" === s.t) {
    const F = (m.agenda || []).flatMap((b) => b.fyi.map((c) => [c, b]));
    return `<article class="mm-card mm-fyi"><div class="mm-key">FYI Only</div><h2 class="mm-title">${F.length} item${1 === F.length ? "" : "s"} for information</h2><ul class="mm-fyilist">${F.map(([c, b]) => {
      const T = tkByCode(c);
      return `<li><span class="mm-chip">${esc(c)}</span> ${esc(T ? T.rec.title : "")} <span class="small muted">· ${esc(b.name)}</span></li>`;
    }).join("")}</ul><button type="button" class="btn" data-mmfyiopen="all">Walk the FYI Items</button></article>`;
  }
  const D = mmCardData(s.code);
  if (!D) return `<article class="mm-card"><div class="mm-key">${esc(s.code)}</div><p class="muted">That task is no longer here.</p></article>`;
  const a = D.T.rec,
    x = D.R.x || {},
    st = tkStatusOf(D.T.kind, a),
    td = today(),
    C = tkComments(a).slice(-2),
    links = tkLinks(a)
      .map((l) => [l, tkLinkInfo(l, x.projectId)])
      .filter(([, i]) => i),
    files = tkAttachments(D.R),
    W0 = a.waitingOn && a.waitingOn.name ? a.waitingOn : null,
    late = a.due && a.due < td && "fyi" !== st,
    flag = a.ownerFlag ? `<div class="mm-flag">Owner set to ${esc(a.assignee)}: ${esc(a.ownerFlag.was || "nobody")} ${"outside" === a.ownerFlag.why ? "is not on the team" : "was named"}. Confirm or reassign.</div>` : "";
  return `<article class="mm-card" data-mmcard="${esc(s.code)}">
  <div class="mm-keyrow"><span class="mm-key">${esc(s.code)}</span><span class="mm-st mm-st-${esc(st)}">${esc(tkStatusSay(st))}</span></div>
  <h2 class="mm-title">${esc(a.title || x.title || "")}</h2>
  <div class="mm-meta"><div><span class="mm-ml">Owner</span><b class="mm-own">${a.assignee ? tvAv(a.assignee) : ""}${esc(a.assignee || "nobody")}</b>${(a.collaborators || []).length ? `<small> with ${esc(a.collaborators.join(", "))}</small>` : ""}</div><div><span class="mm-ml">Due</span><b class="${late ? "bad" : ""}">${a.due ? esc(tkDay(a.due)) + (late ? " · late" : "") : "No date"}</b></div><div><span class="mm-ml">Follow-up</span><b>${a.followUp ? esc(tkDay(a.followUp)) : "None"}</b></div>${a.watchUntil ? `<div><span class="mm-ml">Tracking Until</span><b>${esc(tkDay(a.watchUntil))}</b></div>` : ""}</div>
  ${flag}
  ${W0 ? `<div class="mm-wait">${mmSvg("wait", 20)}<div><b>Waiting on ${esc(W0.name)}${W0.what ? `: ${esc(W0.what)}` : ""}.</b>${W0.promised ? ` Promised ${esc(tkDay(W0.promised))}.` : " No date promised yet."}${W0.evidence ? `<div class="small">${esc(W0.evidence)}</div>` : ""}</div></div>` : ""}
  ${C.length ? `<div class="mm-comments" data-mmnotes>${tkPhone() ? `<div class="mm-notehd"><span class="mm-ml">Last Notes</span><button type="button" class="btn sm mm-notemore" data-mmnotesmore aria-expanded="false">More</button></div>` : '<span class="mm-ml">Last Notes</span>'}${C.map((c) => `<div class="mm-comment"><span class="small muted">${esc((tdyUserOf(c.by) ? tkFirst(c.by) : c.by) || "Someone")} · ${esc(fmt(String(c.at || "").slice(0, 10)))}</span><div>${esc(c.text)}</div></div>`).join("")}</div>` : '<div class="mm-comments muted small">No notes yet.</div>'}
  ${links.length || files.length ? `<div class="mm-links">${links.map(([l, i], k) => `<button type="button" class="mm-linkb" data-mmlink="${k}">${mmSvg("link", 16)}<span>${esc(i.label)}</span></button>`).join("")}${files.map((f) => `<span class="mm-linkb">${mmSvg("file", 16)}<span>${esc(f.name)}</span></span>`).join("")}</div>` : ""}
</article>`;
}
const MM_ACTS = [
  ["date", "New Date", "cal"],
  ["note", "Add a Note", "note"],
  ["done", "Done", "check"],
  ["owner", "Reassign", "person"],
  ["wait", "Waiting On", "wait"],
  ["track", "Track Until", "eye"],
  ["fyi", "FYI", "info"],
  ["skip", "Skip", "skip"],
];
function mmPanelHtml(m, code) {
  const D = mmCardData(code),
    a = D ? D.T.rec : {},
    td = today(),
    next = mtNextMeeting(),
    chips = (attr, extra) =>
      [
        ["Today", td],
        ["Tomorrow", iso(addDays(td, 1))],
        ["Next Meeting", next],
      ]
        .map(([n, d]) => `<button type="button" class="tks-chip" ${attr}="${d}"${extra || ""}>${n}<small>${esc(tkDay(d))}</small></button>`)
        .join("") + `<label class="tks-chip tks-pick">Pick<input type="date" ${attr}pick aria-label="Pick a day"></label>`;
  if ("date" === mmPanel) {
    const f = mmDateField || (a.waitingOn || "waiting" === a.status ? "followUp" : "due");
    return `<div class="mm-panel"><div class="seg sm mm-seg"><button type="button" class="${"due" === f ? "on" : ""}" data-mmfield="due">Due</button><button type="button" class="${"followUp" === f ? "on" : ""}" data-mmfield="followUp">Follow Up</button></div><div class="tks-chips">${chips("data-mmdate")}</div></div>`;
  }
  if ("note" === mmPanel) return `<div class="mm-panel"><div class="tks-row"><input class="tks-in" data-mmnotein placeholder="What was said" aria-label="Note"><button type="button" class="btn" data-mmnoteadd>Add Note</button></div></div>`;
  if ("owner" === mmPanel)
    return `<div class="mm-panel"><div class="tks-people">${tkOwnersList()
      .map((u) => `<button type="button" class="tks-person ${u.name === a.assignee ? "on" : ""}" data-mmowner="${esc(u.name)}"><b>${esc(u.name)}</b><small>${esc(TK_ROLE_SAY[u.role] || "")}</small></button>`)
      .join("")}</div></div>`;
  if ("wait" === mmPanel) {
    const W = a.waitingOn || {};
    return `<div class="mm-panel mm-waitp"><div class="grid2"><div class="f"><label>Waiting On</label><input data-mmw="name" list="mm-contacts" value="${esc(W.name || "")}" placeholder="Carlos, the architect, the client"><datalist id="mm-contacts">${mmContactNames()
      .map((n) => `<option value="${esc(n)}">`)
      .join("")}</datalist></div><div class="f"><label>For What</label><input data-mmw="what" value="${esc(W.what || "")}" placeholder="dining boxes"></div></div><div class="f"><label>Promised</label><div class="tks-chips">${chips("data-mmwprom")}</div></div><input type="hidden" data-mmw="promised" value="${esc(W.promised || "")}"><div class="tks-row"><input class="tks-in" data-mmw="evidence" value="${esc(W.evidence || `Said in the team meeting, ${tkDay(td)}`)}" aria-label="Evidence"><button type="button" class="btn" data-mmwsave>Save</button>${W.name ? '<button type="button" class="btn" data-mmwclear>Not Waiting</button>' : ""}</div></div>`;
  }
  if ("track" === mmPanel) return `<div class="mm-panel"><p class="small muted">Watch it, nothing to do yet: it comes back on the agenda on the day.</p><div class="tks-chips">${chips("data-mmtrack")}</div></div>`;
  if ("decision" === mmPanel)
    return `<div class="mm-panel"><div class="tks-row"><input class="tks-in" data-mmdecin placeholder="What was decided" aria-label="Decision"></div><div class="tks-row"><button type="button" class="btn" data-mmdec="aligned">Aligned</button><button type="button" class="btn" data-mmdec="to-discuss">To Discuss</button></div></div>`;
  if ("more" === mmPanel)
    return `<div class="mm-panel mm-menu"><button type="button" class="btn" data-mmmove="-1">Move Up</button><button type="button" class="btn" data-mmmove="1">Move Down</button><button type="button" class="btn" data-mmpanel="decision">Decision</button><button type="button" class="btn" data-mmsheet>Open the Task</button><button type="button" class="btn" data-mmprojmove="-1">Project Up</button><button type="button" class="btn" data-mmprojmove="1">Project Down</button>${tkPhone() ? '<button type="button" class="btn" data-mmleave>Leave the Meeting</button>' : ""}</div>`;
  if ("add" === mmPanel) {
    const s = mmWhere(m).seq.find((y) => y.code === mmAt),
      bid = s && "__fyi" !== s.board ? s.board : "";
    return bid
      ? `<div class="mm-panel"><div class="tks-row mm-addrow"><input class="tks-in" data-mmaddt placeholder="New task on ${esc(tkBoardName(bid))}" aria-label="New task on ${esc(tkBoardName(bid))}"><select class="mm-addo" data-mmaddo aria-label="Owner">${tkOwnersList()
          .map((u) => `<option ${u.id === mmMe().id ? "selected" : ""}>${esc(u.name)}</option>`)
          .join("")}</select><button type="button" class="btn" data-mmadd>Save Task</button></div></div>`
      : "";
  }
  if ("addproj" === mmPanel)
    return `<div class="mm-panel"><div class="grid2"><div class="f"><label>Project</label><input data-mmp="name" placeholder="Park Ave Duplex"></div><div class="f"><label>Prefix</label><input data-mmp="prefix" placeholder="PAD" maxlength="8"></div></div><div class="f"><label>Client</label><select data-mmp="client"><option value="">None: one of the firm's own lists</option>${(DB.clients || []).map((c) => `<option value="${esc(c.id)}">${esc(c.name)}</option>`).join("")}<option value="__new">New Client…</option></select></div><div class="f" data-mmpnewc hidden><label>New Client's Name</label><input data-mmp="newClient"></div><div class="tks-row"><button type="button" class="btn" data-mmpsave>Save Project</button></div></div>`;
  return "";
}
function mmContactNames() {
  const out = [];
  (DB.vendors || []).forEach((v) => out.push(v.name));
  (DB.clients || []).forEach((c) => out.push(c.name));
  ((DB.hub && DB.hub.contacts) || []).slice(0, 200).forEach((c) => out.push(`${c.first || ""} ${c.last || ""}`.trim() || c.name || ""));
  tdyUsers()
    .filter((u) => /^(foreman|crew|driver)$/.test(u.role))
    .forEach((u) => out.push(u.name));
  return [...new Set(out.filter(Boolean))].slice(0, 400);
}
// one line of the running log: "10:19 · LIN-16 · Waiting on the vendor, promised Thu 10/29. Owner Marco."
function mmLogLine(c) {
  const T = c.taskKey ? tkByCode(c.taskKey) : null,
    st = { done: "Done", fyi: "FYI: status only", doing: "Doing", todo: "Back to To Do", waiting: "Waiting On" },
    say = {
      due: () => `Due moved to ${c.to ? tkDay(c.to) : "no date"}`,
      followUp: () => `Follow-up ${c.to ? tkDay(c.to) : "cleared"}`,
      watchUntil: () => `Tracking until ${c.to ? tkDay(c.to) : "cleared"}`,
      comment: () => `Note: “${tdWords(c.to || "", 12)}”`,
      owner: () => `Reassigned to ${c.to}`,
      status: () => st[c.to] || `Status ${c.to}`,
      waitingOn: () => (c.to ? `Waiting on ${c.to}${c.what ? `: ${c.what}` : ""}${c.promised ? `, promised ${tkDay(c.promised)}` : ""}` : "No longer waiting on anyone"),
      decision: () => `Decision, ${"aligned" === c.status ? "aligned" : "to discuss"}: ${c.to}`,
      created: () => `New: ${tdWords(c.to || "", 10)}`,
      project: () => `New project ${c.to}`,
      projectOrder: () => `${c.to} moved ${c.move < 0 ? "up" : "down"} in the order`,
      order: () => `Moved ${+c.to > +c.from ? "down" : "up"} in its project`,
      collaborators: () => (c.to ? `With ${c.to}` : "No collaborators"),
      link: () => "Linked to a record",
    }[c.field];
  if (!say || ("owner" === c.field && !c.from)) return "";
  const owner = T && !/^(owner|project|projectOrder)$/.test(c.field) ? ` Owner ${T.rec.assignee || "nobody"}.` : "";
  return `<li><span class="mm-lt">${esc(String(c.at || "").slice(11, 16))}</span>${c.taskKey ? ` · <button type="button" class="mm-mlink" data-mmjump="${esc(c.taskKey)}">${esc(c.taskKey)}</button>` : ""} · ${esc(say())}.${esc(owner)}</li>`;
}
function mmHtml() {
  const m = mtCurrent();
  if (!m) return "";
  const W = mmWhere(m),
    s = W.seq[W.i] || null,
    phone = tkPhone(),
    pres = mmPresenter(m),
    td = today(),
    byCode = new Map(tkKeyedRecs().map((r) => [r.rec.code, r])),
    b = s ? (m.agenda || []).find((x) => x.board === s.board) : null,
    inB = b ? W.seq.filter((y) => y.board === b.board && "task" === y.t) : [],
    posB = s ? inB.findIndex((y) => y.code === s.code) + 1 : 0,
    tasks = W.seq.filter((y) => "task" === y.t),
    talked = new Set((m.screenLog || []).map((l) => l.taskKey).concat((m.changes || []).map((c) => c.taskKey))),
    nDisc = tasks.filter((y) => talked.has(y.code)).length,
    mins = Math.max(0, Math.round((appNowMs() - new Date(m.startedAt).getTime()) / 6e4)),
    last = mtLastEnded(m.id),
    changed = !!(b && s && ((b.why || {})[s.code] || []).includes("changed")),
    addedHere = new Set((m.changes || []).filter((c) => "project" === c.field).map((c) => c.board)),
    fyiN = (m.agenda || []).reduce((n, x) => n + x.fyi.length, 0);
  // the agenda: one row per project in the team's order, with its count and what is in it
  const agRows = (m.agenda || [])
    .filter((bb) => bb.items.length || !bb.fyi.length)
    .map((bb) => {
      const R = bb.items.map((c) => byCode.get(c)).filter(Boolean),
        late = R.filter((r) => r.rec.due && r.rec.due < td && !tkRecDone(r.kind, r.rec) && "fyi" !== tkStatusOf(r.kind, r.rec)).length,
        wait = R.filter((r) => r.rec.waitingOn && r.rec.waitingOn.name && !tkRecDone(r.kind, r.rec)).length,
        done = R.filter((r) => tkRecDone(r.kind, r.rec)).length,
        sum = addedHere.has(bb.board) ? "Added in this meeting" : [late ? `${late} late` : "", wait ? `${wait} waiting` : "", done ? `${done} done` : ""].filter(Boolean).join(" · ") || `${bb.items.length} to discuss`;
      return `<div role="button" tabindex="0" class="mm-ag ${s && s.board === bb.board ? "on" : ""}" data-mmboard="${esc(bb.board)}"><span class="mm-agn">${esc(bb.name)} <small>${esc(bb.prefix)}</small></span><span class="mm-agc">${bb.items.length}</span><span class="mm-ags">${esc(sum)}</span></div>`;
    })
    .join("");
  const agenda = `<div class="mm-rh">Agenda</div>${agRows}${fyiN ? `<div role="button" tabindex="0" class="mm-ag mm-agfyi ${s && "__fyi" === s.board ? "on" : ""}" data-mmjump="FYI:all"><span class="mm-agn">FYI Only</span><span class="mm-agc">${fyiN}</span><span class="mm-ags">folded, status only</span></div>` : ""}<button type="button" class="mm-agadd" data-mmact="addproj">${mmSvg("plus", 16)} New Project</button>`;
  const logL = (m.changes || [])
      .slice()
      .reverse()
      .map(mmLogLine)
      .filter(Boolean),
    log = `<div class="mm-rh">Changed in This Meeting</div>${logL.length ? `<ul class="mm-log">${logL.join("")}</ul>` : '<p class="small muted">Nothing changed yet.</p>'}<p class="mm-lognote">After the meeting the transcript is matched to this log by the time each task was on screen. Anything said that is not here arrives as one Meeting Review to approve.</p>`;
  const isTask = !!(s && "task" === s.t),
    acts = isTask ? `<div class="mm-acts" role="toolbar" aria-label="Actions on this task">${MM_ACTS.map(([k, n, ic]) => `<button type="button" class="mm-act ${"date" === k ? "primary" : ""} ${mmPanel === k ? "on" : ""}" data-mmact="${k}">${mmSvg(ic, 20)}<span>${n}</span></button>`).join("")}</div>` : "",
    panel = "addproj" === mmPanel ? mmPanelHtml(m, "") : "add" === mmPanel || ("empty" === (s || {}).t && !mmPanel) ? ((mmPanel = "add"), mmPanelHtml(m, "")) : isTask ? mmPanelHtml(m, s.code) : "",
    addBtn = b ? `<button type="button" class="mm-addbtn ${"add" === mmPanel ? "on" : ""}" data-mmact="add">${mmSvg("plus", 18)}<span>Add a Task to ${esc(b.name)}</span></button>` : "",
    ctx = s ? `<div class="mm-ctx"><span><b>${esc(b ? b.name : "FYI Only")}</b>${b && isTask ? ` · Task ${posB} of ${inB.length}` : ""}</span>${changed ? `<span class="mm-changed">Changed since ${esc(last ? tkDay(last.date) : "the last meeting")}</span>` : ""}<span class="grow"></span>${isTask ? `<button type="button" class="btn sm mm-more ${"more" === mmPanel ? "on" : ""}" data-mmact="more">More</button>` : ""}</div>` : "",
    card = s ? mmCardHtml(m, s, W) : '<article class="mm-card"><h2 class="mm-title">Nothing on the agenda</h2><p class="muted">Every open task is quiet: nothing late, nothing due before the next meeting, nothing waiting.</p></article>',
    nav = `<div class="mm-nav"><button type="button" class="btn mm-prev" data-mmprev ${W.i <= 0 ? "disabled" : ""}>${mmSvg("prev", 20)}<span>Previous</span></button>${phone ? "" : `${addBtn}<span class="mm-hint">Arrow keys move between tasks</span>`}<button type="button" class="btn mm-next" data-mmnext ${W.i >= W.seq.length - 1 ? "disabled" : ""}><span>Next Task</span>${mmSvg("next", 20)}</button></div>`;
  // the phone: the pill, the meeting and its progress on one line; Follow, Agenda and End Meeting behind one menu, so the
  // card and its eight actions are on the first screen
  const pct = tasks.length ? Math.round((100 * nDisc) / tasks.length) : 0,
    // the page keeps its own heading (Tasks, which the phone's top bar carries), so the page-header pass never takes
    // the card's title for the page's and lifts it out of the card
    phTop = `<div class="ph mm-ph"><div><h2>Tasks</h2></div></div><div class="mm-top mm-top-ph"><span class="mm-live" data-mmlive>In Meeting · ${mins} min</span><b class="mm-phttl" title="${esc(m.title)} · ${esc(fmtL(m.date))}">${esc(m.title)}</b><span class="mm-prog mm-prog-ph" aria-label="${nDisc} of ${tasks.length} discussed"><span>${nDisc} of ${tasks.length} <span class="mm-sr">discussed</span></span><span class="mm-pbar"><i style="width:${pct}%"></i></span></span>
  <details class="mm-phmenu"><summary class="btn mm-phmenub" aria-label="Meeting menu: Follow, Agenda, End Meeting" title="Follow, Agenda, End Meeting">${mmSvg("more", 20)}</summary><div class="mm-phmenu-in"><label class="mm-follow"><input type="checkbox" data-mmfollow ${mmFollow ? "checked" : ""}> Follow the presenter</label><button type="button" class="btn" data-mmagenda>Agenda</button>${pres ? '<button type="button" class="btn" data-mmend>End Meeting</button>' : ""}${pres ? "" : `<span class="small muted">${esc(tkFirst(m.presenter) || "someone")} is sharing</span>`}</div></details></div>`;
  return `<div class="mm ${phone ? "mm-phone" : ""}" data-mm="${esc(m.id)}">
  ${phone ? phTop : `<div class="mm-top"><span class="mm-live" data-mmlive>In Meeting · ${mins} min</span><div class="mm-ttl"><b>${esc(m.title)} · ${esc(fmtL(m.date))}</b><span class="small muted">${esc((m.attendees || []).join(", "))}${pres ? "" : ` · ${esc(tkFirst(m.presenter) || "someone")} is sharing`}</span></div><span class="grow"></span>
  <div class="mm-prog"><span>${nDisc} of ${tasks.length} discussed</span><span class="mm-pbar"><i style="width:${tasks.length ? Math.round((100 * nDisc) / tasks.length) : 0}%"></i></span></div>
  <label class="mm-follow"><input type="checkbox" data-mmfollow ${mmFollow ? "checked" : ""}> Follow</label><button type="button" class="btn" data-mmleave>Leave</button>${pres ? '<button type="button" class="btn" data-mmend>End Meeting</button>' : ""}</div>`}
  <div class="mm-body">${phone ? "" : `<aside class="mm-side" aria-label="Agenda" data-noclip="1">${agenda}</aside>`}<section class="mm-main">
    ${ctx}${card}${acts}${panel}${phone ? `<div class="mm-phadd">${addBtn}<button type="button" class="btn mm-addp" data-mmact="addproj">${mmSvg("plus", 16)} New Project</button></div>` : ""}${nav}
    ${phone ? `<details class="mm-phlog"><summary>Changed in This Meeting · ${logL.length}</summary>${log}</details>` : ""}
  </section>${phone ? "" : `<aside class="mm-right" aria-label="Changed in this meeting" data-noclip="1">${log}</aside>`}</div></div>`;
}
// the clock on the In Meeting pill moves without a redraw
setInterval(() => {
  try {
    const el = document.querySelector("[data-mmlive]"),
      m = el && mtCurrent();
    m && (el.textContent = `In Meeting · ${Math.max(0, Math.round((appNowMs() - new Date(m.startedAt).getTime()) / 6e4))} min`);
  } catch (e) {}
}, 3e4);
// ---- the actions ------------------------------------------------------------------------------------------------------
function mmAfter(msg, code, advance) {
  save();
  advance ? mmGo(1) : renderTkAll();
  const T = code && tkByCode(code);
  msg && toast(msg, T ? [{ label: "Open", run: () => tkOpen(T.key) }] : null);
}
function mmSetDate(code, field, d) {
  const T = tkByCode(code),
    m = mtCurrent();
  if (!T || !m) return;
  const a = T.rec,
    was = a[field] || "";
  if (was === d) return void toast(`Already ${tkDay(d)}`);
  if ("due" === field) {
    const R = tkResolve(T.key);
    R && tkSetDue(R, d);
  } else a[field] = d;
  "firm" === T.kind && (a.modifiedAt = today());
  mtLog({ taskKey: code, field: field, from: was, to: d }, m);
  mmPanel = "";
  mmAfter(`${code}: ${{ due: "due", followUp: "follow up", watchUntil: "tracking until" }[field]} ${tkDay(d)}`, code);
}
function mmAct(k, code) {
  const m = mtCurrent(),
    T = code ? tkByCode(code) : null;
  if (!m) return;
  if (["date", "note", "owner", "wait", "track", "more", "decision", "addproj", "add"].includes(k)) {
    mmPanel = mmPanel === k ? "" : k;
    return void renderTkAll();
  }
  if (!T) return;
  const a = T.rec;
  if ("skip" === k) {
    mtLog({ taskKey: code, field: "skip" }, m);
    return void mmAfter("", code, !0);
  }
  if ("fyi" === k) {
    const was = tkStatusOf(T.kind, a);
    if ("fyi" === was) return void toast(`${code} is already FYI`);
    tkSetStatus(T.kind, a, "fyi");
    mtLog({ taskKey: code, field: "status", from: was, to: "fyi" }, m);
    return void mmAfter(`${code} is FYI now: status only, never late`, code, !0);
  }
  if ("done" === k) {
    const was = tkStatusOf(T.kind, a);
    if ("done" === was) return void mmAfter("", code, !0);
    tkToggle(T.kind, a.id, T.p ? T.p.id : "");
    const now = tkByCode(code);
    if (!now || !tkRecDone(now.kind, now.rec)) return; // the proof sheet asks first; the minutes pick it up when it closes
    mtLog({ taskKey: code, field: "status", from: was, to: "done" }, m);
    return void mmAfter(`Done: ${code} ${tdWords(a.title || "", 6)}`, code, !0);
  }
}
function mmAddTask(m, title, owner) {
  const s = mmWhere(m).seq.find((y) => y.code === mmAt),
    bid = s ? s.board : (m.agenda[0] || {}).board;
  if (!bid) return toast("Add a project first");
  if (!String(title || "").trim()) return toast("Say what the task is");
  if (!tkInternal(owner)) return toast("Pick an owner on the team");
  const me = mmMe(),
    src = { meetingId: m.id, kind: "meeting", label: m.title };
  let made = null;
  if (/^p:/.test(bid)) made = crCreateTask({ title: title.trim(), for: "p:" + bid.slice(2), assignee: owner, source: src, handoff: !1 });
  else if ("sales" === bid) made = crCreateTask({ title: title.trim(), for: "sales", assignee: owner, source: src, handoff: !1 });
  else {
    made = crCreateTask({ title: title.trim(), for: "firm", assignee: owner, source: src, handoff: !1, section: bid.slice(2) });
  }
  if (!made || !made.rec) return toast("The task was not made");
  made.rec.createdBy = made.rec.createdBy || me.name || "";
  tkRecSweep();
  const code = made.rec.code;
  // it joins the agenda right after the task on screen, and the walk goes on from there
  const b = m.agenda.find((x) => x.board === bid);
  if (b) {
    const i = b.items.indexOf(mmAt);
    i >= 0 ? b.items.splice(i + 1, 0, code) : b.items.push(code);
    b.why = b.why || {};
    b.why[code] = ["changed"];
  }
  // the first task of a project added in the meeting takes its empty card's place on screen
  /^EMPTY:/.test(mmAt) && ((mmAt = code), mmPresenter(m) && mmShow(m, code));
  mtLog({ taskKey: code, field: "created", from: "", to: title.trim() }, m);
  mtLog({ taskKey: code, field: "owner", from: "", to: made.rec.assignee }, m);
  mmPanel = "";
  save();
  renderTkAll();
  toast(`${code} added for ${made.rec.assignee}: ${tdWords(title, 8)}`, [{ label: "Open", run: () => tkOpen(tkByCode(code).key) }]);
  return code;
}
function mmAddProject(m, f) {
  const name = String(f.name || "").trim();
  if (!name) return toast("Name the project"), null;
  let id = "";
  if (f.client) {
    const p = blankProject(name, "", today(), "");
    if ("__new" === f.client) {
      const nm = String(f.newClient || "").trim();
      if (!nm) return toast("Name the new client"), null;
      const c = blankClient(nm);
      DB.clients.push(c);
      p.clientId = c.id;
    } else p.clientId = f.client;
    DB.projects.push(p);
    id = "p:" + p.id;
  } else {
    id = "s:" + name;
    if (tkBoards().includes(id)) return toast(`${name} is already a list`), null;
    tkBoardMap()[id] = { name: name, created: today(), by: mmMe().name || "" };
  }
  const want = String(f.prefix || "").trim() || tkPrefixGuess(name, id),
    r = tkSetPrefix(id, want);
  r.ok || ((tkBoardMeta(id).prefix = tkPrefixGuess(name, id)), toast(r.why));
  tkBoardMeta(id).keyNext = tkBoardMeta(id).keyNext || 1;
  // after the project on screen, in the team's order and on today's agenda
  const s = mmWhere(m).seq.find((y) => y.code === mmAt),
    L = mtOrder().filter((x) => x !== id),
    at = s ? L.indexOf(s.board) + 1 : L.length;
  L.splice(at, 0, id);
  DB.company.meetOrder = L;
  const ai = s ? m.agenda.findIndex((x) => x.board === s.board) + 1 : m.agenda.length;
  m.agenda.splice(ai, 0, { board: id, name: tkBoardName(id), prefix: tkBoardMeta(id).prefix, items: [], fyi: [], why: {} });
  mtLog({ taskKey: "", field: "project", from: "", to: `${tkBoardName(id)} (${tkBoardMeta(id).prefix})`, board: id }, m);
  mmAt = "EMPTY:" + id;
  mmPresenter(m) && mmShow(m, mmAt);
  mmPanel = "add";
  try {
    audit("board", id, "created", "", name, "in the team meeting");
  } catch (e) {}
  save();
  renderTkAll();
  toast(`${name} added with the prefix ${tkBoardMeta(id).prefix}: its first task will be ${tkBoardMeta(id).prefix}-${tkBoardMeta(id).keyNext}`);
  return id;
}
// the order within a project: moved only from the menu, never by a stray drag
function mmMove(m, code, d) {
  const T = tkByCode(code);
  if (!T) return;
  const L = mtBoardOpen(T.board);
  L.forEach((r, i) => (r.rec.order = (i + 1) * 10));
  const i = L.findIndex((r) => r.rec.code === code),
    j = i + d;
  if (i < 0 || j < 0 || j >= L.length) return void toast(d < 0 ? "Already first in its project" : "Already last in its project");
  const o = L[i].rec.order;
  L[i].rec.order = L[j].rec.order;
  L[j].rec.order = o;
  const b = m.agenda.find((x) => x.board === T.board);
  if (b) {
    const ord = (c) => {
      const t = tkByCode(c);
      return t ? +t.rec.order || 0 : 0;
    };
    b.items.sort((x, y) => ord(x) - ord(y));
  }
  mtLog({ taskKey: code, field: "order", from: o, to: L[i].rec.order }, m);
  mmPanel = "";
  mmAfter(`${code} moved ${d < 0 ? "up" : "down"} in ${tkBoardName(T.board)}`, code);
}
function mmAgendaSheet(m) {
  const S_ = mtSeq(m);
  const mm = mbModal(
    "Agenda",
    `<div class="mm-agsheet">${(m.agenda || [])
      .map(
        (b) =>
          `<div class="tks-h">${esc(b.name)} <span class="muted">${esc(b.prefix)}</span></div>${S_.filter((y) => y.board === b.board)
            .map((y) => {
              const T = "task" === y.t ? tkByCode(y.code) : null;
              return `<button type="button" class="tks-src ${y.code === mmAt ? "on" : ""}" data-mmjump="${esc(y.code)}"><span class="grow">${"fyi" === y.t ? `FYI · ${b.fyi.length} items` : `<b>${esc(y.code)}</b> ${esc(T ? tdWords(T.rec.title || "", 8) : "")}`}</span></button>`;
            })
            .join("")}`,
      )
      .join("")}</div>`,
    { submit: null },
  );
  if (!mm) return;
  mm.classList.add("tks-on");
  mm.querySelectorAll("[data-mmjump]").forEach((x) => (x.onclick = () => (mbCloseModal(), mmJump(x.dataset.mmjump))));
}
function mmWire(host) {
  const m = mtCurrent();
  if (!m || !host) return;
  const q = (s) => host.querySelector(s),
    code = mmAt;
  host.querySelectorAll("[data-mmact]").forEach((b) => (b.onclick = () => mmAct(b.dataset.mmact, code)));
  host.querySelectorAll("[data-mmjump]").forEach((b) => (b.onclick = () => mmJump(b.dataset.mmjump)));
  host.querySelectorAll("[data-mmboard]").forEach(
    (b) =>
      (b.onclick = () => {
        const f = mtSeq(m).find((y) => y.board === b.dataset.mmboard);
        f && mmJump(f.code);
      }),
  );
  host.querySelectorAll(".mm-ag[role=button]").forEach((b) => (b.onkeydown = (e) => ("Enter" === e.key || " " === e.key) && (e.preventDefault(), b.click())));
  // the phone's card keeps the notes short: the latest, two lines; More shows them whole
  host.querySelectorAll("[data-mmnotesmore]").forEach(
    (b) =>
      (b.onclick = () => {
        const box = b.closest("[data-mmnotes]"),
          on = !box.classList.contains("open");
        box.classList.toggle("open", on);
        b.setAttribute("aria-expanded", on ? "true" : "false");
        b.textContent = on ? "Less" : "More";
      }),
  );
  const nx = q("[data-mmnext]"),
    pv = q("[data-mmprev]");
  nx && (nx.onclick = () => mmGo(1));
  pv && (pv.onclick = () => mmGo(-1));
  const fo = q("[data-mmfollow]");
  fo &&
    (fo.onchange = () => {
      mmFollow = fo.checked;
      renderTkAll();
    });
  const lv = q("[data-mmleave]");
  // Leave can sit in More on the phone
  lv && (lv.onclick = () => ((mmOn = !1), renderTkAll(), toast(`${m.title} goes on without this screen: Rejoin from Tasks`)));
  const en = q("[data-mmend]");
  en && (en.onclick = () => mmEndDialog());
  const ag = q("[data-mmagenda]");
  ag && (ag.onclick = () => mmAgendaSheet(m));
  host.querySelectorAll("[data-mmfield]").forEach((b) => (b.onclick = () => ((mmDateField = b.dataset.mmfield), renderTkAll())));
  const field = () => mmDateField || (((tkByCode(code) || {}).rec || {}).waitingOn ? "followUp" : "due");
  host.querySelectorAll("[data-mmdate]").forEach((b) => (b.onclick = () => mmSetDate(code, field(), b.dataset.mmdate)));
  const dp = q("[data-mmdatepick]");
  dp && (dp.onchange = () => dp.value && mmSetDate(code, field(), dp.value));
  host.querySelectorAll("[data-mmtrack]").forEach((b) => (b.onclick = () => mmSetDate(code, "watchUntil", b.dataset.mmtrack)));
  const tp = q("[data-mmtrackpick]");
  tp && (tp.onchange = () => tp.value && mmSetDate(code, "watchUntil", tp.value));
  const ni = q("[data-mmnotein]"),
    na = q("[data-mmnoteadd]"),
    addNote = () => {
      const v = ((ni && ni.value) || "").trim();
      if (!v) return toast("Write the note first");
      const T = tkByCode(code);
      if (!T) return;
      tkLog(T.rec, { text: v, meetingId: m.id });
      mtLog({ taskKey: code, field: "comment", from: "", to: v }, m);
      mmPanel = "";
      mmAfter(`Note added to ${code}`, code);
    };
  na && (na.onclick = addNote);
  ni && (ni.addEventListener("keydown", (e) => "Enter" === e.key && (e.preventDefault(), addNote())), setTimeout(() => ni.focus(), 20));
  host.querySelectorAll("[data-mmowner]").forEach(
    (b) =>
      (b.onclick = () => {
        const T = tkByCode(code);
        if (!T) return;
        const r = tkSetOwner(T, b.dataset.mmowner);
        if (!r.ok) return toast(r.why);
        r.from !== r.to && mtLog({ taskKey: code, field: "owner", from: r.from, to: r.to }, m);
        mmPanel = "";
        mmAfter(`${code} is ${r.to}'s now`, code);
      }),
  );
  // Waiting On: who owes what, by when they promised it, and the evidence
  const wv = (k) => ((q(`[data-mmw="${k}"]`) || {}).value || "").trim();
  host.querySelectorAll("[data-mmwprom]").forEach(
    (b) =>
      (b.onclick = () => {
        const h = q('[data-mmw="promised"]');
        h && (h.value = b.dataset.mmwprom);
        host.querySelectorAll("[data-mmwprom]").forEach((x) => x.classList.toggle("on", x === b));
      }),
  );
  const wpp = q("[data-mmwprompick]");
  wpp &&
    (wpp.onchange = () => {
      const h = q('[data-mmw="promised"]');
      h && (h.value = wpp.value);
    });
  const ws = q("[data-mmwsave]");
  ws &&
    (ws.onclick = () => {
      const T = tkByCode(code);
      if (!T) return;
      const name = wv("name");
      if (!name) return toast("Say who it waits on");
      const W = { name: name, what: wv("what"), promised: wv("promised"), evidence: wv("evidence") },
        was = tkSetWaiting(T.rec, W);
      mtLog({ taskKey: code, field: "waitingOn", from: was ? was.name : "", to: name, what: W.what, promised: W.promised, evidence: W.evidence }, m);
      mmPanel = "";
      mmAfter(`${code}: ${tkWaitSay(T.rec.waitingOn, !0)}`, code);
    });
  const wc = q("[data-mmwclear]");
  wc &&
    (wc.onclick = () => {
      const T = tkByCode(code);
      if (!T) return;
      const was = tkSetWaiting(T.rec, null);
      mtLog({ taskKey: code, field: "waitingOn", from: was ? was.name : "", to: "" }, m);
      mmPanel = "";
      mmAfter(`${code} no longer waits on anyone`, code);
    });
  // a decision, aligned or to discuss, on the meeting's record
  host.querySelectorAll("[data-mmdec]").forEach(
    (b) =>
      (b.onclick = () => {
        const v = ((q("[data-mmdecin]") || {}).value || "").trim();
        if (!v) return toast("Say what was decided");
        (m.decisions = m.decisions || []).push({ id: uid("md"), name: v, text: v, status: b.dataset.mmdec, taskKey: code, by: mmMe().name || "", at: appNowIso() });
        mtLog({ taskKey: code, field: "decision", from: "", to: v, status: b.dataset.mmdec }, m);
        mmPanel = "";
        mmAfter(`Decision recorded, ${"aligned" === b.dataset.mmdec ? "aligned" : "to discuss"}`, code);
      }),
  );
  host.querySelectorAll("[data-mmpanel]").forEach((b) => (b.onclick = () => ((mmPanel = b.dataset.mmpanel), renderTkAll())));
  host.querySelectorAll("[data-mmmove]").forEach((b) => (b.onclick = () => mmMove(m, code, +b.dataset.mmmove)));
  host.querySelectorAll("[data-mmprojmove]").forEach(
    (b) =>
      (b.onclick = () => {
        const s = mmWhere(m).seq.find((y) => y.code === code);
        if (!s) return;
        const d = +b.dataset.mmprojmove;
        if (!mtOrderMove(s.board, d)) return toast(d < 0 ? "Already the first project" : "Already the last project");
        const i = m.agenda.findIndex((x) => x.board === s.board),
          j = i + d;
        j >= 0 && j < m.agenda.length && ([m.agenda[i], m.agenda[j]] = [m.agenda[j], m.agenda[i]]);
        mtLog({ taskKey: "", field: "projectOrder", from: "", to: tkBoardName(s.board), board: s.board, move: d }, m);
        mmPanel = "";
        mmAfter(`${tkBoardName(s.board)} moved ${d < 0 ? "up" : "down"} in the team's order`, "");
      }),
  );
  const sh = q("[data-mmsheet]");
  sh &&
    (sh.onclick = () => {
      const T = tkByCode(code);
      mmPanel = "";
      T && tkSheet(T.key);
    });
  host.querySelectorAll("[data-mmlink]").forEach(
    (b) =>
      (b.onclick = () => {
        const T = tkByCode(code),
          R = T && tkResolve(T.key),
          L = T ? tkLinks(T.rec) : [],
          l = L[+b.dataset.mmlink],
          i = l && tkLinkInfo(l, R && R.x ? R.x.projectId : "");
        i && i.go && ((mmOn = !1), i.go());
      }),
  );
  host.querySelectorAll("[data-mmfyiopen]").forEach(
    (b) =>
      (b.onclick = () => {
        (m.fyiOpen = m.fyiOpen || []).includes("all") || m.fyiOpen.push("all");
        const first = (m.agenda || []).flatMap((x) => x.fyi)[0];
        mmAt = first || mmAt;
        mmPresenter(m) && mmShow(m, mmAt);
        save();
        renderTkAll();
      }),
  );
  // add a task under the project on screen
  const at = q("[data-mmaddt]"),
    ab = q("[data-mmadd]"),
    addT = () => {
      const c = mmAddTask(m, (at && at.value) || "", ((q("[data-mmaddo]") || {}).value || "").trim());
      c && at && (at.value = "");
    };
  ab && (ab.onclick = addT);
  at && at.addEventListener("keydown", (e) => "Enter" === e.key && (e.preventDefault(), addT()));
  // add a project: a job (with its client) or one of the firm's own lists, with its prefix on the spot
  const pn = q('[data-mmp="name"]'),
    pp = q('[data-mmp="prefix"]'),
    pc = q('[data-mmp="client"]');
  pn && pp && (pn.oninput = () => pp.dataset.typed || (pp.value = tkPrefixGuess(pn.value, "")));
  pp && (pp.oninput = () => (pp.dataset.typed = "1"));
  pc &&
    (pc.onchange = () => {
      const nc = q("[data-mmpnewc]");
      nc && ("__new" === pc.value ? nc.removeAttribute("hidden") : nc.setAttribute("hidden", ""));
    });
  const ps = q("[data-mmpsave]");
  ps && (ps.onclick = () => mmAddProject(m, { name: pn && pn.value, prefix: pp && pp.value, client: pc && pc.value, newClient: ((q('[data-mmp="newClient"]') || {}).value || "").trim() }));
}
// arrow keys walk the agenda on a keyboard; never while typing or with a sheet open
document.addEventListener("keydown", (e) => {
  try {
    if (!mmActive() || e.metaKey || e.ctrlKey || e.altKey) return;
    if (document.getElementById("mbm")) return;
    const t = e.target;
    if (t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable)) return;
    "ArrowRight" === e.key ? (e.preventDefault(), mmGo(1)) : "ArrowLeft" === e.key && (e.preventDefault(), mmGo(-1));
  } catch (err) {}
});

// ---- Tasks: Start Meeting, Rejoin, and the meeting taking the page -------------------------------------------------
{
  const base = renderTkAll;
  renderTkAll = function () {
    if (mmActive()) {
      const host = document.getElementById("tkall-body");
      if (host) {
        host.innerHTML = mmHtml();
        mmWire(host);
        return;
      }
    }
    const r = base.apply(this, arguments);
    try {
      mmDecorateTasks();
    } catch (e) {
      console.warn("meeting button", e);
    }
    return r;
  };
}
function mmDecorateTasks() {
  const host = document.getElementById("tkall-body");
  if (!host || host.querySelector("[data-mmbar], [data-mmstart]")) return;
  const m = mtCurrent(),
    can = mmCanRun();
  if (m) {
    // a meeting under way: one line to rejoin it, for everyone on Tasks
    const bar = document.createElement("div");
    bar.className = "mm-bar no-print";
    bar.dataset.mmbar = "1";
    bar.innerHTML = `<span class="grow">${mmSvg("team", 18)} ${esc(m.title)} is under way${m.presenter ? `, ${esc(tkFirst(m.presenter))} sharing` : ""}</span><button type="button" class="btn" data-mmjoin>Rejoin</button>`;
    const anchor = host.querySelector(".tk2-hline, .tk2-bar");
    anchor && anchor.parentNode ? anchor.parentNode.insertBefore(bar, anchor) : host.prepend(bar);
    bar.querySelector("[data-mmjoin]").onclick = () => ((mmOn = !0), (mmFollow = !0), renderTkAll());
    return;
  }
  if (!can) return;
  // Start Meeting sits with the page's own buttons: beside New Task on a wide screen, an icon beside search on the
  // phone (no new row above the list)
  const b = document.createElement("button");
  b.type = "button";
  b.dataset.mmstart = "1";
  b.onclick = () => mmStartDialog();
  const acts = host.querySelector(".tk2-ph .acts"),
    line = host.querySelector(".tk2-hline");
  if (tkPhone() && line) {
    b.className = "tk2-ic";
    b.setAttribute("aria-label", "Start Meeting");
    b.title = "Start Meeting";
    b.innerHTML = mmSvg("team", 20);
    const srch = line.querySelector("[data-tksearch]");
    srch ? line.insertBefore(b, srch) : line.appendChild(b);
  } else if (acts) {
    b.className = "btn";
    b.textContent = "Start Meeting";
    acts.insertBefore(b, acts.querySelector("#tk-new"));
  }
}
// a sign-in starts outside the meeting; Rejoin is one tap
{
  const base = signIn;
  signIn = function () {
    const r = base.apply(this, arguments);
    mmOn = !1;
    mmPanel = "";
    mmFollow = !0;
    return r;
  };
}

// ---- Today: the minutes, one line each, until read ----------------------------------------------------------------
function mtMinutesFor(me) {
  if (!me || !me.id) return [];
  const td = today();
  return mtTeam().filter((m) => {
    if (!m.endedAt || !m.minutes || (m.seen || {})[me.id]) return !1;
    if (dayDiff(m.date, td) > 7) return !1;
    return (m.attendees || []).includes(me.name) || !!(m.minutes.owes || {})[me.name];
  });
}
{
  const base = tdyModel;
  tdyModel = function () {
    const M = base.apply(this, arguments);
    try {
      const me = tdyMe(),
        L = mtMinutesFor(me).map((m) => {
          const owe = ((m.minutes.owes || {})[me.name] || []).length;
          return { kind: "tdyMinutes", id: m.id, src: "meeting", m: m, title: `Minutes: ${m.title}, ${tkDay(m.date)}`, detail: owe ? `you owe ${owe}` : "nothing on you", due: m.date };
        });
      if (L.length && M) {
        M.tasks = (M.tasks || []).concat(L);
        M.all = (M.all || []).concat(L);
      }
    } catch (e) {
      console.warn("minutes on Today", e);
    }
    return M;
  };
}
{
  const base = tdCard;
  tdCard = function (it) {
    if (it && "tdyMinutes" === it.kind) {
      const go = () => mtMinutesSheet(it.id);
      return { line1: `<a href="#" data-tdrec>${esc(it.title)}</a>`, why: esc(`Team meeting minutes · ${it.detail}`), verb: "Read", go: go, run: go };
    }
    return base.apply(this, arguments);
  };
}
{
  const base = tdScore;
  tdScore = function (it) {
    return it && "tdyMinutes" === it.kind ? 14 : base.apply(this, arguments);
  };
}
try {
  STD_MAP.meeting = { p: "", c: ["value", "own", /Close every loop/i] };
} catch (e) {}

// ---- the meeting on Meetings: its minutes and what was on screen --------------------------------------------------
{
  const base = mtMeetingHtml;
  mtMeetingHtml = function (m) {
    if (!m || "team" !== m.kind) return base.apply(this, arguments);
    const M = m.minutes || mtMinutesOf(m),
      log = (m.screenLog || []).map((s) => `<li><b>${esc(s.taskKey)}</b> <span class="small muted">${esc(String(s.from || "").slice(11, 19))} to ${esc(String(s.to || "").slice(11, 19) || "now")}</span></li>`).join("");
    return `<div class="crumb"><a href="#" data-mtback>Meetings</a><span>›</span>${esc(m.title)}</div><div class="ph"><div><h2 data-ia-keep="1">${esc(m.title)}</h2><div class="lead">${esc(tkDay(m.date))}${m.attendees && m.attendees.length ? " · with " + esc(m.attendees.join(", ")) : ""} · ${m.endedAt ? "ended " + esc(String(m.endedAt).slice(11, 16)) : "under way"}</div></div></div>
    <div class="grid2"><div><div class="card"><div class="hd"><h3>Minutes</h3></div><p class="small muted">${esc(m.summary || "")}</p>${mtMinutesHtml(m, M)}</div></div><div><div class="card"><div class="hd"><h3>On Screen</h3><span class="small muted">${(m.screenLog || []).length} tasks</span></div><ul class="mm-min">${log || '<li class="muted">Nothing yet.</li>'}</ul></div></div></div>`;
  };
}
// the meetings list's summary reads every meeting's summary as text
{
  const base = renderMeetings;
  renderMeetings = function () {
    try {
      mtTeam().forEach((m) => "string" != typeof m.summary && (m.summary = ""));
    } catch (e) {}
    const r = base.apply(this, arguments);
    try {
      document.querySelectorAll("#meetings-body [data-mmopen]").forEach(
        (b) =>
          (b.onclick = () => {
            const T = tkByCode(b.dataset.mmopen);
            T && tkOpen(T.key);
          }),
      );
    } catch (e) {}
    return r;
  };
}
// Settings › the team meeting's days and time
{
  const base = mtSettingsHtml;
  mtSettingsHtml = function () {
    const C = mtCadence();
    return (
      base.apply(this, arguments) +
      `<div class="card" style="margin-top:12px" data-mmcadence><div class="hd"><h3>The Team Meeting</h3></div><p class="small muted">The days and time the team walks the board. Meeting Mode reads them for what is due "before the next meeting" and for the Next Meeting date.</p><div class="row" style="gap:8px;flex-wrap:wrap">${[1, 2, 3, 4, 5]
        .map((d) => `<label class="chk"><input type="checkbox" data-mmday="${d}" ${C.days.includes(d) ? "checked" : ""}> ${DOW[d]}</label>`)
        .join("")}<label class="small">At <input type="time" data-mmtime value="${esc(C.time)}"></label></div></div>`
    );
  };
}
document.addEventListener("change", (e) => {
  const t = e.target;
  if (!t || !t.closest || !t.closest("[data-mmcadence]")) return;
  const box = t.closest("[data-mmcadence]"),
    days = [...box.querySelectorAll("[data-mmday]")].filter((x) => x.checked).map((x) => +x.dataset.mmday),
    time = (box.querySelector("[data-mmtime]") || {}).value || "10:00";
  if (!days.length) return void toast("Pick at least one day");
  DB.company = DB.company || {};
  const was = mtCadence();
  DB.company.meetCadence = { days: days, time: time };
  try {
    audit("company", "meetCadence", "cadence", `${was.days.map((d) => DOW[d]).join(", ")} ${was.time}`, `${days.map((d) => DOW[d]).join(", ")} ${time}`, "");
  } catch (err) {}
  save();
  toast(`The team meets ${days.map((d) => DOW[d]).join(" and ")} at ${time}`, [{ label: "Open", run: () => ((view = "meetings"), render()) }]);
});

// ---- found everywhere: ⌘K, Ask and erpQuery read the key ------------------------------------------------------------
{
  const base = palIndex;
  palIndex = function () {
    const items = base.apply(this, arguments);
    try {
      // one row per task: the current job's to-dos were listed on their own, without their key
      for (let i = items.length - 1; i >= 0; i--) "to-do" === items[i].k && items.splice(i, 1);
      tkKeyedRecs().forEach((r) => {
        const a = r.rec;
        if (!a.code || tkRecDone(r.kind, a)) return;
        const key = tkRecKey(r);
        items.push({ k: "Task", t: `${a.code} ${a.title || ""}`, s: `${tkBoardName(r.board)} · ${a.assignee || "nobody"}${a.due ? " · due " + fmt(a.due) : ""}`, go: () => tkOpen(key) });
      });
    } catch (e) {}
    return items;
  };
}
"undefined" != typeof AG_ASST &&
  AG_ASST.unshift({
    id: "tkCode",
    first: !0,
    kind: "ops",
    re: /\b[a-z][a-z0-9]{0,7}-\d{1,5}\b/,
    run(P) {
      if ("client" === role()) return null;
      const m = String(P.l || "").match(/\b([a-z][a-z0-9]{0,7})-(\d{1,5})\b/);
      const T = m && tkByCode(`${m[1]}-${m[2]}`.toUpperCase());
      if (!T) return null;
      const a = T.rec,
        st = tkStatusOf(T.kind, a),
        C = tkComments(a);
      return {
        headline: `${a.code}, ${a.title}: ${tkStatusSay(st).toLowerCase()}, owner ${a.assignee || "nobody"}${a.due ? `, due ${tkDay(a.due)}` : ", no due date"}${a.followUp ? `, follow up ${tkDay(a.followUp)}` : ""}${a.waitingOn && a.waitingOn.name ? `. ${tkWaitSay(a.waitingOn)}` : ""}.`,
        note: `${tkBoardName(T.board)}${a.lastDiscussed ? ` · last discussed ${tkDay(String(a.lastDiscussed.at).slice(0, 10))}` : ""}${C.length ? ` · ${C.length} comment${1 === C.length ? "" : "s"}` : ""}.`,
        work: C.slice(-5).map((c) => `${c.by || "Someone"} (${fmt(String(c.at).slice(0, 10))}): ${c.text}`),
        go: agGo("tkall"),
        ran: agRan("tasks", [`key is ${a.code}`], "", 1),
      };
    },
  });
{
  const base = eqTasks;
  eqTasks = function () {
    const R = base.apply(this, arguments) || [];
    try {
      let L = [];
      try {
        L = tkItems();
      } catch (e) {}
      return R.map((r, i) => {
        const x = L[i];
        if (!x || x.id !== r._id) return r;
        const W = x.waitingOn || null;
        return Object.assign(r, {
          key: x.code || "",
          followUp: x.followUp || "",
          watchUntil: x.watchUntil || "",
          statusLabel: x.done ? "Done" : tkStatusSay(x.status),
          waitingOnName: W ? W.name : x.waitsOn || "",
          waitingOnWhat: W ? W.what || "" : "",
          promised: W ? W.promised || "" : "",
          collaborators: (x.collaborators || []).join(", "),
          lastDiscussed: x.lastDiscussed ? String(x.lastDiscussed.at || "").slice(0, 10) : "",
          _label: x.code ? `${x.code} ${r._label}` : r._label,
        });
      });
    } catch (e) {
      return R;
    }
  };
}

// ---- the creation gate: an owner on the team, always ----------------------------------------------------------------
// The one creation path (crCreateTask). An outside name typed as the owner becomes Waiting On and the person making it
// owns it (or the job's lead), flagged to confirm; the dialogs ask before it gets here (tkOwnerAsk).
{
  const base = crCreateTask;
  crCreateTask = function (f) {
    const F = Object.assign({}, f || {});
    let outside = "";
    try {
      const nm = String(F.assignee || "").trim();
      if (nm && !tkInternal(nm) && !/\//.test(nm)) {
        outside = nm;
        const me = tkInternal(tkMe());
        F.assignee = me ? me.name : "";
        F.waitsOn = F.waitsOn || nm;
      }
    } catch (e) {}
    const made = base.call(this, F);
    try {
      if (made && made.rec) {
        F.section && "firm" === made.kind && (made.rec.section = F.section);
        outside && ((made.rec.ownerFlag = { was: outside, why: "outside", to: made.rec.assignee || "", at: today() }), tkSetWaiting(made.rec, { name: outside, promised: F.escalateOn || "" }));
        tkRecSweep();
        made.code = made.rec.code || "";
      }
    } catch (e) {
      console.warn("task record on create", e);
    }
    return made;
  };
}
// the New Task dialog: Waiting On names the outside person; the owner list is the team (it was free text on the board)
{
  const base = asTaskDialog;
  asTaskDialog = function () {
    const r = base.apply(this, arguments);
    try {
      const m = document.getElementById("mbm"),
        who = m && m.querySelector('[data-f="assignee"]'),
        ok = m && m.querySelector("#mbm-ok");
      if (who && ok && !ok.dataset.mmGate) {
        ok.dataset.mmGate = "1";
        ok.addEventListener(
          "click",
          (e) => {
            const v = String(who.value || "").trim();
            if (!v || tkInternal(v)) return;
            e.stopImmediatePropagation();
            e.preventDefault();
            toast(`${v} is not on the team. Pick the owner on the team; ${tkFirst(v)} goes in Waiting On on the task.`);
            who.focus();
          },
          !0,
        );
      }
    } catch (e) {}
    return r;
  };
}

// the job's task editor offered To Do, Doing and Done: saving a task that was Waiting On or FYI made it To Do
{
  const base = openActionEditor;
  openActionEditor = function (id) {
    const r = base.apply(this, arguments);
    try {
      const sel = document.getElementById("e-status"),
        a = id && S && (S.actions || []).find((x) => x.id === id),
        cur = (a && a.status) || "todo";
      sel && !sel.querySelector('option[value="fyi"]') && (sel.innerHTML = TK_STATUS.map(([k, n]) => `<option value="${k}" ${cur === k ? "selected" : ""}>${n}</option>`).join(""));
    } catch (e) {}
    return r;
  };
}
// ---- boot: the sweep runs once the whole page has loaded ------------------------------------------------------------
tkRecReady = !0;
{
  const base = finishBoot;
  finishBoot = function () {
    const r = base.apply(this, arguments);
    try {
      tkRecSweep() && save();
    } catch (e) {
      console.warn("task records at boot", e);
    }
    return r;
  };
}

// ---- the look --------------------------------------------------------------------------------------------------------
(() => {
  const css = `
#v-tkall .mm-bar{display:flex;align-items:center;gap:10px;min-height:48px;margin:0 0 10px;padding:6px 8px 6px 14px;border:1px solid var(--rule);border-radius:10px;background:var(--paper);font-size:14px}
#v-tkall .mm-bar svg{vertical-align:-4px;color:var(--ink-2)}
#v-tkall .mm-bar .btn{min-height:44px}
.mm{display:flex;flex-direction:column;gap:14px}
.mm-top{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:0 0 12px;border-bottom:1px solid var(--rule-2)}
.mm-top .btn{min-height:44px}
.mm-live{display:inline-flex;align-items:center;gap:6px;min-height:28px;padding:0 12px;border-radius:14px;background:var(--bad,#b3261e);color:#fff;font-size:13px;font-weight:700;white-space:nowrap}
.mm-live::before{content:"";width:8px;height:8px;border-radius:50%;background:#fff}
.mm-ttl{display:flex;flex-direction:column;gap:2px;font-size:18px;min-width:0}
.mm-prog{display:flex;flex-direction:column;gap:4px;font-size:13px;color:var(--ink-2);min-width:150px}
.mm-pbar{display:block;height:6px;border-radius:3px;background:var(--paper-3,#e8e8e8);overflow:hidden}
.mm-pbar i{display:block;height:100%;background:var(--accent)}
.mm-sr{display:inline-block;width:1px;height:1px;margin:0 -1px 0 0;padding:0;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0;vertical-align:top}
.mm-follow{display:inline-flex;align-items:center;gap:6px;min-height:44px;font-size:14px;cursor:pointer}
.mm-follow input{width:20px;height:20px}
.mm-body{display:grid;grid-template-columns:300px minmax(0,1fr) 340px;gap:20px;align-items:start}
.mm-phone .mm-body{grid-template-columns:minmax(0,1fr)}
.mm-side,.mm-right{position:sticky;top:8px;max-height:calc(100vh - 150px);overflow:auto;display:flex;flex-direction:column;gap:6px}
.mm-rh{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);padding:4px 2px 6px}
.mm-ag{display:grid;grid-template-columns:1fr auto;gap:2px 8px;width:100%;text-align:left;border:1px solid var(--rule);border-radius:10px;background:var(--paper);padding:10px 12px;cursor:pointer;min-height:56px}
.mm-ag:hover{background:var(--paper-2)}
.mm-ag.on{border-color:var(--accent);background:var(--accent-bg,#eaf1fb);box-shadow:inset 3px 0 0 var(--accent)}
.mm-agn{font-size:15px;font-weight:600;color:var(--ink)}
.mm-agn small{font-size:11px;font-weight:700;color:var(--ink-3);letter-spacing:.04em;margin-left:4px}
.mm-agc{grid-row:1 / span 2;grid-column:2;align-self:center;min-width:26px;height:26px;border-radius:13px;background:var(--paper-2);display:grid;place-items:center;font-size:13px;font-weight:700;color:var(--ink-2)}
.mm-ags{font-size:13px;color:var(--ink-3)}
.mm-agfyi{border-style:dashed}
.mm-agadd{display:inline-flex;align-items:center;gap:6px;min-height:44px;margin-top:4px;padding:0 12px;border:1px dashed var(--rule);border-radius:10px;background:none;font-size:14px;color:var(--ink-2);cursor:pointer}
.mm-log{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px;font-size:14px;line-height:20px}
.mm-log li{padding:8px 10px;border-radius:10px;background:var(--paper-2)}
.mm-lt{font-weight:700;color:var(--ink-2)}
.mm-lognote{font-size:13px;line-height:19px;color:var(--ink-3);margin:8px 0 0}
.mm-main{display:flex;flex-direction:column;gap:14px;min-width:0}
.mm-ctx{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:15px;color:var(--ink-2)}
.mm-changed{display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:13px;background:var(--bad-bg,#fdecea);color:var(--bad,#b3261e);font-size:13px;font-weight:700}
.mm-more{min-height:40px}
.mm-card{border:1px solid var(--rule);border-radius:16px;background:var(--paper);padding:26px 28px;display:flex;flex-direction:column;gap:16px;box-shadow:0 2px 10px rgba(0,0,0,.04)}
.mm-keyrow{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.mm-key{font-size:20px;font-weight:800;letter-spacing:.03em;color:var(--accent)}
.mm-st{font-size:13px;font-weight:600;padding:3px 10px;border-radius:12px;background:var(--paper-2);color:var(--ink-2)}
.mm-st-waiting{background:var(--warn-bg,#fff4e0)}
.mm-st-fyi{background:var(--paper-3,#eee)}
.mm-st-done{background:var(--ok-bg,#e8f5e9)}
.mm-title{font-size:32px;line-height:38px;margin:0;font-weight:650;word-break:break-word}
.mm-meta{display:flex;flex-wrap:wrap;gap:12px 32px;font-size:17px}
.mm-meta>div{display:flex;flex-direction:column;gap:2px}
.mm-meta .bad{color:var(--bad,#b3261e)}
.mm-own{display:inline-flex;align-items:center;gap:8px}
.mm-ml{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)}
.mm-wait{display:flex;align-items:flex-start;gap:10px;padding:12px 14px;border-radius:12px;background:var(--warn-bg,#fff4e0);border:1px solid #f2c97d;font-size:16px;line-height:22px;color:#6b4a00}
.mm-wait svg{flex:0 0 20px;margin-top:1px}
.mm-flag{padding:8px 12px;border-radius:10px;border:1px dashed var(--bad,#b3261e);font-size:14px}
.mm-comments{display:flex;flex-direction:column;gap:6px}
.mm-comment{padding:8px 12px;border-radius:10px;background:var(--paper-2);font-size:15px;line-height:21px}
.mm-links{display:flex;flex-wrap:wrap;gap:8px}
.mm-linkb{display:inline-flex;align-items:center;gap:6px;min-height:40px;padding:4px 12px;border:1px solid var(--rule);border-radius:10px;background:var(--paper);font-size:14px;cursor:pointer;max-width:100%}
.mm-linkb span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mm-acts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.mm-act{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;min-height:56px;padding:6px 4px;border:1px solid var(--rule);border-radius:12px;background:var(--paper);font-size:14px;line-height:17px;font-weight:600;color:var(--ink);cursor:pointer;white-space:nowrap;min-width:0}
.mm-act span{overflow:hidden;text-overflow:ellipsis;max-width:100%}
.mm-act:hover{background:var(--paper-2)}
.mm-act.on{border-color:var(--accent);background:var(--accent-bg,#eaf1fb)}
#v-tkall .mm .mm-act{min-height:56px;height:auto}
.mm-act.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.mm-act.primary.on{box-shadow:inset 0 0 0 2px rgba(255,255,255,.6);color:#fff;background:var(--accent)}
.mm-nav{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.mm-nav .mm-addbtn{flex:1 1 160px}
.mm-nav .btn{min-height:52px;font-size:16px;display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:0 18px}
.mm-nav .btn[disabled]{opacity:.45}
.mm-next{background:var(--ink,#1f2328);color:var(--paper,#fff);border-color:var(--ink,#1f2328)}
.mm-next:hover{opacity:.9}
.mm-addbtn{display:inline-flex;align-items:center;gap:8px;min-height:52px;padding:0 16px;border:1.5px dashed var(--rule);border-radius:12px;background:none;font-size:15px;font-weight:600;color:var(--ink-2);cursor:pointer;min-width:0}
.mm-addbtn span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mm-addbtn.on{border-color:var(--accent);color:var(--accent)}
.mm-hint{order:5;flex:1 1 100%;text-align:center;font-size:13px;color:var(--ink-3)}
.mm-phadd{display:flex;flex-direction:column;gap:8px}
.mm-phlog summary{min-height:44px;display:flex;align-items:center;font-size:15px;font-weight:600;cursor:pointer}
.mm-panel{border:1px solid var(--rule);border-radius:12px;padding:12px;background:var(--paper-2);display:flex;flex-direction:column;gap:8px}
.mm-panel .tks-chip.on{border-color:var(--accent);background:var(--accent-bg,#eaf1fb)}
.mm-panel .f input,.mm-panel .f select{min-height:44px;font-size:16px}
.mm-menu{flex-direction:row;flex-wrap:wrap}
.mm-menu .btn{min-height:44px}
.mm-seg{align-self:flex-start}
.mm-seg button{min-height:40px;padding:0 16px}
.mm-nav{display:flex;gap:12px}
.mm-nav .btn{flex:1 1 0;min-height:56px;font-size:17px;display:inline-flex;align-items:center;justify-content:center;gap:8px}
.mm-nav .btn[disabled]{opacity:.45}
.mm-addo{min-height:44px;font-size:15px;max-width:40%}
.mm-addrow .tks-in{min-width:0}
.mm-addp{align-self:flex-start;min-height:44px;display:inline-flex;align-items:center;gap:6px}
.mm-fyilist{margin:0;padding-left:0;list-style:none;display:flex;flex-direction:column;gap:6px;font-size:15px}
.mm-chip{display:inline-block;font-weight:700;color:var(--accent);margin-right:6px}
.mm-min{margin:0;padding-left:18px;font-size:14px;line-height:22px}
.mm-mlink{border:0;background:none;padding:0 2px;font-weight:700;color:var(--accent);cursor:pointer;min-height:24px}
.mm-mine{padding:10px 12px;border-radius:10px;background:var(--accent-bg,#eaf1fb);font-size:14px;margin-bottom:8px}
.mm-owes{margin-top:6px}
.mm-start .tks-person.on{border-color:var(--accent);background:var(--accent-bg,#eaf1fb)}
.mm-whole{display:flex;align-items:center;gap:8px;min-height:44px;margin-top:10px}
.mm-agsheet .tks-src.on{border-color:var(--accent)}
.tks-rec{display:flex;flex-direction:column;gap:4px}
.tks-links{display:flex;flex-direction:column;gap:6px}
.tks-links>.btn,.tks-file{align-self:flex-start;min-height:44px;display:inline-flex;align-items:center}
.tks-rec>.btn{align-self:flex-start;min-height:44px}
@media (max-width:760px){
  .mm-card{padding:16px;border-radius:12px;gap:12px}
  .mm-key{font-size:18px}
  .mm-title{font-size:24px;line-height:30px}
  .mm-meta{font-size:16px;gap:10px 20px}
  .mm-wait{font-size:15px}
  .mm-acts{grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
  .mm-act{font-size:13px;padding:6px 2px;letter-spacing:-.01em}
  .mm-phone{padding-bottom:84px;gap:10px}
  .mm-phone .mm-main{gap:10px}
  .mm-phone .mm-card{gap:10px}
  .mm-top.mm-top-ph{flex-wrap:nowrap;gap:8px;padding:0 0 8px;position:relative}
  .mm-top-ph .mm-live{flex:0 0 auto;font-size:12px;padding:0 9px;gap:5px}
  .mm-phttl{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:15px}
  .mm-top-ph .mm-prog{flex:0 0 auto;min-width:0;width:auto;font-size:12px;gap:3px;white-space:nowrap}
  .mm-top-ph .mm-prog .mm-pbar{height:4px}
  .mm-phmenu{flex:0 0 auto;position:static}
  .mm-phmenu>summary{list-style:none;display:inline-grid;place-items:center;width:44px;min-height:44px;padding:0;cursor:pointer}
  .mm-phmenu>summary::-webkit-details-marker{display:none}
  .mm-phmenu-in{position:absolute;right:0;top:calc(100% - 4px);z-index:40;display:flex;flex-direction:column;align-items:stretch;gap:8px;min-width:220px;padding:10px;border:1px solid var(--rule);border-radius:12px;background:var(--paper);box-shadow:0 10px 30px rgba(0,0,0,.16)}
  .mm-phmenu-in .btn{min-height:44px;justify-content:flex-start}
  .mm-notehd{display:flex;align-items:center;justify-content:space-between;gap:8px}
  .mm-notemore{min-height:44px}
  .mm-comments:not(.open) .mm-comment:not(:last-child){display:none}
  .mm-comments:not(.open) .mm-comment>div{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  body:has(.mm-phone .mm-nav) .toast{bottom:calc(58px + 76px + 10px + env(safe-area-inset-bottom))}
  .mm-nav{position:fixed;left:0;right:0;bottom:calc(58px + env(safe-area-inset-bottom));z-index:28;background:var(--paper);padding:8px 16px;border-top:1px solid var(--rule-2);box-shadow:0 -4px 12px rgba(0,0,0,.06)}
  .mm-nav .btn{flex:1 1 0}
  .mm-top{gap:8px}
  .mm-top .btn{padding:0 12px}
  .mm-follow{margin-right:auto}
  .mm-top .mm-ttl{flex:1 1 100%;order:-1}
  .mm-prog{flex:1 1 100%}
  .mm-addbtn{width:100%;justify-content:center}
  #v-tkall .mm button,#v-tkall .mm .mm-addbtn{min-height:44px}
  #v-tkall .mm .mm-mlink{min-width:44px}
  .mm-addo{max-width:46%}
  .mm-addrow{flex-wrap:wrap}
  .mm-addrow .tks-in{flex:1 1 100%}
}`;
  try {
    const s = document.createElement("style");
    (s.id = "mm-css"), (s.textContent = css), document.head.appendChild(s);
  } catch (e) {}
})();
/*<</meeting.js>>*/
