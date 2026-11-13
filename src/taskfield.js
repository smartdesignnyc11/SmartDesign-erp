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
    meta = [O.meta, x.project, tkrDueSay(x.due)].filter(Boolean).map((m) => esc(m)).join('<span class="tk2-dot"> · </span>');
  return `<div class="tkr-row ${late ? "late" : ""}" data-tkopen="${esc(key)}" role="button" tabindex="0" aria-label="Open ${esc(x.title || "the task")}"><div class="tkr-mid"><b>${esc(x.title || "")}</b>${meta ? `<span class="tkr-m">${meta}</span>` : ""}</div>${
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

// ---- "Needs a Photo": a box on the task, ticked from the title, that the person can untick ---------------------------
// A title match alone was too clever ("Picture frame" asked for a photo). The title only pre-ticks the box (rec.needsPhoto
// unset); once a person ticks or unticks it, their choice is the record's and the title no longer decides.
const TKR_PHOTO_TITLE = /^\s*(photograph|(photos?|pictures?) of|take (a |the )?(photo|picture)s?( of)?)\b/i;
function tkNeedsPhoto(x, rec) {
  if (!x || !/^(sched|action|firm)$/.test(x.kind)) return !1;
  if (rec && "boolean" == typeof rec.needsPhoto) return rec.needsPhoto;
  return TKR_PHOTO_TITLE.test(String(x.title || ""));
}
{
  const base = tdyProofNeed;
  tdyProofNeed = function (x, rec) {
    const n = base.apply(this, arguments);
    if (n || !x || (rec && !1 === rec.proofNeed)) return n;
    return tkNeedsPhoto(x, rec) ? Object.assign({ kind: "photos" }, TDY_PROOF.photos, { label: "Photos of the work" }) : null;
  };
}
{
  const base = tkSheet;
  tkSheet = function (k, opts) {
    const m = base.apply(this, arguments);
    try {
      const R = m && tkResolve(k),
        x = R && R.x,
        rec = R && R.rec,
        done = !!(x && (x.done || (rec && "done" === rec.status)));
      if (!R || !rec || done || !/^(sched|action|firm)$/.test(x.kind) || m.querySelector("[data-tkrneedphoto]")) return m;
      const on = tkNeedsPhoto(x, rec),
        at = m.querySelector(".tks-more") || m.querySelector(".tks");
      at &&
        at.insertAdjacentHTML(
          at.classList.contains("tks-more") ? "beforebegin" : "beforeend",
          `<label class="chk tkr-needphoto"><input type="checkbox" data-tkrneedphoto ${on ? "checked" : ""}> <span class="chk-t"><span>Needs a Photo</span> <span class="small muted">${"boolean" != typeof rec.needsPhoto && on ? "Done asks for one (from the title; untick if not)" : "Done asks for one"}</span></span></label>`,
        );
      const box = m.querySelector("[data-tkrneedphoto]");
      box &&
        (box.onchange = () => {
          rec.needsPhoto = !!box.checked;
          try {
            tkLog(rec, { ev: "needsPhoto", to: rec.needsPhoto });
            audit("task", x.id, "needs-photo", "", String(rec.needsPhoto), "");
          } catch (e) {}
          save();
          toast(`${rec.needsPhoto ? "Done will ask for a photo" : "No photo needed"}: ${tdWords(x.title, 8)}`, [{ label: "Open", run: () => tkSheet(R.key) }]);
        });
    } catch (e) {
      console.warn("needs a photo", e);
    }
    return m;
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
    })())}</p><p>Take a photo of the finished work${x.room ? ` in ${esc(x.room)}` : ""}. The item is done once it is on it.</p><div class="small muted" data-tkrshots>No photo yet.</div><button type="button" class="btn" data-tkrcam>${"undefined" != typeof TDY_IC ? TDY_IC.camera : ""}<span>Take a Photo</span></button>${mbF("No Photo? Say Why", '<input data-f="why" placeholder="e.g. the outlet is behind the vanity, no clear shot">')}`,
    {
      submit: "Mark Done",
      onSubmit: (f) => {
        if (!shots.length) {
          // done without a photo only with the reason on the record (who, when, why)
          if (!f.why) return toast("Add a photo of the finished work, or say why there is none"), !1;
          x.noPhotoWhy = { why: f.why, by: tkrMe().name || fWho(), at: appNowIso() };
          try {
            log(`Punch done without a photo: ${x.item || ""} (${f.why})`, "field", x.noPhotoWhy.by);
            audit("punch", x.id, "done-no-photo", "", f.why, x.noPhotoWhy.by);
          } catch (e) {}
          then && then();
          return !0;
        }
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
      title: prTxt(c),
      meta: [t.blocked && "function" == typeof tkBlockSay ? tkBlockSay(t) : "", "milestone" === t.type ? "milestone" : "", t.owner, t.start ? `${fmt(t.start)} – ${fmt(t.end)}` : "", "done" === t.status ? "done" : late ? "late" : ""].filter(Boolean).join(" · "),
      late: late || !!t.blocked,
      actEl: chip || null,
    };
  };
}

