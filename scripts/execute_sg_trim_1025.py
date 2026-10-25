# -*- coding: utf-8 -*-
"""owner 2026-10-25「1 根据你的判断和决定吧」— item 1 of the SG 3-day review: pause the two SG carriers that spent with
almost no registrations: BUSINESS OWNER SG campaign (3 days RM159 · 0 reg) and the WINNERS ad set «Investment | SG 28+»
whose only live ad is 盖电脑 (3 days RM258 · 1 reg). 盖电脑 keeps running in WINNERS «LAL 5% · 盖电脑» (CPL 61).
Item 2 (raises) is NOT in this script — waits for the owner. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
BO_SG = "120250027167260521"
SG_WIN = "120249964890710521"


def pause(g, oid):
    o = g.get_object(oid, "name,status")
    print(f"  «{o['name']}» {o['status']} → PAUSED")
    if CONFIRM and o["status"] != "PAUSED":
        g.update_status(oid, "PAUSED"); time.sleep(1)
        print(f"    ✅ {g.get_object(oid, 'status')['status']}")


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
    pause(g, BO_SG)
    sets = [s for s in g._get_all(SG_WIN + "/adsets", {"fields": "name,status,ads{name,status}", "limit": "20"})
            if s["name"].startswith("Investment |") and s["status"] == "ACTIVE"
            and [a["name"] for a in (s.get("ads") or {}).get("data", []) if a.get("status") == "ACTIVE"] == ["Video：盖电脑，喂！"]]
    assert len(sets) == 1, f"expected one Investment · 盖电脑 set, got {[s['name'] for s in sets]}"
    pause(g, sets[0]["id"])
    print("SG TRIM DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
