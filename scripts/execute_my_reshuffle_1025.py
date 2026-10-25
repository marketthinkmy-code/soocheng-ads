# -*- coding: utf-8 -*-
"""owner 2026-10-25「做」— MY 5.0 3-day review: pause TRAVEL MY (3-day RM201 · 1 reg) and BROAD MY (RM148 · 2, over
the line all week); LUXURY MY 80→100 (CPL 28) · WINNERS MY «Broad · korea» 50→65 (CPL 33). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PAUSE = ["120251500767290329", "120251454704570329"]          # TRAVEL MY · BROAD MY
BUDGET = {"120251454680840329": 10000, "120251533794220329": 6500}   # LUXURY MY · WINNERS Broad · korea


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
    for oid in PAUSE:
        o = g.get_object(oid, "name,status")
        print(f"  «{o['name']}» {o['status']} → PAUSED")
        if CONFIRM and o["status"] != "PAUSED":
            g.update_status(oid, "PAUSED"); time.sleep(1)
            print(f"    ✅ {g.get_object(oid, 'status')['status']}")
    for oid, cents in BUDGET.items():
        o = g.get_object(oid, "name,daily_budget")
        print(f"  «{o['name']}» RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
        if CONFIRM and int(o.get("daily_budget") or 0) != cents:
            g.update_daily_budget(oid, cents); time.sleep(1)
            print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
    print("MY RESHUFFLE DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
