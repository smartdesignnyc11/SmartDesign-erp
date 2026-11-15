/*<<fieldclock.js>>*/
/* ==== the field's clock: automatic by location, and payroll that never pays one hour twice (Alan, 11-06) ===========
   Alan, 11-06: "clock in should always be automatic based on location", and for two punches that overlap, option 1:
   "payroll pays everything else and holds the overlapping hours until the foreman picks the right entry".

   Automatic clock-in (tkGeoTick). Once the person has read and accepted the notice (u.geoAck, with who and when in
   the audit trail), a phone inside a job site's radius (p.project.geo, 250 m by default) clocks them in to that job
   with a toast and Undo; outside it for 15 minutes clocks them out at the time they left; another site's radius moves
   them to that job. A fix whose accuracy is worse than the radius never clocks anyone in: it asks. Every punch it
   makes says "automatic, by location", with the distance and the accuracy. Location is kept only at the punch
   (geoIn, geoOut), never as a track. Clock In and Clock Out by hand stay. Without the acknowledgement it is manual.
   Limits, said plainly: a web app hears the location only while it is open or recently used; opening the app at the
   site clocks in on open. True geofencing with the app closed needs a native wrapper (Capacitor's background
   geolocation, or the platforms' own region monitoring), which is not built.

   Overlaps (tkTimeOverlaps). Two entries of one person whose times overlap, neither voided, are held out of the pay
   run whole (paying either side's own part before the pick could pay the wrong one), and the run says
   "Held: N hours, overlap" for that person; everything else pays. The foreman picks: keep one (the other is voided),
   or keep both without the overlap (the later one starts when the earlier ended). The pick writes an audit row; the
   kept hours are paid on the next run; a voided entry is never paid. From the day before the run's cutoff the
   foreman's Today says "Alex's 9/3 hours overlap: pick one before payroll."

   One switch (the foreman's review, 11-12). Automatic clock-in is turned on in one way only: the notice, then I Agree
   (tkGeoNotice, tkGeoAgree), drawn by tkgSwitchMount where each person clocks in (the Clock page; the foreman's
   Today). The old device-wide checkbox on the Clock page said "on" with no notice, no consent and no punch; it is gone
   (src/app.js renderTime), and the one watch on the device (startGeofence) feeds tkGeoTick and nothing else.
   A punch made here is a time entry like any other: it closes by the same rule as a hand punch (timeCloseOut), the
   person's own list and the foreman's Hours to Approve read it (timeMineWaiting, fHoursToApprove in src/app.js), and
   an overlap shows Pick One on the foreman's Crew page from the moment it exists; Approve refuses until he picks
   (timeApprove), and a run typed by hand holds the pair the same as a run built from time (tkHoldOverlaps).

   Design gate (BACKLOG 1.16): no new store. The time entry is the record (DB.time); the acknowledgement rides on the
   person (u.geoAck) and the audit trail; a run's held hours ride on the run (run.held).
--------------------------------------------------------------------------------------------------------------------- */
const TKG_AWAY_MIN = 15,
  TKG_WEAK_MIN = 30,
  TKG_NOTICE_V = 1;
const tkgMe = () => ("function" == typeof currentUser ? currentUser() : null) || {};
const tkgField = () => ["foreman", "crew", "driver"].includes("function" == typeof role ? role() : "");
const tkgEmp = () => ("function" == typeof myEmp ? myEmp() : null);
// where this person clocks in: the foreman's Today, everyone else's Clock page
const tkgHome = () => ((ROLE_VIEWS[role()] || []).includes("time") ? "time" : "ftoday");
const tkgAcked = (u) => !!(u && u.geoAck && u.geoAck.at && !u.geoAck.off);
const tkgJob = (id) => (DB.projects || []).find((p) => p.id === id) || null;
const tkgMs = (s) => new Date(s).getTime();

// ---- the notice: plain words, read once and accepted before anything is automatic -------------------------------------
const TKG_NOTICE = [
  "When your phone is at a job site, the app clocks you in to that job. When you leave the site for more than 15 minutes, it clocks you out at the time you left.",
  "Your location is saved only at the moment of each clock-in and clock-out, with how far you were from the site. It is never saved as a track of where you go.",
  "You can always clock in and out by hand, and you can undo any automatic punch. Your foreman and payroll see which punches were automatic.",
  "SmartDesign uses this for your hours, payroll and job costs only.",
  "After 8 hours 15 minutes on the clock, and at the end of the day, the app asks if you are still working. If nobody answers in 30 minutes, it clocks you out at your last reading on site and you confirm the time.",
];
function tkGeoNotice() {
  const u = tkgMe();
  if (!u.id) return null;
  const m = mbModal(
    "Automatic Clock-In by Location",
    `${TKG_NOTICE.map((p) => `<p>${esc(p)}</p>`).join("")}<p class="small muted">Saying no keeps the clock manual. You can change your mind on the Clock page.</p>`,
    {
      submit: "I Agree",
      onSubmit: () => (tkGeoAgree(u), !0),
    },
  );
  const c = m && m.querySelector("#mbm-cancel");
  c && (c.textContent = "Not Now");
  return m;
}
function tkGeoAgree(u) {
  u.geoAck = { at: appNowIso(), v: TKG_NOTICE_V, lang: u.lang || "en" };
  // the "are you still working" question reaches the phone as a notification while the app is open or in the
  // background, when he allows it; asked here, with the agreement (tkStillNotify)
  try {
    "Notification" in window && "default" === Notification.permission && Notification.requestPermission().catch(() => {});
  } catch (e) {}
  try {
    audit("consent", u.id, "auto-clock-by-location", "", `agreed to notice v${TKG_NOTICE_V}`, u.name || "");
  } catch (e) {}
  save();
  try {
    "function" == typeof askNotify && askNotify();
    startGeofence();
  } catch (e) {}
  render();
  toast("Automatic clock-in is on: the app clocks you in at a job site", [{ label: "Open", run: () => setView(tkgHome()) }]);
}
function tkGeoOff(u) {
  u.geoAck = Object.assign({}, u.geoAck || {}, { off: appNowIso() });
  try {
    audit("consent", u.id, "auto-clock-off", "", "turned off", u.name || "");
    stopGeofence();
  } catch (e) {}
  save(), render();
  toast("Automatic clock-in is off: clock in by hand");
}

