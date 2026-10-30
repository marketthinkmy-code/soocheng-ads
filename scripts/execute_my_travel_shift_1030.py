# -*- coding: utf-8 -*-
"""owner 2026-10-30「做 ①」— MY 5.0, total unchanged at RM465/day:
  PAUSE campaign «(Webinarkit) STOCKBLOOM | TRAVEL MY | 1-1-5 | 1020» 120251500767290329 (RM60);
  BUSINESS OWNER 120251454700150329 RM90→120 · LUXURY MY 120251454680840329 RM120→150.
Names read back and asserted first (死忌 #1). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PAUSE = ("120251500767290329", "TRAVEL MY")
BUDGET = [("120251454700150329", "BUSINESS OWNER", 12000), ("120251454680840329", "LUXURY MY", 15000)]

g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
oid, must = PAUSE
o = g.get_object(oid, "name,status,effective_status")
assert must in o["name"] and "(Webinarkit)" in o["name"], f"{oid} is «{o['name']}»"
print(f"  PAUSE «{o['name']}» · campaign {oid} · {o['status']}/{o['effective_status']}")
if CONFIRM and o["status"] != "PAUSED":
    g.update_status(oid, "PAUSED"); time.sleep(1)
    print(f"    ✅ now {g.get_object(oid, 'status')['status']}")
for oid, must, cents in BUDGET:
    o = g.get_object(oid, "name,daily_budget")
    assert must in o["name"] and "(Webinarkit)" in o["name"], f"{oid} is «{o['name']}»"
    print(f"  «{o['name']}» · campaign {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ now RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
print("MY TRAVEL SHIFT DONE" + ("" if CONFIRM else " (dry-run)"))
