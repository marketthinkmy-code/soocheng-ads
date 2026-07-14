"""Read-only final verification of the SG clone on act_893025326577600:
5 campaigns, each 1-1-3, advertiser binding present, everything PAUSED. Resilient to
per-account rate limits (per-campaign try/except). No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

DST = "act_893025326577600"


def main() -> None:
    g = graph_client(load_settings())
    camps = g._get_all(f"{DST}/campaigns", {
        "fields": "id,name,effective_status,daily_budget", "limit": "200"})
    sg = [c for c in camps if "STOCKBLOOM" in (c.get("name") or "")]
    print(f"{len(sg)} STOCKBLOOM campaigns on {DST}\n")
    total_ads = 0
    for c in sorted(sg, key=lambda x: x.get("name") or ""):
        print(f"● {c.get('name')}  [{c.get('effective_status')}]  "
              f"RM{(c.get('daily_budget') or 0)}/100/day  ({c['id']})")
        try:
            for aset in g._get_all(f"{c['id']}/adsets", {
                    "fields": "id,name,effective_status,regional_regulation_identities,"
                              "targeting", "limit": "10"}):
                t = aset.get("targeting") or {}
                geo = (t.get("geo_locations") or {}).get("countries")
                rri = aset.get("regional_regulation_identities")
                print(f"   adset [{aset.get('effective_status')}] geo={geo} advertiser={rri}")
                ads = g._get_all(f"{aset['id']}/ads", {
                    "fields": "id,name,effective_status", "limit": "20"})
                total_ads += len(ads)
                for a in ads:
                    print(f"      - {a.get('name')}  [{a.get('effective_status')}]  ({a['id']})")
        except Exception as exc:  # noqa: BLE001
            print(f"   (read throttled/failed: {str(exc)[:80]})")
        print()
    print(f"TOTAL ads across SG campaigns: {total_ads}")
    print("DONE.")


if __name__ == "__main__":
    main()
