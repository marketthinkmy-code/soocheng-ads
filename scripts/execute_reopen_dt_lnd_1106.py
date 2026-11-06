# -*- coding: utf-8 -*-
"""owner 2026-11-06「开」— reopen DAY TRADING › Day Trading | MY 28+ · Video：年纪大的人做不了交易？ · ad 120251454717600329
(veteran: since 10/16 RM403 / 17 报名 = CPL 24; monitor paused it 11/6 09:20 MYT on Thu-week RM63/1). Asserts exact position and
that the monitor (not the owner) paused it. CONFIRM=true writes."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AID = "120251454717600329"
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
a = g.get_object(AID, "name,status,effective_status,campaign{name,status},adset{name,status}")
assert a["name"] == "Video：年纪大的人做不了交易？" and "DAY TRADING" in a["campaign"]["name"] and a["adset"]["name"] == "Day Trading | MY 28+", a
assert not compliance.is_banned(a["name"], s.compliance.banned_creatives)
last = None
for x in sorted(g._get_all(s.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,extra_data",
                                                                 "since": str(int(dt.datetime(2026, 11, 4, tzinfo=dt.timezone.utc).timestamp())), "limit": "2000"}),
                key=lambda x: x["event_time"]):
    if x.get("object_id") == AID and "run_status" in (x.get("event_type") or "") and '"new_value":"Inactive"' in (x.get("extra_data") or "").replace(" ", ""):
        last = x.get("actor_name")
assert last == "STOCKBLOOM-ADS", f"last turned off by {last}"
print(f"  {a['campaign']['name']}({a['campaign']['status']}) › {a['adset']['name']}({a['adset']['status']}) · {a['name']} · ad {AID} · {a['status']} → ACTIVE (关闭者: monitor)")
if CONFIRM and a["status"] != "ACTIVE":
    g.update_status(AID, "ACTIVE"); time.sleep(1)
    b = g.get_object(AID, "status,effective_status")
    print(f"    ✅ {b['status']}/{b['effective_status']}")
print("REOPEN DT 年纪大 DONE" + ("" if CONFIRM else " (dry-run)"))
