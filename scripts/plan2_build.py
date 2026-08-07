"""Build the 6 interest campaigns the owner approved ("A"):

  3 targeting groups — LUXURY GOODS · BUSINESS OWNER · INVESTMENT
  × 2 accounts — MTC X SB 3.0 (act_759339046918885, geo MY) and SG (act_893025326577600, geo SG)

Each is 1-1-3 (campaign + one interest ad set + 3 ads): OUTCOME_SALES, CBO RM100/day,
optimize COMPLETE_REGISTRATION, all PAUSED, scheduled to START 2026-07-16 00:00 GMT+8
(owner activates in Ads Manager — option A).

Ads are today+yesterday's (14-15 Jul) top-3-by-results, split per market — MY ad sets carry
the MY winners, SG ad sets the SG winners (video 1：用我的方法 kept per owner). Reused by
existing post id so social proof carries over.

SG ad sets get the Singapore verified-advertiser binding (regional_regulation_identities +
regional_regulated_categories); MY ad sets do not (Malaysia doesn't require it).

BUSINESS OWNER layers behaviors + job titles on top of interests. Those demographic targets
CAN be blocked under the FINANCIAL_PRODUCTS_SERVICES special category, so that ad set falls
back to interests-only if Meta rejects the fuller spec.

Idempotent (skips a campaign whose name already exists). Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")

PIXEL = "2602956993413536"
DAILY = 10000                                   # RM100/day CBO (cents)
START_TIME = "2026-07-16T00:00:00+0800"         # 16 Jul 2026 12:00am GMT+8
CATS = ["FINANCIAL_PRODUCTS_SERVICES"]
PROMOTED = {"pixel_id": PIXEL, "custom_event_type": "COMPLETE_REGISTRATION"}
LOCALES = [20, 21, 22]
PACE = 2.5                                       # seconds between writes (rate-limit hygiene)
CAMP_GAP = 20.0                                  # seconds between campaigns on one account

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

# ── targeting groups — stable Meta taxonomy ids (resolved + owner-approved) ──
LUXURY_INT = [
    {"id": "6007828099136", "name": "Luxury goods"},
    {"id": "6002893385022", "name": "Luxury watches"},
    {"id": "6003587678073", "name": "Rolex"},
    {"id": "6003266225248", "name": "Jewellery"},
    {"id": "6003715005316", "name": "Luxury yacht"},
    {"id": "6003484864669", "name": "Wealth management"},
    {"id": "6003102546240", "name": "Private banking"},
]
INVEST_INT = [
    {"id": "6003388314512", "name": "Investment"},
    {"id": "6003293787730", "name": "Investment management"},
    {"id": "6003349860951", "name": "Stock market"},
    {"id": "6003104558317", "name": "Day trading"},
    {"id": "6003055476185", "name": "Trading strategy"},
    {"id": "6003003472382", "name": "Electronic trading platform"},  # = trading software
    {"id": "6003347800581", "name": "Foreign exchange market"},
    {"id": "6003143720966", "name": "Personal finance"},
]
BIZ_INT = [
    {"id": "6003371567474", "name": "Entrepreneurship"},
    {"id": "6003325004380", "name": "Start-up company"},
]
BIZ_BEH = [
    {"id": "6002714898572", "name": "Small business owners"},
]
BIZ_WORK = [
    {"id": "103113219728224", "name": "Chief Executive Officer"},
    {"id": "849873341726582", "name": "Founder"},
    {"id": "110722838955052", "name": "Owner"},
    {"id": "874842615892965", "name": "Managing Director"},
]

GROUPS = [
    {"key": "LUXURY GOODS",
     "flex": [{"interests": LUXURY_INT}],
     "flex_fallback": [{"interests": LUXURY_INT}]},
    {"key": "BUSINESS OWNER",
     "flex": [{"interests": BIZ_INT, "behaviors": BIZ_BEH, "work_positions": BIZ_WORK}],
     "flex_fallback": [{"interests": BIZ_INT}]},
    {"key": "INVESTMENT",
     "flex": [{"interests": INVEST_INT}],
     "flex_fallback": [{"interests": INVEST_INT}]},
]

ACCTS = [
    {"label": "MY", "acct": "act_759339046918885", "geo": "MY",
     "special_country": ["MY"], "sg": False, "prefix": "STOCKBLOOM",
     "ads": [  # today+yesterday MY top-3 by results
        ("video 12：不选 forex 不选黄金", "1001334883061622_122109026109286543"),
        ("video 2：你敢吗？",             "1001334883061622_122109020937286543"),
        ("你没有本钱",                    "1001334883061622_122097420417286543"),
     ]},
    {"label": "SG", "acct": "act_893025326577600", "geo": "SG",
     "special_country": ["SG"], "sg": True, "prefix": "[SG] STOCKBLOOM",
     "ads": [  # today+yesterday SG top-3 by results (用我的方法 kept per owner)
        ("trading 早就不是这样了",        "1001334883061622_122108600481286543"),
        ("freestyle 1",                  "1001334883061622_122097411579286543"),
        ("video 1：用我的方法",           "1001334883061622_122097411411286543"),
     ]},
]


def targeting_for(geo, flex):
    return {
        "geo_locations": {"countries": [geo]},
        "age_min": 25, "age_max": 65,
        "locales": LOCALES,
        "flexible_spec": flex,
        "targeting_automation": {"advantage_audience": 0},   # hard interest targeting
    }


def build_one(g, s, ac, grp):
    """Create one 1-1-3 campaign for account `ac` + targeting group `grp`. Idempotent."""
    acct = ac["acct"]
    camp_name = f"{ac['prefix']} | {grp['key']} | 1-1-3"
    aset_name = f"AdSet ({grp['key']} interests | {ac['label']} 25+)"

    existing = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "400"})
    if any(c.get("name") == camp_name for c in existing):
        print(f"  · '{camp_name}' already exists — skip")
        return

    if not CONFIRM:
        tgt_desc = "interests"
        if grp["key"] == "BUSINESS OWNER":
            tgt_desc = "interests + behaviors + job titles (fallback: interests-only)"
        print(f"  WOULD CREATE '{camp_name}'  RM{DAILY/100:.0f}/day CBO OUTCOME_SALES PAUSED")
        print(f"     adset '{aset_name}'  geo={ac['geo']} 25-65 · {tgt_desc} · start {START_TIME}"
              + ("  · SG advertiser binding" if ac["sg"] else ""))
        for nm, osid in ac["ads"]:
            print(f"       ad  {nm}   (post {osid})")
        return

    camp = g.create_campaign(
        acct, name=camp_name, objective="OUTCOME_SALES", daily_budget=DAILY,
        bid_strategy="LOWEST_COST_WITHOUT_CAP", special_ad_categories=CATS,
        special_ad_category_country=ac["special_country"], status="PAUSED")
    print(f"  ✓ campaign {camp['id']}  {camp_name}")
    time.sleep(PACE)

    aset_kwargs = dict(
        name=aset_name, campaign_id=camp["id"],
        optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
        promoted_object=PROMOTED, start_time=START_TIME, status="PAUSED")
    if ac["sg"]:
        aset_kwargs.update(regional_regulated_categories=REGIONAL,
                           regional_regulation_identities=REG_IDENTITIES)

    try:
        aset = g.create_adset(acct, targeting=targeting_for(ac["geo"], grp["flex"]),
                              **aset_kwargs)
        print(f"  ✓ adset {aset['id']}  ({grp['key']} full spec)")
    except Exception as exc:  # noqa: BLE001 — Business-Owner demographics may be blocked
        if grp["flex"] == grp["flex_fallback"]:
            raise
        print(f"  ! full targeting rejected ({str(exc)[:90]}) — retry interests-only")
        time.sleep(PACE)
        aset = g.create_adset(acct, targeting=targeting_for(ac["geo"], grp["flex_fallback"]),
                              **aset_kwargs)
        print(f"  ✓ adset {aset['id']}  ({grp['key']} interests-only fallback)")
    time.sleep(PACE)

    url_tags = s.meta.url_tags or None
    conv = s.meta.conversion_domain_bare or None
    for nm, osid in ac["ads"]:
        spec = {"name": f"{ac['label']} | {nm}", "object_story_id": osid}
        if url_tags:
            spec["url_tags"] = url_tags
        cr = g.create_adcreative(acct, **spec)
        ad = g.create_ad(acct, name=nm, adset_id=aset["id"],
                         creative={"creative_id": cr["id"]}, status="PAUSED",
                         conversion_domain=conv)
        print(f"       ✓ ad {ad['id']}  {nm}")
        time.sleep(PACE)


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    print(f"CONFIRM={CONFIRM}  ·  6 campaigns (3 groups × MY+SG)  ·  RM{DAILY/100:.0f}/day CBO  "
          f"·  start {START_TIME}  ·  PAUSED\n")
    for ac in ACCTS:
        print(f"══ {ac['label']}  {ac['acct']}  geo={ac['geo']}"
              + ("  (SG binding)" if ac["sg"] else "") + " ══")
        for i, grp in enumerate(GROUPS):
            build_one(g, s, ac, grp)
            if CONFIRM and i < len(GROUPS) - 1:
                time.sleep(CAMP_GAP)
        print()
    print("DONE — 6 campaigns built PAUSED; owner activates in Ads Manager."
          if CONFIRM else "DRY-RUN — set CONFIRM=true to build.")


if __name__ == "__main__":
    main()
