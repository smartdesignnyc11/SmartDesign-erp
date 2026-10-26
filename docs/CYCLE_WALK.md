# The cycle walk (tests/cycle_walk.py)

Alan, 2026-10-26: "All these checks pass and then as soon as we do actual work, we fail almost immediately."

The rest of the net drives the app by calling its functions on the seeded data and asserting counts and labels. The cycle
walk does Pilot 3's required work the way a person does it, and fails where a person would be stuck.

## What it does
- **Screens only.** It drives the app through the agent harness's own verbs (`sim/server.py` `/act`): a menu entry by its
  visible label, a tap by label, typing into a labelled field, picking a visible option, `do` batches, and the person's
  own mailbox (`mail send`). It never runs page JavaScript, calls an app function or jumps a view. A lint at the top of the
  file fails the suite if such a call appears in it, and the world controls it may use are an allowlist (`ADMIN_OK`:
  never `script`, `check` or `debug_eval`).
- **New work, not the seed.** A new client and job from the book (`sim/cycle_book.json`: the Ashbys, 214 Lincoln Place, the
  12-line takeoff). The world (`sim/world.py`) plays the outside: the inquiry mail, the client's answers, the signed copy
  (it arrives only when the estimate really reached the Ashbys), the vendors' quotes.
- **The journeys** (`JOURNEYS` in the file):

  | Id | Who | What |
  |---|---|---|
  | J1 | owner | the inquiry mail > lead > won > client > project |
  | J1b | owner | another inquiry (Nadia Okoro), won by the app's own "Close and Start the Proposal": is the estimate tied to its job? |
  | J2 | PM | the radiator asked back to the client; the 12-line estimate keyed from the takeoff, tied to the job |
  | J3 | PM | the estimate sent to the Ashbys |
  | J4 | owner | the signature recorded; the contract and the SOV |
  | J5 | coordinator (+ foreman) | the three yards on file; one RFQ from three estimate lines; the foreman's quantity check; sent |
  | J6 | coordinator | the quotes recorded from the replies; the award |
  | J7 | coordinator | POs from the lines: several lines on one PO, the tile, two buys on the same plumbing line; sent |
  | J8 | billing | the deposit invoice from the contract, sent |

- **Phone and desktop.** The desktop chain runs first and keeps a checkpoint of the company before each journey. Each phone
  journey starts from its checkpoint in a world of its own (`server.py --resume`), so a phone failure upstream never hides
  one downstream.
- **Graded in the records.** After each journey the raw records (`db.json`) are graded by `sim/cycle.py`'s own step checks
  (C01-C14, C30). A failure names the journey, the device, the step, the screen, the last control and what was expected.
- **Taps and time.** Per journey and device: taps (every tap, type, pick, go, back and key; each step of a `do`), calls and
  wall time, held to `TAP_BUDGET` (twice what a professional needs; written in the file).
- **Dangerous buttons, as a class.** For every bill, estimate, invoice, PO and obligation in a held, paid, posted or draft
  state, on the owner's, PM's, coordinator's and billing's screens, phone and desktop: the blue button and the first button
  must be a safe next step for that state (`UNSAFE`); no draft-like button may open a sheet that records the thing as done
  or arrives with today's date in its Filed/Paid/Sent On; no "recommended / approved by <person>" without that person's own
  entry in the audit trail. The blue button is read with the harness's `screen --marks`.

## Run it
```
python3 build.py
tests/slot.sh python3 tests/cycle_walk.py                       # everything, one slot (about an hour)
tests/slot.sh python3 tests/cycle_walk.py --only J2             # one journey (the chain before it runs on the desktop)
tests/slot.sh python3 tests/cycle_walk.py --devices desktop --no-danger
python3 tests/cycle_walk.py --attach <run> --only J3 --devices desktop   # a world you started (development)
```
The report is `review/cycle_walk/report.md` (and `report.json`): the journeys with taps, budgets and times, every failure,
and each journey's trail. The last line is `CYCLE WALK N checks · F failed`; it exits 1 on any failure. `--keep` leaves the
worlds in `sim/runs/` to look at (`SIM_RUN=<run> sim/act <uid> screen` after `python3 sim/server.py --run <run> --resume`).

## Adding a journey
1. Write `def jN_role_what(p):` with the person's verbs only: `p.go(menu label)`, `p.tap(label, after=, exact=)`,
   `p.tap_row(text)`, `p.type(label, text)`, `p.pick(label, option)`, `p.do([...])`, `p.mail('send', to, subject, body)`,
   `p.expect(cond, what a person checks with their eyes, what they saw)`, `switch(p, uid, device)` for a hand-off. Raise
   `Stuck` (or let a verb raise it) where a person could not go on.
2. Add a row to `JOURNEYS`: id, who, title, the function, the world's slots before it (`'next'` moves to the next working
   day), and the steps it must leave right (a `sim/cycle.py` step id, or a function of the world returning (status, detail)).
3. Add its budget to `TAP_BUDGET` with the professional's count in the comment.
4. Run it with `--only` and read the trail in the report. A journey that cannot be done through the screens is the finding;
   never work around it with a call into the app.
