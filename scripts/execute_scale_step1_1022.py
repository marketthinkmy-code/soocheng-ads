# -*- coding: utf-8 -*-
"""owner 2026-10-22「全部根据你的建议」(BROAD SG stays — 我跟你讲 keeps running) — scale step 1, +25-30% on chains
under their CPL line: MY TRAVEL 50→65 · MY BROAD 42→55 · SG LAL 5% 60→75 · SG WINNERS both Investment ad sets
50→65. Nothing else touched. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
MY = {"120251500767290329": 6500, "120251454704570329": 5500}
SG = {"120249918198320521": 7500}
SG_WINNERS = "120249964890710521"


def _set(g, oid, cents):
    o = g.get_object(oid, "name,daily_budget")
    print(f"  «{o['name']}» RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ now RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
    for oid, c in MY.items():
        _set(g, oid, c)
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
    for oid, c in SG.items():
        _set(g, oid, c)
    inv = [s for s in g._get_all(SG_WINNERS + "/adsets", {"fields": "name,status", "limit": "20"})
           if s["name"].startswith("Investment") and s["status"] == "ACTIVE"]
    assert len(inv) == 2, f"expected 2 Investment ad sets, got {[s['name'] for s in inv]}"
    for s in inv:
        _set(g, s["id"], 6500)
    print("STEP1 DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
