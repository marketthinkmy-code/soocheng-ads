# -*- coding: utf-8 -*-
"""owner 2026-10-29「winners my & broad my 都放 50，my 其他可以做」— MY 5.0 daily budgets (SG untouched):
  LUXURY MY 120 (unchanged) · DAY TRADING 115→95 · BUSINESS OWNER 120→90 · TRAVEL MY 90→60 · BROAD MY 50 (unchanged) ·
  WINNERS MY › Broad · 盖电脑 65→50 · WINNERS MY › Broad · korea 65→50.  MY total RM515/day.
Each carrier's name is read back and asserted before it is changed (死忌 #1). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = [("120251454680840329", "LUXURY MY", 12000), ("120251454713670329", "DAY TRADING", 9500),
        ("120251454700150329", "BUSINESS OWNER", 9000), ("120251500767290329", "TRAVEL MY", 6000),
        ("120251454704570329", "BROAD MY", 5000), ("120251533791330329", "盖电脑", 5000),
        ("120251533794220329", "korea", 5000)]

g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
for oid, must, cents in PLAN:
    o = g.get_object(oid, "name,daily_budget")
    assert must in o["name"], f"{oid} is «{o['name']}», expected {must}"
    print(f"  «{o['name']}» · id {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
print("MY CUT DONE" + ("" if CONFIRM else " (dry-run)"))
