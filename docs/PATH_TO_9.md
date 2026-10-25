# The path to 9 (written 2026-10-25, after Pilot 2)

## Where we are, and why
| | Pilot 1 (10-18) | Pilot 2 (10-25) |
|---|---|---|
| Expert grades | mostly 4 to 6 | phone 5.7, desktop 6.2 (averages of nine roles) |
| Money left behind (same 3 days) | $80,036 | $22,636 |
| Records lost to their creator | 30 | 6 |

One week of fixes moved the money and the lost records a lot, but the grades only about one point. The experts did not mark us down for missing features. They marked us down for five things, and those five things are shared by every role:

1. **The app can't be trusted yet.**
   - A $7,400 bill was booked twice. One tap posted money with no review.
   - Unsaved sheets lost what was typed. A dead estimate page said "All changes saved".
   - Clock-out pre-ticked the wrong cost code, and Make It a Task set the wrong due date six times.

   A professional forgives a missing feature, never a wrong number or lost work. This caps every grade near 6.
2. **What I owe is in 3 to 7 places, and the counts disagree.** All nine roles said so: Today 35 against All 55, Buy Board 7 against 12.
3. **The app does not remember for you.**
   - Promises made by mail or phone are tracked nowhere.
   - A row stays open after the person closed the loop by mail.
   - A DOB notice moved an inspection and the calendar kept the old date.

   This is the brain in the mission, and it is the biggest gap with the leaders.
4. **The assistant is weak.**
   - It ignored "make a task" three times and answered the wrong question.
   - It was missing on some phones and proposed nothing on its own.
   - It drafted an internal question to a vendor.

   In the pilot it ran on the app's built-in fallback, not the Claude model. The server returned 503 to the harness, so this grade does not yet measure the real assistant.
5. **The phone is a smaller desktop, not a tool built for the job site.** The foreman's log, the PM's change order, receiving and clock-out each take two to three times the taps they should.

## The plan: five waves, each measured
Each wave ends with its own checks in the test net, so the same class of problem fails loudly next time.

| Wave | What | Done when | Status |
|---|---|---|---|
| 1. Trust | one bill per bank line, no posting without review; client documents with no internal text, one letterhead; drafts never lost (every sheet keeps a draft and warns before discarding); every button does what its label says; defaults from context (due dates from the mail, cost code from today's task, tax from the job) | zero severity-1 findings; a tap-label lint in the net built from the pilot's click check; a draft-loss test on every sheet | building (money, documents); drafts, labels and defaults next |
| 2. One place, one number | Today as each role's single owed list with one count; Messages with three tabs; one directory and Team; Tasks counted the same everywhere | the counts lint covers every label on every role's first screen, phone and desktop | building (navigation lane) |
| 3. It remembers | promises from mail, calls and meetings become tracked commitments with a due date and a chase; dated mail updates the schedule and vendor promises; a loop closed by mail clears its row; meeting minutes become tasks and go to the team | the pilot's "promised by mail" misses fall to zero; a test book of promise mails passes | next |
| 4. The assistant, for real | run on the live model through the platform's `/api/ai`; it makes the task when asked, answers the question asked or says it does not know, proposes catches on its own, and never mails outside without approval | an Ask bank of the pilot's failed questions passes; Pilot 3 runs on the live model | next; the harness needs `/api/` forwarded to the live proxy |
| 5. Phone-native top flows | the five daily jobs of each role, built for one hand: the foreman's log in five taps and clock-out with cost code; the PM's quick-price change order and estimate on the phone; receiving and ordering (procurement P1 to P3); billing's preview without spending a number; the owner's approvals and cash drill-down | each flow at or under its tap target, measured by the pilot's harness | procurement building; the rest after wave 3 |

**UI, running beside waves 1 to 3 (Alan, 10-25: "What about the UI?").** Pilot 2's visual findings are their own class:
- first screens show counters, "Made Today" journals and sub-links instead of the person's work;
- the blue button is not the next step, or there are two;
- headers overlap and chips and tiles scroll sideways at 390px;
- colour means three things;
- pages from different lanes look like different products. Tasks looks modern; Banking and Billing look older.

The fix is what worked for Tasks, the screen the experts rated best:
1. a mockup for Alan's yes;
2. a lane that builds to match;
3. an expert check.

The order, phone and desktop:
- each role's first screen, Today;
- the two or three pages each role lives in (Banking, Billing, the job page, the daily log, the change order);
- one design system (tokens and the shared row, card, sheet, tile, chip and header) so every page reads as one product.

A screen-standard lint enforces the rules:
- the first screen shows the person's work;
- one blue button, and it is the next step;
- no overlap, clipping or sideways chips at 390px;
- one meaning per colour;
- 15px or larger rows on field screens.

The five-second test is measured in every pilot.

Premium client documents and the portal ride with wave 1 (the documents lane) and finish in wave 5.

## Is the path clear?
- **Waves 1, 2 and 5: yes.** The findings are concrete, each has a screen, a role and a tap count, and each can be proven by a check. This is the work that moves a 6 to an 8.
- **Waves 3 and 4: the direction is clear; the result is less certain.** They decide whether this beats NetSuite and Procore rather than matching them, and they depend on the live model reading real mail well. They need Pilot 3 run on the live assistant to measure honestly.
- **The last point, 8 to 9:** simulated experts can't give it. It needs Chen and Jeanette using it for real from Monday, with their friction feeding the same loop.

## Honest estimate
**Rests on:** Pilot 1 to Pilot 2 moved grades about one point for about a week of lanes, and the five causes above are what is left.
| Point | Expected grades |
|---|---|
| After waves 1 and 2, Pilot 3 | about 7 to 7.5 |
| After waves 3 to 5, Pilot 4 | about 8 to 8.5 |
| 9 | needs real use on top of that, about two more short loops |

**Time and usage:**
- Each wave is about a day of build lanes.
- Each pilot measured about 7.7M tokens.
- So about a week of build and two to three pilots. That is heavy usage, roughly the size of the last week.
