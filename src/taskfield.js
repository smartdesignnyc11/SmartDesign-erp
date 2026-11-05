/*<<taskfield.js>>*/
/* ==== tasks on the receiver's side: the field and office support on the phone (lane T1, 2026-11-05) ===============
   Alan, 11-05: "the task module is one of the most important and it isn't great on mobile". The field expert scored
   the phone crew 6, foreman 5, coordinator 7, designer 6 (scratchpad tasks_review/field); the PM expert found that a
   hand-off or a meeting item for the foreman or the crew lands nowhere they look (tasks_review/pm, S1_01 and S1_02).
   What was wrong, as classes:
     - a task row drawn outside the Tasks list (the foreman's Put on You, the crew's Clock, the designer's Today) did
       not open: no sheet, no Done, and the foreman has no Tasks page. Now every such row carries data-tkopen and one
       listener opens the one sheet (tkSheet); its Done runs the one close (tdyDone) with the proof gate.
     - an offer showed only on Tasks (a page the field does not have) and named the task's owner as the sender. Now it
       lands at the top of the person's own list (the foreman's Today, the crew's Clock, the office Today, the
       designer's Today) with Accept and Decline, and the sheet names who offered it.
     - a task made from a field question closed without its question: the asker never heard. Done now asks for the
       answer, closes the question and puts the answer on the asker's Today (For You).
   Design gate (BACKLOG 1.16). No new store, list, queue or menu item: rows are tkAll() / tkItems(); offers are
   tkOfferedToMe() (src/tasks.js), the one function every count of "offered to me" reads; the answer is the field
   question's own record (DB.field.raises), as fAnswerRaise writes it. A crew member's Blocked is a task on the
   foreman's list (crCreateTask) linked to the schedule line, and the line says it is blocked.
--------------------------------------------------------------------------------------------------------------------- */
const TKR_IC = {
  check: '<path d="M5 12.5l4.2 4.2L19 7"/>',
  hand: '<path d="M5 12h12"/><path d="M13 7l5 5-5 5"/>',
};
const tkrSvg = (k, n) => `<svg viewBox="0 0 24 24" width="${n || 18}" height="${n || 18}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${TKR_IC[k] || ""}</svg>`;
const tkrMe = () => {
  try {
    return tdyMe() || {};
  } catch (e) {
    return {};
  }
};
// who offered it: the person who pressed Hand Off (by), not the owner it stays with until accepted (from)
const tkrSender = (H) => (H ? H.by || H.from || "Someone" : "Someone");
function tkrDueSay(due) {
  if (!due) return "";
  const td = today();
  return due < td ? `was due ${fmt(due)}` : due === td ? "due today" : `due ${fmt(due)}`;
}

