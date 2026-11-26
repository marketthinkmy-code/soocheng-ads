# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/26「SG 为什么这么贵？」).
① Funnel, this cycle (11/26 00:00 MYT → last complete hour) — MY vs SG:
   spend · impressions · CPM · link clicks · CTR · CPC · LPV · LPV/click · cost per LPV · 报名 · LPV→报名 · CPL.
② Same funnel for SG (and MY) on earlier cycle Thursdays, SAME hours only (00:00 → same hour) — background reference.
③ SG this cycle by placement (publisher_platform / platform_position).
④ SG this cycle by campaign.
⑤ SG this cycle by age."""
import datetime as dt
import json
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
TODAY = NOW.date()
HMAX = NOW.hour            # complete hours only: 00 .. HMAX-1
PAST = [dt.date(2026, 10, 29), dt.date(2026, 11, 5), dt.date(2026, 11, 12), dt.date(2026, 11, 19)]
ACCTS = (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
f = lambda r, k: float(r.get(k) or 0)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
FIELDS = "spend,impressions,inline_link_clicks,actions"


def acc(rows, tok, keyf=lambda r: "all"):
    t = defaultdict(lambda: [0.0] * 5)   # spend, impr, clicks, lpv, reg
    for r in rows:
        k = keyf(r)
        if k is None:
            continue
        v = t[k]
        v[0] += f(r, "spend"); v[1] += f(r, "impressions"); v[2] += f(r, "inline_link_clicks")
        v[3] += extract_results(r.get("actions"), "landing_page_view"); v[4] += extract_results(r.get("actions"), tok)
    return t


def line(v):
    sp, im, cl, lpv, rg = v
    d = lambda a, b, m=1.0: a / b * m if b else 0
    return (f"RM{sp:5.0f} · 曝光 {im:6.0f} · CPM RM{d(sp, im, 1000):4.0f} · 点击 {cl:4.0f} · CTR {d(cl, im, 100):4.2f}% · 每点击 RM{d(sp, cl):5.2f}"
            f" · LPV {lpv:3.0f}（点击→LPV {d(lpv, cl, 100):3.0f}%）· 每LPV RM{d(sp, lpv):5.2f} · 报名 {rg:2.0f} · LPV→报名 {d(rg, lpv, 100):4.1f}%"
            f" · CPL {('RM%.0f' % d(sp, rg)) if rg else '—'}")


hour_ok = lambda r: int(r["hourly_stats_aggregated_by_advertiser_time_zone"][:2]) < HMAX
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读 · 这一期 = 11/26 00:00 → {HMAX:02d}:00（整点）")
for lab, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {lab}")
    print(f"① / ② 周四 00:00 → {HMAX:02d}:00（同样的钟点）：")
    for day in [TODAY] + PAST[::-1]:
        rows = g._get_all(acct + "/insights", {"fields": FIELDS, "level": "account", "limit": "100", "time_range": tr(day, day),
                                               "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone"})
        t = acc(rows, tok, lambda r: "all" if hour_ok(r) else None)
        tag = "这一期" if day == TODAY else "参考  "
        print(f"   {tag} {day:%m/%d}: {line(t['all'])}")
    if lab != "SG":
        continue
    print("③ 这一期版位（整天到现在）：")
    rows = g._get_all(acct + "/insights", {"fields": FIELDS, "level": "account", "limit": "200", "time_range": tr(TODAY, TODAY),
                                           "breakdowns": "publisher_platform,platform_position"})
    t = acc(rows, tok, lambda r: f"{r['publisher_platform']}/{r['platform_position']}")
    tot = sum(v[0] for v in t.values()) or 1
    for k, v in sorted(t.items(), key=lambda kv: -kv[1][0]):
        if v[0] >= 1:
            print(f"   {k:<34} {v[0] / tot * 100:3.0f}% · {line(v)}")
    print("④ 这一期 campaign：")
    rows = g._get_all(acct + "/insights", {"fields": FIELDS + ",campaign_name,campaign_id", "level": "campaign", "limit": "200",
                                           "time_range": tr(TODAY, TODAY)})
    t = acc(rows, tok, lambda r: f"{r['campaign_name']} · {r['campaign_id']}")
    for k, v in sorted(t.items(), key=lambda kv: -kv[1][0]):
        print(f"   {k}\n      {line(v)}")
    print("⑤ 这一期年龄：")
    rows = g._get_all(acct + "/insights", {"fields": FIELDS, "level": "account", "limit": "50", "time_range": tr(TODAY, TODAY),
                                           "breakdowns": "age"})
    t = acc(rows, tok, lambda r: r["age"])
    for k, v in sorted(t.items()):
        print(f"   {k:<6} {line(v)}")
print("\nSG WHY 1126 DONE (read-only)")
