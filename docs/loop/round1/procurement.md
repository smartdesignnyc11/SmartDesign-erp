# Round one: procurement (Chen, coordinator)

Sources: two local turns on the J5 checkpoint (world `r1_coord`, app day Fri 9/4, phone then desktop, 160 actions), the page walk (47 of 47 census screens, both devices) and one live turn (`r1_live_coord`, phone to desktop to phone, about 55 actions). Diaries: `sim/runs/r1_coord/diary/u_chen.md`, `sim/runs/r1_live_coord/diary/u_chen.md`; conductor notes `docs/loop/round1/turns/coord_t1.md`, `coord_t2.md`.

## 1. The journeys

**J5, get three quotes (budget 30 taps / 20 min).**
- **Result:** FAIL on both devices. No RFQ reached a vendor, no quote was recorded, nothing was awarded.
- **Local, desktop:** about 45 taps and 55 minutes. Three of the 45 taps' worth were New Vendor forms at 7 steps each, because the yards Alan named that morning were not on file. Phone: 4 taps made the RFQ, then it was stuck.
- **Live:** the phone made RFQ-2026-001 from two lines in 4 taps (the first tap was dead); the desktop showed it within a minute; neither device let me finish it.
- **Where it broke:**
  - Ask for Quotes (on the Buy Board and on New RFQ) commits in one tap with no form: no vendors, no item quantities, no need date. It goes straight to Foreman Review.
  - In Foreman Review the coordinator has no Edit, Send, Cancel or Chase. The duplicate RFQ-2026-001 could not be killed.
  - Lines are "1 ls"; the 60 studs, 12 2x6 and 6 CDX have nowhere to go.
  - The need date is assumed ("on site by 9/11"; studs were 9/8).
  - I sent the six RFQs from my own mailbox. The app still says "not sent yet".
- **What I checked:** each RFQ line is linked to its estimate line (yes); three vendors reached (only outside the app); the lead time asked (in my mail only).
- **Grade: 3.** It stays under 9 until the coordinator can build, send, chase and level an RFQ herself, with the foreman's check as a parallel step and not a lock.

**J6, buy it (budget 25 taps / 10 min, phone).**
- **Result:** phone, the start passes (the live sticky bar "2 lines picked · Ask for Quotes · Order 2 Lines"); the finish fails. Desktop: partial.
- **Live:** FM12-1 to Ferguson was drafted on the phone and issued on the desktop. That took about 20 actions and 6 minutes across the switch, against a phone budget of 25 / 10. It did not stay on the phone.
- **Local:** the Order sheet took one item only (1 ls at $1,100), so there was no PO with several lines.
- **Where it broke:**
  - The line link is not carried from a Buy Board line ("1 line is not linked — link it before approval").
  - "$2,340 not covered" stayed on the PO after I linked it.
  - A $2,548 PO issued with no second person, no three-quote or sole-source prompt, and no price against last time.
  - The stock check is missing: the warehouse held the wire, boxes and Type X I needed, and the Buy Board said "At the shop: none".
  - The vendor email has no address, no drawings and no Send.
- **Good:** the order held the faucet back because the record says unlacquered brass and Ferguson's page says chrome. That is the lesson from the tile that came wrong twice, working.
- **What I checked:** committed against the line; W-9 (missing, and the app said so); COI (not checked by the PO).
- **Grade: 4.** Under 9 until the PO knows the line, the stock, the last price and the quote rule before I press Issue, and sends itself to the vendor.

**J7, receive and match (budget 15 taps / 8 min, phone).**
- **Result:** FAIL. Nothing arrived in the local world, so I walked the receiving screens on both devices.
- **Phone:** Deliveries lists Tino and Carlos as "0 lines". Receive opens the title and the item, with no quantity, no Received, no short or damaged, and no slip photo.
- **Desktop (job view):** the quantity starts at the full ordered amount and "Received" is the blue button. One careless tap receives everything, and the bill then matches clean.
- **Matching the credit:** "Apply" matched the Bedrosians $214.50 credit memo (issued 8/31) to a card credit dated 8/25.
- **What I checked:** the receipt records quantity and condition (it cannot); the bill is held at what was received (nothing to hold against).
- **Grade: 2.** Under 9 until a short, damaged delivery can be received on the phone in under a minute and the bill is held at what arrived.

## 2. The questions, answered for my day

