"""The meeting brain reads a whole team meeting (2026-10-18).

A real multi-job team meeting, pasted as Gemini's current notes Doc, showed the brain losing most of it:
  - the Details are paragraphs ("**Heading**: text (00:01:22)"), not bullets, so none were read;
  - the Quick notes topics (headings with bullets) were not read as sections, so the job splitter had little to split;
  - the footer "Tip: ..." became a task;
  - decisions that named no job were compared with the wrong object and silently dropped;
  - steps that matched no job were titled with the first job's name while filed to none;
  - a misspelt street ("Lennox" for Lenox) matched no job;
  - an office errand that shared two words with a job's section was filed to that job;
  - a date the notes got wrong (a past month) was scheduled for next year;
  - money the meeting talked about (a vendor's mistake to recover, billing to hold, a balance) and new leads
    became nothing, or a "Bill" for the remaining balance.
This suite pastes an invented meeting in the same layout through Paste Notes, as the owner, and checks each class.
Invented data only: no real names, jobs, amounts or text from any mailbox or transcript."""
import asyncio
from harness import async_playwright, open_app, sign_in, go, Checks

NOTES = """# **✍️ Quick notes**

## **Weekly Jobs Catch Up**

Sep 3, 2026

[Chen Biron](mailto:chen@example.com) [Billing](mailto:billing@example.com) [Alan](mailto:alan@example.com)

Jobs, money and new work.

## **Credenza pricing**

  - Billing noted the credenza fabric difference on the Klein job; Alan said to keep it in work in progress.

## **Glass vendor error**

  - Keystone Glass cut the parlor panes short and the re-order cost us $1,450.

## **New work**

  - Alan sent the Lindqvist family a bid between $250,000 and $400,000 for a cellar and kitchen.

## **Next steps**

  - \\[Chen Biron\\] Verify Lennox Priority: Confirm the boiler room clean-out priority with Angel.
  - \\[Billing\\] Scan Mail: Scan the office mail on Monday.
  - \\[Billing\\] Resend Sheets: Resend the vendor hours and the LLC property sheets to Alan.
  - \\[Alan\\] Walkthrough Prep: Print the finish schedule for the 140 Prospect Place walkthrough.

**Want to see more?** [View the full notes](about:blank)
Tip: You can always access your full notes from the left sidebar.

# **📝 Full notes**

### **Summary**

Jobs, money and new work.

### **Decisions**

## **Aligned**

  - **Photograph every delivery** As a standard practice going forward, the driver photographs every delivery before signing for it.
  - **Intake form launch** Alan set a target to launch the new client intake form by the end of the year.

### **Next steps**

  - \\[Chen Biron\\] Verify Lennox Priority: Confirm the boiler room clean-out priority with Angel.

### **Details**

**Boiler Room at 206 Lennox**: Chen Biron reported the boiler room at 206 Lennox needs a clean-out before the inspector returns ([00:02:10](https://example.com/doc#h1)).

-----

**Credenza Fabric Difference**: Billing reviewed the credenza fabric for the Klein job and Alan Mishali instructed Billing not to bill the difference of $640 without explicit approval ([00:05:40](https://example.com/doc#h2)).

-----

**Keystone Glass Error**: Keystone Glass cut the parlor panes short and the re-order cost $1,450. Alan Mishali said Keystone Glass should pay us for the re-order and the extra trip ([00:08:15](https://example.com/doc#h3)).

-----

**Harbor Tile Chargeback**: Billing reported Harbor Tile has not credited the cracked boxes; Alan Mishali advised a chargeback on the card if no credit arrives within a couple of days ([00:09:30](https://example.com/doc#h4)).

-----

**Klein Billing Review**: The team reviewed the Klein billing and noted a remaining balance of $310,000 with a month of work left, so the progress billing percentages should be raised ([00:12:00](https://example.com/doc#h5)).

-----

**Prospect Place Walkthrough**: Alan Mishali said the 140 Prospect Place buyers confirmed, with a walkthrough on Friday at 9:00 AM ([00:14:20](https://example.com/doc#h6)).

-----

**Stone Delivery**: Chen Biron said the stone supplier is aiming for the week of June 20 for the slab delivery to 121 State Street ([00:16:05](https://example.com/doc#h7)).

-----

**Lindqvist Referral**: Alan Mishali reported sending the Lindqvist family a bid between $250,000 and $400,000 for a cellar and kitchen ([00:18:40](https://example.com/doc#h8)).

-----

**Hollis Referral**: Alan Mishali said the Hollis family, a referral from a past client, asked for a proposal for a parlor renovation of about $180,000 ([00:20:00](https://example.com/doc#h9)).

# **📖 Transcript**

## **Weekly Jobs Catch Up - Transcript**

**Alan:** Let's start with the boiler room.
"""

