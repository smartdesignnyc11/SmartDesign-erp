/*<<clientdocs.js>>*/
// =====================================================================================================================
// Client documents (lane p2fix3, 2026-10-25). Pilot 2's Documents Workshop: the owner, the designer, the PM, billing
// and the client (Sarah Klein) read every estimate, change order, invoice and pay application as it reached a client.
// "The client's eyes" (CLAUDE.md, Alan's lens 4): clear, premium, nothing that makes them call to ask. Six classes:
//  S1  internal text reached the client: the PM's working notes ("5 lines fell back to cost — check them before
//      sending", "measured by foreman update 9/2") printed on INV-2026-040, and "Angel asked 9/8" on CO-2026-004;
//  S1  a $0 or blank document could be sent or signed (EST-2026-016: $0, one blank line, project "Proposal");
//  S2  no letterhead: "SmartDesigns" in plain text, no mark, address, phone or licences, no SD Plumbing / SD Electric,
//      dates without a year, two estimate templates with contradicting terms (net 7 against "within 15 days"), dues on
//      a Saturday;
//  S2  no invoice said how to pay;
//  S2  the pay application showed its answer twice, retainage read 10% this period and 6.4% to date, and the approved
//      change orders it counted had no line on it;
//  S3  a change order printed no contract sum before and after and no reason type.
//
// The rule (S1): a client document is drawn from the client fields only (CX_CLIENT below). Every other field is
// internal (cost, cost code, margin, vendor, the evidence behind a percent, Internal Notes) and never renders on a
// print, a PDF, the portal or client mail. A client field that holds working-note wording (CX_NOTE_RES) or a staff
// first name in an internal phrase is cleaned where it is drawn, and Send refuses it until the note is moved to
// Internal Notes (one tap). The app's own notes are written to Internal Notes and to the line's evidence at the
// source, and records written before this are moved once at boot.
//
// One renderer (cxDocHtml) draws every client document type on one letterhead from the company settings: proposal,
// change order, invoice, design-fee invoice, deposit invoice and the pay application (AIA G702/G703). printDoc's
// outermost layer uses it, so the root print, ctPrint (the second estimate template), the pay-application block and
// the exhibits layer no longer draw a client document; docPrintHtml (the mail attachment and the tests) reads the same.
//
// Design gate (BACKLOG §1.16). No new noun, list, queue or store. It extends the existing records: the company record
// (DB.company: tagline, lics, remit, footers), the change order (reasonType), the document's Internal Notes (internal)
// and a pay-application line (evidence). The send gate is a refusal on the existing actions (Send, Send to Client, Mark
// as Sent, Print, Approve), with the reason shown. The portal's Waiting on You (clWaitingItems) is unchanged; the
// Overview adds the client's own recent approvals under it and Your Account lists every document already sent, so a
// client finds what they signed and what they owe in one place. Approved change orders missing from an application
// are added to the draft (pgAddCOLines, the existing path); the existing reminder ("approved change orders not yet on a
// progress invoice") carries the rest to billing.
// =====================================================================================================================

const CX_TYPES = ["estimate", "co", "invoice"];

// ---- the company letterhead and how to pay (settings) --------------------------------------------------------------
// Every client document reads these, nowhere else. The demo values are invented (Alan, 2026-10-25: the demo company's
// names and addresses are invented); a live copy shows only what the firm has typed in Settings.
const CX_FOOTERS = {
  estimate: "Prices hold until the date above. Work outside this scope is done only on a change order you approve in writing before it starts.",
  co: "This change order becomes part of your contract when you approve it. The work it describes starts after your written approval.",
  progress: "Retainage is held on each progress application and released with the final invoice once the punch list is complete.",
  deposit: "Your deposit is credited against the progress applications as the work is done.",
  design: "Design fees are billed at the milestones in your design agreement.",
  invoice: "Thank you. Please put the invoice number on your payment.",
};
const CX_REASONS = [
  ["client", "Client request"],
  ["unforeseen", "Unforeseen condition"],
  ["code", "Code requirement"],
  ["design", "Design change"],
];
function cxLetterSeed() {
  // the demo company's letterhead and remit-to (invented); never on the firm's own records
  if (sdSeedsOff()) return;
  const co = DB.company;
  if (!co || co.__cxSeeded) return;
  co.__cxSeeded = 1;
  const fill = (k, v) => {
    (null == co[k] || "" === co[k]) && (co[k] = v);
  };
  fill("tagline", "Design, build, SD Plumbing and SD Electric under one roof");
  fill("addr", "214 Court Street, Brooklyn, NY 11201");
  fill("phone", "(718) 555-0190");
  fill("email", "office@smartdesign.example");
  fill("web", "smartdesign.example");
  (co.lics && co.lics.length) ||
    (co.lics = ["NYC Home Improvement Contractor #2091458", "SD Plumbing: NYC Licensed Master Plumber #2317", "SD Electric: NYC Licensed Master Electrician #11842"]);
  co.remit = Object.assign({ bank: "Atlantic Community Bank", last4: "4417", payableTo: "", mailTo: "" }, co.remit || {});
}
function cxCo(d) {
  const co = DB.company || {},
    ent = d && d.entityId ? (DB.entities || []).find((e) => e.id === d.entityId && "property" !== e.type) : null,
    ent1 = (DB.entities || []).find((e) => "ent1" === e.id) || null,
    lics = (co.lics && co.lics.length ? co.lics : co.lic ? [co.lic] : []).filter(Boolean),
    remit = co.remit || {};
  return {
    name: co.name || "SmartDesign",
    legal: (ent || ent1 || {}).name || co.name || "SmartDesign",
    tagline: co.tagline || "",
    addr: co.addr || "",
    phone: co.phone || "",
    email: co.email || "",
    web: co.web || "",
    logo: co.logo || "",
    lics: lics,
    remit: { bank: remit.bank || "", last4: String(remit.last4 || "").replace(/\D/g, "").slice(-4), payableTo: remit.payableTo || (ent || ent1 || {}).name || co.name || "", mailTo: remit.mailTo || co.addr || "" },
    footers: Object.assign({}, CX_FOOTERS, co.footers || {}),
  };
}

// ---- words the client reads: full dates, units, terms ----------------------------------------------------------------
function cxDate(s) {
  const d = s ? parse(s) : null;
  return d && !isNaN(d) ? d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }) : "";
}
const CX_UNITS = { ls: "lump sum", ea: "each", sf: "sq ft", lf: "linear ft", sy: "sq yd", cy: "cu yd", hr: "hours", hrs: "hours", day: "days", days: "days", wk: "weeks", mo: "months", allow: "allowance", pr: "pairs", set: "sets", lot: "lot" };
function cxQty(l) {
  const q = +l.qty || 0,
    u = String(l.unit || "").trim(),
    w = CX_UNITS[u.toLowerCase()] || u;
  if ("ls" === u.toLowerCase() && 1 === q) return "Lump sum";
  const one = 1 === q && /s$/.test(w) && !/^(sq|cu|linear)/.test(w) ? w.replace(/s$/, "") : w;
  return `${q.toLocaleString()}${one ? " " + one : ""}`;
}
// the days a document's own terms give ("Net 15", "net 7", "Due on receipt"); null when they name none
function cxTermsDays(terms) {
  const t = String(terms || "");
  if (/\b(on receipt|at signing|upon receipt)\b/i.test(t) && !/net\s*\d/i.test(t)) return 0;
  const m = /net\s*(\d+)/i.exec(t) || /(\d+)\s*days/i.exec(t);
  return m ? +m[1] : null;
}
// a due date never lands on a weekend or a holiday: it rolls to the next business day
function cxBizDay(s) {
  try {
    return s ? nextWork(s) : s;
  } catch (e) {
    return s;
  }
}
function cxDueFor(date, terms) {
  const n = cxTermsDays(terms);
  return cxBizDay(iso(addDays(date || today(), null != n ? n : (cxTermsDays(DB.company.terms) ?? 15))));
}

