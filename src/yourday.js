/* =====================================================================================================================
   Your Day: Today, Tasks and Messages (Alan, 11-03 night: "do the same thing for every menu and sub menu page";
   docs/mockups/today/SPEC.md, its chief of staff review and must-fix list; BACKLOG section 10 items 6 and 7).
   The shared kit for this lane's three groups rides here too (src/salespages.js and src/companypages.js use it).

   What was wrong. Today read All 34 / Late 6 / Approvals 22 while the rail said 6; the owner's Approvals held 22
   rows, lessons and rule changes among them, and missed AMP-311 ($9,800, no PO); Messages opened on an empty job
   thread and counted 1 message waiting on the owner while 5 did (two clients past the 2-hour acknowledgement); the
   Inbox, Meetings and Calendar were pages of their own; Tasks opened on My Week 12 while the person page said 15.

   The structure (three pages, three chips each):
     Today     the brief (Safe to Spend from safeToSpend() with its parts folded, the job slipping, the client
               waiting), then Approvals, then Now; chips Today, Approvals, Coming Up; Where the Firm Stands one tap.
               One number: the menu, the phone bar, the date line, the Today chip and the rows (approvals + now).
               The owner's Approvals is the 10-26 exceptions only (paid before approval, over the PO or with none, a
               bank-detail change, a first payment to a new vendor, a PO over $10,000, payroll, a charge made twice);
               lessons and rule changes go to The Brain; other approvals stay on their owner's Today.
               Today is the union of what waits on the person: every message Messages counts, every late or today
               task, every deal the Pipeline says needs them (BACKLOG 10.7).
     Tasks     one list: Mine, Waiting On, Team (grouped by person, no load figures; load lives on Team); List,
               Table, Board and Calendar as one switch, the desktop on Table; the old Calendar is the Calendar view.
     Messages  one list of mail, texts, calls, team chats and meeting notes: Needs an Answer (oldest first), All,
               Meetings. Needs an Answer is one rule (ydMsgNeeds): every message to you, or routed to you, with a
               question or a request and no reply after it; a call the answering service could not put through
               counts. The menu's Messages number is that list.
   Old pages forward (the render wrapper below): Approvals to Today's Approvals chip, the Inbox's list to Needs an
   Answer, Meetings' list to the Meetings chip, the Calendar to Tasks' Calendar view. A message or meeting opened from
   the list keeps its reader (cmOpen, mtOpen).

   Design gate (BACKLOG 1.16). No new store, list or queue: Today stays tdyModel() and td2Rows(); Approvals is that
   queue filtered to the exceptions; Messages reads DB.comms through cmNeedsAnswer, the team threads and DB.meetings;
   Tasks keeps tkAll(). Nothing here posts money.
   ===================================================================================================================== */

