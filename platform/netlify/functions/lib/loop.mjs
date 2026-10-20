// The improvement loop on the server (BACKLOG §1.19, §1.32 item 5: always on, not only while the app is open).
// Once a night it reads the firm's shared records (the signals people's devices synced, the changes, the obligations,
// vendors and orders; never anyone's private rows), runs the same rules the app runs (loop_core.cjs, a copy of
// src/loop_core.js that platform/build.py makes), and files the result in inboxes the app drains on opening:
//   - the owner's: new problems ranked by the Standard, fixes that did not hold a month later (reopen), fixes that did;
//   - each person's: the renewals and certificates that person chases today, which their app then handles under their
//     own rule for Renewal Chases (Act Alone, Ask First, Hand It to Me). The server sends nothing and changes no record.
// The wording can be improved by the small model when LOOP_AI=on (charged to the owner, inside the caps); without it
// the rules' wording stands.
import {rest} from './auth.mjs';
import {firmRecords} from './digest.mjs';
import CORE from './loop_core.cjs';
export {CORE};

const ORDER = (D) => {
  const P = (((D.company || {}).standard || {}).principles || []).map((p) => p && p.id).filter(Boolean);
  return P.length ? P : CORE.PRINCIPLES;
};
const fmt = (d) => { const t = new Date(String(d).slice(0, 10) + 'T12:00:00Z'); return isNaN(t) ? '' : t.toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric', timeZone: 'UTC'}); };
const SCREENS = {home: 'Today', sched: 'Schedule', po: 'Purchase Orders', billing: 'Billing', bank: 'Banking', ap: 'Bills & Payroll', req: 'Requests', flog: 'Daily Log', ftoday: 'Today', proc: 'Buy Board', clients: 'Clients', reports: 'Reports', time: 'Time & Crew'};

// Pure: what tonight's run files, from the records. Tested without a database.
export function plan(D, today) {
  const signals = Array.isArray(D.signals) ? D.signals : [], changes = Array.isArray(D.changes) ? D.changes : [];
  const T = CORE.triage(signals, changes, today, {order: ORDER(D), names: {screen: (v) => SCREENS[v] || v, date: fmt}});
  const drafts = T.drafts.map((x) => ({key: x.key, loop: x.loop, title: x.d.title, what: x.d.what, kind: x.d.kind, delta: x.d.delta, evidence: x.d.evidence, fix: x.d.fix, risk: x.d.risk, accept: x.d.accept, night: today}));
  const checks = changes.filter((c) => c && c.source === 'loop' && c.status === 'live').map((c) => ({key: c.key, v: CORE.verify(c, signals, today)})).filter((x) => x.v);
  const admin = {};
  CORE.adminDue(D, today).forEach((x) => { if (x.uid && !((D.company || {}).adminChase || {})[x.key]) (admin[x.uid] = admin[x.uid] || []).push(x); });
  return {drafts, reopen: T.reopen, checks, admin};
}

export async function runLoop(ws, {today, word} = {}) {
  const t = today || new Date().toISOString().slice(0, 10);
  const D = await firmRecords(ws);
  const P = plan(D, t);
  const people = await rest(`profiles?select=id,role,workspace_id,name,private_key,app_user_id&workspace_id=eq.${encodeURIComponent(ws)}`) || [];
  const owner = people.find((p) => p.role === 'owner');
  if (!owner) return {error: 'no owner in this workspace'};
  if (word && P.drafts.length) { try { await word(owner, P.drafts); } catch (e) { console.error('loop wording', e.message); } }
  const filed = [];
  if (P.drafts.length || P.reopen.length || P.checks.length) {
    await rest('rpc/watch_put_inbox', {method: 'POST', body: JSON.stringify({p_ws: ws, p_key: owner.private_key || owner.id, p_items: {loop: [{at: t, drafts: P.drafts, reopen: P.reopen, checks: P.checks}]}})});
    filed.push('owner');
  }
  // each person's renewals go to their own inbox (one person, several sign-ins: one private key)
  const seen = new Set();
  for (const [uid, items] of Object.entries(P.admin)) {
    const prof = people.find((p) => p.app_user_id === uid);
    if (!prof) continue;
    const k = prof.private_key || prof.id;
    if (seen.has(k)) continue;
    seen.add(k);
    await rest('rpc/watch_put_inbox', {method: 'POST', body: JSON.stringify({p_ws: ws, p_key: k, p_items: {admin: [{at: t, items}]}})});
    filed.push(uid);
  }
  return {drafts: P.drafts.length, reopen: P.reopen.length, checks: P.checks.length, admin: Object.values(P.admin).reduce((a, x) => a + x.length, 0), filed};
}
