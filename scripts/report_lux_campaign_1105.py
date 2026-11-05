# -*- coding: utf-8 -*-
"""READ-ONLY: who turned off campaign «(Webinarkit) STOCKBLOOM | LUXURY MY | 1-1-5 | 1017» 120251454680840329 and when."""
from __future__ import annotations

import datetime as dt

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CID = "120251454680840329"
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
c = g.get_object(CID, "name,status,effective_status,daily_budget,adlabels")
print(f"«{c['name']}» {c['status']}/{c['effective_status']} RM{int(c.get('daily_budget') or 0) // 100} labels {[l.get('name') for l in (c.get('adlabels') or [])] if isinstance(c.get('adlabels'), list) else c.get('adlabels')}")
for x in sorted(g._get_all(s.meta.account_path + "/activities", {"fields": "event_time,event_type,actor_name,object_id,extra_data",
                                                                 "since": str(int(dt.datetime(2026, 10, 30, tzinfo=dt.timezone.utc).timestamp())), "limit": "3000"}),
                key=lambda x: x["event_time"]):
    if x.get("object_id") == CID and ("run_status" in x["event_type"] or "budget" in x["event_type"]):
        print(f"  {x['event_time'][:16]}Z {x.get('actor_name', ''):<16} {x['event_type']} · {(x.get('extra_data') or '')[:120]}")
print("LUX CAMPAIGN DONE (read-only)")
