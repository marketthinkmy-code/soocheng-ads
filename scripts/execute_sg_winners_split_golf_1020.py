# -*- coding: utf-8 -*-
"""owner 2026-10-20「拆」— split SG WINNERS Golf: «我只有一个目的» moves to its own ad set «Golf · 我只有一个目的 | SG 28+»
(RM50, same targeting / promoted object / regional); its ad in the original set is paused; the original becomes
«Golf · 盖电脑 | SG 28+»; campaign name → 1-5-5. CONFIRM=true writes."""
from __future__ import annotations

import os
import re
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CAMP = "120249964890710521"
SRC = "120249964893910521"
O = "Video：我只有一个目的"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    a = g.get_object(SRC, "name,campaign_id,targeting,promoted_object,optimization_goal,billing_event,bid_strategy,"
                          "attribution_spec,regional_regulated_categories,regional_regulation_identities")
    c = g.get_object(CAMP, "name")
    ads = g._get_all(SRC + "/ads", {"fields": "id,name,status,creative{id}", "limit": "10"})
    oad = next(x for x in ads if x["name"] == O)
    print(f"  «{c['name']}» · «{a['name']}» ads {[x['name'] for x in ads]}")
    assert a["campaign_id"] == CAMP
    if not CONFIRM:
        print("DRY RUN"); return
    n = g.create_adset(acct, name="Golf · 我只有一个目的 | SG 28+", campaign_id=CAMP, status="ACTIVE", daily_budget=5000,
                       bid_strategy=a.get("bid_strategy") or "LOWEST_COST_WITHOUT_CAP", optimization_goal=a["optimization_goal"],
                       billing_event=a["billing_event"], targeting=a["targeting"], promoted_object=a["promoted_object"],
                       attribution_spec=a.get("attribution_spec"), regional_regulated_categories=a["regional_regulated_categories"],
                       regional_regulation_identities=a["regional_regulation_identities"])
    time.sleep(2)
    ad = g.create_ad(acct, name=O, adset_id=n["id"], creative={"creative_id": oad["creative"]["id"]}, status="ACTIVE")
    time.sleep(1)
    g.update_status(oad["id"], "PAUSED"); time.sleep(1)
    g._request("POST", SRC, data={"name": "Golf · 盖电脑 | SG 28+"}); time.sleep(1)
    g._request("POST", CAMP, data={"name": re.sub(r"\| 1-\d+-\d+ \|", "| 1-5-5 |", c["name"])}); time.sleep(2)
    sets = g._get_all(CAMP + "/adsets", {"fields": "name,daily_budget,status", "limit": "10"})
    print(f"  ✅ new adset {n['id']} · ad {ad['id']} · paused old ad {oad['id']}")
    print(f"  ✅ «{g.get_object(CAMP, 'name')['name']}» · " + ", ".join(f"{x['name']} RM{int(x['daily_budget']) // 100}" for x in sets))
    print("GOLF SPLIT DONE")


if __name__ == "__main__":
    main()