// ---- the client-field rule -------------------------------------------------------------------------------------------
// The fields a client document may draw. Everything else on the record is internal and never reaches a client.
const CX_CLIENT = {
  doc: ["number", "date", "due", "validUntil", "title", "memo", "terms", "scheduleDays", "reasonType", "exhibits", "depositPct", "retainagePct", "taxRate", "discount"],
  line: ["item", "desc", "qty", "unit", "rate", "scheduled", "prevPct", "pct", "num", "parent", "taxable"],
};
// working-note wording: the app's own notes about evidence and checks, and money a client never sees
const CX_NOTE_RES = [
  /\bfell back to\b/i,
  /\bbefore (sending|you send|it goes out)\b/i,
  /\bcheck (it|them|this|these|those)\b/i,
  /\bmeasured by\b/i,
  /\belapsed time\b/i,
  /\bpercentages proposed\b/i,
  /\bmeasures? below what was already billed\b/i,
  /\bcorrection is a credit with a reason\b/i,
  /\bfill in what you know\b/i,
  /\bno evidence\b/i,
  /\bcost \(fallback\)/i,
  /\bby cost\b/i,
  /\bschedule stale\b/i,
  /\bcost codes?\b/i,
  /\bbudget(ed)? cost\b/i,
  /\bour cost\b/i,
  /\bmargin\b/i,
  /\bmark-?up\b/i,
  /\b(foreman|PM|crew|office) (update|note|asked|said)\b/i,
  /\bdo not send\b/i,
  /\bTODO\b/,
];
const CX_MACHINE = CX_NOTE_RES.slice(0, 13);
// staff first names, less the client's own people (a client named Sarah asking for an outlet is the client)
function cxStaff(c) {
  const mine = new Set(
    [c && c.name, ...((c && c.contacts) || []).map((x) => x.name)]
      .filter(Boolean)
      .flatMap((n) => String(n).split(/[\s&,]+/))
      .map((w) => w.toLowerCase()),
  );
  const out = new Set();
  [...(DB.users || []).filter((u) => u.role && "client" !== u.role && !/^mb/.test(u.role)), ...(DB.employees || [])].forEach((u) => {
    const f = String(u.name || "").split(/\s+/)[0];
    f && f.length > 2 && /^[A-Z][a-z]+$/.test(f) && !/^(Owner|Billing|Controller|Design|Crew|Office|Rachel|Priya)$/.test(f) && !mine.has(f.toLowerCase()) && out.add(f);
  });
  return [...out];
}
function cxStaffRe(c) {
  const n = cxStaff(c);
  return n.length
    ? new RegExp(`\\bper\\s+(?:${n.join("|")})\\b|\\b(?:${n.join("|")})(?:'s)?\\s+(?:asked|said|says|called|wants|wanted|told|requested|flagged|noted|confirmed|measured|checked|thinks|approved|call|note|update)\\b`, "i")
    : null;
}
// sentences: a semicolon joins the parts of one note ("schedule or deliveries; cost only where..."), so it never splits one
const cxPieces = (line) => String(line).split(/(?<=[.!?])\s+/);
function cxIsNote(s, sre, machineOnly) {
  return (machineOnly ? CX_MACHINE : CX_NOTE_RES).some((re) => re.test(s)) || (!machineOnly && !!sre && sre.test(s));
}
// the working-note pieces of a client field
function cxHits(text, c, sre) {
  if (!text) return [];
  const re = void 0 === sre ? cxStaffRe(c) : sre;
  return String(text)
    .split(/\n/)
    .flatMap(cxPieces)
    .map((s) => s.trim())
    .filter((s) => s && cxIsNote(s, re));
}
// a client field with its working-note pieces taken out
function cxClean(text, c, sre) {
  if (!text) return "";
  const re = void 0 === sre ? cxStaffRe(c) : sre;
  return String(text)
    .split(/\n/)
    .map((line) =>
      cxPieces(line)
        .filter((s) => !cxIsNote(s.trim(), re))
        .join(" ")
        .replace(/\s*[;—–-]\s*$/, "")
        .trim(),
    )
    .filter((x, i, A) => x || (i > 0 && A[i - 1]))
    .join("\n")
    .trim();
}
// the record as a client may see it: the same record with its client text cleaned (the portal's summary draws this)
function cxClientCopy(c, d) {
  if (!d || !CX_TYPES.includes(d.type)) return d;
  const re = cxStaffRe(c);
  return Object.assign({}, d, {
    title: cxClean(d.title, c, re),
    memo: cxClean(d.memo, c, re),
    terms: cxClean(d.terms, c, re),
    lines: (d.lines || []).map((l) => Object.assign({}, l, { item: cxClean(l.item, c, re), desc: cxClean(l.desc, c, re) })),
  });
}
// The app's own notes go to Internal Notes and the line's evidence, never to the memo or a line's description.
function cxMoveMachine(d, why) {
  if (!d || !CX_TYPES.includes(d.type)) return 0;
  const wasClean = "function" == typeof docDirty ? !docDirty(d) : !1;
  let n = 0;
  const keep = [],
    moved = [];
  String(d.memo || "")
    .split(/\n/)
    .forEach((line) => {
      const P = cxPieces(line),
        k = P.filter((s) => !cxIsNote(s.trim(), null, !0));
      P.length !== k.length && moved.push(P.filter((s) => cxIsNote(s.trim(), null, !0)).join(" "));
      keep.push(k.join(" ").trim());
    });
  moved.length &&
    ((d.memo = keep.filter(Boolean).join("\n")),
    (d.internal = [d.internal || "", ...moved.filter((m) => !String(d.internal || "").includes(m))].filter(Boolean).join("\n")),
    (n += moved.length));
  (d.lines || []).forEach((l) => {
    if (!l.desc) return;
    const P = cxPieces(l.desc),
      bad = P.filter((s) => cxIsNote(s.trim(), null, !0));
    if (!bad.length) return;
    (l.evidence = [l.evidence || "", bad.join(" ")].filter(Boolean).join(" · ")),
      (l.desc = P.filter((s) => !cxIsNote(s.trim(), null, !0))
        .join(" ")
        .replace(/\s*[;—–-]\s*$/, "")
        .trim()),
      n++;
  });
  if (n) {
    wasClean && "function" == typeof docMark && docMark(d);
    try {
      why && "draft" !== d.status && audit(d.type, d.id, "client-text", "", "", `${n} working note${1 === n ? "" : "s"} moved off the client's copy of ${d.number} to Internal Notes (${why})`);
    } catch (e) {}
  }
  return n;
}
// a person's own working notes in a client field (Send offers to move them in one tap)
function cxMoveTyped(c, d) {
  const re = cxStaffRe(c),
    moved = [],
    take = (txt, where) => {
      const H = cxHits(txt, c, re);
      return H.length ? (moved.push(`${where}: ${H.join(" ")}`), cxClean(txt, c, re)) : txt;
    };
  (d.title = take(d.title, "Title")), (d.memo = take(d.memo, "Notes"));
  (d.lines || []).forEach((l, i) => {
    (l.item = take(l.item, `Line ${i + 1}`)), (l.desc = take(l.desc, `Line ${i + 1}`));
  });
  moved.length && (d.internal = [d.internal || "", ...moved].filter(Boolean).join("\n"));
  return moved.length;
}

