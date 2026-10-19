// What the nightly Brain reads: a compact digest of the firm's own records (jobs, schedule, decisions, materials,
// tasks, obligations, purchase orders, bills, change orders, meetings' next steps, what it already learned).
// Never anyone's mail, calendar or Drive: those live in private rows and are not read here.
import {rest} from './auth.mjs';
const day = s => String(s || '').slice(0, 10);
const cut = (s, n = 140) => String(s || '').replace(/\s+/g, ' ').slice(0, n);
export async function firmRecords(ws) {
  const rows = await rest(`collections?select=name,data&workspace_id=eq.${encodeURIComponent(ws)}&name=not.like.own:*`);
  const D = {projects: []};
  for (const r of rows || []) { if (r.name.startsWith('project:')) D.projects.push(r.data); else D[r.name] = r.data; }
  return D;
}
export function digest(D, today) {
  const late = (d) => d && day(d) < today;
  const out = {today, jobs: [], overdueTasksByOwner: {}, obligationsSoon: [], posLate: [], billsHeld: [], cosOpen: [], meetingSteps: [], learned: [], proposedAlready: []};
  for (const p of D.projects || []) {
    const pr = p.project || {};
    const tasks = (p.tasks || []).filter(t => !t.done && t.status !== 'done' && late(t.end || t.due));
    out.jobs.push({
      job: cut(pr.name, 60), phase: pr.phase || pr.status || '', end: day(pr.end || pr.finish), pctComplete: p.pct ?? pr.pct ?? null,
      lateSchedule: tasks.slice(0, 8).map(t => `${cut(t.name || t.title, 60)} (due ${day(t.end || t.due)}${t.owner ? ', ' + t.owner : ''})`),
      lateScheduleCount: tasks.length,
      openDecisionsLate: (p.decisions || []).filter(d => !d.decided && d.status !== 'decided' && late(d.due)).slice(0, 6).map(d => `${cut(d.title || d.name, 60)} (due ${day(d.due)})`),
      materialsLate: (p.materials || []).filter(m => m.status !== 'received' && late(m.need || m.needBy || m.due)).slice(0, 6).map(m => `${cut(m.name || m.item, 50)} (need ${day(m.need || m.needBy || m.due)}, ${m.status || 'open'})`),
      inspectionsUpcoming: (p.inspections || []).filter(i => i.date && day(i.date) >= today).slice(0, 4).map(i => `${cut(i.name, 50)} ${day(i.date)} ${i.status || ''}`),
      changeOrders: (p.changeOrders || []).filter(c => !['approved', 'void', 'billed'].includes(c.status)).slice(0, 5).map(c => `${cut(c.title || c.name, 60)}: ${c.status || 'draft'} since ${day(c.date || c.at)}`),
    });
  }
  for (const t of D.tasks || []) if (!t.done && t.status !== 'done' && late(t.due)) { const o = t.owner || t.assignee || 'nobody'; (out.overdueTasksByOwner[o] = out.overdueTasksByOwner[o] || []).push(`${cut(t.title, 70)} (due ${day(t.due)})`); }
  for (const k of Object.keys(out.overdueTasksByOwner)) out.overdueTasksByOwner[k] = out.overdueTasksByOwner[k].slice(0, 6);
  const in30 = new Date(Date.parse(today) + 30 * 864e5).toISOString().slice(0, 10);
  out.obligationsSoon = (D.obligations || []).filter(o => o.due && day(o.due) <= in30 && o.status !== 'done').slice(0, 12).map(o => `${cut(o.title || o.name, 70)} (due ${day(o.due)})`);
  out.posLate = (D.pos || []).filter(p => !['received', 'closed', 'void'].includes(p.status) && late(p.expected || p.eta || p.needBy)).slice(0, 12).map(p => `${p.number || p.id} ${cut(p.vendor || p.vendorName, 40)}: expected ${day(p.expected || p.eta || p.needBy)}, ${p.status || 'open'}`);
  out.billsHeld = (D.bills || []).filter(b => /hold|disput|mismatch/i.test(String(b.status || '') + ' ' + String(b.hold || ''))).slice(0, 12).map(b => `${cut(b.vendor, 40)} ${b.number || ''}: ${b.status || ''} ${cut(b.hold || b.note || '', 80)}`);
  out.meetingSteps = (D.meetings || []).flatMap(m => (m.steps || m.actions || []).filter(s => !s.done).map(s => `${cut(s.title || s.text, 80)} (${s.owner || 'no owner'}, from ${cut(m.title, 40)} ${day(m.date)})`)).slice(0, 15);
  out.learned = (D.lessons || []).filter(l => l.active !== false).map(l => cut(l.title, 90)).slice(0, 60);
  out.proposedAlready = (D.changes || []).filter(c => c.status !== 'declined').map(c => cut(c.title, 90)).slice(-60);
  return out;
}
export const standardText = D => String(((D.company || {}).standard || {}).body || '').slice(0, 40000);
