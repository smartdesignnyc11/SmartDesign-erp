# Accounting Module Specification

## The ledger that replaces QuickBooks

*SmartDesign Group · Mercer & Bond · Specification v1.0 · 12 September 2026*

---

## 0. Purpose and scope

This document specifies the accounting module of the SmartDesign ERP to the level a developer builds against and an accountant signs off on. When it is complete, QuickBooks is switched off. Nothing is synced to QuickBooks, nothing is exported to QuickBooks, and no report depends on QuickBooks. The ERP is the system of record for every entity in the group, including the general ledger.

It builds on the design work already in the project (`accounting-rd-2026-09-05`, `spend-architecture-2026-09-09`, `financials-audit-2026-09-04`, `hours-to-line-and-payroll-2026-09-09`, `controls-reconciliation-routing-terms-2026-09-10`) and on the working principle behind the whole ERP: every dollar is born as a document with a job, an estimate line and a cost code on it, and the ledger is what those documents post to. Nothing is re-keyed. The machine proposes, a person confirms, the platform enforces.

Scope, in one list: chart of accounts and dimensions; entities and intercompany; periods, books and locks; the posting engine and the posting rule for every document type; manual journals; bank and card feeds with reconciliation; payroll and its liabilities; sales tax and use tax; 1099s; fixed assets; retainage, deposits and WIP; the close; financial statements and the accountant's year-end package; the audit trail; permissions; migration from QuickBooks and the parallel run; acceptance tests.

Out of scope for v1: multi-currency, inventory valuation, multi-book tax basis (the schema carries a `book` field so it can be added), consolidation eliminations as posted entries (consolidation is a view), payroll tax filing itself (see §9 for the provider decision).

## 1. Entities

The group is several legal entities sharing one chart of accounts. Each has its own books, its own bank accounts, its own tax identity and its own year-end package. Entity is a dimension on every journal line, never a separate database.

| Field | Notes |
|---|---|
| `id`, `name`, `legalName` | e.g. `sd` SmartDesign Group, `sdp` SD Plumbing, `sde` SD Electric, one per property or development LLC, `mb` Mercer & Bond |
| `type` | `operating`, `trade`, `property`, `holding` |
| `ein` | stored encrypted, shown last four |
| `fiscalYearStart` | month; all entities calendar year unless stated |
| `basis` | `accrual` (statements) — cash view is derived, see §12 |
| `bankAccounts[]` | ledger accounts of control type `bank` owned by this entity |
| `parentId` | for the consolidation tree |
| `active` | |

Rules. A document belongs to exactly one entity (the one that issues or receives it). A project belongs to one entity; a trade entity working on another entity's project bills it through an intercompany bill (§7). A payment can only be made from a bank account owned by the paying entity. Reports default to the signed-in user's entity scope and can consolidate (§13).

## 2. Chart of accounts and dimensions

One shared chart of accounts across all entities, seeded for a construction group. Accounts are typed so the statements build themselves and so control accounts cannot be posted to by hand.

| Field | Notes |
|---|---|
| `number`, `name` | four-digit numbers, gaps of 10 |
| `type` | `asset`, `liability`, `equity`, `revenue`, `cogs`, `expense`, `other` |
| `subtype` | e.g. `bank`, `ar`, `retainageReceivable`, `wipUnderBilled`, `fixedAsset`, `accumDep`, `ap`, `retainagePayable`, `depositLiability`, `wipOverBilled`, `payrollLiability`, `salesTaxPayable`, `useTaxPayable`, `creditCard`, `loan`, `intercompany`, `directLabor`, `directMaterial`, `directSub`, `directEquipment`, `directOther`, `indirect`, `ga`, `depreciation`, `interest` |
| `normal` | `debit` or `credit` |
| `control` | `bank`, `ar`, `ap`, `card`, `payroll`, `none`. Control accounts accept postings only from the engine, never from a manual journal (the manual journal to a control account is refused with the reason) |
| `dimsAllowed` | which dimensions may appear on lines: job and estimate line are allowed on revenue, COGS, WIP and retainage accounts only; never on cash, AP, AR or equity |
| `parentId`, `active`, `taxLine` | `taxLine` maps the account to the line on the tax return the accountant wants it on |

