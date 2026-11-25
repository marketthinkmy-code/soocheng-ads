# -*- coding: utf-8 -*-
"""READ-ONLY preview for owner 11/25「之前跑到成绩不错的，都开」: for each candidate campaign — daily budget, status, and every
ad with all 3 layers, marking which would deliver if ONLY the campaign layer were opened (ad + ad set ACTIVE), plus banned /
rejected / non-Webinarkit flags. No writes."""
from __future__ import annotations

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

C = {"MY": ["120251454704570329", "120251995650640329", "120251993979260329", "120251993985380329"],
     "SG": ["120250144810670521", "120250706566080521"]}
for label, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    for cid in C[label]:
        c = g.get_object(cid, "name,status,effective_status,daily_budget")
        print(f"\n[{label}] {c['name']} · campaign {cid} · {c['status']} · CBO RM{float(c.get('daily_budget') or 0) / 100:.0f}"
              f"{'' if c['name'].startswith('(Webinarkit)') else ' ⚠️非Webinarkit'}")
        for a in g._get_all(f"{cid}/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "100"}):
            f = " ⛔禁跑" if (compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]) else ""
            f += " ⚠️被拒" if a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES") else ""
            run = " ← 开 campaign 就会跑" if a["status"] == "ACTIVE" and a["adset"]["status"] == "ACTIVE" else ""
            print(f"  {c['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']} — ad set {a['adset']['status']} / ad {a['status']} → {a['effective_status']}{f}{run}")
print("\nOPEN PREVIEW DONE (read-only)")
