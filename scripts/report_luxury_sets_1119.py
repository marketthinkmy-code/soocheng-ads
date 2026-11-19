# -*- coding: utf-8 -*-
"""READ-ONLY: every past ad set whose name/campaign says luxury (MY 5.0 + MY 3.0) with its interests — to find a pure-luxury one
that does not already contain the Beer / Omakase interests (owner 11/19 CBO Luxury + Beer + Omakase)."""
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

BEER = {"beer", "wine", "alcoholic", "distilled", "bars", "nightclub", "nightlife", "champagne", "sparkling"}
OMA = {"japanese cuisine", "beef", "steak", "sushi", "wagyu", "meat", "michelin"}
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
for ac in ("act_2285351942292267", "act_759339046918885"):
    for x in sorted(g._get_all(ac + "/adsets", {"fields": "name,created_time,targeting,campaign{name}", "limit": "500"}), key=lambda x: x["created_time"]):
        if "luxury" not in (x["name"] + x["campaign"]["name"]).lower():
            continue
        fs = (x.get("targeting") or {}).get("flexible_spec") or []
        ints = [i.get("name") for f in fs for i in (f.get("interests") or [])]
        if not ints:
            continue
        low = " ".join(ints).lower()
        nb, no = sum(k in low for k in BEER), sum(k in low for k in OMA)
        print(f"{ac} {x['created_time'][:10]} «{x['campaign']['name']}» › «{x['name']}» ({x['id']}) · {len(ints)} 个兴趣 · 含酒类词 {nb} · 含日料牛排词 {no}")
        if nb == 0 and no == 0:
            print("     纯 luxury: " + ", ".join(ints))
print("LUXURY SETS DONE (read-only)")
