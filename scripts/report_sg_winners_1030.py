# -*- coding: utf-8 -*-
"""READ-ONLY: why did [SG] WINNERS (campaign 120249964890710521) spend RM304 on 10/29? Per ad: status, updated_time,
10/28 · 10/29 · 10/30 spend/reg; plus every activity on the campaign since 10/27 (any actor)."""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

CID = "120249964890710521"
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
tok = "offsite_conversion.custom.1614065190214320"
days = ("2026-10-28", "2026-10-29", "2026-10-30")
perf = {}
for d in days:
    for r in g._get_all(CID + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "200",
                                            "time_range": json.dumps({"since": d, "until": d})}):
        perf[(r["ad_id"], d)] = (float(r.get("spend") or 0), extract_results(r.get("actions"), tok))
print(f"«{g.get_object(CID, 'name')['name']}» · campaign {CID}")
for a in g._get_all(CID + "/ads", {"fields": "name,status,effective_status,updated_time,adset{name,status,daily_budget}", "limit": "200"}):
    sp = " · ".join(f"{d[5:]} RM{perf.get((a['id'], d), (0, 0))[0]:.0f}/{perf.get((a['id'], d), (0, 0))[1]:.0f}" for d in days)
    if any(perf.get((a["id"], d)) for d in days) or a["effective_status"] == "ACTIVE":
        ad_set = a.get("adset", {})
        print(f"  › {ad_set.get('name')} ({ad_set.get('status')}) · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']} · 更新 {a['updated_time'][:16]} · {sp}")
since = int(dt.datetime(2026, 10, 27, tzinfo=dt.timezone.utc).timestamp())
acts = g._get_all(s.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,object_name,extra_data", "since": str(since), "limit": "500"})
print("\n活动纪录（此 campaign 相关，UTC）:")
for x in sorted(acts, key=lambda x: x["event_time"]):
    if "WINNERS" in (x.get("object_name") or "") or x.get("object_id") == CID or "盖电脑" in (x.get("object_name") or "") or "Investment" in (x.get("object_name") or ""):
        if any(k in (x.get("event_type") or "") for k in ("run_status", "budget", "create")):
            print(f"  {x['event_time'][5:16]} {(x.get('actor_name') or '')[:16]:<16} {x['event_type']:<28} «{(x.get('object_name') or '')[:40]}» id {x['object_id']} · {(x.get('extra_data') or '')[:90]}")
print("\nSG WINNERS DONE (read-only)")
