# -*- coding: utf-8 -*-
"""READ-ONLY: the ads the monitor WOULD pause right now (MY 5.0 + SG) — ad id, name, ad set, campaign, 7-day and
Thu-week (since 10/22) spend / registrations / CPL, so the owner can compare with his Ads Manager view."""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.monitor_cpl import evaluate_account, extract_results
from adbot.settings import REPO_ROOT, load_settings

CC = {"config.my5.yaml": "1048291251556714", "config.sg.yaml": "1614065190214320"}
for cfg, cc in CC.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    print(f"\n## {cfg} (line RM{s.kpi.cpl_threshold_myr:.0f})")
    for d in evaluate_account(g, s):
        if not d.should_pause:
            continue
        a = g.get_object(d.ad_id, "name,adset{name},campaign{name}")
        r = g._get_all(d.ad_id + "/insights", {"fields": "spend,actions", "time_range": json.dumps({"since": "2026-10-22", "until": "2026-10-25"})})
        r = r[0] if r else {}
        sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), f"offsite_conversion.custom.{cc}")
        print(f"  {d.ad_id} «{a['name']}» · {a['campaign']['name'][13:50]} › {a['adset']['name']} · 7天 RM{d.spend:.0f}/{d.results:.0f}"
              f" CPL {d.cpl if d.cpl is not None else 0:.0f} · 周四起 RM{sp:.0f}/{rg:.0f} CPL {sp / rg if rg else 0:.0f} · {d.reason}")
print("WOULD PAUSE DONE (read-only)")
