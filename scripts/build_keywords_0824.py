# -*- coding: utf-8 -*-
"""Owner 2026-08-24: four new detailed-targeting keyword tests, all approved:

  BROKERS (MY+SG)          炒过那么多 + 你敢吗 + trading早就   — broker-app users
  RETIREMENT (MY, 45-60)   年纪大 + 用我的方法 + 炒过那么多
  PRIORITY BANKING (MY+SG) 用我的方法 + freestyle 1 + 我只有一个目的
  COUNTRY CLUB (SG)        korea + freestyle 1 + 盖电脑

Each: 1-1-3 · CBO RM100/day · PAUSED. Interests are validated live against
Meta's adinterest search (exact-match preferred; a campaign builds only if ≥3
resolve). Targeting scaffold (geo/placements/promoted_object) cloned from a
proven interest ad set per account, flexible_spec replaced with the new
interests, custom_audiences dropped. Ads reuse live posts (object_story_id) so
nothing re-enters review. Idempotent at campaign/adset/ad level."""
from __future__ import annotations

import copy as _copy
import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
DAILY = 10000
N = cpa.norm

REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]

# scaffold ad sets: proven interest campaigns per account
SCAFFOLD_CAMP = {"MY": "120247921988670575",   # MY DAY TRADING
                 "SG": "120248220643620521"}   # SG GOLF PICKBLEBALL

AD_CANDS = {
    "炒过那么多": ["video 12：炒过那么多，累而且不稳定"],
    "你敢吗": ["video 2：你敢吗？"],
    "trading早就": ["video 5：trading 早就不是这样了！"],
    "年纪大": ["Video 5：年纪大的人做不了交易？"],
    "用我的方法": ["video 1: 用我的方法，你也可以有将多", "video 1：用我的方法"],
    "freestyle 1": ["freestyle 1"],
    "我只有一个目的": ["video 2: 我只有一个目的"],
    "korea": ["freestyle: korea"],
    "盖电脑": ["video 5：盖电脑，喂！"],
}

