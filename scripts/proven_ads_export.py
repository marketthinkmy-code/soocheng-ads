"""Read-only: proven-ads export, prep for the NEW ad account.

Joins the lifetime Paid Student List (every paid student ever, any account) with the
ads on BOTH banned accounts (old MyTrade50 + MTC X STOCKBLOOM 2) to output, per
winning creative name: paid-student count, revenue, and the reusable post id
(effective_object_story_id) + media ids. No writes anywhere.
"""
from __future__ import annotations

from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import load_settings

OLD = "act_2262468824239770"    # MyTrade50 (banned 2026-06-23)


def _nrm(x):
    """cpa.norm + fold fullwidth colon/punct so old sheet names match account ad names."""
    return (cpa.norm(x or "").replace("\uff1a", ":").replace("\uff01", "!")
            .replace("\uff1f", "?").replace("\uff5c", "|").replace(" ", ""))


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    new_acct = s.meta.account_path

    values = SheetsClient(s.secrets.google_sa_json).read_tab(
        s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s.cpa.price_myr)
    buys, rev, raw = defaultdict(int), defaultdict(float), {}
    for sale in sales:
        if not sale.ad:
            continue
        k = _nrm(sale.ad)
        buys[k] += 1
        rev[k] += sale.amount
        raw.setdefault(k, sale.ad)
    print(f"Paid Student List: {len(sales)} data rows · {sum(buys.values())} attributed "
          f"to an ad · {len(buys)} distinct ad names\n")

    def pull(acct):
        return g._get_all(f"{acct}/ads", {
            "fields": "name,effective_status,"
                      "creative{effective_object_story_id,object_story_id,video_id,image_hash}",
            "limit": "400"})

    ads = {"OLD": [], "NEW": []}
    for label, acct in (("OLD", OLD), ("NEW", new_acct)):
        try:
            ads[label] = pull(acct)
        except Exception as exc:  # noqa: BLE001
            print(f"{label} account read failed:", exc)
    print(f"ads pulled: OLD={len(ads['OLD'])} · NEW={len(ads['NEW'])}\n")

    idx = defaultdict(list)
    for label, lst in ads.items():
        for a in lst:
            idx[_nrm(a.get("name", ""))].append((label, a))

    ranked = sorted(buys, key=lambda k: (-buys[k], -rev[k]))

    print("=" * 78)
    print("A · ALL AD NAMES WITH >= 2 LIFETIME PAID STUDENTS (any account)")
    print("=" * 78)
    print(f"{'#':>2} {'buys':>4} {'revenue':>10}  ad name")
    for i, k in enumerate([k for k in ranked if buys[k] >= 2], 1):
        print(f"{i:>2} {buys[k]:>4} RM{rev[k]:>8,.0f}  {raw[k]}")

    print("\n" + "=" * 78)
    print("B · TOP 22 BY PAID STUDENTS — with POST IDs for the new-account rebuild")
    print("=" * 78)
    for i, k in enumerate(ranked[:22], 1):
        print(f"\n{i}. {raw[k]}   — {buys[k]} paid · RM{rev[k]:,.0f}")
        matches = idx.get(k, [])
        loose = False
        if not matches:
            matches = [(label, a) for label, lst in ads.items() for a in lst
                       if _nrm(a.get("name", ""))
                       and (k in _nrm(a.get("name", "")) or _nrm(a.get("name", "")) in k)]
            loose = bool(matches)
        if loose:
            print("   (loose name match)")
        if not matches:
            print("   !! no ad found on either account under this name")
            continue
        seen = set()
        for label, a in matches:
            cr = a.get("creative") or {}
            post = cr.get("effective_object_story_id") or cr.get("object_story_id") or "-"
            media = cr.get("video_id") or cr.get("image_hash") or "-"
            if (post, media) in seen:
                continue
            seen.add((post, media))
            kind = "vid" if cr.get("video_id") else ("img" if cr.get("image_hash") else "??")
            print(f"   [{label}] post={post}  {kind}={media}  "
                  f"[{a.get('effective_status')}]  {a.get('name')}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
