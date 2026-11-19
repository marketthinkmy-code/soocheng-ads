# -*- coding: utf-8 -*-
"""owner 2026-11-19 10:1x「两支都关」(AskUserQuestion after the 11/19 morning watch: DAY TRADING 10/29起 0 单 —
korea RM1,584 / 35 UTM 报名, 年纪大 RM850 / 22 UTM 报名). Ad-level PAUSE of exactly these two MY 5.0 ads; positions asserted first:

  · DAY TRADING | 1-1-5 | 1017 › Day Trading | MY 28+ · freestyle: korea · ad 120251455974450329
  · DAY TRADING | 1-1-5 | 1017 › Day Trading | MY 28+ · Video：年纪大的人做不了交易？ · ad 120251454717600329

Campaign / ad set not touched (campaign layer is the owner's; the CBO RM165 then has no live ad and stops spending).
Owner-closed = final. CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
ADS = [
    ("120251455974450329", "DAY TRADING | 1-1-5 | 1017", "Day Trading | MY 28+", "korea"),
    ("120251454717600329", "DAY TRADING | 1-1-5 | 1017", "Day Trading | MY 28+", "年纪大"),
]
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
print("APPLY" if CONFIRM else "DRY-RUN")
for aid, cm, sm, am in ADS:
    a = g.get_object(aid, "name,status,effective_status,adset{name},campaign{name,status}")
    assert cm in a["campaign"]["name"] and a["adset"]["name"] == sm and am in a["name"], (aid, a)
    print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · {a['status']}/{a['effective_status']}")
    if CONFIRM and a["status"] != "PAUSED":
        g.update_status(aid, "PAUSED"); time.sleep(2)
    if CONFIRM:
        b = g.get_object(aid, "status,effective_status")
        print(f"    ✅ 回读 {b['status']}/{b['effective_status']}")
c = g.get_object(ADS[0][0], "campaign{id,name,daily_budget,status}")["campaign"]
rows = g._get_all(c["id"] + "/ads", {"fields": "name,effective_status", "limit": "100"})
live = [f"{r['name']} · ad {r['id']}" for r in rows if r["effective_status"] == "ACTIVE"]
print(f"  «{c['name']}» campaign {c['status']} · CBO RM{int(c.get('daily_budget') or 0) // 100} · 在跑 ad {len(live)} {live}")
print("CLOSE DT DONE" + ("" if CONFIRM else " (dry-run)"))
