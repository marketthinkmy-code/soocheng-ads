"""Read-only: which SINGLE-IMAGE (单图) ads actually closed sales?

Joins the lifetime Paid Student List (sales attributed by ad name) with creative types.
An ad is single-image if its creative has image_hash and no video_id. Winning historical
ads mostly lived on now-banned accounts we can't read, so we classify by:
  1) creative lookup on every reachable account (authoritative), else
  2) the ad-name convention (Image… / 单图 / …图 = image; video/Video/freestyle/突访/采访 = video).
Outputs the single-image ad-name list with paid-student counts. No writes.
"""
from __future__ import annotations

from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import load_settings

# accounts to try for creative lookup (reachable + old banned ones, best-effort)
EXTRA_ACCOUNTS = ["act_1263100565619799", "act_2285351942292267",
                  "act_1017936814163755", "act_893025326577600",
                  "act_2262468824239770"]


def _nrm(x):
    return (cpa.norm(x or "").replace("：", ":").replace("！", "!")
            .replace("？", "?").replace("｜", "|").replace(" ", ""))


def name_kind(name: str):
    """Heuristic image/video from the display name; None if undecidable."""
    n = (name or "").lower().strip()
    raw = name or ""
    if (n.startswith("image") or "single image" in n or "单图" in raw
            or raw.rstrip().endswith("图") or "图：" in raw or "图:" in raw):
        return "img"
    if (n.startswith("video") or "freestyle" in n or "突访" in raw or "突击" in raw
            or "采访" in raw or "街头" in raw or raw.startswith("Reel") or "reel" in n):
        return "vid"
    return None


def main() -> None:
    s = load_settings()
    g = graph_client(s)

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
    print(f"Paid Student List: {sum(buys.values())} sales attributed to an ad · "
          f"{len(buys)} distinct ad names\n")

    # creative-type index from every reachable account
    kind_idx = defaultdict(set)
    accts = [s.meta.account_path] + [a for a in EXTRA_ACCOUNTS if a != s.meta.account_path]
    for acct in accts:
        try:
            ads = g._get_all(f"{acct}/ads", {
                "fields": "name,creative{video_id,image_hash}", "limit": "400"})
        except Exception as exc:  # noqa: BLE001
            print(f"  (skip {acct}: {str(exc)[:60]})")
            continue
        for a in ads:
            cr = a.get("creative") or {}
            k = "img" if (cr.get("image_hash") and not cr.get("video_id")) else (
                "vid" if cr.get("video_id") else None)
            if k:
                kind_idx[_nrm(a.get("name", ""))].add(k)
    print()

    rows = []       # (buys, rev, name, method)
    unknown = []    # sales ad names we couldn't classify at all
    for k in buys:
        ck = kind_idx.get(k, set())
        if ck:
            kind, method = ("img" if "img" in ck else "vid"), "creative"
        else:
            kind, method = name_kind(raw[k]), "name"
        if kind == "img":
            rows.append((buys[k], rev[k], raw[k], method))
        elif kind is None:
            unknown.append((buys[k], raw[k]))

    rows.sort(key=lambda r: (-r[0], -r[1]))
    print("=" * 74)
    print("SINGLE-IMAGE (单图) ADS THAT CLOSED SALES")
    print("=" * 74)
    print(f"{'#':>2} {'sales':>5} {'revenue':>10}  ad name   [how classified]")
    tot = 0
    for i, (b, r, name, method) in enumerate(rows, 1):
        tot += b
        print(f"{i:>2} {b:>5} RM{r:>8,.0f}  {name}   [{method}]")
    print(f"\n{len(rows)} single-image ad names · {tot} sales total")

    if unknown:
        unknown.sort(key=lambda x: -x[0])
        print("\n" + "-" * 74)
        print(f"NOT CLASSIFIED (no creative on reachable accounts, name ambiguous) — "
              f"{len(unknown)} names, review manually:")
        for b, name in unknown:
            print(f"   {b:>3} sales  {name}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
