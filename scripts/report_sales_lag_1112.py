# -*- coding: utf-8 -*-
"""READ-ONLY: per live, Paid Student List sales by day offset after the live (0 = live day … 6). Blank rows skipped. No PII."""
import datetime as dt
import re
from collections import Counter

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

LIVES = [dt.date(2026, 9, 23), dt.date(2026, 9, 30), dt.date(2026, 10, 7), dt.date(2026, 10, 14), dt.date(2026, 10, 21),
         dt.date(2026, 10, 28), dt.date(2026, 11, 4), dt.date(2026, 11, 11)]
digits = lambda v: re.sub(r"\D", "", v or "")
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
v = SheetsClient(s0.secrets.google_sa_json).read_tab(s0.cpa.spreadsheet_id, s0.cpa.sales_tab)
hi = next(i for i, r in enumerate(v[:10]) if "UTM Campaign" in r)
ds = [cpa.parse_date(dict(zip(v[hi], r)).get("Date", "")) for r in v[hi + 1:]
      if (dict(zip(v[hi], r)).get("Email") or "").strip() or digits(dict(zip(v[hi], r)).get("Phone Number"))]
ds = [d for d in ds if d]
tot = Counter()
for live in LIVES:
    c = Counter((d - live).days for d in ds if 0 <= (d - live).days <= 6)
    n = sum(c.values())
    if live < dt.date(2026, 11, 11):
        tot.update(c)
    print(f"直播 {live:%m/%d}: 共 {n} · " + " ".join(f"D{k}:{c.get(k, 0)}" for k in range(7)))
n = sum(tot.values())
print(f"11/11 以前合计 {n} 单: 直播当天 D0 占 {tot.get(0, 0) / n:.0%} · D1 {tot.get(1, 0) / n:.0%} · D2–D6 {sum(tot.get(k, 0) for k in range(2, 7)) / n:.0%}")
