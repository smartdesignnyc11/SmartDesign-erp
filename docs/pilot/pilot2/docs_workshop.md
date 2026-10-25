# Documents Workshop: pilot2

Measured by the harness, back end checked by the referee, client view judged by the client agent, the owner and the designer. Everything above "Synthesis" is mechanical.

## Measured, per document type

| Type | Device | Made | Median taps | Target taps | Median seconds | Screens | Typed / filled | Validation stops | Not found after save | Back-end gaps |
|---|---|---|---|---|---|---|---|---|---|---|
| PO | phone | 1 | 3 | 12 | 22 | 8 actions, 5 screens | 0 / 1 | 0 | 0 | none |
| RFQ | desktop | 1 | 5 | 12 | 37 | 14 actions, 4 screens | 0 / 2 | 0 | 0 | quotes due date; three vendors asked |
| bill | desktop | 2 | 3.0 | 6 | 56.0 | 16.0 actions, 3.5 screens | 11 / 12 | 0 | 0 | PO link (three-way match); cost code; due date; estimate-line link; terms |
| bill | phone | 1 | 3 |  | 71 | 8 actions, 2 screens | 0 / 0 | 0 | 0 | PO link (three-way match); cost code; estimate-line link; terms |
| change order | desktop | 1 | 4 | 10 | 56 | 13 actions, 4 screens | 2 / 6 | 0 | 0 | none |
| change order | phone | 1 | 7 | 12 | 32 | 15 actions, 6 screens | 4 / 5 | 0 | 0 | none |
| estimate | desktop | 1 | 5 | 20 | 36 | 13 actions, 5 screens | 2 / 0 | 0 | 0 | job (projectId) |
| estimate | phone | 1 | 11 | 25 | 49 | 20 actions, 7 screens | 0 / 1 | 0 | 0 | a price on every line; a total above zero; cost code on every line |
| invoice | desktop | 3 | 3 | 8 | 21 | 8 actions, 4 screens | 0 / 1 | 0 | 0 | cost code on every line; the record is gone |
| invoice | phone | 1 | 4 |  | 39 | 9 actions, 4 screens | 0 / 0 | 0 | 0 | the record is gone |
| material request | desktop | 1 | 4 |  | 24 | 11 actions, 2 screens | 0 / 0 | 0 | 0 | the task it is for (cost line) |
| material request | phone | 1 | 6 | 5 | 46 | 21 actions, 4 screens | 4 / 9 | 0 | 0 | the task it is for (cost line) |
| pay application | desktop | 1 | 2 | 10 | 23 | 7 actions, 4 screens | 0 / 0 | 0 | 0 | none |

## Typed versus filled, per document type (the item library question, BACKLOG 1.18)

| Type | Documents | Lines | Fields typed | Characters typed into lines | Per line | Picked from a list | Filled, not typed (at save) |
|---|---|---|---|---|---|---|---|
| PO | 1 | 1 | 6 | 0 | 0 | 4 | 1 |
| RFQ | 1 | 1 | 0 | 0 | 0 | 0 | 2 |
| bill | 3 | 3 | 7 | 103 | 34 | 4 | 1 |
| change order | 2 | 2 | 15 | 291 | 146 | 1 | 5 |
| estimate | 2 | 4 | 2 | 23 | 6 | 2 | 1 |
| invoice | 4 | 5 | 1 | 151 | 30 | 0 | 1 |
| material request | 2 | 0 | 5 | 0 | - | 0 | 4 |
| pay application | 1 | 14 | 0 | 0 | 0 | 0 | 0 |

Line descriptions as written (estimate, change order, invoice):
- change order CO-2026-003: GFI outlet, pantry wall — Supply and install one GFI outlet in the pantry wall, tied to the nearest circuit, with box, cover plate and testing
- invoice INV-2026-039: Schematic design — 40% of phase
- invoice INV-2026-039: Design development — 40% of phase
- invoice INV-2026-039: Construction documents — 40% of phase
- invoice INV-2026-039: Filing & permits — 40% of phase
- invoice INV-2026-039: Construction administration — 40% of phase
- estimate EST-2026-015: Kitchen renovation — Full gut and rebuild of the kitchen: demolition, framing, plumbing and electrical by SD Plumbing and SD Electric, custom cabinetry, stone counters, tile backspl
- estimate EST-2026-015: Powder room — New powder room: rough plumbing and electrical, vanity, toilet, fixtures, tile floor and walls, lighting, paint
- estimate EST-2026-015: Parlor floors — Parlor floor: sand, repair and finish existing hardwood, two coats satin polyurethane, protection of adjoining rooms
- pay application INV-2026-040: Demolition & disposal
- pay application INV-2026-040: Framing, blocking & rough carpentry — measured by foreman update 9/2 — Framing & blocking – 3rd floor 90%; 1 running task still on elapsed time
- pay application INV-2026-040: Windows — front & rear façade
- pay application INV-2026-040: Plumbing — rough & finish
- pay application INV-2026-040: Electrical — rough & finish — measured by PM update 9/1 — Rough electrical 55%
- pay application INV-2026-040: Insulation, drywall, taping & prime
- pay application INV-2026-040: Tile — two baths
- pay application INV-2026-040: Flooring
- estimate EST-2026-016: 
- change order CO-2026-004: Stair landing guard to 42 in (code) — Raise stair landing guard to 42 inches per code: new posts and rail, finish to match. Angel asked 9/8.

## Back end, every gap by field (from the referee's audit)

- bill: **terms** (3: CM-0102, SE-0922, PAY-260902)
- invoice: **the record is gone** (3: INV-2026-041, INV-2026-042, INV-2026-043)
- material request: **the task it is for (cost line)** (2: GWB and cement board, 2 items)
- bill: **cost code** (2: SE-0922, PAY-260902)
- bill: **PO link (three-way match)** (2: SE-0922, PAY-260902)
- bill: **estimate-line link** (2: SE-0922, PAY-260902)
- invoice: **cost code on every line** (1: INV-2026-039)
- estimate: **job (projectId)** (1: EST-2026-015)
- estimate: **a total above zero** (1: EST-2026-016)
- estimate: **cost code on every line** (1: EST-2026-016)
- estimate: **a price on every line** (1: EST-2026-016)
- RFQ: **three vendors asked** (1: RFQ-2026-001)
- RFQ: **quotes due date** (1: RFQ-2026-001)
- bill: **due date** (1: SE-0922)

## Client view (client, owner, designer), grouped by document type, worst first