// ---- one row for a task drawn outside the Tasks list: it opens the sheet; Done closes it through the proof gate -----
function tkRowOpenHtml(x, o) {
  const O = o || {},
    key = x.key || t2Key(x),
    late = !x.done && x.due && x.due < today(),
    meta = [O.meta, x.project, tkrDueSay(x.due)].filter(Boolean).join(" · ");
  return `<div class="tkr-row ${late ? "late" : ""}" data-tkopen="${esc(key)}" role="button" tabindex="0" aria-label="Open ${esc(x.title || "the task")}"><div class="tkr-mid"><b>${esc(x.title || "")}</b>${meta ? `<span class="tkr-m">${esc(meta)}</span>` : ""}</div>${
    O.noDone || x.done ? "" : `<button type="button" class="btn tkr-done" data-tkrowdone="${esc(key)}" aria-label="Done: ${esc(x.title || "")}">${tkrSvg("check", 16)}<span>Done</span></button>`
  }</div>`;
}
// Done from a row: the same close the sheet runs (proof where the Standard needs it, the field question's answer)
function tkRowDone(key) {
  const R = tkResolve(key);
  if (!R) return toast("That task is no longer here");
  const t = R.t || Object.assign({ row: R.x }, R.x);
  tdyDone(t.key ? t : Object.assign({ row: R.x }, R.x));
}
// ---- offers: what waits on my yes or no, at the top of my own list ---------------------------------------------------
function tkOffersCardHtml() {
  const L = tkOfferedToMe();
  if (!L.length) return "";
  return `<div class="card tkr-offers" data-tkoffers><div class="hd"><h3>Offered to You</h3><span class="small muted">${L.length}</span></div>${L.map((t) => {
    const H = t.handoff || {},
      meta = [`from ${tkFirst(tkrSender(H))}`, t.project, tkrDueSay(t.due)].filter(Boolean).join(" · ");
    return `<div class="tkr-row tkr-offer" data-tkopen="${esc(t.key)}" role="button" tabindex="0"><div class="tkr-mid"><b>${esc(t.title)}</b><span class="tkr-m">${esc(meta)}</span>${H.note ? `<span class="tkr-note">“${esc(H.note)}”</span>` : ""}</div><div class="tkr-acts"><button type="button" class="btn" data-tkoffacc="${esc(t.key)}">Accept</button><button type="button" class="btn" data-tkoffdec="${esc(t.key)}">Decline</button></div></div>`;
  }).join("")}</div>`;
}
function tkOfferDecline(key) {
  const t = tkOfferedToMe().find((y) => y.key === key);
  if (!t) return toast("That offer is no longer waiting on you");
  const H = t.handoff || {};
  mbModal(
    "Decline",
    `<p class="small muted" style="margin:0 0 8px"><b>${esc(t.title)}</b>. It goes back to ${esc(tkFirst(tkrSender(H)))} with your reason.</p>${mbF("Why", '<input data-f="reason" placeholder="e.g. not mine: the coordinator orders it">')}`,
    { submit: "Decline", onSubmit: (f) => (tdyDecline(t, f.reason) ? !0 : !1) },
  );
}
// one listener for every row and offer button drawn by this file (the rows are redrawn on every render)
document.addEventListener("click", (e) => {
  const tg = e.target && e.target.closest ? e.target : null;
  if (!tg) return;
  let b = tg.closest("[data-tkrowdone]");
  if (b) return e.preventDefault(), e.stopPropagation(), void tkRowDone(b.dataset.tkrowdone);
  if ((b = tg.closest("[data-tkoffacc]"))) {
    e.preventDefault(), e.stopPropagation();
    const t = tkOfferedToMe().find((y) => y.key === b.dataset.tkoffacc);
    return void (t ? tdyAccept(t) : toast("That offer is no longer waiting on you"));
  }
  if ((b = tg.closest("[data-tkoffdec]"))) return e.preventDefault(), e.stopPropagation(), void tkOfferDecline(b.dataset.tkoffdec);
  // a decision row on the designer's Today opens the decision
  if ((b = tg.closest("[data-stdec]")) && !tg.closest("button, a, input, select")) {
    e.preventDefault();
    const [pid, did] = b.dataset.stdec.split("|"),
      p = (DB.projects || []).find((q) => q.id === pid),
      d = p && (p.decisions || []).find((q) => q.id === did);
    return void (d ? flowGo.decision(p, d)() : toast("That decision is no longer open"));
  }
  const r = tg.closest("[data-tkopen]");
  if (!r || tg.closest("button, a, input, select, textarea, label")) return;
  e.preventDefault();
  tkSheet(r.dataset.tkopen);
});
document.addEventListener("keydown", (e) => {
  const r = e.target && e.target.matches && e.target.matches("[data-tkopen]") ? e.target : null;
  r && ("Enter" === e.key || " " === e.key) && (e.preventDefault(), tkSheet(r.dataset.tkopen));
  e.target && e.target.matches && e.target.matches("[data-stdec]") && "Enter" === e.key && (e.preventDefault(), e.target.click());
});

// ---- the sender is the person who pressed Hand Off, and a task nobody named is theirs until it is accepted -----------
// A schedule line the crew does was routed to the job's lead (Alan), so Angel's hand-off to Alberto read "Alan offered
// this to you". The Standard: "if you see it, you own it until a named person accepts the hand-off".
{
  const base = tdyHandOff;
  tdyHandOff = function (x, toName, note) {
    try {
      const me = tkrMe();
      if (x && me.name && ("routed" === x.ownerHow || !x.owner || ("sched" === x.kind && "outside" === x.ownerHow))) x = Object.assign({}, x, { owner: me.name, ownerUid: me.id || "", ownerHow: "routed" });
    } catch (e) {}
    return base.call(this, x, toName, note);
  };
}

