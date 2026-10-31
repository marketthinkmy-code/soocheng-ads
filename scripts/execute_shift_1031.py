# -*- coding: utf-8 -*-
"""owner 2026-10-31「① + ②」(赚美金: owner requested review himself — we leave that ad alone).
① MY 5.0 (total stays RM465): PAUSE LUXURY MY › Luxury | MY 28+ · freestyle: korea · ad 120251456182310329;
   LUXURY MY 120251454680840329 RM150→60 · DAY TRADING 120251454713670329 RM95→135 · BROAD MY 120251454704570329 RM50→100.
② SG: PAUSE campaign DAY TRADING SG 120250027169830521 (RM80) · PURCHASE LAL 5% 120249918198320521 RM55→80.
Every name read back and asserted before writing (死忌 #1). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = {
    "config.my5.yaml": {
        "pause": [("120251456182310329", "freestyle: korea", "LUXURY MY", "Luxury | MY 28+")],
        "budget": [("120251454680840329", "LUXURY MY", 6000), ("120251454713670329", "DAY TRADING", 13500),
                   ("120251454704570329", "BROAD MY", 10000)],
    },
    "config.sg.yaml": {
        "pause": [("120250027169830521", "DAY TRADING SG", None, None)],
        "budget": [("120249918198320521", "PURCHASE LAL 5% | 1-1-5", 8000)],
    },
}
for cfg, p in PLAN.items():
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    print(f"\n## {cfg}")
    for oid, must, camp, aset in p["pause"]:
        if camp:
            o = g.get_object(oid, "name,status,campaign{name},adset{name}")
            assert must == o["name"] and camp in o["campaign"]["name"] and o["adset"]["name"] == aset, f"{oid}: {o}"
            label = f"{o['campaign']['name']} › {o['adset']['name']} · {o['name']} · ad {oid}"
        else:
            o = g.get_object(oid, "name,status")
            assert must in o["name"] and "ALL LANG" not in o["name"] and "(Webinarkit)" in o["name"], f"{oid}: {o['name']}"
            label = f"«{o['name']}» · campaign {oid}"
        print(f"  PAUSE {label} · now {o['status']}")
        if CONFIRM and o["status"] != "PAUSED":
            g.update_status(oid, "PAUSED"); time.sleep(1)
            print(f"    ✅ {g.get_object(oid, 'status')['status']}")
    for oid, must, cents in p["budget"]:
        o = g.get_object(oid, "name,daily_budget")
        assert must in o["name"] and "ALL LANG" not in o["name"] and "(Webinarkit)" in o["name"], f"{oid}: {o['name']}"
        print(f"  «{o['name']}» · campaign {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
        if CONFIRM and int(o.get("daily_budget") or 0) != cents:
            g.update_daily_budget(oid, cents); time.sleep(1)
            print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
print("\nSHIFT 1031 DONE" + ("" if CONFIRM else " (dry-run)"))
