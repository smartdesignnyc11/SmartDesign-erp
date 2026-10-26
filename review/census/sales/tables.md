# Sales and Clients Census: Every Screen

Per role and device: the screen, how it was reached, the view it landed on, its height in screens, sections (above the fold), tab groups, records, blue buttons, the first button, figures. Written by `tests/module_census.py --report` from data.json.

## Owner, desktop

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Sales | Sales | ovsales | 0.7 | 0 (0) | 1 | 6 leads, 6 contacts, 1 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_owner_sales.jpg |
| Sales[Board] | Sales › Board | ovsales | 0.9 | 0 (0) | 1 | 6 leads, 6 contacts, 2 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_owner_sales_board.jpg |
| Estimates | Sales › Estimates | billing | 0.6 | 0 (0) | 1 | 4 estimates, 3 clients | New Estimate | Billing Queue |  | desktop_owner_estimates.jpg |
| Estimates[Billing Queue] | Sales › Estimates › Billing Queue | billing | 0.7 | 0 (0) | 1 | 3 clients, 2 invoices | Draft $17,080 — 45 Cranberry St | Draft $17,080 — 45 Cranberry S | Ready to Bill $46K; Drafts 0; Sent and Unpaid $92K; Overdue $0 | desktop_owner_estimates_billing_queue.jpg |
| Estimates[Progress Billing] | Sales › Estimates › Progress Billing | billing | 5.6 | 6 (2) | 1 | 6 schedule lines, 6 materials, 2 clients, 1 change orders | Draft $12,651 (job is $131,058 ahead of  | Draft $12,651 (job is $131,058 |  | desktop_owner_estimates_progress_billing.jpg |
| Estimates[Change Orders] | Sales › Estimates › Change Orders | billing | 0.4 | 0 (0) | 1 | 2 change orders, 1 clients | New Change Order | New Change Order |  | desktop_owner_estimates_change_orders.jpg |
| Estimates[Invoices] | Sales › Estimates › Invoices | billing | 0.6 | 0 (0) | 1 | 6 invoices, 3 clients |  | Billing Queue |  | desktop_owner_estimates_invoices.jpg |
| Estimates[Schedule of Values] | Sales › Estimates › Schedule of Values | billing | 1.9 | 3 (1) | 1 | 3 clients |  | Billing Queue |  | desktop_owner_estimates_schedule_of_values.jpg |
| Estimates[Payments] | Sales › Estimates › Payments | billing | 0.7 | 1 (1) | 1 | 4 invoices, 2 clients |  | Billing Queue |  | desktop_owner_estimates_payments.jpg |
| Estimates[Client Funds] | Sales › Estimates › Client Funds | billing | 1.1 | 3 (3) | 1 | 4 materials |  | Billing Queue | Bank Balance $184,231; Available Cash (Ours) $158,856; still to purchase agains $63,040; spent ahead of collectio $24,683 | desktop_owner_estimates_client_funds.jpg |
| Numbers | Sales › Numbers | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | desktop_owner_numbers.jpg |
| Numbers[Forecast] | Sales › Numbers › Forecast | hbforecast | 0.9 | 0 (0) | 2 |  |  | Numbers |  | desktop_owner_numbers_forecast.jpg |
| Numbers[Sales Dashboard] | Sales › Numbers › Sales Dashboard | hbdash | 0.8 | 7 (7) | 1 |  |  | Numbers |  | desktop_owner_numbers_sales_dashboard.jpg |
| Numbers[Construction Only] | Sales › Numbers › Construction Only | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply —; No Next Step 0; Proposals Aging 0; Won This Quarter $210K | desktop_owner_numbers_construction_only.jpg |
| Numbers[Design Only] | Sales › Numbers › Design Only | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply —; No Next Step 0; Proposals Aging 0; Won This Quarter $210K | desktop_owner_numbers_design_only.jpg |
| Numbers[By Source] | Sales › Numbers › By Source | salesnum | 0.9 | 1 (1) | 3 |  |  | Numbers | median first reply (7 le 3 h; median inquiry to agreem 48d; average won job $210k; of wins referred (67% of 100% | desktop_owner_numbers_by_source.jpg |
| Numbers[By Source][Funnel] | Sales › Numbers › By Source › Funnel | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | desktop_owner_numbers_by_source_funnel.jpg |
| Partners | Sales › Partners | partners | 0.6 | 0 (0) | 0 | 3 contacts, 3 companies, 3 partners | New Partner | Thank-Yous Owed 1 David sent u | Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K | desktop_owner_partners.jpg |
| Playbook | Sales › Playbook | playbook | 2.2 | 5 (2) | 0 |  |  |  |  | desktop_owner_playbook.jpg |
| Clients | Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_owner_clients.jpg |
| Clients[People] | Clients › People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_owner_clients_people.jpg |
| Clients[Companies] | Clients › Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_owner_clients_companies.jpg |
| Sales (by the link Leads 1 inquiries to qualify) | Sales › link: Leads 1 inquiries to qualify · every one | ovsales | 0.5 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_owner_leads_1_inquiries_to_qualify_every_one.jpg |
| Sales (by the link Leads 1 inquiries to qualify)[Stalled 1 no touch in 14 days — an oppor] | Sales › link: Leads 1 inquiries to qualify · every one › Stalled 1 no touch in 14 days — an oppor | ovsales | 0.5 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_owner_leads_1_inquiries_to_qualify_every_one_stalled_1_no_touch_in_14_days_an_oppor.jpg |
| Numbers — Forecast | Numbers › link: Forecast | hbforecast | 0.9 | 0 (0) | 2 |  |  | Numbers |  | desktop_owner_forecast.jpg |
| Numbers — Forecast[Numbers] | Numbers › link: Forecast › Numbers | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | desktop_owner_forecast_numbers.jpg |
| Numbers — Forecast[Sales Dashboard] | Numbers › link: Forecast › Sales Dashboard | hbdash | 0.8 | 7 (7) | 1 |  |  | Numbers |  | desktop_owner_forecast_sales_dashboard.jpg |
| Numbers — Forecast[Forecast Category] | Numbers › link: Forecast › Forecast Category | hbforecast | 0.8 | 0 (0) | 2 |  |  | Numbers |  | desktop_owner_forecast_forecast_category.jpg |
| Numbers — Dashboard | Numbers › link: Sales Dashboard | hbdash | 0.8 | 7 (7) | 1 |  |  | Numbers |  | desktop_owner_sales_dashboard.jpg |
| Numbers — Dashboard[Numbers] | Numbers › link: Sales Dashboard › Numbers | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | desktop_owner_sales_dashboard_numbers.jpg |
| Numbers — Dashboard[Forecast] | Numbers › link: Sales Dashboard › Forecast | hbforecast | 0.9 | 0 (0) | 2 |  |  | Numbers |  | desktop_owner_sales_dashboard_forecast.jpg |
| People | Clients › link: People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_owner_people.jpg |
| People[Clients] | Clients › link: People › Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_owner_people_clients.jpg |
| People[Companies] | Clients › link: People › Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_owner_people_companies.jpg |
| People[Prev] | Clients › link: People › Prev | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_owner_people_prev.jpg |
| People[Next] | Clients › link: People › Next | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_owner_people_next.jpg |
| Companies | Clients › link: Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_owner_companies.jpg |
| Companies[Clients] | Clients › link: Companies › Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_owner_companies_clients.jpg |
| Companies[People] | Clients › link: Companies › People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_owner_companies_people.jpg |
| Companies[Prev] | Clients › link: Companies › Prev | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_owner_companies_prev.jpg |
| Companies[Next] | Clients › link: Companies › Next | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_owner_companies_next.jpg |

## PM (Alan), desktop

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Clients | Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_pm_clients.jpg |
| Clients[People] | Clients › People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_pm_clients_people.jpg |
| Clients[Companies] | Clients › Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_pm_clients_companies.jpg |
| Sales | More › Sales | ovsales | 0.7 | 0 (0) | 1 | 6 leads, 6 contacts, 1 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_pm_sales.jpg |
| Sales[Board] | More › Sales › Board | ovsales | 0.9 | 0 (0) | 1 | 6 leads, 6 contacts, 2 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_pm_sales_board.jpg |
| Partners | More › Partners | partners | 0.6 | 0 (0) | 0 | 3 contacts, 3 companies, 3 partners | New Partner | Thank-Yous Owed 1 David sent u | Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K | desktop_pm_partners.jpg |
| Playbook | More › Playbook | playbook | 2.2 | 5 (2) | 0 |  |  |  |  | desktop_pm_playbook.jpg |
| Numbers | More › Numbers | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | desktop_pm_numbers.jpg |
| Numbers[Forecast] | More › Numbers › Forecast | hbforecast | 0.9 | 0 (0) | 2 |  |  | Numbers |  | desktop_pm_numbers_forecast.jpg |
| Numbers[Sales Dashboard] | More › Numbers › Sales Dashboard | hbdash | 0.8 | 7 (7) | 1 |  |  | Numbers |  | desktop_pm_numbers_sales_dashboard.jpg |
| Numbers[Construction Only] | More › Numbers › Construction Only | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply —; No Next Step 0; Proposals Aging 0; Won This Quarter $210K | desktop_pm_numbers_construction_only.jpg |
| Numbers[Design Only] | More › Numbers › Design Only | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply —; No Next Step 0; Proposals Aging 0; Won This Quarter $210K | desktop_pm_numbers_design_only.jpg |
| Numbers[By Source] | More › Numbers › By Source | salesnum | 0.9 | 1 (1) | 3 |  |  | Numbers | median first reply (7 le 3 h; median inquiry to agreem 48d; average won job $210k; of wins referred (67% of 100% | desktop_pm_numbers_by_source.jpg |
| Numbers[By Source][Funnel] | More › Numbers › By Source › Funnel | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | desktop_pm_numbers_by_source_funnel.jpg |
| People | Clients › link: People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_pm_people.jpg |
| People[Clients] | Clients › link: People › Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_pm_people_clients.jpg |
| People[Companies] | Clients › link: People › Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_pm_people_companies.jpg |
| People[Prev] | Clients › link: People › Prev | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_pm_people_prev.jpg |
| People[Next] | Clients › link: People › Next | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_pm_people_next.jpg |
| Companies | Clients › link: Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_pm_companies.jpg |
| Companies[Clients] | Clients › link: Companies › Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_pm_companies_clients.jpg |
| Companies[People] | Clients › link: Companies › People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_pm_companies_people.jpg |
| Companies[Prev] | Clients › link: Companies › Prev | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_pm_companies_prev.jpg |
| Companies[Next] | Clients › link: Companies › Next | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_pm_companies_next.jpg |
| Sales (by the link Leads 1 inquiries to qualify) | Sales › link: Leads 1 inquiries to qualify · every one | ovsales | 0.5 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_pm_leads_1_inquiries_to_qualify_every_one.jpg |
| Sales (by the link Leads 1 inquiries to qualify)[Stalled 1 no touch in 14 days — an oppor] | Sales › link: Leads 1 inquiries to qualify · every one › Stalled 1 no touch in 14 days — an oppor | ovsales | 0.5 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_pm_leads_1_inquiries_to_qualify_every_one_stalled_1_no_touch_in_14_days_an_oppor.jpg |
| Numbers — Forecast | Numbers › link: Forecast | hbforecast | 0.9 | 0 (0) | 2 |  |  | Numbers |  | desktop_pm_forecast.jpg |
| Numbers — Forecast[Numbers] | Numbers › link: Forecast › Numbers | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | desktop_pm_forecast_numbers.jpg |
| Numbers — Forecast[Sales Dashboard] | Numbers › link: Forecast › Sales Dashboard | hbdash | 0.8 | 7 (7) | 1 |  |  | Numbers |  | desktop_pm_forecast_sales_dashboard.jpg |
| Numbers — Forecast[Forecast Category] | Numbers › link: Forecast › Forecast Category | hbforecast | 0.8 | 0 (0) | 2 |  |  | Numbers |  | desktop_pm_forecast_forecast_category.jpg |
| Numbers — Dashboard | Numbers › link: Sales Dashboard | hbdash | 0.8 | 7 (7) | 1 |  |  | Numbers |  | desktop_pm_sales_dashboard.jpg |
| Numbers — Dashboard[Numbers] | Numbers › link: Sales Dashboard › Numbers | salesnum | 0.7 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | desktop_pm_sales_dashboard_numbers.jpg |
| Numbers — Dashboard[Forecast] | Numbers › link: Sales Dashboard › Forecast | hbforecast | 0.9 | 0 (0) | 2 |  |  | Numbers |  | desktop_pm_sales_dashboard_forecast.jpg |

## Coordinator (Chen), desktop

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Forecast | More › Forecast | hbforecast | 0.9 | 0 (0) | 2 |  |  | Numbers |  | desktop_coord_forecast.jpg |
| Forecast[Numbers] | More › Forecast › Numbers | home | 1.1 | 2 (2) | 1 | 4 materials, 2 schedule lines, 2 approvals, 2 vendors, 1 to-dos | Chase COI | All 29 |  | desktop_coord_forecast_numbers.jpg |
| Forecast[Sales Dashboard] | More › Forecast › Sales Dashboard | hbdash | 0.8 | 7 (7) | 1 |  |  | Numbers |  | desktop_coord_forecast_sales_dashboard.jpg |
| Forecast[Forecast Category] | More › Forecast › Forecast Category | hbforecast | 0.8 | 0 (0) | 2 |  |  | Numbers |  | desktop_coord_forecast_forecast_category.jpg |
| Sales Dashboard | More › Sales Dashboard | hbdash | 0.8 | 7 (7) | 1 |  |  | Numbers |  | desktop_coord_sales_dashboard.jpg |
| Sales Dashboard[Numbers] | More › Sales Dashboard › Numbers | home | 1.1 | 2 (2) | 1 | 4 materials, 2 schedule lines, 2 approvals, 2 vendors, 1 to-dos | Chase COI | All 29 |  | desktop_coord_sales_dashboard_numbers.jpg |
| Sales Dashboard[Forecast] | More › Sales Dashboard › Forecast | hbforecast | 0.9 | 0 (0) | 2 |  |  | Numbers |  | desktop_coord_sales_dashboard_forecast.jpg |
| Sales | More › Sales | ovsales | 0.7 | 0 (0) | 1 | 6 leads, 6 contacts, 1 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_coord_sales.jpg |
| Sales[Board] | More › Sales › Board | ovsales | 0.9 | 0 (0) | 1 | 6 leads, 6 contacts, 2 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_coord_sales_board.jpg |
| Partners | More › Partners | partners | 0.6 | 0 (0) | 0 | 3 contacts, 3 companies, 3 partners | New Partner | Thank-Yous Owed 1 David sent u | Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K | desktop_coord_partners.jpg |
| Playbook | More › Playbook | playbook | 2.2 | 5 (2) | 0 |  |  |  |  | desktop_coord_playbook.jpg |
| Clients | More › Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_coord_clients.jpg |
| Clients[People] | More › Clients › People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_coord_clients_people.jpg |
| Clients[Companies] | More › Clients › Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_coord_clients_companies.jpg |
| Sales (by the link Leads 1 inquiries to qualify) | Sales › link: Leads 1 inquiries to qualify · every one | ovsales | 0.5 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_coord_leads_1_inquiries_to_qualify_every_one.jpg |
| Sales (by the link Leads 1 inquiries to qualify)[Stalled 1 no touch in 14 days — an oppor] | Sales › link: Leads 1 inquiries to qualify · every one › Stalled 1 no touch in 14 days — an oppor | ovsales | 0.5 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_coord_leads_1_inquiries_to_qualify_every_one_stalled_1_no_touch_in_14_days_an_oppor.jpg |
| People | Clients › link: People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_coord_people.jpg |
| People[Clients] | Clients › link: People › Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_coord_people_clients.jpg |
| People[Companies] | Clients › link: People › Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_coord_people_companies.jpg |
| People[Prev] | Clients › link: People › Prev | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_coord_people_prev.jpg |
| People[Next] | Clients › link: People › Next | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_coord_people_next.jpg |
| Companies | Clients › link: Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_coord_companies.jpg |
| Companies[Clients] | Clients › link: Companies › Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_coord_companies_clients.jpg |
| Companies[People] | Clients › link: Companies › People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_coord_companies_people.jpg |
| Companies[Prev] | Clients › link: Companies › Prev | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_coord_companies_prev.jpg |
| Companies[Next] | Clients › link: Companies › Next | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_coord_companies_next.jpg |

## Designer (Sarah), desktop

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Clients | Clients | clients | 0.6 | 0 (0) | 0 | 5 clients, 5 contacts, 2 leads | New Client | New Client | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_designer_clients.jpg |

## Billing, desktop

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Clients | Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_billing_clients.jpg |
| Clients[People] | Clients › People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_billing_clients_people.jpg |
| Clients[Companies] | Clients › Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_billing_clients_companies.jpg |
| Forecast | More › Forecast | hbforecast | 0.9 | 0 (0) | 2 |  |  | Numbers |  | desktop_billing_forecast.jpg |
| Forecast[Numbers] | More › Forecast › Numbers | home | 0.9 | 1 (1) | 1 | 4 approvals, 3 findings, 1 mail, 1 clients | Resolve, $16, | All 5 |  | desktop_billing_forecast_numbers.jpg |
| Forecast[Sales Dashboard] | More › Forecast › Sales Dashboard | hbdash | 0.8 | 7 (7) | 1 |  |  | Numbers |  | desktop_billing_forecast_sales_dashboard.jpg |
| Forecast[Forecast Category] | More › Forecast › Forecast Category | hbforecast | 0.8 | 0 (0) | 2 |  |  | Numbers |  | desktop_billing_forecast_forecast_category.jpg |
| Sales Dashboard | More › Sales Dashboard | hbdash | 0.8 | 7 (7) | 1 |  |  | Numbers |  | desktop_billing_sales_dashboard.jpg |
| Sales Dashboard[Numbers] | More › Sales Dashboard › Numbers | home | 0.9 | 1 (1) | 1 | 4 approvals, 3 findings, 1 mail, 1 clients | Resolve, $16, | All 5 |  | desktop_billing_sales_dashboard_numbers.jpg |
| Sales Dashboard[Forecast] | More › Sales Dashboard › Forecast | hbforecast | 0.9 | 0 (0) | 2 |  |  | Numbers |  | desktop_billing_sales_dashboard_forecast.jpg |
| Sales | More › Sales | ovsales | 0.7 | 0 (0) | 1 | 6 leads, 6 contacts, 1 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_billing_sales.jpg |
| Sales[Board] | More › Sales › Board | ovsales | 0.9 | 0 (0) | 1 | 6 leads, 6 contacts, 2 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_billing_sales_board.jpg |
| Partners | More › Partners | partners | 0.6 | 0 (0) | 0 | 3 contacts, 3 companies, 3 partners | New Partner | Thank-Yous Owed 1 David sent u | Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K | desktop_billing_partners.jpg |
| Playbook | More › Playbook | playbook | 2.2 | 5 (2) | 0 |  |  |  |  | desktop_billing_playbook.jpg |
| People | Clients › link: People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_billing_people.jpg |
| People[Clients] | Clients › link: People › Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_billing_people_clients.jpg |
| People[Companies] | Clients › link: People › Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_billing_people_companies.jpg |
| People[Prev] | Clients › link: People › Prev | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_billing_people_prev.jpg |
| People[Next] | Clients › link: People › Next | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_billing_people_next.jpg |
| Companies | Clients › link: Companies | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_billing_companies.jpg |
| Companies[Clients] | Clients › link: Companies › Clients | clients | 0.7 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_billing_companies_clients.jpg |
| Companies[People] | Clients › link: Companies › People | hbcontacts | 1.4 | 0 (0) | 2 | 19 contacts, 8 leads, 3 companies, 3 partners, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | desktop_billing_companies_people.jpg |
| Companies[Prev] | Clients › link: Companies › Prev | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_billing_companies_prev.jpg |
| Companies[Next] | Clients › link: Companies › Next | hbcompanies | 0.6 | 0 (0) | 2 | 6 companies | New Company | Clients |  | desktop_billing_companies_next.jpg |
| Sales (by the link Leads 1 inquiries to qualify) | Sales › link: Leads 1 inquiries to qualify · every one | ovsales | 0.5 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_billing_leads_1_inquiries_to_qualify_every_one.jpg |
| Sales (by the link Leads 1 inquiries to qualify)[Stalled 1 no touch in 14 days — an oppor] | Sales › link: Leads 1 inquiries to qualify · every one › Stalled 1 no touch in 14 days — an oppor | ovsales | 0.5 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | desktop_billing_leads_1_inquiries_to_qualify_every_one_stalled_1_no_touch_in_14_days_an_oppor.jpg |

## Controller, desktop

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Clients | More › Clients | clients | 0.6 | 0 (0) | 0 | 5 clients, 5 contacts, 2 leads | New Client | Billing | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | desktop_controller_clients.jpg |

## Owner, phone

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Sales | bar: Sales | ovsales | 1.1 | 0 (0) | 1 | 6 leads, 6 contacts, 1 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_owner_sales.jpg |
| Sales[Board] | bar: Sales › Board | ovsales | 0.9 | 0 (0) | 1 | 6 leads, 6 contacts, 2 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_owner_sales_board.jpg |
| Estimates | menu › Sales › Estimates | billing | 0.9 | 0 (0) | 1 | 4 estimates, 3 clients | New Estimate | Billing Queue |  | phone_owner_estimates.jpg |
| Estimates[Billing Queue] | menu › Sales › Estimates › Billing Queue | billing | 1.1 | 0 (0) | 1 | 3 clients, 2 invoices | Draft $17,080 — 45 Cranberry St | Draft $17,080 — 45 Cranberry S | Ready to Bill $46K; Drafts 0; Sent and Unpaid $92K; Overdue $0 | phone_owner_estimates_billing_queue.jpg |
| Estimates[Progress Billing] | menu › Sales › Estimates › Progress Billing | billing | 6.1 | 6 (1) | 1 | 6 materials, 2 clients, 1 change orders, 1 schedule lines | Draft $12,651 (job is $131,058 ahead of  | Draft $12,651 (job is $131,058 |  | phone_owner_estimates_progress_billing.jpg |
| Estimates[Change Orders] | menu › Sales › Estimates › Change Orders | billing | 0.7 | 0 (0) | 1 | 2 change orders, 1 clients | New Change Order | New Change Order |  | phone_owner_estimates_change_orders.jpg |
| Estimates[Invoices] | menu › Sales › Estimates › Invoices | billing | 0.9 | 0 (0) | 1 | 6 invoices, 3 clients |  | Billing Queue |  | phone_owner_estimates_invoices.jpg |
| Estimates[Schedule of Values] | menu › Sales › Estimates › Schedule of Values | billing | 2.9 | 3 (1) | 1 | 3 clients |  | Billing Queue |  | phone_owner_estimates_schedule_of_values.jpg |
| Estimates[Payments] | menu › Sales › Estimates › Payments | billing | 1.0 | 1 (1) | 1 | 4 invoices, 2 clients |  | Billing Queue |  | phone_owner_estimates_payments.jpg |
| Estimates[Client Funds] | menu › Sales › Estimates › Client Funds | billing | 1.9 | 2 (1) | 1 | 4 materials |  | Billing Queue | Bank Balance $184,231; Available Cash (Ours) $158,856; still to purchase agains $63,040; spent ahead of collectio $24,683 | phone_owner_estimates_client_funds.jpg |
| Numbers | menu › Sales › Numbers | salesnum | 1.1 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | phone_owner_numbers.jpg |
| Numbers[Forecast] | menu › Sales › Numbers › Forecast | hbforecast | 1.4 | 0 (0) | 2 |  |  | Numbers |  | phone_owner_numbers_forecast.jpg |
| Numbers[Sales Dashboard] | menu › Sales › Numbers › Sales Dashboard | hbdash | 2.0 | 7 (2) | 1 |  |  | Numbers |  | phone_owner_numbers_sales_dashboard.jpg |
| Numbers[Construction Only] | menu › Sales › Numbers › Construction Only | salesnum | 1.0 | 1 (1) | 3 |  |  | Numbers | First Reply —; No Next Step 0; Proposals Aging 0; Won This Quarter $210K | phone_owner_numbers_construction_only.jpg |
| Numbers[Design Only] | menu › Sales › Numbers › Design Only | salesnum | 1.0 | 1 (1) | 3 |  |  | Numbers | First Reply —; No Next Step 0; Proposals Aging 0; Won This Quarter $210K | phone_owner_numbers_design_only.jpg |
| Numbers[By Source] | menu › Sales › Numbers › By Source | salesnum | 1.6 | 1 (1) | 3 |  |  | Numbers | median first reply (7 le 3 h; median inquiry to agreem 48d; average won job $210k; of wins referred (67% of 100% | phone_owner_numbers_by_source.jpg |
| Numbers[By Source][Funnel] | menu › Sales › Numbers › By Source › Funnel | salesnum | 1.1 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | phone_owner_numbers_by_source_funnel.jpg |
| Numbers[Lost and Why] | menu › Sales › Numbers › Lost and Why | salesnum | 1.2 | 2 (1) | 3 | 2 leads, 2 contacts |  | Numbers | median first reply (7 le 3 h; median inquiry to agreem 48d; average won job $210k; of wins referred (67% of 100% | phone_owner_numbers_lost_and_why.jpg |
| Partners | menu › Sales › Partners | partners | 0.7 | 0 (0) | 0 | 3 contacts, 3 companies, 3 partners | New Partner | Thank-Yous Owed 1 | Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K | phone_owner_partners.jpg |
| Playbook | menu › Sales › swipe the strip, Playbook | playbook | 4.4 | 5 (1) | 0 |  |  |  |  | phone_owner_playbook.jpg |
| Clients | menu › Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_owner_clients.jpg |
| Clients[People] | menu › Clients › People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_owner_clients_people.jpg |
| Clients[Companies] | menu › Clients › Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_owner_clients_companies.jpg |
| Sales (by the link Leads 1) | Sales › link: Leads 1 | ovsales | 0.7 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_owner_leads_1.jpg |
| Sales (by the link Leads 1)[Stalled] | Sales › link: Leads 1 › Stalled | ovsales | 0.7 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_owner_leads_1_stalled.jpg |
| Numbers — Forecast | Numbers › link: Forecast | hbforecast | 1.4 | 0 (0) | 2 |  |  | Numbers |  | phone_owner_forecast.jpg |
| Numbers — Forecast[Numbers] | Numbers › link: Forecast › Numbers | salesnum | 1.1 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | phone_owner_forecast_numbers.jpg |
| Numbers — Forecast[Sales Dashboard] | Numbers › link: Forecast › Sales Dashboard | hbdash | 2.0 | 7 (2) | 1 |  |  | Numbers |  | phone_owner_forecast_sales_dashboard.jpg |
| Numbers — Forecast[Forecast Category] | Numbers › link: Forecast › Forecast Category | hbforecast | 1.3 | 0 (0) | 2 |  |  | Numbers |  | phone_owner_forecast_forecast_category.jpg |
| Numbers — Dashboard | Numbers › link: Sales Dashboard | hbdash | 2.0 | 7 (2) | 1 |  |  | Numbers |  | phone_owner_sales_dashboard.jpg |
| Numbers — Dashboard[Numbers] | Numbers › link: Sales Dashboard › Numbers | salesnum | 1.1 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | phone_owner_sales_dashboard_numbers.jpg |
| Numbers — Dashboard[Forecast] | Numbers › link: Sales Dashboard › Forecast | hbforecast | 1.4 | 0 (0) | 2 |  |  | Numbers |  | phone_owner_sales_dashboard_forecast.jpg |
| People | Clients › link: People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_owner_people.jpg |
| People[Clients] | Clients › link: People › Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_owner_people_clients.jpg |
| People[Companies] | Clients › link: People › Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_owner_people_companies.jpg |
| People[Prev] | Clients › link: People › Prev | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_owner_people_prev.jpg |
| People[Next] | Clients › link: People › Next | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_owner_people_next.jpg |
| Companies | Clients › link: Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_owner_companies.jpg |
| Companies[Clients] | Clients › link: Companies › Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_owner_companies_clients.jpg |
| Companies[People] | Clients › link: Companies › People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_owner_companies_people.jpg |
| Companies[Prev] | Clients › link: Companies › Prev | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_owner_companies_prev.jpg |
| Companies[Next] | Clients › link: Companies › Next | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_owner_companies_next.jpg |

## PM (Alan), phone

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Clients | bar: Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_pm_clients.jpg |
| Clients[People] | bar: Clients › People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_pm_clients_people.jpg |
| Clients[Companies] | bar: Clients › Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_pm_clients_companies.jpg |
| Sales | menu › More › swipe the strip, Sales | ovsales | 1.1 | 0 (0) | 1 | 6 leads, 6 contacts, 1 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_pm_sales.jpg |
| Sales[Board] | menu › More › swipe the strip, Sales › Board | ovsales | 0.9 | 0 (0) | 1 | 6 leads, 6 contacts, 2 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_pm_sales_board.jpg |
| Partners | menu › More › swipe the strip, Partners | partners | 0.7 | 0 (0) | 0 | 3 contacts, 3 companies, 3 partners | New Partner | Thank-Yous Owed 1 | Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K | phone_pm_partners.jpg |
| Playbook | menu › More › swipe the strip, Playbook | playbook | 4.4 | 5 (1) | 0 |  |  |  |  | phone_pm_playbook.jpg |
| Numbers | menu › More › swipe the strip, Numbers | salesnum | 1.1 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | phone_pm_numbers.jpg |
| Numbers[Forecast] | menu › More › swipe the strip, Numbers › Forecast | hbforecast | 1.4 | 0 (0) | 2 |  |  | Numbers |  | phone_pm_numbers_forecast.jpg |
| Numbers[Sales Dashboard] | menu › More › swipe the strip, Numbers › Sales Dashboard | hbdash | 2.0 | 7 (2) | 1 |  |  | Numbers |  | phone_pm_numbers_sales_dashboard.jpg |
| Numbers[Construction Only] | menu › More › swipe the strip, Numbers › Construction Only | salesnum | 1.0 | 1 (1) | 3 |  |  | Numbers | First Reply —; No Next Step 0; Proposals Aging 0; Won This Quarter $210K | phone_pm_numbers_construction_only.jpg |
| Numbers[Design Only] | menu › More › swipe the strip, Numbers › Design Only | salesnum | 1.0 | 1 (1) | 3 |  |  | Numbers | First Reply —; No Next Step 0; Proposals Aging 0; Won This Quarter $210K | phone_pm_numbers_design_only.jpg |
| Numbers[By Source] | menu › More › swipe the strip, Numbers › By Source | salesnum | 1.6 | 1 (1) | 3 |  |  | Numbers | median first reply (7 le 3 h; median inquiry to agreem 48d; average won job $210k; of wins referred (67% of 100% | phone_pm_numbers_by_source.jpg |
| Numbers[By Source][Funnel] | menu › More › swipe the strip, Numbers › By Source › Funnel | salesnum | 1.1 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | phone_pm_numbers_by_source_funnel.jpg |
| Numbers[Lost and Why] | menu › More › swipe the strip, Numbers › Lost and Why | salesnum | 1.2 | 2 (1) | 3 | 2 leads, 2 contacts |  | Numbers | median first reply (7 le 3 h; median inquiry to agreem 48d; average won job $210k; of wins referred (67% of 100% | phone_pm_numbers_lost_and_why.jpg |
| People | Clients › link: People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_pm_people.jpg |
| People[Clients] | Clients › link: People › Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_pm_people_clients.jpg |
| People[Companies] | Clients › link: People › Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_pm_people_companies.jpg |
| People[Prev] | Clients › link: People › Prev | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_pm_people_prev.jpg |
| People[Next] | Clients › link: People › Next | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_pm_people_next.jpg |
| Companies | Clients › link: Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_pm_companies.jpg |
| Companies[Clients] | Clients › link: Companies › Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_pm_companies_clients.jpg |
| Companies[People] | Clients › link: Companies › People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_pm_companies_people.jpg |
| Companies[Prev] | Clients › link: Companies › Prev | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_pm_companies_prev.jpg |
| Companies[Next] | Clients › link: Companies › Next | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_pm_companies_next.jpg |
| Sales (by the link Leads 1) | Sales › link: Leads 1 | ovsales | 0.7 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_pm_leads_1.jpg |
| Sales (by the link Leads 1)[Stalled] | Sales › link: Leads 1 › Stalled | ovsales | 0.7 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_pm_leads_1_stalled.jpg |
| Numbers — Forecast | Numbers › link: Forecast | hbforecast | 1.4 | 0 (0) | 2 |  |  | Numbers |  | phone_pm_forecast.jpg |
| Numbers — Forecast[Numbers] | Numbers › link: Forecast › Numbers | salesnum | 1.1 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | phone_pm_forecast_numbers.jpg |
| Numbers — Forecast[Sales Dashboard] | Numbers › link: Forecast › Sales Dashboard | hbdash | 2.0 | 7 (2) | 1 |  |  | Numbers |  | phone_pm_forecast_sales_dashboard.jpg |
| Numbers — Forecast[Forecast Category] | Numbers › link: Forecast › Forecast Category | hbforecast | 1.3 | 0 (0) | 2 |  |  | Numbers |  | phone_pm_forecast_forecast_category.jpg |
| Numbers — Dashboard | Numbers › link: Sales Dashboard | hbdash | 2.0 | 7 (2) | 1 |  |  | Numbers |  | phone_pm_sales_dashboard.jpg |
| Numbers — Dashboard[Numbers] | Numbers › link: Sales Dashboard › Numbers | salesnum | 1.1 | 1 (1) | 3 |  |  | Numbers | First Reply 3 h; No Next Step 3; Proposals Aging 0; Won This Quarter $210K | phone_pm_sales_dashboard_numbers.jpg |
| Numbers — Dashboard[Forecast] | Numbers › link: Sales Dashboard › Forecast | hbforecast | 1.4 | 0 (0) | 2 |  |  | Numbers |  | phone_pm_sales_dashboard_forecast.jpg |

## Coordinator (Chen), phone

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Forecast | menu › More › Forecast | hbforecast | 1.4 | 0 (0) | 2 |  |  | Numbers |  | phone_coord_forecast.jpg |
| Forecast[Numbers] | menu › More › Forecast › Numbers | home | 1.2 | 1 (1) | 1 | 3 materials, 2 vendors, 1 to-dos, 1 field requests, 1 COI lapses | Chase COI | All 29 |  | phone_coord_forecast_numbers.jpg |
| Forecast[Sales Dashboard] | menu › More › Forecast › Sales Dashboard | hbdash | 2.0 | 7 (2) | 1 |  |  | Numbers |  | phone_coord_forecast_sales_dashboard.jpg |
| Forecast[Forecast Category] | menu › More › Forecast › Forecast Category | hbforecast | 1.3 | 0 (0) | 2 |  |  | Numbers |  | phone_coord_forecast_forecast_category.jpg |
| Sales Dashboard | menu › More › swipe the strip, Sales Dashboard | hbdash | 2.0 | 7 (2) | 1 |  |  | Numbers |  | phone_coord_sales_dashboard.jpg |
| Sales Dashboard[Numbers] | menu › More › swipe the strip, Sales Dashboard › Numbers | home | 1.2 | 1 (1) | 1 | 3 materials, 2 vendors, 1 to-dos, 1 field requests, 1 COI lapses | Chase COI | All 29 |  | phone_coord_sales_dashboard_numbers.jpg |
| Sales Dashboard[Forecast] | menu › More › swipe the strip, Sales Dashboard › Forecast | hbforecast | 1.4 | 0 (0) | 2 |  |  | Numbers |  | phone_coord_sales_dashboard_forecast.jpg |
| Sales | menu › More › swipe the strip, Sales | ovsales | 1.1 | 0 (0) | 1 | 6 leads, 6 contacts, 1 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_coord_sales.jpg |
| Sales[Board] | menu › More › swipe the strip, Sales › Board | ovsales | 0.9 | 0 (0) | 1 | 6 leads, 6 contacts, 2 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_coord_sales_board.jpg |
| Partners | menu › More › swipe the strip, Partners | partners | 0.7 | 0 (0) | 0 | 3 contacts, 3 companies, 3 partners | New Partner | Thank-Yous Owed 1 | Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K | phone_coord_partners.jpg |
| Playbook | menu › More › swipe the strip, Playbook | playbook | 4.4 | 5 (1) | 0 |  |  |  |  | phone_coord_playbook.jpg |
| Clients | menu › More › swipe the strip, Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_coord_clients.jpg |
| Clients[People] | menu › More › swipe the strip, Clients › People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_coord_clients_people.jpg |
| Clients[Companies] | menu › More › swipe the strip, Clients › Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_coord_clients_companies.jpg |
| Sales (by the link Leads 1) | Sales › link: Leads 1 | ovsales | 0.7 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_coord_leads_1.jpg |
| Sales (by the link Leads 1)[Stalled] | Sales › link: Leads 1 › Stalled | ovsales | 0.7 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_coord_leads_1_stalled.jpg |
| People | Clients › link: People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_coord_people.jpg |
| People[Clients] | Clients › link: People › Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_coord_people_clients.jpg |
| People[Companies] | Clients › link: People › Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_coord_people_companies.jpg |
| People[Prev] | Clients › link: People › Prev | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_coord_people_prev.jpg |
| People[Next] | Clients › link: People › Next | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_coord_people_next.jpg |
| Companies | Clients › link: Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_coord_companies.jpg |
| Companies[Clients] | Clients › link: Companies › Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_coord_companies_clients.jpg |
| Companies[People] | Clients › link: Companies › People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_coord_companies_people.jpg |
| Companies[Prev] | Clients › link: Companies › Prev | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_coord_companies_prev.jpg |
| Companies[Next] | Clients › link: Companies › Next | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_coord_companies_next.jpg |

## Designer (Sarah), phone

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Clients | menu › Clients | clients | 0.8 | 0 (0) | 0 | 5 clients, 5 contacts, 2 leads | New Client | New Client | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_designer_clients.jpg |

## Billing, phone

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Clients | bar: Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_billing_clients.jpg |
| Clients[People] | bar: Clients › People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_billing_clients_people.jpg |
| Clients[Companies] | bar: Clients › Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_billing_clients_companies.jpg |
| Forecast | menu › More › swipe the strip, Forecast | hbforecast | 1.4 | 0 (0) | 2 |  |  | Numbers |  | phone_billing_forecast.jpg |
| Forecast[Numbers] | menu › More › swipe the strip, Forecast › Numbers | home | 1.0 | 0 (0) | 1 | 3 approvals, 2 findings, 1 clients | Resolve, $16, | All 5 |  | phone_billing_forecast_numbers.jpg |
| Forecast[Sales Dashboard] | menu › More › swipe the strip, Forecast › Sales Dashboard | hbdash | 2.0 | 7 (2) | 1 |  |  | Numbers |  | phone_billing_forecast_sales_dashboard.jpg |
| Forecast[Forecast Category] | menu › More › swipe the strip, Forecast › Forecast Category | hbforecast | 1.3 | 0 (0) | 2 |  |  | Numbers |  | phone_billing_forecast_forecast_category.jpg |
| Sales Dashboard | menu › More › swipe the strip, Sales Dashboard | hbdash | 2.0 | 7 (2) | 1 |  |  | Numbers |  | phone_billing_sales_dashboard.jpg |
| Sales Dashboard[Numbers] | menu › More › swipe the strip, Sales Dashboard › Numbers | home | 1.0 | 0 (0) | 1 | 3 approvals, 2 findings, 1 clients | Resolve, $16, | All 5 |  | phone_billing_sales_dashboard_numbers.jpg |
| Sales Dashboard[Forecast] | menu › More › swipe the strip, Sales Dashboard › Forecast | hbforecast | 1.4 | 0 (0) | 2 |  |  | Numbers |  | phone_billing_sales_dashboard_forecast.jpg |
| Sales | menu › More › swipe the strip, Sales | ovsales | 1.1 | 0 (0) | 1 | 6 leads, 6 contacts, 1 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_billing_sales.jpg |
| Sales[Board] | menu › More › swipe the strip, Sales › Board | ovsales | 0.9 | 0 (0) | 1 | 6 leads, 6 contacts, 2 to-dos, 1 clients | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_billing_sales_board.jpg |
| Partners | menu › More › swipe the strip, Partners | partners | 0.7 | 0 (0) | 0 | 3 contacts, 3 companies, 3 partners | New Partner | Thank-Yous Owed 1 | Thank-Yous Owed 1; Due a Touch 1; Leads This Quarter 3; Won Through Partners $210K | phone_billing_partners.jpg |
| Playbook | menu › More › swipe the strip, Playbook | playbook | 4.4 | 5 (1) | 0 |  |  |  |  | phone_billing_playbook.jpg |
| People | Clients › link: People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_billing_people.jpg |
| People[Clients] | Clients › link: People › Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_billing_people_clients.jpg |
| People[Companies] | Clients › link: People › Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_billing_people_companies.jpg |
| People[Prev] | Clients › link: People › Prev | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_billing_people_prev.jpg |
| People[Next] | Clients › link: People › Next | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_billing_people_next.jpg |
| Companies | Clients › link: Companies | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_billing_companies.jpg |
| Companies[Clients] | Clients › link: Companies › Clients | clients | 0.9 | 0 (0) | 1 | 5 clients, 5 contacts, 2 leads | New Client | Clients | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_billing_companies_clients.jpg |
| Companies[People] | Clients › link: Companies › People | hbcontacts | 2.0 | 0 (0) | 2 | 19 contacts, 8 leads, 3 partners, 2 companies, 1 clients | New Person | Clients | Needs Follow-Up 5; New This Week 7; Unreachable 0; Decision Makers 9 | phone_billing_companies_people.jpg |
| Companies[Prev] | Clients › link: Companies › Prev | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_billing_companies_prev.jpg |
| Companies[Next] | Clients › link: Companies › Next | hbcompanies | 0.9 | 0 (0) | 2 | 1 companies | New Company | Clients |  | phone_billing_companies_next.jpg |
| Sales (by the link Leads 1) | Sales › link: Leads 1 | ovsales | 0.7 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_billing_leads_1.jpg |
| Sales (by the link Leads 1)[Stalled] | Sales › link: Leads 1 › Stalled | ovsales | 0.7 | 0 (0) | 2 | 1 leads, 1 contacts | New Lead | New Opportunity | Leads 1; Stalled 1; No Next Step 3; Open Pipeline $1.3M | phone_billing_leads_1_stalled.jpg |

## Controller, phone

| Screen | Path | View | Tall | Sections (above) | Tab groups | Records | Blue | First button | Figures | Shot |
|---|---|---|---|---|---|---|---|---|---|---|
| Clients | menu › More › swipe the strip, Clients | clients | 0.8 | 0 (0) | 0 | 5 clients, 5 contacts, 2 leads | New Client | New Client | Past Due $0; Owed to Us $92K; Unsigned 1; Waiting on Client 1 | phone_controller_clients.jpg |

