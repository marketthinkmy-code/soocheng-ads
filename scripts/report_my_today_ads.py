# -*- coding: utf-8 -*-
"""READ-ONLY: MY 5.0 today (MYT) per ad set › ad — spend, LPV, registrations; plus the same for the last 3 days total."""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
tok = "offsite_conversion.custom.1048291251556714"
for label, since in (("今天", TODAY), ("近3天", TODAY - dt.timedelta(days=2))):
    rows = g._get_all(s.meta.account_path + "/insights", {"fields": "campaign_name,adset_name,ad_name,spend,actions", "level": "ad",
                      "time_range": json.dumps({"since": since.isoformat(), "until": TODAY.isoformat()}), "limit": "200"})
    tsp = sum(float(r.get("spend") or 0) for r in rows)
    trg = sum(extract_results(r.get("actions"), tok) for r in rows)
    print(f"\n== MY {label}（{since}→{TODAY}）花 RM{tsp:.0f} · 报名 {trg:.0f} · CPL {tsp / trg if trg else 0:.0f}")
    for r in sorted(rows, key=lambda r: -float(r.get("spend") or 0)):
        sp = float(r.get("spend") or 0)
        if sp < 3:
            continue
        rg = extract_results(r.get("actions"), tok)
        print(f"   {r['campaign_name'][13:37]:<24} › {r['adset_name'][:22]:<22} › {r['ad_name'][:20]:<20} RM{sp:>4.0f} · "
              f"LPV {extract_results(r.get('actions'), 'landing_page_view'):>2.0f} · 报名 {rg:.0f}")
print("MY ADS DONE")
