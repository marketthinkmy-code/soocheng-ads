# -*- coding: utf-8 -*-
"""owner 2026-10-29「做」— SG budget shift, SG total unchanged at RM270:
  DAY TRADING SG 120250027169830521 RM80→100 (last week CPL 25) · PURCHASE LAL 5% 120249918198320521 RM75→55 (CPL 81).
Names read back and asserted first (死忌 #1). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = [("120250027169830521", "DAY TRADING SG", 10000), ("120249918198320521", "PURCHASE LAL 5% | 1-1-5", 5500)]

g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
for oid, must, cents in PLAN:
    o = g.get_object(oid, "name,daily_budget")
    assert must in o["name"] and "ALL LANG" not in o["name"], f"{oid} is «{o['name']}»"
    print(f"  «{o['name']}» · id {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ {oid} now RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
print("SG SHIFT DONE" + ("" if CONFIRM else " (dry-run)"))
