# Round one: the PM (Alan), 121 State Street and 206 Lenox

Sources: my diaries (`sim/runs/r1_pm/diary/u_alan.md`, `sim/runs/r1_live_pm/diary/u_alan.md`) and the conductor's notes (`docs/loop/round1/turns/pm_t1.md`, `pm_t2.md`, `pm_live.md`). Three local turns ran on the demo day, Thu 9/3: work1 on the phone (40 actions), work2 on the desktop (about 120 actions), and the page walk on both devices (about 100 actions). One live turn ran on the hosted site, phone to desktop to phone. Journeys are judged against `docs/JOURNEYS.md`. In turn 1 I worked from my role file's day list, so J3 and J4 were not taken up as written until turn 2.

## 1. The journeys

**J2, price the job: phone FAIL, desktop FAIL. The estimate was not sent.**
- Phone: about 9 actions and 9 minutes in, 0 of 12 lines entered (budget 60 taps / 20 min). Where it broke:
  - With the project switched to 214 Lincoln, the Estimates list still showed the Kleins' estimates, and New Estimate opened as "New Estimate - Sarah & David Klein". The client comes from a hidden `bill-client` filter on the billing strip, not from the project. It took 3 actions to set the Ashbys.
  - Title and Terms are folded behind the "Proposal · Thu, Sep 3 · valid to" row. Typing failed twice.
  - The blue button on an empty $0 draft is Review and Send.
- Desktop: 13 lines in about 66 actions and 70 minutes (budget 40 / 15). Price $92,520, cost $60,760, margin 34.3%, checked line by line against the takeoff. Where it broke:
  - Typing a name that matches the item library redraws the row. The control numbers move, and one match silently changed line 8's unit from ls to ea (I caught it).
  - The allowance is a tick on a separate "Ranges, Phases and Payers" list at the bottom, not on the line.
  - Ask could not draft lines from the pasted takeoff. It took me off the page with a blank line unsaved.
  - Review and Send looked dead twice. When it opened, the Cover Email was addressed to Wren only (Julian and the owner missing) and said "print to PDF and attach it". Its only button is Open in Mail App: no portal, no attachment, no second-person review.
  - The printed footer says "due within 15 days"; our terms are 30.
- What I checked: margin per line and in total, the allowance marked, the terms. I held it for the owner's review (cabinets out, no contingency line); the Standard asks for a second check before an estimate goes out, and the app has no place for one.
- Live turn: the round trip worked. Three lines saved on the phone were on the desktop about 10 seconds later, exact. A fourth line added on the desktop reached the phone's open estimate without a reload. Nothing was lost.
  - There is no save or sync status on the phone.
  - The desktop showed "Synced" beside "Unsaved Changes".
  - The desktop line editor has no Cost Code field. Line 4 got 05 Plumbing filled in by the app, and I never confirmed it.
- Grade 5. Two things keep it from a 9: the wrong-client risk, and a send path that does not reach the client's portal.

**J3, price a change (phone): FAIL, not reached.**
- 0 taps. The notched-joist extra (two joists, half a day, 2 LVL) sits in Field as "Answered", with a Write Change Order button. The CO was not written inside the turn, and the 48-hour clock has run since 9/3 morning.
- What I saw on the way:
  - The Change Orders list has no days, margin or signed date.
  - The CO page is the Billing page with Billing's subtitle and client filter.
  - CO-2026-001 (radiant heat) is approved, but the mats are still not ordered.
- Grade: none (not walked). Next round I start it from the joist item on the phone.

**J4, the Friday review (desktop): FAIL, partial.**
- About 5 actions on Costs and Change Orders in turn 2. The page walk then opened all five job pages (schedule, costs, COs, decisions, submittals) on both jobs. I did not draft or send a client update. What I found:
  - Windows are at 113% of budget, with 10 bought and 9 billed: a leak to chase.
  - The job is billed $131K ahead.
  - Margin at completion is 21% against 22% planned.
  - The Changes tab shows the Tomas no-show as a move with its reason, which is good.
- Numbers I would not act on:
  - The CO tile-prep line shows $650 margin on $488 cost.
  - "Billed ahead" for 121 State reads $131K on Costs and $66,470 on Billing.
- Missing: an RFI list, and a "draft the client update from this week's logs and photos" step.
- Grade 5. Costs is close; the update and RFIs are not there.

