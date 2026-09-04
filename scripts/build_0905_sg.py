# -*- coding: utf-8 -*-
"""Owner 2026-09-04: SG wave of the new per-ad-budget structure.

  «[SG] STOCKBLOOM | BROAD SG 25+ | 0905»       — ads #1 #4 #5 #7 #9
  «[SG] STOCKBLOOM | TRAVEL | 0905»             — ads #3 #4 #8
  «[SG] STOCKBLOOM | GOLF PICKLEBALL | 0905»    — ads #1 #2 #6 #7

Same spec as the MY 0905 build: one ad per ad set, RM50/day each (ABO,
adset budget sharing disabled), ad set named by targeting, posts reused,
ad sets scheduled 2026-09-05 00:00 MYT. SG regulated-category identity
fields included (financial vertical). Idempotent at (campaign, ad) level."""
from __future__ import annotations

import copy as _copy
import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.5
DAILY = 5000
START = "2026-09-05T00:00:00+0800"
N = cpa.norm

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

AD_CANDS = {
    "freestyle 1": ["freestyle 1"],
    "trading早就": ["video 5：trading 早就不是这样了！"],
    "用我的方法": ["video 1：用我的方法"],
    "office突访": ["video 11：office 突访"],
    "不用看盘": ["video 8：做么你 trading 不用看盘的？"],
    "我只有一个目的": ["video 2: 我只有一个目的"],
    "korea": ["freestyle: korea"],
    "你敢吗": ["video 2：你敢吗？"],
    "盖电脑": ["video 5：盖电脑，喂！"],
}

CAMPAIGNS = [
    {"name": "[SG] STOCKBLOOM | BROAD SG 25+ | 0905", "aset": "Broad SG 25+",
     "scaffold": "BROAD | 1-1-3 B", "broad": True,
     "ads": ["freestyle 1", "trading早就", "用我的方法", "office突访", "不用看盘"]},
    {"name": "[SG] STOCKBLOOM | TRAVEL | 0905", "aset": "Travel",
     "scaffold": "TRAVEL | 1-1-3",
     "ads": ["我只有一个目的", "trading早就", "korea"]},
    {"name": "[SG] STOCKBLOOM | GOLF PICKLEBALL | 0905", "aset": "Golf / Pickleball",
     "scaffold": "GOLF PICKBLEBALL",
     "ads": ["freestyle 1", "你敢吗", "盖电脑", "office突访"]},
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"Build 0905 SG · 3 campaigns / 12 ad sets × RM{DAILY/100:.0f} · "
          f"start {START} — {mode}\n")

    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
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
                    clean = (a.get("name") or "").lstrip("🌟 ")
                    best.append((0 if act else (2 if bad else 1), post, clean))
            if best:
                break
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
            if spec.get("broad"):
                tgt0.pop("flexible_spec", None)
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
                    is_adset_budget_sharing_enabled="false",
                    special_ad_categories=s.meta.special_ad_categories,
                    special_ad_category_country=["SG"], status="ACTIVE")
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
                          billing_event="IMPRESSIONS",
                          bid_strategy="LOWEST_COST_WITHOUT_CAP",
                          promoted_object=promo, targeting=tgt,
                          start_time=START, status="ACTIVE",
                          regional_regulated_categories=REGIONAL,
                          regional_regulation_identities=REG_IDENTITIES)
                aset = g.create_adset(acct, **kw)
                time.sleep(PACE)
                cr_spec = {"name": f"SG | {spec['aset']} | {t['name']}",
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

    print("BUILD 0905 SG DONE — 12 ad sets scheduled 9/5 00:00, RM600/day total."
          if CONFIRM else "DRY-RUN — 核对 post/scaffold 后 confirm=true。")


if __name__ == "__main__":
    main()
