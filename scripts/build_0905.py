# -*- coding: utf-8 -*-
"""Owner 2026-09-04: first build in the NEW per-ad-budget structure.

  Campaign «STOCKBLOOM | BROAD MY 25+ | 0905»       — ads #3 #5 #8 #10 #1 #2
  Campaign «STOCKBLOOM | LUXURY GOODS 30-55 | 0905» — ads #2 #4 #8
  Campaign «STOCKBLOOM | DAY TRADING | 0905»        — ads #1 #3 #7 #6 #2 #10

One ad per ad set, each ad set RM50/day (ABO — no campaign budget), ad set
named exactly by its targeting («Broad MY 25+» / «Luxury Goods 30-55» /
«Day Trading»). Every ad reuses an existing live post (object_story_id).
All ad sets scheduled to start 2026-09-05 00:00 MYT (statuses ACTIVE, the
start_time gates delivery). Scale rule is manual per owner: leads + low CPL
→ RM50→80→100→150 per individual ad set.

Targeting scaffolds cloned from proven ad sets (custom audiences dropped,
interests kept): Broad ← AUG NEW D · Luxury ← LUXURY GOODS 1-1-3 (age
override 30-55, special-ad-category fallback drops ages if refused) ·
Day Trading ← DAY TRADING 1-1-3. Idempotent at (campaign, ad-name) level."""
from __future__ import annotations

import copy as _copy
import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.5
DAILY = 5000                                   # RM50/day per ad set
START = "2026-09-05T00:00:00+0800"
N = cpa.norm

AD_CANDS = {
    "盖电脑":   ["video 5：盖电脑，喂！"],
    "你敢吗":   ["video 2：你敢吗？"],
    "freestyle 1": ["freestyle 1"],
    "我跟你讲": ["video 6：我跟你讲！"],
    "年纪大":   ["Video 5：年纪大的人做不了交易？"],
    "不选forex": ["video 12：不选 forex 不选黄金"],
    "炒过那么多": ["video 12：炒过那么多，累而且不稳定"],
    "korea":    ["freestyle: korea"],
    "不用看盘": ["video 8：做么你 trading 不用看盘的？"],
}

