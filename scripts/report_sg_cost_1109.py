# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/9「新加坡的有点贵，要怎么调整」): SG per ad × day since Thursday 11/5 — spend, impressions, CPM,
link clicks, CTR, landing-page views, Webinarkit registrations, CPL, reg/LPV — plus live vs already-paused split and
10/16→11/4 baseline per ad (same metrics) to see whether cost comes from CPM (auction) or from conversion."""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
THU = _week_start_thursday(TODAY)
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
acct, tok = s.meta.account_path, "offsite_conversion.custom.1614065190214320"
F = "ad_id,ad_name,campaign_name,adset_name,spend,impressions,inline_link_clicks,actions"
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
ads = {a["id"]: a for a in g._get_all(acct + "/ads", {"fields": "effective_status", "limit": "2000"})}


def m(r):
    sp, im, lc = float(r.get("spend") or 0), int(r.get("impressions") or 0), int(r.get("inline_link_clicks") or 0)
    lpv, rg = extract_results(r.get("actions"), "landing_page_view"), extract_results(r.get("actions"), tok)
    return sp, im, lc, lpv, rg


def fmt(sp, im, lc, lpv, rg):
    return (f"RM{sp:>6.0f} · CPM {sp / im * 1000 if im else 0:>4.0f} · CTR {lc / im * 100 if im else 0:.2f}% · LPV {lpv:>3.0f} · "
            f"报名 {rg:>2.0f} · CPL {(sp / rg) if rg else float('inf'):>5.0f} · 报名/LPV {(rg / lpv * 100) if lpv else 0:>3.0f}%")


rows = g._get_all(acct + "/insights", {"fields": F, "level": "ad", "limit": "1000", "time_range": tr(THU, TODAY), "time_increment": "1"})
per_ad = defaultdict(list)
for r in rows:
    if float(r.get("spend") or 0) > 0:
        per_ad[r["ad_id"]].append(r)
tot = {"live": [0.0] * 5, "off": [0.0] * 5}
print(f"SG · {THU}→{TODAY} 每支 ad 每天（今天未完）")
for aid, rs in sorted(per_ad.items(), key=lambda kv: kv[1][0]["campaign_name"]):
    st = ads.get(aid, {}).get("effective_status", "?")
    r0 = rs[0]
    print(f"\n{'🟢' if st == 'ACTIVE' else '🔴'} {r0['campaign_name']} › {r0['adset_name']} · {r0['ad_name']} · ad {aid} · {st}")
    agg = [0.0] * 5
    for r in sorted(rs, key=lambda x: x["date_start"]):
        v = m(r)
        agg = [a + b for a, b in zip(agg, v)]
        print(f"   {r['date_start'][5:]} {fmt(*v)}")
    print(f"   周四起 {fmt(*agg)}")
    k = "live" if st == "ACTIVE" else "off"
    tot[k] = [a + b for a, b in zip(tot[k], agg)]
print(f"\n在跑合计   {fmt(*tot['live'])}\n已关合计   {fmt(*tot['off'])}")

base = g._get_all(acct + "/insights", {"fields": F, "level": "ad", "limit": "1000", "time_range": tr(dt.date(2026, 10, 16), dt.date(2026, 11, 4))})
print("\n10/16→11/4 基准（花 ≥RM50 的 Webinarkit ad）:")
for r in sorted(base, key=lambda x: -float(x.get("spend") or 0)):
    if float(r.get("spend") or 0) >= 50 and "Webinarkit" in r["campaign_name"]:
        print(f"   {r['campaign_name'][13:60]} › {r['adset_name'][:18]} · {r['ad_name'][:22]} · ad {r['ad_id']}\n      {fmt(*m(r))}")
acc = g._get_all(acct + "/insights", {"fields": "spend,impressions,inline_link_clicks,actions", "limit": "50", "time_range": tr(dt.date(2026, 10, 16), TODAY), "time_increment": "1"})
print("\n账户每天:")
for r in acc:
    print(f"   {r['date_start'][5:]} {fmt(*m(r))}")
print("SG COST DONE (read-only)")
