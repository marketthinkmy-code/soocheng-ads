# -*- coding: utf-8 -*-
"""READ-ONLY: review status of every ad (incl. paused / 🚫) in the 9 MY ad sets touched 23:38 + restored 23:44 on 11/19."""
import sys

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

sys.stdout.reconfigure(line_buffering=True)
ADSETS = ["120251995666640329", "120251995661220329", "120251995652710329", "120251993987750329", "120251993979530329",
          "120251840426800329", "120251840061020329", "120251840057130329", "120251454700740329"]
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
for aid in ADSETS:
    for ad in g._get_all(aid + "/ads", {"fields": "name,status,effective_status,adset{name},campaign{name}", "limit": "50"}):
        flag = "⛔" if ad["effective_status"] in ("DISAPPROVED", "WITH_ISSUES") else ("⏳" if ad["effective_status"] in ("PENDING_REVIEW", "IN_PROCESS") else "·")
        print(f"{flag} {ad['campaign']['name'].replace('(Webinarkit) ', '')} › {ad['adset']['name']} · {ad['name']} · ad {ad['id']} — ad {ad['status']} → {ad['effective_status']}")
print("REVIEW CHECK DONE")
