/*<<mtreview.js>>*/
/* =========================================================================================================
   mtreview (lane B of the Asana round, 2026-10-23; docs/TASKS_PLAN.md §2 item 6): the meeting's transcript
   reconciles the board, and the meeting's owner approves it in one Meeting Review.

   Design gate (BACKLOG §1.16). The noun is the meeting (DB.meetings: the same record Meeting Mode writes, with its
   screenLog [{taskKey, ref, from, to}] and changes [{taskKey, field, from, to, by, at}]; lane A's mtCurrent,
   mtScreenLog, mtLog, tkByCode, tkSetOwner and tkSetWaiting are used when they are there, read defensively). Its one list is the meeting's
   proposals (m.proposals): every item the transcript gives lands there, with status "proposed" (to review), "live"
   (already entered in Meeting Mode), "board" (already so on the board), "applied" or "skipped". The Meeting Review is
   a screen of that list, grouped by project. The queue is Approvals (kind "meeting", one item per meeting), routed to
   the meeting's owner (the coordinator who runs it), so it is a card on their Today. Tasks change only through the
   task functions (tkResolve, tkSetDue, tkLog, tkToggle, tdySetOwner), each with an audit line. One new store,
   DB.meetText: the transcript and its timed lines, kept off the shared meetings row because the transcript is
   visible to the meeting's attendees only (Alan, 10-23); on the hosted copy each is its own row (meettx:<id>) that
   only its members and the owner can read, like a message thread. A proposal keeps the line's number and time, not
   its words; the quote is read from the transcript when the viewer may read it.

   How a sentence finds its task: its line's time in the recording, plus the recording's start (the Gemini file's
   name, corrected by the lines that say a task's ID aloud), gives a time of day; the task on screen in Meeting Mode
   at that time is the task it was about. With no screen log: by the ID said ("PAD-23"), then by project and words.
   Reconciled, never doubled: anything already in the meeting's changes, or already so on the board, is not proposed.
   Every task has one internal owner (a team member); an item that names none waits for one to be picked.
--------------------------------------------------------------------------------------------------------- */
const MRV = MEETDOC_CORE;
const MRV_REF = /^[A-Z][A-Z0-9]{0,5}-\d{1,4}$/;
let mrvOn = "", // the meeting whose review is on screen
  mrvShowDone = !1;
