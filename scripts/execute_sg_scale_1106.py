# -*- coding: utf-8 -*-
"""owner 2026-11-06「2」— SG small scale (SG account CPA ≈ RM536 since 10/29 vs MY ≈ RM918):
  BROAD SG 120250144810670521 RM105→130 · TRAVEL SG 120250144814410521 RM80→100. Names asserted first. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = [("120250144810670521", "BROAD SG | 1-1-5 | 1030", 13000), ("120250144814410521", "TRAVEL SG | 1-1-2 | 1030", 10000)]
g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
for oid, must, cents in PLAN:
    o = g.get_object(oid, "name,daily_budget")
    assert must in o["name"] and "(Webinarkit) [SG]" in o["name"], f"{oid}: {o['name']}"
    print(f"  «{o['name']}» · campaign {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
print("SG SCALE DONE" + ("" if CONFIRM else " (dry-run)"))
