# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-23: ads the monitor (STOCKBLOOM-ADS) paused on SG / MY 5.0 since 10/22 22:00 UTC — id, name, ad set, campaign."""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

SINCE = int(dt.datetime(2026, 10, 22, 22, 0, tzinfo=dt.timezone.utc).timestamp())
for cfg in ("config.sg.yaml", "config.my5.yaml"):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acts = g._get_all(s.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,object_name,extra_data", "since": str(SINCE), "limit": "300"})
    print(f"\n## {cfg}")
    for a in acts:
        if a.get("actor_name") == "STOCKBLOOM-ADS" and "ad_run_status" in a.get("event_type", "") and '"Inactive"' in (a.get("extra_data") or ""):
            o = g.get_object(a["object_id"], "name,status,adset{name},campaign{name}")
            print(f"  {a['event_time']} {a['object_id']} «{o['name']}» {o['status']} · {o['adset']['name']} · {o['campaign']['name']}")
print("BOT PAUSES DONE")
