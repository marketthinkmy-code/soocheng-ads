# -*- coding: utf-8 -*-
"""READ-ONLY: first per-ad-set battle report for the 0905 new-structure wave.

For every campaign whose name contains «| 0905» in MY + SG: each ad set's
spend / leads / CPL since 2026-09-05, the ad's review state, and any
Paid-Student-List sales already attributed to a 0905 campaign via UTM."""
from __future__ import annotations

import collections
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import parse_metrics, result_action_type
from adbot.settings import REPO_ROOT, load_settings

SINCE = "2026-09-05"
UNTIL = "2026-09-09"          # 完整 4 天；今天周三 MY 全停，不读当日


def main() -> None:
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    try:
        values = SheetsClient(base.secrets.google_sa_json).read_tab(
            base.cpa.spreadsheet_id, base.cpa.sales_tab)
        sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)
        new_sales = [s for s in sales if "0905" in s.campaign]
    except Exception as e:
        print(f"⚠️ sheet 读取失败: {str(e)[:80]}")
        new_sales = []

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        token = result_action_type(s.meta.conversion_event)
        print(f"═══ [{label}] 0905 结构 · {SINCE} → {UNTIL} ═══")

        ads = g._get_all(
            f"{acct}/ads",
            {"fields": "id,name,effective_status,adset{id,name},campaign{id,name}",
             "limit": "500"})
        time.sleep(1.2)
        rows = [a for a in ads
                if "| 0905" in ((a.get("campaign") or {}).get("name") or "")]

        ins = {r.get("adset_id"): r for r in g.account_insights(
            acct, level="adset", fields="adset_id,spend,actions",
            time_range={"since": SINCE, "until": UNTIL})}
        time.sleep(1.2)

        by_camp = collections.defaultdict(list)
        for a in rows:
            by_camp[(a.get("campaign") or {}).get("name") or "?"].append(a)

        for camp in sorted(by_camp):
            print(f"◆ {camp}")
            for a in sorted(by_camp[camp], key=lambda x: (x.get("name") or "")):
                aset = a.get("adset") or {}
                spend, leads = parse_metrics(ins.get(aset.get("id")), token)
                cpl = spend / leads if leads else None
                est = a.get("effective_status")
                mark = ("✅" if est == "ACTIVE"
                        else "⛔" if est in ("WITH_ISSUES", "DISAPPROVED")
                        else "·")
                print(f"  {mark} [{est:>15}] RM{spend:>6.0f} · {leads:>2.0f} leads · "
                      f"CPL {'RM%.0f' % cpl if cpl else '—':>6}  «{(a.get('name') or '')[:34]}»")
            print()

    if new_sales:
        print("💰 已归因到 0905 结构的成交：")
        for s2 in new_sales:
            print(f"   {s2.date}  «{s2.campaign[:44]}» › «{s2.adset[:24]}» › «{s2.ad[:26]}»")
    else:
        print("💰 0905 结构成交：0（下一场分享会是周三，正常）")
    print("\nREPORT DONE (read-only)")


if __name__ == "__main__":
    main()
