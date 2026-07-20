"""Latest Paid Student List -> rank ads by PAID conversions, isolate the SINGLE-IMAGE
winners (so the team can produce more single-image ads from proven angles). Read-only.

Format is inferred from the ad name (single-image ads are named 'single image ...' / '单图').
Banned creatives (CLAUDE.md 禁跑名单) are flagged so the team never replicates them.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import load_settings

SHEET = "1NMtGKVHRYFSsUw3-dacNPYDZABcYKi6VZgMR0u_oZRE"
TAB = "Paid Student List"
BANNED = ["moomoo", "每天 1 分钟就能盈利", "每天1分钟就能盈利", "1 分钟赚 300", "1分钟赚300",
          "不是怕交易", "厌倦了等待", "你敢吗", "炒过那么多", "freestyle 2"]


def is_single_image(nm: str) -> bool:
    n = nm.lower()
    return ("single image" in n) or ("单图" in nm) or n.startswith("image ")


def is_banned(nm: str) -> bool:
    n = nm.lower()
    return any(b.lower() in n for b in BANNED)


def fmt_of(nm: str) -> str:
    if is_single_image(nm):
        return "单图"
    if nm.lower().startswith("video") or "freestyle" in nm.lower():
        return "video"
    return "?"


def main() -> None:
    s = load_settings()
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(SHEET, TAB)
    sales, _cols, _hdr = cpa.parse_sales(vals, 2399.0)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()

    life: dict = defaultdict(int)
    w30: dict = defaultdict(int)
    for x in sales:
        if not x.ad:
            continue
        life[x.ad] += 1
        if x.date and x.date > today - dt.timedelta(days=30):
            w30[x.ad] += 1
    print(f"sheet rows={len(vals)}  parsed sales={len(sales)}  distinct ads={len(life)}\n")

    si = sorted([(life[a], w30.get(a, 0), a) for a in life if is_single_image(a)],
                key=lambda x: -x[0])
    print("=" * 74)
    print("SINGLE-IMAGE ads by PAID conversions (⛔ = banned, don't replicate)")
    print("  total 30d  ad name")
    print("=" * 74)
    for tot, r30, a in si:
        print(f"  {tot:4d} {r30:3d}   {a[:54]}{'   ⛔BANNED' if is_banned(a) else ''}")

    allr = sorted([(life[a], w30.get(a, 0), a) for a in life], key=lambda x: -x[0])
    print("\n" + "=" * 74)
    print("TOP 20 OVERALL (any format) — winning ANGLES worth adapting into single-image")
    print("  total 30d [fmt ]  ad name")
    print("=" * 74)
    for tot, r30, a in allr[:20]:
        print(f"  {tot:4d} {r30:3d}  [{fmt_of(a):5}] {a[:48]}{'  ⛔' if is_banned(a) else ''}")
    print("\nDONE.")


if __name__ == "__main__":
    main()