**The start of the day.** Today showed three counts for one list (badge 16, All 40, Now 19 + For You 21), and its header line was cut off. The Tomas no-show sheet was good: 3 taps to slip, rebook, confirm and chase. But it never named the job.

## 2. The questions, answered for my day

1. **Information I could act on quickly.** Partly. Field's open items, the Changes tab and Costs gave me what I needed. Overview contradicts itself: it says "At risk" while the list and the schedule header say "on target" for the same Nov 4.
2. **Right place, wrong place, missing.**
   - In the wrong place: the GWB answer (a will-call at Brooklyn Lumber, order 88412) was on the driver's Route, not on Materials or the task. The drawing question went to the designer through a direct chat, because the Answer sheet had no designer route.
   - Missing: RFIs (only "SK-3 RFI 3 sketch" exists, as a file).
3. **Too much, or not mine.**
   - The Billing page under three job entries.
   - "Buying on This Job" filling Overview's first screen.
   - Deliveries as a receiving form.
   - Route with "Approve Route" and "I'm at the Store".
   - The Design studio's hours and rates.
   - Tasks: 4 views, 4 scopes, 3 controls and 8 status tabs.
4. **Sub-pages per job, and which should be one.** The job is 18 pages. The Friday review took 5. Overview, Tasks and Schedule list the same items (census: 27 and 22 shared). Selections should fold into Decisions and Filings into Permits.
5. **Outside the app.**
   - Two phone calls to Tomas. A call is not a record, and texting Tomas is not set up.
   - The takeoff, in my head and pasted.
   - The second-person review, by mail to the owner.
   - The RFI to the designer, by chat.
6. **Numbers I would act on.**
   - Yes: Costs per line (except CO lines with no actual), Decisions' tiles, Submittals' ball in court.
   - No:
     - Overview's schedule verdict.
     - "Billed ahead" (two values).
     - Materials status: insulation is "Ordered" with no vendor or PO.
     - Margin on the phone's Costs: an unlabelled third figure that is actual on some rows and margin on others.
7. **Seeing, fixing and undoing a mistake.** I caught the ls-to-ea unit change only by reading. "What you typed here and had not saved is back" showed after "All changes saved", so I could not tell which value was saved. The taps I am afraid of:
   - "Passed" on unbooked inspections (desktop).
   - "Decide" on the client's decisions (phone).
   - "On Site" on every material row.
   - "Confirm Rev 3" of A-301 proposed from a meeting-note sentence.
   - The blue "Review All New" on 77 messages.
8. **Hand-offs.**
   - The no-show reached the schedule with its reason.
   - Two tasks I gave Chen (STA-31, STA-32) show as mine on Tasks, Overview and Since Yesterday.
   - "Make a task" on the drawing question made the task mine, due today, not Sarah's, due Friday 8:30.
   - The SMS to Tomas reads "Sent · from The assistant", while chat says texting him is not set up. I cannot tell if it went.
9. **A new hire.** Not J2 on the phone: the hidden client filter and the folded Title would beat them. They could do the Friday Costs read.
10. **Saw what I should not, or missed what I need.**
    - Saw: 121 State's daily log on Lenox's Field page, and the same two men logged on both jobs on 9/2 (about 16 h each).
    - Missed: Lenox's tenant complaint (noise before 8, unannounced water shutoff) is on no Lenox page but Mail. The Kleins' alteration agreement (COI and scope before the board) is not on Documents.
11. **Would I switch tomorrow?** No. The one thing stopping me: Change Orders and Estimates are not the job's own pages. That is how the wrong client and the missing days reach a client.
12. **The AI.**
    - Should have: drafted the 13 lines from the pasted takeoff; answered "where are Angel's GWB and the mats" with the will-call and the missing PO; warned that the Lenox demo move shortened its duration; drafted the client update from the logs and photos.
    - Should not have: offered "Confirm Rev 3" from a sentence; possibly marked an SMS sent that cannot reach Tomas.

## 3. Findings, by class

