/* ---------------------------------------------------------------------------------------------------------------------
   The Ask families (founder review, wave 3: BACKLOG section 11, rows 20 to 23; tests/ask_family_test.py and the Ask
   question bank, tests/ask_bank_tune.json ids AF*).

   What was wrong. Ask is a chain of readers, each with its own regular expression, and under them a keyword table
   (QA_ENTITY) that answers with whichever record list a word names. A plain question no reader claimed fell to the
   keyword table and got a list: "where is money leaking" matched "where is" and listed the inventory; "what haven't
   we billed" matched "billed" and listed the invoices that HAVE been billed; "what did we promise the Kleins" and
   "what do we owe the Kleins" were claimed by two readers that read two different stores, and the promise reader
   said "none" from an empty ledger while the client waited on three tasks.

   The class fix. A question a person asks many ways is a FAMILY: one entry names its phrasings and one answer
   function that reads what the screen owning the number reads. The families ride at the head of the first readers
   (AG_ASST, first), so no phrasing falls past its answer to the keyword table; no new paAsk layer. The older readers
   for the same questions call the same functions (the unbilledwork reader, the "owed" reader for a client and the
   owe answer in src/p2nav.js), so there is one answer however the question arrives. Every family answer carries
   `family` (its id) and `fam` (its count and total), which tests/ask_family_test.py compares with the screen.

     family     answers from                                                the screen that owns the number
     leaks      tdCaught(td2Model().M.appr)                                 Today, "N caught for you"
     unbilled   readyToBill() rows and held lines                           Billing Queue, the Ready to Bill tile
     promises   tasks owed to the client, the promise ledger, the           Tasks (Owed to the Client); Standard Watch
                Standard's client rules past their time
   ------------------------------------------------------------------------------------------------------------------ */

// words the typo reader must take as typed ("leaking" was read as "looking")
"undefined" != typeof AG_DICT &&
  "leak leaks leaking leaked leakage unbilled uninvoiced invoiced promised owing".split(" ").forEach((w) => AG_DICT.add(w));

const afRole = () => {
  try {
    return role();
  } catch (e) {
    return "";
  }
};
const AF_OFFICE = ["owner", "pm", "coord", "billing", "controller"],
  AF_MONEY = ["owner", "pm", "billing", "controller"];
const afSum = (L, f) => r2((L || []).reduce((a, x) => a + (+f(x) || 0), 0));
// nobody and nothing named: the question is about the whole firm
const afGeneral = (P) => !P.jobs.length && !P.clients.length && !P.vendors.length && !(P.people || []).filter((e) => e !== P.meEmp).length;
// the standard behind a row, in its own words, and its short source ("Office playbook")
function afStdWhy(it) {
  try {
    return String(standardWhy(it) || "").replace(/^Because:\s*/, "");
  } catch (e) {
    return "";
  }
}
const afStdSource = (it) => (afStdWhy(it).match(/\(([^()]+)\)\s*$/) || [])[1] || "";

