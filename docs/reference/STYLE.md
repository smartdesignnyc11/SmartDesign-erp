# Formatting & wording standard (2026-09-13)

Module `erp/titlecase.js` (runs after every render and on every sheet/panel that opens) · label changes in `app.js` and `glance.js`. Artifact v80.

**Title Case everywhere a thing is named.** Headings, page titles, nav groups, tabs and sub-tabs, segmented filters, chips, tile labels, table headers, form labels, card titles, short buttons (up to four words) and the bottom tab bars: *All Projects*, *Look-Ahead*, *Billable Now*, *Sent, Not Paid*, *Recorded, Not Yet in the Bank*, *10 Working Days*, *Add Task*. Small words stay lowercase inside a title (a, an, the, of, and, or, to, in, on, at, for, by, as, per, vs, with, from, nor, but); hyphenated words capitalise both halves; acronyms and mixed-case words are left alone (P&L, WIP, DOB, COI). Sentences stay sentences: leads, hints, KPI descriptions, timeline entries, log lines, notes, values inside tiles, long call-to-action buttons and anything that ends in a question mark.

**Accounting, not Money.** The nav group, the home card, the dashboard widget group, the PO card, every "Money › …" path and the Today tile now read *Accounting*. The one "Money" that stays is on a sales deal — *Money and Paper* is the buyer's budget and paper process, a different thing.

Implementation note: the standard is applied on the live DOM, so every module keeps its own strings and anything new is cased the same way without anyone remembering to. Seventeen tests that asserted exact sentence-case labels were made case-insensitive; the full regression (89 suites) is clean.
