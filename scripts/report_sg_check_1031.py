# -*- coding: utf-8 -*-
"""READ-ONLY: current status/budget of the SG campaigns in the owner's 10/31 screenshot + ALL LANG ads (10/29→today)."""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()
tok = "offsite_conversion.custom.1614065190214320"
for cid in ("120250027169830521", "120250072526350521", "120249918198320521"):
    c = g.get_object(cid, "name,status,effective_status,daily_budget,updated_time")
    print(f"«{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · RM{int(c.get('daily_budget') or 0) // 100} · 更新 {c['updated_time'][:16]}")
for r in g._get_all("120250072526350521/insights", {"fields": "ad_id,ad_name,spend,actions,impressions", "level": "ad",
                                                     "time_range": json.dumps({"since": "2026-10-29", "until": today})}):
    print(f"   ALL LANG · {r['ad_name']} · ad {r['ad_id']} · RM{float(r['spend']):.2f} · {r['impressions']} 曝光 · {extract_results(r.get('actions'), tok):.0f} 报名")
print("SG CHECK DONE (read-only)")
