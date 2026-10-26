# -*- coding: utf-8 -*-
"""READ-ONLY: SG right now — every live campaign › ad set (budget) › ad (id) with Thursday-to-today and today
spend · registrations. Positions come straight from the API (死忌 #1)."""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
THU = _week_start_thursday(TODAY)
TOK = "offsite_conversion.custom.1614065190214320"
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
acct = s.meta.account_path


def ins(since):
    return {r["ad_id"]: (float(r.get("spend") or 0), extract_results(r.get("actions"), TOK)) for r in g._get_all(
        acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "500",
                             "time_range": json.dumps({"since": since.isoformat(), "until": TODAY.isoformat()})})}


wk, td = ins(THU), ins(TODAY)
total = 0
for c in g._get_all(acct + "/campaigns", {"fields": "name,effective_status,daily_budget", "limit": "200"}):
    if c["effective_status"] != "ACTIVE":
        continue
    cb = int(c.get("daily_budget") or 0) // 100
    total += cb
    print(f"\n«{c['name']}» {'CBO RM' + str(cb) if cb else 'ABO'} · campaign {c['id']}")
    for a in g._get_all(c["id"] + "/adsets", {"fields": "name,effective_status,daily_budget", "limit": "50"}):
        if a["effective_status"] != "ACTIVE":
            continue
        ab = int(a.get("daily_budget") or 0) // 100
        total += ab
        print(f"  › {a['name']}" + (f" RM{ab}" if ab else "") + f" · adset {a['id']}")
        for ad in g._get_all(a["id"] + "/ads", {"fields": "name,effective_status", "limit": "50"}):
            if ad["effective_status"] != "ACTIVE":
                continue
            ws, wr = wk.get(ad["id"], (0.0, 0.0))
            ts, tr = td.get(ad["id"], (0.0, 0.0))
            print(f"      · {ad['name']} · ad {ad['id']} · 周四起 RM{ws:.0f}/{wr:.0f}" + (f"={ws / wr:.0f}" if wr else "")
                  + f" · 今天 RM{ts:.0f}/{tr:.0f}")
print(f"\nSG 在跑日预算合计 ≈ RM{total}\nSG STATE DONE (read-only)")
