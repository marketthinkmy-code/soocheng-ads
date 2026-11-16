# -*- coding: utf-8 -*-
"""owner 2026-11-16 ~10:0x「关盖电脑和 BROAD MY korea」(after the 11/16 morning watch: Sun 11/15 BUSINESS OWNER RM148 / 0 报名,
BROAD MY RM161 / 1 报名; korea 10/29起 CPA RM2,201). Ad-level PAUSE of exactly these two MY 5.0 ads; positions asserted first:

  · BUSINESS OWNER | 1-1-5 | 1017 › Business Owner | MY 28+ · Video：盖电脑，喂！ · ad 120251454701640329
  · BROAD MY | 1-1-5 | 1017 › Broad | MY 28+ · freestyle: korea · ad 120251456191090329

Campaigns / ad sets are not touched (both CBOs then have no live ad and stop spending). Owner-closed = final.
CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
ADS = [
    ("120251454701640329", "BUSINESS OWNER | 1-1-5 | 1017", "Business Owner | MY 28+", "盖电脑"),
    ("120251456191090329", "BROAD MY | 1-1-5 | 1017", "Broad | MY 28+", "korea"),
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
if CONFIRM:
    print("  -- 两个 campaign 还在跑的 ad：")
    for cid_name in ("BUSINESS OWNER | 1-1-5 | 1017", "BROAD MY | 1-1-5 | 1017"):
        pass
    for aid, *_ in ADS:
        c = g.get_object(aid, "campaign{id,name,daily_budget}")["campaign"]
        rows = g._get_all(c["id"] + "/ads", {"fields": "name,effective_status", "limit": "100"})
        live = [r["name"] for r in rows if r["effective_status"] == "ACTIVE"]
        print(f"    «{c['name']}» CBO RM{int(c.get('daily_budget') or 0) // 100} · 在跑 ad {len(live)} {live}")
print("CLOSE BO+BROADMY DONE" + ("" if CONFIRM else " (dry-run)"))
