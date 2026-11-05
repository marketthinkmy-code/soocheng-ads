# -*- coding: utf-8 -*-
"""owner 2026-11-05「做」+「关」(全部听你的建议):
  Budgets: DAY TRADING 120251454713670329 RM135→165 · BROAD MY 120251454704570329 RM100→120 · BROAD SG 120250144810670521 RM85→105.
  PAUSE again: LUXURY MY › Luxury | MY 28+ · Video：用我的方法 · ad 120251456455260329 (reopened at ad level this morning;
  its campaign is owner-paused and the ad's last 7 days were RM81 / 0).
Names asserted first (死忌 #1). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = [("config.my5.yaml", "120251454713670329", "DAY TRADING | 1-1-5 | 1017", 16500),
        ("config.my5.yaml", "120251454704570329", "BROAD MY | 1-1-5 | 1017", 12000),
        ("config.sg.yaml", "120250144810670521", "BROAD SG | 1-1-5 | 1030", 10500)]
for cfg, oid, must, cents in PLAN:
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    o = g.get_object(oid, "name,daily_budget")
    assert must in o["name"] and "(Webinarkit)" in o["name"], f"{oid}: {o['name']}"
    print(f"  «{o['name']}» · campaign {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
AID = "120251456455260329"
a = g.get_object(AID, "name,status,campaign{name},adset{name}")
assert a["name"] == "Video：用我的方法" and "LUXURY MY" in a["campaign"]["name"] and a["adset"]["name"] == "Luxury | MY 28+", f"{AID}: {a}"
print(f"  PAUSE {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {AID} · now {a['status']}")
if CONFIRM and a["status"] != "PAUSED":
    g.update_status(AID, "PAUSED"); time.sleep(1)
    print(f"    ✅ {g.get_object(AID, 'status')['status']}")
print("BUDGET+LUX DONE" + ("" if CONFIRM else " (dry-run)"))
