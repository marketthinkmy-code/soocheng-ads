# -*- coding: utf-8 -*-
"""READ-ONLY follow-up to report_cpl_why_1120.py (owner 11/20「查一下这一期 CPL 为什么到 121」).
① Per cycle (Thu + Fri; this cycle Fri so far), by platform: LPV · 报名 · spend — LPV→报名 and cost per LPV WITHOUT Audience Network
   (AN landing-page visits have never converted: 10/29 起 28 报名 0 买家, and 11/19 MY AN 37 LPV → 0 报名).
② 11/20 by placement (both accounts) — is AN really gone from MY, where did the money go.
③ 11/20 hourly per account (MYT): spend · LPV · 报名 — before vs after the owner's ~10:20 reopen.
④ 11/20 spend split: ads delivering already on 11/19 vs ads that started delivering on 11/20."""
import datetime as dt
import json
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
CYC = [dt.date(2026, 10, 29), dt.date(2026, 11, 5), dt.date(2026, 11, 19)]   # 11/12 left out: 40 bots on 11/13
ACCTS = (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
f = lambda r, k: float(r.get(k) or 0)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
D19, D20 = dt.date(2026, 11, 19), dt.date(2026, 11, 20)
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读（11/12 那期有 40 个机器人，不拿来比）")
for lab, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {lab}")
    print("① 周四+周五（这一期周五到现在），拿掉 Audience Network 之后：")
    for st in CYC:
        t = defaultdict(lambda: [0.0, 0.0, 0.0])
        for r in g._get_all(acct + "/insights", {"fields": "spend,actions", "level": "account", "breakdowns": "publisher_platform",
                                                "limit": "50", "time_range": tr(st, st + dt.timedelta(days=1))}):
            p = r["publisher_platform"]
            t[p][0] += f(r, "spend"); t[p][1] += extract_results(r.get("actions"), "landing_page_view")
            t[p][2] += extract_results(r.get("actions"), tok)
        an = t.get("audience_network", [0, 0, 0])
        sp = sum(v[0] for k, v in t.items() if k != "audience_network")
        lpv = sum(v[1] for k, v in t.items() if k != "audience_network")
        rg = sum(v[2] for k, v in t.items() if k != "audience_network")
        print(f"   {st:%m/%d} 起: 无 AN RM{sp:5.0f} · LPV {lpv:4.0f} · 每LPV RM{sp / lpv if lpv else 0:5.2f} · LPV→报名 {rg / lpv * 100 if lpv else 0:4.1f}% · 报名 {rg:3.0f}"
              f" · CPL {sp / rg if rg else 0:4.0f}  ||  AN RM{an[0]:4.0f} · LPV {an[1]:3.0f} · 报名 {an[2]:.0f}")
    print("② 11/20 版位：")
    pl = g._get_all(acct + "/insights", {"fields": "spend,impressions,inline_link_clicks,actions", "level": "account",
                                         "breakdowns": "publisher_platform,platform_position", "limit": "200", "time_range": tr(D20, D20)})
    tot = sum(f(x, "spend") for x in pl) or 1
    for r in sorted(pl, key=lambda x: -f(x, "spend"))[:8]:
        sp, im, cl = f(r, "spend"), f(r, "impressions"), f(r, "inline_link_clicks")
        lpv, rg = extract_results(r.get("actions"), "landing_page_view"), extract_results(r.get("actions"), tok)
        print(f"     {r['publisher_platform']}/{r['platform_position']:<26} {sp / tot * 100:3.0f}% · RM{sp:4.0f} · CTR {cl / im * 100 if im else 0:4.2f}%"
              f" · LPV {lpv:3.0f} · 报名 {rg:.0f}")
    print("③ 11/20 每小时（MYT）花费 / LPV / 报名：")
    hr = defaultdict(lambda: [0.0, 0.0, 0.0])
    for r in g._get_all(acct + "/insights", {"fields": "spend,actions", "level": "account", "limit": "100", "time_range": tr(D20, D20),
                                             "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone"}):
        h = r["hourly_stats_aggregated_by_advertiser_time_zone"][:2]
        hr[h][0] += f(r, "spend"); hr[h][1] += extract_results(r.get("actions"), "landing_page_view"); hr[h][2] += extract_results(r.get("actions"), tok)
    print("     " + " · ".join(f"{h}时 RM{v[0]:.0f}/{v[1]:.0f}/{v[2]:.0f}" for h, v in sorted(hr.items())))
    a = [v for h, v in hr.items() if int(h) < 10]; b = [v for h, v in hr.items() if int(h) >= 10]
    for name, part in (("00–10 时", a), ("10 时起", b)):
        sp, lpv, rg = (sum(x[i] for x in part) for i in range(3))
        print(f"     {name}: RM{sp:.0f} · LPV {lpv:.0f} · 每LPV RM{sp / lpv if lpv else 0:.2f} · 报名 {rg:.0f}")
    print("④ 11/20 花费：11/19 就在投放的 ad vs 11/20 才开始投放的 ad：")
    d19 = {r["ad_id"] for r in g._get_all(acct + "/insights", {"fields": "ad_id,spend", "level": "ad", "limit": "500", "time_range": tr(D19, D19)})
           if f(r, "spend") >= 1}
    grp = defaultdict(lambda: [0.0, 0.0, 0.0, 0])
    for r in g._get_all(acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "500", "time_range": tr(D20, D20)}):
        k = "11/19 已在投放" if r["ad_id"] in d19 else "11/20 才开始"
        grp[k][0] += f(r, "spend"); grp[k][1] += extract_results(r.get("actions"), "landing_page_view")
        grp[k][2] += extract_results(r.get("actions"), tok); grp[k][3] += 1
    for k, v in grp.items():
        print(f"     {k}: {v[3]} 支 · RM{v[0]:.0f} · LPV {v[1]:.0f} · 每LPV RM{v[0] / v[1] if v[1] else 0:.2f} · 报名 {v[2]:.0f}")
print("\nCPL WHY2 1120 DONE (read-only)")
