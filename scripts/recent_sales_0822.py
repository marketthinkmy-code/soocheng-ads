# -*- coding: utf-8 -*-
"""READ-ONLY: latest Paid Student List rows — every sale dated 2026-08-10 or
later (date · account · ad · campaign), newest first, so the owner sees
whether anything closed since the 8/15 lull."""
from __future__ import annotations

import datetime as dt

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

CUTOFF = dt.date(2026, 8, 10)


def main() -> None:
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    recent = [s for s in sales if s.date and s.date >= CUTOFF]
    total = len([s for s in sales if s.date])
    undated = len(sales) - total
    print(f"sheet 总行数(有日期) {total} · 无日期 {undated} · {CUTOFF} 起 {len(recent)} 单\n")
    for s in sorted(recent, key=lambda x: x.date, reverse=True):
        label = "SG" if s.campaign.startswith("[sg]") else "MY"
        mark = " ★新" if s.date >= dt.date(2026, 8, 16) else ""
        print(f"  {s.date}  [{label}]  «{(s.ad or '(无 UTM ad)')[:36]}»"
              f"  ({(s.campaign or '')[:34]}){mark}")
    by_day = {}
    for s in recent:
        by_day[s.date] = by_day.get(s.date, 0) + 1
    print("\n  按日: " + " · ".join(
        f"{d.strftime('%m/%d')}={n}" for d, n in sorted(by_day.items())))
    print("RECENT SALES DONE (read-only)")


if __name__ == "__main__":
    main()
