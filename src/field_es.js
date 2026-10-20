// =====================================================================================================================
// The field in Spanish (BACKLOG §1.20; lane "items and Spanish", 2026-10-20). Alan, 2026-10-11: "We do need Spanish
// for the field."
//
// Design gate (§1.16). No new store, list or menu item. The person's language is a field on the person (u.lang, the
// one the messages code already reads: msgTextFor reads m.tr[lang]). The foreman, crew and driver read their screens
// in Spanish when their setting says so; office screens and clients stay in English (a client sees Spanish only if
// their own setting asks for it, which the portal does not offer yet).
//  - How: every screen is drawn in English by the code that owns it, then read once more for a Spanish reader by one
//    pass (esPass) that swaps the words of labels, buttons, headings, sheets and toasts for the field's Spanish from
//    ES (below). Records keep their own words: names, notes, task names, what someone wrote, the messages of a thread
//    (marked data-nocase, data-verbatim, or a thread's message text) are never touched. A translation a person asks
//    for (Traducir) is a separate, labelled line.
//  - The words are plain NYC construction Spanish, the way the crew says them; English trade terms stay where that
//    is what the crew says ("sheetrock", "PO", "permit" is "permiso"). Labels keep the house rule in Spanish:
//    Title Case on labels with the connecting words lowercase (de, del, la, el, y, a, en, con, para, por), sentences
//    in sentence case. Jeanette reviews the wording before go-live (Alan, 2026-10-11).
//  - Dates and times read in the person's locale (es-US) and never ambiguously: "9/11" on a Spanish screen reads
//    "11 sept", "Thu, Sep 3" reads "jue 3 sept", "7:30 AM" reads "7:30 a. m.". Money and counts read as in the US.
//  - Voice input listens in Spanish (es-US); the assistant answers in Spanish; the field's parts of the Standard read
//    in Spanish (docs/STANDARD_ES.md, ridden into the page; Alan's English stays the source, and the page says so
//    when the English has changed since the translation).
//  - Chat lines are translated for the reader when they ask (Traducir / Translate), through the platform's door
//    (MSG_TRANSLATE when the platform fills it, else the AI door through mindPost on the small tier). The translation
//    is kept on the line (m.tr[lang]) so the next reader does not pay for it again, and it is always labelled.
// =====================================================================================================================
const ES_FIELD = ["foreman", "crew", "driver"],
  ES_LOCALE = "es-US";
function esUser() {
  try {
    return ("function" == typeof currentUser && currentUser()) || null;
  } catch (e) {
    return null;
  }
}
// the screens are Spanish for a field person whose setting says Spanish, signed in as themselves
function esOn() {
  const u = esUser();
  return !!u && "es" === u.lang && ES_FIELD.includes(u.role) && ES_FIELD.includes("function" == typeof role ? role() : u.role);
}
const esLangOf = (u) => ((u && u.lang) || "en");

// ---- dates and times in the person's locale ------------------------------------------------------------------------
const ES_MON = { jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11 },
  ES_MON_S = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"],
  ES_MON_L = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
  ES_DOW = { sun: "dom", mon: "lun", tue: "mar", wed: "mié", thu: "jue", fri: "vie", sat: "sáb" },
  ES_DOW_L = { sunday: "domingo", monday: "lunes", tuesday: "martes", wednesday: "miércoles", thursday: "jueves", friday: "viernes", saturday: "sábado" },
  ES_D_WORD = "(?:(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat)(?:day|sday|nesday|urday|rsday)?,?\\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\\.?\\s+\\d{1,2}(?:,?\\s+\\d{4})?",
  ES_D_NUM = "(?:1[0-2]|0?[1-9])\\/(?:3[01]|[12]\\d|0?[1-9])(?:\\/(?:\\d{4}|\\d{2}))?",
  ES_D_ANY = `(?:${ES_D_WORD}|${ES_D_NUM})`,
  ES_TIME = "\\d{1,2}(?::\\d{2})?\\s?(?:AM|PM|am|pm|a\\.m\\.|p\\.m\\.)";
