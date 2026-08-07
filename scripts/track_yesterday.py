"""Track YESTERDAY's paid conversions -> (ad name, ad set) and confirm each of those ads is
still ACTIVE on Meta, so the CPL monitor never mis-pauses a converting ad. Read-only.

Prints the sheet header + every date-ish column's recent daily counts (to pin down exactly
which column = 'purchase date' and reconcile the owner's "21 单 yesterday"), then lists
yesterday's sales grouped by (ad, ad set) with live ACTIVE / PAUSED status on both accounts.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import load_settings

SHEET = "1NMtGKVHRYFSsUw3-dacNPYDZABcYKi6VZgMR0u_oZRE"
TAB = "Paid Student List"
ACCTS = [("MY", "act_759339046918885"), ("SG", "act_893025326577600")]


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()  # MYT
    y = today - dt.timedelta(days=1)
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(SHEET, TAB)
    hdr = vals[0]
    cols = cpa.find_columns(hdr)
    datecols = [i for i, h in enumerate(hdr) if "date" in cpa._hkey(h)]
    print(f"today(MYT)={today}  yesterday={y}")
    print("HEADER:", [f"{i}:{h}" for i, h in enumerate(hdr) if h])
    print("parse cols:", cols, " date-ish cols:", [(i, hdr[i]) for i in datecols])
    print("\n-- recent daily counts per date-ish column --")
    for dcol in datecols:
        cnt = Counter()
        for row in vals[1:]:
            dd = cpa.parse_date(row[dcol]) if dcol < len(row) else None
            if dd:
                cnt[dd] += 1
        recent = sorted([(k, v) for k, v in cnt.items() if k >= today - dt.timedelta(days=4)])
        print(f"  col{dcol} «{hdr[dcol]}»: " + ", ".join(f"{k}={v}" for k, v in recent))

    # live ad index (both accounts), by normalised ad name
    name_status: dict = defaultdict(list)   # norm(name) -> [(acct, campaign, adset, status)]
    active_names = set()
    for label, acct in ACCTS:
        ads = g._get_all(f"{acct}/ads",
                         {"fields": "name,effective_status,campaign{name},adset{name}",
                          "limit": "800"})
        for a in ads:
            nm = cpa.norm(a.get("name", ""))
            st = a.get("effective_status")
            name_status[nm].append((label, (a.get("campaign") or {}).get("name", ""),
                                    (a.get("adset") or {}).get("name", ""), st))
            if st == "ACTIVE":
                active_names.add(nm)

    # yesterday's sales via the parse_sales date column
    dcol = cols["date"]
    ys = []
    for row in vals[1:]:
        dd = cpa.parse_date(row[dcol]) if dcol < len(row) else None
        if dd == y:
            def c(i):
                return row[i] if 0 <= i < len(row) else ""
            ys.append((cpa.norm(c(cols["campaign"])), cpa.norm(c(cols["adset"])),
                       cpa.norm(c(cols["ad"]))))

    print(f"\n{'='*92}\nYESTERDAY {y}: {len(ys)} sales — by (ad, ad set), with live status\n{'='*92}")
    grp = Counter((ad, adset) for _camp, adset, ad in ys)
    for (ad, adset), n in grp.most_common():
        act_where = [w for w in name_status.get(ad, []) if w[3] == "ACTIVE"]
        if ad in active_names:
            tag = "✓ ACTIVE " + "+".join(sorted({w[0] for w in act_where}))
        elif name_status.get(ad):
            tag = "⚠ ALL PAUSED"
        else:
            tag = "? name not found"
        print(f"  {n:2d}x  {tag:18}  ad«{ad[:34]}»  set«{adset[:26]}»")

    dead = [(ad, adset, n) for (ad, adset), n in grp.items() if ad not in active_names]
    print(f"\n⚠ yesterday-converting ads NOT currently ACTIVE: {len(dead)}")
    for ad, adset, n in sorted(dead, key=lambda x: -x[2]):
        print(f"   {n}x  ad«{ad[:40]}»  set«{adset[:24]}»  -> {name_status.get(ad) or 'no such ad name on either account'}")

    # where each still-active converting creative is running (placements to protect)
    print("\n-- active placements of yesterday's converting creatives (protect these) --")
    for ad in sorted({ad for (ad, _s) in grp}):
        for label, camp, aset, st in name_status.get(ad, []):
            if st == "ACTIVE":
                print(f"   [{label}] {camp[:38]:38}  / {aset[:30]:30}  ad«{ad[:30]}»")
    print("\nDONE.")


if __name__ == "__main__":
    main()
