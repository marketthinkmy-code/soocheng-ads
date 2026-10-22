# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-22: Paid Student List rows dated >= 10/14 — Date · Amount · Channel · Source · Experience · UTM
(no name / email / phone / remark). Shows where the 10/21 Webinarkit-live buyers came from when UTM is blank."""
from __future__ import annotations

import datetime as dt

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

KEEP = ("Date", "Purchase Amount", "Channel", "Source", "Experience", "UTM Campaign", "UTM Ads Set", "UTM Ads Name")


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    hi = next(i for i, r in enumerate(vals[:8]) if "UTM Campaign" in r)
    h = vals[hi]
    idx = [h.index(k) for k in KEEP if k in h]
    di = h.index("Date")
    print(" | ".join(h[i] for i in idx))
    for r in vals[hi + 1:]:
        d = cpa.parse_date(r[di]) if di < len(r) else None
        if d and d >= dt.date(2026, 10, 14):
            print(" | ".join((r[i] if i < len(r) else "")[:40] for i in idx))
    print("CHANNEL DONE (read-only)")


if __name__ == "__main__":
    main()
