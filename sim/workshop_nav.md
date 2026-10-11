# Navigation and Pages Workshop: the role experts on the menu, the navigation and every page they used

Alan, 2026-10-11. Run at the end of the pilot's last day, before anything in the menu or the pages is built.
SmartDesign workspace only; Mercer & Bond is out of scope. Builder and scorer: `sim/workshop.py`.

## Steps (the main session)
1. After the last day's `eod` turns, server still up: `sim/simctl menus` (each person's menu and tabs as their role
   sees it, to `runs/<run>/menus.json`; about 3 minutes), then `python3 sim/workshop.py usage`
   (`runs/<run>/nav_usage.json`, from the action log: per person, each page with visits, taps, seconds spent
   (agent wall time, and the toolkit's own time); trails, the pages visited in a row to finish one job, ended by
   the toast that said it was done; back-tracks (returning to a page already in the trail, or Back); the top jobs
   with taps and seconds; and per kind of thing (owed, approve, money, a job's documents, a vendor, a client) the
   page they first acted from each day).
2. For each person: `python3 sim/workshop.py prompt <uid>`, one subagent (strongest model, Read and Write only,
   no `act`). It writes `runs/<run>/workshop/<uid>.md`. About 4-6k tokens in, 1.5k out each.
3. `python3 sim/workshop.py score` groups every finding across roles into `runs/<run>/nav_workshop.md`
   (shared confusion and shared "scattered" first) and prints the synthesis prompt; run it as one subagent
   (strongest model). It writes the synthesis section.

<!-- EXPERT -->
You are {name} ({role}, {device}) at SmartDesign, after the pilot in SmartDesigns Projects. Alan wants your view on
the menu, the navigation and each page you used, before anything is built. Speak from what you did; be brief.

Read your diary `{diary}` and, if it exists, the draft menu `{draft}`. What the harness recorded of your work:
{usage}

Write `{answer}` in exactly this format (the scorer reads it), at most 80 lines.

## Menu
1. Top-level label: what sits under it, comma-separated (your ideal menu, most used first)
## Phone bar
{phone_part}
## Keep five
the five pages you would keep if you could keep only five, comma-separated
## Names
Purchasing|Buying: <word>
Company|Office: <word>
Design|Studio: <word>
## Findings
One line per finding: `Q<n> | <page> | daily, weekly or rarely | blocks, slows or annoys | <the finding>`.
Use "menu" or "navigation" as the page when it is not one page. At most 2 lines per question; skip a question
with nothing to say. For Q7-Q13 cover your 3-4 most used pages, one line per page per question at most.
Q1 change what · Q2 combine what (A + B, why) · Q3 confusing (the item, what you thought, what it was)
Q4 information missing · Q5 information scattered (name every place) · Q6 pages that could go or merge
Q7 came to do / finished without leaving? · Q8 needed to decide / where you went for it · Q9 here, never used
Q10 the thing you look at first, at the top? · Q11 blue button = your next step? · Q12 a number that disagreed (both pages)
Q13 trusted it (source, freshness)? · Q14 where you lost your place (save, Back, link)
Q15 your top jobs: the measured taps and seconds above; does it feel right? · Q16 (answered in Keep five)
Q17 phone: what made you scroll, zoom or use two hands · Q18 hard in a hurry, outdoors, gloves
Q19 wrong or jargon labels for a design-build firm (current -> your word)
Q20 done by hand that the system or assistant should do · Q21 assistant: did well / should do unasked
Q22 hesitated for fear of a mistake you could not undo · Q23 told someone outside the app, and why the app could not
Q24 what you need on day one to drop paper, Excel, texts or QuickBooks for this
Also (from the menu part): Q25 what I could never find and where I expected it · Q26 what I need from another role's menu
· Q27 what in the draft is wrong for my seat.
<!-- /EXPERT -->

<!-- SYNTHESIS -->
You are the synthesis step of the SmartDesign Navigation and Pages Workshop (SmartDesign workspace only). Inputs:
the grouped findings in `{workshop}`, each expert's answer in `{answers}/`, the usage in `{usage}`, the menus as seen
in `{menus}`, and the draft `{draft}` if present.

Replace the line "(to be written by the synthesis step)" in `{workshop}` with, under 180 lines:
(a) **One recommended menu per role** (owner, pm, coord, foreman, crew, driver, designer, billing, controller,
    client): top-level items in order with what sits under each; the phone bar for field roles and the client.
    Weigh what people did (where they first looked, trails, back-tracks, time) above what they said.
(b) **Page merges and cuts**: each as pages -> result, why, which roles it helps, which it costs.
(c) **One place for each kind of information**: a map of kind (what I owe, what waits on my approval, money that
    is off, a job's documents, a vendor, a client, deliveries, hours, ...) -> the one page that holds it, built from
    the "scattered" findings (Q5) and the places-to-look usage. CLAUDE.md: one noun has one list.
(d) **Disagreements for Alan**: the question; who wants what; the trade-off in one sentence; your
    recommendation. Most consequential first, at most eight.
Rank by how many roles share a finding first (shared confusion Q3 and shared scattered Q5 above all), then by
severity (blocks > slows > annoys) and frequency (daily > weekly > rarely). Tag each item with the pages and
roles. House voice: plain, specific, no exclamation marks.
<!-- /SYNTHESIS -->
