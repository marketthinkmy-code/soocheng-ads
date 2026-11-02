# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/2 screenshot «my»): the idle MY carriers — WINNERS MY 120251533789970329 + LUXURY MY 120251454680840329.
Per ad set and ad: status, created, Thu-week (10/29→today) and lifetime spend · 报名 · CPL, ban gate, and who last turned it
off (activity log since 10/22: owner vs STOCKBLOOM-ADS monitor)."""
from __future__ import annotations

import datetime as dt
import json

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()
TOK = "offsite_conversion.custom.1048291251556714"
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
f = lambda v: f"RM{v[0]:.0f}/{v[1]:.0f}" + (f"={v[0] / v[1]:.0f}" if v[1] else "")
offby = {}
for a in sorted(g._get_all(s.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,extra_data",
                                                                  "since": str(int(dt.datetime(2026, 10, 22, tzinfo=dt.timezone.utc).timestamp())), "limit": "1000"}),
                key=lambda x: x["event_time"]):
    if "run_status" in (a.get("event_type") or "") and '"new_value":"Inactive"' in (a.get("extra_data") or "").replace(" ", ""):
        offby[a["object_id"]] = f"{a.get('actor_name')} {a['event_time'][5:16]}Z"
for cid in ("120251533789970329", "120251454680840329"):
    c = g.get_object(cid, "name,status,effective_status,daily_budget")
    wk = {r["ad_id"]: (float(r.get("spend") or 0), extract_results(r.get("actions"), TOK)) for r in g._get_all(cid + "/insights", {
        "fields": "ad_id,spend,actions", "level": "ad", "limit": "200", "time_range": json.dumps({"since": "2026-10-29", "until": TODAY})})}
    lt = {r["ad_id"]: (float(r.get("spend") or 0), extract_results(r.get("actions"), TOK)) for r in g._get_all(cid + "/insights", {
        "fields": "ad_id,spend,actions", "level": "ad", "limit": "200", "time_range": json.dumps({"since": "2026-10-01", "until": TODAY})})}
    print(f"\n«{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
    for st in g._get_all(cid + "/adsets", {"fields": "name,status,effective_status,daily_budget,created_time", "limit": "20"}):
        print(f"  › {st['name']} · adset {st['id']} · {st['status']}/{st['effective_status']} · RM{int(st.get('daily_budget') or 0) // 100} · 建 {st['created_time'][:10]}"
              + (f" · 关闭: {offby[st['id']]}" if st["id"] in offby else ""))
        for a in g._get_all(st["id"] + "/ads", {"fields": "name,status,effective_status", "limit": "20"}):
            ban = "🚫禁跑" if compliance.is_banned(a["name"], s.compliance.banned_creatives) else "ok"
            print(f"      · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']} · {ban} · 周四起 {f(wk.get(a['id'], (0, 0)))} · 10/1起 {f(lt.get(a['id'], (0, 0)))}"
                  + (f" · 关闭: {offby[a['id']]}" if a["id"] in offby else ""))
print("\nMY IDLE DONE (read-only)")
