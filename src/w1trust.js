// =====================================================================================================================
// Wave 1, Trust (lane w1trust, 2026-10-25, docs/PATH_TO_9.md). Pilot 2's role experts forgave missing features and
// never forgave lost work or a wrong default. This file holds four classes, each fixed once for every screen:
//  D1  Drafts are never lost. Every sheet and form that takes typing keeps a draft per person and per record as the
//      person types. A sheet closed by a screen change, Back, Escape or a tap outside keeps it, and the same sheet
//      opens again with the text; a reload picks the open sheet up again. Discard asks first.
//  D2  Every button does what its label says (tests/tap_label_lint.py holds it; the fixes are named where they sit).
//  D3  Defaults from context: Make It a Task's due date and notes from its own mail, clock-out's pre-ticked work from
//      what the person clocked in on or logged today, quick add's explicit date and time.
//  D4  Silent saves: every mutation the lint found saving with no word now says what happened, with Open.
//
// Design gate (BACKLOG §1.16). D1 extends the sheets that exist (mbModal's #mbm, the editor drawer, the line sheet,
// the message sheet, the task-view pop-over, Report a Problem, the composer) and p2fix1's "a sheet belongs to its
// screen" rule; no sheet carries its own draft code. The one new store is the drafts themselves, and it is
// deliberately not in DB: a draft is one person's unsent typing on one device (the CLAUDE.md "unsent draft"
// convenience), it must never sync to the firm's shared records (a field role's DB copy would carry the controller's
// half-typed bill), it must never bump the shared version on every keystroke, and nothing counts or reports it. It
// lives in this browser's localStorage under the person's id, and it expires after 14 days. No new list, queue or
// menu item: a kept draft is offered back by its own toast (Open) and by the sheet itself when it opens again.
// =====================================================================================================================

// ---- D1: where a sheet lives, what closes it, what is typed in it ---------------------------------------------------
const W1_HOSTS = [
  { sel: "#mbm", body: ".mbm-bd", title: ".mbm-hd h3", close: () => "function" == typeof mbCloseModal && mbCloseModal() },
  { sel: "#drawer", on: "on", body: "#d-body", title: "#d-title", close: () => "function" == typeof closeEditor && closeEditor() },
  { sel: "#ct-sheet", body: null, title: ".ct-sheet-bar b", close: null },
  { sel: "#msg-sheet", body: ".msg-sheet-in", title: null, close: null },
  { sel: "#tv-pop", body: ".tv-pop-bd", title: ".tv-pop-hd b", close: null },
  { sel: "#rp-panel", body: null, title: ".rp-hd h3", close: () => "function" == typeof rpClose && rpClose() },
  { sel: "#hb-composer", body: null, title: ".hb-composer-hd b", close: (el) => el.remove() },
];
// the controls that close a sheet without acting on it: what was typed is kept as a draft
const W1_CLOSERS =
  ".mbm-x, #mbm-cancel, #d-close, #d-cancel, #rp-x, #hb-comp-x, [data-tvpx], .tv-pop-x, [data-msgsheetx], .msg-sheet-bg, [data-cts=done], .ct-sheet-back";
const W1_CLOSE_WORDS = /^(cancel|close|not now|back|keep editing|done)$/i;
// a field whose text is a search or a filter is not a draft
const W1_SKIP_TYPES = /^(search|hidden|file|password|button|submit|reset|image|range|color)$/;
const W1_SKIP_WORDS = /\b(search|filter|find|look up|type to)\b/i;
const W1_DAYS = 14;

const w1Uid = () => {
  try {
    return (DB && DB.deviceUser) || "";
  } catch (e) {
    return "";
  }
};
function w1Load() {
  try {
    const all = JSON.parse(localStorage.getItem("sd-drafts") || "{}");
    return all && "object" == typeof all ? all : {};
  } catch (e) {
    return {};
  }
}
function w1Store(all) {
  try {
    localStorage.setItem("sd-drafts", JSON.stringify(all));
  } catch (e) {}
}
// this person's drafts, oldest gone after 14 days, at most 40
function w1Mine(all) {
  const u = w1Uid(),
    M = (all[u] = all[u] || {}),
    cut = Date.now() - W1_DAYS * 864e5;
  Object.keys(M).forEach((k) => (M[k].wall || 0) < cut && delete M[k]);
  const ks = Object.keys(M).sort((a, b) => (M[b].wall || 0) - (M[a].wall || 0));
  ks.slice(40).forEach((k) => delete M[k]);
  return M;
}
function w1Get(key) {
  const M = w1Mine(w1Load());
  return M[key] || null;
}
function w1Put(key, d) {
  const all = w1Load(),
    M = w1Mine(all);
  d ? (M[key] = d) : delete M[key];
  w1Store(all);
}
// the drafts this person has, newest first (Ask and the test read them; nothing else lists them)
function w1Drafts() {
  const M = w1Mine(w1Load());
  return Object.keys(M)
    .map((k) => Object.assign({ key: k }, M[k]))
    .filter((d) => d.fields && Object.keys(d.fields).length)
    .sort((a, b) => (b.wall || 0) - (a.wall || 0));
}

const w1Norm = (s) => String(s || "").replace(/\s+/g, " ").trim();
// The app's own reads of a field are how a tap is known to have used what was typed (a Send, a Save, an Add read the
// field while the tap ran; a chip that only paints the sheet again does not). Reads during a tap are noted against the
// field's draft; this file reads fields through the browser's own getters, so it never counts as a reader.
const W1_RAW = (() => {
  const g = (P, k) => {
    const d = Object.getOwnPropertyDescriptor(P, k);
    return d && d.get ? d : null;
  };
  return { iv: g(HTMLInputElement.prototype, "value"), ic: g(HTMLInputElement.prototype, "checked"), tv: g(HTMLTextAreaElement.prototype, "value"), sv: g(HTMLSelectElement.prototype, "value") };
})();
let w1Reading = null; // the sheet or page a tap is running in: only its own fields' reads count
const w1Used = new Map(); // "<draft key>::<field>" -> when a tap read it
(() => {
  const hook = (P, k, d) => {
    if (!d) return;
    try {
      Object.defineProperty(P, k, {
        configurable: !0,
        enumerable: d.enumerable,
        get() {
          w1Reading && this._w1k && w1Reading.contains(this) && w1Used.set(this._w1k, performance.now());
          return d.get.call(this);
        },
        set(v) {
          d.set.call(this, v);
        },
      });
    } catch (e) {}
  };
  hook(HTMLInputElement.prototype, "value", W1_RAW.iv), hook(HTMLInputElement.prototype, "checked", W1_RAW.ic);
  hook(HTMLTextAreaElement.prototype, "value", W1_RAW.tv), hook(HTMLSelectElement.prototype, "value", W1_RAW.sv);
})();
const w1UsedLately = (k) => performance.now() - (w1Used.get(k) || -1e9) < 1500;
// a tap (or Enter) opens a short window in which a read of a typed field in the same sheet or page means the tap used it
function w1OpenReadWindow(scope) {
  if (!scope) return;
  w1Reading = scope;
  setTimeout(() => w1Reading === scope && (w1Reading = null), 0);
}