CAMPAIGNS = [
    {"label": "MY", "name": "STOCKBLOOM | BROKERS | 1-1-3",
     "aset": "AdSet (Brokers | MY 25+)",
     "interests": ["Moomoo", "Tiger Brokers", "Interactive Brokers", "TradingView",
                   "Day trading", "Stockbroker"],
     "ads": ["炒过那么多", "你敢吗", "trading早就"]},
    {"label": "SG", "name": "[SG] STOCKBLOOM | BROKERS | 1-1-3",
     "aset": "AdSet (Brokers | SG 25+)",
     "interests": ["Moomoo", "Tiger Brokers", "Interactive Brokers", "TradingView",
                   "Day trading", "Stockbroker"],
     "ads": ["炒过那么多", "你敢吗", "trading早就"]},
    {"label": "MY", "name": "STOCKBLOOM | RETIREMENT | 1-1-3",
     "aset": "AdSet (Retirement | MY 45-60)", "age": (45, 60),
     "interests": ["Retirement planning", "Employees Provident Fund", "Retirement",
                   "Pension", "Fixed deposit"],
     "ads": ["年纪大", "用我的方法", "炒过那么多"]},
    {"label": "MY", "name": "STOCKBLOOM | PRIORITY BANKING | 1-1-3",
     "aset": "AdSet (Priority Banking | MY 25+)",
     "interests": ["Private banking", "Wealth management", "Dividend",
                   "Passive income", "Financial planning"],
     "ads": ["用我的方法", "freestyle 1", "我只有一个目的"]},
    {"label": "SG", "name": "[SG] STOCKBLOOM | PRIORITY BANKING | 1-1-3",
     "aset": "AdSet (Priority Banking | SG 25+)",
     "interests": ["Private banking", "Wealth management", "Dividend",
                   "Passive income", "Financial planning"],
     "ads": ["我只有一个目的", "freestyle 1", "用我的方法"]},
    {"label": "SG", "name": "[SG] STOCKBLOOM | COUNTRY CLUB | 1-1-3",
     "aset": "AdSet (Country Club Wine | SG 25+)",
     "interests": ["Country club", "Fine dining", "Wine", "Whisky", "Golf club"],
     "ads": ["korea", "freestyle 1", "盖电脑"]},
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"Keyword expansion ×6 · 1-1-3 RM{DAILY/100:.0f}/day PAUSED — {mode}\n")

    cfgs = {"MY": load_settings(REPO_ROOT / "config" / "config.yaml"),
            "SG": load_settings(REPO_ROOT / "config" / "config.sg.yaml")}
    gs = {k: graph_client(v) for k, v in cfgs.items()}

    # post pool from BOTH accounts (page-level posts work cross-account)
    pools = []
    for k in ("MY", "SG"):
        pools.append(gs[k]._get_all(
            f"{cfgs[k].meta.account_path}/ads",
            {"fields": "name,effective_status,creative{effective_object_story_id,object_story_id}",
             "limit": "300"}))
        time.sleep(1)

    def resolve_post(cands):
        best = []
        for nm in cands:
            for ads in pools:
                for a in ads:
                    if N(a.get("name") or "") != N(nm):
                        continue
                    cr = a.get("creative") or {}
                    post = cr.get("effective_object_story_id") or cr.get("object_story_id")
                    if post:
                        best.append((0 if a.get("effective_status") == "ACTIVE" else 1,
                                     post, a.get("name")))
            if best:
                break
        if not best:
            return None, None
        best.sort()
        return best[0][1], best[0][2]

    def find_interest(g, name):
        try:
            rows = (g._request("GET", "search",
                               params={"type": "adinterest", "q": name,
                                       "limit": "10"}) or {}).get("data", [])
        except Exception as e:
            print(f"     ⚠️ interest search «{name}»: {str(e)[:80]}")
            return None
        for r in rows:
            if (r.get("name") or "").lower() == name.lower():
                return r
        return rows[0] if rows else None

    scaffolds = {}
    for label, cid in SCAFFOLD_CAMP.items():
        a = gs[label]._get_all(f"{cid}/adsets",
                               {"fields": "id,name,targeting,promoted_object",
                                "limit": "5"})
        scaffolds[label] = a[0] if a else None
        time.sleep(1)

    for spec in CAMPAIGNS:
        label = spec["label"]
        s, g = cfgs[label], gs[label]
        acct = s.meta.account_path
        conv = s.meta.conversion_domain_bare or None
        print(f"◆ {spec['name']}")
        try:
            ints = []
            for nm in spec["interests"]:
                hit = find_interest(g, nm)
                if hit:
                    size = hit.get("audience_size_upper_bound") or hit.get("audience_size") or "?"
                    print(f"   interest ✓ «{hit.get('name')}» (id {hit.get('id')}, ~{size})")
                    ints.append({"id": hit["id"], "name": hit.get("name")})
                else:
                    print(f"   interest ✗ «{nm}» — 找不到，跳过")
                time.sleep(1)
            if len(ints) < 3:
                print(f"   ⛔ 只解析到 {len(ints)} 个兴趣 — 跳过此 campaign\n")
                continue

            trio = []
            for key in spec["ads"]:
                post, disp = resolve_post(AD_CANDS[key])
                if post:
                    trio.append({"name": disp, "post": post})
                    print(f"   ad ✓ «{disp}»  post={post}")
                else:
                    print(f"   ad ✗ {key} — 无可用 post")
            if len(trio) < 3:
                print(f"   ⛔ 只解析到 {len(trio)} 支广告 — 跳过\n")
                continue

            sc = scaffolds.get(label)
            if not sc:
                print("   ⛔ scaffold 缺失 — 跳过\n")
                continue
            tgt = _copy.deepcopy(sc.get("targeting") or {})
            tgt.pop("custom_audiences", None)
            tgt.pop("flexible_spec", None)
            tgt["flexible_spec"] = [{"interests": ints}]
            if spec.get("age"):
                tgt["age_min"], tgt["age_max"] = spec["age"]
            promo = sc.get("promoted_object") or {}

            if not CONFIRM:
                print("   ▶ would build campaign+adset+3 ads (PAUSED)\n")
                continue

            existing = {c.get("name"): c.get("id") for c in g._get_all(
                f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})}
            camp_id = existing.get(spec["name"])
            if camp_id:
                print(f"   · campaign exists ({camp_id}) — filling gaps")
            else:
                camp = g.create_campaign(
                    acct, name=spec["name"], objective="OUTCOME_SALES",
                    buying_type="AUCTION", daily_budget=DAILY,
                    bid_strategy="LOWEST_COST_WITHOUT_CAP",
                    special_ad_categories=s.meta.special_ad_categories,
                    special_ad_category_country=[label], status="PAUSED")
                camp_id = camp["id"]
                print(f"   ✓ campaign {camp_id}")
                time.sleep(PACE)

            have = {N(a.get("name") or ""): a["id"] for a in g._get_all(
                f"{camp_id}/adsets", {"fields": "id,name", "limit": "10"})}
            aset_id = have.get(N(spec["aset"]))
            if not aset_id:
                kw = dict(name=spec["aset"], campaign_id=camp_id,
                          optimization_goal="OFFSITE_CONVERSIONS",
                          billing_event="IMPRESSIONS", promoted_object=promo,
                          targeting=tgt, status="PAUSED")
                if label == "SG":
                    kw.update(regional_regulated_categories=REGIONAL,
                              regional_regulation_identities=REG_IDENTITIES)
                aset = g.create_adset(acct, **kw)
                aset_id = aset["id"]
                print(f"   ✓ adset {aset_id}")
                time.sleep(PACE)
            else:
                print(f"   · adset exists")

            have_ads = {a.get("name") for a in g._get_all(
                f"{aset_id}/ads", {"fields": "name", "limit": "10"})}
            for t in trio:
                if t["name"] in have_ads:
                    print(f"   · «{t['name']}» 已在 — skip")
                    continue
                cr_spec = {"name": f"{label} | {spec['aset']} | {t['name']}",
                           "object_story_id": t["post"]}
                if s.meta.url_tags:
                    cr_spec["url_tags"] = s.meta.url_tags
                cr = g.create_adcreative(acct, **cr_spec)
                ad = g.create_ad(acct, name=t["name"], adset_id=aset_id,
                                 creative={"creative_id": cr["id"]},
                                 status="PAUSED", conversion_domain=conv)
                print(f"   ✓ ad {ad['id']}  «{t['name']}»")
                time.sleep(PACE)
        except Exception as e:
            print(f"   ❌ {str(e)[:140]} — continuing")
        print()

    print("DONE — 6 keyword campaigns PAUSED; owner reviews & activates."
          if CONFIRM else "DRY-RUN — 检查兴趣解析和 post 后 confirm=true。")


if __name__ == "__main__":
    main()