// ---- the send gate ---------------------------------------------------------------------------------------------------
// What stops a document reaching a client: a $0 total, a line with no words, no one to bill, or a working note in a
// client field. The Standard: "Accuracy is client service" and "The Name Test" (would you sign your name to it?).
// where the bill goes: the client's billing address, else the property, else the job's own address (it fills itself)
function cxBillAddr(c, d) {
  // only the client's own job: a document tagged with another client's job never borrows that job's address
  const mine = (DB.projects || []).filter((x) => x.clientId === (c && c.id)),
    p = (d && d.projectId && mine.find((x) => x.id === d.projectId)) || mine[0];
  return String((c && (c.billingAddr || c.propertyAddr)) || (p && p.project && p.project.addr) || "").trim();
}
const CX_GENERIC_TITLE = /^\s*(proposal|estimate|change order|invoice|new (estimate|proposal|change order|invoice)|untitled|draft)?\s*$/i;
function cxGate(c, d) {
  const R = [];
  if (!c || !d || !CX_TYPES.includes(d.type)) return R;
  const t = docTotal(d),
    sov = "sov" === d.mode,
    L = (d.lines || []).filter((l) => !sov || l.sovId);
  Math.abs(+t.total || 0) < 0.005 &&
    R.push({ k: "zero", msg: sov ? "Nothing is billed on this application: it totals $0." : `It totals $0${L.length ? "" : " and has no lines"}.` });
  sov ||
    L.forEach((l, i) => {
      String(l.item || "").trim() || String(l.desc || "").trim() || R.push({ k: "empty", msg: `Line ${l.num || i + 1} has no description: the client would sign or pay a blank line.` });
    });
  String(c.name || "").trim() || R.push({ k: "billto", msg: "The client has no name to bill." });
  cxBillAddr(c, d) || R.push({ k: "billto", msg: `${esc(c.name || "The client")} has no billing or property address: add it on the client.` });
  const re = cxStaffRe(c),
    note = (txt, where) =>
      cxHits(txt, c, re).forEach((h) => R.push({ k: "note", fix: !0, msg: `${where} says "${esc(h.length > 90 ? h.slice(0, 88) + "…" : h)}": a working note or a staff name never goes to the client.` }));
  note(d.title, "The title"), note(d.memo, "The notes");
  (d.lines || []).forEach((l, i) => {
    note(l.item, `Line ${l.num || i + 1}`), note(l.desc, `Line ${l.num || i + 1}`);
  });
  return R;
}
function cxGateModal(c, d, R, mode) {
  const fix = R.some((r) => r.fix),
    editable = "draft" === d.status,
    kind = { estimate: "proposal", co: "change order", invoice: "invoice" }[d.type];
  mbModal(
    "Not Ready for the Client",
    `<div class="note warn cx-gate-why">${esc(d.number)} cannot go to ${esc(c.name || "the client")} yet. Accuracy is client service (the SmartDesign Standard): a client never reads a working note, a $0 total or a blank line.</div><ul class="cx-gate-list">${R.map((r) => `<li class="small">${r.msg}</li>`).join("")}</ul>${"print" === mode ? '<p class="small muted" style="margin:6px 0 0">Print Draft Copy prints it marked as a draft, for the office only.</p>' : ""}`,
    {
      submit: fix && editable ? "Move Notes to Internal" : null,
      onSubmit: () => {
        const n = cxMoveTyped(c, d);
        save(), render(), toast(`${n} note${1 === n ? "" : "s"} moved to Internal Notes on ${d.number}; the client's copy no longer shows ${1 === n ? "it" : "them"}`, flowGo.doc(c, d.type, d));
      },
      alt: "print" === mode ? { label: "Print Draft Copy", run: () => printDoc(c, d, { draft: !0 }) } : null,
    },
  );
  try {
    audit(d.type, d.id, "client-gate", d.status, d.status, `${mode}: ${R.map((r) => r.k).join(", ")}`);
  } catch (e) {}
  return kind;
}

// ---- contract sums on a change order and a pay application -----------------------------------------------------------
function cxContract(c, projectId) {
  const K = (c.contracts || {})[projectId || ""] || null,
    est = (c.estimates || []).find((e) => ["converted", "billed"].includes(e.status) && (!projectId || e.projectId === projectId));
  return K ? +K.net || +K.base || 0 : est ? docNet(est) : +c.contractNet || +c.contract || 0;
}
const cxApproved = (x) => ["approved", "billed"].includes(x.status);
// the change orders an application counts: approved on or before its date, or already carried on one of its lines
function cxAppCOs(c, d) {
  const onIt = new Set(
    (d.lines || [])
      .map((l) => (c.sov || []).find((v) => v.id === l.sovId))
      .filter((v) => v && v.coId)
      .map((v) => v.coId),
  );
  return (c.changeOrders || []).filter((x) => cxApproved(x) && (!x.projectId || !d.projectId || x.projectId === d.projectId) && (onIt.has(x.id) || !x.approvedOn || !d.date || x.approvedOn <= d.date));
}
// every approved change order on the job has a line on the job's schedule of values and on its draft application
function cxEnsureCoLines(c, d) {
  if (!c || !d || "sov" !== d.mode || "draft" !== d.status) return [];
  const added = [];
  cxAppCOs(c, d).forEach((co) => {
    c.sov.some((v) => v.coId === co.id || v.source === co.number) ||
      c.sov.push({ id: uid("sv"), desc: co.title, scheduled: docTotal(co).total, source: co.number, order: c.sov.length, coId: co.id, projectId: co.projectId || d.projectId || void 0 });
  });
  const p = DB.projects.find((x) => x.id === d.projectId);
  if (p && "function" == typeof pgAddCOLines) {
    const before = new Set((d.lines || []).map((l) => l.sovId));
    pgAddCOLines(c, p, d);
    (d.lines || []).filter((l) => !before.has(l.sovId)).forEach((l) => added.push(l.item));
  }
  return added;
}

// ---- one renderer for every client document --------------------------------------------------------------------------
function cxKind(d) {
  if ("estimate" === d.type) return "estimate";
  if ("co" === d.type) return "co";
  // depositOf names the estimate whose deposit an application draws on; a deposit invoice is one that bills the deposit
  // the contract's deposit invoice (one line, no retainage; ctDepositInvoice) prints as a Deposit Invoice with its own
  // footer, never the construction or plain invoice footer
  // one predicate with the ledger and lineFin (invIsDeposit): an application booked as work prints as an application
  if ("invoice" === d.type && "function" == typeof invIsDeposit && invIsDeposit(d)) return "deposit";
  if ("sov" === d.mode) return "progress";
  if ("design" === d.template || d.retainerOf) return "design";
  const est = d.fromDoc && (DB.clients || []).flatMap((c) => c.estimates || []).find((e) => e.id === d.fromDoc);
  return est && "design" === est.template ? "design" : "invoice";
}
const CX_LABEL = { estimate: "Proposal", co: "Change Order", progress: "Application for Payment", deposit: "Deposit Invoice", design: "Design Fee Invoice", invoice: "Invoice" };
const CX_MARK =
  '<svg class="cx-mark" width="40" height="40" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round" aria-hidden="true"><rect x="1.5" y="1.5" width="37" height="37"/><path d="M9 31V16.5L20 8l11 8.5V31z"/><path d="M15.5 31v-8h9v8M9 20.5h22M14 13.2h12"/></svg>';