function w1IsField(el) {
  if (!el || !el.tagName || el.disabled || el.readOnly) return !1;
  const tg = el.tagName;
  if ("TEXTAREA" !== tg && "INPUT" !== tg && "SELECT" !== tg) return !1;
  if ("INPUT" === tg && W1_SKIP_TYPES.test(el.type || "")) return !1;
  if (el.closest("[data-nodraft], .itp, #pal, header.topbar, #subnav, #mtabs, #tabbar, .w1-dr, #signin")) return !1;
  const words = `${el.placeholder || ""} ${el.getAttribute("aria-label") || ""} ${el.name || ""} ${el.id || ""}`;
  return !W1_SKIP_WORDS.test(words) && !/(^|[-_])(q|search|filter)([-_]|$)/i.test(el.id || "");
}
const w1Fields = (root) => (root ? [...root.querySelectorAll("input, textarea, select")].filter(w1IsField) : []);
// a field's name inside its sheet or page: what names it (id, data-f, name, its data attributes, its label words),
// then which one of the same name it is
function w1Base(el) {
  const da = [...el.attributes]
    .filter((a) => /^data-/.test(a.name) && !/^data-(sim|w1|sd)/.test(a.name))
    .map((a) => `${a.name}=${a.value}`)
    .join(",");
  const nm = el.id || (el.dataset && el.dataset.f) || el.name || da || el.getAttribute("aria-label") || el.placeholder || "";
  return `${el.tagName}:${el.type || ""}:${nm}`;
}
function w1Sigs(root) {
  const seen = {},
    out = new Map();
  w1Fields(root).forEach((el) => {
    const b = w1Base(el),
      n = (seen[b] = (seen[b] || 0) + 1);
    out.set(el, `${b}#${n}`);
  });
  return out;
}
function w1Val(el) {
  const chk = "checkbox" === el.type || "radio" === el.type;
  if (chk) return (W1_RAW.ic ? W1_RAW.ic.get.call(el) : el.checked) ? "1" : "";
  const d = "TEXTAREA" === el.tagName ? W1_RAW.tv : "SELECT" === el.tagName ? W1_RAW.sv : W1_RAW.iv,
    v = d ? d.get.call(el) : el.value;
  return String(v == null ? "" : v);
}
function w1Before(el) {
  if (void 0 !== el._w1d0) return el._w1d0;
  if ("checkbox" === el.type || "radio" === el.type) return el.defaultChecked ? "1" : "";
  if ("SELECT" === el.tagName) {
    const o = [...el.options].find((x) => x.defaultSelected) || el.options[0];
    return o ? o.value : "";
  }
  return String(el.defaultValue == null ? "" : el.defaultValue);
}
function w1Set(el, v) {
  "checkbox" === el.type || "radio" === el.type ? (el.checked = "1" === v) : (el.value = v);
  el._w1typed = !0;
  w1Setting = !0;
  try {
    el.dispatchEvent(new Event("input", { bubbles: !0 })), ("SELECT" === el.tagName || "checkbox" === el.type || "radio" === el.type) && el.dispatchEvent(new Event("change", { bubbles: !0 }));
  } catch (e) {
  } finally {
    w1Setting = !1;
  }
}
let w1Setting = !1;

// ---- D1: the screen a sheet was opened on, and the control that opened it -------------------------------------------
function w1Screen() {
  try {
    return {
      view: "undefined" != typeof view ? view : "",
      doc: "undefined" != typeof docOpen && docOpen ? { kind: docOpen.kind, id: docOpen.id } : null,
      po: "undefined" != typeof poOpen ? poOpen || null : null,
      client: "undefined" != typeof clientOpen ? clientOpen || null : null,
      cur: "undefined" != typeof S && S ? S.id || null : null,
    };
  } catch (e) {
    return {};
  }
}
const w1ScreenKey = (s) => [s.view, s.doc ? s.doc.kind + ":" + s.doc.id : "", s.po || "", s.client || "", s.cur || ""].join("|");
const W1_CTL = "button, a, [role=button], summary, [data-act], [data-bact], tr, .tcard, .gl";
function w1Opener(el) {
  const c = el && el.closest && el.closest(W1_CTL);
  if (!c || w1HostOf(c)) return null;
  const attrs = [...c.attributes].filter((a) => /^data-/.test(a.name) && !/^data-(sim|w1|sd)/.test(a.name) && a.value.length < 120);
  return { tag: c.tagName.toLowerCase(), id: c.id || "", attrs: attrs.map((a) => [a.name, a.value]), txt: w1Norm(c.innerText || c.getAttribute("aria-label") || "").slice(0, 80) };
}
function w1FindOpener(o) {
  if (!o) return null;
  let sel = o.tag + (o.id ? "#" + CSS.escape(o.id) : "");
  (o.attrs || []).forEach(([n, v]) => (sel += `[${n}="${CSS.escape(v)}"]`));
  let C = [];
  try {
    C = [...document.querySelectorAll(sel)].filter((x) => x.getClientRects().length && !w1HostOf(x));
  } catch (e) {}
  const txt = (x) => w1Norm(x.innerText || x.getAttribute("aria-label") || "").slice(0, 80);
  return C.find((x) => txt(x) === o.txt) || (C.length === 1 && (o.id || (o.attrs || []).length) ? C[0] : null);
}

// ---- D1: the last thing the person did (a tap, a key, Back), and where ----------------------------------------------
let w1Last = { t: 0, host: null, close: !1 };
function w1HostOf(el) {
  for (const h of W1_HOSTS) {
    const x = el && el.closest && el.closest(h.sel);
    if (x && (!h.on || x.classList.contains(h.on))) return x;
  }
  return null;
}
function w1IsCloser(el, host) {
  if (!el || !el.closest) return !1;
  if (el === host || (el.classList && el.classList.contains("mbm"))) return !0; // the backdrop of a sheet
  if (el.closest(W1_CLOSERS)) return !0;
  const b = el.closest("button, a, [role=button]");
  return !!(b && W1_CLOSE_WORDS.test(w1Norm(b.innerText || b.getAttribute("aria-label") || "")) && !b.closest(".w1-dr"));
}
function w1Note(e, kind) {
  const el = e && e.target && e.target.nodeType === 1 ? e.target : null;
  let host = el ? w1HostOf(el) : null,
    close = host ? w1IsCloser(el, host) || ("key" === kind && "Escape" === e.key) : !1;
  // the editor's scrim and Report a Problem's scrim sit outside their sheets: a tap on one closes its sheet
  el && "scrim" === el.id && ((host = document.querySelector("#drawer.on")), (close = !0));
  el && "rp-scrim" === el.id && ((host = document.getElementById("rp-panel")), (close = !0));
  w1Last = { t: performance.now(), host, close, kind, opener: host ? null : w1Opener(el) };
  if ("click" === e.type || "Enter" === e.key) {
    const pr = !host && el ? w1PageRoot() : null;
    w1OpenReadWindow(host || (pr && pr.contains(el) ? pr : null));
  }
  if (host && !close && !(el.closest && el.closest(".w1-dr"))) {
    const st = W1.get(host);
    st && ((st.actAt = w1Last.t), setTimeout(() => w1AfterAct(host), 80), setTimeout(() => w1AfterAct(host), 700));
  }
}
document.addEventListener("pointerdown", (e) => w1Note(e, "tap"), !0);
document.addEventListener("click", (e) => w1Note(e, "tap"), !0);
document.addEventListener("keydown", (e) => ("Escape" === e.key || "Enter" === e.key) && w1Note(e, "key"), !0);
window.addEventListener("popstate", () => (w1Last = { t: performance.now(), host: null, close: !0, kind: "back" }), !0);
// "Leave Without Saving" on the Unsaved Changes question is the person's own discard: the held sheet's draft goes
let w1DropAt = 0;
document.addEventListener(
  "click",
  (e) => {
    const a = e.target && e.target.closest && e.target.closest("#mbm-alt");
    a && /Leave Without Saving/.test(a.textContent || "") && (w1DropAt = performance.now());
  },
  !0,
);

