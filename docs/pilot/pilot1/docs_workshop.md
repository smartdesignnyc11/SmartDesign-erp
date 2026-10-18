# Documents Workshop: pilot1

Measured by the harness, back end checked by the referee, client view judged by the client agent, the owner and the designer. Everything above "Synthesis" is mechanical.

## Measured, per document type

| Type | Device | Made | Median taps | Target taps | Median seconds | Screens | Typed / filled | Validation stops | Not found after save | Back-end gaps |
|---|---|---|---|---|---|---|---|---|---|---|
| PO | desktop | 1 | 3 | 10 | 33 | 11 actions, 3 screens | 0 / 1 | 0 | 0 | estimate-line link on every line; vendor; vendor on file (vendorId) |
| PO | phone | 2 | 3.5 | 12 | 30.0 | 10.5 actions, 4.0 screens | 0 / 2 | 0 | 0 | vendor; vendor on file (vendorId) |
| RFQ | desktop | 1 | 4 | 12 | 28 | 11 actions, 3 screens | 0 / 2 | 0 | 0 | quotes due date; three vendors asked |
| change order | desktop | 1 | 4 | 10 | 32 | 13 actions, 5 screens | 4 / 7 | 0 | 0 | link to the estimate line or scope it changes |
| change order | phone | 1 | 12 | 12 | 53 | 30 actions, 8 screens | 7 / 7 | 0 | 0 | none |
| estimate | phone | 1 | 12 | 25 | 55 | 20 actions, 8 screens | 0 / 0 | 0 | 0 | none |
| invoice | desktop | 2 | 2.5 | 8 | 13.5 | 5.0 actions, 3.5 screens | 0 / 2 | 0 | 0 | cost code on every line |
| material request | desktop | 1 | 6 |  | 30 | 12 actions, 3 screens | 0 / 0 | 0 | 0 | the task it is for (cost line) |
| material request | phone | 1 | 6 | 5 | 59 | 14 actions, 4 screens | 3 / 9 | 0 | 0 | the task it is for (cost line) |
| pay application | desktop | 3 | 5 | 10 | 19 | 8 actions, 4 screens | 0 / 0 | 0 | 0 | a total above zero; line CO-2026-001 Radiant floor heat in primary bath: this period's % below the previous; line CO-2026-002 Sand & stain existing treads (3rd fl): billed 100% vs measured 0%; line Demolition & disposal: this period's % below the previous; line Electrical — rough & finish: this peri |

## Typed versus filled, per document type (the item library question, BACKLOG 1.18)

| Type | Documents | Lines | Fields typed | Characters typed into lines | Per line | Picked from a list | Filled, not typed (at save) |
|---|---|---|---|---|---|---|---|
| PO | 3 | 4 | 0 | 0 | 0 | 0 | 3 |
| RFQ | 1 | 1 | 0 | 0 | 0 | 0 | 2 |
| change order | 2 | 2 | 11 | 233 | 116 | 7 | 3 |
| estimate | 1 | 11 | 0 | 0 | 0 | 0 | 0 |
| invoice | 2 | 6 | 0 | 0 | 0 | 0 | 2 |
| material request | 2 | 0 | 2 | 0 | - | 1 | 6 |
| pay application | 3 | 16 | 1 | 0 | 0 | 0 | 0 |

Line descriptions as written (estimate, change order, invoice):
- change order CO-2026-003: GFI outlet in pantry wall: box, wiring from nearest circuit, GFI device and cove
- invoice INV-2026-039: Schematic design — 40% of phase
- invoice INV-2026-039: Design development — 40% of phase
- invoice INV-2026-039: Construction documents — 40% of phase
- invoice INV-2026-039: Filing & permits — 40% of phase
- invoice INV-2026-039: Construction administration — 40% of phase
- pay application INV-2026-040: Demolition & disposal
- pay application INV-2026-040: Framing, blocking & rough carpentry — measured by foreman update 9/2 — Framing & blocking – 3rd floor 90%; 1 running task still on elapsed time
- pay application INV-2026-040: Windows — front & rear façade
- pay application INV-2026-040: Plumbing — rough & finish
- pay application INV-2026-040: Electrical — rough & finish — measured by PM update 9/1 — Rough electrical 55%
- pay application INV-2026-040: Insulation, drywall, taping & prime
- pay application INV-2026-040: Tile — two baths
- pay application INV-2026-040: Flooring
- invoice INV-2026-041: Sarah Davis — Architect — 9/2 – 9/4
- estimate EST-2026-015: Windows — front & rear façade — Supply and install, LPC-compliant profiles, brick mold
- estimate EST-2026-015: Plumbing — rough & finish — Two baths, two kitchens, laundry; fixtures by allowance
- estimate EST-2026-015: Electrical — rough & finish — New circuits, lighting per plan, devices
- estimate EST-2026-015: Insulation, drywall, taping & prime
- estimate EST-2026-015: Tile — two baths — Waterproofing, tile labor; tile by allowance
- estimate EST-2026-015: Flooring — White oak 3rd fl; LVP garden
- estimate EST-2026-015: Millwork & countertops — Parlor and garden kitchens, laundry, living/dining built-ins
- estimate EST-2026-015: Trim, doors, paint & hardware
- pay application INV-2026-042: CO-2026-001 Radiant floor heat in primary bath
- pay application INV-2026-043: CO-2026-002 Sand & stain existing treads (3rd fl)
- change order CO-2026-004: Framing, blocking & rough carpentry — Raise stair landing guard to 42 inches finished height per code: additional guard height, balusters/posts, fasteners, finish match, install

## Back end, every gap by field (from the referee's audit)

- pay application: **line: this period's % below the previous** (15: INV-2026-040, INV-2026-040, INV-2026-040, INV-2026-040)
- PO: **vendor** (3: PO-2026-049, PO-2026-050, PO-2026-051)
- PO: **vendor on file (vendorId)** (3: PO-2026-049, PO-2026-050, PO-2026-051)
- material request: **the task it is for (cost line)** (2: GWB and cement board, 2 items)
- invoice: **cost code on every line** (2: INV-2026-039, INV-2026-041)
- PO: **estimate-line link on every line** (1: PO-2026-051)
- RFQ: **three vendors asked** (1: RFQ-2026-001)
- RFQ: **quotes due date** (1: RFQ-2026-001)
- pay application: **a total above zero** (1: INV-2026-042)
- pay application: **line: billed 100% vs measured 0%** (1: INV-2026-043)
- change order: **link to the estimate line or scope it changes** (1: CO-2026-004)

## Client view (client, owner, designer), grouped by document type, worst first