const CX_CSS = `.cxd{font:12.5px/1.5 Georgia,"Times New Roman",serif;color:#1D2430;max-width:860px;margin:0 auto;position:relative}.cxd .sans{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}.cxd-lh{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;border-bottom:1.5px solid #1D2430;padding-bottom:12px}.cxd-brand{display:flex;gap:12px;align-items:center}.cxd-brand img{max-height:44px}.cxd-word{font-size:26px;letter-spacing:.06em;line-height:1}.cxd-tag{font-size:11px;color:#4A5462;letter-spacing:.04em;margin-top:4px}.cxd-firm{text-align:right;font-size:11px;color:#4A5462;line-height:1.55}.cxd-lics{font-size:10px;color:#6b7480;padding:5px 0 0;letter-spacing:.02em}.cxd-hd{display:flex;justify-content:space-between;align-items:flex-end;margin:22px 0 14px;gap:20px}.cxd-kind{font-size:21px;letter-spacing:.04em}.cxd-num{font-size:11.5px;color:#4A5462;text-align:right;line-height:1.6}.cxd-meta{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:14px}.cxd-k{font-size:10.5px;color:#6b7480;letter-spacing:.06em;text-transform:uppercase;margin-bottom:2px}.cxd-subj{font-size:15px;margin:6px 0 4px}.cxd table{width:100%;border-collapse:collapse;margin:8px 0}.cxd th{font:600 10.5px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;letter-spacing:.04em;text-transform:uppercase;text-align:left;color:#4A5462;border-bottom:1.5px solid #1D2430;padding:6px 6px}.cxd td{padding:7px 6px;border-bottom:1px solid #E6E9EE;vertical-align:top}.cxd .r{text-align:right;white-space:nowrap}.cxd .n{width:28px;color:#6b7480}.cxd .ds{color:#4A5462;font-size:11.5px;white-space:pre-wrap;margin-top:2px}.cxd tr.child td{background:#FAFBFC}.cxd tr.child td:nth-child(2){padding-left:18px}.cxd-tot{margin:10px 0 0 auto;width:360px}.cxd-tot div{display:flex;justify-content:space-between;gap:16px;padding:3px 0}.cxd-tot .big{border-top:1.5px solid #1D2430;margin-top:5px;padding-top:7px;font-size:15px;font-weight:700}.cxd-tot .dim{color:#6b7480;font-size:11.5px}.cxd-box{border:1px solid #D9DDE3;padding:10px 12px;margin:14px 0;font-size:12px}.cxd-box b{letter-spacing:.02em}.cxd-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.cxd-memo{white-space:pre-wrap;margin-top:12px}.cxd-sig{display:grid;grid-template-columns:1fr 1fr;gap:40px;margin-top:38px;font-size:11.5px}.cxd-sig div{border-top:1px solid #1D2430;padding-top:6px;color:#4A5462}.cxd-foot{margin-top:24px;border-top:1px solid #D9DDE3;padding-top:8px;font-size:10.5px;color:#6b7480}.cxd-draft{position:absolute;top:240px;left:0;right:0;text-align:center;font:700 54px -apple-system,Helvetica,Arial,sans-serif;color:rgba(178,34,34,.13);transform:rotate(-18deg);pointer-events:none;letter-spacing:.08em}@media print{.cxd tr{page-break-inside:avoid}}`;
function cxLetterhead(d) {
  const K = cxCo(d),
    firm = [K.addr, [K.phone, K.email].filter(Boolean).join(" · "), K.web].filter(Boolean);
  return `<div class="cxd-lh"><div class="cxd-brand">${K.logo ? `<img src="${esc(K.logo)}" alt="">` : CX_MARK}<div><div class="cxd-word">${esc(K.name)}</div>${K.tagline ? `<div class="cxd-tag sans">${esc(K.tagline)}</div>` : ""}</div></div><div class="cxd-firm sans">${firm.map(esc).join("<br>")}</div></div>${K.lics.length ? `<div class="cxd-lics sans">${K.lics.map(esc).join(" · ")}</div>` : ""}`;
}
// how to pay: one block from the company settings, on every invoice, the portal's invoice and the statement
function cxRemitHtml(c, d, where) {
  const K = cxCo(d),
    R = K.remit,
    portal = (DB.users || []).some((u) => "client" === u.role && u.clientId === (c && c.id)),
    rows = [];
  R.bank && rows.push(`Bank transfer (ACH or wire) to ${esc(K.legal)} at ${esc(R.bank)}${R.last4 ? `, account ending ${esc(R.last4)}` : ""}. Full account details come from us by phone or in your portal, never in an email.`);
  R.payableTo && rows.push(`Check payable to ${esc(R.payableTo)}${R.mailTo ? `, mailed to ${esc(R.mailTo)}` : ""}.`);
  portal && "portal" !== where && rows.push("Your client portal shows this invoice and its balance under Your Account, where you can ask us about it.");
  rows.length || rows.push(`Pay ${esc(K.name)} by check or bank transfer; call${K.phone ? " " + esc(K.phone) : " us"} for the details.`);
  return `<div class="cxd-box cx-remit"><b>How to Pay</b>${d && d.number ? ` <span class="sans" style="font-size:11px;color:#6b7480">· put ${esc(d.number)} on your payment</span>` : ""}<div style="margin-top:4px">${rows.join("<br>")}</div>${K.phone ? `<div class="sans" style="font-size:11px;color:#6b7480;margin-top:4px">We never change where you pay by email. If a message asks you to, call ${esc(K.phone)} before you send anything.</div>` : ""}</div>`;
}
function cxProject(c, d) {
  const p = DB.projects.find((x) => x.id === d.projectId),
    re = cxStaffRe(c),
    pn = ((p && p.project && p.project.name) || "").trim(),
    subj = cxClean(d.title, c, re).replace(/\s*[—–-]\s*work through .*$/i, ""),
    addr = c.propertyAddr || (p && p.project && p.project.addr) || "";
  const name = pn || subj || addr,
    showSubj = subj && subj !== name && !(pn && subj.startsWith(pn + " —")) ? subj : "",
    showAddr = addr && addr !== name && !name.includes(addr) ? addr : "";
  return { name, subj: showSubj, addr: showAddr };
}
function cxLinesHtml(c, d, re) {
  let L = d.lines || [];
  try {
    "construction" === d.template && "function" == typeof ctOrdered && (ctNumber(d), (L = ctOrdered(d)));
  } catch (e) {}
  const kids = new Set(L.filter((l) => l.parent).map((l) => l.parent));
  return `<table><thead><tr><th class="n">#</th><th>Item</th><th class="r">Quantity</th><th class="r">Rate</th><th class="r">Amount</th></tr></thead><tbody>${L.map((l, i) => {
    const item = cxClean(l.item, c, re),
      desc = cxClean(l.desc, c, re);
    return `<tr class="${l.parent ? "child" : ""}"><td class="n">${esc(String(l.num || i + 1))}</td><td>${esc(item)}${desc ? `<div class="ds">${esc(desc)}</div>` : ""}</td><td class="r">${kids.has(l.id) && !+l.rate ? "" : esc(cxQty(l))}</td><td class="r">${kids.has(l.id) && !+l.rate ? "" : money(l.rate)}</td><td class="r">${money(lineAmount(l, d))}</td></tr>`;
  }).join("")}</tbody></table>`;
}
function cxTotalsHtml(d, t, kind, paidOn) {
  const due = "invoice" === d.type;
  return `<div class="cxd-tot sans"><div><span>Subtotal</span><span>${money(t.sub)}</span></div>${t.disc ? `<div><span>Discount</span><span>− ${money(t.disc)}</span></div>` : ""}${t.tax ? `<div><span>Sales tax (${+d.taxRate}%)</span><span>${money(t.tax)}</span></div>` : ""}${t.ret ? `<div><span>Retainage held (${+d.retainagePct}%)</span><span>− ${money(t.ret)}</span></div>` : ""}${t.dep ? `<div><span>Less deposit applied</span><span>− ${money(t.dep)}</span></div>` : ""}${d.retainerApplied ? `<div class="dim"><span>Retainer already applied</span><span>${money(d.retainerApplied)}</span></div>` : ""}<div class="big"><span>${due ? (paidOn ? "Invoice total" : "Amount due") : kind === "co" ? "Change order total" : "Total"}</span><span>${money(t.total)}</span></div>${paidOn ? `<div><span>Payments received</span><span>− ${money(paidOn)}</span></div><div class="big"><span>Balance due</span><span>${money(t.total - paidOn)}</span></div>` : ""}</div>`;
}
// The pay application: AIA G703 continuation lines and the G702 summary, each total shown once.
function cxPayAppHtml(c, d, re) {
  const A = payAppData(c, d),
    t = docTotal(d),
    L = (d.lines || []).filter((l) => l.sovId),
    rows = L.map((l, i) => {
      const s = +l.scheduled || 0,
        prev = r2((s * (+l.prevPct || 0)) / 100),
        now = lineAmount(l, d),
        to = r2(prev + now),
        desc = cxClean(l.desc, c, re);
      return `<tr><td class="n">${i + 1}</td><td>${esc(cxClean(l.item, c, re))}${desc ? `<div class="ds">${esc(desc)}</div>` : ""}</td><td class="r">${money(s)}</td><td class="r">${money(prev)}</td><td class="r">${now ? money(now) : "—"}</td><td class="r">${money(to)}<div class="ds">${s ? r2((to / s) * 100) : 0}%</div></td><td class="r">${money(r2(s - to))}</td></tr>`;
    }),
    pct = +d.retainagePct || 0,
    prevApps = c.invoices.filter((i) => "sov" === i.mode && i.id !== d.id && !["void", "draft"].includes(i.status) && (!i.projectId || i.projectId === d.projectId) && i.date <= d.date),
    depGross = r2(prevApps.filter((i) => !(+i.retainagePct > 0)).reduce((a, i) => a + docTotalBase(i).sub - docTotalBase(i).disc, 0)),
    progGross = r2(A.completed - depGross),
    cos = cxAppCOs(c, d),
    retWhy =
      pct && Math.abs(r2((progGross * pct) / 100) - A.retToDate) < 1
        ? `${pct}% of the ${money(progGross)} of progress work billed to date${depGross ? `; the ${money(depGross)} deposit carries none` : ""}`
        : `${A.completed ? r2((A.retToDate / A.completed) * 100) : 0}% of the ${money(A.completed)} completed to date${depGross ? `, since the ${money(depGross)} deposit carries none` : ""}`;
  return `<table><thead><tr><th class="n">#</th><th>Work</th><th class="r">Scheduled value</th><th class="r">Previous applications</th><th class="r">This period</th><th class="r">Completed to date</th><th class="r">Balance to finish</th></tr></thead><tbody>${rows.join("")}</tbody></table>
  <div class="cxd-grid"><div class="cxd-box sans" style="font-size:11.5px"><b>Retainage</b><div>Held to date: ${money(A.retToDate)}, which is ${retWhy}. It is released with the final invoice.</div>${cos.length ? `<div style="margin-top:6px"><b>Change orders in the contract sum</b><div>${cos.map((x) => `${esc(x.number)} ${esc(cxClean(x.title, c, re))} ${money(docNet(x))}`).join("<br>")}</div></div>` : ""}</div>
  <div class="cxd-tot sans" style="width:auto"><div><span>Original contract sum</span><span>${money(A.orig)}</span></div><div><span>Net change by approved change orders</span><span>${money(A.coAmt)}</span></div><div><span>Contract sum to date</span><span>${money(A.revised)}</span></div><div><span>Completed to date (${A.pctComplete}%)</span><span>${money(A.completed)}</span></div><div><span>Less retainage held to date</span><span>− ${money(A.retToDate)}</span></div><div><span>Earned less retainage</span><span>${money(r2(A.completed - A.retToDate))}</span></div><div><span>Less previous applications</span><span>− ${money(A.prevPaid)}</span></div>${A.dep ? `<div><span>Less deposit applied</span><span>− ${money(A.dep)}</span></div>` : ""}${t.tax ? `<div><span>Sales tax this period</span><span>${money(t.tax)}</span></div>` : ""}<div class="big"><span>Current payment due</span><span>${money(A.due)}</span></div><div class="dim"><span>This period: ${money(A.thisGross)} of work, less ${pct}% retainage (${money(t.ret)})</span><span></span></div><div class="dim"><span>Balance to finish, including retainage</span><span>${money(r2(A.balanceToFinish + A.retToDate))}</span></div></div></div>`;
}
function cxCoBlock(c, d, re) {
  const orig = cxContract(c, d.projectId),
    prior = (c.changeOrders || []).filter(
      (x) => x.id !== d.id && cxApproved(x) && (!x.projectId || !d.projectId || x.projectId === d.projectId) && (!cxApproved(d) || !d.approvedOn || !x.approvedOn || x.approvedOn < d.approvedOn || (x.approvedOn === d.approvedOn && x.number < d.number)),
    ),
    pAmt = r2(prior.reduce((a, x) => a + docNet(x), 0)),
    me = docNet(d),
    days = +d.scheduleDays || 0,
    reason = (CX_REASONS.find((r) => r[0] === (d.reasonType || cxInferReason(d))) || [])[1] || "",
    sov = (c.sov || []).some((v) => "Contract" === v.source && (null == v.projectId || v.projectId === d.projectId));
  return `<div class="cxd-grid"><div class="cxd-box sans" style="font-size:11.5px">${reason ? `<div><b>Reason for the change:</b> ${esc(reason)}</div>` : ""}<div><b>Schedule:</b> ${days ? `adds ${days} working day${1 === days ? "" : "s"}` : "no change to the schedule"}</div><div><b>Billing:</b> ${sov ? "billed on your next progress application once approved" : "invoiced once approved"}</div></div><div class="cxd-tot sans" style="width:auto"><div><span>Original contract sum</span><span>${money(orig)}</span></div><div><span>Change orders approved before this one${prior.length ? ` (${prior.length})` : ""}</span><span>${money(pAmt)}</span></div><div><span>Contract sum before this change</span><span>${money(r2(orig + pAmt))}</span></div><div><span>This change order</span><span>${me < 0 ? "− " + money(-me) : money(me)}</span></div><div class="big"><span>New contract sum</span><span>${money(r2(orig + pAmt + me))}</span></div></div></div>`;
}
function cxInferReason(d) {
  const s = `${d.title || ""} ${d.memo || ""} ${(d.lines || []).map((l) => l.item + " " + (l.desc || "")).join(" ")}`;
  return /\b(code|DOB|inspector|egress|required by)\b/i.test(s)
    ? "code"
    : /\b(found|existing condition|unforeseen|hidden|concealed|rot|discovered|uncovered|behind the wall)\b/i.test(s)
      ? "unforeseen"
      : /\b(redesign|design change|revised drawing|drawings? (changed|revised))\b/i.test(s)
        ? "design"
        : "client";
}
function cxDesignFee(c, d) {
  const est = (c.estimates || []).find((e) => e.id === (d.fromDoc || d.retainerOf));
  if (!est) return "";
  const fee = docTotal(est).total,
    gross = (i) => r2(docTotal(i).sub - docTotal(i).disc + (+i.retainerApplied || 0)),
    before = c.invoices.filter((i) => i.id !== d.id && i.fromDoc === est.id && !["void", "draft"].includes(i.status) && (i.date || "") <= (d.date || "")),
    b = r2(before.reduce((a, i) => a + gross(i), 0)),
    me = gross(d);
  return `<div class="cxd-box sans cx-fee" style="font-size:11.5px"><b>Your design fee</b><div class="cxd-tot" style="width:auto;margin:4px 0 0"><div><span>Design fee in your agreement (${esc(est.number)})</span><span>${money(fee)}</span></div><div><span>Billed before this invoice</span><span>${money(b)}</span></div><div><span>This invoice${d.title ? ` (${esc(d.title)})` : ""}</span><span>${money(me)}</span></div><div class="big" style="font-size:12.5px"><span>Remaining after this invoice</span><span>${money(r2(fee - b - me))}</span></div></div></div>`;
}
function cxDocHtml(c, d, o) {
  o = o || {};
  const kind = cxKind(d),
    K = cxCo(d),
    re = cxStaffRe(c),
    t = docTotal(d),
    pr = cxProject(c, d),
    inv = "invoice" === d.type,
    bt = inv && "function" == typeof crBillTo ? crBillTo(c) : (c.contacts || []).find((x) => x.primary) || (c.contacts || [])[0] || {},
    paidOn = inv && "draft" !== d.status ? (c.payments || []).filter((p) => p.invoiceId === d.id && !p.unapplied).reduce((a, p) => a + (+p.amount || 0), 0) : 0,
    memo = cxClean(d.memo, c, re),
    terms = cxClean(d.terms, c, re),
    dates = [
      `Date: ${cxDate(d.date)}`,
      "progress" === kind ? `Work through: ${cxDate(d.date)}` : "",
      inv && d.due ? `Due: ${cxDate(d.due)}` : "",
      "estimate" === kind && d.validUntil ? `Valid until: ${cxDate(d.validUntil)}` : "",
      d.revisionOf ? `Revises ${esc(d.revisionOf)}` : "",
    ].filter(Boolean);
  let body = "";
  if ("progress" === kind) body = cxPayAppHtml(c, d, re);
  else if ("deposit" === kind && "sov" === d.mode)
    body = `<table><thead><tr><th class="n">#</th><th>Work</th><th class="r">Scheduled value</th><th class="r">Deposit</th><th class="r">Amount</th></tr></thead><tbody>${(d.lines || [])
      .filter((l) => l.sovId && +l.pct)
      .map((l, i) => `<tr><td class="n">${i + 1}</td><td>${esc(cxClean(l.item, c, re))}</td><td class="r">${money(l.scheduled)}</td><td class="r">${r2(+l.pct)}%</td><td class="r">${money(lineAmount(l, d))}</td></tr>`)
      .join("")}</tbody></table>${cxTotalsHtml(d, t, kind, paidOn)}`;
  else body = cxLinesHtml(c, d, re) + cxTotalsHtml(d, t, kind, paidOn);
  const exh = "co" === d.type && "function" == typeof coExhibits ? coExhibits(d) : [],
    foot = K.footers[kind] || "",
    sign = "estimate" === kind || "co" === kind;
  return `<!doctype html><html><head><meta charset="utf-8"><title>${esc(d.number)} · ${esc(K.name)}</title><style>body{margin:36px;background:#fff}${CX_CSS}@media print{body{margin:.45in}}</style></head><body><div class="cxd" data-cxkind="${kind}">${o.draft ? '<div class="cxd-draft">DRAFT · NOT SENT</div>' : ""}
  ${cxLetterhead(d)}
  <div class="cxd-hd"><div class="cxd-kind">${CX_LABEL[kind]}</div><div class="cxd-num sans"><b>${esc(d.number)}</b><br>${dates.join("<br>")}</div></div>
  <div class="cxd-meta"><div><div class="cxd-k sans">${inv ? "Bill to" : "Prepared for"}</div><b>${esc(c.name)}</b><br>${esc(cxBillAddr(c, d))}${bt && bt.name ? `<br><span class="sans" style="font-size:11.5px">${esc(bt.name)}${bt.email ? " · " + esc(bt.email) : ""}</span>` : ""}</div><div><div class="cxd-k sans">Project</div><b>${esc(pr.name)}</b>${pr.addr ? `<br>${esc(pr.addr)}` : ""}</div></div>
  ${pr.subj ? `<div class="cxd-subj">${esc(pr.subj)}</div>` : ""}
  ${body}
  ${"co" === kind ? cxCoBlock(c, d, re) : ""}${"design" === kind ? cxDesignFee(c, d) : ""}
  ${memo ? `<div class="cxd-memo"><b>${"estimate" === kind ? "Scope, allowances and exclusions" : "Notes"}</b>\n${esc(memo)}</div>` : ""}
  ${exh.length ? `<div class="cxd-memo"><b>Exhibits</b>\n${exh.map((x, i) => `${i + 1}. ${esc(cxClean(x.clientCaption || x.caption || "Photo", c, re))}, ${cxDate(x.date)}`).join("\n")}\nThe photos are in your client portal under Photos.</div>` : ""}
  ${terms && !("co" === kind && (c.sov || []).some((v) => "Contract" === v.source && (null == v.projectId || v.projectId === d.projectId))) ? `<div class="cxd-memo sans" style="font-size:12px"><b>${"estimate" === kind ? "Payment schedule" : "Payment terms"}:</b> ${esc(terms)}${inv && d.due ? `, due ${cxDate(d.due)}` : ""}.</div>` : ""}
  ${inv && t.total > 0.005 && d.status !== "paid" ? cxRemitHtml(c, d) : ""}
  ${sign ? `<p class="sans" style="font-size:11.5px;color:#4A5462;margin-top:22px">${"co" === kind ? "By signing, you approve this change order and the new contract sum above." : "By signing, you accept the scope, price and payment schedule in this proposal."}</p><div class="cxd-sig sans"><div>Accepted by ${esc(c.name)} · date</div><div>${esc(K.legal)} · date</div></div>` : ""}
  <div class="cxd-foot sans">${foot ? esc(foot) + "<br>" : ""}${esc(K.legal)}${K.addr ? " · " + esc(K.addr) : ""}${K.phone ? " · " + esc(K.phone) : ""}</div>
  </div>${o.print === !1 ? "" : "<script>window.onload=()=>{window.print();}<\/script>"}</body></html>`;
}

