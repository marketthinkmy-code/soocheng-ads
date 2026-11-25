# -*- coding: utf-8 -*-
"""READ-ONLY. Paid tab: full header list (column names only) and, for rows dated ≥ 11/19, WHICH columns are filled
(names of non-empty columns — never their values). Checks whether contact info sits in a column the attribution misses."""
from __future__ import annotations

import datetime as dt

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
print("Paid tab =", s0.cpa.sales_tab)
v = sc.read_tab(s0.cpa.spreadsheet_id, s0.cpa.sales_tab)
hi = next(i for i, r in enumerate(v[:10]) if "UTM Campaign" in r)
hdr = v[hi]
print("表头（全部栏位名）：", " | ".join(f"[{j}]{h}" for j, h in enumerate(hdr)))
print(f"总行数（表头以下）：{len(v) - hi - 1}")
for n, r in enumerate(v[hi + 1:], start=hi + 2):
    d = dict(zip(hdr, r))
    dd = cpa.parse_date(d.get("Date", ""))
    if dd and dd >= dt.date(2026, 11, 19):
        filled = [f"[{j}]{hdr[j] if j < len(hdr) else '?'}" for j, x in enumerate(r) if str(x).strip()]
        print(f"  第 {n} 行 · {dd:%m/%d} · 有内容的栏位：{', '.join(filled)}")
print("\nPAID FIELDS DONE (read-only, no values)")