// ---- one reading of where the phone is, applied ------------------------------------------------------------------------
// pos {lat, lng, acc}; at: the moment (the app's clock, appNowIso(), unless a test says otherwise)
let tkGeo = { outSince: "", outPos: null, last: null, lastAt: "", timer: null, asked: "", again: "" };
function tkgSiteNear(pos) {
  let best = null;
  (DB.projects || []).forEach((p) => {
    const g = p.project && p.project.geo;
    if (!g) return;
    const d = Math.round(distM(pos, g)),
      rad = g.radius || 250;
    (!best || d < best.d) && (best = { p: p, d: d, rad: rad });
  });
  return best;
}
const tkgSay = (p) => (p && "function" == typeof shortName ? shortName(p) : (p && p.project && p.project.name) || "the site");
function tkgPunchIn(emp, p, pos, at, d, how) {
  const e = {
    id: uid("te"),
    empId: emp.id,
    date: String(at).slice(0, 10),
    in: at,
    out: "",
    breakMin: 0,
    projectId: p.id,
    code: "",
    notes: `Automatic, by location (${d} m from the site, accurate to ${Math.round(pos.acc || 0)} m)`,
    status: "open",
    approvedBy: "",
    geoIn: { lat: pos.lat, lng: pos.lng, acc: Math.round(pos.acc || 0), dist: d },
    geoOut: null,
    source: how || "geo",
    auto: { how: "automatic, by location", dist: d, acc: Math.round(pos.acc || 0) },
    lastOnSite: at,
    work: [],
  };
  // a punch inside a day already on the clock carries it (the pay run holds both until the foreman picks)
  const hit = "function" == typeof tkClockCovers ? tkClockCovers(emp, at) : null;
  hit && ((e.overlapOf = hit.id), (e.notes = `${e.notes} · Overlaps the ${fmt(hit.date)} day already on the clock (${stampTime(hit.in)} to ${stampTime(hit.out)})`));
  DB.time.push(e);
  try {
    audit("time", e.id, "auto-clock-in", null, { projectId: p.id, dist: d, acc: e.auto.acc, at: at });
  } catch (x) {}
  return e;
}
function tkgPunchOut(e, pos, at) {
  const was = { status: e.status, breakMin: e.breakMin || 0, work: (e.work || []).length };
  e.out = at;
  e.geoOut = pos ? { lat: pos.lat, lng: pos.lng, acc: Math.round(pos.acc || 0), dist: null } : null;
  e.autoOut = !0;
  e.auto = Object.assign({}, e.auto || {}, { out: "automatic, by location", was: was });
  // one rule for a punch that closes, by hand or by location (timeCloseOut, src/app.js): work that adds up to the
  // clock sends the day to the foreman; anything else waits on the person, and the foreman still sees it
  "function" == typeof timeCloseOut ? timeCloseOut(e) : "function" == typeof hoursOf && hoursOf(e) >= 6 && !e.breakMin && (e.breakMin = 30);
  try {
    audit("time", e.id, "auto-clock-out", null, { at: at });
  } catch (x) {}
}
function tkgUndoIn(id) {
  const i = (DB.time || []).findIndex((t) => t.id === id);
  if (i < 0) return;
  const e = DB.time[i];
  DB.time.splice(i, 1);
  try {
    audit("time", id, "auto-clock-in-undone", { in: e.in }, null);
  } catch (x) {}
  save(), render(), toast("Clock-in undone");
}
function tkgUndoOut(id) {
  const e = (DB.time || []).find((t) => t.id === id);
  if (!e) return;
  const was = e.out,
    b = e.auto && e.auto.was;
  (e.out = ""), (e.geoOut = null), delete e.autoOut;
  b && ((e.status = b.status), (e.breakMin = b.breakMin), (e.work = (e.work || []).slice(0, b.work)));
  e.auto && (delete e.auto.out, delete e.auto.was);
  tkGeo.outSince = "";
  try {
    audit("time", id, "auto-clock-out-undone", { out: was }, null);
  } catch (x) {}
  save(), render(), toast("Clock-out undone: you are still on the clock");
}
// ---- an automatic punch ends at the last reading on site (the crew expert, 11-15) ---------------------------------------
// A web app hears the phone only while it is open. He left at 4:30 PM and opened the app at home at 7:05 PM: it
// clocked him out at 7:05 (2.6 h too many); he never opened it and the punch ran 33 h, was approved in one tap and paid
// about $1,020 too much. The rule now: every good reading on the punch's own site is kept on the punch (lastOnSite);
// when the next thing the app hears is not on site and comes more than 15 minutes after that reading, or the punch is
// still open on a later day, or runs past 16 hours, or the readings have been too weak to tell for 30 minutes (or past
// the site's day), the punch is closed at that last reading on site and held (timeHold, src/app.js) until he says
// when he left. Held hours count 0 (hoursOf) and no Approve and no pay run passes them (timePayBlock).
const tkgAuto = (t) => !!t && ("geo" === t.source || !!t.auto);
const tkgMinOf = (at) => {
  const m = new Date(at);
  return 60 * m.getHours() + m.getMinutes();
};
// why an open automatic punch can no longer be taken as still running at `at` ("" when it can). how: "inside" (a good
// reading on its own site), "away" (the first good reading anywhere else), "weak" (a reading too weak to act on),
// "none" (nobody's phone said anything: the boot sweep, or someone looking at the punch)
function timeAutoStale(t, at, how) {
  if (!tkgAuto(t) || t.out || !t.in || !at) return "";
  const last = t.lastOnSite || t.in,
    gap = tkgMs(at) - tkgMs(last);
  if (!(gap >= 0)) return "";
  if (String(at).slice(0, 10) > String(t.date)) return "still open on a later day";
  if (tkgMs(at) - tkgMs(t.in) > TIME_MAX_H * 36e5) return `open more than ${TIME_MAX_H} hours`;
  if ("inside" === how) return "";
  const p = tkgJob(t.projectId),
    sh = siteHours(p || S),
    late = tkgMinOf(at) > hmToMin(sh.end);
  if ("away" === how) return gap > TKG_AWAY_MIN * 6e4 ? "no reading on site since" : "";
  if ("cont" === how) return "";
  const weak = t.weakSince && tkgMs(at) - tkgMs(t.weakSince);
  if (t.weakSince && (weak >= TKG_WEAK_MIN * 6e4 || late)) return "location too weak to tell when you left";
  return "";
}
// close it at the last reading on site and hold it; the person is told on the Clock page until he answers
function tkgHoldAuto(t, why) {
  const out = t.lastOnSite || t.in;
  timeHold(t, out, "the last reading on site");
  t.autoOut = !0;
  t.geoOut = null;
  t.auto = Object.assign({}, t.auto || {}, { out: "automatic, at the last reading on site", heldWhy: why });
  delete t.weakSince;
  tkGeo.outSince = "";
  tkGeo.outPos = null;
  return out;
}
// what a held punch says to its person: one made by location ends at the last reading on site; a hand punch says why
const tkgHoldSay = (t) =>
  tkgAuto(t) ? `Clocked out automatically at ${stampTime(t.out)}, your last reading on site. Confirm when you left.` : `The app clocked you out at ${stampTime(t.out)}: ${(t.hold && t.hold.why) || "nobody clocked out"}. Say when you left.`;
