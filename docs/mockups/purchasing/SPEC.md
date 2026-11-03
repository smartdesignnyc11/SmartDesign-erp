# Purchasing: the menu's pages (mock-up and spec, 2026-11-03)

Read with `docs/mockups/QUESTIONS.md` and the approved `docs/mockups/job-structure/`. Figures are the demo company's on 9/3, read from the
build of master 8eeb990 as Chen (coordinator) and the controller; `[PLACEHOLDER]` marks what the build did not have. Nothing in src/ changed.

| File | Screen |
|---|---|
| Menu | Phone menu, Purchasing open, a number on each page that waits on you |
| BuyBoard, DeskBuyBoard | Buy Board, phone (pick lines, sticky bar) and desktop (need panel) |
| Quotes | Quotes, phone (switch: today's empty state, and the requests as they would look once asked) |
| Orders, DeskOrders | Orders, phone and desktop (tiles open their rows) |
| Deliveries | Deliveries, phone, with the Receive sheet (tap Receive) |
| Vendors, Stock | Vendors and Stock, phone |

## 1. Today (census build bd3180c, re-read on 8eeb990)
- **Menu pages, 7:** Buy Board (`proc`), Quotes (`rfq`), Orders (`po`), Deliveries (`recv`, also Projects › Deliveries), Vendors, Stock (`inv`), and the controller's Purchasing (`ovbuy`).
- **Pages behind buttons, 2:** FF&E Buying Tools (its own Buy Board, 6 status tabs, Credits to Confirm, Returns $2,419, Clipper Access, Link to Schedule 8) and Analysis / Cost by Line.
- **Tab screens:** 11 walked by the census (Buy Board 4, Quotes 3, Stock 4), plus 8 it never reached (FF&E 6, Analysis 2): **19**. Vendors › Performance is a mode.
- **Same records twice:** PO-2026-047 on 4 pages; Buy Board and Orders share 9 records; Projects › Materials (6 tabs) is a third buying list.
- **The coordinator expert (round 1):** phone 4, desktop 5; receiving is a dead end on the phone; leaks found on the PO page never reach the lists.

## 2. Proposed: six pages, no tab rows
Buy Board, Quotes, Orders, Deliveries, Vendors, Stock. Each opens on **Needs You** (rows whose next tap is yours, with a red count equal
to the rows), then **Waiting on Someone Else** (each row names who; no number), then the rest one tap down. Job, vendor, trade and document
are filters, never tabs. Inside a record (a need, an order, a vendor) everything is that record; firm-wide lists are a link at the foot.

**Buy Board** (Needs You 9)
- What: every need not yet ordered (estimate and change-order lines, approved selections, site requests), by the date it must be ordered.
- Label: Buy Board, the coordinator's word since 10-19.
- Holds: needs only. Ordered needs move to Deliveries; FF&E's own board, the controller's overview and the job's Materials are this list filtered.
- Who and why: Chen, many times a day ("what must I buy, and what stops me?"); the PM sees it inside the job's Purchasing tab.
- First screen: Needs You (acknowledge 1, order today 1, bids 2, marked ordered with no order 2, no price 3); Waiting on Someone Else (submittal 2, decision 1, the PM's material split 4); Later folded.
- Numbers: 9 = its rows. Today's badge 17 counted late rows that wait on others; those now name who instead.
- The +: Buy From an Estimate or Invoice (job, document, lines), Restock the Warehouse, Blank Need (last, and it asks for the line before approval).
- From the document too: the estimate's, change order's and invoice's own lines carry Buy These Lines (single or multi-select, phone too; PROCUREMENT_PLAN §6), which opens the same order sheet with every line linked. One order path, two doors.
- Every row names its estimate or change-order line. A need with none says so as its reason ("No estimate line: link one"); `[ESTIMATE LINE]` in the mock marks the five rows where the build showed only "Material".
- Phone: cards with labelled Quantity, On Site, Order By; stock and last price on the row; pick lines, then one sticky bar with Ask for Quotes or Order.

**Quotes** (Needs You 0 today)
- What: what things cost: requests out to vendors and subs, and the prices we already know.
- Label: Quotes (Requests for Quote inside a record).
- Holds: RFQs and bids with leveling and award; the receipt price book (from Price Watch). Prospects and Sourcing Research move to Vendors.
- Who and why: Chen ("which quotes am I waiting on, and is this price fair?"); the PM for sub bids.
- First screen: requests that need a chase or a leveling; empty today, so it links the two subs over $2,500 with no bids (on the Buy Board, not copied).
- Numbers: one count, requests whose next step is yours. Savings This Month goes to Reports.
- The +: New Request for Quote, starting from lines; the foreman's scope check runs beside it, never as a lock; Edit, Chase and Cancel stay with Chen.
- Phone: request cards with Budget, Quotes In, Due; vendor rows of 44px.

**Orders** (Needs You 8)
- What: every purchase order and store run from issue to paid, with the claims, returns and credits that hang on them.
- Label: Orders.
- Holds: POs, store-run receipts, vendor issues and credits (the plan's Issues & Credits folds in here); Client Funds goes to Reports › Cash (CX2).
- Who and why: Chen and the controller ("where is money leaking or owed back?"); the owner only through escalations on Today.
- First screen: Window Works +$3,800 over PO-2026-044; Tino $8,000 paid before delivery; range damaged; faucet return $1,880 (11 days); $126 credit to confirm; zellige $551 window closed; $215 credit memo with nothing behind it; $343 paid above best price.
- Numbers: Needs You 8; Owed Back $2,419 (3 returns); Over the Order $3,800; Committed, Not Yet Billed $39K. Each tile opens its rows.
- The +: New Purchase Order, from lines first; a blank order stays behind More.
- Phone: order cards with Total, Paid and Expected labelled; the missing invoice copies the assistant chases are a footer, not a count.

**Deliveries** (Needs You 3)
- What: everything on its way to a site, the office or back to a vendor, and the receiving.
- Label: Deliveries (one page; Projects › Deliveries becomes the job's filter, CX3).
- Holds: Arriving, In Transit, At the Office, Late to Site, the promise ledger, returns going back, and our own store runs.
- Who and why: Chen ("will it be there when the crew needs it?"); the foreman and Alex receive from it.
- First screen: two orders promised after they are needed (PO-2026-048 9/18 for 9/2; PO-2026-047 10/5 for 10/2) and Alex's route to approve, which buys blue tape that is in stock.
- Numbers: 3. Reconfirm drafts appear 48 hours ahead and count only then.
- The +: log something that arrived with no order.
- Phone: Receive is a sheet; the count starts empty; Good, Short, Damaged or Wrong; photograph the slip; Short or Damaged opens a claim on the order.

**Vendors** (Needs You 4)
- What: one record per supplier and sub: papers, terms, and everything bought from them.
- Label: Vendors.
- Holds: vendors, their insurance, W-9, license, terms and performance (Performance becomes columns); Suggested (Prospects, Sourcing Research) is a filter.
- Who and why: Chen before an order or a site visit; billing before a payment.
- First screen: Window Works blocked (insurance lapsed 8/15); Alberto M Plumbing's W-9 before AMP-311 ($9,800) is paid; Tino (order open, no insurance shown); Diamond Appliances (delivers inside).
- Numbers: 4. "No Certificate 7" goes: under the COI rule only those coming on site or inside need one.
- The +: New Vendor, filled from a mail or a card photo.
- Phone: insurance, W-9 and paid on every row (the census found the phone dropped insurance).

**Stock** (Needs You 1)
- What: what the firm owns and where it is: warehouse, truck or a site.
- Label: Stock.
- Holds: consumables and tools; the log is per item, one tap down.
- Who and why: Chen ("use what we have before buying"); Alex picks from it on the Route; the foreman sees his site's tools on Site.
- First screen: PEX fittings at their reorder point. Below, with no count, Wanted by a Need: 18 rolls of blue tape and 12 sheets of Type X that today's needs could use (the pick is decided, and counted, on the need's Buy Board row).
- Numbers: 1 (review, 11-03: was 3, which counted the tape and the drywall a second time).
- The +: New Stock Item, Count a Shelf, Move a Tool.
- Phone: name, quantity and where on every row; filters All, Materials, Tools, At a job.

## 3. Old page or tab, and its new home (nothing reachable today is lost)
| Today | New home |
|---|---|
| Buy Board › To Buy and its chips (All, To Acknowledge, Late, Order This Week, Waiting on Quotes) | Buy Board sections; Waiting on Quotes is a Waiting on Someone Else row |
| Buy Board › Arriving | Deliveries (radiator valves, marked ordered with no order, stay on the Buy Board) |
| Buy Board side panel (line budget, committed, last 3 buys, at the shop) | the desktop need panel; on the phone, the row and its record |
| Buy Board › Cost by Line | Projects › job › Budget, by estimate line (11-03) |
| Buy Board › Analysis (FF&E savings, markup, funded by) | Reports, a saved report for the owner and controller (CX6); its "7 rows on no estimate line" feeds Selections and the job's Budget |
| FF&E Buying Tools › status tabs | To Buy and Late: Buy Board. Flagged: Orders. In Transit and At the Office: Deliveries. Everything: Selections |
| FF&E › New Buy Run | Buy Board multi-select, one order per vendor |
| FF&E › Credits to Confirm, Returns | Orders › Needs You and Owed Back to Us; the boxes on Deliveries › Going Back |
| FF&E › Clipper Access, Link to Schedule | Selections' + (clip); need dates read from the schedule, an assumed date marked on the row |
| Quotes › Requests and the RFQ record | Quotes |
| Quotes › Prospects, Sourcing Research | Vendors › Suggested |
| Quotes › Price Watch: price book; Cheaper at Another Store cases | Quotes › Prices We Know and every Buy Board row; the cases go to Orders › Needs You |
| Price Watch: detector precision, thresholds; Savings This Month | Company and Settings › Approval Rules (owner); Reports |
| Orders tiles: Late to Site, Not Issued, Flagged, Open Commitment | Deliveries; Orders filter Draft; Needs You; Committed, Not Yet Billed |
| Orders › Order Documents and Promises; Promise Ledger | papers: the footer the assistant chases; promises: Deliveries; Bills on Hold: Accounting › Bills and Payroll, linked from the order |
| Orders › Client Funds Waiting to Be Spent | Reports › Cash (controller), and per line on the job's Budget |
| Orders › Run Matching | runs on its own; results arrive as Needs You rows |
| Deliveries (= Projects › Deliveries) | Deliveries; the job's Purchasing tab filters it |
| Vendors tiles (Blocked, No Certificate, Expiring, Bank Changes, Open Balance); Performance | Needs You rows; a bank change goes to the owner's Today; Open Balance to Bills and Payroll; Performance as columns |
| Stock tabs (All, Tools & Machinery, Stock, Low Stock, On This Job); its tiles; Move / Adjust | filters; Needs You; the + menu |
| Purchasing overview `ovbuy` (controller) | Buy Board; the controller's Purchasing opens on Orders |
| Projects › Materials (job, 6 tabs) | the job's Purchasing tab: this menu's lists filtered to the job (11-03) |

**Count:** before, 9 pages and 19 tab screens (plus Materials' 6 on the job); after, 6 pages and no tab rows.

## 4. Who sees what
- **Coordinator:** all six, in the approved 11-03 order (Buy Board, Orders, Quotes, Deliveries, Vendors) with Stock last, and the counts above. No Design menu. Phone bar: Today, Buy Board, Deliveries, Messages.
- **Everyone else with the menu (PM, owner, billing, controller):** the five approved items; Stock is the coordinator's and the driver's register, and its signal reaches the rest on the Buy Board row, the Route and the job's Site.
- **PM:** the menu, opening on his jobs; mostly the job's Purchasing tab. Rows waiting on him (4 material splits) reach his Today.
- **Owner:** the menu, no counts; Today carries only escalations (Window Works' $3,800, a bank change, a claim past its deadline).
- **Foreman:** no Purchasing menu. He asks from Raise and receives from Site's "Coming to Site" with the same Receive sheet.
- **Driver:** no menu. Route is fed by Deliveries (store runs, pickups, returns) and Stock picks; Receipts become store-run orders.
- **Billing, controller:** Vendors (W-9, terms) and Orders (the money rows); vendor bills stay in Accounting.

## 5. Calls I made, and why
1. **Six pages, not the five on the 11-03 phone menu.** Stock is a different noun (what we own), with its own count-and-move work. Its signals reach the Buy Board row and the Route, but the register needs a home. Fold it if Alan prefers five.
2. **Issues & Credits folds into Orders** (PROCUREMENT_PLAN §4 had a seventh page). A claim belongs to an order and a vendor; one home.
3. **Needs You counts only your next taps.** Rows waiting on others say who, with no number (question 7). Hence 9, not today's 17.
4. **An ordered need leaves the Buy Board.** Late promises (PO-2026-047, PO-2026-048) live on Deliveries, so one record has one list.
5. **The price book sits under Quotes,** the page about what things cost, and on every row.
6. **Menu groups carry no number;** each page does (one style, equal to its rows).

## 6. Found while reading the build (what the checks did not check)
- **Stock is not checked before buying.** 18 rolls of blue tape and 12 sheets of Type X are on the shelf. Meanwhile today's route buys tape and the GWB need reads "No price yet" (expert finding 12, still true).
- **"Marked ordered with no order behind it"** on Appliances, Insulation and Radiator valves. The tile says "1 arriving"; nothing is coming.
- **One label, two numbers.** "11 missing a W-9" beside a W-9 column that reads "—" for all 12; the rail's Purchasing 17 against what is truly the coordinator's.
- **One clock.** Selection checks and the range claim are stamped 2026-10-29 to 11-02 on a 9/3 demo day (see design/SPEC.md §6).

## 7. Self-review against QUESTIONS.md
| Page | 1 What | 2 Label | 3 One home | 4 Who | 5 Record | 6 First screen | 7 Numbers | 8 + | 9 Phone | 10 Few | Still weak |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Buy Board | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | Phone Needs You runs about 3 screens; quantities missing on 5 needs ([QTY]: the build has none) |
| Quotes | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | Nothing real to show today; vendor and bid figures in the asked state are placeholders |
| Orders | pass | pass | weak | pass | pass | pass | pass | pass | pass | pass | Store runs as orders do not exist yet; the receipts live only in Price Watch until P5 |
| Deliveries | pass | pass | pass | pass | pass | pass | pass | pass | pass | pass | The route also shows on Chen's Today (same item, Today's filter, one count) |
| Vendors | pass | pass | pass | pass | pass | pass | weak | pass | pass | pass | Diamond and Tino rest on the COI rule (inside or on site) as I read it; trades are blank in the data |
| Stock | pass | pass | pass | pass | pass | pass | pass | pass | pass | weak | A sixth page against Alan's five (call 1) |

Revised during review: the desktop Buy Board's Job and Line merged into the Need column (eight columns did not fit beside the panel).
Phone targets raised to 44px (two segmented switches and three inline links). The Owed Back rows were made to sum to $2,419.
Checked by rendering each screen at its width: no sideways scroll at 390, one blue at most per screen, every handler runs.

## 8. Chief of staff review (11-03, overnight, under Alan's "keep doing this till it's done")
**Verdict: build after the must-fix list below.** The six-page shape, Needs You first, filters for tabs and buying from the line all
follow the approved job pattern. Grades (of the ten questions): Buy Board 8, Quotes 8 (thin evidence: nothing real out today),
Orders 8, Deliveries 8, Vendors 7, Stock 8.

**The four open calls, decided as Alan would (logged in docs/DECISIONS.md, 11-03):**
1. Stock stays, as the sixth item, last, for the coordinator and the driver only; every other role sees the approved five. It is
   another noun (what we own), and "buying what is in stock" is one of his named leaks, so the register needs a home; its signal is
   on every buying row, so nobody else needs the page.
2. Issues & Credits folds into Orders. A claim belongs to an order and a vendor; store runs become orders, so a card claim has a home too.
3. An ordered need leaves the Buy Board, and late promises live on Deliveries, with two conditions: a line with budget left (the
   fourth rough-plumbing buy) stays on the Buy Board for what is left, and a promise later than the need date reaches the PM's
   job and Today the day it is known.
4. Agreed (Design call): no Design menu for the PM; and none for the coordinator either, so it was taken off Chen's menu here.

**Fixed in the mock-up during review:** the menu and rails follow the approved order; Stock counts only its own work (1, not 3);
Owed Back's rows now show $1,880 + $413 + $126 = $2,419 (the zellige row showed $551); Committed, Not Yet Billed shows $38,721,
its rows' sum, not $39K; the W-9 column now agrees with "11 of 12" and the footer no longer claims nothing was paid without one;
Order By shows dates, not weekdays ("Tue, passed"); the five "Material" rows are marked `[ESTIMATE LINE]`; "Move the Task" is now
"Ask the PM to Move It" (the schedule is the PM's); approving tape from stock adds the warehouse stop.

**Must fix before build:**
1. Desktop multi-select. The desktop Buy Board's check boxes do nothing and there is no picked-lines bar. Build it as on the phone:
   pick lines, one bar, Ask for Quotes or Order, one order per vendor and job.
2. One decision, one count. Today's blue tape is counted on the Buy Board (Pick From Stock) and again in the route approval on
   Deliveries. Rule: an item already on a route counts once, in the route approval; its Buy Board row reads "On today's route"
   with no count. Re-count the Buy Board and the menu after.
3. The estimate line on every need. Five needs show only "Material". The build must carry the line or show "No estimate line" as
   the row's reason (it is a back-end gap, not a label).
4. Vendors' Paid column. Window Works, Tino, Nemo Tile and Satish show money paid with no W-9; Alberto M Plumbing shows $9,800
   paid on a bill that "cannot be paid". Re-read the build: if paid, it is a 1099 and backup-withholding gap for the controller's
   Needs You; if billed, the column is mislabelled.
5. Committed, Not Yet Billed is computed from payments in the mock. Use bills, through the one "paid" (PROCUREMENT_PLAN P5).
6. Orders' Draft filter (the old Not Issued tile's home) is missing from the chips.
7. Store runs as orders do not exist yet; Orders' "every order and store run" is not true until P5. Say so on the page until then.

