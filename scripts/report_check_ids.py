# -*- coding: utf-8 -*-
"""READ-ONLY: status of the 3 SG all-language campaigns (10/26) — campaign / ad set / each ad with effective_status and
review feedback, read straight from the API."""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CAMPS = ["120250072520900521", "120250072526350521", "120250072532000521"]
g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
for cid in CAMPS:
    c = g.get_object(cid, "name,effective_status,daily_budget")
    print(f"\n«{c['name']}» · campaign {cid} · {c['effective_status']} · RM{int(c.get('daily_budget') or 0) // 100}")
    for a in g._get_all(cid + "/adsets", {"fields": "name,effective_status", "limit": "5"}):
        print(f"  › {a['name']} · adset {a['id']} · {a['effective_status']}")
        for x in g._get_all(a["id"] + "/ads", {"fields": "name,effective_status,ad_review_feedback", "limit": "10"}):
            fb = x.get("ad_review_feedback")
            print(f"      · {x['name']} · ad {x['id']} · {x['effective_status']}" + (f" ⚠️ {json.dumps(fb, ensure_ascii=False)[:200]}" if fb else ""))
print("CHECK DONE (read-only)")
