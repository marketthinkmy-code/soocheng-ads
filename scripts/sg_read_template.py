"""Read-only: the owner manually built one SG campaign ('[SG] STOCKBLOOM | BROAD | 1-1-3 B')
on act_893025326577600 with the verified advertiser (Siew Lai Yin) attached. Dump its exact
regional_regulation_identities + regulated categories + dsa fields so we can mirror the
advertiser binding onto the API-built clones. No writes.
"""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.settings import load_settings

DST = "act_893025326577600"
WANT = "1-1-3 B"   # substring match on the manually-built template campaign name


def main() -> None:
    g = graph_client(load_settings())

    camps = g._get_all(f"{DST}/campaigns", {
        "fields": "id,name,effective_status,objective,special_ad_categories,"
                  "special_ad_category_country,daily_budget,bid_strategy,buying_type",
        "limit": "200"})
    hit = [c for c in camps if WANT in (c.get("name") or "")]
    print(f"{len(camps)} campaigns on {DST}; {len(hit)} match '{WANT}'\n")
    if not hit:
        print("  template campaign not found — names present:")
        for c in camps:
            print(f"    {c['id']}  {c.get('name')}  [{c.get('effective_status')}]")
        return

    for c in hit:
        print("=" * 80)
        print(f"CAMPAIGN {c['id']}  {c.get('name')}  [{c.get('effective_status')}]")
        print(f"  objective={c.get('objective')} cats={c.get('special_ad_categories')} "
              f"cat_country={c.get('special_ad_category_country')} "
              f"daily={c.get('daily_budget')} bid={c.get('bid_strategy')} buy={c.get('buying_type')}")
        for aset in g._get_all(f"{c['id']}/adsets", {
                "fields": "id,name,effective_status,optimization_goal,billing_event,"
                          "promoted_object,regional_regulated_categories,"
                          "regional_regulation_identities,dsa_beneficiary,dsa_payor,targeting",
                "limit": "50"}):
            print(f"\n  ADSET {aset['id']}  {aset.get('name')}  [{aset.get('effective_status')}]")
            print(f"    opt={aset.get('optimization_goal')} bill={aset.get('billing_event')}")
            print(f"    promoted_object={aset.get('promoted_object')}")
            print(f"    regional_regulated_categories={aset.get('regional_regulated_categories')}")
            print(f"    dsa_beneficiary={aset.get('dsa_beneficiary')!r} "
                  f"dsa_payor={aset.get('dsa_payor')!r}")
            print("    >>> regional_regulation_identities (verbatim) >>>")
            print("    " + json.dumps(aset.get("regional_regulation_identities"),
                                      ensure_ascii=False, indent=2).replace("\n", "\n    "))
            t = aset.get("targeting") or {}
            geo = (t.get("geo_locations") or {}).get("countries")
            print(f"    targeting.geo={geo} age={t.get('age_min')}-{t.get('age_max')} "
                  f"locales={t.get('locales')}")
            for ad in g._get_all(f"{aset['id']}/ads", {
                    "fields": "id,name,effective_status,creative{id,effective_object_story_id,"
                              "object_story_id,call_to_action_type}", "limit": "20"}):
                cr = ad.get("creative") or {}
                print(f"    AD {ad['id']} '{ad.get('name')}' [{ad.get('effective_status')}] "
                      f"osid={cr.get('effective_object_story_id') or cr.get('object_story_id')} "
                      f"cta={cr.get('call_to_action_type')}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
