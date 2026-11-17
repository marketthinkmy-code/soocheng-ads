# -*- coding: utf-8 -*-
"""owner 2026-11-17 ~12:2x (AskUserQuestion 决定 3「周四一起开」): at the 11/19 new cycle, re-open the AD layer of
  BUSINESS OWNER | 1-1-5 | 1017 › Business Owner | MY 28+ · Video：盖电脑，喂！ · ad 120251454701640329
(周四起 CPL 33 · 10/29 起 1 单 CPA RM576). The campaign layer is left to the owner (he opens campaigns by hand); the ad set is
set ACTIVE only if it is PAUSED (prep layer). BROAD MY korea is NOT re-opened (CPA RM2,201).
Refuses writes before 2026-11-19 00:00 MYT; refuses if banned / 🚫 / DISAPPROVED. CONFIRM=true writes + reads back."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
AD = "120251454701640329"
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'}")
a = g.get_object(AD, "name,status,effective_status,adset{id,name,status},campaign{id,name,status,daily_budget}")
aset, camp = a["adset"], a["campaign"]
assert "BUSINESS OWNER" in camp["name"] and aset["name"] == "Business Owner | MY 28+" and "盖电脑" in a["name"], (camp["name"], aset["name"], a["name"])
print(f"  {camp['name']} › {aset['name']} · {a['name']} · ad {AD}")
print(f"  ad {a['status']}/{a['effective_status']} · ad set {aset['id']} {aset['status']} · campaign {camp['id']} {camp['status']} CBO RM{int(camp.get('daily_budget') or 0) // 100}")
why = []
if NOW < dt.datetime(2026, 11, 19, 0, 0):
    why.append("还没到周四 11/19 00:00")
if compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]:
    why.append("禁跑素材")
if a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES"):
    why.append(f"ad 状态 {a['effective_status']}")
if why:
    print("  ⏸ 不开：" + "；".join(why))
elif CONFIRM:
    if aset["status"] == "PAUSED":
        g.update_status(aset["id"], "ACTIVE"); time.sleep(2)
    if a["status"] != "ACTIVE":
        g.update_status(AD, "ACTIVE"); time.sleep(2)
    b = g.get_object(AD, "status,effective_status,adset{status},campaign{status}")
    print(f"  ✅ 回读 ad {b['status']}/{b['effective_status']} · ad set {b['adset']['status']} · campaign {b['campaign']['status']}（campaign 层不动，留给 owner）")
else:
    print("  ✅ 条件满足（dry-run，未写入）")
print("REOPEN BO 盖电脑 1119 DONE" + ("" if CONFIRM else " (dry-run)"))
