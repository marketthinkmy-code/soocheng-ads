# -*- coding: utf-8 -*-
"""READ-ONLY: owner「你看看我现在的最新调整」— (1) every human change (status / budget) on MY 5.0 + SG in the last
6 hours from the activity log, with campaign › ad set · id read back from the API; (2) what is live right now per
account: campaign › ad set (budget) › ad · id, with Thursday-to-today spend · registrations."""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow()
TODAY = (NOW + dt.timedelta(hours=8)).date()
THU = _week_start_thursday(TODAY)
SINCE = int((NOW - dt.timedelta(hours=6)).replace(tzinfo=dt.timezone.utc).timestamp())
ACCTS = (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))

for label, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {label}")
    acts = g._get_all(acct + "/activities", {"fields": "event_time,event_type,actor_name,object_id,object_name,extra_data",
                                             "since": str(SINCE), "limit": "500"})
    keep = [a for a in acts if a.get("actor_name") not in ("STOCKBLOOM-ADS", "Meta", None)
            and any(k in (a.get("event_type") or "") for k in ("run_status", "budget"))]
    print(f"① 最近 6 小时人工改动（{len(keep)} 条，时间为 UTC）:")
    seen = set()
    for a in sorted(keep, key=lambda x: x["event_time"]):
        try:
            ed = json.loads(a.get("extra_data") or "{}")
        except Exception:                                                # noqa: BLE001
            ed = {}
        old, new = ed.get("old_value"), ed.get("new_value")
        if isinstance(old, dict) or isinstance(new, dict):
            old = (old or {}).get("old_value", old) if isinstance(old, dict) else old
            new = (new or {}).get("new_value", new) if isinstance(new, dict) else new
        if "run_status" in a["event_type"] and new not in ("Active", "Inactive"):
            continue
        key = (a["object_id"], a["event_type"], str(new))
        if key in seen:
            continue
        seen.add(key)
        print(f"   {a['event_time'][5:16]} {a.get('actor_name', '')[:16]:<16} {a['event_type'].replace('update_', ''):<26} "
              f"«{(a.get('object_name') or '')[:50]}» id {a['object_id']} · {str(old)[:30]} → {str(new)[:30]}")
    wk = {r["ad_id"]: (float(r.get("spend") or 0), extract_results(r.get("actions"), tok)) for r in g._get_all(
        acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "500",
                             "time_range": json.dumps({"since": THU.isoformat(), "until": TODAY.isoformat()})})}
    print("② 现在在跑的（campaign › ad set › ad · id · 周四起）:")
    total = 0
    for c in g._get_all(acct + "/campaigns", {"fields": "name,effective_status,daily_budget", "limit": "200"}):
        if c["effective_status"] != "ACTIVE":
            continue
        cb = int(c.get("daily_budget") or 0) // 100
        total += cb
        print(f"   «{c['name']}» {'CBO RM' + str(cb) if cb else 'ABO'} · campaign {c['id']}")
        for a in g._get_all(c["id"] + "/adsets", {"fields": "name,effective_status,daily_budget", "limit": "50"}):
            if a["effective_status"] != "ACTIVE":
                continue
            ab = int(a.get("daily_budget") or 0) // 100
            ads = [x for x in g._get_all(a["id"] + "/ads", {"fields": "name,effective_status", "limit": "50"}) if x["effective_status"] == "ACTIVE"]
            if ab and ads:
                total += ab
            print(f"     › {a['name']}" + (f" RM{ab}" if ab else "") + f" · adset {a['id']}" + ("" if ads else " （没有在跑的 ad）"))
            for x in ads:
                sp, rg = wk.get(x["id"], (0.0, 0.0))
                print(f"         · {x['name']} · ad {x['id']} · 周四起 RM{sp:.0f}/{rg:.0f}" + (f"={sp / rg:.0f}" if rg else ""))
    print(f"   {label} 在跑日预算合计 ≈ RM{total}")
print("\nLATEST DONE (read-only)")
