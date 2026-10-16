# -*- coding: utf-8 -*-
"""owner 2026-10-16「budget 你来定」— MY 5.0 Webinarkit CBO budgets, total stays RM600/day, weighted by the
10/8-10/15 paid sales: LUXURY MY 175 (CPA 417) · BROAD MY 150 (859) · BUSINESS OWNER 150 (870) ·
DAY TRADING 125 (0 sales on RM927 despite the cheapest CPL). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
BUDGETS = {"120251454680840329": 17500, "120251454704570329": 15000,
           "120251454700150329": 15000, "120251454713670329": 12500}


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
    for cid, cents in BUDGETS.items():
        c = g.get_object(cid, "name,daily_budget")
        print(f"  «{c['name']}» RM{int(c['daily_budget']) // 100} → RM{cents // 100}")
        if CONFIRM and int(c["daily_budget"]) != cents:
            g.update_daily_budget(cid, cents); time.sleep(1)
            print(f"    ✅ RM{int(g.get_object(cid, 'daily_budget')['daily_budget']) // 100}")
    print(f"  合计 RM{sum(BUDGETS.values()) // 100}/天")
    print("MY BUDGETS DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