// ---- leaks: Today's Caught for You ---------------------------------------------------------------------------------
// The same rows, in the same number, as Today's "N caught for you". A row is money when the Standard files it under
// cost or integrity and it carries dollars (work not billed, a payment with no match, a credit never taken); those
// lead, largest first. The rest would slip without a dollar lost today (a missing certificate, a lead gone quiet,
// whose figure is the deal's value, not money lost) and follow.
function afLeakRows() {
  let R = [];
  try {
    R = tdCaught(td2Model().M.appr) || [];
  } catch (e) {
    console.warn("ask leaks", e);
  }
  const isMoney = (x) => {
    if (!(+x.amount > 0)) return !1;
    try {
      const e = standardMapOf(standardKey(x)).e || {};
      return !!e.leak || "cost" === e.p || "integrity" === e.p;
    } catch (e) {
      return !1;
    }
  };
  return R.map((x, i) => ({ x: x, i: i, money: isMoney(x) })).sort((a, b) => (a.money === b.money ? (+b.x.amount || 0) - (+a.x.amount || 0) || a.i - b.i : a.money ? -1 : 1));
}
// Where a caught row's Open goes: the record its key names, else Today's Caught for You, where its own button is.
function afLeakGo(x) {
  const k = String(x.key || ""),
    pid = (k.match(/(?:^|:)(p\d+\w*)(?::|$)/) || [])[1] || (x.p && x.p.id) || "",
    can = (v) => {
      try {
        return paCanSee(v);
      } catch (e) {
        return !1;
      }
    };
  if (/^(um|txn):/.test(k) && can("bank")) return { view: "bank" };
  if (/^(rtb|held):/.test(k) && can("billing")) return pid ? { view: "billing", project: pid } : { view: "billing" };
  if (/^chase:lead:/.test(k) && can("leads")) return { view: "leads" };
  if (/^task:/.test(k) && can("tkall")) return { view: "tkall" };
  if (pid && can("dash")) return { view: "dash", project: pid };
  return { view: "home", tdQuiet: 1 };
}
function afLeaks(P) {
  const R = afLeakRows(),
    M = R.filter((r) => r.money),
    O = R.filter((r) => !r.money),
    plain = (s) => ("function" == typeof tdPlain ? tdPlain(s) : String(s || "")),
    what = (r) => plain(r.x.what).replace(/\s+/g, " ").trim(),
    row = (r) => {
      const src = afStdSource(r.x),
        m = +r.x.amount > 0 ? money(r.x.amount) : "",
        // the row's own words often open with its figure ("$33,500 on 8/25"): the figure is said once
        sub = String(plain(r.x.sub || "")).replace(/\s+/g, " ").trim(),
        rest = m && sub.startsWith(m) ? sub.slice(m.length).replace(/^[\s,:·-]+/, "") : sub;
      return `${what(r)}${m ? ` · ${m}` : ""}${rest ? ` · ${rest.length > 110 ? rest.slice(0, 110).replace(/\s+\S*$/, "") + "…" : rest}` : ""}${src ? ` (${src})` : ""}`;
    },
    top = M.slice(0, 3).map((r) => `${what(r)} ${money(r.x.amount)}`),
    seen = new Set();
  return {
    headline: R.length
      ? `${agN(R.length, "thing")} caught for you, the same list as Today. ${M.length ? `${agN(M.length, "is", "are")} money, largest first: ${agList(top, 3)}${M.length > 3 ? `, and ${M.length - 3} more below` : ""}.` : "None carries a dollar figure."}${O.length ? ` ${agN(O.length, "other")} would slip without a dollar lost today: ${agList(O.slice(0, 2).map(what), 2)}${O.length > 2 ? ` and ${O.length - 2} more` : ""}.` : ""}`
      : "Nothing is caught for you right now: no leak the checks can see.",
    note: R.length
      ? `${M[0] && afStdWhy(M[0].x) ? `The largest rests on: ${afStdWhy(M[0].x)}. ` : ""}${"undefined" != typeof STD_WASTE ? STD_WASTE + " " : ""}Each row carries its own figure; they are not summed, because one dollar can be caught by two checks (a credit with no return is also a bank line not matched).`
      : "Read from the same checks as Today's Caught for You.",
    work: R.map(row),
    // each row's name opens its record (the first time a name appears; a name caught twice opens the first)
    links: R.map((r) => ({ text: what(r), label: "Open", go: afLeakGo(r.x) })).filter((L) => L.text && !seen.has(L.text) && seen.add(L.text)),
    go: { view: "home", tdQuiet: 1 },
    ran: agRan("Caught for You (tdCaught)", ["ranked by dollars"], "", R.length),
    family: "leaks",
    fam: { n: R.length, money: M.length, top: M[0] ? r2(M[0].x.amount) : 0 },
  };
}

