# -*- coding: utf-8 -*-
"""READ-ONLY (owner 2026-11-19 ~21:00「CPL 都太高了，要做点什么」).
1) Per account per day 11/05 → today: spend · CPM · link CTR · LPV · 报名 · CPL · LPV→报名 (today vs the same weekday of past cycles).
2) Today per ad (both accounts): spend · CPM · CTR · LPV · 报名 · CPL · LPV→报名 — where today's money went.
3) Today per placement (both accounts): spend share · CPM · CTR · 报名 · CPL.
4) Today per hour (MYT, both accounts): spend / 报名 — is it just early in the day?"""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
D0 = dt.date(2026, 11, 5)
ACCTS = (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
f = lambda r, k: float(r.get(k) or 0)


def lpv(r):
    return extract_results(r.get("actions"), "landing_page_view")


def line(r, tok):
    sp, im, cl, lv, rg = f(r, "spend"), f(r, "impressions"), f(r, "inline_link_clicks"), lpv(r), extract_results(r.get("actions"), tok)
    return (f"RM{sp:6.0f} · CPM {sp / im * 1000 if im else 0:4.0f} · CTR {cl / im * 100 if im else 0:4.2f}% · LPV {lv:4.0f} · 报名 {rg:3.0f} · "
            f"CPL {sp / rg if rg else 0:5.0f} · LPV→报名 {rg / lv * 100 if lv else 0:5.1f}%"), sp, rg


print(f"现在 {(dt.datetime.utcnow() + dt.timedelta(hours=8)):%m-%d %H:%M} MYT · 只读")
for label, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {label}")
    print("① 每天（11/05 起）")
    for r in g._get_all(acct + "/insights", {"fields": "spend,impressions,inline_link_clicks,actions", "level": "account",
                                             "time_range": tr(D0, TODAY), "time_increment": "1", "limit": "100"}):
        d = dt.date.fromisoformat(r["date_start"])
        print(f"   {d:%m-%d %a} {line(r, tok)[0]}" + ("  ← 周四" if d.weekday() == 3 else ""))
    print("② 今天每支 ad")
    rows = g._get_all(acct + "/insights", {"fields": "ad_id,ad_name,adset_name,campaign_name,spend,impressions,inline_link_clicks,actions",
                                           "level": "ad", "time_range": tr(TODAY, TODAY), "limit": "500"})
    for r in sorted(rows, key=lambda x: -f(x, "spend")):
        if f(r, "spend") < 1:
            continue
        print(f"   {r['campaign_name'].replace('(Webinarkit) ', '')} › {r['adset_name']} · {r['ad_name']} · ad {r['ad_id']}")
        print(f"        {line(r, tok)[0]}")
    print("③ 今天版位")
    pl = g._get_all(acct + "/insights", {"fields": "spend,impressions,inline_link_clicks,actions", "level": "account",
                                         "breakdowns": "publisher_platform,platform_position", "time_range": tr(TODAY, TODAY), "limit": "200"})
    tot = sum(f(x, "spend") for x in pl) or 1
    for r in sorted(pl, key=lambda x: -f(x, "spend")):
        if f(r, "spend") < 1:
            continue
        print(f"   {r['publisher_platform']}/{r['platform_position']:<28} {f(r, 'spend') / tot * 100:3.0f}% · {line(r, tok)[0]}")
    print("④ 今天每小时（MYT）花费 / 报名")
    hr = defaultdict(lambda: [0.0, 0.0])
    for r in g._get_all(acct + "/insights", {"fields": "spend,actions", "level": "account", "time_range": tr(TODAY, TODAY),
                                             "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone", "limit": "100"}):
        h = r["hourly_stats_aggregated_by_advertiser_time_zone"][:2]
        hr[h][0] += f(r, "spend"); hr[h][1] += extract_results(r.get("actions"), tok)
    print("   " + " · ".join(f"{h}时 RM{v[0]:.0f}/{v[1]:.0f}" for h, v in sorted(hr.items())))
print("\nCPL NOW 1119 DONE (read-only)")
