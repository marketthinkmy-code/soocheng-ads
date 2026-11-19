# -*- coding: utf-8 -*-
"""owner 2026-11-19 10:1x「开回 + 修 monitor」(AskUserQuestion after the 11/19 morning watch). Reopens exactly one SG ad that the
monitor paused on 11/14 (cpl 80.21 vs line 80) while missing its sale (robust-UTM original position, 10/29起 1 单, CPA ~RM685):

  · [SG] STOCKBLOOM | BROAD SG | 1-1-5 | 1030 › Broad | SG 28+ · Video：年纪大的人做不了交易？ · ad 120250144813480521

Makes campaign / ad set / ad ACTIVE (campaign was already reopened by the owner-approved 11/19 00:00 run) and reads back the ad's
effective_status (owner 11/18: always verify the ad actually delivers). Nothing else in the campaign is opened.
Safety gate: banned / 🚫 / DISAPPROVED → refuse; any other ACTIVE ad in the campaign that is banned → refuse.
CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AID, CAMP, ASET, MUST = "120250144813480521", "BROAD SG | 1-1-5 | 1030", "Broad | SG 28+", "年纪大"
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
print("APPLY" if CONFIRM else "DRY-RUN")
a = g.get_object(AID, "name,status,effective_status,adset{id,name,status},campaign{id,name,status,daily_budget}")
aset, camp = a["adset"], a["campaign"]
assert CAMP in camp["name"] and aset["name"] == ASET and MUST in a["name"], (AID, a)
print(f"  {camp['name']} › {aset['name']} · {a['name']} · ad {AID}")
print(f"     现在 campaign {camp['status']} / ad set {aset['status']} / ad {a['status']} → 实际 {a['effective_status']}"
      f" · CBO RM{int(camp.get('daily_budget') or 0) // 100}")
assert not compliance.is_banned(a["name"], s.compliance.banned_creatives) and "🚫" not in a["name"], "banned creative"
assert a["effective_status"] not in ("DISAPPROVED", "WITH_ISSUES"), a["effective_status"]
ads = g._get_all(camp["id"] + "/ads", {"fields": "name,status,effective_status", "limit": "200"})
armed = [x for x in ads if x["status"] == "ACTIVE" and x["id"] != AID]
for x in armed:
    assert not compliance.is_banned(x["name"], s.compliance.banned_creatives) and "🚫" not in x["name"] \
        and x["effective_status"] not in ("DISAPPROVED", "WITH_ISSUES"), ("armed bad ad in campaign", x)
print(f"     campaign 里其它 ad 层 ACTIVE 的: {len(armed)} " + "；".join(f"{x['name']} · ad {x['id']} → {x['effective_status']}" for x in armed))
if CONFIRM:
    for oid, st in ((camp["id"], camp["status"]), (aset["id"], aset["status"]), (AID, a["status"])):
        if st != "ACTIVE":
            g.update_status(oid, "ACTIVE"); time.sleep(2)
    for i in range(6):
        time.sleep(5)
        b = g.get_object(AID, "status,effective_status,adset{status,effective_status},campaign{status}")
        if b["effective_status"] == "ACTIVE":
            break
    ok = b["effective_status"] == "ACTIVE"
    print(f"     {'✅' if ok else '⚠️ 还没在投放'} 回读 campaign {b['campaign']['status']} / ad set {b['adset']['status']} / ad {b['status']}"
          f" → 实际 {b['effective_status']}")
print("REOPEN SG 年纪大 DONE" + ("" if CONFIRM else " (dry-run)"))