// ---- unbilled: Ready to Bill -----------------------------------------------------------------------------------------
// The Billing Queue's Ready to Bill rows and total, the figure its tile shows. An application's rows carry the lines
// behind it, each on its own evidence (lkUnbilledWork, the job's Contract and Billing reading). A design fee billed
// by milestone or by the hour is one row, its milestone or its hours: its phases are not billed line by line.
const AF_RTB_SAY = { dmilestone: "milestone reached", dhours: "design hours banked", application: "measured work, line by line", progress: "work in place", reimbursable: "bought for the client, not billed back", floated: "materials delivered, not billed", deposit: "deposit due", retainer: "retainer due" };
function afUnbilled(P) {
  const R0 = readyToBill() || { rows: [], held: [] },
    on = (r) => agOnJob(P, r.p && r.p.id) && (!P.clients.length || P.clients.some((c) => r.c && r.c.id === c.id)),
    R = (R0.rows || []).filter(on),
    H = (R0.held || []).filter(on),
    tot = afSum(R, (r) => r.amount),
    ht = afSum(H, (h) => h.amount),
    where = P.jobs.length ? ` on ${agShort(P.jobs[0])}` : P.clients.length ? ` for ${P.clients[0].name}` : "",
    say = (r) => AF_RTB_SAY[r.kind] || "earned",
    lines = [...new Set(R.filter((r) => r.p && "application" === r.kind).map((r) => r.p))].flatMap((p) => {
      let W = [];
      try {
        W = lkUnbilledWork(p.id).filter((w) => !w.held);
      } catch (e) {}
      return W.map((w) => `${agShort(p)} · ${w.co ? w.co + " " : ""}${w.desc}: measured ${Math.round(w.measured)}%, billed ${Math.round(w.billed)}%, ${money(w.amount)} not billed`);
    });
  let why = "";
  try {
    why = afStdWhy({ src: "earnedNotBilled", key: "rtb:" });
  } catch (e) {}
  return {
    headline: R.length
      ? `${money(tot)} is earned or bought and not billed${where}, on ${agN(R.length, "item")}: ${agList(R.map((r) => `${agShort(r.p) || (r.c && r.c.name) || ""} ${money(r.amount)} (${say(r)})`), 5)}.${H.length ? ` ${money(ht)} more is held on ${agN(H.length, "line")}, each with its reason.` : ""}`
      : `Nothing is waiting to be billed${where}: $0.${H.length ? ` ${money(ht)} is held on ${agN(H.length, "line")}, each with its reason.` : ""}`,
    note: `The same rows as Ready to Bill on the Billing Queue: measured work not billed, a design milestone reached, design hours banked, and what was bought for a client and not billed back.${why ? ` The standard: ${why}.` : ""} Money not billed cannot go to raises, bonuses, more staff, charity or extra value for the client.`,
    work: R.map((r) => `${r.title || agShort(r.p)}${r.why ? ` · ${r.why}` : ""}`)
      .concat(lines)
      .concat(H.map((h) => `Held · ${agShort(h.p)} · ${money(h.amount)}: ${h.why}`)),
    go: agGo("billing"),
    ran: agRan("ready to bill (readyToBill)", (P.clients.length ? [`client is ${P.clients.map((c) => c.name).join(" or ")}`] : []).concat(agWhereJob(P)), "", R.length),
    family: "unbilled",
    fam: { n: R.length, total: tot, held: H.length, heldTotal: ht },
  };
}