// ---- Clock In over a day already on the clock: the punch is made (a person on site is never refused the clock; the
// driver's Clock In on Route is pinned by w1trust_test), and it carries the day it overlaps, so the hours are not counted
// twice without anyone seeing it: the punch says so, the toast says so, and the foreman has it to sort out.
function tkClockCovers(emp, at) {
  const ms = new Date(at).getTime();
  return (DB.time || []).find((t) => t.empId === emp.id && t.in && t.out && new Date(t.in).getTime() <= ms && ms < new Date(t.out).getTime()) || null;
}
// Clock In looks at today before it punches (the crew's review, 11-12: a first Clock In on a day already closed and sent
// made a second punch for the foreman to sort out, and said so only afterwards). A day of today's that is closed and
// sent for approval is said first, with Start Another Shift: the person decides, nothing is punched until they do.
// A lunch break (a closed punch not yet sent) is not asked about. The automatic clock asks the same way (tkGeoTick).
function tkTodaySent(emp) {
  const td = today();
  return (DB.time || [])
    .filter((t) => emp && t.empId === emp.id && t.date === td && t.in && t.out && (/^(submitted|approved)$/.test(String(t.status || "")) || t.payrollId))
    .sort((a, b) => String(a.in).localeCompare(String(b.in)));
}
function tkTodaySentSay(sent) {
  const spans = sent.map((t) => `${stampTime(t.in)} to ${stampTime(t.out)}`).join(" and "),
    ahead = sent.some((t) => String(t.out) > String(appNowIso()));
  return { spans: spans, ahead: ahead, fore: tkFirst((tdyRoleUser("foreman") || {}).name || "the foreman") };
}
function tkAnotherShiftSheet(sent, go) {
  const s = tkTodaySentSay(sent),
    m = mbModal(
      "Today Is Already Sent",
      `<p>Your ${esc(fmt(today()))} hours, ${esc(s.spans)}, are already sent for approval.</p><p class="small muted">${s.ahead ? `That day ends after now, so a new punch overlaps it: both are marked, the hours are not counted twice, and ${esc(s.fore)} picks one.` : "Clocking in again starts a second shift for today. The first one stays as it is."}</p>`,
      { submit: "Start Another Shift", onSubmit: () => (setTimeout(go, 0), !0) },
    ),
    c = m && m.querySelector("#mbm-cancel");
  c && (c.textContent = "Not Now");
  return m;
}
if ("function" == typeof clockEvent) {
  const base = clockEvent;
  clockEvent = async function (kind, opts) {
    let emp = null,
      hit = null;
    try {
      emp = "in" === kind && "function" == typeof myEmp ? myEmp() : null;
      const sent = emp && !(opts && opts.again) && !(DB.time || []).some((t) => t.empId === emp.id && !t.out) ? tkTodaySent(emp) : [];
      if (sent.length) return void tkAnotherShiftSheet(sent, () => clockEvent("in", { again: !0 }));
      hit = emp && tkClockCovers(emp, appNowIso());
    } catch (e) {}
    const r = await base.call(this, kind);
    try {
      const e = hit && (DB.time || []).find((t) => t.empId === emp.id && !t.out && t.id !== hit.id);
      if (e && !e.overlapOf) {
        const sent = /^(submitted|approved|paid|locked)$/.test(String(hit.status || "")),
          fore = tkFirst((tdyRoleUser("foreman") || {}).name || "the foreman");
        e.overlapOf = hit.id;
        e.notes = `${e.notes ? e.notes + " · " : ""}Overlaps the ${fmt(hit.date)} day already on the clock (${stampTime(hit.in)} to ${stampTime(hit.out)})`;
        try {
          audit("time", e.id, "overlap", hit.id, e.in, sent ? "the earlier day was sent" : "");
        } catch (x) {}
        save();
        toast(`Clocked in, but your ${fmt(hit.date)} already runs ${stampTime(hit.in)} to ${stampTime(hit.out)}${sent ? " and was sent for approval" : ""}. Both punches are marked so the hours are not counted twice; ${fore} sorts it out.`, [{ label: "Open", run: () => ("function" == typeof openTime ? openTime(hit.id) : setView("time")) }]);
      }
    } catch (x) {}
    return r;
  };
}

