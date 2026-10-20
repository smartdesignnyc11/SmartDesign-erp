# The improvement loop: audit before building (lane loop, 2026-10-20)

Scope: BACKLOG §1.19 (signals in, the brain triages, the owner approves, close the loop, measured) and §1.32 items
1, 3, 4, 5. Added mid-lane: §1.33 and the transcript reader (after the above).

## What exists today, and what each item needs

| Piece | Where | What it does | Gap for the loop |
|---|---|---|---|
| Report a Problem | `rpOpen` / `rpSend` / `rpContext` / Problem Reports (`rpbox`, Settings) in src/app.js | One button on every screen (header and rail, phone and desktop) and Ctrl+Shift+. ; captures screen, sub-tab, project, the last 12 presses (`rpTrail`), console errors (`rpErrors`), the screen's shape (no names, amounts or numbers), scrubbed free text, an optional picture. The owner and PM accept, decline, mark fixed and answer; the reporter sees the answer with a dot on the button. | Stored in **localStorage** (`sdp:reports`) plus the artifact runtime's shared db, which the hosted copy does not have: on the hosted copy a report from Angel's phone **never reaches Alan**. No record captured (only the project). Nothing groups reports into one problem, ranks them, or turns them into a change. "Fixed" is a hand mark, never checked. |
| Changes | `DB.changes`; Meetings › Changes (`mtChangesHtml`, `mtWire`), Company overview tiles; `mtChangeApply` (company./project. paths); `bnSendBuild` / `bnBuildBrief` ("Send to the Coder", posts to `/api/build-request`, which the rebuilt platform does not have); `bnIngestServer` (the nightly Brain's proposals); reports.js close-out proposals; messages' chat-records policy | The owner approves or declines drafted changes. A setting or rule applies on approval; a code change is "approved for the next build". | No rank, no people-hurt or frequency, no risk, no undo of an applied setting, no acceptance test, no export as an issue body, no link back to the signals or reporters, nothing checked a month later. The "Approved After the Meeting Read" block lists **every** keyed change (it was written for keys A–J; costbook rows already leak into it). |
| The Brain's lessons | `LEARN_EVENTS`, `lnLoop`, `DB.learn.events/props`, `DB.lessons`, `bnRun` (taught lessons by trigger and phase: `BN_TRIGGERS`, `BN_WHEN`), `bnSuggestLessons`, the Brain tabs (now inside the one assistant) | Events from the records become lesson proposals the owner approves; an approved lesson fires once per matching record. Taught lessons fire on matching jobs at a phase (kickoff, design, 10 days before design ends, before construction, before filing). | Nothing notices when an approved lesson keeps firing (the lesson did not stop it: "When something goes wrong twice, fix the system"). Lessons have no job type (design vs build), and a lesson read from a meeting goes in with "as soon as it matches", not before the moment it matters. |
| Standard Watch | `STANDARD_RULES` / `standardRegisterRule` (rows(), owner role, principle) | Today's breaches per measurable standard. | Breaches are not remembered day to day, so a standard broken every week looks the same as one broken once. |
| Agent findings | `review/` reports, the agent-month harness (`sim/`), Findings in the assistant (`paFindings`) | Findings are files and screens. | No way to bring an agent's or a workshop's findings into the app's queue. |
| Usage | `rpTrail` (presses, screens, toasts, dialogs) | Kept in memory for a report. | Exports to Excel, repeated typing, back-tracking, abandoned forms and rage taps are not counted anywhere. |
| Assistant rules and log | `STD_SEND_TYPES`, `paRule`, `paRuleSet`, `paDidAct`, `paPropAct`, Activity | Act Alone / Ask First / Hand It to Me per action type, logged. | No type for renewal and insurance chases; obligations make a renewal task (`bnObligationTasks`) but nothing goes on the calendar or chases the insurer, agency or vendor. |
| Server timers | `brain-nightly` + `brain-background` (+`/api/brain`), `assistant-run` + `assistant-background` gated by `ASSISTANT_RUNS` | The nightly Brain proposes up to five changes into the owner's inbox; the assistant briefs each office person. | Nothing groups the signals, verifies fixes or chases renewals while the app is closed. |

## The design gate

- **Noun "improvement" = a change in `DB.changes`.** It is already "the improvement loop's one list" (reports.js) and the
  Company overview counts it. A problem the brain triages is a change with `source: "loop"` and a `loop` block
  (signals, people, frequency, principle, rank, fix, risk, verification, history). **No second queue.** The Meetings ›
  Changes tab stays the one list; it gains a ranked section for the loop's rows and the measures card.
- **One new store: `DB.signals`** (the raw inputs: a problem report, a day's usage counts per person, a Standard
  Watch day, a lesson that keeps firing, an agent or workshop finding). Reason: reports must reach the owner on the
  hosted copy, so they must live in a synced collection; usage counts and watch days are per day and per person,
  and have no home today. A signal is evidence, not a to-do: nobody works a list of signals. The Problem Reports
  page stays the readable list of reports (it now reads `DB.signals` too) and each report names the change it was
  grouped into.
- **One new action type, `adminChases`** (Renewal Chases) on the one list `STD_SEND_TYPES`: insurers, licensing
  agencies and vendors asked for the renewed certificate, licence or form. Under Act Alone / Ask First / Hand It to
  Me like every other type, logged in Activity.
- **One new Today item kind: none.** The reporter's "see what changed" is a firm task in `DB.tasks` (the existing
  store Today already reads), with `source.kind = "improve"`.
- **No new menu item.** The page the owner reads is Meetings › Changes (Company group), plus Ask.
- **Server:** one shared pure core (`src/loop_core.js`, copied into the platform by `platform/build.py`), one nightly
  function pair `loop-nightly` / `loop-background` gated by `LOOP_RUNS=on` (off by default), writing into the owner's
  inbox the way the nightly Brain does; the app files it.

## What could go wrong (and the answer in the build)

- **Privacy:** a report's free text is scrubbed (names, amounts, emails, phones, long numbers) before it is stored;
  usage signals are counts per screen, never what was typed (repeated typing compares a local hash on the device
  only); no mail content ever. A field phone receives only its own signals (schema).
- **Noise:** thresholds before a group becomes a proposal (a stuck report, or two reports, or two people; usage
  counts over a floor; a standard broken on two different days; a lesson that fires twice after approval). One
  proposal per problem (stable key), never re-proposed after a decline.
- **Counts:** proposals are not added to Approvals (a count change across the net); recommended next with the counts
  lint, the same call the items lane made.
- **Money and the books:** an approved rule only flips a company setting with an audited from/to and an Undo; nothing
  here touches a record, money or a person.
- **The month later:** the check compares the signal rate in the 30 days before the fix with the 30 days after; a
  problem that did not stop reopens with its history and counts as a repeat.