function mrvInit() {
  "function" == typeof mtInit && mtInit();
  DB.meetText = Array.isArray(DB.meetText) ? DB.meetText : [];
  DB.company = DB.company || {};
  DB.company.meetWatch = Array.isArray(DB.company.meetWatch) ? DB.company.meetWatch : [];
  return DB.meetText;
}
const mrvMe = () => ("function" == typeof tdyMe ? tdyMe() : ("function" == typeof currentUser && currentUser()) || {}) || {};
const mrvTextOf = (m) => (m ? (DB.meetText || []).find((x) => x.meetingId === m.id) || null : null);
// the transcript is the attendees': its members (DB.users ids) and the owner
function mrvCanRead(m) {
  const T = mrvTextOf(m);
  if (!T) return !1;
  if ("owner" === role()) return !0;
  const me = mrvMe();
  return !!me.id && (T.members || []).includes(me.id);
}
const mrvStaff = () => ("function" == typeof mtStaff ? mtStaff() : (DB.users || []).filter((u) => "client" !== u.role).map((u) => u.name));
// a name said in the meeting, as a team member on file (the internal owner), or "" when it is nobody on the team
const mrvWho = (n) => {
  try {
    return (n && "function" == typeof mtPerson && mtPerson(n)) || "";
  } catch (e) {
    return "";
  }
};
const mrvUserId = (name) => {
  const u = (DB.users || []).find((x) => x.name === name) || ("function" == typeof tdyUserOf ? tdyUserOf(name) : null);
  return (u && u.id) || "";
};
const mrvProj = (id) => (id ? (DB.projects || []).find((p) => p.id === id) || null : null);
const mrvPName = (p) => (p ? ("function" == typeof shortName ? shortName(p) : p.project.name.replace(/ —.*$/, "")) : "");
const mrvPrefix = (p) => (p && ((p.project || {}).prefix || (p.project || {}).key || p.prefix)) || "";
// ---- tasks and their IDs ("PAD-23"): Meeting Mode's field when it is there, read defensively -------------------
function mrvRefOf(x, rec) {
  const r = rec || ("function" == typeof tdyRec ? tdyRec(x) : null) || {};
  for (const f of ["tkRef", "tkRefOf", "tkShortId", "tkIdOf"])
    if ("function" == typeof window[f])
      try {
        const v = window[f](x, r);
        if (MRV_REF.test(String(v || ""))) return v;
      } catch (e) {}
  for (const v of [r.ref, r.key, r.code, r.tid, r.shortId, x && x.ref]) if (MRV_REF.test(String(v || ""))) return v;
  const p = x && mrvProj(x.projectId),
    pre = mrvPrefix(p);
  return pre && null != r.num ? `${pre}-${r.num}` : "";
}
function mrvTasks() {
  let A = [];
  try {
    A = tkItems();
  } catch (e) {}
  return A.filter((x) => x && "draft" !== x.kind && "lead" !== x.kind).map((x) => {
    const rec = "function" == typeof tdyRec ? tdyRec(x) : null;
    return { x: x, rec: rec, key: t2Key(x), ref: mrvRefOf(x, rec) };
  });
}
// a key from the screen log or a change: a task ID ("PAD-23") or the task list's own key ("kind:id:project")
function mrvFind(k, T) {
  if (!k) return null;
  const L = T || mrvTasks();
  return L.find((t) => t.ref === k || t.key === k) || L.find((t) => t.x.id === k) || null;
}
const mrvSame = (a, b, T) => {
  if (!a || !b) return !1;
  if (a === b) return !0;
  const x = mrvFind(a, T),
    y = mrvFind(b, T);
  return !!x && !!y && x.key === y.key;
};
// ---- Meeting Mode's record, read defensively until it merges ------------------------------------------------
function mrvLive(m) {
  for (const f of ["mtCurrent", "mtgCurrent"])
    try {
      if ("function" == typeof window[f]) {
        const c = window[f]();
        if (c && c.id === m.id) return c;
      }
    } catch (e) {}
  return m;
}
function mrvScreenLog(m) {
  const L = mrvLive(m);
  let log = L.screenLog || (L.live && L.live.screenLog) || null;
  try {
    !log && "function" == typeof mtScreenLog && (log = mtScreenLog(L));
  } catch (e) {}
  // a line names its task by code (PAD-23) and by the task list's own key (ref), so a renumbered task still matches
  return (Array.isArray(log) ? log : []).filter((e) => e && (e.taskKey || e.ref) && e.from).map((e) => ({ taskKey: e.taskKey || e.ref, ref: e.ref || "", from: mrvWall(e.from), to: e.to ? mrvWall(e.to) : "" }));
}
const mrvChanges = (m) => {
  const L = mrvLive(m);
  return Array.isArray(L.changes) ? L.changes : L.live && Array.isArray(L.live.changes) ? L.live.changes : [];
};
// a stamp in the firm's own clock (appNowIso's form); one with a zone is turned into the firm's time
function mrvWall(s) {
  const t = String(s || "");
  if (!/(Z|[+-]\d{2}:?\d{2})$/.test(t)) return t.slice(0, 19);
  try {
    const d = new Date(t),
      f = new Intl.DateTimeFormat("en-CA", { timeZone: "function" == typeof APP_TZ ? APP_TZ() : "America/New_York", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" }),
      p = {};
    f.formatToParts(d).forEach((o) => (p[o.type] = o.value));
    return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}`;
  } catch (e) {
    return t.slice(0, 19);
  }
}
// ---- the transcript in: Drive (the server), a paste or an upload ------------------------------------------------
// the meeting a doc belongs to: Meeting Mode's record of that day (or the same series), else a new meeting record
// a live record and a recording are the same meeting only when they started within 90 minutes of each other (two
// meetings on one day are two meetings); with no start on either, the day decides
function mrvNear(x, start) {
  const a = MRV.wall(mrvWall(x.startedAt || x.start || ((x.screenLog || [])[0] || {}).from || "")),
    b = MRV.wall(start || "");
  return null == a || null == b || !/T\d/.test(start || "") || Math.abs(a - b) <= 5400;
}
function mrvMeetingFor(doc, o) {
  if (o.meetingId) return DB.meetings.find((x) => x.id === o.meetingId) || null;
  const day = DB.meetings.filter((x) => x.date === doc.date);
  if (o.docId) {
    const d = DB.meetings.find((x) => x.doc && x.doc.id === o.docId);
    if (d) return d;
  }
  return (
    day.find((x) => o.series && x.series === o.series) ||
    day.find((x) => (x.screenLog || (x.live && x.live.screenLog)) && !(x.doc && x.doc.id) && mrvNear(x, doc.start)) ||
    day.find((x) => "function" == typeof mtSim && mtSim(x.title, doc.title) >= 0.6 && !(x.doc && x.doc.id && o.docId)) ||
    null
  );
}
function mrvMembers(m, extra) {
  const ids = new Set(extra || []);
  (m.attendees || []).forEach((n) => {
    const id = mrvUserId(mrvWho(n) || n);
    id && ids.add(id);
  });
  m.owner && m.owner.uid && ids.add(m.owner.uid);
  const me = mrvMe();
  me.id && ids.add(me.id);
  return [...ids];
}
// the person who runs the meeting and approves its review: who the series names, else the coordinator
function mrvOwnerFor(o) {
  const W = (DB.company.meetWatch || []).find((w) => o.series && w.id === o.series);
  const uid = (W && W.ownerUid) || o.ownerUid || "",
    u = (DB.users || []).find((x) => x.id === uid) || (DB.users || []).find((x) => "coord" === x.role) || mrvMe();
  return { uid: u.id || "", name: u.name || "" };
}
function mrvIngest(text, opts) {
  mrvInit();
  const o = opts || {},
    doc = MRV.parseDoc(text, { name: o.name || "" });
  if (o.start && !doc.start) doc.start = mrvWall(o.start);
  if (!doc.date) doc.date = o.date || (doc.start || "").slice(0, 10) || today();
  if (!doc.lines.length && !doc.steps.length && !doc.decisions.length) return toast("Nothing to read: paste the whole notes doc, with its Transcript"), null;
  let m = mrvMeetingFor(doc, o);
  if (!m) {
    m = { id: uid("mt"), source: o.source || "paste", msgId: `${o.source || "paste"}:${o.docId || uid("d")}`, projectId: "", clientId: "", status: "new", createdAt: today(), proposals: [], title: doc.title, date: doc.date, summary: "", sections: [], steps: [], decisions: [], details: [], attendees: [] };
    DB.meetings.push(m);
  }
  m.proposals = m.proposals || [];
  m.title = m.title || doc.title;
  m.summary = m.summary || doc.summary || ("function" == typeof mtTopicLine ? mtTopicLine(doc.sections) : "");
  ["sections", "steps", "details"].forEach((k) => (!(m[k] || []).length && (doc[k] || []).length && (m[k] = doc[k])));
  (doc.quick || []).forEach((q) => (m.sections = m.sections || []).some((s) => s.h === q.h) || m.sections.push(q));
  (doc.decisions || []).length && !(m.decisions || []).length && (m.decisions = doc.decisions.map((d) => ({ text: d.name ? `${d.name}: ${d.text}` : d.text, status: "discuss" === d.status ? "needs-further-discussion" : "aligned", name: d.name })));
  (doc.attendees || []).forEach((n) => {
    const w = mrvWho(n) || n;
    (m.attendees = m.attendees || []).some((x) => mtNorm(x) === mtNorm(w)) || m.attendees.push(w);
  });
  o.series && (m.series = o.series);
  m.doc = { id: o.docId || (m.doc && m.doc.id) || "", url: o.url || (m.doc && m.doc.url) || "", name: o.name || "" };
  m.doc.url && !m.docUrl && (m.docUrl = m.doc.url);
  m.docRead = !0;
  m.owner = m.owner && m.owner.uid ? m.owner : mrvOwnerFor(o);
  let T = mrvTextOf(m);
  T || ((T = { id: `mx_${m.id}`, meetingId: m.id }), DB.meetText.push(T));
  // the shared-device flag holds names only (who sat with whom), so it rides on the meeting for everyone who reviews it
  m.sharedDevice = (doc.shared || []).map((x) => ({ label: x.label, with: x.with }));
  Object.assign(T, { invited: doc.invited || [], speakers: doc.speakers || [], members: mrvMembers(m, T.members), text: MRV.transcriptText(doc), lines: doc.lines, start: doc.start || T.start || "", links: Object.assign({}, T.links || {}, doc.links || {}), url: m.doc.url || "", at: appNowIso() });
  delete m.transcript; // the words live on the attendees' record only
  m.review = { state: "new", at: appNowIso(), source: o.source || "paste" };
  try {
    audit("meeting", m.id, "transcript", "", `${doc.lines.length} lines`, o.source || "paste");
  } catch (e) {}
  return m;
}
// ---- reading: the model where it is reachable (the server's read, or the assistant here), the rules otherwise ----
// ---- who is talking: each speaker label to a person, saved once for the workspace -----------------------------
// DB.company.meetSpeakers: {label (normalised): {uid, name} | {outside: true}, how, by, at}. A label is found by the
// map, then by the Google account's address on the doc's invited list, then by a name on the team, then as a
// vendor or client on file (someone outside the team). A dial-in number or a guest nobody knows is asked once.
const mrvSpk = () => ((DB.company = DB.company || {}), (DB.company.meetSpeakers = DB.company.meetSpeakers || {}), DB.company.meetSpeakers);
const mrvEmailOf = (u) => String(u.email || (/@/.test(u.contact || "") ? u.contact : "") || ((DB.conn || {})[u.id] || {}).email || "").toLowerCase().trim();
function mrvSpeakerOf(m, label) {
  const k = mtNorm(label || "");
  if (!k) return { unknown: !0 };
  const M = mrvSpk(),
    hit = M[k];
  if (hit) return hit.outside ? { outside: !0, how: hit.how } : { name: hit.name, uid: hit.uid, how: hit.how };
  const keep = (x) => ((M[k] = Object.assign({ label: String(label), by: "the reader", at: appNowIso() }, x)), x.outside ? { outside: !0, how: x.how } : { name: x.name, uid: x.uid, how: x.how });
  const T = mrvTextOf(m),
    inv = ((T && T.invited) || []).find((x) => mtNorm(x.name) === k),
    email = (inv && inv.email) || "";
  if (email) {
    const u = (DB.users || []).find((x) => "client" !== x.role && !/^mb_/.test(x.role || "") && mrvEmailOf(x) === email);
    if (u) return keep({ uid: u.id, name: u.name, how: "email" });
    const dom = email.split("@")[1] || "";
    const outside = (DB.vendors || []).some((v) => String(v.email || "").toLowerCase() === email) || (DB.clients || []).some((c) => (c.contacts || []).some((x) => String(x.email || "").toLowerCase() === email));
    if (outside) return keep({ outside: !0, how: "email" });
    dom && (DB.vendors || []).some((v) => String(v.email || "").toLowerCase().endsWith("@" + dom) && !/gmail|yahoo|outlook|icloud|example/.test(dom)) && (M[k] = { outside: !0, how: "domain", label: String(label), by: "the reader", at: appNowIso() });
    if (M[k]) return { outside: !0, how: "domain" };
  }
  const w = mrvWho(label);
  if (w && /[A-Za-z]/.test(label)) return keep({ uid: mrvUserId(w), name: w, how: "name" });
  const first = k.split(" ")[0];
  if (first.length >= 3 && /^[a-z]/.test(first) && ((DB.vendors || []).some((v) => mtNorm(v.name).split(" ")[0] === first) || (DB.clients || []).some((c) => mtNorm(c.name).split(" ").includes(first)))) return keep({ outside: !0, how: "name" });
  return { unknown: !0 };
}
function mrvSetSpeaker(label, value) {
  const k = mtNorm(label || "");
  if (!k) return;
  const me = mrvMe(),
    was = mrvSpk()[k];
  if ("__out" === value) mrvSpk()[k] = { label: String(label), outside: !0, how: "person", by: me.name || "", at: appNowIso() };
  else {
    const u = (DB.users || []).find((x) => x.id === value || x.name === value);
    const n = u ? u.name : mrvWho(value);
    if (!n) return;
    mrvSpk()[k] = { label: String(label), uid: u ? u.id : mrvUserId(n), name: n, how: "person", by: me.name || "", at: appNowIso() };
  }
  try {
    audit("company", k, "meetSpeaker", was ? was.name || (was.outside ? "outside" : "") : "", mrvSpk()[k].name || "outside", String(label));
  } catch (e) {}
  // every review not yet settled reads its lines again with the answer
  (DB.meetings || []).forEach((m) => m.review && "built" === m.review.state && (mrvTextOf(m) || {}).speakers && mrvTextOf(m).speakers.some((x) => mtNorm(x) === k) && mrvBuild(m));
  save();
}
function mrvCtx(m) {
  return {
    speakerOf: (l) => mrvSpeakerOf(m, l),
    speakers: ((mrvTextOf(m) || {}).speakers || []).map((l) => {
      const x = mrvSpeakerOf(m, l);
      return `${l}: ${x.name || (x.outside ? "outside the team" : "not known")}`;
    }),
    staff: mrvStaff(),
    date: m.date || today(),
    projects: (DB.projects || []).map((p) => ({ id: p.id, name: mrvPName(p), prefix: mrvPrefix(p) })),
    notes: { steps: (m.steps || []).slice(0, 40).map((s) => `[${s.owner}] ${s.title}: ${s.detail}`), decisions: (m.decisions || []).slice(0, 20).map((d) => d.text) },
  };
}
function mrvDocOf(m, T) {
  return { date: m.date, lines: T.lines || [], steps: m.steps || [], decisions: (m.decisions || []).map((d) => ({ name: d.name || "", text: d.text, status: /discuss/.test(d.status || "") ? "discuss" : "aligned" })) };
}
// The model reads the transcript in parts, from this page (paste on the hosted copy); its items are kept on the
// attendees' record, so the server's read and this one are used the same way.
async function mrvAiRead(m) {
  const T = mrvTextOf(m);
  if (!T || !T.text) return null;
  if ("function" != typeof ai || ("function" == typeof aiReady && !aiReady())) return null;
  const P = MRV.parts(T.text),
    ctx = mrvCtx(m),
    got = [];
  toast(`Reading the transcript in ${P.length} part${1 === P.length ? "" : "s"}`);
  for (let i = 0; i < P.length; i++) got.push(MRV.parseAnswer(await ai(MRV.prompt(P[i], i, P.length, ctx), 4000, 6e4)));
  if (!got.some(Boolean)) return null;
  T.extract = { by: "model", at: appNowIso(), items: MRV.merge(got) };
  return T.extract;
}
function mrvItems(m) {
  const T = mrvTextOf(m),
    ctx = mrvCtx(m),
    doc = mrvDocOf(m, T || {});
  if (T && T.extract && Array.isArray(T.extract.items)) {
    // the model's items, with Gemini's own steps and decisions it may have dropped (one item once)
    const L = T.extract.items.map((x) => Object.assign({}, x, { line: mrvLineOf(T, x) }));
    return { by: "model", items: MRV.merge([L, MRV.fromNotes(doc, ctx)]) };
  }
  return { by: "rules", items: MRV.rules(doc, ctx) };
}
// the transcript line an item quotes: its time, then its words
function mrvLineOf(T, x) {
  if (null != x.line && x.line >= 0 && T.lines[x.line]) return x.line;
  const L = T.lines || [],
    at = MRV.hms(x.ts),
    q = MRV.words(x.quote || x.what || "");
  let best = -1,
    bs = 0;
  L.forEach((l, i) => {
    const s = MRV.sim(q, MRV.words(l.text)) - (null != at ? Math.min(0.5, Math.abs(l.sec - at) / 600) : 0);
    s > bs && ((bs = s), (best = i));
  });
  return bs >= 0.4 ? best : -1;
}
// ---- one item to one proposal: which task, which project, and whether it is already done ---------------------
// the fields Meeting Mode logs (lane A's mtLog), by the kind of item they settle
const MRV_FIELDS = { tkdate: ["due", "followUp"], tkdone: ["status"], tknote: ["comment", "note"], tkowner: ["owner"], tkwait: ["waitingOn"], tktrack: ["watchUntil"], money: ["comment", "note", "link"] };
const MRV_KIND = { date: "tkdate", done: "tkdone", note: "tknote", owner: "tkowner", track: "tktrack" };
const mrvHash = (s) => {
  let h = 2166136261;
  for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return (h >>> 0).toString(36);
};
// money said aloud, tied to the record it touches: a bill or an order from the vendor named, the amount if it was said
function mrvMoneyLink(text, amount, projectId) {
  const hay = ` ${mtNorm(text)} `;
  const V = (DB.vendors || []).filter((v) => v.name && hay.includes(` ${mtNorm(v.name)} `)).map((v) => v.name);
  const bills = (DB.bills || []).filter((b) => V.some((v) => mtNorm(v) === mtNorm(b.vendor)) && (!projectId || !b.projectId || b.projectId === projectId));
  const pos = (DB.pos || []).filter((p) => V.some((v) => mtNorm(v) === mtNorm(p.vendor)) && (!projectId || !p.projectId || p.projectId === projectId));
  const tot = (b) => {
    try {
      return "function" == typeof billTotal ? billTotal(b) : +b.total || 0;
    } catch (e) {
      return 0;
    }
  };
  const b = bills.find((x) => amount && Math.abs(tot(x) - amount) < 1) || bills[0];
  if (b) return { kind: "bill", id: b.id, label: `${b.number || "Bill"} · ${b.vendor}`, vendor: b.vendor };
  const po = pos[0];
  if (po) return { kind: "po", id: po.id, label: `${po.number} · ${po.vendor}`, vendor: po.vendor };
  return V.length ? { kind: "vendor", id: ((DB.vendors || []).find((v) => v.name === V[0]) || {}).id || "", label: V[0], vendor: V[0] } : null;
}
const MRV_MONEY = { deposit: "Release the deposit", credit: "Get the credit", chargeback: "Pursue the chargeback", zerocost: "Log at zero cost, decide on billing later", overhead: "Finish the overhead calculation", bill: "Bill it", other: "Money" };
function mrvBuild(m, opts) {
  mrvInit();
  const o = opts || {},
    T = mrvTextOf(m);
  if (!T) return null;
  const { by, items } = o.items ? { by: o.by || "model", items: o.items } : mrvItems(m),
    tasks = mrvTasks(),
    log = mrvScreenLog(m),
    changes = mrvChanges(m),
    lines = T.lines || [],
    start = mrvWall(T.start || m.start || m.startedAt || (log[0] && log[0].from) || ""),
    s0 = MRV.wall(start);
  // the recording's start, corrected by the lines that name a task aloud
  const anchors = [];
  items.forEach((x) => {
    const li = mrvLineOf(T, x);
    if (li < 0 || !x.ref || null == s0) return;
    const t = mrvFind(x.ref, tasks);
    anchors.push({ sec: s0 + lines[li].sec, key: x.ref, keys: t ? [t.key, t.x.id] : [] });
  });
  lines.forEach((l) => {
    const r = (MRV.REF.exec(l.text) || [])[0];
    if (!r || null == s0 || anchors.some((a) => a.key === r && a.sec === s0 + l.sec)) return;
    const t = mrvFind(r, tasks);
    anchors.push({ sec: s0 + l.sec, key: r, keys: t ? [t.key, t.x.id] : [] });
  });
  const shift = null == s0 ? 0 : MRV.bestShift(anchors, log, T.start ? 300 : 3600);
  // keep what a person already decided; everything else is read again
  const keep = (m.proposals || []).filter((p) => !p.review || "applied" === p.status || "skipped" === p.status);
  const made = [],
    seen = new Set(keep.map((p) => p.id));
  items.forEach((x, n) => {
    const pr = mrvPropose(m, T, x, { tasks, log, changes, s0, shift, lines, oneJob: mrvOneJob(m) });
    if (!pr) return;
    if (seen.has(pr.id)) return;
    seen.add(pr.id);
    made.push(pr);
  });
  m.proposals = keep.concat(made);
  m.review = Object.assign({}, m.review || {}, { state: "built", by: by, at: appNowIso(), start: start, shift: shift, items: items.length, screen: log.length });
  return m.review;
}
// the one job a meeting is about, when its title and notes name exactly one ("a coordination call on 121 State");
// a team meeting that walks several jobs has none, and each item finds its own
function mrvOneJob(m) {
  const t = " " + mtNorm([m.title, m.summary, ...(m.sections || []).map((x) => `${x.h} ${x.text}`)].join(" ")) + " ";
  const L = (DB.projects || []).filter((p) => {
    const nm = p.project.name.replace(/ \u2014.*$/, "");
    if (t.includes(` ${mtNorm(nm)} `)) return !0;
    const num = nm.match(/(\d{1,4})\s+([A-Za-z]+)/);
    return !!num && new RegExp(`\\b${num[1]}\\s+${mtNorm(num[2])}\\b`).test(t);
  });
  return 1 === L.length ? L[0] : null;
}
// the job a client's name points to ("the Klein parlor counters"), when that client has exactly one open job
function mrvClientJob(text) {
  try {
    const c = "function" == typeof mtMatchClient ? mtMatchClient({ title: "", summary: text }, null) : null;
    const L = c ? (DB.projects || []).filter((p) => p.clientId === c.id && !p.archived) : [];
    return 1 === L.length ? L[0] : null;
  } catch (e) {
    return null;
  }
}
function mrvPropose(m, T, x0, C) {
  let x = x0;
  const li = mrvLineOf(T, x),
    line = li >= 0 ? C.lines[li] : null,
    sec = line && null != C.s0 ? C.s0 + line.sec + C.shift : null,
    shown = null != sec ? MRV.onScreen(C.log, sec) : "",
    byRef = x.ref ? mrvFind(x.ref, C.tasks) : null,
    onTask = shown ? mrvFind(shown, C.tasks) || mrvFind((C.log.find((e) => e.taskKey === shown) || {}).ref, C.tasks) : null;
  // with no screen log, the task named aloud last (the coordinator says each task's ID as the board is walked),
  // within the four minutes before the sentence, is the task it was about
  let named = null;
  if (!byRef && !onTask && !C.log.length && line)
    for (let i = li; i >= 0 && line.sec - C.lines[i].sec <= 240; i--) {
      const r = (MRV.REF.exec(C.lines[i].text) || [])[0];
      if (r) {
        named = mrvFind(r, C.tasks);
        break;
      }
    }
  let task = byRef || onTask || named || null,
    how = byRef ? "id" : onTask ? "screen" : named ? "said" : "";
  const said = `${x.what || ""} ${x.note || ""} ${x.quote || ""}`;
  let p = task ? mrvProj(task.x.projectId) : null;
  p || (p = (x.project && mrJob(x.project, "")) || mrJob("", said) || mrvClientJob(said) || C.oneJob || null);
  const upd = !!MRV_KIND[x.kind] || "waiting" === x.kind || "money" === x.kind;
  // with no screen log, an update finds its task by words, in its project
  if (!task && upd && "waiting" !== x.kind) {
    const pool = C.tasks.filter((t) => !t.x.done && (!p || t.x.projectId === p.id)),
      best = pool.map((t) => ({ t: t, s: MRV.sim(said, t.x.title) })).sort((a, b) => b.s - a.s)[0];
    best && best.s >= 0.5 && ((task = best.t), (how = "words"), (p = mrvProj(task.x.projectId)));
  }
  const id = `mrv_${m.id}_${mrvHash(`${x.kind}|${x.ts || ""}|${x.ref || ""}|${x.what || x.note || ""}|${x.source || ""}`)}`,
    pr = { id: id, review: !0, status: "proposed", kind: "", title: "", detail: "", line: li, ts: line ? line.ts : x.ts || "", head: line ? line.head : "", speaker: line ? line.speaker : x.speaker || "", source: x.source || "transcript", quote: "transcript" === (x.source || "transcript") && li >= 0 ? "" : MRV.clean(x.quote, 300), how: how, taskKey: task ? task.key : "", ref: task ? task.ref : x.ref || "", projectId: p ? p.id : "", apply: {}, at: sec != null ? MRV.wallIso(sec).slice(11) : "" };
  // who said it: a promise in the first person makes the speaker the owner; an unknown speaker is asked about once,
  // and a speaker label that two people shared leaves an owner taken from it to be checked
  const spk = line ? mrvSpeakerOf(m, line.speaker) : {},
    shared = line && (m.sharedDevice || []).find((d) => mtNorm(d.label) === mtNorm(line.speaker));
  if (x.ownerFrom === "speaker" && spk.name && !mrvWho(x.owner)) x = Object.assign({}, x, { owner: spk.name });
  if (x.owner && !mrvWho(x.owner) && spk.name && mtNorm(x.owner) === mtNorm(line.speaker)) x = Object.assign({}, x, { owner: spk.name });
  pr.speakerName = spk.name || "";
  x.speakerUnknown && spk.unknown && (pr.needSpeaker = !0);
  shared && x.ownerFrom === "speaker" && (pr.confirm = { label: shared.label, with: shared.with });
  const t = task ? task.x : null,
    tTitle = t ? t.title : "",
    tName = `${task && task.ref ? task.ref + " · " : ""}${tTitle}`;
  if (MRV_KIND[x.kind]) {
    pr.kind = MRV_KIND[x.kind];
    if (!task) pr.needs = ["task"];
    if ("tkdate" === pr.kind) Object.assign(pr, { title: `New date: ${x.due ? fmtL(x.due) : x.dueSaid || "the date said"}`, apply: { key: pr.taskKey, due: x.due || "" }, from: t ? t.due || "" : "", to: x.due || "" }), x.due || (pr.needs = (pr.needs || []).concat("date"));
    if ("tkdone" === pr.kind) Object.assign(pr, { title: "Mark it done", apply: { key: pr.taskKey } });
    if ("tknote" === pr.kind) Object.assign(pr, { title: `Note: ${MRV.clean(x.note || x.what, 140)}`, apply: { key: pr.taskKey, text: MRV.clean(x.note || x.what, 300) } });
    if ("tkowner" === pr.kind) {
      const w = mrvWho(x.owner);
      Object.assign(pr, { title: `Reassign to ${w || x.owner || "someone on the team"}`, apply: { key: pr.taskKey, owner: w }, from: t ? t.assignee || "" : "", to: w });
      w || (pr.needs = (pr.needs || []).concat("owner"));
    }
    if ("tktrack" === pr.kind) Object.assign(pr, { title: `Track until ${x.due ? fmtL(x.due) : x.dueSaid}`, apply: { key: pr.taskKey, until: x.due || "" } });
  } else if ("waiting" === x.kind && task) {
    const own = mrvWho(t.assignee || t.owner || "");
    Object.assign(pr, { kind: "tkwait", title: `Waiting on ${x.party || "someone outside the team"}${x.due ? ` · promised ${fmtL(x.due)}` : ""}`, apply: { key: pr.taskKey, party: x.party || "", what: MRV.clean(x.what, 160), by: x.due || "", owner: own } });
    own || (pr.needs = ["owner"]);
  } else if ("money" === x.kind && task) {
    const link = mrvMoneyLink(said, x.amount, p ? p.id : "");
    Object.assign(pr, { kind: "money", title: `${MRV_MONEY[x.moneyKind] || "Money"}${x.amount ? ` · ${money(x.amount)}` : ""}`, apply: { key: pr.taskKey, amount: x.amount || 0, moneyKind: x.moneyKind || "other", link: link, text: MRV.clean(x.what || x.quote, 200) }, linkLabel: link ? link.label : "" });
  } else if ("task" === x.kind || "waiting" === x.kind || "money" === x.kind) {
    // new work: one internal owner always; a vendor or consultant is who it waits on
    const owner = mrvWho(x.owner),
      party = "waiting" === x.kind ? x.party || "" : x.party && !mrvWho(x.party) ? x.party : "",
      link = "money" === x.kind ? mrvMoneyLink(said, x.amount, p ? p.id : "") : null,
      title = "money" === x.kind ? `${MRV_MONEY[x.moneyKind] || "Money"}: ${MRV.clean(x.what, 120)}` : "waiting" === x.kind ? `${MRV.clean(x.what, 120)} (from ${party})` : MRV.clean(x.what, 160);
    Object.assign(pr, { kind: "task", title: title, apply: { projectId: p ? p.id : "", title: title, assignee: owner, due: x.due || "", party: party, waitBy: "waiting" === x.kind ? x.due || "" : "", amount: x.amount || 0, link: link, group: !!x.group }, linkLabel: link ? link.label : "" });
    const need = [];
    owner || need.push("owner");
    p || need.push("project");
    need.length && (pr.needs = need);
  } else if ("decision" === x.kind) {
    const aligned = "discuss" !== x.status;
    Object.assign(pr, { kind: "decision", title: `${aligned ? "Decided" : "To discuss"}: ${MRV.clean(x.what, 160)}`, apply: { projectId: p ? p.id : "", name: MRV.clean(x.what, 120), made: aligned, note: `${aligned ? "Decided" : "Raised, to discuss"} in ${m.title} · ${fmtL(m.date)}`, owner: (m.owner && m.owner.name) || "" }, discuss: !aligned });
    p || (pr.needs = ["project"]);
  } else if ("project" === x.kind) {
    const name = MRV.clean(x.project || x.what, 80),
      have = (DB.projects || []).find((q) => mtSim(q.project.name, name) >= 0.8),
      pre = (name.replace(/^\d+\s+/, "").match(/[A-Za-z]+/) || [""])[0].slice(0, 3).toUpperCase();
    if (have) return Object.assign(pr, { kind: "project", status: "board", title: `New project: ${name}`, boardWhy: `${mrvPName(have)} is already a project`, apply: { name: name } });
    Object.assign(pr, { kind: "project", title: `New project: ${name}`, apply: { name: name, prefix: pre } });
  } else if ("meeting" === x.kind) {
    const owner = mrvWho(x.owner);
    Object.assign(pr, { kind: "event", title: `Set up: ${MRV.clean(x.what, 120)}${x.due ? ` · ${fmtL(x.due)}` : ""}${x.time ? ` ${x.time}` : ""}`, apply: { projectId: p ? p.id : "", title: MRV.clean(x.what, 120), due: x.due || "", time: x.time || "", owner: owner } });
    owner || (pr.needs = ["owner"]);
  } else return null;
  pr.detail = mrvDetail(pr, t);
  // reconciled: already entered live in Meeting Mode, or already so on the board
  const fields = MRV_FIELDS[pr.kind];
  if (fields && pr.taskKey) {
    const ch = C.changes.find((c) => c && (mrvSame(c.taskKey, pr.taskKey, C.tasks) || mrvSame(c.ref, pr.taskKey, C.tasks)) && fields.includes(c.field) && ("tkdone" !== pr.kind || /done|complete|true/i.test(String(c.to))));
    if (ch) return Object.assign(pr, { status: "live", liveBy: ch.by || "", liveAt: ch.at || "", liveTo: ch.to });
    const rec = task.rec || {};
    if ("tkdone" === pr.kind && (t.done || "done" === rec.status)) return Object.assign(pr, { status: "board", boardWhy: "already done" });
    if ("tkdate" === pr.kind && pr.apply.due && (t.due === pr.apply.due || rec.due === pr.apply.due)) return Object.assign(pr, { status: "board", boardWhy: "already has that date" });
    if ("tkowner" === pr.kind && pr.apply.owner && mtNorm(t.assignee || "") === mtNorm(pr.apply.owner)) return Object.assign(pr, { status: "board", boardWhy: `already ${pr.apply.owner}'s` });
    if ("tknote" === pr.kind && (rec.thread || []).some((e) => e && e.text && MRV.sim(e.text, pr.apply.text) >= 0.8)) return Object.assign(pr, { status: "board", boardWhy: "the note is there" });
    const wn = (rec.waitingOn && rec.waitingOn.name) || rec.waitsOn || "";
    if ("tkwait" === pr.kind && wn && mtNorm(wn) === mtNorm(pr.apply.party)) return Object.assign(pr, { status: "board", boardWhy: `already waiting on ${wn}` });
  }
  if ("decision" === pr.kind) {
    const live = C.changes.find((c) => c && "decision" === c.field && MRV.sim(String(c.to || ""), pr.apply.name) >= 0.5);
    if (live) return Object.assign(pr, { status: "live", liveBy: live.by || "", liveAt: live.at || "" });
  }
  if ("task" === pr.kind) {
    const live = C.changes.find((c) => c && /^(created|new|task|add)$/.test(c.field || "") && MRV.sim(String(c.to || c.title || ""), pr.apply.title) >= 0.6);
    if (live) return Object.assign(pr, { status: "live", liveBy: live.by || "", liveAt: live.at || "" });
    // the same work already on the board: on the same job, or (with no job known) the same words exactly
    const same = C.tasks.find((k) => !k.x.done && (pr.apply.projectId ? k.x.projectId === pr.apply.projectId && MRV.sim(pr.apply.title, k.x.title) >= 0.6 : MRV.sim(pr.apply.title, k.x.title) >= 0.8));
    if (same) return Object.assign(pr, { status: "board", boardWhy: `on the board as ${same.ref ? same.ref + " · " : ""}${same.x.title}`, taskKey: same.key });
  }
  return pr;
}
function mrvDetail(pr, t) {
  const A = pr.apply || {},
    on = t ? `${pr.ref ? pr.ref + " · " : ""}${t.title}` : "";
  if (/^tk|^money$/.test(pr.kind)) {
    const ch = "tkdate" === pr.kind ? `${pr.from ? fmtL(pr.from) : "no date"} to ${A.due ? fmtL(A.due) : "?"}` : "tkowner" === pr.kind ? `${pr.from || "nobody"} to ${A.owner || "?"}` : "tkwait" === pr.kind ? `${A.party} owes: ${A.what}; ${A.owner || "the owner"} chases it` : "money" === pr.kind ? (pr.linkLabel ? `linked to ${pr.linkLabel}` : "no bill or order matched yet: the note keeps the amount") : "";
    return [on || "No task matched: pick the task", ch].filter(Boolean).join(" · ");
  }
  if ("task" === pr.kind) return [A.assignee ? `Owner ${A.assignee}` : "Needs an owner on the team", A.party ? `waiting on ${A.party}${A.waitBy ? ` by ${fmtL(A.waitBy)}` : ""}` : "", A.due ? `due ${fmtL(A.due)}` : "", pr.linkLabel ? `linked to ${pr.linkLabel}` : ""].filter(Boolean).join(" · ");
  if ("event" === pr.kind) return [A.owner ? `${A.owner} sets it up` : "Needs an owner on the team", A.due ? fmtL(A.due) : "no date said"].join(" · ");
  if ("decision" === pr.kind) return pr.discuss ? "Goes on the decision log as open, to settle" : "Goes on the decision log as made";
  if ("project" === pr.kind) return `A new job with its own prefix (${A.prefix || "set it"}); its scope is set later`;
  return "";
}
// what still has to be picked before Accept
function mrvNeeds(pr) {
  const A = pr.apply || {},
    out = [];
  /^tk|^money$/.test(pr.kind) && !A.key && out.push("task");
  ("task" === pr.kind || "tkwait" === pr.kind) && !mrvWho(A.assignee || A.owner || "") && out.push("owner");
  "tkowner" === pr.kind && !mrvWho(A.owner || "") && out.push("owner");
  "event" === pr.kind && !mrvWho(A.owner || "") && out.push("owner");
  ("task" === pr.kind || "decision" === pr.kind) && !A.projectId && !A.office && out.push("project");
  "tkdate" === pr.kind && !A.due && out.push("date");
  pr.needSpeaker && !mrvWho(A.assignee || A.owner || "") && out.push("speaker");
  return out;
}
// Waiting On, in the task record's shape ({name, what, promised, evidence}; Meeting Mode's tkSetWaiting when there):
// the outsider who owes it, what, the date they promised (the follow-up date) and where it was said
function mrvWait(rec, W) {
  if ("function" == typeof tkSetWaiting) return tkSetWaiting(rec, W);
  rec.waitingOn = { name: W.name, what: W.what || "", promised: W.promised || "", evidence: W.evidence || "" };
  rec.waitsOn = W.name;
  W.promised && !rec.followUp && (rec.followUp = W.promised);
}
// an office task (no job): the firm's own task list (DB.tasks, the "firm" kind every task list reads)
function mrvOfficeTask(t) {
  const L = "function" == typeof asFirmTasks ? asFirmTasks() : (DB.tasks = DB.tasks || []);
  L.push(Object.assign({ code: "", section: "", tags: [], modifiedAt: today() }, t));
  return t2Key({ kind: "firm", id: t.id, projectId: "" });
}
// ---- applying: through the task functions, with an audit line, and on the meeting's changes --------------------
function mrvApply(m, pr) {
  const A = pr.apply || {},
    me = mrvMe(),
    src = `${m.title} · ${fmtL(m.date)}${pr.ts ? ` · ${pr.ts}` : ""}`,
    need = mrvNeeds(pr);
  if (need.length) return { ok: !1, why: need };
  let out = { ok: !0, key: A.key || "" };
  const R = A.key ? tkResolve(A.key) : null;
  if (/^tk|^money$/.test(pr.kind) && !R) return { ok: !1, why: ["task"] };
  const rec = R && R.rec,
    stamp = (field, from, to, key) => {
      // the meeting's own change log (Meeting Mode's mtLog when it is there), so the minutes and a re-read see it
      const k = key || A.key || pr.taskKey || "",
        t = k ? mrvFind(k) : null,
        c = { taskKey: (t && t.ref) || "", ref: (t && t.key) || k, field: field, from: from, to: to, via: "review", proposal: pr.id };
      try {
        if ("function" == typeof mtLog && mtLog.length >= 1 && mtLog(c, m)) return;
      } catch (e) {}
      (m.changes = Array.isArray(m.changes) ? m.changes : []).push(Object.assign({ by: me.name || "", at: appNowIso() }, c));
    };
  if ("tkdate" === pr.kind) {
    const was = R.x.due || "";
    if (!tkSetDue(R, A.due)) return { ok: !1, why: ["task"] };
    rec && tkLog(rec, { text: `New date from ${src}: ${fmtL(A.due)}`, meetingId: m.id });
    stamp("due", was, A.due);
  } else if ("tkdone" === pr.kind) {
    if (!R.x.done && !(rec && "done" === rec.status)) {
      try {
        tkToggle(R.x.kind, R.x.id, R.x.projectId);
      } catch (e) {
        return { ok: !1, why: ["task"] };
      }
    }
    rec && tkLog(rec, { ev: "done", text: `Marked done from ${src}`, meetingId: m.id });
    try {
      audit("task", R.x.id, "done", "", today(), `meeting ${m.id}`);
    } catch (e) {}
    stamp("status", "open", "done");
  } else if ("tknote" === pr.kind || "money" === pr.kind) {
    if (!rec) return { ok: !1, why: ["task"] };
    const text0 = "money" === pr.kind ? `${MRV_MONEY[A.moneyKind] || "Money"}${A.amount ? ` ${money(A.amount)}` : ""}: ${A.text}${A.link ? ` (${A.link.label})` : ""}` : A.text;
    const text = text0;
    tkLog(rec, { text: `${text} (from ${src})`, meetingId: m.id });
    "money" === pr.kind && A.link && !rec.link && (rec.link = { kind: A.link.kind, id: A.link.id });
    "money" === pr.kind && A.amount && !rec.amount && (rec.amount = A.amount);
    try {
      audit("task", R.x.id, "note", "", text.slice(0, 80), `meeting ${m.id}`);
    } catch (e) {}
    stamp("comment", "", text);
  } else if ("tkowner" === pr.kind) {
    const was = R.x.assignee || "";
    if ("function" == typeof tkSetOwner) {
      const r = tkSetOwner(R, A.owner);
      if (!r || !r.ok) return { ok: !1, why: ["owner"] };
    } else {
      "function" == typeof tdySetOwner ? tdySetOwner(R.x, rec, A.owner) : (rec.assignee = A.owner);
      try {
        audit("task", R.x.id, "owner", was, A.owner, `meeting ${m.id}`);
      } catch (e) {}
    }
    rec && tkLog(rec, { ev: "owner", from: was, to: A.owner, text: `Reassigned to ${A.owner} in ${src}`, meetingId: m.id });
    stamp("owner", was, A.owner);
  } else if ("tkwait" === pr.kind) {
    if (!rec) return { ok: !1, why: ["task"] };
    const was = (rec.waitingOn && rec.waitingOn.name) || rec.waitsOn || "";
    mrvWait(rec, { name: A.party, what: A.what, promised: A.by || "", evidence: `Said in ${src}` });
    tkLog(rec, { ev: "waiting", text: `Waiting on ${A.party}: ${A.what}${A.by ? `, promised ${fmtL(A.by)}` : ""} (${src})`, meetingId: m.id });
    try {
      audit("task", R.x.id, "waiting", was, A.party, `meeting ${m.id}`);
    } catch (e) {}
    stamp("waitingOn", was, A.party);
  } else if ("tktrack" === pr.kind) {
    if (!rec) return { ok: !1, why: ["task"] };
    const was = rec.watchUntil || "";
    rec.watchUntil = A.until;
    tkLog(rec, { ev: "track", text: `Track until ${fmtL(A.until)} (${src})`, meetingId: m.id });
    try {
      audit("task", R.x.id, "track", was, A.until, `meeting ${m.id}`);
    } catch (e) {}
    stamp("watchUntil", was, A.until);
  } else if ("task" === pr.kind) {
    const p = mrvProj(A.projectId),
      t = { id: uid("a"), title: A.title, assignee: mrvWho(A.assignee), due: A.due || A.waitBy || "", priority: "med", status: "todo", link: A.link && A.link.id ? { kind: A.link.kind, id: A.link.id } : null, notes: `From ${src}`, source: { kind: "meeting", id: m.id, label: `Meeting · ${m.title} · ${fmtL(m.date)}`, ts: pr.ts || "" }, createdAt: today(), completedAt: "" };
    A.party && mrvWait(t, { name: A.party, what: A.title, promised: A.waitBy || "", evidence: `Said in ${src}` });
    A.amount && (t.amount = A.amount);
    if (p) (p.actions = p.actions || []).push(t), (out.key = t2Key({ kind: "action", id: t.id, projectId: p.id }));
    else out.key = mrvOfficeTask(t);
    try {
      audit("task", t.id, "create", "", A.title, `meeting ${m.id}`);
    } catch (e) {}
    stamp("created", "", A.title, out.key);
    t.assignee && stamp("owner", "", t.assignee, out.key);
  } else if ("decision" === pr.kind) {
    const p = mrvProj(A.projectId);
    if (p) {
      p.decisions = p.decisions || [];
      p.decisions.push({ id: uid("dc"), name: A.name, owner: A.owner || "SmartDesign", due: A.made ? m.date : iso(addDays(parse(m.date || today()), 7)), status: A.made ? "made" : "open", madeAt: A.made ? m.date : "", kind: "general", notes: `${A.note}${pr.ts ? ` (${pr.ts})` : ""}` });
    } else out.key = mrvOfficeTask({ id: uid("a"), title: `${A.made ? "Decided" : "Decide"}: ${A.name}`, assignee: mrvWho(A.owner) || "", due: A.made ? m.date : iso(addDays(parse(m.date || today()), 7)), priority: "med", status: A.made ? "done" : "todo", completedAt: A.made ? m.date : "", notes: A.note, link: null, source: { kind: "meeting", id: m.id, label: `Meeting · ${m.title} · ${fmtL(m.date)}`, ts: pr.ts || "" }, createdAt: today() });
    try {
      audit("meeting", m.id, "decision", "", A.name, A.made ? "made" : "to discuss");
    } catch (e) {}
    stamp("decision", "", A.name, "");
  } else if ("event" === pr.kind) {
    // a follow-up meeting to set up: a task for its owner, on the job or the office's list, with the day and time said
    const p = mrvProj(A.projectId),
      hm = /^(\d{2}):(\d{2})$/.exec(A.time || ""),
      at = hm ? ` at ${+hm[1] % 12 || 12}:${hm[2]} ${+hm[1] >= 12 ? "PM" : "AM"}` : "",
      t = { id: uid("a"), title: `Set up ${A.title.replace(/^(a|the) /i, "the ")}${A.due ? ` for ${fmtL(A.due)}` : ""}${at}`, assignee: mrvWho(A.owner), due: A.due ? iso(addDays(parse(A.due), -1)) < today() ? today() : iso(addDays(parse(A.due), -1)) : "", time: A.time || "", priority: "med", status: "todo", link: null, notes: `From ${src}`, meeting: !0, source: { kind: "meeting", id: m.id, label: `Meeting · ${m.title} · ${fmtL(m.date)}`, ts: pr.ts || "" }, createdAt: today(), completedAt: "" };
    p ? ((p.actions = p.actions || []).push(t), (out.key = t2Key({ kind: "action", id: t.id, projectId: p.id }))) : (out.key = mrvOfficeTask(t));
    try {
      audit("task", t.id, "create", "", t.title, `meeting ${m.id}`);
    } catch (e) {}
    stamp("created", "", t.title, out.key);
  } else if ("project" === pr.kind) {
    if ("function" != typeof blankProject) return { ok: !1, why: ["project"] };
    const np = blankProject(A.name, "", today(), "");
    np.project.scopeUnset = !0;
    np.project.createdFrom = "meeting";
    A.prefix && (np.project.prefix = A.prefix);
    DB.projects.includes(np) || DB.projects.push(np);
    out.projectId = np.id;
    // the new job's open items from this meeting land on it
    m.proposals.forEach((q) => q.review && "proposed" === q.status && (mrvNeeds(q).includes("project") || !q.apply.projectId) && MRV.sim(`${q.title}`, A.name) >= 0.5 && (q.apply.projectId = np.id));
    try {
      audit("project", np.id, "create", "", A.name, `meeting ${m.id}`);
    } catch (e) {}
  }
  pr.status = "applied";
  pr.appliedAt = today();
  pr.by = me.name || "";
  pr.result = out;
  try {
    audit("meeting", m.id, "apply", pr.kind, pr.title, pr.ts ? `transcript ${pr.ts}` : "notes");
  } catch (e) {}
  return out;
}
// the review's own items are kept out of the older apply paths
if ("function" == typeof mtApply) {
  const base = mtApply;
  mtApply = function (m, pr) {
    // the transcript's items are applied from the Meeting Review only (Approve All on the record, and the
    // auto-apply settings, never reach them)
    if (pr && pr.review) return null;
    return base.apply(this, arguments);
  };
}
// Re-Read on the meeting record keeps the review's items (they are read from the transcript, not the notes)
if ("function" == typeof mtReplay) {
  const base = mtReplay;
  mtReplay = function (m) {
    const R = (m.proposals || []).filter((p) => p.review);
    const r = base.apply(this, arguments);
    R.forEach((p) => m.proposals.some((q) => q.id === p.id) || m.proposals.push(p));
    return r;
  };
}
// ---- running a review: read, match, reconcile; the model's read is used when there is one ---------------------
function mrvRun(m, opts) {
  const o = opts || {};
  if (!mrvTextOf(m)) return null;
  const r = mrvBuild(m, o);
  save();
  return r;
}
// meetings whose transcript arrived (from the server or another device) and whose review is not built yet: built
// on the device of someone who may read the transcript and approve it
function mrvSweep() {
  try {
    mrvInit();
    if ("function" == typeof mtCanApprove && !mtCanApprove()) return 0;
    let n = 0;
    (DB.meetings || []).forEach((m) => {
      const R = m.review;
      if (!R || !mrvCanRead(m)) return;
      const stale = "reading" === R.state && R.at && Date.now() - new Date(R.at).getTime() > 20 * 60 * 1e3;
      if ("new" === R.state || stale) mrvBuild(m), n++;
    });
    n && save();
    return n;
  } catch (e) {
    console.warn("meeting review", e);
    return 0;
  }
}
// ---- the screen -----------------------------------------------------------------------------------------------
Object.assign(MT_KIND, { tkdate: "New Date", tkdone: "Done", tknote: "Note", tkowner: "Reassign", tkwait: "Waiting On", tktrack: "Track Until", money: "Money", project: "New Project" });
const mrvReview = (m) => (m.proposals || []).filter((p) => p.review);
const mrvWaiting = (m) => mrvReview(m).filter((p) => "proposed" === p.status);
// the link to the Gemini doc at the line's heading (the server records each heading's link; a paste has the doc)
function mrvDocLink(m, pr) {
  const T = mrvTextOf(m),
    base = (T && T.url) || (m.doc && m.doc.url) || m.docUrl || "";
  const h = (T && T.links && (T.links[pr.head] || T.links[pr.ts])) || "";
  if (/^https?:/.test(h)) return h;
  if (!base) return "";
  return h && /^#/.test(h) ? base.replace(/#.*$/, "") + h : base;
}
function mrvQuote(m, pr) {
  if (pr.quote) return { text: pr.quote, who: "Gemini's notes", ts: "" };
  const T = mrvTextOf(m);
  if (!T || pr.line < 0 || !T.lines[pr.line]) return null;
  if (!mrvCanRead(m)) return { hidden: !0, ts: pr.ts };
  const l = T.lines[pr.line];
  return { text: MRV.clean(l.text, 320), who: l.speaker, ts: l.ts };
}
const MRV_IC = {
  doc: '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/><path d="M9.5 12h6M9.5 15.5h6"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
};
const mrvSvg = (k) => `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${MRV_IC[k]}</svg>`;
function mrvOwnerSel(pr) {
  const A = pr.apply || {},
    cur = mrvWho(A.assignee || A.owner || ""),
    staff = mrvStaff();
  return `<label class="mrv-pick"><span>Owner</span><select data-mrvowner="${esc(pr.id)}" aria-label="Owner on the team"><option value="">Pick the owner</option>${staff.map((n) => `<option ${n === cur ? "selected" : ""}>${esc(n)}</option>`).join("")}</select></label>`;
}
function mrvProjSel(pr) {
  const A = pr.apply || {};
  return `<label class="mrv-pick"><span>Project</span><select data-mrvproj="${esc(pr.id)}" aria-label="Project"><option value="">Pick the project</option>${(DB.projects || []).map((p) => `<option value="${p.id}" ${p.id === A.projectId ? "selected" : ""}>${esc(mrvPName(p))}</option>`).join("")}<option value="__office" ${A.office ? "selected" : ""}>Office, no job</option></select></label>`;
}
function mrvTaskSel(pr) {
  const L = mrvTasks().filter((t) => !t.x.done && (!pr.projectId || t.x.projectId === pr.projectId));
  return `<label class="mrv-pick"><span>Task</span><select data-mrvtask="${esc(pr.id)}" aria-label="Task it is about"><option value="">Pick the task</option>${L.slice(0, 120).map((t) => `<option value="${esc(t.key)}">${esc(`${t.ref ? t.ref + " · " : ""}${t.x.title}${t.x.project ? ` (${t.x.project})` : ""}`)}</option>`).join("")}</select></label>`;
}
function mrvItemHtml(m, pr, can) {
  const q = mrvQuote(m, pr),
    link = mrvDocLink(m, pr),
    need = "proposed" === pr.status ? mrvNeeds(pr) : [],
    st = pr.status;
  const quote = q
    ? q.hidden
      ? `<div class="mrv-q muted small">Said at ${esc(q.ts)}; the transcript is the attendees' to read.</div>`
      : `<blockquote class="mrv-q"><span>“${esc(q.text)}”</span><cite>${esc(q.who || "")}${q.ts ? ` · ${esc(q.ts)}${pr.at ? ` (${esc(pr.at.slice(0, 5))})` : ""}` : ""}${link ? ` · <a href="${esc(link)}" target="_blank" rel="noopener" class="mrv-doc">${mrvSvg("doc")}Open in the Doc</a>` : ""}</cite></blockquote>`
    : "";
  const how = { id: "matched by the ID said", screen: "on screen when it was said", said: "the task named just before", words: "matched by its words" }[pr.how] || "";
  const state = "live" === st ? `<div class="small ok">${mrvSvg("check")} Entered live${pr.liveBy ? ` by ${esc(pr.liveBy)}` : ""}${pr.liveAt ? ` at ${esc(String(pr.liveAt).slice(11, 16))}` : ""}: nothing to do</div>` : "board" === st ? `<div class="small muted">Already so on the board: ${esc(pr.boardWhy || "")}</div>` : "applied" === st ? `<div class="small ok">${mrvSvg("check")} Applied ${fmtL(pr.appliedAt)}${pr.by ? ` by ${esc(pr.by)}` : ""}</div>` : "skipped" === st ? `<div class="small muted">Rejected${pr.by ? ` by ${esc(pr.by)}` : ""}</div>` : "";
  const picks = need.length || ("proposed" === st && pr.confirm) ? `<div class="mrv-picks">${need.includes("task") ? mrvTaskSel(pr) : ""}${need.includes("project") ? mrvProjSel(pr) : ""}${need.includes("owner") || pr.confirm ? mrvOwnerSel(pr) : ""}${need.includes("date") ? `<label class="mrv-pick"><span>Date</span><input type="date" data-mrvdate="${esc(pr.id)}" aria-label="Date"></label>` : ""}</div>` : "";
  const chk = "proposed" === st && pr.confirm ? `<div class="small warn mrv-chk">Check the owner: ${esc(pr.confirm.label)} and ${esc(pr.confirm.with)} shared a device, so this line may be either's. Accept All leaves it for you.</div>` : "",
    spkNeed = need.includes("speaker") ? `<div class="small warn mrv-chk">Who is speaking is not known yet: say who above, or pick the owner here.</div>` : "";
  const acts = "proposed" === st && can ? `<div class="mrv-a"><button class="btn sm" data-mrvok="${esc(pr.id)}" ${need.length ? "disabled" : ""} title="${need.length ? `Pick the ${need.filter((n) => "speaker" !== n).join(" and the ") || "owner"} first` : "Apply it to the board"}">Accept</button><button class="btn sm ghost" data-mrvedit="${esc(pr.id)}">Edit</button><button class="btn sm ghost" data-mrvno="${esc(pr.id)}">Reject</button></div>` : "";
  return `<div class="mrv-it ${esc(st)}" data-mrvit="${esc(pr.id)}" data-os-keep="1"><div class="mrv-hd"><span class="mrv-k">${esc(MT_KIND[pr.kind] || pr.kind)}</span><b>${esc(pr.title)}</b></div>${pr.detail ? `<div class="small mrv-d">${esc(pr.detail)}${how && "proposed" === st ? ` <span class="muted">· ${esc(how)}</span>` : ""}</div>` : ""}${quote}${state}${chk}${spkNeed}${picks}${acts}</div>`;
}
// Who Is Speaking: every label in this meeting's transcript, the unknown ones first and open; one answer is kept for
// the workspace (a dial-in number or a guest is asked once, then remembered)
function mrvSpeakersHtml(m, can) {
  const T = mrvTextOf(m);
  if (!T || !(T.speakers || []).length) return "";
  const L = T.speakers.map((lab) => ({ lab: lab, s: mrvSpeakerOf(m, lab), line: mrvCanRead(m) ? (T.lines || []).find((l) => l.speaker === lab) : null })),
    unk = L.filter((x) => x.s.unknown),
    staff = (DB.users || []).filter((u) => u.name && !/^(client|mb_user|mb_analyst)$/.test(u.role || ""));
  const row = (x) => `<div class="mrv-spk"><div class="mrv-spk-l"><b>${esc(x.lab)}</b>${x.line ? `<span class="small muted">“${esc(MRV.clean(x.line.text, 90))}”</span>` : ""}</div>${can ? `<label class="mrv-pick"><span>Is</span><select data-mrvspk="${esc(x.lab)}" aria-label="Who ${esc(x.lab)} is"><option value="">${x.s.unknown ? "Who is this?" : ""}</option>${staff.map((u) => `<option value="${u.id}" ${x.s.uid === u.id || x.s.name === u.name ? "selected" : ""}>${esc(u.name)}</option>`).join("")}<option value="__out" ${x.s.outside ? "selected" : ""}>Someone outside the team</option></select></label>` : `<span class="small">${esc(x.s.name || (x.s.outside ? "outside the team" : "not known yet"))}</span>`}</div>`;
  const shared = (m.sharedDevice || []).length ? `<div class="note warn mrv-shared">Some speakers shared a device; owners from their lines need a check: ${(m.sharedDevice || []).map((d) => `${esc(d.with)} spoke on ${esc(d.label)}'s line`).join("; ")}.</div>` : "";
  return `${shared}${unk.length ? `<section class="mrv-g mrv-spks"><h3>Who Is Speaking <span class="muted small">${unk.length} not known</span></h3>${unk.map(row).join("")}</section>` : ""}<details class="mrv-g mrv-spks-all"><summary class="small">Speakers: ${L.filter((x) => !x.s.unknown).map((x) => `${esc(x.lab)} is ${esc(x.s.name || "outside the team")}`).join(" · ") || "none known"}</summary>${L.filter((x) => !x.s.unknown).map(row).join("")}</details>`;
}
function mrvHtml(m) {
  const all = mrvReview(m),
    can = "function" == typeof mtCanApprove ? mtCanApprove() : !1,
    R = m.review || {},
    open = all.filter((p) => "proposed" === p.status),
    ready = open.filter((p) => !mrvNeeds(p).length && !p.confirm),
    waitPick = open.filter((p) => mrvNeeds(p).length),
    done = all.filter((p) => "proposed" !== p.status),
    order = [];
  mrvScreenLog(m).forEach((e) => {
    const t = mrvFind(e.taskKey);
    t && !order.includes(t.x.projectId || "") && order.push(t.x.projectId || "");
  });
  const groups = {};
  open.forEach((p) => {
    const k = mrvNeeds(p).includes("project") || mrvNeeds(p).includes("task") ? "__pick" : p.apply.office || !p.projectId && !p.apply.projectId ? "__office" : p.projectId || p.apply.projectId;
    (groups[k] = groups[k] || []).push(p);
  });
  const keys = Object.keys(groups).sort((a, b) => (a === "__pick" ? -1 : b === "__pick" ? 1 : a === "__office" ? 1 : b === "__office" ? -1 : (order.indexOf(a) < 0 ? 99 : order.indexOf(a)) - (order.indexOf(b) < 0 ? 99 : order.indexOf(b)) || mrvPName(mrvProj(a)).localeCompare(mrvPName(mrvProj(b)))));
  const gname = (k) => ("__pick" === k ? "Needs a Project or a Task" : "__office" === k ? "Office, No Job" : mrvPName(mrvProj(k)) || "Project");
  const why = "function" == typeof standardWhy ? standardWhy({ src: "meetreview" }) : "";
  const link = (m.doc && m.doc.url) || m.docUrl || "";
  const reading = "reading" === R.state;
  return `<div class="crumb"><a href="#" data-mtback>Meetings</a><span>›</span>${esc(m.title)}</div>
  <div class="ph mrv-ph"><div><h2 data-ia-keep="1">Meeting Review</h2><div class="lead">${esc(m.title)} · ${fmtL(m.date)} · ${open.length} to review${waitPick.length ? `, ${waitPick.length} waiting for a pick` : ""}${R.by ? ` · read ${"model" === R.by ? "by the assistant" : "by the rules"} from the whole transcript` : ""}</div></div>
  <div class="acts">${ready.length && can ? `<button class="btn primary" id="mrv-all">Accept All · ${ready.length}</button>` : ""}<button class="btn" id="mrv-record">Meeting Record</button>${link ? `<a class="btn" href="${esc(link)}" target="_blank" rel="noopener">Open the Doc</a>` : ""}${can && "function" == typeof ai && "function" == typeof aiReady && aiReady() && mrvCanRead(m) && "model" !== R.by ? '<button class="btn" id="mrv-ai">Read With the Assistant</button>' : ""}</div></div>
  ${reading ? '<div class="note">The transcript is being read. Its items appear here in a few minutes; nothing changes the board until you accept it.</div>' : ""}
  ${mrvSpeakersHtml(m, can)}
  <div class="small muted mrv-why">Nothing changes the board until it is accepted. Accepted items go to their owners' Today with this meeting as the source.${why ? ` ${esc(why)}.` : ""}</div>
  ${keys.length ? keys.map((k) => `<section class="mrv-g" data-mrvg="${esc(k)}"><h3>${esc(gname(k))} <span class="muted small">${groups[k].length}</span></h3>${groups[k].map((p) => mrvItemHtml(m, p, can)).join("")}</section>`).join("") : `<div class="card"><div class="small">${all.length ? "Everything from this meeting is settled." : reading ? "" : "Nothing in the transcript needs a change on the board."}</div></div>`}
  ${done.length ? `<details class="mrv-g mrv-done" ${mrvShowDone ? "open" : ""}><summary><b>Settled</b> <span class="muted small">${done.filter((p) => "live" === p.status).length} entered live · ${done.filter((p) => "board" === p.status).length} already on the board · ${done.filter((p) => "applied" === p.status).length} applied · ${done.filter((p) => "skipped" === p.status).length} rejected</span></summary>${done.map((p) => mrvItemHtml(m, p, can)).join("")}</details>` : ""}`;
}
// Edit: the fields the item carries, in one sheet
function mrvEdit(m, pr) {
  const A = pr.apply || {},
    staff = mrvStaff(),
    owner = mrvWho(A.assignee || A.owner || ""),
    projOpts = [["", "Pick the project"]].concat((DB.projects || []).map((p) => [p.id, mrvPName(p)]), [["__office", "Office, no job"]]),
    F = [];
  ["task", "event", "decision", "project"].includes(pr.kind) && F.push(mbF("Title", mbIn("title", A.title || A.name || "")));
  ["task", "event", "decision"].includes(pr.kind) && F.push(mbF("Project", mbSel("projectId", projOpts, A.office ? "__office" : A.projectId || "")));
  ["task", "event", "tkowner", "tkwait"].includes(pr.kind) && F.push(mbF("Owner on the Team", mbSel("owner", [["", "Pick the owner"]].concat(staff.map((n) => [n, n])), owner)));
  ["task", "tkwait"].includes(pr.kind) && F.push(mbF("Waiting On (Outside the Team)", mbIn("party", A.party || "", "vendor, consultant or client")));
  ["task", "event", "tkdate"].includes(pr.kind) && F.push(mbF("Date", mbIn("due", A.due || "", "", "date")));
  "tkwait" === pr.kind && F.push(mbF("Promised By", mbIn("by", A.by || "", "", "date")));
  "tktrack" === pr.kind && F.push(mbF("Track Until", mbIn("until", A.until || "", "", "date")));
  ["tknote", "money"].includes(pr.kind) && F.push(mbF("Note", mbIn("text", A.text || "")));
  "project" === pr.kind && F.push(mbF("Prefix", mbIn("prefix", A.prefix || "", "3 letters, e.g. ORC")));
  mbModal(esc(`Edit: ${pr.title}`), F.join(""), {
    submit: "Save",
    onSubmit: (f) => {
      null != f.title && f.title && ("decision" === pr.kind || "project" === pr.kind ? (A.name = f.title) : (A.title = f.title));
      null != f.projectId && ((A.office = "__office" === f.projectId), (A.projectId = "__office" === f.projectId ? "" : f.projectId), (pr.projectId = A.projectId));
      null != f.owner && ("task" === pr.kind ? (A.assignee = f.owner) : (A.owner = f.owner));
      null != f.party && ((A.party = f.party), "task" === pr.kind && (A.waitBy = A.waitBy || A.due || ""));
      null != f.due && (A.due = f.due);
      null != f.by && (A.by = f.by);
      null != f.until && (A.until = f.until);
      null != f.text && f.text && (A.text = f.text);
      null != f.prefix && (A.prefix = f.prefix.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6));
      mrvRetitle(pr);
      pr.edited = { by: mrvMe().name || "", at: appNowIso() };
      save(), render();
      toast(`Edited: ${pr.title}`, [{ label: "Open", run: () => mrvOpen(m.id) }]);
    },
  });
}
function mrvRetitle(pr) {
  const A = pr.apply || {};
  if ("task" === pr.kind) pr.title = A.title;
  if ("event" === pr.kind) pr.title = `Set up: ${A.title}${A.due ? ` · ${fmtL(A.due)}` : ""}${A.time ? ` ${A.time}` : ""}`;
  if ("decision" === pr.kind) pr.title = `${A.made ? "Decided" : "To discuss"}: ${A.name}`;
  if ("project" === pr.kind) pr.title = `New project: ${A.name}`;
  if ("tkdate" === pr.kind) pr.title = `New date: ${A.due ? fmtL(A.due) : "?"}`;
  if ("tkowner" === pr.kind) pr.title = `Reassign to ${A.owner || "someone on the team"}`;
  if ("tktrack" === pr.kind) pr.title = `Track until ${A.until ? fmtL(A.until) : "?"}`;
  if ("tknote" === pr.kind) pr.title = `Note: ${MRV.clean(A.text, 140)}`;
  const R = A.key ? tkResolve(A.key) : null;
  pr.detail = mrvDetail(pr, R ? R.x : null);
}
function mrvOpen(id) {
  mrvOn = id;
  "undefined" != typeof mtTab && (mtTab = "meetings");
  mtOpen = id;
  view = "meetings";
  render();
  window.scrollTo(0, 0);
}
function mrvAccept(m, pr) {
  const r = mrvApply(m, pr);
  if (!r || !r.ok) return toast(`Pick the ${(r && r.why ? r.why : ["owner"]).join(" and the ")} first: ${pr.title}`), r;
  save(), render();
  const key = r.key || pr.taskKey;
  toast(`Applied: ${pr.title}`, [{ label: "Open", run: () => (key && "function" == typeof tkOpen ? tkOpen(key) : r.projectId ? (setCurrent(r.projectId), (view = "dash"), render()) : mrvOpen(m.id)) }]);
}
function mrvAcceptAll(m) {
  const L = mrvWaiting(m).filter((p) => !mrvNeeds(p).length && !p.confirm);
  let n = 0;
  L.filter((p) => "project" === p.kind).concat(L.filter((p) => "project" !== p.kind)).forEach((p) => {
    const r = mrvApply(m, p);
    r && r.ok && n++;
  });
  const left = mrvWaiting(m).length;
  save(), render();
  toast(`Applied ${n} from the meeting${left ? `; ${left} wait for an owner, a project or a task` : ""}`, [{ label: "Open", run: () => mrvOpen(m.id) }]);
  return n;
}
function mrvWire(host, m) {
  const by = (id) => (m.proposals || []).find((p) => p.id === id);
  const q = (s) => host.querySelectorAll(s);
  const all = host.querySelector("#mrv-all");
  all && (all.onclick = () => mrvAcceptAll(m));
  const rec = host.querySelector("#mrv-record");
  rec && (rec.onclick = () => ((mrvOn = ""), render()));
  const aiB = host.querySelector("#mrv-ai");
  aiB &&
    (aiB.onclick = async () => {
      aiB.disabled = !0;
      const x = await mrvAiRead(m);
      if (!x) return (aiB.disabled = !1), toast("The assistant could not read it: the rules' read stays");
      mrvBuild(m), save(), render();
      toast(`Read by the assistant: ${mrvWaiting(m).length} to review`, [{ label: "Open", run: () => mrvOpen(m.id) }]);
    });
  q("[data-mrvok]").forEach((b) => (b.onclick = () => by(b.dataset.mrvok) && mrvAccept(m, by(b.dataset.mrvok))));
  q("[data-mrvedit]").forEach((b) => (b.onclick = () => by(b.dataset.mrvedit) && mrvEdit(m, by(b.dataset.mrvedit))));
  q("[data-mrvno]").forEach(
    (b) =>
      (b.onclick = () => {
        const pr = by(b.dataset.mrvno);
        if (!pr) return;
        Object.assign(pr, { status: "skipped", by: mrvMe().name || "", appliedAt: today() });
        try {
          audit("meeting", m.id, "reject", pr.kind, pr.title, pr.ts || "");
        } catch (e) {}
        save(), render();
        toast(`Rejected: ${pr.title}`, [{ label: "Undo", run: () => ((pr.status = "proposed"), save(), render()) }, { label: "Open", run: () => mrvOpen(m.id) }]);
      }),
  );
  const pickThen = (pr, what) => (save(), render(), toast(`${what}: ${pr.title}`, [{ label: "Open", run: () => mrvOpen(m.id) }]));
  q("[data-mrvowner]").forEach(
    (s) =>
      (s.onchange = () => {
        const pr = by(s.dataset.mrvowner);
        if (!pr || !s.value) return;
        "task" === pr.kind ? (pr.apply.assignee = s.value) : (pr.apply.owner = s.value);
        delete pr.confirm;
        mrvRetitle(pr), pickThen(pr, `Owner ${s.value}`);
      }),
  );
  q("[data-mrvproj]").forEach(
    (s) =>
      (s.onchange = () => {
        const pr = by(s.dataset.mrvproj);
        if (!pr || !s.value) return;
        pr.apply.office = "__office" === s.value;
        pr.apply.projectId = pr.apply.office ? "" : s.value;
        pr.projectId = pr.apply.projectId;
        mrvRetitle(pr), pickThen(pr, pr.apply.office ? "Office, no job" : `On ${mrvPName(mrvProj(s.value))}`);
      }),
  );
  q("[data-mrvtask]").forEach(
    (s) =>
      (s.onchange = () => {
        const pr = by(s.dataset.mrvtask);
        if (!pr || !s.value) return;
        const t = mrvFind(s.value);
        pr.apply.key = s.value;
        pr.taskKey = s.value;
        t && ((pr.ref = t.ref), (pr.projectId = t.x.projectId || ""), "tkwait" === pr.kind && !pr.apply.owner && (pr.apply.owner = mrvWho(t.x.assignee || "")), "tkdate" === pr.kind && (pr.from = t.x.due || ""), "tkowner" === pr.kind && (pr.from = t.x.assignee || ""));
        mrvRetitle(pr), pickThen(pr, `On ${t ? t.x.title : "the task"}`);
      }),
  );
  q("[data-mrvdate]").forEach(
    (s) =>
      (s.onchange = () => {
        const pr = by(s.dataset.mrvdate);
        if (!pr || !s.value) return;
        pr.apply.due = s.value;
        pr.to = s.value;
        mrvRetitle(pr), pickThen(pr, `Date ${fmtL(s.value)}`);
      }),
  );
  q("[data-mrvspk]").forEach(
    (s) =>
      (s.onchange = () => {
        if (!s.value) return;
        const lab = s.dataset.mrvspk;
        mrvSetSpeaker(lab, s.value);
        render();
        const who = "__out" === s.value ? "someone outside the team" : ((DB.users || []).find((u) => u.id === s.value) || {}).name || s.value;
        toast(`${lab} is ${who}, for every meeting from now on: ${mrvWaiting(m).length} to review`, [{ label: "Open", run: () => mrvOpen(m.id) }]);
      }),
  );
  const d = host.querySelector(".mrv-done");
  d && d.addEventListener("toggle", () => (mrvShowDone = d.open));
}
// ---- paste or upload a transcript (the fallback when the Drive watch is off, or the meeting was elsewhere) -----
function mrvPasteSheet(m) {
  const body = `<p class="small muted" style="margin-top:0">Paste the whole "Notes by Gemini" doc, Transcript included, or upload it (.txt or .md; in Google Docs, File, Download, Markdown). The transcript is kept on the meeting for its attendees only.</p>
  <div class="f"><label>The Notes Doc</label><textarea data-f="text" id="mrv-text" rows="8" placeholder="Paste here"></textarea></div>
  <div class="f"><label>Or Upload</label><input type="file" id="mrv-file" accept=".txt,.md,text/plain,text/markdown"></div>
  <div class="f2"><div class="f"><label>Recording Started</label><input data-f="start" type="time" step="1" aria-label="Recording started"></div><div class="f"><label>Doc Link (Optional)</label><input data-f="url" placeholder="https://docs.google.com/document/d/…"></div></div>`;
  const box = mbModal(m ? `Add the Transcript: ${esc(m.title)}` : "Read a Transcript", body, {
    submit: "Read It",
    onSubmit: (f) => {
      const text = f.text || "";
      if (!text.trim()) return toast("Paste the doc or upload it first"), !1;
      const day = (m && m.date) || today();
      const x = mrvIngest(text, { meetingId: m ? m.id : "", source: "paste", url: f.url || "", start: f.start ? `${day}T${f.start.length === 5 ? f.start + ":00" : f.start}` : "" });
      if (!x) return !1;
      mrvRun(x);
      setTimeout(() => {
        mrvOpen(x.id);
        toast(`Read ${mrvTextOf(x).lines.length} lines: ${mrvWaiting(x).length} to review`, [{ label: "Open", run: () => mrvOpen(x.id) }]);
      }, 0);
      return !0;
    },
  });
  const fi = box && box.querySelector("#mrv-file");
  fi &&
    (fi.onchange = () => {
      const file = fi.files && fi.files[0];
      if (!file) return;
      const r = new FileReader();
      r.onload = () => {
        const ta = box.querySelector("#mrv-text");
        ta && (ta.value = String(r.result || ""));
      };
      r.readAsText(file);
    });
}
// ---- settings: the recurring meeting's Drive folder the server watches (the owner sets it) -----------------------
function mrvWatchHtml() {
  mrvInit();
  const W = DB.company.meetWatch,
    owner = "owner" === role(),
    staff = (DB.users || []).filter((u) => !/^(client|mb_user|mb_analyst|crew|driver|foreman)$/.test(u.role || ""));
  return `<div class="card mrv-watch" style="margin-top:12px"><div class="hd"><h3>Team Meeting Transcripts</h3></div>
  <p class="small muted" style="margin-top:0">The server reads each new "Notes by Gemini" doc in the recurring meeting's Drive folder, through the organiser's Google connection (Settings, Connections, Keep Watching), and the meeting's owner gets the Meeting Review on Today, usually within 15 minutes of the call. It reads that folder only. The transcript stays on the meeting, for its attendees.</p>
  ${W.length ? W.map((w) => `<div class="mrv-w"><b>${esc(w.name || "Team meeting")}</b><span class="small muted">folder ${esc(w.folder)} · organiser ${esc(((DB.users || []).find((u) => u.id === w.organizerUid) || {}).name || "?")} · reviewed by ${esc(((DB.users || []).find((u) => u.id === w.ownerUid) || {}).name || "?")}${w.on === !1 ? " · paused" : ""}</span>${owner ? `<button class="btn sm ghost" data-mrvwoff="${esc(w.id)}">${w.on === !1 ? "Resume" : "Pause"}</button>` : ""}</div>`).join("") : '<div class="small muted">No meeting folder is watched yet.</div>'}
  ${owner ? `<div class="f2" style="margin-top:8px"><div class="f"><label>Meeting Name</label><input id="mrvw-name" placeholder="Weekly Jobs"></div><div class="f"><label>Drive Folder Link</label><input id="mrvw-folder" placeholder="https://drive.google.com/drive/folders/…"></div></div>
  <div class="f2"><div class="f"><label>Organiser (Their Google)</label><select id="mrvw-org">${staff.map((u) => `<option value="${u.id}">${esc(u.name)}</option>`).join("")}</select></div><div class="f"><label>Reviewed By</label><select id="mrvw-own">${staff.map((u) => `<option value="${u.id}" ${"coord" === u.role ? "selected" : ""}>${esc(u.name)}</option>`).join("")}</select></div></div>
  <button class="btn" id="mrvw-add">Watch This Folder</button>` : '<div class="small muted">The owner sets which folder is watched.</div>'}</div>`;
}
const mrvFolderId = (s) => (String(s || "").match(/folders\/([A-Za-z0-9_-]{10,})/) || String(s || "").match(/^([A-Za-z0-9_-]{10,})$/) || [])[1] || "";
function mrvWatchWire(host) {
  const add = host.querySelector("#mrvw-add");
  add &&
    (add.onclick = () => {
      const v = (s) => ((host.querySelector(s) || {}).value || "").trim(),
        folder = mrvFolderId(v("#mrvw-folder"));
      if (!folder) return toast("Paste the Drive folder's link");
      const w = { id: uid("mw"), name: v("#mrvw-name") || "Team meeting", folder: folder, organizerUid: v("#mrvw-org"), ownerUid: v("#mrvw-own"), on: !0, by: mrvMe().name || "", at: appNowIso() };
      DB.company.meetWatch.push(w);
      try {
        audit("company", w.id, "meetWatch", "", `${w.name} · ${w.folder}`, "");
      } catch (e) {}
      save(), render();
      toast(`Watching ${w.name}'s folder: new notes docs become a Meeting Review`, [{ label: "Open", run: () => ((mtTab = "settings"), (view = "meetings"), render()) }]);
    });
  host.querySelectorAll("[data-mrvwoff]").forEach(
    (b) =>
      (b.onclick = () => {
        const w = DB.company.meetWatch.find((x) => x.id === b.dataset.mrvwoff);
        if (!w) return;
        w.on = w.on === !1;
        save(), render();
        toast(`${w.name}: ${w.on ? "watching again" : "paused"}`, [{ label: "Open", run: () => ((mtTab = "settings"), (view = "meetings"), render()) }]);
      }),
  );
}
// ---- wiring into the meetings screen, Approvals, Today ------------------------------------------------------------
if ("function" == typeof mtMeetingHtml) {
  const base = mtMeetingHtml;
  mtMeetingHtml = function (m) {
    if (m && mrvOn === m.id && m.review) return mrvHtml(m);
    // the record lists the notes' own proposals; the transcript's are on the review
    const keep = m.proposals;
    let h;
    try {
      m.proposals = (keep || []).filter((p) => !p.review);
      h = base.apply(this, arguments);
    } finally {
      m.proposals = keep;
    }
    const w = m.review ? mrvWaiting(m).length : 0;
    const card = m.review
      ? `<div class="card mrv-card"><div class="hd"><h3>Meeting Review</h3><span class="grow"></span><button class="btn sm" data-mrvopen="${esc(m.id)}">Open the Review</button></div><div class="small">${w ? `${w} item${1 === w ? "" : "s"} from the transcript to review` : "Everything from the transcript is settled"} · ${mrvReview(m).filter((p) => "live" === p.status).length} entered live</div></div>`
      : `<div class="card mrv-card"><div class="hd"><h3>Transcript</h3><span class="grow"></span><button class="btn sm" data-mrvpaste="${esc(m.id)}">Add the Transcript</button></div><div class="small muted">With the transcript, everything said and not entered becomes a review for the meeting's owner.</div></div>`;
    return h.replace('<div class="grid2">', card + '<div class="grid2">');
  };
}
if ("function" == typeof mtWire) {
  const base = mtWire;
  mtWire = function (host) {
    const m = mrvOn && (DB.meetings || []).find((x) => x.id === mrvOn);
    if (m && m.review && host.querySelector(".mrv-ph")) {
      const back = host.querySelector("[data-mtback]");
      back && (back.onclick = (e) => (e.preventDefault(), (mrvOn = ""), (mtOpen = ""), render()));
      host.querySelectorAll("[data-mttab]").forEach((b) => (b.onclick = () => ((mtTab = b.dataset.mttab), (mtOpen = ""), (mrvOn = ""), render())));
      return mrvWire(host, m);
    }
    base.apply(this, arguments);
    host.querySelectorAll("[data-mrvopen]").forEach((b) => (b.onclick = () => mrvOpen(b.dataset.mrvopen)));
    host.querySelectorAll("[data-mrvpaste]").forEach((b) => (b.onclick = () => mrvPasteSheet((DB.meetings || []).find((x) => x.id === b.dataset.mrvpaste))));
    const rd = host.querySelector("#mrv-read");
    rd && (rd.onclick = () => mrvPasteSheet(null));
    mrvWatchWire(host);
  };
}
if ("function" == typeof mtSettingsHtml) {
  const base = mtSettingsHtml;
  mtSettingsHtml = function () {
    return base.apply(this, arguments) + mrvWatchHtml();
  };
}
if ("function" == typeof renderMeetings) {
  const base = renderMeetings;
  renderMeetings = function () {
    mrvSweep();
    mrvOn && !(DB.meetings || []).some((x) => x.id === mrvOn && x.review) && (mrvOn = "");
    const r = base.apply(this, arguments);
    try {
      const host = document.getElementById("meetings-body"),
        row = host && !mtOpen && "meetings" === mtTab ? host.querySelector("#mt-paste") : null;
      row && !host.querySelector("#mrv-read") && (row.insertAdjacentHTML("beforebegin", '<button class="btn" id="mrv-read">Read a Transcript</button>'), (host.querySelector("#mrv-read").onclick = () => mrvPasteSheet(null)));
    } catch (e) {}
    return r;
  };
}
// a pasted notes doc with a transcript is read the same way, and its words leave the shared record
if ("function" == typeof mtParseDoc) {
  const base = mtParseDoc;
  mtParseDoc = function (md, m) {
    const r = base.apply(this, arguments);
    try {
      if (m && m.id && (DB.meetings || []).includes(m) && /transcript/i.test(String(md || "")) && MRV.parseDoc(md).lines.length) {
        mrvIngest(md, { meetingId: m.id, source: "paste", url: m.docUrl || "" });
        mrvRun(m);
      }
    } catch (e) {
      console.warn("meeting review", e);
    }
    return r;
  };
}
// the deep read (meetread) reads the attendees' transcript where this person may read it
if ("function" == typeof mrRead) {
  const base = mrRead;
  mrRead = async function (m) {
    const T = mrvTextOf(m),
      lend = m && !m.transcript && T && mrvCanRead(m);
    lend && (m.transcript = T.text);
    try {
      return await base.apply(this, arguments);
    } finally {
      lend && delete m.transcript;
    }
  };
  "function" == typeof bnDeepRead && (bnDeepRead = (m) => mrRead(m));
}
if ("function" == typeof mGo) {
  const base = mGo;
  mGo = function (go) {
    go && "meetings" === go.view && (mrvOn = go.review ? go.meeting || "" : "");
    return base.apply(this, arguments);
  };
}
// a review keeps the board's dates and owners true: the schedule principle, and the value that closes every loop
// on the meeting's day and the next, an unreviewed meeting leaves teammates reading a board the room already changed
// (integrity: we never mislead a teammate); after that it is the board's dates (schedule)
"undefined" != typeof STD_MAP &&
  (STD_MAP.meetreview = {
    p: (it) => {
      const m = (DB.meetings || []).find((x) => x.id === it.id);
      return m && m.date && m.date >= iso(addDays(parse(today()), -1)) ? "integrity" : "schedule";
    },
    c: ["value", "own", /Close every loop/i],
  });