// ---- the kit: one look for the lane's pages (drawn by this script so the shared stylesheet is not touched) ----------
const YD_CSS = `
.yd-host{max-width:1180px}
.view.yd-own > :not(.yd-host):not(script){display:none !important}
.yd-ph{display:flex;align-items:flex-start;gap:12px;margin:0 0 12px}
.yd-ph h2{font-size:20px;line-height:1.2}
.yd-ph .yd-sub{color:var(--ink-3);font-size:13px;margin-top:2px}
.yd-ph .grow{flex:1}
.yd-chips{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}
.yd-chip{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border:1px solid #c9d1e0;border-radius:22px;background:#fff;font-weight:600;font-size:13.5px}
.yd-chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.yd-chip .n{font-size:12px;font-weight:700;color:var(--bad)}
.yd-chip.on .n{color:#fff}
.yd-chip .n:empty{display:none}
.yd-card{background:#fff;border:1px solid var(--rule);border-radius:10px;margin:0 0 14px;overflow:hidden}
.yd-card > h3,.yd-sh{display:flex;align-items:baseline;gap:8px;padding:12px 16px 6px;font-size:14px;margin:0}
.yd-sh .n{color:var(--ink-3);font-weight:600}
.yd-sh .note{color:var(--ink-3);font-weight:400;font-size:12px}
.yd-row{display:flex;align-items:center;gap:12px;padding:10px 16px;border-top:1px solid var(--rule-2);min-height:56px;cursor:pointer}
.yd-row:first-of-type{border-top:0}
.yd-row .yd-t{flex:1;min-width:0}
.yd-row .yd-t b{display:block;font-size:14px;font-weight:600;overflow-wrap:anywhere}
.yd-row .yd-t span{display:block;color:var(--ink-3);font-size:12.5px;overflow-wrap:anywhere}
.yd-row .yd-when{font-size:12px;font-weight:600;color:var(--ink-3);white-space:nowrap}
.yd-row .yd-when.late{color:var(--bad)}
.yd-row .yd-amt{font-weight:600;white-space:nowrap;font-variant-numeric:tabular-nums}
.yd-row .btn{min-height:44px;white-space:nowrap}
.yd-row.sel{background:var(--accent-2)}
.yd-empty{padding:14px 16px;color:var(--ink-3)}
.yd-fold{display:flex;align-items:center;gap:8px;width:100%;min-height:48px;padding:0 16px;border:1px solid var(--rule);border-radius:10px;background:#fff;font-weight:600;font-size:14px;margin:0 0 14px;text-align:left}
.yd-fold .grow{flex:1}
.yd-fold svg{transition:transform .15s}
.yd-fold[aria-expanded="true"]{border-radius:10px 10px 0 0;margin:0}
.yd-fold[aria-expanded="true"] svg{transform:rotate(180deg)}
.yd-fold[aria-expanded="true"] + .yd-card{border-top:0;border-radius:0 0 10px 10px}
.yd-kv{display:flex;align-items:baseline;gap:12px;padding:9px 16px;border-top:1px solid var(--rule-2)}
.yd-kv:first-child{border-top:0}
.yd-kv span{flex:1;color:var(--ink-2)}
.yd-kv span i{display:block;font-style:normal;color:var(--ink-3);font-size:12px}
.yd-kv b{font-variant-numeric:tabular-nums;white-space:nowrap}
.yd-kv b.bad{color:var(--bad)}
.yd-tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:0 0 14px}
.yd-tile{background:#fff;border:1px solid var(--rule);border-radius:10px;padding:12px 14px;text-align:left;min-height:72px}
.yd-tile span{display:block;color:var(--ink-3);font-size:12px;font-weight:600}
.yd-tile b{display:block;font-size:22px;font-variant-numeric:tabular-nums;margin-top:2px}
.yd-tile i{display:block;font-style:normal;color:var(--ink-3);font-size:12px}
.yd-tile.bad b{color:var(--bad)}
.yd-tabs{display:flex;gap:4px;border-bottom:1px solid var(--rule);margin:0 0 14px}
.yd-tab{min-height:44px;padding:0 14px;border:0;border-bottom:2px solid transparent;background:none;font-weight:600;color:var(--ink-3)}
.yd-tab.on{color:var(--ink);border-bottom-color:var(--accent)}
.yd-two{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:16px;align-items:start}
.yd-plus{position:relative}
.yd-plusb{min-width:44px;min-height:44px;border-radius:22px;display:inline-flex;align-items:center;justify-content:center;gap:6px}
.yd-menu{position:absolute;right:0;top:48px;z-index:30;background:#fff;border:1px solid var(--rule);border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.12);min-width:240px;padding:6px}
.yd-menu .yd-mh{display:block;padding:8px 10px;color:var(--ink-3);font-size:12px;font-weight:600}
.yd-menu button{display:block;width:100%;text-align:left;min-height:44px;padding:0 10px;border:0;background:none;border-radius:6px;font-size:14px}
.yd-menu button:hover{background:var(--paper-3)}
.yd-msg{padding:16px}
.yd-msg pre{white-space:pre-wrap;font:inherit;margin:10px 0}
.yd-draft{width:100%;min-height:96px;border:1px solid var(--rule);border-radius:8px;padding:10px;margin:10px 0 6px}
.yd-cash{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:2px 0 6px}
.yd-cash b{font-size:20px;font-variant-numeric:tabular-nums}
.yd-cash b.bad{color:var(--bad)}
.yd-cash .yd-cashb{min-height:44px;border:0;background:none;color:var(--accent);font-weight:600;padding:0 4px}
.yd-cashp{margin:0 0 8px;border:1px solid var(--rule-2);border-radius:8px;background:#fff}
.yd-team{margin:0 0 14px}
.yd-team .yd-gh{display:flex;align-items:center;gap:8px;padding:12px 16px 4px;font-weight:700;font-size:14px}
.yd-foot{padding:12px 16px;color:var(--ink-3);font-size:12.5px}
.yd-back{display:inline-flex;align-items:center;gap:6px;min-height:44px;border:0;background:none;color:var(--accent);font-weight:600;padding:0}
@media (max-width:760px){
  .view.on .yd-chip,.view.on .yd-fold,.view.on .yd-cashb,.view.on .yd-row .btn,.view.on .yd-tab,.view.on .yd-back,.view.on .yd-plusb,.yd-menu button,.view.on .yd-tile,.view.on .yd-host .par-seg button{min-height:44px !important}
  .yd-ph h2{font-size:18px}
  .yd-tiles{grid-template-columns:repeat(2,minmax(0,1fr))}
  .yd-two{grid-template-columns:1fr}
  .yd-row{flex-wrap:wrap;padding:10px 12px}
  .yd-row .yd-t{flex:1 1 60%}
  .yd-row .btn{margin-left:auto}
  .yd-chips{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}
  .yd-chip{flex:none}
  .yd-tabs{overflow-x:auto;scrollbar-width:none}
  .yd-tab{flex:none}
  .yd-menu{position:fixed;left:12px;right:12px;top:auto;bottom:12px}
}`;
(function ydStyle() {
  try {
    if (document.getElementById("yd-css")) return;
    const s = document.createElement("style");
    (s.id = "yd-css"), (s.textContent = YD_CSS), document.head.appendChild(s);
  } catch (e) {}
})();
const YD_IC = {
  down: '<path d="M6 9l6 6 6-6"/>',
  back: '<path d="M15 18l-6-6 6-6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  next: '<path d="M9 6l6 6-6 6"/>',
};
const ydSvg = (k, n) => `<svg viewBox="0 0 24 24" width="${n || 18}" height="${n || 18}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${YD_IC[k] || ""}</svg>`;
const ydPhone = () => ("function" == typeof mOn ? mOn() : innerWidth <= 760);
const ydMay = (v) => (ROLE_VIEWS[role()] || []).includes(v);
const ydMoney0 = (v) => (+v < 0 ? "−" : "") + money(Math.abs(Math.round(+v || 0))).replace(/\.00$/, "");
const ydPlural = (n, one, many) => `${n} ${1 === n ? one : many || one + "s"}`;
// how long a message has waited, in days ("Today" for one that came in today)
const ydAge = (at) => {
  const d = String(at || "").slice(0, 10),
    n = d ? dayDiff(d, today()) : 0;
  return n > 0 ? ydPlural(n, "day") : "Today";
};
const ydWhen = (d) => {
  if (!d) return "";
  const n = dayDiff(today(), String(d).slice(0, 10));
  return 0 === n ? "Today" : 1 === n ? "Tomorrow" : -1 === n ? "Yesterday" : n < 0 ? `${-n} days ago` : n <= 6 ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][parse(String(d).slice(0, 10)).getDay()] : fmt(String(d).slice(0, 10));
};
// a chip row: defs [{k, label, n}]; the one on carries .on; data-ydchip names it
function ydChipsHtml(defs, on, group) {
  return `<div class="yd-chips" role="group" aria-label="Show"${group ? ` data-ydchips="${esc(group)}"` : ""}>${defs
    .map((d) => `<button type="button" class="yd-chip${d.k === on ? " on" : ""}" data-ydchip="${esc(d.k)}" aria-pressed="${d.k === on}">${esc(d.label)}<span class="n">${null == d.n || "" === d.n ? "" : esc(String(d.n))}</span></button>`)
    .join("")}</div>`;
}
// a row: {id, sec, title, meta, when, late, amt, act, primary, n}
function ydRowHtml(r) {
  return `<div class="yd-row${r.sel ? " sel" : ""}" data-ydrow="${esc(r.id)}"${r.sec ? ` data-sec="${esc(r.sec)}"` : ""}${null != r.n ? ` data-n="${esc(String(r.n))}"` : ""}${r.at ? ` data-at="${esc(r.at)}"` : ""} role="button" tabindex="0"><span class="yd-t"><b>${esc(r.title)}</b>${r.meta ? `<span>${esc(r.meta)}</span>` : ""}</span>${r.amt ? `<span class="yd-amt">${esc(r.amt)}</span>` : ""}${r.when ? `<span class="yd-when${r.late ? " late" : ""}">${esc(r.when)}</span>` : ""}${r.act ? `<button type="button" class="btn${r.primary ? " primary" : ""}" data-ydact="${esc(r.id)}">${esc(r.act)}</button>` : ""}</div>`;
}
function ydSectionHtml(title, n, note, rows, empty) {
  return `<section class="yd-card"><div class="yd-sh"><h3>${esc(title)}</h3>${null != n ? `<span class="n">${n}</span>` : ""}${note ? `<span class="note">${esc(note)}</span>` : ""}</div>${rows.length ? rows.map(ydRowHtml).join("") : `<div class="yd-empty">${esc(empty || "Nothing here.")}</div>`}</section>`;
}
function ydFoldHtml(k, label, open, body, n) {
  return `<button type="button" class="yd-fold" data-ydfold="${esc(k)}" aria-expanded="${!!open}"><span class="grow">${esc(label)}</span>${null != n ? `<span class="muted">${esc(String(n))}</span>` : ""}${ydSvg("down")}</button>${open ? `<section class="yd-card">${body}</section>` : ""}`;
}
const ydKv = (k, v, sub, bad) => `<div class="yd-kv"><span>${esc(k)}${sub ? `<i>${esc(sub)}</i>` : ""}</span><b class="${bad ? "bad" : ""}">${esc(v)}</b></div>`;
// The lane's pages take the view's section: a host first in it, the old content hidden behind it (never removed, so
// every older renderer still finds its elements)
function ydHost(v, on) {
  const s = document.getElementById("v-" + v);
  if (!s) return null;
  let h = s.querySelector(":scope > .yd-host");
  if (!on) {
    s.classList.remove("yd-own");
    h && (h.hidden = !0);
    return null;
  }
  h || ((h = document.createElement("div")), (h.className = "yd-host"), (h.id = "yd-" + v), s.prepend(h));
  (h.hidden = !1), s.classList.add("yd-own");
  return h;
}
// a section of its own for a page the lane adds (the deal, the hub, Company Settings)
function ydSection(v) {
  let s = document.getElementById("v-" + v);
  if (s) return s;
  const any = document.getElementById("v-jbill") || document.querySelector("section.view");
  if (!any || !any.parentNode) return null;
  s = document.createElement("section");
  (s.className = "view"), (s.id = "v-" + v);
  any.parentNode.insertBefore(s, any);
  return s;
}
// row actions are kept per draw: [data-ydact] and a row tap run the row's action
let ydActs = {};
const ydAct = (id, f) => ((ydActs[id] = f), id);
const ydOffice = (r) => {
  r = r || role();
  return "object" == typeof MENU && MENU[r] && !MENU[r].field && "client" !== r;
};

