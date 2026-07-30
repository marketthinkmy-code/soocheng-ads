# -*- coding: utf-8 -*-
"""Latest Paid Student List -> LAST-30-DAY winners only: TOP ads / ad sets / campaigns by
real paid conversions. Shows the 30-day denominator (+ MY vs SG split) so the ranking is
trustworthy. Flags 禁跑名单 creatives (⛔). Read-only.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from adbot import cpa as C
from adbot.clients.sheets import SheetsClient
from adbot.settings import load_settings

SHEET = "1NMtGKVHRYFSsUw3-dacNPYDZABcYKi6VZgMR0u_oZRE"
TAB = "Paid Student List"
PRICE = 2399.0
WINDOW = 30

BANNED = ["不是怕交易", "厌倦了等待", "moomoo", "1 分钟赚 300", "1分钟赚300",
          "每天 1 分钟", "每天1分钟", "你敢吗", "freestyle 2", "炒过那么多"]


def is_banned(nm: str) -> bool:
    n = (nm or "").lower()
    return any(b.lower() in n for b in BANNED)


def fmt_of(nm: str) -> str:
    n = (nm or "").lower()
    if "single image" in n or "单图" in nm or n.startswith("image"):
        return "单图"
    if n.startswith("video") or "freestyle" in n:
        return "video"
    return "?"


def top(counter, n=10):
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def main() -> None:
    s = load_settings()
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(SHEET, TAB)
    sales, _cols, _hdr = C.parse_sales(vals, PRICE)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    cut = today - dt.timedelta(days=WINDOW)
    recent = [x for x in sales if x.date and x.date > cut]

    my = sum(1 for x in recent if not (x.campaign or "").startswith("[sg]"))
    sg = len(recent) - my
    print(f"WINDOW = last {WINDOW} days ({cut} → {today}, GMT+8)")
    print(f"30-day paid sales = {len(recent)}   (SG {sg} · MY/other {my})   [lifetime total {len(sales)}]\n")

    ad, aset, camp = defaultdict(int), defaultdict(int), defaultdict(int)
    for x in recent:
        if x.ad:
            ad[x.ad] += 1
        if x.adset:
            aset[x.adset] += 1
        if x.campaign:
            camp[x.campaign] += 1

    print("=" * 72)
    print(f"TOP ADS — last {WINDOW} days   (⛔ = 禁跑名单, don't replicate)")
    print("=" * 72)
    for i, (nm, n) in enumerate(top(ad), 1):
        flag = "  ⛔BANNED" if is_banned(nm) else ""
        print(f"  {i:2d}. {n:3d}  [{fmt_of(nm):5}] {nm[:48]}{flag}")

    print("\n" + "=" * 72)
    print(f"TOP AD SETS — last {WINDOW} days")
    print("=" * 72)
    for i, (nm, n) in enumerate(top(aset), 1):
        print(f"  {i:2d}. {n:3d}  {nm[:58]}")

    print("\n" + "=" * 72)
    print(f"TOP CAMPAIGNS — last {WINDOW} days   (cross-check; cleaner attribution)")
    print("=" * 72)
    for i, (nm, n) in enumerate(top(camp), 1):
        print(f"  {i:2d}. {n:3d}  {nm[:58]}")
    print("\nDONE (read-only).")


if __name__ == "__main__":
    main()
