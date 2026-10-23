/*<<subs.js>>*/
// ---- Subcontractors and the Payment Check (BACKLOG §1.10 item 1, §1.12; Alan, 2026-10-11) ---------------------------
// "Vendors are never overpaid: every payment checked before it leaves." Subs are the bigger money, and they need a
// subcontract with a schedule of values, retainage, papers on file, pay applications approved against work in place,
// and lien waivers with every payment.
//
// Design gate (BACKLOG §1.16): no new store, list or menu item.
//   - A subcontract is the purchase order (DB.pos, type "subcontract"). Its terms ride on the PO as `po.sc`
//     {scope, inclusions[], exclusions[], signedOn, signedBy, retainageAt, retainageOk, changes[]}; its schedule of
//     values is the PO's lines plus its approved changes (scSov). The one list stays Purchase Orders and the vendor.
//   - A sub's pay application is a bill (DB.bills) with `b.payApp` {no, periodTo, lines[{id, desc, scheduled, prevPct,
//     pct, measured}], revised, asClaimed}. It is approved where every bill is: Approvals, the PM first.
//   - A lien waiver is a row on the bill it covers, `b.waivers[]` {id, type conditional|unconditional, scope
//     progress|final, amount, through, received, by, at, note}; `b.waiver` stays the summary the older register reads.
//   - The Payment Check is a function (pcCheck), not a store. Its result is stamped on the payment it let through
//     (DB.payments[].check); a person's release of a hold is kept on the bill (`b.pcRel[]`, who, when, why).
//   - Holds wait in the one Approvals queue (kind "payhold": a held bill, or a bank change to verify by phone), routed
//     by DELEGATION. The bank change is the vendor's existing `bankPending`, now with who asked and the call-back.
//   - The per-vendor, per-job ledger is a read (scLedger), queryable as EQ_TABLES.vendorledger and in Ask.
// ------------------------------------------------------------------------------------------------------------------
const SC_DEF = { tolPts: 5, ownerAbove: 2500, bankWatchDays: 30, dupDays: 60 };
function scSet() {
  const c = (DB && DB.company) || {};
  return Object.assign({}, SC_DEF, c.payCheck || {});
}
const scLow = (s) => String(s || "").trim().toLowerCase(),
  scMe = () => {
    try {
      return (currentUser() || {}).name || (S && S.project && S.project.userName) || role();
    } catch (e) {
      return "someone";
    }
  },
  scVendor = (name) => (DB.vendors || []).find((v) => scLow(v.name) === scLow(name)) || null,
  scIsSubcontract = (po) => !!po && "subcontract" === po.type,
  scPOOf = (b) => (b && b.poId && (DB.pos || []).find((p) => p.id === b.poId)) || null,
  scProj = (id) => (DB.projects || []).find((p) => p.id === id) || null,
  scJob = (id) => {
    const p = scProj(id);
    return p ? String(p.project.name).replace(/ —.*$/, "") : "overhead";
  },
  scLive = (b) => !!b && !["void", "rejected", "draft"].includes(b.status),
  scPaidSt = (b) => ["paid", "verified"].includes(b.status),
  scT = (po) => (po && po.sc) || {},
  scDay = (d) => (d ? fmtL(String(d).slice(0, 10)) : "");
// a sub: said so on the vendor, else the trade or retainage (isSub), else a subcontract on file with them
function scIsSub(v) {
  if (!v) return !1;
  if ("sub" === v.kind) return !0;
  if ("supplier" === v.kind) return !1;
  try {
    if (isSub(v)) return !0;
  } catch (e) {}
  return (DB.pos || []).some((po) => scIsSubcontract(po) && scLow(po.vendor) === scLow(v.name));
}
// a payment to a sub for their work: the bill is on a subcontract, or coded to subs, from a vendor who is a sub
function scSubBill(b) {
  if (!b || b.ic) return !1;
  const v = scVendor(b.vendor);
  return !!v && scIsSub(v) && (scIsSubcontract(scPOOf(b)) || subBill(b));
}
const scChangesOk = (po) => (scT(po).changes || []).filter((c) => "approved" === c.status),
  scChangeTotal = (po) => r2(scChangesOk(po).reduce((a, c) => a + (+c.amount || 0), 0)),
  scContract = (po) => r2(poTotal(po).total + scChangeTotal(po));
// The schedule of values: the subcontract's lines, then each approved change as a line of its own.
function scSov(po) {
  if (!po) return [];
  const L = (po.lines || [])
    .filter((l) => l.item || l.desc || +l.price)
    .map((l) => ({ id: l.id, desc: l.item || l.desc || "", scheduled: r2((+l.qty || 0) * (+l.price || 0)), line: l.line || "", code: l.code || "", taskIds: l.taskIds || null }));
  scChangesOk(po).forEach((c) =>
    L.push({ id: c.id, desc: `${c.number}: ${c.desc}`, scheduled: r2(+c.amount || 0), line: c.line || (L[0] || {}).line || "", code: (L[0] || {}).code || "", taskIds: c.taskIds || null, change: !0 }),
  );
  return L;
}
// The site tasks a line of work is measured by: the ones named on the line; else, among the tasks of its estimate
// line, the ones its words name ("Parlor kitchen + laundry millwork" is "Millwork – parlor kitchen & laundry", not
// the whole millwork line); else any task its words name.
function scTasksFor(po, L) {
  const p = scProj(po && po.projectId);
  if (!p || !L) return [];
  const T = (p.tasks || []).filter((t) => "milestone" !== t.type);
  if (L.taskIds && L.taskIds.length) return T.filter((t) => L.taskIds.includes(t.id));
  const w = tpWords(L.desc),
    score = (t) => tpWords(t.name).filter((a) => w.some((b) => tpSame(a, b))).length;
  let pool = [];
  try {
    L.line && (pool = (tpLineTasks(p) || {})[L.line] || []);
  } catch (e) {}
  if (pool.length > 1) {
    const best = Math.max(...pool.map(score));
    best >= 2 && (pool = pool.filter((t) => score(t) === best));
  }
  if (!pool.length) {
    const best = T.length ? Math.max(...T.map(score)) : 0;
    best >= 2 && (pool = T.filter((t) => score(t) === best));
  }
  return pool;
}
// Work in place for a line: what the site measured (prgMeasure over its tasks), who measured it, when, and the
// photos filed against those tasks. basis "measured" only when someone measured; otherwise the % is the plan's.
function scMeasured(po, L) {
  const p = scProj(po && po.projectId),
    T = scTasksFor(po, L);
  if (!p || !T.length) return { pct: null, basis: "none", tasks: [], photos: 0 };
  let m = null;
  try {
    m = withProject(p, () => prgMeasure(T));
  } catch (e) {}
  if (!m) return { pct: null, basis: "none", tasks: [], photos: 0 };
  const last = m.measured && m.measured.last,
    ids = new Set(T.map((t) => t.id)),
    photos = (DB.photos || []).filter((ph) => ph.projectId === p.id && (ids.has(ph.taskId) || (ph.ref && ids.has(ph.ref.id)))).length;
  return {
    pct: r2(Math.max(0, Math.min(100, +m.pct || 0))),
    basis: m.measured ? "measured" : "unmeasured",
    by: last ? last.by || "" : "",
    on: last ? last.on || "" : "",
    src: last ? last.src || "" : "",
    note: last ? last.note || "" : "",
    photos: photos,
    tasks: T.map((t) => t.name),
    taskIds: T.map((t) => t.id),
  };
}
const scMeasuredWords = (M) =>
  !M || null == M.pct
    ? "no site task measures this line yet"
    : "measured" === M.basis
      ? `${Math.round(M.pct)}% in place, measured by ${M.by || "the site"} ${scDay(M.on)}${M.photos ? `, ${M.photos} photo${1 === M.photos ? "" : "s"}` : ""}`
      : `not measured on site yet (the plan says ${Math.round(M.pct)}%)`;
// ---- bills, billed and paid on a subcontract -----------------------------------------------------------------------
const scBillsOf = (po) => (DB.bills || []).filter((b) => b.poId === po.id && scLive(b));
// what one bill bills on each SOV line (gross): its lines that name the line; an unlinked bill on a one-line
// subcontract is that line's
function scBillByLine(b, po) {
  const out = {},
    sov = scSov(po),
    one = 1 === sov.length ? sov[0].id : "";
  (b.lines || []).forEach((l) => {
    const k = l.scLineId || l.poLineId || one || "_";
    out[k] = r2((out[k] || 0) + (+l.amount || 0));
  });
  return out;
}
// a deposit (a prepayment the terms allow, "50% deposit" on a shop's millwork) is not progress: it is applied as the
// work is billed, so it counts toward the contract but never as work claimed
const scIsDeposit = (b) => !!b && (!!b.deposit || /\bdeposit\b/i.test([b.notes || "", ...(b.lines || []).map((l) => l.desc || "")].join(" ")));
function scBilledToDate(po, exceptId, o) {
  const out = { _total: 0 };
  scBillsOf(po)
    .filter((b) => b.id !== exceptId && !b.retainageRelease && billGross(b) > 0 && !(o && o.progress && scIsDeposit(b)))
    .forEach((b) => {
      const m = scBillByLine(b, po);
      Object.keys(m).forEach((k) => ((out[k] = r2((out[k] || 0) + m[k])), (out._total = r2(out._total + m[k]))));
      // a difference held in dispute (approved at the PO amount, the rest disputed) is not billed until accepted
      out._total = r2(out._total - pcDisputed(b));
    });
  return out;
}
// what has left the firm for a bill, by any method and from any entity: its payments, and bank or card lines tied
// to it that no payment holds; a bill marked paid with neither is taken as paid in full
function scPaidBill(b) {
  const P = "function" == typeof payOfBill ? payOfBill(b) : [];
  let s = P.filter((p) => !p.credit).reduce((a, p) => a + (+p.amount || 0), 0);
  (DB.txns || []).filter((t) => t.billId === b.id && +t.amt < 0 && !P.some((p) => p.txnId === t.id)).forEach((t) => (s -= +t.amt));
  return r2(!s && scPaidSt(b) ? billTotal(b) : s);
}
const pcDisputed = (b) => ("function" == typeof pay3HeldCost ? +pay3HeldCost(b) || 0 : 0);
const scCreditsTaken = (b) => r2(((b && b.creditsTaken) || []).reduce((a, c) => a + (+c.amount || 0), 0));
// what is still to pay on a bill: its open amount less the vendor credits taken against it
const pcOpen = (b) => r2(Math.max(0, ("function" == typeof payOpen ? payOpen(b) : billTotal(b) - scPaidBill(b)) - scCreditsTaken(b)));
// ---- lien waivers: rows on the bill they cover -----------------------------------------------------------------------
function wvList(b) {
  if (!b) return [];
  if (Array.isArray(b.waivers) && b.waivers.length) return b.waivers;
  const w = b.waiver;
  return w && w.type ? [{ id: "legacy", type: w.type, scope: b.retainageRelease ? "final" : "progress", amount: billTotal(b), received: w.received || "", by: w.by || "", note: w.note || "", legacy: !0 }] : [];
}
// one covering waiver: an unconditional one answers a conditional need; a final need wants a final waiver
const wvHas = (b, type, scope, amount) =>
  wvList(b).some((w) => ("unconditional" === type ? "unconditional" === w.type : !0) && ("final" !== scope || "final" === w.scope) && (+w.amount || 0) >= (+amount || 0) - 1);
function wvSync(b) {
  const L = wvList(b),
    best = L.filter((w) => "unconditional" === w.type).pop() || L[L.length - 1];
  b.waiver = best ? { type: best.type, scope: best.scope, received: best.received, note: best.note || "", by: best.by || "" } : b.waiver;
}
function wvAdd(b, w) {
  if (!b || !w || !w.type) return null;
  Array.isArray(b.waivers) && b.waivers.length ? 0 : (b.waivers = wvList(b).map((x) => Object.assign({}, x)));
  const row = {
    id: uid("wv"),
    type: "unconditional" === w.type ? "unconditional" : "conditional",
    scope: "final" === w.scope ? "final" : "progress",
    amount: r2(+w.amount || 0),
    through: w.through || today(),
    received: w.received || today(),
    fileId: w.fileId || "",
    note: w.note || "",
    by: scMe(),
    at: appNowIso(),
  };
  b.waivers.push(row), wvSync(b);
  try {
    audit("bill", b.id, "waiver", "", `${row.type} ${row.scope} ${money(row.amount)}`, row.note);
  } catch (e) {}
  return row;
}
// prior payments to this sub on this job with no unconditional waiver back yet (the older rule, read from the rows)
const wvPriorMissing = (b) =>
  (DB.bills || []).filter(
    (x) => x.id !== b.id && scLow(x.vendor) === scLow(b.vendor) && x.projectId === b.projectId && billTotal(x) > 0 && (scPaidSt(x) || scPaidBill(x) > 0) && scSubBill(x) && !x.ic && !x.retainageRelease && !wvHas(x, "unconditional", "progress", Math.min(billTotal(x), scPaidBill(x) || billTotal(x))),
  );

