# -*- coding: utf-8 -*-
"""owner 2026-11-19「MY CBO 预算 100 · SG 1-1-3 也是 100」. Campaign-level (CBO) daily budget:
  MY (Webinarkit) STOCKBLOOM | CBO · LUX BEER OMAKASE | 1-3-3 | 1120 · campaign 120251995650640329 → RM100
  SG (Webinarkit) [SG] STOCKBLOOM | BEST · Broad | 1-1-3 | 1120 · campaign 120250705800700521 → RM100
Names asserted; status not touched. CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
JOBS = [("config.my5.yaml", "120251995650640329", "(Webinarkit) STOCKBLOOM | CBO · LUX BEER OMAKASE | 1-3-3 | 1120", 10000),
        ("config.sg.yaml", "120250705800700521", "(Webinarkit) [SG] STOCKBLOOM | BEST · Broad | 1-1-3 | 1120", 10000)]
print("APPLY" if CONFIRM else "DRY-RUN")
for cfg, cid, name, cents in JOBS:
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    c = g.get_object(cid, "name,status,effective_status,daily_budget")
    assert c["name"] == name, c
    print(f"  «{c['name']}» · campaign {cid} · {c['status']}/{c['effective_status']} · RM{int(c.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(c.get("daily_budget") or 0) != cents:
        g.update_daily_budget(cid, cents)
        time.sleep(3)
    if CONFIRM:
        b = g.get_object(cid, "status,daily_budget")
        print(f"     ✅ 回读 {b['status']} · RM{int(b.get('daily_budget') or 0) // 100}")
print("BUDGET TESTS DONE" + ("" if CONFIRM else " (dry-run)"))
