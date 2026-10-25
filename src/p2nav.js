// =====================================================================================================================
// Pilot 2 navigation (lane p2nav, 2026-10-25). Alan's calls after the role experts' three days on phone and desktop
// (docs/pilot/pilot2/nav_workshop.md (a)-(e), docs/DECISIONS.md 2026-10-25):
//  N1  Ask is a labelled button (the sparkle and the word) in the header of every screen, phone and desktop, for every
//      role with an assistant; a screen that draws its own header (the phone's Tasks, Meeting Mode) carries it there,
//      and a sheet carries it in its own header (the sheet is held, not lost, and comes back with one tap).
//  N2  Tasks is its own page; the designer's Today tile, the Tasks page and the phone read one number (tkTasksN).
//  N3  Messages: one door with three tabs, Team (the job and direct threads, with read marks), Mail (the firm's inbox)
//      and Field (questions from the site), one unread count on the menu, the bar and the header, and what is
//      addressed to the person (a direct line, an @mention) on Today.
//  N4  One Clients directory (Clients, People, Companies as tabs of one page) and a Team page of every staff member
//      with phone and email, which Messages and every mail To and Cc field use to find a colleague.
//  N5  The foreman's bar gets Requests; the owner's Today opens on Approvals when anything waits on him; the
//      coordinator's Time & Crew shows the payroll run's status read-only (the run is built in Bills & Payroll).
//
// Design gate (BACKLOG §1.16). Nouns, lists and queues extended, nothing duplicated:
//  - Messages is the existing thread store (DB.threads and each job's p.chat, msgThreadsFor), the existing mail list
//    (DB.comms, cmListFor / cmNeedsAnswer, renderCommsInbox) and the existing site questions (DB.field.raises, the
//    Approvals queue's raise items, PRED.siteQuestionsMine). The page is the existing Chat view (v-chat) and Inbox view
//    (v-comms) under one name with one tab strip; Field is a pane of v-chat listing PRED rows, not a new list.
//  - The menu gains one item, Messages (the Chat view, which the header button reached but no menu listed); Inbox
//    leaves Today's group (it is Messages > Mail). People and Companies leave Sales: they are tabs of Clients.
//  - The Team page is a view of DB.users and DB.employees (no new store). It adds two fields to a user, email and phone,
//    because the firm had no place for a colleague's phone (the pilot's "Chen" could not be reached by name).
//  - Read marks on a team thread extend the direct thread's shared read row (t.read) to group threads, and to a job's
//    team thread through DB.msgReads[thread key][uid] (kept out of the job row, so reading never rewrites a job).
//  - Today's Inbox filter gains the chat lines addressed to the person (tdyModel().inbox): no new filter.
//  - Payroll: no new record. Time & Crew reads DB.payroll's latest run.
// =====================================================================================================================
const P2N_SPARK =
  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5l1.9 5.1 5.1 1.9-5.1 1.9L12 17.5l-1.9-5.1L5 10.5l5.1-1.9z"/><path d="M18.5 15.5l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/></svg>';
const p2nMay = (v, r) => ((ROLE_VIEWS[r || role()] || []).includes(v));
// a role has an assistant when it may open Ask (pa); the Mercer & Bond workspace keeps its own header
const p2nHasAsk = () => {
  try {
    return p2nMay("pa") && "client" !== role() && !document.body.classList.contains("ws-mb");
  } catch (e) {
    return !1;
  }
};
const p2nVis = (el) => !!el && el.getClientRects().length > 0 && "hidden" !== getComputedStyle(el).visibility;
const p2nAskHtml = (cls) => `<button type="button" class="btn tb-ask p2n-ask ${cls || ""}" data-p2nask title="Ask" aria-label="Ask">${P2N_SPARK}<span>Ask</span></button>`;

// ---- N1 Ask: the word on every header ---------------------------------------------------------------------------
// The header button (#tb-ask, mnAsk) already existed on every screen; on the phone and on a narrow desktop it was
// drawn as an unlabelled sparkle, which owner, PM, billing and the coordinator did not find. It now always carries
// its word (styles.css, "p2nav"). The sparkle in the header is the menu's own (M_ICON.ask): one mark for Ask.
function p2nAskOpen() {
  if (!p2nHasAsk()) return;
  try {
    const m = document.getElementById("mbm");
    m ? p2nHold(m) : !p2nHeld && "function" == typeof mmActive && mmActive() && (p2nHeld = { el: null, view: "tkall", title: "the Meeting" });
  } catch (e) {}
  setView("pa");
}
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("[data-p2nask]") : null;
    if (!b) return;
    e.preventDefault(), e.stopPropagation();
    p2nAskOpen();
  },
  !0,
);
// A screen that hides the app's header and draws its own (the phone's Tasks page, Meeting Mode) carries Ask in it.
const P2N_OWN_HEADS = [".view.on .tv-phhd", ".mm-top-ph .mm-phr", ".mm-top"];
function p2nAskOwnHeads() {
  const want = p2nHasAsk(),
    tb = document.getElementById("tb-ask"),
    tbOn = want && p2nVis(tb);
  // the header's own Ask goes the same way as every other (a sheet or the meeting is held, not lost)
  tb && !tb.hasAttribute("data-p2nask") && tb.setAttribute("data-p2nask", "");
  document.querySelectorAll(".p2n-ask.p2n-own").forEach((b) => {
    (!want || tbOn || !p2nVis(b.parentElement)) && b.remove();
  });
  if (!want || tbOn) return;
  for (const sel of P2N_OWN_HEADS) {
    const h = [...document.querySelectorAll(sel)].find(p2nVis);
    if (h) {
      h.querySelector("[data-p2nask]") || h.insertAdjacentHTML("beforeend", p2nAskHtml("p2n-own"));
      break;
    }
  }
}

