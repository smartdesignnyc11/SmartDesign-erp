# Today at a glance, and the project row on a phone (2026-09-13)

Module `erp/glance.js` · CSS `.glance`, `.gl`, `.subnav.m-projrow` in `ia.css` · checks in `erp/mobile_test.py` (59). Artifact v79. From Alan's two screenshots: the project row was cramped, and the four tiles at the top of Today were hard to read, arguably the wrong facts, and dead to the touch.

## The tiles
Four questions a person has when they open a project, one tile each, every tile a button to the screen that holds the answer, coloured by state (green / amber / red bar and value), with a chevron so it reads as a place to go:

- **Finish** → Schedule. *On target · 3 days late · 5 days early*; the forecast finish, the target, the critical-path count.
- **Money** → Costs. *22% margin*; planned margin, billed of contract, and whether we are billed ahead or have earned work not yet billed.
- **Needs you** → Decisions (or Field when the site is what is waiting). *4 now*; decisions open, inspections, questions from the site.
- **Materials** → Materials. *3 at risk · 22 to land · All on site*; how many not yet on site and the next needed date.

Across all projects: **Projects** (*4 of 4 on time*, the worst offender named) → All Projects · **Money** (portfolio margin on contracted) → Reports · **Needs you** (the Approvals count — what actually waits on your yes or no) → Approvals · **Materials** (at risk across projects).

Gone: the *project health 48 / 100* — a number nobody could act on; the finish and needs-you tiles say what it was trying to say.

## The project row
On a phone the row is two lines: a full-width picker that contains **All projects** as its first entry, then the tabs. The *All Projects* tab leaves the strip; picking All projects on Today shows the portfolio, on any other project tab it opens All Projects. Today opens across all projects until a project is chosen, and the tab strip starts at the active tab. Desktop is unchanged apart from the tiles.

## The check
Found and fixed while building: the ledger already had a `glWire` (renamed mine — a name collision silently broke the Ledger's tabs until the regression caught it); the tab strip was scrolling to hide the first tab (a selector that found the hidden cross-project strip first). `mobile_test.py` 59/59; full regression 89 suites clean; hosted app 28/28.
