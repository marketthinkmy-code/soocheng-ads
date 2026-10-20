# -*- coding: utf-8 -*-
"""READ-ONLY: SG WINNERS campaign state — name, ad sets with budget/status, ads with status."""
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CAMP = "120249964890710521"
g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
c = g.get_object(CAMP, "name,status,effective_status")
print(f"«{c['name']}» {c['status']}/{c['effective_status']}")
for a in g._get_all(CAMP + "/adsets", {"fields": "id,name,status,daily_budget", "limit": "10"}):
    ads = g._get_all(a["id"] + "/ads", {"fields": "name,status,effective_status", "limit": "10"})
    print(f"  {a['name']} RM{int(a['daily_budget']) // 100} {a['status']} · " + ", ".join(f"{x['name']}={x['status']}/{x['effective_status']}" for x in ads))
print("STATE DONE")