1. **Information I could act on.** Half. The Buy Board row (need, order-by, why it is stuck) and the side panel (line budget, committed) are right. The price book, the stock, the card buys and the quotes I asked for are not on that row.
2. **Right place.** The Receipt Price Book is in Quotes > Price Watch; I looked on the Buy Board line. Returns and credits are inside FF&E Buying Tools; I looked in Orders. Tino's double invoice is on the PO page; I looked at Orders > Flagged. The COI for a sub not on file had nowhere to go.
3. **Too much, or not for me.** The owner's flag-precision table and thresholds in Price Watch. Cost by Line and Analysis (job-cost reports) under the Buy Board. Seven near-identical "thin category" cards. Subcontract buy-outs padding my material Late list.
4. **Sub-pages for one job.** One purchase took Buy Board, Quotes, the RFQ, Vendors, New Vendor ×3, Stock, Orders and the PO: about 10 pages. The Buy Board, Materials and FF&E Buying Tools should be one Buy Board, with the RFQ and the PO opening in a side sheet; Arriving belongs in Deliveries; Prospects and Sourcing Research belong together.
5. **Outside the app.** Six RFQs by mail, the stud and wire quantities in my head, phone calls to Angel and Alex. Tasks for the driver had to be made by hand. The insurance chase for Tomas Restoration was by mail.
6. **Numbers I trust.** I trust the line budget, committed $ and Open Commitment. I do not trust Flagged Orders (it missed Tino), "Paid above best price $0" (it missed a 5x buy), "Materials: All on site" on a job with nothing bought, or any count that changes with the chip I press.
7. **Mistakes and the tap I fear.** I could not cancel my own duplicate RFQ. The tap I fear is the blue "Received" with the full quantity already typed in, and "Apply" on a credit match.
8. **Hand-offs.**
   - To Angel: the RFQ check sat all day, with no nudge and no override.
   - To Alex: Move / Adjust on stock put nothing on his list, so I made the task by hand. The live Look-Ahead shows the run as my task.
   - To the vendor: the email draft has no address and no Send.
   - To billing: the reimbursable link on the PO landed.
9. **A new hire.** Stopped by "Foreman Review" with no way out, by "1 ls" lines, by "Quote out" next to "not sent yet", and by a menu entry that reopens the last record instead of the list.
10. **What I can see or miss.** I see nothing I should not. I miss the vendor's insurance on the phone row, and stock location on the phone.
11. **Would I switch tomorrow.** No. The one thing: receiving and the three-way match must work on the phone, with the bill held at what arrived.
12. **The AI.**
    - **Did well:** caught the finish mismatch; found Brooklyn Lumber in my mail; caught Tino's double invoice on the PO.
    - **Should have:**
      - read the vendor quotes and replies into the RFQ;
      - told me the wire was on the shelf;
      - flagged the 5x drywall buy and the credit dated before its memo;
      - drafted the chase to Angel.
    - **Ask:** answered the record back instead of "how do I cancel"; answered about shower glass when I asked for a card line; left RFQ-2026-001 out of "what is stuck on Angel" (live).
    - **Should not have:** it started RFQs and sent them to the foreman in one tap, without the form.

## 3. Findings, by class

**A. Receiving and the three-way match (J7)**
1. **Phone receiving is a dead end.** Deliveries on the phone shows "0 lines"; Receive has no quantity, Received, short, damaged or photo. On the desktop the quantity is prefilled to the full order and Received is blue.
   - Fix: line quantity starts empty; short and damaged sit on the line with a slip photo; Received is under the thumb.
   - S1. Blocks J7 steps 1 to 3.
2. **No partial receiving and no claim on the line.** A 1 ls millwork PO cannot record one short cabinet. "Report a Problem" is separate from the line.
   - Fix: receive by piece; the claim opens from the line with a 48-hour clock.
   - S2. Blocks J7 step 3.
3. **Credit matched to the wrong card line.** The Bedrosians $214.50 memo (8/31) was matched to a card credit dated 8/25, before the memo existed.
   - Fix: refuse or flag a match dated before its source document.
   - S1. Blocks J7 step 4.

**B. Leaks the PO page knows but the lists do not (money)**
4. **Tino's double invoice is missing from the lists.** Two invoices on PO-2026-047, both over the PO, plus $8,000 paid ahead of "100% on delivery". This is missing from Flagged Orders, Bills on Hold and the Orders row.
   - Fix: one flag engine feeds the PO, the list, the tile and Today.
   - S1. Blocks J7 step 2.
