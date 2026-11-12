/* ---------------------------------------------------------------------------------------------------------------------
   fmnumbers: finished-material documents are numbered per job (Alan, 11-06).

   A materials-template invoice (d.template === "materials", the finished-material sheet fmWire draws) is numbered in
   its job's FM series with a short prefix from the job's address, so the number is unique across the firm:
   "121State-FM14". A materials estimate takes the same prefix and its own series: "121State-FME1". Every other
   document keeps the firm's sequence (INV-2026-039, EST-2026-015). The number is d.number, the one field every list,
   the PDF, Cmd-K, Ask, the reports, the QuickBooks export and the portal already print: one question, one number.

   Rules:
   - only a document made from now on (fmNew, stamped in newDoc) and still a draft that was never sent is numbered;
     a document's number never changes once it is sent, and existing documents keep theirs;
   - the series continues after the highest FM number the job already has anywhere: its Selections items (it.fm), its
     purchase orders (po.fm), invoices on the job numbered FM<n> (an import) or <prefix>-FM<n>, and the series' own
     counter: a voided number stays burned; a draft deleted before it was sent gives its number back (fmFree), so the
     client never sees FM3 then FM5;
   - the firm's INV or EST number the draft held is given back (the sequence keeps no gap), as a deleted draft's is;
   - the prefix is the house number and the street word ("121 State Street" → "121State"), from the job's address,
     else the client's property address, else the job's name; with none, the client's last name. It is set once per
     address (DB.company.fmPrefix), never re-derived, and a second address that gives the same prefix gets a letter;
   - the whole number is 21 characters or fewer (QuickBooks' invoice-number limit), with room for a revision ("-R9").
   A revision keeps its original's number with -R<n> (lkRevise); a credit memo is CM-.
   Suite: tests/fm_numbers_test.py.
--------------------------------------------------------------------------------------------------------------------- */
const FM_MAX = 21,
  FM_PREFIX_MAX = 11, // 11 + "-FME" + 3 digits + "-R9" = 21
  FM_DIR = /^(e|w|n|s|east|west|north|south)$/i,
  FM_NOT_NAME = /^(family|group|llc|inc|co|corp|trust|holdings|the|and|&)$/i;
