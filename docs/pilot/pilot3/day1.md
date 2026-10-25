# Pilot 3, day 1 (Thu 9/3): the owner and the PM

Alan, 10-25: the pilot must give real feedback on day-to-day work, the data and how it is shown, phone and desktop. A lean run inside the last quarter of the week: day 1 the owner and the PM, day 2 the PM and the coordinator. Build: Buy Board and client documents on top of the navigation build (pilot3-build 530b85e). The invented job: the Ashbys, 214 Lincoln Place, a 12-line takeoff worth $91,120.

Full diaries: `diary/u_owner.md`, `diary/u_alan.md`. The realism judge: `judge/`. Harness faults and how they were handled: `conductor_notes.md`.

## The numbers
| | Owner | PM |
|---|---|---|
| Turns, actions | 4 turns, 82 actions | 4 turns, 147 actions |
| Grade, desktop | 5 | 5 |
| Grade, phone | 5 | 4 |
| Realism judge | 4 turns, 2 flagged (out of order; a guess not checked) | 4 turns, 2 flagged (client mail sorted late, twice) |
| Coverage of the main module | 36% (not a valid grade) | 16% of Projects (not a valid grade) |

**Business cycle (referee, from the raw records):** 2 of 35 steps right, 3 wrong, 30 not done. Most are day 2 and 3 work. The ones that should be done by now:
- No project for the Ashbys.
- The lead was never marked won.
- The estimate is one line ($1,400 against the $91,120 takeoff).
- The Friday review did not look at a single job page.

**Cost, measured:**
- 8 turns: 768,218 tokens (about 96k a turn).
- 2 judges: 199,589 tokens.
- Day 1 in all: about 0.97M tokens.

## Two harness faults (fixed during the day, discounted)
1. **Ask.** The toolkit looked for the old icon button and told the owner there was no assistant. The app's labelled Ask works.
2. **News.** The toolkit dropped what a person had been told after one read. The owner's 12-line takeoff, told to both at 7:30, was gone by the next turn, so the 10:00 estimate turn had no lines to key. Now everything heard is kept in the person's notes.

## What they found, by how much it hurts

**Severity 1 (blocks the work or risks money)**
- **The phone cannot build an estimate.** Add Line Item does nothing, and tapping a line does nothing (the PM, 13:30 and 14:06). Pilot 2's PM hit the same thing. Being reproduced.
- **A held bill still shows a blue Approve.** WW-2026-118 was paid on the Amex before approval and $3,800 over its PO. "The tap I fear most."
- **"Draft the Renewal" opens Record the Filing** with today's date already in Filed On: an easy false record of a filing that never happened.
- **"PM recommended" was stamped on a bill the PM never recommended.**
- **"Mark Sent" is the first button under a draft estimate** the owner has not reviewed.
- **The assistant answered a different question every time:**
  - "POs today" for the PM's PO check.
  - Retainage for "draft the estimate".
  - AP only for "AR, AP, Zelle, jobs at risk".
  - A mail search for "who is Aliya Chen".

  The model was never called, because the built-in rules gave a confident wrong answer first.

**Severity 2 (slows the work daily)**
- **No "I owe" list.** Promises made by phone and mail ("by 5 pm", "by noon") live nowhere. The PM missed three and a client went two days without an answer.
  - The 2-hour client acknowledgement is a Standard the ERP should check, and it did not.
  - A promise the PM made to the owner showed on the owner's Today.
- **Estimates are buried.**
  - Estimates are not in the PM's menu.
  - Opening one is Clients, the client, Billing, Estimates, the row.
  - The client Overview shows no estimate.
  - The estimate's Project field is empty with no options, so it cannot be tied to the job.
- **What clients owe us is nowhere.** Overdue AR $0.00 is the only figure. The owner looked in five places.
- **Today's order.** An LLC renewal and two meeting bookings sat above the $33,500 paid-before-approval bill. 61 items on All and 34 approvals cannot be triaged standing on a phone.
- **Money disagrees with itself.** The $9,500 Zelle is in a bank alert in Messages but not in the bank lines.
- **Hand-offs are mail, not tasks.** Nothing the owner or the PM handed on became a task with a due time the app chases, and neither could see whether it was read.

**Severity 3 (annoys)**
- Payroll approval: 3 taps, the toast twice, then a jump to Tasks.
- "Jobs at Risk" opened Messages; "Organize" opened Tasks.
- The Hold sheet appeared only after the next tap.
- The estimate footer said 15-day terms against the 30 typed.
- "Add" under Quotes made a client but no estimate.
- "Estimates1" reads as a tab label.

## What worked (keep it)
- **The estimate form, once reached:** rate, quantity, unit, cost and margin on each line; internal notes that do not print; allowances and exploratory phases for old buildings; "All changes saved".
- **The Window Works bill page:** over its PO, paid before approval, insurance expired and bank details changed, in one place. "What a controller should see."
- **Today's three numbers** at 7:30: Safe to Spend, Overdue AR and Jobs at Risk.
- **Banking's breakdown of Safe to Spend.**
- **Lead to opportunity in two taps.**
- **Mail and calls are quick** on both devices.

## What it tells us about the build
1. **The estimate is the PM's most important document and it is broken on the phone and hard to reach on the desktop.** Fix both before anything else on the PM's path: Add Line Item on the phone; Estimates in the menu and on the job; the project on the estimate; paste or propose a takeoff for approval.
2. **Wave 3 (it remembers) is the PM's biggest gap:** one "I owe" list from mail, calls and tasks, with the promised time, and the 2-hour client rule checked.
3. **Wave 4 (the assistant) must route requests to the model.** A request to draft or do goes to the model. An answer that does not match the question counts as no answer.
4. **Dangerous buttons are a class:**
   - Approve on a held or paid bill.
   - Record on a draft action.
   - Mark Sent on an unreviewed draft.
   - A stamp in someone's name they did not give.

   One check for all of them goes into the net.
5. **The Today rebuild (running) already addresses** the order (what needs you, by the Standard's order) and the noise (five items and "N more").

## Day 2
The PM and the coordinator. The PM's desk turn gets the room to key the 13 lines (90 actions, as on day 1). Day 2 is the coordinator's first day: RFQs from the estimate lines, quotes in four formats, the award and the POs on the new Buy Board.

**Estimate:** about 1.3M tokens. It rests on day 1's 96k a turn, with the coordinator's turns longer.
