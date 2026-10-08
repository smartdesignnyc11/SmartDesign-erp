# Foreman role — what shipped (2026-09-06)

Built from a 20-year design-build foreman's brief: *"I need to know what's happening today, what's going to stop me tomorrow, and one button to reach the person who can fix it — with a clock on their answer."*

## The role

- New role **Foreman** (Angel is the foreman on 121 State Street; Alberto, Satish stay Crew). Crew label renamed from "Foreman / crew" to "Crew".
- Phone: five bottom tabs — **Today · Raise · Site · Log · Crew**. Desktop: a "Field" group first in the rail with the same five screens, plus Schedule, Documents, Chat, Requests, Receiving, Tasks.
- No money anywhere on the foreman's screens: no budgets, margins, rates, vendor prices, CO dollars, client funds, KPIs or Gantt. Requests, receiving, schedule list and photos are the only shared pages.

## Today
Clock in/out at the top. Then, in order: **Today's work** (build-track tasks active today, owner, "N things missing" in red, Started / Done buttons, "Change the plan → PM", Call PM) · **Who's here** (each crew member: in since / hours / not in; each sub due today: on site / confirmed / no-show / Call — tapping *No-show* sends a raise to the PM and coordinator instantly) · **Coming to site** (deliveries expected today with Received / Problem; inspections today or tomorrow with a link to the prep list) · **Tomorrow** (auto-built blockers: material not on site, sub unconfirmed, decision open, drawing question open, inspection not passed, predecessor unfinished — each with a *still need this →* button that opens a pre-filled raise to the right person) · **Next two weeks** (build-track tasks per workday, green ready / amber missing something / red blocked; hover/tap for the reason).

## Raise
Eight big buttons, each pre-routed with an answer window:

| Type | Goes to | Copied | Window |
|---|---|---|---|
| I need something (material / sub / decision / drawing) | Coordinator | PM | 24 h |
| Drawing question | Designer | PM | 48 h |
| Hidden condition / extra | PM | — | 4 h |
| Sub no-show | PM | Coordinator | 2 h |
| Delivery problem | Coordinator | PM | 24 h |
| Inspection (ready / result) | PM | Coordinator (expeditor) | 24 h |
| Client asked me… | PM | — | 24 h |
| Safety incident (red) | PM | Owner | 1 h |

Each raise: one line (typed or spoken), sheet/detail for drawing questions, "what it would take" (hours/people/material — no dollars) for extras, which task it holds, who it goes to (changeable), need-by date, photos (compressed ~900 px). Drawing questions also land in the project's Field list as an RFI so nothing is double-entered.
Status flow: **sent → seen → answered → got it (closed)**. Past the window with no answer → **escalated**: the owner is copied, the foreman's row turns red and grows *Call PM* / *Call Owner* / *Still waiting* (bump). Answered items show the answer inline with a "Got it" button; extras show the PM's decision (proceed as extra / no charge / hold).

## Site
- **Subs — next two weeks**: date, for which task, company · lead, status. Confirmed / Here / No-show buttons, *Text lead* (pre-written "confirming you're at … Reply YES") and *Call*. "Add a sub day" for anything the office didn't schedule. Unconfirmed subs feed the amber on the look-ahead.
- **Deliveries**: POs and materials due in 14 days; Received (asks where it's staged, marks material on-site / PO received, logs it for the coordinator and PM), Problem (raise with photo), *Where is it?* for anything not yet ordered. Request material / tools, Call coordinator, Call driver.
- **Inspections**: upcoming with a **prep checklist** by type (plumbing: pressure test holding, joints exposed, permit + plans on site…; electrical; insulation/energy; LPC; final). *Ready — call it in* unlocks when the list is complete and sends to the PM + expeditor. On the day: Passed / Failed — a fail sends the PM what failed and asks for a re-inspection; a pass tells the PM the gated task is clear.
- **Punch list**: room, item, photo, assignee (crew or sub), open → done → verified.

## Daily log
Pre-filled from the day: weather + temp, crew on site with hours (from Clock), subs marked "here", deliveries received, work started/finished. Foreman adds what happened (typed or spoken) and photos, taps Send. The PM and owner see the last three logs under "From the field". This is the dispute record.

## Crew
This week per person (days, hours, OT flag, in/out today, Call). **Hours to approve**: the project's submitted entries with the engine's anomaly flags (late start, left early, far from site, no work logged, overlaps…). *Approve* one, *Approve N clean* at once, *Fix* (in/out/break + a note for the office, then approve). Safety: last toolbox talk, *Log toolbox talk* (topic list + attendees), amber after seven days; red *Report an incident*.

## The office side
- **PM / Owner / Coordinator — Field page**: "From the field" card at the top: every raise routed to me or copied to me, escalations first, with the foreman's note, photos, his take, and the task it holds. Answer (short and definite — it goes straight to the foreman's phone), or for extras: **Proceed as extra / Do it, no charge / Hold**. "Proceed as extra" creates a task *Write change order: …* for the PM. Hand-off buttons (hand to designer / coordinator). Call the foreman.
- **Coordinator — Requests page**: the same card filtered to material, delivery and no-show items.
- **Designer — My day**: "From the field" with drawing questions only; answering closes the RFI in the project too.
- **Brief / attention**: open field items show as "From the field: …" (sev 3 when escalated, incident, or past need-by), badge counts on Field.
- Viewing the card marks the item *seen* — the foreman can tell the difference between "sent" and "they've looked".

