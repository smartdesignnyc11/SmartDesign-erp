# Studio module — features from the 140 Prospect Place meeting

Companion to `claude/design-studio-module-rd-2026-09-06.md`. Sources: the 1h47 design-kickoff transcript (read in full), the 09.05.2026 design-direction deck, and the Aug 26 proposal/agreement. The meeting extraction itself is in `claude/meeting-140-prospect-place-2026-09-05.md`.

## 1. What the meeting shows about the process

The deck is existing photos → existing plan → proposed plan → references → renderings, floor by floor, with no dimensions on the plans ("It's hard to know when you don't have dimensions"). The client decides by *seeing*: every layout question ended with "I'd be curious to see that rendered". Two decision-makers with different tastes — the daughter owns aesthetics, the mother owns money and practical questions. The designer had not been in the house; the plans are drawn on the realtor's marketing plan, which Alan said "is off everywhere… so we don't find an extra 12 inches after we've already designed the whole entire kitchen." The client's inspiration (a year of Pinterest saves) was never received before the design was done. The island question looped three times; the angled-tub idea was described verbally with no drawing; the roof-stair decision has a soft 60-day clock tied to demo; a fireplace check gates the whole kitchen layout and nobody owns it; ~15 promises were made in both directions with no dates; the acceptance form is unsigned while work proceeds; a $111,000 filing figure was read aloud and never explained. The architect dropped off before the budget conversation.

None of that is a people problem. It is what happens when a two-hour conversation is the system of record.

## 2. The measurement problem — how the module prevents it

Principle: **a dimension is a data point with a provenance, and drawings inherit the weakest provenance of the dimensions they depend on.** The designer never fills a form about this; they see one badge and one list.

1. **Every room carries a dimension set** (wall lengths, ceiling height, window and door openings, fireplace projection, arch width/height, molding profile heights, radiator/riser positions). Each value has a source: *listing plan* (unverified), *field-measured* (who, when, photo of the tape or laser reading), *trade-verified* (millshop, window vendor, stone fabricator — the second, independent measurement), or *as-built*.
2. **Drawings and renderings declare which rooms they depend on** (a tag, not a form). A drawing's badge is the lowest provenance underneath it: "Kitchen plan — drawn on listing dimensions, not field-verified." That badge prints on the deck page and on the PDF, so the client sees "conceptual — not measured" and the expectations problem disappears.
3. **Gates, not nags.** Three things are blocked until the dimensions they need are field-measured: moving a room from Schematic to Design Development, issuing any set (LPC/DOB/CD), and creating a millwork, window, stone or appliance PO line for that room. The block says exactly which dimensions are missing. Nothing else about the designer's day changes.
4. **The survey visit writes the checklist.** When a project is created from a proposal, the survey task is generated with the room list from the scope; on the phone, the surveyor walks room by room entering values and photos (voice entry: "kitchen rear wall fourteen feet six"). Values land directly on the room's dimension set with provenance *field-measured*. The 24-hour survey line on this proposal becomes the 24 hours it takes to fill that list.
5. **Second measurement before fabrication.** Any dimension that drives millwork, stone, windows or appliances requires a trade-verified value before the PO is issued. When the millshop's number comes in and differs from the field measure by more than the tolerance (default ½"), the module lists every drawing, rendering, estimate line, PO line and deck page that carries the old value and marks them stale — the designer sees the redesign *before* fabrication, not after, and the client sees a change record, not a surprise.
6. **Fit checks.** Alan did the kitchen rear-wall stack-up in his head: sink 30" + dishwasher 24" + pull-outs + trash 24" ≈ 7' against the wall length, leaving 12–18" doors. The room card does this arithmetic: fixtures and cabinetry placed on a wall sum against the verified wall length, and the remaining width for the doors, the arch and the windows shows in the margin. Same for the hall-bath shower minimum "pinch point", the 24" hanging-closet depth, the 66" study room, and the laundry sink between two counters. The check is a number on the card, not a warning dialog.
7. **Change records list their reach.** A dimension change (or any design change) creates one record: what changed, why (survey, client, LPC objection, millshop), and every artifact affected across LPC/DOB/CD sets, schedules, estimate lines, POs and decks. Each affected item shows stale until re-issued or confirmed. This is the domino stopped at the first tile.

## 3. Decisions, questions, promises — the record the meeting didn't have