- all docs · change · brand_u_owner: One letterhead: real logo, SmartDesign, address, phone, NYC HIC license no., quiet "with Mercer & Bond" line. Full dates with year, plain units ("lump sum"), footer terms only where they apply, pay instructions on every 
- all invoices · slows · brand_u_owner: No way to pay is printed: no ACH details, no pay link, no remit-to. Every invoice makes the client ask how to pay.
- all print docs · blocks · brand_u_sarah: Strip every internal note and reviewer instruction from client output. Notes the client sees should be written for the client only, and send should fail if a "check before sending" note is still there.
- all print docs · slows · brand_u_owner: Dates have no year ("Thu, Sep 3", "Valid until Sun, Oct 4"). "1 ls" is estimator shorthand. Content fills the left 60% of the page with dead space on the right. None of it reads as premium.
- all print docs · slows · brand_u_sarah: Branded letterhead: logo mark, "SmartDesign" with the full legal entity, address, phone, licence numbers and a one-line promise (design, build, plumbing and electric under one roof). Full dates with year. "Lump sum" in p
- all print docs · annoys · brand_u_owner: Clean, but it's a generic SaaS template, not a landmark brownstone firm: "SmartDesigns" in plain bold text, no logo or mark, no address, phone, license no. or Mercer & Bond line. Our name is SmartDesign, not SmartDesigns
- all print docs · annoys · brand_u_owner: The same footer goes on everything: progress terms, retainage and CO approval, even on an hourly design invoice and on change orders. It reads as boilerplate nobody checked.
- all print docs · annoys · brand_u_sarah: Clean and legible, but it is a generic SaaS template: "SmartDesigns" in plain bold text, no mark, no address/phone/licence/web, nothing that says landmark brownstones, one roof, in-house trades. Our name is SmartDesign, 
- all print docs · annoys · brand_u_sarah: Dates have no year ("Thu, Sep 3") on contracts and pay apps; units read "1 ls" (lump sum jargon); the same retainage/progress-invoice footer prints on a CO, a design-hours invoice and an estimate where it does not apply.
- client portal · annoys · brand_u_owner: It looks like an app, not like us. Two identical chat icons in the header, a ragged indent on the work-hours/PM lines, photo captions cut off ("Parlor kitchen ba"), and "Alan" with no surname or title.
- CO docs · slows · brand_u_sarah: The title of the change goes in the item line, with the cost code kept internal. Always show schedule impact ("none" if none). Drop Net 15 from COs, or say "billed on next pay application".
- CO-2026-003 · annoys · client: Clear: one GFI outlet in the pantry wall, $285. The only friction is that the item has no title, just a grey description line.
- CO-2026-003 · annoys · client: Scope is plain and complete (box, wiring, GFI device, plate). Not said: whether patching and painting the pantry wall is included.
- CO-2026-003 · annoys · client: The portal is calm and well laid out, but the header has two identical chat-bubble icons, and "Your project manager: Alan" gives no surname.
- CO-2026-003 · annoys · client: Why does one pantry outlet add a full working day to the schedule?
- CO-2026-003 · annoys · client: The line has no title, only a description, and "1 ls" (lump sum) means nothing to me.
- CO-2026-003 / CO-2026-004 · annoys · brand_u_owner: Voice is fine and plain. But "via Angel, on site" is internal. CO-004's item heading is our cost code ("Framing, blocking & rough carpentry"), not the change. Schedule impact shows on 003 but not on 004.
- CO-2026-003 portal · good · brand_u_owner: Clear and right: plain title, price, CO number, View/Ask/Approve on one card. Keep this pattern.
- CO-2026-003, -004 · annoys · brand_u_sarah: "Terms: Net 15" on a change order that is not an invoice. 003 shows schedule impact, 004 shows none at all, so the client cannot tell whether 004 has no impact or it was forgotten.
- CO-2026-003, -004 portal · good · brand_u_sarah: View / Ask / Approve right on the card, with price and date: clear, one tap, nothing to chase. The print COs are short, plainly worded and signable.
- CO-2026-003, CO-2026-004 · slows · client: Yes. Both are on Overview under "Waiting on You" with Approve, about one tap. But Approve is an outline button with the same weight as View and Ask, it sits below the fold under two design choices, and I can approve with
- CO-2026-003, CO-2026-004 · annoys · client: Each says "Terms: Net 15". Do I pay when I sign, or is it billed on the next pay application? Neither says.
- CO-2026-003, CO-2026-004, EST-2026-015, INV-2026-040 · slows · client: Clean and legible, but not premium: a plain text wordmark, no logo, no firm address, phone, licence or PM name, dates with no year, descriptions in small grey type.
- CO-2026-004 · slows · client: $780 to raise the stair landing guard to 42 in. is clear, but the line is titled "Framing, blocking & rough carpentry", which is a trade bucket and not what I am buying.
- CO-2026-004 · slows · client: "The planned guard height is raised" means the original plans fell short of code, so why is a code requirement an extra for me? It also gives no schedule impact, unlike CO-2026-003.
- CO-2026-004 · slows · client: Why am I paying for a code item the plans missed, and does the higher guard change the stair finish or railing design?
- CO-2026-004 · annoys · client: Not clear: the line "Framing, blocking & rough carpentry" should read something like "Stair landing guard: raise to 42 in. (code)".
- CO-2026-004 · annoys · brand_u_owner: Charging $780 for a guard height that code requires, on a job we designed ourselves, contradicts "no other contractor to blame". The client will ask why our drawings missed it.
- CO-2026-004 · annoys · brand_u_sarah: The item title is the cost code "Framing, blocking & rough carpentry"; the real change (guard raised to 42 in) is in grey small text. CO-2026-003 does it the other way round. Notes on 003 name "via Angel, on site", which
- CO-2026-004 · change · brand_u_owner: Hold it. Decide whether a code-required guard is ours to absorb. If it's billed, say why it wasn't in the drawings, title it by the change, and show schedule impact as on CO-003.
- EST-2026-015 · blocks · client: A new $416,000 estimate for the same "Garden unit + 3rd floor renovation" I am already under contract for ($485,000, EST-2026-014). The lines and prices match my contract minus demo and framing. Am I being asked to buy i
- EST-2026-015 · blocks · client: Under "Scope, allowances & exclusions" there are no exclusions at all, and no inclusions beyond a few grey notes. Five lines have no description.
- EST-2026-015 · blocks · client: "20% deposit" on $416,000 is $83,200. Would that be a second deposit on top of the one I already paid under my contract?
- EST-2026-015 · blocks · client: Why is there a second estimate for my job, $69,000 less and without demo and framing? Is my contract being replaced?
- EST-2026-015 · blocks · brand_u_owner: A second estimate for 121 State Street at $416,000, while the pay apps run on a $485,000 contract from EST-2026-014. It has no demo or framing lines and doesn't say it's a revision or an add. The client will think the pr
- EST-2026-015 · blocks · brand_u_sarah: A new $416,000 estimate for 121 State Street, dated Sep 4, on a job already contracted at $485,000 (EST-014) and 54% billed. It also drops demo and framing. The Kleins will think the price changed or that we lost track.
- EST-2026-015 · blocks · brand_u_sarah: Do not send a second estimate on a contracted job. Make it a change order or a revision of EST-014 that shows the delta, and say which document it replaces.
- EST-2026-015 · slows · client: Allowances are listed (tile $18/sf, fixtures $9,500, lighting $7,200) but not what happens when I go over. $9,500 of fixtures for two baths, two kitchens and a laundry looks low.
- EST-2026-015 · slows · client: The only landmark note is "LPC-compliant profiles". There is nothing on LPC approvals or protecting historic fabric, which is why I hired a landmark firm.
- EST-2026-015 · slows · client: Five lines have no description: Insulation, drywall, taping & prime; Trim, doors, paint & hardware; Exterior — scaffold, brick mold, paint; Permits, inspections, special inspections; General conditions & supervision. "LV
- EST-2026-015 · slows · brand_u_owner: It says "Scope, allowances & exclusions" but lists no exclusions, and the deposit has no dollar amount. "LVP garden" and "3rd fl" read like a takeoff sheet, not a proposal for a landmark house.
- EST-2026-015 / INV-2026-041 · change · brand_u_owner: Label the estimate as a revision or add and tie it to the $485,000 contract, with real exclusions and the deposit in dollars. Hourly invoices list what the hours produced.
- INV-2026-039 · slows · brand_u_sarah: Every phase is "40% of phase", including Construction administration and Filing at the filing milestone. A client will ask why they pay 40% of CA before construction starts. Bill-to has an empty address line (same on 041
- INV-2026-039 · annoys · client: Every line reads "40% of phase", including Construction administration, which can't have started at filing.
- INV-2026-039 · annoys · brand_u_owner: 40% of Construction administration and Filing & permits billed "at filing", before construction starts. No client address (blank line under "Rivera family").
- INV-2026-039, INV-2026-041 · blocks · client: These are not mine. They belong to the Rivera family (45 Cranberry St, $17,080) and the Jessop family (140 Prospect Place, $3,900) and show their names and emails. If their bills reach me, mine may reach them.
- INV-2026-039, INV-2026-041 · blocks · client: One client's file leaks to another, and 041 bills a named employee by the hour ("Sarah Davis — Architect, 19.5 hr at $200"). That is the opposite of premium and discreet.
- INV-2026-039, INV-2026-041 · blocks · client: Why did I receive the Rivera and Jessop invoices, and who received mine?
- INV-2026-039, INV-2026-041 · blocks · client: Not on my portal, which is right since they aren't mine, and that makes the copies that reached me stranger.
- INV-2026-039, INV-2026-041 · annoys · client: The footer about retainage and change orders is printed on design-fee invoices that have no retainage. It is boilerplate, not written for the document.
- INV-2026-040 · blocks · client: No. Every line shows "Previously 51.67%", even demolition and windows, which the portal still lists as upcoming (Demo & subfloor prep 9/3-9/11, LPC window sign-off 9/3-9/12). It reads like a deposit spread over the lines
- INV-2026-040 · blocks · client: Only framing ($11,103) and electrical ($1,548) move this period, and the note "4 lines fell back to cost — check them before sending" tells me the firm has not checked what it is charging me for.
- INV-2026-040 · blocks · client: It says "Less retainage (10%)", yet retainage to date is $16,933, only 6.4% of $266,335 completed. There are two totals blocks (Current payment due and Total this invoice, both $11,386), with Balance to finish wedged bet
- INV-2026-040 · blocks · client: The portal says "Invoices Due $81,316", but what I received adds up to $13,051 ($11,386 + $0 + $1,665). No invoice says how to pay: no ACH details, check payee, pay link or firm address, just "Net 15".
- INV-2026-040 · blocks · client: Demolition and windows are billed at 51.67%, while the portal shows demo and the LPC window sign-off as still upcoming this week.
- INV-2026-040 · blocks · client: Its portal view is the Overview: an "Invoices Due $81,316" chip, no invoice and no Pay button. I'd guess Account, then the invoice, then pay, at least three taps, with no payment method shown.
- INV-2026-040 · blocks · brand_u_sarah: Two stacked totals: "Current payment due $11,386", then Balance to finish, then a second Subtotal/retainage block and "Total this invoice $11,386". Every line shows exactly 51.67% previously, which looks spread, not meas
- INV-2026-040 · slows · brand_u_owner: "Previously 51.67%" is the same on all 13 lines, so it looks computed, not measured. The totals block shows "Current payment due" and then "Total this invoice" with Subtotal/retainage below Balance to finish: two totals,
- INV-2026-040 · annoys · client: Lines 2 and 5 carry internal notes ("measured by foreman update 9/2 — ... 1 running task still on elapsed time"). Line 14 "CO-2026-001 Radiant floor heat in primary bath" puts a code in the name.
- INV-2026-040, -042, -043 · blocks · brand_u_sarah: Internal staff note prints to the client: "4 lines fell back to cost — check them before sending." Same for "measured by foreman update 9/2 … 1 running task still on elapsed time". Not our voice, and it tells the client 
- INV-2026-040, INV-2026-042, INV-2026-043 · slows · client: Lines are named only by trade ("Plumbing — rough & finish"). Nothing says in plain words what was done this period, except two internal measuring notes.
- INV-2026-040, INV-2026-042, INV-2026-043 · annoys · client: Internal workflow text is printed to me: "check them before sending", "fell back to cost", "1 running task still on elapsed time". A landmark firm does not send its draft notes.
- INV-2026-040/-042/-043 · blocks · brand_u_sarah: One pay application per period per project, with base contract and CO lines on it. Never send a $0 app. One summary block that ends in one "Amount due". Number and date apps in the order they are certified.
- INV-2026-040/042/043 · blocks · brand_u_owner: An internal instruction is printed for the client: "4 lines fell back to cost — check them before sending." INV-040 line 2 also carries crew notes ("1 running task still on elapsed time"). That's our kitchen, not their i
- INV-2026-041 · blocks · brand_u_sarah: Line reads "Sarah Davis — Architect". My title is designer; "Architect" is a licensed title in NY and cannot appear unless it is true. Hours are one line with no tasks, so 19.5 hr at $200 reads as a bare number.
- INV-2026-041 · blocks · brand_u_sarah: Show the real role title from the staff record (Designer) and list the tasks behind the hours (e.g. 9/2 tile layouts 4.0 hr).
- INV-2026-041 · slows · brand_u_owner: "Sarah Davis — Architect, 19.5 hr" with no word on what was done. The client will ask what they bought. Also a blank address line under "Jessop family".
- INV-2026-041 · annoys · client: The line is a person's name and title ("Sarah Davis — Architect"), not the work done in those 19.5 hours.
- INV-2026-042 · blocks · brand_u_owner: The Kleins get a $0 invoice. Then a second pay app (043) the same day, and a third (040) the day before. Three pay apps in two days for one house says we don't know what we're billing.
- INV-2026-042 · blocks · brand_u_sarah: A $0 pay application went out (CO-001 0% this period). Its "previous applications" $251,066 already includes INV-043, which is numbered after it. A client gets three pay apps in two days with numbers that only add up in 
- INV-2026-042 · annoys · client: A $0 invoice for the radiant floor heat CO (50% before, 0% this period). I can't tell why it was sent or whether I owe anything.
- INV-2026-042 · annoys · client: What does a $0 invoice want from me: payment, a signature, or nothing?
- INV-2026-042 vs 043 · blocks · brand_u_owner: Same completed-to-date ($268,185) and retainage, but different "Less previous applications" ($251,066 vs $249,401). 042 counts 043 as previous though it's numbered first. A client or their lender will catch it.
- INV-2026-042, EST-2026-015 · blocks · client: Not on the portal. I can't accept the estimate or acknowledge the pay application from my phone, only read a PDF.
- INV-2026-042, INV-2026-043 · blocks · client: Same day, same $268,185 completed to date, but "Less previous applications" is $251,066 on 042 and $249,401 on 043. So 042 counts 043 as already billed, though 042 is numbered first.
- INV-2026-042, INV-2026-043 · blocks · client: Three pay applications in two days (040 on Sep 3, 042 and 043 on Sep 4), when the estimate terms say "progress billing monthly". I want one application a month.
- INV-2026-042, INV-2026-043 · annoys · client: Line names start with the CO number ("CO-2026-002 Sand & stain existing treads (3rd fl)") and abbreviate ("3rd fl").
- INV-2026-043 · blocks · client: The portal says "54.39% certified on INV-2026-043 · 15% measured on site", so I have been billed for more than three times what the crew has measured. This is my first call to Alan.
- INV-2026-043 · blocks · client: On the portal it appears only as a Progress line ("certified on INV-2026-043"), with no amount, nothing to open and no way to pay.
- INV-2026-043 · slows · client: Clear: CO-2026-002 tread sand & stain at 100%, $1,850 less $185 retainage = $1,665. But the signed CO it rests on is not attached or referenced.
- portal Overview · slows · brand_u_sarah: Add the firm's mark and the project address to the header. Reconcile or explain certified vs measured before showing both. Break down Invoices Due. Coming Up shows only future starts. Use red only for real deadlines, in 
- portal Overview · annoys · brand_u_owner: "Invoices Due $81,316" and "Waiting on You 8" in red is the first thing they see: a dunning screen. Nothing ties $81,316 to the invoices they hold ($11,386 + $1,665).
- portal Overview · annoys · brand_u_sarah: No logo or firm name in the header. Two identical chat icons sit next to a flag. Text lines are indented unevenly. "Waiting on You 8" and the first decision are in red ("as soon as you can") so the home screen reads as p
- portal Overview · annoys · brand_u_sarah: "Invoices Due $81,316" with no breakdown, next to pay apps of $11,386 and $1,665. "What's Coming Up" lists work that started 8/10 and 8/31. Photo captions are cut off ("Parlor kitchen ba", "Casing on the re").
- portal Overview (CO/INV) · slows · brand_u_sarah: Progress card says "54.39% certified on INV-2026-043 · 15% measured on site". The client will read that as overbilled by 39 points. "Recently Completed" is empty while half the contract is billed.
- portal Progress · blocks · brand_u_owner: "54.39% certified" sits next to "15% measured on site", and "Recently Completed" is empty. The client reads that we billed 54% for 15% of the work. That's the call we least want.
- progress billing · change · brand_u_owner: One pay application per project per period, with COs as lines inside it. Never send a $0 invoice. Previous applications computed in issue order. Internal notes and "check before sending" text stripped by a send gate that
- progress billing / portal · change · brand_u_owner: Reconcile certified vs measured before anything reaches the client. If they differ, explain it in one plain sentence with photos, or don't bill ahead of the work.

## Creators, by document type

- PO · slows · u_chen: D1 PO-2026-049 at 1 tap and 9s was only fast because Order makes an empty $0 draft. PO-2026-050 took 51s over 5 screens (Purchase Orders > Vendors > Ask > Requests) looking for a lumber vendor that is not in the list.
- PO · annoys · u_chen: D1 PO-2026-051 (33s, 3 screens) was me acknowledging the rosin paper request. The speed means nothing, because three POs still sat as $0 drafts with no vendor days later.
- PO · blocks · u_chen: D2 0 characters typed, because there was nothing to put in. Vendor, $2,140.50, card and receipt for PO-2026-049 should have come from the vendor mail and the card line. Instead the PO stayed at $0 and that money never reach
- PO · blocks · u_chen: D3 On the phone I could not record "bought on card at a yard that is not our vendor". There is no add-vendor step from the PO and no card-purchase option, so PO-2026-049 stayed a vendorless draft.
- PO · slows · u_chen: D3 For PO-2026-050 (studs) I went back and forth across 5 screens, including Ask, on a small screen looking for a lumber vendor, then left it with no vendor and no price.
- PO · blocks · u_chen: D4 No Brooklyn Lumber vendor record (no W-9, no COI), so there was nothing to put on PO-2026-049. The PO also had no field for the vendor's promised date, and I got five dates (9/4, 9/10, 9/8, 9/9, Thu 9/10 7am) with none o
- PO · slows · u_chen: D4 Draft POs do not show on Purchasing > Deliveries, so boards, rosin/tape and studs were on no screen. "Late to Site 0" was false while Alberto's studs were a day late.
- PO · blocks · u_chen: D5 No. PO-2026-049 shows $0 against a $2,140.50 card charge, PO-2026-050 has unit price 0, and the Promise Ledger said 0 broken while Brooklyn Lumber had broken five dates. The totals only hold what I type in.
- PO · blocks · u_chen: D6 1) Order on a request asks "ordered from whom, by when" in the same step, not just an empty draft. 2) A draft PO still shows on Deliveries as "expected, not confirmed", and a $0 draft with no vendor counts as a problem.
- PO · annoys · u_chen: D6 3) Offer "Log a Promise" on the PO right after every call or vendor mail that names a date. 4) Let me create a vendor from the PO and request the W-9/COI there.
- PO · annoys · u_chen: D8 The PO-2026-049 link came from the estimate line (Insulation/drywall, code 07). The quantities and prices I kept in my diary and in mail to Alan and Angel, from the vendor mail and my calls.
- PO · blocks · u_chen: D9 2x4x8 KD stud (ea) with its last price should have priced PO-2026-050. Instead it sat at 0 and the studs went late. Brooklyn Lumber's $2,140.50 for 25+6 boards should be in price history.
- RFQ · slows · u_chen: D1 28s and 4 taps to create RFQ-2026-001 is right. The time that matters came after: it went to Angel's phone for a quantity check and nothing goes to vendors until he answers.
- RFQ · slows · u_chen: D2 I typed nothing. The quantity was not on the line to fill (EST-2026-014 says 1 ls, no door count), so I had to mail Angel for count, sizes, swing, prehung and hardware.
- RFQ · blocks · u_chen: D4 No door count, size or budget on the estimate line, and only one door/millwork vendor in the list (Carlos Millwork), so I could not name three vendors.
- RFQ · slows · u_chen: D5 No budget on the line, so when quotes come in there is nothing to compare them to. It is over $2,500 and needs three quotes, but I have one vendor.
- RFQ · slows · u_chen: D6 1) Carry quantity and units from the estimate line, or ask for them when the line is a lump sum. 2) Suggest door/millwork vendors and let me add one from the RFQ.
- RFQ · slows · u_chen: D8 The line came from EST-2026-014 "Trim, doors, paint & hardware". The door details will have to come from Angel's mail and the plans.
- RFQ · slows · u_chen: D9 Interior prehung door (ea) and door hardware set (ea) should replace the 1 ls line, with sizes and swing as fields, so the RFQ asks vendors for priced units.
- change order · slows · u_alan: D1 CO-2026-003 on the phone: 12 taps and 53s sounds fine, but it took 30 actions over 8 screens (Tasks, Projects, Today, Costs, then Billing) because nothing in the project links to change orders. I spent about 10 actions j
- change order · slows · u_alan: D1 CO-2026-004 at the desk: 4 taps and 32s once I knew it lives under Billing > Change Orders. That is about right. It still went through Field and Ask before Billing, because Angel's question is in Field and the CO is not.
- change order · annoys · u_alan: D2 CO-2026-003: I typed all 7 of 7 fields. Project (121 State), client (Klein) and the task it extends (Rough electrical) should have come from the job I was standing in, and cost should have come from the GFI item or my us
- change order · annoys · u_alan: D2 CO-2026-004: the description (stair landing guard to 42 in, code), the cause date (9/8) and the project should have come from Angel's Field question. I retyped 146 characters the system already had.
- change order · slows · u_alan: D3 Finding change orders on the phone means walking the menu tab by tab. On site at the Kleins' I had no "New Change Order" on the project or on the Field item, so the hunt ate my actions.
- change order · blocks · u_alan: D4 No price or cost basis on screen for either CO. The GFI $285/$170 and the guard $780/$480 are from my head. For CO-004 I did not have the linear feet of the landing guard either, so I still owe a check with Angel.
- change order · slows · u_alan: D4 Nothing on Billing or Home showed "CO owed to client" or the 48h clock. CO-2026-003 sat at $0 and unsent overnight, and only my diary knew.
- change order · annoys · u_alan: D5 The CO math is just my own two numbers, so I trust it. I do not trust where it lands: Projects shows the contract at $493,050 against $485,000 on EST-2026-014, and nothing on screen ties the COs into that difference. Bil
- change order · annoys · u_alan: D5 CO-2026-004: I ticked the Framing line, but the record carries no link to the estimate line or scope it changes, so the CO total cannot roll into that line's budget or job cost. The number is right and it lands nowhere.
- change order · blocks · u_alan: D6 1) New Change Order from the project and from a Field question, carrying project, client, description, cause date and the estimate line. 2) Price and cost basis on screen (item library, last price for the same item). 3) 
- change order · annoys · u_alan: D6 4) Ticking the line it changes must save as a real link, so the CO feeds that line's budget, job cost and the contract total. 5) Show the contract total reconciled: estimate plus each CO.
- change order · slows · u_alan: D7 Both CO lines were written from scratch: "add GFI receptacle" (87 characters) and "raise stair landing guard to 42 in per code" (146 characters). Small electrical adds and code-driven guard and rail fixes come up on almo
- change order · annoys · u_alan: D8 CO-2026-003: the description was from my own site notes, and the $285/$170 from the plan in my diary. CO-2026-004: retyped from Angel's question in Field, with nothing copied in the app.
- change order · slows · u_alan: D9 GFI receptacle, add: description, unit ea, price $285, cost $170, cost code Rough electrical (SD Electric). Guard extension to 42 in: description with the code reference, unit lf, price and cost per lf, cost code Framing
- estimate · blocks · u_alan: D1 EST-2026-015: the 12 taps and 55s are not a real estimate. Billing > Estimates has no New Estimate button, so Duplicate on EST-2026-014 cloned the whole $485,000 contract (13 lines). The time went into deleting lines one
- estimate · annoys · u_alan: D2 I typed nothing (0 characters) because I never got to write the parlor floor line. Client, project and the standard scope/exclusions block should start filled for a new estimate on 121 State, not cloned from the contract
- estimate · blocks · u_alan: D3 Remove line renumbers every control after each tap, so it is one tap per round trip. Clearing 11 unwanted lines one at a time, one-handed, on a cloned $485K estimate is not workable. I need multi-select delete or a blank
- estimate · blocks · u_alan: D4 No floor area, wood species, finish or cost basis for the parlor floor anywhere I looked (mail, Costs). I will not invent a price, so the estimate stopped there. There was no way to ask Angel for a field measure from the
- estimate · blocks · u_alan: D5 No. The draft total is the cloned $485K contract minus two lines. That is a meaningless number with Klein's name on it, one wrong tap from being sent.
- estimate · blocks · u_alan: D6 1) A New Estimate button: blank, or from a template or item list, never Duplicate of the contract. 2) Multi-select remove, and controls that do not renumber. 3) A one-tap request to the foreman for the measurements (sq f
- estimate · slows · u_alan: D7 I never got far enough to write it, but the parlor floor refinish (sand, stain, finish coats, protection, furniture moves) plus the standard inclusions and exclusions is a line I write on every job.
- estimate · annoys · u_alan: D8 The only "copy" the system offered was the whole EST-2026-014 contract via Duplicate. That copied 13 lines I did not want and none I did.
- estimate · slows · u_alan: D9 Hardwood floor refinish: description (sand, stain, 3 coats), unit sf, price and cost per sf, cost code Finish flooring, with the standard exclusions attached.
- invoice · none · u_billing: D1 Right speed: INV-039 took 2 taps/14s and INV-041 3 taps/13s, both built from the Billing Queue row with nothing typed. The time went elsewhere: the day's work took three turns, mostly hunting for where things live.
- invoice · slows · u_billing: D1 INV-041 went through 4 screens (Ask > Billing > Invoice). I started in Ask because the assistant's "waiting on you" list and the Billing table each hold part of what I owe, so I check both before I bill.
- invoice · none · u_billing: D2 Nothing. I typed 0 characters. The amount, client, due date and line all came from the queue row (Cranberry 40% at filing $17,080; Jessop 19.5 design hours $3,900).
- invoice · none · u_billing: D4 Nothing was missing for these two flat invoices. The milestone, hours, rate and client were on the row. Missing around it: payment records had no deposit evidence, so I could not tell a client what was already paid.
- invoice · none · u_billing: D5 Yes. $17,080 is the 40% filing milestone and $3,900 is 19.5 h x $200. Each sum is one line I could check in my head, and both had a cost code on every line.
- invoice · annoys · u_billing: D6 1) The queue should hold the stored-materials item or the line-by-line invoice, not both, or say "includes Windows; stored materials will drop". 2) One list of what Billing owes, instead of the assistant's list and the B
- invoice · none · u_billing: D7 None from scratch. The design-fee milestone (% at filing) and the banked design hours come on every design job, and the queue built both lines for me.
- invoice · none · u_billing: D8 None copied. The descriptions came from the contract fee schedule (Cranberry) and the designer's hours (Sarah Davis 9/2-9/4).
- invoice · none · u_billing: D9 The fill-in already worked: rate, unit (hour) and cost code came through on the hours line. A library is not what was missing.
- material request · slows · u_angel: D1 59s and 6 taps for 2 lines is right for a phone; the form itself was quick. The time went to getting there: 4 screens (a stale screen, Today, Site, Requests) before I could start.
- material request · annoys · u_angel: D1 One of my 14 actions went to deleting a junk third line the parser made out of my date words ("needed by Mon 9/7 for the floor crew"). It cost me time and I still had to check the card afterwards.
- material request · slows · u_angel: D2 I typed the item names, the quantities and the needed date. The job (121 State), deliver-to, who it goes to (Chen) and the task it is for were already known from Today and the floor-crew task, so it should have offered t
- material request · annoys · u_angel: D2 "Needed Mon 9/7" should be a date pick, not words for a parser. Typed, the date became a line item, and the card still showed the chip as a line and "2 items" after I removed it.
- material request · annoys · u_angel: D3 Getting to Requests on the phone is the hard part: it sits under Site, not on Today where I start the day. With gloves on, a "Request Material" button on Today next to the task it is for would save the 4-screen walk.
- material request · annoys · u_angel: D3 When I removed the junk line I could not tell if the card had updated: it kept showing the parser chip. On a small screen what I send has to read back exactly what I will get.
- material request · blocks · u_angel: D4 It never told me 9/7 is Labor Day. I asked for a delivery date nobody can make, and only noticed it myself. Alan later moved it to Fri with the boards, but the form should have flagged the holiday when I picked the date.
- material request · blocks · u_angel: D4 Afterwards the card showed no acknowledgement for 6 h and then "Not Ordered" for days, while Chen's mail said he aimed for Friday. I needed the vendor, ship date and PO on the card, plus whether we already have rosin or 
- material request · annoys · u_angel: D5 There were no prices, so there was no total to check. What I did not trust was the count: I asked for 4 tape and 4 rosin, and Chen's mail says tape 6 rolls. The app never showed the change or who made it.
- material request · annoys · u_angel: D5 "2 items" on the card while the parser chip still showed as a line means one record gave two counts. A request that turns into a PO has to keep my line quantities, or flag a change for me to accept.
- material request · blocks · u_angel: D6 1) Needed-by is a date pick that warns on holidays and weekends, and no free-text parsing into lines. 2) The card shows the office's real status: acknowledged by whom, PO number, vendor, ship date, and any quantity chang
- material request · slows · u_angel: D6 3) A Request Material button on Today and on the task, with job, task, cost line and deliver-to filled in. 4) Unacknowledged after 4 h should go to Chen and Alan on its own, not as a banner telling me to call the office.
- material request · annoys · u_angel: D7 Not an estimate, CO or invoice. Still, I write floor protection (blue tape, rosin paper) before every floor crew on every job, and I write it from scratch each time.
- material request · annoys · u_angel: D8 I did not copy anything. Items and quantities came from my head and my notes for the floor crew. Nothing in the app offered a past request or the last job's floor-protection kit.
- material request · slows · u_angel: D9 Blue tape and rosin paper should come from the item library: name, unit (roll), usual quantity per floor, last vendor and price, and the floor-protection or general-conditions cost code, so I pick two lines and change on
- material request · slows · u_angel: D9 The Demo kit offered on the Requests banner shows a kit works. A Floor Protection kit (rosin, tape, Ram Board, corner guards) tied to the flooring task would turn this request into one pick.
- material request · slows · u_chen: D1 6 taps and 30s is fine for one request, but the time went on a detour through Home > Vendors, and Apply on Home only put it on the Buy Board, so the request still read "not acknowledged" and I had to come back on Purchas
- material request · annoys · u_chen: D2 I typed nothing. What it should have known: Brooklyn Lumber's 9/1 mail says order 88412 (25 GWB 1/2 4x8 + 6 cement board) was filled and paid on the Square card for $2,140.50, and the request still showed "not ordered".
- material request · blocks · u_chen: D4 Missing: that the field had already bought it. The card purchase and the vendor mail never reached the request, so I spent the day tracing an order that was already paid for.
- material request · annoys · u_chen: D5 No money on it. The $2,140.50 that was really spent lived only in a vendor mail.
- material request · blocks · u_chen: D6 1) One step on the request: "bought on card, vendor X, receipt", without needing a vendor record, so a field purchase is acknowledged and closed the moment I hear about it.
- material request · annoys · u_chen: D8 Description came from Angel's request. The real order detail (25 GWB 1/2 4x8 + 6 cement board, order 88412) I copied from Brooklyn Lumber's 9/1 mail into my diary and mail, not into the app.
- material request · slows · u_chen: D9 GWB 1/2 4x8 (sheet), cement board (sheet), rosin paper (roll), blue painter's tape (roll), each with unit, last price and cost code 07, should have filled in from a library.
- pay application · slows · u_billing: D1 The 5 taps/17s for INV-040 is not the real time. I held it overnight to check the Windows line on Progress Billing against the $13,970 stored-materials row. The real time was a day, not 17s.
- pay application · annoys · u_billing: D1 INV-042: 11 actions, 21s, and all it gave me was an empty $0 draft, because tapping New Progress Invoice on CO-001 saves a draft at once. INV-043 took 8 actions over 5 screens (Ask > Billing > Change Order > Invoice) for
- pay application · none · u_billing: D2 Nothing typed. The % this period was proposed for me (Framing 27.08% from the foreman, Electrical 3.33% from the PM, CO-001 0%). The trouble was not typing. It was that I could not tell whether the proposed % was true.
- pay application · blocks · u_billing: D4 INV-040: neither the queue's "Send INV-040" row nor the "Draft $13,970 stored materials" row said they share the same 121 State windows. I only found the overlap on Progress Billing, and only there could I see that the "
- pay application · blocks · u_billing: D4 CO lines showed no measured % from the field. On CO-001 I could not tell whether the radiant heat was done, so I left a $0 draft. On CO-002 I billed 100% on approval alone, and the harness says measured was 0%. The CO sc
- pay application · annoys · u_billing: D5 I trusted the retainage arithmetic ($12,651 to $11,386 net; $1,850 to $1,665 net). I did not trust the %s. The job is $143,593 over-billed against about 14% measured, and INV-040 saved with every one of its 14 lines at a
- pay application · blocks · u_billing: D5 The totals added up but were wrong against the work. INV-043 billed CO-002 at 100% against 0% measured, and INV-042 saved a $0 total. The app let me save both without a stop.
- pay application · blocks · u_billing: D6 1) Stop or warn when the billed % is above the measured % (CO-002 100% vs 0%) or a line's % drops below the previous period. 2) New Progress Invoice should not save an empty $0 draft. 3) Show the field-measured % and who
- pay application · none · u_billing: D8 None copied. Lines came from the 121 State schedule of values and from the CO titles (CO-001 radiant floor heat, CO-002 sand & stain treads).
- pay application · slows · u_billing: D9 Stored materials should sit on the SOV item it belongs to (Windows, with the contract's stored-materials rule), not as a separate queue item. Then the line's billed, stored and measured numbers would fill in together, an
- payment reversal · blocks · u_controller: D1 Rivera $5,000 + $16,350 reversal took zero seconds because it can't be done: the payment row and invoice show "Paid · read only" with no Reverse or Void for Billing or for me.
- payment reversal · blocks · u_controller: D4 A recorded client payment carries no proof of who typed its method, reference or deposit account, or when. Billing said there was no method on 9/4, and by 9/8 the screen read "ACH" with the invoice number as reference.
- payment reversal · blocks · u_controller: D5 Receivable is overstated by $21,350 (Rivera recorded, never in Chase) and the app will not post the correction, so I cannot trust the AR total or close August.
- payment reversal · blocks · u_controller: D6 3) Reverse and Void on recorded payments and bills, with a required reason, posting a linked reversal with who, when and why. The invoice text already promises this.
- vendor bill · blocks · u_controller: D1 Never finished, so nothing to measure: I opened New Vendor Bill for Carlos CM-0102 ($19,000) at 10:30 Thu 9/3, typed vendor, invoice # and project, and the turn's 16 actions ran out; the draft was left unsaved and was st
- vendor bill · slows · u_controller: D1 The time went to everything around the bill rather than the form: finding the PO (Purchasing shows "No purchase orders yet"), then mailing Alan for the PO-2026-048 total. He hadn't answered three days later, so the bill 
- vendor bill · annoys · u_controller: D2 I typed the vendor, the invoice number (CM-0102) and the project (121 State Street). All three are on the attached PDF and on the PO the assistant says exists. Amount, date 9/1, net 15 and due 9/16 were next, and those a
- vendor bill · slows · u_controller: D2 The PO link should have come from the invoice ("progress billing against PO-2026-048"). Instead the Purchase Order select offered only "-- none --".
- vendor bill · blocks · u_controller: D4 I was missing the PO-2026-048 total, its progress schedule and any receipt. CM-0091 $38,000 had already been paid with nothing received, and with CM-0102 that is $57,000 billed against a PO I could not see.
- vendor bill · blocks · u_controller: D4 The approved amount and the approver weren't on the bill. Banking showed WW-2026-118 as "pm-approved" at $33,500, while Alan approved $29,700 and disputed $3,800 in mail. The PM's decision only lived in my mailbox.
- vendor bill · slows · u_controller: D4 Vendor risk facts were never joined on the bill: bank details changed 8/20, no W-9, paid before approval. I pieced the Window Works picture together from Approvals, the vendor statement in mail and Alan's mail.
- vendor bill · blocks · u_controller: D5 I did not trust the bill amount against the PO. "Bills over the PO stop at the PO" is enforced by me reading mail, because Purchasing has no POs, so the app cannot check the sum.
- vendor bill · blocks · u_controller: D5 I did not trust the match totals either. Confirm would have linked WW $33,500 to an approval nobody gave, and the dumpster $1,650 was offered against estimate line EST-2026-014, which is a price to the client and not a c
- vendor bill · blocks · u_controller: D6 1) Load the existing POs into Purchasing and let the bill link to the PO line, so a three-way match is possible and a bill over the PO stops at the PO.
- vendor bill · blocks · u_controller: D6 2) Put the PM's approve or dispute decision, the approved amount and who approved it on the bill and on every match, not a bare status word.
- vendor bill · annoys · u_controller: D6 4) Flag a payment within N days of a vendor bank change and block it without a W-9. Keep the draft bill when the session ends. Never offer an estimate line as a match target. Separate "enter bill from payment (paid befor
- vendor bill · slows · u_controller: D8 All of it came from the vendor's PDF (files/u_controller/Carlos-Millwork-Invoice-CM-0102.pdf): "parlor kitchen/laundry millwork, progress billing against PO-2026-048, lumber and veneer purchased, carcasses cut, nothing d
- vendor bill · slows · u_controller: D9 The PO line should have filled cost code 10 Millwork & countertops, the job (121 State), the vendor and the remaining PO balance. I was left deciding Materials vs Subcontractors by hand.

