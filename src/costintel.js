// =====================================================================================================================
// Cost intelligence (BACKLOG §1.29 items 1 to 5, §1.31's price-book and route tests; lane "costintel", 2026-10-20).
// Alan, 2026-10-17: founder, controller, PM and operations all see it. "Every dollar matters."
//
// Design gate (§1.16). What this extends, and the two things it adds with their reason:
//  - Jobs spending more than they bring in: one predicate, PRED.jobsOverspending (label "Jobs Spending More Than They
//    Bring In"), one row per job. Its over-budget part IS the existing rule (ovsAll, the overspend-at-landing reader the
//    Caught for You "Over Budget" entry already reads); it adds cash out above cash in, cost ahead of billings and a
//    line forecast to go over (committed past its budget, or measured progress that projects past it). Caught for You
//    gets one CATCH entry (jobCash) for the parts Over Budget does not carry, so nothing is counted twice. The list is
//    Reports › Projects › Cost Intelligence; Ask and ⌘K read the same rows.
//  - Benchmarks: read from the jobs' own records (price history buys on the job, its measures) and from close-outs.
//    NEW STORE DB.closeouts, reason: a closed job's measures (fixtures, devices, boards, SF, LF) and what each rough
//    trade bought and installed, frozen at close so a later edit or an archive never moves the benchmark. Past jobs
//    that predate the ERP exist nowhere else. It holds no live price: the item price history stays the one history
//    (price watch, pwData). A job's measures ride on the project (p.project.measures), not in a store.
//    Feeding estimating is a drafted change in Company › Changes (DB.changes, the improvement loop's one list); only the
//    owner's approval writes DB.company.costBook.bench. One price path for estimating: DB.company.costBook is the one
//    store of what new estimates carry (the reports lane's close-out factors by cost code, and these benchmarks under
//    its "bench" key); ciCostGuide is the one reader, used by the estimate editor's hints and the item library's fill.
//  - Receipt price book: no new store. Receipt lines already read by the app (DB.docs kind "receipt", the field's
//    receipts DB.spend[].read.lines) join the ONE price history through a pwBuild wrapper (kind "receipt"); items
//    match across stores through pwMake's identity (UPC, then a normalised spec: size, gauge, length, pack, variant).
//    One new price watch detector, pwStoreCheaper ("Cheaper at Another Store"), registered like every PW_DET entry.
//    The page is RFQs › Price Watch, which gains a Receipt Price Book card. Retailer purchase-history imports become
//    receipt documents (DB.docs), never a parallel table.
//  - Driver routes: the noun is the store run (DB.storeRuns). A planned route is a run in status "planned" →
//    "approved" (coordinator) → then the existing "open" / "closed". planDriverDay keeps being the one route the
//    driver's Route screen and its Navigate links read.
//  - The brain's weekly review: proposals go to Company › Changes (DB.changes) with a dollar or hour value; approved
//    rules and processes become lessons (DB.lessons), code becomes a build request. No new queue.
//  - Savings: rows pushed to window.SV_SOURCES (the savings lane's registry), never a ledger here.
// Field roles (foreman, crew, driver) never see a price: the driver sees which store to buy at and the saving on his
// own pickup list, nothing else.
// =====================================================================================================================
const CI_FIELD = ["foreman", "crew", "driver"],
  ciRole = () => {
    try {
      return role();
    } catch (e) {
      return "";
    }
  },
  ciIsField = () => CI_FIELD.includes(ciRole()),
  ciCan = (v) => {
    try {
      return (ROLE_VIEWS[ciRole()] || []).includes(v);
    } catch (e) {
      return !1;
    }
  },
  ciMe = () => ((typeof currentUser == "function" && currentUser()) || {}).name || ciRole(),
  ciR4 = (x) => Math.round((+x || 0) * 1e4) / 1e4,
  ciPct = (a, b) => (b ? Math.round(((a - b) / b) * 1000) / 10 : 0),
  ciJobName = (pid) => {
    const p = (DB.projects || []).find((x) => x.id === pid);
    return p ? shortName(p) : "";
  },
  CI_MONEY_LINE = "Money wasted cannot go to raises, bonuses, more staff, charity or extra value for the client.",
  CI_ICON_ROUTE = ICON_SVG('<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h8a3 3 0 0 0 0-6H8a3 3 0 0 1 0-6h8"/>', 14),
  CI_ICON_TAG = ICON_SVG('<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/>', 13);
