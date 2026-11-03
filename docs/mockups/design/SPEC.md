# Design: the menu's pages (mock-up and spec, 2026-11-03)

Read with `docs/mockups/QUESTIONS.md` and the approved `docs/mockups/job-structure/`. Figures are the demo company's on 9/3, read from the
build of master 8eeb990 as Sarah Davis (designer), Alan (PM) and the Kleins (client); `[PLACEHOLDER]` marks what the build did not have.
The registers of 45 Cranberry and 140 Prospect were not read (the build switches jobs through its picker, not the record). Nothing in src/ changed.

| File | Screen |
|---|---|
| Selections, DeskSelections | Selections, phone and desktop (job and room filters, client view) |
| Drawings, DeskDrawings | Drawings, phone (By Sheet or By Room) and desktop |
| InDesign | Where the Design overview goes: Projects › All Projects, the In Design filter (phone) |

## 1. Today (census build bd3180c, re-read on 8eeb990)
- **Menu pages, 5:** Design (`ovstudio`, the studio overview), Project Board (`sboard`), Filings (`sfile`), Selections (`sel`), Drawings (`plans`, the designer's bar; also Projects › Drawings).
- **Also:** `sdraw` (allowed, never reached) and the link "2 projects need attention", which reopens Design.
- **Tab screens, 8:** Project Board's Client, Meetings and FF&E (after Rooms), and Selections' room tabs (Guest bath, Kitchen, Parlor, Primary bath, Whole house).
- **Who reaches it:** the designer, 5 pages; the PM through More (4); the coordinator Selections through More; the owner 6.
- **Empty or doubled:** Filings lists nothing on 121 State; Project Board says "All clear" and "No design proposal on this job yet". The designer's own Today already carries To Re-Issue 6, Hours Not Logged and the field's question.

## 2. Proposed: two pages, as the 11-03 phone menu shows
**Selections** and **Drawings**. Both open on **Needs You** across every job, then **With Someone Else** (who, no number), then the full
list one tap down. Job and room are filters, not tabs. The studio overview becomes a filter of the Projects list (InDesign); filings,
meetings and the client profile go to the job and the client, where 11-03 put them.

**Selections** (Needs You 6)
- What: every product we specified, on every job: maker, SKU, finish, size, cost, lead and where it stands.
- Label: Selections, the designer's and the client's word.
- Holds: the selection record, one record from clip to install. It is a need on the Buy Board as it is. The client's approval is a Decision on the job (11-03), and both link to the same record.
- Who and why: the designer ("what must I fix before it is bought or installed?"); the PM and coordinator reach it from a decision or a Buy Board row.
- First screen: six items to fix. Five lack the spec sheet the field needs before the wall closes; the picture light moved from $385 to $412; the shower drain was bought on no approved estimate line. Then the faucet (Alberto's resubmittal) and the knob set (the Kleins).
- Numbers: 6, the rows. The tiles go: Red Flags and To Check become reasons on rows; Awaiting Approval 2 is counted once, in the job's Decisions; Still to Buy is the Buy Board.
- The +: Clip From a Web Page, From a Spec Sheet or Photo, Choose From Past Jobs, already tied to the job in the filter.
- Phone: card with a line-drawn image, labelled Quantity, Cost Each, On Site, Status, the reasons, one action; "See This Job as the Client Does".

**Drawings** (Needs You 8)
- What: every job's current sheets, and what the field and the agencies are waiting on.
- Label: Drawings (one register per job, 10-19 call 6; the job's Documents shows the same register filtered).
- Holds: sheets, revisions, sets, field acknowledgments, the Set Check and its lessons, rooms (from Project Board) and filings at the agency (a link to the job's permit record).
- Who and why: the designer ("what is the field building from, and what do they need from me?"); the foreman reads current sheets from Site.
- First screen: Angel's question on A-301 (3" or 2" drop, answer by 9/4, holds framing); 6 sheets to re-issue on 45 Cranberry (rear wall 14'-6" to 13'-6"); 140 Prospect's 11 unmeasured rooms. Then At the Agency: LPC Certificate of Appropriateness, 6 days.
- Numbers: 8 = 1 + 6 + 1 rows; today's designer Today shows To Re-Issue 6, the same rows.
- The +: New Revision, Issue a Set, Upload a Consultant Sheet, New Room, for the job in the filter.
- Phone: sheet rows with sheet, revision, title, status and date, what changed and the field's acknowledgment; By Room groups the same sheets under rooms.

**Where the studio overview goes (InDesign, Projects menu)**
- The design projects are projects: one list. Projects › All Projects gains an In Design filter with phase, hours against the proposal, survey, drawings, filings and the team on each card. Hours not logged sit at its foot.
- The owner's signal (45 Cranberry's schematic design 41.5 of 40 hours) reaches his Today, as question 4 asks.

## 3. Old page or tab, and its new home (nothing reachable today is lost)
| Today | New home |
|---|---|
| Design (`ovstudio`): the project table | Projects › All Projects › In Design |
| Its tiles: Projects to Survey, Sets to Re-Issue | Drawings › Needs You |
| Over Hours or Gated | the In Design card and the owner's Today |
| At the Agency | Drawings › At the Agency, linking the job's permit record |
| Hours Not Logged; Who Is on What | the designer's Today (already there) and the In Design foot; the team line on each card and Company › Team |
| "2 projects need attention" link | removed; Needs You on Drawings |
| Project Board › Rooms (phase, sheets, Dimensions, Survey checklist) | Drawings › By Room; Dimensions on the room; the checklist from the survey row |
| Rooms › Timer; New Room | Today's Day Sheet (time) / Drawings' + |
| Project Board › header strip (Finish, Design and Permit tracks, Waiting, Pending COs) | the job's header (job-structure) |
| Project Board › "All clear" band | gone: an empty Needs You says it |
| Project Board › Client: contacts, preference profile | Clients › the Kleins' record |
| Client tab: open decisions, we owe, the client owes | the job's Decisions |
| Client tab: explorations (studies with an hour cost) | the job's Decisions, as options with their hours |
| Project Board › Meetings | Messages › Meetings filtered to the job; transcripts on the job's Documents |
| Project Board › FF&E (+ Selection) | Selections filtered to the job; its + |
| Project Board › Precedents | Company › The Brain's lessons, shown on the room in Drawings › By Room |
| Filings (`sfile`): fixed-fee tracks, NYC sequence, Before Anything Is Filed | the job's Documents › Permits and Filings (10-19 call 7); the fee milestones draft invoices in Contract and Billing |
| Selections (`sel`): tiles, room tabs | reasons on rows; the room filter |
| Selections: Client View, Get Clips and Clip an Item, Verify All | "See It as the Client Does"; the + menu; Verify on each row (Verify All as a row action on Needs You) |
| Drawings (`plans`): Set Check, What the Sets Teach, register, Set and Status filters | Drawings, across jobs, with the job filter |
| Drawings: Field Acknowledgments; Mark in Revision, Issue a Set, New Revision | the Field column; the row and the + |
| `sdraw` | forwards to Drawings |
| The designer's Today (`sday`) | unchanged, in Your Day |

**Count:** before, 5 pages (plus `sdraw` and a duplicate link) and 8 tab screens; after, 2 pages, no tab rows, and one filter added to Projects.

## 4. Who sees what
- **Designer:** Design › Selections and Drawings, with the counts above. Phone bar: Today, Drawings, Selections, Messages.
- **PM:** no Design menu (the PM expert asked for it off his menu). He reaches drawings through the job's Documents, and selections through the job's Decisions and Purchasing tabs. The field's question reaches him only if the designer is out.
- **Client:** never sees Design pages. The portal's Decisions holds "We Need Your Choice" and "Approve Before We Order"; Selections' client view shows what they will see.
- **Owner:** the Design menu, no counts. On Today: hours over the proposal, a filing past its date, an item bought on no estimate line.
- **Coordinator:** no Design menu (today it hides under More); a Buy Board row opens its selection.
- **Foreman:** current sheets on Site and Documents, acknowledged there. His questions land on Drawings' Needs You.

## 5. Calls I made, and why
1. **The studio overview becomes the Projects list's In Design filter,** not a third Design page. Design projects are projects (one noun, one list), and its signals already sit on the designer's and owner's Today.
2. **Rooms go to Drawings › By Room.** A room's state is its sheets and its measurements, and the designer works sheet by sheet.
3. **Filings live on the job's Documents** (one permit list per job, decided 10-19); Drawings shows what is at the agency across jobs, linking it.
4. **A selection's client approval is a Decision.** Selections links to it and does not count it, so "waiting on the Kleins" is one number in one place.
5. **By Sheet or By Room** is a grouping of one list, not a second screen.

## 6. Found while reading the build (what the checks did not check)
- **One clock is broken in Selections.** Its checks are stamped 2026-11-02, and the range's claim was raised 2026-10-29, on a demo day of 9/3.
  - The faucet and the shower set share the order-by 8/13; one reads "passed 20 days ago", the other "passed 80 days ago".
  - The sink's order-by is 9/18, still ahead, yet it reads "passed 45 days ago".
  - Class fix: no stored date may be later than today(), and a lint should fail on wall-clock stamps.
- **One label, two numbers.**
  - Selections' To Check reads 4, while 6 cards say "No spec sheet attached".
  - Hours Not Logged reads 4 on the designer's Today and "5 designer-days" on Design.
  - Waiting on Decisions reads 11 on Today, against 8 open on 121 State Street (other jobs may explain it; not checked).
- **Money.** The shower drain was bought ($95) on no approved estimate line, and Analysis lists 7 such rows. Nobody is asked to bill it back or write a change order.

## 7. Self-review against QUESTIONS.md
| Page | 1 What | 2 Label | 3 One home | 4 Who | 5 Record | 6 First screen | 7 Numbers | 8 + | 9 Phone | 10 Few | Still weak |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Selections | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | Only 121 State's open items were read; 45 Cranberry shows installed items by name only |
| Drawings | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | The 45 Cranberry and 140 Prospect registers are placeholders; the phone page is long below Needs You (sheets one tap down would fix it) |
| In Design (Projects) | pass | pass | pass | pass | pass | pass | weak | pass | pass | pass | It belongs to the Projects menu, not mine to settle. Its cards show figures (hours, sheets) where nothing waits on you; labelled, but question 7 leans against them |

Revised during review: the desktop sheet table went from 8 columns to 5 (it broke beside the side panel). Phone targets were raised to 44px (the By Sheet and By Room switch, two inline links). New Room was added to Drawings' + once Rooms moved there.
Checked by rendering each screen at its width: no sideways scroll at 390, one blue at most (Answer Angel), every handler runs.