// ---- wiring: print, PDF, portal, mail -------------------------------------------------------------------------------
{
  const base = printDoc;
  printDoc = function (c, d, o) {
    if (!c || !d || !CX_TYPES.includes(d.type)) return base.apply(this, arguments);
    const html = cxDocHtml(c, d, o),
      w = window.open("", "_blank");
    w && w.document ? (w.document.write(html), w.document.close()) : toast("Allow pop-ups to print");
  };
}
if ("function" == typeof payAppData) {
  // an application's contract sum is as of its own date: a change order approved after it was sent is on the next one
  const base = payAppData;
  payAppData = function (c, d) {
    const A = base.apply(this, arguments);
    try {
      const coAmt = r2(cxAppCOs(c, d).reduce((a, x) => a + docNet(x), 0));
      if (Math.abs(coAmt - A.coAmt) > 0.005) {
        const revised = r2(A.orig + coAmt);
        Object.assign(A, { coAmt: coAmt, revised: revised, pctComplete: revised ? r2((A.completed / revised) * 100) : 0, balanceToFinish: r2(revised - A.completed) });
      }
    } catch (e) {}
    return A;
  };
}
if ("function" == typeof docSummaryHtml) {
  const base = docSummaryHtml;
  docSummaryHtml = function (c, d) {
    return base.call(this, c, cxClientCopy(c, d));
  };
}
if ("function" == typeof portalView) {
  // the portal's invoice: the same How to Pay as the printed invoice
  const base = portalView;
  portalView = function (c, k, d) {
    if ("invoice" !== k || !c || !d) return base.apply(this, arguments);
    const run = () => {
      const o = (clientFin(c).open || []).find((x) => x.x.id === d.id),
        bal = o ? o.bal : r2(docTotal(d).total - invoicePaid(c, d));
      mbModal(
        `Invoice ${esc(d.number)}`,
        `${docSummaryHtml(c, d)}${bal > 0.005 ? `<div class="card" style="margin-top:10px">${cxRemitHtml(c, d, "portal").replace('class="cxd-box cx-remit"', 'class="cx-remit small"')}<div class="small muted" style="margin-top:6px">Balance on this invoice: <b>${money(bal)}</b>${d.due ? ` · due ${cxDate(d.due)}` : ""}</div></div>` : '<div class="note ok" style="margin-top:10px">Paid in full. Thank you.</div>'}`,
        { submit: null, alt: bal > 0.005 ? { label: "Ask About This Invoice", run: () => (mbCloseModal(), setTimeout(() => portalQuestion(c, d), 60)) } : null },
      );
    };
    return "function" == typeof ljAsUser ? ljAsUser(run) : run();
  };
}
if ("function" == typeof crDocEmail) {
  const base = crDocEmail;
  crDocEmail = function (c, d) {
    const E = base.apply(this, arguments);
    try {
      const re = cxStaffRe(c);
      (E.subject = cxClean(E.subject, c, re) || E.subject), (E.body = String(E.body || "").split("\n").map((x) => (x.trim() ? cxClean(x, c, re) : x)).join("\n"));
    } catch (e) {}
    return E;
  };
}
if ("function" == typeof repStatement) {
  // the account statement on the same letterhead, with How to Pay and no contract boilerplate
  const base = repStatement;
  repStatement = function () {
    let h = base.apply(this, arguments);
    try {
      const c = (DB.clients || []).find((x) => x.id === repClient);
      if (!c) return h;
      DB.company.tc && (h = h.split(`<p class="small muted" style="margin-top:12px">${esc(DB.company.tc)}</p>`).join(""));
      h = `<style>${CX_CSS}</style><div class="cxd cx-stmt" style="max-width:none">${cxLetterhead(null)}</div>` + h + `<div class="cxd" style="max-width:none">${cxRemitHtml(c, null)}<div class="cxd-foot sans">${esc(cxCo().footers.invoice)}</div></div>`;
    } catch (e) {}
    return h;
  };
}

