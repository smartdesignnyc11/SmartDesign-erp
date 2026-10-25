// =====================================================================================================================
// Pilot 2 phone fixes (lane p2fix1, 2026-10-25). Role experts worked the app on a phone and found three classes:
//  S1  a layer outlived its screen and covered every control under it (the estimate's line sheet, #ct-sheet);
//  S2  starting an estimate from a job took twelve taps;
//  S3  controls and pages with no name a screen reader could read.
//
// Design gate (BACKLOG §1.16). No new noun, list, queue or store. The menu gains no item: the phone menu's groups
// open in place to show the pages they already hold (the same entries as the page strip, mnBuild), so the PM's
// Projects > Estimates is two taps from the open menu. New Estimate is the existing button (docNewEstimate) on the
// existing Billing > Estimates tab, which a job's strip already opens.
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

// ---- S2: the phone menu opens a group in place --------------------------------------------------------------------
// The phone menu showed each group as one entry that opened its first page; a page further in (the PM's Estimates,
// under Projects) was a page and a sideways swipe of the strip away. Each group of two or more pages now carries a
// Show Pages toggle; it lists the group's own pages under it, captioned by section, and one tap opens a page.
const P2_CHEV = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>';
let p2MnOpen = "";
function p2MenuGroups() {
  const wrap = document.getElementById("nav-groups");
  if (!wrap || !("function" == typeof mOn && mOn()) || !("function" == typeof mnOn && mnOn())) return;
  const B = mnBuild(role());
  if (!B || B.field) return;
  const G = B.groups.concat(B.more.length ? [{ id: "more", n: "More", items: B.more }] : []).concat(B.bottom ? [B.bottom] : []);
  wrap.querySelectorAll("button[data-grp]").forEach((b) => {
    const g = G.find((x) => x.id === b.dataset.grp);
    if (!g || g.items.length < 2 || b.parentElement.classList.contains("mn-gr")) return;
    const row = document.createElement("div");
    row.className = "mn-gr" + (b.classList.contains("mn-gap") ? " mn-gap" : "");
    b.classList.remove("mn-gap");
    b.before(row), row.appendChild(b);
    const open = p2MnOpen === g.id;
    let last = "";
    const kids = g.items
      .map((it, i) => {
        const cap = it.sec && it.sec !== last ? `<div class="mn-kcap">${esc(it.sec)}</div>` : "";
        return (last = it.sec), `${cap}<a href="#" role="button" class="mn-kid" data-mnkid="${g.id}:${i}">${esc(it.l)}</a>`;
      })
      .join("");
    row.insertAdjacentHTML(
      "beforeend",
      `<a href="#" role="button" class="mn-exp" data-mnexp="${g.id}" aria-expanded="${open}" aria-label="Show ${esc(g.n)} Pages">${P2_CHEV}</a><div class="mn-kids" ${open ? "" : "hidden"}>${kids}</div>`,
    );
    row.querySelector(".mn-exp").onclick = (e) => {
      e.preventDefault(), e.stopPropagation();
      p2MnOpen = p2MnOpen === g.id ? "" : g.id;
      wrap.querySelectorAll(".mn-gr").forEach((r) => {
        const on = r.querySelector(".mn-exp").dataset.mnexp === p2MnOpen;
        r.querySelector(".mn-exp").setAttribute("aria-expanded", on), (r.querySelector(".mn-kids").hidden = !on);
      });
    };
    row.querySelectorAll("[data-mnkid]").forEach(
      (a) =>
        (a.onclick = (e) => {
          e.preventDefault(), e.stopPropagation();
          const it = g.items[+a.dataset.mnkid.split(":")[1]];
          // leave a record the way the group's own entry does (the rail's click pass clears the open record)
          try {
            if ("undefined" != typeof docOpen && docOpen) {
              const c = (DB.clients || []).find((x) => x.id === clientOpen),
                d = c && findDoc(c, docOpen.kind, docOpen.id);
              d && "function" == typeof docLeave && docLeave(c, d), (docOpen = null);
            }
            "undefined" != typeof poOpen && (poOpen = null), "undefined" != typeof clientOpen && (clientOpen = null);
          } catch (x) {}
          it && mnGo(g, it);
        }),
    );
  });
}
if ("function" == typeof mnRail) {
  const base = mnRail;
  mnRail = function () {
    const r = base.apply(this, arguments);
    try {
      p2MenuGroups();
    } catch (e) {
      console.warn("menu groups", e);
    }
    return r;
  };
}
// the open group follows the page on screen when the menu opens
document.addEventListener(
  "click",
  (e) => {
    if (!e.target.closest || !e.target.closest("#menu-btn")) return;
    try {
      const cur = mnCur(mnBuild(role()));
      p2MnOpen = (cur && cur.g.id) || p2MnOpen;
      document.querySelectorAll("#nav-groups .mn-gr").forEach((r) => {
        const on = r.querySelector(".mn-exp").dataset.mnexp === p2MnOpen;
        r.querySelector(".mn-exp").setAttribute("aria-expanded", on), (r.querySelector(".mn-kids").hidden = !on);
      });
    } catch (x) {}
  },
  !0,
);

// ---- S3: every control and every page has a name ---------------------------------------------------------------------
// A page's section carries its menu name (a screen reader read the Daily Log as "v-flog"), and an icon-only control
// with a title reads its title. Controls drawn without either are named where they are drawn.
function p2Names() {
  const v = document.querySelector(".view.on");
  if (v) {
    let n = "";
    try {
      const cur = "function" == typeof mnCur && mnCur(mnBuild(role()));
      n = (cur && cur.it.l) || ("function" == typeof mnLabel ? mnLabel(view) : "");
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
(() => {
  const css = `
#nav-groups .mn-gr{display:grid;grid-template-columns:1fr 44px;align-items:stretch;column-gap:4px;position:relative}
#nav-groups .mn-gr.mn-gap{margin-top:14px}
#nav-groups .mn-gr.mn-gap::before{content:"";position:absolute;left:10px;right:10px;top:-8px;border-top:1px solid rgba(255,255,255,.12)}
#nav-groups .mn-gr>button{min-width:0}
#nav-groups .mn-exp{display:flex;align-items:center;justify-content:center;min-height:44px;border-radius:8px;color:inherit;opacity:.8}
#nav-groups .mn-exp[aria-expanded=true] svg{transform:rotate(180deg)}
#nav-groups .mn-kids{grid-column:1/3;display:flex;flex-direction:column;padding:2px 0 8px 38px}
#nav-groups .mn-kids[hidden]{display:none}
#nav-groups .mn-kid{display:flex;align-items:center;min-height:44px;padding:0 10px;border-radius:8px;color:inherit;text-decoration:none;font-size:15px}
#nav-groups .mn-kcap{font-size:11.5px;letter-spacing:.04em;text-transform:uppercase;opacity:.6;padding:8px 10px 2px}
`;
  const st = document.createElement("style");
  (st.id = "p2fix-css"), (st.textContent = css), document.head.appendChild(st);
})();