## Data points created (all queryable)
`DB.field.raises` (type, to, cc, dueBy, status, seen/answered/closed timestamps, escalated, decision, answer, guess, sheet, photos, taskId), `DB.field.subs` (sub day: vendor, lead, phone, date, task, status confirmed/onsite/noshow, timestamps), `DB.field.logs` (daily log: weather, temp, crew hours, subs, deliveries, work, notes, photos), `DB.field.punch`, `DB.field.talks`, inspection `prep`/`readyOn`/`resultOn`, material/PO `staged`/`receivedOn`, time `approvedBy`/`foremanFixed`, user `phone`.
Reports these enable later: response time by person and type, no-show rate by sub, blockers by cause, inspections first-pass rate, extras raised vs. CO written, daily-log compliance.

## Not built (next)
- Real push/SMS delivery (the raise is portal-only until email/SMS is turned on — same decision as Studio).
- Weather auto-fill (needs hosted app).
- Sub lead as a portal user who can confirm from a text reply.
- Client questions → PM → client thread (today it is a raise to the PM only).
- Foreman across multiple projects (assumes one active job; the switcher still works).

## Testing
`foreman_test.py` — phone (390) and desktop (1400): sign in as Angel, every screen, raise from "still need this", extra → PM decision → "got it", sub confirm/no-show, prep list → ready, receive with staging, punch, daily log send, approve hours / fix / approve all, toolbox talk, then Alan (Field + Brief), Chen (Requests), Sarah (My day) answering, escalation to Owner. Regression: accept 34/34, h4, home, studio — green. Screenshots in `screens/fm_*.png`.

---

# Voice-first layer (same day, after the foreman review)

Review verdict was a 4/10 for a foreman who talks rather than types: too many taps to raise anything, nothing came *to* him, crew questions had no answer, Today was too long, interruptions lost work, phone calls didn't close the loop. Built:

**Say it** — one mic button on every foreman screen (floating, bottom right; also the top of Raise). He taps and talks (or types); the app reads it and shows a one-line take before he sends: *Sub no-show → Alan · Chen copied · Restoration crew · 9/3*. Send is one tap; "Change details" opens the full form pre-filled. The reader (`fParse`) is rule-based so it works offline and on the file version; it finds the person by name or role ("Alan…", "tell Chen…", "the designer"), the kind from how he'd say it, and matches the task, material, sub, inspection, sheet number, staging spot and need-by date from the words. Sixteen realistic phrases pass in the test: no-show, drawing question with sheet, material need with a day, received + where staged, log note, hidden condition, inspection passed, sub confirmed, injury, task finished, client question, short delivery, punch item, plan change, generic need, spec question. Some phrases don't send anything — they *do* things: "received the insulation, it's in the garden by the door" marks it on site and staged; "Carlos confirmed for Tuesday" confirms the sub day; "done with framing" marks the task; "log: …" appends to today's log; "touch up …" adds a punch item. Injuries always go to the PM + owner regardless of who he names.

**For you** — a strip at the top of Today with everything the office sent him: answers to his questions (with the PM's decision in bold), messages from the office (plan change / delivery update / decision / drawing revised / note — the PM, coordinator and designer have a "Message the foreman" button on their From-the-field card), decisions made in the last five days, and sheets issued. Each with Got it.

**Now** — Today opens with a five-line card: who's not clocked in, sub no-shows / unconfirmed, things missing for today's work, deliveries expected, questions past due, and after 3:30 "Today's log not sent — Send as is". Tap any line to go there. On the phone, Who's here / Coming to site / Tomorrow / Next two weeks fold under their headers (Tomorrow opens itself when something isn't ready); folds remember. Desktop shows everything.

**Talked to them** — on any open question: what they said (typed or spoken), the decision for extras, or "no answer yet — just log the call". Closes the loop on phone calls so nothing escalates to the owner after it was settled by phone; calls are listed under the item.

**Ask about a room** — pick a room (Studio rooms with confirmed dimensions where they exist, takeoff rooms otherwise): dimensions on record with provenance (amber = from the listing, don't build off it), current drawings, decisions made, decisions still open ("don't build past these"), questions out, and the work scheduled there. "Ask the designer about this room" opens Say it pre-addressed.

**Drafts** — whatever he was saying survives an interruption: the Say it text is kept, the button shows an amber dot, and it comes back on the next tap.

Still not built: outbound texts/push and sub reply-to-confirm (needs the hosted app), AI reading of the transcript (the assistant can replace `fParse` when hosted — same output shape), weather auto-fill.
