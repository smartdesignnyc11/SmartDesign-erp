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
