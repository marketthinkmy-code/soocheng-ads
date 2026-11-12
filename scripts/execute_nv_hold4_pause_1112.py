# -*- coding: utf-8 -*-
"""owner 2026-11-12「做」— park 4 NEW VIDEO ads with 0–1 报名 today (11/12) for 2 days; reopen Sat 11/14 00:00
(execute_nv_hold4_reopen_1114.py). Owner: 「我不想一下子预算全部放在前几天…平摊广告留子弹给 2 天后」.
Ad level only (ABO, 1 ad per ad set). Names asserted. Reads back. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
HOLD = {"120251840352430329": "Luxury Goods | MY 28+ · V2", "120251840350550329": "Luxury Goods | MY 28+ · V1",
        "120251840364150329": "Luxury Goods | MY 28+ · V4", "120251840063080329": "News | MY 28+ · V5"}
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
print("APPLY" if CONFIRM else "DRY-RUN")
for aid, aset in HOLD.items():
    a = g.get_object(aid, "name,status,effective_status,adset{name},campaign{name}")
    assert "NEW VIDEO" in a["campaign"]["name"] and a["adset"]["name"] == aset, (aid, a)
    print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · {a['status']}/{a['effective_status']} → PAUSED")
    if CONFIRM and a["status"] != "PAUSED":
        g.update_status(aid, "PAUSED"); time.sleep(2)
if CONFIRM:
    time.sleep(3)
    for aid in HOLD:
        b = g.get_object(aid, "status,effective_status")
        print(f"    ✅ 回读 ad {aid} · {b['status']}/{b['effective_status']}")
print("NV HOLD4 PAUSE DONE" + ("" if CONFIRM else " (dry-run)"))
