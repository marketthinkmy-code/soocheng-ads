"""Clone the owner's 5 ACTIVE MY campaigns (act_759339046918885) onto the SG account
(act_893025326577600), 1:1 structure, reusing each ad's object_story_id so the exact
same page posts (with their likes/comments/shares) run on SG. Everything PAUSED — the
owner reviews + activates in Ads Manager. Dry-run unless CONFIRM=true.

Resolved facts (read-only probes, 2026-07-13):
  • SG token access: user_tasks = DRAFT/ANALYZE/ADVERTISE/MANAGE  -> can create. ✓
  • SG account: [SG] MTC X SB, status ACTIVE, MYR, HAS_VALID_PAYMENT_METHODS, empty. ✓
  • SG pixel 2602956993413536 (same one the MY adsets already optimize on). ✓
  • Page 1001334883061622 is a client_page on the SG business -> post reuse works. ✓

GEO decision: targeting SINGAPORE, because this is the [SG] account and the SG market.
  To ship a verbatim MY-targeted copy instead, set GEO = ["MY"] and re-run.
Everything else (budget RM100/day CBO, bid, financial category, opt/event, age, locales)
is copied verbatim from the source.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")

DST = "act_893025326577600"                 # [SG] MTC X SB (destination)
PIXEL = "2602956993413536"                  # STOCK BLOOM X MTC (on the SG account)
DAILY = 10000                               # RM100/day CBO — verbatim from source
CATS = ["FINANCIAL_PRODUCTS_SERVICES"]
GEO = ["SG"]                                # <-- flip to ["MY"] for a verbatim MY copy
# Financial special-ad-category REQUIRES the declared country to match the audience geo,
# else Meta rejects with (#2909034). Keep this in lockstep with GEO.
SPECIAL_COUNTRY = ["SG"]
# Singapore law requires every ad set targeting SG to declare a regional regulated
# category; the general value is SINGAPORE_UNIVERSAL. Only applies when GEO includes SG.
REGIONAL = ["SINGAPORE_UNIVERSAL"] if "SG" in GEO else None
AGE_MIN, AGE_MAX = 25, 65
LOCALES = [20, 21, 22]                       # verbatim from source adsets

PROMOTED = {"pixel_id": PIXEL, "custom_event_type": "COMPLETE_REGISTRATION"}
TARGETING = {
    "geo_locations": {"countries": GEO},
    "age_min": AGE_MIN, "age_max": AGE_MAX,
    "locales": LOCALES,
    "targeting_automation": {"advantage_audience": 1},
}

# Source structure captured from the read-only resolve (each ad -> its reusable post id).
CAMPAIGNS = [
    {"name": "STOCKBLOOM | GOLF PICKBLEBALL | 1-1-3",
     "adset": "AdSet (GOLF PICKLEBALL | SG 25+)",
     "ads": [
         ("freestyle 2", "1001334883061622_122097410667286543"),
         ("video 5：trading 早就不是这样了！", "1001334883061622_122108600481286543"),
         ("video 2: 我只有一个目的", "1001334883061622_122114950617286543"),
     ]},
    {"name": "STOCKBLOOM | TRAVEL | 1-1-3",
     "adset": "AdSet (TRAVEL SG 25+)",
     "ads": [
         ("video 11：office 突访", "1001334883061622_122109024921286543"),
         ("video 8：做么你 trading 不用看盘的？", "1001334883061622_122108597175286543"),
         ("video 1: 用我的方法，你也可以有将多", "1001334883061622_122097411411286543"),
     ]},
    {"name": "STOCKBLOOM | TRAVEL | 1-1-3 (2)",
     "adset": "AdSet (TRAVEL SG 25+)",
     "ads": [
         ("video 5: 你没有本钱", "1001334883061622_122097420417286543"),
         ("video 5：盖电脑，喂！", "1001334883061622_1788611461813837"),
         ("video 6：我跟你讲！", "1001334883061622_4377635152552494"),
     ]},
    {"name": "STOCKBLOOM | BROAD | 1-1-3 A",
     "adset": "AdSet (Broad SG 25+)",
     "ads": [
         ("freestyle: korea", "1001334883061622_122109881127286543"),
         ("video 12：不选 forex 不选黄金", "1001334883061622_122109026109286543"),
         ("Video 12：炒过那么多，累而且不稳定", "1001334883061622_122116264815286543"),
     ]},
    {"name": "STOCKBLOOM | BROAD | 1-1-3 B",
     "adset": "AdSet (Broad SG 25+)",
     "ads": [
         ("video 2：你敢吗？", "1001334883061622_122109020937286543"),
         ("freestyle 1", "1001334883061622_122097411579286543"),
         ("video 6：街头突击采访！", "1001334883061622_122108595957286543"),
     ]},
]


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    url_tags = s.meta.url_tags or None
    conv = s.meta.conversion_domain_bare or None

    print(f"CONFIRM={CONFIRM}  ({'LIVE — will create' if CONFIRM else 'DRY RUN — prints only'})")
    print(f"DEST={DST}  GEO={GEO}  special_ad_category_country={SPECIAL_COUNTRY}  "
          f"regional={REGIONAL}  pixel={PIXEL}  daily=RM{DAILY/100:.0f} CBO  cats={CATS}")
    print(f"url_tags={'set' if url_tags else 'none'}  conversion_domain={conv}\n")

    # Preflight: remove any earlier orphan of these exact campaigns (safe — SG account was
    # confirmed empty). Keeps re-runs idempotent after a partial failure.
    target_names = {c["name"] for c in CAMPAIGNS}
    existing = g._get_all(f"{DST}/campaigns", {"fields": "id,name", "limit": "200"})
    orphans = [c for c in existing if c.get("name") in target_names]
    if orphans:
        print(f"PREFLIGHT: {len(orphans)} pre-existing campaign(s) with my target names:")
        for c in orphans:
            if CONFIRM:
                g._request("DELETE", c["id"])
                print(f"   deleted orphan {c['id']}  {c.get('name')}")
            else:
                print(f"   WOULD DELETE {c['id']}  {c.get('name')}")
        print()

    n_camp = n_ad = 0
    for c in CAMPAIGNS:
        print(f"CAMPAIGN  {c['name']}")
        print(f"   OUTCOME_SALES · RM{DAILY/100:.0f}/day CBO · LOWEST_COST_WITHOUT_CAP · {CATS}")
        print(f"   ADSET  {c['adset']}  (OFFSITE_CONVERSIONS/COMPLETE_REGISTRATION, "
              f"geo={GEO}, age {AGE_MIN}-{AGE_MAX}, locales={LOCALES}, Advantage+ audience)")
        if not CONFIRM:
            for name, osid in c["ads"]:
                print(f"      AD  {name}   (reuse post {osid})")
            print("   WOULD CREATE campaign + adset + 3 ads (all PAUSED)\n")
            n_camp += 1
            n_ad += len(c["ads"])
            continue

        camp = g.create_campaign(
            DST, name=c["name"], objective="OUTCOME_SALES", daily_budget=DAILY,
            bid_strategy="LOWEST_COST_WITHOUT_CAP", special_ad_categories=CATS,
            special_ad_category_country=SPECIAL_COUNTRY, status="PAUSED")
        cid = camp["id"]
        adset_kwargs = dict(
            name=c["adset"], campaign_id=cid,
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            promoted_object=PROMOTED, targeting=TARGETING, status="PAUSED")
        if REGIONAL:
            adset_kwargs["regional_regulated_categories"] = REGIONAL
        aset = g.create_adset(DST, **adset_kwargs)
        asid = aset["id"]
        print(f"   ✓ campaign {cid} · adset {asid}")
        n_camp += 1
        for name, osid in c["ads"]:
            spec = {"name": f"SG | {name}", "object_story_id": osid}
            if url_tags:
                spec["url_tags"] = url_tags
            cr = g.create_adcreative(DST, **spec)
            ad = g.create_ad(DST, name=name, adset_id=asid,
                             creative={"creative_id": cr["id"]}, status="PAUSED",
                             conversion_domain=conv)
            print(f"      ✓ AD {ad['id']}  {name}  (creative {cr['id']} ← post {osid})")
            n_ad += 1
        print()

    verb = "created" if CONFIRM else "planned"
    print(f"DONE — {verb} {n_camp} campaigns · {n_ad} ads on {DST} (all PAUSED).")


if __name__ == "__main__":
    main()