// ---- a task made from a field question: Done asks for the answer, closes the question and tells the asker ----------
// The link is the record's raiseId (a question raised from the field makes its issue with it); a seeded issue that
// names the same work as an open drawing question on the same job is the same question.
function tkRaiseOf(x) {
  try {
    if (!x || x.done) return null;
    const R = (DB.field && DB.field.raises) || [],
      rec = tdyRec(x) || {},
      id = rec.raiseId || (rec.link && "raise" === rec.link.kind ? rec.link.id : "") || (rec.source && rec.source.raiseId) || "";
    let r = id ? R.find((q) => q.id === id) : null;
    if (!r && "issue" === x.kind && "rfi" === rec.type && rec.taskId)
      (r = R.find((q) => "rfi" === q.type && q.projectId === x.projectId && q.taskId === rec.taskId) || null), r && (rec.raiseId = r.id);
    return r && !/^(answered|closed)$/.test(String(r.status || "")) ? r : null;
  } catch (e) {
    return null;
  }
}
function tkAnswerRaise(r, answer, x) {
  const me = tkrMe().name || DB.me || "";
  Object.assign(r, { status: "answered", answer: answer, decision: r.decision || "", answeredBy: me, answeredAt: appNowIso() });
  try {
    const p = (DB.projects || []).find((q) => q.id === r.projectId);
    // the issue that is this task closes through its own Done; any other issue on the same question is answered
    (p && (p.issues || []).filter((i) => i.raiseId === r.id)).forEach((i) => {
      x && "issue" === x.kind && i.id === x.id ? 0 : (i.status = "answered");
      i.notes = `${i.notes || ""} — Answer: ${answer}`.replace(/^ — /, "");
    });
    p && "function" == typeof czOn ? czOn(p, () => log(`${(F_TYPES[r.type] || {}).n || "Question"} answered → ${r.by}: ${answer}`, "field", me)) : log(`Answered → ${r.by}: ${answer}`, "field", me);
  } catch (e) {}
  try {
    audit("raise", r.id, "answered", "", answer.slice(0, 80), x ? `closed with ${x.title}` : "");
  } catch (e) {}
}
function tkAnswerSheet(x, r, then) {
  const asker = tkFirst(r.by || "the field");
  return mbModal(
    `Answer ${esc(asker)}'s Question`,
    `<p class="small muted" style="margin:0 0 8px">${esc(asker)} asked: <b>${esc(r.title)}</b>${r.note ? ` — ${esc(r.note)}` : ""}</p><p class="small muted" style="margin:0 0 8px">Closing this task closes the question. The answer goes to ${esc(asker)}'s Today.</p>${mbF("Answer", '<textarea data-f="a" rows="3" placeholder="Short and definite: this goes to the field"></textarea>')}`,
    {
      submit: "Send the Answer and Mark Done",
      onSubmit: (f) => {
        if (!f.a) return toast(`Write the answer: ${asker} is waiting on it`), !1;
        tkAnswerRaise(r, f.a, x);
        save();
        setTimeout(() => then && then(), 0);
        toast(`Answer sent to ${asker}: ${tdWords(r.title, 8)}`, [{ label: "Open", run: () => tkOpen(t2Key(x)) }]);
        return !0;
      },
    },
  );
}
{
  const base = tdyDone;
  tdyDone = function (t) {
    const x = (t && t.row) || t,
      r = tkRaiseOf(x);
    if (r) return tkAnswerSheet(x, r, () => base.call(this, t));
    return base.apply(this, arguments);
  };
}
{
  const base = tkToggle;
  tkToggle = function (kind, id, projectId) {
    try {
      const x = tkItems().find((q) => q.kind === kind && q.id === id && (q.projectId || "") === (projectId || "")),
        r = x && tkRaiseOf(x);
      if (r) return void setTimeout(() => tkAnswerSheet(x, r, () => base.call(this, kind, id, projectId)), 0);
    } catch (e) {}
    return base.apply(this, arguments);
  };
}

// ---- a task whose work is a photograph is done with the photograph ---------------------------------------------------
{
  const base = tdyProofNeed;
  tdyProofNeed = function (x, rec) {
    const n = base.apply(this, arguments);
    if (n || !x || !/^(sched|action|firm)$/.test(x.kind) || (rec && !1 === rec.proofNeed)) return n;
    return /^\s*(photograph|photo|take (a |the )?(photo|picture)s?|picture)\b/i.test(String(x.title || "")) ? Object.assign({ kind: "photos" }, TDY_PROOF.photos, { label: "Photos of the work" }) : null;
  };
}