const fmCap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : "");
function fmAddrKey(a) {
  return String(a || "")
    .split(/[,··]/)[0]
    .toLowerCase()
    .replace(/\bstreet\b/g, "st")
    .replace(/\bavenue\b/g, "ave")
    .replace(/\bplace\b/g, "pl")
    .replace(/\broad\b/g, "rd")
    .replace(/\s+/g, " ")
    .trim();
}
// "121 State Street" → "121State"; "200 E 66th St 9G" → "200E66th"; no house number → ""
function fmFromAddr(a) {
  const line = String(a || "").split(/[,··]/)[0].trim(),
    m = /^(\d+[A-Za-z]?)(?:-\d+)?\s+(.+)$/.exec(line);
  if (!m) return "";
  const words = m[2].split(/\s+/).map((w) => w.replace(/[^A-Za-z0-9]/g, "")).filter(Boolean);
  let dir = "";
  while (words.length > 1 && FM_DIR.test(words[0])) dir += words.shift().charAt(0).toUpperCase();
  const street = fmCap(words[0] || "");
  return street ? (m[1] + dir + street).slice(0, FM_PREFIX_MAX) : "";
}
function fmFromName(c) {
  const w = String((c && c.name) || "")
    .split(/\s+/)
    .map((x) => x.replace(/[^A-Za-z0-9]/g, ""))
    .filter((x) => x && !FM_NOT_NAME.test(x));
  return fmCap((w[w.length - 1] || "Client").toLowerCase()).slice(0, FM_PREFIX_MAX);
}
// the address a document is for, and the prefix that address carries (set once, unique across the firm)
function fmPrefixFor(c, d) {
  const p = d && d.projectId && (DB.projects || []).find((x) => x.id === d.projectId),
    cands = [p && p.project && p.project.addr, c && c.propertyAddr, p && p.project && p.project.name],
    addr = cands.find((a) => fmFromAddr(a)) || "",
    key = addr ? fmAddrKey(addr) : "client:" + ((c && c.id) || ""),
    base = addr ? fmFromAddr(addr) : fmFromName(c),
    reg = (DB.company.fmPrefix = DB.company.fmPrefix || {});
  const mine = Object.keys(reg).find((k) => reg[k] === key);
  if (mine) return mine;
  let pre = base,
    i = 0;
  while (reg[pre] && reg[pre] !== key) pre = base.slice(0, FM_PREFIX_MAX - 1) + "BCDEFGHJKLMNPQRSTUVWXYZ".charAt(i++);
  reg[pre] = key;
  return pre;
}
// the highest number already taken in a series: the counter, every document carrying the prefix, and the job's own
// FM marks (Selections, purchase orders, an imported "FM3" on one of its invoices)
function fmHighest(pre, kind, pid) {
  const tag = "estimate" === kind ? "FME" : "FM",
    rx = new RegExp(`^${pre.replace(/[^A-Za-z0-9]/g, "")}-${tag}(\\d+)(?:-R\\d+)?$`, "i"),
    bare = new RegExp(`^${tag}(\\d+)(?:-R\\d+)?$`, "i"),
    seq = ((DB.company.fmSeq || {})[pre] || {})[tag] || 0;
  let n = +seq || 0;
  const take = (s, r) => {
    const m = r.exec(String(s || "").trim());
    m && (n = Math.max(n, +m[1]));
  };
  (DB.clients || []).forEach((c) =>
    ["estimate" === kind ? "estimates" : "invoices"].forEach((k) =>
      (c[k] || []).forEach((x) => {
        take(x.number, rx);
        pid && x.projectId === pid && take(x.number, bare);
      }),
    ),
  );
  if ("estimate" !== kind && pid) {
    ((DB.sel && DB.sel.items) || []).forEach((it) => it.projectId === pid && take(it.fm, /^FM(\d+)$/i));
    (DB.pos || []).forEach((po) => po.projectId === pid && take(po.fm, /^FM(\d+)$/i));
  }
  return n;
}
// give back the firm-sequence number a draft held before it took its FM number (as clientdocs does for a deleted draft)
function fmGiveBack(kind, num) {
  const k = { estimate: "est", invoice: "inv" }[kind],
    m = /-(\d+)$/.exec(num || ""),
    n = m ? +m[1] : 0,
    seq = (DB.company.seq || {})[k] || 0,
    used = (DB.clients || []).some((x) => [...(x.estimates || []), ...(x.changeOrders || []), ...(x.invoices || [])].some((y) => y.number === num));
  if (!k || !n || used) return;
  n === seq ? (DB.company.seq[k] = seq - 1) : (((DB.company.cxFree = DB.company.cxFree || {})[k] = (DB.company.cxFree[k] || []).filter((x) => x !== num)).push(num));
}
function fmWants(d) {
  return !!(d && d.fmNew && "materials" === d.template && ["invoice", "estimate"].includes(d.type) && "draft" === d.status && !d.sentAt && !d.revisionOf && !d.creditMemo && !d.fmNumbered);
}
// number one document in its job's series; returns the number (or "" when the document keeps its own)
function fmAssign(c, d) {
  if (!fmWants(d) || !c) return "";
  const pre = fmPrefixFor(c, d),
    tag = "estimate" === d.type ? "FME" : "FM",
    top = fmHighest(pre, d.type, d.projectId),
    // a number a deleted, never-sent draft gave back is handed out first, so the client's series has no hole
    pool = (((DB.company.fmFree = DB.company.fmFree || {})[pre] = DB.company.fmFree[pre] || {})[tag] = (DB.company.fmFree[pre][tag] || []).filter((k) => k <= top && !fmTaken(pre, tag, k, d.projectId)).sort((a, b) => a - b)),
    n = pool.length ? pool.shift() : top + 1,
    num = `${pre}-${tag}${n}`;
  if (num.length > FM_MAX) return "";
  ((DB.company.fmSeq = DB.company.fmSeq || {})[pre] = DB.company.fmSeq[pre] || {})[tag] = Math.max(n, +DB.company.fmSeq[pre][tag] || 0);
  const was = d.number;
  (d.number = num), (d.fmNumbered = !0), (d.fmPrefix = pre);
  (c.activity || []).forEach((a) => a.text && was && a.text.includes(was) && /created/.test(a.text) && (a.text = a.text.split(was).join(num)));
  d.title && was && d.title.includes(was) && (d.title = d.title.split(was).join(num));
  fmGiveBack(d.type, was);
  try {
    audit(d.type, d.id, "numbered", { number: was }, { number: num }, `${num}: finished-material ${"estimate" === d.type ? "estimate" : "invoice"} ${n} for ${pre} (${was} given back to the firm's sequence)`);
  } catch (e) {}
  return num;
}
// A finished-material invoice line names the selection it bills (selId) and the purchase-order line that bought it
// (poId, poLineId), so the item table (lane P5) and the client's bill-back find the invoice from the item. The invoice
// from an estimate (invoiceFromEstimate) copied only the line's words and price: the source line's selId is taken
// from its fromLine key, and the order line from the job's orders that bought that selection. Only links are added;
// amounts, quantities and words are never touched, and a link a line already has is kept.
// Drafts only: a sent invoice is linked once, by the audited backfill (fmBackfill), never silently on a draw.
function fmLineLinks(d, o) {
  o = o || {};
  if (!d || "invoice" !== d.type || "materials" !== d.template || "void" === d.status) return 0;
  if ("draft" !== d.status && !o.backfill) return 0;
  let n = 0;
  (d.lines || []).forEach((l) => {
    const was = { selId: l.selId || "", poLineId: l.poLineId || "" };
    if (!l.selId && l.fromLine) {
      const [k, docId, lineId] = String(l.fromLine).split(":"),
        src = (DB.clients || []).flatMap((c) => ("co" === k ? c.changeOrders : c.estimates) || []).find((x) => x.id === docId),
        sl = src && (src.lines || []).find((x) => x.id === lineId);
      sl && sl.selId && ((l.selId = sl.selId), n++);
    }
    if (l.selId && !l.poLineId) {
      const P = (DB.pos || []).filter((po) => !["void", "cancelled", "draft"].includes(po.status) && (!d.projectId || !po.projectId || po.projectId === d.projectId));
      for (const po of P) {
        const pl = (po.lines || []).find((x) => x.selId === l.selId);
        if (pl) {
          (l.poId = po.id), (l.poLineId = pl.id), n++;
          break;
        }
      }
    }
    o.backfill &&
      (was.selId !== (l.selId || "") || was.poLineId !== (l.poLineId || "")) &&
      audit("invoice", d.id, "line-linked", was, { selId: l.selId || "", poId: l.poId || "", poLineId: l.poLineId || "" }, `${d.number} · ${d.status} · line "${l.item || ""}" linked to its selection and order line (links only; amounts unchanged)`);
  });
  return n;
}
// The one-time backfill for finished-material invoices already sent before lines carried their links: each link it
// adds writes an audit row; it runs once (DB.company.fmLinkBackfill) and never touches an amount.
function fmBackfill() {
  if (DB.company.fmLinkBackfill) return 0;
  let n = 0;
  (DB.clients || []).forEach((c) => (c.invoices || []).forEach((d) => "materials" === d.template && !["draft", "void"].includes(d.status) && (n += fmLineLinks(d, { backfill: !0 }))));
  DB.company.fmLinkBackfill = { at: appNowIso(), links: n };
  return n;
}
// a number in the series is taken while any document, selection or order on the job carries it
function fmTaken(pre, tag, k, pid) {
  const num = `${pre}-${tag}${k}`.toLowerCase(),
    bare = `${tag}${k}`.toLowerCase(),
    docs = (DB.clients || []).flatMap((c) => ("FME" === tag ? c.estimates : c.invoices) || []);
  if (docs.some((x) => String(x.number || "").toLowerCase().replace(/-r\d+$/, "") === num || (pid && x.projectId === pid && String(x.number || "").toLowerCase() === bare))) return !0;
  if ("FM" === tag && pid)
    return ((DB.sel && DB.sel.items) || []).some((it) => it.projectId === pid && String(it.fm || "").toLowerCase() === bare) || (DB.pos || []).some((po) => po.projectId === pid && String(po.fm || "").toLowerCase() === bare);
  return !1;
}
// every eligible draft, wherever it was made: a new document takes its template after newDoc in most paths
function fmSweep() {
  fmBackfill();
  (DB.clients || []).forEach((c) => (c.invoices || []).forEach((d) => "materials" === d.template && "draft" === d.status && fmLineLinks(d)));
  let n = 0;
  (DB.clients || []).forEach((c) =>
    [...(c.invoices || []), ...(c.estimates || [])].forEach((d) => {
      if (fmWants(d)) return void (fmAssign(c, d) && n++);
      // a draft moved off the materials template before it went out takes the firm's number; its FM number stays burned
      if (d.fmNumbered && "materials" !== d.template && "draft" === d.status && !d.sentAt) {
        const was = d.number;
        (d.number = nextNumber(d.type)), (d.fmNumbered = !1), (d.fmNew = !1);
        try {
          audit(d.type, d.id, "numbered", { number: was }, { number: d.number }, `${d.number}: no longer a finished-material document; ${was} stays burned`);
        } catch (e) {}
        n++;
      }
    }),
  );
  return n;
}
let fmHold = 0;
if ("function" == typeof newDoc) {
  const base = newDoc;
  newDoc = function (c, kind) {
    const d = base.apply(this, arguments);
    try {
      d && ["invoice", "estimate"].includes(kind) && (d.fmNew = !0);
      d && !fmHold && fmWants(d) && fmAssign(c, d);
    } catch (e) {}
    return d;
  };
}
// a revision keeps its original's number with -R<n>: it never draws a new FM number
if ("function" == typeof lkRevise) {
  const base = lkRevise;
  lkRevise = function () {
    fmHold++;
    try {
      return base.apply(this, arguments);
    } finally {
      fmHold--;
    }
  };
}
// docMark runs right after a path sets the template (invoiceFromEstimate, the materials sheet): number it there, so the
// toast and the activity line that follow already read the FM number
if ("function" == typeof docMark) {
  const base = docMark;
  docMark = function (d) {
    try {
      if (fmWants(d)) {
        const c = (DB.clients || []).find((x) => (x.invoices || []).includes(d) || (x.estimates || []).includes(d));
        c && fmAssign(c, d);
      }
      fmLineLinks(d);
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
// and before anything leaves: a draft goes out under its FM number, never under the number it was made with
if ("function" == typeof docAction) {
  const base = docAction;
  docAction = async function (c, d, a) {
    try {
      fmWants(d) && fmAssign(c, d);
    } catch (e) {}
    // a deleted draft that was never sent gives its FM number back, as the INV rule does; a void keeps it burned
    const del = "del" === a && d && d.fmNumbered && "draft" === d.status && !d.sentAt ? { num: d.number, pre: d.fmPrefix, tag: "estimate" === d.type ? "FME" : "FM", pid: d.projectId, coll: docColl(c, d.type) } : null;
    const r = await base.apply(this, arguments);
    try {
      if (del && !del.coll.includes(d)) {
        const m = new RegExp(`-${del.tag}(\\d+)$`).exec(del.num || ""),
          k = m ? +m[1] : 0,
          S0 = ((DB.company.fmSeq = DB.company.fmSeq || {})[del.pre] = DB.company.fmSeq[del.pre] || {}),
          F = (((DB.company.fmFree = DB.company.fmFree || {})[del.pre] = DB.company.fmFree[del.pre] || {})[del.tag] = DB.company.fmFree[del.pre][del.tag] || []);
        if (k && !fmTaken(del.pre, del.tag, k, del.pid)) {
          if (k === +S0[del.tag]) {
            S0[del.tag] = k - 1;
            while (F.includes(+S0[del.tag])) F.splice(F.indexOf(+S0[del.tag]), 1), (S0[del.tag] -= 1);
          } else F.includes(k) || F.push(k);
          audit(d.type, d.id, "number-given-back", { number: del.num }, null, `${del.num} deleted before it was sent: the number is handed out again`);
          save();
        }
      }
    } catch (e) {}
    return r;
  };
}
{
  const base = render;
  render = function () {
    try {
      fmSweep();
    } catch (e) {
      console.warn("fm numbers", e);
    }
    return base.apply(this, arguments);
  };
}
