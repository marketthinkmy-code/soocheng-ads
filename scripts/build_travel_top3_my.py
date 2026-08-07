# -*- coding: utf-8 -*-
"""Owner-approved (2026-07-30): the MY twin of the SG TRAVEL TOP3 1-1-3.

Same 3 winner posts (freestyle 1 · video 12 炒过那么多 · video 5 trading 早就不是这样了),
targeting copied LIVE from the best-CPA converting MY Travel ad set (campaign
120247524817830575, CPA≈RM263). 1 CBO campaign RM100/day OUTCOME_SALES + 1 ad set + 3 ads,
ALL PAUSED — owner activates. video 12 re-enters Meta review here too (owner accepted the
strike risk on 2026-07-30). Idempotent. Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5

SG = "act_893025326577600"
MY = "act_759339046918885"
REF_TRAVEL_CAMP = "120247524817830575"   # STOCKBLOOM | TRAVEL | 1-1-3 (MY, CPA≈RM263)
CAMP_NAME = "STOCKBLOOM | TRAVEL TOP3 | 1-1-3"
ASET_NAME = "AdSet (Travel MY 25+)"
DAILY = 10000                            # RM100/day CBO (cents)


def _norm(s: str) -> str:
    return " ".join((s or "").replace("：", ":").split()).casefold()


# NB: "炒过那么多" pins the banned-list video 12 — there is a DIFFERENT clean video 12
# (不选 forex 不选黄金); never match on the "video 12" prefix alone.
WINNERS = [
    ("freestyle 1",                        lambda n: n == "freestyle 1"),
    ("video 12：炒过那么多，累而且不稳定",   lambda n: "炒过那么多" in n),
    ("video 5：trading 早就不是这样了！",    lambda n: "早就不是这样" in n),
]


def resolve_posts(g) -> dict:
    """{ad_name: post_id} from live ads; prefer MY-account instances, ACTIVE over others."""
    pools = []
    for acct in (MY, SG):
        ads = g._get_all(f"{acct}/ads",
                         {"fields": "name,effective_status,creative{effective_object_story_id,object_story_id}",
                          "limit": "200"})
        pools.append((acct, ads))
    out = {}
    for disp, match in WINNERS:
        cands = []
        for acct, ads in pools:
            for a in ads:
                if not match(_norm(a.get("name") or "")):
                    continue
                cr = a.get("creative") or {}
                post = cr.get("effective_object_story_id") or cr.get("object_story_id")
                if post:
                    cands.append((0 if a.get("effective_status") == "ACTIVE" else 1,
                                  0 if acct == MY else 1, post, acct, a.get("name")))
        if not cands:
            raise SystemExit(f"‼️ no live ad found matching «{disp}» — cannot resolve its post id")
        cands.sort()
        _, _, post, acct, src = cands[0]
        print(f"  «{disp}»  post={post}  from {acct} ad «{src}»")
        out[disp] = post
    return out


def travel_targeting(g) -> tuple:
    adsets = g._get_all(f"{REF_TRAVEL_CAMP}/adsets",
                        {"fields": "id,name,targeting,promoted_object", "limit": "20"})
    if not adsets:
        raise SystemExit("reference MY Travel campaign has no ad sets")
    ref = adsets[0]
    tgt = ref.get("targeting") or {}
    promo = ref.get("promoted_object") or {}
    ints = []
    for blk in tgt.get("flexible_spec") or []:
        ints += [i.get("name", "?") for i in blk.get("interests", [])]
    geo = (tgt.get("geo_locations") or {}).get("countries")
    print(f"  ref adset {ref['id']} «{ref.get('name')}»  geo={geo}  interests={len(ints)}: {', '.join(ints[:6])}…")
    print(f"  promoted_object={promo}")
    if not ints:
        raise SystemExit("‼️ reference MY Travel ad set returned no interests — aborting")
    if geo != ["MY"]:
        raise SystemExit(f"‼️ reference geo is {geo}, expected ['MY'] — wrong reference ad set")
    return tgt, promo


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    print(f"CONFIRM={CONFIRM}  ·  {CAMP_NAME}  ·  RM{DAILY/100:.0f}/day CBO · PAUSED (MY)\n")

    print("== resolve winner post ids ==")
    posts = resolve_posts(g)
    print("\n== copy Travel MY targeting ==")
    tgt, promo = travel_targeting(g)

    existing = g._get_all(f"{MY}/campaigns", {"fields": "id,name", "limit": "500"})
    if any(c.get("name") == CAMP_NAME for c in existing):
        print(f"\n· '{CAMP_NAME}' already exists — skip (idempotent)")
        return

    if not CONFIRM:
        print(f"\nWOULD CREATE campaign '{CAMP_NAME}' (OUTCOME_SALES, RM{DAILY/100:.0f}/day, PAUSED)")
        print(f"WOULD CREATE adset  '{ASET_NAME}'  (Travel MY targeting copied)")
        for disp, post in posts.items():
            print(f"WOULD CREATE ad     «{disp}»  from post {post}  (PAUSED)")
        print("\nDRY-RUN — set CONFIRM=true to build.")
        return

    camp = g.create_campaign(
        MY, name=CAMP_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
        daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
        special_ad_categories=s.meta.special_ad_categories,
        special_ad_category_country=["MY"], status="PAUSED")
    print(f"\n✓ campaign {camp['id']}  {CAMP_NAME}")
    time.sleep(PACE)

    aset = g.create_adset(
        MY, name=ASET_NAME, campaign_id=camp["id"],
        optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
        promoted_object=promo, targeting=tgt, status="PAUSED")
    print(f"✓ adset {aset['id']}  ({ASET_NAME})")
    time.sleep(PACE)

    conv = s.meta.conversion_domain_bare or None
    for disp, post in posts.items():
        spec = {"name": f"MY | {disp}", "object_story_id": post}
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        cr = g.create_adcreative(MY, **spec)
        ad = g.create_ad(MY, name=disp, adset_id=aset["id"],
                         creative={"creative_id": cr["id"]}, status="PAUSED",
                         conversion_domain=conv)
        print(f"   ✓ ad {ad['id']}  «{disp}»")
        time.sleep(PACE)

    print("\nDONE — MY 1-1-3 built PAUSED; owner reviews + activates in Ads Manager.")


if __name__ == "__main__":
    main()