// ---- N1 Ask from a sheet: the sheet is held, not lost ------------------------------------------------------------
// A sheet (mbModal) covers the header on the phone and the desktop alike. Its own header carries Ask; pressing it
// sets the sheet aside with what was typed in it and opens Ask, and "Back to <the sheet>" puts it back as it was.
// Meeting Mode is the same: Ask from the meeting leaves it running, and "Back to the Meeting" returns to it.
let p2nHeld = null;
function p2nHold(m) {
  if (!m || p2nHeld) return;
  const a = document.activeElement;
  a && m.contains(a) && a.blur && a.blur();
  const t = m.querySelector(".mbm-hd h3");
  p2nHeld = { el: m, view: view, title: (t && t.textContent.trim()) || "the sheet" };
  (m.id = "mbm-held"), (m.hidden = !0), m.classList.add("p2n-held");
}
function p2nResume() {
  const H = p2nHeld;
  if (!H) return;
  p2nHeld = null;
  document.getElementById("p2n-resume")?.remove();
  "function" == typeof mbCloseModal && mbCloseModal();
  if (!H.el) return void setView(H.view);
  view !== H.view && ((view = H.view), render());
  (H.el.id = "mbm"), (H.el.hidden = !1), H.el.classList.remove("p2n-held");
  const f = H.el.querySelector("input:not([type=hidden]),textarea,select");
  f && setTimeout(() => f.focus(), 30);
}
function p2nResumeBar() {
  let b = document.getElementById("p2n-resume");
  // a held sheet lives while it is in the page; the meeting while it is on and the person is away from it
  const live = (H) => !!H && (H.el ? document.body.contains(H.el) : view !== H.view && "function" == typeof mtCurrent && !!mtCurrent());
  if (!live(p2nHeld)) return (p2nHeld = null), void (b && b.remove());
  if (!b) {
    (b = document.createElement("button")), (b.type = "button"), (b.id = "p2n-resume"), (b.className = "p2n-resume no-print");
    b.onclick = () => p2nResume();
    document.body.appendChild(b);
  }
  b.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg><span>Back to ${esc(p2nHeld.title)}</span>`;
  b.setAttribute("aria-label", `Back to ${p2nHeld.title}`);
}
{
  const base = mbModal;
  mbModal = function (title) {
    const m = base.apply(this, arguments);
    try {
      const hd = m && m.querySelector && m.querySelector(".mbm-hd");
      hd && p2nHasAsk() && !hd.querySelector("[data-p2nask]") && hd.querySelector(".mbm-x")?.insertAdjacentHTML("beforebegin", p2nAskHtml("p2n-sheet"));
      m && p2nColleagueFields(m);
    } catch (e) {
      console.warn("sheet ask", e);
    }
    return m;
  };
}

// ---- N2 Tasks: the designer's Today tile reads the one Tasks number ----------------------------------------------
// Her Today (My Day) led with "Due or Late 7", a count of design schedule items, sheets to re-issue and meeting notes
// to confirm, beside "3 due soon" on Tasks and "Due Soon 3" on the phone: three numbers for one question. The tile is
// now Due Soon, tkTasksN() (the Tasks list's own first view), and opens that view; sheets to re-issue keep a tile.
if ("object" == typeof TL_SETS && "function" == typeof TL_SETS.sday) {
  const base = TL_SETS.sday;
  TL_SETS.sday = function () {
    const T = base.apply(this, arguments) || [];
    try {
      const i = T.findIndex((x) => "due" === x.key);
      if (i < 0 || "function" != typeof tkTasksN) return T;
      const n = tkTasksN(),
        C = "function" == typeof tkMyCounts ? tkMyCounts() : {},
        late = C.overdue || 0,
        names = ("function" == typeof tkSoonFor ? tkSoonFor() : []).slice(0, 2).map((x) => String(x.title || x.name || "").replace(/ [—–-] .*$/, "")).filter(Boolean);
      T[i] = {
        key: "due",
        k: "Due Soon",
        v: n,
        tone: late ? "bad" : n ? "warn" : "",
        s: n ? `${late ? `${late} late · ` : ""}${names.map(esc).join(", ")}` : "nothing due in the next 7 days",
        rule: "Yours, late or due in the next 7 days: the Tasks list's Due Soon",
        go: () => ((tkWho = "me"), (tkProject = ""), (t2View = "week"), setView("tkall")),
      };
      let stale = 0;
      try {
        stale = (DB.projects || []).reduce((a, p) => a + ("function" == typeof sheetsOf ? sheetsOf(p.id) : []).filter((s) => s.stale && "current" === s.status).length, 0);
      } catch (e) {}
      stale && !T.some((x) => "reissue" === x.key) && T.splice(i + 1, 0, { key: "reissue", k: "To Re-Issue", v: stale, tone: "bad", s: `sheet${1 === stale ? "" : "s"} behind a newer revision`, go: () => setView("plans") });
    } catch (e) {
      console.warn("designer tasks tile", e);
    }
    return T;
  };
}

// ---- N3 Messages: one door, three tabs, one count -----------------------------------------------------------------
let p2nPane = "team";
const p2nMe = () => ("function" == typeof msgMe ? msgMe() : {}) || {};
// the site questions waiting on me (office), or my own questions answered and not yet closed (the foreman)
function p2nFieldRows() {
  try {
    if (MSG_FIELD.includes(role())) {
      if (!p2nMay("fraise")) return [];
      const me = p2nMe().name || "";
      return (((DB.field || {}).raises) || []).filter((x) => fOpen(x) && (!me || x.by === me || x.byUid === p2nMe().id));
    }
    return PRED.siteQuestionsMine.can() ? PRED.siteQuestionsMine.rows() : [];
  } catch (e) {
    return [];
  }
}
function p2nFieldN() {
  try {
    if (MSG_FIELD.includes(role())) return p2nFieldRows().filter((x) => "answered" === x.status).length;
  } catch (e) {}
  return p2nFieldRows().length;
}
const p2nTabsFor = () =>
  [
    ["team", "Team", p2nMay("chat")],
    ["mail", "Mail", p2nMay("comms")],
    ["field", "Field", MSG_FIELD.includes(role()) ? p2nMay("fraise") : (() => { try { return PRED.siteQuestionsMine.can(); } catch (e) { return !1; } })()],
  ].filter((x) => x[2]);
// The one Messages number: unread team lines, mail that needs an answer, field questions that wait on me.
function p2nMsgN() {
  const out = { team: 0, mail: 0, field: 0, n: 0 };
  try {
    const u = p2nMe();
    if (!u.id) return out;
    const T = p2nTabsFor().map((x) => x[0]);
    T.includes("team") && (out.team = msgUnreadTotal(u).n || 0);
    T.includes("mail") && (out.mail = ("function" == typeof cmNeedsAnswer ? cmNeedsAnswer() : []).length);
    T.includes("field") && (out.field = p2nFieldN());
    out.n = out.team + out.mail + out.field;
  } catch (e) {}
  return out;
}
function p2nTabsHtml(on) {
  const L = p2nTabsFor();
  if (L.length < 2) return "";
  const N = p2nMsgN();
  return `<div class="p2n-mtabs no-print" role="tablist" aria-label="Messages">${L.map(
    ([k, l]) => `<button type="button" role="tab" data-p2nmt="${k}" aria-selected="${k === on}" class="${k === on ? "on" : ""}">${l}${N[k] ? `<span class="n">${N[k]}</span>` : ""}</button>`,
  ).join("")}</div>`;
}
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("[data-p2nmt]") : null;
    if (!b) return;
    e.preventDefault(), e.stopPropagation();
    const k = b.dataset.p2nmt;
    if ("mail" === k) return void ((p2nPane = "team"), setView("comms"));
    "team" === k && "function" == typeof msgEnter && msgEnter();
    (p2nPane = k), setView("chat");
  },
  !0,
);
// opening a conversation (a notification, a row, a card) is the Team tab
if ("function" == typeof msgOpen) {
  const base = msgOpen;
  msgOpen = function () {
    return (p2nPane = "team"), base.apply(this, arguments);
  };
}
if ("function" == typeof msgEnter) {
  const base = msgEnter;
  msgEnter = function () {
    return (p2nPane = "team"), base.apply(this, arguments);
  };
}
// who a question went to, by name ("Sent to designer" read as a code)
const p2nWho = (k) => {
  try {
    const p = "function" == typeof fPerson ? fPerson(k) : null;
    if (p && p.name) return msgFirst(p.name);
  } catch (e) {}
  return k ? p2nRoleName(k) || k : "the office";
};
// the Field pane: the same rows and verbs as Today's (tdCard), so an answer here is the answer there
function p2nFieldHtml() {
  const field = MSG_FIELD.includes(role()),
    R = p2nFieldRows();
  if (field) {
    const row = (r) => {
      const p = (DB.projects || []).find((x) => x.id === r.projectId);
      return `<button type="button" class="p2n-frow" data-p2nfr="${esc(r.id)}"><span class="grow"><b data-nocase>${esc(r.title || r.type || "")}</b><span class="small muted" data-nocase>${esc([p ? shortName(p) : "", "answered" === r.status ? `Answered: ${String(r.answer || r.decision || "").slice(0, 80)}` : `Sent to ${p2nWho(r.to)} · waiting`].filter(Boolean).join(" · "))}</span></span></button>`;
    };
    return `<div class="p2n-field">${R.length ? R.map(row).join("") : '<div class="empty">No open questions from you. Raise one from the job when you need the office.</div>'}${p2nMay("fraise") ? '<div class="row" style="margin-top:12px"><button type="button" class="btn" data-p2nraise>Raise a Question</button></div>' : ""}</div>`;
  }
  return `<div class="p2n-field"><p class="small muted p2n-fieldlead">Questions from the site waiting on you to answer, the same list as Approvals' Site Questions.</p>${
    R.length
      ? R.map((it, i) => {
          const c = tdCard(it);
          return `<div class="p2n-frow" data-p2nfq="${i}"><span class="grow"><b>${c.line1}</b><span class="small muted">${c.why || ""}</span></span><button type="button" class="btn sm" data-p2nfqgo="${i}">${esc(c.verb || "Open")}</button></div>`;
        }).join("")
      : '<div class="empty">No question from the site is waiting on you.</div>'
  }</div>`;
}
document.addEventListener(
  "click",
  (e) => {
    const t = e.target && e.target.closest ? e.target : null;
    if (!t) return;
    const go = t.closest("[data-p2nfqgo], [data-p2nfq] [data-tdrec]"),
      fr = t.closest("[data-p2nfr]"),
      rs = t.closest("[data-p2nraise]");
    if (go) {
      e.preventDefault(), e.stopPropagation();
      const row = go.closest("[data-p2nfq]"),
        it = p2nFieldRows()[+(go.dataset.p2nfqgo || (row && row.dataset.p2nfq) || 0)];
      if (!it) return;
      const c = tdCard(it);
      (go.dataset.p2nfqgo ? c.run : c.go || c.run)();
    } else if (fr) {
      e.preventDefault();
      const r = (((DB.field || {}).raises) || []).find((x) => x.id === fr.dataset.p2nfr);
      r && ("function" == typeof setCurrent && setCurrent(r.projectId), setView("fraise"));
    } else if (rs) (e.preventDefault(), setView("fraise"));
  },
  !0,
);
// the page: headed Messages, the strip on top, the Field pane in place of the conversations when it is the tab
function p2nMsgPage() {
  const r = role();
  if (!MENU[r] || "client" === r) return;
  const v = document.getElementById("v-" + view);
  if ("chat" === view && v) {
    const field = "field" === p2nPane && p2nTabsFor().some((x) => "field" === x[0]);
    v.classList.toggle("p2n-fieldon", field);
    let s = v.querySelector(":scope > .p2n-mtabs");
    const html = p2nTabsHtml(field ? "field" : "team");
    s && s.remove();
    html && (v.querySelector(".msg-wrap") || v.firstChild).insertAdjacentHTML("beforebegin", html);
    let f = v.querySelector(":scope > .p2n-fieldwrap");
    if (field) {
      f || ((f = document.createElement("div")), (f.className = "p2n-fieldwrap"), (v.querySelector(".msg-wrap") || v.lastChild).after(f));
      f.innerHTML = p2nFieldHtml();
    } else f && f.remove();
    v.querySelectorAll(".ph h2, .msg-side-h h2").forEach((h) => "Chat" === h.textContent.trim() && (h.textContent = "Messages"));
    document.querySelectorAll("#crumbs b").forEach((c) => "Chat" === c.textContent.trim() && (c.textContent = "Messages"));
    field && document.body.classList.remove("msg-thread", "msg-solo-ph");
  }
  if ("comms" === view && v) {
    let s = v.querySelector(":scope > .p2n-mtabs");
    s && s.remove();
    const html = p2nTabsHtml("mail"),
      ph = v.querySelector(":scope > .ph");
    html && (ph ? ph.after(document.createRange().createContextualFragment(html)) : v.insertAdjacentHTML("afterbegin", html));
    v.querySelectorAll(":scope > .ph h2").forEach((h) => /^(Inbox|Mail)$/.test(h.textContent.trim()) && (h.textContent = "Messages"));
    document.querySelectorAll("#crumbs b").forEach((c) => /^(Inbox|Mail)$/.test(c.textContent.trim()) && (c.textContent = "Messages"));
    p2nMailNew(v);
  }
}
// one count on every door: the rail, the phone bar, the field bar, the header
if ("function" == typeof msgBadges) {
  msgBadges = function () {
    const u = p2nMe();
    if (!u.id) return;
    const tot = p2nMsgN().n;
    document.querySelectorAll('#nav-groups [data-v="chat"], [data-mv="chat"], [data-tab="chat"], [data-sub="chat"]').forEach((el) => {
      let s = el.querySelector(".n.msg-n") || el.querySelector(".n");
      !s && tot && ((s = document.createElement("span")), (s.className = "n msg-n"), el.appendChild(s));
      s && (s.textContent = tot ? String(tot) : "");
    });
  };
}
if ("function" == typeof mnChat) {
  const base = mnChat;
  mnChat = function () {
    const r = base.apply(this, arguments);
    try {
      const a = document.getElementById("tb-chat");
      if (a) {
        const n = a.hidden ? 0 : p2nMsgN().n,
          sp = a.querySelector("span:not(.msg-n)"),
          c = a.querySelector(".msg-n");
        sp && (sp.textContent = "Messages"), (a.title = "Messages");
        c && (c.textContent = n ? String(n) : "");
        a.setAttribute("aria-label", n ? `Messages, ${n} unread` : "Messages");
        a.classList.toggle("on", ["chat", "comms"].includes(view));
      }
    } catch (e) {}
    return r;
  };
}
// the menu's Messages entry carries the same number
if ("function" == typeof mnItemN) {
  const base = mnItemN;
  mnItemN = function (it) {
    if (it && !it.tab && "chat" === it.v) return p2nMsgN().n;
    return base.apply(this, arguments);
  };
}

// ---- N3 read marks on a team thread: "Seen by Chen, Angel", else Sent ---------------------------------------------
// A direct thread already said Read. A group or a job's team thread said nothing, so the sender chased by phone what
// had already been read. Each member's read row (who, how far, when) is kept with the thread: a group's on its shared
// row (t.read, as a direct thread's), a job team thread's in DB.msgReads, never on the job.
const p2nReadRow = (T) => {
  if (!T) return null;
  if (T.t) return "group" === T.kind ? (T.t.read = T.t.read || {}) : null;
  if ("job" !== T.kind) return null;
  const R = (DB.msgReads = DB.msgReads && "object" == typeof DB.msgReads ? DB.msgReads : {});
  return (R[T.key] = R[T.key] || {});
};
if ("function" == typeof msgSeenSet) {
  const base = msgSeenSet;
  msgSeenSet = function (T, u) {
    const r = base.apply(this, arguments);
    try {
      if (T && u && msgIn(T, u) && !msgIsClient(u)) {
        const row = p2nReadRow(T);
        if (row) {
          const all = T.all(),
            last = all[all.length - 1],
            cur = row[u.id];
          if (!cur || cur.n !== all.length) return (row[u.id] = { id: last ? last.id : "", n: all.length, at: appNowIso() }), !0;
        }
      }
    } catch (e) {}
    return r;
  };
}
// who in the thread has read up to my last line (not me, not the assistant), in the order they read it
function p2nSeenBy(T, u) {
  const row = p2nReadRow(T);
  if (!row) return null;
  const all = T.all(),
    vis = all.filter((m) => msgVisible(m, T, u)),
    mine = vis.filter((m) => msgMine(m, u) && !m.system),
    last = mine[mine.length - 1];
  if (!last) return null;
  const k = all.indexOf(last);
  return Object.keys(row)
    .filter((id) => id !== u.id && (+row[id].n || 0) > k)
    .sort((a, b) => String(row[a].at || "").localeCompare(String(row[b].at || "")))
    .map((id) => (msgUser(id) || {}).name)
    .filter(Boolean);
}
if ("function" == typeof renderChat) {
  const base = renderChat;
  renderChat = function () {
    const r = base.apply(this, arguments);
    try {
      const u = p2nMe(),
        T = msgCur(u),
        list = document.getElementById("chat-list");
      if (T && list && !msgIsClient(u) && ("group" === T.kind || "job" === T.kind)) {
        const names = p2nSeenBy(T, u),
          mine = [...list.querySelectorAll(".cm.me:not(.sys)")].pop();
        if (mine && names) {
          // under the bubble, in the page's own ink (inside the accent bubble it could not be read)
          const t = mine.querySelector(".msg-bub");
          t &&
            !mine.querySelector(".p2n-seen") &&
            t.insertAdjacentHTML(
              "afterend",
              `<span class="p2n-seen small" title="${names.length ? "Read by" : "Sent; nobody has read it yet"}">${names.length ? `Seen by ${esc(names.map(msgFirst).join(", "))}` : "Sent"}</span>`,
            );
        }
      }
    } catch (e) {
      console.warn("seen by", e);
    }
    return r;
  };
}

// ---- N3 Today: what is addressed to me in Team chat -----------------------------------------------------------------
// A direct line or an @mention to me that I have not read is a Today row (Inbox filter), with Reply; read, it leaves.
function p2nChatItems() {
  const u = p2nMe();
  if (!u.id || !p2nMay("chat")) return [];
  const out = [];
  try {
    msgThreadsFor(u).forEach((T) => {
      const un = msgUnread(T, u);
      if (!un.n) return;
      const direct = !!(T.t && "direct" === T.kind);
      if (!direct && !un.at) return;
      const vis = T.all().filter((m) => msgVisible(m, T, u) && !msgMine(m, u)),
        m = (direct ? vis : vis.filter((x) => (x.mentions || []).includes(u.id))).pop();
      if (!m) return;
      out.push({
        kind: "tdyChat",
        id: T.key,
        src: "chat",
        key: T.key,
        title: `${msgFirst(m.by) || "Someone"}: ${String(msgPreview(m, u) || "").slice(0, 80)}`,
        detail: [direct ? "Direct message" : `Mentioned you · ${T.title}`, msgClock(m)].filter(Boolean).join(" · "),
        due: "",
      });
    });
  } catch (e) {
    console.warn("today chat", e);
  }
  return out;
}
if ("function" == typeof tdyModel) {
  const base = tdyModel;
  tdyModel = function () {
    const M = base.apply(this, arguments);
    try {
      const C = p2nChatItems();
      if (C.length && M && Array.isArray(M.inbox)) {
        M.inbox = C.concat(M.inbox);
        const i = M.all.findIndex((it) => "tdyMail" === it.kind),
          j = i < 0 ? M.all.findIndex((it) => !M.appr.includes(it)) : i;
        M.all.splice(j < 0 ? M.all.length : j, 0, ...C);
      }
    } catch (e) {}
    return M;
  };
}
if ("function" == typeof tdCard) {
  const base = tdCard;
  tdCard = function (it) {
    if (!it || "tdyChat" !== it.kind) return base.apply(this, arguments);
    const go = () => msgOpen(it.key);
    return { line1: `<a href="#" data-tdrec>${esc(it.title)}</a>`, why: esc(it.detail), verb: "Reply", go: go, run: go };
  };
}

// ---- N4 one Clients directory: Clients, People and Companies are tabs of one page --------------------------------
const P2N_DIR = [
  ["clients", "Clients"],
  ["hbcontacts", "People"],
  ["hbcompanies", "Companies"],
];
function p2nDirTabs() {
  if (!["clients", "hbcontacts", "hbcompanies"].includes(view) || !MENU[role()]) return;
  const v = document.getElementById("v-" + view);
  if (!v) return;
  if ("clients" === view && "undefined" != typeof clientOpen && clientOpen) return void v.querySelector(":scope > .p2n-dtabs")?.remove();
  const L = P2N_DIR.filter(([k]) => p2nMay(k));
  v.querySelector(":scope > .p2n-dtabs")?.remove();
  if (L.length < 2) return;
  v.insertAdjacentHTML(
    "afterbegin",
    `<div class="p2n-dtabs p2n-mtabs no-print" role="tablist" aria-label="Clients">${L.map(([k, l]) => `<button type="button" role="tab" data-p2ndir="${k}" aria-selected="${k === view}" class="${k === view ? "on" : ""}">${l}</button>`).join("")}</div>`,
  );
  // one page, one name: the heading is the directory's
  v.querySelectorAll(".ph h2, .hb-h1, h1").forEach((h) => /^(People|Companies|Contacts)$/.test(h.textContent.trim()) && !h.querySelector("input,select") && (h.dataset.p2nwas = h.textContent.trim(), (h.textContent = "Clients")));
  document.querySelectorAll("#crumbs b").forEach((c) => /^(People|Companies|Contacts)$/.test(c.textContent.trim()) && (c.textContent = "Clients"));
}
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("[data-p2ndir]") : null;
    if (!b) return;
    e.preventDefault(), e.stopPropagation();
    "clients" === b.dataset.p2ndir && "undefined" != typeof clientOpen && (clientOpen = null);
    setView(b.dataset.p2ndir);
  },
  !0,
);

// ---- N4 the Team page: every staff member, phone and email, Message and Email ---------------------------------
const P2N_DEMO_PHONE = { u_owner: "(917) 555-0100", u_alan: "(917) 555-0101", u_chen: "(917) 555-0102", u_sarah: "(917) 555-0103", u_billing: "(917) 555-0104", u_controller: "(917) 555-0105", u_angel: "(917) 555-0106", u_alberto: "(917) 555-0107", u_alex: "(917) 555-0108", u_satish: "(917) 555-0109" };
// The demo's people get invented phones (the 555-01xx range) and the demo workspace's addresses, once, demo only.
function p2nTeamSeed() {
  if ("function" == typeof sdSeedsOff && sdSeedsOff()) return !1;
  if (DB.__p2nTeamSeed) return !1;
  DB.__p2nTeamSeed = 1;
  const D = "undefined" != typeof DW_STAFF ? DW_STAFF : {};
  (DB.users || []).forEach((u) => {
    if (!u || !u.id || "client" === u.role || /^mb_/.test(u.role || "")) return;
    !u.email && D[u.id] && (u.email = D[u.id][1]);
    !u.phone && P2N_DEMO_PHONE[u.id] && (u.phone = P2N_DEMO_PHONE[u.id]);
  });
  return !0;
}
// one person: their sign-in (if any) and their employee record (if any), joined by employeeId or name
const p2nRoleName = (r) => ("undefined" != typeof ROLE_NAMES && ROLE_NAMES[r]) || r || "";
function p2nTeam() {
  const out = [],
    seen = new Set();
  (DB.users || [])
    .filter((u) => u && u.id && u.name && "client" !== u.role && !/^mb_/.test(u.role || "") && !u.mb)
    .forEach((u) => {
      const e = (DB.employees || []).find((x) => x.id === (u.employeeId || u.empId)) || null;
      e && seen.add(e.id), seen.add("n:" + u.name.toLowerCase());
      out.push({ id: u.id, uid: u.id, name: u.name, role: (e && e.role) || p2nRoleName(u.role), email: u.email || (/@/.test(u.contact || "") ? u.contact : "") || (e && e.email) || "", phone: u.phone || (e && e.phone) || "" });
    });
  (DB.employees || [])
    .filter((e) => e && !1 !== e.active && !seen.has(e.id) && !seen.has("n:" + String(e.name || "").toLowerCase()))
    .forEach((e) => out.push({ id: "em:" + e.id, uid: "", name: e.name, role: e.role || "Team", email: e.email || "", phone: e.phone || "" }));
  return out;
}
// the person as a mail address: "Chen Biron <chen@...>"
const p2nAddr = (p) => (p.email ? `${p.name} <${p.email}>` : "");
function p2nTeamHtml() {
  const me = p2nMe(),
    T = p2nTeam(),
    q = String(p2nTeamQ || "").trim().toLowerCase(),
    rows = T.filter((p) => !q || [p.name, p.role, p.email, p.phone].join(" ").toLowerCase().includes(q)),
    can = p2nMay("chat");
  return `<div class="ph"><div><h2>Team</h2><div class="lead">Everyone at the firm, with their phone and email. Message them here, or pick them in any email's To and Cc.</div></div></div>
  <label class="p2n-tq"><input type="search" id="p2n-tq" placeholder="Search the team" aria-label="Search the team" value="${esc(p2nTeamQ)}" autocomplete="off"></label>
  <div class="p2n-team">${
    rows
      .map(
        (p) => `<div class="p2n-person" data-p2nperson="${esc(p.id)}">${"function" == typeof msgAvatar ? msgAvatar(p.uid || p.id, p.name) : ""}<div class="grow p2n-pmid"><b data-nocase>${esc(p.name)}${p.uid === me.id ? " (you)" : ""}</b><span class="small muted" data-nocase>${esc(p.role)}</span><span class="small p2n-pc" data-nocase>${p.phone ? `<a href="tel:${esc(p.phone.replace(/[^\d+]/g, ""))}">${esc(p.phone)}</a>` : '<span class="muted">no phone on file</span>'}${p.email ? ` · <a href="mailto:${esc(p.email)}">${esc(p.email)}</a>` : ' · <span class="muted">no email on file</span>'}</span></div><div class="p2n-pact">${
          can && p.uid && p.uid !== me.id ? `<button type="button" class="btn sm" data-p2nmsg="${esc(p.uid)}">Message</button>` : ""
        }${p.email && p2nMay("comms") && p.uid !== me.id ? `<button type="button" class="btn sm" data-p2nmail="${esc(p.id)}">Email</button>` : ""}${p.uid && canEditTeam() ? `<button type="button" class="btn sm ghost" data-p2nedit="${esc(p.uid)}">Edit</button>` : ""}</div></div>`,
      )
      .join("") || '<div class="empty">Nobody matches.</div>'
  }</div>`;
}
let p2nTeamQ = "";
const canEditTeam = () => ["owner"].includes(role()) || ("function" == typeof isOwner && isOwner());
function renderP2nTeam() {
  const v = document.getElementById("v-team");
  if (!v) return;
  const had = document.activeElement && "p2n-tq" === document.activeElement.id;
  v.innerHTML = p2nTeamHtml();
  if (had) {
    const q = document.getElementById("p2n-tq");
    q && (q.focus(), q.setSelectionRange(q.value.length, q.value.length));
  }
  // a firm page, not a job's: the trail names it
  const cr = document.getElementById("crumbs");
  cr && !cr.querySelector("input,select") && (cr.innerHTML = "<b>Team</b>");
  const q = v.querySelector("#p2n-tq");
  q && (q.oninput = () => ((p2nTeamQ = q.value), renderP2nTeam()));
}
document.addEventListener(
  "click",
  (e) => {
    const t = e.target && e.target.closest ? e.target : null;
    if (!t) return;
    const m = t.closest("[data-p2nmsg]"),
      ml = t.closest("[data-p2nmail]"),
      ed = t.closest("[data-p2nedit]"),
      tm = t.closest("[data-p2nteam]");
    if (m) {
      e.preventDefault(), e.stopPropagation();
      const T = msgDirectWith(m.dataset.p2nmsg, !0);
      save(), msgOpen(T.key);
      const who = (msgUser(m.dataset.p2nmsg) || {}).name || "them";
      toast(`Chat with ${msgFirst(who)} is open`, () => msgOpen(T.key));
      setTimeout(() => document.getElementById("chat-text")?.focus(), 0);
    } else if (ml) {
      e.preventDefault(), e.stopPropagation();
      const p = p2nTeam().find((x) => x.id === ml.dataset.p2nmail);
      p && p2nCompose({ to: p2nAddr(p) });
    } else if (ed) {
      e.preventDefault(), e.stopPropagation();
      p2nEditPerson(ed.dataset.p2nedit);
    } else if (tm) (e.preventDefault(), e.stopPropagation(), setView("team"));
  },
  !0,
);
function p2nEditPerson(uid0) {
  const u = (DB.users || []).find((x) => x.id === uid0);
  if (!u) return;
  mbModal(`${esc(u.name)}: Phone and Email`, `${mbF("Phone", mbIn("phone", u.phone || "", "(917) 555-0100", "tel"))}${mbF("Email", mbIn("email", u.email || "", "name@smartdesign.nyc", "email"))}`, {
    submit: "Save",
    onSubmit: (f) => {
      if (f.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(f.email)) return toast("That email does not look right"), !1;
      const was = { phone: u.phone || "", email: u.email || "" };
      (u.phone = f.phone), (u.email = f.email);
      try {
        audit("user", u.id, "contact", JSON.stringify(was), JSON.stringify({ phone: u.phone, email: u.email }), `${p2nMe().name || "Someone"} changed ${u.name}'s phone and email`);
      } catch (e) {}
      save(), render(), toast(`${u.name}'s phone and email saved`, () => setView("team"));
    },
  });
}
// every mail To, Cc and Bcc field offers the team by name: "Chen" finds Chen Biron <chen@...>
function p2nColleagueList() {
  let dl = document.getElementById("p2n-colleagues");
  dl || ((dl = document.createElement("datalist")), (dl.id = "p2n-colleagues"), document.body.appendChild(dl));
  const me = p2nMe();
  dl.innerHTML = p2nTeam()
    .filter((p) => p.email && p.uid !== me.id)
    .map((p) => `<option value="${esc(p2nAddr(p))}">${esc(p.role)}</option>`)
    .join("");
  return dl;
}
function p2nColleagueFields(root) {
  const F = [...root.querySelectorAll('input[data-f="to"], input[data-f="cc"], input[data-f="bcc"]')].filter((i) => !i.type || ["text", "email", "search"].includes(i.type));
  if (!F.length) return;
  p2nColleagueList();
  F.forEach((i) => i.getAttribute("list") || i.setAttribute("list", "p2n-colleagues"));
}
// a colleague named by first name or full name in a To or Cc reads as their address
function p2nResolve(s) {
  const T = p2nTeam().filter((p) => p.email);
  return String(s || "")
    .split(/[,;]+/)
    .map((x) => x.trim())
    .filter(Boolean)
    .map((x) => {
      if (/@/.test(x)) return x;
      const k = x.toLowerCase(),
        hit = T.filter((p) => p.name.toLowerCase() === k || p.name.toLowerCase().split(/\s+/)[0] === k);
      return 1 === hit.length ? p2nAddr(hit[0]) : x;
    });
}
// New Email (Messages > Mail): written by the person, kept as a draft they send (AI assists, people send)
function p2nCompose(pre) {
  pre = pre || {};
  mbModal(
    "New Email",
    `${mbF("To", mbIn("to", pre.to || "", "Name or email; Chen finds Chen Biron"))}${mbF("Cc", mbIn("cc", pre.cc || "", "Name or email"))}${mbF("Subject", mbIn("subject", pre.subject || "", ""))}${mbF("Message", `<textarea data-f="body" rows="7">${esc(pre.body || "")}</textarea>`)}<p class="small muted" style="margin:0">Saved as a draft for you to send; it waits on your Today until you do.</p>`,
    {
      submit: "Save Draft",
      onSubmit: (f) => {
        const to = p2nResolve(f.to),
          cc = p2nResolve(f.cc),
          bad = to.concat(cc).filter((x) => !/@/.test(x));
        if (!to.length) return toast("Who does it go to?"), !1;
        if (bad.length) return toast(`No address for ${bad.join(", ")}: add it on Team or type the email`), !1;
        if (!f.subject) return toast("Give it a subject"), !1;
        const me = p2nMe(),
          nm = (a) => (/^(.*?)\s*<(.+)>$/.exec(a) || [null, "", a]),
          first = nm(to[0]);
        DB.outbox = DB.outbox || [];
        const o = {
          id: uid("ox"),
          kind: "email",
          to: { name: first[1] || first[2], email: first[2] },
          toAll: to,
          cc: cc,
          subject: f.subject,
          body: f.body || "",
          about: { label: f.subject },
          aboutKey: "mail|" + uid("m"),
          forName: me.name || "",
          forUid: me.id || "",
          status: "draft",
          at: today(),
          by: me.name || "",
        };
        DB.outbox.push(o);
        try {
          audit("outbox", o.id, "draft", "", to.concat(cc).join(", "), `${me.name || "Someone"} wrote a draft`);
        } catch (e) {}
        save(), render();
        toast(`Draft to ${to.map((a) => msgFirst(nm(a)[1] || nm(a)[2])).join(", ")} saved; send it from Today`, () => setView("home"));
      },
    },
  );
}
function p2nMailNew(v) {
  if (v.querySelector("[data-p2nnewmail]")) return;
  const bar = v.querySelector(".ib-bar") || v.querySelector("#comms-body");
  bar && bar.insertAdjacentHTML("afterbegin", '<button type="button" class="btn sm" data-p2nnewmail>New Email</button>');
}
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("[data-p2nnewmail]") : null;
    b && (e.preventDefault(), e.stopPropagation(), p2nCompose());
  },
  !0,
);
// every staff role may open Team. Run again at boot and sign-in: the designer's and the foreman's lists are rebuilt by
// sections that load after this one (menu_test found Team missing for them).
function p2nTeamViews() {
  ["owner", "pm", "coord", "designer", "design_mgr", "billing", "controller", "foreman", "crew", "driver"].forEach((r) => ROLE_VIEWS[r] && !ROLE_VIEWS[r].includes("team") && ROLE_VIEWS[r].push("team"));
}
// the page itself and who may open it: every staff role
(() => {
  if (!document.getElementById("v-team")) {
    const sec = document.createElement("section");
    (sec.className = "view"), (sec.id = "v-team");
    (document.getElementById("v-chat") || document.querySelector(".view"))?.parentElement?.appendChild(sec);
  }
  p2nTeamViews();
  "object" == typeof NAV_LABELS && (NAV_LABELS.team = "Team");
  "object" == typeof IA_LABELS && (IA_LABELS.team = "Team");
  "object" == typeof NAV_LABELS && (NAV_LABELS.chat = "Messages");
  "object" == typeof IA_LABELS && (IA_LABELS.chat = "Messages");
  "function" == typeof mnKnow && (mnKnow("team", "Team"), mnKnow("chat", "Messages"), mnKnow("chat", "Chat"), mnKnow("comms", "Inbox"), mnKnow("comms", "Messages"));
  "object" == typeof MN_HOMEGROUP && ((MN_HOMEGROUP.team = "Company"), (MN_HOMEGROUP.chat = "Messages"));
  // the query layer's People (eqPeople, Ask's "what is Chen's phone") reads the team's phone and email from here
  if ("function" == typeof eqPeople) {
    const base = eqPeople;
    eqPeople = function () {
      const R = base.apply(this, arguments) || [];
      try {
        const T = p2nTeam();
        R.forEach((x) => {
          const p = T.find((t) => t.name === x.name && (String(x.id || "").startsWith("em:") || String(x.id || "").startsWith("us:")));
          p && (x.phone = x.phone || p.phone, x.email = x.email || p.email);
        });
      } catch (e) {}
      return R;
    };
  }
})();

