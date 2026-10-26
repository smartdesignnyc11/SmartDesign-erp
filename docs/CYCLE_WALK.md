# The cycle walk (tests/cycle_walk.py)

Alan, 2026-10-26: "All these checks pass and then as soon as we do actual work, we fail almost immediately."

The rest of the net drives the app by calling its functions on the seeded data and asserting counts and labels. The cycle
walk does the ten core journeys of `docs/JOURNEYS.md` the way a person does them, and fails where a person would be stuck.
Its last lines are the number progress is measured by (PROCESS.md rule 10): `JOURNEYS desktop N of 10 · phone M of 10`.

## What it does
- **Screens only.** It drives the app through the agent harness's own verbs (`sim/server.py` `/act`): a menu entry by its
  visible label, a tap by label, typing into a labelled field, picking a visible option, `do` batches, a file or a photo, and
  the person's own mailbox (`mail send`). It never runs page JavaScript, calls an app function or jumps a view. A lint at the
  top of the file fails the suite if such a call appears in it, and the world controls it may use are an allowlist
  (`ADMIN_OK`: never `script`, `check` or `debug_eval`).
- **New work, not the seed.** A new client and job from the book (`sim/cycle_book.json`: the Ashbys, 214 Lincoln Place, the
  12-line takeoff). The world (`sim/world.py`, `sim/script_p3.js`) plays the outside: the inquiry mail, the client's answers
  and signature (it arrives only when the estimate really reached the Ashbys), the vendors' quotes and bills, the foreman's
  field day and his field issue (the rotted joists, with a photo), the trucks, the bank feed, the tile house's credit memo.
  In this walk the coordinator receives the trucks herself and the controller sits (`cycle on --play
  u_controller,u_angel:receive --feed`), so nothing a journey owns is scripted for it.
- **The journeys** (`JOURNEYS` in the file; the ten are JOURNEYS.md's, walked by its owner on its devices):

  | Id | Who | What | Graded on (sim/cycle.py) |
  |---|---|---|---|
  | J1 | owner | the inquiry mail > a lead > the walk-through noted > won > one client > the project, the notes on it | C01 C02 C03 C09 |
  | J2 | PM | the 12-line estimate from the takeoff on the job, the margin read, sent to the client's mail and portal | C05 C06 C37 |
  | J3 | PM | the foreman's joists > a change order with cost, margin and days > sent > Wren's approval recorded | C43 C44 |
  | J4 | PM | Friday: schedule, costs, change orders, decisions, submittals; the client update naming the lines over budget | C45 |
  | J5 | coordinator (+ foreman) | one RFQ from three estimate lines to three yards, the foreman's check, the quotes (one in prose), levelled, awarded | C10 C11 C13 |
  | J6 | coordinator | the award's PO issued and sent, the tile moved and price-checked, two buys on one plumbing line, the stock looked at | C12 C14 |
  | J7 | coordinator (+ owner) | two trucks received with the short and the damage, the bills against their orders, held, claimed, the credit memo | C16 C15 C17 C18 C19 |
  | J8 | billing (+ owner) | the signature and contract (the owner), the 25% deposit invoice, sent; the next morning the transfer matched to its bank line | C07 C08 C30 C31 |
  | J9 | billing | the progress invoice from the SOV with retainage, the change order and the pendants on it, sent, the chase set | C32 C35 C34 C36 |
  | J10 | controller (+ owner on the phone) | the week's lines matched or coded, the payroll built and approved, cash, AR and job cost read and graded | C25 C23 C24 + the numbers |
  | X1 | owner | an extra, not one of the ten: a proposal started at won, tied to its job | the probe |

  The chain runs in the book's days: J1, X1, J2 and J8 on Thursday 9/3 (J8 ends Friday morning at the bank), J5, J6 and J4
  on Friday, J3, J7, J9 and J10 on Tuesday 9/8. A journey that spans time moves the world inside it (`p.world_step`).
- **Phone and desktop.** The desktop chain runs first and keeps a checkpoint of the company before each journey. Each phone
  journey starts from its checkpoint in a world of its own (`server.py --resume`), so a phone failure upstream never hides
  one downstream.
- **Pass or fail.** A journey passes on a device only with no stop, no failed expectation on the way (what a person checks
  with their eyes), every record check right and JOURNEYS.md's tap budget kept (every tap, type, pick, go, back, key, file
  and photo, each step of a `do`, every person in the journey; the walk's own re-reads of the screen are not counted).
  Where JOURNEYS.md names a budget for one device, the other is held to the same.
- **Minutes are reported, not gating.** The minutes beside each budget are the harness's model (sim/server.py's MINUTES:
  about a minute per typed field), not a person's time, so the report prints them as "modelled" and no journey fails on
  them. They gate only once the model is calibrated against real recorded sessions: Alan's feedback-session recordings give
  real times per step to set it from. The report names where each journey stops, whose taps they were, and what the walk did by hand (a person's way
  round the app, such as a mail sent from their own mailbox): those ways round keep the chain going, and the expectation
  that failed before them still fails the journey.
