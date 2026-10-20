/* =========================================================================================================
   loop (lane "loop", 2026-10-20): the improvement loop (BACKLOG §1.19) and the Brain's own jobs (§1.32 items 1,
   3, 4, 5). Rides after reports.js and before items.js (build.py SRC), so its wrappers sit inside the item library's
   and the Spanish pass's. The rules are LOOP_CORE (src/loop_core.js, shared with the server's nightly run).

   1. Signals in (DB.signals, the one new store; review/loop/audit.md says why). A problem report from any screen
      (rpPut, the existing Report a Problem; now synced, so it reaches the owner from a phone on the hosted copy),
      with the record that was open; a day's usage counts per person (exports to Excel, the same words typed
      again, a trip away and straight back, a form typed in and left, repeated taps), counts and screens only;
      a Standard Watch day per rule; a lesson that keeps firing after its approval; an agent's or a workshop's
      findings (lpImportFindings).
   2. The brain triages (lpTriage): LOOP_CORE groups the signals into one problem each, ranks them by the Standard's
      decision principles, then someone stuck, then people hurt and how often, and words the proposal (what is
      wrong, the evidence, the fix, the risk, how it is checked). The assistant rewords it through the platform's
      door when it is there (lpReword); the rules' wording stands without it.
   3. The owner approves in the one list, Meetings › Changes (DB.changes, source "loop"): a rule applies on approval
      with its from and to on the audit trail and an Undo; a change to the ERP becomes a build ticket (the evidence
      and the acceptance test, copied as a GitHub issue body; nothing is opened on GitHub).
   4. Close the loop: the people who reported it get the answer on their report and a Today task "See what changed";
      a month after it went live the loop compares the signals before and after and reopens it if it did not stop
      (a repeat). "Still Wrong" on a fixed report reopens it at once.
   5. Measured: found against fixed, time to fix, repeats, on the Changes tab and in Ask; EQ_TABLES improvements and
      signals.
--------------------------------------------------------------------------------------------------------- */
const LP = LOOP_CORE;
const lpOwner = () => {
  try {
    return "owner" === role();
  } catch (e) {
    return !1;
  }
};
const lpMe = () => {
  try {
    return currentUser() || {};
  } catch (e) {
    return {};
  }
};
function lpInit() {
  DB.signals = Array.isArray(DB.signals) ? DB.signals : [];
  DB.changes = Array.isArray(DB.changes) ? DB.changes : [];
  DB.company = DB.company || {};
  DB.company.loopWatch = DB.company.loopWatch || {};
  return DB.signals;
}
// a page's name as the menu says it (the view id when nothing names it)
function lpScreen(v) {
  const k = String(v || "");
  try {
    if ("object" == typeof NAV_LABELS && NAV_LABELS[k]) return NAV_LABELS[k];
  } catch (e) {}
  try {
    if ("object" == typeof IA_LABELS && IA_LABELS[k]) return IA_LABELS[k];
  } catch (e) {}
  return k;
}
const lpNames = () => ({ screen: lpScreen, date: (d) => (d ? fmtL(d) : "") });
const lpOrder = () => {
  try {
    const P = (standard().principles || []).map((p) => p.id).filter(Boolean);
    return P.length ? P : LP.PRINCIPLES;
  } catch (e) {
    return LP.PRINCIPLES;
  }
};
const lpPWord = (p) => {
  try {
    const x = (standard().principles || []).find((y) => y.id === p);
    if (x && x.name) return x.name;
  } catch (e) {}
  return LP.P_WORDS[p] || "No principle named";
};
// Keep the store bounded: 120 days of signals (the loop reads 90; the month-later check reads 60).
function lpPrune() {
  const cut = LP.addDays(today(), -120);
  DB.signals = lpInit().filter((s) => s && String(s.day || "") >= cut);
}
function lpAdd(sig) {
  const S = lpInit();
  if (!sig || !sig.id) return null;
  const i = S.findIndex((x) => x.id === sig.id);
  i >= 0 ? (S[i] = Object.assign(S[i], sig)) : S.push(sig);
  return sig;
}