// ---- N3/N4/N5 the menus ---------------------------------------------------------------------------------------------
// Messages after Tasks for every office role; Inbox leaves Today's group (it is Messages > Mail); People and Companies
// leave Sales (they are Clients' tabs); Team joins Company; the foreman's bar takes Requests; Chat reads Messages.
(() => {
  // the rail's mark for Messages: the two square bubbles of the header's and the bar's Messages (never Ask's sparkle)
  "object" == typeof MN_ICON && (MN_ICON.chat = '<path d="M14 9a2 2 0 0 1-2 2H6l-3 3V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2z"/><path d="M18 9h1a2 2 0 0 1 2 2v9l-3-3h-6a2 2 0 0 1-2-2v-1"/>');
  const MSG_G = () => MN_G("msgs", "Messages", "chat", [["chat", "Messages"]]);
  const office = ["owner", "pm", "coord", "billing", "controller", "designer", "design_mgr"];
  office.forEach((r) => {
    const M = MENU[r];
    if (!M || !M.groups) return;
    M.groups = M.groups.map((g) => {
      const items = g.items.filter((x) => !(Array.isArray(x) && ("home" === g.id ? "comms" === x[0] : "sales" === g.id && ["hbcontacts", "hbcompanies"].includes(x[0]))));
      "office" === g.id && !items.some((x) => Array.isArray(x) && "team" === x[0]) && items.splice(Math.min(2, items.length), 0, ["team", "Team"]);
      return Object.assign({}, g, { items: items });
    });
    const i = M.groups.findIndex((g) => "mytasks" === g.id);
    M.groups.some((g) => "msgs" === g.id) || M.groups.splice(i < 0 ? 1 : i + 1, 0, MSG_G());
    (M.phone || []).forEach((x) => "chat" === x[0] && (x[1] = "Messages"));
  });
  ["foreman", "crew", "driver"].forEach((r) => {
    const M = MENU[r];
    M && (M.bar || []).forEach((x) => "chat" === x[0] && (x[1] = "Messages"));
    // Team is placed at the foot of the field menu (the colleague to call), not left to fall under More
    M && M.rest && !M.rest.some((x) => "team" === x[0]) && M.rest.push(["team", "Team", "people"]);
  });
  // the foreman: Requests on the bar (Today shows his hours to approve; Crew stays under the rest). The bar keeps four
  // shortcuts (Alan, 2026-10-19: "a max of 4"), so Site, the one the synthesis ranks below Daily Log, leads the rest.
  const F = MENU.foreman;
  F &&
    ((F.bar = [
      ["ftoday", "Today", "home"],
      ["flog", "Daily Log", "list"],
      ["req", "Requests", "box"],
      ["chat", "Messages", "chat"],
    ]),
    (F.rest = [["fsite", "Site", "box"]].concat((F.rest || []).filter((x) => !["req", "fsite"].includes(x[0])))));
  "object" == typeof MN_ALIAS && Object.assign(MN_ALIAS, { comms: "chat", hbcontacts: "clients", hbcompanies: "clients" });
  "undefined" != typeof MN_BUTTON && MN_BUTTON.delete && MN_BUTTON.delete("chat");
  try {
    "function" == typeof mnKnowAll && mnKnowAll();
    "function" == typeof mnHomeGroups && mnHomeGroups();
  } catch (e) {}
})();

