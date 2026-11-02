# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/2「哪些关了的广告是 CPA 好的？」).
Per-position CPA is not measurable for the (Webinarkit) ads yet: before the 10/29 UTM fix the sheet's UTM was the
contact's FIRST touch, so (Webinarkit) positions show 0 sales. Best available proxy = CREATIVE-level CPA:
  spend on every ad whose name carries that creative (MY 3.0 + MY 5.0 + SG, 2026-07-14 → today)
  ÷ Paid Student List rows (Date in the same window) whose UTM ad name carries that creative.
Also: buyers whose UTM is a (Webinarkit) campaign, if any. No PII."""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

SINCE = dt.date(2026, 7, 14)                     # MY 3.0 went live 07-13; SG running by then
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
KEYS = {"盖电脑": lambda n: "盖电脑" in n, "freestyle: korea": lambda n: "korea" in n,
        "用我的方法": lambda n: "用我的方法" in n and "将多" not in n, "用我的方法 将多": lambda n: "将多" in n,
        "年纪大的人": lambda n: "年纪大" in n, "我跟你讲": lambda n: "我跟你讲" in n, "赚美金=求人": lambda n: "求人" in n,
        "不选 forex": lambda n: "不选 forex" in n or "不选forex" in n, "我只有一个目的": lambda n: "一个目的" in n}
spend = defaultdict(lambda: defaultdict(float))
for label, cfg in (("MY3", "config.yaml"), ("MY5", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    for r in g._get_all(s.meta.account_path + "/insights", {"fields": "ad_name,spend", "level": "ad", "limit": "500",
                                                            "time_range": json.dumps({"since": SINCE.isoformat(), "until": TODAY.isoformat()})}):
        n = (r.get("ad_name") or "").lower()
        for k, fn in KEYS.items():
            if fn(n):
                spend[k][label] += float(r.get("spend") or 0)
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sales, _c, _h = cpa.parse_sales(SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab), 2399.0)
buy, wk = defaultdict(int), 0
for x in sales:
    if not x.date or x.date < SINCE:
        continue
    n = (x.ad or "").lower()
    wk += "webinarkit" in (x.campaign or "").lower()
    for k, fn in KEYS.items():
        if fn(n):
            buy[k] += 1
print(f"窗口 {SINCE} → {TODAY}（花费 = MY3+MY5+SG；成交 = Paid Student List，按 UTM ad 名，first-touch）")
print(f"Paid 表里 UTM campaign 是 (Webinarkit) 的成交：{wk} 笔")
for k in sorted(KEYS, key=lambda k: (sum(spend[k].values()) / buy[k]) if buy[k] else 9e9):
    sp = sum(spend[k].values())
    print(f"   {k:<12} 花费 RM{sp:>7,.0f}（MY3 {spend[k]['MY3']:,.0f} · MY5 {spend[k]['MY5']:,.0f} · SG {spend[k]['SG']:,.0f}） · 成交 {buy[k]:>3} · "
          + (f"CPA RM{sp / buy[k]:,.0f}" if buy[k] else "CPA —"))
print("\nCREATIVE CPA DONE (read-only)")