- all docs · blocks · brand_u_owner: One template for EST, CO, INV and pay app: SmartDesign wordmark and logo, address, phone, licence, a one-roof tagline, the year on every date, and per-document footers. Right now the retainage/CO boilerplate prints on a 
- all docs · blocks · brand_u_owner: Strip internal fields from client output by class, not by line: foreman/PM evidence notes, "check before sending", names like "Angel asked". Add a send-gate check that fails if any internal note, $0 total or empty line w
- all invoices · slows · brand_u_owner: Nowhere does it say how to pay: no ACH details, no pay link, no remit-to, no "questions, call Alan". The client has to call to ask, which our standard says should never happen. Due dates land on a Saturday (Sep 19).
- all print docs · blocks · brand_u_sarah: Strip every internal note, staff name and evidence trail from client output by rule (client-facing field vs internal field), not per document; add a check that fails a print containing "check them before", "fell back", "
- all print docs · annoys · brand_u_owner: Not us yet. The header says "SmartDesigns" (we are SmartDesign) in plain bold text, with no logo mark, no office address, phone or licence/HIC number, and no line saying design, SD Plumbing and SD Electric under one roof
- all print docs · annoys · brand_u_sarah: Reads like a generic SaaS template, not a landmark design-build firm: wordmark is plain bold "SmartDesigns" (the firm is SmartDesign), no logo mark, no address, phone, licence, SD Plumbing/SD Electric or Mercer & Bond li
- all print docs · annoys · brand_u_sarah: Same footer boilerplate on every document (retainage, change orders) including a design-fee invoice and a CO, so it reads as filler; units show as "1 ls" and "1 ea", which is our shorthand, not client language.
- all print docs · annoys · brand_u_sarah: One letterhead for every document type: the SmartDesign mark from Settings, firm address, phone, licence numbers, "Design · Build · SD Plumbing · SD Electric", year on every date, units written out ("lump sum", "each"), 
- CO-2026-003 · blocks · client: The portal screen doesn't show CO-2026-003 anywhere. Waiting on You lists CO-2026-004 and the finish choices, so I can't find where to approve this one, or whether I already did.
- CO-2026-003 · slows · client: $420 is clear. "Net 15" on a change order: from when? Is it added to my next pay application or billed now? No retainage note, no how to pay. The footer talks about progress invoices.
- CO-2026-003 · slows · client: "Schedule impact: 1 working day." Which date moves, and does it push the Nov 4 finish? Is wall patching included?
- CO-2026-003 · annoys · client: Plain enough, but nothing says what is excluded. Does it cover patching and painting the wall, and the electrical inspection?
- CO-2026-003 · annoys · client: Clean but generic. "SmartDesigns" in plain text with no logo, firm address, phone or licence. The date has no year ("Thu, Sep 3").
- CO-2026-003 · annoys · client: "GFI" is trade shorthand; say "GFCI (shock-protected) outlet". "1 ea" is fine. Otherwise clear.
- CO-2026-003 · annoys · brand_u_sarah: Good: short, specific, priced, signature lines, schedule impact. Bad: the portal shot does not show CO-2026-003 at all, only CO-2026-004 and decisions, so the client cannot find the CO they are signing next to the one on
- CO-2026-003 · ok · client: Yes: one GFI outlet in the pantry wall, $420.
- CO-2026-003 print · good · brand_u_owner: One clear line, the reason, schedule impact (1 working day), and a signature block. A client understands it in ten seconds. This is the bar for every CO.
- CO-2026-003, CO-2026-004 · slows · brand_u_sarah: Add original contract, prior COs and revised contract sum on every CO, schedule impact on every CO (even "none"), and the reason category (client request, code, existing condition) in client language.
- CO-2026-004 · blocks · client: "If it's a code requirement your drawings missed, why is it a change order to me?" I would call before approving.
- CO-2026-004 · blocks · brand_u_owner: "Guard raised from the drawn height to 42 inches to meet code". We drew it. Charging the client $1,450 to fix our own drawing to meet code goes against "no other contractor to blame". The client will notice that first. A
- CO-2026-004 · slows · client: Plain, but "raised from the drawn height to meet code" tells me your drawing was below code. Why am I paying for the firm's drawing miss? No exclusions given.
- CO-2026-004 · slows · brand_u_sarah: "Stair landing guard raised to 42 inches (code)" at $1,450: the client's first thought is why they pay for our drawing missing code. Needs one plain sentence on why it is a change (existing condition, LPC, or client choi
- CO-2026-004 · annoys · client: $1,450, Net 15, but no word on when it's billed. There's no schedule impact line, though CO-2026-003 had one. No how to pay.
- CO-2026-004 · annoys · client: Clean, but "Angel asked 9/8" is an internal note in the line description. The same plain header without year, address or licence.
- CO-2026-004 · annoys · client: "Stair landing guard to 42 in (code)" is fine. Drop "Angel asked 9/8" and say what finish "to match" means (stain/paint, which rail).
- CO-2026-004 · annoys · brand_u_owner: "Angel asked 9/8" is an internal note on a client document. CO-2026-003 is clean and plain. The words are right, but both look like a receipt.
- CO-2026-004 · annoys · brand_u_sarah: Description says "Angel asked 9/8": a crew name and internal trigger on a client document. No schedule impact line (CO-2026-003 has one) and no revised contract sum on either CO.
- CO-2026-004 · ok · client: Yes: raise the stair landing guard to 42 in, $1,450.
- CO-2026-004 · ok · client: The portal shows it in Waiting on You with $1,450 and an Approve button: 1 tap from Overview (2 with a confirmation). Approve is outlined while "Choose" above is blue, so it's easy to miss.
- COs · slows · brand_u_owner: Add the original contract, prior COs and new contract sum to every CO. Use a reason type (client request / code / unforeseen / design). A design-or-code miss on our drawings routes to me before it is priced to the client
- EST-2026-015 · blocks · client: Not mine (Nadia Okoro, 88 Garfield Pl). As theirs: three lump sums totalling $210,000, clear at the headline level.
- EST-2026-015 · blocks · client: Not on the portal, so there's no way to accept it from a phone. It's print-and-sign only.
- EST-2026-015 · slows · client: Inclusions are decent. No exclusions or allowances: who supplies the appliances, cabinet, stone and tile allowances, permits/DOB/LPC, design fee, haul-away.
- EST-2026-015 · slows · client: "Net 15" on a $210k proposal with no deposit or payment schedule. The footer mentions retainage but gives no rate. Contrast EST-2026-016, which says deposit at signing.
- EST-2026-015 · slows · client: "$40,000 to sand and refinish the parlor floor?" No timeline. "Are appliances in the $128k?"
- EST-2026-015 · slows · brand_u_sarah: Project title repeats itself ("88 Garfield Place, Park Slope — Design-build — proposal" in bold, then again below); line descriptions are good and specific, the voice is right there. Terms "Net 15" on an estimate with no
- EST-2026-015 · annoys · client: The project title "88 Garfield Place, Park Slope — Design-build — proposal" is printed three times. For a $210k proposal there are no drawings reference, no timeline and no company credentials.
- EST-2026-015 · annoys · client: Descriptions are professional. The "Parlor floors" line needs square footage and species. "1 ls" is jargon.
- EST-2026-015 · annoys · brand_u_owner: The line descriptions are in our voice (gut and rebuild, SD Plumbing and SD Electric, satin poly, protection of adjoining rooms). The rest is weak: the project line repeats "88 Garfield Place, Park Slope — Design-build —
- EST-2026-016 · blocks · client: Nothing. One blank line at $0, total $0, and the project is called "Proposal". An empty estimate was sent to me.
- EST-2026-016 · blocks · client: No scope at all, and I'm asked to sign that "the client agrees to the scope, pricing and payment schedule".
- EST-2026-016 · blocks · client: A blank $0 estimate with a signature line looks careless. Its layout also differs from the other documents (Description/Rate/Qty against Item/Qty/Rate).
- EST-2026-016 · blocks · client: "What is this? Did you mean to send me something?"
- EST-2026-016 · blocks · client: Line 1 has no description at all.
- EST-2026-016 · blocks · brand_u_owner: It uses a second template: bigger name, Description/Rate/Qty instead of Item/Qty/Rate, "Client signature" instead of "Accepted by (client)", and "net 7" in the terms while the footer says 15 days. Two looks and two sets 
- EST-2026-016 · blocks · brand_u_owner: A $0 estimate with an empty line "1." and a project called "Proposal" can be printed and signed. A client who received this would think we are not serious.
- EST-2026-016 · blocks · brand_u_sarah: Different template from EST-2026-015 (bigger wordmark, Rate before Qty, "Description" not "Item", boxed Billing note) and it is empty: one blank line at $0, project called "Proposal". Two terms that disagree on one page:
- EST-2026-016 · blocks · brand_u_sarah: A $0 estimate with a blank line and a signature block; if it went out it says we are careless with the one document that sells the job.
- EST-2026-016 · blocks · brand_u_sarah: Block print/send of an estimate with a $0 total, an empty line or a project titled "Proposal"; move it onto the same template as EST-2026-015 and reconcile its terms (one term, stated once).
- EST-2026-016 · slows · client: Terms contradict: "progress invoices net 7" against the footer "due within 15 days". No deposit amount and no retainage rate.
- EST-2026-016 · slows · client: Not on the portal, so I can't sign from a phone; just as well, since it's empty.
- estimates · slows · brand_u_owner: A proposal for $210k needs more than three prices: the inclusions, exclusions and allowances, LPC/DOB permits, the schedule, the payment schedule (deposit and progress) instead of "Net 15", and our one-roof promise. Bloc
- INV-2026-039 · blocks · client: Not my invoice (Rivera family, 45 Cranberry St). Read as theirs: five phases each billed at "40% of phase", including Construction administration before construction has started. That is unclear.
- INV-2026-039 · blocks · client: Not on the portal, so it can't be paid from a phone. Zero taps available; I'd have to call or mail a cheque.
- INV-2026-039 · slows · client: No phase totals, no fee to date, and nothing saying what "filing / submission" delivered to earn 40%.
- INV-2026-039 · slows · client: $17,080 due Sep 18, Net 15. No previous billing, no remaining balance, no how to pay. The retainage and change-order footer doesn't apply to a design invoice. The Bill to address line is blank.
- INV-2026-039 · slows · client: "Why am I paying 40% of construction administration now?" "What is my total design fee and what's left?"
- INV-2026-039 · slows · brand_u_sarah: Bill to "Rivera family" with a blank address line; every phase including construction administration billed at "40% of phase" at filing, which a client will question; the "At filing / submission — 40% of design fee" line
- INV-2026-039 · slows · brand_u_sarah: Fill the bill-to address from the client record; add a fee schedule summary (total design fee, billed to date, this invoice, remaining) so "40% of phase" makes sense.
- INV-2026-039 · annoys · client: Same plain template. The blank address line under "Rivera family" looks unfinished.
- INV-2026-039 · annoys · client: "40% of phase" repeats on every line and says nothing. "1 ls" is jargon. The line names themselves are fine.
- INV-2026-039 · annoys · brand_u_owner: 40% of Construction administration billed at filing, before construction starts. The client will ask why. "Bill to Rivera family" has a blank address line.
- INV-2026-040 · blocks · client: No. Every line shows "Previously 51.67%", even lines barely started. The total says 53.97% completed, yet the portal says 15% of the work is complete on site. I can't tell what I'm paying for.
- INV-2026-040 · blocks · client: The Notes are internal and sent to me: "5 lines fell back to cost — check them before sending" and "12 lines measure below what was already billed". It reads like a draft, not a premium firm.
- INV-2026-040 · blocks · client: I'd call at once. Have I been overbilled on 12 lines? Why is billing 39 points ahead of the work? The portal tile says Invoices Due $79,651 but this invoice is $11,386; what is the rest?
- INV-2026-040 · blocks · brand_u_owner: Internal working notes print on the client's pay application: "1 running task still on elapsed time", "5 lines fell back to cost — check them before sending", "measured by foreman update 9/2". That is the PM's checklist,
- INV-2026-040 · blocks · brand_u_owner: Money: approved COs add $8,470 but only CO-2026-001 ($6,200) is on the schedule of values. $2,270 of approved change work has no line to bill against, so it is work done and never billed.
- INV-2026-040 · blocks · brand_u_owner: Hold this application until I decide. Reconcile the 12 over-billed lines (credit with a reason or hold), put every approved CO on the SOV, show one total, show retainage consistently, and add AIA G703 columns ($ previous
- INV-2026-040 · blocks · brand_u_sarah: Internal working notes printed to the client: "5 lines fell back to cost — check them before sending", "12 lines measure below what was already billed ... A correction is a credit with a reason, approved", and "measured 
- INV-2026-040 · blocks · brand_u_sarah: First thing the Kleins see: every line "Previously 51.67%", the note saying billing is ahead of measured work, and on the portal "Billed to Date $266,335 · 54% ... 15% of the work complete on site ... ahead by 39 points"
- INV-2026-040 · blocks · brand_u_sarah: Hold it until the PM confirms the 51.67% previously column and the 54% billed vs 15% on site gap; show the AIA summary once (drop the duplicate subtotal block) and explain the deposit credit in the client's words on the 
- INV-2026-040 · slows · client: The line names are plain, but there's no scope text. Net change by change orders is $8,470, yet only CO-2026-001 ($6,200) appears as a line. Where is the other $2,270?
- INV-2026-040 · slows · client: Two totals blocks ("Current payment due" and "Total this invoice", both $11,386). "Subtotal" sits under "Balance to finish". Retainage says 10%, but retainage to date is $16,933 on $266,335 (6.4%). No how to pay. It is d
- INV-2026-040 · slows · client: The portal capture shows the Overview with the billed-to-date story but no Pay button. It's at least 2+ taps through Account, and I can't see a pay option at all.
- INV-2026-040 · slows · client: Line 2 "measured by foreman update 9/2 … 1 running task still on elapsed time" and line 5 "measured by PM update 9/1" are internal notes. Lines 1-13 are fine as names.
- INV-2026-040 · annoys · brand_u_owner: Every line shows "Previously 51.67%" across the board, so it looks billed by formula, not by work. Two totals stack ($11,386 Current payment due, then $11,386 Total this invoice). Retainage reads 10% this period but work
- INV-2026-040 print + portal · blocks · brand_u_owner: The client sees that we billed 54% while only 15% of the work is done, and that 12 lines are "below what was already billed". Our own document tells them we overbilled. The portal says "19 are progress billed ahead of wh
- portal · annoys · brand_u_owner: Lead with progress and photos, not dollars owed. One Approve button per CO with View as a link. Neutral wording on decisions ("needed by 9/10 to keep plumbing on schedule"), not red. Fix the clipped captions.
- portal · annoys · brand_u_sarah: Header says "Garden unit + 3rd floor · Brooklyn, NY" while every printed document says "121 State Street"; "Your project manager: Alan" with no surname; photo captions cut off mid-word.
- portal · annoys · brand_u_sarah: Red "as soon as you can ... holding the schedule" text and a red Waiting on You 7 badge greet the client; feels like we are pushing them, not guiding them. Invoices Due $79,651 sits beside it with no breakdown.
- portal · annoys · brand_u_sarah: Use the same project name as the documents, give the PM's full name, show the CO or invoice the client was sent at the top of Waiting on You, use calm wording with a date instead of red urgency.
- portal (CO-2026-003 / -004 / INV-2026-040) · annoys · brand_u_owner: The first thing on screen is "Invoices Due $79,651" next to a red "Waiting on You 7". Red text "holding the schedule" pressures the client. CO-2026-003 does not appear on the captured screen at all. Each item has three s

## Creators, by document type, phone

- PO · slows · u_chen: D1 3 taps and 22s is the creation tap only; my turn spent 24 actions: 6 finding the request (Today, Buy Board, then Purchasing > Requests), 3 linking the estimate line, 3 creating the vendor, and the PO still ended a $0 dra
- PO · blocks · u_chen: D2 The estimate line (picked by reading a sheet of every line), the vendor (5-field new vendor sheet), the quote number 88412 and the 100% deposit terms. The request knew the job and the item, and mail 10 knew the vendor, o
- PO · blocks · u_chen: D3 The Payment Terms "Custom..." pick opened a sheet its label did not name, and that sheet covered the Sales Tax field, so my save stopped and the terms were lost with no unsaved warning.
- PO · slows · u_chen: D3 The estimate-line Link sheet is a long unsearched list on a small screen; the Purchase Orders table needs sideways scrolling to reach Match; the assistant was not on my phone screen at all.
- PO · blocks · u_chen: D4 The card charge the PO should match, the vendor's W-9/COI status before I started (the PO can't be issued without them), and the pickup date, which should have gone red on Deliveries when nobody picked up 9/4.
- PO · blocks · u_chen: D5 No. The PO shows $0 ("Not Issued 1 · $0") because the price was never filled, while the card already paid $2,140.50. Sales Tax defaulted to "No tax (labor/service)" for boards, which is wrong for materials. The harness s
- PO · blocks · u_chen: D6 First: a PO from a request carries the estimate line, item, qty and the matching card charge or vendor mail, with tax set from the item type (materials taxed). Second: a "Record a purchase already paid" path that ties to
- PO · slows · u_chen: D6 Third: no hidden sheets behind dropdown picks, and warn before leaving an unsaved sheet. Fourth: search on the Link sheet, best match first.
- PO · slows · u_chen: D8 The quote number, order, quantities (25 GWB + 6 cement board) and amount came from Brooklyn Lumber's 9/1 mail; I retyped from my reading of the mail.
- PO · blocks · u_chen: D9 GWB 1/2" and cement board: item, description, unit, last price from Brooklyn Lumber, cost code 07 and "materials, taxable". All known before; none filled.
- PO · annoys · u_chen: D10 The phone was fine for Order from a request (1 tap, toast, Open) and new vendor; the desktop is clearer for the PO table and tiles. The phone should copy the desktop's full PO view without sideways scroll; both need the 
- bill · blocks · u_controller: D1 PAY-260902: 3 taps and 71s, and I never meant to make this bill. Confirm on the Satish 9/2 ACH match card created it next to SE-0922; the time went to opening the row and reading a card that wrongly said "no bill on file
- bill · annoys · u_controller: D2 PAY-260902: I typed nothing. The system used a made-up number (PAY-260902) in place of the vendor's real invoice SE-0922, which was already on file.
- bill · blocks · u_controller: D3 The match card fits at 390px, but it did not check for an existing bill before Confirm. On a phone I cannot open the desktop Payments table to see that SE-0922 already pays the line, so the phone is where a duplicate get
- bill · annoys · u_controller: D3 Made Today journals fill the first screen of Banking and Bills & Payroll on the phone. The Bills tiles lose their dollar amounts, and on the phone first screen I saw PAY-260902 but not SE-0922.
- bill · blocks · u_controller: D4 PAY-260902: the match card said "no bill on file" when SE-0922 had been posted on Friday. The one fact I needed, that this bank line was already paid by a bill, was the one it did not have.
- bill · blocks · u_controller: D5 PAY-260902: no. Two $7,400 payments cleared by one ACH, both "cleared yes", and ledger cash fell from $180K to $173K. The duplicate toast fired one second after the post. A catch after the save is a reversal for me, not 
- bill · blocks · u_controller: D6 3. "Not this, it duplicates SE-0922" on the match card reverses PAY-260902 with a linked reason in one tap. And a paid-before-approval bill shows in the bills list as "Paid, Unapproved", not only as a Payments row.
- bill · annoys · u_controller: D8 PAY-260902: the payee and amount came from the 9/2 bank line, not from the vendor's invoice. A bill built from a bank line is evidence of payment, not a bill, and should be labelled so.
- bill · blocks · u_controller: D9 PAY-260902: it was coded to Overhead with no cost code, PO or estimate line. A job vendor's ACH should default to that vendor's open PO line and its cost code, never to Overhead.
- bill · annoys · u_controller: D10 Phone Accept All (6 lines, 1 tap) is the right speed, and the desktop bill form should copy it: prefilled from PO and mail, one Post. Desktop Bills & Payroll shows tile dollars ($14K, $41K) and the phone should show them
- change order · slows · u_alan: D1 7 taps and 32s is fair for the form, but the real cost was 8 calls across Projects > project card > Change Orders > form; a $420 pantry outlet should be 3 from Today (Quick Price, amount, Send to Client).
- change order · slows · u_alan: D1 Time went to overwriting the From Estimate line (item, description, unit, rate, cost) and a long scroll past 13 estimate lines to reach Schedule Impact.
- change order · annoys · u_alan: D2 Item, description, unit, rate and cost: I typed all of them over the whole $46,500 electrical description the estimate line dragged in; a GFI outlet add is a stock line with a stock price.
- change order · annoys · u_alan: D2 The Schedule Impact +1 working day on Rough electrical; the system knows an outlet sits in rough electrical and should propose the day.
- change order · slows · u_alan: D3 Control numbers shifted after typing (Send to Client moved 27 to 28) and I nearly tapped the wrong one; Schedule Impact is far below the price on a phone scroll.
- change order · annoys · u_alan: D3 The "no price found for Electrical" warning showed after I had already typed my price, so it read as an error on a correct line.
- change order · slows · u_alan: D4 The cost and margin of similar small electrical adds on past jobs; I priced $420 / $240 from memory.
- change order · annoys · u_alan: D5 I trusted $420 and the 43% margin because I typed both; the line showed $0 with All changes saved until I priced it, which is a total I would not trust if I were not watching.
- change order · blocks · u_alan: D6 A Quick Price change order from Today or from the site question: one line, amount, days, Send to Client, without dragging the original estimate line in.
- change order · slows · u_alan: D6 Put Schedule Impact next to the price, collapse the 13 estimate lines, and run the price check before I type, not after.
- change order · slows · u_alan: D7 Small electrical adds (GFI outlet, extra receptacle, dedicated circuit) with standard labor, material and +1 day on rough electrical.
- change order · annoys · u_alan: D8 None copied; the estimate line description had to be deleted, not reused. Price and margin came from my head.
- change order · slows · u_alan: D9 GFI outlet: item, "Add GFI duplex receptacle, pantry wall", ea, $420, cost $240, electrical cost code, +1 day rough electrical.
- change order · annoys · u_alan: D10 The phone send sheet (To, Subject, Message prefilled, says what Send does) is right; keep it on both.
- estimate · blocks · u_alan: D1 The 11 taps and 49s do not match what I lived: three turns on 9/4 and 9/8 and the page never took a word (Title, Scope, Line, Add Line Item all dead or timed out); the parlor floor price never went to the Kleins.
- estimate · blocks · u_alan: D1 About 12 actions just finding New Estimate (only on the client page, not Projects > Estimates, not in Menu), then 5 taps each time to get back to the draft; the screen path ending on Tasks is the misroute I logged.
- estimate · blocks · u_alan: D2 Nothing filled in, and I could not type either: client and property came from the client page (good), but title, scope, inclusions and exclusions for parlor floor refinishing are the same every time.
- estimate · blocks · u_alan: D3 The estimate page is unusable on the phone: line and Add Line Item report covered and tap through, every text field times out, and it still says All changes saved on a $0 blank draft.
- estimate · blocks · u_alan: D3 No New Estimate on Projects > Estimates, no Estimates in Menu, no Ask on the phone; standing in the client's parlor I had no door to start or price.
- estimate · blocks · u_alan: D4 Where my draft lived: the client page does not list draft estimates, and Made Today did not show it, so I could not find what I had just made.
- estimate · annoys · u_alan: D4 No due time on the estimate: the noon promise to the Kleins was not on the record or on Today, so the app never warned me I missed it twice.
- estimate · blocks · u_alan: D5 No: the harness says a total above zero with a price and cost code on every line, but every time I opened it the draft was $0 and the line count flipped 1 to 0; a save I could not see is not a save I trust.
- estimate · blocks · u_alan: D6 Fix the phone estimate page so it takes a line and a price; then New Estimate on Projects > Estimates, and drafts on the client page and Made Today.
- estimate · annoys · u_alan: D6 Give the estimate a promised-by time that lands on Today and in my assistant's briefing.
- estimate · slows · u_alan: D7 Parlor floor refinish scope: sand, spot repair, stain to match, 3 coats waterborne; exclusions subfloor repair and furniture moving. I write this on every brownstone.
- estimate · annoys · u_alan: D8 The scope was in my head and my diary; I meant to copy it from past parlor floor jobs but had no way to pull an old estimate into this one on the phone.
- estimate · slows · u_alan: D9 Parlor floor refinish per sf: item, the standard scope text, sf, price per sf, flooring cost code, with inclusions and exclusions as the template.
- estimate · blocks · u_alan: D10 I never got the estimate working on either device; desktop could not find it from the client page either. Both need drafts findable where they were made.
- invoice · slows · u_billing: D1 INV-2026-043 took 4 taps and 39s, but I drafted it only to see the lines of the $3,846 application. Alan said no, and deleting it took 4 more taps on the desktop and used up number 043. One Preview tap would have done th
- invoice · slows · u_billing: D1 Before any work, 4 of 12 actions went on news, mail, read and screen. Then the app opened on Tasks, not the queue.
- invoice · annoys · u_billing: D2 My diary doesn't account for the 151 characters typed into lines; I opened it only to look. Whatever went in (evidence or a hold reason) should have come from Angel's log and Alan's mail, not my thumbs.
- invoice · blocks · u_billing: D3 The line table says "Scroll sideways for Amount", and the amount column is cut off at 390px. On an application, the amount is the one number I need.
- invoice · slows · u_billing: D3 Billing and Ask are not on the top bar: 9 to 14 menu controls come before content. The follow-up task I added straight after was filed under 206 Lenox, with "Alan" and "Lenox" stripped from the text.
- invoice · blocks · u_billing: D4 The row went from $3,588 Friday to $3,846 Tuesday with no note of what changed. Framing +9.38% rested on "1 of 2 tasks done", a fallback with no foreman note. No PM hold status was shown.
- invoice · blocks · u_billing: D5 I did not trust it. The one line that moved rested on a task count, not a signed log, and the held lines were still at 51.67% billed ahead. The $3,461 after retainage adds up, but adding up is not the same as being earne
- invoice · blocks · u_billing: D6 1. Preview on the queue row that uses no number. 2. A PM hold ("Alan: no, 9/8") that blocks Send and shows on the row: 043 still had Send after he said delete. 3. One stacked card per line at 390px, with no sideways scro
- invoice · annoys · u_billing: D6 4. Billing and Ask on the phone top bar, and open my seat on the Billing Queue. 5. The task parser keeps the names I typed and files the task on the project I'm billing.
- invoice · annoys · u_billing: D7 None from scratch; the lines came from the SOV.
- invoice · annoys · u_billing: D8 None copied. I checked the line against Alan's 9/8 mail and Angel's site numbers (3rd floor framing 100%, garden bedroom 80%, treads 60%).
- invoice · slows · u_billing: D9 Percent complete should fill from Angel's signed daily log, line names from the SOV and retainage from the contract. Retainage filled; the other two didn't.
- invoice · slows · u_billing: D10 The desktop was faster and clearer for reading and judging lines. The phone is as good for the morning glance (Ready $20K, Sent $121K, Overdue $0 above the fold). The phone should copy the desktop grid as cards, and the 
- material request · slows · u_angel: D1 46s and 6 taps is about right for the sending itself, but 21 actions for 2 items is too many: the time went to getting there (Today > More for Today did nothing new > Site > Requests, one wasted tap) and to fixing the se
- material request · annoys · u_angel: D1 After my first fix the row numbers moved, so my next tap missed and I lost an action; a 2-item request should be sentence, check, Send: 3 taps, under 20s.
- material request · slows · u_angel: D2 I typed 4 of 9 fields: the sentence plus qty, unit and name on rosin paper, because "4 rolls of blue tape and rosin paper" became 4 roll tape and 1 ea "rosin paper for the floor crew"; it should carry 4 rolls to both and
- material request · annoys · u_angel: D2 The job, the task it is for and the needed-by date it already had right from where I was standing; good, keep that.
- material request · blocks · u_angel: D3 The entry is buried: Request Material sits under Site, not on Today where I start the day; I want one big Request Material button on Today and on the task row I am buying for.
- material request · annoys · u_angel: D3 Editing a line's qty and unit on a 390px screen with the rows re-ordering under my thumb; lines should stay put while I edit and qty should be a plus/minus, not a typed box.
- material request · blocks · u_angel: D4 It said an older open request for 1 case of blue tape (needed 9/4) exists and Chen is checking stock, but gave me no one-tap "add to that request" or "cancel mine"; I could not tell if I was double buying.
- material request · slows · u_angel: D4 After Send I never saw the request again: no status on Today (ordered, in stock, arriving Fri), no who-owns-it; Chen's stock answer came by nothing.
- material request · annoys · u_angel: D5 No money shown, which is fine for me, but I could not see whether tape and paper come from stock or a new buy, so I could not trust it was not a second purchase.
- material request · blocks · u_angel: D6 Most important: when the same item is already requested or in stock, stop me and offer Merge or Use Stock in one tap, and tell Chen; that is real money.
- material request · slows · u_angel: D6 Then: parse "4 rolls of X and Y" as 4 rolls each; a Request Material button on Today and on each task row; the open request shows on Today with its status until it lands. Keep the Labor Day catch, it saved a no-show deli
- material request · annoys · u_angel: D8 Copied nothing; the words came from the floor crew's ask out loud. The second line took my crew's phrase as the item name; it should have matched it to the item instead.
- material request · slows · u_angel: D9 "Blue tape 1.5in" was already a known item and matched; rosin paper should have matched too, with unit roll, the usual qty, and the cost code from the task I was on, so I type only the sentence.
- material request · annoys · u_angel: D10 Made it on the phone only and did not see it on the desktop; on the desktop Today showed my other open items in one view, so the open request and its stock check should show there and on the phone Today the same way.