// ---- the gate on every action that reaches a client --------------------------------------------------------------------
{
  const base = docAction;
  docAction = async function (c, d, a) {
    if (c && d && CX_TYPES.includes(d.type)) {
      const out = ["send", "sendclient", "email"].includes(a),
        sign = ["approve", "approveconvert"].includes(a) && "invoice" !== d.type && !["approved", "converted", "billed"].includes(d.status);
      if (out || "print" === a || sign) {
        if ("sov" === d.mode && "draft" === d.status) {
          const add = cxEnsureCoLines(c, d);
          add.length && (save(), toast(`${add.join(", ")} added to ${d.number}: every approved change order bills on the application`, flowGo.doc(c, d.type, d)));
        }
        let R = cxGate(c, d);
        "draft" !== d.status && (R = R.filter((r) => "note" !== r.k));
        if (R.length) return void cxGateModal(c, d, R, "print" === a ? "print" : "send");
        if (out && "draft" === d.status) {
          CX_GENERIC_TITLE.test(d.title || "") && (d.lines || []).find((l) => l.item) && (d.title = cxClean((d.lines || []).find((l) => l.item).item, c));
          "co" === d.type && !d.reasonType && (d.reasonType = cxInferReason(d));
          // the due date the person saved stands: Send moved a saved 9/19 (a Saturday) to 9/21 without a word (round
          // one, TRIAGE class 7). Dates the app picks itself land on business days (cxDueFor, at newDoc).
        }
      }
    }
    return base.apply(this, arguments);
  };
}
if ("function" == typeof crSendToClient) {
  const base = crSendToClient;
  crSendToClient = async function (c, d) {
    if (c && d && "draft" === d.status) {
      "sov" === d.mode && cxEnsureCoLines(c, d);
      const R = cxGate(c, d);
      if (R.length) return void cxGateModal(c, d, R, "send");
    }
    return base.apply(this, arguments);
  };
}

