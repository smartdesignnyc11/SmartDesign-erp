// =====================================================================================================================
// Pilot 2 phone fixes (lane p2fix1, 2026-10-25). Role experts worked the app on a phone and found three classes:
//  S1  a layer outlived its screen and covered every control under it (the estimate's line sheet, #ct-sheet);
//  S2  starting an estimate from a job took twelve taps;
//  S3  controls and pages with no name a screen reader could read.
//
// Design gate (BACKLOG §1.16). No new noun, list, queue or store. The phone menu's groups opened in place here (an
// arrow beside each); the 11-03 menu (src/app.js, the menu section) folds that in: a group opens on its name. New
// Estimate is the existing button (docNewEstimate) on the existing Billing > Estimates tab, which a job's strip opens.
// =====================================================================================================================

// ---- S1: a sheet on <body> belongs to the screen that opened it ------------------------------------------------------
// The line sheet is a full-screen layer appended to <body>; only its own Done closed it. Escape, the phone's Back and a
// move to another page left it on top of the next screen, so every tap went to it. A sheet registered here closes
// when the screen changes (another page, record or job), on Escape and on Back. What was typed is committed first:
// the focused field is blurred, so its change event saves it, before the sheet goes.
const P2_SHEETS = [
  { sel: "#ct-sheet", close: (redraw) => (ctCloseSheet(), save(), redraw && render()) },
  { sel: "#msg-sheet", close: () => "function" == typeof msgSheetClose && msgSheetClose() },
  { sel: "#tv-pop", close: () => "function" == typeof tvPopClose && tvPopClose() },
];
function p2SheetOpen() {
  return P2_SHEETS.find((s) => document.querySelector(s.sel)) || null;
}
function p2CloseSheets(redraw) {
  let n = 0;
  P2_SHEETS.forEach((s) => {
    const el = document.querySelector(s.sel);
    if (!el) return;
    const a = document.activeElement;
    a && el.contains(a) && a.blur && a.blur();
    try {
      s.close(redraw), n++;
    } catch (e) {
      console.warn("sheet close", e);
      el.remove();
    }
  });
  return n;
}
const p2ScreenKey = () => {
  try {
    return [view, "undefined" != typeof docOpen && docOpen ? docOpen.kind + ":" + docOpen.id : "", "undefined" != typeof poOpen ? poOpen || "" : "", "undefined" != typeof clientOpen ? clientOpen || "" : "", S && S.id].join("|");
  } catch (e) {
    return "";
  }
};
let p2LastKey = null;
{
  const base = render;
  render = function () {
    const k = p2ScreenKey();
    p2LastKey !== null && k !== p2LastKey && p2SheetOpen() && p2CloseSheets(!1);
    p2LastKey = k;
    return base.apply(this, arguments);
  };
}
window.addEventListener("keydown", (e) => {
  // a picker or a dialog on top answers its own Escape first (the item list, a modal over the sheet)
  if ("Escape" !== e.key || e.defaultPrevented || document.getElementById("mbm") || document.querySelector(".itp")) return;
  p2SheetOpen() && (e.preventDefault(), p2CloseSheets(!0));
});
window.addEventListener("popstate", () => p2SheetOpen() && p2CloseSheets(!0));

// ---- S1: nothing scrolls a control under the bars -------------------------------------------------------------------
// The browser brings a control into view at the bottom edge when it is focused, linked to or tapped by a tool: on the
// phone that edge is under the bottom bar (and Say It, a wizard's step bar), so the owner's approval button below the
// first screen of an estimate came up "covered by another element", and a field focused at the bottom typed blind.
// The page's scroll padding is the height of what is fixed at its top and foot, measured, on every draw and resize.
const P2_FOOT = "#mtabs, #tabbar, #fsay, .dl-nav, .m-callbar, [data-fixedbar]";
function p2ScrollPad() {
  // the page scrolls on <html> or on <body> depending on the screen (html/body overflow-x): both carry the padding
  const els = [document.documentElement, document.body],
    set = (t, f) => els.forEach((de) => ((de.style.scrollPaddingTop = t), (de.style.scrollPaddingBottom = f)));
  if (!("function" == typeof mOn && mOn())) return void set("", "");
  const H = innerHeight;
  let top = 0,
    foot = H;
  document.querySelectorAll("header.topbar, #subnav").forEach((e) => {
    if (!e.getClientRects().length || !/fixed|sticky/.test(getComputedStyle(e).position)) return;
    const r = e.getBoundingClientRect();
    r.top < H / 3 && (top = Math.max(top, r.bottom));
  });
  document.querySelectorAll(P2_FOOT).forEach((e) => {
    if (!e.getClientRects().length || "fixed" !== getComputedStyle(e).position) return;
    const r = e.getBoundingClientRect();
    r.height > 0 && r.top > H / 2 && (foot = Math.min(foot, r.top));
  });
  set(Math.round(top + 8) + "px", Math.round(H - foot + 8) + "px");
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      p2ScrollPad();
    } catch (e) {}
    return r;
  };
}
window.addEventListener("resize", () => {
  try {
    p2ScrollPad();
  } catch (e) {}
});

// ---- S2: New Estimate for the job, from the job's Estimates tab ------------------------------------------------------
// Billing > Estimates is where a job's strip lands (MN_JOBS: ["billing", "Estimates", "estimates"]). Its New Estimate
// starts for the job the strip came from, not only the client: the job is S when the person came through Projects.
function p2EstContext() {
  const k = "function" == typeof crDocContext ? crDocContext() : {};
  try {
    if ("billing" === view && "jobs" === mnLastGrp && S && S.clientId && (!k.clientId || k.clientId === S.clientId)) return { clientId: S.clientId, projectId: S.id };
  } catch (e) {}
  return k;
}

// ---- S3: every control and every page has a name ---------------------------------------------------------------------
// A page's section carries its menu name (a screen reader read the Daily Log as "v-flog"), and an icon-only control
// with a title reads its title. Controls drawn without either are named where they are drawn.
function p2Names() {
  const v = document.querySelector(".view.on");
  if (v) {
    let n = "";
    try {
      // the page's menu name (inside a job, its tab's; the job's name is the record's)
      const cur = "function" == typeof mnCur && mnCur(mnBuild(role()));
      n = ("function" == typeof mnCurLabel && mnCurLabel(cur)) || ("function" == typeof mnLabel ? mnLabel(view) : "");
    } catch (e) {}
    n && n !== view && v.getAttribute("aria-label") !== n && v.setAttribute("aria-label", n);
    v.getAttribute("role") || v.setAttribute("role", "region");
  }
  document.querySelectorAll(".view.on button:not([aria-label]), .view.on a:not([aria-label]), header.topbar button:not([aria-label])").forEach((b) => {
    if ((b.textContent || "").trim()) return;
    const t = (b.getAttribute("title") || "").trim();
    t && b.setAttribute("aria-label", t);
  });
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      p2Names();
    } catch (e) {
      console.warn("names", e);
    }
    return r;
  };
}
