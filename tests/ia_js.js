// The information map's in-page reader (tests/ia_map.py). Read-only: it signs in, opens views and reads the screen;
// it writes nothing to the data except the app's day during the precursor scan (restored after).
// window.IA.catalog()  every record a person might be shown, by noun, with the text that identifies it on screen
// window.IA.scan(cat)  the open screen: heading, tabs, sections (cards), what each section lists, counts, clutter
// window.IA.find(cat)  where each record of the catalog sits on the open screen (y, row rank, above the fold)
(() => {
  const norm = (s) => String(s == null ? "" : s).toLowerCase().replace(/[‘’“”"']/g, "").replace(/[–—‒−]/g, "-").replace(/…/g, "").replace(/\s+/g, " ").trim();
  // a record's needle: its title less a trailing " - <project>", at most 34 characters, at least 8. A needle that
  // is only a project, client, vendor or person's name is no needle (it would match every page about that job).
  let STOP = null;
  const stop = () => STOP || (STOP = [].concat(
    DB.projects.map((p) => norm((p.project && p.project.name) || "")), (DB.clients || []).map((c) => norm(c.name)),
    (DB.vendors || []).map((v) => norm(v.name)), (DB.users || []).map((u) => norm(u.name))).filter((x) => x && x.length > 3));
  const needle = (s, keepName) => {
    let n = norm(s);
    const cut = n.lastIndexOf(" - ");
    if (cut >= 10) { const tail = n.slice(cut + 3); if (stop().some((x) => tail.startsWith(x.slice(0, 10)) || x.startsWith(tail.slice(0, 10)))) n = n.slice(0, cut); }
    n = n.replace(/^(re|fwd?): /, "");
    n = n.slice(0, 34).trim();
    if (!keepName && stop().some((x) => x === n || (x.startsWith(n) && n.length < 16) || (n.startsWith(x) && n.length - x.length < 4))) return "";
    return n.length >= (keepName ? 4 : 8) ? n : "";
  };
  const vis = (el) => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== "hidden";
  const T = () => today();
  const wdAdd = (d, n) => addWork(d, n, !1);
  const projName = (p) => (p.project && p.project.name) || p.name || p.id;
  const safe = (f, d) => { try { const v = f(); return v == null ? d : v; } catch (e) { return d; } };
  const ROLE_OF = { u_owner: "owner", u_alan: "pm", u_chen: "coord", u_angel: "foreman", u_alberto: "crew", u_alex: "driver", u_sarah: "designer", u_billing: "billing", u_controller: "controller", u_klein: "client" };

  function catalog() {
    const out = [], td = T(), r = role();
    // x.alt: the other words the same record goes by (the client's wording of a decision or submittal)
    const add = (noun, k, title, x) => { const n = needle(title, x && x.ctx); if (!n) return; const alt = ((x && x.alt) || []).map((a) => needle(a, x.ctx)).filter((a) => a && a !== n); out.push(Object.assign({ noun: noun, k: noun + ":" + k, t: String(title).slice(0, 90) }, x || {}, { n: [n].concat(alt) })); };
    const byKey = () => { const m = {}; out.forEach((o) => (m[o.k] = o)); return m; };
    // tasks: the one accessor (schedule tasks are their own noun below)
    safe(() => tkAll({ open: !0 }), []).forEach((t) => {
      if (t.kind === "sched") return;
      add("task", t.key, t.title, { due: t.due || "", who: t.ownerUid || "", pid: t.projectId || "" });
    });
    // schedule tasks (open), with what puts them at risk
    DB.projects.forEach((p) => (p.tasks || []).forEach((t) => {
      if (t.status === "done" || t.type === "milestone") return;
      const st = safe(() => prgState(t), null), deps = (t.deps || []).map((id) => (p.tasks || []).find((x) => x.id === id)).filter(Boolean);
      const depLate = deps.filter((d) => d.status !== "done" && ((d.end < td) || safe(() => prgState(d), {}) && safe(() => prgState(d).behind, !1)));
      const late = t.end < td || (t.start < td && t.status === "planned");
      add("sched", p.id + ":" + t.id, t.name, { pid: p.id, start: t.start, end: t.end, risk: late ? "late" : st && st.behind ? "behind" : depLate.length ? "pred-late" : "", deps: depLate.map((d) => d.name) });
    }));
    // decisions, materials to buy, field requests, submittals, inspections, site questions
    DB.projects.forEach((p) => {
      (p.decisions || []).filter((d) => d.status === "open").forEach((d) => add("decision", p.id + ":" + d.id, d.name, { pid: p.id, due: safe(() => withProject(p, () => decDue(d)), ""), owner: d.owner, alt: [safe(() => withProject(p, () => clTitle(d)), "")] }));
      ((DB.field && DB.field.subs) || []).filter((s) => s.projectId === p.id && s.status === "unconfirmed" && s.date >= T()).forEach((s) => add("subconfirm", s.id, s.vendor, { pid: p.id, due: s.date, ctx: "confirm" }));
      (p.requests || []).filter((q) => !["delivered", "closed", "done", "cancelled"].includes(q.status)).forEach((q) => add("request", p.id + ":" + q.id, q.what, { pid: p.id, due: q.neededBy || "", status: q.status }));
      (p.submittals || []).filter((s) => !["closed", "approved", "void"].includes(s.status)).forEach((s) => add("submittal", p.id + ":" + s.id, s.title, { pid: p.id, status: s.status, alt: [s.clientTitle || ""] }));
      (p.inspections || []).filter((i) => i.status !== "passed").forEach((i) => add("inspection", p.id + ":" + i.id, i.name, { pid: p.id, status: i.status, date: i.date || "" }));
      (p.issues || []).filter((i) => i.status === "open").forEach((i) => add("siteq", p.id + ":" + i.id, i.title, { pid: p.id, due: i.due || "" }));
    });
    safe(() => PRED.toBuy.rows(), []).forEach((x) => add("material", x.p.id + ":" + (x.key || (x.m && x.m.id) || x.name), x.name, { pid: x.p.id, due: x.orderBy || "", needBy: x.needBy || "" }));
    // the selections still to buy (the Buy Board's own rows: fixtures, hardware, lighting), stage Selected or Approved
    safe(() => DB.sel.items, []).filter((it) => ["sel", "appr", undefined, ""].includes(it.stage)).forEach((it) => add("material", "sel:" + it.projectId + ":" + norm(it.name).slice(0, 40), it.name, { pid: it.projectId, due: safe(() => selOrderBy(it), "") }));
    safe(() => PRED.siteQuestions.rows(), []).forEach((x) => add("siteq", "raise:" + x.x.id, x.x.title, { pid: x.p.id, due: x.x.dueBy || x.x.needBy || "", to: x.x.to || "" }));
    // insurance (COI) lapsing within 30 days or lapsed: the vendor's name next to the word insurance or certificate
    (DB.vendors || []).forEach((v) => {
      const e = v.insuranceExp || v.coiExp || "";
      if (e && e <= iso(addDays(td, 30))) add("coi", v.id, v.name, { due: e, ctx: "insur|coi|certificate|compliance" });
    });
    // and the vendors the compliance detector holds (a sub with no certificate on file)
    const C = (typeof CATCH !== "undefined" ? CATCH : []).find((c) => c.name === "compliance");
    safe(() => C.rows(), []).forEach((x) => { const v = (DB.vendors || []).find((v) => "coi:" + v.id === x.key); v && !out.some((o) => o.k === "coi:" + v.id) && add("coi", v.id, v.name, { due: td, ctx: "insur|coi|certificate|compliance" }); });
    // money: invoices not paid, bills not paid, open POs
    (DB.clients || []).forEach((c) => (c.invoices || []).filter((i) => !["paid", "void"].includes(i.status)).forEach((i) => i.number && add("invoice", c.id + ":" + i.id, i.number, { status: i.status, due: i.due || "" })));
    (DB.bills || []).filter((b) => b.status !== "paid" && b.status !== "void").forEach((b) => b.number && add("bill", b.id, b.number, { status: b.status, due: b.due || "" }));
    (DB.pos || []).filter((x) => !["closed", "void", "received", "cancelled"].includes(x.status)).forEach((x) => x.number && add("po", x.id, x.number, { status: x.status }));
    // the approval queue (everyone's): an approval about a decision, request, bill, submittal or site question is
    // that record shown again; its approval title becomes a second needle of the same record
    const K = byKey();
    safe(() => mApprovals({ everyone: !0 }), []).forEach((a) => {
      let k = "";
      // ids come as "<id>@<project>" for job records, or bare
      const [aid, apid] = String(a.id).split("@");
      const pOf = (f) => apid || (DB.projects.find(f) || {}).id;
      if (a.kind === "dec") { const pid = pOf((p) => (p.decisions || []).some((d) => d.id === aid)); k = "decision:" + pid + ":" + aid; }
      else if (a.kind === "req") { const pid = pOf((p) => (p.requests || []).some((d) => d.id === aid)); k = "request:" + pid + ":" + aid; }
      else if (a.kind === "subm") { const pid = pOf((p) => (p.submittals || []).some((d) => d.id === aid)); k = "submittal:" + pid + ":" + aid; }
      else if (a.kind === "raise") k = "siteq:raise:" + aid;
      else if (a.kind === "bill") k = "bill:" + aid;
      const n = needle(a.title);
      if (k && K[k]) { n && !K[k].n.includes(n) && K[k].n.push(n); K[k].appr = a.who || ""; }
      else add("approval", a.kind + ":" + a.id, a.title, { who: a.who || "", akind: a.kind });
    });
    // mail routed to me
    safe(() => cmListFor("open"), []).forEach((m) => add("inbox", m.id, m.subject || m.text, {}));
    // money flags (Caught for You's detectors) and this role's specialist findings
    (typeof CATCH !== "undefined" ? CATCH : []).forEach((c) => safe(() => c.rows(), []).forEach((x) => add("flag", c.name + ":" + x.key, x.what, { det: c.label })));
    safe(() => rsFindings(r), []).forEach((f) => add("finding", f.key, f.what, { area: f.check && f.check.area }));
    // a needle that belongs to more than one record of different nouns is ambiguous: it counts for each
    return out;
  }

  // the screen: sections are cards (.card, section, .td-sec, details, .panel) holding a visible heading; text outside
  // any section is the page body. Each text node belongs to its nearest section, so nested cards never double count.
  const SEC = ".card, section.td-sec, .td-sec, details, .panel, .f-card, .kpi-card, .tile, .ov-tile, .note.warn, .note";
  const ROW = ".td-card, .f-row, .f-now, .f3-row, .t2-row, tr, li, .q-row, .ap-row, .rowcard, .row-card, .tk-row, .cm-row, .ma-row, .msg-thread, .mt-row, .card .row";
  const JARGON = /\b(detectors?|predicates?|registry|sweeps?|ingest(ed)?|seeded|undefined|null|nan|object object|orphan(ed)?|unrouted|nyh|delegation|payload|webhook|hash|cursor|wip|eac|sov|gl|three-way match|3-way match|obligations?|standard watch|cmtask|tkall|pred)\b/gi;
  const FIELD_JARGON = /\b(retainage|ledger|accrual|accrued|margin|committed|cost codes?|job cost|overhead|wip|eac|sov|coi|three-way|submittals?|rfis?|po lines?|allowance)\b/gi;

  function scrollTop() {
    try { window.scrollTo(0, 0); } catch (e) {}
    document.querySelectorAll(".main, main, #main, .content, .view.on").forEach((e) => { try { e.scrollTop = 0; } catch (x) {} });
  }
  function fold() {
    const bar = [...document.querySelectorAll("#mtabs, #tabbar")].find(vis);
    return bar ? Math.round(bar.getBoundingClientRect().top) : innerHeight;
  }
  function headOf(el) {
    const H = [...el.querySelectorAll("h1,h2,h3,h4,summary,.td-hd b,.hd b")].filter((x) => x.closest(SEC) === el);
    // the phone hides some headings (the header carries the title): the section keeps its name
    const h = H.find(vis) || (el.getAttribute("aria-label") ? null : H[0]);
    return h ? h.textContent.replace(/\s+/g, " ").trim().slice(0, 70) : (el.getAttribute("aria-label") || "").slice(0, 70);
  }
  // a section's shown count: the first number in its header line other than in the heading's own words
  function shownCount(el) {
    const hd = el.querySelector(".td-hd, .hd, summary, .ph");
    if (!hd || hd.closest(SEC) !== el) return null;
    const c = hd.querySelector(".td-cnt, .n, .cnt, .badge, .small.muted, .count");
    const t = (c ? c.textContent : "").trim();
    // a count, never the start of an address ("121 State Street")
    const m = /^\d+\s+[A-Z]/.test(t) ? null : t.match(/^(\d+)\b/);
    return m ? +m[1] : null;
  }
  function tabs(v) {
    return [...v.querySelectorAll(".td-tabs button, .ctabs button, .seg button, .tabs button, [role=tablist] button, .sub-tabs button")].filter(vis).map((b) => {
      const n = b.querySelector(".n, .cnt, .badge");
      const lab = (b.getAttribute("aria-label") || b.title || b.textContent || "").replace(/\s+/g, " ").replace(/\s*\d+\+?$/, "").trim();
      return { l: lab.slice(0, 40), n: n ? +(n.textContent.match(/\d+/) || [0])[0] : null, on: b.classList.contains("on") || b.getAttribute("aria-selected") === "true" };
    });
  }
  function textIndex(v) {
    const secs = new Map(), page = { el: null, segs: [], txt: "" }, getSec = new Map();
    const secOf = (el) => {
      if (getSec.has(el)) return getSec.get(el);
      let e = el, s = null;
      while (e && e !== v) { if (e.matches && e.matches(SEC) && headOf(e)) { s = e; break; } e = e.parentElement; }
      getSec.set(el, s);
      return s;
    };
    const w = document.createTreeWalker(v, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = w.nextNode())) {
      const t = node.nodeValue;
      if (!t || !t.trim()) continue;
      const pe = node.parentElement;
      if (!pe || !vis(pe)) continue;
      if (pe.closest("script,style,select,option,datalist,template")) continue;
      const s = secOf(pe);
      let rec = s ? secs.get(s) : page;
      if (s && !rec) { rec = { el: s, segs: [], txt: "" }; secs.set(s, rec); }
      rec.segs.push({ at: rec.txt.length, node: pe });
      rec.txt += norm(t) + " ";
    }
    return { secs: [...secs.values()], page: page };
  }
  function nodeAt(rec, i) {
    let lo = 0, hi = rec.segs.length - 1, best = rec.segs[0];
    while (lo <= hi) { const m = (lo + hi) >> 1; if (rec.segs[m].at <= i) { best = rec.segs[m]; lo = m + 1; } else hi = m - 1; }
    return best && best.node;
  }
  function rows(v) { return [...v.querySelectorAll(ROW)].filter(vis); }
  // where each catalog record sits: one entry per record found, with the section, its y, its row rank
  function locate(cat, v, idx) {
    const R = rows(v), F = fold(), found = {};
    const all = idx.secs.concat([idx.page]);
    for (const rec of all) {
      if (!rec.txt) continue;
      for (const o of cat) {
        if (o.ctx && !new RegExp(o.ctx).test(rec.txt)) continue;
        for (const n of o.n) {
          let i = rec.txt.indexOf(n);
          // a name-only needle (a vendor) counts only next to its context word (insurance, confirm)
          if (o.ctx) { const re = new RegExp(o.ctx); while (i >= 0 && !re.test(rec.txt.slice(Math.max(0, i - 90), i + n.length + 90))) i = rec.txt.indexOf(n, i + 1); }
          if (i < 0) continue;
          const el = nodeAt(rec, i), b = el ? el.getBoundingClientRect() : { top: 0, bottom: 0 };
          const row = el && el.closest(ROW), rank = row ? R.indexOf(row) + 1 : 0;
          const f = found[o.k];
          const y = Math.round(b.top + (window.scrollY || 0));
          if (!f || y < f.y) found[o.k] = { k: o.k, noun: o.noun, sec: rec.el ? headOf(rec.el) : "(page)", y: y, rank: rank, above: b.top >= 0 && b.top < F - 16 };
          break;
        }
      }
    }
    return found;
  }
  function scan(cat) {
    scrollTop();
    const v = document.querySelector(".view.on");
    if (!v) return null;
    const F = fold(), idx = textIndex(v), found = locate(cat || [], v, idx);
    const h = [...v.querySelectorAll("h1, h2")].find(vis), cr = document.querySelector("#crumbs b");
    const heading = (h ? h.textContent : vis(cr) ? cr.textContent : "").replace(/\s+/g, " ").trim().slice(0, 60);
    const secs = idx.secs.map((rec) => {
      const b = rec.el.getBoundingClientRect(), txt = rec.txt, head = headOf(rec.el);
      const body = txt.replace(norm(head), "").trim();
      const fk = Object.values(found).filter((f) => f.sec === head);
      const nouns = {};
      fk.forEach((f) => (nouns[f.noun] = (nouns[f.noun] || 0) + 1));
      return { h: head, y: Math.round(b.top), hgt: Math.round(b.height), n: shownCount(rec.el), len: body.length,
        empty: body.length < 25 || /^(nothing|no |none|all clear|you're clear|empty|all caught up)/.test(body), nouns: nouns,
        folded: rec.el.tagName === "DETAILS" ? !rec.el.open : rec.el.classList.contains("f-fold") && !rec.el.classList.contains("open") };
    });
    const pageNouns = {};
    Object.values(found).filter((f) => f.sec === "(page)").forEach((f) => (pageNouns[f.noun] = (pageNouns[f.noun] || 0) + 1));
    if (Object.keys(pageNouns).length) secs.push({ h: "(page)", y: 0, hgt: 0, n: null, len: idx.page.txt.length, empty: !1, nouns: pageNouns });
    const alltxt = idx.secs.map((r) => r.txt).join(" ") + " " + idx.page.txt;
    const jar = [...new Set((alltxt.match(JARGON) || []).map((x) => x.toLowerCase()))];
    const fjar = [...new Set((alltxt.match(FIELD_JARGON) || []).map((x) => x.toLowerCase()))];
    const groups = [...v.querySelectorAll(SEC)].filter((e) => vis(e) && !e.parentElement.closest(SEC));
    return {
      view: view, heading: heading, tabs: tabs(v), secs: secs, found: Object.values(found),
      fold: F, pageH: Math.round(v.scrollHeight || v.getBoundingClientRect().height), sw: document.documentElement.scrollWidth, w: innerWidth,
      above: secs.filter((s) => s.h !== "(page)" && s.y < F - 16 && s.y + s.hgt > 0).length,
      groups: groups.length, groupsAbove: groups.filter((e) => e.getBoundingClientRect().top < F - 16).length,
      words: alltxt.split(/\s+/).filter(Boolean).length, jargon: jar, fieldJargon: fjar,
      buttons: [...v.querySelectorAll("button, a.btn")].filter(vis).length, primary: [...v.querySelectorAll(".btn.primary")].filter(vis).length,
    };
  }
  // Delay precursors as of the app's day: what becomes a delay in the next 10 working days if nobody acts, and who
  // must act. Each carries the needles that find it on a screen and the date by which the action is due.
  const UID = { pm: "u_alan", coord: "u_chen", designer: "u_sarah", foreman: "u_angel", owner: "u_owner", client: "u_klein", arch: "u_sarah", sub: "u_chen" };
  function precursors() {
    const td = T(), win = wdAdd(td, 10), tom = wdAdd(td, 1), out = [];
    const add = (kind, k, title, due, actors, why, x) => { const n = needle(title, x && x.ctx); const alt = ((x && x.alt) || []).map((a) => needle(a, x.ctx)).filter((a) => a && a !== n); n && out.push(Object.assign({ kind: kind, k: k, t: String(title).slice(0, 80), due: due || "", actors: [...new Set(actors.filter(Boolean))], why: why }, x || {}, { n: [n].concat(alt) })); };
    const clientOf = (pid) => (pid === "p121" ? "u_klein" : "");
    // materials whose order-by date falls before the window closes (late ones included: they were precursors once)
    safe(() => PRED.toBuy.rows(), []).forEach((r) => {
      if (r.ordered || !r.orderBy || r.orderBy > win) return;
      add("order-by", "material:" + r.p.id + ":" + (r.key || (r.m && r.m.id) || r.name), r.name, r.orderBy, ["u_chen"].concat(r.dec ? ["u_alan"] : []), `order by ${r.orderBy} (needed on site ${r.needBy || "?"})${r.dec ? ", held by a decision" : ""}`, { pid: r.p.id });
    });
    safe(() => DB.sel.items, []).filter((it) => ["sel", "appr", undefined, ""].includes(it.stage)).forEach((it) => {
      const ob = safe(() => selOrderBy(it), "");
      if (!ob || ob > win) return;
      add("order-by", "material:sel:" + it.projectId + ":" + norm(it.name).slice(0, 40), it.name, ob, ["u_chen"].concat(it.stage === "sel" ? ["u_sarah"] : []), `selection ${it.stage === "sel" ? "not yet approved by the client" : "approved"}, order by ${ob}`, { pid: it.projectId });
    });
    DB.projects.forEach((p) => withProject(p, () => {
      (p.decisions || []).filter((d) => d.status === "open").forEach((d) => {
        const due = safe(() => decDue(d), "");
        if (!due || due > win) return;
        const o = String(d.owner || "");
        const act = /client/i.test(o) ? [clientOf(p.id), "u_alan"] : /design|architect/i.test(o) ? ["u_sarah", "u_alan"] : ["u_alan"];
        add("decision", "decision:" + p.id + ":" + d.id, d.name, due, act, `decision needed by ${due} (${o || "no owner"})`, { pid: p.id, alt: [safe(() => clTitle(d), "")] });
      });
      (p.inspections || []).filter((i) => !["passed", "scheduled"].includes(i.status)).forEach((i) => {
        const g = i.gates && (p.tasks || []).find((t) => t.id === i.gates);
        if (!g) return;
        const by = wdAdd(g.start, -((p.project && p.project.inspBuf) || 5));
        if (by > win) return;
        add("inspection", "inspection:" + p.id + ":" + i.id, i.name, by, ["u_alan", "u_angel"], `book by ${by}: ${g.name} starts ${g.start}`, { pid: p.id });
      });
      safe(() => smRows(p), []).forEach((R) => {
        const s = R.s, D = R.D || {}, B = R.B || {};
        if (["closed", "approved", "void"].includes(s.status)) return;
        const due = (R.L && R.L.late && td) || D.submitBy || D.approveBy || "";
        if (!due || due > win) return;
        add("submittal", "submittal:" + p.id + ":" + s.id, s.title, D.submitBy || D.approveBy || due, [UID[B.role] || "u_alan", "u_alan"], `submittal ${s.status}: submit by ${D.submitBy || "?"}, approve by ${D.approveBy || "?"}${B.who ? ", with " + B.who : ""}`, { pid: p.id, alt: [s.clientTitle || ""] });
      });
      (p.requests || []).filter((q) => !["delivered", "closed", "done", "cancelled"].includes(q.status) && q.neededBy && q.neededBy <= wdAdd(td, 2)).forEach((q) =>
        add("crew request", "request:" + p.id + ":" + q.id, q.what, q.neededBy, ["u_chen", "u_angel"], `requested by ${q.by}, needed ${q.neededBy}, status ${q.status}`, { pid: p.id }));
      ((DB.field && DB.field.subs) || []).filter((s) => s.projectId === p.id && s.status === "unconfirmed" && s.date >= td && s.date <= wdAdd(td, 4)).forEach((s) =>
        add("sub to confirm", "subconfirm:" + s.id, s.vendor, s.date, ["u_alan", "u_angel"], `${s.vendor} not confirmed for ${s.date}`, { pid: p.id, ctx: "confirm" }));
      (p.tasks || []).filter((t) => t.status !== "done" && t.start <= win && t.start >= td).forEach((t) => {
        const late = (t.deps || []).map((id) => (p.tasks || []).find((x) => x.id === id)).filter((d) => d && d.status !== "done" && (d.end < td || safe(() => prgState(d).behind, !1)));
        late.length && add("predecessor late", "sched:" + p.id + ":" + t.id, t.name, t.start, ["u_alan", "u_angel"], `starts ${t.start}; ${late.map((d) => d.name + (d.end < td ? " (past its end " + d.end + ")" : " (behind)")).join(", ")}`, { pid: p.id });
      });
    }));
    safe(() => PRED.siteQuestions.rows(), []).forEach((r) => {
      const x = r.x, to = String(x.to || "").toLowerCase();
      const u = DB.users.find((u) => u.id === x.to || u.role === to || (u.name || "").toLowerCase() === to);
      add("site question", "siteq:raise:" + x.id, x.title, x.dueBy || x.needBy || td, [u ? u.id : "u_alan"], `asked by ${x.by || "the site"} ${String(x.at || "").slice(0, 10)}, due ${x.dueBy || x.needBy || "today"}`, { pid: r.p.id });
    });
    (DB.vendors || []).forEach((v) => {
      const e = v.insuranceExp || "";
      if (e && e <= iso(addDays(td, 30))) add("COI lapse", "coi:" + v.id, v.name, iso(addDays(e, -30)), ["u_chen", "u_owner"], `insurance ${e < td ? "lapsed" : "lapses"} ${e} (the Standard: chase 30 days ahead)`, { ctx: "insur|coi|certificate|compliance" });
    });
    const C = (typeof CATCH !== "undefined" ? CATCH : []).find((c) => c.name === "compliance");
    safe(() => C.rows(), []).forEach((x) => { const v = (DB.vendors || []).find((v) => "coi:" + v.id === x.key); v && !out.some((o) => o.k === "coi:" + v.id) && add("COI lapse", "coi:" + v.id, v.name, td, ["u_chen", "u_owner"], `no insurance certificate on file (${x.sub})`, { ctx: "insur|coi|certificate|compliance" }); });
    return { today: td, window: win, tomorrow: tom, items: out };
  }
  window.IA = { norm: norm, needle: needle, catalog: catalog, scan: scan, fold: fold, scrollTop: scrollTop, ROLE_OF: ROLE_OF, precursors: precursors,
    find: (cat) => { scrollTop(); const v = document.querySelector(".view.on"); return v ? Object.values(locate(cat, v, textIndex(v))) : []; } };
})();