5. **The overpayment is not held.** Live: Window Works paid $67,000 against a $29,700 PO (+126%) shows as a row note only.
   - Fix: hold, and escalate to the controller in the Standard format.
   - S1. Blocks J7.
6. **A card buy is not tied to its need.** Brooklyn Lumber 88412, $2,140.50 for 31 sheets (about 5x the price book), was paid 9/1. The same need still reads "Order This Week, No price yet", and Price Watch says $0 paid above best.
   - Fix: match card lines to Buy Board needs; run the price check on card buys.
   - S1. Blocks J6 (no double buy).
7. **Returns and credits are hidden.** Returns $2,419 and Credits to Confirm 1 sit inside FF&E Buying Tools.
   - Fix: move them to Orders, with a credit-not-received age.
   - S2. Blocks J7 step 4.

**C. The coordinator cannot finish her own work (J5, J6)**
8. **The RFQ is a one-tap lock.** RFQs are made in one tap with no form and locked in Foreman Review: no Edit, Send, Cancel or Chase, and duplicates are not stopped.
   - Fix: a form first (vendors, items, quantities, need date, due date); the foreman's check runs in parallel; Cancel and Chase for the owner of the RFQ.
   - S2. Blocks J5 steps 1 to 3.
9. **RFQ lines cannot be itemised, and the facts are wrong.** Lines are "1 ls". The record says "no material budget on this line" while Cost by Line shows $1,100 and $1,800. The need date is an assumption.
   - Fix: item rows under the line; the budget read from the line; need dates from the schedule, marked when assumed.
   - S2. Blocks J5.
10. **The PO skips the Standard's checks.**
    - A $2,548 PO issued with no second approval, no three-quote or sole-source prompt over $2,500, and no price against last time.
    - The line link is lost when ordering from the Buy Board.
    - "Not covered" stays stale after linking.
    - The header says Ship to: Office while the field says Job site.
    - Fix: run the checks before Issue; carry the line link from the board.
    - S2. Blocks J6 steps 1 and 4.
11. **The vendor email cannot be sent.** It has no To (no contact on file), no drawings attached, no Send, and does not ask for the missing W-9.
    - Fix: pull the contact, attach the job's drawings from Drive, send or queue it, ask for the W-9.
    - S2. Blocks J6 step 5.

**D. The Buy Board does not know what the firm knows**
12. **Stock and the price book are ignored.** The side panel says "At the shop: none / Last 3 buys: none" while the warehouse and the price book have the items; 18 rolls of blue tape sit on the shelf while Angel's blue tape request is Late.
    - Fix: stock and the last three prices on every row and on the RFQ and PO sheets.
    - S2. Blocks J6 step 3.
13. **214 Lincoln is half on the board and the job says all is well.** Its drywall and electrical lines are missing from the board; with no schedule there are no order-by dates; the job page says "nothing late, All on site, Needs You: Nothing".
    - Fix: every estimate line on the board; say plainly when no order-by date can be computed.
    - S2. Blocks J5 and J6.

**E. One noun, two lists; one label, several numbers**
14. **Materials and the Buy Board disagree about the same records.** Insulation reads "Ordered" on one and "no order behind it" on the other; LVP reads "Quoted" and "No price yet". FF&E Buying Tools is a third buying list.
    - Fix: one list, with job and FF&E as filters.
    - S2.
15. **Counts move.**
    - Buy Board chips recount inside the active chip.
    - 121 State shows 15 late, 5 at risk, 15 late and 17 on one screen and the board.
    - Today live: 42, 50, 43, 42.
    - The "Vendors 1" badge counts nothing named.
    - Open Flags 2 sits over a detector table of zeros.
    - S2 / S3.

**F. Phone, sync and navigation**
16. **The phone Buy Board gets stuck.** A desktop chip filter carries to the phone, which has no chips: "2 of 41 shown", the filter sheet says All, and To Buy does not clear it.
    - S2. Blocks J6 on the phone.
17. **Sync costs taps and hides saves.** The phone never shows its save status. Sync re-renders ate three taps (Ask for Quotes, a PO row, Draft Email) and one menu go landed on Orders. Sync itself was fast: under a minute every time, nothing lost.
    - S2.
