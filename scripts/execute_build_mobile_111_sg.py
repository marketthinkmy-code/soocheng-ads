# -*- coding: utf-8 -*-
"""Owner 2026-09-10晚:「sg 也建」— SG twin of the MOBILE GADGETS 1-1-1.

  Campaign «[SG] STOCKBLOOM | MOBILE GADGETS | 1-1-1» — ABO, 1 ad set RM50/day
  PAUSED + SG regulated fields (SINGAPORE_UNIVERSAL identities), 1 ad ACTIVE
  reusing the SG account's own approved «Image：iPhone Duo 对比» post from the
  SG 0910 Broad build. Same live-resolved 8-interest stack, advantage_audience=0.
  No special ad category (owner untick). Idempotent. Dry-run unless CONFIRM=true."""
from __future__ import annotations

import copy as _copy
import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

from execute_build_mobile_111 import AD_NAME, KEYWORDS, pick_interest  # noqa: E402

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 5.0
DAILY = 5000
N = cpa.norm

CAMP_NAME = "[SG] STOCKBLOOM | MOBILE GADGETS | 1-1-1"
ASET_NAME = "MOBILE GADGETS | SG"
SOURCE_CAMPAIGN = "120249341323780521"   # [SG] BROAD SG 25+ | 0910 重拍 — SG 自己的 iPhone Duo post
REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"1-1-1 SG build · «{CAMP_NAME}» · RM{DAILY/100:.0f}/day PAUSED — {mode}\n")

    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None

    chosen, seen = [], set()
    for kw in KEYWORDS:
        best, _rows = pick_interest(g, kw)
        time.sleep(1.0)
        if not best:
            print(f"  ⛔ «{kw}» 无结果 — 跳过")
            continue
        if best["id"] not in seen:
            seen.add(best["id"])
            chosen.append({"id": best["id"], "name": best.get("name")})
            print(f"  ✓ {kw:>14} → «{best.get('name')}»  id={best['id']}")
    if not chosen:
        print("⛔ 一个兴趣都没找到 — 停")
        return
    print(f"→ flexible_spec 1 组（OR）：{len(chosen)} 个兴趣\n")

    src_ads = g._get_all(
        f"{SOURCE_CAMPAIGN}/ads",
        {"fields": "name,effective_status,adset{targeting,promoted_object},"
                   "creative{effective_object_story_id,object_story_id}",
         "limit": "50"})
    time.sleep(1.2)
    cand = []
    for a in src_ads:
        if N("iphone duo") not in N(a.get("name") or ""):
            continue
        cr = a.get("creative") or {}
        post = cr.get("effective_object_story_id") or cr.get("object_story_id")
        if post:
            act = a.get("effective_status") == "ACTIVE"
            bad = a.get("effective_status") in ("WITH_ISSUES", "DISAPPROVED")
            cand.append((0 if act else (2 if bad else 1), post, a))
    cand.sort(key=lambda x: x[0])
    if not cand:
        print("⛔ SG 0910 campaign 里找不到 iPhone Duo 的 post — 停")
        return
    _, post_id, src = cand[0]
    print(f"post ✓ «{src.get('name')}» ({src.get('effective_status')})  {post_id}")

    src_aset = src.get("adset") or {}
    tgt = _copy.deepcopy(src_aset.get("targeting") or {})
    for k in ("custom_audiences", "excluded_custom_audiences", "flexible_spec",
              "age_range", "targeting_relaxation_types"):   # age_range 只在 Advantage+ ON 合法
        tgt.pop(k, None)
    tgt.setdefault("age_min", 25)
    tgt.setdefault("age_max", 65)
    tgt["targeting_automation"] = {"advantage_audience": 0}   # 硬锁兴趣
    tgt["flexible_spec"] = [{"interests": chosen}]
    promo = src_aset.get("promoted_object") or {}
    print(f"targeting: age {tgt.get('age_min')}-{tgt.get('age_max')} · "
          f"geo {((tgt.get('geo_locations') or {}).get('countries'))} · "
          f"locales {tgt.get('locales')} · advantage_audience=0 · interests×{len(chosen)}")

    if not CONFIRM:
        print(f"\n▶ would create: campaign(ABO ACTIVE, special_ad_categories=[]) + "
              f"adset «{ASET_NAME}» RM50 PAUSED (SG regulated fields) + "
              f"ad «{AD_NAME}» ACTIVE (post reuse)")
        return

    camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
    time.sleep(1.2)
    camp_id = next((c["id"] for c in camps if (c.get("name") or "") == CAMP_NAME), None)
    if camp_id:
        print(f"· campaign exists ({camp_id}) — filling gaps")
    else:
        camp = g.create_campaign(
            acct, name=CAMP_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            is_adset_budget_sharing_enabled="false",
            special_ad_categories=[],            # owner 2026-09-10: untick
            status="ACTIVE")
        camp_id = camp["id"]
        print(f"✓ campaign {camp_id} (ABO ACTIVE, no special category)")
        time.sleep(PACE)

    have = {N(a.get("name") or "") for a in g._get_all(
        f"{camp_id}/ads", {"fields": "name", "limit": "50"})}
    if N(AD_NAME) in have:
        print(f"· «{AD_NAME}» 已在 — nothing to do")
        return

    aset = g.create_adset(
        acct, name=ASET_NAME, campaign_id=camp_id, daily_budget=DAILY,
        optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
        bid_strategy="LOWEST_COST_WITHOUT_CAP", promoted_object=promo,
        targeting=tgt, status="PAUSED",
        regional_regulated_categories=REGIONAL,
        regional_regulation_identities=REG_IDENTITIES)
    time.sleep(PACE)
    spec = {"name": f"SG | MOBILE | {AD_NAME}", "object_story_id": post_id}
    if s.meta.url_tags:
        spec["url_tags"] = s.meta.url_tags
    cr = g.create_adcreative(acct, **spec)
    ad = g.create_ad(acct, name=AD_NAME, adset_id=aset["id"],
                     creative={"creative_id": cr["id"]},
                     status="ACTIVE", conversion_domain=conv)
    print(f"✓ adset {aset['id']}(PAUSED, RM50, SG regulated) + ad {ad['id']}  «{AD_NAME}»")
    print("\nBUILD MOBILE 1-1-1 SG DONE — ad set PAUSED，owner 审后自行开启。")


if __name__ == "__main__":
    main()
