# Procurement: review and plan (Alan, 2026-10-24)

> "The next item that we can begin implementing before the full ERP is ready is the procurement module. That also needs a ton of work; it's nowhere near ready. It needs a full review and major changes."

Procurement is the second module the team adopts, after Tasks. It must carry a real buying day for the coordinator, with the PM, the foreman, the driver, billing and the owner each doing their part, and leave the money truth intact from the estimate line to the bank line.

**Mockup** (phone first, for Alan's yes): https://claude.ai/artifact/7oKRRgpH3hH6jU4U8VAgat. It has five phone screens (Buy Board with two lines picked, the order sheet with its checks, Arriving with Reconfirm, Receive, a vendor issue with its credit) and the desktop Buy Board with the need's panel. Its data is invented.

## 1. What the review used
- **The last three team meetings** (10-15, 10-19 and 10-22). They were read for what actually goes wrong in buying; the content stays outside the repo, and the problems below are paraphrased.
- **A code inventory of the whole chain:** estimate line, need, quote, order, delivery, receipt, issue, bill, payment and job cost. It covers every view, store, status, link, wrapper layer and test.
- **The coordinator expert's buying day on 10-21** (`review/experts/coordinator.md`): 24 findings, of which F1 and F2 (the order gates) are fixed and live.
- **The leaders:**
  - Procore Materials: inventory, procurement and field in one tool, POs synced to receipts, mobile receiving with photos, delay risk flags.
  - Procore Commitments: POs checked against budget, and a three-way match of PO, receipt and claim.
  - NetSuite procure-to-pay: requisition, PO, item receipt, bill, a three-way match before payment, and vendor return authorisations and credits.
  - Buildertrend: bid requests through a vendor portal, POs, then bills with lien waivers attached.
- **The coordinator expert's buying day, 10-25** (`review/procurement/coordinator_day.md`, 32 findings). Grades: finding 4, reading 5, taps 5, phone 4, money safety 3, versus the leaders 4. Five money findings (a deposit paid twice, studs bought twice, an unflagged vendor prepayment, a sub award with no COI, sales tax different by path) became P0 and P1 items below; the tax call in section 7 was corrected.

## 2. What goes wrong today: the meetings
These are the firm's real buying problems, the ones the module must stop:
1. **Stock and delivery promises that do not hold.**
   - A tile supplier showed an item in stock, then backordered it, and the delay threatened an inspection.
   - A second supplier swapped an order and its manager stopped answering.
   - A backordered set arrives at month end.

   Nobody holds the promised date against the date the job needs it.
2. **Vendor errors cost the firm, and the credit is chased by memory.** On 10-15 the team set the policy: when a vendor's mistake creates work or cost, the firm asks for compensation.
   - The policy was applied to a wrong tile delivery and a faulty tile replacement.
   - For a utility-meter replacement, the threat was "credit within days or a card chargeback".

   Nothing records the claim, the amount, the deadline or the answer.
3. **Deposits gate deliveries.** A stone fabricator would not release slabs until a deposit was paid. A deposit is a payment against an order that is not yet a bill, and it has to be applied when the bill comes.
4. **Trade-account pricing gets lost.** A lighting purchase on a trade account landed at $0 on work in progress, and the discount was not recorded.
5. **Three quotes by hand.**
   - Demolition quotes needed more bidders, and a same-day walk to get them.
   - Millwork went out for a quote to one shop.
   - HVAC equipment pricing was negotiated against a target.
   - Laundry specs were gathered to negotiate.
6. **What the client pays for and what they have approved.** A fabric and labour price difference was held in work in progress, not billed, until the client approved it. "Track it, don't bill it without approval" has to be a state, not a memory.
7. **Site rules and receiving.**
   - Deliveries must land in the site window (8 to 4).
   - An appliance delivery had to be verified.
   - A faulty item was picked up for return.
   - Delivered quantities, such as slate for fireplaces and stairs, are tracked with the foreman by hand.
8. **Where to buy.** The designer must buy from preferred vendors, not from overseas direct sites. A missing light fixture had to be chosen from what is available now, not ordered with a lead time.
9. **Finding a vendor's contact** meant looking in QuickBooks.

## 3. What the code does today
The pieces are mostly there. The problem is that they are spread out and disagree with each other.

**Too many lists for one thing:**
- Purchasing has 10 views: Purchasing, Selections, Requests, Buy Board, RFQs, Purchase Orders, Deliveries, Route, Vendors and Inventory.
- The Buy Board has two modes and opens on Finish Selections, not on the lines Today counts.
- The same board is mounted again on the Purchase Orders page.

**Four rules for "late"** (lateMaterial, selLate, buyStrip, Materials):
- An ordered line whose ETA is after the need-by date shows only as a strip count. It never reaches Do Now or Today.
- Change-order lines never reach the Buy Board.

**Three ways to make an order from a line** (the Order sheet, Which Lines, New PO), plus four more (submittal release, RFQ award, request to PO, FF&E run). The gates are spread over 13 wrappers of `poAction` and 6 of `poValid`.

**Records lose their link to the estimate line:**
- A field request has no line field.
- An RFQ award copies neither the request nor the material into the PO, so the request stays "acknowledged" and the material stays "not ordered" after the award.
- A store-run card purchase creates no PO.

**Three receiving models** (PO lines, FF&E stages with condition, store-run "bought"). On a material PO:
- "Everything Arrived" receives everything with no count, slip photo, condition or early-date warning.
- No manual Reconfirm exists.

**Claims, returns and credits exist only for FF&E.** A problem on a material delivery records an issue but expects no credit, so it is never chased: the exact leak in section 2, item 2.

**The three-way match works on totals.**
- Line quantity billed against received is checked only when an invoice document is filed.
- A bill keyed by hand for the whole order before delivery passes.
- The PO's "paid" counts only bank lines, so it disagrees with Bills.

**Six approval thresholds** in six places:
- order approval ($10,000);
- over the line ($1,000);
- three quotes ($2,500);
- spend routing ($500 and $5,000);
- Payment Check ($2,500);
- bill approval.

**The COI gate is partial.** A first materials order to a vendor with no COI issues. A missing W-9 only warns.

**The vendor master** has no preferred-vendor, category or trade-account fields. Orders name the vendor as text.

**Ask and the Report Builder** cannot see requests, materials, receipts, store runs, returns, claims or order issues.

**Roles:**
- Billing has no purchasing view, and vendor bills are not on its landing page.
- The driver's route approval is not in the coordinator's Approvals or Do Now.

## 4. The design: one noun, one list, one path
Each kind of thing has one record, one list and one count everywhere (BACKLOG §1.16 registry).

| Noun | One list | Replaces | Carries |
|---|---|---|---|
| **Need** (what must be bought) | **Buy Board** | Buy Board modes, Selections board as a separate list, Requests list, Materials at risk, Purchasing overview rows | estimate, CO or FF&E line (asked if not known, never guessed silently), job, cost code, qty, need-by, order-by, who asked, stock check |
| **Quote Request** | **Quotes** | RFQs page "Requests" tab | the needs it covers, vendors asked, quotes read, leveling (materials and sub bids), award |
| **Order** | **Orders** | Purchase Orders (the board copy is removed) | vendor id, lines linked to needs, gates passed with reasons, approvals, deposit paid, promised dates |
| **Delivery** | **Deliveries** | Deliveries, Projects › Deliveries, Arriving Today, In Transit, Late to Site, Route pickups | order or store run, promised date, last reconfirmed, site window, who receives |
| **Receipt** | on the Delivery | three receiving models | per line count, slip photo, condition, who, when; early or late against the promise |
| **Vendor Issue** (claim) | **Issues & Credits** | FF&E claims and returns, PO issues, Credit With No Return | short, damaged, wrong, backorder, late, vendor error; the cost to us; the credit asked; the deadline; the answer; the credit memo or chargeback, matched to the bill or bank line |
| **Vendor** | **Vendors** | text vendor names | id, categories, preferred for, trade account and discount, COI, W-9, terms, lead time learned |

**The Purchasing menu becomes:** Buy Board, Quotes, Orders, Deliveries, Issues & Credits, Vendors and Stock. That is 7 entries, down from 10. Route stays as the driver's own screen, fed from Deliveries and the Buy Board. Selections stays a design tool; its items join the Buy Board when approved.

**One "late"** for a need:
- not ordered by its order-by date; or
- ordered with a promised date after its need-by date; or
- promised and not delivered by the promised date.

The same set shows on the Buy Board, Today, Do Now, the morning brief and Ask. A tile's count equals its rows.

**One path to an order:**
1. From one or more needs (single or multi-select, on the phone too).
2. Then the order sheet: vendor, price filled from the line, the price book and the last quote; the stock check; then the gates, shown inline as the vendor is picked.
3. Then Issue, or Send for Approval when a gate needs a person.

Blank starts stay, behind "More". Every other entry point (submittal release, award, request, FF&E run) calls this same sheet.

**One approval ladder.** The six thresholds move into one table in Settings › Approval Rules, owned by Alan and versioned like the Standard:
- order total;
- over the line;
- three quotes;
- new vendor;
- deposit;
- paying a bill.

Each rule names the Standard item behind it.

**Gates at issue, in Standard order:**
1. **Safety and the law.** A COI is required for anyone who comes on site: subs, services, installers, and vendors who deliver inside. A W-9 is required before the first payment, and on any order of $600 or more to an individual or partnership.
2. **Integrity.** Over the line needs a reason and the owner at $1,000 or more. Three quotes over $2,500, or a reason (sole source, client's choice, emergency).
3. **Money.** It is checked against stock. It is checked against the last price paid and against the trade-account price. A deposit is recorded as a prepayment on the order and applied to the bill.

**Receiving that checks.**
- One screen for the foreman, driver or coordinator: each line's count (prefilled, adjust down), a slip photo, condition (good, damaged, wrong), then Done.
- A receipt more than 3 days off the promise asks "early or late, still right?".
- Damaged, short or wrong opens a Vendor Issue at once, with the credit expected.

**Reconfirm, the Standard's 48 hours.**
- Every delivery due in the next 2 working days gets a Reconfirm draft to the vendor, carrying the site window and the site contact. The coordinator approves it.
- The card shows "Reconfirmed Tue 9:10" or "Not reconfirmed".
- A changed date updates the promise and re-tests "late".

**Vendor Issues and credits (the 10-15 policy, enforced).**
- Every issue that costs the firm work or money proposes a claim. It names the amount: the item, the extra labour or trip at the job's rate, and any restocking fee.
- The claim's lifecycle:
  1. A chase is drafted for the coordinator's approval.
  2. It is followed up at 3 and 7 days.
  3. At the deadline it escalates to the owner, per the Standard format, with options: credit memo, replacement, a deduction on the next bill, or a card chargeback (only for card purchases, inside the card's dispute window).
  4. It closes only when a credit memo or bank credit is matched.
- Credits never applied are a money leak on Today: "Money wasted is money that cannot go to raises, bonuses, staff, charity or client value."

**Line-level three-way match.** Before a bill can be approved, each bill line must pass:
- qty billed ≤ qty received;
- price ≤ the order price, or within the approved change;
- deposits applied;
- each money counted once.

A bill ahead of delivery holds as "Billed Before Delivery", with the line named. The order's "paid" counts payments and bank lines once, the same as Bills.

**The client's side.**
- A need bought on the client's behalf, or a price difference from the estimate line, is tagged Bill Back or Client to Approve.
- Client to Approve holds in work in progress and shows on the PM's Today until the client approves through a change order or a selection approval.
- Nothing is billed before approval, and nothing is forgotten: "purchases made on a client's behalf that were not billed back" is a leak the ERP catches.

**Vendors as one record.**
- Vendor id everywhere, with a one-time migration that matches the text names (a person confirms near-matches).
- Categories and preferred vendors per category, which the designer's buys use first. An overseas direct site needs a reason.
- The trade account number (last 4 digits) and its discount.
- Lead time learned from promised against actual dates.
- One contact card, with no need to look in QuickBooks.

**Each person's day:**
- **Coordinator (phone first).** The bar: Today, Chat, Tasks, Buy Board. Buy Board sections: Late, Order This Week, Waiting on Quotes, Arriving (with Reconfirm). One blue button per card: the safe next step (Order, Reconfirm, Chase).
- **PM.** Client to Approve and over-line approvals in Approvals. Each job shows its buying state.
- **Foreman.** Requests from the site with photo and voice. The need is linked to the line by the coordinator, not by the foreman. Receive on the phone with big targets.
- **Driver.** Route from Deliveries and pickups. Receive at the store or site. A card purchase becomes a store-run order linked to the need.
- **Billing.** "Vendor Bills to Enter or Approve" on the landing page, with the same count as Approvals. Holds named per line.
- **Owner.** Only escalations: over the line, approvals over the ladder, claims past their deadline.

**Ask and reports.** Every procurement noun goes into `erpQuery`, ⌘K and the Report Builder: needs, quotes, orders, deliveries, receipts, vendor issues and vendors. The coordinator's questions join the Ask bank:
- "what's late";
- "what arrives this week";
- "which quotes am I waiting on";
- "which credits are open";
- "is the tile above the estimate".

## 5. Think past the ask
**What Alan may not be thinking about:**
- Vendor ids are the migration risk. Today orders hold vendor names as text, and the Asana-style cleanup must not merge two different vendors. Near-matches are confirmed by a person.
- Partial deliveries and backorders split one line into several promises. The need stays one record with a dated promise per quantity.
- Card chargebacks have a dispute window, often 60 days from the statement. A claim on a card purchase must surface well before it closes.
- Deposits are money out with no bill yet. They must show in the cash forecast and job cost once, and be applied, never paid again on the bill.
- Sales tax: on a capital-improvement job in New York the contractor is the consumer of the materials. The firm pays sales tax to the vendor, or accrues use tax when the vendor does not charge it. The capital-improvement certificate (ST-124) stops the firm charging the client sales tax; it never makes the firm's own purchases exempt. Corrected 10-25 after the expert's buying day (section 7.4 had it backwards); to be confirmed with the firm's accountant.

**How it gets better:**
- The assistant reads the mail (quotes, confirmations, delay notices, credit memos) and updates promises and claims as proposals.
- Price and lead-time history make the next order's defaults.
- A late promise proposes the fix: expedite, an alternative vendor from the preferred list, or moving the task.

**What could go wrong:**
- **Data:** a migration that breaks links. Each phase runs the chain, the finance cross-check and the reports suite.
- **Money:**
  - a deposit counted twice;
  - a credit applied twice;
  - a claim closed with no matched credit.
- **Fraud:**
  - a vendor's bank details changed by email. A bank change is a person-verified event.
  - an order split to slip under a threshold. Split orders to one vendor within 7 days sum against the ladder.
- **The field:** a receipt that is too slow gets skipped, so it must be under 20 seconds for a full delivery.
- **The phone:** the Buy Board as a reflowed table. It becomes cards with sections, never a sideways scroll.
- **The books:** stock bought for the shop must go to Inventory, not to expense (BACKLOG §1.8 item 12).

## 6. Phases (one lane at a time; each deploys when green)
| # | Lane | What | Proof |
|---|---|---|---|
| P0 | **Money first** (from the 10-25 buying day) | a deposit paid on an order is applied to its bill, counted once, and the bill cannot be approved at the full amount while a deposit sits on it; a bank or card payment to a vendor with no bill (a prepayment) is flagged to the coordinator and controller with the vendor's papers, and the order's "paid" agrees with Vendors; one purchase-tax rule on every path (order, award, store run), as section 5 says | a $4,400 deposit then an $8,800 bill pays $4,400; a prepayment shows on Today; the same item taxed the same on every path; chain, reports, baseline and finance cross-check |
| P1 | **One Buy Board** | the Need record and one list (estimate, CO, FF&E, requests); one "late" with ETAs; requests carry the line; award updates request and material; opens on the lines; Today, Do Now, brief and Ask read the same set; the route approval in Approvals and Do Now; each request locked to one path (order, store run or stock); subcontract buyout as a Need (bid packages, leveling by scope, award as a subcontract behind the COI gate); a Need is a line's material or subcontract portion, never our own labour; one order-by formula, old sourcing flags to a weekly audit; the PM sees his job's orders | counts lint on every procurement label; a CO line reaches the board; a late ETA reaches Do Now; month sim holds |
| P2 | **One order path and the ladder** | one order sheet for every entry point; Approval Rules in Settings; gates by the Standard (COI on site, W-9 before pay, three quotes or reason, stock, price, split orders); deposits on the order; vendor ids with the migration | po_gates and purchasing suites on every entry point; deposit counted once in job cost and forecast; finance cross-check |
| P3 | **Deliveries and receiving** | one Delivery list; Reconfirm drafts at 48 hours with the site window; one receiving screen with count, slip photo, condition, early or late check; partials and backorders as promises | a receipt on the phone in under 20 seconds; early receipt asks; damaged opens an issue |
| P4 | **Issues and credits** | one Vendor Issue for materials and FF&E; the claim amount; chase, follow-up, escalation; chargeback window; matched credit closes it; leak on Today | a claim cannot close without a matched credit; card window alert; leak tests |
| P5 | **Match and billing** | line-level three-way match; Billed Before Delivery; one "paid"; vendor bills on billing's landing; Client to Approve and Bill Back | chain and reports suites; a bill ahead of delivery holds by line |
| P6 | **Vendors, price and Ask** | categories, preferred vendors, trade accounts; learned lead times; every noun in erpQuery, ⌘K and the Report Builder; the coordinator's Ask bank | Ask bank; report builder covers every noun |

Each phase:
1. starts from a Playwright check that fails the way the review saw it;
2. runs the must-run suites one at a time (smoke, baseline, reports, chain, finance cross-check, counts lint, menu, today, month sim);
3. merges and deploys under the standing go, with live checks and screenshots;
4. ends with an expert re-walk of the coordinator's day.

**Size, on what it rests:** the last three lanes (polish, speed, money fix) each took 2 to 3 hours from start to merge. P1, P2 and P3 are each larger than those, about 3 to 5 hours. P4, P5 and P6 are about 2 to 4 hours each. With one expert walk before and one after, about 25 to 30 hours of build time. The 10-25 buying day adds P0 and widens P1; the expert's guess is 4 to 6 more hours, so about 30 to 36 hours (a guess, not measured), run one lane at a time. That is heavy usage; it starts only after Alan's yes on the plan and the mockup. P1 alone would let the team start using the Buy Board.

## 7. Calls for Alan
1. **The plan and the phone mockup:** yes or changes.
2. **COI rule (recommended):** required for anyone who comes on site, plus vendors who deliver inside the building. Material suppliers who drop at the curb or ship need only a W-9 before the first payment.
3. **Vendor-error claims (recommended):** the claim proposes the item, extra labour at the job's rate and the trip. The owner approves a chargeback; the coordinator sends ordinary chases.
4. **Sales tax on purchases (corrected 10-25).** The first recommendation was wrong: a capital-improvement job does not make the firm's purchases exempt. The firm pays sales tax on materials (or accrues use tax); the job's capital-improvement status, set by the PM with the ST-124 on file, only means the client is not charged sales tax on the work. Alan's yes was to the wrong version; the build follows the corrected rule, to be confirmed with the accountant.
