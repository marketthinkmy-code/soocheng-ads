# -*- coding: utf-8 -*-
"""Build on the NEW MY account «[MY] MTC X SB 5.0» — owner 2026-10-08 structure:

  «STOCKBLOOM | DAY TRADING | 1-1-5 | 1008»     CBO RM100  · 1 adset (Day Trading 兴趣, 硬锁 30+)
  «STOCKBLOOM | BUSINESS OWNER | 1-1-5 | 1008»  CBO RM100  · 1 adset (Business Owner 兴趣, 硬锁 30+)
  «STOCKBLOOM | BROAD MY 30+ | 1-1-5 | 1008»    CBO RM100  · 1 adset (Broad, Advantage+ ON, 30-65 建议)
  each with the SAME 5 clean post-reuse ads (old MY winners that were never rejected).

Why these mechanics (CLAUDE.md):
  · campaign ACTIVE + adset PAUSED gate = 0 spend until the owner flips the adset himself;
  · interest targeting is CLONED from the proven ad sets on the disabled 3.0 account
    (same flexible_spec), with age_min 30 hard-locked, age_range stripped, Advantage+ off;
    broad gets age_range [30,65] as the suggestion (hard age_min can't be set with Adv+ ON);
  · audiences that live on the old account can't be reused -> stripped from the clone;
  · special_ad_categories mirrored from the source campaign (consistency with what ran);
  · post reuse (object_story_id) keeps copy + social proof and uploads nothing new;
  · ban gate on every ad name before any write; idempotent at (campaign, adset, ad) names.
Dry-run unless CONFIRM=true (prints the cloned targeting so it can be eyeballed first)."""
from __future__ import annotations

import json
import os
import time

from adbot import compliance, cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 5.0
DAILY = 10000                      # RM100/day CBO each (owner 2026-10-08)
OLD_MY = "act_759339046918885"     # disabled, still readable — source of targeting + posts
N = cpa.norm

# (ad name on Meta, page post to reuse — effective_object_story_id of the best-selling cut on old MY)
ADS = [
    ("Video：盖电脑，喂！",            "1001334883061622_1788611461813837"),
    ("Video：不选 forex 不选黄金",     "1001334883061622_122109026109286543"),
    ("Video：年纪大的人做不了交易？",   "1001334883061622_122120962899286543"),
    ("Video：freestyle korea",        "1001334883061622_122109881127286543"),
    ("Video：赚美金，一定要接美国客户？", "1001334883061622_122120277969286543"),
]
# (campaign name, adset name, source campaign fragment on old MY for the targeting clone | None = broad)
BUILDS = [
    ("STOCKBLOOM | DAY TRADING | 1-1-5 | 1008",    "Day Trading | MY 30+",    "DAY TRADING | 1-1-3"),
    ("STOCKBLOOM | BUSINESS OWNER | 1-1-5 | 1008", "Business Owner | MY 30+", "BUSINESS OWNER | 1-1-3"),
    ("STOCKBLOOM | BROAD MY 30+ | 1-1-5 | 1008",   "Broad | MY 30+",          None),
]
DROP_KEYS = ("custom_audiences", "excluded_custom_audiences", "age_range", "genders",
             "targeting_optimization", "targeting_relaxation_types", "publisher_platforms",
             "facebook_positions", "instagram_positions", "messenger_positions",
             "audience_network_positions", "device_platforms", "user_os")


