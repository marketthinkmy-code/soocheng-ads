# -*- coding: utf-8 -*-
"""Scale step 2 (owner-approved 10/22「全部根据你的建议」; scheduled 10/24). Raise only carriers under their CPL line on
10/22–10/23 (SG judged on 10/23 — 10/22 was the SG registration outage):
  MY BUSINESS OWNER 120→150 (27/44, cum 27) · DAY TRADING 96→115 (+20% only: 10/23 weak, 2-day 33) ·
  TRAVEL MY 65→80 (2-day 33) · SG LAL 5% 75→90 (10/23 91, cum 61) · SG WINNERS Investment · 盖电脑 65→80 (81, cum 66).
Held: BROAD MY (2-day 60 = line) · SG Investment · 用我的方法 (0 reg 10/23) · SG Travel · 盖电脑 (cum 203).
CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
MY = {"120251454700150329": 15000, "120251454713670329": 11500, "120251500767290329": 8000}
SG = {"120249918198320521": 9000}
SG_WIN, SG_INV_GAI = "120249964890710521", ("Investment", "Video：盖电脑，喂！", 8000)


def _set(g, oid, cents):
    o = g.get_object(oid, "name,daily_budget")
    print(f"  «{o['name']}» RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
    for oid, c in MY.items():
        _set(g, oid, c)
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
    for oid, c in SG.items():
        _set(g, oid, c)
    pre, ad_name, cents = SG_INV_GAI
    sets = [s for s in g._get_all(SG_WIN + "/adsets", {"fields": "name,status,ads{name,status}", "limit": "20"})
            if s["name"].startswith(pre) and s["status"] == "ACTIVE"
            and [a["name"] for a in (s.get("ads") or {}).get("data", []) if a.get("status") == "ACTIVE"] == [ad_name]]
    assert len(sets) == 1, f"expected exactly one Investment set with only 盖电脑 active, got {[s['name'] for s in sets]}"
    _set(g, sets[0]["id"], cents)
    print("STEP2 DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