// ---- where the documents are made: one terms source, due dates on business days, the app's notes off the client copy -----
if ("function" == typeof newDoc) {
  const base = newDoc;
  newDoc = function (c, kind, opts) {
    const d = base.apply(this, arguments);
    try {
      const o = opts || {},
        f = o.fields || {};
      if ("estimate" === kind && d.template && "simple" !== d.template && !f.terms && /progress invoices net 7/.test(d.terms || "")) {
        const n = cxTermsDays(DB.company.terms);
        d.terms = `Deposit due at signing; progress invoices net ${null != n ? n : 15}`;
      }
      "invoice" === kind && !f.due && d.date && (d.due = cxDueFor(d.date, d.terms));
      "function" == typeof docMark && docMark(d);
    } catch (e) {}
    return d;
  };
}
if ("function" == typeof progressPrefill) {
  const base = progressPrefill;
  progressPrefill = function (c, inv) {
    const r = base.apply(this, arguments);
    try {
      cxMoveMachine(inv);
    } catch (e) {}
    return r;
  };
}
if ("function" == typeof pgApply) {
  const base = pgApply;
  pgApply = function () {
    const out = base.apply(this, arguments);
    try {
      out && out.inv && (cxMoveMachine(out.inv), out.client && cxEnsureCoLines(out.client, out.inv));
    } catch (e) {}
    return out;
  };
}
{
  // a draft deleted before it is sent gives its number back (a Preview or a mistaken draft never leaves a gap)
  const base = nextNumber;
  nextNumber = function (kind) {
    const k = { estimate: "est", co: "co", invoice: "inv" }[kind],
      pool = (DB.company.cxFree || {})[k] || [];
    if (pool.length) return pool.sort().shift();
    return base.apply(this, arguments);
  };
}
{
  const base = docAction;
  docAction = async function (c, d, a) {
    const del = "del" === a && d && "draft" === d.status && !d.sentAt && d.number,
      num = d && d.number,
      k = d && { estimate: "est", co: "co", invoice: "inv" }[d.type],
      had = del && (c[{ estimate: "estimates", co: "changeOrders", invoice: "invoices" }[d.type]] || []).some((x) => x.id === d.id);
    const r = await base.apply(this, arguments);
    try {
      if (had && !(c[{ estimate: "estimates", co: "changeOrders", invoice: "invoices" }[d.type]] || []).some((x) => x.id === d.id)) {
        const seq = (DB.company.seq || {})[k] || 0,
          m = /-(\d+)$/.exec(num || ""),
          n = m ? +m[1] : 0,
          used = DB.clients.some((x) => [...(x.estimates || []), ...(x.changeOrders || []), ...(x.invoices || [])].some((y) => y.number === num));
        if (n && !used) n === seq ? (DB.company.seq[k] = seq - 1) : (((DB.company.cxFree = DB.company.cxFree || {})[k] = (DB.company.cxFree[k] || []).filter((x) => x !== num)).push(num));
        save();
      }
    } catch (e) {}
    return r;
  };
}

// ---- the editor: what blocks Send, the change order's reason, the evidence behind each percent ---------------------------
if ("function" == typeof renderDocEditor) {
  const base = renderDocEditor;
  renderDocEditor = function (c, d) {
    let h = base.apply(this, arguments);
    try {
      if (!c || !d || !CX_TYPES.includes(d.type)) return h;
      if ("draft" === d.status) {
        const R = cxGate(c, d);
        R.length &&
          (h = h.replace(
            '<div class="dochd">',
            `<div class="note warn no-doc-print cx-gate" style="margin-bottom:10px"><b>Not ready for the client.</b> ${R.map((r) => r.msg).join(" ")}${R.some((r) => r.fix) ? ' <button class="btn sm" data-cxfix="1">Move Notes to Internal</button>' : ""}</div><div class="dochd">`,
          ));
      }
      if ("co" === d.type) {
        const cur = d.reasonType || cxInferReason(d),
          sel = `<div class="f cx-reason"><label>Reason for the Change</label><select data-cxreason="1" ${"draft" === d.status ? "" : "disabled"}>${CX_REASONS.map(([v, l]) => `<option value="${v}" ${v === cur ? "selected" : ""}>${l}</option>`).join("")}</select></div>`;
        h = h.replace('<div class="f"><label>Schedule impact (working days)</label>', sel + '<div class="f"><label>Schedule impact (working days)</label>');
      }
      "sov" === d.mode &&
        (d.lines || []).forEach((l) => {
          if (!l.evidence) return;
          const a = h.indexOf(`<tr data-line="${l.id}">`);
          if (a < 0) return;
          const b = h.indexOf("</tr>", a);
          b > -1 && (h = h.slice(0, b + 5) + `<tr class="cx-ev no-doc-print"><td></td><td colspan="9"><span class="small muted" data-nocase>How we know (not printed): ${esc(l.evidence)}</span></td></tr>` + h.slice(b + 5));
        });
    } catch (e) {
      console.warn("client docs editor", e);
    }
    return h;
  };
}
const cxOpenDoc = () => {
  try {
    const c = DB.clients.find((x) => x.id === clientOpen),
      d = c && docOpen && findDoc(c, docOpen.kind, docOpen.id);
    return c && d ? { c, d } : null;
  } catch (e) {
    return null;
  }
};
document.addEventListener("change", (e) => {
  const s = e.target.closest && e.target.closest("[data-cxreason]");
  if (!s) return;
  const o = cxOpenDoc();
  if (!o) return;
  (o.d.reasonType = s.value), save(), toast(`${o.d.number}: reason set to ${(CX_REASONS.find((r) => r[0] === s.value) || [])[1] || s.value}`, flowGo.doc(o.c, o.d.type, o.d));
});
document.addEventListener("click", (e) => {
  const b = e.target.closest && e.target.closest("[data-cxfix]");
  if (b) {
    const o = cxOpenDoc();
    if (!o) return;
    e.preventDefault();
    const n = cxMoveTyped(o.c, o.d);
    save(), render(), toast(`${n} note${1 === n ? "" : "s"} moved to Internal Notes on ${o.d.number}`, flowGo.doc(o.c, o.d.type, o.d));
  }
  const p = e.target.closest && e.target.closest("[data-cxprev]");
  p && (e.preventDefault(), e.stopPropagation(), cxPreviewApplication(p.dataset.cxprev));
  const v = e.target.closest && e.target.closest("[data-cxview]");
  if (v) {
    e.preventDefault();
    const c = "function" == typeof clientUserOf ? clientUserOf() : null,
      [k, id] = v.dataset.cxview.split(":"),
      d = c && findDoc(c, k, id);
    d && portalView(c, k, d);
  }
}, !0);

// ---- Preview from the Billing Queue: the application as it would go, with no draft and no number used --------------------
function cxPreviewApplication(pid) {
  const p = DB.projects.find((x) => x.id === pid),
    c = p && DB.clients.find((x) => x.id === p.clientId);
  if (!c) return toast("No client on that job");
  const snap = JSON.stringify(c),
    seq = JSON.stringify(DB.company.seq || {}),
    free = JSON.stringify(DB.company.cxFree || {}),
    keep = { save: save, audit: audit, act: c.activity.length };
  let html = "",
    total = 0,
    number = "";
  try {
    (save = () => {}), (audit = () => {});
    const out = pgApply(pid);
    if (out && out.inv) (number = out.inv.number), (total = docTotal(out.inv).total), (html = cxDocHtml(c, Object.assign({}, out.inv, { number: "Preview" }), { draft: !0, print: !1 }));
  } catch (e) {
    console.warn("preview", e);
  } finally {
    (save = keep.save), (audit = keep.audit);
    const back = JSON.parse(snap);
    Object.keys(c).forEach((k) => delete c[k]), Object.assign(c, back), (DB.company.seq = JSON.parse(seq)), (DB.company.cxFree = JSON.parse(free));
  }
  if (!html) return toast("Nothing to preview on that job");
  mbModal(
    `Preview: ${esc(p.project.name)} application`,
    `<p class="small muted" style="margin:0 0 8px">This is what Draft would put on the application (${money(total)} after retainage). Nothing was saved and no invoice number was used${number ? ` (Draft would use ${esc(number)})` : ""}.</p><iframe class="cx-prev" title="Preview" style="width:100%;height:62vh;border:1px solid var(--line,#D9DDE3);background:#fff" srcdoc="${esc(html)}"></iframe>`,
    { submit: "Draft It", onSubmit: () => void setTimeout(() => rtbAct("app:" + pid), 0) },
  );
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      "billing" === view &&
        // a ready application, and one held because the job is billed ahead (lane 1): Preview shows what it would bill
        // before anyone decides, with no number and no draft
        document.querySelectorAll('[data-blact^="rtb:app:"], [data-blact^="held:ahead:"][data-blact$=":application"]').forEach((b) => {
          if (b.parentNode.querySelector("[data-cxprev]")) return;
          const a = b.dataset.blact,
            pid = /^rtb:app:/.test(a) ? a.slice(8) : a.split(":")[2];
          const x = document.createElement("button");
          (x.className = "btn sm"), (x.textContent = "Preview"), (x.dataset.cxprev = pid), (x.style.marginRight = "8px"), b.parentNode.insertBefore(x, b);
        });
    } catch (e) {}
    return r;
  };
}
if ("function" == typeof billingRows) {
  // a $0 draft is never offered as work to send: it says so, and what to do with it
  const base = billingRows;
  billingRows = function () {
    const R = base.apply(this, arguments);
    try {
      (R || []).forEach((r) => {
        "draft" === r.kind && Math.abs(+r.amount || 0) < 0.005 && ((r.why = "$0: nothing to bill on it, so it cannot be sent; delete it or add the work"), (r.needs = !1), (r.zero = !0));
      });
    } catch (e) {}
    return R;
  };
}