// ---- the Payment Check -------------------------------------------------------------------------------------------
// Every payment, by any method, is checked before it leaves (BACKLOG §1.12). pcCheck(b, {amount, method}) answers
// {holds, ok, released}: each hold says what is off in plain words, the money at stake, the next step, the Standard
// line behind it, who may release it (owner, or the owner and the controller) and whether a release is allowed at
// all (a bank change is verified by a call-back, never released by a reason).
const PC_STD = {
  approval: { p: "cost", c: ["value", "dollar", /No money is committed/i] },
  self: { p: "integrity", c: ["principle", "integrity"] },
  bank: { p: "integrity", c: ["principle", "integrity"] },
  papers: { p: "law", c: ["pb", "office", "standards", /Insurance certificates/i] },
  w9: { p: "law", c: ["pb", "office", "actFrom", /Everything findable/i] },
  dup: { p: "cost", leak: !0, c: ["value", "dollar", /Waste nothing/i] },
  prior: { p: "cost", leak: !0, c: ["value", "dollar", /Waste nothing/i] },
  contract: { p: "cost", leak: !0, c: ["pb", "office", "never", /doesn't match a PO/i] },
  threeway: { p: "cost", leak: !0, c: ["pb", "office", "standards", /Three-way match/i] },
  work: { p: "cost", leak: !0, c: ["value", "dollar", /No money is committed/i] },
  retainage: { p: "cost", leak: !0, c: ["value", "dollar", /No money is committed/i] },
  waiver: { p: "law", c: ["principle", "law"] },
  credits: { p: "cost", leak: !0, c: ["value", "dollar", /Waste nothing/i] },
};
// a figure with cents keeps them ($812.40), a round one reads as dollars ($18,000)
const scM = (n) => (Math.abs((+n || 0) % 1) > 0.004 && "function" == typeof money2 ? money2(n) : money(n));
const pcWhy = (key) => {
  try {
    return standardWhy("pc:" + key) || "";
  } catch (e) {
    return "";
  }
};
const pcSig = (h) => `${h.key}|${Math.round(+h.money || 0)}`;
function pcReleasedBy(b, h) {
  return ((b && b.pcRel) || []).filter((r) => r.sig === pcSig(h)).pop() || null;
}
// the bank and card lines to this vendor that no bill, payment or order holds: a charge that may already have paid it
function pcLooseTxns(b, amounts) {
  const n = scLow(b.vendor).split(/\s+/)[0],
    from = iso(addDays(b.date || today(), -15)),
    to = iso(addDays(b.date || today(), 75)),
    held = new Set((DB.payments || []).map((p) => p.txnId).filter(Boolean));
  (DB.pos || []).forEach((po) => (po.matchedTxns || []).forEach((id) => held.add(id)));
  return (DB.txns || []).filter((t) => {
    if (!(+t.amt < 0) || t.billId || held.has(t.id) || t.retId) return !1;
    if (!t.date || t.date < from || t.date > to) return !1;
    const who = scLow(`${t.vendor || ""} ${t.desc || ""}`);
    if (!(n.length > 2 && who.includes(n))) return !1;
    return amounts.some((a) => a > 0 && Math.abs(Math.abs(+t.amt) - a) <= 1);
  });
}
function pcCheck(b, o) {
  o = o || {};
  const Z = scSet(),
    v = scVendor(b.vendor),
    po = scPOOf(b),
    sub = scSubBill(b),
    open = pcOpen(b),
    amt = r2(null != o.amount && "" !== o.amount ? +o.amount : open),
    method = o.method || b.payMethod || "ACH",
    me = o.by || scMe(),
    holds = [],
    ok = [],
    warn = [],
    H = (key, what, x) => holds.push(Object.assign({ key: key, what: what, money: 0, next: "", act: "", who: "any", fixed: !1 }, x || {})),
    K = (key, text) => ok.push({ key: key, text: text }),
    Wn = (key, text) => warn.push({ key: key, text: text }),
    // the owner's override of a compliance block at approval (the reason given then) stands for those papers here
    preFor = (re) => {
      const a = (b.approvals || []).filter((x) => "owner" === x.role && ("compliance override" === x.action || (/^override:/.test(x.note || "") && re.test(x.note || "")))).pop();
      return a ? { by: a.by || "the owner", why: String(a.note || "").replace(/^override:\s*/, "").replace(/\s*\(.*\)\s*$/, ""), at: a.ts || "" } : null;
    },
    pre = preFor(/insurance|COI|license/i),
    preW9 = preFor(/W-9/i);
  // approval and separation of duties
  ["approved", "verified", "paid"].includes(b.status)
    ? K("approval", `Approved${b.approvedAt ? " " + scDay(b.approvedAt) : ""}`)
    : H("approval", `Not approved for payment yet (${billState(b).text || b.status})`, { money: amt, fixed: !0, next: "Open the Bill", act: "open" });
  // a held bill and a bill the bank already paid are never paid from here (S1 fix, owner review 2026-10-21: both
  // paid-before-approval bills sat in the Payment Run, and a held bill showed no hold on its row)
  const hold = b.onHold && "open" === b.onHold.state ? b.onHold : null,
    paidAt = "function" == typeof billPaidTxn ? billPaidTxn(b) : null;
  hold && H("held", `Held by ${hold.by}: ${hold.why}`, { money: amt, fixed: !0, next: "Open the Bill", act: "open" });
  paidAt && !["paid", "verified"].includes(b.status) && H("paidbank", `Already paid: ${money(Math.abs(+paidAt.amt || 0))} left the bank on ${scDay(paidAt.date)}; paying it again would pay it twice`, { money: amt, fixed: !0, next: "Open the Bill", act: "open" });
  const createdBy = scLow(b.createdBy),
    vendorBy = scLow(v && v.createdBy);
  createdBy && createdBy === scLow(me)
    ? H("self", `${me} entered this bill: a second person releases its payment`, { money: amt, fixed: !0 })
    : vendorBy && vendorBy === scLow(me)
      ? H("self", `${me} set this vendor up: a second person releases its payments`, { money: amt, fixed: !0 })
      : K("self", "Released by someone who neither entered the bill nor set up the vendor");
  // the right account: the details on file, unchanged without the call-back
  if (v && v.bankPending) {
    const bp = v.bankPending;
    H("bank", `${v.name}'s bank details were asked to change ${bp.at ? scDay(bp.at) : bp.t || ""}${bp.by ? ` by ${bp.by}` : ""}${bp.via ? ` (${bp.via})` : ""}: every payment is held until someone other than ${bp.by || "the person who asked"} calls ${v.name} at the number on file`, {
      money: amt,
      fixed: !0,
      next: "Verify by Phone",
      act: "bank",
    });
  } else if (v && v.bankChangedAt && dayDiff(v.bankChangedAt, today()) <= Z.bankWatchDays && !(v.bankVerified && v.bankVerified.on >= v.bankChangedAt) && /ach|wire|zelle/i.test(method)) {
    H("bank", `${v.name}'s bank details changed ${scDay(v.bankChangedAt)} with no call-back on record: confirm by phone before money goes to the new account`, { money: amt, fixed: !0, next: "Verify by Phone", act: "bank" });
  } else if (v && /wire/i.test(method) && !(v.bank && v.bank.last4)) {
    H("bank", `No bank account on file for ${v.name}: a wire goes only to an account on file and confirmed by phone; pay by check instead`, { money: amt, fixed: !0, next: "Pay by Check", act: "check" });
  } else if (v && /ach|zelle/i.test(method) && !(v.bank && v.bank.last4)) {
    Wn("bank", `No bank account for ${v.name} on file here, so the account the bank pays is not checked: add it, confirmed by phone, so it is`);
  } else
    K(
      "bank",
      /check|card/i.test(method)
        ? `Paid by ${method.toLowerCase()}, not to a bank account`
        : v && v.bankVerified && v.bankChangedAt
          ? `Bank account ····${(v.bank || {}).last4 || ""}, changed ${scDay(v.bankChangedAt)} and confirmed by phone by ${v.bankVerified.by}`
          : `Bank account ····${((v && v.bank) || {}).last4 || ""}, unchanged`,
    );
  // papers: insurance, licence, W-9
  if (v) {
    const td = today(),
      need = sub || !!v.onSite;
    v.insuranceExp && v.insuranceExp < td
      ? H("papers", `${v.name}'s certificate of insurance expired ${scDay(v.insuranceExp)}`, { money: amt, who: "owner", next: "Request the COI", act: "coi", pre: pre })
      : !v.insuranceExp && need
        ? H("papers", `No certificate of insurance on file for ${v.name}`, { money: amt, who: "owner", next: "Request the COI", act: "coi", pre: pre })
        : K("papers", v.insuranceExp ? `Insurance current through ${scDay(v.insuranceExp)}` : "No certificate needed (not on site)");
    v.licenseExp && v.licenseExp < td && H("papers", `${v.name}'s license expired ${scDay(v.licenseExp)}`, { money: amt, who: "owner", key2: "license", pre: pre });
    !v.w9 && (sub || billTotal(b) >= 600)
      ? H("w9", `No W-9 on file for ${v.name}: the 1099 cannot be filed`, { money: amt, who: "owner", next: "Request the W-9", act: "w9", pre: preW9 })
      : K("w9", v.w9 ? "W-9 on file" : "No W-9 needed under $600");
  }
  // duplicates: the same invoice number, the same amount and date, the same pay application
  const num = scLow(b.number).replace(/[^a-z0-9]/g, ""),
    others = (DB.bills || []).filter((x) => x.id !== b.id && !["void", "rejected"].includes(x.status) && scLow(x.vendor) === scLow(b.vendor));
  const dn = num && others.find((x) => scLow(x.number).replace(/[^a-z0-9]/g, "") === num),
    da = !dn && others.find((x) => x.date === b.date && Math.abs(billGross(x) - billGross(b)) < 0.5 && billGross(b) > 0),
    dp = !dn && !da && b.payApp && others.find((x) => x.payApp && x.poId === b.poId && +x.payApp.no === +b.payApp.no);
  dn || da || dp
    ? H(
        "dup",
        dn
          ? `Same invoice number as ${dn.number} already on file (${billState(dn).text || dn.status}, ${scM(billGross(dn))})`
          : da
            ? `Same amount and date as ${da.number || "another bill"} from ${b.vendor} (${scM(billGross(da))}, ${scDay(da.date)})`
            : `Pay application ${b.payApp.no} on this subcontract is already on file as ${dp.number || "another bill"}`,
        { money: amt, next: "Compare the Two", act: "dup", other: (dn || da || dp).id },
      )
    : K("dup", "No other bill with this number, or this amount and date, or this pay application");
  // what was already paid on this bill, by any method and entity
  const paidHere = scPaidBill(b),
    loose = pcLooseTxns(b, [amt, billTotal(b), billGross(b)]);
  paidHere + amt > billTotal(b) - scCreditsTaken(b) + 0.5
    ? H("prior", `${scM(paidHere)} was already paid on this bill; ${scM(amt)} more would pay ${scM(r2(paidHere + amt - billTotal(b) + scCreditsTaken(b)))} over it`, { money: r2(paidHere + amt - billTotal(b) + scCreditsTaken(b)), who: "owner" })
    : loose.length
      ? H(
          "prior",
          `${loose
            .map((t) => {
              const a = (DB.accounts || []).find((x) => x.id === t.acct);
              return `a ${a && "card" === a.type ? "card charge" : "bank payment"} of ${scM(Math.abs(t.amt))} on ${scDay(t.date)}${a ? ` (${a.name}${a.last4 ? " ····" + a.last4 : ""})` : ""}`;
            })
            .join("; ")} may already have paid this bill: match it before paying again`,
          { money: r2(Math.abs(+loose[0].amt)), next: "Open Banking", act: "bank-lines" },
        )
      : K("prior", paidHere ? `${scM(paidHere)} paid before on this bill; this pays the rest` : "Nothing paid on this bill before, by any method or entity");
  // the contract: paid and billed to date never beyond the PO or subcontract plus approved changes without the owner
  if (po) {
    const C = scContract(po),
      billed = r2(scBilledToDate(po, b.id)._total + (b.retainageRelease ? 0 : Math.max(0, billGross(b) - pcDisputed(b)))),
      paidPO = r2(scBillsOf(po).reduce((a, x) => a + scPaidBill(x), 0) + (DB.txns || []).filter((t) => (po.matchedTxns || []).includes(t.id) && !t.billId).reduce((a, t) => a - +t.amt, 0)),
      signed = (b.approvals || []).some((a) => /approved as billed|over the po|over po|beyond the order/i.test(`${a.action || ""}`) && ("owner" === a.role || /owner/i.test(a.action || ""))),
      dep = scBillsOf(po).filter((x) => x.id !== b.id && /\bdeposit\b/i.test([x.notes || "", ...(x.lines || []).map((l) => l.desc || "")].join(" ")));
    billed > C + 0.5 && !signed
      ? H("contract", `Billed ${scM(billed)} to date against ${po.number}'s ${scM(C)}${scChangeTotal(po) ? " with its approved changes" : ""}: ${scM(r2(billed - C))} over${dep.length ? ` (a deposit of ${scM(dep.reduce((a, x) => a + billGross(x), 0))} was billed before: is it taken off this invoice?)` : ""}`, {
          money: r2(billed - C),
          who: "owner",
          next: "Open the PO",
          act: "po",
        })
      : paidPO + amt > C + 0.5
        ? H("contract", `Paid ${scM(paidPO)} on ${po.number} so far; ${scM(amt)} more is ${scM(r2(paidPO + amt - C))} beyond its ${scM(C)}`, { money: r2(paidPO + amt - C), who: "owner", next: "Open the PO", act: "po" })
        : K("contract", `${po.number}: ${scM(billed)} billed and ${scM(r2(paidPO + amt))} paid with this, of ${scM(C)}${signed ? " (the owner approved the bill as billed)" : ""}`);
    // three-way match for goods: the order, what was received, the invoice
    if (!scIsSubcontract(po) && "service" !== po.type) {
      const short = (b.lines || [])
        .filter((l) => l.poLineId)
        .map((l) => {
          const pl = (po.lines || []).find((x) => x.id === l.poLineId);
          if (!pl || !(+pl.price > 0)) return null;
          const billedQ = (+l.amount || 0) / +pl.price,
            got = +pl.received || 0;
          return billedQ > got + 0.01 ? { pl: pl, billedQ: billedQ, got: got, money: r2((billedQ - got) * +pl.price) } : null;
        })
        .filter(Boolean);
      const any = (po.lines || []).some((l) => +l.received > 0) || (po.receipts || []).length || ["received", "partial"].includes(po.status);
      // a difference already disputed (approved at the PO amount) is not billed past the delivery
      const shortMoney = r2(short.reduce((a, x) => a + x.money, 0) - pcDisputed(b));
      short.length && shortMoney > 0.5
        ? H("threeway", `Billed for more than was received: ${short.map((x) => `${x.pl.item || x.pl.desc} billed ${r2(x.billedQ)}, received ${x.got}`).join("; ")}`, { money: shortMoney, next: "Open the PO", act: "po" })
        : !any
          ? H("threeway", `Nothing has been received on ${po.number} yet: no delivery to match this invoice to`, { money: amt, next: "Open the PO", act: "po" })
          : K("threeway", `Three-way match: ${po.number}, the delivery and this invoice agree`);
    }
  } else if (b.projectId && !sub) {
    const pm = (b.approvals || []).some((a) => "pm" === a.role);
    pm ? K("contract", "No purchase order; the PM signed off on the bill") : H("contract", "No purchase order behind this bill, and no PM sign-off", { money: amt, next: "Open the Bill", act: "open" });
  }
  // work actually done, for subs: what is billed to date against what the site measured
  if (sub && po && scIsSubcontract(po) && !b.retainageRelease && amt > 0.005 && scIsDeposit(b)) K("work", "A deposit the terms allow, not progress: it is applied as the work is billed, within the contract");
  else if (sub && po && scIsSubcontract(po) && !b.retainageRelease && amt > 0.005) {
    const W = pcWorkAhead(b, po);
    W.rows.length
      ? H("work", `Paying ahead of work: ${W.rows.map((r) => `${r.desc} ${r.claimedWord}, ${r.measuredWord}`).join("; ")}, ${scM(W.ahead)} ahead`, { money: W.ahead, who: "any", next: "Approve at Measured", act: "work" })
      : K("work", W.words || "Work in place supports what is billed");
  }
  // retainage: held at the contract rate, released only at the milestone, with a final waiver
  // a retainage release names no PO (releaseRetainage): its subcontract is the sub's on the job
  const spo = po || (b.retainageRelease ? (DB.pos || []).find((x) => scIsSubcontract(x) && scLow(x.vendor) === scLow(b.vendor) && x.projectId === b.projectId) : null);
  if (sub && spo && scIsSubcontract(spo)) {
    const po = spo,
      rate = +po.retainagePct || 0;
    if (b.retainageRelease) {
      const p = scProj(b.projectId),
        pct = p ? tpJobPct(p) : 0,
        at = scT(po).retainageAt || "substantial completion";
      scT(po).retainageOk || pct >= 95
        ? K("retainage", `Retainage release: ${scJob(b.projectId)} at ${pct}%${scT(po).retainageOk ? `, released for payment by ${scT(po).retainageOk.by}` : ""}`)
        : H("retainage", `Retainage is released at ${at}; ${scJob(b.projectId)} is ${pct}% complete`, { money: amt, who: "owner", next: "Open the PO", act: "po" });
    } else if (rate > 0 && (+b.retainagePct || 0) < rate - 0.001 && !scIsDeposit(b)) {
      const should = r2((billGross(b) * (rate - (+b.retainagePct || 0))) / 100);
      H("retainage", `Retainage not held: ${po.number} holds ${rate}%, this bill holds ${+b.retainagePct || 0}%: ${scM(should)} should stay back until ${scT(po).retainageAt || "substantial completion"}`, {
        money: should,
        who: "owner",
        next: scPaidSt(b) || scPaidBill(b) > 0 ? "" : `Hold ${rate}%`,
        act: scPaidSt(b) || scPaidBill(b) > 0 ? "" : "retain",
      });
    } else rate > 0 ? K("retainage", `Retainage ${rate}% held: ${scM(r2(billGross(b) - billTotal(b)))} stays back`) : K("retainage", "No retainage on this subcontract");
  }
  // lien waivers: a conditional waiver for this payment, an unconditional one for each payment before it
  if (sub && amt > 0.005) {
    const final = !!b.retainageRelease,
      prior = wvPriorMissing(b),
      thisOk = wvHas(b, "conditional", final ? "final" : "progress", amt);
    prior.length
      ? H("waiver", `No unconditional lien waiver for the payment${prior.length > 1 ? "s" : ""} before: ${prior.map((x) => `${x.number || "a bill"} (${scM(scPaidBill(x) || billTotal(x))}, paid ${scDay(x.paidAt || x.date)})`).join(", ")}`, { money: r2(prior.reduce((a, x) => a + (scPaidBill(x) || billTotal(x)), 0)), who: "owner", next: "Record the Waiver", act: "waiver-prior", bills: prior.map((x) => x.id) })
      : K("waiver", "Every payment before has its unconditional waiver");
    thisOk
      ? K("waiver", `${final ? "Final" : "Progress"} waiver on file for ${scM(amt)}`)
      : H("waiver", `No ${final ? "final" : "conditional"} lien waiver for this payment of ${scM(amt)}: it comes in before or with the check`, { money: amt, who: "owner", next: "Record the Waiver", act: "waiver" });
  }
  // deposits and credits: an open vendor credit is taken before new money goes out
  const credits = pcOpenCredits(b);
  credits.length
    ? H("credits", `${b.vendor} has ${credits.length > 1 ? `${credits.length} open credits` : "an open credit"} of ${scM(r2(credits.reduce((a, c) => a + c.left, 0)))} (${credits.map((c) => c.b.number || "a credit memo").join(", ")}) not taken yet`, { money: r2(credits.reduce((a, c) => a + c.left, 0)), next: "Take the Credit", act: "credit" })
    : K("credits", scCreditsTaken(b) ? `${scM(scCreditsTaken(b))} of vendor credit taken off this bill` : "No open credit or deposit from this vendor");
  // a person's release of a hold, with a reason, stands for that hold at that amount
  const released = [],
    live = [];
  holds.forEach((h) => {
    const r = !h.fixed && (pcReleasedBy(b, h) || (h.pre ? Object.assign({ approval: !0 }, h.pre) : null));
    r ? released.push(Object.assign({}, h, { rel: r })) : live.push(h);
  });
  live.forEach((h) => (h.why = pcWhy(h.key)));
  return { bill: b, amount: amt, method: method, open: open, holds: live, released: released, ok: ok, warn: warn, pass: !live.length, at: appNowIso(), by: me, sub: sub };
}
// what a sub bill bills ahead of the work: each SOV line's claimed % to date (this bill's pay application, or what
// the bills to date add up to) against the % the site measured, beyond the tolerance
function pcWorkAhead(b, po) {
  const Z = scSet(),
    sov = scSov(po),
    before = scBilledToDate(po, b.id, { progress: !0 }),
    mine = scBillByLine(b, po),
    rows = [];
  let measuredAny = !1,
    words = "";
  sov.forEach((L) => {
    if (!(L.scheduled > 0)) return;
    const pa = b.payApp && (b.payApp.lines || []).find((x) => x.id === L.id),
      claimed = pa ? +pa.pct || 0 : r2((100 * ((before[L.id] || 0) + (mine[L.id] || 0))) / L.scheduled),
      M = scMeasured(po, L);
    if (null == M.pct || "measured" !== M.basis) return;
    measuredAny = !0;
    claimed > M.pct + Z.tolPts &&
      rows.push({
        id: L.id,
        desc: L.desc,
        claimed: claimed,
        measured: M.pct,
        money: r2(((claimed - M.pct) / 100) * L.scheduled),
        claimedWord: `${pa ? "claims" : "billed to"} ${Math.round(claimed)}%`,
        measuredWord: scMeasuredWords(M),
      });
  });
  words = measuredAny ? `Work in place supports what is billed (within ${Z.tolPts} points of what the site measured)` : "No site task measures this subcontract yet: the PM's approval stands for the work in place";
  return { rows: rows, ahead: r2(rows.reduce((a, r) => a + r.money, 0)), words: words };
}
// open vendor credits: a credit memo entered as a bill (a negative total), approved and not yet taken in full
function pcOpenCredits(b) {
  return (DB.bills || [])
    .filter((x) => x.id !== b.id && scLow(x.vendor) === scLow(b.vendor) && "approved" === x.status && billTotal(x) < -0.005)
    .map((x) => ({ b: x, left: r2(-billTotal(x) - ((x.takenBy || []).reduce((a, t) => a + (+t.amount || 0), 0))) }))
    .filter((c) => c.left > 0.005);
}
// who may release a hold: never the person it is about; the owner above the limit or when the hold says so
function pcCanRelease(b, h, amt) {
  if (!h || h.fixed) return !1;
  const r = role();
  if (!["owner", "controller"].includes(r)) return !1;
  if (scLow(b.createdBy) === scLow(scMe())) return !1;
  if ("owner" === h.who || (+amt || 0) > scSet().ownerAbove) return "owner" === r;
  return !0;
}
function pcRelease(b, h, why, amt) {
  if (!why || !String(why).trim()) return toast("Say why first"), !1;
  if (!pcCanRelease(b, h, amt))
    return toast(h.fixed ? "This hold is not released by a reason: do what it asks" : "owner" === h.who || amt > scSet().ownerAbove ? "Only the owner releases this hold" : "The owner or the controller releases a hold"), !1;
  const r = { key: h.key, sig: pcSig(h), what: h.what, why: String(why).trim(), by: scMe(), role: role(), at: appNowIso(), amount: r2(+amt || 0) };
  (b.pcRel = b.pcRel || []).push(r), (b.approvals = b.approvals || []).push({ t: nowStamp(), ts: appNowIso(), by: r.by, role: r.role, action: `payment hold released: ${h.key}`, note: r.why });
  try {
    audit("bill", b.id, "pay-hold-released", h.what, h.key, r.why);
  } catch (e) {}
  return save(), r;
}
// ---- the Payment Check on screen: a quiet tick list, or each hold with its difference and next step ----------------
function pcHtml(R, o) {
  o = o || {};
  if (!R) return "";
  const b = R.bill,
    tick = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg>',
    stop = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/></svg>';
  const holds = R.holds
      .map(
        (h, i) =>
          `<li class="pc-hold" data-pchold="${i}"><span class="pc-ic bad-t">${stop}</span><div class="pc-tx"><b>${esc(h.what)}</b>${+h.money ? `<span class="small">${money(h.money)} at stake</span>` : ""}${h.why ? `<span class="small muted">${esc(h.why)}${PC_STD[h.key] && PC_STD[h.key].leak ? ". " + esc(STD_WASTE) : ""}</span>` : ""}<span class="pc-acts">${h.act && h.next ? `<button type="button" class="btn sm" data-pcact="${esc(h.act)}" data-pci="${i}">${esc(h.next)}</button>` : ""}${!o.noRelease && pcCanRelease(b, h, R.amount) ? `<button type="button" class="btn sm ghost" data-pcrel="${i}">Release with a Reason</button>` : ""}</span></div></li>`,
      )
      .join(""),
    rel = R.released.map((h) => `<li class="pc-rel"><span class="pc-ic warn-t">${tick}</span><div class="pc-tx"><span>${esc(h.what)}</span><span class="small muted">${h.rel.approval ? "Overridden at approval" : "Released"} by ${esc(h.rel.by)}${h.rel.at ? " " + esc(scDay(h.rel.at)) : ""}: ${esc(h.rel.why)}</span></div></li>`).join(""),
    ok = R.ok.map((k) => `<li class="pc-ok"><span class="pc-ic ok-t">${tick}</span><span class="small">${esc(k.text)}</span></li>`).join(""),
    warn = (R.warn || []).map((k) => `<li class="pc-warn"><span class="pc-ic warn-t">${stop}</span><span class="small">${esc(k.text)}</span></li>`).join("");
  return `<div class="card pc-card ${R.pass ? "pc-pass" : "pc-held"}" data-pcbill="${esc(b.id)}"><div class="pc-hd"><h4>Payment Check</h4><span class="pill ${R.pass ? "ok" : "bad"}">${R.pass ? `Checked · ${R.ok.length + R.released.length} Points` : `Held · ${R.holds.length}`}</span></div><div class="small muted pc-sub">${R.pass ? `${money(R.amount)} to ${esc(b.vendor)} by ${esc(R.method)} passes every check.` : `${money(R.amount)} to ${esc(b.vendor)} does not leave until ${R.holds.length > 1 ? "these are" : "this is"} cleared.`}</div>${holds ? `<ul class="pc-list">${holds}</ul>` : ""}${rel ? `<ul class="pc-list">${rel}</ul>` : ""}${warn ? `<ul class="pc-list">${warn}</ul>` : ""}<details class="pc-more"${R.pass && !o.closed ? " open" : ""}><summary class="small">What Was Checked (${R.ok.length})</summary><ul class="pc-list">${ok}</ul></details></div>`;
}
// the buttons on a check card, wherever it is drawn (the bill, the pay sheet, the run)
function pcWire(el, b, R, again) {
  if (!el || !b || !R) return;
  el.querySelectorAll("[data-pcrel]").forEach(
    (x) =>
      (x.onclick = (e) => {
        e.preventDefault();
        const h = R.holds[+x.dataset.pcrel];
        h &&
          billAskWhy(
            `Release the Hold — ${esc(b.vendor)} ${esc(b.number || "")}`,
            `${esc(h.what)}${+h.money ? ` · ${money(h.money)} at stake` : ""}`,
            "Release the Hold",
            "e.g. the vendor's corrected invoice is in hand; credit memo CM-114 covers the difference",
            (why) => {
              const r = pcRelease(b, h, why, R.amount);
              r && (render(), rcToast(`Hold released on ${b.vendor} ${b.number || ""} by ${r.by}: ${r.why}`, [{ label: "Open", run: () => flowGo.bill(b)() }]), again && setTimeout(again, 40));
            },
          );
      }),
  );
  el.querySelectorAll("[data-pcact]").forEach(
    (x) =>
      (x.onclick = (e) => {
        e.preventDefault();
        pcDo(b, R.holds[+x.dataset.pci], R, again);
      }),
  );
}
// a hold's next step
function pcDo(b, h, R, again) {
  if (!h) return;
  const v = scVendor(b.vendor),
    po = scPOOf(b);
  switch (h.act) {
    case "bank":
      return v ? scCallBackSheet(v) : null;
    case "check":
      return (b.payMethod = "Check"), save(), again ? again() : render();
    case "waiver":
      return wvSheet(b, { amount: R.amount, scope: b.retainageRelease ? "final" : "progress", type: "conditional", after: again });
    case "waiver-prior": {
      const x = (DB.bills || []).find((y) => y.id === (h.bills || [])[0]);
      return x ? wvSheet(x, { amount: scPaidBill(x) || billTotal(x), type: "unconditional", after: again }) : null;
    }
    case "retain": {
      if (!po) return;
      const was = +b.retainagePct || 0;
      b.retainagePct = +po.retainagePct || 0;
      (b.approvals = b.approvals || []).push({ t: nowStamp(), ts: appNowIso(), by: scMe(), role: role(), action: `retainage set to ${b.retainagePct}% (the subcontract's rate)`, note: `was ${was}%` });
      try {
        audit("bill", b.id, "retainage", `${was}%`, `${b.retainagePct}%`, po.number);
      } catch (e) {}
      save(), render();
      rcToast(`${b.number || "The bill"}: ${b.retainagePct}% retainage held, ${money(r2(billGross(b) - billTotal(b)))} stays back; ${money(billTotal(b))} payable`, [{ label: "Open", run: () => flowGo.bill(b)() }]);
      return again && setTimeout(again, 40);
    }
    case "credit":
      return pcTakeCredits(b, again);
    case "work":
      return scPayAppReview(b);
    case "po":
      return po && flowCan("po") ? (mbCloseModal(), "function" == typeof closeEditor && closeEditor(), flowGo.po(po)()) : toast(`${po ? po.number : "The order"} is on Purchase Orders`);
    case "dup": {
      const x = (DB.bills || []).find((y) => y.id === h.other);
      return x && (mbCloseModal(), "function" == typeof closeEditor && closeEditor(), flowGo.bill(x)());
    }
    case "bank-lines":
      return mbCloseModal(), "function" == typeof closeEditor && closeEditor(), flowCan("bank") ? ((view = "bank"), render()) : toast("Banking holds the bank and card lines");
    case "coi":
    case "w9":
      return scPaperRequest(v, h.act);
    case "open":
      return mbCloseModal(), flowGo.bill(b)();
  }
}
// take an open vendor credit off a bill before paying it (approved credits only; the GL already holds the credit,
// so taking it moves no money: the bill's payment is that much smaller and the credit is used up)
function pcTakeCredits(b, again) {
  const C = pcOpenCredits(b);
  if (!C.length) return toast("No open credit from this vendor");
  let left = pcOpen(b),
    took = 0;
  C.forEach((c) => {
    if (left <= 0.005) return;
    const a = r2(Math.min(left, c.left));
    (b.creditsTaken = b.creditsTaken || []).push({ billId: c.b.id, number: c.b.number || "", amount: a, by: scMe(), at: appNowIso() });
    (c.b.takenBy = c.b.takenBy || []).push({ billId: b.id, number: b.number || "", amount: a, by: scMe(), at: appNowIso() });
    -billTotal(c.b) - c.b.takenBy.reduce((s, t) => s + (+t.amount || 0), 0) <= 0.005 && ((c.b.status = "paid"), (c.b.paidAt = today()));
    (c.b.approvals = c.b.approvals || []).push({ t: nowStamp(), ts: appNowIso(), by: scMe(), role: role(), action: `credit of ${money(a)} taken on ${b.number || "a bill"}` });
    (left = r2(left - a)), (took = r2(took + a));
    try {
      audit("bill", b.id, "credit-taken", "", `${c.b.number || c.b.id} ${money(a)}`, "");
    } catch (e) {}
  });
  (b.approvals = b.approvals || []).push({ t: nowStamp(), ts: appNowIso(), by: scMe(), role: role(), action: `vendor credit of ${money(took)} taken before payment` });
  pcOpen(b) <= 0.005 && scPaidBill(b) + scCreditsTaken(b) >= billTotal(b) - 0.005 && ((b.status = "paid"), (b.paidAt = today()));
  save(), render();
  rcToast(`${money(took)} of ${b.vendor}'s credit taken off ${b.number || "the bill"}: ${money(pcOpen(b))} left to pay`, [{ label: "Open", run: () => flowGo.bill(b)() }]);
  again && setTimeout(again, 40);
}

// ---- recording a payment: the one path every payment of a bill takes ---------------------------------------------
// The check runs on the amount and method entered; a held payment is refused with what holds it. The result is
// stamped on the payment, so the record says what was checked and who released what.
function pcRecord(b, f, o) {
  o = o || {};
  const amt = r2(+f.amount || 0),
    ent = b.entityId || entDefault(),
    R = pcCheck(b, { amount: amt, method: f.method });
  if (!amt || amt < 0) return { err: "An amount" };
  if (amt > pcOpen(b) + 0.005) return { err: `Only ${money(pcOpen(b))} is open on this bill` };
  if (!R.pass) return { err: `Held: ${R.holds.map((h) => h.what).join("; ")}`, R: R };
  if (!entOwnsAccount(ent, f.acct)) return { err: "That account belongs to another entity" };
  if ("function" == typeof glLocked && glLocked(f.date, ent, "ap")) return { err: `${String(f.date).slice(0, 7)} is locked for AP — date the payment in an open period` };
  const by = scMe(),
    p = {
      id: uid("pay"),
      billId: b.id,
      entityId: ent,
      vendor: b.vendor,
      date: f.date,
      amount: amt,
      acctId: f.acct,
      method: f.method,
      ref: f.ref || "",
      txnId: "",
      by: by,
      at: appNowIso(),
      run: o.run || "",
      check: { at: R.at, by: by, pass: !0, checked: R.ok.map((k) => k.text), released: R.released.map((h) => ({ key: h.key, what: h.what, by: h.rel.by, why: h.rel.why })) },
    };
  payInit().push(p), (b.payMethod = f.method);
  if (pcOpen(b) <= 0.005) {
    (b.status = "paid"), (b.paidAt = f.date), (b.approvals = b.approvals || []).push({ t: nowStamp(), ts: appNowIso(), by: by, role: role(), action: `payment released (${f.method}${f.ref ? " " + f.ref : ""}), payment check passed` });
    try {
      audit("bill", b.id, "paid", null, { paidAt: f.date, acct: f.acct, amount: amt, check: R.ok.length });
    } catch (e) {}
    try {
      log(`Payment released: ${b.vendor} ${money(amt)} (${f.method}), payment check passed`);
    } catch (e) {}
  } else {
    (b.approvals = b.approvals || []).push({ t: nowStamp(), ts: appNowIso(), by: by, role: role(), action: `partial payment ${money(amt)} (${f.method}), payment check passed` });
    try {
      audit("bill", b.id, "partial-payment", null, { amount: amt, acct: f.acct });
    } catch (e) {}
  }
  return { p: p, R: R };
}
// The pay sheet: the check first, then where the money comes from. Replaces "Pay bill": every payment of a bill
// goes through it (the bill's Pay button, Approvals, the payment run's single rows).
function pcPaySheet(billId, o) {
  const b = (DB.bills || []).find((x) => x.id === billId || x === billId);
  if (!b) return;
  payInit();
  const ent = b.entityId || entDefault(),
    accts = entAccountsOf(ent);
  if (!accts.length) return void toast(`${glEntName ? glEntName(ent) : ent} has no bank or card account — add one under Settings › Company`);
  o = o || {};
  const amt0 = null != o.amount && "" !== o.amount ? o.amount : pcOpen(b),
    method0 = o.method || b.payMethod || "ACH",
    R = pcCheck(b, { amount: amt0, method: method0 }),
    // after a hold's step (a credit taken, a waiver recorded) the sheet opens again on what is open now
    again = () => pcPaySheet(b.id, { amount: null != o.amount && +o.amount <= pcOpen(b) ? o.amount : null, method: b.payMethod || method0 });
  const m = mbModal(
    "Pay Bill",
    `<div class="small muted" style="margin-bottom:8px">Bill ${esc(b.number || b.id)} · ${esc(b.vendor)} · ${esc(glEntName(ent))} · ${money(billTotal(b))}${+b.retainagePct ? ` net of ${b.retainagePct}% retainage` : ""}${scPaidBill(b) ? ` · ${money(scPaidBill(b))} paid before` : ""}${scCreditsTaken(b) ? ` · ${money(scCreditsTaken(b))} credit taken` : ""} · ${money(pcOpen(b))} open</div>${pcHtml(R, { closed: !0 })}
    <div class="grid2">${mbF("From Account", mbSel("acct", accts.map((a) => [a.id, `${a.name}${a.last4 ? " ····" + a.last4 : ""}`]), accts[0].id))}${mbF("Date", mbIn("date", today(), "", "date"))}</div>
    <div class="grid2">${mbF("Amount", mbIn("amount", String(amt0), "", "number"))}${mbF("Method", mbSel("method", ["ACH", "Check", "Card", "Wire", "Zelle"], method0))}</div>
    ${mbF("Reference (Check Number, Confirmation)", mbIn("ref", "", "optional"))}
    <p class="small muted">The check runs again on the amount and method you enter. The bank line that clears this payment is matched to it.</p>`,
    {
      submit: R.pass ? "Record Payment" : "Check Again",
      onSubmit: (f) => {
        const C = pcCheck(b, { amount: +f.amount || 0, method: f.method });
        if (!C.pass) return setTimeout(() => pcPaySheet(b.id, { amount: +f.amount || 0, method: f.method }), 0), C.holds.length && toast(`Held: ${C.holds[0].what}`), !0;
        const out = pcRecord(b, f);
        if (out.err) return toast(out.err), !1;
        save(), "function" == typeof closeEditor && closeEditor(), render();
        rcToast(`${money(out.p.amount)} to ${b.vendor} recorded, payment check passed${pcOpen(b) > 0.005 ? ` · ${money(pcOpen(b))} still open` : ""}`, [{ label: "Open", run: () => flowGo.bill(b)() }]);
      },
    },
  );
  m && m.classList.add("pc-sheet"), pcWire(m, b, R, again);
  return m;
}

// ---- lien waivers: record one ------------------------------------------------------------------------------------
function wvSheet(b, o) {
  o = o || {};
  const final = !!b.retainageRelease || "final" === o.scope,
    paid = scPaidBill(b);
  mbModal(
    `Lien Waiver — ${esc(b.vendor)} ${esc(b.number || "")}`,
    `<p class="small muted" style="margin:0 0 8px">${paid ? `${money(paid)} paid on this bill.` : `${money(pcOpen(b))} to pay on this bill.`} A conditional waiver comes in before or with the check; the unconditional one once it clears.</p>
    <div class="grid2">${mbF("Type", mbSel("type", [["conditional", "Conditional (With the Check)"], ["unconditional", "Unconditional (After It Clears)"]], o.type || (paid ? "unconditional" : "conditional")))}${mbF("Scope", mbSel("scope", [["progress", "Progress Payment"], ["final", "Final Payment"]], final ? "final" : "progress"))}</div>
    <div class="grid2">${mbF("Amount", mbIn("amount", String(r2(o.amount || paid || pcOpen(b) || billTotal(b))), "", "number"))}${mbF("Work Through", mbIn("through", (b.payApp && b.payApp.periodTo) || b.date || today(), "", "date"))}</div>
    ${mbF("Received", mbIn("received", today(), "", "date"))}${mbF("Note or File Reference", mbIn("note", "", "e.g. signed PDF in the job's documents"))}`,
    {
      submit: "Record the Waiver",
      onSubmit: (f) => {
        if (!(+f.amount > 0)) return toast("The amount the waiver covers"), !1;
        const w = wvAdd(b, f);
        save(), render();
        rcToast(`${w.type === "unconditional" ? "Unconditional" : "Conditional"} ${w.scope} waiver from ${b.vendor} for ${money(w.amount)} recorded on ${b.number || "the bill"}`, [{ label: "Open", run: () => flowGo.bill(b)() }]);
        o.after && setTimeout(o.after, 40);
      },
    },
  );
}
function wvHtml(b) {
  if (!scSubBill(b)) return "";
  const L = wvList(b),
    need = b.retainageRelease ? "final" : "progress";
  return `<div class="card wv-card"><div class="pc-hd"><h4>Lien Waivers</h4><button type="button" class="btn sm" data-wvadd="${esc(b.id)}">Record a Waiver</button></div>${
    L.length
      ? `<table class="t wv-t"><tbody>${L.map((w) => `<tr><td>${esc(w.type === "unconditional" ? "Unconditional" : "Conditional")} · ${esc(w.scope)}</td><td class="money">${money(w.amount)}</td><td class="small muted">${esc(scDay(w.received))}${w.by ? " · " + esc(w.by) : ""}${w.note ? " · " + esc(w.note) : ""}</td></tr>`).join("")}</tbody></table>`
      : `<div class="small muted">None on file. A ${need === "final" ? "final" : "conditional progress"} waiver comes in before or with this payment; the unconditional one after it clears.</div>`
  }</div>`;
}

// ---- the bank change: held until someone other than the requester calls the vendor at the number on file ----------
function scBankRequest(v, o) {
  const prev = v.bankPending;
  v.bankPending = { name: o.name || "", last4: String(o.last4 || "").slice(-4), t: nowStamp(), at: appNowIso(), by: scMe(), via: o.via || "entered here", phoneOnFile: v.phone || "" };
  try {
    audit("vendor", v.id, "bank-change-requested", v.bank, v.bankPending, o.via || "");
  } catch (e) {}
  save();
  return prev;
}
function scCallBackSheet(v) {
  const bp = v.bankPending,
    me = scMe();
  if (!bp && !(v.bankChangedAt && !(v.bankVerified && v.bankVerified.on >= v.bankChangedAt))) return toast(`${v.name}'s bank details are not waiting on a call-back`);
  if (!["owner", "controller"].includes(role())) return toast("The owner or the controller makes the call-back");
  if (bp && scLow(bp.by) === scLow(me)) return toast(`${me} asked for this change: someone else makes the call-back`);
  const phone = (bp && bp.phoneOnFile) || v.phone || "";
  mbModal(
    `Verify by Phone — ${esc(v.name)}`,
    `<div class="note warn small">Call ${esc(v.name)} at the number on file from before the request${phone ? `: <b>${esc(phone)}</b>` : ""}. Never a number from the email or letter that asked for the change. Ask them to read the new account's last four back to you.</div>
    ${bp ? `<p class="small">Asked ${esc(scDay(bp.at) || bp.t || "")} by ${esc(bp.by || "")}${bp.via ? ` (${esc(bp.via)})` : ""}: ${esc(bp.name || "a bank")} ····${esc(bp.last4 || "")}${v.bank && v.bank.last4 ? `, replacing ····${esc(v.bank.last4)}` : ""}.</p>` : ""}
    <div class="grid2">${mbF("Number Called", mbIn("phone", phone, "the number on file"))}${mbF("Spoke With", mbIn("spoke", v.contact || "", "name and role"))}</div>
    ${mbF("Last Four They Read Back", mbIn("last4", "", "e.g. 4471"))}`,
    {
      submit: "Confirmed: Apply the New Account",
      alt: bp ? { label: "They Did Not Ask: Reject", run: () => scBankReject(v) } : null,
      onSubmit: (f) => {
        if (!f.phone) return toast("The number you called"), !1;
        if (!f.spoke) return toast("Who you spoke with"), !1;
        const want = bp ? bp.last4 : (v.bank || {}).last4;
        if (String(f.last4 || "").slice(-4) !== String(want || "")) return toast(`They read back ····${f.last4 || "nothing"}, the request says ····${want}: do not apply it; reject the change`), !1;
        const before = Object.assign({}, v.bank || {});
        bp && ((v.bank = { name: bp.name, last4: bp.last4 }), (v.bankChangedAt = today()));
        v.bankVerified = { by: me, role: role(), on: today(), at: appNowIso(), phone: f.phone, spokeWith: f.spoke, requestedBy: bp ? bp.by : "" };
        (v.bankLog = v.bankLog || []).push({ from: before, to: Object.assign({}, v.bank), requestedBy: bp ? bp.by : "", via: bp ? bp.via : "", verifiedBy: me, phone: f.phone, spokeWith: f.spoke, at: appNowIso() });
        v.bankPending = null;
        try {
          audit("vendor", v.id, "bank-change-verified", before, v.bank, `called ${f.phone}, spoke with ${f.spoke}`);
        } catch (e) {}
        save(), render();
        rcToast(`${v.name}'s new account ····${(v.bank || {}).last4} confirmed by phone with ${f.spoke}; payments can go out`, [{ label: "Open", run: () => vendorPage(v.id) }]);
      },
    },
  );
}
function scBankReject(v) {
  const bp = v.bankPending;
  if (!bp) return;
  (v.bankLog = v.bankLog || []).push({ rejected: !0, asked: bp, by: scMe(), at: appNowIso() });
  try {
    audit("vendor", v.id, "bank-change-rejected", null, bp, "the vendor did not ask for it");
  } catch (e) {}
  (v.bankPending = null), save(), render();
  rcToast(`Bank change for ${v.name} rejected: the account on file stays. If the request came by email, it may be fraud: tell the owner.`, [{ label: "Open", run: () => vendorPage(v.id) }]);
}
// ask the vendor for the paper (a draft the coordinator sends; nothing leaves on its own)
function scPaperRequest(v, kind) {
  if (!v) return;
  const coord = (DB.users || []).find((u) => "coord" === u.role) || {},
    first = String(v.contact || v.name || "").split(" ")[0],
    what = "w9" === kind ? "a signed W-9" : "a current certificate of insurance naming SmartDesign as additional insured",
    o = {
      id: uid("ox"),
      kind: "paper-request",
      to: { name: v.contact || v.name, email: v.email || "" },
      subject: `${"w9" === kind ? "W-9" : "Certificate of insurance"} needed before payment`,
      body: `Hi ${first},\n\nBefore we release your next payment we need ${what}. Could you send it today?\n\nThank you,\n${coord.name || scMe()}\nSmartDesign`,
      about: { label: `${v.name}: ${"w9" === kind ? "W-9" : "COI"} for payment` },
      aboutKey: `pc|${v.id}|${kind}`,
      forName: coord.name || "",
      status: "draft",
      at: today(),
      by: "assistant",
    };
  if ((DB.outbox || []).some((x) => x.aboutKey === o.aboutKey && "draft" === x.status)) return toast(`The request to ${v.name} is already drafted, waiting on ${coord.name || "the coordinator"}`);
  (DB.outbox = DB.outbox || []).push(o), save(), render();
  rcToast(`Request to ${v.name} for ${"w9" === kind ? "the W-9" : "the COI"} drafted — it waits on ${coord.name || "the coordinator"} to send`, [{ label: "Open", run: () => vendorPage(v.id) }]);
}

// ---- the subcontract's pay applications ---------------------------------------------------------------------------
// what each SOV line has been claimed to date before this application (its share of every bill before it)
function scPrevPct(po, L, exceptId) {
  const B = scBilledToDate(po, exceptId, { progress: !0 });
  return L.scheduled > 0 ? r2((100 * (B[L.id] || 0)) / L.scheduled) : 0;
}
// the next application number: one past every bill billed on the subcontract (a bill before pay applications counts)
function scNextAppNo(po) {
  const B = scBillsOf(po).filter((b) => !b.retainageRelease && billGross(b) > 0);
  return 1 + Math.max(B.length, ...B.map((b) => (b.payApp && +b.payApp.no) || 0));
}
// New Pay Application: the sub's claim, line by line, beside what the site measured; it becomes a bill on the
// subcontract at the contract's retainage, submitted for the PM's approval
function scPayAppSheet(po) {
  if (!po || !scIsSubcontract(po)) return;
  if (!["issued", "partial", "received"].includes(po.status)) return toast(`${po.number} is not issued yet: issue the subcontract first`);
  const sov = scSov(po),
    no = scNextAppNo(po),
    rate = +po.retainagePct || 0,
    rows = sov.map((L) => ({ L: L, prev: scPrevPct(po, L), M: scMeasured(po, L) }));
  const m = mbModal(
    `New Pay Application — ${esc(po.vendor)} · ${esc(po.number)}`,
    `<p class="small muted" style="margin:0 0 8px">Application ${no}. Enter what ${esc(po.vendor)} claims complete to date on each line; what the site measured sits beside it. ${rate ? `${rate}% retainage is held.` : "No retainage on this subcontract."}</p>
    <div class="grid2">${mbF("Sub's Invoice Number", mbIn("number", "", "e.g. CM-0102"))}${mbF("Work Through", mbIn("periodTo", today(), "", "date"))}</div>
    <div class="sc-pa-lines">${rows
      .map(
        (r, i) =>
          `<div class="sc-pa-line"><div class="sc-pa-h"><b>${esc(r.L.desc)}</b><span class="small muted">${money(r.L.scheduled)} scheduled · ${Math.round(r.prev)}% claimed before</span></div><div class="sc-pa-m small ${"measured" === r.M.basis ? "" : "muted"}">Site: ${esc(scMeasuredWords(r.M))}</div><label class="f sc-pa-in"><span>Claimed to Date %</span><input type="number" inputmode="decimal" min="${Math.round(r.prev)}" max="100" step="1" data-f="pct${i}" value="${Math.round(r.prev)}"></label><div class="small sc-pa-amt" data-paamt="${i}"></div></div>`,
      )
      .join("")}</div>
    <div class="note small sc-pa-total" id="sc-pa-total"></div>
    <label class="chk"><input type="checkbox" data-f="waiver"> A conditional progress waiver came in with it</label>`,
    {
      submit: "Submit for Approval",
      onSubmit: (f) => {
        if (!f.number) return toast("The sub's invoice number: it is how the application is matched and paid"), !1;
        const lines = [],
          paLines = [];
        rows.forEach((r, i) => {
          const pct = Math.max(r.prev, Math.min(100, +f["pct" + i] || 0)),
            amt = r2(((pct - r.prev) / 100) * r.L.scheduled);
          paLines.push({ id: r.L.id, desc: r.L.desc, scheduled: r.L.scheduled, prevPct: r.prev, pct: pct, measured: r.M.pct, measuredBasis: r.M.basis, measuredBy: r.M.by || "", measuredOn: r.M.on || "" });
          amt > 0 && lines.push(Object.assign({ id: uid("bl"), desc: `${r.L.desc}: ${Math.round(r.prev)}% to ${Math.round(pct)}%`, qty: 1, unit: "ls", amount: amt, code: r.L.code || "", line: r.L.line || "" }, r.L.change ? { scLineId: r.L.id } : { poLineId: r.L.id }));
        });
        if (!lines.length) return toast("Nothing claimed beyond the last application"), !1;
        const b = scPayAppBill(po, { number: f.number, periodTo: f.periodTo, lines: lines, paLines: paLines, no: no });
        f.waiver && wvAdd(b, { type: "conditional", scope: "progress", amount: billTotal(b), note: `with pay application ${no}` });
        save(), render();
        const W = pcWorkAhead(b, po);
        rcToast(`Pay application ${no} from ${po.vendor}: ${money(billGross(b))}${rate ? ` (${money(billTotal(b))} after retainage)` : ""} waits on the PM's approval${W.rows.length ? `; it claims ${money(W.ahead)} ahead of what the site measured` : ""}`, [{ label: "Open", run: () => flowGo.bill(b)() }]);
      },
    },
  );
  if (!m) return;
  m.classList.add("sc-pa-sheet");
  const calc = () => {
    let tot = 0,
      ahead = 0;
    rows.forEach((r, i) => {
      const inp = m.querySelector(`[data-f="pct${i}"]`),
        pct = Math.max(r.prev, Math.min(100, +inp.value || 0)),
        amt = r2(((pct - r.prev) / 100) * r.L.scheduled),
        over = "measured" === r.M.basis && pct > r.M.pct + scSet().tolPts ? r2(((pct - r.M.pct) / 100) * r.L.scheduled) : 0;
      (tot += amt), (ahead += over);
      const el = m.querySelector(`[data-paamt="${i}"]`);
      el && (el.innerHTML = `This application ${money(amt)}${over ? ` · <b class="bad-t">${money(over)} ahead of the site</b>` : ""}`);
    });
    const t = m.querySelector("#sc-pa-total");
    t && (t.innerHTML = `Gross ${money(tot)}${rate ? ` · ${rate}% retainage ${money(r2((tot * rate) / 100))} · payable ${money(r2(tot - (tot * rate) / 100))}` : ""}${ahead ? ` · <b class="bad-t">${money(ahead)} claimed ahead of the work measured: the PM approves at measured, or says why</b>` : ""}`);
  };
  m.querySelectorAll('[data-f^="pct"]').forEach((x) => x.addEventListener("input", calc)), calc();
  return m;
}
// the bill a pay application is: on the subcontract, its job, entity, cost code and estimate line, at its retainage
function scPayAppBill(po, o) {
  const v = scVendor(po.vendor),
    rate = +po.retainagePct || 0,
    net = /net ?(\d+)/i.test((v && v.terms) || "") ? +v.terms.match(/net ?(\d+)/i)[1] : 30,
    to = o.periodTo || today(),
    b = {
      id: uid("b"),
      vendor: po.vendor,
      number: o.number,
      date: to,
      due: iso(addDays(to, net)),
      entityId: "function" == typeof poEntity ? poEntity(po) : po.entityId || "ent1",
      projectId: po.projectId || "",
      poId: po.id,
      cat: "subs",
      code: (po.lines[0] || {}).code || "",
      line: 1 === po.lines.length ? po.lines[0].line || "" : "",
      lines: o.lines,
      payMethod: (v && v.payMethod) || "ACH",
      fileId: "",
      notes: `Pay application ${o.no} on ${po.number}, work through ${scDay(to)}`,
      status: "submitted",
      approvals: [{ t: nowStamp(), ts: appNowIso(), by: scMe(), role: role(), action: `pay application ${o.no} submitted` }],
      createdBy: scMe(),
      createdAt: appNowIso(),
      retainagePct: rate,
      taxStatus: po.taxStatus || "none",
      payApp: { no: o.no, periodTo: to, lines: o.paLines, at: appNowIso(), by: scMe() },
    };
  "function" == typeof billLinesNorm && billLinesNorm(b);
  DB.bills.push(b);
  try {
    audit("bill", b.id, "pay-app", "", `${po.number} #${o.no}`, `${money(billGross(b))} gross`);
    log(`Pay application ${o.no} from ${po.vendor} on ${po.number}: ${money(billGross(b))}${rate ? `, ${money(r2(billGross(b) - billTotal(b)))} retainage held` : ""}`);
  } catch (e) {}
  return b;
}
// The PM's approval of a pay application, against the work in place: each line claimed beside what the site
// measured. Approve at Measured is the safe yes; Approve as Claimed asks why and keeps it as the hold's release.
let scReviewing = 0;
function scApproveAct(b) {
  const owner = isOwner(),
    tot = billTotal(b);
  return "submitted" !== b.status || owner ? ("submitted" === b.status && needsOwner(tot) && owner ? "pmok" : "approve") : "pmok";
}
function scRunApproval(b, why) {
  const keep = S,
    p = scProj(b.projectId);
  p && (S = p);
  scReviewing++;
  try {
    billAction(b, scApproveAct(b), why);
  } catch (e) {
    console.warn("pay app approval", e);
  } finally {
    scReviewing--, (S = keep);
  }
  render();
}
function scApproveAtMeasured(b) {
  const po = scPOOf(b);
  if (!po || !b.payApp) return null;
  const tol = scSet().tolPts,
    claimedGross = billGross(b),
    changed = [];
  (b.payApp.lines || []).forEach((pl) => {
    const L = scSov(po).find((x) => x.id === pl.id);
    if (!L) return;
    const M = scMeasured(po, L);
    if ("measured" !== M.basis || null == M.pct || !(pl.pct > M.pct + tol)) return;
    const to = Math.max(+pl.prevPct || 0, M.pct),
      amt = r2(((to - (+pl.prevPct || 0)) / 100) * L.scheduled),
      bl = (b.lines || []).find((l) => l.poLineId === pl.id || l.scLineId === pl.id);
    changed.push({ id: pl.id, desc: pl.desc, claimed: pl.pct, approved: to, measured: M.pct, by: M.by, on: M.on });
    pl.claimedPct = pl.pct;
    pl.pct = to;
    bl && ((bl.amount = amt), (bl.desc = `${L.desc}: ${Math.round(+pl.prevPct || 0)}% to ${Math.round(to)}% (approved at measured; ${Math.round(pl.claimedPct)}% claimed)`));
  });
  b.lines = (b.lines || []).filter((l) => +l.amount > 0 || !(l.poLineId || l.scLineId));
  if (!changed.length) return null;
  const diff = r2(claimedGross - billGross(b));
  b.payApp.revised = { by: scMe(), role: role(), at: appNowIso(), claimed: claimedGross, approved: billGross(b), diff: diff, lines: changed };
  (b.approvals = b.approvals || []).push({ t: nowStamp(), ts: appNowIso(), by: scMe(), role: role(), action: `pay application approved at measured: ${money(billGross(b))} of ${money(claimedGross)} claimed`, note: `${money(diff)} ahead of the work goes to the next application` });
  try {
    audit("bill", b.id, "payapp-at-measured", money(claimedGross), money(billGross(b)), changed.map((c) => `${c.desc} ${c.claimed}% to ${c.approved}%`).join("; "));
  } catch (e) {}
  // the conditional waiver that came in at the claimed amount still covers the smaller payment
  return b.payApp.revised;
}
function scPayAppReview(b) {
  const po = scPOOf(b);
  if (!po) return;
  const W = pcWorkAhead(b, po),
    sov = scSov(po),
    rows = (b.payApp ? b.payApp.lines : sov.map((L) => ({ id: L.id, desc: L.desc, pct: r2((100 * ((scBilledToDate(po)[L.id] || 0) + 0)) / (L.scheduled || 1)), prevPct: scPrevPct(po, L, b.id) }))).map((pl) => {
      const L = sov.find((x) => x.id === pl.id) || { scheduled: pl.scheduled || 0, desc: pl.desc };
      return { pl: pl, L: L, M: scMeasured(po, L) };
    });
  mbModal(
    `Pay Application ${esc((b.payApp && b.payApp.no) || "")} — ${esc(b.vendor)}`,
    `<p class="small muted" style="margin:0 0 8px">${esc(po.number)} · ${esc(scJob(b.projectId))}. What ${esc(b.vendor)} claims beside the work in place the site measured (daily logs, progress updates and photos).</p>
    <div class="sc-pa-lines">${rows
      .map((r) => {
        const over = "measured" === r.M.basis && +r.pl.pct > r.M.pct + scSet().tolPts;
        return `<div class="sc-pa-line ${over ? "pc-held" : ""}"><div class="sc-pa-h"><b>${esc(r.L.desc || r.pl.desc)}</b><span class="small muted">${money(r.L.scheduled)} scheduled</span></div><div class="small">Claimed ${Math.round(+r.pl.pct || 0)}% to date (${Math.round(+r.pl.prevPct || 0)}% before)</div><div class="small ${over ? "bad-t" : "muted"}">Site: ${esc(scMeasuredWords(r.M))}${over ? ` · ${money(r2(((r.pl.pct - r.M.pct) / 100) * r.L.scheduled))} ahead` : ""}</div>${r.M.tasks.length ? `<div class="small muted">Measured by: ${esc(r.M.tasks.join(", "))}</div>` : ""}</div>`;
      })
      .join("")}</div>
    ${W.rows.length ? `<div class="note warn small">${money(W.ahead)} is claimed ahead of the work measured. Approve at Measured pays what is in place; the rest goes on the next application.</div>` : `<div class="note small">${esc(W.words)}.</div>`}`,
    {
      submit: W.rows.length && b.payApp ? "Approve at Measured" : "Approve",
      alt: W.rows.length ? { label: "Approve as Claimed", run: () => scAsClaimed(b) } : null,
      onSubmit: () => {
        W.rows.length && b.payApp && scApproveAtMeasured(b);
        scRunApproval(b);
        const R = b.payApp && b.payApp.revised;
        rcToast(`${b.number || "Pay application"} ${"pm-approved" === b.status ? "recommended" : "approved" === b.status ? "approved" : "reviewed"}${R ? ` at measured: ${money(R.approved)} of ${money(R.claimed)} claimed, ${money(R.diff)} to the next application` : ""}`, [{ label: "Open", run: () => flowGo.bill(b)() }]);
      },
    },
  );
}
function scAsClaimed(b) {
  billAskWhy(
    `Approve as Claimed — ${esc(b.vendor)}`,
    "The site measured less than the sub claims. Say why the claim is right: what you saw, and when.",
    "Approve as Claimed",
    "e.g. walked it today with Angel: the uppers are hung, the log is a day behind",
    (why) => {
      const po = scPOOf(b),
        W = po ? pcWorkAhead(b, po) : { rows: [], ahead: 0 },
        h = { key: "work", money: W.ahead };
      b.payApp && (b.payApp.asClaimed = { why: why, by: scMe(), role: role(), at: appNowIso(), ahead: W.ahead });
      (b.pcRel = b.pcRel || []).push({ key: "work", sig: pcSig(h), what: `Paying ahead of work, ${money(W.ahead)}`, why: why, by: scMe(), role: role(), at: appNowIso(), amount: W.ahead });
      try {
        audit("bill", b.id, "payapp-as-claimed", "", money(W.ahead), why);
      } catch (e) {}
      scRunApproval(b, why);
      rcToast(`${b.number || "Pay application"} approved as claimed by ${scMe()}: ${why}`, [{ label: "Open", run: () => flowGo.bill(b)() }]);
    },
  );
}

// ---- the per-vendor, per-job ledger -------------------------------------------------------------------------------
// contract, approved changes, billed, paid, retainage held, credits and deposits open, balance to finish, and the
// work in place against it. One reading: the vendor page, the subcontract card, Ask and the query table use it.
function scLedger(vname, pid) {
  const n = scLow(vname),
    pos = (DB.pos || []).filter((po) => scLow(po.vendor) === n && (!pid || po.projectId === pid) && !["cancelled", "void", "draft"].includes(po.status)),
    bills = (DB.bills || []).filter((b) => scLow(b.vendor) === n && (!pid || b.projectId === pid) && scLive(b)),
    base = r2(pos.reduce((a, po) => a + poTotal(po).total, 0)),
    cos = r2(pos.reduce((a, po) => a + scChangeTotal(po), 0)),
    work = bills.filter((b) => !b.retainageRelease && billGross(b) > 0),
    billed = r2(work.reduce((a, b) => a + billGross(b), 0)),
    credits = bills.filter((b) => billTotal(b) < -0.005),
    creditOpen = r2(credits.filter((b) => "approved" === b.status).reduce((a, b) => a - billTotal(b) - (b.takenBy || []).reduce((s, t) => s + (+t.amount || 0), 0), 0)),
    deposits = r2(work.filter(scIsDeposit).reduce((a, b) => a + billGross(b), 0)),
    retHeld = r2(work.filter((b) => +b.retainagePct).reduce((a, b) => a + billGross(b) - billTotal(b), 0)),
    retReleased = r2(bills.filter((b) => b.retainageRelease).reduce((a, b) => a + billGross(b), 0)),
    paidBills = r2(bills.filter((b) => billTotal(b) > 0).reduce((a, b) => a + scPaidBill(b), 0)),
    direct = r2(pos.reduce((a, po) => a + (DB.txns || []).filter((t) => (po.matchedTxns || []).includes(t.id) && !t.billId).reduce((s, t) => s - +t.amt, 0), 0)),
    paid = r2(paidBills + direct),
    payable = r2(bills.filter((b) => billTotal(b) > 0 && ["approved", "pm-approved", "submitted"].includes(b.status)).reduce((a, b) => a + Math.max(0, billTotal(b) - scPaidBill(b) - scCreditsTaken(b)), 0)),
    subs = pos.filter(scIsSubcontract);
  let inPlace = null,
    measuredOf = 0;
  subs.forEach((po) =>
    scSov(po).forEach((L) => {
      const M = scMeasured(po, L);
      "measured" === M.basis && null != M.pct && ((inPlace = r2((inPlace || 0) + (M.pct / 100) * L.scheduled)), (measuredOf = r2(measuredOf + L.scheduled)));
    }),
  );
  const subBilled = r2(work.filter((b) => !scIsDeposit(b) && subs.some((po) => po.id === b.poId)).reduce((a, b) => a + billGross(b), 0)),
    ahead = null == inPlace ? 0 : r2(Math.max(0, subBilled - inPlace)),
    contract = r2(base + cos),
    v = scVendor(vname),
    noWaiver = bills.filter((b) => billTotal(b) > 0 && scSubBill(b) && !b.retainageRelease && (scPaidSt(b) || scPaidBill(b) > 0) && !wvHas(b, "unconditional", "progress", Math.min(billTotal(b), scPaidBill(b) || billTotal(b)))),
    retShort = r2(
      work
        .filter((b) => {
          const po = scPOOf(b);
          return po && scIsSubcontract(po) && !scIsDeposit(b) && +po.retainagePct > (+b.retainagePct || 0);
        })
        .reduce((a, b) => a + (billGross(b) * (+scPOOf(b).retainagePct - (+b.retainagePct || 0))) / 100, 0),
    );
  return {
    vendor: (v && v.name) || vname,
    projectId: pid || "",
    project: pid ? scJob(pid) : "all jobs",
    sub: !!v && scIsSub(v),
    pos: pos,
    bills: bills,
    contractBase: base,
    changes: cos,
    contract: contract,
    billed: billed,
    paid: paid,
    payable: payable,
    retainageHeld: r2(retHeld - retReleased),
    retainageShort: retShort,
    creditsOpen: creditOpen,
    deposits: deposits,
    balanceToFinish: pos.length ? r2(contract - billed) : 0,
    left: pos.length ? r2(contract - paid) : 0,
    inPlace: inPlace,
    measuredOf: measuredOf,
    aheadOfWork: ahead,
    waiversMissing: noWaiver,
  };
}
// every vendor and job pair with an order or a bill
function scLedgerRows() {
  const seen = new Set(),
    out = [];
  (DB.pos || []).filter((po) => !["cancelled", "void", "draft"].includes(po.status)).forEach((po) => seen.add(`${scLow(po.vendor)}|${po.projectId || ""}`));
  (DB.bills || []).filter(scLive).forEach((b) => seen.add(`${scLow(b.vendor)}|${b.projectId || ""}`));
  seen.forEach((k) => {
    const [vn, pid] = k.split("|"),
      v = (DB.vendors || []).find((x) => scLow(x.name) === vn);
    vn && out.push(scLedger(v ? v.name : vn, pid || ""));
  });
  return out;
}
function scLedgerSay(L) {
  return `${L.vendor} on ${L.project}: ${L.pos.length ? `contract ${money(L.contract)}${L.changes ? ` (with ${money(L.changes)} of approved changes)` : ""}, ` : "no order on file, "}billed ${money(L.billed)}, paid ${money(L.paid)}${L.retainageHeld ? `, ${money(L.retainageHeld)} retainage held` : ""}${L.payable ? `, ${money(L.payable)} billed and not paid yet` : ""}${L.pos.length ? `, ${money(L.left)} left to pay on the contract (${money(L.balanceToFinish)} still to bill)` : ""}${L.creditsOpen ? `, ${money(L.creditsOpen)} of credit open` : ""}${L.deposits ? `; ${money(L.deposits)} of it a deposit, applied as the work is billed` : ""}${null != L.inPlace ? `; work in place ${money(L.inPlace)} as measured on site${L.aheadOfWork ? `, billed ${money(L.aheadOfWork)} ahead of it` : ""}` : ""}${L.retainageShort ? `; ${money(L.retainageShort)} of retainage was not held` : ""}${L.waiversMissing.length ? `; ${L.waiversMissing.length} payment${L.waiversMissing.length > 1 ? "s" : ""} without an unconditional lien waiver` : ""}.`;
}
function scLedgerHtml(rows, o) {
  o = o || {};
  if (!rows.length) return "";
  return `<div class="tw"><table class="t sc-ledger"><thead><tr><th>${o.byVendor ? "Vendor" : "Job"}</th><th class="money">Contract</th><th class="money">Billed</th><th class="money">Paid</th><th class="money">Retainage</th><th class="money">To Finish</th><th>Work in Place</th></tr></thead><tbody>${rows
    .map(
      (L) =>
        `<tr><td><b>${esc(o.byVendor ? L.vendor : L.project)}</b>${L.waiversMissing.length ? `<div class="small warn-t">${L.waiversMissing.length} without a lien waiver</div>` : ""}${L.creditsOpen ? `<div class="small">${money(L.creditsOpen)} credit open</div>` : ""}</td><td class="money">${L.pos.length ? money(L.contract) : "—"}${L.changes ? `<div class="small muted">${money(L.changes)} changes</div>` : ""}</td><td class="money">${money(L.billed)}</td><td class="money">${money(L.paid)}${L.payable ? `<div class="small muted">${money(L.payable)} to pay</div>` : ""}</td><td class="money">${L.retainageHeld ? money(L.retainageHeld) : "—"}${L.retainageShort ? `<div class="small bad-t">${money(L.retainageShort)} not held</div>` : ""}</td><td class="money">${L.pos.length ? money(L.balanceToFinish) : "—"}</td><td class="small">${null == L.inPlace ? '<span class="muted">not measured</span>' : `${money(L.inPlace)}${L.aheadOfWork ? ` · <b class="bad-t">${money(L.aheadOfWork)} billed ahead</b>` : ""}`}</td></tr>`,
    )
    .join("")}</tbody></table></div>`;
}

// ---- the subcontract on its PO page ---------------------------------------------------------------------------
function scPapers(v) {
  const td = today(),
    out = [];
  if (!v) return [{ ok: !1, t: "Vendor not on file" }];
  out.push(v.insuranceExp ? (v.insuranceExp < td ? { ok: !1, t: `COI expired ${scDay(v.insuranceExp)}` } : { ok: !0, t: `COI through ${scDay(v.insuranceExp)}` }) : { ok: !1, t: "No COI on file" });
  out.push(v.licenseExp ? (v.licenseExp < td ? { ok: !1, t: `License expired ${scDay(v.licenseExp)}` } : { ok: !0, t: `License through ${scDay(v.licenseExp)}` }) : { ok: null, t: "No license on file" });
  out.push(v.w9 ? { ok: !0, t: "W-9 on file" } : { ok: !1, t: "No W-9 on file" });
  return out;
}
function scCardHtml(po) {
  const t = scT(po),
    v = scVendor(po.vendor),
    sov = scSov(po),
    B = scBilledToDate(po, "", { progress: !0 }),
    L = scLedger(po.vendor, po.projectId),
    rate = +po.retainagePct || 0,
    bills = scBillsOf(po),
    dep = r2(bills.filter((b) => scIsDeposit(b) && !b.retainageRelease).reduce((a, b) => a + billGross(b), 0)),
    canEdit = ["owner", "pm", "coord"].includes(role()),
    changes = t.changes || [];
  const pill = (p) => `<span class="pill ${p.ok ? "ok" : null === p.ok ? "" : "bad"}">${esc(p.t)}</span>`;
  return `<div class="card sc-card" data-scpo="${esc(po.id)}"><div class="pc-hd"><h3>Subcontract</h3><span class="row sc-acts">${canEdit ? '<button type="button" class="btn sm" data-sc="terms">Edit Terms</button><button type="button" class="btn sm" data-sc="change">Add a Change</button>' : ""}${["issued", "partial", "received"].includes(po.status) && ["owner", "pm", "coord", "billing", "controller"].includes(role()) ? '<button type="button" class="btn sm" data-sc="payapp">New Pay Application</button>' : ""}</span></div>
  <div class="sc-terms small">${t.scope ? `<div><b>Scope</b> ${esc(t.scope)}</div>` : `<div class="muted">No scope written yet. A subcontract says what is in and what is out, so the bid, the pay applications and any backcharge read against the same words.</div>`}${(t.inclusions || []).length ? `<div><b>Includes</b> ${esc(t.inclusions.join("; "))}</div>` : ""}${(t.exclusions || []).length ? `<div><b>Excludes</b> ${esc(t.exclusions.join("; "))}</div>` : ""}<div>${t.signedOn ? `Signed ${esc(scDay(t.signedOn))}${t.signedBy ? " by " + esc(t.signedBy) : ""}` : '<span class="warn-t">Not signed yet</span>'} · ${rate ? `${rate}% retainage until ${esc(t.retainageAt || "substantial completion")}` : "no retainage"}</div></div>
  <div class="sc-papers">${scPapers(v).map(pill).join("")}</div>
  <div class="tw"><table class="t sc-sov"><thead><tr><th>Schedule of Values</th><th class="money">Scheduled</th><th class="money">Billed to Date</th><th>In Place</th><th class="money">To Finish</th></tr></thead><tbody>${sov
    .map((x) => {
      const M = scMeasured(po, x),
        billed = B[x.id] || 0,
        pct = x.scheduled ? Math.round((100 * billed) / x.scheduled) : 0,
        ahead = "measured" === M.basis && pct > M.pct + scSet().tolPts;
      return `<tr><td>${esc(x.desc)}${x.change ? ' <span class="pill">Change</span>' : ""}</td><td class="money">${money(x.scheduled)}</td><td class="money">${money(billed)}<div class="small muted">${pct}%</div></td><td class="small ${ahead ? "bad-t" : ""}">${esc(scMeasuredWords(M))}</td><td class="money">${money(r2(x.scheduled - billed))}</td></tr>`;
    })
    .join("")}${dep ? `<tr><td>Deposit <span class="small muted">applied as the work is billed</span></td><td></td><td class="money">${money(dep)}</td><td></td><td></td></tr>` : ""}<tr class="sc-tot"><td><b>Contract</b>${L.changes ? `<div class="small muted">${money(L.contractBase)} and ${money(L.changes)} of changes</div>` : ""}</td><td class="money"><b>${money(scContract(po))}</b></td><td class="money"><b>${money(r2(B._total + dep))}</b></td><td class="small">${null == L.inPlace ? "" : `${money(L.inPlace)} in place${L.aheadOfWork ? ` · <b class="bad-t">${money(L.aheadOfWork)} billed ahead</b>` : ""}`}</td><td class="money"><b>${money(r2(scContract(po) - B._total - dep))}</b></td></tr></tbody></table></div>
  <div class="small sc-money">Paid ${money(L.paid)} · retainage held ${money(L.retainageHeld)}${L.retainageShort ? ` · <b class="bad-t">${money(L.retainageShort)} retainage not held</b>` : ""}${L.payable ? ` · ${money(L.payable)} billed, not paid` : ""}${L.waiversMissing.length ? ` · <b class="warn-t">${L.waiversMissing.length} payment${L.waiversMissing.length > 1 ? "s" : ""} without an unconditional waiver</b>` : ""}</div>
  ${changes.length ? `<h4 class="sc-h4">Changes to the Subcontract</h4><ul class="sc-changes">${changes.map((c) => `<li><b>${esc(c.number)}</b> ${esc(c.desc)} · ${money(c.amount)} · ${esc(c.status)}${c.by ? ` · ${esc(c.by)}` : ""}${"pending" === c.status && ["owner", "pm"].includes(role()) ? ` <button type="button" class="btn sm" data-sc="approve-change" data-scc="${esc(c.id)}">Approve the Change</button>` : ""}</li>`).join("")}</ul>` : ""}
  <h4 class="sc-h4">Pay Applications</h4>${
    bills.length
      ? `<ul class="sc-apps">${bills
          .map((b) => {
            const R = ["approved", "pm-approved", "submitted"].includes(b.status) && pcOpen(b) > 0.005 ? pcCheck(b) : null,
              hold = R ? R.holds.filter((h) => "approval" !== h.key) : [];
            return `<li><a href="#" data-scbill="${esc(b.id)}">${b.payApp ? `Application ${esc(b.payApp.no)}` : b.retainageRelease ? "Retainage Release" : scIsDeposit(b) ? "Deposit" : "Bill"} · ${esc(b.number || "")}</a> <span class="small muted">${money(billGross(b))} gross${+b.retainagePct ? `, ${money(billTotal(b))} after retainage` : ""} · ${esc(billState(b).text || b.status)}${wvList(b).length ? ` · ${esc(wvList(b).slice(-1)[0].type)} waiver` : scSubBill(b) ? " · no waiver" : ""}</span>${hold.length ? ` <span class="pill bad">Held · ${hold.length}</span>` : R ? ' <span class="pill ok">Checked</span>' : ""}</li>`;
          })
          .join("")}</ul>`
      : '<div class="small muted">No pay application yet. New Pay Application takes the sub\'s claim line by line, beside what the site measured.</div>'
  }</div>`;
}
function scTermsSheet(po) {
  const t = scT(po);
  mbModal(
    `Subcontract Terms — ${esc(po.vendor)} · ${esc(po.number)}`,
    `${mbF("Scope", `<textarea data-f="scope" rows="3" placeholder="What the sub builds, in plain words">${esc(t.scope || "")}</textarea>`)}
    <div class="grid2">${mbF("Includes (One per Line)", `<textarea data-f="inc" rows="3">${esc((t.inclusions || []).join("\n"))}</textarea>`)}${mbF("Excludes (One per Line)", `<textarea data-f="exc" rows="3">${esc((t.exclusions || []).join("\n"))}</textarea>`)}</div>
    <div class="grid2">${mbF("Signed On", mbIn("signedOn", t.signedOn || "", "", "date"))}${mbF("Retainage Released At", mbSel("retainageAt", ["substantial completion", "final completion", "the sub's last day on site"], t.retainageAt || "substantial completion"))}</div>
    ${scBillsOf(po).length ? `<p class="small muted">Retainage stays at ${+po.retainagePct || 0}%: bills are already on file against it.</p>` : mbF("Retainage %", mbIn("ret", String(+po.retainagePct || 0), "", "number"))}`,
    {
      submit: "Save Terms",
      onSubmit: (f) => {
        const before = JSON.stringify(scT(po));
        po.sc = Object.assign({}, scT(po), {
          scope: f.scope || "",
          inclusions: String(f.inc || "").split("\n").map((x) => x.trim()).filter(Boolean),
          exclusions: String(f.exc || "").split("\n").map((x) => x.trim()).filter(Boolean),
          signedOn: f.signedOn || "",
          signedBy: f.signedOn ? scT(po).signedBy || scMe() : "",
          retainageAt: f.retainageAt || "substantial completion",
          changes: scT(po).changes || [],
        });
        null != f.ret && "" !== f.ret && !scBillsOf(po).length && (po.retainagePct = Math.max(0, Math.min(20, +f.ret || 0)));
        try {
          audit("po", po.id, "subcontract-terms", before, JSON.stringify(po.sc), "");
        } catch (e) {}
        save(), render();
        rcToast(`${po.number}: subcontract terms saved`, [{ label: "Open", run: () => flowGo.po(po)() }]);
      },
    },
  );
}
function scChangeSheet(po) {
  const self = ["owner", "pm"].includes(role());
  mbModal(
    `Add a Change — ${esc(po.vendor)} · ${esc(po.number)}`,
    `<p class="small muted" style="margin:0 0 8px">A change to the subcontract adds to what the sub may bill. ${self ? "You approve it as you add it." : "The PM or the owner approves it."}</p>${mbF("What Changed", mbIn("desc", "", "e.g. add pantry uppers"))}<div class="grid2">${mbF("Amount", mbIn("amount", "", "", "number"))}${mbF("Why", mbIn("why", "", "e.g. the client's CO-2026-004"))}</div>`,
    {
      submit: "Add the Change",
      onSubmit: (f) => {
        if (!f.desc) return toast("What changed"), !1;
        if (!+f.amount) return toast("The amount"), !1;
        const c = scAddChange(po, { desc: f.desc, amount: +f.amount, why: f.why });
        save(), render();
        rcToast(`${c.number} on ${po.number}: ${money(c.amount)} ${c.status}${"approved" === c.status ? `; the subcontract is now ${money(scContract(po))}` : ", waiting on the PM"}`, [{ label: "Open", run: () => flowGo.po(po)() }]);
      },
    },
  );
}
function scAddChange(po, o) {
  const t = (po.sc = Object.assign({}, scT(po)));
  t.changes = (t.changes || []).slice();
  const self = ["owner", "pm"].includes(role()),
    c = { id: uid("scc"), number: `SCO-${t.changes.length + 1}`, desc: o.desc, amount: r2(+o.amount || 0), why: o.why || "", status: self ? "approved" : "pending", by: scMe(), at: appNowIso(), approvedBy: self ? scMe() : "" };
  t.changes.push(c);
  try {
    audit("po", po.id, "subcontract-change", "", `${c.number} ${money(c.amount)} ${c.status}`, c.why);
  } catch (e) {}
  return c;
}
function scApproveChange(po, cid) {
  const c = (scT(po).changes || []).find((x) => x.id === cid);
  if (!c || "pending" !== c.status) return;
  if (!["owner", "pm"].includes(role())) return toast("The PM or the owner approves a change");
  if (scLow(c.by) === scLow(scMe())) return toast("A second person approves the change");
  (c.status = "approved"), (c.approvedBy = scMe()), (c.approvedAt = appNowIso());
  try {
    audit("po", po.id, "subcontract-change-approved", "pending", c.number, money(c.amount));
  } catch (e) {}
  save(), render();
  rcToast(`${c.number} approved: ${po.number} is now ${money(scContract(po))}`, [{ label: "Open", run: () => flowGo.po(po)() }]);
}

// ---- what a held payment is, for the queues ----------------------------------------------------------------------
// the approved bills with money still to pay whose check holds them (the approval itself is not a hold here)
function pcHeldBills() {
  return (DB.bills || [])
    .filter((b) => "approved" === b.status && billTotal(b) > 0 && pcOpen(b) > 0.005 && !b.ic)
    .map((b) => ({ b: b, R: pcCheck(b) }))
    .filter((x) => x.R.holds.some((h) => "approval" !== h.key));
}
const pcNeedsOwner = (x) => x.R.holds.some((h) => "owner" === h.who || h.fixed) || x.R.amount > scSet().ownerAbove;

// ---- where it is joined ------------------------------------------------------------------------------------------
// A bill's control flags (the ones an owner's approval answers with a reason): the retainage held is a fact on the
// bill, not a control to override; a subcontract is never "received" (its work is measured on site), so it says
// what it claims ahead of the work instead.
{
  const base = billFlags;
  billFlags = function (b) {
    let f = base.apply(this, arguments);
    try {
      if (!Array.isArray(f) || !b) return f;
      f = f.filter((x) => !/^Retainage \d+(\.\d+)?% held — net/.test(String(x)));
      const po = scPOOf(b);
      if (po && scIsSubcontract(po)) {
        f = f.filter((x) => !new RegExp(`^${po.number} shows nothing received`).test(String(x)));
        if (!b.retainageRelease && ["draft", "submitted", "pm-approved"].includes(b.status)) {
          const W = pcWorkAhead(b, po);
          W.rows.length && !pcReleasedBy(b, { key: "work", money: W.ahead }) && f.push(`Claims ${money(W.ahead)} ahead of the work measured on site`);
        }
      }
    } catch (e) {}
    return f;
  };
}
// the Standard behind each hold, the held-payment queue item and the paid-ahead catch
Object.assign(STD_MAP, Object.fromEntries(Object.keys(PC_STD).map((k) => ["pc:" + k, PC_STD[k]])), {
  payhold: { p: "integrity", c: ["pb", "office", "standards", /Three-way match/i] },
  subsAhead: { p: "cost", leak: !0, c: ["value", "dollar", /No money is committed/i] },
});
// Approvals: one chip for held payments and bank changes to verify; delegated by who may release them
APPR_CHIPS.splice(
  APPR_CHIPS.findIndex(([k]) => "other" === k),
  0,
  ["payhold", "Payment Holds"],
);
DELEGATION.payhold = {
  role: "controller",
  rule: "a held payment is released by the controller under the owner's limit, by the owner above it or when the hold says so; a bank change is verified by phone by the owner, or by the controller when the owner asked for it",
  who: (it) => {
    if (it.bank) {
      const v = (DB.vendors || []).find((x) => x.id === it.bank);
      return v && v.bankPending && "owner" === apprRoleOf(v.bankPending.by) ? "controller" : "owner";
    }
    const b = (DB.bills || []).find((x) => x.id === it.id);
    return b && pcNeedsOwner({ b: b, R: pcCheck(b) }) ? "owner" : "controller";
  },
};
{
  const base = mApprovals;
  mApprovals = function (opts) {
    const out = base.apply(this, arguments);
    try {
      if (!Array.isArray(out)) return out;
      // a pay application's card says what it claims against the work in place
      out.forEach((it) => {
        if ("bill" !== it.kind) return;
        const b = (DB.bills || []).find((x) => x.id === it.id),
          po = b && scPOOf(b);
        if (!b || !po || !scIsSubcontract(po) || b.retainageRelease) return;
        const W = pcWorkAhead(b, po);
        W.rows.length && ((it.detail = `${b.payApp ? `Pay application ${b.payApp.no}: ` : ""}${money(W.ahead)} claimed ahead of the work measured on site · ${it.detail || ""}`), (it.sev = "bad"));
      });
      const add = [];
      pcHeldBills().forEach((x) => {
        const H = x.R.holds.filter((h) => "approval" !== h.key);
        add.push({
          kind: "payhold",
          id: x.b.id,
          projectId: x.b.projectId || "",
          sev: "bad",
          n: money(x.R.amount),
          title: `Payment held · ${x.b.vendor} ${x.b.number || ""}`,
          detail: H.map((h) => h.what).join(" · "),
          yes: "Review",
          no: "Hold",
          act: "review",
          open: { view: "ap", billId: x.b.id },
        });
      });
      (DB.vendors || [])
        .filter((v) => v.bankPending)
        .forEach((v) =>
          add.push({
            kind: "payhold",
            id: "bank:" + v.id,
            bank: v.id,
            sev: "bad",
            n: "bank",
            title: `Verify ${v.name}'s new bank details by phone`,
            detail: `asked ${scDay(v.bankPending.at) || v.bankPending.t || ""} by ${v.bankPending.by || "someone"}${v.bankPending.via ? ` (${v.bankPending.via})` : ""} · every payment to ${v.name} is held until someone else calls the number on file`,
            yes: "Verify by Phone",
            no: "Reject",
            act: "verify",
            open: { view: "vendors" },
          }),
        );
      add.forEach((it) => (it.who = apprOwner(it)));
      const mine = opts && opts.everyone ? add : add.filter((it) => it.who === role());
      return out.concat(mine);
    } catch (e) {
      console.warn("payment holds", e);
      return out;
    }
  };
}
// the yes and no on a held payment, wherever the card is drawn
function pcApprYes(it) {
  if (!it) return;
  if (it.bank) {
    const v = (DB.vendors || []).find((x) => x.id === it.bank);
    return v && scCallBackSheet(v);
  }
  return pcPaySheet(it.id);
}
function pcApprNo(it) {
  if (!it) return;
  if (it.bank) {
    const v = (DB.vendors || []).find((x) => x.id === it.bank);
    return v && scBankReject(v);
  }
  const b = (DB.bills || []).find((x) => x.id === it.id);
  b && "function" == typeof billHoldSheet && billHoldSheet(b, "hold");
}
{
  const base = renderMApprove;
  renderMApprove = function () {
    const r = base.apply(this, arguments);
    try {
      const v = document.getElementById("v-mapprove");
      if (v && v.querySelector('.m-appr[data-mk="payhold"]')) {
        const items = mApprovals();
        v.querySelectorAll('.m-appr[data-mk="payhold"]').forEach((el) => {
          const it = items.find((x) => "payhold" === x.kind && String(x.id) === el.dataset.mid);
          if (!it) return;
          const y = el.querySelector("[data-myes]"),
            n = el.querySelector("[data-mno]");
          y && (y.onclick = (e) => (e.preventDefault(), e.stopPropagation(), pcApprYes(it)));
          n && (n.onclick = (e) => (e.preventDefault(), e.stopPropagation(), pcApprNo(it)));
        });
      }
    } catch (e) {
      console.warn("payment holds in approvals", e);
    }
    return r;
  };
}
{
  const base = tdCard;
  tdCard = function (it) {
    const c = base.apply(this, arguments);
    try {
      if (it && "payhold" === it.kind) {
        const b = !it.bank && (DB.bills || []).find((x) => x.id === it.id);
        c.line1 = b ? `<a href="#" data-tdrec>${esc(b.number || "Bill")}</a> · ${esc(b.vendor)} · payment held` : esc(it.title);
        c.why = esc(String(it.detail || "").split(" · ")[0]);
        c.verb = it.yes;
        c.run = () => pcApprYes(it);
        b && (c.go = flowGo.bill(b));
      }
    } catch (e) {}
    return c;
  };
}
// Who is blocked: a held payment is a vendor waiting on money, ranked with the bills
{
  const base = tdScore;
  tdScore = function (it) {
    if (it && "payhold" === it.kind) return 52 + ("bad" === it.sev ? 5 : 0);
    return base.apply(this, arguments);
  };
}
// Caught for You: a sub billed ahead of the work measured on site, or billed with retainage not held
CATCH.push({
  name: "subsAhead",
  label: "Subs Paid Ahead",
  rows: () =>
    scLedgerRows()
      .filter((L) => L.sub && (L.aheadOfWork > 500 || L.retainageShort > 0.5))
      .map((L) => {
        const po = L.pos.find(scIsSubcontract);
        return {
          key: `subahead:${scLow(L.vendor)}:${L.projectId}`,
          what: `${L.vendor} ${L.aheadOfWork > 500 ? "billed ahead of the work" : "billed without retainage"}`,
          sub: `${L.project}: ${L.aheadOfWork > 500 ? `${money(L.billed)} billed, ${money(L.inPlace)} in place as measured` : ""}${L.aheadOfWork > 500 && L.retainageShort > 0.5 ? "; " : ""}${L.retainageShort > 0.5 ? `${money(L.retainageShort)} of retainage not held` : ""}`,
          amount: r2(L.aheadOfWork + L.retainageShort),
          verb: "Review",
          run: po ? flowGo.po(po) : () => vendorPage((scVendor(L.vendor) || {}).id),
        };
      }),
});
// An overpayment that slipped through (a bill paid past its total, by any method): a credit or refund request the
// coordinator approves, tracked until a credit memo or a refund from the vendor covers it (BACKLOG §1.12).
function pcOverpaid() {
  return (DB.bills || [])
    .filter((b) => scLive(b) && billTotal(b) > 0 && !b.ic)
    .map((b) => ({ b: b, over: r2(scPaidBill(b) + scCreditsTaken(b) - billTotal(b) - pcDisputed(b)) }))
    .filter((x) => x.over > 0.5)
    .map((x) => {
      const R = x.b.recover || {},
        back = r2(
          (DB.bills || []).filter((c) => scLow(c.vendor) === scLow(x.b.vendor) && scLive(c) && billTotal(c) < 0 && (c.recovers === x.b.id || (R.at && c.date >= String(R.at).slice(0, 10)))).reduce((a, c) => a - billTotal(c), 0) +
            (DB.txns || []).filter((t) => +t.amt > 0 && R.at && t.date >= String(R.at).slice(0, 10) && scLow(`${t.vendor || ""} ${t.desc || ""}`).includes(scLow(x.b.vendor).split(/\s+/)[0])).reduce((a, t) => a + +t.amt, 0),
        );
      return Object.assign(x, { requested: !!R.draftId, back: back, open: r2(Math.max(0, x.over - back)) });
    })
    .filter((x) => x.open > 0.5);
}
function pcRecoverDraft(b, over) {
  const v = scVendor(b.vendor) || { name: b.vendor },
    coord = (DB.users || []).find((u) => "coord" === u.role) || {},
    first = String(v.contact || v.name || "").split(" ")[0],
    o = {
      id: uid("ox"),
      kind: "overpay-credit",
      to: { name: v.contact || v.name, email: v.email || "" },
      subject: `Overpayment on ${b.number || "your invoice"}: credit or refund of ${scM(over)}`,
      body: `Hi ${first},\n\nOur records show we paid ${scM(scPaidBill(b))} against invoice ${b.number || ""} for ${scM(billTotal(b))}, ${scM(over)} more than it was for. Could you send a credit memo we can take off the next invoice, or refund the difference?\n\nThank you,\n${coord.name || scMe()}\nSmartDesign`,
      about: { label: `${b.vendor} ${b.number || ""}: overpaid ${scM(over)}`, billId: b.id },
      aboutKey: `pc|${b.id}|overpay`,
      forName: coord.name || "",
      status: "draft",
      at: today(),
      by: "assistant",
      because: `${standardWhy("pc:prior")}. ${STD_WASTE}`,
    };
  (DB.outbox = DB.outbox || []).push(o);
  b.recover = { amount: over, draftId: o.id, at: appNowIso(), by: scMe() };
  try {
    audit("bill", b.id, "overpay-credit-requested", "", scM(over), o.id);
  } catch (e) {}
  save(), render();
  rcToast(`Credit request to ${b.vendor} for ${scM(over)} drafted — it waits on ${coord.name || "the coordinator"} to send, and stays on Caught for You until the credit or refund lands`, [{ label: "Open", run: () => flowGo.bill(b)() }]);
  return o;
}
CATCH.push({
  name: "vendorOverpaid",
  label: "Vendors Overpaid",
  rows: () =>
    pcOverpaid().map((x) => ({
      key: "overpaid:" + x.b.id,
      what: `${x.b.vendor} overpaid on ${x.b.number || "a bill"}`,
      sub: `${scM(x.over)} paid past the bill${x.back ? `, ${scM(x.back)} back so far` : ""}${x.requested ? "; credit requested" : ""}`,
      amount: x.open,
      verb: x.requested ? "Open" : "Request Credit",
      run: x.requested ? flowGo.bill(x.b) : () => pcRecoverDraft(x.b, x.open),
    })),
});
STD_MAP.vendorOverpaid = { p: "cost", leak: !0, c: ["value", "dollar", /Waste nothing/i] };
// the money path: every payment of a bill goes through the check; Mark Paid too
payDialog = function (billId) {
  return pcPaySheet(billId);
};
{
  const base = billAction;
  billAction = function (b, a, why) {
    try {
      if (b && "paid" === a && "__pc" !== why) {
        const R = pcCheck(b, { amount: pcOpen(b) });
        if (!R.pass) return void rcToast(`Not paid: ${R.holds[0].what}${R.holds.length > 1 ? `, and ${R.holds.length - 1} more` : ""}`, [{ label: "Open", run: () => pcPaySheet(b.id) }]);
      }
      // a sub's bill claiming ahead of the work measured opens the PM's review (at measured, or as claimed with why)
      if (b && ["pmok", "approve"].includes(a) && !scReviewing && ["submitted", "pm-approved"].includes(b.status) && !b.retainageRelease) {
        const po = scPOOf(b);
        if (po && scIsSubcontract(po) && scSubBill(b)) {
          const W = pcWorkAhead(b, po);
          if (W.rows.length && !pcReleasedBy(b, { key: "work", money: W.ahead })) return void scPayAppReview(b);
        }
      }
    } catch (e) {
      console.warn("payment check", e);
    }
    return base.apply(this, arguments);
  };
}
// a subcontract is billed by pay application, never by Bill This PO
{
  const base = billFromPO;
  billFromPO = function (po) {
    if (po && scIsSubcontract(po)) return scPayAppSheet(po);
    return base.apply(this, arguments);
  };
}
// mobilisation: no subcontract issues to a sub without a current COI, or with a lapsed license
{
  const base = poAction;
  poAction = function (po, a) {
    try {
      if (po && scIsSubcontract(po) && ["issue", "submit", "approve"].includes(a) && ["draft", "pending"].includes(po.status)) {
        const v = scVendor(po.vendor),
          td = today(),
          R = [];
        v && !v.insuranceExp && R.push(`${v.name} has no certificate of insurance on file`);
        v && v.insuranceExp && v.insuranceExp < td && R.push(`${v.name}'s certificate of insurance expired ${scDay(v.insuranceExp)}`);
        v && v.licenseExp && v.licenseExp < td && R.push(`${v.name}'s license expired ${scDay(v.licenseExp)}`);
        if (R.length) return void poRefuse(po, R.concat(["a sub mobilises only with current insurance and license"]));
      }
    } catch (e) {
      console.warn("subcontract papers", e);
    }
    return base.apply(this, arguments);
  };
}
// the order's open amount counts the subcontract's approved changes (a pay application billing a change is not over)
{
  const base = pay3PO;
  pay3PO = function (b) {
    const P = base.apply(this, arguments);
    try {
      if (P && P.po && scIsSubcontract(P.po)) {
        const add = scChangeTotal(P.po);
        add && ((P.total = r2(P.total + add)), (P.left = r2(P.left + add)));
      }
    } catch (e) {}
    return P;
  };
}
// who set a vendor up (whoever did cannot release its payments)
{
  const base = saveVendor;
  saveVendor = function () {
    const isNew = !(editing && editing.id),
      n = (DB.vendors || []).length,
      kind = (document.getElementById("sc-vkind") || {}).value;
    const r = base.apply(this, arguments);
    try {
      const v = isNew ? (DB.vendors || []).length > n && DB.vendors[DB.vendors.length - 1] : (DB.vendors || []).find((x) => x.id === (editing || {}).id);
      isNew && v && !v.createdBy && ((v.createdBy = scMe()), (v.createdAt = appNowIso()));
      if (v && null != kind) {
        const was = v.kind || "";
        kind ? (v.kind = kind) : delete v.kind;
        was !== (v.kind || "") && audit("vendor", v.id, "kind", was, v.kind || "auto", "");
        save();
      }
    } catch (e) {}
    return r;
  };
}
{
  const base = openVendor;
  openVendor = function (id) {
    const r = base.apply(this, arguments);
    try {
      const v = id ? (DB.vendors || []).find((x) => x.id === id) : null,
        body = document.getElementById("d-body");
      if (!body) return r;
      // the kind: a sub is a first-class kind of vendor (pay applications, retainage, waivers, the papers)
      if (!body.querySelector("#sc-vkind")) {
        const k = document.createElement("div");
        (k.className = "f sc-vkind"),
          (k.innerHTML = `<label>Kind</label><select id="sc-vkind"><option value="">Read from the Trade</option><option value="sub" ${v && "sub" === v.kind ? "selected" : ""}>Subcontractor</option><option value="supplier" ${v && "supplier" === v.kind ? "selected" : ""}>Supplier</option></select>`);
        const first = body.querySelector(".f2");
        first ? first.after(k) : body.prepend(k);
      }
      // the call-back: shown to the owner and the controller, never to the person who asked for the change
      const ex = v && v.bankPending && [...body.querySelectorAll(".exc")].find((x) => /Pending change/.test(x.textContent));
      if (ex) {
        ex.querySelectorAll("#bank-verify, #bank-reject").forEach((x) => x.remove());
        const can = ["owner", "controller"].includes(role()) && scLow(v.bankPending.by) !== scLow(scMe());
        ex.insertAdjacentHTML(
          "beforeend",
          can
            ? '<div class="row" style="margin-top:6px;gap:8px"><button type="button" class="btn sm" id="sc-bank-verify">Verify by Phone</button><button type="button" class="btn sm danger" id="sc-bank-reject">Reject</button></div>'
            : `<div class="small muted" style="margin-top:6px">Every payment to ${esc(v.name)} is held until ${scLow(v.bankPending.by) === scLow(scMe()) ? "someone other than you" : "the owner or the controller"} calls them at the number on file.</div>`,
        );
        body.querySelector("#sc-bank-verify") && (body.querySelector("#sc-bank-verify").onclick = () => scCallBackSheet(v));
        body.querySelector("#sc-bank-reject") && (body.querySelector("#sc-bank-reject").onclick = () => scBankReject(v));
      }
    } catch (e) {
      console.warn("vendor kind and call-back", e);
    }
    return r;
  };
}
// a bank change entered on the vendor is recorded with who asked and how, and holds every payment
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("#bank-request") : null;
    if (!b || !editing || "vendor" !== editing.kind || !editing.id) return;
    e.preventDefault(), e.stopPropagation();
    const v = (DB.vendors || []).find((x) => x.id === editing.id),
      name = ((document.getElementById("e-bankname") || {}).value || "").trim(),
      l4 = ((document.getElementById("e-banklast4") || {}).value || "").trim();
    if (!v) return;
    if (!/^\d{4}$/.test(l4)) return toast("The new account's last four digits");
    scBankRequest(v, { name: name, last4: l4, via: "entered by " + scMe() });
    openVendor(v.id);
    rcToast(`${v.name}'s bank change is held: no payment goes to it until someone other than you calls ${v.name} at the number on file`, [{ label: "Open", run: () => vendorPage(v.id) }]);
  },
  !0,
);
// the vendor page: its subcontracts and the per-job ledger, and the bank's history
{
  const base = vendorPageHtml;
  vendorPageHtml = function (v) {
    let h = base.apply(this, arguments);
    try {
      const rows = scLedgerRows().filter((L) => scLow(L.vendor) === scLow(v.name)),
        log = (v.bankLog || []).slice(-4).reverse(),
        card = `<div class="card sc-vledger"><div class="hd"><h3>By Job</h3><span class="small muted">contract, billed, paid, retainage and what is left, job by job${scIsSub(v) ? "; work in place as the site measured it" : ""}</span></div>${scLedgerHtml(rows) || '<div class="empty">No order or bill with this vendor yet.</div>'}${
          log.length
            ? `<h4 class="sc-h4">Bank Details History</h4><ul class="sc-banklog small">${log.map((x) => (x.rejected ? `<li>${esc(scDay(x.at))}: a change to ····${esc((x.asked || {}).last4 || "")} rejected by ${esc(x.by)}</li>` : `<li>${esc(scDay(x.at))}: ····${esc((x.from || {}).last4 || "none")} to ····${esc((x.to || {}).last4 || "")}, asked by ${esc(x.requestedBy || "")}, confirmed by phone by ${esc(x.verifiedBy)} (${esc(x.phone)}, ${esc(x.spokeWith)})</li>`)).join("")}</ul>`
            : ""
        }</div>`,
        at = h.lastIndexOf("</div>");
      h = at > 0 ? h.slice(0, at) + card + h.slice(at) : h + card;
    } catch (e) {
      console.warn("vendor ledger", e);
    }
    return h;
  };
}
// One question, one number: a vendor's "paid to date" (the vendor list, its tile, the vendor page) is the ledger's paid
// (every payment of their bills by any method, bank lines matched to their orders) plus bank and card lines to them
// that no bill, payment or order holds. It read bank lines whose words held the vendor's first word, so Brooklyn
// Stair Works was "paid" a Brooklyn print shop's card charge and none of its own check payments.
function scVendorPaid(v) {
  if (!v || !v.name) return 0;
  const L = scLedger(v.name, ""),
    n = scLow(v.name),
    held = new Set((DB.payments || []).map((p) => p.txnId).filter(Boolean));
  (DB.pos || []).forEach((po) => (po.matchedTxns || []).forEach((id) => held.add(id)));
  const loose = (DB.txns || []).filter((t) => +t.amt < 0 && !t.billId && !held.has(t.id) && !["transfer", "cc-payment"].includes(t.cat) && (scLow(t.vendor) === n || scLow(t.desc).replace(/[^a-z0-9 ]/g, " ").includes(n.replace(/[^a-z0-9 ]/g, " "))));
  return r2(L.paid + loose.reduce((a, t) => a - +t.amt, 0));
}
{
  const base = vendorSpend;
  vendorSpend = function (v) {
    try {
      return scVendorPaid(v);
    } catch (e) {
      return base.apply(this, arguments);
    }
  };
}
// the subcontract card on its PO page
{
  const base = renderPODoc;
  renderPODoc = function (po) {
    const h = base.apply(this, arguments);
    try {
      if (po && scIsSubcontract(po) && "string" == typeof h && !["foreman", "crew", "driver", "client"].includes(role())) return h + scCardHtml(po);
    } catch (e) {
      console.warn("subcontract card", e);
    }
    return h;
  };
}
document.addEventListener(
  "click",
  (e) => {
    const x = e.target && e.target.closest ? e.target.closest("[data-sc], [data-scbill]") : null;
    if (!x) return;
    const card = x.closest("[data-scpo]"),
      po = card && (DB.pos || []).find((p) => p.id === card.dataset.scpo);
    if (!po) return;
    e.preventDefault(), e.stopPropagation();
    if (x.dataset.scbill) {
      const b = (DB.bills || []).find((y) => y.id === x.dataset.scbill);
      return b && (flowCan("ap") ? flowGo.bill(b)() : toast(`${b.number || "The bill"} is on Bills & Payroll`));
    }
    const k = x.dataset.sc;
    "terms" === k ? scTermsSheet(po) : "change" === k ? scChangeSheet(po) : "payapp" === k ? scPayAppSheet(po) : "approve-change" === k && scApproveChange(po, x.dataset.scc);
  },
  !0,
);
// the PO's bill button on a subcontract reads as what it does
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      if ("po" === view && "undefined" != typeof poOpen && poOpen) {
        const po = (DB.pos || []).find((x) => x.id === poOpen);
        po &&
          scIsSubcontract(po) &&
          document.querySelectorAll('.view.on [data-poact="bill"]').forEach((b) => {
            (b.textContent = "New Pay Application"), (b.disabled = !1), (b.title = "The sub's claim, line by line, beside the work measured on site");
          });
      }
    } catch (e) {}
    return r;
  };
}
// the bill: its pay application, the Payment Check and its lien waivers, at the top of the sheet
function scPayAppHtml(b) {
  const P = b.payApp,
    po = scPOOf(b);
  if (!P || !po) return "";
  return `<div class="card sc-pa-card"><div class="pc-hd"><h4>Pay Application ${esc(P.no)} · ${esc(po.number)}</h4><button type="button" class="btn sm" data-pareview>Lines and the Site</button></div><div class="small muted">Work through ${esc(scDay(P.periodTo))}. ${(P.lines || []).map((l) => `${esc(l.desc)}: ${Math.round(+l.prevPct || 0)}% to ${Math.round(+l.pct || 0)}%`).join(" · ")}</div>${P.revised ? `<div class="small">Approved at measured by ${esc(P.revised.by)}: ${money(P.revised.approved)} of ${money(P.revised.claimed)} claimed; ${money(P.revised.diff)} goes to the next application.</div>` : ""}${P.asClaimed ? `<div class="small warn-t">Approved as claimed by ${esc(P.asClaimed.by)}: ${esc(P.asClaimed.why)}</div>` : ""}</div>`;
}
function pcStampHtml(b) {
  const P = (DB.payments || []).filter((p) => p.billId === b.id && !p.void && p.check);
  return P.length
    ? `<div class="card pc-card pc-pass"><div class="pc-hd"><h4>Payment Check</h4><span class="pill ok">Checked at Release</span></div>${P.map((p) => `<div class="small">${money(p.amount)} ${esc(scDay(p.date))} by ${esc(p.method)}: ${p.check.checked.length} points checked by ${esc(p.check.by)}${p.check.released.length ? `; released: ${esc(p.check.released.map((x) => `${x.what} (${x.by}: ${x.why})`).join("; "))}` : ""}</div>`).join("")}</div>`
    : "";
}
function scBillDrawer(id) {
  const b = (DB.bills || []).find((x) => x.id === id),
    body = document.getElementById("d-body");
  if (!b || !body || body.querySelector(".pc-wrap")) return;
  let h = scPayAppHtml(b),
    R = null;
  if (["submitted", "pm-approved", "approved"].includes(b.status) && billTotal(b) > 0 && pcOpen(b) > 0.005) {
    R = pcCheck(b);
    const pre = "approved" !== b.status;
    pre && ((R.holds = R.holds.filter((h0) => "approval" !== h0.key)), (R.pass = !R.holds.length));
    h += pcHtml(R, { noRelease: pre }).replace("<h4>Payment Check</h4>", pre ? "<h4>Payment Check Before Approval</h4>" : "<h4>Payment Check</h4>");
  } else h += pcStampHtml(b);
  h += wvHtml(b);
  if (!h) return;
  const wrap = document.createElement("div");
  (wrap.className = "pc-wrap"), (wrap.innerHTML = h), body.prepend(wrap);
  const again = () => {
    "function" == typeof closeEditor && closeEditor();
    openBill(b.id);
  };
  R && pcWire(wrap, b, R, again);
  wrap.querySelectorAll("[data-wvadd]").forEach((x) => (x.onclick = () => wvSheet(b, { after: again })));
  wrap.querySelectorAll("[data-pareview]").forEach((x) => (x.onclick = () => scPayAppReview(b)));
}
{
  const base = openBill;
  openBill = function (id) {
    const r = base.apply(this, arguments);
    try {
      scBillDrawer(id);
    } catch (e) {
      console.warn("payment check on the bill", e);
    }
    return r;
  };
}
// Bills & Payroll: the payment run. Approved bills, each with its check; only the checked ones are paid.
// What a Payment Run may hold: approved, an open balance after every payment and every bank line matched to it,
// not held. One rule for the run card, preparing a run and releasing it.
function pcRunnable(b) {
  return !!(
    b &&
    "approved" === b.status &&
    !b.ic &&
    billTotal(b) > 0 &&
    pcOpen(b) > 0.005 &&
    !(b.onHold && "open" === b.onHold.state) &&
    !("function" == typeof billPaidTxn && billPaidTxn(b))
  );
}
function pcRunHtml() {
  const B = (DB.bills || []).filter(pcRunnable);
  if (!B.length) return "";
  const rows = B.map((b) => ({ b: b, R: pcCheck(b) }));
  const n = rows.filter((x) => x.R.pass).length;
  return `<div class="card pc-run" id="pc-run"><div class="hd"><h3>Payment Run</h3><span class="small muted">approved bills, each checked before money leaves: ${n} of ${rows.length} pass</span></div><div class="tw"><table class="t"><thead><tr><th style="width:44px"></th><th>Vendor</th><th>Bill</th><th class="money">To Pay</th><th>Payment Check</th></tr></thead><tbody>${rows
    .map(
      (x) =>
        `<tr><td><input type="checkbox" aria-label="Pay ${esc(x.b.vendor)} ${esc(x.b.number || "")}" data-pcrun="${esc(x.b.id)}" ${x.R.pass ? "checked" : "disabled"}></td><td><b>${esc(x.b.vendor)}</b><div class="small muted">${esc(scJob(x.b.projectId))}</div></td><td>${esc(x.b.number || "")}</td><td class="money">${money(x.R.amount)}</td><td class="small">${x.R.pass ? `<span class="pill ok">Checked · ${x.R.ok.length + x.R.released.length}</span>` : `<span class="pill bad">Held · ${x.R.holds.length}</span> ${esc(x.R.holds[0].what)}`} <a href="#" data-pcopen="${esc(x.b.id)}">Review</a></td></tr>`,
    )
    .join("")}</tbody></table></div><div class="row" style="margin-top:8px"><button type="button" class="btn" id="pc-run-go" ${n ? "" : "disabled"}>Pay the Checked Bills</button></div></div>`;
}
function pcRunSheet(ids) {
  const B = ids.map((id) => (DB.bills || []).find((b) => b.id === id)).filter(Boolean);
  if (!B.length) return toast("Tick the bills to pay");
  const ents = [...new Set(B.map((b) => b.entityId || entDefault()))],
    total = r2(B.reduce((a, b) => a + pcOpen(b), 0));
  mbModal(
    "Pay the Checked Bills",
    `<p class="small muted" style="margin:0 0 8px">${B.length} bill${B.length > 1 ? "s" : ""}, ${money(total)}. Each is checked again as it is paid; one that no longer passes stays unpaid and says why.</p>${ents
      .map((e) => {
        const A = entAccountsOf(e);
        return mbF(`From (${esc(glEntName(e))})`, A.length ? mbSel("acct_" + e, A.map((a) => [a.id, `${a.name}${a.last4 ? " ····" + a.last4 : ""}`]), A[0].id) : '<span class="small bad-t">no account for this entity</span>');
      })
      .join("")}<div class="grid2">${mbF("Date", mbIn("date", today(), "", "date"))}${mbF("Method", mbSel("method", [["", "Each Bill's Own Method"], ["ACH", "ACH"], ["Check", "Check"]], ""))}</div>`,
    {
      submit: "Record the Payments",
      onSubmit: (f) => {
        const run = uid("run"),
          done = [],
          held = [];
        B.forEach((b) => {
          const out = pcRecord(b, { acct: f["acct_" + (b.entityId || entDefault())], date: f.date, amount: pcOpen(b), method: f.method || b.payMethod || "ACH", ref: "" }, { run: run });
          out.err ? held.push(`${b.vendor} ${b.number || ""}: ${out.err}`) : done.push(out.p);
        });
        save(), render();
        rcToast(`${done.length} payment${1 === done.length ? "" : "s"} recorded, ${money(r2(done.reduce((a, p) => a + p.amount, 0)))}, every one checked${held.length ? `; ${held.length} held: ${held.join("; ")}` : ""}`, [{ label: "Open", run: () => ((view = "ap"), render()) }]);
      },
    },
  );
}
{
  const base = renderAP;
  renderAP = function () {
    const r = base.apply(this, arguments);
    try {
      const v = document.getElementById("v-ap");
      if (!v || !["owner", "controller", "billing"].includes(role())) return r;
      v.querySelector("#pc-run") && v.querySelector("#pc-run").remove();
      const h = pcRunHtml();
      if (!h) return r;
      const w = document.createElement("div");
      w.innerHTML = h;
      const card = w.firstChild,
        at = v.querySelector("#ap-table");
      at && at.parentElement ? at.parentElement.insertBefore(card, at) : v.appendChild(card);
      card.querySelectorAll("[data-pcopen]").forEach((a) => (a.onclick = (e) => (e.preventDefault(), pcPaySheet(a.dataset.pcopen))));
      const go = card.querySelector("#pc-run-go");
      go && (go.onclick = () => pcRunSheet([...card.querySelectorAll("[data-pcrun]:checked")].map((x) => x.dataset.pcrun)));
    } catch (e) {
      console.warn("payment run", e);
    }
    return r;
  };
}
// ---- Ask and the query tables -------------------------------------------------------------------------------------
EQ_TABLES.vendorledger = () =>
  scLedgerRows().map((L) => ({
    _id: `${scLow(L.vendor)}|${L.projectId}`,
    _module: "Purchasing",
    _label: `${L.vendor} · ${L.project}`,
    _go: eqGo("vendors", {}),
    vendor: L.vendor,
    project: L.project,
    projectId: L.projectId,
    sub: L.sub,
    contract: L.contract,
    changes: L.changes,
    billed: L.billed,
    paid: L.paid,
    payable: L.payable,
    retainageHeld: L.retainageHeld,
    retainageShort: L.retainageShort,
    creditsOpen: L.creditsOpen,
    balanceToFinish: L.balanceToFinish,
    left: L.left,
    workInPlace: L.inPlace,
    aheadOfWork: L.aheadOfWork,
    waiversMissing: L.waiversMissing.length,
  }));
