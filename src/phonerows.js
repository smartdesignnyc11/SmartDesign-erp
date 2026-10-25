// =====================================================================================================================
// Phone rows (lane phonerows, 2026-10-25; the mobile designer's review, findings 6, 8, 9, 10, 12 and 22, and "What would
// make this a 9" item 1). One phone row for every list the phone opens: a title, one meta line, an optional chip and
// the row's one action, 64px tall at least, 44px targets. It is the Tasks row (src/tasks.js tkRowHtml) made general.
//
// Design gate (BACKLOG §1.16). No new noun, list, queue or menu item. Every list stays the list it was, on the page it
// was; this file changes how a list is drawn under 760px (mOn), never what is in it, so every count is untouched:
//  - mCardTables (app.js), the one place a table became a phone card, now makes phone rows (prTable). The label/value
//    card and its "+ N More" are gone; a row whose record has no page of its own opens in place (the same cells).
//  - Card lists the phone opens (Approvals, Deliveries) fold to the same row (prCards); a tap opens the card.
//  - A page's own row content (Projects, Decisions, Bills & Payroll, Clients, Invoices, Estimates, Change Orders,
//    Vendors) is a spec in PR_SPECS, read off the row's own record.
//  - Phone search is the existing palette (#pal) as a full-height sheet with grouped two-line rows (prSearch).
//  - The foreman's Today keeps its cards and orders them (prFieldToday): Clock In, Today's Work, Arriving Today,
//    Questions, then the rest behind one "More for Today".
// Desktop is untouched: every pass here returns at once above 760px. tests/phone_rows_lint.py holds the rule.
// =====================================================================================================================
const PR_ON = () => "function" == typeof mOn && mOn(),
  // a field person's rows are read by the Spanish pass (the meta line holds the app's words: "expected", "received")
  PR_FIELD = () => ["foreman", "crew", "driver"].includes(role());
