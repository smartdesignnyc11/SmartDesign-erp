// The module census's in-page reader (tests/projects_census.py), on top of the information map's (tests/ia_js.js,
// window.IA). Read-only: it opens views, presses tabs and reads the screen; it writes nothing to the data. A tap that
// would save anyway is counted (CENSUS.saves) and reported, so a census that changed the data says so.
// window.CENSUS.catalog()   IA.catalog() plus the job's own nouns (change orders, estimates, files, drawing sheets,
//                           selections, daily logs, punch and field items, photos), each with the words it shows by
// window.CENSUS.read(cat)   IA.scan() plus what the census needs: the sub-tab strip, the page's tab groups, columns
//                           and form fields, figures (a label with a number), empty states, blue buttons, sideways
//                           scroll and clipping, the links that leave the page
// window.CENSUS.tabGroups() the page's tab groups (a row of two or more buttons, one of them on)
// window.CENSUS.press(g, l) press the tab labelled l of the group whose labels are g
(() => {
  const vis = (el) => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== "hidden";
  const txt = (el) => (el ? (el.innerText || el.textContent || "") : "").replace(/\s+/g, " ").trim();
  const norm = (s) => IA.norm(s);
  const safe = (f, d) => { try { const v = f(); return v == null ? d : v; } catch (e) { return d; } };
  const V = () => document.querySelector(".view.on");
  // the save counter: every save()/saveNow() while the census runs
  const C = (window.CENSUS = window.CENSUS || {});
  C.saves = C.saves || 0;
  if (!C.wrapped) {
    C.wrapped = 1;
    ["save", "saveNow"].forEach((n) => {
      try {
        // the app's save is a global binding (reassigned by later sections): read and replace it through eval
        const f = (0, eval)(n);
        if (typeof f !== "function") return;
        window["__census_" + n] = function () { C.saves++; return f.apply(this, arguments); };
        (0, eval)(n + " = window.__census_" + n + ";");
      } catch (e) {}
    });
  }

  // ---- the job's own nouns, on top of the information map's catalog -------------------------------------------
  function catalog() {
    const out = safe(() => IA.catalog(), []);
    const add = (noun, k, title, x) => {
      const n = IA.needle(title, x && x.keepName);
      if (!n) return;
      out.push(Object.assign({ noun: noun, k: noun + ":" + k, t: String(title).slice(0, 90), n: [n] }, x || {}));
    };
    (DB.clients || []).forEach((c) => {
      (c.cos || c.changeOrders || []).forEach((o) => add("co", c.id + ":" + o.id, o.title || o.name || o.number || "", { pid: o.projectId || "" }));
      (c.estimates || []).forEach((e) => add("estimate", c.id + ":" + e.id, e.title || e.name || e.number || "", { pid: e.projectId || "" }));
    });
    (DB.cos || []).forEach((o) => add("co", o.id, o.title || o.name || o.number || "", { pid: o.projectId || "" }));
    (DB.estimates || []).forEach((e) => add("estimate", e.id, e.title || e.name || e.number || "", { pid: e.projectId || "" }));
    DB.projects.forEach((p) => {
      (p.files || []).forEach((f) => add("file", p.id + ":" + (f.id || f.name), f.name || f.title || "", { pid: p.id }));
      (p.issues || []).filter((i) => i.status !== "open").forEach((i) => add("fielditem", p.id + ":" + i.id, i.title, { pid: p.id }));
      (p.punch || []).forEach((i) => add("punch", p.id + ":" + (i.id || i.title), i.title || i.text || i.what || "", { pid: p.id }));
      (p.logs || p.dailyLogs || []).forEach((l) => add("log", p.id + ":" + (l.id || l.date), l.summary || l.title || l.note || "", { pid: p.id }));
      (p.materials || []).forEach((m) => out.some((o) => o.noun === "material" && o.t === m.name) || add("material", p.id + ":m:" + m.id, m.name, { pid: p.id }));
      (p.decisions || []).filter((d) => d.status !== "open").forEach((d) => add("decision", p.id + ":" + d.id + ":closed", d.name, { pid: p.id, closed: 1 }));
      (p.inspections || []).filter((i) => i.status === "passed").forEach((i) => add("inspection", p.id + ":" + i.id + ":passed", i.name, { pid: p.id, closed: 1 }));
      (p.submittals || []).filter((s) => ["closed", "approved", "void"].includes(s.status)).forEach((s) => add("submittal", p.id + ":" + s.id + ":closed", s.title, { pid: p.id, closed: 1 }));
    });
    safe(() => DB.studio.sheets, []).forEach((s) => add("sheet", s.id, (s.number ? s.number + " " : "") + (s.title || ""), { pid: s.projectId || "", keepName: 1 }));
    safe(() => DB.sel.items, []).forEach((it) => out.some((o) => o.noun === "material" && o.t === it.name) || add("selection", it.projectId + ":" + norm(it.name).slice(0, 40), it.name, { pid: it.projectId }));
    return out;
  }

  // ---- the page's tab groups: two or more buttons side by side, one of them on ------------------------------------
  const ON = (b) => b.classList.contains("on") || b.classList.contains("active") || b.getAttribute("aria-selected") === "true" || b.getAttribute("aria-pressed") === "true";
  // a tab never does anything but show: words that commit are never pressed
  const ACTION = /^(new|add|delete|remove|send|approve|pay|post|void|archive|mark|done|close|record|save|submit|create|upload|take|import|export|print|download|reject|decline|accept|sign|clear|reset|run|write|draft|email|call|book|order|start|stop|clock)\b/i;
  const labOf = (b) => (b.getAttribute("aria-label") || b.title || txt(b)).replace(/\s+/g, " ").replace(/\s*\d+\+?$/, "").trim().slice(0, 40);
  const cntOf = (b) => { const n = b.querySelector(".n, .cnt, .badge, .count"); const m = n ? txt(n).match(/\d+/) : txt(b).match(/\s(\d+)\+?$/); return m ? +(m[1] || m[0]) : null; };
  function tabGroups() {
    const v = V();
    if (!v) return [];
    const seen = new Set(), out = [];
    [...v.querySelectorAll("button, [role=tab], a.tab")].filter(vis).filter(ON).forEach((b) => {
      const box = b.parentElement;
      if (!box || seen.has(box)) return;
      seen.add(box);
      const bs = [...box.children].filter((x) => x.matches("button, [role=tab], a.tab") && vis(x));
      // tabs have exactly one on: a row with several on is a set of toggles (a job's working days), never pressed
      if (bs.length < 2 || bs.filter(ON).length !== 1) return;
      // a group of tabs inside a sheet that is not the page is not the page's
      if (box.closest("#mbm, .modal, .drawer")) return;
      const labels = bs.map(labOf);
      if (labels.filter((l) => ACTION.test(l)).length > labels.length / 2) return;
      const r = box.getBoundingClientRect();
      out.push({ labels: labels, counts: bs.map(cntOf), on: bs.findIndex(ON), y: Math.round(r.top + scrollY), id: box.id || "", cls: String(box.className || "").slice(0, 40) });
    });
    return out;
  }
  function press(labels, label) {
    const g = tabGroups().map((x, i) => ({ x: x, i: i, ov: x.labels.filter((l) => labels.includes(l)).length })).sort((a, b) => b.ov - a.ov)[0];
    if (!g || !g.ov) return false;
    const v = V(), boxes = [];
    const seen = new Set();
    [...v.querySelectorAll("button, [role=tab], a.tab")].filter(vis).filter(ON).forEach((b) => { const box = b.parentElement; if (box && !seen.has(box)) { seen.add(box); const bs = [...box.children].filter((x) => x.matches("button, [role=tab], a.tab") && vis(x)); bs.length >= 2 && bs.filter(ON).length === 1 && !box.closest("#mbm, .modal, .drawer") && boxes.push(bs); } });
    const bs = boxes.find((bs) => bs.map(labOf).join("|") === g.x.labels.join("|"));
    const b = bs && bs.find((x) => labOf(x) === label);
    if (!b || ACTION.test(label)) return false;
    b.click();
    return true;
  }

  // ---- figures: a short label with a number (tiles, KPI cards, summary lines, two-column tables, dl) -------------
  const NUM = /(-|−)?\$?\s?\d[\d,]*(\.\d+)?\s?(%|k|m)?/i;
  const FIG = ".kpi, .tile, .ov-tile, .kpi-card, .stat, .td-pulse > *, .pulse > *, .fin-tile, .sum-tile, .metric, .ovt, .fig, .jt-tile, .kpis > *, .tiles > *, .stats > *, .summary > *";
  function figures(v) {
    const out = [];
    const push = (label, value, el, src) => {
      label = String(label || "").replace(/\s+/g, " ").trim();
      value = String(value || "").replace(/\s+/g, " ").trim();
      if (!label || !value || label.length > 60 || !/[a-z]/i.test(label)) return;
      const r = el.getBoundingClientRect();
      out.push({ l: label.slice(0, 60), v: value.slice(0, 40), src: src, y: Math.round(r.top + scrollY) });
    };
    const done = [];
    // a tile: a label part and a value part (the job page's glance tiles, KPI cards, pulse numbers)
    [...v.querySelectorAll(FIG + ", .gl")].filter(vis).forEach((el) => {
      if (done.some((x) => x.contains(el))) return;
      const vEl = el.querySelector(".gl-v, .kpi-v, .v, .big, .num, b, strong");
      const kEl = el.querySelector(".gl-k, .kpi-k, .k, .lbl, .label");
      if (vEl && kEl && vEl !== kEl) { done.push(el); push(txt(kEl), txt(vEl), el, "tile"); return; }
      const t = txt(el);
      if (!t || t.length > 120) return;
      if (vEl && txt(vEl).length < 40 && NUM.test(txt(vEl))) { done.push(el); push(t.replace(txt(vEl), " ").replace(/[·:|]/g, " ").slice(0, 60), txt(vEl), el, "tile"); return; }
      const m = t.match(NUM);
      if (!m) return;
      done.push(el);
      push(t.replace(m[0], " ").replace(/[·:|]/g, " ").slice(0, 60), m[0], el, "tile");
    });
    // a bold money figure leading a sentence card ("Ready to bill on this job: $12,651")
    [...v.querySelectorAll(".note b, .note strong, .banner b, .hint b")].filter(vis).forEach((b) => {
      const m = txt(b).match(/^(.{4,50}?):?\s*((-|−)?\$[\d,]+(\.\d+)?)$/);
      m && push(m[1], m[2], b, "note");
    });
    [...v.querySelectorAll("dl")].filter(vis).forEach((dl) => [...dl.querySelectorAll("dt")].forEach((dt) => { const dd = dt.nextElementSibling; const m = dd && txt(dd).match(NUM); m && push(txt(dt), m[0], dt, "dl"); }));
    [...v.querySelectorAll("table")].filter(vis).forEach((t) => {
      const rows = [...t.querySelectorAll("tr")].filter(vis);
      if (rows.length > 25) return;
      rows.forEach((tr) => { const c = [...tr.children]; if (c.length !== 2) return; const m = txt(c[1]).match(NUM); m && /\$|%/.test(m[0]) && push(txt(c[0]), m[0], tr, "table"); });
    });
    return out.slice(0, 80);
  }
  // ---- the page's outline: every visible heading, its level, y, the count beside it, and the height it heads ----
  function outline(v) {
    const H = [...v.querySelectorAll("h1, h2, h3, h4, summary, .hd b, .td-hd b")].filter(vis).filter((h) => !h.closest("#mbm, .modal, .drawer") && txt(h).length > 1 && txt(h).length < 80);
    const out = H.map((h) => {
      const r = h.getBoundingClientRect(), row = h.parentElement;
      const c = row ? [...row.querySelectorAll(".n, .cnt, .badge, .count, .td-cnt, .small.muted, .muted.small")].find((x) => x !== h && !h.contains(x) && /^\d+\b/.test(txt(x)) && !/^\d+\s+[A-Z]/.test(txt(x))) : null;
      const lvl = /^H(\d)$/.test(h.tagName) ? +h.tagName[1] : 4;
      return { lvl: lvl, h: txt(h).slice(0, 70), y: Math.round(r.top + scrollY), n: c ? +txt(c).match(/^\d+/)[0] : null };
    });
    const end = v.scrollHeight || v.getBoundingClientRect().height;
    out.forEach((o, i) => { const nx = out.slice(i + 1).find((x) => x.lvl <= o.lvl); o.hgt = Math.max(0, Math.round((nx ? nx.y : end) - o.y)); });
    return out.slice(0, 60);
  }
  // ---- columns and fields ---------------------------------------------------------------------------------------
  function columns(v) {
    return [...v.querySelectorAll("table")].filter(vis).filter((t) => !t.closest("#mbm")).slice(0, 12).map((t) => {
      const hr = t.querySelector("thead tr") || [...t.querySelectorAll("tr")].find((r) => r.querySelector("th"));
      const hs = hr ? [...hr.children].map(txt).map((x) => x.slice(0, 30)) : [];
      const sec = t.closest(".card, section.td-sec, .td-sec, details, .panel");
      const h = sec ? txt(sec.querySelector("h2, h3, h4, summary, .hd b")).slice(0, 50) : "";
      return { sec: h, cols: hs, rows: [...t.querySelectorAll("tbody tr")].filter(vis).length, y: Math.round(t.getBoundingClientRect().top + scrollY) };
    });
  }
  function fields(v) {
    const seen = new Set();
    return [...v.querySelectorAll("input, select, textarea")].filter(vis).filter((e) => e.type !== "hidden" && e.type !== "checkbox" && e.type !== "file").map((e) => {
      const l = e.labels && e.labels[0] ? txt(e.labels[0]) : "";
      return (e.getAttribute("aria-label") || l || e.placeholder || e.name || e.id || e.tagName.toLowerCase()).replace(/\s+/g, " ").slice(0, 40);
    }).filter((x) => x && !seen.has(x) && seen.add(x)).slice(0, 30);
  }
  // ---- empty states ---------------------------------------------------------------------------------------------
  function empties(v) {
    const E = /^(nothing|no [a-z]|none\b|not yet|all clear|you're clear|empty|all caught up|no one)/i;
    const out = [];
    [...v.querySelectorAll(".empty, .muted, p, .small, td, div")].filter(vis).forEach((e) => {
      if (e.children.length > 2) return;
      const t = txt(e);
      if (t.length < 4 || t.length > 140 || !E.test(t)) return;
      if (out.some((o) => o.t === t)) return;
      out.push({ t: t.slice(0, 100), y: Math.round(e.getBoundingClientRect().top + scrollY) });
    });
    return out.slice(0, 12);
  }
  // ---- the phone: sideways scroll and what runs past the edge ---------------------------------------------------
  function clip(v) {
    const W = innerWidth, out = [];
    const scroller = (e) => { for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) { const s = getComputedStyle(p); if (/auto|scroll|hidden|clip/.test(s.overflowX)) return p; } return null; };
    [...v.querySelectorAll("*")].forEach((e) => {
      if (!vis(e) || e.children.length > 3) return;
      const r = e.getBoundingClientRect();
      if (r.width < 2 || r.right <= W + 1) return;
      const s = scroller(e);
      const t = txt(e).slice(0, 40) || e.tagName.toLowerCase() + (e.className ? "." + String(e.className).split(" ")[0] : "");
      out.push({ t: t, right: Math.round(r.right), inScroller: !!s, clipped: !!s && /hidden|clip/.test(getComputedStyle(s).overflowX), scroller: s ? (s.id || String(s.className).split(" ")[0] || s.tagName.toLowerCase()) : "" });
    });
    // the page itself, and the parts that clip (one entry per scroller)
    const by = {};
    out.forEach((o) => { const k = !o.inScroller ? "past the edge" : (o.clipped ? "cut off by " : "scrolls in ") + o.scroller; (by[k] = by[k] || []).push(o.t); });
    return { sw: document.documentElement.scrollWidth, bodySw: document.body.scrollWidth, w: W, sideways: document.documentElement.scrollWidth > W + 1, parts: Object.entries(by).map(([k, ts]) => ({ where: k, n: ts.length, ex: [...new Set(ts)].slice(0, 4) })).slice(0, 10) };
  }
  // ---- the links that leave the page: what a tap opens (read, not pressed) --------------------------------------
  let VIEWS = null;
  function links(v) {
    // a tap that opens another page: any data attribute (or onclick) whose value names a view
    VIEWS = VIEWS || new Set([...document.querySelectorAll("section.view")].map((x) => x.id.replace(/^v-/, "")));
    const out = [];
    [...v.querySelectorAll("*")].filter((e) => (Object.keys(e.dataset).length > 0 || e.hasAttribute("onclick")) && vis(e)).forEach((e) => {
      let to = "", how = "";
      for (const k in e.dataset) { const val = String(e.dataset[k]); if (VIEWS.has(val)) { to = val; how = "data-" + k; break; } }
      if (!to) { const m = (e.getAttribute("onclick") || "").match(/(?:setView\(|view\s*=\s*)['"](\w+)/); if (m && VIEWS.has(m[1])) { to = m[1]; how = "onclick"; } }
      if (!to) return;
      out.push({ to: to, t: txt(e).slice(0, 40), how: how, y: Math.round(e.getBoundingClientRect().top + scrollY) });
    });
    const seen = new Set();
    return out.filter((o) => { const k = o.to + "|" + o.t; if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 60);
  }
  // ---- the sub-tab strip (a job's pages) and the bar ------------------------------------------------------------
  function strip() {
    const sn = document.getElementById("subnav");
    if (!sn || sn.hidden) return { shown: false, items: [] };
    // inView: on the screen without a swipe (the phone's strip scrolls sideways)
    const inView = (b) => { if (!vis(b) || getComputedStyle(b).display === "none") return false; const r = b.getBoundingClientRect(); return r.left >= -1 && r.right <= innerWidth + 1 && r.width > 0; };
    const items = [...sn.querySelectorAll("[data-mni], [data-sub]")].map((b) => ({ v: b.dataset.sub, tab: b.dataset.subtab || "", i: b.dataset.mni == null ? null : +b.dataset.mni, l: labOf(b), n: cntOf(b), on: b.classList.contains("on"), vis: vis(b) && getComputedStyle(b).display !== "none", inView: inView(b) }));
    const r = sn.getBoundingClientRect();
    return { shown: vis(sn) && r.height > 0, y: Math.round(r.top), h: Math.round(r.height), proj: !!sn.querySelector(".sub-proj select"), sw: sn.scrollWidth, cw: sn.clientWidth, items: items };
  }
  function bar() {
    return [...document.querySelectorAll("#mtabs button, #tabbar button")].filter(vis).map((b) => ({ v: b.dataset.mv || b.dataset.v || "", l: labOf(b), n: cntOf(b), on: b.classList.contains("on") }));
  }
  function read(cat) {
    const s = IA.scan(cat);
    if (!s) return null;
    const v = V();
    const F = IA.fold();
    const blue = [...v.querySelectorAll(".btn.primary, button.primary")].filter(vis).filter((b) => !b.closest("#mbm")).map((b) => { const r = b.getBoundingClientRect(); return { l: labOf(b), y: Math.round(r.top + scrollY), above: r.top < F - 16 }; });
    // rows per section: the ROW selector of the information map, counted inside each section
    return Object.assign(s, {
      vid: v.id, pid: safe(() => S.id, ""), pname: safe(() => S.project.name, ""), dashAll: safe(() => view === "dash" && !!dashAll, false),
      strip: strip(), bar: bar(), groups: tabGroups(), outline: outline(v), cols: columns(v), fields: fields(v), figs: figures(v), empties: empties(v),
      blue: blue, clip: clip(v), links: links(v), modal: !!document.querySelector("#mbm") && vis(document.querySelector("#mbm")),
      lead: txt(v.querySelector(".ph .lead, p.lead")).slice(0, 160),
    });
  }
  Object.assign(C, { catalog: catalog, read: read, tabGroups: tabGroups, press: press, strip: strip, bar: bar });
})();
