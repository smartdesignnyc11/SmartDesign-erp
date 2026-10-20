// =====================================================================================================================
// Items: one library that fills every line (BACKLOG §1.18; lane "items and Spanish", 2026-10-20).
// Alan, 2026-10-11: "an important feature". Most buying starts from a line, and every line used to be typed by hand.
//
// Design gate (§1.16). The noun is "item". Its one store stays DB.company.itemLib (itemLib()), the library the
// Settings card already kept; nothing new holds items.
//  - Sources the search reads, never stores: what the firm has BOUGHT is the one price history (pwData /
//    itemPriceHistory, price watch: PO lines, bills, card lines, confirmed quotes); what it has SOLD is the estimates
//    and change orders (costLibrary). A library item and its history are joined by name, so "last paid" is always
//    today's history, not a copy.
//  - itemFind(q, ctx) is the one search. Every line that is typed uses it through one picker (itpShow): estimate,
//    change order and invoice lines (sell side), PO lines, the coordinator's item list behind an estimate line,
//    RFQ lines, bill lines, the field's request box and receipt lines (buy side). It replaces the history pop
//    (libShow) and the native datalists on those inputs, so a line has one picker, not two.
//  - Picking an item fills the line through that line's own record (the document, the PO) or, for a form that is
//    read when it is sent, through its fields. Each filled field is recorded on the line (l.fill: from where, when,
//    by whom, which fields) and every field can still be changed on that document.
//  - Field roles (foreman, crew, driver) never see a price in the picker: name, description, unit and vendor only.
//  - Learning is proposals, never silent: itemProposals() reads use (a name on two or more lines that is not in the
//    library), purchases (the last buy moved the unit cost more than 10%) and signed estimates (a description the
//    library lacks). The owner or the estimator (PM) approves; the change is written on the item's own history
//    (item.hist, append-only: who, when, why). A declined proposal is remembered in DB.company.itemLibDeclined, the
//    library's own map, or the same proposal would come back every day. Changing the library never rewrites a sent
//    document: only a line being typed is filled.
//  - Assemblies are library items (kind "assembly") whose parts are other items with a quantity per measure.
//  - Recent picks are a per-person convenience in localStorage, never a record.
// Queryable: EQ_TABLES.items and EQ_TABLES.itemproposals (Ask, ⌘K, the Report Builder); field roles get no money.
// =====================================================================================================================
const IT_FIELD = ["foreman", "crew", "driver"],
  IT_SELL = ["estimate", "co", "invoice"],
  itMe = () => ("function" == typeof currentUser && currentUser()) || {},
  itIsField = () => IT_FIELD.includes(String(itMe().role || ("function" == typeof role ? role() : ""))),
  itCanApprove = () => ["owner", "pm"].includes("function" == typeof role ? role() : ""),
  itNorm = (s) => ("function" == typeof normItem ? normItem(s) : String(s || "").toLowerCase().trim()),
  itMoney2 = (n) => {
    const v = +n || 0;
    return "$" + (Math.abs(v) >= 100 ? Math.round(v).toLocaleString("en-US") : v.toFixed(2));
  };
function itemLibDeclined() {
  const C = DB.company || (DB.company = {});
  return (C.itemLibDeclined = C.itemLibDeclined || {}), C.itemLibDeclined;
}
const itemById = (id) => (id ? itemLib().find((x) => x.id === id) || null : null);

