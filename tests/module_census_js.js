// The module census's in-page helpers (tests/module_census.py), on top of the projects census's reader
// (tests/census_js.js) and the information map's (tests/ia_js.js). Read-only: it presses menu entries, the phone bar
// and links, and reads the screen; it writes nothing to the data.
// window.CMOD.extra()        nouns the firm-wide modules list, added to the census catalog (clients, vendors, leads,
//                            contacts, companies, every invoice, bill and PO, payroll runs, stock, meetings, journals,
//                            obligations, lessons, partners, bank lines)
// window.CMOD.entries()      the signed-in role's menu as entries a person taps: the rail group, its index in the
//                            group's strip, the phone bar, More and Settings; field roles' and the client's own menus
// window.CMOD.go(e)          reach an entry the way a person does: the phone bar, or the menu (the hamburger on the
//                            phone), the group, then the strip. Returns the taps and where it landed
// window.CMOD.firstBtn()     the first button on the page as it opens (label, blue or not, y)
// window.CMOD.follow(to, t)  tap the link on the page whose target is `to` and whose words are `t`
(() => {
  const vis = (el) => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== "hidden" && getComputedStyle(el).display !== "none";
  const txt = (el) => (el ? (el.innerText || el.textContent || "") : "").replace(/\s+/g, " ").trim();
  const safe = (f, d) => { try { const v = f(); return v == null ? d : v; } catch (e) { return d; } };
  const V = () => document.querySelector(".view.on");
  const C = (window.CMOD = window.CMOD || {});

  // ---- more nouns ---------------------------------------------------------------------------------------------
  function extra() {
    const out = [];
    const add = (noun, k, title, x) => {
      const n = IA.needle(title, x && x.keepName);
      if (!n) return;
      out.push(Object.assign({ noun: noun, k: noun + ":" + k, t: String(title).slice(0, 90), n: [n] }, x || {}));
    };
    const have = new Set((window.__cecat || []).map((o) => o.k));
    (DB.clients || []).forEach((c) => {
      add("client", c.id, c.name || "", { keepName: 1 });
      // every invoice: the information map lists the unpaid ones under the same key
      (c.invoices || []).forEach((i) => i.number && !have.has("invoice:" + c.id + ":" + i.id) && add("invoice", c.id + ":" + i.id, i.number, { closed: 1 }));
    });
    (DB.vendors || []).forEach((v) => add("vendor", v.id, v.name || "", { keepName: 1 }));
    (DB.bills || []).forEach((b) => b.number && !have.has("bill:" + b.id) && add("bill", b.id, b.number, { closed: 1 }));
    (DB.pos || []).forEach((p) => p.number && !have.has("po:" + p.id) && add("po", p.id, p.number, { closed: 1 }));
    (DB.leads || []).forEach((l) => add("lead", l.id, l.name || l.addr || "", { keepName: 1 }));
    safe(() => DB.hub.contacts, []).forEach((c) => add("contact", c.id, c.name || [c.first, c.last].filter(Boolean).join(" "), { keepName: 1 }));
    safe(() => DB.hub.companies, []).forEach((c) => add("company", c.id, c.name || "", { keepName: 1 }));
    (DB.payroll || []).forEach((r) => add("payroll", r.id, "Payroll · " + (r.period || ""), {}));
    (DB.inventory || []).forEach((s) => add("stock", s.id, s.name || "", {}));
    (DB.meetings || []).forEach((m) => add("meeting", m.id, m.title || "", {}));
    (DB.obligations || []).forEach((o) => add("obligation", o.id, o.name || "", {}));
    (DB.lessons || []).forEach((l) => add("lesson", l.id, l.title || "", {}));
    (DB.partners || []).forEach((p) => add("partner", p.id, p.name || "", { keepName: 1 }));
    // a bank or card line, and a journal entry only where its words are not a bank line's (a line's posting carries
    // the line's description, so it would count the same row twice)
    (DB.txns || []).forEach((t) => t.desc && add("bankline", t.id, t.desc, {}));
    const lines = new Set(out.filter((o) => o.noun === "bankline").map((o) => o.n[0]));
    safe(() => DB.gl.journals, []).forEach((j) => j.memo && !lines.has(IA.needle(j.memo)) && add("journal", j.id, j.memo, {}));
    (DB.threads || []).forEach((t) => t.title && add("thread", t.id, t.title, {}));
    return out;
  }

  // ---- the menu as entries ------------------------------------------------------------------------------------
  // e: { grp, gname, mni, v, tab, l, sec, place, bar }
  function entries() {
    const r = role(), out = [];
    const phoneBar = new Set();
    if (r === "client") {
      (FD_CLIENT_NAV || []).filter(([v]) => (ROLE_VIEWS.client || []).includes(v)).forEach(([v, l]) => out.push({ grp: "cl-" + v, gname: l, mni: null, v: v, tab: "", l: l, sec: "", place: "client", bar: true }));
      return out;
    }
    const m = typeof mnMap === "function" && mnOn() ? mnMap() : null;
    if (!m) return out;
    const split = (x) => { const [a, l] = x.split("="); const [v, tab] = a.split(":"); return { v: v, tab: tab || "", l: l }; };
    if (m.field) {
      const bar = new Set(m.bar.map((x) => split(x).v));
      [].concat(m.bar, m.rest, m.more || [], m.bottom || []).forEach((x, i) => {
        const it = split(x);
        const place = m.bar.includes(x) ? "bar" : m.rest.includes(x) ? "menu" : (m.more || []).includes(x) ? "more" : "settings";
        out.push({ grp: "f-" + it.v, gname: it.l, mni: null, v: it.v, tab: "", l: it.l, sec: "", place: place, bar: bar.has(it.v) });
      });
      return out;
    }
    (m.phone || []).forEach((x) => phoneBar.add(split(x).v));
    m.groups.forEach((g) => g.items.forEach((x, i) => { const it = split(x); out.push({ grp: g.id, gname: g.n, mni: i, v: it.v, tab: it.tab, l: it.l, sec: "", place: "rail", bar: phoneBar.has(it.v) && !it.tab, single: g.items.length === 1 }); }));
    (m.more || []).forEach((x, i) => { const it = split(x); out.push({ grp: "more", gname: "More", mni: i, v: it.v, tab: it.tab, l: it.l, sec: "", place: "more", bar: phoneBar.has(it.v), single: m.more.length === 1 }); });
    (m.bottom || []).forEach((x, i) => { const it = split(x); out.push({ grp: "setup", gname: "Settings", mni: i, v: it.v, tab: it.tab, l: it.l, sec: "", place: "settings", bar: phoneBar.has(it.v), single: m.bottom.length === 1 }); });
    return out;
  }

  // ---- reach an entry -----------------------------------------------------------------------------------------
  const phone = () => innerWidth < 760;
  function barBtn(v) {
    return [...document.querySelectorAll('#mtabs button[data-mv="' + v + '"], #tabbar button[data-tab="' + v + '"]')].find(vis) || null;
  }
  function railBtn(grp) {
    return [...document.querySelectorAll('#nav-groups button[data-grp="' + grp + '"]')].find(vis) || null;
  }
  function openMenu() {
    const b = document.getElementById("menu-btn");
    if (b && vis(b)) { b.click(); return true; }
    return false;
  }
  function go(e) {
    const taps = [];
    const label = (b) => txt(b).replace(/\s*\d+$/, "").trim();
    // the phone bar first: one tap
    if (phone() && e.bar && !e.tab) {
      const b = barBtn(e.v);
      if (b) { taps.push("bar: " + label(b)); b.click(); return { taps: taps, how: "bar" }; }
    }
    let rb = railBtn(e.grp);
    if (!rb && phone()) { if (openMenu()) { taps.push("menu"); rb = railBtn(e.grp); } }
    if (!rb) {
      // no button: open it as a link would
      try { setView(e.v); } catch (x) { view = e.v; render(); }
      return { taps: taps.concat(["no button: set view"]), how: "none" };
    }
    taps.push(label(rb));
    rb.click();
    if (e.mni == null || e.single) return { taps: taps, how: phone() && taps[0] === "menu" ? "menu" : "rail" };
    // the strip: a group's pages (the first is where the group's button lands; it is pressed only if it carries a tab)
    if (e.mni === 0 && !e.tab) return { taps: taps, how: "rail" };
    const sb = document.querySelector('#subnav [data-mni="' + e.mni + '"]');
    if (!sb) return { taps: taps.concat(["no strip entry"]), how: "rail" };
    const r = sb.getBoundingClientRect();
    const swipe = r.left < -1 || r.right > innerWidth + 1;
    taps.push((swipe ? "swipe the strip, " : "") + label(sb));
    sb.click();
    return { taps: taps, how: "strip", swipe: swipe };
  }

  // ---- the first button -----------------------------------------------------------------------------------------
  function firstBtn() {
    const v = V();
    if (!v) return null;
    const bs = [...v.querySelectorAll("button, a.btn, [role=button]")].filter(vis).filter((b) => !b.closest("#mbm, .modal, .drawer") && txt(b).length + (b.getAttribute("aria-label") || "").length > 0);
    if (!bs.length) return null;
    bs.sort((a, b) => { const x = a.getBoundingClientRect(), y = b.getBoundingClientRect(); return Math.abs(x.top - y.top) > 6 ? x.top - y.top : x.left - y.left; });
    const b = bs[0], r = b.getBoundingClientRect();
    return { l: (b.getAttribute("aria-label") || txt(b)).slice(0, 40), blue: b.classList.contains("primary"), y: Math.round(r.top + scrollY), n: bs.length };
  }

  // ---- follow a link the page shows ---------------------------------------------------------------------------
  const ACTION = /^(new|add|delete|remove|send|approve|pay|post|void|archive|mark|done|close|record|save|submit|create|upload|take|import|export|print|download|reject|decline|accept|sign|clear|reset|run|write|draft|email|call|book|order|start|stop|clock)\b/i;
  function follow(to, t) {
    const v = V();
    if (!v) return false;
    const el = [...v.querySelectorAll("*")].filter(vis).find((e) => {
      if (txt(e).slice(0, 40) !== t) return false;
      for (const k in e.dataset) if (String(e.dataset[k]) === to) return true;
      const m = (e.getAttribute("onclick") || "").match(/(?:setView\(|view\s*=\s*)['"](\w+)/);
      return !!m && m[1] === to;
    });
    if (!el || ACTION.test(t)) return false;
    el.click();
    return true;
  }
  Object.assign(C, { extra: extra, entries: entries, go: go, firstBtn: firstBtn, follow: follow });
})();
