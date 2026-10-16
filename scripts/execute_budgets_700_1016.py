# -*- coding: utf-8 -*-
"""owner 2026-10-16「照这个」— start the Webinarkit chains at RM700/day (learning phase on a new conversion),
raise later by 20-30% on chains under the CPL line. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = {
    "config.my5.yaml": {"120251454680840329": 12500, "120251454704570329": 10000,
                        "120251454700150329": 10000, "120251454713670329": 7500},
    "config.sg.yaml": {"120249918193090521": 10000, "120249918195380521": 7500,
                       "120249918198320521": 7500, "120249918201630521": 5000},
}


def main() -> None:
    total = 0
    for cfg, camps in PLAN.items():
        g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
        for cid, cents in camps.items():
            c = g.get_object(cid, "name,status,daily_budget")
            total += cents
            print(f"  «{c['name']}» {c['status']} RM{int(c['daily_budget']) // 100} → RM{cents // 100}")
            if CONFIRM and int(c["daily_budget"]) != cents:
                g.update_daily_budget(cid, cents); time.sleep(1)
                print(f"    ✅ RM{int(g.get_object(cid, 'daily_budget')['daily_budget']) // 100}")
    print(f"  合计 RM{total // 100}/天")
    print("BUDGETS 700 DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
