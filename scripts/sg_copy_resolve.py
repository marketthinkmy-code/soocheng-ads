"""Read-only: resolve everything to clone the ACTIVE MY campaigns (act_759339046918885)
into the SG account (act_893025326577600). Prints each source campaign→adset→ad with
its creative reuse handle (object_story_id / video_id / image_hash), and the SG account's
pixel + whether the page is promotable there. No writes.
"""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import load_settings

SRC = "act_759339046918885"          # MTC X SB 3.0 (MY)
DST = "act_893025326577600"          # [SG] MTC X SB
BUSINESS = "769016565904540"
PAGE = "1001334883061622"


def main() -> None:
    g = graph_client(load_settings())

    print("=" * 80)
    print("SOURCE — ACTIVE campaigns on act_759339046918885 (MY)")
    print("=" * 80)
    camps = g._get_all(f"{SRC}/campaigns", {
        "fields": "id,name,effective_status,objective,daily_budget,lifetime_budget,"
                  "bid_strategy,special_ad_categories", "limit": "200"})
    active = [c for c in camps if c.get("effective_status") == "ACTIVE"]
    print(f"{len(camps)} campaigns total · {len(active)} ACTIVE\n")
    for c in active:
        print(f"CAMP {c['id']}  {c.get('name')}")
        print(f"   objective={c.get('objective')} daily_budget={c.get('daily_budget')} "
              f"bid={c.get('bid_strategy')} cats={c.get('special_ad_categories')}")
        for aset in g._get_all(f"{c['id']}/adsets", {
                "fields": "id,name,optimization_goal,billing_event,promoted_object,"
                          "daily_budget,start_time,targeting", "limit": "50"}):
            t = aset.get("targeting") or {}
            geo = (t.get("geo_locations") or {}).get("countries")
            print(f"   ADSET {aset['id']} '{aset.get('name')}'")
            print(f"      opt={aset.get('optimization_goal')} bill={aset.get('billing_event')} "
                  f"geo={geo} age={t.get('age_min')}-{t.get('age_max')} "
                  f"locales={t.get('locales')} promoted={aset.get('promoted_object')}")
            for ad in g._get_all(f"{aset['id']}/ads", {
                    "fields": "id,name,creative{id,object_story_id,effective_object_story_id,"
                              "video_id,image_hash,call_to_action_type}", "limit": "50"}):
                cr = ad.get("creative") or {}
                osid = cr.get("effective_object_story_id") or cr.get("object_story_id")
                print(f"      AD '{ad.get('name')}'  osid={osid}  "
                      f"vid={cr.get('video_id')} img={cr.get('image_hash')} "
                      f"cta={cr.get('call_to_action_type')}")
        print()

    print("=" * 80)
    print("DEST — [SG] MTC X SB (act_893025326577600) capabilities")
    print("=" * 80)
    try:
        px = g._get_all(f"{DST}/adspixels", {"fields": "id,name", "limit": "50"})
        for p in px:
            print(f"  pixel {p.get('id')}  {p.get('name')}")
        if not px:
            print("  ⚠ NO pixel on the SG account — need one for COMPLETE_REGISTRATION optimization")
    except Exception as exc:  # noqa: BLE001
        print("  pixel read failed:", exc)
    try:
        info = g.get_object(DST, "name,account_status,currency,timezone_name")
        print(f"  account: {info.get('name')} status={info.get('account_status')} "
              f"currency={info.get('currency')} tz={info.get('timezone_name')}")
    except Exception as exc:  # noqa: BLE001
        print("  account read failed:", exc)
    for edge in ("client_pages", "owned_pages"):
        try:
            pgs = g._get_all(f"{BUSINESS}/{edge}", {"fields": "id,name", "limit": "100"})
            hit = any(str(p.get("id")) == PAGE for p in pgs)
            print(f"  business/{edge}: page {PAGE} present = {hit}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {edge}: {str(exc)[:70]}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