// The sweep: every open automatic punch, whoever's, read against now. It runs as the app draws (when anyone looks
// at a punch), at boot, and each new day (APP_DAY_HOOKS).
function tkPunchSweep(now) {
  const at = now || appNowIso(),
    L = (DB.time || []).filter((t) => tkgAuto(t) && !t.out && t.in);
  let n = 0;
  L.forEach((t) => {
    const why = timeAutoStale(t, at, "none");
    why && (tkgHoldAuto(t, why), n++);
  });
  // a hand punch still open on a later day: closed at its 8 h 15 mark or the end of its work day, whichever is earlier,
  // and held; the hours count 0 until he says when he left
  const W = tkgWindow();
  (DB.time || [])
    .filter((t) => !tkgAuto(t) && t.in && !t.out && !t.payrollId && String(t.date) < String(at).slice(0, 10) && !/^(void|rejected)$/.test(String(t.status || "")))
    .forEach((t) => {
      const mark = tkgIsoAt(tkgMs(t.in) + TKG_STILL_H * 36e5);
      let out = [mark, `${t.date}T${W.end}:00`].sort()[0];
      String(out) <= String(t.in) && (out = mark);
      timeHold(t, out, "nobody clocked out");
      n++;
    });
  n && save();
  return n;
}
// notifications: asked once, at a Clock In tap or with the automatic clock-in agreement (a browser asks only on a tap)
function tkNotifyAsk() {
  try {
    "Notification" in window && "default" === Notification.permission && Notification.requestPermission().catch(() => {});
  } catch (e) {}
}
"undefined" != typeof APP_DAY_HOOKS && APP_DAY_HOOKS.push(["tkPunchSweep", () => (tkPunchSweep(), tkStillCheck(), !0)]);
function tkGeoTick(pos, at0) {
  const at = at0 || appNowIso(),
    u = tkgMe(),
    emp = "function" == typeof myEmp ? myEmp() : null;
  if (!pos || !emp) return { did: "none", why: "no position or no employee" };
  if (!tkgAcked(u)) return { did: "none", why: "no acknowledgement" };
  tkGeo.last = pos;
  tkGeo.lastAt = at;
  const near = tkgSiteNear(pos),
    inside = !!near && near.d <= near.rad,
    poor = (+pos.acc || 0) > ((near && near.rad) || 250);
  let open = (DB.time || []).find((t) => t.empId === emp.id && !t.out),
    held = null;
  tkGeo.weak = poor;
  // an automatic punch the app can no longer vouch for ends at its last reading on site, held (timeAutoStale)
  if (tkgAuto(open)) {
    poor && (open.weakSince = open.weakSince || at);
    const how = poor ? "weak" : inside && near.p.id === open.projectId ? "inside" : tkGeo.outSince && tkGeo.outFor === open.id ? "cont" : "away",
      why = timeAutoStale(open, at, how);
    if (why) {
      tkgHoldAuto(open, why);
      held = open;
      open = null;
      save();
    } else if ("inside" === how) {
      open.lastOnSite = at;
      delete open.weakSince;
    }
  }
  const heldSay = held ? tkgHoldSay(held) : "",
    heldAct = held ? [{ label: "Confirm", run: () => tkHoldSheet(held) }] : [];
  if (held && !(inside && !poor)) {
    render();
    toast(heldSay, heldAct);
    return { did: "held", id: held.id, at: held.out, why: held.auto.heldWhy };
  }
  // a poor fix never clocks anyone in or out on its own: near a site and not on the clock, it asks
  if (poor) {
    if (!open && near && near.d <= near.rad + (+pos.acc || 0) && tkGeo.asked !== near.p.id) {
      tkGeo.asked = near.p.id;
      toast(`Your location is not precise enough (within ${Math.round(pos.acc)} m) to clock you in on its own. At ${tkgSay(near.p)}?`, [
        { label: "Clock In", run: () => ("function" == typeof setCurrent && setCurrent(near.p.id), clockEvent("in")) },
      ]);
      return { did: "asked", why: "poor fix" };
    }
    return { did: "none", why: "poor fix" };
  }
  // inside a site: clock in, or move from another job
  if (inside) {
    const wasOut = open && tkGeo.outSince && tkGeo.outFor === open.id ? { at: tkGeo.outSince, pos: tkGeo.outPos } : null;
    tkGeo.outSince = "";
    tkGeo.outPos = null;
    if (open && open.projectId === near.p.id) return save(), { did: "none", why: "on the clock here" };
    // the window (tkgWindow, the owner's one setting): nothing punches outside it, and he is told once, with Clock In
    // by hand. On site before it opens, the punch starts when it opens, and says so.
    const day = String(at).slice(0, 10),
      W = tkgWindow(),
      openIso = `${day}T${W.start}:00`;
    let inAt = at,
      early = "";
    if (!open && !tkgWatching(near.p, at)) {
      const before = W.days.includes(new Date(at).getDay()) && String(at) < openIso;
      before && (tkGeo.early = { pid: near.p.id, day: day, pos: pos, at: at });
      const k = "hours|" + near.p.id + "|" + day + "|" + (before ? "early" : "out");
      tkGeo.asked !== k &&
        ((tkGeo.asked = k),
        toast(before ? `You are at ${tkgSay(near.p)} before automatic clock-in starts at ${stampTime(openIso)}. Clock in by hand for time before ${tkgHmShort(W.start)}.` : `${tkgWindowSay()} Clock in by hand now.`, [
          { label: "Clock In", run: () => ("function" == typeof setCurrent && setCurrent(near.p.id), clockEvent("in")) },
        ]));
      return { did: "none", why: before ? "before the window" : "outside the window" };
    }
    if (!open && tkGeo.early && tkGeo.early.pid === near.p.id && tkGeo.early.day === day && tkgMs(at) - tkgMs(tkGeo.early.at) <= TKG_AWAY_MIN * 6e4) {
      // his readings had him on site before the window opened and this one, within 15 minutes, still does: the punch
      // starts at the opening. With a longer gap the app does not know he stayed: it starts at this reading.
      inAt = String(at) > openIso ? openIso : at;
      early = `Clocked in at ${stampTime(openIso)}, when automatic clock-in starts. You arrived earlier: clock in by hand for time before ${tkgHmShort(W.start)}.`;
    }
    tkGeo.early = null;
    // today is already closed and sent for approval: the app asks, it does not punch a second shift on its own
    const sent = !open && String(at).slice(0, 10) === today() && "function" == typeof tkTodaySent ? tkTodaySent(emp) : [];
    if (sent.length && tkGeo.again !== near.p.id + "|" + today()) {
      const key = "sent|" + near.p.id + "|" + today();
      if (tkGeo.asked === key) return { did: "none", why: "today already sent; asked" };
      tkGeo.asked = key;
      const s = tkTodaySentSay(sent);
      // the question stays on the Clock page until he answers it (tkSentAskHtml), not in a toast that asks once
      tkGeo.sentAsk = { pid: near.p.id, pos: pos, at: at, test: !!at0, ids: sent.map((t) => t.id), spans: s.spans };
      render();
      toast(`You are at ${tkgSay(near.p)}, and your ${fmt(today())} hours (${s.spans}) are already sent for approval.`, [
        { label: "Start Another Shift", run: () => tkSentAnswer("again") },
        { label: "Those Hours Aren't Mine", run: () => tkSentAnswer("notmine") },
      ]);
      return { did: "asked", why: "today already sent" };
    }
    if (open) {
      const from = tkgJob(open.projectId),
        // he was seen leaving the first site: its punch ends then, not on arrival at the next (lunch and the drive
        // are on neither job)
        left = wasOut ? wasOut.at : at;
      tkgPunchOut(open, (wasOut && wasOut.pos) || pos, left);
      const e = tkgPunchIn(emp, near.p, pos, at, near.d);
      save(), render();
      toast(`Moved to ${tkgSay(near.p)} at ${stampTime(at)}${from ? `, out of ${tkgSay(from)} at ${stampTime(left)}` : ""}`, [
        { label: "Undo", run: () => (tkgUndoIn(e.id), tkgUndoOut(open.id)) },
      ]);
      return { did: "switch", id: e.id, from: open.id };
    }
    const e = tkgPunchIn(emp, near.p, pos, inAt, near.d);
    e.lastOnSite = at;
    try {
      "function" == typeof setCurrent && (!S || S.id !== near.p.id) && setCurrent(near.p.id);
    } catch (x) {}
    save(), render();
    const hit = e.overlapOf && (DB.time || []).find((t) => t.id === e.overlapOf);
    toast(
      (early
        ? early
        : hit
        ? `Clocked in at ${tkgSay(near.p)}, ${stampTime(at)}. Your ${fmt(hit.date)} already runs ${stampTime(hit.in)} to ${stampTime(hit.out)}: both punches are marked so the hours are not counted twice, and your foreman picks one.`
        : `Clocked in at ${tkgSay(near.p)}, ${stampTime(at)}`) + (held ? `. Your ${fmt(held.date)} punch: ${heldSay}` : ""),
      held ? [{ label: "Undo", run: () => tkgUndoIn(e.id) }].concat(heldAct) : [{ label: "Undo", run: () => tkgUndoIn(e.id) }],
    );
    return held ? { did: "in", id: e.id, held: held.id } : { did: "in", id: e.id };
  }
  inside || poor || (tkGeo.early = null);
  // outside every site, on the clock: away for 15 minutes clocks out at the time they left
  if (open) {
    if (!tkGeo.outSince || tkGeo.outFor !== open.id) {
      tkGeo.outSince = at;
      tkGeo.outPos = pos;
      tkGeo.outFor = open.id;
      clearTimeout(tkGeo.timer);
      tkGeo.timer = setTimeout(() => tkGeo.last && tkGeoTick(tkGeo.last, appNowIso()), TKG_AWAY_MIN * 6e4 + 1e3);
      return { did: "none", why: "left; waiting 15 minutes" };
    }
    if (tkgMs(at) - tkgMs(tkGeo.outSince) < TKG_AWAY_MIN * 6e4) return { did: "none", why: "away less than 15 minutes" };
    const left = tkGeo.outSince,
      p = tkgJob(open.projectId);
    tkgPunchOut(open, tkGeo.outPos || pos, left);
    tkGeo.outSince = "";
    tkGeo.outPos = null;
    save(), render();
    toast(`Clocked out at ${tkgSay(p)}, ${stampTime(left)}`, [{ label: "Undo", run: () => tkgUndoOut(open.id) }]);
    return { did: "out", id: open.id, at: left };
  }
  return { did: "none", why: "not at a site" };
}
// ---- the window automatic clock-in watches: one setting, the owner's (Alan, 11-15: "7am to 5pm") ---------------------
// DB.company.autoClock = { days, start, end }: Monday to Friday, 7:00 AM to 5:00 PM unless the owner changes it in
// Company Settings, The Clock and the Demo (tkgWindowEdit). Everything reads it here: the punch (no automatic punch
// before the start; on site earlier, the punch starts at the start), the question at the end (tkStillCheck), the
// switch and the Clock page (not watching now, clock in by hand), the foreman's flag on time outside it (timeFlags).
const TKG_WIN_DEF = { days: [1, 2, 3, 4, 5], start: "07:00", end: "17:00" },
  TKG_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
