# -*- coding: utf-8 -*-
"""READ-ONLY (owner 2026-11-17「这两天 cpl 很高。然后有些星期四到现在的广告，cpl 便宜的被关了」).
1) Per account per day 11/05 → today: spend · CPM · link CTR · LPV · 报名 · CPL · LPV→报名 % (where the funnel broke).
2) Per ad with Thu-week spend: Thu-week spend / 报名 / CPL, then 11/14 · 11/15 · 11/16 · 11/17 (spend / 报名 / CTR / LPV),
   status — live ads and ads closed since Thursday, so cheap-CPL closures are visible with their own daily trend."""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
THU = _week_start_thursday(TODAY)
D0 = dt.date(2026, 11, 5)
DAYS = [THU + dt.timedelta(days=i) for i in range(2, (TODAY - THU).days + 1)]
ACCTS = (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
F = "ad_id,ad_name,adset_name,campaign_name,spend,impressions,inline_link_clicks,actions"


def ins(g, acct, level, since, until, daily):
    p = {"fields": F if level == "ad" else "spend,impressions,inline_link_clicks,actions", "level": level, "limit": "500",
         "time_range": json.dumps({"since": since.isoformat(), "until": until.isoformat()})}
    if daily:
        p["time_increment"] = "1"
    return g._get_all(acct + "/insights", p)


def m(r, tok):
    sp, im, lc = float(r.get("spend") or 0), float(r.get("impressions") or 0), float(r.get("inline_link_clicks") or 0)
    lpv = extract_results(r.get("actions"), "landing_page_view")
    rg = extract_results(r.get("actions"), tok)
    return sp, im, lc, lpv, rg


for label, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {label} · 每天（CPM · 链接 CTR · LPV · 报名 · CPL · LPV→报名）")
    for r in ins(g, acct, "account", D0, TODAY, True):
        sp, im, lc, lpv, rg = m(r, tok)
        d = dt.date.fromisoformat(r["date_start"])
        print(f"   {d:%m-%d %a} RM{sp:6.0f} · CPM {sp / im * 1000 if im else 0:5.0f} · CTR {lc / im * 100 if im else 0:4.2f}% · "
              f"LPV {lpv:4.0f} · 报名 {rg:3.0f} · CPL {sp / rg if rg else 0:5.0f} · LPV→报名 {rg / lpv * 100 if lpv else 0:4.1f}%"
              + ("  ← 周四" if d.weekday() == 3 else ""))
    wk = {r["ad_id"]: r for r in ins(g, acct, "ad", THU, TODAY, False)}
    daily = defaultdict(dict)
    for r in ins(g, acct, "ad", DAYS[0], TODAY, True):
        daily[r["ad_id"]][r["date_start"]] = r
    st = {a["id"]: a for a in g._get_all(acct + "/ads", {"fields": "effective_status", "limit": "500"})}
    print(f"\n   每支 ad：周四起 → " + " · ".join(f"{d:%m/%d}" for d in DAYS) + "（花费/报名 CTR LPV）")
    for aid, r in sorted(wk.items(), key=lambda kv: -float(kv[1].get("spend") or 0)):
        sp, im, lc, lpv, rg = m(r, tok)
        if sp < 30:
            continue
        es = st.get(aid, {}).get("effective_status", "?")
        line = f"   [{'在跑' if es == 'ACTIVE' else es}] {r['campaign_name'].replace('(Webinarkit) ', '')} › {r['adset_name']} · {r['ad_name']} · ad {aid}\n" \
               f"        周四起 RM{sp:.0f}/{rg:.0f} CPL {sp / rg if rg else 0:.0f} ‖"
        for d in DAYS:
            x = daily[aid].get(d.isoformat())
            if not x:
                line += f" {d:%m/%d} —  |"
                continue
            a, b, c, e, f_ = m(x, tok)
            line += f" {d:%m/%d} {a:.0f}/{f_:.0f} {c / b * 100 if b else 0:.1f}% {e:.0f} |"
        print(line)
print("\nCPL SPIKE 1117 DONE (read-only)")
