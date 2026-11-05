# -*- coding: utf-8 -*-
"""owner 2026-11-05「② + ③」(after choosing C for the 11/5 rejections).
② reopen 4 monitor-paused ads (Thu-week reset 11/5), ad level → ACTIVE:
   LUXURY MY › Luxury | MY 28+ · Video：用我的方法 · ad 120251456455260329
   BUSINESS OWNER › Business Owner | MY 28+ · Video：用我的方法 · ad 120251456457820329
   BUSINESS OWNER › Business Owner | MY 28+ · Video：年纪大的人做不了交易？ · ad 120251454702680329
   DAY TRADING › Day Trading | MY 28+ · Video：用我的方法 · ad 120251456459470329
③ SG: PURCHASE LAL 5% 120249918198320521 RM80→100 · TRAVEL SG 120250144814410521 RM65→80.
Asserts: exact ad name + campaign + ad set; ban gate; last status change on each ad came from the monitor (STOCKBLOOM-ADS),
never from the owner by hand. CONFIRM=true writes."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
REOPEN = [("120251456455260329", "Video：用我的方法", "LUXURY MY", "Luxury | MY 28+"),
          ("120251456457820329", "Video：用我的方法", "BUSINESS OWNER", "Business Owner | MY 28+"),
          ("120251454702680329", "Video：年纪大的人做不了交易？", "BUSINESS OWNER", "Business Owner | MY 28+"),
          ("120251456459470329", "Video：用我的方法", "DAY TRADING", "Day Trading | MY 28+")]
BUDGET = [("120249918198320521", "PURCHASE LAL 5% | 1-1-5", 10000), ("120250144814410521", "TRAVEL SG | 1-1-2", 8000)]

my = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(my)
acts = g._get_all(my.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,extra_data",
                                                        "since": str(int(dt.datetime(2026, 10, 25, tzinfo=dt.timezone.utc).timestamp())), "limit": "2000"})
last_off = {}
for x in sorted(acts, key=lambda x: x["event_time"]):
    if "run_status" in (x.get("event_type") or "") and '"new_value":"Inactive"' in (x.get("extra_data") or "").replace(" ", ""):
        last_off[x["object_id"]] = x.get("actor_name")
print("## ② MY 5.0 reopen")
for aid, name, camp, aset in REOPEN:
    a = g.get_object(aid, "name,status,effective_status,campaign{name,effective_status},adset{name,effective_status}")
    assert a["name"] == name and camp in a["campaign"]["name"] and a["adset"]["name"] == aset, f"{aid}: {a}"
    assert not compliance.is_banned(a["name"], my.compliance.banned_creatives), f"{aid} banned"
    assert last_off.get(aid) == "STOCKBLOOM-ADS", f"{aid} last turned off by {last_off.get(aid)} — not the monitor, do not reopen"
    print(f"  {a['campaign']['name']}({a['campaign']['effective_status']}) › {a['adset']['name']}({a['adset']['effective_status']}) · {a['name']} · ad {aid} · {a['status']} → ACTIVE (关闭者: monitor)")
    if CONFIRM and a["status"] != "ACTIVE":
        g.update_status(aid, "ACTIVE"); time.sleep(1)
        b = g.get_object(aid, "status,effective_status")
        print(f"    ✅ {b['status']}/{b['effective_status']}")
print("## ③ SG budgets")
sg = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
for oid, must, cents in BUDGET:
    o = sg.get_object(oid, "name,daily_budget")
    assert must in o["name"] and "(Webinarkit) [SG]" in o["name"] and "ALL LANG" not in o["name"], f"{oid}: {o['name']}"
    print(f"  «{o['name']}» · campaign {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        sg.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ RM{int(sg.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
print("REOPEN+SCALE DONE" + ("" if CONFIRM else " (dry-run)"))