**A. The job's money pages are the firm's Billing page (one class, three entries)**
1. Estimates, Change Orders and Billing under a job open one firm-wide page with a hidden `bill-client` filter. Effects:
   - New Estimate takes its client from the filter, not the project: the wrong client on an estimate.
   - Billing's blue button on 121 State and on 206 Lenox, desktop and phone, is "Draft $17,080 - 45 Cranberry St".
   - Change Orders carries Billing's subtitle, client and project columns, and no days, margin or signed date.
   - Fix: job-scoped Estimates and Change Orders pages, the client from the project, and a CO row with days, margin, signed and "work started before signature". S1. Blocks J2 step 1 and J3 steps 1 to 3.

**B. Wrong or doubled money figures**
2. The Costs row for a CO line with no actual shows projected margin as the full price ("Additional tile prep" $650, 100%, on $488 cost; true $162). The total uses the right figure, so the row and the total disagree. S1. J4.
3. The phone's Costs rows show three unlabelled figures, and the third switches between actual cost and margin (Electrical "$46,500 · $36,000 · $10,500"). Fix: label it, or show the same column every time. S1. J4 on the phone.
4. Billed ahead for 121 State is $131,058 on Overview and Costs, and $66,470 on 7 lines on Billing. The margin tile says $102K, the table $103,313. One question, one number. S1. J4.
5. Lenox Costs is $0 on a running job: three logs at 15.5 crew hours, a scaffold delivered. Labor and rentals are not reaching job cost, and an owner's job cannot get a budget except through a client estimate. S1. J4.

**C. Records on the wrong job or the wrong person**
6. Lenox's Field page shows 121 State's 9/2 daily log. Lenox's 9/2 log books work to a 121 State task (Exterior, scaffold). S1. J4.
7. Alberto (8 h + 8 h) and Alex (7.25 h + 7.5 h) are on both jobs' logs on 9/2. Payroll and job cost double unless one is wrong. Fix: flag a person logged over a day's hours across jobs. S1.
8. Tasks handed to Chen show Owner "Alan". "Make a task" from a site question makes it mine, due today. Fix: keep the named doer, and let me set doer and due in that tap. S2. J4 (promises due).

**D. Status that is not tied to a record**
9. Materials shows insulation "Ordered" with no vendor and no PO (Deliveries has none). GWB shows "order by 9/11" while Route has it on a will-call today. The tile "Order This Week 1" sits over a section of 3 items. Fix: status from the PO and receipt, and a tile equal to its rows. S2. J4.
10. Schedule's Changes on Lenox shows a 2-day late start, caused by the missing ACP-5, as "-3 working days" because the duration was cut from 8 to 3 days. This is the CO-R2 class. Fix: warn when a move shortens a duration or gives back float, and say who absorbs it. S2. J3 (schedule effect), J4.
11. The schedule verdict reads "At risk" on Overview and "on target" on the list and the Schedule header. S2. J4.
12. Lenox Permits says "All clear" while its logs say demo waits on the ACP-5. ACP-5 lives as an unticked box on Design > Filings, which names no job. Fix: Filings into Permits, with ACP-5 as a permit. S2. J4.
13. The save status disagrees with itself: the phone shows no sync status; the desktop shows "Synced" beside "Unsaved Changes"; toasts say "Saved" or "Draft kept" while the banner says "Unsaved Changes". S2. J2.

**E. One-tap commits that a PM should not have, or should not have bare**
14. Desktop Permits: "Passed" on every inspection, even when nothing is booked. Phone Decisions: "Decide" on the client's decisions, where I want "Send to the Client" or "Chase". Every Materials row has "On Site". Drawings: "Confirm Rev 3" of A-301 from a meeting-note sentence. Mail: blue "Review All New" on 77 messages. S2.
15. J2's send path: blue Review and Send on an empty draft; the cover email goes to one of two clients; print to PDF; Open in Mail App; no portal, no second-person review. S2. J2 last step.

**F. Missing records a PM runs on**
16. No RFI record, number or log. The drawing question has no designer route from the Answer sheet, and the chat it became is untagged. S2. J4 (RFIs).
17. No client update draft from the week's logs and photos, and no "add these photos to the update or the CO". S2. J4 last step, J3 step 1.
18. The Project Board's Client tab says "We owe the client 0 / The client owes us 0" while five decisions sit with the client, a CO waits on a signature and Sarah's mail is unanswered. S2. J4.