// one item per meeting in Approvals, for the meeting's owner: a review reads as one
if ("function" == typeof mApprovals) {
  const base = mApprovals;
  mApprovals = function () {
    const out = base.apply(this, arguments);
    try {
      (Array.isArray(out) ? out : []).forEach((it) => {
        if ("meeting" !== it.kind) return;
        const m = (DB.meetings || []).find((x) => x.id === it.id);
        if (!m || !m.review) return;
        const w = mrvWaiting(m),
          other = (m.proposals || []).filter((p) => !p.review && "proposed" === p.status).length,
          P = new Set(w.map((p) => p.apply.projectId || p.projectId || "office"));
        it.title = `Meeting Review · ${m.title} · ${fmtL(m.date)}`;
        it.detail = `${w.length} from the transcript${other ? ` and ${other} from the notes` : ""} · ${P.size} project${1 === P.size ? "" : "s"} · nothing changes until you accept`;
        it.n = String(w.length + other);
        it.yes = "Review";
        it.review = !0;
        it.due = m.date || ""; // reviewed the day of the meeting (the Standard: close every loop)
        it.src = "meetreview"; // ranked by the Standard as the board's dates and owners (schedule), not as housekeeping
        it.open = { view: "meetings", meeting: m.id, review: !0 };
      });
    } catch (e) {}
    return out;
  };
}
// the meeting's owner approves its review (the coordinator who runs it), then the rule as before
if ("undefined" != typeof DELEGATION && DELEGATION.meeting) {
  const base = DELEGATION.meeting.who;
  DELEGATION.meeting.rule = "a meeting's review goes to the meeting's owner (the person who runs it); other proposals from a meeting go to someone who was in it and can approve here: the PM, then the coordinator, then the owner";
  DELEGATION.meeting.who = (it) => {
    const m = (DB.meetings || []).find((x) => x.id === it.id),
      u = m && m.review && m.owner && (DB.users || []).find((x) => x.id === m.owner.uid);
    if (u && ["owner", "pm", "coord", "billing", "controller"].includes(u.role)) return u.role;
    return base ? base(it) : "";
  };
}
if ("function" == typeof tdCard) {
  const base = tdCard;
  tdCard = function (it) {
    const c = base.apply(this, arguments);
    try {
      if (it && "meeting" === it.kind && it.review) {
        const m = (DB.meetings || []).find((x) => x.id === it.id);
        if (m) {
          const w = mrvWaiting(m),
            P = new Set(w.map((p) => p.apply.projectId || p.projectId || "office"));
          c.line1 = `<a href="#" data-tdrec>Meeting Review</a> · ${esc(m.title)}`;
          c.why = esc(`${w.length} to review from ${fmtL(m.date)} · ${P.size} project${1 === P.size ? "" : "s"}`);
          c.verb = "Review";
          c.run = c.go = () => mrvOpen(m.id);
        }
      }
    } catch (e) {}
    return c;
  };
}
if ("function" == typeof tdScore) {
  const base = tdScore;
  tdScore = function (it) {
    if (it && "meeting" === it.kind && it.review) {
      const m = (DB.meetings || []).find((x) => x.id === it.id),
        age = m && m.date ? Math.max(0, (parse(today()) - parse(m.date)) / 864e5) : 9;
      return (age <= 2 ? 36 : 22) + ("warn" === it.sev ? 2 : 0);
    }
    return base.apply(this, arguments);
  };
}
// built before Today draws, so the card is there the first time the owner looks
if ("function" == typeof renderHome) {
  const base = renderHome;
  renderHome = function () {
    mrvSweep();
    return base.apply(this, arguments);
  };
}
if ("function" == typeof finishBoot) {
  const base = finishBoot;
  finishBoot = function () {
    const r = base.apply(this, arguments);
    try {
      mrvSweep();
    } catch (e) {}
    return r;
  };
}
