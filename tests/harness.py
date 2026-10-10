"""Shared Playwright helpers. Every suite opens the build next to it (dist/), never a hardcoded path.
The app's day is pinned to 2026-09-03 (today()); seeded demo data loads on first boot."""
import os, asyncio, json
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'file://' + os.path.join(ROOT, 'dist', 'smartdesigns_projects.html')
USERS = ['u_owner', 'u_alan', 'u_chen', 'u_angel', 'u_alberto', 'u_alex', 'u_klein', 'u_sarah', 'u_billing', 'u_controller']
DESKTOP = {'width': 1440, 'height': 900}
PHONE = {'width': 390, 'height': 844}

async def open_app(p, phone=False):
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport=PHONE if phone else DESKTOP, is_mobile=phone, has_touch=phone)
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text and errs.append('console: ' + m.text))
    await pg.goto(URL)
    await pg.wait_for_function("document.body.dataset.booted==='1'", timeout=60000)
    # A phone run must lay out at the phone's width. Without the viewport meta the page lays out at 980px
    # and every sideways-scroll check passes vacuously (the round-4 recovery lost that tag).
    want = (PHONE if phone else DESKTOP)['width']
    got = await pg.evaluate('innerWidth')
    if got != want: raise SystemExit(f'layout width {got}, expected {want}: is the viewport meta missing?')
    return b, pg, errs

async def sign_in(pg, uid):
    await pg.evaluate("u => { signIn(u); render(); }", uid)
    await pg.wait_for_timeout(150)

async def go(pg, view):
    await pg.evaluate("v => { view = v; render(); }", view)
    await pg.wait_for_timeout(120)

class Checks:
    def __init__(self): self.n = 0; self.fail = []
    def ok(self, cond, msg):
        self.n += 1
        if not cond: self.fail.append(msg); print('FAIL', msg)
    def done(self):
        print('ALL PASS' if not self.fail else f'{len(self.fail)} FAILED', f'({self.n} checks)')
        return 0 if not self.fail else 1

async def attach_workspace(pg, uid, path=None):
    """Load a workspace JSON for `uid` into the open page (gsAttachWorkspace), so gcDemoConnect() serves it as
    the Loaded Workspace. The file comes from an absolute path OUTSIDE the repo, or from the env var
    SD_WORKSPACE_<UID> (e.g. SD_WORKSPACE_u_chen); a path inside the repo is refused, so a real mailbox never
    lands in the tree (CLAUDE.md, Privacy). docs/ARCHITECTURE.md ("Demo Workspace") has the JSON shape."""
    path = path or os.environ.get('SD_WORKSPACE_' + uid) or os.environ.get('SD_WORKSPACE_' + uid.upper())
    if not path: raise SystemExit(f'attach_workspace: no path and no SD_WORKSPACE_{uid} in the environment')
    real = os.path.realpath(path)
    if not os.path.isabs(path): raise SystemExit(f'attach_workspace: {path} is not an absolute path')
    if real == os.path.realpath(ROOT) or real.startswith(os.path.realpath(ROOT) + os.sep):
        raise SystemExit(f'attach_workspace: {path} is inside the repo; workspace files stay outside it')
    with open(real, encoding='utf-8') as f: ws = json.load(f)
    return await pg.evaluate("([u, ws]) => gsAttachWorkspace(u, ws)", [uid, ws])
# ---------------------------------------------------------------- QuickBooks snapshot (BACKLOG §1.6 item 5)
def qbo_snapshot_path(path=None):
    """The snapshot lives OUTSIDE the repo and is never committed: an absolute path, or the SD_QBO_SNAPSHOT
    environment variable. A path inside the repo is refused so that no real export can be seeded or published."""
    p = path or os.environ.get('SD_QBO_SNAPSHOT') or ''
    if not p: raise ValueError('no snapshot path: pass one or set SD_QBO_SNAPSHOT')
    if not os.path.isabs(p): raise ValueError(f'the snapshot path must be absolute: {p}')
    real = os.path.realpath(p)
    root = os.path.realpath(ROOT)
    if real == root or real.startswith(root + os.sep):
        raise ValueError(f'refused: {p} is inside the repo; keep the QuickBooks snapshot outside it')
    return real

async def load_qbo_snapshot(pg, path=None):
    """Read a QuickBooks snapshot JSON from outside the repo and load it through the app's own import paths
    (qboLoad in the page). Returns qboLoad's result: counts of what was added or updated."""
    real = qbo_snapshot_path(path)
    with open(real, encoding='utf-8') as f: snap = json.load(f)
    if not isinstance(snap, dict) or snap.get('source') != 'quickbooks':
        raise ValueError('not a QuickBooks snapshot: expected {"source": "quickbooks", ...}')
    out = await pg.evaluate("s => qboLoad(s)", snap)
    await pg.wait_for_timeout(150)
    return out
