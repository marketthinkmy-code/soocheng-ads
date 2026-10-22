# -*- coding: utf-8 -*-
"""owner 2026-10-22「做」— MY 5.0 +20% on the two best Webinarkit CBOs: BUSINESS OWNER RM100 → 120 (CPL 24),
DAY TRADING RM80 → 96 (CPL 33). Roll back if 10/28 live shows 0 ad-attributed sales. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
BUDGETS = {"120251454700150329": 12000, "120251454713670329": 9600}


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
    for cid, cents in BUDGETS.items():
        c = g.get_object(cid, "name,daily_budget")
        print(f"  «{c['name']}» RM{int(c['daily_budget']) // 100} → RM{cents // 100}")
        if CONFIRM and int(c["daily_budget"]) != cents:
            g.update_daily_budget(cid, cents); time.sleep(1)
            print(f"    ✅ now RM{int(g.get_object(cid, 'daily_budget')['daily_budget']) // 100}")
    print("MY SCALE DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
