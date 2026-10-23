# Tasks: Replacing Asana for the Team Meetings

Alan, 2026-10-23: the team meets twice a week (Monday and Thursday, 10am) and walks the task board. Today the meeting transcript (Gemini notes in Drive) goes into Claude, which writes a CSV that is imported into Asana. From now on the team runs its tasks in SmartDesigns Projects instead, so that using the platform becomes a daily habit. The task module has to carry everything the meeting needs. The views are poor, except Board and Table, and the Table looks like a spreadsheet.

No real meeting content is in this file (CLAUDE.md, Privacy). The examples below describe the kinds of items, not the items themselves.

## 1. How the meeting actually works (read from the 10-22 meeting)

- The coordinator shares the board and walks it **project by project, in a set order, one task at a time**. Tasks carry short IDs with a project prefix (for example `PAD-23`, `OPS-12`, `F-19`), and people refer to them aloud by those IDs.
- For each task, one of a handful of things happens, live:
  - the **date moves** ("update it to today so we keep chasing it");
  - a **note** is added;
  - it is **marked done** ("to remove the clutter");
  - it is **reassigned**;
  - it gets a **"track until" date** (watch it, nothing to do yet);
  - it is **skipped**: "nothing to discuss, don't crowd my brain".
- **New tasks and new projects** are created mid-meeting. Asana could not create a project from the import, so anything unmatched fell into "General" and had to be fixed by hand.
- **Owners are often not app users:** the foreman, the outside designer, vendors and subs. Some tasks belong to two people, or to "the group".
- **Many tasks are money**, and Asana knows nothing about the money:
  - release a deposit to a fabricator;
  - get a credit from a supplier for a wrong delivery;
  - log an item at zero cost on job cost and decide later whether to bill it;
  - finish an overhead calculation before a cost-plus invoice;
  - pursue a vendor chargeback.
- **Decisions** are made in the meeting, and the notes split them into "aligned" and "needs further discussion" (for example, a client still has to confirm a finish).
- **Delay threats** are discussed late, by accident: a supplier's stock delay that pushes a delivery past the completion date and the inspections.
- **Follow-ups are scheduled from the board:** a schedule meeting, a site walk, a consultant call.
- **Mistakes the tool allowed:**
  - one click reordered the board mid-meeting;
  - a proposal sent in chat couldn't be found;
  - one job was known by two names (a street address and a neighbourhood name), which confused people.

## 2. What we build, in order

### Phase 0: finish what is open (today)
- Merge the three lanes still open from the overnight round: the fix lane (people matched by user id, chase dates, the bank and bill truth), Coming Up, and one place. Each merges on a green net with the month held.
- Fix Ask's answer to "notify me when updates come in". It answered with deliveries; it should set the person's notifications.
- Fix the hosted assistant run that was not filed as a briefing (live_assistant_test).

### Phase 1: the team can run Monday's meeting in the app (target: Monday 10-26, run alongside Asana)
1. **A real workspace for the team on the hosted copy.**
   - Alan, the coordinator and the office admin sign in. Their real projects come in; no demo data. The real clock applies, not the demo's pinned day.
   - Only tasks, projects and people are loaded for the pilot. Money records follow later, with the live-jobs load and its server-side field-privacy rule.
2. **Import the Asana board once,** from Asana's CSV export:
   - tasks, sections, assignees, due dates, notes, completed history;
   - the existing IDs (`PAD-23` keeps its name).

   Nothing is retyped. Unmatched rows go to a review list, never into "General".
