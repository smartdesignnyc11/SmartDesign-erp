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

   Design gate (BACKLOG 1.16): no new store. The time entry is the record (DB.time); the acknowledgement rides on the
   person (u.geoAck) and the audit trail; a run's held hours ride on the run (run.held).
--------------------------------------------------------------------------------------------------------------------- */
const TKG_AWAY_MIN = 15,
  TKG_NOTICE_V = 1;
const tkgMe = () => ("function" == typeof currentUser ? currentUser() : null) || {};
const tkgField = () => ["foreman", "crew", "driver"].includes("function" == typeof role ? role() : "");
const tkgAcked = (u) => !!(u && u.geoAck && u.geoAck.at && !u.geoAck.off);
const tkgJob = (id) => (DB.projects || []).find((p) => p.id === id) || null;
const tkgMs = (s) => new Date(s).getTime();

// ---- the notice: plain words, read once and accepted before anything is automatic -------------------------------------
const TKG_NOTICE = [
  "When your phone is at a job site, the app clocks you in to that job. When you leave the site for more than 15 minutes, it clocks you out at the time you left.",
  "Your location is saved only at the moment of each clock-in and clock-out, with how far you were from the site. It is never saved as a track of where you go.",
  "You can always clock in and out by hand, and you can undo any automatic punch. Your foreman and payroll see which punches were automatic.",
  "SmartDesign uses this for your hours, payroll and job costs only.",
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
  try {
    audit("consent", u.id, "auto-clock-by-location", "", `agreed to notice v${TKG_NOTICE_V}`, u.name || "");
  } catch (e) {}
  save();
  try {
    "function" == typeof askNotify && askNotify();
    startGeofence();
  } catch (e) {}
  render();
  toast("Automatic clock-in is on: the app clocks you in at a job site", [{ label: "Open", run: () => setView("time") }]);
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
let tkGeo = { outSince: "", outPos: null, last: null, lastAt: "", timer: null, asked: "" };
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
  e.out = at;
  e.geoOut = pos ? { lat: pos.lat, lng: pos.lng, acc: Math.round(pos.acc || 0), dist: null } : null;
  e.autoOut = !0;
  e.auto = Object.assign({}, e.auto || {}, { out: "automatic, by location" });
  "function" == typeof hoursOf && hoursOf(e) >= 6 && !e.breakMin && (e.breakMin = 30);
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
  const was = e.out;
  (e.out = ""), (e.geoOut = null), delete e.autoOut;
  e.auto && delete e.auto.out;
  tkGeo.outSince = "";
  try {
    audit("time", id, "auto-clock-out-undone", { out: was }, null);
  } catch (x) {}
  save(), render(), toast("Clock-out undone: you are still on the clock");
}
function tkGeoTick(pos, at0) {
  const at = at0 || appNowIso(),
    u = tkgMe(),
    emp = "function" == typeof myEmp ? myEmp() : null;
  if (!pos || !emp) return { did: "none", why: "no position or no employee" };
  if (!tkgAcked(u)) return { did: "none", why: "no acknowledgement" };
  tkGeo.last = pos;
  tkGeo.lastAt = at;
  const near = tkgSiteNear(pos),
    open = (DB.time || []).find((t) => t.empId === emp.id && !t.out),
    inside = !!near && near.d <= near.rad,
    poor = (+pos.acc || 0) > ((near && near.rad) || 250);
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
    tkGeo.outSince = "";
    tkGeo.outPos = null;
    if (open && open.projectId === near.p.id) return { did: "none", why: "on the clock here" };
    const sh = siteHours(near.p),
      m = new Date(at),
      mins = 60 * m.getHours() + m.getMinutes();
    if (!open && (!sh.days.includes(m.getDay()) || mins < hmToMin(sh.start) - 60 || mins > hmToMin(sh.end) + 120)) return { did: "none", why: "outside the site's hours" };
    if (open) {
      const from = tkgJob(open.projectId);
      tkgPunchOut(open, pos, at);
      const e = tkgPunchIn(emp, near.p, pos, at, near.d);
      save(), render();
      toast(`Moved to ${tkgSay(near.p)} at ${stampTime(at)}${from ? `, out of ${tkgSay(from)}` : ""}`, [
        { label: "Undo", run: () => (tkgUndoIn(e.id), tkgUndoOut(open.id)) },
      ]);
      return { did: "switch", id: e.id, from: open.id };
    }
    const e = tkgPunchIn(emp, near.p, pos, at, near.d);
    try {
      "function" == typeof setCurrent && (!S || S.id !== near.p.id) && setCurrent(near.p.id);
    } catch (x) {}
    save(), render();
    toast(`Clocked in at ${tkgSay(near.p)}, ${stampTime(at)}`, [{ label: "Undo", run: () => tkgUndoIn(e.id) }]);
    return { did: "in", id: e.id };
  }
  // outside every site, on the clock: away for 15 minutes clocks out at the time they left
  if (open) {
    if (!tkGeo.outSince) {
      tkGeo.outSince = at;
      tkGeo.outPos = pos;
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
// the watch itself: the device's position, read while the app is open (and once when it opens at the site)
if ("function" == typeof startGeofence) {
  startGeofence = function () {
    if (null != geoWatch || !navigator.geolocation) return;
    const onPos = (pos) => {
      const here = { lat: pos.coords.latitude, lng: pos.coords.longitude, acc: Math.round(pos.coords.accuracy || 0) };
      try {
        clockState.geo = here;
        clockState.err = "";
      } catch (e) {}
      tkGeoTick(here);
    };
    try {
      navigator.geolocation.getCurrentPosition(onPos, () => {}, { enableHighAccuracy: !0, timeout: 8e3, maximumAge: 6e4 });
    } catch (e) {}
    geoWatch = navigator.geolocation.watchPosition(
      onPos,
      (e) => {
        try {
          clockState.err = geoMessage(e);
        } catch (x) {}
      },
      { enableHighAccuracy: !0, maximumAge: 3e4 },
    );
  };
}
// on for a field person who accepted the notice, off for anyone else (one person's phone, one person's choice)
{
  const base = render;
  render = function () {
    const r = base.apply(this, arguments);
    try {
      const u = tkgMe();
      if (tkgField() && tkgAcked(u)) null == geoWatch && startGeofence();
      else if (null != geoWatch && !(DB.autoClock && !tkgField())) stopGeofence();
      tkgClockCard();
      tkHoldReminderMount();
    } catch (e) {
      console.warn("field clock", e);
    }
    return r;
  };
}
// the Clock page: the notice's card (or the status with Turn Off) in place of the old device-wide checkbox
function tkgClockCard() {
  if ("time" !== view || !tkgField()) return;
  const v = document.getElementById("v-time"),
    old = v && v.querySelector("#geo-auto"),
    host = (old && old.closest("label")) || (v && v.querySelector("#geo-line"));
  if (!host) return;
  old && (old.closest("label").hidden = !0);
  const u = tkgMe(),
    on = tkgAcked(u);
  let box = v.querySelector(".tkg-card");
  box || ((box = document.createElement("div")), (box.className = "tkg-card"), host.insertAdjacentElement("afterend", box));
  box.innerHTML = on
    ? `<div class="small"><b>Automatic clock-in is on.</b> The app clocks you in at a job site while it is open. <button type="button" class="btn sm" data-tkgoff>Turn Off</button></div>`
    : `<button type="button" class="btn tkg-on" data-tkgon>Turn On Automatic Clock-In</button><div class="small muted">Read what it does first. Until you agree, the clock is manual.</div>`;
  const b1 = box.querySelector("[data-tkgon]"),
    b2 = box.querySelector("[data-tkgoff]");
  b1 && (b1.onclick = () => tkGeoNotice());
  b2 && (b2.onclick = () => tkGeoOff(u));
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
function tkHeldOf(run) {
  return (run && run.held) || [];
}
if ("function" == typeof payrollFromTime) {
  const base = payrollFromTime;
  payrollFromTime = function () {
    // the entries in an unresolved overlap stay out of the run; everything else pays
    const O = tkTimeOverlaps(),
      hold = new Map();
    O.forEach((o) => [o.a, o.b].forEach((t) => !t.payrollId && hold.set(t.id, { t: t, st: t.status })));
    hold.forEach(({ t }) => (t.status = "held-overlap"));
    let run = null;
    try {
      run = base.apply(this, arguments);
    } finally {
      hold.forEach(({ t, st }) => (t.status = st));
    }
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
function tkHoldDue() {
  const cut = tkPayCutoff(),
    from = iso(addDays(parse(cut), -1));
  return today() >= from ? tkTimeOverlaps().filter((o) => !o.a.payrollId || !o.b.payrollId) : [];
}
function tkHoldReminderMount() {
  if ("ftoday" !== view || "foreman" !== role()) return;
  const root = document.getElementById("ftoday-body");
  if (!root) return;
  root.querySelectorAll(".tkg-remind").forEach((c) => c.remove());
  const L = tkHoldDue();
  if (!L.length) return;
  const html = `<div class="card f-card tkg-remind"><div class="hd"><h3>Before Payroll</h3><span class="small muted">${L.length}</span></div>${L.map(
    (o, i) => `<div class="f-row warn"><div class="grow"><b>${esc(tkFirst(o.name))}'s ${esc(fmt(o.date))} hours overlap: pick one before payroll.</b><span class="small">${esc(stampTime(o.a.in))} to ${esc(o.a.out ? stampTime(o.a.out) : "now")} and ${esc(stampTime(o.b.in))} to ${esc(o.b.out ? stampTime(o.b.out) : "now")} · ${o.h} h held</span></div><button type="button" class="btn sm" data-tkgpick="${i}">Pick One</button></div>`,
  ).join("")}</div>`;
  const at = root.querySelector(":scope > .tkr-offers") || root.querySelector(":scope > .f-hero");
  at ? at.insertAdjacentHTML("afterend", html) : root.insertAdjacentHTML("afterbegin", html);
  root.querySelectorAll("[data-tkgpick]").forEach((b) => (b.onclick = () => tkOverlapPick(L[+b.dataset.tkgpick])));
}
// the foreman's pick: keep one (the other is voided), or keep both without the overlap
function tkOverlapPick(o) {
  if (!o) return;
  const span = (t) => `${stampTime(t.in)} to ${t.out ? stampTime(t.out) : "now"}`,
    paidA = !!o.a.payrollId,
    paidB = !!o.b.payrollId;
  let pick = "";
  const m = mbModal(
    `${esc(tkFirst(o.name))}'s ${esc(fmt(o.date))} Hours`,
    `<p class="small muted" style="margin:0 0 8px">Two punches claim ${o.h} hours of the same time. Payroll holds them until you pick; nothing is paid twice.</p><div class="tks-chips" role="radiogroup">${[
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
  toast(`${tkFirst(o.name)}'s ${fmt(o.date)} hours: ${"both" === pick ? "both kept, without the overlap" : "one punch kept, the other voided"}. Paid on the next run.`, [{ label: "Open", run: () => setView("time") }]);
}

(() => {
  const css = `
.tkg-card{margin-top:8px;display:flex;flex-direction:column;gap:6px}
.tkg-card .btn{min-height:44px}
.tkg-held{margin-bottom:10px}`;
  try {
    const s = document.createElement("style");
    (s.id = "tkg-css"), (s.textContent = css), document.head.appendChild(s);
  } catch (e) {}
})();
/*<</fieldclock.js>>*/
