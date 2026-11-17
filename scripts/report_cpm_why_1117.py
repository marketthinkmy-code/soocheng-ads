# -*- coding: utf-8 -*-
"""READ-ONLY (owner 2026-11-17「为什么变贵了？」). Why CPM rose / CTR fell on 11/16–11/17:
1) account daily since 10/16: CPM · CTR · daily frequency (market / weekly pattern?);
2) every ad that spent since Thu: lifetime-since-10/16 reach & frequency, Thu-week frequency, daily CPM/CTR/freq 11/13→today;
3) placement mix per day 11/13→today (spend share, CPM, CTR) — did delivery shift?;
4) ad quality / engagement / conversion rankings (Thu-week) and ad set learning stage."""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import _week_start_thursday, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
THU = _week_start_thursday(TODAY)
D1 = THU + dt.timedelta(days=1)
ACCTS = (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
f = lambda r, k: float(r.get(k) or 0)

for label, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {label}")
    print("① 账户每天 CPM · CTR · 当天频次 · 报名（10/16 起）")
    for r in g._get_all(acct + "/insights", {"fields": "spend,impressions,reach,inline_link_clicks,actions", "level": "account",
                                             "time_range": tr(dt.date(2026, 10, 16), TODAY), "time_increment": "1", "limit": "100"}):
        d = dt.date.fromisoformat(r["date_start"]); im = f(r, "impressions")
        print(f"   {d:%m-%d %a} RM{f(r, 'spend'):5.0f} CPM {f(r, 'spend') / im * 1000 if im else 0:4.0f} CTR {f(r, 'inline_link_clicks') / im * 100 if im else 0:4.2f}% "
              f"freq {im / f(r, 'reach') if f(r, 'reach') else 0:4.2f} 报名 {extract_results(r.get('actions'), tok):3.0f}" + (" ←周四" if d.weekday() == 3 else ""))
    wk = {r["ad_id"]: r for r in g._get_all(acct + "/insights", {"fields": "ad_id,ad_name,adset_id,adset_name,campaign_name,spend,impressions,reach,frequency,quality_ranking,engagement_rate_ranking,conversion_rate_ranking",
                                                                    "level": "ad", "time_range": tr(THU, TODAY), "limit": "500"})}
    life = {r["ad_id"]: r for r in g._get_all(acct + "/insights", {"fields": "ad_id,spend,impressions,reach,frequency", "level": "ad",
                                                                      "time_range": tr(dt.date(2026, 10, 16), TODAY), "limit": "500"})}
    daily = defaultdict(dict)
    for r in g._get_all(acct + "/insights", {"fields": "ad_id,spend,impressions,reach,inline_link_clicks", "level": "ad",
                                             "time_range": tr(D1, TODAY), "time_increment": "1", "limit": "500"}):
        daily[r["ad_id"]][r["date_start"]] = r
    st = {a["id"]: a for a in g._get_all(acct + "/ads", {"fields": "effective_status,created_time", "limit": "500"})}
    print("\n② 每支 ad（周四起花 ≥RM60）：10/16 起触达/频次 · 周四起频次 · 排名(质量/互动/转化) · 每天 CPM/CTR/当天频次")
    seen = set()
    for aid, r in sorted(wk.items(), key=lambda kv: -f(kv[1], "spend")):
        if f(r, "spend") < 60:
            continue
        L = life.get(aid, {}); es = st.get(aid, {}).get("effective_status", "?")
        print(f"   [{'在跑' if es == 'ACTIVE' else es}] {r['campaign_name'].replace('(Webinarkit) ', '')} › {r['adset_name']} · {r['ad_name']} · ad {aid} · 建于 {st.get(aid, {}).get('created_time', '?')[:10]}")
        print(f"        10/16起 触达 {f(L, 'reach'):.0f} 频次 {f(L, 'frequency'):.2f} · 周四起 触达 {f(r, 'reach'):.0f} 频次 {f(r, 'frequency'):.2f} · "
              f"排名 {r.get('quality_ranking', '-')}/{r.get('engagement_rate_ranking', '-')}/{r.get('conversion_rate_ranking', '-')}")
        line = "       "
        for i in range((TODAY - D1).days + 1):
            d = (D1 + dt.timedelta(days=i)).isoformat(); x = daily[aid].get(d)
            if not x:
                line += f" {d[5:]} — |"; continue
            im = f(x, "impressions")
            line += f" {d[5:]} CPM {f(x, 'spend') / im * 1000 if im else 0:.0f} CTR {f(x, 'inline_link_clicks') / im * 100 if im else 0:.1f}% fq {im / f(x, 'reach') if f(x, 'reach') else 0:.2f} |"
        print(line)
        seen.add(r["adset_id"])
    print("\n③ 版位每天（花费占比 · CPM · CTR）")
    pl = defaultdict(dict)
    for r in g._get_all(acct + "/insights", {"fields": "spend,impressions,inline_link_clicks", "level": "account", "breakdowns": "publisher_platform,platform_position",
                                             "time_range": tr(D1, TODAY), "time_increment": "1", "limit": "500"}):
        pl[r["date_start"]][f"{r['publisher_platform']}/{r['platform_position']}"] = r
    for d in sorted(pl):
        tot = sum(f(x, "spend") for x in pl[d].values()) or 1
        top = sorted(pl[d].items(), key=lambda kv: -f(kv[1], "spend"))[:5]
        print(f"   {d[5:]} " + " · ".join(f"{k} {f(x, 'spend') / tot * 100:.0f}% CPM {f(x, 'spend') / f(x, 'impressions') * 1000 if f(x, 'impressions') else 0:.0f} CTR {f(x, 'inline_link_clicks') / f(x, 'impressions') * 100 if f(x, 'impressions') else 0:.1f}%" for k, x in top))
    print("\n④ 在跑 ad set 学习期")
    for a in g._get_all(acct + "/adsets", {"fields": "name,effective_status,learning_stage_info,campaign{name}", "limit": "200"}):
        if a.get("effective_status") == "ACTIVE":
            print(f"   {a['campaign']['name'].replace('(Webinarkit) ', '')} › {a['name']} · {json.dumps(a.get('learning_stage_info', {}), ensure_ascii=False)[:200]}")
print("\nCPM WHY 1117 DONE (read-only)")
