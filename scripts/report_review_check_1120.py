# -*- coding: utf-8 -*-
"""READ-ONLY (11/20 12:0x owner removed Audience Network in Power Editor → ads re-reviewed, incl. paused ones).
Every ad in both accounts that is DISAPPROVED / WITH_ISSUES / PENDING_REVIEW / IN_PROCESS right now, banned flag included."""
import datetime as dt

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读")
for lab, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    rows = g._get_all(s.meta.account_path + "/ads", {"fields": "name,status,effective_status,adset{name},campaign{name}", "limit": "500",
                                                    "effective_status": '["DISAPPROVED","WITH_ISSUES","PENDING_REVIEW","IN_PROCESS"]'})
    print(f"\n### {lab}: {len(rows)} 支")
    for r in rows:
        b = " ⛔禁跑" if compliance.is_banned(r["name"], s.compliance.banned_creatives) else ""
        print(f"   {r['effective_status']:<15} ad {r['status']}{b} | {r['campaign']['name']} › {r['adset']['name']} · {r['name']} · ad {r['id']}")
print("\nREVIEW CHECK DONE (read-only)")
