# -*- coding: utf-8 -*-
"""READ-ONLY: per-account (UTM [sg] split) top converting ADS with
lifetime / 60d / 30d sale counts from the Paid Student List."""
from __future__ import annotations

import datetime as dt

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

TODAY = dt.date(2026, 8, 19)
D30 = TODAY - dt.timedelta(days=30)
D60 = TODAY - dt.timedelta(days=60)
SHOW = 8


def main() -> None:
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)

    per = {"MY": {}, "SG": {}}
    for s in sales:
        if not s.ad:
            continue
        label = "SG" if s.campaign.startswith("[sg]") else "MY"
        d = per[label].setdefault(s.ad, {"life": 0, "d60": 0, "d30": 0})
        d["life"] += 1
        if s.date and s.date > D60:
            d["d60"] += 1
        if s.date and s.date > D30:
            d["d30"] += 1

    for label in ("MY", "SG"):
        print(f"═══ [{label}] — sales by ad (lifetime / 60d / 30d) ═══")
        ranked = sorted(per[label].items(),
                        key=lambda kv: (-kv[1]["d30"], -kv[1]["d60"], -kv[1]["life"]))
        for name, d in ranked[:SHOW]:
            print(f"  life={d['life']:3d}  60d={d['d60']:2d}  30d={d['d30']:2d}   «{name[:56]}»")
        print()
    print("COUNTS DONE (read-only)")


if __name__ == "__main__":
    main()