// ---- Messages: one rule for what waits on you -------------------------------------------------------------------
// A request asks for an answer as plainly as a question does ("They also need a COI", "Let's plan to meet at 1:30").
const YD_ASK_RX = /\b(?:need|needs|needed)\b[^.]{0,60}\b(?:from (?:you|the contractor)|a coi|scope|before|by)\b|\blooking forward to (?:receiving|hearing|your)\b|\blet'?s (?:plan|meet|schedule|set up|talk)\b|\bplease\b/i;
// an answering-service call that was not put through waits for a call back
const ydCallBack = (c) => "call" === c.channel && /not transferred|call ?back|please call|returning your call/i.test(String(c.text || ""));
function ydMsgAsks(c) {
  const t = `${c.subject || ""} ${"function" == typeof cmOwnText ? cmOwnText(c.text || "") : c.text || ""}`;
  return ("object" == typeof CM_QUESTION_RX && CM_QUESTION_RX.test(t)) || YD_ASK_RX.test(t) || ydCallBack(c);
}
const ydMailOf = (u) => String((u && u.email) || "").toLowerCase();
const ydAddrs = (c) => [].concat(c.to || [], c.cc || []).map((x) => String((x && x.email) || x || "").toLowerCase());
// The person a message waits on. Client and job mail goes to the job's PM first and reaches the owner as an exception
// once the 2-hour acknowledgement is missed (DECISIONS 11-03); mail to a person with no login goes to the owner (there
// is no job PM on file in the demo); a staff member's question waits on the person it is addressed to.
function ydMsgOwners(c) {
  const users = (DB.users || []).filter((u) => u.email && !/^(client|mb_)/.test(u.role)),
    by = (e) => users.find((u) => ydMailOf(u) === e),
    to = ydAddrs(c),
    owner = (DB.users || []).find((u) => "owner" === u.role),
    out = new Set();
  to.forEach((e) => {
    const u = by(e);
    u && out.add(u.id);
  });
  const R = c.route || {},
    pid = R.projectId || c.projectId || "",
    p = pid && (DB.projects || []).find((x) => x.id === pid),
    pmName = p && p.project && p.project.pm,
    pm = pmName ? (DB.users || []).find((u) => u.name === pmName) : (DB.users || []).find((u) => "pm" === u.role);
  pid && pm && out.add(pm.id);
  // nobody with a login was addressed (Jeanette, the firm's number): the owner
  ![...out].some((id) => id !== (pm && pm.id)) && owner && out.add(owner.id);
  // past the 2-hour acknowledgement every client or job message reaches the owner too
  owner && (pid || R.clientId || R.contact || R.leadName) && out.add(owner.id);
  return out;
}
// Ours: what the person or the firm sent. A colleague's question to the person is a question like any other.
function ydMsgOurs(c, me) {
  const from = String((c.from || {}).email || "").toLowerCase(),
    mine = ydMailOf(me);
  if ((c.labels || []).includes("SENT") || (c.labels || []).includes("DRAFT")) return !0;
  if (mine && from === mine) return !0;
  const staff = "function" == typeof cmIsStaff ? cmIsStaff(from) : /@smartdesign\.nyc$/.test(from);
  if (staff || "out" === c.direction) {
    // a colleague writing to the person: not ours, it waits on them
    if (mine && ydAddrs(c).includes(mine) && from !== mine) return !1;
    if (!mine && "owner" === me.role && ydAddrs(c).some((e) => /^alan@/.test(e))) return !1;
    return !0;
  }
  return !1;
}
// cmNeedsAnswer, the one rule (Messages' Needs an Answer, the menu's Messages number, Today's message rows, Ask):
// the last message in each thread that is not ours, after our last reply, from a person (not a bot, a bank or an
// automated sender), with a question or a request, waiting on the person signed in.
cmNeedsAnswer = function () {
  const me = ("function" == typeof paMe ? paMe() : null) || currentUser() || {},
    L = (DB.comms || []).filter((c) => (!c.owner || c.owner === me.id) && "ignored" !== c.status),
    byThread = {};
  L.forEach((c) => {
    const k = c.threadId || c.id;
    (byThread[k] = byThread[k] || []).push(c);
  });
  return Object.values(byThread)
    .map((T) => {
      T.sort((a, b) => String(a.date || "").localeCompare(String(b.date || "")));
      const lastOurs = T.filter((c) => ydMsgOurs(c, me)).map((c) => String(c.date || "")).sort().pop() || "",
        asks = T.filter(
          (c) =>
            !ydMsgOurs(c, me) &&
            String(c.date || "") > lastOurs &&
            !(c.route || {}).bot &&
            // an answering service relays a person: the caller waits, whatever address the service writes from
            (("call" === c.channel && ydCallBack(c)) ||
              (!("function" == typeof cmBankSender && cmBankSender(c)) && !("object" == typeof PA_AUTOMATED && PA_AUTOMATED.test(String((c.from || {}).email || "").toLowerCase())))) &&
            !(c.proposals || []).every((p) => p.applied) &&
            ydMsgAsks(c) &&
            (!me.id || ydMsgOwners(c).has(me.id)),
        );
      return asks[asks.length - 1] || null;
    })
    .filter(Boolean)
    .sort((a, b) => (b.date || "").localeCompare(a.date || ""));
};
// Needs an Answer for the person: the messages above and the team lines addressed to them (p2nav's direct lines and
// @mentions), each once. Oldest first: the one waiting longest is on top.
function ydMsgNeeds() {
  let mail = [],
    chat = [];
  try {
    mail = ydMay("comms") || ydMay("chat") ? cmNeedsAnswer() : [];
  } catch (e) {}
  try {
    chat = "function" == typeof p2nChatItems ? p2nChatItems() : [];
  } catch (e) {}
  // a question from the site waiting on the person (Approvals' Site Questions) is a question like any other
  let site = [];
  try {
    site = ydOffice() && PRED.siteQuestionsMine ? PRED.siteQuestionsMine.rows() : [];
  } catch (e) {}
  const raiseAt = (it) => {
    const r = (((DB.field || {}).raises) || []).find((x) => x.id === it.id);
    return String((r && r.at) || "");
  };
  const out = mail
    .map((c) => ({ kind: "tdyMail", id: c.id, c: c, at: String(c.date || "") }))
    .concat(chat.map((it) => ({ kind: it.kind, id: it.id, it: it, at: String(it.at || it.due || (it.m && it.m.at) || "") })))
    .concat(site.map((it) => ({ kind: "raise", id: it.id, it: it, at: raiseAt(it) })));
  return out.sort((a, b) => a.at.localeCompare(b.at));
}
// the menu's Messages number, the Needs an Answer chip and its rows: one list
{
  const base = "function" == typeof p2nMsgN ? p2nMsgN : null;
  p2nMsgN = function () {
    const out = base ? base.apply(this, arguments) : { team: 0, mail: 0, field: 0, n: 0 };
    try {
      if (ydOffice()) out.n = ydMsgNeeds().length;
    } catch (e) {}
    return out;
  };
}
// who wrote, in a line: "R. Torres, Halstead Management" from the answering service's text, else the sender
function ydMsgWho(c) {
  if ("call" === c.channel) {
    const m = /Caller'?s Full Name\s*:\s*([^\n]+?)\s+Phone/i.exec(String(c.text || ""));
    if (m) return m[1].trim();
  }
  const R = c.route || {};
  return (c.from && c.from.name) || R.contact || R.leadName || (c.from && c.from.email) || "Someone";
}
function ydMsgWhere(c) {
  const R = c.route || {},
    p = R.projectId && (DB.projects || []).find((x) => x.id === R.projectId),
    cl = R.clientId && (DB.clients || []).find((x) => x.id === R.clientId);
  return (p && ("function" == typeof shortName ? shortName(p) : p.project.name)) || (cl && cl.name) || R.existingJob || R.addr || "";
}
// what a message is about, in a line: a call's "Regarding", else the subject
function ydMsgAbout(c) {
  if ("call" === c.channel) {
    const m = /Regarding\s*:\s*([^\n]+?)(?:\s+Transfer Result|$)/i.exec(String(c.text || ""));
    if (m) return tdWords(m[1].replace(/^\w+ is calling about /i, "").trim(), 12);
    return "called";
  }
  return c.subject || "a message";
}
const ydMsgKind = (c) => ("call" === c.channel ? "Call" : "sms" === c.channel ? "Text" : "Mail");
function ydMsgOpen(c) {
  try {
    "function" == typeof cmInit && cmInit();
  } catch (e) {}
  (cmOpen = c.id), (ydMsgKeep = !0), setView("comms"), window.scrollTo(0, 0);
}
let ydCalKeep = !1,
  ydMsg = { chip: "need", sel: "", thread: !1 },
  ydMsgKeep = !1;