**G. Entry and layout (phone first)**
19. Hidden phone fields: Title behind the header row; Cost Code and Vendor behind a panel that closes on every line. The desktop line editor has no Cost Code at all. The library match redraws the row and can change the unit. S2. J2.
20. The phone job Tasks page drops the switcher and the job strip, which strands me in the firm Tasks page. Field reopens on its last tab, hiding the open questions. Documents says "Drop files here" on a phone. Materials leads with Import and Export CSV on a phone. S2 for Tasks, S3 for the rest.
21. Duplicates and noise: the LPC and Lenox Coffee emails each listed twice; raw "(tvrs project)" column headers on Tasks; a stale $825,152 draft beside the converted estimate; Route stopping twice at Brooklyn Lumber; a per-job "Today" date field anyone can change. S3 (the date field S2).

## 4. The page walk, page by page

24 of the 25 pages the census lists for me, on the desktop (both jobs) and the phone. The 25th, Design reached by its link, is the same page as Design.

| Page | Verdict | Too much, or not mine | Missing |
|---|---|---|---|
| Projects list | keep | Email box; "ranked by attention" puts nothing-needs-you jobs first | what I owe each client today |
| Overview | keep | Chen's buying list on the first screen; 4+ screens; brief behind a button | open RFIs, COs waiting, subs confirmed for tomorrow, client mail owed |
| Project Settings | keep | per-job "Today"; "Your name" | street address, BIN, LPC number, consultants, subs |
| Schedule | keep | three add buttons | warning on shortened durations; who absorbs a move |
| Tasks | merge into Overview and firm Tasks | 4 views, 4 scopes, 8 tabs; raw headers | the doer on each row |
| Decisions | keep | "Decide" on client items (phone) | the person owed, sent and chased dates, options with prices |
| Submittals | keep | - | Release the Order on approval; a chase of what sits with me |
| Permits | keep, absorb Filings | "Passed" on unbooked rows; sideways scroll at 1440 | ACP-5 and filings; a proposed booking date |
| Field | keep Open Items and Daily Log; Takeoff to Estimates | CO button on a material request | RFI log; client update from logs |
| Photos | keep | filters before the first photo on the phone | select, then attach to CO or update |
| Deliveries | move to foreman, driver, coordinator | receiving form | read-only "lands this week" in Materials |
| Materials | keep for the coordinator; my view in Overview | CSV first on the phone; "On Site" per row | status from the PO |
| Costs | keep | - | right CO margin; labelled phone figures; owner's budget |
| Change Orders | keep, as the job's own page | Billing shell and filter | days, margin, signed, revision |
| Estimates | keep, as the job's own page | Billing shell; stale draft | "superseded" mark |
| Billing | move to billing, or scope to the job | other jobs' blue button | - |
| Documents | keep, without its Photos and Drawings repeats | 10 tabs; tiles disagree with Photos and Permits | the alteration agreement |
| Drawings | keep | Set Check before the sheet list | open field questions counted as conflicts |
| Mail | keep | duplicate messages; blue bulk review | tenant complaint surfaced on Overview |
| Requests (More) | merge into Field | a form for one job | all open requests with the 4-hour clock |
| Route (More) | move to driver and coordinator | Approve Route for a PM | - |
| Project Board (More) | move to designer | "All clear" and "owe 0" while items are open; ignores the switched job | - |
| Filings (More) | merge into Permits | names no job | - |
| Selections (More) | merge into Decisions | names no job | - |
| Design (More) | move to owner and designer | hours and rates | Sets to Re-Issue belongs on Drawings |

The five pages I would change first: Change Orders, Estimates and Billing (class A); Costs (class B); Field (classes C and F); Overview (one verdict, the doer, what I owe the client); Tasks and Decisions (the doer, the phone strip, no "Decide" for the client).

## 5. Retest

None this round. It is the first walk; nothing was fixed since.

## 6. Grades

Valid: I opened 18 of 18 Projects pages (my main module) on both devices, and 24 of 25 across my three modules.

- **Phone: 5/10.** The field answer sheets and sync are quick. But the estimate can start on the wrong client, its fields hide, and the job's Tasks page loses the job. On Costs, the unlabelled third figure is margin on some rows and actual on others.
- **Desktop: 6/10.** Costs, Field's open items and the schedule's Changes tab are what I would use. But the job's money pages are the firm's Billing page, two money figures are wrong or doubled, and there is no RFI log or client update draft.
- Live turn, for reference: phone 6, desktop 7. Sync held both ways; the save status and the missing desktop cost code held it down.

DONE: report written