// ---- N5 the owner's Today opens on Approvals when anything waits on him ------------------------------------------
let p2nLastView = "";
{
  const base = render;
  render = function () {
    try {
      if ("home" === view && "home" !== p2nLastView && "owner" === role() && "undefined" != typeof tdyTabs) {
        const me = tdyMe(),
          k = me.id || role(),
          n = (tdyModel().appr || []).length;
        n && ((tdyTabs[k] = "appr"), (tdyLanding = "appr"), (tdyAllOpen = !1));
      }
    } catch (e) {}
    p2nLastView = view;
    const r = base.apply(this, arguments);
    try {
      p2nMsgPage(), p2nDirTabs(), "team" === view && renderP2nTeam(), p2nPayrollStatus();
      p2nAskOwnHeads(), p2nResumeBar(), msgBadges();
    } catch (e) {
      console.warn("p2nav", e);
    }
    return r;
  };
}
if ("function" == typeof signIn) {
  const base = signIn;
  signIn = function () {
    p2nLastView = "";
    try {
      p2nTeamViews();
    } catch (e) {}
    return base.apply(this, arguments);
  };
}

// ---- N5 payroll: one run record, in Bills & Payroll ----------------------------------------------------------------
// The coordinator built a payroll run from Time & Crew that was not the controller's. The run is built and approved in
// Bills & Payroll; her Time & Crew shows the entries and the latest run's status and who holds it, read-only.
function p2nPayrollStatus() {
  if ("time" !== view || "coord" !== role()) return;
  const b = document.getElementById("btn-payrollfromtime");
  b && (b.style.display = "none");
  const v = document.getElementById("v-time");
  if (!v) return;
  let c = document.getElementById("p2n-payrun");
  const R = (DB.payroll || []).slice().sort((a, b2) => String(b2.to || b2.payDate || "").localeCompare(String(a.to || a.payDate || "")))[0],
    held = !R
      ? "No payroll run yet. The controller builds it in Bills & Payroll from the approved hours."
      : "approved" === R.status || "paid" === R.status
        ? `Approved${R.approvedBy ? ` by ${R.approvedBy}` : ""}${R.payDate ? `, paid ${fmt(R.payDate)}` : ""}.`
        : `${"draft" === R.status ? "Being prepared by the controller" : "Waiting on the owner's approval"}${R.payDate ? `, to be paid ${fmt(R.payDate)}` : ""}.`,
    open = (DB.time || []).filter((t) => "approved" === t.status && !t.payrollId).length,
    sub = (DB.time || []).filter((t) => "submitted" === t.status).length;
  c || ((c = document.createElement("div")), (c.id = "p2n-payrun"), (c.className = "card p2n-payrun"), (document.getElementById("time-kpis") || v.querySelector(".ph") || v).after(c));
  c.innerHTML = `<div class="hd"><h3>Payroll Run</h3></div><p style="margin:0 0 4px"><b>${R ? esc(R.period || `${fmt(R.from)} to ${fmt(R.to)}`) : "None yet"}</b> · ${esc(held)}</p><p class="small muted" style="margin:0">${sub} entr${1 === sub ? "y" : "ies"} to approve · ${open} approved and not in a run yet. The run is built and approved in Bills & Payroll, not here.</p>`;
}

// ---- boot ---------------------------------------------------------------------------------------------------------
if ("function" == typeof finishBoot) {
  const base = finishBoot;
  finishBoot = function () {
    const r = base.apply(this, arguments);
    try {
      p2nTeamViews();
      p2nTeamSeed() && save();
    } catch (e) {
      console.warn("team seed", e);
    }
    return r;
  };
}
