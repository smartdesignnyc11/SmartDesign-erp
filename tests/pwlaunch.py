"""One place that makes every browser launch work when Playwright's own browser build is missing.
A container can carry a Playwright whose expected Chromium build (e.g. 1255) is not installed, while the image's
Chromium (/opt/pw-browsers/chromium) is. Then every p.chromium.launch() fails before a check runs (seen 11-18:
a fresh container with Python Playwright 1.65 and Chromium 1243). Importing this module makes launch() fall back
to SD_CHROMIUM, else /opt/pw-browsers/chromium, only when the default executable does not exist and the caller
named none. harness.py imports it, so every suite that imports the harness is covered."""
import os
FALLBACK = os.environ.get('SD_CHROMIUM') or '/opt/pw-browsers/chromium'

def _wrap(cls):
    if getattr(cls.launch, '_sd_fallback', False):
        return
    orig = cls.launch
    def launch(self, *a, **kw):
        if self.name == 'chromium' and not kw.get('executable_path') and os.path.exists(FALLBACK):
            try:
                missing = not os.path.exists(self.executable_path)
            except Exception:
                missing = True
            if missing:
                kw['executable_path'] = FALLBACK
        return orig(self, *a, **kw)
    launch._sd_fallback = True
    cls.launch = launch

from playwright.async_api import BrowserType as _AsyncBT
from playwright.sync_api import BrowserType as _SyncBT
_wrap(_AsyncBT)
_wrap(_SyncBT)