// ---- the house style (the Standard, estimating playbook: "plain-language scope: the client should understand
// exactly what is included and what is not"). itemStyle tidies a description; itemDescribe drafts one for an item that
// has none, from its cost code: what we do, what it includes, what it does not.
const IT_ABBR = [
  [/\bw\/o\b/gi, "without"],
  [/\bw\//gi, "with "],
  [/\bincl\.?(?=\s)/gi, "including"],
  [/\bexcl\.?(?=\s)/gi, "excluding"],
  [/\bapprox\.?(?=\s)/gi, "approximately"],
  [/\bqty\b/gi, "quantity"],
  [/\binstall'?n\b/gi, "installation"],
  [/\bS&I\b/g, "supply and install"],
  [/\bF&I\b/g, "furnish and install"],
  [/\bGC\b/g, "general contractor"],
  [/\s&\s/g, " and "],
  [/\betc\.?$/i, "and similar"],
];
function itemStyle(text) {
  let s = String(text || "").replace(/\r/g, "");
  if (!s.trim()) return "";
  return s
    .split("\n")
    .map((line) => {
      let t = line.replace(/[ \t]+/g, " ").replace(/\s+$/, "");
      if (!t.trim()) return "";
      const lead = (t.match(/^\s*(?:[-•*]\s*)?/) || [""])[0];
      let body = t.slice(lead.length);
      // a line typed in capitals reads as shouting to a client: sentence case, keeping short codes (DOB, LPC, GFCI)
      /[a-z]/.test(body) || (body = body.toLowerCase().replace(/\b(dob|lpc|gfci|afci|hvac|led|pvc|pex|mdf|osb|lvl|nyc|ny)\b/g, (w) => w.toUpperCase()));
      IT_ABBR.forEach(([re, w]) => (body = body.replace(re, w)));
      body = body.replace(/\s{2,}/g, " ").trim();
      body = body.charAt(0).toUpperCase() + body.slice(1);
      return (lead.trim() ? "- " : "") + body;
    })
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
// by cost code: [what we do, includes, excludes]
const IT_SCOPE = {
  "01": ["Site supervision and general conditions for the duration of the work", "a foreman on site, daily protection and cleanup, dumpsters and disposal, permits and filing as listed, and insurance", "work by the owner's own trades"],
  "02": ["Careful demolition and removal", "protection of the areas we keep, separation of anything salvaged and labeled, debris carted away", "hazardous materials abatement, which is priced separately if testing finds any"],
  "03": ["Framing and rough carpentry", "layout checked against the drawings, blocking for fixtures, cabinets and grab bars", "structural repairs found once walls are open, which we price before doing them"],
  "04": ["Supply and installation", "removal of what is replaced, flashing, sealing and interior trim to match", "Landmarks filing if the work needs one, unless listed separately"],
  "05": ["Plumbing by SD Plumbing", "rough-in, pressure test, finish connections and filing with the Department of Buildings where required", "fixtures and fittings unless listed, and work to a gas service"],
  "06": ["Electrical by SD Electric", "rough wiring, devices, circuit tests, panel labeling and filing where required", "light fixtures unless listed, and utility company work"],
  "07": ["Insulation, drywall and finishing", "insulation, board, tape and three coats of compound, sanded and primed", "plaster restoration and finish paint, listed separately"],
  "08": ["Tile installation", "layout reviewed with you before setting, waterproofing in wet areas, setting materials, grout and sealer", "tile supply unless listed, and stone fabrication"],
  "09": ["Flooring", "floor preparation, installation and transitions at doorways", "moving furniture and repairs to the subfloor found under existing finishes"],
  "10": ["Millwork and countertops", "shop drawings for your approval, delivery, installation and adjustment", "appliances and plumbing fixtures"],
  "11": ["Finish carpentry, doors and hardware", "doors hung and adjusted, casings and base to match the existing profiles, hardware installed", "hardware supply unless listed"],
  "12": ["Paint and restoration", "surface preparation, patching, primer and two finish coats in the colours you choose", "wallcovering, decorative finishes and lead abatement"],
  "13": ["Fixtures and appliances", "delivery check, installation, connection and a test with you", "the fixtures and appliances themselves unless listed"],
  "14": ["Permits, inspections and fees", "filing, the fees listed, scheduling inspections and attending them", "fees for work outside this scope"],
};
function itemDescribe(it) {
  if (!it) return "";
  const nm = String(it.name || "").trim();
  if (it.desc && it.desc.trim()) return itemStyle(it.desc);
  const S0 = IT_SCOPE[it.code];
  if (!S0) return nm ? itemStyle(`${nm}, as shown on the drawings.`) : "";
  return [`${S0[0]}: ${nm.charAt(0).toLowerCase() + nm.slice(1)}.`, `Includes ${S0[1]}.`, `Excludes ${S0[2]}.`].join("\n");
}
// what a vendor reads on a PO or RFQ: the item, its spec, the unit it is priced in
function itemVendorText(it, h) {
  if (it && it.vendorDesc && it.vendorDesc.trim()) return it.vendorDesc.trim();
  const nm = String((it && it.name) || (h && h.name) || "").trim(),
    u = (it && it.unit) || (h && h.unit) || "";
  return nm ? `${nm}${u && "ls" !== u ? `, priced per ${u}` : ""}. As specified; tell us of any substitution before it ships.` : "";
}

// ---- the Spanish the crew types into a request box, to the item it means (§1.20: trade words as the crew says them)
const IT_ES = {
  tornillo: "screw", tornillos: "screws", clavo: "nail", clavos: "nails", madera: "lumber", paral: "stud", parales: "studs", montante: "stud", montantes: "studs",
  cinta: "tape", plastico: "plastic", "plástico": "plastic", pintura: "paint", primer: "primer", yeso: "plaster", cemento: "cement", arena: "sand",
  tubo: "pipe", tubos: "pipes", tuberia: "pipe", "tubería": "pipe", cable: "wire", alambre: "wire", caja: "box", cajas: "boxes", enchufe: "outlet", enchufes: "outlets",
  interruptor: "switch", interruptores: "switches", puerta: "door", puertas: "doors", ventana: "window", ventanas: "windows", azulejo: "tile", azulejos: "tile", loseta: "tile",
  losetas: "tile", baldosa: "tile", piso: "flooring", pisos: "flooring", pegamento: "adhesive", silicon: "caulk", "silicón": "caulk", silicona: "caulk", lija: "sandpaper",
  brocha: "brush", rodillo: "roller", guantes: "gloves", bolsas: "bags", bolsa: "bag", triplay: "plywood", contrachapado: "plywood", viga: "beam", vigas: "beams",
  vigueta: "joist", viguetas: "joists", lechada: "grout", mezcla: "mortar", aislante: "insulation", aislamiento: "insulation", moldura: "molding", molduras: "molding",
  bisagra: "hinge", bisagras: "hinges", llave: "faucet", inodoro: "toilet", lavamanos: "sink", "bañera": "tub", banera: "tub", lampara: "fixture", "lámpara": "fixture",
  zocalo: "base", "zócalo": "base", escalera: "ladder", andamio: "scaffold", "protección": "protection", proteccion: "protection", carton: "cardboard", "cartón": "cardboard",
};
const itEsWords = (q) =>
  String(q || "")
    .toLowerCase()
    .split(/\s+/)
    .map((w) => IT_ES[w] || IT_ES[w.normalize("NFD").replace(/[̀-ͯ]/g, "")] || w)
    .join(" ");

// ---- the index the search reads: the library, what was bought, what was sold. Rebuilt when the records change.
let itIdx = null;
function itSig() {
  let n = 0;
  try {
    DB.clients.forEach((c) => [...c.estimates, ...c.changeOrders, ...(c.invoices || [])].forEach((d) => (n += (d.lines || []).length)));
  } catch (e) {}
  return [itemLib().length, itemLib().reduce((a, x) => a + (x.hist || []).length + (!1 === x.active ? 1 : 0), 0), n, (DB.pos || []).length, (DB.pos || []).reduce((a, p) => a + (p.lines || []).length, 0), (DB.bills || []).length, Object.keys(itemLibDeclined()).length].join("|");
}
function itemIndex() {
  const sig = itSig();
  if (itIdx && itIdx.sig === sig) return itIdx;
  const pw = (() => {
      try {
        return "function" == typeof pwData ? pwData().items : {};
      } catch (e) {
        return {};
      }
    })(),
    pwByNorm = {},
    sold = (() => {
      try {
        return "function" == typeof costLibrary ? costLibrary() : [];
      } catch (e) {
        return [];
      }
    })(),
    soldBy = {},
    uses = {},
    rows = [],
    seen = new Set();
  Object.values(pw).forEach((I) => {
    const k = itNorm(I.label);
    k && !pwByNorm[k] && (pwByNorm[k] = I);
  });
  sold.forEach((o) => (soldBy[o.key] = o));
  // how often each name is on a line: estimates, change orders, invoices, POs, bills, requests
  const use = (name) => {
    const k = itNorm(name);
    k && (uses[k] = (uses[k] || 0) + 1);
  };
  try {
    DB.clients.forEach((c) => [...c.estimates, ...c.changeOrders, ...(c.invoices || [])].forEach((d) => (d.lines || []).forEach((l) => use(l.item))));
    (DB.pos || []).forEach((po) => (po.lines || []).forEach((l) => use(l.item)));
    (DB.bills || []).forEach((b) => (b.lines || []).forEach((l) => use(String(l.desc || "").split(" — ")[0])));
    (DB.projects || []).forEach((p) => (p.requests || []).forEach((r) => ("function" == typeof reqItems ? reqItems(r) : []).forEach((x) => use(x.what))));
  } catch (e) {}
  const lastOf = (I) => {
    if (!I || !I.buys || !I.buys.length) return null;
    const b = I.buys[I.buys.length - 1];
    return { price: +b.price || 0, unit: b.normUnit || I.unit || "", vendor: b.vendor || "", date: b.date || "", doc: b.docNo || "", kind: b.kind || "" };
  };
  const byVendorOf = (I) => {
    const o = {};
    (I && I.buys ? I.buys : []).forEach((b) => (o[String(b.vendor || "").toLowerCase()] = { price: +b.price || 0, unit: b.normUnit, vendor: b.vendor, date: b.date, doc: b.docNo }));
    return o;
  };
  itemLib()
    .filter((x) => !1 !== x.active)
    .forEach((it) => {
      const k = itNorm(it.name),
        I = (it.pwKey && pw[it.pwKey]) || pwByNorm[k] || null,
        so = soldBy[k];
      seen.add(k), I && seen.add(itNorm(I.label));
      rows.push({
        key: "lib:" + it.id,
        src: "library",
        lib: it,
        name: it.name,
        es: it.es || "",
        unit: it.unit || (I && I.unit) || "",
        code: it.code || "",
        cat: it.cat || "",
        desc: it.desc || "",
        rate: +it.rate || (so && so.avgPrice) || 0,
        cost: +it.cost || 0,
        costAt: it.costAt || "",
        last: lastOf(I),
        byVendor: byVendorOf(I),
        vendor: it.vendor || (lastOf(I) || {}).vendor || "",
        uses: (uses[k] || 0) + (it.uses || 0),
        kind: it.kind || "",
      });
    });
  // bought but not in the library: still found (with its history), and proposed for the library after use
  Object.values(pw).forEach((I) => {
    const k = itNorm(I.label);
    if (!k || seen.has(k)) return;
    seen.add(k);
    const L = lastOf(I);
    rows.push({ key: "pw:" + I.key, src: "bought", lib: null, name: I.label, es: "", unit: I.unit || "", code: (I.buys.find((b) => b.code) || {}).code || "", cat: "materials", desc: "", rate: 0, cost: L ? L.price : 0, costAt: L ? L.date : "", last: L, byVendor: byVendorOf(I), vendor: L ? L.vendor : "", uses: uses[k] || I.buys.length, kind: "" });
  });
  // sold on an estimate or change order but not in the library
  sold.forEach((o) => {
    if (seen.has(o.key) || !o.n) return;
    seen.add(o.key);
    rows.push({ key: "sold:" + o.key, src: "sold", lib: null, name: o.name, es: "", unit: o.unit || "", code: "", cat: "", desc: ((o.est || []).find((x) => x.desc) || {}).desc || "", rate: o.avgPrice || 0, cost: o.avgCost || 0, costAt: "", last: null, byVendor: {}, vendor: "", uses: uses[o.key] || o.n, kind: "" });
  });
  // asked for by the field (requests): the words the crew uses, found again on the next request
  try {
    (DB.projects || []).forEach((p) =>
      (p.requests || []).forEach((rq) =>
        ("function" == typeof reqItems ? reqItems(rq) : []).forEach((x) => {
          const k = itNorm(x.what);
          if (!k || k.length < 3 || seen.has(k)) return;
          seen.add(k);
          rows.push({ key: "req:" + k, src: "requested", lib: null, name: String(x.what).trim(), es: "", unit: x.unit || "ea", code: "", cat: "materials", desc: "", rate: 0, cost: 0, costAt: "", last: null, byVendor: {}, vendor: "", uses: uses[k] || 1, kind: "" });
        }),
      ),
    );
  } catch (e) {}
  rows.forEach((r) => {
    const cn = "function" == typeof codeName && r.code ? codeName(r.code) : "";
    r.hay = ` ${itNorm(r.name)} ${itNorm(r.es)} ${itNorm(cn)} ${itNorm(r.lib && r.lib.alias)} `;
  });
  return (itIdx = { sig: sig, rows: rows, uses: uses });
}
// recent picks: a convenience on this phone, per person
function itRecent() {
  try {
    return JSON.parse(localStorage.getItem("sd_itemRecent_" + (itMe().id || "")) || "[]") || [];
  } catch (e) {
    return [];
  }
}
function itRecentPush(key) {
  try {
    const L = itRecent().filter((k) => k !== key);
    L.unshift(key), localStorage.setItem("sd_itemRecent_" + (itMe().id || ""), JSON.stringify(L.slice(0, 12)));
  } catch (e) {}
}
// The one search. ctx: {side: "sell"|"buy", vendor, limit}. Words may be typed in any order and cut short ("stud 2x4",
// "porc til"); Spanish trade words find the item they mean. Most used first, the person's recent picks ahead, and on
// the buy side what this vendor sold us before.
function itemFind(q, ctx) {
  ctx = ctx || {};
  const X = itemIndex(),
    raw = itNorm(q),
    words = itNorm(itEsWords(q)).split(" ").filter(Boolean),
    rawWords = raw.split(" ").filter(Boolean),
    rec = itRecent(),
    vkey = String(ctx.vendor || "").toLowerCase(),
    side = ctx.side || "sell",
    out = [];
  X.rows.forEach((r) => {
    let s = 0;
    if (words.length) {
      let all = !0;
      words.forEach((w, i) => {
        const w0 = rawWords[i] || w,
          hit = r.hay.includes(" " + w) || r.hay.includes(" " + w0) || (w.length > 2 && r.hay.includes(w));
        hit ? (s += r.hay.includes(" " + w) || r.hay.includes(" " + w0) ? 10 : 4) : (all = !1);
      });
      if (!all) return;
      r.hay.startsWith(" " + raw) && (s += 12);
      itNorm(r.name) === raw && (s += 30);
    }
    s += Math.min(12, Math.log2(1 + (r.uses || 0)) * 3);
    const ri = rec.indexOf(r.key);
    ri >= 0 && (s += 14 - ri);
    "library" === r.src && (s += 6);
    if ("assembly" === r.kind) {
      if ("sell" !== side) return;
      s += 2;
    }
    if ("buy" === side) {
      r.last && (s += 3);
      vkey && r.byVendor[vkey] && (s += 8);
      ("construction" === r.cat || "design" === r.cat) && "assembly" !== r.kind && (s -= words.length ? 6 : 30);
    } else ("bought" === r.src || "requested" === r.src) && (s -= 4);
    out.push({ r: r, s: s });
  });
  out.sort((a, b) => b.s - a.s || String(a.r.name).localeCompare(String(b.r.name)));
  return out.slice(0, ctx.limit || 6).map((x) => x.r);
}
// What one hit offers a line: the price a sell line starts from, the price a buy line starts from (this vendor's last,
// else the last buy, else the library's unit cost), and where each came from.
function itOffer(h, side, vendor) {
  const vk = String(vendor || "").toLowerCase(),
    vb = vk && h.byVendor && h.byVendor[vk],
    buy = vb ? { price: vb.price, from: `last paid at ${vb.vendor}${vb.date ? ", " + fmt(vb.date) : ""}${vb.doc ? " (" + vb.doc + ")" : ""}` } : h.last && h.last.price ? { price: h.last.price, from: `last paid at ${h.last.vendor}${h.last.date ? ", " + fmt(h.last.date) : ""}${h.last.doc ? " (" + h.last.doc + ")" : ""}` } : h.cost ? { price: h.cost, from: `the library's unit cost${h.costAt ? " of " + fmt(h.costAt) : ""}` } : null;
  return { side: side, buy: buy, sell: h.rate ? { price: h.rate, from: h.lib ? "the item library" : "the average on our estimates" } : null };
}

// ---- the picker -------------------------------------------------------------------------------------------------
// One per typed line. Desktop: under the field. Phone: full width, big rows, the person's recent items first when the
// field is empty, so a line added in a client's kitchen takes seconds.
const ITP_SLOTS = [
  // [selector, slot kind, side]
  ['tr[data-line] input[data-f="item"]', "doc", "sell"],
  ['.ct-row[data-ctl] input[data-ctf="item"]', "ct", "sell"],
  ['input[data-csf="item"]', "csf", "sell"],
  ['#ct-itbl tr[data-cti] input[data-f="name"]', "ctitems", "buy"],
  ['tr[data-bl] input[data-f="desc"]', "bill", "buy"],
  ["#rfq-b-item, #rfq-add-item", "rfq", "buy"],
  ["#cp-text", "req", "buy"],
  ['tr[data-spl] input[data-slf="note"]', "receipt", "buy"],
  ['#mbm input[data-f="item"]', "generic", "buy"],
];
function itSlot(el) {
  if (!el || !el.matches || el.readOnly || el.disabled) return null;
  for (const [sel, kind, side0] of ITP_SLOTS)
    if (el.matches(sel)) {
      let side = side0,
        k = kind;
      if ("doc" === kind) {
        const po = el.closest('[id^="po-"]');
        if (po) (k = "po"), (side = "buy");
        else if (!el.closest('[id^="doc-"]')) k = "generic";
      }
      return { kind: k, side: side };
    }
  return null;
}
let itp = null; // {el, input, slot, hits, sel, q}
function itpVendorOf(input, slot) {
  if ("po" === slot.kind) {
    const root = input.closest('[id^="po-"]'),
      po = root && (DB.pos || []).find((x) => "po-" + x.id === root.id);
    return (po && po.vendor) || "";
  }
  if ("bill" === slot.kind) return (document.getElementById("e-vendor") || {}).value || "";
  if ("receipt" === slot.kind) return ((document.querySelector('#mbm [data-sf="vendor"]') || {}).value || "").trim();
  if ("ctitems" === slot.kind) return ((input.closest("tr") || document).querySelector('[data-f="vendor"]') || {}).value || "";
  return "";
}
// the words to search with: the field's value, or in the request box, the item the caret is on ("40 2x4x8, a box of
// 3": items are split by commas or lines) less its quantity and unit
const IT_QTY_RE = /^\s*(\d+(?:\.\d+)?)\s*(ea|each|pcs?|box(?:es)?|cases?|sf|lf|sheets?|rolls?|gal|bags?|bundles?|pk|packs?|tubes?|cajas?|bolsas?|rollos?|galones?|hojas?)?\b\s*/i;
function itpQuery(input, slot) {
  if ("req" !== slot.kind) return { q: input.value, qty: "", unit: "" };
  const v = input.value,
    at = input.selectionStart == null ? v.length : input.selectionStart,
    a0 = Math.max(v.lastIndexOf("\n", at - 1), v.lastIndexOf(",", at - 1), v.lastIndexOf(";", at - 1)) + 1,
    ends = ["\n", ",", ";"].map((c) => v.indexOf(c, at)).filter((x) => x >= 0),
    b = ends.length ? Math.min(...ends) : v.length,
    a = a0 + (v.slice(a0, b).match(/^\s*/) || [""])[0].length,
    seg = v.slice(a, b),
    m = seg.match(IT_QTY_RE),
    rest = m ? seg.slice(m[0].length) : seg;
  return { q: rest.trim(), qty: m ? m[1] : "", unit: m && m[2] ? m[2] : "", a: a, b: b };
}
function itpHide() {
  itp && itp.el && itp.el.remove(), (itp = null);
}
function itpRowHtml(h, i, slot, field, vendor) {
  const o = itOffer(h, slot.side, vendor),
    cn = h.code && "function" == typeof codeName ? codeName(h.code) : "",
    tag = "assembly" === h.kind ? "Assembly" : "library" === h.src ? "" : "bought" === h.src ? "Bought Before" : "requested" === h.src ? "Asked For Before" : "On Estimates",
    meta = [h.unit ? (field ? h.unit : "per " + h.unit) : "", cn, field ? "" : "buy" === slot.side ? (o.buy ? `${itMoney2(o.buy.price)} ${o.buy.from}` : "") : o.sell ? `${itMoney2(o.sell.price)} sell` : "", "buy" === slot.side && h.vendor && field ? h.vendor : ""].filter(Boolean),
    d1 = String(h.desc || "").split("\n").find((x) => x.trim()) || "";
  return `<button type="button" class="itp-row${i === (itp ? itp.sel : 0) ? " on" : ""}" data-itp="${i}" role="option"><span class="itp-n"><b data-nocase>${esc(h.name)}</b>${tag ? `<span class="itp-tag">${tag}</span>` : ""}</span>${d1 ? `<span class="itp-d" data-nocase>${esc(d1.replace(/^[-•]\s*/, "").slice(0, 110))}</span>` : ""}${meta.length ? `<span class="itp-m" data-nocase>${esc(meta.join(" · "))}</span>` : ""}</button>`;
}
function itpShow(input, force) {
  const slot = itSlot(input);
  if (!slot) return itpHide();
  const Q = itpQuery(input, slot),
    q = String(Q.q || "").trim(),
    phone = ("function" == typeof vw ? vw() : innerWidth) <= 640,
    field = itIsField();
  if (!force && q.length < 2 && !(phone && !q && "req" !== slot.kind)) return itpHide();
  const vendor = itpVendorOf(input, slot),
    hits = itemFind(q, { side: slot.side, vendor: vendor, limit: phone ? 5 : 7 }).filter((h) => !(field && "assembly" === h.kind));
  if (!hits.length || (q && hits.length === 1 && itNorm(hits[0].name) === itNorm(q) && !force)) return itpHide();
  let el = itp && itp.input === input ? itp.el : null;
  el || (itpHide(), (el = document.createElement("div")), (el.className = "itp"), el.setAttribute("role", "listbox"), document.body.appendChild(el));
  itp = { el: el, input: input, slot: slot, hits: hits, sel: 0, q: q, vendor: vendor };
  el.innerHTML = `<div class="itp-h"><span>${q ? "Items" : "Recent and Most Used"}</span></div>${hits.map((h, i) => itpRowHtml(h, i, slot, field, vendor)).join("")}`;
  itpPlace();
  el.querySelectorAll("[data-itp]").forEach((b) => {
    b.addEventListener("pointerdown", (e) => e.preventDefault());
    b.addEventListener("mousedown", (e) => e.preventDefault());
    b.addEventListener("click", (e) => {
      e.preventDefault(), e.stopPropagation();
      const h = itp && itp.hits[+b.dataset.itp];
      h && itemPick(input, slot, h);
    });
  });
}
// under the field, or above it when the keyboard leaves no room below; it follows the field when the page scrolls
function itpPlace() {
  if (!itp || !itp.el) return;
  const el = itp.el,
    r = itp.input.getBoundingClientRect(),
    W = "function" == typeof vw ? vw() : innerWidth,
    H = innerHeight,
    phone = W <= 640;
  phone ? ((el.style.left = "8px"), (el.style.width = W - 16 + "px")) : ((el.style.width = Math.max(320, Math.min(440, r.width + 120)) + "px"), (el.style.left = Math.max(8, Math.min(r.left, W - 448)) + "px"));
  const h = el.offsetHeight || 0,
    below = H - r.bottom - 8,
    up = h > below && r.top - 8 > below;
  el.style.maxHeight = Math.max(160, Math.min(420, (up ? r.top : below) - 12)) + "px";
  el.style.top = (up ? Math.max(8, r.top - Math.min(h, r.top - 12) - 4) : r.bottom + 4) + "px";
}
function itpMove(d) {
  if (!itp) return;
  itp.sel = (itp.sel + d + itp.hits.length) % itp.hits.length;
  itp.el.querySelectorAll("[data-itp]").forEach((b, i) => b.classList.toggle("on", i === itp.sel));
}
// one listener set for every slot; the native datalist comes off the field so the line has one picker
document.addEventListener("input", (e) => {
  const t = e.target;
  itSlot(t) && itpShow(t);
});
document.addEventListener("focusin", (e) => {
  const t = e.target,
    s = itSlot(t);
  if (!s) return;
  t.getAttribute("list") && (t.dataset.itpList = t.getAttribute("list"), t.removeAttribute("list"));
  t.setAttribute("autocomplete", "off");
  setTimeout(() => document.activeElement === t && itpShow(t), 0);
});
document.addEventListener("focusout", (e) => {
  itp && e.target === itp.input && setTimeout(() => itp && document.activeElement !== itp.input && itpHide(), 180);
});
// on window, in capture: ahead of the line editors' own Enter (next row, or a new line), which would commit the typed words first
window.addEventListener(
  "keydown",
  (e) => {
    if (!itp || e.target !== itp.input) return;
    if ("ArrowDown" === e.key) e.preventDefault(), itpMove(1);
    else if ("ArrowUp" === e.key) e.preventDefault(), itpMove(-1);
    else if ("Escape" === e.key) e.preventDefault(), itpHide();
    else if ("Enter" === e.key && !e.shiftKey && itp.hits[itp.sel] && (itp.q || "req" !== itp.slot.kind)) e.preventDefault(), e.stopPropagation(), itemPick(itp.input, itp.slot, itp.hits[itp.sel]);
  },
  !0,
);
window.addEventListener("scroll", () => itp && itp.input && (itp.input.isConnected ? itpPlace() : itpHide()), !0);
// the old history pop and its datalist give way to the one picker
"function" == typeof libShow && (libShow = function () {});

// ---- filling a line -----------------------------------------------------------------------------------------------
const IT_FILL_WORDS = { desc: "description", unit: "unit", rate: "price", price: "price", cost: "budget cost", code: "cost code", vendor: "vendor", spec: "spec" };
function itFillNote(l, h, fields, extra) {
  l.fill = Object.assign({ src: h.src, id: h.lib ? h.lib.id : h.key, name: h.name, by: itMe().name || ("function" == typeof role ? role() : ""), at: "function" == typeof appNowIso ? appNowIso() : "", fields: fields }, extra || {});
}
function itFillWords(fields) {
  const w = [...new Set(fields.map((f) => IT_FILL_WORDS[f] || f))];
  return w.length > 1 ? w.slice(0, -1).join(", ") + " and " + w[w.length - 1] : w[0] || "the name";
}
function itToast(h, fields, from) {
  const src = h.lib ? "the item library" : "bought" === h.src ? "what we bought before" : "our estimates",
    go = h.lib ? [{ label: "Open Item", run: () => itemOpen(h.lib.id) }] : [{ label: "Add to Library", run: () => itemAddFrom(h) }];
  toast(`${h.name}: ${itFillWords(fields)} filled from ${src}${from ? ` (${from})` : ""}. Every field can still be changed.`, go);
}
// a sell line (estimate, change order, invoice): the library's own fill (cost code, unit, rate, budget, description),
// and a description in the house style when the library has none
function itFillSell(l, h, d) {
  const before = { desc: l.desc || "", unit: l.unit || "", rate: +l.rate || 0, cost: +l.cost || 0, code: l.code || "" };
  l.item = h.name;
  if (h.lib && "function" == typeof libFillLine) libFillLine(l, h.lib, d);
  else {
    (!l.unit || "ls" === l.unit) && h.unit && (l.unit = h.unit);
    !+l.rate && h.rate && (l.rate = h.rate);
    !+l.cost && h.cost && (l.cost = r2(h.cost * (+l.qty || 1)));
    "function" == typeof itemAutoCode && itemAutoCode(l, d);
  }
  l.desc || ((l.desc = itemDescribe(h.lib || h)), l.desc && (l.descDrafted = !0));
  const fields = Object.keys(before).filter((k) => String(before[k]) !== String("rate" === k || "cost" === k ? +l[k] || 0 : l[k] || ""));
  return itFillNote(l, h, fields), fields;
}
// a buy line (PO): the vendor-facing description, the unit, the price this vendor charged last (else the last buy,
// else the library's unit cost), the cost code
function itFillBuy(l, h, vendor, priceKey) {
  const pk = priceKey || "price",
    before = { desc: l.desc || "", unit: l.unit || "", [pk]: +l[pk] || 0, code: l.code || "" },
    o = itOffer(h, "buy", vendor);
  l.item = h.name;
  l.desc || (l.desc = itemVendorText(h.lib, h));
  h.unit && (!l.unit || ("ea" === l.unit && h.unit !== "ea")) && (l.unit = h.unit);
  !+l[pk] && o.buy && (l[pk] = o.buy.price);
  !l.code && h.code && (l.code = h.code);
  h.lib && (l.libId = h.lib.id);
  const fields = Object.keys(before).filter((k) => String(before[k]) !== String(k === pk ? +l[k] || 0 : l[k] || ""));
  return itFillNote(l, h, fields, o.buy && fields.includes(pk) ? { priceFrom: o.buy.from } : null), { fields: fields, from: o.buy && fields.includes(pk) ? o.buy.from : "" };
}
// set a form field the way a person would: a value and the events its form listens for
function itSet(el, v) {
  if (!el) return !1;
  el.value = v;
  el.dispatchEvent(new Event("input", { bubbles: !0 })), el.dispatchEvent(new Event("change", { bubbles: !0 }));
  return !0;
}
// fill a row whose form redraws on every change: set one field, find the row again by its id, set the next
function itSetSeq(rowSel, steps) {
  let n = 0;
  steps.forEach(([sel, v, onlyEmpty]) => {
    const row = document.querySelector(rowSel),
      el = row && row.querySelector(sel);
    if (!el || null == v || "" === v) return;
    if (onlyEmpty && String(el.value || "").trim() && !("select-one" === el.type && !el.value)) return;
    itSet(el, v) && n++;
  });
  return n;
}
function itemPick(input, slot, h) {
  itpHide(), itRecentPush(h.key);
  if ("assembly" === h.kind && ["doc", "ct"].includes(slot.kind)) return itemAsmPick(input, slot, h);
  try {
    if ("doc" === slot.kind || "ct" === slot.kind) {
      const c = DB.clients.find((x) => x.id === clientOpen),
        d = c && docOpen && findDoc(c, docOpen.kind, docOpen.id),
        id = "ct" === slot.kind ? input.closest("[data-ctl]").dataset.ctl : input.closest("tr[data-line]").dataset.line,
        l = d && d.lines.find((x) => x.id === id);
      // a progress invoice's lines are the schedule of values: only the name is the item's
      if (!l || "sov" === d.mode) return itSet(input, h.name);
      // the field shows the name first: a commit of the field as the screen redraws writes the item, not the typed letters
      input.value = h.name;
      const f = itFillSell(l, h, d);
      return save(), render(), itToast(h, f);
    }
    if ("po" === slot.kind) {
      const root = input.closest('[id^="po-"]'),
        po = root && (DB.pos || []).find((x) => "po-" + x.id === root.id),
        l = po && po.lines.find((x) => x.id === input.closest("tr[data-line]").dataset.line);
      if (!l) return itSet(input, h.name);
      input.value = h.name;
      const R = itFillBuy(l, h, po.vendor);
      return save(), "function" == typeof rxPOLineSync && rxPOLineSync(po), render(), itToast(h, R.fields, R.from);
    }
    if ("req" === slot.kind) {
      const Q = itpQuery(input, slot),
        v = input.value,
        unit = Q.unit || h.unit || "ea",
        line = `${Q.qty || 1} ${unit} ${h.name}`;
      input.value = v.slice(0, Q.a) + line + v.slice(Q.b);
      const at = Q.a + line.length;
      input.setSelectionRange && input.setSelectionRange(at, at);
      input.dispatchEvent(new Event("input", { bubbles: !0 }));
      itpHide();
      return toast(`${h.name} put on the request${h.unit ? ", counted in " + (Q.unit || h.unit) : ""}`);
    }
    if ("rfq" === slot.kind) {
      itSet(input, h.name), (input.dataset.itpPick = h.key);
      const u = document.getElementById("rfq-b-item" === input.id ? "rfq-b-unit" : "rfq-add-unit");
      u && h.unit && (u.value = h.unit);
      itPending = { name: h.name, h: h };
      return toast(`${h.name}: unit filled from ${h.lib ? "the item library" : "what we bought before"}. Say how many, then Add.`);
    }
    if ("bill" === slot.kind) {
      itSet(input, h.name);
      const code = document.getElementById("e-code");
      code && !code.value && h.code && (code.value = h.code);
      const o = itOffer(h, "buy", itpVendorOf(input, slot));
      return toast(`${h.name}${o.buy ? `: ${itMoney2(o.buy.price)} per ${h.unit || "unit"} ${o.buy.from}` : ""}. Enter the amount the bill shows.`);
    }
    if ("receipt" === slot.kind) {
      const row = input.closest("tr[data-spl]"),
        rs = `#mbm tr[data-spl="${row.dataset.spl}"]`;
      itSetSeq(rs, [
        ['[data-slf="note"]', h.name, !1],
        ['[data-slf="code"]', h.code, !0],
      ]);
      return toast(`${h.name}${h.code ? ` on cost code ${h.code}` : ""}`);
    }
    if ("ctitems" === slot.kind) {
      const i = input.closest("tr[data-cti]").dataset.cti,
        rs = `#ct-itbl tr[data-cti="${i}"]`,
        o = itOffer(h, "buy", itpVendorOf(input, slot));
      itSetSeq(rs, [
        ['[data-f="name"]', h.name, !1],
        ['[data-f="unit"]', h.unit, !0],
        ['[data-f="cost"]', o.buy ? o.buy.price : "", !0],
        ['[data-f="vendor"]', h.vendor, !0],
      ]);
      return itToast(h, ["unit", "price", "vendor"], o.buy ? o.buy.from : "");
    }
    if ("csf" === slot.kind) {
      const sheet = input.closest(".ct-sheet-body") || document,
        o = itOffer(h, "sell");
      itSet(input, h.name);
      const set = (k, v) => {
        const el = sheet.querySelector(`[data-csf="${k}"]`);
        el && v && !String(el.value || "").trim() && itSet(el, v);
      };
      set("unit", h.unit), o.sell && set("rate", o.sell.price), set("desc", itemDescribe(h.lib || h));
      return itToast(h, ["unit", "rate", "desc"]);
    }
    itSet(input, h.name);
    toast(`${h.name} from ${h.lib ? "the item library" : "what we bought before"}`);
  } catch (e) {
    console.warn("item pick", e), itSet(input, h.name);
  }
}
// An RFQ line added after a pick carries the item's spec, cost code and link (the RFQ forms read their fields on Add).
let itPending = null;
document.addEventListener(
  "click",
  (e) => {
    const b = e.target.closest && e.target.closest("#rfq-b-add, #rfq-add-go");
    if (!b || !itPending) return;
    const P = itPending;
    setTimeout(() => {
      try {
        let hit = 0;
        ("function" == typeof rfqInit ? rfqInit() : DB.rfqs || []).forEach((r) =>
          (r.lines || []).forEach((l) => {
            if (l.item !== P.name || l.libId || l.fill) return;
            l.spec || (l.spec = itemVendorText(P.h.lib, P.h));
            l.costCode || (l.costCode = P.h.code || "");
            P.h.lib && (l.libId = P.h.lib.id);
            itFillNote(l, P.h, ["spec", "code"]), hit++;
          }),
        );
        hit && save();
      } catch (err) {
        console.warn("rfq item", err);
      }
      itPending = null;
    }, 30);
  },
  !0,
);
// Where a filled field came from, shown on the field itself after every draw (title, and a dotted underline)
function itDecorate() {
  try {
    const c = "undefined" != typeof clientOpen && DB.clients.find((x) => x.id === clientOpen),
      d = c && "undefined" != typeof docOpen && docOpen && findDoc(c, docOpen.kind, docOpen.id),
      mark = (row, l) => {
        if (!row || !l || !l.fill) return;
        const F = l.fill,
          src = "library" === F.src ? "the item library" : "bought" === F.src ? "what we bought before" : "our estimates",
          t = `Filled from ${src} by ${F.by || "someone"}${F.at ? " on " + fmt(String(F.at).slice(0, 10)) : ""}${F.priceFrom ? "; price: " + F.priceFrom : ""}. Change any field if this job is different.`;
        row.querySelectorAll('[data-f="item"],[data-ctf="item"]').forEach((x) => ((x.title = t), x.classList.add("itp-filled")));
        (F.fields || []).forEach((f) => row.querySelectorAll(`[data-f="${f}"],[data-ctf="${f}"]`).forEach((x) => ((x.title = t), x.classList.add("itp-filled"))));
      };
    d &&
      document.querySelectorAll(`#doc-${d.id} tr[data-line], #doc-${d.id} [data-ctl]`).forEach((row) => {
        const id = row.dataset.line || row.dataset.ctl;
        mark(row, d.lines.find((x) => x.id === id));
      });
    document.querySelectorAll('[id^="po-"]').forEach((root) => {
      const po = (DB.pos || []).find((x) => "po-" + x.id === root.id);
      po && root.querySelectorAll("tr[data-line]").forEach((row) => mark(row, po.lines.find((x) => x.id === row.dataset.line)));
    });
  } catch (e) {}
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    return itp && itp.input && !itp.input.isConnected && itpHide(), itDecorate(), r;
  };
}

// ---- assemblies: one pick, a set of lines, quantities from one measurement (§1.18 item 3)
const IT_ASM = [
  { name: "Bathroom gut and rebuild", measure: "sf", ask: "The bathroom's floor area, in sq ft", parts: [["Demolition & disposal", 1, "ls"], ["Plumbing — rough & finish", 1, "ls"], ["Electrical — rough & finish", 1, "ls"], ["Insulation, drywall, taping & prime", 1, "ls"], ["Tile & waterproofing", 1, "ls"], ["Porcelain tile", 2.6, "sf"], ["Fixtures & appliances — install", 1, "ls"], ["Paint & finishes", 1, "ls"]] },
  { name: "Brownstone parlor floor refinish", measure: "sf", ask: "The floor area to refinish, in sq ft", parts: [["Protection & cleanup", 1, "ls"], ["Floor refinishing — sand & stain", 1, "sf"]] },
  { name: "Rough plumbing per fixture", measure: "ea", ask: "How many fixtures", parts: [["Plumbing — rough & finish", 1, "ea"]] },
];
const IT_GC = ["General conditions & supervision", "Protection & cleanup", "Permits, inspections & fees"];
function itemAsmSeed() {
  // the firm's default assemblies, structure the firm keeps and edits (like libSeed's common items); never records
  if (DB.__itemAsmV || itemLib().length < 10) return;
  const L = itemLib(),
    by = (n) => L.find((x) => itNorm(x.name) === itNorm(n));
  IT_ASM.forEach((A) => {
    if (by(A.name)) return;
    const parts = A.parts.map(([n, per, u]) => ({ itemId: (by(n) || {}).id || "", name: n, per: per, unit: u })).filter((p) => p.itemId);
    parts.length && L.push({ id: uid("li"), name: A.name, kind: "assembly", cat: "construction", code: "01", unit: A.measure, measure: A.measure, ask: A.ask, parts: parts, rate: 0, cost: 0, desc: "", active: !0, src: "default" });
  });
  DB.__itemAsmV = 1;
}
let itAsmDone = !1;
function itemAsmPick(input, slot, h) {
  const A = h.lib,
    c = DB.clients.find((x) => x.id === clientOpen),
    d = c && docOpen && findDoc(c, docOpen.kind, docOpen.id);
  if (!A || !d) return;
  // the field reads the assembly while its sheet is open, so a commit of the field writes its name, not the typed letters
  input.value = A.name;
  mbModal(
    `Add ${esc(A.name)}`,
    `<label class="f"><span>${esc(A.ask || "How many")}</span><input id="itasm-n" type="number" inputmode="decimal" min="0" step="any" placeholder="${esc(A.measure || "")}"></label><p class="small muted">Adds ${A.parts.length} lines from the item library, each with its description, unit, price and cost code. General conditions are added if this ${"co" === d.type ? "change order" : "estimate"} has none, as the Standard requires.</p>`,
    {
      submit: "Add the Lines",
      onSubmit: () => {
        const n = +((document.getElementById("itasm-n") || {}).value || 0);
        if (n > 0) itAsmDone = !0;
        if (!(n > 0)) return toast("Enter the measurement"), !1;
        const row = "ct" === slot.kind ? input.closest("[data-ctl]") : input.closest("tr[data-line]"),
          at = row ? d.lines.findIndex((x) => x.id === (row.dataset.ctl || row.dataset.line)) : -1,
          cur = at >= 0 ? d.lines[at] : null,
          made = [],
          mk = (it, qty, unit) => {
            const l = { id: uid("l"), item: "", desc: "", qty: qty, unit: unit || it.unit || "ls", rate: 0, cost: 0, taxable: !1, vendor: "", code: "", parent: "", items: [] };
            return itFillSell(l, { src: "library", lib: it, name: it.name, unit: it.unit, rate: it.rate, cost: it.cost, code: it.code, key: "lib:" + it.id }, d), (l.fill.asm = A.id), l;
          };
        A.parts.forEach((p) => {
          const it = itemById(p.itemId);
          it && made.push(p.unit === A.measure && p.per ? mk(it, r2(n * p.per), p.unit) : mk(it, 1));
        });
        // general conditions (cost code 01) and permits (14) are added only when no line already carries that code:
        // a second general-conditions line would bill the client twice for the same supervision
        const codes = new Set(d.lines.map((l) => ("function" == typeof lineCode ? lineCode(l, d) : l.code) || l.code).concat(made.map((l) => l.code)));
        IT_GC.forEach((g) => {
          const it = itemLib().find((x) => itNorm(x.name) === itNorm(g));
          it && !codes.has(it.code) && (made.unshift(mk(it, 1)), "14" === it.code && codes.add("14"));
        });
        // the empty line the assembly was typed on becomes its first line; otherwise its lines go under that one
        !cur ? d.lines.push(...made) : String(cur.item || "").trim() && itNorm(cur.item) !== itNorm(A.name) ? d.lines.splice(at + 1, 0, ...made) : d.lines.splice(at, 1, ...made);
        "function" == typeof ctNumber && "construction" === d.template && ctNumber(d);
        save(), render();
        toast(`${made.length} lines added from ${A.name}`, [{ label: "Open Item", run: () => itemOpen(A.id) }]);
      },
    },
  );
  setTimeout(() => document.getElementById("itasm-n")?.focus(), 60);
  // closed without adding: the line goes back to what it held, so the assembly's name is not left on it as a line
  const row0 = "ct" === slot.kind ? input.closest("[data-ctl]") : input.closest("tr[data-line]"),
    l0 = row0 && d.lines.find((x) => x.id === (row0.dataset.ctl || row0.dataset.line)),
    was = l0 ? l0.item || "" : "",
    t0 = setInterval(() => {
      if (document.getElementById("itasm-n")) return;
      clearInterval(t0);
      !itAsmDone && l0 && itNorm(l0.item) === itNorm(A.name) && ((l0.item = was), save(), render());
      itAsmDone = !1;
    }, 250);
}

// ---- learning: proposals from use, purchases and signed estimates; a person approves --------------------------------
function itemProposals() {
  const X = itemIndex(),
    dec = itemLibDeclined(),
    out = [],
    names = {};
  // new: a name on two or more lines (sold or bought) that the library does not hold
  const note = (name, src) => {
    const k = itNorm(name);
    if (!k || k.length < 3) return;
    const o = (names[k] = names[k] || { name: String(name).trim(), n: 0, docs: new Set(), src: new Set() });
    o.n++, src.doc && o.docs.add(src.doc), o.src.add(src.kind);
  };
  try {
    DB.clients.forEach((c) => [...c.estimates, ...c.changeOrders].forEach((d) => ["rejected", "expired", "void"].includes(d.status) || (d.lines || []).forEach((l) => l.item && note(l.item, { kind: "sold", doc: d.number }))));
    (DB.pos || []).forEach((po) => "cancelled" !== po.status && (po.lines || []).forEach((l) => l.item && note(l.item, { kind: "bought", doc: po.number })));
    (DB.projects || []).forEach((p) => (p.requests || []).forEach((rq) => ("function" == typeof reqItems ? reqItems(rq) : []).forEach((x) => x.what && note(x.what, { kind: "requested", doc: `${"function" == typeof shortName ? shortName(p) : ""} request` }))));
  } catch (e) {}
  Object.entries(names).forEach(([k, o]) => {
    if (o.n < 2 || ("function" == typeof libFind && libFind(o.name)) || dec["new:" + k]) return;
    const h = X.rows.find((r) => itNorm(r.name) === k) || {},
      code = (("function" == typeof itemCodeLookup && itemCodeLookup(o.name, {})) || {}).code || h.code || "";
    out.push({ id: "new:" + k, kind: "new", name: o.name, n: o.n, docs: [...o.docs].slice(0, 4), unit: h.unit || "", code: code, rate: h.rate || 0, cost: (h.last && h.last.price) || h.cost || 0, vendor: h.vendor || "", desc: h.desc || "", what: `Add ${o.name} to the library`, why: `Typed on ${o.n} lines (${[...o.docs].slice(0, 3).join(", ")}). In the library it fills itself in next time.` });
  });
  // price: the last buy moved the unit cost more than 10% since the library's figure was set
  X.rows
    .filter((r) => r.lib && r.last && r.last.price > 0)
    .forEach((r) => {
      const it = r.lib,
        cur = +it.cost || 0,
        nu = r2(r.last.price),
        id = `price:${it.id}:${nu}`;
      if (dec[id] || (cur && Math.abs(nu - cur) / cur <= 0.1) || (it.costAt && r.last.date && r.last.date <= it.costAt)) return;
      out.push({ id: id, kind: "price", itemId: it.id, name: it.name, from: cur, to: nu, unit: r.last.unit || it.unit, vendor: r.last.vendor, date: r.last.date, doc: r.last.doc, what: `Unit cost of ${it.name}: ${cur ? itMoney2(cur) + " to " : ""}${itMoney2(nu)} per ${r.last.unit || it.unit || "unit"}`, why: `Last bought at ${r.last.vendor} on ${fmt(r.last.date)}${r.last.doc ? " (" + r.last.doc + ")" : ""}. Estimates priced from an old cost lose money on every line.` });
    });
  // description: a signed estimate wrote one the library lacks
  try {
    DB.clients.forEach((c) =>
      c.estimates
        .filter((d) => ["approved", "converted", "billed"].includes(d.status))
        .forEach((d) =>
          (d.lines || []).forEach((l) => {
            const it = l.libId ? itemById(l.libId) : "function" == typeof libFind ? libFind(l.item) : null,
              txt = itemStyle(String(l.desc || "").split("\n").slice(0, 6).join("\n"));
            if (!it || (it.desc || "").trim() || !txt || txt.length < 20) return;
            const id = "desc:" + it.id;
            dec[id] || out.some((x) => x.id === id) || out.push({ id: id, kind: "desc", itemId: it.id, name: it.name, text: txt, doc: d.number, what: `Description for ${it.name}`, why: `Signed by the client on ${d.number}; written in the house style. The next estimate starts from it.` });
          }),
        ),
    );
  } catch (e) {}
  return out;
}
function itemHist(it, what, why) {
  (it.hist = it.hist || []).push({ at: appNowIso(), by: itMe().name || role(), what: what, why: why || "" });
}
function itemPropApprove(id) {
  if (!itCanApprove()) return toast("The owner or the estimator approves changes to the library"), !1;
  const P = itemProposals().find((x) => x.id === id);
  if (!P) return toast("That proposal is no longer open"), !1;
  let it = null;
  if ("new" === P.kind) {
    it = { id: uid("li"), name: P.name, cat: (("function" == typeof itemCodeLookup && itemCodeLookup(P.name, {})) || {}).cat || "construction", code: P.code || "99", unit: P.unit || "ea", rate: P.rate || 0, cost: P.cost || 0, costAt: P.cost ? today() : "", desc: P.desc ? itemStyle(P.desc) : "", vendor: P.vendor || "", active: !0, src: "learned" };
    it.desc || (it.desc = itemDescribe(it));
    itemLib().push(it), itemHist(it, "added from use", P.why);
  } else if ("price" === P.kind) {
    it = itemById(P.itemId);
    if (!it) return !1;
    itemHist(it, `unit cost ${itMoney2(P.from)} to ${itMoney2(P.to)}`, P.why), (it.cost = P.to), (it.costAt = P.date || today()), (it.costSrc = `${P.vendor}${P.doc ? " " + P.doc : ""}`);
  } else if ("desc" === P.kind) {
    it = itemById(P.itemId);
    if (!it) return !1;
    itemHist(it, "description from a signed estimate", P.why), (it.desc = P.text);
  }
  "function" == typeof audit && audit("company", "itemlib", "item-proposal-approved", "", P.what, P.why);
  save(), render();
  toast(`Approved: ${P.what}. Lines already sent keep their own words.`, it ? [{ label: "Open Item", run: () => itemOpen(it.id) }] : null);
  return !0;
}
function itemPropDecline(id, why) {
  if (!itCanApprove()) return toast("The owner or the estimator decides on the library"), !1;
  const P = itemProposals().find((x) => x.id === id);
  if (!P) return !1;
  itemLibDeclined()[id] = { at: appNowIso(), by: itMe().name || role(), why: why || "", what: P.what };
  "function" == typeof audit && audit("company", "itemlib", "item-proposal-declined", "", P.what, why || "");
  save(), render(), toast(`Declined: ${P.what}. It will not be proposed again.`, [{ label: "Open", run: () => libOpenCard() }]);
  return !0;
}

// ---- the library's own screen: the Settings card, now the Item Library with what it learned ----------------------
// The library lives in Company Settings (Settings › Company Settings), and opens as a sheet from any estimate.
function libOpenCard() {
  "undefined" != typeof settingsMode && (settingsMode = "company");
  "function" == typeof setView ? setView("proj") : ((view = "proj"), render());
  setTimeout(() => document.getElementById("lib-card")?.scrollIntoView({ block: "start" }), 80);
}
"function" == typeof libModal &&
  (libModal = function () {
    mbModal("Item Library", libTableHtml(), { submit: null });
    const box = document.querySelector("#mbm .mbm-box");
    box && (box.style.maxWidth = "1040px"), wireLib(document.getElementById("mbm"));
  });
{
  const base = ctLinesHtml;
  ctLinesHtml = function () {
    return String(base.apply(this, arguments) || "").replace(">Line item library</a>", ">Item Library</a>");
  };
}
function itemOpen(id) {
  const it = itemById(id);
  if (!it) return libOpenCard();
  ["owner", "pm", "coord"].includes(role()) ? libItemDialog(it, null, () => render()) : libOpenCard();
}
function itemAddFrom(h) {
  libItemDialog(null, { name: h.name, unit: h.unit || "ea", rate: h.rate || 0, cost: (h.last && h.last.price) || h.cost || 0, cat: h.cat || "materials", code: h.code || "", desc: h.desc || "" }, () => render());
}
{
  const baseTable = libTableHtml;
  libTableHtml = function () {
    const P = itemProposals(),
      can = itCanApprove(),
      X = itemIndex(),
      byId = {};
    X.rows.forEach((r) => r.lib && (byId[r.lib.id] = r));
    const L = itemLib()
        .slice()
        .sort((a, b) => ("undefined" != typeof CAT_ORDER ? CAT_ORDER.indexOf(a.cat) - CAT_ORDER.indexOf(b.cat) : 0) || String(a.code || "").localeCompare(String(b.code || "")) || a.name.localeCompare(b.name)),
      props = P.length
        ? `<div class="itl-props" data-itprops="${P.length}"><h4>Proposed from Use <span class="pill info">${P.length}</span></h4><p class="small muted">Learned from what the firm typed, bought and signed. ${can ? "Approve to change the library; documents already sent keep their own words." : "The owner or the estimator approves."}</p>${P.map((x) => `<div class="itl-prop" data-itprop="${esc(x.id)}"><div class="grow"><b data-nocase>${esc(x.what)}</b><span class="small muted" data-nocase>${esc(x.why)}</span>${"desc" === x.kind ? `<div class="small itl-desc" data-nocase>${esc(x.text)}</div>` : ""}</div>${can ? `<button type="button" class="btn sm" data-itpok="${esc(x.id)}">Approve</button><button type="button" class="btn sm ghost" data-itpno="${esc(x.id)}">Decline</button>` : ""}</div>`).join("")}</div>`
        : "";
    return `${props}<div class="row" style="margin-bottom:8px"><input id="lib-q" class="btn" style="flex:1;height:36px;text-align:left" placeholder="Search items" aria-label="Search items"><button class="btn sm" id="lib-add">New Item</button></div><div class="tw" style="max-height:60vh;overflow:auto"><table class="t" id="lib-table"><thead><tr><th>Item</th><th>Cost Code</th><th>Unit</th><th class="money">Price</th><th class="money">Unit Cost</th><th>Last Bought</th><th class="money">Used</th><th></th></tr></thead><tbody>${L.map((x) => {
      const r = byId[x.id] || {},
        last = r.last;
      return `<tr data-lib="${x.id}" class="${!1 === x.active ? "muted" : ""}"><td><b data-nocase>${esc(x.name)}</b>${"assembly" === x.kind ? ' <span class="pill neutral">assembly</span>' : ""}${x.desc ? `<div class="small muted" data-nocase style="white-space:pre-line">${esc(x.desc.split("\n")[0])}</div>` : ""}</td><td data-nocase>${esc(x.code || "")} ${esc("function" == typeof codeName ? codeName(x.code) : "")}</td><td>${esc(x.unit || "")}</td><td class="money">${x.rate ? money(x.rate) : "—"}</td><td class="money">${x.cost ? itMoney2(x.cost) : "—"}${x.costAt ? `<div class="small muted">${fmt(x.costAt)}</div>` : ""}</td><td class="small" data-nocase>${last ? `${itMoney2(last.price)} · ${esc(last.vendor)} · ${fmt(last.date)}` : "—"}</td><td class="money">${r.uses || 0}</td><td><a href="#" data-libedit="${x.id}" class="small">Edit</a> · <a href="#" data-libtoggle="${x.id}" class="small">${!1 === x.active ? "Restore" : "Retire"}</a></td></tr>`;
    }).join("")}</tbody></table></div><div class="small muted" style="margin-top:6px">Every line in the firm picks from here: estimates, change orders, invoices, purchase orders, requests for quote, bills, field requests and receipts. Prices come from what we bought, dated; a change waits for the owner or the estimator.</div>`;
  };
  const baseWire = wireLib;
  wireLib = function (root) {
    baseWire.apply(this, arguments);
    const R = root || document;
    R.querySelectorAll("[data-itpok]").forEach((b) => (b.onclick = () => itemPropApprove(b.dataset.itpok)));
    R.querySelectorAll("[data-itpno]").forEach(
      (b) =>
        (b.onclick = () => {
          const why = "function" == typeof appPrompt ? null : prompt("Why not? (kept with the decision)", "");
          itemPropDecline(b.dataset.itpno, why || "");
        }),
    );
  };
}
{
  const base = renderProj;
  renderProj = function () {
    const r = base.apply(this, arguments),
      card = document.getElementById("lib-card");
    if (card) {
      const h = card.querySelector("h3"),
        p = card.querySelector("p");
      h && (h.textContent = "Item Library");
      p && p.classList.contains("small") && !p.closest(".itl-props") && (p.textContent = "Every item the firm sells or buys: its words for the client, its words for the vendor, cost code, unit, price and what we paid last. Lines everywhere fill themselves in from here.");
    }
    return r;
  };
}
// The item form: what an item holds (§1.18 item 1). The old form's fields stay; the rest are added under them.
{
  const base = libItemDialog;
  libItemDialog = function (it, seed, done) {
    base.apply(this, arguments);
    const m = document.getElementById("mbm");
    if (!m) return;
    const cur = it || Object.assign({}, seed || {}),
      desc = m.querySelector("#li-desc");
    desc && desc.closest("label") && (desc.closest("label").querySelector("span").textContent = "Description the client reads — what is included and what is not");
    const box = document.createElement("div");
    box.className = "itl-more";
    box.innerHTML = `<div class="row" style="gap:8px;margin:-4px 0 10px"><button type="button" class="btn sm" id="li-tidy">Write in the House Style</button><span class="small muted">Plain words, what is included and what is not.</span></div><label class="f"><span>Description the vendor reads on a PO or request for quote</span><textarea id="li-vdesc" style="min-height:52px">${esc(cur.vendorDesc || "")}</textarea></label><div class="f2"><label class="f"><span>Preferred vendor</span><input id="li-vendor" value="${esc(cur.vendor || "")}" list="ct-vendors"></label><label class="f"><span>Lead time (working days)</span><input id="li-lead" type="number" min="0" value="${cur.leadDays || ""}"></label></div><div class="f2" style="grid-template-columns:1fr 1fr 1fr"><label class="f"><span>Markup %</span><input id="li-markup" type="number" step="any" value="${cur.markup ?? ""}"></label><label class="f"><span>Material share %</span><input id="li-mat" type="number" min="0" max="100" value="${cur.matPct ?? ""}"></label><label class="f chk" style="align-self:end"><input type="checkbox" id="li-tax" ${cur.taxable ? "checked" : ""}> Taxable</label></div><div class="f2"><label class="f"><span>Name in Spanish, for the field</span><input id="li-es" value="${esc(cur.es || "")}"></label><label class="f"><span>Internal note</span><input id="li-note" value="${esc(cur.note || "")}"></label></div>${(cur.hist || []).length ? `<div class="small muted">History: ${cur.hist.slice(-4).map((x) => `${esc(x.what)} (${esc(x.by)}, ${fmt(String(x.at).slice(0, 10))})`).join("; ")}</div>` : ""}`;
    const anchor = desc ? desc.closest("label") : null;
    anchor ? anchor.after(box) : m.querySelector(".mbm-bd, .mbm-box")?.appendChild(box);
    m.querySelector("#li-tidy").onclick = () => {
      const d = m.querySelector("#li-desc");
      d.value = d.value.trim() ? itemStyle(d.value) : itemDescribe({ name: m.querySelector("#li-name").value, code: m.querySelector("#li-code").value });
    };
    const ok = m.querySelector("#mbm-ok"),
      costBefore = it ? +it.cost || 0 : 0;
    ok &&
      ok.addEventListener(
        "click",
        () => {
          // read now; written once the form's own save has run and closed the sheet (a refused save keeps it open)
          const v = (sel) => (m.querySelector(sel) || {}).value || "",
            name = v("#li-name").trim(),
            vals = { vendorDesc: v("#li-vdesc").trim(), vendor: v("#li-vendor").trim(), leadDays: +v("#li-lead") || 0, markup: "" === v("#li-markup") ? null : +v("#li-markup"), matPct: "" === v("#li-mat") ? null : +v("#li-mat"), taxable: !!(m.querySelector("#li-tax") || {}).checked, es: v("#li-es").trim(), note: v("#li-note").trim() };
          setTimeout(() => {
            if (document.getElementById("li-name") || !name) return;
            const target = it || itemLib().filter((x) => itNorm(x.name) === itNorm(name)).pop();
            if (!target) return;
            Object.assign(target, vals);
            (+target.cost || 0) !== costBefore && ((target.costAt = today()), (target.costSrc = "set by hand"));
            itemHist(target, it ? "edited" : "added", "");
            save();
            toast(`${target.name} saved in the item library`, [{ label: "Open Item", run: () => itemOpen(target.id) }]);
          }, 0);
        },
        !0,
      );
  };
}

// ---- queryable: Ask, ⌘K and the Report Builder read the library and its proposals
"object" == typeof EQ_TABLES &&
  ((EQ_TABLES.items = () =>
    itemIndex().rows.map((r) => ({
      _id: r.key,
      _module: "Purchasing",
      _label: r.name,
      _go: { view: "proj" },
      name: r.name,
      source: r.src,
      kind: r.kind || "item",
      unit: r.unit,
      costCode: r.code,
      costCodeName: r.code && "function" == typeof codeName ? codeName(r.code) : "",
      description: r.desc,
      vendorDescription: (r.lib && r.lib.vendorDesc) || "",
      price: r.rate || 0,
      unitCost: r.cost || 0,
      unitCostDate: r.costAt || "",
      unitPrice: r.last ? r.last.price : null, // the last price paid, per unit (a field role never reads it)
      lastVendor: r.last ? r.last.vendor : "",
      lastBought: r.last ? r.last.date : "",
      preferredVendor: (r.lib && r.lib.vendor) || "",
      leadDays: (r.lib && r.lib.leadDays) || null,
      spanish: r.es || "",
      used: r.uses || 0,
    }))),
  (EQ_TABLES.itemproposals = () => itemProposals().map((p) => ({ _id: p.id, _module: "Purchasing", _label: p.what, _go: { view: "proj" }, kind: p.kind, item: p.name, what: p.what, why: p.why }))));

// boot: the library's default assemblies, once the library itself is there (finishBoot calls libSeed)
{
  const base = "function" == typeof libSeed ? libSeed : null;
  base &&
    (libSeed = function () {
      const r = base.apply(this, arguments);
      try {
        itemAsmSeed();
      } catch (e) {}
      return r;
    });
}

// ---- the look (kept with the feature, so the lane is one file)
(function () {
  const css = `
.itp{position:fixed;z-index:10000;background:var(--paper);border:1px solid var(--rule);border-radius:10px;box-shadow:0 12px 32px rgba(16,24,40,.16);padding:4px;max-height:min(60vh,420px);overflow:auto}
.itp-h{display:flex;justify-content:space-between;font-size:11px;color:var(--ink-3);padding:6px 10px 4px;font-weight:600}
.itp-row{display:flex;flex-direction:column;gap:2px;width:100%;text-align:left;background:none;border:0;border-radius:8px;padding:8px 10px;min-height:44px;cursor:pointer}
.itp-row:hover,.itp-row.on{background:var(--accent-2)}
.itp-n{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}.itp-n b{font-size:13px}
.itp-tag{font-size:10.5px;color:var(--ink-3);border:1px solid var(--rule);border-radius:9px;padding:0 6px}
.itp-d{font-size:12px;color:var(--ink-2);line-height:1.35}.itp-m{font-size:11.5px;color:var(--ink-3)}
input.itp-filled,textarea.itp-filled{text-decoration:underline dotted var(--accent);text-underline-offset:3px}
.itl-props{border:1px solid var(--accent-2);background:var(--paper-2);border-radius:8px;padding:10px 12px;margin:0 0 12px}
.itl-props h4{display:flex;gap:8px;align-items:center;margin:0 0 4px}
.itl-prop{display:flex;gap:8px;align-items:flex-start;padding:8px 0;border-top:1px solid var(--rule-2);flex-wrap:wrap}
.itl-prop .grow{display:flex;flex-direction:column;gap:2px;min-width:200px}
.itl-desc{white-space:pre-line;color:var(--ink-2);margin-top:4px}
@media (max-width:640px){.itp-row{min-height:52px;padding:10px 12px}.itp-n b{font-size:14px}.itl-prop .btn{min-height:44px}}
`;
  const s = document.createElement("style");
  (s.id = "items-css"), (s.textContent = css), document.head.appendChild(s);
})();