// ---- D1: one record per open sheet ----------------------------------------------------------------------------------
const W1 = new Map(); // host element -> { def, key, title, screen, opener, at, actAt }
const w1HostDef = (el) => W1_HOSTS.find((h) => el.matches && el.matches(h.sel));
const w1BodyOf = (el, st) => (st.def.body && el.querySelector(st.def.body)) || el;
function w1Title(el, def) {
  const t = def && def.title ? el.querySelector(def.title) : null;
  return w1Norm((t && t.textContent) || el.getAttribute("aria-label") || ((el.querySelector("[role=dialog]") || {}).getAttribute || (() => ""))("aria-label") || "");
}
function w1BodyText(el, def) {
  const b = (def && def.body && el.querySelector(def.body)) || el,
    c = b.cloneNode(!0);
  c.querySelectorAll("input, select, textarea, option, script, style, .w1-dr, button").forEach((x) => x.remove());
  return w1Norm(c.textContent).slice(0, 160);
}
function w1KeyOf(el, def) {
  const title = w1Title(el, def);
  if ("#drawer" === def.sel)
    try {
      if ("undefined" != typeof editing && editing) return `drawer|${editing.kind}|${editing.id || "new"}|${title}`;
    } catch (e) {}
  if ("#ct-sheet" === def.sel)
    try {
      return `line|${docOpen ? docOpen.kind + ":" + docOpen.id : ""}|${title}`;
    } catch (e) {}
  return `${def.sel}|${title}|${w1BodyText(el, def)}`;
}
function w1Register(el) {
  const def = w1HostDef(el);
  if (!def || W1.has(el) || (def.on && !el.classList.contains(def.on))) return;
  const opener = w1Last.opener && performance.now() - w1Last.t < 4e3 ? w1Last.opener : null;
  const st = { def, key: w1KeyOf(el, def), title: w1Title(el, def), screen: w1Screen(), opener, at: performance.now(), actAt: 0 };
  W1.set(el, st), (w1Opened = !0);
  const d = w1Get(st.key);
  d && ((d.open = !0), (d.screen = st.screen), (d.opener = opener || d.opener), w1Put(st.key, d));
  // wait for the sheet's own wiring (prefills, focus) before putting the typing back
  setTimeout(() => w1Restore(el), 40);
  // a sheet that paints its body again (a chip, a step) gets its typing back too
  try {
    const mo = new MutationObserver(() => {
      clearTimeout(st.rt), (st.rt = setTimeout(() => el.isConnected && w1Restore(el), 30));
    });
    mo.observe(el, { childList: !0, subtree: !0 }), (st.mo = mo);
  } catch (e) {}
}
// put back what this person typed in this sheet, field by field, where the field still shows what it showed before
// and no tap used it since
function w1Restore(el) {
  const st = W1.get(el);
  if (!st || st.discarded) return;
  const d = w1Get(st.key);
  if (!d || !d.fields) return;
  let put = 0;
  w1Sigs(w1BodyOf(el, st)).forEach((sig, f) => {
    const x = d.fields[sig];
    f._w1k = st.key + "::" + sig;
    if (!x || x.v === x.d0 || (f._w1typed && f._w1own) || w1UsedLately(f._w1k)) return;
    const now = w1Val(f);
    if (now === x.v || now !== x.d0) return;
    if ((f._w1n = (f._w1n || 0) + 1) > 3) return;
    w1Set(f, x.v), (f._w1d0 = x.d0), put++;
  });
  put && !st.restored && ((st.restored = !0), w1Bar(el, st, d));
}
// "Your draft is back", with Discard Draft, which asks first
function w1Bar(el, st, d) {
  const box = w1BodyOf(el, st);
  if (!box || box.querySelector(":scope > .w1-dr")) return;
  const bar = document.createElement("div");
  (bar.className = "w1-dr"), bar.setAttribute("role", "status");
  const when = d.at ? stampText(d.at).replace(/^\d+\/\d+, /, "") : "";
  const paint = () => {
    bar.innerHTML = `<span class="grow">Your draft${when ? ` from ${esc(when)}` : ""} is back, as you left it.</span><button type="button" class="btn sm" data-w1ask>Discard Draft</button>`;
    bar.querySelector("[data-w1ask]").onclick = (e) => (e.preventDefault(), ask());
  };
  const ask = () => {
    bar.innerHTML = `<span class="grow">Discard what you typed here? It cannot be brought back.</span><button type="button" class="btn sm" data-w1keep>Keep It</button><button type="button" class="btn sm danger" data-w1drop>Discard</button>`;
    bar.querySelector("[data-w1keep]").onclick = (e) => (e.preventDefault(), paint());
    bar.querySelector("[data-w1drop]").onclick = (e) => {
      e.preventDefault();
      const cur = w1Get(st.key);
      cur &&
        w1Sigs(w1BodyOf(el, st)).forEach((sig, f) => {
          const x = cur.fields[sig];
          x && w1Val(f) === x.v && w1Set(f, x.d0);
        });
      w1Put(st.key, null), (st.discarded = !0), bar.remove(), toast(`Draft discarded: ${st.title || "this sheet"}`);
    };
  };
  paint(), box.prepend(bar);
}
// what is typed now is the draft (only the fields the person typed in, where they differ from what the field showed)
function w1Snap(el) {
  const st = W1.get(el);
  if (!st || st.discarded) return;
  const prev = w1Get(st.key),
    fields = Object.assign({}, (prev && prev.fields) || {});
  w1Sigs(w1BodyOf(el, st)).forEach((sig, f) => {
    f._w1k = st.key + "::" + sig;
    const x = fields[sig];
    if (!x && !f._w1typed) return;
    const v = w1Val(f),
      d0 = x ? x.d0 : w1Before(f);
    v === d0 ? delete fields[sig] : (fields[sig] = { v, d0 });
  });
  if (!Object.keys(fields).length) return void (prev && w1Put(st.key, null));
  w1Put(st.key, { title: st.title, at: appNowIso(), wall: Date.now(), fields, screen: st.screen, opener: st.opener, open: !0, scope: "sheet" });
}
// after a tap inside the sheet: still open, what is typed now is the draft
function w1AfterAct(el) {
  const st = W1.get(el);
  st && el.isConnected && (!st.def.on || el.classList.contains(st.def.on)) && w1Snap(el);
}
// the sheet closed. By its own Save or Send (the last thing the person did was a tap inside it, not a close) the draft
// goes. By a close, a screen change, Back, Escape or a tap outside, it stays and the toast offers it back.
function w1Gone(el) {
  const st = W1.get(el);
  if (!st) return;
  W1.delete(el), st.mo && st.mo.disconnect(), clearTimeout(st.st);
  const d = w1Get(st.key);
  if (!d) return;
  const acted = w1Last.host === el && !w1Last.close;
  if (st.discarded || acted || performance.now() - w1DropAt < 1500) return void w1Put(st.key, null);
  (d.open = !1), w1Put(st.key, d);
  setTimeout(() => {
    // another sheet took its place (a question asked over it, the next step): the person is looking at that one
    if (document.querySelector("#mbm, #mbm-held, #drawer.on") || !w1Get(st.key)) return;
    toast(`Draft kept: ${st.title || "what you typed"}`, { label: "Open", run: () => w1Reopen(st.key) });
  }, 0);
}
// open a kept draft's sheet again: its screen, then the control that opened it
function w1Reopen(key) {
  const d = w1Get(key);
  if (!d) return toast("That draft is no longer here");
  const s = d.screen || {};
  if (/^drawer\|/.test(key)) {
    const [, kind, id] = key.split("|");
    try {
      return void openEditor(kind, "new" === id ? void 0 : id);
    } catch (e) {}
  }
  try {
    s.cur && "function" == typeof setCurrent && (!S || S.id !== s.cur) && setCurrent(s.cur);
    "undefined" != typeof clientOpen && (clientOpen = s.client || null);
    "undefined" != typeof poOpen && (poOpen = s.po || null);
    "undefined" != typeof docOpen && (docOpen = s.doc ? Object.assign({}, s.doc) : null);
    s.view && (view = s.view);
    render();
  } catch (e) {
    console.warn("draft reopen", e);
  }
  setTimeout(() => {
    const b = w1FindOpener(d.opener);
    b ? b.click() : toast(`Your draft of ${d.title || "that sheet"} is kept: open it here again and the text comes back`);
  }, 80);
}
// every keystroke in a sheet is the draft (a short wait, so a fast typist is one write)
["input", "change"].forEach((k) =>
  document.addEventListener(
    k,
    (e) => {
      const f = e.target;
      if (w1Setting || !w1IsField(f)) return;
      (f._w1typed = !0), (f._w1own = !0);
      const host = w1HostOf(f);
      if (host) {
        W1.has(host) || w1Register(host);
        const st = W1.get(host);
        st && (clearTimeout(st.st), (st.st = setTimeout(() => host.isConnected && w1Snap(host), 250)));
        return;
      }
      clearTimeout(f._w1pt), (f._w1pt = setTimeout(() => f.isConnected && w1PageType(f), 250));
    },
    !0,
  ),
);
// what a field showed before the person typed (a prefill drawn after the page counts as what it showed)
document.addEventListener(
  "focusin",
  (e) => {
    const f = e.target;
    f && w1IsField(f) && void 0 === f._w1d0 && (f._w1d0 = w1Val(f));
  },
  !0,
);
// a sheet appears or goes
try {
  new MutationObserver((M) => {
    M.forEach((m) => {
      m.addedNodes.forEach((n) => n.nodeType === 1 && w1HostDef(n) && w1Register(n));
      m.removedNodes.forEach((n) => n.nodeType === 1 && W1.has(n) && w1Gone(n));
    });
  }).observe(document.body, { childList: !0 });
  const dr = document.getElementById("drawer");
  dr &&
    new MutationObserver(() => {
      dr.classList.contains("on") ? W1.has(dr) || w1Register(dr) : W1.has(dr) && w1Gone(dr);
    }).observe(dr, { attributes: !0, attributeFilter: ["class"] });
} catch (e) {
  console.warn("drafts", e);
}

