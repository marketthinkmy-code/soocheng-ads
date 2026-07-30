# -*- coding: utf-8 -*-
"""Owner-approved (2026-07-30): build ONE 1-1-3 on SG — TOP 1 ad set targeting × TOP 3 ads.

30-day Paid Student List basis:
  TOP 1 ad set  = Travel SG 25+ (12 buyers)  -> targeting copied LIVE from the converting
                  reference ad set (campaign 120248220646980521), not guessed.
  TOP 3 clean ads = freestyle 1 (12) · video 5：trading 早就不是这样了！(8) ·
                  video 5：盖电脑，喂！(8).  video 12 (#2 raw) is ⛔禁跑名单 — excluded.

Each ad reuses the winner's live page POST (object_story_id) so social proof carries over.
Post ids are resolved dynamically from live ads (SG account first, then MY; prefer ACTIVE),
never hardcoded. 1 campaign (CBO RM100/day, OUTCOME_SALES) + 1 ad set (Travel SG interests +
Singapore advertiser binding) + 3 ads — ALL PAUSED; owner activates in Ads Manager.
Idempotent. Dry-run unless CONFIRM=true.
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
REF_TRAVEL_CAMP = "120248220646980521"   # [SG] STOCKBLOOM | TRAVEL | 1-1-3 (7 buyers 30d)
CAMP_NAME = "[SG] STOCKBLOOM | TRAVEL TOP3 | 1-1-3"
ASET_NAME = "AdSet (Travel SG 25+)"
DAILY = 10000                            # RM100/day CBO (cents)

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]


def _norm(s: str) -> str:
    return " ".join((s or "").replace("：", ":").split()).casefold()


# (display/ad name, matcher) — matcher takes the normalized live-ad name
WINNERS = [
    ("freestyle 1",                       lambda n: n == "freestyle 1"),
    ("video 5：trading 早就不是这样了！",   lambda n: "早就不是这样" in n),
    ("video 5：盖电脑，喂！",              lambda n: "盖电脑" in n),
]


def resolve_posts(g) -> dict:
    """{ad_name: post_id} resolved from live ads; prefer SG then MY, ACTIVE over PAUSED."""
    pools = []
    for acct in (SG, MY):
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
                                  0 if acct == SG else 1, post, acct, a.get("name")))
        if not cands:
            raise SystemExit(f"‼️ no live ad found matching «{disp}» — cannot resolve its post id")
        cands.sort()
        _, _, post, acct, src = cands[0]
        posts = {c[2] for c in cands}
        note = f" (⚠️ {len(posts)} distinct posts across variants — took the ACTIVE one)" if len(posts) > 1 else ""
        print(f"  «{disp}»  post={post}  from {acct} ad «{src}» [{'ACTIVE' if cands[0][0]==0 else 'not-active'}]{note}")
        out[disp] = post
    return out


def travel_targeting(g) -> tuple:
    """Copy the converting Travel SG ad set's targeting + promoted_object verbatim."""
    adsets = g._get_all(f"{REF_TRAVEL_CAMP}/adsets",
                        {"fields": "id,name,targeting,promoted_object", "limit": "20"})
    if not adsets:
        raise SystemExit("reference Travel SG campaign has no ad sets")
    ref = adsets[0]
    tgt = ref.get("targeting") or {}
    promo = ref.get("promoted_object") or {}
    ints = []
    for blk in tgt.get("flexible_spec") or []:
        ints += [i.get("name", "?") for i in blk.get("interests", [])]
    print(f"  ref adset {ref['id']} «{ref.get('name')}»  interests={len(ints)}: {', '.join(ints[:6])}…")
    print(f"  promoted_object={promo}")
    if not ints:
        raise SystemExit("‼️ reference Travel ad set returned no interests — aborting")
    return tgt, promo


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    print(f"CONFIRM={CONFIRM}  ·  {CAMP_NAME}  ·  RM{DAILY/100:.0f}/day CBO · PAUSED\n")

    print("== resolve winner post ids ==")
    posts = resolve_posts(g)
    print("\n== copy Travel SG targeting ==")
    tgt, promo = travel_targeting(g)

    existing = g._get_all(f"{SG}/campaigns", {"fields": "id,name", "limit": "500"})
    if any(c.get("name") == CAMP_NAME for c in existing):
        print(f"\n· '{CAMP_NAME}' already exists — skip (idempotent)")
        return

    if not CONFIRM:
        print(f"\nWOULD CREATE campaign '{CAMP_NAME}' (OUTCOME_SALES, RM{DAILY/100:.0f}/day, PAUSED)")
        print(f"WOULD CREATE adset  '{ASET_NAME}'  (Travel SG targeting copied · SG advertiser binding)")
        for disp, post in posts.items():
            print(f"WOULD CREATE ad     «{disp}»  from post {post}  (PAUSED)")
        print("\nDRY-RUN — set CONFIRM=true to build.")
        return

    camp = g.create_campaign(
        SG, name=CAMP_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
        daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
        special_ad_categories=s.meta.special_ad_categories,
        special_ad_category_country=["SG"], status="PAUSED")
    print(f"\n✓ campaign {camp['id']}  {CAMP_NAME}")
    time.sleep(PACE)

    aset = g.create_adset(
        SG, name=ASET_NAME, campaign_id=camp["id"],
        optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
        promoted_object=promo, targeting=tgt, status="PAUSED",
        regional_regulated_categories=REGIONAL,
        regional_regulation_identities=REG_IDENTITIES)
    print(f"✓ adset {aset['id']}  ({ASET_NAME})")
    time.sleep(PACE)

    conv = s.meta.conversion_domain_bare or None
    for disp, post in posts.items():
        spec = {"name": f"SG | {disp}", "object_story_id": post}
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        cr = g.create_adcreative(SG, **spec)
        ad = g.create_ad(SG, name=disp, adset_id=aset["id"],
                         creative={"creative_id": cr["id"]}, status="PAUSED",
                         conversion_domain=conv)
        print(f"   ✓ ad {ad['id']}  «{disp}»")
        time.sleep(PACE)

    print("\nDONE — 1-1-3 built PAUSED; owner reviews + activates in Ads Manager.")


if __name__ == "__main__":
    main()
