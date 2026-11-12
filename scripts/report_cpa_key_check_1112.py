# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/12「改吧」— monitor CPA join to ignore the «| 1-1-4 |» segment).
A) collision check: every campaign (any status) in MY 5.0 + SG; group by the stripped key; any key shared by
   2+ DIFFERENT campaign ids is a collision (would let one campaign's sale protect another).
B) Paid Student List sales (60 days): which match a live (campaign, ad set, ad) only AFTER stripping — per ad,
   old vs new sales count, with campaign › ad set · ad id. No PII."""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey
from adbot.settings import REPO_ROOT, load_settings

SEG = re.compile(r"\|\s*\d+-\d+-\d+\s*\|")
new_key = lambda n: _mkey(SEG.sub("|", n or ""))
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
values = SheetsClient(s0.secrets.google_sa_json).read_tab(s0.cpa.spreadsheet_id, s0.cpa.sales_tab)
sales, _c, _h = cpa.parse_sales(values, s0.cpa.price_myr)
cut = TODAY - dt.timedelta(days=60)
recent = [s for s in sales if s.date and s.date > cut]
old_idx, new_idx = defaultdict(int), defaultdict(int)
for s in recent:
    old_idx[(_mkey(s.campaign), _mkey(s.adset), s.ad)] += 1
    new_idx[(new_key(s.campaign), _mkey(s.adset), s.ad)] += 1
print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT · 60 天内成交 {len(recent)} 笔")
for label, cfg in (("MY 5.0", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    acct = load_settings(REPO_ROOT / "config" / cfg).meta.account_path
    camps = g._get_all(acct + "/campaigns", {"fields": "name,effective_status", "limit": "500"})
    grp = defaultdict(list)
    for c in camps:
        grp[new_key(c["name"])].append(c)
    coll = {k: v for k, v in grp.items() if len({c["id"] for c in v}) > 1}
    print(f"\n######## {label}: {len(camps)} 个 campaign · 去掉 1-x-y 后撞名 {len(coll)} 组")
    for k, v in coll.items():
        for c in v:
            print(f"   ⚠️ 撞名 «{c['name']}» · {c['id']} · {c['effective_status']}")
    ads = g._get_all(acct + "/ads", {"fields": "name,effective_status,campaign{name},adset{name}", "limit": "2000"})
    for a in ads:
        ok_old = old_idx.get((_mkey(a["campaign"]["name"]), _mkey(a["adset"]["name"]), cpa.norm(a["name"])), 0)
        ok_new = new_idx.get((new_key(a["campaign"]["name"]), _mkey(a["adset"]["name"]), cpa.norm(a["name"])), 0)
        if ok_new != ok_old:
            print(f"   {'🟢' if a['effective_status'] == 'ACTIVE' else '⚪'} {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']}"
                  f" · {a['effective_status']} · 成交 旧 {ok_old} → 新 {ok_new}")
print("\nCPA KEY CHECK DONE (read-only)")
