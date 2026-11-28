# -*- coding: utf-8 -*-
"""owner 2026-11-28 10:0x「开」(morning watch: Paid row 846 = nov25 sale via this ad, 10/29起 RM740 / CPA 740). Reopens exactly one MY ad that the
monitor paused 11/26 09:00 (0-reg floor, 周四起 RM81.64 / 0) before the sale reached the Paid table:

  · (Webinarkit) STOCKBLOOM | NEW VIDEO · Broad | 1-5-1 | 1110 › Broad | MY 28+ · V2 · Video：炒了五年，账户还是那个数 · ad 120251840432100329

Makes campaign (paused 11/26 09:50 by the empty-campaign rule) / ad set / ad ACTIVE and reads back the ad's effective_status.
Nothing else in the campaign is opened. Safety gate: banned / 🚫 / DISAPPROVED → refuse; any other ad in the campaign whose ad AND
ad set are both ACTIVE (= would start running with the campaign) → refuse.
CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AID, CAMP, ASET, MUST = "120251840432100329", "NEW VIDEO · Broad | 1-5-1 | 1110", "Broad | MY 28+ · V2", "炒了五年"
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
print("APPLY" if CONFIRM else "DRY-RUN")
a = g.get_object(AID, "name,status,effective_status,adset{id,name,status,daily_budget},campaign{id,name,status,daily_budget}")
aset, camp = a["adset"], a["campaign"]
assert CAMP in camp["name"] and aset["name"] == ASET and MUST in a["name"], (AID, a)
assert camp["name"].lower().startswith("(webinarkit)"), ("not a Webinarkit campaign", camp["name"])
print(f"  {camp['name']} › {aset['name']} · {a['name']} · ad {AID}")
print(f"     现在 campaign {camp['status']} / ad set {aset['status']} / ad {a['status']} → 实际 {a['effective_status']}"
      f" · ad set 预算 RM{int(aset.get('daily_budget') or camp.get('daily_budget') or 0) // 100}")
assert not compliance.is_banned(a["name"], s.compliance.banned_creatives) and "🚫" not in a["name"], "banned creative"
assert a["effective_status"] not in ("DISAPPROVED", "WITH_ISSUES"), a["effective_status"]
ads = g._get_all(camp["id"] + "/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "200"})
for x in ads:
    print(f"     · {x['adset']['name']} · {x['name']} · ad {x['id']} → ad {x['status']} / ad set {x['adset']['status']}")
armed = [x for x in ads if x["status"] == "ACTIVE" and x["adset"]["status"] == "ACTIVE" and x["id"] != AID]
for x in armed:
    assert not compliance.is_banned(x["name"], s.compliance.banned_creatives) and "🚫" not in x["name"] \
        and x["effective_status"] not in ("DISAPPROVED", "WITH_ISSUES"), ("armed bad ad in campaign", x)
print(f"     campaign 里其它会跟着跑的（ad + ad set 都 ACTIVE）: {len(armed)} " + "；".join(f"{x['name']} · ad {x['id']} → {x['effective_status']}" for x in armed))
assert not armed, "other ads would start running with the campaign; refusing"
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
print("\n-- 两个账户所有实际在投放的 ad（campaign 前面要有 (Webinarkit)）:")
for label, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s2 = load_settings(REPO_ROOT / "config" / cfg)
    g2 = graph_client(s2)
    rows = g2._get_all(s2.meta.account_path + "/ads", {"fields": "name,effective_status,adset{name,daily_budget},campaign{name,daily_budget}",
                                                      "limit": "500", "effective_status": '["ACTIVE","IN_PROCESS","PENDING_REVIEW"]'})
    for r in rows:
        ok = r["campaign"]["name"].lower().startswith("(webinarkit)")
        b = int(r["campaign"].get("daily_budget") or r["adset"].get("daily_budget") or 0) // 100
        print(f"   {'✅' if ok else '❌ 不是 Webinarkit'} {label} {r['campaign']['name']} › {r['adset']['name']} · {r['name']} · ad {r['id']} → {r['effective_status']} · RM{b}")
    if not rows:
        print(f"   {label}: 0 支")
print("REOPEN NV BROAD V2 DONE" + ("" if CONFIRM else " (dry-run)"))
