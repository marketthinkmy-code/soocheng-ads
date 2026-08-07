"""Build a '[SG] STOCKBLOOM | RUNNING | 1-1' campaign + ad set on the SG account
(act_893025326577600) targeting the running-club interest cluster, geo Singapore, with
the verified-advertiser binding. Ad set only (no ads yet — single-image creatives TBD).
Dry-run unless CONFIRM=true.

Also a live test: does SG's FINANCIAL_PRODUCTS_SERVICES special category ALLOW interest
targeting? If create_adset rejects the flexible_spec, SG can only run broad.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")

DST = "act_893025326577600"
PIXEL = "2602956993413536"
DAILY = 10000
CATS = ["FINANCIAL_PRODUCTS_SERVICES"]
SPECIAL_COUNTRY = ["SG"]
REGIONAL = ["SINGAPORE_UNIVERSAL"]
REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
PROMOTED = {"pixel_id": PIXEL, "custom_event_type": "COMPLETE_REGISTRATION"}

# real Meta interest ids resolved via /search?type=adinterest (running-club cluster)
INTERESTS = [
    {"id": "6003198391601", "name": "running club"},
    {"id": "6003397496347", "name": "Running"},
    {"id": "6003424404140", "name": "marathons"},
    {"id": "6004114617224", "name": "Half marathon"},
    {"id": "6003091202415", "name": "Jogging"},
    {"id": "6003343543428", "name": "Trail running"},
    {"id": "6008199007172", "name": "long-distance running"},
    {"id": "6009883959155", "name": "10K run"},
    {"id": "6003351764757", "name": "Triathlons"},
    {"id": "6003516434242", "name": "Ironman Triathlon"},
    {"id": "6003401026143", "name": "Strava"},
    {"id": "6003459401689", "name": "Parkrun"},
    {"id": "6003166470558", "name": "Garmin"},
    {"id": "6003254588288", "name": "ASICS"},
    {"id": "6014885750394", "name": "Hoka One One"},
]
TARGETING = {
    "geo_locations": {"countries": ["SG"]},
    "age_min": 25, "age_max": 65,
    "locales": [20, 21, 22],
    "flexible_spec": [{"interests": INTERESTS}],
    "targeting_automation": {"advantage_audience": 0},   # hard interest targeting
}

CAMP_NAME = "[SG] STOCKBLOOM | RUNNING | 1-1"
ADSET_NAME = "AdSet (RUNNING interests | SG 25+)"


def main() -> None:
    g = graph_client(load_settings())
    print(f"CONFIRM={CONFIRM}  DEST={DST}  geo=SG  daily=RM{DAILY/100:.0f} CBO")
    print(f"interests: {', '.join(i['name'] for i in INTERESTS)}\n")

    # skip if a same-named campaign already exists (idempotent)
    existing = g._get_all(f"{DST}/campaigns", {"fields": "id,name", "limit": "200"})
    dup = [c for c in existing if c.get("name") == CAMP_NAME]
    if dup:
        print(f"campaign already exists: {dup[0]['id']} — nothing to do")
        return

    if not CONFIRM:
        print(f"WOULD CREATE campaign '{CAMP_NAME}' (OUTCOME_SALES · RM{DAILY/100:.0f}/day CBO · {CATS})")
        print(f"WOULD CREATE adset '{ADSET_NAME}' (OFFSITE_CONVERSIONS/COMPLETE_REGISTRATION, "
              f"geo=SG, age 25-65, {len(INTERESTS)} interests, advertiser {REG_IDENTITIES['singapore_universal_payer']})")
        print("   (no ads — single-image creatives decided separately)")
        return

    camp = g.create_campaign(
        DST, name=CAMP_NAME, objective="OUTCOME_SALES", daily_budget=DAILY,
        bid_strategy="LOWEST_COST_WITHOUT_CAP", special_ad_categories=CATS,
        special_ad_category_country=SPECIAL_COUNTRY, status="PAUSED")
    print(f"✓ campaign {camp['id']}")
    aset = g.create_adset(
        DST, name=ADSET_NAME, campaign_id=camp["id"],
        optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
        promoted_object=PROMOTED, targeting=TARGETING,
        regional_regulated_categories=REGIONAL,
        regional_regulation_identities=REG_IDENTITIES, status="PAUSED")
    print(f"✓ adset {aset['id']}  (interest targeting ACCEPTED under financial category)")
    print("\nDONE — campaign + RUNNING ad set live, PAUSED. Add single-image ads next.")


if __name__ == "__main__":
    main()