function ydMsgRows(chip) {
  const td = today();
  if ("need" === chip)
    return ydMsgNeeds().map((x) => {
      if (x.c) {
        const c = x.c,
          d = String(c.date || "").slice(0, 10),
          age = d ? dayDiff(d, td) : 0;
        return { id: c.id, at: x.at, title: `${ydMsgWho(c)}: ${ydMsgAbout(c)}`, meta: [ydMsgKind(c), ydMsgWhere(c)].filter(Boolean).join(" · "), when: ydAge(c.date), late: !0, act: "call" === c.channel ? "Call Back" : "Reply", run: () => ydMsgOpen(c), c: c };
      }
      const it = x.it;
      if ("raise" === x.kind) {
        let c = null;
        try {
          c = tdCard(it);
        } catch (e) {}
        return { id: String(x.id), at: x.at, title: tdPlain((c && td2Txt(c.line1)) || it.title || "A question from the site"), meta: `From the site \u00b7 ${tdPlain((c && td2Txt(c.why)) || it.detail || "")}`, when: ydWhen(x.at), late: !0, act: "Answer", run: () => (c ? c.run() : mGo(it.open)) };
      }
      return { id: String(x.id), at: x.at, title: tdPlain(it.title || "A message"), meta: tdPlain(it.detail || "Team"), when: ydWhen(x.at), late: !0, act: "Reply", run: () => (it.open ? mGo(it.open) : setView("chat")) };
    });
  if ("meet" === chip)
    return (DB.meetings || [])
      .slice()
      .sort((a, b) => String(b.date || "").localeCompare(String(a.date || "")))
      .map((m) => {
        const p = (DB.projects || []).find((x) => x.id === m.projectId),
          open = (m.proposals || []).filter((x) => !x.applied && !x.skipped).length;
        return { id: m.id, at: String(m.date || ""), title: `Notes: ${m.title}`, meta: [p ? shortName(p) : "", open ? `${open} next steps to review` : "reviewed"].filter(Boolean).join(" · "), when: ydWhen(m.date), act: "Open", run: () => ((mtTab = "meetings"), (mtOpen = m.id), (ydMsgKeep = !0), setView("meetings")) };
      });
  // All: every conversation, newest first: mail, texts, calls, meeting notes, and the team threads that hold a message
  const me = currentUser() || {},
    mail = (DB.comms || [])
      .filter((c) => (!c.owner || c.owner === me.id) && "ignored" !== c.status)
      .map((c) => ({ id: c.id, at: String(c.date || ""), title: `${ydMsgWho(c)}: ${ydMsgAbout(c)}`, meta: [ydMsgKind(c), ydMsgWhere(c)].filter(Boolean).join(" · "), when: ydWhen(c.date), act: "Open", run: () => ydMsgOpen(c), c: c }));
  let threads = [];
  try {
    threads = msgThreadsFor(msgMe(), !0)
      .filter((T) => T.all().length)
      .map((T) => {
        const L = T.all(),
          last = L[L.length - 1] || {};
        return { id: "th:" + T.key, at: String(last.at || ""), title: T.name || T.title || "Team", meta: `${last.by || ""}: ${tdWords(String(last.text || ""), 10)}`, when: ydWhen(last.at), act: "Open", run: () => ((ydMsg.thread = !0), msgOpen(T.key)) };
      });
  } catch (e) {}
  return mail.concat(threads).sort((a, b) => b.at.localeCompare(a.at));
}
function ydMsgPane(r) {
  if (!r) return '<section class="yd-card"><div class="yd-empty">Pick a conversation.</div></section>';
  const c = r.c;
  if (!c) return `<section class="yd-card yd-msg"><h3>${esc(r.title)}</h3><p class="muted">${esc(r.meta)}</p><div style="margin-top:12px"><button type="button" class="btn primary" data-ydact="${esc(r.id)}">${esc(r.act)}</button></div></section>`;
  const text = "function" == typeof cmOwnText ? cmOwnText(c.text || "") : c.text || "",
    who = ydMsgWho(c),
    first = String(who).split(/[\s,]+/)[0];
  let draft = "";
  try {
    const A = (DB.asst || {})[(currentUser() || {}).id] || {},
      d = (A.drafts || {})[c.id];
    draft = (d && d.text) || "";
  } catch (e) {}
  draft = draft || (/^call$/.test(c.channel) ? "" : `Hi ${first},\n\nThank you. I am on it and will come back to you today with an answer.\n\n`);
  return `<section class="yd-card yd-msg"><h3>${esc(c.subject || (c.channel === "call" ? "A call" : "A message"))}</h3><p class="muted small">${esc([ydMsgKind(c), who, ydMsgWhere(c), c.date ? fmt(String(c.date).slice(0, 10)) : ""].filter(Boolean).join(" · "))}</p><pre>${esc(tdWords(text, 120))}</pre>${
    "call" === c.channel
      ? `<button type="button" class="btn primary" data-ydact="${esc(r.id)}">Call Back</button>`
      : `<label class="small muted" for="yd-draft">Your reply, drafted by your assistant: nothing is sent until you press Send</label><textarea class="yd-draft" id="yd-draft">${esc(draft)}</textarea><div class="row"><button type="button" class="btn primary" data-ydact="${esc(r.id)}">Reply</button><button type="button" class="btn" data-ydopenmsg="${esc(c.id)}">Open the Message</button></div>`
  }</section>`;
}
function ydMsgRender() {
  const on = "chat" === view && ydOffice() && !ydMsg.thread;
  const h = ydHost("chat", on);
  if (!on || !h) return;
  const phone = ydPhone(),
    rows = ydMsgRows(ydMsg.chip),
    needN = ydMsgNeeds().length;
  ydActs = {};
  rows.forEach((r) => ydAct(r.id, r.run));
  const sel = phone ? null : rows.find((r) => r.id === ydMsg.sel) || rows[0];
  const list = rows.length
    ? rows.map((r) => Object.assign({}, r, { sec: ydMsg.chip, primary: !1, sel: sel && r.id === sel.id })).map((r) => ydRowHtml(r).replace('data-ydrow="', 'data-ydmrow="' + esc(r.id) + '" data-ydrow="')).join("")
    : `<div class="yd-empty">${"need" === ydMsg.chip ? "Nobody is waiting on an answer from you." : "Nothing here yet."}</div>`;
  const chips = ydChipsHtml(
    [
      { k: "need", label: "Needs an Answer", n: needN || "" },
      { k: "all", label: "All", n: "" },
      { k: "meet", label: "Meetings", n: "" },
    ],
    ydMsg.chip,
    "msgs",
  );
  const head = `<div class="yd-ph"><div class="grow"><h2>Messages</h2><div class="yd-sub">${needN ? `${ydPlural(needN, "person waits", "people wait")} on an answer from you, the longest first` : "Nobody waits on an answer from you"}</div></div><button type="button" class="btn" data-ydnewmsg>New Message</button></div>`;
  h.innerHTML = phone
    ? `${head}${chips}<section class="yd-card">${list}</section>`
    : `${head}${chips}<div class="yd-two"><section class="yd-card">${list}</section><div>${ydMsgPane(sel)}</div></div>`;
}
// opening a conversation from the list, a notification or a link is the thread; the list is one tap back
if ("function" == typeof msgOpen) {
  const base = msgOpen;
  msgOpen = function () {
    ydMsg.thread = !0;
    return base.apply(this, arguments);
  };
}

