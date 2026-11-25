# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/25「有 day trading 咩？」). Every ad in (Webinarkit) DAY TRADING | 1-1-5 | 1017: status per layer,
spend since 10/29, and the monitor's OWN 60-day CPA view (build_cpa_context + position_sales — the code the live monitor runs),
so 'would the CPA hard stop fire' is computed, not guessed. No writes."""
from __future__ import annotations

import datetime as dt
import json

from adbot import cpa
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, build_cpa_context, position_sales
from adbot.settings import REPO_ROOT, load_settings

s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
ctx = build_cpa_context(g, s, today)
sold60, _by_ad, spend60 = ctx[0], ctx[1], ctx[2]
buyers = ctx[3] if len(ctx) == 4 else None
CAMP = "120251454713670329"
c = g.get_object(CAMP, "name,status,daily_budget")
print(f"{c['name']} · campaign {CAMP} · {c['status']} · CBO RM{float(c.get('daily_budget') or 0) / 100:.0f}")
since = g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": json.dumps(
    {"since": "2026-10-29", "until": today.isoformat()}), "fields": "ad_id,spend", "limit": "500"})
sp29 = {r["ad_id"]: float(r.get("spend") or 0) for r in since}
for a in g._get_all(f"{CAMP}/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "100"}):
    n = position_sales(buyers, sold60, _mkey(c["name"]), a["adset"]["name"], a["name"])
    s60 = spend60.get(a["id"], 0.0)
    cpa60 = s60 / n if n else None
    print(f"  {c['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']} — ad set {a['adset']['status']} / ad {a['status']} → {a['effective_status']}\n"
          f"      10/29 起 RM{sp29.get(a['id'], 0):,.0f} · monitor 60 天：RM{s60:,.0f} / {n} 单 → "
          + (f"CPA RM{cpa60:,.0f}（硬线 RM{s.cpa.hard_stop_myr:,.0f}，{'已超' if cpa60 > s.cpa.hard_stop_myr else f'还差 RM{n * s.cpa.hard_stop_myr - s60:,.0f}'}）" if n else "0 单"))
print("\nDT CHECK DONE (read-only)")