// ---- Done offers a photo (the crew's review, 11-12) -------------------------------------------------------------------
// Done stays one tap. A field person who marks a task done is then offered a photo of the finished work: Add a Photo
// on the toast opens the camera in one tap, the photo lands on the task (the same place a proof photo does), and
// ignoring it skips it. A task that needs proof is not asked this way: its Done already stops for the photo
// (tdyProofSheet). Where Done is pressed: the crew's Clock rows and the foreman's Today rows (their own handlers set
// the line done), and the task sheet (tkToggle).
const tkrField = () => ["foreman", "crew", "driver"].includes("function" == typeof role ? role() : "");
function tkDonePhotoAdd(x) {
  mReadPhoto((url) => {
    const p = tdyProj(x),
      n0 = ((p && p.files) || []).length;
    tdyAddProofPhotos(x, [url]);
    const f = p && (p.files || [])[n0];
    f && ((f.name = `done-${today()}-${f.id}.jpg`), (f.notes = `Finished: ${x.title}`));
    try {
      audit("task", x.id, "photo", "", f ? f.name : "", "added when it was marked done");
    } catch (e) {}
    save(), render();
    toast(`Photo added to ${tdWords(x.title, 8)}`, [{ label: "Open", run: () => tkSheet(t2Key(x)) }]);
  }, "environment");
}
function tkDonePhotoOffer(x, undo) {
  if (!tkrField() || !x || !/^(sched|action|firm)$/.test(x.kind)) return !1;
  // the proof sheet just took its photos: nothing more to ask (earlier progress photos on the task do not count:
  // the offer is for the finished work)
  try {
    const rec = tdyRec(x);
    if (rec && rec.proof && rec.proof.ok && "photos" === rec.proof.kind) return !1;
  } catch (e) {}
  toast(`${tdWords(x.title, 8)}: marked done. Add a photo of the finished work?`, [{ label: "Add a Photo", run: () => tkDonePhotoAdd(x) }].concat(undo ? [{ label: "Undo", run: undo }] : []), 9e3);
  return !0;
}
const tkIsDone = (kind, id, pid) => {
  const t = "function" == typeof tkFind ? tkFind(kind, id, pid) : null;
  return !!t && ("hub" === kind ? !!t.completed : "done" === t.status);
};
// the rows' own Done buttons: read the line before the tap, look again after its handler ran
document.addEventListener(
  "click",
  (e) => {
    const b = e.target && e.target.closest ? e.target.closest("[data-fdone], [data-fm-done]") : null;
    if (!b || b.closest("#mbm") || !tkrField()) return;
    try {
      const id = b.dataset.fdone || b.dataset.fmDone,
        pid = (S && S.id) || "",
        t = tkFind("sched", id, pid);
      if (!t || "done" === t.status) return;
      const was = { status: t.status, actualEnd: t.actualEnd || "", pct: t.pct };
      setTimeout(() => {
        if ("done" !== t.status) return;
        const R = tkResolve(`sched:${id}:${pid}`);
        R &&
          tkDonePhotoOffer(R.x, () => {
            (t.status = was.status), (t.actualEnd = was.actualEnd), void 0 === was.pct ? delete t.pct : (t.pct = was.pct), save(), render(), toast(`Not done after all: ${tdWords(t.name, 8)}`);
          });
      }, 80);
    } catch (err) {
      console.warn("done photo", err);
    }
  },
  !0,
);
// the task sheet's Done, and every other Done that goes through tkToggle
{
  const base = tkToggle;
  tkToggle = function (kind, id, projectId) {
    const was = tkIsDone(kind, id, projectId),
      r = base.apply(this, arguments);
    try {
      !was &&
        tkrField() &&
        setTimeout(() => {
          if (!tkIsDone(kind, id, projectId)) return;
          const R = tkResolve(`${kind}:${id}:${projectId || ""}`);
          R && tkDonePhotoOffer(R.x, () => tkToggle(kind, id, projectId));
        }, 80);
    } catch (e) {}
    return r;
  };
}

