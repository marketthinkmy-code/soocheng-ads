# -*- coding: utf-8 -*-
"""owner 2026-11-12 Thursday review:「BROAD MY 的 campaign 预算从 RM275 降到 RM150」
(korea · ad 120251456191090329: 10/29起 43 UTM 报名 → 1 成交, CPA RM1,608). MY BROAD MY 120251454704570329 RM275 → RM150.
Name asserted first; only writes if the current budget is RM275. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
OID, MUST, OLD, NEW = "120251454704570329", "BROAD MY | 1-1-5 | 1017", 27500, 15000
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
o = g.get_object(OID, "name,daily_budget,status,effective_status")
assert MUST in o["name"] and "(Webinarkit)" in o["name"], f"{OID}: {o['name']}"
cur = int(o.get("daily_budget") or 0)
print(f"  «{o['name']}» · campaign {OID} · {o['status']}/{o['effective_status']} · RM{cur // 100} → RM{NEW // 100}")
if CONFIRM:
    assert cur in (OLD, NEW), f"budget is RM{cur // 100}, expected RM{OLD // 100} — not touching"
    if cur != NEW:
        g.update_daily_budget(OID, NEW); time.sleep(2)
    print(f"    ✅ 回读 RM{int(g.get_object(OID, 'daily_budget')['daily_budget']) // 100}")
print("BROAD MY 150 DONE" + ("" if CONFIRM else " (dry-run)"))
