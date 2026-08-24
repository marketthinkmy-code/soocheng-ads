# -*- coding: utf-8 -*-
"""READ-ONLY: full MY+SG delivery inventory after the owner activated the new
keyword campaigns (2026-08-24).

Per account, every ACTIVE campaign with:
  · its real daily budget (CBO campaign budget, or the sum of its ACTIVE ad
    sets' budgets for ABO),
  · how many ad sets / ads inside are actually live (effective_status ACTIVE),
    flagging the classic trap: campaign switched on but children still PAUSED,
  · yesterday + today spend & leads.
Then the account's total daily budget and the MY+SG grand total. Also lists
recently-touched campaigns that remain PAUSED (so the owner sees what wasn't
activated)."""
from __future__ import annotations

import datetime as dt
import time

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

NOW_MYT = dt.datetime.utcnow() + dt.timedelta(hours=8)
TODAY = NOW_MYT.date()
YEST = TODAY - dt.timedelta(days=1)

WATCH = ("BROKERS", "RETIREMENT", "PRIORITY", "COUNTRY CLUB", "AUG NEW",
         "LAL", "MJ", "DAY TRADING", "INVESTMENT", "TRAVEL", "GOLF",
         "RUNNING", "BROAD", "用我的方法", "1-1-3", "1-1-1", "1-5-3")


def main() -> None:
    print(f"预算/交付盘点 — MYT {NOW_MYT:%Y-%m-%d %H:%M}（read-only）\n")
    grand = 0.0
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        token = result_action_type(s.meta.conversion_event)
        print(f"═══ [{label}] {acct} ═══")

        camps = g._get_all(
            f"{acct}/campaigns",
            {"fields": "id,name,status,effective_status,daily_budget,lifetime_budget",
             "limit": "500"})
        time.sleep(1.2)
        asets = g._get_all(
            f"{acct}/adsets",
            {"fields": "id,name,status,effective_status,daily_budget,"
                       "lifetime_budget,campaign_id", "limit": "500"})
        time.sleep(1.2)
        ads = g._get_all(
            f"{acct}/ads",
            {"fields": "id,status,effective_status,campaign_id", "limit": "500"})
        time.sleep(1.2)

        spend = {}  # campaign_id -> {day: (spend, leads)}
        for day in (YEST, TODAY):
            iso = day.isoformat()
            try:
                for r in g.account_insights(
                        acct, level="campaign",
                        fields="campaign_id,campaign_name,spend,actions",
                        time_range={"since": iso, "until": iso}):
                    spend.setdefault(r.get("campaign_id"), {})[day] = (
                        float(r.get("spend") or 0),
                        extract_results(r.get("actions"), token))
            except Exception as e:
                print(f"  ⚠️ insights {iso}: {str(e)[:80]}")
            time.sleep(1.2)

        by_c_asets = {}
        for a in asets:
            by_c_asets.setdefault(a.get("campaign_id"), []).append(a)
        by_c_ads = {}
        for a in ads:
            by_c_ads.setdefault(a.get("campaign_id"), []).append(a)

        total = 0.0
        actives = [c for c in camps if c.get("effective_status") == "ACTIVE"]
        actives.sort(key=lambda c: c.get("name") or "")
        for c in actives:
            cid = c["id"]
            ca = by_c_asets.get(cid, [])
            cads = by_c_ads.get(cid, [])
            live_asets = [a for a in ca if a.get("effective_status") == "ACTIVE"]
            live_ads = [a for a in cads if a.get("effective_status") == "ACTIVE"]
            if c.get("daily_budget"):
                bud = int(c["daily_budget"]) / 100
                btype = "CBO"
            else:
                bud = sum(int(a.get("daily_budget") or 0) / 100 for a in live_asets)
                btype = "ABO"
            total += bud
            ysp, yld = spend.get(cid, {}).get(YEST, (0.0, 0.0))
            tsp, tld = spend.get(cid, {}).get(TODAY, (0.0, 0.0))
            flags = []
            if not live_ads:
                flags.append("⚠️不会花钱:0支ACTIVE广告")
            elif not live_asets:
                flags.append("⚠️adset全PAUSED")
            if c.get("lifetime_budget") and not c.get("daily_budget"):
                flags.append(f"lifetime预算{int(c['lifetime_budget'])/100:.0f}")
            print(f"  RM{bud:6.0f}/day {btype}  昨RM{ysp:5.0f}·{yld:2.0f}名单"
                  f"  今RM{tsp:5.0f}·{tld:2.0f}名单"
                  f"  adset {len(live_asets)}/{len(ca)} ad {len(live_ads)}/{len(cads)}"
                  f"  «{(c.get('name') or '')[:44]}»"
                  f"{('  ' + ' '.join(flags)) if flags else ''}")
        print(f"  ── [{label}] ACTIVE campaign ×{len(actives)} · 日预算合计 RM{total:,.0f}")
        grand += total

        paused_watch = [c for c in camps
                        if c.get("effective_status") != "ACTIVE"
                        and any(w in (c.get("name") or "") for w in WATCH)]
        if paused_watch:
            print(f"  ── 关注名单里仍 PAUSED/关闭 ×{len(paused_watch)}:")
            for c in paused_watch:
                st = c.get("effective_status")
                print(f"     [{st}] «{(c.get('name') or '')[:52]}»")
        print()

    print(f"★ MY+SG 合计日预算 RM{grand:,.0f}/day")
    print("INVENTORY DONE (read-only)")


if __name__ == "__main__":
    main()