## Creators, by document type, desktop

- RFQ · slows · u_chen: D1 5 taps and 37s is right only for the clicks: the "Which Lines?" sheet showed about 28 lines over two pages with no search, I found "Trim, doors, paint & hardware" by reading, and Create RFQ sat at the bottom of page 2. S
- RFQ · slows · u_chen: D2 Nothing typed into the RFQ, but I had to mail Angel for door count, size, swing and pre-hung or slab: the lump-sum estimate line carried no door list, and Sarah's door schedule did not exist yet.
- RFQ · blocks · u_chen: D4 Which vendors I may issue to: only Carlos Millwork had COI and W-9 for doors. The assistant could not suggest three door vendors, and the Buy Board order-by (9/16, on site 10/7) and RFQ need date (on site 9/14) disagreed
- RFQ · annoys · u_chen: D5 No totals yet to trust: one lump-sum line, no vendors picked, nothing sent (it went to Foreman Review). The harness "three vendors asked" did not happen; the RFQ was not sent during the pilot.
- RFQ · slows · u_chen: D6 "Request Quotes" from the estimate line itself; a search on Which Lines?; a vendor pick that shows only vendors with COI and W-9 and suggests from past purchases; split lines so trim/paint/hardware can go while doors wai
- RFQ · slows · u_chen: D8 The door spec (6 doors, size, swing, pre-hung) came from Angel's mail; the trim quote BLQ-2210 from Brooklyn Lumber's mail. Neither landed on the RFQ by itself.
- RFQ · slows · u_chen: D9 Interior door, pre-hung, with size/swing/hardware options, and its cost code; plus the vendors who supplied it last time.
- bill · slows · u_controller: D1 CM-0102: 22 actions and 40s is too many for a one-line bill on a PO I had already picked; the time went to 4 screens (Banking, Purchasing, Bills & Payroll) and two wasted `find` calls because "Description" and "Amount" r
- bill · blocks · u_controller: D1 SE-0922: 2 taps and 72s is fast for the wrong reason; at 10:30 the New Vendor Bill form took 1 open plus 8 steps and still did not save, then at 16:30 Enter the Bill on Today posted it in one tap with no form. Right is 3
- bill · slows · u_controller: D2 CM-0102: I typed 11 of 12 fields. Vendor, PO, job, entity, cost code, estimate line and category (Subcontractors was my guess against Materials) all follow from PO-2026-048, and the due date follows from net 15. Only the
- bill · annoys · u_controller: D2 SE-0922: I typed nothing, and that was the problem. The amount, invoice number and date came from Satish's mail. What it should have filled and then shown me was 06 Electrical, the Electrical rough & finish line, the PO 
- bill · blocks · u_controller: D4 CM-0102: the invoice PDF was not in the "Invoice Document" list and the form could not attach it from my files. I also had no receipt or progress evidence for the 25% of PO billed, so I had to mail Chen. A bill with no s
- bill · blocks · u_controller: D4 SE-0922: before it posted I never saw the cost code, the estimate line, the bank line it would match, or which journal it would reverse ("Reversal of #26"). I still do not know what #26 was.
- bill · slows · u_controller: D5 CM-0102: yes on the sum. PO $76,000, $38,000 paid, this $19,000 leaves $19,000, and it showed once I picked the PO. "Round-dollar amount" is a fair flag on a progress bill. Terms were not stored on the record even though
- bill · blocks · u_controller: D5 SE-0922: no. Safe to Spend moved $9,373 on a $7,400 bill and Subcontractors over budget moved $7,400. I cannot trace the extra $1,973 from the screen, and the toast said "submitted for approval" for a bill that posted as
- bill · blocks · u_controller: D6 1. One bill per bank line, enforced before any write: Enter the Bill on Today, Confirm on Banking and New Vendor Bill all check for an existing bill on the vendor, amount and bank line, and offer "Match to SE-0922" in pl
- bill · blocks · u_controller: D6 2. No one-tap posting of a money record. Enter the Bill opens a review prefilled from the PO and the attached PDF: vendor, invoice, amount, terms and due date, cost code, estimate line, PO, bank match and any reversal. T
- bill · annoys · u_controller: D8 CM-0102: the description and amount came from Carlos Millwork's invoice PDF (25% of the PO for shop drawings), and the cost code and line from PO-2026-048. I retyped them because the form could not read the PDF.
- bill · annoys · u_controller: D8 SE-0922: everything came from Satish's mail (invoice 8/31, $7,400, paid ACH 9/2). The system lifted it from the mail, which is right, but posted it without showing me.
- bill · slows · u_controller: D9 CM-0102: the PO-2026-048 line should have carried the item, description, unit, cost code 10 Millwork & countertops and the estimate line onto the bill. I picked the PO, and I still picked cost code, line and category by 
- bill · blocks · u_controller: D9 SE-0922: the harness shows no due date, terms, cost code, PO link or estimate-line link on it. With Satish's PO and the vendor's default 06 Electrical, it should have filled all five and passed a three-way match.
- bill · annoys · u_controller: D10 Desktop is clearer: the Payments table names the bill, account and cleared line, and that is how I found the duplicate. The phone match card is faster and readable, but it is blind to bills posted elsewhere. The phone sh
- change order · slows · u_alan: D1 4 taps, 56s is right; Start Change Order to sent in one form was the best flow of the pilot. The seconds went into pricing the line myself because nothing in the library or past COs had a 42 in guard.
- change order · annoys · u_alan: D2 Description and price for the guard; I typed 144 characters for a code-driven guard height change that every brownstone stair job sees.
- change order · slows · u_alan: D4 Item library and past COs had no price for the guard; I needed the carpenter's labor and material cost on screen, not just "price it before it goes to the client".
- change order · annoys · u_alan: D5 $1,450 / $980 / 32% added up, but no tax or markup shown on the CO line and no sign of how it changes the contract and retainage on the next billing; I want the revised contract value on the CO.
- change order · annoys · u_alan: D6 Show the revised contract value and the next billing effect on the CO, and remember my priced guard line in the library so the next job fills it.
- change order · slows · u_alan: D7 Code-driven guard and rail height changes (36 to 42 in) with the build-and-hold-finish note; the language and price repeat across stair jobs.
- change order · annoys · u_alan: D8 The 42 in reason came from my call with Angel; the cost I built from the carpenter's usual numbers, outside the app.
- change order · slows · u_alan: D9 Stair guard to 42 in: item, description, ea or lf, $1,450 / $980 last time, millwork cost code; the library should learn it from this CO.
- change order · annoys · u_alan: D10 Desktop was faster and clearer (one form, toast, portal); the phone should copy the single form with price and schedule together and no estimate line dump.
- estimate · slows · u_owner: D1 The measured 5 taps, 13 actions, 36s is only the start: Lead > Convert > Closed Won > "Close and Start the Proposal" made an empty $0 EST-2026-015 in about 6 of my actions, and that part is right and fast.
- estimate · slows · u_owner: D1 The real work was at 10:30: 28 actions to write 3 lines ($128,000 + $42,000 + $40,000 = $210,000), budget cost, scope, inclusions, exclusions; lines go in one at a time with no template, and 2 more were lost on Draft Cov
- estimate · slows · u_owner: D2 The three areas, the ~$210k budget and the Tue 9/8 due date were already in Nadia's mail and my walk notes, and I typed them again; the 20% margin and budget cost I worked out by hand instead of the firm default filling 
- estimate · blocks · u_owner: D2 Project should have filled itself: the select had only "—", so a signed $210,000 had no 88 Garfield job to cost against (the harness says projectId is set; on my screen it was "—" through 9/8, so check which is true). Ow
- estimate · blocks · u_owner: D4 Whether Mark Sent emailed Nadia or only changed the status; I mailed her myself to be safe, so she may have two. Where the cover email draft went.
- estimate · annoys · u_owner: D4 The deposit terms: the estimate says Net 15 and progress invoices with no deposit line, so when she signed and asked for the deposit invoice I had nothing on the estimate telling billing what % to bill.
- estimate · annoys · u_owner: D5 The sum I trusted: three lines, $210,000, and I checked it by hand. Margin I set myself (budget cost $168,000, 20%); no markup or overhead line shown, no tax line, no retainage, so I trust it only because I did the arith
- estimate · blocks · u_owner: D5 I do not trust the back end yet: with no project, the $168,000 budget cost cannot feed job cost or tie to bills, and nothing flagged that.
- estimate · blocks · u_owner: D6 1. Close and Start the Proposal must create the project (88 Garfield) and link it, or refuse to call the estimate approved without one; Project "—" on a signed estimate is a red flag, not a dash.
- estimate · slows · u_owner: D6 2. A design-build template (kitchen, bath, floors, with typical inclusions and exclusions and default margin) and lines drafted from the walk notes and the client's mail. 3. Record Client Accepted at the top, with the si
- estimate · slows · u_owner: D7 Inclusions and exclusions (permits and LPC filing, protection, debris removal, owner-supplied fixtures excluded, asbestos and hidden conditions excluded), payment terms and validity (30 days): written by me again, same o
- estimate · slows · u_owner: D7 The scope paragraph for a kitchen and a powder room in a Park Slope brownstone: demo, rough plumbing and electric by SD Plumbing and SD Electric, finishes; I write it on every job.
- estimate · annoys · u_owner: D8 Copied the scope and totals from my walk notes with Nadia and her mail (kitchen, powder room, parlor floors, ~$210k); inclusions and exclusions from memory of older estimates, because I could not see an old estimate to c
- estimate · slows · u_owner: D9 From the library: "Kitchen renovation, brownstone" and "Powder room" and "Parlor floor refinish" as items with unit (lump sum or per sq ft), default price and cost (to give the budget cost), cost code, and the in-house t
- estimate · annoys · u_owner: D10 Made on the desktop; I recorded her approval on the phone the same day. Phone: the record reads well (total, client, three lines above the line) but the approve control was "(docact lkapprove)", unnamed, at the bottom; r
- estimate · annoys · u_owner: D10 Desktop was faster and clearer for writing; the phone should copy its named buttons and one row per estimate. Both should put "Client Accepted" next to Follow Up and Revise, take the signed PDF, and offer the deposit inv
- invoice · annoys · u_billing: D1 INV-2026-039 (Rivera 40% at filing, $17,080) at 2 taps and 24s is right; most of the time went on reading the queue row and the Send to Client sheet, which is time well spent.
- invoice · slows · u_billing: D1 INV-2026-041 and 042 measured 3 and 6 taps, but both were $0 CO drafts I should never have made. Deleting them cost 4 more taps each, and one Delete got lost behind "Please Confirm", so the real cost was about double wha
- invoice · annoys · u_billing: D2 Nothing. I typed 0 of 1 fields on 039, because the milestone percent, amount, due date and client mail all came from the fee schedule.
- invoice · blocks · u_billing: D4 On the CO invoices, percent complete and a completion note were not on the CO page. I found out the CO had nothing to bill only after New Progress Invoice had used a number. CO-001 was 50% billed at 0% complete, and noth
- invoice · slows · u_billing: D4 On 039, the proof that the filing milestone was reached (date, filing reference) is not on the invoice. I confirmed it from mail. A client who asks "what milestone?" should see it on the page.
- invoice · annoys · u_billing: D5 I trusted 039: 40% of the fee is $17,080, I checked it, and Made Today showed the journal entry. I don't trust billed-to-date on CO invoices while the app lets billed % run ahead of complete % with no warning.
- invoice · blocks · u_billing: D6 1. New Progress Invoice on a CO with nothing to bill should say "0% complete, nothing to bill" and make no draft or number. 2. Block Send at $0. 3. The queue row link "INV-2026-041" opened EST-2026-D140; it should open t
- invoice · annoys · u_billing: D6 4. A Delete confirm sheet must not be skippable by the next action. If it is dismissed, say "not deleted" in a toast.
- invoice · annoys · u_billing: D7 None from scratch. The design-fee milestone line ("40% of design fee at filing") is on every job, and it filled itself.
- invoice · annoys · u_billing: D8 None copied. The milestone wording came from the fee schedule, and the CO names came from the COs.
- invoice · slows · u_billing: D9 The CO invoices made 0 lines. A CO invoice should carry the CO line with its number, description, cost code and approved amount even when nothing is billable, or refuse to start. The fee line on 039 already filled item, 
- invoice · slows · u_billing: D10 I also drafted one on the phone (043). The desktop was clearer and faster for reading lines. The phone queue's first screen is as good as the desktop's for a quick look.
- material request · slows · u_chen: D1 4 taps and 24s to acknowledge one field request is double what it should be: "Apply" on Today only put it on the Buy Board, and a second tap "Acknowledge" was the real acknowledgement. Should be 1 tap, 5s.
- material request · annoys · u_chen: D2 Nothing typed, but the request did not carry the cost line it is for; I had to work out later that it belonged to estimate line 07 Insulation/drywall.
- material request · blocks · u_chen: D4 That the material was already bought: Brooklyn Lumber order 88412, paid on the Square card $2,140.50, pickup by 9/4. It was only in my mail; nothing on the request said so, so I could have bought it twice.
- material request · annoys · u_chen: D5 No money on it at all, so nothing ties the request to the $2,140.50 card charge or the estimate line budget.
- material request · slows · u_chen: D6 One "Acknowledge" button on Today that also files it to the Buy Board; and show matching open orders, card charges and mail on the request before I buy.
- material request · annoys · u_chen: D10 On the phone (9/8) Acknowledge on Today was one tap with a clear toast; the desktop's two-step Apply then Acknowledge should copy the phone.
- pay application · annoys · u_billing: D1 INV-2026-040 at 2 taps and 23s is right: Draft, Send to Client, Send. The real time went before it: 5 of 12 actions on news and mail, then reading 14 rows to find the 2 that moved.
- pay application · slows · u_billing: D1 Getting Alan's sign-off took a mail and a phone call the day before. That wait is the true cycle time of an application, and the measurement does not see it.
- pay application · annoys · u_billing: D2 I typed nothing. Retainage at 10%, line values and evidence notes all filled. What should fill but doesn't is Alan's conditional yes (by phone, 9/4 07:38): it is not recorded anywhere on the application.
- pay application · blocks · u_billing: D4 Billed-ahead was not flagged. Every line showed 51.67% billed on INV-2026-038, against a schedule at 0 to 20% on six lines (Windows, Tile, Trim, Exterior, General conditions, Millwork). I caught it by eye in the grid.
- pay application · slows · u_billing: D4 The Framing "what was done" note was cut off, so I couldn't read all the evidence for an $11,103 line. The "3 lines to look at first" toast doesn't mark which lines. The SOV lines have no names, so I matched them by amou
- pay application · blocks · u_billing: D5 I trusted the sum and retainage: $12,651 gross, $11,386 after 10%, and Framing $11,103 + Electrical $1,548 adds up. I did not trust billed-to-date, because invoice 2 ($68,265) carries up to 51 points of unearned revenue 
- pay application · blocks · u_billing: D6 1. A billed-ahead flag on each line where billed % is above complete %, carried to the queue row and Caught for You, with that line held on its own. 2. One tap "Needs PM Sign-Off" on the queue row that records the PM's y
- pay application · slows · u_billing: D6 3. Pin the lines that moved to the top and fold the 12 held lines. 4. Show each evidence note in full. 5. Put line names on the Schedule of Values.
- pay application · annoys · u_billing: D7 None from scratch; all 14 lines came from the contract SOV. The line names should come from the estimate lines on every job; today they are amounts only.
- pay application · annoys · u_billing: D8 None copied. The app pulled the evidence (foreman note 9/2, PM update 9/1). I checked it by hand against Alan's call notes in my diary.
- pay application · slows · u_billing: D9 Line name, cost code and scheduled value should fill from the estimate line, and percent complete from the signed foreman log. On the next application, Framing fell back to a task count.
- pay application · slows · u_billing: D10 I saw the next application on the phone (043). The desktop grid (billed %, complete %, evidence side by side) is what let me catch billed-ahead. The phone should show the same three facts as one stacked card per line.