// ---- a punch item is done with a photo of the finished work (Site's Punch Done asked for nothing) --------------------
function tkPunchProof(x, then) {
  const shots = [];
  const m = mbModal(
    `Done: ${esc(tdWords(x.item || "Punch item", 6))}`,
    `<p class="small muted tdy-proof-why">${esc((() => {
      try {
        return tdyCite(TDY_PROOF.photos) || "Photograph the finished work";
      } catch (e) {
        return "Photograph the finished work";
      }
    })())}</p><p>Take a photo of the finished work${x.room ? ` in ${esc(x.room)}` : ""}. The item is done once it is on it.</p><div class="small muted" data-tkrshots>No photo yet.</div><button type="button" class="btn" data-tkrcam>${"undefined" != typeof TDY_IC ? TDY_IC.camera : ""}<span>Take a Photo</span></button>`,
    {
      submit: "Mark Done",
      onSubmit: () => {
        if (!shots.length) return toast("Add a photo of the finished work first"), !1;
        x.photos = (x.photos || []).concat(shots);
        x.donePhotos = shots.length;
        try {
          "function" == typeof fSavePhotos && fSavePhotos(shots, `Punch done: ${x.item || ""}`, { kind: "punch", id: x.id });
        } catch (e) {}
        then && then();
        return !0;
      },
    },
  );
  const cam = m && m.querySelector("[data-tkrcam]"),
    box = m && m.querySelector("[data-tkrshots]");
  cam &&
    (cam.onclick = () =>
      mReadPhoto((url) => {
        shots.push(url), box && (box.textContent = `${shots.length} photo${1 === shots.length ? "" : "s"} ready to attach.`);
      }, "environment"));
  return m;
}

// ---- quick add that names a record (PO-2026-047, CO-3, an estimate, an invoice, a selection) is linked to it and filed
// on its job, not under Office. The parser is the one shared reader, tkRefsIn (src/meeting.js, lane T2).
if ("function" == typeof tvQaCreate) {
  const base = tvQaCreate;
  tvQaCreate = function (F, photo) {
    let refs = [];
    try {
      refs = "function" == typeof tkRefsIn ? tkRefsIn(String((F && (F.text || F.title)) || "")) || [] : [];
    } catch (e) {
      refs = [];
    }
    const pid = refs.map((r) => r.pid).find(Boolean) || "",
      G = F && !F.pid && pid ? Object.assign({}, F, { pid: pid }) : F,
      made = base.call(this, G, photo);
    try {
      if (made && made.rec && refs.length && "function" == typeof tkAddLink) {
        refs.forEach((r) => tkAddLink(made.rec, { kind: r.kind, id: r.id }) && tkLog(made.rec, { ev: "link", kind: r.kind, id: r.id }));
        save();
      }
    } catch (e) {
      console.warn("quick add links", e);
    }
    return made;
  };
}

// ---- the schedule's list on the phone: one row per line, its name, who and when, and its progress as the action ------
// The row read "Rough electrical 55%9/1" (the progress chip's words run into the name) and kept the line's notes as a
// title tooltip that stuck on a long press (the foreman, Schedule > List).
if ("undefined" != typeof PR_SPECS) {
  PR_SPECS.sched = (tr, get) => {
    const name = get(/^task$/i);
    if (!name) return null;
    tr.removeAttribute("title");
    const c = name.cloneNode(!0);
    c.querySelectorAll(".prg-chip, .sub, .dot").forEach((x) => x.remove());
    const id = String(tr.dataset.edit || "").replace(/^task:/, ""),
      t = "undefined" != typeof S && S && (S.tasks || []).find((q) => q.id === id),
      chip = name.querySelector(".prg-chip");
    if (!t) return { title: prTxt(c) };
    const late = "done" !== t.status && t.end && t.end < today();
    return {
      title: prTxt(c) + ("milestone" === t.type ? " (milestone)" : ""),
      meta: [t.owner, t.start ? `${fmt(t.start)} – ${fmt(t.end)}` : "", "done" === t.status ? "done" : late ? "late" : ""].filter(Boolean).join(" · "),
      late: late,
      actEl: chip || null,
    };
  };
}

