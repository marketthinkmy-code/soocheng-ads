# -*- coding: utf-8 -*-
"""owner 2026-10-22「第三步，我同意」— MY WINNERS (mirror of SG WINNERS): ABO campaign
«(Webinarkit) STOCKBLOOM | WINNERS MY | 1-3-3 | 1022», created PAUSED (owner activates); 3 single-creative ad sets
× RM50 so Meta can't starve the creative inside a pool — 盖电脑 (top seller, RM28 spend in MY pools), korea, 赚美金.
Targeting = the BROAD MY Webinarkit ad set (Advantage+ broad, age 28+ suggestion); promoted object + regional from
it; creatives = the approved ones in MY BUSINESS OWNER. Ban gate. Idempotent by name. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NAME = "(Webinarkit) STOCKBLOOM | WINNERS MY | 1-3-3 | 1022"
SRC_BROAD_SET = "120251454705570329"
SRC_CREATIVES_SET = "120251454700740329"
SETS = [("Broad · 盖电脑 | MY 28+", "Video：盖电脑，喂！"), ("Broad · korea | MY 28+", "freestyle: korea"),
        ("Broad · 赚美金 | MY 28+", "Video：赚美金，一定要接美国客户？")]
DAILY = 5000


def main() -> None:
    my = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(my)
    acct = my.meta.account_path
    print(f"MY WINNERS build — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    assert not compliance.filter_banned([w for _, w in SETS], my.compliance.banned_creatives), "banned"
    src = g.get_object(SRC_BROAD_SET, "name,promoted_object,regional_regulated_categories,regional_regulation_identities,targeting")
    t = src["targeting"]
    print(f"  targeting from «{src['name']}»: age {t.get('age_min')}-{t.get('age_max')} · age_range {t.get('age_range')} · "
          f"adv+ {(t.get('targeting_automation') or {}).get('advantage_audience')} · geo {t.get('geo_locations', {}).get('countries')}")
    cr = {}
    for a in g._get_all(SRC_CREATIVES_SET + "/ads", {"fields": "name,creative{id}", "limit": "20"}):
        cr.setdefault(a["name"], a["creative"]["id"])
    assert all(w in cr for _, w in SETS), "creative missing"
    camps = {c["name"]: c["id"] for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "200"})}
    print(f"  creatives {[(w, cr[w]) for _, w in SETS]} · exists {NAME in camps}")
    if not CONFIRM or NAME in camps:
        print("\nWINNERS MY DONE (dry-run / exists)"); return
    c = g.create_campaign(acct, name=NAME, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                          is_adset_budget_sharing_enabled=False, buying_type="AUCTION")
    time.sleep(2)
    for sname, w in SETS:
        a = g.create_adset(acct, name=sname, campaign_id=c["id"], status="ACTIVE", daily_budget=DAILY,
                           bid_strategy="LOWEST_COST_WITHOUT_CAP", optimization_goal="OFFSITE_CONVERSIONS",
                           billing_event="IMPRESSIONS", targeting=t, promoted_object=src["promoted_object"],
                           attribution_spec=[{"event_type": "CLICK_THROUGH", "window_days": 7}],
                           regional_regulated_categories=src["regional_regulated_categories"],
                           regional_regulation_identities=src["regional_regulation_identities"])
        time.sleep(2)
        ad = g.create_ad(acct, name=w, adset_id=a["id"], creative={"creative_id": cr[w]}, status="ACTIVE")
        print(f"  ✅ «{sname}» {a['id']} RM{DAILY // 100} · ad {ad['id']}")
        time.sleep(2)
    print(f"  ✅ {NAME}: campaign {c['id']} (PAUSED, ABO 3×RM{DAILY // 100})\nWINNERS MY DONE")


if __name__ == "__main__":
    main()