## Creators, by document type

- (no answers yet)

## Synthesis, per document type: time and taps against the target, back-end gaps, client-view issues ranked, top fixes

How to read the measures first. The "Back-end gaps" column names what is missing, not what passed. Three creators read it as a claim of done (Alan on EST-2026-016, the owner on EST-2026-015's project, Chen on the RFQ's "three vendors asked"); the saved data agrees with them, not with their reading: EST-2026-015 has no project, RFQ-2026-001 has no vendors and no due date. Rename the column "Missing". Where the measures are wrong: PO-2026-049 shows "none" with a $0 price, no total and the wrong tax; the pay application and both COs show "none" while billing runs 39 points ahead and approved change work is off the schedule of values; "Not found after save 0" while Alan could not find his draft estimate; "Validation stops 0" while Chen's PO save stopped behind a sheet; taps and seconds count only the creating step (Chen 3 taps measured against 24 actions lived; the owner's 28 actions writing lines are not counted), and INV-2026-041/042/043 count as made though all three were deleted. The client reader was shown other clients' documents by the harness; docs.json shows INV-2026-039 addressed to the Rivera family and EST-2026-015 to Nadia Okoro, so that is a harness artifact, not an app leak. The gallery `client_docs/index.html` was not written.

### Estimate
- **Time and taps.** Desktop (owner, EST-2026-015): measured 5 taps, 36s against 20 taps; the start from Lead > Convert > Close and Start the Proposal is right, but writing three lines took 28 more actions and 2 were lost on Draft Cover Email. Phone (Alan, EST-2026-016): measured 11 taps, 49s against 25 taps and 10 minutes; in practice it failed: three turns, no field took input, about 12 actions to find New Estimate and 5 to get back to the draft. The phone target is not met at any length.
- **Back end.** S1 project: approved $210,000 EST-2026-015 has an empty projectId, so the $168,000 budget cost cannot feed job cost or tie to bills, and nothing flagged it. S1 total, price, description and cost code: EST-2026-016 is $0 with one blank line and can be printed and signed. S2 payment schedule: no deposit field, so billing had nothing to bill the deposit from. S2 terms: net 7 against a 15-day footer on one page. S2 promised-by date: the noon promise to the Kleins is on no record.
- **Client view, ranked.** (1) Client, owner, designer, blocks: EST-2026-016 is an empty $0 estimate called "Proposal" with a signature line. (2) Owner, designer, client, blocks: it uses a second template with contradicting terms. (3) Client, owner, designer, slows: EST-2026-015 has no exclusions, allowances, permits/LPC, schedule or payment schedule, and says "Net 15". (4) Client, blocks: estimates are not on the portal, so nobody accepts from a phone. (5) All three, annoys: project title printed three times, "1 ls".
- **Typed versus filled.** Measured 23 characters over 4 lines (6 per line), 2 picks, 1 filled; the owner's scope, inclusions and exclusions, typed in a later turn, are not in the count. An item library fills: Kitchen renovation (brownstone), Powder room, Parlor floor refinish per sf, each with scope text, unit, default price and cost (budget cost and margin), cost code and the SD Plumbing / SD Electric split; plus a design-build proposal template with standard inclusions, exclusions, payment schedule and 30-day validity.
- **Top fixes.** (1) Estimate page, phone: takes a line and a price, and the draft shows on the client page, Projects > Estimates and Made Today. (2) Lead convert sheet and estimate header: Close and Start the Proposal creates and links the project; no Approved without one. (3) Estimate print/send: block a $0 total, an empty line or a "Proposal" title, and print one template.