function esDate(s) {
  const t = String(s).trim();
  let m = t.match(/^(?:(Sun|Mon|Tue|Wed|Thu|Fri|Sat)[a-z]*,?\s+)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})(?:,?\s+(\d{4}))?$/);
  if (m) {
    const mo = ES_MON[m[2].toLowerCase()],
      dw = m[1] ? ES_DOW[m[1].toLowerCase()] + " " : "";
    return `${dw}${+m[3]} ${ES_MON_S[mo]}${m[4] ? " " + m[4] : ""}`;
  }
  m = t.match(/^(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?$/);
  if (m && +m[1] >= 1 && +m[1] <= 12 && +m[2] >= 1 && +m[2] <= 31) return `${+m[2]} ${ES_MON_S[+m[1] - 1]}${m[3] ? " " + (m[3].length === 2 ? "20" + m[3] : m[3]) : ""}`;
  m = t.match(/^(\d{1,2})(?::(\d{2}))?\s?(AM|PM|am|pm|a\.m\.|p\.m\.)$/);
  if (m) return `${+m[1]}${m[2] ? ":" + m[2] : ""} ${/^p/i.test(m[3]) ? "p. m." : "a. m."}`;
  m = t.match(/^(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)$/i);
  if (m) return ES_DOW_L[m[1].toLowerCase()];
  m = t.match(/^(January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+(\d{4}))?$/i);
  if (m) return ES_MON_L[ES_MON[m[1].slice(0, 3).toLowerCase()]] + (m[2] ? " " + m[2] : "");
  return null;
}
// dates and times inside a sentence that is otherwise translated
function esDatesIn(s) {
  return String(s)
    .replace(new RegExp(ES_D_WORD, "g"), (x) => esDate(x) || x)
    .replace(new RegExp(ES_TIME, "g"), (x) => esDate(x) || x);
}

// ---- the dictionary: exact strings, then templates ----------------------------------------------------------------
// Template keys hold placeholders: {n} a number, {d} a date or time, {x} words kept as written (a name, a record),
// {t} words translated in their turn. The same placeholder is written in the Spanish where it goes.
// ES is filled by the dictionary section below this one; it can also be extended (esAdd) by a later section.
const ES = Object.create(null),
  ES_LC = Object.create(null),
  ES_TPL = [];