// ---- Clock In never overlaps a day already sent: the crew clocked in at 10:00 on a 9/3 that read 7:30 to 4:00, sent ---
function tkClockCovers(emp, at) {
  const ms = new Date(at).getTime();
  return (DB.time || []).find((t) => t.empId === emp.id && t.in && t.out && new Date(t.in).getTime() <= ms && ms < new Date(t.out).getTime()) || null;
}
if ("function" == typeof clockEvent) {
  const base = clockEvent;
  clockEvent = async function (kind) {
    try {
      const emp = "in" === kind && "function" == typeof myEmp ? myEmp() : null,
        hit = emp && tkClockCovers(emp, appNowIso());
      if (hit) {
        const sent = /^(submitted|approved|paid|locked)$/.test(String(hit.status || ""));
        return void toast(`Your ${fmt(hit.date)} already runs ${stampTime(hit.in)} to ${stampTime(hit.out)}${sent ? " and was sent for approval" : ""}. A new clock-in would count those hours twice; ask ${tkFirst((tdyRoleUser("foreman") || {}).name || "the foreman")} to reopen it if it is wrong.`, [{ label: "Open", run: () => ("function" == typeof openTime ? openTime(hit.id) : setView("time")) }]);
      }
    } catch (e) {}
    return base.apply(this, arguments);
  };
}

// ---- where the receiver looks: the foreman's Today, the crew's Clock, the office Today, the designer's Today ----------
function tkrMount(root, where) {
  if (!root) return;
  root.querySelectorAll(":scope .tkr-offers").forEach((c) => c.remove());
  const html = tkOffersCardHtml();
  if (!html) return;
  where ? where.insertAdjacentHTML("afterend", html) : root.insertAdjacentHTML("afterbegin", html);
}
// what is put on the crew member (a meeting's action item, a task Angel gave him), drawn on his Clock
function tkMineCardHtml(o) {
  const me = tkrMe();
  if (!me.id) return "";
  const L = tkAll({ open: !0, uid: me.id }).filter((t) => t.ownerUid === me.id && "sched" !== t.kind && !t.approval);
  if (!L.length) return "";
  const late = L.filter((t) => t.due && t.due < today()).length;
  return `<div class="card f-card f-mine tkr-mine"><div class="hd"><h3>Put on You</h3><span class="small muted">${late ? `${late} past due` : `${L.length} open`}</span></div>${L.slice(0, 8)
    .map((t) => tkRowOpenHtml(t))
    .join("")}${L.length > 8 ? `<div class="small muted" style="padding:6px 0">and ${L.length - 8} more</div>` : ""}</div>`;
}
// ---- Blocked, from the crew's Clock: the reason goes to the foreman as a task of his, and the job's line says it ------
const TKR_BLOCK_WHY = ["Waiting on material", "Waiting on another trade", "Need an answer", "Not safe to work", "Other"];
function tkBlockedSheet(taskId) {
  const p = S,
    t = p && (p.tasks || []).find((q) => q.id === taskId);
  if (!t) return toast("That task is no longer on the schedule");
  let why = "";
  const m = mbModal(
    `Blocked: ${esc(tdWords(t.name, 6))}`,
    `<p class="small muted" style="margin:0 0 8px">Say what stops the work. It goes to ${esc(tkFirst((tdyRoleUser("foreman") || {}).name || "the foreman"))} as a task, and the job shows the line as blocked.</p><div class="tks-chips" role="radiogroup" aria-label="What stops it">${TKR_BLOCK_WHY.map((w) => `<button type="button" class="tks-chip" role="radio" aria-checked="false" data-tkrwhy="${esc(w)}">${esc(w)}</button>`).join("")}</div>${mbF("What Stops It", '<input data-f="note" placeholder="e.g. no LVL on site, framing can\'t start">')}`,
    {
      submit: "Send to the Foreman",
      onSubmit: (f) => {
        const reason = [why && "Other" !== why ? why : "", f.note].filter(Boolean).join(": ");
        if (!reason) return toast("Say what stops the work"), !1;
        return tkBlock(p, t, reason) ? !0 : !1;
      },
    },
  );
  m &&
    m.querySelectorAll("[data-tkrwhy]").forEach(
      (b) =>
        (b.onclick = () => {
          why = b.dataset.tkrwhy;
          m.querySelectorAll("[data-tkrwhy]").forEach((y) => (y.classList.toggle("on", y === b), y.setAttribute("aria-checked", String(y === b))));
        }),
    );
  return m;
}
function tkBlock(p, t, reason) {
  const me = tkrMe(),
    fore = tdyRoleUser("foreman"),
    to = fore && fore.id !== me.id ? fore.name : (tdyLeadOf({ projectId: p.id }) || {}).name || "";
  const made = crCreateTask({ title: `Blocked: ${t.name} — ${reason}`, for: `p:${p.id}`, assignee: to, due: today(), priority: "high", notes: `${me.name || "The crew"} cannot go on with ${t.name}: ${reason}`, source: { field: !0, blocked: t.id }, handoff: !1 });
  if (!made) return !1;
  try {
    made.rec && ((made.rec.link = { kind: "sched", id: t.id }), (made.rec.waitsOn = ""));
    t.blocked = { reason: reason, by: me.name || "", at: appNowIso(), taskId: made.id };
    czOn(p, () => log(`${t.name}: blocked — ${reason} (${me.name || "crew"})`, "field", me.name || ""));
    audit("task", t.id, "blocked", "", reason, me.name || "");
  } catch (e) {}
  save(), render();
  toast(`Sent to ${tkFirst(to) || "the foreman"}: ${t.name} is blocked`, [{ label: "Open", run: () => tkSheet(`action:${made.id}:${p.id}`) }]);
  return !0;
}
if ("function" == typeof fmClockHome) {
  const base = fmClockHome;
  fmClockHome = function () {
    const r = base.apply(this, arguments);
    try {
      const card = document.getElementById("fm-today");
      if (!card) return r;
      card.querySelectorAll("[data-fm-block]").forEach((b) => (b.onclick = (e) => (e.stopPropagation(), tkBlockedSheet(b.dataset.fmBlock))));
      // a blocked line says so where the crew reads it
      card.querySelectorAll(".fm-row[data-tkopen]").forEach((row) => {
        const id = String(row.dataset.tkopen).split(":")[1],
          t = S && (S.tasks || []).find((q) => q.id === id),
          s = t && t.blocked && row.querySelector(".small");
        s && !s.querySelector(".tkr-blk") && s.insertAdjacentHTML("beforeend", ` · <b class="tkr-blk">blocked: ${esc(t.blocked.reason)}</b>`);
      });
      document.querySelectorAll("#v-time .tkr-mine, #v-time .tkr-offers").forEach((c) => c.remove());
      const mine = tkMineCardHtml();
      mine && card.insertAdjacentHTML("beforebegin", mine);
      const off = tkOffersCardHtml();
      off && card.parentNode.insertBefore(document.createRange().createContextualFragment(off), card.parentNode.querySelector(".tkr-mine") || card);
    } catch (e) {
      console.warn("clock tasks", e);
    }
    return r;
  };
}
if ("function" == typeof fRenderToday) {
  const base = fRenderToday;
  fRenderToday = function () {
    const r = base.apply(this, arguments);
    try {
      const root = document.getElementById("ftoday-body");
      root && tkrMount(root, root.querySelector(":scope > .f-hero"));
    } catch (e) {
      console.warn("foreman offers", e);
    }
    return r;
  };
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      if ("home" === view) {
        // above the day's rows, under the chips and the brief
        const list = document.querySelector("#v-home .td2-list");
        if (list) {
          list.parentNode.querySelectorAll(":scope > .tkr-offers").forEach((c) => c.remove());
          const html = tkOffersCardHtml();
          html && list.insertAdjacentHTML("beforebegin", html);
        }
      } else if ("sday" === view) {
        const root = document.getElementById("sday-body");
        root && tkrMount(root, root.querySelector(":scope > .ph"));
      }
    } catch (e) {
      console.warn("offers on Today", e);
    }
    return r;
  };
}

