# -*- coding: utf-8 -*-
"""READ-ONLY: owner「星期四到现在的广告如何？」— the Thu-week since 2026-10-22: per campaign / ad (same output as
report_webinarkit_since_1017 with the window moved), then per creative across campaigns per account."""
from __future__ import annotations

import json
import time
from collections import defaultdict

import report_webinarkit_since_1017 as base
from adbot import cpa
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

base.WIN["since"] = "2026-10-22"
base.main()
for (label, cfg, token, line), camps in base.PLAN.items():
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    agg = defaultdict(lambda: [0.0, 0.0])
    for cid in camps:
        for r in g._get_all(cid + "/insights", {"fields": "ad_name,spend,actions", "level": "ad", "time_range": json.dumps(base.WIN)}):
            k = cpa.creative_key(r.get("ad_name"))
            agg[k][0] += float(r.get("spend") or 0); agg[k][1] += extract_results(r.get("actions"), token)
        time.sleep(0.5)
    print(f"\n== {label} 素材（10/22 起，跨 campaign）")
    for k, (sp, rg) in sorted(agg.items(), key=lambda kv: -kv[1][0]):
        if sp >= 5:
            print(f"   {k[:30]:<30} RM{sp:>5.0f} · 报名 {rg:>3.0f} · CPL {sp / rg if rg else float('inf'):>5.0f}")
print("WEEK DONE (read-only)")