// ---- Today ----------------------------------------------------------------------------------------------------------
const YD_TD_ROLES = ["owner", "pm", "coord", "billing", "controller"];
(function ydTodaySpec() {
  if ("object" != typeof TD2_SPEC) return;
  Object.assign(TD2_CHIP, { today: "Today", coming: "Coming Up" });
  Object.assign(TD2_SEC, { coming: "Coming Up" });
  YD_TD_ROLES.forEach((r) => TD2_SPEC[r] && Object.assign(TD2_SPEC[r], { chips: ["today", "appr", "coming"], secs: ["appr", "now", "coming"], rest: "coming" }));
  // Safe to Spend is the brief's own figure, with its parts: not a line of the update as well
  ["owner", "billing", "controller"].forEach((r) => TD2_FACTS[r] && (TD2_FACTS[r] = TD2_FACTS[r].filter((k) => "cash" !== k)));
})();
// The 10-26 exceptions (DECISIONS 10-26 decision 3; 11-03: a bill with no PO counts as over the PO, a charge made
// twice as paid before approval). Each reason in the words the row prints.
function ydBillExc(b) {
  const why = [];
  try {
    "function" == typeof billPaidUnapproved && billPaidUnapproved(b) && why.push("paid before approval");
    b.poId ? "function" == typeof billOverPO && billOverPO(b) && why.push("over its PO") : why.push("no PO behind it");
    b.bankChanged && why.push("the vendor's bank details changed");
    const v = (DB.vendors || []).find((x) => x.name === b.vendor);
    v && v.newVendor && why.push("a first payment to a new vendor");
    if (!b.poId) {
      const t = ydUnmatchedPay(b);
      t && why.push(`a ${money(Math.abs(+t.amt || 0))} ${t.acctName || "bank"} payment on ${fmt(t.date)} is matched to nothing`);
    }
  } catch (e) {}
  return why;
}
// a bank or card line of the bill's amount with nothing matched to it (the payment that may be this bill)
function ydUnmatchedPay(b) {
  const amt = Math.round(100 * ("function" == typeof billTotal ? billTotal(b) : 0));
  if (!amt) return null;
  const t = (DB.txns || []).find((x) => Math.round(-100 * (+x.amt || 0)) === amt && !x.billId && !x.matchId && !(x.match && x.match.id) && !x.ignored);
  if (!t) return null;
  const a = (DB.accounts || []).find((x) => x.id === t.acctId || x.id === t.accountId);
  return Object.assign({}, t, { acctName: a ? String(a.name).split(" ")[0] : "" });
}
// a purchase order's total (poTotal returns its parts: sub, tax, shipping, total)
function ydPoAmt(po) {
  const t = "function" == typeof poTotal ? poTotal(po) : null;
  return +(t && "object" == typeof t ? t.total : t) || +po.total || 0;
}
const YD_BILL_DONE = ["approved", "paid", "void", "voided", "rejected", "scheduled", "deleted"];
// The owner's Approvals: the queue's rows that are exceptions, and the bills that are exceptions but sit in another
// person's queue or in none (AMP-311, submitted with no PO). Every other approval stays with its owner.
function ydOwnerExc(appr) {
  const out = [],
    seen = new Set();
  (appr || []).forEach((it) => {
    let why = null;
    if ("payroll" === it.kind) why = ["payroll is approved before pay day"];
    else if ("bill" === it.kind) {
      const b = (DB.bills || []).find((x) => x.id === it.id);
      const w = b ? ydBillExc(b) : [];
      w.length && (why = w);
      b && seen.add(b.id);
    } else if ("po" === it.kind) {
      const po = (DB.pos || []).find((x) => x.id === it.id);
      po && ydPoAmt(po) > 1e4 && (why = ["a purchase order over $10,000"]);
    } else if ("hand" === it.kind && /^std:unb:/.test(String(it.id))) why = ["a charge on no estimate or change-order line"];
    why && ((it.ydWhy = why), out.push(it));
  });
  (DB.bills || []).forEach((b) => {
    if (seen.has(b.id) || YD_BILL_DONE.includes(b.status) || !b.status) return;
    const why = ydBillExc(b);
    if (!why.length) return;
    out.push({ kind: "bill", id: b.id, title: `${b.vendor} · bill ${b.number}`, detail: why.join(" · "), open: { view: "ap" }, ydWhy: why, ydExtra: 1, who: "owner", due: b.date || "" });
  });
  return out;
}
const ydBrainKind = (it) => ["change", "lesson", "learn"].includes(it && it.kind);
// The one predicate (DECISIONS 10-26): does this waiting item need the owner? Every surface that counts approvals reads
// it through the queue itself (mApprovals below): Today's chip, Ask, PRED.waitingOnMe, the bar.
function ydIsExc(it) {
  if (!it) return !1;
  if ("payroll" === it.kind) return !0;
  if ("bill" === it.kind) {
    const b = (DB.bills || []).find((x) => x.id === it.id);
    return !!(b && ydBillExc(b).length);
  }
  if ("po" === it.kind) {
    const po = (DB.pos || []).find((x) => x.id === it.id);
    return !!(po && ydPoAmt(po) > 1e4);
  }
  return "hand" === it.kind && /^std:unb:/.test(String(it.id));
}
// money another person approves (a clean bill is the PM's, hours the PM's, a payment the controller's): never the
// owner's own to-do when it is not an exception
const YD_MONEY_KINDS = ["bill", "po", "payroll", "time", "pay"];
// The queue, delegated (mApprovals): the owner's approvals are the exceptions (and the bills that are exceptions
// wherever they sat, AMP-311 among them); everyone else's queue no longer holds an exception. The full queue, lessons
// and the owner's own to-dos included, is ydQueueBase: The Brain and Today read it for what is not an approval.
const ydQueueBase = mApprovals;
mApprovals = function (opts) {
  const R = ydQueueBase.apply(this, arguments);
  try {
    if (!Array.isArray(R)) return R;
    if (opts && opts.everyone) {
      R.forEach((it) => ydIsExc(it) && (it.who = "owner"));
      const have = new Set(R.filter((it) => "bill" === it.kind).map((it) => it.id));
      ydOwnerExc([])
        .filter((it) => !have.has(it.id))
        .forEach((it) => R.push(Object.assign(it, { who: "owner" })));
      return R;
    }
    if ("owner" === role()) return ydOwnerExc(R);
    return R.filter((it) => !ydIsExc(it));
  } catch (e) {
    return R;
  }
};
// Where each item of the owner's full queue is, for the check that nothing waiting is lost: on his Approvals, a row of
// his Today (or the task or message that stands for it), or in The Brain.
function ydOwnerPlaced() {
  if ("owner" !== role()) return { placed: [], lost: [] };
  const T = td2Model(),
    rows = T.rows.map((x) => x.it),
    keys = new Set(rows.map((it) => it.kind + ":" + it.id)),
    refs = new Set(rows.flatMap((it) => [].concat(it.t && it.t.refs ? it.t.refs : [], "tdyMail" === it.kind ? ["comm:" + it.id] : []))),
    mails = rows.filter((it) => "tdyMail" === it.kind).map((it) => String(((it.c || {}).from || {}).email || "").toLowerCase()).filter(Boolean),
    brain = new Set(ydBrainItems().flatMap((it) => [it].concat(it.also || [])).map((it) => it.kind + ":" + it.id)),
    placed = [],
    lost = [];
  ydQueueBase().forEach((it) => {
    const k = it.kind + ":" + it.id;
    let at = keys.has(k) ? "today" : brain.has(k) ? "brain" : "";
    if (!at)
      try {
        tdyApprRefs(it).some((r) => refs.has(r)) && (at = "today");
      } catch (e) {}
    !at && "hand" === it.kind && mails.some((e) => String(it.id).toLowerCase().includes(e)) && (at = "today");
    (at ? placed : lost).push(k + (at ? "@" + at : ""));
  });
  return { placed: placed, lost: lost };
}
// The deals the Pipeline says need the owner and that no task row on Today already stands for
function ydDealRows(M) {
  if ("function" != typeof slNeedYou || !["owner"].includes(role())) return [];
  const keys = new Set((M.all || []).filter((it) => "tdyTask" === it.kind).map((it) => it.id));
  return slNeedYou()
    .filter((x) => "signed" === x.why || !x.taskKeys.some((k) => keys.has(k)))
    .map((x) => ({ kind: "ydDeal", id: x.l.id, x: x, title: x.title, detail: x.meta, due: x.due || today() }));
}
// Every message Messages counts as the person's is a row on Today (BACKLOG 10.7). One an approval or a hold already
// stood for (an escalation, a calendar hold read from it) was hidden behind that item: the message is the row, and the
// reader shows what was proposed from it.
function ydMailRows(M) {
  if (!YD_TD_ROLES.includes(role())) return;
  let need = [];
  try {
    need = ydMsgNeeds().filter((x) => x.c);
  } catch (e) {}
  const have = new Set((M.all || []).filter((it) => "tdyMail" === it.kind).map((it) => it.id)),
    add = need.filter((x) => !have.has(x.id)).map((x) => tdyMailItem(x.c));
  if (!add.length) return;
  const ids = new Set(add.map((it) => "comm:" + it.id)),
    holds = (it) => {
      try {
        return tdyApprRefs(it).some((k) => ids.has(k)) || !!(it.nyh && ids.has("comm:" + it.nyh.commId));
      } catch (e) {
        return !1;
      }
    },
    gone = new Set((M.all || []).filter((it) => "tdyMail" !== it.kind && holds(it) && "bill" !== it.kind && "payroll" !== it.kind));
  M.inbox = (M.inbox || []).concat(add);
  M.appr = (M.appr || []).filter((it) => !gone.has(it));
  let all = (M.all || []).filter((it) => !gone.has(it)).concat(add);
  const mins = all.filter((it) => "tdyMinutes" === it.kind);
  all = all.filter((it) => "tdyMinutes" !== it.kind);
  try {
    all = standardOrder(all, stdQueueTie);
  } catch (e) {}
  M.all = all.concat(mins);
}
{
  const base = tdyModel;
  tdyModel = function () {
    const M = base.apply(this, arguments);
    try {
      ydMailRows(M);
    } catch (e) {
      console.warn("your day: message rows", e);
    }
    try {
      const r = role();
      if ("owner" === r) {
        const exc = ydOwnerExc(M.appr),
          mailFrom = new Set((M.inbox || []).filter((it) => "tdyMail" === it.kind).map((it) => String(((it.c || {}).from || {}).email || "").toLowerCase()).filter(Boolean)),
          // a calendar hold read from a mail is that mail's row (Samantha Field: Reply and Hold), not a second one
          dupHold = (it) => "hand" === it.kind && /^flmail:hold:/.test(String(it.id)) && [...mailFrom].some((e) => String(it.id).toLowerCase().includes(e)),
          // what is his own to do from the full queue (a renewal to file, a draft to send): Now rows, not approvals
          own = ydQueueBase().filter((it) => !ydIsExc(it) && !ydBrainKind(it) && !YD_MONEY_KINDS.includes(it.kind) && !dupHold(it)),
          ownRefs = new Set(own.flatMap((it) => {
            try {
              return tdyApprRefs(it);
            } catch (e) {
              return [];
            }
          })),
          // the renewal's task is that renewal: one row, the one that drafts it
          heldTask = (it) => "tdyTask" === it.kind && !!it.t && (it.t.refs || []).some((k) => ownRefs.has(k)),
          have = new Set((M.all || []).map((it) => it.kind + ":" + it.id));
        const all = (M.all || []).filter((it) => !ydBrainKind(it) && !dupHold(it) && !heldTask(it)),
          extra = exc.filter((it) => !have.has(it.kind + ":" + it.id)),
          mine = own.filter((it) => !have.has(it.kind + ":" + it.id)),
          deals = ydDealRows(M),
          mins = all.filter((it) => "tdyMinutes" === it.kind),
          rest = all.filter((it) => "tdyMinutes" !== it.kind).concat(extra, mine, deals);
        let ordered = rest;
        try {
          ordered = standardOrder(rest, stdQueueTie);
        } catch (e) {}
        M.appr = exc;
        M.tasks = (M.tasks || []).filter((it) => !heldTask(it));
        M.all = ordered.concat(mins);
      } else if ("controller" === r) {
        const have = new Set((M.all || []).filter((it) => "ydPay" === it.kind).map((it) => it.id)),
          pay = ydReadyToPay().filter((b) => !have.has(b.id)).map((b) => ({ kind: "ydPay", id: b.id, b: b, title: `${b.number} · ${b.vendor}`, detail: "approved, to pay", due: b.due || "" }));
        if (pay.length) {
          let all = (M.all || []).concat(pay);
          try {
            all = standardOrder(all, stdQueueTie);
          } catch (e) {}
          M.all = all;
        }
      } else if (YD_TD_ROLES.includes(r)) {
        // a bill that is an exception is the owner's to decide, in his queue only
        const isOwners = (it) => "bill" === it.kind && (() => {
          const b = (DB.bills || []).find((x) => x.id === it.id);
          return !!(b && ydBillExc(b).length);
        })();
        const gone = new Set((M.appr || []).filter(isOwners));
        gone.size && ((M.appr = M.appr.filter((it) => !gone.has(it))), (M.all = (M.all || []).filter((it) => !gone.has(it))));
      }
    } catch (e) {
      console.warn("your day: today's rows", e);
    }
    return M;
  };
}
// Approved and unpaid: the controller's Ready to Pay (the Bills page's To Pay)
function ydReadyToPay() {
  return (DB.bills || []).filter((b) => "approved" === b.status && !b.paidAt);
}
{
  const base = tdCard;
  tdCard = function (it) {
    if (it && "ydPay" === it.kind) {
      const b = it.b,
        last = (b.approvals || []).slice(-1)[0] || {},
        go = () => ("function" == typeof openBill ? openBill(b.id) : setView("ap"));
      return { line1: `<a href="#" data-tdrec>${esc(it.title)}</a>`, why: esc(["Ready to Pay", money(billTotal(b)), last.by ? `approved by ${last.by}${last.rule ? " under the exceptions rule" : ""}` : "", b.due ? `due ${fmt(b.due)}` : ""].filter(Boolean).join(" \u00b7 ")), verb: "Pay", go: go, run: go };
    }
    if (it && "ydDeal" === it.kind) {
      const x = it.x,
        go = () => slOpenDeal(x.l.id);
      return { line1: `<a href="#" data-tdrec>${esc(x.title)}</a>`, why: esc(x.meta), verb: x.act, go: go, run: () => x.run() };
    }
    const c = base.apply(this, arguments);
    try {
      if (it && "tdyMail" === it.kind && it.c) {
        const cc = it.c;
        c.line1 = `<a href="#" data-tdrec>${esc(tdWords(`${ydMsgWho(cc)}: ${ydMsgAbout(cc)}`, 12))}</a>`;
        c.why = esc([ydMsgKind(cc), ydMsgWhere(cc), cc.date ? `since ${fmt(String(cc.date).slice(0, 10))}` : ""].filter(Boolean).join(" · "));
        c.verb = "call" === cc.channel ? "Call Back" : (cc.proposals || []).some((p) => "hold" === p.kind && !p.applied) ? "Reply and Hold" : "Reply";
      }
      if (it && it.ydWhy && "bill" === it.kind) {
        const b = (DB.bills || []).find((x) => x.id === it.id);
        b && ((c.why = esc(it.ydWhy.slice(0, 2).join(" · "))), c.verb === "Open" && (c.verb = "Review"));
      }
      if (it && "payroll" === it.kind && "owner" === role()) c.verb = "Review Payroll";
      // a clean bill the PM approves is approved (it waits on no one after him): his verb says so
      if (it && "bill" === it.kind && "pm" === role() && "Recommend" === c.verb) {
        const b = (DB.bills || []).find((x) => x.id === it.id);
        b && !ydBillExc(b).length && (c.verb = "Approve");
      }
      if (it && "hand" === it.kind && it.ydWhy) c.verb = "Review";
    } catch (e) {}
    return c;
  };
}
// The page's model: Today (approvals, then now), Approvals, Coming Up (the next 7 days, not counted in the badge)
let ydTdMemo = { k: "", T: null };
td2Model = function () {
  const r = role(),
    S = TD2_SPEC[r] || TD2_SPEC.pm,
    k = [td2Tick, (tdyMe() || {}).id || r, tdyTabOf(), tdyAllOpen, ydPhone()].join("|");
  if (ydTdMemo.k === k && ydTdMemo.T) return ydTdMemo.T;
  const M = tdyModel(),
    td = today(),
    wk = iso(addDays(parse(td), 7)),
    rows = td2Rows(M)
      .map((x) => {
        // everything else of the person's is Coming Up (the queue holds the next 7 days of tasks; an order or a decision
        // dated later still waits on them and is never dropped)
        const sec = x.appr ? "appr" : "now" === x.sec || x.late || (x.due && x.due <= td) ? "now" : "coming";
        void wk;
        return Object.assign(x, { sec: sec });
      })
      .filter((x) => x.sec),
    inTab = (t, x) => ("appr" === t ? "appr" === x.sec : "coming" === t ? "coming" === x.sec : "appr" === x.sec || "now" === x.sec),
    chips = ["today", "appr", "coming"].map((c) => ({ k: c, label: TD2_CHIP[c], n: rows.filter((x) => inTab(c, x)).length })),
    stored = tdyTabOf(),
    tab = ["today", "appr", "coming"].includes(stored) ? stored : "today",
    Q = rows.filter((x) => inTab(tab, x)),
    desk = td2Desk(),
    fold = "today" === tab && !tdyAllOpen,
    cap = desk ? 14 : 5,
    secsOf = "appr" === tab ? ["appr"] : "coming" === tab ? ["coming"] : ["appr", "now"],
    shown = [];
  secsOf.forEach((s) => Q.filter((x) => x.sec === s).forEach((x) => (!fold || shown.length < cap) && shown.push(x)));
  const secs = secsOf.map((s) => ({ k: s, name: TD2_SEC[s], rows: shown.filter((x) => x.sec === s), n: Q.filter((x) => x.sec === s).length })).filter((s) => s.rows.length);
  const T = { M: M, r: r, S: S, rows: rows, chips: chips, tab: tab, Q: Q, shown: shown, secs: secs, hidden: Q.length - shown.length, late: rows.filter((x) => x.late).length, need: chips[0].n };
  return (ydTdMemo = { k: k, T: T }), T;
};
// the one number: the rows Today opens on (approvals + now), on the menu, the phone bar, the date line and the chip
td2LateN = function () {
  try {
    return TD2_SPEC[role()] ? td2Model().need : 0;
  } catch (e) {
    return 0;
  }
};
td2DateLine = function (T, long) {
  const d = parse(today()),
    day = long ? d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" }) : d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  return `${day} · ${T.need} need you today`;
};
// the update says up to three things on the phone too: the job slipping, the client waiting, the rest by the Standard
td2Brief = function (T) {
  const L = td2Look(),
    F = td2Facts(T),
    top = F.slice(0, 3),
    key = td2KeyOf(top),
    since = L.seen || "",
    sinceW = !since ? "Since yesterday" : since.slice(0, 10) === today() ? `Since ${td2Clock(since)}` : 1 === dayDiff(since.slice(0, 10), today()) ? "Since yesterday" : `Since ${fmt(since.slice(0, 10))}`,
    nothing = !!since && L.seenKey === key;
  let lines = top.map((f) => ({ pre: f.pre, link: f.link, post: f.post, go: f.go, why: f.why, model: !1 }));
  const C = L.cache;
  C && C.key === key && C.lines && C.lines.length === top.length && (lines = C.lines.map((x, i) => Object.assign({}, x, { go: top[i].go, why: top[i].why, model: !0 })));
  return { head: sinceW, since: since, facts: top, all: F, key: key, nothing: nothing, lines: nothing ? [] : lines, plain: top.map(td2Plain) };
};
// Safe to Spend at the head of the brief, read through the app's one function, its parts one tap down
let ydCashOpen = !1;
function ydCashHtml() {
  if (!["owner", "billing", "controller"].includes(role()) || ("function" == typeof tdNoMoney && tdNoMoney())) return "";
  let X = null;
  try {
    X = safeToSpend();
  } catch (e) {
    return "";
  }
  const safe = +X.safe || 0,
    recon = ((X.B && X.B.cashBy) || [])
      .map((x) => {
        const a = x.a || {},
          d = a.recon && a.recon.date;
        return `${String(a.name || x.name || "").split(" ")[0]} ····${a.last4 || ""} ${d ? `reconciled through ${fmt(d)}` : "never reconciled"}`;
      })
      .join(" · ");
  let why = "";
  try {
    why = "function" == typeof stsWhy ? stsWhy(X) : "";
  } catch (e) {}
  return `<div class="yd-cash" data-ydsafe="${r2(safe)}"><span>Safe to Spend</span><b class="${safe < 0 ? "bad" : ""}">${esc(ydMoney0(safe))}</b><button type="button" class="yd-cashb" data-ydcash aria-expanded="${ydCashOpen}">${ydCashOpen ? "Hide the Parts" : "The Parts"}</button></div>${
    ydCashOpen ? `<div class="yd-cashp">${ydKv("How it is made", "", why)}${recon ? ydKv("The accounts", "", recon) : ""}</div>` : ""
  }`;
}
{
  const base = td2BriefHtml;
  td2BriefHtml = function (B, desk) {
    const h = base.apply(this, arguments) || "",
      cash = ydCashHtml();
    if (!cash) return h;
    if (!h) return `<section class="td2-brief" aria-label="Your Brief">${cash}</section>`;
    // a function, not a replacement string: "$104,999" in a string is read as the pattern "$10" (it printed "04,999")
    return h.replace(/(<section class="td2-brief"[^>]*>)/, (m) => m + cash);
  };
}
// Where the Firm Stands: each line the count of its page, one tap from Today
function ydFirmRows() {
  const r = role(),
    out = [],
    add = (k, label, v, sub, go, money) => out.push({ k: k, label: label, v: v, sub: sub || "", go: go, money: !!money }),
    cnt = (n) => {
      try {
        return PRED[n] ? PRED[n].count() : 0;
      } catch (e) {
        return 0;
      }
    };
  add("risk", "Jobs at Risk", cnt("jobsAtRisk"), "late tasks, no-shows and overruns", () => setView("ovjobs"));
  ["owner", "pm", "controller"].includes(r) && add("budget", "Lines Over Budget", cnt("linesOverBudget"), "estimate lines spent past their budget", () => setView("ovjobs"), !0);
  "function" == typeof slNeedYou && ydMay("ovsales") && add("deals", "Deals That Need You", slNeedYou().length, "the Pipeline's Need You: past their date, quiet 14 days, signed with no job", () => slOpenPipeline("need"));
  "function" == typeof ydCompliance && add("comp", "Compliance", ydCompliance().length, "vendors on site without insurance, and the firm's own required records", () => setView(ydMay("obligations") ? "obligations" : "vendors"));
  ["owner", "pm", "coord"].includes(r) && add("people", "People Overloaded", cnt("peopleOverloaded"), "load lives on Team", () => setView("team"));
  "owner" === r && "function" == typeof ydBrainItems && add("brain", "Lessons and Changes to Approve", ydBrainItems().length, "in The Brain", () => setView("brain"));
  return out.filter((x) => !(x.money && "function" == typeof tdNoMoney && tdNoMoney()));
}
let ydFirmOpen = !1;
function ydFirmHtml() {
  const R = ydFirmRows();
  if (!R.length) return "";
  ydActs.firm = ydActs.firm || {};
  return `<div class="yd-firm" data-ydfirmwrap>${ydFoldHtml(
    "firm",
    "Where the Firm Stands",
    ydFirmOpen,
    R.map((x) => `<div class="yd-row" data-ydfirmrow="${esc(x.k)}" role="button" tabindex="0"><span class="yd-t"><b>${esc(x.label)}</b><span>${esc(x.sub)}</span></span><span class="yd-amt">${esc(String(x.v))}</span></div>`).join(""),
  ).replace('data-ydfold="firm"', 'data-ydfold="firm" data-ydfirm')}</div>`;
}
function ydTodayAfter() {
  if ("home" !== view || !TD2_SPEC[role()] || !td2Cur) return;
  const root = document.querySelector("#v-home .td2");
  if (!root) return;
  // the Approvals page is this chip now: no link to it
  root.querySelectorAll("[data-tdall]").forEach((a) => a.remove());
  root.querySelectorAll("[data-ydfirmwrap]").forEach((x) => x.remove());
  const at = root.querySelector(".td2-quiet");
  const html = ydFirmHtml();
  html && (at ? at.insertAdjacentHTML("beforebegin", html) : (root.querySelector(".td2-left") || root).insertAdjacentHTML("beforeend", html));
  // the chips say "Today 16", the phone bar's badge reads the same rows
  const n = td2Cur.T.need;
  document.querySelectorAll('#mtabs [data-mv="home"]').forEach((b) => b.setAttribute("aria-label", `Today, ${n} need you`));
}