function prRowHtml(o) {
  const chip = o.chip ? `<span class="pr-chip ${o.chip.tone || ""}">${esc(o.chip.t)}</span>` : "",
    dot = o.dot ? `<i class="pr-dot ${o.dot}" aria-hidden="true"></i>` : "";
  return `<div class="pr-row ${o.cls || ""}"${o.attrs ? " " + o.attrs : ""}>${dot}<div class="pr-mid"><div class="pr-t"${PR_FIELD() ? "" : " data-nocase"}>${o.titleHtml || esc(o.title || "")}</div>${o.meta || chip ? `<div class="pr-m">${chip}<span${PR_FIELD() ? "" : " data-nocase"}>${esc(o.meta || "")}</span></div>` : ""}</div><span class="pr-act-slot"></span></div>`;
}
const prTxt = (el) => (el ? (el.textContent || "").replace(/\s+/g, " ").trim() : ""),
  prTone = (el) => {
    const p = el && (el.matches && el.matches(".pill") ? el : el.querySelector(".pill"));
    if (!p) return "";
    return ["bad", "warn", "ok", "info"].find((t) => p.classList.contains(t)) || "";
  },
  prMd = (s) => {
    // "8/26" or "8/26/2027" on a row, read in the app's year
    const m = String(s || "").match(/(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?/);
    if (!m) return "";
    const y = m[3] ? (m[3].length === 2 ? "20" + m[3] : m[3]) : today().slice(0, 4);
    return `${y}-${String(m[1]).padStart(2, "0")}-${String(m[2]).padStart(2, "0")}`;
  };
// ---- the row look ---------------------------------------------------------------------------------------------------
(() => {
  const css = `
.pr-row{display:flex;align-items:center;gap:10px;min-height:64px;padding:8px 12px 8px 14px;box-sizing:border-box;background:var(--paper);cursor:pointer;text-align:left;width:100%}
.pr-row:hover{background:var(--paper-2)}
.pr-mid{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:2px}
.pr-t{font-size:16px;line-height:20px;color:var(--ink);font-weight:500;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;word-break:break-word}
.pr-t .sub,.pr-t small{font-weight:400;color:var(--ink-3);font-size:13px;margin-left:6px}
.pr-m{font-size:13px;line-height:17px;color:var(--ink-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pr-m.late,.pr-row.late .pr-m b{color:var(--bad,#b3261e)}
.pr-chip{display:inline-block;vertical-align:-5px;max-width:58%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:600;line-height:18px;padding:0 8px;margin-right:6px;border-radius:9px;background:var(--paper-2);color:var(--ink-2)}
.pr-chip.bad{background:#fbe9e7;color:var(--bad,#b3261e)} .pr-chip.warn{background:#fdf3dc;color:#8a5a00} .pr-chip.ok{background:#e6f4ea;color:var(--ok-2,#2e7d32)} .pr-chip.info{background:var(--accent-2,#e8eefb);color:var(--accent)}
.pr-dot{flex:0 0 10px;width:10px;height:10px;border-radius:50%;background:var(--ink-4,#c4c8cf)}
.pr-dot.ok{background:var(--ok,#2e7d32)} .pr-dot.warn{background:var(--warn,#c98a00)} .pr-dot.bad{background:var(--bad,#b3261e)}
.pr-act-slot{flex:0 0 auto;display:flex}
.pr-act-slot:empty{display:none}
.pr-act-slot>.btn,.pr-act-slot>button{min-height:44px !important;min-width:64px;padding:0 14px;border-radius:22px;font-size:14px;font-weight:600;white-space:nowrap}
.pr-act-slot>.btn:not(.primary){background:var(--paper);border:1px solid var(--rule);color:var(--ink)}
.pr-row.pr-sev3{box-shadow:inset 3px 0 0 var(--bad,#b3261e)} .pr-row.pr-sev2{box-shadow:inset 3px 0 0 var(--warn,#c98a00)}
@media (max-width:760px){
  table.pr-tbl{display:block;width:100% !important;min-width:0 !important;border:0;background:transparent;table-layout:auto}
  table.pr-tbl>thead,table.pr-tbl>tfoot{display:none}
  table.pr-tbl>tbody{display:block}
  table.pr-tbl>tbody>tr{display:block;border:0;border-bottom:1px solid var(--rule-2);background:var(--paper);margin:0;padding:0;border-radius:0;min-height:0}
  table.pr-tbl>tbody>tr.pr-tr>td{display:none}
  table.pr-tbl>tbody>tr.pr-tr>td.pr-cell{display:block;padding:0;border:0;width:auto !important;height:auto;white-space:normal;background:transparent}
  table.pr-tbl>tbody>tr.pr-tr>td.pr-cell::before{display:none !important;content:none !important}
  table.pr-tbl>tbody>tr.pr-tr.pr-open>td:not(.pr-cell):not(:empty):not(.pr-moved){display:flex;justify-content:space-between;align-items:baseline;gap:12px;padding:4px 14px 4px 38px;border:0;font-size:14px;line-height:1.35;white-space:normal;text-align:right;width:auto !important;height:auto}
  table.pr-tbl>tbody>tr.pr-tr.pr-open>td:not(.pr-cell)::before{content:attr(data-l);display:block;color:var(--ink-3);font-size:12.5px;text-align:left;flex:0 0 40%;margin:0}
  table.pr-tbl>tbody>tr.pr-tr.pr-open{padding-bottom:8px;background:var(--paper-2)}
  table.pr-tbl>tbody>tr.pr-flat{display:block;padding:14px 14px 6px;font-size:13px;font-weight:600;color:var(--ink-2);background:none;border-bottom:1px solid var(--rule-2)}
  table.pr-tbl>tbody>tr.pr-flat>td{display:inline;border:0;padding:0;background:none}
  table.pr-tbl>tbody>tr.pr-flat>td::before{content:none !important;display:none !important}
  table.pr-tbl>tbody>tr.pr-flat>td:empty{display:none}
  .dg:has(table.pr-tbl),.tw:has(table.pr-tbl),.card:has(> .tw > table.pr-tbl){overflow:hidden}
  .dg-scroll:has(> table.pr-tbl),.tw:has(> table.pr-tbl){overflow:visible !important;margin:0;padding:0}
  .pr-card{padding:0 !important;overflow:hidden}
  .pr-card>:not(.pr-row){display:none !important}
  .pr-card.pr-open>:not(.pr-row){display:revert !important}
  .pr-card.pr-open>.pr-row{border-bottom:1px solid var(--rule-2)}
  .pr-card.pr-open{padding:0 0 10px !important}
  .pr-card.pr-open>:not(.pr-row){margin-left:14px;margin-right:14px}
  .pr-cards{gap:0 !important}
  .pr-cards.pr-own{border:1px solid var(--rule);border-radius:10px;overflow:hidden;background:var(--paper)}
  .pr-cards>.pr-card{margin:0 !important;border:0 !important;border-radius:0 !important;border-bottom:1px solid var(--rule-2) !important;box-shadow:none !important}
  /* a list page's own buttons sit on one line; the blue one is the safe next step (the urgent row's, when there is one) */
  .view.pr-page .ph{margin-bottom:8px}
  .view.pr-page .ph .lead{display:none}
  .view.pr-page .ph .acts{display:flex;flex-wrap:wrap;gap:8px;width:100%}
  .view.pr-page .ph .acts>.btn{flex:1 1 0;width:auto;min-width:0;min-height:44px}
  /* every target on a phone page is 44px tall (lint TARGET_SMALL): the shared classes, not each button; the
     Tasks page is the taskfix lane's and sets its own */
  .view:not(#v-tkall):not(#v-tasks) .btn,.view:not(#v-tkall):not(#v-tasks) .btn.sm,.view:not(#v-tkall):not(#v-tasks) .seg button,.view:not(#v-tkall):not(#v-tasks) .ctabs button,.view:not(#v-tkall):not(#v-tasks) .sub-tabs button,.view:not(#v-tkall):not(#v-tasks) select,.view:not(#v-tkall):not(#v-tasks) input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=file]),.view:not(#v-tkall):not(#v-tasks) .chip,.view:not(#v-tkall):not(#v-tasks) .hb-btn,.view:not(#v-tkall):not(#v-tasks) .hb-viewtab,.view:not(#v-tkall):not(#v-tasks) [role=tab],.view:not(#v-tkall):not(#v-tasks) .nm-act,.view:not(#v-tkall):not(#v-tasks) .mic,.view:not(#v-tkall):not(#v-tasks) .ov-stat,.view:not(#v-tkall):not(#v-tasks) [role=button],.view:not(#v-tkall):not(#v-tasks) .sel-rooms button,.view:not(#v-tkall):not(#v-tasks) .sp-groups button,.view:not(#v-tkall):not(#v-tasks) .sp-nav button{min-height:44px !important}
  .view:not(#v-tkall):not(#v-tasks) .glance.tl>.gl,.view:not(#v-tkall):not(#v-tasks) .glance.tl-auto>.gl{height:44px !important;min-height:44px !important}
  .view:not(#v-tkall):not(#v-tasks) .seg{min-height:44px}
  .view:not(#v-tkall):not(#v-tasks) input.q{height:44px !important}
  .view:not(#v-tkall):not(#v-tasks) label.chip{min-height:44px !important}
  .view:not(#v-tkall):not(#v-tasks) .hb-pill{height:auto;min-height:44px}
  body.pr-v-ovjobs #subnav .sub-proj{display:none}
  .view .hb-dash{grid-template-columns:minmax(0,1fr) !important}
  .view .pr-hide{display:none !important}
}`;
  const s = document.createElement("style");
  (s.id = "pr-css"), (s.textContent = css), document.head.appendChild(s);
})();
// ---- tables become rows ---------------------------------------------------------------------------------------------
// The cells keep their handlers: the row's one action is the row's own button, moved into the row; the cell that named
// the record keeps its link. A row with a page of its own (data-edit and the like) opens it on a tap, as on desktop;
// a row without one opens in place to the cells it had (label and value), so nothing the card showed is lost.
const PR_SKIP = ".m-keep, .gantt-wrap, .gantt, .docwrap, .prev, .mbm, .drawer, [data-chart], .cal, .cal-grid, .tv-cal, .pr-keep",
  PR_TITLE_RE = /^(memo|name|title|description|item|subject|file|project|client|vendor|decision needed|what|bill|opportunity|meeting|obligation|material|inspection|person|contact|account|transaction|task|document|drawing|sheet)\b/i;
function prHeads(t) {
  const row = t.tHead && t.tHead.rows[0];
  return row ? [...row.cells].map((th) => prTxt(th).replace(/[↑↓⋮▾▴]/g, "").trim()) : [];
}
function prCandidate(t) {
  if (t.classList.contains("pr-tbl") || t.closest(PR_SKIP) || t.classList.contains("lines") || t.classList.contains("to")) return !1;
  const H = prHeads(t);
  if (H.length >= 4) return !0;
  // a narrow table that still runs past its box (three wide columns) is a list too
  if (H.length === 3) {
    const r = t.getBoundingClientRect(), p = t.parentElement && t.parentElement.getBoundingClientRect();
    return !!(p && r.width > p.width + 1);
  }
  return !1;
}
// the row read the generic way: the cell that names the record, up to three short facts, the first status pill, the
// first button
function prGeneric(tr, cells, H) {
  const named = cells.findIndex((td, i) => PR_TITLE_RE.test(H[i] || "") && /[A-Za-z]{2}/.test(prTxt(td)) && !td.querySelector("select, input")),
    first = cells.findIndex((td) => /[A-Za-z]{3}/.test(prTxt(td)) && !td.querySelector("select, input, button") && !td.querySelector(".pill")),
    ti = named >= 0 ? named : first >= 0 ? first : 0,
    tcell = cells[ti],
    chipCell = cells.find((td, i) => i !== ti && td.querySelector(".pill")),
    act = [...tr.querySelectorAll("button, a.btn, .btn")].find((b) => !tcell.contains(b) && !b.closest(".m-more") && !b.closest("[data-l=''], .sel") && prTxt(b).length > 1),
    facts = [];
  cells.forEach((td, i) => {
    if (i === ti || td === chipCell || td.querySelector("button, select, input, textarea") || facts.length >= 3) return;
    const s = prTxt(td);
    if (!s || "—" === s || "-" === s || s.length > 60) return;
    facts.push(s);
  });
  return {
    titleHtml: tcell.innerHTML.replace(/<(button|select|input)[\s\S]*?(<\/\1>|>)/g, ""),
    meta: facts.join(" · "),
    chip: chipCell ? { t: prTxt(chipCell.querySelector(".pill")), tone: prTone(chipCell) } : null,
    actEl: act || null,
  };
}
function prTable(t, spec) {
  const H = prHeads(t);
  t.classList.remove("m-cards", "rx-cards", "wide");
  t.classList.add("pr-tbl");
  [...t.tBodies].forEach((tb) =>
    [...tb.rows].forEach((tr) => {
      if (tr.querySelector(":scope > td.pr-cell")) return;
      tr.querySelectorAll(":scope > td.m-more").forEach((x) => x.remove());
      const cells = [...tr.cells];
      if (tr.classList.contains("grp") || tr.classList.contains("sec") || tr.classList.contains("m-row-flat") || cells.length < 2 || (cells.length === 1 && cells[0].colSpan > 1))
        return void tr.classList.add("pr-flat");
      cells.forEach((td, i) => {
        td.classList.remove("m-hide", "m-title");
        !td.dataset.l && H[i] && (td.dataset.l = H[i]);
      });
      const get = (re) => cells[H.findIndex((h) => re.test(h))] || null;
      let o = null;
      try {
        o = spec ? spec(tr, get, cells, H) : null;
      } catch (e) {
        console.warn("phone row", e);
      }
      o = o || prGeneric(tr, cells, H);
      const cell = document.createElement("td");
      cell.className = "pr-cell";
      cell.colSpan = cells.length || 1;
      const sev = tr.classList.contains("sev3") ? "pr-sev3" : tr.classList.contains("sev2") ? "pr-sev2" : "";
      cell.innerHTML = prRowHtml(Object.assign({ cls: [sev, o.late ? "late" : ""].join(" ") }, o));
      const slot = cell.querySelector(".pr-act-slot");
      if (o.actEl) {
        const home = o.actEl.closest("td");
        slot.appendChild(o.actEl);
        o.label && (o.actEl.textContent = o.label);
        home && !prTxt(home) && !home.querySelector("button, select, input") && home.classList.add("pr-moved");
      } else if (o.actHtml) slot.innerHTML = o.actHtml;
      // one blue button a page: a moved button keeps its blue only where a spec says it is the urgent one
      o.actEl && !o.primary && o.actEl.classList.remove("primary");
      tr.appendChild(cell);
      tr.classList.add("pr-tr");
      const opens = !!(tr.onclick || [...tr.attributes].some((a) => /^data-/.test(a.name) && !/^data-(l|nocase|sev)$/.test(a.name)) || tr.classList.contains("click"));
      if (!opens) {
        const link = cells.map((td) => td.querySelector("a[href]:not([href^='tel']):not([href^='mailto']), [data-open], [data-edit]")).find(Boolean);
        cell.addEventListener("click", (e) => {
          if (e.target.closest(".pr-act-slot")) return;
          if (link) return void link.click();
          tr.classList.toggle("pr-open");
        });
      }
    }),
  );
}
// Card lists the phone opens fold to rows: the card stays (its buttons, inputs and handlers), drawn as its row until
// tapped; the row's one action is the card's own first button.
function prCards(list, sel, spec) {
  if (!list) return;
  const cards = [...list.querySelectorAll(":scope > " + sel)].filter((c) => !c.classList.contains("pr-card"));
  if (!cards.length) return;
  list.classList.add("pr-cards");
  cards.forEach((c) => {
    let o = null;
    try {
      o = spec(c);
    } catch (e) {
      console.warn("phone card row", e);
    }
    if (!o) return;
    c.classList.add("pr-card");
    const w = document.createElement("div");
    w.innerHTML = prRowHtml(o);
    const row = w.firstElementChild;
    c.prepend(row);
    o.actEl && (row.querySelector(".pr-act-slot").appendChild(o.actEl), o.primary || o.actEl.classList.remove("primary"));
    row.addEventListener("click", (e) => {
      if (e.target.closest(".pr-act-slot")) return;
      c.classList.toggle("pr-open");
    });
  });
}
// Any other card list the phone opens, found the way tests/phone_rows_lint.py finds one: three or more full-width cards
// of one kind side by side, each with its own controls, fewer than four to a screen. Each folds to the row the card
// would say first: its bold line, its first small line, its status pill, its verb (a blue one, else the first that is
// not Open, Call, Text or Message: those stay in the card, a tap away). Sections that group records (a week of the
// look-ahead, a day of photos, a chain of checks, the field's cards) are not records: PR_SECTIONS, read by the lint too.
const PR_SECTIONS = ["card", "f-card", "portlet", "tw", "msg", "t2-group", "td-card", "nm-band", "hd", "row", "f", "grid2", "kpi", "kpis", "ph", "glance", "acts", "la-week", "pst-day", "cs-chainblock", "tk2-row", "gl", "sec", "section"];
const PR_PASSIVE = /^(open|call|text|message|email|view|show|hide|more|less|why|details?)\b/i;
function prCardGeneric(c) {
  const t = [...c.querySelectorAll("h3, h4, b, strong, .title, .t")].find((e) => !e.closest("button, a, .pill") && /[A-Za-z]{3}/.test(prTxt(e)));
  if (!t) return null;
  const sm = [...c.querySelectorAll(".small, .muted, .sub, .s, p")].find((e) => !e.contains(t) && !t.contains(e) && !e.closest("button") && prTxt(e).length > 2),
    pill = c.querySelector(".pill, .tag, .badge"),
    btns = [...c.querySelectorAll("button, a.btn, .btn")].filter((b) => prTxt(b).length > 1 && !b.closest(".pr-row")),
    act = btns.find((b) => b.classList.contains("primary")) || btns.find((b) => !PR_PASSIVE.test(prTxt(b)) && !b.matches("a[href^='tel'], a[href^='mailto'], a[href^='sms']")) || null;
  return {
    title: prTxt(t),
    meta: sm ? prTxt(sm).slice(0, 140) : "",
    chip: pill && !t.contains(pill) ? { t: prTxt(pill), tone: prTone(pill) } : null,
    cls: c.classList.contains("bad") || c.classList.contains("sev3") ? "pr-sev3" : c.classList.contains("warn") || c.classList.contains("sev2") ? "pr-sev2" : "",
    actEl: act,
  };
}
function prFoldCards(v) {
  const W = v.getBoundingClientRect().width || vw(),
    usable = (window.innerHeight || 844) - 120,
    found = [];
  v.querySelectorAll("*").forEach((p) => {
    if (p.children.length < 3 || "TBODY" === p.tagName || "TR" === p.tagName || "TABLE" === p.tagName || p.closest("table, .pr-card, .tk2-list, #mbm, .mbm, .gantt-wrap, .pr-keep")) return;
    const by = {};
    for (const c of p.children) {
      const k = [...c.classList].filter((x) => "card" !== x && !/^(on|bad|warn|ok|info|late|sev\d|open)$/.test(x))[0];
      if (!k || PR_SECTIONS.includes(k) || /^pr-/.test(k) || c.classList.contains("pr-card")) continue;
      (by[k] = by[k] || []).push(c);
    }
    Object.entries(by).forEach(([k, cs]) => {
      if (cs.length < 3) return;
      const hs = cs.map((c) => [c.offsetWidth, c.offsetHeight]);
      if (hs.some(([w, h]) => !h || w < W * 0.75)) return;
      if (!cs.every((c) => c.querySelector("button, select, input"))) return;
      const avg = hs.reduce((s, x) => s + x[1], 0) / hs.length;
      Math.floor(usable / avg) < 4 && found.push([p, k]);
    });
  });
  found.forEach(([p, k]) => prCards(p, "." + k, prCardGeneric));
}
// ---- what each page's row says ----------------------------------------------------------------------------------------
const PR_SPECS = {
  // Projects (finding 6): one row per job: the name, a health dot, what needs me, the next milestone
  ovjobs: (tr, get) => {
    const name = get(/^project/i);
    if (!name) return null;
    const health = get(/^health/i),
      need = prTxt(get(/^needs/i)),
      next = prTxt(get(/^next/i)).replace(/^(\d{1,2}\/\d{1,2})\s+Starts:\s*/i, "$1 "),
      first = String(tr.title || "").split(" · ")[0].replace(/^Decision:\s*/i, ""),
      bits = [];
    +need ? bits.push(`${need} need${"1" === need ? "s" : ""} you${first ? ": " + first : ""}`) : bits.push("Nothing needs you");
    next && bits.push("Next " + next);
    return { title: prTxt(name), dot: prTone(health) || "ok", meta: bits.join(" · ") };
  },
  // Decisions (finding 9): what, who owes it, what it holds up, days late; the action is Decide (the Record It sheet)
  dec: (tr, get) => {
    const what = get(/^decision/i);
    if (!what) return null;
    const by = prTxt(get(/^owed/i)),
      blocks = prTxt(get(/^blocks/i)).replace(/^(Order|Task):\s*/i, ""),
      due = prMd(prTxt(get(/^due/i))),
      late = due && due < today() ? dayDiff(due, today()) : 0,
      act = tr.querySelector("[data-decided]"),
      bits = [by ? "Owed by " + by : "", blocks ? "holds up " + blocks : ""].filter(Boolean);
    late ? bits.unshift(`${late} day${1 === late ? "" : "s"} late`) : due && bits.push("due " + fmt(due));
    return { title: prTxt(what), meta: bits.join(" · "), late: !!late, actEl: act, label: "Decide" };
  },
  // Bills & Payroll (finding 8): the vendor and bill number, amount and due, the one status
  ap: (tr, get) => {
    const item = get(/^(item|bill)$/i);
    if (!item) return null;
    const amt = prTxt(get(/^amount/i)),
      due = prTxt(get(/^due/i)) || prTxt(get(/^date/i)),
      proj = prTxt(get(/^project/i)),
      st = get(/^status/i),
      act = tr.querySelector("[data-finbill]");
    return {
      titleHtml: item.innerHTML.replace(/<span class="sub">/, '<span class="sub">'),
      meta: [amt, due ? (get(/^due/i) ? "due " : "") + due : "", proj].filter(Boolean).join(" · "),
      chip: st && st.querySelector(".pill") ? { t: prTxt(st.querySelector(".pill")), tone: prTone(st) } : null,
      actEl: act,
      primary: !!act,
    };
  },
  // Clients (finding 22): the name, who, what they owe us, the last contact
  clients: (tr, get) => {
    const name = get(/^client/i);
    if (!name) return null;
    const id = ((tr.dataset.edit || "").split(":")[1] || "").trim();
    let owed = 0;
    try {
      owed = (("function" == typeof arRows && arRows()) || []).filter((r) => r.c && r.c.id === id).reduce((a, r) => a + (+r.bal || 0), 0);
    } catch (e) {}
    const who = prTxt(get(/^(person|contact)/i)),
      last = prTxt(get(/^last/i)),
      bits = [who, owed ? "owes " + money(owed) : "", last && "—" !== last ? "last contact " + last : "no contact logged"].filter(Boolean);
    return { title: prTxt(name), meta: bits.join(" · "), chip: owed ? null : null };
  },
  // Vendors: the name and trade, what is wrong (insurance, W-9, banking), what we paid
  vendors: (tr, get) => {
    const name = get(/^vendor/i);
    if (!name) return null;
    const st = get(/^status/i),
      bits = [prTxt(get(/^trade/i)), prTxt(get(/^paid/i)) ? "paid " + prTxt(get(/^paid/i)) : "", String(tr.title || "").split(" · ")[0]].filter((x) => x && "—" !== x);
    return { title: prTxt(name), meta: bits.join(" · "), chip: st && st.querySelector(".pill") ? { t: prTxt(st.querySelector(".pill")), tone: prTone(st) } : null };
  },
};
// Billing's tabs (Invoices, Estimates, Change Orders, Billable): the document's title and number, the amount and date
PR_SPECS.billing = (tr, get, cells, H) => {
  const num = get(/^(#|no\.?|number|invoice|estimate|change order|co)$/i),
    title = get(/^(title|what|description|name)$/i),
    total = get(/^(total|amount|balance|due amount)$/i),
    date = get(/^(date|sent|issued|due)$/i),
    st = get(/^(status|stage|where it stands)$/i);
  if (!num && !title) return null;
  const t = prTxt(title) || prTxt(num),
    bits = [title && num ? prTxt(num) : "", prTxt(total), prTxt(date), prTxt(get(/^(job|project|client)$/i))].filter((x) => x && "—" !== x);
  const pill = st && st.querySelector(".pill");
  return {
    title: t,
    meta: bits.join(" · "),
    chip: pill ? { t: prTxt(pill), tone: prTone(st) } : st && prTxt(st) ? { t: prTxt(st) } : null,
    actEl: [...tr.querySelectorAll("button, .btn")].find((b) => prTxt(b).length > 1 && !(title || num).contains(b)) || null,
  };
};
// ---- the conversion runs where the phone card did, and once more when a page redraws a list on its own -----------------
if ("function" == typeof mCardTables) {
  mCardTables = function (root) {
    if (!PR_ON() || !root) return;
    root.querySelectorAll("table").forEach((t) => {
      if (!prCandidate(t)) return;
      // an outer list's spec reads only its own table; a page with several lists keeps the generic reading for the rest
      const spec = PR_SPECS[view] || null;
      prTable(t, spec);
    });
  };
}
function prPage() {
  const v = document.querySelector(".view.on");
  [...document.body.classList].filter((c) => /^pr-v-/.test(c)).forEach((c) => document.body.classList.remove(c));
  if (!v || !PR_ON()) return;
  document.body.classList.add("pr-v-" + view);
  try {
    mCardTables(v);
  } catch (e) {
    console.warn("phone rows", e);
  }
  try {
    (PR_PAGE[view] || (() => {}))(v);
  } catch (e) {
    console.warn("phone page", e);
  }
  v.querySelectorAll(".m-appr-list.pr-cards, #recv-body.pr-cards").forEach((x) => x.classList.add("pr-own"));
  // the Tasks page is the taskfix lane's and the foreman's Today has its own order; every other page folds its card lists
  if (!["tkall", "tasks", "ftoday"].includes(view))
    try {
      prFoldCards(v);
    } catch (e) {
      console.warn("phone card lists", e);
    }
  v.querySelector(".pr-tbl, .pr-cards") && v.classList.add("pr-page");
}
// what a page does beyond its rows: its one blue button and its filters
const PR_PAGE = {
  // Bills & Payroll: the paid-before-approval Review is the blue button; the filter segment rides with the chips
  ap: (v) => {
    const rev = v.querySelector("#fin-pbu [data-finbill]");
    if (rev) {
      rev.classList.add("primary");
      v.querySelectorAll(".ph .acts .btn.primary").forEach((b) => b.classList.remove("primary"));
    }
    const seg = v.querySelector("#ap-filter"),
      chips = v.querySelector("#ap-kpis");
    // the segment's buttons are drawn as chips beside the tiles; a press goes to the segment's own button (its handler
    // is delegated on #ap-filter, and the tiles are redrawn each render, so the chips are drawn again each time)
    if (seg && chips && !chips.querySelector(".pr-segchip")) {
      [...seg.querySelectorAll("button")].forEach((b) => {
        const c = document.createElement("button");
        (c.type = "button"), (c.className = "gl pr-segchip" + (b.classList.contains("on") ? " on" : "")), (c.innerHTML = `<span class="gl-k">${esc(prTxt(b))}</span>`);
        c.onclick = () => b.click();
        chips.appendChild(c);
      });
      seg.closest(".row") && seg.closest(".row").classList.add("pr-hide");
    }
  },
  // Decisions: blocking first (overdue rows lead), Decide on the top one is the safe next step
  dec: (v) => {
    const tb = v.querySelector("#dec-table table.pr-tbl tbody");
    if (tb && !tb.dataset.pr) {
      tb.dataset.pr = "1";
      const rows = [...tb.rows],
        w = (tr) => (tr.querySelector(".pr-row.late") ? 0 : 1);
      rows.sort((a, b) => w(a) - w(b)).forEach((tr) => tb.appendChild(tr));
    }
    const top = v.querySelector("#dec-table .pr-row.late [data-decided]");
    if (top) {
      top.classList.add("primary");
      v.querySelectorAll(".ph .acts .btn.primary").forEach((b) => b.classList.remove("primary"));
    }
  },
  // Clients: the stray Billing button goes (Billing is in the menu); New Client stays the one blue button
  clients: (v) => {
    const b = v.querySelector("#btn-gobilling");
    b && (b.style.display = "none");
  },
  // Approvals: each card is a row (title, amount and why, the yes verb); the top one keeps its blue
  mapprove: (v) =>
    v.querySelectorAll(".m-appr-list").forEach((list, li) =>
      prCards(list, ".m-appr", (c) => {
        const t = c.querySelector(".m-appr-t"),
          n = c.querySelector(".m-appr-n"),
          d = c.querySelector(".m-appr-d"),
          acts = [...c.querySelectorAll(".m-appr-a button, .m-appr-a .btn")],
          act = acts[0] || null,
          title = t ? prTxt(t).replace(prTxt(n), "").trim() : prTxt(c).slice(0, 80);
        return {
          title: title,
          // the card's facts are a list (who, when, how much): each its own part of the line
          meta: [prTxt(n)]
            .concat(c.querySelectorAll("li").length ? [...c.querySelectorAll("li")].map(prTxt) : [prTxt(d).replace(/^Because:\s*/i, "")])
            .filter(Boolean)
            .join(" · "),
          cls: c.classList.contains("bad") ? "pr-sev3" : c.classList.contains("warn") ? "pr-sev2" : "",
          actEl: act,
          primary: !!act && act.classList.contains("primary") && 0 === li && c === list.querySelector(".m-appr"),
        };
      }),
    ),
  // Deliveries: one row per order: who, the PO and when, how much is in; Receive opens the card's lines
  recv: (v) => {
    const body = v.querySelector("#recv-body");
    prCards(body, ".recv-po", (c) => {
      const head = c.querySelector(".row"),
        who = head && head.querySelector("b"),
        po = head && head.querySelector(".rc-polink"),
        when = head ? prTxt(head.querySelector(".small.muted")).replace(prTxt(po), "").replace(/^\s*·\s*/, "") : "",
        got = head ? prTxt([...head.querySelectorAll(".small")].pop()) : "",
        lines = c.querySelectorAll(".recv-line").length;
      return {
        title: `${prTxt(who)}${po ? " · " + prTxt(po) : ""}`,
        meta: [`${lines} line${1 === lines ? "" : "s"}`, when, got].filter(Boolean).join(" · "),
        actHtml: "",
      };
    });
    body &&
      body.querySelectorAll(".pr-card > .pr-row .pr-act-slot").forEach((s) => {
        if (s.firstChild) return;
        const b = document.createElement("button");
        (b.type = "button"), (b.className = "btn"), (b.textContent = "Receive");
        b.onclick = (e) => (e.stopPropagation(), s.closest(".pr-card").classList.add("pr-open"));
        s.appendChild(b);
      });
  },
};
// The foreman's Today (finding 10): one job, big targets, plain words. Clock In (Clock Out once in) is the blue button,
// then Today's Work, Arriving Today and the questions answered for him (For You); everything else on the page (the
// packing slip camera, the log and time notes, Now, Put on You, Who's Here, Tomorrow, the next two weeks) is one tap
// away under More for Today. The page title is the header's; the sentence under it goes. Text is 15 to 16px.
PR_PAGE.ftoday = (v) => {
  if ("foreman" !== role()) return;
  const body = v.querySelector("#ftoday-body");
  if (!body) return;
  v.classList.add("pr-ftoday");
  const hero = body.querySelector(":scope > .f-hero"),
    keep = [hero, body.querySelector(":scope > .f-work"), body.querySelector(":scope > .f3-arriving"), body.querySelector(":scope > .f-you")].filter(Boolean),
    clock = hero && hero.querySelector("[data-fclock]");
  clock && clock.classList.add("primary");
  // the one blue button is the clock: a blue elsewhere on the first two screens would be a second
  keep.slice(1).forEach((c) => c.querySelectorAll(".btn.primary").forEach((b) => b.classList.remove("primary")));
  let more = body.querySelector(":scope > details.pr-more");
  if (!more) {
    more = document.createElement("details");
    more.className = "pr-more card f-card";
    more.innerHTML = '<summary class="pr-more-s"><span>More for Today</span><i class="n"></i></summary><div class="pr-more-b"></div>';
  }
  const box = more.querySelector(".pr-more-b"),
    title = body.querySelector(":scope > .ph");
  // the header carries the page's name (the tdChrome rule: a heading the header repeats is marked td-in-hdr)
  title && (title.classList.add("pr-hide"), title.querySelectorAll("h1, h2").forEach((h) => h.classList.add("td-in-hdr")));
  keep.forEach((c) => body.appendChild(c));
  const rest = [...body.children].filter((c) => !keep.includes(c) && c !== more && c !== title);
  const cap = v.querySelector(":scope > #trk-capture");
  cap && rest.unshift(cap);
  rest.forEach((c) => box.appendChild(c));
  more.querySelector(".n").textContent = String(box.children.length || "");
  box.children.length ? body.appendChild(more) : more.remove();
};
(() => {
  const css = `
@media (max-width:760px){
  #v-ftoday.pr-ftoday{padding-bottom:132px;font-size:16px}
  #v-ftoday.pr-ftoday .small,#v-ftoday.pr-ftoday .muted{font-size:15px}
  #v-ftoday.pr-ftoday .f-hero{padding:0;margin-bottom:10px;flex-wrap:nowrap}
  #v-ftoday.pr-ftoday .f-hero>div:first-child{min-width:0}
  #v-ftoday.pr-ftoday .f-hero>div:first-child>*{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  #v-ftoday.pr-ftoday .f-hero [data-fclock]{flex:0 0 auto;min-width:116px;font-size:16px}
  #v-ftoday.pr-ftoday .f-card .hd h3{font-size:18px}
  #v-ftoday.pr-ftoday .f-card .hd{margin-bottom:4px}
  #v-ftoday.pr-ftoday .f-work .f-row{display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:8px;row-gap:2px;align-items:center;padding:7px 0}
  #v-ftoday.pr-ftoday .f-work .f-row>.grow{display:contents}
  #v-ftoday.pr-ftoday .f-work .f-row>.grow>b{grid-column:1/-1;font-size:16px;line-height:20px}
  #v-ftoday.pr-ftoday .f-work .f-row>.grow>span.small{grid-column:1/-1;font-size:15px;line-height:19px}
  #v-ftoday.pr-ftoday .f-work .f-row>.grow>.prg-chip{grid-column:1;justify-self:start;width:auto;min-width:112px;margin:0}
  #v-ftoday.pr-ftoday .f-work .f-row>.row{grid-column:2;gap:8px !important}
  #v-ftoday.pr-ftoday .f-you .f-row b,#v-ftoday.pr-ftoday .f3-row b{font-size:16px}
  #v-ftoday.pr-ftoday details.pr-more{padding:0}
  #v-ftoday.pr-ftoday .pr-more-s{display:flex;align-items:center;gap:8px;min-height:56px;padding:0 16px;font-size:17px;font-weight:600;cursor:pointer;list-style:none}
  #v-ftoday.pr-ftoday .pr-more-s::-webkit-details-marker{display:none}
  #v-ftoday.pr-ftoday .pr-more-s .n{font-style:normal;font-weight:500;color:var(--ink-3);font-size:15px}
  #v-ftoday.pr-ftoday .pr-more-b{padding:0 12px 12px}
  #v-ftoday.pr-ftoday .pr-more-b>.card{margin:10px 0 0}
  #v-ftoday.pr-ftoday .pr-hide{display:none !important}
}`;
  const s = document.createElement("style");
  (s.textContent = css), document.head.appendChild(s);
})();
// The foreman's Today is redrawn on its own by some presses (Clock In, Got It) without a render: the fold follows it
{
  let busy = !1;
  const mo = new MutationObserver(() => {
    if (busy || !PR_ON() || "ftoday" !== view) return;
    const v = document.getElementById("v-ftoday"),
      body = v && v.querySelector("#ftoday-body");
    if (!body) return;
    // a pass that adds a card after the fold (the log note, a late answer) is folded too; our own moves are not news
    busy = !0;
    try {
      PR_PAGE.ftoday(v);
    } catch (e) {
      console.warn("field today", e);
    }
    mo.takeRecords();
    busy = !1;
  });
  const arm = () => {
    const b = document.getElementById("ftoday-body");
    b && !b.dataset.prmo && ((b.dataset.prmo = "1"), mo.observe(b, { childList: !0 }));
  };
  arm(), document.addEventListener("DOMContentLoaded", arm);
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      arm();
    } catch (e) {}
    return r;
  };
}
// A list drawn after the render (a report that fills in later, a section redrawn on a press) is a table too: on the
// phone, a table added to the page is made rows where it lands. Only added tables are read, so typing costs nothing.
{
  const mo = new MutationObserver((recs) => {
    if (!PR_ON()) return;
    const v = document.querySelector(".view.on");
    if (!v) return;
    const hit = [];
    for (const r of recs)
      for (const n of r.addedNodes)
        1 === n.nodeType && v.contains(n) && ("TABLE" === n.tagName ? hit.push(n) : n.querySelector && n.querySelector("table") && hit.push(n));
    if (!hit.length) return;
    try {
      hit.forEach((n) => ("TABLE" === n.tagName ? prCandidate(n) && prTable(n, PR_SPECS[view] || null) : mCardTables(n)));
    } catch (e) {
      console.warn("phone rows, late table", e);
    }
    mo.takeRecords();
  });
  const main = () => document.querySelector(".main");
  main() ? mo.observe(main(), { childList: !0, subtree: !0 }) : document.addEventListener("DOMContentLoaded", () => main() && mo.observe(main(), { childList: !0, subtree: !0 }));
}
// Projects: the job picker belongs to a job's pages, not the list of every job (CSS on body.pr-v-ovjobs)
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      prPage();
    } catch (e) {
      console.warn("phone rows", e);
    }
    return r;
  };
}
// A Decide on the phone opens the Record It sheet Today uses (flowDecide), with the options and the order it releases.
// The sample gate (lsNeedsSample) runs before this listener and stops it when a sample is owed.
document.addEventListener(
  "click",
  (e) => {
    if (!PR_ON() || "function" != typeof flowDecide) return;
    const b = e.target.closest && e.target.closest("[data-decided]");
    if (!b || !S) return;
    const d = (S.decisions || []).find((x) => x.id === b.dataset.decided);
    if (!d) return;
    e.preventDefault(), e.stopImmediatePropagation(), flowDecide(S, d);
  },
  !0,
);
// ---- phone search (finding 12): the palette as a full-height sheet, results grouped, two lines each ------------------
// The same index (palIndex) and the same ranking (the palette's own palRender); under 760px the rows are redrawn by
// group, each keeping its data-pi so a tap opens what it opened before. No keyboard hints.
const PR_PAL_GROUPS = [
  ["Bills", ["bill"]],
  ["Orders", ["PO", "request"]],
  ["Deliveries", ["delivery"]],
  ["Tasks", ["task", "to-do", "field"]],
  ["Decisions", ["decision"]],
  ["Clients", ["client", "person"]],
  ["Projects", ["project"]],
  ["Documents", ["invoice", "estimate", "change order", "document"]],
  ["Vendors", ["vendor"]],
  ["Pages", ["view"]],
];
if ("function" == typeof palIndex) {
  const base = palIndex;
  palIndex = function () {
    const items = base.apply(this, arguments);
    // a delivery is an order on its way: found by vendor, PO number or job, it opens the job's Deliveries
    try {
      (ROLE_VIEWS[role()] || []).includes("recv") &&
        (DB.pos || [])
          .filter((po) => ["issued", "partial"].includes(po.status))
          .forEach((po) => {
            const p = DB.projects.find((x) => x.id === po.projectId);
            items.push({
              k: "delivery",
              t: `${po.vendor || "Delivery"} · ${po.number || ""}`,
              s: `${po.expected ? "expected " + fmt(po.expected) : "no date yet"}${p ? " · " + p.project.name : ""}`,
              go: () => {
                p && setCurrent(p.id), setView("recv");
              },
            });
          });
    } catch (e) {
      console.warn("search deliveries", e);
    }
    return items;
  };
}
if ("function" == typeof palRender) {
  const base = palRender;
  palRender = function () {
    const r = base.apply(this, arguments);
    try {
      const pal = document.getElementById("pal"),
        res = document.getElementById("pal-res");
      if (!pal || !res) return r;
      pal.classList.toggle("pr-pal", PR_ON());
      if (!PR_ON()) return r;
      const list = res._list || [];
      if (!list.length) return r;
      const groupOf = (k) => (PR_PAL_GROUPS.find((g) => g[1].includes(k)) || ["More"])[0],
        order = PR_PAL_GROUPS.map((g) => g[0]).concat(["More"]),
        by = {};
      list.forEach((it, n) => (by[groupOf(it.k)] = by[groupOf(it.k)] || []).push([it, n]));
      const note = res.querySelector(".a4-pal-note");
      res.innerHTML =
        (note ? note.outerHTML : "") +
        order
          .filter((g) => by[g])
          .map(
            (g) =>
              `<div class="pr-pal-g">${esc(g)}</div>` +
              by[g]
                .map(
                  ([it, n]) =>
                    `<div class="r pr-pal-r ${n === palIdx ? "on" : ""}" data-pi="${n}"><span class="pr-pal-t" data-nocase>${esc(it.t)}</span><span class="pr-pal-s" data-nocase>${esc([it.k === "view" ? "" : it.k, it.s].filter(Boolean).join(" · "))}</span></div>`,
                )
                .join(""),
          )
          .join("");
      res._list = list;
    } catch (e) {
      console.warn("phone search", e);
    }
    return r;
  };
}
(() => {
  const css = `
@media (max-width:760px){
  .pal.pr-pal{padding:0;align-items:stretch;background:var(--paper)}
  .pal.pr-pal .box{width:100%;max-width:none;height:100dvh;border-radius:0;box-shadow:none;display:flex;flex-direction:column;position:relative}
  .pal.pr-pal input{height:56px;font-size:17px;padding:0 60px 0 16px;flex:0 0 auto}
  .pal.pr-pal .res{max-height:none;flex:1 1 auto;overflow:auto;-webkit-overflow-scrolling:touch;padding-bottom:24px}
  .pal.pr-pal .hint{display:none}
  .pal.pr-pal .pr-pal-g{padding:14px 16px 6px;font-size:13px;font-weight:600;color:var(--ink-2);border-bottom:1px solid var(--rule-2)}
  .pal.pr-pal .r.pr-pal-r{display:flex;flex-direction:column;align-items:stretch;justify-content:center;gap:2px;min-height:60px;padding:8px 16px;border-bottom:1px solid var(--rule-2)}
  .pal.pr-pal .pr-pal-t{font-size:16px;line-height:20px;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .pal.pr-pal .pr-pal-s{font-size:13px;line-height:17px;color:var(--ink-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .pal.pr-pal .pr-pal-close{position:absolute;right:6px;top:6px;width:44px;height:44px;border:0;background:none;color:var(--ink-2);display:grid;place-items:center;cursor:pointer}
}
.pal:not(.pr-pal) .pr-pal-close{display:none}`;
  const s = document.createElement("style");
  (s.textContent = css), document.head.appendChild(s);
})();
// the sheet needs a way out without a keyboard's Esc: a 44px close button beside the input, on the phone only
if ("function" == typeof openPal) {
  const base = openPal;
  openPal = function () {
    const pal = document.getElementById("pal");
    pal && pal.classList.toggle("pr-pal", PR_ON());
    const r = base.apply(this, arguments);
    try {
      const box = pal && pal.querySelector(".box");
      if (box && PR_ON() && !box.querySelector(".pr-pal-close")) {
        const b = document.createElement("button");
        (b.type = "button"), (b.className = "pr-pal-close"), b.setAttribute("aria-label", "Close search"), (b.title = "Close");
        b.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';
        b.onclick = () => closePal();
        box.appendChild(b);
      }
      const q = document.getElementById("pal-q");
      q && PR_ON() && (q.setAttribute("enterkeyhint", "search"), (q.placeholder = "Search bills, orders, deliveries, tasks, clients"));
    } catch (e) {
      console.warn("phone search", e);
    }
    return r;
  };
}
