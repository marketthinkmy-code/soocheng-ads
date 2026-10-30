# -*- coding: utf-8 -*-
"""owner 2026-10-30「做，DAY TRADING SG 降到 80」— campaign 120250027169830521 RM100→80. Name asserted first (死忌 #1).
CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
OID, MUST, CENTS = "120250027169830521", "DAY TRADING SG", 8000

g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
o = g.get_object(OID, "name,daily_budget")
assert MUST in o["name"] and "ALL LANG" not in o["name"], f"{OID} is «{o['name']}»"
print(f"  «{o['name']}» · campaign {OID} · RM{int(o.get('daily_budget') or 0) // 100} → RM{CENTS // 100}")
if CONFIRM and int(o.get("daily_budget") or 0) != CENTS:
    g.update_daily_budget(OID, CENTS); time.sleep(1)
    print(f"    ✅ now RM{int(g.get_object(OID, 'daily_budget')['daily_budget']) // 100}")
print("SG DT 80 DONE" + ("" if CONFIRM else " (dry-run)"))