# scaffold: campaign-name fragment whose first ad set donates targeting+promo
CAMPAIGNS = [
    {"name": "STOCKBLOOM | BROAD MY 25+ | 0905", "aset": "Broad MY 25+",
     "scaffold": "BROAD | 1-1-3 A", "broad": True,
     "ads": ["freestyle 1", "年纪大", "korea", "不用看盘", "盖电脑", "你敢吗"]},
    {"name": "STOCKBLOOM | LUXURY GOODS 30-55 | 0905", "aset": "Luxury Goods 30-55",
     "scaffold": "LUXURY GOODS | 1-1-3", "age": (30, 55),
     "ads": ["你敢吗", "我跟你讲", "korea"]},
    {"name": "STOCKBLOOM | DAY TRADING | 0905", "aset": "Day Trading",
     "scaffold": "DAY TRADING | 1-1-3",
     "ads": ["盖电脑", "freestyle 1", "炒过那么多", "不选forex", "你敢吗", "不用看盘"]},
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"Build 0905 · 新结构 3 campaigns / 15 ad sets × RM{DAILY/100:.0f} · "
          f"start {START} — {mode}\n")

    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None

    pool = g._get_all(
        f"{acct}/ads",
        {"fields": "name,effective_status,creative{effective_object_story_id,object_story_id}",
         "limit": "500"})
    time.sleep(1.2)

    def resolve_post(cands):
        best = []
        for nm in cands:
            for a in pool:
                if N(a.get("name") or "") != N(nm):
                    continue
                cr = a.get("creative") or {}
                post = cr.get("effective_object_story_id") or cr.get("object_story_id")
                if post:
                    bad = a.get("effective_status") in ("WITH_ISSUES", "DISAPPROVED")
                    act = a.get("effective_status") == "ACTIVE"
                    clean = (a.get("name") or "").lstrip("🌟 ")   # 新广告不带星
                    best.append((0 if act else (2 if bad else 1), post, clean))
        if not best:
            return None, None
        best.sort()
        return best[0][1], best[0][2]

    camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
    time.sleep(1.2)

    def find_camp(frag):
        hits = [c for c in camps if frag in (c.get("name") or "")]
        return hits[0] if hits else None

    for spec in CAMPAIGNS:
        print(f"◆ {spec['name']}")
        try:
            sc_camp = find_camp(spec["scaffold"])
            if not sc_camp:
                print(f"   ⛔ scaffold campaign «{spec['scaffold']}» 找不到 — 跳过\n")
                continue
            sc = (g._get_all(f"{sc_camp['id']}/adsets",
                             {"fields": "id,name,targeting,promoted_object",
                              "limit": "5"}) or [None])[0]
            time.sleep(1)
            if not sc:
                print("   ⛔ scaffold 无 ad set — 跳过\n")
                continue
            tgt0 = _copy.deepcopy(sc.get("targeting") or {})
            tgt0.pop("custom_audiences", None)
            if spec.get("broad"):          # 真广投：清掉任何兴趣定向
                tgt0.pop("flexible_spec", None)
            if spec.get("age"):
                tgt0["age_min"], tgt0["age_max"] = spec["age"]
            promo = sc.get("promoted_object") or {}
            print(f"   scaffold ✓ «{(sc.get('name') or '')[:40]}» "
                  f"(interests {'yes' if tgt0.get('flexible_spec') else 'broad'})")

            plan = []
            for key in spec["ads"]:
                post, disp = resolve_post(AD_CANDS[key])
                if post:
                    plan.append({"name": disp, "post": post})
                    print(f"   ad ✓ «{disp}»  post={post}")
                else:
                    print(f"   ad ✗ {key} — 无可用 post — 这支跳过")
            if not plan:
                print("   ⛔ 无可建广告 — 跳过\n")
                continue

            if not CONFIRM:
                print(f"   ▶ would build campaign(ABO) + {len(plan)} × "
                      f"[adset «{spec['aset']}» RM50 start 9/5 00:00 + ad]\n")
                continue

            camp_id = next((c["id"] for c in camps
                            if (c.get("name") or "") == spec["name"]), None)
            if camp_id:
                print(f"   · campaign exists ({camp_id}) — filling gaps")
            else:
                camp = g.create_campaign(
                    acct, name=spec["name"], objective="OUTCOME_SALES",
                    buying_type="AUCTION",
                    # ABO：预算在 ad set 层，且禁止 ad set 之间共享预算
                    is_adset_budget_sharing_enabled="false",
                    special_ad_categories=s.meta.special_ad_categories,
                    special_ad_category_country=["MY"], status="ACTIVE")
                camp_id = camp["id"]
                print(f"   ✓ campaign {camp_id} (ABO, ACTIVE — 无预算，不会跑)")
                time.sleep(PACE)

            have = {N(a.get("name") or "") for a in g._get_all(
                f"{camp_id}/ads", {"fields": "name", "limit": "50"})}
            for t in plan:
                if N(t["name"]) in have:
                    print(f"   · «{t['name']}» 已在 — skip")
                    continue
                tgt = _copy.deepcopy(tgt0)
                kw = dict(name=spec["aset"], campaign_id=camp_id,
                          daily_budget=DAILY, optimization_goal="OFFSITE_CONVERSIONS",
                          billing_event="IMPRESSIONS", promoted_object=promo,
                          targeting=tgt, start_time=START, status="ACTIVE")
                try:
                    aset = g.create_adset(acct, **kw)
                except Exception as e:
                    if "age" in str(e).lower() and "age_min" in tgt:
                        print("   ⚠️ 特殊广告类别拒绝年龄限制 — 去掉 30-55 重试")
                        tgt.pop("age_min", None)
                        tgt.pop("age_max", None)
                        kw["targeting"] = tgt
                        aset = g.create_adset(acct, **kw)
                    else:
                        raise
                time.sleep(PACE)
                cr_spec = {"name": f"MY | {spec['aset']} | {t['name']}",
                           "object_story_id": t["post"]}
                if s.meta.url_tags:
                    cr_spec["url_tags"] = s.meta.url_tags
                cr = g.create_adcreative(acct, **cr_spec)
                ad = g.create_ad(acct, name=t["name"], adset_id=aset["id"],
                                 creative={"creative_id": cr["id"]},
                                 status="ACTIVE", conversion_domain=conv)
                print(f"   ✓ adset {aset['id']} + ad {ad['id']}  «{t['name']}» RM50 @9/5")
                time.sleep(PACE)
        except Exception as e:
            print(f"   ❌ {str(e)[:140]} — continuing")
        print()

    print("BUILD 0905 DONE — 15 ad sets scheduled 9/5 00:00, RM750/day total."
          if CONFIRM else "DRY-RUN — 核对 post/scaffold 后 confirm=true。")


if __name__ == "__main__":
    main()
