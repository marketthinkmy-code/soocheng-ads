# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-22: Register rows 10/19→today by phone country (+65 / +60 / other) × UTM present / [SG] UTM.
Tells whether SG people stopped registering or just stopped being attributed. Counts only, no PII."""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings


def cc(raw: str) -> str:
    d = re.sub(r"\D", "", raw or "")
    if d.startswith("65") and len(d) == 10 or (len(d) == 8 and d[0] in "689"):
        return "+65"
    if d.startswith("60") or d.startswith("01") or (d.startswith("1") and 9 <= len(d) <= 10):
        return "+60"
    return "其他" if d else "空"


s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
vals = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, "Register")
hi = next(i for i, r in enumerate(vals[:8]) if "UTM Campaign" in r)
h = vals[hi]
di, pi, ui = h.index("Created date"), h.index("Phone Number"), h.index("UTM Campaign")
cnt = Counter()
for r in vals[hi + 1:]:
    d = cpa.parse_date(r[di][:20]) if di < len(r) else None
    if d and d >= dt.date(2026, 10, 19):
        u = (r[ui] if ui < len(r) else "").strip().lower()
        tag = "[SG] UTM" if "[sg]" in u else ("MY UTM" if u else "无UTM")
        cnt[(d.isoformat(), cc(r[pi] if pi < len(r) else ""), tag)] += 1
for k, n in sorted(cnt.items()):
    print(f"  {k[0]} · {k[1]:<4} · {k[2]:<8} {n}")
print("REG BY COUNTRY DONE (read-only)")