### Change order
- **Time and taps.** Phone (Alan, CO-2026-003): 7 taps, 32s against 12 taps and 2 minutes, met on the form; the real cost was 8 calls through Projects > card > Change Orders, overwriting the $46,500 estimate line the form dragged in, and scrolling past 13 lines to Schedule Impact. Desktop (CO-2026-004): 4 taps, 56s against 10, the best flow of the pilot; the seconds went to pricing from memory.
- **Back end.** The audit says none; it did not check these. S1 billing: approved COs total $8,470 but only $6,200 is on INV-2026-040's schedule of values, so $2,270 of approved change work has no line to bill. S2 contract sum: no original, prior COs or revised contract on either CO. S2 reason type: none, so a code miss in our own drawing (CO-2026-004, $1,450) is priced to the client without reaching Alan. S2 price check runs after the price is typed; the line reads $0 with "All changes saved" until priced.
- **Client view, ranked.** (1) Client, owner, designer, blocks: CO-2026-004 charges the client for our drawing missing code; the owner says a design miss is ours, his call per job. (2) Client blocks, designer and owner: CO-2026-003 is not in Waiting on You. (3) Client, owner, designer, annoys: "Angel asked 9/8" prints. (4) Client and designer, slows: no schedule impact on CO-2026-004, no word on when it is billed ("Net 15 from when?"), no revised contract. (5) Client, annoys: no exclusions, "GFI" is jargon, Approve is outlined while Choose is blue.
- **Typed versus filled.** The most typing of any type: 15 fields, 291 characters into 2 lines (146 per line), 1 pick, 5 filled. A library fills: GFI outlet, ea, $420 / cost $240, 06 Electrical, +1 day on rough electrical; stair guard to 42 in, ea, $1,450 / $980, millwork code. It should learn each priced CO line.
- **Top fixes.** (1) Today and the site question, phone: Quick Price CO with one line, amount, days and Send to Client, no estimate-line drag, Schedule Impact beside the price. (2) CO form and print: original, prior, this and revised contract sum, and a reason type; design or code misses route to Alan before pricing. (3) CO print and portal: internal fields never print, and every sent CO heads Waiting on You.