## Synthesis, per document type: time and taps against the target, back-end gaps, client-view issues ranked, top fixes

Sources: the tables above, docs_usage.json (14 documents), the answers in workshop/docs_*.md (u_alan, u_chen, u_angel, u_billing, u_controller, client, brand_u_owner, brand_u_sarah) and the client gallery. S1 means money or a report is wrong; S2 means a standard is missed or the record is incomplete with no wrong number yet. One caveat first: the client reader saw INV-039 (Rivera) and INV-041 (Jessop) because the gallery shows every document to the Klein reader. Neither is on the Klein portal. Treat the "cross-client leak" as a workshop artifact until the send path is checked, and check it before the next round.

### Estimate (target: on the phone in under 10 minutes)
- **Time and taps.** EST-2026-015: 12 taps, 55 s, 20 actions over 8 screens on the phone, against 25 taps and 10 minutes. That meets the target on paper, but no estimate was made. Billing > Estimates has no New Estimate, so Alan duplicated the $485,000 contract (EST-014) and spent the turn removing 2 of 13 lines, one tap per round trip, because Remove line renumbers the controls. Nothing was priced or sent. **Target missed.**
- **Back end.** The referee found no gap by field, but the draft holds a $416,000 total with Klein's name on it that is the contract minus two lines, one tap from being sent (S1 if sent). Nothing marks it as a revision of EST-014 or an add.
- **Client view, ranked.** (1) Blocks, all three readers: a second $416,000 estimate on a job contracted at $485,000 and 54% billed, with demo and framing gone; the client asks whether the contract is being replaced. (2) Blocks: "20% deposit" with no dollar amount reads as a second $83,200 deposit. (3) Blocks, client and owner: "Scope, allowances & exclusions" lists no exclusions; five lines have no description. (4) Slows: allowances with no overage rule, $9,500 fixtures looks low. (5) Slows: one landmark note only ("LPC-compliant profiles"). (6) Annoys: takeoff shorthand ("LVP garden", "3rd fl", "ls").
- **Typed versus filled.** 0 fields typed, 0 filled, 11 lines cloned, 0 characters, because the line Alan came to write (parlor floor refinish) was never reached. A library would have filled it: hardwood floor refinish, description (sand, stain, 3 coats, protection, furniture moves), unit sf, price and cost per sf, cost code Finish flooring, standard exclusions attached. The five blank descriptions are the same gap.
- **Top three fixes.**
  1. New Estimate on Billing > Estimates and on the project: blank, from a template or from library items. On a contracted job it opens as a revision of the contract or a change order, shows the delta and names what it replaces. Never Duplicate of the contract by default.
  2. Estimate editor: multi-select remove, and controls that keep their place after a remove.
  3. Estimate print: a standard inclusions and exclusions block, the deposit in dollars, a description on every line, and a one-tap request to the foreman for measurements that lands back on the line.