// ---- promises: what we owe a client ----------------------------------------------------------------------------------
// One answer for "what did we promise", "what do we owe" and "what are we committed to" a client: the open tasks they
// are waiting for (Tasks, Owed to the Client), promises in mail and meeting next steps not yet a task (the promise
// ledger), and the Standard's client rules past their time on this client's jobs and mail (Standard Watch). An empty
// ledger is one source that found nothing; the answer reads all three before it says "none".
function afClientStd(c) {
  const out = [],
    seen = new Set(),
    jobs = (DB.projects || []).filter((p) => p.clientId === c.id),
    names = [c.name].concat((c.contacts || []).map((k) => k && k.name)).filter(Boolean).map((n) => String(n).toLowerCase()),
    mails = new Set([c.email].concat((c.contacts || []).map((k) => k && k.email)).filter(Boolean).map((e) => String(e).toLowerCase()));
  ("undefined" != typeof STANDARD_RULES ? STANDARD_RULES : [])
    .filter((R) => "client" === R.p && !1 !== R.measured)
    .forEach((R) => {
      let rows = [];
      try {
        rows = standardRuleRows(R) || [];
      } catch (e) {}
      rows.forEach((r) => {
        const cmId = (r.c && r.c.id) || (String(r.key || "").match(/^(?:mail|cm):(.+)$/) || [])[1] || "",
          cm = r.c || (cmId && (DB.comms || []).find((x) => x.id === cmId)) || null,
          route = (cm && cm.route) || {},
          pid = (r.p && r.p.id) || (String(r.key || "").match(/^upd:(.+)$/) || [])[1] || route.projectId || route.existingJob || "",
          mine =
            jobs.some((p) => p.id === pid) ||
            route.clientId === c.id ||
            (cm && (mails.has(String((cm.from || {}).email || "").toLowerCase()) || names.includes(String((cm.from || {}).name || "").toLowerCase()))) ||
            (r.q && jobs.some((p) => (p.clientQs || []).includes(r.q)));
        // one message is one breach, whichever reading of the rule found it
        const k = cmId ? "cm:" + cmId : String(r.key || r.what);
        if (!mine || seen.has(k)) return;
        seen.add(k);
        out.push({ rule: R, r: r, what: r.what, sub: r.sub || "", source: afStdSource({ kind: "std", rule: R.id, src: "std:" + R.id, key: r.key }) });
      });
    });
  return out;
}
function afPromises(P, subj) {
  const c = P.clients[0];
  if (!c) return null;
  const me = "function" == typeof tkMe ? tkMe() : "",
    T = t2Sort(openTasks("all").filter((x) => tkOwedBy(x, "client") && (tkClientOfTask(x) || {}).id === c.id)),
    mine = T.filter((x) => tkOwnerMatch(x.assignee, me)),
    pids = (DB.projects || []).filter((p) => p.clientId === c.id).map((p) => p.id),
    names = [c.name]
      .concat((c.contacts || []).map((k) => k && k.name))
      .flatMap((n) => String(n || "").toLowerCase().split(/[^a-z]+/))
      .filter((w) => w.length >= 4 && !/^(family|llc|inc)$/.test(w)),
    toClient = (x) => "promise" === x.kind || /\bclients?\b/i.test(nsText(x)) || names.some((w) => new RegExp(`\\b${w}(s|'s)?\\b`, "i").test(nsText(x))),
    key = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim().slice(0, 40),
    have = new Set(T.map((x) => key(x.title)));
  let L = [];
  try {
    L = nsOwed({ pids: pids }).filter((x) => toClient(x) && !have.has(key(x.title)));
  } catch (e) {}
  const S = afClientStd(c),
    n = T.length + L.length + S.length,
    late = T.filter((x) => x.late).length,
    who = "i" === subj ? "You and the firm owe" : "We owe",
    tline = (x) => `${x.code ? x.code + " " : ""}${tdWords(x.title, 9)}${x.due ? `, ${x.due < today() ? "late since" : "due"} ${fmtL(x.due)}` : ", no date"} (${tkFirst(x.assignee) || "nobody yet"})`,
    parts = [T.length ? `${agN(T.length, "open task")}${late ? ` (${late} late)` : ""}` : "", L.length ? `${agN(L.length, "promise or next step", "promises and next steps")} not yet a task` : "", S.length ? `${agN(S.length, "thing")} past the Standard` : ""].filter(Boolean),
    last = String(c.name).split(/\s+/).pop();
  return {
    kind: "tasks",
    headline: n
      ? `${who} ${c.name} ${agN(n, "thing")}: ${agList(parts, 3)}.${S.length ? ` Past the Standard: ${agList(S.map((s) => `${s.what}${s.sub ? ` (${s.sub})` : ""}`), 2)}.` : ""}`
      : `Nothing is owed or promised to ${c.name} right now: no open task they wait for, no promise in mail or a meeting, nothing past the Standard.`,
    work: T.map(tline)
      .concat(L.map((x) => `${x.title} · ${x.owner || "nobody"} · ${x.due ? fmtL(x.due) : "no date"} · ${x.from}`))
      .concat(S.map((s) => `Past the Standard: ${s.what}${s.sub ? ` · ${s.sub}` : ""}${s.source ? ` (${s.source})` : ""}`)),
    note: `Open tasks on ${c.name}'s jobs that they are waiting for (Tasks, Owed to the Client)${"i" === subj && T.length ? `, ${mine.length} of them yours` : ""}; promises in mail and meeting next steps not yet tasks; and the Standard's client rules past their time (client messages acknowledged within 2 business hours, the Friday update). What ${c.name} owes us is a money question: ask "what do the ${last}s owe us".`,
    go: { view: "tkall", tkOwed: "client", project: "" },
    ran: agRan("tasks owed to the client, the promise ledger, meeting next steps and the Standard's client rules", [`client is ${c.name}`, "open"], "", n),
    family: "promises",
    fam: { n: n, tasks: T.length, ledger: L.length, standard: S.length },
  };
}

