# -*- coding: utf-8 -*-
"""READ-ONLY: has this exact ad ever sold? Paid Student List rows whose UTM ad name contains 赚美金 — date · amount ·
UTM campaign › ad set › ad, and whether they match the live MY 5.0 position
(Webinarkit) STOCKBLOOM | DAY TRADING | 1-1-5 | 1017 › Day Trading | MY 28+ · ad 120251454718680329. No PII."""
from __future__ import annotations

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey
from adbot.settings import REPO_ROOT, load_settings

AD = "120251454718680329"
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
a = g.get_object(AD, "name,created_time,campaign{name},adset{name}")
key = (_mkey(a["campaign"]["name"]), _mkey(a["adset"]["name"]), cpa.norm(a["name"]))
print(f"目标：{a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {AD} · 建立 {a['created_time'][:10]}")
vals = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
sales, _c, _h = cpa.parse_sales(vals, 2399.0)
hits = [x for x in sales if "赚美金" in (x.ad or "")]
print(f"\nPaid Student List 里 UTM ad 名含「赚美金」的成交：{len(hits)} 笔")
exact = 0
for x in sorted(hits, key=lambda x: (x.date is None, x.date)):
    m = (_mkey(x.campaign), _mkey(x.adset), x.ad) == key
    exact += m
    print(f"   {x.date} RM{x.amount:,.0f} · {x.campaign[:55]} › {x.adset[:30]} › {x.ad[:34]}" + ("   ← 就是这一支" if m else ""))
print(f"\n完全同一个位置（campaign + ad set + ad）的成交：{exact} 笔")
print("SALES FOR AD DONE (read-only)")