def clone_targeting(g, fragment: str, locales):
    """Interest targeting from the proven old-MY ad set, hardened per the 30+ rule."""
    camps = g._get_all(OLD_MY + "/campaigns", {
        "fields": "id,name,special_ad_categories,special_ad_category_country", "limit": "500"})
    time.sleep(1.0)
    src = [c for c in camps if fragment in (c.get("name") or "")]
    src.sort(key=lambda c: not (c.get("name") or "").startswith("🌟"))   # prefer the 🌟 sold chain
    if not src:
        raise RuntimeError(f"old MY has no campaign matching «{fragment}»")
    camp = src[0]
    asets = g._get_all(camp["id"] + "/adsets", {"fields": "id,name,targeting", "limit": "10"})
    time.sleep(1.0)
    if not asets or not asets[0].get("targeting"):
        raise RuntimeError(f"no targeting on «{camp.get('name')}»")
    t = dict(asets[0]["targeting"])
    for k in DROP_KEYS:
        t.pop(k, None)
    t["age_min"], t["age_max"] = 30, 65                          # 硬锁 30 起（owner 2026-09-11）
    t["targeting_automation"] = {"advantage_audience": 0}        # 兴趣组 = 硬锁，不给 Meta 放宽
    if locales and not t.get("locales"):
        t["locales"] = locales
    return t, camp


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None
    locales = s.meta.targeting.locales
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"MY 5.0 build on {acct} · 3 × (CBO RM{DAILY/100:.0f} · 1 adset PAUSED · 5 post-reuse ads) — {mode}\n")

    # ── gate 0: ban list on every ad name ───────────────────────────────────
    hits = compliance.filter_banned([n for n, _p in ADS], s.compliance.banned_creatives)
    if hits:
        print(f"⛔ 禁跑命中，停：{hits}")
        return

    # ── gate 1: account alive + posts readable ───────────────────────────────
    info = g._request("GET", acct, params={"fields": "name,account_status,disable_reason,currency"})
    print(f"账户 «{info.get('name')}» status={info.get('account_status')} {info.get('currency')}")
    if info.get("account_status") != 1:
        print("⛔ 账户不是 ACTIVE，停"); return
    for name, post in ADS:
        try:
            p = g._request("GET", post, params={"fields": "id,created_time"})
            print(f"  post ✓ «{name[:28]}» {post} (建 {(p.get('created_time') or '')[:10]})")
        except Exception as exc:                                   # noqa: BLE001
            print(f"  post ? «{name[:28]}» {post} — 读不到（{str(exc)[:80]}），建的时候再看 Meta 接不接受")
        time.sleep(0.6)
    print()

    # ── targeting specs ──────────────────────────────────────────────────────
    specs = {}
    for camp_name, aset_name, frag in BUILDS:
        if frag:
            t, src_camp = clone_targeting(g, frag, locales)
            cats = src_camp.get("special_ad_categories") or []
            cat_country = src_camp.get("special_ad_category_country") or []
            print(f"▶ «{camp_name}»  targeting cloned from «{src_camp.get('name')}»"
                  f"  special={cats} country={cat_country}")
        else:
            t = {"geo_locations": {"countries": s.meta.targeting.countries},
                 "age_range": [30, 65], "targeting_automation": {"advantage_audience": 1}}
            if locales:
                t["locales"] = locales
            cats, cat_country = list(s.meta.special_ad_categories), []
            print(f"▶ «{camp_name}»  Broad Adv+ ON · age_range 30-65 · special={cats}")
        print("   " + json.dumps(t, ensure_ascii=False)[:600])
        specs[camp_name] = (t, cats, cat_country)
    print()

    if not CONFIRM:
        print("DRY RUN — 以上就是会建的东西；CONFIRM=true 才动手。")
        return

    camps_now = g._get_all(acct + "/campaigns", {"fields": "id,name", "limit": "100"})
    time.sleep(1.0)
    for camp_name, aset_name, _frag in BUILDS:
        t, cats, cat_country = specs[camp_name]
        try:
            camp_id = next((c["id"] for c in camps_now if (c.get("name") or "") == camp_name), None)
            if camp_id:
                print(f"  · campaign exists ({camp_id}) — filling gaps")
            else:
                kw = dict(name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
                          daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                          special_ad_categories=cats, status="ACTIVE")
                if cat_country:
                    kw["special_ad_category_country"] = cat_country
                camp_id = g.create_campaign(acct, **kw)["id"]
                print(f"  ✓ campaign {camp_id} «{camp_name}» CBO RM{DAILY/100:.0f} (ACTIVE; adset gate below)")
                time.sleep(PACE)

            asets = g._get_all(camp_id + "/adsets", {"fields": "id,name", "limit": "10"})
            time.sleep(1.0)
            aset_id = next((x["id"] for x in asets if (x.get("name") or "") == aset_name), None)
            if not aset_id:
                aset_id = g.create_adset(
                    acct, name=aset_name, campaign_id=camp_id,
                    optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                    promoted_object=s.meta.promoted_object, targeting=t, status="PAUSED")["id"]
                print(f"  ✓ adset {aset_id} «{aset_name}» (PAUSED gate)")
                time.sleep(PACE)

            have = {N(a.get("name") or "") for a in g._get_all(camp_id + "/ads", {"fields": "name", "limit": "50"})}
            time.sleep(1.0)
            for name, post in ADS:
                if N(name) in have:
                    continue
                spec = {"name": f"MY5 | {name}", "object_story_id": post}
                if s.meta.url_tags:
                    spec["url_tags"] = s.meta.url_tags
                cr = g.create_adcreative(acct, **spec)
                ad = g.create_ad(acct, name=name, adset_id=aset_id,
                                 creative={"creative_id": cr["id"]}, status="ACTIVE",
                                 conversion_domain=conv)
                print(f"  ✓ ad {ad['id']} «{name}»")
                time.sleep(PACE)
        except Exception as exc:                                   # noqa: BLE001
            print(f"  ❌ «{camp_name}» 停在：{str(exc)[:220]}")
        print()
    print("MY5 BUILD DONE — 3 campaigns CBO RM100 ACTIVE / adsets PAUSED，owner 审后自行开启。")


if __name__ == "__main__":
    main()