// ---- the driver's Route: Receive a Delivery, beside the slip's photo ---------------------------------------------------
// The driver had the slip's photo and nothing to count against. The button opens Deliveries on every job (he drives
// for all of them); Receive on an order there is the one receive sheet: a count per line, Good / Short / Damaged /
// Wrong, the slip's photo.
function tkDriverReceiveMount() {
  if ("route" !== view || "driver" !== role() || !(ROLE_VIEWS.driver || []).includes("recv")) return;
  const card = document.querySelector("#v-route #trk-capture");
  if (!card || card.querySelector("[data-drvrecv]")) return;
  const n = (DB.pos || []).filter((po) => ["issued", "partial"].includes(po.status) && !("function" == typeof poIsSub && poIsSub(po))).length;
  card.insertAdjacentHTML("beforeend", `<button type="button" class="btn trk-big" data-drvrecv style="margin-top:8px">Receive a Delivery</button><div class="small muted" style="margin-top:6px">${n ? `${n} order${1 === n ? "" : "s"} to count in, line by line.` : "Nothing is on order right now."}</div>`);
  card.querySelector("[data-drvrecv]").onclick = () => {
    recvAll = !0;
    setView("recv");
  };
}
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      tkDriverReceiveMount();
    } catch (e) {
      console.warn("driver receive", e);
    }
    return r;
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
// ---- Blocked, from the crew's Clock -----------------------------------------------------------------------------------
// The reason goes to the job's foreman (the foreman on the job's crew list, p.team) as a task of his, and the job's PM
// watches it: a follow-up of the PM's that waits on the foreman (Waiting On), closed with it. "Not safe to work" goes to
// both at once as a safety escalation in the Standard's format, worded as a stop-work so it ranks first (decision
// principle 1). A block nobody has touched by the end of the shift (the site's hours, on the app's clock) escalates to
// the PM. The schedule line says it is blocked on the crew's Clock, the foreman's Today and the job's schedule until the
// foreman's task closes.
const TKR_BLOCK_WHY = ["Waiting on material", "Waiting on another trade", "Need an answer", "Not safe to work", "Other"],
  TKR_UNSAFE = "Not safe to work";
