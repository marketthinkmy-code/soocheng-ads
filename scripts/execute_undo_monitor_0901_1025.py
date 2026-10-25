# -*- coding: utf-8 -*-
"""owner 2026-10-25「先不关」— undo the 3 ad pauses the 09:01 UTC monitor dispatch made (sent just before the owner
interrupted it): find every ad the bot (STOCKBLOOM-ADS) set Active → Inactive between 09:00 and 09:10 UTC on MY 5.0 + SG,
print id · ad set · campaign · Thu-week numbers, and set it ACTIVE again. Ban gate. CONFIRM=true writes."""
from __future__ import annotations

import datetime as dt
import json
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
T0 = int(dt.datetime(2026, 10, 25, 9, 0, tzinfo=dt.timezone.utc).timestamp())
T1 = int(dt.datetime(2026, 10, 25, 9, 10, tzinfo=dt.timezone.utc).timestamp())
CC = {"config.my5.yaml": "1048291251556714", "config.sg.yaml": "1614065190214320"}

for cfg, cc in CC.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acts = g._get_all(s.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,extra_data",
                                                            "since": str(T0), "until": str(T1), "limit": "200"})
    ids = {a["object_id"] for a in acts if a.get("actor_name") == "STOCKBLOOM-ADS" and a.get("event_type") == "update_ad_run_status"
           and '"Inactive"' in (a.get("extra_data") or "")}
    print(f"\n## {cfg}: {len(ids)} ads paused by the bot 09:00–09:10 UTC")
    for oid in ids:
        o = g.get_object(oid, "name,status,adset{name},campaign{name}")
        r = g._get_all(oid + "/insights", {"fields": "spend,actions", "time_range": json.dumps({"since": "2026-10-22", "until": "2026-10-25"})})
        r = r[0] if r else {}
        sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), f"offsite_conversion.custom.{cc}")
        print(f"  {oid} «{o['name']}» {o['status']} · {o['campaign']['name'][13:52]} › {o['adset']['name']} · 周四起 RM{sp:.0f}/{rg:.0f}")
        if compliance.is_banned(o["name"], s.compliance.banned_creatives):
            print("    ⛔ banned — not reopened"); continue
        if CONFIRM and o["status"] != "ACTIVE":
            g.update_status(oid, "ACTIVE"); time.sleep(1)
            print(f"    ✅ {g.get_object(oid, 'status')['status']}")
print("UNDO DONE" + ("" if CONFIRM else " (dry-run)"))
