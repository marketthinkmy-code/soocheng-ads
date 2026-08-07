"""Clone the owner's 5 proven MY campaigns onto the SG account (act_893025326577600),
reusing each ad's object_story_id, targeting Singapore, all PAUSED. Dry-run unless CONFIRM=true.

Singapore delivery requires each ad set to carry the VERIFIED advertiser via
regional_regulation_identities (payer + beneficiary = 'Siew Lai Yin', id 1466824068581066),
read verbatim from the owner's manually-built template campaign
'[SG] STOCKBLOOM | BROAD | 1-1-3 B' (120248197444090521). Free-text dsa_* is NOT used for SG.

The owner already built BROAD B (adset + 1 ad 'freestyle 1'), so we:
  • build the OTHER 4 campaigns fresh (GOLF, TRAVEL, TRAVEL 2, BROAD A) — 3 ads each, and
  • COMPLETE BROAD B by adding its 2 missing ads to the owner's existing ad set.
No duplicate campaigns; everything created PAUSED for owner review.
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
GEO = ["SG"]
SPECIAL_COUNTRY = ["SG"]
REGIONAL = ["SINGAPORE_UNIVERSAL"]
# Verified advertiser (Siew Lai Yin) — verbatim from the owner's template ad set.
REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
AGE_MIN, AGE_MAX = 25, 65
LOCALES = [20, 21, 22]

PROMOTED = {"pixel_id": PIXEL, "custom_event_type": "COMPLETE_REGISTRATION"}
TARGETING = {
    "geo_locations": {"countries": GEO},
    "age_min": AGE_MIN, "age_max": AGE_MAX,
    "locales": LOCALES,
    "targeting_automation": {"advantage_audience": 1},
}

# 4 campaigns to build fresh (BROAD B is owner-built; completed separately below).
CAMPAIGNS = [
    {"name": "[SG] STOCKBLOOM | GOLF PICKBLEBALL | 1-1-3",
     "adset": "AdSet (GOLF PICKLEBALL | SG 25+)",
     "ads": [
         ("freestyle 2", "1001334883061622_122097410667286543"),
         ("video 5：trading 早就不是这样了！", "1001334883061622_122108600481286543"),
         ("video 2: 我只有一个目的", "1001334883061622_122114950617286543"),
     ]},
    {"name": "[SG] STOCKBLOOM | TRAVEL | 1-1-3",
     "adset": "AdSet (TRAVEL SG 25+)",
     "ads": [
         ("video 11：office 突访", "1001334883061622_122109024921286543"),
         ("video 8：做么你 trading 不用看盘的？", "1001334883061622_122108597175286543"),
         ("video 1: 用我的方法，你也可以有将多", "1001334883061622_122097411411286543"),
     ]},
    {"name": "[SG] STOCKBLOOM | TRAVEL | 1-1-3 (2)",
     "adset": "AdSet (TRAVEL SG 25+)",
     "ads": [
         ("video 5: 你没有本钱", "1001334883061622_122097420417286543"),
         ("video 5：盖电脑，喂！", "1001334883061622_1788611461813837"),
         ("video 6：我跟你讲！", "1001334883061622_4377635152552494"),
     ]},
    {"name": "[SG] STOCKBLOOM | BROAD | 1-1-3 A",
     "adset": "AdSet (Broad SG 25+)",
     "ads": [
         ("freestyle: korea", "1001334883061622_122109881127286543"),
         ("video 12：不选 forex 不选黄金", "1001334883061622_122109026109286543"),
         ("Video 12：炒过那么多，累而且不稳定", "1001334883061622_122116264815286543"),
     ]},
]

# BROAD B — owner already built this campaign + ad set (with 'freestyle 1'); add the rest.
BROADB_CAMP_NAME = "[SG] STOCKBLOOM | BROAD | 1-1-3 B"
BROADB_ADS = [
    ("video 2：你敢吗？", "1001334883061622_122109020937286543"),
    ("freestyle 1", "1001334883061622_122097411579286543"),          # already present
    ("video 6：街头突击采访！", "1001334883061622_122108595957286543"),
]

# Fresh-campaign names we may delete as orphans from a prior partial run (never BROAD B).
DELETE_NAMES = {c["name"] for c in CAMPAIGNS} | {
    "STOCKBLOOM | GOLF PICKBLEBALL | 1-1-3", "STOCKBLOOM | TRAVEL | 1-1-3",
    "STOCKBLOOM | TRAVEL | 1-1-3 (2)", "STOCKBLOOM | BROAD | 1-1-3 A",
}


def make_ad(g, s, adset_id, name, osid, url_tags, conv):
    spec = {"name": f"SG | {name}", "object_story_id": osid}
    if url_tags:
        spec["url_tags"] = url_tags
    cr = g.create_adcreative(DST, **spec)
    ad = g.create_ad(DST, name=name, adset_id=adset_id,
                     creative={"creative_id": cr["id"]}, status="PAUSED",
                     conversion_domain=conv)
    return ad["id"], cr["id"]


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    url_tags = s.meta.url_tags or None
    conv = s.meta.conversion_domain_bare or None

    print(f"CONFIRM={CONFIRM}  ({'LIVE — will create' if CONFIRM else 'DRY RUN — prints only'})")
    print(f"DEST={DST}  GEO={GEO}  cat_country={SPECIAL_COUNTRY}  regional={REGIONAL}")
    print(f"regional_regulation_identities={REG_IDENTITIES}")
    print(f"pixel={PIXEL}  daily=RM{DAILY/100:.0f} CBO  url_tags={'set' if url_tags else 'none'}  "
          f"conv={conv}\n")

    existing = g._get_all(f"{DST}/campaigns", {"fields": "id,name", "limit": "200"})

    # preflight: drop orphans of the 4 fresh campaigns (never the owner's BROAD B)
    orphans = [c for c in existing if c.get("name") in DELETE_NAMES]
    for c in orphans:
        if CONFIRM:
            g._request("DELETE", c["id"])
            print(f"PREFLIGHT deleted orphan {c['id']}  {c.get('name')}")
        else:
            print(f"PREFLIGHT would delete {c['id']}  {c.get('name')}")
    if orphans:
        print()

    n_camp = n_ad = 0
    for c in CAMPAIGNS:
        print(f"CAMPAIGN  {c['name']}  (OUTCOME_SALES · RM{DAILY/100:.0f}/day CBO · {CATS})")
        print(f"   ADSET  {c['adset']}  geo={GEO} · advertiser id "
              f"{REG_IDENTITIES['singapore_universal_payer']}")
        for name, osid in c["ads"]:
            print(f"      AD  {name}   (post {osid})")
        if not CONFIRM:
            print("   WOULD CREATE campaign + adset + 3 ads (PAUSED)\n")
            n_camp += 1
            n_ad += len(c["ads"])
            continue
        camp = g.create_campaign(
            DST, name=c["name"], objective="OUTCOME_SALES", daily_budget=DAILY,
            bid_strategy="LOWEST_COST_WITHOUT_CAP", special_ad_categories=CATS,
            special_ad_category_country=SPECIAL_COUNTRY, status="PAUSED")
        aset = g.create_adset(
            DST, name=c["adset"], campaign_id=camp["id"],
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            promoted_object=PROMOTED, targeting=TARGETING,
            regional_regulated_categories=REGIONAL,
            regional_regulation_identities=REG_IDENTITIES, status="PAUSED")
        print(f"   ✓ campaign {camp['id']} · adset {aset['id']}")
        n_camp += 1
        for name, osid in c["ads"]:
            ad_id, cid = make_ad(g, s, aset["id"], name, osid, url_tags, conv)
            print(f"      ✓ AD {ad_id}  {name}")
            n_ad += 1
        print()

    # BROAD B — complete the owner's existing campaign by adding any missing ads
    print(f"BROAD B (owner-built) — {BROADB_CAMP_NAME}")
    bcamps = [c for c in existing if c.get("name") == BROADB_CAMP_NAME]
    if not bcamps:
        print("   ⚠ owner's BROAD B campaign not found — skipping completion")
    else:
        bcamp = bcamps[0]
        bsets = g._get_all(f"{bcamp['id']}/adsets", {"fields": "id,name", "limit": "5"})
        if not bsets:
            print("   ⚠ no ad set under BROAD B — skipping")
        else:
            basid = bsets[0]["id"]
            have = set()
            for ad in g._get_all(f"{basid}/ads", {
                    "fields": "creative{effective_object_story_id,object_story_id}",
                    "limit": "50"}):
                cr = ad.get("creative") or {}
                have.add(cr.get("effective_object_story_id") or cr.get("object_story_id"))
            print(f"   adset {basid} already has {len(have)} ad(s)")
            for name, osid in BROADB_ADS:
                if osid in have:
                    print(f"      · keep existing: {name}")
                    continue
                if not CONFIRM:
                    print(f"      WOULD ADD  {name}  (post {osid})")
                    n_ad += 1
                    continue
                ad_id, cid = make_ad(g, s, basid, name, osid, url_tags, conv)
                print(f"      ✓ ADDED AD {ad_id}  {name}")
                n_ad += 1

    verb = "created" if CONFIRM else "planned"
    print(f"\nDONE — {verb} {n_camp} new campaigns + completed BROAD B · {n_ad} ads total "
          f"on {DST} (all PAUSED).")


if __name__ == "__main__":
    main()