### Change order (target: on the phone in under 2 minutes and about 12 taps)
- **Time and taps.** CO-003 on the phone: 12 taps and 53 s, on target, but 30 actions over 8 screens (Tasks, Projects, Today, Costs, Billing), about 10 of them hunting for change orders. Alan ran out before pricing and sent it the next morning, inside 48 h by one day. CO-004 at the desk: 4 taps, 32 s, 13 actions over 5 screens (Field, Ask, Billing). **Taps met; the real elapsed time was overnight.**
- **Back end.** CO-004: **link to the estimate line or scope it changes** is missing (S1). Alan ticked the Framing line but no link saved, so the $780 cannot reach that line's budget, job cost or the contract total. Projects shows the contract at $493,050 against $485,000 with nothing tying the COs to the difference (S1, report). No CO owed or 48 h clock showed on Home or Billing; CO-003 sat at $0 overnight (S2).
- **Client view, ranked.** (1) Slows, all three readers: CO-004's line is titled by the cost code ("Framing, blocking & rough carpentry"), not the change. (2) Slows, client and owner: CO-004 bills a code-required guard on a job we designed; the client asks why the drawings missed it. Owner says hold it; this is a decision for Alan. (3) Slows, client and designer: schedule impact shows on 003 but not 004. (4) Annoys, client and designer: "Terms: Net 15" on a change order; pay on signing or on the next pay application? (5) Annoys: "via Angel, on site" is internal; "1 ls"; no word on patch and paint; why one outlet adds a working day. Keep: the portal card with View, Ask and Approve (owner and designer); make Approve the primary button above the fold (client).
- **Typed versus filled.** 11 fields typed, 233 characters into lines (116 per line), 7 picks, 3 filled; about 650 characters typed across both COs counting title, reason and internal notes. CO-003 typed 7 of 7 fields, including project, client and task that the job already knew. CO-004 retyped 146 characters already in Angel's Field question. A library would have filled both lines: GFI receptacle, add (ea, $285 price, $170 cost, Rough electrical, SD Electric) and guard extension to 42 in (lf, price and cost per lf, code reference, Framing). Both prices came from Alan's head.
- **Top three fixes.**
  1. New Change Order on the project page and on a Field question, carrying project, client, task, description, cause date and the estimate line; an unsent or unpriced CO shows on Home and Billing with the 48 h clock.
  2. CO editor: the line it changes saves as a real link, and Projects shows the contract total as estimate plus each CO, reconciled.
  3. CO print and portal: the change is the line title, the cost code stays internal, schedule impact always prints ("none" if none), and Net 15 becomes "billed on the next pay application".

