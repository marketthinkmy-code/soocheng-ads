# -*- coding: utf-8 -*-
"""owner 2026-11-19 14:4x「旧 1008 那 3 支开着的 ad 关掉」. Ad-level PAUSE of exactly the 3 ads still ACTIVE at the ad layer inside the
(already paused, non-Webinarkit) campaign STOCKBLOOM | DAY TRADING | 1-1-5 | 1008 · campaign 120251329144280329 — so nobody can start them by
opening the campaign. Positions asserted first; reads back. CONFIRM=true writes; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CID, CNAME, ASET = "120251329144280329", "STOCKBLOOM | DAY TRADING | 1-1-5 | 1008", "Day Trading | MY 28+"
ADS = [("120251329149060329", "盖电脑"), ("120251329157060329", "年纪大"), ("120251329160210329", "freestyle korea")]
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
print("APPLY" if CONFIRM else "DRY-RUN")
for aid, must in ADS:
    a = g.get_object(aid, "name,status,effective_status,adset{name},campaign{id,name}")
    assert a["campaign"]["id"] == CID and a["campaign"]["name"] == CNAME and a["adset"]["name"] == ASET and must in a["name"], (aid, a)
    print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · {a['status']}/{a['effective_status']}")
    if CONFIRM and a["status"] != "PAUSED":
        g.update_status(aid, "PAUSED")
        time.sleep(2)
    if CONFIRM:
        b = g.get_object(aid, "status,effective_status")
        print(f"    ✅ 回读 {b['status']}/{b['effective_status']}")
left = [x for x in g._get_all(CID + "/ads", {"fields": "name,status", "limit": "100"}) if x["status"] == "ACTIVE"]
print(f"  campaign 1008 里 ad 层还开着的: {len(left)} " + "；".join(f"{x['name']} · ad {x['id']}" for x in left))
print("CLOSE DT1008 ADS DONE" + ("" if CONFIRM else " (dry-run)"))