- **Faults of the walk are not findings.** An exception in the walk is reported as `THE WALK ITSELF FAILED` and listed under
  `WALK ERRORS`; a wait judged in seconds is noted, not failed, when the machine is loaded (load above 0.75 per CPU).
- **Dangerous buttons, as a class.** For every bill, estimate, invoice, PO and obligation in a held, paid, posted or draft
  state, on the owner's, PM's, coordinator's and billing's screens, phone and desktop: the blue button and the first button
  must be a safe next step for that state (`UNSAFE`); no draft-like button may open a sheet that records the thing as done
  or arrives with today's date in its Filed/Paid/Sent On; no "recommended / approved by <person>" without that person's own
  entry in the audit trail. It runs on every role's Today in the morning and at the end over every list above.

## Run it
```
python3 build.py
tests/slot.sh python3 tests/cycle_walk.py                       # everything, one slot (about 30 minutes on an idle machine)
tests/slot.sh python3 tests/cycle_walk.py --only J7             # one journey (the chain before it runs on the desktop)
tests/slot.sh python3 tests/cycle_walk.py --devices desktop --no-danger --keep
tests/slot.sh python3 tests/cycle_walk.py --from cw_<stamp>_desktop:J7 --only J7   # from a kept checkpoint, no chain before it
tests/slot.sh python3 tests/cycle_walk.py --checkpoints cw_<stamp>_desktop          # the phone from a kept desktop run
python3 tests/cycle_walk.py --selftest                          # the walk's own units, no browser (seconds)
python3 tests/cycle_walk.py --rereport                          # the pass rule applied again to the last report (no browser)
python3 tests/cycle_walk.py --attach <run> --only J3 --devices desktop   # a world you started (development)
python3 tests/cycle_walk.py --attach <run> --danger-only                  # only the dangerous-button walk, on that world
```
The report is `review/cycle_walk/report.md` (and `report.json`): the journeys with taps, budgets, modelled minutes and where each
stops, every failure, what was done by hand, and each journey's trail. It exits 1 on any failure. `--keep` leaves the worlds
and their checkpoints in `sim/runs/` (`sim/runs/<run>.ck/<J>`) to look at or to start from. Never run it while other heavy
runs share the machine if you can avoid it: check `uptime`.

## Adding or changing a journey
JOURNEYS.md is Alan's; a journey changes there first, with its date. Then, in the same commit:
1. Write `def jN_what(p):` with the person's verbs only: `p.go(menu label)`, `p.tap(label, after=, exact=)`,
   `p.tap_row(text)`, `p.type(label, text)`, `p.pick(label, option)`, `p.do([...])`, `p.upload(label, path)`,
   `p.mail('send', to, subject, body)`, `p.expect(cond, what a person checks with their eyes, what they saw)`,
   `switch(p, uid, device)` for a hand-off, `p.world_step(slot)` when time passes. Raise `Stuck` (or let a verb raise it)
   where a person could not go on; `p.note(...)` what a person did by hand.
2. Add a row to `JOURNEYS`: id, owner, title, the function, the world's slots before it (`'next'` moves to the next working
   day), and the steps it must leave right (a `sim/cycle.py` step id, or a function of the world and the person).
3. Set its `BUDGET` from JOURNEYS.md (`--selftest` fails until the two agree).
4. Run it with `--only` and read the trail in the report. A journey that cannot be done through the screens is the finding;
   never work around it with a call into the app.
