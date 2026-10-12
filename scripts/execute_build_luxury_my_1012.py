# -*- coding: utf-8 -*-
"""owner 2026-10-12「我想照你刚刚建议的做」— new MY 5.0 campaign for the 14/10 live scale-up:

  «STOCKBLOOM | LUXURY MY | 1-1-4 | 1012»  CBO RM100 · 1 adset «Luxury | MY 28+» (PAUSED gate) · 4 post-reuse ads
  audience = the old account's best-CPA interest sets (CLAUDE.md: Luxury Goods · Beer/Alcohol · Omakase/Wagyu),
  cloned from the disabled 3.0 account's ad sets and merged into ONE interest group; age 28-65 hard-locked,
  Advantage+ audience OFF, old-account custom audiences stripped. Fallback: interest search if a set is missing.
  Ads: 盖电脑 · korea · 年纪大 · 赚美金 (NOT 不选 forex). Same mechanics as execute_build_my5_1008.py:
  campaign ACTIVE + adset PAUSED gate = 0 spend until the owner flips it; reviews run while paused.
Dry-run unless CONFIRM=true."""
from __future__ import annotations

import json
import os
import time

from adbot import compliance, cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 5.0
DAILY = 10000
OLD_MY = "act_759339046918885"
N = cpa.norm
CAMP_NAME = "STOCKBLOOM | LUXURY MY | 1-1-4 | 1012"
ASET_NAME = "Luxury | MY 28+"
SOURCES = ("LUXURY", "BEER", "OMAKASE")          # old-MY campaign-name fragments (case-insensitive)
SEARCH_FALLBACK = {"LUXURY": "Luxury goods", "BEER": "Beer", "OMAKASE": "Omakase"}
ADS = [
    ("Video：盖电脑，喂！",            "1001334883061622_1788611461813837"),
    ("Video：freestyle korea",        "1001334883061622_122109881127286543"),
    ("Video：年纪大的人做不了交易？",   "1001334883061622_122120962899286543"),
    ("Video：赚美金，一定要接美国客户？", "1001334883061622_122120277969286543"),
]
DROP_KEYS = ("custom_audiences", "excluded_custom_audiences", "age_range", "genders",
             "targeting_optimization", "targeting_relaxation_types", "publisher_platforms",
             "facebook_positions", "instagram_positions", "messenger_positions",
             "audience_network_positions", "device_platforms", "user_os", "flexible_spec",
             "exclusions", "interests", "behaviors", "work_positions", "work_employers")


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None
    locales = s.meta.targeting.locales
    print(f"LUXURY MY build on {acct} — {'APPLY' if CONFIRM else 'DRY-RUN'}\n")

    hits = compliance.filter_banned([n for n, _p in ADS], s.compliance.banned_creatives)
    if hits:
        print(f"⛔ 禁跑命中，停：{hits}"); return
    info = g._request("GET", acct, params={"fields": "name,account_status,disable_reason,currency"})
    print(f"账户 «{info.get('name')}» status={info.get('account_status')} {info.get('currency')}")
    if info.get("account_status") != 1:
        print("⛔ 账户不是 ACTIVE，停"); return

    # ── interests: clone from the old account's Luxury / Beer / Omakase sets ───────────
    camps_old = g._get_all(OLD_MY + "/campaigns", {
        "fields": "id,name,special_ad_categories,special_ad_category_country", "limit": "500"})
    time.sleep(1.0)
    base, cats, cat_country = None, list(s.meta.special_ad_categories), []
    groups: dict = {}          # interest id -> name
    found = []
    for frag in SOURCES:
        src = [c for c in camps_old if frag in (c.get("name") or "").upper()]
        src.sort(key=lambda c: not (c.get("name") or "").startswith("🌟"))
        if not src:
            print(f"  old MY: no campaign matching «{frag}» — will search interests instead")
            continue
        camp = src[0]
        asets = g._get_all(camp["id"] + "/adsets", {"fields": "id,name,targeting", "limit": "10"})
        time.sleep(0.8)
        t = (asets[0].get("targeting") if asets else None) or {}
        ints = []
        for fs in t.get("flexible_spec") or []:
            ints += fs.get("interests") or []
        ints += t.get("interests") or []
        print(f"  «{camp.get('name')}» → {len(ints)} interests: " + ", ".join(i.get("name", "?") for i in ints)[:300])
        for i in ints:
            groups[i["id"]] = i.get("name", "")
        if base is None and t:
            base = dict(t)
            cats = camp.get("special_ad_categories") or cats
            cat_country = camp.get("special_ad_category_country") or []
        found.append(frag)
    for frag in SOURCES:
        if frag in found:
            continue
        q = SEARCH_FALLBACK[frag]
        res = g._get_all("search", {"type": "adinterest", "q": q, "limit": "5"})
        time.sleep(0.8)
        print(f"  search «{q}»: " + " · ".join(f"{r.get('name')} ({r.get('id')}, {r.get('audience_size_upper_bound', '?')})" for r in res[:5]))
        if res:
            groups[res[0]["id"]] = res[0].get("name", "")
    if not groups:
        print("⛔ 没有任何兴趣可用，停"); return

    t = dict(base or {})
    for k in DROP_KEYS:
        t.pop(k, None)
    t["geo_locations"] = {"countries": s.meta.targeting.countries}
    t["flexible_spec"] = [{"interests": [{"id": i, "name": n} for i, n in groups.items()]}]
    t["age_min"], t["age_max"] = 28, 65
    t["targeting_automation"] = {"advantage_audience": 0}
    if locales and not t.get("locales"):
        t["locales"] = locales
    print(f"\n▶ «{CAMP_NAME}» / «{ASET_NAME}»  special={cats} country={cat_country}")
    print("   " + json.dumps(t, ensure_ascii=False)[:900])
    print(f"   ads: {[n for n, _p in ADS]}\n")

    if not CONFIRM:
        print("DRY RUN — 以上就是会建的东西；CONFIRM=true 才动手。")
        print("LUXURY MY BUILD DONE (dry-run)")
        return

    camps_now = g._get_all(acct + "/campaigns", {"fields": "id,name", "limit": "100"})
    time.sleep(1.0)
    camp_id = next((c["id"] for c in camps_now if (c.get("name") or "") == CAMP_NAME), None)
    if camp_id:
        print(f"  · campaign exists ({camp_id}) — filling gaps")
    else:
        kw = dict(name=CAMP_NAME, objective="OUTCOME_SALES", buying_type="AUCTION",
                  daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                  special_ad_categories=cats, status="ACTIVE")
        if cat_country:
            kw["special_ad_category_country"] = cat_country
        camp_id = g.create_campaign(acct, **kw)["id"]
        print(f"  ✓ campaign {camp_id} «{CAMP_NAME}» CBO RM{DAILY/100:.0f} (ACTIVE; adset gate below)")
        time.sleep(PACE)
    asets = g._get_all(camp_id + "/adsets", {"fields": "id,name", "limit": "10"})
    time.sleep(1.0)
    aset_id = next((x["id"] for x in asets if (x.get("name") or "") == ASET_NAME), None)
    if not aset_id:
        aset_id = g.create_adset(
            acct, name=ASET_NAME, campaign_id=camp_id,
            optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
            promoted_object=s.meta.promoted_object, targeting=t, status="PAUSED")["id"]
        print(f"  ✓ adset {aset_id} «{ASET_NAME}» (PAUSED gate)")
        time.sleep(PACE)
    have = {N(a.get("name") or "") for a in g._get_all(camp_id + "/ads", {"fields": "name", "limit": "50"})}
    time.sleep(1.0)
    for name, post in ADS:
        if N(name) in have:
            print(f"  · ad exists «{name}»"); continue
        spec = {"name": f"MY5 | {name} @ LUXURY", "object_story_id": post}
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        try:
            cr = g.create_adcreative(acct, **spec)
            ad = g.create_ad(acct, name=name, adset_id=aset_id,
                             creative={"creative_id": cr["id"]}, status="ACTIVE", conversion_domain=conv)
            print(f"  ✓ ad {ad['id']} «{name}»")
        except Exception as exc:                                   # noqa: BLE001
            print(f"  ❌ ad «{name}» 停在：{str(exc)[:220]}")
        time.sleep(PACE)
    print("\nLUXURY MY BUILD DONE — campaign ACTIVE / adset PAUSED，owner 审后自行开启（或讲「开」）。")


if __name__ == "__main__":
    main()
