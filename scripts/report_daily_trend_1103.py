# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/3「最近 cpl 上来了」): daily account funnel 10/15 → today for MY 5.0 + SG —
spend · 报名 · CPL · CPM · link CTR · cost/click · LPV→报名 % · frequency. Shows whether CPL moves with the weekly
webinar cycle (Wed live) or with CPM / CTR / landing conversion."""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
WD = "一二三四五六日"
for label, cfg, cc in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    tok = f"offsite_conversion.custom.{cc}"
    rows = g._get_all(s.meta.account_path + "/insights", {"fields": "spend,impressions,cpm,inline_link_clicks,inline_link_click_ctr,frequency,actions",
                                                          "time_increment": "1", "time_range": json.dumps({"since": "2026-10-15", "until": TODAY.isoformat()})})
    print(f"\n######## {label}")
    for r in rows:
        d = dt.date.fromisoformat(r["date_start"])
        sp, lc = float(r.get("spend") or 0), float(r.get("inline_link_clicks") or 0)
        lpv = sum(float(a["value"]) for a in r.get("actions") or [] if a["action_type"] == "landing_page_view")
        rg = extract_results(r.get("actions"), tok)
        print(f"   {d:%m-%d} 周{WD[d.weekday()]} RM{sp:>5.0f} · 报名 {rg:>3.0f} · CPL {sp / rg if rg else 0:>4.0f} · CPM {float(r.get('cpm') or 0):>4.0f} · "
              f"CTR {float(r.get('inline_link_click_ctr') or 0):.2f}% · RM{sp / lc if lc else 0:.2f}/click · LPV {lpv:>3.0f} · LPV→报名 {100 * rg / lpv if lpv else 0:>3.0f}%")
print("\nTREND DONE (read-only)")
