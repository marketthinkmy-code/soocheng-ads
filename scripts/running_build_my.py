"""Build the same RUNNING interest campaign on MTC X SB 3.0 (act_759339046918885, MY):
campaign + ad set (running-club interests, geo MALAYSIA) + the 3 best-CPL currently-running
ads (reused by post id). PAUSED. No SG advertiser binding (that's Singapore-only).
Idempotent (skips if the campaign already exists). Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")

ACCT = "act_759339046918885"                 # MTC X SB 3.0 (MY)
PIXEL = "2602956993413536"                   # pixel the 3.0 campaigns actually optimize on
DAILY = 10000
CATS = ["FINANCIAL_PRODUCTS_SERVICES"]
SPECIAL_COUNTRY = ["MY"]                      # match geo (else #2909034)
PROMOTED = {"pixel_id": PIXEL, "custom_event_type": "COMPLETE_REGISTRATION"}

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
    "geo_locations": {"countries": ["MY"]},
    "age_min": 25, "age_max": 65,
    "locales": [20, 21, 22],
    "flexible_spec": [{"interests": INTERESTS}],
    "targeting_automation": {"advantage_audience": 0},
}

CAMP_NAME = "STOCKBLOOM | RUNNING | 1-1"
ADSET_NAME = "AdSet (RUNNING interests | MY 25+)"
ADS = [
    ("video 12：不选 forex 不选黄金", "1001334883061622_122109026109286543"),  # CPL15.7 · 4 reg
    ("video 2：你敢吗？", "1001334883061622_122109020937286543"),               # CPL13.5 · 3 reg
    ("freestyle 1", "1001334883061622_122097411579286543"),                    # CPL12.2 · 3 reg
]


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    url_tags = s.meta.url_tags or None
    conv = s.meta.conversion_domain_bare or None
    print(f"CONFIRM={CONFIRM}  ACCT={ACCT}  geo=MY  pixel={PIXEL}  daily=RM{DAILY/100:.0f} CBO")
    print(f"interests: {', '.join(i['name'] for i in INTERESTS)}\n")

    existing = g._get_all(f"{ACCT}/campaigns", {"fields": "id,name", "limit": "300"})
    dup = [c for c in existing if c.get("name") == CAMP_NAME]
    if dup:
        print(f"campaign already exists: {dup[0]['id']} — nothing to do")
        return

    if not CONFIRM:
        print(f"WOULD CREATE campaign '{CAMP_NAME}' + adset '{ADSET_NAME}' "
              f"({len(INTERESTS)} interests, geo MY) + {len(ADS)} ads (all PAUSED):")
        for name, osid in ADS:
            print(f"   AD {name}  (post {osid})")
        return

    camp = g.create_campaign(
        ACCT, name=CAMP_NAME, objective="OUTCOME_SALES", daily_budget=DAILY,
        bid_strategy="LOWEST_COST_WITHOUT_CAP", special_ad_categories=CATS,
        special_ad_category_country=SPECIAL_COUNTRY, status="PAUSED")
    print(f"✓ campaign {camp['id']}")
    aset = g.create_adset(
        ACCT, name=ADSET_NAME, campaign_id=camp["id"],
        optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
        promoted_object=PROMOTED, targeting=TARGETING, status="PAUSED")
    print(f"✓ adset {aset['id']}  (interest targeting)")
    for name, osid in ADS:
        spec = {"name": f"MY | {name}", "object_story_id": osid}
        if url_tags:
            spec["url_tags"] = url_tags
        cr = g.create_adcreative(ACCT, **spec)
        ad = g.create_ad(ACCT, name=name, adset_id=aset["id"],
                         creative={"creative_id": cr["id"]}, status="PAUSED",
                         conversion_domain=conv)
        print(f"   ✓ AD {ad['id']}  {name}")
    print("\nDONE — RUNNING campaign + 3 ads on 3.0 (MY), all PAUSED.")


if __name__ == "__main__":
    main()
