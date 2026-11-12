# -*- coding: utf-8 -*-
"""owner 2026-11-12 22:xx「关。」— close BROAD MY's two live ads (expensive by sales / pure waste):
  korea · ad 120251456191090329 (10/29起 RM1,662 · 44 UTM 报名 → 1 成交 · CPA RM1,662)
  盖电脑 · ad 120251454707880329 (10/16起 RM106 · 0 报名)
Campaign must be «BROAD MY | 1-1-5 | 1017», ad set «Broad | MY 28+». Ad level only. Reads back. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
ADS = ["120251456191090329", "120251454707880329"]
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
print("APPLY" if CONFIRM else "DRY-RUN")
for aid in ADS:
    a = g.get_object(aid, "name,status,effective_status,adset{name},campaign{id,name}")
    assert "BROAD MY | 1-1-5 | 1017" in a["campaign"]["name"] and a["adset"]["name"] == "Broad | MY 28+", (aid, a)
    print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · {a['status']}/{a['effective_status']} → PAUSED")
    if CONFIRM and a["status"] != "PAUSED":
        g.update_status(aid, "PAUSED"); time.sleep(2)
if CONFIRM:
    time.sleep(3)
    for aid in ADS:
        b = g.get_object(aid, "status,effective_status")
        print(f"    ✅ 回读 ad {aid} · {b['status']}/{b['effective_status']}")
    live = [x for x in g._get_all("120251454704570329/ads", {"fields": "effective_status", "limit": "50"}) if x["effective_status"] == "ACTIVE"]
    print(f"    BROAD MY campaign 剩在跑 ad: {len(live)}")
print("BROAD MY CLOSE DONE" + ("" if CONFIRM else " (dry-run)"))
