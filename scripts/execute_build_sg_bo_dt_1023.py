# -*- coding: utf-8 -*-
"""owner 2026-10-23「建」— two new SG Webinarkit campaigns copying MY 5.0's two best audiences (CPL 28 each):
«(Webinarkit) [SG] STOCKBLOOM | BUSINESS OWNER SG | 1-1-5 | 1023» and «… | DAY TRADING SG | 1-1-5 | 1023», CBO RM60 each,
created PAUSED (owner activates). Ad set interests = the MY BUSINESS OWNER / DAY TRADING Webinarkit ad sets'
flexible_spec; geo/locales = SG LAL ad set; age 28-65 hard, Advantage+ off; promoted object (SG custom conversion) +
SINGAPORE_UNIVERSAL from SG WINNERS Investment. 5 ads reusing SG-approved creatives: 用我的方法 · 盖电脑 · 不选 forex ·
我跟你讲 · 我只有一个目的 (不选 forex is SG-only — never MY). No Financial special category (owner 10/15). Ban gate.
Idempotent by name. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
DAILY = 6000
BUILDS = [("(Webinarkit) [SG] STOCKBLOOM | BUSINESS OWNER SG | 1-1-5 | 1023", "Business Owner | SG 28+", "120251454700740329"),
          ("(Webinarkit) [SG] STOCKBLOOM | DAY TRADING SG | 1-1-5 | 1023", "Day Trading | SG 28+", "120251454714430329")]
SG_LAL_SET = "120249918199040521"
SG_PROMO_SET = "120249964897130521"
CREATIVES = {"Video：用我的方法": None, "Video：盖电脑，喂！": None, "Video：不选 forex 不选黄金": None,
             "Video：我跟你讲！": "1104962755787873", "Video：我只有一个目的": "3149055588633786"}


def main() -> None:
    sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(sg)
    acct = sg.meta.account_path
    assert acct.endswith("893025326577600")
    print(f"SG BO/DT build — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    assert not compliance.filter_banned(list(CREATIVES), sg.compliance.banned_creatives), "banned"
    for x in g._get_all(SG_LAL_SET + "/ads", {"fields": "name,creative{id}", "limit": "20"}):
        if x["name"] in CREATIVES and not CREATIVES[x["name"]]:
            CREATIVES[x["name"]] = x["creative"]["id"]
    assert all(CREATIVES.values()), f"creative missing {CREATIVES}"
    print("  creatives:", CREATIVES)
    geo = g.get_object(SG_LAL_SET, "targeting")["targeting"]
    promo = g.get_object(SG_PROMO_SET, "promoted_object,optimization_goal,billing_event,attribution_spec,"
                                       "regional_regulated_categories,regional_regulation_identities")
    my = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
    camps = {c["name"]: c["id"] for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "300"})}
    for cname, sname, my_set in BUILDS:
        flex = my.get_object(my_set, "targeting")["targeting"].get("flexible_spec")
        assert flex, f"no interests on {my_set}"
        names = [i["name"] for spec in flex for k in ("interests", "behaviors", "work_positions", "industries") for i in (spec.get(k) or [])]
        t = {"geo_locations": geo["geo_locations"], "locales": geo.get("locales"), "flexible_spec": flex,
             "age_min": 28, "age_max": 65, "targeting_automation": {"advantage_audience": 0}}
        t = {k: v for k, v in t.items() if v is not None}
        print(f"\n  «{cname}» exists {cname in camps} · geo {t['geo_locations'].get('countries')} · {len(names)} interests: {names}")
        if not CONFIRM or cname in camps:
            continue
        c = g.create_campaign(acct, name=cname, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                              daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP", buying_type="AUCTION")
        time.sleep(2)
        a = g.create_adset(acct, name=sname, campaign_id=c["id"], status="ACTIVE", optimization_goal=promo["optimization_goal"],
                           billing_event=promo["billing_event"], targeting=t, promoted_object=promo["promoted_object"],
                           attribution_spec=promo.get("attribution_spec"),
                           regional_regulated_categories=promo["regional_regulated_categories"],
                           regional_regulation_identities=promo["regional_regulation_identities"])
        time.sleep(2)
        ids = []
        for n, cr in CREATIVES.items():
            ids.append(g.create_ad(acct, name=n, adset_id=a["id"], creative={"creative_id": cr}, status="ACTIVE")["id"]); time.sleep(2)
        print(f"  ✅ campaign {c['id']} (PAUSED, RM{DAILY // 100}) · adset {a['id']} · ads {ids}")
    print("\nSG BO/DT DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