// ---- 1a. problem reports: the existing button, now a shared signal with the record that was open --------------
// rpContext adds the record on screen (ids only: the job, the client, the document, the order, the vendor, the editor).
if ("function" == typeof rpContext) {
  const base = rpContext;
  rpContext = function () {
    const c = base.apply(this, arguments);
    try {
      const rec = {};
      "undefined" != typeof S && S && S.id && (rec.projectId = S.id);
      "undefined" != typeof clientOpen && clientOpen && (rec.clientId = clientOpen);
      "undefined" != typeof docOpen && docOpen && (rec.docId = "object" == typeof docOpen ? docOpen.id || "" : docOpen);
      "undefined" != typeof poOpen && poOpen && (rec.poId = "object" == typeof poOpen ? poOpen.id || "" : poOpen);
      "undefined" != typeof vendOpen && vendOpen && (rec.vendorId = "object" == typeof vendOpen ? vendOpen.id || "" : vendOpen);
      "undefined" != typeof editing && editing && editing.kind && (rec.editing = `${editing.kind}${editing.id ? ":" + editing.id : ""}`);
      c.rec = rec;
    } catch (e) {}
    return c;
  };
}
// the report as a signal: everything but the picture (a picture stays on the reporter's device)
function lpReportSignal(r) {
  const me = lpMe();
  return {
    id: "rp:" + r.id,
    kind: "report",
    at: r.at,
    day: today(),
    uid: r.by ? me.id || "" : "",
    role: r.role || "",
    screen: r.screen || "",
    label: r.screenTitle || lpScreen(r.screen),
    what: r.what || "other",
    sev: r.bad || "",
    // rpScrub took names on file, amounts, emails, long numbers and full phone numbers; short ones go too
    text: [r.text, r.expect ? "Expected: " + r.expect : ""].filter(Boolean).join(" ").replace(/\b\d{3}[ .-]\d{4}\b/g, "[phone]").slice(0, 1200),
    rec: r.rec || null,
    errors: (r.errors || []).slice(-3).map((e) => ({ m: String(e.m || "").slice(0, 140), at: e.at || "" })),
    trail: (r.trail || []).slice(-8).map((x) => ({ kind: x.kind, what: x.what, where: x.where })),
    rep: Object.assign({}, r, { photo: r.photo ? "(on the reporter's device)" : "" }),
  };
}
if ("function" == typeof rpPut) {
  const base = rpPut;
  rpPut = function (r) {
    try {
      r && r.id && (lpAdd(lpReportSignal(r)), lpTriage("report"), save());
    } catch (e) {
      console.warn("loop report", e);
    }
    return base.apply(this, arguments);
  };
}
// The list of reports reads the shared signals too, so a report from another device is on the owner's.
if ("function" == typeof rpAll) {
  const base = rpAll;
  rpAll = function () {
    const out = base.apply(this, arguments) || [];
    try {
      const have = new Set(out.map((r) => r.id));
      lpInit()
        .filter((s) => "report" === s.kind && s.rep && s.rep.id)
        .forEach((s) => {
          const i = out.findIndex((r) => r.id === s.rep.id);
          const rep = Object.assign({}, s.rep, { loopId: s.loopId || "" });
          // the shared copy carries the answer the owner gave on another device
          if (i >= 0) out[i] = Object.assign({}, out[i], { status: rep.status || out[i].status, reply: rep.reply || out[i].reply, repliedBy: rep.repliedBy || out[i].repliedBy, repliedAt: rep.repliedAt || out[i].repliedAt, loopId: rep.loopId });
          else have.has(rep.id) || out.push(rep);
        });
      out.sort((a, b) => String(a.at).localeCompare(String(b.at)));
    } catch (e) {}
    return out;
  };
}
if ("function" == typeof rpPatch) {
  const base = rpPatch;
  rpPatch = function (id, patch) {
    try {
      const s = lpInit().find((x) => "report" === x.kind && x.rep && x.rep.id === id);
      s && (Object.assign(s.rep, patch), save());
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
// A reporter whose report was marked fixed can say it is still wrong: one tap, the same problem reopens.
function lpStillWrong(repId) {
  const s = lpInit().find((x) => "report" === x.kind && x.rep && x.rep.id === repId);
  if (!s) return toast("That report is not on the shared list yet"), !1;
  const again = Object.assign({}, s, { id: s.id + ":again:" + today(), day: today(), at: appNowIso(), still: !0, sev: "stuck", text: "Still wrong after the fix", rep: null });
  lpAdd(again), lpTriage("still");
  try {
    rpPatch(repId, { status: "accepted", movedAt: appNowIso(), reply: "You said it is still wrong. It is open again, at the top." });
  } catch (e) {}
  save();
  toast("Thank you. It is open again for the owner", [{ label: "Open", run: () => (rpClose(), rpOpen()) }]);
  return !0;
}
if ("function" == typeof rpOpen) {
  const base = rpOpen;
  rpOpen = function () {
    const r = base.apply(this, arguments);
    try {
      const rows = document.querySelectorAll("#rp-panel .rp-mine-row"),
        mine = rpMine().slice(0, 8);
      rows.forEach((row, i) => {
        const rep = mine[i];
        if (!rep || "fixed" !== rep.status || row.querySelector("[data-lpstill]")) return;
        const b = document.createElement("button");
        (b.type = "button"), (b.className = "btn sm"), (b.dataset.lpstill = rep.id), (b.textContent = "Still Wrong");
        b.onclick = (e) => (e.stopPropagation(), lpStillWrong(rep.id));
        row.appendChild(b);
      });
    } catch (e) {}
    return r;
  };
}

// ---- 1b. usage, measured in the app: counts and screens only, never what was typed ----------------------------
// One signal per person per day (us:<day>:<uid>): by[screen] = {export, retype, back, abandon, rage, to, label}.
let lpUsageDirty = !1;
function lpUsage(screen, metric, extra) {
  try {
    if (!screen || "undefined" == typeof DB || !DB || !DB.company) return;
    const me = lpMe(),
      who = me.id || "r:" + role(),
      d = today(),
      id = `us:${d}:${who}`;
    let s = lpInit().find((x) => x.id === id);
    s || ((s = { id: id, kind: "usage", day: d, uid: me.id || "", role: role(), by: {} }), DB.signals.push(s));
    const m = (s.by[screen] = s.by[screen] || {});
    m[metric] = (m[metric] || 0) + 1;
    m.label || (m.label = lpScreen(screen));
    extra && extra.to && ((m.to = m.to || {}), (m.to[extra.to] = (m.to[extra.to] || 0) + 1));
    extra && extra.field && !m.field && (m.field = String(extra.field).slice(0, 40));
    extra && extra.form && !m.form && (m.form = String(extra.form).slice(0, 60));
    lpUsageDirty = !0;
  } catch (e) {}
}
// saved with the next save, or within a minute
setInterval(() => {
  if (lpUsageDirty) {
    lpUsageDirty = !1;
    try {
      save();
    } catch (e) {}
  }
}, 6e4);
const lpView = () => ("undefined" != typeof view ? String(view || "") : "");
// exports: a spreadsheet or CSV file made for download
try {
  const base = URL.createObjectURL;
  URL.createObjectURL = function (o) {
    try {
      o && o.type && /csv|spreadsheet|excel|officedocument\.spreadsheet/i.test(o.type) && lpUsage(lpView(), "export");
    } catch (e) {}
    return base.apply(this, arguments);
  };
} catch (e) {}
// back-tracking: A, then B, then straight back to A within 30 seconds counts on A ("they went to B for it")
const lpTrack = [];
if ("function" == typeof render) {
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      const v = lpView(),
        t = Date.now(),
        last = lpTrack[lpTrack.length - 1];
      if (v && (!last || last.v !== v)) {
        lpTrack.push({ v: v, t: t }), lpTrack.length > 6 && lpTrack.shift();
        const n = lpTrack.length;
        n >= 3 && lpTrack[n - 3].v === v && t - lpTrack[n - 3].t < 3e4 && lpUsage(v, "back", { to: lpTrack[n - 2].v });
      }
    } catch (e) {}
    return r;
  };
}
// rage taps: three taps on the same control within 1.2 seconds
const lpTaps = { el: null, n: 0, t: 0 };
document.addEventListener(
  "click",
  (e) => {
    try {
      const el = e.target.closest("button, a, [role=button], .btn, .gl, .kpi, tr");
      if (!el || el.closest("#rp-panel")) return;
      const t = Date.now();
      el === lpTaps.el && t - lpTaps.t < 1200 ? lpTaps.n++ : ((lpTaps.el = el), (lpTaps.n = 1)), (lpTaps.t = t);
      3 === lpTaps.n && lpUsage(lpView(), "rage");
    } catch (er) {}
  },
  !0,
);
// abandoned forms: a dialog typed in and closed without its save
document.addEventListener(
  "input",
  (e) => {
    const m = e.target && e.target.closest && e.target.closest("#mbm");
    m && (m.dataset.lpdirty = "1");
  },
  !0,
);
document.addEventListener(
  "click",
  (e) => {
    const ok = e.target && e.target.closest && e.target.closest("#mbm-ok, #mbm-alt");
    ok && ok.closest("#mbm") && (ok.closest("#mbm").dataset.lpsub = "1");
  },
  !0,
);
if ("function" == typeof mbCloseModal) {
  const base = mbCloseModal;
  mbCloseModal = function () {
    try {
      const m = document.getElementById("mbm");
      m && "1" === m.dataset.lpdirty && "1" !== m.dataset.lpsub && lpUsage(lpView(), "abandon", { form: ((m.querySelector(".mbm-hd h3") || {}).textContent || "").trim() });
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
// repeated typing: the same words typed into the same field a third time in 14 days. The comparison is a hash kept
// on this device only; the signal carries the field's label, never the words.
const LP_TYPED = "sdp:loop-typed";
function lpHash(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) (h ^= s.charCodeAt(i)), (h = Math.imul(h, 16777619));
  return (h >>> 0).toString(36);
}
document.addEventListener(
  "change",
  (e) => {
    try {
      const el = e.target;
      if (!el || !/^(INPUT|TEXTAREA)$/.test(el.tagName) || /^(checkbox|radio|file|date|number|hidden|password|search)$/i.test(el.type || "")) return;
      const v = String(el.value || "").trim().toLowerCase();
      if (v.length < 6) return;
      const lab = ((el.closest(".f") || {}).querySelector ? (el.closest(".f").querySelector("label") || {}).textContent : "") || el.getAttribute("placeholder") || el.dataset.f || el.name || "a field",
        key = lpView() + "|" + String(lab).trim().slice(0, 40),
        h = lpHash(key + "|" + v);
      let M = {};
      try {
        M = JSON.parse(localStorage.getItem(LP_TYPED) || "{}");
      } catch (er) {}
      const now = Date.now(),
        cut = now - 14 * 864e5;
      Object.keys(M).forEach((k) => (M[k] = (M[k] || []).filter((t) => t > cut)));
      (M[h] = M[h] || []).push(now);
      3 === M[h].length && lpUsage(lpView(), "retype", { field: String(lab).trim() });
      const keys = Object.keys(M).filter((k) => M[k].length);
      keys.length > 400 && keys.slice(0, keys.length - 400).forEach((k) => delete M[k]);
      try {
        localStorage.setItem(LP_TYPED, JSON.stringify(M));
      } catch (er) {}
    } catch (er) {}
  },
  !0,
);

// ---- 1c. the Standard Watch, one signal per rule per day; 1d. lessons that keep firing -------------------------
function lpWatchSnap() {
  const d = today();
  let n = 0;
  ("undefined" != typeof STANDARD_RULES ? STANDARD_RULES : []).forEach((R) => {
    if (!R || !1 === R.measured || "function" != typeof R.rows) return;
    let rows = [];
    try {
      rows = R.rows() || [];
    } catch (e) {
      return;
    }
    const id = `sw:${R.id}:${d}`;
    if (!rows.length) return void (DB.signals = lpInit().filter((x) => x.id !== id));
    let label = R.id;
    try {
      const c = standardCite(R.c);
      c && c.text && (label = String(c.text).replace(/[.:].*$/, "").slice(0, 70));
    } catch (e) {}
    lpAdd({ id: id, kind: "watch", day: d, what: R.id, n: rows.length, p: R.p || "", owner: R.owner || "", label: label, screen: "", text: rows.slice(0, 2).map((r) => r.what).join(" · ").slice(0, 200) }), n++;
  });
  return n;
}
function lpLessonSignals() {
  let n = 0;
  try {
    const L = lnInit();
    (DB.lessons || [])
      .filter((l) => l.learn && !1 !== l.active && l.at)
      .forEach((l) => {
        const E = ("undefined" != typeof LEARN_EVENTS ? LEARN_EVENTS : []).find((x) => x.kind === l.learn) || {};
        let p = "";
        try {
          p = (standard().principles || [])[standardTier({ kind: "learn:" + l.learn }) - 1]?.id || "";
        } catch (e) {}
        Object.values(L.events || {})
          .filter((ev) => ev.kind === l.learn && String(ev.seen || "") > String(l.at))
          .forEach((ev) => {
            const id = "ln:" + ev.key;
            lpInit().some((s) => s.id === id) || (lpAdd({ id: id, kind: "lesson", day: ev.seen, what: l.learn, label: l.title, text: ev.what, p: p, approvedAt: l.at }), n++);
          });
      });
  } catch (e) {}
  return n;
}
// ---- 1e. agents' and workshops' findings: [{title, screen, sev, role, text, fix}] from a review or the agent month
function lpImportFindings(list, source) {
  if (!Array.isArray(list)) return 0;
  let n = 0;
  list.forEach((f, i) => {
    if (!f || !(f.title || f.text)) return;
    const id = "fd:" + lpHash(`${source || ""}|${f.screen || ""}|${f.title || f.text}`);
    if (lpInit().some((s) => s.id === id)) return;
    const sev = String(f.sev || f.severity || "").replace(/^s(ev)?/i, "");
    lpAdd({ id: id, kind: "finding", day: f.day || today(), role: f.role || "", uid: "", screen: f.screen || "", label: String(f.title || "").slice(0, 140), text: String(f.text || f.title || "").slice(0, 600), sev: sev, p: f.p || ("1" === sev ? "integrity" : "quality"), fix: String(f.fix || "").slice(0, 400), source: source || "a review" }), n++;
  });
  return n && (lpTriage("findings"), save()), n;
}

// ---- 2. the brain triages ----------------------------------------------------------------------------------------
function lpChangeOf(key) {
  return (DB.changes || []).find((c) => c && c.key === key) || null;
}
function lpTriage(src) {
  lpInit();
  const td = today(),
    T = LP.triage(DB.signals, DB.changes, td, { order: lpOrder(), names: lpNames() }),
    made = [];
  T.drafts.forEach((x) => {
    const c = {
      id: uid("ch"),
      key: x.key,
      title: x.d.title,
      why: x.d.what,
      kind: x.d.kind,
      delta: x.d.delta || undefined,
      evidence: x.d.evidence,
      status: "draft",
      at: td,
      by: "The Brain",
      source: "loop",
      loop: Object.assign(x.loop, { fix: x.d.fix, risk: x.d.risk, accept: x.d.accept, wordedBy: "rules", history: [{ at: td, what: "Found", by: "The Brain", src: src || "" }], reopened: 0 }),
    };
    DB.changes.push(c), made.push(c);
  });
  T.updates.forEach((u) => {
    const c = lpChangeOf(u.key);
    if (!c) return;
    const keep = c.loop || {};
    c.loop = Object.assign({}, keep, u.loop, { fix: keep.fix, risk: keep.risk, accept: keep.accept, wordedBy: keep.wordedBy, history: keep.history || [], reopened: keep.reopened || 0, ticket: keep.ticket, applied: keep.applied, liveAt: keep.liveAt, appliedAt: keep.appliedAt, verified: keep.verified, notified: keep.notified, aiText: keep.aiText });
    // the evidence and the count move with the signals while it waits; the wording the assistant wrote stays
    u.d && "draft" === c.status && ((c.evidence = u.d.evidence), "rules" === (keep.wordedBy || "rules") && (c.why = u.d.what));
    "live" === c.status || "approved" === c.status || "draft" === c.status || delete c.loop.rank;
  });
  T.reopen.forEach((r) => lpReopen(lpChangeOf(r.key), r.why));
  // each report knows the problem it was grouped into
  DB.changes.filter((c) => "loop" === c.source && c.loop).forEach((c) => (c.loop.signals || []).forEach((sid) => {
    const s = DB.signals.find((x) => x.id === sid);
    s && "report" === s.kind && (s.loopId = c.id);
  }));
  made.length && lpTell(made);
  made.length && lpReword(made);
  return { drafted: made.length, updated: T.updates.length, reopened: T.reopen.length };
}
// The owner hears of new problems once, in their assistant, with the way to the list.
function lpTell(made) {
  try {
    if (!lpOwner() || "function" != typeof paNudge) return;
    paNudge(
      `${made.length} problem${1 === made.length ? "" : "s"} for you to decide.`,
      `From what people reported and what the ERP measured: ${made.map((c) => `"${c.title}"`).slice(0, 3).join(", ")}${made.length > 3 ? ` and ${made.length - 3} more` : ""}. Each is ranked by the Standard with its evidence, the fix and the risk, under Company › Meetings › Changes.`,
      { kind: "brain", id: "loop-" + today() + "-" + made[0].id },
      "the improvement loop",
    );
  } catch (e) {}
}
// The assistant's wording through the platform's door, when it is there; the rules' wording otherwise. It sees the
// proposal and the evidence (already scrubbed), never mail.
async function lpReword(list) {
  try {
    if (!window.SDP_CONFIG || "function" != typeof ai || ("function" == typeof aiReady && !aiReady())) return 0;
  } catch (e) {
    return 0;
  }
  let n = 0;
  for (const c of list) {
    try {
      const prompt = `You write for the owner of a design-build firm. Rewrite this proposed improvement to the firm's ERP in plain, specific words, no exclamation marks, as JSON {"title":"under 12 words","what":"what is wrong, one or two sentences","fix":"the fix, one or two sentences","risk":"the risk, one sentence"}. Keep every number and every name of a screen. Do not invent anything.\n\n${JSON.stringify({ title: c.title, what: c.why, fix: c.loop.fix, risk: c.loop.risk, evidence: (c.evidence || []).map((e) => e.t).slice(0, 6) })}`;
      const out = await ai(prompt, 600);
      const m = String(out || "").match(/\{[\s\S]*\}/),
        j = m ? JSON.parse(m[0]) : null;
      if (!j || !j.title || !j.what) continue;
      const cl = (s, k) => String(s || "").replace(/[<>]/g, "").slice(0, k);
      (c.loop.aiText = { title: cl(j.title, 140), what: cl(j.what, 500), fix: cl(j.fix, 500), risk: cl(j.risk, 300) }), (c.loop.wordedBy = "assistant"), n++;
    } catch (e) {}
  }
  n && (save(), render());
  return n;
}
const lpT = (c, k) => (c.loop && c.loop.aiText && c.loop.aiText[k]) || ("title" === k ? c.title : "what" === k ? c.why : (c.loop || {})[k] || "");

// ---- 3. the owner approves --------------------------------------------------------------------------------------
function lpFind(id) {
  return (DB.changes || []).find((c) => c.id === id && "loop" === c.source) || null;
}
function lpLog(c, what, why) {
  c.loop.history = c.loop.history || [];
  c.loop.history.push({ at: today(), stamp: appNowIso(), what: what, by: lpMe().name || role(), why: why || "" });
}
// The build ticket: the record with the evidence and the acceptance test, and the GitHub issue body made from it.
function lpTicket(c) {
  const L = c.loop,
    n = (DB.changes || []).filter((x) => x.loop && x.loop.ticket).length + 1,
    no = (L.ticket && L.ticket.no) || "IMP-" + String(n).padStart(3, "0");
  const body = [
    `## ${lpT(c, "title")}`,
    "",
    `**Ticket:** ${no} · **Change:** ${c.id} · **Approved:** ${L.approvedBy || ""} ${L.approvedAt ? fmtL(L.approvedAt) : ""}`,
    `**Decision principle:** ${lpPWord(L.p)} · **Rank when approved:** ${L.rank || "—"} · **People:** ${L.people} (${(L.roles || []).map((r) => LP.ROLE_WORDS[r] || r).join(", ") || "none named"}) · **Seen:** ${L.n} times on ${L.days} days, ${fmtL(L.first)} to ${fmtL(L.last)}`,
    `**Screen:** ${lpScreen(L.screen) || "—"}${L.screen ? ` (\`${L.screen}\`)` : ""}`,
    "",
    "### What is wrong",
    lpT(c, "what"),
    "",
    "### Evidence",
    ...(c.evidence || []).map((e) => `- ${e.t}${e.m ? ` _(${e.m})_` : ""}`),
    "",
    "### The fix",
    lpT(c, "fix"),
    "",
    "### Risk",
    lpT(c, "risk"),
    "",
    "### Acceptance test",
    ...(L.accept || []).map((a) => `- [ ] ${a}`),
    "- [ ] The full test net is green (smoke, baseline, lint, counts lint, day walk, finance cross-check, Ask bank) and the role walks pass on desktop and phone.",
    "- [ ] The owner approves the release; the change turns Live in Meetings › Changes and the people who reported it are told.",
    "",
    `_Drafted by the ERP's improvement loop from ${plur(L.signals ? L.signals.length : 0, "signal")}. No names, amounts or mail are in this ticket._`,
  ].join("\n");
  return { no: no, at: today(), body: body, accept: (L.accept || []).slice() };
}
const plur = (n, w) => `${n} ${w}${1 === n ? "" : "s"}`;
function lpApprove(id) {
  const c = lpFind(id);
  if (!c || "draft" !== c.status) return !1;
  if (!lpOwner()) return toast("Only the owner approves a change"), !1;
  const by = lpMe().name || "Owner",
    td = today();
  (c.loop.approvedBy = by), (c.loop.approvedAt = td), (c.approvedBy = by), (c.approvedAt = td);
  if ("rule" === c.kind || "setting" === c.kind) {
    const d = c.delta || {},
      was = lpGet(d.path);
    lpSet(d.path, d.to);
    c.loop.applied = { path: d.path, from: was, to: d.to, at: td, by: by };
    (c.status = "live"), (c.loop.appliedAt = td), (c.loop.liveAt = td);
    try {
      audit("change", c.id, "applied", JSON.stringify(was), JSON.stringify(d.to), `${by} approved: ${c.title}`);
    } catch (e) {}
    lpLog(c, "Approved and applied", `${d.label || d.path}: ${String(was)} to ${String(d.to)}`);
    lpNotify(c, "live");
    "function" == typeof lpWatchFire && lpWatchFire();
  } else {
    (c.status = "approved"), (c.loop.ticket = lpTicket(c));
    try {
      audit("change", c.id, "approved", "draft", "approved", `${by} approved a build: ${c.title}`);
    } catch (e) {}
    lpLog(c, `Approved; build ticket ${c.loop.ticket.no}`, "");
    lpNotify(c, "approved");
  }
  try {
    log(`Change ${c.status}: ${c.title}`, "change", by);
  } catch (e) {}
  save();
  toast("live" === c.status ? `Applied: ${c.title}` : `Approved: build ticket ${c.loop.ticket.no}`, [{ label: "Open", run: () => lpOpen(c.id) }]);
  render();
  return !0;
}
function lpDecline(id, why) {
  const c = lpFind(id);
  if (!c || "draft" !== c.status) return !1;
  if (!lpOwner()) return toast("Only the owner declines a change"), !1;
  if (!String(why || "").trim()) return toast("Say why, so it is not proposed again for the same reason"), !1;
  (c.status = "declined"), (c.loop.declined = { at: today(), by: lpMe().name || "Owner", why: String(why).slice(0, 300) });
  lpLog(c, "Declined", why);
  lpNotify(c, "declined");
  save(), toast(`Declined: ${c.title}. It will not be proposed again`, [{ label: "Open", run: () => lpOpen(c.id) }]), render();
  return !0;
}
// An applied rule goes back to what it was, on the audit trail too.
function lpUndo(id) {
  const c = lpFind(id);
  if (!c || "live" !== c.status || !c.loop.applied) return !1;
  if (!lpOwner()) return toast("Only the owner undoes a change"), !1;
  const A = c.loop.applied;
  lpSet(A.path, A.from);
  (c.status = "reverted"), (c.loop.revertedAt = today());
  try {
    audit("change", c.id, "reverted", JSON.stringify(A.to), JSON.stringify(A.from), `${lpMe().name || "Owner"} undid: ${c.title}`);
  } catch (e) {}
  lpLog(c, "Undone", `${A.path} back to ${String(A.from)}`);
  save(), toast(`Undone: ${c.title}`, [{ label: "Open", run: () => lpOpen(c.id) }]), render();
  return !0;
}
// A build goes live when the version that carries it arrives; the owner marks it, the loop starts the month check.
function lpShipped(id) {
  const c = lpFind(id);
  if (!c || !["approved", "requested"].includes(c.status)) return !1;
  if (!lpOwner()) return toast("Only the owner marks a build shipped"), !1;
  (c.status = "live"), (c.loop.liveAt = today()), c.loop.ticket && (c.loop.ticket.shippedAt = today());
  lpLog(c, "Shipped", c.loop.ticket ? c.loop.ticket.no : "");
  lpNotify(c, "live");
  save(), toast(`Live: ${c.title}. The loop checks it on ${fmtL(LP.addDays(today(), LP.MONTH))}`, [{ label: "Open", run: () => lpOpen(c.id) }]), render();
  return !0;
}
function lpGet(path) {
  const [root, ...rest] = String(path || "").split(".");
  let o = "company" === root ? DB.company : null;
  for (const k of rest) o = o && "object" == typeof o ? o[k] : void 0;
  return void 0 === o ? !1 : o;
}
function lpSet(path, v) {
  const [root, ...rest] = String(path || "").split(".");
  if ("company" !== root || !rest.length) return !1;
  let o = DB.company;
  for (let i = 0; i < rest.length - 1; i++) (o[rest[i]] = o[rest[i]] && "object" == typeof o[rest[i]] ? o[rest[i]] : {}), (o = o[rest[i]]);
  return (o[rest[rest.length - 1]] = v), !0;
}
function lpReopen(c, why) {
  if (!c || !c.loop) return !1;
  const was = c.status;
  (c.status = "draft"), (c.loop.reopened = (c.loop.reopened || 0) + 1), (c.loop.repeat = !0);
  (c.loop.lastLiveAt = c.loop.liveAt), delete c.loop.liveAt, delete c.loop.verified, delete c.loop.approvedAt;
  lpLog(c, "Reopened", why);
  try {
    audit("change", c.id, "reopened", was, "draft", why);
  } catch (e) {}
  lpNotify(c, "reopened");
  return !0;
}

// ---- 4. close the loop: the people who reported it are told; a month later the loop checks -----------------------
const LP_TELL = {
  approved: { st: "accepted", say: (c) => `Accepted: the owner approved a change for it (${c.loop.ticket ? c.loop.ticket.no : "a build"}). You will hear when it is live.` },
  live: { st: "fixed", say: (c) => `Changed: ${lpT(c, "fix")} If it still happens, press Still Wrong on this report.` },
  declined: { st: "declined", say: (c) => `The owner decided not to change it: ${(c.loop.declined || {}).why || ""}` },
  reopened: { st: "accepted", say: () => "It came back, so it is open again, at the top of the owner's list." },
};
function lpNotify(c, what) {
  const T = LP_TELL[what];
  if (!T || !c.loop) return 0;
  const reps = lpInit().filter((s) => "report" === s.kind && s.rep && (c.loop.signals || []).includes(s.id)),
    told = (c.loop.notified = c.loop.notified || []);
  let n = 0;
  reps.forEach((s) => {
    try {
      rpPatch(s.rep.id, { status: T.st, movedAt: appNowIso(), reply: T.say(c), repliedBy: "The Brain", repliedAt: appNowIso() });
    } catch (e) {}
    n++;
  });
  // a Today task for each named office person who reported it, when it changed for them
  if ("live" === what) {
    const people = [...new Set(reps.map((s) => s.uid).filter(Boolean))];
    people.forEach((u) => {
      const U = (DB.users || []).find((x) => x.id === u);
      if (!U || ["foreman", "crew", "driver", "client"].includes(U.role)) return;
      const key = `${c.id}|${u}|${c.loop.reopened || 0}`;
      if (told.includes(key)) return;
      "function" == typeof asFirmTasks &&
        asFirmTasks().push({ id: uid("a"), title: `See what changed: ${lpT(c, "title")}`, assignee: U.name, due: today(), priority: "low", status: "todo", createdAt: today(), completedAt: "", notes: `${lpT(c, "fix")} You reported this. If it still happens, press Still Wrong on your report.`, link: null, source: { kind: "improve", id: c.id, label: c.title } });
      told.push(key);
    });
  }
  return n;
}
function lpVerifyAll() {
  let n = 0;
  (DB.changes || [])
    .filter((c) => "loop" === c.source && "live" === c.status && c.loop)
    .forEach((c) => {
      const v = LP.verify(c, lpInit(), today());
      if (!v) return;
      if ("stopped" === v.result) (c.loop.verified = v), lpLog(c, "Checked a month later: it stopped", `${v.before} before, ${v.after} after`), n++;
      else lpReopen(c, `Checked a month later: it did not stop (${v.before} in the 30 days before, ${v.after} in the 30 after)`), n++;
    });
  return n;
}
// An approved watch rule: each breach becomes a dated task for the rule's owner the morning it appears, once.
function lpWatchFire() {
  const W = (DB.company || {}).loopWatch || {};
  let n = 0;
  ("undefined" != typeof STANDARD_RULES ? STANDARD_RULES : []).forEach((R) => {
    if (!W[R.id] || "function" != typeof R.rows) return;
    let rows = [];
    try {
      rows = R.rows() || [];
    } catch (e) {
      return;
    }
    const U = (DB.users || []).find((u) => u.role === R.owner) || {},
      T = asFirmTasks();
    rows.forEach((r) => {
      const key = `lw:${R.id}:${r.key}`;
      if (T.some((a) => a.source && a.source.key === key)) return;
      T.push({ id: uid("a"), title: String(r.what || R.id).slice(0, 120), assignee: U.name || "", due: today(), priority: "high", status: "todo", createdAt: today(), completedAt: "", notes: `${r.sub || ""}${r.sub ? ". " : ""}The owner turned this standard's breaches into tasks (the improvement loop).`, link: null, source: { kind: "improve", key: key, rule: R.id, label: R.id } }), n++;
    });
  });
  return n;
}

// ---- the loop's day: what boot, a new day and the timers run ----------------------------------------------------
function lpDay(src) {
  lpInit(), lpPrune();
  const w = lpWatchSnap(),
    l = lpLessonSignals(),
    t = lpTriage(src || "day"),
    v = lpVerifyAll(),
    f = lpWatchFire();
  DB.company.loopLast = { at: appNowIso(), day: today(), src: src || "day", watch: w, lessons: l, drafted: t.drafted, verified: v, fired: f };
  return DB.company.loopLast;
}
"undefined" != typeof APP_DAY_HOOKS && APP_DAY_HOOKS.push(["lpDay", () => (lpDay("day"), !0)]);
if ("function" == typeof finishBoot) {
  const base = finishBoot;
  finishBoot = function () {
    const r = base.apply(this, arguments);
    // after the first paint: the watch's rows are not cheap, and nothing on the first screen waits on them
    setTimeout(() => {
      try {
        const last = (DB.company || {}).loopLast;
        (last && last.day === today()) || (lpDay("boot"), save());
      } catch (e) {
        console.warn("loop boot", e);
      }
    }, 1200);
    return r;
  };
}

// ---- 5. the page: Meetings › Changes, the ranked problems first, with the measures ------------------------------
function lpOpen(id) {
  try {
    (mtTab = "changes"), (mtOpen = "");
  } catch (e) {}
  (window.lpFocus = id || ""), (view = "meetings"), render();
  setTimeout(() => {
    const el = id && document.querySelector(`[data-lpcard="${id}"]`);
    el && el.scrollIntoView({ block: "center" });
  }, 60);
}
const LP_ST = { draft: ["warn", "Waiting on You"], approved: ["info", "Being Built"], requested: ["info", "Being Built"], live: ["ok", "Live"], declined: ["neutral", "Declined"], reverted: ["neutral", "Undone"] };
function lpStatsHtml() {
  const S = LP.stats(DB.changes, today()),
    tile = (k, v, s, tone) => `<div class="gl static ${tone || ""}"><span class="gl-k">${k}</span><b class="gl-v">${v}</b><span class="gl-s">${s}</span></div>`;
  return `<div class="card lp-measure" data-lpmeasure><div class="hd"><h3>How the Loop Is Doing</h3><span class="small muted">found against fixed, from what people report and what the ERP measures</span></div><div class="glance tl">${tile("Found", S.found, `${S.found30} in the last 30 days`)}${tile("Waiting on You", S.waiting, "ranked below", S.waiting ? "warn" : "")}${tile("Being Built", S.building, "approved, with a ticket")}${tile("Fixed", S.fixed, `${S.held} held a month · ${S.checking} being checked`)}${tile("Repeats", S.repeats, "came back after a fix", S.repeats ? "bad" : "")}${tile("Time to Fix", null == S.medianDays ? "—" : `${S.medianDays} d`, "median, first seen to live")}</div></div>`;
}
function lpCardHtml(c, first) {
  const L = c.loop,
    st = LP_ST[c.status] || ["neutral", c.status],
    owner = lpOwner(),
    roles = (L.roles || []).map((r) => LP.ROLE_WORDS[r] || r).join(", "),
    acts = [];
  if ("draft" === c.status && owner) acts.push(`<button class="btn sm ${first ? "primary" : ""}" data-lpact="ok|${c.id}">${"rule" === c.kind ? "Approve and Apply" : "Approve the Build"}</button>`, `<button class="btn sm ghost" data-lpact="no|${c.id}">Decline</button>`);
  if (["approved", "requested"].includes(c.status) && L.ticket) acts.push(`<button class="btn sm" data-lpact="issue|${c.id}">Copy as GitHub Issue</button>`), owner && acts.push(`<button class="btn sm ghost" data-lpact="ship|${c.id}">Mark Shipped</button>`);
  if ("live" === c.status && L.applied && owner) acts.push(`<button class="btn sm ghost" data-lpact="undo|${c.id}">Undo</button>`);
  "draft" !== c.status || owner || acts.push('<span class="small muted">Waiting on the owner</span>');
  const check = "live" === c.status ? (L.verified ? `<div class="small ok">Checked ${fmtL(L.verified.at)}: it stopped (${L.verified.before} in the 30 days before, ${L.verified.after} after)</div>` : `<div class="small muted">Live since ${fmtL(L.liveAt)}. The loop checks on ${fmtL(LP.addDays(L.liveAt, LP.MONTH))} whether it stopped, and reopens it if not.</div>`) : "";
  return `<div class="card lp-card ${c.status}${window.lpFocus === c.id ? " lp-focus" : ""}" data-lpcard="${c.id}">
    <div class="lp-hd"><span class="lp-rank" title="Rank by the Standard">${L.rank && ["draft", "approved", "requested"].includes(c.status) ? "#" + L.rank : ""}</span><span class="pill ${st[0]}">${st[1]}</span><span class="pill neutral">${esc(lpPWord(L.p))}</span>${L.repeat ? '<span class="pill bad">Repeat</span>' : ""}<b class="lp-title">${esc(lpT(c, "title"))}</b></div>
    <div class="small muted lp-sub">${plur(L.people || 0, "person").replace("persons", "people")}${roles ? ` (${esc(roles)})` : ""} · seen ${L.n} time${1 === L.n ? "" : "s"} on ${plur(L.days || 0, "day")}${L.stuck ? ` · ${L.stuck} stuck` : ""} · ${"rule" === c.kind ? "a rule, applies on approval" : "a change to the ERP, a build ticket on approval"}${L.wordedBy === "assistant" ? " · worded by the assistant" : ""}</div>
    <p class="small lp-what">${esc(lpT(c, "what"))}</p>
    <div class="small lp-fix"><b>The fix:</b> ${esc(lpT(c, "fix"))}</div>
    <div class="small lp-risk"><b>The risk:</b> ${esc(lpT(c, "risk"))}</div>
    ${c.delta && c.delta.label ? `<div class="small"><b>${esc(c.delta.label)}</b>${L.applied ? `: was ${esc(String(L.applied.from))}, now ${esc(String(L.applied.to))}` : ""}</div>` : ""}
    <details class="lp-ev"><summary>The Evidence (${(c.evidence || []).length})</summary>${(c.evidence || []).map((e) => `<div class="small">${esc(e.t)}${e.m ? ` <span class="muted">· ${esc(e.m)}</span>` : ""}</div>`).join("")}${(L.accept || []).length ? `<div class="small" style="margin-top:6px"><b>How it is checked:</b></div>${L.accept.map((a) => `<div class="small muted">${esc(a)}</div>`).join("")}` : ""}${(L.history || []).length ? `<div class="small" style="margin-top:6px"><b>History:</b></div>${L.history.map((h) => `<div class="small muted">${fmtL(h.at)} · ${esc(h.what)}${h.by ? ` · ${esc(h.by)}` : ""}${h.why ? ` · ${esc(h.why)}` : ""}</div>`).join("")}` : ""}</details>
    ${L.ticket ? `<div class="small muted">Ticket ${esc(L.ticket.no)} · ${fmtL(L.ticket.at)}${L.ticket.shippedAt ? ` · shipped ${fmtL(L.ticket.shippedAt)}` : ""}</div>` : ""}
    ${check}
    ${acts.length ? `<div class="row lp-acts">${acts.join("")}</div>` : ""}
  </div>`;
}
function lpListHtml() {
  const O = ["draft", "approved", "requested", "live", "reverted", "declined"],
    L = (DB.changes || [])
      .filter((c) => "loop" === c.source && c.loop)
      .sort((a, b) => O.indexOf(a.status) - O.indexOf(b.status) || (a.loop.rank || 999) - (b.loop.rank || 999) || String(b.at).localeCompare(String(a.at)));
  const firstDraft = L.find((c) => "draft" === c.status);
  return `${lpStatsHtml()}<div class="lp-list"><div class="hd" style="margin:10px 0 6px"><h3>Problems the Brain Ranked</h3><span class="small muted">by the Standard: safety, law, integrity, quality, client, schedule, cost; then someone stuck, people hurt and how often</span></div>${L.length ? L.map((c) => lpCardHtml(c, c === firstDraft)).join("") : '<div class="empty">Nothing found yet. What people report with Report a Problem, what the ERP measures around the screens, a standard broken on two days and a lesson that did not stop it all land here, ranked.</div>'}</div><div class="hd" style="margin:14px 0 6px"><h3>From the Meetings and the Close-Out</h3></div>`;
}
if ("function" == typeof mtChangesHtml) {
  const base = mtChangesHtml;
  mtChangesHtml = function () {
    const all = DB.changes || [];
    let h = "";
    // the older layers draw every other change as before; the loop's rows are drawn above, ranked
    DB.changes = all.filter((c) => !(c && "loop" === c.source));
    try {
      h = base.apply(this, arguments);
    } finally {
      DB.changes = all;
    }
    try {
      return lpListHtml() + h.replace(/<button class="btn sm primary" data-chok/g, (m) => (lpChangeFirstPrimary() ? '<button class="btn sm" data-chok' : m));
    } catch (e) {
      console.warn("loop changes", e);
      return h;
    }
  };
}
// one blue button on the screen: when a ranked problem waits, the older rows' Approve buttons are plain
const lpChangeFirstPrimary = () => lpOwner() && (DB.changes || []).some((c) => "loop" === c.source && "draft" === c.status);
function lpIssueSheet(c) {
  const body = (c.loop.ticket || lpTicket(c)).body;
  clipCopy(body).then((ok) => {
    mbModal(
      `Build Ticket ${esc(c.loop.ticket ? c.loop.ticket.no : "")}`,
      `<p class="small muted">${ok ? "Copied. " : ""}Paste it as a new issue on GitHub (title: the first line). Nothing is opened on GitHub from here.</p><textarea rows="16" class="lp-issue" readonly style="width:100%;font-family:monospace;font-size:11px">${esc(body)}</textarea>`,
      { submit: null },
    );
  });
}
document.addEventListener("click", (e) => {
  const b = e.target.closest && e.target.closest("[data-lpact]");
  if (!b) return;
  e.preventDefault();
  const [act, id] = b.dataset.lpact.split("|"),
    c = lpFind(id);
  if (!c) return;
  if ("ok" === act) return void lpApprove(id);
  if ("undo" === act) return void lpUndo(id);
  if ("ship" === act) return void lpShipped(id);
  if ("issue" === act) return void lpIssueSheet(c);
  if ("no" === act)
    mbModal(`Decline: ${esc(lpT(c, "title"))}`, `<div class="f"><label>Why Not</label><textarea data-f="why" rows="3" placeholder="It works as intended: the total leaves out unapproved change orders on purpose."></textarea></div><p class="small muted">The people who reported it are told, and it is not proposed again.</p>`, {
      submit: "Decline It",
      onSubmit: (f) => !1 !== lpDecline(id, f.why) && void 0,
    });
});
// The Problem Reports page names the change each report was grouped into, with the way to it.
if ("function" == typeof rpCard) {
  const base = rpCard;
  rpCard = function (r) {
    let h = base.apply(this, arguments);
    try {
      const c = r.loopId && (DB.changes || []).find((x) => x.id === r.loopId);
      c && (h = h.replace('<div class="row rp-acts">', `<div class="small lp-part">Part of <a href="#" data-lpgo="${c.id}">${esc(lpT(c, "title"))}</a> · ${esc((LP_ST[c.status] || ["", c.status])[1])}${c.loop.rank && "draft" === c.status ? ` · ranked #${c.loop.rank}` : ""}</div><div class="row rp-acts">`));
    } catch (e) {}
    return h;
  };
}
document.addEventListener("click", (e) => {
  const a = e.target.closest && e.target.closest("[data-lpgo]");
  a && (e.preventDefault(), lpOpen(a.dataset.lpgo));
});

// ---- Ask and the query tables ------------------------------------------------------------------------------------
if ("object" == typeof EQ_TABLES) {
  EQ_TABLES.improvements = () =>
    (DB.changes || [])
      .filter((c) => "loop" === c.source && c.loop)
      .map((c) => ({ _id: c.id, _module: "Company", _label: lpT(c, "title"), _go: { view: "meetings" }, date: c.at, status: (LP_ST[c.status] || ["", c.status])[1], rank: c.loop.rank || null, principle: lpPWord(c.loop.p), kind: "rule" === c.kind ? "rule" : "build", people: c.loop.people, seen: c.loop.n, days: c.loop.days, first: c.loop.first, last: c.loop.last, live: c.loop.liveAt || "", ticket: (c.loop.ticket || {}).no || "", repeat: !!c.loop.repeat, reopened: c.loop.reopened || 0, checked: c.loop.verified ? c.loop.verified.result : "" }));
  EQ_TABLES.signals = () =>
    lpInit()
      .filter((s) => "usage" !== s.kind)
      .map((s) => ({ _id: s.id, _module: "Company", _label: `${s.kind}: ${s.label || s.what}`, _go: { view: "report" === s.kind ? "rpbox" : "meetings" }, date: s.day, kind: s.kind, screen: lpScreen(s.screen), what: s.what, severity: s.sev || "", count: s.n || 1, role: s.role || "" }));
  "undefined" != typeof EQ_ALIAS && Object.assign(EQ_ALIAS, { improvement: "improvements", problems: "improvements", loop: "improvements", problemreports: "signals" });
  "undefined" != typeof MD_VIEWS && ((MD_VIEWS.improvements = ["meetings", "rpbox"]), (MD_VIEWS.signals = ["meetings", "rpbox"]));
}
function lpAskRoute(q) {
  const l = String(q || "").toLowerCase();
  if (!/\b(improvement loop|the loop|problems? (people )?reported|reported problems?|what('?s| has| have)? (been )?fixed|repeat problems?|problems? (came|come) back|time to fix|found (vs|versus|against) fixed|what did (we|the erp) (fix|improve)|what should (we|i) (fix|improve)|top problems?)\b/.test(l)) return null;
  let r = "";
  try {
    r = role();
  } catch (e) {}
  if (!(ROLE_VIEWS[r] || []).includes("meetings")) return null;
  const S = LP.stats(DB.changes, today()),
    L = (DB.changes || []).filter((c) => "loop" === c.source && c.loop),
    open = L.filter((c) => "draft" === c.status).sort((a, b) => (a.loop.rank || 99) - (b.loop.rank || 99));
  return {
    headline: `${S.found} problem${1 === S.found ? "" : "s"} found, ${S.fixed} fixed (${S.held} held a month), ${S.waiting} waiting on the owner, ${S.building} being built, ${S.repeats} came back after a fix. ${null == S.medianDays ? "No fix has gone live yet." : `Median time to fix: ${S.medianDays} days.`}`,
    work: open.slice(0, 6).map((c) => `#${c.loop.rank} ${lpT(c, "title")} · ${lpPWord(c.loop.p)} · ${c.loop.people} people · seen ${c.loop.n}×`).concat(L.filter((c) => "live" === c.status).slice(0, 4).map((c) => `Live ${fmtL(c.loop.liveAt)}: ${lpT(c, "title")}${c.loop.verified ? ` · ${c.loop.verified.result}` : " · being checked"}`)),
    note: "Ranked by the Standard's decision principles, then someone stuck, people hurt and how often: Company › Meetings › Changes.",
    go: { view: "meetings" },
    total: S.found,
  };
}
if ("function" == typeof paAsk) {
  const base = paAsk;
  paAsk = function (q) {
    let a = null;
    try {
      a = lpAskRoute(q);
    } catch (e) {
      a = null;
    }
    if (a) {
      try {
        paInit();
      } catch (e) {}
      return paOut(Object.assign({}, a, { kind: "loop", routedBy: "loop", go: a.go ? paGo(a.go) : null, offers: [] }));
    }
    return base.apply(this, arguments);
  };
}

/* ---- 6. §1.32 item 1: lessons carried to the next matching job, before the moment it matters --------------------
   A lesson already fires on every job its trigger matches, at a phase (BN_WHEN: kickoff, the design phase, 10 working
   days before design ends, before construction, before the first filing). What was missing: the kind of job (a
   design-only lesson on a build job is noise; bnRun now reads l.jobType) and a lesson read from a meeting arriving
   with "as soon as it matches", which is after the moment on a job that is already past it. lpLessonInfer reads the
   lesson's own words for the moment and the kind of job; the teach form opens with them, and a person changes them.
   Each lesson card says where it raises next: the job and the date. */
const LP_WHEN_RX = [
  [/\b(kick-?off|scope (letter|sheet|confirmed)|contract|retainer|proposal)\b/i, "kickoff"],
  [/\b(sample|samples|selection|selections|finish|finishes|fixture|fixtures|millwork|cabinet|tile|stone|lighting plan|design phase|drawings?)\b/i, "design"],
  [/\b(long[- ]lead|lead time|overseas|import|imported|ship(ped|ping)? from|order(ed)? early|order-by)\b/i, "predesignend"],
  [/\b(filing|file|permit|dob|lpc|landmarks?|expedit\w*|meter number|plan exam)\b/i, "prefiling"],
  [/\b(demo|demolition|framing|rough[- ]in|mobili[sz]\w*|site start|start of construction|protection)\b/i, "preconstruction"],
];
function lpLessonInfer(text) {
  const t = String(text || "");
  const hit = LP_WHEN_RX.find(([rx]) => rx.test(t));
  const design = /\b(design (job|engagement|fee|hours)|designer'?s?|interior design|studio|rendering|concept)\b/i.test(t),
    build = /\b(site|crew|foreman|sub(contractor)?s?|framing|plumb\w*|electric\w*|inspection|delivery|deliveries|demo)\b/i.test(t);
  return { when: hit ? hit[1] : "", jobType: design && !build ? "design" : build && !design ? "build" : "" };
}
// Where a lesson raises next: each live job it matches and has not fired on, with the date it will (before the moment).
function lpLessonNext(l) {
  const out = [];
  try {
    if (!l || l.learn || !1 === l.active) return out;
    const T = BN_TRIGGERS[l.trigger];
    if (!T) return out;
    (DB.projects || []).forEach((p) => {
      if (p.archived || "closed" === (p.project || {}).status) return;
      if (l.jobType && ("design" === l.jobType) !== !!lsIsDesign(p)) return;
      let hit = !1;
      try {
        hit = !!T.test(p, l.match);
      } catch (e) {}
      if (!hit || bnSatisfied(p, l)) return;
      if ((DB.brainQueue || []).some((q) => q.lessonId === l.id && q.projectId === p.id && "expired" !== q.status)) return;
      const due = bnDue(p, l.when);
      out.push({ projectId: p.id, job: String(p.project.name || "").replace(/ —.*$/, ""), due: due || "" });
    });
  } catch (e) {}
  return out.sort((a, b) => String(a.due || "9").localeCompare(String(b.due || "9")));
}
if ("function" == typeof bnLessonCard) {
  const base = bnLessonCard;
  bnLessonCard = function (l) {
    let h = base.apply(this, arguments);
    try {
      const N = lpLessonNext(l),
        kind = l.jobType ? ("design" === l.jobType ? "Design jobs only" : "Construction jobs only") : "";
      if (N.length || kind)
        h = h.replace(/<div class="row" style="gap:6px;margin-top:4px">/, `<div class="small lp-next" data-lpnext="${esc(l.id)}">${kind ? `${kind}. ` : ""}${N.length ? `Raises next on ${N.slice(0, 3).map((x) => `${esc(x.job)}${x.due ? ` by ${fmtL(x.due)}` : ""}`).join("; ")}${N.length > 3 ? ` and ${N.length - 3} more` : ""}` : "No live job matches it now"}.</div><div class="row" style="gap:6px;margin-top:4px">`);
    } catch (e) {}
    return h;
  };
}

/* ---- 7. §1.32 item 3: admin on its own, where allowed ----------------------------------------------------------
   Renewals (the obligations register: insurance, licences, filings) and vendors' insurance certificates lapsing within
   30 days on an open order (the Standard: COI 30 days ahead) go on the person's ERP calendar on the day the renewal is
   due to start, and the request to the insurer, agency or vendor follows that person's rule for Renewal Chases:
   Act Alone sends it (only to an address on file, never money, never a signature), Ask First drafts it into Approvals,
   Hand It to Me hands it back in Findings. Each step is on the assistant's Activity with its evidence. The sweep runs
   for the person signed in (their own rules and calendar), on a new day and on the server's timer. */
"undefined" != typeof STD_SEND_TYPES &&
  !STD_SEND_TYPES.some((t) => "adminChases" === t.id) &&
  STD_SEND_TYPES.push({ id: "adminChases", label: "Renewal Chases", kind: "send", def: "ask", roles: ["owner", "pm", "coord", "controller", "billing"], live: !0, what: "to an insurer, licensing agency or vendor: asks for the renewed certificate, licence or filing before it lapses. Never money, never a signature, never a new term." });
"undefined" != typeof STD_MAP && (STD_MAP.adminChases = STD_MAP.adminChases || { p: "law", c: ["value", "own", /Close every loop/i] });
const LP_ADMIN_NEVER = /\$\s?\d|\bpay(ment|ing)?\b|\bsign(ature|ed)?\b|\bprice\b|\bpremium\b|\bnew term/i;
// what is due (LOOP_CORE.adminDue, the same rule the server runs): renewals inside their lead time, and vendors'
// certificates lapsing in 30 days on an open order, each with the person who chases it
const lpAdminDue = () => LP.adminDue(DB, today());
function lpAdminSweep(src, items) {
  const me = lpMe();
  if (!me.id || "function" != typeof paRule) return { held: 0, sent: 0, drafted: 0, handed: 0 };
  DB.company.adminChase = DB.company.adminChase || {};
  const done = DB.company.adminChase,
    lv = paRule("adminChases"),
    out = { held: 0, sent: 0, drafted: 0, handed: 0 };
  DB.calendar = DB.calendar || { external: [], map: {}, last: "", calendarId: "" };
  DB.calendar.external = DB.calendar.external || [];
  (items || lpAdminDue())
    .filter((x) => x && x.key && x.uid === me.id && !done[x.key])
    .forEach((x) => {
      const ev = [`${x.what} expires ${fmtL(x.expires)}`, `Renewal starts ${fmtL(x.start)}${"coi" === x.kind ? " (the Standard: certificates 30 days ahead)" : ""}`];
      // on the calendar: the ERP's own entry on the day the renewal is due to start (today when that has passed)
      const day = x.start < today() ? today() : x.start;
      DB.calendar.external.some((e) => e.adminKey === x.key) ||
        (DB.calendar.external.push({ id: uid("ev"), kind: "hold", source: "erp", adminKey: x.key, owner: me.id, title: `Renewal: ${x.what}`, start: `${day}T09:00:00`, end: `${day}T09:30:00`, where: "", status: "confirmed" }), out.held++);
      const subject = `Renewal: ${x.what}`,
        first = String(x.party || "").split(/\s+/)[0] || "there",
        body = `Hello ${first},\n\nOur ${"coi" === x.kind ? "certificate of insurance on file for you" : x.what} expires on ${fmtL(x.expires)}. Please send the renewed ${"coi" === x.kind ? "certificate, naming SmartDesign as additional insured as before" : "document"} when you have it.\n\nThank you,\n${me.name}`;
      const rec = { at: today(), by: me.name, level: lv, src: src || "" };
      if ("hand" === lv) {
        "function" == typeof paPropAct && paPropAct({ kind: "handed", type: "adminChases", what: `Renew: ${x.what}`, why: "your rule for renewal chases is Hand It to Me", ev: ev, go: { view: "ovoffice" }, ref: x.ref });
        out.handed++, (rec.did = "handed");
      } else if ("alone" === lv && x.email && !LP_ADMIN_NEVER.test(body) && "function" == typeof standardAllows && "alone" === (standardAllows({ action: "send", type: "adminChases" }) || {}).mode) {
        DB.outbox = DB.outbox || [];
        DB.outbox.push({ id: uid("ox"), kind: "renewal", asstType: "adminChases", to: { name: x.party, email: x.email }, subject: subject, body: body, about: { label: x.what }, aboutKey: "lp|adm|" + x.key, forName: me.name, status: "sent", sentAt: appNowIso(), approvedBy: "delegated: renewal chases", at: today(), by: `${String(me.name || "").split(" ")[0]}'s assistant`, why: "your rule for renewal chases is Act Alone" });
        "function" == typeof paDidAct && paDidAct({ kind: "did", type: "adminChases", what: `Asked ${x.party} for the renewed ${"coi" === x.kind ? "certificate" : "document"}`, why: "your rule for renewal chases is Act Alone", ev: ev.concat([`To: ${x.email}`, `Subject: ${subject}`]), go: { view: "comms" } });
        try {
          standardLog("sent", `renewal chase to ${x.party} (delegated: renewal chases)`, "");
        } catch (e) {}
        out.sent++, (rec.did = "sent");
      } else {
        DB.outbox = DB.outbox || [];
        const o = { id: uid("ox"), kind: "renewal", asstType: "adminChases", to: { name: x.party, email: x.email || "" }, subject: subject, body: body, about: { label: x.what }, aboutKey: "lp|adm|" + x.key, forName: me.name, status: "draft", at: today(), by: `${String(me.name || "").split(" ")[0]}'s assistant`, why: "alone" === lv ? (x.email ? "it names money or a signature, so it waits for you" : "no address on file, so it waits for you to address it") : "your rule for renewal chases is Ask First" };
        DB.outbox.push(o);
        "function" == typeof paPropAct && paPropAct({ kind: "proposed", type: "adminChases", what: `Drafted a renewal request to ${x.party}`, why: o.why, ev: ev, go: { view: "mapprove" } });
        out.drafted++, (rec.did = "drafted");
      }
      done[x.key] = rec;
    });
  return out;
}
"undefined" != typeof APP_DAY_HOOKS && APP_DAY_HOOKS.push(["lpAdminSweep", () => (lpAdminSweep("day"), !0)]);

/* ---- 8. what the server's nightly run left in the inbox (§1.32 item 5) ------------------------------------------
   box.loop (the owner's): new problems, worded by the small model when the server had it on; reopen orders; the
   month-later checks. box.admin (each person's): today's renewals and certificates, chased here under this person's
   own rule. Filed once: a problem already on the list is updated, never added twice. */
function lpIngestServer(box) {
  if (!box) return 0;
  lpInit();
  let n = 0;
  (box.loop || []).forEach((run) => {
    (run.drafts || []).forEach((d) => {
      if (!d || !d.key || !d.title) return;
      const have = lpChangeOf(d.key);
      if (have) return void (d.aiText && "draft" === have.status && have.loop && ((have.loop.aiText = d.aiText), (have.loop.wordedBy = "assistant")));
      DB.changes.push({ id: uid("ch"), key: d.key, title: String(d.title).slice(0, 140), why: d.what || "", kind: "rule" === d.kind ? "rule" : "code", delta: d.delta || undefined, evidence: (d.evidence || []).slice(0, 10), status: "draft", at: today(), by: "The Brain (overnight)", source: "loop", loop: Object.assign({}, d.loop || {}, { fix: d.fix || "", risk: d.risk || "", accept: d.accept || [], wordedBy: d.aiText ? "assistant" : "rules", aiText: d.aiText || undefined, history: [{ at: today(), what: "Found overnight", by: "The Brain", src: "server" }], reopened: 0 }) });
      n++;
    });
    (run.reopen || []).forEach((r) => lpReopen(lpChangeOf(r.key), r.why) && n++);
    (run.checks || []).forEach((x) => {
      const c = lpChangeOf(x.key);
      if (!c || "live" !== c.status || !x.v || c.loop.verified) return;
      "stopped" === x.v.result ? ((c.loop.verified = x.v), lpLog(c, "Checked a month later: it stopped", `${x.v.before} before, ${x.v.after} after`)) : lpReopen(c, `Checked a month later: it did not stop (${x.v.before} in the 30 days before, ${x.v.after} in the 30 after)`);
      n++;
    });
  });
  (box.admin || []).forEach((run) => {
    const r = lpAdminSweep("server", run.items || []);
    n += r.held + r.sent + r.drafted + r.handed;
  });
  return n;
}
if ("function" == typeof gsIngestServer) {
  const base = gsIngestServer;
  gsIngestServer = function (box) {
    let n = 0;
    try {
      n = lpIngestServer(box);
      n && save();
    } catch (e) {
      console.warn("loop inbox", e);
    }
    const r = base.apply(this, arguments);
    try {
      n && render();
    } catch (e) {}
    return (+r || 0) + n;
  };
}