// ---- Tasks ----------------------------------------------------------------------------------------------------------
// The chips: Mine (every open task of yours), Waiting On (what waits on someone else), Team (grouped by person).
if ("function" == typeof tvBuiltIns) {
  tvBuiltIns = function () {
    const S = (o) => Object.assign({ tkWho: "all", tkProject: "", tkArea: "", tkPri: "", t2View: "all", t2Q: "", tvFF: "{}" }, o);
    return [
      { id: "b:open", name: "Mine", s: S({ tkWho: "me" }) },
      { id: "b:wait", name: "Waiting On", s: S({ t2View: "blocked" }) },
      // Team is the old Everything (everyone, all open): its id stays, so a saved link or a test that names it lands here
      { id: "b:all", name: "Team", s: S({}) },
    ];
  };
}
const ydTeamOn = () => {
  try {
    // the Team list by person is the List's and the phone's; the Table and the Board keep their own layout of the same rows
    return "tkall" === view && ydTeamPick && tvIsOn(tvBuiltIns()[2]) && ("cards" === (tkMode || "cards") || ydPhone());
  } catch (e) {
    return !1;
  }
};
let ydTkFirst = "",
  // the person picked the Team chip (the Team list by person); any other pick leaves it
  ydTeamPick = !1;
if ("function" == typeof tvApply) {
  const base = tvApply;
  tvApply = function (id) {
    ydTeamPick = "b:all" === id;
    return base.apply(this, arguments);
  };
}
// the first draw for a person opens on Mine (every open task of theirs), not on what is due this week
{
  const base = renderTkAll;
  renderTkAll = function () {
    try {
      const u = (currentUser() || {}).id || "";
      if (u && u !== ydTkFirst && ydOffice()) {
        ydTkFirst = u;
        (tkWho = "me"), (t2View = "all"), (tkProject = ""), (tkArea = ""), (tkPri = "");
      }
    } catch (e) {}
    const r = base.apply(this, arguments);
    try {
      ydTasksAfter();
    } catch (e) {
      console.warn("your day: tasks", e);
    }
    return r;
  };
}
function ydTeamHtml() {
  const T = tkAll({ open: !0 }).filter((t) => !t.approval),
    td = today(),
    people = "function" == typeof ydPeople ? ydPeople() : (DB.users || []).map((u) => ({ id: u.id, name: u.name })),
    byPerson = people.map((p) => ({ p: p, T: T.filter((t) => (p.uid ? t.ownerUid === p.uid : !1) || (!t.ownerUid && t.owner === p.name)) })),
    named = new Set(byPerson.flatMap((x) => x.T.map((t) => t.key))),
    other = T.filter((t) => !named.has(t.key)),
    has = byPerson.filter((x) => x.T.length),
    none = byPerson.filter((x) => !x.T.length).map((x) => x.p.name);
  const row = (t) => {
    const s = tdyShape ? tdyShape(t) : t,
      late = t.due && t.due < td;
    return `<div class="yd-row" data-ydtask="${esc(s.key || t.key || "")}" role="button" tabindex="0"><span class="yd-t"><b>${esc(t.title)}</b><span>${esc([t.code, t.sourceLabel || t.project].filter(Boolean).join(" · "))}</span></span><span class="yd-when${late ? " late" : ""}">${esc(t.due ? (late ? `${dayDiff(t.due, td)} days late` : ydWhen(t.due)) : "No date")}</span></div>`;
  };
  const sortT = (L) => L.slice().sort((a, b) => String(a.due || "9999").localeCompare(String(b.due || "9999")));
  const groups = has
    .map((x) => `<section class="yd-card yd-team" data-ydteamwho="${esc(x.p.id)}"><div class="yd-gh">${esc(x.p.name)}</div>${sortT(x.T).map(row).join("")}</section>`)
    .concat(other.length ? [`<section class="yd-card yd-team" data-ydteamwho="nobody"><div class="yd-gh">No Owner Yet</div>${sortT(other).map(row).join("")}</section>`] : [])
    .join("");
  return `<div class="yd-teamv">${groups}<p class="yd-foot" data-ydteamfoot>${esc(`${people.length} people at the firm; ${has.length} have open tasks${none.length ? `. Nothing open: ${none.join(", ")}` : ""}. Load per person lives on Team.`)}</p></div>`;
}
function ydTasksAfter() {
  const host = document.getElementById("tkall-body");
  if (!host || "tkall" !== view || !ydOffice()) return;
  const phone = ydPhone();
  // the Team chip carries no number (it waits on nobody in particular)
  host.querySelectorAll('[data-tvview="b:all"] .n').forEach((n) => (n.textContent = ""));
  if (phone) {
    // the phone's chips are the same three
    const q = host.querySelector(".tv-qchips");
    if (q) {
      const vs = tvBuiltIns(),
        P = {},
        on = vs.find((v) => tvIsOn(v));
      q.innerHTML = vs
        .map((v) => {
          const n = "b:all" === v.id ? "" : tvCountFor(v, P);
          return `<button type="button" class="yd-chip${on && on.id === v.id ? " on" : ""}" data-ydchip="${esc(v.id)}" aria-pressed="${!!(on && on.id === v.id)}">${esc(v.name)}<span class="n">${n}</span></button>`;
        })
        .join("");
      q.classList.add("yd-chips");
      q.querySelectorAll("[data-ydchip]").forEach((b) => (b.onclick = (e) => (e.preventDefault(), tvApply(b.dataset.ydchip))));
    }
  }
  host.querySelectorAll(".yd-teamv, .yd-calall").forEach((x) => x.remove());
  // the Calendar view shows the tasks; everything else dated (decisions, inspections, milestones, deliveries, expiries)
  // is one tap away on the calendar of every dated thing, so nothing the old Calendar page held is lost
  if ("cal" === tkMode && ydMay("calendar")) {
    const at = host.querySelector(".t2-list") || host.lastElementChild;
    at && at.insertAdjacentHTML("beforebegin", `<div class="yd-calall yd-ph"><button type="button" class="btn" data-ydcalall>Everything Dated</button><span class="small muted">decisions, inspections, milestones, deliveries and expiries beside the tasks</span></div>`);
    const b = host.querySelector("[data-ydcalall]");
    b && (b.onclick = (e) => (e.preventDefault(), (ydCalKeep = !0), setView("calendar")));
  }
  const list = host.querySelector(".t2-list");
  if (ydTeamOn()) {
    list && (list.hidden = !0);
    (list || host.lastElementChild).insertAdjacentHTML("afterend", ydTeamHtml());
    host.querySelectorAll("[data-ydtask]").forEach((r) => (r.onclick = () => ("function" == typeof tkSheet ? tkSheet(r.dataset.ydtask) : tkOpen(r.dataset.ydtask))));
  } else list && (list.hidden = !1);
}

