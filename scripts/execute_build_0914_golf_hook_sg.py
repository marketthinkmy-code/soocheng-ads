# -*- coding: utf-8 -*-
"""Owner 2026-09-14「建 GOLF / PICKLEBALL 就好」— SG GOLF audience for the 4 HOOKs.

  «[SG] STOCKBLOOM | GOLF PICKLEBALL 30-55 | 0914 HOOK 重拍» — ABO, 4 ad sets ×
  RM50/day PAUSED (SG regulated fields), 1 ad each REUSING the SG HOOK wave's
  posts (built this morning; engagement pools, review carries per-ad).
  Interests + base targeting cloned from the converting 🌟 GOLF PICKBLEBALL |
  1-1-3 ad set (SG 的安静冠军: 近7天 CPL ~49, 我只有一个目的 6 单 + trading
  早就不是这样了 9 单都在这条链). Hard audience: advantage_audience=0, 30-55
  hard, age_range stripped. No special ad category. Idempotent. Dry-run unless
  CONFIRM=true."""
from __future__ import annotations

import copy as _copy
import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 5.0
DAILY = 5000
N = cpa.norm

HOOK_CAMP_SG = "120249390872620521"       # [SG] 0911 HOOK 重拍 — the 4 SG posts
SCAFFOLD = "GOLF PICKBLEBALL | 1-1-3"     # 🌟 converting GOLF chain (account spelling)
CAMP_NAME = "[SG] STOCKBLOOM | GOLF PICKLEBALL 30-55 | 0914 HOOK 重拍"
ASET_NAME = "Golf Pickleball SG 30-55"

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

HOOKS = [
    "HOOK：Video 5：盖电脑，喂！",
    "HOOK：Video 12：不选 forex 不选黄金",
    "HOOK：Video 8：做么你 Trading 不用看盘的？",
    "HOOK：Video 12：炒过那么多，累而且不稳定",
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"SG GOLF × HOOK · 1-4-4 RM50 PAUSED — {mode}\n")
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None

    src_ads = g._get_all(
        f"{HOOK_CAMP_SG}/ads",
        {"fields": "name,effective_status,"
                   "creative{effective_object_story_id,object_story_id}",
         "limit": "25"})
    time.sleep(1)
    posts = {}
    for want in HOOKS:
        hit = [a for a in src_ads if N(want) == N(a.get("name") or "")]
        if len(hit) != 1:
            print(f"⛔ post «{want}» 匹配 {len(hit)} — 停")
            return
        cr = hit[0].get("creative") or {}
        post = cr.get("effective_object_story_id") or cr.get("object_story_id")
        if not post:
            print(f"⛔ «{want}» 无 post id — 停")
            return
        posts[want] = post
        print(f"post ✓ «{want[:34]}»  {post}")

    camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
    time.sleep(1)
    sc_camp = next((c for c in camps if SCAFFOLD in (c.get("name") or "")), None)
    if not sc_camp:
        print(f"⛔ scaffold «{SCAFFOLD}» 找不到")
        return
    sc = (g._get_all(f"{sc_camp['id']}/adsets",
                     {"fields": "id,name,targeting,promoted_object", "limit": "5"})
          or [None])[0]
    time.sleep(1)
    tgt0 = _copy.deepcopy(sc.get("targeting") or {})
    for k in ("custom_audiences", "excluded_custom_audiences",
              "age_range", "targeting_relaxation_types"):
        tgt0.pop(k, None)
    tgt0["age_min"], tgt0["age_max"] = 30, 55
    tgt0["targeting_automation"] = {"advantage_audience": 0}
    promo = sc.get("promoted_object") or {}
    n_int = sum(len(fs.get("interests") or []) for fs in (tgt0.get("flexible_spec") or []))
    names = [i.get("name") for fs in (tgt0.get("flexible_spec") or [])
             for i in (fs.get("interests") or [])]
    print(f"GOLF targeting ✓ interests×{n_int}: "
          f"{'、'.join((x or '?')[:16] for x in names[:6])} · "
          f"geo {(tgt0.get('geo_locations') or {}).get('countries')} · 30-55 hard")

    if not CONFIRM:
        print(f"\n▶ would create campaign(ABO ACTIVE, special=[]) + 4 × "
              f"[adset «{ASET_NAME}» RM50 PAUSED (硬锁, SG regulated) + post-reuse ad ACTIVE]")
        return

    camp_id = next((c["id"] for c in camps if (c.get("name") or "") == CAMP_NAME), None)
    if camp_id:
        print(f"· campaign exists ({camp_id}) — filling gaps")
    else:
        camp = g.create_campaign(
            acct, name=CAMP_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            is_adset_budget_sharing_enabled="false",
            special_ad_categories=[], status="ACTIVE")
        camp_id = camp["id"]
        print(f"✓ campaign {camp_id}  «{CAMP_NAME}»")
        time.sleep(PACE)
    have = {N(a.get("name") or "") for a in g._get_all(
        f"{camp_id}/ads", {"fields": "name", "limit": "50"})}
    for want in HOOKS:
        if N(want) in have:
            print(f"  · «{want[:30]}» 已在 — skip")
            continue
        aset = g.create_adset(
            acct, name=ASET_NAME, campaign_id=camp_id, daily_budget=DAILY,
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            bid_strategy="LOWEST_COST_WITHOUT_CAP", promoted_object=promo,
            targeting=_copy.deepcopy(tgt0), status="PAUSED",
            regional_regulated_categories=REGIONAL,
            regional_regulation_identities=REG_IDENTITIES)
        time.sleep(PACE)
        spec = {"name": f"SG | GOLF HOOK | {want}", "object_story_id": posts[want]}
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        cr = g.create_adcreative(acct, **spec)
        ad = g.create_ad(acct, name=want, adset_id=aset["id"],
                         creative={"creative_id": cr["id"]},
                         status="ACTIVE", conversion_domain=conv)
        print(f"  ✓ adset {aset['id']}(PAUSED) + ad {ad['id']}  «{want[:30]}»")
        time.sleep(PACE)
    print("\nBUILD 0914 SG GOLF HOOK DONE — 全部 ad set PAUSED，owner 审后自行开启。")


if __name__ == "__main__":
    main()