### Invoice
- **Time and taps.** Desktop (billing): INV-2026-039 at 2 taps, 24s against 8, met, with 0 of 1 fields typed. INV-2026-041 and 042 (3 and 6 taps) were $0 CO drafts never wanted; each delete cost 4 more taps and one was lost behind Please Confirm, so the real cost is about double. Phone: INV-2026-043 at 4 taps, 39s was a draft made only to preview; it used a number and took 4 more desktop taps to delete.
- **Back end.** S1 numbering: 041, 042 and 043 issued and deleted leave holes in the invoice sequence. S1 CO invoices: New Progress Invoice made $0, zero-line drafts with no block. S1 billed ahead: CO-001 was 50% billed at 0% complete, unflagged. S2 cost code on every line of INV-2026-039. S2 link: queue row "INV-2026-041" opened EST-2026-D140. S2 bill-to address blank; milestone proof (date, filing reference) not on the invoice.
- **Client view, ranked.** (1) Owner, client, designer, slows: no way to pay on any invoice (ACH, link, remit-to, contact), and due dates fall on a weekend. (2) Client, blocks: INV-2026-039 is not on the portal. (3) Client, owner, designer, slows: 40% of construction administration billed at filing, with no fee summary (total, to date, this, remaining). (4) All three, annoys: blank bill-to address. (5) Designer and client: retainage and CO footer on a design invoice, "1 ls".
- **Typed versus filled.** 5 lines, 1 field and 151 characters typed, all on 043, which billing did not mean to type into. INV-2026-039 filled itself from the fee schedule: the model for the rest. The lever is the fee schedule and SOV, not the item library; a CO invoice should carry the CO line (number, description, cost code, approved amount) or refuse to start.
- **Top fixes.** (1) Billing Queue row: Preview that uses no number; nothing billable means no draft; Send blocked at $0; the link opens the invoice. (2) Invoice print and portal: a how-to-pay block and Pay button, bill-to from the client record, due dates off weekends. (3) Invoice page, phone: line table as stacked cards at 390px with Amount visible.

