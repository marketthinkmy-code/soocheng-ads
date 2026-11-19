# -*- coding: utf-8 -*-
"""READ-ONLY: where / what state are the two 1-1-3 | 1120 campaigns (owner 11/19「是建好了？paused？在哪里？my sg？」)."""
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

for label, cfg in (("MY 5.0", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    hits = [c for c in g._get_all(s.meta.account_path + "/campaigns", {"fields": "name,status,effective_status,daily_budget", "limit": "500"})
            if "1-1-3 | 1120" in c["name"]]
    print(f"## {label} {s.meta.account_path}: {len(hits)} 个")
    for c in hits:
        print(f"  «{c['name']}» · campaign {c['id']} · {c['status']}/{c['effective_status']} · CBO RM{int(c.get('daily_budget') or 0) // 100}")
        for a in g._get_all(c["id"] + "/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "20"}):
            print(f"     › {a['adset']['name']} ({a['adset']['status']}) · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']}")
print("113 STATUS DONE (read-only)")
