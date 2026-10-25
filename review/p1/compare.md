# Procurement P1: the Buy Board against Alan's mockup (procmock, approved 2026-10-24)

Screens in this folder, taken at 1440x900 and 390x844 by tests/buyboard_test.py (d1, d2, p1 to p4) and by hand
(u_chen_*, u_alan_dash_desk). "Matches" means the mockup's inline style is the style on the page (the CSS is in
src/buyboard.js, copied from the mockup's values); checked items are asserted in tests/buyboard_test.py.
The demo data is the seeded 121 State / 206 Lenox jobs, not the mockup's invented Linden St / Hudson Loft rows.

## 1. Phone, To Buy (p1_tobuy.png, p2_two_picked.png vs Main.dc.html)
| Mockup element | Result |
|---|---|
| Header: menu, "Buy Board" 22px/700, 44px gray search and filter | The app's own header keeps the menu and the title ("Buy Bo…" is the app header's truncation); the page row carries the 44px search and filter buttons. The page's own h2 is hidden by the app's phone rule, so the late pill ("16 late", red) leads the row. |
| Two-tab segment "To Buy N / Arriving N", #F1F3F6, 36px tabs, white active | matches [checked: tab count equals the rows] |
| Sections LATE (red) / ORDER THIS WEEK / WAITING ON QUOTES, 12px caps with counts | matches; a fourth section, LATER, holds the rest (the plan's four sections). [checked: the sections hold every row] |
| Rows in one white 14px card, #ECEEF2 ring, 44px pick box, 16px/600 title | matches [checked: picks are 44x44] |
| Line 2 "project · qty · line" | matches; the line reads the estimate or CO number ("EST-2026-014", "CO-2026-001"), "FF&E, Primary bath", "Material" for a material with no line, "No line yet" for a request |
| Line 3 the day, red/600 when late ("Order by Fri, passed") | matches; a late promise reads "Promised 9/25, needed on site 9/10" |
| One chip per row (red / amber / blue) | matches; the chip is the reason that matters most (no order behind it, decision, asked from the site, no sub contracted, stock, quotes, no material portion, no price) |
| Pick bar: "2 lines picked", outlined Ask for Quotes, blue Order 2 Lines, above the bottom bar | matches [checked: Order 2 Lines is the one blue button]; the bar is fixed just above the app's bottom bar |
| Bottom bar Today, Chat, Tasks, Buy Board with a red badge | matches; the badge is the one late count (16 in the demo), the same number as the rail [counts_lint] |
| Remaining | The app's sub-tab strip (Buy, Buy Board, Quotes, Orders, More) stays under the header on the phone; the mockup does not draw it. A card body opens the need as a sheet with its steps (p3_need_sheet.png); the mockup has no sheet. "FF&E Buying Tools" at the foot opens the old FF&E buy runs, returns and credits until P4. |

## 2. Phone, Arriving (p4_arriving.png vs PhoneArriving.dc.html)
| Mockup element | Result |
|---|---|
| Sections LATE / TODAY / NEXT 2 WORKING DAYS | matches; LATER and NO DATE PROMISED follow, so the tab count equals its rows [checked] |
| Row: what, "vendor · project · PO", status line, one 44px outlined action | matches [checked 44px]; the action is Chase (late), Receive (today) or Open |
| "Reconfirmed Mon 9:10" / "Not reconfirmed" | shown only from the follow-ups log: "Reconfirmed <date>" when a reconfirmation was sent, "Reconfirmation drafted", or "Not reconfirmed" inside two working days. No Reconfirm button (P3). |
| Blue "2 deliveries … not reconfirmed. Review 2" banner | not built (P3 drafts the reconfirmations) |
| Remaining | The demo has one arriving line today (radiator valves, no date promised): Tino's flooring and Carlos's millwork are promised after their need-by, so by the one rule they are Late on To Buy, not Arriving. |

## 3. Desktop (d1_buyboard.png, d2_panel_late_promise.png vs Desk.dc.html)
| Mockup element | Result |
|---|---|
| "Buy Board" 24px/700, To Buy / Arriving segment, 280px search, outlined button right | matches; the outlined button is FF&E Buying Tools (New Order belongs to P2's one order sheet) |
| Chips All / Late (red) / Order This Week / Waiting on Quotes, then Project / Vendor / Trade | matches [checked: each chip equals its rows]; the filters are selects styled as the chips |
| Grouped rows: pick, Need and Line, Project, Qty, Need By, Where It Stands | matches; a selected row has the #F5F8FF ground and the 3px blue edge |
| Side panel 380px: ref line, title 20px, red late box, blue "Proposed" box, the money grid, WHAT HAPPENED, blue button and two outlined | matches in layout. The red box says "N days late to the site" and why. The blue box reads "The choices" (Expedite, another vendor, move the task, with the Standard line); the mockup's priced alternative ("Ceramic Supply has 200 sf at $4.10") needs vendor stock and price feeds, which P6 brings. The grid shows Line budget, Committed, Last 3 buys, At the shop, Asked by; "Open claim" waits for P4. |
| One blue button | matches [checked]; while lines are picked, the pick bar's Order N Lines is the blue one and the panel's turns outlined |
| Rail: PURCHASING Buy Board 3, Quotes, Orders, Deliveries, Issues & Credits, Vendors, Stock | The app's rail keeps its groups; Purchasing's sub-tabs read Buy Board, Quotes, Orders, Deliveries, Vendors, Stock [checked]; Issues & Credits joins in P4. The Purchasing badge is the late count. |
| Remaining | no tiles on the board (the old Late to Order / Red Flags / No Price tiles are gone: the chips are the counts) [checked] |

## 4. Beyond the mockup, for the review
- Today (u_chen_home_*): the coordinator's Do Now lists the late needs with one verb each: Order (to buy), Fix (a late promise: Expedite, Other Vendor, Move the Task), Decide (held by a decision), Ask for Bids (a sub scope with no sub). The driver's route is an Approvals card, "Approve Alex's route", due before the van leaves.
- The PM (u_alan_dash_desk.png): Buying on This Job on the job's Overview (late needs, open orders), and the late needs on his own jobs on Today.
- The order picker (Which Lines?) shows each line's budget left after the orders already on it, its vendor error scrolls into view with a toast, and its ticks are 44px.
