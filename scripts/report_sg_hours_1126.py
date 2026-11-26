# -*- coding: utf-8 -*-
"""READ-ONLY follow-up to report_sg_levers_1126.py: does the SG hour-of-day CPL gap hold up?
Per account (MY, SG), MYT hour blocks: 00–12 vs 12–24 and 3-hour blocks, for
  (a) each sub-range separately (10/29–11/12, 11/14–11/25; 11/13 bot day out),
  (b) action_report_time=impression vs =conversion (when registrations are counted),
  (c) this cycle (11/26 00:00 → last complete hour)."""
import datetime as dt
import json
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
RANGES = [(dt.date(2026, 10, 29), dt.date(2026, 11, 12)), (dt.date(2026, 11, 14), dt.date(2026, 11, 25))]
f = lambda r, k: float(r.get(k) or 0)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
HK = "hourly_stats_aggregated_by_advertiser_time_zone"


def hours(g, acct, tok, a, b, art="impression", hmax=24):
    t = defaultdict(lambda: [0.0, 0.0, 0.0])
    for r in g._get_all(acct + "/insights", {"fields": "spend,actions", "level": "account", "limit": "100", "breakdowns": HK,
                                             "time_range": tr(a, b), "action_report_time": art}):
        h = int(r[HK][:2])
        if h >= hmax:
            continue
        t[h][0] += f(r, "spend"); t[h][1] += extract_results(r.get("actions"), "landing_page_view")
        t[h][2] += extract_results(r.get("actions"), tok)
    return t


def blk(t, lo, hi):
    sp, lpv, rg = (sum(v[i] for h, v in t.items() if lo <= h < hi) for i in range(3))
    return f"RM{sp:5.0f} / LPV {lpv:4.0f} / 报名 {rg:3.0f} · CPL {('RM%.0f' % (sp / rg)) if rg else '—':>6}"


print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读")
for lab, cfg, cc in (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {lab}")
    for a, b in RANGES:
        for art in ("impression", "conversion"):
            t = hours(g, acct, tok, a, b, art)
            print(f"   {a:%m/%d}–{b:%m/%d} 报名按{'曝光' if art == 'impression' else '报名'}时间：00–12 时 {blk(t, 0, 12)}  ||  12–24 时 {blk(t, 12, 24)}")
    t = defaultdict(lambda: [0.0, 0.0, 0.0])
    for a, b in RANGES:
        for h, v in hours(g, acct, tok, a, b).items():
            for i in range(3):
                t[h][i] += v[i]
    print("   两段合计，三小时一组（按曝光时间）：")
    for lo in range(0, 24, 3):
        print(f"     {lo:02d}–{lo + 3:02d} 时 {blk(t, lo, lo + 3)}")
    tc = hours(g, acct, tok, NOW.date(), NOW.date(), hmax=NOW.hour)
    print(f"   这一期 11/26 00:00 → {NOW.hour:02d}:00：00–12 时 {blk(tc, 0, 12)}  ||  12 时起 {blk(tc, 12, 24)}")
print("\nSG HOURS 1126 DONE (read-only)")
