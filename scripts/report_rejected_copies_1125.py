# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/25「SG 申诉 ad…已经 review 后被 rejected 了」). Every ad in MY 5.0 + SG whose name carries the
炒了五年 or 我跟你讲 creative: campaign › ad set · ad ID, ad / ad set / campaign status, effective_status. No writes."""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

KEYS = ("炒了五年", "我跟你讲")
for label, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    ads = g._get_all(s.meta.account_path + "/ads", {"fields": "name,status,effective_status,adset{name,status},campaign{name,status}",
                                                     "limit": "500"})
    for k in KEYS:
        rows = [a for a in ads if k in a["name"]]
        on = [a for a in rows if a["status"] == "ACTIVE"]
        print(f"\n## {label} · {k}：{len(rows)} 支 · ad 层 ACTIVE {len(on)} 支")
        for a in sorted(rows, key=lambda a: (a["effective_status"] != "DISAPPROVED", a["status"] != "ACTIVE")):
            print(f"   {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']} — "
                  f"campaign {a['campaign']['status']} / ad set {a['adset']['status']} / ad {a['status']} → {a['effective_status']}")
print("\nREJECTED COPIES DONE (read-only)")
