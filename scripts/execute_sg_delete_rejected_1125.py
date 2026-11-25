# -*- coding: utf-8 -*-
"""owner 2026-11-25「只删 2 支被拒的」（同 11/05 例外 C）— DELETE only the 2 SG ads whose owner appeal failed
(rejected 11/21, re-reviewed → still DISAPPROVED). Other copies of 炒了五年 / 我跟你讲 are NOT touched:
no PAUSE, no 🚫, not added to banned_creatives (owner's decision, recorded in CLAUDE.md).
Each ad is asserted: exact name, effective_status DISAPPROVED, campaign not ACTIVE, expected campaign. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
ADS = {"120250706569810521": ("Video：炒了五年，账户还是那个数", "120250706566080521"),   # [SG] LOW CPL · Broad | 1-1-3 | 1120
       "120250144814180521": ("Video：我跟你讲！", "120250144810670521")}               # [SG] BROAD SG | 1-1-5 | 1030
g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
for aid, (name, camp) in ADS.items():
    a = g.get_object(aid, "name,status,effective_status,campaign{id,name,status},adset{name,status}")
    assert a["name"] == name and a["effective_status"] == "DISAPPROVED" and a["campaign"]["id"] == camp \
        and a["campaign"]["status"] != "ACTIVE", f"{aid}: {a}"
    print(f"  DELETE {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · "
          f"campaign {a['campaign']['status']} / ad set {a['adset']['status']} / ad {a['status']} → {a['effective_status']}")
    if CONFIRM:
        g._request("POST", aid, data={"status": "DELETED"}); time.sleep(1)
        print(f"    ✅ 回读 {g.get_object(aid, 'status')['status']}")
print("SG DELETE REJECTED 1125 DONE" + ("" if CONFIRM else " (dry-run)"))
