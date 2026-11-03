# -*- coding: utf-8 -*-
"""READ-ONLY「目前的广告情况」— both accounts right now: live tree campaign (budget) › ad set › ad · id with today and
Thursday-to-today spend · 报名 · CPL; account totals; human status/budget changes in the last 24h. Light on API calls."""
from __future__ import annotations

import datetime as dt
import json
import time
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow()
TODAY = (NOW + dt.timedelta(hours=8)).date()
THU = _week_start_thursday(TODAY)
f = lambda v: f"RM{v[0]:.0f}/{v[1]:.0f}" + (f"={v[0] / v[1]:.0f}" if v[1] else "")
print(f"现在 {(NOW + dt.timedelta(hours=8)):%m-%d %H:%M} MYT · 周四窗口 {THU} → {TODAY}")
for label, cfg, cc in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct, tok = s.meta.account_path, f"offsite_conversion.custom.{cc}"

    def ins(since):
        return {r["ad_id"]: (float(r.get("spend") or 0), extract_results(r.get("actions"), tok)) for r in g._get_all(
            acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "1000",
                                 "time_range": json.dumps({"since": since.isoformat(), "until": TODAY.isoformat()})})}
    td, wk = ins(TODAY), ins(THU)
    time.sleep(1)
    camps = {c["id"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name,effective_status,daily_budget", "limit": "300"})}
    sets = {a["id"]: a for a in g._get_all(acct + "/adsets", {"fields": "name,effective_status,daily_budget", "limit": "500"})}
    tree = defaultdict(lambda: defaultdict(list))
    for a in g._get_all(acct + "/ads", {"fields": "name,effective_status,campaign_id,adset_id", "limit": "2000"}):
        if a["effective_status"] == "ACTIVE":
            tree[a["campaign_id"]][a["adset_id"]].append(a)
    tot_td = [sum(v[0] for v in td.values()), sum(v[1] for v in td.values())]
    tot_wk = [sum(v[0] for v in wk.values()), sum(v[1] for v in wk.values())]
    budget = 0
    print(f"\n################ {label} · 今天 {f(tot_td)} · 周四起 {f(tot_wk)}")
    for cid, by_set in tree.items():
        c = camps[cid]
        cb = int(c.get("daily_budget") or 0) // 100
        budget += cb
        ctd = [sum(td.get(a["id"], (0, 0))[0] for l in by_set.values() for a in l), sum(td.get(a["id"], (0, 0))[1] for l in by_set.values() for a in l)]
        print(f"  «{c['name']}» · campaign {cid}" + (f" · CBO RM{cb}" if cb else "") + f" · 今天(在跑ad) {f(ctd)}")
        for sid, lst in by_set.items():
            sb = int(sets[sid].get("daily_budget") or 0) // 100
            budget += sb
            print(f"    › {sets[sid]['name']} · adset {sid}" + (f" · RM{sb}" if sb else ""))
            for a in sorted(lst, key=lambda a: -wk.get(a["id"], (0, 0))[0]):
                print(f"        · {a['name']} · ad {a['id']} · 今天 {f(td.get(a['id'], (0, 0)))} · 周四起 {f(wk.get(a['id'], (0, 0)))}")
    print(f"  {label} 在跑日预算合计 RM{budget}")
    since = int((NOW - dt.timedelta(hours=24)).replace(tzinfo=dt.timezone.utc).timestamp())
    ch = [x for x in g._get_all(acct + "/activities", {"fields": "event_time,event_type,actor_name,object_name,object_id,extra_data", "since": str(since), "limit": "500"})
          if x.get("actor_name") not in ("STOCKBLOOM-ADS", "Meta", None) and any(k in (x.get("event_type") or "") for k in ("run_status", "budget"))]
    print(f"  最近 24h 人工改动 {len(ch)} 条" + ("：" if ch else ""))
    for x in sorted(ch, key=lambda x: x["event_time"])[:15]:
        print(f"    {x['event_time'][5:16]}Z {x.get('actor_name', '')[:14]} {x['event_type']} «{(x.get('object_name') or '')[:40]}» id {x['object_id']}")
print("\nNOW DONE (read-only)")