function esAdd(map) {
  Object.entries(map).forEach(([k, v]) => {
    if (/\{[ndxt]\}/.test(k)) {
      const names = [],
        src = k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/\\\{([ndxt])\\\}/g, (a, p) => {
          names.push(p);
          return p === "n" ? "([\\d,.]+%?)" : p === "d" ? `(${ES_D_ANY}|${ES_TIME})` : "(.+?)";
        });
      ES_TPL.push({ re: new RegExp("^" + src + "$", "i"), names: names, out: v, lit: k.replace(/\{[ndxt]\}/g, "").length });
    } else (ES[k] = v), (ES_LC[k.toLowerCase()] = v);
  });
  ES_TPL.sort((a, b) => b.lit - a.lit);
}
const ES_SEP = /(\s+[·•|›]\s+|\s+[—–]\s+)/;
const esCap = (src, out) => (/^[A-Z]/.test(src) && /^[a-záéíóúñ¿¡]/.test(out) ? out.charAt(0).toUpperCase() + out.slice(1) : out);
let esDepth = 0;
// One string in, its Spanish out (or the same string when it is not the app's words: a name, a record, a note).
function esT(s0) {
  const s = String(s0 == null ? "" : s0);
  // a date on its own ("9/3") reads in the person's locale too
  if (!/[A-Za-z]/.test(s)) return /^\s*\d{1,2}\/\d{1,2}(?:\/\d{2,4})?\s*$/.test(s) ? esDate(s) || s : s;
  const t = s.replace(/\s+/g, " ").trim();
  if (!t) return s;
  if (t in ES) return ES[t];
  const lc = t.toLowerCase();
  if (lc in ES_LC) return esCap(t, ES_LC[lc]);
  const dt = esDate(t);
  if (dt) return esCap(t, dt);
  if (esDepth > 6) return s;
  esDepth++;
  try {
    for (const T of ES_TPL) {
      const m = t.match(T.re);
      if (!m) continue;
      // a name or a record is short: a long run of words there is someone's sentence, not the app's ("Labor Day
      // leaves Tue–Wed to finish before plumbing starts 9/10." is a note; it is not "{x} starts {d}")
      if (T.names.some((nm, j) => "x" === nm && String(m[j + 1]).split(/\s+/).length > 7)) continue;
      let i = 0,
        out = T.out;
      const vals = T.names.map((nm) => {
        const v = m[++i];
        // a name stays as written, unless it is one of the app's own words ("Crew · ends 9/11")
        if (nm === "d") return esDate(v) || v;
        if (nm === "t") return esT(v);
        const dv = esDate(v);
        return v in ES ? ES[v] : v.toLowerCase() in ES_LC ? esCap(v, ES_LC[v.toLowerCase()]) : dv ? esCap(v, dv) : v.replace(/&amp;/g, "&");
      });
      // each placeholder in the Spanish takes the next value of its kind, in order
      const used = { n: 0, d: 0, x: 0, t: 0 };
      out = out.replace(/\{([ndxt])\}/g, (a, nm) => {
        let k = -1,
          c = 0;
        for (let j = 0; j < T.names.length; j++) if (T.names[j] === nm && c++ === used[nm]) (k = j), j = T.names.length;
        used[nm]++;
        return k >= 0 ? vals[k] : a;
      });
      // a time that ends a sentence ends it once: "hasta las 5:35 p. m." not "p. m.."
      return out.replace(/([ap]\. m\.)\.(?=\s|$)/g, "$1");
    }
    // a sentence of parts: "Crew · ends 9/11", "Tomorrow — Fri, Sep 4"
    for (const SEP of [ES_SEP, /(;\s+)/, /(,\s+)/]) {
      if (!SEP.test(t)) continue;
      const parts = t.split(SEP),
        outp = parts.map((p, i) => (i % 2 ? p : esT(p)));
      if (outp.some((p, i) => p !== parts[i])) return outp.join("");
    }
    // a label with its punctuation: "Notes:", "(optional)", "Photos…", "Due 9/3."
    const pm = t.match(/^([(“"'¿]*)(.*?)([)”"'.:;,…?!]*)$/);
    // a short label with its punctuation; a long sentence with a full stop is someone's words, left as written
    if (pm && (pm[1] || pm[3]) && pm[2] && (pm[1] || pm[2].split(/\s+/).length <= 6 || !/\.$/.test(pm[3]))) {
      const inner = esT(pm[2]);
      if (inner !== pm[2]) return pm[1] + inner + pm[3];
    }
  } finally {
    esDepth--;
  }
  return s;
}

// ---- the pass over the screen --------------------------------------------------------------------------------------
// What is never translated: a record's own words. The code that draws them marks them (data-nocase, data-verbatim);
// a thread's message text, a quoted reply, what a person is typing, and the assistant's own answer (it answers in
// Spanish itself) are left as written.
const ES_SKIP = "[data-nocase],[data-verbatim],[data-es-skip],.cm:not(.sys) .msg-tx,.msg-quote,.pa-answer,.pa-md2,script,style,textarea,[contenteditable],#sd-standard-md,#sd-standard-es-md,.itp-d,.itp-n b,code,pre",
  // marked as a record's words but holding the app's own around the names ("Team Only · Crew: Angel, Alberto"): the
  // names are not in the dictionary, so only the app's words change
  ES_FORCE = ".msg-sub, #fnd-made .fnd-row .small, #fnd-made .fnd-row b";
const ES_ATTRS = ["placeholder", "title", "aria-label"];
// one English word, two meanings: "Clear" is the weather on the daily log and a verb on a button that empties a list
const ES_CTX = [["#fnd-made [data-fndclear], [data-tlclear], [data-clear]", { Clear: "Limpiar" }]];
const esOrig = new WeakMap(), // node -> English it held, to put back when the person switches to English
  esDone = new WeakMap(); // node -> the Spanish we wrote, so a node is read once per change
function esSkip(el) {
  const k = el && el.closest && el.closest(ES_SKIP);
  return !!k && !k.matches(ES_FORCE);
}
// The house rule for labels, in Spanish: a label (what the app's own Title Case pass treats as one: buttons, tabs,
// headings, chips) reads in Title Case with the connecting words lowercase; a sentence stays a sentence.
const ES_SMALL = new Set("de del la las el los y e o u a al en con por para sin un una que se su sus tu tus lo le mi ni".split(" "));
function esIsLabel(el) {
  try {
    return !!el && el.matches("undefined" != typeof TC_SEL ? TC_SEL : "button,h1,h2,h3,h4,[role=tab],.chip") && !el.closest(".small,.muted,.lead,.hint,.note,p");
  } catch (e) {
    return !1;
  }
}
function esTitle(s) {
  const w = String(s).split(/(\s+)/);
  if (w.filter((x) => x.trim()).length > 6 || /[.?!]\s*\S/.test(s)) return s;
  let first = !0;
  return w
    .map((x) => {
      if (!x.trim()) return x;
      const lw = x.toLowerCase(),
        f = first;
      first = !1;
      // numbers, codes, and the parts of a date or time ("3 sept", "4:30 p. m.") keep their case
      if (/[\d@#$%/]/.test(x) || /^[A-Z]{2,}/.test(x) || !/^[a-záéíóúñü¿¡(]/i.test(x) || /^(?:ene|feb|mar|abr|may|jun|jul|ago|sept|oct|nov|dic|lun|mié|jue|vie|sáb|dom|[ap]\.|m\.)[,.]?$/.test(lw)) return x;
      if (!f && ES_SMALL.has(lw)) return lw;
      const i = x.search(/[a-záéíóúñü]/i);
      return i < 0 ? x : x.slice(0, i) + x.charAt(i).toUpperCase() + x.slice(i + 1);
    })
    .join("");
}
function esText(n) {
  const v = n.data;
  if (esDone.get(n) === v) return;
  const p = n.parentElement;
  if (!p || esSkip(p)) return;
  const core = v.trim();
  if (!core || (!/[A-Za-z]/.test(core) && !/^\d{1,2}\/\d{1,2}(?:\/\d{2,4})?$/.test(core))) return;
  const ctx = ES_CTX.find(([sel, map]) => core in map && p.closest(sel)),
    out = ctx ? ctx[1][core] : esT(core);
  if (out === core) return;
  const lead = v.match(/^\s*/)[0],
    trail = v.match(/\s*$/)[0],
    nv = lead + (esIsLabel(p) ? esTitle(out) : out) + trail;
  esOrig.has(n) || esOrig.set(n, v);
  esDone.set(n, nv);
  n.data = nv;
}
const esAOrig = new WeakMap(), // element -> {attribute: English}
  esADone = new WeakMap(); // element -> {attribute: Spanish we wrote}
function esAttr(el) {
  if (!el || !el.getAttribute || (el.closest && el.closest("[data-nocase],[data-verbatim],[data-es-skip]"))) return;
  ES_ATTRS.forEach((a) => {
    const v = el.getAttribute(a);
    if (!v || !/[A-Za-z]/.test(v)) return;
    const done = esADone.get(el) || {};
    if (done[a] === v) return;
    const out = esT(v);
    if (out === v) return;
    const orig = esAOrig.get(el) || {};
    a in orig || ((orig[a] = v), esAOrig.set(el, orig));
    (done[a] = out), esADone.set(el, done);
    el.setAttribute(a, out);
  });
}
function esPass(root) {
  if (!esOn()) return;
  root = root || document.body;
  if (!root) return;
  if (root.nodeType === 3) return esText(root);
  if (root.nodeType !== 1) return;
  // a field's own words stay as typed, but its hint (placeholder) is the app's
  const hint = (n) => n.matches && n.matches("textarea,input") && esAttr(n);
  if (esSkip(root)) return void hint(root);
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, {
    acceptNode: (n) => (n.nodeType === 1 && n.matches && n.matches(ES_SKIP) && !n.matches(ES_FORCE) ? (hint(n), NodeFilter.FILTER_REJECT) : NodeFilter.FILTER_ACCEPT),
  });
  esAttr(root);
  let n;
  while ((n = w.nextNode())) n.nodeType === 3 ? esText(n) : esAttr(n);
}
// back to English: every node this pass changed gets its English back
function esRestore() {
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = w.nextNode())) esOrig.has(n) && ((n.data = esOrig.get(n)), esOrig.delete(n), esDone.delete(n));
  document.querySelectorAll("[placeholder],[title],[aria-label]").forEach((el) => {
    const o = esAOrig.get(el);
    o && (Object.entries(o).forEach(([a, v]) => el.setAttribute(a, v)), esAOrig.delete(el), esADone.delete(el));
  });
}
// Everything drawn later (a sheet, a toast, a list that fills in) is read as it lands.
let esObs = null,
  esQ = new Set(),
  esQT = 0;
function esFlush() {
  esQT = 0;
  if (!esOn()) return void esQ.clear();
  const L = [...esQ];
  esQ.clear();
  L.forEach((n) => n.isConnected && esPass(n));
}
function esWatch() {
  if (esObs || !window.MutationObserver) return;
  esObs = new MutationObserver((recs) => {
    if (!esOn()) return;
    recs.forEach((r) => {
      if ("childList" === r.type) r.addedNodes.forEach((n) => esQ.add(n));
      else if ("characterData" === r.type) esQ.add(r.target);
      else if ("attributes" === r.type) esQ.add(r.target);
    });
    // a microtask: before the browser paints, so the English never shows
    esQT || ((esQT = 1), Promise.resolve().then(esFlush));
  });
  esObs.observe(document.body, { childList: !0, subtree: !0, characterData: !0, attributes: !0, attributeFilter: ES_ATTRS });
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      esApply();
    } catch (e) {
      console.warn("es", e);
    }
    return r;
  };
}
let esWas = !1;
function esApply() {
  const on = esOn();
  document.documentElement.lang = on ? "es" : "en";
  document.body && document.body.classList.toggle("es", on);
  esTitleCase(on);
  if (on) esWatch(), esPass(document.body);
  else esWas && esRestore();
  esWas = on;
  try {
    esLangCtl();
  } catch (e) {}
}

// ---- the house label rule in Spanish: the words in ES are already cased as labels in Spanish (Title Case, connecting
// words lowercase), so the app's English Title Case pass stands down while the screen is Spanish (TC_OFF, its own
// switch), and comes back as it was when the screen is English again.
let esTcWas = null;
function esTitleCase(on) {
  if ("undefined" == typeof TC_OFF) return;
  on ? (null === esTcWas && (esTcWas = TC_OFF), (TC_OFF = !0)) : null !== esTcWas && ((TC_OFF = esTcWas), (esTcWas = null));
}

// ---- the setting: the person's own, in the menu (where a person who reads no English can find it: "Idioma"), and the
// owner's Team list. It is the person's field (u.lang), saved with the person and audited.
function esSetLang(uid, lang) {
  const u = (DB.users || []).find((x) => x.id === uid);
  if (!u || !["en", "es"].includes(lang)) return !1;
  const was = u.lang || "en";
  if (was === lang) return !0;
  u.lang = lang;
  "function" == typeof audit && audit("user", u.id, `language ${was} → ${lang}`);
  save(), render();
  const me = esUser();
  toast(me && me.id === uid ? ("es" === lang ? "Listo: la app está en español" : "Done: the app is in English") : `${u.name} reads ${"es" === lang ? "Spanish" : "English"} on the field screens`);
  return !0;
}
function esLangCtl() {
  const u = esUser(),
    foot = document.querySelector(".rail .foot");
  if (!foot) return;
  let box = document.getElementById("es-lang");
  if (!u || !ES_FIELD.includes(u.role)) return void (box && box.remove());
  const lang = esLangOf(u);
  box || ((box = document.createElement("div")), (box.id = "es-lang"), (box.className = "es-lang"), foot.insertBefore(box, document.getElementById("foot")));
  const want = `<span class="es-lang-k" data-es-skip>Idioma · Language</span><div class="es-lang-seg" role="group" aria-label="Idioma" data-es-skip><button type="button" data-eslang="en" class="${"en" === lang ? "on" : ""}" aria-pressed="${"en" === lang}">English</button><button type="button" data-eslang="es" class="${"es" === lang ? "on" : ""}" aria-pressed="${"es" === lang}">Español</button></div>`;
  box.innerHTML !== want && (box.innerHTML = want);
  box.querySelectorAll("[data-eslang]").forEach((b) => (b.onclick = () => esSetLang(u.id, b.dataset.eslang)));
}
// the owner's Team list: each person's language, next to their role
"function" == typeof renderUsers &&
  (() => {
    const base = renderUsers;
    renderUsers = function () {
      const r = base.apply(this, arguments);
      try {
        document.querySelectorAll("#users-list [data-urole]").forEach((sel) => {
          const u = (DB.users || []).find((x) => x.id === sel.dataset.urole);
          if (!u || sel.parentElement.querySelector("[data-ulang]")) return;
          const s = document.createElement("select");
          s.dataset.ulang = u.id;
          s.setAttribute("aria-label", `${u.name}'s language`);
          s.title = "Language of the field screens";
          s.innerHTML = `<option value="en" ${"es" !== u.lang ? "selected" : ""}>English</option><option value="es" ${"es" === u.lang ? "selected" : ""}>Español</option>`;
          s.onchange = () => esSetLang(u.id, s.value);
          sel.after(s);
        });
      } catch (e) {}
      return r;
    };
  })();

// ---- voice input listens in the person's language: every recogniser the app makes asks for es-US
(function () {
  const wrap = (C) => {
    if (!C || C.__es) return C;
    const W = function () {
      const r = new C();
      let lang = r.lang;
      try {
        Object.defineProperty(r, "lang", {
          configurable: !0,
          get: () => lang,
          set: (v) => {
            lang = esOn() && /^en/i.test(String(v || "")) ? ES_LOCALE : v;
            try {
              C.prototype && Object.getOwnPropertyDescriptor(Object.getPrototypeOf(r), "lang") && Object.getOwnPropertyDescriptor(Object.getPrototypeOf(r), "lang").set.call(r, lang);
            } catch (e) {}
          },
        });
        r.lang = lang || "en-US";
      } catch (e) {}
      return r;
    };
    W.prototype = C.prototype;
    W.__es = !0;
    return W;
  };
  try {
    window.SpeechRecognition && (window.SpeechRecognition = wrap(window.SpeechRecognition));
    window.webkitSpeechRecognition && (window.webkitSpeechRecognition = wrap(window.webkitSpeechRecognition));
  } catch (e) {}
})();

// ---- the assistant answers a Spanish reader in Spanish
"function" == typeof mindSystem &&
  (() => {
    const base = mindSystem;
    mindSystem = function () {
      const s = base.apply(this, arguments);
      return esOn() ? `${s}\n\nThis person reads Spanish (their language setting). Answer in plain Spanish as construction crews in New York speak it, short sentences, keeping the trade words they say in English (sheetrock, framing, taping, PO) and every name, number, date and record number as written.` : s;
    };
  })();

// ---- the field's Standard in Spanish -------------------------------------------------------------------------------
let esStdEnglish = !1;
function esMdInline(t) {
  return esc(t).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\*(.+?)\*/g, "<i>$1</i>");
}
function esStandardHtml() {
  const el = document.getElementById("sd-standard-es-md"),
    md = el ? el.textContent : "",
    lines = md.split("\n");
  let h = "",
    list = "",
    table = [];
  const flush = () => {
    list && ((h += `</${list}>`), (list = ""));
    if (table.length) {
      const rows = table.filter((r) => !/^\|\s*-/.test(r)).map((r) => r.replace(/^\||\|$/g, "").split("|").map((c) => c.trim()));
      const hd = rows.shift() || [];
      h += `<div class="es-esc">${rows.map((r) => `<div class="es-esc-row"><b>${esMdInline(r[0])}</b><span><span class="muted">${esc(hd[1] || "")}:</span> ${esMdInline(r[1] || "")}</span><span><span class="muted">${esc(hd[2] || "")}:</span> ${esMdInline(r[2] || "")}</span></div>`).join("")}</div>`;
      table = [];
    }
  };
  let src = "";
  lines.forEach((ln) => {
    const t = ln.trim();
    if (/^Fuente:/.test(t)) return void (src = t.replace(/^Fuente:\s*/, ""));
    if (/^\|/.test(t)) return void table.push(t);
    if (/^- /.test(t)) return list !== "ul" && (flush(), (h += "<ul>"), (list = "ul")), void (h += `<li>${esMdInline(t.slice(2))}</li>`);
    if (/^\d+\. /.test(t)) return list !== "ol" && (flush(), (h += "<ol>"), (list = "ol")), void (h += `<li>${esMdInline(t.replace(/^\d+\.\s/, ""))}</li>`);
    flush();
    if (!t) return;
    if (/^# /.test(t)) return void (h += `<div class="ph"><div><h2>${esMdInline(t.slice(2))}</h2></div></div>`);
    if (/^## /.test(t)) return void (h += `<h3 class="es-std-h">${esMdInline(t.slice(3))}</h3>`);
    h += `<p>${esMdInline(t)}</p>`;
  });
  flush();
  // the English is the source: when Alan has published a newer version, the page says so
  let note = "";
  try {
    const v = "function" == typeof standardLive ? standardLive() : null,
      was = +(String(src).match(/\d+/) || [0])[0];
    v && was && +v.version > was && (note = `<div class="note warn small es-std-new">El inglés cambió después de esta traducción (versión ${+v.version}, ${esc(String(v.at || "").slice(0, 10))}). Mientras se traduce, lo que vale es el inglés: tócalo abajo.</div>`);
  } catch (e) {}
  return `<div class="es-std" data-es-skip>${h}${note}<div class="row" style="margin-top:14px"><button type="button" class="btn" data-esstden>Ver Todo en Inglés</button></div></div>`;
}
"function" == typeof renderStandard &&
  (() => {
    const base = renderStandard;
    renderStandard = function () {
      const r = base.apply(this, arguments),
        host = document.getElementById("standard-body"),
        u = esUser();
      if (!host || !u || !ES_FIELD.includes(u.role) || "es" !== u.lang) return r;
      if (esStdEnglish) {
        if (!host.querySelector("[data-esstdes]")) {
          const b = document.createElement("div");
          b.className = "row";
          b.style.margin = "0 0 12px";
          b.innerHTML = '<button type="button" class="btn" data-esstdes data-es-skip>Ver en Español</button>';
          host.prepend(b);
          b.querySelector("button").onclick = () => ((esStdEnglish = !1), renderStandard());
        }
        return r;
      }
      host.innerHTML = esStandardHtml();
      host.querySelector("[data-esstden]").onclick = () => ((esStdEnglish = !0), renderStandard(), window.scrollTo(0, 0));
      return r;
    };
  })();

// ---- chat lines translated for the reader ---------------------------------------------------------------------------
// A line is written in its writer's language (m.lang; English when unset). A reader in another language sees a
// Traducir / Translate button under it; the translation is kept on the line (m.tr[lang]) and shown labelled, with the
// original one tap away. The office gets the field's Spanish lines in English on its own when the AI door is there.
const esTrShowOrig = new Set(),
  esTrBusy = new Set();
function esLineLang(m) {
  return (m && m.lang) || "en";
}
"function" == typeof msgTextFor &&
  (() => {
    msgTextFor = function (m, u) {
      const want = esLangOf(u);
      return m && m.tr && m.tr[want] && esLineLang(m) !== want && !esTrShowOrig.has(m.id) ? m.tr[want] : String((m && m.text) || "");
    };
  })();
function esMsgFind(id) {
  const u = esUser();
  try {
    for (const T of msgThreadsFor(u, !0)) {
      const m = (T.all ? T.all() : T.msgs || []).find((x) => x && x.id === id);
      if (m) return m;
    }
  } catch (e) {}
  return null;
}
async function esAiTranslate(text, to) {
  const j = await mindPost(
    {
      tier: "small",
      purpose: "translate",
      max_tokens: 700,
      system: `Translate the message into ${"es" === to ? "Spanish as construction crews in New York speak it" : "plain English"}. Keep every name, number, measurement, address, record number and the trade words the crew says in English (sheetrock, framing, taping, PO). Answer with the translation only.`,
      messages: [{ role: "user", content: String(text || "") }],
    },
    3e4,
  );
  const out = ((j && j.content) || [])
    .filter((b) => "text" === b.type)
    .map((b) => b.text)
    .join("")
    .trim();
  if (!out) throw new Error("no translation came back");
  return out;
}
function esTranslator() {
  if ("function" == typeof MSG_TRANSLATE) return MSG_TRANSLATE;
  try {
    return "function" == typeof mindCan && mindCan() ? esAiTranslate : null;
  } catch (e) {
    return null;
  }
}
async function esTranslateLine(id, quiet) {
  const m = esMsgFind(id),
    u = esUser(),
    to = esLangOf(u),
    es = "es" === to;
  if (!m) return !1;
  if (m.tr && m.tr[to]) return esTrShowOrig.has(id) ? esTrShowOrig.delete(id) : esTrShowOrig.add(id), render(), !0;
  const f = esTranslator();
  if (!f) return quiet || toast(es ? "Para traducir hace falta la app de la empresa en línea" : "Translating needs the firm's app online (the AI door)"), !1;
  if (esTrBusy.has(id)) return !1;
  esTrBusy.add(id), quiet || render();
  try {
    const out = await f(String(m.text || ""), to);
    (m.tr = Object.assign({}, m.tr || {}, { [to]: String(out) })), (m.trAt = Object.assign({}, m.trAt || {}, { [to]: appNowIso() }));
    save();
    quiet || toast(es ? "Traducido; el original está a un toque" : "Translated; the original is one tap away");
    return !0;
  } catch (e) {
    quiet || toast((es ? "No se pudo traducir: " : "Could not translate: ") + String(e.message || e).slice(0, 80));
    return !1;
  } finally {
    esTrBusy.delete(id), render();
  }
}
let esAutoDone = new Set();
function esChatDecorate() {
  if ("chat" !== view) return;
  const u = esUser();
  if (!u) return;
  const to = esLangOf(u),
    es = "es" === to,
    auto = !ES_FIELD.includes(u.role) && "client" !== u.role && !!esTranslator();
  document.querySelectorAll(".view.on .cm[data-mid]:not(.sys)").forEach((row) => {
    const id = row.dataset.mid,
      m = id && esMsgFind(id);
    if (!m || !String(m.text || "").trim() || esLineLang(m) === to) return;
    const has = !!(m.tr && m.tr[to]),
      busy = esTrBusy.has(id),
      orig = esTrShowOrig.has(id);
    // the office reads the field's Spanish in English on its own, once per line, while the AI door is there
    auto && !has && !busy && "es" === esLineLang(m) && !esAutoDone.has(id) && esAutoDone.size < 40 && (esAutoDone.add(id), esTranslateLine(id, !0));
    const lab = busy ? (es ? "Traduciendo…" : "Translating…") : has ? (orig ? (es ? "Ver Traducción" : "Show Translation") : es ? "Traducido · Ver Original" : "Translated · Show Original") : es ? "Traducir" : "Translate",
      html = `<button type="button" class="es-trb${has && !orig ? " on" : ""}" data-estr="${esc(id)}" data-es-skip ${busy ? "disabled" : ""}>${lab}</button>`;
    let b = row.querySelector(".es-trb");
    if (b && b.outerHTML === html) return;
    b && b.remove();
    const col = row.querySelector(".msg-col") || row;
    col.insertAdjacentHTML("beforeend", html);
    col.querySelector(".es-trb").onclick = (e) => (e.stopPropagation(), esTranslateLine(id));
  });
}
// The PM's answer to something the field raised (Today › For You) is the office's words: a Spanish reader gets the same
// Traducir under it, and the translation is kept on the raise (r.answerTr[lang]), labelled.
const esAnsBusy = new Set(),
  esAnsOrig = new Set();
async function esTranslateAnswer(id) {
  const r = ((DB.field || {}).raises || []).find((x) => x.id === id),
    to = esLangOf(esUser()),
    es = "es" === to;
  if (!r || !String(r.answer || "").trim()) return !1;
  if (r.answerTr && r.answerTr[to]) return esAnsOrig.has(id) ? esAnsOrig.delete(id) : esAnsOrig.add(id), render(), !0;
  const f = esTranslator();
  if (!f) return toast(es ? "Para traducir hace falta la app de la empresa en línea" : "Translating needs the firm's app online (the AI door)"), !1;
  esAnsBusy.add(id), render();
  try {
    r.answerTr = Object.assign({}, r.answerTr || {}, { [to]: String(await f(String(r.answer), to)) });
    save(), toast(es ? "Traducido; el original está a un toque" : "Translated; the original is one tap away");
    return !0;
  } catch (e) {
    toast((es ? "No se pudo traducir: " : "Could not translate: ") + String(e.message || e).slice(0, 80));
    return !1;
  } finally {
    esAnsBusy.delete(id), render();
  }
}
function esAnswerDecorate() {
  if (!esOn() || "ftoday" !== view) return;
  const to = esLangOf(esUser());
  document.querySelectorAll('.view.on [data-fack^="answer:"]').forEach((b) => {
    const id = b.dataset.fack.slice(7),
      r = ((DB.field || {}).raises || []).find((x) => x.id === id),
      row = b.parentElement,
      span = row && row.querySelector(".grow .small");
    if (!r || !span || !String(r.answer || "").trim()) return;
    const tr = r.answerTr && r.answerTr[to],
      busy = esAnsBusy.has(id),
      orig = esAnsOrig.has(id);
    if (tr && !orig) {
      const a = String(r.answer).trim(),
        cur = span.textContent;
      cur.includes(a) && ((span.textContent = cur.replace(a, tr)), span.setAttribute("data-es-skip", ""));
    }
    const lab = busy ? "Traduciendo…" : tr ? (orig ? "Ver Traducción" : "Traducido · Ver Original") : "Traducir";
    let btn = row.querySelector(".es-trb");
    btn || ((btn = document.createElement("button")), (btn.type = "button"), (btn.className = "es-trb"), btn.setAttribute("data-es-skip", ""), span.after(btn));
    btn.textContent !== lab && (btn.textContent = lab);
    btn.disabled = busy;
    btn.onclick = (e) => (e.stopPropagation(), esTranslateAnswer(id));
  });
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      esChatDecorate(), esAnswerDecorate();
    } catch (e) {
      console.warn("translate", e);
    }
    return r;
  };
}

