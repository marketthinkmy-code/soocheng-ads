# -*- coding: utf-8 -*-
"""owner 2026-10-20「帮我建 TRAVEL 的 1-1-5 for MY」— one Webinarkit campaign on MY 5.0:
«(Webinarkit) STOCKBLOOM | TRAVEL MY | 1-1-5 | 1020», CBO RM50 (same as the other MY chains), created PAUSED
(owner activates). One ad set «Travel | MY 28+»: the travel interests of the SG TRAVEL ad set, geo MY, age 28-65
hard, Advantage+ OFF; optimizes «WED WEBINARKIT REGISTER» (1048291251556714); MALAYSIA_UNIVERSAL verified
advertiser copied from a running MY Webinarkit ad set. 5 ads reusing the exact creatives already approved in the
MY BUSINESS OWNER Webinarkit ad set (headline versions + owner's korea post). Ban gate. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NAME = "(Webinarkit) STOCKBLOOM | TRAVEL MY | 1-1-5 | 1020"
ASET = "Travel | MY 28+"
DAILY = 5000
SRC_MY_SET = "120251454700740329"      # MY BUSINESS OWNER Webinarkit ad set (creatives + promoted object + regional)
SG_ACCT = "act_893025326577600"
WANT = ["Video：盖电脑，喂！", "Video：年纪大的人做不了交易？", "Video：赚美金，一定要接美国客户？", "freestyle: korea", "Video：用我的方法"]


def main() -> None:
    my = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(my)
    acct = my.meta.account_path
    print(f"TRAVEL MY build — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    assert not compliance.filter_banned(WANT, my.compliance.banned_creatives), "banned"
    src = g.get_object(SRC_MY_SET, "promoted_object,regional_regulated_categories,regional_regulation_identities,targeting")
    ads = g._get_all(SRC_MY_SET + "/ads", {"fields": "name,status,creative{id}", "limit": "20"})
    cr = {}
    for a in ads:
        if a["name"] in WANT and a["name"] not in cr:
            cr[a["name"]] = a["creative"]["id"]
    missing = [w for w in WANT if w not in cr]
    assert not missing, f"creatives missing in source set: {missing}"
    print("  creatives:", cr)
    print("  promoted:", {k: v for k, v in src["promoted_object"].items() if k != "pixel_rule"})
    # travel interests from the SG TRAVEL ad set
    camps = g._get_all(SG_ACCT + "/campaigns", {"fields": "id,name,created_time", "limit": "300"})
    trav = sorted([c for c in camps if "| TRAVEL |" in c["name"] and "webinar" not in c["name"].lower()],
                  key=lambda c: c.get("created_time") or "", reverse=True)
    flex = None
    for c in trav:
        sets = g._get_all(c["id"] + "/adsets", {"fields": "targeting", "limit": "5"}); time.sleep(0.5)
        if sets and (sets[0]["targeting"].get("flexible_spec")):
            flex, src_name = sets[0]["targeting"]["flexible_spec"], c["name"]; break
    assert flex, "no SG travel interests found"
    names = [i["name"] for spec in flex for i in (spec.get("interests") or [])] + \
            [b["name"] for spec in flex for b in (spec.get("behaviors") or [])]
    print(f"  interests from «{src_name}» ({len(names)}): {names}")
    t0 = src["targeting"]
    t = {"geo_locations": t0["geo_locations"], "locales": t0.get("locales"), "flexible_spec": flex,
         "age_min": 28, "age_max": 65, "targeting_automation": {"advantage_audience": 0}}
    t = {k: v for k, v in t.items() if v is not None}
    print(f"  geo {t['geo_locations']} · age 28-65 hard · adv+ off · CBO RM{DAILY // 100}")
    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。\nTRAVEL DONE (dry-run)"); return
    c = g.create_campaign(acct, name=NAME, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                          daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP", buying_type="AUCTION")
    time.sleep(2)
    a = g.create_adset(acct, name=ASET, campaign_id=c["id"], status="ACTIVE", optimization_goal="OFFSITE_CONVERSIONS",
                       billing_event="IMPRESSIONS", targeting=t, promoted_object=src["promoted_object"],
                       attribution_spec=[{"event_type": "CLICK_THROUGH", "window_days": 7}],
                       regional_regulated_categories=src["regional_regulated_categories"],
                       regional_regulation_identities=src["regional_regulation_identities"])
    time.sleep(2)
    ids = []
    for w in WANT:
        ids.append(g.create_ad(acct, name=w, adset_id=a["id"], creative={"creative_id": cr[w]}, status="ACTIVE")["id"]); time.sleep(2)
    print(f"  ✅ {NAME}: campaign {c['id']} (PAUSED, RM{DAILY // 100}) · adset {a['id']} · ads {ids}")
    print("TRAVEL DONE")


if __name__ == "__main__":
    main()
