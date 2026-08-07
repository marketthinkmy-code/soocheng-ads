"""Read-only: rank ad sets (= targeting) by paid students, from the Paid Student List.
The ad-set name is the UTM utm_adset value on each sale. Groups by ad-set, ranks by
sales count, and shows which campaign(s) each ran under. No writes.
"""
from __future__ import annotations

from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import load_settings


def main() -> None:
    s = load_settings()
    values = SheetsClient(s.secrets.google_sa_json).read_tab(
        s.cpa.spreadsheet_id, s.cpa.sales_tab)
    _sales, cols, header = cpa.parse_sales(values, s.cpa.price_myr)
    hidx = next(i for i, r in enumerate(values) if r == header)
    ai, ci = cols.get("adset", -1), cols.get("campaign", -1)

    def cell(row, i):
        return row[i].strip() if 0 <= i < len(row) else ""

    buys = defaultdict(int)
    raw = {}
    camps = defaultdict(lambda: defaultdict(int))
    no_adset = attributed = 0
    for row in values[hidx + 1:]:
        aset, camp = cell(row, ai), cell(row, ci)
        if not aset and not camp:
            continue                      # blank row
        if not aset:
            no_adset += 1
            continue                      # a sale with no ad-set UTM (organic/manual)
        k = cpa.norm(aset)
        buys[k] += 1
        attributed += 1
        raw.setdefault(k, aset)
        if camp:
            camps[k][camp] += 1

    ranked = sorted(buys, key=lambda k: -buys[k])
    print(f"{attributed} sales carry an ad-set UTM · {len(buys)} distinct ad sets · "
          f"{no_adset} sales had NO ad-set tag\n")

    print("=" * 74)
    print("TOP 3 AD SETS (targeting) BY PAID STUDENTS")
    print("=" * 74)
    for i, k in enumerate(ranked[:3], 1):
        top_camps = sorted(camps[k].items(), key=lambda x: -x[1])[:2]
        cc = " · ".join(f"{c} ({n})" for c, n in top_camps)
        print(f"{i}. {raw[k]}  —  {buys[k]} 成交")
        print(f"     campaigns: {cc}")

    print("\n" + "-" * 74)
    print("FULL RANKING (ad set → 成交)")
    print("-" * 74)
    for i, k in enumerate(ranked, 1):
        print(f"{i:>2}. {buys[k]:>3}  {raw[k]}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
