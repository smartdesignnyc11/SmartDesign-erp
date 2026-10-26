/*<<fbsession.js>>*/
/* ==== Record a Feedback Session (Alan, 2026-10-26) ===================================================================
   "One of the best ways to improve this site is for me to record my screen and talk about what is working and what
   isn't. Create the same start meeting feature to record exactly where in the site I am and what I'm clicking and
   looking at, with a time stamp that matches my transcript time stamp."
   The person records their screen and voice with their own tool (Google Meet, the phone's recorder, Loom) and gets a
   transcript with times. This file records the other half: every page, tap, field, scroll, toast, error and Mark, with
   the device's own clock, and lines the transcript up against it.

   Design gate (BACKLOG §1.16). The noun is the Problem Report (Report a Problem, view rpbox, src/app.js rp*): a
   finished session is a report of kind "session". Nothing new is added to the menu:
     - rpAll() lists the person's own sessions with every other report, so Problem Reports stays the one list; rpCard,
       rpMd, rpSave and rpPatch learn the kind. A session never goes through rpPut: it is not a shared report and never
       becomes one of the loop's shared signals.
     - Where a finished session is kept: DB.rpSessions, one store with a reason. Report a Problem keeps its reports in
       the device's localStorage (5 MB, shared by every report, too small for a log of an hour) and in two shared
       places (the artifact's shared list, the loop's signals). A session is the person's own record, like their mail:
       every session carries its owner, and on the hosted copy platform/public/cloud.js files rpSessions as a private
       list (own:<person>:rpSessions), never a shared row. Only its owner sees it, on the local copy too.
     - While it records, the live session sits in IndexedDB (the "smartdesigns" kv store the app already persists DB
       in, key fbs:live), written as it goes, so a reload or a crash keeps it and the session carries on.
     - The session's own page (view "fbs") is a record page, like an estimate's: reached from the toast's Open, the
       report's card, Report a Problem and the menu's foot; not a menu entry (menu_test: MN_BUTTON).
   The start: Record a Feedback Session sits in the Report a Problem panel, on Problem Reports and at the foot of the
   menu (the phone's Today has no Report a Problem in its header, so the menu's foot is the way in on every screen),
   for every staff role, styled as Start Meeting.

   THE CLOCK. The app has one clock (today(), appNow(): the demo's day is pinned to 2026-09-03) and every record is
   stamped with it. The session's events are the one deliberate exception: they carry the device's real wall-clock time
   (fbsWallIso: ISO with the time zone, to the millisecond) and the seconds since the session started, because they must
   line up with a recording made outside the app, whose transcript runs on real time. Nothing else is ever stamped this
   way: the report itself (r.at) and everything it touches use appNowIso().

   PRIVACY. Nothing typed is captured: a field gives its label and the length typed, never the value (no money, no
   passwords, no bank data, no client text). A control gives its visible label (or aria-label), with amounts, long
   numbers, emails and phone numbers masked. Records appear as their numbers and titles, as on screen. Nothing leaves
   the device except by Download Session / Export Timeline, or the hosted copy's private sync.
--------------------------------------------------------------------------------------------------------------------- */
const FBS_KEY = "fbs:live",
  FBS_MAX_EVENTS = 8000;
let fbsLive = null, // the session recording on this device
  fbsOpenId = "", // the session on the fbs page
  fbsLastKey = "",
  fbsLastHeads = "",
  fbsSaveT = null,
  fbsTickT = null,
  fbsPollT = null,
  fbsScrollT = null,
  fbsFlash = "",
  fbsFlashT = null,
  fbsLastSaveMsg = "",
  fbsOwnToast = !1;
const fbsP2 = (n) => String(Math.floor(n)).padStart(2, "0");
// The device's wall clock, never the app's (see THE CLOCK above): only a session's events are stamped with it.
function fbsWallIso(ms) {
  const d = new Date(ms),
    off = -d.getTimezoneOffset(),
    a = Math.abs(off);
  return `${d.getFullYear()}-${fbsP2(d.getMonth() + 1)}-${fbsP2(d.getDate())}T${fbsP2(d.getHours())}:${fbsP2(d.getMinutes())}:${fbsP2(d.getSeconds())}.${String(d.getMilliseconds()).padStart(3, "0")}${off >= 0 ? "+" : "-"}${fbsP2(a / 60)}:${fbsP2(a % 60)}`;
}
// "10:14:02 AM" on the device's clock, for the page
const fbsClock = (ms) => new Date(ms).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", second: "2-digit" });
const fbsDur = (sec) => {
  const s = Math.max(0, Math.floor(sec || 0)),
    h = Math.floor(s / 3600);
  return h ? `${h}:${fbsP2((s % 3600) / 60)}:${fbsP2(s % 60)}` : `${fbsP2(s / 60)}:${fbsP2(s % 60)}`;
};
const fbsHms = (sec) => {
  const neg = sec < 0,
    s = Math.abs(Math.round(sec || 0));
  return `${neg ? "-" : ""}${fbsP2(s / 3600)}:${fbsP2((s % 3600) / 60)}:${fbsP2(s % 60)}`;
};
// where the transcript's 00:00:00 falls: after the session started, or before it
const fbsShift = (sec) => {
  const x = Math.round(Math.abs(sec || 0) * 10) / 10;
  return sec < 0 ? `the transcript's 00:00:00 is ${x} s before the session started` : `the transcript's 00:00:00 is ${x} s into the session`;
};
const fbsMinutes = (sec) => {
  const m = Math.round((sec || 0) / 60);
  return m < 1 ? `${Math.max(1, Math.round(sec || 0))} s` : `${m} min`;
};
const FBS_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"];
const FBS_ROLE = { owner: "Owner", pm: "Project manager", coord: "Coordinator", foreman: "Foreman", crew: "Crew", driver: "Driver", designer: "Designer", design_mgr: "Design director", billing: "Billing", controller: "Controller", mb_user: "Mercer & Bond", mb_analyst: "Mercer & Bond analyst" };
const fbsMe = () => {
  try {
    return ("function" == typeof tdyMe ? tdyMe() : null) || ("function" == typeof currentUser ? currentUser() : null) || {};
  } catch (e) {
    return {};
  }
};
const fbsStaff = () => {
  try {
    return "client" !== role();
  } catch (e) {
    return !1;
  }
};
const fbsPhone = () => ("function" == typeof vw ? vw() : innerWidth) < 820;
// what is said aloud is never typed text, but a label or a heading can carry an amount or a number: masked the way
// Report a Problem masks its trail
function fbsMask(s, n) {
  return String(s == null ? "" : s)
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\$\s?\d[\d,]*(\.\d+)?[kKmM]?/g, "$…")
    .replace(/\b[\w.%+-]+@[\w.-]+\.[a-z]{2,}\b/gi, "[email]")
    .replace(/\(?\b\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b/g, "[phone]")
    .replace(/\b\d{7,}\b/g, "…")
    .slice(0, n || 80);
}
const fbsTxt = (el) => (el ? (el.innerText || el.textContent || "").replace(/\s+/g, " ").trim() : "");
const fbsVis = (el) => !!el && el.getClientRects().length > 0 && "hidden" !== getComputedStyle(el).visibility;
function fbsDevice() {
  const ua = navigator.userAgent || "";
  return {
    kind: fbsPhone() ? "phone" : "desktop",
    viewport: `${innerWidth}x${innerHeight}`,
    platform: /iPhone|iPad/.test(ua) ? "iOS" : /Android/.test(ua) ? "Android" : /Mac/.test(ua) ? "Mac" : /Windows/.test(ua) ? "Windows" : /Linux/.test(ua) ? "Linux" : "other",
    browser: /Edg\//.test(ua) ? "Edge" : /CriOS|Chrome/.test(ua) ? "Chrome" : /Firefox/.test(ua) ? "Firefox" : /Safari/.test(ua) ? "Safari" : "other",
    touch: !!("ontouchstart" in window || navigator.maxTouchPoints > 0),
    tz: (() => {
      try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone || "";
      } catch (e) {
        return "";
      }
    })(),
  };
}

// ---- where the person is: the page, its heading, the record open, the tab, the sheet or panel on top ---------------
const FBS_OVER = "#mbm, #drawer.on, #rp-panel, #ai.on, [role=dialog], .sheet.on, .m-sheet.on, .bsheet.on, .tks-sheet, .modal.on";
function fbsOver() {
  const L = [...document.querySelectorAll(FBS_OVER)].filter((el) => fbsVis(el) && !el.closest("[data-fbs], #fbs-bar"));
  const el = L[L.length - 1];
  if (!el) return null;
  const h = el.querySelector("#d-title, h2, h3, .rp-hd h3, [class*=title], [class*=-hd] b, legend");
  const kind = "drawer" === el.id ? "panel" : "rp-panel" === el.id ? "panel" : "ai" === el.id ? "assistant" : "sheet";
  return { kind: kind, title: fbsMask(fbsTxt(h) || el.getAttribute("aria-label") || "", 70) };
}
function fbsHeading() {
  const v = document.querySelector(".view.on");
  // the page's own heading is its first; when the phone hides it (Today, the Buy Board), the header's title says it
  const first = v && v.querySelector(".ph h2, h1, h2"),
    h = first && fbsVis(first) ? first : null;
  const crumbs = document.querySelector("#crumbs b") || document.getElementById("crumbs");
  return fbsMask(fbsTxt(h) || fbsTxt(crumbs) || ("object" == typeof NAV_LABELS && NAV_LABELS[view]) || view, 70);
}
function fbsTab() {
  const sub = [...document.querySelectorAll("#subnav .on, .sub-tabs .on")].find(fbsVis),
    seg = [...document.querySelectorAll(".view.on .seg .on, .view.on .ctabs .on, .view.on [role=tab][aria-selected=true]")].find(fbsVis),
    t = (el) => fbsTxt(el).replace(/\s*\d+\+?$/, "").trim();
  return [sub && t(sub), seg && t(seg)].filter(Boolean).filter((x, i, a) => a.indexOf(x) === i).join(" · ").slice(0, 70);
}
const FBS_NO = /\b(?:[A-Z]{1,6}-\d{2,4}(?:-\d{1,5})?|[A-Z]{2,6}\d{2,6})\b/;
// the record open, as its number and title on screen (type, no, title)
function fbsRecord() {
  const rec = { type: "", no: "", title: "" };
  try {
    if ("undefined" != typeof editing && editing && editing.kind && document.querySelector("#drawer.on")) {
      rec.type = editing.kind;
      rec.title = fbsMask(fbsTxt(document.getElementById("d-title")), 80);
    } else if ("undefined" != typeof docOpen && docOpen && "clients" === view && "function" == typeof findDoc) {
      const c = (DB.clients || []).find((x) => x.id === clientOpen),
        d = c && findDoc(c, docOpen.kind, docOpen.id);
      d && ((rec.type = docOpen.kind), (rec.no = String(d.number || d.no || "")), (rec.title = fbsMask(d.title || d.name || "", 80)));
    } else if ("undefined" != typeof poOpen && poOpen && "po" === view) {
      const po = (DB.pos || []).find((x) => x.id === poOpen);
      po && ((rec.type = "po"), (rec.no = String(po.number || po.no || po.id)), (rec.title = fbsMask(po.title || po.vendor || po.vendorName || "", 80)));
    } else if ("undefined" != typeof clientOpen && clientOpen && "clients" === view) {
      const c = (DB.clients || []).find((x) => x.id === clientOpen);
      c && ((rec.type = "client"), (rec.title = fbsMask(c.name, 80)));
    } else if ("undefined" != typeof vendOpen && vendOpen && "vendors" === view) {
      const v = (DB.vendors || []).find((x) => x.id === vendOpen);
      v && ((rec.type = "vendor"), (rec.title = fbsMask(v.name, 80)));
    }
  } catch (e) {}
  if (!rec.no) {
    const o = document.querySelector("#mbm h3, #drawer.on #d-title"),
      v = document.querySelector(".view.on");
    const hay = [fbsTxt(o), v ? [...v.querySelectorAll(".ph h2, .ph h3, .ph .lead, .doc-hd, h2")].slice(0, 4).map(fbsTxt).join(" ") : ""].join(" ");
    const m = FBS_NO.exec(hay);
    m && !/^(CO2|PM\d)/.test(m[0]) && (rec.no = m[0]);
  }
  try {
    const pa = document.getElementById("paddr");
    "undefined" != typeof S && S && S.project && pa && fbsVis(pa) && fbsTxt(pa) && (rec.job = fbsMask(S.project.name, 60));
  } catch (e) {}
  return rec;
}
function fbsScreen() {
  let r = "";
  try {
    r = role();
  } catch (e) {}
  return { view: "undefined" != typeof view ? view : "", heading: fbsHeading(), tab: fbsTab(), over: fbsOver(), record: fbsRecord(), role: r, device: fbsPhone() ? "phone" : "desktop" };
}
const fbsKey = (s) => JSON.stringify([s.view, s.heading, s.tab, s.over && s.over.title, s.record.type, s.record.no, s.record.title, s.role, s.device]);
const fbsPage = (s) => (s ? [s.heading || s.view, s.record && s.record.no, s.record && s.record.title && s.record.title !== s.heading ? s.record.title : "", s.over ? `${s.over.title || s.over.kind}` : ""].filter(Boolean).join(" · ") : "");

