# -*- coding: utf-8 -*-
"""READ-ONLY (11/21 12:4x): hourly report ALERT「SG 今天 Audience Network 还在花钱 RM9」. Which SG ad set spent on AN today,
and does that ad set's targeting still include audience_network? (Owner removed AN from 8 SG ad sets 11/20 12:02; SG CBO 1-3-3 was
PAUSED then and opened 11/21 10:45.) Placements are owner-only to change — this only reads."""
import datetime as dt
import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
acct = s.meta.account_path
day = NOW.date().isoformat()
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读 · SG 今天 {day} 按 ad set × 版位")
rows = g._get_all(acct + "/insights", {"fields": "adset_id,adset_name,campaign_name,spend,actions", "level": "adset",
                                       "breakdowns": "publisher_platform", "limit": "500",
                                       "time_range": json.dumps({"since": day, "until": day})})
an = [r for r in rows if r.get("publisher_platform") == "audience_network" and float(r.get("spend") or 0) > 0]
print(f"\nAN 有花钱的 ad set：{len(an)}")
for r in an:
    t = g.get_object(r["adset_id"], "targeting,status,effective_status").get("targeting") or {}
    pp = t.get("publisher_platforms")
    print(f"  {r['campaign_name']} › {r['adset_name']} · adset {r['adset_id']} · AN 今天 RM{float(r['spend']):.2f}"
          f" · targeting.publisher_platforms = {pp if pp else '（未指定 = 自动版位，含 AN）'}")
print("\n全部 ad set 今天按版位：")
for r in sorted(rows, key=lambda x: (x["campaign_name"], x["adset_name"], x.get("publisher_platform", ""))):
    if float(r.get("spend") or 0) > 0:
        print(f"  {r['campaign_name']} › {r['adset_name']} · {r.get('publisher_platform')} · RM{float(r['spend']):.2f}")
print("\nSG AN 1121 DONE (read-only)")