- **Meeting intake.** Paste the transcript (or the recorder's notes). The assistant proposes: decisions (25 in this meeting), open questions (24), promises in both directions (~30), preferences and dislikes, FF&E selections, measurement/site notes — each tagged to a room. A person confirms, edits or drops each one; nothing is committed by the machine. Confirmed items become cards with an owner and a date.
- **Gates.** Some open questions block others; the module lets the designer mark them: fireplace works? → kitchen seating and island position; survey done? → every plan; roof-stair intent? → framing. A gate shows on the project strip with its date and on the director's view when it is the thing holding the phase.
- **Design explorations cost hours.** "Render the third kitchen option" is an exploration card with an hour estimate; the client sees it on the portal as *requested — est. 8 hrs*. Alan's warning ("something as simple as 'I'd love to see what that looks like' could be 30 hours") becomes visible instead of spoken once.
- **Promises with dates.** Every "I'll send you…" gets an owner and a due date at confirmation time, in both directions; the designer's day shows theirs, the client portal shows the client's (Pinterest board, LG drying-closet spec, acceptance form, wire). Overdue promises are the top of the design manager's list.
- **Two decision-makers.** Client contacts carry a role: *decides design*, *decides money*, *informed*. Decisions record who made them; money items route to the money contact. The portal shows each contact only what they own.

## 4. The client's experience

- **Portal per project**: the current deck (versioned — the client always knows which deck they saw), decisions by room with dates, what SmartDesign owes them and when, what they owe SmartDesign, explorations requested and their hours, the preference profile, the survey status ("your kitchen is drawn on measured dimensions" is a badge they can see), filing status in plain words, and retainer hours used.
- **Preference profile.** Likes, dislikes and hard rules captured from meetings and the inspiration intake ("no recessed cans", "no beige", "nothing hidden behind doors", "glass showers", "brass over chrome", "steel + rosy marble"). Every room card shows the profile; before a deck is issued the assistant reads the spec and rendering notes against it and flags conflicts ("kitchen rendering has recessed cans — client said no"). The deck presented in this meeting skewed to the mother's taste; the profile would have caught it.
- **Inspiration intake.** One link (Pinterest board, folder, photos texted to the designer) lands on the project board as reference cards; nothing is lost in text messages "at any hour".
- **Dimensioned plans in the deck.** The deck template pulls verified dimensions onto the proposed plans automatically; unverified rooms print the conceptual badge.

## 5. Hours, fees, filings — from the proposal

- Retainer of 120 hours against 344–464 estimated by phase, at $200 blended; replenish at 20 hours; hourly increments; itemized statements. The design estimate template already carries phases and retainer; the module adds **hours left in this phase** next to every entry so the designer sees why the entry matters, and the retainer balance on the client portal.
- The 1h47 meeting with two SmartDesign attendees is two hour entries, pre-filled from the calendar with the phase *Client meetings*, waiting for a tap.
- Five fixed-fee filings (Alt-CO $45k, Demolition $12k, Partition/framing $12k, Alt-2 $15k, LPC rear windows $27k = $111k) billed 50% at start / 25% at submission / 25% at approval, two ordinary comment rounds included. Each filing is a track with those three milestones as invoice triggers, a comment-round counter (third round = additional service at $200/hr, flagged automatically), the predecessor rules from the NYC sequence, and days in review. The $111k figure the client read aloud becomes a line on the portal with its breakdown.
- Exclusions are data: front facade, front windows/doors, roof/bulkhead, deck, structural/MEP consultants. When a meeting decision touches an excluded item (facade now, roof stair, deck cover, skylights, sump pump), the confirmation step offers *add as additional service* and creates the proposal line — the scope creep from this meeting is nine items.

## 6. What each role sees

- **Designer / architect** — My day (touched-things chips, calendar blocks, hours left per phase), the project board (rooms as cards with dimension badge, decisions, references, explorations), the preference profile, the drawing register for their sheets.
- **Design manager** — promises overdue both directions, gates holding phases, surveys outstanding, sets due, filings with days in review and comment rounds, second-measure requests outstanding before fabrication, stale artifacts after changes.
- **Design director** — who is on what for eight weeks, hours vs estimate per phase per project, retainer balances, realization, explorations requested vs approved, client decision latency, and the scope-creep-to-proposal conversion.

## 7. Build plan (unchanged: two sessions)

**Studio A** — Studio nav; My day with day sheet; project board with rooms, dimension sets and provenance badges; survey checklist (phone); fit checks; change records with stale propagation into estimate lines, POs, materials; second-measure rule on millwork/stone/window/appliance POs; filings tracks from the proposal with milestone billing; tests. Seed: 140 Prospect Place from these documents.

**Studio B** — meeting intake with human confirmation (seeded with this transcript's extraction); decisions/questions/promises/gates; preference profile and deck check; explorations with hours; client portal; FF&E cards into purchasing; director view; precedent pane.

## 8. Studio A — built 2026-09-06

Shipped in `studio.js` (spliced into app.js) + CSS: Studio nav group (My day · Project · Drawings · Filings · Studio); roles `designer` (Sarah Davis, Maya, Maja) and `design_mgr` (Design director) with sign-in entries; owner/PM see the group too.
- **Dimensions with provenance** on every room (`DB.studio.rooms[].dims[].src` = listing | field | trade | asbuilt, with by/when); room badge = weakest; sheet badge = weakest of its rooms. Feet-inch parser (`14'-6"`, `14 6`, `174`).
- **Gates**: room phase SD→DD, issuing LPC/DOB/CD/FF&E sets, and fabrication POs (millwork/stone/window/appliance words) all wait for field measurements; fabrication POs also require the fabricator's own measurements (`po.tradeVerified`) — the second measurement.
- **Fit checks**: items placed on a wall sum against the wall length; "left" shown on the card and in the room dialog (kitchen rear wall stack-up, hall-bath pinch point, laundry sink).
- **Change records**: a measured value that differs beyond `DB.company.dimTol` (½") creates a record listing every current sheet (incl. consultant sheets → "notify consultant"), estimate/CO line, PO and material carrying it; each goes stale until re-issued or ticked; a filed sheet affected raises "PAA / LPC amendment?".
- **Drawing register**: sets (deck, SD, LPC, DOB, CD, FF&E, structural, MEP), rev, status Current/Stale/Superseded, Drive link, New rev supersedes, Issue a set → issue checklist (stale, unverified rooms, dimension audit count) → transmittal; issuing LPC/DOB advances the filing.
- **Survey checklist**: generated from rooms; phone-first; optional mic; saves as field-measured.
- **Filings**: five fixed-fee tracks from the proposal with predecessors (survey, ACP-5, LPC permit, demo, framing), status, days in review, comment-round counter (3rd round flagged as additional service), Start/Submitted/Approved each draft the 50/25/25 invoice.
- **My day**: due design tasks, decisions and gates, drawings to re-issue, surveys outstanding; day sheet of touched things (rooms, sheets, issues, filings, timers) and recorded meetings → one tap logs hours to the right phase; timers on room cards; direct log line.
- **Studio (director)**: projects × phase / hours vs proposal / retainer / filings in review / survey / stale sheets / gates; designer-days without hours; who is on what.
- **Reminders/Home**: unverified rooms with drawings, stale sheets, filings in review, retainers at replenishment, "yesterday without hours" for designers.
- Seed: 140 Prospect Place (proposal lines, 120-hr retainer invoice, 11 rooms from the deck on listing dimensions, 7 sheets, 5 filings, 3 gates, kickoff meeting 9/5 as an unlogged 1.75-hr chip) and 45 Cranberry with a live millshop change (14'-6" → 13'-6") marking six sheets stale.

Next — **Studio B**: meeting intake (transcript → decisions/questions/promises, human-confirmed), promises with dates both directions, explorations with hour estimates on the portal, preference profile + deck check, client portal page, FF&E cards → purchasing, precedent pane, decision-maker routing.

## 9. Studio B — built 2026-09-06

`studio2.js`: 
- **Meeting intake** — "+ Meeting / transcript" on the board's Meetings tab: paste the recorder transcript; the assistant returns proposals (decision / question / promise / pref / ffe / site) tagged to rooms; each is edited inline and confirmed or dropped by a person (or "Confirm all shown"). Confirmed: decisions → room notes + the client's "Decisions so far" with who decided; questions → open decisions (client-owned ones appear in the client's "decisions we need from you"); promises → dated promises in either direction, and any with an hour estimate become **exploration** tasks the client can see the cost of; prefs → the profile (Loves / Never / Hard rules); ffe → selections; site notes → room notes. The 9/5 kickoff is seeded as 43 proposals to review.
- **Client tab** — what we owe / what the client owes with Done, preference profile (editable chips), explorations with "client approved the hours".
- **FF&E tab** — selections proposed → client approved → ordered → delivered → installed; "Add to purchasing" creates the material on the buy board with lead time and room, so it flows into the existing PO chain and gets flagged by a dimension change.
- **Deck check** — issuing a set runs the client's rules/dislikes against sheet titles and notes ("recessed can lighting", "beige palettes" caught on DECK-01) and asks before issuing.
- **Client portal** — "Where the design stands" (measured vs conceptual badge, latest deck, retainer hours, hours to date), what we owe you, what we need from you (with the hour cost of studies requested), filings in plain words, decisions so far by room, the profile.
- **Precedents** — "what we did last time" card on the Rooms tab.
- **My day / Studio / reminders** — meetings awaiting confirmation, promises due/overdue both directions, explorations not yet approved.
Not built (needs a desktop helper): passive capture of files opened in CAD. Decision (Alan, 2026-09-06): confirmed decisions stay portal-only for now — no automatic client emails.
