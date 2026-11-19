# -*- coding: utf-8 -*-
"""READ-ONLY (owner 2026-11-19「开回 + 修 monitor」): what the monitor's sales join sees before vs after adding the
Register-UTM join. For every ad with 60-day spend, prints positions whose sale count changes, with 60d CPA old → new
and the CPA tier, plus the live ads' counts. Same position rule as before (campaign › ad set · ad). No PII."""
from __future__ import annotations

import datetime as dt
import math

from adbot import cpa
from adbot.commands import graph_client
from adbot.monitor_cpl import CPA_UNAVAILABLE, _mkey, build_cpa_context, position_sales
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
for label, cfg in (("MY 5.0", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    ctx = build_cpa_context(g, s, TODAY)
    assert ctx is not CPA_UNAVAILABLE and len(ctx) == 4, "context failed"
    sold60, _, spend60, buyers = ctx
    tiers = cpa.CpaTiers(s.cpa.healthy_max_myr, s.cpa.max_acceptable_myr, s.cpa.hard_stop_myr)
    ads = g._get_all(s.meta.account_path + "/ads", {"fields": "name,effective_status,adset{name},campaign{name}", "limit": "500"})
    n_ex = len({r for v in buyers["exact"].values() for r in v})
    n_rb = len({r for v in buyers["robust"].values() for r in v})
    print(f"\n######## {label} · 60 天 Paid 行：自带 UTM 有位置 {n_ex} · 报名表认到位置 {n_rb}")
    rows = []
    for a in ads:
        sp = spend60.get(a["id"], 0.0)
        if sp <= 0:
            continue
        ck = _mkey(a["campaign"]["name"])
        old = sold60.get((ck, _mkey(a["adset"]["name"]), cpa.norm(a["name"])), 0)
        new = position_sales(buyers, sold60, ck, a["adset"]["name"], a["name"])
        rows.append((a, sp, old, new))
    fmt = lambda sp, n: (f"RM{sp / n:,.0f} {cpa.cpa_tier(sp / n, tiers).replace('cpa_', '')}" if n else "∞")
    print("  -- 认到的单数有变化的位置:")
    for a, sp, old, new in sorted(rows, key=lambda r: (-(r[3] - r[2]), r[0]["campaign"]["name"])):
        if new != old:
            print(f"   {'🟢' if a['effective_status'] == 'ACTIVE' else '⚪'} {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']}\n"
                  f"        60天 RM{sp:,.0f} · 单数 {old} → {new} · CPA {fmt(sp, old)} → {fmt(sp, new)}")
    print("  -- 在跑的 ad:")
    for a, sp, old, new in rows:
        if a["effective_status"] == "ACTIVE":
            print(f"   🟢 {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']} · 60天 RM{sp:,.0f} · 单数 {old} → {new}")
print("\nJOIN DIFF DONE (read-only)")
