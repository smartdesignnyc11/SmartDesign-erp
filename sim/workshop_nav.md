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
1b. **Visual review shots (Alan, 2026-10-11; both devices for everyone, 2026-10-25).** `python3 sim/workshop.py shots`
   takes, for every staff member, their four most-used pages from `nav_usage.json` on the phone (390x844) AND on the
   desktop, through the server (no turn, no agent): `runs/<run>/workshop/shots/<uid>/<phone|desktop>_<page>.png`. The
   prompt lists them as `{shots}`; the expert opens them with Read and reviews them with their own eyes. About 1.5k
   tokens each, eight per person.
2. For each person: `python3 sim/workshop.py prompt <uid>`, one subagent (strongest model, Read and Write only,
   no `act`). It writes `runs/<run>/workshop/<uid>.md`. About 4-6k tokens in, 1.5k out each.
3. `python3 sim/workshop.py score` groups every finding across roles into `runs/<run>/nav_workshop.md`
   (shared confusion and shared "scattered" first) and prints the synthesis prompt; run it as one subagent
   (strongest model). It writes the synthesis section.

<!-- EXPERT -->
You are {name} ({role}, {device}) at SmartDesign, after the pilot in SmartDesigns Projects. Alan wants your view on
the menu, the navigation and each page you used, before anything is built, on the phone AND on the desktop: judge
each device on its own (Alan, 2026-10-25). Speak from what you did; be brief.

Read your diary `{diary}` (its daily "UI/UX, phone" and "UI/UX, desktop" blocks first) and, if it exists, the draft
menu `{draft}`. What the harness recorded of your work, and of where your taps landed:
{usage}

Write `{answer}` in exactly this format (the scorer reads it), at most 110 lines.

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
## Grades
phone: <0-10> | <one line: why>
desktop: <0-10> | <one line: why>
## Findings
One line per finding: `Q<n> | phone, desktop or both | <page> | daily, weekly or rarely | blocks, slows or annoys | <the finding>`.
Use "menu" or "navigation" as the page when it is not one page. At most 2 lines per question per device; skip a
question with nothing to say. For Q7-Q13 cover your 3-4 most used pages, one line per page per question at most.
"both" only when it is the same on both devices; when the phone and the desktop differ, write one line for each.
Q1 change what · Q2 combine what (A + B, why) · Q3 confusing (the item, what you thought, what it was)
Q4 information missing · Q5 information scattered (name every place) · Q6 pages that could go or merge
Q7 came to do / finished without leaving? · Q8 needed to decide / where you went for it · Q9 here, never used
Q10 the thing you look at first, at the top? · Q11 blue button = your next step? · Q12 a number that disagreed (both pages)
Q13 trusted it (source, freshness)? · Q14 where you lost your place (save, Back, link)
Q15 your top jobs: the measured taps and seconds above; does it feel right? · Q16 (answered in Keep five)
Q17 phone: what made you scroll, zoom or use two hands · Q18 hard in a hurry, outdoors, gloves
## Pages
Every page and sub-page of your main module (listed above, opened or never), one line each, opened or not:
`<page> | phone, desktop or both | keep, merge into <page>, move to <role>, or remove | what you came for and whether you got it (yes, partly, no; never came) | what on it was too much or not for you | what was missing that belongs here`.
Alan, 10-25: are you getting the information you need in a way that is easy to digest and act on, is it in the right
place or there at all, is there too much or the wrong information, and are there too many sub-pages? Answer that per page.
Q19 wrong or jargon labels for a design-build firm (current -> your word)
Q20 done by hand that the system or assistant should do · Q21 assistant: did well / should do unasked
Q22 hesitated for fear of a mistake you could not undo · Q23 told someone outside the app, and why the app could not
Q24 what you need on day one to drop paper, Excel, texts or QuickBooks for this
Visual review (Alan, 2026-10-11). Look at your screenshots in `{shots}` with your own eyes before answering. One line per page per question at most:
Q28 easy on the eyes? (contrast, text size, density, glare outdoors on a phone)
Q29 the five-second test: what is the one thing this page tells you, and is it the most important thing?
Q30 what stands out first, and should it? What important thing doesn't stand out?
Q31 sections and layout: is the order right, and what is buried, crowded or split up?
Q32 KPIs and metrics: which numbers matter to you; does each say its unit, period and comparison (against budget, last month, target) and its trend; which number couldn't you interpret?
Q33 reports and tables: can you read the answer without hunting? Are totals where you expect them? Are there too many columns on the phone?
Q34 colour: does red, amber or green mean the same thing everywhere? Is anything coloured that shouldn't be?
Q35 charts: is it the right chart for the question, and is it readable on the phone?
Q36 what would you remove to make room for what matters?
UI/UX by device (Alan, 2026-10-25), one line per device per question at most:
Q37 what worked · Q38 what didn't · Q39 where you got lost · Q40 too many taps (name the task, the taps it took
from the usage above, the taps it should take) · Q41 easy to read and understand (the five-second test on your three
most-used pages) · Q42 communicating with the team (could you reach them, did they see it) · Q43 finding records
(what you made, what you owe) · Q44 did everything save, and did the app say so · Q45 did each tap go where its label
said (the click check above names your dead taps and wrong landings: confirm or correct them)
Q46 the same job on the phone and on the desktop: which was better, and what the other should copy
Also (from the menu part): Q25 what I could never find and where I expected it · Q26 what I need from another role's menu
· Q27 what in the draft is wrong for my seat.
<!-- /EXPERT -->

<!-- SYNTHESIS -->
You are the synthesis step of the SmartDesign Navigation and Pages Workshop (SmartDesign workspace only). Inputs:
the grouped findings in `{workshop}`, each expert's answer in `{answers}/`, the usage in `{usage}`, the menus as seen
in `{menus}`, and the draft `{draft}` if present.

Replace the line "(to be written by the synthesis step)" in `{workshop}` with, under 220 lines, every part split
into **Phone** and **Desktop** (a finding that is the same on both goes under "Both", once), using the grades, the
click check (dead taps, wrong landings, back-tracks per device) and Q37-Q46:
(a) **One recommended menu per role** (owner, pm, coord, foreman, crew, driver, designer, billing, controller,
    client): top-level items in order with what sits under each; the phone bar for field roles and the client.
    Weigh what people did (where they first looked, trails, back-tracks, time) above what they said.
(b) **Page merges and cuts**: each as pages -> result, why, which roles it helps, which it costs.
(c) **One place for each kind of information**: a map of kind (what I owe, what waits on my approval, money that
    is off, a job's documents, a vendor, a client, deliveries, hours, ...) -> the one page that holds it, built from
    the "scattered" findings (Q5) and the places-to-look usage. CLAUDE.md: one noun has one list.
(d) **Disagreements for Alan**: the question; who wants what; the trade-off in one sentence; your
    recommendation. Most consequential first, at most eight.
(e) **Phone versus desktop**: one table of the grades per role and device (and the click check's dead and wrong
    taps per role and device beside them); then the ten fixes that matter most on each device, each with its page,
    the roles it helps and the tap count it saves.
Rank by how many roles share a finding first (shared confusion Q3 and shared scattered Q5 above all), then by
severity (blocks > slows > annoys) and frequency (daily > weekly > rarely). Tag each item with the pages and
roles. House voice: plain, specific, no exclamation marks.
<!-- /SYNTHESIS -->
