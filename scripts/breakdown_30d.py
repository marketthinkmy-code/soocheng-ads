# -*- coding: utf-8 -*-
"""Account for EVERY one of the last-30d paid sales — no top-N truncation.

Answers 「总数 112 单，top 1 才 12 单？」: shows the full per-ad distribution, the rows with
no ad name, the organic/non-ads portion, and a creative-FAMILY rollup (freestyle 1 + korea,
video 5 variants, …) so concentration is judged fairly. Read-only.
"""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter

from adbot import cpa as C
from adbot.clients.sheets import SheetsClient
from adbot.settings import load_settings

SHEET = "1NMtGKVHRYFSsUw3-dacNPYDZABcYKi6VZgMR0u_oZRE"
TAB = "Paid Student List"
WINDOW = 30
ORGANIC_TOKENS = ("link_in_bio", "linkinbio", "bio", "wamsg", "scigbio", "whatsapp", "organic")

BANNED = ["不是怕交易", "厌倦了等待", "moomoo", "1分钟赚300", "1 分钟赚 300",
          "每天1分钟", "每天 1 分钟", "你敢吗", "freestyle 2", "炒过那么多"]


def is_banned(nm: str) -> bool:
    n = (nm or "").lower()
    return any(b.lower() in n for b in BANNED)


def family(nm: str) -> str:
    """'video 5：盖电脑，喂！' -> 'video 5' ; 'freestyle: korea' -> 'freestyle' ;
    'freestyle 1' -> 'freestyle'."""
    n = (nm or "").strip().lower()
    m = re.match(r"(video\s*\d+)", n)
    if m:
        return m.group(1)
    if n.startswith("freestyle"):
        return "freestyle"
    m = re.match(r"(single\s*image|image)\s*\d*", n)
    if m:
        return "单图"
    return n[:24]


def is_organic(x) -> bool:
    blob = f"{x.campaign} {x.adset} {x.ad}".lower()
    if any(t in blob for t in ORGANIC_TOKENS):
        return True
    return not x.campaign  # no utm_campaign at all -> not a paid ad click


def main() -> None:
    s = load_settings()
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(SHEET, TAB)
    sales, _cols, _hdr = C.parse_sales(vals, s.cpa.price_myr)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    cut = today - dt.timedelta(days=WINDOW)
    recent = [x for x in sales if x.date and x.date > cut]

    organic = [x for x in recent if is_organic(x)]
    paid = [x for x in recent if not is_organic(x)]
    paid_named = [x for x in paid if x.ad]
    paid_unnamed = [x for x in paid if not x.ad]

    print(f"last {WINDOW}d ({cut} → {today}): {len(recent)} sales total")
    print(f"  = paid ads with ad name  : {len(paid_named)}")
    print(f"  + paid ads, ad name BLANK: {len(paid_unnamed)}")
    print(f"  + organic / non-ads      : {len(organic)}  (link_in_bio / wamsg / no utm etc.)\n")

    print("=" * 70)
    print("EVERY AD — full 30d distribution (nothing truncated)")
    print("=" * 70)
    counts = Counter(x.ad for x in paid_named)
    total_check = 0
    for i, (nm, n) in enumerate(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])), 1):
        total_check += n
        share = 100.0 * n / len(recent)
        print(f"  {i:2d}. {n:3d}  ({share:4.1f}%)  {nm[:46]}{'  ⛔' if is_banned(nm) else ''}")
    print(f"  ── named-ad subtotal = {total_check}")

    if paid_unnamed:
        print("\n  paid but ad-name blank — their campaigns:")
        for nm, n in Counter(x.campaign or "(blank)" for x in paid_unnamed).most_common():
            print(f"    {n:3d}  {nm[:56]}")

    if organic:
        print("\n  organic / non-ads rows — their source markers:")
        for nm, n in Counter((x.campaign or x.adset or x.ad or "(all blank)") for x in organic).most_common():
            print(f"    {n:3d}  {nm[:56]}")

    print("\n" + "=" * 70)
    print("CREATIVE FAMILY rollup (fair concentration view)")
    print("=" * 70)
    fam = Counter(family(x.ad) for x in paid_named)
    for nm, n in fam.most_common(12):
        share = 100.0 * n / len(paid_named)
        print(f"  {n:3d}  ({share:4.1f}% of paid-named)  {nm}")

    named = sorted(counts.values(), reverse=True)
    top5 = sum(named[:5])
    print(f"\nconcentration: distinct ads with ≥1 sale = {len(counts)} · "
          f"top1 {named[0]}/{len(recent)} = {100*named[0]/len(recent):.0f}% · "
          f"top5 = {top5} ({100*top5/len(recent):.0f}%)")
    print("\nDONE (read-only).")


if __name__ == "__main__":
    main()