// ---- old pages forward to their new homes ---------------------------------------------------------------------------
function ydForward() {
  if (!ydOffice()) return;
  const v = view;
  if ("mapprove" === v) return (view = "home"), tdyTabSet("appr"), (ydTdMemo.k = "");
  // the Chief of Staff's findings are Today's rows (its Every Chain stays a part of Ask's Findings tab)
  if ("cos" === v && ydMay("home")) return (view = "home");
  if ("comms" === v && !ydMsgKeep && !("undefined" != typeof cmOpen && cmOpen)) return (view = "chat"), (ydMsg.chip = "need"), (ydMsg.thread = !1);
  if ("meetings" === v && !ydMsgKeep && !("undefined" != typeof mtOpen && mtOpen) && ydMay("chat")) return (view = "chat"), (ydMsg.chip = "meet"), (ydMsg.thread = !1);
  if ("calendar" === v && ydMay("tkall") && !ydCalKeep) return (view = "tkall"), (tkMode = "cal");
}
{
  const base = setView;
  setView = function (v) {
    // a page opened from the menu or a link starts at its list; a message or meeting opened from the list keeps its reader
    "chat" === v && (ydMsg.thread = !1);
    if (("comms" === v || "meetings" === v) && !ydMsgKeep) {
      try {
        "comms" === v && (cmOpen = null);
        "meetings" === v && (mtOpen = "");
      } catch (e) {}
    }
    if ("calendar" === v && ydOffice() && ydMay("tkall") && !ydCalKeep) {
      try {
        tkSetMode("cal");
      } catch (e) {}
      v = "tkall";
    }
    "calendar" !== v && (ydCalKeep = !1);
    const r = base.call(this, v);
    ydMsgKeep = !1;
    return r;
  };
}
{
  const base = render;
  render = function () {
    try {
      ydForward();
    } catch (e) {
      console.warn("your day: forward", e);
    }
    const r = base.apply(this, arguments);
    try {
      // a person's page is opened on purpose: any other page (or another person signing in) leaves it
      "team" !== view && "undefined" != typeof ydPersonId && (ydPersonId = "");
      ydOffice() && document.querySelectorAll('#mtabs [data-mv="tkall"] i.n').forEach((i) => i.remove());
      ydMsgRender();
      ydTodayAfter();
      document.querySelectorAll(".view").forEach((e) => e.classList.toggle("on", e.id === "v-" + view));
    } catch (e) {
      console.warn("your day", e);
    }
    return r;
  };
}
// Ask's "what is waiting on me" is Today's Approvals chip and Messages' Needs an Answer: the same rows, one number
if ("function" == typeof paAsk) {
  const base = paAsk;
  const fix = (a) => {
    try {
      if (!a || "onme" !== a.kind || !YD_TD_ROLES.includes(role()) || !TD2_SPEC[role()]) return a;
      const T = td2Model(),
        n = (T.chips.find((c) => "appr" === c.k) || {}).n || 0,
        m = ydMsgNeeds().length;
      a.headline = n
        ? `${ydPlural(n, "thing")} waiting on your approval${m ? `, and ${ydPlural(m, "message")} waiting on your answer` : ""}.`
        : `Nothing is waiting on your approval${m ? `; ${ydPlural(m, "message")} waiting on your answer` : ""}.`;
      a.note = "The same list as Today's Approvals chip, and Messages' Needs an Answer.";
      "function" == typeof paGo && (a.go = paGo({ view: "home" }));
    } catch (e) {}
    return a;
  };
  paAsk = function () {
    const a = base.apply(this, arguments);
    return a && "function" == typeof a.then ? a.then(fix) : fix(a);
  };
}
// Tasks carries no number in the menu: Today already counts what is due (the approved menu, Your Day SPEC 2)
{
  const base = mnItemN;
  mnItemN = function (it) {
    if (it && "tkall" === it.v && ydOffice()) return 0;
    return base.apply(this, arguments);
  };
}
// A bill the PM approves that is no exception needs no owner (DECISIONS 10-26): it is Approved, To Pay, and its record
// says who approved it, when, and under which rule. The controller pays it from his Today; nothing pays itself.
const YD_EXC_RULE = "Exceptions only (Alan, 10-26): the owner decides a bill paid before approval, over its PO or with none, a bank-detail change, a first payment to a new vendor, a PO over $10,000 and payroll";
{
  const base = billAction;
  billAction = function (b, a) {
    const r = base.apply(this, arguments);
    try {
      if ("pmok" === a && b && "pm-approved" === b.status && !ydBillExc(b).length) {
        const by = (S && S.project && S.project.userName) || ((currentUser() || {}).name) || role();
        b.status = "approved";
        b.approvedAt = today();
        b.approvals.push({ t: nowStamp(), ts: appNowIso(), by: by, role: role(), action: "approved: no exception, so it does not wait on the Owner", rule: YD_EXC_RULE });
        audit("bill", b.id, "approved under the exceptions rule", { status: "pm-approved" }, { status: "approved" }, YD_EXC_RULE);
        save(), render();
        toast(`${b.number}: approved, to pay. The controller pays it.`, () => ("function" == typeof openBill ? openBill(b.id) : setView("ap")));
      }
    } catch (e) {
      console.warn("bill under the exceptions rule", e);
    }
    return r;
  };
}
// the menu lights the page a forwarded view lands on
"object" == typeof MN_ALIAS && Object.assign(MN_ALIAS, { comms: "chat", meetings: "chat", calendar: "tkall", mapprove: "home" });