// ---- the portal: what the client signed, and every document in one place ----------------------------------------------------
function cxPortalDocs(c) {
  const P = new Set((DB.projects || []).filter((p) => p.clientId === c.id && (!S || p.id === S.id)).map((p) => p.id)),
    inScope = (d) => !d.projectId || P.has(d.projectId);
  return [
    ...(c.estimates || []).filter((d) => ["sent", "approved", "converted", "billed"].includes(d.status)),
    ...(c.changeOrders || []).filter((d) => ["sent", "approved", "billed"].includes(d.status)),
    ...(c.invoices || []).filter((d) => !["draft", "void"].includes(d.status)),
  ].filter(inScope);
}
const CX_WORD = { estimate: "Proposal", co: "Change order", invoice: "Invoice" };
if ("function" == typeof renderPortalApprovals) {
  const base = renderPortalApprovals;
  renderPortalApprovals = function () {
    const r = base.apply(this, arguments);
    try {
      const c = clientUserOf(),
        card = document.querySelector("#cl-approvals .cl-waiting");
      if (c && card && !card.querySelector(".cx-done")) {
        const td = today(),
          A = cxPortalDocs(c)
            .filter((d) => "invoice" !== d.type && (d.clientApproval || d.approvedOn) && dayDiff(d.approvedOn || (d.clientApproval.ts || "").slice(0, 10) || td, td) <= 30)
            .sort((a, b) => String(b.approvedOn || "").localeCompare(String(a.approvedOn || "")));
        A.length &&
          card.insertAdjacentHTML(
            "beforeend",
            `<div class="cx-done" style="margin-top:10px"><div class="small muted" style="text-transform:uppercase;letter-spacing:.04em">You Approved</div>${A.map((d) => `<div class="pa-row"><div class="pa-main"><b data-nocase>${esc(d.title || d.number)}</b><div class="small muted">${CX_WORD[d.type]} ${esc(d.number)} · approved${d.clientApproval && d.clientApproval.name ? " by " + esc(d.clientApproval.name) : ""} ${esc(cxDate(d.approvedOn || (d.clientApproval.ts || "").slice(0, 10)))}</div></div><b class="pa-amt">${money(docTotal(d).total)}</b><div class="pa-acts"><button class="btn sm" data-cxview="${d.type}:${d.id}">View</button></div></div>`).join("")}</div>`,
          );
      }
    } catch (e) {
      console.warn("portal approved", e);
    }
    return r;
  };
}
if ("function" == typeof renderClient) {
  const base = renderClient;
  renderClient = function () {
    const r = base.apply(this, arguments);
    try {
      const c = "client" === role() ? clientUserOf() : null,
        host = document.getElementById("cl-account");
      if (c && host && !host.querySelector(".cx-docs")) {
        const D = cxPortalDocs(c).sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")));
        D.length &&
          host.insertAdjacentHTML(
            "beforeend",
            `<div class="cx-docs" style="margin-top:10px"><b>Your Documents</b>${D.map((d) => {
              const st = "invoice" === d.type ? invoiceStatus(c, d) : d.status;
              return `<div class="chg"><span>${esc(d.number)}</span><a href="#" data-cxview="${d.type}:${d.id}" data-nocase>${esc(CX_WORD[d.type])}: ${esc(d.title || "")}</a> · ${money(docTotal(d).total)} · ${esc({ sent: "sent to you", approved: "approved", converted: "signed", billed: "billed", paid: "paid", partial: "part paid", overdue: "past due" }[st] || st)}</div>`;
            }).join("")}</div>`,
          );
      }
    } catch (e) {
      console.warn("portal documents", e);
    }
    return r;
  };
}

// ---- settings: the letterhead, how to pay and the footers, in one card ------------------------------------------------------
if ("function" == typeof renderProj) {
  const base = renderProj;
  renderProj = function () {
    const r = base.apply(this, arguments);
    try {
      const anchor = document.getElementById("co-save"),
        card = anchor && anchor.closest(".card");
      if (card && !document.getElementById("cx-card") && ["owner", "controller", "billing"].includes(role())) {
        const co = DB.company,
          R = co.remit || {},
          F = Object.assign({}, CX_FOOTERS, co.footers || {}),
          fld = (id, label, v, ph) => `<div class="f"><label>${label}</label><input id="${id}" value="${esc(v || "")}"${ph ? ` placeholder="${esc(ph)}"` : ""}></div>`;
        card.insertAdjacentHTML(
          "afterend",
          `<div class="card" id="cx-card" style="margin-bottom:14px"><h3>Client Documents: Letterhead and How to Pay</h3><p class="small muted" style="margin:0 0 8px">Every proposal, change order, invoice, pay application and statement prints from these. The legal name comes from the document's entity.</p>
          <div class="f2">${fld("cx-tag", "Tagline", co.tagline, "Design, build, SD Plumbing and SD Electric under one roof")}${fld("cx-web", "Website", co.web)}</div>
          <div class="f"><label>Licences (one per line)</label><textarea id="cx-lics" rows="3">${esc((co.lics || []).join("\n"))}</textarea></div>
          <div class="f2">${fld("cx-bank", "Bank Name", R.bank)}${fld("cx-last4", "Account Ending (Last 4 Only)", R.last4)}</div>
          <div class="f2">${fld("cx-payto", "Checks Payable To", R.payableTo, "the document's entity")}${fld("cx-mailto", "Checks Mailed To", R.mailTo, "the company address")}</div>
          ${Object.keys(CX_FOOTERS).map((k) => `<div class="f"><label>Footer: ${{ estimate: "Proposal", co: "Change Order", progress: "Pay Application", deposit: "Deposit Invoice", design: "Design Fee Invoice", invoice: "Invoice" }[k]}</label><input data-cxfoot="${k}" value="${esc(F[k])}"></div>`).join("")}
          <button class="btn" id="cx-save">Save Client Documents</button></div>`,
        );
        document.getElementById("cx-save").onclick = () => {
          const before = JSON.stringify({ t: co.tagline, l: co.lics, r: co.remit, f: co.footers });
          (co.tagline = document.getElementById("cx-tag").value.trim()),
            (co.web = document.getElementById("cx-web").value.trim()),
            (co.lics = document.getElementById("cx-lics").value.split("\n").map((x) => x.trim()).filter(Boolean)),
            (co.remit = { bank: document.getElementById("cx-bank").value.trim(), last4: document.getElementById("cx-last4").value.replace(/\D/g, "").slice(-4), payableTo: document.getElementById("cx-payto").value.trim(), mailTo: document.getElementById("cx-mailto").value.trim() }),
            (co.footers = Object.fromEntries([...document.querySelectorAll("[data-cxfoot]")].map((i) => [i.dataset.cxfoot, i.value.trim()])));
          try {
            audit("company", "company", "client-documents", before, JSON.stringify({ t: co.tagline, l: co.lics, r: co.remit, f: co.footers }), "letterhead, how to pay and footers");
          } catch (e) {}
          save(), toast("Client documents saved: every document prints from them now", () => ((view = "proj"), render()));
        };
      }
    } catch (e) {
      console.warn("client docs settings", e);
    }
    return r;
  };
}

// ---- boot: the firm's name, the letterhead, and the notes written before this onto client fields ---------------------------
function cxBoot() {
  const co = DB.company;
  if (!co) return;
  // the firm is SmartDesign (Alan): the old default "SmartDesigns" was the product's name, not the firm's
  "SmartDesigns" === co.name && (co.name = "SmartDesign");
  cxLetterSeed();
  if (co.__cxMoved !== CX_V) {
    (co.__cxMoved = CX_V),
      (DB.clients || []).forEach((c) => [...(c.estimates || []), ...(c.changeOrders || []), ...(c.invoices || [])].forEach((d) => cxMoveMachine(d, "boot")));
  }
}
if ("function" == typeof finishBoot) {
  const base = finishBoot;
  finishBoot = function () {
    const r = base.apply(this, arguments);
    try {
      cxBoot();
    } catch (e) {
      console.warn("client docs boot", e);
    }
    return r;
  };
}