function tkgWindow() {
  const w = (DB.company && DB.company.autoClock) || {};
  return { days: Array.isArray(w.days) && w.days.length ? w.days.map(Number) : TKG_WIN_DEF.days, start: /^\d\d:\d\d$/.test(w.start || "") ? w.start : TKG_WIN_DEF.start, end: /^\d\d:\d\d$/.test(w.end || "") ? w.end : TKG_WIN_DEF.end };
}
const tkgHmShort = (hm) => stampTime(`${today()}T${hm}:00`).replace(/:00(?= ?[AP]M)/i, "");
function tkgDaysSay(D) {
  const d = [...D].sort((a, b) => a - b);
  return d.join() === "1,2,3,4,5" ? "Monday to Friday" : d.join() === "0,1,2,3,4,5,6" ? "every day" : d.map((x) => TKG_DAYS[x]).join(", ");
}
function tkgWindowSay() {
  const W = tkgWindow();
  return `Automatic clock-in runs ${stampTime(`${today()}T${W.start}:00`)} to ${stampTime(`${today()}T${W.end}:00`)}, ${tkgDaysSay(W.days)}.`;
}
function tkgWatching(p, at) {
  const W = tkgWindow(),
    a = String(at || appNowIso()),
    d = a.slice(0, 10);
  return W.days.includes(new Date(a).getDay()) && a >= `${d}T${W.start}:00` && a <= `${d}T${W.end}:00`;
}
// the owner changes the window: who, when and the window before and after are recorded
function tkgWindowSet(w, why) {
  const before = tkgWindow(),
    after = { days: (w.days || before.days).map(Number), start: w.start || before.start, end: w.end || before.end };
  if (!(after.start < after.end) || !after.days.length) return "The window needs at least one day, and the start before the end";
  DB.company = DB.company || {};
  const by = tkgMe().name || "";
  DB.company.autoClock = Object.assign({}, after, { by: by, at: appNowIso() });
  try {
    audit("company", "autoClock", "work-day-changed", before, after, why || by);
  } catch (x) {}
  save();
  return "";
}
function tkgWindowRowMeta() {
  return tkgWindowSay().replace(/^Automatic clock-in runs /, "").replace(/\.$/, "");
}
function tkgWindowEdit() {
  if (!("function" == typeof isOwner && isOwner())) return toast("Only the owner changes when automatic clock-in runs"), null;
  const W = tkgWindow(),
    m = mbModal(
      "Automatic Clock-In Hours",
      `<p class="small muted" style="margin:0 0 8px">No automatic punch starts before the start. At the end, anyone still clocked in is asked if they are still working. Outside these hours the crew clocks in by hand.</p><div class="grid2"><div class="f"><label>Starts</label><input type="time" data-f="start" value="${esc(W.start)}"></div><div class="f"><label>Ends</label><input type="time" data-f="end" value="${esc(W.end)}"></div></div><div class="f"><label>Days</label><div class="tks-chips">${[1, 2, 3, 4, 5, 6, 0].map((d) => `<label class="pill neutral"><input type="checkbox" data-f="d${d}" ${W.days.includes(d) ? "checked" : ""}> ${TKG_DAYS[d]}</label>`).join("")}</div></div>`,
      {
        submit: "Save",
        onSubmit: (f) => {
          const days = [0, 1, 2, 3, 4, 5, 6].filter((d) => f["d" + d]),
            bad = tkgWindowSet({ days: days, start: f.start, end: f.end });
          if (bad) return toast(bad), !1;
          render();
          toast(`${tkgWindowSay()} Saved.`, [{ label: "Open", run: () => setView("cosettings") }]);
          return !0;
        },
      },
    );
  return m;
}
// ---- "Are you still working?" (Alan, 11-15: "after 8 hours and 15 minutes it should send them a notification") -------
// When a person's time on the clock for the day reaches 8 h 15 min (every punch of that day, lunch clock-outs left out,
// automatic or by hand), or an automatic punch is still open when the window ends, the punch asks once. Still Working
// keeps it running and is recorded on the punch (who, when), and it asks again an hour later while it stays open.
// No answer in 30 minutes: the punch is closed and held (timeHold) for him to confirm, and the foreman sees it held on
// his crew list; nothing keeps paying on silence. It closes at his last reading on site after the last thing that
// said he was working (the 8 h 15 mark or his last Still Working), else at that moment; at the window's end, at the
// end or his last reading on site, whichever is earlier.
// What a phone receives: the question is on the Clock page and the foreman's Today, and when notifications are allowed
// (asked with the automatic clock-in agreement) the browser shows it while the app is open or in the background. With
// the app closed nothing arrives from this: the hosted copy can push (platform/sw.src.js, lib/push.mjs) but no server
// job sends this question yet, so the 30-minute rule carries the money safety the next time anyone opens the app.
const TKG_STILL_H = 8.25,
  TKG_STILL_WAIT = 30,
  TKG_STILL_EVERY = 60;