### Invoice
- **Time and taps.** INV-039 2 taps, 14 s; INV-041 3 taps, 13 s; median 2.5 taps against 8, both built from the Billing Queue row. **Target met.** The time went to hunting across the assistant's list and the Billing table, which each hold part of what Billing owes.
- **Back end.** **Cost code on every line** is missing on INV-039 and INV-041 (S1: revenue by cost code is wrong), although Billing believed both carried one, so the screen does not show it. Bill-to address is blank on both (S2). INV-039 bills 40% of Construction administration and of Filing at filing; check the fee-schedule rule (S1 if the milestone is wrong). Next to it: Rivera's $5,000 and $16,350 were recorded but never reached Chase, and the payment cannot be reversed, so AR is overstated by $21,350 and August cannot close (S1).
- **Client view, ranked.** (1) Blocks, designer: INV-041 prints "Sarah Davis — Architect"; she is a designer, and Architect is a licensed title in New York. (2) Slows, owner and client: no way to pay is printed (no ACH, check payee, pay link or remit-to). (3) Slows, all three: INV-041 is a name and 19.5 hr with no tasks; INV-039 reads "40% of phase" on every phase. (4) Annoys, client and owner: the retainage and CO footer prints on design-fee invoices. (5) Annoys: no letterhead, dates with no year.
- **Typed versus filled.** 0 typed, 2 filled, 6 lines; the queue built every line. Billing says a library is not what was missing. What should fill is the role title from the staff record and the tasks behind the hours from the timesheet.
- **Top three fixes.**
  1. Send step on every invoice: refuse to send without a cost code on every line and a bill-to address; print the role title from the staff record.
  2. Invoice print: pay instructions on every invoice, footer terms that fit the document type, hourly lines listing the tasks behind the hours.
  3. Accounting > Payments: Reverse and Void on a recorded payment, with a required reason and a linked reversal showing who, when and why.