function tkJobForeman(p) {
  const team = p && Array.isArray(p.team) ? p.team : [];
  return (DB.users || []).find((u) => team.includes(u.id) && "foreman" === u.role) || tdyRoleUser("foreman");
}
function tkJobPm(p) {
  try {
    return tdyUserOf(nsJobLead(p)) || tdyRoleUser("pm");
  } catch (e) {
    return tdyRoleUser("pm");
  }
}
function tkShiftEnd(day) {
  let end = "16:30";
  try {
    const h = siteHours();
    h && h.end && (end = h.end);
  } catch (e) {}
  return `${day}T${end}:00`;
}
function tkBlockedSheet(taskId) {
  const p = S,
    t = p && (p.tasks || []).find((q) => q.id === taskId);
  if (!t) return toast("That task is no longer on the schedule");
  const fore = tkJobForeman(p);
  let why = "";
  const m = mbModal(
    `Blocked: ${esc(tdWords(t.name, 6))}`,
    `<p class="small muted" style="margin:0 0 8px">Say what stops the work. It goes to ${esc(tkFirst((fore || {}).name || "the foreman"))} as a task, the PM watches it, and the job shows the line as blocked. Not safe to work goes to both at once.</p><div class="tks-chips" role="radiogroup" aria-label="What stops it">${TKR_BLOCK_WHY.map((w) => `<button type="button" class="tks-chip" role="radio" aria-checked="false" data-tkrwhy="${esc(w)}">${esc(w)}</button>`).join("")}</div>${mbF("What Stops It", '<input data-f="note" placeholder="e.g. no LVL on site, framing can\'t start">')}`,
    {
      submit: "Send to the Foreman",
      onSubmit: (f) => {
        if (!why && !f.note) return toast("Say what stops the work"), !1;
        return tkBlock(p, t, why, f.note) ? !0 : !1;
      },
    },
  );
  m &&
    m.querySelectorAll("[data-tkrwhy]").forEach(
      (b) =>
        (b.onclick = () => {
          why = b.dataset.tkrwhy;
          m.querySelectorAll("[data-tkrwhy]").forEach((y) => (y.classList.toggle("on", y === b), y.setAttribute("aria-checked", String(y === b))));
          const ok = m.querySelector("#mbm-ok");
          ok && (ok.textContent = TKR_UNSAFE === why ? "Stop the Work and Tell Them" : "Send to the Foreman");
        }),
    );
  return m;
}
// the Standard's escalation format: what happened, the impact on cost, schedule and quality, options, recommendation,
// and when the decision is needed
function tkSafetyNote(p, t, reason, me) {
  return [
    `What happened: ${me || "The crew"} stopped ${t.name} at ${shortName(p)}: not safe to work${reason ? ` (${reason})` : ""}.`,
    `Impact: safety first. Cost: none recorded yet. Schedule: ${t.name} holds until it is made safe${t.end ? ` (ends ${fmtL(t.end)})` : ""}. Quality: work on an unsafe site is not done.`,
    "Options: make it safe now and restart; keep the work stopped and move the crew to other work; call the owner.",
    "Recommendation: keep the work stopped in that area until the foreman has seen it and made it safe.",
    `Decide by: now, ${fmtL(today())}, before anyone goes back to it.`,
  ].join("\n");
}
function tkBlock(p, t, why, note) {
  const me = tkrMe(),
    unsafe = TKR_UNSAFE === why,
    reason = [why && "Other" !== why ? why : "", note].filter(Boolean).join(": "),
    fore = tkJobForeman(p),
    pm = tkJobPm(p),
    to = fore && fore.id !== me.id ? fore.name : (pm || {}).name || "",
    src = { field: !0, blocked: t.id, unsafe: unsafe, by: me.name || "" };
  if (!to) return toast("Nobody runs this job's site yet: call the office"), !1;
  const made = crCreateTask({
    title: unsafe ? `Safety: stop work on ${t.name} — not safe to work${note ? `: ${note}` : ""}` : `Blocked: ${t.name} — ${reason}`,
    for: `p:${p.id}`,
    assignee: to,
    due: today(),
    priority: "high",
    notes: unsafe ? tkSafetyNote(p, t, note, me.name) : `${me.name || "The crew"} cannot go on with ${t.name}: ${reason}`,
    source: src,
    handoff: !1,
  });
  if (!made) return !1;
  // the PM: on a safety stop, the same escalation at once; otherwise a follow-up that waits on the foreman
  let watch = null;
  if (pm && pm.name !== to)
    watch = crCreateTask(
      unsafe
        ? { title: `Safety: stop work on ${t.name} — not safe to work${note ? `: ${note}` : ""}`, for: `p:${p.id}`, assignee: pm.name, due: today(), priority: "high", notes: tkSafetyNote(p, t, note, me.name), source: Object.assign({ watchOf: made.id }, src), handoff: !1 }
        : { title: `Watch: ${t.name} is blocked — ${reason}`, for: `p:${p.id}`, assignee: pm.name, due: today(), priority: "med", notes: `${tkFirst(to)} has it. ${me.name || "The crew"} cannot go on: ${reason}. This closes when ${tkFirst(to)}'s task closes; it comes to you at the end of the shift if nobody has touched it.`, waitsOn: to, source: Object.assign({ watchOf: made.id }, src), handoff: !1 },
    );
  try {
    made.rec && (made.rec.link = { kind: "sched", id: t.id });
    watch && watch.rec && (watch.rec.link = { kind: "sched", id: t.id });
    t.blocked = { reason: unsafe ? `not safe to work${note ? `: ${note}` : ""}` : reason, unsafe: unsafe, by: me.name || "", at: appNowIso(), taskId: made.id, watchId: watch ? watch.id : "", to: to, pm: pm ? pm.name : "", escalated: unsafe ? appNowIso() : "" };
    czOn(p, () => log(`${t.name}: ${unsafe ? "STOP WORK, not safe" : "blocked"} — ${reason} (${me.name || "crew"})`, "field", me.name || ""));
    audit("task", t.id, unsafe ? "stop-work" : "blocked", "", reason, me.name || "");
  } catch (e) {}
  save(), render();
  toast(unsafe ? `Work stopped: ${tkFirst(to)}${pm && pm.name !== to ? ` and ${tkFirst(pm.name)}` : ""} have it now` : `Sent to ${tkFirst(to)}: ${t.name} is blocked`, [{ label: "Open", run: () => tkSheet(`action:${made.id}:${p.id}`) }]);
  return !0;
}
// the block's tasks and line, read back: the foreman's task (or null), the line
function tkBlockOf(p, t) {
  const B = t && t.blocked;
  if (!B) return null;
  const a = (p.actions || []).find((x) => x.id === B.taskId) || null;
  return { B: B, a: a };
}
// the end of the shift: an untouched block goes to the PM; a closed one clears the line and its watch
function tkBlockSweep() {
  const now = appNowIso();
  let n = 0;
  (DB.projects || []).forEach((p) =>
    (p.tasks || []).forEach((t) => {
      const R = tkBlockOf(p, t);
      if (!R) return;
      const { B: B, a: a } = R;
      if (!a || "done" === a.status) return void (tkBlockClear(p, t, a), n++);
      // touched: the foreman moved it, wrote on it or handed it on (the crew's own note at creation is not a touch)
      const touched = "todo" !== (a.status || "todo") || (a.thread || []).some((e) => e.by && tkFirst(e.by) !== tkFirst(B.by || "")) || !!a.handoff;
      // the end of the shift it was raised in; raised after hours, the end of the next working day's
      let due = tkShiftEnd(String(B.at).slice(0, 10));
      String(B.at) >= due && (due = tkShiftEnd(nextWork(iso(addDays(parse(String(B.at).slice(0, 10)), 1)))));
      if (B.escalated || touched || now < due) return;
      B.escalated = now;
      const w = (p.actions || []).find((x) => x.id === B.watchId);
      w && ((w.priority = "high"), (w.title = w.title.replace(/^Watch:/, "Escalated:")), (w.due = today()), (w.waitsOn = ""), "waiting" === w.status && (w.status = "todo"));
      try {
        czOn(p, () => log(`${t.name}: blocked since ${stampTime(B.at)} and nobody has picked it up by the end of the shift — escalated to ${B.pm || "the PM"}`, "field", "The assistant"));
        audit("task", t.id, "block-escalated", B.to || "", B.pm || "", "end of shift");
      } catch (e) {}
      n++;
    }),
  );
  return n;
}
function tkBlockClear(p, t, a) {
  const B = t.blocked;
  if (!B) return;
  (t.blockHist = t.blockHist || []).push(Object.assign({}, B, { cleared: appNowIso() }));
  delete t.blocked;
  const w = (p.actions || []).find((x) => x.id === B.watchId);
  w && "done" !== w.status && ((w.status = "done"), (w.completedAt = today()), (w.waitsOn = ""));
  try {
    czOn(p, () => log(`${t.name}: unblocked${a && a.assignee ? ` (${a.assignee})` : ""}`, "field", (tkrMe().name || "")));
  } catch (e) {}
}
// a closed block clears its line at once, whichever list closed it
{
  const base = tkToggle;
  tkToggle = function (kind, id, projectId) {
    const r = base.apply(this, arguments);
    try {
      if ("action" === kind) {
        const p = (DB.projects || []).find((q) => q.id === projectId),
          a = p && (p.actions || []).find((x) => x.id === id),
          t = a && a.source && a.source.blocked && (p.tasks || []).find((q) => q.id === a.source.blocked);
        t && t.blocked && t.blocked.taskId === id && "done" === a.status && (tkBlockClear(p, t, a), save());
      }
    } catch (e) {}
    return r;
  };
}
// where a block shows: the crew's Clock, the foreman's Today's Work, and the job's schedule (the list's row meta)
const tkBlockSay = (t) => (t && t.blocked ? `${t.blocked.unsafe ? "STOPPED, not safe" : "blocked"}: ${t.blocked.unsafe ? t.blocked.reason.replace(/^not safe to work:?\s*/i, "") || "see the foreman" : t.blocked.reason}` : "");
function tkBlockMark(root, sel) {
  root &&
    root.querySelectorAll(sel).forEach((row) => {
      const id = String(row.dataset.tkopen || "").split(":")[1],
        t = S && (S.tasks || []).find((q) => q.id === id),
        s = t && t.blocked && row.querySelector(".small");
      s && !s.querySelector(".tkr-blk") && s.insertAdjacentHTML("beforeend", ` · <b class="tkr-blk">${esc(tkBlockSay(t))}</b>`);
    });
}