// ---- the families, at the head of the first readers --------------------------------------------------------------------
// re and not are tested on the question as agParse reads it: lowercased, typos read, "haven't" spelt "have not".
const ASK_FAMILIES = [
  {
    id: "leaks",
    kind: "ops",
    roles: AF_OFFICE,
    re: /\bleak(s|ing|ed|age)?\b|\b(losing|lose|lost|wasting|waste|bleeding|burning) (us )?money\b|\bmoney (is |are )?(slipping|draining|wasted|lost|being wasted)\b|\bwhere (are|is) (we|the firm|the company) (losing|bleeding|wasting)\b|\bwhat (did|have) you (catch|caught)\b|\bcaught for (me|us)\b|\bwhat (was|is|got) caught\b/,
    not: /\b(roof|pipes?|water|plumb\w*|faucet|valve|ceiling|basement|gas|radiator|shower|toilet|windows?|skylight|inspection|data|password|memory)\b/,
    ok: afGeneral,
    answer: afLeaks,
  },
  {
    id: "unbilled",
    kind: "money",
    roles: AF_MONEY,
    re: /\bun-?(billed|invoiced)\b|\bnot (yet )?(been )?(billed|invoiced)\b|\b(have|has|did|do|does|is|are|was|were) (we |i |they )?not (yet )?(been )?(billed|invoiced|bill|invoice)\b|\b(have|has|did|do|does) not (we |i |they )(yet )?(bill|billed|invoice|invoiced)\b|\bnever (been )?(billed|invoiced)\b|\bto be (billed|invoiced)\b/,
    not: /\b(bought|buy|buying|purchas\w*|receipts?|cards?|change orders?|cos?|pos?|purchase orders?|held|hold|holding|design hours|banked|billed us|retainage|deposits?|backlog|hours|vendors?|bills?)\b|\bco-\d|\b(left|remaining|still) to bill\b/,
    ok: (P) => !P.vendors.length && !(P.people || []).filter((e) => e !== P.meEmp).length,
    answer: afUnbilled,
  },
];
"undefined" != typeof AG_ASST &&
  AG_ASST.unshift(
    ...ASK_FAMILIES.map((F) => ({
      id: "family:" + F.id,
      first: !0,
      kind: F.kind,
      re: F.re,
      not: F.not,
      run(P) {
        if (!F.roles.includes(afRole())) return null;
        try {
          if (F.ok && !F.ok(P)) return null;
        } catch (e) {
          return null;
        }
        const a = F.answer(P);
        return a ? Object.assign(a, { family: F.id }) : null;
      },
    })),
  );
