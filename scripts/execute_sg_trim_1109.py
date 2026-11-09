# -*- coding: utf-8 -*-
"""owner 2026-11-09「做」— SG too expensive after the 11/8 raise (CPM 208→330, 11/8–11/9 RM561/5 = CPL 112 on only 3 live ads):
  SG BROAD SG 120250144810670521 RM175→130 (undo the 11/8 +45). TRAVEL SG stays RM100. Name asserted first. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = [("config.sg.yaml", "120250144810670521", "BROAD SG | 1-1-5 | 1030", 13000)]
for cfg, oid, must, cents in PLAN:
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    o = g.get_object(oid, "name,daily_budget")
    assert must in o["name"] and "(Webinarkit)" in o["name"] and "ALL LANG" not in o["name"], f"{oid}: {o['name']}"
    print(f"  «{o['name']}» · campaign {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
print("SG TRIM 1109 DONE" + ("" if CONFIRM else " (dry-run)"))
