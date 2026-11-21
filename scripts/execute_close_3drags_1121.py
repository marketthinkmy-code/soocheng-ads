# -*- coding: utf-8 -*-
"""owner 2026-11-21 ~15:0x「CPL 太高了」→ AskUserQuestion →「3 支都关」.
Ad-level PAUSE of exactly these three MY 5.0 ads (veteran / CPA-hold drags in the Thursday window, 14:49 data); positions asserted first:

  · DAY TRADING | 1-1-5 | 1017 › Day Trading | MY 28+ · freestyle: korea · ad 120251455974450329（周四起 RM124 / 2，CPL 62，10/29 起 0 单）
  · BUSINESS OWNER | 1-1-5 | 1017 › Business Owner | MY 28+ · 年纪大 · ad 120251454702680329（RM61 / 0，60 天 CPA 1,242 / 1，cpa.hold 到 11/25）
  · DAY TRADING | 1-1-5 | 1017 › Day Trading | MY 28+ · 年纪大 · ad 120251454717600329（RM54 / 0，10/29 起 0 单）

Campaign / ad set not touched here (empty DAY TRADING campaign → execute_close_empty_campaigns_1120.py, WK standing rule).
Owner-closed = final. CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
TARGETS = [
    ("120251455974450329", "DAY TRADING | 1-1-5 | 1017", "Day Trading | MY 28+", "korea"),
    ("120251454702680329", "BUSINESS OWNER | 1-1-5 | 1017", "Business Owner | MY 28+", "年纪大"),
    ("120251454717600329", "DAY TRADING | 1-1-5 | 1017", "Day Trading | MY 28+", "年纪大"),
]
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
print("APPLY" if CONFIRM else "DRY-RUN")
adsets = {}
for aid, cm, sm, am in TARGETS:
    a = g.get_object(aid, "name,status,effective_status,adset{id,name,status},campaign{id,name,status,daily_budget}")
    assert cm in a["campaign"]["name"] and a["adset"]["name"] == sm and am in a["name"], a
    print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · {a['status']}/{a['effective_status']}")
    adsets[a["campaign"]["id"]] = a["campaign"]
    if CONFIRM and a["status"] != "PAUSED":
        g.update_status(aid, "PAUSED"); time.sleep(2)
    if CONFIRM:
        b = g.get_object(aid, "status,effective_status")
        print(f"    ✅ 回读 {b['status']}/{b['effective_status']}")
for cid, c in adsets.items():
    rows = g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "100"})
    live = [f"{r['adset']['name']} · {r['name']} · ad {r['id']}" for r in rows
            if r["status"] == "ACTIVE" and (r.get("adset") or {}).get("status") == "ACTIVE"]
    print(f"  campaign «{c['name']}» {c['status']} · CBO RM{int(c.get('daily_budget') or 0) // 100} · ad 层开着的 {len(live)}：{live}")
print("CLOSE 3 DRAGS 1121 DONE" + ("" if CONFIRM else " (dry-run)"))
