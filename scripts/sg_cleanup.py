"""Remove any half-built clone campaigns from the SG account (act_893025326577600).
The SG build is blocked on Singapore advertiser verification; this deletes the empty
orphan campaign(s) so the account is left clean until verification is done. Dry-run
unless CONFIRM=true.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
DST = "act_893025326577600"
TARGET_NAMES = {
    "STOCKBLOOM | GOLF PICKBLEBALL | 1-1-3",
    "STOCKBLOOM | TRAVEL | 1-1-3",
    "STOCKBLOOM | TRAVEL | 1-1-3 (2)",
    "STOCKBLOOM | BROAD | 1-1-3 A",
    "STOCKBLOOM | BROAD | 1-1-3 B",
}


def main() -> None:
    g = graph_client(load_settings())
    camps = g._get_all(f"{DST}/campaigns",
                       {"fields": "id,name,effective_status", "limit": "200"})
    print(f"{len(camps)} campaign(s) on {DST}")
    hits = [c for c in camps if c.get("name") in TARGET_NAMES]
    if not hits:
        print("  no clone orphans present — nothing to clean.")
    for c in hits:
        if CONFIRM:
            g._request("DELETE", c["id"])
            print(f"  deleted {c['id']}  [{c.get('effective_status')}]  {c.get('name')}")
        else:
            print(f"  WOULD DELETE {c['id']}  [{c.get('effective_status')}]  {c.get('name')}")
    # show remaining
    left = g._get_all(f"{DST}/campaigns", {"fields": "id,name", "limit": "200"})
    print(f"\nremaining campaigns on {DST}: {len(left)}")
    print("DONE.")


if __name__ == "__main__":
    main()
