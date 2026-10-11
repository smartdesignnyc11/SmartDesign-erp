# Documents Workshop: creating estimates, COs, invoices, pay applications, POs, RFQs and bills

Alan, 2026-10-11. Is each document easy on the go, quick to create, does it carry the back end that accounting
and reporting need, and does it look right to the client? The documents are made as real work in the pilot:
the tasks sit in the day plan's work slots (`doc_tasks` in `day_plan.json` / `day_plan_lean.json`), and
`simctl begin` puts the person on their phone when the task says so. Builder and scorer: `sim/docs.py`.

## Who creates what, and where (the day plan's doc_tasks)
| Who | Document | Device |
|---|---|---|
| PM (u_alan) | change order, in the client's kitchen | phone (390px) |
| PM | estimate for added work | phone; a second one on the desktop |
| Coordinator (u_chen) | PO from estimate lines | phone, from the site |
| Coordinator | RFQ from estimate lines, three vendors | desktop |
| Foreman (u_angel) | material request | phone |
| Billing (u_billing) | invoice (the approved CO, or a design fee) | desktop |
| Billing | progress billing: pay application from the schedule of values, with retainage | desktop |
| Controller (u_controller) | a vendor bill from the mail, against its PO | desktop |

## What is measured and checked
- **The harness, for every document created:** taps, seconds (agent wall time) and the toolkit's own time,
  screens visited, fields typed against fields filled on the form when saved (the rest were defaulted); for
  estimate, CO and invoice lines, which fields were typed (with characters) and which were picked from a list,
  characters typed per line, and the line descriptions as saved (the item-library question, BACKLOG 1.18);
  validation stops and errors, and whether the creator found it on their screen after saving and after a reload
  (`python3 sim/docs.py usage` > `docs_usage.json`).
- **The referee, every day, independently** (`AUDIT_JS` in `sim/docs.py`, in `ledger.json` "docs" and
  `ledger.md` "Documents"): job, client and entity; cost codes and estimate-line links; tax and retainage; terms
  and due dates; a CO's approval record and budget effect (jobFin contract = base + approved COs); a pay
  application's % per line against the schedule of values and the measured %; a PO's line links, sourcing (an RFQ
  or quotes behind an order over $2,500) and terms; a bill's PO link and job cost; and that each reached its
  report with its own number (AR, the PO report, job cost) through erpQuery and jobFin, as chain_test reads them.
  Every missing or wrong field is a finding naming the field.
- **The client's view:** `sim/simctl client-docs` renders every client-facing document the team created
  (estimate, change order, invoice, pay application) as the client receives it: the portal on the client's
  phone, and the print / PDF the firm sends. Screenshots, PDFs and the text go to `runs/<run>/client_docs/`.

## Steps at the end of the pilot (after the Navigation and Pages Workshop's capture, server still up)
1. `sim/simctl referee` (fresh audit), `sim/simctl client-docs`, `python3 sim/docs.py usage`.
2. One subagent each (strongest model, Read and Write only): `python3 sim/docs.py prompt creator <uid>` for the
   PM, coordinator, foreman, billing and controller; `prompt client` for the Kleins; `prompt brand u_owner` and
   `prompt brand u_sarah`. About 3-6k tokens in (the client reads the text files, and looks at each image once),
   under 1k out.
3. `python3 sim/docs.py score` writes `runs/<run>/docs_workshop.md` and prints the synthesis prompt; one subagent.
4. `python3 sim/docs.py gallery` writes `runs/<run>/client_docs/index.html` (portal and print side by side, with
   the client's, owner's and designer's notes), self-contained beside its images, ready to publish for Alan.

<!-- CREATOR -->
You are {name} ({role}) at SmartDesign. You created these documents in the pilot; the harness measured them:
{measured}
Read your diary `{diary}` for what you noted at the time. Write `{answer}`, one line per answer, at most 2 lines per
question per document type, at most 40 lines, in this format: `D<n> | <document type> | blocks, slows or annoys | <answer>`
D1 how fast was it (the measured taps and seconds: right, or too slow, and where the time went)
D2 what you typed that the system should have filled in
D3 what was hard on the phone (skip if you made it on a desktop)
D4 what information was missing when you needed it
D5 did you trust the totals (tax, retainage, markup, the sum), and why not
D6 what you would change, most important first
D7 (estimate, CO, invoice) which lines you wrote from scratch that you write on every job
D8 which descriptions you copied from elsewhere (an old estimate, a vendor quote, your notes), and from where
D9 what should have filled itself in from an item library (item, description, unit, price, cost code)
<!-- /CREATOR -->

<!-- CLIENT -->
You are Sarah Klein, the client at 121 State Street, reading the documents the firm sent you, as you received them:
{docs}
Read each text file; look at each image once. Write `{answer}`, at most 2 lines per question per document, at most
50 lines: `C<n> | <document number> | blocks, slows or annoys | <answer>`
C1 is it clear what I am paying for · C2 is the scope in plain language, with inclusions and exclusions
C3 are the totals, retainage, payment terms and how to pay clear · C4 does it look like a premium landmark-renovation firm
C5 what would make me call the PM with a question · C6 can I approve or pay from my phone, and how many taps
C7 are the line descriptions clear and professional (name the lines that are not)
<!-- /CLIENT -->

<!-- BRAND -->
You are {name} ({role}) at SmartDesign, judging the client-facing documents against the firm's brand (a premium
landmark brownstone and townhouse design-build firm; docs/STANDARD.md "Who we are"):
{docs}
Look at each image once. Write `{answer}`, at most 25 lines: `B<n> | <document number or type> | blocks, slows or annoys | <answer>`
B1 does it look and read like us (type, layout, logo, voice, numbers) · B2 what a client would notice first, good or bad
B3 what you would change before it goes to another client
<!-- /BRAND -->

<!-- SYNTHESIS -->
You are the synthesis step of the SmartDesign Documents Workshop. Inputs: `{workshop}` (measured, back-end gaps,
client-view and creator answers, grouped), `{usage}`, the answers in `{answers}/` (docs_*.md) and the gallery
`{gallery}`. Replace "(to be written by the synthesis step)" in `{workshop}` with, under 140 lines, one block per
document type (estimate, change order, invoice, pay application, PO, RFQ, bill, material request):
- time and taps against the target (a CO on the phone in under 2 minutes and about 12 taps; an estimate on the
  phone in under 10 minutes; a material request in under 30 seconds and 5 taps; a bill in under a minute);
- the back-end gaps, by field, that would put wrong numbers in accounting or reporting (S1 if money or a report
  is wrong);
- the client-view issues, ranked (several readers on the same issue first; blocks > slows > annoys);
- typed versus filled (fields typed, characters per line, picks, defaults) and what an item library would have
  filled, from the measurements and D7-D9; this shapes BACKLOG 1.18 (the item library);
- the top three fixes, each with the screen it lives on.
End with the five fixes across all documents that matter most to Alan, in order. House voice: plain, specific,
no exclamation marks.
<!-- /SYNTHESIS -->
