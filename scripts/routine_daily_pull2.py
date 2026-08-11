# -*- coding: utf-8 -*-
"""Daily routine pull, part 2 (READ-ONLY).

Two follow-ups the main pull leaves open:

  1. **Sales histogram, last 21 days** — the ad-level pull reports "0 sales yesterday"
     from the Paid Student List, which is indistinguishable from "the sheet hasn't been
     filled in yet". Printing the per-day counts plus the sheet's newest sale date tells
     the two apart.
  2. **Campaign-level daily budgets + yesterday-only spend** — every ad set is CBO, so
     the budget lives on the campaign, not the ad set (the main pull could only report
     "CBO/campaign级"). Needed to verify the MY TRAVEL cut to RM70/day landed and to see
     each campaign's actual yesterday burn against it.
"""
from __future__ import annotations

import datetime as dt
import time
from collections import Counter

from adbot import cpa
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

ACCTS = (("MY", "config.yaml"), ("SG", "config.sg.yaml"))
PACE = 1.0


def main() -> None:
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    yday = today - dt.timedelta(days=1)
    base = load_settings(REPO_ROOT / "config" / "config.yaml")

    from adbot.clients.sheets import SheetsClient
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    print(f"══════ 成交日历 · 最近 21 天 (today MYT={today}) ══════")
    cnt = Counter(s.date for s in sales if s.date)
    dated = [s.date for s in sales if s.date]
    print(f"  sheet 总行数={len(sales)} · 有日期={len(dated)} · 最新一单日期={max(dated) if dated else '—'}")
    for i in range(20, -1, -1):
        d = today - dt.timedelta(days=i)
        n = cnt.get(d, 0)
        amt = sum(s.amount for s in sales if s.date == d)
        bar = "█" * n
        print(f"  {d} {d.strftime('%a')} · {n:>2} 单 · RM{amt:>7.0f} {bar}")

    print(f"\n══════ 昨天 ({yday}) 每单明细 ══════")
    rows = [s for s in sales if s.date == yday]
    if not rows:
        print("  (无)")
    for s in rows:
        print(f"  RM{s.amount:.0f} · [{s.campaign[:56]}] · «{s.ad[:44]}»")

    for label, cfg in ACCTS:
        print(f"\n════════ [{label}] campaign 预算 vs 昨天花费 ════════")
        try:
            s = load_settings(REPO_ROOT / "config" / cfg)
            g = graph_client(s)
            acct = s.meta.account_path
            token = result_action_type(s.meta.conversion_event)

            camps = g._get_all(f"{acct}/campaigns", {
                "fields": "id,name,effective_status,daily_budget,lifetime_budget",
                "limit": "200"})
            time.sleep(PACE)
            ins = g.account_insights(
                acct, level="campaign", fields="campaign_id,spend,actions",
                time_range={"since": str(yday), "until": str(yday)})
            by_id = {r.get("campaign_id"): r for r in ins}

            for c in sorted(camps, key=lambda x: x.get("name", "")):
                if c.get("effective_status") != "ACTIVE":
                    continue
                db = c.get("daily_budget")
                bud = f"RM{float(db) / 100:.0f}/day" if db else (
                    f"lifetime RM{float(c['lifetime_budget']) / 100:.0f}"
                    if c.get("lifetime_budget") else "—")
                r = by_id.get(c["id"])
                sp = float((r or {}).get("spend") or 0)
                rg = extract_results((r or {}).get("actions"), token)
                cpl = f"RM{sp / rg:.1f}" if rg else ("∞" if sp else "-")
                print(f"  {c.get('name','?')[:44]:44} | 预算 {bud:>16} | "
                      f"昨天 RM{sp:>6.0f} · {int(rg):>2} reg · CPL {cpl}")
        except Exception as exc:  # noqa: BLE001
            print(f"  !! [{label}] 失败: {exc}")

    print("\nPART 2 DONE (read-only)")


if __name__ == "__main__":
    main()
