# -*- coding: utf-8 -*-
"""READ-ONLY: Register rows for webinar_dec2 with an [SG] UTM campaign — created date/time, campaign › ad set › ad.
No PII printed (no name / email / phone). TEST rows skipped."""
from __future__ import annotations

from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

SRC = "dec2"
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
reg = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, "Register")
hi = next(i for i, r in enumerate(reg[:8]) if "UTM Campaign" in r)
h = reg[hi]
print("columns:", [c for c in h if c and (c.lower().startswith("utm") or not any(x in c.lower() for x in ("name", "email", "phone", "experience", "remark")))])
AD = next((c for c in h if c and c.lower().startswith("utm") and "ad" in c.lower() and "set" not in c.lower()), None)
n = 0
for r in (dict(zip(h, x)) for x in reg[hi + 1:]):
    if SRC not in (r.get("Source") or "").lower():
        continue
    if any("test" in (v or "").lower() for k, v in r.items() if k and ("name" in k.lower() or "email" in k.lower())):
        continue
    u = (r.get("UTM Campaign") or "").strip()
    if "[sg]" not in u.lower():
        continue
    n += 1
    print(f"   {(r.get('Created date') or '')[:19]} · {u} › {r.get('UTM Ads Set') or ''} › {r.get(AD) or '' if AD else ''}"
          f" · placement {r.get('UTM Placement') or ''}")
print(f"SG dec2 rows: {n}\nSG REGS DEC2 DONE (read-only)")
