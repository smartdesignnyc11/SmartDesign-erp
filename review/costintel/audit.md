# Cost intelligence audit (BACKLOG §1.29 items 1 to 5), 2026-10-20

The Cost Intelligence lane's starting point. App day 2026-09-03, demo seed, read from the running build (master at
39815c3) through the app's own readers. Each item: what exists, what it lacks, what this lane builds on it.

## What exists today

| Piece | Where | What it does | What it lacks for §1.29 |
|---|---|---|---|
| Price watch (§1.8 item 11) | `pwData` / `pwBuild` / `itemPriceHistory`, `PW_DET` | The one price history: PO lines, bills, card lines with a quantity, confirmed quotes. Nine detectors (Paid More Than Before, Quantity Over, duplicates, splits, fees, rare vendor, not delivered, card with no job, use tax). `pwAboveBest` dollars above the best recent price. Same Item? proposals (`pwMatchProps`). | No receipt lines at all: `DB.docs` receipts and the field's `DB.spend[].read.lines` are read but never reach the history. Identity is SKU, else category + normalised words + unit, so "2X4-8 KD STUD SPF" (Home Depot) and "2-in x 4-in x 8-ft Kiln-Dried SPF Stud" (Lowe's) are two items. "Another vendor was cheaper" needs three prior buys and never names a store. |
| Receipt readers | `rcParseText` / `rcRead` (field spend), `trkRead` / `trkNewDoc` (order documents) | Read SKU, description, quantity, unit price, extension, store, total, tax; tie a receipt to its card line (`trkCheck`). | Nothing reads the lines for price. No retailer import. |
| Stock | `stockSpec` / `stockCompare` / `stockCheck` | Matches a request to stock by drywall family, thickness, size, type; else words and numbers. | Fine for stock; no length, gauge, species or pack, so not enough to match across stores. |
| The driver's run and day plan | `STORES`, `runItems`, `startRun` / `closeRun`, `planDriverDay`, `renderDriverPlan`, `renderRunCard`, Office Pickups (`pickupList`) | Store run with a countdown, a shopping list by job, a day plan of warehouse pickups, yard pickups, one store stop, sites by nearest-next, dump runs when the van fills. | Every buy goes to `STORES[0]`. No price per store, no cost of the driver's time or fuel, no delivery windows, no approval, no comparison with receipts. No lumber yard or supply house in `STORES`. |
| Job money | `jobFin` (actual, committed, EAC by line, billed, collected), `ovsAll` (overspend at landing), CATCH `budgetOverrun`, `jobsAtRisk` (margin fade), `analystFindings` | Over budget by code and by estimate line once a record lands; margin fade. | No cash-out-versus-cash-in test per job (a card payment of a bill not yet marked paid is cash that left), no cost-ahead-of-billing test, no line forecast (committed past budget, or measured progress projecting past it). No single list of "jobs spending more than they bring in". |
| Reports lane | `rpCashHtml` (13-week cash), `rpLineRows` (line income to cost), `rpCloseout` + `rpProposeCostBook` (close-out cost factor into `DB.company.costBook`) | Cash forecast, line margin, estimate versus actual at close-out. | `DB.company.costBook` is written on approval and read by nothing in estimating. |
| Item library (§1.18) | `itemLib`, `itemFind`, `itFillSell`, `libFillLine`, `itemProposals` | One picker fills every line; price proposals when the last buy moved 10%. | Unit cost ignores the close-out factor and any benchmark. |
| Brain | `DB.changes` (Company › Changes), `LEARN_EVENTS` / `lnLoop` / `DB.lessons`, `bnIngestServer` | Proposals the owner approves; lessons. | Nothing mines cost: overruns, price outliers, waste. |
| Past jobs | none | — | No close-out record: the demo has four live jobs and no closed one, so there is nothing to benchmark against. |

## What each item needed, and what was built

