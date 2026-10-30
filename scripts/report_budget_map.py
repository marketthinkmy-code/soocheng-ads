# -*- coding: utf-8 -*-
"""READ-ONLY: every live budget carrier on MY 5.0 + SG right now (CBO campaign or ABO ad set that has ≥1 live ad),
its daily budget, and last week's (Thu 10/22 → Wed 10/28) spend · registrations · CPL — for a budget re-plan.
Light on API calls; positions straight from the API."""
from __future__ import annotations

import json
import time
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

import datetime as dt
WIN = json.dumps({"since": "2026-10-29", "until": (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()})
ACCTS = (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))

for label, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    camps = {c["id"]: c for c in g._get_all(acct + "/campaigns", {"fields": "name,effective_status,daily_budget", "limit": "300"})}
    sets = {a["id"]: a for a in g._get_all(acct + "/adsets", {"fields": "name,effective_status,daily_budget,campaign_id", "limit": "500"})}
    live_ads = defaultdict(int)
    for a in g._get_all(acct + "/ads", {"fields": "effective_status,adset_id", "limit": "1000"}):
        if a.get("effective_status") == "ACTIVE":
            live_ads[a["adset_id"]] += 1
    time.sleep(1)
    perf_c = {r["campaign_id"]: r for r in g._get_all(acct + "/insights", {"fields": "campaign_id,spend,actions", "level": "campaign", "time_range": WIN, "limit": "300"})}
    perf_s = {r["adset_id"]: r for r in g._get_all(acct + "/insights", {"fields": "adset_id,spend,actions", "level": "adset", "time_range": WIN, "limit": "500"})}
    print(f"\n################ {label}")
    total = 0
    for cid, c in camps.items():
        if c["effective_status"] != "ACTIVE":
            continue
        live_sets = [a for a in sets.values() if a["campaign_id"] == cid and a["effective_status"] == "ACTIVE" and live_ads[a["id"]]]
        if not live_sets:
            continue
        cb = int(c.get("daily_budget") or 0) // 100
        if cb:
            r = perf_c.get(cid, {})
            sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), tok)
            total += cb
            print(f"  CBO RM{cb:<4} «{c['name']}» · campaign {cid} · 本周(10/29起) RM{sp:.0f}/{rg:.0f}" + (f"={sp / rg:.0f}" if rg else "") + f" · {sum(live_ads[a['id']] for a in live_sets)} ads")
        else:
            for a in live_sets:
                ab = int(a.get("daily_budget") or 0) // 100
                r = perf_s.get(a["id"], {})
                sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), tok)
                total += ab
                print(f"  ABO RM{ab:<4} «{c['name']}» › {a['name']} · adset {a['id']} · 本周(10/29起) RM{sp:.0f}/{rg:.0f}" + (f"={sp / rg:.0f}" if rg else "") + f" · {live_ads[a['id']]} ads")
    print(f"  {label} 在跑日预算合计 RM{total}")
print("\nBUDGET MAP DONE (read-only)")