// ---- the crew's own answers: a question a crew member asked is answered on his Clock, not only the foreman's Today ----
function tkMyAnswersHtml() {
  const me = tkrMe();
  if (!me.name) return "";
  const first = tkFirst(me.name).toLowerCase(),
    L = ((DB.field || {}).raises || []).filter((r) => "answered" === r.status && tkFirst(r.by || "").toLowerCase() === first);
  if (!L.length) return "";
  return `<div class="card f-card f-you tkr-answers"><div class="hd"><h3>Answered for You</h3><span class="small muted">${L.length}</span></div>${L.map((r) => `<div class="f-row ok"><div class="grow"><b>${esc(tkFirst(r.answeredBy || "The office"))} answered: ${esc(r.title)}</b><span class="small">${esc(r.answer || "")}</span></div><button class="btn sm" data-fack="answer:${esc(r.id)}">Got It</button></div>`).join("")}</div>`;
}

if ("function" == typeof fmClockHome) {
  const base = fmClockHome;
  fmClockHome = function () {
    const r = base.apply(this, arguments);
    try {
      const card = document.getElementById("fm-today");
      if (!card) return r;
      card.querySelectorAll("[data-fm-block]").forEach((b) => (b.onclick = (e) => (e.stopPropagation(), tkBlockedSheet(b.dataset.fmBlock))));
      tkBlockMark(card, ".fm-row[data-tkopen]");
      document.querySelectorAll("#v-time .tkr-mine, #v-time .tkr-offers, #v-time .tkr-answers").forEach((c) => c.remove());
      const mine = tkMineCardHtml();
      mine && card.insertAdjacentHTML("beforebegin", mine);
      const off = tkOffersCardHtml();
      off && card.parentNode.insertBefore(document.createRange().createContextualFragment(off), card.parentNode.querySelector(".tkr-mine") || card);
      const ans = tkMyAnswersHtml();
      if (ans) {
        card.parentNode.insertBefore(document.createRange().createContextualFragment(ans), card.parentNode.querySelector(".tkr-offers") || card.parentNode.querySelector(".tkr-mine") || card);
        "function" == typeof fWireForYou && fWireForYou(card.parentNode.querySelector(".tkr-answers"));
      }
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
      root && tkBlockMark(root, ".f-row[data-tkopen^='sched:']");
    } catch (e) {
      console.warn("foreman offers", e);
    }
    return r;
  };
}
{
  const base = render;
  render = function () {
    // the end-of-shift check runs before the draw, so the screen shows what it did
    try {
      tkBlockSweep() && save();
    } catch (e) {
      console.warn("block sweep", e);
    }
    const r = base.apply(this, arguments);
    try {
      // the office Today shows an offer once, as its row with Accept (td2Model keeps it unfolded); the designer's Today
      // is not that page, so it carries the offers card
      if ("sday" === view) {
        const root = document.getElementById("sday-body");
        root && tkrMount(root, root.querySelector(":scope > .ph"));
      }
    } catch (e) {
      console.warn("offers on Today", e);
    }
    return r;
  };
}

