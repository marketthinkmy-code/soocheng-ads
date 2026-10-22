# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-22: any spend since 10/17 on campaigns that are NOT Webinarkit (MY 5.0 + SG)?"""
from __future__ import annotations

import datetime as dt

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

WIN = {"since": "2026-10-17", "until": (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()}

for cfg in ("config.my5.yaml", "config.sg.yaml"):
    st = load_settings(REPO_ROOT / "config" / cfg)
    rows = graph_client(st).account_insights(st.meta.account_path, level="campaign",
                                             fields="campaign_name,spend,inline_link_clicks", time_range=WIN)
    other = [r for r in rows if "webinarkit" not in (r.get("campaign_name") or "").lower()]
    print(f"\n{cfg}: 非 Webinarkit campaign {len(other)} 条")
    for r in sorted(other, key=lambda r: -float(r.get("spend") or 0)):
        print(f"   RM{float(r.get('spend') or 0):>7.0f} · 点击 {r.get('inline_link_clicks', 0)} · {r['campaign_name'][:70]}")
print("\nNONWK DONE (read-only)")
