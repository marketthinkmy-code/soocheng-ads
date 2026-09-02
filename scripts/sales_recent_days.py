# -*- coding: utf-8 -*-
"""Recent paid sales (last N days, default 7) from the Paid Student List, grouped per day and
per (ad, ad set, campaign) UTM, with each ad's live status on both accounts. Read-only.

track_yesterday.py answers "yesterday only"; the daily routine also needs same-day sales
(the Wednesday webinar closes land on the day itself), so this widens the window and shows
which creative each sale is attributed to.
"""
from __future__ import annotations

import datetime as dt
import os
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import load_settings

SHEET = "1NMtGKVHRYFSsUw3-dacNPYDZABcYKi6VZgMR0u_oZRE"
TAB = "Paid Student List"
ACCTS = [("MY", "act_759339046918885"), ("SG", "act_893025326577600")]
DAYS = int(os.environ.get("DAYS", "7"))


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()  # MYT
    since = today - dt.timedelta(days=DAYS - 1)
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(SHEET, TAB)
    cols = cpa.find_columns(vals[0])
    dcol = cols["date"]

    name_status: dict = defaultdict(list)
    for label, acct in ACCTS:
        for a in g._get_all(f"{acct}/ads",
                            {"fields": "name,effective_status,campaign{name},adset{name}",
                             "limit": "800"}):
            name_status[cpa.norm(a.get("name", ""))].append(
                (label, (a.get("campaign") or {}).get("name", ""),
                 (a.get("adset") or {}).get("name", ""), a.get("effective_status")))

    rows = []
    for row in vals[1:]:
        dd = cpa.parse_date(row[dcol]) if dcol < len(row) else None
        if dd and since <= dd <= today:
            def c(i):
                return row[i] if 0 <= i < len(row) else ""
            rows.append((dd, cpa.norm(c(cols["campaign"])), cpa.norm(c(cols["adset"])),
                         cpa.norm(c(cols["ad"]))))

    print(f"today(MYT)={today}  window={since} → {today}  rows={len(rows)}")
    for d in sorted({r[0] for r in rows}):
        day = [r for r in rows if r[0] == d]
        print(f"\n=== {d}: {len(day)} sales ===")
        for (camp, adset, ad), n in Counter((c, a, x) for _d, c, a, x in day).most_common():
            where = name_status.get(ad, [])
            act = sorted({w[0] for w in where if w[3] == "ACTIVE"})
            if not ad:
                tag = "— no UTM ad name on the row"
            elif act:
                tag = "✓ ACTIVE " + "+".join(act)
            elif where:
                tag = "⚠ ALL PAUSED"
            else:
                tag = "? name not found on either account"
            print(f"  {n}x  ad«{ad}»  set«{adset}»  camp«{camp}»  -> {tag}")
    print("\nDONE.")


if __name__ == "__main__":
    main()