// ---- D1: a form on the page (an estimate's or a change order's fields, a composer, a decision) ----------------------
// A field that saves when it loses focus saves on the way out (the screen change blurs it first). A field with its own
// Save or Send keeps what was typed when the page is drawn again or the person comes back to it, until a tap uses it.
let w1PageKey = null;
const w1PageRoot = () => document.querySelector("section.view.on") || document.querySelector("main");
const w1PageDraftKey = () => "page|" + w1ScreenKey(w1Screen());
function w1PageType(f) {
  const root = w1PageRoot();
  if (!root || !root.contains(f)) return;
  const key = w1PageDraftKey(),
    sig = w1Sigs(root).get(f);
  if (!sig) return;
  f._w1k = key + "::" + sig;
  const d = w1Get(key) || { title: "", fields: {}, scope: "page" },
    x = d.fields[sig],
    v = w1Val(f),
    d0 = x ? x.d0 : w1Before(f);
  v === d0 ? delete d.fields[sig] : (d.fields[sig] = { v, d0 });
  (d.at = appNowIso()), (d.wall = Date.now()), (d.screen = w1Screen());
  w1Put(key, Object.keys(d.fields).length ? d : null);
}
// a tap that read a typed field used it (its Send, its Save, its Add): that field's draft goes once the tap has run
function w1PageUsed() {
  setTimeout(() => {
    const key = w1PageDraftKey(),
      d = w1Get(key);
    if (!d) return;
    let n = 0;
    Object.keys(d.fields).forEach((sig) => w1UsedLately(key + "::" + sig) && (delete d.fields[sig], n++));
    n && w1Put(key, Object.keys(d.fields).length ? d : null);
  }, 30);
}
document.addEventListener("click", w1PageUsed, !0);
document.addEventListener("keydown", (e) => "Enter" === e.key && w1PageUsed(), !0);
function w1PageRestore() {
  const root = w1PageRoot();
  if (!root) return;
  const key = w1PageDraftKey(),
    d = w1Get(key);
  if (!d || !d.fields) return;
  let put = 0,
    gone = 0;
  w1Sigs(root).forEach((sig, f) => {
    const x = d.fields[sig];
    f._w1k = key + "::" + sig;
    if (!x || (f._w1typed && f._w1own)) return;
    if (w1UsedLately(f._w1k)) return delete d.fields[sig], void gone++; // a tap just used it
    const now = w1Val(f);
    if (now === x.v) return delete d.fields[sig], void gone++; // saved: nothing left to keep
    if (now !== x.d0) return;
    w1Set(f, x.v), (f._w1d0 = x.d0), f.classList.add("w1-typed"), put++;
  });
  gone && w1Put(key, Object.keys(d.fields).length ? d : null);
  if (!put || root.querySelector(".w1-dr")) return;
  const bar = document.createElement("div");
  (bar.className = "w1-dr w1-dr-page"), bar.setAttribute("role", "status");
  const paint = () => {
    bar.innerHTML = `<span class="grow">What you typed here and had not saved is back.</span><button type="button" class="btn sm" data-w1ask>Discard It</button>`;
    bar.querySelector("[data-w1ask]").onclick = () => {
      bar.innerHTML = `<span class="grow">Discard what you typed here? It cannot be brought back.</span><button type="button" class="btn sm" data-w1keep>Keep It</button><button type="button" class="btn sm danger" data-w1drop>Discard</button>`;
      bar.querySelector("[data-w1keep]").onclick = paint;
      bar.querySelector("[data-w1drop]").onclick = () => {
        const cur = w1Get(key) || { fields: {} };
        w1Sigs(w1PageRoot()).forEach((sig, f) => {
          const x = cur.fields[sig];
          x && w1Val(f) === x.v && (w1Set(f, x.d0), f.classList.remove("w1-typed"));
        });
        w1Put(key, null), bar.remove(), toast("Discarded what you typed");
      };
    };
  };
  paint();
  const first = root.querySelector(".w1-typed"),
    at = first && (first.closest(".card, form, .f") || first);
  at ? at.before(bar) : root.prepend(bar);
}

// ---- D1: a sheet belongs to its screen; the screen change saves on the way out --------------------------------------
// p2fix1 closes the line sheet, the message sheet and the task-view pop-over with their screen. Every other sheet
// (#mbm, the editor drawer, Report a Problem, the composer) now goes the same way when the person moved to another
// screen after opening it: the cost-code sheet no longer stays on top of every page until answered, and what was
// typed in it is the draft. A sheet that the same tap opened along with the new screen stays: it is that screen's.
// A focused field on the page is blurred first, so a field that saves on change saves before its screen goes.
function w1LeaveScreen() {
  const a = document.activeElement;
  try {
    a && a !== document.body && w1IsField(a) && !w1HostOf(a) && a.blur();
  } catch (e) {}
  W1.forEach((st, el) => {
    if (!el.isConnected || !st.def.close) return;
    if (st.def.on && !el.classList.contains(st.def.on)) return;
    if (!(w1Last.t > st.at && w1Last.host !== el)) return; // only a move the person made after it opened, from outside it
    if ("#mbm" === st.def.sel && "mbm" !== el.id) return; // a sheet held aside under a question
    w1Snap(el);
    try {
      st.def.close(el);
    } catch (e) {
      console.warn("sheet close", e);
    }
  });
}
{
  const base = render;
  render = function () {
    let k = "";
    try {
      k = w1ScreenKey(w1Screen());
      null !== w1PageKey && k !== w1PageKey && w1LeaveScreen();
    } catch (e) {}
    w1PageKey = k;
    const r = base.apply(this, arguments);
    try {
      w1PageRestore(), w1ReopenAfterReload();
    } catch (e) {
      console.warn("drafts", e);
    }
    return r;
  };
}
// a reload (the phone dropped the page, a new version, the next turn) brings back the sheet that was open, once
// (only before this page has opened a sheet of its own)
let w1Reloaded = !1,
  w1Opened = !1;
function w1ReopenAfterReload() {
  if (w1Reloaded || w1Opened || !w1Uid() || "1" !== document.body.dataset.booted) return;
  const k = w1ScreenKey(w1Screen());
  const d = w1Drafts().find((x) => x.open && "sheet" === x.scope && x.screen && w1ScreenKey(x.screen) === k && Date.now() - (x.wall || 0) < 864e5);
  if (!d) return;
  w1Reloaded = !0;
  const o = w1Get(d.key);
  o && ((o.open = !1), w1Put(d.key, o));
  setTimeout(() => {
    if (document.querySelector("#mbm, #drawer.on")) return;
    if (/^drawer\|/.test(d.key)) {
      const [, kind, id] = d.key.split("|");
      try {
        return void openEditor(kind, "new" === id ? void 0 : id);
      } catch (e) {}
    }
    const b = w1FindOpener(d.opener);
    b && b.click();
  }, 120);
}
// a different person signing in on this device gets their own drafts only, and their own pick-up
{
  const base = signIn;
  signIn = function () {
    w1Reloaded = !1;
    return base.apply(this, arguments);
  };
}