// ---- the clicks -----------------------------------------------------------------------------------------------------
document.addEventListener(
  "click",
  (e) => {
    const t = e.target && e.target.closest ? e.target : null;
    if (!t) return;
    const at = (s) => t.closest(s);
    let b;
    if ((b = at("#yd-chat [data-ydchip]"))) return e.preventDefault(), (ydMsg.chip = b.dataset.ydchip), (ydMsg.sel = ""), void render();
    if ((b = at("#yd-chat [data-ydnewmsg]"))) {
      e.preventDefault();
      return void ("function" == typeof cmCompose ? cmCompose() : "function" == typeof gcCompose ? gcCompose() : ((ydMsg.thread = !0), render()));
    }
    if ((b = at("#yd-chat [data-ydopenmsg]"))) {
      e.preventDefault();
      const c = (DB.comms || []).find((x) => x.id === b.dataset.ydopenmsg);
      return void (c && ydMsgOpen(c));
    }
    if ((b = at("#yd-chat [data-ydact]"))) {
      e.preventDefault(), e.stopPropagation();
      const f = ydActs[b.dataset.ydact];
      return void (f && f());
    }
    if ((b = at("#yd-chat [data-ydmrow]")) && !at("button")) {
      e.preventDefault();
      // a row is its conversation: it opens (the reader holds the reply, the proposals read from it and the record)
      const f = ydActs[b.dataset.ydmrow];
      return void (f && f());
    }
    if ((b = at("#v-home [data-ydcash]"))) return e.preventDefault(), e.stopPropagation(), (ydCashOpen = !ydCashOpen), void render();
    if ((b = at("#v-home [data-ydfirm]"))) return e.preventDefault(), e.stopPropagation(), (ydFirmOpen = !ydFirmOpen), void render();
    if ((b = at("#v-home [data-ydfirmrow]"))) {
      e.preventDefault();
      const x = ydFirmRows().find((y) => y.k === b.dataset.ydfirmrow);
      return void (x && x.go && x.go());
    }
  },
  !0,
);
// a thread opened from Messages has a way back to the list
function ydMsgBack() {
  const v = document.getElementById("v-chat");
  if (!v) return;
  v.querySelectorAll(":scope > .yd-msgback").forEach((x) => x.remove());
  if ("chat" !== view || !ydOffice() || !ydMsg.thread) return;
  v.insertAdjacentHTML("afterbegin", `<div class="yd-msgback"><button type="button" class="yd-back" data-ydmsgback>${ydSvg("back")}Messages</button></div>`);
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      ydMsgBack();
    } catch (e) {}
    return r;
  };
}
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("[data-ydmsgback]") : null;
    if (!b) return;
    e.preventDefault(), (ydMsg.thread = !1), render();
  },
  !0,
);
