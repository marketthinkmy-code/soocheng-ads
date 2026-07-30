# -*- coding: utf-8 -*-
"""Latest Paid Student List -> TOP 5 winning ADS (by name) + TOP 3 winning AD SETS,
ranked by real paid conversions (buyers). Whole list (MY + SG). Lifetime rank with a 30-day
column for freshness. Flags 禁跑名单 creatives (⛔ — don't replicate). Read-only.
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

# CLAUDE.md 禁跑名单 — match by DESCRIPTOR (so "video 2：你敢吗" is banned but
# "video 2: 我只有一个目的" is not). Casefold-safe; Chinese is unaffected by casefold.
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


def main() -> None:
    s = load_settings()
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(SHEET, TAB)
    sales, _cols, _hdr = C.parse_sales(vals, PRICE)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    cut30 = today - dt.timedelta(days=30)

    ad_life, ad_30 = defaultdict(int), defaultdict(int)
    aset_life, aset_30 = defaultdict(int), defaultdict(int)
    for x in sales:
        recent = bool(x.date and x.date > cut30)
        if x.ad:
            ad_life[x.ad] += 1
            if recent:
                ad_30[x.ad] += 1
        if x.adset:
            aset_life[x.adset] += 1
            if recent:
                aset_30[x.adset] += 1

    dated = [x for x in sales if x.date]
    span = f"{min(x.date for x in dated)} → {max(x.date for x in dated)}" if dated else "n/a"
    print(f"Paid Student List: {len(sales)} sales · date span {span} · as-of {today} (GMT+8)")
    print(f"distinct ads with a name={len(ad_life)} · distinct ad sets={len(aset_life)}\n")

    print("=" * 78)
    print("TOP 5 WINNING ADS  (by paid conversions · lifetime, 30d shown · ⛔ = 禁跑名单)")
    print("  life  30d  [fmt ]  ad name")
    print("=" * 78)
    for nm, n in sorted(ad_life.items(), key=lambda kv: (-kv[1], kv[0]))[:5]:
        flag = "  ⛔BANNED — do NOT replicate" if is_banned(nm) else ""
        print(f"  {n:4d} {ad_30.get(nm,0):4d}  [{fmt_of(nm):5}] {nm[:46]}{flag}")

    print("\n" + "=" * 78)
    print("TOP 3 WINNING AD SETS  (by paid conversions · lifetime, 30d shown)")
    print("  life  30d  ad set (utm_adset)")
    print("=" * 78)
    for nm, n in sorted(aset_life.items(), key=lambda kv: (-kv[1], kv[0]))[:3]:
        print(f"  {n:4d} {aset_30.get(nm,0):4d}  {nm[:60]}")

    # freshness aid: what's winning in the last 30 days specifically
    print("\n-- for reference: TOP 5 ADS in the LAST 30 DAYS --")
    for nm, n in sorted(ad_30.items(), key=lambda kv: (-kv[1], kv[0]))[:5]:
        flag = "  ⛔" if is_banned(nm) else ""
        print(f"  {n:4d}  [{fmt_of(nm):5}] {nm[:46]}{flag}")
    print("\n-- for reference: TOP 3 AD SETS in the LAST 30 DAYS --")
    for nm, n in sorted(aset_30.items(), key=lambda kv: (-kv[1], kv[0]))[:3]:
        print(f"  {n:4d}  {nm[:60]}")
    print("\nDONE (read-only).")


if __name__ == "__main__":
    main()