### Pay application
- **Time and taps.** Desktop (INV-2026-040): 2 taps, 23s against 10, met. The true cycle is Alan's sign-off, a mail and a call the day before, which the measure cannot see, plus reading 14 rows to find the 2 that moved. Phone: the next application (043) cut off the Amount column at 390px.
- **Back end.** The audit says none; it is wrong. S1 billed ahead: every line "Previously 51.67%" against 0 to 20% complete on six lines; 54% billed against 15% on site; INV-2026-038 ($68,265) carries up to 51 points of unearned revenue in AR. S1 unbilled change work: the $2,270 above. S2 retainage: 10% stated, 6.4% to date ($16,933 on $266,335). S2 PM approval: Alan's conditional yes is recorded nowhere. S2 SOV lines carry no names or cost codes; Framing fell back to a task count on the next application.
- **Client view, ranked.** (1) Client, owner, designer, blocks: internal notes print ("5 lines fell back to cost, check them before sending", "measured by foreman update 9/2"). (2) All three, blocks: the document and portal tell the client billing is 39 points ahead and 12 lines are below what was billed; it reads as overbilling. (3) Client and owner, blocks: the missing $2,270 CO, and Invoices Due $79,651 on the portal with no breakdown against an $11,386 invoice. (4) All three, slows: two totals blocks, retainage inconsistent. (5) Client, slows: no Pay button on the portal.
- **Typed versus filled.** 14 lines, nothing typed, all from the contract SOV. Missing fills: percent complete from the signed foreman log, line names and cost codes from the estimate lines. The estimate-line link is the lever here, not the item library.
- **Top fixes.** (1) Pay application grid and Billing Queue row: a billed-ahead flag per line, that line held on its own, carried to Caught for You; hold INV-2026-040 for Alan. (2) CO approval: every approved CO joins the SOV the same moment. (3) Pay application print: internal notes stripped, the G702/G703 summary once, the PM's yes or hold recorded on the row.