3. **The task record gains what the meeting uses.** These are fields on the existing task stores (`tkItems`), not a new store:
   - a project key and number (`PAD-23`), shown and searchable everywhere, Ask included;
   - **one internal owner, always** (Alan, 10-23): a team member who makes sure it gets done. A vendor, consultant, designer or client is never the owner. They are **Waiting On**: who owes what, by when they promised it, and the evidence (mail, call, meeting). Others on the team can be collaborators. "The group" must name a lead. A task cannot be saved, imported or approved without an internal owner: an import row or a proposal with no owner waits for one to be picked;
   - **next follow-up** (the chase date) apart from the **due** date;
   - **watch until** for tracking items;
   - status: To Do, Doing, Waiting On, Done; plus **FYI** for status-only items;
   - the order within a project, locked during the meeting;
   - a comment thread with who and when (a note is never overwritten);
   - attachments;
   - links to the record it is about (vendor, PO, bill, decision, file, email);
   - **last discussed** (date, and which meeting).
4. **Meeting Mode**, the centrepiece. One screen for the screen share:
   - **The agenda is built for you:** projects in the team's order; inside each, what changed since the last meeting, what is late, what is due before the next meeting, and what waits on someone outside.
   - **One big card at a time,** with one-tap actions:
     - New Date (Today, Tomorrow, Next Meeting, Pick);
     - Note;
     - Done;
     - Reassign;
     - Waiting On;
     - Track Until;
     - Skip.
   - Add a task or a whole project inline; a new project gets its prefix on the spot.
   - The order cannot be changed by a stray click. Next and Previous are keyboard arrows on desktop and big buttons on the phone.
   - End Meeting writes the minutes: what moved, what's new, what's done, the decisions (aligned, and to discuss), and who owes what by when. It lands in the meeting's record and in each person's Today.
5. **The views, rebuilt** (Board and Table kept and improved; List rebuilt):
   - **List:** grouped by project and section; clean rows (title, ID, owner, due, follow-up, status) with tap-to-edit on each; no grid lines.
   - **Table:** a real work table, not a spreadsheet:
     - sticky header, sorting, grouping;
     - a column chooser;
     - inline editing with the right control per field (a date picker, a person picker, a status chip);
     - quiet row separators, comfortable row height;
     - totals per group.
   - **Board:** by status or by project; drag to move; cards show the ID, owner, due date and a waiting-on chip.
   - **Calendar** by due date and follow-up date.
   - **Saved views per person** (My Week, Waiting on Others, By Project), and the one task sheet from the tasks lane behind every row.

### Phase 2: the transcript updates the board, people approve (target: Thursday 10-29, Asana retired)
6. **Every meeting is captured in two layers, and the transcript reconciles.** (Alan, 10-23: "what's the best way to do it so the platform captures everything in the meeting?")
   - **Live, in Meeting Mode.** Every change is recorded the moment it is made, with the meeting, the time and who made it. Meeting Mode also logs which task was on screen and when (for example, PAD-23 from 10:14:02 to 10:15:40). This is the key: each line of the transcript has a time, so the reader knows which task each sentence was about, instead of guessing from the words.
   - **After the meeting, automatically.** Gemini saves the notes doc to the organiser's Drive, in the recurring meeting's folder, a few minutes after the call ends. The server watches that folder through the organiser's Google connection (the same watcher as mail and calendar), reads the **whole transcript**, not only Gemini's "next steps" (which missed items on 10-22), and extracts:
     - new tasks, with the internal owner, any Waiting On, the date said, and the project;
     - date changes, completions, notes and reassignments;
     - commitments made by outsiders ("will bring it Thursday"), which become Waiting On with the promised date;
     - decisions, aligned and to discuss;
     - money items, linked to the bill, credit or job cost line they touch;
     - new projects;
     - follow-up meetings to schedule.
   - **Reconciled, never doubled.** Anything already done live in Meeting Mode is matched and left alone. Only what the meeting said and nobody entered becomes a proposal.
   - **One review, then applied.** About 15 minutes after the call, the meeting's owner (the coordinator) gets a Meeting Review on Today, grouped by project. Each item shows the quoted sentence with its time link, and has Accept, Edit and Reject; Accept All is available. Nothing changes the board until a person accepts (AI assists, people commit). Accepted items go to each owner's Today, and the minutes are final.
   - **Fallbacks.** If the meeting was not recorded, Meeting Mode alone is the record. A transcript can also be pasted or uploaded, or recorded on the phone in the app.
   - **Privacy.** The server reads only that meeting's folder. The transcript is stored on the meeting's record in the hosted workspace, visible to the attendees, and never in the repo.

   **The old step 6, kept: meeting notes become proposed updates.**
   - The Gemini notes doc lands in Drive. The app reads it through the Google connection each person already has, from the meeting's own folder only.
   - Each next step is matched to an existing task (by ID, project and words). The app proposes:
     - new tasks;
     - date changes;
     - completions;
     - notes;
     - reassignments;
     - decisions;
     - new projects.
   - The coordinator or Alan approves the batch on one screen, item by item or all at once. It is applied with an audit trail, and anything unmatched waits on that screen.

   This extends the meeting reader (`src/meetread.js`), not a new pipeline. It replaces transcript to Claude to CSV to Asana.
