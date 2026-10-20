/* =========================================================================================================
   loop_core (lane "loop", 2026-10-20): the improvement loop's rules, pure (BACKLOG §1.19, §1.32 items 4-5).
   No DB, no page, no clock: the app (src/loop.js) and the server's nightly run (platform/netlify/functions/
   lib/loop.mjs, through the copy platform/build.py makes) call the same functions with the signals, the changes
   and the day, so a problem is grouped, ranked, worded and checked the same way on a phone and on the server.

   A signal is evidence, never a to-do:
     {id, kind: report|usage|watch|lesson|finding, day: YYYY-MM-DD, uid, role, screen, what, sev, n, p, label,
      text, still, rec, by}
   usage signals hold a day's counts for one person: by[screen] = {export, retype, back, abandon, rage, to: {view: n}}.
   A problem is a group of signals with one key (gkey). A problem that qualifies is drafted as a change
   (DB.changes, source "loop", key "imp:" + gkey) for the owner; a declined one is never proposed again.
--------------------------------------------------------------------------------------------------------- */
var LOOP_CORE = (function () {
  "use strict";
  const PRINCIPLES = ["safety", "law", "integrity", "quality", "client", "schedule", "cost"];
  const P_WORDS = { safety: "Safety", law: "Law, code and landmarks", integrity: "Integrity", quality: "Quality", client: "Client experience", schedule: "Schedule", cost: "Cost" };
  // what a problem report says went wrong: the words and the decision principle at stake
  const RP = {
    save: { words: "did not save", p: "integrity" },
    wrong: { words: "showed the wrong number", p: "integrity" },
    find: { words: "could not find it", p: "schedule" },
    slow: { words: "was too slow", p: "schedule" },
    broken: { words: "looked broken", p: "quality" },
    other: { words: "had a problem", p: "quality" },
  };
  // usage measures: the floor over 30 days before a screen's count becomes a problem
  const US = {
    export: { min: 3, p: "cost", noun: "exports to Excel" },
    retype: { min: 3, p: "cost", noun: "times the same words were typed again" },
    back: { min: 4, p: "cost", noun: "trips away and straight back" },
    abandon: { min: 3, p: "quality", noun: "forms typed in and left unsaved" },
    rage: { min: 3, p: "quality", noun: "repeated taps on one button" },
  };
  const WINDOW = 90, MONTH = 30;
  const day = (s) => String(s || "").slice(0, 10);
  const addDays = (d, n) => new Date(Date.parse(day(d) + "T12:00:00Z") + n * 864e5).toISOString().slice(0, 10);
  const daysBetween = (a, b) => Math.round((Date.parse(day(b) + "T12:00:00Z") - Date.parse(day(a) + "T12:00:00Z")) / 864e5);
  const norm = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9 ]+/g, " ").split(/\s+/).filter((w) => w.length > 2).slice(0, 6).join(" ");
  const plural = (n, w, ws) => `${n} ${1 === n ? w : ws || w + "s"}`;
  const clean = (s, n) => String(s || "").replace(/[<>]/g, "").replace(/\s+/g, " ").trim().slice(0, n || 300);

  // One signal becomes one or more atoms, each with its group key.
  function atoms(signals) {
    const out = [];
    (signals || []).forEach((s) => {
      if (!s || !s.kind) return;
      const base = { sid: s.id, day: day(s.day || s.at), uid: s.uid || "", role: s.role || "" };
      if ("usage" === s.kind) {
        Object.entries(s.by || {}).forEach(([screen, m]) => {
          Object.keys(US).forEach((metric) => {
            const n = +((m || {})[metric]) || 0;
            if (!n) return;
            const top = "back" === metric ? Object.entries((m || {}).to || {}).sort((a, b) => b[1] - a[1])[0] : null;
            out.push(Object.assign({}, base, { gkey: `us|${screen}|${metric}`, family: "usage", screen: screen, what: metric, n: n, p: US[metric].p, label: (m || {}).label || screen, other: top ? top[0] : "", form: (m || {}).form || "", field: (m || {}).field || "" }));
          });
        });
        return;
      }
      if ("report" === s.kind) return void out.push(Object.assign({}, base, { gkey: `rp|${s.screen || "?"}|${s.what || "other"}`, family: "report", screen: s.screen || "", what: s.what || "other", n: 1, p: (RP[s.what] || RP.other).p, sev: s.sev || "", label: s.label || s.screen || "", text: s.text || "", still: !!s.still, rec: s.rec || null, errors: s.errors || [], trail: s.trail || [] }));
      if ("watch" === s.kind) return void out.push(Object.assign({}, base, { gkey: `sw|${s.what}`, family: "watch", screen: s.screen || "", what: s.what, n: +s.n || 0, p: s.p || "", label: s.label || s.what, owner: s.owner || "", sample: s.text || "" }));
      if ("lesson" === s.kind) return void out.push(Object.assign({}, base, { gkey: `ln|${s.what}`, family: "lesson", screen: s.screen || "", what: s.what, n: 1, p: s.p || "", label: s.label || s.what, text: s.text || "", approvedAt: s.approvedAt || "" }));
      if ("finding" === s.kind) return void out.push(Object.assign({}, base, { gkey: `fd|${s.screen || "?"}|${norm(s.label || s.text)}`, family: "finding", screen: s.screen || "", what: s.sev || "", n: 1, p: s.p || "quality", sev: s.sev || "", label: s.label || "", text: s.text || "", fix: s.fix || "", source: s.source || "" }));
    });
    return out;
  }

  // Group the atoms of the last 90 days into problems.
  function group(signals, today) {
    const from = addDays(today, -WINDOW), m30 = addDays(today, -MONTH), G = {};
    atoms(signals)
      .filter((a) => a.day && a.day >= from && a.day <= today)
      .forEach((a) => {
        const g = (G[a.gkey] = G[a.gkey] || { gkey: a.gkey, family: a.family, screen: a.screen, what: a.what, p: a.p, label: a.label, atoms: [], sids: [], uids: [], roles: [], days: [], n: 0, n30: 0, stuck: 0, first: a.day, last: a.day });
        g.atoms.push(a);
        g.sids.includes(a.sid) || g.sids.push(a.sid);
        a.uid && !g.uids.includes(a.uid) && g.uids.push(a.uid);
        a.role && !g.roles.includes(a.role) && g.roles.push(a.role);
        a.n > 0 && !g.days.includes(a.day) && g.days.push(a.day);
        g.n += a.n;
        a.day >= m30 && (g.n30 += a.n);
        "stuck" === a.sev && g.stuck++;
        a.day < g.first && (g.first = a.day), a.day > g.last && (g.last = a.day);
        a.p && (g.p = a.p), a.label && (g.label = a.label);
      });
    return Object.values(G).map((g) => Object.assign(g, { people: g.uids.length || g.roles.length }));
  }

  // When a group is a problem worth the owner's time. A person's report always is; the counted signals need a floor.
  function qualifies(g) {
    if ("report" === g.family || "finding" === g.family) return !0;
    if ("usage" === g.family) return g.n30 >= (US[g.what] || { min: 3 }).min;
    // "When something goes wrong twice, fix the system": a standard broken on two different days
    if ("watch" === g.family) return g.days.length >= 2;
    // an approved lesson that did not stop it: the same thing twice since the lesson
    if ("lesson" === g.family) return g.n >= 2;
    return !1;
  }

  const ROLE_WORDS = { owner: "the owner", pm: "the PM", coord: "the coordinator", foreman: "the foreman", crew: "the crew", driver: "the driver", designer: "the designer", design_mgr: "the design director", billing: "billing", controller: "the controller", client: "a client" };
  const who = (g) => (g.roles.length ? g.roles.map((r) => ROLE_WORDS[r] || r).join(", ") : "nobody named");

  // The proposal, in plain words: what is wrong, the evidence, the fix, the risk, and how it would be checked.
  function draft(g, names) {
    const N = names || {}, D = N.date || ((x) => x), screen = (N.screen && N.screen(g.screen)) || g.label || g.screen || "a screen";
    const ev = [], since = g.first;
    let title = "", what = "", fix = "", risk = "", kind = "code", delta = null, accept = [];
    if ("report" === g.family) {
      const w = (RP[g.what] || RP.other).words;
      title = `${screen}: it ${w}`;
      what = `${plural(g.sids.length, "report")} from ${plural(g.people, "person", "people")} (${who(g)}) since ${D(since)}${g.stuck ? `, ${g.stuck} of them stuck` : ""}: on ${screen} it ${w}.`;
      g.atoms.slice(-5).forEach((a) => {
        ev.push({ t: `${D(a.day)} · ${ROLE_WORDS[a.role] || a.role || "someone"}${a.sev ? ` · ${a.sev}` : ""}: ${a.text ? clean(a.text, 200) : "(no words)"}`, m: "Report a Problem" });
        (a.errors || []).slice(-1).forEach((e) => ev.push({ t: `Error: ${clean(e.m || e, 140)}`, m: "the app" }));
        a.trail && a.trail.length && ev.push({ t: `Just before: ${a.trail.slice(-4).map((x) => `${x.kind} ${x.what}`).join(" › ")}`, m: "the steps" });
      });
      fix = {
        save: `Find where the save is lost on ${screen} (the steps and any error are attached), fix it at the root, and add a check that saves, reloads and finds it again as ${who(g)}, on the phone and the desktop.`,
        wrong: `Trace the figure on ${screen} to its records, fix the reader so it ties to the report it should match, and add the figure to the counts lint so a drift fails the build.`,
        find: `Put what they looked for where they looked first: ${screen} links to it, and Search finds it by the words they used. Add a find-it-again check for it.`,
        slow: `Measure ${screen} on a mid-range phone, bring it under one second, and add it to the speed test.`,
        broken: `Fix the layout or error on ${screen} and add the screen to the phone lint at 390px.`,
        other: `Read the reports with the person who wrote them, name the cause, and fix it at the root.`,
      }[g.what] || "";
      risk = "Low: a change to the ERP, built behind the full test net; the release waits for the owner.";
      accept = [`As ${who(g)}, on ${screen}, what was reported no longer happens (desktop and phone 390px).`, "A Playwright check reproduces it first and passes after the fix.", "No new report of this on this screen for 30 days."];
    } else if ("usage" === g.family) {
      const U = US[g.what] || {};
      const field = g.atoms.map((a) => a.field).filter(Boolean)[0] || "", form = g.atoms.map((a) => a.form).filter(Boolean)[0] || "", other = g.atoms.map((a) => a.other).filter(Boolean)[0] || "";
      const otherW = (other && N.screen && N.screen(other)) || other;
      title = {
        export: `${screen} is taken to Excel`,
        retype: `The same words are typed again on ${screen}`,
        back: `People leave ${screen} for ${otherW || "another page"} and come straight back`,
        abandon: `${form || "A form"} on ${screen} is started and left`,
        rage: `A button on ${screen} gets tapped again and again`,
      }[g.what] || `${screen}: ${U.noun}`;
      what =`${g.n30} ${U.noun} in the last 30 days, by ${plural(g.people, "person", "people")} (${who(g)}), on ${screen}.`;
      ev.push({ t: `Counted on ${g.days.length} day${1 === g.days.length ? "" : "s"} from ${D(since)} to ${D(g.last)}. Counts and screens only: nothing anyone typed is kept.`, m: "usage, measured in the app" });
      fix = {
        export: `Ask the people who export it what they do with the spreadsheet (one question from their assistant), then put that column, total or report on ${screen} so the spreadsheet is not needed.`,
        retype: `Fill ${field ? `"${field}"` : "the field"} in from what the system knows: a default from the job, the last value used, or an item from the library.`,
        back: `Show what they go to ${otherW || "the other page"} for on ${screen} itself, or put the next step's button there.`,
        abandon: `Shorten ${form || "the form"}, fill in what the system knows, and ask the people who left it what stopped them.`,
        rage: `Answer every tap at once (a pressed state and progress), and find the button that looks dead or is slow.`,
      }[g.what] || "";
      risk = "None to the books or to anyone's work: a change to the screen, built behind the full test net.";
      accept = [`The ${U.noun} on ${screen} fall by at least three quarters in the 30 days after the change.`, `As ${who(g)}, the job they did around the screen is done on it.`];
    } else if ("watch" === g.family) {
      const ownerW = ROLE_WORDS[g.atoms.map((a) => a.owner).filter(Boolean)[0]] || "the person who owns it";
      const owner = g.atoms.map((a) => a.owner).filter(Boolean)[0] || "";
      title = `The standard "${g.label}" keeps being broken`;
      what = `Broken on ${plural(g.days.length, "day")} since ${D(since)} (${g.atoms.slice(-1)[0].n} today or last seen ${D(g.last)}). The Standard: when something goes wrong twice, fix the system.`;
      g.atoms.slice(-4).forEach((a) => ev.push({ t: `${D(a.day)}: ${plural(a.n, "breach", "breaches")}${a.sample ? ` · ${clean(a.sample, 160)}` : ""}`, m: "the Standard Watch" }));
      kind = "rule";
      delta = { path: `company.loopWatch.${g.what}`, from: !1, to: !0, owner: owner, label: `Each breach of "${g.label}" becomes a dated task for ${ownerW} every morning until the standard holds` };
      fix = `Turn each breach into a dated task for ${ownerW} the morning it appears, so it is handled the same day instead of found on the Watch.`;
      risk = `More tasks for ${ownerW} until the standard holds. Undo turns it off at once; nothing touches money or a record.`;
      accept = ["The Standard Watch shows no breach of it on any day in the 30 days after.", "Every breach in between was a task, done the day it appeared."];
    } else if ("lesson" === g.family) {
      title = `The lesson "${g.label}" did not stop it`;
      what = `Approved${g.atoms[0].approvedAt ? ` on ${D(g.atoms[0].approvedAt)}` : ""}, and the same thing happened ${plural(g.n, "time")} since. A reminder is not enough here.`;
      g.atoms.slice(-5).forEach((a) => ev.push({ t: `${D(a.day)}: ${clean(a.text, 200)}`, m: "the Brain's lessons" }));
      fix = "Make it a hard stop in the ERP at the moment it happens (a hold, a required field or a check before the record can move on), not a reminder after.";
      risk = "A hard stop can slow the person who meets it; the build names who and when, and the owner can release it with a reason.";
      accept = ["The event the lesson was about cannot happen without the stop being met or released with a reason.", "None of it for 30 days after the release."];
    } else {
      title = clean(g.label || `${screen}: a finding`, 140);
      what = `${plural(g.sids.length, "finding")} from ${g.atoms.map((a) => a.source).filter(Boolean)[0] || "the agents and workshops"} on ${screen}${g.atoms.some((a) => /^s?1$/.test(a.sev)) ? " (severity 1)" : g.atoms.some((a) => /^s?2$/.test(a.sev)) ? " (severity 2)" : ""}.`;
      g.atoms.slice(-5).forEach((a) => ev.push({ t: clean(a.text || a.label, 240), m: a.source || "a finding" }));
      fix = clean(g.atoms.map((a) => a.fix).filter(Boolean)[0], 400) || "As the finding says; fix the class, not the instance.";
      risk = "A change to the ERP, built behind the full test net; the release waits for the owner.";
      accept = ["The reviewer who found it walks it again and it is gone.", "A check that would have caught it is in the net."];
    }
    return { title: clean(title, 140), what: what, evidence: ev.slice(0, 10), fix: fix, risk: risk, kind: kind, delta: delta, accept: accept, p: g.p || "" };
  }

  // The order: the Standard's decision principle first, then someone stuck, then how many people, then how often.
  function rankKey(g, order) {
    const O = order && order.length ? order : PRINCIPLES, i = O.indexOf(g.p);
    return [i < 0 ? O.length : i, g.stuck ? 0 : 1, -(g.people || 0), -(g.n30 || g.n || 0)];
  }
  const cmp = (a, b) => { for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] - b[i]; return 0; };

  // Everything the loop does with the signals today: new drafts, the open ones updated, the fixed ones a person says
  // are still wrong (reopened at once). `changes` are DB.changes; nothing is written here.
  function triage(signals, changes, today, opts) {
    const o = opts || {}, C = changes || [], out = { drafts: [], updates: [], reopen: [] };
    const G = group(signals, today).filter(qualifies);
    G.sort((a, b) => cmp(rankKey(a, o.order), rankKey(b, o.order)));
    let rank = 0;
    G.forEach((g) => {
      const key = "imp:" + g.gkey, have = C.find((c) => c && c.key === key);
      const loop = { gkey: g.gkey, family: g.family, screen: g.screen, what: g.what, p: g.p, people: g.people, roles: g.roles.slice(), uids: g.uids.slice(), signals: g.sids.slice(-60), n: g.n, n30: g.n30, days: g.days.length, stuck: g.stuck, first: g.first, last: g.last };
      if (!have) { rank++; out.drafts.push({ key: key, loop: Object.assign(loop, { rank: rank }), d: draft(g, o.names) }); return; }
      if ("declined" === have.status) return;
      const open = ["draft", "approved", "requested"].includes(have.status);
      open && (loop.rank = ++rank);
      out.updates.push({ key: key, loop: loop, d: open ? draft(g, o.names) : null });
      // a person who reported it says the fix did not work: reopen now, not in a month
      const live = have.loop && (have.loop.liveAt || have.loop.appliedAt);
      if (["live", "requested"].includes(have.status) && live && g.atoms.some((a) => a.still && a.day >= day(live))) out.reopen.push({ key: key, why: "a person who reported it says it is still wrong" });
    });
    return out;
  }

  // A month after a fix went live: did the problem stop? Before = the 30 days up to the fix, after = the 30 after it.
  function verify(change, signals, today) {
    const L = (change && change.loop) || {}, at = day(L.liveAt || L.appliedAt);
    if (!at || L.verified || daysBetween(at, today) < MONTH) return null;
    const A = atoms(signals).filter((a) => a.gkey === L.gkey);
    const sum = (from, to) => A.filter((a) => a.day >= from && a.day < to).reduce((s, a) => s + (a.n || 0), 0);
    // the day it went live counts as before: what was reported that morning was reported against the old version
    const before = sum(addDays(at, -MONTH), addDays(at, 1)), after = sum(addDays(at, 1), addDays(at, MONTH + 1));
    const stopped = 0 === after || (before > 0 && after <= before / 4);
    return { at: today, before: before, after: after, result: stopped ? "stopped" : "repeat" };
  }

  // Found against fixed, time to fix, repeats.
  function stats(changes, today) {
    const L = (changes || []).filter((c) => c && "loop" === c.source && c.loop);
    const live = L.filter((c) => "live" === c.status), open = L.filter((c) => ["draft", "approved", "requested"].includes(c.status));
    const ttf = live.map((c) => daysBetween(c.loop.first || c.at, c.loop.liveAt || c.loop.appliedAt || c.at)).filter((n) => n >= 0).sort((a, b) => a - b);
    const median = ttf.length ? (ttf.length % 2 ? ttf[(ttf.length - 1) / 2] : Math.round((ttf[ttf.length / 2 - 1] + ttf[ttf.length / 2]) / 2)) : null;
    const m30 = addDays(today, -MONTH);
    return {
      found: L.length,
      found30: L.filter((c) => day(c.at) >= m30).length,
      open: open.length,
      waiting: L.filter((c) => "draft" === c.status).length,
      building: L.filter((c) => ["approved", "requested"].includes(c.status)).length,
      fixed: live.length,
      held: live.filter((c) => c.loop.verified && "stopped" === c.loop.verified.result).length,
      checking: live.filter((c) => !c.loop.verified).length,
      declined: L.filter((c) => "declined" === c.status).length,
      reverted: L.filter((c) => "reverted" === c.status).length,
      repeats: L.filter((c) => (c.loop.reopened || 0) > 0).length,
      medianDays: median,
      byPrinciple: PRINCIPLES.map((p) => ({ p: p, n: open.filter((c) => c.loop.p === p).length })).filter((x) => x.n),
    };
  }

  // §1.32 item 3: what admin is due today. Renewals on the obligations register inside their lead time (renewLead, 30
  // days unless set), and vendors' insurance certificates lapsing within 30 days while an order is open with them (the
  // Standard: certificates 30 days ahead). Each with the person who chases it: the obligation's owner when that names
  // a person, else the coordinator, else the owner. D holds users, obligations, vendors and pos.
  function adminDue(D, today) {
    const U = D.users || [], out = [];
    const coord = U.find((u) => "coord" === u.role) || U.find((u) => "owner" === u.role) || {};
    const lc = (s) => String(s || "").trim().toLowerCase();
    (D.obligations || []).forEach((o) => {
      if (!o || "active" !== o.status || !o.expires || day(o.expires) < today) return;
      const start = addDays(o.expires, -(+o.renewLead || 30));
      if (start > today) return;
      const who = U.find((u) => u.name && u.name === o.owner) || coord,
        v = (D.vendors || []).find((x) => lc(x.name) === lc(o.party));
      out.push({ key: `ob:${o.id}:${day(o.expires)}`, kind: "renewal", what: `${o.name}${o.number ? " · " + o.number : ""}`, party: o.party || "", email: (v && v.email) || o.email || "", expires: day(o.expires), start: start, uid: who.id || "", ref: { kind: "obligation", id: o.id } });
    });
    const on = new Set((D.pos || []).filter((po) => po && ["issued", "partial", "pending", "approved"].includes(po.status)).map((po) => lc(po.vendor)));
    const to = addDays(today, 30);
    (D.vendors || []).forEach((v) => {
      if (!v || !on.has(lc(v.name)) || !v.insuranceExp || day(v.insuranceExp) < today || day(v.insuranceExp) > to) return;
      out.push({ key: `coi:${v.id}:${day(v.insuranceExp)}`, kind: "coi", what: `${v.name}: certificate of insurance`, party: v.name, email: v.email || (/@/.test(v.contact || "") ? v.contact : ""), expires: day(v.insuranceExp), start: addDays(v.insuranceExp, -30), uid: coord.id || "", ref: { kind: "vendor", id: v.id } });
    });
    return out;
  }

  return { PRINCIPLES, P_WORDS, RP, US, WINDOW, MONTH, ROLE_WORDS, day, addDays, daysBetween, norm, atoms, group, qualifies, draft, rankKey, triage, verify, stats, adminDue };
})();
if ("undefined" != typeof module && module && module.exports) module.exports = LOOP_CORE;
