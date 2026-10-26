# -*- coding: utf-8 -*-
"""owner 2026-10-26「建」— SG reach tests (30-day SG reach was only ~10.9k people at frequency 3.7, every ad set locked to
Chinese-UI locales [20,21,22]). Three new SG Webinarkit campaigns, CBO RM50 each, created PAUSED (owner activates):
  A «(Webinarkit) [SG] STOCKBLOOM | DAY TRADING SG · ALL LANG | 1-1-4 | 1026» — DAY TRADING SG's 23 interests, NO locale lock,
     age 28-65 hard, Advantage+ off;
  B «(Webinarkit) [SG] STOCKBLOOM | PURCHASE LAL 5% · ALL LANG | 1-1-4 | 1026» — the SG purchase LAL 5%, NO locale lock,
     age 28-65 hard, Advantage+ off;
  C «(Webinarkit) [SG] STOCKBLOOM | BROAD SG · ALL LANG | 1-1-4 | 1026» — SG only, no interests, no locale lock,
     Advantage+ audience ON with age_range [28,65] suggestion (CLAUDE.md age rule).
Promoted object (SG custom conversion) + SINGAPORE_UNIVERSAL from the live DAY TRADING SG ad set. 4 ads each, reusing SG-approved
creatives (用我的方法 · 不选 forex · 我跟你讲 · 盖电脑). No Financial special category (owner 10/15). Ban gate. Idempotent by name.
Dry-run prints the exact targeting. CONFIRM=true writes."""
from __future__ import annotations

import copy
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
DT_SET, LAL_SET, BROAD_SET = "120250027170880521", "120249918199040521", "120249918193310521"
CREATIVES = {"Video：用我的方法": "1473832997895184", "Video：不选 forex 不选黄金": "1644593024032530",
             "Video：我跟你讲！": "1104962755787873", "Video：盖电脑，喂！": "1783486816241364"}
DAILY = 5000


def strip_locale(t: dict) -> dict:
    t = copy.deepcopy(t)
    t.pop("locales", None)
    return t


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    assert acct.endswith("893025326577600")
    assert not compliance.filter_banned(list(CREATIVES), s.compliance.banned_creatives), "banned"
    src = g.get_object(DT_SET, "targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                               "regional_regulated_categories,regional_regulation_identities")
    lal_t = g.get_object(LAL_SET, "targeting")["targeting"]
    broad_t = g.get_object(BROAD_SET, "targeting")["targeting"]
    a_t = strip_locale(src["targeting"]); a_t.update({"age_min": 28, "age_max": 65, "targeting_automation": {"advantage_audience": 0}}); a_t.pop("age_range", None)
    b_t = strip_locale(lal_t); b_t.update({"age_min": 28, "age_max": 65, "targeting_automation": {"advantage_audience": 0}}); b_t.pop("age_range", None)
    c_t = strip_locale(broad_t); c_t.pop("flexible_spec", None); c_t.pop("custom_audiences", None)
    c_t.update({"targeting_automation": {"advantage_audience": 1}, "age_range": [28, 65]})
    builds = [("(Webinarkit) [SG] STOCKBLOOM | DAY TRADING SG · ALL LANG | 1-1-4 | 1026", "Day Trading | SG 28+ · 全语言", a_t),
              ("(Webinarkit) [SG] STOCKBLOOM | PURCHASE LAL 5% · ALL LANG | 1-1-4 | 1026", "Purchase LAL 5% | SG 28+ · 全语言", b_t),
              ("(Webinarkit) [SG] STOCKBLOOM | BROAD SG · ALL LANG | 1-1-4 | 1026", "Broad | SG 28+ · 全语言", c_t)]
    camps = {c["name"]: c["id"] for c in g._get_all(acct + "/campaigns", {"fields": "name", "limit": "300"})}
    print(f"SG ALL-LANG build — {'APPLY' if CONFIRM else 'DRY-RUN'}")
    for cname, sname, t in builds:
        flex = t.get("flexible_spec") or []
        n = sum(len(spec.get(k) or []) for spec in flex for k in ("interests", "behaviors", "work_positions", "industries"))
        print(f"\n  «{cname}» exists {cname in camps}\n    › «{sname}» geo {t.get('geo_locations', {}).get('countries')} · locales {t.get('locales')} · "
              f"age_min {t.get('age_min')} age_max {t.get('age_max')} age_range {t.get('age_range')} · adv+ {t['targeting_automation']['advantage_audience']} · "
              f"interests {n} · CA {[x.get('name', x.get('id')) for x in t.get('custom_audiences', [])]}")
        if not CONFIRM or cname in camps:
            continue
        c = g.create_campaign(acct, name=cname, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                              daily_budget=DAILY, bid_strategy="LOWEST_COST_WITHOUT_CAP", buying_type="AUCTION")
        time.sleep(2)
        a = g.create_adset(acct, name=sname, campaign_id=c["id"], status="ACTIVE", optimization_goal=src["optimization_goal"],
                           billing_event=src["billing_event"], targeting=t, promoted_object=src["promoted_object"],
                           attribution_spec=src.get("attribution_spec"),
                           regional_regulated_categories=src["regional_regulated_categories"],
                           regional_regulation_identities=src["regional_regulation_identities"])
        time.sleep(2)
        ids = []
        for n_, cr in CREATIVES.items():
            ids.append(g.create_ad(acct, name=n_, adset_id=a["id"], creative={"creative_id": cr}, status="ACTIVE")["id"]); time.sleep(2)
        print(f"    ✅ campaign {c['id']} (PAUSED, RM{DAILY // 100}) · adset {a['id']} · ads {ids}")
    print("\nSG ALL-LANG DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