const tkgIsoAt = (ms) => appIso(new Date(ms));
const tkgHmin = (h) => `${Math.floor(h + 1e-6)} h ${Math.round((h - Math.floor(h + 1e-6)) * 60)} min`;
// the day's time on the clock up to `at` (a punch whose recorded end is later counts only to `at`)
function tkStillDayH(t, at) {
  return timeHoursOf((DB.time || []).filter((x) => x.empId === t.empId && x.date === t.date && String(x.in) <= String(at)).map((x) => (x.out && String(x.out) > String(at) ? Object.assign({}, x, { out: at }) : x)), at);
}
function tkStillCheck(now) {
  const at = now || appNowIso();
  let n = 0;
  (DB.time || [])
    .filter((t) => t.in && !t.out && !t.payrollId && String(t.in) <= String(at) && !/^(void|rejected)$/.test(String(t.status || "")))
    .forEach((t) => {
      const s = t.still,
        W = tkgWindow(),
        endIso = `${t.date}T${W.end}:00`,
        atEnd = tkgAuto(t) && W.days.includes(new Date(`${t.date}T12:00:00`).getDay()) && String(at) >= endIso;
      if (s && s.askedAt) {
        if (tkgMs(at) - tkgMs(s.askedAt) < TKG_STILL_WAIT * 6e4) return;
        // silence: close and hold. A punch made by location ends at his last reading on site, never at a time the
        // clock chose (Alan, 11-15: "based on geo location"); a hand punch at what last said he was working (the
        // 8 h 15 mark, or his last Still Working)
        const last = s.answers && s.answers.length ? s.answers[s.answers.length - 1].at : "";
        let out = tkgAuto(t) ? t.lastOnSite || t.in : [s.mark, last].filter(Boolean).sort().pop() || s.askedAt;
        String(out) < String(t.in) && (out = t.in);
        String(out) > String(at) && (out = at);
        timeHold(t, out, "no answer to Still Working");
        t.autoOut = tkgAuto(t) || void 0;
        Object.assign(s, { askedAt: "", closedAt: at, closedOut: out });
        try {
          audit("time", t.id, "still-working-unanswered", null, { out: out, asked: s.n });
        } catch (x) {}
        n++;
        return;
      }
      const h = tkStillDayH(t, at),
        long = h >= TKG_STILL_H && (!s || !s.next || String(at) >= String(s.next)),
        end = atEnd && !(s && s.endAsked);
      if (!long && !end) return;
      const x = (t.still = s || { answers: [], n: 0 });
      x.mark || !(h >= TKG_STILL_H) || (x.mark = tkgIsoAt(Math.round((tkgMs(at) - (h - TKG_STILL_H) * 36e5) / 6e4) * 6e4));
      Object.assign(x, { askedAt: at, why: end ? "end" : "long", n: (x.n || 0) + 1, h: r2(h) });
      end && (x.endAsked = at);
      try {
        audit("time", t.id, "still-working-asked", null, { at: at, h: r2(h), why: x.why });
      } catch (y) {}
      n++;
      (tkgEmp() || {}).id === t.empId && tkStillNotify(t);
    });
  n && save();
  return n;
}
function tkStillSay(t) {
  const s = t && t.still;
  return s && "end" === s.why ? `It is ${stampTime(`${t.date}T${tkgWindow().end}:00`)}, when automatic clock-in stops. Are you still working?` : `You have been clocked in ${tkgHmin(Math.max(TKG_STILL_H, (s && s.h) || TKG_STILL_H))}. Are you still working?`;
}
// the browser's own notification, when the person allowed it: while the app is open or in the background
function tkStillNotify(t) {
  try {
    if (!("Notification" in window) || "granted" !== Notification.permission) return !1;
    const body = esT ? esT(tkStillSay(t)) : tkStillSay(t),
      o = { body: body, tag: "still-" + t.id, renotify: !0 };
    navigator.serviceWorker && navigator.serviceWorker.controller
      ? navigator.serviceWorker.ready.then((r) => r.showNotification("SmartDesigns Projects", o))
      : new Notification("SmartDesigns Projects", o);
    return !0;
  } catch (e) {
    return !1;
  }
}
function tkStillAnswer(t, how) {
  const s = t && t.still;
  if (!s || !s.askedAt) return;
  const by = tkgMe().name || "",
    at = appNowIso();
  if ("yes" === how) {
    (s.answers = s.answers || []).push({ at: at, by: by });
    s.askedAt = "";
    s.next = tkgIsoAt(tkgMs(at) + TKG_STILL_EVERY * 6e4);
    try {
      audit("time", t.id, "still-working", null, { at: at, by: by });
    } catch (x) {}
    save(), render();
    return void toast(`Still working, recorded at ${stampTime(at)}. Asked again at ${stampTime(s.next)}.`, [{ label: "Open", run: () => setView(tkgHome()) }]);
  }
  // Clock Out: when he left, defaulting to his last reading on site
  const def = (tkgAuto(t) && t.lastOnSite) || at;
  mbModal(
    "When Did You Leave",
    `<div class="f"><label>Left At</label><input type="time" data-f="out" value="${esc(String(def).slice(11, 16))}"></div><p class="small muted" style="margin:6px 0 0">Clocked in ${esc(stampTime(t.in))}.${tkgAuto(t) && t.lastOnSite ? ` Your last reading on site was ${esc(stampTime(t.lastOnSite))}.` : ""}</p>`,
    {
      submit: "Clock Out",
      onSubmit: (f) => {
        const out = `${t.date}T${f.out || String(def).slice(11, 16)}:00`;
        if (out <= t.in || out > appNowIso()) return toast("The time you left has to be after you clocked in, and not later than now"), !1;
        t.out = out;
        timeCloseOut(t);
        Object.assign(s, { askedAt: "", clockedOut: { at: appNowIso(), by: by, out: out } });
        try {
          audit("time", t.id, "clock-out-asked", null, { out: out, by: by });
        } catch (x) {}
        save(), render();
        toast(`Clocked out at ${stampTime(out)}: ${hoursOf(t).toFixed(1)} h. Log what you worked on to send the day.`, [{ label: "Open", run: () => setView(tkgHome()) }]);
        return !0;
      },
    },
  );
}
function tkStillHtml() {
  const emp = tkgEmp(),
    t = emp && (DB.time || []).find((x) => x.empId === emp.id && !x.out && x.still && x.still.askedAt);
  return t
    ? `<div class="card f-card tkh-card warn" data-tkstill="${esc(t.id)}"><div class="small"><b>${esc(tkStillSay(t))}</b></div><div class="tkh-acts"><button type="button" class="btn primary" data-tksa="yes">Still Working</button><button type="button" class="btn" data-tksa="out">Clock Out</button></div></div>`
    : "";
}
// on the foreman's crew list: who is past 8 h 15 today, and what they said
function tkStillCrewSay(t) {
  const s = t && t.still;
  if (!s) return "";
  const last = s.answers && s.answers.length ? s.answers[s.answers.length - 1] : null;
  return s.askedAt ? `past 8 h 15, asked at ${stampTime(s.askedAt)}, no answer yet` : last ? `past 8 h 15, still working (said ${stampTime(last.at)})` : "";
}
// ---- today already sent: three answers, asked on the Clock page until one is given ------------------------------------
function tkSentAnswer(how) {
  const a = tkGeo.sentAsk;
  if (!a) return;
  tkGeo.sentAsk = null;
  if ("no" === how) return void render();
  "notmine" === how && tkNotMine(a.ids);
  tkGeo.again = a.pid + "|" + today();
  const r = tkGeoTick(a.pos, a.test ? a.at : appNowIso());
  "notmine" === how && r && "in" === r.did && toast(`Clocked in. ${tkTodaySentSay([]).fore} is told the earlier ${fmt(today())} hours are not yours and checks them before anything is approved.`, [{ label: "Open", run: () => setView(tkgHome()) }]);
  return r;
}
// "Those hours aren't mine": the earlier punches are flagged to the foreman (timeFlags; timeApproveBlock refuses them
// until he checks them and says why, in Fix)
function tkNotMine(ids) {
  const me = tkgMe().name || "";
  (DB.time || [])
    .filter((t) => (ids || []).includes(t.id) && !t.payrollId)
    .forEach((t) => {
      t.notMine = { by: me, at: appNowIso() };
      try {
        audit("time", t.id, "not-mine", null, { by: me });
      } catch (x) {}
    });
  save();
}
function tkSentAskHtml() {
  const a = tkGeo.sentAsk,
    p = a && tkgJob(a.pid);
  if (!a || !p) return "";
  return `<div class="card f-card tkh-card warn" data-tkhsent><div class="small"><b>You are at ${esc(tkgSay(p))}, and your ${esc(fmt(today()))} hours (${esc(a.spans)}) are already sent.</b> Is this another shift?</div><div class="tkh-acts"><button type="button" class="btn" data-tkhsa="again">Start Another Shift</button><button type="button" class="btn" data-tkhsa="notmine">Those Hours Aren't Mine</button><button type="button" class="btn" data-tkhsa="no">Not Now</button></div></div>`;
}
// ---- a held punch: the person says when they left (or the foreman, with a reason) -------------------------------------
function tkHoldSheet(e) {
  if (!e || !timeHeld(e)) return null;
  const mine = (tkgEmp() || {}).id === e.empId,
    who = String(empName(e.empId)).split(" ")[0];
  return mbModal(
    "When Did You Leave",
    `<p class="small" style="margin:0 0 8px">${esc(mine ? tkgHoldSay(e) : `The app closed ${who}'s ${fmt(e.date)} punch at ${stampTime(e.out)}, the last reading on site.`)}</p><div class="f"><label>Left At</label><input type="time" data-f="out" value="${esc(String(e.out).slice(11, 16))}"></div>${mine ? "" : `<div class="f"><label>Why (required)</label><input data-f="why" placeholder="e.g. Called him: he left at 4:30"></div>`}<p class="small muted" style="margin:6px 0 0">Clocked in ${esc(stampTime(e.in))}. Until this is confirmed the hours are not approved or paid.</p>`,
    {
      submit: "Confirm",
      onSubmit: (f) => {
        if (!mine && !String(f.why || "").trim()) return toast("Say why: you are correcting someone else's time"), !1;
        const by = tkgMe().name || "",
          bad = timeHoldConfirm(e, `${e.date}T${f.out || String(e.out).slice(11, 16)}:00`, by, mine ? `confirmed by ${by}` : f.why);
        if (bad) return toast(bad), !1;
        save(), render();
        toast(`${mine ? "Your" : `${who}'s`} ${fmt(e.date)} hours: ${stampTime(e.in)} to ${stampTime(e.out)}, ${hoursOf(e).toFixed(1)} h.${"submitted" === e.status ? " Sent for approval." : " Log the work to send the day."}`, [{ label: "Open", run: () => setView(mine ? tkgHome() : (ROLE_VIEWS[role()] || []).includes("fcrew") ? "fcrew" : "time") }]);
        return !0;
      },
    },
  );
}
function tkHoldHtml(L) {
  return L.map(
    (e) =>
      `<div class="card f-card tkh-card warn" data-tkhold="${esc(e.id)}"><div class="small"><b>${esc(fmt(e.date))}: ${esc(tkgHoldSay(e))}</b> Until you do, these hours are not approved or paid.</div><div class="tkh-acts"><button type="button" class="btn" data-tkhok="${esc(e.id)}">Confirm When I Left</button></div></div>`,
  ).join("");
}
// drawn where the person clocks in: the Clock page, the foreman's Today
function tkHoldMount() {
  const emp = tkgEmp();
  if (!emp) return;
  const host = "time" === view ? document.getElementById("clock-card") : "ftoday" === view && "foreman" === role() ? document.querySelector("#ftoday-body .f-hero") : null;
  document.querySelectorAll(".tkh-card").forEach((c) => c.remove());
  if (!host || !host.parentNode) return;
  const L = (DB.time || []).filter((t) => t.empId === emp.id && timeHeld(t) && !t.payrollId),
    html = tkStillHtml() + tkHoldHtml(L) + tkSentAskHtml();
  if (!html) return;
  "time" === view ? host.insertAdjacentHTML("beforebegin", html) : host.insertAdjacentHTML("afterend", html);
  document.querySelectorAll("[data-tkhok]").forEach((b) => (b.onclick = () => tkHoldSheet((DB.time || []).find((t) => t.id === b.dataset.tkhok))));
  document.querySelectorAll("[data-tkhsa]").forEach((b) => (b.onclick = () => tkSentAnswer(b.dataset.tkhsa)));
  document.querySelectorAll("[data-tksa]").forEach((b) => (b.onclick = () => tkStillAnswer((DB.time || []).find((t) => t.id === b.closest("[data-tkstill]").dataset.tkstill), b.dataset.tksa)));
}
// The watch itself is startGeofence (src/app.js): one watch, every reading to tkGeoTick. It runs for a person with an
// employee record who accepted the notice, and for nobody else (one person's phone, one person's choice).
{
  const base = render;
  render = function () {
    // whoever looks: an open automatic punch the app can no longer vouch for is closed at its last reading on site
    // and held, before anything reads it (tkPunchSweep)
    try {
      (DB.time || []).some((t) => t.in && !t.out) && tkPunchSweep();
      (DB.time || []).some((t) => t.in && !t.out) && tkStillCheck();
      // on site before the window opened, and the window is open now: the punch starts (tkGeoTick)
      // only on a current reading (the last one, within 15 minutes): the opening itself never starts a punch
      tkGeo.early && tkGeo.last && tkGeo.lastAt && tkgMs(appNowIso()) - tkgMs(tkGeo.lastAt) <= TKG_AWAY_MIN * 6e4 && tkgAcked(tkgMe()) && tkgWatching(null, appNowIso()) && tkGeoTick(tkGeo.last, appNowIso());
    } catch (e) {
      console.warn("punch sweep", e);
    }
    const r = base.apply(this, arguments);
    try {
      const u = tkgMe();
      if (tkgEmp() && tkgAcked(u)) null == geoWatch && startGeofence();
      else null != geoWatch && stopGeofence();
      tkgSwitchMountAll();
      tkOverlapMount();
      tkHoldMount();
    } catch (e) {
      console.warn("field clock", e);
    }
    return r;
  };
}
// THE switch (11-12): the one control that turns automatic clock-in on or off, wherever it is drawn. Off: one button
// that opens the notice. On: what it does, and Turn Off. On with no location: it says the clock is still by hand,
// because "on" must mean a punch really happens on arrival.
function tkgSwitchHtml(u) {
  if (!tkgAcked(u)) return `<button type="button" class="btn tkg-on" data-tkgon>Turn On Automatic Clock-In</button><div class="small muted">Read what it does first. Until you agree, the clock is manual.</div>`;
  const err = "undefined" != typeof clockState && clockState && clockState.err,
    noSite = "undefined" != typeof S && S && S.project && !S.project.geo;
  // when it is not watching (outside its window) and when the readings are too weak to act on, it says so
  const more = ` <span data-tkglimit>Automatic clock-in works while this app is open. With the app closed it cannot see you arrive or leave: clock in by hand, and confirm when you left.</span>${tkgWatching(S) ? "" : ` <span class="bad-t" data-tkgwindow>It is not watching now: clock in by hand now.</span>`}${tkGeo.weak ? ` <span class="bad-t" data-tkgweak>Your location is not reliable right now: clock out by hand when you leave.</span>` : ""}`;
  return err
    ? `<div class="small tkg-say"><b class="bad-t">Automatic clock-in is on, but the app cannot read your location.</b> Clock in by hand until this phone allows location for the app. ${esc(tkgWindowSay(S))}${more}</div><button type="button" class="btn sm" data-tkgoff>Turn Off</button>`
    : `<div class="small tkg-say"><b>Automatic clock-in is on.</b> The app clocks you in at a job site while it is open. ${esc(tkgWindowSay(S))}${noSite ? ` <span class="bad-t" data-tkgnosite>This job has no site location yet: clock in by hand here.</span>` : ""}${more}</div><button type="button" class="btn sm" data-tkgoff>Turn Off</button>`;
}
function tkgSwitchMount(host, how) {
  if (!host) return null;
  const u = tkgMe();
  let box = host.parentNode && host.parentNode.querySelector(":scope > .tkg-card");
  "inside" === how && (box = host.querySelector(":scope > .tkg-card"));
  box || ((box = document.createElement("div")), (box.className = "tkg-card"), "inside" === how ? host.appendChild(box) : host.insertAdjacentElement("afterend", box));
  box.innerHTML = tkgSwitchHtml(u);
  const b1 = box.querySelector("[data-tkgon]"),
    b2 = box.querySelector("[data-tkgoff]");
  b1 && (b1.onclick = () => tkGeoNotice());
  b2 && (b2.onclick = () => tkGeoOff(u));
  return box;
}
// where it is drawn: the Clock page for anyone with an employee record; the foreman's Today, under his Clock In
function tkgSwitchMountAll() {
  if (!tkgMe().id || !tkgEmp() || ("undefined" != typeof clockState && clockState && clockState.blocked)) return;
  if ("time" === view) tkgSwitchMount(document.querySelector("#v-time #geo-line"));
  else if ("ftoday" === view && "foreman" === role()) tkgSwitchMount(document.querySelector("#ftoday-body .f-hero"), "inside");
}
// the person's own row on the phone's Clock page: when, where, and whether the app made the punch
if ("undefined" != typeof PR_SPECS) {
  PR_SPECS.time = (tr) => {
    const emp = tkgEmp(),
      t = tkgField() && emp ? (DB.time || []).find((x) => "time:" + x.id === tr.dataset.edit) : null;
    if (!t || t.empId !== emp.id) return null;
    const p = tkgJob(t.projectId),
      auto = "geo" === t.source || !!t.auto,
      ov = tkOverlapFor(t),
      st = t.payrollId ? ["paid", "ok"] : timeHeld(t) ? ["confirm when you left", "warn"] : "approved" === t.status ? ["approved", "ok"] : "rejected" === t.status ? ["rejected", "bad"] : "void" === t.status ? ["not counted", ""] : "submitted" === t.status ? ["to approve", "info"] : t.out ? ["needs details", "warn"] : ["on the clock", "ok"];
    return {
      title: t.out ? `${fmt(t.date)} · ${stampTime(t.in)} to ${stampTime(t.out)}` : `Clocked in ${auto ? "automatically " : ""}at ${stampTime(t.in)}`,
      chip: { t: st[0], tone: st[1] },
      meta: [t.out ? `${hoursClock(t).toFixed(1)} h` : "", ov ? "overlaps another punch" : "", t.out && auto ? "automatic" : "", p ? tkgSay(p) : ""].filter(Boolean).join(" · "),
      late: !!ov,
    };
  };
}

// ---- overlapping punches: held from payroll until the foreman picks ---------------------------------------------------
const tkgLive = (t) => t && !/^(void|rejected)$/.test(String(t.status || ""));
function tkTimeOverlaps(empId) {
  const now = appNowIso(),
    by = {};
  (DB.time || []).filter((t) => tkgLive(t) && t.in && (!empId || t.empId === empId)).forEach((t) => (by[t.empId] = by[t.empId] || []).push(t));
  const out = [];
  Object.entries(by).forEach(([eid, L]) => {
    L.sort((a, b) => String(a.in).localeCompare(String(b.in)));
    for (let i = 0; i < L.length; i++)
      for (let j = i + 1; j < L.length; j++) {
        const a = L[i],
          b = L[j],
          s = Math.max(tkgMs(a.in), tkgMs(b.in)),
          e = Math.min(tkgMs(a.out || now), tkgMs(b.out || now));
        if (e - s > 6e4) {
          const emp = (DB.employees || []).find((x) => x.id === eid) || {};
          out.push({ empId: eid, name: emp.name || "", a: a, b: b, h: r2((e - s) / 36e5), date: a.date });
        }
      }
  });
  return out;
}
// the overlaps still to pick (a pair whose two punches are both paid is history): all, one job's, or one entry's
function tkOverlapsOpen(pid) {
  return tkTimeOverlaps().filter((o) => !(o.a.payrollId && o.b.payrollId) && (!pid || o.a.projectId === pid || o.b.projectId === pid));
}
function tkOverlapFor(t) {
  if (!t || !t.empId || !tkgLive(t)) return null;
  return tkTimeOverlaps(t.empId).find((o) => (o.a.id === t.id || o.b.id === t.id) && !(o.a.payrollId && o.b.payrollId)) || null;
}
const tkOverlapSpan = (t) => `${stampTime(t.in)} to ${t.out ? stampTime(t.out) : "now"}`;
function tkHeldOf(run) {
  return (run && run.held) || [];
}
// Anything that puts hours on a run does it inside this: the entries in an overlap still to pick read as held for the
// length of the call, so neither side can be paid. A run built from time, and a run typed by hand that covers their
// dates (prLinkTime), both go through it.
function tkHoldOverlaps(fn) {
  const O = tkTimeOverlaps(),
    hold = new Map();
  O.forEach((o) => [o.a, o.b].forEach((t) => !t.payrollId && hold.set(t.id, { t: t, st: t.status })));
  hold.forEach(({ t }) => (t.status = "held-overlap"));
  try {
    return { r: fn(), O: O, hold: hold };
  } finally {
    hold.forEach(({ t, st }) => "held-overlap" === t.status && (t.status = st));
  }
}
if ("function" == typeof prLinkTime) {
  const base = prLinkTime;
  prLinkTime = function () {
    const a = arguments,
      self = this;
    return tkHoldOverlaps(() => base.apply(self, a)).r;
  };
}
// the run recorded for wages accrued at a close with no run (ctOrphanRecordRun) is built from approved time too
if ("function" == typeof ctOrphanRecordRun) {
  const base = ctOrphanRecordRun;
  ctOrphanRecordRun = function () {
    const a = arguments,
      self = this;
    return tkHoldOverlaps(() => base.apply(self, a)).r;
  };
}
if ("function" == typeof payrollFromTime) {
  const base = payrollFromTime;
  payrollFromTime = function () {
    // the entries in an unresolved overlap stay out of the run; everything else pays
    const a = arguments,
      self = this,
      H = tkHoldOverlaps(() => base.apply(self, a)),
      run = H.r,
      O = H.O,
      hold = H.hold;
    try {
      if (run) {
        const per = {};
        O.forEach((o) => {
          if (!hold.has(o.a.id) && !hold.has(o.b.id)) return;
          const x = (per[o.empId] = per[o.empId] || { empId: o.empId, name: o.name, hours: 0, pairs: [] });
          (x.hours = r2(x.hours + o.h)), x.pairs.push([o.a.id, o.b.id]);
        });
        run.held = Object.values(per);
        run.held.length &&
          (run.notes = `${String(run.notes || "").replace(/ Held: .*$/, "")} Held: ${run.held.map((x) => `${x.name} ${x.hours} h, overlap`).join("; ")} (the foreman picks; paid on the next run).`);
        save();
      }
    } catch (e) {
      console.warn("payroll hold", e);
    }
    return run;
  };
}
// the run's review: "Held: N hours, overlap" for each person
if ("function" == typeof openPayroll) {
  const base = openPayroll;
  openPayroll = function (id) {
    const r = base.apply(this, arguments);
    try {
      const run = (DB.payroll || []).find((x) => x.id === id),
        H = tkHeldOf(run),
        body = document.getElementById("d-body");
      if (body && H.length && !body.querySelector(".tkg-held"))
        body.insertAdjacentHTML(
          "afterbegin",
          `<div class="note warn tkg-held">${H.map((x) => `<div><b>Held: ${x.hours} hours, overlap</b> · ${esc(x.name)}: two punches claim the same time. Nothing is paid twice; the foreman picks one and it is paid on the next run.</div>`).join("")}</div>`,
        );
    } catch (e) {}
    return r;
  };
}
// the cutoff: two working days before pay day; the foreman's reminder starts the day before it
function tkPayCutoff(day) {
  const P = payPeriodOf(day || today());
  return addWork(P.payDate, -2);
}
// From the moment an overlap exists (11-12: it showed only from the day before the cutoff, and only on Today), the
// foreman has it with Pick One: on Today, and on Crew beside the person and in Hours to Approve (fRenderCrew).
function tkHoldDue() {
  return tkOverlapsOpen();
}
// one overlap, said the same way wherever the foreman meets it
function tkOverlapRowHtml(o, i, how) {
  const head = "crew" === how ? `${esc(tkFirst(o.name))} · ${esc(fmt(o.date))} · two punches overlap` : `${esc(tkFirst(o.name))}'s ${esc(fmt(o.date))} hours overlap: pick one before payroll.`;
  return `<div class="f-row warn tkg-ov" data-tkgov="${esc(o.a.id)}|${esc(o.b.id)}"><div class="grow"><b>${head}</b><span class="small">${esc(tkOverlapSpan(o.a))} and ${esc(tkOverlapSpan(o.b))} · ${o.h} h held</span></div><button type="button" class="btn sm" data-tkgpick="${i}">Pick One</button></div>`;
}
function tkOverlapWire(root, L) {
  root && root.querySelectorAll("[data-tkgpick]").forEach((b) => (b.onclick = () => tkOverlapPick(L[+b.dataset.tkgpick])));
}
function tkOverlapMount() {
  if ("ftoday" !== view || "foreman" !== role()) return;
  const root = document.getElementById("ftoday-body");
  if (!root) return;
  root.querySelectorAll(".tkg-remind").forEach((c) => c.remove());
  const L = tkHoldDue();
  if (!L.length) return;
  const html = `<div class="card f-card tkg-remind"><div class="hd"><h3>Before Payroll</h3><span class="small muted">${L.length}</span></div>${L.map((o, i) => tkOverlapRowHtml(o, i)).join("")}</div>`;
  const at = root.querySelector(":scope > .tkr-offers") || root.querySelector(":scope > .f-hero");
  at ? at.insertAdjacentHTML("afterend", html) : root.insertAdjacentHTML("afterbegin", html);
  tkOverlapWire(root.querySelector(".tkg-remind"), L);
}
// the foreman's pick: keep one (the other is voided), or keep both without the overlap
// which punch is which, said plainly on the Pick One sheet (the crew expert, 11-15): how it was made, where it stands
function tkPunchHow(t) {
  const how = tkgAuto(t) ? "automatic, by location" : "manual" === t.source ? "typed in by the office" : "clocked by hand";
  const st = t.payrollId ? "paid" : "approved" === t.status ? "approved" : "submitted" === t.status ? "sent for approval" : t.out ? "not sent yet" : "still open";
  return `${how}, ${st}`;
}
function tkOverlapPick(o) {
  if (!o) return;
  const span = tkOverlapSpan,
    paidA = !!o.a.payrollId,
    paidB = !!o.b.payrollId;
  let pick = "";
  const m = mbModal(
    `${esc(tkFirst(o.name))}'s ${esc(fmt(o.date))} Hours`,
    `<p class="small muted" style="margin:0 0 8px">Two punches claim ${o.h} hours of the same time. Payroll holds them until you pick; nothing is paid twice.</p>${[o.a, o.b].map((t) => `<p class="small" style="margin:0 0 4px" data-tkgwhich>${esc(`${span(t)}: ${tkPunchHow(t)}.`)}</p>`).join("")}<div class="tks-chips" role="radiogroup">${[
      ["a", `Keep ${span(o.a)}`, paidB],
      ["b", `Keep ${span(o.b)}`, paidA],
      ["both", "Keep Both, Without the Overlap", !1],
    ]
      .filter(([, , no]) => !no)
      .map(([k, l]) => `<button type="button" class="tks-chip" role="radio" aria-checked="false" data-tkgk="${k}">${esc(l)}</button>`)
      .join("")}</div>`,
    {
      submit: "Pick",
      onSubmit: () => (pick ? (tkOverlapResolve(o, pick), !0) : (toast("Pick which hours are right"), !1)),
    },
  );
  m &&
    m.querySelectorAll("[data-tkgk]").forEach(
      (b) =>
        (b.onclick = () => {
          pick = b.dataset.tkgk;
          m.querySelectorAll("[data-tkgk]").forEach((y) => (y.classList.toggle("on", y === b), y.setAttribute("aria-checked", String(y === b))));
        }),
    );
  return m;
}
function tkOverlapResolve(o, pick) {
  const me = tkgMe().name || "",
    voidIt = (t, why) => {
      t.voidedFrom = t.status;
      t.status = "void";
      t.voidWhy = why;
    };
  if ("a" === pick) voidIt(o.b, `overlapped ${o.a.id}; ${me} kept the other punch`);
  else if ("b" === pick) voidIt(o.a, `overlapped ${o.b.id}; ${me} kept the other punch`);
  else {
    // the later punch starts when the earlier one ended; a punch left with no time is voided
    const [first, later] = tkgMs(o.a.in) <= tkgMs(o.b.in) ? [o.a, o.b] : [o.b, o.a],
      end = first.out || appNowIso();
    later.trimmedFrom = later.in;
    later.in = end;
    later.out && tkgMs(later.out) <= tkgMs(later.in) && voidIt(later, `nothing left after the overlap with ${first.id}`);
  }
  try {
    audit("time", o.a.id, "overlap-picked", { a: o.a.id, b: o.b.id }, { pick: pick }, me);
  } catch (e) {}
  save(), render();
  toast(`${tkFirst(o.name)}'s ${fmt(o.date)} hours: ${"both" === pick ? "both kept, without the overlap" : "one punch kept, the other voided"}. Paid on the next run.`, [{ label: "Open", run: () => setView((ROLE_VIEWS[role()] || []).includes("fcrew") ? "fcrew" : "time") }]);
}

(() => {
  const css = `
.tkg-card{margin-top:8px;display:flex;flex-direction:column;gap:6px}
.tkg-card .btn{min-height:44px}
.tkg-card .btn{align-self:flex-start}
.tkg-card .tkg-say,.tkg-card .tkg-say b{font-size:13px;line-height:1.4;font-weight:400}
.tkg-card .tkg-say b{font-weight:600}
.f-hero>.tkg-card{margin-top:10px;text-align:left;flex:1 1 100%}
.tkg-ov .btn{min-height:44px;white-space:nowrap}
.tkg-held{margin-bottom:10px}
.tkh-card{margin:0 0 10px;display:flex;flex-direction:column;gap:8px}
.tkh-acts{display:flex;flex-wrap:wrap;gap:8px}
.tkh-acts .btn{min-height:44px}`;
  try {
    const s = document.createElement("style");
    (s.id = "tkg-css"), (s.textContent = css), document.head.appendChild(s);
  } catch (e) {}
})();
/*<</fieldclock.js>>*/
