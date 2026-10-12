# -*- coding: utf-8 -*-
"""READ-ONLY: what does a running SG ad set / ad creative carry for Singapore's regulated-advertiser requirement?
Probes candidate ad-set fields one by one (unknown names 400 individually) on the 0911 HOOK 重拍 ad set and prints
the creative's regional_regulation_identities. No PII."""
from __future__ import annotations

import json
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CANDS = ["regional_regulated_categories", "dsa_beneficiary", "dsa_payor", "regulated_categories", "advertiser",
         "verified_advertiser", "rrc_advertiser", "regional_regulation_identities", "contextual_bundling_spec",
         "is_dynamic_creative", "destination_type", "attribution_spec", "bid_strategy", "optimization_goal",
         "promoted_object", "daily_min_spend_target", "learning_stage_info", "issues_info", "configured_status",
         "multi_optimization_goal_weight", "optimization_sub_event", "targeting_optimization_types", "review_feedback",
         "creative_sequence", "frequency_control_specs", "existing_customer_budget_percentage", "bid_amount"]


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    camps = [c for c in g._get_all(acct + "/campaigns", {"fields": "id,name,status", "limit": "300"}) if "0911 HOOK" in (c.get("name") or "")]
    sets = g._get_all(camps[0]["id"] + "/adsets", {"fields": "id,name,status", "limit": "5"})
    aset = next(a for a in sets if a.get("status") == "ACTIVE")
    print(f"probing adset {aset['id']} «{aset.get('name')}»")
    found = {}
    for f in CANDS:
        try:
            r = g.get_object(aset["id"], f)
            found[f] = r.get(f)
            print(f"  ✓ {f} = {json.dumps(r.get(f), ensure_ascii=False)[:300]}")
        except Exception as exc:                                   # noqa: BLE001
            print(f"  ✗ {f}: {str(exc)[:90]}")
        time.sleep(0.4)
    ads = g._get_all(aset["id"] + "/ads", {"fields": "id,name,status,creative{id,name,object_story_id,effective_object_story_id}", "limit": "10"})
    for a in ads:
        cr = (a.get("creative") or {})
        print(f"\nad «{a.get('name')}» {a.get('status')} creative {cr.get('id')}")
        for f in ["regional_regulation_identities", "authorization_category", "contextual_multi_ads", "degrees_of_freedom_spec", "object_story_spec"]:
            try:
                r = g.get_object(cr["id"], f)
                print(f"  ✓ creative.{f} = {json.dumps(r.get(f), ensure_ascii=False)[:400]}")
            except Exception as exc:                               # noqa: BLE001
                print(f"  ✗ creative.{f}: {str(exc)[:90]}")
            time.sleep(0.4)
    # the campaign too
    for f in ["special_ad_categories", "special_ad_category_country", "is_adset_budget_sharing_enabled", "advantage_state_info"]:
        try:
            r = g.get_object(camps[0]["id"], f)
            print(f"  ✓ campaign.{f} = {json.dumps(r.get(f), ensure_ascii=False)[:200]}")
        except Exception as exc:                                   # noqa: BLE001
            print(f"  ✗ campaign.{f}: {str(exc)[:90]}")
        time.sleep(0.4)
    print("ADSET FIELDS DONE (read-only)")


if __name__ == "__main__":
    main()