(() => {
  const css = `
.tkr-row{display:flex;align-items:center;gap:10px;min-height:56px;padding:8px 0;border-top:1px solid var(--rule-2);cursor:pointer}
.tkr-row:first-of-type{border-top:0}
.tkr-mid{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:2px}
.tkr-mid b{font-size:16px;line-height:20px;overflow-wrap:anywhere}
.tkr-m{font-size:14px;color:var(--ink-3);line-height:18px}
.tkr-row.late .tkr-m{color:var(--bad,#b3261e)}
.tkr-note{font-size:14px;color:var(--ink-2)}
.tkr-done,.tkr-acts .btn{min-height:44px;min-width:64px;display:inline-flex;align-items:center;justify-content:center;gap:6px;flex:0 0 auto}
.tkr-acts{display:flex;gap:8px;flex:0 0 auto}
.tkr-offer{flex-wrap:wrap}
.card.tkr-offers{border-color:var(--accent)}
@media (max-width:760px){.tkr-offer .tkr-acts{width:100%}.tkr-offer .tkr-acts .btn{flex:1 1 0}}
#toast a,#toast button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;min-width:44px;padding:0 10px;box-sizing:border-box}`;
  try {
    const s = document.createElement("style");
    (s.id = "tkr-css"), (s.textContent = css), document.head.appendChild(s);
  } catch (e) {}
})();
/*<</taskfield.js>>*/
