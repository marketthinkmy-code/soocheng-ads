"""Paid Student List -> TOP ad set TARGETING by paid conversions in the last 30 days.
Groups sales by targeting theme (keyword-matched from utm ad set + campaign name), and also
dumps the raw utm ad-set / campaign breakdown so the ranking can be verified. Read-only.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import load_settings

SHEET = "1NMtGKVHRYFSsUw3-dacNPYDZABcYKi6VZgMR0u_oZRE"
TAB = "Paid Student List"

THEMES = [
    ("News", ["news"]),
    ("Travel", ["travel"]),
    ("Golf/Pickleball", ["golf", "pickle", "pickble"]),
    ("Luxury Goods", ["luxury"]),
    ("Business Owner", ["business owner", "bizowner", "biz owner"]),
    ("Investment", ["investment"]),
    ("Running", ["running", "run club", "runclub"]),
    ("Omakase/Wagyu", ["omakase", "wagyu"]),
    ("Luxury Watches", ["watch"]),
    ("Broad/Advantage+", ["broad", "advantage", "1-1-9", "1-1-10", "1-1-3", "andro"]),
]


def theme_of(adset: str, camp: str):
    s = (adset + " " + camp).lower()
    for name, kws in THEMES:
        if any(k in s for k in kws):
            return name
    return None


def main() -> None:
    st = load_settings()
    vals = SheetsClient(st.secrets.google_sa_json).read_tab(SHEET, TAB)
    sales, _cols, _hdr = cpa.parse_sales(vals, 2399.0)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    cut30 = today - dt.timedelta(days=30)
    y = today - dt.timedelta(days=1)
    recent = [x for x in sales if x.date and x.date > cut30]
    yday = [x for x in sales if x.date == y]
    print(f"sheet rows={len(vals)}  total sales={len(sales)}  last30d={len(recent)} (since {cut30})  "
          f"yesterday({y})={len(yday)}\n")

    themed = Counter()
    unmatched = Counter()
    for x in recent:
        t = theme_of(x.adset, x.campaign)
        if t:
            themed[t] += 1
        else:
            unmatched[(x.adset or x.campaign or "(blank)")[:46]] += 1

    print("=" * 66)
    print("AD SET TARGETING by paid conversions — LAST 30 DAYS (themed)")
    print("=" * 66)
    for t, c in themed.most_common():
        print(f"  {c:4d}  {t}")
    print("\n-- unmatched (no theme keyword) --")
    for k, c in unmatched.most_common(12):
        print(f"  {c:4d}  {k}")

    print("\n=== raw utm AD SET (last 30d, top 20) ===")
    for a, c in Counter(x.adset for x in recent if x.adset).most_common(20):
        print(f"  {c:4d}  {a[:52]}")

    print("\n=== raw utm CAMPAIGN (last 30d, top 20) ===")
    for a, c in Counter(x.campaign for x in recent if x.campaign).most_common(20):
        print(f"  {c:4d}  {a[:52]}")
    print("\nDONE.")


if __name__ == "__main__":
    main()