// ---- the log ----------------------------------------------------------------------------------------------------------
function fbsAdd(k, o) {
  const S_ = fbsLive;
  if (!S_ || "recording" !== S_.status) return null;
  if (S_.paused && !["pause", "resume", "finish", "error"].includes(k)) return null;
  if (S_.events.length >= FBS_MAX_EVENTS && !["finish", "mark"].includes(k)) {
    S_.full || ((S_.full = !0), fbsBar());
    return null;
  }
  const now = Date.now(),
    e = Object.assign({ n: S_.events.length + 1, k: k, at: fbsWallIso(now), t: Math.round(now - S_.startMs) / 1000 }, o || {});
  S_.events.push(e);
  fbsPersist();
  return e;
}
function fbsPersist(now) {
  if (!fbsLive) return;
  clearTimeout(fbsSaveT);
  const put = () => {
    try {
      "function" == typeof idbSet && idbSet(FBS_KEY, JSON.parse(JSON.stringify(fbsLive, (k, v) => ("_tap" === k || "_then" === k ? void 0 : v))));
    } catch (e) {}
  };
  now ? put() : (fbsSaveT = setTimeout(put, 250));
}
function fbsCheck(why) {
  if (!fbsLive || "recording" !== fbsLive.status || fbsLive.paused) return;
  let sc;
  try {
    sc = fbsScreen();
  } catch (e) {
    return;
  }
  const k = fbsKey(sc);
  if (k === fbsLastKey) return;
  fbsLastKey = k;
  fbsAdd("nav", Object.assign({ why: why || "" }, sc));
  try {
    fbsLastHeads = fbsHeadsInView().join("|");
  } catch (e) {
    fbsLastHeads = "";
  }
}
const fbsLastNav = () => {
  const E = (fbsLive && fbsLive.events) || [];
  for (let i = E.length - 1; i >= 0; i--) if ("nav" === E[i].k) return E[i];
  return null;
};