// ---- D3: Make It a Task takes its date and its notes from its own mail ---------------------------------------------
// Pilot 2, the designer: six times Make It a Task set the wrong due date. A promise of "end of day" read as a week
// later (Friday written on a Friday was taken as next Friday); Chen's "by noon today (order-by 9/16)" took the order-by
// date; and the notes came from Chen's other mail (the thread's old subject, "Re: laundry depth"). The rule, for every
// path that makes a task from a mail (the Today card, the Inbox's Task From This Message): the date the person
// promised in their own reply on that thread, else the date the mail asks for, else the event it names (a hearing, an
// inspection: the working day before), never an order-by, ship-by or delivery date; and the notes are that mail's own
// words.
const W1_DOW = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
const W1_SAMEDAY = /\b(end of (?:the )?day|eod|close of business|cob|tonight|this (?:morning|afternoon|evening)|noon|midday|today)\b/i;
// a date that is not the ask: when the thing must be ordered, shipped, delivered, released, on site, or someone is out
const W1_NOTASK = /\b(order(?:ed)?|ship(?:s|ped|ping)?|deliver(?:y|ed|s)?|release[sd]?|arriv(?:e|es|al)|lead time|on site|onsite|install(?:ed)?|fabricat\w*|back|out)[-\s]*(?:by|on|date|for|to|until)?[\s:(]*$/i;
// one date phrase in words, read against the day the mail was written
function w1DateWord(w, base) {
  const t = String(w || "").toLowerCase().trim(),
    b = base || today();
  let m = t.match(/\b(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?\b/);
  if (m) {
    const y = m[3] ? (m[3].length === 2 ? 2000 + +m[3] : +m[3]) : +b.slice(0, 4),
      d = iso(new Date(y, +m[1] - 1, +m[2]));
    return !m[3] && d < iso(addDays(b, -60)) ? iso(new Date(y + 1, +m[1] - 1, +m[2])) : d;
  }
  m = t.match(/\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b/);
  if (m) return iso(new Date(+b.slice(0, 4), ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].indexOf(m[1]), +m[2]));
  if (/\btomorrow\b/.test(t)) return iso(addDays(b, 1));
  m = t.match(/\b(next\s+)?(sun|mon|tue|wed|thu|fri|sat)[a-z]*\b/);
  if (m) {
    let k = (W1_DOW.indexOf(m[2]) - parse(b).getDay() + 7) % 7;
    // "Friday" written on a Friday is that day; "next Friday" is the one after
    m[1] && k < 7 && (k += 7);
    return iso(addDays(b, k));
  }
  if (/\bend of (?:the )?week\b|\bthis week\b/.test(t)) return w1DateWord("friday", b);
  if (/\bnext week\b/.test(t)) return addWork(b, 5);
  if (W1_SAMEDAY.test(t)) return b;
  return "";
}
// every dated deadline in a text that is when the person must act (not an order-by), the ones said with "by" first
const W1_DATE_RX = /\b(?:(?:by|before|no later than|until|due|for|on)\s+)?((?:next\s+)?(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)[a-z]*\.?(?:\s+\d{1,2}\/\d{1,2})?|\d{1,2}\/\d{1,2}(?:\/\d{2,4})?|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.? \d{1,2}|tomorrow|today|tonight|end of (?:the )?(?:day|week)|eod|close of business|cob|this (?:morning|afternoon|evening)|noon(?:\s+today)?)\b/gi;
function w1Deadlines(text, base) {
  const out = [],
    t = String(text || "").replace(/\s+/g, " ");
  let m;
  W1_DATE_RX.lastIndex = 0;
  while ((m = W1_DATE_RX.exec(t))) {
    const before = t.slice(Math.max(0, m.index - 28), m.index),
      lead = /^(by|before|no later than|until|due|for|on)\b/i.test(m[0]) ? m[0].split(/\s+/)[0] : "";
    // "(order-by 9/16)", "ships 9/11", "Tomas out to 9/14": not when the person must act
    if (W1_NOTASK.test(before + (lead ? lead + " " : "")) || W1_NOTASK.test(before)) continue;
    const said = !!lead && /^(by|before|no|until|due)$/i.test(lead) || /\b(by|before|due|until)\s*$/i.test(before) || W1_SAMEDAY.test(m[1]) || /end of/i.test(m[1]);
    let d = w1DateWord(m[1], base);
    // "by end of day Wed 9/9", "by noon tomorrow": the time of day belongs to the date after it
    if (W1_SAMEDAY.test(m[1]) && !/\btoday\b/i.test(m[1])) {
      const ahead = t.slice(m.index + m[0].length, m.index + m[0].length + 26).match(/^\s*,?\s*(?:on\s+)?((?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?(?:\s+\d{1,2}\/\d{1,2})?|\d{1,2}\/\d{1,2}|tomorrow|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? \d{1,2})/i);
      ahead && (d = w1DateWord(ahead[1], base) || d) && (W1_DATE_RX.lastIndex = m.index + m[0].length + ahead[0].length);
    }
    d && d >= base && out.push({ d, said, words: m[0].trim() });
  }
  return out.sort((a, b) => b.said - a.said || a.d.localeCompare(b.d));
}
const w1Own = (c) => ("function" == typeof cmOwnText ? cmOwnText((c && c.text) || "") : String((c && c.text) || ""));
const w1Sents = (t) => String(t || "").replace(/\s+/g, " ").split(/(?<=[.?!;])\s+/);
// the person's own mail on the thread after the ask, that commits to a date ("I ... send the count by end of day Wed 9/9")
function w1MyReply(c) {
  if (!c || !c.threadId) return null;
  const me = currentUser() || {},
    em = ("function" == typeof lnMyEmail && lnMyEmail(me.id)) || String(me.email || "").toLowerCase(),
    at = String(c.date || "");
  const mine = (DB.comms || [])
    .filter((x) => x !== c && x.threadId === c.threadId && String(x.date || "") >= at)
    .filter((x) => (em && String((x.from || {}).email || "").toLowerCase() === em) || ("out" === x.direction && (!x.owner || x.owner === me.id)))
    .sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")));
  for (const x of mine) {
    const base = String(x.date || "").slice(0, 10) || today();
    for (const s of w1Sents(w1Own(x))) {
      if (!/\b(i|we|i'll|we'll|you'll have)\b/i.test(s)) continue;
      const D = w1Deadlines(s, base).filter((y) => y.said);
      if (D.length) return { due: D[0].d, sentence: s.trim(), mail: x };
    }
  }
  return null;
}
// the date a mail asks for, in its own words
function w1AskedDate(c) {
  const base = String((c && c.date) || "").slice(0, 10) || today();
  for (const s of w1Sents(w1Own(c))) {
    const D = w1Deadlines(s, base).filter((y) => y.said);
    if (D.length) return { due: D[0].d, sentence: s.trim() };
  }
  return null;
}
// the one rule for a task made from a mail: { due, why, sentence }
function w1MailDue(c, p) {
  if (!c) return null;
  const td = today(),
    clamp = (d) => (d < td ? td : d);
  const r = w1MyReply(c);
  if (r) return { due: clamp(r.due), why: `the date you gave in your reply, ${fmtL(r.due)}`, sentence: r.sentence };
  const a = w1AskedDate(c);
  if (a) return { due: clamp(a.due), why: `the date the mail asks for, ${fmtL(a.due)}`, sentence: a.sentence };
  try {
    const pr = p || ((c.route || {}).projectId && (DB.projects || []).find((x) => x.id === c.route.projectId));
    const R = "function" == typeof recDueFrom ? recDueFrom(`${c.subject || ""}\n${w1Own(c)}`, pr) : null;
    if (R) return { due: R.due, why: R.why, sentence: "" };
  } catch (e) {}
  return null;
}
// the notes: that mail's words, who wrote them and when (a reply's old subject belongs to another conversation)
function w1MailNotes(c, sentence) {
  const who = (c.from && (c.from.name || c.from.email)) || "The sender",
    day = String(c.date || "").slice(0, 10),
    own = w1Own(c).replace(/\s+/g, " ").trim(),
    subj = /^(re|fwd?|fw):/i.test(String(c.subject || "").trim()) ? "" : String(c.subject || "").trim();
  const said = sentence && own.includes(sentence.slice(0, 40)) ? sentence : own.slice(0, 240);
  return `${who}${day ? ` on ${fmtL(day)}` : ""}${subj ? ` (${subj})` : ""}: “${said}”`;
}
{
  const base = newTaskDialog;
  newTaskDialog = function (preset, opts) {
    try {
      const P = preset || {},
        cid = P.source && P.source.commId,
        c = cid && (DB.comms || []).find((x) => x.id === cid);
      if (c && !P.dueKept) {
        const pr = P.projectId && (DB.projects || []).find((x) => x.id === P.projectId);
        const R = w1MailDue(c, pr);
        const P2 = Object.assign({}, P, { notes: w1MailNotes(c, R && R.sentence) });
        R && ((P2.due = R.due), (P2.source = Object.assign({}, P.source, { label: `${P.source.label || "a message"}; due ${fmtL(R.due)}, ${R.why}` })));
        arguments[0] = P2;
      }
    } catch (e) {
      console.warn("task from mail", e);
    }
    return base.apply(this, arguments);
  };
}
// a promise made in mail ("I'll send the window drawing by end of day"): due the day it was written, not a week on
{
  const base = lnPromiseOf;
  lnPromiseOf = function (c) {
    const r = base.apply(this, arguments);
    try {
      const sent = String((c && c.date) || "").slice(0, 10) || today(),
        txt = String((c && c.text) || "").replace(/\s+/g, " ");
      if (!r) {
        const m = txt.match(/\b(?:I(?:'|’)ll|I will|we(?:'|’)ll|we will)\s+(send|get|have|deliver|finish|issue|share|email|submit|bring|forward)\s+([^.!?\n]{4,90}?)\s+(?:by\s+|before\s+)?(end of (?:the )?day|eod|close of business|cob|tonight|this (?:morning|afternoon|evening)|noon)\b/i);
        if (!m) return r;
        const t0 = (c.to || [])[0],
          to = (t0 && (t0.name || t0.email)) || ("string" == typeof t0 ? t0 : "") || "";
        return { what: `${m[1]} ${m[2]}`.replace(/\s+/g, " ").trim(), due: sent, to: String(to).replace(/<.*$/, "").trim(), sent };
      }
      const m = txt.match(LN_PROMISE);
      if (m) {
        const d = w1DateWord(m[3], sent);
        d && d >= sent && (r.due = d);
      }
    } catch (e) {}
    return r;
  };
}

// ---- D3: quick add keeps the date and time the person said ----------------------------------------------------------
// The PM typed "Call a backup mason for 121 State restoration (Tomas out to 9/14) Wed 9/9 8am" and got Mon 9/14: the
// first date anywhere won, even inside the parenthesis, and the title lost "to 9/14". A parenthesis is the person's
// note: it stays in the title whole and its dates are never the due date; a short weekday with a date ("Wed 9/9") is
// that date, and the time said stays in the title.
if ("function" == typeof tvQaParse) {
  const base = tvQaParse;
  tvQaParse = function (text) {
    const raw = String(text || ""),
      keep = [],
      masked = raw.replace(/\([^()]*\)/g, (x) => (keep.push(x), ` zqpar${keep.length - 1}q `));
    const r = base.call(this, masked);
    try {
      r.text = raw;
      let t = String(r.title || "");
      keep.forEach((x, i) => (t = t.replace(new RegExp(`\\s*zqpar${i}q\\s*`, "i"), ` ${x} `)));
      const outside = masked.replace(/zqpar\d+q/g, " ");
      const dm = outside.match(/\b(mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)\.?\s+(\d{1,2}\/\d{1,2})\b/i);
      if (dm) {
        const d = w1DateWord(dm[2], today());
        d && (r.due = d), (t = t.replace(new RegExp(`\\b${dm[1]}\\.?(?=\\s|$)`, "i"), " "));
      } else if (!r.due) {
        const wm = outside.match(/\b(?:by |on |due )?(mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)\b\.?/i);
        wm && ((r.due = w1DateWord(wm[1], today())), (t = t.replace(wm[0], " ")));
      }
      // the time said ("8am") stays, as a time
      t = t.replace(/\b(\d{1,2})(?::(\d\d))?\s*(am|pm)\b/i, (x, h, mi, ap) => `by ${+h}${mi ? ":" + mi : ""} ${ap.toUpperCase()}`);
      t = t.replace(/\s{2,}/g, " ").replace(/\s+([,.;:!?)])/g, "$1").replace(/\(\s+/g, "(").trim();
      r.title = t ? t.charAt(0).toUpperCase() + t.slice(1) : t;
    } catch (e) {
      console.warn("quick add", e);
    }
    return r;
  };
}

// ---- D3: clock-out ticks only what the person was on ---------------------------------------------------------------
// Pilot 2: the clock-out sheet ticked "Windows & interior trim" for Alberto (his task is Framing & blocking, his name on
// it) and for Alex the driver, because an in-house task that had started was taken as everyone's day; and it replaced
// the line Alberto had just logged with Add a Line. The job then pays finish carpentry for a van run. Ticked now: a
// line the person already logged today (with its hours), the task or cost code they clocked in on, a task with their
// name on it, a task they logged progress on today. Nothing else, so an unknown day is ticked by the person, never
// guessed. The driver's sheet has the driver's own work: driving and material runs, pickups, deliveries.
if ("function" == typeof f3WorkedOn) {
  f3WorkedOn = function (t, e, p) {
    try {
      if ((e.work || []).some((w) => w.taskId && w.taskId === t.id)) return !0;
      if (e.taskId && e.taskId === t.id) return !0;
      if (e.code && "99" !== e.code && t.trade && codeForTrade(t.trade) === e.code) return !0;
      const emp = (DB.employees || []).find((x) => x.id === e.empId) || {},
        nm = String(emp.name || "").toLowerCase(),
        first = nm.split(" ")[0],
        own = String(t.owner || t.assignee || "").trim().toLowerCase();
      if (first && own && (own === nm || own === first || own.split(/[\s,&/]+/).includes(first))) return !0;
      return (t.pctLog || []).some((l) => l.on === e.date && first && String(l.by || "").toLowerCase().split(" ")[0] === first);
    } catch (x) {
      return !1;
    }
  };
}
const W1_DRIVE = [
  ["w1drv:drive", "Driving and material runs"],
  ["w1drv:pickup", "Pickups"],
  ["w1drv:deliver", "Deliveries"],
];
function w1IsDriver(e) {
  const emp = (DB.employees || []).find((x) => x.id === (e && e.empId)) || {},
    u = (DB.users || []).find((x) => x.employeeId === emp.id) || {};
  return "driver" === u.role || /\bdriver\b/i.test(emp.role || "");
}
if ("function" == typeof f3DaySheet) {
  const base = f3DaySheet;
  f3DaySheet = function (e) {
    if (e && w1IsDriver(e)) return w1DriverDay(e);
    const logged = ((e && e.work) || []).filter((w) => w.taskId && +w.hours > 0);
    const r = base.apply(this, arguments);
    try {
      const m = document.getElementById("mbm");
      // what the person logged with Add a Line comes ticked with its hours: the sheet confirms the day, it does not redo it
      m &&
        logged.forEach((w) => {
          const cb = m.querySelector(`[data-f3t2="${CSS.escape(w.taskId)}"]`),
            h = m.querySelector(`[data-f3h="${CSS.escape(w.taskId)}"]`);
          cb && ((cb.checked = !0), cb.dispatchEvent(new Event("change", { bubbles: !0 })));
          h && ((h.value = String(w.hours)), h.dispatchEvent(new Event("change", { bubbles: !0 })));
        });
    } catch (x) {}
    return r;
  };
}
function w1DriverDay(e) {
  const p = (DB.projects || []).find((x) => x.id === e.projectId) || S,
    total = "function" == typeof hoursOf ? r2(hoursOf(e)) : 0,
    td = e.date,
    tasks = ((p && p.tasks) || []).filter((t) => t.start && t.end && t.start <= td && t.end >= td && "done" !== t.status),
    logged = (e.work || []).filter((w) => +w.hours > 0),
    on = (id) => logged.some((w) => (w.taskId || w.drv) === id),
    hrs = (id) => (logged.find((w) => (w.taskId || w.drv) === id) || {}).hours || "",
    row = (id, name, sub) =>
      `<label class="f3-dayrow"><input type="checkbox" data-f3t2="${esc(id)}" ${on(id) ? "checked" : ""}><span class="nm"><b>${esc(name)}</b><i>${esc(sub)}</i></span><input class="hr" type="number" step="0.25" min="0" data-f3h="${esc(id)}" value="${esc(String(hrs(id)))}" aria-label="Hours on ${esc(name)}"></label>`;
  const gc = COST_CODES.find((c) => "01" === c[0]) || ["01", "General conditions & supervision"];
  mbModal(
    `${total} hours on ${esc(p.project.name)}`,
    `<p class="small muted" style="margin:0 0 10px">What did the day go to? Tick it and the hours split evenly across what you tick; change any of them if the day was not even.</p>
    <div class="f3-day">${W1_DRIVE.map(([id, n]) => row(id, n, `${gc[0]} · ${gc[1]}`)).join("")}${tasks.map((t) => row(t.id, t.name, t.trade ? `${codeForTrade(t.trade)} · on site` : "on site")).join("")}</div>
    <div class="f3-sum"><span>Accounted for</span><b id="f3-sum">0 of ${total} h</b></div>
    <p class="small muted" style="margin:8px 0 0">This puts your hours on a cost code, so the job knows what it paid for.</p>`,
    {
      submit: "That Is My Day",
      onSubmit: () => {
        const m = document.getElementById("mbm"),
          ids = [...m.querySelectorAll("[data-f3t2]:checked")].map((x) => x.dataset.f3t2);
        if (!ids.length) return toast("Tick what the day went to"), !1;
        const H = {};
        let given = 0;
        ids.forEach((id) => {
          const v = +(m.querySelector(`[data-f3h="${CSS.escape(id)}"]`) || {}).value || 0;
          v > 0 && ((H[id] = v), (given = r2(given + v)));
        });
        const blank = ids.filter((id) => !H[id]);
        blank.forEach((id) => (H[id] = r2(Math.max(0, total - given) / blank.length)));
        e.work = ids.map((id) => {
          const d = W1_DRIVE.find((x) => x[0] === id),
            t = d ? null : (p.tasks || []).find((x) => x.id === id) || {};
          return d
            ? { projectId: p.id, taskId: "", drv: id, code: gc[0], line: "", hours: r2(H[id] || 0), note: d[1] }
            : { projectId: p.id, taskId: id, code: t.trade ? codeForTrade(t.trade) : "", line: t.lineRef || "", hours: r2(H[id] || 0), note: t.name || "" };
        });
        e.code = e.work[0].code;
        e.status = "submitted";
        audit("time", e.id, "day-logged", null, { hours: total, lines: ids.length });
        save(), render();
        toast(`${total} h logged: ${e.work.map((w) => w.note).join(", ")}. The office sees it for approval`, { label: "Open", run: () => ("function" == typeof openTime ? openTime(e.id) : ((view = "time"), render())) });
      },
    },
  );
  const m = document.getElementById("mbm");
  if (!m) return;
  const sum = () => {
    const ids = [...m.querySelectorAll("[data-f3t2]:checked")].map((x) => x.dataset.f3t2);
    let given = 0,
      blank = 0;
    ids.forEach((id) => {
      const v = +(m.querySelector(`[data-f3h="${CSS.escape(id)}"]`) || {}).value || 0;
      v > 0 ? (given = r2(given + v)) : blank++;
    });
    const el = m.querySelector("#f3-sum");
    el && (el.textContent = blank ? `${ids.length} ticked · the rest splits evenly` : `${given} of ${total} h`);
  };
  m.querySelectorAll("[data-f3t2],[data-f3h]").forEach((x) => x.addEventListener("change", sum)), sum();
}

// ---- D2: every button does what its label says (tests/tap_label_lint.py) ---------------------------------------------
// A mail row's verb says what the tap does. "Apply" on a row whose apply only notes it and makes a task (the client's
// "money is sent" mail: it records that a payment is expected and gives the controller a task; the bank line is matched
// where money is matched) read as if it recorded something (Pilot 2, billing: "Apply did not apply anything").
// A certificate or a W-9 files on the vendor, and says so.
function w1MailVerb(pkind, pr) {
  if ("deposit" === pkind) return "Watch the Feed";
  if ("ar" === pkind && !pr.clientId) return "Watch for the Money";
  if ("coi" === pkind || "w9" === pkind) return pr.vendorId ? "File on the Vendor" : "Make It a Task";
  return null;
}
if ("function" == typeof nyhRowsAll) {
  const base = nyhRowsAll;
  nyhRowsAll = function () {
    const out = base.apply(this, arguments);
    try {
      (out || []).forEach((r) => {
        if ("mail" !== r.kind || "Apply" !== r.verb) return;
        const c = (DB.comms || []).find((x) => x.id === r.commId),
          pr = c && (c.proposals || []).find((p) => p.kind === r.pkind && (r.key || "").startsWith(`mail:${p.kind}:`));
        const v = pr && w1MailVerb(r.pkind, pr);
        v && (r.verb = v);
      });
    } catch (e) {}
    return out;
  };
}
// The toast's Open goes to the record the tap changed, not to the mail it came from: the controller's Enter the Bill
// toast opened Inbox, a page the controller does not have ("Mail is opened by the Owner, the PM and the coordinator"),
// not SE-0922. What changed is read from the records themselves, before and after.
const W1_REC = [
  ["bills", () => DB.bills || [], (x) => flowGo.bill(x)],
  ["pos", () => DB.pos || [], (x) => flowGo.po(x)],
  ["vendors", () => DB.vendors || [], (x) => flowGo.vendor(x)],
  ["leads", () => DB.leads || [], (x) => flowGo.lead(x)],
  ["txns", () => DB.txns || [], (x) => () => ("function" == typeof txnDialog ? txnDialog(x.id) : flowGo.viewOf("bank")())],
];
function w1Snapshot() {
  const S0 = {};
  W1_REC.forEach(([k, get]) => {
    const m = new Map();
    try {
      get().forEach((x) => x && x.id && m.set(x.id, JSON.stringify(x)));
    } catch (e) {}
    S0[k] = m;
  });
  try {
    S0.tasks = new Map();
    (DB.projects || []).forEach((p) => (p.actions || []).forEach((a) => S0.tasks.set(a.id, p.id)));
  } catch (e) {}
  return S0;
}
// the record a tap made or changed, as a toast link the person may follow
function w1Touched(S0) {
  for (const [k, get, go] of W1_REC) {
    const before = S0[k] || new Map();
    let hit = null;
    try {
      hit = get().find((x) => x && x.id && !before.has(x.id)) || get().find((x) => x && x.id && before.has(x.id) && before.get(x.id) !== JSON.stringify(x));
    } catch (e) {}
    if (hit) return { kind: k, rec: hit, run: go(hit) };
  }
  try {
    for (const p of DB.projects || [])
      for (const a of p.actions || [])
        if (!S0.tasks.has(a.id))
          return {
            kind: "task",
            rec: a,
            run: () => ("function" == typeof crOpenTask ? crOpenTask({ kind: "action", id: a.id, projectId: p.id, rec: a }) : (setCurrent(p.id), (view = "tasks"), render())),
          };
  } catch (e) {}
  return null;
}
const w1MayOpen = (k) => {
  const v = { bills: ["ap", "bills"], pos: ["po", "proc"], vendors: ["vendors", "vend"], leads: ["hbdeals", "leads"], txns: ["bank", "txns"] }[k];
  return !v || v.some((x) => (ROLE_VIEWS[role()] || []).includes(x));
};
if ("function" == typeof nyhApplyMail) {
  const base = nyhApplyMail;
  nyhApplyMail = function (c, pr) {
    const S0 = w1Snapshot(),
      r = base.apply(this, arguments);
    try {
      const t = w1Touched(S0),
        el = document.getElementById("toast"),
        msg = el && el.classList.contains("on") ? ((el.querySelector(".toast-msg") || el).textContent || "").trim() : "";
      t && msg && (w1MayOpen(t.kind) || "task" === t.kind) && toast(msg, { label: "Open", run: t.run });
    } catch (e) {}
    return r;
  };
}
// Add Milestone opened the editor titled "New Task": the editor's title says what is being made
document.addEventListener("change", (e) => {
  const t = e.target;
  if (!t || "e-type" !== t.id || !t.closest("#drawer")) return;
  const h = document.getElementById("d-title");
  h && /^New (Task|Milestone)$/.test(h.textContent.trim()) && (h.textContent = "milestone" === t.value ? "New Milestone" : "New Task");
});
document.addEventListener("click", (e) => {
  if (!e.target.closest || !e.target.closest("#btn-addms")) return;
  setTimeout(() => {
    const h = document.getElementById("d-title"),
      ty = document.getElementById("e-type");
    h && ty && "milestone" === ty.value && /^New Task$/.test(h.textContent.trim()) && (h.textContent = "New Milestone");
  }, 0);
});

// ---- D4: a question asked before a step never swallows the step ----------------------------------------------------
// "Yes, Continue" replays the button that asked. When the screen was drawn again under the question (a row's Done on a
// list that refreshed, Delete behind Please Confirm), that button was no longer on the page and the replay clicked
// nothing: the foreman's first Yes, Continue on Done gave no toast and the row stayed at 90%, billing's Yes, Continue on
// Delete said nothing. The button is now found again on the screen by what it is (its data attributes and its label),
// and when it is truly gone the person is told, never left with silence.
const w1Desc = (el) =>
  el && el.attributes
    ? {
        tag: el.tagName.toLowerCase(),
        id: el.id || "",
        attrs: [...el.attributes].filter((a) => /^data-/.test(a.name) && !/^data-(sim|w1|sd|cr)/.test(a.name) && a.value.length < 120).map((a) => [a.name, a.value]),
        txt: w1Norm(el.innerText || el.getAttribute("aria-label") || "").slice(0, 80),
      }
    : null;
function w1Again(d) {
  if (!d || (!d.id && !(d.attrs || []).length && !d.txt)) return null;
  let sel = d.tag + (d.id ? "#" + CSS.escape(d.id) : "");
  (d.attrs || []).forEach(([n, v]) => (sel += `[${n}="${CSS.escape(v)}"]`));
  let C = [];
  try {
    C = [...document.querySelectorAll(sel)].filter((x) => x.getClientRects().length || x.closest("#mbm-held"));
  } catch (e) {}
  const txt = (x) => w1Norm(x.innerText || x.getAttribute("aria-label") || "").slice(0, 80);
  return C.find((x) => txt(x) === d.txt) || (1 === C.length && (d.id || (d.attrs || []).length) ? C[0] : null);
}
let w1AskD = null;
{
  const base = appConfirm;
  appConfirm = function () {
    try {
      "undefined" != typeof askEl && askEl && (w1AskD = w1Desc(askEl));
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
{
  const base = appPrompt;
  appPrompt = function () {
    try {
      "undefined" != typeof askEl && askEl && (w1AskD = w1Desc(askEl));
    } catch (e) {}
    return base.apply(this, arguments);
  };
}
{
  const base = askReplay;
  askReplay = function (msg, val) {
    try {
      if (askEl && !askEl.isConnected) {
        const d = w1AskD,
          again = w1Again(d);
        again ? (askEl = again) : setTimeout(() => toast(`That step did not go through: the screen changed under the question. Tap ${d && d.txt ? `“${d.txt}”` : "it"} again`), 30);
      }
    } catch (e) {}
    return base.apply(this, arguments);
  };
}

// ---- D4: saves that said nothing ---------------------------------------------------------------------------------------
// Pilot 2: Save Changes on a payroll run saved with no toast (the controller), Re-Read on a meeting changed nothing and
// said nothing (the owner), Add Line added a line in silence. Each now says what happened, with Open where there is a
// record to open.
let w1ToastN = 0;
{
  const base = toast;
  toast = function () {
    w1ToastN++;
    return base.apply(this, arguments);
  };
}
if ("function" == typeof savePayroll) {
  const base = savePayroll;
  savePayroll = function () {
    const id = "undefined" != typeof editing && editing ? editing.id : null,
      n0 = w1ToastN,
      r = base.apply(this, arguments);
    try {
      const run = id ? (DB.payroll || []).find((x) => x.id === id) : (DB.payroll || [])[(DB.payroll || []).length - 1];
      !document.querySelector("#drawer.on") && w1ToastN === n0 && run && toast(`Payroll ${run.period || ""} saved`.replace(/\s+saved/, " saved"), { label: "Open", run: () => openPayroll(run.id) });
    } catch (e) {}
    return r;
  };
}
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest && e.target.closest("#mt-redo");
    if (!b) return;
    let m = null;
    try {
      m = (DB.meetings || []).find((x) => "undefined" != typeof mtOpen && x.id === mtOpen) || null;
    } catch (x) {}
    const n0 = m ? (m.proposals || []).length : -1;
    setTimeout(() => {
      try {
        const m2 = m || null,
          n1 = m2 ? (m2.proposals || []).length : -1,
          waiting = m2 ? (m2.proposals || []).filter((x) => "proposed" === x.status).length : 0;
        toast(n1 > n0 ? `Read the notes again: ${n1 - n0} new to review, ${waiting} waiting` : `Read the notes again: nothing new${waiting ? `, ${waiting} still waiting for you` : ""}`);
      } catch (x) {}
    }, 60);
  },
  !0,
);

// ---- D2: Route's Clock In clocks in where the driver is ----------------------------------------------------------------
// Pilot 2, the driver: Clock In on Route dropped him on the Clock page; he wanted to stay on Route. It clocks in (or
// out, which opens the hours sheet) and the Route stays.
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      const b = document.getElementById("fm-rclock");
      if (b && !b.dataset.w1) {
        b.dataset.w1 = "1";
        const emp = "function" == typeof myEmp ? myEmp() : null,
          open = emp && (DB.time || []).find((t) => t.empId === emp.id && !t.out);
        b.textContent = open ? `Clock Out · In Since ${stampTime(open.in)}` : "Clock In";
        b.onclick = async () => {
          try {
            await clockEvent(open ? "out" : "in");
          } catch (x) {
            console.warn("clock", x);
          }
        };
      }
    } catch (e) {}
    return r;
  };
}

(() => {
  const css = `
.w1-dr{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 10px;padding:8px 10px;border-radius:8px;background:var(--amber-bg, #fff7e0);color:var(--ink, #222);font-size:13.5px;line-height:1.35}
.w1-dr .grow{flex:1 1 180px;min-width:0}
.w1-dr .btn{min-height:36px}
.w1-typed{outline:2px solid var(--amber, #d89b00);outline-offset:1px}
@media (max-width: 819px){.w1-dr .btn{min-height:44px}}
`;
  const st = document.createElement("style");
  (st.id = "w1-css"), (st.textContent = css), document.head.appendChild(st);
})();
