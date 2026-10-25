# Pilot 2 (2026-10-25): the role experts' three days, phone and desktop

Alan, 10-25: "Run Pilot 2 after the phone lanes. Make sure they give feedback on the UI/UX for both mobile and desktop."

**What ran.** The same three days as Pilot 1 (9/3, 9/4, 9/8), with 30 more events covering the whole firm:
- prospect to client, estimate, contract, deposit and progress invoices;
- two change orders;
- a PO received one short, with its bill held;
- clock in and out to payroll;
- a portal question, hand-offs and the team meeting.

Nine role experts worked through the screens on build 0c3cd8f (taskfix and phonerows merged, before P0 money). Every office role had phone turns each day. Every tap was checked against its label. Each expert graded phone and desktop separately, and day 3 ended with five-second tests on both devices. Both workshops followed.

**The score** (`ledger.md`; the referee scores the world, not the players):
| | Pilot 1 (10-18) | Pilot 2 |
|---|---|---|
| Money left behind | $80,036 | $22,636 |
| Records the creator could not find again | 30 | 6 |
| Schedule days lost | 10 | 5 |
| Missed, Pilot 1's events | 30 | 20 |
| On time, all events | 25 of 56 | 40 of 68 |

**Taps:**
- **Phone:** 181 taps; 133 landed where the label said, 5 were dead.
- **Desktop:** 184 taps; 146 landed, 3 were dead.

**Grades, phone / desktop:**
| Role | Phone | Desktop |
|---|---|---|
| Owner | 5 | 6 |
| PM | 4 | 6 |
| Coordinator | 6 | 6.5 |
| Designer | 6 | 6.5 |
| Billing | 6 | 7 |
| Controller | 6 | 6 |
| Foreman | 6 | 5.5 |
| Crew | 7 | 7 |
| Driver | 6 | 5 |

Averages: phone 5.7, desktop 6.2.

**Cost, measured** (`cost.md`): 70 working turns used 5.76M tokens over 103 agent-minutes, and the workshops about 1.9M. That is about 7.7M in all, against an estimate of 20M.

**What it found** (`nav_workshop.md`, `docs_workshop.md`, the diaries, `conductor_notes.md`). These three are shared by all nine roles:
1. What each person owes sits in 3 to 7 places, with counts that disagree.
2. Buttons do something other than their label. Two of them posted money with no preview: a $7,400 bill was booked twice.
3. People reach each other only outside the app. Promises made by mail or call are tracked nowhere.

**Then:**
- Client documents print internal notes and allow $0 sends.
- Billing ahead of progress is never flagged.
- The phone estimate editor was dead.
- The assistant ignores "make a task" and answers the wrong question.
- Make It a Task gets the due date wrong.
- Unsaved sheets lose typing.
- Clock-out pre-ticks the wrong cost code.
- Meeting Mode was not found by the owner.
- The schedule ignores dated mail.

**Fix lanes started from it:**
- **p2fix1:** the dead phone editor, controls under the bar, names and pages. Merged and live.
- **p2fix2:** one bill per bank line, no blind posting, no cash without a bank line, the billed-ahead flag.
- **p2fix3:** client documents.

The rest is queued in `docs/PLAN.md`.

**Harness fixes before Pilot 3** (`conductor_notes.md`):
- Mail should take several recipients and cc, and resolve every colleague.
- The document measures must report what reached the person, not the stored record. "Missing" is the right column name.
- Action caps should allow a save at the end of a filled form.