1. **Jobs spending more than they bring in.** One predicate, `PRED.jobsOverspending`: cash out (every job bank and
   card line, a paid bill no bank line backs, payroll paid) above cash in (client payments); cost to date above billed;
   a line over budget (exactly `ovsAll`, the rule Over Budget already uses) or forecast to go over (committed past its
   budget; measured progress projecting more than 5% past it). Each line names its cause from the records (a bill over
   its PO, a PO past the budget, a card line with no change order) and a fix (Dispute Difference, Draft Change Order,
   Chase Payment, Bill It). Caught for You gets one entry for the parts Over Budget does not carry. Demo: 121 State
   (windows $3,800 over, the bill over its PO; millwork $1,000 committed past budget), 45 Cranberry (construction
   documents projecting $322 over at 46% complete).
2. **Benchmarks.** Close-outs (`DB.closeouts`; six invented brownstones and one condo kept apart) hold measures and
   what each rough trade bought and installed. Material per unit per trade (rough plumbing per fixture and per bath,
   rough electric per device and per 100 SF, sheetrock per board and per 100 SF, taping per 100 SF, framing per LF of
   wall and per 100 SF); median of comparable jobs; a job more than 15% above the median of the others is flagged with
   its cause, split exactly into quantity × waste × price. A running job is flagged when it has already bought more
   per unit than comparable jobs used in total, or pays more than 15% above their prices (121 State's 5/8 Type X:
   20% on price). Feeding estimating: a drafted change in Company › Changes; approved, it lives in the one book,
   `DB.company.costBook.bench`, beside the reports lane's close-out factors, read by `ciCostGuide` for the estimate's
   hints and the item library's fill.
3. **Receipt price book.** Receipt lines join price watch's history (`pwBuild` wrapper, kind "receipt"); identity by
   UPC, then a complete spec (lumber dimensions, length, KD/PT, species; sheet thickness, size, type; cable gauge,
   conductors, length; PEX type, size, length, colour ignored; compound kind and size; packs priced per piece). One
   detector, Cheaper at Another Store, one case per receipt with the store and the saving; price watch's own "another
   vendor" reason is dropped for receipts so a line is never on two detectors. Retailer adapters: purchase-history
   export (CSV) from Home Depot Pro Xtra and Lowe's Pro, e-mailed and photographed receipts; no scraping; none
   connected (the page says what each needs). Demo: nine receipts across Home Depot (two branches), Lowe's, Ferguson,
   a supply house and a lumber yard; four of them tie to card lines already in the feed to the cent (t4, t10, t14,
   ta9). Two cases: $119.60 and $223.65 (the second includes sheetrock 22% above the supply house, $126.00).
4. **Driver routes.** Phase 1: each item on the run's list says which store and what it saves; a cheaper store the
   route skips says it is not worth the extra stop. Phase 2: `ciRouteSolve` picks the store set and the order that
   minimise item cost + route minutes × the driver's hourly cost + fuel, with stock on hand taken from the shelf, yard
   pickups, site delivery windows, van capacity (a second trip when needed) and the dump; `ciRouteNearest` is the
   baseline it must beat. Travel time behind one interface: an offline estimate, or `/api/routes` (platform) calling
   the Google Maps Routes API once `GOOGLE_MAPS_KEY` is set in Netlify (it is not; Alan adds it). The coordinator
   approves; the driver's Route screen shows the approved route with no prices; receipts are compared back.
5. **The brain's weekly review.** Overruns (a trade's last three comparable jobs against the jobs before them),
   price outliers (the same item bought above the best store more than once), waste, vendor delays (broken promises)
   and repeated site questions; each a drafted change with a dollar or hour value; approved rules become lessons.

## What the checks would not have caught, and the check added

- A receipt that ties to nothing: every demo receipt linked to a card line is checked to the cent against it.
- One buy flagged twice (Paid More Than Before and Cheaper at Another Store): the suite asserts one case per receipt
  and that price watch's "another vendor" reason no longer fires on receipts.
- A second price store: the suite asserts there is no `DB.company.costBench` and the approved benchmark is in
  `DB.company.costBook.bench`.
- A route that looks clever and costs more: every route in the bank must cost no more than the nearest-store route.