Seeded structure (numbers indicative): 1000s cash and undeposited funds, 1100 AR, 1150 retainage receivable, 1200 WIP costs in excess of billings, 1300 vendor prepayments, 1400 client escrow (GBL 771-a), 1500 fixed assets and 1590 accumulated depreciation, 1700 intercompany receivable; 2000 AP, 2050 retainage payable, 2100 credit cards, 2200 payroll liabilities (wages, federal, state, city, FICA, SUI, workers' comp accrual, garnishments), 2300 sales tax payable, 2310 use tax payable, 2400 customer deposits, 2450 client funds held for purchases, 2500 billings in excess of costs, 2700 loans, 2800 intercompany payable; 3000 equity, distributions, retained earnings; 4000 contract revenue by category (design, construction, finish materials, plumbing, electrical), 4900 other income; 5000 direct cost by cost type (labor, burden, materials, subcontract, equipment, other) with cost code as a dimension not an account; 6000 indirect field cost; 7000 G&A; 8000 depreciation, interest, other.

Dimensions carried on every journal line, populated from the source document and never typed:

| Dimension | Source |
|---|---|
| `entityId` | the document's entity |
| `projectId` | the document or line's project |
| `cat`, `code` | category and cost code from the estimate line |
| `lineId` | the immutable estimate-line id (`estimate:<doc>:<line>` or `co:…`); splits create children with `parentLineId`; every project has an `unassigned` line for cost that arrives before the estimate |
| `partyType`, `partyId` | client, vendor, employee, entity |
| `sourceType`, `sourceId`, `sourceLineId` | the document and line that produced this posting |
| `custom{}` | any registered custom field flagged GL-impacting (§16) |

This is the NetSuite custom-segment idea without the setup: the estimate line is the segment, so a P&L by line, by code, by client, by entity, or by any custom field is a filter on the ledger.

## 3. Periods, books and locks

| Object | Fields |
|---|---|
| `Book` | `id`, `name`, `basis` (`accrual`), `isDefault`. One book in v1. |
| `Period` | `id`, `fiscalYear`, `n` (1–12, plus 13 for year-end adjustments), `start`, `end`, `status` per entity per subledger `{ar, ap, payroll, bank, gl}` each `open | locked`, `lockedBy/At`, `reopenReason`, `reopenedBy/At` |

Locks bite. A posting dated in a locked subledger period is refused by the engine and the document that tried it is flagged; the user is offered the correction path (§5.4). Reopening requires the Owner and a reason, both stored. Period 13 is open only to manual journals for the accountant's year-end adjustments.

## 4. The journal

| Object | Fields |
|---|---|
| `Journal` | `id`, `entityId`, `bookId`, `periodId`, `date`, `kind` (`posting`, `manual`, `reversal`, `opening`, `accrual`, `wip`, `ic`, `depreciation`, `allocation`), `sourceType`, `sourceId`, `sourceVersion`, `ruleVersion`, `status` (`pending`, `posted`, `reversed`), `reversalOf`, `reversedBy`, `autoReverseOn`, `memo`, `createdBy/At`, `approvedBy/At`, `postedAt` |
| `JournalLine` | `id`, `journalId`, `n`, `accountId`, `debit`, `credit` (cents, integers, exactly one non-zero), `entityId`, `projectId`, `cat`, `code`, `lineId`, `partyType`, `partyId`, `sourceLineId`, `eliminate`, `memo`, `custom{}` |
| `Balance` | materialized on post: `entityId × bookId × periodId × accountId × projectId × lineId` → `debit`, `credit`. Statements read balances; only drill-through reads lines. |

Invariants, enforced at write time and checked nightly: every journal balances to the cent; every line has an account the engine is allowed to post to; dimension rules per account hold; a posted journal is never edited, only reversed; a journal's `sourceVersion` matches the version of the document that produced it, and if the document has since changed in an open period the engine has re-posted (reversal plus new posting, linked); the ledger-versus-engine drift check (re-derive every open-period posting from its document and compare) reports zero differences, and any difference is a red card on the Controls view until explained.

## 5. The posting engine

### 5.1 Principle

Every document event produces exactly one journal through a named posting rule with a version. Rules are pure functions of the document and the configuration (account mapping, tax status, entity). They are deterministic and re-runnable, which is what makes the drift check possible. Once the journal is posted it is the record; the document is the evidence.

### 5.2 Trigger events

A document posts when it reaches its posting state, not when it is created: an invoice when it is sent; a bill when it is approved; a payment or receipt when it is recorded; a bank or card charge when its settlement is confirmed; payroll when the run is approved; a journal when the Owner approves it. Drafts never post. Voiding a posted document produces a reversal dated the void date (or the first open day if the original period is locked).

### 5.3 Posting rules

Amounts are in cents. "Line" means the document line's estimate line and cost code carried onto the journal line.

| Document / event | Debit | Credit | Notes |
|---|---|---|---|
| Client invoice, sent (SOV or items) | AR (gross less retainage); Retainage receivable (retainage held) | Contract revenue by category, by line; Sales tax payable (if taxable status) | Deposit applied on the invoice: debit Customer deposits, credit AR for the applied amount. Freight on items-mode lines posts to revenue with the line. |
| Credit memo | Revenue by line (and sales tax payable) | AR | Only correction path for a sent invoice in a locked period |
| Client payment received | Undeposited funds (or Bank if deposited directly) | AR | Partial payments allocate to invoices then lines pro rata unless the user allocates by hand; the allocation is stored |
| Bank deposit of undeposited funds | Bank | Undeposited funds | Matches the feed's deposit line |
| Customer deposit (money before an invoice) | Bank or Undeposited funds | Customer deposits (liability); residential contracts with the GBL 771-a flag post to Client escrow instead of operating cash | Applied when an invoice is sent (see above) |
| Client funds held for purchases | none posted | none | Computed disclosure per `financials-audit` (reserved = min(collected − spent, budget − spent)); shown on the balance sheet as a memo line, not a posting, because it is a subset of AR collections already in cash |
| Retainage release (client) | AR | Retainage receivable | On the release invoice; passes the lien-waiver gate |
| Vendor bill, approved | Direct cost by cost type, by line and code (or Fixed asset, or G&A for overhead bills); Use tax payable is credited and the same cost debited when the bill is untaxed capital-improvement material | AP (net of retainage); Retainage payable (held) | Three-way match runs before approval; a bill whose PO carried a prepayment debits Vendor prepayments down first |
| Bill credit | AP | Cost by line | |
| Bill payment | AP | Bank | Records `paidByEntityId` and the payment method for 1099 (card payments are excluded from 1099 totals) |
| Vendor prepayment (deposit on a PO) | Vendor prepayments | Bank | Relieved by the bill |
| Retainage release (vendor) | Retainage payable | AP, then Bank on payment | Through the compliance gate (COI, W-9, lien waiver) |
| Card charge, settlement confirmed against a spend record | Cost by line and code (split receipts post one line per split) | Credit card liability | The card register's holder and last-four ride on the line's `custom` |
| Card charge with no spend record | Uncategorised spend (asset clearing) | Credit card liability | Sits on the Controls "money with nobody's name on it" list; reclassified when confirmed |
| Card statement payment | Credit card liability | Bank | |
| Bank charge / fee / interest | G&A or Interest | Bank | Two-tier rule: auto-create proposals for recurring overhead, still confirmed by a person |
| Employee reimbursement (approved) | Cost by line | Reimbursements payable | Paid with payroll or by transfer |
| Payroll run, approved | Direct labor by job, line and code (hours × rate); Burden by job (employer taxes and workers' comp pro-rated by earnings); Indirect or G&A payroll for non-job hours | Wages payable (net pay); each payroll liability (federal, state, city, FICA employer and employee, SUI, workers' comp accrual, garnishments, benefits) | One journal per run per entity; per-employee detail is on the run, not the journal |
| Payroll paid / tax deposited | Wages payable; the liability account | Bank | Matches the feed |
| Accrued wages at close | Direct labor by job | Accrued wages | For days worked past the last pay date; auto-reverses on day one of the next period |
| Received-not-billed at close | Cost by line | Accrued liabilities | From POs received without a bill; auto-reverses |
| WIP at close, per job, gross | Costs in excess of billings (under-billed jobs) | Contract revenue | Cost-to-cost: earned = contract × (cost to date ÷ estimated total cost); under-billed jobs post an asset, over-billed jobs post a liability (debit revenue, credit Billings in excess); never netted across jobs; auto-reverses |
| Intercompany bill (trade entity to GC) | GC entity: Direct subcontract cost by line. Trade entity: Intercompany receivable | GC: Intercompany payable. Trade: Intercompany revenue | Billed at cost; both sides flagged `eliminate`; the markup is a separate period entry so the GC's cost-to-cost percent complete is not inflated |
| Intercompany settlement | Intercompany payable | Bank (GC); Trade: Bank / Intercompany receivable | |
| Depreciation, monthly | Depreciation expense | Accumulated depreciation | Generated from the asset register (§10) |
| Loan payment | Loan principal; Interest expense | Bank | Split from the amortisation schedule on the loan record |
| Owner distribution / contribution | Distributions / Bank | Bank / Equity | Manual journal, Owner approval |
| Opening balances | per trial balance | per trial balance | One `opening` journal per entity, Owner-approved, period 0 |
| Manual journal | as entered | as entered | Owner approval; control accounts refused; `autoReverseOn` optional |

### 5.4 Edits and corrections

In an open period, editing a posted document's GL-impacting field re-posts: the engine reverses the old journal and posts a new one, both linked, and writes a system note (field, old, new, who, when). In a locked period, GL-impacting fields are read-only; the user is offered a credit memo or bill credit, or a reversal-and-repost pair dated the first open day and linked to the source. The document's "sent to client" state already locks invoice content; the period lock is the second gate.

## 6. Bank and card feeds and reconciliation

Feeds are the reason QuickBooks is still open at the firm. Replacing it means the feed lands here and the daily re-pull of the month ends.

| Object | Fields |
|---|---|
| `FeedConnection` | `entityId`, `accountId` (ledger bank or card account), `provider` (Plaid or the bank's direct feed), `externalId`, `lastSync`, `status` |
| `FeedTransaction` | `id`, `connectionId`, `accountId`, `date`, `postedDate`, `amount`, `description`, `merchant`, `cardLast4`, `externalId`, `status` (`new`, `proposed`, `confirmed`, `excluded`), `journalId`, `settlesType/Id` (spend record, invoice payment, bill payment, transfer, payroll, tax deposit) |
| `Statement` | `accountId`, `periodEnd`, `openingBalance`, `closingBalance`, `file`, `lines[]` (parsed), `reconciledAt/By` |

Settlement, not categorisation: every feed line is scored against open spend records, expected payments, bill payments, payroll runs and tax deposits on amount, party, date window and card last four. Nothing is proposed dated before the thing it settles. One record settles one transaction. Confirming inherits everything and posts (§5.3). A charge with no candidate goes to "money with nobody's name on it" and posts to the clearing account until someone names it. Transfers between the group's own accounts are matched as pairs and post bank to bank with no P&L effect.

Reconciliation is by statement, not by feed: the monthly statement is uploaded or parsed, its closing balance is typed by the reconciler (never pre-filled), the ledger balance for that account and date is shown beside it, and the difference is explained line by line: outstanding checks and deposits in transit, feed lines missing from the statement, statement lines missing from the feed (the charge that never downloaded is found by difference). The account's `bank` subledger for the period cannot lock until the reconciliation difference is zero and signed.

Card accounts reconcile the same way against the card statement, with the register (§ `card-register`) providing holder and last four per line.

## 7. Intercompany

SD Plumbing and SD Electric work on SmartDesign projects and on their own. Labor and materials a trade entity puts into a GC project are billed to the GC through an intercompany bill at cost, coded to the GC project's estimate line, and post on both sides with `eliminate = true`. The markup the trade entity earns is a single monthly journal per pair (debit intercompany receivable, credit intercompany revenue on the trade side; the mirror on the GC side), so job cost on the GC's books is cost, not cost plus. Intercompany balances must agree pair by pair before either entity's `gl` subledger locks; the close shows the pair table with differences. Consolidated statements are a view that excludes `eliminate` lines and nets the intercompany accounts; no elimination entity exists.

## 8. Sales tax and use tax

Tax status is a contract-level attribute, mirrored on the PO. A capital-improvement contract with an ST-124 on file issues untaxed invoices and accrues use tax on materials bought untaxed (credit Use tax payable at bill posting, with the cost debited). A repair or maintenance contract issues taxable invoices at the project's jurisdiction rate and posts Sales tax payable. Rates are on a small table by jurisdiction with effective dates. The tax return report lists taxable sales, tax collected, untaxed purchases subject to use tax, and use tax accrued by period and entity, so the quarterly filing is a read-off. Filing itself is manual in v1.

## 9. Payroll

Hours already resolve to a job and a line (`hours-to-line-and-payroll`). The module owns gross-to-net, the liabilities, the postings and the job burden; the filing of federal, state and city payroll taxes and the production of W-2s is done by a payroll provider driven from the ERP's run (Gusto or ADP through their API), because being a day late on a 941 costs more than the provider does. The provider is not the record: the run, the rates, the hours by job and the postings are here; the provider receives the approved run and returns the tax amounts and confirmations, which are stored on the run.

| Object | Fields |
|---|---|
| `Employee` | `entityId`, `payType` (hourly, salary), `rate`, `overtimeRule`, `withholding` (stored encrypted), `workersCompClass`, `costType` (direct or indirect), `default job/line`, `active` |
| `PayrollRun` | `entityId`, `periodStart/End`, `payDate`, `status` (draft, approved, sent, confirmed, paid), `lines[]` per employee `{regular, overtime, hours by job/line, gross, deductions, employerTaxes, net}`, `providerRef`, `journalId` |
| `PayrollLiability` | per run per tax: amount, due date, `paidAt`, `feedTransactionId` |

Employer taxes and workers' comp are pro-rated to jobs by earnings and post as burden by job, which is what makes the burdened margin on the job report a ledger number rather than a report-only one.

## 10. Fixed assets and loans

| Object | Fields |
|---|---|
| `Asset` | `entityId`, `name`, `class` (vehicle, equipment, tools, leasehold, computer), `acquired`, `cost`, `salvage`, `method` (straight-line; MACRS class recorded for the accountant), `lifeMonths`, `accountId`, `accumDepAccountId`, `sourceBillId`, `disposedAt`, `disposalProceeds` |
| `Loan` | `entityId`, `lender`, `principal`, `rate`, `term`, `paymentAmount`, `schedule[]`, `accountId` |

A bill line coded to a fixed-asset account creates the asset record; monthly depreciation is generated at close and posted as a `depreciation` journal; disposal posts the gain or loss. Vehicle assets link to the driver module's vehicle list. HTC deals: cost codes flagged QRE-eligible accumulate qualified rehabilitation expenditure from day one on the property entity, reportable by period.

## 11. The close

The close is a checklist per entity that posts for you and shows the statements before you lock. Order: bank and card reconciliations signed → AR review (unapplied payments, deposits to apply, retainage due) → AP review (unmatched bills, received-not-billed accrual posted) → payroll (accrued wages posted, liabilities matched to deposits) → sales and use tax computed → depreciation posted → intercompany pairs agree → WIP posted per job → statements previewed → lock subledgers in order (bank, ar, ap, payroll, gl). Each step shows its exceptions and cannot be checked while they exist; the Owner can override a step with a reason, which is stored. A closing-date exception report lists anything posted into a period after it was locked (only possible by reopening) with who reopened it and why.

## 12. Financial statements and the year-end package

Three hard-coded layouts, by entity and consolidated, for any period range: the construction P&L (contract revenue by category, direct cost by cost type, gross profit, indirect field cost, G&A, operating income, other, net income); the balance sheet (with retainage, WIP assets and liabilities, deposits, escrow, client funds memo line and intercompany shown gross by entity and netted in consolidation); and the cash flow statement (indirect method from the two above). Supporting schedules: WIP schedule by job (contract, estimated cost, cost to date, percent complete, earned revenue, billed, over/under), AR and AP aging with retainage separated, trial balance, general ledger detail with drill to the source document, journal listing, cash basis conversion (accrual statements less AR and AP movements, for the tax return), 1099 summary by vendor and paying entity, sales and use tax return support, fixed asset roll-forward, loan schedule, intercompany matrix, and the QRE report for HTC entities.

The year-end package is one export per entity, in the accountant's preferred order, as a zip of CSV plus PDF: trial balance, GL detail, journal listing, the three statements, all schedules above, and the period-13 adjustments the accountant booked. A "send to accountant" action produces it and records that it was sent.

## 13. Audit trail and permissions

Every journal line names its source document and line; every document names its journals. Every GL-impacting field change is a system note (record, field, old, new, who, when, reason if a locked period was reopened). The assistant's proposals are recorded as proposals with who confirmed them; a posting always has a human on it. Cross-record audit search: by account, by party, by document, by user, by date.

Roles. The Billing role posts invoices, payments and credit memos. The Controller role approves bills, confirms settlements, runs reconciliations, runs the close through payroll, and drafts manual journals. The Owner approves manual journals, opening balances and reopens; only the Owner locks `gl`. The Foreman, Driver and Designer roles never see the ledger. Reports by role follow the existing `ROLE_VIEWS`.

## 14. Migration from QuickBooks and the parallel run

Cut-over is at a fiscal period boundary; the recommendation is the first day of the next quarter. Steps: (1) map every QuickBooks account to an ERP account and every QuickBooks class, customer, vendor, employee and item to their ERP records, with a mapping table kept as evidence; (2) enter opening balances per entity as one approved `opening` journal from the QuickBooks trial balance at the cut-over date; (3) bring open AR and AP over as documents, not totals, so aging and retainage carry over (invoices and bills dated their original dates, flagged `migrated`, posted only to AR/AP against an opening-balance offset so they do not double count); (4) bring over unreconciled bank items, customer deposits, vendor prepayments, fixed assets with accumulated depreciation, loans with schedules, and year-to-date payroll totals per employee for W-2 continuity; (5) run both systems for two full months, posting everything in both, and compare trial balances and the three statements per entity at each month-end; differences are resolved and the resolution recorded; (6) the accountant signs the second month's comparison; (7) QuickBooks is set read-only and retained for seven years; nothing is posted there again. The ERP shows a "parallel run" banner and a difference card until step 6 is recorded.

## 15. Build order

Phase A, the ledger foundation: chart of accounts, entities, periods, books, journals, balances, the posting engine for invoices, payments, deposits, bills, bill payments, prepayments, retainage, card and bank charges, and manual journals; trial balance, balance sheet, P&L and cash flow from the ledger; the drift check; locks that refuse. Phase B, the feeds: feed connections, settlement, statement reconciliation, the lock condition. Phase C, payroll: employees, runs, liabilities, provider integration, burden posting. Phase D, the close: accruals, WIP, intercompany, depreciation, tax, the checklist, exception report, statements preview. Phase E, migration and parallel run. Phase F, the year-end package, 1099s, tax return support, QRE. Each phase ships with its acceptance tests below and with the module's existing test discipline (Playwright suites, zero console errors, mobile and desktop).

## 16. Platform hooks

The field registry (`accounting-rd` §3, Principle 3) applies here: any record type can take a custom field; a field flagged GL-impacting rides on journal lines in `custom{}` and is filterable in the report builder, saved searches and KPIs. Rules: block (a bill with no cost code cannot be approved; a payment from an account the entity does not own is refused), warn (a change order over contingency), notify (the Controller when committed exceeds budget). GL-impacting custom fields are enabled only after the first close has been survived.

## 17. Acceptance tests

The module is done when, per entity, on seeded data and then on migrated data: every journal balances and the trial balance balances; the balance sheet balances by construction for every period; an invoice with 10% retainage posts AR, retainage receivable and revenue by line and the aging shows retainage separately; a partial payment allocates and the AR aging agrees to the sum of open documents; a customer deposit posts as a liability and is relieved by the invoice; a bill with a prepayment relieves the prepayment first; a split card receipt posts one line per split with the right code; a feed charge dated before its spend record is never proposed; a statement reconciliation with a missing feed line finds it by difference and the bank subledger will not lock until the difference is zero; a payroll run posts labor and burden by job and the liabilities equal the provider's confirmation; accrued wages and received-not-billed post at close and reverse on day one; WIP posts gross per job and the WIP schedule ties to the balance sheet; an intercompany bill at cost eliminates in consolidation and the pair table shows zero difference; editing a posted bill in an open period reverses and re-posts with a system note; editing it in a locked period is refused and the credit path is offered; a posting into a locked period is impossible without a recorded reopen; the drift check reports zero; depreciation posts monthly and the asset roll-forward ties; sales tax payable equals tax on taxable invoices and use tax equals accrued untaxed material; the 1099 summary excludes card payments and groups by paying entity; the year-end package exports and re-imports as a trial balance that matches; the two-month parallel run agrees to QuickBooks per entity and the accountant's sign-off is recorded.

## 18. Decisions required from Alan

1. Cut-over date (recommended: first day of the next fiscal quarter, with the two-month parallel run before QuickBooks goes read-only).
2. Payroll provider for filings (recommended: keep the run and the postings in the ERP, use Gusto or ADP through the API for tax deposits, filings and W-2s).
3. Feed provider (recommended: Plaid for all group bank and card accounts, direct bank feed where Plaid does not cover).
4. Intercompany at cost with a separate monthly markup entry (recommended) versus cost-plus billing as today.
5. Residential deposits under GBL 771-a tracked in a tagged escrow account (recommended).
6. Which entities are in scope at cut-over (all trade and operating entities together, property and development LLCs in a second wave, or everything at once).