18. **Menu entries do not land on the list.** They reopen the last sub-page: Quotes opens the last RFQ, Orders opens the last PO, and Quotes on the phone opens Price Watch. Deliveries says "this job" without naming it.
    - S2.
19. **Wrong records and wrong places.** On the phone, PO-2026-048 opened PO-2026-041. Today-card links land on the Messages list. RFQ lines will not expand on the phone. Raw ids show ("estimate:es1:l7") and controls are unlabeled ("(rfql L1)").
    - S2 / S3.
20. **Phone rows drop the column that matters.** Vendors loses insurance, Stock loses where, Orders loses amount and date, Materials loses vendor and ETA. Orders tiles lose their reason line.
    - S3.

**G. Vendors and compliance**
21. **Blocked vendors and insurance chasing.**
    - Tino is Blocked but his row reads "attention", with no reason.
    - There is no Request COI or W-9 on the row or in bulk (12 of 17 have no COI).
    - A sub's COI (Tomas Restoration) cannot be filed because the sub is not on file.
    - Prospects are stale after vendors are added.
    - Performance (lead and damage rates) is a separate page that covers only the FF&E vendors.
    - S2. Blocks J6 (COI before site).

**H. The assistant**
22. **Ask reads the record back instead of answering.** Examples: how to cancel; a card line answered with shower glass; half of "what is stuck on Angel" (live).
    - Fix: answer the question; act through proposals.
    - S2.

## 4. Per-page verdicts (page walk, 47 of 47 screens)

| Page | Verdict | Too much / not mine | Missing |
|---|---|---|---|
| Purchasing > Buy Board (To Buy, chips) | keep, the hub | sub buy-outs in Late; no column heads | price, stock, card buys on the row; stable chip counts; phone filter visible |
| Buy Board > Arriving | merge into Deliveries | one radiator row with no order | every open PO, promise against need |
| Buy Board > Cost by Line | move to Projects > Costs | heading reads Buy Board; "profit now 100%" | - |
| Buy Board > Analysis | move to Reports | jargon lead | - |
| Buy Board > FF&E Buying Tools | merge into Buy Board and Orders | a second Buy Board | returns and credits belong on Orders |
| Quotes > Requests | keep, rebuild the row | "Angel checks" four times | vendors, quotes in of asked, due date, Cancel/Send/Chase |
| Quotes > RFQ record | keep | raw ids, unlabeled controls | items with quantities, vendors, actions while in review |
| Quotes > Prospects | move to Vendors (Suggested) | seven repeated cards | refresh when vendors are added |
| Quotes > Sourcing Research | merge into Vendors (Suggested) | a tab for one button | - |
| Quotes > Price Watch | split: price book to the Buy Board and PO; cases to Orders; precision and thresholds to the owner | owner tables | card buys checked |
| Purchasing > Orders | keep | five New PO buttons in Client Funds | PO-page flags on the list; bills on hold; received against billed |
| Purchasing > Deliveries (= Projects > Deliveries) | keep, one page | - | phone receiving, empty quantities, short/damaged/photo, job named |
| Purchasing > Vendors | keep | W-9 count inside Open Balance | Blocked reason, Request COI / W-9, insurance on the phone |
| Vendors > Performance | merge into Vendors as columns | - | non-FF&E vendors |
| Purchasing > Stock (5 tabs) | keep | a tab "Stock" on a page "Stock" | unit cost, order from Reorder Now, job picker on On This Job, where on the phone |
| Projects > Overview, Buying on This Job | keep, top of the job | four numbers for "late" | "cannot compute order-by" when there is no schedule |
| Projects > Materials (6 tabs) | merge into the Buy Board for me; keep for PM and foreman | CSV buttons first on the phone | price, line, PO; agree with the Buy Board |

Five to change first: Deliveries, Buy Board, Quotes requests and the RFQ, Orders, Vendors.

## 5. Retest

None this round (first iteration).

## 6. Grades

These grades are valid: I opened 47 of 47 census screens of Purchasing and the job's purchasing pages, both devices.

- **Phone: 4/10.** Picking lines and ordering from the sticky bar is fast and caught a wrong finish. But receiving is a dead end, the board can get stuck on a hidden filter, and the phone never says whether a save landed.
- **Desktop: 5/10.** The Buy Board, the PO form and the line-link sheet are the right tools. But I cannot send or finish my own RFQ, and the leaks the PO page finds (double invoice, 5x card buy, +126% paid) never reach the lists I work from.

DONE: report written