EQ_TABLES.paymentholds = () =>
  pcHeldBills().map((x) => ({
    _id: x.b.id,
    _module: "Bills & Payroll",
    _label: `Held · ${x.b.vendor} ${x.b.number || ""}`,
    _go: eqGo("ap", {}),
    vendor: x.b.vendor,
    bill: x.b.number || "",
    projectId: x.b.projectId || "",
    project: scJob(x.b.projectId),
    amount: x.R.amount,
    holds: x.R.holds.filter((h) => "approval" !== h.key).map((h) => h.what).join("; "),
    owner: pcNeedsOwner(x),
  }));
EQ_TABLES.waiverrows = () =>
  (DB.bills || [])
    .filter((b) => scLive(b) && scSubBill(b))
    .flatMap((b) => wvList(b).map((w) => ({ b: b, w: w })))
    .map(({ b: b, w: w }) => ({
      _id: `${b.id}:${w.id}`,
      _module: "Reports",
      _label: `${w.type} waiver · ${b.vendor} ${b.number || ""}`,
      _go: eqGo("ap", {}),
      vendor: b.vendor,
      bill: b.number || "",
      projectId: b.projectId || "",
      project: scJob(b.projectId),
      type: w.type,
      scope: w.scope,
      amount: w.amount,
      received: w.received,
    }));
