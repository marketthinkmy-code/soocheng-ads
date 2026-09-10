# -*- coding: utf-8 -*-
"""Owner 2026-09-10晚: iPhone Duo 单图 1-1-1, MY — 手机/数码 兴趣 ad set.

  Campaign «STOCKBLOOM | MOBILE GADGETS | 1-1-1» — ABO, 1 ad set RM50/day PAUSED
  (owner 在 Ads Manager 审后自行开启; campaign ACTIVE but inert), 1 ad ACTIVE.

  Ad = REUSE the already-approved & delivering «Image：iPhone Duo 对比» post from
  the 0910 MY Broad build (post reuse = zero re-review risk, keeps engagement).

  Ad set targeting = the 0910 broad shape + a stacked interest group resolved live
  from Meta's adinterest search for the owner's 8 keywords (mobile / gadgets /
  mobile devices / iphone / apple / samsung / huawei / xiaomi), OR-ed in one
  flexible_spec group, advantage_audience=0 (hard interest lock — otherwise Meta
  treats interests as a hint and the test is fake).

  Campaign declares NO special ad category (owner 2026-09-10「全部帮我 untick」;
  the FINANCIAL declaration also blocks detailed/interest targeting).
  Idempotent at (campaign, ad-name). Dry-run unless CONFIRM=true."""
from __future__ import annotations

import copy as _copy
import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 5.0
DAILY = 5000                        # RM50/day
N = cpa.norm

CAMP_NAME = "STOCKBLOOM | MOBILE GADGETS | 1-1-1"
ASET_NAME = "MOBILE GADGETS | MY"
AD_NAME = "Image：iPhone Duo 对比"
SOURCE_CAMPAIGN = "120248787484510575"   # MY BROAD 0910 重拍 — holds the approved iPhone Duo post
KEYWORDS = ["mobile", "gadgets", "mobile devices", "iphone",
            "apple", "samsung", "huawei", "xiaomi"]


def pick_interest(g, kw):
    """Best adinterest for a keyword: exact name match first, else the largest
    audience whose name contains the keyword, else the top result. Returns
    (chosen or None, all candidates) so the dry-run can show the field."""
    rows = (g._request("GET", "search",
                       params={"type": "adinterest", "q": kw, "limit": "6"})
            or {}).get("data") or []
    for r in rows:
        r["_size"] = r.get("audience_size_upper_bound") or r.get("audience_size") or 0
    exact = [r for r in rows if (r.get("name") or "").lower() == kw.lower()]
    contains = [r for r in rows if kw.lower() in (r.get("name") or "").lower()]
    pool = exact or contains or rows
    return (max(pool, key=lambda r: r["_size"]) if pool else None), rows


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"1-1-1 build · «{CAMP_NAME}» · RM{DAILY/100:.0f}/day PAUSED — {mode}\n")

    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None

    # 1) resolve the owner's 8 interest keywords against Meta's adinterest search
    chosen, seen = [], set()
    print("兴趣搜索（每行 = 选中的；缩进 = 其他候选）：")
    for kw in KEYWORDS:
        best, rows = pick_interest(g, kw)
        time.sleep(1.0)
        if not best:
            print(f"  ⛔ «{kw}» 无结果 — 跳过")
            continue
        tag = "（重复，合并）" if best["id"] in seen else ""
        print(f"  ✓ {kw:>14} → «{best.get('name')}»  id={best['id']}  "
              f"size≈{best['_size']:,}{tag}")
        for r in rows:
            if r["id"] != best["id"]:
                print(f"                   · {r.get('name')}  size≈{r['_size']:,}")
        if best["id"] not in seen:
            seen.add(best["id"])
            chosen.append({"id": best["id"], "name": best.get("name")})
    if not chosen:
        print("⛔ 一个兴趣都没找到 — 停")
        return
    print(f"→ 叠进 1 个 flexible_spec 组（OR）：{len(chosen)} 个兴趣\n")

    # 2) source post + targeting shape from the 0910 iPhone Duo ad's own ad set
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
        print("⛔ 0910 campaign 里找不到 iPhone Duo 的 post — 停")
        return
    _, post_id, src = cand[0]
    print(f"post ✓ «{src.get('name')}» ({src.get('effective_status')})  {post_id}")

    src_aset = src.get("adset") or {}
    tgt = _copy.deepcopy(src_aset.get("targeting") or {})
    for k in ("custom_audiences", "excluded_custom_audiences", "flexible_spec"):
        tgt.pop(k, None)
    tgt["targeting_automation"] = {"advantage_audience": 0}   # 硬锁兴趣
    tgt["flexible_spec"] = [{"interests": chosen}]
    promo = src_aset.get("promoted_object") or {}
    print(f"targeting: age {tgt.get('age_min')}-{tgt.get('age_max')} · "
          f"geo {((tgt.get('geo_locations') or {}).get('countries'))} · "
          f"locales {tgt.get('locales')} · advantage_audience=0 · "
          f"interests×{len(chosen)}")

    if not CONFIRM:
        print(f"\n▶ would create: campaign(ABO ACTIVE, special_ad_categories=[]) + "
              f"adset «{ASET_NAME}» RM50 PAUSED + ad «{AD_NAME}» ACTIVE (post reuse)")
        return

    # 3) build (idempotent)
    camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
    time.sleep(1.2)
    camp_id = next((c["id"] for c in camps if (c.get("name") or "") == CAMP_NAME), None)
    if camp_id:
        print(f"· campaign exists ({camp_id}) — filling gaps")
    else:
        camp = g.create_campaign(
            acct, name=CAMP_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
            is_adset_budget_sharing_enabled="false",
            special_ad_categories=[],            # owner 2026-09-10: untick（兴趣定向也需要）
            status="ACTIVE")
        camp_id = camp["id"]
        print(f"✓ campaign {camp_id} (ABO ACTIVE, no special category — ad set PAUSED 是闸门)")
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
        targeting=tgt, status="PAUSED")
    time.sleep(PACE)
    spec = {"name": f"MY | MOBILE | {AD_NAME}", "object_story_id": post_id}
    if s.meta.url_tags:
        spec["url_tags"] = s.meta.url_tags
    cr = g.create_adcreative(acct, **spec)
    ad = g.create_ad(acct, name=AD_NAME, adset_id=aset["id"],
                     creative={"creative_id": cr["id"]},
                     status="ACTIVE", conversion_domain=conv)
    print(f"✓ adset {aset['id']}(PAUSED, RM50) + ad {ad['id']}  «{AD_NAME}»")
    print("\nBUILD MOBILE 1-1-1 DONE — ad set PAUSED，owner 在 Ads Manager 审后自行开启。")


if __name__ == "__main__":
    main()
