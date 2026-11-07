# -*- coding: utf-8 -*-
"""owner 2026-11-07「做」:
  SG  PURCHASE LAL 5% 120249918198320521 RM100→60 (its 用我的方法 ad 120249918410030521 is left to the monitor's CPA hard-stop).
  MY  DAY TRADING 120251454713670329 RM200→165 · BROAD MY 120251454704570329 RM145→175.
Names asserted first. Also reports the LAL 用我的方法 ad's current status. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = [("config.sg.yaml", "120249918198320521", "PURCHASE LAL 5% | 1-1-5 | 1017", 6000),
        ("config.my5.yaml", "120251454713670329", "DAY TRADING | 1-1-5 | 1017", 16500),
        ("config.my5.yaml", "120251454704570329", "BROAD MY | 1-1-5 | 1017", 17500)]
for cfg, oid, must, cents in PLAN:
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    o = g.get_object(oid, "name,daily_budget")
    assert must in o["name"] and "(Webinarkit)" in o["name"] and "ALL LANG" not in o["name"], f"{oid}: {o['name']}"
    print(f"  «{o['name']}» · campaign {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
a = g.get_object("120249918410030521", "name,status,effective_status")
print(f"  SG PURCHASE LAL 5% › {a['name']} · ad 120249918410030521 · now {a['status']}/{a['effective_status']}")
print("SHIFT 1107 DONE" + ("" if CONFIRM else " (dry-run)"))
