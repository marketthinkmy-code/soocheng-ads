# -*- coding: utf-8 -*-
"""owner 2026-11-09「A」— BUSINESS OWNER worse since the 11/8 raise (CPM 138→182, 11/8–11/9 RM340/3 = CPL 113, only 1 live ad):
  MY BUSINESS OWNER 120251454700150329 RM165→120 · MY BROAD MY 120251454704570329 RM230→275 (total unchanged). Names asserted first. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = [("config.my5.yaml", "120251454700150329", "BUSINESS OWNER | 1-1-5 | 1017", 12000),
        ("config.my5.yaml", "120251454704570329", "BROAD MY | 1-1-5 | 1017", 27500)]
for cfg, oid, must, cents in PLAN:
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    o = g.get_object(oid, "name,daily_budget")
    assert must in o["name"] and "(Webinarkit)" in o["name"] and "ALL LANG" not in o["name"], f"{oid}: {o['name']}"
    print(f"  «{o['name']}» · campaign {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
print("MY SHIFT 1109 DONE" + ("" if CONFIRM else " (dry-run)"))