Object.assign(EQ_ALIAS, { subledger: "vendorledger", vendor_ledger: "vendorledger", subcontracts: "vendorledger", heldpayments: "paymentholds", payment_holds: "paymentholds", lien_waiver_rows: "waiverrows" });
["vendorledger", "paymentholds", "waiverrows"].forEach((k) => EQ_MONEY_TABLES.includes(k) || EQ_MONEY_TABLES.push(k));
"undefined" != typeof MD_VIEWS && Object.assign(MD_VIEWS, { vendorledger: ["ap", "vendors", "po", "proc"], paymentholds: ["ap", "mapprove"], waiverrows: ["ap", "vendors"] });
// "what have we paid Tino on 121 State, and what's left?"
AG_FIN.unshift({
  id: "vendorledger",
  re: /\b(left|remaining|retainage|ledger|balance to finish|still to (pay|bill)|what'?s left|to finish|paid (to )?date|paid so far)\b/,
  not: /\b(payroll|clients?|customers?|invoices? to)\b/,
  kind: "money",
  run(P) {
    if (!P.vendors || !P.vendors.length) return null;
    const pid = P.jobs && P.jobs.length ? P.jobs[0].id : "",
      R = P.vendors.map((v) => scLedger(v.name, pid)).filter((L) => L.pos.length || L.bills.length);
    if (!R.length) return { headline: `Nothing on file with ${P.vendors.map((v) => v.name).join(" or ")}${pid ? ` on ${scJob(pid)}` : ""}: no order and no bill.`, work: [], go: agGo("vendors"), ran: agRan("vendor ledger", [`vendor is ${P.vendors.map((v) => v.name).join(" or ")}`].concat(pid ? [`job is ${scJob(pid)}`] : []), "", 0) };
    return {
      headline: R.map(scLedgerSay).join(" "),
      note: "Paid counts every payment of their bills, by any method and from any entity, and bank lines matched straight to their orders.",
      work: R.flatMap((L) => L.bills.map((b) => `${b.number || "bill"} · ${scDay(b.date)} · ${money(billGross(b))} gross · ${billState(b).text || b.status} · paid ${money(scPaidBill(b))}`)),
      go: agGo("vendors"),
      ran: agRan("vendor ledger", [`vendor is ${P.vendors.map((v) => v.name).join(" or ")}`].concat(pid ? [`job is ${scJob(pid)}`] : []), "", R.length),
    };
  },
});
// "what payments are held", "why is the Carlos payment held"
AG_FIN.unshift({
  id: "paymentholds",
  // payments only: "bills on hold" is the order-tracking hold (TRK), answered by its own reader
  re: /\bpayments?\b.*\b(held|on hold|holds?)\b|\b(held|holds?|on hold)\b.*\bpayments?\b|\bpayment check\b/,
  not: /\b(disput|short[- ]?pa)/,
  kind: "money",
  run(P) {
    let H = pcHeldBills();
    P.vendors && P.vendors.length && (H = H.filter((x) => P.vendors.some((v) => scLow(v.name) === scLow(x.b.vendor))));
    const bank = (DB.vendors || []).filter((v) => v.bankPending && (!P.vendors || !P.vendors.length || P.vendors.some((x) => x.id === v.id)));
    return {
      headline: H.length || bank.length
        ? `${H.length ? `${agN(H.length, "payment")} held, ${money(r2(H.reduce((a, x) => a + x.R.amount, 0)))}: ${H.map((x) => `${x.b.vendor} ${x.b.number || ""} (${x.R.holds.filter((h) => "approval" !== h.key).map((h) => h.what).join("; ")})`).join("; ")}.` : ""}${bank.length ? ` ${bank.map((v) => `${v.name}'s bank change waits on a call-back`).join("; ")}.` : ""}`.trim()
        : "No approved payment is held: every approved bill passes its payment check.",
      work: H.map((x) => `${x.b.vendor} ${x.b.number || ""} · ${money(x.R.amount)} · ${x.R.holds.map((h) => h.what).join(" · ")}`),
      go: agGo("mapprove"),
      ran: agRan("payment holds", ["approved, money still to pay, the payment check holds it (pcCheck)"], "", H.length),
    };
  },
});

// ---- the demo's one subcontract, written as a subcontract -----------------------------------------------------------
// Carlos Millwork's PO-2026-048 on 121 State: its scope and terms (no money moves). Demo only, never on live data.
function scSeed() {
  if ("function" == typeof sdSeedsOff && sdSeedsOff()) return;
  if (DB.__scSeed) return;
  const po = (DB.pos || []).find((x) => "po4" === x.id && "Carlos Millwork" === x.vendor && scIsSubcontract(x));
  DB.__scSeed = 1;
  if (!po || po.sc) return;
  po.sc = {
    scope: "Fabricate, deliver and install the parlor kitchen and laundry millwork to the shop drawings, finished in place.",
    inclusions: ["Boxes, doors and drawer fronts, finished", "Installation and scribe to the walls", "Hardware install (hardware by the owner)"],
    exclusions: ["Countertops", "Appliances and their hook-ups", "Plumbing and electrical"],
    signedOn: "2026-07-28",
    signedBy: "Owner",
    retainageAt: "substantial completion",
    changes: [],
  };
}
{
  const base = finishBoot;
  finishBoot = function () {
    const r = base.apply(this, arguments);
    try {
      scSeed();
    } catch (e) {
      console.warn("subcontract seed", e);
    }
    return r;
  };
}
/*<</subs.js>>*/

// ---- 9. Who releases the run (Alan, 2026-10-20: "Go" on the recommendation) --------------------------------------
// The controller keys every bill, and whoever keys a bill can never release its payment, so the controller could pay
// almost nothing. Decided: the controller keys, matches and prepares the weekly Payment Run; the owner releases it in
// one tap; billing releases it when the owner has marked himself away. A prepared run is a record (DB.payRuns) because
// it waits across days and must be findable by both people: in the owner's Approvals (kind "payrun") and on the run
// card. Releasing records each bill through pcRecord as the releaser, so every bill is checked again at that moment.
const prStore = () => (Array.isArray(DB.payRuns) ? DB.payRuns : (DB.payRuns = [])),
  prOpen = () => prStore().filter((x) => "prepared" === x.status),
  prAway = () => {
    const a = (DB.company || {}).ownerAway;
    return !!(a && a.from <= today() && (!a.to || a.to >= today()));
  },
  prReleaser = () => (prAway() ? "billing" : "owner"),
  prCanRelease = () => role() === prReleaser() || ("owner" === role() && !prAway()),
  prBills = (run) => run.bills.map((x) => ({ x: x, b: (DB.bills || []).find((b) => b.id === x.id) })).filter((y) => y.b);
function prPrepareSheet(ids) {
  const B0 = ids.map((id) => (DB.bills || []).find((b) => b.id === id)).filter(Boolean),
    B = B0.filter(pcRunnable),
    out = B0.filter((b) => !pcRunnable(b));
  if (out.length) toast(`Left out of the run: ${out.map((b) => `${b.vendor} ${b.number || ""} (${b.onHold && "open" === b.onHold.state ? "held" : "already paid or not approved"})`).join(", ")}`);
  if (!B.length) return out.length ? void 0 : toast("Tick the bills to put in the run");
  const ents = [...new Set(B.map((b) => b.entityId || entDefault()))],
    total = r2(B.reduce((a, b) => a + pcOpen(b), 0)),
    who = prAway() ? "billing (the owner is away)" : "the owner";
  mbModal(
    "Prepare the Payment Run",
    `<p class="small muted" style="margin:0 0 8px">${B.length} bill${B.length > 1 ? "s" : ""}, ${money(total)}. It goes to ${who} to release in one tap; each bill is checked again then.</p>${ents
      .map((e) => {
        const A = entAccountsOf(e);
        return mbF(`From (${esc(glEntName(e))})`, A.length ? mbSel("acct_" + e, A.map((a) => [a.id, `${a.name}${a.last4 ? " ····" + a.last4 : ""}`]), A[0].id) : '<span class="small bad-t">no account for this entity</span>');
      })
      .join("")}<div class="grid2">${mbF("Pay On", mbIn("date", today(), "", "date"))}${mbF("Method", mbSel("method", [["", "Each Bill's Own Method"], ["ACH", "ACH"], ["Check", "Check"]], ""))}</div>`,
    {
      submit: "Send to Release",
      onSubmit: (f) => {
        const run = {
          id: uid("prun"),
          status: "prepared",
          bills: B.map((b) => ({ id: b.id, amount: pcOpen(b), acct: f["acct_" + (b.entityId || entDefault())] || "" })),
          date: f.date || today(),
          method: f.method || "",
          total: total,
          preparedBy: scMe(),
          preparedAt: appNowIso(),
        };
        prStore().push(run);
        try {
          audit("payrun", run.id, "prepared", "", money(total), `${B.length} bills for ${prReleaser()}`);
        } catch (e) {}
        save(), render();
        rcToast(`Payment Run of ${money(total)} (${B.length} bill${B.length > 1 ? "s" : ""}) sent to ${prAway() ? "billing" : "the owner"} to release`, [{ label: "Open", run: () => ((view = "ap"), render()) }]);
      },
    },
  );
}
// Release: each bill recorded by the releaser, checked again now; a bill that no longer passes stays unpaid and says why
function prRelease(id) {
  const run = prStore().find((x) => x.id === id);
  if (!run || "prepared" !== run.status) return toast("That run is not waiting to be released");
  if (!prCanRelease()) return toast(`${prAway() ? "Billing" : "The owner"} releases a prepared run`);
  const done = [],
    held = [];
  prBills(run).forEach(({ x, b }) => {
    const amount = Math.min(x.amount, pcOpen(b));
    if (amount <= 0.005) return void held.push(`${b.vendor} ${b.number || ""}: already paid`);
    const out = pcRecord(b, { acct: x.acct, date: run.date, amount: amount, method: run.method || b.payMethod || "ACH", ref: "" }, { run: run.id });
    out.err ? held.push(`${b.vendor} ${b.number || ""}: ${out.err}`) : done.push(out.p);
  });
  Object.assign(run, { status: "released", releasedBy: scMe(), releasedAt: appNowIso(), paid: r2(done.reduce((a, p) => a + p.amount, 0)), held: held });
  try {
    audit("payrun", run.id, "released", "", money(run.paid), held.length ? `${held.length} held` : "all paid");
  } catch (e) {}
  save(), render();
  rcToast(`Payment Run released: ${done.length} payment${1 === done.length ? "" : "s"}, ${money(run.paid)}, every one checked${held.length ? `; ${held.length} held: ${held.join("; ")}` : ""}`, [{ label: "Open", run: () => ((view = "ap"), render()) }]);
}
function prReturn(id) {
  const run = prStore().find((x) => x.id === id);
  if (!run || "prepared" !== run.status) return;
  mbModal("Return the Run", `<p class="small muted" style="margin:0 0 8px">${money(run.total)}, prepared by ${esc(run.preparedBy)}. Say what to change; nothing is paid.</p>${mbF("Why", mbIn("why", "", "e.g. hold Window Works until the credit lands"))}`, {
    submit: "Return It",
    onSubmit: (f) => {
      if (!f.why) return toast("Say why, so it can be fixed"), !1;
      Object.assign(run, { status: "returned", returnedBy: scMe(), returnedAt: appNowIso(), why: f.why });
      try {
        audit("payrun", run.id, "returned", "", "", f.why);
      } catch (e) {}
      save(), render();
      toast(`Run returned to ${run.preparedBy}: ${f.why}`, () => ((view = "ap"), render()));
    },
  });
}
// The owner marks himself away: billing releases runs until the date he sets
function prAwaySheet() {
  const a = (DB.company || {}).ownerAway;
  if (prAway()) {
    try {
      audit("company", "ownerAway", "ended", `${a.from} to ${a.to}`, today(), "back early");
    } catch (e) {}
    return delete DB.company.ownerAway, save(), render(), toast("Back: you release Payment Runs again", () => ((view = "ap"), render()));
  }
  mbModal("Away: Billing Releases Runs", `<p class="small muted" style="margin:0 0 8px">While you are away, billing releases prepared Payment Runs. Every bill is still checked, and the holds above your limit still wait for you.</p><div class="grid2">${mbF("From", mbIn("from", today(), "", "date"))}${mbF("Back On", mbIn("to", "", "", "date"))}</div>`, {
    submit: "Set Away",
    onSubmit: (f) => {
      if (!f.to) return toast("Say when you are back"), !1;
      DB.company.ownerAway = { from: f.from || today(), to: f.to, by: scMe(), at: appNowIso() };
      try {
        audit("company", "ownerAway", "set", "", `${f.from} to ${f.to}`, "billing releases Payment Runs");
      } catch (e) {}
      save(), render();
      toast(`Away ${fmtL(f.from || today())} to ${fmtL(f.to)}: billing releases Payment Runs`, () => ((view = "ap"), render()));
    },
  });
}
// the run card: prepared runs on top; the controller prepares, the owner (or billing when he is away) releases
function prCardHtml() {
  const P = prOpen(),
    R = prStore().filter((x) => "returned" === x.status && !x.seen).slice(-3),
    rel = prCanRelease();
  const row = (run) =>
    `<div class="row wrap pr-row" data-prun="${esc(run.id)}" style="gap:8px;align-items:center;padding:8px 0;border-top:1px solid var(--rule)"><div class="grow"><b>Payment Run · ${money(run.total)}</b><div class="small muted">${run.bills.length} bill${1 === run.bills.length ? "" : "s"} · pay on ${fmtL(run.date)} · prepared by ${esc(run.preparedBy)} ${esc(stampText(run.preparedAt))} · waiting for ${prAway() ? "billing (the owner is away)" : "the owner"}</div></div>${rel ? `<button type="button" class="btn" data-prrel="${esc(run.id)}">Release ${money(run.total)}</button><button type="button" class="btn" data-prret="${esc(run.id)}">Return</button>` : ""}</div>`;
  return `${P.map(row).join("")}${R.map((run) => `<div class="note warn small" data-prseen="${esc(run.id)}">Run of ${money(run.total)} returned by ${esc(run.returnedBy)}: ${esc(run.why)}</div>`).join("")}${"owner" === role() ? `<div class="row" style="margin-top:6px"><button type="button" class="btn sm" data-praway>${prAway() ? `Away to ${fmtL(DB.company.ownerAway.to)}: I Am Back` : "Away: Billing Releases Runs"}</button></div>` : ""}`;
}
{
  const base = renderAP;
  renderAP = function () {
    const r = base.apply(this, arguments);
    try {
      const v = document.getElementById("v-ap"),
        card = v && v.querySelector("#pc-run");
      if (!v || !["owner", "controller", "billing"].includes(role())) return r;
      const go = card && card.querySelector("#pc-run-go");
      // whoever is not the releaser prepares the run instead of paying it
      if (go && !prCanRelease()) {
        go.textContent = "Prepare the Run";
        go.onclick = () => prPrepareSheet([...card.querySelectorAll("[data-pcrun]:checked")].map((x) => x.dataset.pcrun));
      }
      const extra = prCardHtml();
      if (extra) {
        let host = card;
        if (!host) {
          host = document.createElement("div");
          host.className = "card pc-run";
          host.id = "pc-run";
          host.innerHTML = `<div class="hd"><h3>Payment Run</h3></div>`;
          const at = v.querySelector("#ap-table");
          at && at.parentElement ? at.parentElement.insertBefore(host, at) : v.appendChild(host);
        }
        const w = document.createElement("div");
        w.className = "pr-runs";
        w.innerHTML = extra;
        host.querySelector(".hd").after(w);
        w.querySelectorAll("[data-prrel]").forEach((b) => (b.onclick = () => prRelease(b.dataset.prrel)));
        w.querySelectorAll("[data-prret]").forEach((b) => (b.onclick = () => prReturn(b.dataset.prret)));
        w.querySelectorAll("[data-praway]").forEach((b) => (b.onclick = () => prAwaySheet()));
        w.querySelectorAll("[data-prseen]").forEach((n) => {
          const run = prStore().find((x) => x.id === n.dataset.prseen);
          run && run.preparedBy === scMe() && (run.seen = appNowIso());
        });
      }
    } catch (e) {
      console.warn("payment run release", e);
    }
    return r;
  };
}
// Approvals: a prepared run is one card for the releaser, released in one tap
STD_MAP.payrun = { p: "integrity", c: ["pb", "office", "standards", /Three-way match/i] };
APPR_CHIPS.splice(
  APPR_CHIPS.findIndex(([k]) => "other" === k),
  0,
  ["payrun", "Payment Runs"],
);
DELEGATION.payrun = {
  role: "owner",
  rule: "the controller prepares the weekly Payment Run and the owner releases it in one tap; billing releases it while the owner is away (Alan, 2026-10-20)",
  who: () => prReleaser(),
};
{
  const base = mApprovals;
  mApprovals = function (opts) {
    const out = base.apply(this, arguments);
    try {
      if (!Array.isArray(out)) return out;
      const add = prOpen().map((run) => ({
        kind: "payrun",
        id: run.id,
        sev: "warn",
        n: money(run.total),
        title: `Payment Run · ${run.bills.length} bill${1 === run.bills.length ? "" : "s"}`,
        detail: `prepared by ${run.preparedBy} · pay on ${fmtL(run.date)} · each bill is checked again as it is paid`,
        yes: "Release",
        no: "Return",
        act: "release",
        open: { view: "ap" },
      }));
      add.forEach((it) => (it.who = apprOwner(it)));
      return out.concat(opts && opts.everyone ? add : add.filter((it) => it.who === role()));
    } catch (e) {
      console.warn("payment runs", e);
      return out;
    }
  };
}
{
  const base = renderMApprove;
  renderMApprove = function () {
    const r = base.apply(this, arguments);
    try {
      document.querySelectorAll('#v-mapprove .m-appr[data-mk="payrun"]').forEach((el) => {
        const y = el.querySelector("[data-myes]"),
          n = el.querySelector("[data-mno]"),
          id = el.dataset.mid;
        y && (y.onclick = (e) => (e.preventDefault(), e.stopPropagation(), prRelease(id)));
        n && (n.onclick = (e) => (e.preventDefault(), e.stopPropagation(), prReturn(id)));
      });
    } catch (e) {}
    return r;
  };
}
{
  const base = tdCard;
  tdCard = function (it) {
    const c = base.apply(this, arguments);
    try {
      if (it && "payrun" === it.kind) {
        c.line1 = `Payment Run · ${esc(it.n)} · prepared by ${esc(String(it.detail).split(" · ")[0].replace(/^prepared by /, ""))}`;
        c.why = "each bill is checked again as it is paid";
        c.verb = "Release";
        c.run = () => prRelease(it.id);
        c.go = () => ((view = "ap"), render());
      }
    } catch (e) {}
    return c;
  };
}
{
  const base = tdScore;
  tdScore = function (it) {
    if (it && "payrun" === it.kind) return 58;
    return base.apply(this, arguments);
  };
}
