# -*- coding: utf-8 -*-
"""owner 2026-10-20「建」— SG «WINNERS» Webinarkit campaign from the 90-day pattern read:
ABO (each ad set owns its budget so Meta can't starve the high-CPA-quality creatives), 3 ad sets × RM50:
  TRAVEL     → 盖电脑 only          (90d TRAVEL × 盖电脑: RM2,755 · 6 sales · CPA ~459)
  GOLF       → 我只有一个目的 + 盖电脑 (GOLF CPA 721; 我只有一个目的 CPA 634)
  INVESTMENT → 用我的方法 + 盖电脑    (INVESTMENT CPA 732)
Interests cloned from the latest SG ad set of each family; geo SG; age 28-65 hard; Advantage+ off; optimizes
«WED WEBINARKIT REGISTER (SG)» 1614065190214320; SINGAPORE_UNIVERSAL verified advertiser copied from a running
Webinarkit ad set. Creatives: the approved SG Webinarkit headline creatives (盖电脑 / 用我的方法); 我只有一个目的 gets a
new creative from its SG dark-post video + caption, link → -wed, same headline. Campaign created PAUSED.
Ban gate. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NAME = "(Webinarkit) [SG] STOCKBLOOM | WINNERS | 1-3-4 | 1020"
SRC_SET = "120249918195680521"          # SG LUXURY GOODS Webinarkit ad set (headline creatives, promoted object, regional)
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
HEADLINE = "🚨 教你如何在 1️⃣ 分钟内，判读市场节奏"
PAGE, IG = "1001334883061622", "17841480427751602"
G, M, O = "Video：盖电脑，喂！", "Video：用我的方法", "Video：我只有一个目的"
# GOLF starts with 盖电脑 only: 我只有一个目的 has no dark post anywhere — owner adds it by hand
SETS = [("TRAVEL", "Travel | SG 28+", [G]), ("GOLF", "Golf | SG 28+", [G]), ("INVESTMENT", "Investment | SG 28+", [M, G])]
DAILY = 5000


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    print(f"SG WINNERS build — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    assert not compliance.filter_banned([G, M], s.compliance.banned_creatives), "banned"
    src = g.get_object(SRC_SET, "promoted_object,regional_regulated_categories,regional_regulation_identities")
    cr = {}
    for a in g._get_all(SRC_SET + "/ads", {"fields": "name,creative{id,url_tags,object_story_spec}", "limit": "20"}):
        if a["name"] in (G, M):
            vd = ((a["creative"].get("object_story_spec") or {}).get("video_data") or {})
            if vd.get("title") == HEADLINE:
                cr[a["name"]] = a["creative"]["id"]
                url_tags = a["creative"].get("url_tags")
    assert G in cr and M in cr, f"headline creatives not found: {cr}"
    # 我只有一个目的: dark-post video + caption from the SG account
    print(f"  creatives: {cr} · url_tags {url_tags}")
    # targeting per family
    camps = g._get_all(acct + "/campaigns", {"fields": "id,name,created_time", "limit": "300"})
    plan = []
    for fam, aset_name, ads_ in SETS:
        cands = sorted([c for c in camps if fam in c["name"].upper() and "webinar" not in c["name"].lower()],
                       key=lambda c: c.get("created_time") or "", reverse=True)
        t0 = None
        for c in cands:
            sets = g._get_all(c["id"] + "/adsets", {"fields": "targeting", "limit": "5"}); time.sleep(0.5)
            for st in sets:
                if (st.get("targeting") or {}).get("flexible_spec"):
                    t0, src_name = st["targeting"], c["name"]; break
            if t0:
                break
        assert t0, f"{fam}: no interest ad set found"
        t = {"geo_locations": t0["geo_locations"], "flexible_spec": t0["flexible_spec"], "age_min": 28, "age_max": 65,
             "targeting_automation": {"advantage_audience": 0}}
        if t0.get("locales"):
            t["locales"] = t0["locales"]
        names = [i["name"] for sp in t0["flexible_spec"] for i in (sp.get("interests") or []) + (sp.get("behaviors") or [])]
        print(f"  {fam}: from «{src_name}» · {len(names)} interests: {names[:12]}{' …' if len(names) > 12 else ''} · ads {ads_}")
        plan.append((aset_name, t, ads_))
    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。\nWINNERS DONE (dry-run)"); return
    c = g.create_campaign(acct, name=NAME, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                          buying_type="AUCTION", is_adset_budget_sharing_enabled=False)
    time.sleep(2)
    for aset_name, t, ads_ in plan:
        a = g.create_adset(acct, name=aset_name, campaign_id=c["id"], status="ACTIVE", daily_budget=DAILY,
                           bid_strategy="LOWEST_COST_WITHOUT_CAP", optimization_goal="OFFSITE_CONVERSIONS",
                           billing_event="IMPRESSIONS", targeting=t, promoted_object=src["promoted_object"],
                           attribution_spec=[{"event_type": "CLICK_THROUGH", "window_days": 7}],
                           regional_regulated_categories=src["regional_regulated_categories"],
                           regional_regulation_identities=src["regional_regulation_identities"])
        time.sleep(2)
        ids = [g.create_ad(acct, name=n, adset_id=a["id"], creative={"creative_id": cr[n]}, status="ACTIVE")["id"] for n in ads_]
        print(f"  ✅ {aset_name}: adset {a['id']} RM{DAILY // 100} · ads {ids}"); time.sleep(2)
    print(f"  campaign {c['id']} «{NAME}» PAUSED")
    print("WINNERS DONE")


if __name__ == "__main__":
    main()
