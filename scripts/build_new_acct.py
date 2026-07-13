"""Build the first wave on the NEW account act_759339046918885 (MTC X SB 3.0):
2 × 1-1-3 campaigns, 6 proven posts reused via object_story_id (keeps each post's
likes/comments/shares), scheduled to start 2026-07-14 00:00 MYT, RM100/day CBO each,
MY Broad 25+ Chinese. EVERYTHING PAUSED — owner reviews + activates. Dry-run unless
CONFIRM=true. Each ad is created independently; a post that can't be reused is reported,
not fatal.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")

ACCT = "act_759339046918885"
PAGE = "1001334883061622"
IG = "17841480427751602"
PIXEL = "24482357924768693"                 # "ENG options pixel" on the new account
START = "2026-07-14T00:00:00+08:00"         # 12am 14 Jul 2026 MYT
DAILY = 10000                               # RM100/day (cents) per campaign, CBO
CATS = ["FINANCIAL_PRODUCTS_SERVICES"]
URL_TAGS = ("utm_source={{adset.name}}&utm_medium={{placement}}"
            "&utm_campaign={{campaign.name}}&utm_content={{ad.name}}")

TARGETING = {
    "geo_locations": {"countries": ["MY"]},
    "age_min": 25, "age_max": 65,
    "locales": [1004],                       # Chinese (All)
    "targeting_automation": {"advantage_audience": 1},
}
PROMOTED = {"pixel_id": PIXEL, "custom_event_type": "COMPLETE_REGISTRATION"}

# (campaign label, [(ad name = historical UTM name, object_story_id), ...])
CAMPAIGNS = [
    ("STOCKBLOOM | 1-1-3 A", [
        ("freestyle 1", "1001334883061622_122097411579286543"),
        ("video 6：街头突击采访！", "1001334883061622_122108595957286543"),
        ("video 2：你敢吗？", "1001334883061622_122109020937286543"),
    ]),
    ("STOCKBLOOM | 1-1-3 B", [
        ("freestyle: korea", "1001334883061622_122109881127286543"),
        ("video 12：不选 forex 不选黄金", "1001334883061622_122109026109286543"),
        ("Video 12：炒过那么多，累而且不稳定", "1001334883061622_122116264815286543"),
    ]),
]


def main() -> None:
    g = graph_client(load_settings())
    print(f"CONFIRM={CONFIRM}  acct={ACCT}  pixel={PIXEL}")
    print(f"start={START}  budget=RM{DAILY/100:.0f}/day per campaign  targeting=MY 25-65 Chinese\n")
    made = []
    for camp_name, ads in CAMPAIGNS:
        print(f"══ {camp_name} ══")
        if not CONFIRM:
            print(f"  WOULD create campaign OUTCOME_SALES · CBO RM{DAILY/100:.0f}/day · PAUSED")
            print(f"  WOULD create ad set OFFSITE_CONVERSIONS · pixel {PIXEL} · start {START} · PAUSED")
            for nm, pid in ads:
                print(f"    WOULD create ad  '{nm}'  ← post {pid}")
            print()
            continue
        camp = g.create_campaign(
            ACCT, name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
            status="PAUSED", special_ad_categories=CATS, daily_budget=DAILY,
            bid_strategy="LOWEST_COST_WITHOUT_CAP")
        cid = camp["id"]
        print(f"  ✅ campaign {cid}")
        aset = g.create_adset(
            ACCT, campaign_id=cid, name=f"{camp_name} | AdSet (Broad MY 25+)",
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            promoted_object=PROMOTED, targeting=TARGETING, start_time=START, status="PAUSED")
        aid = aset["id"]
        print(f"  ✅ ad set   {aid}")
        for nm, pid in ads:
            try:
                spec = {"name": f"{camp_name} | {nm}", "object_story_id": pid,
                        "url_tags": URL_TAGS}
                if IG:
                    spec["instagram_user_id"] = IG
                cr = g.create_adcreative(ACCT, **spec)
                ad = g.create_ad(ACCT, name=nm, adset_id=aid,
                                 creative={"creative_id": cr["id"]}, status="PAUSED")
                print(f"    ✅ ad {ad['id']}  '{nm}'  (creative {cr['id']})")
                made.append((camp_name, nm, ad["id"]))
            except Exception as exc:  # noqa: BLE001
                print(f"    ❌ '{nm}'  post {pid} — {str(exc)[:180]}")
        print()
    if CONFIRM:
        print(f"SUMMARY: created {len(made)} ad(s), all PAUSED. Review + activate in Ads Manager.")
    print("DONE.")


if __name__ == "__main__":
    main()