function ciMedian(a) {
  const s = a.filter((x) => null != x && isFinite(x)).slice().sort((x, y) => x - y),
    n = s.length;
  return n ? (n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2) : null;
}
const ciMoney = (v) => money(r2(v));
const ciCents = (v) => {
  const n = r2(v);
  return (n < 0 ? "−" : "") + "$" + Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

// ---------------------------------------------------------------------------------------------------------------------
// 1. Stores: the one store list (STORES, the driver's "I'm at the store" list) gains the chain each belongs to, and the
//    supply house and lumber yard the firm buys from. A receipt's store resolves to one of these.
// ---------------------------------------------------------------------------------------------------------------------
const CI_CHAINS = [
  { id: "homedepot", n: "Home Depot", kind: "big box", re: /home ?depot|\bthd\b|\bhd ?pro\b/i },
  { id: "lowes", n: "Lowe's", kind: "big box", re: /lowe'?s/i },
  { id: "lumber", n: "Lumber yard", kind: "lumber yard", re: /lumber|lumberyard/i },
  { id: "supply", n: "Supply house", kind: "supply house", re: /ferguson|supply|supplies|dakota hardware|plumbing supply|electric supply/i },
  { id: "tile", n: "Tile supplier", kind: "supplier", re: /tile|stone/i },
];
(function ciStores() {
  try {
    const add = [
      { n: "Brooklyn Lumber — Red Hook", lat: 40.677, lng: -74.0125 },
      { n: "Quality Building Supply — Park Slope", lat: 40.6726, lng: -73.9851 },
    ];
    add.forEach((s) => STORES.some((x) => x.n === s.n) || STORES.push(s));
    STORES.forEach((s) => {
      const c = CI_CHAINS.find((x) => x.re.test(s.n));
      s.chain = s.chain || (c ? c.id : "other");
      s.id = s.id || s.n.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    });
  } catch (e) {
    console.warn("costintel: stores", e);
  }
})();
// a store number on a receipt names the branch (invented for the demo; a real firm's numbers are learned the same way)
const CI_STORE_NOS = { 1265: "Home Depot — Gowanus", 6166: "Home Depot — Flatbush", 1675: "Lowe's — Gowanus" };
function ciStoreOf(text) {
  const t = String(text || "");
  if (!t.trim()) return null;
  const no = (t.match(/#\s*(\d{3,5})\b/) || [])[1];
  if (no && CI_STORE_NOS[no]) return STORES.find((s) => s.n === CI_STORE_NOS[no]) || null;
  const exact = STORES.find((s) => s.n.toLowerCase() === t.toLowerCase());
  if (exact) return exact;
  const c = CI_CHAINS.find((x) => x.re.test(t));
  if (!c) return null;
  const mine = STORES.filter((s) => s.chain === c.id),
    words = t.toLowerCase().split(/[^a-z]+/).filter((w) => w.length > 3);
  return mine.find((s) => words.some((w) => s.n.toLowerCase().includes(w) && !c.re.test(w))) || mine.find((s) => c.re.test(s.n) && s.n.toLowerCase().startsWith(t.toLowerCase().split(/\s|—|-/)[0])) || mine[0] || null;
}
const ciStoreName = (text) => {
  const s = ciStoreOf(text);
  return s ? s.n : String(text || "").trim();
};
const ciStoreByName = (n) => STORES.find((s) => s.n === n) || null;
const ciIsStore = (vendor) => !!ciStoreByName(vendor) || CI_CHAINS.some((c) => c.re.test(String(vendor || "")));

// ---------------------------------------------------------------------------------------------------------------------
// 2. Item identity across stores. One normalised spec per item: the same 2x4 stud reads "2X4-8 KD STUD SPF" at one
//    store, "2-in x 4-in x 8-ft Kiln-Dried SPF Stud" at another and "2X4 8' KD SPF STUD" at the yard. A spec is only
//    used when it is complete (every attribute that changes the price is named); otherwise the item keeps price
//    watch's own key and a near match stays a proposal a person confirms (pwMatchProps, Same Item?).
// ---------------------------------------------------------------------------------------------------------------------
function ciCanon(desc) {
  let t = " " + String(desc || "").toLowerCase().replace(/[”“″]/g, '"').replace(/[’‘′]/g, "'").replace(/[×]/g, "x").replace(/[–—]/g, "-") + " ";
  t = t
    // "2-in", "8-ft", "250-ft": the unit after a dash
    .replace(/(\d)\s*-\s*(in\.?|inch(?:es)?|ft\.?|feet|foot|gal\.?|lbs?\.?)(?=[\s,x]|$)/g, "$1 $2")
    .replace(/kiln[\s-]*dried|\bk\.?d\.?(?=[\s,])/g, " kd ")
    .replace(/pressure[\s-]*treated|\bp\.?t\.?(?=[\s,])/g, " pt ")
    .replace(/douglas[\s-]*fir|doug[\s-]*fir|\bd\.?f\.?(?=[\s,])|\bdfir\b/g, " df ")
    .replace(/spruce[\s-]*pine[\s-]*fir|\bs-?p-?f\b/g, " spf ")
    .replace(/moisture[\s-]*(?:resistant|res\.?)|mold[\s-]*(?:resistant|tough)|\bm\/r\b|\bmr\b|green ?board/g, " mr ")
    .replace(/fire[\s-]*(?:rated|code|resistant)|type[\s-]*x\b/g, " typex ")
    .replace(/\bromex\b/g, " nmb ")
    .replace(/\bnm[\s-]*b\b/g, " nmb ")
    .replace(/\bpex[\s-]*a\b/g, " pexa ")
    .replace(/\bpex[\s-]*b\b/g, " pexb ")
    .replace(/(\d)\s*(?:in\.?|inch(?:es)?|")(?=[\s\-x,]|$)/g, "$1in ")
    .replace(/(\d)\s*(?:ft\.?|feet|foot|')(?=[\s\-x,]|$)/g, "$1ft ")
    .replace(/(\d)\s*-\s*(\d+\/\d+)/g, "$1-$2")
    .replace(/(\d)\s*(?:gal\.?|gallons?)(?=[\s,]|$)/g, "$1gal ")
    .replace(/(\d)\s*(?:lbs?\.?|pounds?)(?=[\s,]|$)/g, "$1lb ");
  return t.replace(/\s+/g, " ").trim();
}
// a pack size in the words ("10PK", "box of 50", "25 pack")
function ciPack(desc) {
  const m = String(desc || "").match(/\b(\d+)\s*-?\s*(?:pk|pack|ct|count)\b|\b(?:box|pack|case|bag)\s+of\s+(\d+)\b/i);
  return m ? +(m[1] || m[2]) || 0 : 0;
}
const CI_FRAC = { "1/4": 0.25, "3/8": 0.375, "1/2": 0.5, "5/8": 0.625, "3/4": 0.75, "7/8": 0.875 };
const ciFrac = (s) => {
  const m = String(s).match(/^(\d+)-(\d+\/\d+)$/);
  return m ? +m[1] + (CI_FRAC[m[2]] || 0) : CI_FRAC[s] != null ? CI_FRAC[s] : +s;
};
// {key, label, cat} for a complete spec, else null
function ciSpec(desc) {
  const t = ciCanon(desc),
    has = (re) => re.test(t);
  // dimensional lumber: 2x4 with a length (2x4x8, 2x4-8, 2x4 8ft, 2in x 4in x 8ft), kd or pt, species when named
  const dm = t.match(/\b(\d)(?:in)?\s*x\s*(\d{1,2})(?:in)?(?:\s*(?:x|-)\s*(\d{1,3}(?:-\d+\/\d+)?)(ft|in)?|\s+(\d{1,2})ft)\b/);
  if (dm && !has(/\b(drywall|gypsum|sheetrock|plywood|cdx|osb|tile|porcelain|hanger|bracket|angle|screw|nail)\b/)) {
    const a = dm[1],
      b = dm[2],
      lenRaw = dm[3] || dm[5],
      unit = dm[4] || (dm[5] ? "ft" : ""),
      lenN = ciFrac(lenRaw);
    if (lenRaw && +a <= 6 && +b >= 2 && +b <= 12) {
      const ft = "in" === unit || lenN > 24 ? Math.round((lenN / 12) * 1000) / 1000 : lenN,
        treat = has(/\bpt\b/) ? "pt" : "kd",
        // a stud is SPF unless it says otherwise; any other piece of lumber has to name its species
        species = has(/\bdf\b/) ? "df" : has(/\bspf\b/) ? "spf" : has(/\bstuds?\b/) && "2" === a && ["4", "6"].includes(b) ? "spf" : "";
      if (!species) return null;
      return { key: `lumber|${a}x${b}|${ft}ft|${treat}|${species}`, label: `${a}x${b}x${ft} ${treat.toUpperCase()} ${species.toUpperCase()}`, cat: "Lumber", unit: "ea" };
    }
  }
  // sheet goods: plywood and drywall by thickness, size and type
  const thk = (t.match(/(?:^|[^\d/-])(1\/4|3\/8|1\/2|5\/8|3\/4)(?:in)?(?![\d/])/) || [])[1],
    size = (t.match(/\b(4)(?:ft)?\s*x\s*(8|9|10|12)(?:ft)?\b/) || []).slice(1, 3).join("x") || "4x8";
  if (has(/\b(plywood|cdx|osb)\b/) && thk) {
    const g = has(/\bosb\b/) ? "osb" : has(/\bcdx\b/) ? "cdx" : has(/\bbc\b/) ? "bc" : "";
    return g ? { key: `plywood|${thk}|${size}|${g}`, label: `${thk} in ${g.toUpperCase()} plywood ${size}`, cat: "Lumber", unit: "sheet" } : null;
  }
  if (has(/\b(drywall|gypsum|sheetrock|gwb|wallboard)\b/) && !has(/\b(screw|compound|tape|bead|anchor|knife|lift)\b/) && thk) {
    const ty = has(/\btypex\b/) && has(/\bmr\b/) ? "xmr" : has(/\btypex\b/) ? "x" : has(/\bmr\b/) ? "mr" : "reg";
    return { key: `drywall|${thk}|${size}|${ty}`, label: `${thk} in ${{ x: "Type X", mr: "moisture-resistant", xmr: "Type X moisture-resistant", reg: "regular" }[ty]} drywall ${size}`, cat: "Drywall", unit: "sheet" };
  }
  // cable: gauge/conductors and length (12/2 NM-B 250 ft)
  const gm = t.match(/\b(10|12|14)\s*[\/-]\s*(2|3)\b/),
    lenM = t.match(/\b(\d{2,4})\s*ft\b/);
  if (gm && has(/\bnmb\b|\bwire\b|\bcable\b/) && lenM) return { key: `nmb|${gm[1]}/${gm[2]}|${lenM[1]}ft`, label: `${gm[1]}/${gm[2]} NM-B ${lenM[1]} ft`, cat: "Electrical", unit: "roll" };
  // PEX pipe and fittings: type, size, length; colour is a variant at one price
  if (has(/\bpexa\b|\bpexb\b|\bpex\b/)) {
    const ty = has(/\bpexb\b/) ? "b" : "a",
      sz = (t.match(/(?:^|[^\d/-])(1\/2|3\/4|1)in\b/) || t.match(/(?:^|[^\d/-])(1\/2|3\/4)(?![\d/])/) || [])[1];
    if (!sz) return null;
    if (has(/\b(elbow|tee|coupling|adapter|fitting|ring|plug)\b/)) {
      const f = (t.match(/\b(elbow|tee|coupling|adapter|plug)\b/) || ["", "fitting"])[1];
      return { key: `pex${ty}-${f}|${sz}`, label: `${sz} in PEX-${ty.toUpperCase()} ${f}`, cat: "Plumbing" };
    }
    if (lenM && has(/\b(pipe|tubing|coil)\b/)) return { key: `pex${ty}|${sz}|${lenM[1]}ft`, label: `${sz} in PEX-${ty.toUpperCase()} ${lenM[1]} ft`, cat: "Plumbing", unit: "coil" };
    return null;
  }
  // joint compound by kind and size
  if (has(/\bjoint compound\b|\bmud\b|\ball purpose\b/) && has(/\b\d+(?:\.\d+)?gal\b/)) {
    const k = has(/\blightweight|\blite\b/) ? "lightweight" : has(/\bsetting\b|\beasy sand\b/) ? "setting" : "all-purpose",
      g = t.match(/\b(\d+(?:\.\d+)?)gal\b/)[1];
    return { key: `compound|${k}|${g}gal`, label: `${k} joint compound ${g} gal`, cat: "Drywall", unit: "bucket" };
  }
  return null;
}
const ciSpecKey = (desc) => {
  const s = ciSpec(desc);
  return s ? s.key : "";
};

// ---------------------------------------------------------------------------------------------------------------------
// 3. Receipt lines: every receipt the app already reads, at line level (item, SKU, UPC, unit, quantity, unit price,
//    store, date), joined to the one price history.
// ---------------------------------------------------------------------------------------------------------------------
function ciReceiptLines() {
  const out = [],
    seen = new Set();
  const push = (o) => {
    const k = `${o.txnId || o.srcId}|${String(o.item).toLowerCase()}|${o.qty}|${o.price}`;
    if (seen.has(k)) return;
    seen.add(k), out.push(o);
  };
  (DB.docs || []).forEach((d) => {
    if (!d || "receipt" !== d.kind || !trkLive(d) || ["unread", "proposed"].includes(d.status)) return;
    const F = d.fields || {},
      L = d.links || {},
      store = ciStoreName(F.store || F.vendor || ""),
      date = F.date || String(d.at || "").slice(0, 10);
    (F.lines || []).forEach((l, i) => {
      const q = +l.qty || 0,
        ext = +l.ext || 0,
        pr = +l.price || (q ? ext / q : 0);
      if (!(q > 0) || !(pr > 0) || PW_FEE_RE.test(l.item || "")) return;
      push({ id: `rcpt:${d.id}:${i}`, srcId: d.id, src: "doc", docId: d.id, number: F.number || "", store: store, date: date, item: String(l.item || "").replace(/^\d{6,}\s+/, ""), sku: l.sku || (String(l.item || "").match(/^(\d{6,})\s+/) || [])[1] || "", upc: l.upc || "", unit: l.unit || "", qty: q, price: ciR4(pr), ext: r2(ext || q * pr), jobId: L.jobId || "", txnId: L.txnId || "", by: d.by || "" });
    });
  });
  (DB.spend || []).forEach((s) => {
    if (!s || !s.read || ["draft", "void", "rejected"].includes(s.status)) return;
    const store = ciStoreName(s.vendor || s.read.vendor || ""),
      date = s.dateOnPaper || s.date;
    (s.read.lines || []).forEach((l, i) => {
      const q = +l.qty || 0,
        amt = +l.amount || 0,
        pr = +l.unit || (q ? amt / q : 0);
      if (!(q > 0) || !(pr > 0) || PW_FEE_RE.test(l.desc || "")) return;
      push({ id: `rcpt:${s.id}:${i}`, srcId: s.id, src: "spend", spendId: s.id, number: "", store: store, date: date, item: l.desc || "", sku: l.sku || "", upc: "", unit: "", qty: q, price: ciR4(pr), ext: r2(amt || q * pr), jobId: s.projectId || "", txnId: s.txnId || "", by: s.by || "" });
    });
  });
  return out;
}
// The identity: a UPC or a complete spec puts the same item from different stores under one key.
if ("function" == typeof pwMake) {
  const ciPwMakeBase = pwMake;
  pwMake = function (o) {
    const b = ciPwMakeBase.apply(this, arguments);
    if (!b) return b;
    try {
      const sp = ciSpec(b.item),
        upc = String((o && o.upc) || "").replace(/\D/g, "");
      if (sp) (b.rawKey = "spec:" + sp.key), (b.key = pwResolve(b.rawKey)), (b.spec = sp), (b.cat = sp.cat);
      else if (upc.length >= 11) (b.rawKey = "upc:" + upc), (b.key = pwResolve(b.rawKey));
    } catch (e) {}
    return b;
  };
}
if ("function" == typeof pwBuild) {
  const ciPwBuildBase = pwBuild;
  pwBuild = function () {
    const D = ciPwBuildBase.apply(this, arguments);
    try {
      const add = [];
      ciReceiptLines().forEach((r) => {
        const pack = ciPack(r.item),
          sp = ciSpec(r.item),
          unit = pack > 1 && (!r.unit || /^(ea|each|pc)?$/i.test(r.unit)) ? "pack" : r.unit || (sp && sp.unit) || "",
          b = pwMake({ id: r.id, kind: "receipt", date: r.date, vendor: r.store, projectId: r.jobId, item: r.item, sku: r.sku, upc: r.upc, unit: unit, qty: r.qty, price: r.price, code: "", line: "", docId: r.docId || "", spendId: r.spendId || "", txnId: r.txnId || "", txnIds: r.txnId ? [r.txnId] : [], doc: r.docId ? "doc:" + r.docId : "spend:" + r.spendId, docNo: `receipt${r.number ? " " + r.number : ""} · ${r.store}`, receipt: r, src: { kind: "receipt", label: `receipt${r.number ? " " + r.number : ""} · ${r.store} · ${fmtL(r.date)}`, date: r.date, docId: r.docId || "", txnId: r.txnId || "" } });
        b && !D.byId[b.id] && add.push(b);
      });
      add.forEach((b) => {
        D.buys.push(b), (D.byId[b.id] = b);
        const I = (D.items[b.key] = D.items[b.key] || { key: b.key, label: (b.spec && b.spec.label) || b.item, cat: b.cat, unit: b.normUnit, buys: [], quotes: [], raw: [] });
        I.raw.includes(b.rawKey) || I.raw.push(b.rawKey), I.buys.push(b);
      });
      add.length && (D.buys.sort(pwByDate), Object.values(D.items).forEach((I) => I.buys.sort(pwByDate)));
    } catch (e) {
      console.warn("costintel: receipts in the price history", e);
    }
    return D;
  };
}
if ("function" == typeof pwSig) {
  const ciPwSigBase = pwSig;
  pwSig = function () {
    let extra = "";
    try {
      extra = `|r${(DB.docs || []).filter((d) => d && "receipt" === d.kind).map((d) => d.id + d.status + ((d.fields || {}).lines || []).length + (d.links || {}).jobId).join(",")}|s${(DB.spend || []).filter((s) => s && s.read).map((s) => s.id + s.status + (s.read.lines || []).length).join(",")}`;
    } catch (e) {}
    return ciPwSigBase.apply(this, arguments) + extra;
  };
}
// A receipt's cheaper price at another store is this lane's detector (it names the store and the saving); price watch's
// own "another vendor was cheaper" reason is left to the vendors it was written for, so one buy is never flagged twice.
if ("function" == typeof pwPriceCheck) {
  const ciPwPriceCheckBase = pwPriceCheck;
  pwPriceCheck = function (B) {
    const R = ciPwPriceCheckBase.apply(this, arguments);
    try {
      B && "receipt" === B.kind && R && R.reasons && (R.reasons = R.reasons.filter((x) => "otherVendor" !== x.kind));
    } catch (e) {}
    return R;
  };
}

// ---------------------------------------------------------------------------------------------------------------------
// 4. The receipt price book: per matched item, each store's latest price in the recent window and the best one.
// ---------------------------------------------------------------------------------------------------------------------
const CI_PB = { overPct: 3, minLine: 1, minCase: 5 };
const ciPbSet = () => {
  const S = (DB.priceWatch && DB.priceWatch.settings) || {};
  return { overPct: null != S.storeOverPct ? +S.storeOverPct : CI_PB.overPct, minLine: CI_PB.minLine, minCase: null != S.storeMin ? +S.storeMin : CI_PB.minCase, recentDays: pwSet().recentDays, checkDays: pwSet().checkDays };
};
// Each store's best price for an item over the `days` before `at` (store buys only: receipts and card lines at a store).
function ciStorePrices(I, at, days) {
  const to = at || today(),
    from = iso(addDays(to, -(days || pwSet().recentDays))),
    by = {};
  ((I && I.buys) || []).forEach((x) => {
    if (x.date < from || x.date > to || !ciIsStore(x.vendor)) return;
    const st = ciStoreName(x.vendor),
      cur = by[st];
    (!cur || x.price < cur.price - 1e-9 || (Math.abs(x.price - cur.price) < 1e-9 && x.date > cur.date)) && (by[st] = { store: st, price: x.price, date: x.date, id: x.id, source: (x.sources[0] || {}).label || x.docNo || "" });
  });
  return Object.values(by).sort((a, b) => a.price - b.price || a.store.localeCompare(b.store));
}
function ciPriceBook() {
  return pwMemoGet("ciPriceBook", () => {
    const D = pwData(),
      S = ciPbSet(),
      out = [];
    Object.values(D.items).forEach((I) => {
      const storeBuys = I.buys.filter((x) => ciIsStore(x.vendor));
      if (!storeBuys.length) return;
      const prices = ciStorePrices(I, today(), S.recentDays),
        last = storeBuys[storeBuys.length - 1],
        best = prices[0] || null,
        stores = [...new Set(storeBuys.map((x) => ciStoreName(x.vendor)))];
      out.push({ key: I.key, item: I.label, cat: I.cat, unit: I.unit, matched: I.raw.length > 1 || stores.length > 1, raw: I.raw.slice(), stores: prices, allStores: stores, best: best, last: { store: ciStoreName(last.vendor), price: last.price, date: last.date, id: last.id }, buys: storeBuys.length, spread: best && prices.length > 1 ? ciR4(prices[prices.length - 1].price - best.price) : 0 });
    });
    return out.sort((a, b) => b.buys - a.buys || a.item.localeCompare(b.item));
  });
}
// The store a buy should have been made at: the best price at another store in the recent window before it.
function ciStoreCheck(B, I, S0) {
  const S = S0 || ciPbSet();
  if (!B || !I || !ciIsStore(B.vendor)) return null;
  const mine = ciStoreName(B.vendor),
    others = ciStorePrices({ buys: I.buys.filter((x) => x.id !== B.id && (x.date < B.date || (x.date === B.date && String(x.id) < String(B.id)))) }, B.date, S.recentDays).filter((x) => x.store !== mine);
  if (!others.length) return null;
  const best = others[0];
  if (!(B.price > best.price * (1 + S.overPct / 100) + 1e-9)) return null;
  const save = r2((B.price - best.price) * B.normQty);
  return save >= S.minLine ? { buy: B, store: best.store, price: best.price, date: best.date, source: best.source, save: save, pct: ciPct(B.price, best.price) } : null;
}
// ---- the detector: one case per receipt (or card line), the lines on it bought above the best recent store price
try {
  PW_DET.pwStoreCheaper = {
    label: "Cheaper at Another Store",
    short: "store",
    rule: "a receipt bought at a store more than 3% above the best price for the same item (matched by UPC or spec: size, gauge, length, pack) at another store in the 90 days before it; one case per receipt, with the cheaper store and the saving",
  };
  PW_HYP.pwStoreCheaper = ["the cheaper store was out of stock that day", "the job could not wait for the trip to the other store", "a different grade or brand than the cheaper one", "a contractor discount at the cheaper store not on our account"];
  PW_STEPS.pwStoreCheaper = ["pricebook", "explain"];
  predDef("pwStoreCheaper", { label: PW_DET.pwStoreCheaper.label, rule: PW_DET.pwStoreCheaper.rule, rows: (scope) => pwCases("pwStoreCheaper").filter((c) => !scope || c.projectId === scope) });
  CATCH.push({ name: "pwStoreCheaper", label: PW_DET.pwStoreCheaper.label, rows: () => PRED.pwStoreCheaper.rows().map((c) => ({ key: c.key, what: `${PW_DET.pwStoreCheaper.label}: ${c.what}`, sub: c.sub, amount: c.amount, verb: "Open Case", run: () => pwCaseSheet(c.key) })) });
  "undefined" != typeof STD_MAP && !STD_MAP.pwStoreCheaper && STD_MAP.pwPaidMore && (STD_MAP.pwStoreCheaper = STD_MAP.pwPaidMore);
} catch (e) {
  console.warn("costintel: store detector", e);
}
function ciStoreCases() {
  const D = pwData(),
    S = ciPbSet(),
    td = today(),
    since = iso(addDays(td, -S.checkDays)),
    groups = {};
  let paidKeys = null;
  D.buys
    .filter((B) => B.date >= since && B.date <= td && ("receipt" === B.kind || "card" === B.kind) && ciIsStore(B.vendor))
    .forEach((B) => {
      const r = ciStoreCheck(B, D.items[B.key], S);
      if (!r) return;
      // a line price watch already flags as Paid More Than Before stays there (never counted twice)
      paidKeys = paidKeys || new Set((ciPwCasesBase ? ciPwCasesBase() : []).filter((c) => "pwPaidMore" === c.det).map((c) => c.buy && c.buy.id));
      if (paidKeys.has(B.id)) return;
      const g = B.docId || B.spendId || (B.txnIds || [])[0] || B.id;
      (groups[g] = groups[g] || []).push(r);
    });
  return Object.entries(groups)
    .map(([g, R]) => {
      const B0 = R[0].buy,
        amount = r2(R.reduce((a, r) => a + r.save, 0)),
        cheaper = [...new Set(R.map((r) => r.store))];
      return {
        key: "pw:store:" + g,
        det: "pwStoreCheaper",
        at: B0.date,
        what: `${ciStoreName(B0.vendor)} receipt, ${fmtL(B0.date)}`,
        sub: `${agN(R.length, "item")} cheaper at ${cheaper.join(" and ")}: ${ciCents(amount)} more than the best recent price`,
        amount: amount,
        vendor: ciStoreName(B0.vendor),
        projectId: B0.projectId || "",
        itemKey: B0.key,
        buy: B0,
        lines: R.map((r) => ({ item: r.buy.item, key: r.buy.key, qty: r.buy.normQty, unit: r.buy.normUnit, paid: r.buy.price, store: r.store, best: r.price, bestDate: r.date, save: r.save, pct: r.pct, source: r.source })),
        refs: [B0.docId, B0.spendId].concat(B0.txnIds || []).filter(Boolean),
        docNos: [B0.docNo].filter(Boolean),
        facts: R.map((r) => `${r.buy.item}: ${pwU2(r.buy.price)} per ${r.buy.normUnit} × ${r.buy.normQty}; ${r.store} had it at ${pwU2(r.price)} on ${fmtL(r.date)} (${r.pct}% less) — ${ciCents(r.save)}`),
        hist: R.map((r) => pwHistRow(r.buy, D.items[r.buy.key], r.buy.date)),
      };
    })
    .filter((c) => c.amount >= S.minCase - 1e-9);
}
let ciPwCasesBase = null;
if ("function" == typeof pwCasesAll) {
  ciPwCasesBase = pwCasesAll;
  pwCasesAll = function () {
    const base = ciPwCasesBase.apply(this, arguments);
    let mine = [];
    try {
      mine = pwMemoGet("ciStoreCases", ciStoreCases).map((c) => Object.assign({ steps: PW_STEPS[c.det], hyps: PW_HYP[c.det], label: PW_DET[c.det].label }, c));
    } catch (e) {
      console.warn("costintel: store cases", e);
    }
    return pwMemoGet("ciAllCases", () => base.concat(mine));
  };
}

// ---------------------------------------------------------------------------------------------------------------------
// 5. Retailer adapters. No scraping, ever. A retailer's data comes in only through what the retailer allows: the
//    firm's own Pro account purchase history (Home Depot Pro Xtra and Lowe's Pro export it as a file), a receipt
//    e-mailed to the firm, or a photo. None is connected yet; each says what it would take.
// ---------------------------------------------------------------------------------------------------------------------
const CI_RETAILERS = [
  { id: "homedepot", n: "Home Depot Pro Xtra", how: "Purchase history export (CSV) from the firm's Pro Xtra account; the Pro desk can also e-mail each receipt", api: "Home Depot offers no public pricing API; its terms forbid scraping the site", connected: !1 },
  { id: "lowes", n: "Lowe's Pro (MyLowe's Pro)", how: "Purchase history export (CSV) from the firm's Pro account; e-receipts to the purchasing inbox", api: "No public pricing API; scraping is against the terms", connected: !1 },
  { id: "supply", n: "Supply houses (Ferguson and others)", how: "Their invoices and receipts by e-mail, read by the document reader; Ferguson's online account exports order history", api: "Account-level price lists can be requested in writing", connected: !1 },
  { id: "lumber", n: "Lumber yards", how: "Receipts by e-mail or photo; the yard's quote sheet as a confirmed RFQ quote", api: "None", connected: !1 },
];
function ciCsvRows(text) {
  const rows = [];
  let cur = [],
    f = "",
    q = !1;
  const s = String(text || "");
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (q) '"' === ch ? ('"' === s[i + 1] ? ((f += '"'), i++) : (q = !1)) : (f += ch);
    else if ('"' === ch) q = !0;
    else if ("," === ch) cur.push(f), (f = "");
    else if ("\n" === ch || "\r" === ch) {
      "\r" === ch && "\n" === s[i + 1] && i++;
      cur.push(f), (f = ""), cur.some((x) => x.trim()) && rows.push(cur), (cur = []);
    } else f += ch;
  }
  return cur.push(f), cur.some((x) => x.trim()) && rows.push(cur), rows;
}
// A purchase-history export becomes receipt documents, one per transaction, read by the same price history.
function ciImportPurchaseHistory(text, retailer, opts) {
  const R = ciCsvRows(text);
  if (R.length < 2) return { ok: !1, why: "Nothing to read: paste the export with its header row" };
  const H = R[0].map((h) => h.toLowerCase().trim()),
    col = (...names) => H.findIndex((h) => names.some((n) => h === n || h.includes(n))),
    c = { date: col("date", "purchase date", "transaction date"), store: col("store", "store number", "location"), tx: col("transaction", "receipt", "order"), sku: col("sku", "item number", "item #", "model"), upc: col("upc"), desc: col("description", "item description", "product"), qty: col("quantity", "qty"), price: col("unit price", "price each", "price"), ext: col("extended", "total", "amount"), job: col("job", "po", "project") };
  if (c.desc < 0 || c.qty < 0 || (c.price < 0 && c.ext < 0)) return { ok: !1, why: "The header needs a description, a quantity and a price (or an extended amount)" };
  const chain = CI_CHAINS.find((x) => x.id === retailer),
    byTx = {};
  R.slice(1).forEach((r) => {
    const v = (i) => (i >= 0 ? String(r[i] || "").trim() : ""),
      num = (i) => +String(v(i)).replace(/[$,\s]/g, "") || 0,
      d = v(c.date),
      dm = d.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/),
      date = dm ? `${dm[3].length === 2 ? "20" + dm[3] : dm[3]}-${dm[1].padStart(2, "0")}-${dm[2].padStart(2, "0")}` : /^\d{4}-\d{2}-\d{2}/.test(d) ? d.slice(0, 10) : "",
      tx = v(c.tx) || `${date}|${v(c.store)}`,
      q = num(c.qty),
      ext = c.ext >= 0 ? num(c.ext) : 0,
      pr = c.price >= 0 ? num(c.price) : q ? ext / q : 0;
    if (!date || !(q > 0) || !(pr > 0) || !v(c.desc)) return;
    const T = (byTx[tx] = byTx[tx] || { date: date, store: v(c.store), job: v(c.job), lines: [] });
    T.lines.push({ item: v(c.desc), sku: v(c.sku), upc: v(c.upc), qty: q, unit: "", price: r2(pr), ext: r2(ext || q * pr) });
  });
  const made = [];
  Object.entries(byTx).forEach(([tx, T]) => {
    if ((DB.docs || []).some((d) => d && "receipt" === d.kind && d.source && d.source.retailerTx === `${retailer}:${tx}`)) return;
    const storeTxt = `${(chain && chain.n) || retailer} ${/^\d+$/.test(T.store) ? "#" + T.store : T.store}`.trim(),
      sub = r2(T.lines.reduce((a, l) => a + l.ext, 0)),
      p = T.job && "function" == typeof cmJobNamed ? cmJobNamed(T.job) : null,
      d = ciNewReceipt({ store: ciStoreName(storeTxt) || storeTxt, number: tx, date: T.date, lines: T.lines, subtotal: sub, tax: null, jobId: p ? p.id : "", txnId: "", source: { type: "retailer", retailer: retailer, retailerTx: `${retailer}:${tx}`, file: (opts && opts.file) || "" } });
    made.push(d);
  });
  return made.length && save(), { ok: !0, made: made, skipped: Object.keys(byTx).length - made.length };
}
function ciNewReceipt(o) {
  const lines = o.lines.map((l) => ({ item: l.item, sku: l.sku || "", upc: l.upc || "", qty: +l.qty, unit: l.unit || "", price: +l.price, ext: r2(l.ext != null ? l.ext : +l.qty * +l.price) })),
    sub = r2(null != o.subtotal ? o.subtotal : lines.reduce((a, l) => a + l.ext, 0)),
    tax = null != o.tax ? r2(o.tax) : r2(sub * 0.08875),
    fields = { vendor: (ciStoreOf(o.store) || {}).n ? CI_CHAINS.find((c) => c.id === ciStoreOf(o.store).chain)?.n || o.store : o.store, store: o.store, number: o.number || "", date: o.date, lines: lines, subtotal: sub, tax: tax, total: r2(sub + tax), storeZip: o.zip || "11215" },
    conf = {};
  Object.keys(fields).forEach((k) => "lines" !== k && (conf[k] = 0.98));
  lines.forEach((l, i) => ["qty", "price", "ext"].forEach((k) => (conf[`lines.${i}.${k}`] = 0.98)));
  const d = trkNewDoc({ read: { kind: "receipt", fields: fields, conf: conf, readable: !0 }, source: o.source || { type: "upload" }, links: { jobId: o.jobId || "", txnId: o.txnId || "" }, status: "filed", by: o.by || ciMe() });
  return o.id && (d.id = o.id), d;
}

// ---------------------------------------------------------------------------------------------------------------------
// 6. Jobs spending more than they bring in: one rule, by line, with the cause and a drafted fix.
//    cash      cash out (paid bills, bank and card lines on the job, payroll paid) above cash in (client payments)
//    ahead     cost to date above what the job has billed
//    over      a line over its budget: the overspend-at-landing rule (ovsAll), the same rows Caught for You's Over Budget
//    forecast  a line not over yet that will be: committed past its budget, or its measured progress projects past it
//              (at least 10% measured, more than 5% over the budget)
// ---------------------------------------------------------------------------------------------------------------------
const CI_RULE = { forecastMinPct: 10, forecastOverPct: 5, minCash: 1, minAhead: 1 };
function ciLaborPaid(p) {
  // time is cash once the payroll run that holds it is paid (a submitted run is owed, not paid)
  const runs = (Array.isArray(DB.payroll) ? DB.payroll : []).filter((r) => ["paid", "verified", "posted"].includes(r.status)),
    inRun = (e) => runs.some((r) => (r.entries || r.timeIds || []).includes(e.id) || (r.from && r.to && e.date >= r.from && e.date <= r.to));
  let n = 0;
  (DB.time || [])
    .filter((e) => e.projectId === p.id && "rejected" !== e.status && inRun(e))
    .forEach((e) => {
      const emp = (DB.employees || []).find((x) => x.id === e.empId);
      n += hoursOf(e) * laborRate(emp);
    });
  return r2(n);
}
// Cash is what left the bank: every bank and card line on the job (a bill's payment included, whatever the bill's own
// status says), plus a bill marked paid that no bank line backs (paid outside the feed), plus payroll paid.
function ciCashOf(p, J) {
  const bills = (DB.bills || []).filter((b) => b.projectId === p.id),
    lines = (DB.txns || []).filter((t) => t.projectId === p.id && +t.amt < 0 && isJobCat(t.cat) && "labor" !== t.cat && !t.voided),
    bank = r2(lines.reduce((a, t) => a - +t.amt, 0)),
    backed = (b) => lines.some((t) => t.billId === b.id || txnViaBill(t, [b])),
    billsPaid = r2(bills.filter((b) => ["paid", "verified"].includes(b.status) && !backed(b)).reduce((a, b) => a + billCost(b), 0)),
    labor = ciLaborPaid(p),
    out = r2(billsPaid + bank + labor);
  return { in: r2(J.collected || 0), out: out, billsPaid: billsPaid, bank: bank, labor: labor };
}
function ciLineForecasts(p, J) {
  const out = [];
  let detail = null;
  try {
    detail = tpJobPctDetail(p);
  } catch (e) {}
  const pctOf = (key) => {
    const r = detail && (detail.lines || []).find((x) => x.x && x.x.key === key);
    return r && "measured" === r.basis ? +r.pct || 0 : null;
  };
  (J.eacLines || []).forEach((x) => {
    const budget = r2(+x.budget || 0),
      actual = r2(+x.actual || 0),
      committed = r2(+x.committed || 0);
    if (!(budget > 0) || actual - budget >= 1) return; // over already: the overspend rule carries it
    if (actual + committed - budget >= 1) return void out.push({ key: x.key, name: x.name, code: x.code, budget: budget, actual: actual, committed: committed, forecast: r2(actual + committed), over: r2(actual + committed - budget), kind: "committed", why: `committed ${ciMoney(committed)} on top of ${ciMoney(actual)} spent: ${ciMoney(actual + committed - budget)} past its ${ciMoney(budget)} budget` });
    const pct = pctOf(x.key);
    if (null == pct || pct < CI_RULE.forecastMinPct || !(actual > 0)) return;
    const f = r2(actual / (pct / 100));
    f > budget * (1 + CI_RULE.forecastOverPct / 100) && out.push({ key: x.key, name: x.name, code: x.code, budget: budget, actual: actual, committed: committed, forecast: f, over: r2(f - budget), pct: Math.round(pct), kind: "measured", why: `${ciMoney(actual)} spent at ${Math.round(pct)}% complete (measured) projects ${ciMoney(f)} against a ${ciMoney(budget)} budget` });
  });
  return out;
}
function ciJobMoney(p) {
  let J = null;
  try {
    J = jobFin(p);
  } catch (e) {
    return null;
  }
  const C = ciCashOf(p, J),
    over = (("function" == typeof ovsAll ? ovsAll() : []) || []).filter((o) => o.p && o.p.id === p.id),
    fc = ciLineForecasts(p, J),
    reasons = [],
    fixes = [];
  const billed = r2(J.billed || 0),
    actual = r2(J.actual || 0),
    c = (DB.clients || []).find((x) => x.id === p.clientId),
    openInv = c ? (clientFin(c).open || []).filter((o) => o.x && (!o.x.projectId || o.x.projectId === p.id) && +o.bal > 0.005) : [],
    rtb = (() => {
      try {
        return readyToBill().rows.filter((r) => r.p && r.p.id === p.id);
      } catch (e) {
        return [];
      }
    })(),
    rtbAmt = r2(rtb.reduce((a, r) => a + (+r.amount || 0), 0)),
    openAmt = r2(openInv.reduce((a, o) => a + (+o.bal || 0), 0));
  if (C.out - C.in >= CI_RULE.minCash && C.out > 0) {
    reasons.push({ kind: "cash", amount: r2(C.out - C.in), t: `cash out ${ciMoney(C.out)} is ${ciMoney(C.out - C.in)} more than the ${ciMoney(C.in)} the client has paid`, cause: openAmt ? `${ciMoney(openAmt)} billed and not yet paid` : billed ? "the client has paid less than was spent" : "nothing billed yet" });
    openAmt && fixes.push({ kind: "chase", label: "Chase Payment", t: `Chase the ${agN(openInv.length, "open invoice")} (${ciMoney(openAmt)}): the Standard's collections at due, 7, 15 and 30 days`, amount: openAmt, clientId: c ? c.id : "" });
  }
  if (actual - billed >= CI_RULE.minAhead && actual > 0) {
    reasons.push({ kind: "ahead", amount: r2(actual - billed), t: `cost to date ${ciMoney(actual)} is ${ciMoney(actual - billed)} ahead of the ${ciMoney(billed)} billed`, cause: rtbAmt ? `${ciMoney(rtbAmt)} earned and ready to bill` : "work done ahead of the billing schedule" });
  }
  rtbAmt > 0 && reasons.some((r) => "cash" === r.kind || "ahead" === r.kind) && fixes.push({ kind: "bill", label: "Bill It", t: `Bill the ${ciMoney(rtbAmt)} earned and not billed (the Standard: invoice within 2 business days of a milestone)`, amount: rtbAmt, key: rtb[0] && "function" == typeof blRtbKey ? blRtbKey(rtb[0]) : "" });
  const lines = over
    .map((o) => ({ key: o.line ? o.line.key : "code:" + o.code, name: o.line ? o.name : `${o.code} ${o.name}`, code: o.code, budget: r2(o.budget), actual: r2(o.actual), committed: o.line ? r2(+o.line.committed || 0) : 0, forecast: o.line ? r2(Math.max(+o.line.eac || 0, o.actual)) : r2(o.actual), over: r2(o.over), kind: "over", ovsKey: o.key, by: (o.by || []).map((x) => ({ kind: x.kind, id: x.id, label: x.label, amt: x.amt })), why: `${ciMoney(o.actual)} spent against ${ciMoney(o.budget)} budgeted` + ((o.by || [])[0] ? `; taken over by ${o.by[0].label}` : "") }))
    .concat(fc);
  lines.forEach((l) => {
    const cause = ciLineCause(p, l);
    (l.cause = cause.t), (l.fix = cause.fix);
  });
  lines.length && reasons.push({ kind: "lines", amount: r2(lines.reduce((a, l) => a + l.over, 0)), t: `${agN(lines.length, "line")} over budget or forecast to go over (${ciMoney(lines.reduce((a, l) => a + l.over, 0))})` });
  if (!reasons.length) return null;
  return { p: p, J: J, cash: C, billed: billed, actual: actual, reasons: reasons, lines: lines, fixes: fixes, amount: r2(Math.max(...reasons.map((r) => r.amount))), key: "cimoney:" + p.id };
}
// The cause of a line's overrun, from the records behind it, and the fix that recovers the money.
function ciLineCause(p, l) {
  const pos = (DB.pos || []).filter((po) => po.projectId === p.id && (po.lines || []).some((x) => x.line === l.key) && !["cancelled", "draft"].includes(po.status)),
    bills = (DB.bills || []).filter((b) => b.projectId === p.id && (b.line === l.key || (b.lines || []).some((x) => x.line === l.key) || pos.some((po) => po.id === b.poId)) && !["void", "rejected"].includes(b.status)),
    overPo = bills.find((b) => "function" == typeof pay3Default && pay3Can(b) && pay3Default(b) > 0),
    poTot = r2(pos.reduce((a, po) => a + poTotal(po).sub, 0));
  if (overPo) {
    const P = pay3PO(overPo);
    return { t: `${overPo.vendor} billed ${ciMoney(billTotal(overPo))} on ${overPo.number} against ${P && P.po ? P.po.number : "the PO"}, ${ciMoney(r2(billTotal(overPo) - pay3Default(overPo)))} over the PO`, fix: { kind: "dispute", label: isOwner() ? "Dispute Difference" : "Review the Bill", billId: overPo.id, t: "Pay what the PO allows and ask the vendor for a credit, or price the extra to the client as a change order" } };
  }
  if ("committed" === l.kind && poTot > l.budget + 0.5) {
    const po = pos.slice().sort((a, b) => poTotal(b).sub - poTotal(a).sub)[0];
    return { t: `${po.number} to ${po.vendor} commits ${ciMoney(poTotal(po).sub)} against the line's ${ciMoney(l.budget)} budget`, fix: { kind: "co", label: "Draft Change Order", t: `If the client asked for the extra scope, a change order for ${ciMoney(l.over)} of cost at the line's markup, before the work is done` } };
  }
  const txn = (DB.txns || []).filter((t) => t.projectId === p.id && t.line === l.key && +t.amt < 0).sort((a, b) => a.amt - b.amt)[0];
  if (txn && "over" === l.kind)
    return { t: `${txn.vendor || txn.desc} ${ciMoney(-txn.amt)} on ${fmtL(txn.date)} took the line over with no change order behind it`, fix: { kind: "co", label: "Draft Change Order", t: `A change order for ${ciMoney(l.over)} of cost if the client added the scope; otherwise re-forecast the line and say why` } };
  if ("measured" === l.kind) return { t: `spending is running ahead of the work measured as done (${l.pct}%)`, fix: { kind: "review", label: "Review the Line", t: "Check the measurement with the foreman, then re-forecast the line or price the extra scope" } };
  return { t: l.why, fix: { kind: "review", label: "Review the Line", t: "Re-forecast the line and say why" } };
}
function ciJobsOverspending(scope) {
  return (DB.projects || [])
    .filter((p) => !p.archived && "closed" !== (p.project || {}).status && (!scope || p.id === scope))
    .map(ciJobMoney)
    .filter(Boolean)
    .sort((a, b) => b.amount - a.amount);
}
predDef("jobsOverspending", {
  label: "Jobs Spending More Than They Bring In",
  rule: "a live job whose cash out is above its cash in, whose cost to date is ahead of what it billed, or with a line over budget (the overspend rule) or forecast to go over (committed past its budget, or measured progress projecting more than 5% past it)",
  rows: (scope) => ciJobsOverspending(scope),
  figure() {
    return r2(this.rows().reduce((a, x) => a + x.amount, 0));
  },
});
// Caught for You: only what Over Budget does not already carry (cash, cost ahead of billing, lines forecast to go over)
CATCH.push({
  name: "jobCash",
  label: "Spending More Than It Brings In",
  rows: () =>
    PRED.jobsOverspending
      .rows()
      .map((x) => ({ x: x, R: x.reasons.filter((r) => "lines" !== r.kind), F: x.lines.filter((l) => "over" !== l.kind) }))
      .filter((y) => y.R.length || y.F.length)
      .map(({ x, R, F }) => ({
        key: x.key,
        what: `Spending more than it brings in: ${shortName(x.p)}`,
        sub: R.length ? R[0].t : `${F[0].name}: ${F[0].why}`,
        amount: r2(Math.max(0, ...R.map((r) => r.amount), ...F.map((l) => l.over))),
        verb: "Review",
        run: () => ciOpenTab(x.p.id),
      })),
});
"undefined" != typeof STD_MAP && !STD_MAP.jobCash && (STD_MAP.jobCash = { p: "cost", leak: !0, c: ["pb", "office", "actFrom", /Cash is oxygen/i] });
let ciFocusJob = "";
function ciOpenTab(pid) {
  try {
    pid && setCurrent(pid);
  } catch (e) {}
  (view = "reports"), (repTab = "costintel"), (ciFocusJob = pid || ""), render();
}
// The drafted fix for a line, run by a person: a change order draft priced at the line's markup. Nothing is sent.
function ciDraftCO(pid, key) {
  const p = (DB.projects || []).find((x) => x.id === pid),
    M = p && ciJobMoney(p),
    l = M && M.lines.find((x) => x.key === key);
  if (!p || !l) return toast("That line is no longer over its budget"), null;
  const c = (DB.clients || []).find((x) => x.id === p.clientId);
  if (!c) return toast("This job has no client to send a change order to"), null;
  let price = l.over;
  try {
    const f = lineFin(l.key);
    f && +f.price > 0 && l.budget > 0 && (price = r2((l.over * +f.price) / l.budget));
  } catch (e) {}
  const d = newDoc(c, "co", { projectId: p.id });
  d.projectId = d.projectId || p.id;
  d.title = `Added scope: ${l.name}`;
  d.lines = [{ id: uid("l"), item: `${l.name} — added scope`, desc: `${l.cause || l.why}. Priced at the line's markup on ${ciMoney(l.over)} of cost.`, qty: 1, unit: "ls", rate: price, taxable: !1, cost: l.over, line: l.key }];
  d.ciFrom = { key: l.key, over: l.over, at: today(), by: ciMe() };
  try {
    audit("co", d.id, "drafted", null, { from: "cost intelligence", line: l.key, over: l.over });
  } catch (e) {}
  save();
  toast(`Change order drafted for ${l.name}: ${ciMoney(price)}`, () => ciOpenDoc(c, d));
  return d;
}
function ciOpenDoc(c, d) {
  try {
    flowGo.doc(c, "co", d)();
  } catch (e) {
    (view = "clients"), render();
  }
}
// ---------------------------------------------------------------------------------------------------------------------
// 7. Benchmarks from past jobs: rough material per unit, by trade, across comparable jobs (same kind of job).
//    A trade's sample on a job = what it bought for the trade (quantity × price) ÷ the job's measure for that trade.
//    The cause of a sample above the median is split three ways against the comparable jobs, exactly:
//      cost per unit = (used at typical prices ÷ measure) × (bought ÷ used) × (paid ÷ typical prices)
//                    =  quantity                        ×  waste           ×  price
//    the term furthest above its median names the cause. A job still running has no "used" yet: what it bought so
//    far is compared with what comparable jobs bought in total (it can only grow), and its prices are compared now.
// ---------------------------------------------------------------------------------------------------------------------
const CI_TRADES = [
  { id: "roughPlumbing", label: "Rough plumbing material", code: "05", per: "fixture", measure: "fixtures", alt: { per: "bath", measure: "baths" }, scale: 1, re: /\b(pex|pexa|pexb|copper pipe|type l|type m|ball valve|stop valve|dwv|cpvc|manifold)\b/i, not: /\b(faucet|toilet|vanity|sink|tub|shower ?head|trim kit|fixture)\b/i },
  { id: "roughElectric", label: "Rough electric material", code: "06", per: "device", measure: "devices", alt: { per: "100 SF", measure: "sf", scale: 100 }, scale: 1, re: /\b(nmb|nm-?b|romex|mc cable|bx cable|new ?work box|old ?work box|outlet box|switch box|[12]-gang|conduit|emt)\b/i, not: /\b(cover plate|wall plate|dimmer|fixture)\b/i },
  { id: "sheetrock", label: "Sheetrock", code: "07", per: "board", measure: "boards", alt: { per: "100 SF", measure: "sheetrockSf", scale: 100 }, scale: 1, re: /\b(drywall|sheetrock|gypsum|gwb|wallboard)\b/i, not: /\b(screw|compound|tape|bead|anchor|knife|lift|mud)\b/i },
  { id: "taping", label: "Taping material", code: "07", per: "100 SF", measure: "tapeSf", scale: 100, re: /\b(joint compound|compound|mud|paper tape|drywall tape|mesh tape|corner bead)\b/i },
  { id: "framing", label: "Framing lumber", code: "03", per: "LF of wall", measure: "framingLf", alt: { per: "100 SF", measure: "sf", scale: 100 }, scale: 1, re: /\b(\dx\d{1,2}|stud|studs|plate stock|header)\b/i, not: /\b(plywood|cdx|osb|drywall|hanger|angle|screw|nail|tile)\b/i },
];
const CI_BENCH = { overPct: 15, minJobs: 3 };
const ciTrade = (id) => CI_TRADES.find((t) => t.id === id) || null;
function ciTradeOf(desc) {
  const t = ciCanon(desc),
    sp = ciSpec(desc);
  if (sp) {
    if (/^pex/.test(sp.key)) return "roughPlumbing";
    if (/^nmb\|/.test(sp.key)) return "roughElectric";
    if (/^drywall\|/.test(sp.key)) return "sheetrock";
    if (/^compound\|/.test(sp.key)) return "taping";
    if (/^lumber\|/.test(sp.key)) return "framing";
    if (/^plywood\|/.test(sp.key)) return "";
  }
  const T = CI_TRADES.find((x) => x.re.test(t) && !(x.not && x.not.test(t)));
  return T ? T.id : "";
}
const ciItemKey = (desc) => ciSpecKey(desc) || pwNorm(desc);
function ciCloseouts() {
  return (DB.closeouts = Array.isArray(DB.closeouts) ? DB.closeouts : []);
}
// A job's measures: the closeout's, or the project's own (p.project.measures, set by the PM from the drawings)
const ciMeasures = (job) => (job && (job.measures || (job.project && job.project.measures))) || {};
const ciJobType = (job) => (job && (job.type || (job.project && job.project.jobType))) || "";
// One trade's sample on one job.
function ciSample(job, tradeId, opts) {
  const T = ciTrade(tradeId),
    M = ciMeasures(job),
    qty = +M[T.measure] || 0,
    live = !!(opts && opts.live),
    rows = live ? ciLiveBuys(job, tradeId) : (job.buys || []).filter((b) => b.trade === tradeId);
  if (!rows.length || !(qty > 0)) return null;
  const items = rows.map((b) => ({ item: b.item, key: ciItemKey(b.item), unit: b.unit || "ea", bought: +b.bought, used: live ? +b.bought : +b.used, price: +b.price, ext: r2(+b.bought * +b.price), vendor: b.vendor || "", date: b.date || "" })),
    material = r2(items.reduce((a, x) => a + x.ext, 0)),
    scale = T.scale || 1,
    perUnit = r2((material / qty) * scale),
    altQty = T.alt ? +M[T.alt.measure] || 0 : 0;
  return { jobId: job.id, job: job.name || (job.project && job.project.name) || job.id, type: ciJobType(job), closed: !live, closedOn: job.closedOn || "", trade: tradeId, measure: T.measure, qty: qty, per: T.per, items: items, material: material, perUnit: perUnit, alt: altQty > 0 ? { per: T.alt.per, qty: altQty, perUnit: r2((material / altQty) * (T.alt.scale || 1)) } : null };
}
// What a running job bought for a trade: the price history's buys on the job (POs, bills, card lines, receipts).
function ciLiveBuys(p, tradeId) {
  const D = pwData();
  return D.buys
    .filter((B) => B.projectId === p.id && "quote" !== B.kind && ciTradeOf(B.item) === tradeId)
    .map((B) => ({ item: B.item, unit: B.normUnit, bought: B.normQty, used: B.normQty, price: B.price, vendor: B.vendor, date: B.date }));
}
// Comparable closed jobs: the same kind of job. A running job is compared with all of them; a closed one with the others.
function ciComparables(type, exceptId) {
  return ciCloseouts().filter((c) => c.type === type && c.id !== exceptId);
}
function ciDecompose(s, others) {
  // typical price per item: the median paid across the comparable jobs' samples
  const refOf = {};
  others.forEach((o) => o.items.forEach((x) => (refOf[x.key] = refOf[x.key] || []).push(x.price)));
  const ref = (x) => {
    const m = ciMedian(refOf[x.key] || []);
    return null == m ? x.price : m;
  };
  const parts = (smp) => {
    const rb = smp.items.reduce((a, x) => a + x.bought * ref(x), 0),
      ru = smp.items.reduce((a, x) => a + x.used * ref(x), 0);
    return { price: rb ? smp.material / rb : 1, waste: ru ? rb / ru - 1 : 0, qty: ru / smp.qty, rb: rb, ru: ru };
  };
  const me = parts(s),
    O = others.map(parts),
    med = { price: ciMedian(O.map((x) => x.price)) || 1, waste: ciMedian(O.map((x) => x.waste)) || 0, qty: ciMedian(O.map((x) => x.qty)) || me.qty },
    terms = [
      { cause: "price", v: Math.log(me.price / med.price), mine: me.price, med: med.price },
      { cause: "waste", v: Math.log((1 + me.waste) / (1 + med.waste)), mine: me.waste, med: med.waste },
      { cause: "quantity", v: Math.log(me.qty / med.qty), mine: me.qty, med: med.qty },
    ];
  s.closed || (terms[1].v = 0);
  const top = terms.slice().sort((a, b) => b.v - a.v)[0];
  return { me: me, med: med, terms: terms, cause: top.v > 0 ? top.cause : "", ref: ref };
}
function ciCauseWords(s, D, T) {
  const t = D.terms.find((x) => x.cause === D.cause);
  if (!t) return "";
  if ("price" === D.cause) return `price: paid ${Math.round((t.mine / t.med - 1) * 100)}% above what comparable jobs paid for the same items`;
  if ("waste" === D.cause) return `waste: bought ${Math.round(t.mine * 100)}% more than was installed, against ${Math.round(t.med * 100)}% on comparable jobs`;
  return `quantity: ${Math.round((t.mine / t.med - 1) * 100)}% more material per ${T.per} than comparable jobs used${s.closed ? "" : " (waste is separable only at close-out)"}`;
}
// The benchmark per trade (closed comparable jobs), and each job's sample against it.
function ciBenchmarks(type) {
  const ty = type || "brownstone";
  return pwMemoGet("ciBench:" + ty + ":" + ciCloseouts().length + ":" + JSON.stringify(ciBenchBook()), () =>
    CI_TRADES.map((T) => {
      const samples = ciComparables(ty, "").map((c) => ciSample(c, T.id)).filter(Boolean),
        vals = samples.map((s) => s.perUnit),
        alts = samples.filter((s) => s.alt).map((s) => s.alt.perUnit),
        med = vals.length ? r2(ciMedian(vals)) : null,
        live = ciBenchBook()[T.id] || null;
      return { trade: T.id, label: T.label, per: T.per, code: T.code, type: ty, n: samples.length, median: med, min: vals.length ? Math.min(...vals) : null, max: vals.length ? Math.max(...vals) : null, altPer: T.alt ? T.alt.per : "", altMedian: alts.length ? r2(ciMedian(alts)) : null, samples: samples, inEstimating: live, enough: samples.length >= CI_BENCH.minJobs };
    }),
  );
}
// Every job (closed or running) more than 15% above the median of the comparable closed jobs, with the cause.
function ciBenchFlags() {
  return pwMemoGet("ciBenchFlags:" + ciCloseouts().length, () => {
    const out = [],
      types = [...new Set(ciCloseouts().map((c) => c.type).concat((DB.projects || []).map((p) => ciJobType(p)).filter(Boolean)))];
    types.forEach((ty) => {
      const jobs = ciCloseouts()
        .filter((c) => c.type === ty)
        .map((c) => ({ job: c, live: !1 }))
        .concat((DB.projects || []).filter((p) => !p.archived && ciJobType(p) === ty).map((p) => ({ job: p, live: !0 })));
      jobs.forEach(({ job, live }) =>
        CI_TRADES.forEach((T) => {
          const s = ciSample(job, T.id, { live: live });
          if (!s) return;
          const others = ciComparables(ty, job.id).map((c) => ciSample(c, T.id)).filter(Boolean);
          if (others.length < CI_BENCH.minJobs) return;
          const med = r2(ciMedian(others.map((o) => o.perUnit))),
            D = ciDecompose(s, others),
            over = s.perUnit > med * (1 + CI_BENCH.overPct / 100) + 1e-9,
            priceOver = live && D.me.price > D.med.price * (1 + CI_BENCH.overPct / 100) + 1e-9;
          if (!over && !priceOver) return;
          const cause = over ? D.cause || "price" : "price",
            Dc = Object.assign({}, D, { cause: cause }),
            pid = live ? job.id : "",
            line = live ? ciTradeLine(job, T) : null,
            dollars = over ? r2(((s.perUnit - med) * s.qty) / (T.scale || 1)) : r2(s.material - s.material / (D.me.price / D.med.price));
          out.push({ key: `bench:${job.id}:${T.id}`, jobId: job.id, projectId: pid, job: s.job, live: live, trade: T.id, label: T.label, per: T.per, perUnit: s.perUnit, median: med, pct: ciPct(s.perUnit, med), qty: s.qty, measure: T.measure, material: s.material, over: over, priceOnly: !over, cause: cause, why: ciCauseWords(s, Dc, T), dollars: dollars, n: others.length, line: line, priceIdx: ciR4(D.me.price / D.med.price) });
        }),
      );
    });
    return out.sort((a, b) => b.dollars - a.dollars);
  });
}
// The estimate line a trade's material lands on (by cost code), for a running job.
function ciTradeLine(p, T) {
  try {
    const L = (jobFin(p).eacLines || []).filter((x) => x.code === T.code);
    return L.length ? { key: L[0].key, name: L[0].name } : null;
  } catch (e) {
    return null;
  }
}
predDef("benchOver", {
  label: "Above the Benchmark",
  rule: "a job's rough material per unit more than 15% above the median of at least three comparable closed jobs, or a running job paying more than 15% above the prices they paid, with the cause (quantity, price or waste)",
  rows: (scope) => ciBenchFlags().filter((f) => !scope || f.projectId === scope),
});
// Feeding estimating: a drafted change the owner approves in Company › Changes. Approved, it is DB.company.costBook.bench.
function ciProposeBench(tradeId, type) {
  const B = ciBenchmarks(type).find((x) => x.trade === tradeId);
  if (!B || !B.enough) return toast("Not enough comparable jobs to propose a benchmark (three are needed)"), null;
  if (!["owner", "pm", "controller"].includes(ciRole())) return toast("The owner, a PM or the controller proposes a benchmark"), null;
  const key = `costbench:${B.type}:${tradeId}:${B.median}`;
  if ((DB.changes || []).some((c) => c.key === key && "declined" !== c.status)) return toast("Already proposed: it waits under Company › Changes"), null;
  const from = ciBenchBook()[tradeId] || null,
    ch = {
      id: uid("ch"),
      key: key,
      title: `Estimating: carry ${B.label.toLowerCase()} at ${ciCents(B.median)} per ${B.per} on ${B.type} jobs`,
      why: `The median of ${agN(B.n, "comparable closed job")} (${ciCents(B.min)} to ${ciCents(B.max)} per ${B.per}). New estimates for ${B.type} jobs show it next to the line, so a takeoff below it is a question before it is a loss. (Estimating and preconstruction: estimate vs. actual, with lessons fed into the price book. Every dollar matters.)`,
      kind: "setting",
      delta: { path: `company.costBook.bench.${tradeId}`, from: from, to: { perUnit: B.median, per: B.per, type: B.type, n: B.n, at: today(), label: B.label }, label: `Benchmark for ${B.label.toLowerCase()} on new estimates` },
      evidence: B.samples.map((s) => ({ t: `${s.job}: ${ciCents(s.material)} for ${s.qty} ${ciTrade(tradeId).measure.replace(/([A-Z])/g, " $1").toLowerCase()} = ${ciCents(s.perUnit)} per ${B.per}`, m: "close-out" })),
      status: "draft",
      at: today(),
      by: ciMe(),
      source: "benchmark",
      value: { dollars: 0, basis: "an estimate that carries the real cost" },
    };
  (DB.changes = DB.changes || []).push(ch);
  try {
    log(`Proposed a benchmark: ${ch.title}`, "change", ch.by);
  } catch (e) {}
  save(), render();
  toast(`Proposed to Company › Changes: ${B.label} at ${ciCents(B.median)} per ${B.per}`, () => ciOpenChanges());
  return ch;
}
function ciOpenChanges() {
  try {
    (mtTab = "changes"), (mtOpen = "");
  } catch (e) {}
  (view = "meetings"), render();
}
// ---- One price path for estimating (coordinator's ask, 2026-10-20): DB.company.costBook is the one store of what
// new estimates carry. Its cost-code keys ("05": 1.12) are the close-out cost factors the reports lane proposes
// (Estimate Versus Actual, rpProposeCostBook); its "bench" key holds the per-unit benchmarks this lane proposes
// (costBook.bench.<trade>). Both are written only by the owner's approval in Company › Changes. ciCostGuide is the
// one reader: the estimate editor's hints and the item library's fill (libFillLine, itFillSell) both go through it.
const ciBenchBook = () => {
  const B = ((DB.company || {}).costBook || {}).bench;
  return B && "object" == typeof B ? B : {};
};
const ciCodeFactor = (code) => {
  const f = +(((DB.company || {}).costBook || {})[String(code || "")] || 0);
  return f > 0 && isFinite(f) ? f : null;
};
function ciCostGuide(l, d) {
  const p = d && (DB.projects || []).find((x) => x.id === d.projectId),
    type = p ? ciJobType(p) : "",
    code = (l && l.code) || "",
    factor = ciCodeFactor(code);
  return { code: code, factor: factor, factorWhy: factor ? `close-out cost factor for ${code} ${(COST_CODES.find((x) => x[0] === code) || [code, ""])[1]}: ×${factor} (approved under Company › Changes)` : "", bench: ciEstimateHints(`${(l && l.item) || ""} ${(l && l.desc) || ""}`, type) };
}
// The item library's fill: a unit cost it fills (the library's, or the last price) is scaled by the cost code's
// close-out factor, once, and the line says so. A cost someone typed is never touched.
function ciGuideFill(l, d, costBefore) {
  try {
    if (!l || +costBefore > 0 || !(+l.cost > 0) || l.costGuide) return;
    const G = ciCostGuide(l, d);
    if (!G.factor || 1 === G.factor) return;
    const from = +l.cost;
    (l.cost = r2(from * G.factor)), (l.costGuide = { factor: G.factor, code: G.code, from: from, src: "costBook", at: today() });
  } catch (e) {}
}
if ("function" == typeof libFillLine) {
  const ciLibFillBase = libFillLine;
  libFillLine = function (l, it, d) {
    const before = +((l && l.cost) || 0),
      r = ciLibFillBase.apply(this, arguments);
    return ciGuideFill(l, d, before), r;
  };
}
// What estimating reads: the approved benchmarks a line's words cover, and what this job's measures make of them.
const CI_LINE_TRADES = [
  ["roughPlumbing", /\b(rough plumbing|plumbing[\s\-–—,&]+rough|plumbing rough|rough[- ]in plumbing)\b/i],
  ["roughElectric", /\b(rough electric|electrical[\s\-–—,&]+rough|electrical rough|rough[- ]in electric)/i],
  ["sheetrock", /\b(drywall|sheetrock|gypsum board)\b/i],
  ["taping", /\b(taping|tape and finish|spackle)\b/i],
  ["framing", /\b(framing|partitions|stud walls?)\b/i],
];
function ciEstimateHints(text, type) {
  const B = ciBenchBook();
  return CI_LINE_TRADES.filter(([id, re]) => re.test(String(text || "")) && B[id] && (!type || !B[id].type || B[id].type === type)).map(([id]) => ({ trade: id, perUnit: B[id].perUnit, per: B[id].per, n: B[id].n, label: B[id].label || ciTrade(id).label, t: `${B[id].label || ciTrade(id).label}: benchmark ${ciCents(B[id].perUnit)} per ${B[id].per} (median of ${B[id].n} ${B[id].type || ""} jobs, approved)`.replace(/\s+/g, " ") }));
}
function ciHintPass() {
  try {
    if (!docOpen || !["estimate", "co"].includes(docOpen.kind) || !Object.keys((DB.company || {}).costBook || {}).length) return;
    const c = (DB.clients || []).find((x) => x.id === clientOpen),
      d = c && (c.estimates || []).concat(c.changeOrders || []).find((x) => x.id === docOpen.id);
    if (!d) return;
    const p = (DB.projects || []).find((x) => x.id === d.projectId),
      M = p ? ciMeasures(p) : {};
    document.querySelectorAll(".view.on tr[data-line]").forEach((tr) => {
      if (tr.querySelector(".ci-hint")) return;
      const l = (d.lines || []).find((x) => x.id === tr.dataset.line);
      if (!l) return;
      const G = ciCostGuide(l, d);
      if (!G.bench.length && !G.factor) return;
      const cell = tr.querySelector("td:nth-child(2)") || tr.firstElementChild;
      cell &&
        cell.insertAdjacentHTML(
          "beforeend",
          (G.factor ? `<div class="small ci-hint" data-cihint="factor:${esc(G.code)}">${esc(G.factorWhy.charAt(0).toUpperCase() + G.factorWhy.slice(1))}${l.costGuide ? ` · applied to the filled cost (${ciMoney(l.costGuide.from)} → ${ciMoney(l.cost)})` : ""}</div>` : "") +
            G.bench
              .map((h) => {
                const T = ciTrade(h.trade),
                  q = +M[T.measure] || 0,
                  want = q ? r2((h.perUnit * q) / (T.scale || 1)) : null;
                return `<div class="small ci-hint" data-cihint="${h.trade}">${esc(h.t)}${want ? ` · this job's ${q} ${esc(T.measure.replace(/([A-Z])/g, " $1").toLowerCase())}: about ${ciMoney(want)} of material` : ""}</div>`;
              })
              .join(""),
        );
    });
  } catch (e) {
    console.warn("costintel: estimate hints", e);
  }
}
if ("function" == typeof render) {
  const ciRenderBase = render;
  render = function () {
    const r = ciRenderBase.apply(this, arguments);
    ciHintPass();
    return r;
  };
}
// ---------------------------------------------------------------------------------------------------------------------
// 8. Driver routes.
//    Phase 1: every item on the pickup list says which store to buy it at and what that saves.
//    Phase 2: the route itself. It minimises item cost + route time × the driver's hourly cost + fuel, over which stores
//    to use (each item from the cheapest store in the set), stock on hand, the order of stops, site delivery windows,
//    the dump stop and van capacity. A store that saves $6 but costs a 40-minute detour is never chosen: the detour costs
//    more in the driver's time than it saves. The coordinator approves the route; the driver gets it on the phone.
//    Travel time sits behind one interface: an offline estimate (demo and tests), or the platform's /api/routes, which
//    calls the Google Maps Routes API once GOOGLE_MAPS_KEY is set in Netlify, and falls back to the estimate otherwise.
// ---------------------------------------------------------------------------------------------------------------------
const CI_ROUTE = { mph: 11, detour: 1.3, parkMin: 3, storeDwell: 15, siteDwell: 10, dumpDwell: 20, yardDwell: 10, startMin: 420, siteOpen: 420, fuelPerMile: 0.32, hourly: 35, latePerMin: 50, maxStores: 7, cap: 1 };
const CI_TRAVEL = {
  offline: {
    id: "offline",
    n: "Offline estimate",
    note: "drive times estimated offline: straight-line distance × 1.3 for the street grid, at 11 mph average with traffic, plus 3 minutes to park",
    leg(a, b) {
      if (!a || !b || null == a.lat || null == b.lat) return { min: 15, miles: 3, guessed: !0 };
      if (a.lat === b.lat && a.lng === b.lng) return { min: 0, miles: 0 };
      const miles = (distM(a, b) / 1609.34) * CI_ROUTE.detour;
      return { min: Math.round(((miles / CI_ROUTE.mph) * 60 + CI_ROUTE.parkMin) * 10) / 10, miles: Math.round(miles * 100) / 100 };
    },
  },
  // the platform's door: one matrix per plan, cached in memory for the day; any failure falls back to the estimate
  platform: {
    id: "google",
    n: "Google Maps Routes",
    note: "drive times from the Google Maps Routes API, with traffic for the departure time",
    cache: {},
    async matrix(points, departAt) {
      const sig = JSON.stringify(points.map((p) => [p.lat, p.lng])) + "|" + (departAt || "");
      if (this.cache[sig]) return this.cache[sig];
      const url = (((window.SDP_CONFIG || {}).aiUrl || "/api/ai").replace(/\/ai$/, "/routes")),
        r = await ("function" == typeof bnFetch ? bnFetch : fetch)(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ points: points.map((p) => ({ lat: p.lat, lng: p.lng })), departAt: departAt || "" }) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || !j.ok || !Array.isArray(j.min)) throw new Error(j.why || j.error || `the route service answered ${r.status}`);
      return (this.cache[sig] = j);
    },
  },
};
let ciTravelUse = "offline",
  ciTravelLast = { source: "offline", note: CI_TRAVEL.offline.note };
// One leg's minutes and miles from the provider in use (a fetched matrix when there is one, else the estimate).
function ciLegFn(matrix, points) {
  const idx = new Map(points.map((p, i) => [p, i]));
  return (a, b) => {
    if (matrix && idx.has(a) && idx.has(b)) {
      const i = idx.get(a),
        j = idx.get(b),
        m = matrix.min[i] && matrix.min[i][j],
        mi = matrix.miles[i] && matrix.miles[i][j];
      // the matrix is wheels turning; parking at the stop is the same few minutes either way
      if (null != m && isFinite(m)) return { min: i === j ? 0 : Math.round((m + CI_ROUTE.parkMin) * 10) / 10, miles: mi || 0 };
    }
    return CI_TRAVEL.offline.leg(a, b);
  };
}
function ciPerms(a) {
  if (a.length <= 1) return [a.slice()];
  const out = [];
  a.forEach((x, i) => ciPerms(a.slice(0, i).concat(a.slice(i + 1))).forEach((p) => out.push([x].concat(p))));
  return out;
}
// the order of a set of stops from a point: every order when there are few, else nearest-next then 2-opt
function ciOrder(from, stops, leg, score) {
  if (stops.length <= 6) {
    let best = null;
    ciPerms(stops).forEach((p) => {
      const s = score ? score(p) : ciPathMin(from, p, leg);
      (!best || s < best.s) && (best = { p: p, s: s });
    });
    return best ? best.p : [];
  }
  const left = stops.slice(),
    path = [];
  let cur = from;
  for (; left.length; ) {
    left.sort((x, y) => leg(cur, x).min - leg(cur, y).min);
    const n = left.shift();
    path.push(n), (cur = n);
  }
  let improved = !0;
  for (let k = 0; improved && k < 20; k++) {
    improved = !1;
    for (let i = 0; i < path.length - 1; i++)
      for (let j = i + 1; j < path.length; j++) {
        const cand = path.slice(0, i).concat(path.slice(i, j + 1).reverse(), path.slice(j + 1));
        (score ? score(cand) < score(path) : ciPathMin(from, cand, leg) < ciPathMin(from, path, leg)) && (path.splice(0, path.length, ...cand), (improved = !0));
      }
  }
  return path;
}
const ciPathMin = (from, path, leg) => path.reduce((a, s, i) => a + leg(i ? path[i - 1] : from, s).min, 0);
// The solver. Pure: everything it needs is in the input, so the route tests can call it on their own bank.
function ciRouteSolve(I, opts) {
  const o = opts || {},
    leg = I.leg || ((a, b) => CI_TRAVEL.offline.leg(a, b)),
    cap = (I.van && I.van.cap) || CI_ROUTE.cap,
    hourly = +I.hourly || CI_ROUTE.hourly,
    fuel = null != I.fuelPerMile ? +I.fuelPerMile : CI_ROUTE.fuelPerMile,
    stores = I.stores || [],
    buys = I.buys || [],
    general = (s) => ["homedepot", "lowes"].includes(s.chain),
    // a known price; null: no price on file, so any general store sells it at the same unknown price; undefined: not here
    priceAt = (b, s) => (b.prices && null != b.prices[s.n] ? +b.prices[s.n] : b.any && general(s) ? null : void 0);
  // which stores can be in a set: any store that carries something, capped at the best few
  let cand = stores.filter((s) => buys.some((b) => void 0 !== priceAt(b, s)));
  if (cand.length > CI_ROUTE.maxStores) {
    const keep = new Set();
    buys.forEach((b) =>
      cand
        .filter((s) => void 0 !== priceAt(b, s))
        .sort((x, y) => (priceAt(b, x) ?? 1e9) - (priceAt(b, y) ?? 1e9))
        .slice(0, 2)
        .forEach((s) => keep.add(s)),
    );
    cand.slice().sort((x, y) => leg(I.start, x).min - leg(I.start, y).min).slice(0, 2).forEach((s) => keep.add(s));
    cand = [...keep].slice(0, CI_ROUTE.maxStores);
  }
  const subsets = [];
  if (o.only) subsets.push(o.only);
  else if (!buys.length) subsets.push([]);
  else for (let m = 1; m < 1 << cand.length; m++) subsets.push(cand.filter((_, i) => m & (1 << i)));
  let best = null;
  subsets.forEach((S) => {
    const assign = [];
    for (const b of buys) {
      const opts2 = S.filter((s) => void 0 !== priceAt(b, s));
      if (!opts2.length) return;
      // unknown price: the same everywhere, so the store that is already on the way; known: the cheapest
      const pick = opts2.slice().sort((x, y) => (priceAt(b, x) ?? 0) - (priceAt(b, y) ?? 0) || S.indexOf(x) - S.indexOf(y))[0];
      assign.push({ b: b, s: pick, price: priceAt(b, pick) });
    }
    if (S.some((s) => !assign.some((a) => a.s === s))) return; // a store in the set that buys nothing is never a stop
    const plan = ciRouteEval(I, S, assign, leg, cap, hourly, fuel);
    plan && (!best || plan.total < best.total - 1e-9) && (best = plan);
  });
  return best;
}
// One set of stores, priced and routed: legs (more than one when the van cannot carry it all), each leg the collect
// stops (warehouse load, yards, stores, other sites' pickups) in their best order, then the sites in the order that
// keeps their windows, a dump run when debris would crowd out the next delivery, and back.
function ciRouteEval(I, S, assign, leg, cap, hourly, fuel) {
  const sites = (I.sites || []).filter((s) => s.items.length || s.garbage > 0),
    volOf = (siteId) => assign.filter((a) => a.b.siteId === siteId).reduce((x, a) => x + (+a.b.vol || 0), 0) + (I.loads || []).filter((l) => l.siteId === siteId).reduce((x, l) => x + (+l.vol || 0), 0) + (I.yards || []).reduce((x, y) => x + y.items.filter((it) => it.siteId === siteId).reduce((z, it) => z + (+it.vol || 0), 0), 0),
    legs = [];
  sites
    .slice()
    .sort((a, b) => volOf(b.id) - volOf(a.id))
    .forEach((s) => {
      const v = volOf(s.id),
        L = legs.find((x) => x.vol + v <= cap + 1e-9);
      L ? (L.sites.push(s), (L.vol += v)) : legs.push({ sites: [s], vol: v });
    });
  legs.length || legs.push({ sites: [], vol: 0 });
  let t = I.startMin || CI_ROUTE.startMin,
    cur = I.start,
    drive = 0,
    miles = 0,
    dwell = 0,
    wait = 0,
    late = 0;
  const stops = [],
    warnings = [],
    go = (to) => {
      const l = leg(cur, to);
      (drive += l.min), (miles += l.miles), (t += l.min), l.guessed && warnings.push(`No location for ${to.n}: its drive time is a guess`), (cur = to);
      return l;
    };
  legs.forEach((L, li) => {
    const ids = new Set(L.sites.map((s) => s.id)),
      myAssign = assign.filter((a) => ids.has(a.b.siteId)),
      myLoads = (I.loads || []).filter((l) => ids.has(l.siteId)),
      myYards = (I.yards || []).map((y) => Object.assign({}, y, { items: y.items.filter((it) => ids.has(it.siteId)) })).filter((y) => y.items.length),
      myStores = S.filter((s) => myAssign.some((a) => a.s === s)),
      collect = myYards.map((y) => ({ kind: "pickup", n: y.n, lat: y.lat, lng: y.lng, ref: y })).concat(myStores.map((s) => ({ kind: "store", n: s.n, lat: s.lat, lng: s.lng, ref: s })));
    myLoads.length && stops.push({ kind: "load", n: I.start.n, lat: I.start.lat, lng: I.start.lng, at: t, items: myLoads, load: 0 });
    let load = myLoads.reduce((a, l) => a + (+l.vol || 0), 0);
    const order = ciOrder(cur, collect, leg);
    order.forEach((c) => {
      go(c);
      const its = "store" === c.kind ? myAssign.filter((a) => a.s === c.ref) : c.ref.items.map((it) => ({ b: it }));
      its.forEach((a) => (load += +a.b.vol || 0));
      const dw = "store" === c.kind ? CI_ROUTE.storeDwell : CI_ROUTE.yardDwell;
      (dwell += dw), (t += dw), stops.push({ kind: c.kind, n: c.n, lat: c.lat, lng: c.lng, at: t - dw, items: its, load: r2(load) });
    });
    // the sites: the order that is latest-safe for the windows, then shortest
    const from0 = cur,
      t0 = t,
      score = (path) => {
        let tt = t0,
          c = from0,
          d = 0,
          lt = 0,
          w = 0;
        path.forEach((s) => {
          const l = leg(c, s);
          (d += l.min), (tt += l.min);
          s.from && tt < s.from && ((w += s.from - tt), (tt = s.from));
          s.to && tt > s.to && (lt += tt - s.to);
          (tt += CI_ROUTE.siteDwell), (c = s);
        });
        return d + w + lt * 100;
      },
      sorder = ciOrder(from0, L.sites, leg, score);
    let garbage = 0;
    sorder.forEach((s, k) => {
      const drop = myAssign.filter((a) => a.b.siteId === s.id).reduce((x, a) => x + (+a.b.vol || 0), 0) + myLoads.filter((l) => l.siteId === s.id).reduce((x, l) => x + (+l.vol || 0), 0) + myYards.reduce((x, y) => x + y.items.filter((it) => it.siteId === s.id).reduce((z, it) => z + (+it.vol || 0), 0), 0);
      // debris on board that would crowd out this delivery goes to the dump first
      if (garbage > 0 && I.dump && load + (s.garbage || 0) - drop > cap + 1e-9) {
        go(I.dump), (dwell += CI_ROUTE.dumpDwell), (t += CI_ROUTE.dumpDwell), (load -= garbage), stops.push({ kind: "dump", n: I.dump.n, lat: I.dump.lat, lng: I.dump.lng, at: t - CI_ROUTE.dumpDwell, garbage: r2(garbage), load: r2(load) }), (garbage = 0);
      }
      go(s);
      s.from && t < s.from && ((wait += s.from - t), (t = s.from));
      s.to && t > s.to && ((late += t - s.to), warnings.push(`${s.n}: arrives ${ciClock(t)}, after its ${s.window || "window"}`));
      (load -= drop), (garbage += s.garbage || 0), (load += s.garbage || 0);
      (dwell += CI_ROUTE.siteDwell), (t += CI_ROUTE.siteDwell), stops.push({ kind: "site", n: s.n, lat: s.lat, lng: s.lng, at: t - CI_ROUTE.siteDwell, siteId: s.id, window: s.window || "", load: r2(load), garbage: r2(garbage) });
    });
    if (garbage > 0 && I.dump) go(I.dump), (dwell += CI_ROUTE.dumpDwell), (t += CI_ROUTE.dumpDwell), (load -= garbage), stops.push({ kind: "dump", n: I.dump.n, lat: I.dump.lat, lng: I.dump.lng, at: t - CI_ROUTE.dumpDwell, garbage: r2(garbage), load: r2(load) });
    (li < legs.length - 1 || I.returnToStart !== !1) && go(I.end || I.start);
    li < legs.length - 1 && warnings.push(`Two trips: the van cannot carry everything at once, so it comes back to ${I.start.n} after ${L.sites.map((s) => s.n).join(", ")}`);
  });
  const itemCost = r2(assign.reduce((a, x) => a + (null == x.price ? 0 : x.price * (+x.b.qty || 0)), 0)),
    routeMin = Math.round((drive + dwell + wait) * 10) / 10,
    laborCost = r2((routeMin / 60) * hourly),
    fuelCost = r2(miles * fuel),
    total = r2(itemCost + laborCost + fuelCost + late * CI_ROUTE.latePerMin);
  return { stores: S.map((s) => s.n), assign: assign.map((a) => ({ key: a.b.key, what: a.b.what, qty: a.b.qty, unit: a.b.unit, siteId: a.b.siteId, store: a.s.n, price: a.price, cost: null == a.price ? null : r2(a.price * a.b.qty) })), stops: stops, itemCost: itemCost, driveMin: Math.round(drive * 10) / 10, dwellMin: dwell, waitMin: Math.round(wait), routeMin: routeMin, miles: Math.round(miles * 100) / 100, laborCost: laborCost, fuelCost: fuelCost, lateMin: Math.round(late), total: total, legs: legs.length, warnings: [...new Set(warnings)], endMin: Math.round(t) };
}
const ciClock = (m) => {
  const h = Math.floor(m / 60),
    mm = Math.round(m % 60);
  return `${((h + 11) % 12) + 1}:${String(mm).padStart(2, "0")} ${h < 12 ? "am" : "pm"}`;
};
// The baseline the optimiser must beat: every item at the store nearest the start that carries it.
function ciRouteNearest(I) {
  const leg = I.leg || ((a, b) => CI_TRAVEL.offline.leg(a, b)),
    general = (s) => ["homedepot", "lowes"].includes(s.chain),
    carries = (b, s) => (b.prices && null != b.prices[s.n]) || (b.any && general(s)),
    S = [];
  (I.buys || []).forEach((b) => {
    const s = (I.stores || []).filter((x) => carries(b, x)).sort((x, y) => leg(I.start, x).min - leg(I.start, y).min)[0];
    s && !S.includes(s) && S.push(s);
  });
  const fixed = Object.assign({}, I, { buys: (I.buys || []).map((b) => Object.assign({}, b, { prices: (() => {
    const s = (I.stores || []).filter((x) => carries(b, x)).sort((x, y) => leg(I.start, x).min - leg(I.start, y).min)[0];
    return s ? { [s.n]: b.prices && null != b.prices[s.n] ? b.prices[s.n] : (b.prices && Object.values(b.prices).length ? Math.max(...Object.values(b.prices)) : 0) } : {};
  })(), any: !1 })) });
  return ciRouteSolve(fixed, { only: S });
}
// ---- the input from the records: what is to be bought, picked from stock, collected, dropped and dumped today
const CI_WINDOW_END = { "By 9 am": 540, "By noon": 720, "By 3 pm": 900, "End of day": 1020 };
function ciDriverHourly() {
  try {
    const u = (DB.users || []).find((x) => "driver" === x.role),
      emp = u && (DB.employees || []).find((e) => e.id === u.employeeId),
      r = emp ? laborRate(emp) : 0;
    return r > 0 ? r2(r) : CI_ROUTE.hourly;
  } catch (e) {
    return CI_ROUTE.hourly;
  }
}
// Each store's recent price for an item on a request, read from the price history (store buys in the last 90 days).
function ciStoreQuotes(what) {
  let H = null;
  try {
    const sk = ciSpec(what);
    H = sk ? (pwData().items["spec:" + sk.key] ? { item: pwData().items[pwResolve("spec:" + sk.key)] } : null) : null;
    H = H || itemPriceHistory(what);
  } catch (e) {}
  const I = H && H.item;
  if (!I) return { prices: {}, label: "" };
  const P = ciStorePrices(I, today(), pwSet().recentDays),
    prices = {};
  P.forEach((x) => (prices[x.store] = x.price));
  return { prices: prices, label: I.label, list: P, key: I.key, unit: I.unit };
}
function ciRouteInput() {
  const WH = DB.company.warehouseGeo || { lat: 40.6784, lng: -73.995, n: "Warehouse" },
    DUMP = DB.company.dumpGeo || { lat: 40.658, lng: -73.988, n: "Cooper Tank transfer station" },
    items = runItems({ bought: {} }).filter((x) => !x.it.done && !x.it.bought),
    sites = {},
    site = (p) =>
      (sites[p.id] =
        sites[p.id] ||
        (() => {
          const g = p.project.geo || null,
            dw = (p.project.delivery || {}).from;
          return { id: p.id, n: p.project.name, lat: g ? g.lat : null, lng: g ? g.lng : null, from: dw || CI_ROUTE.siteOpen, to: null, window: "", items: [], garbage: 0, geo: !!g };
        })()),
    buys = [],
    loads = [],
    yards = {};
  items.forEach((x) => {
    const s = site(x.p),
      it = x.it,
      w = x.r.timeWindow && CI_WINDOW_END[x.r.timeWindow];
    w && (!s.to || w < s.to) && ((s.to = w), (s.window = x.r.timeWindow.toLowerCase()));
    if (it.garbage) return void (s.garbage += VAN_FRACTIONS[it.garbage][1]);
    const vol = itemVolume(it);
    s.items.push(x);
    if (it.invId) return void loads.push({ key: x.key, what: it.what, qty: it.qty, unit: it.unit, vol: vol, siteId: x.p.id, from: it.pickupFrom || "wh" });
    if (/^v:/.test(it.pickupFrom || "")) {
      const vn = it.pickupFrom.slice(2),
        V = (DB.vendors || []).find((v) => v.name === vn) || {};
      return void (yards[vn] = yards[vn] || { n: vn, lat: (V.geo || {}).lat ?? null, lng: (V.geo || {}).lng ?? null, items: [] }).items.push({ key: x.key, what: it.what, qty: it.qty, unit: it.unit, vol: vol, siteId: x.p.id });
    }
    // stock on hand covers what it can: take it from the shelf, buy only the rest
    let qty = +it.qty || 0;
    try {
      const sc = stockCheck({ item: it.what, qty: qty, unit: it.unit });
      sc && "high" === sc.matchConfidence && sc.fromStock > 0 && (loads.push({ key: x.key + ":stock", what: it.what, qty: sc.fromStock, unit: it.unit, vol: (vol * sc.fromStock) / (qty || 1), siteId: x.p.id, from: sc.match.loc, stock: sc.match.name }), (qty = r2(qty - sc.fromStock)));
    } catch (e) {}
    if (!(qty > 0)) return;
    const Q = ciStoreQuotes(it.what);
    buys.push({ key: x.key, what: it.what, qty: qty, unit: it.unit, vol: (vol * qty) / (+it.qty || 1), siteId: x.p.id, prices: Q.prices, any: !Object.keys(Q.prices).length, item: Q.label, reqId: x.r.id, by: x.r.by || "" });
  });
  return {
    start: Object.assign({ n: WH.n || "Warehouse" }, WH),
    end: Object.assign({ n: WH.n || "Warehouse" }, WH),
    dump: Object.assign({ n: DUMP.n }, DUMP),
    stores: STORES.filter((s) => "tile" !== s.chain || 0),
    buys: buys,
    loads: loads,
    yards: Object.values(yards),
    sites: Object.values(sites),
    hourly: ciDriverHourly(),
    fuelPerMile: +((DB.company || {}).fuelPerMile || CI_ROUTE.fuelPerMile),
    van: { cap: CI_ROUTE.cap },
    startMin: CI_ROUTE.startMin,
    date: today(),
  };
}
// Today's plan: the optimiser against the nearest-store baseline, each with its total, in one record shape.
let ciRouteMemo = null;
function ciRoutePlanNow() {
  const I = ciRouteInput();
  if (!I.buys.length && !I.loads.length && !I.sites.length && !I.yards.length) return null;
  const msig = [ciRouteSig(I), JSON.stringify(I.buys.map((b) => b.prices)), today(), ciTravelUse, I.hourly, I.fuelPerMile].join("|");
  if (ciRouteMemo && ciRouteMemo.sig === msig) return ciRouteMemo.N;
  const N = ciRoutePlanCompute(I);
  return (ciRouteMemo = { sig: msig, N: N }), N;
}
function ciRoutePlanCompute(I) {
  const pts = [I.start, I.dump].concat(I.stores, I.sites.filter((s) => null != s.lat), I.yards.filter((y) => null != y.lat)),
    M = ciTravelUse === "google" && CI_TRAVEL.platform.cache[ciTravelSig(pts)];
  I.leg = ciLegFn(M || null, pts);
  const opt = ciRouteSolve(I),
    near = ciRouteNearest(I);
  if (!opt) return null;
  return { date: I.date, input: { buys: I.buys.length, loads: I.loads.length, sites: I.sites.length }, plan: opt, nearest: near, saves: near ? r2(near.total - opt.total) : 0, hourly: I.hourly, fuelPerMile: I.fuelPerMile, travel: M ? { source: "google", note: CI_TRAVEL.platform.note } : { source: "offline", note: CI_TRAVEL.offline.note }, buys: I.buys, sig: ciRouteSig(I) };
}
const ciTravelSig = (pts) => JSON.stringify(pts.map((p) => [p.lat, p.lng])) + "|";
const ciRouteSig = (I) => JSON.stringify([I.buys.map((b) => [b.key, b.qty]), I.loads.map((l) => [l.key, l.qty]), I.sites.map((s) => [s.id, s.garbage, s.to])]);
// Ask the platform for real drive times (Google Maps Routes when the key is set); say plainly when it is not.
async function ciTravelFetch() {
  if (!window.SDP_CONFIG) {
    ciTravelLast = { source: "offline", note: CI_TRAVEL.offline.note, why: "this copy has no platform: Google drive times come from the hosted copy, once GOOGLE_MAPS_KEY is set in Netlify" };
    return toast("Drive times stay estimated: Google Maps drive times come from the hosted copy, once Alan adds the GOOGLE_MAPS_KEY in Netlify"), void render();
  }
  const I = ciRouteInput(),
    pts = [I.start, I.dump].concat(I.stores, I.sites.filter((s) => null != s.lat), I.yards.filter((y) => null != y.lat));
  try {
    const hh = String(Math.floor(CI_ROUTE.startMin / 60)).padStart(2, "0"),
      mm = String(CI_ROUTE.startMin % 60).padStart(2, "0"),
      mo = +today().slice(5, 7),
      M = await CI_TRAVEL.platform.matrix(pts, `${today()}T${hh}:${mm}:00${mo > 3 && mo < 11 ? "-04:00" : "-05:00"}`);
    CI_TRAVEL.platform.cache[ciTravelSig(pts)] = M;
    (ciTravelUse = "google"), (ciTravelLast = { source: "google", note: CI_TRAVEL.platform.note });
    toast("Drive times now from Google Maps");
  } catch (e) {
    (ciTravelUse = "offline"), (ciTravelLast = { source: "offline", note: CI_TRAVEL.offline.note, why: String(e.message || e) });
    toast(`Drive times stay estimated: ${String(e.message || e).slice(0, 140)}`);
  }
  render();
}
// ---- the plan as a store run: planned (drafted), approved (the coordinator), then the existing open and closed
function ciRuns() {
  return (DB.storeRuns = DB.storeRuns || []);
}
const ciRunFor = (date) => ciRuns().filter((r) => r.plan && r.date === date && ["planned", "approved"].includes(r.status)).pop() || null;
function ciApproveRoute() {
  if (!["coord", "owner", "pm"].includes(ciRole())) return toast("The coordinator approves the route"), null;
  const N = ciRoutePlanNow();
  if (!N) return toast("Nothing to route today"), null;
  const old = ciRunFor(N.date);
  old && ((old.status = "replaced"), (old.replacedAt = appNowIso()));
  const run = {
    id: uid("run"),
    date: N.date,
    status: "approved",
    driver: ((DB.users || []).find((u) => "driver" === u.role) || {}).name || "Driver",
    store: N.plan.stores.join(", "),
    plan: { stops: N.plan.stops.map((s) => ({ kind: s.kind, n: s.n, lat: s.lat, lng: s.lng, at: s.at, siteId: s.siteId || "", window: s.window || "", load: s.load, garbage: s.garbage || 0, items: (s.items || []).map((a) => ({ key: (a.b || a).key, what: (a.b || a).what, qty: (a.b || a).qty, unit: (a.b || a).unit, siteId: (a.b || a).siteId, price: a.price ?? null, stock: (a.b || a).stock || "" })) })), assign: N.plan.assign, itemCost: N.plan.itemCost, routeMin: N.plan.routeMin, driveMin: N.plan.driveMin, miles: N.plan.miles, laborCost: N.plan.laborCost, fuelCost: N.plan.fuelCost, total: N.plan.total, warnings: N.plan.warnings, endMin: N.plan.endMin },
    nearest: N.nearest ? { stores: N.nearest.stores, itemCost: N.nearest.itemCost, routeMin: N.nearest.routeMin, total: N.nearest.total, assign: N.nearest.assign } : null,
    saves: N.saves,
    travel: N.travel,
    hourly: N.hourly,
    sig: N.sig,
    approvedBy: ciMe(),
    approvedAt: appNowIso(),
    bought: {},
    receiptId: "",
  };
  ciRuns().push(run);
  try {
    audit("storerun", run.id, "route approved", null, { stores: run.store, total: run.plan.total, saves: run.saves });
    log(`Route approved for ${fmtL(run.date)}: ${run.store} (${ciMoney(run.saves)} under the nearest-store route)`, "manual", run.approvedBy);
    notify(`Route for ${fmtL(run.date)} approved`, `${run.plan.stops.length} stops, ${Math.round(run.plan.routeMin)} minutes. Open Route.`);
  } catch (e) {}
  save(), render();
  toast(`Route approved: ${run.plan.stops.length} stops, ${ciMoney(run.saves)} under buying at the nearest store`, () => ((view = "route"), render()));
  return run;
}
// The approved route goes stale when what is on the list changes; the coordinator is told and the driver is not misled.
const ciRunStale = (run) => {
  try {
    return !!run && run.sig !== ciRouteSig(ciRouteInput());
  } catch (e) {
    return !1;
  }
};
// planDriverDay stays the one route the Route screen and its Navigate links read: the approved route when there is one,
// else today's optimised plan, in the shape it always had.
if ("function" == typeof planDriverDay) {
  const ciPlanDriverDayBase = planDriverDay;
  planDriverDay = function (driverName) {
    const base = ciPlanDriverDayBase.apply(this, arguments);
    try {
      const run = ciRunFor(today()),
        N = run ? null : ciRoutePlanNow(),
        P = run ? run.plan : N && N.plan;
      if (!P) return base;
      const siteRefs = (sid) => (base.stops.find((s) => "site" === s.kind && DB.projects.some((p) => p.id === sid && p.project.name === s.name)) || {}),
        lineOf = (a) => `${a.qty} ${a.unit || ""} ${a.what}`.replace(/\s+/g, " ").trim(),
        stops = P.stops.map((s) => {
          const items = s.items || [];
          if ("site" === s.kind) {
            const B = siteRefs(s.siteId);
            return { kind: "site", name: s.n, geo: null != s.lat ? { lat: s.lat, lng: s.lng } : null, lines: B.lines || [], dropRefs: B.dropRefs || [], note: B.note || "", load: s.load, garbage: s.garbage || 0, at: s.at };
          }
          if ("dump" === s.kind) return { kind: "dump", name: s.n, geo: { lat: s.lat, lng: s.lng }, lines: [`Dump ${Math.round(100 * (s.garbage || 0))}% of a van of debris`], note: "", load: s.load, garbage: 0, at: s.at };
          const verb = "store" === s.kind ? "Buy" : "Load";
          return { kind: "load" === s.kind ? "pickup" : s.kind, name: s.n, geo: null != s.lat ? { lat: s.lat, lng: s.lng } : null, lines: items.map((a) => `${verb} ${lineOf(a.b || a)} → ${ciJobName((a.b || a).siteId)}${(a.b || a).stock ? ` (from stock: ${(a.b || a).stock})` : ""}`), note: "", load: s.load, garbage: 0, at: s.at, ci: !0 };
        });
      stops.forEach((st, i) => {
        i > 0 && st.geo && stops[i - 1].geo && (st.dist = distM(stops[i - 1].geo, st.geo));
      });
      return Object.assign({}, base, { stops: stops, totalKm: r2(stops.reduce((a, s) => a + (s.dist || 0), 0) / 1e3), warnings: (P.warnings || []).concat(base.warnings.filter((w) => /two trips|van/i.test(w) ? !1 : !0)), ci: run ? { approved: run } : { proposed: N } });
    } catch (e) {
      console.warn("costintel: route", e);
      return base;
    }
  };
}
// Phase 1 for one item: which store is cheapest, and what that saves against the store the run would otherwise use
// (the store the driver is at, or else the nearest one to the warehouse that carries it).
function ciPickFor(what, qty, atStore) {
  const Q = ciStoreQuotes(what),
    L = Q.list || [];
  if (!L.length) return null;
  const WH = DB.company.warehouseGeo || { lat: 40.6784, lng: -73.995 },
    best = L[0],
    nearest = L.slice().sort((a, b) => {
      const A = ciStoreByName(a.store),
        B = ciStoreByName(b.store);
      return (A ? distM(WH, A) : 1e9) - (B ? distM(WH, B) : 1e9);
    })[0],
    ref = atStore ? L.find((x) => x.store === atStore) : nearest;
  return { store: best.store, price: best.price, save: ref && ref.store !== best.store ? r2((ref.price - best.price) * (+qty || 0)) : 0, vs: ref && ref.store !== best.store ? ref.store : "", here: atStore ? atStore === best.store : !1, n: L.length };
}
// The route's say on each item: the store it is planned at, the saving against the nearest-store route, and a cheaper
// store the route skipped because the extra stop costs more in driving than it saves.
function ciRouteCtx() {
  try {
    const pl = planDriverDay(""),
      A = pl && pl.ci && pl.ci.approved,
      N = pl && pl.ci && pl.ci.proposed,
      R = A || N;
    return R ? { assign: (A ? A.plan : N.plan).assign || [], near: (R.nearest && R.nearest.assign) || [], approved: !!A } : { assign: [], near: [] };
  } catch (e) {
    return { assign: [], near: [] };
  }
}
function ciItemPick(x, atStore, ctx) {
  const a = (ctx.assign || []).find((y) => y.key === x.key),
    pk = ciPickFor(x.it.what, a ? a.qty : x.it.qty, atStore || "");
  if (!a && !pk) return null;
  if (atStore) return pk ? { store: pk.store, save: pk.save, here: pk.here, plannedHere: !!a && a.store === atStore } : null;
  const n = a && (ctx.near || []).find((y) => y.key === x.key),
    save = a && n && null != n.price && null != a.price && n.store !== a.store ? r2((n.price - a.price) * a.qty) : 0;
  return { store: a ? a.store : pk.store, save: a ? save : pk.save, skipped: a && pk && pk.store !== a.store ? pk.store : "", planned: !!a };
}
// ---- the Route screen: one route card for the driver and the coordinator
const ciCoordName = () => (((DB.users || []).find((u) => "coord" === u.role) || {}).name || "the coordinator").split(" ")[0];
function ciRouteCardHtml(emp) {
  let plan = null;
  try {
    plan = planDriverDay(emp && emp.name);
  } catch (e) {}
  if (!plan || !plan.items) return "";
  const A = plan.ci && plan.ci.approved,
    N = plan.ci && plan.ci.proposed,
    field = ciIsField(),
    canApprove = ["coord", "owner", "pm"].includes(ciRole()),
    P = A ? A.plan : N ? N.plan : null,
    saves = A ? A.saves : N ? N.saves : 0,
    stale = A && ciRunStale(A),
    near = A ? A.nearest : N && N.nearest,
    travel = A ? A.travel : N ? N.travel : ciTravelLast,
    mi = P ? P.miles : r2(plan.totalKm / 1.609),
    head = A ? "Today's Route" : "Suggested Day Plan",
    status = A
      ? `<div class="ci-rt-ok" data-cirtstate="approved">${ICON_CHECK || ""}<span>Approved by <span data-nocase>${esc(A.approvedBy)}</span>, ${esc(fmtL(String(A.approvedAt).slice(0, 10)))}</span></div>${stale ? `<div class="qcheck" data-cirtstale="1">The list changed after the route was approved. ${canApprove ? "Approve it again to send the new route." : `${esc(ciCoordName())} approves the new route.`}</div>` : ""}`
      : `<div class="small muted" data-cirtstate="proposed">${canApprove ? "Proposed by the route planner. Approve it and the driver gets it on his phone." : `Waiting for ${esc(ciCoordName())} to approve.`}</div>`,
    money2 = !field && P
      ? `<div class="ci-rt-sum" data-cirttotal="${P.total}"><span>Items <b>${ciMoney(P.itemCost)}</b></span><span>Driver ${Math.round(P.routeMin)} min <b>${ciMoney(P.laborCost)}</b></span><span>Fuel <b>${ciMoney(P.fuelCost)}</b></span><span>Total <b>${ciMoney(P.total)}</b></span></div>${near ? `<div class="small" data-cirtsaves="${saves}">${saves > 0.005 ? `${ciMoney(saves)} under buying everything at the nearest store (${ciMoney(near.total)}: ${esc((near.stores || []).join(", ") || "none")}).` : "The nearest store is already the cheapest route."}</div>` : ""}<div class="small muted" data-cirttravel="${esc(travel.source)}">${esc(travel.note || "")}${travel.why ? ` · ${esc(travel.why)}` : ""}</div>`
      : saves > 0.005
        ? `<div class="small" data-cirtsaves="${saves}">This route saves ${ciMoney(saves)} against buying it all at the nearest store.</div>`
        : "",
    acts = canApprove
      ? `<div class="row ci-rt-acts">${!A || stale ? `<button type="button" class="btn ${field ? "" : "primary"}" data-ciapprove="1">Approve Route</button>` : ""}<button type="button" class="btn" data-citravel="1">Use Google Drive Times</button></div>`
      : "",
    whyStore = (s) => {
      if ("store" !== s.kind || !P) return "";
      const mine = (P.assign || []).filter((a) => a.store === s.name),
        nAs = (near && near.assign) || [],
        sav = r2(
          mine.reduce((acc, a) => {
            const b = nAs.find((x) => x.key === a.key);
            return acc + (b && null != b.price && null != a.price && b.store !== a.store ? Math.max(0, (b.price - a.price) * a.qty) : 0);
          }, 0),
        );
      return mine.length ? `<div class="s" data-cistorewhy="${esc(s.name)}">${sav > 0.005 ? `Cheapest for ${mine.length === 1 ? "this item" : "these items"}: saves ${ciMoney(sav)}` : mine.some((a) => null == a.price) ? "No price on file for these: the store already on the way" : "Cheapest for these items"}</div>` : "";
    };
  return `<div class="card ci-rt" style="margin-top:10px" data-cirt="1"><div class="hd"><h3>${head}</h3><span class="small muted">${plan.stops.length} stops · ~${mi} mi · ${plan.items} items</span></div>
    ${status}${money2}${acts}
    ${(plan.warnings || []).map((w) => `<div class="qcheck">${esc(w)}</div>`).join("")}
    ${plan.stops
      .map(
        (s, i) =>
          `<div class="stop ${s.kind}"><div class="n">${i + 1}</div><div><b data-nocase>${esc(s.name)}</b>${s.dist ? ` <span class="s">· ${(s.dist / 1609.34).toFixed(1)} mi</span>` : ""}${null != s.at && P ? ` <span class="s">· by ${ciClock(s.at)}</span>` : ""}${s.note ? `<div class="s">${esc(s.note)}</div>` : ""}${whyStore(s)}<ul>${s.lines.map((l, k) => `<li>${esc(l)}${(s.dropRefs || [])[k] ? ` <button type="button" class="btn sm" style="margin:4px 0 4px 8px" data-drvdrop="${esc(s.dropRefs[k].pid)}:${esc(s.dropRefs[k].rid)}">Delivered</button>` : ""}</li>`).join("")}</ul></div><div class="s" style="text-align:right">van after stop<div class="cap ${s.load > 1 ? "over" : ""}"><i style="width:${Math.min(100, Math.max(0, Math.round(100 * (s.load || 0))))}%"></i></div>${Math.max(0, Math.round(100 * (s.load || 0)))}%${s.garbage ? ` · debris ${Math.round(100 * s.garbage)}%` : ""}</div></div>`,
      )
      .join("")}
    ${A ? ciPlanVsReceiptsHtml(A) : ""}
    <div class="small muted" style="margin-top:8px">Deliveries before debris; a dump run when the van fills.</div></div>`;
}
if ("function" == typeof renderDriverPlan)
  renderDriverPlan = function (emp) {
    try {
      return ciRouteCardHtml(emp);
    } catch (e) {
      console.warn("costintel: route card", e);
      return "";
    }
  };
// Phase 1 on the store-run list itself: each item says where it is cheapest and what that saves.
function ciPickHtml(x, atStore, ctx) {
  if (!x || !x.it || x.it.invId || x.it.garbage) return "";
  const pk = ciItemPick(x, atStore, ctx || ciRouteCtx());
  if (!pk) return "";
  // one sentence per line, so the field's Spanish pass reads it whole (the store's name is kept as written)
  if (atStore) {
    if (pk.here) return `<div class="s ci-pick ok" data-cipick="${esc(x.key)}">Best price is here</div>`;
    return pk.save > 0.005 ? `<div class="s ci-pick" data-cipick="${esc(x.key)}">${esc(`Cheaper at ${pk.store} · saves ${ciMoney(pk.save)}`)}</div>` : "";
  }
  return `<div class="s ci-pick" data-cipick="${esc(x.key)}">${esc(`Buy at ${pk.store}${pk.save > 0.005 ? ` · saves ${ciMoney(pk.save)}` : ""}`)}</div>${pk.skipped ? `<div class="s ci-pick muted" data-ciskip="${esc(x.key)}">${esc(`${pk.skipped} is cheaper, but not worth the extra stop today`)}</div>` : ""}`;
}
if ("function" == typeof renderRunCard) {
  const ciRenderRunCardBase = renderRunCard;
  renderRunCard = function (emp) {
    const r = ciRenderRunCardBase.apply(this, arguments);
    try {
      const card = document.getElementById("run-card");
      if (!card) return r;
      const run = activeRun(),
        items = runItems(run || { bought: {} }),
        byKey = new Map(items.map((x) => [x.key, x])),
        ctx = ciRouteCtx();
      // the open run: the store the driver is at, against the best store for each item
      card.querySelectorAll("[data-buy]").forEach((cb) => {
        const row = cb.closest(".shopitem"),
          x = byKey.get(cb.dataset.buy);
        row && x && !row.querySelector("[data-cipick]") && row.children[1] && row.children[1].insertAdjacentHTML("beforeend", ciPickHtml(x, run && run.store, ctx));
      });
      // the preview list: grouped by job as it is, each item with its store (the preview lists every open item in order)
      const shown = [];
      Object.values(items.reduce((a, x) => ((a[x.p.project.name] = a[x.p.project.name] || []).push(x), a), {})).forEach((xs) => xs.forEach((x) => shown.push(x)));
      card.querySelectorAll("details .shopitem").forEach((row, i) => {
        const x = shown[i];
        x && !row.querySelector("[data-cipick]") && row.children[1] && row.children[1].insertAdjacentHTML("beforeend", ciPickHtml(x, "", ctx));
      });
      card.querySelectorAll("[data-ciapprove]").forEach((b) => (b.onclick = () => ciApproveRoute()));
      // one blue button: for the coordinator the safe next step is approving the route, not starting a run
      card.querySelector("[data-ciapprove].primary") && card.querySelectorAll(".btn.primary:not([data-ciapprove])").forEach((b) => b.classList.remove("primary"));
      card.querySelectorAll("[data-citravel]").forEach((b) => (b.onclick = () => ciTravelFetch()));
    } catch (e) {
      console.warn("costintel: run card", e);
    }
    return r;
  };
}
// The actual receipts against the plan: was each item bought at the planned store, at about the planned price.
function ciPlanVsReceipts(run) {
  const D = pwData(),
    after = run.date,
    out = [];
  (run.plan.assign || []).forEach((a) => {
    const sk = ciSpecKey(a.what),
      k = sk ? pwResolve("spec:" + sk) : null,
      buys = D.buys.filter((B) => "receipt" === B.kind && B.date >= after && B.projectId === a.siteId && (k ? B.key === k : pwNorm(B.item) === pwNorm(a.what)));
    const B = buys[0];
    out.push({ key: a.key, what: a.what, qty: a.qty, planned: a.store, plannedPrice: a.price, bought: B ? ciStoreName(B.vendor) : "", paid: B ? B.price : null, diff: B && null != a.price ? r2((B.price - a.price) * Math.min(+a.qty || 0, B.normQty)) : null, asPlanned: !!B && ciStoreName(B.vendor) === a.store });
  });
  return out;
}
function ciPlanVsReceiptsHtml(run) {
  const R = ciPlanVsReceipts(run),
    got = R.filter((r) => r.bought);
  if (!got.length) return "";
  const field = ciIsField(),
    extra = r2(got.reduce((a, r) => a + (r.diff > 0 ? r.diff : 0), 0));
  return `<div class="ci-pvr" data-cipvr="${got.length}"><b class="small">Plan Against the Receipts</b>${got
    .map((r) => `<div class="small" data-cipvrrow="${r.asPlanned ? "planned" : "elsewhere"}">${esc(`${r.asPlanned ? "As planned" : "Bought elsewhere"}: ${r.what} at ${r.bought}`)}${!field && null != r.diff && Math.abs(r.diff) > 0.005 ? `<span> (${r.diff > 0 ? "+" : "−"}${ciMoney(Math.abs(r.diff))} against the plan)</span>` : ""}</div>`)
    .join("")}${!field && extra > 0.005 ? `<div class="small">${ciMoney(extra)} more than planned. ${esc(CI_MONEY_LINE)}</div>` : ""}</div>`;
}
// ---------------------------------------------------------------------------------------------------------------------
// 9. RFQs › Price Watch gains the Receipt Price Book card (the same page, the same history).
// ---------------------------------------------------------------------------------------------------------------------
function ciPriceBookHtml() {
  const B = ciPriceBook(),
    can = ["coord", "owner", "pm"].includes(ciRole()),
    matched = B.filter((x) => x.stores.length > 1);
  return `<div class="card rfq-sec ci-pb" data-cipb="${B.length}"><h3>Receipt Price Book</h3>
    <p class="small muted">Every receipt line the app has read (store receipts, the field's receipts, a Pro account's purchase history), matched across Home Depot, Lowe's, supply houses and lumber yards by UPC or by spec: size, gauge, length, pack and variant. The best price is the lowest at any store in the last ${pwSet().recentDays} days; a buy above it by more than ${ciPbSet().overPct}% is a Cheaper at Another Store case.</p>
    ${B.length ? `<div class="pw-tw"><table class="t ci-pbt"><thead><tr><th>Item</th><th>Best Recent</th><th>Each Store</th><th>Last Bought</th></tr></thead><tbody>${B.map((x) => `<tr data-cipbitem="${esc(x.key)}"><td><b data-nocase>${esc(x.item)}</b><div class="small muted">per ${esc(x.unit)}${x.raw.length > 1 ? ` · ${x.raw.length} descriptions matched` : ""}</div></td><td>${x.best ? `<b>${pwU2(x.best.price)}</b><div class="small" data-nocase>${esc(x.best.store)}, ${fmtL(x.best.date)}</div>` : '<span class="small muted">none in 90 days</span>'}</td><td class="small" data-nocase>${x.stores.map((s) => `${esc(s.store)} ${pwU2(s.price)}`).join("<br>") || "—"}</td><td class="small" data-nocase>${esc(x.last.store)} ${pwU2(x.last.price)}<br>${fmtL(x.last.date)}</td></tr>`).join("")}</tbody></table></div><p class="small">${agN(matched.length, "item")} priced at more than one store.</p>` : '<p class="small">No receipt has been read yet.</p>'}
    <h4 style="margin:12px 0 4px">Where Prices Come From</h4>${CI_RETAILERS.map((r) => `<div class="pw-row"><span class="grow small"><b>${esc(r.n)}</b> · ${r.connected ? "connected" : "not connected"}<br>${esc(r.how)}. <span class="muted">${esc(r.api)}.</span></span></div>`).join("")}
    ${can ? `<div class="row" style="margin-top:8px"><button type="button" class="btn" data-ciimport="1">Import Purchase History</button></div>` : ""}</div>`;
}
if ("function" == typeof pwPageHtml) {
  const ciPwPageBase = pwPageHtml;
  pwPageHtml = function () {
    const h = ciPwPageBase.apply(this, arguments);
    try {
      return h.replace(/<\/div>\s*$/, ciPriceBookHtml() + "</div>");
    } catch (e) {
      console.warn("costintel: price book", e);
      return h;
    }
  };
}
if ("function" == typeof pwWirePage) {
  const ciPwWireBase = pwWirePage;
  pwWirePage = function (host) {
    ciPwWireBase.apply(this, arguments);
    host && host.querySelectorAll("[data-ciimport]").forEach((b) => (b.onclick = () => ciImportDialog()));
  };
}
function ciImportDialog() {
  mbModal(
    "Import Purchase History",
    `<p class="small">Paste the purchase history your Pro account exports (CSV, with its header row). Each transaction becomes a receipt document; nothing is read from a retailer's website.</p>${mbF("Retailer", mbSel("retailer", CI_RETAILERS.filter((r) => ["homedepot", "lowes"].includes(r.id)).map((r) => [r.id, r.n]), "homedepot"))}${mbF("The Export", '<textarea data-f="csv" rows="8" placeholder="Date,Store Number,Transaction ID,SKU,UPC,Description,Quantity,Unit Price,Extended Price,Job Name"></textarea>')}`,
    {
      submit: "Import",
      onSubmit: (f) => {
        const R = ciImportPurchaseHistory(f.csv, f.retailer);
        if (!R.ok) return toast(R.why), !1;
        render();
        toast(`${agN(R.made.length, "receipt")} filed from the purchase history${R.skipped ? `, ${R.skipped} already on file` : ""}`, () => ("function" == typeof pwOpenPage ? pwOpenPage() : null));
      },
    },
  );
}

// ---------------------------------------------------------------------------------------------------------------------
// 10. The brain's weekly review: what went wrong more than once, with a dollar or hour value, proposed through the
//     brain's own channel (Company › Changes). Approved: a rule or process becomes a lesson, code a build request.
//     Mined: overruns (a trade running over the comparable jobs), price outliers (cheaper at another store, again and
//     again), waste (bought far beyond what was installed), delays (vendors late on promises and orders), repeated
//     questions (the same site question asked again).
// ---------------------------------------------------------------------------------------------------------------------
const ciWeekOf = (d) => {
  const x = parse(d),
    day = (x.getDay() + 6) % 7;
  return iso(addDays(d, -day));
};
function ciWeeklyFindings() {
  const out = [],
    wk = ciWeekOf(today());
  const tryM = (name, fn) => {
    try {
      fn();
    } catch (e) {
      console.warn("costintel: weekly", name, e);
    }
  };
  // overruns: a trade's last three comparable jobs against the jobs before them
  tryM("overrun", () =>
    CI_TRADES.forEach((T) => {
      const S = ciCloseouts()
        .filter((c) => "brownstone" === c.type)
        .sort((a, b) => String(a.closedOn).localeCompare(String(b.closedOn)))
        .map((c) => ciSample(c, T.id))
        .filter(Boolean);
      if (S.length < 5) return;
      const last = S.slice(-3),
        prior = S.slice(0, -3),
        mL = ciMedian(last.map((s) => s.perUnit)),
        mP = ciMedian(prior.map((s) => s.perUnit)),
        pct = ciPct(mL, mP);
      if (!(pct >= 10)) return;
      const causes = last.map((s) => ciDecompose(s, prior).cause),
        cause = ["price", "waste", "quantity"].map((c) => [c, causes.filter((x) => x === c).length]).sort((a, b) => b[1] - a[1])[0][0],
        avgQty = last.reduce((a, s) => a + s.qty, 0) / last.length,
        perJob = r2(((mL - mP) * avgQty) / (T.scale || 1)),
        perYear = r2(perJob * Math.max(1, ciJobsPerYear("brownstone")));
      out.push({
        key: `weekly:overrun:${T.id}:${wk}`,
        kind: "price" === cause ? "rule" : "setting",
        brainKind: "overrun",
        title: `${T.label} ran ${Math.round(pct)}% over on the last 3 brownstones: ${"price" === cause ? "price it from the supplier that held the old price, or re-quote it" : "raise the template allowance"}`,
        because: `${last.map((s) => `${s.job} ${ciCents(s.perUnit)}`).join(", ")} per ${T.per}, against ${ciCents(mP)} on the ${prior.length} before them. The cause on ${causes.filter((c) => c === cause).length} of 3 is ${cause}.`,
        value: { dollars: perYear, hours: 0, basis: `${ciCents(perJob)} a job × ${ciJobsPerYear("brownstone")} brownstones a year` },
        delta: "price" === cause ? { path: `company.ciRules.${T.id}Price`, from: null, to: `Rough material for ${T.label.toLowerCase()} is re-quoted before each job; the last three ran ${Math.round(pct)}% over on price`, label: `${T.label}: re-quote before each job` } : { path: `company.costBook.bench.${T.id}`, from: ciBenchBook()[T.id] || null, to: { perUnit: r2(mL), per: T.per, type: "brownstone", n: 3, at: today(), label: T.label }, label: `Template allowance for ${T.label.toLowerCase()}` },
        evidence: last.map((s) => `${s.job}: ${ciCents(s.material)} for ${s.qty} = ${ciCents(s.perUnit)} per ${T.per}`),
        lesson: `${T.label}: carry ${ciCents(mL)} per ${T.per} on brownstones and re-quote the material before ordering`,
      });
    }),
  );
  // price outliers: the same item bought above the best store more than once in 90 days
  tryM("price", () => {
    const C = pwCases("pwStoreCheaper").filter((c) => c.at >= iso(addDays(today(), -90))),
      D = pwData(),
      by = {};
    C.forEach((c) =>
      (c.lines || []).forEach((l) => {
        const k = l.store + "|" + l.key,
          x = (by[k] = by[k] || { store: l.store, item: (D.items[l.key] || {}).label || l.item, key: l.key, n: 0, save: 0, from: new Set() });
        (x.n += 1), (x.save = r2(x.save + l.save)), x.from.add(c.vendor);
      }),
    );
    Object.values(by)
      .filter((x) => x.n >= 2)
      .forEach((x) =>
        out.push({
          key: `weekly:price:${x.key}:${wk}`,
          kind: "rule",
          brainKind: "price",
          title: `Buy ${x.item} at ${x.store}: bought ${x.n} times elsewhere in 90 days for ${ciCents(x.save)} more`,
          because: `${x.n} receipts from ${[...x.from].join(" and ")} paid above ${x.store}'s price for the same item (matched by spec).`,
          value: { dollars: r2(x.save * 4), hours: 0, basis: `${ciCents(x.save)} in 90 days, a year at the same rate` },
          delta: { path: `company.ciRules.store_${String(x.key).replace(/[^a-z0-9]/gi, "_")}`, from: null, to: `${x.item}: ${x.store} first`, label: `Preferred store for ${x.item}` },
          evidence: C.filter((c) => (c.lines || []).some((l) => l.key === x.key)).map((c) => `${c.what}: ${c.sub}`),
          lesson: `${x.item}: the driver's list sends it to ${x.store} unless it is out of stock`,
        }),
      );
  });
  // waste: a trade bought well beyond what was installed on more than one job
  tryM("waste", () =>
    CI_TRADES.forEach((T) => {
      const F = ciBenchFlags().filter((f) => f.trade === T.id && "waste" === f.cause && !f.live);
      if (!F.length) return;
      const S = ciCloseouts().filter((c) => "brownstone" === c.type).map((c) => ciSample(c, T.id)).filter(Boolean),
        waste = (s) => {
          const b = s.items.reduce((a, x) => a + x.bought, 0),
            u = s.items.reduce((a, x) => a + x.used, 0);
          return u ? b / u - 1 : 0;
        },
        med = ciMedian(S.map(waste)),
        dollars = r2(F.reduce((a, f) => a + f.dollars, 0));
      out.push({
        key: `weekly:waste:${T.id}:${wk}`,
        kind: "rule",
        brainKind: "waste",
        title: `${T.label}: order to the takeoff plus ${Math.round(med * 100) + 2}%, not by eye`,
        because: `${F.map((f) => `${f.job} bought ${f.why.replace(/^waste: /, "")}`).join("; ")}.`,
        value: { dollars: r2(dollars * Math.max(1, ciJobsPerYear("brownstone") / Math.max(1, S.length))), hours: 0, basis: `${ciCents(dollars)} of material bought and not installed` },
        delta: { path: `company.ciRules.${T.id}Waste`, from: null, to: `Order ${T.label.toLowerCase()} to the takeoff plus ${Math.round(med * 100) + 2}%`, label: `${T.label}: order to the takeoff` },
        evidence: F.map((f) => `${f.job}: ${ciCents(f.perUnit)} per ${f.per} against ${ciCents(f.median)} (${f.why})`),
        lesson: `${T.label}: the order is the takeoff plus ${Math.round(med * 100) + 2}%; anything more needs the PM's reason`,
      });
    }),
  );
  // delays: a vendor that broke promises or shipped late more than once
  tryM("delay", () => {
    const P = "function" == typeof trkPromises ? trkPromises().filter((p) => "broken" === p.status) : [],
      by = {};
    P.forEach((p) => ((by[p.vendor] = by[p.vendor] || []).push(p)));
    Object.entries(by)
      .filter(([, L]) => L.length >= 2)
      .forEach(([v, L]) => {
        const days = L.reduce((a, p) => a + Math.max(1, dayDiff(p.due, p.closedAt || today())), 0);
        out.push({ key: `weekly:delay:${v}:${wk}`, kind: "rule", brainKind: "delay", title: `${v}: confirm in writing two days before every date, and line up a second source`, because: `${agN(L.length, "promise")} broken: ${L.map((p) => p.what).slice(0, 3).join("; ")}.`, value: { dollars: 0, hours: days * 4, basis: `${days} days late × 4 crew-hours held each day (an assumption the owner can change)` }, delta: { path: `company.ciRules.vendor_${pwVKey(v)}`, from: null, to: `${v}: written confirmation two days ahead`, label: `Vendor rule for ${v}` }, evidence: L.map((p) => `${p.what} due ${fmtL(p.due)}: ${p.evidence || "not kept"}`), lesson: `${v}: written confirmation two days before every delivery date` });
      });
  });
  // repeated questions: the same site question raised again
  tryM("questions", () => {
    const R = ((DB.field || {}).raises || []).filter((r) => "question" === r.type || "drawing" === r.type),
      by = {};
    R.forEach((r) => {
      const k = pwNorm(String(r.title || "").replace(/\b(at|on|in)\s+\d+\s+\w+.*$/i, "")).split(" ").slice(0, 4).join(" ");
      k && (by[k] = by[k] || []).push(r);
    });
    Object.entries(by)
      .filter(([, L]) => L.length >= 3)
      .forEach(([k, L]) => out.push({ key: `weekly:q:${k}:${wk}`, kind: "code", brainKind: "questions", title: `Answer "${L[0].title}" on the screen where it is asked`, because: `Asked ${L.length} times: ${L.map((r) => ciJobName(r.projectId)).filter(Boolean).join(", ")}.`, value: { dollars: 0, hours: r2((L.length * 15) / 60), basis: "15 minutes each time it is asked and answered" }, evidence: L.map((r) => `${r.title} (${ciJobName(r.projectId)})`), lesson: "" }));
  });
  return out.sort((a, b) => (b.value.dollars || 0) - (a.value.dollars || 0) || (b.value.hours || 0) - (a.value.hours || 0));
}
const ciJobsPerYear = (type) => {
  const from = iso(addDays(today(), -365));
  return Math.max(1, ciCloseouts().filter((c) => c.type === type && c.closedOn >= from).length);
};
function ciWeekly(src) {
  const F = ciWeeklyFindings(),
    by = src === "button" ? ciMe() : "The Brain (weekly)";
  DB.changes = DB.changes || [];
  const fresh = F.filter((f) => !DB.changes.some((c) => c.key === f.key || (c.ciBase && c.ciBase === f.key.replace(/:\d{4}-\d{2}-\d{2}$/, "") && "declined" === c.status)));
  fresh.forEach((f) =>
    DB.changes.push({
      id: uid("ch"),
      key: f.key,
      ciBase: f.key.replace(/:\d{4}-\d{2}-\d{2}$/, ""),
      title: f.title,
      why: `${f.because} Worth ${f.value.dollars ? ciMoney(f.value.dollars) + " a year" : ""}${f.value.dollars && f.value.hours ? " and " : ""}${f.value.hours ? `${f.value.hours} hours` : ""} (${f.value.basis}). ${CI_MONEY_LINE}`,
      kind: f.kind,
      delta: f.delta || null,
      evidence: (f.evidence || []).map((t) => ({ t: String(t), m: "the records" })),
      status: "draft",
      at: today(),
      by: "The Brain (weekly)",
      source: "brain-weekly",
      brainKind: f.brainKind,
      value: f.value,
      lesson: f.lesson || "",
    }),
  );
  ((DB.company = DB.company || {}).ciWeekly = { at: appNowIso(), day: today(), by: by, found: F.length, proposed: fresh.length });
  if (fresh.length)
    try {
      paNudge(`The Brain's weekly review proposed ${agN(fresh.length, "change")}.`, `From this week's overruns, prices, waste, delays and repeated questions: ${fresh.map((f) => `"${f.title}"`).slice(0, 3).join(", ")}${fresh.length > 3 ? " and more" : ""}. Each says what it is worth; approve or decline them under Company › Changes.`, { kind: "brain", id: "weekly-" + today() }, "the Brain's weekly review");
    } catch (e) {}
  return save(), fresh;
}
// on the first app day of a new week, once
"undefined" != typeof APP_DAY_HOOKS &&
  APP_DAY_HOOKS.push([
    "ciWeekly",
    () => {
      const W = (DB.company || {}).ciWeekly;
      return !W || ciWeekOf(W.day) !== ciWeekOf(today()) ? (ciWeekly("day"), !0) : !1;
    },
  ]);
// An approved weekly proposal becomes a lesson (rules and processes); code is approved for the next build as before.
if ("function" == typeof mtChangeApply) {
  const ciChangeApplyBase = mtChangeApply;
  mtChangeApply = function (ch) {
    const r = ciChangeApplyBase.apply(this, arguments);
    try {
      if (ch && ["brain-weekly", "benchmark"].includes(ch.source) && ch.lesson && !(DB.lessons || []).some((l) => l.fromChange === ch.id)) {
        (DB.lessons = DB.lessons || []).push({ id: uid("ln"), title: ch.lesson, trigger: "weekly", match: ch.brainKind || "", when: "now", then: { kind: "rule", title: ch.lesson, owner: "coord" }, why: ch.why, evidence: (ch.evidence || []).map((e) => e.t), source: "Learned", taughtBy: ((currentUser() || {}).name) || "Owner", at: today(), auto: !1, active: !0, fired: [], fromChange: ch.id, value: ch.value || null });
        audit("lesson", ch.id, "approved", "", ch.lesson, "an approved weekly proposal became a lesson");
      }
    } catch (e) {
      console.warn("costintel: lesson", e);
    }
    return r;
  };
}

// ---------------------------------------------------------------------------------------------------------------------
// 11. Savings: realised only, pushed to the savings lane's registry (never a ledger here).
// ---------------------------------------------------------------------------------------------------------------------
function ciSavingsRows() {
  const out = [];
  ciRuns()
    .filter((r) => r.plan && ["approved", "closed"].includes(r.status) && r.nearest)
    .forEach((run) => {
      ciPlanVsReceipts(run)
        .filter((x) => x.asPlanned && null != x.paid)
        .forEach((x) => {
          const n = (run.nearest.assign || []).find((a) => a.key === x.key);
          if (!n || null == n.price || n.store === x.bought) return;
          const amt = r2((n.price - x.paid) * (+x.qty || 0));
          amt > 0.005 && out.push({ amount: amt, evidence: `Route ${fmtL(run.date)}: ${x.what} bought at ${x.bought} as planned (${pwU2(x.paid)}); the nearest store, ${n.store}, had it at ${pwU2(n.price)}`, by: run.approvedBy || "", at: run.date, source: "costintel:route", jobId: (run.plan.assign.find((a) => a.key === x.key) || {}).siteId || "" });
        });
    });
  return out;
}
try {
  window.SV_SOURCES = window.SV_SOURCES || [];
  window.SV_SOURCES.includes(ciSavingsRows) || window.SV_SOURCES.push(ciSavingsRows);
} catch (e) {}
// ---------------------------------------------------------------------------------------------------------------------
// 12. Reports › Projects › Cost Intelligence: the jobs spending more than they bring in, and the benchmarks.
// ---------------------------------------------------------------------------------------------------------------------
try {
  const g = REP_GROUPS.find((x) => "jobs" === x.id);
  g && !g.tabs.some((t) => "costintel" === t[0]) && g.tabs.splice(2, 0, ["costintel", "Cost Intelligence"]);
  REP_DEFS.costintel = "Jobs spending more than they bring in, by line, with the cause and the fix; and rough material per unit against comparable past jobs.";
  "undefined" != typeof POINT_IN_TIME_TABS && !POINT_IN_TIME_TABS.includes("costintel") && POINT_IN_TIME_TABS.push("costintel");
} catch (e) {}
function ciJobCardHtml(x) {
  const canFix = ["owner", "pm"].includes(ciRole()),
    fig = (l, v, d) => `<div><span>${l}</span><b${d ? ` data-ci${d}="${r2(v)}"` : ""}>${ciMoney(v)}</b></div>`;
  return `<div class="card ci-job${ciFocusJob === x.p.id ? " on" : ""}" data-cijob="${esc(x.p.id)}" data-ciamount="${x.amount}"><div class="hd"><h3 data-nocase>${esc(x.p.project.name)}</h3><span class="pill warn">${ciMoney(x.amount)} at stake</span></div>
    <div class="ci-figs">${fig("Cash In", x.cash.in, "cashin")}${fig("Cash Out", x.cash.out, "cashout")}${fig("Billed", x.billed, "billed")}${fig("Cost to Date", x.actual, "actual")}</div>
    <ul class="ci-why">${x.reasons.map((r) => `<li data-cireason="${r.kind}"><b>${esc(r.t.charAt(0).toUpperCase() + r.t.slice(1))}.</b>${r.cause ? ` <span class="small">Cause: ${esc(r.cause)}.</span>` : ""}</li>`).join("")}</ul>
    ${x.fixes.length ? `<div class="ci-fix">${x.fixes.map((f) => `<div class="pw-row"><span class="grow small">${esc(f.t)}</span>${canFix ? `<button type="button" class="btn sm" data-cifix="${esc(f.kind)}" data-cijobid="${esc(x.p.id)}" data-cikey="${esc(f.key || f.clientId || "")}">${esc(f.label)}</button>` : ""}</div>`).join("")}</div>` : ""}
    ${x.lines.length ? `<div class="tw"><table class="t ci-lines"><thead><tr><th>Line</th><th class="money">Budget</th><th class="money">Spent</th><th class="money">Committed</th><th class="money">Forecast</th><th class="money">Over</th><th>Cause and Fix</th></tr></thead><tbody>${x.lines
      .map(
        (l) =>
          `<tr data-ciline="${esc(l.key)}" data-cikind="${l.kind}"><td><b data-nocase>${esc(l.name)}</b><div class="small muted">${{ over: "over budget", committed: "committed past its budget", measured: "forecast to go over" }[l.kind]}</div></td><td class="money">${ciMoney(l.budget)}</td><td class="money">${ciMoney(l.actual)}</td><td class="money">${ciMoney(l.committed)}</td><td class="money">${ciMoney(l.forecast)}</td><td class="money bad">${ciMoney(l.over)}</td><td class="small">${esc(l.cause || "")}${l.fix ? `<div>${esc(l.fix.t)}</div>${canFix ? `<button type="button" class="btn sm" data-cilinefix="${esc(l.fix.kind)}" data-cijobid="${esc(x.p.id)}" data-cikey="${esc(l.key)}" data-cibill="${esc(l.fix.billId || "")}">${esc(l.fix.label)}</button>` : ""}` : ""}</td></tr>`,
      )
      .join("")}</tbody></table></div>` : ""}</div>`;
}
function ciBenchHtml() {
  const B = ciBenchmarks("brownstone"),
    F = ciBenchFlags(),
    can = ["owner", "pm", "controller"].includes(ciRole()),
    jobs = ciComparables("brownstone", "");
  return `<h3 class="rep-h">Benchmarks From Past Jobs</h3><p class="small muted">Rough material per unit on ${agN(jobs.length, "closed brownstone job")} (${jobs.map((j) => esc(j.name)).join(", ")}). A job or line more than ${CI_BENCH.overPct}% above the median of the others is flagged with its cause: quantity, price or waste. A benchmark reaches estimating only when the owner approves it under Company › Changes.</p>
  <div class="tw"><table class="t ci-bench"><thead><tr><th>Trade</th><th class="money">Median</th><th>Range</th><th>Jobs</th><th>In Estimating</th><th></th></tr></thead><tbody>${B.map(
    (b) =>
      `<tr data-cibench="${b.trade}" data-cimedian="${b.median}"><td><b>${esc(b.label)}</b><div class="small muted">per ${esc(b.per)}${b.altPer ? ` · ${ciCents(b.altMedian)} per ${esc(b.altPer)}` : ""}</div></td><td class="money">${null == b.median ? "—" : ciCents(b.median)}</td><td class="small">${null == b.min ? "—" : `${ciCents(b.min)} to ${ciCents(b.max)}`}</td><td>${b.n}</td><td class="small">${b.inEstimating ? `${ciCents(b.inEstimating.perUnit)} per ${esc(b.inEstimating.per)}, approved ${fmtL(b.inEstimating.at)}` : '<span class="muted">not yet</span>'}</td><td>${can && b.enough && (!b.inEstimating || Math.abs(b.inEstimating.perUnit - b.median) > 0.005) ? `<button type="button" class="btn sm" data-ciprop="${b.trade}">Propose to Estimating</button>` : ""}</td></tr>`,
  ).join("")}</tbody></table></div>
  ${(() => {
    const F = Object.entries(((DB.company || {}).costBook) || {}).filter(([k, v]) => "bench" !== k && +v > 0);
    return `<p class="small" data-cifactors="${F.length}"><b>What new estimates carry</b> (one book, Company › Changes approves every entry): ${F.length ? F.map(([k, v]) => `${esc(k)} ${esc((COST_CODES.find((x) => x[0] === k) || [k, ""])[1])} ×${v} (close-out factor)`).join("; ") : "no close-out cost factor approved yet"}; ${Object.keys(ciBenchBook()).length ? Object.entries(ciBenchBook()).map(([t, b]) => `${esc(b.label || t)} ${ciCents(b.perUnit)} per ${esc(b.per)}`).join("; ") : "no benchmark approved yet"}. The item library's fill applies the factor to the unit cost it fills; the estimate shows both next to the line.</p>`;
  })()}
  <h3 class="rep-h">Above the Benchmark <span class="pill${F.length ? " warn" : ""}" data-ciflagn="${F.length}">${F.length}</span></h3>${
    F.length
      ? F.map((f) => `<div class="pw-row" data-ciflag="${esc(f.key)}"><span class="grow small"><b data-nocase>${esc(f.job)}</b>${f.live ? ' <span class="pill info">running</span>' : ""} · ${esc(f.label)}${f.line ? ` (<span data-nocase>${esc(f.line.name)}</span>)` : ""}: ${f.priceOnly ? `paying ${Math.round((f.priceIdx - 1) * 100)}% above comparable jobs' prices` : `${ciCents(f.perUnit)} per ${esc(f.per)} against a ${ciCents(f.median)} median (+${f.pct}%)`}<br>${esc(f.why)} · ${ciMoney(f.dollars)}</span></div>`).join("")
      : '<p class="small">No job is more than 15% above its comparables.</p>'
  }`;
}
function ciTabHtml() {
  const J = PRED.jobsOverspending.rows(),
    W = (DB.company || {}).ciWeekly,
    waiting = (DB.changes || []).filter((c) => ["brain-weekly", "benchmark"].includes(c.source) && "draft" === c.status).length,
    owner = ["owner", "pm", "controller"].includes(ciRole());
  return `<div class="ci-tab"><div class="rep-head"><div><h2 style="margin:0">Cost Intelligence</h2><div class="small muted">As of ${fmtL(today())}. Every figure is read from the job's own records and opens them.</div></div></div>
    <h3 class="rep-h">Jobs Spending More Than They Bring In <span class="pill${J.length ? " warn" : ""}" data-cijobn="${J.length}">${J.length}</span></h3>
    <p class="small muted">One rule: cash out above cash in, cost ahead of billings, a line over its budget (the same rows as Over Budget on Caught for You) or forecast to go over (committed past its budget, or measured progress that projects more than ${CI_RULE.forecastOverPct}% past it). ${esc(CI_MONEY_LINE)}</p>
    ${J.length ? J.map(ciJobCardHtml).join("") : '<p class="small">Every live job is bringing in at least what it spends, and no line is over or heading over.</p>'}
    ${ciBenchHtml()}
    ${owner ? `<h3 class="rep-h">The Brain's Weekly Review</h3><div class="pw-row"><span class="grow small">${W ? `Last run ${fmtL(W.day)}: ${agN(W.found, "finding")}, ${agN(W.proposed, "new proposal")}.` : "Runs on the first day of each week."} ${agN(waiting, "proposal")} from it wait${1 === waiting ? "s" : ""} in Company › Changes.</span><button type="button" class="btn sm" data-ciweekly="1">Run the Review Now</button>${waiting ? '<button type="button" class="btn sm" data-cichanges="1">Open Changes</button>' : ""}</div>` : ""}</div>`;
}
if ("function" == typeof renderReports) {
  const ciRenderReportsBase = renderReports;
  renderReports = function () {
    const out = ciRenderReportsBase.apply(this, arguments);
    try {
      if ("reports" !== view || "costintel" !== repTab) return out;
      const host = document.getElementById("rep-print-area");
      if (!host) return out;
      host.innerHTML = ciTabHtml();
      ciWireTab(host);
      ciFocusJob && setTimeout(() => {
        const el = host.querySelector(`[data-cijob="${CSS.escape(ciFocusJob)}"]`);
        el && el.scrollIntoView && el.scrollIntoView({ block: "start" });
        ciFocusJob = "";
      }, 30);
    } catch (e) {
      console.warn("costintel: tab", e);
    }
    return out;
  };
}
function ciWireTab(host) {
  host.querySelectorAll("[data-ciprop]").forEach((b) => (b.onclick = () => ciProposeBench(b.dataset.ciprop, "brownstone")));
  host.querySelectorAll("[data-ciweekly]").forEach(
    (b) =>
      (b.onclick = () => {
        const n = ciWeekly("button");
        render();
        toast(n.length ? `The weekly review proposed ${agN(n.length, "change")}` : "Nothing new this week: every finding is already proposed or decided", n.length ? () => ciOpenChanges() : null);
      }),
  );
  host.querySelectorAll("[data-cichanges]").forEach((b) => (b.onclick = () => ciOpenChanges()));
  host.querySelectorAll("[data-cifix]").forEach(
    (b) =>
      (b.onclick = () => {
        const k = b.dataset.cifix;
        if ("bill" === k && b.dataset.cikey) return void rtbAct(b.dataset.cikey);
        if ("chase" === k) {
          const c = (DB.clients || []).find((x) => x.id === b.dataset.cikey);
          return void (c ? flowGo.client(c)() : ((view = "billing"), render()));
        }
      }),
  );
  host.querySelectorAll("[data-cilinefix]").forEach(
    (b) =>
      (b.onclick = () => {
        const k = b.dataset.cilinefix,
          pid = b.dataset.cijobid;
        if ("co" === k) return void ciDraftCO(pid, b.dataset.cikey);
        if ("dispute" === k) {
          const bill = (DB.bills || []).find((x) => x.id === b.dataset.cibill);
          return void (bill && (isOwner() ? billAction(bill, "short") : flowGo.bill(bill)()));
        }
        (repTab = "profit"), (repProj = pid), render();
      }),
  );
}

// ---------------------------------------------------------------------------------------------------------------------
// 13. Ask: the tables the model and the Report Builder read, and the questions answered locally from the same rows.
//     Field roles read no money: the route table names stores and items, its prices and savings are stripped for them.
// ---------------------------------------------------------------------------------------------------------------------
const CI_EQ = {
  jobmoney: () =>
    PRED.jobsOverspending.rows().flatMap((x) =>
      [{ _id: x.key, _module: "Reports", _label: `${x.p.project.name} · spending more than it brings in`, _go: { view: "reports", tab: "costintel" }, projectId: x.p.id, project: x.p.project.name, row: "job", cashIn: x.cash.in, cashOut: x.cash.out, billed: x.billed, actual: x.actual, amount: x.amount, reasons: x.reasons.map((r) => r.t).join("; "), fixes: x.fixes.map((f) => f.t).join("; ") }].concat(
        x.lines.map((l) => ({ _id: `${x.key}:${l.key}`, _module: "Reports", _label: `${x.p.project.name} · ${l.name}`, _go: { view: "reports", tab: "costintel" }, projectId: x.p.id, project: x.p.project.name, row: "line", line: l.name, lineKey: l.key, kind: l.kind, budget: l.budget, actual: l.actual, committed: l.committed, forecast: l.forecast, overBy: l.over, cause: l.cause || "", fix: (l.fix || {}).t || "" })),
      ),
    ),
  benchmarks: () =>
    ciBenchmarks("brownstone").flatMap((b) =>
      [{ _id: "bench:" + b.trade, _module: "Reports", _label: `${b.label} benchmark`, _go: { view: "reports", tab: "costintel" }, row: "benchmark", trade: b.label, per: b.per, median: b.median, low: b.min, high: b.max, jobs: b.n, inEstimating: b.inEstimating ? b.inEstimating.perUnit : null }].concat(
        b.samples.map((s) => ({ _id: `bench:${b.trade}:${s.jobId}`, _module: "Reports", _label: `${s.job} · ${b.label}`, _go: { view: "reports", tab: "costintel" }, row: "job", trade: b.label, job: s.job, closed: s.closedOn, per: b.per, perUnit: s.perUnit, material: s.material, measure: s.qty })),
      ),
    ),
  benchflags: () => ciBenchFlags().map((f) => ({ _id: f.key, _module: "Reports", _label: `${f.job} · ${f.label}`, _go: { view: "reports", tab: "costintel" }, projectId: f.projectId, job: f.job, running: f.live, trade: f.label, per: f.per, perUnit: f.perUnit, median: f.median, overPct: f.pct, cause: f.cause, why: f.why, overBy: f.dollars })),
  pricebook: () =>
    ciPriceBook().flatMap((x) =>
      (x.stores.length ? x.stores : [{ store: x.last.store, price: x.last.price, date: x.last.date }]).map((s) => ({ _id: `pb:${x.key}:${s.store}`, _module: "Purchasing", _label: `${x.item} · ${s.store}`, _go: { view: "rfq", rfqTab: "pricewatch" }, item: x.item, unit: x.unit, store: s.store, price: s.price, date: s.date, best: !!x.best && x.best.store === s.store, bestStore: x.best ? x.best.store : "", bestPrice: x.best ? x.best.price : null })),
    ),
  routeplan: () => {
    let plan = null;
    try {
      plan = planDriverDay("");
    } catch (e) {}
    const A = plan && plan.ci && plan.ci.approved,
      N = plan && plan.ci && plan.ci.proposed,
      P = A ? A.plan : N ? N.plan : null;
    return P
      ? (P.assign || []).map((a) => ({ _id: `rt:${a.key}`, _module: "Purchasing", _label: `${a.what} at ${a.store}`, _go: { view: "route" }, date: (A || N).date, status: A ? "approved" : "proposed", store: a.store, item: a.what, qty: a.qty, unit: a.unit, project: ciJobName(a.siteId), projectId: a.siteId, price: a.price, cost: a.cost }))
      : [];
  },
};
const CI_EQ_ALIAS = { overspending: "jobmoney", cashnegative: "jobmoney", jobcash: "jobmoney", benchmark: "benchmarks", costbenchmarks: "benchmarks", aboveBenchmark: "benchflags", abovebenchmark: "benchflags", receiptprices: "pricebook", storeprices: "pricebook", route: "routeplan", routes: "routeplan", pickuplist: "routeplan" };
try {
  Object.keys(CI_EQ).forEach((k) => {
    EQ_TABLES[k] || (EQ_TABLES[k] = () => CI_EQ[k]());
    "routeplan" !== k && !EQ_MONEY_TABLES.includes(k) && EQ_MONEY_TABLES.push(k);
  });
  Object.entries(CI_EQ_ALIAS).forEach(([a, k]) => EQ_TABLES[a.toLowerCase()] || EQ_ALIAS[a.toLowerCase()] || (EQ_ALIAS[a.toLowerCase()] = k));
  "undefined" != typeof MD_VIEWS && Object.assign(MD_VIEWS, { jobmoney: ["reports"], benchmarks: ["reports"], benchflags: ["reports"], pricebook: ["rfq", "reports"], routeplan: ["route"] });
} catch (e) {
  console.warn("costintel: Ask tables", e);
}
const CI_ASK = [
  {
    id: "overspending",
    rx: /\b(spend(ing)?|spent) more than (it|they|we) (bring|brings|brought|take|takes) in\b|\bcash[- ]negative\b|\bcash out (is )?(more|greater|bigger|higher) than( the)? cash in\b|\b(jobs?|projects?) (losing|burning) (money|cash)\b|\bforecast to go over\b/,
    roles: ["owner", "pm", "controller", "billing", "design_mgr"],
    answer: () => {
      const R = PRED.jobsOverspending.rows();
      return {
        headline: R.length ? `${agN(R.length, "job is", "jobs are")} spending more than ${1 === R.length ? "it brings" : "they bring"} in: ${R.map((x) => `${x.p.project.name} (${ciMoney(x.amount)} at stake)`).join(", ")}.` : "No live job is spending more than it brings in, and no line is over or heading over.",
        work: R.flatMap((x) => x.reasons.map((r) => `${x.p.project.name}: ${r.t}`).concat(x.lines.map((l) => `${x.p.project.name} · ${l.name}: ${l.why}. Cause: ${l.cause}. Fix: ${(l.fix || {}).t || ""}`))),
        go: { view: "reports", tab: "costintel" },
        n: R.length,
      };
    },
  },
  {
    id: "benchmark",
    rx: /\bbenchmarks?\b|\b(cost|material) per (fixture|device|board|bath|lf|linear foot|sf|square foot)\b|\bper (fixture|device|board)\b|\babove the (median|benchmark)\b/,
    roles: ["owner", "pm", "controller", "coord", "billing", "design_mgr"],
    answer: (l) => {
      const B = ciBenchmarks("brownstone"),
        T = B.find((b) => new RegExp(b.label.toLowerCase().split(" ").slice(0, 2).join(" ")).test(l) || (/plumb/.test(l) && "roughPlumbing" === b.trade) || (/electric|device/.test(l) && "roughElectric" === b.trade) || (/sheetrock|drywall|board/.test(l) && "sheetrock" === b.trade) || (/tap(e|ing)|compound|mud/.test(l) && "taping" === b.trade) || (/fram|lumber|stud/.test(l) && "framing" === b.trade)),
        F = ciBenchFlags().filter((f) => !T || f.trade === T.trade);
      return {
        headline: T ? `${T.label}: ${ciCents(T.median)} per ${T.per}, the median of ${agN(T.n, "closed brownstone job")} (${ciCents(T.min)} to ${ciCents(T.max)})${T.inEstimating ? `; estimating carries ${ciCents(T.inEstimating.perUnit)}` : "; not yet approved for estimating"}. ${agN(F.length, "job is", "jobs are")} more than 15% above it.` : `Benchmarks on ${agN(ciComparables("brownstone", "").length, "closed brownstone job")}: ${B.map((b) => `${b.label.toLowerCase()} ${ciCents(b.median)} per ${b.per}`).join("; ")}. ${agN(F.length, "flag")} above them.`,
        work: F.map((f) => `${f.job} · ${f.label}: ${f.priceOnly ? "price" : `${ciCents(f.perUnit)} per ${f.per} (+${f.pct}%)`}: ${f.why}`),
        go: { view: "reports", tab: "costintel" },
        n: F.length,
      };
    },
  },
  {
    id: "store",
    rx: /\b(where|which store|what store)\b.*\b(buy|get|cheapest|cheaper)\b|\bcheapest (store|place|price)\b|\bprice book\b|\bcheaper at\b/,
    roles: ["owner", "pm", "coord", "controller", "billing", "driver", "foreman"],
    answer: (l) => {
      const words = l.replace(/\b(where|which|what|store|should|do|we|i|buy|get|the|cheapest|cheaper|is|are|for|to|price|book|a|an|at)\b/g, " ").replace(/\s+/g, " ").trim(),
        Q = words ? ciStoreQuotes(words) : { list: [] },
        field = ciIsField();
      if (!Q.list || !Q.list.length) return { headline: words ? `No store price on file for ${words} in the last 90 days.` : `The receipt price book holds ${agN(ciPriceBook().length, "item")}; ask for one by name.`, work: [], go: field ? { view: "route" } : { view: "rfq", rfqTab: "pricewatch" }, n: 0 };
      const b = Q.list[0],
        w = Q.list[Q.list.length - 1];
      return {
        headline: field ? `Buy ${Q.label} at ${b.store}${Q.list.length > 1 ? `: it is the cheapest of ${Q.list.length} stores` : ""}.` : `${Q.label}: cheapest at ${b.store}, ${pwU2(b.price)} per ${Q.unit} (${fmtL(b.date)})${Q.list.length > 1 ? `; ${w.store} charged ${pwU2(w.price)}` : ""}.`,
        work: field ? Q.list.map((x) => x.store) : Q.list.map((x) => `${x.store}: ${pwU2(x.price)} per ${Q.unit}, ${fmtL(x.date)} (${x.source})`),
        go: field ? { view: "route" } : { view: "rfq", rfqTab: "pricewatch" },
        n: Q.list.length,
      };
    },
  },
  {
    id: "route",
    rx: /\b(today'?s|the|my|driver'?s?) route\b|\broute (for )?today\b|\bwhich stores? (today|on the route)\b|\bpickup list\b/,
    roles: ["owner", "pm", "coord", "driver"],
    answer: () => {
      const plan = planDriverDay(""),
        A = plan.ci && plan.ci.approved,
        N = plan.ci && plan.ci.proposed,
        P = A ? A.plan : N ? N.plan : null,
        field = ciIsField();
      if (!P) return { headline: "Nothing on the route today.", work: [], go: { view: "route" }, n: 0 };
      return {
        headline: `${A ? `Today's route, approved by ${A.approvedBy}` : "Today's suggested route, waiting on the coordinator"}: ${agN(plan.stops.length, "stop")}${P.stores.length ? `, buying at ${P.stores.join(" and ")}` : ""}${field ? "" : `; ${ciMoney(P.total)} in all, ${ciMoney((A || N).saves)} under the nearest store`}.`,
        work: plan.stops.map((s, i) => `${i + 1}. ${s.name}: ${s.lines.join("; ")}`),
        go: { view: "route" },
        n: plan.stops.length,
      };
    },
  },
];
function ciAskRoute(q) {
  const r = ciRole(),
    l = String(q || "").toLowerCase().replace(/\s+/g, " ").trim(),
    it = CI_ASK.find((x) => x.rx.test(l) && x.roles.includes(r));
  return it ? Object.assign(it.answer(l), { kind: "ci-" + it.id, routedBy: "costintel" }) : null;
}
if ("function" == typeof paAsk) {
  const ciPaAskBase = paAsk;
  paAsk = function (q) {
    let a = null;
    try {
      a = ciAskRoute(q);
    } catch (e) {
      console.warn("costintel ask", e), (a = null);
    }
    if (a) {
      try {
        paInit();
      } catch (e) {}
      return paOut(Object.assign({}, a, { go: a.go ? paGo(a.go) : null, offers: [] }));
    }
    return ciPaAskBase.apply(this, arguments);
  };
}
if ("function" == typeof palIndex) {
  const ciPalBase = palIndex;
  palIndex = function () {
    const items = ciPalBase.apply(this, arguments);
    try {
      ciCan("reports") && items.push({ k: "view", t: "Cost Intelligence", s: "Jobs spending more than they bring in, and the benchmarks", go: () => ciOpenTab("") });
      ciCan("reports") && PRED.jobsOverspending.rows().forEach((x) => items.push({ k: "Cost Intelligence", t: `Spending more than it brings in: ${x.p.project.name}`, s: x.reasons[0].t, go: () => ciOpenTab(x.p.id) }));
    } catch (e) {}
    return items;
  };
}
"undefined" != typeof AG_DICT && "benchmark benchmarks fixture fixtures sheetrock taping cheapest pickup".split(" ").forEach((w) => AG_DICT.add(w));

// ---------------------------------------------------------------------------------------------------------------------
// 14. The demo: invented past jobs (close-outs), store receipts at line level, and 121 State's measures. Guarded: on the
//     hosted copy, once the server holds the firm's records, none of this is written (sdSeedsOff).
// ---------------------------------------------------------------------------------------------------------------------
const CI_DEMO_ITEMS = {
  roughPlumbing: [["1/2 in PEX-A pipe 100 ft coil", "coil", 40.0, 0.55], ["3/4 in PEX-A pipe 100 ft coil", "coil", 70.0, 0.18], ["1/2 in PEX-A elbow", "ea", 1.65, 6], ["1/2 in brass ball valve", "ea", 11.5, 1.2]],
  roughElectric: [["12/2 NM-B wire 250 ft", "roll", 105.0, 0.045], ["14/2 NM-B wire 250 ft", "roll", 82.0, 0.03], ["1-gang new work box", "ea", 0.68, 1]],
  sheetrock: [["1/2 in regular drywall 4x8", "sheet", 12.4, 0.6], ["5/8 in Type X drywall 4x8", "sheet", 14.6, 0.3], ["1/2 in moisture resistant drywall 4x8", "sheet", 15.8, 0.1]],
  taping: [["All purpose joint compound 4.5 gal", "bucket", 17.0, 0.0042], ["Paper drywall tape 500 ft", "roll", 6.5, 0.0016], ["Metal corner bead 8 ft", "ea", 3.4, 0.012]],
  framing: [["2x4x8 KD SPF stud", "ea", 4.1, 0.9], ["2x4x16 KD SPF", "ea", 8.8, 0.14], ["2x6x12 Douglas fir KD", "ea", 15.4, 0.05]],
};
// [id, name, type, closedOn, measures {fixtures, baths, devices, sf, boards, tapeSf, framingLf}, {trade: [price factor, waste, quantity factor]}]
const CI_DEMO_JOBS = [
  ["co_ci_berkeley", "88 Berkeley Place", "brownstone", "2025-03-28", { fixtures: 11, baths: 3, devices: 180, sf: 3600, boards: 340, tapeSf: 10880, framingLf: 720 }, { roughPlumbing: [1.2, 0.06, 1] }],
  ["co_ci_clinton", "312 Clinton Street", "brownstone", "2025-06-20", { fixtures: 9, baths: 2, devices: 150, sf: 3000, boards: 290, tapeSf: 9280, framingLf: 610 }, { framing: [1, 0.06, 1.25] }],
  ["co_ci_strong", "19 Strong Place", "brownstone", "2025-10-10", { fixtures: 10, baths: 3, devices: 170, sf: 3400, boards: 320, tapeSf: 10240, framingLf: 680 }, { sheetrock: [1, 0.25, 1] }],
  ["co_ci_w22", "455 West 22nd Street", "brownstone", "2026-01-23", { fixtures: 14, baths: 4, devices: 210, sf: 4200, boards: 400, tapeSf: 12800, framingLf: 820 }, { roughElectric: [1.24, 0.06, 1] }],
  ["co_ci_ppw", "71 Prospect Park West", "brownstone", "2026-04-17", { fixtures: 12, baths: 3, devices: 190, sf: 3800, boards: 360, tapeSf: 11520, framingLf: 760 }, { roughElectric: [1.26, 0.06, 1] }],
  ["co_ci_garden", "27 Garden Place", "brownstone", "2026-06-12", { fixtures: 8, baths: 2, devices: 145, sf: 2900, boards: 275, tapeSf: 8800, framingLf: 580 }, { roughElectric: [1.25, 0.06, 1] }],
  ["co_ci_water", "200 Water Street, unit 12B", "condo", "2026-02-20", { fixtures: 7, baths: 2, devices: 80, sf: 1400, boards: 120, tapeSf: 3840, framingLf: 210 }, {}],
];
const CI_DEMO_VENDORS = { roughPlumbing: "Ferguson — Brooklyn", roughElectric: "Home Depot — Gowanus", sheetrock: "Quality Building Supply — Park Slope", taping: "Quality Building Supply — Park Slope", framing: "Brooklyn Lumber — Red Hook" };
function ciDemoCloseout(row) {
  const [id, name, type, closedOn, m, F] = row,
    meas = Object.assign({ sheetrockSf: m.boards * 32 }, m),
    buys = [];
  CI_TRADES.forEach((T) => {
    const [pf, wf, qf] = F[T.id] || [1, 0.06, 1],
      q = +meas[T.measure] || 0;
    CI_DEMO_ITEMS[T.id].forEach(([item, unit, ref, per]) => {
      const used = Math.max(1, Math.round(per * q * qf)),
        bought = Math.round(used * (1 + wf));
      buys.push({ trade: T.id, item: item, unit: unit, used: used, bought: bought, price: r2(ref * pf), vendor: CI_DEMO_VENDORS[T.id], date: iso(addDays(closedOn, -60)) });
    });
  });
  return { id: id, name: name, type: type, closedOn: closedOn, measures: meas, buys: buys, source: "demo", at: closedOn, by: "Imported close-out" };
}
// The receipts: [id, store, number, date, jobId, txnId, [[description, sku, qty, price]]]. Five of them back card
// lines already in the demo bank feed, to the cent (t4, t10, t14, ta9); the rest are earlier purchase history.
const CI_DEMO_RECEIPTS = [
  ["dc_ci_r1", "Home Depot — Gowanus", "1265-00418", "2026-06-18", "", "", [["2X4-8 KD STUD SPF", "161640", 60, 4.27], ["1/2 IN X 4 FT X 8 FT REGULAR DRYWALL", "586498", 30, 13.98], ["12/2 NM-B ROMEX 250FT", "128198", 2, 112.0], ["1/2 IN X 100 FT PEX-A PIPE RED", "319011", 2, 44.97]]],
  ["dc_ci_r2", "Lowe's — Gowanus", "1675-22107", "2026-07-09", "", "", [["2-IN X 4-IN X 8-FT KILN-DRIED SPF STUD", "6005", 40, 4.38], ["SOUTHWIRE 250-FT 12/2 ROMEX NM-B", "70920", 3, 96.48], ["1/2-IN X 4-FT X 8-FT REGULAR DRYWALL PANEL", "12235", 24, 12.48], ["ALL PURPOSE JOINT COMPOUND 4.5 GAL", "33671", 4, 17.98]]],
  ["dc_ci_r3", "Brooklyn Lumber — Red Hook", "BL-30871", "2026-07-22", "", "", [["2X4 8' KD SPF STUD", "", 120, 3.98], ["2X6 12' DOUGLAS FIR KD", "", 24, 15.2], ["3/4 CDX PLYWOOD 4X8", "", 10, 54.9]]],
  ["dc_ci_r4", "Ferguson — Brooklyn", "FB-118204", "2026-07-30", "", "", [["1/2\" PEX-A PIPE 100FT RED", "UP100A12", 4, 38.4], ["3/4\" PEX-A PIPE 100FT", "UP100A34", 2, 69.8], ["1/2\" PEX-A ELBOW 25PK", "UPQ4751", 2, 40.5]]],
  ["dc_ci_r5", "Quality Building Supply — Park Slope", "QBS-55190", "2026-08-05", "", "", [["5/8 TYPE X DRYWALL 4X8", "", 60, 14.33], ["1/2 REGULAR DRYWALL 4X8", "", 40, 11.2], ["ALL PURPOSE JOINT COMPOUND 4.5 GAL", "", 6, 16.4]]],
  ["dc_ci_r6", "Home Depot — Flatbush", "6166-01944", "2026-08-14", "p121", "t4", [["2X4-8 KD STUD SPF", "161640", 100, 4.47], ["2X6-12 DOUGLAS FIR KD", "161926", 20, 16.48], ["3/4 IN CDX PLYWOOD 4X8", "166014", 6, 62.4], ["SIMPSON A35 ANGLE 50PK", "100375", 1, 31.49]]],
  ["dc_ci_r7", "Home Depot — Gowanus", "1265-07722", "2026-08-27", "p121", "t10", [["2X4-8 KD STUD SPF", "161640", 150, 4.47], ["2X4-16 KD SPF", "161675", 40, 9.98], ["5/8 IN TYPE X DRYWALL 4X8", "561118", 40, 17.48], ["3/4 IN CDX PLYWOOD 4X8", "166014", 3, 62.95]]],
  ["dc_ci_r8", "Home Depot — Gowanus", "1265-08113", "2026-09-01", "", "t14", [["1-5/8 COARSE DRYWALL SCREW 5LB", "100148", 6, 27.98], ["3 IN CONSTRUCTION SCREW 5LB", "205601", 5, 19.09]]],
  ["dc_ci_r9", "Brooklyn Lumber — Red Hook", "BL-31502", "2026-09-02", "", "ta9", [["2X4 8' KD SPF STUD", "", 200, 3.98], ["2X6 12' DOUGLAS FIR KD", "", 40, 15.2], ["3/4 CDX PLYWOOD 4X8", "", 9, 54.9], ["2X4 16' KD SPF", "", 8, 8.49]]],
];
function ciSeed() {
  if ("function" == typeof sdSeedsOff && sdSeedsOff()) return;
  if (DB.__ciSeed || !DB.projects || !DB.projects.length) return;
  DB.__ciSeed = 1;
  const C = ciCloseouts();
  CI_DEMO_JOBS.forEach((row) => C.some((c) => c.id === row[0]) || C.push(ciDemoCloseout(row)));
  const p = DB.projects.find((x) => "p121" === x.id);
  p && !p.project.measures && ((p.project.measures = { fixtures: 9, baths: 2, devices: 165, sf: 3200, boards: 310, sheetrockSf: 9920, tapeSf: 9920, framingLf: 640 }), (p.project.jobType = "brownstone"));
  const have = new Set((DB.docs || []).map((d) => d.id));
  CI_DEMO_RECEIPTS.forEach(([id, store, number, date, jobId, txnId, lines]) => {
    if (have.has(id)) return;
    if (txnId && !(DB.txns || []).some((t) => t.id === txnId)) txnId = "";
    ciNewReceipt({ id: id, store: store, number: number, date: date, jobId: jobId, txnId: txnId, lines: lines.map(([item, sku, qty, price]) => ({ item: item, sku: sku, qty: qty, price: price })), source: { type: "demo", retailer: (ciStoreOf(store) || {}).chain || "" }, by: "Purchase history" });
  });
}
if ("function" == typeof finishBoot) {
  const ciFinishBootBase = finishBoot;
  finishBoot = function () {
    const r = ciFinishBootBase.apply(this, arguments);
    try {
      const first = !DB.__ciSeed;
      ciSeed(), first && DB.__ciSeed && save();
    } catch (e) {
      console.error("costintel: seed", e);
    }
    return r;
  };
}

// ---------------------------------------------------------------------------------------------------------------------
// 15. Styles (phone first: no table pushes the page sideways; buttons are 44px on a phone)
// ---------------------------------------------------------------------------------------------------------------------
(function ciStyles() {
  if (document.getElementById("ci-styles")) return;
  const s = document.createElement("style");
  s.id = "ci-styles";
  s.textContent = `.ci-tab,.ci-pb,.ci-rt{max-width:100%;overflow-wrap:anywhere}
.ci-tab .tw,.ci-pb .pw-tw{overflow-x:auto;max-width:100%}
.ci-job{margin:10px 0}.ci-job.on{outline:2px solid var(--accent,#2563eb)}
.ci-figs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:6px 0 8px}
.ci-figs>div{display:flex;flex-direction:column;border:1px solid var(--rule);border-radius:var(--r,8px);padding:6px 8px}
.ci-figs span{font-size:11.5px;color:var(--ink-3)}
.ci-why{margin:4px 0 8px 18px;padding:0}.ci-why li{margin:2px 0}
.ci-lines td,.ci-lines th,.ci-bench td,.ci-bench th,.ci-pbt td,.ci-pbt th{vertical-align:top}
.ci-rt-sum{display:flex;flex-wrap:wrap;gap:6px 14px;margin:6px 0;font-size:13px}
.ci-rt-ok{display:flex;gap:6px;align-items:center;font-size:13px;color:var(--ok,#15803d)}
.ci-rt-acts{gap:8px;flex-wrap:wrap;margin:6px 0}
.ci-pick{color:var(--ink-2)}.ci-pick.ok{color:var(--ok,#15803d)}
.ci-pvr{margin-top:8px;border-top:1px solid var(--rule);padding-top:6px}
@media (max-width:700px){.ci-figs{grid-template-columns:1fr 1fr}.ci-tab .btn.sm,.ci-rt .btn,.ci-pb .btn{min-height:44px}.ci-lines th:nth-child(7),.ci-lines td:nth-child(7){min-width:180px}}`;
  document.head.appendChild(s);
})();