// ---- the look
(function () {
  const css = `
.es-lang{margin:0 0 10px}.es-lang-k{display:block;font-size:10.5px;letter-spacing:.5px;text-transform:uppercase;color:rgba(255,255,255,.42);font-weight:600;margin:0 0 4px}
.es-lang-seg{display:flex;gap:8px}.es-lang-seg button{flex:1;min-height:44px;border-radius:var(--r);border:1px solid rgba(255,255,255,.18);background:#232B3B;color:rgba(255,255,255,.85);font-size:13px;font-weight:600}
.es-lang-seg button.on{background:#fff;color:var(--ink);border-color:#fff}
.es-trb{align-self:flex-start;background:none;border:0;color:var(--accent);font-size:12px;padding:6px 4px;min-height:32px;cursor:pointer}
.cm.me .es-trb{align-self:flex-end}.es-trb.on{color:var(--ink-3)}.grow>.es-trb{display:block;padding-left:0}
.es-std h3.es-std-h{margin:18px 0 6px;font-size:15px}.es-std p{margin:6px 0;line-height:1.5}.es-std ul,.es-std ol{margin:6px 0 6px 18px;padding:0}.es-std li{margin:4px 0;line-height:1.45}
.es-esc{display:flex;flex-direction:column;gap:8px;margin:8px 0}.es-esc-row{display:flex;flex-direction:column;gap:2px;border:1px solid var(--rule);border-radius:8px;padding:8px 10px;background:var(--paper)}
.es-std-new{margin-top:12px}
@media (max-width:640px){.es-trb{min-height:44px}}
`;
  const s = document.createElement("style");
  (s.id = "es-css"), (s.textContent = css), document.head.appendChild(s);
})();