// ---- taps, typing, scrolling, toasts and errors ------------------------------------------------------------------------
const FBS_CTL = "button, a, [role=button], [role=tab], [role=menuitem], [role=option], .btn, summary, label.chk, input[type=checkbox], input[type=radio], .kpi, .gl, .tcard, tr[data-edit], tr[data-id], [data-edit], [data-v], [data-grp], .chip, .rp-chip, .pill-btn, [onclick], li[tabindex], div[tabindex]";
function fbsCtlKind(el) {
  if (el.closest("#nav-groups, .rail nav, #nav")) return "menu";
  if (el.closest("#mtabs, #tabbar")) return "bottom bar";
  if (el.matches("[role=tab]") || el.closest("#subnav, .sub-tabs, .seg, .ctabs, [role=tablist]")) return "tab";
  if (el.matches("input[type=checkbox], label.chk")) return "checkbox";
  if (el.matches("input[type=radio]")) return "choice";
  if (el.matches(".kpi, .gl, .tcard")) return "tile";
  if (el.matches("tr, [data-edit], li[tabindex], div[tabindex]")) return "row";
  if (el.matches(".chip, .rp-chip, .pill-btn, [aria-pressed]")) return "chip";
  if (el.matches("summary")) return "fold";
  if (el.matches("a")) return "link";
  return "button";
}
// a money or people screen's row is named by the screen, not by what it holds
const FBS_PRIVATE_ROWS = "#v-bank, #v-gl, #v-payroll, #v-time, #v-verify, #v-ap, .bank-row, #v-mbown, #v-mbraise, .trail";
function fbsCtlLabel(el, kind) {
  if ("row" === kind && el.closest(FBS_PRIVATE_ROWS)) return `a row on ${fbsHeading()}`;
  if ("tile" === kind) {
    const k = el.querySelector(".gl-k, .kpi-k, span:not(.gl-v):not(.gl-s)");
    return "tile " + fbsMask(fbsTxt(k), 40);
  }
  let t = el.getAttribute("aria-label") || "";
  if (!t && "row" === kind) {
    const cell = el.querySelector("td:not(.money):not(.num), .tk2-t, .pr-t, b, strong") || el;
    t = fbsTxt(cell);
  }
  if (!t && el.matches("input")) t = (el.labels && el.labels[0] && fbsTxt(el.labels[0])) || el.title || el.name || "";
  t = t || fbsTxt(el) || el.getAttribute("title") || el.dataset.v || "";
  return fbsMask(t.replace(/\s*\d+\+?$/, (m) => (/[A-Za-z]/.test(t) ? "" : m)), 60) || "(no label)";
}
function fbsWhere(el) {
  if (el.closest("#nav-groups, .rail")) return "Menu";
  if (el.closest("header.topbar")) return "Top Bar";
  if (el.closest("#mtabs, #tabbar")) return "Bottom Bar";
  if (el.closest("#toast")) return "Toast";
  let host = el.closest(".card, .td-sec, .ph, #mbm, #drawer, #rp-panel, [role=dialog], .f-card, section, table, details, .view");
  while (host) {
    const h = host.querySelector("h2, h3, h4, .hd b, legend, summary, #d-title");
    const t = h && !h.contains(el) ? fbsTxt(h) : h && h === el ? "" : fbsTxt(h);
    if (t) return fbsMask(t, 50);
    host = host.parentElement && host.parentElement.closest(".card, .td-sec, .ph, #mbm, #drawer, #rp-panel, [role=dialog], section, .view");
  }
  return "";
}
document.addEventListener(
  "click",
  (ev) => {
    if (!fbsLive || "recording" !== fbsLive.status || fbsLive.paused) return;
    const t = ev.target;
    if (!t || !t.closest || t.closest("#fbs-bar, [data-fbs]")) return;
    // a tap into a field is the typing that follows it, logged as typing
    if (t.matches("input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit]), textarea, select, [contenteditable]") && !t.closest("label.chk")) return;
    const el = t.closest(FBS_CTL);
    if (!el) return;
    // the tap before this one is settled first: what it led to is what was on screen before this one
    fbsLive._then && fbsLive._then();
    const kind = fbsCtlKind(el),
      before = fbsLastKey,
      e = fbsAdd("tap", { label: fbsCtlLabel(el, kind), ctl: kind, where: fbsWhere(el), page: fbsPage(fbsLastNav()) });
    if (!e) return;
    fbsLive._tap = e;
    // what happened after it: the screen it landed on, a toast and its words, an error
    let done = !1;
    const settle = () => {
      if (done || !fbsLive) return;
      done = !0;
      fbsLive._then === settle && (fbsLive._then = null);
      fbsCheck("tap");
      const nav = fbsLastNav();
      e.then = Object.assign(e.then || {}, { screen: fbsPage(nav) });
      fbsLastKey !== before && (e.then.moved = !0);
      fbsPersist();
    };
    fbsLive._then = settle;
    setTimeout(settle, 700);
    setTimeout(() => {
      fbsLive && fbsLive._tap === e && (fbsLive._tap = null);
    }, 1600);
  },
  !0,
);
function fbsFieldLabel(el) {
  let l = "";
  try {
    l = (el.labels && el.labels[0] && fbsTxt(el.labels[0])) || "";
  } catch (e) {}
  if (!l) {
    const f = el.closest(".f, .field, label");
    const lab = f && (f.matches("label") ? f : f.querySelector("label"));
    lab && lab !== el && (l = fbsTxt(lab));
  }
  l = l || el.getAttribute("aria-label") || el.getAttribute("placeholder") || el.getAttribute("title") || el.dataset.f || el.name || el.id || el.tagName.toLowerCase();
  return fbsMask(String(l).replace(/\(optional\)/i, ""), 60);
}
const fbsFieldKind = (el) => (el.isContentEditable ? "text" : "TEXTAREA" === el.tagName ? "long text" : "SELECT" === el.tagName ? "choice" : (el.getAttribute("type") || "text").toLowerCase());
let fbsTyping = null;
document.addEventListener(
  "input",
  (ev) => {
    if (!fbsLive || "recording" !== fbsLive.status || fbsLive.paused) return;
    const el = ev.target;
    if (!el || !el.matches || !el.matches("input, textarea, [contenteditable]") || el.matches("input[type=checkbox], input[type=radio], input[type=file]") || el.closest("#fbs-bar, [data-fbs]")) return;
    // the length only: the value itself is never read into the log
    const len = el.isContentEditable ? (el.textContent || "").length : String(el.value || "").length,
      now = Date.now();
    if (fbsTyping && fbsTyping.el === el && now - fbsTyping.last < 8000 && fbsLive.events[fbsLive.events.length - 1] === fbsTyping.e) {
      fbsTyping.e.len = len;
      fbsTyping.last = now;
      fbsPersist();
      return;
    }
    const e = fbsAdd("type", { field: fbsFieldLabel(el), input: fbsFieldKind(el), len: len, where: fbsWhere(el) });
    e && (fbsTyping = { el: el, e: e, last: now });
  },
  !0,
);
document.addEventListener(
  "change",
  (ev) => {
    if (!fbsLive || "recording" !== fbsLive.status || fbsLive.paused) return;
    const el = ev.target;
    if (!el || !el.matches || !el.matches("select") || el.closest("#fbs-bar, [data-fbs]")) return;
    fbsAdd("choose", { field: fbsFieldLabel(el), where: fbsWhere(el) });
  },
  !0,
);
// scrolls that change what is in view: the first headings on screen, once the scrolling stops
function fbsHeadsInView() {
  const v = document.querySelector(".view.on");
  if (!v) return [];
  const top = (document.querySelector("header.topbar") || { getBoundingClientRect: () => ({ bottom: 0 }) }).getBoundingClientRect().bottom;
  // a heading, or a list's section head (the Buy Board's "LATE", Today's "NOW": a class ending in -sh or -gh)
  const H = [...v.querySelectorAll('h2, h3, h4, [role=heading], [class*="-sh"], [class*="-gh"]')].filter((h) => (/^H[234]$/.test(h.tagName) || "heading" === h.getAttribute("role") || [...h.classList].some((c) => /-(sh|gh)$/.test(c))) && fbsTxt(h));
  const label = (h) => fbsMask(fbsTxt(h).replace(/\s*\d+$/, ""), 50);
  const inView = H.filter((h) => {
    const r = h.getBoundingClientRect();
    return r.height > 0 && r.bottom > top && r.top < innerHeight;
  });
  if (inView.length) return inView.slice(0, 3).map(label);
  // no heading on screen: the section being read is the last one above it
  const above = H.filter((h) => {
    const r = h.getBoundingClientRect();
    return r.height > 0 && r.bottom <= top;
  });
  return above.length ? [`${label(above[above.length - 1])} (continued)`] : [];
}
document.addEventListener(
  "scroll",
  (ev) => {
    if (!fbsLive || "recording" !== fbsLive.status || fbsLive.paused) return;
    if (ev.target && ev.target.closest && ev.target.closest("#fbs-bar, [data-fbs]")) return;
    clearTimeout(fbsScrollT);
    fbsScrollT = setTimeout(() => {
      const H = fbsHeadsInView(),
        sig = H.join("|");
      // what a page showed when it opened is its nav (fbsCheck notes it); a scroll is a change of what is in view
      if (!H.length || sig === fbsLastHeads) return;
      fbsLastHeads = sig;
      fbsAdd("scroll", { inView: H });
    }, 600);
  },
  { capture: !0, passive: !0 },
);
window.addEventListener("error", (e) => {
  const x = fbsAdd("error", { what: "page", msg: fbsMask(e.message || "error", 160), src: `${String(e.filename || "").split("/").pop()}:${e.lineno || ""}` });
  x && fbsLive && fbsLive._tap && (fbsLive._tap.then = Object.assign(fbsLive._tap.then || {}, { error: x.msg }));
});
window.addEventListener("unhandledrejection", (e) => {
  const m = fbsMask((e.reason && e.reason.message) || e.reason || "a promise failed", 160),
    x = fbsAdd("error", { what: "promise", msg: m });
  x && fbsLive && fbsLive._tap && (fbsLive._tap.then = Object.assign(fbsLive._tap.then || {}, { error: m }));
});
if ("function" == typeof toast) {
  const base = toast;
  toast = function (msg) {
    try {
      if (!fbsOwnToast && fbsLive && "recording" === fbsLive.status) {
        const words = fbsMask(msg, 140),
          x = fbsAdd("toast", { text: words });
        x && fbsLive._tap && (fbsLive._tap.then = Object.assign(fbsLive._tap.then || {}, { toast: words }));
      }
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
// a failed save is an error in the log, once per message
if ("function" == typeof saveStatus) {
  const base = saveStatus;
  saveStatus = function () {
    const r = base.apply(this, arguments);
    try {
      if ("undefined" != typeof saveState && saveState && !saveState.ok && saveState.msg !== fbsLastSaveMsg) {
        fbsLastSaveMsg = saveState.msg || "";
        fbsAdd("error", { what: "save", msg: fbsMask(saveState.msg || "not saved", 160) });
      } else if ("undefined" != typeof saveState && saveState && saveState.ok) fbsLastSaveMsg = "";
    } catch (e) {}
    return r;
  };
}
// a sheet or a panel opening is a change of screen even when nothing re-renders
if ("function" == typeof mbModal) {
  const base = mbModal;
  mbModal = function () {
    const r = base.apply(this, arguments);
    fbsLive && setTimeout(() => fbsCheck("sheet"), 0);
    // a toast raised before the sheet opened sat on the sheet's buttons (Download JSON, the phone): placed again
    try {
      const t = document.getElementById("toast");
      t && t.classList.contains("on") && "function" == typeof toastPlace && requestAnimationFrame(() => t.classList.contains("on") && toastPlace(t));
    } catch (e) {}
    return r;
  };
}
if ("function" == typeof openEditor) {
  const base = openEditor;
  openEditor = function () {
    const r = base.apply(this, arguments);
    fbsLive && setTimeout(() => fbsCheck("panel"), 0);
    return r;
  };
}
if ("function" == typeof closeEditor) {
  const base = closeEditor;
  closeEditor = function () {
    const r = base.apply(this, arguments);
    fbsLive && setTimeout(() => fbsCheck("panel"), 0);
    return r;
  };
}
if ("function" == typeof rpClose) {
  const base = rpClose;
  rpClose = function () {
    const r = base.apply(this, arguments);
    fbsLive && setTimeout(() => fbsCheck("panel"), 0);
    return r;
  };
}

// ---- start, mark, pause, finish ----------------------------------------------------------------------------------------
function fbsStart() {
  if (!fbsStaff()) return toast("Feedback sessions are for the team");
  if (fbsLive && "recording" === fbsLive.status) return void toast("A feedback session is already recording: Finish it first");
  const me = fbsMe(),
    now = Date.now();
  let r = "";
  try {
    r = role();
  } catch (e) {}
  fbsLive = {
    id: "R-" + Math.random().toString(36).slice(2, 7).toUpperCase(),
    kind: "session",
    status: "recording",
    owner: me.id || "",
    by: me.name || "",
    role: r,
    startMs: now,
    startedAt: fbsWallIso(now),
    device: fbsDevice(),
    workspace: document.body.classList.contains("ws-mb") ? "Mercer & Bond" : "SmartDesign",
    app: "undefined" != typeof APP_VERSION ? APP_VERSION : "",
    marks: 0,
    paused: !1,
    events: [],
  };
  fbsLastKey = "";
  fbsLastHeads = "";
  fbsAdd("start", { role: r, device: fbsLive.device.kind, viewport: fbsLive.device.viewport });
  fbsCheck("start");
  fbsPersist(!0);
  fbsRun();
  fbsBar();
}
function fbsMark() {
  if (!fbsLive || "recording" !== fbsLive.status) return;
  const no = (fbsLive.marks || 0) + 1,
    e = fbsAdd("mark", { no: no, page: fbsPage(fbsLastNav()) });
  if (!e) return;
  fbsLive.marks = no;
  fbsPersist(!0);
  fbsFlash = `Mark ${no} at ${fbsDur(e.t)}: say "mark ${FBS_WORDS[no] || no}"`;
  clearTimeout(fbsFlashT);
  fbsFlashT = setTimeout(() => ((fbsFlash = ""), fbsBar()), 5000);
  fbsBar();
}
function fbsPause() {
  if (!fbsLive) return;
  if (fbsLive.paused) {
    fbsLive.paused = !1;
    fbsAdd("resume");
    fbsLastKey = "";
    fbsCheck("resume");
  } else {
    fbsAdd("pause");
    fbsLive.paused = !0;
  }
  fbsPersist(!0);
  fbsBar();
}
function fbsFinishSheet() {
  if (!fbsLive) return;
  const S_ = fbsLive,
    dur = (Date.now() - S_.startMs) / 1000,
    pages = new Set(S_.events.filter((e) => "nav" === e.k).map((e) => e.heading)).size,
    first = (S_.events.find((e) => "nav" === e.k) || {}).heading || "";
  const box = mbModal(
    "Finish the Feedback Session",
    `<p class="small muted" style="margin-top:0">${fbsMinutes(dur)} · ${S_.events.length} steps on ${pages} page${1 === pages ? "" : "s"} · ${S_.marks || 0} mark${1 === S_.marks ? "" : "s"}. It is saved as your own Problem Report, for you only. Nothing is sent anywhere until you download it.</p>
    <div class="f"><label>Title</label><input data-f="title" id="fbs-title" placeholder="What you walked through, e.g. Estimates on the phone" value=""></div>
    <p class="small muted">Then stop your own recording, and add its transcript on the session's page.</p>
    <button type="button" class="btn ghost sm" data-fbsdiscard>Discard the Session</button>`,
    {
      submit: "Save the Session",
      onSubmit: (f) => {
        fbsFinish(String(f.title || "").trim() || `Feedback on ${first || "the app"}`);
        return !0;
      },
    },
  );
  if (box) {
    box.dataset.fbs = "1";
    const d = box.querySelector("[data-fbsdiscard]");
    d &&
      (d.onclick = () => {
        box.remove();
        mbModal("Discard the Session", `<div class="note warn">The ${fbsMinutes(dur)} just recorded goes for good. Nothing was saved or sent.</div>`, {
          submit: "Keep Recording",
          alt: { label: "Discard It", run: () => fbsDiscard() },
        });
        const m2 = document.getElementById("mbm");
        m2 && (m2.dataset.fbs = "1");
      });
    setTimeout(() => box.querySelector("#fbs-title") && box.querySelector("#fbs-title").focus(), 40);
  }
}
function fbsStop() {
  clearInterval(fbsTickT);
  clearInterval(fbsPollT);
  fbsTickT = fbsPollT = null;
  fbsLive = null;
  fbsLastKey = "";
  "function" == typeof idbDel && idbDel(FBS_KEY);
  fbsBar();
}
function fbsDiscard() {
  fbsStop();
  fbsOwnToast = !0;
  try {
    toast("The feedback session was discarded");
  } finally {
    fbsOwnToast = !1;
  }
}
function fbsInit() {
  DB.rpSessions = Array.isArray(DB.rpSessions) ? DB.rpSessions : [];
  return DB.rpSessions;
}
function fbsFinish(title) {
  const S_ = fbsLive;
  if (!S_) return;
  fbsAdd("finish");
  const end = Date.now(),
    first = S_.events.find((e) => "nav" === e.k) || {};
  const r = {
    id: S_.id,
    kind: "session",
    what: "session",
    whatLabel: "Feedback Session",
    bad: "note",
    badLabel: "Feedback Session",
    status: "new",
    // the report is stamped on the app's clock like every record; the session's own times are the device's
    at: appNowIso(),
    title: fbsMask(title, 120),
    owner: S_.owner,
    by: S_.by,
    role: S_.role,
    okToAsk: !0,
    screen: first.view || "",
    screenTitle: fbsMask(title, 60),
    platform: S_.device.platform,
    browser: S_.device.browser,
    viewport: S_.device.viewport,
    online: navigator.onLine,
    device: S_.device,
    workspace: S_.workspace,
    app: S_.app,
    startedAt: S_.startedAt,
    startMs: S_.startMs,
    endedAt: fbsWallIso(end),
    durSec: Math.round(end - S_.startMs) / 1000,
    marks: S_.marks || 0,
    events: JSON.parse(JSON.stringify(S_.events)),
    transcript: null,
    findings: {},
  };
  fbsInit().push(r);
  "function" == typeof saveNow ? saveNow() : save();
  fbsStop();
  fbsOwnToast = !0;
  try {
    toast(`Feedback session ${r.id} saved: ${fbsMinutes(r.durSec)}, ${r.events.length} steps, ${r.marks} mark${1 === r.marks ? "" : "s"}`, [{ label: "Open", run: () => fbsOpen(r.id) }]);
  } finally {
    fbsOwnToast = !1;
  }
}
function fbsRun() {
  clearInterval(fbsTickT);
  clearInterval(fbsPollT);
  fbsTickT = setInterval(() => {
    const t = document.querySelector("#fbs-bar .fbs-time");
    fbsLive && t && (t.textContent = fbsDur((Date.now() - fbsLive.startMs) / 1000));
  }, 1000);
  // a change no render announces (a sheet, a tab drawn by its own code): looked for once a second
  fbsPollT = setInterval(() => fbsCheck("poll"), 1000);
}
// after a reload or a crash: the session carries on from what was written
async function fbsResume() {
  if (fbsLive || "function" != typeof idbGet) return;
  let s = null;
  try {
    s = await idbGet(FBS_KEY);
  } catch (e) {}
  if (!s || "recording" !== s.status || !Array.isArray(s.events)) return;
  fbsLive = s;
  fbsLive._tap = fbsLive._then = null;
  fbsLastKey = "";
  const was = fbsLive.paused;
  fbsLive.paused = !1;
  fbsAdd("reload", { note: "the page reloaded; the session carried on" });
  fbsLive.paused = was;
  fbsCheck("reload");
  fbsPersist(!0);
  fbsRun();
  fbsBar();
}
(function fbsBoot() {
  const go = () => (document.body && "1" === document.body.dataset.booted ? fbsResume() : setTimeout(go, 200));
  setTimeout(go, 0);
})();
addEventListener("pagehide", () => fbsLive && fbsPersist(!0));
document.addEventListener("visibilitychange", () => "hidden" === document.visibilityState && fbsLive && fbsPersist(!0));

// ---- the bar while it records ----------------------------------------------------------------------------------------
const FBS_SVG = {
  rec: '<rect x="3" y="5" width="18" height="12" rx="2"/><path d="M8 21h8M12 17v4"/><circle cx="12" cy="11" r="2.5"/>',
  mark: '<path d="M6 21V4M6 4h11l-2.5 4L17 12H6"/>',
  pause: '<path d="M9 5v14M15 5v14"/>',
  play: '<path d="M7 5l12 7-12 7z"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="1.5"/>',
  down: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
  doc: '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M10 12h5M10 16h5"/>',
  del: '<path d="M5 7h14M10 7V4h4v3M7 7l1 13h8l1-13"/>',
};
const fbsSvg = (k, w) => `<svg viewBox="0 0 24 24" width="${w || 16}" height="${w || 16}" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${FBS_SVG[k]}</svg>`;
function fbsBar() {
  let bar = document.getElementById("fbs-bar");
  if (!fbsLive || "recording" !== fbsLive.status) return void (bar && bar.remove());
  if (!bar) {
    bar = document.createElement("div");
    bar.id = "fbs-bar";
    bar.className = "fbs-bar no-print";
    bar.setAttribute("role", "region");
    bar.setAttribute("aria-label", "Feedback Session");
    bar.dataset.fixedbar = "1";
    document.body.appendChild(bar);
  }
  const S_ = fbsLive,
    phone = fbsPhone(),
    hint = S_.full ? "The session is full: Finish it and start another." : S_.paused ? "Paused: nothing is recorded until you resume." : fbsFlash || (S_.marks ? "" : "Start your recording now, then tap Mark and say 'mark one' so the two line up.");
  bar.classList.toggle("fbs-phone", phone);
  bar.classList.toggle("fbs-paused", !!S_.paused);
  bar.innerHTML = `<div class="fbs-row"><span class="fbs-live">${S_.paused ? "Paused" : "Recording"}</span><b class="fbs-time" aria-label="Time recorded">${fbsDur((Date.now() - S_.startMs) / 1000)}</b><span class="grow"></span>
    <button type="button" class="btn fbs-mk" data-fbsmark aria-label="Mark">${fbsSvg("mark")}<span>Mark</span>${S_.marks ? `<i class="n">${S_.marks}</i>` : ""}</button>
    <button type="button" class="btn" data-fbspause aria-label="${S_.paused ? "Resume" : "Pause"}">${fbsSvg(S_.paused ? "play" : "pause")}<span class="fbs-bt">${S_.paused ? "Resume" : "Pause"}</span></button>
    <button type="button" class="btn" data-fbsfinish aria-label="Finish">${fbsSvg("stop")}<span>Finish</span></button></div>${hint ? `<div class="fbs-hint">${esc(hint)}</div>` : ""}`;
  bar.querySelector("[data-fbsmark]").onclick = fbsMark;
  bar.querySelector("[data-fbspause]").onclick = fbsPause;
  bar.querySelector("[data-fbsfinish]").onclick = fbsFinishSheet;
  fbsPlace();
  // a toast already up when the bar appeared moves above it
  const t = document.getElementById("toast");
  t && t.classList.contains("on") && "function" == typeof toastClear && toastClear(t);
}
// above whatever is fixed at the foot of the screen (the phone's bottom bar, Say It), beside the menu on a wide screen
function fbsPlace() {
  const bar = document.getElementById("fbs-bar");
  if (!bar) return;
  let floor = innerHeight;
  document.querySelectorAll("#mtabs, #tabbar, #fsay, .m-callbar, .dl-nav, .chat-compose, .mm-nav").forEach((el) => {
    if (!fbsVis(el)) return;
    const cs = getComputedStyle(el);
    if (!/fixed|sticky/.test(cs.position)) return;
    const r = el.getBoundingClientRect();
    r.height && r.top > innerHeight * 0.5 && (floor = Math.min(floor, r.top));
  });
  bar.style.bottom = `${Math.round(innerHeight - floor + 8)}px`;
  if (fbsPhone()) bar.style.left = bar.style.right = "8px";
  else {
    const rail = document.querySelector("aside.rail"),
      rr = rail && fbsVis(rail) ? rail.getBoundingClientRect() : null;
    bar.style.left = `${Math.round((rr && rr.left <= 0 && rr.width < innerWidth / 2 ? rr.right : 0) + 16)}px`;
    bar.style.right = "";
  }
}
addEventListener("resize", () => fbsLive && fbsBar());
// A toast raised without toast() (Report a Problem's "Something went wrong ... Report This" writes its own) sat on
// the bar's Mark button for nine seconds on the phone: while the bar is up, every toast is placed above it.
(function fbsToastWatch() {
  const t = document.getElementById("toast");
  if (!t || "function" != typeof MutationObserver) return void setTimeout(fbsToastWatch, 500);
  new MutationObserver(() => {
    if (!fbsLive || !t.classList.contains("on") || !document.getElementById("fbs-bar")) return;
    const bar = document.getElementById("fbs-bar").getBoundingClientRect(),
      r = t.getBoundingClientRect();
    r.bottom > bar.top - 4 && r.top < bar.bottom && r.right > bar.left && r.left < bar.right && "function" == typeof toastClear && toastClear(t);
  }).observe(t, { attributes: !0, attributeFilter: ["class"] });
})();

// ---- the ways in: Report a Problem, Problem Reports, the menu's foot ---------------------------------------------------
const fbsStartBtn = (cls, id) => `<button type="button" class="btn ${cls || ""}" ${id ? `id="${id}"` : ""} data-fbsstart>${fbsSvg("rec")}<span>Record a Feedback Session</span></button>`;
function fbsMine() {
  const me = fbsMe();
  return fbsInit()
    .filter((s) => s && s.owner && s.owner === me.id)
    .sort((a, b) => String(b.startedAt || "").localeCompare(String(a.startedAt || "")));
}
function fbsWireStart(root) {
  (root || document).querySelectorAll("[data-fbsstart]").forEach((b) => {
    b.onclick = (e) => {
      e.preventDefault();
      "function" == typeof rpClose && rpClose();
      // from the phone's menu: the menu closes, as it does on any page it opens
      document.querySelector(".rail")?.classList.remove("open");
      document.getElementById("railscrim")?.classList.remove("on");
      fbsLive ? fbsFinishSheet() : fbsStart();
    };
  });
}
function fbsMountRail() {
  const who = document.getElementById("whoami");
  if (!who || !fbsStaff()) return void (who && who.querySelector("#fbs-rail") && who.querySelector("#fbs-rail").remove());
  let b = who.querySelector("#fbs-rail");
  if (!b) {
    who.insertAdjacentHTML("beforeend", fbsStartBtn("sm fbs-railbtn", "fbs-rail"));
    b = who.querySelector("#fbs-rail");
  }
  const on = !!fbsLive;
  b.querySelector("span").textContent = on ? "Finish the Feedback Session" : "Record a Feedback Session";
  fbsWireStart(who);
}
if ("function" == typeof rpOpen) {
  const base = rpOpen;
  rpOpen = function () {
    const r = base.apply(this, arguments);
    try {
      const bd = document.querySelector("#rp-panel .rp-bd");
      if (bd && fbsStaff()) {
        const mine = fbsMine();
        bd.insertAdjacentHTML(
          "afterbegin",
          `<div class="fbs-rp">${fbsLive ? `<div class="small"><b>A feedback session is recording.</b> Finish it from the bar at the foot of the screen.</div>` : `${fbsStartBtn("", "fbs-rp-start")}<div class="small muted">Talk through what works and what does not while you use the app; it records where you are and what you tap, to line up with your own recording's transcript.</div>`}${mine.length ? `<div class="small"><a href="#" data-fbsopen="${esc(mine[0].id)}">Open your last session</a><span class="muted"> · ${mine.length} saved</span></div>` : ""}</div>`,
        );
        fbsWireStart(bd);
        bd.querySelectorAll("[data-fbsopen]").forEach((a) => (a.onclick = (e) => (e.preventDefault(), "function" == typeof rpClose && rpClose(), fbsOpen(a.dataset.fbsopen))));
      }
    } catch (e) {
      console.warn("fbs rp", e);
    }
    return r;
  };
}

// ---- the session as a Problem Report: one list, the person's own ------------------------------------------------------
const fbsIsSess = (r) => !!r && "session" === r.kind;
if ("function" == typeof rpAll) {
  const base = rpAll;
  rpAll = function () {
    const out = (base.apply(this, arguments) || []).filter((r) => !fbsIsSess(r));
    try {
      fbsMine().forEach((s) => out.push(s));
      out.sort((a, b) => String(a.at).localeCompare(String(b.at)));
    } catch (e) {}
    return out;
  };
}
// a list saved back (Delete, Clear Handled): sessions stay in their own store, and one left out of the list is gone
if ("function" == typeof rpSave) {
  const base = rpSave;
  rpSave = function (list) {
    try {
      const L = Array.isArray(list) ? list : [],
        keep = new Set(L.filter(fbsIsSess).map((r) => r.id)),
        me = fbsMe().id;
      DB.rpSessions = fbsInit().filter((s) => s.owner !== me || keep.has(s.id));
      save();
      return base.call(this, L.filter((r) => !fbsIsSess(r)));
    } catch (e) {
      return base.apply(this, arguments);
    }
  };
}
const fbsGet = (id) => fbsMine().find((s) => s.id === id) || null;
if ("function" == typeof rpPatch) {
  const base = rpPatch;
  rpPatch = function (id, patch) {
    const s = fbsGet(id);
    if (s) return Object.assign(s, patch), save(), Promise.resolve();
    return base.apply(this, arguments);
  };
}
if ("function" == typeof rpMd) {
  const base = rpMd;
  rpMd = function (r) {
    if (!fbsIsSess(r)) return base.apply(this, arguments);
    const tx = r.transcript;
    return [`### Feedback session: ${r.title} (${r.id})`, `- **Who:** ${r.by || r.role} · ${r.role} · ${(r.device || {}).kind || ""} ${r.viewport || ""}`, `- **When:** ${r.startedAt} to ${r.endedAt} (${fbsMinutes(r.durSec)}), ${(r.events || []).length} steps, ${r.marks} marks`, tx ? `- **Transcript:** ${tx.name || "pasted"} (${tx.format}, ${(tx.lines || []).length} lines)` : "- **Transcript:** not added yet", "", "_The full log and the timeline are on the session's page: Download Session, Export Timeline._"].join("\n");
  };
}
if ("function" == typeof rpCard) {
  const base = rpCard;
  rpCard = function (r) {
    if (!fbsIsSess(r)) return base.apply(this, arguments);
    const st = (RP_STATUS[r.status] || RP_STATUS.new).slice(),
      open = ["new", "accepted"].includes(r.status),
      tx = r.transcript,
      flags = Object.keys(r.findings || {}).length;
    "fixed" === r.status && (st[1] = "Handled");
    return `<div class="card rp-card fbs-card" data-rpid="${esc(r.id)}">
    <div class="rp-card-hd"><b>${esc(r.title || "Feedback Session")}</b><span class="pill info">Feedback Session</span><span class="pill ${st[0]}">${st[1]}</span><span class="grow"></span><span class="small muted">${esc(r.id)} · ${esc(r.by || r.role)} · ${r.at ? fmtL(String(r.at).slice(0, 10)) : ""}</span></div>
    <div class="small muted">${fbsMinutes(r.durSec)} · ${(r.events || []).length} steps · ${r.marks} mark${1 === r.marks ? "" : "s"} · ${esc((r.device || {}).kind || "")} ${esc(r.viewport || "")} · ${tx ? `transcript ${esc(tx.format)}, ${(tx.lines || []).length} lines${flags ? `, ${flags} flagged` : ""}` : "no transcript yet"}</div>
    <div class="row rp-acts"><button class="btn sm" data-fbsopen="${esc(r.id)}">Open Session</button><button class="btn sm" data-fbsdl="${esc(r.id)}">Download Session</button>${open ? '<button class="btn sm" data-rpset="fixed">Mark Handled</button>' : '<button class="btn sm" data-rpset="new">Reopen</button>'}<span class="grow"></span><button class="btn sm ghost" data-rpcopy>Copy This One</button><button class="btn sm ghost" data-rpdel>Delete</button></div></div>`;
  };
}
if ("function" == typeof rpBoxHtml) {
  const base = rpBoxHtml;
  rpBoxHtml = function () {
    let h = base.apply(this, arguments);
    try {
      fbsStaff() && (h = h.replace('<button class="btn" id="rp-copy">', `${fbsStartBtn("", "fbs-rpbox-start")}<button class="btn" id="rp-copy">`));
    } catch (e) {}
    return h;
  };
}
if ("function" == typeof renderRpBox) {
  const base = renderRpBox;
  renderRpBox = function () {
    const r = base.apply(this, arguments);
    try {
      const host = document.getElementById("rpbox-body");
      if (host) {
        fbsWireStart(host);
        host.querySelectorAll("[data-fbsopen]").forEach((b) => (b.onclick = () => fbsOpen(b.dataset.fbsopen)));
        host.querySelectorAll("[data-fbsdl]").forEach((b) => (b.onclick = () => fbsDownloadSession(fbsGet(b.dataset.fbsdl))));
      }
    } catch (e) {}
    return r;
  };
}

// ---- the transcript: read it, line it up three ways ---------------------------------------------------------------------
const FBS_NUM = Object.fromEntries(FBS_WORDS.map((w, i) => [w, i]));
function fbsMarkSaid(text) {
  const m = /\bmark(?:er)?[\s,.-]*(?:number\s*)?#?\s*(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|\d{1,2})\b/i.exec(String(text || ""));
  if (!m) return 0;
  const w = m[1].toLowerCase();
  return /^\d+$/.test(w) ? +w : FBS_NUM[w] || 0;
}
// the local midnight of the session's day, on the device's clock
const fbsMidnight = (ms) => {
  const d = new Date(ms);
  d.setHours(0, 0, 0, 0);
  return d.getTime();
};
// New York wall time ("2026-10-26T09:58:00", what a Meet doc's name gives) as epoch milliseconds
function fbsNyMs(wall) {
  const C = MEETDOC_CORE,
    sec = C.wall(wall);
  if (null == sec) return null;
  return (sec + 3600 * (C.usDst(String(wall).slice(0, 10)) ? 4 : 5)) * 1000;
}
// every way this transcript can be lined up with this session, and what each rests on
function fbsWays(s) {
  const tx = s.transcript,
    marks = (s.events || []).filter((e) => "mark" === e.k),
    anchors = [];
  if (!tx) return { marks: marks, anchors: anchors, clock: null };
  const seen = new Set();
  (tx.lines || []).forEach((l) => {
    const no = fbsMarkSaid(l.text);
    if (!no || seen.has(no)) return;
    const mk = marks.find((m) => m.no === no);
    mk && (seen.add(no), anchors.push({ no: no, sec: l.sec, t: mk.t, line: l.i }));
  });
  anchors.sort((a, b) => a.sec - b.sec);
  // the clock: the transcript writes times of day, or its start is known (the doc's name, or typed)
  let clock = null;
  if (tx.clock) clock = { kind: "times", base: (fbsMidnight(s.startMs) - s.startMs) / 1000 };
  else if (null != tx.recStartMs) clock = { kind: "start", base: (tx.recStartMs - s.startMs) / 1000 };
  return { marks: marks, anchors: anchors, clock: clock };
}
// the session second each transcript line was said at, by the chosen way, plus the nudge
function fbsAlign(s) {
  const tx = s.transcript;
  if (!tx) return null;
  const W = fbsWays(s),
    A = (tx.align = tx.align || {}),
    nudge = +A.nudge || 0;
  let how = A.how;
  if (!how || ("mark" === how && !W.anchors.length) || ("clock" === how && !W.clock)) how = W.anchors.length ? "mark" : W.clock ? "clock" : "offset";
  const off = +A.offset || 0;
  // By Mark: marks that agree (within 1.5 s: the transcript's own rounding) are one shift, their mean; marks that do
  // not (the recorder was paused, or drifted) each set the shift from where they were said until the next one
  const O = W.anchors.map((a) => a.t - a.sec),
    one = O.length && Math.max(...O) - Math.min(...O) <= 1.5,
    mean = O.length ? O.reduce((x, y) => x + y, 0) / O.length : 0;
  const at = (l) => {
    if ("mark" === how) {
      if (one) return l.sec + mean + nudge;
      let a = W.anchors[0];
      W.anchors.forEach((x) => x.sec <= l.sec && (a = x));
      return l.sec + (a.t - a.sec) + nudge;
    }
    if ("clock" === how) return l.sec + W.clock.base + nudge;
    return l.sec + off + nudge;
  };
  let say = "";
  if ("mark" === how)
    say =
      W.anchors.map((a) => `"mark ${FBS_WORDS[a.no] || a.no}" said at ${fbsHms(a.sec)} in the transcript is Mark ${a.no}, tapped ${fbsDur(a.t)} into the session`).join("; ") +
      (O.length > 1 ? (one ? `; the marks agree, so ${fbsShift(mean)} throughout` : "; the marks disagree (a pause in the recording?), so each mark lines up the lines after it") : `; ${fbsShift(mean)}`);
  else if ("clock" === how) say = W.clock.kind === "times" ? "the transcript's times are times of day, read on this device's clock" : `the recording started at ${fbsClock(tx.recStartMs)}: ${fbsShift(W.clock.base)}`;
  else say = fbsShift(off);
  nudge && (say += `; nudged ${nudge > 0 ? "+" : ""}${nudge} s`);
  return { how: how, nudge: nudge, offset: off, ways: W, at: at, say: say };
}
// what was on screen and what was tapped around each line, grouped by page
const FBS_WIN = { before: 6, after: 3, recent: 60 };
function fbsTimeline(s) {
  const A = fbsAlign(s);
  if (!A) return null;
  const E = s.events || [],
    navs = E.filter((e) => "nav" === e.k),
    taps = E.filter((e) => ["tap", "type", "choose"].includes(e.k)),
    loud = E.filter((e) => ["tap", "toast", "error"].includes(e.k)),
    rows = (s.transcript.lines || []).map((l) => {
      const t = Math.round(A.at(l) * 1000) / 1000;
      let nav = null;
      navs.forEach((n) => n.t <= t + 0.25 && (nav = n));
      return {
        i: l.i,
        t: t,
        at: fbsWallIso(s.startMs + t * 1000),
        ts: l.ts,
        speaker: l.speaker || "",
        said: l.text,
        page: nav ? { view: nav.view, heading: nav.heading, tab: nav.tab, over: nav.over, record: nav.record, role: nav.role, device: nav.device } : null,
        pageKey: nav ? fbsKey(nav) : "",
        taps: taps.filter((e) => e.t >= t - FBS_WIN.before && e.t <= t + FBS_WIN.after),
        recent: loud.filter((e) => e.t <= t + FBS_WIN.after && e.t >= t - FBS_WIN.recent).slice(-4),
        finding: (s.findings || {})[l.i] || "",
      };
    });
  const groups = [];
  rows.forEach((r) => {
    const g = groups[groups.length - 1];
    g && g.key === r.pageKey ? g.rows.push(r) : groups.push({ key: r.pageKey, page: r.page, rows: [r] });
  });
  return { align: A, rows: rows, groups: groups };
}
function fbsReadInto(s, text, name, startTyped) {
  const R = MEETDOC_CORE.readTimed(text, { name: name || "" });
  if (!R.lines.length) return null;
  let rec = null;
  if (startTyped) {
    const sec = MEETDOC_CORE.tsec(startTyped);
    null != sec && (rec = fbsMidnight(s.startMs) + sec * 1000);
  } else if (R.start) rec = fbsNyMs(R.start);
  s.transcript = {
    name: fbsMask(name || "", 120),
    format: R.format,
    // the transcript is the person's own words, kept on their own private session
    lines: R.lines.map((l) => ({ i: l.i, sec: l.sec, ts: l.ts, speaker: String(l.speaker || "").slice(0, 60), text: String(l.text || "").slice(0, 2000) })),
    clock: !!R.clock,
    recStartMs: rec,
    addedAt: appNowIso(),
    align: {},
  };
  s.findings = {};
  return s.transcript;
}

// ---- the session's page --------------------------------------------------------------------------------------------------
function fbsOpen(id) {
  fbsOpenId = id || "";
  fbsEnsureView();
  "function" == typeof setView ? setView("fbs") : ((view = "fbs"), render());
}
function fbsEnsureView() {
  if (!document.getElementById("v-fbs")) {
    const sec = document.createElement("section");
    sec.className = "view";
    sec.id = "v-fbs";
    sec.setAttribute("aria-label", "Feedback Session");
    sec.innerHTML = '<div id="fbs-body"></div>';
    (document.getElementById("v-rpbox") || document.getElementById("v-settings") || document.querySelector(".view"))?.parentElement?.appendChild(sec);
  }
  try {
    "object" == typeof ROLE_VIEWS &&
      Object.keys(ROLE_VIEWS).forEach((r) => {
        "client" !== r && Array.isArray(ROLE_VIEWS[r]) && !ROLE_VIEWS[r].includes("fbs") && ROLE_VIEWS[r].push("fbs");
      });
    "object" == typeof NAV_LABELS && (NAV_LABELS.fbs = "Feedback Session");
    "object" == typeof IA_LABELS && (IA_LABELS.fbs = "Feedback Session");
    "undefined" != typeof MN_BUTTON && MN_BUTTON.add("fbs");
  } catch (e) {}
}
fbsEnsureView();
const FBS_KIND = { nav: "Page", tap: "Tapped", type: "Typed", choose: "Chose", scroll: "Scrolled", toast: "The app said", error: "Error", mark: "Mark", pause: "Paused", resume: "Resumed", start: "Started", finish: "Finished", reload: "Reloaded" };
function fbsStepText(e) {
  switch (e.k) {
    case "nav":
      return `${e.heading || e.view}${e.record && e.record.no ? ` · ${e.record.no}` : ""}${e.record && e.record.title && e.record.title !== e.heading ? ` · ${e.record.title}` : ""}${e.tab ? ` · ${e.tab}` : ""}${e.over ? ` · ${e.over.kind} "${e.over.title}"` : ""}`;
    case "tap":
      return `${e.ctl} "${e.label}"${e.where ? ` in ${e.where}` : ""}${e.then && e.then.toast ? `; the app said "${e.then.toast}"` : ""}${e.then && e.then.error ? `; error: ${e.then.error}` : ""}${e.then && e.then.moved ? `; went to ${e.then.screen}` : ""}`;
    case "type":
      return `${e.len} character${1 === e.len ? "" : "s"} into ${e.field}${e.where ? ` (${e.where})` : ""}`;
    case "choose":
      return `an option in ${e.field}`;
    case "scroll":
      return `to ${(e.inView || []).join(", ")}`;
    case "toast":
      return `"${e.text}"`;
    case "error":
      return `${e.what}: ${e.msg}${e.src ? ` (${e.src})` : ""}`;
    case "mark":
      return `Mark ${e.no}`;
    case "start":
      return `as ${FBS_ROLE[e.role] || e.role} on the ${e.device} (${e.viewport})`;
    default:
      return e.note || "";
  }
}
function fbsLogHtml(s) {
  const E = s.events || [],
    G = [];
  E.filter((e) => "start" !== e.k).forEach((e) => {
    if ("nav" === e.k || !G.length) G.push({ nav: "nav" === e.k ? e : null, steps: [] });
    "nav" !== e.k && G[G.length - 1].steps.push(e);
  });
  return G.map(
    (g) =>
      `<div class="fbs-g"><div class="fbs-gh"><h3>${esc(g.nav ? g.nav.heading || g.nav.view : "Before the First Page")}</h3><span class="small muted">${g.nav ? `${esc(fbsStepText(g.nav).replace(/^[^·]*·?\s*/, ""))}${g.nav.t != null ? ` · at ${fbsDur(g.nav.t)}` : ""}` : ""}</span></div>${g.steps.length ? g.steps.map((e) => `<div class="fbs-step fbs-k-${e.k}"><span class="fbs-st">${fbsDur(e.t)}</span><span class="fbs-sk">${esc(FBS_KIND[e.k] || e.k)}</span><span class="fbs-sx">${esc(fbsStepText(e))}</span></div>`).join("") : '<div class="small muted fbs-step">Looked, nothing tapped.</div>'}</div>`,
  ).join("");
}
function fbsTimelineHtml(s, T) {
  const flag = (r) =>
    `<div class="fbs-fl" role="group" aria-label="Finding for line ${r.i + 1}">${[
      ["problem", "Problem"],
      ["idea", "Idea"],
      ["works", "Works"],
    ]
      .map(([k, l]) => `<button type="button" class="fbs-chip ${r.finding === k ? "on fbs-" + k : ""}" data-fbsflag="${k}" data-fbsline="${r.i}" aria-pressed="${r.finding === k}">${l}</button>`)
      .join("")}</div>`;
  const tapLine = (r) =>
    r.taps.length
      ? r.taps
          .map((e) => ("tap" === e.k ? `Tapped <b>${esc(e.label)}</b>${e.where ? ` <span class="muted">in ${esc(e.where)}</span>` : ""}${e.then && e.then.toast ? ` <span class="muted">then "${esc(e.then.toast)}"</span>` : ""}` : "type" === e.k ? `Typed ${e.len} into <b>${esc(e.field)}</b>` : `Chose in <b>${esc(e.field)}</b>`) + ` <span class="muted">${fbsDur(e.t)}</span>`)
          .join("<br>")
      : '<span class="muted">Nothing tapped</span>';
  return T.groups
    .map((g) => {
      const p = g.page,
        a = g.rows[0].t,
        b = g.rows[g.rows.length - 1].t;
      return `<div class="fbs-tg"><div class="fbs-gh"><h3>${esc(p ? p.heading || p.view : "Before the Session")}</h3><span class="small muted">${p ? esc([p.record && p.record.no, p.record && p.record.title !== p.heading ? p.record.title : "", p.tab, p.over ? `${p.over.kind} "${p.over.title}"` : ""].filter(Boolean).join(" · ")) : ""}${p ? " · " : ""}${fbsDur(Math.max(0, a))} to ${fbsDur(Math.max(0, b))} · ${g.rows.length} line${1 === g.rows.length ? "" : "s"}</span></div>${g.rows
        .map(
          (r) =>
            `<div class="fbs-tl ${r.finding ? "fbs-has-" + r.finding : ""}" id="fbs-line-${r.i}" data-fbsrow="${r.i}"><div class="fbs-tt"><b>${r.t < 0 ? "-" : ""}${fbsDur(Math.abs(r.t))}</b><small>${esc(fbsClock(s.startMs + r.t * 1000))}</small><small class="muted">said at ${esc(r.ts)}</small></div><div class="fbs-said">${r.speaker ? `<span class="fbs-spk">${esc(r.speaker)}</span> ` : ""}${esc(r.said)}</div><div class="fbs-on small">${tapLine(r)}</div>${flag(r)}</div>`,
        )
        .join("")}</div>`;
    })
    .join("");
}
function fbsAlignHtml(s, T) {
  const A = T.align,
    W = A.ways,
    tx = s.transcript,
    seg = [
      ["mark", "By Mark", W.anchors.length ? "" : W.marks.length ? "no \"mark one\" found in the transcript" : "no marks were dropped"],
      ["clock", "By Clock Time", W.clock ? "" : "set Recording Started At"],
      ["offset", "By Offset", ""],
    ];
  return `<div class="card fbs-align"><div class="hd"><h3>Lined Up</h3><span class="small muted">${esc(tx.name || "Pasted transcript")} · ${esc(tx.format)} · ${tx.lines.length} lines</span></div>
  <div class="seg fbs-seg" role="tablist" aria-label="How the transcript is lined up">${seg.map(([k, l, why]) => `<button type="button" role="tab" class="${A.how === k ? "on" : ""}" data-fbshow="${k}" aria-selected="${A.how === k}" ${why ? `title="${esc(why)}"` : ""}>${l}</button>`).join("")}</div>
  <div class="fbs-arow"><div class="f fbs-off"><label for="fbs-off">Offset (Seconds)</label><input id="fbs-off" inputmode="decimal" value="${A.offset || 0}" aria-label="Offset in seconds"></div>
  <div class="f fbs-rst"><label for="fbs-rst">Recording Started At</label><input id="fbs-rst" type="time" step="1" value="${tx.recStartMs != null ? esc(new Date(tx.recStartMs).toTimeString().slice(0, 8)) : ""}" aria-label="Recording started at"></div>
  <div class="f fbs-nudge"><label>Nudge (Seconds)</label><div class="row">${[-5, -1, 1, 5].map((n) => `<button type="button" class="btn sm" data-fbsnudge="${n}" aria-label="Nudge ${n > 0 ? "later" : "earlier"} ${Math.abs(n)} seconds">${n > 0 ? "+" : "−"}${Math.abs(n)}</button>`).join("")}<span class="small fbs-nv">${A.nudge ? `${A.nudge > 0 ? "+" : ""}${A.nudge} s` : "none"}</span></div></div></div>
  <p class="small fbs-say" data-fbssay>Applied: ${esc(A.say)}.</p></div>`;
}
function fbsPageHtml() {
  const mine = fbsMine();
  let s = fbsOpenId ? fbsGet(fbsOpenId) : null;
  s || (s = mine[0] || null);
  s && (fbsOpenId = s.id);
  const pick = mine.length > 1 ? `<div class="f fbs-pick"><label for="fbs-pick">Session</label><select id="fbs-pick" data-fbspick>${mine.map((x) => `<option value="${esc(x.id)}" ${x.id === (s && s.id) ? "selected" : ""}>${esc(x.title)} · ${esc(x.id)}</option>`).join("")}</select></div>` : "";
  if (!s)
    return `<div class="ph"><div><h2>Feedback Session</h2><div class="lead">${fbsLive ? "A session is recording now. Finish it from the bar at the foot of the screen and it opens here." : "No feedback sessions yet. Start one, record your screen and voice with your own tool, and add its transcript here."}</div></div><div class="acts fbs-acts">${fbsLive ? "" : fbsStartBtn("", "fbs-empty-start")}</div></div>`;
  const tx = s.transcript,
    T = tx ? fbsTimeline(s) : null,
    pages = new Set((s.events || []).filter((e) => "nav" === e.k).map((e) => e.heading)).size;
  return `<div class="ph"><div><h2>Feedback Session</h2><div class="lead"><b>${esc(s.title)}</b> · ${esc(s.id)} · started ${esc(fbsClock(s.startMs))} on ${esc(new Date(s.startMs).toLocaleDateString("en-US", { month: "short", day: "numeric" }))} · ${fbsMinutes(s.durSec)} · ${esc((s.device || {}).kind || "")} · ${esc(FBS_ROLE[s.role] || s.role)} · ${s.marks} mark${1 === s.marks ? "" : "s"} · ${(s.events || []).length} steps on ${pages} page${1 === pages ? "" : "s"}</div></div>
  <div class="acts fbs-acts">${tx ? `<button type="button" class="btn primary" data-fbsexport>${fbsSvg("down")}<span>Export Timeline</span></button><button type="button" class="btn" data-fbstx>${fbsSvg("doc")}<span>Replace the Transcript</span></button>` : `<button type="button" class="btn primary" data-fbstx>${fbsSvg("doc")}<span>Add Transcript</span></button>`}<button type="button" class="btn" data-fbsdlnow>${fbsSvg("down")}<span>Download Session</span></button><button type="button" class="btn ghost" data-fbsdelnow aria-label="Delete the session">${fbsSvg("del")}<span>Delete</span></button></div></div>
  ${pick}
  ${
    tx
      ? `${fbsAlignHtml(s, T)}<div class="fbs-tlh small muted"><span>Time</span><span>What Was Said</span><span>What Was Tapped</span><span>Finding</span></div><div class="fbs-tlist">${fbsTimelineHtml(s, T)}</div>`
      : `<div class="note">Add the transcript from your own recording (Google Meet, the phone's recorder, Loom, Otter): a file or pasted text, as WebVTT, SRT, the Meet transcript doc, an Otter or Loom export, or lines like "00:01:23 text". It is lined up by your Mark, by the clock, or by an offset you type.</div><div class="card fbs-log"><div class="hd"><h3>What Was Recorded</h3><span class="small muted">every page, tap, field and toast, with the time since the start</span></div>${fbsLogHtml(s)}</div>`
  }`;
}
function renderFbs() {
  const host = document.getElementById("fbs-body");
  if (!host) return;
  host.innerHTML = fbsPageHtml();
  fbsWirePage(host);
}
// the page's scroller: the body on the phone, the document on a wide screen
const fbsScroller = () => (document.body.scrollHeight > document.body.clientHeight + 2 && /auto|scroll/.test(getComputedStyle(document.body).overflowY) ? document.body : document.scrollingElement || document.documentElement);
function fbsRerender(keepScroll) {
  const sc = fbsScroller(),
    y = sc.scrollTop;
  renderFbs();
  keepScroll && (sc.scrollTop = y);
}
function fbsWirePage(host) {
  fbsWireStart(host);
  const s = fbsGet(fbsOpenId);
  const pk = host.querySelector("[data-fbspick]");
  pk && (pk.onchange = () => ((fbsOpenId = pk.value), renderFbs()));
  if (!s) return;
  const q = (sel) => host.querySelector(sel);
  q("[data-fbstx]") && (q("[data-fbstx]").onclick = () => fbsTranscriptSheet(s));
  q("[data-fbsdlnow]") && (q("[data-fbsdlnow]").onclick = () => fbsDownloadSession(s));
  q("[data-fbsexport]") && (q("[data-fbsexport]").onclick = () => fbsExportSheet(s));
  q("[data-fbsdelnow]") &&
    (q("[data-fbsdelnow]").onclick = () =>
      mbModal("Delete the Session", `<div class="note">${esc(s.title)} (${esc(s.id)}) and its transcript go for good. A copy you downloaded stays where you saved it.</div>`, {
        submit: "Delete It",
        onSubmit: () => {
          DB.rpSessions = fbsInit().filter((x) => x.id !== s.id);
          save();
          fbsOpenId = "";
          toast(`Feedback session ${s.id} deleted`, [{ label: "Open", run: () => fbsOpen("") }]);
          renderFbs();
        },
      }));
  const tx = s.transcript;
  if (!tx) return;
  const A = (tx.align = tx.align || {});
  const apply = (msg) => {
    save();
    fbsRerender(!0);
    msg && toast(msg, [{ label: "Open", run: () => fbsOpen(s.id) }]);
  };
  host.querySelectorAll("[data-fbshow]").forEach(
    (b) =>
      (b.onclick = () => {
        const W = fbsWays(s),
          k = b.dataset.fbshow;
        if ("mark" === k && !W.anchors.length) return toast(W.marks.length ? 'No "mark one" was found in the transcript: line it up by offset' : "No marks were dropped in this session: line it up by offset");
        if ("clock" === k && !W.clock) return toast("Set Recording Started At first, or line it up by Mark or offset"), void (q("#fbs-rst") && q("#fbs-rst").focus());
        A.how = k;
        apply(`Lined up ${b.textContent.trim().toLowerCase()}`);
      }),
  );
  const off = q("#fbs-off");
  off &&
    (off.onchange = () => {
      const v = String(off.value || "").trim(),
        neg = /^-|^−/.test(v),
        t = MEETDOC_CORE.tsec(v.replace(/^[-+−]/, "")),
        n = null != t ? (neg ? -t : t) : parseFloat(v.replace("−", "-"));
      if (!isFinite(n)) return toast("Type the offset in seconds, like 12 or -4.5, or as 1:05");
      A.offset = Math.round(n * 1000) / 1000;
      A.how = "offset";
      apply(`Lined up by an offset of ${A.offset} s`);
    });
  const rst = q("#fbs-rst");
  rst &&
    (rst.onchange = () => {
      const t = MEETDOC_CORE.tsec(rst.value);
      if (null == t) return;
      tx.recStartMs = fbsMidnight(s.startMs) + t * 1000;
      tx.clock = !1;
      A.how = "clock";
      apply(`Lined up by the clock: the recording started ${fbsClock(tx.recStartMs)}`);
    });
  host.querySelectorAll("[data-fbsnudge]").forEach(
    (b) =>
      (b.onclick = () => {
        A.nudge = Math.round(((+A.nudge || 0) + +b.dataset.fbsnudge) * 1000) / 1000;
        apply(`Nudged to ${A.nudge > 0 ? "+" : ""}${A.nudge} s`);
      }),
  );
  host.querySelectorAll("[data-fbsflag]").forEach(
    (b) =>
      (b.onclick = () => {
        const i = +b.dataset.fbsline,
          k = b.dataset.fbsflag;
        s.findings = s.findings || {};
        s.findings[i] === k ? delete s.findings[i] : (s.findings[i] = k);
        save();
        const row = host.querySelector(`[data-fbsrow="${i}"]`);
        row &&
          (row.className = `fbs-tl ${s.findings[i] ? "fbs-has-" + s.findings[i] : ""}`,
          row.querySelectorAll("[data-fbsflag]").forEach((x) => {
            const on = s.findings[i] === x.dataset.fbsflag;
            x.className = `fbs-chip ${on ? "on fbs-" + x.dataset.fbsflag : ""}`;
            x.setAttribute("aria-pressed", on);
          }));
        toast(s.findings[i] ? `Line ${i + 1} flagged: ${{ problem: "a problem", idea: "an idea", works: "what works" }[k]}` : `Line ${i + 1} unflagged`, [{ label: "Open", run: () => (fbsOpen(s.id), setTimeout(() => document.getElementById(`fbs-line-${i}`)?.scrollIntoView({ block: "center" }), 60)) }]);
      }),
  );
}
function fbsTranscriptSheet(s) {
  const box = mbModal(
    s.transcript ? "Replace the Transcript" : "Add Transcript",
    `<p class="small muted" style="margin-top:0">From your own recording: WebVTT (.vtt), SRT (.srt), the Google Meet transcript doc, an Otter or Loom export, or plain lines like "00:01:23 text" or "[1:23] text". It stays on your own session.${s.transcript ? " The flags on the old lines go with it." : ""}</p>
    <div class="f"><label for="fbs-file">Upload a File</label><input type="file" id="fbs-file" accept=".vtt,.srt,.txt,.md,text/vtt,text/plain,text/markdown,application/x-subrip"></div>
    <div class="f"><label for="fbs-text">Or Paste the Transcript</label><textarea data-f="text" id="fbs-text" rows="8" placeholder="Paste here"></textarea></div>
    <div class="f"><label for="fbs-start">Recording Started At <span class="muted">(optional)</span></label><input data-f="start" id="fbs-start" type="time" step="1" aria-label="Recording started at"></div>
    <p class="small muted">Said "mark one" when you tapped Mark? It lines up by itself. Otherwise give the time your recording started, or type an offset on the next screen.</p>`,
    {
      submit: "Read It",
      onSubmit: (f) => {
        const text = f.text || "";
        if (!text.trim()) return toast("Upload the file or paste the transcript first"), !1;
        const tx = fbsReadInto(s, text, (box && box.dataset.fname) || "", f.start || "");
        if (!tx) return toast("No timed lines found: each line needs a time, like 00:01:23 or [1:23]"), !1;
        save();
        const A = fbsAlign(s);
        setTimeout(() => {
          fbsOpen(s.id);
          toast(`Read ${tx.lines.length} lines (${tx.format}); lined up ${{ mark: "by Mark", clock: "by the clock", offset: "by offset" }[A.how]}`, [{ label: "Open", run: () => fbsOpen(s.id) }]);
        }, 0);
        return !0;
      },
    },
  );
  if (!box) return;
  box.dataset.fbs = "1";
  const fi = box.querySelector("#fbs-file");
  fi &&
    (fi.onchange = () => {
      const file = fi.files && fi.files[0];
      if (!file) return;
      box.dataset.fname = file.name;
      const r = new FileReader();
      r.onload = () => {
        const ta = box.querySelector("#fbs-text");
        ta && (ta.value = String(r.result || ""));
      };
      r.readAsText(file);
    });
}

// ---- the files: the session, and the timeline for Claude to read --------------------------------------------------------
function fbsDownload(name, text, mime) {
  try {
    const blob = new Blob([text], { type: mime || "application/json" }),
      url = URL.createObjectURL(blob),
      a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => (URL.revokeObjectURL(url), a.remove()), 1500);
    return !0;
  } catch (e) {
    return toast("This browser would not save the file"), !1;
  }
}
const fbsSlug = (s) => String(s || "session").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "session";
function fbsSessionJson(s) {
  const o = Object.assign({ format: "smartdesigns-feedback-session", version: 1, clock: "events carry the device's wall-clock time (at) and seconds since the session started (t)" }, s);
  delete o._tap;
  return JSON.stringify(o, null, 1);
}
function fbsDownloadSession(s) {
  if (!s) return;
  const name = `feedback-session-${s.id}-${fbsSlug(s.title)}.json`;
  fbsDownload(name, fbsSessionJson(s), "application/json") && toast(`Saved ${name} to your downloads`, [{ label: "Open", run: () => fbsOpen(s.id) }]);
}
const fbsPageOf = (p) => (p ? [p.heading || p.view, p.record && p.record.no, p.record && p.record.title && p.record.title !== p.heading ? p.record.title : "", p.tab ? `tab ${p.tab}` : "", p.over ? `${p.over.kind} "${p.over.title}"` : ""].filter(Boolean).join(" · ") : "before the session");
const fbsEvShort = (e) => ("tap" === e.k ? `tapped "${e.label}"${e.where ? ` (${e.where})` : ""}${e.then && e.then.moved ? ` -> ${e.then.screen}` : ""}` : "toast" === e.k ? `the app said "${e.text}"` : "error" === e.k ? `error: ${e.msg}` : "type" === e.k ? `typed ${e.len} characters into ${e.field}` : `chose in ${e.field}`);
function fbsTimelineData(s) {
  const T = fbsTimeline(s);
  const ev = (e) => {
    const o = { t: e.t, at: e.at, kind: e.k };
    ["label", "ctl", "where", "field", "len", "text", "msg", "then"].forEach((k) => null != e[k] && (o[k] = e[k]));
    return o;
  };
  return {
    format: "smartdesigns-feedback-timeline",
    version: 1,
    session: { id: s.id, title: s.title, by: s.by, role: s.role, device: s.device, startedAt: s.startedAt, endedAt: s.endedAt, durSec: s.durSec, marks: (s.events || []).filter((e) => "mark" === e.k).map((e) => ({ no: e.no, t: e.t, at: e.at })) },
    transcript: { name: s.transcript.name, format: s.transcript.format, lines: s.transcript.lines.length },
    alignment: { how: T.align.how, offsetSec: T.align.offset, nudgeSec: T.align.nudge, applied: T.align.say, window: FBS_WIN },
    lines: T.rows.map((r) => ({ line: r.i + 1, t: r.t, at: r.at, said_at: r.ts, speaker: r.speaker, said: r.said, page: r.page ? { view: r.page.view, heading: r.page.heading, tab: r.page.tab, over: r.page.over, record: r.page.record } : null, taps: r.taps.map(ev), recent: r.recent.map(ev), finding: r.finding })),
    pages: T.groups.map((g) => ({ page: fbsPageOf(g.page), from: g.rows[0].t, to: g.rows[g.rows.length - 1].t, lines: g.rows.map((r) => r.i + 1) })),
  };
}
function fbsTimelineMd(s) {
  const D = fbsTimelineData(s),
    T = fbsTimeline(s),
    out = [
      `# Feedback session: ${s.title}`,
      "",
      `- **Session:** ${s.id} · ${s.by || ""} (${FBS_ROLE[s.role] || s.role}) · ${(s.device || {}).kind || ""} ${(s.device || {}).viewport || ""} · started ${s.startedAt} · ${fbsMinutes(s.durSec)} · ${D.session.marks.length} marks`,
      `- **Transcript:** ${s.transcript.name || "pasted"} (${s.transcript.format}, ${s.transcript.lines.length} lines)`,
      `- **Lined up:** ${T.align.how}; ${T.align.say}`,
      `- **How to read it:** each line is what was said, at its time in the session (and the device's clock), then the page and record on screen, what was tapped from ${FBS_WIN.before} s before to ${FBS_WIN.after} s after, and the last taps, toasts and errors before it. A flag (problem, idea, works) is the person's own. Nothing typed was recorded, only field names and lengths.`,
      "",
    ];
  T.groups.forEach((g, gi) => {
    out.push(`## ${gi + 1}. ${fbsPageOf(g.page)} (${fbsDur(Math.max(0, g.rows[0].t))} to ${fbsDur(Math.max(0, g.rows[g.rows.length - 1].t))})`, "");
    g.rows.forEach((r) => {
      out.push(`- **${fbsHms(r.t)}** (${fbsClock(s.startMs + r.t * 1000)}, said at ${r.ts})${r.speaker ? ` ${r.speaker}:` : ""} "${r.said}"${r.finding ? ` **[${r.finding}]**` : ""}`);
      r.taps.length && out.push(`  - tapped then: ${r.taps.map((e) => `${fbsEvShort(e)} at ${fbsHms(e.t)}`).join("; ")}`);
      r.recent.length && out.push(`  - just before: ${r.recent.map((e) => `${fbsEvShort(e)} at ${fbsHms(e.t)}`).join("; ")}`);
    });
    out.push("");
  });
  const F = T.rows.filter((r) => r.finding);
  F.length && out.push("## Flagged", "", ...F.map((r) => `- [${r.finding}] ${fbsHms(r.t)} on ${fbsPageOf(r.page)}: "${r.said}"`), "");
  return out.join("\n");
}
function fbsExportSheet(s) {
  const base = `feedback-timeline-${s.id}-${fbsSlug(s.title)}`;
  const box = mbModal(
    "Export Timeline",
    `<p class="small muted" style="margin-top:0">The transcript beside what was on screen and tapped, line by line, for Claude to read and turn into findings. Markdown reads best; JSON holds the same for a program.</p>`,
    {
      submit: "Download Markdown",
      alt: { label: "Download JSON", run: () => fbsDownload(`${base}.json`, JSON.stringify(fbsTimelineData(s), null, 1), "application/json") && toast(`Saved ${base}.json to your downloads`, [{ label: "Open", run: () => fbsOpen(s.id) }]) },
      onSubmit: () => {
        fbsDownload(`${base}.md`, fbsTimelineMd(s), "text/markdown") && toast(`Saved ${base}.md to your downloads`, [{ label: "Open", run: () => fbsOpen(s.id) }]);
        return !0;
      },
    },
  );
  box && (box.dataset.fbs = "1");
}

// ---- render, sign-in, Ask ----------------------------------------------------------------------------------------------
{
  const base = render;
  render = function () {
    fbsEnsureView();
    const r = base.apply(this, arguments);
    try {
      // a role's list of pages is rebuilt on the way (the foreman's, f3Nav): the session page stays on it
      fbsEnsureView();
      "fbs" === view && renderFbs();
      fbsMountRail();
      fbsLive && (document.getElementById("fbs-bar") ? fbsPlace() : fbsBar());
      fbsLive && setTimeout(() => fbsCheck("render"), 0);
    } catch (e) {
      console.warn("fbs", e);
    }
    return r;
  };
}
if ("function" == typeof signIn) {
  const base = signIn;
  signIn = function () {
    const r = base.apply(this, arguments);
    try {
      fbsEnsureView();
      fbsOpenId = "";
    } catch (e) {}
    return r;
  };
}
if ("object" == typeof EQ_TABLES) {
  // the person's own sessions only, as on Problem Reports
  EQ_TABLES.feedbackSessions = () =>
    fbsMine().map((s) => ({ _id: s.id, _module: "Company", _label: `Feedback session: ${s.title}`, _go: { view: "fbs" }, date: String(s.at || "").slice(0, 10), title: s.title, minutes: Math.round((s.durSec || 0) / 60), steps: (s.events || []).length, marks: s.marks || 0, transcript: s.transcript ? s.transcript.format : "", lines: s.transcript ? s.transcript.lines.length : 0, flagged: Object.keys(s.findings || {}).length, status: s.status }));
  "undefined" != typeof EQ_ALIAS && Object.assign(EQ_ALIAS, { feedback: "feedbackSessions", sessions: "feedbackSessions", feedbacksession: "feedbackSessions" });
}

// ---- the look ----------------------------------------------------------------------------------------------------------
(() => {
  const css = `
.fbs-bar{position:fixed;z-index:9990;bottom:16px;left:16px;max-width:560px;padding:8px 10px 8px 14px;border:1px solid #E7E9EE;border-radius:14px;background:#fff;box-shadow:0 8px 28px rgba(16,24,40,.18);font-size:14px;color:#1A1D23}
.fbs-bar .fbs-row{display:flex;align-items:center;gap:8px;min-width:0}
.fbs-bar .grow{flex:1 1 auto}
.fbs-bar .btn{min-height:44px;display:inline-flex;align-items:center;gap:6px;padding:0 12px;flex:none}
.fbs-bar .btn svg{flex:none}
.fbs-bar .fbs-mk .n{font-style:normal;font-size:12px;font-weight:700;min-width:18px;height:18px;line-height:18px;border-radius:9px;background:#EEF3FD;color:#1D47A8;text-align:center}
.fbs-live{display:inline-flex;align-items:center;gap:8px;height:28px;padding:0 10px;border-radius:999px;background:#FDECEA;color:#B42318;font-size:13px;font-weight:700;white-space:nowrap;flex:none}
.fbs-live::before{content:"";width:8px;height:8px;border-radius:50%;background:#D92D20}
.fbs-paused .fbs-live{background:#F1F3F6;color:#4A5060}
.fbs-paused .fbs-live::before{background:#8A90A0}
.fbs-time{font-variant-numeric:tabular-nums;font-size:15px;min-width:48px;flex:none}
.fbs-hint{margin-top:6px;font-size:13px;line-height:1.35;color:#4A5060}
.fbs-bar.fbs-phone{max-width:none;padding:6px 8px}
.fbs-bar.fbs-phone .fbs-live{font-size:0;gap:0;width:28px;padding:0;justify-content:center}
.fbs-bar.fbs-phone .fbs-bt{display:none}
.fbs-bar.fbs-phone .btn{padding:0 10px}
.fbs-railbtn{display:inline-flex;align-items:center;gap:6px;margin-top:8px;white-space:nowrap}
.fbs-rp{display:flex;flex-direction:column;gap:6px;margin:0 0 12px;padding:10px 12px;border:1px solid var(--rule,#E7E9EE);border-radius:10px;background:#F7F8FA}
.fbs-rp .btn{display:inline-flex;align-items:center;gap:6px;align-self:flex-start;min-height:44px}
#v-fbs .ph .fbs-acts{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
#v-fbs .ph .fbs-acts .btn,#v-rpbox [data-fbsstart]{display:inline-flex;align-items:center;gap:6px;flex:0 0 auto;width:auto;max-width:100%;min-height:44px;white-space:nowrap}
#v-fbs .fbs-pick{max-width:420px;margin:0 0 12px}
#v-fbs .fbs-g,#v-fbs .fbs-tg{margin:0 0 14px}
#v-fbs .fbs-gh{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;padding:8px 0 4px;border-bottom:1px solid var(--rule,#E7E9EE)}
#v-fbs .fbs-gh h3{margin:0;font-size:15px}
#v-fbs .fbs-step{display:grid;grid-template-columns:56px 96px minmax(0,1fr);gap:8px;padding:5px 0;font-size:13px;border-bottom:1px solid #F1F3F6}
#v-fbs .fbs-st{font-variant-numeric:tabular-nums;color:#6A7080}
#v-fbs .fbs-sk{font-weight:600}
#v-fbs .fbs-sx{min-width:0;overflow-wrap:anywhere}
#v-fbs .fbs-k-error .fbs-sk{color:#B42318}
#v-fbs .fbs-k-mark .fbs-sk{color:#1D47A8}
#v-fbs .fbs-align{margin:0 0 14px}
#v-fbs .fbs-arow{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;margin-top:10px}
#v-fbs .fbs-arow .f{margin:0}
#v-fbs .fbs-off input{width:110px}
#v-fbs .fbs-nudge .row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
#v-fbs .fbs-nudge .btn{min-height:44px;min-width:56px}
#v-fbs .fbs-seg{margin-top:8px}
#v-fbs .fbs-seg button{min-height:44px}
#v-fbs .fbs-say{margin:10px 0 0;color:#4A5060}
#v-fbs .fbs-tlh,#v-fbs .fbs-tl{display:grid;grid-template-columns:110px minmax(0,1.3fr) minmax(0,1fr) 230px;gap:12px;align-items:start}
#v-fbs .fbs-tlh{padding:0 0 4px;font-weight:600}
#v-fbs .fbs-tl{padding:8px 0;border-bottom:1px solid #F1F3F6}
#v-fbs .fbs-tt{display:flex;flex-direction:column;font-variant-numeric:tabular-nums}
#v-fbs .fbs-tt small{font-size:12px}
#v-fbs .fbs-spk{font-weight:600}
#v-fbs .fbs-said{min-width:0;overflow-wrap:anywhere}
#v-fbs .fbs-on{min-width:0;overflow-wrap:anywhere;color:#1A1D23}
#v-fbs .fbs-fl{display:flex;gap:8px;flex-wrap:wrap}
#v-fbs .fbs-chip{min-height:44px;padding:0 12px;border:1px solid #D5D9E1;border-radius:999px;background:#fff;font:inherit;font-size:13px;cursor:pointer}
#v-fbs .fbs-chip.on.fbs-problem{background:#FDECEA;border-color:#F4B4AE;color:#B42318}
#v-fbs .fbs-chip.on.fbs-idea{background:#EEF3FD;border-color:#B9CBF3;color:#1D47A8}
#v-fbs .fbs-chip.on.fbs-works{background:#E9F7EF;border-color:#A9DCC0;color:#18794E}
#v-fbs .fbs-has-problem{box-shadow:inset 3px 0 0 #D92D20;padding-left:8px}
#v-fbs .fbs-has-idea{box-shadow:inset 3px 0 0 #2456C9;padding-left:8px}
#v-fbs .fbs-has-works{box-shadow:inset 3px 0 0 #18794E;padding-left:8px}
@media (max-width:819px){
  #v-fbs .fbs-tlh{display:none}
  #v-fbs .fbs-tl{grid-template-columns:minmax(0,1fr);gap:6px}
  #v-fbs .fbs-tt{flex-direction:row;gap:10px;align-items:baseline}
  #v-fbs .fbs-step{grid-template-columns:48px minmax(0,1fr)}
  #v-fbs .fbs-sk{display:none}
  #v-fbs .ph{flex-direction:column;align-items:stretch}
  #v-fbs .ph .fbs-acts{margin-top:8px}
  #v-fbs .fbs-pick{max-width:none}
}
@media print{.fbs-bar{display:none}}`;
  const st = document.createElement("style");
  st.id = "fbs-css";
  st.textContent = css;
  document.head.appendChild(st);
})();
