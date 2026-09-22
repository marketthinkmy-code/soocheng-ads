# -*- coding: utf-8 -*-
"""Owner 2026-09-22「rm100 就好。建」— the Andromeda pool campaigns, additive budget
(no existing chain touched):

  «STOCKBLOOM | ANDRO POOL 30+ | 0922»        (MY)  CBO RM100/day
  «[SG] STOCKBLOOM | ANDRO POOL 30+ | 0922»   (SG)  CBO RM100/day

Each: 1 CBO campaign (ACTIVE, special=[]) + 1 Broad Advantage+ ad set (PAUSED
gate — owner reviews, may edit the budget, and activates himself) + 7-8 ads
REUSING already-approved winner posts (object_story_id — zero re-review; the
caption rides with the post, so image↔copy pairing is inherited from the live
ads). Targeting: Broad, Advantage+ ON, age_range [30,65] suggestion (CLAUDE.md
targeting 硬规则), locales from config; SG ad set carries the Singapore
beneficiary/payer declaration. Idempotent at (campaign name, ad name).
Dry-run unless CONFIRM=true."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 5.0
DAILY = 10000                      # RM100/day CBO (owner:「rm100 就好」)
N = cpa.norm

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

# (pool ad name, source ad exact name, source campaign fragment)
POOL_MY = [
    ("HOOK：Video 8：做么你 Trading 不用看盘的？", "HOOK：Video 8：做么你 Trading 不用看盘的？", "0911 HOOK"),
    ("HOOK：Video 12：不选 forex 不选黄金", "HOOK：Video 12：不选 forex 不选黄金", "0911 HOOK"),
    ("HOOK：Video 12：炒过那么多，累而且不稳定", "HOOK：Video 12：炒过那么多，累而且不稳定", "0911 HOOK"),
    ("拼接：Video 1：用我的方法", "拼接：Video 1：用我的方法", "0911 HOOK"),
    ("freestyle: korea", "freestyle: korea", "BROAD MY 25+ | 0905"),
    ("freestyle 1", "freestyle 1", "BROAD MY 25+ | 0905"),
    ("video 2：你敢吗？", "🌟 video 2：你敢吗？", "PURCHASE LAL 1-5%"),
]
POOL_SG = [
    ("HOOK：Video 12：炒过那么多，累而且不稳定", "HOOK：Video 12：炒过那么多，累而且不稳定", "BROAD SG 25+ | 0911"),
    ("HOOK：Video 12：不选 forex 不选黄金", "HOOK：Video 12：不选 forex 不选黄金", "BROAD SG 25+ | 0911"),
    ("HOOK：Video 5：盖电脑，喂！", "HOOK：Video 5：盖电脑，喂！", "GOLF PICKLEBALL"),
    ("freestyle 1", "🌟 freestyle 1", "BROAD | 1-1-3 B"),
    ("video 2: 我只有一个目的", "🌟 video 2: 我只有一个目的", "GOLF PICKBLEBALL"),
    ("freestyle: korea", "freestyle: korea", "BROAD | 1-1-3 A"),
    ("重拍：Video 6：我跟你讲！", "重拍：Video 6：我跟你讲！", "BROAD SG 25+ | 0910"),
    ("video 1：用我的方法", "video 1：用我的方法", "BROAD SG 25+ | 0905"),
]
BUILDS = [
    ("config.yaml", "STOCKBLOOM | ANDRO POOL 30+ | 0922", "Broad Pool MY 30+", POOL_MY, False),
    ("config.sg.yaml", "[SG] STOCKBLOOM | ANDRO POOL 30+ | 0922", "Broad Pool SG 30+", POOL_SG, True),
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"ANDRO POOL build · MY+SG · CBO RM{DAILY / 100:.0f}/day · adset PAUSED — {mode}\n")

    for cfg, camp_name, aset_name, pool, is_sg in BUILDS:
        label = "SG" if is_sg else "MY"
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        conv = s.meta.conversion_domain_bare or None

        ads = g._get_all(
            f"{acct}/ads",
            {"fields": "name,status,effective_status,campaign{id,name},"
                       "creative{effective_object_story_id,object_story_id}",
             "limit": "500"})
        time.sleep(1.2)

        posts, missing = {}, []
        for pool_name, src_name, cfrag in pool:
            hits = [a for a in ads
                    if N(a.get("name") or "") == N(src_name)
                    and cfrag in ((a.get("campaign") or {}).get("name") or "")]
            hits.sort(key=lambda a: a.get("status") != "ACTIVE")   # prefer own-status ACTIVE
            post = None
            for h in hits:
                cr = h.get("creative") or {}
                post = cr.get("effective_object_story_id") or cr.get("object_story_id")
                if post:
                    break
            if not post:
                missing.append(pool_name)
                print(f"  ⛔ [{label}] 找不到 post «{src_name[:32]}» ({cfrag}) — 这支跳过")
                continue
            posts[pool_name] = post
            print(f"  post ✓ [{label}] «{pool_name[:32]}»  {post}")
        if not posts:
            print(f"  ⛔ [{label}] 一支 post 都没解析到 — 停")
            continue

        targeting = {
            "geo_locations": {"countries": s.meta.targeting.countries},
            "age_range": [30, 65],                     # Advantage+ ON -> suggestion only
            "targeting_automation": {"advantage_audience": 1},
        }
        if s.meta.targeting.locales:
            targeting["locales"] = s.meta.targeting.locales

        if not CONFIRM:
            print(f"  ▶ [{label}] would create «{camp_name}» CBO RM{DAILY / 100:.0f} ACTIVE "
                  f"+ adset «{aset_name}» PAUSED (Broad Adv+, 30+ 建议) + {len(posts)} post-reuse ads\n")
            continue

        camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
        time.sleep(1.2)
        camp_id = next((c["id"] for c in camps if (c.get("name") or "") == camp_name), None)
        if camp_id:
            print(f"  · [{label}] campaign exists ({camp_id}) — filling gaps")
        else:
            camp = g.create_campaign(
                acct, name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
                daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                special_ad_categories=[], status="ACTIVE")
            camp_id = camp["id"]
            print(f"  ✓ [{label}] campaign {camp_id}  «{camp_name}» CBO RM{DAILY / 100:.0f}")
            time.sleep(PACE)

        asets = g._get_all(f"{camp_id}/adsets", {"fields": "id,name", "limit": "10"})
        time.sleep(1.2)
        aset_id = next((x["id"] for x in asets if (x.get("name") or "") == aset_name), None)
        if not aset_id:
            kw = dict(name=aset_name, campaign_id=camp_id,
                      optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                      promoted_object=s.meta.promoted_object,
                      targeting=targeting, status="PAUSED")
            if is_sg:
                kw["regional_regulated_categories"] = REGIONAL
                kw["regional_regulation_identities"] = REG_IDENTITIES
            aset = g.create_adset(acct, **kw)
            aset_id = aset["id"]
            print(f"  ✓ [{label}] adset {aset_id} «{aset_name}» (PAUSED gate)")
            time.sleep(PACE)

        have = {N(a.get("name") or "") for a in g._get_all(
            f"{camp_id}/ads", {"fields": "name", "limit": "50"})}
        time.sleep(1.2)
        for pool_name, _src, _f in pool:
            if pool_name not in posts or N(pool_name) in have:
                continue
            spec = {"name": f"{label} | POOL | {pool_name}", "object_story_id": posts[pool_name]}
            if s.meta.url_tags:
                spec["url_tags"] = s.meta.url_tags
            cr = g.create_adcreative(acct, **spec)
            ad = g.create_ad(acct, name=pool_name, adset_id=aset_id,
                             creative={"creative_id": cr["id"]},
                             status="ACTIVE", conversion_domain=conv)
            print(f"  ✓ [{label}] ad {ad['id']}  «{pool_name[:32]}»")
            time.sleep(PACE)
        print()
    print("ANDRO POOL BUILD DONE — campaign CBO RM100 ACTIVE / ad set PAUSED，owner 审后自行开启。")


if __name__ == "__main__":
    main()