### Pay application
- **Time and taps.** INV-040 5 taps, 17 s; INV-042 3 taps, 21 s; INV-043 6 taps, 19 s; median 5 against 10. **Taps met; the real time was a day.** Billing held INV-040 overnight to untangle the Windows line from a separate $13,970 stored-materials queue row; INV-042 was a $0 draft saved the moment New Progress Invoice was tapped.
- **Back end, all S1.** (a) INV-040 saved 14 lines with this period's % below the previous (15 lines across 040 and 042) with no warning. (b) INV-043 billed CO-002 at 100% against 0% measured ($1,850). (c) INV-042 has a $0 total, and its "previous applications" ($251,066) already counts INV-043, numbered after it ($249,401 on 043). (d) "Less retainage (10%)" while retainage to date is $16,933, 6.4% of $266,335. (e) The job is $143,593 over-billed against about 14% measured. (f) Stored materials sit apart from the Windows line, so the same windows can be billed twice.
- **Client view, ranked.** (1) Blocks, all three: certified 54.39% next to 15% measured on the portal; every line "Previously 51.67%", including demo and windows the portal shows as upcoming. "This is my first call to Alan." (2) Blocks, all three: "4 lines fell back to cost — check them before sending" and crew notes print to the client. (3) Blocks, all three: three pay apps in two days, one of them $0, against "progress billing monthly". (4) Blocks, client and owner: previous applications out of issue order. (5) Blocks, all three: two totals blocks, Balance to finish between them, and a retainage label that does not match. (6) Blocks, client: "Invoices Due $81,316" on the portal against $13,051 received; no Pay button; 042 and 043 cannot be opened on the portal. (7) Slows: lines name the trade, not what was done; CO numbers lead the line names.
- **Typed versus filled.** 1 field typed (3 characters, this period's % on 043), 16 lines, 0 filled at save; lines come from the schedule of values and CO titles. A library is not the gap. What is missing is the measured % and who measured it on every line, CO lines included, and stored materials on the SOV line they belong to.
- **Top three fixes.**
  1. Billing > Progress Billing: stop on billed % above measured %, or on a % below the previous period, with the measured % and who measured it on every line.
  2. One pay application per project per period with CO lines inside it; no $0 draft on New Progress Invoice; previous applications computed in issue order; stored materials on their SOV line.
  3. Pay application print and portal: one totals block ending in one "Amount due", the true retainage rate, internal notes stripped at send, and certified against measured reconciled, or explained in one sentence with photos, before either reaches the client.

### PO (internal; no client view)
- **Time and taps.** Desktop 3 taps, 33 s against 10; phone 3.5 taps, 30 s against 12. **Met, and meaningless:** Order makes an empty $0 draft in one tap. PO-050 took 51 s over 5 screens looking for a lumber vendor that is not in the list. Three POs sat as $0 vendorless drafts for days.
- **Back end.** **Vendor** and **vendor on file (vendorId)** are missing on all three (S1): the $2,140.50 card purchase at Brooklyn Lumber never reached job cost, and PO-050 has unit price 0. **Estimate-line link** is missing on PO-051 (S1, cost by line). PO-051 also carries "needed by Mon 9/7 for the floor crew" as a line item (S2). No promised-date field: Brooklyn Lumber gave five dates and the Promise Ledger said 0 broken (S2). Draft POs are not on Deliveries, so "Late to Site 0" was false while the studs were a day late (S2).
- **Typed versus filled.** 0 typed, 3 filled, 4 lines. Nothing was typed because there was nothing to type: no vendor, no price. A library with price history would have priced PO-050 (2x4x8 KD stud, ea, last price) and kept Brooklyn Lumber's $2,140.50 for 25 GWB and 6 cement board.
- **Top three fixes.**
  1. Purchasing > Requests, Order: ask "from whom, by when, at what price" in the same step; record a card purchase at a yard that is not a vendor, with the receipt; create a vendor from the PO and request the W-9 and COI there.
  2. Purchasing > Deliveries: draft POs show as "expected, not confirmed", and a $0 or vendorless draft counts as a problem.
  3. PO editor: a promised-date field with Log a Promise after each call or vendor mail, and the last price filled from history.

### RFQ (internal; no client view)
- **Time and taps.** RFQ-001: 4 taps, 28 s against 12. **Met.** Then it stopped: the line is "1 ls", so it went to Angel for count, sizes and swing, and nothing goes to vendors until he answers.
- **Back end (S2).** **Three vendors asked** and **quotes due date** are missing; the RFQ is over $2,500 and the list has one door and millwork vendor (Carlos Millwork). No budget on the line to compare quotes against (S2, S1 once a quote is accepted blind).
- **Typed versus filled.** 0 typed, 2 filled out of 27 fields on the form. A library would replace the 1 ls line with interior prehung door (ea) and door hardware set (ea), with size and swing as fields, so vendors price units.
- **Top three fixes.**
  1. RFQ editor: carry quantity and unit from the estimate line, and ask for them when the line is a lump sum, splitting it into library units.
  2. RFQ editor: suggest vendors by trade, add a vendor from the RFQ, and refuse to send over $2,500 without three vendors and a due date.
  3. RFQ: show the line's budget beside each quote.

### Bill (target: under a minute; internal)
- **Time and taps.** CM-0102 ($19,000) was never saved. The controller typed vendor, invoice number and project, ran out of actions, and the draft was lost; it was still not entered on 9/8. **Target missed.** The time went to finding PO-2026-048: Purchasing shows "No purchase orders yet".
- **Back end, all S1.** No PO to link, so $57,000 is billed against a PO nobody can see (CM-0091 $38,000 paid with nothing received). Banking shows WW-2026-118 "pm-approved" at $33,500 while Alan approved $29,700 and disputed $3,800 in mail. The dumpster $1,650 was offered against an estimate line, a client price, not a cost. Window Works changed bank details 8/20, has no W-9 and was paid before approval, and the bill shows none of it.
- **Typed versus filled.** 3 fields typed (vendor, invoice number, project), every one on the attached PDF; amount, date, terms and due date were next and also on the PDF. A library is not the fix. The PO line should fill cost code 10, the job, the vendor and the remaining PO balance.
- **Top three fixes.**
  1. Purchasing: load the existing POs and let New Vendor Bill link to a PO line, so three-way match runs and a bill over the PO stops at the PO.
  2. Bill and match screens: the PM's approve or dispute decision, approved amount and approver on the record; never offer an estimate line as a match target.
  3. New Vendor Bill: fill from the attached PDF, keep the draft when the session ends, and flag a payment within N days of a bank change or without a W-9.

### Material request (target: under 30 seconds and 5 taps)
- **Time and taps.** Angel on the phone: 6 taps, 59 s, 14 actions over 4 screens (stale screen, Today, Site, Requests). **Missed on both, roughly double the time.** The form was quick; getting to it was not, and one action went to deleting a junk line the parser made from "needed by Mon 9/7 for the floor crew". Chen at the desk: 6 taps, 30 s, via a detour through Home > Vendors.
- **Back end.** **The task it is for (cost line)** is missing on both requests (S2; S1 once it becomes a PO), although Angel believed it filled. The field's card purchase and the vendor mail never reached the GWB request, so Chen traced an order already paid (S1 through the PO). Angel asked for 4 tape; Chen's mail says 6, and the app shows no change (S2). 9/7 is Labor Day and nothing flagged it (S2).
- **Typed versus filled.** 2 fields typed (79 characters of items and quantities, 10 of a third line), 1 pick (the date), 6 filled; on Angel's form 9 of 11 filled and 6 defaulted. Job, deliver-to and Chen were known; the task was known from Today. A library would make it two picks: blue tape and rosin paper, unit roll, usual quantity per floor, last vendor and price, floor-protection cost code. A Floor Protection kit (rosin, tape, Ram Board, corner guards) on the flooring task would make it one pick, as the Demo kit already does.
- **Top three fixes.**
  1. Request Material on Today and on the task, with job, task, cost line and deliver-to filled.
  2. Request form: needed-by is a date pick that warns on holidays and weekends; no free text parsed into lines; the card reads back exactly what will be sent.
  3. Request card: who acknowledged it, PO, vendor, ship date and any quantity change; "bought on card, vendor X, receipt" closes it; unacknowledged after 4 h goes to Chen and Alan on its own.

### What this means for BACKLOG 1.18 (the item library)
Typing is concentrated in change orders (116 characters per line, every price from memory) and material requests; the estimate would have been the same had Alan reached the line. Invoices and pay applications fill from the queue and the schedule of values, and the bill fills from the PO and the PDF; a library does not help them. Each item needs: client-facing name and description, unit spelled out for print ("lump sum", not "ls"), price, cost, cost code, entity (SD Electric, SD Plumbing), standard exclusions, usual quantity rule, last vendor and price history fed by POs and bills, and kits (Floor Protection, Demo). First items, from this round: GFI receptacle add, guard extension to 42 in, hardwood floor refinish, prehung interior door, door hardware set, 2x4x8 KD stud, GWB 1/2 4x8, cement board, rosin paper, blue tape.

### The five fixes that matter most to Alan, in order
1. **Progress billing tells the truth** (Billing > Progress Billing): one pay app per project per period with CO lines inside; stop when billed exceeds measured or a % goes backwards; no $0 apps; previous applications in issue order; one Amount due; certified and measured reconciled before the portal shows either. This is $143,593 billed ahead and the Kleins' first call.
2. **A send gate on every client document** (the send step on estimates, COs, invoices, pay apps): strip internal notes and fail on "check before sending"; require a cost code on every line, a bill-to address and true staff titles; print pay instructions, footer terms by document type, full dates and plain units on one SmartDesign letterhead.
3. **Every record carries its line link** (CO editor, Purchasing, New Vendor Bill): a CO saves the estimate line it changes and the contract total reconciles; a PO has a vendor, a price and its estimate line, and card purchases count; existing POs are loaded so bills match PO lines and stop at the PO, with the PM's approved amount on the bill.
4. **Start each document where the work is** (Billing > Estimates, the project, Field, Today): New Estimate that is blank, from a template or a revision of the contract, never a clone; New Change Order from the project and the Field question, with the 48 h clock on Home; Request Material on Today and on the task.
5. **The item library with kits and price history** (BACKLOG 1.18), filling CO, estimate, RFQ, PO and request lines with description, unit, price, cost and cost code, so nobody types or remembers a price the firm already paid.

Waiting on Alan: whether the code-required guard on CO-004 ($780) is ours to absorb.

