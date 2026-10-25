"""Static check: no demo seeder can write invented records over the firm's real ones.
On the hosted copy, once the server holds the firm's records, sdSeedsOff() is true and every seeder listed in
SD_DEMO_SEEDS does nothing. A seeder declared later that is neither listed nor checks sdSeedsOff() itself would
plant demo data in the live workspace (found 2026-10-19: msgSeed, the demo's message threads, was in neither).
Every function named *Seed* must be listed, guarded, or in ALLOW below with the reason it is safe on real data.
Run: python3 seed_guard_test.py"""
import os, re, sys
H = os.path.dirname(os.path.abspath(__file__))
src = ''.join(open(os.path.join(H, '..', f), encoding='utf-8').read() + '\n' for f in ('src/app.js', 'src/mind.js', 'src/subs.js', 'src/assistant.js', 'src/livejobs.js', 'src/reports.js', 'src/loop_core.js', 'src/loop.js', 'src/meetread.js', 'src/costintel.js', 'src/specialists.js', 'src/tasks.js', 'src/taskviews.js', 'src/meeting.js', 'src/teamws.js', 'src/meetdoc_core.js', 'src/mtreview.js', 'src/p0money.js', 'src/phonerows.js', 'src/p2fix.js', 'src/items.js', 'src/field_es.js', 'src/field_es_words.js'))
ALLOW = {
    'seedUsers': 'runs only when there are no users at all (first boot of an empty copy), and never in the team\'s own workspace',
    'msgTeamSeed': "a job's first crew from its own records (time, daily logs, requests, thread lines), once per job with no crew; no demo data",
    'msgPolicySeed': 'one drafted change (stable id) for the owner to approve: the chat-records notice; a proposal, not records',
    'budgetSeedFromActuals': 'a feature: a budget from last year\'s actual books, on request',
    'seedSearches': 'default saved searches, structure not records',
    'libSeed': 'the item library\'s common items, a default the firm keeps',
    'itemAsmSeed': 'the item library\'s default assemblies (parts are library items), structure the firm keeps and edits; no records',
    'fin2SeedSignOpening': 'acts only on demo bank lines (source "seed")',
    'clSeedOptions': 'keyed by the demo\'s decision ids; no real decision matches',
    'budSeed': 'an empty budget plan structure when none exists',
    'bfSeedTypedOnly': 'a predicate on one demo bank line id',
    'bfSeedCardStatements': 'called only from bfSeed, which is guarded',
    'smSeedOne': 'called only from smSeed',
    'smSeed': 'needs the demo job p121; no real job has that id',
    'fxSeed': 'needs the demo job p121; no real job has that id',
    'stdRegionSeed': 'keyed by the demo vendors\' names (STD_DEMO_REGION)',
    'sdSeedBillDocs': 'its only caller is guarded by sdSeedsOff() (the __sdTruthSeeded block)',
    'sdSeedsOff': 'the guard itself',
}
reg = set(re.findall(r'"(\w+)"', re.search(r'const SD_DEMO_SEEDS = \[(.*?)\]', src, re.S).group(1)))
fails, n = [], 0
for m in re.finditer(r'^(?:async )?function (\w*[sS]eed\w*)\s*\(', src, re.M):
    name, n = m.group(1), n + 1
    body = src[m.end():m.end() + 800]
    if name in reg or 'sdSeedsOff' in body or name in ALLOW: continue
    fails.append(f'{name}: not in SD_DEMO_SEEDS, no sdSeedsOff() check, not in ALLOW (it could seed demo data over the firm\'s records)')
for name in ALLOW:
    if not re.search(r'^(?:async )?function ' + name + r'\s*\(', src, re.M): fails.append(f'ALLOW names {name}, which no longer exists: remove it')
for f in fails: print('FAIL', f)
print(f'{len(fails)} FAILED ({n} seeders)' if fails else f'ALL PASS ({n} seeders)')
sys.exit(1 if fails else 0)
