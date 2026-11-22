# -*- coding: utf-8 -*-
"""READ-ONLY (owner 2026-11-22「有沒有要建議我的？」). The RM5,950 spend cap is projected to pause every campaign around
Tue 11/24 night until Wed 15:00 — i.e. the whole Wednesday morning before the live. This checks, from REAL Meta hourly account
insights, how Wednesday 00:00–15:00 MYT performed in the last three cycles vs the rest of the same cycle (Thu–Tue), and how
the Tue 18:00–24:00 slot did, so the advice is backed by numbers, not memory.
Windows: cycles 10/29–11/04, 11/05–11/11, 11/12–11/18 (each ends on the live Wednesday). Registrations = Meta pixel
CompleteRegistration (same token the monitor uses). Register-table S1 bots: 40 on 11/13 + 1 on 11/11 (CLAUDE.md) — 11/13 is
in the Thu–Tue slice of 11/12–11/18 and is subtracted there; the 11/11 one is shown as a note. No personal data printed."""
import datetime as dt
import json
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
CYCLES = [(dt.date(2026, 10, 29), dt.date(2026, 11, 4)), (dt.date(2026, 11, 5), dt.date(2026, 11, 11)),
          (dt.date(2026, 11, 12), dt.date(2026, 11, 18))]
ACCTS = (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
BOTS = {dt.date(2026, 11, 13): 40}   # Register S1 bots (both accounts together; CLAUDE.md 11/18 audit)

print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读 · Meta 每小时账户数据（广告账户时区 = MYT）")
tot = defaultdict(lambda: [0.0, 0.0])
for c0, c1 in CYCLES:
    slots = defaultdict(lambda: [0.0, 0.0])
    for lab, cfg, cc in ACCTS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        tok = f"offsite_conversion.custom.{cc}"
        rows = g._get_all(s.meta.account_path + "/insights", {
            "fields": "spend,actions", "level": "account", "time_increment": "1",
            "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone", "limit": "500",
            "time_range": json.dumps({"since": c0.isoformat(), "until": c1.isoformat()})})
        for r in rows:
            d = dt.date.fromisoformat(r["date_start"])
            h = int(r["hourly_stats_aggregated_by_advertiser_time_zone"][:2])
            sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), tok)
            if d == c1 and h < 15:
                k = "周三 00–15"
            elif d == c1:
                continue                                     # live afternoon — owner closes by hand
            elif d == c1 - dt.timedelta(days=1) and h >= 18:
                k = "周二 18–24"
            elif d >= c1 - dt.timedelta(days=2):
                k = "周一–周二 18 点前"
            else:
                k = "周四–周日"
            for kk in (k, f"{lab} {k}"):
                slots[kk][0] += sp
                slots[kk][1] += rg
    bots = sum(n for d, n in BOTS.items() if c0 <= d <= c1)
    slots["周四–周日"][1] -= bots
    print(f"\n### 周期 {c0:%m/%d}–{c1:%m/%d}（直播 {c1:%m/%d} 周三）" + (f" · 周四–周日已扣机器人 {bots}" if bots else ""))
    for k in ("周四–周日", "周一–周二 18 点前", "周二 18–24", "周三 00–15"):
        sp, rg = slots[k]
        my, sg = slots[f"MY {k}"], slots[f"SG {k}"]
        print(f"   {k:<12} RM{sp:>6,.0f} / {rg:>4.0f} 报名 · CPL {sp / rg if rg else float('nan'):>5.0f}"
              f"   (MY RM{my[0]:,.0f}/{my[1]:.0f} · SG RM{sg[0]:,.0f}/{sg[1]:.0f})")
        tot[k][0] += sp
        tot[k][1] += rg
print("\n### 三期合计")
for k in ("周四–周日", "周一–周二 18 点前", "周二 18–24", "周三 00–15"):
    sp, rg = tot[k]
    print(f"   {k:<12} RM{sp:>6,.0f} / {rg:>4.0f} 报名 · CPL {sp / rg if rg else float('nan'):>5.0f}")
print("\n注：11/11 另有 1 笔机器人（日期在周三，时段未知，未扣）。11/18 周三 owner 11:21 已手动全关，所以那天只有约 11 小时。")
print("WED MORNING DONE (read-only)")
