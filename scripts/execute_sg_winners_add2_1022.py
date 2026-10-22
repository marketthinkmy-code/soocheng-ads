# -*- coding: utf-8 -*-
"""owner 2026-10-22「建」— SG WINNERS +2 single-creative ad sets (ABO RM50 each), created PAUSED inside the live
WINNERS campaign (owner activates):
  «LAL 5% · 盖电脑 | SG 28+»     — targeting/promoted/regional copied from the SG LAL 5% Webinarkit ad set, 盖电脑 creative from it
  «Investment · 我跟你讲 | SG 28+» — copied from WINNERS Investment (用我的方法) ad set, 我跟你讲 creative from BROAD SG
Only already-approved SG creatives (Webinarkit link + url_tags). Ban gate. Idempotent by name. Campaign name → 1-7-7.
CONFIRM=true writes."""
from __future__ import annotations

import os
import re
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CAMP = "120249964890710521"
F = ("name,targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
     "regional_regulated_categories,regional_regulation_identities")
PLAN = [  # (new ad set name, targeting source ad set, creative name, creative source ad set)
    ("LAL 5% · 盖电脑 | SG 28+", "120249918199040521", "Video：盖电脑，喂！", "120249918199040521"),
    ("Investment · 我跟你讲 | SG 28+", "120249964897130521", "Video：我跟你讲！", "120249918193310521"),
]


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    print(f"SG WINNERS +2 — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    assert not compliance.filter_banned([p[2] for p in PLAN], s.compliance.banned_creatives), "banned"
    have = {x["name"] for x in g._get_all(CAMP + "/adsets", {"fields": "name", "limit": "20"})}
    made = 0
    for name, tsrc, cname, csrc in PLAN:
        a = g.get_object(tsrc, F)
        t = a["targeting"]
        cad = next(x for x in g._get_all(csrc + "/ads", {"fields": "name,creative{id}", "limit": "20"}) if x["name"] == cname)
        print(f"  «{name}» ← targeting «{a['name']}» (age {t.get('age_min')}-{t.get('age_max')} · range {t.get('age_range')} · "
              f"adv+ {(t.get('targeting_automation') or {}).get('advantage_audience')} · CA {[c.get('name', c.get('id')) for c in t.get('custom_audiences', [])]}) "
              f"· creative {cad['creative']['id']} · exists {name in have}")
        if not CONFIRM or name in have:
            continue
        n = g.create_adset(acct, name=name, campaign_id=CAMP, status="PAUSED", daily_budget=5000,
                           bid_strategy="LOWEST_COST_WITHOUT_CAP", optimization_goal=a["optimization_goal"],
                           billing_event=a["billing_event"], targeting=t, promoted_object=a["promoted_object"],
                           attribution_spec=a.get("attribution_spec"),
                           regional_regulated_categories=a["regional_regulated_categories"],
                           regional_regulation_identities=a["regional_regulation_identities"])
        time.sleep(2)
        ad = g.create_ad(acct, name=cname, adset_id=n["id"], creative={"creative_id": cad["creative"]["id"]}, status="ACTIVE")
        print(f"    ✅ adset {n['id']} (PAUSED, RM50) · ad {ad['id']}")
        made += 1
        time.sleep(2)
    if CONFIRM and made:
        c = g.get_object(CAMP, "name")
        g._request("POST", CAMP, data={"name": re.sub(r"\| 1-\d+-\d+ \|", "| 1-7-7 |", c["name"])}); time.sleep(1)
        print(f"  ✅ «{g.get_object(CAMP, 'name')['name']}» · sets: " + ", ".join(
            f"{x['name']} {x['status']} RM{int(x.get('daily_budget') or 0) // 100}"
            for x in g._get_all(CAMP + "/adsets", {"fields": "name,status,daily_budget", "limit": "20"})))
    print("SG WINNERS ADD2 DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