### PO
- **Time and taps.** Phone only (Chen, PO-2026-049): measured 3 taps, 22s against 12; lived 24 actions (6 finding the request through Today, Buy Board and Purchasing > Requests, 3 linking the line, 3 creating the vendor), ending in a $0 draft.
- **Back end.** S1 price and total: $0 while the Square card already paid $2,140.50, with no card match. S1 sales tax: set exempt (capital improvement) on boards we buy; materials we buy are taxed to us. S2 terms lost when the Custom sheet covered Sales Tax and the save stopped, with no unsaved warning. S2 vendor W-9 and COI not checked before issue; pickup date 9/4 not tracked. The estimate line (07) did carry through: keep that.
- **Client view.** Internal document; none.
- **Typed versus filled.** 6 fields typed (5 on the new-vendor sheet, the quote number), 4 picks, 1 filled, 0 characters into lines. The request knew the job and item; Brooklyn Lumber's 9/1 mail knew order 88412, 25 GWB and 6 cement board and the amount. A library fills GWB 1/2" and cement board: unit, last price from that vendor, code 07, taxable materials.
- **Top fixes.** (1) PO form from a request: carries item, qty, last price or the vendor mail, and tax from the item type. (2) Purchasing and Banking: Record a Purchase Already Paid, matched to the card line. (3) PO form, phone: no hidden sheet behind a pick, an unsaved warning, search on the Link sheet.

### RFQ
- **Time and taps.** Desktop only (Chen, RFQ-2026-001): 5 taps, 37s against 12, but the Which Lines? sheet showed about 28 lines over two pages with no search and Create RFQ at the bottom of page 2; it should be 2 taps from the estimate line.
- **Back end.** S2 vendors: none asked, so the three-quotes-over-$2,500 standard is unchecked; S2 quotes due date empty; not sent (Foreman Review). S2 need date: Buy Board says order by 9/16 for 10/7, the RFQ says on site 9/14. Only Carlos Millwork had COI and W-9 for doors.
- **Client view.** Internal document; none.
- **Typed versus filled.** Nothing typed, 2 filled of 27. The door spec (6 doors, size, swing, pre-hung) sat in Angel's mail and trim quote BLQ-2210 in Brooklyn Lumber's; neither landed. A library fills an interior pre-hung door with size, swing and hardware options, its cost code and the vendors who supplied it.
- **Top fixes.** (1) Estimate line, both devices: Request Quotes on the line itself. (2) RFQ form: vendor pick shows only vendors with current COI and W-9 and suggests three from past purchases. (3) RFQ form and Buy Board: one need date, and split a line so trim goes while doors wait.

### Bill
- **Time and taps.** Target under a minute. Desktop: CM-0102 at 4 taps, 40s, met on the clock but 22 actions over Banking, Purchasing and Bills & Payroll with 11 of 12 fields typed; SE-0922 at 2 taps, 72s, fast for the wrong reason: the New Vendor Bill form failed to save, then Enter the Bill on Today posted it in one tap with no review. Phone: PAY-260902 at 3 taps, 71s was a duplicate the controller never meant to make, created by Confirm on an ACH match card that said "no bill on file".
- **Back end.** S1 duplicate: PAY-260902 and SE-0922, both $7,400, both cleared by one ACH; ledger cash fell $180K to $173K and the duplicate toast came after the post. S1 SE-0922: no cost code, PO, estimate line, terms or due date; Safe to Spend moved $9,373 on a $7,400 bill ($1,973 untraceable); toast said "submitted for approval" for a bill posted paid; "Reversal of #26" unexplained. S1 PAY-260902 coded to Overhead with a made-up number. S2 CM-0102: terms not stored, invoice PDF not attachable, category guessed.
- **Client view.** Internal document; none.
- **Typed versus filled.** 3 bills, 7 fields and 103 characters typed (34 per line), 4 picks, 1 filled. PO-2026-048 knew vendor, job, entity, cost code 10, estimate line and net 15; the PDF knew the rest. The lever is carry-over from the PO line and reading the PDF or mail, then a review; the phone's Accept All is the right speed to copy.
- **Top fixes.** (1) Enter the Bill on Today, the Banking match card and New Vendor Bill: one bill per bank line, checked before any write, offering "Match to SE-0922". (2) Enter the Bill: no one-tap post; a prefilled review from PO and PDF (terms, due, code, line, bank match, any reversal), then Post, with a toast that says the real status. (3) Bill form and match card: a job vendor's ACH defaults to its open PO line, never Overhead, and "Not this, it duplicates" reverses with a linked reason.

### Material request
- **Time and taps.** Target under 30s and 5 taps. Phone (Angel): 6 taps, 46s, 21 actions for 2 items: missed on both counts; the path ran Today > More > Site > Requests, and rows moved under his thumb. Desktop (Chen acknowledging): 4 taps, 24s; Apply then Acknowledge is two steps where the phone does it in one.
- **Back end.** S2 cost line: neither request carries the estimate line it is for (it was 07 Insulation/drywall); the job, task and needed-by date were right. S2 leak risk: the GWB was already bought (order 88412, card $2,140.50) and nothing on the request said so; an older blue-tape request was open with no merge.
- **Client view.** Internal document; none.
- **Typed versus filled.** 4 of 9 fields typed (a 74-character sentence, then fixing line 2), 9 filled, 4 defaults. "4 rolls of blue tape and rosin paper" gave rosin paper 1 ea named after the crew. A library matches rosin paper as it matched blue tape: unit roll, usual qty, cost code from the task.
- **Top fixes.** (1) Today, phone: a big Request Material button there and on each task row, with the open request and its status until it lands. (2) Request sheet and Buy Board: when the item is already requested, bought or in stock, stop and offer Merge or Use Stock in one tap, and tell Chen. (3) Request parser: carry qty and unit across "and", keep "for the floor crew" as a note, keep rows still while editing.

### The five fixes that matter most to Alan, in order
1. **One bill per bank line, and no one-tap posting of money** (Today, Banking match card, New Vendor Bill). A $7,400 duplicate already cleared; money that leaves twice cannot go to raises, staff, charity or the client.
2. **Billed-ahead flag and every approved CO on the SOV** (pay application grid, Billing Queue, CO approval). $2,270 of approved work has no line to bill, and INV-2026-040 shows the client billing 39 points ahead of the work; hold it until Alan decides.
3. **A client-output gate** (print and send for estimates, COs, invoices and pay applications): internal fields never print by class, $0 or empty lines block, one letterhead with how to pay. Every client reader called on this.
4. **The estimate works on the phone and always has a job** (estimate page, Lead convert sheet). Alan could not price at the client's parlor, and a $210,000 approved estimate has no project to cost against.
5. **Records fill from what the system knows** (BACKLOG 1.18): PO from the request with price and tax, bill from the PO line and PDF, CO and estimate lines from an item library that learns each priced line. The CO's 146 characters per line and the controller's 11 of 12 typed fields are what it removes.

