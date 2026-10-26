# -*- coding: utf-8 -*-
"""owner 2026-10-26「全部跟着你的建议做」— the open recommendations of today's watch + SG plan:
  SG: pause campaign «(Webinarkit) [SG] STOCKBLOOM | LUXURY GOODS | 1-1-5 | 1017» 120249918195380521 (Thu-week RM268 · 1).
  MY: pause the two 赚美金 test copies with ≥RM100 and ≤1 报名:
      TRAVEL MY › Travel | MY 28+ · ad 120251500771840329 (Thu-week RM84/1, since 10/16 RM110/1)
      BROAD MY › Broad | MY 28+ · ad 120251454712610329 (Thu-week RM20/0, since 10/16 RM113/1)
  (BROAD SG is already off; MY BUSINESS OWNER / DAY TRADING budgets: watch one more day — no change.)
Each object's name is printed from the API before it is paused (死忌 #1). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = (("config.sg.yaml", "120249918195380521", "LUXURY GOODS"),
        ("config.my5.yaml", "120251500771840329", "赚美金"),
        ("config.my5.yaml", "120251454712610329", "赚美金"))

for cfg, oid, must in PLAN:
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    o = g.get_object(oid, "name,status")
    where = ""
    try:
        x = g.get_object(oid, "campaign{name},adset{name}")
        where = f"{x['campaign']['name']} › {x['adset']['name']} · "
    except Exception:                                                    # noqa: BLE001  (a campaign has no parent)
        pass
    assert must in o["name"], f"{oid} is «{o['name']}», expected {must}"
    print(f"  {where}«{o['name']}» · id {oid} · {o['status']} → PAUSED")
    if CONFIRM and o["status"] != "PAUSED":
        g.update_status(oid, "PAUSED"); time.sleep(1)
        print(f"    ✅ {g.get_object(oid, 'status')['status']}")
print("OWNER ALL 1026 DONE" + ("" if CONFIRM else " (dry-run)"))
