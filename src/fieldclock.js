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
  // the app's own sight of the end (timeSeenEnd, src/app.js): a later end given afterwards needs the approver's reason
  e.seenOut = at;
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
  (e.out = ""), (e.geoOut = null), delete e.autoOut, delete e.seenOut;
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
      W = tkgWindowOf(near.p),
      openIso = `${day}T${W.start}:00`;
    let inAt = at,
      early = "";
    if (!open && !tkgWatching(near.p, at)) {
      const before = W.days.includes(new Date(at).getDay()) && String(at) < openIso;
      before && (tkGeo.early = { pid: near.p.id, day: day, pos: pos, at: at });
      const k = "hours|" + near.p.id + "|" + day + "|" + (before ? "early" : "out");
      tkGeo.asked !== k &&
        ((tkGeo.asked = k),
        toast(before ? `You are at ${tkgSay(near.p)} before automatic clock-in starts at ${stampTime(openIso)}. Clock in by hand for time before ${tkgHmShort(W.start)}.` : `${tkgWindowSay(near.p)} Clock in by hand now.`, [
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
  // allowMin: how much later than his last reading on site a confirmed time may be before the approver must say why
  return { days: Array.isArray(w.days) && w.days.length ? w.days.map(Number) : TKG_WIN_DEF.days, start: /^\d\d:\d\d$/.test(w.start || "") ? w.start : TKG_WIN_DEF.start, end: /^\d\d:\d\d$/.test(w.end || "") ? w.end : TKG_WIN_DEF.end, allowMin: +w.allowMin >= 0 && "" !== w.allowMin && null != w.allowMin ? +w.allowMin : 15 };
}
const tkgHmShort = (hm) => stampTime(`${today()}T${hm}:00`).replace(/:00(?= ?[AP]M)/i, "");
function tkgDaysSay(D) {
  const d = [...D].sort((a, b) => a - b);
  return d.join() === "1,2,3,4,5" ? "Monday to Friday" : d.join() === "0,1,2,3,4,5,6" ? "every day" : d.map((x) => TKG_DAYS[x]).join(", ");
}
// the window of one job: the firm's work day, or the job's own hours where it has them (siteHours, src/app.js)
function tkgWindowOf(p) {
  const h = p && "function" == typeof siteHours ? siteHours(p) : null;
  return h && h.own ? { days: h.days || [1, 2, 3, 4, 5], start: h.start, end: h.end, own: h.own, allowMin: tkgWindow().allowMin } : tkgWindow();
}
function tkgWindowSay(p) {
  const W = p ? tkgWindowOf(p) : tkgWindow();
  return `${W.own ? "This job's own hours: a" : "A"}utomatic clock-in runs ${stampTime(`${today()}T${W.start}:00`)} to ${stampTime(`${today()}T${W.end}:00`)}, ${tkgDaysSay(W.days)}.`;
}
function tkgWatching(p, at) {
  const W = tkgWindowOf(p || ("undefined" != typeof S ? S : null)),
    a = String(at || appNowIso()),
    d = a.slice(0, 10);
  return W.days.includes(new Date(a).getDay()) && a >= `${d}T${W.start}:00` && a <= `${d}T${W.end}:00`;
}
// the owner changes the window: who, when and the window before and after are recorded
function tkgWindowSet(w, why) {
  const before = tkgWindow(),
    after = { days: (w.days || before.days).map(Number), start: w.start || before.start, end: w.end || before.end, allowMin: null != w.allowMin && "" !== w.allowMin ? Math.max(0, +w.allowMin || 0) : before.allowMin };
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
      `<p class="small muted" style="margin:0 0 8px">No automatic punch starts before the start. At the end, anyone still clocked in is asked if they are still working. Outside these hours the crew clocks in by hand.</p><div class="grid2"><div class="f"><label>Starts</label><input type="time" data-f="start" value="${esc(W.start)}"></div><div class="f"><label>Ends</label><input type="time" data-f="end" value="${esc(W.end)}"></div></div><div class="f"><label>Minutes Allowed Past the Last Reading</label><input type="number" min="0" step="5" inputmode="numeric" data-f="allow" value="${esc(String(W.allowMin))}"><span class="hint">A time someone confirms later than this past the app's last reading of them on site needs the approver's reason.</span></div><div class="f"><label>Days</label><div class="tks-chips">${[1, 2, 3, 4, 5, 6, 0].map((d) => `<label class="pill neutral"><input type="checkbox" data-f="d${d}" ${W.days.includes(d) ? "checked" : ""}> ${TKG_DAYS[d]}</label>`).join("")}</div></div>`,
      {
        submit: "Save",
        onSubmit: (f) => {
          const days = [0, 1, 2, 3, 4, 5, 6].filter((d) => f["d" + d]),
            bad = tkgWindowSet({ days: days, start: f.start, end: f.end, allowMin: f.allow });
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
// the question comes 15 minutes past the expected day (TIME_DAY_H, src/app.js)
const TKG_STILL_H = ("undefined" != typeof TIME_DAY_H ? TIME_DAY_H : 8) + 0.25,
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
        W = tkgWindowOf(tkgJob(t.projectId)),
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
  return s && "end" === s.why ? `It is ${stampTime(`${t.date}T${tkgWindowOf(tkgJob(t.projectId)).end}:00`)}, when automatic clock-in stops. Are you still working?` : `You have been clocked in ${tkgHmin(Math.max(TKG_STILL_H, (s && s.h) || TKG_STILL_H))}. Are you still working?`;
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
    `<p class="small" style="margin:0 0 8px">${esc(tkgAuto(e) ? `The app last saw ${mine ? "you" : who} on site at ${stampTime(e.out)}. When did ${mine ? "you" : "he"} leave?` : mine ? tkgHoldSay(e) : `The app closed ${who}'s ${fmt(e.date)} punch at ${stampTime(e.out)}: ${(e.hold && e.hold.why) || "nobody clocked out"}.`)}</p><p class="small muted" style="margin:0 0 8px">A phone with the app closed sends no readings. A time more than ${esc(String(tkgWindow().allowMin))} minutes after that goes to your foreman with both times.</p><div class="f"><label>Left At</label><input type="time" data-f="out" value="${esc(String(e.out).slice(11, 16))}"></div>${mine ? "" : `<div class="f"><label>Why (required)</label><input data-f="why" placeholder="e.g. Called him: he left at 4:30"></div>`}<p class="small muted" style="margin:6px 0 0">Clocked in ${esc(stampTime(e.in))}. Until this is confirmed the hours are not approved or paid.</p>`,
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
      labPickMount();
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
    ? `<div class="small tkg-say"><b class="bad-t">Automatic clock-in is on, but the app cannot read your location.</b> <span>Clock in by hand until this phone allows location for the app.</span> <span data-tkgwin>${esc(tkgWindowSay(S))}</span>${more}</div><button type="button" class="btn sm" data-tkgoff>Turn Off</button>`
    : `<div class="small tkg-say"><b>Automatic clock-in is on.</b> <span>The app clocks you in at a job site while it is open.</span> <span data-tkgwin>${esc(tkgWindowSay(S))}</span>${noSite ? ` <span class="bad-t" data-tkgnosite>This job has no site location yet: clock in by hand here.</span>` : ""}${more}</div><button type="button" class="btn sm" data-tkgoff>Turn Off</button>`;
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
const tkgLive = (t) => t && !t.forDate && !/^(void|rejected)$/.test(String(t.status || ""));
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

/* ==== two labour rules (Alan, 11-15: "Yes to both"; BACKLOG section 12) ============================================
   Rule 1. Hours logged, not clocked. Only clocked, approved time is job cost and payroll (jobFin and payrollFromTime
   read DB.time, never a daily log). Hours a daily log gives an hourly field person (the crew rows of a signed log)
   with no punch behind them for that person, day and job are rows of ONE flag per job on the job lead's Caught for
   You (nsJobLead: the job's PM, else the firm's PM, else the owner): "N hours logged, not clocked", Review, and the
   sheet has one row per person, day and log with Approve as Time and Dismiss. Nothing is cost or pay until a person
   decides. Approve as Time makes one time entry (source "log", fromLog) carrying who, when (the app's clock) and why;
   Dismiss records who and why on the log (l.timeDecisions[empId]) and the row does not come back for that log. A log
   edited after approval makes no second entry: the difference is a row of its own ("changed after approval"), and
   approving it changes the one entry (or, once that entry is paid, adds a separate entry for the added hours).
   Hourly or salaried: the employee record says neither (DB.employees carry rate and burden only), so the rule reads
   emp.payType when a record has one, and otherwise the department (empDept): construction is hourly field time;
   office and design staff never raise it.
   Rule 2. Hours on a cost code with no estimate line. Once a field person is on the clock, their Clock page (the
   foreman's Today) asks which line: the job's estimate and approved change-order lines (jobFinEacLines), most likely
   first (today's tasks they are on), four at a time, with Other, which asks for a note. Clocked cost that still sits on
   a code no line carries (jobFin's eacUnlined, the Budget's "Not on an Estimate Line" row) is a proposal on the job
   lead's Caught for You, and the same buttons on that Budget row: Move to a Line (the likely line picked) or Draft a
   Change Order. Nothing moves by itself. A move is recorded on each entry (moves: who, when, from, to, why) and keeps
   its hours; an entry dated in a closed month moves as of the open day (postOn), so the closed month's job cost by
   code reads as it was reported (timeCodeAt in src/app.js, read by jobFin) and the job's estimate today takes it.
   Design gate (BACKLOG 1.16): no new store, list, queue or menu item. The flag and the proposal are CATCH entries
   (Caught for You); the decisions ride on the daily log and the time entry; the line picker is part of the clock.
--------------------------------------------------------------------------------------------------------------------- */
const LAB_LIVE = (t) => !!t && !/^(void|rejected)$/.test(String(t.status || ""));
const labEmp = (id) => (DB.employees || []).find((x) => x.id === id) || null;
const labJob = (id) => (DB.projects || []).find((p) => p.id === id) || null;
const labMe = () => ("function" == typeof currentUser ? currentUser() : null) || {};
const labJobName = (p) => (p ? ("function" == typeof shortName ? shortName(p) : p.project.name) : "the job");
function labHourly(emp) {
  if (!emp || !1 === emp.active) return !1;
  if (emp.payType) return "hourly" === String(emp.payType).toLowerCase();
  if (emp.salaried) return !1;
  return "construction" === empDept(emp);
}
// Who decides for a job: its lead (the PM named on it, else the firm's PM, else the owner)
function labLead(p) {
  let u = null;
  try {
    u = tdyUserOf(nsJobLead(p));
  } catch (e) {}
  return u || (DB.users || []).find((x) => "owner" === x.role) || null;
}
function labMine(p) {
  const me = labMe(),
    L = labLead(p);
  if (!me.id || !["pm", "owner"].includes(role())) return !1;
  return L ? L.id === me.id || ("owner" === role() && "owner" === L.role) : "owner" === role();
}
// Was this person already paid for this day (the crew expert, 11-15, round 2: Logged, Not Clocked read 224 h, about
// $10,239 "not in cost or payroll", for days pay run pr1 had paid)? The pay run whose dates cover the day: one built
// from time paid the punches it holds; one typed by hand paid the people its lines name, or, with no lines, everyone
// of its entity when its headcount says so (pr1: 6 employees, the six of ent1). { run, paid, open } or null.
const LAB_RUN_SHUT = /^(submitted|approved|paid|posted|verified)$/;
// who decides a job's Logged, Not Clocked on Approvals: its lead (nsJobLead), as Caught for You has it
"object" == typeof DELEGATION &&
  (DELEGATION.lognc = {
    role: "pm",
    rule: "hours on a daily log with no punch behind them are the job lead's: approve as time or dismiss",
    who: (it) => {
      const L = labLead(labJob(String(it.id).split(":")[1]));
      return (L && L.role) || "pm";
    },
  });
function labPaidBy(empId, day) {
  const emp = labEmp(empId),
    ent = (emp && emp.entityId) || "ent1";
  let hit = null;
  for (const r of DB.payroll || []) {
    if (/^(rejected|void)$/.test(String(r.status || ""))) continue;
    const to = r.fromTime ? payPeriodOf(r.from).to : r.to || payPeriodOf(r.from).to;
    if (!(day >= r.from && day <= to)) continue;
    const mine = prParts(r).some((x) => (x.entityId || "ent1") === ent);
    let paid = !1;
    if (mine) {
      if (r.fromTime) paid = (DB.time || []).some((t) => t.payrollId === r.id && t.empId === empId && t.date === day);
      else {
        const names = (r.detail || []).map((d) => d.name);
        paid = names.length ? !!emp && names.includes(emp.name) : +r.employees >= (DB.employees || []).filter((e) => (e.entityId || "ent1") === ent && !1 !== e.active).length;
      }
    }
    if (paid) return { run: r, paid: !0 };
    hit = hit || { run: r, paid: !1 };
  }
  return hit && { run: hit.run, paid: !1, shut: LAB_RUN_SHUT.test(String(hit.run.status || "")) };
}
// ---- Rule 1: every row still to decide, all jobs or one --------------------------------------------------------------
function labUnclocked(pid) {
  const out = [];
  ((DB.field && DB.field.logs) || [])
    .filter((l) => (!pid || l.projectId === pid) && !/^(draft|void)$/.test(String(l.status || "")))
    .forEach((l) =>
      (l.crew || []).forEach((cw) => {
        if (!cw.empId) return;
        const emp = labEmp(cw.empId);
        if (!labHourly(emp)) return;
        const logged = r2(+cw.hours || 0),
          D = (l.timeDecisions || {})[cw.empId],
          rate = laborRate(emp);
        if (D && "dismissed" === D.kind) return;
        if (D && "approved" === D.kind) {
          const diff = r2(logged - (+D.hours || 0));
          Math.abs(diff) >= 0.25 && out.push({ key: l.id + ":" + cw.empId, kind: "changed", l: l, cw: cw, emp: emp, pid: l.projectId, date: l.date, hours: diff, was: +D.hours || 0, now: logged, timeId: D.timeId, cost: r2(diff * rate) });
          return;
        }
        // a log with a punch behind it in any state is not "not clocked": a held punch (its hours wait on him) or a
        // voided one (the foreman picked) is the clock's answer. The gap is read off the clock's own hours.
        const mine = (DB.time || []).filter((e) => e.projectId === l.projectId && e.empId === cw.empId && e.date === l.date && !e.forDate);
        if (mine.some((e) => !LAB_LIVE(e) || timeHeld(e))) return;
        const clocked = r2(mine.reduce((a, e) => a + hoursClock(e), 0)),
          gap = r2(logged - clocked);
        if (!(gap >= 0.25)) return;
        // already paid for that day by the pay run: the log and the pay agree, nothing is missing
        const pay = labPaidBy(cw.empId, l.date);
        if (pay && pay.paid) return;
        out.push({ key: l.id + ":" + cw.empId, kind: "new", l: l, cw: cw, emp: emp, pid: l.projectId, date: l.date, hours: gap, logged: logged, clocked: clocked, cost: r2(gap * rate), late: pay && pay.shut ? pay.run : null });
      }),
    );
  return out;
}
// one job's flag: the hours (each row's, a change after approval by its size), the cost they would carry, who and when
function labUnclockedSum(pid) {
  const R = labUnclocked(pid);
  return {
    rows: R,
    hours: r2(R.reduce((a, r) => a + Math.abs(r.hours), 0)),
    cost: r2(R.reduce((a, r) => a + Math.abs(r.cost), 0)),
    days: new Set(R.map((r) => r.date)).size,
    late: R.filter((r) => r.late).length,
    people: [...new Set(R.map((r) => r.cw.name || r.emp.name))],
  };
}
const labHrs = (h) => `${r2(h)} ${1 === r2(h) ? "hour" : "hours"}`;
const labLogSay = (l) => `daily log of ${fmt(l.date)}${l.signedBy || l.by ? `, by ${l.signedBy || l.by}` : ""}`;
function labRowHtml(r) {
  const nm = r.cw.name || r.emp.name,
    what =
      "changed" === r.kind
        ? `<b>${esc(nm)} · ${fmt(r.date)} · log changed after approval</b><span class="small">${r.was} h approved, ${r.now} h on the log now (${r.hours > 0 ? "+" : ""}${r.hours} h) · ${esc(labLogSay(r.l))}</span>`
        : `<b>${esc(nm)} · ${r.hours} h · ${fmt(r.date)}</b><span class="small">${r.clocked ? `${r.logged} h on the log, ${r.clocked} h clocked · ` : ""}${esc(labLogSay(r.l))} · about ${money(r.cost)}</span>${r.late ? `<span class="small bad-t" data-lablate>Logged ${esc(fmt(r.date))}, not clocked, and pay run ${esc(labRunSay(r.late))} is already ${esc(r.late.status)}.</span>` : ""}`;
  return `<div class="f-row lab-row" data-labrow="${esc(r.key)}" data-h="${Math.abs(r.hours)}"><div class="grow">${what}</div><div class="lab-acts"><button type="button" class="btn sm" data-labok="${esc(r.key)}">Approve as Time</button><button type="button" class="btn sm" data-labno="${esc(r.key)}">Dismiss</button></div></div>`;
}
const labRunSay = (r) => `${fmt(r.from)} to ${fmt(r.fromTime ? payPeriodOf(r.from).to : r.to)}`;
function labUnclockedSheet(pid) {
  const p = labJob(pid),
    U = labUnclockedSum(pid);
  if (!U.rows.length) return toast(`Nothing logged and not clocked on ${labJobName(p)}`), null;
  const m = mbModal(
    `Logged, Not Clocked: ${esc(labJobName(p))}`,
    `<p class="small muted" style="margin:0 0 8px">${labHrs(U.hours)} logged, not clocked. Only clocked, approved time is job cost and payroll: these hours are on daily logs with no punch behind them, and nothing is costed or paid until you decide. Approve as Time makes the time entry; Dismiss keeps them out.</p><div class="lab-rows">${U.rows.map(labRowHtml).join("")}</div>`,
    { submit: null },
  );
  m && (m.querySelectorAll("[data-labok]").forEach((b) => (b.onclick = () => labApproveSheet(b.dataset.labok))), m.querySelectorAll("[data-labno]").forEach((b) => (b.onclick = () => labDismissSheet(b.dataset.labno))));
  const c = m && m.querySelector("#mbm-cancel");
  c && (c.textContent = "Close");
  return m;
}
function labRowOf(key) {
  const l = ((DB.field && DB.field.logs) || []).find((x) => x.id === String(key).split(":")[0]);
  return (l && labUnclocked(l.projectId).find((r) => r.key === key)) || null;
}
function labApproveSheet(key) {
  const r = labRowOf(key);
  if (!r) return toast("That row is already decided"), null;
  const p = labJob(r.pid),
    L = r.kind === "new" ? labLines(p) : [],
    best = L.length ? labLikely(p, `${r.cw.trade || ""} ${r.emp.role || ""}`, L) : null,
    nm = r.cw.name || r.emp.name;
  return mbModal(
    `Approve as Time: ${esc(nm)}, ${esc(fmt(r.date))}`,
    `<p class="small muted" style="margin:0 0 8px">${
      "changed" === r.kind
        ? `The ${esc(labLogSay(r.l))} now says ${r.now} h; ${r.was} h were approved. Approving changes that one time entry to ${r.now} h: nothing is counted twice.`
        : r.late
          ? `${r.hours} h on the ${esc(labLogSay(r.l))}, with no punch behind them, and pay run ${esc(labRunSay(r.late))} is already ${esc(r.late.status)} without them. Approving makes late time: it goes to the controller as an adjustment in the open period, never into the closed run or the month it closed, and is paid only when the controller approves it.`
          : `${r.hours} h on the ${esc(labLogSay(r.l))}, with no punch behind them. Approving makes a time entry: the hours are job cost and go to payroll, at ${esc(nm)}'s rate, with overtime worked out from the entry.`
    }</p>${mbF("Why", `<input data-f="why" value="Worked as the log says; confirmed with ${esc(r.l.signedBy || r.l.by || "the foreman")}">`)}${
      L.length ? mbF("Estimate Line", `<select data-f="line">${L.map((x) => `<option value="${esc(x.key)}" ${best && best.key === x.key ? "selected" : ""}>${esc(x.name)}</option>`).join("")}<option value="">Not on a line yet</option></select>`) : ""
    }`,
    { submit: "Approve as Time", onSubmit: (f) => (f.why ? (labApprove(key, f.why, f.line), !0) : (toast("Say why the hours are right"), !1)) },
  );
}
function labDismissSheet(key) {
  const r = labRowOf(key);
  if (!r) return toast("That row is already decided"), null;
  const nm = r.cw.name || r.emp.name;
  return mbModal(
    `Dismiss: ${esc(nm)}, ${esc(fmt(r.date))}`,
    `<p class="small muted" style="margin:0 0 8px">The ${Math.abs(r.hours)} h stay out of job cost and payroll, and this row does not come back for this log. Your name and reason are kept on the log.</p>${mbF("Why", '<input data-f="why" placeholder="e.g. was at the yard, not on site">')}`,
    { submit: "Dismiss", onSubmit: (f) => (f.why ? (labDismiss(key, f.why), !0) : (toast("Say why the hours are not right"), !1)) },
  );
}
const labHm = (min) => `${String(Math.floor(min / 60)).padStart(2, "0")}:${String(Math.round(min % 60)).padStart(2, "0")}`;
function labApprove(key, why, lineKey) {
  const r = labRowOf(key);
  if (!r) return null;
  const me = labMe(),
    at = appNowIso(),
    p = labJob(r.pid),
    l = r.l,
    D0 = (l.timeDecisions = l.timeDecisions || {})[r.cw.empId],
    nm = r.cw.name || r.emp.name;
  let e = null;
  if ("changed" === r.kind) {
    const te = (DB.time || []).find((t) => t.id === (D0 && D0.timeId));
    if (te && !te.payrollId) {
      const h0 = hoursOf(te),
        h1 = r2(h0 + r.hours);
      if (h1 <= 0) return toast("The log now has no hours for this person: reject the entry instead"), null;
      te.out = `${te.date}T${labHm(hmToMin(String(te.in).slice(11, 16)) + Math.round(h1 * 60))}:00`;
      (te.work || []).forEach((w) => (w.hours = r2((+w.hours || 0) * (h1 / (h0 || h1)))));
      (te.changes = te.changes || []).push({ from: h0, to: h1, by: me.name || "", at: at, why: why });
      te.fromLog.hours = r.now;
      e = te;
    } else if (r.hours > 0) e = labMakeEntry(r, r.hours, why, te ? te.line : lineKey, te ? te.id : "");
    else return toast("Those hours are already paid: correct them on the next pay run"), null;
  } else e = labMakeEntry(r, r.hours, why, lineKey, "");
  // a time entry made from the log passes the one pay guard like any other (timePayBlock: over 16 hours, say)
  const pay = e && "function" == typeof timePayBlock ? timePayBlock(e) : "";
  if (pay) {
    e.id && !e.adjOf && "changed" !== r.kind && (DB.time = (DB.time || []).filter((t) => t !== e));
    return toast(pay), null;
  }
  l.timeDecisions[r.cw.empId] = { kind: "approved", by: me.name || "", at: at, why: why, timeId: e.adjOf ? D0.timeId : e.id, hours: r.kind === "new" ? r2((+r.clocked || 0) + r.hours) : r.now };
  try {
    audit("time", e.id, "approved-from-log", null, { logId: l.id, empId: r.cw.empId, hours: hoursOf(e), why: why }, me.name || "");
  } catch (x) {}
  save(), render();
  toast(
    e.forDate
      ? `Late time sent to the controller: ${nm}, ${r.hours} h for ${fmt(r.date)} at ${labJobName(p)}. Pay run ${e.late.runSay} was already closed to it; it is an adjustment in the open period once the controller approves.`
      : `Approved as time: ${nm}, ${"changed" === r.kind ? `${r.now} h` : `${r.hours} h`} on ${fmt(r.date)} at ${labJobName(p)}. It is job cost now and goes to payroll.`,
    [{ label: "Open", run: () => openTime(e.id) }],
  );
  return e;
}
function labMakeEntry(r, hours, why, lineKey, adjOf) {
  const me = labMe(),
    p = labJob(r.pid),
    day = r.date,
    // after the person's last punch that day, else at the site's start: never over a punch already there
    last = (DB.time || []).filter((t) => t.empId === r.cw.empId && t.date === day && t.out && LAB_LIVE(t)).sort((a, b) => String(b.out).localeCompare(String(a.out)))[0],
    start0 = last ? hmToMin(String(last.out).slice(11, 16)) : hmToMin(siteHours(p).start),
    mins = Math.round(hours * 60),
    start = Math.max(0, Math.min(start0, 24 * 60 - 1 - mins)),
    x = lineKey ? labLines(p).find((k) => k.key === lineKey) : null,
    code = x ? x.code : "",
    e = {
      id: uid("te"),
      empId: r.cw.empId,
      date: day,
      in: `${day}T${labHm(start)}:00`,
      out: `${day}T${labHm(start + mins)}:00`,
      breakMin: 0,
      projectId: r.pid,
      code: code,
      line: x ? x.key : "",
      notes: `From the ${labLogSay(r.l)}: ${hours} h logged, not clocked`,
      status: "approved",
      approvedBy: me.name || "",
      approvedAt: appNowIso(),
      approveWhy: why,
      source: "log",
      fromLog: { logId: r.l.id, empId: r.cw.empId, hours: r.kind === "new" ? r.logged : r.now },
      work: [{ projectId: r.pid, code: code, hours: r2(hours), note: "" }],
    };
  adjOf && (e.adjOf = adjOf);
  // late time (its pay run already submitted without it): an adjustment in the open period, for the controller. It is
  // dated in the open period, so the closed run and the month it closed do not move; forDate keeps the day it was
  // worked; it waits on the controller's approval (timeApproveBlock) and the day's readers leave it out (timeHoursOf)
  if (r.late) {
    const td = today(),
      mins2 = Math.round(hours * 60);
    Object.assign(e, { date: td, in: `${td}T00:00:00`, out: `${td}T${labHm(mins2)}:00`, forDate: day, late: { run: r.late.id, runSay: labRunSay(r.late), pmBy: me.name || "", at: appNowIso(), why: why }, status: "submitted", approvedBy: "", approvedAt: "" });
    e.notes = `Late time for ${fmt(day)} from the ${labLogSay(r.l)}: pay run ${labRunSay(r.late)} was already ${r.late.status} without it. An adjustment in the open period, for the controller.`;
  }
  DB.time.push(e);
  return e;
}
function labDismiss(key, why) {
  const r = labRowOf(key);
  if (!r) return;
  const me = labMe(),
    l = r.l,
    nm = r.cw.name || r.emp.name,
    D0 = (l.timeDecisions = l.timeDecisions || {})[r.cw.empId];
  l.timeDecisions[r.cw.empId] = Object.assign({}, D0 && "approved" === D0.kind ? { timeId: D0.timeId } : {}, { kind: "dismissed", by: me.name || "", at: appNowIso(), why: why, hours: Math.abs(r.hours) });
  try {
    audit("dailylog", l.id, "logged-hours-dismissed", null, { empId: r.cw.empId, hours: Math.abs(r.hours), why: why }, me.name || "");
  } catch (x) {}
  save(), render();
  toast(`Dismissed: ${nm}'s ${Math.abs(r.hours)} h on the ${fmt(r.date)} log stay out of cost and payroll`, [{ label: "Open", run: () => ("function" == typeof dlOpen ? dlOpen(l.id) : setView("field")) }]);
}
CATCH.push({
  name: "loggedNotClocked",
  label: "Logged, Not Clocked",
  rows() {
    if (!["pm", "owner"].includes(role())) return [];
    return (DB.projects || [])
      .filter((p) => !p.archived && labMine(p))
      .map((p) => ({ p: p, U: labUnclockedSum(p.id) }))
      .filter((x) => x.U.rows.length)
      .map(({ p, U }) => ({
        key: "lognc:" + p.id,
        what: `${labHrs(U.hours)} logged, not clocked: ${labJobName(p)}`,
        sub: `${U.people.join(", ")} · ${U.days} ${1 === U.days ? "day" : "days"} · about ${money(U.cost)} ${U.late ? `(${U.late} ${1 === U.late ? "row" : "rows"} in a pay period already submitted, for the controller) ` : ""}not in cost or payroll until you approve as time, or dismiss`,
        amount: U.cost,
        verb: "Review",
        run: () => labUnclockedSheet(p.id),
      }));
  },
});

// ---- Rule 2: the job's lines, the likely one, the picker at clock-in --------------------------------------------------
function labLines(p) {
  if (!p) return [];
  try {
    return (jobFinEacLines(jobFin(p), p) || []).map((x) => ({ key: x.key, code: String(x.code || ""), name: x.name, budget: +x.budget || 0, room: r2((+x.budget || 0) - (+x.actual || 0) - (+x.committed || 0)), doc: x.doc }));
  } catch (e) {
    return [];
  }
}
const LAB_STOP = new Set(["and", "the", "with", "for", "work", "crew", "hours", "rough", "finish"]);
const labWords = (s) =>
  String(s || "")
    .toLowerCase()
    .split(/[^a-z]+/)
    .filter((w) => w.length > 2 && !LAB_STOP.has(w))
    .map((w) => w.replace(/(ing|s)$/, ""));
// the line a piece of work most likely belongs to: the most words in common, then the most budget left
function labLikely(p, text, L0) {
  const L = L0 || labLines(p),
    w = labWords(text);
  if (!L.length) return null;
  const score = (x) => labWords(x.name).filter((a) => w.includes(a)).length;
  return L.slice().sort((a, b) => score(b) - score(a) || b.room - a.room)[0];
}
// the picker's order: the lines of today's tasks this person is on, then the rest as the estimate lists them
function labPickOrder(e, p) {
  const L = labLines(p),
    first = [];
  try {
    withProject(p, () =>
      (fActive(e.date || today()) || [])
        .filter((t) => "function" != typeof f3WorkedOn || f3WorkedOn(t, e, p))
        .forEach((t) => {
          const x = tpTaskLine(p, t),
            k = x && L.find((l) => l.key === x.key);
          k && !first.includes(k) && first.push(k);
        }),
    );
  } catch (x) {}
  return first.concat(L.filter((l) => !first.includes(l)));
}
let labPickAll = !1;
function labPickHtml(e, p) {
  const L = labPickOrder(e, p);
  if (!L.length) return "";
  if (e.line || e.lineOther) {
    const x = L.find((l) => l.key === e.line);
    return `<div class="lab-pick lab-on"><div class="small"><span>Working on</span> <b data-verbatim>${esc(x ? x.name : e.lineOther)}</b></div><button type="button" class="btn sm" data-labchange>Change</button></div>`;
  }
  const show = labPickAll ? L : L.slice(0, 4);
  return `<div class="lab-pick"><b class="lab-q">What Are You Working On?</b><div class="small muted">Pick the line of the estimate. Your hours go to its budget.</div><div class="lab-chips">${show
    .map((l) => `<button type="button" class="btn lab-chip" data-labline="${esc(l.key)}"><span data-verbatim>${esc(l.name)}</span></button>`)
    .join("")}${L.length > show.length ? '<button type="button" class="btn lab-chip" data-labmore>More Lines</button>' : ""}<button type="button" class="btn lab-chip" data-labother>Other</button></div></div>`;
}
function labPickSet(e, key, note) {
  const p = labJob(e.projectId),
    x = key ? labLines(p).find((l) => l.key === key) : null,
    me = labMe();
  if (x) (e.line = x.key), (e.code = x.code), delete e.lineOther;
  else (e.lineOther = note), (e.line = ""), (e.code = "");
  e.linePick = { at: appNowIso(), by: me.name || "", how: "clock-in" };
  try {
    audit("time", e.id, "line-picked", null, x ? { line: x.key, code: x.code } : { other: note });
  } catch (y) {}
  labPickAll = !1;
  save(), render();
  toast(x ? `Your hours go to ${x.name}` : "Noted. The PM puts these hours on a line.", [{ label: "Open", run: () => openTime(e.id) }]);
}
function labOtherSheet(e) {
  return mbModal("Other Work", `<p class="small muted" style="margin:0 0 8px">Say in a few words what you are doing. The PM puts the hours on the right line.</p>${mbF("What Are You Doing?", '<input data-f="note" placeholder="e.g. moving the dumpster">')}`, {
    submit: "Save",
    onSubmit: (f) => (f.note ? (labPickSet(e, "", f.note), !0) : (toast("Say what you are doing"), !1)),
  });
}
// drawn where the person clocks in: the Clock page, the foreman's Today
function labPickMount() {
  if (!tkgField()) return;
  const emp = tkgEmp(),
    e = emp && (DB.time || []).find((t) => t.empId === emp.id && !t.out && t.projectId);
  document.querySelectorAll(".view.on .lab-pick").forEach((x) => x.remove());
  if (!e) return;
  const p = labJob(e.projectId),
    html = labPickHtml(e, p);
  if (!html) return;
  let host = null;
  if ("time" === view) {
    const b = document.querySelector("#v-time #clock-out");
    host = b && (b.closest(".row") || b.parentNode);
    host && host.insertAdjacentHTML("afterend", html);
  } else if ("ftoday" === view) {
    host = document.querySelector("#ftoday-body .f-hero");
    host && host.insertAdjacentHTML("beforeend", html);
  }
  const box = host && document.querySelector(".view.on .lab-pick");
  if (!box) return;
  box.querySelectorAll("[data-labline]").forEach((b) => (b.onclick = () => labPickSet(e, b.dataset.labline)));
  const more = box.querySelector("[data-labmore]"),
    other = box.querySelector("[data-labother]"),
    ch = box.querySelector("[data-labchange]");
  more && (more.onclick = () => ((labPickAll = !0), render()));
  other && (other.onclick = () => labOtherSheet(e));
  ch &&
    (ch.onclick = () => {
      delete e.lineOther;
      e.line = "";
      render();
    });
  try {
    "function" == typeof esPass && esPass(box);
  } catch (x) {}
}

// ---- Rule 2: cost still off a line is a proposal to the job's lead ----------------------------------------------------
// what is clocked to each code no line carries: the time entries behind jobFin's unlined rows, at jobFin's own rate
function labOffLine(pid) {
  const out = [];
  (DB.projects || [])
    .filter((p) => !p.archived && (!pid || p.id === pid))
    .forEach((p) => {
      let U = null;
      try {
        U = jobFin(p).eacUnlined;
      } catch (e) {}
      if (!U || !U.rows || !U.rows.length) return;
      const tu = "function" == typeof payrollTrueUp ? payrollTrueUp() : null;
      U.rows.forEach((r) => {
        const T = r.src
          .filter((s) => /^time:/.test(s))
          .map((s) => (DB.time || []).find((t) => "time:" + t.id === s))
          // a punch held for the time he left is not moved to a line until it is confirmed (timeHeld): its hours are
          // not known yet, and they count 0 meanwhile
          .filter((t) => LAB_LIVE(t) && !timeHeld(t) && !(t.word && !t.word.okBy));
        if (!T.length) return;
        const cost = r2(T.reduce((a, t) => a + hoursOf(t) * laborRate(labEmp(t.empId)) * (tu ? +tu(t, labEmp(t.empId)) || 1 : 1), 0)),
          co = T.map((t) => t.offLineCo).find(Boolean),
          c = (DB.clients || []).find((x) => x.id === p.clientId),
          doc = co && c && (c.changeOrders || []).find((d) => d.id === co && "void" !== d.status);
        out.push({ p: p, code: String(r.code), name: r.name, T: T, hours: r2(T.reduce((a, t) => a + hoursOf(t), 0)), cost: cost, co: doc || null });
      });
    });
  return out;
}
function labOffLineSheet(pid, code) {
  const R = labOffLine(pid).find((x) => x.code === String(code));
  if (!R) return toast("Nothing clocked off a line there now"), null;
  const p = R.p,
    L = labLines(p),
    best = labLikely(p, `${R.name} ${R.T.map((t) => t.notes || t.lineOther || "").join(" ")}`, L);
  if (!L.length) return toast(`${labJobName(p)} has no estimate lines yet`), null;
  const m = mbModal(
    `Off a Line: ${esc(labJobName(p))}, ${esc(R.name)}`,
    `<p class="small muted" style="margin:0 0 8px">${r2(R.hours)} crew hours, ${money(R.cost)}, are clocked to cost code ${esc(R.code)} (${esc(R.name)}), which no line of the estimate or an approved change order carries: they cannot be held to a budget or billed. Move them to the line the work belongs to, or draft a change order for the client. Nothing moves until you say.${R.co ? ` ${esc(R.co.number)} is drafted for them: once the client approves it, they are on its line.` : ""}</p><div class="lab-rows">${R.T.map(
      (t) => `<div class="f-row"><div class="grow"><b>${esc(empName(t.empId))} · ${hoursOf(t)} h · ${esc(fmt(t.date))}</b><span class="small">${esc(t.status)}${isLocked(t.date) ? " · in a closed month: the move posts today" : ""}</span></div></div>`,
    ).join("")}</div>${mbF("Move to", `<select data-f="line">${L.map((x) => `<option value="${esc(x.key)}" ${best && best.key === x.key ? "selected" : ""}>${esc(x.name)}${best && best.key === x.key ? " (likely)" : ""}</option>`).join("")}</select>`)}${mbF("Why", `<input data-f="why" value="The work is ${esc(R.name.toLowerCase())}, part of this line">`)}`,
    {
      submit: "Move to a Line",
      alt: { label: R.co ? `Open ${esc(R.co.number)}` : "Draft a Change Order", run: () => (R.co ? labOpenCo(R.p, R.co) : labDraftCo(R)) },
      onSubmit: (f) => (f.line ? (labMoveTime(R, f.line, f.why), !0) : (toast("Pick the line"), !1)),
    },
  );
  return m;
}
function labMoveTime(R, key, why) {
  const p = R.p,
    x = labLines(p).find((l) => l.key === key);
  if (!x) return;
  const me = labMe(),
    at = appNowIso(),
    eac0 = jobFin(p).eac;
  R.T.forEach((t) => {
    const from = String(t.code || "99"),
      locked = "function" == typeof isLocked && isLocked(t.date);
    (t.moves = t.moves || []).push({ from: from, to: x.code, fromLine: t.line || "", toLine: x.key, by: me.name || "", at: at, postOn: locked ? today() : t.date, why: why || "" });
    t.code = x.code;
    t.line = x.key;
    (t.work || []).forEach((w) => (!w.projectId || w.projectId === t.projectId) && String(w.code || "") === from && (w.code = x.code));
    try {
      audit("time", t.id, "moved-to-line", { code: from }, { code: x.code, line: x.key, postOn: t.moves[t.moves.length - 1].postOn }, me.name || "");
    } catch (y) {}
  });
  save(), render();
  const eac1 = jobFin(p).eac;
  toast(`Moved ${r2(R.hours)} h (${money(R.cost)}) to ${x.name}: ${labJobName(p)}'s estimate at completion is ${money(eac1)}${Math.abs(eac1 - eac0) > 0.005 ? `, was ${money(eac0)}` : ""}`, [
    { label: "Open", run: () => (setCurrent(p.id), (view = "costs"), render()) },
  ]);
}
function labOpenCo(p, d) {
  try {
    (docOpen = { kind: "co", id: d.id }), (view = (ROLE_VIEWS[role()] || []).includes("billing") ? "billing" : "clients"), (billTab = "co"), (clientOpen = p.clientId), render();
  } catch (e) {}
}
function labDraftCo(R) {
  const p = R.p,
    c = (DB.clients || []).find((x) => x.id === p.clientId);
  if (!c) return toast("No client on this job"), null;
  const per = R.hours ? r2(R.cost / R.hours) : 0,
    item = `${R.name}: crew hours`,
    d = newDoc(c, "co", { fields: { title: item, projectId: p.id, lines: [{ id: uid("l"), item: item, desc: `${r2(R.hours)} crew hours clocked to cost code ${R.code} (${R.name}), on no estimate line; at cost, before markup`, qty: r2(R.hours), unit: "hr", rate: per, cost: per, code: R.code, taxable: !1 }] } });
  d.fromTime = R.T.map((t) => t.id);
  R.T.forEach((t) => (t.offLineCo = d.id));
  try {
    audit("co", d.id, "co-from-hours-off-line", "", d.number, `${r2(R.hours)} h on code ${R.code}`);
  } catch (e) {}
  save();
  labOpenCo(p, d);
  toast(`${d.number} drafted for ${r2(R.hours)} crew hours on ${R.name}, ${money(R.cost)} at cost. Add the markup, then Send to Client; the hours stay where they are until it is approved.`, [{ label: "Open", run: () => labOpenCo(p, d) }]);
  return d;
}
CATCH.push({
  name: "offLine",
  label: "Hours Off a Line",
  rows() {
    if (!["pm", "owner"].includes(role())) return [];
    return labOffLine()
      .filter((R) => labMine(R.p))
      .map((R) => ({
        key: `offline:${R.p.id}:${R.code}`,
        what: `Cost off a line: ${labJobName(R.p)} · ${R.name}`,
        sub: `${money(R.cost)} · ${r2(R.hours)} crew hours on code ${R.code}, no estimate line · ${R.co ? `${R.co.number} drafted` : "move to a line, or draft a change order"}`,
        amount: R.cost,
        verb: "Review",
        run: () => labOffLineSheet(R.p.id, R.code),
      }));
  },
});

(() => {
  const css = `
.lab-pick{margin-top:10px;display:flex;flex-direction:column;gap:6px;text-align:left;flex:1 1 100%}
.lab-pick.lab-on{flex-direction:row;align-items:center;gap:10px;flex-wrap:wrap}
.lab-pick .lab-q{font-size:15px}
.lab-chips{display:flex;flex-direction:column;gap:8px}
.lab-chip{min-height:48px;width:100%;justify-content:flex-start;text-align:left;white-space:normal}
.lab-pick .btn.sm{min-height:44px}
.lab-row{align-items:center;gap:8px;flex-wrap:wrap}
.lab-acts{display:flex;gap:8px;flex-wrap:wrap}
.lab-acts .btn{min-height:40px}
.lab-nlacts{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}`;
  try {
    const s = document.createElement("style");
    (s.id = "lab-css"), (s.textContent = css), document.head.appendChild(s);
  } catch (e) {}
})();

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
