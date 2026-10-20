# -*- coding: utf-8 -*-
"""owner 2026-10-20「照建议」— SG Webinarkit: pause the TRAVEL campaign (RM219 · 1 reg · CPL 219, worst 4 days running);
PURCHASE LAL 5% RM50 → RM60 (+20%, CPL 67). BROAD SG is left to the monitor (over-line rules resume 10/21).
Before-value guards. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
TRAVEL = "120249918201630521"
LAL = "120249918198320521"


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
    t = g.get_object(TRAVEL, "name,status")
    l = g.get_object(LAL, "name,status,daily_budget")
    assert "TRAVEL" in t["name"] and "LAL 5%" in l["name"], (t, l)
    print(f"  «{t['name']}» {t['status']} → PAUSED")
    print(f"  «{l['name']}» RM{int(l['daily_budget']) // 100} → RM60")
    if not CONFIRM:
        print("DRY RUN"); return
    if t["status"] != "PAUSED":
        g.update_status(TRAVEL, "PAUSED"); time.sleep(1)
    if int(l["daily_budget"]) == 5000:
        g.update_daily_budget(LAL, 6000); time.sleep(1)
    else:
        print(f"  ! LAL budget was RM{int(l['daily_budget']) // 100}, not RM50 — left alone")
    t2, l2 = g.get_object(TRAVEL, "status"), g.get_object(LAL, "daily_budget")
    print(f"  ✅ TRAVEL {t2['status']} · LAL 5% RM{int(l2['daily_budget']) // 100}")
    print("SG ADJUST DONE")


if __name__ == "__main__":
    main()