// ---- a photo in a direct or group message ---------------------------------------------------------------------------
// It offered only Share a Record. A photo sent in a thread tied to a job is filed on that job (never shared with the
// client: shareClient stays off); a thread with no job keeps it on the thread itself, read only by its members. The job
// the sender last opened is never used. (The job's own thread keeps the upload it always had.)
async function tkDmPhoto(T, list) {
  const me = tkrMe(),
    pid = T.t.projectId || T.t.pid || "",
    p = pid ? (DB.projects || []).find((q) => q.id === pid) : null,
    ids = [];
  for (const file of list)
    try {
      const img = /^image\//.test(file.type || ""),
        dataUrl = img ? (await compressImage(file)).dataUrl : await readAsDataURL(file),
        size = Math.round(0.75 * dataUrl.length);
      if (size > 4194304) {
        toast(`${file.name} is ${(size / 1048576).toFixed(1)} MB, over the 4 MB limit. Link it from Drive instead.`);
        continue;
      }
      const id = uid("f"),
        rec = { id: id, name: file.name || `photo-${today()}.jpg`, type: file.type || "application/octet-stream", size: size, cat: img ? "photo" : "doc", date: today(), by: me.name || "", link: { kind: "thread", id: T.key }, notes: `Sent in ${T.title}`, shareClient: !1, ai: null, uploadedAt: appNowIso(), dataUrl: dataUrl };
      if (p) {
        (p.files = p.files || []).push(rec);
        try {
          putBlob(id, dataUrl).then((ok) => (rec.persisted = ok));
        } catch (e) {}
      } else (T.t.files = T.t.files || []).push(Object.assign(rec, { private: !0 }));
      ids.push(id);
    } catch (e) {
      console.warn("thread photo", e), toast(`Could not read ${file.name || "the photo"}`);
    }
  if (!ids.length) return;
  const tx = document.getElementById("chat-text"),
    raw = ((tx && tx.value) || "").trim();
  msgPostDm(T, raw, { files: ids });
  tx && (tx.value = "");
  render();
  toast(`${ids.length === 1 ? "Photo" : ids.length + " files"} sent to ${T.title}${p ? `, filed on ${shortName(p)}` : ", kept in this conversation only"}`, [{ label: "Open", run: () => msgOpen(T.key) }]);
}
document.addEventListener(
  "change",
  (e) => {
    const f = e.target;
    if (!f || "chat-file" !== f.id) return;
    let T = null;
    try {
      T = msgCur(msgMe());
    } catch (x) {}
    if (!T || !T.t) return;
    e.stopImmediatePropagation();
    const list = [...(f.files || [])];
    f.value = "";
    list.length && tkDmPhoto(T, list);
  },
  !0,
);
// a thread's own photo shows in its line (the job's files are looked up by the line already)
{
  const base = msgLineHtml;
  msgLineHtml = function (m, T) {
    const h = base.apply(this, arguments);
    try {
      const own = T && T.t && (T.t.files || []).filter((f) => (m.files || []).includes(f.id));
      if (!own || !own.length) return h;
      const imgs = own.map((f) => (/^image\//.test(f.type) ? `<img class="msg-dmimg" src="${esc(f.dataUrl)}" alt="${esc(f.name)}">` : `<span class="pill info">${esc(String(f.name).slice(0, 22))}</span>`)).join("");
      return h.replace(/(<div class="msg-bub[^"]*">)/, `$1<div class="msg-files tkr-dmfiles">${imgs}</div>`);
    } catch (e) {
      return h;
    }
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
.tkr-blk{color:var(--bad,#b3261e)}
.msg-dmimg{display:block;max-width:220px;max-height:260px;border-radius:10px;margin:2px 0 4px}
.tkr-needphoto{display:flex;align-items:center;gap:8px;min-height:44px;margin-top:10px}
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
