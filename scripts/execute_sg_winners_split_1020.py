# -*- coding: utf-8 -*-
"""owner 2026-10-20「1」— split the SG WINNERS Investment ad set so 盖电脑 and 用我的方法 each own RM50:
copy ad set 120249964897130521 → «Investment · 盖电脑 | SG 28+» (same targeting / promoted object / regional, RM50)
holding the 盖电脑 ad; pause the 盖电脑 ad in the original set and rename it «Investment · 用我的方法 | SG 28+»;
campaign name → 1-4-4. The campaign is still PAUSED (never delivered). CONFIRM=true writes."""
from __future__ import annotations

import os
import re
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CAMP = "120249964890710521"
SRC = "120249964897130521"
G = "Video：盖电脑，喂！"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    a = g.get_object(SRC, "name,campaign_id,daily_budget,targeting,promoted_object,optimization_goal,billing_event,"
                          "bid_strategy,attribution_spec,regional_regulated_categories,regional_regulation_identities")
    c = g.get_object(CAMP, "name,status")
    ads = g._get_all(SRC + "/ads", {"fields": "id,name,status,creative{id}", "limit": "10"})
    gad = next(x for x in ads if x["name"] == G)
    print(f"  campaign «{c['name']}» {c['status']} · source set «{a['name']}» RM{int(a['daily_budget']) // 100} · ads {[x['name'] for x in ads]}")
    assert a["campaign_id"] == CAMP and c["status"] == "PAUSED"
    if not CONFIRM:
        print("DRY RUN"); return
    n = g.create_adset(acct, name="Investment · 盖电脑 | SG 28+", campaign_id=CAMP, status="ACTIVE", daily_budget=5000,
                       bid_strategy=a.get("bid_strategy") or "LOWEST_COST_WITHOUT_CAP", optimization_goal=a["optimization_goal"],
                       billing_event=a["billing_event"], targeting=a["targeting"], promoted_object=a["promoted_object"],
                       attribution_spec=a.get("attribution_spec"), regional_regulated_categories=a["regional_regulated_categories"],
                       regional_regulation_identities=a["regional_regulation_identities"])
    time.sleep(2)
    ad = g.create_ad(acct, name=G, adset_id=n["id"], creative={"creative_id": gad["creative"]["id"]}, status="ACTIVE")
    time.sleep(1)
    g.update_status(gad["id"], "PAUSED"); time.sleep(1)
    g._request("POST", SRC, data={"name": "Investment · 用我的方法 | SG 28+"}); time.sleep(1)
    g._request("POST", CAMP, data={"name": re.sub(r"\| 1-\d+-\d+ \|", "| 1-4-4 |", c["name"])}); time.sleep(1)
    print(f"  ✅ new adset {n['id']} RM50 · ad {ad['id']} · paused old 盖电脑 ad {gad['id']}")
    print(f"  ✅ «{g.get_object(CAMP, 'name')['name']}» · sets: " +
          ", ".join(f"{x['name']} RM{int(x['daily_budget']) // 100}" for x in g._get_all(CAMP + "/adsets", {"fields": "name,daily_budget", "limit": "10"})))
    print("SPLIT DONE")


if __name__ == "__main__":
    main()