DUMP = """() => {
  const m = DB.meetings[DB.meetings.length - 1], pn = (id) => ((DB.projects.find(p => p.id === id) || {}).project || {}).name || '';
  return { title: m.title, details: (m.details || []).length, sections: (m.sections || []).map(s => s.h), decisions: (m.decisions || []).map(d => d.name || d.text),
    P: (m.proposals || []).map(x => ({ id: x.id, kind: x.kind, title: x.title, detail: x.detail || '', status: x.status, mw: !!x.mw,
      project: pn((x.apply || {}).projectId || x.projectId), due: (x.apply || {}).due || '', time: (x.apply || {}).time || '',
      notes: (x.apply || {}).notes || (x.apply || {}).note || '', rule: (x.apply || {}).rule || '' })) };
}"""


async def paste(pg):
    await go(pg, 'meetings')
    await pg.click('#mt-paste')
    await pg.fill('[data-f=title]', 'Weekly Jobs Catch Up')
    await pg.fill('[data-f=date]', '2026-09-03')
    await pg.fill('[data-f=text]', NOTES)
    await pg.locator('#mbm button', has_text='Read').first.click()
    await pg.wait_for_timeout(600)
    return await pg.evaluate(DUMP)


async def main():
    c = Checks()
    async with async_playwright() as p:
        b, pg, errs = await open_app(p)
        await sign_in(pg, 'u_owner')
        leads0 = await pg.evaluate("() => (DB.leads || []).length")
        pb0 = await pg.evaluate("() => (DB.company.playbook || []).length")
        m = await paste(pg)
        P = m['P']
        T = lambda k: [x for x in P if x['kind'] == k]
        find = lambda f: [x for x in P if f(x)]

        # Reading the current Doc layout
        c.ok(m['details'] >= 8, f"every Details paragraph is read: {m['details']} of 8")
        c.ok({'Credenza pricing', 'Glass vendor error', 'New work'} <= set(m['sections']), f"the Quick notes topics are sections: {m['sections']}")
        c.ok(not find(lambda x: x['title'].lower().startswith(('tip', 'want to see'))), 'the notes footer is not a task')

        # Filing to the right job
        lx = find(lambda x: x['title'].startswith('Verify Lennox Priority'))
        c.ok(lx and lx[0]['project'].startswith('206 Lenox'), f"a misspelt street finds its job: {[(x['title'], x['project']) for x in lx]}")
        mail = find(lambda x: x['title'].startswith('Scan Mail'))
        c.ok(mail and not mail[0]['project'] and '·' not in mail[0]['title'], f"an office step names no job in its title and files to none: {[(x['title'], x['project']) for x in mail]}")
        sh = find(lambda x: x['title'].startswith('Resend Sheets'))
        c.ok(sh and not sh[0]['project'], f"an office errand sharing two words with a job is not filed to it: {[(x['title'], x['project']) for x in sh]}")

        # Every decision is accounted for: a policy goes to the playbook, a goal becomes a dated task
        rules = [x for x in T('rule') if 'Photograph every delivery' in x['rule']]
        c.ok(len(rules) == 1, f"the standing practice is one playbook rule: {[x['rule'][:60] for x in T('rule')]}")
        goal = find(lambda x: x['kind'] == 'task' and 'Intake form' in x['title'])
        c.ok(goal and goal[0]['due'] == '2026-12-31', f"a firm goal is a task due at year end: {[(x['title'], x['due']) for x in goal]}")
        for d in m['decisions']:
            key = d.split(':')[0][:20]
            c.ok(find(lambda x: key.lower() in (x['title'] + x['detail'] + x['rule']).lower()), f'decision not dropped: {d}')

        # Money: hold, recover, never bill a balance
        hold = find(lambda x: x['title'].startswith("Hold, don't bill yet"))
        c.ok(len(hold) == 1, f"billing the meeting said to hold is one hold task: {[x['title'] for x in hold]}")
        c.ok(not find(lambda x: x['kind'] == 'billing' and 'credenza' in (x['notes'] + x['detail']).lower()), 'the held amount is never proposed as a bill')
        rk = find(lambda x: x['title'].startswith('Recover from the vendor') and 'Keystone' in x['title'] + x['detail'])
        c.ok(len(rk) == 1 and '$1,450' in rk[0]['title'] + rk[0]['detail'], f"a vendor's mistake is one recovery task with its amount: {[x['title'] for x in rk]}")
        c.ok(rk and 'raises' in rk[0]['detail'], "the recovery says why the money matters")
        rh = find(lambda x: x['title'].startswith('Recover from the vendor') and 'Harbor' in x['title'] + x['detail'])
        c.ok(len(rh) == 1, f"a chargeback ultimatum is a recovery task: {[x['title'] for x in rh]}")
        c.ok(not find(lambda x: x['kind'] == 'billing' and '$310,000' in x['title']), f"a remaining balance is never the amount of a bill: {[x['title'] for x in T('billing')]}")

        # New work and dates
        ld = [x for x in T('lead') if 'Hollis' in x['title'] + x['detail']]
        c.ok(len(ld) == 1 and ld[0]['title'].startswith('New lead') and '$180,000' in ld[0]['title'], f"a new referral with a value is one new lead: {[x['title'] for x in T('lead')]}")
        up = [x for x in T('lead') if 'Lindqvist' in x['title'] + x['detail']]
        c.ok(len(up) == 1 and up[0]['title'].startswith('Update the lead') and '$400,000' in up[0]['title'], f"a bid for a lead already in the pipeline updates it, never duplicates it: {[x['title'] for x in up]}")
        ev = [x for x in T('event') if x['due'] == '2026-09-04']
        c.ok(ev and ev[0]['time'] == '09:00' and ev[0]['project'].startswith('140 Prospect'), f"a walkthrough in a Details clause is an event on its day and job: {[(x['title'], x['due'], x['time'], x['project']) for x in T('event')]}")
        chk = find(lambda x: x['title'].startswith('Check a date in the notes'))
        c.ok(len(chk) == 1 and 'june 20' in chk[0]['detail'].lower(), f"a date before the meeting is asked about: {[x['title'] for x in chk]}")
        c.ok(not find(lambda x: x['due'].startswith('2027')), f"nothing is scheduled a year out from a slip: {[(x['title'], x['due']) for x in P if x['due'].startswith('2027')]}")

        # Approve all: the records land where people look
        await pg.evaluate("() => { const m = DB.meetings[DB.meetings.length - 1]; openMeeting(m.id); }")
        await pg.wait_for_timeout(300)
        await pg.click('#mt-okall')
        await pg.wait_for_timeout(600)
        after = await pg.evaluate("""() => { const m = DB.meetings[DB.meetings.length - 1];
          return { left: m.proposals.filter(x => x.status === 'proposed').length,
            lead: (DB.leads || []).find(l => /hollis/i.test(l.name + ' ' + (l.notes || ''))) || null,
            known: (DB.leads || []).filter(l => /lindqvist/i.test(l.name)).map(l => ({ stage: l.stage, value: l.value, notes: l.notes || '' })),
            leads: (DB.leads || []).length, pb: (DB.company.playbook || []).map(r => r.text) }; }""")
        c.ok(after['left'] == 0, f"Approve All leaves nothing proposed: {after['left']}")
        c.ok(after['leads'] == leads0 + 1 and after['lead'] and after['lead'].get('source') == 'Meeting' and after['lead'].get('nextDue'), f"the lead is in the pipeline with a follow-up date: {after['lead']}")
        k = after['known']
        c.ok(len(k) == 1 and k[0]['value'] == 400000 and 'Weekly Jobs Catch Up' in k[0]['notes'], f"the existing lead now shows the bid, its value and the meeting: {k}")
        c.ok(len(after['pb']) > pb0 and any('Photograph every delivery' in t for t in after['pb']), "the rule is in the firm's playbook")
        await go(pg, 'leads')
        txt = await pg.evaluate("document.body.innerText")
        c.ok('Hollis' in txt, 'the new lead is findable on Leads')
        c.ok(not errs, f'no page errors: {errs[:3]}')
        await b.close()
    return c.done()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
