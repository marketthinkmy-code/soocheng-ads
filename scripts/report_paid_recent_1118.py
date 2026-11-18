# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/18「这个成交不是 webinarkit 的」): Paid Student List header (non-PII columns) and rows dated ≥ 11/11
grouped by date × any source-like column, so non-Webinarkit sales can be told apart. No PII printed."""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
v = sc.read_tab(s0.cpa.spreadsheet_id, s0.cpa.sales_tab)
hi = next(i for i, r in enumerate(v[:10]) if "UTM Campaign" in r)
hdr = v[hi]
safe = [h for h in hdr if h and not re.search("name|email|phone|mail|电话|名字|ic|address|地址", h, re.I)]
print("表头(不含个资): " + str(safe))
rows = [dict(zip(hdr, r)) for r in v[hi + 1:]]
c = Counter()
for r in rows:
    d = cpa.parse_date(r.get("Date", ""))
    if d and d >= dt.date(2026, 11, 11):
        c[(str(d),) + tuple((h, (r.get(h) or "")[:40]) for h in safe if h not in ("Date",) and re.search("source|utm campaign|program|课程|product|event|channel|来源|webinar", h, re.I))] += 1
for k, n in sorted(c.items()):
    print(f"   {n} · {k}")
print("PAID RECENT DONE (read-only)")