7. **Tasks that are money stay tied to the money:**
   - "release a deposit" links to the bill and payment;
   - "get a credit" links to the vendor credit tracker;
   - "log at zero cost, decide on billing later" links to the job cost line and the unbilled-cost check.

   A task closes itself, as a proposal, when its record is done.
8. **Notifications, per person, switchable:**
   - assigned to you, mentioned, a comment, a date moved, a follow-up due;
   - a 7am digest by email and push.

   Ask can set these ("notify me when …").
9. **On the phone, one-handed:** add a task by voice ("Angel, measure the windows at the new job, tomorrow"), with the project, person and date filled in from the words.

### Phase 3: better than anyone (after the two meetings run clean)
- Delay threats discussed in the meeting become Coming Up rows with days left: a supplier stock delay against the completion date and the inspections.
- The assistant drafts the chase for each Waiting On item before the meeting, for approval.
- Recurring tasks: books by the 10th, COIs 30 days ahead, the weekly site walk.
- Dependencies and a timeline for tasks that hold schedule lines.
- Workload by person before tasks are assigned.

## 3. The bar: who we beat and how

| Leader | What it does well | How we beat it for this firm |
|---|---|---|
| Asana | Clean list and board, sections, multi-assignee | Meeting Mode, the transcript proposals, and tasks tied to jobs, money and the schedule |
| Linear | Speed, IDs, keyboard, a clean table | The same speed on the phone, outdoors; IDs per project |
| ClickUp, Monday | Many views, custom fields | Fewer views that each work; the fields this firm needs, not a field builder |
| Procore, Buildertrend | Construction to-dos and punch lists tied to the job | Tied to the money as well (bills, credits, job cost), with an assistant that chases |

## 4. How we prove it
- **A new suite, `tasks_meeting_test`:**
  - import a sample Asana CSV (invented data) with nothing lost;
  - run a meeting through Meeting Mode as the coordinator on desktop, with every action, and as a second person on the phone at the same time (sync during the meeting);
  - the minutes are right;
  - a sample Gemini-format notes doc (invented) produces the right proposals, and approving them updates the board.
- The table and list pass the screen-standard lint and the phone rules: 390px, no sideways scroll, 44px targets.
- **The real proof:** the coordinator runs Monday's meeting from the app with Asana open beside it. If nothing was missing, Thursday's meeting runs from the app alone.

## 5. What we need from Alan
1. **The Asana export:** in Asana, each project's menu, Export, CSV. Send the files; they are imported into the hosted workspace only, never into the repo.
2. **Who is in the pilot:** Alan, the coordinator and the office admin first. The foreman and crew join when the field-privacy rule is live on the server.
3. **Yes to the dates:** Monday in parallel with Asana, Thursday on the app alone.

## 6. Usage
- Phase 0: about 3–5% of a week.
- Phase 1: about 15–20%.
- Phase 2: about 8–12%.
- Phase 3: later, on its own yes.

The week reset on 10-23.
